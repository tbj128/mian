

import unittest
from functools import partialmethod
from multiprocessing import Pool
import datetime

from mian.model.otu_table import OTUTable


def f(b, x):
    # time.sleep(0.1)
    b["a"] = 2
    print(x)
    return x * x

class TestOTUTable(unittest.TestCase):

    def test_load_tsv(self):
        pass
        
        # second_arg = {"a": 1}
        # with Pool(5) as pool:
        #     iterable = [0] * 20
        #     func = partialmethod(f, second_arg)
        #     pool.map(func, iterable)
        #
        # print(second_arg)

        # otu_table = OTUTable("unit_tests", "large_biom")

        # start = datetime.datetime.now()
        # otu_table.aggregate_otu_table_at_taxonomic_level_np(otu_table.get_table(), 2)
        #
        # end = datetime.datetime.now()
        # elapsed = end - start
        # print(elapsed)


        # start = datetime.datetime.now()
        # otu_table.aggregate_otu_table_at_taxonomic_level(otu_table.get_table(), 2)
        #
        # end = datetime.datetime.now()
        # elapsed = end - start
        # print(elapsed)

        # start = datetime.datetime.now()
        # otu_table.aggregate_otu_table_at_taxonomic_level(otu_table.get_table(), 2)
        # end = datetime.datetime.now()
        # elapsed = end - start
        # print(elapsed)

        # =========
        # arr = [2] * 200
        # start = datetime.datetime.now()
        #
        # with Pool(5) as p:
        #     qwe = p.map(partial(f, b), arr)
        #     print(str(len(qwe)))
        #
        # end = datetime.datetime.now()
        # elapsed = end - start
        # print(elapsed)
        #
        # print("---")
        #
        # start = datetime.datetime.now()
        # new_row = []
        # for row in arr:
        #     new_row.append(f(row))
        #     time.sleep(0.1)
        # print(len(new_row))
        #
        # end = datetime.datetime.now()
        # elapsed = end - start
        # print(elapsed)


if __name__ == '__main__':
    unittest.main()