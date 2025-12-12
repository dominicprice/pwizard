from pwizard.generate import Generator
from playhouse.db_url import connect
import click
from pathlib import Path


@click.command("generate")
@click.argument(
    "config_file",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
)
@click.argument("db_url", type=str)
def main(config_file: Path, db_url: str):
    generator = Generator.from_config(config_file)
    with connect(db_url) as database:
        generator.generate(database)


if __name__ == "__main__":
    main()
