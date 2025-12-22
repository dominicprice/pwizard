import configparser
import os
import re
import typing as t
from collections import defaultdict
from inspect import isclass
from pathlib import Path

import jinja2
import peewee
from playhouse.reflection import DatabaseMetadata, Introspector

from pwizard.generate.types import Column, DatabaseType, Index, Table
from pwizard.utils.split import split_relist

if t.TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


class Generator:
    def __init__(
        self,
        output_path: "StrOrBytesPath",
        *,
        driver: DatabaseType | None = None,
        template_path: "StrOrBytesPath | None" = None,
        include_tables: list[str | re.Pattern] = [],
        exclude_tables: list[str | re.Pattern] = [],
        include_views: bool = True,
        snake_case: bool = True,
        custom_column_types: t.Mapping[str, type[peewee.Field]] | None = None,
    ):
        self.output_path = output_path
        self.driver = driver
        if template_path is None:
            self.template_path = Path(__file__).parent / "templates" / "main.py.tmpl"
        else:
            self.template_path = Path(os.fsdecode(template_path))
        self.include_views = include_views
        self.snake_case = snake_case
        self.include_tables = include_tables
        self.exclude_tables = exclude_tables
        self.custom_column_types = (
            {} if custom_column_types is None else dict(custom_column_types)
        )

    @classmethod
    def from_config(cls, config_file: "StrOrBytesPath") -> t.Self:
        parser = configparser.ConfigParser(
            delimiters=["="],
            comment_prefixes=["#"],
            default_section="default",
            converters={
                "relist": split_relist,
            },
        )
        parser.read(config_file)

        kwargs: dict[str, t.Any] = {}

        db = parser["db"]
        if driver := db.get("driver", fallback=None):
            kwargs["driver"] = DatabaseType(driver)
        else:
            kwargs["driver"] = None

        models = parser["models"]
        kwargs["include_views"] = models.getboolean("include_views", fallback=False)
        kwargs["include_tables"] = models.getrelist("include_tables", fallback=[])
        kwargs["exclude_tables"] = models.getrelist("exclude_tables", fallback=[])

        templates = parser["templates"]
        kwargs["template_path"] = templates.get("template_path", fallback=None)
        kwargs["snake_case"] = templates.getboolean("snake_case", fallback=True)

        output = parser["output"]
        kwargs["output_path"] = output.get("output_path")

        return cls(**kwargs)

    def generate(self, database: peewee.Database):
        driver = self.driver
        if driver is None:
            if isinstance(database, peewee.PostgresqlDatabase):
                driver = DatabaseType.Postgresql
            elif isinstance(database, peewee.SqliteDatabase):
                driver = DatabaseType.SQLite
            elif isinstance(database, peewee.MySQLDatabase):
                driver = DatabaseType.MySQL
            else:
                driver = DatabaseType.Proxy

        # create the template
        loader = jinja2.FileSystemLoader(self.template_path.parent)
        jinja = jinja2.Environment(loader=loader)
        template = jinja.get_template(self.template_path.name)

        # get the data for the template from the database
        introspector = Introspector.from_database(database)
        for colname, coltype in self.custom_column_types.items():
            introspector.metadata.column_map[colname] = coltype
        metadata = introspector.introspect(
            include_views=self.include_views,
            snake_case=self.snake_case,
        )
        data = self._get_template_data(driver, introspector, metadata)

        # generate the output
        with open(self.output_path, "w") as f:
            for s in template.generate(**data):
                f.write(s)

    def _get_template_data(
        self,
        driver: DatabaseType,
        introspector: Introspector,
        metadata: DatabaseMetadata,
    ) -> dict[str, t.Any]:
        imports: defaultdict[str, set[str]] = defaultdict(lambda: set())
        imports["peewee"].update(["Model", driver.database])
        if driver == DatabaseType.Proxy:
            imports["peewee"].add("Database")
            imports["playhouse.db_url"].add("connect")
        tables: dict[str, Table] = {}
        for table in sorted(metadata.model_names.keys()):
            self._parse_table(
                table,
                tables,
                [],
                imports,
                introspector,
                metadata,
            )

        return {
            "driver": driver,
            "imports": imports,
            "tables": tables,
        }

    def _parse_table(
        self,
        table: str,
        tables: dict[str, Table],
        accum: list[str],
        imports: defaultdict[str, set[str]],
        introspector: Introspector,
        metadata: DatabaseMetadata,
    ):
        if table in tables:
            # already parsed
            return

        if self._skip_table(table):
            # check if trying to skip a table which is a foreign key relation
            if len(accum) > 0:
                raise RuntimeError(
                    "cannot exclude table '"
                    + table
                    + "' as it is required by a foreign key relation"
                )

            # exclude from output
            return

        # ensure all tables to foreign keys have been parsed
        for foreign_key in metadata.foreign_keys[table]:
            dest = foreign_key.dest_table
            # prevent reference cycles
            if dest in accum and table not in accum:
                raise RuntimeError("reference cycle: " + dest)
            if dest not in tables and dest not in accum:
                if dest != table:
                    self._parse_table(
                        dest,
                        tables,
                        accum + [table],
                        imports,
                        introspector,
                        metadata,
                    )

        primary_keys = metadata.primary_keys[table]
        if len(primary_keys) > 1:
            imports["peewee"].add("CompositeKey")

        columns = []
        for name, col in metadata.columns[table].items():
            if (
                name in primary_keys
                and name == "id"
                and len(primary_keys) > 1
                and col.field_class in introspector.pk_classes
            ):
                continue

            if col.primary_key and len(primary_keys) > 1:
                col.primary_key = False
            field_params = {}
            for key, value in col.get_field_parameters().items():
                if isclass(value) and issubclass(value, peewee.Field):
                    value = value.__name__
                field_params[key] = value
            column = Column(
                col.name,
                col.field_class,
                field_params,
            )
            columns.append(column)
            modname, classname = column.get_import()
            if modname is not None:
                imports[modname].add(classname)

        indexes = []
        if multi_column_indexes := metadata.multi_column_indexes(table):
            for fields, unique in sorted(multi_column_indexes):
                indexes.append(Index(fields, unique))

        primary_key_names = sorted(
            field.name
            for col, field in metadata.columns[table].items()
            if col in primary_keys
        )

        table_model = Table(
            metadata.model_names[table],
            table,
            columns,
            indexes,
            introspector.schema,
            primary_key_names,
        )

        tables[metadata.model_names[table]] = table_model

    def _skip_table(self, table: str) -> bool:
        # return True if it is not in the list of
        # included tables
        if len(self.include_tables) > 0:
            for pat in self.include_tables:
                if isinstance(pat, re.Pattern):
                    if pat.match(table):
                        break
                else:
                    if pat == table:
                        break

            else:
                return True

        # return True if it is in the list of excluded tables
        for pat in self.exclude_tables:
            if isinstance(pat, re.Pattern):
                if pat.match(table):
                    return True
            else:
                if pat == table:
                    return True

        return False
