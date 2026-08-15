# tox Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

tox automates Python project checks by creating isolated environments, installing dependencies and the project package, running configured commands, and reporting a per-environment result. It is a command line application first, with a small Python entry point and a plugin API for projects or third-party packages that need to extend tox.

tox is test-tool agnostic. A tox environment may run pytest, linters, formatters, documentation builders, packaging tools, or any other command. Its distinctive contract is that the same project configuration can describe many environments, select which ones run, resolve substitutions and conditional values, isolate environment variables, and expose the resolved state through CLI views such as `tox list`, `tox config`, and `tox schema`.

## Non-Goals

- Private module layout, private helper functions, exact source classes, and internal cache file implementation are not specified.
- Terminal colors, progress spinner frames, debug timestamps, and exact prose of non-error log lines are excluded except where documented behavior or machine-readable output requires them.
- Real network access to public package indexes is excluded; dependency installation may use local packages, local indexes, skipped installs, or controlled test doubles.
- Build backends, virtual environments, package installers, and interpreter discovery are delegated to installed tools or controlled doubles while preserving documented configuration, selection, invocation, and reporting decisions.
- Undocumented private imports, test-only fixtures, and maintainer onboarding material are excluded from the public user API.

## Representative Workflows

Create a TOML configuration with two Python test environments and one lint environment:

```toml
env_list = ["3.13", "3.12", "lint"]

[env_run_base]
description = "run the test suite"
deps = ["pytest>=8"]
commands = [["pytest", { replace = "posargs", default = ["tests"], extend = true }]]

[env.lint]
description = "run lint checks"
skip_install = true
deps = ["ruff"]
commands = [["ruff", "check", { replace = "posargs", default = ["."], extend = true }]]
```

The following commands demonstrate common interactions with the configuration above:

```console
$ tox run -e 3.13 -- -v
$ tox list
default environments:
3.13 -> run the test suite
3.12 -> run the test suite
lint -> run lint checks
$ tox config -e 3.13 -k deps commands --format json
$ tox exec -e 3.13 -- python -c "import sys; print(sys.executable)"
```

`tox run -e 3.13 -- -v` passes `-v` to pytest through the positional replacement. `tox list` shows all configured environments with descriptions. `tox config` with `--format json` shows resolved values a tool can consume programmatically. `tox exec` runs only the specified command inside the environment without executing the configured command phases.

For coverage aggregation, define test environments and a `coverage` environment with `depends = ["3.*"]`. Selecting `tox run -e 3.13,3.12,coverage` runs the selected test environments before coverage. Selecting only `tox run -e coverage` does not automatically add the test environments; dependencies order and gate selected environments but do not expand the selection.

For a plugin, install a package that declares a `tox` entry point and implements hooks decorated with `tox.plugin.impl`. A hook can add a config key in `tox_add_env_config`, observe package installation in `tox_on_install`, and summarize command outcomes in `tox_after_run_commands`. A project-local `toxfile.py` can define the same hooks without packaging a separate plugin.

## Configuration Files

This section covers how tox discovers, parses, and structures project configuration from supported file formats.

**Format support.** tox supports both TOML and INI configuration.  TOML is recommended for new projects because it preserves types directly.  INI remains supported for existing projects.

**Discovery order.** When tox discovers configuration from the current project, the documented search order is: (1) `tox.ini` using INI syntax; (2) `setup.cfg` using INI syntax with `[tox:tox]` as the core section header; (3) `pyproject.toml` with native `tool.tox` TOML configuration; (4) `pyproject.toml` with `tool.tox.legacy_tox_ini` containing INI text; (5) `tox.toml` using TOML syntax.  When both native `tool.tox` and `legacy_tox_ini` are present in `pyproject.toml`, native TOML configuration must be preferred.  The `-c` flag must override discovery and select an explicit configuration file regardless of working directory.

**Section structure.** INI files use `[tox]` for core settings, `[testenv]` as the base for run environments, `[testenv:<name>]` for specific run environments, and `[pkgenv]` as the base for package environments.  `setup.cfg` uses `[tox:tox]` as the core section header instead of `[tox]`.  Native TOML uses top-level keys for core settings, `[env_run_base]` for run-environment defaults, `[env.<name>]` for explicit run environments, `[env_base.<name>]` for templates that generate environments from factors, and `[env_pkg_base]` for package-environment defaults.

