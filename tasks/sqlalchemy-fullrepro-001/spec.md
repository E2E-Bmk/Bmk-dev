<!-- INTERNAL
task_id: sqlalchemy-fullrepro-001
spec_version: v1
delta: Initial Stage 2 draft. Focused the candidate-visible contract on SQLAlchemy's documented day-one Core/ORM/SQLite public behavior: metadata/table/column, SQL expression construction and compilation, SQLite engine execution, reflection basics, declarative/session/unit-of-work basics, relationship loading basics, and SQLite dialect behavior. Excluded internal module organization, sqlalchemy.testing fixture contracts, exact internal repr details, backend-server dialect behavior, async support, event systems, pooling internals, extension systems, migration tooling, advanced DDL, and broad advanced ORM features not needed for a fair SQLite-local reconstruction benchmark.
source_boundary:
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\README.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\__init__.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\orm\__init__.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\engine\create.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\sql\schema.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\sql\_selectable_constructors.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\sql\_elements_constructors.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\sql\_dml_constructors.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\orm\decl_api.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\orm\_orm_constructors.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\orm\session.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\orm\strategy_options.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\exc.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\lib\sqlalchemy\orm\exc.py
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\tutorial\index.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\tutorial\engine.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\tutorial\dbapi_transactions.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\tutorial\metadata.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\tutorial\data_select.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\tutorial\orm_related_objects.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\core\metadata.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\core\sqlelement.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\core\engines.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\orm\quickstart.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\orm\session_basics.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\orm\queryguide\relationships.rst
  - G:\research\01_agents\swe-e2e\repo-pool\sqlalchemy__sqlalchemy\doc\build\dialects\sqlite.rst
