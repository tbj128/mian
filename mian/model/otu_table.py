from functools import lru_cache

from mian.core.constants import RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_FILENAME, \
    RAW_OTU_TABLE_LABELS_FILENAME, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME
from mian.core.data_io import DataIO
from mian.model.metadata import Metadata
import logging
from multiprocessing import Pool
from functools import partial
import datetime
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class OTUTable(object):

    def __init__(self, user_id, pid, use_raw=False):
        self.user_id = ""
        self.pid = ""
        self.sample_metadata = ""
        self.table = []
        self.headers = []
        self.sample_labels = []
        self.load_otu_table(user_id, pid, use_raw)
        logger.info(DataIO.tsv_to_table.cache_info())

    def load_otu_table(self, user_id, pid, use_raw):
        self.user_id = user_id
        self.pid = pid
        logger.info("Before load")
        self.sample_metadata = Metadata(user_id, pid)
        logger.info("Finished metadata loading")
        if use_raw:
            logger.info("Using raw data")
            self.table = DataIO.tsv_to_np_table(self.user_id, self.pid, RAW_OTU_TABLE_FILENAME)
            labels = DataIO.tsv_to_table(self.user_id, self.pid, RAW_OTU_TABLE_LABELS_FILENAME)
            self.headers = labels[0]
            self.sample_labels = labels[1]
        else:
            logger.info("Using subsampled data")
            self.table = DataIO.tsv_to_np_table(self.user_id, self.pid, SUBSAMPLED_OTU_TABLE_FILENAME)
            labels = DataIO.tsv_to_table(self.user_id, self.pid, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)
            self.headers = labels[0]
            self.sample_labels = labels[1]
        logger.info("Finished table loading")

    def get_table(self):
        return self.table

    def get_headers(self):
        return self.headers

    def get_sample_labels(self):
        return self.sample_labels

    def get_table_after_filtering(self, user_request):
        t, h, s = self.filter_otu_table_by_metadata(self.table, self.headers, self.sample_labels, user_request)
        return t, h, s

    def get_otu_metadata(self):
        return self.otu_metadata

    def get_sample_metadata(self):
        return self.sample_metadata

    def filter_otu_table_by_metadata(self, base, headers, sample_labels, user_request):
        """
        Filters an OTU table by a particular metadata category by identifying the samples that fall under the
        metadata category
        :param base:
        :param metadata:
        :param catvar:
        :param values:
        :return:
        """
        catvar = user_request.sample_filter
        role = user_request.sample_filter_role
        values = user_request.sample_filter_vals
        if catvar == "none" or catvar == "" or (len(values) == 1 and values[0] == "mian-select-all"):
            # Filtering is not enabled or everything is selected
            logger.info("Sample filtering not enabled or all samples are selected")
            return base, headers, sample_labels

        metadata_map = self.sample_metadata.get_sample_id_to_metadata_map(catvar)

        samples = {}

        row = 0
        while row < len(base):
            sample_id = sample_labels[row]
            if sample_id in metadata_map:
                if role == "Include":
                    if metadata_map[sample_id] in values:
                        samples[sample_id] = 1
                else:
                    if metadata_map[sample_id] not in values:
                        samples[sample_id] = 1

            row += 1

        if samples is None or samples == "":
            samples = []

        new_otu_table = []
        new_sample_labels = []

        num_filtered_samples = 0
        i = 0
        while i < len(base):
            sample_id = sample_labels[i]
            if sample_id in samples:
                new_otu_table.append(base[i])
                new_sample_labels.append(sample_id)
            else:
                num_filtered_samples += 1
            i += 1

        logger.info("Filtered out " + str(num_filtered_samples) + "/" + str(len(base)) + " samples")
        return new_otu_table, headers, new_sample_labels

    @staticmethod
    def get_otu_table_headers_at_taxonomic_level(user_id, pid, level, use_raw=False):
        if use_raw:
            logger.info("Using raw data")
            labels = DataIO.tsv_to_table(user_id, pid, RAW_OTU_TABLE_LABELS_FILENAME)
            headers = labels[0]
        else:
            logger.info("Using subsampled data")
            labels = DataIO.tsv_to_table(user_id, pid, SUBSAMPLED_OTU_TABLE_LABELS_FILENAME)
            headers = labels[0]

        return headers
