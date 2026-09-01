# Peewee Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`peewee` is a Python ORM and SQL query builder that maps model classes to relational tables, field objects to columns, model instances to rows, and composable expression objects to SQL executed against a local SQLite database.

The package exposes a top-level `peewee` module, selected `playhouse` helper modules, and a `pwiz` command. The covered behavior is the SQLite-local workflow: define models, create schema, insert and query rows, manage connection and transaction state, inspect schema metadata, apply lightweight migrations, parse SQLite URLs, and generate model code from an existing SQLite database.

## Non-Goals

- This specification does not require live MySQL, MariaDB, PostgreSQL, CockroachDB, SQLCipher, APSW, cysqlite, async driver, gevent, web framework, or Pydantic behavior.
- This specification does not require C extensions, SQLite user-defined function libraries, full-text-search ranking helpers, queue databases, connection pools, or encrypted SQLite databases.
- This specification does not define private helper modules, private attributes, exact object representation text, exact exception message text, logging text, or internal compiler data structures.
- This specification does not require compatibility with external database servers, network access, or backend-specific SQL dialect behavior beyond SQLite.

## Representative Workflows

Define two related models, create tables, write rows, and read joined data:

```python
import datetime
from peewee import *

db = SqliteDatabase(":memory:", pragmas={"foreign_keys": 1})

class BaseModel(Model):
    class Meta:
        database = db
        legacy_table_names = False

class User(BaseModel):
    username = TextField(unique=True)

class Tweet(BaseModel):
    user = ForeignKeyField(User, backref="tweets")
    content = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now, index=True)
    published = BooleanField(default=True)

db.connect()
db.create_tables([Tweet, User])

user = User.create(username="charlie")
Tweet.create(user=user, content="hello")

query = Tweet.select(Tweet, User).join(User).where(Tweet.published == True)
for tweet in query.order_by(Tweet.timestamp.desc()):
    print(tweet.user.username, tweet.content)
```

The database creates `User` before `Tweet` because the foreign key depends on it. `User.create()` returns a saved instance with an auto-incrementing `id`, `Tweet.user` resolves to a `User` instance when selected through a join, and `user.tweets` returns a pre-filtered query for related rows.

Reflect an existing SQLite file, generate models, and alter the schema:

```python
from peewee import *
from playhouse.db_url import connect
from playhouse.reflection import generate_models
from playhouse.migrate import SchemaMigrator, migrate

db = connect("sqlite:///inventory.db")
db.connect(reuse_if_open=True)

models = generate_models(db)
Product = models["product"]

migrator = SchemaMigrator.from_database(db)
with db.atomic():
    migrate(migrator.add_column("product", "active", BooleanField(default=True)))

for row in Product.select().dicts():
    print(row)
```

The URL helper returns a `SqliteDatabase`, reflection returns model classes keyed by table name, and migration operations execute against the same database state. Wrapping migrations in `atomic()` makes normal exits commit and exception exits roll back according to SQLite transaction rules.

Generate model source from a shell:

```shell
pwiz -e sqlite -i -t user,tweet app.db > models.py
```

The `pwiz` command introspects the selected SQLite tables, emits import lines, a bound database object, a base model class, generated model classes, explicit table names, foreign-key fields where metadata exists, and comments for unmapped columns unless unknown fields are ignored.

## Model And Field Mapping

Model classes, field declarations, and metadata define the schema contract that all ORM operations use.

**Model Class Construction.**
The `Model` base class must convert non-private `Field` attributes declared on subclasses into database columns, and the model class must expose those fields as descriptors on the class and instance. When a concrete model declares no primary key, the model must add an auto-incrementing integer `AutoField` named `id`. When a model inherits from another model, the subclass must inherit field declarations and inheritable `Meta` options, and it must receive its own table. If a model sets `Meta.primary_key` to `False`, then instance `save()` and `delete_instance()` must raise a primary-key-related error when they need a row identity.