**Environment generation.** INI generative environment lists must expand factor groups enclosed in braces into a Cartesian product of their elements; `py{310,311}-django{42,50}` must produce environments `py310-django42`, `py310-django50`, `py311-django42`, and `py311-django50`.  TOML `env_list` must also accept `product` replacement objects that define factor ranges; a product object with `prefix`, `start`, and `stop` fields combined with a list of suffix factors must generate the corresponding Cartesian product of environments.  `[env_base.<name>]` must accept a `factors` list and must generate one environment per factor, named `<name>-<factor>`, inheriting the template's settings.

**Labels and dependencies.** Environments may declare `labels` as a list of label names.  Core configuration may define `labels.<name>` to associate label names with environment lists.  The `depends` key must declare prerequisite environments; dependencies must affect ordering but must not silently add unselected environments to the run.

**Unused keys.** Options belong to either the core configuration or an environment configuration.  A key placed in the wrong section must be treated as unused rather than moved automatically.  Users can surface unused keys with verbose runs or `tox config`.

## Packaging

This section covers how tox builds and installs project packages for run environments.

**Package modes.** The `package` setting controls project packaging.  When set to `sdist`, tox must build a source distribution; this is the default mode.  When set to `wheel`, it must build a wheel.  When set to `sdist-wheel`, it must build an sdist and then build a wheel from that sdist.  When set to `editable`, it must build an editable wheel using PEP 660.  When set to `editable-legacy`, it must invoke pip editable installation.  When set to `skip`, it must not package the project.  When set to `external`, it must use a package supplied externally.

**Package environments.** Package environments must not inherit from `env_run_base` or `[testenv]`; they must inherit from `env_pkg_base` or `[pkgenv]`.  For sdist builds, the package environment must default to `.pkg`.  Wheel builds must use a wheel build environment name based on the target Python implementation and version unless `wheel_build_env` overrides it.  `sdist-wheel` must use both the sdist package environment and a wheel build environment.  The resolved `package_env` key must be visible in configuration output and must identify the packaging environment associated with each run environment.

**Artifact exposure.** When tox builds a package for a run environment, it must expose the built artifact path through `TOX_PACKAGE` in that environment.  When there are multiple artifacts, the paths must be joined with the platform path separator.

**Auto-provisioning.** When the installed tox version or declared `requires` constraints are not satisfied, tox must auto-provision itself into a dedicated tox environment, install the required tox and plugin versions there, and delegate the invocation to that provisioned tox.  The provisioning environment must not inherit normal run-environment defaults.

## Substitutions and Conditional Values

This section covers how tox resolves substitution expressions, conditional values, and positional arguments in configuration values.

**INI substitutions.** INI values use string substitutions inside `{...}`.  Native TOML supports inline replacement objects for the same concepts.  Backslash escapes literal `{`, `}`, `:`, `[`, and `]` in substitution expressions.  Special substitutions with colon-delimited arguments must not have a space after the colon.

**Built-in substitution variables.** Important substitution variables include `{tox_root}` and `{toxinidir}` for the directory where the configuration file is located; `{work_dir}` and `{toxworkdir}` for the tox working directory; `{env_name}` and `{envname}` for the current environment name; `{env_dir}` and `{envdir}` for the environment directory; `{env_tmp_dir}` and `{envtmpdir}` for the environment temporary directory; `{env_bin_dir}` and `{envbindir}` for the environment executable directory; `{env_python}` and `{envpython}` for the environment Python executable; `{env_site_packages_dir}` and `{envsitepackagesdir}` for pure Python site packages; `{env_site_packages_dir_plat}` and `{envsitepackagesdir_plat}` for platform-specific site packages; `{base_python}` and `{basepython}` for the configured base interpreter; `{/}` for the OS path separator; `{:}` for the OS path-list separator; `{tty:ON:OFF}` for interactive-terminal dependent values.

**Environment variable substitution.** Environment variable substitution reads the host environment.  An unset variable must resolve to an empty string unless a default is supplied.  The syntax `{env:VAR:default}` must resolve to the value of `VAR` from the host environment, or `default` when `VAR` is not set.

**Positional arguments.** Positional-argument substitution must insert the arguments supplied after `--` on the command line.  When no positional arguments are supplied, the configured default must be used.  Positional arguments must be visible only through positional substitutions or the explicit command passed to `tox exec`; they must not change unrelated configuration keys.

**Glob and list expansion.** Glob substitution expands file matches relative to `tox_root`.  In TOML list contexts, replacement objects with `extend = true` must spread list results into the containing list.  Without `extend`, a replacement object must contribute a single value.

