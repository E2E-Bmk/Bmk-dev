# DVC Specification

## Product Overview

DVC is a command-line and Python-accessible tool for versioning data and reproducible pipelines alongside Git projects. In the pipeline workflow, users describe commands, dependencies, parameters, metrics, plots, and outputs in `dvc.yaml`, then use DVC to decide which stages are out of date, run the necessary commands in dependency order, cache produced data, and record the resolved state in `dvc.lock`.

This specification covers the public full-pipeline reproduction behavior: creating stages, selecting stages to reproduce, preserving the relationship between declarative files and workspace files, reporting status, freezing stages, and restoring data from local DVC remotes or run cache when documented command options request that behavior.

## Scope

The covered feature areas are:

- The `dvc` console command and the subcommands `stage add`, `stage list`, `repro`, `status`, `pull`, `freeze`, and `unfreeze`.
- `dvc.yaml` stage definitions and the `dvc.lock` state produced by executed stages.
- Dependency and output files in the workspace, including regular outputs, no-cache outputs, persistent outputs, metrics, and plots as they affect reproduction.
- Local cache behavior that is visible through workspace files, skipped command execution, `dvc status`, and `dvc pull`.
- Run cache behavior that is visible through `dvc repro`, `--no-run-cache`, `--pull`, and `--run-cache`.
- Local filesystem and Git-backed project workflows when they use documented CLI options and do not require a cloud service.

## Installable Surface

Installing DVC provides a `dvc` console command. The command-line interface is the primary surface for this slice.

The top-level `dvc` package exposes version/build metadata:

```python
import dvc

dvc.__version__
dvc.version_tuple
dvc.PKG
```

The public Python API module exports:

```python
from dvc.api import (
    DVCFileSystem,
    all_branches,
    all_commits,
    all_tags,
    artifacts_show,
    exp_save,
    exp_show,
    get_dataset,
    get_url,
    metrics_show,
    open,
    params_show,
    read,
)
```

Those API functions are installable public names, but this document only specifies their interaction with pipeline files where relevant. The reproduction workflow can also be driven through a repository object:

```python
from dvc.repo import Repo
```

## Public API

The CLI commands in scope have these public forms:

```text
dvc stage add -n <name> [options] command...
dvc stage list [targets...] [--all] [--fail] [-R|--recursive] [--name-only]
dvc repro [options] [targets...]
dvc status [options] [targets...]
dvc pull [options] [targets...]
dvc freeze targets...
dvc unfreeze targets...
```

`dvc stage add` creates or updates a stage entry in the `dvc.yaml` file in the current working directory. `-n` or `--name` is required. The remaining arguments after DVC options become the stage command; command flags that appear after the command begins belong to the command, not to `dvc stage add`.

Important `stage add` options are:

- `-f`, `--force`: overwrite an existing stage with the same name.
- `-d`, `--deps <path>`: declare a dependency file or directory. This does not pass the dependency to the command; the command must read any files it needs.
- `-p`, `--params [<filename>:]<params_list>`: declare parameter keys as additional dependencies.
- `-o`, `--outs <path>`: declare a cached output.
- `-O`, `--outs-no-cache <path>`: declare an output that DVC tracks in metadata but does not store in the DVC cache.
- `--outs-persist <path>`: declare a cached output that is not removed before the stage command runs.
- `--outs-persist-no-cache <path>`: declare a persistent output that is not cached.
- `-m`, `--metrics <path>` and `-M`, `--metrics-no-cache <path>`: declare output metrics files.
- `--plots <path>` and `--plots-no-cache <path>`: declare output plot files.
- `-w`, `--wdir <path>`: run the command from a directory inside the project.
- `--always-changed`: consider the stage changed on every reproduction.
- `--desc <text>`: store a user description that does not affect DVC operations.
- `--run`: execute the new or updated stage immediately after creating it.

`dvc repro` reproduces complete or partial pipelines:

```text
dvc repro [-f] [-i] [-s] [-p] [-P] [-R] [--downstream]
          [--force-downstream] [--pull] [--allow-missing]
          [--dry] [--glob] [--no-commit] [--no-run-cache]
          [-k|--keep-going] [--ignore-errors] [targets...]
```

Targets may be stage names from the current `dvc.yaml`, generated stage names, paths to `dvc.yaml` or `.dvc` files, `path/to/dvc.yaml:stage` references, tracked output paths, or directories when recursive mode is used. With `--glob`, wildcard matching applies to stage names within the selected stage file, not to arbitrary path segments.

The repository object exposes the same workflow programmatically:

