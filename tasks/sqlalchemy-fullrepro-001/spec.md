# SQLAlchemy Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

SQLAlchemy is a Python SQL toolkit and Object Relational Mapper. It has two closely related layers:

- Core provides database connectivity, transaction management, schema metadata, SQL expression construction, SQL compilation, and result handling.
- ORM builds on Core to map Python classes to database tables, track object identity and changes in a `Session`, and load related objects through relationship attributes.

The Core and ORM share the same SQL expression system. A `select()` statement can be executed by a Core `Connection` or by an ORM `Session`; the difference is whether the selected objects are table/column constructs or ORM mapped entities.

## Non-Goals

- Reproducing SQLAlchemy's internal module layout, helper classes, cache keys, visitor internals, compiler internals, or private attributes.
- Reproducing `sqlalchemy.testing`, upstream test fixtures, pytest plugin behavior, or test-suite convenience APIs.
- Matching exact object `repr()` strings, anonymous alias numbering beyond user-visible SQL semantics, logging line formatting, or SQL whitespace.
- Implementing every SQLAlchemy public export. Advanced Core constructs such as CTEs, lateral joins, table-valued functions, lambda statements, `CreateView`, `CreateTableAs`, custom operators, and set operations are outside this scope.
- Implementing database-server dialects such as PostgreSQL, MySQL, SQL Server, or other server databases, or optional third-party DBAPI integrations.
- Implementing asyncio APIs, greenlet behavior, connection pool tuning, engine plugins, event dispatch APIs, and low-level DBAPI adaptation.
- Implementing advanced ORM topics such as inheritance mapping, polymorphic loading, dataclass mappings, composites, synonyms, association proxies, scoped sessions, dynamic/write-only relationships, custom collections, mapper/session events, merge/frozen result helpers, and legacy `Query` coverage.
- Implementing Alembic migrations or long-term schema migration workflows.
- Guaranteeing SQLite behavior that depends on unavailable SQLite library features; when SQLite itself rejects unsupported SQL, SQLAlchemy may surface the DBAPI-derived error.

## Representative Workflows

### Core and ORM over SQLite

```python
from typing import List, Optional

from sqlalchemy import (
    Column, ForeignKey, Integer, MetaData, String, Table,
    create_engine, insert, select, text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload

engine = create_engine("sqlite://")

metadata = MetaData()
user_table = Table(
    "user_account",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(30), nullable=False),
    Column("fullname", String),
)
address_table = Table(
    "address",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("user_account.id"), nullable=False),
    Column("email_address", String, nullable=False),
)
metadata.create_all(engine)

with engine.begin() as conn:
    result = conn.execute(
        insert(user_table).returning(user_table.c.id),
        [{"name": "sandy", "fullname": "Sandy Cheeks"}],
    )
    sandy_id = result.scalar_one()
    conn.execute(
        insert(address_table),
        [{"user_id": sandy_id, "email_address": "sandy@example.org"}],
    )

stmt = (
    select(user_table.c.name, address_table.c.email_address)
    .join_from(user_table, address_table)
    .where(user_table.c.name == "sandy")
)
with engine.connect() as conn:
    rows = conn.execute(stmt).all()
    assert rows[0].name == "sandy"

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]
    addresses: Mapped[List["Address"]] = relationship(back_populates="user")

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    email_address: Mapped[str]
    user: Mapped[User] = relationship(back_populates="addresses")

with Session(engine) as session:
    user = session.scalars(
        select(User).options(selectinload(User.addresses)).where(User.name == "sandy")
    ).one()
    assert user.addresses[0].email_address == "sandy@example.org"

    user.addresses.append(Address(email_address="sandy2@example.org"))
    session.commit()

reflected = Table("address", MetaData(), autoload_with=engine)
assert reflected.c.email_address.name == "email_address"

with engine.connect() as conn:
    count = conn.scalar(text("select count(*) from address"))
    assert count == 2
```

## Engine and Connection Management

This section covers how applications create database engines, obtain connections, manage transaction boundaries, execute statements, and consume results.

**Engine Creation and URL Forms**

When `create_engine` is called with a database URL string or `URL` object, it must return an `Engine`. The engine must not open a DBAPI connection until the first operation that needs one, such as `Engine.connect()`, `Engine.begin()`, ORM `Session` use, or schema creation. When `echo=True` is passed, the engine must log SQL through SQLAlchemy's logging integration.