**Metadata Options.**
The model metadata object at `ModelClass._meta` must expose the resolved `database`, `table_name`, `fields`, `primary_key`, indexes, constraints, schema, and table options for the model. When `Meta.table_name` is set, the model must use it as the database table name. When `Meta.table_function` is set, the model must call it with the model class to derive the table name. When `Meta.legacy_table_names` is true, the model must derive the table name by lowercasing the class name and replacing non-word runs with underscores; when it is false, the model must derive the table name by converting the class name to snake_case. If metadata lacks a database and a query is executed, then the operation must raise `InterfaceError`.

**Field Parameters.**
Every concrete `Field` must accept common keyword parameters including `null`, `index`, `unique`, `column_name`, `default`, `primary_key`, `constraints`, `collation`, `choices`, `help_text`, and `verbose_name`, and it must use them for Python value handling, DDL generation, or metadata. When `default` is a callable, model instantiation must call it for each new instance; when `default` is a literal object, instances must receive that literal value. When `choices` is provided, the field must retain choice metadata and must not validate assignments against it. When `constraints` includes `Check` or `Default`, generated table DDL must include those SQL constraints.

**Field Types.**
SQLite storage must map integer, floating, decimal, text, blob, UUID, date, time, datetime, timestamp, boolean, JSON, and foreign-key fields to compatible SQLite column types. `DateField`, `TimeField`, and `DateTimeField` must expose date-part expressions such as `year`, `month`, `day`, `hour`, `minute`, and `second` according to the field type. `TimestampField` must store datetimes as integer Unix timestamps, using its `resolution` and `utc` settings for conversion. If a value fails conversion for a field, then the database operation must raise the conversion or driver exception rather than silently storing unrelated data.

**Foreign Keys And Back References.**
A `ForeignKeyField` must store the related row primary key in a column whose default database column name appends `_id` to the field name. When assigned a related model instance, the field must store that instance identity; when assigned a raw primary-key value, the field must store that value. When `backref` is set, the related model must expose that name as a pre-filtered `Select` query. When no `backref` is set, the related model must expose a default `<model>_set` query name. When `lazy_load` is false, accessing the foreign-key attribute without an eagerly selected related object must return the raw identity value. If a foreign key refers to `'self'`, then the model must resolve it to the declaring model class after class construction.

**Composite And Deferred Relationships.**
`CompositeKey` must designate multiple field names as the primary key for a model. `DeferredForeignKey` and `DeferredThroughModel` must allow relationships to be declared before the target class exists and must resolve once the target model is defined. `ManyToManyField` must expose a descriptor for adding, removing, clearing, and querying related objects through a through model. If `ManyToManyField` receives an unsaved source instance while unsaved protection is enabled, then relationship mutation must raise `ValueError`.

## Queries And Expressions

Query objects describe reads and writes lazily until execution, and expression objects provide the public vocabulary for SQL construction.

**Selection And Result Rows.**
`Model.select()` must return a lazy `Select` query. When a select query is iterated, indexed, sliced, counted, converted with `scalar()`, or executed, it must run SQL against the bound database. Re-iterating the same query object must reuse its result cache; when `iterator()` is used, the query must stream rows without populating that cache. By default a model select must return model instances. When `dicts()`, `tuples()`, `namedtuples()`, or `objects()` is chained before execution, the query must return dictionaries, tuples, named tuples, or flattened objects respectively. If selected columns omit a field, then the returned model instance must not populate that field from hidden data.

**Single-Row Retrieval.**
`Model.get()` must execute the query and return the first matching row. If no row matches, then `Model.get()` must raise the model-specific `DoesNotExist` subclass, and that subclass must also be an instance of top-level `DoesNotExist`. `Model.get_or_none()` and `Select.first()` must return `None` when no row is found. `Model.get_by_id()` and `ModelClass[primary_key]` must perform primary-key lookup.

**Filtering Operators.**
Field comparisons must build SQL expressions for equality, inequality, ordering comparisons, `between()`, `in_()`, `not_in()`, `is_null()`, `contains()`, `startswith()`, `endswith()`, `regexp()`, `iregexp()`, `bin_and()`, `bin_or()`, `concat()`, `distinct()`, `collate()`, and `cast()`. The `&`, `|`, and unary `~` operators must combine expressions as SQL AND, OR, and NOT. The `<<` operator must represent IN and the `>>` operator must represent IS. If Python logical operators are used before an expression reaches peewee, then peewee must receive the resulting Python value and must not reconstruct the lost SQL expression.

