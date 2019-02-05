import csv
import json
import os
import numpy as np
import math

from mian.core.constants import SUBSAMPLED_OTU_TABLE_FILENAME, SAMPLE_METADATA_FILENAME, TAXONOMY_FILENAME, \
    SUBSAMPLED_OTU_TABLE_LABELS_FILENAME
from mian.model.user_request import UserRequest
from mian.model.taxonomy import Taxonomy
from mian.model.metadata import Metadata

from mian.rutils import r_package_install

r_package_install.importr_custom("vegan")
r_package_install.importr_custom("RColorBrewer")
r_package_install.importr_custom("ranger")
r_package_install.importr_custom("Boruta")
r_package_install.importr_custom("glmnet")


class AnalysisTestUtils(object):
    TEST_ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    TEST_INPUT_ROOT_DIR = os.path.join(TEST_ROOT_DIR, "input")
    TEST_OUTPUT_ROOT_DIR = os.path.join(TEST_ROOT_DIR, "output")

    SIMPLE_TEST_CASE_ROOT = os.path.join(TEST_INPUT_ROOT_DIR, "simple_test_case")
    SIMPLE_TEST_CASE_OUTPUT_ROOT = os.path.join(TEST_OUTPUT_ROOT_DIR, "simple_test_case")

    @staticmethod
    def create_default_user_request():
        # -2 represents no taxonomy filtering
        user_request = UserRequest("testuid", "testpid", 0, 0, -2, "Include", [], "", "Include", [], -2, "")
        return user_request

    @staticmethod
    def get_expected_output(test_dir, test_file_name):
        test_file = os.path.join(test_dir, test_file_name)
        with open(test_file, 'r') as tsf:
            data = tsf.read()
            return json.loads(data)

    @staticmethod
    def get_test_input_as_table(test_dir, csv_name=SUBSAMPLED_OTU_TABLE_FILENAME, sep="\t", use_np=False):
        output = []
        csv_name = os.path.join(test_dir, csv_name)
        print("Opening file with name " + csv_name)
        with open(csv_name, 'r') as csvfile:
            base_csv = csv.reader(csvfile, delimiter=sep, quotechar='|')
            for o in base_csv:
                if len(o) > 1:
                    output.append(o)
        if use_np:
            return np.array(output, dtype=float)
        return output

    @staticmethod
    def get_test_input_as_metadata(test_dir, csv_name=SUBSAMPLED_OTU_TABLE_LABELS_FILENAME, sep="\t"):
        output = []
        csv_name = os.path.join(test_dir, csv_name)
        print("Opening file with name " + csv_name)
        with open(csv_name, 'r') as csvfile:
            base_csv = csv.reader(csvfile, delimiter=sep, quotechar='|')
            for o in base_csv:
                if len(o) > 1:
                    output.append(o)
        return output[0], output[1]

    @staticmethod
    def get_test_taxonomy(test_dir):
        taxonomy_table = AnalysisTestUtils.get_test_input_as_table(test_dir, TAXONOMY_FILENAME)
        taxonomy_map = {}
        i = 0
        for row in taxonomy_table:
            if i > 0:
                taxonomy_map[row[Taxonomy.OTU_COL]] = row[Taxonomy.TAXONOMY_COL:]
            i += 1
        return taxonomy_map

    @staticmethod
    def get_disease_metadata_values(test_dir):
        return AnalysisTestUtils.get_col_from_metadata(test_dir, 1)

    @staticmethod
    def get_statistically_relevant_metadata_values(test_dir):
        return AnalysisTestUtils.get_col_from_metadata(test_dir, 2)

    @staticmethod
    def get_non_statistically_relevant_metadata_values(test_dir):
        return AnalysisTestUtils.get_col_from_metadata(test_dir, 3)

    @staticmethod
    def get_sample_ids_from_metadata(test_dir):
        return AnalysisTestUtils.get_col_from_metadata(test_dir, 0)

    @staticmethod
    def get_sample_id_to_metadata(test_dir, target_col, csv_name=SAMPLE_METADATA_FILENAME, sep="\t"):
        output = {}
        csv_name = os.path.join(test_dir, csv_name)
        print("Opening file with name " + csv_name)
        with open(csv_name, 'r') as csvfile:
            base_csv = csv.reader(csvfile, delimiter=sep, quotechar='|')
            i = 0
            for o in base_csv:
                if i > 0:
                    output[o[0]] = o[target_col]
                i += 1
        return output

    @staticmethod
    def get_col_from_metadata(test_dir, target_col, csv_name=SAMPLE_METADATA_FILENAME, sep="\t"):
        output = []
        csv_name = os.path.join(test_dir, csv_name)
        print("Opening file with name " + csv_name)
        with open(csv_name, 'r') as csvfile:
            base_csv = csv.reader(csvfile, delimiter=sep, quotechar='|')
            i = 0
            for o in base_csv:
                if i > 0:
                    output.append(o[target_col])
                i += 1
        return output

    @staticmethod
    def get_metadata_obj(test_dir, csv_name=SAMPLE_METADATA_FILENAME, sep="\t"):
        output = []
        csv_name = os.path.join(test_dir, csv_name)
        print("Opening file with name " + csv_name)
        with open(csv_name, 'r') as csvfile:
            base_csv = csv.reader(csvfile, delimiter=sep, quotechar='|')
            i = 0
            for o in base_csv:
                output.append(o)
                i += 1
        metadata = Metadata("", "", load_samples=False)
        metadata.set_table(output)
        return metadata

    @staticmethod
    def compare_two_objects(obj1, obj2, order_matters=True, relative_tolerance=1e-5):
        """
        Compares two objects based on equality of all fields
        """
        if obj1 is None or obj2 is None:
            return False

        if isinstance(obj1, np.float64):
            obj1 = float(obj1)
        if isinstance(obj2, np.float64):
            obj2 = float(obj2)

        if type(obj1) is not type(obj2):
            return False
        elif type(obj1) is float or type(obj1) is int:
            return math.isclose(obj1, obj2, rel_tol=relative_tolerance)
        elif type(obj1) is str:
            return obj1 == obj2
        elif type(obj1) is dict:
            for attr, v in obj1.items():
                if attr not in obj2:
                    return False

                value1 = v
                value2 = obj2[attr]

                inner_comparison = AnalysisTestUtils.compare_two_objects(value1, value2, order_matters,
                                                                         relative_tolerance)
                if not inner_comparison:
                    return False
            return True
        elif type(obj1) is list:
            list1 = obj1
            list2 = obj2
            if len(list1) != len(list2):
                return False
            if order_matters:
                counter = 0
                while counter < len(list1):
                    inner_comparison = AnalysisTestUtils.compare_two_objects(list1[counter], list2[counter], order_matters, relative_tolerance)
                    if not inner_comparison:
                        return False
                    counter += 1
            else:
                visited = {}
                counter = 0
                while counter < len(list1):
                    inner_counter = 0
                    found = False
                    while inner_counter < len(list2):
                        if inner_counter not in visited:
                            inner_comparison = AnalysisTestUtils.compare_two_objects(list1[counter], list2[inner_counter], order_matters, relative_tolerance)
                            if inner_comparison:
                                found = True
                                visited[inner_counter] = True
                                break
                        inner_counter += 1
                    if not found:
                        return False
                    counter += 1

            return True
        else:
            print("Unknown comparison type")
            return False

