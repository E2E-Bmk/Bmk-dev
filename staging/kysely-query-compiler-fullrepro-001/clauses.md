# Clause IDs — kysely-query-compiler-fullrepro-001

Sidecar mapping of clause IDs to spec statements (section anchors in parentheses).

## Query Compiler Instances And Dialects (KYSL-INST)

- KYSL-INST-001: The `Kysely` constructor accepts a configuration object with a required `dialect` and an optional `plugins` array; a dialect provides `createAdapter()`, `createDriver()`, `createQueryCompiler()`, `createIntrospector(db)`.
- KYSL-INST-002: Ready component classes exist for three engines (Postgres/Mysql/Sqlite Adapter, QueryCompiler, Introspector) plus `DummyDriver`, which opens no connection and returns empty results.
- KYSL-INST-003: If the configuration lacks a dialect, construction must throw an error.
- KYSL-INST-004: Every query builder exposes `compile()` returning an object with `sql` (string) and `parameters` (array of bound values in placeholder order).
- KYSL-INST-005: Compilation requires no database and is repeatable: two `compile()` calls on the same builder return equal `sql` and equal `parameters`.
- KYSL-INST-006: PostgreSQL compiler quotes identifiers with double quotes and numbers placeholders `$1..$n`; MySQL uses backticks and `?`; SQLite uses double quotes and `?`; keywords render lowercase.
- KYSL-INST-007: One query definition compiles under any of the three compilers with the same parameter values in the same order.

## Row Selection Queries (KYSL-SEL)

- KYSL-SEL-001: `selectFrom` accepts a table name; `'crew as c'` registers an alias rendering `"crew" as "c"`.
- KYSL-SEL-002: `select` accepts a single column, an array, or an expression-builder callback; `'call_sign as cs'` renders `"call_sign" as "cs"`; qualified names render each segment quoted.
- KYSL-SEL-003: `selectAll()` renders `select *`; `selectAll('c')` renders `select "c".*`; `distinct()` renders `select distinct`.
- KYSL-SEL-004: `selectNoFrom` builds a from-less selection from aliased expressions.
- KYSL-SEL-005: `where(lhs, op, rhs)` binds the right-hand value as a parameter; repeated `where` calls join with `and` in call order, unparenthesized.
- KYSL-SEL-014: `where` accepts a selection builder as the right-hand side, rendering a parenthesized subquery in place of a placeholder.
- KYSL-SEL-006: `whereRef(lhsRef, op, rhsRef)` compares two columns with no parameter.
- KYSL-SEL-007: `is` / `is not` with `null` renders `is null` / `is not null` and binds nothing; `=` with `null` binds `null` as an ordinary parameter.
- KYSL-SEL-008: `clearWhere()` discards every accumulated filter.
- KYSL-SEL-009: `innerJoin(table, leftRef, rightRef)` / `leftJoin` render `inner join` / `left join` clauses with `on` conditions; callback form provides `onRef` (column-to-column) and `on` (parameterized), joined with `and`.
- KYSL-SEL-010: A derived table joins via a subquery callback named with `as`, rendering `inner join (select …) as "alias" on …`.
- KYSL-SEL-011: `groupBy` renders `group by "col"`; `having` accepts the same shapes as `where` including an expression-builder callback left-hand side.
- KYSL-SEL-012: `orderBy` with one argument renders the bare column; `'asc'`/`'desc'` appends verbatim; expression callbacks order by the rendered expression; repeated calls accumulate comma-separated.
- KYSL-SEL-013: `limit` and `offset` bind their counts as ordinary parameters in every dialect.

## Expressions And Scalar Functions (KYSL-EXPR)

