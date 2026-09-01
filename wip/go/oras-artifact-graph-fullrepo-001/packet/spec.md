# Artifact graph storage and workflow coordination

## Product Overview

ORAS Go is a library for constructing, storing, copying, and resolving
descriptor-addressed OCI artifact graphs. The supported surface includes
in-memory content, filesystem content, OCI image layouts, repository references,
graph traversal, and a coordination package that publishes durable receipts for
multi-step artifact operations.

### Specification Authority

This document defines the supported public behavior. Exported behavior not
described here is not part of this compatibility surface.

## Non-Goals

- This specification does not require access to a public container registry.
- This specification does not require Docker credential helpers or a user
  credential file.
- This specification does not require command-line programs.
- This specification does not define private storage layout, worker scheduling,
  log text, or exact error messages.
- This specification does not require symbolic-link extraction or platform-
  specific file permission preservation.

## Representative Workflows

### Build, copy, and reopen a local artifact

Create descriptors with `content.NewDescriptorFromBytes`, push their bytes into
`memory.New`, and build a manifest with `oras.Pack`. `oras.Copy` transfers the
reachable graph into a store opened with `oci.New`; tagging the returned root
provides a stable target name. Closing and reopening the layout at the same
directory preserves resolution and byte retrieval for every reachable node.

### Publish an operation receipt

Create a `flow.CopyJournal` and a `flow.Coordinator`, then copy a graph through
the coordinator. The returned descriptor, destination target, predecessor view,
and journal entries describe the same copy. Repeating a copy against an already
complete destination produces skipped entries without reporting those nodes as
new copies.

### Recover a cancelled file ingestion

Create a `flow.FileIngester` over a file or OCI content store and call `Ingest`
with a context. Cancellation returns the context error, removes transaction-
owned temporary data, and leaves target resolution unchanged. A later call with
a live context commits normally and publishes one committed receipt.

## Descriptor and content behavior

Descriptors are the identity boundary for every content operation. Storage
operations preserve content-addressed identity across memory and filesystem
projections.

**Descriptor identity.** `content.NewDescriptorFromBytes` returns a descriptor
whose digest and size describe the supplied bytes and whose media type equals
the caller's media type. `content.Equal` treats descriptors as equal according
to their content identity rather than caller-owned object identity.

**Verified reads.** `content.NewVerifyReader`, `content.ReadAll`, and
`content.FetchAll` return the complete bytes only when the observed length and
digest match the descriptor. A truncated stream, extra data, or a digest
mismatch raises an error and never returns unverified bytes as success.

**Content stores.** `memory.New`, `file.New`, `oci.NewStorage`, and the storage
view of `oci.Store` implement descriptor-addressed `Push`, `Fetch`, and `Exists`.
Successful push followed by fetch returns identical bytes. Pushing an existing
descriptor raises an error wrapping `errdef.ErrAlreadyExists` and preserves the
original bytes. Pushing bytes that do not match the descriptor raises an error
and leaves no newly readable object.

**File names and directories.** A file store associates logical names with
descriptors while retaining content identity. Closing a file store releases its
resources. All paths used by this surface stay beneath the caller-provided
working directory.

## Targets, graphs, and layouts

Targets add names and graph relationships to content. A name is a projection of
a descriptor; changing the projection never changes descriptor identity.

**Tag resolution.** `Tag` associates a name with an existing descriptor and
`Resolve` returns the descriptor currently associated with the name. Repeating
the same tag operation is idempotent. Replacing a name changes subsequent
resolution to the replacement descriptor. Resolving an unknown name raises
`errdef.ErrNotFound` through error wrapping.

**Graph traversal.** `content.Successors` returns the descriptors directly
referenced by a supported manifest or index. `Predecessors` returns descriptors
that directly reference a descriptor. Traversal results contain descriptors,
not decoded private records, and remain consistent after a complete graph copy.

**Packing.** `oras.Pack` and `oras.PackManifest` push a manifest that refers to
the supplied descriptors and return the manifest descriptor. Fetching and
decoding that descriptor exposes the same reachable children and artifact type.
Options control subject, annotations, and manifest version as documented by the
public option records.

**Copying.** `oras.Copy` resolves a source reference, copies every required node,
and tags the destination reference only after the graph is available.
`oras.CopyGraph` copies a descriptor-selected graph without adding a name.
Callbacks in `CopyOptions` and `CopyGraphOptions` observe descriptors at their
documented copy phases. A callback error stops the operation and is returned.

