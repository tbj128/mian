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
    SUBSAMPLED_OTU_TABLE_FILENAME, BIOM_FILENAME, SAMPLE_METADATA_FILENAME, \
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
SAMPLE_METADATA_ERROR = -5
OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR = -7

class ProjectManager(object):
    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def __init__(self, user_id):
        self.user_id = user_id

    def create_project_from_tsv(self, project_name, otu_filename, sample_metadata_filename, subsample_type="auto", subsample_to=0):

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
        base = np.zeros(shape=(num_samples, num_otus), dtype=float)

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
                    base[row - row_offset][col - col_offset] = float(base_arr[row][col])
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
