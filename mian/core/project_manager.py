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

from mian.core.data_io import DataIO
from mian.core.constants import RAW_TABLE_FILENAME, SAMPLE_METADATA_FILENAME, RAW_TABLE_LABELS_FILENAME
import os
import logging
import shutil

from mian.model.map import Map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OK = 0
GENERAL_ERROR = -1
OTU_ERROR = -3
SAMPLE_METADATA_ERROR = -5
OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR = -7

class ProjectManager(object):
    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")
    STAGING_DIRECTORY = os.path.join(DATA_DIRECTORY, "staging")

    def __init__(self, user_id):
        self.user_id = user_id

    def create_project_from_tsv(self, project_name, filename, sample_metadata_filename):

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

        base_arr = DataIO.tsv_to_table_from_path(os.path.join(user_staging_dir, filename))

        # Processes the uploaded file by removing unnecessary columns and extracting the headers and sample labels
        try:
            base, headers, sample_labels, samples_removed = self.__process_base(self.user_id, pid, base_arr, sample_ids_from_sample_metadata)
        except:
            logger.exception("Invalid OTU file format")
            # Removes the project directory since the files in it are invalid
            shutil.rmtree(project_dir, ignore_errors=True)
            return OTU_ERROR, ""

        # Creates map.txt file
        map_file = Map(self.user_id, pid)
        map_file.project_name = project_name
        map_file.table_name = filename
        map_file.sample_metadata_name = sample_metadata_filename
        map_file.save()

        if len(samples_removed) > 0:
            return OTU_LABEL_NOT_IN_SAMPLE_METADATA_ERROR, ", ".join(samples_removed)
        else:
            return pid, ""

    def __process_base(self, user_id, pid, base_arr, sample_ids_from_sample_metadata, output_raw_file_name=RAW_TABLE_FILENAME,
                       output_raw_labels_file_name=RAW_TABLE_LABELS_FILENAME):
        '''
        Takes a CSV-separated base file and extracts the header and the sample labels from the file.
        Returns an gene file (with only numeric values) and corresponding table header and sample labels
        :param user_id:
        :param pid:
        :return:
        '''

        project_dir = os.path.join(ProjectManager.DATA_DIRECTORY, user_id)
        project_dir = os.path.join(project_dir, pid)
        raw_table_path = os.path.join(project_dir, output_raw_file_name)
        raw_table_labels_path = os.path.join(project_dir, output_raw_labels_file_name)

        col_offset = 1
        row_offset = 1

        samples_to_remove_map = {}
        samples_to_remove = []
        samples_kept = []
        col = 1
        while col < len(base_arr[0]):
            if base_arr[0][col] not in sample_ids_from_sample_metadata:
                samples_to_remove_map[base_arr[0][col]] = True
                samples_to_remove.append(base_arr[0][col])
            else:
                samples_kept.append(base_arr[0][col])
            col += 1

        base = []

        row = row_offset
        while row < len(base_arr):
            new_row = []
            col = col_offset
            while col < len(base_arr[row]):
                try:
                    if base_arr[0][col] not in samples_to_remove_map:
                        new_row.append(float(base_arr[row][col]))
                except ValueError:
                    # TODO: Handle case where bad input file format
                    logger.exception("Bad table")
                    pass
                col += 1
            base.append(new_row)
            row += 1

        logger.info("Finished extracting numeric values from base")

        # Transpose the table to ensure the samples are rows
        base = list(map(list, zip(*base)))

        logger.info("Finished transposing base")

        headers = []

        sample_col = 0
        row = 1
        while row < len(base_arr):
            headers.append(base_arr[row][sample_col])
            row += 1

        labels = [headers, samples_kept]

        DataIO.table_to_tsv(base, user_id, pid, raw_table_path)
        DataIO.table_to_tsv(labels, user_id, pid, raw_table_labels_path)

        return base, headers, samples_kept, samples_to_remove

    def __validate_gene_table_sample_labels(self, sample_labels, sample_ids_from_metadata):
        missing = []
        for sample_label in sample_labels:
            if sample_label not in sample_ids_from_metadata:
                missing.append(sample_label)
        return missing

