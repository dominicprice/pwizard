import typing as t
from datetime import datetime, timedelta
from time import time_ns

import peewee

from pwizard.migrate.hooks import MigrationHooks
from pwizard.migrate.internal import AppliedMigration
from pwizard.migrate.migration import Migration
from pwizard.migrate.warnings import (
    HashesDifferWarning,
    MigrationWarning,
    ParentDiffersWarning,
)


class Migrator:
    def __init__(
        self,
        migrations: t.Iterable[Migration] | None = None,
        table_name: str = "migrations",
        text_type: str = "TEXT",
        fix_warnings: bool = False,
        hooks: MigrationHooks | None = None,
    ):
        self.migrations = list(migrations or [])
        self.table_name = table_name
        self.text_type = text_type
        self.fix_warnings = fix_warnings
        self.hooks = hooks if hooks is not None else MigrationHooks()

    def set_migrations(self, migrations: t.Iterable[Migration]):
        self.migrations = list(migrations)

    def migrate(self, database: peewee.Database):
        self.hooks.on_begin_migrations(len(self.migrations))

        skipped = 0
        warned = 0
        applied = 0
        parent: str | None = None
        start_time = time_ns()

        with database.atomic():
            self._ensure_migrations_table(database)
            for migration in self.migrations:
                self.hooks.on_before_migration(migration)

                was_applied = False
                warning: MigrationWarning | None = None
                fixed = False
                applied_migration = self._get_migration(database, migration)
                if applied_migration is None:
                    self._apply_migration(database, migration, parent)
                    was_applied = True
                else:
                    warning, fixed = self._skip_migration(
                        database,
                        migration,
                        parent,
                        applied_migration,
                    )

                if was_applied:
                    applied += 1
                elif warning is not None:
                    warned += 1
                else:
                    skipped += 1

                self.hooks.on_after_migration(
                    migration,
                    was_applied,
                    warning,
                    fixed,
                )

                parent = migration.name()

        elapsed = timedelta(seconds=(time_ns() - start_time) / 1e9)
        self.hooks.on_finish_migrations(skipped, warned, applied, elapsed)

    def _ensure_migrations_table(self, database: peewee.Database):
        self.hooks.on_check_migration_table_exists()

        exists = database.table_exists(self.table_name)
        if not exists:
            stmt = create_migrations_table_sql.format(
                table_name=self.table_name,
                text_type=self.text_type,
            )
            database.execute_sql(stmt)

        self.hooks.on_checked_migration_table_exists(not exists)

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

    def _skip_migration(
        self,
        database: peewee.Database,
        migration: Migration,
        parent: str | None,
        applied_migration: AppliedMigration,
    ) -> tuple[MigrationWarning | None, bool]:
        warning: MigrationWarning | None = None
        fixed = False
        if applied_migration.hash != migration.hash():
            warning = HashesDifferWarning(
                migration.hash(),
                applied_migration.hash,
                applied_migration.applied_at,
            )
            if self.fix_warnings:
                stmt = set_migration_hash_sql.format(
                    table_name=self.table_name,
                    param=database.param,
                )
                params = (migration.hash(), migration.name())
                database.execute_sql(stmt, params)
                fixed = True
        elif applied_migration.parent != parent:
            warning = ParentDiffersWarning(
                parent,
                applied_migration.parent,
                applied_migration.applied_at,
            )
            if self.fix_warnings:
                stmt = set_migration_parent_sql.format(
                    table_name=self.table_name,
                    param=database.param,
                )
                params = (parent, migration.name())
                database.execute_sql(stmt, params)
                fixed = True

        return warning, fixed

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

set_migration_hash_sql = """
UPDATE
    {table_name}
SET
    hash = {param}
WHERE
    name = {param}
"""

set_migration_parent_sql = """
UPDATE
    {table_name}
SET
    parent = {param}
WHERE
    name = {param}
"""
