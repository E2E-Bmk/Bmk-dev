# pre-commit Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

pre-commit is a framework for managing and running Git hook checks from a repository configuration file. A project declares hook repositories and hook ids in `.pre-commit-config.yaml`; pre-commit validates that configuration, prepares any required hook environments, installs Git hook scripts, selects files from the Git working tree, and runs the configured hooks with predictable exit-code and output behavior.

The central state is shared across several public views:

- YAML configuration files in the working tree;
- hook manifests supplied by hook repositories;
- the Git repository and its staged, changed, or all-file views;
- installed scripts under `.git/hooks`;
- a persistent pre-commit cache/store;
- command-line output and exit codes.

## Non-Goals

- Full reproduction of every external language environment backend is excluded; bounded local languages cover the specified hook execution surface.
- Remote repository transport behavior is excluded beyond observable configuration and cache effects.
- Exact terminal column widths, color escape-byte choices, and long human help text are not part of the contract unless they affect documented behavior.
- Project development helpers outside the installed `pre_commit` package are not runtime API.
- Private helper functions and underscored modules are not public API.
- Hosted CI service integration is excluded from local hook execution.

## Representative Workflows

### Configure, Install, And Run Local Hooks

A repository contains `.pre-commit-config.yaml` with a local hook:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-debug
        name: check for debug statements
        entry: grep -rn "import pdb"
        language: system
        types: [python]
```

Validation, installation, and execution use the CLI:

```console
$ pre-commit validate-config .pre-commit-config.yaml
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
$ pre-commit run --all-files
check for debug statements..............................................Passed
```

`validate-config` confirms the YAML is well-formed, `install` writes the Git hook script, and `run --all-files` resolves the local hook, selects matching Python files, and returns zero when the hook passes without modifying files.

### Define And Consume A Hook Manifest

A hook repository declares `.pre-commit-hooks.yaml`:

```yaml
- id: trailing-whitespace
  name: trim trailing whitespace
  entry: trailing-whitespace-fixer
  language: system
  types: [text]
```

A consumer config references that repository:

```yaml
repos:
  - repo: https://github.com/example/hooks
    rev: v1.0.0
    hooks:
      - id: trailing-whitespace
        args: ["--fix"]