public_surface_audit:
  method: Read top-level sqlalchemy exports, ORM public exports, and docs body import examples. Each exported name was considered against Q1 public contract for this scoped candidate packet and Q2 non-derivable/library-specific need. Candidate-visible body includes only items judged in-scope and non-derivable for the fair SQLite/Core/ORM reconstruction target.
  sqlalchemy_exports_read: AdaptedConnection, BaseRow, BindTyping, ChunkedIteratorResult, Compiled, Connection, create_engine, create_mock_engine, create_pool_from_url, CreateEnginePlugin, CursorResult, Dialect, Engine, engine_from_config, ExceptionContext, ExecutionContext, FrozenResult, Inspector, IteratorResult, make_url, MappingResult, MergedResult, NestedTransaction, Result, result_tuple, ResultProxy, RootTransaction, Row, RowMapping, ScalarResult, Transaction, TwoPhaseTransaction, TypeCompiler, URL, inspect, AssertionPool, AsyncAdaptedQueuePool, NullPool, Pool, PoolProxiedConnection, PoolResetState, QueuePool, SingletonThreadPool, StaticPool, BaseDDLElement, BLANK_SCHEMA, CheckConstraint, CheckFirst, Column, ColumnDefault, Computed, Constraint, CreateTable, CreateTableAs, CreateView, DDL, DDLElement, DefaultClause, DropTable, DropView, ExecutableDDLElement, FetchedValue, ForeignKey, ForeignKeyConstraint, Identity, Index, insert_sentinel, MetaData, Named, PrimaryKeyConstraint, Sequence, Table, TypedColumns, UniqueConstraint, ColumnExpressionArgument, NotNullable, Nullable, SelectLabelStyle, aggregate_order_by, AggregateOrderBy, Alias, alias, AliasedReturnsRows, all_, and_, any_, asc, between, BinaryExpression, bindparam, BindParameter, bitwise_not, BooleanClauseList, CacheKey, Case, case, Cast, cast, ClauseElement, ClauseList, collate, CollectionAggregate, column, ColumnClause, ColumnCollection, ColumnElement, ColumnOperators, CompoundSelect, CTE, cte, custom_op, Delete, delete, desc, distinct, except_, except_all, Executable, Exists, exists, Extract, extract, false, False_, FrameClause, FrameClauseType, from_dml_column, FromClause, FromGrouping, func, funcfilter, Function, FunctionElement, FunctionFilter, GenerativeSelect, Grouping, HasCTE, HasPrefixes, HasSuffixes, Insert, insert, intersect, intersect_all, Join, join, Label, label, LABEL_STYLE_DEFAULT, LABEL_STYLE_DISAMBIGUATE_ONLY, LABEL_STYLE_NONE, LABEL_STYLE_TABLENAME_PLUS_COL, lambda_stmt, LambdaElement, Lateral, lateral, literal, literal_column, modifier, not_, Null, null, nulls_first, nulls_last, nullsfirst, nullslast, Operators, or_, OrderByList, outerjoin, outparam, Over, over, quoted_name, ReleaseSavepointClause, ReturnsRows, RollbackToSavepointClause, SavepointClause, ScalarSelect, Select, select, Selectable, SelectBase, SQLColumnExpression, StatementLambdaElement, Subquery, table, TableClause, TableSample, tablesample, TableValuedAlias, TableValuedColumn, text, TextAsFrom, TextClause, TextualSelect, true, True_, try_cast, TryCast, TString, tstring, Tuple, tuple_, type_coerce, TypeClause, TypeCoerce, UnaryExpression, union, union_all, Update, update, UpdateBase, Values, values, ValuesBase, Visitable, within_group, WithinGroup, ARRAY, BIGINT, BigInteger, BINARY, BLOB, BOOLEAN, Boolean, CHAR, CLOB, DATE, Date, DATETIME, DateTime, DECIMAL, DOUBLE, Double, DOUBLE_PRECISION, Enum, FLOAT, Float, INT, INTEGER, Integer, Interval, JSON, LargeBinary, NCHAR, NUMERIC, Numeric, NumericCommon, NVARCHAR, PickleType, REAL, SMALLINT, SmallInteger, String, TEXT, Text, TIME, Time, TIMESTAMP, TupleType, TypeDecorator, Unicode, UnicodeText, UUID, Uuid, VARBINARY, VARCHAR.
  orm_exports_read: exc, mapperlib, strategy_options, mapper, aliased, backref, clear_mappers, column_property, composite, contains_alias, create_session, deferred, dynamic_loader, join, mapped_column, orm_insert_sentinel, outerjoin, query_expression, relationship, synonym, with_loader_criteria, with_polymorphic, AttributeEventToken, InstrumentedAttribute, QueryableAttribute, class_mapper, DynamicMapped, InspectionAttrExtensionType, LoaderCallableStatus, Mapped, NotExtension, ORMDescriptor, PassiveFlag, SQLORMExpression, WriteOnlyMapped, FromStatement, QueryContext, add_mapped_attribute, as_declarative, as_typed_table, declarative_base, declarative_mixin, DeclarativeBase, DeclarativeBaseNoMeta, DeclarativeMeta, declared_attr, has_inherited_table, mapped_as_dataclass, MappedAsDataclass, registry, synonym_for, TypeResolve, unmapped_dataclass, MappedClassProtocol, Composite, CompositeProperty, Synonym, SynonymProperty, AppenderQuery, AttributeEvents, InstanceEvents, InstrumentationEvents, MapperEvents, QueryEvents, RegistryEvents, SessionEvents, IdentityMap, ClassManager, EXT_CONTINUE, EXT_SKIP, EXT_STOP, InspectionAttr, InspectionAttrInfo, MANYTOMANY, MANYTOONE, MapperProperty, NO_KEY, NO_VALUE, ONETOMANY, PropComparator, RelationshipDirection, UserDefinedOption, merge_frozen_result, merge_result, attribute_keyed_dict, attribute_mapped_collection, column_keyed_dict, column_mapped_collection, keyfunc_mapping, KeyFuncDict, mapped_collection, MappedCollection, configure_mappers, Mapper, reconstructor, validates, ColumnProperty, MappedColumn, MappedSQLExpression, AliasOption, Query, foreign, Relationship, RelationshipProperty, remote, QueryPropertyDescriptor, scoped_session, close_all_sessions, make_transient, make_transient_to_detached, object_session, ORMExecuteState, Session, sessionmaker, SessionTransaction, SessionTransactionOrigin, AttributeState, InstanceState, contains_eager, defaultload, defer, immediateload, joinedload, lazyload, Load, load_only, noload, raiseload, selectin_polymorphic, selectinload, subqueryload, undefer, undefer_group, with_expression, UOWTransaction, Bundle, CascadeOptions, DictBundle, LoaderCriteriaOption, object_mapper, polymorphic_union, was_deleted, with_parent, WriteOnlyCollection.
  included_q1_yes_q2_non_derivable:
    - sqlalchemy.create_engine, Engine, Connection, Transaction, Result, CursorResult, Row, RowMapping, ScalarResult, MappingResult, URL, make_url, inspect, Inspector: public day-one engine/result/inspection objects with SQLAlchemy-specific transaction, row, URL, and reflection behavior.
    - sqlalchemy.MetaData, Table, Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint, CheckConstraint, Index, BLANK_SCHEMA: public day-one metadata graph objects with SQLAlchemy-specific collection, dependency, DDL, and reflection behavior.
    - sqlalchemy.Integer, String, Text, Boolean, Date, DateTime, Time, Numeric, Float, LargeBinary, JSON and uppercase SQLite-compatible type aliases INTEGER, VARCHAR, TEXT, BOOLEAN, DATE, DATETIME, TIME, NUMERIC, FLOAT, BLOB: public type objects needed to build and reflect SQLite-local schemas.
    - sqlalchemy.select, Select, insert, Insert, update, Update, delete, Delete, text, TextClause, bindparam, BindParameter, and_, or_, not_, true, false, null, literal, literal_column, column, table, func, cast, type_coerce, label, asc, desc, between, join, outerjoin: public expression constructors with SQLAlchemy-specific generative, bound-parameter, compilation, and execution behavior.
    - sqlalchemy.orm.DeclarativeBase, declarative_base, Mapped, mapped_column, relationship, Session, sessionmaker, joinedload, selectinload, lazyload, raiseload, contains_eager, Load, object_session: public ORM setup/session/loader behavior needed by documented quickstart and relationship workflows.
    - sqlalchemy.dialects.sqlite.insert, sqlalchemy.dialects.sqlite.Insert, sqlalchemy.dialects.sqlite.DATE, DATETIME, TIME, JSON, and documented SQLite uppercase types: public SQLite dialect API with SQLite-specific compilation/value behavior.
    - sqlalchemy.exc.SQLAlchemyError, ArgumentError, InvalidRequestError, NoResultFound, MultipleResultsFound, StatementError, DBAPIError, IntegrityError, OperationalError, NoSuchTableError, NoReferencedTableError, NoReferencedColumnError, NoForeignKeysError, AmbiguousForeignKeysError and sqlalchemy.orm.exc.DetachedInstanceError, FlushError, UnmappedClassError, UnmappedInstanceError: public exception classes needed to describe user-visible failures.
  excluded_q1_no_for_this_scoped_packet_q2_omit_each_export:
    - sqlalchemy engine/pool advanced exports: AdaptedConnection, BaseRow, BindTyping, ChunkedIteratorResult, Compiled, create_mock_engine, create_pool_from_url, CreateEnginePlugin, Dialect, engine_from_config, ExceptionContext, ExecutionContext, FrozenResult, IteratorResult, MergedResult, NestedTransaction, result_tuple, ResultProxy, RootTransaction, TwoPhaseTransaction, TypeCompiler, AssertionPool, AsyncAdaptedQueuePool, NullPool, Pool, PoolProxiedConnection, PoolResetState, QueuePool, SingletonThreadPool, StaticPool.
    - sqlalchemy schema advanced exports: BaseDDLElement, CheckFirst, ColumnDefault, Computed, Constraint, CreateTable, CreateTableAs, CreateView, DDL, DDLElement, DefaultClause, DropTable, DropView, ExecutableDDLElement, FetchedValue, Identity, insert_sentinel, Named, Sequence, TypedColumns.
    - sqlalchemy expression advanced exports: ColumnExpressionArgument, NotNullable, Nullable, SelectLabelStyle, aggregate_order_by, AggregateOrderBy, Alias, alias, AliasedReturnsRows, all_, any_, BinaryExpression, bitwise_not, BooleanClauseList, CacheKey, Case, case, Cast, ClauseElement, ClauseList, collate, CollectionAggregate, ColumnClause, ColumnCollection, ColumnElement, ColumnOperators, CompoundSelect, CTE, cte, custom_op, distinct, except_, except_all, Executable, Exists, exists, Extract, extract, False_, FrameClause, FrameClauseType, from_dml_column, FromClause, FromGrouping, funcfilter, Function, FunctionElement, FunctionFilter, GenerativeSelect, Grouping, HasCTE, HasPrefixes, HasSuffixes, intersect, intersect_all, Join, Label, LABEL_STYLE_DEFAULT, LABEL_STYLE_DISAMBIGUATE_ONLY, LABEL_STYLE_NONE, LABEL_STYLE_TABLENAME_PLUS_COL, lambda_stmt, LambdaElement, Lateral, lateral, modifier, Null, nulls_first, nulls_last, nullsfirst, nullslast, Operators, OrderByList, outparam, Over, over, quoted_name, ReleaseSavepointClause, ReturnsRows, RollbackToSavepointClause, SavepointClause, ScalarSelect, Selectable, SelectBase, SQLColumnExpression, StatementLambdaElement, Subquery, TableClause, TableSample, tablesample, TableValuedAlias, TableValuedColumn, TextAsFrom, TextualSelect, True_, try_cast, TryCast, TString, tstring, Tuple, tuple_, TypeClause, TypeCoerce, UnaryExpression, union, union_all, UpdateBase, Values, values, ValuesBase, Visitable, within_group, WithinGroup.
    - sqlalchemy type-system advanced exports: ARRAY, BIGINT, BigInteger, BINARY, CHAR, CLOB, DECIMAL, DOUBLE, Double, DOUBLE_PRECISION, Enum, Interval, NCHAR, NVARCHAR, PickleType, REAL, SMALLINT, SmallInteger, TupleType, TypeDecorator, Unicode, UnicodeText, UUID, Uuid, VARBINARY.
    - sqlalchemy.orm advanced configuration/query/event/collection exports: exc, mapperlib, strategy_options, mapper, aliased, backref, clear_mappers, column_property, composite, contains_alias, create_session, deferred, dynamic_loader, join, orm_insert_sentinel, outerjoin, query_expression, synonym, with_loader_criteria, with_polymorphic, AttributeEventToken, InstrumentedAttribute, QueryableAttribute, class_mapper, DynamicMapped, InspectionAttrExtensionType, LoaderCallableStatus, NotExtension, ORMDescriptor, PassiveFlag, SQLORMExpression, WriteOnlyMapped, FromStatement, QueryContext, add_mapped_attribute, as_declarative, as_typed_table, declarative_mixin, DeclarativeBaseNoMeta, DeclarativeMeta, declared_attr, has_inherited_table, mapped_as_dataclass, MappedAsDataclass, registry, synonym_for, TypeResolve, unmapped_dataclass, MappedClassProtocol, Composite, CompositeProperty, Synonym, SynonymProperty, AppenderQuery, AttributeEvents, InstanceEvents, InstrumentationEvents, MapperEvents, QueryEvents, RegistryEvents, SessionEvents, IdentityMap, ClassManager, EXT_CONTINUE, EXT_SKIP, EXT_STOP, InspectionAttr, InspectionAttrInfo, MANYTOMANY, MANYTOONE, MapperProperty, NO_KEY, NO_VALUE, ONETOMANY, PropComparator, RelationshipDirection, UserDefinedOption, merge_frozen_result, merge_result, attribute_keyed_dict, attribute_mapped_collection, column_keyed_dict, column_mapped_collection, keyfunc_mapping, KeyFuncDict, mapped_collection, MappedCollection, configure_mappers, Mapper, reconstructor, validates, ColumnProperty, MappedColumn, MappedSQLExpression, AliasOption, Query, foreign, Relationship, RelationshipProperty, remote, QueryPropertyDescriptor, scoped_session, close_all_sessions, make_transient, make_transient_to_detached, ORMExecuteState, SessionTransaction, SessionTransactionOrigin, AttributeState, InstanceState, defaultload, defer, immediateload, load_only, noload, selectin_polymorphic, subqueryload, undefer, undefer_group, with_expression, UOWTransaction, Bundle, CascadeOptions, DictBundle, LoaderCriteriaOption, object_mapper, polymorphic_union, was_deleted, with_parent, WriteOnlyCollection.
  q2_derivable_or_constructor-produced_mentions:
    - Result object classes, statement classes, expression classes, and loader option classes are mostly produced by public functions; the candidate-visible spec names only their user-visible methods/behaviors where needed.
    - SQL formatting whitespace, anonymous label counters beyond stable public access behavior, and exact repr strings are derivable or implementation-specific and are excluded.
