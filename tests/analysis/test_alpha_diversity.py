import json

from mian.analysis.alpha_diversity import AlphaDiversity
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest

from mian.rutils import r_package_install
r_package_install.importr_custom("vegan", version="2.5.4")


class TestAlphaDiversity(unittest.TestCase):

    def test_simple_alpha_diversity(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("expvar", "")
        user_request.set_custom_attr("colorvar", "")
        user_request.set_custom_attr("sizevar", "")
        user_request.set_custom_attr("plotType", "boxplot")
        user_request.set_custom_attr("alphaType", "shannon")
        user_request.set_custom_attr("alphaContext", "evenness")
        user_request.set_custom_attr("statisticalTest", "ttest")
        user_request.set_custom_attr("phylogenetic_tree", "")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = AlphaDiversity()
        actual_output = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata_values, metadata_values, metadata_values, "")
        print(json.dumps(actual_output))

        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "alpha_diversity_shannon_evenness.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()