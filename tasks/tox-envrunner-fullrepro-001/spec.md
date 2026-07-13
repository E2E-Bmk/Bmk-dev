# tox Specification

## Product Overview

tox automates Python project checks by creating isolated environments, installing dependencies and the project package, running configured commands, and reporting a per-environment result. It is a command line application first, with a small Python entry point and a plugin API for projects or third-party packages that need to extend tox.

tox is test-tool agnostic. A tox environment may run pytest, linters, formatters, documentation builders, packaging tools, or any other command. Its distinctive contract is that the same project configuration can describe many environments, select which ones run, resolve substitutions and conditional values, isolate environment variables, and expose the resolved state through CLI views such as `tox list`, `tox config`, and `tox schema`.

## Scope

This specification covers:

- the `tox` command line interface and its documented subcommands;
- configuration discovery and the supported TOML and INI configuration shapes;
- environment selection, generative environment lists, labels, factors, and dependencies;
- environment creation, dependency installation, project packaging modes, command execution, logging, and result reporting;
- substitution syntax, TOML replacement tables, environment variable composition, and injected variables;
- the public Python import surface and the documented plugin hook surface.

## Installable Surface

The installed package provides the `tox` console script. Invoking `tox` with no subcommand is equivalent to running the default environments listed by `env_list`.

The top-level Python import surface is:

```python
from tox import __version__, main

main(args: Sequence[str]) -> int
```

`__version__` is the installed tox version string. `main(args)` executes tox as if `args` were the command line arguments after the program name and returns the process status code. The console script entry point wraps the same behavior and exits the process with that status.

Plugin authors use:

```python
from tox.plugin import NAME, impl
```

`NAME` is the pluggy project name, `"tox"`. `impl` is the hook implementation marker used to decorate tox plugin hook functions.

tox discovers distributable plugins from Python package entry points in the `tox` group, and also loads project-local hooks from `toxfile.py` beside the tox configuration file.

## Public API

The CLI subcommands are:

- `run` (`r`): run selected environments sequentially. This is the default action for normal tox invocations.
- `run-parallel` (`p`, also documented as parallel mode): run selected environments concurrently after packaging has completed.
- `depends` (`de`): inspect or resolve environment dependency ordering.
- `man`: set up the tox man page for the current shell.
- `list` (`l`): list configured environments and their descriptions.
- `devenv` (`d`): create a development environment at a requested directory from tox configuration.
- `schema`: generate a schema for tox configuration.
- `config` (`c`): show resolved tox configuration, optionally for selected environments, keys, and output formats.
- `quickstart` (`q`): interactively create an initial tox configuration file.
- `exec` (`e`): run an arbitrary command inside a tox environment without running the environment's configured command phases.
- `legacy` (`le`): preserve the legacy entry-point command behavior.

Common global options include selecting a configuration file or folder, setting the tox work directory, setting the project root, choosing a default runner, changing verbosity or color behavior, and applying configuration overrides with `-x` or `--override`.

`tox config` supports an INI-style default output and machine-readable `json` and `toml` formats. JSON and TOML output preserve native types and use the same structural names as native TOML configuration: core settings at the top level and environment settings under `env.<name>`. `-o` writes the selected format to a file without color codes. Unused configuration keys appear in the rendered configuration so users can diagnose misplaced or misspelled options.

`tox exec -e ENV -- COMMAND ...` creates or reuses the selected environment and runs the given command inside it. It does not run `commands`, `commands_pre`, or `commands_post`, and it skips project package installation. The command must resolve inside the environment `PATH` or be explicitly permitted through `allowlist_externals`.

The documented plugin hook functions are:

```python
tox_register_tox_env(register) -> None
tox_extend_envs() -> Iterable[str]
tox_add_option(parser) -> None
tox_add_core_config(core_conf, state) -> None
tox_add_env_config(env_conf, state) -> None
tox_before_run_commands(tox_env) -> None
tox_after_run_commands(tox_env, exit_code: int, outcomes: list[Outcome]) -> None
tox_on_install(tox_env, arguments: Any, section: str, of_type: str) -> None
tox_env_teardown(tox_env) -> None
```