-->

# SQLAlchemy Specification

## Product Overview

SQLAlchemy is a Python SQL toolkit and Object Relational Mapper. It has two closely related layers:

- Core provides database connectivity, transaction management, schema metadata, SQL expression construction, SQL compilation, and result handling.
- ORM builds on Core to map Python classes to database tables, track object identity and changes in a `Session`, and load related objects through relationship attributes.

The Core and ORM share the same SQL expression system. A `select()` statement can be executed by a Core `Connection` or by an ORM `Session`; the difference is whether the selected objects are table/column constructs or ORM mapped entities.

## Scope

This specification covers the SQLite-local, day-one public contract:

- Core `Engine`, `Connection`, transactions, `Result`, `Row`, and bound-parameter execution.
- `MetaData`, `Table`, `Column`, common constraints, common SQL types, DDL creation/drop, and table reflection.
- SQL expression construction for `select()`, `insert()`, `update()`, `delete()`, `text()`, boolean expressions, joins, labels, functions, casts, and compilation.
- SQLite execution behavior using the standard `sqlite3` DBAPI through `sqlite://`, `sqlite:///:memory:`, and `sqlite:///path.db` URLs.
- ORM declarative mappings using `DeclarativeBase`, `Mapped`, `mapped_column()`, `relationship()`, `Session`, and `sessionmaker`.
- ORM unit-of-work basics: add, flush, commit, rollback, delete, identity map, expiration, and query execution with `select()`.
- Relationship synchronization and basic loading strategies: lazy loading, `selectinload()`, `joinedload()`, `lazyload()`, `raiseload()`, and `contains_eager()`.
- SQLite dialect basics: SQLite type names, date/time/JSON value behavior, and SQLite-specific `insert()` with conflict handling.

