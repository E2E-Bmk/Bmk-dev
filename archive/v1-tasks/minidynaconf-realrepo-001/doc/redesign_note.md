# MiniDynaconf Lifecycle Redesign Note

Date: 2026-06-28

## Diagnosis

The v2 task improved over the original checklist by making system rows assert one canonical settings tree across loaders, env, secrets, validators, runtime mutation, export, and reload. That version still had two weakness signals:

- Current Codex subagent v2 scored unit 100.00% and system 100.00%, so the public surface was too directly implementable for the target population.
- Weaker OpenHands v2 candidates showed a unit-over-system gap, but their failures still overlapped local runtime/cast/file primitives. That was useful weak-control evidence, not enough to accept the task.

The v3 redesign therefore avoided adding PathLike, nested-dict, YAML, or parser edge cases and materially enriched the product-natural lifecycle instead.

Post-v3 evidence showed that the lifecycle signal was still partly primitive-capped:

- Reference v3 passed unit 100.00% and system 100.00%.
- Codex subagent v3 scored unit 75.00% and system 80.00%. The only system miss was `MDS002`, and the failure was explained by a typed export/reload prerequisite already visible in local runtime/import behavior rather than by durable lifecycle divergence.
- OpenHands DeepSeek v3 scored unit 25.00% and system 0.00%. Several system rows crashed before reaching lifecycle assertions because nested attribute proxies returned raw dictionaries, a primitive failure already visible in unit rows.

This conservative fairness revision keeps the public lifecycle and reference behavior but changes system rows to use semantic projections (`get`, `exists`, `as_dict`, `export`, validators, and reloaded objects) before attribute-proxy-specific checks can dominate. It also moves explicit runtime cast tokens out of lifecycle rows unless the row is specifically about casting.

Validation after the revision:

- Reference rerun: unit 100.00%, system 100.00%, 13/13 cases, weighted 92/92.
- Same Codex artifact rerun: unit 75.00%, system 100.00%. This is a fairness signal, not acceptance evidence: the former `MDS002` miss was removed because it was capped by a runtime cast/export prerequisite rather than a lifecycle invariant.
- Same OpenHands artifact rerun: unit 25.00%, system 40.00%. Remaining system failures now reach semantic source precedence, export shape, and failed lifecycle replay instead of being dominated by nested attribute proxy crashes.

## Shared Fact Source

The canonical fact source is the nested case-insensitive configuration tree materialized from:

- durable sources: constructor defaults, configured files, process env, secrets, successful `load_file()` imports, and successful `load_env_file()` imports;
- runtime overlays: `set`, `update`, and `import_dict`;
- runtime deletion tombstones from `delete`.

Public projections must all read this same materialized tree: attribute proxies, item lookup, dotted `get`, `exists`, validator inputs/defaults, `as_dict`, `export`, JSON export files, reloaded settings, and replacement state after `configure()`. System evidence should distinguish projection primitive readiness from lifecycle invariants; one missing nested attribute proxy should not explain every lifecycle row.

## New Lifecycle

The public lifecycle now has explicit operations:

- `load_file(path, ...)` and `load_env_file(path)` add durable imports that replay on `reload()`.
- `set`, `update`, `import_dict`, and `delete` create runtime-only overlays above durable sources.
- `reload()` rebuilds from durable sources and clears runtime overlays and deletion tombstones.
- `export(path=None)` returns/writes the semantic canonical tree.
- `configure(**kwargs)` replaces loader configuration and clears incremental imports, runtime overlays, deletion tombstones, and derived validator defaults.
- Failed casts, validated imports, malformed files, and failed configure attempts roll back both projections and loader lifecycle state. The revised system atomicity row emphasizes validated import, malformed durable import, and failed configure rollback; explicit cast failure remains covered in unit tests.

## Why Unit Is Not Enough

Unit rows cover local primitives: file loading, env parsing, nested attribute proxying, mutation, casting, validation, export/import helpers, reload, and configure. A candidate can pass those with independent per-feature state.

System rows require the primitives to coordinate through one lifecycle model. Implementations should lose system credit if they:

- flatten initial sources once and forget successful incremental imports during reload;
- maintain separate data for semantic access/export/validators;
- implement deletion only against runtime dictionaries and leave lower-priority values visible;
- keep stale runtime overlays or validator defaults after configure;
- roll back `_data` after failure but leave changed loader options or imported-source lists behind.

## Rubric Shape

Unit weight is 32 across eight local rows. System weight is 60 across five lifecycle invariant rows:

- `MDS001`: source stack projection across defaults/files/env/secrets/validators/runtime/delete/export, checked through semantic access rather than nested attribute proxies;
- `MDS002`: typed runtime import/delete/export/reimport round trip;
- `MDS003`: durable incremental imports replay on reload while runtime overlays clear;
- `MDS004`: failed validated import, malformed durable import, and failed configure preserve tree and lifecycle;
- `MDS005`: configure replacement clears stale imports, typed overlays, tombstones, and defaults.

This keeps system loss focused on shared-state lifecycle behavior rather than repeated local primitives.

## Fairness Risks

- The lifecycle model is broader than v2. The PRD now explicitly states durable imports, runtime overlays, reload clearing, configure replacement, export semantics, and atomic lifecycle recovery.
- Hidden system cases use string paths, JSON files, semantic dictionaries, and `get`/`exists` projections to avoid PathLike/YAML/private parser/nested-attribute traps.
- Runtime values inside lifecycle rows are mostly supplied as already-typed Python values so export/reload and configure evidence is not capped by explicit cast-token defects already tested in unit rows.
- Exact exception text, private storage names, and output ordering are not scored.
- The reference passes the revised rubric at 100%. Existing v1/v2, pre-revision v3 candidate reports, and same-artifact sanity reruns are diagnosis only and should not be treated as acceptance evidence for the revised packet.
