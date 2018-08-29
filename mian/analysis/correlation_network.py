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
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        return self.analyse(user_request, base, headers)

    def analyse(self, user_request, base, headers):
        maxFeatures = int(user_request.get_custom_attr("maxFeatures"))
        cutoff = float(user_request.get_custom_attr("cutoff"))

        X = np.array(base)
        otu_names = headers

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

        abundances_obj = {
            "nodes": nodes,
            "links": links,
            "cmd": "",
        }

        return abundances_obj

