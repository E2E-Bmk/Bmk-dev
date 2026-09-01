<!-- SPEC.md -->
# SQLAlchemy Core and ORM specification

## Scope

Implement the documented synchronous SQLAlchemy Core and ORM behavior described
here over the standard-library SQLite driver.  The covered surface is the public
package, Core schema/expression/execution API, declarative ORM, sessions,
relationships, loader options, and public event registration.  Network databases,
async drivers, migrations, query plans, timing, concurrency, private dialect or
compiler state, private mapper or unit-of-work state, pool internals, and exact SQL
or diagnostic prose are outside scope.

All workflows use a fresh database.  A one-connection workflow may use
`sqlite:///:memory:`.  Independent connection/session visibility uses a fresh file
database, explicit transactions, and independent public connections.  Outcomes are
compared through public inspection, returned values and exceptions, and ordered
database rows—not SQLite file bytes or implementation internals.

## Public owners and declarations

Documented imports for engine creation, inspection, events, Core constructs, ORM
sessions/mappings/loaders, and the public SQLite `insert` constructor must resolve
without importing private modules.

`MetaData` owns tables in a public keyed collection preserving declaration order.
A `Table` preserves its declared name and ordered column collection; iteration,
keys, and attribute/key lookup identify the same columns.  A representative integer
primary-key column is primary and non-nullable with no invented client or server
default.  A `ForeignKey` exposes its target fullname and resolves to the declared
target column once the metadata graph is complete.

Named primary-key, foreign-key, unique, check, and index constructs attach to the
intended public tables and columns.  Foreign-key dependencies place a referenced
table before its dependent in `MetaData.sorted_tables`.

Annotated declarative mappings project class properties onto the same public
`Table` and `MetaData`.  Required annotations are non-nullable and optional
annotations nullable.  Public mapper inspection, mapped attributes, table keys,
types, primary keys, and nullability describe one mapping.  A paired
`relationship(..., back_populates=...)` exposes a collection direction on the
one-to-many endpoint and a scalar direction on the many-to-one endpoint.

## Schema creation, inspection, and reflection

Metadata-wide creation creates the declared SQLite tables and columns.  Public
inspection reports their names, types, nullability, and the admitted named primary,
foreign, unique, check, and index facts.  Metadata-wide removal removes them.
Conditional `Table.create(..., checkfirst=True)` is idempotent and preserves
existing rows.

Reflection reconstructs operational public tables, columns, and foreign-key
targets.  An unambiguous reflected relationship supports inferred joins.  A
reflected table supports insert, select, update, and delete against the original
physical table.

An unresolved foreign-key table graph raises `NoReferencedTableError` without
leaving a partial wrong schema in a fresh database.  A corrected metadata graph may
then create and use its intended schema.

## Expressions, compilation, and results

Column comparison constructs a Boolean SQL expression with the column as its left
owner and the Python value retained as bound parameter data.  Statement modifiers
are generative: a derived where/order/limit/offset statement does not mutate the
earlier selection.

Bound values remain in compiled parameter state and are represented structurally;
they are not interpolated into SQL text.  The same law applies to named parameters
on `text`.  Exact placeholder spelling, whitespace, quoting, aliases, and generated
SQL text are not compatibility requirements.

Public functions, casts, type coercion, and labels compose.  When an explicit
public result type is supplied to a function it is retained, and labels remain the
mapping keys of executed results.  Date, time, datetime, JSON, binary, numeric,
float, string, integer, Boolean, and null type owners construct and participate in
SQLite-compatible round trips.

A returned `Row` exposes one selected value consistently by position, supported
attribute access, and `row._mapping`.  Mapping projections preserve public key and
value order.  Scalar, mapping, and row projections made from equivalent fresh
results agree while respecting normal stream consumption.

Empty `first()` and scalar access return `None`.  `scalar_one()` returns the one
value for exactly one row, raises `NoResultFound` for zero rows, and raises
`MultipleResultsFound` for multiple rows.

## Core execution and DML

Executing compiled or textual statements uses bound values as data, including
strings containing quotes and SQL-looking text.  Public Boolean, null, membership,
range, and pattern predicates filter deterministic rows according to SQLite
semantics.  Function/cast/type-coercion expressions retain their label and converted
result through execution.

An inferred join follows one unambiguous foreign-key path.  Missing and ambiguous
paths raise `NoForeignKeysError` and `AmbiguousForeignKeysError`, respectively.  An
explicit corrected condition then joins the intended rows without data mutation
from the failed construction.