**Ordering, Grouping, And Aggregates.**
`order_by()` must accept fields, expressions, ascending or descending modifiers, and `SQL` aliases. `limit()`, `offset()`, and `paginate()` must constrain result windows, and `paginate()` must treat page numbers as 1-based. `count()` must return an integer count for the query. `fn` must create function calls for arbitrary SQL function names, and `group_by()` plus `having()` must build aggregate queries. `scalar()` must return the first column of the first row, and when `as_tuple` is true it must return multiple scalar columns from that row. If a query requires a database and no database is bound, then execution must raise `InterfaceError`.

**Joins And Prefetch.**
`join()`, `left_outer_join()`, `join_from()`, and `switch()` must build joins between model sources using declared foreign keys or explicit `on` expressions. When joined model columns are selected, peewee must reconstruct the related model graph so foreign-key attributes reference populated instances without extra lookups. `prefetch()` must execute the primary query and subqueries, then associate related rows onto their parent instances according to foreign-key relationships. If a join has no discoverable foreign key and no `on` expression, then query construction or execution must raise an error rather than guessing the relationship.

**Writing Queries.**
`Model.create()` must insert a row and return the saved instance with its generated primary key when SQLite supplies one. A new model instance `save()` must insert; a saved instance with a primary key must update. `Model.insert()` and `Model.insert_many()` must return executable write queries; `insert_many()` must accept dictionaries or tuples with an explicit field list for tuple rows. `Model.update()` and `Model.delete()` must execute against all rows matching their `where()` expressions and must return affected-row counts unless `returning()` changes the result into an iterable cursor. `replace()`, `on_conflict_replace()`, `on_conflict_ignore()`, and `on_conflict()` must implement SQLite conflict handling, with `EXCLUDED` exposing incoming values for conflict update expressions. If a unique or foreign-key constraint is violated, then SQLite-backed execution must raise `IntegrityError`.

**Raw SQL And Query Builder Objects.**
`SQL`, `Entity`, `Value`, `Column`, `Table`, `Tuple`, `Case`, `Cast`, `Window`, `ValuesList`, `DQ`, `JOIN`, `OP`, and `fn` must be importable building blocks for expressions and table queries. `Table` must support `select()`, `insert()`, `update()`, and `delete()` without declaring a `Model`. `Window` must support partitioning, ordering, frame boundaries, frame type constants, aliases, extension of prior windows, and function use through `over()`. If raw SQL placeholders and parameters do not match the underlying driver requirements, then execution must raise the driver error.

## Database Connections And Transactions

Database objects own connection state, driver calls, schema operations, and transaction boundaries.

**Initialization And Binding.**
`SqliteDatabase` must accept a database filename or `":memory:"`, optional `pragmas`, SQLite driver options, `timeout`, `autoconnect`, and `returning_clause`. A database initialized with `None` must be deferred until `init()` supplies the database name and driver options. `DatabaseProxy.initialize()` must attach a concrete database and forward database operations after initialization. If an uninitialized database or proxy is used for execution, then it must raise `InterfaceError` or `AttributeError` according to the object used. `Database.bind()`, `Model.bind()`, `bind_ctx()`, and `ThreadSafeDatabaseMetadata` must update the database used by model queries, with context managers restoring the previous binding on exit.

**Connection Lifecycle.**
`connect()` must open a connection and return `True` when it opens a new connection. If `connect()` is called while the connection is open and `reuse_if_open` is false, then it must raise `OperationalError`; when `reuse_if_open` is true it must return `False`. `close()` must close an open connection and return `True`; when already closed it must return `False`. `is_closed()` must report current connection state. `connection()` and query execution must open a connection automatically when `autoconnect` is enabled. If `autoconnect` is disabled and execution needs a closed connection, then execution must raise an interface or operational connection error.

**Context Managers.**
Using a database as a context manager or decorator must open a connection, begin a transaction, commit on normal exit, roll back on exception exit, close the connection, and re-raise unhandled exceptions. `connection_context()` must manage only connection lifetime and must not begin an implicit transaction. `atomic()` must open a transaction for the outer block and savepoints for nested blocks. When a wrapped `atomic()` block exits normally, it must commit its transaction or release its savepoint; when an exception leaves the block, it must roll back that transaction or savepoint and re-raise. Manual `commit()` or `rollback()` on the transaction object returned by `atomic()` must immediately start a new transaction or savepoint for the remaining block.

