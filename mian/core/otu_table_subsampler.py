# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#

import sys
import numpy as np
import shutil

import matplotlib

from mian.model.otu_table import OTUTable

matplotlib.use('TkAgg')

from mian.core.data_io import DataIO
from mian.core.constants import SUBSAMPLE_TYPE_AUTO, SUBSAMPLE_TYPE_MANUAL, SUBSAMPLE_TYPE_DISABLED, \
    SUBSAMPLED_OTU_TABLE_FILENAME, RAW_OTU_TABLE_FILENAME
import csv
import os
import logging
from skbio.stats import subsample_counts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OTUTableSubsampler(object):

    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")

    @staticmethod
    def subsample_otu_table(user_id, pid, subsample_type, manual_subsample_to, raw_otu_file_name=RAW_OTU_TABLE_FILENAME, output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME):
        """
        Subsamples the OTU table to the size of the smallest sample if subsample_to < 1. Otherwise, subsample
        the OTU table to the specified value
        :param subsample_type:
        :param subsample_to:
        :return:
        """

        project_dir = os.path.join(OTUTableSubsampler.DATA_DIRECTORY, user_id)
        project_dir = os.path.join(project_dir, pid)
        raw_table_path = os.path.join(project_dir, raw_otu_file_name)
        subsampled_table_path = os.path.join(project_dir, output_otu_file_name)

        base = DataIO.tsv_to_table(user_id, pid, raw_otu_file_name)

        if subsample_type == SUBSAMPLE_TYPE_AUTO:
            current_subsampled_depth = OTUTableSubsampler.__get_subsampled_depth(base)
            if current_subsampled_depth > -1:
                # Check if the table is already subsampled.
                # If so, we just need to copy the raw table to the subsampled table location
                logger.error("Table is already subsampled to a depth of " + str(current_subsampled_depth))
                shutil.copyfile(raw_table_path, subsampled_table_path)
                return current_subsampled_depth, {}
            else:
                # Picks the sample with the lowest sequences as the subsample to value
                lowest_sequences = sys.maxsize
                i = 1
                while i < len(base):
                    total = 0
                    j = OTUTable.OTU_START_COL
                    while j < len(base[i]):
                        total += int(float(base[i][j]))
                        j += 1
                    if total < lowest_sequences:
                        lowest_sequences = total
                    i += 1
                subsample_to = lowest_sequences
        elif subsample_type == SUBSAMPLE_TYPE_MANUAL:
            if str(manual_subsample_to).isdigit():
                subsample_to = int(manual_subsample_to)
            else:
                logger.error("Provided manual_subsample_to of " + str(manual_subsample_to) + " is not valid")
                raise ValueError("Provided subsample value is not valid")
        elif subsample_type == SUBSAMPLE_TYPE_DISABLED:
            # Just copy the raw data table to the subsampled table location
            logger.error("Subsampling disabled")
            shutil.copyfile(raw_table_path, subsampled_table_path)
            return 0, {}
        else:
            logger.error("Invalid action selected")
            raise NotImplementedError("Invalid action selected")

        logger.info("Subsampling OTU table " + str(raw_otu_file_name) + " to " + str(subsample_to) + " using type " + str(subsample_type))

        empty_otus = []
        subsampled_base = []
        i = 0
        while i < len(base):
            if i == 0:
                subsampled_base.append(base[i])
                empty_otus = [True] * len(base[i])
            else:
                j = OTUTable.OTU_START_COL
                row = []
                while j < len(base[i]):
                    val = float(base[i][j])
                    row.append(val)
                    if val > 0:
                        empty_otus[j] = False
                    j += 1
                row = np.array(row, dtype=np.int64)
                row = subsample_counts(row, subsample_to)

                # Add back the sample ID
                row = row.tolist()
                row.insert(0, base[i][0])

                subsampled_base.append(row)
            i += 1

        # To conserve space, remove all OTUs that no longer have any associated values while writing new
        # subsampled OTU table
        with open(subsampled_table_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in subsampled_base:
                processed_row = []
                j = OTUTable.OTU_START_COL
                while j < len(row):
                    if not empty_otus[j]:
                        processed_row.append(row[j])
                    j += 1
                processed_row.insert(0, row[OTUTable.SAMPLE_ID_COL])
                output_tsv.writerow(processed_row)

        otus_removed = {}
        j = OTUTable.OTU_START_COL
        while j < len(subsampled_base[0]):
            if empty_otus[j]:
                otus_removed[subsampled_base[0][j]] = 1
            j += 1

        return subsample_to, otus_removed


    @staticmethod
    def get_is_subsampled(userID, projectID):
        base = DataIO.tsv_to_table(userID, projectID, RAW_OTU_TABLE_FILENAME)
        if OTUTableSubsampler.__get_subsampled_depth(base) == -1:
            return False
        else:
            return True

    @staticmethod
    def __get_subsampled_depth(base):
        """
        Returns the depth that the table is subsampled to, or -1 if the table is not subsampled
        :param self:
        :param base:
        :return:
        """
        last_total = -1
        i = 1
        while i < len(base):
            total = 0
            j = OTUTable.OTU_START_COL
            while j < len(base[i]):
                total += float(base[i][j])
                j += 1
            if last_total > -1 and last_total != total:
                return -1
            last_total = total
            i += 1
        return last_total