**Conditional replacement.** Native TOML conditional replacement uses `{ replace = "if", condition = "...", then = ..., "else" = ... }`.  Conditions can read `env.VAR` or `env["VAR"]`, factor truth values with `factor.NAME` or `factor["NAME"]`, the full `env_name`, string literals, equality/inequality, and `and`/`or`/`not`.  The selected branch must then be processed through normal substitution.  Conditions must read from the host environment before `set_env` is applied.  When the condition references an unset environment variable, the `else` branch must be selected.

**Factor labels.** `{factor:label}` must resolve to the active value for a labeled factor group.  Plain factor groups must also have positional labels, starting at `{factor:0}`.

## Execution and Failure Behavior

This section covers how tox executes commands within environments, handles command outcomes, manages environment lifecycle, and runs environments in parallel.

**Command phases.** Each environment may define `commands_pre`, `commands`, and `commands_post` phases.  When `--notest` is supplied, tox must skip the `commands` phase but must still run `extra_setup_commands` if configured.  The `--skip-pkg-install` flag must skip project package installation while still executing the configured command phases.

**Command prefixes.** In INI configuration, a command line prefixed with `-` must ignore a non-zero exit code from that command and must continue to the next command.  A command line prefixed with `!` must invert the success expectation: the command must succeed when it exits with a non-zero code and must fail when it exits with zero.  Commands without a prefix must fail the environment when they exit with a non-zero code.

**Command failure.** When a command exits with a non-zero code and is not configured to ignore or invert that result, the environment must fail and later commands for that environment must not be run.

**Environment variables.** `pass_env` must define patterns of host environment variables to pass through to the environment.  `disallow_pass_env` must exclude specific variables from pass-through even when matched by `pass_env`.  `set_env` must define environment variables to set explicitly in the environment, overriding any passed-through values.  These resolved values must be visible in `tox config` output.

**Environment lifecycle.** A repeated `tox run` for the same environment must reuse the existing environment directory when it is still valid.  The `-r` or `--recreate` flag must force tox to delete and recreate the environment directory from scratch before running commands.

**Parallel execution.** Parallel mode must run environments in separate workers after packaging is complete.  `--parallel` must accept `all`, `auto`, or an integer limit; `auto` must limit concurrency to the CPU count.  Parallel mode can show a spinner, suppress the spinner, or show live output.  Standard input must be disabled for parallel execution.  In parallel mode, dependencies must delay scheduling until prerequisite environments have completed, regardless of their outcome.  Parallel mode must show output for failed environments and for environments configured to show parallel output.

**Fail-fast.** `fail_fast` must stop scheduling additional environments after the first non-ignored failure.  In parallel mode, environments already running must continue to completion, while not-yet-started environments must be skipped.  Environments with `ignore_outcome = true` must not trigger fail-fast.  Dependent environments must not run when their dependency fails under fail-fast.

**Exit status.** tox must return exit code `0` only when all required selected environments complete successfully.  A failed command must normally contribute its exit code to the final outcome.  Skipped environments and handled tox-level errors must use tox's documented non-success statuses.

## Command Line Interface

This section covers the subcommands, flags, output formats, and plugin hooks exposed by the tox command line.

**Subcommands.** The CLI subcommands are: `run` (`r`) for running selected environments sequentially (the default action); `run-parallel` (`p`) for running selected environments concurrently after packaging; `depends` (`de`) for inspecting or resolving environment dependency ordering; `list` (`l`) for listing configured environments and their descriptions; `config` (`c`) for showing resolved tox configuration; `exec` (`e`) for running an arbitrary command inside a tox environment; `devenv` (`d`) for creating a development environment; `schema` for generating a configuration schema; `quickstart` (`q`) for interactively creating initial configuration; `man` for setting up the tox man page; and `legacy` (`le`) for preserving legacy entry-point behavior.

**Global options.** Common global options include `-c` for selecting a configuration file or folder, setting the tox work directory, setting the project root, choosing a default runner, changing verbosity (repeated `-v` flags increase detail), color behavior via `--colored {yes,no,auto}`, and applying configuration overrides with `-x` or `--override`.

**Environment selection and filtering.** The `-e` flag must select specific environments by name.  The `-f` flag must filter environments by factor, selecting only those whose name includes the specified factor.  The `-m` flag must select environments by label, choosing only those associated with the named label.  Selecting an unknown environment name must return a nonzero exit code.

