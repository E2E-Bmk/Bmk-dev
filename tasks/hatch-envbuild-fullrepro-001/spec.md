# Hatch Specification

## Product Overview

Hatch is a command line tool for working with Python projects from the project root. In this scope, Hatch reads project metadata from `pyproject.toml`, reads Hatch-specific project configuration from either `tool.hatch` in `pyproject.toml` or from top-level keys in `hatch.toml`, manages named local environments, runs commands and scripts inside those environments, builds local artifacts, and displays or updates the project version.

Hatch treats a project as one state model with several public projections: the configuration files on disk, the project metadata view, the environment view, the build artifact view, and the version view. Commands must keep those projections consistent for the duration of a single invocation and across later invocations that read the same files.

## Scope

This specification covers local workflows for:

- `hatch` root invocation and project selection.
- `hatch config` commands that locate, show, restore, and set local configuration values.
- Project discovery and project metadata display.
- Environment configuration, inheritance, matrices, selection, creation, lookup, display, removal, pruning, command execution, inline Python script execution, and lockfile commands.
- Local build and clean commands for `sdist` and `wheel` targets and configured build output directories.
- Version display and version updates for static versions and Hatch-managed dynamic versions.

## Installable Surface

The installed console script is `hatch`, defined as `hatch.cli:main`.

Module execution is supported: `python -m hatch` must invoke the same CLI entry point as the `hatch` console script.

The scoped Python import surface is intentionally small:

```python
from hatch.cli import hatch, main
```

`hatch.cli.hatch` is the root command object. `hatch.cli.main()` runs it with program name `hatch` and exits with status code `1` after printing an exception report for uncaught exceptions. The top-level `hatch` package does not export user-facing functions or classes for these workflows.

## Public API

The public interface for this scope is the CLI:

```text
hatch [ROOT_OPTIONS] COMMAND [ARGS...]
python -m hatch [ROOT_OPTIONS] COMMAND [ARGS...]
```

Root options:

- `-e, --env ENV_NAME` selects the active environment and defaults to `default`.
- `-p, --project PROJECT_NAME` selects a configured project by name.
- `-v, --verbose` increases verbosity and is additive.
- `-q, --quiet` decreases verbosity and is additive.
- `--color` and `--no-color` force color behavior.
- `--interactive` and `--no-interactive` force prompt/progress behavior.
- `--data-dir PATH`, `--cache-dir PATH`, and `--config PATH` override the data directory, cache directory, and user config file.
- `--version` prints Hatch's version.
- `-h, --help` prints help.

Environment variables mirror the documented root options: `HATCH_ENV`, `HATCH_PROJECT`, `HATCH_VERBOSE`, `HATCH_QUIET`, `HATCH_INTERACTIVE`, `HATCH_DATA_DIR`, `HATCH_CACHE_DIR`, `HATCH_CONFIG`, `FORCE_COLOR`, and `NO_COLOR`. If `--config` or `HATCH_CONFIG` names a file that does not exist, the invocation must fail before running the requested command. If no config file exists at the default path, Hatch must create a default config file before running subcommands.

The command groups and commands in scope are:

```text
hatch config find
hatch config show [--all]
hatch config restore
hatch config set KEY [VALUE]
hatch status
hatch project metadata [FIELD]
hatch env create [ENV_NAME]
hatch env find [ENV_NAME]
hatch env show [ENVS...] [--ascii] [--json] [--internal]
hatch env remove [ENV_NAME]
hatch env prune
hatch env run [OPTIONS] ARGS...
hatch run [ENV:]ARGS...
hatch shell [ENV_NAME] [--name NAME] [--path PATH]
hatch env lock [ENV_NAME] [--upgrade] [--upgrade-package NAME] [--export PATH] [--export-all DIR] [--check]
hatch dep lock [--upgrade] [--upgrade-package NAME] [--export PATH] [--export-all DIR] [--check]
hatch lock [--upgrade] [--upgrade-package NAME] [--export PATH] [--export-all DIR] [--check]
hatch build [LOCATION] [-t TARGET] [--hooks-only] [--no-hooks] [--ext] [--clean] [--clean-hooks-after]
hatch clean [LOCATION] [-t TARGET] [--hooks-only] [--no-hooks] [--ext]
hatch version [DESIRED_VERSION] [--force]
```

