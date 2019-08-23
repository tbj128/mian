import json

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.composition import Composition
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestComposition(unittest.TestCase):

    def test_simple_composition(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "Category"
        user_request.set_custom_attr("plotType", "donut")
        user_request.set_custom_attr("xaxis", "Metadata")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = Composition()
        actual_output = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata_values)
        print(json.dumps(actual_output))

        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "composition_category.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()