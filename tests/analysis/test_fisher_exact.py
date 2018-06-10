import json

from mian.analysis.fisher_exact import FisherExact
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestFisherExact(unittest.TestCase):

    def test_simple_fisher_exact(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = 1 # This is the "categorical" column
        user_request.set_custom_attr("minthreshold", 0)
        user_request.set_custom_attr("keepthreshold", 5)
        user_request.set_custom_attr("pwVar1", "Control")
        user_request.set_custom_attr("pwVar2", "Disease")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        sample_ids_from_metadata = AnalysisTestUtils.get_sample_ids_from_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = FisherExact()
        actual_output = plugin.analyse(user_request, otu_table, metadata_values, sample_ids_from_metadata)
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "fisher_exact_0_5_control_disease.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()