## Product State Model

Hatch's local state has these public projections:

- Project files: `pyproject.toml`, optional `hatch.toml`, optional lockfiles, source files, and generated distributions.
- User configuration: `config.toml`, selected via the default platform path or the `--config`/`HATCH_CONFIG` override.
- Environment state: named local environments stored according to configured directories, plus dependency state metadata and optional lockfiles.
- Metadata state: normalized project metadata exposed by `hatch project metadata`.
- Version state: either `project.version` or the configured dynamic version source.
- Build state: artifacts in the requested build location, defaulting to `dist`.

Cross-view invariants:

- A project discovered by `hatch status` must be the same project used by `hatch project metadata`, `hatch env ...`, `hatch build`, and `hatch version` when those commands run with the same root options and current directory.
- A root `--project PROJECT_NAME` selection must use the configured project location for all scoped commands and must fail when the named project cannot be resolved.
- A root `--env ENV_NAME` selection must be the default target for `hatch run`, `hatch shell`, `hatch dep lock`, `hatch lock`, and `hatch env remove` when those commands do not name a different environment.
- Environment names shown by `hatch env show --json` must be valid inputs to `hatch env create`, `hatch env find`, `hatch env run -e`, and `hatch env remove`.
- Environment matrix names generated from configuration must be the names used by environment execution, lookup, display, removal, and locking.
- A version displayed by `hatch version` must match the version field returned by `hatch project metadata version` for the same project state.
- A version successfully updated by `hatch version DESIRED_VERSION` must be visible to a later `hatch version` invocation and to local build metadata for the same project.
- A build output location selected by command argument or build configuration must be the location that `hatch build` writes to and `hatch clean` removes from for the same target selection.
- A lockfile generated for an environment must be the file checked by `--check` for the same environment unless `--export`, `--export-all`, or `lock-filename` selects a different path.

## Project And Configuration Behavior

Hatch must locate a local project by searching from the current directory upward for `pyproject.toml`. If none is found, it must treat the current location as an environment-management-only project with a project name derived from the directory. If a `setup.py` file is found before `pyproject.toml`, Hatch must treat that directory as the project location for initialization workflows.

Project-specific Hatch configuration is read from `[tool.hatch]` in `pyproject.toml` and from top-level keys in `hatch.toml`. When the same Hatch option is defined in both files, the top-level value from `hatch.toml` must take precedence. If a configuration table has the wrong type, Hatch must fail with an error that identifies the invalid field.

The user config file controls project selection mode, default project aliases, data/cache directories, environment storage directories, shell settings, and terminal styles. In `local` mode, Hatch must use project discovery from the current directory. In `project` mode, Hatch must work on the selected configured project and must fail if that project cannot be found. In `aware` mode, Hatch must use local discovery when a project is present and must fall back to configured project selection when no local project is detected.

`hatch config find` must print the active config file path. `hatch config show` must print the config file contents with sensitive publish settings scrubbed, and `hatch config show --all` must print them without scrubbing. `hatch config restore` must replace the config file with default settings. `hatch config set KEY VALUE` must write a TOML value at the dotted key path, must coerce `true` and `false` to booleans, must parse values beginning with `{` or `[` as Python literal-style tables or arrays, and must fail without saving when the resulting config is invalid.

`hatch status` must report the selected project, project location, and config path. If no project is detected, it must report that state instead of pretending a project exists.

## Project Metadata Behavior

`hatch project metadata` must display the project's core metadata as JSON with empty values omitted. `hatch project metadata FIELD` must display a single field. String fields must be printed as strings; structured fields must be printed as formatted JSON. If `FIELD` is `readme`, Hatch must print the readme text, rendering Markdown when the content type is Markdown. If the field does not exist, the command must fail.

Project metadata must follow the standard `[project]` table. The project name is required for packaged projects. The version must be either statically defined as `project.version` or declared as dynamic with `dynamic = ["version"]` and configured through Hatch's version table. Dependency entries support Hatch context formatting and direct references are rejected unless `tool.hatch.metadata.allow-direct-references = true`.

## Environment Configuration Behavior

