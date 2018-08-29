

from mian.core.data_io import DataIO
import unittest


class TestDataIO(unittest.TestCase):

    def test_load_tsv(self):
        loaded_table = DataIO.tsv_to_table("unit_tests", "small_biom", "table.subsampled.tsv")
        self.assertEqual(6, len(loaded_table))
        self.assertEqual(5, len(loaded_table[0]))
        self.assertEqual("23", loaded_table[0][1])

    def test_np_load_tsv(self):
        loaded_table = DataIO.tsv_to_np_table("unit_tests", "small_biom", "table.subsampled.tsv")
        self.assertEqual(6, len(loaded_table))
        self.assertEqual(5, len(loaded_table[0]))
        self.assertEqual(23, loaded_table[0][1])

if __name__ == '__main__':
    unittest.main()