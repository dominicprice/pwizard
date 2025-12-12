from datetime import timedelta

from pwizard.migrate.migration import Migration
from pwizard.migrate.warnings import MigrationWarning


class MigrationHooks:
    """
    Base class for defining hooks during the migration lifecycle. This
    default implementation performs no actions, but can be subclassed
    and implementations provided.
    """

    def on_begin_migrations(self, num_migrations: int) -> None:
        pass

    def on_check_migration_table_exists(self) -> None:
        pass

    def on_checked_migration_table_exists(self, created: bool) -> None:
        pass

    def on_before_migration(self, migration: Migration) -> None:
        pass

    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
        fixed: bool,
    ) -> None:
        pass

    def on_finish_migrations(
        self,
        skipped: int,
        warned: int,
        applied: int,
        elapsed: timedelta,
    ) -> None:
        pass
