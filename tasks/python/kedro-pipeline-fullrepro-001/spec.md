# Kedro Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

This package is a Python framework for defining data pipelines as named nodes, binding node inputs and outputs to a data catalog, loading project configuration from environment folders, and running a registered pipeline from either Python or the `kedro` command line.

This specification covers local pipeline execution. A run must resolve the requested pipeline graph, load inputs from the catalog, execute nodes in dependency order, save outputs back to the catalog, and return the pipeline output dataset objects.

## Non-Goals

- This specification does not require Project creation from starters or cookiecutter template rendering.
- This specification does not require Telemetry, server and HTTP APIs, Jupyter and IPython magics, or rich terminal formatting details.
- This specification does not require Cloud or remote storage behavior.
- This specification does not require Contributed dataset implementations beyond their use as catalog class paths.
- This specification does not require Dataset versioning internals, hook plugin ordering beyond session calls, or parallel or shared-memory execution details.
- This specification does not require LLM context helpers or exact log text.

## Representative Workflows

```python
from pathlib import Path

from kedro.config import OmegaConfigLoader
from kedro.framework.session import KedroSession
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline, node

def add_one(x):
    return x + 1

def double(y):
    return y * 2

pipe = Pipeline(
    [
        node(add_one, "x", "y", name="add_one", tags="math"),
        node(double, "y", "z", name="double"),
    ]
)

catalog = DataCatalog({"x": MemoryDataset(2)})
first_result = pipe.nodes[0].run({"x": catalog.load("x")})
catalog.save("y", first_result["y"])

conf_loader = OmegaConfigLoader(
    conf_source="project-config",
    base_env="base",
    default_run_env="local",
    runtime_params={"example": 1},
)

bootstrap_project(Path.cwd())
with KedroSession.create(
    project_path=Path.cwd(),
    runtime_params={"example": 2},
) as session:
    outputs = session.run(tags=["math"])
```

The direct node run must produce `{"y": 3}`. The catalog save must make `catalog.load("y")` return `3`. The configuration loader must merge the base environment with the selected run environment before runtime parameters are applied to parameters. The session run must execute the pipeline selected by the project and return output dataset objects keyed by output dataset name.

## Configuration Loading

This section covers how project configuration files are discovered, merged, and resolved.

**Loader construction.** `OmegaConfigLoader` must accept `conf_source` pointing to the root configuration folder, `base_env` identifying the base configuration folder, `default_run_env` identifying the environment folder used when no explicit `env` is supplied, `runtime_params` for runtime parameter overrides, `merge_strategy` controlling how base and environment values combine, and additional options including `config_patterns`, `custom_resolvers`, and `ignore_hidden`.

**Loading by key.** Accessing a loader by key (e.g., `loader["parameters"]`, `loader["catalog"]`) must load files matching the configured patterns for that key from the base folder first and the selected run environment second. The default patterns must include `catalog`, `parameters`, `credentials`, and `globals`. Configuration files must be accepted when their extension is `.yml`, `.yaml`, or `.json`. Unknown keys must raise `KeyError`. Known keys with no matching files must raise `MissingConfigException`, except `globals`, which must return an empty mapping when absent.

**Duplicate key handling.** Within the same environment folder, duplicate non-hidden top-level keys must raise `ValueError`. For `parameters`, duplicate nested keys must raise `ValueError`.

**Merge strategies.** The default `destructive` strategy must replace a colliding top-level key with the run environment value. The `soft` strategy must merge nested dictionaries while preserving non-conflicting nested keys from the base environment. Unsupported merge strategies must raise `ValueError`.

**Runtime parameters.** For `parameters`, values supplied through `runtime_params` must merge after file configuration and must take precedence over file values. For non-parameter configuration, top-level keys beginning with `_` must be omitted from the returned dictionary when hidden entries are ignored.

## Data Catalog and Datasets

This section covers how datasets are registered, loaded, saved, and managed.

