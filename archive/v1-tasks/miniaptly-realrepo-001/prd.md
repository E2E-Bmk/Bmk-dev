# MiniAptly Public Product Packet

## Overview

Build `miniaptly.py`, a dependency-free Python archive manager inspired by aptly-style package repository workflows. The product manages simplified package artifacts, local repositories, immutable snapshots, published repository trees, cleanup reachability, recovery after interrupted publish operations, and graph/report projections.

The goal is not Debian compatibility. The goal is a coherent archive lifecycle where all public projections describe the same package state after mixed operations.

The module must be importable from the solution directory:

```python
from miniaptly import MiniAptly, ArchiveError
```

`MiniAptly()` constructs a fresh in-memory archive. Implementations may also accept
an optional root/path argument for durable storage, but the zero-argument form must
work.

The implementation may also provide a CLI wrapper, but the scoring surface will use the Python API.

Use only the Python standard library.

## Public Product Contract And Semantic Output Schemas

All public query methods must return plain Python dictionaries/lists/sets that can be serialized to JSON. Tests compare semantic records, not display strings, file layout, private database state, or graph edge order.

### Package Artifact

Package artifacts are text files with a control stanza, a blank line, then payload bytes:

```text
Name: alpha
Version: 1.2.0
Arch: amd64
Depends: beta >=1.0, gamma

payload
```

Public fields:

- `Name`: lowercase letters, digits, dash, and underscore.
- `Version`: dot-separated non-negative integers. Comparison uses numeric tuple comparison with trailing zero trimming.
- `Arch`: one of `amd64`, `arm64`, `all`.
- `Depends`: comma-separated dependency atoms. Dependency solving is out of scope; dependency text is preserved in reports and graph metadata.
- `checksum`: SHA256 of payload bytes.

Package identity is `(name, version, arch)`. Importing the same identity with the same checksum is idempotent. Importing the same identity with a different checksum fails atomically.

### Semantic Records

The API must expose these semantic records:

- package record: `{name, version, arch, checksum, depends}`
- repo show: sorted package records
- snapshot show: `{name, sources, packages, parents}`
- snapshot diff: `{added, removed, changed}`
- publish show: `{distribution, component, arch, snapshot, packages, index_digest}`
- cleanup dry-run: `{remove, keep, blocked}` over package checksums with public reasons
- graph: edge records `{from_type, from, to_type, to, relation}`
- recover: `{status, prefix}` where status is `no_pending`, `rolled_back`, or `completed`

`depends` may be returned as either a comma-separated string or a list of dependency
atoms; semantic tests normalize both forms. Prefix strings may use any visible
separator as long as distribution, component, and arch are recoverable from the
public value.

`snapshot_diff.changed` must identify the old and new package records for each
changed `(name, arch)` pair. The field names may be `before`/`after` or `from`/`to`.

Graph relation names are public but semantic tests compare edge endpoints by type
and identity; edge order is never significant.

## Feature Set

### Package Parser

`parse_package(path)` parses an artifact and returns a package record. Malformed artifacts raise `ArchiveError`.

### Local Repositories

`add(repo, package_path)` imports a package into a local repo. `remove(repo, name, version=None, arch=None)` removes matching package identities from the repo without deleting pool artifacts that remain reachable elsewhere.

`repo_show(repo)` returns the current repo package records. `repo_search(repo, **predicates)` filters by name, arch, and minimum version.

### Snapshots

`snapshot_create(name, source)` creates an immutable snapshot from a repo or snapshot. Later source mutations must not mutate existing snapshots.

`snapshot_merge(name, sources, *, first_wins=False)` merges snapshots left to right. If two inputs contain the same `(name, arch)` with different versions, the higher version wins unless `first_wins=True`. If the same identity has different checksums, merge fails atomically.

`snapshot_filter(name, source, *, name_filter=None, arch=None, min_version=None)` creates a filtered snapshot. All predicates must hold.

`snapshot_show(name)` and `snapshot_diff(left, right)` expose semantic snapshot records.

### Publishing

`publish(snapshot, distribution, component, arch)` materializes a published prefix from a snapshot. `publish_switch(snapshot, distribution, component, arch, *, fail_at=None)` switches an existing prefix to a new snapshot while preserving the prefix options.

`fail_at` is a public test hook. Supported values are `after_journal`, `after_index`, and `after_publish_record`. It may only be used by tests. If an operation fails with a pending transaction, mutating commands other than `recover()` must fail until recovery.

`publish_show(distribution, component, arch)` returns the semantic publish record. `published_index(distribution, component, arch)` returns the package records in the materialized index.

### Cleanup

`cleanup_dry_run()` returns package checksums that would be removed, kept, or blocked. Reachability comes from local repos, snapshots, published prefixes, and pending transactions. `cleanup_apply()` removes only unreachable pool artifacts and returns the same semantic report with an `applied` flag.

### Recovery

`recover()` is idempotent. It either reports no pending transaction, rolls back to the last committed published state, or completes a pending publish/switch so all projections agree.

### Graph

`graph()` returns order-insensitive semantic edges among repos, snapshots, published prefixes, and package identities. Merge and filter operations preserve parent edges.

## Global Invariants

- Package identity and checksum semantics are shared by repos, snapshots, published indexes, cleanup, search/show, and graph.
- Snapshots are immutable.
- Published index records, publish metadata, graph edges, and cleanup reachability must agree on the published snapshot.
- Cleanup must never remove a package artifact reachable from any repo, snapshot, published prefix, or pending transaction.
- Failed imports, snapshot creation, merge/filter, publish, switch, cleanup, and recovery are atomic at the public projection level.
- While a pending transaction exists, read-only projections expose the last committed state plus pending status; mutating commands other than `recover()` fail.
- `recover()` is idempotent and leaves all projections consistent.

## Non-Goals

Do not implement real `.deb` parsing, APT dependency solving, GPG signing, compression, network mirrors, HTTP serving, OS package-manager behavior, full Debian version ordering, or exact aptly CLI compatibility.

## Evaluation Style

Unit tests exercise feature-pure primitives: package parsing, local repo membership, snapshot creation, publish index emission, cleanup reachability over explicit fixture graphs, and recovery marker behavior.

System tests exercise lifecycle invariants over at least three public projections after mixed operations such as repo mutation after snapshot, publish switch, cleanup, interrupted publish recovery, and merge/filter publish flows.
