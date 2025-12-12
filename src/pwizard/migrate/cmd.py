import typing as t
from datetime import timedelta
from glob import glob

import click
from colorama import Fore, Style
from colorama import init as init_colorama
from playhouse.db_url import connect

from pwizard.migrate import MigrationWarning, Migrator
from pwizard.migrate.hooks import MigrationHooks
from pwizard.migrate.migration import Migration, SQLMigration
from pwizard.utils.duration import format_timedelta


@click.command("migrate")
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Set the verbosity level (can be specified up to three times)",
)
@click.option(
    "--table-name",
    "-t",
    default="migrations",
    help="The name of the migrations table in the database",
)
@click.option(
    "--text-type",
    "-T",
    default="TEXT",
    help="The type of text fields to use when creating the migrations table",
)
@click.option(
    "--fix",
    "-f",
    is_flag=True,
    help="Fix migrations which would usually generate a warning",
)
@click.option(
    "--color",
    "-c",
    default="auto",
    type=click.Choice(
        ["auto", "always", "never"],
    ),
    help="Control how the output is colored",
)
@click.option(
    "--migration",
    "-m",
    multiple=True,
    help="A glob pattern for sql files to be used as migrations",
)
@click.argument("db_url", type=str)
def migrate_cmd(
    db_url: str,
    verbose: int,
    table_name: str,
    text_type: str,
    fix: bool,
    color: str,
    migration: list[str],
):
    # set up coloring
    if color == "always":
        # never remove ansi sequences
        init_colorama(strip=False)
    elif color == "never":
        # always remove ansi sequences
        init_colorama(strip=True)
    elif color == "auto":
        # only keep ansi sequences for tty
        init_colorama(strip=None)

    # collect all migrations
    migrations: list[Migration] = []
    for pat in migration:
        migrations.extend([SQLMigration(f) for f in sorted(glob(pat))])

    # set up hooks based on verbosity level
    hooks: MigrationHooks = Verbosity0Hooks()
    if verbose == 1:
        hooks = Verbosity1Hooks()
    elif verbose == 2:
        hooks = Verbosity2Hooks()
    elif verbose >= 3:
        hooks = Verbosity3Hooks()

    # initialise the migrator
    migrator = Migrator(
        migrations,
        table_name=table_name,
        text_type=text_type,
        fix_warnings=fix,
        hooks=hooks,
    )

    # perform migrations
    with connect(db_url) as database:
        migrator.migrate(database)


class Verbosity0Hooks(MigrationHooks):
    "Hooks when no verbose flag given, do not print any output"

    pass


class Verbosity1Hooks(MigrationHooks):
    "Hooks when one verbosity flag is given, print warnings"

    @t.override
    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
        fixed: bool,
    ):
        _ = applied
        if warning is not None:
            print(
                Fore.YELLOW
                + ("fixed: " if fixed else "warning: ")
                + migration.name()
                + warning.describe()
                + Style.RESET_ALL
            )


class Verbosity2Hooks(MigrationHooks):
    "Hooks when two verbosity flags are given, print warnings and summary"

    @t.override
    def on_begin_migrations(self, num_migrations: int):
        print(
            Fore.CYAN
            + "Starting "
            + str(num_migrations)
            + " migrations..."
            + Style.RESET_ALL
        )

    @t.override
    def on_finish_migrations(
        self,
        skipped: int,
        warned: int,
        applied: int,
        elapsed: timedelta,
    ):
        print(Fore.CYAN + "Completed in " + format_timedelta(elapsed) + Style.RESET_ALL)
        print(
            Fore.BLUE
            + str(skipped)
            + " skipped"
            + Style.RESET_ALL
            + ", "
            + Fore.YELLOW
            + str(warned)
            + " warnings"
            + Style.RESET_ALL
            + ", "
            + Fore.GREEN
            + str(applied)
            + " applied"
        )

    @t.override
    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
        fixed: bool,
    ):
        _ = applied
        if warning is not None:
            print(
                Fore.YELLOW
                + ("fixed: " if fixed else "warning: ")
                + migration.name()
                + warning.describe()
                + Style.RESET_ALL
            )


class Verbosity3Hooks(MigrationHooks):
    """
    Hooks when three verbosity flags are given, print warnings, summary and
    progress for each individual migration
    """

    @t.override
    def on_begin_migrations(self, num_migrations: int):
        print(
            Fore.CYAN
            + "Starting "
            + str(num_migrations)
            + " migrations..."
            + Style.RESET_ALL
        )

    @t.override
    def on_finish_migrations(
        self, skipped: int, warned: int, applied: int, elapsed: timedelta
    ):
        print(Fore.CYAN + "Completed in " + format_timedelta(elapsed) + Style.RESET_ALL)
        print(
            Fore.BLUE
            + str(skipped)
            + " skipped"
            + Style.RESET_ALL
            + ", "
            + Fore.YELLOW
            + str(warned)
            + " warnings"
            + Style.RESET_ALL
            + ", "
            + Fore.GREEN
            + str(applied)
            + " applied"
        )

    @t.override
    def on_before_migration(self, migration: Migration):
        print("applying " + migration.name(), end="...")

    @t.override
    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
        fixed: bool,
    ):
        _ = migration
        if applied:
            print("applied")
        else:
            print("skipped")
        if warning is not None:
            print(
                Fore.YELLOW
                + ("fixed: " if fixed else "warning: ")
                + warning.describe()
                + Style.RESET_ALL
            )