**Transaction APIs.**
`transaction()` must create a flat transaction whose nested uses are ignored in favor of the outermost transaction. `savepoint()` must create a savepoint inside an active transaction and must allow nested savepoints. `manual_commit()` must suspend peewee-managed transaction boundaries so explicit `begin()`, `commit()`, and `rollback()` calls control the driver transaction. SQLite lock types passed to outer `atomic()` or `begin()` must be emitted as SQLite transaction modes such as `DEFERRED`, `IMMEDIATE`, or `EXCLUSIVE`. If a savepoint is requested outside a transaction, then the database must raise an operational transaction error.

**SQLite Pragmas And Extensions.**
`SqliteDatabase.pragma()` must read and write SQLite PRAGMA values for the current connection, and when `permanent` is true it must apply the setting to future connections. The shortcut properties `foreign_keys`, `journal_mode`, `cache_size`, and related pragma properties must read and write the same PRAGMA state. `register_function()`, `func()`, `register_aggregate()`, `aggregate()`, `register_window_function()`, `window_function()`, `register_collation()`, `collation()`, `load_extension()`, `unload_extension()`, `attach()`, and `detach()` must expose SQLite extension hooks. If the SQLite library lacks a requested capability, then the call must raise the SQLite driver error or `NotSupportedError`.

## Schema Management, Reflection, And Migrations

Schema APIs expose the same SQLite database structure through DDL, metadata records, generated model classes, migration operations, and command output.

**Creating And Dropping Schema.**
`Database.create_tables()` must create tables for the supplied model classes and must order them so foreign-key dependencies are created before dependents. By default it must use safe creation semantics equivalent to creating only missing tables; when `safe` is false it must let SQLite raise if the table already exists. `Database.drop_tables()` and `Model.drop_table()` must use safe drop semantics by default and must let SQLite raise when `safe` is false and the table is absent. `Model.create_table()`, `Model.table_exists()`, `SchemaManager.create_table()`, `create_indexes()`, `drop_indexes()`, `truncate_table()`, `create_all()`, and `drop_all()` must operate through the model's bound database. If a schema operation relies on unsupported SQLite DDL, then it must raise `OperationalError` or `NotSupportedError`.

**Introspection Metadata.**
`get_tables()` must return table names visible in the database. `get_views()` must return `ViewMetadata` records for views. `get_columns()` must return `ColumnMetadata` records with public attributes including `name`, `data_type`, `null`, `primary_key`, `table`, and `default`. `get_indexes()` must return `IndexMetadata` records with public attributes including `name`, `sql`, `columns`, `unique`, and `table`. `get_foreign_keys()` must return `ForeignKeyMetadata` records with public attributes including `column`, `dest_table`, `dest_column`, and `table`. If introspection targets a missing table, then SQLite must raise the driver error or return the backend's empty metadata result according to the requested metadata kind.

**Reflection.**
`Introspector.from_database()` must create an introspector suitable for the supplied database. `generate_models()` and `Introspector.generate_models()` must return a dictionary mapping database table names to generated `Model` classes. Generated models must include fields for reflected columns, table names matching the source tables, primary-key metadata, indexes supported by the reflection layer, and foreign-key relationships where the database metadata provides them. When `table_names` is supplied, reflection must restrict generation to those tables. When `include_views` is true, reflected views must be included. When `bare_fields` is true for SQLite, generated columns must use `BareField` instead of inferred field classes. If invalid table names are present and `skip_invalid` is true, then those tables must be omitted; otherwise model generation must raise a naming error.

**Migration Operations.**
`SchemaMigrator.from_database()` must return `SqliteMigrator` for a `SqliteDatabase`. The module-level `migrate()` function must execute one or more `Operation` objects in order. Migrator methods including `add_column`, `drop_column`, `rename_column`, `drop_not_null`, `add_not_null`, `alter_column_type`, `rename_table`, `add_index`, `drop_index`, `add_column_default`, and `drop_column_default` must create executable operations when called normally and must emit or execute SQL when run with migration context. When `add_column()` receives a non-null field, that field must define a default value so existing rows receive a value before the column becomes not-null. If SQLite cannot apply a requested constraint operation such as `add_constraint`, `drop_constraint`, or `add_unique`, then the SQLite migrator must raise `NotSupportedError` or `OperationalError`.