SQLite URL forms are part of the public contract. `sqlite://` must create an in-memory SQLite database using the default SQLite DBAPI. `sqlite:///:memory:` must explicitly use SQLite's `:memory:` database. `sqlite:///relative.db` must use a relative file path. `sqlite:////absolute/path.db` must use an absolute Unix-style path. `sqlite:///C:\path\to\file.db` must be accepted for Windows paths. `sqlite+pysqlite://...` must explicitly name the built-in pysqlite/sqlite3 driver.

**Connection Lifecycle and Transactions**

When `Engine.connect()` is called, it must return a `Connection` context manager. Executing through a connection must begin an implicit DBAPI transaction when work first occurs. Exiting a `connect()` block without committing must roll back uncommitted work. When `Connection.commit()` is called, it must commit current work and allow later work in the same connection block to begin a new transaction.

When `Engine.begin()` is called, it must return a context manager that provides a `Connection` and commits on successful block exit. If an exception leaves the block, the transaction must be rolled back.

**Statement Execution**

When `Connection.execute(statement, parameters)` is called, it must execute the statement and return a `Result`. When `Connection.scalar(statement, parameters)` is called, it must return the first column of the first row. The `parameters` argument may be one dictionary for a single execution or a list of dictionaries for executemany. Textual SQL parameters must use SQLAlchemy's named colon form, such as `text("select * from t where id=:id")`; the SQLite dialect must adapt these to the DBAPI's qmark parameter style when sending SQL to SQLite.

**Result and Row Behavior**

A `Result` must be iterable and yield `Row` objects. `Result.all()` must return all remaining rows as a list. `Result.first()` must return the first row or `None`. `Result.one()` must require exactly one row and raise `NoResultFound` when no row exists or `MultipleResultsFound` when more than one row exists. `Result.scalar()` must return the first column of the first row or `None`. `Result.scalar_one()` must return the first column of the single row or raise cardinality errors. `Result.scalars()` must return a `ScalarResult` over the first selected element of each row. `ScalarResult.one()` must enforce the same cardinality constraints as `Result.one()`. `ScalarResult.all()` must return all scalar values as a list. `Result.mappings()` must return mapping rows whose keys are column names, labels, or ORM entity names where applicable; mapping rows must support dictionary-style subscript access and conversion to `dict`.

A `Row` must behave like a named tuple for positional unpacking and integer indexing. It must also expose column names as attributes when those names are present and unambiguous. Mapping-style access must be available from rows produced by `Result.mappings()`.

## Schema Definition and Reflection

This section covers how applications define database schemas through metadata collections, declare tables and columns with constraints, create and drop DDL, reflect existing schemas from the database, and inspect schema information.

**MetaData and Table Declaration**

A `MetaData` instance must serve as a collection of schema constructs. `MetaData.tables` must be keyed by table name, or by schema-qualified table name when a table has a schema. `MetaData.sorted_tables` must return tables ordered so referenced tables precede dependent tables based on foreign key dependencies.

When a `Table` is constructed with a name, metadata, and columns, it must attach itself to the `MetaData` collection. A table's columns must be available through `table.c` and `table.columns`. The column collection must support attribute access for ordinary names, indexed access for all names, iteration in declaration order, and `keys()` which must return column names in declaration order.

**Column and Type Behavior**

When a `Column` is constructed, the common user-visible attributes must include `name`, `key`, `type`, `nullable`, `primary_key`, `foreign_keys`, and `table`. The `key` attribute must default to `name` and control Python-side lookup when set explicitly. A column with `primary_key=True` must participate in the table's primary key and must be treated as non-nullable unless explicitly overridden. A `ForeignKey("other_table.id")` must be able to infer the local column type from the referenced column when no local type is given. Every `ForeignKey` must expose a `target_fullname` attribute containing the fully qualified string reference (e.g., `"table_name.column_name"`).

Common type classes must include `Integer`, `String`, `Text`, `Boolean`, `Date`, `DateTime`, `Time`, `Numeric`, `Float`, `LargeBinary`, and `JSON`. Type classes may be passed either as classes or instances in normal column declarations. When `String(30)` is used, it must carry a length for DDL and SQL compilation.