```

```console
$ pre-commit validate-manifest .pre-commit-hooks.yaml
$ pre-commit run trailing-whitespace --all-files
trim trailing whitespace.................................................Passed
```

`validate-manifest` checks that required fields (`id`, `name`, `entry`, `language`) are present. Hook resolution merges manifest defaults with consumer overrides (here, extra `args`), and the runner invokes the entry command with the configured arguments and selected filenames.

## Command Line Interface

This section defines how the `pre-commit` command-line tool dispatches subcommands and interprets common flags.

**Subcommand dispatch.** `pre-commit` with no subcommand must behave like `pre-commit run`. The supported subcommands are `run`, `install`, `uninstall`, `install-hooks`, `init-templatedir`, `validate-config`, `validate-manifest`, `sample-config`, `migrate-config`, `clean`, `gc`, `autoupdate`, `try-repo`, and `help`.

**Common flags.** `--config` must select a configuration file, defaulting to `.pre-commit-config.yaml`, for commands that operate on a project configuration. `--color` must accept `auto`, `always`, and `never` for most user-facing commands.

**Git root resolution.** Commands that operate on a repository must first resolve the Git root and interpret relative paths from that root. Commands such as `clean`, `gc`, `sample-config`, `validate-config`, and `validate-manifest` must not require the current directory to be inside a Git repository.

**Help.** `pre-commit help` must print usage information containing "usage: pre-commit" and exit with code zero. `pre-commit help COMMAND` must print command-specific usage containing "usage: pre-commit COMMAND" and exit with code zero.

**Version.** `pre-commit --version` must print output beginning with "pre-commit " and exit with code zero. The package must also be invocable as `python -m pre_commit`, which must behave identically for `--version` and all other subcommands.

## Configuration and Manifest

This section defines the YAML structure and field semantics for project configuration files and hook manifest files.

**Project configuration structure.** `.pre-commit-config.yaml` must contain a mapping at the document root with a required `repos` key. The `repos` value must be a list. A YAML sequence at the document root must fail validation. A non-list value for `repos` (such as a mapping) must fail validation.

**Top-level configuration keys.** Beyond `repos`, the configuration must accept the following optional keys: `default_install_hook_types` specifies hook types installed when no `--hook-type` flag is supplied, defaulting to `["pre-commit"]`; `default_language_version` maps language names to default version strings for hooks that use `language_version: default`; `default_stages` specifies stages used by hooks that do not set `stages`, defaulting to all supported hook types; `files` and `exclude` are global include and exclude regular expressions; `fail_fast` stops hook execution after the first failing hook when true; `minimum_pre_commit_version` specifies the minimum compatible pre-commit version; and `ci` is an optional mapping accepted but not interpreted by local hook execution.

**Repository and hook entries.** Each entry in `repos` must contain a `repo` value (a Git URL or path, or one of the sentinel values `local` or `meta`) and a `hooks` key whose value must be a list of hook mappings. A mapping value for `hooks` instead of a list must fail validation. Normal repositories (non-local, non-meta) must include `rev`; `local` and `meta` repositories must not use `rev`. A normal repository without `rev` must fail validation, and a `local` repository with `rev` must fail validation. A configuration may contain multiple repository entries, including multiple `local` repositories, each with multiple hooks. Hook mappings must support `id`, `alias`, `name`, `entry`, `language`, `language_version`, `files`, `exclude`, `types`, `types_or`, `exclude_types`, `args`, `stages`, `additional_dependencies`, `always_run`, `fail_fast`, `pass_filenames`, `require_serial`, `verbose`, `log_file`, `description`, and `minimum_pre_commit_version`. When a consumer config specifies any of these fields, the value must override the manifest default during hook resolution.

**Stage semantics.** Supported hook types are `commit-msg`, `post-checkout`, `post-commit`, `post-merge`, `post-rewrite`, `pre-commit`, `pre-merge-commit`, `pre-push`, `pre-rebase`, and `prepare-commit-msg`. Supported stages are the hook types plus `manual`. Legacy stage names must be normalized: `commit` to `pre-commit`, `merge-commit` to `pre-merge-commit`, `push` to `pre-push`. Both legacy and current stage names must be accepted in the same `stages` list. `default_install_hook_types` must accept only supported hook types; since `manual` is a stage but not a hook type, specifying `manual` as a default install hook type must fail validation. `default_stages` must accept all supported stages including `manual`; an unknown stage name must fail validation.

**Meta hooks.** When `repo` is `meta`, pre-commit must expose built-in meta hooks including `identity`, `check-hooks-apply`, and `check-useless-excludes`. An unknown meta hook id must fail validation. Meta hooks must not allow overriding their fixed `entry` behavior — specifying an `entry` override for a meta hook must fail validation. Meta hooks cannot override their fixed entry behavior.

**Hook manifest structure.** `.pre-commit-hooks.yaml` must contain a list of hook definitions at the document root. A mapping at the root must fail validation. A manifest file may contain multiple hook definitions. Each hook definition must include `id`, `name`, `entry`, and `language`; a manifest entry missing any required field must fail validation. Optional manifest fields include `alias`, `files`, `exclude`, `types`, `types_or`, `exclude_types`, `additional_dependencies`, `args`, `always_run`, `fail_fast`, `pass_filenames`, `description`, `language_version`, `log_file`, `require_serial`, `stages`, `verbose`, and `minimum_pre_commit_version`.

**Validation constraints.** `files` and `exclude` fields are regular expressions, not glob patterns; an invalid regular expression must fail validation. Suspicious glob-like strings must produce warnings but must still validate when they are valid regexes. Unknown type tags in `types`, `types_or`, or `exclude_types` must fail validation. Unknown keys at the root, repository, or hook level must produce warnings but must not prevent validation from succeeding. When `minimum_pre_commit_version` specifies a version greater than the installed pre-commit version, validation must fail; a satisfied version constraint must pass.

## Hook Resolution

This section defines how configured hooks are resolved into executable hook objects.

**Resolution by repository type.** When hooks are resolved from a loaded configuration, each repository entry must produce hook objects used by runners. When `repo` is `local`, hooks must run from the current working tree for languages that need no managed environment, or from a local store entry when dependencies require a managed environment. When `repo` is `meta`, hooks must use pre-commit's built-in meta hook definitions. For normal repositories, the hook manifest from the cached checkout must be read, manifest defaults must be merged with config overrides, and a requested hook id absent from the manifest must produce an error.

**Language version resolution.** When a hook specifies `language_version` as `default`, that value must first resolve through the config-level `default_language_version` mapping. If it remains `default` after that lookup, the language backend's own default version must be used.

**Stage inheritance.** Hooks with empty `stages` must inherit `default_stages` from the configuration. When `default_stages` is not set, hooks with empty `stages` must be eligible for all supported hook types.

## Store and Cache

This section defines how pre-commit manages its persistent cache of hook repository checkouts and configuration state.

**Store directory selection.** The store directory must be selected by checking, in order: the `PRE_COMMIT_HOME` environment variable when set; `XDG_CACHE_HOME/pre-commit` when `XDG_CACHE_HOME` is set; then `~/.cache/pre-commit`. The store must create its directory when needed and must write a README.

**Store creation and reuse.** Running hooks must create the store directory if it does not already exist. The store must maintain a SQLite database for cached repositories and configuration usage. Repository cache entries must be keyed by repository identity, revision, and additional dependencies. A cached entry for a given key tuple must be reused by later hook resolution for the same tuple, so running hooks twice with the same configuration must not duplicate cache entries.

**Clean.** `pre-commit clean` must remove the store directory entirely and return zero. When the store directory does not exist, `clean` must still return zero without error.

**Garbage collection.** `pre-commit gc` must remove cached repositories not referenced by remembered configuration files. It must preserve the store directory itself and must return zero.

## Installing Git Hooks

This section defines how pre-commit writes and removes hook scripts in a Git repository's `.git/hooks` directory.

**Install.** `pre-commit install` must write hook scripts into `.git/hooks` for each selected hook type. When no `--hook-type` is supplied, `default_install_hook_types` from the configuration must control which hook types are installed. When multiple `--hook-type` flags are supplied, each specified hook type must receive a hook script. The installed script must dispatch to `pre-commit hook-impl` and must contain references to both the hook type name and the `hook-impl` dispatch mechanism.

**Legacy hook preservation.** When an existing non-pre-commit hook file is present, installation must preserve it as a legacy hook unless `--overwrite` is requested. When the installed file is already a pre-commit script, reinstalling must be idempotent. `--overwrite` must replace the existing hook entirely and must discard any legacy hook, so uninstalling after an overwrite must remove the hook file completely rather than restoring a legacy hook.

**Uninstall.** `pre-commit uninstall` must remove pre-commit-managed hook scripts for the selected hook types. When a legacy hook was preserved during installation (without `--overwrite`), uninstalling must restore the original legacy hook content.

**Template directory.** `pre-commit init-templatedir DIRECTORY` must write hook scripts into the specified template directory for the selected `--hook-type`, so future Git repositories created from that template contain pre-commit hook scripts. The hook script must contain the `hook-impl` dispatch mechanism.

**Allow missing config.** `--allow-missing-config` must allow installed hook scripts to skip cleanly when a configuration file is absent at runtime.

**Hooks path conflict.** Installing hooks must refuse to proceed when Git `core.hooksPath` is set unless a concrete git directory is explicitly supplied by the caller-level command path.

## Running Hooks

This section defines how `pre-commit run` selects and executes hooks.

**Hook selection.** `pre-commit run` must select hooks from the loaded configuration whose `id` or `alias` matches the optional `HOOK` argument and whose `stages` include the selected `--hook-stage`. When a specific hook id is provided as the `HOOK` argument, only that hook must run. Hooks configured for `manual` stage must not run during a default (non-manual) run; they must run only when `--hook-stage manual` is explicitly supplied.

**File selection.** When `--all-files` is supplied, hooks must receive all tracked files. When `--files FILE ...` is supplied, hooks must receive only the explicitly listed files. When `--from-ref` and `--to-ref` are both supplied, hooks must receive files changed between the two refs; these flags must be supplied together. During normal pre-commit hook execution without explicit files, hooks must receive staged files and pre-commit must temporarily hide unstaged changes.

**File filtering.** Global `files` and `exclude` filters must apply before hook-level filters, so a file excluded by the global `exclude` pattern must not be passed to any hook even if the hook's own `files` pattern would match it. Similarly, the global `files` include pattern must restrict which files reach hooks — only files matching the global pattern may proceed to hook-level filtering. Hook-level `files`, `exclude`, `types`, `types_or`, and `exclude_types` must further filter files for each hook. A hook whose file filter matches no tracked files must be skipped silently unless `always_run` is true.

**Always run and pass filenames.** When `always_run` is true, a hook must execute even when no files match its filter. When `pass_filenames` is false, the hook must run without filename arguments in its command; the entry message must appear in output but selected filenames must not.

**Execution.** Hook command arguments must be built from `entry`, hook `args`, and selected filenames. `PRE_COMMIT=1` must be set during hook execution. Push, rebase, checkout, merge, commit-message, and rewrite hook stages must expose their stage-specific values through documented `PRE_COMMIT_*` environment variables.

**Skip environment.** The `SKIP` environment variable may contain comma-separated hook ids or aliases. When a hook's `id` or `alias` appears in `SKIP`, that hook must be skipped and the overall run must pass for that hook.

**Hook failure.** A hook must be considered failed when its process exits nonzero or when it modifies files. Failing hooks must show their hook id, exit code, output, and modification status. Passing hooks must normally suppress hook output unless `verbose` is true. When `log_file` is set, hook output must be written to that file when a hook fails or when `verbose` is true.

**Fail fast.** When `fail_fast` is true at the config level, hook execution must stop after the first failing hook and must not run subsequent hooks. When `fail_fast` is true at the hook level, that hook's failure must prevent later hooks from running. In both cases, hooks after the first failure must not appear in output.

## Bounded Local Languages

This section defines the local language backends that execute hooks without requiring external package managers or network services.

**System and script languages.** `language: system` and `language: script` must be accepted for historical configurations. Languages without managed environments must run hooks from the current working tree prefix. Other language backends may be present in the package, but full environment creation for every supported language is outside this scope.

**Fail language.** `language: fail` must cause the hook to return failure unconditionally. The configured `entry` text and matching filenames must appear in the output. This language is useful for deliberately blocking commits.

**Pygrep language.** `language: pygrep` must treat the hook `entry` as a Python regular expression. It must return nonzero when the pattern matches any content in the selected files, and must write matching file names, line information, and matched text to output. When no match is found, it must return zero. The `args` field must support `--ignore-case` for case-insensitive matching, `--multiline` for patterns that span multiple lines, and `--negate` to invert the match logic so that the hook passes when the pattern matches and fails when it does not.

**Meta hooks.** `repo: meta` hooks are built-in local hooks and must not require external installation. The `identity` meta hook must resolve and pass when run with matching files.

## Validation and Utility Commands

This section defines validation, sample generation, migration, autoupdate, and try-repo command behaviors.

**Validate config.** `pre-commit validate-config` must validate one or more configuration files and return zero only when all supplied files are valid. When any file among the supplied files is invalid, the command must return nonzero. When no filenames are supplied, the command must validate the default `.pre-commit-config.yaml` in the current directory.

**Validate manifest.** `pre-commit validate-manifest` must validate one or more manifest files and return zero only when all supplied files are valid. When any file is invalid, the command must return nonzero. When no filenames are supplied, the command must validate the default `.pre-commit-hooks.yaml` in the current directory.

**Sample config.** `pre-commit sample-config` must print a minimal `.pre-commit-config.yaml` example to stdout and return zero. The printed output must be valid YAML containing a mapping with a `repos` list that contains at least one entry with a `hooks` list. The output must pass `validate-config` when saved to a file.

**Migrate config.** `pre-commit migrate-config` must rewrite old-format configuration into current format. It must wrap legacy list-style config syntax (a YAML list at the document root) into map-style syntax with a `repos` key. It must rewrite the legacy `sha` key to `rev` in repository mappings. It must normalize legacy stage names (`commit` to `pre-commit`, `push` to `pre-push`, `merge-commit` to `pre-merge-commit`) in both `default_stages` and hook-level `stages`. It must preserve YAML style where possible. It must leave already-current config semantically unchanged — migrating a current-format config must be idempotent with respect to the parsed result. Migrated config must pass validation.

**Autoupdate.** `pre-commit autoupdate` must rewrite hook repository revisions in the config. By default it must select the latest tag; `--bleeding-edge` must select the current HEAD; `--freeze` must write immutable hashes with a human-readable tag comment when available. Network transport details are not part of the local contract.

**Try-repo.** `pre-commit try-repo REPO` must let a user run hooks from a local or remote hook repository without editing the project's config. For local paths, tracked uncommitted changes must be included in the temporary hook repository snapshot. When a specific hook id is supplied as an argument after the repo path, only that hook must run from the repository's manifest.

**Color utilities.** `format_color` must wrap text in terminal color escape sequences when color is enabled and must return plain text when color is disabled. `use_color` must resolve `always`, `never`, and `auto` settings.

**Command execution utilities.** `normalize_cmd` must resolve an executable command using shebangs and PATH; missing executables must raise `ExecutableNotFoundError`. `partition` and `xargs` must split long argument lists into executable command batches and combine return values and output across batches; argument lists exceeding platform command length limits must raise `ArgumentTooLongError`. `cmd_output` and `cmd_output_b` must run subprocesses and return returncode, stdout, and stderr; when configured to check return codes, nonzero exits must raise `CalledProcessError` carrying the command, return code, stdout, and stderr.

## State Model

A pre-commit project has three public projections of the same hook state: YAML configuration and manifests, resolved hooks and cached environments, and command or installed-Git-hook execution. A hook id and stage must resolve consistently in all three views. File selection, skip rules, and hook outcomes must agree between direct runs and installed hook dispatch. Config migration may change serialization but must preserve the resolved hook behavior.

## Error Semantics

- Invalid config files must raise `InvalidConfigError` when loaded through `load_config` and must produce nonzero CLI status through validation commands.
- Invalid manifest files must raise `InvalidManifestError` when loaded through `load_manifest` and must produce nonzero CLI status through validation commands.
- A `minimum_pre_commit_version` greater than the installed pre-commit version must fail validation.
- Unknown type tags must fail validation.
- Missing required config or manifest keys must fail validation.
- Normal repositories require `rev`; `local` and `meta` repositories must not use `rev`. A `local` repository with `rev` must fail validation.
- Meta hooks only allow supported meta hook ids and must not allow overriding fixed entries.
- `run --from-ref` and `--to-ref` must be supplied together.
- `commit-msg` and `prepare-commit-msg` runs require a commit message filename.
- Running from outside a Git repository fails for commands that need repository state.
- Installing hooks refuses to proceed when Git `core.hooksPath` is set unless a concrete git directory is explicitly supplied by the caller-level command path.

## Cross-View Invariants

1. A hook id listed in `.pre-commit-config.yaml` must resolve to either a matching manifest hook, a local hook definition, or a supported meta hook before it can run.
2. The hook script installed in `.git/hooks/<hook-type>` must dispatch the same config file and hook type that `pre-commit install` was asked to install.
3. The hook types selected by `default_install_hook_types` must match the hook scripts installed when `install` is run without explicit hook types.
4. A file excluded by global or hook-level exclude patterns must not be passed to that hook even if Git reports it as staged or changed.
5. A hook with `always_run: true` must run consistently from `run --all-files`, explicit `run HOOK`, and installed Git hook dispatch even when no files match.
6. A repository/ref/dependency tuple cached by `Store` must be reused by later hook resolution for the same tuple.
7. Validation commands and Python loaders must agree on whether a config or manifest is valid; a config that fails `validate-config` must also fail when loaded for `run`.
8. Config migration must preserve the behavior of the config while changing the serialized representation, and the migrated output must pass `validate-config`.
9. Hook execution exit codes, printed status, and file modifications must describe the same hook result.
10. `SKIP` filtering must affect both direct `pre-commit run` and installed hook dispatch.
11. A store directory created during hook execution must be preserved and reusable across subsequent runs, and must be fully removable by `clean`.

## Public Interface

### Import Surface

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

`main` accepts command-line arguments and returns an integer process-style status code. The configuration-loading behavior described above is also available through the public `load_config` helper; implementations may organize that helper and CLI command handlers internally as they choose.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| main | function | CLI entry point; parse argv and return process status |
| load_config | function | Load and validate a project configuration file |
| load_manifest | function | Load and validate a hook manifest file |
| Hook | class | Resolved hook object used by runners |
| Prefix | class | Hook repository checkout or local execution prefix |
| Store | class | Persistent cache for hook repositories and config usage |
| format_color | function | Wrap text in terminal color escape sequences when enabled |
| use_color | function | Resolve color setting among always, never, and auto |
| normalize_cmd | function | Resolve an executable command using shebangs and PATH |
| partition | function | Split long argument lists into executable command batches |
| xargs | function | Run command batches and combine return values and output |
| cmd_output | function | Run a subprocess and return returncode, stdout, and stderr |
| cmd_output_b | function | Run a subprocess and return byte stdout and stderr |
| InvalidConfigError | exception | Raised for invalid project configuration |
| InvalidManifestError | exception | Raised for invalid hook manifest |
| ExecutableNotFoundError | exception | Raised when a required executable is missing |
| ArgumentTooLongError | exception | Raised when arguments exceed platform command limits |
| CalledProcessError | exception | Raised when subprocess execution fails under check mode |

### CLI Entry Points

The `pre-commit` console script and `python -m pre_commit` are supported. Validation, installation, cleanup, migration, sample generation, and successful hook runs return zero; invalid configuration or a failed required hook returns nonzero. The public `main` helper returns the same process-style status.

## Appendix A: Environment

The implementation may use third-party packages available on PyPI. Runtime dependencies must be declared in a standard `requirements.txt` or `pyproject.toml` at the project root and are installed before use. Covered workflows use local Git repositories and local hook definitions and must not require remote network access.

## Appendix B: Assessment Notes

Validation focuses on observable behavior through the public interfaces described above. Checks exercise CLI command dispatch, YAML config and manifest validation, hook resolution, installed hook scripts, Git file selection, store/cache persistence, local hook execution, meta hooks, bounded local languages, utility APIs that affect command behavior, and cross-view consistency among files, Git state, cache state, output, and exit codes.

A correct implementation should preserve behavior across views: configuration loaded through Python helpers should drive the same hooks as the CLI, installed hook scripts should dispatch the same stage and config selected during installation, cache entries should be reused by later hook resolution, and hook output/exit code should match file modifications. Equivalent internal organization is acceptable; private helper names and exact internal database layout are not part of the contract.
