from dataclasses import dataclass
from datetime import datetime
from typing import Set

from git import Actor
from git import Commit


@dataclass
class RemoteUser:
    name: str
    email: str

    def to_json(self):
        return {"name": self.name, "email": self.email, "username": self.email}


class RemoteCommit:
    def __init__(self, url_pattern: str, source: Commit):
        self.revision: str = source.hexsha
        self.message: str = source.message
        author: Actor = source.author
        self.author = RemoteUser(author.name, author.email)
        self.date: datetime = source.committed_datetime
        self.files: Set[str] = set()
        self.parents: Set[str] = set(p.hexsha for p in source.iter_parents())
        self.url = url_pattern.replace("REVISION", self.revision)

    def to_json(self):
        return {
            "revision": self.revision,
            "message": self.message,
            "author": self.author.to_json(),
            "date": self.date.isoformat(),
            "files": list(self.files)[:200],
            "parents": list(self.parents)[:200],
            "url": self.url,
        }


class RemoteFile:
    def __init__(self, file_url_pattern: str, revision: str, path: str):
        self.path = path
        self.url = file_url_pattern.replace("REVISION", revision).replace("PATH", path)
        self.additions = 0
        self.deletions = 0

    def to_json(self):
        return {
            "path": self.path,
            "url": self.url,
            "additions": self.additions,
            "deletions": self.deletions,
        }