**Primary Key and Constraint Collections**

A table must expose `table.primary_key` as a primary key constraint object. `table.primary_key.columns.keys()` must return the list of column names participating in the primary key. Columns with `foreign_keys` must expose that attribute as a set of foreign key objects.

**Constraints and Indexes**

Constraints may be declared through column flags or explicit objects. `PrimaryKeyConstraint`, `ForeignKeyConstraint`, `UniqueConstraint`, `CheckConstraint`, and `Index` must be associated with tables and participate in DDL generation and reflection where SQLite can report them.

**DDL Creation and Destruction**

When `MetaData.create_all(engine_or_connection)` is called, it must emit DDL for all contained tables that are not already present. Tables must be created in dependency order based on foreign keys. When `MetaData.drop_all(engine_or_connection)` is called, it must drop tables in reverse dependency order. `Table.create()` and `Table.drop()` must operate on a single table; when `checkfirst=True` is passed, SQLAlchemy must check for existence first.

**Reflection from Database**

When a `Table` is constructed with `autoload_with=engine_or_connection`, it must reflect an existing table into Python metadata by reading database schema information. The reflected `Table` must be usable like an explicitly declared table: it must have `c`, `columns`, `primary_key`, `foreign_keys`, and column type/nullability information.

When `MetaData.reflect(bind=engine)` is called, it must reflect all tables in the database into the metadata collection. The resulting `MetaData.tables` must contain entries for all discovered tables with their columns and foreign key relationships intact.

**Inspector**

When `inspect(engine_or_connection)` is called, it must return an `Inspector`. The inspector must expose `get_table_names()` returning a list of table name strings, `get_columns(table_name)` returning a list of dictionaries each containing a `"name"` key, `get_pk_constraint(table_name)` returning a dictionary with a `"constrained_columns"` key, `get_foreign_keys(table_name)` returning a list of dictionaries each containing `"referred_table"` and `"constrained_columns"` keys, `get_indexes(table_name)` returning a list of dictionaries each containing a `"name"` key, `get_unique_constraints(table_name)` returning a list of dictionaries each containing a `"name"` key, and `get_check_constraints(table_name)` returning a list of dictionaries each containing a `"name"` key.

**Reflection Errors**

Reflecting a missing table must raise `sqlalchemy.exc.NoSuchTableError`. A foreign key string that cannot locate its target table must raise `NoReferencedTableError`. A foreign key that cannot locate its target column must raise `NoReferencedColumnError`.

## SQL Expression Construction

This section covers how applications build SQL statements programmatically, combine boolean expressions, use functions and casts, label result columns, join tables, and execute DML operations.

**Select Statement Construction**

When `select(*entities)` is called, it must accept tables, columns, SQL expressions, and ORM entities. Selecting a `Table` must expand to its columns. Selecting columns must infer a `FROM` clause from the tables represented by those columns. Selecting an ORM class must return ORM instances when executed through `Session`.

`Select` must be generative: methods such as `.where()`, `.filter_by()`, `.join()`, `.join_from()`, `.outerjoin()`, `.select_from()`, `.order_by()`, `.group_by()`, `.limit()`, `.offset()`, `.options()`, and `.execution_options()` must return a new statement with the added behavior while preserving the earlier statement.

**Column Expressions and Comparisons**

Column comparisons such as `table.c.name == "sandy"`, `!=`, `<`, `<=`, `>`, `>=`, `.like()`, `.in_()`, `.is_(None)`, and `.is_not(None)` must produce SQL boolean expressions rather than Python booleans. The `.between(low, high)` method on a column must produce a SQL BETWEEN expression. Python literals in expressions must become bound parameters unless the API explicitly represents literal SQL text.

**Boolean Combinations**

Multiple criteria passed to `.where()` or produced by repeated `.where()` calls must be joined with SQL `AND`. `and_()`, `or_()`, and `not_()` must build explicit boolean combinations. `true()`, `false()`, and `null()` must represent SQL constants. When `null().is_(None)` is evaluated, it must produce a true result.

**Textual SQL and Bound Parameters**