- KYSL-EXPR-001: `eb(lhs, op, rhs)` builds one comparison; supported operators include `=`, `!=`, `<>`, `>`, `>=`, `<`, `<=`, `in`, `not in`, `like`, `not like`, `ilike`, `is`, `is not`; `!=` and `<>` render exactly as written.
- KYSL-EXPR-002: An operator outside the supported set must throw an `Error` whose message names the rejected operator.
- KYSL-EXPR-003: `eb.and(list)` / `eb.or(list)` join members with ` and ` / ` or ` inside one pair of parentheses; `eb.not(expr)` prefixes `not `.
- KYSL-EXPR-004: `eb.between(ref, lo, hi)` renders `between $1 and $2` with both bounds parameterized.
- KYSL-EXPR-005: An `in`/`not in` list binds each element as its own parameter, comma-separated inside parentheses; an empty list renders `in ()` with no parameters.
- KYSL-EXPR-006: `eb.selectFrom(...)` builds correlated subqueries; an aliased subquery in a projection renders parenthesized with its alias; `eb.exists(subquery)` renders `exists (select …)`.
- KYSL-EXPR-007: `eb.case().when(...).then(v).else(v).end()` renders `case when … then $n else $m end` with `then`/`else` parameterized; the result aliases with `as`.
- KYSL-EXPR-008: `eb.cast(ref, type)` renders `cast("ref" as type)` with the type unquoted; `eb.val(v)` renders a bound parameter.
- KYSL-EXPR-009: `eb.fn(name, argRefs)` renders a function call over column references; `eb.fn.count(ref)` renders `count("ref")`; `eb.fn.coalesce(ref, expr)` renders `coalesce(...)`; aggregates expose `distinct()`; function expressions alias with `as`.

## Insert, Update And Delete (KYSL-MUT)

- KYSL-MUT-001: `insertInto(table).values(row)` renders the column list from the row's keys in object-key order and one placeholder per value.
- KYSL-MUT-002: `values` with an array renders one tuple per row; the column list is the union of row keys in first-encountered order; a missing column renders the keyword `default`.
- KYSL-MUT-003: A raw fragment as an insert value renders inline instead of binding a parameter.
- KYSL-MUT-004: `defaultValues()` renders `insert into "t" default values`.
- KYSL-MUT-005: `onConflict` with `oc.column(name).doNothing()` renders `on conflict ("name") do nothing`; `doUpdateSet(row)` renders `do update set …` with parameterized values.
- KYSL-MUT-006: Under MySQL, `ignore()` renders `insert ignore into`.
- KYSL-MUT-007: On PostgreSQL and SQLite, insert/update/delete support `returning(columns)` and `returningAll()` (`returning *`).
- KYSL-MUT-008: `updateTable(t).set(row)` renders assignments in object-key order with parameterized values; `set` with an expression-builder callback renders expressions in assignments.
- KYSL-MUT-009: `deleteFrom(table)` renders `delete from "t"` and shares the selection `where` API.

## Query Composition And Reuse (KYSL-COMP)

- KYSL-COMP-001: `with(name, cb)` prepends a CTE; repeated calls accumulate comma-separated in call order; later CTE bodies select from earlier CTEs by name.
- KYSL-COMP-002: `withRecursive(nameWithColumns, cb)` renders `with recursive`; `'nums(n)'` renders `"nums"("n")`.
- KYSL-COMP-003: `union(other)` joins with ` union `; `unionAll(other)` joins with ` union all `; operations chain in call order.
- KYSL-COMP-004: `$if(condition, cb)` applies the callback only when the condition is true; when false the builder compiles as if `$if` had not been called.
- KYSL-COMP-005: Every builder method returns a new builder and leaves the receiver unchanged; compilation is pure and repeatable.

## Raw SQL Fragments (KYSL-RAW)

- KYSL-RAW-001: The `sql` template tag binds each interpolated value as a parameter in interpolation order.
- KYSL-RAW-002: A fragment compiles standalone through `compile(instance)`, returning the compiled-query shape; the instance's dialect controls quoting and placeholders.
- KYSL-RAW-003: Fragments embed as `where` left-hand sides, projection items via `as(alias)`, and insert values; embedded parameters interleave with the host statement's parameters in left-to-right order.
- KYSL-RAW-004: `sql.ref(name)` renders a quoted column reference; `sql.id(...parts)` renders parts quoted and dot-joined; `sql.table(name)` renders a quoted table name.
- KYSL-RAW-005: `sql.lit(value)` renders an inline literal (strings single-quoted); `sql.raw(text)` splices text verbatim.
- KYSL-RAW-006: `sql.join(items)` renders items as parameters separated by `, `; a second argument replaces the separator with a raw fragment.

