# SQLAlchemy-Utils Public SQLite Utilities Specification

## Product Overview

SQLAlchemy-Utils provides SQLAlchemy data types, scalar coercion, ORM
inspection helpers, and database utilities. This package defines a small
SQLite-only model so those public behaviors can be observed through
construction, persistence, reload, querying, and schema inspection.

## Scope

The supported model has `Category` rows and `Record` rows. A record contains
an integer identifier, a database-column alias for its title, UUID token, URL,
password, fixed status choice, text and integer scalar lists, JSON payload,
boolean state, optional note, and a foreign key to a category. The model uses
the public SQLAlchemy declarative and session APIs.

The exercised route covers `UUIDType`, `URLType`, `PasswordType` and
`Password`, `ChoiceType` and `Choice`, `ScalarListType`, and `JSONType`.
Automatic scalar conversion is enabled through `force_auto_coercion`.
Inspection covers columns, primary keys, types, mappers, tables, table names,
column keys, declarative bases, class lookup, identity, and natural
equivalence. SQLite database helpers cover memory URLs, deterministic file
creation and removal, wildcard escaping, and index inspection.

## Public Import Surface

The application imports the documented names from `sqlalchemy_utils`,
including the custom types and value objects, `force_auto_coercion`,
`database_exists`, `create_database`, `drop_database`, `escape_like`,
`has_index`, `has_unique_index`, `get_bind`, `get_class_by_table`,
`get_column_key`, `get_columns`, `get_declarative_base`, `get_mapper`,
`get_primary_keys`, `get_tables`, `get_type`, `identity`,
`naturally_equivalent`, and `table_name`. SQLAlchemy imports are limited to
public engine, schema, ORM, and inspection APIs.

## Product State Model

`force_auto_coercion` is called before the declarative models are configured.
Assigning strings or compatible scalar values to coercible fields produces
UUID, furl URL, password, and choice value objects on model instances.
`ScalarListType` stores list values as delimited text and restores configured
element types. `JSONType` stores deterministic JSON text on SQLite and
restores mappings and sequences.

`Base.metadata.create_all` creates the category and record tables in a fresh
SQLite memory engine. A session can insert, flush, commit, expire, reload,
update, and query deterministic rows. UUIDs, URLs, password verification,
choices, scalar lists, JSON values, nullable fields, foreign keys, indexes,
and mapped column aliases remain observable through later public views.

## Error Semantics

The contract checks documented exception classes and state preservation rather
than incidental message text. Unknown choice codes raise `KeyError`.
Scalar-list delimiter violations raised while SQLAlchemy binds values are
reported through SQLAlchemy's public `StatementError` wrapper. A failed
operation does not create a partial row or corrupt a previously committed
row. Exact hash strings, URL representations, SQL text, and exception
messages are outside the contract.

## Cross-View Invariants

The mapped column keys returned by `get_columns` agree with declarative
attribute names, while table column names preserve explicit database aliases.
`get_primary_keys`, `identity`, `get_mapper`, `get_tables`, `get_type`,
`get_column_key`, and `table_name` describe the same models and relationships.

Values coerced before a session operation have the same logical type after a
SQLite round trip. Choice codes agree with their labels, scalar-list element
types survive reload, URL query parameters survive reassignment, password
verification agrees with the persisted hash, and JSON query values agree with
reloaded model values. Index helpers agree with declared indexed and unique
columns. File database existence agrees with successful schema creation and
subsequent removal.

The pinned `get_bind` implementation is exercised with public SQLAlchemy
`Connection` objects. Direct `Engine` and unbound `Session` handling is not
required because the pinned implementation exposes a non-executable `bind`
attribute in those SQLAlchemy 2.x cases.

## Representative Workflow

An application creates a SQLite memory engine, creates the declared schema,
constructs records with string and scalar input, and commits them. It then
expires and reloads rows, verifies custom value objects, changes a URL,
password, choice, scalar lists, UUID, and JSON payload, and compares the
results with query projections.

The application also inspects the same mapped classes and tables through the
public helper functions, checks indexes and primary keys, uses a public
connection for a scalar query, escapes a literal wildcard in a SQLite
`LIKE` predicate, and repeats the round trip with a temporary SQLite file.

## Non-Goals

PostgreSQL, MySQL, MSSQL, dialect drivers, external services, network
access, sockets, migrations, encryption, phone and locale integrations,
private implementation attributes, source-test imports, timing behavior,
performance, exact SQL formatting, exact password hashes, incidental
representations, and exact exception wording are excluded.

## Invocation Protocol

Install the requirements listed in the accompanying requirements file, make the pinned
`sqlalchemy_utils` package importable, and run:

```bash
python -m pytest <test-directory> -q --json-report -W error
```

The tests use only deterministic in-memory or temporary SQLite databases.
Temporary file names are supplied by pytest and are not compared as output.

## Environment

The intended environment is Linux with Python 3.11 and without network access
during the test run. The target package is not pre-installed; the evaluated
implementation must provide `sqlalchemy_utils`. Required packages are
`SQLAlchemy`, `furl`, `passlib`, `pytest`, and `pytest-json-report`, at the
versions listed in the accompanying requirements file.

## Evaluation Notes

This route favors stable public behavior over dialect-specific breadth.
Password checks validate secrets without comparing generated hashes, and URL
checks compare public parsed components. SQLite file lifecycle checks use
temporary paths and remove their files. The same-process local replay
evidence is reproducibility evidence only; it does not establish a trusted
black-box runner, an external signature, or final qualification.
