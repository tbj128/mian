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
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_col = []
        if user_request.get_custom_attr("type") == "SampleID" and user_request.catvar != "none":
            metadata_col = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)

        return self.analyse(user_request, base, headers, sample_labels, metadata_col)

    def analyse(self, user_request, base, headers, sample_labels, metadata_col):
        corrType = user_request.get_custom_attr("type")
        cutoff = float(user_request.get_custom_attr("cutoff"))

        X = np.array(base)

        catvar_map = {}
        if corrType == "SampleID":
            correlation_headers = sample_labels
            partial_correlations = np.corrcoef(X, rowvar=True)

            if len(sample_labels) == len(metadata_col):
                i = 0
                while i < len(sample_labels):
                    catvar_map[sample_labels[i]] = metadata_col[i]
                    i += 1
        else:
            # Filter OTU table columns so that the matrix created is manageable in size
            correlation_headers = headers
            partial_correlations = np.corrcoef(X, rowvar=False)

        non_zero = (np.abs(np.triu(partial_correlations, k=1)) > cutoff)

        _, labels = cluster.affinity_propagation(partial_correlations)
        n_labels = labels.max()

        # Plot the edges
        start_idx, end_idx = np.where(non_zero)
        # # a sequence of (*line0*, *line1*, *line2*), where::
        # #            line = (x0, y0), (x1, y1), ... (xm, ym)
        segments = [[correlation_headers[start], correlation_headers[stop]]
                    for start, stop in zip(start_idx, end_idx)]
        values = partial_correlations[non_zero]

        nodes = [{"id": str(correlation_headers[i]), "c": str(labels[i]), "v": self.get_catvar(corrType, correlation_headers[i], catvar_map)}
                 for i in range(len(correlation_headers))]
        links = [{"source": str(seg[0]), "target": str(seg[1]), "v": round(float(val), 3)}
                 for seg, val in zip(segments, values)]
        if len(links) > 5000:
            # Take the top 5000 links (to allow for efficient rendering
            top_links = sorted(links, key=lambda kv: kv["v"], reverse=True)
            cutoff_val = top_links[5000]["v"]
            top_links = top_links[:5000]
        else:
            cutoff_val = cutoff
            top_links = links

        nodes_to_keep = {}
        for link in top_links:
            nodes_to_keep[link["source"]] = True
            nodes_to_keep[link["target"]] = True

        nodes_to_return = list(filter(lambda x: nodes_to_keep[x["id"]] if x["id"] in nodes_to_keep else False, nodes))
        nodes_removed = len(nodes) - len(nodes_to_return)

        unique_groups = {}
        for n in nodes_to_return:
            unique_groups[n["v"]] = True

        abundances_obj = {
            "nodes": nodes_to_return,
            "links": top_links,
            "cutoff_val": cutoff_val,
            "nodes_removed": nodes_removed,
            "unique_groups": list(unique_groups.keys())
        }

        return abundances_obj

    def get_catvar(self, corrType, label, catvar_map):
        if corrType == "SampleID":
            return catvar_map[label] if label in catvar_map else ""
        else:
            return ""
