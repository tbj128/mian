import numpy as np
import scipy
from scipy.sparse import csr_matrix
import os

from skbio.diversity import alpha_diversity

from mian.core.data_io import DataIO

otu = scipy.sparse.load_npz("/Users/boyanjin/Documents/Personal/workspace/mian/mian/data/18/b54c2ded-31db-4ae6-9d05-9e1550370f03/table.subsampled.npz")

labels = DataIO.tsv_to_table_from_path("/Users/boyanjin/Documents/Personal/workspace/mian/mian/data/18/b54c2ded-31db-4ae6-9d05-9e1550370f03/table.subsampled.labels.tsv", False)

otu_table = otu.toarray()
ad = alpha_diversity("observed_otus", otu_table, ids=labels[1])
print(ad)


ad = alpha_diversity("shannon", otu_table, ids=labels[1])
print(ad)