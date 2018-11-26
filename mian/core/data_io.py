import csv
import os
import logging
from functools import lru_cache
import numpy as np
import pandas as pd

from mian.core.constants import RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_FILENAME, TAXONOMY_FILENAME, \
    SAMPLE_METADATA_FILENAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class DataIO:

    @staticmethod
    @lru_cache(maxsize=128)
    def tsv_to_np_table(user_id, pid, csv_name, sep="\t"):
        return np.array(DataIO.tsv_to_table(user_id, pid, csv_name, sep), dtype=int)

    @staticmethod
    @lru_cache(maxsize=128)
    def tsv_to_table(user_id, pid, csv_name, sep="\t"):
        """
        Reads a CSV/TSV table from a provided file location and returns the table
        contents in an array, where each row in the array is a row in the original
        input file.

        Args:
            user_id (str): The user ID of the associated account
            pid (str): The project ID under the user account
            csv_name (str): The name of the CSV file (not path)
            sep (str): How the CSV file is delimited. Defaults to tab.

        Returns:
            array: Array representation of the input CSV file

        """

        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_name = os.path.join(project_dir, csv_name)

        logger.info("Opening file with name " + csv_name)

        return DataIO.tsv_to_table_from_path(csv_name, sep)

    # @staticmethod
    # def get_sep_type(csv_path):
    #     sniffer = csv.Sniffer()
    #     with open(csv_path) as f:
    #         reader = csv.reader(f)
    #         sample_row = next(reader)
    #         dialect = sniffer.sniff(sample_row)
    #         dialect.delimiter


    @staticmethod
    def tsv_to_table_from_path(csv_path, sep="\t"):
        otu_map = []
        with open(csv_path, 'r') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.readline())
            csvfile.seek(0)
            # base_csv = csv.reader(csvfile, delimiter=dialect, quotechar='|')
            base_csv = csv.reader(csvfile, dialect)
            for o in base_csv:
                if o != "":
                    otu_map.append(o)

        return otu_map

    @staticmethod
    def table_to_tsv(base, user_id, pid, csv_name):
        """
        Exports a table to CSV and writes it to the project directory
        :param base:
        :param user_id:
        :param pid:
        :param csv_name:
        :return:
        """
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_path = os.path.join(project_dir, csv_name)
        logger.info("Before write")
        outputCSV = csv.writer(open(csv_path, 'w'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in base:
            outputCSV.writerow(row)
        logger.info("After write")
