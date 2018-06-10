# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

from mian.model.otu_table import OTUTable
from sklearn.preprocessing import LabelEncoder
import numpy as np
from sklearn import cluster, covariance


class CorrelationNetwork(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        return self.analyse(user_request, otu_table)

    def analyse(self, user_request, otu_table):
        maxFeatures = int(user_request.get_custom_attr("maxFeatures"))
        cutoff = float(user_request.get_custom_attr("cutoff"))

        table = np.array(otu_table)
        X = np.array(table[1:len(table)])
        X = np.delete(X, 0, 1) # Deletes first sample ID column
        X = X.astype(np.float)
        otu_names = table[0, 1:]

        # Filter OTU table columns so that the matrix created is manageable in size
        if len(otu_names) > maxFeatures:
            max_nodes = maxFeatures
            otu_sums = np.sum(X, axis=0)
            nth_largest_sum = sorted(otu_sums, reverse=True)[max_nodes]
            cols_to_delete = []
            for c in range(len(otu_sums)):
                if otu_sums[c] < nth_largest_sum:
                    cols_to_delete.append(c)
            X = np.delete(X, cols_to_delete, 1)  # Deletes all non-selected columns
            otu_names = np.delete(otu_names, cols_to_delete)  # Deletes all non-selected columns

        partial_correlations = np.corrcoef(X, rowvar=False)
        non_zero = (np.abs(np.triu(partial_correlations, k=1)) > cutoff)

        _, labels = cluster.affinity_propagation(partial_correlations)
        n_labels = labels.max()

        # Plot the edges
        start_idx, end_idx = np.where(non_zero)
        # # a sequence of (*line0*, *line1*, *line2*), where::
        # #            line = (x0, y0), (x1, y1), ... (xm, ym)
        segments = [[otu_names[start], otu_names[stop]]
                    for start, stop in zip(start_idx, end_idx)]
        values = partial_correlations[non_zero]

        nodes = [{"id": str(otu_names[i]), "c": str(labels[i])}
                 for i in range(len(otu_names))]
        links = [{"source": str(seg[0]), "target": str(seg[1]), "v": round(float(val), 3)}
                 for seg, val in zip(segments, values)]

        # # Creates the matrix and inverse covariations
        # edge_model = covariance.GraphLassoCV()
        #
        # fit = edge_model.fit(X)
        #
        # _, labels = cluster.affinity_propagation(edge_model.covariance_)
        # n_labels = labels.max()
        #
        # for i in range(n_labels + 1):
        #     print('Cluster %i: %s' % ((i + 1), ', '.join(otu_names[labels == i])))
        #
        # partial_correlations = edge_model.precision_.copy()
        # d = 1 / np.sqrt(np.diag(partial_correlations))
        # partial_correlations *= d
        # partial_correlations *= d[:, np.newaxis]
        # non_zero = (np.abs(np.triu(partial_correlations, k=1)) > 0.02)

        # # Plot the edges
        # start_idx, end_idx = np.where(non_zero)
        # # a sequence of (*line0*, *line1*, *line2*), where::
        # #            line = (x0, y0), (x1, y1), ... (xm, ym)
        # segments = [[start, stop]
        #             for start, stop in zip(start_idx, end_idx)]
        # values = np.abs(partial_correlations[non_zero])
        #
        # nodes = [{"id": str(otu_names[i]), "c": str(labels[i])}
        #          for i in range(len(otu_names))]
        # links = [{"f": int(seg[0]), "t": int(seg[1]), "v": round(float(val), 3)}
        #          for seg, val in zip(segments, values)]

        abundances_obj = {
            "nodes": nodes,
            "links": links,
            "cmd": "",
        }

        return abundances_obj

