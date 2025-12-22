from dataclasses import dataclass
from enum import Enum

from peewee import Field


class DatabaseType(str, Enum):
    Postgresql = "postgresql"
    SQLite = "sqlite"
    MySQL = "mysql"
    Proxy = "proxy"

    @property
    def database(self) -> str:
        if self == DatabaseType.Postgresql:
            return "PostgresqlDatabase"
        elif self == DatabaseType.SQLite:
            return "SqliteDatabase"
        elif self == DatabaseType.MySQL:
            return "MySQL"
        elif self == DatabaseType.Proxy:
            return "DatabaseProxy"
        raise ValueError


@dataclass
class Column:
    name: str
    type: type[Field]
    params: dict[str, str]

    @property
    def definition(self) -> str:
        params = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name} = {self.type.__qualname__}({params})"

    def get_import(self) -> tuple[str | None, str]:
        modname = self.type.__module__
        if self.type.__module__ == "builtins" or self.type.__module__ == "":
            modname = None
        classname = self.type.__qualname__.split(".")[0]
        return modname, classname


@dataclass
class Index:
    fields: list[str]
    unique: bool

    @property
    def definition(self) -> str:
        fields = ", ".join('"' + f + '"' for f in self.fields)
        return f"(({fields}), {'True' if self.unique else 'False'})"


@dataclass
class Table:
    model_name: str
    table_name: str
    columns: list[Column]
    indexes: list[Index]
    schema: str | None
    primary_keys: list[str]
