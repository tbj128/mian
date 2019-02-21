# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

#
# ======== R specific setup =========
#
import os
import shutil
import uuid
import numpy as np
from sklearn import manifold
from skbio import TreeNode
from io import StringIO
from skbio.diversity import beta_diversity
from sklearn.decomposition import PCA
from sklearn.metrics import euclidean_distances

from mian.util import ROOT_DIR
from mian.model.otu_table import OTUTable

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class NMDS(object):
    #
    # ======== Main code begins =========
    #

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)
        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        phylogenetic_tree = table.get_phylogenetic_tree()
        return self.analyse(user_request, base, headers, sample_labels, metadata_vals, phylogenetic_tree)

    def analyse(self, user_request, base, headers, sample_labels, metadata_vals, phylogenetic_tree):
        logger.info("Starting NMDS analysis")
        type = user_request.get_custom_attr("type")

        if type == "weighted_unifrac" or type == "unweighted_unifrac":
            if phylogenetic_tree == "":
                return {
                    "no_tree": True
                }
            # TODO: Warn users about decimals
            base = base.astype(int)
            tree = TreeNode.read(StringIO(phylogenetic_tree))
            dist_matrix = beta_diversity(type, base, ids=sample_labels, otu_ids=headers, tree=tree)
        elif type == "euclidean":
            dist_matrix = euclidean_distances(base)
        else:
            base = base.astype(int)
            dist_matrix = beta_diversity(type, base)

        similarities = []
        i = 0
        while i < dist_matrix.shape[0]:
            new_row = []
            j = 0
            while j < dist_matrix.shape[0]:
                new_row.append(dist_matrix[i][j])
                j += 1
            similarities.append(new_row)
            i += 1

        # Use traditional MDS to determine the initial position
        mds = manifold.MDS(n_components=2, max_iter=3000, eps=1e-9, dissimilarity="precomputed", n_jobs=1)
        pos = mds.fit(similarities).embedding_
        # Use NMDS to adjust the original positions to optimize for stress
        nmds = manifold.MDS(n_components=2, metric=False, dissimilarity="precomputed", max_iter=3000, eps=1e-12)
        npos = nmds.fit_transform(similarities, init=pos)

        ret_table = []
        i = 0
        while i < len(npos):
            meta = ""
            if metadata_vals and len(metadata_vals) > 0:
                meta = metadata_vals[i]
            obj = {"s": sample_labels[i],
                   "m": meta,
                   "nmds1": npos[i][0],
                   "nmds2": npos[i][1],
                   }

            ret_table.append(obj)
            i += 1

        logger.info("After NMDS plotting")

        buffer = 1.5
        abundancesObj = {"nmds": ret_table,
                         "nmds1Max": np.max(npos[:, 0]) * buffer,
                         "nmds1Min": np.min(npos[:, 0]) * buffer,
                         "nmds2Max": np.max(npos[:, 1]) * buffer,
                         "nmds2Min": np.min(npos[:, 1]) * buffer}
        return abundancesObj