`text()` must represent literal SQL text and may be executed directly. Its parameter style must be SQLAlchemy named colon syntax. `literal_column()` must represent a textual SQL column expression. `literal()` must represent a Python value as a SQL bound value. `bindparam(key, value=None)` must create an explicitly named bound parameter that can be reused in statements and filled at execution time. Bound parameters must never interpolate values into SQL text; even potentially dangerous strings must be passed safely as parameters.

**Functions, Cast, and Type Coerce**

`func.<name>(...)` must create a SQL function call for arbitrary function names. Common functions such as `func.count()` and `func.sum()` must have useful SQLAlchemy return types. `cast(expression, type_)` must render SQL `CAST` and give the expression SQLAlchemy type behavior. `type_coerce(expression, type_)` must give SQLAlchemy type behavior without rendering a SQL `CAST`.

**Labels and Column Naming**

`ColumnElement.label(name)` must assign a result-column name. Labels must be available on returned rows by the label name when unambiguous.

**Statement Compilation and String Representation**

When `str(stmt)` is called on a statement, it must produce a SQL text representation containing the relevant clause structure (SELECT columns, FROM tables, WHERE conditions) with named bound parameters in colon syntax. When `stmt.compile()` is called, the resulting compiled object must expose a `.params` dictionary mapping parameter names to their bound values.

**Joins**

`Select.join(target)` and `Select.join_from(left, right, onclause=None)` must add JOINs. With table metadata, SQLAlchemy must be able to infer an ON clause from one unambiguous foreign key path. With ORM relationship attributes, passing the relationship to `.join()` must supply both the target and the ON clause. `Select.select_from(entity)` must set the FROM clause explicitly, which is required when using aggregate functions like `func.count()` without selecting from a specific column.

**SQL Compilation for SQLite**

Compiling for SQLite must use SQLite identifier quoting, parameter style, type names, and dialect features. The exact whitespace of SQL strings is not part of the contract; the SQL structure, selected columns, FROM/JOIN/WHERE semantics, parameter binding, and result behavior are.

**Insert, Update, and Delete**

When `insert(table)` is called, it must create an `Insert`. `.values()` must supply values, `.returning()` must ask for returned columns where the dialect supports it, and execution with a list of parameter dictionaries must perform executemany. For SQLite versions that support it, SQLAlchemy may use SQLite `RETURNING`.

When `update(table)` is called, it must create an `Update`. `.where()` must filter rows and `.values()` must supply new values.

When `delete(table)` is called, it must create a `Delete`. `.where()` must filter rows.

**DML Results**

Executed DML must return a `CursorResult`. The result must expose `rowcount` as an integer reflecting the number of affected rows. The result must expose `inserted_primary_key` as a tuple containing the primary key values of the inserted row where the backend can provide it. `Result.scalar_one()` must return the single scalar value from a RETURNING clause.

## ORM Mapping and Session

This section covers how applications define ORM mapped classes, create and manage sessions, persist and query objects through the identity map, and control transaction boundaries at the ORM level.

**Declarative Mapping**

When `DeclarativeBase` is subclassed, it must create a base class for mapped models. The base must have a `metadata` collection and a `registry`. Subclasses with `__tablename__` and mapped attributes must be configured as ORM mapped classes at class creation time. Each mapped class must receive a `__table__` attribute referring to the generated `Table`. That `__table__` must be the same object as `Base.metadata.tables[tablename]`.

`declarative_base()` must be the function form for creating a declarative base and must remain supported.

**Mapped Attributes and Type Inference**

`Mapped[T]` must mark ORM mapped attributes for typing and declarative configuration. `mapped_column()` must declare a table column in a declarative class. When no explicit SQLAlchemy type is supplied, common Python annotations must infer common SQL types: `int` to `Integer`, `str` to `String`. When `Optional[str]` or `str | None` is used as the annotation, the column must be nullable unless `nullable=` is explicitly supplied. When a non-optional type like `Mapped[str]` is used, the column must be non-nullable. Every mapped class must have a primary key mapping.

**Default Initializer**

Declarative mapped classes must receive a default `__init__()` when they do not define one. The default initializer must accept mapped attribute names as optional keyword arguments, including relationship attributes. Constructing a mapped instance with keyword arguments must set those attributes on the new instance.

**Class-Level vs Instance-Level Attributes**