Environment definitions live under `[tool.hatch.envs.<ENV_NAME>]` or under `[envs.<ENV_NAME>]` in `hatch.toml`. The default environment is named `default`; if it is not configured, Hatch must synthesize it with type `virtual`.

Every environment has a `type`; the built-in type in scope is `virtual`. The `virtual` type must use local virtual environments and supports `python`, `python-sources`, `path`, `system-packages`, and `installer`. The `path` option, when present, must select the environment location and accepts absolute paths or paths relative to the project root. Environment directory config under `[dirs.env]` must control storage when `path` is absent. A relative environment directory must be interpreted relative to the project root.

Environment inheritance must use the `template` option and defaults to inheriting from `default`. A child environment must inherit unspecified options from its template, must not inherit matrices, and must override inherited scalar options when it defines them. Setting `template` to the environment's own name must disable inheritance. Setting `detached = true` must make the environment self-referential and set `skip-install = true`.

Dependencies must combine project dependencies, selected project features, dependency groups, environment `dependencies`, and `extra-dependencies` according to the environment's install settings. `skip-install = true` must skip project installation. `dev-mode = false` must install the project only during environment creation rather than keeping it editable with the current source tree.

`env-vars` defines environment variables injected into commands. `env-include` and `env-exclude` filter inherited process environment variables; exclusion patterns must take precedence over inclusion patterns and must not remove variables explicitly defined by `env-vars`.

Scripts live under an environment's `scripts` table. Each script value must be a string or an array of strings. A script name at the beginning of another script command must expand to that script's commands with the remaining arguments appended. A command beginning with `- ` must ignore that command's exit code. Circular script references must fail.

`extra-scripts` must add only script names that are not already defined by the environment or its template and must not override existing script names.

## Matrix And Override Behavior

An environment matrix is defined with one or more `[[tool.hatch.envs.<ENV_NAME>.matrix]]` tables. Each matrix table must generate the product of its variable values. Generated names must be prefixed by `<ENV_NAME>.` except for matrices on the `default` environment. Values from `python` or `py` variables must appear first in generated names and must be prefixed with `py` unless the value already starts with `py`; `py` must be treated as the `python` variable for selection. A matrix table that contains both `py` and `python` must fail.

`matrix-name-format` must format non-Python variable parts using `{variable}` and `{value}` and must contain `{value}`. If it is invalid or lacks `{value}`, Hatch must fail.

Option overrides live under `[tool.hatch.envs.<ENV_NAME>.overrides]`. Supported override sources are `platform`, `env`, `matrix`, and `name`. Override values must support scalar replacement, array appending, mapping key insertion, and whole-option replacement with the `set-` prefix. Inline override entries support `if`, `platform`, and `env` conditions; an entry must be skipped when any condition does not match.

Override application order for whole-option replacements and mapping-key replacements must be `platform`, then environment variables, then matrix variables, then generated names. This order is part of the public configuration contract. Invalid override shapes must fail with an error identifying the invalid override field.

## Environment Command Behavior

`hatch env show` must display standalone environments and matrix environments. `hatch env show --json` must output a compact JSON object keyed by environment name and must include resolved environment variables, dependencies, pre-install commands, post-install commands, and scripts when those values are present. Without `--internal`, internal environments whose names are reserved for Hatch's own workflows must be hidden. If one or more environment names are passed and any is not configured, the command must fail.

`hatch env create [ENV_NAME]` must create the named environment, defaulting to `default`. If the selected name is a matrix parent, the command must expand it to all generated matrix environments. Existing environments must be reported and left intact. If a selected non-matrix environment is incompatible with the current platform or Python constraints, the command must fail. If a matrix parent expands to both compatible and incompatible environments, incompatible generated environments must be skipped and reported.

`hatch env find [ENV_NAME]` must print the filesystem location for the selected environment or each generated environment for a matrix parent. It must fail when the name is not defined by project config.

`hatch env remove [ENV_NAME]` must remove the selected environment, defaulting to the active root environment. If the selected name is a matrix parent, the command must remove all generated environments. It must fail when the name is not defined. It must fail when attempting to remove the currently active environment.

`hatch env prune` must remove all configured project environments, including internal environments, and must fail before removing anything when any selected environment has an unknown type or is currently active.