**List output.** `tox list` must show all configured environments with their descriptions.  `tox list --no-desc` must list environment names without descriptions, one per line.  Label filtering with `-m` must restrict the listed environments to those matching the label.

**Config output.** `tox config` must support an INI-style default output and machine-readable `json` and `toml` formats via `--format`.  JSON and TOML output must preserve native booleans, numbers, arrays, and tables and must use the same structural names as native TOML configuration: environment settings under `env.<name>`.  By default, the `tox` core configuration section must not appear in JSON output; the `--core` flag must include core settings under the `tox` key.  The `-k` flag must limit the projection to the named configuration keys.  The `-o` flag must write the selected format to a file and must produce no output on stdout.  Unused configuration keys must appear in the rendered configuration so users can diagnose misplaced or misspelled options.

**Exec.** `tox exec -e ENV -- COMMAND ...` must create or reuse the selected environment and must run the given command inside it.  It must not run `commands`, `commands_pre`, or `commands_post`, and it must skip project package installation.  The command must resolve inside the environment `PATH` or be explicitly permitted through `allowlist_externals`.

**Plugin hooks.** Plugin hook functions receive the objects documented by the hook name.  The `impl` decorator must mark the decorated function with a `tox_impl` attribute so it is discoverable by the plugin system.  `tox_extend_envs` must return additional environment names that tox should consider.  `tox_add_env_config` must receive the environment configuration object and state, and may call `env_conf.add_config` to register custom configuration keys.  `tox_on_install` must run before tox executes an installation command and must identify the install phase with `section` and `of_type`.  `tox_after_run_commands` must receive the final command-phase exit code and the per-command `Outcome` objects.  `tox_env_teardown` must run after an environment has finished, whether it succeeded or failed.  Project-local hooks in `toxfile.py` must follow the same protocol without requiring a separate package.

**Execution result object.** The execution result object visible to plugin hooks must expose the execution request, whether output was shown on standard streams, the command exit code, captured stdout and stderr text, start and end time samples, the command as executed, optional metadata, an elapsed duration, and an output pair helper.  It must be truthy only when the exit code is zero.

## State Model

A tox project has three public projections of the same resolved environment state: source configuration, machine-readable list/config/dependency views, and the environments and commands executed by a run. Discovery and inheritance must produce the same environment names and values in every projection. Selection and dependency ordering must agree between inspection and execution. Reuse or recreation may change filesystem state but must not change the resolved command contract.

## Error Semantics

A malformed or inconsistent configuration should produce a handled tox error with a clear message and a non-zero status, not an internal traceback.

Missing required TOML configuration keys raise a configuration-key error during loading. Circular configuration references raise a circular-chain error. Duplicate plugin configuration definitions for the same non-core config key are rejected.

An empty command execution request is invalid and raises `ValueError`.

If an environment's selected interpreter cannot be found, tox either skips or fails according to `skip_missing_interpreters`. The default behavior is to fail the run; setting the option or flag to skip missing interpreters reports the environment as skipped instead.

If an environment name implies a Python version or architecture that conflicts with explicit `base_python`, tox reports the conflict unless `ignore_base_python_conflict` permits it.

If a command exits with a non-zero code and is not configured to ignore or invert that result, the environment fails and later commands for that environment are not run.

`pylock` and `deps` are mutually exclusive for dependency installation. A configuration that sets both for the same environment is invalid.

The `virtualenv-pep-723` runner reads PEP 723 metadata from a configured script. Script paths are resolved relative to `tox_root`, paths escaping `tox_root` are rejected, and the runner rejects an explicit `base_python` because the script metadata owns Python-version constraints.

## Cross-View Invariants

1. An environment visible in `tox list` is the same environment name accepted by `tox run -e`, `tox config -e`, and `tox exec -e`, subject to the same selection and generation rules.
2. A value shown by `tox config` is the value tox uses for the run after inheritance, overrides, substitutions, and conditional replacements have been resolved.
3. `tox config --format json` and `tox config --format toml` expose the same resolved configuration as the default config view while preserving native booleans, numbers, arrays, and tables.
4. `tox run`, `tox run-parallel`, and `tox depends` agree on dependency ordering: dependencies can reorder selected environments but do not silently add unselected environments to the run.
5. The environment variable view from `tox config -k set_env pass_env` matches command execution: variables selected by `pass_env`, removed by `disallow_pass_env`, overridden by `set_env`, and injected by tox are the variables commands receive.
6. A selected package mode determines both the package artifact built and the packaging environment used; run environments observe the result through package installation and `TOX_PACKAGE`, not by inheriting package-environment settings.
7. Positional arguments after `--` are visible only through positional substitutions or the explicit command passed to `tox exec`; they do not change unrelated configuration keys.
8. Labels, factors, and generated environment names are consistent across `tox list`, `tox run -m`, `tox run -f`, and substitution expressions such as `factor.NAME` or `{factor:label}`.
9. Unused or misplaced configuration keys remain visible as unused in configuration views and warnings; tox does not silently reinterpret them in another section.
10. The final process status agrees with the per-environment report: a success status requires all required selected environments to succeed, while failed, skipped, or ignored outcomes are reflected according to their documented configuration.

