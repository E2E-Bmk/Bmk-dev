# Copier Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`copier` is a project-templating tool with a `copier` CLI entry point. It renders project templates into destination project trees. A template is a directory, often a Git repository, that may contain a `copier.yml` or `copier.yaml` configuration file, Jinja-rendered file contents, Jinja-rendered path names, questions for the user, and optional lifecycle commands.

Two broad workflows are in scope:

- Generate a new project from a local template path, a Git URL, or a shortcut URL that expands to a hosted repository.
- Keep an existing generated project aligned with an evolving Git-versioned template by replaying the previous answers and applying template changes.

Template execution is treated as potentially dangerous. Jinja extensions, tasks, migrations, and external data outside the project root require explicit trust through the API, CLI, or user settings.

## Non-Goals

- This specification does not require Compatibility with deprecated internal module import paths.
- This specification does not require Prescribing internal class layout, caching strategy, subprocess implementation, prompt toolkit integration, or Git command implementation.
- This specification does not require Network access in tests; local paths and local Git repositories are sufficient to exercise the documented behavior.
- This specification does not require Exact terminal colors, emoji rendering, progress wording, or full snapshot matching of help text.
- This specification does not require Reproducing private test helpers, private attributes, or internal metadata structures beyond the documented answers file or public template variables.
- This specification does not require Template features that depend on third-party extensionsunless those extensions are installed and explicitly trusted.

## Representative Workflows

### Create and Update a Git-Versioned Project

Create a template repository with this structure:

```text
template/
  copier.yml
  {{ project_name }}/__init__.py.jinja
  {{ _copier_conf.answers_file }}.jinja
```

Configure questions and the answers file:

```yaml
# copier.yml
project_name:
  type: str
  default: demo
  help: Project package name

_min_copier_version: "9.0.0"
_skip_if_exists:
  - "local-secrets.yml"
```

```yaml
# {{ _copier_conf.answers_file }}.jinja
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers|to_nice_yaml -}}
```

Generate a project:

```python
from copier import run_copy

run_copy(
    "path/to/template",
    "path/to/project",
    data={"project_name": "billing"},
    defaults=True,
)
```

The destination contains the rendered package path and `.copier-answers.yml` with the template source metadata and `project_name: billing`. After the template repository receives a newer PEP 440 tag, update the project:

```python
from copier import run_update

run_update("path/to/project", defaults=True, conflict="inline")
```

Copier reads the recorded template source and answers, renders the new template version, preserves compatible project edits, and writes inline conflict markers if a project edit and template edit cannot be merged automatically.

### Check Updates from Automation

```shell
copier check-update --output-format json path/to/project
copier check-update --quiet path/to/project
```

JSON output is for reporting. Quiet mode is for scripts: exit code `2` means a newer template version is available, and exit code `0` means no update is available.

## CLI and API Copy Operations

The copy, recopy, and update operations control how templates are rendered and how projects evolve over time.

**Copy operation.** `copier copy TEMPLATE_SRC DESTINATION_PATH` generates a new destination project. Through the API, `run_copy` accepts `src_path` and `dst_path`. When `defaults=True`, prompting is suppressed and available defaults are used. When `data` is supplied, those answers take precedence over prompted answers, previous answers, user settings defaults, and template defaults. When `overwrite=True`, existing files are replaced. When `force=True`, the operation implies both defaults and overwrite.

**Recopy operation.** `copier recopy` reapplies the original template recorded in the destination answers file. It ignores project evolution since the last execution and behaves like a fresh copy over the existing project while reusing the recorded source and answers. Through the API, `run_recopy` accepts the destination path and reads the template source from the answers file. `skip_answered=True` must keep previously recorded answers without asking those questions again.

**Update operation.** `copier update` updates an existing generated project from its recorded template source and last answers. The destination should contain a valid answers file with template source metadata. When `vcs_ref` is supplied, the operation targets that template version. `conflict="inline"` writes unresolved update hunks with conflict markers. `conflict="rej"` writes unresolved hunks to `.rej` files. `context_lines` controls surrounding lines for conflict detection. Through the API, `run_update` accepts the destination path.

