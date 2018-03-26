# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#

import uuid

from io import StringIO
from mian.core.otu_table_subsampler import OTUTableSubsampler
from mian.core.constants import RAW_OTU_TABLE_FILENAME, \
    SUBSAMPLED_OTU_TABLE_FILENAME, BIOM_FILENAME, TAXONOMY_FILENAME, SAMPLE_METADATA_FILENAME
import csv
import os
import re
import logging
from biom import load_table

from mian.model.map import Map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectManager(object):

    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def __init__(self, user_id):
        self.user_id = user_id

    def create_project_from_tsv(self, project_name, otu_filename, taxonomy_filename, sample_metadata_filename, subsample_type="auto", subsample_to=0):

        # Creates a directory for this project
        pid = str(uuid.uuid4())
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        else:
            raise Exception("Cannot create project folder as it already exists")

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        os.rename(os.path.join(user_staging_dir, otu_filename), os.path.join(project_dir, RAW_OTU_TABLE_FILENAME))
        ### TODO: PROCESS THE TAXONOMY FILE
        os.rename(os.path.join(user_staging_dir, taxonomy_filename), os.path.join(project_dir, TAXONOMY_FILENAME))
        os.rename(os.path.join(user_staging_dir, sample_metadata_filename), os.path.join(project_dir, SAMPLE_METADATA_FILENAME))

        # Subsamples raw OTU table
        subsample_value = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                 pid=pid,
                                                                 subsample_type=subsample_type,
                                                                 manual_subsample_to=subsample_to,
                                                                 raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                 output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        # Creates map.txt file
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.orig_otu_table_name = otu_filename
        map_file.orig_sample_metadata_name = sample_metadata_filename
        map_file.orig_taxonomy_name = taxonomy_filename
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.save()

        return pid

    def create_project_from_biom(self, project_name, biom_name, subsample_type="auto", subsample_to=0):
        """
        Reads a .biom from a provided file location and converts it into a mian-compatible TSV file

        Args:
            user_id (str): The user ID of the associated account
            pid (str): The project ID under the user account
            biom_name (str): The name of the BIOM file (not path)

        Returns:
            array: Array representation of the input TSV file

        """

        # Creates a directory for this project
        pid = str(uuid.uuid4())
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        else:
            raise Exception("Cannot create project folder as it already exists")

        return self.__process_biom_file(pid, project_dir, project_name, biom_name, subsample_type, subsample_to)

    def __process_biom_file(self, pid, project_dir, project_name, biom_name, subsample_type="auto", subsample_to=0):
        # Renames the uploaded file to a standard file schema and moves to the project directory
        biom_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        biom_staging_dir = os.path.join(biom_staging_dir, biom_name)
        biom_project_dir = os.path.join(project_dir, BIOM_FILENAME)
        os.rename(biom_staging_dir, biom_project_dir)
        logger.info("Moved " + str(biom_staging_dir) + " to " + str(biom_project_dir))

        # Extracts the OTU table from the biom file and saves the raw OTU file
        biom_path = os.path.join(project_dir, BIOM_FILENAME)
        raw_table_path = os.path.join(project_dir, RAW_OTU_TABLE_FILENAME)

        logger.info("Converting biom to intermediate TSV file " + biom_path)
        table = load_table(biom_path)
        self.__save_biom_table_as_tsv(table, raw_table_path)

        # Subsamples the raw OTU file
        subsample_to, removed_otus = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                            pid=pid,
                                                                            subsample_type=subsample_type,
                                                                            manual_subsample_to=subsample_to,
                                                                            raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                            output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        # Create Sample Metadata File
        logger.info("Creating sample metadata file")
        sample_metadata_path = os.path.join(project_dir, SAMPLE_METADATA_FILENAME)
        sample_metadata = table.metadata(None, 'sample')
        sample_ids = table.ids('sample')
        with open(sample_metadata_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            sample_index = 0
            for k in sample_metadata:
                if sample_index == 0:
                    # We will write out the metadata headers at the top of this file
                    headers = ["SampleID"]
                    for key, value in sorted(k.items()):
                        headers.append(key)
                    output_tsv.writerow(headers)

                sample_id = sample_ids[sample_index]
                row_data = [sample_id]
                for key, value in sorted(k.items()):
                    # Write out the contents of each metadata
                    row_data.append(value)
                output_tsv.writerow(row_data)
                sample_index += 1

        # Generates Taxonomy File
        logger.info("Creating taxonomy file")
        otu_metadata = table.metadata(None, 'observation')
        otu_ids = table.ids('observation')
        otu_metadata_path = os.path.join(project_dir, TAXONOMY_FILENAME)
        taxonomy_type = ""
        with open(otu_metadata_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            otu_index = 0
            taxonomy_key = ""

            # Each row in the otu_metadata is the metadata for the corresponding OTU
            for k in otu_metadata:
                if otu_index == 0:
                    # Do some additional processing for the first OTU metadata line processed
                    logger.info("Processing first OTU metadata / taxonomy header line")

                    # We will write out the metadata headers at the top of this file
                    headers = ["OTU"]

                    # Find which column is the taxonomy column
                    # Logic:
                    #    1) Look for the metadata key which says "taxonomy"
                    #    2) If (1) does not work, look into the metadata value to find one that contains "Bacteria"
                    #       as this is common to both Silva and Greengenes taxonomy

                    logger.info("Finding taxonomy key %s", str(k))

                    potential_taxonomy_key = ""
                    for key, value in k.items():
                        if key.lower() == "taxonomy":
                            taxonomy_key = key
                            break
                        elif (type(value) is list and any("bacteria" in s.lower() for s in value)) or \
                                (type(value) is str and "bacteria" in value.lower()):
                            potential_taxonomy_key = key

                    if taxonomy_key == "":
                        logger.info("Using the potential taxonomy key of " + str(potential_taxonomy_key) +
                                    " because could not find the actual taxonomy key")
                        taxonomy_key = potential_taxonomy_key

                    if taxonomy_key == "":
                        logger.error("No taxonomy found!")
                        raise ValueError("No taxonomy found!")

                    taxonomy_type = self.get_taxonomy_type(k[taxonomy_key])
                    logger.info("Taxonomy type was determined to be %s", taxonomy_type)

                    headers.append(taxonomy_key)

                    for key, value in sorted(k.items()):
                        if key != taxonomy_key:
                            headers.append(key)
                    output_tsv.writerow(headers)

                # Write out the taxonomy file line by line such that the taxonomy is always the second column
                # We keep the other OTU metadata just in case we will use it in the future
                otu_id = otu_ids[otu_index]
                if otu_id not in removed_otus:
                    row_data = [otu_id] + self.process_taxonomy_line(taxonomy_type, k[taxonomy_key])
                    logger.info("Row data generated: " + str(row_data))
                    for key, value in sorted(k.items()):
                        if key != taxonomy_key:
                            row_data.append(value)
                    output_tsv.writerow(row_data)
                otu_index += 1

        # Creates map.txt file
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.orig_biom_name = biom_name
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_to
        map_file.taxonomy_type = taxonomy_type
        map_file.save()

        return pid

    def __save_biom_table_as_tsv(self, table, output_path):
        result = table.to_tsv(header_key="",
                              header_value="",
                              metadata_formatter="sc_separated")

        # Converts the TSV string to an array
        f = StringIO(result)
        intermediate_table = []
        base_csv = csv.reader(f, delimiter='\t', quotechar='|')
        for o in base_csv:
            if len(o) > 1:
                intermediate_table.append(o)

        # The intermediate table is sample-columnar (ie. rows are OTUs) but the majority of the analysis in
        # mian uses samples as rows so we perform a conversion
        with open(output_path, 'w') as out_f:
            output_tsv = csv.writer(out_f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for x in zip(*intermediate_table):
                output_tsv.writerow(x)

        logger.info("Finished transposing to final TSV file " + output_path)

    def replace_existing_biom_file(self, pid, biom_filename, subsample_type, subsample_to):
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            raise Exception("Project does not exist")
        map_file = Map(self.user_id, pid)
        return self.__process_biom_file(pid, project_dir, map_file.project_name, biom_filename, subsample_type, subsample_to)

    def replace_existing_otu_table(self, pid, otu_filename, subsample_type, subsample_to):
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        map_file = Map(self.user_id, pid)

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        os.rename(os.path.join(user_staging_dir, otu_filename), os.path.join(project_dir, RAW_OTU_TABLE_FILENAME))

        # Subsamples raw OTU table
        subsample_value = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                 pid=pid,
                                                                 subsample_type=subsample_type,
                                                                 manual_subsample_to=subsample_to,
                                                                 raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                                                                 output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME)

        map_file.project_name = map_file.project_name
        map_file.orig_otu_table_name = otu_filename
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.save()
        return subsample_value

    def replace_existing_sample_metadata(self, pid, uploaded_filename):
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        map_file = Map(self.user_id, pid)
        map_file.orig_sample_metadata_name = uploaded_filename
        map_file.save()

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        os.rename(os.path.join(user_staging_dir, uploaded_filename), os.path.join(project_dir, SAMPLE_METADATA_FILENAME))

    def replace_existing_taxonomy(self, pid, uploaded_filename):
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        map_file = Map(self.user_id, pid)
        map_file.orig_taxonomy_name = uploaded_filename
        map_file.save()

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        os.rename(os.path.join(user_staging_dir, uploaded_filename), os.path.join(project_dir, TAXONOMY_FILENAME))


    def get_taxonomy_type(self, taxonomy_line):
        if type(taxonomy_line) is list:
            if any("k__" in s.lower() for s in taxonomy_line):
                return "Greengenes"
            else:
                return "Silva"
        else:
            if "k__" in taxonomy_line:
                return "Greengenes"
            else:
                return "Silva"

    def process_taxonomy_line(self, taxonomy_type, taxonomy_line):
        if taxonomy_type == "Greengenes":
            return self.__decompose_gg_taxonomy(taxonomy_line)
        else:
            return self.__decompose_silva_taxonomy(taxonomy_line)

    def __decompose_silva_taxonomy(self, taxonomy_arg):
        # IPF OTU Map
        # Bacteria(100);"Bacteroidetes"(100);Flavobacteria(100);"Flavobacteriales"(100);Flavobacteriaceae(100);Chryseobacterium(100);
        # ["Bacteria", "Bacteroidetes"]

        taxonomy_line = taxonomy_arg
        if type(taxonomy_arg) is list:
            # Creates a semi-colon delimited string for consistent processing below
            taxonomy_line = ";".join(taxonomy_arg)
        elif taxonomy_arg.startswith("["):
            taxonomy_line = taxonomy_arg[1:-1]
            taxonomy_line = taxonomy_line.replace(",", ";")

        taxonomy_line = taxonomy_line.strip()

        taxonomy_line = taxonomy_line.replace("\"", "")

        invalid_pattern = re.compile("(\(\d*?\))|(\[\d*?\])")
        taxonomy_line = re.sub(invalid_pattern, "", taxonomy_line)

        decomposed = taxonomy_line.split(";")

        # Pad the array until the desired classification depth is achieved
        while len(decomposed) < 7:
            decomposed.append("")

        return decomposed

    def __decompose_gg_taxonomy(self, taxonomy_arg):
        # k__Bacteria;p__Bacteroidetes;c__Bacteroidia;o__Bacteroidales;f__[Paraprevotellaceae];
        # k__Bacteria;p__Bacteroidetes;c__Bacteroidia;o__Bacteroidales;f__Prevotellaceae;g__Prevotella;
        # ['k__Bacteria', 'p__Firmicutes', 'c__Clostridia', 'o__Halanaerobiales', 'f__Halanaerobiaceae', 'g__Halanaerobium', 's__Halanaerobiumsaccharolyticum']
        # Root;k__Bacteria;p__Firmicutes;c__Clostridia;o__Clostridiales;f__Lachnospiraceae

        taxonomy_line = taxonomy_arg
        if type(taxonomy_arg) is list:
            # Creates a semi-colon delimited string for consistent processing below
            taxonomy_line = ";".join(taxonomy_arg)
        elif taxonomy_arg.startswith("["):
            taxonomy_line = taxonomy_arg[1:-1]
            taxonomy_line = taxonomy_line.replace(",", ";")

        taxonomy_line = taxonomy_line.strip()

        taxonomy_line = taxonomy_line.replace("\"", "")

        if taxonomy_line.startswith("Root;") or taxonomy_line.startswith("root;"):
            taxonomy_line = taxonomy_line[5:]

        invalid_pattern = re.compile("(\(\d*?\))|(\[\d*?\])")
        taxonomy_line = re.sub(invalid_pattern, "", taxonomy_line)

        arr = taxonomy_line.split(";")
        decomposed = []
        for tax in arr:
            if tax.lower() == "root":
                continue
            else:
                gg_tax_item = tax
                if "__" in tax:
                    gg_tax_item = tax.split("__")[1]
                decomposed.append(gg_tax_item)

        # Pad the array until the desired classification depth is achieved
        while len(decomposed) < 7:
            decomposed.append("")

        return decomposed





    #
    # @staticmethod
    # def filter_otu_table_by_metadata(base, metadata, catvar, values):
    #     """
    #     Filters an OTU table by a particular metadata category by identifying the samples that fall under the
    #     metadata category
    #     :param base:
    #     :param metadata:
    #     :param catvar:
    #     :param values:
    #     :return:
    #     """
    #     if values is None or values == "":
    #         values = []
    #
    #     if catvar == "none" or catvar == "":
    #         return base
    #
    #     meta_col = DataProcessor.get_cat_col(metadata, catvar)
    #     metadata_map = DataProcessor.map_id_to_metadata(metadata, meta_col)
    #
    #     samples = {}
    #
    #     row = 1
    #     while row < len(base):
    #         sample_id = base[row][OTU_GROUP_ID_COL]
    #         if sample_id in metadata_map:
    #             if metadata_map[sample_id] in values:
    #                 samples[sample_id] = 1
    #         row += 1
    #
    #     return DataProcessor.filter_otu_by_samples(base, samples)
    #
    # @staticmethod
    # def filter_otu_by_samples(base, samples):
    #     """
    #     Filters the OTU table by selected samples
    #     :param base:
    #     :param samples:
    #     :return:
    #     """
    #     if samples is None or samples == "":
    #         samples = []
    #
    #     new_otu_table = []
    #
    #     i = 0
    #     while i < len(base):
    #         if i == 0:
    #             new_otu_table.append(base[i])
    #         else:
    #             sample_id = base[i][OTU_GROUP_ID_COL]
    #             if sample_id in samples:
    #                 new_otu_table.append(base[i])
    #         i += 1
    #
    #     return new_otu_table
    #
    # @staticmethod
    # def filter_otu_by_min_positives(base, min_positives):
    #     """
    #     Returns the base OTU table such that any OTUs with less than min_positives number of non-zero values are removed.
    #     This is useful to remove OTUs with a lot of zero values.
    #     :param base:
    #     :param min_positives:
    #     :return:
    #     """
    #     new_otu_table = np.array(base)
    #
    #     dimens = new_otu_table.shape
    #
    #     j = dimens[1] - 1
    #     while j >= OTU_START_COL:
    #         non_zero_count = 0
    #         i = 1
    #         while i < dimens[0]:
    #             if float(new_otu_table[i, j]) != 0:
    #                 non_zero_count += 1
    #             i += 1
    #         if non_zero_count < min_positives:
    #             new_otu_table = np.delete(new_otu_table, j, 1)
    #         j -= 1
    #     return new_otu_table.tolist()
    #
    # @staticmethod
    # def filter_otu_table_by_taxonomic_items(base, taxonomic_map, items_of_interest, level):
    #     """
    #     Returns an OTU table that has been filtered by specific taxonomic items of interest
    #     (eg. if the user selected that they only wanted to see Staphylococcus genus, an OTU table
    #     will be returned that only contains Staphylococcus OTUs)
    #     :param base:
    #     :param taxonomic_map:
    #     :param items_of_interest:
    #     :param level:
    #     :return:
    #     """
    #     if items_of_interest is None or items_of_interest == "":
    #         items_of_interest = []
    #
    #     if items_of_interest == "mian-select-all":
    #         level = -2
    #
    #     otus = {}
    #     for otu, classification in taxonomic_map.items():
    #         if 0 <= int(level) < len(classification):
    #             if classification[int(level)] in items_of_interest:
    #                 otus[otu] = 1
    #         elif int(level) == -1:
    #             if otu in items_of_interest:
    #                 otus[otu] = 1
    #         else:
    #             otus[otu] = 1
    #
    #     new_otu_table = []
    #     relevant_cols = {}
    #
    #     i = 0
    #     while i < len(base):
    #         if i == 0:
    #             # Header row
    #             # Ignores the first column (sample ID)
    #             new_row = []
    #             j = 0
    #             while j < OTU_START_COL:
    #                 new_row.append(base[i][j])
    #                 relevant_cols[j] = 1
    #                 j += 1
    #
    #             j = OTU_START_COL
    #             while j < len(base[i]):
    #                 if base[i][j] in otus:
    #                     new_row.append(base[i][j])
    #                     relevant_cols[j] = 1
    #                 j += 1
    #             new_otu_table.append(new_row)
    #         else:
    #             new_row = []
    #             j = 0
    #             while j < len(base[i]):
    #                 if j in relevant_cols:
    #                     new_row.append(base[i][j])
    #                 j += 1
    #             new_otu_table.append(new_row)
    #         i += 1
    #     return new_otu_table
    #
    # @staticmethod
    # def aggregate_otu_table_at_taxonomic_level(base, taxonomyMap, itemsOfInterest, level):
    #     """
    #     Returns an OTU table that has been aggregated at a specific taxonomic level (eg. this could return a
    #     table that is grouped at the Family taxonomic level)
    #     :param base:
    #     :param taxonomyMap:
    #     :param itemsOfInterest:
    #     :param level:
    #     :return:
    #     """
    #     otus = {}
    #     taxa_specific_to_otus = {}
    #     otu_to_taxa_specific = {}
    #     for otu, classification in taxonomyMap.items():
    #         if 0 <= int(level) < len(classification):
    #             if itemsOfInterest == "All" or itemsOfInterest == "mian-select-all" or classification[int(level)] in itemsOfInterest:
    #                 otus[otu] = 1
    #                 otu_to_taxa_specific[otu] = classification[int(level)]
    #
    #                 if classification[int(level)] not in taxa_specific_to_otus:
    #                     taxa_specific_to_otus[classification[int(level)]] = [otu]
    #                 else:
    #                     taxa_specific_to_otus[classification[int(level)]].append(otu)
    #         else:
    #             # OTU level
    #             if int(level) == -2 or itemsOfInterest == "All" or itemsOfInterest == "mian-select-all" or otu in itemsOfInterest:
    #                 otus[otu] = 1
    #                 otu_to_taxa_specific[otu] = otu
    #
    #                 if otu not in taxa_specific_to_otus:
    #                     taxa_specific_to_otus[otu] = [otu]
    #                 else:
    #                     taxa_specific_to_otus[otu].append(otu)
    #
    #     new_otu_table = []
    #     relevant_cols = {}
    #
    #     i = 0
    #     while i < len(base):
    #         if i == 0:
    #             # Header row
    #             # Ignores the first column (sample ID)
    #
    #             newRow = []
    #             j = 0
    #             while j < OTU_START_COL:
    #                 newRow.append(base[i][j])
    #                 relevant_cols[j] = 1
    #                 j += 1
    #
    #             j = OTU_START_COL
    #             while j < len(base[i]):
    #                 if base[i][j] in otus:
    #                     newRow.append(base[i][j])
    #                     relevant_cols[j] = 1
    #                 j += 1
    #             new_otu_table.append(newRow)
    #         else:
    #             newRow = []
    #             j = 0
    #             while j < len(base[i]):
    #                 if j in relevant_cols:
    #                     newRow.append(base[i][j])
    #                 j += 1
    #             new_otu_table.append(newRow)
    #         i += 1
    #     base = new_otu_table
    #
    #     # Merge the OTUs at the same taxa level
    #     otuToColNum = {}
    #     uniqueSpecificTax = []
    #     j = OTU_START_COL
    #     while j < len(base[0]):
    #         otuToColNum[base[0][j]] = j
    #         if otu_to_taxa_specific[base[0][j]] not in uniqueSpecificTax:
    #             uniqueSpecificTax.append(otu_to_taxa_specific[base[0][j]])
    #         j += 1
    #
    #     newBase = []
    #     i = 0
    #     while i < len(base):
    #         newRow = []
    #         j = 0
    #         while j < OTU_START_COL:
    #             newRow.append(base[i][j])
    #             j += 1
    #
    #         for specificTaxa in uniqueSpecificTax:
    #             if i > 0:
    #                 relevantOTUs = taxa_specific_to_otus[specificTaxa]
    #                 tot = 0
    #                 for relevantOTU in relevantOTUs:
    #                     if relevantOTU in otuToColNum:
    #                         tot += float(base[i][otuToColNum[relevantOTU]])
    #                 newRow.append(tot)
    #             else:
    #                 newRow.append(specificTaxa)
    #         i += 1
    #         newBase.append(newRow)
    #     base = newBase
    #
    #     return base
    #
    #
    #
    # @staticmethod
    # def get_relevant_otus(taxonomy_map, level, items_of_interest):
    #     """
    #
    #     :param taxonomy_map:
    #     :param level:
    #     :param items_of_interest:
    #     :return:
    #     """
    #     otus = {}
    #     for otu, classification in taxonomy_map.items():
    #         if 0 <= int(level) < len(classification):
    #             if classification[int(level)] in items_of_interest:
    #                 otus[otu] = 1
    #         elif int(level) == -1:
    #             if otu in items_of_interest:
    #                 otus[otu] = 1
    #         else:
    #             otus[otu] = 1
    #
    #     return otus
    #
    # @staticmethod
    # def get_relevant_cols(otu_table, relevant_otus):
    #     """
    #
    #     :param otu_table:
    #     :param relevant_otus:
    #     :return:
    #     """
    #     cols = {}
    #     j = OTU_START_COL
    #     while j < len(otu_table[0]):
    #         if otu_table[0][j] in relevant_otus:
    #             cols[j] = 1
    #         j += 1
    #     return cols
