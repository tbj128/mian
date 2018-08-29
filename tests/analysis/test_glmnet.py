import json

from mian.analysis.glmnet import GLMNet
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestGLMNet(unittest.TestCase):

    def test_simple_glmnet(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("alpha", 0.5)
        user_request.set_custom_attr("family", "binomial")
        user_request.set_custom_attr("lambdathreshold", "lambda")
        user_request.set_custom_attr("lambdaval", -2)

        otu_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, use_np=True)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = GLMNet()
        actual_output = plugin.analyse(user_request, otu_table, headers, metadata_values)
        self.assertEquals(5, len(actual_output["results"]["Control"]))
        self.assertEquals(5, len(actual_output["results"]["Disease"]))


if __name__ == '__main__':
    unittest.main()