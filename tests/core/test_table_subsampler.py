

import unittest
import pandas as pd
import os
from scipy import sparse

from mian.core.otu_table_subsampler import OTUTableSubsampler


class TestOTUTableSubsampler(unittest.TestCase):

    def test_cumulative_sum_scaling(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        df = pd.read_csv(f"{dir_path}/../input/metagenomeSeq/mouseData.csv", index_col=0)
        scaled_arr = OTUTableSubsampler.cumulative_sum_scaling(sparse.csr_matrix(df.to_numpy().transpose()).toarray())
        # scaled_arr = OTUTableSubsampler.cumulative_sum_scaling(df.to_numpy().transpose())
        self.assertEqual(6427.632, round(sum(scaled_arr[0, :]), 3))

    def test_cum_norm_stat_fast(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        df = pd.read_csv(f"{dir_path}/../input/metagenomeSeq/mouseData.csv", index_col=0)
        # print(df.to_numpy(), df.columns.values, df.index.values)
        self.assertEqual(0.5, OTUTableSubsampler.cum_norm_stat_fast(df.to_numpy()))

    def test_upper_quantile_scaling(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        df = pd.read_csv(f"{dir_path}/../input/metagenomeSeq/upperQuantileMat.csv", index_col=0)
        headers = list(df.index.values)
        scaled_arr, headers = OTUTableSubsampler.upper_quantile_scaling(
            sparse.csr_matrix(df.to_numpy().transpose()).toarray(),
            headers
        )
        self.assertEqual(69.0, round(sum(scaled_arr[0, :]), 3))


if __name__ == '__main__':
    unittest.main()