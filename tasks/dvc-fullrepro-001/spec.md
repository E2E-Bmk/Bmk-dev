# DVC Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`dvc` is a data-versioning and pipeline tool with a `dvc` CLI entry point. It versions data and reproducible pipelines alongside Git projects. In the pipeline workflow, users describe commands, dependencies, parameters, metrics, plots, and outputs in `dvc.yaml`, then use the tool to decide which stages are out of date, run the necessary commands in dependency order, cache produced data, and record the resolved state in `dvc.lock`.

This specification covers the public full-pipeline reproduction behavior: creating stages, selecting stages to reproduce, preserving the relationship between declarative files and workspace files, reporting status, freezing stages, and restoring data from local DVC remotes or run cache when documented command options request that behavior.

## Non-Goals

- This specification does not require Internal stage, output, file-loader, graph, cache-manager, lock, or filesystem object layouts.
- This specification does not require Private reset methods, private cache toggles, private attributes, or monkeypatch-only behavior.
- This specification does not require Cloud-service remote authentication or service-specific backends such as object stores, SSH servers, HDFS, WebDAV, or hosted studio integrations.
- This specification does not require Experiment management commands, queues, plots rendering, metrics comparison, artifacts registry behavior, datasets, imports, garbage collection, or unrelated Python API features.
- This specification does not require Exact stdout wording beyond stable success/failure meaning, status categories, or documented user-facing messages.
- This specification does not require Shell-specific behavior outside the documented effect that stage commands run in the stage working directory with environment variables.
- This specification does not require Compatibility with old metadata formats except where current public commands explicitly document migration-related behavior.

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

DVC executes `prepare` before `train`, creates or updates workspace outputs, stores cacheable outputs in the DVC cache, and writes `dvc.lock`. A later `dvc repro` with no relevant changes skips both stages. If `train.py` changes while the `prepare` inputs remain unchanged, the `train` stage becomes changed and `prepare` remains up to date.

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

## Pipeline Files

Pipeline files declare stages, their commands, dependencies, outputs, and metadata in a structured YAML format that sits alongside Git-tracked code.

**Stage definitions.** `dvc.yaml` uses YAML and is intended to be small enough to version with Git. Its `stages` mapping is the main pipeline definition surface. Each stage name maps to a stage definition with these public fields:

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

**Lock file.** `dvc.lock` is generated or updated when stages run. It records the resolved command, dependency metadata, parameter values, and output metadata for each executed stage. It has schema version `2.0` and a `stages` mapping keyed by stage name:

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

Directory outputs are represented by a directory hash and include child file entries when DVC writes expanded file metadata. Callers must treat `dvc.lock` as the public record of the workspace state that DVC compares on future reproductions.

**Data placeholders.** `.dvc` files are supported as data placeholders for standalone tracked files or directories. For this pipeline slice, they matter as targets accepted by `repro`, `status`, and `pull`, and as files whose `outs`, `deps`, `wdir`, and output metadata describe tracked data outside a multi-stage `dvc.yaml` pipeline.

## Stage Creation

Stage creation defines pipeline stages in `dvc.yaml` and validates graph constraints before persisting the definition.

**Adding stages.** `dvc stage add` writes the stage definition without running the command unless `--run` is used. With `--run`, DVC executes the command, saves or links/cache-checks declared outputs as appropriate, and updates `dvc.lock`. `dvc stage list` reports declared stages; with `--name-only`, it prints only stage names. Adding a stage with the same name as an existing stage must fail unless `--force` is used, in which case the existing stage definition is replaced.

**Graph validation.** Stage names are required and must be valid DVC stage names. Adding a stage checks public graph constraints before writing the project file: the same output path cannot be claimed by more than one stage, overlapping output paths are rejected, and dependency/output relationships cannot form cycles. An invalid stage name must be rejected before writing to the project file, preserving the existing pipeline definition.

**Output classifications.** Output classifications affect later reproduction:

- Cached outputs are stored in the DVC cache when the stage is executed.
- No-cache outputs remain ordinary workspace files tracked by DVC metadata but are not stored in the DVC cache.
- Persistent outputs remain in place before the command runs; non-persistent outputs are removed from the workspace before command execution.
- Metrics and plots are outputs with additional meaning for DVC reporting, and they still participate in reproduction state.

