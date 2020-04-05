import logging
import numpy as np
import scipy.cluster.hierarchy as hcluster

from mian.analysis.analysis_base import AnalysisBase

from mian.model.otu_table import OTUTable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def distance_comparator(a, b):
    return np.linalg.norm(a[1]-b[1])


class CompositionHeatmap(AnalysisBase):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        base, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_column = []
        catvar = user_request.catvar
        if catvar != "none" and (user_request.get_custom_attr("rows") == "SampleID" or user_request.get_custom_attr("cols") == "SampleID"):
            # Only if the sample ID is on the rows or the columns can we actually color the heatmap catvar indicator
            metadata_column = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, catvar)

        return self.analyse(user_request, base, headers, sample_labels, metadata_column)

    def analyse(self, user_request, base, headers, sample_labels, metadata_column):
        """
        Return the composition to be parsed as a heatmap. Either the row or the column must be numeric
        """
        rows = user_request.get_custom_attr("rows")
        cols = user_request.get_custom_attr("cols")
        clustersamples = user_request.get_custom_attr("clustersamples")
        clustertaxonomic = user_request.get_custom_attr("clustertaxonomic")

        if int(user_request.level) != -1:
            base = np.array(base, dtype=float)

        if rows == "none" or cols == "none":
            return {}

        new_metadata_column = np.array(metadata_column)
        row_headers = []
        if rows == "none":
            return {}
        elif rows == "Taxonomic":
            row_headers = np.array(headers)
            if clustertaxonomic == "otu":
                if int(user_request.level) == -1:
                    # CSR matrix
                    col_sums = base.sum(axis=0).A[0]
                else:
                    col_sums = np.sum(base, axis=0)

                sorted_indices = np.argsort(-col_sums)
                row_headers = row_headers[sorted_indices]
                base = base[:, sorted_indices]
        elif rows == "SampleID":
            row_headers = np.array(sample_labels)
            if user_request.catvar != "none" and clustersamples == "categorical":
                sorted_indices = np.argsort(metadata_column)
                new_metadata_column = new_metadata_column[sorted_indices] if len(
                    new_metadata_column) > 0 else new_metadata_column



                # Gets the start index of each unique metadata value
                unique_metadata_vals = sorted(set(metadata_column))
                meta_val_to_start_index = {}
                last_meta_val = ""
                i = 0
                while i < len(new_metadata_column):
                    if new_metadata_column[i] != last_meta_val:
                        meta_val_to_start_index[new_metadata_column[i]] = i
                        last_meta_val = new_metadata_column[i]
                    i += 1

                # Creates a final sorted index (samples within each group are sorted)
                final_sorted_indices = []
                for val in unique_metadata_vals:
                    if int(user_request.level) == -1:
                        # CSR matrix
                        max_each_row = base[new_metadata_column == val, :].max(axis=1).toarray()[:,0]
                    else:
                        max_each_row = np.max(base[new_metadata_column == val, :], axis=1)
                    indices_sort_range = np.argsort(-max_each_row) + meta_val_to_start_index[val]
                    i = 0
                    j = 0
                    while i < len(new_metadata_column):
                        if new_metadata_column[i] == val:
                            final_sorted_indices.append(indices_sort_range[j])
                            j += 1
                        i += 1

                row_headers = row_headers[final_sorted_indices]
                base = base[final_sorted_indices, :]



        col_headers = []
        if cols == "none":
            return {}
        elif cols == "Taxonomic":
            col_headers = np.array(headers)
            if clustertaxonomic == "otu":
                if int(user_request.level) == -1:
                    # CSR matrix
                    col_sums = base.sum(axis=0).A[0]
                else:
                    col_sums = np.sum(base, axis=0)
                sorted_indices = np.argsort(-col_sums)
                col_headers = col_headers[sorted_indices]
                base = base[:, sorted_indices]
        elif cols == "SampleID":
            col_headers = np.array(sample_labels)
            if user_request.catvar != "none" and clustersamples == "categorical":
                sorted_indices = np.argsort(metadata_column)
                new_metadata_column = new_metadata_column[sorted_indices] if len(
                    new_metadata_column) > 0 else new_metadata_column

                # Gets the start index of each unique metadata value
                unique_metadata_vals = sorted(set(metadata_column))
                meta_val_to_start_index = {}
                last_meta_val = ""
                i = 0
                while i < len(new_metadata_column):
                    if new_metadata_column[i] != last_meta_val:
                        meta_val_to_start_index[new_metadata_column[i]] = i
                        last_meta_val = new_metadata_column[i]
                    i += 1

                # Creates a final sorted index (samples within each group are sorted)
                final_sorted_indices = []
                for val in unique_metadata_vals:
                    if int(user_request.level) == -1:
                        # CSR matrix
                        max_each_row = base[new_metadata_column == val, :].max(axis=1).toarray()[:,0]
                    else:
                        max_each_row = np.max(base[new_metadata_column == val, :], axis=1)

                    indices_sort_range = np.argsort(-max_each_row) + meta_val_to_start_index[val]
                    i = 0
                    j = 0
                    while i < len(new_metadata_column):
                        if new_metadata_column[i] == val:
                            final_sorted_indices.append(indices_sort_range[j])
                            j += 1
                        i += 1

                col_headers = col_headers[final_sorted_indices]
                base = base[final_sorted_indices, :]

        min = base.min()
        max = base.max()

        if rows == "Taxonomic":
            # Transpose the table
            base = base.transpose()

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            base = base.toarray()

        abundances_obj = {
            "catvar": new_metadata_column.tolist(),
            "row_headers": row_headers.tolist(),
            "col_headers": col_headers.tolist(),
            "data": base.tolist(),
            "max": float(max),
            "min": float(min)
        }
        return abundances_obj


