from enum import Enum, IntEnum
from pathlib import Path
from glob import glob
from peewee import Field, SqliteDatabase, TextField
from pathlib import Path

from pwizard.generate import Generator
from pwizard.migrate import Migrator
from pwizard.migrate.migration import SQLMigration
import importlib.util
import sys

dir = Path(__file__).parent
schemas_dir = dir / "schemas"
output_dir = dir / "output"
output_dir.mkdir(exist_ok=True)


class Colour(str, Enum):
    Red = "red"
    Blue = "blue"
    Green = "green"


class ColourField(Field):
    field_type = "COLOUR"

    def adapt(self, value):
        return Colour(value)


class Status(IntEnum):
    Active = 0
    Inactive = 1
    Deactivated = 2


class StatusField(Field):
    field_type = "STATUS"

    def adapt(self, value):
        return Status(value)


def test_schemas():
    for schema in glob("*.sql", root_dir=schemas_dir):
        database = SqliteDatabase(":memory:")
        migrator = Migrator([SQLMigration(schemas_dir / schema)])
        migrator.migrate(database)

        generator = Generator(output_dir / schema.replace(".sql", ".py"))
        generator.generate(database)


def test_custom_types(tmp_path: Path):
    database = SqliteDatabase(":memory:")
    migrator = Migrator([SQLMigration(schemas_dir / "customtype.sql")])
    migrator.migrate(database)

    generator = Generator(
        tmp_path / "customtype.py",
        custom_column_types={
            "name": TextField,
            "colour": ColourField,
            "status": StatusField,
        },
    )
    generator.generate(database)
    database.close()

    spec = importlib.util.spec_from_file_location(
        "customtype",
        tmp_path / "customtype.py",
    )
    assert spec is not None
    customtype = importlib.util.module_from_spec(spec)
    sys.modules["customtype"] = customtype
    assert spec.loader is not None
    spec.loader.exec_module(customtype)

    database = customtype.connect(":memory:")
    migrator.migrate(database)

    customtype.Custom.create(
        name="Alice",
        favourite_colour=Colour.Blue,
        status=Status.Deactivated,
    )
    customtype.Custom.create(
        name="Bob",
        favourite_colour=Colour.Red,
        status=Status.Active,
    )

    assert customtype.Custom.select().count() == 2
    res = (
        customtype.Custom.select(
            customtype.Custom.status, customtype.Custom.favourite_colour
        )
        .where(customtype.Custom.name == "Alice")
        .get()
    )
    assert res.favourite_colour is Colour.Blue
    assert res.status is Status.Deactivated