```python
Repo.init(root_dir=".", no_scm=False, force=False, subdir=False)
Repo(root_dir=None, rev=None, subrepos=False, uninitialized=False, remote=None, remote_config=None)
Repo.reproduce(targets=None, recursive=False, pipeline=False, all_pipelines=False,
               downstream=False, single_item=False, glob=False,
               on_error="fail", **repro_options)
Repo.run(no_exec=False, no_commit=False, run_cache=True, force=True, **stage_options)
Repo.status(targets=None, jobs=None, cloud=False, remote=None,
            all_branches=False, with_deps=False, all_tags=False,
            all_commits=False, recursive=False, check_updates=True)
Repo.pull(targets=None, jobs=None, remote=None, all_branches=False,
          with_deps=False, all_tags=False, force=False, recursive=False,
          all_commits=False, run_cache=False, glob=False, allow_missing=False)
Repo.freeze(target)
Repo.unfreeze(target)
```

`Repo.reproduce()` returns the stages that actually reproduced. If no stages needed to run, the CLI reports that data and pipelines are up to date. `Repo.status()` returns a mapping describing local or cache-vs-remote status. `Repo.pull()` fetches needed objects and checks them out into the workspace, returning operation counts and checkout changes.

## Pipeline Files

`dvc.yaml` uses YAML and is intended to be small enough to version with Git. Its `stages` mapping is the main pipeline definition surface. Each stage name maps to a stage definition with these public fields:

```yaml
stages:
  <stage-name>:
    cmd: <string or list of commands>
    wdir: <path>
    deps:
      - <path>
    params:
      - <param-key>
      - <file>: [<param-key>, ...]
    outs:
      - <path>
      - <path>:
          cache: false
          persist: true
          remote: <remote-name>
          push: false
    metrics:
      - <path>
    plots:
      - <path>
    frozen: true
    always_changed: true
    desc: <text>
    meta: <user-data>
```

`cmd` is required for a runnable pipeline stage. `deps`, `params`, `outs`, `metrics`, and `plots` determine whether a stage is up to date and how it contributes to the dependency graph. `wdir` changes where the command runs and how relative dependency and output paths are interpreted. `desc` and `meta` are user-facing metadata and do not make a stage changed.

`dvc.lock` is generated or updated when stages run. It records the resolved command, dependency metadata, parameter values, and output metadata for each executed stage. It has schema version `2.0` and a `stages` mapping keyed by stage name:

```yaml
schema: "2.0"
stages:
  <stage-name>:
    cmd: <command>
    deps:
      - path: <path>
        md5: <hash>
    params:
      <file>:
        <param-key>: <value>
    outs:
      - path: <path>
        md5: <hash>
```

Directory outputs may be represented by a directory hash and, when DVC writes expanded file metadata, a list of child file entries. Callers should treat `dvc.lock` as the public record of the workspace state that DVC will compare on future reproductions.

`.dvc` files are supported as data placeholders for standalone tracked files or directories. For this pipeline slice, they matter as targets accepted by `repro`, `status`, and `pull`, and as files whose `outs`, `deps`, `wdir`, and output metadata describe tracked data outside a multi-stage `dvc.yaml` pipeline.

## Stage Creation

`dvc stage add` writes the stage definition without running the command unless `--run` is used. With `--run`, DVC executes the command, saves or links/cache-checks declared outputs as appropriate, and updates `dvc.lock`.

Stage names are required and must be valid DVC stage names. Adding a stage checks public graph constraints before writing the project file: the same output path cannot be claimed by more than one stage, overlapping output paths are rejected, and dependency/output relationships cannot form cycles.

Output classifications affect later reproduction:

- Cached outputs are stored in the DVC cache when the stage is executed.
- No-cache outputs remain ordinary workspace files tracked by DVC metadata but are not stored in the DVC cache.
- Persistent outputs remain in place before the command runs; non-persistent outputs are removed from the workspace before command execution.
- Metrics and plots are outputs with additional meaning for DVC reporting, and they still participate in reproduction state.

## Reproduction Behavior

Running `dvc repro` with no targets uses `dvc.yaml` in the current working directory as the default target. DVC reads pipeline definitions in the project, determines the dependency graph from stage outputs and downstream dependencies, and runs only the stages that need reproduction.

A stage needs reproduction when its command, dependencies, parameter values, output state, or stage configuration differs from the recorded state, when declared data is missing in a way that requires the stage, when the stage is marked `always_changed`, or when the user forces execution. Stages with no dependencies and no outputs are considered always changed.

When a stage runs, DVC executes its command from the stage working directory. If `cmd` is a list, commands run one after another in the listed order; a failing command stops the remaining commands for that stage. During command execution, DVC provides `DVC_ROOT` as the project root and `DVC_STAGE` as the stage address in the environment.

