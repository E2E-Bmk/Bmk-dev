# Koanf Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

# Context

## Product Overview

`koanf` is a Go configuration library that composes provider facts into a delimiter-addressed configuration graph. The graph supports native lookups, typed decoding, serialization, ordered merge behavior, generation-aware publication, immutable snapshots, semantic change receipts, and optimistic reload transactions.

A `Koanf` value is the live owner of one published fact graph. Providers and parsers acquire facts, while generations, snapshots, receipts, and reload transactions make publication boundaries explicit to callers.

## Non-Goals

- This specification does not require remote cloud providers, network services, credential discovery, or external configuration daemons.
- This specification does not require a command-line program.
- This specification does not define debug string formatting, map iteration order, file notification latency, or exact error text.
- This specification does not require caller-visible implementation fields or a particular synchronization algorithm.

# Orientation

## Representative Workflows

### Load with a receipt and preserve a snapshot

1. Create a `Koanf` value and load initial provider facts.
2. Capture a `Snapshot` of the published generation.
3. Call `LoadWithReceipt` with a later provider.
4. Inspect the receipt's generation transition and sorted semantic changes.
5. Observe the old snapshot and the new live value independently.

The snapshot must retain the earlier facts, while the receipt and every fresh live projection must describe the later published generation.

### Stage and commit a local reload

1. Start a `ReloadTxn` from the live value.
2. Stage a file load and a map overlay through the transaction.
3. Inspect `Preview` while ordinary live lookups still return the preceding generation.
4. Commit the transaction.
5. Compare the commit receipt, a fresh live snapshot, typed decode, and serialized bytes.

A successful commit must publish all staged facts exactly once. A failed stage, aborted transaction, or stale commit must not publish a partial graph.

### Compare semantic projections

1. Load equivalent facts through different local provider and parser combinations.
2. Capture snapshots and their `ProjectionDigest` values.
3. Marshal and reload one snapshot.
4. Compare digests, keys, raw maps, and selected typed values.

Equivalent facts must produce equal digests even when map order or lossless numeric Go representation differs.

# Behavior

## Generation and Publication

This domain defines when live facts become a new published generation and how callers observe that boundary.

**Generation clock.** A new `Koanf` value must report `Generation(0)`. When `Load`, `Set`, `Delete`, `Merge`, `MergeAt`, `LoadWithReceipt`, or a reload commit publishes a semantically changed fact graph, `Koanf.Generation` must advance by exactly one. When an operation is equivalent to the current graph, then the generation must remain unchanged. If an operation returns an error, then the generation and all live projections must retain the preceding publication.

**Provider ownership.** When a provider returns a map, the live owner must publish defensively owned facts. If the provider map, a different `Koanf` value loaded from that provider, or a returned projection is later modified, then the published graph must remain independent.

**Direct publication receipt.** When `LoadWithReceipt` succeeds, it must apply the same provider, parser, option, and merge rules as `Load` and return a `MergeReceipt`. The receipt's `Before` and `After` fields must identify the generation transition. `Published` must be true exactly when the canonical fact graph changed. If the load fails, then the method must return the load error together with an unpublished receipt whose generations and digest describe the retained live graph.

## Snapshots, Receipts, and Canonical Projections

This domain defines immutable observations and semantic equivalence across path, map, byte, typed, and receipt views.

**Snapshot isolation.** When `Koanf.Snapshot` succeeds, the returned `Snapshot` must freeze the current generation and complete fact graph. Later live loads, sets, deletes, merges, reloads, and caller changes to returned maps must not alter the snapshot. `Snapshot.Generation`, `Published`, `Get`, `Exists`, `Keys`, `All`, `Raw`, `Marshal`, `Unmarshal`, and `UnmarshalWithConf` must observe that same frozen graph. A live snapshot must report `Published` as true; a transaction preview must report it as false and must report the transaction's base generation.

**Change receipt.** A `MergeReceipt` must expose `Before`, `After`, `Published`, `Changes`, and `Digest`. Each `Change` must name one normalized logical leaf `Path` and one `Kind`: `ChangeAdded`, `ChangeUpdated`, or `ChangeRemoved`. The change list must be sorted lexicographically by path, contain each changed path once, and describe the transition from the before graph to the after graph. A scalar-to-map or map-to-scalar replacement must report the removed and added logical leaves produced by that replacement.

**Canonical digest.** `ProjectionDigest` must be a lowercase hexadecimal SHA-256 value for the complete semantic fact graph. Canonicalization must ignore Go map iteration order and delimiter spelling after logical path normalization, retain slice order, distinguish an absent fact from a present nil fact, and treat losslessly equal integral numeric values as equivalent across signed, unsigned, and floating Go representations. When marshal and reload preserve semantic facts, then snapshots before and after reload must have equal digests. A receipt digest must equal the digest of a fresh live snapshot at its `After` generation.

## Reload Transactions and Recovery

This domain defines staged reload ownership, optimistic publication, and last-good recovery.

