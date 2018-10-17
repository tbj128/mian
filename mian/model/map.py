import json
import os


class Map(object):

    def __init__(self, user_id, pid):
        self.user_id = user_id
        self.pid = pid
        self.project_name = ""
        self.table_name = ""
        self.sample_metadata_name = ""
        self.load()

    def load(self):
        if os.path.exists(self.__get_map_path()):
            with open(self.__get_map_path()) as f:
                map_from_json = json.load(f)
                self.project_name = map_from_json["project_name"]
                self.table_name = map_from_json["table_name"]
                self.sample_metadata_name = map_from_json["sample_metadata_name"]

    def save(self):
        map_from_json = {
            "project_name": self.project_name,
            "table_name": self.table_name,
            "sample_metadata_name": self.sample_metadata_name,
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