
# Kedro Specification

## Product Overview

Kedro is a Python framework for defining data pipelines as named nodes, binding node inputs and outputs to a data catalog, loading project configuration from environment folders, and running a registered pipeline from either Python or the `kedro` command line.

This specification covers local pipeline execution. A run must resolve the requested pipeline graph, load inputs from the catalog, execute nodes in dependency order, save outputs back to the catalog, and return the pipeline output dataset objects.

## Scope

The covered feature areas are:

- Pipeline and node construction through `kedro.pipeline.Node`, `kedro.pipeline.node`, `kedro.pipeline.Pipeline`, and `kedro.pipeline.pipeline`.
- Pipeline graph inspection and filtering by inputs, outputs, node names, tags, namespaces, and dependency direction.
- `kedro.io.DataCatalog` with directly supplied datasets, raw values wrapped as `MemoryDataset`, lazy datasets created from configuration, and `MemoryDataset` load/save/release behavior.
- `kedro.config.OmegaConfigLoader` for local YAML, YML, and JSON configuration under `base` and run environment folders.
- Programmatic pipeline execution with `KedroSession.create` and `KedroSession.run`.
- The `kedro run` command as a project command that maps CLI options into `KedroSession.run`.

## Installable Surface

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

## Public API

### Pipeline Nodes

```python
Node(
    func,
    inputs,
    outputs,
    *,
    name=None,
    tags=None,
    confirms=None,
    namespace=None,
    preview_fn=None,
)

node(
    func,
    inputs,
    outputs,
    *,
    name=None,
    tags=None,
    confirms=None,
    namespace=None,
    preview_fn=None,
) -> Node
```

`func` must be callable. `inputs` must be `None`, a dataset name string, a list of dataset name strings, or a dictionary mapping function argument names to dataset name strings. `outputs` must be `None`, a dataset name string, a list of dataset name strings, or a dictionary mapping function return keys to dataset name strings. A node must declare at least one input or one output.

Node names and tags must contain only letters, digits, hyphens, underscores, and periods. Dataset names used as node inputs and outputs must be strings. A node must raise `ValueError` when the function is not callable, when inputs or outputs use unsupported shapes, when declared input names do not bind to the callable signature, when declared outputs contain duplicates, or when any input name is the same dataset as any output name after transcoding markers are ignored.

`Node.run(inputs=None)` must return a dictionary keyed by the node output dataset names. With `inputs=None`, the node receives an empty mapping. A single string input must call the function with one positional value. A list input must call the function with positional values in the declared list order. A dictionary input must call the function with keyword arguments using the dictionary keys as argument names and the dictionary values as catalog dataset names. If the supplied runtime input mapping does not exactly match the declared input dataset names, `Node.run` must raise `ValueError`.

When `outputs` is `None`, `Node.run` must return `{}` and must ignore any function return value. When `outputs` is a string, `Node.run` must bind the whole function return value to that output name. When `outputs` is a list, the function return value must be a list or tuple of the same length, otherwise `Node.run` must raise `ValueError`. When `outputs` is a dictionary, the function return value must be a dictionary with exactly the declared return keys, otherwise `Node.run` must raise `ValueError`; the returned dictionary must use the mapped dataset names as keys.

`Node.inputs`, `Node.outputs`, `Node.confirms`, and `Node.tags` must return lists or sets representing the public node definition. `Node.name` must return the explicit name when provided and must otherwise return the generated unique name for the callable and datasets. `Node.short_name` must return the node name without namespace prefixes. `Node.namespace` must return the node namespace or `None`. `Node.namespace_prefixes` must return namespace prefixes from outermost to innermost. `Node.tag(tags)` must return a new node with the supplied tags added and must leave the original node unchanged.

### Pipelines

```python
Pipeline(
    nodes,
    *,
    inputs=None,
    outputs=None,
    parameters=None,
    tags=None,
    namespace=None,
    prefix_datasets_with_namespace=True,
)

pipeline(
    pipe,
    *,
    inputs=None,
    outputs=None,
    parameters=None,
    tags=None,
    namespace=None,
    prefix_datasets_with_namespace=True,
) -> Pipeline
```

