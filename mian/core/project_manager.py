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

import numpy as np
import scipy.sparse as sparse

from mian.core.data_io import DataIO
from mian.core.otu_table_subsampler import OTUTableSubsampler
from mian.core.constants import RAW_OTU_TABLE_FILENAME, \
    SUBSAMPLED_OTU_TABLE_FILENAME, BIOM_FILENAME, TAXONOMY_FILENAME, SAMPLE_METADATA_FILENAME, \
    RAW_OTU_TABLE_LABELS_FILENAME, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME, SUBSAMPLE_TYPE_DISABLED, PHYLOGENETIC_FILENAME, \
    GENE_FILENAME, GENE_LABELS_FILENAME, SUBSAMPLE_TYPE_CSS
import csv
import os
import re
import logging
import shutil
from biom import load_table

from mian.model.map import Map
from mian.model.otu_table import OTUTable
from mian.model.user_request import UserRequest

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
OTU_DATATYPE_ERROR = -8


class ProjectManager(object):
    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def __init__(self, user_id):
        self.user_id = user_id

    def get_file_for_download(self, project_name, type):
        if type == "phylogenetic":
            return DataIO.text_from_path(self.user_id, project_name, PHYLOGENETIC_FILENAME, replace_newlines=False)
        if type == "gene":
            return DataIO.text_from_path(self.user_id, project_name, GENE_FILENAME, replace_newlines=False)
        elif type == "sample_metadata":
            return DataIO.tsv_to_table(self.user_id, project_name, SAMPLE_METADATA_FILENAME)
        elif type == "taxonomy":
            return DataIO.tsv_to_table(self.user_id, project_name, TAXONOMY_FILENAME)
        elif type == "biom":
            return DataIO.text_from_path(self.user_id, project_name, BIOM_FILENAME, replace_newlines=False)
        elif type == "otu":
            table = DataIO.load_sparse(self.user_id, project_name, RAW_OTU_TABLE_FILENAME).toarray()
            labels = DataIO.tsv_to_table(self.user_id, project_name, RAW_OTU_TABLE_LABELS_FILENAME)
            new_headers = ["Sample Labels"]
            new_headers.extend(labels[0])
            full_table = [new_headers]
            i = 0
            while i < table.shape[0]:
                new_row = [labels[1][i] if i < len(labels[1]) else ""]
                new_row.extend(table[i].tolist())
                full_table.append(new_row)
                i += 1
            return full_table
        elif type == "otu_subsampled":
            table = DataIO.load_sparse(self.user_id, project_name, SUBSAMPLED_OTU_TABLE_FILENAME).toarray()
            labels = DataIO.tsv_to_table(self.user_id, project_name, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)
            new_headers = ["Sample Labels"]
            new_headers.extend(labels[0])
            full_table = [new_headers]
            i = 0
            while i < table.shape[0]:
                new_row = [labels[1][i] if i < len(labels[1]) else ""]
                new_row.extend(table[i].tolist())
                full_table.append(new_row)
                i += 1
            return full_table
        else:
            return []

    def get_filtering_info(self, pid, sampleFilter, sampleFilterRole, sampleFilterVals):
        """
        Returns information that will tell the user what samples will be removed and what the subsample value would be
        :param pid:
        :param sampleFilter:
        :param sampleFilterRole:
        :param sampleFilterVals:
        :return:
        """
        user_request = UserRequest(self.user_id, pid, "", "", "",
                                   "", [], sampleFilter, sampleFilterRole,
                                   sampleFilterVals, 0, "")
        map = Map(self.user_id, pid)

        table = OTUTable(self.user_id, pid, use_raw=True, use_sparse=True)
        orig_base = table.get_table()
        orig_headers = table.get_headers()
        orig_sample_labels = table.get_sample_labels()
        base, headers, sample_labels = table.filter_otu_table_by_metadata(orig_base, orig_headers, orig_sample_labels, user_request)
        initial_samples_removed = set(orig_sample_labels) - set(sample_labels)

        has_float = map.matrix_type == "float"
        min_sample_row_sum = base.sum(axis=1).min()
        orig_row_sums = orig_base.sum(axis=1).tolist()

        samples = {}
        i = 0
        while i < orig_base.shape[0]:
            row_sum = orig_row_sums[i]
            samples[orig_sample_labels[i]] = {
                "row_sum": row_sum,
                "removed": orig_sample_labels[i] in initial_samples_removed
            }
            i += 1

        return {
            "samples": samples,
            "min_sample_val": min_sample_row_sum.item(),
            "has_float": has_float
        }


    def stage_project_from_tsv(self, project_name, otu_filename, taxonomy_filename, sample_metadata_filename,
                                gene_filename, phylogenetic_filename):
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
        if phylogenetic_filename != "":
            os.rename(os.path.join(user_staging_dir, phylogenetic_filename),
                      os.path.join(project_dir, PHYLOGENETIC_FILENAME))

        sample_ids_from_sample_metadata = {}
        sample_metadata = DataIO.tsv_to_table(self.user_id, pid, SAMPLE_METADATA_FILENAME, accept_empty_headers=False)

        i = 0
        while i < len(sample_metadata):
            if i > 0:
                if len(sample_metadata[i]) > 0:
                    sample_ids_from_sample_metadata[sample_metadata[i][0]] = 1
            i += 1

        logger.info("Beginning to load the OTU table")
        base_arr = DataIO.tsv_to_table_from_path(os.path.join(user_staging_dir, otu_filename),
                                                 accept_empty_headers=False)

        # Processes the uploaded OTU file by removing unnecessary columns and extracting the headers and sample labels
        try:
            logger.info("Beginning to process the OTU table")
            base, headers, sample_labels, matrix_type = self.__process_base(self.user_id, pid, base_arr)
        except ValueError:
            logger.exception("OTU file contains non-integers")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return OTU_DATATYPE_ERROR, ""
        except:
            logger.exception("Invalid OTU file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return OTU_ERROR, ""

        # Processes the gene file (if necessary) by extracting the gene labels, transposing, and validating that the
        # correct number of sample labels are present
        if gene_filename != "":
            self.__process_gene_expression(self.user_id, pid, sample_labels, os.path.join(user_staging_dir, gene_filename))

        # Processes the taxonomy file by decomposing string-based taxonomies into tab separated format (if applicable)
        try:
            logger.info("Beginning to process the taxonomy file")
            otus_from_taxonomy = self.__process_taxonomy_file(self.user_id, pid)
        except:
            logger.exception("Invalid taxonomy file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return TAXONOMY_ERROR, ""

        # Validates that the uploaded files are valid
        logger.info("Validating the OTU table")
        missing_headers = self.__validate_otu_table_headers(headers, otus_from_taxonomy)
        if len(missing_headers) > 0:
            return OTU_HEADER_NOT_IN_TAXONOMY_ERROR, ", ".join(missing_headers)
        missing_labels = self.__validate_otu_table_sample_labels(sample_labels, sample_ids_from_sample_metadata)
        if len(missing_labels) > 0:
            if missing_labels[0].lower().startswith("otu"):
                return OTU_ERROR, ""
            else:
                return OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR, ", ".join(missing_labels)

        # Creates map.txt file
        logger.info("Creating the map.txt file")
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.orig_otu_table_name = otu_filename
        map_file.orig_sample_metadata_name = sample_metadata_filename
        map_file.orig_taxonomy_name = taxonomy_filename
        map_file.orig_phylogenetic_name = phylogenetic_filename
        map_file.orig_gene_name = gene_filename
        map_file.matrix_type = matrix_type
        map_file.num_samples = len(sample_labels)
        map_file.num_otus = len(headers)
        map_file.save()

        return OK, pid


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

        is_mothur = False
        if base_arr[0][0] == "label" and base_arr[0][2] == "numOtus":
            # Input file is mothur - we need to delete unnecessary "label" and "numOtus" columns
            is_mothur = True

        base = []

        matrix_type = "int"

        # Adds the numeric values into the base np array
        col_offset = 3 if is_mothur else 1
        row_offset = 1
        row = row_offset
        while row < len(base_arr):
            new_row = []
            col = col_offset
            while col < len(base_arr[row]):
                if base_arr[row][col] == "":
                    # Empty values will default to zero
                    new_row.append(0)
                else:
                    val = float(base_arr[row][col])
                    if val.is_integer():
                        new_row.append(int(float(base_arr[row][col])))
                    else:
                        new_row.append(float(base_arr[row][col]))
                        matrix_type = "float"
                col += 1
            base.append(new_row)
            row += 1

        headers = base_arr[0][col_offset:]

        sample_labels = []

        sample_col = 1 if is_mothur else 0
        row = 1
        while row < len(base_arr):
            sample_labels.append(base_arr[row][sample_col])
            row += 1

        labels = [headers, sample_labels]

        DataIO.table_to_npz(sparse.csr_matrix(base), user_id, pid, output_raw_otu_file_name)
        DataIO.table_to_tsv(labels, user_id, pid, output_raw_otu_labels_file_name)

        return base, headers, sample_labels, matrix_type


    def __process_gene_expression(self, user_id, pid, sample_labels, raw_gene_file_path):
        gene_table = DataIO.tsv_to_table_from_path(raw_gene_file_path)

        # Validate that the gene table has all the samples
        # Samples are in the first row of the raw input
        #
        actual_sample_labels = {}
        for actual_sample_label in gene_table[0]:
            actual_sample_labels[actual_sample_label] = True
        for sample_label in sample_labels:
            if sample_label not in actual_sample_labels:
                raise AssertionError("The gene expression file is missing a sample label")

        # Extract the sample labels and genes and transpose the table
        base = []
        sample_labels = gene_table[0][1:]
        headers = []
        i = 0
        for row in gene_table:
            if i > 0:
                headers.append(row[0])
                new_row = []
                j = 0
                for col in row:
                    if j > 0:
                        new_row.append(float(col))
                    j += 1
                base.append(new_row)
            i += 1

        base = np.array(base).transpose().tolist()

        sample_id_to_row = {}
        i = 0
        while i < len(sample_labels):
            sample_id_to_row[sample_labels[i]] = i
            i += 1
        new_base = []
        for orig_sample_label in sample_labels:
            new_base.append(base[sample_id_to_row[orig_sample_label]])

        labels = [headers, sample_labels]

        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)
        gene_table_path = os.path.join(project_dir, GENE_FILENAME)
        gene_labels_path = os.path.join(project_dir, GENE_LABELS_FILENAME)

        DataIO.table_to_tsv(new_base, user_id, pid, gene_table_path)
        DataIO.table_to_tsv(labels, user_id, pid, gene_labels_path)


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
                    if len(taxonomy_table[row]) > 1:
                        taxonomy_line = taxonomy_table[row][1]
                        taxonomy_type = self.get_taxonomy_type(taxonomy_line)
                        taxonomy_arr = self.process_taxonomy_line(taxonomy_type, taxonomy_line)

                        new_row = [taxonomy_table[row][0]] + taxonomy_arr
                        new_taxonomy_table.append(new_row)
                    row += 1
            DataIO.table_to_tsv(new_taxonomy_table, user_id, pid, TAXONOMY_FILENAME)

        return otus_from_taxonomy_file

    def stage_project_from_biom(self, project_name, biom_name, sample_metadata_filename, gene_filename,
                                phylogenetic_filename):
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

            # Renames the uploaded file to a standard file schema and moves to the project directory
            biom_base_staging_dir = os.path.join(ProjectManager.STAGING_DIRECTORY, self.user_id)
            biom_staging_dir = os.path.join(biom_base_staging_dir, biom_name)
            biom_project_dir = os.path.join(project_dir, BIOM_FILENAME)
            os.rename(biom_staging_dir, biom_project_dir)
            logger.info("Moved " + str(biom_staging_dir) + " to " + str(biom_project_dir))

            # Move the sample metadata to the correction location
            orig_sample_metadata_filename = ""
            if sample_metadata_filename != "":
                os.rename(os.path.join(biom_base_staging_dir, sample_metadata_filename),
                          os.path.join(project_dir, SAMPLE_METADATA_FILENAME))

            # Move the phylogenetic tree to the correction location
            if phylogenetic_filename != "":
                os.rename(os.path.join(biom_base_staging_dir, phylogenetic_filename),
                          os.path.join(project_dir, PHYLOGENETIC_FILENAME))

            # Extracts the OTU table from the biom file and saves the raw OTU file
            biom_path = os.path.join(project_dir, BIOM_FILENAME)

            logger.info("Loading biom into table")
            biom_table = load_table(biom_path)
            logger.info("Transposing biom")
            biom_table = biom_table.transpose()
            logger.info("Converting biom to intermediate TSV file " + biom_path)

            # Processes the uploaded OTU file by removing unnecessary columns and extracting the headers and sample labels
            try:
                headers, sample_labels, matrix_type = self.__save_biom_table_as_tsv(self.user_id, pid, biom_table)
            except ValueError:
                logger.exception("OTU file contains non-integers")
                # Removes the project directory since the files in it are invalid
                shutil.rmtree(project_dir, ignore_errors=True)
                return OTU_DATATYPE_ERROR, ""

            logger.info("Processed biom TSV file " + biom_path)
            num_headers = len(headers)
            num_samples = len(sample_labels)

            # Create Sample Metadata File
            logger.info("Creating sample metadata file")
            sample_metadata_path = os.path.join(project_dir, SAMPLE_METADATA_FILENAME)
            sample_metadata = biom_table.metadata(None, 'observation')
            sample_ids = biom_table.ids('observation')
            sample_ids_from_sample_metadata = {}

            if sample_metadata_filename == "" and sample_metadata is not None and len(sample_metadata) > 1 and len(sample_metadata[0]) > 1:
                # Write out the sample metadata from the biom file
                # Based on user feedback, we will prefer the uploaded sample metadata over the biom sample metadata
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
            else:
                if sample_metadata_filename != "":
                    # Maybe the user uploaded the sample metadata themselves, so we'll use that instead
                    sample_metadata = DataIO.tsv_to_table(self.user_id, pid, SAMPLE_METADATA_FILENAME, accept_empty_headers=False)
                    i = 0
                    while i < len(sample_metadata):
                        if i > 0:
                            if len(sample_metadata[i]) > 0:
                                sample_ids_from_sample_metadata[sample_metadata[i][0]] = 1
                        i += 1

                    logger.info("Finished reading user uploaded sample metadata file")
                else:
                    # User did not upload a sample metadata file and the biom file had not sample metadata so
                    # we will just use the sample labels as-is (ie. treat it like there's no sample metadata)
                    with open(sample_metadata_path, 'w') as f:
                        output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                        output_tsv.writerow(["SampleID"])

                        i = 0
                        while i < len(sample_labels):
                            sample_ids_from_sample_metadata[sample_labels[i]] = 1
                            output_tsv.writerow([sample_labels[i]])
                            i += 1
            logger.info("Validating OTU sample labels")
            missing_labels = self.__validate_otu_table_sample_labels(sample_labels, sample_ids_from_sample_metadata)
            if len(missing_labels) > 0:
                logger.info("Missing the following labels: {}".format(missing_labels))
                return OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR, ", ".join(missing_labels)

            # Generates BIOM File
            # Processes the gene file (if necessary) by extracting the gene labels, transposing, and validating that the
            # correct number of sample labels are present
            if gene_filename != "":
                self.__process_gene_expression(self.user_id, pid, sample_labels,
                                               os.path.join(biom_base_staging_dir, gene_filename))

            # Generates Taxonomy File
            logger.info("Creating taxonomy file")
            otu_metadata = biom_table.metadata(None, 'sample')
            if otu_metadata == None:
                # Mian requires the metadata file to function correctly
                raise ValueError("Taxonomy data file is required")

            otu_ids = biom_table.ids('sample')
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
                    row_data = [otu_id] + self.process_taxonomy_line(taxonomy_type, k[taxonomy_key])
                    for key, value in sorted(k.items()):
                        if key != taxonomy_key:
                            row_data.append(value)
                    output_tsv.writerow(row_data)
                    otu_index += 1

            # Creates map.txt file
            logger.info("Creating the map.txt file")
            map_file = Map(self.user_id, pid)
            map_file.project_name = project_name
            map_file.orig_biom_name = biom_name
            map_file.orig_sample_metadata_name = sample_metadata_filename
            map_file.orig_phylogenetic_name = phylogenetic_filename
            map_file.orig_gene_name = gene_filename
            map_file.matrix_type = matrix_type
            map_file.num_samples = num_samples
            map_file.num_otus = num_headers
            map_file.save()

            return OK, pid
        except:
            logger.exception("Error while processing the file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return BIOM_ERROR, ""


    def create_project(self, pid, sampleFilter, sampleFilterRole, sampleFilterVals,
                       subsample_type="auto", subsample_to=0, low_expression_filtering_type="none",
                       low_expression_filtering_count=0, low_expression_filtering_prevalence=0):

        map_file = Map(self.user_id, pid)

        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, self.user_id)
        project_dir = os.path.join(project_dir, pid)

        try:
            user_request = UserRequest(self.user_id, pid, "", "", "",
                                       "", [], sampleFilter, sampleFilterRole,
                                       sampleFilterVals, 0, "")

            if map_file.matrix_type == "float":
                # Float-type matrix cannot be subsampled
                subsample_type = SUBSAMPLE_TYPE_DISABLED

            table = OTUTable(self.user_id, pid, use_raw=True, use_np=False, use_sparse=True)
            orig_base = table.get_table()
            orig_headers = table.get_headers()
            orig_sample_labels = table.get_sample_labels()

            low_expression_otus_removed = 0
            if low_expression_filtering_type == "filter-before":
                logger.info(f"Low-expression filtering before normalization - shape {orig_base.shape}")
                orig_num_otus = orig_base.shape[1]
                orig_base, orig_headers, orig_sample_labels = table.filter_out_low_count(orig_base, orig_headers, orig_sample_labels, low_expression_filtering_count, low_expression_filtering_prevalence)
                logger.info(f"Post low-expression filtering - shape {orig_base.shape}")
                low_expression_otus_removed = orig_num_otus - orig_base.shape[1]

            base, headers, sample_labels = table.filter_otu_table_by_metadata(orig_base, orig_headers, orig_sample_labels,
                                                                              user_request)

            initial_samples_removed = list(set(orig_sample_labels) - set(sample_labels))

            # Subsamples the raw OTU file
            base, subsample_to, subsampled_headers, subsampled_sample_labels = OTUTableSubsampler.subsample_otu_table(base=base,
                                                                                                                      headers=headers,
                                                                                                                      sample_labels=sample_labels,
                                                                                                                      subsample_type=subsample_type,
                                                                                                                      manual_subsample_to=subsample_to)

            logger.info("Subsampled file")

            if low_expression_filtering_type == "filter-after":
                logger.info(f"Low-expression filtering after normalization - shape {base.shape}")
                orig_num_otus = base.shape[1]
                base, subsampled_headers, subsampled_sample_labels = table.filter_out_low_count(base, subsampled_headers, subsampled_sample_labels, low_expression_filtering_count, low_expression_filtering_prevalence)
                logger.info(f"Post low-expression filtering - shape {base.shape}")
                low_expression_otus_removed = orig_num_otus - base.shape[1]

            # Saves output file
            labels = [subsampled_headers, subsampled_sample_labels]
            DataIO.table_to_npz(base, self.user_id, pid, SUBSAMPLED_OTU_TABLE_FILENAME)
            DataIO.table_to_tsv(labels, self.user_id, pid, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)

            # Updates map.txt file
            map_file.subsampled_type = subsample_type
            map_file.subsampled_value = subsample_to
            map_file.subsampled_removed_samples = initial_samples_removed
            map_file.low_expression_filter_otus_removed = low_expression_otus_removed
            map_file.low_expression_filter_type = low_expression_filtering_type
            map_file.low_expression_filter_count = low_expression_filtering_count
            map_file.low_expression_filter_prevalence = low_expression_filtering_prevalence
            map_file.num_samples = len(subsampled_sample_labels)
            map_file.num_otus = len(subsampled_headers)
            map_file.save()

            return pid, ""
        except Exception as e:
            print(e)
            logger.exception("Error while processing the file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return GENERAL_ERROR, ""


    def __save_biom_table_as_tsv(self, user_id, pid, biom_table, raw_table_path=RAW_OTU_TABLE_FILENAME, output_raw_otu_labels_file_name=RAW_OTU_TABLE_LABELS_FILENAME):
        headers = biom_table._sample_ids.tolist()
        sample_labels = biom_table._observation_ids.tolist()

        logger.info("Finished table.to_tsv")

        matrix_type = "int"

        # Converts the TSV string to an array
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_path = os.path.join(project_dir, raw_table_path)
        sparse.save_npz(csv_path, biom_table.matrix_data.astype(dtype=int))

        logger.info("Finished loading to intermediate table")

        labels = [headers, sample_labels]
        DataIO.table_to_tsv(labels, user_id, pid, output_raw_otu_labels_file_name)

        return headers, sample_labels, matrix_type

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
        base = DataIO.load_sparse(self.user_id, pid, RAW_OTU_TABLE_FILENAME)

        # Convert to int as you can only subsample int tables
        base = base.astype(int)

        labels = DataIO.tsv_to_table(self.user_id, pid, RAW_OTU_TABLE_LABELS_FILENAME)
        base, subsample_value, subsampled_headers, subsampled_sample_labels = OTUTableSubsampler.subsample_otu_table(subsample_type=subsample_type,
                                                                                                                     manual_subsample_to=subsample_to,
                                                                                                                     base=base,
                                                                                                                     headers=labels[0],
                                                                                                                     sample_labels=labels[1])

        if isinstance(subsample_value, (np.generic)):
            subsample_value = subsample_value.item()

        # Saves output file
        labels = [subsampled_headers, subsampled_sample_labels]
        DataIO.table_to_npz(base, self.user_id, pid, SUBSAMPLED_OTU_TABLE_FILENAME)
        DataIO.table_to_tsv(labels, self.user_id, pid, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)

        # Updates the map.txt file
        map_file = Map(self.user_id, pid)
        map_file.subsampled_type = subsample_type
        map_file.subsampled_value = subsample_value
        map_file.subsampled_removed_samples = samples_removed
        map_file.save()

        return subsample_value
