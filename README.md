# pwizard: Migrations and Code Generation for peewee

I've been using [peewee](https://github.com/coleifer/peeweehttps://github.com/coleifer/peewee) quite a bit recently, and while the `pwiz` tool
is really good I found myself wanting to customize the output a bit. I
also end up writing pretty much the same code for doing database
migrations every time I spin up a new project, so I just packaged all
of my common code together and put it here as making it a PyPI
dependency makes it much easier to include in my projects.

## Overview

The `pwizard` package contains two main submodules: `generate` and `migrate`.

### Generate

This introspects a database and produces a Python file with peewee
models which can be used to interact with the database, similarly to
the `pwiz` module included with peewee, but allowing more customization
of the output.

The generator introspects the database, collecting metadata about the
database and its tables, then feeds the introspected data into [jinja2](https://github.com/pallets/jinja)
to produce the output file.

### Migrate

This is a migration tool which creates a special migrations table in
the database to keep track of which migrations have already been
applied. It has builtin support for running migrations from SQL files,
but can be extended to perform arbitrary migrations.

## Installation

To install the latest master version of this repo, run `pip install git+https://github.com/dominicprice/pwizard`.

## Usage

My general usage is as follows:
* Run all my migrations using the `migrate` tool on a temporary
  database, which I then use the `generate` tool on to generate the
  database models.
* When my program launches, the `migrate` tool is run to ensure that the
  unerlying database is up to date.

### As a library

__Generate__ 

As an example:

```python
from pwizard.generate import Generator

database = SqliteDatabase("mydb.sqlite") # or any peewee Database instance

generator = Generator("./path/to/output/models.py")
generator.generate(database)
```

The `Generator` object takes extra optional parameters, see the definition.

__Migrate__ 

As an example:

```python
from pwizard.migrate import Migrator
from pwizard.migrate.migration import SQLMigration

database = SqliteDatabase("mydb.sqlite") # or any peewee Database instance

migrations = [
    SQLMigration("./migrations/01_init.sql"),
	SQLMigration("./migrations/02_extra.sql"),
	SQLMigration("./migrations/03_fix_issue_4125.sql"),
]
migrator = Migrator(migrations)
migrator.migrate(database)
```

### As command line tools

__Generate__ 

You can run `pwizard generate CONFIG_FILE DB_URL` once the package is installed to run the generator as a CLI program. The config file contains all the options for the generator, all the options are described here:

```ini
[db]
# Specify the database driver to use: can either be
# postgresql, sqlite, mysql or proxy. This determines
# what peewee Database type to use when declaring the database.
# If not provided, then it is determined based on the type of
# the database used to generate the models.
driver = sqlite

[models]
# Whether to generate models for views as well as tables.
# Defaults to false.
include_views = true

# List of literal strings or regexp patterns (surrounded by //) 
# for tables to include in the generated output. You should specify one
# table per line, indented by four spaces. If not specified, all tables
# will be included.
include_tables = 
    a_special_table
	/important_.*/

# List of literal strings or regexp patterns (surrounded by //) 
# for tables to exclude in the generated output. This overrides any
# tables specified in include_tables. You should specify one
# table per line, indented by four spaces.
exclude_tables = 
    important_but_should_not_generate
	
[templates]
# Specify a custom custom template file to use to generate the template.
# If not provided, the builtin template will be used.
template_path = ./src/project/models.py.tmpl

# If set to true, then field names will be converted to snake case.
# Defaults to true
snake_case = true

[output]
# The path of the file to generate the models to
output_path = ./src/project/models.py
```

__Migrate__ 

You can run `pwizard migrate DB_URL` to migrate a database using SQL
files. You should provide the list of SQL files to use for the
migration using the `--migration` flag, which accepts a glob pattern
(which will be sorted lexically).