## Identifier Transforms And Schema Scoping (KYSL-PLUG)

- KYSL-PLUG-001: With `CamelCasePlugin`, camelCase identifiers render snake_case: table names, column references, qualified references, alias definitions in both positions, insert column lists, and `sql.ref` references.
- KYSL-PLUG-002: `CamelCasePlugin` must not change the parameters array of any query.
- KYSL-PLUG-003: `withSchema(name)` returns a scoped instance whose table references render schema-qualified in selections, insertions, updates, deletions, and schema definition statements.

## Schema Definition Statements (KYSL-DDL)

- KYSL-DDL-001: `schema.createTable(name).addColumn(name, type, modifiers?)` renders columns comma-separated in parentheses; the type string passes through unquoted exactly as written.
- KYSL-DDL-002: Column modifiers render: `primaryKey()` → `primary key`; `notNull()` → `not null`; `unique()` → `unique`; `references('crew.id')` → `references "crew" ("id")`; `onDelete('cascade')` → `on delete cascade`; `autoIncrement()` → `auto_increment`; modifiers render in a fixed canonical order (`default`, `not null`, `unique`, `primary key`, `auto_increment`, `references … on delete …` last) independent of call order.
- KYSL-DDL-003: `defaultTo(value)` renders `default` plus the value inline (numbers bare, strings single-quoted, raw fragments verbatim), never a parameter.
- KYSL-DDL-004: `schema.createIndex(name).on(table).column(col)` renders `create index "idx" on "tbl" ("col")`; `dropTable(name)` renders `drop table`, with `ifExists()` inserting `if exists`; `alterTable(name).addColumn(...)` renders `alter table "tbl" add column …`.
- KYSL-DDL-005: Schema definition statements compile through the same `compile()` contract with an empty parameter list.

## Execution Lifecycle (KYSL-EXEC)

- KYSL-EXEC-001: `execute()` resolves with the row array — an empty array under `DummyDriver`; `executeTakeFirst()` resolves with the first row (`undefined` when empty).
- KYSL-EXEC-002: `executeTakeFirstOrThrow()` must reject with `NoResultError` (exported `Error` subclass, message `no result`) when no row comes back.
- KYSL-EXEC-003: The driver initializes lazily on first execution; while the driver has been initialized by a prior execution, after `destroy()` every `execute()` variant rejects with an `Error` stating the driver has already been destroyed, while `compile()` continues to work.

## Error Semantics (KYSL-ERR)

- KYSL-ERR-001: Construction without a dialect throws an error.
- KYSL-ERR-002: An unsupported comparison operator throws `Error` naming the operator.
- KYSL-ERR-003: `executeTakeFirstOrThrow()` on an empty result rejects with `NoResultError`.
- KYSL-ERR-004: Execution after `destroy()` on an instance that has executed at least one statement rejects with an `Error`.

## Cross-View Invariants (KYSL-INV)

- KYSL-INV-001: One definition compiled under all three compilers yields the same parameter values in the same order; only quoting and placeholder style differ.
- KYSL-INV-002: Placeholder count in `sql` equals `parameters.length` in every compiled query.
- KYSL-INV-003: Deriving a new builder never changes an existing builder's compilation.
- KYSL-INV-004: `CamelCasePlugin` and `withSchema` change only rendered identifiers; parameters are unchanged.
- KYSL-INV-005: Interpolated fragment values appear in compiled parameters in interpolation order, standalone or embedded.
- KYSL-INV-006: `destroy()` flips only the execution projection (after a destruction that follows at least one execution); compilation output is identical before and after.
