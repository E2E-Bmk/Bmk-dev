# pre-commit Specification

## Product Overview

pre-commit is a framework for managing and running Git hook checks from a repository configuration file. A project declares hook repositories and hook ids in `.pre-commit-config.yaml`; pre-commit validates that configuration, prepares any required hook environments, installs Git hook scripts, selects files from the Git working tree, and runs the configured hooks with predictable exit-code and output behavior.

The central state is shared across several public views:

- YAML configuration files in the working tree;
- hook manifests supplied by hook repositories;
- the Git repository and its staged, changed, or all-file views;
- installed scripts under `.git/hooks`;
- a persistent pre-commit cache/store;
- command-line output and exit codes.

## Scope

This package provides the behavior needed for local pre-commit workflows:

- reading and validating `.pre-commit-config.yaml` and `.pre-commit-hooks.yaml`;
- installing, uninstalling, and dispatching Git hook scripts;
- running hooks for staged files, all files, explicit files, and changed ranges;
- resolving local, meta, and cached hook repositories into hook objects;
- maintaining the pre-commit cache/store;
- executing bounded local hook languages that do not require external services;
- exposing command-line entry points and the documented Python helpers used by those workflows.

## Installable Surface

The installed distribution is named `pre_commit`. It provides a console script:

```text
pre-commit = pre_commit.main:main
```

The package can also be invoked as a module:

```bash
python -m pre_commit
```

Public imports used by the local workflow surface include:

```python
from pre_commit.main import main
```

`main(argv=None)` accepts command-line arguments and returns an integer
process-style status code. The configuration-loading behavior described below
is also available through the public `load_config(path)` helper; implementations
may organize that helper and CLI command handlers internally as they choose.

## Command Line Interface

`pre-commit` with no subcommand behaves like `pre-commit run`.

Common commands:

```text
pre-commit run [HOOK] [--all-files | --files FILE ...] [--hook-stage STAGE]
pre-commit install [--hook-type HOOK_TYPE] [--overwrite] [--install-hooks]
pre-commit uninstall [--hook-type HOOK_TYPE]
pre-commit install-hooks
pre-commit init-templatedir DIRECTORY [--hook-type HOOK_TYPE]
pre-commit validate-config [FILE ...]
pre-commit validate-manifest [FILE ...]
pre-commit sample-config
pre-commit migrate-config
pre-commit clean
pre-commit gc
pre-commit autoupdate [--bleeding-edge] [--freeze] [--repo REPO] [-j JOBS]
pre-commit try-repo REPO [HOOK] [--ref REV] [run options]
pre-commit help [COMMAND]
pre-commit --version
```

`--config` selects a configuration file and defaults to `.pre-commit-config.yaml` for commands that operate on a project configuration. Most user-facing commands support `--color` with `auto`, `always`, and `never`.

Commands that operate on a repository first resolve the Git root, then interpret relative paths from that root. Commands such as `clean`, `gc`, `sample-config`, `validate-config`, and `validate-manifest` do not require the current directory to be inside a Git repository.

## Configuration File

`.pre-commit-config.yaml` contains a mapping with a required `repos` list.

Top-level keys:

- `repos`: a list of repository mappings.
- `default_install_hook_types`: hook types used by `install` when no `--hook-type` is supplied; defaults to `["pre-commit"]`.
- `default_language_version`: mapping from language name to default version for hooks that use `language_version: default`.
- `default_stages`: stages used by hooks that do not set `stages`; defaults to all supported hook types.
- `files`: global include regular expression; defaults to the empty pattern.
- `exclude`: global exclude regular expression; defaults to `^$`.
- `fail_fast`: when true, hook execution stops after the first failing hook.
- `minimum_pre_commit_version`: minimum compatible pre-commit version.
- `ci`: optional mapping for pre-commit.ci configuration; it is accepted but is not interpreted by local hook execution.

Repository mappings have:

- `repo`: a Git URL/path, or one of the sentinel values `local` or `meta`;
- `rev`: required for normal repositories and absent for `local` and `meta`;
- `hooks`: a list of hook mappings.

Hook mappings select a hook id and may override hook fields supplied by the manifest. Important fields are `id`, `alias`, `name`, `entry`, `language`, `language_version`, `files`, `exclude`, `types`, `types_or`, `exclude_types`, `args`, `stages`, `additional_dependencies`, `always_run`, `fail_fast`, `pass_filenames`, `require_serial`, `verbose`, `log_file`, `description`, and `minimum_pre_commit_version`.

