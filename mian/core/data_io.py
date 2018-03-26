import csv
import os
import logging
from biom import load_table
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class DataIO:

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

        otu_map = []
        csv_name = os.path.join(project_dir, csv_name)
        logger.info("Opening file with name " + csv_name)
        with open(csv_name, 'r') as csvfile:
            base_csv = csv.reader(csvfile, delimiter=sep, quotechar='|')
            for o in base_csv:
                if len(o) > 1:
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
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, user_id)
        project_dir = os.path.join(project_dir, pid)
        csv_name = os.path.join(project_dir, csv_name)
        outputCSV = csv.writer(open(csv_name, 'wb'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in base:
            outputCSV.writerow(row)
