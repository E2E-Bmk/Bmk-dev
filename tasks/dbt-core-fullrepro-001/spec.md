# dbt-core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`dbt-core` is a data-transformation framework with a `dbt` CLI entry point. It reads a local dbt project, resolves project resources into a graph, and exposes that graph through command-line commands, JSON artifacts, compiled SQL files, and the Python `dbtRunner` interface. The project graph is the central state: parsing builds it, selection queries it, compilation enriches selected executable nodes with rendered SQL, and JSON artifacts serialize the public view of the invocation.

This specification covers local project parsing and compilation workflows. It focuses on observable files, command results, and Python runner results for projects that have local files, a valid project configuration, and a usable profile for commands that require one.

## Non-Goals

- This specification does not require Adapter conformance behavior, PostgreSQL service tests, cloud services, RPC server lifecycle, platform features, package installation, documentation site generation, source freshness execution, snapshot semantics, seed loading semantics, data test pass/fail semantics, or adapter-specific SQL execution details.

- Byte-for-byte equality of complete `manifest.json` or `run_results.json` files is not required. The public artifact fields and cross-view relationships described in this specification are in scope.

- This specification does not require Reproducing private helper modules, test fixtures, hidden Click parameters, internal parser class names, internal msgpack schema details, or exact terminal log wording.

## Representative Workflows

### Parse, Inspect, And Compile A Local Project

```text
dbt parse --project-dir ./jaffle_shop --profiles-dir ./profiles --target-path ./target
dbt ls --project-dir ./jaffle_shop --profiles-dir ./profiles --target-path ./target --select tag:nightly --output json --output-keys name resource_type unique_id original_file_path
dbt compile --project-dir ./jaffle_shop --profiles-dir ./profiles --target-path ./target --select stg_orders
```

After the parse command succeeds, `./target/manifest.json`, `./target/semantic_manifest.json`, `./target/perf_info.json`, and `./target/partial_parse.msgpack` must exist when JSON writing and partial parsing are enabled. The list command must print newline-delimited JSON objects for selected enabled resources. The compile command must update `manifest.json`, write `run_results.json`, and place compiled SQL for `stg_orders` under the target path.

### Use The Python Runner

```python
from dbt.cli.main import dbtRunner, dbtRunnerResult

runner = dbtRunner()
parse_result: dbtRunnerResult = runner.invoke(
    ["parse", "--project-dir", "./jaffle_shop", "--profiles-dir", "./profiles"]
)
manifest = parse_result.result

list_result = dbtRunner(manifest=manifest).invoke(
    ["list", "--project-dir", "./jaffle_shop", "--profiles-dir", "./profiles", "--output", "name"]
)
```

The parse invocation must return a successful result with a manifest-like result object. The second invocation must accept the supplied manifest, must apply the same list behavior as the CLI, and must return a list of selected names.

## Parsing and Manifest Behavior

Parsing reads and validates a local dbt project, building a manifest that represents the project's enabled resources.

**Parse command.** `dbt parse` must read the project and construct a manifest representing enabled resources including models, tests, sources, macros, docs blocks, exposures, metrics, semantic models, saved queries, seeds, snapshots, analyses, unit tests, parent maps, child maps, selectors, disabled resources, and metadata. The command must accept `--project-dir`, `--profiles-dir`, `--target-path`, `--threads`, `--quiet`, and `--no-version-check` options.

**Manifest content.** `manifest.json` must contain top-level dictionaries or arrays for the public resource collections and dependency maps. Resource entries must include public identity fields such as `name`, `unique_id`, `package_name`, `path`, `original_file_path`, and `resource_type` when those fields apply.

**Artifact writing.** When parsing succeeds and JSON writing is enabled, dbt-core must write `manifest.json`, `semantic_manifest.json`, and `perf_info.json` to the target path. `perf_info.json` must contain parser timing and path-count information.

**Parse-only behavior.** When `dbt parse` succeeds, the manifest must not contain compiled SQL for ordinary model nodes that were only parsed. Compiled SQL requires `dbt compile` or another compilation command.

**Parse failures.** When project files contain invalid YAML, invalid Jinja, unresolved required references, duplicate resource identities, or invalid project/profile configuration, parsing must fail and must not report a successful command result.

**JSON writing control.** When `--no-write-json` is supplied, commands must avoid writing JSON artifacts. They must still return their command result through the Python runner.

**Partial parse cache.** When partial parsing is enabled, `partial_parse.msgpack` in the target path serves as a persistent cache. After a successful parse, this file must be written. When `--no-partial-parse` is supplied, dbt-core must perform a full parse. When the cache is invalid, stale, or from an incompatible version, dbt-core must fall back to a full parse.

