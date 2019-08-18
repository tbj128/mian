from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.core.data_io import DataIO
import numpy as np

from mian.model.quantiles import Quantiles
from mian.model.genes import Genes


class Metadata(object):

    def __init__(self, user_id, pid, is_categorical_tool=True, load_samples=True):
        self.user_id = user_id
        self.pid = pid
        self.metadata = []
        self.is_categorical_tool = is_categorical_tool
        if load_samples:
            self.__load_metadata_samples()

    def __load_metadata_samples(self):
        """
        Loads a metadata file into memory if needed
        :return:
        """
        if len(self.metadata) == 0:
            self.metadata = DataIO.tsv_to_table(self.user_id, self.pid, SAMPLE_METADATA_FILENAME)

    def set_table(self, metadata):
        """
        Test helper that allows a user to manually load the contents of the metadata
        :param metadata:
        :return:
        """
        self.metadata = metadata

    def get_as_table_in_table_order(self, sample_labels, metadata_names=None):
        """
        Returns the metadata of the metadata values. The values will correspond directly to the input OTU table order.
        :param meta_col:
        :return:
        """

        new_metadata_table = []

        if metadata_names is not None and len(metadata_names) > 0:
            genes = Genes(self.user_id, self.pid)
            quantile = Quantiles(self.user_id, self.pid)

            new_headers = ["Samples"]
            new_headers.extend(metadata_names)

            for _ in sample_labels:
                new_metadata_table.append([])

            j = 0
            while j < len(metadata_names):
                col = self.get_metadata_column_table_order(sample_labels, metadata_names[j], genes=genes, quantile=quantile)
                i = 0
                while i < len(sample_labels):
                    if len(col) > 0:
                        new_metadata_table[i].append(col[i])
                    else:
                        new_metadata_table[i].append("")
                    i += 1
                j += 1
        else:
            # Return the entire metadata table
            # TODO: Below doesn't include the genes as part of the table output. Let's try to deprecate this code block
            sample_id_to_metadata_table_row = {}
            i = 1
            while i < len(self.metadata):
                sample_id_to_metadata_table_row[self.metadata[i][0]] = i
                i += 1

            new_headers = self.metadata[0][1:]
            i = 0
            while i < len(sample_labels):
                row_index = sample_id_to_metadata_table_row[sample_labels[i]]
                new_metadata_table.append(self.metadata[row_index][1:])
                i += 1
        return new_metadata_table, new_headers, sample_labels


    def get_metadata_headers_with_type(self):
        """
        Gets the metadata columns with indication of whether they are numeric or categorical
        :return: array of objects; each object contains name and type
        """
        headers = []
        added_headers = {}

        quantile = Quantiles(self.user_id, self.pid)

        j = 1
        while j < len(self.metadata[0]):
            # Go through each column
            numeric_entries = {}
            is_numeric = True
            i = 1
            while i < len(self.metadata):
                if not any(c.isalpha() for c in self.metadata[i][j]):
                    numeric_entries[self.metadata[i][j]] = 1
                else:
                    is_numeric = False
                i += 1
            # A column is "both" if all the entries are numeric, but there is not many unique values
            is_both = is_numeric and len(numeric_entries) < len(self.metadata) - 1

            added_headers[self.metadata[0][j]] = True
            quantile_status = quantile.exists(self.metadata[0][j])

            if is_both:
                headers.append({
                    "name": self.metadata[0][j],
                    "type": "both",
                    "quantileStatus": quantile_status
                })
            elif is_numeric:
                headers.append({
                    "name": self.metadata[0][j],
                    "type": "numeric",
                    "quantileStatus": quantile_status
                })
            else:
                headers.append({
                    "name": self.metadata[0][j],
                    "type": "categorical",
                    "quantileStatus": quantile_status
                })
            j += 1

        for quantile_range_name, quantile_obj in quantile.quantiles.items():
            if quantile_range_name not in added_headers:
                headers.append({
                    "name": quantile_range_name + " (Quantile Range)",
                    "type": "categorical",
                    "quantileStatus": True
                })

        return headers

    def get_numeric_metadata_info(self, metadata_name):
        metadata_col_num = self.get_metadata_column_number(metadata_name)
        col_arr = []

        # Ignoring first row because it is the table header
        i = 1
        while i < len(self.metadata):
            if any(c.isalpha() for c in self.metadata[i][metadata_col_num]):
                return {
                    "numeric": False
                }
            col_arr.append(float(self.metadata[i][metadata_col_num]))
            i += 1

        col_arr = np.array(col_arr)
        q_0 = np.percentile(col_arr, 0)
        q_25 = np.percentile(col_arr, 25)
        q_33 = np.percentile(col_arr, 33)
        q_50 = np.percentile(col_arr, 50)
        q_66 = np.percentile(col_arr, 66)
        q_75 = np.percentile(col_arr, 75)
        q_100 = np.percentile(col_arr, 100)

        return {
            "numeric": True,
            "q_0": q_0,
            "q_25": q_25,
            "q_33": q_33,
            "q_50": q_50,
            "q_66": q_66,
            "q_75": q_75,
            "q_100": q_100
        }

    def get_as_filtered_table(self, metadata_name, filter_role, filter_values):
        if metadata_name == "none" or metadata_name == "":
            return self.metadata

        if filter_values is None or filter_values == "":
            filter_values = []

        metadata_col = self.get_metadata_column_number(metadata_name)
        filtered_metadata = [self.metadata[0]]
        i = 0
        for row in self.metadata:
            if i > 0:
                if filter_role == "Include":
                    if row[metadata_col] in filter_values:
                        filtered_metadata.append(row)
                else:
                    if row[metadata_col] not in filter_values:
                        filtered_metadata.append(row)
            i += 1
        return filtered_metadata

    def get_metadata_column_number(self, metadata_name):
        """
        Gets the column that a particular category appears in the metadata file
        :param catvar:
        :return:
        """
        if metadata_name == "mian-sample-id":
            return 0

        cat_col = -1
        j = 0
        while j < len(self.metadata[0]):
            if self.metadata[0][j] == metadata_name:
                cat_col = j
            j += 1
        return cat_col

    def get_metadata_column_table_order(self, sample_labels, metadata_name, genes: Genes=None, quantile: Quantiles=None):
        """
        Returns an array of the metadata values. The values will correspond directly to the input OTU table order.
        The header of the metadata is ignored.
        :param sample_labels:
        :param metadata_name:
        :param genes:
        :param quantile:
        :return:
        """

        if genes is None:
            genes = Genes(self.user_id, self.pid)

        if quantile is None:
            quantile = Quantiles(self.user_id, self.pid)

        meta_vals = []

        if " (Quantile Range)" in metadata_name:
            # Can be either sample metadata or gene expression quantile range
            actual_metadata_name = metadata_name.split(" (Quantile Range)")[0]

            metadata_map = self.get_sample_id_to_metadata_map(actual_metadata_name)
            if len(metadata_map.keys()) == 0:
                # Check that maybe this quantile range is a gene
                meta_vals = genes.get_multi_gene_values([actual_metadata_name], sample_labels=sample_labels)
                if len(meta_vals) == 0:
                    # No matching gene found
                    return meta_vals
            else:
                row = 0
                while row < len(sample_labels):
                    if sample_labels[row] in metadata_map:
                        meta_vals.append(metadata_map[sample_labels[row]])
                    row += 1

            if quantile.exists(actual_metadata_name):
                existing_quantile = quantile.get_existing(actual_metadata_name)

                transformed_meta_vals = []
                for v in meta_vals:
                    for quantile in existing_quantile["quantiles"]:
                        if float(v) >= float(quantile["min"]) and float(v) < float(quantile["max"]):
                            transformed_meta_vals.append(quantile["displayName"])
                        elif float(v) == float(quantile["max"]) and float(quantile["max"]) == float(existing_quantile["max"]):
                            transformed_meta_vals.append(quantile["displayName"])
                return transformed_meta_vals
        else:
            metadata_map = self.get_sample_id_to_metadata_map(metadata_name)
            if len(metadata_map.keys()) == 0:
                # Check that maybe this requested variable is a gene
                meta_vals = genes.get_multi_gene_values([metadata_name], sample_labels=sample_labels)
                return meta_vals

            row = 0
            while row < len(sample_labels):
                if sample_labels[row] in metadata_map:
                    meta_vals.append(metadata_map[sample_labels[row]])
                row += 1
        return meta_vals


    def get_sample_id_to_metadata_map(self, metadata_name):
        """
        Returns a map of sample IDs to metadata values
        :param meta_col:
        :return:
        """
        meta_vals = {}
        if metadata_name.lower() == "none" or metadata_name.lower() == "":
            return meta_vals

        meta_col = self.get_metadata_column_number(metadata_name)
        if meta_col < 0:
            return meta_vals

        i = 0
        while i < len(self.metadata):
            # Maps the ID column to metadata column
            meta_vals[self.metadata[i][0]] = self.metadata[i][meta_col]
            i += 1
        return meta_vals

    def get_metadata_unique_vals(self, metadata_name, genes: Genes=None, quantile: Quantiles=None):
        """
        Gets the unique metadata values for a particular metadata column.
        SHOULD NOT GET NUMERICAL VALUES FROM THIS
        :param metadata_name:
        :return:
        """

        unique_vals = {}
        if metadata_name == "none":
            return list(unique_vals.keys())

        if quantile is None:
            quantile = Quantiles(self.user_id, self.pid)

        if " (Quantile Range)" in metadata_name:
            # Can be either sample metadata or gene expression quantile range
            actual_metadata_name = metadata_name.split(" (Quantile Range)")[0]
            if quantile.exists(actual_metadata_name):
                existing_quantile = quantile.get_existing(actual_metadata_name)
                quantile_display_names = []

                for quantile in existing_quantile["quantiles"]:
                    quantile_display_names.append(quantile["displayName"])
                return quantile_display_names
        else:
            catvar_col = self.get_metadata_column_number(metadata_name)

            if catvar_col == -1:
                return list(unique_vals.keys())

            i = 1
            while i < len(self.metadata):
                if self.metadata[i][catvar_col] not in unique_vals:
                    unique_vals[self.metadata[i][catvar_col]] = True
                i += 1
        return list(unique_vals.keys())



    #########




    def get_metadata_samples(self):
        """
        Gets the sample names that are in the metadata file in order of the metadata file
        :return:
        """
        samples = []
        samplesUnique = {}
        i = 1
        while i < len(self.metadata):
            if self.metadata[i][0] not in samplesUnique:
                samplesUnique[self.metadata[i][0]] = 1
                samples.append(self.metadata[i][0])
            i += 1
        return samples


    def get_metadata_headers_with_metadata(self):
        """
        Gets the metadata headers with the metadata file itself
        :return:
        """
        headers = []
        i = 1
        while i < len(self.metadata[0]):
            headers.append(self.metadata[0][i])
            i += 1
        return headers, self.metadata




    def map_id_to_metadata(self, meta_col):
        """
        Returns a map of sample IDs to metadata values
        :param meta_col:
        :return:
        """
        meta_vals = {}
        i = 1
        while i < len(self.metadata):
            # Maps the ID column to metadata column
            meta_vals[self.metadata[i][0]] = self.metadata[i][meta_col]
            i += 1
        return meta_vals



    def get_unique_metadata_cat_vals(self, meta_col):
        """
        Gets the unique values for a particular metadata columns
        :param meta_col:
        :return:
        """
        unique_vals = []
        i = 1
        while i < len(self.metadata):
            # Maps the ID column to metadata column
            if self.metadata[i][meta_col] not in unique_vals:
                unique_vals.append(self.metadata[i][meta_col])
            i += 1
        return unique_vals
