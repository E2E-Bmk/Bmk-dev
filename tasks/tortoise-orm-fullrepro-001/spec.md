# Tortoise ORM Public Behavior Specification

## Product Overview

Tortoise ORM is an asynchronous Python object-relational mapper. Applications
declare `Model` subclasses with public data and relation fields, initialize a
database through `Tortoise`, generate a schema, and use model and QuerySet
methods for persisted objects, dictionaries, tuples, counts, and relations.
This package exercises the documented SQLite behavior of that workflow.

## Scope

The supported application is a small library catalog using three public model
classes in the `models` app:

* `Author`: `id` is an integer primary key, `name` is a character field,
  and `active` is a Boolean field defaulting to `True`. Its table is
  `library_author` and its documented default ordering is by `name`.
* `Tag`: `id` is an integer primary key and `label` is a unique character
  field. Its table is `library_tag`.
* `Book`: `id` is an integer primary key; `title` is a character field;
  `pages` is an integer field; `price` is a nullable decimal field; `published`
  is a Boolean field defaulting to `True`; and `metadata` is a nullable JSON
  field. `author` is a foreign key to `Author` with reverse name `books` and
  cascading deletion. `tags` is a many-to-many field to `Tag` through
  `library_book_tag`, with reverse name `books`. Its table is `library_book`.

The public route covers model metadata, schema generation, deterministic CRUD,
QuerySet filtering and ordering, dictionary and tuple projections, SQLite
memory and file databases, forward and reverse foreign-key traversal, and
many-to-many mutation and prefetching.

The supported lookup forms used by this route are equality, `__gte`, `__lt`,
`__range`, `__in`, `__iexact`, `__icontains`, and `__isnull`, including
lookups through the `author` relation. `exclude` negates a condition, and
`order_by` accepts field names with an optional leading `-`.

## Public Import Surface

The implementation must provide the documented names imported by the
application:

* `Tortoise` and `fields` from `tortoise`;
* `Model` from `tortoise.models`;
* field constructors and the `CASCADE` option from `tortoise.fields`;
* public model methods `describe`, `create`, `save`, `delete`, `get`,
  `get_or_none`, `get_or_create`, `update_or_create`, `bulk_create`,
  `bulk_update`, `filter`, `exclude`, `all`, `first`, and `fetch_related`;
* public QuerySet methods `filter`, `exclude`, `order_by`, `values`,
  `values_list`, `count`, `exists`, `first`, `last`, `limit`, `offset`,
  `get_or_none`, `update`, `delete`, `prefetch_related`, and `all`;
* public relation-container methods `add`, `remove`, `clear`, `create`, and
  iteration after a relation has been fetched; and
* `Tortoise.init`, `Tortoise.generate_schemas`, `Tortoise.close_connections`,
  `Tortoise.describe_models`, and the public `pk` alias.

## Product State Model

`Tortoise.init` accepts a SQLite URL and a `modules` mapping containing the
`models` app. `Tortoise.generate_schemas()` creates the declared tables, and
the safe form can be called again without changing the usable schema.
`Tortoise.close_connections()` releases the database connection.

The catalog data used for the observable projections is deterministic:

* authors `(1, "Alice", True)`, `(2, "Bob", False)`, and
  `(3, "Carol", True)`;
* tags `(100, "fiction")`, `(101, "science")`, and `(102, "poetry")`;
* books `(10, "Alpha", 100, 12.50, True, fiction, Alice)`,
  `(11, "Beta", 240, 18.00, True, science and fiction, Alice)`,
  `(12, "Gamma", 80, null, False, poetry, Bob)`, and
  `(13, "Delta", 320, 25.75, True, poetry, Carol)`.

Integer, Boolean, decimal, nullable, and JSON values round-trip through
`create`, `save`, `filter`, `values`, and `values_list`. Explicit primary keys
remain available through `pk`. A new instance can be inserted with `save`;
`save(update_fields=[...])` changes only the requested persisted fields.

## Error Semantics

This package does not require exact exception text. Where a public operation
reports an error, only the documented exception class and the absence of
unrelated side effects are contract-relevant. Missing rows queried with
`get_or_none` produce `None`; the tests do not require exact messages for
validation, field, configuration, or database errors.

## Cross-View Invariants

The following independent public views must agree:

* `Model.describe()` and `Tortoise.describe_models()` expose the qualified
  names, configured table names, primary-key description, data fields, foreign
  key fields, and many-to-many fields of the declared models. The serializable
  descriptions can be passed to `json.dumps`.
* Filtering by a foreign-key field and selecting a related field through
  `values` or `values_list` agree with the name of a prefetched related object.
* Reverse `books` prefetching agrees with filtering `Book` by
  `author__name`.
* Many-to-many prefetching and related `values_list` rows expose the same tag
  labels. Repeated `add` calls do not duplicate a relation, and `remove` and
  `clear` change subsequent prefetched results.
* `create`, `save`, QuerySet `update`, QuerySet `delete`, `bulk_create`, and
  `bulk_update` are visible through later counts, existence checks, model
  instances, and dictionary or tuple projections.
* `order_by` applies ascending and descending order before `first`, `last`,
  `limit`, `offset`, `values`, and `values_list`.
* `get_or_create` reports whether it inserted a row, while
  `update_or_create` updates an existing row without changing its primary key.
  A QuerySet can be built before a later insert and evaluated afterward.
* A SQLite file URL creates a file-backed database whose schema and rows are
  visible through the same public model and QuerySet APIs as an in-memory
  database. The file-backed workflow can be opened again and queried.

## Representative Workflow

An application defines the three catalog models, initializes an in-memory
SQLite database, generates the schema, creates authors, books, and tags, and
connects books to authors and tags. It then:

1. reads metadata through `describe` methods;
2. updates and removes rows through model and QuerySet CRUD methods;
3. filters and orders books, projects scalar fields with `values` and
   `values_list`, and checks counts and existence;
4. prefetches forward, reverse, and many-to-many relations and compares those
   objects with related-field projections;
5. uses `get_or_create`, `update_or_create`, bulk operations, and related
   creation; and
6. repeats the schema/query workflow with a deterministic temporary SQLite file.

## Non-Goals

The package does not require non-SQLite backends, live services, network
access, migration command implementation, raw SQL text, private implementation
attributes, source-test imports, performance guarantees, transaction timing,
or exact exception wording. It also does not require a particular database
driver version beyond the listed SQLite requirements.

## Invocation Protocol

Install the requirements listed in the accompanying requirements file, make
the implementation importable as `tortoise`, and run:

```bash
python -m pytest <test-directory> -q -W error
```

The tests use only deterministic data, `asyncio.run`, and pytest temporary
paths. They do not contact a service or depend on wall-clock timing.

## Environment

The intended environment is Linux with Python 3.11 and without network access
during the test run. The target Tortoise package is not pre-installed; the
implementation under evaluation must provide the `tortoise` package. Required
test/runtime packages are `pytest`, `pytest-json-report`, `aiosqlite`,
`pypika-tortoise`, `iso8601`, and `anyio`.

## Evaluation Notes

There are 30 atomic tests for individual public facts and 30 integration tests
that combine model metadata, schema state, CRUD/query results, file-backed
storage, and related-object projections. Integration tests compare at least
two public views or operations of the same catalog facts. No assertion depends
on private pypika behavior, exact SQL formatting, machine-specific paths,
sleep calls, or warning-producing diagnostics.