**OCI layouts.** `oci.New` creates or opens a writable OCI image layout.
`oci.NewWithContext` also observes context cancellation. Tags, content,
predecessors, and the index persist across close and reopen. `Untag` removes only
the selected name. `Delete` removes the selected content according to store
reachability rules, while `GC` removes content no longer reachable from layout
targets.

**Repository references.** `registry.ParseReference` accepts an absolute
repository reference with an optional tag or digest and returns its registry,
repository, and reference projections. Invalid or incomplete references raise
an error. `Reference.String`, `Host`, and `ReferenceOrDefault` remain mutually
consistent.

## Relationship receipts

The `flow` package records subject and referrer relationships without replacing
the underlying content graph. Receipts are monotonic observations of committed
relationship changes.

**Recording edges.** `flow.NewReceiptIndex` returns an empty concurrency-safe
index. `Record` accepts a subject descriptor and a referrer descriptor. It
returns an `EdgeReceipt` with both descriptors, `Present=true`, and the revision
that made the relationship visible. Recording an already visible relationship
returns the existing logical relationship without duplicating either view.

**Removing edges.** `Remove` accepts a referrer descriptor. For a visible edge
it removes the referrer from its subject and returns an `EdgeReceipt` with
`Present=false` and a later revision. Removing an unknown referrer raises
`errdef.ErrNotFound` and leaves the revision unchanged.

**Querying edges.** `Referrers` returns a deterministic descriptor list for a
subject. `Subject` returns the subject and `true` for a visible referrer, or a
zero descriptor and `false` otherwise. Returned slices are caller-owned
snapshots. For every visible edge, the subject and referrer queries agree.

## Copy receipts and target history

Copy and retarget transactions publish receipts after their public effects
become observable.

**Copy journal.** `flow.NewCopyJournal` returns an empty concurrency-safe
journal. `Record` appends a `CopyReceipt` containing a descriptor, a
`CopyDisposition`, an optional source name, and a strictly increasing sequence.
The supported dispositions are `Copied`, `Skipped`, and `Mounted`. `Entries`
returns an ordered caller-owned snapshot; `Counts` returns totals that equal the
entries by disposition.

**Coordinated graph copy.** `flow.NewCoordinator` binds a journal. Its `CopyGraph`
operation delegates descriptor transfer through the public ORAS graph/storage
interfaces and records exactly one terminal disposition for every visited
descriptor. A descriptor already available at the destination is skipped. A
successful cross-repository mount is mounted. All other committed transfers are
copied. An error returns without recording an uncommitted descriptor as copied.

**Retarget transactions.** `flow.NewRetargeter` binds a `flow.TagStore`. `Retarget`
associates a name with a descriptor and returns a `RetargetReceipt` containing
the name, previous descriptor when present, current descriptor, orphan status,
and revision. `Untag` removes a name and returns the same receipt shape with no
current descriptor. `History` returns an ordered snapshot for a name.

**Reachability preservation.** Retargeting or untagging changes the name view
only. Content that remains reachable from another name or graph edge stays
fetchable and copyable. If the underlying tag operation fails, resolution,
history, and revision remain unchanged.

## Transactional ingestion and layout recovery

Ingestion and recovery make failure boundaries observable without exposing
temporary filenames or internal algorithms.

**Verified ingestion.** `flow.NewVerifier` binds a `content.Storage`. `Push`
accepts a descriptor and reader, verifies the full stream, and returns an
`IngestReceipt`. Success sets `Committed=true` and reports the descriptor and
byte count. A mismatch or storage error returns an error, leaves
`Committed=false`, and makes no transaction-created partial object readable.
Retrying with correct bytes produces one committed result.

**Cancellation-safe files.** `flow.NewFileIngester` binds a store and temporary
directory. `Ingest` has the same receipt contract as verified ingestion and
observes its context before commit. Cancellation returns `context.Canceled` or
`context.DeadlineExceeded`, removes transaction-owned temporary data, and never
changes a target name. Cancellation after all bytes are staged but before
commit has the same public result.

**Layout reconciliation.** `flow.ReopenLayout` opens an OCI layout and returns
the store plus a `RepairReceipt`. The receipt lists names removed because their
descriptor is absent, the missing descriptors that caused removal, and whether
public state changed. Invalid index entries never become resolvable. Running
reconciliation again without an intervening change returns
`Changed=false` and empty repair lists.