`tox_extend_envs` returns additional environment names that tox should consider. `tox_on_install` runs before tox executes an installation command and identifies the install phase with `section` and `of_type`. `tox_after_run_commands` receives the final command-phase exit code and the per-command `Outcome` objects. `tox_env_teardown` runs after an environment has finished, whether it succeeded or failed.

The execution result object visible to plugin hooks has these stable user-facing attributes: the execution request, whether output was shown on standard streams, the command exit code, captured stdout and stderr text, start and end time samples, the command as executed, optional metadata, an `elapsed` duration, and an `out_err()` pair. It is truthy only when the exit code is zero.

## Configuration Files

tox supports both TOML and INI configuration. TOML is recommended for new projects because it preserves types directly. INI remains supported for existing projects.

When tox discovers configuration from the current project, the documented search order is:

1. `tox.ini` using INI syntax;
2. `setup.cfg` using INI syntax;
3. `pyproject.toml` with native `tool.tox` TOML configuration;
4. `pyproject.toml` with `tool.tox.legacy_tox_ini` containing INI text;
5. `tox.toml` using TOML syntax.

If both native `tool.tox` and `legacy_tox_ini` are present in `pyproject.toml`, native TOML configuration is preferred for tox versions that understand it.

INI files use `[tox]` for core settings, `[testenv]` as the base for run environments, `[testenv:<name>]` for specific run environments, and `[pkgenv]` as the base for package environments. Native TOML uses top-level keys for core settings, `[env_run_base]` for run-environment defaults, `[env.<name>]` for explicit run environments, `[env_base.<name>]` for templates that generate environments from factors, and `[env_pkg_base]` for package-environment defaults.

Options belong to either the core configuration or an environment configuration. A key placed in the wrong section is treated as unused rather than moved automatically. Users can surface unused keys with verbose runs or `tox config`.

## Environment Selection

`env_list` defines the default environments run by `tox` with no explicit environment selection. CLI selection can name one environment, a comma-separated list, labels, or factors. Sequential runs preserve the selected order except where dependencies require a different order.

Environment names are split on `-` into factors. The current platform value, such as `linux`, `darwin`, or `win32`, is available as an implicit factor for conditional configuration. Python-like environment names also imply a base Python interpreter:

- `N.M` selects CPython `N.M` and is the preferred spelling;
- `pyNM` and `pyN.M` are legacy CPython spellings;
- `pypyNM`, `cpythonNM`, and `graalpyNM` select the named implementation and version.

An environment without a Python factor uses its explicit `base_python`, then `default_base_python`, then the Python interpreter running tox. If an explicitly defined environment is misspelled using a nearby Python-version spelling, tox reports the mismatch instead of silently falling back to the base environment. Unknown non-Python-like environment names may still be created from base settings unless the project configuration disallows that pattern.

INI generative lists use brace expansion, such as `py3{10-14}-django{42,50}`. Native TOML does not expand strings; TOML uses structured items. A literal string is one environment name. A bare range dict such as `{ prefix = "3.", start = 10, stop = 14 }` is a single axis. A bare labeled dict maps a label to factor values and enables `{factor:label}` substitution. A `product` dict creates Cartesian products from factor groups. Factor-group lists may contain strings, not nested range or labeled dicts.

Open-ended Python ranges expand deterministically to tox's known supported CPython minor bounds for the release. They do not probe the local machine for installed interpreters.

`env_base.<name>` templates generate environments from their `factors` key. The template name itself is not runnable. Generated environments inherit from the template, and the template inherits from `env_run_base`. The precedence for generated run environments is explicit `env.<name>`, then matching `env_base.<template>`, then `env_run_base`, then the built-in default.

Labels group environments. Environments whose `labels` include a requested label are selected by `tox run -m LABEL`. Factor selection with `-f FACTOR` runs environments whose names include that factor.