**Database URLs And pwiz.**
`playhouse.db_url.parse()` must parse database URLs into a dictionary containing `database` plus present `host`, `port`, `user`, `password`, and query-string options, converting `"true"`, `"false"`, integers, floats, `"null"`, and `"none"` query values to Python values. `playhouse.db_url.connect()` must instantiate the database class registered for the URL scheme and must merge explicit connection parameters over URL parameters. If the scheme is not registered, then `connect()` must raise `RuntimeError`. The `pwiz` console script and `python -m pwiz` must accept a database name plus options for `engine`, `host`, `port`, `user`, password prompt, `schema`, `tables`, `views`, `info`, `preserve-order`, `ignore-unknown`, and `legacy-naming`. When `engine` is omitted, `pwiz` must choose SQLite if the database path exists and PostgreSQL otherwise. If no database name is supplied or the engine is unknown, then `pwiz` must print usage or an error and exit nonzero.

## SQLite JSON And Serialization Helpers

The portable top-level JSON field and selected `playhouse` helpers provide structured value behavior over SQLite rows.

**JSONField And JSONPath.**
Top-level `JSONField` must serialize Python dictionaries, lists, strings, numbers, booleans, and `None` to a SQLite text column and deserialize them on retrieval. Path access with `field["key"]`, integer array indexes, or `field.path(...)` must return a `JSONPath` expression usable in select lists, filters, ordering, and updates. Path equality must compare JSON values in SQLite JSON form. Path `is_null()` and equality to `None` must match SQL NULL, missing keys, and JSON null through SQLite JSON extraction semantics. Field-level `is_null()` and equality to `None` must test only the column SQL NULL. `as_text()`, `as_int()`, and `as_float()` must force text or numeric casting for comparisons. If a stored value is not valid JSON for deserialization, then retrieval must raise the configured JSON loader error.

**JSON Mutation.**
`JSONPath.set()`, `insert()`, `replace()`, `append()`, `remove()`, and `length()` must produce expressions suitable for `UPDATE` or `SELECT` statements. `JSONField.append()`, `length()`, and `update()` must operate at the document root. On SQLite, JSON update semantics must follow SQLite JSON functions, including deep merge behavior for object update and deletion of keys whose patch value is JSON null. If SQLite lacks JSON function support, then executing JSON expressions must raise the SQLite driver error.

**Serialization Shortcuts.**
`model_to_dict()` must convert a model instance to a dictionary keyed by field names, recursing into foreign keys by default, using raw foreign-key IDs when `recurse` is false, including back-reference lists only when `backrefs` is true, and honoring `only`, `exclude`, `extra_attrs`, `fields_from_query`, `max_depth`, and `manytomany`. `dict_to_model()` must construct an unsaved model instance from field keys, nested foreign-key dictionaries, and back-reference lists. `update_model_from_dict()` must update an existing model instance using the same mapping rules. If unknown keys are present and `ignore_unknown` is false, then these helpers must raise an attribute or key error.

## State Model

The core state is a SQLite database plus a set of Python model classes bound to database objects. Public projections expose that state as model metadata, generated SQL expressions, connection state, transaction state, database schema metadata, model instances, row-type iterators, reflected classes, migration side effects, and `pwiz` generated source.

1. Model metadata projection: field descriptors, `_meta`, `_schema`, primary keys, table names, indexes, and constraints.
2. Query projection: `Select`, `Insert`, `Update`, `Delete`, expression objects, SQL strings, parameters, row cursors, and returned model or row values.
3. Database projection: open or closed connection status, transaction depth, SQLite pragmas, attached databases, schema objects, and introspection metadata.
4. Reflection and tooling projection: generated model classes from `generate_models()` or text emitted by `pwiz`.
5. Migration projection: ordered DDL operations and the resulting SQLite schema visible through queries and introspection.