## Bounded page traversal

Bounded traversal converts untrusted continuation streams into deterministic,
finite snapshots.

**Page sources.** `flow.TagPageSource` returns one tag page and its continuation
cursor. `flow.ReferrerPageSource` returns one descriptor page and its cursor.
An empty cursor terminates traversal.

**Budgets and loops.** `flow.NewPager` requires a positive page budget.
`CollectTags` and `CollectReferrers` visit pages until termination. They retain
first-seen order while removing duplicates. Exceeding the budget raises
`flow.ErrPageBudget`. Repeating any non-empty cursor raises `flow.ErrCursorLoop`.
Both failures return no successful collection and stop requesting pages.

**Context.** Page collection observes cancellation before each request and
before returning success. A context error takes precedence over making another
page request.

## State Model

The core fact source is a set of descriptor-addressed bytes plus directed
descriptor edges. Public state is visible through content existence and fetch,
target resolution, successor/predecessor traversal, OCI index persistence,
relationship queries, ordered operation journals, retarget history, repair
receipts, and bounded page results.

Receipts use monotonically increasing revisions or sequences within their owner.
Failed operations do not advance those counters. Snapshot-returning methods
return caller-owned values and never expose later changes through an earlier
slice or map.

## Error Semantics

| Condition | Required result |
|---|---|
| Unknown target or relationship | An error wrapping `errdef.ErrNotFound` |
| Descriptor digest or size mismatch | Verification error; no successful bytes or commit receipt |
| Copy callback or storage failure | The original error remains discoverable through wrapping; no false copied receipt |
| Failed tag, untag, or retarget | Name, history, and revision remain unchanged |
| Cancelled ingestion or page traversal | `context.Canceled` or `context.DeadlineExceeded` |
| Repeated non-empty page cursor | `flow.ErrCursorLoop` |
| Page count exceeds its positive budget | `flow.ErrPageBudget` |
| Non-positive page budget | Constructor error |
| Malformed repository reference | Parse error; no partial `registry.Reference` contract |

Error strings are not part of the contract.

## Cross-View Invariants

1. Bytes accepted for a descriptor through any supported store match verified
   fetch through that descriptor.
2. A target returned by `Resolve` is fetchable from the same target, unless a
   later successful delete operation removed the content.
3. A graph copied into another store preserves every reachable descriptor and
   direct edge observed from the copied root.
4. The total of copy-journal counts equals the number of journal entries, and
   each visited descriptor has exactly one terminal disposition.
5. Subject-to-referrer and referrer-to-subject relationship queries describe
   the same visible edge set after every successful record or remove operation.
6. A retarget receipt, current resolution, and history tail describe the same
   committed name change.
7. A failed or cancelled ingestion creates neither readable partial content nor
   a target/history/journal claim of success.
8. Reopening a reconciled OCI layout preserves content and names, and a second
   reopen without intervening changes reports no further repair.
9. Bounded tag and referrer collection returns unique first-seen values or an
   error; it never returns a successful partial collection.
10. Copying a referrer graph preserves both graph traversal and relationship
    receipt projections at the destination.

## Public Interface

### Import Surface

```go
import (
    oras "oras.land/oras-go/v2"
    "oras.land/oras-go/v2/content"
    "oras.land/oras-go/v2/content/file"
    "oras.land/oras-go/v2/content/memory"
    "oras.land/oras-go/v2/content/oci"
    "oras.land/oras-go/v2/errdef"
    "oras.land/oras-go/v2/flow"
    "oras.land/oras-go/v2/registry"
    "oras.land/oras-go/v2/registry/remote"
)
```

