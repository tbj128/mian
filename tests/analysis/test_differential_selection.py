import json

import numpy as np

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.differential_selection import DifferentialSelection
from tests.analysis.analysis_test_utils import AnalysisTestUtils
from mian.model.metadata import Metadata
import unittest


class TestDifferentialSelection(unittest.TestCase):

    def test_simple_differential_selection(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "Category"
        user_request.set_custom_attr("pvalthreshold", 0.01)
        user_request.set_custom_attr("pwVar1", "Control")
        user_request.set_custom_attr("pwVar2", "Disease")
        user_request.set_custom_attr("type", "ttest")
        user_request.set_custom_attr("fixTraining", "yes")
        user_request.set_custom_attr("trainingIndexes", [])
        user_request.set_custom_attr("trainingProportion", 1.0)

        otu_table = np.array(AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT))
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)
        taxonomic_map = AnalysisTestUtils.get_test_taxonomy(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        metadata = Metadata("test", "test", load_samples=False)
        metadata.set_table(metadata_table)

        plugin = DifferentialSelection()
        abundances = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata_values, taxonomic_map)
        print(json.dumps(abundances))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "differential_selection_control_disease.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, abundances)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(abundances)
        self.assertTrue(comparison_output)

if __name__ == '__main__':
    unittest.main()