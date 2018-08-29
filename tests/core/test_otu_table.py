

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
        # pass

        # second_arg = {"a": 1}
        # with Pool(5) as pool:
        #     iterable = [0] * 20
        #     func = partialmethod(f, second_arg)
        #     pool.map(func, iterable)
        #
        # print(second_arg)


        start = datetime.datetime.now()
        otu_table = OTUTable("unit_tests", "large_biom")
        end = datetime.datetime.now()
        elapsed = end - start
        print(elapsed)

        start = datetime.datetime.now()
        filtered_table, headers, sample_metadata = otu_table.aggregate_otu_table_at_taxonomic_level(otu_table.get_table(), otu_table.headers,
                                                                          otu_table.sample_labels, 2)
        filtered_table, headers, sample_metadata = otu_table.filter_out_low_count_np(filtered_table, headers, sample_metadata)
        print(filtered_table.shape[0])
        print(filtered_table.shape[1])
        end = datetime.datetime.now()
        elapsed = end - start
        print(elapsed)
        print("")
        start = datetime.datetime.now()
        filtered_table, headers, sample_metadata = otu_table.aggregate_otu_table_at_taxonomic_level_np(otu_table.get_table(), otu_table.headers, otu_table.sample_labels, 2)
        filtered_table, headers, sample_metadata = otu_table.filter_out_low_count_np(filtered_table, headers, sample_metadata)
        print(filtered_table.shape[0])
        print(filtered_table.shape[1])

        end = datetime.datetime.now()
        elapsed = end - start
        print(elapsed)

        # print("Num OTUs = " + str(len(otu_table.get_table()[0])))
        # start = datetime.datetime.now()
        # filtered_base = otu_table.filter_out_low_count_np(otu_table.get_table(), 2, 20)
        # print("Num OTUs After = " + str(len(filtered_base[0])))
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