## Error Semantics

| Condition | Required Result |
|---|---|
| `connect()` is called on an open database with `reuse_if_open` false | Raise `OperationalError` |
| A deferred database is used before `init()` | Raise `InterfaceError` |
| An uninitialized `DatabaseProxy` is used | Raise `AttributeError` |
| `Model.get()` finds no row | Raise the model-specific `DoesNotExist` subclass |
| A SQLite uniqueness, foreign-key, or not-null constraint fails | Raise `IntegrityError` |
| A query executes without a bound database | Raise `InterfaceError` |
| A requested backend feature is unsupported by SQLite | Raise `OperationalError` or `NotSupportedError` |
| A `ManyToManyField` mutation receives an unsaved protected instance | Raise `ValueError` |
| `playhouse.db_url.connect()` receives an unknown URL scheme | Raise `RuntimeError` |
| `pwiz` receives no database name or an unrecognized engine | Exit nonzero after printing usage or an error |
| `dict_to_model()` or `update_model_from_dict()` receives an unknown key while `ignore_unknown` is false | Raise an attribute or key error |

## Cross-View Invariants

1. A field declared on a model class must appear in `_meta.fields`, generated table DDL, inserted row storage, selected model instances, dictionary row output, and reflection metadata for the created table.
2. A `ForeignKeyField` relationship must agree across stored `<field>_id` values, joined model reconstruction, back-reference queries, `prefetch()` association, introspected foreign-key metadata, and `pwiz` generated field declarations.
3. A transaction rollback through `atomic()`, `transaction()`, or `savepoint()` must remove its uncommitted row changes from subsequent selects, counts, introspection-dependent workflows, and reflected generated models.
4. A schema change applied through `migrate()` must be visible through `get_columns()`, reflected model fields, `pwiz` output, and ORM queries that use the changed column or table name.
5. A table name derived from `Meta.table_name`, `Meta.table_function`, or `legacy_table_names` must match SQL execution, `table_exists()`, schema introspection names, reflection dictionary keys, and generated model `Meta.table_name`.
6. A JSON value inserted through a model field must round-trip through model instances, `dicts()` rows, JSON path filters, JSON path selected aliases, and JSON mutation expressions according to SQLite JSON semantics.
7. A database binding change through `bind()` or `bind_ctx()` must affect model query execution, schema creation, reflection over the target database, and migration operations, and `bind_ctx()` must restore the previous database after exit.
8. A write query using `returning()` on SQLite with returning support must expose affected rows consistently through cursor iteration, row-type adapters, affected database state, and subsequent select queries.

## Public Interface

### Import Surface

```python
import peewee
from peewee import *
```

```python
from peewee import (
    AnyField, AsIs, AutoField, BareField, BigAutoField, BigBitField,
    BigIntegerField, BinaryUUIDField, BitField, BlobField, BooleanField,
    Case, Cast, CharField, Check, Column, CompositeKey, Context, Database,
    DatabaseError, DatabaseProxy, DataError, DateField, DateTimeField,
    DecimalField, Default, DeferredForeignKey, DeferredThroughModel,
    DJANGO_MAP, DoesNotExist, DoubleField, DQ,
    Entity, EXCLUDED, Field, FixedCharField, FloatField, fn, ForeignKeyField,
    IdentityField, ImproperlyConfigured, Index, IntegerField, IntegrityError,
    InterfaceError, InternalError, IPField, JOIN, JSONField, Load,
    ManyToManyField, Model, ModelIndex, MySQLDatabase, NotSupportedError, OP,
    OperationalError, PostgresqlDatabase, PrimaryKeyField, prefetch,
    PREFETCH_TYPE, ProgrammingError, Proxy, QualifiedNames, SchemaManager,
    Select, SmallIntegerField, SQL, SqliteDatabase, Table, TextField,
    TimeField, TimestampField, Tuple, UUIDField, Value, ValuesList, Window,
    chunked,
)
```

