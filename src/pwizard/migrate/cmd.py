import os
from datetime import datetime
from glob import glob
from pathlib import Path

import click
import jinja2
from colorama import init as init_colorama
from playhouse.db_url import connect

from pwizard.migrate import Migrator
from pwizard.migrate.hooks import (
    MigrationHooksBase,
    MigrationHooksSummary,
    MigrationHooksVerbose,
    MigrationHooksWarnings,
)
from pwizard.migrate.migration import Migration, SQLMigration
from pwizard.utils.catch import catch_exception


@click.group("migrate")
def migrate_cmd():
    pass


@migrate_cmd.command("new")
@click.option(
    "--output-directory",
    "-o",
    default=".",
    type=click.Path(
        exists=True,
        file_okay=False,
        writable=True,
        path_type=Path,
    ),
    help="Path to generate new migration in",
)
@click.option(
    "--type",
    "-t",
    default="auto",
    type=click.Choice(["auto", "sql", "py"]),
    help="Migration type",
)
@click.option(
    "--templates-dir",
    "-T",
    default=None,
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=Path,
    ),
    help="Path where templates (named migration.TYPE.tmpl) should be found",
)
@click.argument("name")
@click.argument("description", default=None)
@catch_exception(Exception)
def migrate_new_cmd(
    name: str,
    description: str | None,
    type: str,
    templates_dir: Path | None,
    output_directory: Path,
):
    # default to the builtin templates
    if templates_dir is None:
        templates_dir = Path(__file__).parent / "templates"

    # attempt to guess migration type
    if type == "auto":
        _, ext = os.path.splitext(name)
        if ext == "":
            raise ValueError("cannot guess migration type")
        type = ext[1:]

    # append file extension if not included in name
    if not name.endswith("." + type):
        name += "." + type

    # create the template
    loader = jinja2.FileSystemLoader(templates_dir)
    jinja = jinja2.Environment(loader=loader)
    try:
        template = jinja.get_template(f"migration.{type}.tmpl")
    except jinja2.TemplateNotFound:
        raise ValueError("no template for " + type + " found")

    # build the data for the template
    data = {
        "generated_at": datetime.now(),
        "name": name,
        "description": description,
    }

    # generate the output
    with open(output_directory / name, "w") as f:
        for s in template.generate(**data):
            f.write(s)


@migrate_cmd.command("run")
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
    type=click.Choice(["auto", "always", "never"]),
    help="Control how the output is colored",
)
@click.option(
    "--migration",
    "-m",
    multiple=True,
    help="A glob pattern for files to be used as migrations",
)
@click.argument("db_url", type=str)
@catch_exception(Exception)
def migrate_run_cmd(
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