## Selection and List Behavior

The list command queries the parsed project graph to identify and display selected resources.

**List command.** `dbt list` and `dbt ls` must list resources in the parsed project without running SQL queries against the data platform. Both aliases must produce identical output for identical arguments.

**Default resource types.** By default, list output must include models, snapshots, seeds, tests, sources, exposures, metrics, saved queries, semantic models, and unit tests. Analysis resources must be included only when selected through `--resource-type analysis` or an all-resource selection.

**Models flag.** `--models` must select only model resources and must be mutually exclusive with `--select` and `--resource-type`. Combining `--models` with either of those arguments must raise a runtime error.

**Selection and exclusion.** `--select`, `--exclude`, and `--selector` must filter the graph using dbt resource selection semantics. `--exclude` must remove matching resources from the selected set. When no resources are selected, the command must return an empty result list.

**Output modes.** `--output selector` must return selection strings using the appropriate format per resource type (e.g., `source:package.source_name.table_name` for sources, fully qualified name joined by periods for graph nodes). `--output name` must return search names. `--output path` must return `original_file_path` values. `--output json` must return one JSON object per selected resource with either the default keys or the keys requested by `--output-keys`.

**Enabled-only output.** Disabled resources must not appear in list output. Returned resources must have `config.enabled` equal to `true` when that config field is present.

## Compile, Run, and Compiled Files

Compilation renders Jinja and dbt macros for selected resources, while run executes them through an adapter.

**Compile command.** `dbt compile` must parse the project, select executable resources, render Jinja and dbt macros, and write compiled SQL under the target path. It must not materialize model results into database relations. When JSON writing is enabled, it must write `manifest.json`, `semantic_manifest.json`, and `run_results.json`.

**Compile results.** When a selected model compiles successfully, its result in `run_results.json` must have a successful status, `compiled` equal to `true`, a non-empty `compiled_code`, and a `unique_id` that maps to the corresponding manifest entry. The compiled SQL must also be written as a file under the target path.

**Inline compilation.** When `dbt compile --inline SQL` is used, the inline query must be compiled as a temporary SQL operation named `inline_query`, the compiled SQL must be printed or returned according to the output mode, and the temporary inline node must be removed from the persistent manifest. `--output json` must emit the compiled node in JSON form. `--output text` must emit compiled output as text.

**Run command.** `dbt run` must compile selected executable model resources and execute them through the configured adapter. `run_results.json` must include only executed selected nodes with status, timing, unique_id, compiled state, compiled code, and relation name fields. Run results must show `status` as `"success"` for successfully executed models.

## Artifact Contracts

Artifacts are the file-level projections of the project graph state.

**Target path.** The target path defaults to `target/` relative to the active project. When `--target-path PATH` is supplied, all artifacts and compiled files must be written under that path.

**manifest.json.** Produced by parse-capable commands when JSON writing is enabled. It must represent the full enabled project graph. Fields that depend on compilation must appear only for compiled nodes.

**semantic_manifest.json.** Written alongside `manifest.json` when manifest writing occurs.

**run_results.json.** Produced by commands that execute or compile nodes. It must contain top-level `metadata`, `args`, `elapsed_time`, and `results`. Each result must include `unique_id` and status data sufficient to map back to the manifest.

**perf_info.json.** Produced by `dbt parse`. Must describe parser work such as path counts, parser names, and elapsed timings.

**partial_parse.msgpack.** Internal cache file. Its presence, reuse, invalidation, and deletion behavior must match the partial parsing cache rules. Callers must not depend on its serialized schema.

## State Model

dbt-core exposes the same project state through three public projections:

- The command projection: terminal output, command status, and Python runner success values.
- The graph projection: selected resource identifiers and resource fields in `dbt list`/`dbt ls` and manifest-like Python return values.
- The file projection: JSON artifacts, partial-parse cache files, performance info, and compiled SQL files under the target path.

The state model must satisfy these cross-view rules:

- A resource parsed into the graph projection must appear in `manifest.json` when JSON writing is enabled and the resource is enabled.
- A selected executable node compiled by `dbt compile` must appear in `run_results.json` with a successful compile result when compilation succeeds.
- A selected model printed by `dbt list --output name` must correspond to the same resource as a `manifest.json` node with the same package and resource name.
- A target path passed through `--target-path` must be the root for written artifacts and compiled files for that invocation.
- A manifest object returned by `dbtRunner.invoke(["parse"])` must describe the same project resources as the `manifest.json` written by the same invocation when JSON writing is enabled.
- A `dbtRunner.invoke(["list", ...])` list result must contain the same selected strings as the CLI output for the same arguments and project state.

