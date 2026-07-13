# Full-Reproduction System Task Policy

Date: 2026-06-28

## Decision

New strict benchmark tasks must be full-reproduction system tasks. "Multi-file"
is only a minimum structural condition; it is not sufficient. A candidate is
ineligible if the natural implementation is one standalone Python file, one
central in-memory model, or a thin "mini" clone of a large upstream repository.

This policy applies before Layer-1 PRD/rubric construction. It is a Layer-0
reject gate, not a later preference.

## Required Shape

Each new task must require a complete bounded product/subsystem reproduction
with an installable package or service layout, for example:

```text
product_replica/
  pyproject.toml or setup.cfg
  src/<package>/
    __init__.py
    cli.py
    store.py
    planner.py
    index.py
    recovery.py
    reports.py
  tests or public examples/
```

Minimum strict-task requirements:

- at least 10 candidate-owned source modules or service files;
- at least 2,000 non-test reference LOC unless the task is explicitly rejected
  as too small by a judge;
- at least two logical persistence artifacts, indexes, caches, ledgers, or
  generated materialized outputs;
- at least four public projections that can drift;
- at least three end-to-end user workflows with create/update/delete/replay or
  recovery phases;
- one CLI or package entrypoint that exercises the project as a system;
- one importable API surface used by tests independently from the CLI;
- hidden scoring run from outside the candidate workspace;
- no hidden test may import private helpers directly.

The reference solution should be large enough that a direct one-pass rewrite is
not the natural strategy. If a capable agent can rebuild the task in under
roughly 1,000 LOC while preserving all behavior, the task has probably been
under-scoped.

## Rejection Rule

Reject or materially rescope when:

- the reference can be naturally implemented as one short file;
- the candidate can pass by implementing only the public examples plus a few
  adjacent cases;
- all public views are direct functions over one dict/tree/graph;
- the system tests can be satisfied by one-shot recomputation from current state;
- the task only becomes hard by adding exact output text, private files, or
  arbitrary ordering;
- the only multi-file aspect is artificial packaging around a single model;
- the PRD is shorter than the product surface being evaluated and does not
  specify state model, lifecycle, persistence, errors, and compatibility rules.

## PRD And Test Scale

A full-reproduction task needs a product-grade public packet, not a prompt-sized
feature list. The packet must include:

- product overview and non-goals;
- state model and durable file/database layout at the public behavior level;
- CLI and API contracts with schemas;
- lifecycle workflows and failure/recovery semantics;
- compatibility/ordering/determinism rules;
- realistic examples covering multi-step workflows;
- ambiguity boundaries that prevent hidden-oracle preference.

The scoring suite must also scale with the task:

- at least 50 executable checks for a first strict candidate, preferably 80+;
- unit checks cover primitives across modules without cross-feature setup;
- integration checks exercise API/CLI/persistence boundaries;
- system checks exercise multi-step workflows, rollback, replay, exported
  artifacts, reverse indexes, reports, and recovery;
- black-box checks run from outside the candidate package and import only public
  APIs or execute public CLIs;
- hidden tests must include metamorphic and operation-sequence cases, not only
  final-result checks.

## Preferred Patterns

Prefer ProgramBench-like or real system surfaces:

- reverse-engineering or oracle-observation tasks with bundled docs;
- job schedulers with durable ledger, retries, cron, metrics, and event stream;
- build/cache systems with CAS, action metadata, eviction, status, and recovery;
- schema registries with global ID table, subject versions, compatibility,
  deletes, and reverse references;
- migration/build/archive tools with plans, state files, materialized outputs,
  rollback, and reports.

## Harness Implication

Strict runs should use a mini-SWE-agent-style cleanroom:

- visible root contains only public packet, starter project skeleton if any, and
  empty implementation files;
- no `rubric.json`, score reports, reference solution, prior candidates, or
  iteration notes;
- network disabled by default;
- full trajectory saved;
- final artifact copied out and scored externally.

OpenHands runs may still be useful for debugging, but they do not count as
strict pass-rate evidence unless run inside the same cleanroom contract.

## Candidate Impact

Existing mini tasks remain historical diagnostics and must not be promoted.
They should not be expanded unless the public scope becomes a real
full-reproduction subsystem. For example:

- JobLedger should be a package/service with store, scheduler, uniqueness,
  retry, metrics, events, recovery, CLI, and public API modules.
- BuildCache should be a package/service with CAS, action cache, eviction,
  status, namespace, audit, recovery, HTTP/CLI surfaces, and durable state.
- SchemaRegistry should be a package/service with parser, canonicalizer,
  subject store, compatibility engine, references, deletion, reports, CLI/API,
  and persistent ID/version history.
