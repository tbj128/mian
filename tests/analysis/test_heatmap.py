import json

from mian.analysis.heatmap import Heatmap
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestHeatmap(unittest.TestCase):

    def test_heatmap(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("corrvar1", 'Taxonomy')
        user_request.set_custom_attr("corrvar2", 'Taxonomy')
        user_request.set_custom_attr("cluster", 'Yes')
        user_request.set_custom_attr("minSamplesPresent", '1')

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, use_np=True)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata = AnalysisTestUtils.get_metadata_obj(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = Heatmap()
        actual_output = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata, "")
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "heatmap.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()