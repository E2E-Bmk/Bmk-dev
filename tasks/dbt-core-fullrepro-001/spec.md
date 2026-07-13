# dbt-core Specification

## Product Overview

dbt-core reads a local dbt project, resolves project resources into a graph, and exposes that graph through command-line commands, JSON artifacts, compiled SQL files, and the Python `dbtRunner` interface. The project graph is the central state: parsing builds it, selection queries it, compilation enriches selected executable nodes with rendered SQL, and JSON artifacts serialize the public view of the invocation.

This specification covers dbt-core 1.10 behavior for local project parsing and compilation workflows. It focuses on observable files, command results, and Python runner results for projects that have local files, a valid project configuration, and a usable profile for commands that require one.

## Scope

The covered feature areas are:

- Local project discovery through `dbt_project.yml`, `profiles.yml`, `--project-dir`, `--profiles-dir`, `--target`, `--target-path`, `--threads`, and `--vars`.
- The `dbt parse`, `dbt list`, `dbt ls`, `dbt compile`, and `dbt run` command surfaces where they expose local project graph, selection, compiled SQL, and artifacts.
- Selection and exclusion of models, tests, sources, exposures, metrics, semantic models, saved queries, seeds, snapshots, analyses, and unit tests as public resource categories.
- Artifact emission for `manifest.json`, `semantic_manifest.json`, `run_results.json`, `perf_info.json`, and `partial_parse.msgpack`.
- Compiled SQL file emission under the target path for selected executable resources.
- Python invocation through `dbt.cli.main.dbtRunner` and result reporting through `dbt.cli.main.dbtRunnerResult`.

## Installable Surface

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

## Public API

### Command Forms

The command-line entry point must accept:

```text
dbt parse [GLOBAL_FLAGS]
dbt list [GLOBAL_FLAGS] [LIST_FLAGS]
dbt ls [GLOBAL_FLAGS] [LIST_FLAGS]
dbt compile [GLOBAL_FLAGS] [COMPILE_FLAGS]
dbt run [GLOBAL_FLAGS] [RUN_FLAGS]
```

`dbt ls` must behave as an alias of `dbt list`. The alias must accept the same arguments and return the same selected resources for the same project state.

The global flags in scope are:

```text
--project-dir PATH
--profiles-dir PATH
--profile NAME
--target NAME
--target-path PATH
--threads N
--vars YAML
--partial-parse / --no-partial-parse
--write-json / --no-write-json
--state PATH
--defer / --no-defer
--defer-state PATH
--favor-state / --no-favor-state
--cache-selected-only / --no-cache-selected-only
--populate-cache / --no-populate-cache
--static-parser / --no-static-parser
--version-check / --no-version-check
--quiet / --no-quiet
--debug / --no-debug
--warn-error
--warn-error-options YAML
```

The list flags in scope are:

```text
--select SELECTION...
--models SELECTION...
--exclude SELECTION...
--selector NAME
--resource-type TYPE...
--resource-types TYPE...
--exclude-resource-type TYPE...
--exclude-resource-types TYPE...
--output selector|name|path|json
--output-keys KEY...
```

The compile flags in scope are:

```text
--select SELECTION...
--exclude SELECTION...
--selector NAME
--inline SQL
--output text|json
--introspect / --no-introspect
--empty / --no-empty
--full-refresh
```

The run flags in scope are:

```text
--select SELECTION...
--exclude SELECTION...
--selector NAME
--resource-type TYPE...
--resource-types TYPE...
--exclude-resource-type TYPE...
--exclude-resource-types TYPE...
--empty / --no-empty
--full-refresh
```

### Python Runner

`dbtRunner` must have this constructor and invocation shape:

```python
dbtRunner(
    manifest: Optional[Manifest] = None,
    callbacks: Optional[List[Callable[[EventMsg], None]]] = None,
)

dbtRunner.invoke(args: List[str], **kwargs) -> dbtRunnerResult
```

`dbtRunnerResult` must have these public attributes:

```python
success: bool
exception: Optional[BaseException] = None
result: object = None
```

