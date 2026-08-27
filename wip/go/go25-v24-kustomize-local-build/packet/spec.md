# kustomize Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in interface design, parameter naming, behavioral edge cases, and error semantics.
> Implementations derived from memory of external codebases will fail the evaluation.

# Context

## Product Overview

`kustomize` is a local YAML build system that accumulates resources from bases and overlays, generates configuration resources, applies ordered declarative transforms, updates references, and emits a coherent resource set. The Go API and command line share the same in-memory filesystem, resource identity, transform, and YAML contracts.

A resource is identified by group, version, kind, name, and namespace as those values evolve. Original, previous, and current identities let patches, generators, name changes, replacements, and references remain connected across the build.

## Non-Goals

- This specification does not require remote Git access, Helm execution, container access, executable plugins, or public network services.
- This specification does not define server-side Kubernetes defaulting, admission, validation, or apply behavior.
- This specification does not require undocumented transformer internals, filesystem-global state, or process-global caches.

# Orientation

## Representative Workflows

### Workflow 1: Build a base and overlay

1. Populate `filesys.MakeFsInMemory` with a base, an overlay, resource YAML, and kustomization files.
2. Configure the overlay with a namespace, name prefix or suffix, labels, patches, replacements, and image changes.
3. Run `krusty.MakeKustomizer` with `MakeDefaultOptions`.
4. Observe the returned `resmap.ResMap` through resources, current identities, original identities, selectors, and YAML.
5. Run `kustomize build` over the equivalent on-disk tree and compare resource-set semantics.

### Workflow 2: Generate data and update references

1. Define `configMapGenerator` and `secretGenerator` inputs from literals and local files.
2. Reference generated names from workloads and apply a content-changing overlay.
3. Build the overlay, observe generated hashes and rewritten references, then change one generator input.
4. Build again and observe that only identities and references derived from the changed content move together.
5. Localize sibling path references with `localizer.Run` or `kustomize localize`, then rebuild the localized tree and compare resource-set semantics.

### Workflow 3: Capture and compare a build receipt

1. Create a `receipt.BuildPlan`, select one logical target, and enable resource, identity, transform, file, and localization projections needed by the caller.
2. Build the target through the API or command surface and record each accepted source file and ordered transformer in a caller-owned `receipt.BuildJournal`.
3. Call `receipt.Capture` after reference closure and serialization; a failed load, generation, transform, reference update, or localization publishes no partial receipt.
4. Validate the receipt against the built resource map and fresh file observations.
5. Compare a later build with `receipt.Diff`, ignoring only temporary-root prefixes and YAML presentation without semantic effect.

# Behavior

## Domain 1: Local Loading and Resource Accumulation

This domain defines how kustomization files, resources, bases, overlays, components, and local paths become one resource map.

**Filesystem loading.** When `Kustomizer.Run` receives a filesystem and valid target path, it must locate a recognized kustomization file, load every declared local resource in declaration order, and recursively accumulate local bases and components. `MakeDefaultOptions` must restrict loading to the target's allowed directory boundary and disable external plugins. If a path is missing, escapes the configured boundary, forms a cycle, or contains malformed YAML, then the build must return an error and no successful resource map.

**Resource identity.** When `resource.Factory` or `resmap.Factory` parses YAML, each document must produce a resource with current identity, original identity, previous identities, content, and generation behavior. When a resource changes name or namespace, `StorePreviousId` must preserve referenceable history. If duplicate current identities enter one resource map, then append or accumulation must return an error.

**Map projections.** When a `ResMap` is observed through `Resources`, `AllIds`, `Select`, `GetByCurrentId`, or `AsYaml`, every projection must describe the same ordered resource set. `DeepCopy` must return independent resources. If a selector is invalid or identifies an ambiguous current identity where one resource is required, then the lookup must return an error.

## Domain 2: Generation, Names, and References

This domain defines generated ConfigMaps and Secrets, content hashes, name changes, namespaces, and reference rewrites.

**Generators.** When `ConfigMapArgs` or `SecretArgs` supplies literals, files, or environment-style entries, generation must merge those key/value sources according to declared behavior and options. Unless hash suffixing is disabled, generated names must include a deterministic suffix derived from semantic generated content. If keys conflict under create behavior, source files are missing, or behavior is invalid, then generation must return an error without publishing a partial resource.

**Name and namespace transforms.** When name prefix, name suffix, or namespace is configured, the transform must update every selected resource identity and every field declared as a name or namespace reference. Cluster-scoped resources must retain their namespace rules. Repeating the same build over unchanged input must not duplicate prefixes, suffixes, or namespace changes.

