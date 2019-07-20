import json
import os


class Quantiles(object):

    def __init__(self, user_id, pid):
        self.user_id = user_id
        self.pid = pid
        self.quantiles = {}
        self.load()

    def load(self):
        if len(self.quantiles) == 0:
            if os.path.exists(self.__get_map_path()):
                with open(self.__get_map_path()) as f:
                    map_from_json = json.load(f)
                    self.quantiles = map_from_json["quantiles"]

    def update_quantile(self, sample_metadata_name, min, max, quantiles, type, quantile_type):
        quantile = {
            "min": min,
            "max": max,
            "quantiles": quantiles,
            "type": type, # eg. q_50
            "quantile_type": quantile_type # gene or metadata
        }
        self.quantiles[sample_metadata_name] = quantile

    def remove_quantile(self, sample_metadata_name):
        del self.quantiles[sample_metadata_name]

    def exists(self, sample_metadata_name):
        return sample_metadata_name in self.quantiles

    def get_existing(self, sample_metadata_name):
        return_obj = self.quantiles[sample_metadata_name]
        return_obj["new"] = False
        return return_obj

    def save(self):
        map_from_json = {
            "quantiles": self.quantiles
        }

        with open(self.__get_map_path(), 'w') as outfile:
            json.dump(map_from_json, outfile)

    def __get_map_path(self):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))  # Gets the parent folder
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, self.user_id)
        project_dir = os.path.join(project_dir, self.pid)
        map_path = os.path.join(project_dir, "quantiles.txt")
        return map_path