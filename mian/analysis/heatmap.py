# ===========================================
#
# mian Heatmap Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

from mian.model.otu_table import OTUTable
import numpy as np


class Heatmap(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)
        metadata = table.get_sample_metadata()

        return self.analyse(user_request, base, headers, sample_labels, metadata)

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

    def analyse(self, user_request, base, headers, sample_labels, metadata):
        corrvar1 = user_request.get_custom_attr("corrvar1")
        corrvar2 = user_request.get_custom_attr("corrvar2")
        cluster = user_request.get_custom_attr("cluster")
        minSamplesPresent = int(user_request.get_custom_attr("minSamplesPresent"))

        metadata_otu_order, metadata_headers, _ = metadata.get_as_table_in_table_order(sample_labels)
        numeric_metadata, numeric_metadata_headers = self.get_numeric_metadata_table(metadata_otu_order, metadata_headers)
        numeric_metadata = numeric_metadata.astype(float)

        if corrvar1 == 'Taxonomy' and corrvar2 == 'Metadata':
            X = np.array(base)
            non_zero = np.count_nonzero(X, axis=0)
            X = X[:, non_zero >= minSamplesPresent]
            headers = np.array(headers)
            headers = headers[non_zero >= minSamplesPresent]

            non_zero = np.count_nonzero(numeric_metadata, axis=0)
            numeric_metadata = numeric_metadata[:, non_zero >= minSamplesPresent]
            numeric_metadata_headers = numeric_metadata_headers[non_zero >= minSamplesPresent]

            X = np.concatenate((X, numeric_metadata), axis=1)

            correlations = np.corrcoef(X, rowvar=False)
            correlations = correlations[len(headers):len(headers) + len(numeric_metadata_headers), 0:len(headers)]
            row_headers = numeric_metadata_headers.tolist()
            col_headers = headers.tolist()

        elif corrvar2 == 'Taxonomy' and corrvar1 == 'Metadata':
            X = np.array(base)
            non_zero = np.count_nonzero(X, axis=0)
            X = X[:, non_zero >= minSamplesPresent]
            headers = np.array(headers)
            headers = headers[non_zero >= minSamplesPresent]

            non_zero = np.count_nonzero(numeric_metadata, axis=0)
            numeric_metadata = numeric_metadata[:, non_zero >= minSamplesPresent]
            numeric_metadata_headers = numeric_metadata_headers[non_zero >= minSamplesPresent]

            X = np.concatenate((numeric_metadata, X), axis=1)

            correlations = np.corrcoef(X, rowvar=False)
            correlations = correlations[len(numeric_metadata_headers):len(numeric_metadata_headers) + len(headers), 0:len(numeric_metadata_headers)]
            row_headers = headers.tolist()
            col_headers = numeric_metadata_headers.tolist()

        elif corrvar2 == 'Metadata' and corrvar1 == 'Metadata':
            X = np.array(numeric_metadata)
            non_zero = np.count_nonzero(X, axis=0)
            X = X[:, non_zero >= minSamplesPresent]

            correlations = np.corrcoef(X, rowvar=False)
            row_headers = numeric_metadata_headers.tolist()
            col_headers = numeric_metadata_headers.tolist()

        else:
            X = np.array(base)
            non_zero = np.count_nonzero(X, axis=0)
            X = X[:, non_zero >= minSamplesPresent]
            correlations = np.corrcoef(X, rowvar=False)
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
