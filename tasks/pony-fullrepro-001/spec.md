# Pony ORM Public Behavior Specification

## Product Overview

Pony ORM is a Python object-relational mapper. Applications declare entity
classes on a `Database`, bind the database to a provider, generate a mapping,
and use Python expressions to query and change persisted objects. This package
exercises a deterministic SQLite memory database through the public
`pony.orm` surface.

## Scope

The supported application is a small library catalog with these public entity
declarations:

* `Author` has an explicit integer `PrimaryKey`, a unique required `name`, a
  required Boolean `active` value defaulting to `True`, a reverse `Set` of
  authored books, and a reverse `Set` of edited books.
* `Tag` has an explicit integer `PrimaryKey`, a unique required `label`, and a
  reverse `Set` of books.
* `Book` has an explicit integer `PrimaryKey`, a unique required `code`, a
  required `title`, required integer `pages`, optional decimal `price`,
  required Boolean `published` defaulting to `True`, and optional `Json`
  `metadata` whose public empty-object default is observable. It has a
  required `author` relationship, an optional `editor` relationship, and a
  many-to-many `tags` relationship.
* `AutoRecord` has an auto-generated integer `PrimaryKey` and a required
  `label`.

The database is created with `Database("sqlite", ":memory:")` and
`generate_mapping(create_tables=True)`. The supported query route covers
`select`, entity and query `filter`, ascending and descending `order_by`,
slicing, `first`, `get`, `exists`, `count`, `sum`, `avg`, `min`, and `max`.
The mutation route covers entity construction, `set`, `delete`, collection
`add`, `remove`, `clear`, collection `create`, `flush`, `commit`, and
`db_session` transaction handling.

## Public Import Surface

The application imports `Database`, `Required`, `Optional`, `Set`,
`PrimaryKey`, `Json`, `db_session`, `select`, `count`, `sum`, `avg`, `min`,
`max`, `desc`, `flush`, and `commit` from `pony.orm`. It also uses public
entity methods, reverse collections, and public exception classes for
validation and session errors, including `CacheIndexError` and
`DatabaseSessionIsOver`.

## Product State Model

The deterministic seed contains authors `(1, "Alice", True)`,
`(2, "Bob", False)`, and `(3, "Carol", True)`; tags `(100, "fiction")`,
`(101, "science")`, and `(102, "poetry")`; and books:

* `10 / B10 / Alpha / 100 / 12.50 / published / Alice`;
* `11 / B11 / Beta / 240 / 18.00 / published / Alice`;
* `12 / B12 / Gamma / 80 / no price / unpublished / Bob`; and
* `13 / B13 / Delta / 320 / 25.75 / published / Carol`.

The first book has the fiction tag, the second has fiction and science, and
the third and fourth have poetry. The first, second, and fourth books carry
small JSON objects; the third uses the public empty JSON default. Editors are
Carol, Bob, no editor, and Alice respectively. Explicit primary keys remain
available through entity lookup and auto-generated keys are available after
`flush` or serialization.

## Error Semantics

Assertions require public exception classes and observable state effects, not
exact exception text. Missing required values and invalid value types report
`ValueError`; unknown attributes report `TypeError`; duplicate primary keys
report the public cache/index error; and objects read from a strict session
cannot be loaded after that session ends. A session context commits normally,
rolls back when an unallowed exception escapes, and commits when the exception
is listed in `allowed_exceptions`.

## Cross-View Invariants

The following public views must agree:

* Entity queries and scalar or tuple projections expose the same rows and
  ordering.
* Forward relationship filters, reverse `Set` collections, and relationship
  fields identify the same authors, editors, and books.
* Many-to-many collection contents agree with `to_dict(with_collections=True)`;
  repeated additions do not duplicate a relation, and removal changes both
  sides.
* Entity `set`, construction, deletion, collection creation, and transaction
  boundaries are visible through later lookup, counts, existence checks, and
  projections.
* Aggregate counts and sums grouped by author match the corresponding
  per-author collections and filtered calculations.
* Plain and related-object `to_dict` modes preserve the same primary key and
  scalar row values.
* Session identity and cache behavior keeps repeated primary-key lookup
  identity-stable within a session while strict-session objects expire after
  the session closes.

## Representative Workflow

An application declares the catalog entities, creates an in-memory SQLite
mapping, and seeds authors, tags, books, and relationships. It then:

1. reads entities and scalar projections through generator expressions;
2. filters and orders rows, applies slices, and computes aggregates;
3. updates, creates, and deletes objects through public CRUD methods;
4. traverses forward, reverse, optional, and many-to-many relationships;
5. serializes rows with scalar, collection, related-object, only, and exclude
   forms of `to_dict`; and
6. repeats the workflow across successful, rolled-back, allowed-exception,
   nested, and strict database sessions.

## Non-Goals

The package does not cover external database servers, non-SQLite providers,
Flask integration, private modules or attributes, imports from source tests,
exact SQL text, generated SQL formatting, sleeps, timing, network access,
host state, performance limits, or exact exception wording.

## Invocation Protocol

Install the requirement listed in the accompanying requirements file, make the
implementation importable as `pony`, and run:

```bash
python -m pytest <test-directory> -q -W error
```

The tests use deterministic data, a local SQLite memory database, and public
`pony.orm` operations. They do not contact a service or depend on wall-clock
timing.

## Environment

The intended environment is Linux with Python 3.11 and without network access
during the test run. The target Pony package is not pre-installed; the
implementation under evaluation must provide the `pony` package. The required
test package is `pytest`.

## Evaluation Notes

There are 35 atomic tests for individual public facts and 31 integration tests
that combine mapping state, CRUD/query results, aggregates, relationships,
serialization, validation, session boundaries, and cache identity. Every
integration case depends only on named atomic cases. Assertions avoid private
implementation state, machine-specific paths, exact SQL formatting, sleeps,
and warning-producing diagnostics.
