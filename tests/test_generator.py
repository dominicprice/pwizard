from pathlib import Path
from glob import glob
from peewee import SqliteDatabase
from pathlib import Path

from pwizard.generate import Generator
from pwizard.migrate import Migrator
from pwizard.migrate.migration import SQLMigration

dir = Path(__file__).parent
schemas_dir = dir / "schemas"
output_dir = dir / "output"
output_dir.mkdir(exist_ok=True)


def test_schemas():
    for schema in glob("*.sql", root_dir=schemas_dir):
        database = SqliteDatabase(":memory:")
        migrator = Migrator([SQLMigration(schemas_dir / schema)])
        migrator.migrate(database)

        generator = Generator(output_dir / schema.replace(".sql", ".py"))
        generator.generate(database)