If the project cannot be discovered, the profile cannot be read for commands that require one, YAML or Jinja syntax is invalid, or a selector is invalid, the command must fail with a nonzero status or a `dbtRunnerResult` whose `success` is `False`.

## Error Semantics

Invalid CLI options, unknown options, and malformed command usage must produce a usage failure. In `dbtRunner`, these failures must be returned as `dbtRunnerResult(success=False, exception=..., result=None)` where the exception is a `BaseException`.

A Click exit with code `0` must produce `dbtRunnerResult(success=True)` when no command result object is returned. A Click exit with a nonzero unhandled code must produce `dbtRunnerResult(success=False)`.

Handled command failures, such as selected node failures or command-managed result exits, must produce `success=False` and preserve the command result when a result object exists.

Unhandled exceptions must produce `success=False`, must place the exception object in `dbtRunnerResult.exception`, and must not fabricate a successful result.

If both `--models` and `--select` are passed to `dbt list` or `dbt ls`, dbt-core must raise a runtime error. If both `--models` and `--resource-type` are passed to list commands, dbt-core must raise a runtime error.

If the manifest or graph is unexpectedly absent after command setup, dbt-core must raise an internal error and must not return partial list or compile output.

## Cross-View Invariants

1. `dbt parse` must return a manifest-like object through `dbtRunner` that describes the same enabled resources written to `manifest.json` by the same invocation when JSON writing is enabled.
2. `dbt list --output json` must return resource identities that resolve to entries in `manifest.json` for the same project and target path after parsing succeeds.
3. `dbt list --output path` must return paths that match `original_file_path` values for the same selected resources in `manifest.json`.
4. `dbt ls` must return the same selected strings as `dbt list` for identical arguments, project files, profile, variables, and target path.
5. `dbt compile` must write `run_results.json` entries whose `unique_id` values return matching resource entries in the written `manifest.json`.
6. `dbt compile` must write compiled files and compiled-code fields that represent the same rendered SQL for the selected node.
7. `dbt run` must write `run_results.json` entries only for executed selected nodes, while `manifest.json` must continue to include the full enabled project graph.
8. `--target-path` must redirect `manifest.json`, `semantic_manifest.json`, `run_results.json`, `perf_info.json`, `partial_parse.msgpack`, and compiled SQL files for the invocation.
9. `--no-write-json` must suppress JSON artifact writes without changing the in-memory command result returned by `dbtRunner` for a completed command.
10. Disabling partial parsing must preserve the logical manifest for unchanged project files, while changing only whether the cache participates in parse startup.

## Public Interface

### Import Surface

The package is installed as `dbt-core` and exposes the console script:

```text
dbt = dbt.cli.main:cli
```

The public Python imports in this scope are:

```python
from dbt.cli.main import cli
from dbt.cli.main import dbtRunner
from dbt.cli.main import dbtRunnerResult
from dbt.cli import dbt_cli
```

`dbt_cli` is a re-export of the same Click command group as `cli`. The top-level `dbt` package is a namespace package and must not expose a separate command API from `dbt.__init__`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `cli` | command group | Click command group for the `dbt` console entry point |
| `dbt_cli` | alias | Re-export of the same Click command group as `cli` |
| `dbtRunner` | class | Programmatic command dispatcher with optional cached manifest |
| `dbtRunner.invoke` | method | Run one CLI-equivalent command and return a result object |
| `dbtRunnerResult` | class | Public result container for runner invocations |
| `dbtRunnerResult.success` | attribute | Whether the invocation completed without error |
| `dbtRunnerResult.exception` | attribute | Raised exception for failed invocations, if any |
| `dbtRunnerResult.result` | attribute | Command-specific result object when available |

### CLI Entry Points

The supported console script is `dbt`.

`python -m dbt` is not supported because the `dbt` package does not expose a package `__main__` module. `python -m dbt.cli.main` is supported for module execution of the Click command group.

Exit behavior:

| Scenario | CLI exit status | `dbtRunnerResult.success` | Result | Exception |
|---|---:|---|---|---|
| Invocation completed without error | 0 | `True` | Command-specific result | `None` |
| Invocation completed with handled node or command errors | 1 | `False` | Command-specific result when available | `None` |
| Invocation failed from invalid usage or unhandled exception | 2 or nonzero command failure | `False` | `None` unless a result-bearing exit occurred | Exception object |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Local project files, `dbtRunner` results, list output, manifests, run results, compiled SQL, and partial-parse state are different views of the same project graph. Implementations should derive those views from shared graph state so selection and identity remain consistent across commands.

Service integrations, adapter conformance internals, private helper objects, complete JSON key ordering, and exact terminal wording are outside this contract.
