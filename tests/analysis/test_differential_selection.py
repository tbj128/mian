import json
import unittest
import pandas as pd

from mian.analysis.py_deseq import py_DESeq2
from mian.analysis.differential_selection import DifferentialSelection
from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.model.metadata import Metadata
from rutils import r_package_install
from tests.analysis.analysis_test_utils import AnalysisTestUtils

r_package_install.importr_custom("DESeq2", is_bioconductor=True)

class TestDifferentialSelection(unittest.TestCase):

    def test_deseq(self):
        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "Category"
        user_request.set_custom_attr("pvalthreshold", 0.01)
        user_request.set_custom_attr("pwVar1", "Control")
        user_request.set_custom_attr("pwVar2", "Disease")
        user_request.set_custom_attr("type", "ttest")
        user_request.set_custom_attr("fixTraining", "yes")
        user_request.set_custom_attr("trainingIndexes", [])
        user_request.set_custom_attr("trainingProportion", 1.0)

        otu_table = AnalysisTestUtils.get_test_npz_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(
            AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT,
                                                                   SAMPLE_METADATA_FILENAME)
        taxonomic_map = AnalysisTestUtils.get_test_taxonomy(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        metadata = Metadata("test", "test", load_samples=False)
        metadata.set_table(metadata_table)

        # Note data is transposed for input into DESeq2
        sparse_df = pd.DataFrame.sparse.from_spmatrix(otu_table, index=sample_labels, columns=headers).transpose()
        sparse_df = sparse_df.sparse.to_dense()
        sparse_df.index.name = 'otu_id'
        sparse_df.reset_index(inplace=True)
        print(sparse_df.shape)
        print(sparse_df.head())
        design_df = pd.concat([pd.DataFrame(sample_labels), pd.DataFrame(metadata_values)], axis=1)
        design_df.columns = ["samples", "treatment"]
        design_df.set_index("samples")
        print(design_df.shape)
        print(design_df.head())

        dds = py_DESeq2(count_matrix=sparse_df,
                        design_matrix=design_df,
                        design_formula='~ treatment',
                        gene_column='otu_id')

        dds.run_deseq()
        dds.get_deseq_result()
        res = dds.deseq_result
        print(res.head())

    def test_simple_differential_selection(self):

        user_request = AnalysisTestUtils.create_default_user_request()
        user_request.catvar = "Category"
        user_request.set_custom_attr("pvalthreshold", 0.01)
        user_request.set_custom_attr("pwVar1", "Control")
        user_request.set_custom_attr("pwVar2", "Disease")
        user_request.set_custom_attr("type", "ttest")
        user_request.set_custom_attr("fixTraining", "yes")
        user_request.set_custom_attr("trainingIndexes", [])
        user_request.set_custom_attr("trainingProportion", 1.0)

        otu_table = AnalysisTestUtils.get_test_npz_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        headers, sample_labels = AnalysisTestUtils.get_test_input_as_metadata(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_table = AnalysisTestUtils.get_test_input_as_table(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT, SAMPLE_METADATA_FILENAME)
        taxonomic_map = AnalysisTestUtils.get_test_taxonomy(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)
        metadata_values = AnalysisTestUtils.get_disease_metadata_values(AnalysisTestUtils.SIMPLE_TEST_CASE_ROOT)

        metadata = Metadata("test", "test", load_samples=False)
        metadata.set_table(metadata_table)

        plugin = DifferentialSelection()
        abundances = plugin.analyse(user_request, otu_table, headers, sample_labels, metadata_values, taxonomic_map)
        print(json.dumps(abundances))
        expected_output = AnalysisTestUtils.get_expected_output(AnalysisTestUtils.SIMPLE_TEST_CASE_OUTPUT_ROOT,
                                                                "differential_selection_control_disease.json")
        comparison_output = AnalysisTestUtils.compare_two_objects(expected_output, abundances)
        if not comparison_output:
            print("Expected: ")
            print(expected_output)
            print("Actual: ")
            print(abundances)
        self.assertTrue(comparison_output)

if __name__ == '__main__':
    unittest.main()