When `dbtRunner.invoke` receives `args`, the first command token must follow the same command grammar as the CLI. When keyword arguments are supplied, their keys must be applied as command parameters for that invocation. Keyword arguments must not perform extra type coercion beyond the command layer.

When a command completes without errors, `dbtRunnerResult.success` must be `True`, `exception` must be `None`, and `result` must hold the command result. When a command completes with handled node failures, `success` must be `False`, `exception` must be `None`, and `result` must hold the command result. When invocation cannot complete because of an unhandled error or invalid usage, `success` must be `False`, `result` must be `None` unless the command raised a result-bearing exit, and `exception` must contain the raised exception.

For commands in this scope, `dbtRunnerResult.result` must return a manifest-like object for `parse`, a list of strings for `list` and `ls`, and a run-execution-result-like object for `compile` and `run`.

## Product State Model

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

## Parsing And Manifest Behavior

`dbt parse` must read and validate the local project. It must construct a manifest representing the project's enabled resources, including models, tests, sources, macros, docs blocks, exposures, metrics, semantic models, saved queries, seeds, snapshots, analyses, unit tests, parent maps, child maps, selectors, disabled resources, and metadata where those resource types are present.

When parsing succeeds and JSON writing is enabled, dbt-core must write `manifest.json` and `semantic_manifest.json` to the target path. `manifest.json` must contain top-level dictionaries or arrays for the public resource collections and dependency maps. Resource entries must include public identity fields such as `name`, `unique_id`, `package_name`, `path`, `original_file_path`, and `resource_type` when those fields apply to the resource.

When `dbt parse` succeeds, it must write `perf_info.json` to the target path. The file must contain parser timing and path-count information for the projects parsed during the invocation.

When `dbt parse` succeeds, the manifest must not contain compiled SQL for ordinary model nodes that were only parsed. If a caller needs compiled SQL, the caller must run `dbt compile` or another command that compiles selected nodes.

When project files contain invalid YAML, invalid Jinja, unresolved required references, duplicate resource identities, invalid protected or private references, or invalid project/profile configuration, parsing must fail and must not report a successful command result.

When `--write-json` is disabled, commands must avoid writing JSON artifacts for that invocation. They must still return their command result through the Python runner when the command completes.

## Selection And List Behavior

`dbt list` and `dbt ls` must list resources in the parsed project without running SQL queries against the data platform. The command must read the connection profile when target-specific project logic requires it.

By default, list output must include models, snapshots, seeds, tests, sources, exposures, metrics, saved queries, semantic models, and unit tests. Analysis resources must be included only when selected through `--resource-type analysis`, `--resource-types analysis`, or an all-resource selection that includes analysis.

`--models` must select only model resources and must be mutually exclusive with `--select` and `--resource-type` for list commands. When a caller combines `--models` with either of those arguments, dbt-core must raise a runtime error and the command must not report success.

`--select`, `--exclude`, and `--selector` must filter the graph using dbt resource selection semantics. `--exclude` must remove matching resources from the selected set. When no resources are selected, the command must return an empty result list and must emit the no-nodes-selected warning behavior for the command surface.

`--output selector` must return selection strings that identify the selected resources. Source resources must use `source:package.source_name.table_name`, exposures must use `exposure:package.name`, metrics must use `metric:package.name`, saved queries must use `saved_query:package.name`, semantic models must use `semantic_model:package.name`, unit tests must use `unit_test:package.versioned_name`, and ordinary graph nodes must use their fully qualified name joined by periods.

`--output name` must return each selected resource's search name. `--output path` must return each selected resource's `original_file_path`. `--output json` must return one JSON object per selected resource. When `--output-keys` is omitted, JSON output must include the supported default keys only. When `--output-keys` is supplied, JSON output must include the requested keys that exist on the resource.

Disabled resources must not appear in list output. Schema tests that depend on disabled models must not appear in list output. Returned resources must have `config.enabled` equal to `true` when that config field is present.

If selection returns a resource type that list does not support, dbt-core must raise a runtime error rather than silently printing an unsupported object.

## Compile, Run, And Compiled Files