## Installable Surface

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

## Public API

### Engine and Execution

```python
create_engine(url, **kwargs) -> Engine
```

`create_engine()` accepts a database URL string or `URL` object and returns an `Engine`. The engine does not open a DBAPI connection until the first operation that needs one, such as `Engine.connect()`, `Engine.begin()`, ORM `Session` use, or schema creation. `echo=True` logs SQL through SQLAlchemy's logging integration.

SQLite URL forms are part of the public contract:

- `sqlite://` creates an in-memory SQLite database using the default SQLite DBAPI.
- `sqlite:///:memory:` explicitly uses SQLite's `:memory:` database.
- `sqlite:///relative.db` uses a relative file path.
- `sqlite:////absolute/path.db` uses an absolute Unix-style path.
- `sqlite:///C:\path\to\file.db` is accepted for Windows paths.
- `sqlite+pysqlite://...` explicitly names the built-in pysqlite/sqlite3 driver.

`Engine.connect()` returns a `Connection` context manager. Executing through a connection begins an implicit DBAPI transaction when work first occurs. Exiting a `connect()` block without committing rolls back. `Connection.commit()` commits current work and allows later work in the same connection block to begin a new transaction.

`Engine.begin()` returns a context manager that provides a `Connection` and commits on successful block exit or rolls back when an exception leaves the block.

```python
Connection.execute(statement, parameters=None) -> Result
Connection.scalar(statement, parameters=None) -> object
Connection.commit() -> None
Connection.rollback() -> None
```

