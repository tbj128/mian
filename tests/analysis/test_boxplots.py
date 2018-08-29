import json

from mian.analysis.boxplots import Boxplots
from tests.analysis.analysis_test_utils import AnalysisTestUtils
from mian.core.constants import SAMPLE_METADATA_FILENAME
import unittest


class TestBoxplots(unittest.TestCase):

    def test_simple_metadata_boxplots(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("yvals", "MetadataSignificant")

        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)

        plugin = Boxplots()
        actual_output = plugin.process_metadata_boxplots(user_request, "MetadataSignificant", metadata_table)
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "boxplots_metadata.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)

    def test_simple_abundance_boxplots(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("yvals", "mian-abundance")
        user_request.set_custom_attr("yvalsSpecificTaxonomy", "")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)

        plugin = Boxplots()
        actual_output = plugin.process_abundance_boxplots(user_request, "mian-abundance", otu_table, headers, sample_labels, metadata_table)
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "boxplots_abundance.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()