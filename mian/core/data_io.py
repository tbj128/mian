import csv
import os
import logging
from functools import lru_cache
import numpy as np
import scipy.sparse

from mian.core.constants import RAW_OTU_TABLE_FILENAME, SUBSAMPLED_OTU_TABLE_FILENAME, TAXONOMY_FILENAME, \
    SAMPLE_METADATA_FILENAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class DataIO:

    @staticmethod
    def does_file_exist(user_id, pid, csv_name):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_name = os.path.join(project_dir, csv_name)
        return os.path.exists(csv_name)

    @staticmethod
    @lru_cache(maxsize=128)
    def load_sparse(user_id, pid, name):

        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_name = os.path.join(project_dir, name)

        logger.info("Opening file with name " + csv_name)
        return scipy.sparse.load_npz(csv_name)

    @staticmethod
    @lru_cache(maxsize=128)
    def tsv_to_np_table(user_id, pid, csv_name, sep="\t"):
        return np.array(DataIO.tsv_to_table(user_id, pid, csv_name, sep), dtype=float)

    @staticmethod
    @lru_cache(maxsize=128)
    def tsv_to_table(user_id, pid, csv_name, sep="\t", accept_empty_headers=True):
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

        return DataIO.tsv_to_table_from_path(csv_name, accept_empty_headers)

    @staticmethod
    def text_from_path(user_id, pid, filename, replace_newlines=True):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_name = os.path.join(project_dir, filename)
        if not os.path.isfile(csv_name):
            return ""
        else:
            with open(csv_name, 'r', encoding='utf-8') as fn:
                if replace_newlines:
                    return fn.read().replace('\n', '')
                else:
                    return fn.read()

    @staticmethod
    def tsv_to_table_from_path(csv_path, accept_empty_headers=True):
        otu_map = []
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.readline())
            delimiter = dialect.delimiter
            if delimiter != "\t" and delimiter != ",":
                delimiter = "\t"

            csvfile.seek(0)

            base_csv = csv.reader(csvfile, delimiter=delimiter)
            empty_header_cols = {}
            i = 0
            for o in base_csv:
                if len(o) > 0:
                    if i == 0:
                        if not accept_empty_headers:
                            j = 0
                            while j < len(o):
                                if o[j].strip() == "":
                                    empty_header_cols[j] = True
                                j += 1

                    new_row = []
                    j = 0
                    while j < len(o):
                        if j not in empty_header_cols:
                            if isinstance(o[j], str):
                                new_row.append(o[j].strip())
                            else:
                                new_row.append(o[j])
                        j += 1
                    if len(new_row) > 0:
                        otu_map.append(new_row)
                i += 1

        return otu_map

    @staticmethod
    def table_to_npz(base, user_id, pid, csv_name):
        """
        Exports a table to NPZ and writes it to the project directory
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
        scipy.sparse.save_npz(csv_path, base)
        logger.info("After write")

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
        outputCSV = csv.writer(open(csv_path, 'w', encoding='utf-8'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in base:
            new_row = []
            j = 0
            while j < len(row):
                if isinstance(row[j], str):
                    new_row.append(row[j].strip())
                else:
                    new_row.append(row[j])
                j += 1
            outputCSV.writerow(new_row)
        logger.info("After write")
