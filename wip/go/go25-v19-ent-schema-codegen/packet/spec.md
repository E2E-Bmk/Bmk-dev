# Ent Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in interface design, parameter naming, behavioral edge cases, and error semantics.
> Implementations derived from memory of external codebases will fail the evaluation.

# Context

## Product Overview

`ent` is a Go schema compiler that turns declarative entities into a normalized graph, generated Go packages, relational table descriptions, and runtime client behavior. Fields, edges, indexes, mixins, and annotations begin as schema facts; loading validates them, graph construction resolves cross-schema ownership, and generation emits one compilable API generation.

Generated source is a semantic projection. Harmless layout differences do not change the required declarations, methods, relationships, storage facts, or driver operations.

## Non-Goals

- This specification does not require a live SQL server, cloud database, or network service.
- This specification does not define byte identity for generated Go source or SQL formatting.
- This specification does not require optional graph backends, remote schema registries, or undocumented generator internals.
- This specification does not require every extension or feature flag.

# Orientation

## Concepts and Terms

A **schema declaration** is a Go type implementing `ent.Interface` through `ent.Schema` methods. A **descriptor** is the field, edge, or index record produced by a builder. A **normalized graph** resolves names, inverse edges, indexes, ID policy, mixins, and annotations. An **artifact generation** is the complete file set emitted from one graph. A **table projection** is the relational description returned by `gen.Graph.Tables`.

Generated identifier families derive from schema type and member names. For a schema type named `T`, the generated package exposes entity `T`, its client, create/query/update/delete builders, predicates, and member constants under the documented naming rules.

## Representative Workflows

### Workflow 1: Load, generate, and compile

1. Define multiple schema types with fields, a paired edge, and an index.
2. Load the schema package with `entc.LoadGraph`.
3. Observe normalized graph and relational table projections.
4. Generate the complete Go artifact set with `entc.Generate` or `gen.Graph.Gen`.
5. Compile a new consumer package against the generated public names.

A successful workflow must publish one coherent graph and one compilable artifact generation.

### Workflow 2: Evolve storage and observe a driver operation

1. Load an initial schema graph and obtain its table projection.
2. Load a changed schema family with field or index changes allowed by the declared safety policy.
3. Derive the ordered relational changes through the public migration surface.
4. Apply the plan to a caller-owned driver or inspect the planned tables.
5. Construct a new generated client operation and observe its public driver call.
6. Capture the graph, artifacts, tables, and driver journal as one `receipt.GenerationReceipt`, then compare it with a later generation.

Graph, generated API, table description, and driver observation must agree on names, types, nullability, identity, and relationship ownership.

# Behavior

## Domain 1: Schema DSL and Graph Normalization

This domain defines how independently declared schema facts become one validated cross-schema graph.

**Fields.** When a field builder publishes its `Descriptor`, the descriptor must retain name, type information, optionality, nillability, uniqueness, immutability, default ownership, storage key, validation, tags, and annotations selected by builder methods. Optionality must control write requirements, while nillability must control pointer representation. If field flags conflict, a validator is invalid, an enum is malformed, or storage identity is duplicated, then loading must return an error before graph publication.

**Edges.** When `edge.To` declares an association or `edge.From` with `Ref` declares its inverse, normalization must resolve a paired edge to one relationship with consistent direction, cardinality, field binding, and storage key. Where `Required`, `Unique`, `Immutable`, `Field`, `Through`, or `StorageKey` is present, the resulting descriptor must preserve that selection. If the referenced schema, inverse name, bound field, or cardinality is incompatible, then loading must return an error without a usable graph.

**Indexes and mixins.** When `index.Fields` or `index.Edges` declares an index, every referenced member must belong to the receiving schema, and composite order must remain stable. When a mixin contributes fields, edges, indexes, hooks, or annotations, normalization must merge them under documented schema-local precedence. If contributed and local names conflict incompatibly, then loading must return an error.

## Domain 2: Artifact Generation and Compilation

This domain defines the transition from a normalized graph to one coherent, compilable public Go API.

**Loading and publication.** When `entc.LoadGraph` succeeds, it must return a complete normalized `gen.Graph`. If package loading or normalization fails, then it must return an error and no partial graph. When `entc.Generate` or `gen.Graph.Gen` succeeds, it must publish one complete artifact generation under the configured target and package.

