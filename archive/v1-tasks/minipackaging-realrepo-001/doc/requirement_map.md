# MiniPackaging Unit/System Requirement Map

Date: 2026-06-28

Public packet: `task/minipackaging-realrepo-001/prd.md`

Rubric: `task/minipackaging-realrepo-001/rubric.json`

Status: `metadata-index-lock-lifecycle-redesign`. Score reports before this revision are stale for acceptance gating because the public product surface has moved beyond a stateless `resolve_metadata()` resolver into a candidate-owned `MetadataIndex` lifecycle. Fresh reference scoring is required before acceptance; fresh candidate scoring is required before claiming a fair unit/system gap.

## Lifecycle-Enrichment Brief

- `shared_fact_source`: the candidate-owned `MetadataIndex` fact table: normalized project name, canonical `Version`, copied outgoing requirement metadata, revision, and JSON-safe export/import state.
- `new_lifecycle`: incremental add/update/remove, cache invalidation, reverse dependency query, local lock snapshot creation, lock replay, export/import replay, multi-environment reuse, and failed update/apply atomicity.
- `derived_views`: `index()`, `resolve()` selected/excluded/edges/dependents/requested_extras/requirements, `dependents_of()`, `resolve_lock()`, `apply_lock()`, and `export_state()`/`import_state()`.
- `candidate_owned_surface`: public `MetadataIndex` methods plus the existing `resolve_metadata()` convenience API. System tests call those APIs directly and compare semantic public fields.
- `why_unit_not_enough`: a candidate can pass version, specifier, requirement, marker, and one-shot resolver checks while keeping stale reverse edges, stale exclusions, stale extras, non-atomic batches, or locks that do not replay after metadata changes.
- `fairness_risk`: exact private lock layouts, arbitrary storage ordering, exact exception messages, and repeated primitive failures. The rubric avoids these by comparing semantic projections, sorted public fields, boolean atomicity outcomes, and public exception class families only where downstream state is affected.
- `stop_condition`: if a fresh capable candidate reaches roughly 85%+ on both unit and system with only narrow primitive or display misses and no residual lifecycle divergence, stop micro-extending this task and send it to solved/fairness audit.

## Scout Report

- `verdict`: `materially-rescope` with build confidence after expanding the public product surface to `MetadataIndex` lifecycle and local lock replay.
- `fact source`: revisioned local package metadata table owned by `MetadataIndex`.
- `public projections`: stored index, resolver graph, reverse dependents, exclusions, requested extras, active requirement facts, lock snapshots, lock replay, export/import state, and atomic rollback behavior.
- `obvious-architecture result`: a single one-shot dependency graph is no longer sufficient because projections must survive and invalidate across mutations, replay locks, and imported state.
- `one-shot recomputation result`: one-shot recomputation can still satisfy `resolve_metadata()`, but cannot by itself prove stale-index invalidation, failed batch rollback, lock replay, or multi-environment reuse.
- `primitive-capping risks`: parser/version/specifier/marker primitives remain in unit tests; system rows count them only when lifecycle projections diverge.
- `next action`: run a local reference scorer if available, then run fresh candidates; do not add private lock fields, exact exception text, arbitrary ordering checks, or repeated parser roots.

## Shared Fact Source

The canonical system fact source is the candidate-owned `MetadataIndex` table. It stores copied candidate records by normalized name and canonical version, maintains a revision, and derives every public projection from those same records:

- stored candidate projection from `index()`;
- selected versions, excluded versions, active dependency edges, reverse dependents, requested extras, and active requirement facts from `resolve()`;
- reverse dependency lists from `dependents_of()`;
- JSON-safe local lock snapshots from `resolve_lock()`;
- replayed locked graphs from `apply_lock()`;
- persisted/reloaded state from `export_state()` and `import_state()`.

