import json
import os


class Map(object):

    def __init__(self, user_id, pid):
        self.user_id = user_id
        self.pid = pid
        self.project_name = ""
        self.subsampled_value = ""
        self.subsampled_type = ""
        self.subsampled_removed_samples = []
        self.orig_biom_name = ""
        self.orig_otu_table_name = ""
        self.orig_taxonomy_name = ""
        self.orig_sample_metadata_name = ""
        self.taxonomy_type = ""
        self.load()

    def load(self):
        if os.path.exists(self.__get_map_path()):
            with open(self.__get_map_path()) as f:
                map_from_json = json.load(f)
                self.project_name = map_from_json["project_name"]
                self.subsampled_value = map_from_json["subsampled_value"]
                self.subsampled_type = map_from_json["subsampled_type"]
                self.subsampled_removed_samples = map_from_json["subsampled_removed_samples"]
                self.orig_biom_name = map_from_json["orig_biom_name"]
                self.orig_otu_table_name = map_from_json["orig_otu_table_name"]
                self.orig_taxonomy_name = map_from_json["orig_taxonomy_name"]
                self.orig_sample_metadata_name = map_from_json["orig_sample_metadata_name"]
                self.taxonomy_type = map_from_json["taxonomy_type"]

    def save(self):
        map_from_json = {
            "project_name": self.project_name,
            "subsampled_value": self.subsampled_value,
            "subsampled_type": self.subsampled_type,
            "subsampled_removed_samples": self.subsampled_removed_samples,
            "orig_biom_name": self.orig_biom_name,
            "orig_otu_table_name": self.orig_otu_table_name,
            "orig_taxonomy_name": self.orig_taxonomy_name,
            "orig_sample_metadata_name": self.orig_sample_metadata_name,
            "taxonomy_type": self.taxonomy_type
        }

        with open(self.__get_map_path(), 'w') as outfile:
            json.dump(map_from_json, outfile)

    def __get_map_path(self):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, self.user_id)
        project_dir = os.path.join(project_dir, self.pid)
        map_path = os.path.join(project_dir, "map.txt")
        return map_path