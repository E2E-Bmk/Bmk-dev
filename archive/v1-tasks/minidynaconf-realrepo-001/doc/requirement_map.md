# MiniDynaconf Unit/System Requirement Map

Date: 2026-06-28

Public packet: `task/minidynaconf-realrepo-001/prd.md`

Rubric: `task/minidynaconf-realrepo-001/rubric.json`

Reference score report: `task/minidynaconf-realrepo-001/doc/score_reports/score_report_reference_lifecycle_v3_20260628.json`

## Public Requirements

| ID | Capability | PRD section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-package-shape` | Importable public names | Overview | `MiniDynaconf`, `Validator`, `ValidationError`, and `SettingsError` import from `minidynaconf` |
| `REQ-feature-set` | Seven-module feature boundary | Feature Set | File loading, env overrides, secrets, casting, validators, runtime API, and lifecycle operations are distinct features sharing one namespace |
| `REQ-data-model` | Canonical nested configuration tree | Data Model | Case-insensitive dotted, attribute/item, export, validator, import, delete, and reload views address the same logical nested values |
| `REQ-global-invariants` | Cross-source and cross-feature semantics | Global Invariants | Projection consistency, priority, recursive merge, casting-before-validation, export/reload round trip, source replay, configure replacement, runtime-overlay clearing, and atomicity remain consistent |
| `REQ-file-loading` | Settings file loading | Settings File Loading | JSON, TOML/INI, YAML subset, and Python settings files load mappings into settings; successful incremental loads replay on reload |
| `REQ-environments` | Environment sections in files | Settings File Loading | `default` values load before active environment overlays |
| `REQ-env-overrides` | Environment and dotenv overrides | Environment Variable Overrides | Prefixed env vars and dotenv entries map into logical keys, including nested double-underscore keys; successful dotenv imports replay on reload |
| `REQ-secrets` | Secrets file priority | Secrets Loading | Secrets files load through the same namespace and override lower-priority sources |
| `REQ-type-casting` | Automatic and explicit casting | Type Casting | Text values become Python booleans, numbers, lists, dicts, `None`, or protected strings |
| `REQ-validators` | Validation rules | Validators | Required/default/type/comparison/equality/callable validators inspect current settings and raise `ValidationError` |
| `REQ-runtime-api` | Settings object API | Runtime Settings API | Attribute/item/get/set/update/delete/exists/as_dict/reload/configure expose, export, rebuild, and mutate settings |
| `REQ-lifecycle-api` | Public lifecycle operations | Runtime Settings API | `import_dict`, `export`, `load_file`, `load_env_file`, `reload`, and `configure` preserve one lifecycle model over durable sources plus runtime overlays |
| `REQ-error-atomicity` | Failed operations preserve state | Error Behavior | Bad casts, malformed files, failed validators, failed imports, and failed configure attempts do not partially mutate settings or loader lifecycle state |
| `REQ-unit-eval` | Primitive-local unit scoring | Evaluation Style | Unit cases isolate loader, env, nested attribute proxy, runtime mutation, explicit cast, validator, import/export, reload, and configure primitives |
| `REQ-system-eval` | Cross-feature system scoring | Evaluation Style | System cases test lifecycle invariants over one canonical configuration tree and avoid multiplying one missing primitive across rows |

## Unit Coverage

| Test | Primitive cluster | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `MDU001` | runtime API | `REQ-package-shape` | Required public names import and construct |
| `MDU002` | file loader | `REQ-file-loading`, `REQ-environments` | TOML `default` and active environment sections overlay in the file-loading primitive |
| `MDU003` | environment loader | `REQ-env-overrides`, `REQ-type-casting` | Prefix filtering, double-underscore nesting, and automatic casts work for process env vars |
| `MDU004` | runtime mutation | `REQ-runtime-api`, `REQ-data-model` | `set`, `update`, and `delete` recursively merge and remove dotted nested keys |
| `MDU005` | explicit casts | `REQ-type-casting`, `REQ-error-atomicity` | `@int`, `@str`, `@json`, `@none`, and invalid explicit casts behave atomically |
| `MDU006` | validators | `REQ-validators`, `REQ-error-atomicity` | Validator defaults and condition callbacks see settings, and failed validation rolls back |
| `MDU007` | lifecycle primitives | `REQ-runtime-api`, `REQ-lifecycle-api` | `export` returns a deep copy and `import_dict` overlays or replaces runtime state |
| `MDU008` | reload/configure | `REQ-runtime-api`, `REQ-lifecycle-api` | `reload` drops runtime-only state and `configure` replaces configured file sources |

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Cross-feature contract |
| --- | --- | --- | --- | --- |
| `MDS001` | `global_invariant` | defaults -> files -> env -> secrets -> validators -> runtime update/delete -> export | `REQ-global-invariants`, `REQ-file-loading`, `REQ-env-overrides`, `REQ-secrets`, `REQ-validators`, `REQ-runtime-api`, `REQ-lifecycle-api` | One merged tree projects consistently through semantic dotted access, validator inputs/defaults, runtime writes/deletes, and export without depending on nested attribute proxies |
| `MDS002` | `boundary_crossing` | runtime import/delete -> export file -> JSON file loader -> validators -> access views | `REQ-global-invariants`, `REQ-runtime-api`, `REQ-file-loading`, `REQ-validators`, `REQ-lifecycle-api` | Exporting typed runtime state after mutation and deletion, then reloading into a fresh object, preserves the canonical tree observed by validators and semantic access projections |
| `MDS003` | `state_accumulation` | configured files -> incremental file import -> dotenv import -> env -> secrets -> runtime overlay/delete -> reload | `REQ-global-invariants`, `REQ-file-loading`, `REQ-env-overrides`, `REQ-secrets`, `REQ-runtime-api`, `REQ-lifecycle-api` | Durable source imports replay on reload while runtime overlays and deletion tombstones are cleared |
| `MDS004` | `error_atomicity` | configured source -> import_dict -> malformed durable import -> validators -> configure -> reload/export views | `REQ-global-invariants`, `REQ-runtime-api`, `REQ-validators`, `REQ-error-atomicity`, `REQ-lifecycle-api` | Failed validated imports, failed durable file imports, and failed configure attempts preserve both the canonical tree and loader lifecycle |
| `MDS005` | `operation_order_sensitivity` | configured file -> incremental import -> validator defaults -> typed runtime overlay/delete -> configure replacement -> export | `REQ-global-invariants`, `REQ-runtime-api`, `REQ-file-loading`, `REQ-validators`, `REQ-lifecycle-api` | `configure` clears stale imports, overlays, deletion tombstones, and derived defaults before projecting the new configured tree |

System dimension coverage:

- `global_invariant`: `MDS001`
- `boundary_crossing`: `MDS002`
- `state_accumulation`: `MDS003`
- `error_atomicity`: `MDS004`
- `operation_order_sensitivity`: `MDS005`
- `cross_feature_dataflow`: covered inside `MDS001`, `MDS002`, `MDS003`, and `MDS005`

## Redesign Note

Canonical fact source: the nested case-insensitive configuration tree materialized from durable sources plus runtime overlays and deletion tombstones.

Durable source state: constructor defaults/files/env/secrets, successful `load_file()` imports, and successful `load_env_file()` imports. These are replayed by `reload()`.

Runtime overlay state: `set`, `update`, `import_dict`, and `delete` tombstones. These sit above durable sources in the current projection but are cleared by `reload()` and `configure()` unless written to a durable source.

Derived views: attribute proxies, item lookup, dotted `get`, `exists`, validator inputs/defaults, `as_dict`, `export`, JSON export files, reloaded settings, and replaced settings after `configure()`.

Primitive clustering: unit rows cover loaders, env parsing, nested attribute proxies, mutation, casting, validation, export/import helpers, reload, and configure locally. System rows avoid PathLike, YAML, nested-attribute, explicit-runtime-cast, and nested-dict traps where those primitives are not the invariant under test; they use plain string paths plus semantic `get`, `exists`, JSON, and dictionary comparisons.

Expected gap mechanism: a function-by-function implementation can pass local primitives while failing system rows if it flattens state once, stores independent semantic/export/validator views, forgets incremental source imports on reload, keeps stale runtime overlays after configure, or rolls back only the direct data dictionary but not loader lifecycle state.

Reference validation: `py -3.11 tools\score_unit_system.py task\minidynaconf-realrepo-001\rubric.json --solution-dir runs\minidynaconf-realrepo-001\solution-reference --timeout 10` passes the revised packet: 13/13 cases, weighted 92/92, unit 100.00%, system 100.00%.

## Fairness Notes

- The public packet states the lifecycle model needed for hidden checks: durable imports replay on reload; runtime overlays and deletions clear on reload/configure; configure replaces loader state; export is a semantic projection.
- System checks compare observable values, semantic dictionaries, and exception categories, not private storage structures, nested attribute object shape, or exact exception text.
- System rows use string file paths, simple JSON files, and ordinary dictionaries so PathLike, YAML, and parser edge cases do not dominate system loss.
- Runtime values inside lifecycle rows are mostly supplied as already-typed Python values. Explicit runtime cast behavior remains covered in unit rows and does not gate export/reload or configure lifecycle evidence.
- The system layer intentionally uses denser lifecycle rows. Candidate failures should be classified by root invariant: shared projection, export/reimport, durable replay, atomic lifecycle recovery, or configure clearing stale state.
- v3 evidence showed primitive caps: Codex scored unit 75.00% and system 80.00%, with the only system failure tied to a typed export/reload prerequisite; OpenHands scored unit 25.00% and system 0.00%, with several system rows crashing on nested attribute proxies already visible in unit failures. This fairness revision keeps the lifecycle scope but reduces those primitive-specific gates.
- Sanity reruns of the same pre-existing candidate artifacts are diagnosis only: Codex now scores unit 75.00% and system 100.00%, showing the prior `MDS002` loss was primitive-capped; OpenHands now scores unit 25.00% and system 40.00%, with remaining system loss concentrated on semantic source precedence, export shape, and failed lifecycle replay.
- A fresh candidate run is still needed to confirm the intended gap for the target population. Do not use the pre-revision candidate reports or same-artifact sanity reruns as acceptance evidence for the revised packet.