**Staged state.** When `Koanf.BeginReload` returns a `ReloadTxn`, the transaction must capture the live generation and a defensively owned copy of its facts. `ReloadTxn.Load`, `Set`, and `Delete` must apply native behavior to staged facts only. `Preview` must return an unpublished snapshot of the complete staged graph. While a transaction is open, ordinary live observations must remain on the current published generation.

**Commit.** When `ReloadTxn.Commit` runs while the live generation still equals the transaction's base generation, it must atomically compare the staged graph with the live graph, close the transaction, and return a `MergeReceipt`. A changed graph must publish once and advance one generation. An equivalent graph must close without publication and return an empty change list.

**Optimistic conflict.** If the live generation changes after a transaction begins, then `Commit` must return `ErrStaleGeneration`, close the transaction, and leave the newer live graph unchanged. The stale transaction's staged facts must never overwrite or merge into the newer generation.

**Recovery and closure.** If a staged load, parse, set, or delete fails, then the transaction must remain open with its preceding last-good preview unchanged. When `Abort` succeeds, it must close the transaction without changing the live graph. After commit, stale rejection, or abort, `Load`, `Set`, `Delete`, `Preview`, `Commit`, and `Abort` must return `ErrClosedReload`. Both public errors must support comparison through `errors.Is`.

## Native Configuration Operations

This domain defines the underlying provider, parser, merge, query, serialization, and typed decode behavior used by direct and transactional workflows.

**Loading and merge.** When a provider implements map acquisition, `Load` must merge its nested map. When a provider supplies bytes, `Load` must require a parser and merge the parsed map. Later scalar facts must replace earlier scalar facts, nested maps must merge recursively, and unrelated siblings must remain. Where `WithMergeFunc` is present, the supplied function must own the merge result. If acquisition, parsing, or merge fails, then no partial graph must be published.

**Queries and explicit changes.** `Get`, typed getters, `Exists`, `Keys`, `All`, `Raw`, and `KeyMap` must observe delimiter-normalized paths in one graph. `Set`, `Delete`, `Merge`, and `MergeAt` must update all derived path projections atomically. Returned maps and derived `Copy`, `Cut`, and `Slices` values must not expose caller-writable ownership of their source.

**Serialization and typed decode.** `Marshal` must serialize the complete nested facts through the selected parser. Semantic marshal and reload must preserve path values. `Unmarshal` and `UnmarshalWithConf` must decode the selected path with tag, flat-path, default hook, and conversion behavior supplied by `UnmarshalConf`. If conversion fails, then decode must return an error without changing configuration state; non-Must typed getters must return their documented zero values for absent or incompatible facts.

# Contract

## State Model

A `Koanf` value begins at generation zero with an empty published graph. A semantic direct change moves it to the next published generation; an equivalent or failed change retains the current generation. A live `Snapshot` is an immutable published observation.

A `ReloadTxn` begins open with a base generation and staged copy. Successful staging moves only the staged graph. Commit moves the transaction to committed, stale rejection moves it to stale-closed, and abort moves it to aborted. Every terminal transaction remains closed. A preview is immutable and unpublished; a successful commit produces the next live published generation only when its staged facts differ semantically.

## Error Semantics

| Condition | Required result |
|---|---|
| Provider acquisition or parser failure | The operation must return the underlying error and retain the live or staged last-good graph. |
| Missing parser for byte input | The load must return an error without publication. |
| Merge or explicit change failure | The operation must return an error without a partial graph or generation advance. |
| Stale transaction base | `Commit` must return `ErrStaleGeneration`, close the transaction, and retain the newer live generation. |
| Method on a terminal transaction | The method must return `ErrClosedReload` without changing live or staged facts. |
| Typed decode failure | Decode must return an error without changing the observed graph. |
| Marshal failure | Marshal must return the parser error without changing generation, facts, receipt state, or snapshot state. |

## Cross-View Invariants

1. `Koanf.Generation`, a fresh live `Snapshot.Generation`, and a successful published receipt's `After` must identify the same publication.
2. `Get`, `Exists`, `Keys`, `All`, `Raw`, typed decode, and marshal must describe one fact graph within a live value or snapshot.
3. A snapshot's projections and digest must remain unchanged after any later live or staged operation.
4. A receipt's sorted changes must transform the before snapshot's logical leaves into the after snapshot's logical leaves exactly once.
5. A transaction preview digest must equal the commit receipt digest when that preview commits without intervening changes.
6. A failed staged operation, stale commit, or abort must preserve the live generation, live digest, and every live projection.
7. Equivalent facts loaded through supported local providers and parsers must converge to the same canonical digest and normalized logical paths.
8. A semantic change must advance generation exactly once across direct load, explicit edits, watched reload, and transaction commit.

# Reference

## Public Interface

### Import Surface