`hatch shell [ENV_NAME]` must create or synchronize the selected environment before entering a shell. It must fail when the selected environment is already active. If a matrix parent is selected, it must fail and show the generated environment names to choose from. Shell name, path, and arguments must come from the user config unless overridden by `--name` or `--path`.

`hatch env run` must run a command in one or more environments. If no `-e/--env` is given, it must target the active root environment. Multiple `-e/--env` selections must be deduplicated while preserving order. Selecting `system` must run without creating a project environment and must expose project-level scripts. If no environments are selected, the command must fail.

`hatch env run -i/--include` and `-x/--exclude` must select matrix environments by variables. Inclusion filters must be an intersection; exclusion filters must be a union. Variable selection must fail for non-matrix environments. Duplicate included variables or duplicate excluded variables must fail. `--filter JSON` must require a JSON mapping and must select environments whose config contains matching key-value pairs.

`hatch run [ENV:]ARGS...` must be a convenience wrapper around `hatch env run`. A prefix before the first colon selects the environment; no prefix uses the active root environment; an empty prefix selects `system`. Leading `+VARIABLE[=VALUES]` and `-VARIABLE[=VALUES]` arguments must be translated to matrix include and exclude filters. If no command remains after matrix filters, the command must fail.

When `hatch run` receives a path ending in `.py` that exists and contains PEP 723 inline script metadata, Hatch must create a dedicated script environment keyed by the script's absolute path, set `skip-install = true`, default the installer to `uv`, merge top-level `dependencies`, honor `[tool.hatch]` environment settings from the script metadata, infer a Python version from `requires-python` when needed, and run `python SCRIPT_PATH` with remaining arguments. Multiple inline script metadata blocks of type `script` must fail.

## Environment Lockfile Behavior

An environment with `locked = true` must use a PEP 751 lockfile. The default lockfile name must be `pylock.toml` for the `default` environment and `pylock.<ENV_NAME>.toml` for other environments. `lock-filename` must override that path for a specific environment. `lock-envs = true` must make locking the default for all environments, while `locked = false` on an environment must opt that environment out.

`hatch env lock` with no environment name must lock all environments configured with `locked = true` and must fail when none are configured. `hatch env lock ENV_NAME` must lock the named environment or all generated environments for a matrix parent. A named environment must have `locked = true` unless `--export` or `--export-all` is used. Unknown environment names must fail.

`hatch dep lock` and `hatch lock` must run the same lock workflow for the active root environment selected by `-e/--env` or `HATCH_ENV`. `--export-all` must lock all configured environments into the chosen directory. `--export` and `--export-all` are mutually exclusive and must fail when used together.

`--check` must fail when the selected lockfile does not exist or is not up to date. If the lockfile is up to date, it must report success and leave the file unchanged. `--upgrade` must request upgrading all locked packages. Repeated `--upgrade-package NAME` options must request upgrades for only those packages.

## Build And Clean Behavior

Build configuration lives under `[tool.hatch.build]` and `[tool.hatch.build.targets.<TARGET_NAME>]`. The built-in targets in scope are `sdist` and `wheel`. Invoking `hatch build` without targets must build both `sdist` and `wheel`. Repeating `-t/--target TARGET` must build only the selected targets in the requested order. A target string supports versions using `TARGET:VERSION` or comma-separated versions, and the target/version string must be passed through to the build backend.

The build output directory must be the command `LOCATION` argument when provided; otherwise it must be `tool.hatch.build.directory` when configured; otherwise it must be `dist`. Relative output directories must be relative to the project root. Successful builds must print the generated artifact paths.

Global build config defines defaults for targets, and target config must override global config for the same target. Build target `dependencies`, `require-runtime-dependencies`, and `require-runtime-features` must affect the build environment's additional dependencies. Invalid build config types must fail with an error identifying the invalid field.

File selection must support `include`, `exclude`, `artifacts`, `only-include`, `packages`, `force-include`, `only-packages`, and `sources`. `exclude` must take precedence over normal include patterns. `artifacts` must include files ignored by VCS and must not be removed by `exclude`; artifact negation patterns must come after the broader artifact pattern. `only-include` must ignore `include`. `packages` must behave as `only-include` plus source-prefix removal. `force-include` sources must exist and must fail if they overwrite an already included path.

