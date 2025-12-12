import abc
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import time_ns

import peewee

from pwizard.migrate.migration import Migration


@dataclass
class AppliedMigration:
    parent: str | None
    hash: str
    applied_at: datetime


class MigrationWarning(abc.ABC):
    @abc.abstractmethod
    def describe(self) -> str: ...


class HashesDifferWarning(MigrationWarning):
    def __init__(self, hash: str, previous_hash: str, applied_at: datetime):
        self.hash = hash
        self.previous_hash = previous_hash
        self.applied_at = applied_at

    def describe(self) -> str:
        hash_trunc = 8
        if len(self.hash) > hash_trunc:
            hash = self.hash[:hash_trunc] + "..."
        else:
            hash = self.hash
        if len(self.previous_hash) > hash_trunc:
            previous_hash = self.previous_hash[:hash_trunc] + "..."
        else:
            previous_hash = self.previous_hash
        return f"hash '{hash}' differs from previous application of the migration at {self.applied_at} with hash '{previous_hash}'"


class ParentDiffersWarning(MigrationWarning):
    def __init__(
        self, parent: str | None, previous_parent: str | None, applied_at: datetime
    ):
        self.parent = parent
        self.previous_parent = previous_parent
        self.applied_at = applied_at

    def describe(self) -> str:
        return f"parent '{self.parent}' differs from previous application of the migration at {self.applied_at} with parent '{self.previous_parent}'"


class OnBeginMigrationsFn(t.Protocol):
    def __call__(self, num_migrations: int) -> None: ...


class OnCheckMigrationTableExistsFn(t.Protocol):
    def __call__(self) -> None: ...


class OnCheckedMigrationTableExistsFn(t.Protocol):
    def __call__(self, created: bool) -> None: ...


class OnBeforeMigrationFn(t.Protocol):
    def __call__(self, migration: Migration) -> None: ...


class OnAfterMigrationFn(t.Protocol):
    def __call__(
        self,
        migration: Migration,
        applied: bool,
        warning: MigrationWarning | None,
    ) -> None: ...


class OnFinishMigrationsFn(t.Protocol):
    def __call__(
        self,
        skipped: int,
        warned: int,
        applied: int,
        elapsed: timedelta,
    ) -> None: ...


class Migrator:
    def __init__(
        self,
        migrations: t.Iterable[Migration] | None = None,
        table_name: str = "migrations",
        text_type: str = "TEXT",
    ):
        self.migrations = list(migrations or [])
        self.table_name = table_name
        self.text_type = text_type

        # hooks
        self.on_begin_migrations: OnBeginMigrationsFn | None = None
        self.on_check_migration_table_exists: OnCheckMigrationTableExistsFn | None = (
            None
        )
        self.on_checked_migration_table_exists: (
            OnCheckedMigrationTableExistsFn | None
        ) = None
        self.on_before_migration: OnBeforeMigrationFn | None = None
        self.on_after_migration: OnAfterMigrationFn | None = None
        self.on_finish_migrations: OnFinishMigrationsFn | None = None

    def set_migrations(self, migrations: t.Iterable[Migration]):
        self.migrations = list(migrations)

    def migrate(self, database: peewee.Database):
        if self.on_begin_migrations:
            self.on_begin_migrations(len(self.migrations))

        skipped = 0
        skipped_with_warning = 0
        applied = 0
        parent: str | None = None
        start_time = time_ns()

        with database.atomic():
            self._ensure_migrations_table(database)
            for migration in self.migrations:
                if self.on_before_migration:
                    self.on_before_migration(migration)

                was_applied = False
                warning: MigrationWarning | None = None
                applied_migration = self._get_migration(database, migration)
                if applied_migration is None:
                    self._apply_migration(database, migration, parent)
                    was_applied = True
                else:
                    warning = self._skip_migration(
                        migration,
                        parent,
                        applied_migration,
                    )

                if was_applied:
                    applied += 1
                elif warning is not None:
                    skipped_with_warning += 1
                else:
                    skipped += 1

                if self.on_after_migration:
                    self.on_after_migration(migration, was_applied, warning)

                parent = migration.name()

        end_time = time_ns()
        if self.on_finish_migrations:
            elapsed_seconds = (end_time - start_time) / 1e9
            self.on_finish_migrations(
                skipped,
                skipped_with_warning,
                applied,
                timedelta(seconds=elapsed_seconds),
            )

    def _ensure_migrations_table(self, database: peewee.Database):
        if self.on_check_migration_table_exists:
            self.on_check_migration_table_exists()
        if database.table_exists(self.table_name):
            if self.on_checked_migration_table_exists:
                self.on_checked_migration_table_exists(False)
            return
        stmt = create_migrations_table_sql.format(
            table_name=self.table_name,
            text_type=self.text_type,
        )
        database.execute_sql(stmt)
        if self.on_checked_migration_table_exists:
            self.on_checked_migration_table_exists(True)

    def _apply_migration(
        self,
        database: peewee.Database,
        migration: Migration,
        parent: str | None,
    ):
        migration.execute(database)

        stmt = insert_migration_sql.format(
            table_name=self.table_name,
            param=database.param,
        )
        values = (
            migration.name(),
            parent,
            migration.hash(),
            datetime_to_string(datetime.now()),
        )
        database.execute_sql(stmt, values)

        if self.on_after_migration:
            self.on_after_migration(migration, True, None)

    def _skip_migration(
        self,
        migration: Migration,
        parent: str | None,
        applied_migration: AppliedMigration,
    ) -> MigrationWarning | None:
        if applied_migration.hash != migration.hash():
            return HashesDifferWarning(
                migration.hash(),
                applied_migration.hash,
                applied_migration.applied_at,
            )
        elif applied_migration.parent != parent:
            return ParentDiffersWarning(
                parent,
                applied_migration.parent,
                applied_migration.applied_at,
            )

        return None

    def _get_migration(
        self,
        database: peewee.Database,
        migration: Migration,
    ) -> AppliedMigration | None:
        stmt = get_migration_sql.format(
            table_name=self.table_name,
            param=database.param,
        )
        cursor = database.execute_sql(stmt, (migration.name(),))
        row = cursor.fetchone()
        if row is None:
            return None
        return AppliedMigration(row[0], row[1], datetime_from_string(row[2]))


def datetime_from_string(s: str) -> datetime:
    return datetime.fromisoformat(s)


def datetime_to_string(d: datetime) -> str:
    return d.isoformat()


create_migrations_table_sql = """
CREATE TABLE {table_name}(
    name {text_type} NOT NULL PRIMARY KEY,
    parent {text_type},
    hash {text_type} NOT NULL,
    applied_at {text_type} NOT NULL
);
"""

insert_migration_sql = """
INSERT INTO
    {table_name} (name, parent, hash, applied_at)
VALUES
    ({param}, {param}, {param}, {param})
"""

get_migration_sql = """
SELECT
    parent, hash, applied_at
FROM
    {table_name}
WHERE
    name = {param}
"""
