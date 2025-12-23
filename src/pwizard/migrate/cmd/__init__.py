import click

from pwizard.migrate.cmd.new import migrate_new_cmd
from pwizard.migrate.cmd.run import migrate_run_cmd


@click.group("migrate")
def migrate_cmd():
    pass


migrate_cmd.add_command(migrate_new_cmd)
migrate_cmd.add_command(migrate_run_cmd)
