import abc
import hashlib
import os
import typing as t
from pathlib import Path

import peewee
import sqlparse

if t.TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


class Migration(abc.ABC):
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def hash(self) -> str: ...

    @abc.abstractmethod
    def execute(self, database: peewee.Database): ...


class SQLMigration(Migration):
    def __init__(self, path: "StrOrBytesPath", name: str | None = None):
        self.path = Path(os.fsdecode(path))
        self._name = self.path.name if name is None else name
        self._hash: str | None = None

    def name(self) -> str:
        return self._name

    def hash(self) -> str:
        if self._hash is None:
            with open(self.path, "rb") as f:
                self._hash = hashlib.sha256(f.read()).hexdigest()
        return self._hash

    def execute(self, database: peewee.Database):
        with open(self.path, "r") as f:
            statements = sqlparse.split(f.read())
        for statement in statements:
            database.execute_sql(statement)