`parameters` may be one dictionary for a single execution or a list of dictionaries for executemany. Textual SQL parameters use SQLAlchemy's named colon form, such as `text("select * from t where id=:id")`; the SQLite dialect adapts these to the DBAPI's qmark parameter style when sending SQL to SQLite.

`Result` is iterable and yields `Row` objects. `Result.all()` returns all remaining rows as a list. `Result.first()` returns the first row or `None`. `Result.one()` requires exactly one row. `Result.scalar()` returns the first column of the first row or `None`. `Result.scalars()` returns a `ScalarResult` over the first selected element of each row. `Result.mappings()` returns mapping rows whose keys are column names, labels, or ORM entity names where applicable.

`Row` behaves like a named tuple for positional unpacking and integer indexing. It also exposes column names as attributes when those names are present and unambiguous. Mapping-style access is available from `row._mapping` and from rows produced by `Result.mappings()`.

### Metadata, Tables, Columns, and Types

```python
MetaData(schema=None, naming_convention=None, info=None)
Table(name, metadata, *columns, schema=None, autoload_with=None, extend_existing=False, keep_existing=False, **dialect_options)
Column(name=None, type_=None, *constraints, primary_key=False, nullable=None, default=None, server_default=None, index=None, unique=None, key=None, autoincrement="auto", **dialect_options)
ForeignKey(column, onupdate=None, ondelete=None, name=None, use_alter=False, link_to_name=False, **dialect_options)
```

`MetaData` is a collection of schema constructs. `MetaData.tables` is keyed by table name, or by schema-qualified table name when a table has a schema. `MetaData.sorted_tables` returns tables ordered so referenced tables precede dependent tables.

`Table` represents a database table and attaches itself to a `MetaData` collection. A table's columns are available through `table.c` and `table.columns`. The column collection supports attribute access for ordinary names, indexed access for all names, tuple indexed access for multiple names, iteration in declaration order, and `keys()`.

`Column` represents a database column. The common user-visible attributes are `name`, `key`, `type`, `nullable`, `primary_key`, `foreign_keys`, and `table`. `key` defaults to `name` and controls Python-side lookup when set explicitly. A column with `primary_key=True` participates in the table's primary key and is treated as non-nullable unless explicitly overridden by supported dialect behavior. A `ForeignKey("other_table.id")` can infer the local column type from the referenced column when no local type is given.

Common type classes and aliases include `Integer`, `String(length=None)`, `Text`, `Boolean`, `Date`, `DateTime`, `Time`, `Numeric`, `Float`, `LargeBinary`, and `JSON`. Type classes may be passed either as classes or instances in normal column declarations. `String(30)` carries a length for DDL and SQL compilation.

`MetaData.create_all(engine_or_connection)` emits DDL for all contained tables that are not already present. Tables are created in dependency order based on foreign keys. `MetaData.drop_all(engine_or_connection)` drops tables in reverse dependency order. `Table.create()` and `Table.drop()` operate on a single table; `checkfirst=True` asks SQLAlchemy to check for existence first.

Constraints may be declared through column flags or explicit objects. `PrimaryKeyConstraint`, `ForeignKeyConstraint`, `UniqueConstraint`, `CheckConstraint`, and `Index` are associated with tables and participate in DDL generation and reflection where SQLite can report them.

### Reflection and Inspection

`Table(name, metadata, autoload_with=engine_or_connection)` reflects an existing table into Python metadata by reading database schema information. The reflected `Table` is usable like an explicitly declared table: it has `c`, `columns`, `primary_key`, `foreign_keys`, and column type/nullability information.

`inspect(engine_or_connection)` returns an `Inspector`. In this scope, the inspector exposes basic SQLite schema information such as table names, column dictionaries, primary key information, foreign keys, indexes, and unique constraints when available from SQLite.

Reflecting a missing table raises `sqlalchemy.exc.NoSuchTableError`. A foreign key string that cannot locate its target table or target column raises `NoReferencedTableError` or `NoReferencedColumnError` when the reference is resolved.

### SQL Expressions and Compilation

```python
select(*entities) -> Select
insert(table) -> Insert
update(table) -> Update
delete(table) -> Delete
text(sql_text) -> TextClause
bindparam(key, value=None, type_=None, unique=False, required=None, expanding=False, literal_execute=False)
```

SQLAlchemy expressions are composable Python objects. Calling `str(statement)` or `statement.compile(...)` produces SQL text and bound parameter state without executing the statement.

`select()` accepts tables, columns, SQL expressions, and ORM entities. Selecting a `Table` expands to its columns. Selecting columns infers a `FROM` clause from the tables represented by those columns. Selecting an ORM class returns ORM instances when executed through `Session`.

`Select` is generative: methods such as `.where()`, `.filter_by()`, `.join()`, `.join_from()`, `.outerjoin()`, `.select_from()`, `.order_by()`, `.group_by()`, `.limit()`, `.offset()`, `.options()`, and `.execution_options()` return a new statement with the added behavior while preserving the earlier statement.

Column comparisons such as `table.c.name == "sandy"`, `!=`, `<`, `<=`, `>`, `>=`, `.like()`, `.in_()`, `.is_(None)`, and `.is_not(None)` produce SQL boolean expressions rather than Python booleans. Python literals in expressions become bound parameters unless the API explicitly represents literal SQL text.

