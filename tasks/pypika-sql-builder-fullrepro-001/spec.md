# PyPika Public SQL Builder

## Product Overview

PyPika is a Python API for building SQL strings from composable query, table,
field, criterion, function, and dialect builder objects.

## Scope

This package covers the documented public `Query`, `Table`, `Field`, and
expression surface for deterministic SQL construction. It includes SELECT
queries, FROM and WHERE clauses, aliases, arithmetic and boolean criteria,
joins, functions and aggregates, GROUP BY and HAVING, ORDER BY, LIMIT and
OFFSET, INSERT, UPDATE, DELETE, set operations, subqueries, CTEs, parameters,
analytic functions, and selected dialect builders.

SQL assertions use a stable normalization helper that collapses whitespace.
They check documented SQL tokens, quoting, clause order, values, aliases, and
composed semantics without depending on incidental line wrapping.

## Installable Surface

The package is imported as `pypika`. The checks use public names exported from
`pypika`, the documented `pypika.functions`, `pypika.analytics`, and
`pypika.terms.Values` surfaces, and public dialect/query classes. No database
connection or SQL execution is involved.

## Product State Model

Query builders are immutable public descriptions of SQL statements. Tables
provide fields and namespaces, fields compose into arithmetic and criteria
expressions, and builder methods add clauses while preserving the SQL
structure. Dialect query classes select vendor-specific quoting, pagination,
DML, and conflict-handling syntax.

## Error Semantics

The package checks public exception classes only where needed for invalid
builder combinations and does not assert exact diagnostic text. The primary
contract is successful deterministic SQL generation for documented inputs.

## Cross-View Invariants

`str(query)` and `query.get_sql()` describe the same normalized SQL. Aliases
remain visible in projections and nested scopes. Criteria preserve boolean
composition, joins preserve their ON or USING relationship, aggregates remain
inside GROUP BY and HAVING workflows, and dialect builders preserve the same
logical statement while changing documented vendor syntax.

## Representative Workflows

Representative workflows compose multiple public operations, such as selecting
from an aliased table, filtering and ordering, joining and aggregating,
building a CTE or correlated subquery, inserting from a SELECT, updating or
deleting with criteria, collecting parameter values, and applying a dialect
builder's conflict or pagination features.

## Non-Goals

This package does not execute SQL, connect to a database, use network or
socket APIs, depend on host state, inspect private modules, import upstream
tests, assert exact incidental exception strings, or cover nondeterministic
database behavior. Whole-output behavior outside the stable normalization
helper and documented SQL semantics is excluded.

## Invocation Protocol

Run pytest against this package with `--target-root` pointing to the supplied
PyPika source checkout. The target root is inserted before collection so the
public import resolves to the selected checkout.

## Environment

The reference environment is Python 3.11 on Linux without network access.
Python 3.10 is also used for an independent local replay. The target package
is not pre-installed; the target checkout is supplied as the pytest target
root. Required packages are `pytest` and `pytest-json-report`. No runtime
database, service, or network dependency is used.

## Evaluation Notes

Current evidence is same-process local replay only. It does not establish a
trusted black-box Stage 4 runner, external signature, trusted provenance,
candidate score, final qualification, or final QUALIFIED status.
