import json

from mian.analysis.nmds import NMDS
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestNMDS(unittest.TestCase):

    def test_simple_nmds(self):

        user_request = AnalysisTestUtils.create_default_user_request()

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, use_np=True)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = NMDS()
        abundances = plugin.analyse(user_request, otu_table, sample_labels, metadata_values)
        self.assertEquals(5, len(abundances))


if __name__ == '__main__':
    unittest.main()