The public records use
`github.com/opencontainers/image-spec/specs-go/v1.Descriptor`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `oras.Pack` | function | Builds and pushes an artifact manifest |
| `oras.PackManifest` | function | Builds a selected OCI manifest version |
| `oras.Copy` | function | Copies a named artifact between targets |
| `oras.CopyGraph` | function | Copies a descriptor-selected graph |
| `oras.CopyOptions` | record | Configures named copy callbacks and graph behavior |
| `oras.CopyGraphOptions` | record | Configures graph-copy callbacks and concurrency |
| `oras.Target` | interface | Combines storage and tag resolution for writes |
| `oras.ReadOnlyTarget` | interface | Combines fetch and resolution for reads |
| `content.NewDescriptorFromBytes` | function | Derives descriptor identity from bytes |
| `content.NewVerifyReader` | function | Wraps a stream with descriptor verification |
| `content.ReadAll` | function | Reads and verifies a descriptor-bound stream |
| `content.FetchAll` | function | Fetches and verifies descriptor content |
| `content.Successors` | function | Lists directly referenced descriptors |
| `content.Storage` | interface | Pushes and fetches descriptor-addressed bytes |
| `content.GraphStorage` | interface | Adds predecessor traversal to storage |
| `memory.New` | function | Creates an in-memory graph target |
| `file.New` | function | Creates a filesystem content target |
| `oci.New` | function | Creates or opens a writable OCI layout |
| `oci.NewWithContext` | function | Opens a writable OCI layout with cancellation |
| `oci.NewStorage` | function | Creates descriptor storage for an OCI layout |
| `oci.NewFromFS` | function | Opens a read-only layout from an `fs.FS` |
| `oci.NewFromTar` | function | Opens a read-only OCI layout archive |
| `registry.Reference` | record | Exposes registry, repository, and reference views |
| `registry.ParseReference` | function | Parses an absolute repository reference |
| `registry.Tags` | function | Collects repository tags |
| `registry.Referrers` | function | Collects descriptors referring to a subject |
| `registry.TagLister` | interface | Streams tag pages |
| `registry.ReferrerLister` | interface | Streams referrer pages |
| `remote.NewRepository` | function | Creates a remote repository client |
| `flow.EdgeReceipt` | record | Describes a relationship revision and visibility |
| `flow.ReceiptIndex` | type | Owns bidirectional subject/referrer receipts |
| `flow.NewReceiptIndex` | function | Creates an empty relationship index |
| `flow.CopyDisposition` | type | Classifies copied, skipped, or mounted nodes |
| `flow.Copied` | constant | Marks a committed byte transfer |
| `flow.Skipped` | constant | Marks a node already present at the destination |
| `flow.Mounted` | constant | Marks a committed cross-repository mount |
| `flow.CopyReceipt` | record | Describes one terminal graph-copy observation |
| `flow.CopyJournal` | type | Owns ordered copy receipts and counts |
| `flow.NewCopyJournal` | function | Creates an empty copy journal |
| `flow.Coordinator` | type | Couples graph copy with terminal receipts |
| `flow.NewCoordinator` | function | Creates a coordinator over a journal |
| `flow.TagStore` | interface | Provides resolve, tag, untag, and reachability views |
| `flow.RetargetReceipt` | record | Describes a committed name transition |
| `flow.Retargeter` | type | Owns atomic target changes and history |
| `flow.NewRetargeter` | function | Creates a retarget transaction owner |
| `flow.IngestReceipt` | record | Describes verified ingest outcome and byte count |
| `flow.Verifier` | type | Owns descriptor-verifying storage commits |
| `flow.NewVerifier` | function | Creates a verifier over content storage |
| `flow.FileIngester` | type | Owns cancellation-safe staged ingestion |
| `flow.NewFileIngester` | function | Creates a file ingester with a temporary directory |
| `flow.RepairReceipt` | record | Describes public OCI layout repairs |
| `flow.ReopenLayout` | function | Opens and reconciles a writable OCI layout |
| `flow.TagPageSource` | interface | Supplies one tag page and continuation cursor |
| `flow.ReferrerPageSource` | interface | Supplies one referrer page and continuation cursor |
| `flow.Pager` | type | Collects bounded, de-duplicated page streams |
| `flow.NewPager` | function | Creates a pager with a positive page budget |
| `flow.ErrCursorLoop` | variable | Identifies a repeated continuation cursor |
| `flow.ErrPageBudget` | variable | Identifies a page-budget overflow |

There is no console script in this compatibility surface.

## Appendix A: Environment

The working environment runs Go 1.25 on Linux without network access. The
pinned module closure for ORAS Go and its OpenContainers dependencies is
available locally. Implementations use ordinary Go module metadata and do not
download tools or modules during execution.

## Appendix B: Assessment Notes

Compatibility is defined by public outcomes across content, targets, graphs,
receipts, persistence, cancellation, and bounded traversal. Private structs,
goroutine counts, callback implementation order beyond the documented phases,
exact error text, and formatting are not part of the contract.
