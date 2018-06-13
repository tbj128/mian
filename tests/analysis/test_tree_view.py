import json

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.tree_view import TreeView
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestTreeView(unittest.TestCase):

    def test_simple_tree_view(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "Category"
        user_request.set_custom_attr("taxonomy_display_level", 2)
        user_request.set_custom_attr("display_values", "nonzero")
        user_request.set_custom_attr("exclude_unclassified", "yes")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        taxonomy_map = AnalysisTestUtils.get_test_taxonomy(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        sample_ids_from_metadata = AnalysisTestUtils.get_sample_ids_from_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_vals = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        unique_metadata_vals = list(set(AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)))
        sample_id_to_metadata = dict(zip(sample_ids_from_metadata, metadata_vals))

        plugin = TreeView()
        actual_output = plugin.analyse(user_request, otu_table, taxonomy_map, unique_metadata_vals, sample_id_to_metadata)
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "tree_view_2_nonzero_yes.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output, order_matters=False)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()