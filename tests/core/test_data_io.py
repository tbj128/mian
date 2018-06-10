import json

from mian.core.data_io import DataIO
from tests.analysis.analysis_test_utils import AnalysisTestUtils
import unittest


class TestDataIO(unittest.TestCase):

    def test_small_biom_to_tsv(self):
        tsv_file_name = DataIO.convert_biom_to_tsv("unit_tests", "small_biom", "small_biom_v1.biom", "testfile.txt")
        self.assertEquals("testfile.txt", tsv_file_name)

    @unittest.skip
    def test_large_biom_to_tsv(self):
        tsv_file_name = DataIO.convert_biom_to_tsv("unit_tests", "large_biom", "large_biom_v1.biom", "testfile.txt")
        self.assertEquals("testfile.txt", tsv_file_name)


if __name__ == '__main__':
    unittest.main()