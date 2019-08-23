import json

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.correlations import Correlations
from mian.model.metadata import Metadata
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestCorrelations(unittest.TestCase):

    def test_simple_correlations(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("corrvar1", "MetadataSignificant")
        user_request.set_custom_attr("corrvar2", "MetadataNonSignificant")
        user_request.set_custom_attr("corrvar1SpecificTaxonomies", "[]")
        user_request.set_custom_attr("corrvar2SpecificTaxonomies", "[]")
        user_request.set_custom_attr("colorvar", "MetadataSignificant")
        user_request.set_custom_attr("sizevar", "MetadataNonSignificant")
        user_request.set_custom_attr("sizevarSpecificTaxonomies", "[]")
        user_request.set_custom_attr("samplestoshow", "both")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)

        metadata = Metadata("test", "test", load_samples=False)
        metadata.set_table(metadata_table)

        plugin = Correlations()
        actual_output = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata, "")
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "correlation_sign_nonsign_sign_nonsign.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, actual_output)
        print(json.dumps(actual_output))
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(actual_output)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()