Legacy stage names are normalized:

| legacy name | normalized stage |
|---|---|
| `commit` | `pre-commit` |
| `merge-commit` | `pre-merge-commit` |
| `push` | `pre-push` |

Supported hook types are:

```text
commit-msg, post-checkout, post-commit, post-merge, post-rewrite,
pre-commit, pre-merge-commit, pre-push, pre-rebase, prepare-commit-msg
```

Supported stages are the hook types plus `manual`.

`repo: local` defines hooks entirely in the project configuration. `repo: meta` exposes pre-commit's built-in meta hooks, including `identity`, `check-hooks-apply`, and `check-useless-excludes`; meta hooks cannot override their fixed entry behavior.

## Hook Manifest

`.pre-commit-hooks.yaml` is a list of hook definitions supplied by a hook repository.

Each hook definition requires `id`, `name`, `entry`, and `language`. Optional fields have defaults:

- `alias`: `""`
- `files`: `""`
- `exclude`: `^$`
- `types`: `["file"]`
- `types_or`: `[]`
- `exclude_types`: `[]`
- `additional_dependencies`: `[]`
- `args`: `[]`
- `always_run`: `false`
- `fail_fast`: `false`
- `pass_filenames`: `true`
- `description`: `""`
- `language_version`: `default`
- `log_file`: `""`
- `require_serial`: `false`
- `stages`: all configured default stages when empty
- `verbose`: `false`
- `minimum_pre_commit_version`: `"0"`

`load_manifest(filename)` loads and validates a manifest and returns normalized hook dictionaries. `load_config(filename)` loads and validates a project configuration and returns normalized repository dictionaries. Invalid files raise `InvalidManifestError` or `InvalidConfigError`.

Unknown keys do not become part of hook behavior. They produce warnings at the root, repository, or hook level. Regular-expression fields are regexes, not glob patterns; suspicious glob-like strings produce warnings but still validate when they are valid regexes.

## Hook Resolution

`Hook` is the public hook object used by runners. It contains:

```python
Hook(
    src, prefix, id, name, entry, language, alias, files, exclude,
    types, types_or, exclude_types, additional_dependencies, args,
    always_run, fail_fast, pass_filenames, description,
    language_version, log_file, minimum_pre_commit_version,
    require_serial, stages, verbose,
)
```

`Hook.install_key` groups hooks by repository prefix, language, language version, and additional dependencies.

`Prefix(prefix_dir)` represents a hook repository checkout or local execution prefix. `path(*parts)` joins and normalizes paths under that prefix, `exists(*parts)` checks for files under the prefix, and `star(end)` lists prefix entries ending with a suffix.

`all_hooks(config, store)` resolves every configured repository into a tuple of `Hook` objects:

- `repo: local` hooks run from the current working tree when the language needs no environment, or from a local store entry when dependencies require a managed environment.
- `repo: meta` hooks use pre-commit's built-in meta hook definitions.
- normal repositories are cloned or reused from `Store`, read their `.pre-commit-hooks.yaml`, merge manifest defaults with config overrides, and fail if a requested hook id is absent.

Hook-specific `language_version: default` first resolves through `default_language_version`; if it remains `default`, the language backend's default version is used. Hooks with empty `stages` inherit `default_stages`.

## Store And Cache

`Store(directory=None)` manages pre-commit's persistent cache. The default directory is selected as follows:

1. `PRE_COMMIT_HOME`, when set;
2. `XDG_CACHE_HOME/pre-commit`, when `XDG_CACHE_HOME` is set;
3. `~/.cache/pre-commit`.

The store creates its directory when needed, writes a README, and maintains a SQLite database for cached repositories and configuration usage. Repository cache keys include repository identity, revision, and additional dependencies.

`Store.clone(repo, ref, deps=())` returns a path to a cached checkout at the requested ref. It reuses existing cache entries and otherwise initializes a new checkout. `Store.make_local(deps)` returns a cached local hook repository for local hooks that need managed environments. `Store.exclusive_lock()` serializes cache writes. Cleanup commands operate on the same store:

- `clean` removes the pre-commit store directory.
- `gc` removes cached repositories not referenced by remembered configuration files.

## Installing Git Hooks

`pre-commit install` writes hook scripts into `.git/hooks` for the selected hook types. When no hook type is supplied, `default_install_hook_types` controls which hook scripts are installed. The installed script dispatches to `pre-commit hook-impl` with the selected hook type and configuration path.