**Reference closure.** When a generated or ordinary resource changes current identity, workload references, role references, service references, and replacement selectors owned by the configured field specifications must resolve to the changed identity. If a required replacement source or selected field is missing, then replacement must return an error unless its public field options explicitly permit creation or absence.

## Domain 3: Ordered Transforms and YAML Projections

This domain defines patch selection, replacement flow, built-in transform order, kyaml filters, and stable output.

**Patch selection and order.** When a `types.Patch` declares a target selector, it must apply to every matching group, version, kind, name, namespace, label selector, and annotation selector. Patches in one kustomization must run in declaration order. If a patch document, path, target expression, or operation is invalid, then the build must return an error and no successful resource map.

**Built-in order.** When a build uses multiple built-ins, it must configure strategic-merge patches, general patches, namespace, prefix, suffix, labels, annotations, JSON patch, replica count, image tag, and replacements in that order. Generator resources must enter the accumulated set before these transforms. Reference updates and identity history must make later transforms observe the current result of earlier transforms.

**Replacements and kyaml.** When a `Replacement` selects one source field and target fields, it must copy the source scalar through declared delimiter and index options to every selected target. When `yaml.RNode.Pipe`, `Lookup`, `SetField`, or `Filter` transforms a node, the returned node and serialized YAML must agree. If a path meets an incompatible node kind, then kyaml must return `InvalidNodeKindError`.

**Output and localization.** When `ResMap.AsYaml` or `kustomize build` emits resources, output order must follow `krusty.Options.Reorder`; the default must preserve depth-first resource input order. When `localizer.Run` or `kustomize localize` copies a local dependency closure, references in the destination must resolve locally and a fresh destination build must preserve source-build resource semantics. If localization encounters a disallowed scheme, missing dependency, or destination conflict, then it must return an error without a successful destination receipt.

## Domain 4: Build Plans, Journals, and Receipts

This domain defines the public `sigs.k8s.io/kustomize/api/receipt` package. It binds resource accumulation, generated identity, transform order, reference closure, file provenance, serialization, and localization into one coherent build generation.

**Plans.** `receipt.NewBuildPlan` must create an immutable empty plan. `BuildPlan.SelectTarget` must return a new plan with one stable logical target and build options; an empty target or inconsistent load restriction must return an error without changing the prior plan. `IncludeResources`, `IncludeTransforms`, `IncludeFiles`, and `IncludeLocalization` must return new plans that retain every earlier selection. A plan that requests localization without resource and file projections is invalid.

**Facts and capture.** `ResourceFact` must identify original, previous, and current resource identity plus a semantic content digest. `TransformerFact` must identify declaration order, selected resources, and the resulting identities. `FileFact` must identify logical path, role, and content digest. `BuildFact` must bind build options, ordered output resources, and the serialized semantic digest. `receipt.Capture` must return one complete `BuildReceipt` only after every requested projection succeeds. It must reject facts drawn from different targets or build generations and must never combine pre-transform identities with post-transform content.

**Journal ownership.** `receipt.NewBuildJournal` must create an empty journal. `BuildJournal.Record` must append source-file and transformer observations with strictly increasing sequence values. `BuildJournal.Entries` must return an ordered caller-owned snapshot. Mutating inputs after `Record`, or mutating a returned entry slice or byte field, must not change the journal or a previously captured receipt.

**Validation, identity, and change.** `BuildReceipt.Validate` must reject missing requested projections, duplicate current identities, broken identity ancestry, non-increasing journal sequence, a transformed reference that does not resolve to the current identity, a generated hash inconsistent with semantic content, and file or localization facts outside the selected dependency closure. `Digest` and `Equivalent` must cover build options, ordered resource identities, semantic YAML, generated content, references, transform order, file closure, and localization mapping. They must ignore only temporary-root prefixes and YAML presentation with no semantic effect. `receipt.Diff` must return a `ChangeReceipt` deterministically ordered by projection and logical identity. Equivalent builds must produce no changes; resource order, identity ancestry, generated content, reference, transform, dependency, or localized-path changes must remain observable.

# Contract

## State Model

A target moves through **unread**, **loaded**, **accumulated**, **generated**, **transformed**, **reference-closed**, **serialized**, and **localized** states. Resource identity moves from original through zero or more previous identities to one current identity. Each build creates a new resource map; changing the filesystem after completion does not silently alter that returned map.

Public projections are filesystem files, kustomization values, resources, identity history, generated content, selectors, patches, references, replacements, kyaml nodes, ordered YAML, command output, localized files, and returned errors. A successful build must publish one coherent resource generation.

## Error Semantics

