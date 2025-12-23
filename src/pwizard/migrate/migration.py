import abc
import hashlib
import importlib.util
import os
from types import ModuleType
import re
import typing as t
from pathlib import Path

import peewee
import sqlparse

if t.TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

NULLHASH = "0000000000000000000000000000000000000000"


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


class FunctionMigration(Migration):
    def __init__(
        self, fn: t.Callable[[peewee.Database], None], name: str | None = None
    ):
        self._fn = fn
        self._name = name if name is not None else fn.__qualname__

    def name(self) -> str:
        return self._name

    def hash(self) -> str:
        return NULLHASH

    def execute(self, database: peewee.Database):
        self._fn(database)


class ModuleMigration(Migration):
    def __init__(self, module: str | ModuleType, package: str | None = None):
        if isinstance(module, ModuleType):
            self.module = module
        else:
            self.module = importlib.import_module(module, package)

    def name(self) -> str:
        return self.module.__name__

    def hash(self) -> str:
        return NULLHASH

    def execute(self, database: peewee.Database):
        self.module.migrate(database)


class ScriptMigration(Migration):
    def __init__(self, script_path: "StrOrBytesPath", name: str | None = None):
        self.path = Path(os.fsdecode(script_path))
        self._name = self.path.name if name is None else name
        self._hash: str | None = None
        spec = importlib.util.spec_from_file_location(self.name(), self.path)
        if spec is None:
            raise RuntimeError("failed to create spec for script")
        script = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise RuntimeError("failed to create loader for script")
        spec.loader.exec_module(script)

    def name(self) -> str:
        # returns a name which is a valid python module name
        return re.sub(r"\W|^(?=\d)", "_", str(self.path))

    def hash(self) -> str:
        if self._hash is None:
            with open(self.path, "rb") as f:
                self._hash = hashlib.sha256(f.read()).hexdigest()
        return self._hash

    def execute(self, database: peewee.Database):
        script.migrate(database)
