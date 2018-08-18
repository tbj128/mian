from functools import lru_cache

from mian.core.constants import SAMPLE_ID_COL, RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_FILENAME
from mian.core.data_io import DataIO
from mian.model.metadata import Metadata
from mian.model.taxonomy import Taxonomy
import logging
from multiprocessing import Pool
from functools import partial
import datetime
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class OTUTable(object):

    SAMPLE_ID_COL = SAMPLE_ID_COL
    OTU_START_COL = 1

    def __init__(self, user_id, pid, use_raw=False):
        self.user_id = ""
        self.pid = ""
        self.sample_metadata = ""
        self.otu_metadata = ""
        self.table = ""
        self.load_otu_table(user_id, pid, use_raw)
        logger.info(DataIO.tsv_to_table.cache_info())

    def load_otu_table(self, user_id, pid, use_raw):
        self.user_id = user_id
        self.pid = pid
        logger.info("Before load")
        self.sample_metadata = Metadata(user_id, pid)
        logger.info("Finished metadata loading")
        self.otu_metadata = Taxonomy(user_id, pid)
        logger.info("Finished taxonomy loading")
        if use_raw:
            logger.info("Using raw data")
            self.table = DataIO.tsv_to_table(self.user_id, self.pid, RAW_OTU_TABLE_FILENAME)
        else:
            logger.info("Using subsampled data")
            self.table = DataIO.tsv_to_table(self.user_id, self.pid, SUBSAMPLED_OTU_TABLE_FILENAME)
        logger.info("Finished table loading")

    def get_table(self):
        return self.table

    def get_table_after_filtering(self, taxFilter, taxFilterRole, taxFilterVals, sampleFilter, sampleFilterRole, sampleFilterVals):
        t = self.filter_otu_table_by_metadata(self.table, sampleFilter, sampleFilterRole, sampleFilterVals)
        t = self.filter_otu_table_by_taxonomic_items(t, self.otu_metadata.get_taxonomy_map(), taxFilter, taxFilterRole, taxFilterVals)
        return t

    def get_table_after_filtering_and_aggregation(self, taxFilter, taxFilterRole, taxFilterVals, sampleFilter, sampleFilterRole, sampleFilterVals, taxAggregationLevel):
        logger.info("Starting filtering and aggregation")
        t = self.filter_otu_table_by_metadata(self.table, sampleFilter, sampleFilterRole, sampleFilterVals)
        logger.info("Finished filtering by metadata")
        t = self.filter_otu_table_by_taxonomic_items(t, self.otu_metadata.get_taxonomy_map(), taxFilter, taxFilterRole, taxFilterVals)
        logger.info("Finished filtering by taxonomic items")
        t = self.aggregate_otu_table_at_taxonomic_level(t, taxAggregationLevel)
        logger.info("Finished aggregation")
        return t

    def get_table_after_filtering_and_aggregation_and_low_count_exclusion(self, taxFilter, taxFilterRole, taxFilterVals, sampleFilter, sampleFilterRole, sampleFilterVals, taxAggregationLevel):
        logger.info("Starting filtering and aggregation")
        t = self.filter_otu_table_by_metadata(self.table, sampleFilter, sampleFilterRole, sampleFilterVals)
        logger.info("Finished filtering by metadata")
        t = self.filter_otu_table_by_taxonomic_items(t, self.otu_metadata.get_taxonomy_map(), taxFilter, taxFilterRole, taxFilterVals)
        logger.info("Finished filtering by taxonomic items")
        t = self.aggregate_otu_table_at_taxonomic_level(t, taxAggregationLevel)
        logger.info("Finished filtering by low counts")
        t = self.filter_out_low_count(t)
        logger.info("Finished aggregation")
        return t

    def get_otu_metadata(self):
        return self.otu_metadata

    def get_sample_metadata(self):
        return self.sample_metadata

    def filter_otu_table_by_metadata(self, base, catvar, role, values):
        """
        Filters an OTU table by a particular metadata category by identifying the samples that fall under the
        metadata category
        :param base:
        :param metadata:
        :param catvar:
        :param values:
        :return:
        """
        if values is None or values == "":
            values = []

        if catvar == "none" or catvar == "":
            return base

        metadata_map = self.sample_metadata.get_sample_id_to_metadata_map(catvar)

        samples = {}

        row = 1
        while row < len(base):
            sample_id = base[row][OTUTable.SAMPLE_ID_COL]
            if sample_id in metadata_map:
                if role == "Include":
                    if metadata_map[sample_id] in values:
                        samples[sample_id] = 1
                else:
                    if metadata_map[sample_id] not in values:
                        samples[sample_id] = 1

            row += 1

        return self.__filter_otu_by_samples(samples)

    def __filter_otu_by_samples(self, samples):
        """
        Filters the OTU table by selected samples
        :param base:
        :param samples:
        :return:
        """
        if samples is None or samples == "":
            samples = []

        new_otu_table = []

        i = 0
        while i < len(self.table):
            if i == 0:
                new_otu_table.append(self.table[i])
            else:
                sample_id = self.table[i][OTUTable.SAMPLE_ID_COL]
                if sample_id in samples:
                    new_otu_table.append(self.table[i])
            i += 1

        return new_otu_table

    def filter_otu_table_by_taxonomic_items(self, base, taxonomic_map, level, role, items_of_interest):
        """
        Returns an OTU table that has been filtered by specific taxonomic items of interest
        (eg. if the user selected that they only wanted to see Staphylococcus genus, an OTU table
        will be returned that only contains Staphylococcus OTUs)
        :param base:
        :param taxonomic_map:
        :param items_of_interest:
        :param level:
        :return:
        """
        if items_of_interest is None or items_of_interest == "":
            items_of_interest = []

        if items_of_interest == "mian-select-all":
            return base

        otus = {}
        for otu, classification in taxonomic_map.items():
            if 0 <= int(level) < len(classification):
                if role == "Include":
                    if classification[int(level)] in items_of_interest:
                        otus[otu] = 1
                else:
                    if classification[int(level)] not in items_of_interest:
                        otus[otu] = 1
            elif int(level) == -1:
                if role == "Include":
                    if otu in items_of_interest:
                        otus[otu] = 1
                else:
                    if otu not in items_of_interest:
                        otus[otu] = 1
            else:
                otus[otu] = 1

        new_otu_table = []
        relevant_cols = {}

        i = 0
        while i < len(base):
            if i == 0:
                # Header row
                # Ignores the first column (sample ID)
                new_row = []
                j = 0
                while j < OTUTable.OTU_START_COL:
                    new_row.append(base[i][j])
                    relevant_cols[j] = 1
                    j += 1

                j = OTUTable.OTU_START_COL
                while j < len(base[i]):
                    if base[i][j] in otus:
                        new_row.append(base[i][j])
                        relevant_cols[j] = 1
                    j += 1
                new_otu_table.append(new_row)
            else:
                new_row = []
                j = 0
                while j < len(base[i]):
                    if j in relevant_cols:
                        new_row.append(base[i][j])
                    j += 1
                new_otu_table.append(new_row)
            i += 1
        return new_otu_table

    def aggregate_otu_table_at_taxonomic_level_orig(self, base, level):
        """
        Returns an OTU table that has been aggregated at a specific taxonomic level (eg. this could return a
        table that is grouped at the Family taxonomic level)
        :param base:
        :param level:
        :return:
        """
        if int(level) < 0:
            # We want to aggregate at the OTU level, which is essentially not aggregating at all
            return base

        taxonomy_map = self.otu_metadata.get_taxonomy_map()
        taxonomies = []
        taxonomy_to_cols = {}
        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            otu = base[0][j]
            taxonomy = taxonomy_map[otu][int(level)]
            if taxonomy in taxonomy_to_cols:
                taxonomy_to_cols[taxonomy].append(j)
            else:
                taxonomy_to_cols[taxonomy] = [j]
                taxonomies.append(taxonomy)
            j += 1

        aggregated_base = []
        i = 0
        for row in base:
            new_row = [row[OTUTable.SAMPLE_ID_COL]]
            for taxonomy in taxonomies:
                cols_to_aggregate = taxonomy_to_cols[taxonomy]
                if i == 0:
                    # Just print out the headers
                    new_row.append(taxonomy)
                else:
                    s = 0
                    for col in cols_to_aggregate:
                        s += float(row[col])
                    new_row.append(s)
            aggregated_base.append(new_row)
            i += 1

        return aggregated_base

    def aggregate_otu_table_at_taxonomic_level_np(self, base, level):
        """
        Returns an OTU table that has been aggregated at a specific taxonomic level (eg. this could return a
        table that is grouped at the Family taxonomic level)
        :param base:
        :param level:
        :return:
        """
        if int(level) < 0:
            # We want to aggregate at the OTU level, which is essentially not aggregating at all
            return base

        taxonomy_map = self.otu_metadata.get_taxonomy_map()
        taxonomies = []
        taxonomy_to_cols = {}
        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            otu = base[0][j]
            taxonomy = taxonomy_map[otu][int(level)]
            if taxonomy in taxonomy_to_cols:
                taxonomy_to_cols[taxonomy].append(j - 1)
            else:
                taxonomy_to_cols[taxonomy] = [j - 1]
                taxonomies.append(taxonomy)
            j += 1

        rows = len(base) - 1
        cols = len(taxonomies)
        base = np.array(base[1:])
        base = np.array(base[:,1:], dtype=float)
        # base = np.delete(base, 0, 1)
        # base = np.genfromtxt(base)

        aggregated_base = np.zeros((rows, cols))
        i = 0
        for taxonomy in taxonomies:
            cols_to_aggregate = taxonomy_to_cols[taxonomy]
            aggregated_base[:, i] += np.sum(base[:, cols_to_aggregate])
            i += 1

        return aggregated_base


    def aggregate_otu_table_at_taxonomic_level(self, base, level):
        """
        Returns an OTU table that has been aggregated at a specific taxonomic level (eg. this could return a
        table that is grouped at the Family taxonomic level)
        :param base:
        :param level:
        :return:
        """
        if int(level) < 0:
            # We want to aggregate at the OTU level, which is essentially not aggregating at all
            return base

        taxonomy_map = self.otu_metadata.get_taxonomy_map()
        taxonomies = []
        taxonomy_to_cols = {}
        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            otu = base[0][j]
            taxonomy = "; ".join(taxonomy_map[otu][:int(level) + 1])
            if taxonomy in taxonomy_to_cols:
                taxonomy_to_cols[taxonomy].append(j)
            else:
                taxonomy_to_cols[taxonomy] = [j]
                taxonomies.append(taxonomy)
            j += 1

        with Pool() as pool:
            func = partial(process_row_aggregate_otu_table_at_taxonomic_level, taxonomies, taxonomy_to_cols)
            aggregated_base = pool.map(func, base[1:])

            # Add back the headers
            header_row = [base[0][0]]
            header_row.extend(taxonomies)
            aggregated_base.insert(0, header_row)
            return aggregated_base

    def filter_out_low_count(self, base, count_threshold=3, min_prevalence=20):
        """
        TODO: Generate filtered dataset DURING CREATION???
        TODO: Make faster
        Returns an OTU table after removing OTUs who appear in less than or equal to the threshold count
        :param base:
        :param level:
        :return:
        """

        filtered_base = []
        cols_to_remove = {}

        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            total_num_samples = len(base) - 1
            over_threshold = 0
            i = 1
            while i < len(base):
                otu_val = float(base[i][j])
                if otu_val > count_threshold:
                    over_threshold += 1
                i += 1
            if over_threshold / total_num_samples < min_prevalence / 100:
                cols_to_remove[j] = 1
            j += 1

        i = 0
        while i < len(base):
            new_row = []
            j = 0
            while j < len(base[i]):
                if j not in cols_to_remove:
                    new_row.append(base[i][j])
                j += 1
            filtered_base.append(new_row)
            i += 1

        return filtered_base

    def filter_out_low_count_np(self, base, count_threshold=3, min_prevalence=20):
        """
        TODO: Generate filtered dataset DURING CREATION???
        TODO: Make faster
        Returns an OTU table after removing OTUs who appear in less than or equal to the threshold count
        :param base:
        :param level:
        :return:
        """

        base_np = np.array(base)
        print(str(np.sum(base_np[2, 1:])))

        filtered_base = []
        cols_to_remove = {}

        j = OTUTable.OTU_START_COL
        while j < len(base[0]):
            total_num_samples = len(base) - 1
            over_threshold = 0
            i = 1
            while i < len(base):
                otu_val = float(base[i][j])
                if otu_val > count_threshold:
                    over_threshold += 1
                i += 1
            if over_threshold / total_num_samples < min_prevalence / 100:
                cols_to_remove[j] = 1
            j += 1

        i = 0
        while i < len(base):
            new_row = []
            j = 0
            while j < len(base[i]):
                if j not in cols_to_remove:
                    new_row.append(base[i][j])
                j += 1
            filtered_base.append(new_row)
            i += 1

        return filtered_base

def process_row_aggregate_otu_table_at_taxonomic_level(taxonomies, taxonomy_to_cols, row):
    new_row = [row[OTUTable.SAMPLE_ID_COL]]
    for taxonomy in taxonomies:
        cols_to_aggregate = taxonomy_to_cols[taxonomy]
        s = 0
        for col in cols_to_aggregate:
            s += float(row[col])
        new_row.append(s)
    return new_row