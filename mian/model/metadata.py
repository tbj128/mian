from mian.core.constants import SAMPLE_METADATA_FILENAME
from mian.core.data_io import DataIO


class Metadata(object):

    def __init__(self, user_id, pid, load_samples=True):
        self.user_id = user_id
        self.pid = pid
        self.metadata = []
        if load_samples:
            self.__load_metadata_samples()

    def __load_metadata_samples(self):
        """
        Loads a metadata file into memory
        :return:
        """
        self.metadata = DataIO.tsv_to_table(self.user_id, self.pid, SAMPLE_METADATA_FILENAME)

    def set_table(self, metadata):
        """
        Test helper that allows a user to manually load the contents of the metadata
        :param metadata:
        :return:
        """
        self.metadata = metadata

    def get_as_table(self):
        """
        Loads the metadata as a table
        :return:
        """
        return self.metadata

    def get_as_table_in_table_order(self, sample_labels):
        """
        Returns the metadata of the metadata values. The values will correspond directly to the input OTU table order.
        The header of the metadata is ignored.
        :param meta_col:
        :return:
        """
        sample_id_to_metadata_table_row = {}
        i = 1
        while i < len(self.metadata):
            sample_id_to_metadata_table_row[self.metadata[i][0]] = i
            i += 1

        new_metadata_table = []
        new_metadata_table.append(self.metadata[0])
        i = 0
        while i < len(sample_labels):
            row_index = sample_id_to_metadata_table_row[sample_labels[i]]
            new_metadata_table.append(self.metadata[row_index])
            i += 1
        return new_metadata_table

    def get_metadata_headers(self):
        """
        Gets the metadata headers in order of the metadata file
        :return:
        """
        headers = []
        i = 1
        while i < len(self.metadata[0]):
            headers.append(self.metadata[0][i])
            i += 1
        return headers

    def get_metadata_headers_with_type(self):
        """
        Gets the metadata columns with indication of whether they are numeric or categorical
        :return: array of objects; each object contains name and type
        """
        headers = []

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

            if is_both:
                headers.append({
                    "name": self.metadata[0][j],
                    "type": "both"
                })
            elif is_numeric:
                headers.append({
                    "name": self.metadata[0][j],
                    "type": "numeric"
                })
            else:
                headers.append({
                    "name": self.metadata[0][j],
                    "type": "categorical"
                })
            j += 1
        return headers

    def get_numeric_metadata_headers(self):
        """
        Gets the metadata columns that are completely numeric in value
        :return:
        """
        headers = []

        j = 1
        while j < len(self.metadata[0]):
            # Go through each column
            is_numeric = True
            i = 1
            while i < len(self.metadata):
                # Go through each row in each column
                if any(c.isalpha() for c in self.metadata[i][j]):
                    is_numeric = False
                    break
                i += 1
            if is_numeric:
                headers.append(self.metadata[0][j])
            j += 1
        return headers

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

    def get_metadata_column_table_order(self, sample_labels, metadata_name):
        """
        Returns an array of the metadata values. The values will correspond directly to the input OTU table order.
        The header of the metadata is ignored.
        :param meta_col:
        :return:
        """
        metadata_map = self.get_sample_id_to_metadata_map(metadata_name)
        meta_vals = []
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
        i = 0
        while i < len(self.metadata):
            # Maps the ID column to metadata column
            meta_vals[self.metadata[i][0]] = self.metadata[i][meta_col]
            i += 1
        return meta_vals

    def get_metadata_unique_vals(self, catvar):
        """
        Gets the unique metadata values for a particular metadata column
        :param catvar:
        :return:
        """
        unique_vals = {}
        if catvar == "none":
            return unique_vals

        catvar_col = self.get_metadata_column_number(catvar)

        i = 1
        while i < len(self.metadata):
            if self.metadata[i][catvar_col] not in unique_vals:
                unique_vals[self.metadata[i][catvar_col]] = 1
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