**Catalog as mapping.** `DataCatalog` must act as a mapping from dataset names to dataset instances. `keys()`, `values()`, `items()`, iteration, containment, indexing, and `len()` must include both materialized datasets and lazy configured datasets. `catalog[name]` must return a dataset instance and must raise `DatasetNotFoundError` when the name is absent. `catalog.get(name)` must return the dataset instance or `None` when absent.

**Assignment behavior.** Assigning an `AbstractDataset` instance with `catalog[name] = dataset` must register that dataset. Assigning any other value must wrap the value in `MemoryDataset` and register it under that name. Reassigning an existing name must replace the previous dataset.

**Building from config.** `DataCatalog.from_config` must accept a mapping whose values contain a `type` entry plus constructor arguments for the dataset. Core `kedro.io` dataset classes must be loadable by class name or fully qualified path. A `load_versions` entry for a dataset not present in the catalog configuration must raise `DatasetNotFoundError`. A catalog entry that is not a dictionary or lacks `type` must raise `DatasetError`.

**Load, save, and lifecycle.** `DataCatalog.load(name)` must load a registered dataset and return its data; it must raise `DatasetNotFoundError` when the dataset is absent and must wrap dataset load failures in `DatasetError`. `DataCatalog.save(name, data)` must save through the registered dataset and must raise `DatasetNotFoundError` when the dataset is absent. `DataCatalog.exists(name)` must return `False` for absent datasets and must otherwise delegate to the dataset. `DataCatalog.release(name)` must release the dataset. `DataCatalog.confirm(name)` must call a dataset `confirm()` method when present and must raise `DatasetError` when the dataset lacks a `confirm` method.

**MemoryDataset.** `MemoryDataset` must store data in memory only. Loading before data has been supplied or saved must raise `DatasetError`. Saving data must store a copied value according to `copy_mode`; valid copy modes are `"deepcopy"`, `"copy"`, and `"assign"`. Loading must return a copied value according to the same mode; with `"deepcopy"`, mutations to loaded data must not affect the stored copy. With `"assign"`, loading must return the same object reference. An unsupported `copy_mode` must raise `DatasetError`. `release()` must clear the stored value so that a subsequent `load()` raises `DatasetError`. `exists()` must return whether data is currently stored.

## Pipeline Graph and Filtering

This section covers how nodes and pipelines define execution graphs and how filtering selects subsets.

**Node construction.** The `node` factory must return a `Node` binding a callable to dataset inputs and outputs. `inputs` may be `None`, one dataset name, a list of dataset names, or a mapping from argument names to dataset names. `outputs` may be `None`, one dataset name, a list of dataset names, or a mapping from return keys to dataset names. A node must declare at least one input or one output. A non-callable function argument must raise `ValueError`. Inputs that do not bind to the callable signature must raise `TypeError`. Duplicate output names and same-input-output datasets must raise `ValueError`.

**Node metadata.** `Node.name` must return the explicit name when provided. `Node.short_name` must return the name without namespace prefixes. `Node.namespace` must return the node namespace or `None`. `Node.namespace_prefixes` must return namespace prefixes from outermost to innermost. `Node.inputs`, `Node.outputs`, `Node.confirms`, and `Node.tags` must return lists or sets representing the public node definition.

**Node.run behavior.** When `inputs` is `None`, `Node.run()` must call the function without arguments. With a single string input, it must call the function with one positional value. With a list input, it must call the function with positional values in declared order. With a dictionary input, it must call the function with keyword arguments. Supplied runtime inputs that do not exactly match declared input dataset names must raise `ValueError`.

When `outputs` is `None`, `Node.run` must return `{}`. When `outputs` is a string, it must bind the whole return value. When `outputs` is a list, the return value must be a sequence of matching length, otherwise `ValueError` must be raised. When `outputs` is a dictionary, the return value must be a dictionary with the declared return keys, and the result must use the mapped dataset names as keys.

**Node tagging.** `Node.tag(tags)` must return a new node with the supplied tags added while leaving the original node unchanged.

