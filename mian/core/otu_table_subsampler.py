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
    SUBSAMPLED_OTU_TABLE_FILENAME, RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME
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
    def subsample_otu_table(user_id, pid, subsample_type, manual_subsample_to, base, headers, sample_labels, output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME, output_otu_labels_file_name=SUBSAMPLED_OTU_TABLE_LABELS_FILENAME):
        """
        Subsamples the OTU table to the size of the smallest sample if subsample_to < 1. Otherwise, subsample
        the OTU table to the specified value
        :param subsample_type:
        :param subsample_to:
        :return:
        """

        project_dir = os.path.join(OTUTableSubsampler.DATA_DIRECTORY, user_id)
        project_dir = os.path.join(project_dir, pid)
        subsampled_table_path = os.path.join(project_dir, output_otu_file_name)

        if subsample_type == SUBSAMPLE_TYPE_AUTO:
            current_subsampled_depth = OTUTableSubsampler.__get_subsampled_depth(base)
            if current_subsampled_depth > -1:
                # Check if the table is already subsampled.
                # If so, we just need to copy the raw table to the subsampled table location
                logger.error("Table is already subsampled to a depth of " + str(current_subsampled_depth))
                labels = [headers, sample_labels]
                DataIO.table_to_tsv(base, user_id, pid, output_otu_file_name)
                DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)
                return current_subsampled_depth, {}, []
            else:
                # Sums each sample row to find the row with the smallest sum
                # TODO: Bad input data may have very small row sum
                subsample_to = np.sum(base, axis=1).min().item()

        elif subsample_type == SUBSAMPLE_TYPE_MANUAL:
            if str(manual_subsample_to).isdigit():
                subsample_to = int(manual_subsample_to)
            else:
                logger.error("Provided manual_subsample_to of " + str(manual_subsample_to) + " is not valid")
                raise ValueError("Provided subsample value is not valid")

        elif subsample_type == SUBSAMPLE_TYPE_DISABLED:
            # Just copy the raw data table to the subsampled table location
            logger.error("Subsampling disabled")
            labels = [headers, sample_labels]
            DataIO.table_to_tsv(base, user_id, pid, output_otu_file_name)
            DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)
            return 0, {}, []
        else:
            logger.error("Invalid action selected")
            raise NotImplementedError("Invalid action selected")

        logger.info("Subsampling OTU table to " + str(subsample_to) + " using type " + str(subsample_type))


        samples_removed = []
        subsampled_base = []
        subsampled_sample_labels = []
        i = 0
        for row in base:
            if np.sum(row) < subsample_to:
                # Any row with fewer sequences than the requested depth will be omitted
                samples_removed.append(sample_labels[i])
            else:
                row = subsample_counts(row, subsample_to)
                subsampled_base.append(row)
                subsampled_sample_labels.append(sample_labels[i])
            i += 1

        subsampled_base = np.array(subsampled_base)

        # Find any columns which now only have 0 values
        non_zero_column_mask = ~np.all(subsampled_base == 0, axis=0)

        # To conserve space, remove all OTUs that no longer have any associated values while writing new
        # subsampled OTU table
        with open(subsampled_table_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in subsampled_base:
                processed_row = []
                j = 0
                while j < len(row):
                    if non_zero_column_mask[j]:
                        processed_row.append(row[j])
                    j += 1
                output_tsv.writerow(processed_row)

        subsampled_headers = []
        otus_removed = {}
        j = 0
        while j < len(headers):
            if not non_zero_column_mask[j]:
                otus_removed[headers[j]] = 1
            else:
                subsampled_headers.append(headers[j])
            j += 1

        labels = [subsampled_headers, subsampled_sample_labels]
        DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)

        return subsample_to, otus_removed, samples_removed


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
        i = 0
        while i < len(base):
            total = 0
            j = 0
            while j < len(base[i]):
                total += float(base[i][j])
                j += 1
            if last_total > -1 and last_total != total:
                return -1
            last_total = total
            i += 1
        return last_total