The stateless `resolve_metadata()` API remains public, but it is now a convenience projection over supplied candidates. It anchors one-shot resolver equivalence rather than being the whole system task.

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-package-shape` | Importable module names | Overview | Public classes, functions, and exception types import from `minipackaging`, including `MetadataIndex` and `resolve_metadata` |
| `REQ-feature-set` | Bounded 8-module feature set | Feature Set | Versions, specifiers, requirements, markers, environments, satisfaction, one-shot metadata resolution, and persistent metadata indexing are separate but composable modules |
| `REQ-global-invariants` | Cross-feature metadata invariants | Global Invariants | Version normalization, extras normalization, marker variables, requirement fields, resolver selections, edges, dependents, exclusions, locks, and exported state remain coherent |
| `REQ-version` | Version parsing and ordering | Data Model / Version | Supported PEP 440 subset parses, canonicalizes, compares, and rejects invalid text |
| `REQ-specifier` | Specifier parsing and containment | Data Model / SpecifierSet | Range, wildcard, compatible-release, exclusion, and prerelease behavior works predictably |
| `REQ-requirement` | Requirement grammar | Data Model / Requirement | Name, extras, specifier, URL, and marker are parsed into distinct fields, serialized canonically, and compared/hashed by normalized semantic fields |
| `REQ-marker` | Marker grammar and evaluation | Data Model / Marker | Boolean marker expressions evaluate against caller environments and requested extras |
| `REQ-environment` | Environment dictionary behavior | Data Model / Environment | Default and caller-supplied environments provide marker variable values without mutation |
| `REQ-satisfaction` | Composed requirement evaluation | Data Model / Requirement Satisfaction | Requirement applicability and version satisfaction are combined by `is_requirement_satisfied` |
| `REQ-resolution-api` | Public local metadata resolver | Data Model / Dependency Metadata Invariants; Commands / API | `resolve_metadata()` accepts roots/candidates/environment/extras/prerelease policy and returns documented projection keys without mutating caller metadata |
| `REQ-resolution-invariants` | Deterministic candidate metadata projections | Data Model / Dependency Metadata Invariants | Candidate metadata evaluates into selected versions, edges, reverse dependents, requested extras, active requirements, and exclusions using public semantics |
| `REQ-index-api` | Persistent metadata index lifecycle | Data Model / Persistent Metadata Index; Commands / API | `MetadataIndex` owns copied candidate metadata and supports add, update, remove, batch apply, resolve, reverse query, export, import, and cache invalidation |
| `REQ-lock-lifecycle` | Local lock snapshot and replay | Data Model / Persistent Metadata Index; Commands / API | `resolve_lock()` creates JSON-safe semantic locks and `apply_lock()` replays or rejects them atomically against current metadata |
| `REQ-errors` | Public error behavior | Error Behavior | Invalid syntax, missing variables, failed mutations, failed batches, and failed lock applies raise documented public exception families atomically |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit cases exercise one feature module at a time |
| `REQ-system-eval` | System testing definition | Evaluation Style | System cases assert cross-component invariants over shared metadata lifecycle projections |

## Unit Coverage

| Test | Feature | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `MPU001` | imports | `REQ-package-shape` | Public names, including `MetadataIndex` and `resolve_metadata`, and exception hierarchy |
| `MPU002` | version | `REQ-version` | Canonical version serialization |
| `MPU003` | version | `REQ-version` | Dev, pre, final, and post ordering |
| `MPU004` | version | `REQ-version` | Epoch and local-label ordering |
| `MPU005` | version | `REQ-version`, `REQ-errors` | Invalid versions raise `InvalidVersion` |
| `MPU006` | specifier | `REQ-specifier` | Inclusive and exclusive ranges |
| `MPU007` | specifier | `REQ-specifier` | Equality, inequality, and wildcard prefixes |
| `MPU008` | specifier | `REQ-specifier` | Compatible-release bounds |
| `MPU009` | specifier | `REQ-specifier` | Prerelease inclusion policy |
| `MPU010` | specifier | `REQ-specifier`, `REQ-errors` | Invalid specifiers raise `InvalidSpecifier` |
| `MPU011` | requirement | `REQ-requirement` | Names, extras, and specifiers parse canonically |
| `MPU012` | requirement | `REQ-requirement` | Direct URL and marker fields remain distinct |
| `MPU013` | requirement | `REQ-requirement` | Equality and hashing use normalized public fields |
| `MPU014` | requirement | `REQ-requirement`, `REQ-errors` | Invalid requirements raise `InvalidRequirement` |
| `MPU015` | marker | `REQ-marker` | Caller environment comparisons |
| `MPU016` | marker | `REQ-marker` | Boolean precedence and parentheses |
| `MPU017` | marker | `REQ-marker` | Membership and requested-extra evaluation |
| `MPU018` | marker | `REQ-marker`, `REQ-errors` | Syntax and missing-variable exceptions |
| `MPU019` | resolve metadata schema | `REQ-resolution-api`, `REQ-resolution-invariants` | Public projection keys, simple schema, and caller metadata non-mutation |

Unit tests intentionally keep the current parser, version, specifier, requirement, marker, and one-shot resolver primitives as readiness checks. The system layer does not multiply isolated primitive roots unless lifecycle projections actually diverge.

## System Coverage

System tests call public `MetadataIndex` and `resolve_metadata()` APIs. They compare public semantic fields rather than private objects, hidden helper shapes, exact exception messages, or incidental insertion order.

| Test | system_dimension | Crossed modules | Requirement refs | Cross-feature contract |
| --- | --- | --- | --- | --- |
| `MPS001` | `state_accumulation` | index add/copy -> resolver projections -> extras/marker graph | `REQ-index-api`, `REQ-resolution-invariants`, `REQ-global-invariants` | Added candidates are copied into the index, caller mutations do not leak, and selected/edge/dependent/extras views agree |
| `MPS002` | `projection_consistency` | batch update/remove -> cache invalidation -> index/resolve/dependents | `REQ-index-api`, `REQ-resolution-invariants`, `REQ-global-invariants` | Updating and removing candidates invalidates stale selection, exclusion, stored index, and reverse-dependent projections together |
| `MPS003` | `bidirectional_consistency` | resolve edges -> direct and transitive reverse query | `REQ-index-api`, `REQ-resolution-invariants`, `REQ-global-invariants` | `dependents_of()` is the reverse projection of the same active graph returned by `resolve()` |
| `MPS004` | `boundary_crossing` | marker/environment/extras -> repeated stateful resolve | `REQ-index-api`, `REQ-marker`, `REQ-environment`, `REQ-resolution-invariants`, `REQ-global-invariants` | One index can be reused across environments and requested extras without stale marker or extras state |
| `MPS005` | `state_accumulation` | resolve lock -> candidate addition -> fresh resolve vs locked replay | `REQ-index-api`, `REQ-lock-lifecycle`, `REQ-resolution-invariants`, `REQ-global-invariants` | Lock replay preserves locked selected versions after unrelated candidate additions while fresh resolve can select newer versions |
| `MPS006` | `error_atomicity` | stale lock detection -> export/index stability | `REQ-index-api`, `REQ-lock-lifecycle`, `REQ-errors`, `REQ-global-invariants` | A lock whose selected candidate metadata changed is rejected without mutating revision or exported state |
| `MPS007` | `boundary_crossing` | export/import -> resolve/dependents/lock replay | `REQ-index-api`, `REQ-lock-lifecycle`, `REQ-resolution-invariants`, `REQ-global-invariants` | Export/import replays candidate table, resolver projections, reverse dependents, and lock behavior |
| `MPS008` | `error_atomicity` | failed batch apply -> later valid batch -> projection refresh | `REQ-index-api`, `REQ-errors`, `REQ-resolution-invariants`, `REQ-global-invariants` | Failed mixed batches are atomic; a later valid batch updates selected versions and reverse dependents together |
| `MPS009` | `error_atomicity` | failed remove/update -> valid remove -> resolver invalidation | `REQ-index-api`, `REQ-errors`, `REQ-global-invariants` | Failed single mutations do not change revision/export state; valid removal invalidates selected/excluded projections |
| `MPS010` | `bidirectional_consistency` | root/transitive constraints -> selected/excluded/dependents | `REQ-index-api`, `REQ-specifier`, `REQ-version`, `REQ-resolution-invariants`, `REQ-global-invariants` | Index resolution derives selected versions, exclusions, and reverse dependents from one normalized constraint set |
| `MPS011` | `global_invariant` | environment-sensitive lock -> replay validation -> fresh environment resolve | `REQ-index-api`, `REQ-lock-lifecycle`, `REQ-marker`, `REQ-environment`, `REQ-global-invariants` | Lock replay revalidates marker decisions and rejects environment mismatch instead of reusing stale graph state |
| `MPS012` | `projection_consistency` | stateless resolver -> stateful resolver -> lifecycle metadata | `REQ-index-api`, `REQ-resolution-api`, `REQ-resolution-invariants`, `REQ-global-invariants` | `resolve_metadata()` and `MetadataIndex.resolve()` expose equivalent semantic projections from the same candidates, with lifecycle metadata added only by the index |

System dimension coverage:

- `state_accumulation`: `MPS001`, `MPS005`
- `projection_consistency`: `MPS002`, `MPS012`
- `bidirectional_consistency`: `MPS003`, `MPS010`
- `boundary_crossing`: `MPS004`, `MPS007`
- `error_atomicity`: `MPS006`, `MPS008`, `MPS009`
- `global_invariant`: `MPS011`

## Weights

| Layer | Count | Weight each | Total |
| --- | ---: | ---: | ---: |
| Unit | 19 | 4 | 76 |
| System | 12 | 8 | 96 |

Total weighted score: 172.

## Fairness Notes

- The PRD defines `MetadataIndex`, `resolve_lock()`, and `apply_lock()` as public candidate-owned APIs. Hidden tests should not invent an evaluator-only index, resolver, lock parser, or private storage shape.
- System rows compare semantic public projections: normalized names, canonical versions, selected versions, excluded versions, dependency edges, reverse dependents, requested extras, active requirement facts, revision equality, export/import equality, and boolean atomicity outcomes.
- The rubric avoids exact exception messages, arbitrary candidate insertion order, private object identity, exact private lock layout, network access, pip-compatible lockfile details, and full installer backtracking.
- Requirement-string canonicalization, equality/hash behavior, invalid syntax rejection, version ordering, and specifier parsing remain unit-level readiness checks. They should not be counted repeatedly in system rows unless they cause stale or divergent lifecycle projections.
- Residual gap should come from maintaining one shared fact table across mutable operations, cached projections, reverse queries, locks, environment-specific replay, export/import, and failed-operation rollback. A candidate with independent per-method state can pass many units but should lose system rows through stale or inconsistent projections.
