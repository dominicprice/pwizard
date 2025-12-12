import abc
from datetime import timedelta
import click
from glob import glob
import sys

from playhouse.db_url import connect

from pwizard.migrate import MigrationWarning, Migrator
from pwizard.migrate.migration import Migration, SQLMigration


@click.command("migrate")
@click.option("--verbose", "-v", count=True)
@click.option("--table-name", "-t", default="migrations")
@click.option("--text-type", "-T", default="TEXT")
@click.option(
    "--color",
    "-c",
    default="auth",
    type=click.Choice(
        ["auto", "always", "never"],
    ),
)
@click.option(
    "--migration",
    "-m",
    multiple=True,
)
@click.argument("db_url", type=str)
def main(
    db_url: str,
    verbose: int,
    table_name: str,
    text_type: str,
    color: str,
    migration: list[str],
):
    migrations: list[Migration] = []
    for pat in migration:
        migrations.extend([SQLMigration(f) for f in glob(pat)])

    migrator = Migrator(
        migrations,
        table_name=table_name,
        text_type=text_type,
    )

    if verbose == 1:
        Verbosity1Hooks(color).connect(migrator)
    elif verbose == 2:
        Verbosity2Hooks(color).connect(migrator)
    elif verbose >= 3:
        Verbosity3Hooks(color).connect(migrator)

    with connect(db_url) as database:
        migrator.migrate(database)


color_warn = ""
color_reset = ""


class VerbosityHooksBase(abc.ABC):
    def __init__(self, color: str):
        if color == "auto":
            if sys.stdout.isatty():
                color = "always"

        if color == "always":
            self.cyellow = "\033[1;33m"
            self.ccyan = "\033[0;36m"
            self.cgreen = "\033[0;32m"
            self.cblue = "\033[0;34m"
            self.creset = "\033[0m"
        elif color == "never":
            self.cyellow = ""
            self.ccyan = ""
            self.cgreen = ""
            self.cblue = ""
            self.creset = ""
        else:
            raise ValueError("invalid value for --color flag")

    @abc.abstractmethod
    def connect(self, migrator: Migrator): ...


class Verbosity1Hooks(VerbosityHooksBase):
    def connect(self, migrator: Migrator):
        migrator.on_after_migration = self.on_after_migration

    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
    ):
        _ = applied
        if warning is not None:
            print(
                self.cyellow
                + "warning: "
                + migration.name()
                + warning.describe()
                + self.creset
            )


class Verbosity2Hooks(VerbosityHooksBase):
    def connect(self, migrator: Migrator):
        migrator.on_begin_migrations = self.on_begin_migrations
        migrator.on_after_migration = self.on_after_migration
        migrator.on_finish_migrations = self.on_finish_migrations

    def on_begin_migrations(self, num_migrations: int):
        print(
            self.ccyan
            + "Starting "
            + str(num_migrations)
            + " migrations..."
            + self.creset
        )

    def on_finish_migrations(
        self, skipped: int, warned: int, applied: int, elapsed: timedelta
    ):
        print(
            self.ccyan
            + "Completed in "
            + "{:.3f}".format(elapsed.total_seconds)
            + "s"
            + self.creset
        )
        print(
            self.cblue
            + str(skipped)
            + " skipped"
            + self.creset
            + ", "
            + self.cyellow
            + str(warned)
            + " warnings"
            + self.creset
            + ", "
            + self.cgreen
            + str(applied)
            + " applied"
        )

    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
    ):
        _ = applied
        if warning is not None:
            print(
                self.cyellow
                + "warning: "
                + migration.name()
                + warning.describe()
                + self.creset
            )


class Verbosity3Hooks(VerbosityHooksBase):
    def connect(self, migrator: Migrator):
        migrator.on_begin_migrations = self.on_begin_migrations
        migrator.on_before_migration = self.on_before_migration
        migrator.on_after_migration = self.on_after_migration
        migrator.on_finish_migrations = self.on_finish_migrations

    def on_begin_migrations(self, num_migrations: int):
        print(
            self.ccyan
            + "Starting "
            + str(num_migrations)
            + " migrations..."
            + self.creset
        )

    def on_finish_migrations(
        self, skipped: int, warned: int, applied: int, elapsed: timedelta
    ):
        print(
            self.ccyan
            + "Completed in "
            + "{:.3f}".format(elapsed.total_seconds)
            + "s"
            + self.creset
        )
        print(
            self.cblue
            + str(skipped)
            + " skipped"
            + self.creset
            + ", "
            + self.cyellow
            + str(warned)
            + " warnings"
            + self.creset
            + ", "
            + self.cgreen
            + str(applied)
            + " applied"
        )

    def on_before_migration(self, migration: Migration):
        print("applying " + migration.name(), end="...")

    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
    ):
        _ = migration
        if applied:
            print("applied")
        else:
            print("skipped")
        if warning is not None:
            print(self.cyellow + "warning: " + warning.describe() + self.creset)
