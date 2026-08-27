# go-containerregistry Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in interface design, parameter naming, behavioral edge cases, and error semantics.
> Implementations derived from memory of external codebases will fail the evaluation.

# Context

## Product Overview

`go-containerregistry` is a Go library and command suite that models container layers, images, indexes, descriptors, references, local layouts, tar archives, and registry transport as one content-addressed graph. Callers inspect the graph through structured manifests and configs, transform it through immutable image operations, persist it locally, and publish or retrieve it through an OCI-compatible HTTP registry.

Digest, size, media type, platform, and descriptor metadata form the public identity contract. Local and HTTP projections must preserve that identity when their bytes and metadata are unchanged.

## Non-Goals

- This specification does not require a container daemon, cloud registry, credential helper, or public network service.
- This specification does not define operating-system execution of an image filesystem.
- This specification does not require undocumented transport internals, retry timing, or process-global caches.

# Orientation

## Representative Workflows

### Workflow 1: Build and persist an image graph

1. Create compressed layer bytes with `static.NewLayer` and begin with `empty.Image`.
2. Append layers and update config metadata with the `mutate` package.
3. Validate the image, then observe its manifest, config, descriptors, digest, diff IDs, media types, and size.
4. Write the image to an OCI layout and a tar archive.
5. Reopen each local representation and compare its structured graph and content identity.

### Workflow 2: Publish and retrieve through a local registry

1. Start `registry.New` on an operating-system-selected loopback address.
2. Parse a tag with `name.ParseReference` or `name.NewTag`.
3. Publish an image with `remote.Write` or `crane.Push`.
4. Retrieve the descriptor with `remote.Get`, then load the image with `remote.Image` or `crane.Pull`.
5. Observe the retrieved manifest, config, layers, platform, and digest from a fresh client request.
6. Capture local and retrieved graphs into `receipt.GraphReceipt` values and reconcile their semantic identities.

# Behavior

## Domain 1: References, Hashes, and Descriptor Identity

This domain defines the names and content identities that connect every image projection.

**Reference normalization.** When `ParseReference`, `NewTag`, `NewDigest`, `NewRepository`, or `NewRegistry` receives valid input, it must return a normalized value whose `String`, `Name`, `Context`, and `Identifier` views agree. Where default registry or default tag options are present, normalization must insert those defaults. Where strict validation is present, invalid case, separators, tags, or digest syntax must return `ErrBadName`; `MustParseReference` must panic for the same invalid input.

**Hash identity.** When `NewHash` receives a supported algorithm and correctly encoded digest, it must return a `Hash` whose string form round-trips through text and JSON. When `SHA256` reads content, it must return the hash and the exact number of bytes consumed. If algorithm or encoding is invalid, then hash construction must return an error.

**Descriptors and platforms.** When a layer, image, or index publishes a descriptor, its digest, size, and media type must describe the same bytes returned by the corresponding raw projection. Where platform matching is requested, `Platform.Equals`, `Platform.Satisfies`, and platform matchers must apply operating system, architecture, variant, version, and features consistently. If no child descriptor satisfies a requested platform, then selection must return an error rather than an unrelated child.

## Domain 2: Image Graph Construction and Validation

This domain defines immutable graph changes and the relationships among config, manifest, layers, images, and indexes.

**Layer and image construction.** When `static.NewLayer` receives compressed bytes and a media type, the resulting `Layer` must expose those compressed bytes, their digest, uncompressed diff identity, size, and media type. When `mutate.AppendLayers` appends layers, it must preserve prior layer order, append new descriptors in argument order, and update config diff IDs to the corresponding uncompressed content. If a layer cannot expose required content or identity, then the operation must return an error and leave the source image unchanged.

**Config and manifest changes.** When `mutate.Config`, `mutate.ConfigFile`, `mutate.Annotations`, `mutate.MediaType`, or `mutate.CreatedAt` changes an image, it must return a new image projection and preserve unrelated graph facts. When `mutate.AppendManifests` adds index entries, it must retain supplied descriptor annotations and platform metadata. If requested media types are incompatible with the target object, then the change must return an error.

**Validation.** When `validate.Image`, `validate.Index`, or `validate.Layer` succeeds, every referenced blob must have matching digest and size, every required manifest/config relation must resolve, and layer compressed/uncompressed identities must agree. If any required blob is missing, truncated, or mislabeled, then validation must return a descriptive error.

## Domain 3: Local Persistence and Registry Transport

This domain defines how one content graph survives layout, tar, API, CLI, and HTTP boundaries.