`nodes` must be an iterable of `Node` or `Pipeline` instances, or a `Pipeline`. Pipelines nested inside the iterable must be expanded into their nodes. A pipeline with duplicate node identities, duplicate produced output datasets, duplicate confirmed datasets, or circular dependencies must raise the corresponding pipeline construction error. `nodes=None` must raise `ValueError`.

Pipeline execution order must be dependency order, not input list order. `Pipeline.nodes` must return nodes sorted topologically. `Pipeline.inputs()` must return free input dataset names that are not produced by another node in the pipeline. `Pipeline.outputs()` must return free output dataset names that are not consumed by another node in the pipeline. `Pipeline.all_inputs()`, `Pipeline.all_outputs()`, and `Pipeline.datasets()` must return all declared input names, all declared output names, and all dataset names respectively.

`Pipeline.describe(names_only=True)` must return a readable execution-order description. `Pipeline.node_dependencies` must return each node mapped to the set of upstream nodes it depends on. `Pipeline.grouped_nodes` and `Pipeline.group_nodes_by("namespace")` must return grouped node information preserving dependency relationships between groups. Unsupported grouping criteria must raise `ValueError`.

`Pipeline.only_nodes`, `only_nodes_with_inputs`, `from_inputs`, `only_nodes_with_outputs`, `to_outputs`, `from_nodes`, `to_nodes`, `only_nodes_with_tags`, and `only_nodes_with_namespaces` must return new `Pipeline` objects. Missing requested node names, dataset names, or namespaces must raise `ValueError`. `Pipeline.filter(...)` must apply all supplied filter dimensions as an intersection against the original pipeline and must raise `ValueError` when the resulting pipeline has no nodes. `Pipeline.tag(tags)` must return a new pipeline whose nodes include the supplied tags.

`Pipeline.__add__` and `Pipeline.__or__` must return the union of two pipelines. `Pipeline.__sub__` must return nodes from the left pipeline that are not in the right pipeline. `Pipeline.__and__` must return the intersection. Unsupported operands must return `NotImplemented`.

## Product State Model

Kedro exposes the same run state through three public projections:

1. The pipeline graph projection: `Node` and `Pipeline` objects define dataset dependencies and the subset of nodes selected for a run.
2. The catalog/config projection: `OmegaConfigLoader` returns configuration dictionaries, and `DataCatalog` turns those dictionaries or direct dataset objects into loadable and saveable datasets.
3. The execution projection: `kedro run`, `KedroSession.run`, and runner objects execute a selected pipeline and persist outputs into the catalog.

These projections must stay aligned. A dataset name selected by graph filtering must be the same name used to load from and save to the catalog. A parameter loaded by configuration must be available in the catalog under `parameters`, `params:<name>`, and nested `params:<name>.<field>` keys. A run output returned by the execution projection must identify the same output dataset name that the pipeline graph reports through `Pipeline.outputs()`.

## Configuration Loading

```python
OmegaConfigLoader(
    conf_source,
    env=None,
    runtime_params=None,
    *,
    config_patterns=None,
    base_env=None,
    default_run_env=None,
    custom_resolvers=None,
    merge_strategy=None,
    ignore_hidden=True,
)
```

`conf_source` must point to the root configuration folder or a supported local archive path. For local projects, `base_env` identifies the base configuration folder and `default_run_env` identifies the environment folder used when `env` is not supplied. `OmegaConfigLoader[key]` must load files matching the configured patterns for that key from the base folder first and the selected run environment second.

The default patterns must include `catalog`, `parameters`, `credentials`, and `globals`. Configuration files must be accepted when their extension is `.yml`, `.yaml`, or `.json`. For `catalog`, default matching must include files named like `catalog*`, files under directories named like `catalog*`, and files named like `catalog*` in nested directories. Unknown keys must raise `KeyError`. Known keys with no matching files must raise `MissingConfigException`, except `globals`, which returns an empty mapping when absent.