**Generated API.** When a schema graph is generated, each schema type must produce its entity, client, create/query/update/delete builders, predicates, field constants, and edge methods under the documented naming rules. Field optionality, nillability, immutability, uniqueness, defaults, enums, custom IDs, and edge cardinality must agree across entity fields and builder methods. If any generated declaration fails Go compilation, then generation must not report a successful artifact generation.

**Artifact stability and commands.** When equal schema facts and equal generation options are supplied, exported names, signatures, descriptor facts, table facts, and runtime call ownership must remain semantically equal. `ent generate` and `ent describe` must load the same graph rules as the Go API. If generation fails, then newly produced files must not form a mixed semantic generation with stale owners.

## Domain 3: Table Planning and Driver Receipts

This domain defines the relational projection, ordered schema changes, and runtime calls issued by generated clients.

**Tables.** When `gen.Graph.Tables` derives relational tables, it must preserve table names, columns, indexes, primary keys, foreign keys, custom IDs, storage keys, inverse-edge ownership, optionality, and uniqueness from the normalized graph. If the graph contains an unsupported relational fact, then table derivation must return an error instead of an incomplete table set.

**Change planning.** When old and new semantic table sets are compared, the plan must order prerequisites before dependents and must apply destructive operations only where policy enables them. If a change is unsafe under the active policy or driver application fails, then planning or application must return an error and the preceding inspected state must remain current.

**Generated driver calls.** When a generated client operation reaches `dialect.Driver`, the call must preserve operation ownership, selected table and columns, relationship storage, arguments, and transaction boundaries. If the driver returns an error, then the generated client must return that error without a successful entity, count, or transaction result.

## Domain 4: Generation Receipts and Reconciliation

This domain defines a stable public observation layer that reconciles schema graphs with generated and runtime projections.

**Observation plans.** `receipt.NewPlan` must return an empty caller-owned plan. `Plan.SelectNode` must select a schema type by name, while `IncludeTables`, `IncludeArtifacts`, and `IncludeDriverCalls` must enable complete relational, generated-source, and driver-journal projections. Repeating a selection must retain its original order. Empty names, conflicting selections, and nil inputs must return an error without changing the preceding plan.

**Generation capture.** `receipt.Capture` must read a complete `gen.Graph` under one plan and return one `GenerationReceipt`. Selected node facts must preserve fields, edges, indexes, mixin provenance, annotations, ID policy, and normalized order. Table facts must derive from `gen.Graph.Tables`; artifact facts must describe exported declarations from one complete generation; driver facts must come from a caller-owned `DriverJournal`. If a selected projection fails, then capture must return an error and no partial receipt.

**Validation and comparison.** `GenerationReceipt.Validate` must reject contradictions between nodes, tables, artifacts, and driver facts. `Digest` must derive from normalized semantic facts rather than source layout, temporary paths, SQL formatting, or map iteration order. `Equivalent` must compare normalized facts, and `receipt.Diff` must return a `ChangeReceipt` whose additions, removals, and changes reconcile old and new receipts without mutating either input.

**Driver journal.** `receipt.NewDriverJournal` must create an empty ordered journal. `Record` must append a caller-owned `DriverFact` with a strictly increasing sequence, and `Entries` must return an independent snapshot. Failed transactions must remain distinguishable from committed operations, and changing a returned entry must not change later observations.

# Contract

## State Model

A schema family moves through **declared**, **loaded**, **normalized**, **generated**, **planned**, and **observed** states. **Rejected** describes an operation that returned an error and published no later successful state. Repeated loading of equal declarations creates an independent but semantically equivalent graph.

Public projections are builder descriptors, loaded schema records, normalized graph nodes, generated identifiers, generated Go artifacts, relational tables, ordered changes, command descriptions, driver calls, transaction boundaries, and returned errors. Each successful generation must connect all projections to one graph generation.

## Error Semantics

