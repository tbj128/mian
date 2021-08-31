# ===========================================
#
# mian Heatmap Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
from scipy.stats import stats

from mian.model.otu_table import OTUTable
import numpy as np
from mian.analysis.alpha_diversity import AlphaDiversity


class Heatmap(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)
        metadata = table.get_sample_metadata()
        phylogenetic_tree = table.get_phylogenetic_tree()

        return self.analyse(user_request, base, headers, sample_labels, metadata, phylogenetic_tree)

    def get_numeric_metadata_table(self, metadata, metadata_headers):
        metadata = np.array(metadata)
        metadata_headers = np.array(metadata_headers)
        cols_to_keep = []
        j = 0
        while j < len(metadata_headers):
            all_are_numeric = True
            i = 0
            while i < len(metadata):
                if not metadata[i][j].isnumeric():
                    all_are_numeric = False
                i += 1
            if all_are_numeric:
                cols_to_keep.append(j)
            j += 1

        new_metadata = metadata[:, cols_to_keep]
        new_metadata_headers = metadata_headers[cols_to_keep]
        return new_metadata, new_metadata_headers

    def analyse(self, user_request, base, headers, sample_labels, metadata, phylogenetic_tree):
        corrvar1 = user_request.get_custom_attr("corrvar1")
        corrvar2 = user_request.get_custom_attr("corrvar2")
        corrMethod = user_request.get_custom_attr("corrMethod")
        cluster = user_request.get_custom_attr("cluster")
        minSamplesPresent = int(user_request.get_custom_attr("minSamplesPresent"))

        metadata_otu_order, metadata_headers, _ = metadata.get_as_table_in_table_order(sample_labels)
        numeric_metadata, numeric_metadata_headers = self.get_numeric_metadata_table(metadata_otu_order, metadata_headers)
        numeric_metadata = numeric_metadata.astype(float)

        alpha = AlphaDiversity()
        corrvar1Base = []
        corrvar1Headers = []
        if corrvar1 == "Taxonomy":
            corrvar1Base = base.toarray()
            corrvar1Headers = headers
        elif corrvar1 == "Metadata":
            corrvar1Base = numeric_metadata
            corrvar1Headers = numeric_metadata_headers.tolist()
        elif corrvar1 == "Alpha":
            alpha_params = user_request.get_custom_attr("corrvar1Alpha")
            if int(user_request.level) == -1:
                # OTU tables are returned as a CSR matrix
                base = base.toarray()
            alpha_vals = alpha.calculate_alpha_diversity(base, sample_labels, headers, phylogenetic_tree, alpha_params[1],
                                                         alpha_params[0])
            corrvar1Base = []
            i = 0
            while i < len(alpha_vals):
                corrvar1Base.append([alpha_vals[i]])
                i += 1
            corrvar1Headers = ["Alpha Diversity"]

        corrvar2Base = []
        corrvar2Headers = []
        if corrvar2 == "Taxonomy":
            corrvar2Base = base.toarray()
            corrvar2Headers = headers
        elif corrvar2 == "Metadata":
            corrvar2Base = numeric_metadata
            corrvar2Headers = numeric_metadata_headers.tolist()
        elif corrvar2 == "Alpha":
            alpha_params = user_request.get_custom_attr("corrvar2Alpha")
            if int(user_request.level) == -1:
                # OTU tables are returned as a CSR matrix
                base = base.toarray()
            alpha_vals = alpha.calculate_alpha_diversity(base, sample_labels, headers, phylogenetic_tree, alpha_params[1],
                                                         alpha_params[0])
            corrvar2Base = []
            i = 0
            while i < len(alpha_vals):
                corrvar2Base.append([alpha_vals[i]])
                i += 1
            corrvar2Headers = ["Alpha Diversity"]

        if corrvar1 != corrvar2:
            X = np.array(corrvar1Base)
            non_zero = np.count_nonzero(X, axis=0)
            X = X[:, non_zero >= minSamplesPresent]
            headers = np.array(corrvar1Headers)
            headers = headers[non_zero >= minSamplesPresent]

            Y = np.array(corrvar2Base)
            non_zero = np.count_nonzero(Y, axis=0)
            Y = Y[:, non_zero >= minSamplesPresent]
            y_headers = np.array(corrvar2Headers)
            y_headers = y_headers[non_zero >= minSamplesPresent]

            X = np.concatenate((X, Y), axis=1)

            if corrMethod == "spearman":
                correlations, _ = stats.spearmanr(X)
            elif corrMethod == "pearson":
                correlations = np.corrcoef(X, rowvar=False)
            else:
                raise NotImplementedError("Correlation method not implemented")
            correlations = correlations[len(headers):len(headers) + len(y_headers), 0:len(headers)]
            row_headers = y_headers.tolist()
            col_headers = headers.tolist()
        else:
            X = np.array(corrvar1Base)
            non_zero = np.count_nonzero(X, axis=0)
            X = X[:, non_zero >= minSamplesPresent]
            if corrMethod == "spearman":
                correlations, _ = stats.spearmanr(X)
            elif corrMethod == "pearson":
                correlations = np.corrcoef(X, rowvar=False)
            else:
                raise NotImplementedError("Correlation method not implemented")
            row_headers = headers
            col_headers = headers

        if cluster == "Yes":
            # Perform some simple clustering by ordering by the col sums
            col_sums = np.sum(correlations, axis=0).tolist()
            col_sums = sorted(range(len(col_sums)), key=col_sums.__getitem__, reverse=True)

            if corrvar1 != corrvar2:
                row_sums = np.sum(correlations, axis=1).tolist()
                row_sums = sorted(range(len(row_sums)), key=row_sums.__getitem__, reverse=True)
            else:
                row_sums = col_sums

            correlations = correlations[:, col_sums]
            correlations = correlations[row_sums, :]

            row_headers = np.array(row_headers)
            row_headers = row_headers[row_sums].tolist()
            col_headers = np.array(col_headers)
            col_headers = col_headers[col_sums].tolist()

        correlations_list = []
        if corrvar1 == corrvar2:
            correlations = correlations.tolist()
            i = 0
            while i < len(correlations):
                row = []
                j = i
                while j < len(correlations[i]):
                    row.append(round(correlations[i][j], 2))
                    j += 1
                correlations_list.append(row)
                i += 1
        else:
            correlations_list = correlations.tolist()


        abundances_obj = {
            "row_headers": row_headers,
            "col_headers": col_headers,
            "data": correlations_list,
        }
        return abundances_obj