**Check-update operation.** `copier check-update` reports whether the project can move to a newer template version. In JSON mode (`--output-format json`), the result object must contain `update_available`, `current_version`, and `latest_version`. In quiet mode (`--quiet`), exit code `2` must mean an update is available and exit code `0` must mean no update.

**Pretend mode.** `pretend=True` or `--pretend` must compute the requested operation without changing the destination tree or answers file.

**Quiet mode.** `quiet=True` or `--quiet` must suppress status and template messages but must not change rendering, answer precedence, or update decisions.

## Template Configuration and Questions

The root of a template may contain `copier.yml` or `copier.yaml`. When both are present, Copier must raise `MultipleConfigFilesError`.

**Settings and questions.** Configuration entries whose keys begin with `_` are settings. Entries whose keys do not begin with `_` are questions. Answers precedence from highest to lowest is: CLI/API `data`, interactive prompting, answers from the last Copier execution, template defaults, and user defaults.

**Question types.** The `type` field accepts `bool`, `float`, `int`, `json`, `path`, `str`, or `yaml`; `yaml` is the default. When `data` supplies a string value for a typed question, the value must be parsed according to the question type.

**Conditional questions.** The `when` field controls whether a question is asked. A skipped question must not be recorded in the answers file, but its default must remain available in the render context for template rendering.

**Secret questions.** When `secret` is true or the question name appears in `secret_questions`, the answer may affect rendering during the current operation but must not be recorded in `_copier_answers` or the answers file.

**Choices.** The `choices` field defines selectable options. Choice values may differ from labels. When `multiselect` is true, the answer must be a list of selected choice values.

**Minimum version.** `_min_copier_version` specifies a PEP 440 minimum Copier version. When the installed version does not satisfy it, `UnsupportedVersionError` must be raised.

**Environment options.** `_envops` configures the Jinja environment (e.g., custom delimiters like `variable_start_string` and `variable_end_string`). Changes must affect how template files are rendered.

**Subdirectory.** `_subdirectory` selects a template subdirectory as the template root. Only files from that subdirectory must be copied to the destination.

**Exclusion patterns.** `_exclude` defines gitignore-style patterns evaluated against destination paths. Matching files must not be rendered or copied. CLI/API `exclude` values extend template/default values.

**Skip-if-exists patterns.** `_skip_if_exists` defines patterns for files that are skipped only when already present. Missing matching files must be recreated during update.

## Rendering and Template Variables

Copier copies every file and directory from the active template root into the destination unless an exclusion matches it.

**Template suffix.** File contents are rendered with Jinja only when the source path ends with the configured template suffix, `.jinja` by default. The rendered destination path drops that suffix. When `templates_suffix` is empty, Copier must attempt to render every file except default exclusions.

**Template variables.** These variables must be available in template rendering: `_copier_answers` (answers for future updates), `_copier_conf` (JSON-serializable runtime configuration exposing `answers_file`, `dst_path`, `src_path`, and other settings), `_copier_python` (absolute path to the Python interpreter running Copier), `_copier_phase` (one of `"prompt"`, `"tasks"`, `"migrate"`, `"render"`, or `"undefined"`), `_copier_operation` (`"copy"` or `"update"`), and `_folder_name` (destination project root directory name).

**Answers file.** The default answers file is `.copier-answers.yml`. Templates that support updates should include a rendered answers file template. The answers file stores Copier metadata under underscore-prefixed keys and question answers under their question names. When `answers_file` is supplied via API or CLI, that path must override the template default.

**Jinja filters and functions.** Copier provides Jinja2 plus filters from `jinja2-ansible-filters`. The `to_nice_yaml` filter must serialize values as YAML. The `to_json` filter must serialize values as JSON.

## Tasks and Unsafe Features

Tasks and migrations are template-defined commands that run during copy or update operations.

**Tasks.** `_tasks` defines commands run after copy or update, in declaration order, with `STAGE=task`. Tasks are unsafe unless trusted.

**Unsafe template detection.** Custom Jinja extensions, tasks, and migrations are unsafe features. When a template uses unsafe features and the run is not trusted, `UnsafeTemplateError` must be raised; the CLI must exit with code `4`.