## Reproduction Behavior

Reproduction executes pipeline stages that are out of date according to their declared dependencies, parameters, outputs, and state.

**Default behavior.** Running `dvc repro` with no targets uses `dvc.yaml` in the current working directory as the default target. DVC reads pipeline definitions in the project, determines the dependency graph from stage outputs and downstream dependencies, and runs only the stages that need reproduction.

**Change detection.** A stage needs reproduction when its command, dependencies, parameter values, output state, or stage configuration differs from the recorded state, when declared data is missing in a way that requires the stage, when the stage is marked `always_changed`, or when the user forces execution. Stages with no dependencies and no outputs are considered always changed.

**Command execution.** When a stage runs, DVC executes its command from the stage working directory. If `cmd` is a list, commands run one after another in the listed order; a failing command stops the remaining commands for that stage. During command execution, DVC provides `DVC_ROOT` as the project root and `DVC_STAGE` as the stage address in the environment.

**Output handling.** Before running a non-persistent output stage, DVC removes declared outputs from the workspace so the command recreates them. Commands are responsible for creating any needed directories. After successful execution, DVC updates the cache unless `--no-commit` was used, and updates `dvc.lock` with the new dependency and output state.

**Target selection.** Target selection options change the reproduction set:

- `--single-item` reproduces the selected target stages without recursive dependency checking.
- `--pipeline` reproduces the complete pipeline containing the selected targets.
- `--all-pipelines` reproduces all pipelines in all project `dvc.yaml` files and ignores explicit targets.
- `--recursive` searches directories for pipeline files.
- `--downstream` starts from the specified targets and reproduces their descendants.
- `--force` runs selected stages even when DVC sees no changes.
- `--force-downstream` forces descendants of a changed or forced stage to reproduce even if their direct dependencies appear unchanged.
- `--dry` prints the commands that would run and does not execute them or update workspace outputs.

`--pull` lets reproduction download missing data as needed before deciding whether stages are runnable or restorable. `--allow-missing` skips stages whose only issue is missing data. Without `--pull`, DVC does not automatically download missing data during `repro`.

## Status, Freeze, And Pull

These commands inspect pipeline state, control reproduction flow, and restore tracked data from storage.

**Status reporting.** `dvc status` reports changed stages and tracked data state. With no changes it reports that data and pipelines are up to date. With `--quiet`, it suppresses output and exits with success only when there are no reported changes. With `--json`, it emits the status mapping as JSON. The JSON status for a changed stage must include the stage name as a key with change details; for a clean pipeline it must return an empty mapping.

For cacheable outputs, status compares the workspace and lockfile state with the availability of the corresponding local cache objects. When a no-commit run updates the workspace output and lockfile checksum without storing the cache object, local status must report the stage as changed. JSON status must include the changed stage, text status must describe the same state, and quiet status must return nonzero.

Local status does not accept branch/tag/commit expansion or job-count options; those options only make sense for cache-vs-remote status. `--with-deps` includes dependency stages for the selected targets. `--recursive` reports stages inside selected directories. `--no-updates` disables update checks for imported data.

**Freezing.** `dvc freeze targets...` marks stages or `.dvc` files frozen by writing `frozen: true` to the stage definition in `dvc.yaml`. `dvc unfreeze targets...` removes that `frozen` flag. A frozen non-import stage remains a pipeline node, but its dependencies are not reproduced through that stage, and status/reproduction warn that dependency changes are not being followed for it. Freezing one stage must not affect other stages in the same pipeline.

**Pull.** `dvc pull` downloads tracked files or directories from DVC remote storage into the local cache and checks them out into the workspace. For local filesystem remotes, this behavior is fully local and service-free. Pulling data does not update Git-tracked code, `dvc.yaml`, or `.dvc` files; those remain Git concerns.

Pull identifies remote storage through an output-specific `remote` field, the `--remote` or `-r` CLI option, or the configured default remote. If the selected storage does not contain a required object and `--allow-missing` is absent, the command must report a transfer or checkout failure.

Without targets, `pull` considers all files and directories referenced by the current workspace metadata. Targets limit the pull to tracked files or directories, paths inside tracked directories, `.dvc` files, and stage names. `--all-branches`, `--all-tags`, and `--all-commits` expand the Git revisions whose DVC metadata is considered. `--run-cache` fetches run history as well as data objects. `--allow-missing` ignores errors for files or directories that remain unavailable.