`dbt compile` must parse the project, select executable resources, render Jinja and dbt macros for selected resources, and write compiled SQL under the target path. It must not materialize model results into database relations.

When `dbt compile` succeeds and JSON writing is enabled, dbt-core must write `manifest.json`, `semantic_manifest.json`, and `run_results.json` to the target path. The manifest must include all enabled project resources, while `run_results.json` must include only nodes executed or compiled by the invocation.

When `dbt compile --select NAME` selects a model, test, analysis, snapshot, seed, or SQL operation that compiles successfully, that node's result in `run_results.json` must have a successful status, `compiled` equal to `true`, a non-empty `compiled_code` when the node has SQL code, and a `unique_id` that maps to the corresponding manifest entry.

When `dbt compile --inline SQL` is used, dbt-core must compile the inline query as a temporary SQL operation named `inline_query`, print or return the compiled SQL according to the selected output mode, and remove the temporary inline node from the persistent manifest before the command completes.

When `dbt compile --output json` is used for interactive compile output, the compiled node output must be emitted in JSON form. When `--output text` is used or omitted, compiled output must be emitted as text.

When compilation of a selected node fails because of invalid SQL templating, invalid refs or sources, unavailable required metadata while introspection is disabled, or another compilation error, the command must fail and must not mark the node as successfully compiled.

`dbt run` must compile selected executable model resources and execute them through the configured adapter. When `dbt run` completes and JSON writing is enabled, `run_results.json` must include only executed selected nodes and must include status, timing, thread id, execution time, message, adapter response, failures when applicable, `unique_id`, compiled state, compiled code, and relation name fields where those fields apply.

## Partial Parsing Cache

When partial parsing is enabled, dbt-core must use `partial_parse.msgpack` in the target path as the persistent cache of parsed project state. After a successful parse-capable invocation, dbt-core must write or update that file when the manifest state is suitable for reuse.

When a later invocation uses the same target path and partial parsing remains enabled, dbt-core must compare current project inputs with the saved cache and must parse only changed files and dependent files when the cache is valid.

When `--no-partial-parse` is supplied, dbt-core must perform a full parse and must not rely on `partial_parse.msgpack` for the command result.

When `--vars`, profile contents, project configuration, installed packages, dbt version, or widely used override macros change in a way that invalidates the saved cache, dbt-core must fall back to a full parse and must still produce a correct manifest if the project is otherwise valid.

When partial parsing produces stale or invalid project state, callers must be able to force a correct full parse by running with `--no-partial-parse` or by deleting `target/partial_parse.msgpack`.

When the cache file is missing, unreadable, generated by an incompatible dbt version, or invalid for the current project, dbt-core must parse from project files and must not report success from stale cache contents.

## Artifact Contracts

The target path defaults to `target/` relative to the active project. When `--target-path PATH` is supplied, all covered artifacts and compiled files for that invocation must be written under that path.

`manifest.json` must be produced by parse-capable commands when JSON writing is enabled. The file must represent the full enabled project graph rather than only selected nodes. Fields whose values depend on compilation must appear only for nodes that were compiled by the invocation.

`semantic_manifest.json` must be written alongside `manifest.json` when manifest writing occurs.

`run_results.json` must be produced by commands that execute or compile nodes, including `compile` and `run`, when JSON writing is enabled. It must contain top-level `metadata`, `args`, `elapsed_time`, and `results`. Each result must include `unique_id` and status data sufficient to map the result back to the manifest.

`perf_info.json` must be produced by `dbt parse` and must describe parser work such as path counts, parser names, and elapsed timings.

`partial_parse.msgpack` is an internal cache file with public file-level behavior. Callers must not depend on its serialized schema, but its presence, reuse, invalidation, and deletion behavior must match the partial parsing cache rules above.

If artifact writing fails because the target path is not writable, the command must fail or return a failed runner result rather than silently claiming successful artifact emission.

## Error Semantics

Invalid CLI options, unknown options, and malformed command usage must produce a usage failure. In `dbtRunner`, these failures must be returned as `dbtRunnerResult(success=False, exception=DbtUsageException(...), result=None)`.

