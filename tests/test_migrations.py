from peewee import SqliteDatabase
from pathlib import Path

from pwizard.migrate import Migrator
from pwizard.migrate.migration import SQLMigration

dir = Path(__file__).parent


def test_migrations():
    database = SqliteDatabase(":memory:")

    migrator = Migrator(
        [
            SQLMigration(dir / "migrations_1" / "mig1.sql"),
            SQLMigration(dir / "migrations_1" / "mig2.sql"),
            SQLMigration(dir / "migrations_1" / "mig3.sql"),
        ]
    )

    s, w, a = 0, 0, 0

    def finish_hook(skipped, warned, applied, elapsed):
        _ = elapsed
        assert skipped == s
        assert warned == w
        assert applied == a

    migrator.on_finish_migrations = finish_hook

    # migration runs ok
    s, w, a = 0, 0, 3
    migrator.migrate(database)
    # rerunning is a noop
    s, w, a = 3, 0, 0
    migrator.migrate(database)

    # migrations2 has a different first migration
    migrator.set_migrations(
        [
            SQLMigration(dir / "migrations_2" / "mig1.sql"),
            SQLMigration(dir / "migrations_2" / "mig2.sql"),
            SQLMigration(dir / "migrations_2" / "mig3.sql"),
            SQLMigration(dir / "migrations_2" / "mig4.sql"),
        ]
    )

    # throws a warning about the first migration
    s, w, a = 2, 1, 1
    migrator.migrate(database)
    # still throws a warning about the first migration
    s, w, a = 3, 1, 0
    migrator.migrate(database)

    # migrations3 swaps the first and second migrations
    migrator.set_migrations(
        [
            SQLMigration(dir / "migrations_3" / "mig1.sql"),
            SQLMigration(dir / "migrations_3" / "mig2.sql"),
            SQLMigration(dir / "migrations_3" / "mig3.sql"),
        ]
    )
    s, w, a = 0, 3, 0
