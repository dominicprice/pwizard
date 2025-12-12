import click
from pwizard.generate.cmd import generate_cmd
from pwizard.migrate.cmd import migrate_cmd


@click.group("pwizard")
def main():
    pass


main.add_command(generate_cmd)
main.add_command(migrate_cmd)

if __name__ == "__main__":
    main()
