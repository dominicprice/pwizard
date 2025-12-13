from glob import glob

import click
from colorama import init as init_colorama
from playhouse.db_url import connect

from pwizard.migrate import Migrator
from pwizard.migrate.hooks import (
    MigrationHooksBase,
    MigrationHooksWarnings,
    MigrationHooksSummary,
    MigrationHooksVerbose,
)
from pwizard.migrate.migration import Migration, SQLMigration


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
    hooks = MigrationHooksBase()
    if verbose == 1:
        hooks = MigrationHooksWarnings()
    elif verbose == 2:
        hooks = MigrationHooksSummary()
    elif verbose >= 3:
        hooks = MigrationHooksVerbose()

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