Mapped class attributes must be SQL expression objects at the class level and ordinary instrumented attributes at the instance level. `select(User)` must select ORM entities. `select(User.name, User.fullname)` must select individual column values.

**Session Creation and Binding**

When `Session(engine)` is called, it must bind a session to an engine. When used as `with Session(engine) as session:`, it must close the session at block exit. When `Session(bind=connection)` is used, the session must share the provided connection's transaction. `sessionmaker(engine)` must create a reusable factory. When `SessionFactory.begin()` is used as a context manager, it must open a session and transaction, committing on success and rolling back on exception.

**Identity Map**

The session must maintain an identity map: within one session, rows with the same mapped class and primary key must resolve to the same Python object. `Session.get(Entity, primary_key)` must first check the identity map and query the database if needed. Composite primary keys may be passed as tuples.

**Adding and Flushing Objects**

`Session.add(obj)` must place a transient or detached instance into the session. `Session.add_all([...])` must add several instances. New instances must become pending and be INSERTed on flush. Already persistent instances must not need to be added again.

`Session.flush()` must write pending INSERT, UPDATE, and DELETE statements to the database transaction without committing it. With default autoflush, flush must occur before ORM-enabled `Session.execute()` calls, before lazy loads, before refresh operations, and inside `Session.commit()`. `Session.no_autoflush` must temporarily suppress autoflush as a context manager, but commit must still flush pending changes.

**Commit and Expire Behavior**

`Session.commit()` must flush pending changes, commit the database transaction, release the connection, and by default expire all persistent objects so later attribute access refreshes them in a new transaction. When `expire_on_commit=False` is passed to the session, that expiration behavior must be disabled.

`Session.expire(obj, attribute_names)` must mark the specified attributes on a persistent object as expired so that the next access triggers a refresh from the database within the current transaction.

**Rollback**

`Session.rollback()` must roll back the current transaction if one exists, release connections, expunge pending objects whose INSERT was rolled back (so `object_session(obj)` returns `None` for those objects), restore deleted objects to persistent state when appropriate, and expire remaining persistent objects.

**Session Close**

`Session.close()` must expunge all ORM objects and release transactional resources. A closed session must be reset and may be reused.

**Executing Through Session**

`Session.execute(statement, parameters)` must execute Core or ORM statements and return `Result`. `Session.scalars(statement, parameters)` must return a `ScalarResult` over the first selected element. `ScalarResult.one()` must raise `NoResultFound` for no rows and `MultipleResultsFound` for more than one row.

**Deleting Objects**

`Session.delete(obj)` must mark a persistent object for DELETE on the next flush. Related rows must not be deleted by default merely because a relationship exists; relationship cascade options must control delete and delete-orphan behavior.

**Object Session Lookup**

`object_session(instance)` must return the session that owns the given persistent instance, or `None` if the instance is not associated with any session.

## Relationship Loading Strategies

This section covers how related ORM objects are loaded from the database, including lazy loading, eager loading strategies, raise-on-access behavior, and explicit join population.

**Relationship Declaration**

When `relationship()` is used to link mapped classes, SQLAlchemy must infer direction and join conditions from foreign keys in the mapped tables for simple relationships. When `back_populates` names the complementary relationship, it must make in-memory assignment synchronize both sides: appending a related object to a collection must update the reverse scalar relationship, and assigning the scalar relationship must place the object in the reverse collection.

**Collection Initialization and Cascade**

For a one-to-many collection relationship, a new instance must expose an empty collection before anything is assigned. The default cascade must include `save-update`, so adding a parent object to a session must also add transient related objects reachable through normal relationships. On flush, the unit of work must order INSERTs so parent primary keys are available for dependent foreign keys.

**Lazy Loading (Default)**

Relationships must be lazy-loaded by default with `lazy="select"`. Accessing an unloaded collection or scalar relationship must emit a SELECT using the current session and store the loaded value in memory. Re-accessing the loaded relationship must not emit SQL until it is expired. For simple many-to-one relationships, lazy loading must be able to resolve from the identity map without SQL when the target object is already present in the session.

**Selectin Loading**

When `selectinload(Entity.rel)` is applied as a query option, it must configure eager loading that emits a second SELECT using parent primary key values in an IN expression. It must load only relationships not already populated. It is the preferred eager strategy for most one-to-many collections.

