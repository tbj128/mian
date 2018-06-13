import json

from mian.analysis.boruta import Boruta
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestBoruta(unittest.TestCase):

    def test_boruta(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("keepthreshold", "5")
        user_request.set_custom_attr("pval", "0.01")
        user_request.set_custom_attr("maxruns", "100")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        sample_ids_from_metadata = AnalysisTestUtils.get_sample_ids_from_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = Boruta()
        actual_output = plugin.analyse(user_request, otu_table, metadata_values, sample_ids_from_metadata)
        print(json.dumps(actual_output))

        expected_output_v1 = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "boruta_5_0.01_100_v1.json")
        expected_output_v2 = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "boruta_5_0.01_100_v2.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output_v1, actual_output, order_matters=False) or \
                            AnalysisTestUtils.compare_two_objects(expected_output_v2, actual_output, order_matters=False)
        if not comparison_output:
            print("Expected: ")
            print(expected_output_v1)
            print("or Expected: ")
            print(expected_output_v2)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()