## Cache And Run Cache

The cache system stores output data outside Git and enables skipping previously completed stage runs through run-cache matching.

**Data cache.** DVC stores data and model files outside Git in a cache while keeping lightweight metadata in the repository. Reproduction and pull make data visible in the workspace by linking or copying from cache according to the configured cache type.

**No-commit behavior.** A clean local cacheable output requires the workspace file, its lockfile checksum, and its corresponding local cache object to agree. A no-commit reproduction executes the command and records the resulting workspace and lockfile state without storing that object. The stage remains eligible for reproduction while the object is unavailable. When run-cache restoration is disabled, repeating `repro --no-commit --no-run-cache` must execute the command again even when the workspace output checksum matches `dvc.lock`.

**Run cache.** The run cache records successful stage runs by their command, dependencies, outputs, and related stage state. It is enabled by default for reproducible stages. When a previous matching run contains restorable outputs, DVC restores those outputs and skips command execution. `--no-run-cache` disables this shortcut for `dvc repro` and forces command execution whenever the stage otherwise needs reproduction.

Run cache is not used for every possible stage. It is not available for stages that lack a command, dependencies, or outputs, for stages marked always changed, and for output configurations that make cached restoration unsupported. If a matching run-cache entry contains the required output objects, DVC reports that the stage is cached, skips the command, and checks out the recorded outputs.

When `dvc repro --pull` is used with run cache enabled, DVC attempts to pull run cache metadata before reproduction and must pull available data objects when a selected cached run needs them. When `dvc pull --run-cache` is used, DVC fetches run history in addition to ordinary tracked data objects.

## State Model

The product state model has three public projections. The declarative projection is the stage and data metadata stored in `dvc.yaml` and `.dvc` files. The resolved projection is the command, dependency, parameter, and output state recorded in `dvc.lock` together with cache objects that DVC has committed. The materialized projection is the files and directories visible in the workspace.

These projections obey the same lifecycle. A successfully executed stage must leave its materialized outputs consistent with the resolved lockfile state. A dependency or parameter change in the declarative or materialized projection must make the affected stage report changed against the resolved projection. A pull or run-cache restoration must materialize the resolved output state without rewriting the declarative stage definition. A dry run must leave all three projections unchanged. A no-commit run must update the materialized and lockfile projections while leaving the corresponding output object absent from the local cache, which keeps the stage changed until that cache state is reconciled.

## Error Semantics

CLI commands return `0` on success and nonzero when argument validation or a DVC operation fails. Public repository operation failures raise `DvcException` or an applicable public subclass; CLI argument validation reports an argument error without entering the repository operation.

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
- Pull or checkout fails to materialize requested files from cache or remote storage: DVC reports checkout or transfer failure and preserves operation counts for transfers and checkouts that completed successfully.

## Cross-View Invariants

- A stage recorded by `dvc stage add` must be visible in `dvc.yaml`, must appear in `dvc stage list`, and must be selectable by name in `dvc repro`.
- If a stage output is also another stage dependency, `dvc repro` must treat that relationship as a pipeline edge and must run the upstream stage before the downstream stage when both need reproduction.
- Successful reproduction must update workspace outputs and `dvc.lock` together, unless the command is a dry run or an error stops the stage before DVC commits state.
- If no dependency, parameter, command, or output state changed, `dvc status` must report no local pipeline changes and `dvc repro` must skip the stage.
- If a dependency file changes, the stage that depends on it must be reported as changed and must be eligible to run; downstream stages must be considered according to the selected reproduction mode.
- A changed or missing no-cache output must affect status and reproduction state even though DVC does not store that output in the object cache.
- A persistent output must remain in the workspace before its stage command runs; a non-persistent output must be removed before command execution.
- A frozen stage's dependency changes must not cause reproduction to pass through that stage until it is unfrozen.
- `dvc pull` must restore requested tracked data to the workspace when the corresponding cache or remote objects are available, and it must not modify Git-tracked source files or pipeline definition files.
- `--dry` and `--no-commit` must remain distinct: dry reproduction must not execute commands, while no-commit reproduction must execute commands but must not store produced outputs in the cache.
- Run-cache restoration must change the workspace outputs without running the stage command, and disabling run cache must prevent that command skip.
- JSON status and text status must describe the same underlying project state, differing only in output formatting.