`depends` declares ordering constraints between environments. Glob patterns are supported. Dependencies reorder selected environments and gate scheduling in parallel mode, but selecting an environment does not automatically pull unselected dependencies into the run.

## Environment Lifecycle

For each selected run environment, tox creates or reuses an isolated environment, installs configured dependencies, optionally builds and installs the project package, runs extra setup commands, then runs configured commands.

Environment creation normally uses the `virtualenv` runner. The runner can be changed with the `runner` setting. For virtualenv-backed Python environments, `base_python` controls interpreter discovery. A base Python spec may include an architecture suffix such as `cpython3.12-64-arm64`; tox validates the discovered interpreter's architecture as well as its implementation and version.

tox reuses environments across runs. It recreates an environment when relevant project, interpreter, dependency, or virtualenv-spec inputs change. `tox run -r` forces recreation. When recreation occurs, `recreate_commands` run in the old environment before it is removed; failures in those cleanup commands are warnings and do not block recreation.

Dependency installation uses `deps` and `dependency_groups` unless `pylock` is configured. `pylock` installs from a PEP 751 lock file and is mutually exclusive with `deps`. Lock file package markers are evaluated against the target environment's Python and selected extras/dependency groups, not merely the host Python running tox.

`--skip-pkg-install` skips building and installing the project package while still allowing dependency installation. `--skip-env-install` skips both dependency installation and project package installation and requires the environment to already exist. Commands still run in either mode.

`extra_setup_commands` run after installations and before normal commands, and they run during the `--notest` phase.

The `commands` list runs in order. A non-zero exit code stops the environment and marks it failed. A command prefixed with `-` ignores its exit code. A command prefixed with `!` inverts success, treating non-zero as success and zero as failure. Command retries, when configured, retry failed commands up to the configured count before the failure is final.

## Packaging

The `package` setting controls project packaging:

- `sdist`: build a source distribution; this is the default mode.
- `wheel`: build a wheel.
- `sdist-wheel`: build an sdist, then build a wheel from that sdist.
- `editable`: build an editable wheel using PEP 660.
- `editable-legacy`: invoke pip editable installation.
- `skip`: do not package the project.
- `external`: use a package supplied externally.

Package environments do not inherit from `env_run_base` or `[testenv]`. They inherit from `env_pkg_base` or `[pkgenv]`. This keeps test-run settings from accidentally changing the build environment.

For sdist builds, the package environment defaults to `.pkg`. Wheel builds use a wheel build environment name based on the target Python implementation and version unless `wheel_build_env` overrides it. `sdist-wheel` uses both the sdist package environment and a wheel build environment.

When tox builds a package for a run environment, it exposes the built artifact path through `TOX_PACKAGE` in that environment. If there are multiple artifacts, the paths are joined with the platform path separator.

If the installed tox version or declared `requires` constraints are not satisfied, tox can auto-provision itself into a dedicated tox environment, install the required tox and plugin versions there, and delegate the invocation to that provisioned tox. The provisioning environment does not inherit normal run-environment defaults.

## Substitutions and Conditional Values

INI values use string substitutions inside `{...}`. Native TOML supports inline replacement objects for the same concepts. Backslash escapes literal `{`, `}`, `:`, `[`, and `]` in substitution expressions. Special substitutions with colon-delimited arguments must not have a space after the colon.

Important substitution variables include:

- `{tox_root}` and `{toxinidir}` for the directory where the configuration file is located;
- `{work_dir}` and `{toxworkdir}` for the tox working directory;
- `{env_name}` and `{envname}` for the current environment name;
- `{env_dir}` and `{envdir}` for the environment directory;
- `{env_tmp_dir}` and `{envtmpdir}` for the environment temporary directory;
- `{env_bin_dir}` and `{envbindir}` for the environment executable directory;
- `{env_python}` and `{envpython}` for the environment Python executable;
- `{env_site_packages_dir}` and `{envsitepackagesdir}` for pure Python site packages;
- `{env_site_packages_dir_plat}` and `{envsitepackagesdir_plat}` for platform-specific site packages;
- `{base_python}` and `{basepython}` for the configured base interpreter;
- `{/}` for the OS path separator;
- `{:}` for the OS path-list separator;
- `{tty:ON:OFF}` for interactive-terminal dependent values.

