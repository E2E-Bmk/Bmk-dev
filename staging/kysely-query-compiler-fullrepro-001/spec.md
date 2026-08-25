# kysely Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`kysely` is a SQL query building and compilation library for TypeScript and JavaScript. A caller composes a query through an immutable fluent builder API — selections, joins, filters, mutations, common table expressions, set operations, raw fragments, and schema definition statements — and the library compiles that single query definition into dialect-specific SQL text plus a bound parameter list. Three engine dialects are built in (PostgreSQL, MySQL, SQLite), each with its own identifier quoting and placeholder style, and every query definition compiles under any of them.

Compilation is fully decoupled from execution. A dialect is assembled from four components — an adapter, a driver, a query compiler, and an introspector — and the built-in `DummyDriver` lets an application compile and "execute" queries with no database at all, which makes the compiled-SQL contract directly observable. Plugins transform queries before compilation: the bundled `CamelCasePlugin` maps camelCase identifiers in the API to snake_case identifiers in SQL, and `withSchema` scopes table references to a named schema.

The installable package name is `kysely`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require connectivity to a real database server, nor driver components for PostgreSQL, MySQL, or SQLite network protocols. Execution behavior is defined only over the bundled `DummyDriver`.
- This specification does not define transaction management, connection pooling, streaming, or migration tooling.
- This specification does not define database introspection results. Introspector components must exist as dialect plumbing, but no behavior of their metadata queries is defined here.
- This specification does not require dialects beyond PostgreSQL, MySQL, and SQLite.
- This specification does not define `merge into` statements.
- This specification does not define compile-time type inference quality. Behavior is assessed through runtime compilation output, not through the type system.
- This specification does not require a command-line interface.

## Representative Workflows

A query definition is written once against the fluent API and projected into any dialect's SQL. A dialect object supplies the four component factories; `DummyDriver` stands in for a live connection.

```ts
import {
  Kysely, DummyDriver,
  PostgresAdapter, PostgresIntrospector, PostgresQueryCompiler,
  MysqlAdapter, MysqlIntrospector, MysqlQueryCompiler,
} from 'kysely'

const pg = new Kysely<any>({
  dialect: {
    createAdapter: () => new PostgresAdapter(),
    createDriver: () => new DummyDriver(),
    createIntrospector: (db) => new PostgresIntrospector(db),
    createQueryCompiler: () => new PostgresQueryCompiler(),
  },
})

const query = pg
  .selectFrom('crew')
  .select(['id', 'call_sign'])
  .where('missions', '>', 4)

const compiled = query.compile()
// compiled.sql        === 'select "id", "call_sign" from "crew" where "missions" > $1'
// compiled.parameters deep-equals [4]
```

The same chain compiled under a MySQL dialect renders backtick quoting and `?` placeholders: ``select `id`, `call_sign` from `crew` where `missions` > ?``.

Mutations, plugins, and execution compose the same way. With `CamelCasePlugin` installed, the API accepts camelCase names while the SQL uses snake_case, and execution through `DummyDriver` resolves with no rows:

```ts
import { Kysely, CamelCasePlugin } from 'kysely'

const db = new Kysely<any>({ dialect, plugins: [new CamelCasePlugin()] })

const ins = db
  .insertInto('crewMember')
  .values({ callSign: 'Vega', missionCount: 3 })
  .returning(['id'])

ins.compile().sql
// 'insert into "crew_member" ("call_sign", "mission_count") values ($1, $2) returning "id"'

await ins.execute()          // resolves to [] under DummyDriver
await db.destroy()           // afterwards execute() rejects; compile() still works
```

## Query Compiler Instances And Dialects

An instance is the entry point for building and compiling queries; its dialect decides how a query definition renders as SQL text.

**Construction.** The `Kysely` constructor accepts a configuration object with a required `dialect` and an optional `plugins` array. A dialect is any object providing four factory methods: `createAdapter()`, `createDriver()`, `createQueryCompiler()`, and `createIntrospector(db)`. The package exports ready component classes for three engines — `PostgresAdapter`/`PostgresQueryCompiler`/`PostgresIntrospector`, `MysqlAdapter`/`MysqlQueryCompiler`/`MysqlIntrospector`, `SqliteAdapter`/`SqliteQueryCompiler`/`SqliteIntrospector` — plus `DummyDriver`, a driver that opens no connection and returns empty results for every statement. If the configuration lacks a dialect, construction must throw an error.

