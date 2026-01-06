import typing as t
import logging
from datetime import timedelta

from colorama import Fore, Style

from pwizard.migrate.migration import Migration
from pwizard.migrate.warnings import MigrationWarning
from pwizard.utils.duration import format_timedelta


class MigrationHooksBase:
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


class MigrationHooksWarningsAsErrors(MigrationHooksBase):
    """
    Migrations hooks which raises a RuntimeError if a warnings
    is emitted
    """

    @t.override
    def on_after_migration(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
        fixed: bool,
    ):
        if warning is not None:
            raise RuntimeError(warning.describe())


class MigrationHooksWarnings(MigrationHooksBase):
    "Migration hooks which prints any warnings generated"

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


class MigrationHooksSummary(MigrationHooksBase):
    "Migrations hooks which print warnings and a summary"

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
            + Style.RESET_ALL
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


class MigrationHooksVerbose(MigrationHooksBase):
    """
    Migration hooks which print warnings, a summary and
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
            + Style.RESET_ALL
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


class MigrationHooksLogger(MigrationHooksBase):
    """
    Migration hooks which print warnings, a summary and
    progress for each individual migration
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @t.override
    def on_begin_migrations(self, num_migrations: int):
        self.logger.info("starting %d migrations", num_migrations)

    @t.override
    def on_finish_migrations(
        self, skipped: int, warned: int, applied: int, elapsed: timedelta
    ):
        self.logger.info(
            "completed in %s, %d skipped, %d warnings, %d applied",
            format_timedelta(elapsed),
            skipped,
            warned,
            applied,
        )

    @t.override
    def on_before_migration(self, migration: Migration):
        self.logger.info("applying: %s", migration.name())

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
            self.logger.info("applied: %s", migration.name())
        else:
            self.logger.info("skipped: %s", migration.name())
        if warning is not None:
            self.logger.warning(
                "%s: %s: %s",
                "fixed" if fixed else "warning",
                migration.name(),
                warning.describe(),
            )
