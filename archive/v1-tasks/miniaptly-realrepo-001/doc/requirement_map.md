# MiniAptly Requirement Map

## Requirements

- `REQ-package-format`: simplified package artifacts expose `Name`, `Version`, `Arch`, `Depends`, payload checksum, and identity `(name, version, arch)`.
- `REQ-repo`: local repos support idempotent add, atomic conflict rejection, remove, show, and search.
- `REQ-snapshot`: snapshots are immutable package identity sets created from repos or snapshots.
- `REQ-snapshot-merge`: merge/filter rules are public and deterministic, including version choice, checksum conflict rejection, predicates, and parent graph preservation.
- `REQ-publish`: publishing materializes semantic index and release metadata for a distribution/component/architecture prefix.
- `REQ-cleanup`: cleanup reachability includes repos, snapshots, published prefixes, and pending transactions.
- `REQ-recovery`: public `fail_at` hooks create pending transactions; `recover()` is idempotent and restores/finishes consistent public state.
- `REQ-graph`: graph output is an order-insensitive semantic edge set across repos, snapshots, published prefixes, and packages.
- `REQ-atomicity`: failed operations do not expose mixed public projection state.

## Unit Coverage

- `MAU001`, `MAU002` -> `REQ-package-format`
- `MAU003`, `MAU004` -> `REQ-repo`, `REQ-atomicity`
- `MAU005`, `MAU006` -> `REQ-snapshot`, `REQ-snapshot-merge`
- `MAU007` -> `REQ-publish`
- `MAU008` -> `REQ-cleanup`
- `MAU009` -> `REQ-recovery`
- `MAU010` -> `REQ-graph`

## System Coverage

- `MAS001`: snapshot immutability across repo mutation; projections: snapshot show, diff, graph, published index.
- `MAS002`: publish switch cross-feature agreement; projections: published index, publish show, graph, cleanup dry-run.
- `MAS003`: cleanup reachability across repo/snapshot/published/pending states.
- `MAS004`: failed switch rollback/recovery across publish metadata, index, graph, cleanup, and recover.
- `MAS005`: merge/filter ordering and parentage across snapshot, publish, search/show, graph, and cleanup.

## Primitive-Cascade Guard

System rows should use prevalidated package fixtures and semantic comparisons. Parser, checksum, and identity failures should be clustered as primitive roots and not counted repeatedly as residual compositional gap.
