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
import numpy as np

from mian.core.data_io import DataIO
from mian.core.otu_table_subsampler import OTUTableSubsampler
from mian.core.constants import RAW_OTU_TABLE_FILENAME, \
    SUBSAMPLED_OTU_TABLE_FILENAME, BIOM_FILENAME, TAXONOMY_FILENAME, SAMPLE_METADATA_FILENAME, \
    RAW_OTU_TABLE_LABELS_FILENAME
import csv
import os
import re
import logging
import shutil
from biom import load_table

from mian.model.map import Map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OK = 0
GENERAL_ERROR = -1
BIOM_ERROR = -2
OTU_ERROR = -3
TAXONOMY_ERROR = -4
SAMPLE_METADATA_ERROR = -5
OTU_HEADER_NOT_IN_TAXONOMY_ERROR = -6
OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR = -7

class ProjectManager(object):
    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def __init__(self, user_id):
        self.user_id = user_id

    def create_project_from_tsv(self, project_name, otu_filename, taxonomy_filename, sample_metadata_filename,
                                subsample_type="auto", subsample_to=0):

        # Creates a directory for this project
        pid = str(uuid.uuid4())
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        else:
            logger.exception("Cannot create project folder")
            raise Exception("Cannot create project folder as it already exists")

        # Renames the uploaded files to a standard file schema and moves to the project directory
        user_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        os.rename(os.path.join(user_staging_dir, taxonomy_filename), os.path.join(project_dir, TAXONOMY_FILENAME))
        os.rename(os.path.join(user_staging_dir, sample_metadata_filename),
                  os.path.join(project_dir, SAMPLE_METADATA_FILENAME))

        sample_ids_from_sample_metadata = {}
        sample_metadata = DataIO.tsv_to_table(self.user_id, pid, SAMPLE_METADATA_FILENAME)
        i = 0
        while i < len(sample_metadata):
            if i > 0:
                sample_ids_from_sample_metadata[sample_metadata[i][0]] = 1
            i += 1


        base_arr = DataIO.tsv_to_table_from_path(os.path.join(user_staging_dir, otu_filename))

        # Processes the uploaded OTU file by removing unnecessary columns and extracting the headers and sample labels
        try:
            base, headers, sample_labels = self.__process_base(self.user_id, pid, base_arr)
        except:
            logger.exception("Invalid OTU file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return OTU_ERROR, ""

        # Processes the taxonomy file by decomposing string-based taxonomies into tab separated format (if applicable)
        try:
            otus_from_taxonomy = self.__process_taxonomy_file(self.user_id, pid)
        except:
            logger.exception("Invalid taxonomy file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return TAXONOMY_ERROR, ""

        # Validates that the uploaded files are valid
        missing_headers = self.__validate_otu_table_headers(headers, otus_from_taxonomy)
        if len(missing_headers) > 0:
            return OTU_HEADER_NOT_IN_TAXONOMY_ERROR, ", ".join(missing_headers)
        missing_labels = self.__validate_otu_table_sample_labels(sample_labels, sample_ids_from_sample_metadata)
        if len(missing_labels) > 0:
            return OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR, ", ".join(missing_labels)

        # Subsamples raw OTU table
        try:
            subsample_value, otus_removed, samples_removed = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                                                    pid=pid,
                                                                                                    base=base,
                                                                                                    headers=headers,
                                                                                                    sample_labels=sample_labels,
                                                                                                    subsample_type=subsample_type,
                                                                                                    manual_subsample_to=subsample_to)
        except:
            logger.exception("Error when subsampling the OTU file")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return OTU_ERROR, ""

        # Creates map.txt file
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.orig_otu_table_name = otu_filename
        map_file.orig_sample_metadata_name = sample_metadata_filename
        map_file.orig_taxonomy_name = taxonomy_filename
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.subsampled_removed_samples = samples_removed
        map_file.save()

        return pid, ""

    def __process_base(self, user_id, pid, base_arr, output_raw_otu_file_name=RAW_OTU_TABLE_FILENAME,
                       output_raw_otu_labels_file_name=RAW_OTU_TABLE_LABELS_FILENAME):
        '''
        Takes a TSV-separated base OTU file and extracts the header and the sample labels from the OTU file.
        Removes unnecessary columns if input is mothur derived file.
        Returns an OTU file (with only numeric values) and corresponding table header and sample labels
        :param user_id:
        :param pid:
        :return:
        '''

        project_dir = os.path.join(OTUTableSubsampler.DATA_DIRECTORY, user_id)
        project_dir = os.path.join(project_dir, pid)
        raw_table_path = os.path.join(project_dir, output_raw_otu_file_name)

        is_mothur = False
        if base_arr[0][0] == "label" and base_arr[0][2] == "numOtus":
            # Input file is mothur - we need to delete unnecessary "label" and "numOtus" columns
            is_mothur = True

        num_samples = len(base_arr) - 1  # Accounts for the header row
        num_otus = len(base_arr[0]) - 1  # Accounts for the sample labels
        if is_mothur:
            num_otus = len(base_arr[0]) - 3  # Accounts for the additional columns mothur adds
        base = np.zeros(shape=(num_samples, num_otus), dtype=int)

        # Adds the numeric values into the base np array
        col_offset = 3 if is_mothur else 1
        row_offset = 1
        row = row_offset
        while row < len(base_arr):
            col = col_offset
            while col < len(base_arr[row]):
                try:
                    # TODO: Validate input format
                    # base[row - row_offset][col - col_offset] = float(base_arr[row][col])
                    base[row - row_offset][col - col_offset] = int(float(base_arr[row][col]))
                except ValueError:
                    # TODO: Handle case where bad input file format
                    logger.exception("Bad OTU table")
                    pass
                col += 1
            row += 1

        headers = base_arr[0][col_offset:]
        sample_labels = []

        sample_col = 1 if is_mothur else 0
        row = 1
        while row < len(base_arr):
            sample_labels.append(base_arr[row][sample_col])
            row += 1

        labels = [headers, sample_labels]

        DataIO.table_to_tsv(base, user_id, pid, raw_table_path)
        DataIO.table_to_tsv(labels, user_id, pid, output_raw_otu_labels_file_name)

        return base, headers, sample_labels

    def __process_taxonomy_file(self, user_id, pid):
        taxonomy_table = DataIO.tsv_to_table(user_id, pid, TAXONOMY_FILENAME)

        new_taxonomy_table = []
        core_taxonomy_table = np.array(taxonomy_table[1:])
        otus_from_taxonomy_file = dict(zip(core_taxonomy_table[:, 0], core_taxonomy_table[:, 0]))

        num_cols = len(taxonomy_table[1])
        if num_cols == 1:
            # Invalid columnar format
            logger.exception("Invalid taxonomy format")
            raise Exception("Invalid taxonomy file format")
        else:
            if taxonomy_table[0][1] == "Size":
                # This is a mothur constaxonomy file so we should delete the Size column
                taxonomy_table = np.array(taxonomy_table)
                taxonomy_table = np.delete(taxonomy_table, 1, 1)

            max_length = 0
            for row in taxonomy_table:
                if len(row) > max_length:
                    max_length = len(row)


            if max_length > 2:
                new_taxonomy_table = taxonomy_table
            else:
                new_taxonomy_table.append(taxonomy_table[0])
                row = 1
                while row < len(taxonomy_table):
                    taxonomy_line = taxonomy_table[row][1]
                    taxonomy_type = self.get_taxonomy_type(taxonomy_line)
                    taxonomy_arr = self.process_taxonomy_line(taxonomy_type, taxonomy_line)

                    new_row = [taxonomy_table[row][0]] + taxonomy_arr
                    new_taxonomy_table.append(new_row)
                    row += 1
            DataIO.table_to_tsv(new_taxonomy_table, user_id, pid, TAXONOMY_FILENAME)

        return otus_from_taxonomy_file

    def create_project_from_biom(self, project_name, biom_name, subsample_type="auto", subsample_to=0):
        """
        Reads a .biom from a provided file location and converts it into a mian-compatible TSV file

        """

        # Creates a directory for this project
        pid = str(uuid.uuid4())
        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        else:
            logger.exception("Cannot create project folder")
            raise Exception("Cannot create project folder as it already exists")

        try:
            status, message = self.__process_biom_file(pid, project_dir, project_name, biom_name, subsample_type, subsample_to)
            if status != OK:
                # Removes the project directory since the files in it are invalid
                shutil.rmtree(project_dir, ignore_errors=True)
                return status, message
            return pid, ""
        except:
            logger.exception("Invalid BIOM file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return BIOM_ERROR, ""

    def __process_biom_file(self, pid, project_dir, project_name, biom_name, subsample_type="auto", subsample_to=0):
        # Renames the uploaded file to a standard file schema and moves to the project directory
        biom_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
        biom_staging_dir = os.path.join(biom_staging_dir, biom_name)
        biom_project_dir = os.path.join(project_dir, BIOM_FILENAME)
        os.rename(biom_staging_dir, biom_project_dir)
        logger.info("Moved " + str(biom_staging_dir) + " to " + str(biom_project_dir))

        # Extracts the OTU table from the biom file and saves the raw OTU file
        biom_path = os.path.join(project_dir, BIOM_FILENAME)

        logger.info("Loading biom into table")
        biom_table = load_table(biom_path)
        logger.info("Converting biom to intermediate TSV file " + biom_path)

        # Processes the uploaded OTU file by removing unnecessary columns and extracting the headers and sample labels
        base, headers, sample_labels = self.__save_biom_table_as_tsv(self.user_id, pid, biom_table)

        logger.info("Processed biom TSV file " + biom_path)

        # Subsamples the raw OTU file
        subsample_to, removed_otus, samples_removed = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                                             pid=pid,
                                                                                             base=base,
                                                                                             headers=headers,
                                                                                             sample_labels=sample_labels,
                                                                                             subsample_type=subsample_type,
                                                                                             manual_subsample_to=subsample_to)

        logger.info("Subsampled TSV file")

        # Create Sample Metadata File
        logger.info("Creating sample metadata file")
        sample_metadata_path = os.path.join(project_dir, SAMPLE_METADATA_FILENAME)
        sample_metadata = biom_table.metadata(None, 'sample')
        sample_ids = biom_table.ids('sample')
        sample_ids_from_sample_metadata = {}
        with open(sample_metadata_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            sample_index = 0
            if sample_metadata is not None:
                for k in sample_metadata:
                    if sample_index == 0:
                        # We will write out the metadata headers at the top of this file
                        headers = ["SampleID"]
                        for key, value in sorted(k.items()):
                            headers.append(key)
                        output_tsv.writerow(headers)

                    sample_id = sample_ids[sample_index]
                    sample_ids_from_sample_metadata[sample_id] = 1
                    row_data = [sample_id]
                    for key, value in sorted(k.items()):
                        # Write out the contents of each metadata
                        row_data.append(value)
                    output_tsv.writerow(row_data)
                    sample_index += 1
            else:
                # There is no sample metadata associated with this biom
                while sample_index < len(sample_ids):
                    if sample_index == 0:
                        headers = ["SampleID"]
                        output_tsv.writerow(headers)
                    sample_id = sample_ids[sample_index]
                    sample_ids_from_sample_metadata[sample_id] = 1
                    row_data = [sample_id]
                    output_tsv.writerow(row_data)
                    sample_index += 1

        missing_labels = self.__validate_otu_table_sample_labels(sample_labels, sample_ids_from_sample_metadata)
        if len(missing_labels) > 0:
            return OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR, ", ".join(missing_labels)


        # Generates Taxonomy File
        logger.info("Creating taxonomy file")
        otu_metadata = biom_table.metadata(None, 'observation')
        if otu_metadata == None:
            # Mian requires the metadata file to function correctly
            raise ValueError("Taxonomy data file is required")

        otu_ids = biom_table.ids('observation')
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
        map_file.subsampled_removed_samples = samples_removed
        map_file.taxonomy_type = taxonomy_type
        map_file.save()

        return OK, ""

    def __save_biom_table_as_tsv(self, user_id, pid, biom_table, raw_table_path=RAW_OTU_TABLE_FILENAME, output_raw_otu_labels_file_name=RAW_OTU_TABLE_LABELS_FILENAME):
        result = biom_table.to_tsv(header_key="",
                              header_value="",
                              metadata_formatter="sc_separated")

        logger.info("Finished table.to_tsv")

        # Converts the TSV string to an array
        f = StringIO(result)
        base_csv = []
        base_csv_reader = csv.reader(f, delimiter='\t', quotechar='|')
        i = 0
        for o in base_csv_reader:
            if i > 0:
                # Ignores the first "Created from biom file" line
                base_csv.append(o)
            i += 1

        num_samples = len(base_csv[0]) - 1  # Accounts for the header row (samples are headers in this case)
        num_otus = len(base_csv) - 1  # Accounts for the sample labels
        intermediate_table = np.zeros(shape=(num_samples, num_otus), dtype=int)
        sample_labels = base_csv[0][1:]
        headers = []

        row = 1
        while row < len(base_csv):
            headers.append(base_csv[row][0])
            col = 1
            while col < len(base_csv[row]):
                # TODO: Validate input format
                # intermediate_table[col - 1][row - 1] = float(base_csv[row][col])
                intermediate_table[col - 1][row - 1] = int(float(base_csv[row][col]))
                col += 1
            row += 1

        logger.info("Finished loading to intermediate table")

        labels = [headers, sample_labels]
        DataIO.table_to_tsv(intermediate_table, user_id, pid, raw_table_path)
        DataIO.table_to_tsv(labels, user_id, pid, output_raw_otu_labels_file_name)

        return intermediate_table, headers, sample_labels

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

    def __validate_otu_table_headers(self, headers, otus_from_taxonomy):
        missing = []
        for header in headers:
            if header not in otus_from_taxonomy:
                missing.append(header)
        return missing

    def __validate_otu_table_sample_labels(self, sample_labels, sample_ids_from_metadata):
        missing = []
        for sample_label in sample_labels:
            if sample_label not in sample_ids_from_metadata:
                missing.append(sample_label)
        return missing

    def modify_subsampling(self, pid, subsample_type="auto", subsample_to=0):
        # Subsamples raw OTU table
        base = DataIO.tsv_to_np_table(self.user_id, pid, RAW_OTU_TABLE_FILENAME)
        labels = DataIO.tsv_to_table(self.user_id, pid, RAW_OTU_TABLE_LABELS_FILENAME)
        subsample_value, otus_removed, samples_removed = OTUTableSubsampler.subsample_otu_table(user_id=self.user_id,
                                                                                                pid=pid,
                                                                                                subsample_type=subsample_type,
                                                                                                manual_subsample_to=subsample_to,
                                                                                                base=base,
                                                                                                headers=labels[0],
                                                                                                sample_labels=labels[1])

        # Updates the map.txt file
        map_file = Map(self.user_id, pid)
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.subsampled_removed_samples = samples_removed
        map_file.save()

        return subsample_value
