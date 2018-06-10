import json

from mian.analysis.nmds import NMDS
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestNMDS(unittest.TestCase):

    def test_simple_nmds(self):

        user_request = AnalysisTestUtils.create_default_user_request()

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        sample_ids_from_metadata = AnalysisTestUtils.get_sample_ids_from_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = NMDS()
        abundances = plugin.analyse(user_request, otu_table, metadata_values, sample_ids_from_metadata)

        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "nmds.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, abundances)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(abundances)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()