If an existing hook file is present, installation preserves it as a legacy hook unless overwrite is requested. If the installed file is already a pre-commit script, reinstalling is idempotent. `--overwrite` replaces existing hooks and disables migration behavior. `--allow-missing-config` allows installed hook scripts to skip cleanly when a configuration file is absent.

`pre-commit uninstall` removes pre-commit-managed hook scripts for the selected hook types and restores preserved legacy hooks when present. `pre-commit init-templatedir DIRECTORY` writes hook scripts into a template directory so future Git repositories created from that template contain pre-commit hook scripts.

## Running Hooks

`pre-commit run` selects hooks from the loaded config and executes hooks whose `id` or `alias` matches the optional `HOOK` argument and whose `stages` include the selected `--hook-stage`.

File selection:

- With `--all-files`, hooks receive all tracked files.
- With `--files`, hooks receive the explicit file list.
- With `--from-ref` and `--to-ref`, hooks receive files changed between the two refs.
- During normal pre-commit hook execution without explicit files, hooks receive staged files and pre-commit temporarily hides unstaged changes.
- Global `files` and `exclude` filters apply before hook-level filters.
- Hook `files`, `exclude`, `types`, `types_or`, and `exclude_types` further select files for each hook.
- Hooks with `always_run: true` run even when no files match.
- Hooks with `pass_filenames: false` run without filename arguments.

Execution behavior:

- Hook command arguments are built from `entry`, hook `args`, and selected filenames.
- `SKIP` may contain comma-separated hook ids or aliases to skip.
- `PRE_COMMIT=1` is set during hook execution.
- Push, rebase, checkout, merge, commit-message, and rewrite hook stages expose their stage-specific values through documented `PRE_COMMIT_*` environment variables.
- A hook fails when its process exits nonzero or when it modifies files.
- `fail_fast` at the config level or hook level stops subsequent hook execution after a failure.
- Passing hooks normally suppress hook output unless `verbose` is true.
- Failing hooks show their hook id, exit code, output, and modification status.
- `log_file` receives hook output when a hook fails or when `verbose` is true.

`pre-commit run --hook-stage manual` runs hooks configured for `manual`; no Git hook invokes the `manual` stage automatically.

## Bounded Local Languages

The local reconstruction surface includes hook execution that does not require external package managers or network services.

- `language: system` and `language: script` are accepted for historical configurations as `unsupported` and `unsupported_script`.
- Languages without managed environments run from the current working tree prefix.
- `language: fail` returns failure and prints the configured entry and filenames. It is useful for deliberately blocking commits.
- `language: pygrep` treats `entry` as a Python regular expression. It returns nonzero when a match is found, writes matching file and line information, supports `--ignore-case`, `--multiline`, and `--negate`, and returns zero when no problem is found.
- `repo: meta` hooks are built-in local hooks and do not require external installation.

Other language backends may be present in the package, but full environment creation for every supported language is outside this scope.

## Validation And Utility Behavior

`pre-commit validate-config` validates one or more config files and returns zero only when all supplied files are valid. `pre-commit validate-manifest` does the same for manifest files. With no filenames, these commands validate their default file names.

`pre-commit sample-config` writes a minimal `.pre-commit-config.yaml` example to stdout.

`pre-commit migrate-config` rewrites old list-style config syntax into map-style syntax, updates legacy stage names, preserves YAML style where possible, and leaves already-current config semantically unchanged.

`pre-commit autoupdate` rewrites hook repository revisions in the config. By default it selects the latest tag; `--bleeding-edge` selects the current HEAD; `--freeze` writes immutable hashes with a human-readable tag comment when available. Network transport details are not part of the local contract.

`pre-commit try-repo` lets a user run hooks from a local or remote hook repository without manually editing the project's config. For local paths, tracked uncommitted changes are included in the temporary hook repository snapshot.

`format_color(text, color, use_color_setting)` wraps text in terminal color escape sequences when color is enabled and returns plain text when color is disabled. `use_color(setting)` resolves `always`, `never`, and `auto`.

`normalize_cmd(cmd, env=None)` resolves an executable command using shebangs and PATH. Missing executables raise `ExecutableNotFoundError`.

`partition(cmd, varargs, target_concurrency=...)` and `xargs(cmd, varargs, ...)` split long argument lists into executable command batches and combine return values/output across batches. Argument lists that cannot fit platform command length limits raise `ArgumentTooLongError`.