| Condition | Required result |
|---|---|
| Unknown schema or inverse edge | Loading must return an error and no usable graph. |
| Missing index member or duplicate schema member | Loading must return an error before normalization publication. |
| Invalid field flags, enum, validator, or type | Descriptor loading must return an error. |
| Package load failure | `entc.LoadGraph` must return the package error and no graph. |
| Artifact writer or template failure | Generation must return an error without a mixed successful generation. |
| Unsupported or unsafe relational change | Planning must return an error without applying a partial plan. |
| Driver or transaction failure | Generated clients must return the driver error without a successful result. |
| Invalid command input | The command must exit nonzero with a schema or generation diagnostic. |

## Cross-View Invariants

1. Field, edge, and index descriptors must agree with their normalized graph members.
2. A paired edge must have one cardinality and storage owner across both generated endpoints and the table projection.
3. Generated identifiers and signatures must agree with optionality, nillability, defaults, immutability, enums, and custom IDs.
4. `gen.Graph.Tables` and generated client calls must agree on tables, columns, indexes, and foreign keys.
5. `ent describe` and `entc.LoadGraph` must report the same schema member facts.
6. Reloading equal declarations must yield a semantically equal graph and artifact catalog.
7. A failed load, generation, plan, transaction, or driver operation must publish no partial later state.
8. Mixins and annotations must appear once under their documented owner in descriptors, generated artifacts, and table facts.
9. A generation receipt must reconcile selected graph, artifact, table, and driver facts under one semantic generation.
10. Equivalent schema generations must produce equal receipt digests across target directories, command and API entry points, and independent graph loads.

# Reference

## Public Interface

### Import Surface

- `entgo.io/ent`: `Interface`, `Schema`, `Mixin`, `Field`, `Edge`, `Index`
- `entgo.io/ent/schema`: `Annotation`
- `entgo.io/ent/schema/field`: `String`, `Text`, `Bytes`, `Bool`, `Time`, `Int`, `Enum`, `UUID`, `JSON`, `Descriptor`
- `entgo.io/ent/schema/edge`: `To`, `From`, `Descriptor`, `Table`, `Column`, `Columns`, `Symbol`, `Symbols`
- `entgo.io/ent/schema/index`: `Fields`, `Edges`, `Builder`, `Descriptor`
- `entgo.io/ent/entc`: `LoadGraph`, `Generate`, `Option`, `Storage`, `FeatureNames`, `Annotations`, `BuildFlags`, `BuildTags`, `Extensions`
- `entgo.io/ent/entc/gen`: `Config`, `Graph`, `Type`, `Field`, `Edge`, `Index`
- `entgo.io/ent/entc/load`: `Config`, `SchemaSpec`
- `entgo.io/ent/dialect`: `Driver`, `ExecQuerier`, `Tx`, `NopTx`
- `entgo.io/ent/dialect/sql/schema`: `Table`, `Column`, `Index`, `ForeignKey`
- `entgo.io/ent/entc/receipt`: `Plan`, `NewPlan`, `NodeFact`, `ArtifactFact`, `TableFact`, `DriverFact`, `DriverJournal`, `NewDriverJournal`, `GenerationReceipt`, `ChangeReceipt`, `Capture`, `Diff`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `ent.Interface`, `ent.Schema`, `ent.Mixin` | interfaces and type | Declare schema methods and reusable members. |
| `ent.Field`, `ent.Edge`, `ent.Index` | interfaces | Carry descriptor builders into loading. |
| `schema.Annotation` | interface | Attach mergeable metadata to schema facts. |
| `field.String`, `Text`, `Bytes`, `Bool`, `Time`, `Int`, `Enum`, `UUID`, `JSON` | functions | Create typed field builders. |
| `field.Descriptor` | type | Expose field facts used by normalization and generation. |
| `field builder Descriptor`, `Optional`, `Nillable`, `Unique`, `Immutable`, `Default`, `StorageKey`, `StructTag`, `Validate`, `Annotations` | methods | Configure and publish field facts. |
| `edge.To`, `edge.From` | functions | Create association and inverse edge builders. |
| `edge.Descriptor` | type | Expose relationship facts. |
| `edge builder Ref`, `Unique`, `Required`, `Immutable`, `Field`, `Through`, `StorageKey`, `Descriptor` | methods | Configure and publish edge facts. |
| `edge.Table`, `Column`, `Columns`, `Symbol`, `Symbols` | functions | Configure relationship storage identity. |
| `index.Fields`, `index.Edges`, `index.Builder` | functions and type | Declare composite and edge indexes. |
| `index.Descriptor` | type | Expose index facts. |
| `entc.LoadGraph`, `entc.Generate` | functions | Load a schema package or emit its artifacts. |
| `entc.Option`, `Storage`, `FeatureNames`, `Annotations`, `BuildFlags`, `BuildTags`, `Extensions` | option type and functions | Configure graph loading and generation. |
| `gen.Config` | type | Configure schema source, target, package, ID, storage, and features. |
| `gen.Graph`, `gen.Type`, `gen.Field`, `gen.Edge`, `gen.Index` | types | Expose normalized schema graph facts. |
| `gen.Graph.Gen`, `Tables`, `SchemaSnapshot`, `MutableNodes`, `SupportMigrate` | methods | Emit artifacts and derive graph projections. |
| `load.Config`, `load.SchemaSpec` | types | Load schema declarations into public schema descriptions. |
| `dialect.Driver`, `dialect.ExecQuerier`, `dialect.Tx`, `dialect.NopTx` | interfaces and function | Define runtime calls and transaction ownership. |
| `sql/schema.Table`, `Column`, `Index`, `ForeignKey` | types | Represent the relational projection. |
| Generated `T`, `TClient`, create/query/update/delete builders, predicates, field constants, and edge methods | generated identifier families | Expose the Go API derived from each schema type and declared member. |

