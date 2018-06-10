import json

from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.analysis.enriched_selection import EnrichedSelection
from tests.analysis.analysis_test_utils import AnalysisTestUtils
from mian.model.metadata import Metadata
import unittest


class TestEnrichedSelection(unittest.TestCase):

    def test_simple_enriched_selection(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "Category"
        user_request.set_custom_attr("enrichedthreshold", 0.25)
        user_request.set_custom_attr("pwVar1", "Control")
        user_request.set_custom_attr("pwVar2", "Disease")

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)
        taxonomy_map = AnalysisTestUtils.get_test_taxonomy(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        sample_ids_from_metadata = AnalysisTestUtils.get_sample_ids_from_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        metadata = Metadata("test", "test", False)
        metadata.set_table(metadata_table)

        plugin = EnrichedSelection()
        abundances = plugin.analyse(user_request, otu_table, metadata, taxonomy_map, sample_ids_from_metadata)
        print(json.dumps(abundances))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "enriched_selection_0.25_control_disease.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, abundances)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(abundances)
        self.assertTrue(comparison_output)


if __name__ == '__main__':
    unittest.main()