Environment variable substitution reads the host environment. An unset variable resolves to an empty string unless a default is supplied. Positional-argument substitution inserts the arguments after `--`; if no positional arguments are supplied, the configured default is used.

Glob substitution expands file matches relative to `tox_root`. In TOML list contexts, replacement objects with `extend = true` spread list results into the containing list. Without `extend`, a replacement object contributes a single value.

Native TOML conditional replacement uses `{ replace = "if", condition = "...", then = ..., "else" = ... }`. Conditions can read `env.VAR` or `env["VAR"]`, factor truth values with `factor.NAME` or `factor["NAME"]`, the full `env_name`, string literals, equality/inequality, and `and`/`or`/`not`. The selected branch is then processed through normal substitution. Conditions read from the host environment before `set_env` is applied.

`{factor:label}` resolves to the active value for a labeled factor group. Plain factor groups also have positional labels, starting at `{factor:0}`.

## Environment Variables and Commands

tox composes the environment for commands in this order:

1. `pass_env` glob patterns select host environment variables to pass through.
2. `disallow_pass_env` removes excluded variables after `pass_env` expansion.
3. tox prepends the virtual environment's executable directory to `PATH`.
4. `set_env` values are applied and can override earlier values, including `PATH`.
5. tox injects final variables that cannot be overridden, including `TOX_ENV_NAME`, `TOX_WORK_DIR`, `TOX_ENV_DIR`, `VIRTUAL_ENV`, `PIP_USER=0`, and `PYTHONIOENCODING=utf-8`.

If a user sets `PATH` in `set_env`, that value replaces the composed `PATH`. To keep environment-local command resolution, the configured value should include `{env_bin_dir}`.

Commands run with the configured `change_dir`. Installer commands run from `tox_root`. Command invocations are logged under `.tox/<env_name>/log`. Environment variable values whose names contain sensitive words such as `password`, `secret`, `token`, `key`, or `credential` are redacted in logs.

By default, command output is captured for logging and reporting. `--no-capture` (`-i`) gives the subprocess direct terminal access and is intended for REPLs, debuggers, and terminal UI programs. It is mutually exclusive with result JSON output and parallel mode. `tox exec` always runs in an interactive style appropriate for one-off commands.

External commands must either be available from the tox environment's `PATH` or be allowed by `allowlist_externals`.

## Parallel and Failure Behavior

Parallel mode runs environments in separate workers after packaging is complete. `--parallel` accepts `all`, `auto`, or an integer limit. `auto` limits concurrency to the CPU count. Parallel mode can show a spinner, suppress the spinner, or show live output. Standard input is disabled for parallel execution.

In parallel mode, dependencies delay scheduling until prerequisite environments have completed, regardless of their outcome. Parallel mode normally shows output for failed environments and for environments configured to show parallel output.

`fail_fast` stops scheduling additional environments after the first non-ignored failure. In parallel mode, environments already running continue to completion, while not-yet-started environments are skipped. Environments with `ignore_outcome = true` do not trigger fail-fast. Dependent environments do not run when their dependency fails under fail-fast.

tox returns exit code `0` only when all required selected environments complete successfully. A failed command normally contributes its exit code to the final outcome. Skipped environments and handled tox-level errors use tox's documented non-success statuses.

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

