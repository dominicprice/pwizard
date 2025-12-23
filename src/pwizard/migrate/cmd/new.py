import os
from pathlib import Path

import click
import jinja2

from pwizard.migrate.generate import generate_new_migration
from pwizard.utils.catch import catch_exception


@click.command("new")
@click.option(
    "--output-dir",
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

    # generate the migration file
    generate_new_migration(
        output_directory / name,
        template,
        name,
        description,
    )