Executemany insert preserves each record's field-to-column identity, and ordered
mapping results expose the same values.  On the supplied SQLite runtime, a normal
insert exposes its inserted primary key; public `INSERT ... RETURNING` returns the
requested inserted row; representative update and delete operations report one
affected row; and durable selected rows agree with all of those results.

The public SQLite insert conflict API supports a representative unique-key
workflow.  Do-nothing keeps the existing row.  Do-update changes the selected
columns when its public condition holds, without replacing the existing identity.

Numeric values return as `Decimal`; floats, dates, times, datetimes, bytes, nested
JSON values, strings, integers, Booleans, and null return with their corresponding
public Python semantic values.

## Connections and transactions

Leaving an `Engine.connect()` context without committing rolls back its pending
work.  A later independent connection sees no such row.  `Engine.begin()` commits
on normal completion and rolls back when its body raises.

`Connection.begin_nested()` provides the admitted savepoint surface.  Rolling back
the nested transaction discards inner changes while the outer transaction remains
usable and can commit its own before/after changes.

After a public `IntegrityError` in an explicit connection transaction, rolling back
that transaction permits reuse of the same `Connection`.  Corrected work in a new
transaction commits once and contains no failed duplicate.

For a file SQLite engine using independent connections, an observer sees no
uncommitted insert and sees it after commit.  This result depends only on explicit
boundaries, never sleeps, locks, races, or pool-private identity.

## Sessions, identity, and durability

Adding and committing a mapped object assigns its durable database identity.
`Session.get` returns the session-owned identity instance for an existing key and
`None` for a missing key, including the public tuple form for a composite primary
key.  A missing lookup does not add a pending object.  `object_session` reports the
owning session for the managed instance.

A `sessionmaker.begin()` context commits on success and rolls back on exception.
Closing a session ends that object conversation but leaves engine-level committed
rows durable; a new session loads a new managed Python instance for the same key.

Pending ORM work is hidden from an ORM selection inside `Session.no_autoflush` and
becomes visible to the normal ORM selection after autoflush.  Flush alone is not a
commit: an independent connection does not see the row before commit and does see it
afterward.

An integrity failure during flush makes the session inactive.  `Session.rollback()`
restores the same session to active use.  Corrected input can then commit once, and
durable rows contain the original and corrected values but no failed duplicate.

After `Session.delete`, a persistent object is not yet in the public deleted state
before flush; it is deleted after flush.  With an open `expire_on_commit=False`
session, the object remains publicly deleted rather than detached after
commit, while Core sees no durable row.

With expiration on commit enabled, committed attributes are expired.  A later
committed Core update is observed when the ORM attribute is refreshed through
normal public access.

Core and ORM share table identity and durable state.  ORM materializes a Core-
inserted row with its converted value.  An ORM-committed update is the same key and
value selected through both the declared and reflected Core tables.

## Relationships and loaders

Bidirectional assignment keeps parent and child views coherent.  Cascade
persistence inserts both endpoints and child foreign keys pointing to the durable
parent identity.

`selectinload` and `joinedload` return the same parent/child graph and reuse the
session's identity instances.  A joined eager load of a collection requires the
public `Result.unique()` step; omitting it raises `InvalidRequestError`.

Normal lazy many-to-one access may resolve to the already managed parent identity.
Explicit `raiseload` access raises `InvalidRequestError`.  Lazy access from a
detached instance raises `DetachedInstanceError`.  Loading the same identity again
in a valid session restores relationship access.

An explicit filtered join combined with `contains_eager` populates only the
relationship members represented by the joined rows, and those members are the
same instances held by the session identity map.

## Public event lifecycle and correction

An instance-level Core `before_cursor_execute` listener runs before the matching
`after_cursor_execute` listener and does not change the statement's result.  Public
removal stops later callbacks.  A listener-raised exception propagates; after
rollback where a transaction was begun, removing the listener permits corrected
execution on the same public connection.

An instance-level session `before_flush` listener may propagate a controlled
failure before rows are written.  `Session.rollback()`, public listener removal,
input correction, and re-adding the graph permit one successful flush/commit.  A
subsequent ORM eager load, reflected Core join, durable parent/child rows, and the
single corrected flush observation all agree, with no residue from the failed
attempt.

## Compatibility boundaries

Compatibility is determined only by the public observations above.  Do not depend
on private attributes other than documented `Row._mapping`, generated SQL spelling,
raw SQLite storage, database file bytes, global listener residue, current time,
locale, randomness, network services, threads, sleeps, or performance.