Multiple criteria passed to `.where()` or produced by repeated `.where()` calls are joined with SQL `AND`. `and_()`, `or_()`, and `not_()` build explicit boolean combinations. `true()`, `false()`, and `null()` represent SQL constants.

`text()` represents literal SQL text and may be executed directly. Its parameter style is SQLAlchemy named colon syntax. `literal_column()` represents a textual SQL column expression. `literal()` represents a Python value as a SQL bound value. `bindparam()` creates an explicitly named bound parameter that can be reused in statements and filled at execution time.

`func.<name>(...)` creates a SQL function call for arbitrary function names. Common functions such as `count()` have useful SQLAlchemy return types. Unknown functions are still rendered by name and may have a null/unknown SQL type unless `type_=` is supplied.

`cast(expression, type_)` renders SQL `CAST` and gives the expression SQLAlchemy type behavior. `type_coerce(expression, type_)` gives SQLAlchemy type behavior without rendering a SQL `CAST`.

`ColumnElement.label(name)` and `label(name, expression)` assign result-column names. Labels are available on returned rows by the label name when unambiguous.

`Select.join(target)` and `Select.join_from(left, right, onclause=None)` add JOINs. With table metadata, SQLAlchemy can infer an ON clause from one unambiguous foreign key path. With ORM relationship attributes, passing the relationship to `.join()` supplies both the target and the ON clause.

Compiling for SQLite uses SQLite identifier quoting, parameter style, type names, and dialect features. The exact whitespace of SQL strings is not part of the contract; the SQL structure, selected columns, FROM/JOIN/WHERE semantics, parameter binding, and result behavior are.

### DML

`insert(table)` creates an `Insert`. `.values()` supplies values, `.returning()` asks for returned columns where the dialect supports it, and execution with a list of parameter dictionaries performs executemany. For SQLite versions that support it, SQLAlchemy may use SQLite `RETURNING`; otherwise callers should not rely on `RETURNING` for portability.

`update(table)` creates an `Update`. `.where()` filters rows and `.values()` supplies new values.

`delete(table)` creates a `Delete`. `.where()` filters rows.

Executed DML returns a `CursorResult`. The result exposes DBAPI-derived rowcount and inserted primary key information where the backend can provide it.

### ORM Declarative Mapping

```python
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
```

`DeclarativeBase` is subclassed to create a base class for mapped models. The base has a `metadata` collection and a `registry`. Subclasses with `__tablename__` and mapped attributes are configured as ORM mapped classes at class creation time. Each mapped class receives a `__table__` referring to the generated `Table`.

`declarative_base()` is the function form for creating a declarative base and remains supported.

`Mapped[T]` marks ORM mapped attributes for typing and declarative configuration. `mapped_column()` declares a table column in a declarative class. If no explicit SQLAlchemy type is supplied, common Python annotations infer common SQL types, such as `int` to `Integer` and `str` to `String`. Optional annotations such as `Optional[str]` or `str | None` imply nullable columns unless `nullable=` is explicitly supplied. Every mapped class must have a primary key mapping.

Declarative mapped classes receive a default `__init__()` when they do not define one. The default initializer accepts mapped attribute names as optional keyword arguments, including relationship attributes.

Mapped class attributes are SQL expression objects at the class level and ordinary instrumented attributes at the instance level. `select(User)` selects ORM entities. `select(User.name, User.fullname)` selects individual column values.

### Session and Unit of Work

```python
Session(bind=None, *, autoflush=True, expire_on_commit=True, autobegin=True, **kwargs)
sessionmaker(bind=None, class_=Session, autoflush=True, expire_on_commit=True, **kwargs)
```

`Session` is the ORM's database conversation object. It is mutable, stateful, and represents one logical transaction at a time. It should not be shared concurrently across threads or asyncio tasks.

`Session(engine)` binds a session to an engine. `with Session(engine) as session:` closes the session at block exit. `sessionmaker(engine)` creates a reusable factory. `with Session.begin() as session:` from a sessionmaker opens a session and transaction, committing on success and rolling back on exception.

The session maintains an identity map: within one session, rows with the same mapped class and primary key resolve to the same Python object. `Session.get(Entity, primary_key)` first checks the identity map and queries the database if needed. Composite primary keys may be passed as tuples or dictionaries.

`Session.add(obj)` places a transient or detached instance into the session. `Session.add_all([...])` adds several instances. New instances become pending and are INSERTed on flush. Already persistent instances do not need to be added again.

`Session.flush()` writes pending INSERT, UPDATE, and DELETE statements to the database transaction without committing it. With default autoflush, flush occurs before ORM-enabled `Session.execute()` calls, before lazy loads, before refresh operations, and inside `Session.commit()`. `Session.no_autoflush` temporarily suppresses autoflush, but commit still flushes pending changes.

`Session.commit()` flushes pending changes, commits the database transaction, releases the connection, and by default expires all persistent objects so later attribute access refreshes them in a new transaction. `expire_on_commit=False` disables that expiration behavior.