- `github.com/knadh/koanf/v2`: `Provider`, `Parser`, `Conf`, `UnmarshalConf`, `Option`, `WithMergeFunc`, `New`, `NewWithConf`, `Koanf`, `Generation`, `ProjectionDigest`, `ChangeKind`, `ChangeAdded`, `ChangeUpdated`, `ChangeRemoved`, `Change`, `MergeReceipt`, `Snapshot`, `ReloadTxn`, `ErrStaleGeneration`, `ErrClosedReload`
- `github.com/knadh/koanf/maps`: `Merge`, `MergeStrict`, `Flatten`, `Unflatten`, `Copy`
- `github.com/knadh/koanf/providers/confmap`: `Provider`
- `github.com/knadh/koanf/providers/rawbytes`: `Provider`
- `github.com/knadh/koanf/providers/file`: `Provider`
- `github.com/knadh/koanf/parsers/json`: `Parser`
- `github.com/knadh/koanf/parsers/yaml`: `Parser`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Provider`, `Parser` | interfaces | Supply nested facts or bytes and convert between bytes and facts. |
| `Conf`, `UnmarshalConf`, `Option`, `WithMergeFunc` | types and function | Configure delimiters, native merge, and typed decode behavior. |
| `New`, `NewWithConf`, `Koanf` | functions and type | Create and own a live published configuration graph. |
| `Koanf.Load`, `Set`, `Delete`, `Merge`, `MergeAt` | methods | Apply native direct changes to the live graph. |
| `Koanf.Get`, `Exists`, `Keys`, `All`, `Raw`, `KeyMap`, `Delim` | methods | Observe live path, flattened, nested, and delimiter projections. |
| `Koanf.String`, `Strings`, `Int`, `Ints`, `Int64`, `Float64`, `Bool`, `Bytes`, `Duration`, `Time` | methods | Return typed live path projections. |
| `Koanf.Copy`, `Cut`, `Slices` | methods | Derive independently owned configuration views. |
| `Koanf.Marshal`, `Unmarshal`, `UnmarshalWithConf` | methods | Serialize or decode the live graph. |
| `Generation`, `Koanf.Generation` | type and method | Identify the current live publication. |
| `ProjectionDigest` | type | Identify one canonical semantic fact graph. |
| `ChangeKind`, `ChangeAdded`, `ChangeUpdated`, `ChangeRemoved` | type and constants | Classify logical leaf changes. |
| `Change`, `Change.Path`, `Change.Kind` | type and fields | Describe one normalized logical leaf change. |
| `MergeReceipt` | type | Describe one attempted direct or transactional publication. |
| `MergeReceipt.Before`, `After`, `Published`, `Changes`, `Digest` | fields | Expose receipt generations, outcome, changes, and after digest. |
| `Koanf.LoadWithReceipt` | method | Apply a direct load and return its semantic publication receipt. |
| `Koanf.Snapshot`, `Snapshot` | method and type | Capture an immutable live generation. |
| `Snapshot.Generation`, `Snapshot.Published`, `Snapshot.Digest` | methods | Identify a snapshot's source state and canonical facts. |
| `Snapshot.Get`, `Exists`, `Keys`, `All`, `Raw` | methods | Observe immutable path, flattened, and nested facts. |
| `Snapshot.Marshal`, `Unmarshal`, `UnmarshalWithConf` | methods | Serialize or decode immutable facts. |
| `Koanf.BeginReload`, `ReloadTxn` | method and type | Start and own an optimistic staged reload. |
| `ReloadTxn.Load`, `Set`, `Delete` | methods | Apply provider and explicit changes to staged facts. |
| `ReloadTxn.Preview`, `ReloadTxn.Commit`, `ReloadTxn.Abort` | methods | Observe, publish, or discard staged facts. |
| `ErrStaleGeneration`, `ErrClosedReload` | error values | Report optimistic conflicts and terminal transaction use. |
| `maps.Merge`, `MergeStrict`, `Flatten`, `Unflatten`, `Copy` | functions | Compose, normalize, and copy nested maps. |
| `confmap.Provider`, `rawbytes.Provider`, `file.Provider` | functions | Create supported local providers. |
| `json.Parser`, `yaml.Parser` | functions | Create supported semantic parsers. |
| `file.File.Watch`, `Unwatch` | methods | Start and stop local file notifications. |

### CLI Entry Points

There is no command-line entry point for this package. Programmatic use is through the Go import paths listed above.

# Meta

## Appendix A: Environment

The working environment runs the pinned Go toolchain on Linux amd64 without network access. The complete dependency closure is supplied in a read-only module cache or vendor tree. Every run receives a new temporary directory and isolated Go build cache. Tests use only evaluator-owned local files, bytes, maps, and bounded file notifications; they do not require a fixed port, service, credential, user configuration, or persistent host path.

The project must retain the module paths named in the import surface. Only those target packages and the supplied dependency closure participate.

## Appendix B: Assessment Notes

Conformance is assessed across direct and staged publication, semantic no-ops, generation conflicts, frozen observations, change classification, digest equivalence, provider and parser composition, typed decode, local reload recovery, and fresh cross-view receipts. Exact debug formatting, map iteration order, notification latency, implementation layout, and synchronization strategy have no contractual meaning.