**Compilation.** Every query builder (selection, insertion, update, deletion, and every schema definition builder) exposes `compile()`, which returns a compiled query object exposing `sql`, the finished SQL string, and `parameters`, the array of bound values in placeholder order. Compiling must not require any database and must be repeatable: calling `compile()` twice on the same builder returns equal `sql` and equal `parameters`.

**Dialect rendering rules.** The PostgreSQL compiler must quote identifiers with double quotes and number placeholders `$1`, `$2`, … in parameter order. The MySQL compiler must quote identifiers with backticks and write every placeholder as `?`. The SQLite compiler must quote identifiers with double quotes and write every placeholder as `?`. All keywords render in lowercase. One query definition must compile under any of the three compilers with the same parameter values in the same order; only the SQL text differs.

## Row Selection Queries

Selection builders produce `select` statements from table sources, projections, filters, joins, grouping, ordering, and pagination.

**Sources and projections.** `selectFrom` accepts a table name; the form `'crew as c'` registers an alias and renders `"crew" as "c"`. `select` accepts a single column, an array of columns, or a callback receiving the expression builder; the form `'call_sign as cs'` renders `"call_sign" as "cs"`. Qualified names like `'c.call_sign'` render each segment quoted: `"c"."call_sign"`. `selectAll()` renders `select *`; `selectAll('c')` renders `select "c".*`. `distinct()` renders `select distinct`. `selectNoFrom` builds a from-less selection from aliased expressions (`select 1 + 1 as "v"`). An empty projection list must still compile (the column list is empty), and selecting a mix of expressions and columns preserves the given order.

**Filters.** `where(lhs, op, rhs)` appends one comparison; the right-hand value binds as a parameter. Repeated `where` calls join with `and`, unparenthesized, in call order. `whereRef(lhsRef, op, rhsRef)` compares two columns with no parameter. Passing `null` with operator `is` or `is not` renders the literal SQL `is null` / `is not null` and binds nothing, while `=` with `null` binds `null` as an ordinary parameter. `where` also accepts a callback receiving the expression builder, a raw fragment as the left-hand side, and a selection builder as the right-hand side — the subquery renders parenthesized in place of a placeholder. `clearWhere()` discards every accumulated filter.

**Joins.** `innerJoin(table, leftRef, rightRef)` renders `inner join "pet" on "pet"."owner_id" = "crew"."id"` style clauses; `leftJoin` renders `left join`. Each also accepts a callback form receiving a join builder with `onRef(leftRef, op, rightRef)` for column-to-column conditions and `on(ref, op, value)` for parameterized conditions; multiple conditions join with `and`. A derived table joins through a callback that builds a subquery and names it with `as`, rendering `inner join (select …) as "alias" on …`. Join clauses render in call order after the `from` clause.

**Grouping, ordering, pagination.** `groupBy` accepts a column and renders `group by "col"`. `having` accepts the same trigger shapes as `where`, including an expression-builder callback as the left-hand side (`having count("id") > $1`). `orderBy` with one argument renders the bare column (`order by "gen"`); a second argument `'asc'` or `'desc'` appends that direction verbatim; an expression callback orders by the rendered expression; repeated calls accumulate comma-separated terms in call order. `limit` and `offset` bind their counts as ordinary parameters in every dialect (`limit $1 offset $2` under PostgreSQL, `limit ? offset ?` under MySQL and SQLite).

## Expressions And Scalar Functions

The expression builder — received by callbacks passed to `where`, `select`, `having`, `set`, and `orderBy` — constructs comparison, logical, and function expressions that render inside any statement.

**Comparisons and logic.** Calling the expression builder itself as `eb(lhs, op, rhs)` builds one comparison. The operator must be one of the supported comparison operators — including `=`, `!=`, `<>`, `>`, `>=`, `<`, `<=`, `in`, `not in`, `like`, `not like`, `ilike`, `is`, `is not` — and both `!=` and `<>` render exactly as written. If the operator is not in the supported set, the call must throw an `Error` whose message names the rejected operator. `eb.and(list)` and `eb.or(list)` render their members joined by ` and ` / ` or ` inside one pair of parentheses. `eb.not(expr)` prefixes `not `. `eb.between(ref, lo, hi)` renders `"ref" between $1 and $2` with both bounds parameterized. An `in`/`not in` list binds each element as its own parameter, comma-separated inside parentheses; an empty list renders `in ()` with no parameters.