`Session.rollback()` rolls back the current transaction if one exists, releases connections, expunges pending objects whose INSERT was rolled back, restores deleted objects to persistent state when appropriate, and expires remaining persistent objects.

`Session.close()` expunges all ORM objects and releases transactional resources. By default a closed session is reset and may be reused.

`Session.execute(statement, parameters=None)` executes Core or ORM statements and returns `Result`. `Session.scalars(statement, parameters=None)` returns a `ScalarResult` over the first selected element. `ScalarResult.one()` raises `NoResultFound` for no rows and `MultipleResultsFound` for more than one row.

`Session.delete(obj)` marks a persistent object for DELETE on the next flush. Related rows are not deleted by default merely because a relationship exists; relationship cascade options control delete and delete-orphan behavior.

### Relationships and Loading

```python
relationship(argument=None, secondary=None, *, back_populates=None, cascade="save-update, merge", lazy="select", uselist=None, collection_class=None, order_by=False, passive_deletes=False, **kwargs)
```

`relationship()` links mapped classes. For simple relationships, SQLAlchemy infers direction and join conditions from foreign keys in the mapped tables. `back_populates` names the complementary relationship and makes in-memory assignment synchronize both sides.

For a one-to-many collection relationship, a new instance exposes an empty collection before anything is assigned. Appending a related object to the collection updates the reverse scalar relationship when `back_populates` is configured. Assigning the scalar relationship likewise places the object in the reverse collection.

The default cascade includes `save-update`, so adding a parent object to a session also adds transient related objects reachable through normal relationships. On flush, the unit of work orders INSERTs so parent primary keys are available for dependent foreign keys.

Relationships are lazy-loaded by default with `lazy="select"`. Accessing an unloaded collection or scalar relationship emits a SELECT using the current session and then stores the loaded value in memory. Re-accessing the loaded relationship does not emit SQL until it is expired. For simple many-to-one relationships, lazy loading can resolve from the identity map without SQL when the target object is already present.

`selectinload(Entity.rel)` configures eager loading that emits a second SELECT using parent primary key values in an IN expression. It is the preferred eager strategy for most one-to-many collections. It loads only relationships not already populated.

`joinedload(Entity.rel, innerjoin=False)` configures eager loading by adding a JOIN dedicated to population of the relationship. This loader must not change which primary entities the query returns. For collection joined eager loads, callers use `Result.unique()` or `ScalarResult.unique()` before consuming all objects so duplicate primary rows produced by the SQL JOIN are collapsed into unique ORM instances.

`lazyload(Entity.rel)` forces lazy loading for a relationship on a particular statement.

`raiseload(Entity.rel)` or `relationship(lazy="raise_on_sql")` replaces a lazy load with `InvalidRequestError` when access would emit SQL. `raise_on_sql` may still allow access that can be satisfied from the identity map without SQL. Raiseload does not prevent internal loads that the unit of work needs during flush.

`contains_eager(Entity.rel)` tells the ORM that an explicit join already present in the statement should be used to populate the relationship. The option path must match the joined relationship path. When using a custom filtered join to populate an already-loaded collection differently, `execution_options(populate_existing=True)` refreshes existing in-memory state.

### SQLite Dialect Behavior

SQLite is available without an external database server through Python's standard `sqlite3` DBAPI. In-memory SQLite databases are per DBAPI connection unless the selected pool/connection strategy preserves one connection.

SQLite DDL uses SQLite type names and SQLite reflection pragmas. `MetaData.create_all()` checks table presence before creating tables. Reflection reads table columns, primary keys, foreign keys, indexes, and unique constraints to the extent SQLite exposes them.

The SQLite dialect exports uppercase type names such as `INTEGER`, `VARCHAR`, `TEXT`, `BOOLEAN`, `DATE`, `DATETIME`, `TIME`, `NUMERIC`, `FLOAT`, and `BLOB`. SQLite date/time types store values in SQLite-compatible textual forms and convert back to Python `date`, `datetime`, or `time` objects when SQLAlchemy type processing is in effect.

SQLite `JSON` provides SQLAlchemy JSON expression behavior on SQLite. SQLite itself stores JSON values according to SQLite capabilities; SQLAlchemy handles Python-side JSON bind/result processing and JSON path expression compilation for supported SQLite JSON functions.

`sqlalchemy.dialects.sqlite.insert(table)` creates a SQLite-specific `Insert`. It supports SQLite ON CONFLICT helpers:

```python
sqlite_insert(table).on_conflict_do_nothing(index_elements=None, index_where=None)
sqlite_insert(table).on_conflict_do_update(index_elements=None, index_where=None, set_=..., where=None)
```

`on_conflict_do_nothing()` renders an INSERT that skips rows conflicting with the chosen unique constraint or index target. `on_conflict_do_update()` renders an INSERT that updates columns for conflicting rows. The SQLite `Insert.excluded` namespace refers to values proposed for insertion inside the conflict update clause.

## Error Semantics

`sqlalchemy.exc.SQLAlchemyError` is the common base class for SQLAlchemy-raised exceptions.

`ArgumentError` is raised for invalid API construction arguments, such as inconsistent mapping or expression configuration.

