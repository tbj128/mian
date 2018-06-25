import json

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.correlations_selection import CorrelationsSelection
from mian.model.metadata import Metadata
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestCorrelationsSelection(unittest.TestCase):

    def test_correlations_selection(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "MetadataSignificant"

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)

        metadata = Metadata("test", "test", False)
        metadata.set_table(metadata_table)

        plugin = CorrelationsSelection()
        actual_output = plugin.analyse(user_request, otu_table, metadata)
        print(json.dumps(actual_output))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "correlations_selection.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()