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
            logger.info("Subsample type is auto")
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
                subsample_to = OTUTableSubsampler.__get_min_depth(base)

        elif subsample_type == SUBSAMPLE_TYPE_MANUAL:
            logger.info("Subsample type is manual")
            if str(manual_subsample_to).isdigit():
                subsample_to = int(manual_subsample_to)
            else:
                logger.error("Provided manual_subsample_to of " + str(manual_subsample_to) + " is not valid")
                raise ValueError("Provided subsample value is not valid")

        elif subsample_type == SUBSAMPLE_TYPE_DISABLED:
            # Just copy the raw data table to the subsampled table location
            logger.info("Subsample type is disabled")
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
            if subsample_type == SUBSAMPLE_TYPE_MANUAL and sum(row) < subsample_to:
                # Any row with fewer sequences than the requested depth will be omitted
                samples_removed.append(sample_labels[i])
            else:
                row = subsample_counts(row, subsample_to)
                subsampled_base.append(row)
                subsampled_sample_labels.append(sample_labels[i])
            i += 1

        logger.info("Finished basic subsampling")

        # Find any columns which now only have 0 values
        zero_column_mask = OTUTableSubsampler.__get_zero_columns(subsampled_base)

        # To conserve space, remove all OTUs that no longer have any associated values while writing new
        # subsampled OTU table
        with open(subsampled_table_path, 'w') as f:
            output_tsv = csv.writer(f, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in subsampled_base:
                processed_row = []
                j = 0
                while j < len(row):
                    if j not in zero_column_mask:
                        processed_row.append(row[j])
                    j += 1
                output_tsv.writerow(processed_row)

        subsampled_headers = []
        otus_removed = {}
        j = 0
        while j < len(headers):
            if j in zero_column_mask:
                otus_removed[headers[j]] = 1
            else:
                subsampled_headers.append(headers[j])
            j += 1

        logger.info("Finished writing CSV")

        labels = [subsampled_headers, subsampled_sample_labels]
        DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)

        return subsample_to, otus_removed, samples_removed

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
            total = sum(base[i])
            if last_total > -1 and last_total != total:
                return -1
            last_total = total
            i += 1
        return last_total

    @staticmethod
    def __get_min_depth(base):
        """
        Returns the sum of the row with the min sum
        :param self:
        :param base:
        :return:
        """
        min = -1
        i = 0
        while i < len(base):
            total = sum(base[i])
            if min == -1 or total < min:
                min = total
            i += 1
        return min

    @staticmethod
    def __get_zero_columns(base):
        """
        Returns column indices which have sum of zero
        :param self:
        :param base:
        :return:
        """
        zero_columns = {}
        j = 0
        while j < len(base[0]):
            is_zero = True
            i = 0
            while i < len(base):
                if base[i][j] != 0:
                    is_zero = False
                    break
                i += 1
            if is_zero:
                zero_columns[j] = True
            j += 1
        return zero_columns