**Trust control.** A run is trusted when `unsafe=True`, `--trust`, `--UNSAFE`, or user settings mark the template as trusted. `skip_tasks=True` avoids normal task execution but does not trust the template and does not skip migrations.

**Cleanup on error.** `cleanup_on_error=True` (default for copy) must delete a destination directory only when Copier created that directory during a failed copy operation. `--no-cleanup` must preserve the destination after failure.

## Settings and User Configuration

`load_settings` reads user settings from a YAML file at the platform-specific configuration path or from `COPIER_SETTINGS_PATH`.

**Settings loading.** When `COPIER_SETTINGS_PATH` names a missing file, Copier must warn with `MissingSettingsWarning` and return empty settings. Invalid YAML or invalid settings structure must raise `SettingsError`. A missing default settings path must produce an empty `Settings`.

**Settings container.** `Settings` is a frozen container with `defaults` (reusable default answers) and `trust` (trusted template repositories or prefixes). `Settings()` must produce isolated instances with empty defaults and trust. `Settings.defaults` must override template question defaults for unanswered questions during defaults-mode operations.

**Phase management.** `Phase` exposes string values `"prompt"`, `"tasks"`, `"migrate"`, `"render"`, and `"undefined"`. `Phase.current()` must return the current execution phase. `Phase.use(phase)` must temporarily set the phase for a block and restore the previous phase on exit.

**VcsRef.** `VcsRef.CURRENT` has value `":current:"` and selects the template ref already recorded for the project.

## State Model

A Copier project has one template source and revision, one resolved answer set, one destination tree, one answers-file projection, and one update history. The Python API and CLI operate on these same public projections.

- Values selected from defaults, settings, data files, and direct data must agree in rendered paths, rendered contents, task context, and the recorded answers file.
- Recopy and update must read the same recorded template source and answers that a prior copy wrote, unless the caller supplies a documented override.
- Pretend mode must compute the requested operation without changing the destination tree or answers file.
- Trust decisions must apply consistently to tasks, migrations, Jinja extensions, and external data from both CLI and Python entry points.

## Error Semantics

All Copier-specific exceptions inherit from `CopierError` unless they are warnings. `UserMessageError` carries a user-facing message; the CLI prints it and exits with code `1`.

- `UnsupportedVersionError`: the template requires a Copier version that the installed package does not satisfy.
- `ConfigFileError`: base class for configuration file problems.
- `InvalidConfigFileError`: the template configuration file is syntactically or structurally invalid.
- `MultipleConfigFilesError`: both `copier.yml` and `copier.yaml` exist for one template root.
- `InvalidTypeError`: a question declares an unsupported type.
- `PathError`: base class for invalid path usage.
- `PathNotAbsoluteError`: a value required to be absolute is relative.
- `PathNotRelativeError`: a value required to be relative is absolute.
- `ForbiddenPathError`: rendering or external data would access a forbidden path.
- `ExtensionNotFoundError`: a configured Jinja extension cannot be imported.
- `CopierAnswersInterrupt`: interactive prompting was interrupted and partial answers are available on the exception.
- `UnsafeTemplateError`: unsafe features were detected without trust.
- `YieldTagInFileError`: a yield tag appears in file content rather than a path name.
- `MultipleYieldTagsError`: a path name contains more than one yield tag.
- `TaskError`: a task command exits nonzero; it behaves like `subprocess.CalledProcessError` and includes the command, return code, stdout, and stderr.
- `InteractiveSessionError`: input would require an interactive session but none is available.
- `SettingsError`: `load_settings` could not parse or validate settings.

Warnings:

- `CopierWarning`: base warning class.
- `UnknownCopierVersionWarning`: Copier cannot determine its installed version.
- `OldTemplateWarning`: the template was designed for an older Copier version.
- `DirtyLocalWarning`: a local template has uncommitted changes or untracked files.
- `ShallowCloneWarning`: a template repository clone is shallow.
- `MissingSettingsWarning`: `COPIER_SETTINGS_PATH` points to a missing file.
- `MissingFileWarning`: an optional expected file could not be found.