## Public Interface

### Import Surface

Installing DVC provides the `dvc` console command, which is the primary command-line surface for this slice.

```python
import dvc
from dvc.api import (
    DVCFileSystem, all_branches, all_commits, all_tags, artifacts_show,
    exp_save, exp_show, get_dataset, get_url, metrics_show, open,
    params_show, read,
)
from dvc.repo import Repo
```

Importing the top-level package as `dvc` provides the public version/build metadata names `dvc.__version__`, `dvc.version_tuple`, and `dvc.PKG`. The `dvc.api` names remain installable public API, while their data, experiment, artifact, and metric behaviors are outside the pipeline slice unless a behavior is specified below. Repository methods and the installed console command must observe the same project files, workspace state, cache state, and reproduction decisions.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Repo.init` | class method | Initialize a repository in a project directory |
| `Repo` | class | Open a repository and expose pipeline operations |
| `Repo.reproduce` | method | Reproduce selected stages or pipelines |
| `Repo.run` | method | Create or update and optionally execute a stage |
| `Repo.status` | method | Report local or cache-vs-remote status |
| `Repo.pull` | method | Fetch tracked data and check it out into the workspace |
| `Repo.freeze` | method | Mark a stage or `.dvc` file frozen |
| `Repo.unfreeze` | method | Remove the frozen mark from a stage or `.dvc` file |
| `dvc.__version__` | attribute | Installed package version string |
| `dvc.version_tuple` | attribute | Installed package version tuple |
| `dvc.PKG` | attribute | Package distribution identifier |

The CLI commands in scope are `dvc stage add`, `dvc stage list`, `dvc repro`, `dvc status`, `dvc pull`, `dvc freeze`, and `dvc unfreeze`.

`dvc stage add` creates or updates a stage entry in the `dvc.yaml` file in the current working directory. `-n` or `--name` is required. The remaining arguments after DVC options become the stage command; command flags that appear after the command begins belong to the command, not to `dvc stage add`.

Important `stage add` options include `--force`, `--deps`, `--params`, cached and no-cache output declarations, persistent output declarations, metrics and plots declarations, `--wdir`, `--always-changed`, `--desc`, and `--run`.

`dvc repro` reproduces complete or partial pipelines. Valid targets are stage names from the current `dvc.yaml`, generated stage names, paths to `dvc.yaml` or `.dvc` files, `path/to/dvc.yaml:stage` references, tracked output paths, or directories when recursive mode is used. With `--glob`, wildcard matching applies to stage names within the selected stage file.

The repository object exposes the same workflow programmatically. `Repo` accepts the project path and an `uninitialized` flag; when `uninitialized` is true, it opens the directory without requiring an initialized DVC repository. `Repo.init` accepts `root_dir` for the target directory and `no_scm` to initialize without requiring a Git repository. `Repo.run` accepts stage definition arguments including `name`, `cmd`, `deps`, `params`, `outs`, `metrics`, `plots`, `desc`, `wdir`, `always_changed`, `force`, and `no_exec`; when `no_exec` is true, it writes the stage definition to `dvc.yaml` without executing the command or creating output files, and returns a stage object whose `name` and `cmd` attributes reflect the written definition. `Repo.reproduce()` returns the stages that actually reproduced. If no stages needed to run, the CLI reports that data and pipelines are up to date. `Repo.status()` returns a mapping describing local or cache-vs-remote status. `Repo.pull()` fetches needed objects and checks them out into the workspace, returning operation counts and checkout changes.

### CLI Entry Points

The supported command-line entry point is the installed `dvc` console command. `python -m dvc` is not part of this specification. Successful commands return exit code `0`; rejected arguments, invalid targets, graph conflicts, command failures, and unavailable requested data return a nonzero exit code.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

The implementation must preserve the documented cross-view invariants across command output, serialized project state, workspace files, cache effects, exit codes, exceptions, and programmatic return values. Private object identities, undocumented attributes, private module paths, cloud services, and implementation-specific helper functions are outside this contract.