| Condition | Required result |
|---|---|
| Missing, cyclic, disallowed, or malformed local input | Build must return an error and no successful resource map. |
| Duplicate current identity | Accumulation or append must return an error. |
| Invalid generator source or conflict | Generation must return an error without a partial generated resource. |
| Invalid patch or target | Build must return an error without transformed output. |
| Missing required replacement source or field | Replacement must return an error. |
| Incompatible kyaml node kind | The operation must return `InvalidNodeKindError`. |
| Writer failure | YAML emission must return the writer error. |
| Localization dependency or destination failure | Localization must return an error without a success receipt. |

## Cross-View Invariants

1. `Resources`, `AllIds`, selectors, identity lookup, and YAML emission must describe the same ordered resource set.
2. Original, previous, and current identity projections must remain connected across generators, name changes, namespace changes, patches, replacements, and references.
3. Generated semantic content, generated hash suffix, resource current identity, and rewritten workload references must move together.
4. Patch target selection and replacement target selection must use the same current group, version, kind, name, namespace, label, and annotation projections.
5. Transform order must agree across the Go API, command output, resource identity history, and kyaml serialization.
6. A deep-copied resource map must preserve semantic output while remaining independently writable.
7. In-memory API builds and filesystem command builds must return equivalent resource sets under identical options.
8. A localized destination build must preserve the source build's resource identities, content, references, and output order.
9. A `receipt.BuildReceipt` must describe the same target, ordered resources, identity ancestry, transform sequence, references, file closure, serialized semantics, and localization result as its native build projections.
10. Fresh API and command captures of equivalent local inputs must produce equivalent receipts; receipt normalization removes only temporary-root prefixes and YAML presentation without semantic effect.

# Reference

## Public Interface

### Import Surface

- `sigs.k8s.io/kustomize/api/krusty`: `Kustomizer`, `MakeKustomizer`, `Options`, `MakeDefaultOptions`, `ReorderOption`, `ReorderOptionLegacy`, `ReorderOptionNone`, `ReorderOptionUnspecified`
- `sigs.k8s.io/kustomize/api/krusty/localizer`: `Run`
- `sigs.k8s.io/kustomize/api/filesys`: `FileSystem`, `MakeFsInMemory`, `MakeFsOnDisk`
- `sigs.k8s.io/kustomize/api/resmap`: `ResMap`, `Factory`, `NewFactory`, `New`, `Transformer`, `Generator`
- `sigs.k8s.io/kustomize/api/resource`: `Resource`, `Factory`, `NewFactory`
- `sigs.k8s.io/kustomize/api/types`: `Kustomization`, `ConfigMapArgs`, `SecretArgs`, `GeneratorArgs`, `GeneratorOptions`, `GenerationBehavior`, `NewGenerationBehavior`, `Patch`, `Replacement`, `SourceSelector`, `TargetSelector`, `FieldOptions`, `Selector`, `FieldSpec`, `LoadRestrictions`
- `sigs.k8s.io/kustomize/kyaml/yaml`: `RNode`, `Node`, `Parse`, `Filter`, `FilterFunc`, `Lookup`, `LookupCreate`, `SetField`, `Set`, `InvalidNodeKindError`, `ErrorIfInvalid`
- `sigs.k8s.io/kustomize/api/receipt`: `BuildPlan`, `NewBuildPlan`, `ResourceFact`, `TransformerFact`, `FileFact`, `BuildFact`, `JournalEntry`, `BuildJournal`, `NewBuildJournal`, `BuildReceipt`, `Capture`, `ChangeReceipt`, `Diff`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `krusty.Kustomizer`, `MakeKustomizer` | type and function | Build a target from a supplied filesystem. |
| `krusty.Options`, `MakeDefaultOptions` | type and function | Configure loading, plugins, labeling, and output order. |
| `krusty.ReorderOption`, `ReorderOptionLegacy`, `ReorderOptionNone`, `ReorderOptionUnspecified` | type and constants | Select resource output order. |
| `localizer.Run` | function | Copy a local dependency closure into a destination. |
| `filesys.FileSystem`, `MakeFsInMemory`, `MakeFsOnDisk` | interface and functions | Provide in-memory or on-disk local files. |
| `resmap.ResMap` | interface | Expose the ordered resource set and its projections. |
| `resmap.Factory`, `NewFactory`, `New` | type and functions | Construct resource maps. |
| `resmap.Transformer`, `Generator` | interfaces | Apply public transforms or produce resources. |
| `resource.Resource` | type | Expose YAML content and identity history. |
| `resource.Factory`, `NewFactory` | type and function | Parse YAML and construct resources. |
| `types.Kustomization` | type | Represent a kustomization file. |
| `types.ConfigMapArgs`, `SecretArgs`, `GeneratorArgs`, `GeneratorOptions` | types | Configure generated resources and key/value sources. |
| `types.GenerationBehavior`, `NewGenerationBehavior` | type and function | Select create, replace, or merge behavior. |
| `types.Patch` | type | Couple a patch source with target selection. |
| `types.Replacement`, `SourceSelector`, `TargetSelector`, `FieldOptions` | types | Configure source-to-target field replacement. |
| `types.Selector`, `FieldSpec`, `LoadRestrictions` | types | Configure resource selection, field ownership, and loading boundaries. |
| `yaml.RNode`, `Node`, `Parse` | types and function | Represent and parse YAML nodes. |
| `yaml.Filter`, `FilterFunc`, `Lookup`, `LookupCreate`, `SetField`, `Set` | interfaces, types, and functions | Traverse and transform YAML nodes. |
| `yaml.InvalidNodeKindError`, `ErrorIfInvalid` | error type and function | Report incompatible YAML node kinds. |
| `receipt.BuildPlan`, `receipt.NewBuildPlan` | type and function | Build an immutable multi-view capture plan. |
| `receipt.BuildPlan.SelectTarget`, `receipt.BuildPlan.IncludeResources`, `receipt.BuildPlan.IncludeTransforms`, `receipt.BuildPlan.IncludeFiles`, `receipt.BuildPlan.IncludeLocalization` | methods | Select a target and enable receipt projections without mutating earlier plans. |
| `receipt.ResourceFact`, `receipt.TransformerFact`, `receipt.FileFact`, `receipt.BuildFact`, `receipt.JournalEntry` | types | Represent coherent resource, transform, dependency, build, and ordered journal facts. |
| `receipt.BuildJournal`, `receipt.NewBuildJournal` | type and function | Record ordered caller-owned build observations. |
| `receipt.BuildJournal.Record`, `receipt.BuildJournal.Entries` | methods | Append an observation and return an isolated ordered snapshot. |
| `receipt.BuildReceipt`, `receipt.Capture` | type and function | Publish one complete build generation. |
| `receipt.BuildReceipt.Validate`, `receipt.BuildReceipt.Digest`, `receipt.BuildReceipt.Equivalent` | methods | Validate, identify, and compare build generations. |
| `receipt.ChangeReceipt`, `receipt.Diff` | type and function | Report deterministic semantic changes between builds. |