Before running a non-persistent output stage, DVC removes declared outputs from the workspace so the command recreates them. Commands are responsible for creating any needed directories. After successful execution, DVC updates the cache unless `--no-commit` was used, and updates `dvc.lock` with the new dependency and output state.

Target selection options change the reproduction set:

- `--single-item` reproduces the selected target stages without recursive dependency checking.
- `--pipeline` reproduces the complete pipeline containing the selected targets.
- `--all-pipelines` reproduces all pipelines in all project `dvc.yaml` files and ignores explicit targets.
- `--recursive` searches directories for pipeline files.
- `--downstream` starts from the specified targets and reproduces their descendants.
- `--force` runs selected stages even when DVC sees no changes.
- `--force-downstream` forces descendants of a changed or forced stage to reproduce even if their direct dependencies appear unchanged.
- `--dry` prints the commands that would run and does not execute them or update workspace outputs.

`--pull` lets reproduction download missing data as needed before deciding whether stages can run or be restored. `--allow-missing` skips stages whose only issue is missing data. Without `--pull`, DVC does not automatically download missing data during `repro`.

## Status, Freeze, And Pull

`dvc status` reports changed stages and tracked data state. With no changes it reports that data and pipelines are up to date. With `--quiet`, it suppresses output and exits with success only when there are no reported changes. With `--json`, it emits the status mapping as JSON.

Local status does not accept branch/tag/commit expansion or job-count options; those options only make sense for cache-vs-remote status. `--with-deps` includes dependency stages for the selected targets. `--recursive` reports stages inside selected directories. `--no-updates` disables update checks for imported data.

`dvc freeze targets...` marks stages or `.dvc` files frozen. `dvc unfreeze targets...` removes that mark. A frozen non-import stage remains a pipeline node, but its dependencies are not reproduced through that stage, and status/reproduction warn that dependency changes are not being followed for it. The frozen state is written to the project file rather than to the lockfile.

`dvc pull` downloads tracked files or directories from DVC remote storage into the local cache and checks them out into the workspace. For local filesystem remotes, this behavior is fully local and service-free. Pulling data does not update Git-tracked code, `dvc.yaml`, or `.dvc` files; those remain Git concerns.

Remote selection for `pull` is resolved in this order:

1. A `remote` field on the relevant output entry.
2. The `--remote` or `-r` CLI option.
3. The configured default remote.

Without targets, `pull` considers all files and directories referenced by the current workspace metadata. Targets limit the pull to tracked files or directories, paths inside tracked directories, `.dvc` files, and stage names. `--all-branches`, `--all-tags`, and `--all-commits` expand the Git revisions whose DVC metadata is considered. `--run-cache` fetches run history as well as data objects. `--allow-missing` ignores errors for files or directories that remain unavailable.

## Cache And Run Cache

DVC stores data and model files outside Git in a cache while keeping lightweight metadata in the repository. Reproduction and pull make data visible in the workspace by linking or copying from cache according to the configured cache type.

The run cache records successful stage runs by their command, dependencies, outputs, and related stage state. It is enabled by default for reproducible stages and lets DVC skip command execution when a previous matching run can restore the outputs. `--no-run-cache` disables this shortcut for `dvc repro` and forces command execution whenever the stage otherwise needs reproduction.

Run cache is not used for every possible stage. It is not available for stages that lack a command, dependencies, or outputs, for stages marked always changed, and for output configurations that make cached restoration unsupported. If a stage can be restored from run cache, DVC reports that the stage is cached, skips the command, and checks out the recorded outputs.

When `dvc repro --pull` is used with run cache enabled, DVC attempts to pull run cache metadata before reproduction and may pull data objects needed by a cached run. When `dvc pull --run-cache` is used, DVC fetches run history in addition to ordinary tracked data objects.

## Error Semantics

CLI commands return `0` on success and nonzero when a DVC operation fails. Most user-visible failures are reported as `DvcException` or subclasses.

Important public error conditions are:

- A command executed by a stage fails: reproduction fails for that stage; by default `dvc repro` stops and reports a reproduction failure.
- `--keep-going` is used: DVC continues with stages that do not depend on the failed stage and skips dependents of the failed stage.
- `--ignore-errors` is used: DVC logs stage errors and continues without using the dependency-skip behavior of `--keep-going`.
- A target is neither a stage, a valid DVC file, nor a tracked output: DVC reports that no output or stage exists for that target.
- A stage name is invalid: DVC rejects the stage definition before writing it.
- A stage file path is missing, invalid, not a file, or Git-ignored: DVC reports a DVC file error instead of silently creating unrelated state.
- Two stages claim the same output or overlapping outputs: DVC rejects the new or changed stage.
- A dependency/output relationship creates a cycle: DVC rejects the graph.
- Local status is requested with branch/tag/commit/job options that only apply to remote status: DVC reports invalid arguments.
- Pull or checkout cannot materialize requested files from cache or remote storage: DVC reports checkout or transfer failure and preserves the successful operation counts it can report.