Within the same environment folder, duplicate non-hidden top-level keys must raise `ValueError`; for `parameters`, duplicate nested keys must raise `ValueError`. Across base and run environment folders, the run environment must override base according to the configured merge strategy. The default `destructive` strategy must replace a colliding top-level key with the run environment value. The `soft` strategy must merge nested dictionaries while preserving non-conflicting nested keys. Unsupported merge strategies must raise `ValueError`.

For `parameters`, `runtime_params` must merge after file configuration and must take precedence over file values. For non-parameter configuration, top-level keys beginning with `_` must be omitted from the returned dictionary when hidden entries are ignored. `credentials` loading must resolve environment-variable interpolation. `globals` interpolation must reject globals keys beginning with `_`; missing globals or runtime parameter resolver values without defaults must raise interpolation resolution errors.

## Data Catalog And Datasets

```python
DataCatalog(
    datasets=None,
    config_resolver=None,
    load_versions=None,
    save_version=None,
)

DataCatalog.from_config(catalog, credentials=None, load_versions=None, save_version=None) -> DataCatalog

MemoryDataset(data=<empty>, copy_mode=None, metadata=None)
```

`DataCatalog` must act as a mapping from dataset names to dataset instances. `keys()`, `values()`, `items()`, iteration, containment, indexing, and `len()` must include both materialized datasets and lazy configured datasets. `catalog[name]` must return a dataset instance and must raise `DatasetNotFoundError` when the name is absent. `catalog.get(name)` must return the dataset instance or `None` when absent.

Assigning an `AbstractDataset` instance with `catalog[name] = dataset` must register that dataset. Assigning any other value must wrap the value in `MemoryDataset` and register it under that name. Reassigning an existing name must replace the previous dataset and clear stale lazy configuration or version state for that name.

`DataCatalog.from_config` must accept a mapping whose values contain a `type` entry plus constructor arguments for the dataset. Core `kedro.io` dataset classes must be loadable by class name or fully qualified path. A `load_versions` entry for a dataset not present in the catalog configuration or dataset factory patterns must raise `DatasetNotFoundError`. A catalog entry that is not a dictionary or lacks `type` must raise `DatasetError`.

`DataCatalog.load(name, version=None)` must load a registered dataset and return its data. It must raise `DatasetNotFoundError` when the dataset is absent and must wrap dataset load failures in `DatasetError` with the dataset name. `DataCatalog.save(name, data)` must save through the registered dataset and must raise `DatasetNotFoundError` when the dataset is absent. `DataCatalog.exists(name)` must return `False` for absent datasets and must otherwise delegate to the dataset. `DataCatalog.release(name)` must release the dataset. `DataCatalog.confirm(name)` must call a dataset `confirm()` method when present and must raise `DatasetError` when absent.

`MemoryDataset` must store data in memory only. Loading before data has been supplied or saved must raise `DatasetError`. Saving data must store a copied value according to `copy_mode`; valid copy modes are `"deepcopy"`, `"copy"`, and `"assign"`. Loading must return a copied value according to the same mode. `release()` must clear the stored value so that a subsequent `load()` raises `DatasetError`. `exists()` must return whether data is currently stored.

## Pipeline Execution

`SequentialRunner().run(pipeline, catalog, only_missing_outputs=False)` must load free inputs from the supplied `DataCatalog`, execute nodes in pipeline dependency order, save each produced dataset through that same catalog, and return the terminal output datasets keyed by the names reported by `Pipeline.outputs()`. A filtered pipeline must execute only its retained nodes while preserving their dependency order.

When a node raises, its downstream nodes must not execute and the original exception must propagate. A missing free input must raise before the affected node executes. A catalog load or save failure must propagate as the corresponding dataset error and must prevent dependent nodes from executing. Dataset confirmations declared by a completed node must be applied through the catalog.

## Session Execution