**OCI layout.** When `layout.Write` creates a layout, it must persist the index, manifests, configs, and blobs required by the supplied `ImageIndex`. When `Path.AppendImage`, `AppendIndex`, `ReplaceImage`, or `ReplaceIndex` succeeds, a fresh `FromPath` and `ImageIndex` read must observe the updated descriptor set. If a required blob is absent or corrupt, then layout access must return an error and must not synthesize content.

**Tar archives.** When `tarball.Write` or `crane.Save` writes an image, reopening it with `tarball.ImageFromPath` or `crane.Load` must preserve config, layer order, and content identities. If the archive has invalid metadata, duplicate conflicts, or missing layer content, then loading must return an error.

**Registry transport.** When `remote.Write`, `WriteIndex`, or `WriteLayer` publishes to a registry, a later `Get`, `Head`, `Image`, `Index`, or `Layer` request must return matching descriptor identity and graph content. Where `WithTransport`, `WithContext`, `WithJobs`, or authentication options are present, every request must use the supplied option. If the context is canceled, the server rejects the request, or returned bytes fail identity checks, then the operation must return an error and must not return a successful graph.

**Crane parity.** When `crane.Pull`, `Push`, `Manifest`, `Config`, `Digest`, `Save`, or `Load` performs an operation, it must preserve the same graph and error semantics as the corresponding package APIs. CLI commands must use the same reference normalization and must exit nonzero on invalid input or failed transport.

## Domain 4: Graph Receipts and Transfer Reconciliation

This domain defines a stable observation layer across in-memory images, indexes, local persistence, and registry transfers.

**Graph plans.** `receipt.NewGraphPlan` must return an empty caller-owned plan. `GraphPlan.SelectImage` and `SelectIndex` must associate stable names with graph objects, while `IncludeLayers`, `IncludeRawJSON`, and `IncludeTransfers` must select complete projections. Repeating a name must replace the graph without changing its original position. Empty names, nil objects, and conflicting selections must return an error without changing the preceding plan.

**Graph capture.** `receipt.Capture` must execute one plan and return one complete `GraphReceipt`. `ImageFact`, `IndexFact`, and `LayerFact` must reconcile structured descriptors with manifest, config, compressed, and uncompressed identities. `TransferFact` values must come from a caller-owned `TransferJournal` and must preserve reference, direction, descriptor, completion, and failure boundary. If validation or any selected projection fails, then capture must return an error and no partial receipt.

**Normalization and comparison.** `GraphReceipt.Validate` must reject missing children, descriptor mismatches, order divergence, platform contradictions, or transfer outcomes that disagree with the captured graph. `Digest` must derive from normalized semantic content and ignore temporary paths, HTTP timing, and JSON object order. `Equivalent` and `receipt.Diff` must compare independent memory, layout, tar, registry, and crane observations without changing either input.

**Transfer journal.** `receipt.NewTransferJournal` must create an empty ordered journal. `Record` must append one caller-owned `TransferFact` with a strictly increasing sequence, and `Entries` must return an independent snapshot. Failed or canceled transfers must remain distinguishable from committed transfers and must not claim a completed graph.

# Contract

## State Model

A content object progresses through **bytes available**, **layer identified**, **image assembled**, **index assembled**, **validated**, **persisted**, **published**, and **freshly retrieved** states. Graph change functions return new projections and do not alter the source object. Layout and registry writes become observable only after all required content for the published descriptor is available.

Public projections are compressed and uncompressed layer streams, hashes, config files, manifests, descriptors, indexes, layout files, tar archives, HTTP responses, crane results, and returned errors. Each successful receipt must refer to one coherent content graph.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid repository, tag, digest, or registry syntax | Name construction must return `ErrBadName`; the Must-prefixed parser must panic. |
| Unsupported or malformed hash | `NewHash` must return an error. |
| Missing or corrupt layer/blob content | Access and validation must return an error without a successful descriptor receipt. |
| Config and manifest inconsistency | Image validation must return an error. |
| Platform selection without a match | Selection must return an error. |
| Invalid layout or tar archive | Local loading must return an error without a partial graph. |
| HTTP rejection or identity mismatch | Remote operations must return the transport or verification error. |
| Canceled context | Remote and crane operations must return the context error. |

## Cross-View Invariants

