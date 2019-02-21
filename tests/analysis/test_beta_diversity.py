import json

from mian.analysis.beta_diversity import BetaDiversity
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest
from mian.rutils import r_package_install
r_package_install.importr_custom("vegan")

class TestBetaDiversity(unittest.TestCase):

    def test_simple_beta_diversity(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("betaType", "bray")
        user_request.set_custom_attr("strata", "")
        user_request.set_custom_attr("api", "beta")
        user_request.set_custom_attr("phylogenetic_tree", "")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        strata_values = AnalysisTestUtils.get_non_statistically_relevant_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        sample_ids_from_metadata = AnalysisTestUtils.get_sample_ids_from_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = BetaDiversity()
        actual_output = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata_values, strata_values, sample_ids_from_metadata, "")
        print(json.dumps(actual_output))

        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "beta_diversity_bray.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output["abundances"])
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()