## Cross-View Invariants

- A stage recorded by `dvc stage add` is visible in `dvc.yaml`, appears in `dvc stage list`, and can be selected by name in `dvc repro`.
- If a stage output is also another stage dependency, `dvc repro` treats that relationship as a pipeline edge and runs the upstream stage before the downstream stage when both need reproduction.
- Successful reproduction updates workspace outputs and `dvc.lock` together, unless the command is a dry run or an error stops the stage before state can be committed.
- If no dependency, parameter, command, or output state changed, `dvc status` reports no local pipeline changes and `dvc repro` skips the stage.
- If a dependency file changes, the stage that depends on it is reported as changed and is eligible to run; downstream stages are considered according to the selected reproduction mode.
- A no-cache output can affect status and reproduction state even though DVC does not store that output in the object cache.
- A persistent output is not removed before its stage command runs; a non-persistent output is removed before command execution.
- A frozen stage's dependency changes do not cause reproduction to pass through that stage until it is unfrozen.
- `dvc pull` can restore tracked data to the workspace from cache/remote metadata, but it does not modify Git-tracked source files or pipeline definition files.
- `--dry` and `--no-commit` are distinct: dry reproduction does not execute commands, while no-commit reproduction executes commands but avoids storing produced outputs in the cache.
- Run-cache restoration changes the workspace outputs without running the stage command, and disabling run cache prevents that command skip.
- JSON status and text status describe the same underlying project state, only with different output formatting.

## Representative Workflows

Create a two-stage pipeline:

```text
dvc stage add -n prepare -d raw.txt -o prepared.txt "python prepare.py raw.txt prepared.txt"
dvc stage add -n train -d prepared.txt -d train.py -o model.bin -M metrics.json "python train.py prepared.txt model.bin metrics.json"
```

After these commands, `dvc.yaml` contains both stages. The `train` stage depends on `prepared.txt`, so DVC treats `prepare` as upstream of `train`.

Run the pipeline:

```text
dvc repro
```

DVC executes `prepare` before `train`, creates or updates workspace outputs, stores cacheable outputs in the DVC cache, and writes `dvc.lock`. A later `dvc repro` with no relevant changes skips both stages. If `train.py` changes, the `train` stage becomes changed while `prepare` can remain up to date.

Use targeted reproduction:

```text
dvc repro train
dvc repro --downstream prepare
dvc repro --force train
dvc repro --dry train
```

The first command reproduces what is needed for `train`. The downstream form starts at `prepare` and continues through descendants. The force form runs `train` even when unchanged. The dry form reports commands without running them.

Freeze a stage and restore data:

```text
dvc freeze prepare
dvc status
dvc repro train
dvc unfreeze prepare
dvc pull -r localstore train
```

While frozen, changes behind `prepare` do not flow through it. After unfreezing, normal dependency tracking resumes. Pull fetches tracked data for `train` from the selected local remote into the cache and materializes it in the workspace.

## Non-Goals

This specification does not cover:

- Internal stage, output, file-loader, graph, cache-manager, lock, or filesystem object layouts.
- Private reset methods, private cache toggles, private attributes, or monkeypatch-only behavior.
- Cloud-service remote authentication or service-specific backends such as S3, Azure, Google Cloud, Google Drive, OSS, SSH servers, HDFS, WebDAV, or Studio.
- Experiment management commands, queues, plots rendering, metrics comparison, artifacts registry behavior, datasets, imports, garbage collection, and unrelated Python API features.
- Exact stdout wording beyond stable success/failure meaning, status categories, and documented user-facing messages.
- Shell-specific behavior outside the documented effect that stage commands run in the stage working directory with DVC environment variables.
- Compatibility with old DVC metadata formats except where current public commands explicitly document migration-related behavior.

## Implementation Guidance

The expected implementation focuses on public behavior that a DVC user can observe through commands, repository methods, YAML files, lockfiles, workspace files, cache effects, exit codes, and exceptions.

Tests may exercise stage creation, target resolution, pipeline ordering, incremental reproduction, forced and dry reproduction, missing data handling, run-cache skips, status output modes, freeze/unfreeze state, local pull/fetch/checkout behavior, and consistency between CLI calls and repository methods.

Scoring should reward implementations that preserve the documented cross-view invariants across command output, serialized project state, workspace files, and programmatic return values. Tests should not require private object identities, undocumented attributes, private module paths, cloud services, or implementation-specific helper functions.

