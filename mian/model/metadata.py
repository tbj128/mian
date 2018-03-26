from mian.core.constants import SAMPLE_METADATA_FILENAME, SAMPLE_ID_COL
from mian.core.data_io import DataIO


class Metadata(object):

    def __init__(self, user_id, pid):
        self.user_id = user_id
        self.pid = pid
        self.metadata = []
        self.__load_metadata_samples()

    def __load_metadata_samples(self):
        """
        Loads a metadata file into memory
        :return:
        """
        self.metadata = DataIO.tsv_to_table(self.user_id, self.pid, SAMPLE_METADATA_FILENAME)

    def get_as_table(self):
        return self.metadata

    def get_as_filtered_table(self, metadata_name, filter_values):
        if metadata_name == "none" or metadata_name == "":
            return self.metadata

        if filter_values is None or filter_values == "":
            filter_values = []

        metadata_col = self.__get_metadata_column(metadata_name)
        filtered_metadata = [self.metadata[0]]
        i = 0
        for row in self.metadata:
            if i > 0:
                if row[metadata_col] in filter_values:
                    filtered_metadata.append(row)
            i += 1
        return filtered_metadata

    def get_single_metadata_column(self, otu_table, metadata_name):
        """
        Returns an array of the metadata values. The values will correspond directly to the input OTU table order.
        The header of the metadata is ignored.
        :param meta_col:
        :return:
        """
        metadata_map = self.get_sample_id_to_metadata_map(metadata_name)
        meta_vals = []
        row = 1
        while row < len(otu_table):
            if otu_table[row][SAMPLE_ID_COL] in metadata_map:
                meta_vals.append(metadata_map[otu_table[row][SAMPLE_ID_COL]])
            row += 1
        return meta_vals

    def get_sample_id_to_metadata_map(self, metadata_name):
        """
        Returns a map of sample IDs to metadata values
        :param meta_col:
        :return:
        """
        meta_vals = {}
        meta_col = self.__get_metadata_column(metadata_name)
        i = 1
        while i < len(self.metadata):
            # Maps the ID column to metadata column
            meta_vals[self.metadata[i][0]] = self.metadata[i][meta_col]
            i += 1
        return meta_vals

    # def get_metadata_in_otu_table_order(self, metadata_name):
    #     """
    #     Returns an array of the metadata values. The values will correspond directly to the input OTU table order.
    #     The header of the metadata is ignored.
    #     :param otu_table:
    #     :param meta_col:
    #     :return:
    #     """
    #     meta_col = self.__get_metadata_column(metadata_name)
    #     metadata_map = self.map_id_to_metadata(meta_col)
    #     meta_vals = []
    #     row = 1
    #     while row < len(self.otu_table):
    #         if self.otu_table[row][OTU_GROUP_ID_COL] in metadata_map:
    #             meta_vals.append(metadata_map[self.otu_table[row][OTU_GROUP_ID_COL]])
    #         row += 1
    #     return meta_vals

    def __get_metadata_column(self, metadata_name):
        """
        Gets the column that a particular category appears in the metadata file
        :param otu_metadata:
        :param catvar:
        :return:
        """
        if metadata_name == "mian-sample-id":
            return 0

        cat_col = 1
        j = 0
        while j < len(self.metadata[0]):
            if self.metadata[0][j] == metadata_name:
                cat_col = j
            j += 1
        return cat_col


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


    def get_numeric_metadata(self):
        """
        Gets the metadata columns that are completely numeric in value
        :return:
        """
        headers = []
        j = 1
        while j < len(self.metadata[0]):
            isNumeric = True
            i = 1
            while i < len(self.metadata[i]):
                if any(c.isalpha() for c in self.metadata[i][j]):
                    isNumeric = False
                    break
                i += 1
            if isNumeric:
                headers.append(self.metadata[0][j])
            j += 1
        return headers

    def get_metadata_unique_vals(self, catvar):
        """
        Gets the unique metadata values for a particular metadata column
        :param catvar:
        :return:
        """
        unique_vals = []
        catvar_col = self.__get_metadata_column(catvar)

        i = 1
        while i < len(self.metadata):
            if self.metadata[i][catvar_col] not in unique_vals:
                unique_vals.append(self.metadata[i][catvar_col])
            i += 1
        return unique_vals

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