**Subqueries.** `eb.selectFrom(...)` starts a correlated subquery with the full selection API; `whereRef` expresses the correlation. An aliased subquery in a projection renders parenthesized: `(select "name" from "cargo" where … limit $1) as "cargo_name"`. `eb.exists(subquery)` renders `exists (select …)`.

**Case, cast, and values.** `eb.case().when(lhs, op, rhs).then(value).else(value).end()` renders `case when … then $n else $m end`, with `then`/`else` values parameterized, and the finished expression aliases with `as`. `eb.cast(ref, type)` renders `cast("ref" as type)` with the type text unquoted. `eb.val(v)` turns a plain value into a bound-parameter expression.

**Functions.** `eb.fn(name, argRefs)` renders a function call over column references (`length("b")`). Named helpers exist for common functions: `eb.fn.count(ref)` renders `count("ref")`, `eb.fn.coalesce(ref, expr)` renders `coalesce("ref", …)`. Aggregate builders expose `distinct()`, rendering `count(distinct "a")`, and every function expression aliases with `as`, rendering `count("id") as "num"`.

## Insert, Update And Delete

Mutation builders produce `insert`, `update`, and `delete` statements with dialect-appropriate clause support.

**Insert.** `insertInto(table).values(row)` renders the column list from the row's keys in object-key order and one placeholder per value: `insert into "crew" ("call_sign", "missions") values ($1, $2)`. `values` with an array of rows renders one parenthesized tuple per row; the column list is the union of all row keys in first-encountered order, and a row missing a column renders the keyword `default` in that position. A raw fragment as a value renders inline in the tuple instead of binding a parameter. `defaultValues()` renders `insert into "crew" default values`.

**Conflict handling.** `onConflict` accepts a callback over a conflict builder: `oc.column(name).doNothing()` renders `on conflict ("name") do nothing`, and `oc.column(name).doUpdateSet(row)` renders `on conflict ("name") do update set "col" = $n …` with the update values parameterized. Under the MySQL dialect, `ignore()` on an insert renders `insert ignore into`.

**Returning.** On PostgreSQL and SQLite, insert, update, and delete builders support `returning(columns)` — rendering `returning "id"` style lists with alias support — and `returningAll()`, rendering `returning *`.

**Update and delete.** `updateTable(table).set(row)` renders `update "crew" set "a" = $1, "b" = $2` with assignments in object-key order and values parameterized. `set` also accepts a callback receiving the expression builder, so an assignment renders an expression instead of a placeholder: `set "missions" = "missions" + $1`. `deleteFrom(table)` renders `delete from "crew"`, and filters attach through the same `where` API as selection.

## Query Composition And Reuse

Builders are immutable values: query definitions compose, branch, and extend without interfering with each other.

**Common table expressions.** `with(name, cb)` prepends a CTE whose body is built by the callback: `with "adults" as (select …) select …`. Repeated `with` calls accumulate comma-separated CTEs in call order, and a later CTE body must be able to select from an earlier CTE by name. `withRecursive(nameWithColumns, cb)` renders `with recursive`; a name of the form `'nums(n)'` renders the quoted name followed by the quoted column list: `"nums"("n")`.

**Set operations.** `union(other)` joins two selections with ` union `; `unionAll(other)` joins with ` union all `. The operations chain left-to-right in call order.

**Conditional building.** `$if(condition, cb)` applies the callback's refinements only when the condition is true; when false, the builder compiles as if `$if` had not been called.

**Immutability.** Every builder method returns a new builder and must leave the receiver unchanged: after deriving `q2 = q1.where(…)`, compiling `q1` must show no trace of the added filter. Compilation is a pure projection — it must not mutate the builder, and repeated calls return equal results.

## Raw SQL Fragments

The `sql` template tag builds raw fragments that carry their own parameters and compile under any dialect, standalone or embedded.

**The template tag.** An expression `` sql`select * from t where a > ${x}` `` binds each interpolated value as a parameter in interpolation order. A fragment compiles standalone through `compile(instance)`, returning the same compiled-query shape as builders, and the dialect of the passed instance controls quoting and placeholder style. Fragments embed anywhere an expression is accepted — as a `where` left-hand side, as a projection item via `as(alias)`, as an insert value — and an embedded fragment's parameters interleave with the host statement's parameters in overall left-to-right order.

**Identifier and literal helpers.** `sql.ref(name)` renders a quoted column reference. `sql.id(...parts)` renders each part quoted and dot-joined: `"x"."y"`. `sql.table(name)` renders a quoted table name. `sql.lit(value)` renders the value as an inline literal (strings in single quotes) instead of a parameter. `sql.raw(text)` splices the text verbatim with no quoting or binding. `sql.join(items)` renders the items as parameters separated by `, `; a second argument replaces the separator with a raw fragment (for example ` or `). All identifier helpers follow the quoting style of the dialect the fragment ultimately compiles under.

