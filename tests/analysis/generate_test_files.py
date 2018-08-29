import json

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.tree_view import TreeView
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest
import os
import random
import numpy as np
import csv

class TestGenerate(unittest.TestCase):

    def test_generate(self):

        output_dir = os.path.join(AnalysisTestUtils.TEST_INPUT_ROOT_DIR, "generate")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        total_columns = 60
        differential_columns_start = 0
        correlated_columns_start = 10
        non_sparse_columns_start = 20
        sparse_columns_start = 30

        num_samples = 100
        differential_categories = ["Disease", "Control"]

        otu = []
        headers = ["Sample ID"]
        sample_labels = []
        taxonomy = [["OTU", "Taxonomy"]]
        metadata = []


        is_differential = False
        is_sparse = False
        is_correlated = False
        is_non_sparse = False
        j = 0
        while j < total_columns:
            if j == differential_columns_start:
                is_differential = True
                is_sparse = False
                is_correlated = False
                is_non_sparse = False
            if j == correlated_columns_start:
                is_differential = False
                is_sparse = False
                is_correlated = True
                is_non_sparse = False
            if j == non_sparse_columns_start:
                is_differential = False
                is_sparse = False
                is_correlated = False
                is_non_sparse = True
            if j == sparse_columns_start:
                is_differential = False
                is_sparse = True
                is_correlated = False
                is_non_sparse = False

            if is_differential:
                otu.append(generate_differential_column(num_samples, len(differential_categories)))
                otu_name = "OtuDiff" + str(j)
                headers.append(otu_name)
                taxonomy.append([otu_name, "K", "P", "C", "O", "F", "G", "S"])
            if is_correlated:
                otu.append(generate_correlated_column(num_samples))
                otu_name = "OtuCorr" + str(j)
                headers.append(otu_name)
                taxonomy.append([otu_name, "K", "P", "C", "O", "F", "G", "S"])
            if is_sparse:
                otu.append(generate_sparse_column(num_samples))
                otu_name = "OtuSparse" + str(j)
                headers.append(otu_name)
                taxonomy.append([otu_name, "K", "P", "C", "O", "F", "G", "S"])
            if is_non_sparse:
                otu.append(generate_non_sparse_column(num_samples))
                otu_name = "OtuNonSparse" + str(j)
                headers.append(otu_name)
                taxonomy.append([otu_name, "K", "P", "C", "O", "F", "G", "S"])

            j += 1


        metadata_row_labels = ["Metadata"]
        i = 0
        while i < num_samples:
            sample = "Sample" + str(i)
            metadata_row_labels.append(sample)
            sample_labels.append(sample)
            i += 1
        metadata.append(metadata_row_labels)
        metadata.append(["Differential"] + generate_differential_metadata_column(num_samples, differential_categories))
        metadata.append(["Correlated"] + generate_correlated_metadata_column(num_samples))
        metadata.append(["Non-Significant Numeric"] + generate_non_significant_numeric_metadata_column(num_samples))
        metadata.append(["Non-Significant Categorical"] + generate_non_significant_categorical_metadata_column(num_samples, 3))

        otu.insert(0, sample_labels)
        otu = np.array(otu)
        otu = np.transpose(otu)

        csv_path = os.path.join(output_dir, "table.tsv")
        output_otu_csv = csv.writer(open(csv_path, 'w'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        output_otu_csv.writerow(headers)
        for row in otu:
            output_otu_csv.writerow(row)

        metadata_csv_path = os.path.join(output_dir, "metadata.tsv")
        metadata = np.array(metadata)
        metadata = np.transpose(metadata)
        output_metadata_csv = csv.writer(open(metadata_csv_path, 'w'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in metadata:
            output_metadata_csv.writerow(row)

        taxonomy_csv_path = os.path.join(output_dir, "taxonomy.tsv")
        taxonomy_csv = csv.writer(open(taxonomy_csv_path, 'w'), delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in taxonomy:
            taxonomy_csv.writerow(row)


def generate_non_sparse_column(num_samples):
    weights = []

    x = 0
    while x < 30:
        weights.append(random.randint(30, 101))
        x += 1

    col = []
    i = 0
    while i < num_samples:
        col.append(random.choice(weights))
        i += 1

    return col


def generate_sparse_column(num_samples):
    weights = [0] * 90 + [1] * 10

    col = []
    i = 0
    while i < num_samples:
        col.append(random.choice(weights))
        i += 1

    return col


def generate_differential_column(num_samples, num_categories):
    samples_per_category = num_samples / num_categories
    category = 0

    col = []
    i = 0
    while i < num_samples:
        if i % samples_per_category == 0:
            category += 1

        rand_weight = random.randint(category * 10, category * 10 + 3)
        col.append(rand_weight)
        i += 1
    return col

def generate_correlated_column(num_samples):
    col = []
    i = 0
    while i < num_samples:
        rand_weight = random.randint(i * 10, i * 10 + 3)
        col.append(rand_weight)
        i += 1
    return col


def generate_non_significant_numeric_metadata_column(num_samples):
    weights = []

    x = 0
    while x < 30:
        weights.append(random.randint(30, 101))
        x += 1

    col = []
    i = 0
    while i < num_samples:
        col.append(random.choice(weights))
        i += 1

    return col


def generate_non_significant_categorical_metadata_column(num_samples, num_categories):
    weights = []

    x = 0
    while x < num_categories:
        weights.append("Meta" + str(random.randint(30, 101)))
        x += 1

    col = []
    i = 0
    while i < num_samples:
        col.append(random.choice(weights))
        i += 1

    return col


def generate_differential_metadata_column(num_samples, differential_categories):
    samples_per_category = num_samples / len(differential_categories)
    category = -1

    col = []
    i = 0
    while i < num_samples:
        if i % samples_per_category == 0:
            category += 1

        col.append(differential_categories[category])
        i += 1
    return col


def generate_correlated_metadata_column(num_samples):
    col = []
    i = 0
    while i < num_samples:
        rand_weight = random.randint(i * 10, i * 10 + 3)
        col.append(rand_weight)
        i += 1
    return col


if __name__ == '__main__':
    # unittest.main()
    pass