`bootstrap_project(project_path) -> ProjectMetadata` must locate `pyproject.toml`, read the `[tool.kedro]` project metadata, add the configured source directory to Python's import path, and configure the named project package. It must be called before direct `KedroSession` use in a fresh Python process. The `kedro` command performs this bootstrap automatically when it recognizes a project.

```python
KedroSession.create(
    project_path=None,
    save_on_close=True,
    env=None,
    runtime_params=None,
    conf_source=None,
) -> KedroSession

KedroSession.run(
    pipeline_name=None,
    pipeline_names=None,
    tags=None,
    runner=None,
    node_names=None,
    from_nodes=None,
    to_nodes=None,
    from_inputs=None,
    to_outputs=None,
    load_versions=None,
    namespaces=None,
    only_missing_outputs=False,
) -> dict
```

`KedroSession.create` must return a session for the project selected by `project_path`. The session must use the explicit `env` when one is supplied; otherwise it must use `KEDRO_ENV` when that environment variable is set. Runtime parameters supplied through `runtime_params` must take precedence over parameter values loaded from configuration. As a context manager, leaving the context must close the session, and closing must persist session data when `save_on_close` is true.

`KedroSession.run` must execute one run per session; a second run attempt must raise the session error. When no pipeline is named, the run must select `__default__`. When one or more pipeline names are supplied, it must combine those registered pipelines and must raise `ValueError` when a requested name is absent. It must apply graph filters for tags, node names, node ranges, dataset ranges, and namespaces before execution. It must use a supplied runner instance, or a sequential runner when `runner` is not supplied. Supplying a runner class instead of a runner instance must raise the session error. The return value must be a dictionary whose keys are output dataset names and whose values are dataset objects.

## Run Command

`kedro run` must create a `KedroSession` and call `session.run` with CLI-selected filters and run options. The command must support these option families:

- Pipeline selection: `--pipeline`/`-p`.
- Node selection: `--nodes`/`-n`, `--from-nodes`, and `--to-nodes`.
- Dataset selection: `--from-inputs` and `--to-outputs`.
- Namespace and tag selection: `--namespaces`/`-ns` and `--tags`/`-t`.
- Runner selection: `--runner`/`-r` and `--async`.
- Configuration selection: `--env`, `--conf-source`, `--params`, `--load-versions`/`-lv`, `--config`/`-c`, and `--only-missing-outputs`.

Comma-separated CLI values must be split before they are passed to the session. `--params` must become runtime parameters for the session. `--runner` must resolve a runner class name or dotted path and instantiate it. If the current directory is not inside a Kedro project, `kedro run` must fail with a non-zero exit and report that project commands are available only inside a project.

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

## Representative Workflow

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

## Non-Goals

This specification excludes project creation from starters, cookiecutter template rendering, telemetry, server and HTTP APIs, Jupyter and IPython magics, rich terminal formatting details, cloud or remote storage behavior, contributed `kedro-datasets` implementations beyond their use as catalog class paths, dataset versioning internals, hook plugin ordering beyond session calls, parallel/shared-memory execution details, LLM context helpers, and exact log text.

## Invocation Protocol

| Invocation | Support | Result |
|---|---|---|
| `kedro --help` | supported | exits `0` and lists global commands |
| `python -m kedro --help` | supported | exits `0` and lists global commands |
| `kedro run` inside a Kedro project | supported | exits `0` when the selected pipeline run completes successfully |
| `kedro run` outside a Kedro project | supported failure | exits non-zero and reports that project commands require a project |
| `python -m kedro run` inside a Kedro project | supported | follows the same project command behavior as the console script |

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Project, catalog, and configuration workflows use local temporary directories and in-memory datasets.

## Evaluation Notes

Assessment covers the documented imports, graph construction and filtering, catalog behavior, dataset state, configuration merges, session execution, command option mapping, and agreement among graph, catalog, configuration, and run outputs. Internal helper names, private attributes, exact log prose, and terminal styling are outside the contract.