## Public Interface

### Import Surface

The installed package provides the `tox` console script. Invoking `tox` with no subcommand is equivalent to running the default environments listed by `env_list`.

The top-level Python import surface is:

```python
from tox import main
```

`main(args)` executes tox as if `args` were the command line arguments after the program name and returns the process status code. The console script entry point wraps the same behavior and exits the process with that status.

Plugin authors use:

```python
from tox.plugin import NAME, impl
```

`NAME` is the pluggy project name, `"tox"`. `impl` is the hook implementation marker used to decorate tox plugin hook functions.

tox discovers distributable plugins from Python package entry points in the `tox` group, and also loads project-local hooks from `toxfile.py` beside the tox configuration file.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| main | function | Execute tox from an argument list and return process status |
| NAME | constant | Pluggy project name for plugin registration |
| impl | decorator | Marker for tox plugin hook implementations |
| tox_register_tox_env | hook | Register custom tox environment types |
| tox_extend_envs | hook | Return additional environment names |
| tox_add_option | hook | Add CLI options to the tox parser |
| tox_add_core_config | hook | Add core configuration keys |
| tox_add_env_config | hook | Add per-environment configuration keys |
| tox_before_run_commands | hook | Run before an environment executes its commands |
| tox_after_run_commands | hook | Observe command outcomes after an environment run |
| tox_on_install | hook | Observe installation commands before execution |
| tox_env_teardown | hook | Run after an environment finishes |
| Outcome | class | Per-command execution result visible to plugin hooks |
| run | CLI subcommand | Run selected environments sequentially |
| run-parallel | CLI subcommand | Run selected environments concurrently after packaging |
| depends | CLI subcommand | Inspect or resolve environment dependency ordering |
| list | CLI subcommand | List configured environments and descriptions |
| config | CLI subcommand | Show resolved configuration in human or machine-readable form |
| exec | CLI subcommand | Run an arbitrary command inside one environment |
| schema | CLI subcommand | Generate a configuration schema |
| devenv | CLI subcommand | Create a development environment from tox configuration |
| quickstart | CLI subcommand | Interactively create an initial configuration file |
| legacy | CLI subcommand | Preserve legacy entry-point command behavior |
| man | CLI subcommand | Set up the tox man page for the current shell |

### CLI Entry Points

The `tox` console script and `python -m tox` are supported.  `--version` must print version information and return zero.  `--help` must print usage information including available subcommands and return zero.  Every subcommand accepts the root-level option `--colored {yes,no,auto}` controlling colored output; `--colored no` must disable ANSI color codes so output is plain text.  A successful help, version, list, config, schema, or completed run must return zero.  Invalid configuration, unknown environment selection, or a required failed command must return nonzero.  The public `main(args)` function must return the same process-style status.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. Deterministic workflows may use temporary projects, local packages, virtual environments, and controlled subprocess commands without public package-index access.

## Appendix B: Assessment Notes

The expected implementation exercises the behavior described here through public imports, CLI invocations, configuration files, plugin hooks, and observable filesystem/output state. Tests may compare the same project through several public views, such as `tox list`, `tox config`, a run result, log files, and generated schema output.

The focus is on user-visible contracts: configuration discovery and precedence, environment generation and selection, substitution and conditional evaluation, environment variable composition, package-mode effects, command execution outcomes, skip/fail behavior, plugin hook calls, and consistency between resolved configuration and actual runs.

Tests should not require private tox modules or hidden fixture shapes. They may use temporary projects, local files, local packages, and controlled subprocess commands to make outcomes deterministic. Exact stdout formatting is relevant only where tox documents a machine-readable format, a stable CLI option, an error condition, or a user-facing status distinction.