1. A descriptor digest and size must agree with the raw bytes returned by image, index, layer, layout, tar, and HTTP projections.
2. Manifest layer order and config diff-ID order must remain aligned after append, persistence, publication, and retrieval.
3. Structured config and manifest values must agree with their raw JSON projections.
4. Image and index media types must agree across graph interfaces, descriptors, local layouts, tar archives, and registry responses.
5. Platform selection through matchers, index descriptors, remote loading, and crane options must choose the same child.
6. Graph changes must preserve source-object observations while the returned object publishes updated identity.
7. A fresh local or HTTP read after a successful write must observe the same content graph as the write receipt.
8. Validation failure must prevent layout, tar, remote, and crane projections from reporting a successful verified image.
9. A graph receipt must reconcile selected image, index, layer, raw, and transfer facts under one content generation.
10. Equivalent image graphs must produce equal receipt digests across memory, OCI layout, tar archive, registry, and crane projections.

# Reference

## Public Interface

### Import Surface

- `github.com/google/go-containerregistry/pkg/name`: `Reference`, `Tag`, `Digest`, `Repository`, `Registry`, `ParseReference`, `MustParseReference`, `NewTag`, `NewDigest`, `NewRepository`, `NewRegistry`, `StrictValidation`, `WeakValidation`, `Insecure`, `WithDefaultRegistry`, `WithDefaultTag`, `ErrBadName`
- `github.com/google/go-containerregistry/pkg/v1`: `Layer`, `Image`, `ImageIndex`, `Hash`, `NewHash`, `SHA256`, `Descriptor`, `Manifest`, `IndexManifest`, `ConfigFile`, `Config`, `Platform`, `ParsePlatform`
- `github.com/google/go-containerregistry/pkg/v1/static`: `NewLayer`
- `github.com/google/go-containerregistry/pkg/v1/empty`: `Image`, `Index`
- `github.com/google/go-containerregistry/pkg/v1/mutate`: `AppendLayers`, `Config`, `ConfigFile`, `Annotations`, `MediaType`, `CreatedAt`, `IndexAddendum`, `AppendManifests`
- `github.com/google/go-containerregistry/pkg/v1/validate`: `Image`, `Index`, `Layer`, `Fast`
- `github.com/google/go-containerregistry/pkg/v1/layout`: `Path`, `FromPath`, `Write`, `ImageIndexFromPath`, `WithAnnotations`, `WithURLs`, `WithPlatform`
- `github.com/google/go-containerregistry/pkg/v1/tarball`: `Write`, `WriteToFile`, `ImageFromPath`, `Image`, `MultiRefWrite`
- `github.com/google/go-containerregistry/pkg/v1/remote`: `Descriptor`, `Get`, `Head`, `Image`, `Index`, `Layer`, `Write`, `WriteIndex`, `WriteLayer`, `WithTransport`, `WithContext`, `WithJobs`
- `github.com/google/go-containerregistry/pkg/registry`: `New`
- `github.com/google/go-containerregistry/pkg/crane`: `Pull`, `Push`, `Manifest`, `Config`, `Digest`, `Save`, `Load`, `WithTransport`, `WithContext`, `WithPlatform`, `WithJobs`
- `github.com/google/go-containerregistry/pkg/v1/receipt`: `GraphPlan`, `NewGraphPlan`, `ImageFact`, `IndexFact`, `LayerFact`, `TransferFact`, `TransferJournal`, `NewTransferJournal`, `GraphReceipt`, `ChangeReceipt`, `Capture`, `Diff`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `name.Reference`, `Tag`, `Digest`, `Repository`, `Registry` | interfaces and types | Represent normalized registry names and identifiers. |
| `name.ParseReference`, `MustParseReference`, `NewTag`, `NewDigest`, `NewRepository`, `NewRegistry` | functions | Parse and construct named references. |
| `name.StrictValidation`, `WeakValidation`, `Insecure`, `WithDefaultRegistry`, `WithDefaultTag` | options | Select name validation and defaults. |
| `name.ErrBadName` | error type | Reports invalid name syntax. |
| `v1.Layer`, `Image`, `ImageIndex` | interfaces | Expose the content graph. |
| `v1.Hash`, `NewHash`, `SHA256` | type and functions | Represent and compute content identity. |
| `v1.Descriptor`, `Manifest`, `IndexManifest`, `ConfigFile`, `Config`, `Platform`, `ParsePlatform` | types and function | Expose structured graph metadata. |
| `static.NewLayer`, `empty.Image`, `empty.Index` | function and values | Create initial graph objects. |
| `mutate.AppendLayers`, `Config`, `ConfigFile`, `Annotations`, `MediaType`, `CreatedAt`, `AppendManifests` | functions | Return changed image or index projections. |
| `mutate.IndexAddendum` | type | Couples an index child with descriptor metadata. |
| `validate.Image`, `Index`, `Layer`, `Fast` | functions and option | Verify graph consistency. |
| `layout.Path`, `FromPath`, `Write`, `ImageIndexFromPath` | type and functions | Read and write OCI layouts. |
| `layout.WithAnnotations`, `WithURLs`, `WithPlatform` | functions | Configure layout descriptors. |
| `tarball.Write`, `WriteToFile`, `ImageFromPath`, `Image`, `MultiRefWrite` | functions | Read and write image tar archives. |
| `remote.Descriptor`, `Get`, `Head`, `Image`, `Index`, `Layer` | type and functions | Retrieve remote descriptors and content. |
| `remote.Write`, `WriteIndex`, `WriteLayer` | functions | Publish graph objects. |
| `remote.WithTransport`, `WithContext`, `WithJobs` | functions | Configure transport operations. |
| `registry.New` | function | Create an in-process registry handler. |
| `crane.Pull`, `Push`, `Manifest`, `Config`, `Digest`, `Save`, `Load` | functions | Provide high-level graph operations. |
| `crane.WithTransport`, `WithContext`, `WithPlatform`, `WithJobs` | functions | Configure high-level operations. |

