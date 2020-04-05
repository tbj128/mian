# ==============================================================================
#
# Utility functions used for data transformation or other common functionality
# @author: tbj128
#
# ==============================================================================

#
# Imports
#

import matplotlib

from biom import Table

matplotlib.use('TkAgg')

from mian.core.data_io import DataIO
from mian.core.constants import SUBSAMPLE_TYPE_AUTO, SUBSAMPLE_TYPE_MANUAL, SUBSAMPLE_TYPE_DISABLED, \
    SUBSAMPLED_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OTUTableSubsampler(object):

    BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Gets the parent folder
    DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, "data")

    @staticmethod
    def subsample_otu_table(user_id, pid, subsample_type, manual_subsample_to, base, headers, sample_labels, output_otu_file_name=SUBSAMPLED_OTU_TABLE_FILENAME, output_otu_labels_file_name=SUBSAMPLED_OTU_TABLE_LABELS_FILENAME, is_biom=False):
        """
        Subsamples the OTU table to the size of the smallest sample if subsample_to < 1. Otherwise, subsample
        the OTU table to the specified value
        :param subsample_type:
        :param subsample_to:
        :return:
        """

        if subsample_type == SUBSAMPLE_TYPE_AUTO:
            logger.info("Subsample type is auto")
            current_subsampled_depth = OTUTableSubsampler.__get_subsampled_depth(base)
            if current_subsampled_depth > -1:
                # Check if the table is already subsampled.
                # If so, we just need to copy the raw table to the subsampled table location
                logger.error("Table is already subsampled to a depth of " + str(current_subsampled_depth))
                labels = [headers, sample_labels]
                DataIO.table_to_npz(base, user_id, pid, output_otu_file_name)
                DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)
                return current_subsampled_depth, headers, sample_labels
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
            DataIO.table_to_npz(base, user_id, pid, output_otu_file_name)
            DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)
            return 0, headers, sample_labels
        else:
            logger.error("Invalid action selected")
            raise NotImplementedError("Invalid action selected")

        logger.info("Subsampling OTU table to " + str(subsample_to) + " using type " + str(subsample_type))

        temp_table = Table(base.transpose(), observation_ids=headers, sample_ids=sample_labels)
        temp_table = temp_table.subsample(subsample_to, axis="sample")
        subsampled_sample_labels = temp_table._sample_ids.tolist()
        subsampled_headers = temp_table._observation_ids.tolist()
        DataIO.table_to_npz(temp_table.matrix_data.transpose(), user_id, pid, output_otu_file_name)

        logger.info("Finished basic subsampling")

        labels = [subsampled_headers, subsampled_sample_labels]
        DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)

        return subsample_to, subsampled_headers, subsampled_sample_labels

    @staticmethod
    def __get_subsampled_depth(base):
        """
        Returns the depth that the table is subsampled to, or -1 if the table is not subsampled
        :param self:
        :param base:
        :return:
        """
        all_sum = base.sum(axis=1)
        if set(all_sum.A[:,0].tolist()) == 1:
            return all_sum.min().item()
        else:
            return -1

    @staticmethod
    def __get_min_depth(base):
        """
        Returns the sum of the row with the min sum
        :param self:
        :param base:
        :return:
        """
        return base.sum(axis=1).min().item()

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