```python
from playhouse.db_url import connect, parse, register_database
from playhouse.migrate import (
    Operation, SchemaMigrator, SqliteMigrator, migrate, make_index_name,
)
from playhouse.reflection import (
    Column, Introspector, UnknownField, generate_models, introspect,
    print_model, print_table_sql,
)
from playhouse.shortcuts import (
    ThreadSafeDatabaseMetadata, dict_to_model, model_to_dict,
    update_model_from_dict,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `AnyField` | class | Field that accepts arbitrary storage values. |
| `AsIs` | function | Wraps a value for direct SQL use. |
| `AutoField` | class | Auto-incrementing integer primary-key field. |
| `BareField` | class | SQLite-oriented field with caller-provided adaptation. |
| `BigAutoField` | class | Auto-incrementing large integer primary-key field. |
| `BigBitField` | class | Blob-backed bitmap field. |
| `BigIntegerField` | class | Large integer field. |
| `BinaryUUIDField` | class | UUID field stored as bytes. |
| `BitField` | class | Integer bitmask field with flag helpers. |
| `BlobField` | class | Bytes field. |
| `BooleanField` | class | Boolean field stored compatibly with SQLite. |
| `Case` | function | Builds SQL CASE expressions. |
| `Cast` | class | Casts an expression to a SQL type. |
| `CharField` | class | Variable-length text field. |
| `Check` | function | Builds a SQL CHECK constraint. |
| `chunked` | function | Splits an iterable into fixed-size batches. |
| `Column` | class | Query-builder column reference. |
| `CompositeKey` | class | Composite primary-key declaration for model metadata. |
| `Context` | class | SQL rendering context for nodes and values. |
| `Database` | class | Base database abstraction for execution, connections, schema, and transactions. |
| `DatabaseError` | exception | Base database exception. |
| `DatabaseProxy` | class | Deferred database placeholder. |
| `DataError` | exception | Data-value database exception. |
| `DateField` | class | Date field with date-part expressions. |
| `DateTimeField` | class | Datetime field with date and time part expressions. |
| `DecimalField` | class | Decimal field with precision settings. |
| `Default` | function | Builds a SQL DEFAULT constraint. |
| `DeferredForeignKey` | class | Foreign key resolved after the target model exists. |
| `DeferredThroughModel` | class | Placeholder through model for many-to-many relationships. |
| `DJANGO_MAP` | constant | Mapping for Django-style query operator names. |
| `DoesNotExist` | exception | Base no-row-found exception. |
| `DoubleField` | class | Double-precision floating field. |
| `DQ` | class | Django-style query expression object. |
| `Entity` | class | Quoted SQL identifier path. |
| `EXCLUDED` | constant | Namespace for values proposed by an upsert. |
| `Field` | class | Base field descriptor and value converter. |
| `FixedCharField` | class | Fixed-length character field. |
| `FloatField` | class | Floating-point field. |
| `fn` | constant | Dynamic SQL function namespace. |
| `ForeignKeyField` | class | Field representing a relationship to another model. |
| `IdentityField` | class | SQL identity field where supported. |
| `ImproperlyConfigured` | exception | Configuration error exception. |
| `Index` | class | SQL index declaration. |
| `IntegerField` | class | Integer field. |
| `IntegrityError` | exception | Constraint violation exception. |
| `InterfaceError` | exception | Misuse of a database interface exception. |
| `InternalError` | exception | Internal database error exception. |
| `IPField` | class | IP address field stored as an integer. |
| `JOIN` | constant | Join-type namespace. |
| `JSONField` | class | Portable JSON field. |
| `Load` | class | Prefetch loading helper. |
| `ManyToManyField` | class | Relationship descriptor backed by a junction model. |
| `Model` | class | Base ORM model class. |
| `ModelIndex` | class | Index bound to model fields. |
| `MySQLDatabase` | class | MySQL database class exposed for imports but not required for local SQLite behavior. |
| `NotSupportedError` | exception | Unsupported feature exception. |
| `OP` | constant | SQL operator namespace. |
| `OperationalError` | exception | Operational database exception. |
| `PostgresqlDatabase` | class | PostgreSQL database class exposed for imports but not required for local SQLite behavior. |
| `PrimaryKeyField` | class | Compatibility alias for integer primary-key behavior. |
| `prefetch` | function | Eagerly loads related objects for model queries. |
| `PREFETCH_TYPE` | constant | Prefetch strategy namespace. |
| `ProgrammingError` | exception | Programming database exception. |
| `Proxy` | class | Generic deferred-object proxy. |
| `QualifiedNames` | class | SQL rendering option for qualified names. |
| `SchemaManager` | class | Model DDL manager. |
| `SmallIntegerField` | class | Small integer field. |
| `Select` | class | Query-builder SELECT object. |
| `SQL` | class | Raw SQL fragment with optional parameters. |
| `SqliteDatabase` | class | SQLite database implementation. |
| `Table` | class | Query-builder table source. |
| `TextField` | class | Text field. |
| `TimeField` | class | Time field with time-part expressions. |
| `TimestampField` | class | Unix timestamp datetime field. |
| `Tuple` | class | SQL tuple expression. |
| `UUIDField` | class | UUID field stored as text. |
| `Value` | class | Bound SQL value wrapper. |
| `ValuesList` | class | VALUES list source for queries. |
| `Window` | class | SQL window definition. |
| `connect` | function | Parses a database URL and returns a database instance. |
| `parse` | function | Parses a database URL into connection parameters. |
| `register_database` | function | Registers URL schemes for database classes. |
| `Operation` | class | Deferred migration operation. |
| `SchemaMigrator` | class | Factory and base class for schema migrations. |
| `SqliteMigrator` | class | SQLite migration implementation. |
| `migrate` | function | Executes migration operations in order. |
| `make_index_name` | function | Derives an index name from a table and columns. |
| `Introspector` | class | Generates models from existing database metadata. |
| `UnknownField` | class | Placeholder for columns with unknown reflected types. |
| `generate_models` | function | Returns reflected model classes keyed by table name. |
| `introspect` | function | Builds reflection metadata from a database. |
| `print_model` | function | Prints a model schema summary. |
| `print_table_sql` | function | Prints CREATE TABLE SQL for a model. |
| `ThreadSafeDatabaseMetadata` | class | Metadata class storing active database in thread-local state. |
| `dict_to_model` | function | Builds a model instance graph from a dictionary. |
| `model_to_dict` | function | Serializes a model instance graph to dictionaries and lists. |
| `update_model_from_dict` | function | Updates an instance graph from a dictionary. |

### CLI Entry Points

Console script: `pwiz`

Module invocation: `python -m pwiz`

Purpose: introspect a database and print model source code.

| Option | Role |
|---|---|
| `database_name` | Required database name or SQLite file path. |
| `-e`, `--engine` | Database engine; SQLite-local assessment uses `sqlite` or `sqlite3`. |
| `-H`, `--host` | Host connection parameter for engines that use hosts. |
| `-p`, `--port` | Integer port connection parameter. |
| `-u`, `--user` | User connection parameter. |
| `-P`, `--password` | Prompt for a password and include it in generated database kwargs. |
| `-s`, `--schema` | Schema name passed to introspection. |
| `-t`, `--tables` | Comma-separated table names to include. |
| `-v`, `--views` | Include views in generated models. |
| `-i`, `--info` | Include generation metadata comments. |
| `-o`, `--preserve-order` | Emit columns in source database order. |
| `-I`, `--ignore-unknown` | Comment or omit unknown fields rather than emitting `UnknownField` definitions. |
| `-L`, `--legacy-naming` | Use legacy generated Python names. |

| Exit | Meaning |
|---:|---|
| 0 | Model source was generated successfully. |
| 1 | Required arguments, engine selection, connection, or introspection failed. |

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access. The SQLite driver is provided by the Python standard library `sqlite3` module. No third-party runtime packages are required for the SQLite-local behavior in this specification. The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so the package is installable with pip.

## Appendix B: Assessment Notes

Assessment covers public behavior through Python imports and the `pwiz` command. The checks exercise model declaration, field conversion, relationship access, query construction, row-return adapters, writes, transactions, schema creation and deletion, SQLite pragmas, reflection, migration operations, URL parsing, serialization helpers, JSON path behavior, and command output dimensions.

The assessment compares observable results: returned values, raised exception classes, SQLite rows and schema metadata, generated model classes, SQL execution effects, and CLI exit status. It does not inspect private attributes, private modules, exact representation strings, exact error messages, external services, or network behavior.