**Pipeline construction.** `Pipeline` accepts an iterable of `Node` or nested `Pipeline` instances. Nested pipelines must be expanded. Duplicate produced output datasets, duplicate confirmed datasets, or circular dependencies must raise the corresponding construction error. `nodes=None` must raise `ValueError`.

**Pipeline properties.** `Pipeline.nodes` must return nodes in topological dependency order, not input list order. `Pipeline.inputs()` must return free input dataset names not produced by another node. `Pipeline.outputs()` must return free output dataset names not consumed by another node. `Pipeline.all_inputs()`, `Pipeline.all_outputs()`, and `Pipeline.datasets()` must return all declared names. `Pipeline.node_dependencies` must return each node mapped to its upstream dependencies. `Pipeline.describe(names_only=True)` must return a readable execution-order description.

**Pipeline filtering.** `Pipeline.only_nodes`, `only_nodes_with_inputs`, `from_inputs`, `only_nodes_with_outputs`, `to_outputs`, `from_nodes`, `to_nodes`, `only_nodes_with_tags`, and `only_nodes_with_namespaces` must return new `Pipeline` objects. Missing requested names must raise `ValueError`. `Pipeline.filter(...)` must apply all supplied filter dimensions as an intersection and must raise `ValueError` when the result has no nodes.

**Pipeline operators.** `Pipeline.__add__` and `Pipeline.__or__` must return the union. `Pipeline.__sub__` must return the difference. `Pipeline.__and__` must return the intersection.

**Pipeline factory with namespace.** The `pipeline` factory function must accept a `Pipeline` or iterable of nodes along with a `namespace` parameter. When `namespace` is supplied, node names and non-free dataset names must be prefixed with the namespace. Datasets listed in `inputs` must remain unprefixed as free inputs.

**Pipeline tagging.** `Pipeline.tag(tags)` must return a new pipeline whose nodes include the supplied tags, leaving the original pipeline unchanged.

## Pipeline Execution

This section covers how runners execute pipeline graphs through a catalog.

**Sequential execution.** `SequentialRunner().run(pipeline, catalog)` must load free inputs from the supplied `DataCatalog`, execute nodes in pipeline dependency order, save each produced dataset through that same catalog, and return the terminal output datasets keyed by the names reported by `Pipeline.outputs()`. The returned values must be dataset instances that can be loaded.

**Error propagation.** When a node raises, its downstream nodes must not execute and the original exception must propagate. A missing free input must raise before the affected node executes. A catalog load or save failure must propagate as the corresponding dataset error and must prevent dependent nodes from executing.

**Confirmations.** Dataset confirmations declared by a completed node (via `confirms`) must be applied through the catalog after that node completes.

## Session Execution

This section covers how a Kedro project session orchestrates a pipeline run.

**Bootstrap.** `bootstrap_project(project_path)` must locate `pyproject.toml`, read the `[tool.kedro]` project metadata, add the configured source directory to Python's import path, and configure the named project package. It must return a `ProjectMetadata` whose `project_path` matches the supplied path. It must be called before direct `KedroSession` use in a fresh Python process.

**Session creation.** `KedroSession.create` must return a session for the project. The session must use the explicit `env` when one is supplied; otherwise it must use `KEDRO_ENV` when that environment variable is set. Runtime parameters supplied through `runtime_params` must take precedence over parameter values loaded from configuration. As a context manager, leaving the context must close the session.

**Session run.** `KedroSession.run` must execute one run per session; a second run attempt must raise the session error. When no pipeline is named, the run must select `__default__`. When `pipeline_name` is supplied, it must select that registered pipeline and must raise `ValueError` when the name is absent. It must apply graph filters for `tags`, `node_names`, `from_nodes`, `to_nodes`, `from_inputs`, `to_outputs`, and `namespaces` before execution. It must use a supplied runner instance, or a sequential runner when `runner` is not supplied. The return value must be a dictionary whose keys are output dataset names and whose values are dataset objects.