`InvalidRequestError` is raised when an API call is not valid for the current object state, such as using `raiseload` and then accessing a relationship that would need SQL.

`NoResultFound` is raised by `.one()` or scalar-one style result methods when no row is present. `MultipleResultsFound` is raised when exactly one row was required but multiple rows are present.

`StatementError` wraps errors that occur while executing a statement and carries statement/parameter context. `DBAPIError` is the base for wrapped DBAPI exceptions. `IntegrityError`, `OperationalError`, and related database error subclasses correspond to DBAPI error categories.

`NoSuchTableError` is raised when reflecting or inspecting a table that does not exist.

`NoReferencedTableError` and `NoReferencedColumnError` are raised when a foreign key target table or column cannot be resolved.

`NoForeignKeysError` is raised when SQLAlchemy is asked to infer a join path but no foreign key relationship exists. `AmbiguousForeignKeysError` is raised when more than one foreign key path exists and no explicit join condition disambiguates it.

`orm_exc.DetachedInstanceError` is raised when an unloaded or expired ORM attribute needs a session but the object is detached.

`orm_exc.FlushError` is raised for ORM flush problems that SQLAlchemy can identify before or during unit-of-work processing. Database constraint violations during flush are typically surfaced as DBAPI-derived exceptions such as `IntegrityError`, and the session must be rolled back before normal use continues.

`orm_exc.UnmappedClassError` and `orm_exc.UnmappedInstanceError` are raised when ORM operations receive classes or instances that are not mapped.

## Cross-View Invariants

1. A `Table` declared in `MetaData` and the SQL generated from it describe the same table name, column names, primary key, nullable flags, and foreign key relationships.
2. A `Column` reached through `table.c.name`, selected with `select(table.c.name)`, returned through a row attribute, and reflected back from SQLite refers to the same user-visible column key unless an explicit label or key changes that view.
3. Python literal values in expression comparisons and textual parameters are sent as bound parameters during execution; the values are not interpolated into SQL text by ordinary expression construction.
4. Core execution and ORM session execution share the same transaction rule: database work occurs inside a transaction that is committed explicitly or rolled back when the scope exits without commit.
5. A row inserted through Core DML and later queried through an ORM mapping over the same table produces an ORM object with attributes matching the stored column values.
6. Within a single `Session`, two queries that load the same mapped class and primary key return the same Python object identity.
7. A flush writes pending ORM changes to the database transaction, but another transaction should not rely on those changes being durable until commit succeeds.
8. Relationship `back_populates` keeps both Python-side directions synchronized before and after persistence.
9. Loader strategies may change how many SQL statements are emitted, but they do not change the set of primary ORM objects a statement is meant to return.
10. Reflection produces metadata objects that can be used by the same SQL expression and execution APIs as explicitly declared metadata.

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

## Non-Goals

- Reproducing SQLAlchemy's internal module layout, helper classes, cache keys, visitor internals, compiler internals, or private attributes.
- Reproducing `sqlalchemy.testing`, upstream test fixtures, pytest plugin behavior, or test-suite convenience APIs.
- Matching exact object `repr()` strings, anonymous alias numbering beyond user-visible SQL semantics, logging line formatting, or SQL whitespace.
- Implementing every SQLAlchemy public export. Advanced Core constructs such as CTEs, lateral joins, table-valued functions, lambda statements, `CreateView`, `CreateTableAs`, custom operators, and set operations are outside this scope.
- Implementing database-server dialects such as PostgreSQL, MySQL, Oracle, or SQL Server, or optional third-party DBAPI integrations.
- Implementing asyncio APIs, greenlet behavior, connection pool tuning, engine plugins, event dispatch APIs, and low-level DBAPI adaptation.
- Implementing advanced ORM topics such as inheritance mapping, polymorphic loading, dataclass mappings, composites, synonyms, association proxies, scoped sessions, dynamic/write-only relationships, custom collections, mapper/session events, merge/frozen result helpers, and legacy `Query` coverage.
- Implementing Alembic migrations or long-term schema migration workflows.
- Guaranteeing SQLite behavior that depends on unavailable SQLite library features; when SQLite itself rejects unsupported SQL, SQLAlchemy may surface the DBAPI-derived error.

## Evaluation Notes

Evaluation should exercise public behavior through documented imports and ordinary user workflows. Tests should create SQLite-local engines, define metadata and declarative models, execute Core and ORM statements, inspect returned rows and objects, reflect simple schemas, and verify relationship loading behavior through public APIs.

Scoring should reward semantic compatibility rather than internal fidelity. SQL text may be checked for structural clauses, identifiers, and bound parameter behavior, but exact whitespace, private names, logging text, and internal reprs should not be used as pass/fail criteria.

Tests should cover successful workflows and representative error cases: missing reflected tables, ambiguous or missing foreign-key joins, result cardinality errors, detached lazy loads, raiseload access, and database constraint failures. They should not import `sqlalchemy.testing`, private modules, or upstream-only fixture helpers.

The SQLite dialect is the execution target for this packet. Tests should avoid requiring external database servers, optional drivers, async APIs, or dialect features not exposed by the standard Python SQLite environment.