`cmd_output()` and `cmd_output_b()` run subprocesses and return `(returncode, stdout, stderr)`. When command execution is configured to check return codes, nonzero exits raise `CalledProcessError` carrying the command, return code, stdout, and stderr.

## Error Semantics

- Invalid config files raise `InvalidConfigError` through `load_config()` and produce nonzero CLI status through validation commands.
- Invalid manifest files raise `InvalidManifestError` through `load_manifest()` and produce nonzero CLI status through validation commands.
- A `minimum_pre_commit_version` greater than the installed pre-commit version fails validation.
- Unknown type tags fail validation.
- Missing required config or manifest keys fail validation.
- Normal repositories require `rev`; `local` and `meta` repositories do not use `rev`.
- Meta hooks only allow supported meta hook ids and cannot override fixed entries.
- `run --from-ref` and `--to-ref` must be supplied together.
- `commit-msg` and `prepare-commit-msg` runs require a commit message filename.
- Running from outside a Git repository fails for commands that need repository state.
- Installing hooks refuses to proceed when Git `core.hooksPath` is set unless a concrete git directory is explicitly supplied by the caller-level command path.

## Cross-View Invariants

- A hook id listed in `.pre-commit-config.yaml` must resolve to either a matching manifest hook, a local hook definition, or a supported meta hook before it can run.
- The hook script installed in `.git/hooks/<hook-type>` must dispatch the same config file and hook type that `pre-commit install` was asked to install.
- The hook types selected by `default_install_hook_types` must match the hook scripts installed when `install` is run without explicit hook types.
- A file excluded by global or hook-level exclude patterns must not be passed to that hook even if Git reports it as staged or changed.
- A hook with `always_run: true` must run consistently from `run --all-files`, explicit `run HOOK`, and installed Git hook dispatch even when no files match.
- A repository/ref/dependency tuple cached by `Store` must be reused by later hook resolution for the same tuple.
- Validation commands and Python loaders must agree on whether a config or manifest is valid.
- Config migration must preserve the behavior of the config while changing the serialized representation.
- Hook execution exit codes, printed status, and file modifications must describe the same hook result.
- `SKIP` filtering must affect both direct `pre-commit run` and installed hook dispatch.

## Representative Workflows

### Configure, Install, And Run Local Hooks

1. A repository contains `.pre-commit-config.yaml` with `repo: local` and a hook whose language can run without external environment creation.
2. `pre-commit validate-config` validates the config.
3. `pre-commit install` writes `.git/hooks/pre-commit`.
4. `pre-commit run --all-files` resolves the local hook, selects matching files, runs the hook, and returns zero only when all selected hooks pass and do not modify files.
5. A later `git commit` invokes the installed hook script, which dispatches to the same config and stage.

### Define And Consume A Hook Manifest

1. A hook repository declares `.pre-commit-hooks.yaml`.
2. `pre-commit validate-manifest` validates required fields and defaults.
3. A consumer config references the repository, revision, and hook id.
4. Hook resolution reads the manifest, applies consumer overrides, prepares the store entry, and produces a `Hook` object.
5. The runner invokes the hook entry with configured args and selected filenames.

## Non-Goals

- Exact reproduction of every external language environment backend is not required.
- Network-dependent remote repository transport behavior is outside the local reconstruction surface beyond observable config/cache effects.
- Exact terminal column widths, color escape-byte choices, and long human help text are not part of the contract unless they affect documented behavior.
- Project development helpers outside the installed `pre_commit` package are not runtime API.
- Private helper functions and underscored modules are not public API.
- pre-commit.ci service behavior is not part of local pre-commit execution.

## Evaluation Notes

Validation focuses on observable behavior through the public interfaces described above. Checks exercise CLI command dispatch, YAML config and manifest validation, hook resolution, installed hook scripts, Git file selection, store/cache persistence, local hook execution, meta hooks, bounded local languages, utility APIs that affect command behavior, and cross-view consistency among files, Git state, cache state, output, and exit codes.

A correct implementation should preserve behavior across views: configuration loaded through Python helpers should drive the same hooks as the CLI, installed hook scripts should dispatch the same stage and config selected during installation, cache entries should be reused by later hook resolution, and hook output/exit code should match file modifications. Equivalent internal organization is acceptable; private helper names and exact internal database layout are not part of the contract.
