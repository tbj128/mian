import json

import numpy as np

from mian.analysis.deep_neural_network import DeepNeuralNetwork
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestDeepNeuralNetwork(unittest.TestCase):

    def test_deep_neural_network(self):
        np.random.seed(0)

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.set_custom_attr("dnnModel", [{"type":"dense","units":10,"dropoutfrac":0,"key":1},{"type":"dropout","units":0,"dropoutfrac":0.5,"key":2},{"type":"dense","units":10,"dropoutfrac":0,"key":3},{"type":"dropout","units":0,"dropoutfrac":0.5,"key":4}])
        user_request.set_custom_attr("epochs", 100)
        user_request.set_custom_attr("problemType", "classification")
        user_request.set_custom_attr("fixTraining", "yes")
        user_request.set_custom_attr("trainingProportion", 0.7)
        user_request.set_custom_attr("validationProportion", 0.3)
        user_request.set_custom_attr("trainingIndexes", [])

        otu_table = AnalysisTestUtils.get_test_npz_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        plugin = DeepNeuralNetwork()
        actual_output = plugin.analyse(user_request, otu_table, headers, metadata_values)
        print(json.dumps(actual_output))

        self.assertEquals(35, len(actual_output["training_indexes"]))

if __name__ == '__main__':
    unittest.main()