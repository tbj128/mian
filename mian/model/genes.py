from mian.core.constants import GENE_FILENAME, GENE_LABELS_FILENAME
from mian.core.data_io import DataIO
import os
import sqlite3
import numpy as np

GO_DB_NAME = "go.db"
GO_HEADERS_NAME = "go_terms.txt"
RELATIVE_PATH = os.path.dirname(os.path.realpath(__file__))
RELATIVE_PATH = os.path.abspath(os.path.join(RELATIVE_PATH, os.pardir))
GO_DB_PATH = os.path.join(RELATIVE_PATH, GO_DB_NAME)
GO_HEADERS_PATH = os.path.join(RELATIVE_PATH, GO_HEADERS_NAME)


class Genes(object):

    def __init__(self, user_id, pid):
        self.user_id = user_id
        self.pid = pid

        # Lazy load the gene table/labels as needed
        self.gene_table = []
        self.gene_labels = []

    def get_gene_headers(self, type):
        if type == "Group":
            headers = []
            with open(GO_HEADERS_PATH, 'r') as f:
                for line in f:
                    headers.append(line)
        else:
            if len(self.gene_labels) == 0:
                self.gene_labels = DataIO.tsv_to_table(self.user_id, self.pid, GENE_LABELS_FILENAME)
            return self.gene_labels[0]

    def get_as_table(self, gene_list=[], orig_sample_labels=[]):
        """
        Gets a gene table where the samples are rows and genes are columns
        :param gene_list: filters columns to those genes in this list. if empty, return all columns
        :param orig_sample_labels: if not empty, return table with rows reordered to the sample label order
        :return:
        """
        if len(self.gene_table) == 0:
            self.gene_table = DataIO.tsv_to_table(self.user_id, self.pid, GENE_FILENAME)

        if len(self.gene_labels) == 0:
            self.gene_labels = DataIO.tsv_to_table(self.user_id, self.pid, GENE_LABELS_FILENAME)
        headers = self.gene_labels[0]
        sample_labels = self.gene_labels[1]

        new_headers = []
        cols_to_keep = {}
        i = 0
        while i < len(headers):
            if len(gene_list) == 0 or headers[i] in gene_list:
                cols_to_keep[i] = True
                new_headers.append(headers[i])
            i += 1

        new_sample_labels = []
        rows_to_keep = {}
        i = 0
        while i < len(sample_labels):
            if len(orig_sample_labels) == 0 or sample_labels[i] in orig_sample_labels:
                rows_to_keep[i] = True
                new_sample_labels.append(sample_labels[i])
            i += 1

        base = []
        i = 0
        while i < len(self.gene_table):
            if i in rows_to_keep:
                new_row = []
                j = 0
                while j < len(self.gene_table[i]):
                    if j in cols_to_keep:
                        new_row.append(self.gene_table[i][j])
                    j += 1
                base.append(new_row)
            i += 1

        return base, new_headers, new_sample_labels

    def get_multi_gene_values(self, gene_list):
        """
        Gets the summed values of the gene list in the order of the sample labels
        :param gene_list:
        :param sample_labels:
        :return:
        """
        if len(self.gene_table) == 0:
            # Gene table is already in the order of the samples
            self.gene_table = DataIO.tsv_to_table(self.user_id, self.pid, GENE_FILENAME)

        if len(self.gene_labels) == 0:
            self.gene_labels = DataIO.tsv_to_table(self.user_id, self.pid, GENE_LABELS_FILENAME)
        headers = self.gene_labels[0]
        cols_of_interest = {}
        j = 0
        while j < len(headers):
            if headers[j] in gene_list:
                cols_of_interest[j] = True
            j += 1
        if len(cols_of_interest) == 0:
            return []

        vals = []

        for row in self.gene_table:
            tot = 0
            for c in cols_of_interest.keys():
                tot += float(row[c])
            vals.append(tot)

        return vals


    def get_genes_of_interest(self, labels_of_interest):
        # Fetch the functional annotations
        db = sqlite3.connect(GO_DB_PATH)
        c = db.cursor()
        c.execute('SELECT gene FROM go_gene WHERE go_term in (\'' + "','".join(labels_of_interest) + '\')')
        rows = c.fetchall()
        genes_of_interest = {}
        for row in rows:
            genes_of_interest[row[0]] = True
        db.close()
        return list(genes_of_interest)

    def get_gene_info(self, gene):
        col_arr = self.get_multi_gene_values([gene])

        col_arr = np.array(col_arr)
        q_0 = np.percentile(col_arr, 0)
        q_25 = np.percentile(col_arr, 25)
        q_33 = np.percentile(col_arr, 33)
        q_50 = np.percentile(col_arr, 50)
        q_66 = np.percentile(col_arr, 66)
        q_75 = np.percentile(col_arr, 75)
        q_100 = np.percentile(col_arr, 100)

        return {
            "numeric": True,
            "q_0": q_0,
            "q_25": q_25,
            "q_33": q_33,
            "q_50": q_50,
            "q_66": q_66,
            "q_75": q_75,
            "q_100": q_100
        }