| `v1.Layer.Digest`, `DiffID`, `Compressed`, `Uncompressed`, `Size`, `MediaType` | methods | Observe compressed and uncompressed layer identity and content. |
| `v1.Image.Layers`, `MediaType`, `Size`, `ConfigName`, `ConfigFile`, `RawConfigFile`, `Digest`, `Manifest`, `RawManifest`, `LayerByDigest`, `LayerByDiffID` | methods | Observe one image graph through structured and raw projections. |
| `v1.ImageIndex.MediaType`, `Digest`, `Size`, `IndexManifest`, `RawManifest`, `Image`, `ImageIndex` | methods | Observe an index and resolve its children. |
| `layout.Path.Image`, `ImageIndex`, `Blob`, `Bytes`, `AppendImage`, `AppendIndex`, `ReplaceImage`, `ReplaceIndex` | methods | Read and change an OCI layout. |
| `name.Reference.Context`, `Identifier`, `Name`, `String` | methods | Expose normalized name components. |
| `v1.Platform.Equals`, `Satisfies`, `String` | methods | Compare and format platform constraints. |
| `receipt.GraphPlan`, `receipt.NewGraphPlan` | type and function | Select named images indexes and complete graph projections. |
| `receipt.GraphPlan.SelectImage`, `receipt.GraphPlan.SelectIndex`, `receipt.GraphPlan.IncludeLayers`, `receipt.GraphPlan.IncludeRawJSON`, `receipt.GraphPlan.IncludeTransfers` | methods | Build a stable caller-owned graph observation plan. |
| `receipt.ImageFact`, `receipt.IndexFact`, `receipt.LayerFact`, `receipt.TransferFact` | records | Normalize structured graph content and transfer outcomes. |
| `receipt.TransferJournal`, `receipt.NewTransferJournal` | type and function | Own ordered registry and local transfer observations. |
| `receipt.TransferJournal.Record`, `receipt.TransferJournal.Entries` | methods | Append transfer outcomes and return independent ordered snapshots. |
| `receipt.GraphReceipt`, `receipt.Capture` | type and function | Capture one complete image graph across selected projections. |
| `receipt.GraphReceipt.Validate`, `receipt.GraphReceipt.Digest`, `receipt.GraphReceipt.Equivalent` | methods | Reconcile and compare normalized content generations. |
| `receipt.ChangeReceipt`, `receipt.Diff` | type and function | Describe semantic additions removals and changes between graph receipts. |

### CLI Entry Points

| Command | Role | Success | Failure |
|---|---|---|---|
| `crane pull` | Save a referenced image locally. | Exit 0 after a complete archive is written. | Exit nonzero on invalid reference, transport, or archive failure. |
| `crane push` | Publish a local image archive. | Exit 0 after registry publication succeeds. | Exit nonzero on invalid input or publication failure. |
| `crane manifest`, `crane config`, `crane digest` | Observe a referenced image. | Exit 0 with the requested projection. | Exit nonzero when retrieval or parsing fails. |
| `crane validate` | Validate a local or referenced image. | Exit 0 for a consistent graph. | Exit nonzero with a validation error. |

# Meta

## Appendix A: Environment

The working environment runs Go 1.25 on Linux without public network access. All registry interaction targets an in-process loopback handler. OCI layouts, archives, and blob content use temporary directories supplied by the caller. A container daemon and cloud credentials are absent.

## Appendix B: Assessment Notes

Conformance is assessed across reference normalization, descriptor identity, layer compression, image and index changes, platform selection, validation, layout and tar round trips, local registry publication, retry-visible failure, and crane/API parity. Exact temporary paths, JSON object key order, retry delay, and undocumented implementation structure have no contractual meaning.