| `index.Builder.Fields`, `Edges`, `Unique`, `StorageKey`, `Annotations`, `Descriptor` | methods | Configure and publish index facts. |
| `dialect.Driver.Dialect`, `Tx`, `Close`, `Exec`, `Query` | methods | Expose runtime dialect, transactions, execution, and query calls. |
| `receipt.Plan`, `receipt.NewPlan` | type and function | Select named graph nodes and complete table, artifact, and driver projections. |
| `receipt.Plan.SelectNode`, `receipt.Plan.IncludeTables`, `receipt.Plan.IncludeArtifacts`, `receipt.Plan.IncludeDriverCalls` | methods | Build a stable, caller-owned observation plan. |
| `receipt.NodeFact`, `receipt.ArtifactFact`, `receipt.TableFact`, `receipt.DriverFact` | records | Normalize public facts from schema, generation, relational, and runtime views. |
| `receipt.DriverJournal`, `receipt.NewDriverJournal` | type and function | Own an ordered caller-supplied runtime operation journal. |
| `receipt.DriverJournal.Record`, `receipt.DriverJournal.Entries` | methods | Append driver outcomes and return independent ordered snapshots. |
| `receipt.GenerationReceipt`, `receipt.Capture` | type and function | Capture one complete semantic generation across selected projections. |
| `receipt.GenerationReceipt.Validate`, `receipt.GenerationReceipt.Digest`, `receipt.GenerationReceipt.Equivalent` | methods | Reconcile projections and compare normalized generations. |
| `receipt.ChangeReceipt`, `receipt.Diff` | type and function | Describe semantic additions, removals, and changes between generations. |


### CLI Entry Points

| Command | Role | Success | Failure |
|---|---|---|---|
| `ent generate` | Load schemas and emit Go artifacts. | Exit 0 after one complete artifact generation. | Exit nonzero on load, normalization, generation, or writer failure. |
| `ent describe` | Present normalized schema members and relationships. | Exit 0 with the graph description. | Exit nonzero on load or normalization failure. |

## Behavioral Reference

Builder descriptors are the first public fact source. The normalized graph resolves cross-schema meaning; generated code, tables, commands, and driver calls are projections. Source-file byte layout is not authoritative. Relationship direction, optionality, identity, and storage derive from graph rules.

# Meta

## Appendix A: Environment

The accompanying environment contract defines the Linux toolchain, temporary modules, local driver, dependency closure, and filesystem boundaries.

## Appendix B: Assessment Notes

Conformance is assessed across schema names, field types, edge cardinalities, indexes, mixins, annotations, generation targets, old/new table sets, compilation, commands, and driver calls. Harmless source layout and SQL rendering differences have no contractual meaning.
