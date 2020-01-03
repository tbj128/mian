import json
from typing import List, Dict

import os
import datetime

from mian.model.notebook_section import NotebookSection


class Notebook(object):

    def __init__(self, user_id: str, pid: str):
        self.user_id: str = user_id
        self.pid: str = pid
        self.title: str = ""
        self.create_date: str = datetime.datetime.now().isoformat()
        self.sections: List[Dict] = []
        self.load()

    def update_section_title(self, key: str, title: str):
        for i in range(len(self.sections)):
            if self.sections[i]["key"] == key:
                self.sections[i]["title"] = title
        self.save()

    def update_section_description(self, key: str, description: str):
        for i in range(len(self.sections)):
            if self.sections[i]["key"] == key:
                self.sections[i]["description"] = description
        self.save()

    def add_section(self, section: NotebookSection):
        self.sections.append(vars(section))
        self.save()

    def remove_section(self, key: str):
        index_to_del = -1
        for i in range(len(self.sections)):
            if self.sections[i]["key"] == key:
                index_to_del = i
        if index_to_del >= 0:
            del self.sections[index_to_del]
            self.save()

    def load(self):
        if os.path.exists(self.__get_path()):
            with open(self.__get_path()) as f:
                notebook_from_json = json.load(f)
                self.sections = notebook_from_json["sections"]
                self.title = notebook_from_json["title"]
                self.create_date = notebook_from_json["create_date"]
                for i in range(len(self.sections)):
                    if self.sections[i]["type"] == "table":
                        if type(self.sections[i]["content"]) is str:
                            self.sections[i]["content"] = json.loads(self.sections[i]["content"])

    def save(self):
        notebook_from_json = {
            "sections": self.sections,
            "title": self.title,
            "create_date": self.create_date,
        }

        with open(self.__get_path(), 'w') as outfile:
            json.dump(notebook_from_json, outfile)

    def __get_path(self):
        project_dir = os.path.dirname(__file__)
        project_dir = os.path.abspath(os.path.join(project_dir, os.pardir))
        project_dir = os.path.join(project_dir, "data")
        project_dir = os.path.join(project_dir, self.user_id)
        project_dir = os.path.join(project_dir, self.pid)
        path = os.path.join(project_dir, "notebook.json")
        return path
