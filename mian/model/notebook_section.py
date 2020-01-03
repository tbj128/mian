import datetime
import uuid


class NotebookSection(object):

    def __init__(self, key: str = str(uuid.uuid4()), link: str = "", type: str = "",
                 content: str = "", date: str = datetime.datetime.now().isoformat(),
                 title: str = "", description: str = ""):
        self.key: str = key
        self.link: str = link
        self.type: str = type
        self.content: str = content
        self.date: str = date
        self.title: str = title
        self.description: str = description

    def fromDict(self, d):
        self.key = d["key"]
        self.link = d["link"]
        self.type = d["type"]
        self.content = d["content"]
        self.date = d["date"]
        self.title = d["title"]
        self.description = d["description"]