**Joined Loading**

When `joinedload(Entity.rel)` is applied as a query option, it must configure eager loading by adding a JOIN dedicated to population of the relationship. This loader must not change which primary entities the query returns. For collection joined eager loads, callers must use `Result.unique()` or `ScalarResult.unique()` before consuming all objects so duplicate primary rows produced by the SQL JOIN are collapsed into unique ORM instances.

**Lazy Load Override**

When `lazyload(Entity.rel)` is applied, it must force lazy loading for a relationship on that particular statement.

**Raise Load**

When `raiseload(Entity.rel)` is applied or when `lazy="raise_on_sql"` is configured on a relationship, accessing that relationship must raise `InvalidRequestError` when access would emit SQL. `raise_on_sql` may still allow access that can be satisfied from the identity map without SQL. Raiseload must not prevent internal loads that the unit of work needs during flush.

**Contains Eager**

When `contains_eager(Entity.rel)` is applied, it must tell the ORM that an explicit join already present in the statement should be used to populate the relationship. When using a custom filtered join to populate an already-loaded collection differently, `execution_options(populate_existing=True)` must refresh existing in-memory state. The result must use `.unique()` to collapse duplicate rows when a join produces them.

**Detached Access**

When a lazy-loaded attribute is accessed on an ORM object that is detached from its session (e.g., after `session.close()`), it must raise `DetachedInstanceError`.

## SQLite Dialect Behavior

This section covers SQLite-specific type handling, date/time roundtrip behavior, JSON support, and ON CONFLICT upsert operations.

**SQLite Connectivity**

SQLite must be available without an external database server through Python's standard `sqlite3` DBAPI. In-memory SQLite databases must be per DBAPI connection unless the selected pool/connection strategy preserves one connection.

**DDL and Reflection**

SQLite DDL must use SQLite type names and SQLite reflection pragmas. `MetaData.create_all()` must check table presence before creating tables. Reflection must read table columns, primary keys, foreign keys, indexes, unique constraints, and check constraints to the extent SQLite exposes them.

**Uppercase Type Names**

The SQLite dialect must export uppercase type names such as `INTEGER`, `VARCHAR`, `TEXT`, `BOOLEAN`, `DATE`, `DATETIME`, `TIME`, `NUMERIC`, `FLOAT`, and `BLOB`. These types must be usable in column declarations and must round-trip values correctly through insert and select.

**Date, DateTime, and Time Types**

SQLite `DATE`, `DATETIME`, and `TIME` types must store values in SQLite-compatible textual forms. When read back through SQLAlchemy type processing, they must convert to Python `date`, `datetime`, or `time` objects respectively, preserving microsecond precision. When the same data is read through raw `text()` queries bypassing type processing, the values must remain as strings.

**JSON Type**

SQLite `JSON` must provide SQLAlchemy JSON expression behavior on SQLite. SQLite itself stores JSON values according to SQLite capabilities; SQLAlchemy must handle Python-side JSON bind/result processing. Nested Python structures including dictionaries, lists, booleans, and strings must round-trip through JSON columns faithfully.

**ON CONFLICT Operations**

`sqlalchemy.dialects.sqlite.insert(table)` must create a SQLite-specific `Insert`. It must support:

- `on_conflict_do_nothing(index_elements=None)` which must render an INSERT that skips rows conflicting with the chosen unique constraint or index target. The result's `rowcount` must be 0 when the row is skipped.
- `on_conflict_do_update(index_elements=None, set_=..., where=None)` which must render an INSERT that updates columns for conflicting rows. The result's `rowcount` must reflect whether the update actually occurred.

The SQLite `Insert.excluded` namespace must refer to values proposed for insertion inside the conflict update clause. When a `where` condition is supplied in `on_conflict_do_update`, the update must only apply when that condition evaluates to true for the existing row; if the condition is false, the row must remain unchanged and `rowcount` must be 0.

## State Model

SQLAlchemy exposes one database state through three public projections: schema metadata and reflection, Core expressions and result rows, and ORM mapped objects within sessions. A declared or reflected table must describe the same columns and constraints used by Core execution. Core writes and ORM reads over the same transaction must agree on row values. ORM relationship changes, after flush or commit as required, must be visible through both relationship loaders and equivalent Core joins.