By default, builds must be reproducible for targets that support reproducibility. When reproducibility is enabled, build timestamps must use `SOURCE_DATE_EPOCH` if set and otherwise use Hatch's stable default timestamp. `reproducible = false` must disable that behavior.

`--hooks-only`, `--no-hooks`, `--clean`, and `--clean-hooks-after` must be honored by the build workflow and by their corresponding `HATCH_BUILD_*` environment variables. `--no-hooks` must take precedence over hook-enabling options. `--ext` must behave as `--hooks-only -t wheel`.

`hatch clean` must remove build artifacts by invoking the same target selection and hook artifact selection rules as `hatch build` in clean-only mode. It must accept the same location, target, hook-only, no-hooks, and extension-target options that are in scope for cleaning.

## Version Behavior

`hatch version` must display the current project version. If the project has a static `project.version`, Hatch must print that value. If the version is dynamic, Hatch must use `[tool.hatch.version]`. The default version source is `regex`, which requires a relative `path` to a file containing the version. The default regex must find a variable named `__version__` or `VERSION` assigned to a string, with an optional lowercase `v` prefix. A custom `pattern` must contain a named capture group called `version`; if it does not, version retrieval or update must fail.

`hatch version DESIRED_VERSION` must update a dynamic Hatch-managed version source and print the old and new versions. If the project version is statically defined in `project.version`, setting a version must fail. If the build backend is not Hatchling, setting a version must fail, though displaying dynamic metadata must still work through the configured build frontend.

The default version scheme is the standard PEP 440-based scheme. Explicit version updates must reject invalid versions and downgrades unless `--force` is supplied. Segment updates must support `release`, `major`, `minor`, `micro`, `patch`, `fix`, `a`, `alpha`, `b`, `beta`, `c`, `rc`, `pre`, `preview`, `r`, `rev`, `post`, and `dev`. Comma-separated segment updates must be applied as one requested update, such as `major,rc`.

If no project is detected, `hatch version` must fail. If a configured project name was selected but its location is not a valid project, the command must fail and identify that project.

## Error Semantics

- Missing custom config file selected by `--config` or `HATCH_CONFIG` must fail before subcommand execution.
- Unknown configured project selected by `--project` must fail.
- Invalid TOML shape for Hatch configuration tables and known options must fail with the invalid field name.
- Unknown metadata field in `hatch project metadata FIELD` must fail.
- Unknown environment name in `env create`, `env find`, `env show`, `env remove`, `env run`, `env lock`, `dep lock`, or `lock` must fail.
- Unknown environment type must fail when Hatch needs to instantiate or prune that environment.
- Removing or pruning the currently active environment must fail.
- Selecting matrix variables for a non-matrix environment must fail.
- Duplicate matrix include variables or duplicate matrix exclude variables must fail.
- `hatch env run --filter` with non-mapping JSON must fail.
- Matrix definitions with empty variables, empty values, duplicate values, non-string values, both `py` and `python`, or invalid `matrix-name-format` must fail.
- Environment inheritance with an unknown template or circular template chain must fail.
- Script expansion with a circular script reference must fail.
- Multiple PEP 723 script metadata blocks of type `script` must fail.
- `hatch env lock`, `hatch dep lock`, and `hatch lock` must fail when `--export` and `--export-all` are used together.
- Lock checking must fail when the lockfile does not exist or is out of date.
- Build target names unsupported by the active build backend must fail.
- `force-include` entries whose source path does not exist or that overwrite an already included distribution path must fail.
- Version setting must fail for static `project.version`, missing project state, invalid versions, disallowed downgrades, unsupported build backend updates, and dynamic regex patterns without a named `version` group.

## Cross-View Invariants