## Identifier Transforms And Schema Scoping

Plugins and schema scoping rewrite identifier rendering without changing query structure or parameters.

**CamelCasePlugin.** With `new CamelCasePlugin()` in the instance's `plugins`, every camelCase identifier written through the API renders in snake_case: table names (`crewMember` → `"crew_member"`), column references, qualified references (`cm.firstName` → `"cm"."first_name"`), alias definitions in both positions (`firstName as displayLabel` → `"first_name" as "display_label"`), insert column lists, and `sql.ref` references. The plugin must not change the parameters array of any query.

**Schema scoping.** `withSchema(name)` returns a scoped instance whose table references render schema-qualified in selections, insertions, updates, deletions, and schema definition statements: `"mats"."crew"`. Scoping composes with the rest of the API unchanged.

## Schema Definition Statements

The `schema` property of an instance builds data-definition statements that compile through the same `compile()` contract with an empty parameter list.

**Creating tables.** `schema.createTable(name)` starts a table definition; each `addColumn(name, type, modifiers?)` appends one column, and the columns render comma-separated inside parentheses. The type string passes through unquoted exactly as written (`integer`, `text`, `serial`, `varchar(50)`, `timestamptz`). The optional third argument is a callback over a column builder with these modifiers: `primaryKey()` renders `primary key`; `notNull()` renders `not null`; `unique()` renders `unique`; `references('crew.id')` renders `references "crew" ("id")`; `onDelete('cascade')` renders `on delete cascade` after the reference; `defaultTo(value)` renders `default` followed by the value inline (numbers bare, strings in single quotes, raw fragments verbatim — never a parameter); `autoIncrement()` renders the MySQL keyword `auto_increment`. Modifiers render in a fixed canonical order independent of the call order on the column builder: `default …`, then `not null`, then `unique`, then `primary key`, then `auto_increment`, with `references … on delete …` rendered last.

**Indexes, drops, and alterations.** `schema.createIndex(name).on(table).column(col)` renders `create index "idx" on "tbl" ("col")`. `schema.dropTable(name)` renders `drop table "tbl"`, and `ifExists()` inserts `if exists`. `schema.alterTable(name).addColumn(name, type)` renders `alter table "tbl" add column "col" type`.

## Execution Lifecycle

Execution is a thin layer over compilation; under `DummyDriver` it observes the connection lifecycle without any database.

**Executing.** `execute()` on any query builder compiles the query, runs it through the dialect's driver, and resolves with the row array; under `DummyDriver` it must resolve with an empty array. `executeTakeFirst()` resolves with the first row, hence `undefined` under `DummyDriver`. `executeTakeFirstOrThrow()` must reject with a `NoResultError` when no row comes back; `NoResultError` is an exported `Error` subclass and its message is `no result`.

**Destruction.** The driver initializes lazily on the first execution. `destroy()` returns a promise and shuts the driver down. While the driver has been initialized by a prior execution, after `destroy()` every `execute()` variant must reject with an `Error` stating the driver has already been destroyed; `compile()` on that instance's builders must continue to work — compilation never touches the driver.

## State Model

The core state is the query definition: an immutable value assembled by fluent builder calls, where every call yields a new definition and no call observes or mutates its receiver. An instance holds the dialect components, the plugin list, and one driver whose lifecycle (live → destroyed) is the only mutable state in the system.

Public projections of a query definition:

1. **PostgreSQL compilation** — SQL text with `"…"` quoting and `$n` placeholders, plus the parameter array.
2. **MySQL compilation** — SQL text with backtick quoting and `?` placeholders, plus the same parameter array.
3. **SQLite compilation** — SQL text with `"…"` quoting and `?` placeholders, plus the same parameter array.
4. **Plugin-transformed compilation** — the same definition rendered through identifier transforms (`CamelCasePlugin`) and schema scoping (`withSchema`).
5. **Execution** — the definition run through the driver (`execute`, `executeTakeFirst`, `executeTakeFirstOrThrow`), which under `DummyDriver` observes the empty-result and lifecycle contracts.
6. **Raw-fragment compilation** — `sql` fragments compiled standalone against an instance.

## Error Semantics