- An environment visible in `tox list` is the same environment name accepted by `tox run -e`, `tox config -e`, and `tox exec -e`, subject to the same selection and generation rules.
- A value shown by `tox config` is the value tox uses for the run after inheritance, overrides, substitutions, and conditional replacements have been resolved.
- `tox config --format json` and `tox config --format toml` expose the same resolved configuration as the default config view while preserving native booleans, numbers, arrays, and tables.
- `tox run`, `tox run-parallel`, and `tox depends` agree on dependency ordering: dependencies can reorder selected environments but do not silently add unselected environments to the run.
- The environment variable view from `tox config -k set_env pass_env` matches command execution: variables selected by `pass_env`, removed by `disallow_pass_env`, overridden by `set_env`, and injected by tox are the variables commands receive.
- A selected package mode determines both the package artifact built and the packaging environment used; run environments observe the result through package installation and `TOX_PACKAGE`, not by inheriting package-environment settings.
- Positional arguments after `--` are visible only through positional substitutions or the explicit command passed to `tox exec`; they do not change unrelated configuration keys.
- Labels, factors, and generated environment names are consistent across `tox list`, `tox run -m`, `tox run -f`, and substitution expressions such as `factor.NAME` or `{factor:label}`.
- Unused or misplaced configuration keys remain visible as unused in configuration views and warnings; tox does not silently reinterpret them in another section.
- The final process status agrees with the per-environment report: a success status requires all required selected environments to succeed, while failed, skipped, or ignored outcomes are reflected according to their documented configuration.

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

Running `tox` creates or reuses the `3.13`, `3.12`, and `lint` environments in the configured order. The Python environments inherit dependencies and commands from `env_run_base`; `lint` overrides the command and skips project installation. `tox run -e 3.13 -- -v` passes `-v` to pytest through the positional replacement. `tox list` shows all configured environments with descriptions. `tox config -e 3.13 -k deps commands --format json` shows the resolved values a tool can consume programmatically. `tox exec -e 3.13 -- python -c "import sys; print(sys.executable)"` runs only that one command inside the environment without executing the configured pytest command phase.

For coverage aggregation, define test environments and a `coverage` environment with `depends = ["3.*"]`. Selecting `tox run -e 3.13,3.12,coverage` runs the selected test environments before coverage. Selecting only `tox run -e coverage` does not automatically add the test environments; dependencies order and gate selected environments but do not expand the selection.

For a plugin, install a package that declares a `tox` entry point and implements hooks decorated with `tox.plugin.impl`. A hook can add a config key in `tox_add_env_config`, observe package installation in `tox_on_install`, and summarize command outcomes in `tox_after_run_commands`. A project-local `toxfile.py` can define the same hooks without packaging a separate plugin.

## Non-Goals

This specification does not require reproducing tox's private module layout, private helper functions, exact source classes, or internal cache file implementation.

It does not require matching terminal colors, progress spinner frames, debug timestamps, or exact prose of non-error log lines beyond the documented behavior and machine-readable output contracts.

It does not require real network access to public package indexes. Dependency installation behavior may be tested with local packages, local indexes, skipped installs, or mocked executors.

It does not require implementing a build backend, virtualenv, pip, or Python interpreter discovery from scratch. tox may delegate those responsibilities to installed tools or controlled test doubles while preserving tox's documented decisions around configuration, selection, invocation, and reporting.

It does not require supporting undocumented private imports, test-only fixtures, or project-maintainer onboarding material as public user API.

## Evaluation Notes

Evaluation exercises the behavior described here through public imports, CLI invocations, configuration files, plugin hooks, and observable filesystem/output state. Tests may compare the same project through several public views, such as `tox list`, `tox config`, a run result, log files, and generated schema output.

Scoring focuses on user-visible contracts: configuration discovery and precedence, environment generation and selection, substitution and conditional evaluation, environment variable composition, package-mode effects, command execution outcomes, skip/fail behavior, plugin hook calls, and consistency between resolved configuration and actual runs.

Tests should not require private tox modules or hidden fixture shapes. They may use temporary projects, local files, local packages, and controlled subprocess commands to make outcomes deterministic. Exact stdout formatting is relevant only where tox documents a machine-readable format, a stable CLI option, an error condition, or a user-facing status distinction.