## Run Command

`kedro run` must create a `KedroSession` and call `session.run` with CLI-selected filters and run options.

**Pipeline and node selection.** The command must support `--pipeline`/`-p` for pipeline selection, `--nodes`/`-n`, `--from-nodes`, `--to-nodes` for node selection, `--from-inputs` and `--to-outputs` for dataset selection, `--namespaces`/`-ns` and `--tags`/`-t` for namespace and tag selection.

**Runner and configuration.** Runner selection via `--runner`/`-r` must resolve a runner class name or dotted path and instantiate it. Configuration options include `--env`, `--conf-source`, `--params` (becoming runtime parameters), `--load-versions`/`-lv`, `--config`/`-c`, and `--only-missing-outputs`.

**CLI value splitting.** Comma-separated CLI values must be split before they are passed to the session.

**Project requirement.** If the current directory is not inside a Kedro project, `kedro run` must fail with a non-zero exit and report that project commands are available only inside a project.

## State Model

Kedro exposes the same run state through three public projections:

1. The pipeline graph projection: `Node` and `Pipeline` objects define dataset dependencies and the subset of nodes selected for a run.
2. The catalog/config projection: `OmegaConfigLoader` returns configuration dictionaries, and `DataCatalog` turns those dictionaries or direct dataset objects into loadable and saveable datasets.
3. The execution projection: `kedro run`, `KedroSession.run`, and runner objects execute a selected pipeline and persist outputs into the catalog.

These projections must stay aligned. A dataset name selected by graph filtering must be the same name used to load from and save to the catalog. A parameter loaded by configuration must be available in the catalog under `parameters`, `params:<name>`, and nested `params:<name>.<field>` keys. A run output returned by the execution projection must identify the same output dataset name that the pipeline graph reports through `Pipeline.outputs()`.

## Error Semantics

- `Node` construction must raise `ValueError` for invalid node definitions and `TypeError` when declared inputs do not bind to the callable signature.
- `Node.run` must raise `ValueError` for runtime input mismatches and output shape mismatches.
- `Pipeline` construction must raise `ValueError`, `PipelineError`, `OutputNotUniqueError`, `ConfirmNotUniqueError`, or `CircularDependencyError` for the corresponding invalid graph condition.
- Pipeline filtering methods must raise `ValueError` when requested names, datasets, tags, or namespaces leave no matching node where the method requires a match.
- `OmegaConfigLoader.__getitem__` must raise `KeyError` for unknown config keys, `MissingConfigException` for absent matching config files, `ValueError` for duplicate keys in one environment, and parser errors for malformed YAML or JSON.
- `DataCatalog.__getitem__`, `load`, `save`, `release`, and `confirm` must raise `DatasetNotFoundError` for absent datasets where a dataset is required.
- `DataCatalog.from_config` and lazy dataset materialization must raise `DatasetError` for invalid dataset configuration.
- `MemoryDataset.load` must raise `DatasetError` when no data is stored.
- `KedroSession.run` must raise the session error for multiple runs in one session or for a runner class supplied where a runner instance is required, and must raise `ValueError` for missing pipeline names.

## Cross-View Invariants