## Error Semantics

`sqlalchemy.exc.SQLAlchemyError` is the common base class for SQLAlchemy-raised exceptions.

`ArgumentError` is raised for invalid API construction arguments, such as inconsistent mapping or expression configuration.

`InvalidRequestError` is raised when an API call is not valid for the current object state, such as using `raiseload` and then accessing a relationship that would need SQL.

`NoResultFound` is raised by `.one()` or scalar-one style result methods when no row is present. `MultipleResultsFound` is raised when exactly one row was required but multiple rows are present.

`StatementError` wraps errors that occur while executing a statement and carries statement/parameter context. `DBAPIError` is the base for wrapped DBAPI exceptions. `IntegrityError`, `OperationalError`, and related database error subclasses correspond to DBAPI error categories. After an `IntegrityError` during flush, the session must be rolled back before normal use continues.

`NoSuchTableError` is raised when reflecting or inspecting a table that does not exist.

`NoReferencedTableError` and `NoReferencedColumnError` are raised when a foreign key target table or column cannot be resolved.

`NoForeignKeysError` is raised when SQLAlchemy is asked to infer a join path but no foreign key relationship exists. `AmbiguousForeignKeysError` is raised when more than one foreign key path exists and no explicit join condition disambiguates it.

`orm_exc.DetachedInstanceError` is raised when an unloaded or expired ORM attribute needs a session but the object is detached.

`orm_exc.FlushError` is raised for ORM flush problems that SQLAlchemy can identify before or during unit-of-work processing. Database constraint violations during flush are typically surfaced as DBAPI-derived exceptions such as `IntegrityError`, and the session must be rolled back before normal use continues.

`orm_exc.UnmappedClassError` and `orm_exc.UnmappedInstanceError` are raised when ORM operations receive classes or instances that are not mapped.

## Cross-View Invariants

1. A `Table` declared in `MetaData` and the SQL generated from it must describe the same table name, column names, primary key, nullable flags, and foreign key relationships; a reflected `Table` must produce metadata objects usable by the same SQL expression and execution APIs as explicitly declared metadata.
2. A `Column` reached through `table.c.name`, selected with `select(table.c.name)`, returned through a row attribute, and reflected back from SQLite must refer to the same user-visible column key unless an explicit label or key changes that view.
3. Python literal values in expression comparisons and textual parameters must be sent as bound parameters during execution; the values must not be interpolated into SQL text by ordinary expression construction.
4. Core execution and ORM session execution must share the same transaction rule: database work occurs inside a transaction that is committed explicitly or rolled back when the scope exits without commit.
5. A row inserted through Core DML and later queried through an ORM mapping over the same table must produce an ORM object with attributes matching the stored column values.
6. Within a single `Session`, two queries that load the same mapped class and primary key must return the same Python object identity; `Session.get()` must also return this same identity-mapped instance.
7. An ORM update committed through `Session` must be visible when the same row is queried through Core execution on a reflected table from the same engine.
8. Relationship `back_populates` must keep both Python-side directions synchronized before persistence, and after flush and commit, the stored foreign key values must be consistent with the relationship traversal through both Core joins and ORM loaders.
9. Loader strategies may change how many SQL statements are emitted, but they must not change the set of primary ORM objects a statement is meant to return; `joinedload` with `.unique()` must return the same primary objects as `selectinload`.
10. `MetaData.reflect(bind=engine)` must reconstruct the same foreign key `target_fullname` references and column structure that was originally declared and created with `MetaData.create_all()`.

## Public Interface

### Import Surface

The library is imported as `sqlalchemy`; ORM helpers live in `sqlalchemy.orm`; SQLite dialect helpers live in `sqlalchemy.dialects.sqlite`.

Common Core imports:

```python
from sqlalchemy import (
    create_engine, inspect, text, bindparam,
    MetaData, Table, Column, ForeignKey, ForeignKeyConstraint,
    PrimaryKeyConstraint, UniqueConstraint, CheckConstraint, Index,
    Integer, String, Text, Boolean, Date, DateTime, Time, Numeric, Float,
    LargeBinary, JSON,
    select, insert, update, delete,
    and_, or_, not_, true, false, null,
    literal, literal_column, column, table, func,
    cast, type_coerce, asc, desc, between,
)
from sqlalchemy import exc
```

