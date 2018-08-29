from functools import lru_cache

from mian.core.constants import RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_FILENAME, \
    RAW_OTU_TABLE_LABELS_FILENAME, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME
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

    def __init__(self, user_id, pid, use_raw=False):
        self.user_id = ""
        self.pid = ""
        self.sample_metadata = ""
        self.otu_metadata = ""
        self.table = []
        self.headers = []
        self.sample_labels = []
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
            self.table = DataIO.tsv_to_np_table(self.user_id, self.pid, RAW_OTU_TABLE_FILENAME)
            labels = DataIO.tsv_to_table(self.user_id, self.pid, RAW_OTU_TABLE_LABELS_FILENAME)
            self.headers = labels[0]
            self.sample_labels = labels[1]
        else:
            logger.info("Using subsampled data")
            self.table = DataIO.tsv_to_np_table(self.user_id, self.pid, SUBSAMPLED_OTU_TABLE_FILENAME)
            labels = DataIO.tsv_to_table(self.user_id, self.pid, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)
            self.headers = labels[0]
            self.sample_labels = labels[1]
        logger.info("Finished table loading")

    def get_table(self):
        return self.table

    def get_headers(self):
        return self.headers

    def get_sample_labels(self):
        return self.sample_labels

    def get_table_after_filtering(self, user_request):
        t, h, s = self.filter_otu_table_by_metadata(self.table, self.headers, self.sample_labels, user_request)
        t, h, s = self.filter_otu_table_by_taxonomic_items(t, h, s, self.otu_metadata.get_taxonomy_map(), user_request)
        return t, h, s

    def get_table_after_filtering_and_aggregation(self, user_request):
        logger.info("Starting filtering and aggregation")
        t, h, s = self.filter_otu_table_by_metadata(self.table, self.headers, self.sample_labels, user_request)
        logger.info("Finished filtering by metadata")
        t, h, s = self.filter_otu_table_by_taxonomic_items(t, h, s, self.otu_metadata.get_taxonomy_map(), user_request)
        logger.info("Finished filtering by taxonomic items")
        t, h, s = self.aggregate_otu_table_at_taxonomic_level(t, h, s, user_request)
        logger.info("Finished aggregation")
        return t, h, s

    def get_table_after_filtering_and_aggregation_and_low_count_exclusion(self, user_request):
        logger.info("Starting filtering and aggregation")
        t, h, s = self.filter_otu_table_by_metadata(self.table, self.headers, self.sample_labels, user_request)
        logger.info("Finished filtering by metadata")
        t, h, s = self.filter_otu_table_by_taxonomic_items(t, h, s, self.otu_metadata.get_taxonomy_map(), user_request)
        logger.info("Finished filtering by taxonomic items")
        t, h, s = self.aggregate_otu_table_at_taxonomic_level(t, h, s, user_request)
        logger.info("Finished filtering by low counts")
        t, h, s = self.filter_out_low_count_np(t, h, s, user_request)
        logger.info("Finished aggregation")
        return t, h, s

    def get_table_after_filtering_and_aggregation_and_low_count_aggregation(self, user_request):
        logger.info("Starting filtering and aggregation")
        t, h, s = self.filter_otu_table_by_metadata(self.table, self.headers, self.sample_labels, user_request)
        logger.info("Finished filtering by metadata")
        t, h, s = self.filter_otu_table_by_taxonomic_items(t, h, s, self.otu_metadata.get_taxonomy_map(), user_request)
        logger.info("Finished filtering by taxonomic items")
        t, h, s = self.aggregate_otu_table_at_taxonomic_level(t, h, s, user_request)
        logger.info("Finished filtering by low counts")
        t, h, s = self.aggregate_low_count_np(t, h, s, user_request)
        logger.info("Finished aggregation")
        return t, h, s

    def get_otu_metadata(self):
        return self.otu_metadata

    def get_sample_metadata(self):
        return self.sample_metadata

    def filter_otu_table_by_metadata(self, base, headers, sample_labels, user_request):
        """
        Filters an OTU table by a particular metadata category by identifying the samples that fall under the
        metadata category
        :param base:
        :param metadata:
        :param catvar:
        :param values:
        :return:
        """
        catvar = user_request.sample_filter
        role = user_request.sample_filter_role
        values = user_request.sample_filter_vals
        if catvar == "none" or catvar == "" or (len(values) == 1 and values[0] == "mian-select-all"):
            # Filtering is not enabled or everything is selected
            logger.info("Sample filtering not enabled or all samples are selected")
            return base, headers, sample_labels

        metadata_map = self.sample_metadata.get_sample_id_to_metadata_map(catvar)

        samples = {}

        row = 0
        while row < len(base):
            sample_id = sample_labels[row]
            if sample_id in metadata_map:
                if role == "Include":
                    if metadata_map[sample_id] in values:
                        samples[sample_id] = 1
                else:
                    if metadata_map[sample_id] not in values:
                        samples[sample_id] = 1

            row += 1

        if samples is None or samples == "":
            samples = []

        new_otu_table = []
        new_sample_labels = []

        num_filtered_samples = 0
        i = 0
        while i < len(base):
            sample_id = sample_labels[i]
            if sample_id in samples:
                new_otu_table.append(base[i])
                new_sample_labels.append(sample_id)
            else:
                num_filtered_samples += 1
            i += 1

        logger.info("Filtered out " + str(num_filtered_samples) + "/" + str(len(base)) + " samples")
        return new_otu_table, headers, new_sample_labels

    def filter_otu_table_by_taxonomic_items(self, base, headers, sample_labels, taxonomic_map, user_request):
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
        level = user_request.taxonomy_filter
        role = user_request.taxonomy_filter_role
        items_of_interest = user_request.taxonomy_filter_vals

        if int(level) == -2 or (len(items_of_interest) == 1 and items_of_interest[0] == "mian-select-all"):
            # -2 indicates that we should not filter by taxonomic items or everything is selected
            logger.info("OTU filtering not enabled or all OTUs are selected")
            return base, headers, sample_labels

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
        new_headers = []

        num_filtered_otus = 0
        i = 0
        while i < len(base):
            new_row = []
            j = 0
            while j < len(base[i]):
                if headers[j] in otus:
                    new_row.append(base[i][j])
                    if i == 0:
                        new_headers.append(headers[j])
                else:
                    if i == 0:
                        num_filtered_otus += 1
                j += 1
            new_otu_table.append(new_row)
            i += 1
        logger.info("Table cols = " + str(len(new_otu_table[0])) + " header cols = " + str(len(new_headers)))
        logger.info("Filtered out " + str(num_filtered_otus) + "/" + str(len(base[0])) + " OTUs/taxas")
        return new_otu_table, new_headers, sample_labels

    def aggregate_otu_table_at_taxonomic_level(self, base, headers, sample_labels, user_request):
        """
        Returns an OTU table that has been aggregated at a specific taxonomic level (eg. this could return a
        table that is grouped at the Family taxonomic level)
        :param base:
        :param level:
        :return:
        """
        level = user_request.level
        if int(level) < 0:
            # We want to aggregate at the OTU level, which is essentially not aggregating at all
            return base, headers, sample_labels

        taxonomy_map = self.otu_metadata.get_taxonomy_map()
        taxonomies = []
        taxonomy_to_cols = {}
        j = 0
        while j < len(headers):
            otu = headers[j]

            if otu not in taxonomy_map:
                # TODO: This actually indicates bad input data
                j += 1
                continue

            taxonomy = "; ".join(taxonomy_map[otu][:int(level) + 1])
            if taxonomy in taxonomy_to_cols:
                taxonomy_to_cols[taxonomy].append(j)
            else:
                taxonomy_to_cols[taxonomy] = [j]
                taxonomies.append(taxonomy)
            j += 1

        with Pool() as pool:
            func = partial(process_row_aggregate_otu_table_at_taxonomic_level, taxonomies, taxonomy_to_cols)
            aggregated_base = pool.map(func, base)
            aggregated_headers = taxonomies
            logger.info("Agg Table cols = " + str(len(aggregated_base[0])) + " header cols = " + str(len(aggregated_headers)))
            return aggregated_base, aggregated_headers, sample_labels

    def aggregate_otu_table_at_taxonomic_level_np(self, base, headers, sample_labels, level):
        """
        Returns an OTU table that has been aggregated at a specific taxonomic level (eg. this could return a
        table that is grouped at the Family taxonomic level). Approx 5x slower than non-np version
        :param base:
        :param level:
        :return:
        """
        if int(level) < 0:
            # We want to aggregate at the OTU level, which is essentially not aggregating at all
            return base, headers, sample_labels

        taxonomy_map = self.otu_metadata.get_taxonomy_map()
        taxonomies = []
        taxonomy_to_cols = {}
        i = 0
        while i < len(headers):
            otu = headers[i]
            if otu not in taxonomy_map:
                # TODO: This actually indicates bad input data
                i += 1
                continue

            taxonomy = "; ".join(taxonomy_map[otu][:int(level) + 1])
            if taxonomy in taxonomy_to_cols:
                taxonomy_to_cols[taxonomy].append(i)
            else:
                taxonomy_to_cols[taxonomy] = [i]
                taxonomies.append(taxonomy)
            i += 1

        rows = len(base)
        cols = len(taxonomies)

        aggregated_base = np.zeros((rows, cols))
        i = 0
        for taxonomy in taxonomies:
            cols_to_aggregate = taxonomy_to_cols[taxonomy]
            aggregated_base[:, i] += np.sum(base[:, cols_to_aggregate], axis=1)
            i += 1

        aggregated_headers = taxonomies

        return aggregated_base, aggregated_headers, sample_labels

    def filter_out_low_count_np(self, base, headers, sample_labels, user_request):

        logger.info("Starting filtering by low count")
        count_threshold = user_request.taxonomy_filter_count
        min_prevalence = user_request.taxonomy_filter_prevalence

        base = np.array(base)
        headers = np.array(headers)
        num_samples = base.shape[0]
        min_prevalence_percentage = min_prevalence / float(100)
        otus_over_threshold = (base > count_threshold).astype(int)
        otus_to_keep = np.divide(np.sum(otus_over_threshold, axis=0), num_samples) >= min_prevalence_percentage

        logger.info(
            "Done filtering by low count. Kept " + str(sum(otus_to_keep)) + " cols out of " + str(len(headers)))
        return base[:, otus_to_keep], headers[otus_to_keep], sample_labels

    def aggregate_low_count_np(self, base, headers, sample_labels, user_request):
        count_threshold = user_request.taxonomy_filter_count
        min_prevalence = user_request.taxonomy_filter_prevalence

        base = np.array(base)
        headers = np.array(headers)
        num_samples = base.shape[0]
        min_prevalence_percentage = min_prevalence / float(100)
        otus_over_threshold = (base > count_threshold).astype(int)
        otus_to_keep = np.divide(np.sum(otus_over_threshold, axis=0), num_samples) >= min_prevalence_percentage
        otus_to_aggregate = np.divide(np.sum(otus_over_threshold, axis=0), num_samples) < min_prevalence_percentage
        aggregated_col = np.sum(base[:, otus_to_aggregate], axis=1)
        aggregated_base = np.c_[base[:, otus_to_keep], aggregated_col]
        aggregated_headers = headers[otus_to_keep].append("Other")

        logger.info(
            "Aggregate low count cols = " + str(len(otus_to_aggregate)) + " header cols = " + str(len(aggregated_headers)))
        return aggregated_base, aggregated_headers, sample_labels


    @staticmethod
    def get_otu_table_headers_at_taxonomic_level(user_id, pid, level, use_raw=False):
        if use_raw:
            logger.info("Using raw data")
            labels = DataIO.tsv_to_table(user_id, pid, RAW_OTU_TABLE_LABELS_FILENAME)
            headers = labels[0]
        else:
            logger.info("Using subsampled data")
            labels = DataIO.tsv_to_table(user_id, pid, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)
            headers = labels[0]

        if int(level) == -1:
            # OTUs requested
            return headers

        taxonomy = Taxonomy(user_id, pid)
        taxonomy_map = taxonomy.get_taxonomy_map()
        taxonomies = []
        taxonomy_to_cols = {}
        j = 0
        while j < len(headers):
            otu = headers[j]
            if otu in taxonomy_map:
                # Uncomment below if we want to use the fully quantified taxonomy string
                # taxonomy = "; ".join(taxonomy_map[otu][:int(level) + 1])
                taxonomy = taxonomy_map[otu][int(level)]
                if taxonomy != "":
                    if taxonomy in taxonomy_to_cols:
                        taxonomy_to_cols[taxonomy].append(j)
                    else:
                        taxonomy_to_cols[taxonomy] = [j]
                        taxonomies.append(taxonomy)
            j += 1
        return taxonomies

# Global method
def process_row_aggregate_otu_table_at_taxonomic_level(taxonomies, taxonomy_to_cols, row):
    new_row = []
    for taxonomy in taxonomies:
        cols_to_aggregate = taxonomy_to_cols[taxonomy]
        s = 0
        for col in cols_to_aggregate:
            s += float(row[col])
        new_row.append(s)
    return new_row