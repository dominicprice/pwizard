from datetime import timedelta
from peewee import SqliteDatabase
from pathlib import Path

from pwizard.migrate import Migrator
from pwizard.migrate.hooks import MigrationHooksBase
from pwizard.migrate.migration import Migration, SQLMigration
from pwizard.migrate.warnings import MigrationWarning

dir = Path(__file__).parent


def test_migrations():
    database = SqliteDatabase(":memory:")

    hooks = AssertionHooks()
    migrator = Migrator(
        [
            SQLMigration(dir / "migrations_1" / "mig1.sql"),
            SQLMigration(dir / "migrations_1" / "mig2.sql"),
            SQLMigration(dir / "migrations_1" / "mig3.sql"),
        ],
        hooks=hooks,
    )

    # migration runs ok
    hooks.expect(0, 0, 3)
    migrator.migrate(database)

    # rerunning is a noop
    hooks.expect(3, 0, 0)
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
    hooks.expect(2, 1, 1)
    migrator.migrate(database)

    # still throws a warning about the first migration
    hooks.expect(3, 1, 0)
    migrator.migrate(database)

    # migrations3 swaps the first and second migrations
    migrator.set_migrations(
        [
            SQLMigration(dir / "migrations_3" / "mig1.sql"),
            SQLMigration(dir / "migrations_3" / "mig2.sql"),
            SQLMigration(dir / "migrations_3" / "mig3.sql"),
        ]
    )
    hooks.expect(1, 2, 0)
    migrator.migrate(database)

    # fix migrations
    migrator.fix_warnings = True
    # warns the first time that they were fixed
    hooks.expect(1, 2, 0)
    migrator.migrate(database)
    # no warnings second time
    hooks.expect(3, 0, 0)
    migrator.migrate(database)


class AssertionHooks(MigrationHooksBase):
    def __init__(self):
        self.expect(0, 0, 0)

    def expect(self, skipped: int, warned: int, applied: int):
        self.nskipped = skipped
        self.nwarned = warned
        self.napplied = applied
        self.migrations: list[str] = []

    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
        fixed: bool,
    ) -> None:
        if applied:
            self.migrations += [f"applied {migration.name()}"]
        elif warning is not None:
            if fixed:
                self.migrations += [f"fixed {migration.name()}"]
            else:
                self.migrations += [f"warned {migration.name()}"]
        else:
            self.migrations += [f"skipped {migration.name()}"]

    def on_finish_migrations(
        self,
        skipped: int,
        warned: int,
        applied: int,
        elapsed: timedelta,
    ) -> None:
        _ = elapsed
        assert skipped == self.nskipped, self.summarize(
            self.nskipped,
            skipped,
            "skipped",
        )
        assert warned == self.nwarned, self.summarize(
            self.nwarned,
            warned,
            "warned",
        )
        assert applied == self.napplied, self.summarize(
            self.napplied,
            applied,
            "applied",
        )

    def summarize(self, expected: int, actual: int, type_: str):
        return "\n".join(
            [f"expected {expected} events of type {type_}, got {actual}"]
            + self.migrations
        )