A Click exit with code `0` must produce `dbtRunnerResult(success=True)` when no command result object is returned. A Click exit with a nonzero unhandled code must produce `dbtRunnerResult(success=False, exception=DbtInternalException(...), result=None)`.

Handled command failures, such as selected node failures or command-managed result exits, must produce `success=False` and preserve the command result when a result object exists.

Unhandled exceptions must produce `success=False`, must place the exception object in `dbtRunnerResult.exception`, and must not fabricate a successful result.

If both `--models` and `--select` are passed to `dbt list` or `dbt ls`, dbt-core must raise a runtime error. If both `--models` and `--resource-type` are passed to list commands, dbt-core must raise a runtime error.

If the manifest or graph is unexpectedly absent after command setup, dbt-core must raise an internal error and must not return partial list or compile output.

If no selected executable nodes are available for a runnable command, dbt-core must warn or error according to warning configuration and must return an empty run-execution result for the command surface when the warning is not promoted to an error.

## Cross-View Invariants

- `dbt parse` must return a manifest-like object through `dbtRunner` that describes the same enabled resources written to `manifest.json` by the same invocation when JSON writing is enabled.
- `dbt list --output json` returns resource identities that must resolve to entries in `manifest.json` for the same project and target path after parsing succeeds.
- `dbt list --output path` returns paths that must match `original_file_path` values for the same selected resources in `manifest.json`.
- `dbt ls` returns the same selected strings as `dbt list` for identical arguments, project files, profile, variables, and target path.
- `dbt compile` must write `run_results.json` entries whose `unique_id` values return matching resource entries in the written `manifest.json`.
- `dbt compile` must write compiled files and compiled-code fields that represent the same rendered SQL for the selected node, ignoring differences that are only file formatting or terminal formatting.
- `dbt run` must write `run_results.json` entries only for executed selected nodes, while `manifest.json` must continue to include the full enabled project graph.
- `--target-path` must redirect `manifest.json`, `semantic_manifest.json`, `run_results.json`, `perf_info.json`, `partial_parse.msgpack`, and compiled SQL files for the invocation.
- `--no-write-json` must suppress JSON artifact writes without changing the in-memory command result returned by `dbtRunner` for a completed command.
- Disabling partial parsing must preserve the logical manifest for unchanged project files, while changing only whether the cache participates in parse startup.

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

## Non-Goals

This specification does not cover adapter conformance behavior, PostgreSQL service tests, cloud services, RPC server lifecycle, dbt platform features, package installation, documentation site generation, source freshness execution, snapshot semantics, seed loading semantics, data test pass/fail semantics, or adapter-specific SQL execution details.

This specification does not require byte-for-byte equality of complete `manifest.json` or `run_results.json` files. It requires the public artifact fields and cross-view relationships described above.

This specification does not require reproducing private helper modules, `dbt.tests` fixtures, hidden Click parameters, internal parser class names, internal msgpack schema details, or exact terminal log wording.

## Invocation Protocol

The supported console script is `dbt`.

`python -m dbt` is not supported because the `dbt` package does not expose a package `__main__` module. `python -m dbt.cli.main` is supported for module execution of the Click command group.

Exit behavior:

| Scenario | CLI exit status | `dbtRunnerResult.success` | Result | Exception |
|---|---:|---|---|---|
| Invocation completed without error | 0 | `True` | Command-specific result | `None` |
| Invocation completed with handled node or command errors | 1 | `False` | Command-specific result when available | `None` |
| Invocation failed from invalid usage or unhandled exception | 2 or nonzero command failure | `False` | `None` unless a result-bearing exit occurred | Exception object |

## Implementation Guidance

Automated checks exercise public behavior through local project files, CLI invocations, Python `dbtRunner` calls, and emitted artifacts. They inspect command status, runner result objects, selected list output, artifact presence, key artifact fields, compiled SQL projections, partial-parse cache reuse and invalidation, and the relationships between list output, manifest entries, run results, and compiled files.

The checks intentionally avoid service dependencies and adapter conformance suites. They compare observable behavior and public fields rather than private helper objects, complete JSON snapshots, or exact terminal wording.

