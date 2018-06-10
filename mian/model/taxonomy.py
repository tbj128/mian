from mian.core.constants import TAXONOMY_FILENAME
from mian.core.data_io import DataIO
import ast


class Taxonomy(object):

    OTU_COL = 0
    TAXONOMY_COL = 1

    def __init__(self, user_id, pid):
        self.user_id = user_id
        self.pid = pid
        self.taxonomy_map = {}
        self.__load_taxonomy()

    def __load_taxonomy(self):
        tax = DataIO.tsv_to_table(self.user_id, self.pid, TAXONOMY_FILENAME)
        self.taxonomy_map = self.__get_taxonomy_mapping_from_dict(tax)

    def get_taxonomy_map(self):
        return self.taxonomy_map

    def __get_taxonomy_mapping_from_dict(self, taxonomyMapping):
        taxonomyMap = {}
        i = 0
        for row in taxonomyMapping:
            if i > 0:
                taxonomyMap[row[Taxonomy.OTU_COL]] = row[Taxonomy.TAXONOMY_COL:]
            i += 1
        return taxonomyMap