Common ORM imports:

```python
from sqlalchemy.orm import (
    DeclarativeBase, declarative_base, Mapped, mapped_column,
    relationship, Session, sessionmaker, object_session,
    joinedload, selectinload, lazyload, raiseload, contains_eager, Load,
)
from sqlalchemy.orm import exc as orm_exc
```

SQLite dialect imports:

```python
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.sqlite import DATE, DATETIME, TIME, JSON
```

There is no command-line interface in this scope.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| create_engine | function | Create a database engine from a URL |
| Engine | class | Database connectivity and connection factory |
| Connection | class | Active database connection with transaction control |
| Result | class | Iterable result set from statement execution |
| CursorResult | class | DML result with rowcount and inserted primary key |
| Row | class | Named-tuple-like row from a result set |
| ScalarResult | class | Scalar projection over result rows |
| MetaData | class | Collection of schema constructs |
| Table | class | Database table representation |
| Column | class | Database column representation |
| ForeignKey | class | Foreign key reference to another column |
| PrimaryKeyConstraint | class | Primary key constraint |
| ForeignKeyConstraint | class | Multi-column foreign key constraint |
| UniqueConstraint | class | Unique constraint |
| CheckConstraint | class | Check constraint |
| Index | class | Table index |
| inspect | function | Return an Inspector for schema introspection |
| Inspector | class | Schema introspection interface |
| select | function | Create a SELECT statement |
| insert | function | Create an INSERT statement |
| update | function | Create an UPDATE statement |
| delete | function | Create a DELETE statement |
| text | function | Create a literal SQL text clause |
| bindparam | function | Create a named bound parameter |
| func | namespace | SQL function call generator |
| cast | function | Render a SQL CAST expression |
| type_coerce | function | Apply type behavior without SQL CAST |
| and_ | function | Combine boolean expressions with AND |
| or_ | function | Combine boolean expressions with OR |
| not_ | function | Negate a boolean expression |
| asc | function | Mark a column for ascending sort order |
| desc | function | Mark a column for descending sort order |
| literal | function | Represent a Python value as a SQL bound value |
| literal_column | function | Represent textual SQL as a column expression |
| DeclarativeBase | class | Base class for ORM declarative models |
| declarative_base | function | Function form for creating a declarative base |
| Mapped | type | ORM mapped attribute annotation |
| mapped_column | function | Declare a column in a declarative class |
| relationship | function | Link mapped classes through foreign keys |
| Session | class | ORM database conversation and identity map |
| sessionmaker | class | Reusable Session factory |
| object_session | function | Return the Session owning a persistent instance |
| selectinload | function | Eager-load a relationship with a second SELECT |
| joinedload | function | Eager-load a relationship with a JOIN |
| lazyload | function | Force lazy loading on a statement |
| raiseload | function | Raise on SQL-emitting lazy load access |
| contains_eager | function | Populate a relationship from an explicit join |
| sqlite.insert | function | Create a SQLite-specific INSERT with ON CONFLICT |

### CLI Entry Points

SQLAlchemy is a library-only interface in this scope. It provides no required console command, and `python -m sqlalchemy` is not supported. Callers use the documented Core, ORM, inspection, and SQLite dialect imports.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. The covered workflows use the standard Python SQLite driver and require no external database server.

## Appendix B: Assessment Notes

The expected implementation should exercise public behavior through documented imports and ordinary user workflows. Tests should create SQLite-local engines, define metadata and declarative models, execute Core and ORM statements, inspect returned rows and objects, reflect simple schemas, and verify relationship loading behavior through public APIs.

Assessment should reward semantic compatibility rather than internal fidelity. SQL text may be checked for structural clauses, identifiers, and bound parameter behavior, but exact whitespace, private names, logging text, and internal reprs should not be used as pass/fail criteria.

Tests should cover successful workflows and representative error cases: missing reflected tables, ambiguous or missing foreign-key joins, result cardinality errors, detached lazy loads, raiseload access, and database constraint failures. They should not import `sqlalchemy.testing`, private modules, or upstream-only fixture helpers.

The SQLite dialect is the execution target for this packet. Tests should avoid requiring external database servers, optional drivers, async APIs, or dialect features not exposed by the standard Python SQLite environment.