1. A dataset name returned by `Pipeline.inputs()` must be the same key that `DataCatalog.load(name)` reads when that dataset is supplied to a run.
2. A dataset name returned by `Pipeline.outputs()` must be the same key that `DataCatalog.save(name, data)` writes when a terminal node produces that output.
3. A value assigned through `catalog[name] = raw_value` must be returned by `catalog.load(name)` and must appear as a `MemoryDataset` through `catalog[name]`.
4. A value saved through `catalog.save(name, value)` into a `MemoryDataset` must be returned by `catalog.load(name)` until `catalog.release(name)` is called.
5. A parameter loaded by `OmegaConfigLoader["parameters"]` must be present in the run catalog as `parameters`, `params:<name>`, and nested `params:<name>.<field>` entries when a session context builds the catalog.
6. A top-level catalog entry returned by `OmegaConfigLoader["catalog"]` must become a dataset name accepted by `DataCatalog.from_config(...).load`, `save`, `exists`, and indexing when the dataset type is available.
7. A pipeline subset selected by `Pipeline.filter(...)` must be the same subset executed by `KedroSession.run` when the corresponding CLI or API filter arguments are supplied.
8. A terminal output dataset produced by a runner must appear in the dictionary returned from the run and must be loadable from the same catalog under the same dataset name.
9. An environment-specific config value that overrides a base catalog entry must be the value used to construct the dataset for `kedro run` and for manual `OmegaConfigLoader` plus `DataCatalog.from_config` usage.
10. Runtime parameters supplied to `KedroSession.create(runtime_params=...)` must override file-loaded parameter values for the same keys and must be the values supplied to nodes that consume the corresponding `params:` datasets.

## Public Interface

### Import Surface

The package must expose these import paths:

```python
from kedro.pipeline import Node, Pipeline, GroupedNodes, node, pipeline
from kedro.io import AbstractDataset, DataCatalog, MemoryDataset
from kedro.io import DatasetError, DatasetNotFoundError, DatasetAlreadyExistsError
from kedro.config import AbstractConfigLoader, BadConfigException, MissingConfigException, OmegaConfigLoader
from kedro.framework.session import KedroSession
from kedro.framework.startup import ProjectMetadata, bootstrap_project
from kedro.runner import SequentialRunner
```

The installed console script must be named `kedro` and must dispatch to Kedro's CLI. Invocation with `python -m kedro` is supported for the same global CLI entry point. The `run` command is a project command and must be available when the current directory or one of its parents is a Kedro project.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Node` | class | One pipeline step with callable, inputs, outputs, and metadata |
| `node` | function | Factory for `Node` instances |
| `Pipeline` | class | Ordered graph of nodes with filtering and composition |
| `pipeline` | function | Factory for `Pipeline` instances with namespace support |
| `GroupedNodes` | class | Grouped node view for namespace or tag grouping |
| `AbstractDataset` | class | Base dataset contract for load, save, and release |
| `DataCatalog` | class | Named dataset registry and load/save surface |
| `MemoryDataset` | class | In-memory dataset storage |
| `DatasetError` | exception | Dataset operation failure |
| `DatasetNotFoundError` | exception | Missing dataset name |
| `DatasetAlreadyExistsError` | exception | Duplicate dataset registration |
| `AbstractConfigLoader` | class | Base configuration loader contract |
| `OmegaConfigLoader` | class | OmegaConf-backed project configuration loader |
| `BadConfigException` | exception | Invalid configuration content |
| `MissingConfigException` | exception | Missing required configuration files |
| `KedroSession` | class | Project session with one run lifecycle |
| `ProjectMetadata` | class | Project bootstrap metadata |
| `bootstrap_project` | function | Locates project metadata and configures imports |
| `SequentialRunner` | class | Executes pipeline nodes in dependency order |

### CLI Entry Points

| Invocation | Support | Result |
|---|---|---|
| `kedro --help` | supported | exits `0` and lists global commands |
| `python -m kedro --help` | supported | exits `0` and lists global commands |
| `kedro run` inside a Kedro project | supported | exits `0` when the selected pipeline run completes successfully |
| `kedro run` outside a Kedro project | supported failure | exits non-zero and reports that project commands require a project |
| `python -m kedro run` inside a Kedro project | supported | follows the same project command behavior as the console script |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Project, catalog, and configuration workflows use local temporary directories and in-memory datasets.

## Appendix B: Assessment Notes

Assessment covers the documented imports, graph construction and filtering, catalog behavior, dataset state, configuration merges, session execution, command option mapping, and agreement among graph, catalog, configuration, and run outputs. Internal helper names, private attributes, exact log prose, and terminal styling are outside the contract.
