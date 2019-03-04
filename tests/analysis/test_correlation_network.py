import json

from mian.analysis.correlation_network import CorrelationNetwork
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestCorrelationNetwork(unittest.TestCase):

    def test_simple_correlation_network(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("type", "Taxonomic")
        user_request.set_custom_attr("cutoff", 0.75)

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, use_np=True)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_col = []

        plugin = CorrelationNetwork()
        actual_output = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata_col)
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "correlation_network.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()