| `krusty.Kustomizer.Run` | method | Build a target from a supplied filesystem and path. |
| `resmap.ResMap.Resources`, `AllIds`, `Select`, `GetByCurrentId`, `AsYaml`, `DeepCopy`, `Append`, `AppendAll` | methods | Change and observe one ordered resource set. |
| `resmap.Factory.NewResMapFromBytes`, `NewResMapFromConfigMapArgs`, `NewResMapFromSecretArgs` | methods | Construct resource maps from YAML or generator arguments. |
| `resource.Factory.FromBytes`, `SliceFromBytes`, `MakeConfigMap`, `MakeSecret` | methods | Parse resources and create generated resources. |
| `resource.Resource.CurId`, `OrgId`, `PrevIds`, `StorePreviousId` | methods | Observe and advance resource identity history. |
| `resource.Resource.AsYAML`, `DeepCopy`, `NeedHashSuffix`, `Hash`, `GetRefBy` | methods | Observe YAML, copying, content identity, and reference ownership. |
| `resource.Resource.ApplySmPatch`, `ApplyFilter` | methods | Apply strategic-merge or kyaml transforms. |
| `yaml.RNode.Pipe`, `YNode`, `String` | methods | Transform and observe a YAML node. |

### CLI Entry Points

| Command | Role | Success | Failure |
|---|---|---|---|
| `kustomize build` | Build and emit a local target. | Exit 0 with the complete resource stream. | Exit nonzero on loading, generation, transform, or output failure. |
| `kustomize localize` | Copy a local dependency closure. | Exit 0 after destination creation and semantic validation. | Exit nonzero on dependency, destination, or validation failure. |

# Meta

## Appendix A: Environment

The working environment runs Go 1.24 on Linux without network access. Inputs, generated data, overlays, localized trees, YAML output, and command state use caller-created temporary directories. Only local path references and built-in generators and transformers participate.

## Appendix B: Assessment Notes

Conformance is assessed across base/overlay loading, duplicate identities, generator behavior, content hashes, prefix/suffix and namespace changes, name-reference closure, patch selection and order, replacements, kyaml node errors, deep copies, output order, localization, and CLI/API parity. Exact temporary paths, YAML presentation details without semantic effect, and undocumented implementation structure have no contractual meaning.