| Condition | Outcome |
|---|---|
| `new Kysely(config)` where `config` has no `dialect` | throws an error at construction |
| Comparison built with an operator outside the supported set | throws `Error`; the message names the rejected operator |
| `executeTakeFirstOrThrow()` when execution yields no rows | rejects with `NoResultError` (an `Error` subclass, message `no result`) |
| `execute()` (any variant) after `destroy()` on an instance that has executed at least one statement | rejects with an `Error` stating the driver has already been destroyed |

All other API sequences described in this document must succeed without throwing. Compilation itself never validates against a schema: unknown tables and columns compile normally.

## Cross-View Invariants

1. One query definition compiled under the PostgreSQL, MySQL, and SQLite compilers must produce the same parameter values in the same order; the dialects differ only in identifier quoting and placeholder style.
2. In every compiled query, the number of placeholders in `sql` must equal the length of `parameters` — for PostgreSQL the highest `$n` index equals the array length, and for MySQL/SQLite the count of `?` equals it.
3. Deriving a new builder from an existing one must never change the existing builder's compilation: `compile()` before and after the derivation returns identical `sql` and `parameters`.
4. Installing `CamelCasePlugin` or scoping with `withSchema` must change only rendered identifiers in `sql`; the `parameters` array of every query is byte-for-byte unchanged.
5. Values interpolated into a `sql` fragment must appear in the compiled `parameters` in interpolation order, whether the fragment compiles standalone or embedded inside a larger statement's parameter sequence.
6. `destroy()` must flip only the execution projection: after a destruction that follows at least one execution, every `execute()` variant rejects, while `compile()` on the same builders returns the same result as before destruction.

## Public Interface

### Import Surface

```ts
import {
  Kysely,
  DummyDriver,
  PostgresAdapter, PostgresIntrospector, PostgresQueryCompiler,
  MysqlAdapter, MysqlIntrospector, MysqlQueryCompiler,
  SqliteAdapter, SqliteIntrospector, SqliteQueryCompiler,
  CamelCasePlugin,
  NoResultError,
  sql,
} from 'kysely'
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Kysely` | class | Instance entry point: builder roots, `schema`, `withSchema`, `destroy` |
| `DummyDriver` | class | Driver that opens no connection and returns empty results |
| `PostgresAdapter` | class | PostgreSQL dialect adapter component |
| `PostgresQueryCompiler` | class | Compiles definitions to PostgreSQL SQL (`"…"`, `$n`) |
| `PostgresIntrospector` | class | PostgreSQL dialect introspector component |
| `MysqlAdapter` | class | MySQL dialect adapter component |
| `MysqlQueryCompiler` | class | Compiles definitions to MySQL SQL (backticks, `?`) |
| `MysqlIntrospector` | class | MySQL dialect introspector component |
| `SqliteAdapter` | class | SQLite dialect adapter component |
| `SqliteQueryCompiler` | class | Compiles definitions to SQLite SQL (`"…"`, `?`) |
| `SqliteIntrospector` | class | SQLite dialect introspector component |
| `CamelCasePlugin` | class | Plugin mapping camelCase API identifiers to snake_case SQL |
| `NoResultError` | class | `Error` subclass rejected by `executeTakeFirstOrThrow` on empty results |
| `sql` | function | Template tag for raw fragments, with `ref`, `id`, `table`, `lit`, `raw`, `join` helpers |

### CLI Entry Points

There is no console script for this package. Programmatic use is through the package's named exports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. Tests execute with `vitest` under TypeScript (`typescript`, `@types/node` available). No third-party runtime dependencies are required or available to the implementation at runtime; the package must function self-contained.

The project must be an installable npm package named `kysely` whose root entry point provides the named exports listed in Public Interface, resolvable by Node.js under both ESM `import` and TypeScript `NodeNext` resolution. The assessment environment provides the same runtime and module resolution.

## Appendix B: Assessment Notes

Assessment exercises the public API only, in three dimensions: (1) atomic behavior — single-clause compilation under each dialect, expression and function rendering, mutation clause rendering, raw-fragment helpers, plugin identifier transforms, schema definition statements, and declared error semantics; (2) integration — combinations that span projections, such as one definition compiled under all three dialects, composed queries mixing CTEs, joins, subqueries and raw fragments, plugin plus schema scoping over mutations, and builder immutability across derivations; (3) end-to-end workflows — assembling instances from dialect components, building and compiling full statement families, and observing the execution lifecycle through `DummyDriver` and `destroy()`. Expected values are concrete SQL strings and parameter arrays computed from the rules in this document. Each test is assessed independently.
