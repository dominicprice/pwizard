from pathlib import Path

import click
from playhouse.db_url import connect

from pwizard.generate import Generator
from pwizard.utils.catch import catch_exception


@click.command("generate")
@click.argument(
    "config_file",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
)
@click.argument(
    "db_url",
    type=str,
)
@catch_exception(Exception)
def generate_cmd(config_file: Path, db_url: str):
    generator = Generator.from_config(config_file)
    with connect(db_url) as database:
        generator.generate(database)
