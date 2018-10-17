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
        # Just copy the raw data table to the subsampled table location
        logger.error("Subsampling disabled")
        labels = [headers, sample_labels]
        DataIO.table_to_tsv(base, user_id, pid, output_otu_file_name)
        DataIO.table_to_tsv(labels, user_id, pid, output_otu_labels_file_name)
        return 0, {}, []


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