- `hatch config set project NAME` must affect later project-mode invocations that rely on the config file selected by the same config path.
- `hatch config set dirs.env.virtual PATH` must affect later `hatch env find` results for virtual environments that do not define an explicit `path`.
- `hatch env show --json` must return script expansions, environment variables, dependencies, pre-install commands, and post-install commands in the same resolved form used by `hatch env run`.
- `hatch env create NAME` must create the same environment path that `hatch env find NAME` returns.
- `hatch env remove NAME` must remove the environment path that `hatch env find NAME` returned before removal.
- `hatch run ENV:SCRIPT` must target the same environment that `hatch env run -e ENV SCRIPT` targets.
- `hatch run +py=VERSION ENV:SCRIPT` must select the same generated matrix environments as `hatch env run -e ENV -i py=VERSION SCRIPT`.
- `hatch env lock NAME --check` must validate the same dependency inputs used by `hatch env lock NAME` for that environment.
- `hatch version DESIRED_VERSION` must update the same version source read by later `hatch version` and by `hatch project metadata version`.
- `hatch build LOCATION -t wheel` must write wheel artifacts to the same location that `hatch clean LOCATION -t wheel` cleans.

## Representative Workflow

Start with a local project containing `pyproject.toml`:

```toml
[project]
name = "demo-app"
dynamic = ["version"]
dependencies = ["click"]

[tool.hatch.version]
path = "src/demo_app/__about__.py"

[tool.hatch.envs.test]
dependencies = ["pytest"]

[tool.hatch.envs.test.scripts]
run = "pytest {args:tests}"

[[tool.hatch.envs.test.matrix]]
python = ["3.11", "3.12"]
mode = ["unit", "integration"]

[tool.hatch.build.targets.wheel]
packages = ["src/demo_app"]
```

The command `hatch env show --json` must show `default`, the generated `test.py3.11-unit`, `test.py3.11-integration`, `test.py3.12-unit`, and `test.py3.12-integration` environments. `hatch run +py=3.11 test:run -q` must run the expanded `run` script in only the two Python 3.11 matrix environments, creating or synchronizing them first. `hatch version minor` must update the configured version source. `hatch build -t wheel` must create a wheel in `dist`. `hatch clean -t wheel` must remove the wheel build artifacts selected by the same target rules.

If the same project adds `hatch.toml` with:

```toml
[envs.test.scripts]
run = "pytest -m smoke"
```

then `hatch run test:run` must use the `hatch.toml` script definition because top-level Hatch options in `hatch.toml` take precedence over matching `tool.hatch` project options.

## Non-Goals

This scoped contract does not require:

- Implementing Hatchling's full backend internals or every wheel/sdist file layout edge case beyond the local Hatch CLI contracts above.
- Publishing artifacts to package indexes, network repository APIs, credentials, keyring behavior, or trusted publishing.
- Downloading, updating, or managing Python distributions.
- Implementing third-party plugin discovery or custom plugin internals beyond honoring documented built-in names and public configuration errors.
- Matching exact Rich table borders, color styles, spinner frames, traceback styling, or other terminal formatting details.
- Implementing static analysis, test runner, Python installation management, self-update, project template generation, or dependency display commands outside the scoped command list.
- Preserving exact wording of non-contractual status messages.
- Supporting remote filesystems or non-local project workflows.

## Invocation Protocol

`hatch` and `python -m hatch` are both supported.

Exit codes:

| Situation | Exit code |
| --- | ---: |
| Help or version output succeeds | 0 |
| A scoped command completes successfully | 0 |
| A command executed by `hatch run` or `hatch env run` exits nonzero without ignored exit handling | that command's exit code |
| Multiple commands run with `--force-continue` and at least one fails | the first failing command's exit code |
| User input, configuration, project, environment, build, lock, or version validation fails | nonzero |
| An uncaught internal exception reaches `hatch.cli.main()` | 1 |

Commands that execute inside environments must run from the project root, regardless of the original current working directory. Commands that operate on a selected project by configured name must use that project's root as their working project location.

## Evaluation Notes

The assessment exercises observable local CLI behavior and file effects. It covers project discovery, config-file precedence, command option parsing, environment inheritance and matrices, environment selection and script expansion, lockfile command validation, local build/clean target selection, version display/update behavior, and error handling for invalid local configuration.

Tests use temporary local projects and local files. They do not require remote package publication, credential storage, network index interaction, Python distribution downloads, exact terminal styling, or private implementation names. Passing work should focus on correct user-visible state transitions, filesystem effects, JSON/plain output content, and exit statuses rather than matching decorative formatting.