## Cross-View Invariants

1. A successful API copy and a successful CLI copy with equivalent options must produce the same destination files, answers file, and recorded template metadata.
2. An answer supplied through API `data` or CLI `--data` must be visible in template rendering, must suppress prompting for that question unless `ask` matches it, and must take precedence over `--data-file`, previous answers, user defaults, and template defaults.
3. The answers file path used for rendering, recording, recopy, update, and check-update must be the same relative path selected by `answers_file` or the template default.
4. A question marked secret, or listed in `secret_questions`, may affect rendering during the current operation but must not be recorded in `_copier_answers` or the answers file.
5. `exclude` must prevent matching paths from being rendered at all, while `skip_if_exists` must only preserve matching paths that already exist and must recreate missing matching paths on update.
6. `pretend=True` and `--pretend` must preserve the same decision-making behavior as a real run while leaving destination files unchanged.
7. `quiet=True` and `--quiet` must suppress status and template messages but must not change rendering, answer precedence, unsafe checks, or update decisions.
8. Unsafe features must be allowed or rejected consistently across API and CLI according to explicit trust, user settings trust, and the presence of unsafe template configuration.
9. `VcsRef.CURRENT` and CLI `--vcs-ref=:current:` must both keep the recorded template ref instead of selecting the latest tag.
10. `copier check-update --output-format json` must report the same update decision that quiet mode encodes as exit status `2` for update available and `0` for no update.

## Public Interface

### Import Surface

Python callers import the primary API from `copier`:

```python
from copier import (
    Phase,
    Settings,
    VcsRef,
    load_settings,
    run_copy,
    run_recopy,
    run_update,
)
```

The documented exception and warning namespace is `copier.errors`. It exports:

```python
from copier.errors import (
    CopierAnswersInterrupt,
    CopierError,
    CopierWarning,
    ConfigFileError,
    DirtyLocalWarning,
    ExtensionNotFoundError,
    ForbiddenPathError,
    InteractiveSessionError,
    InvalidConfigFileError,
    InvalidTypeError,
    MissingFileWarning,
    MissingSettingsWarning,
    MultipleConfigFilesError,
    MultipleYieldTagsError,
    OldTemplateWarning,
    PathError,
    PathNotAbsoluteError,
    PathNotRelativeError,
    ShallowCloneWarning,
    TaskError,
    UnknownCopierVersionWarning,
    UnsafeTemplateError,
    UnsupportedVersionError,
    UserMessageError,
    YieldTagInFileError,
)
```

`load_settings()` may raise `copier.errors.SettingsError` for invalid settings data.

The console script is named `copier`. The same commands must be available through `python -m copier`; module invocation is a public CLI entry point and must have the same observable exit status and filesystem effects as the `copier` console script.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `run_copy` | function | Generate a destination project from a template source |
| `run_recopy` | function | Reapply the original template recorded in the destination answers file |
| `run_update` | function | Update an existing generated project from its recorded template source |
| `load_settings` | function | Load user settings from the configured settings path |
| `Settings` | class | Frozen settings container for default answers and trusted template sources |
| `Phase` | enum | Current execution phase values for template rendering and lifecycle |
| `VcsRef` | enum | Special template reference sentinel for keeping the recorded ref |
| `Phase.current` | method | Return the current execution phase |
| `Phase.use` | context manager | Temporarily set the execution phase for a block |
| `VcsRef.CURRENT` | constant | Sentinel value that selects the template ref already recorded for the project |

### CLI Entry Points

The console command is `copier`, with covered `copy`, `recopy`, `update`, and `check-update` operations. Successful copy, recopy, and update operations must return status 0. Configuration errors, unsafe operations without trust, unsupported template versions, and generation failures must return a nonzero status; unsafe-feature refusal uses status 4.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers copy, recopy, update, settings, rendering, answer persistence, trust decisions, error conditions, and CLI/API agreement. It observes returned paths, destination files, answers files, command output modes, exceptions, and exit statuses. Private worker classes, filesystem staging, VCS-helper layout, exact progress wording, fixture-specific shapes, and source organization are not part of this contract.
