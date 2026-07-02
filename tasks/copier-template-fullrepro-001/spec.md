<!-- INTERNAL
task_id: copier-template-fullrepro-001
spec_version: v1
delta: Initial Stage 2 behavioral specification. Included the documented top-level Python API, documented copier.errors classes, CLI copy/recopy/update/check-update behavior, template configuration, rendering, answers, update, unsafe-feature, and settings contracts. Omitted deprecated/internal compatibility modules and implementation classes.
source_boundary:
  - G:\research\01_agents\swe-e2e\Bmk-dev\wip\copier-template-fullrepro-001\filter_notes.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\README.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\pyproject.toml
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\docs\reference\api.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\docs\generating.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\docs\updating.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\docs\configuring.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\docs\creating.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\docs\settings.md
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\__init__.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\main.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\settings.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\types.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\errors.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\_main.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\_settings.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\_types.py
  - G:\research\01_agents\swe-e2e\repo-pool\copier-org__copier\copier\_cli.py
  - Local CLI help attempted with `python -m copier --help`; unavailable because this checkout lacks installed dependency `jinja2`.
-->

# Copier Specification

## Product Overview

Copier is a Python library and command-line application for rendering project templates into destination project trees. A template is a directory, often a Git repository, that may contain a `copier.yml` or `copier.yaml` configuration file, Jinja-rendered file contents, Jinja-rendered path names, questions for the user, and optional lifecycle commands.

Copier supports two broad workflows:

- Generate a new project from a local template path, a Git URL, or a shortcut URL such as `gh:namespace/project` or `gl:namespace/project`.
- Keep an existing generated project aligned with an evolving Git-versioned template by replaying the previous answers and applying template changes.

Copier treats template execution as potentially dangerous. Jinja extensions, tasks, migrations, and external data outside the project root require explicit trust through the API, CLI, or user settings.

## Scope

This specification covers:

- The installable `copier` Python package and `copier` CLI command.
- Project generation with `copy` and `run_copy`.
- Project regeneration with `recopy` and `run_recopy`.
- Smart project updates with `update` and `run_update`.
- Update availability checks with `copier check-update`.
- Template configuration through `copier.yml` or `copier.yaml`.
- Answers, answers files, user defaults, trusted repositories, template variables, file rendering, path rendering, exclusions, skips, tasks, migrations, unsafe-feature checks, and documented error classes.

## Installable Surface

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

The console script is named `copier`. It provides these user-facing commands:

- `copier copy TEMPLATE_SRC DESTINATION_PATH`
- `copier recopy [DESTINATION_PATH]`
- `copier update [DESTINATION_PATH]`
- `copier check-update [DESTINATION_PATH]`
- `copier` as a shortcut that copies when a destination is supplied and updates when run inside an existing Copier-generated project with enough answers metadata.

## Public API

### `run_copy`

```python
run_copy(
    src_path: str,
    dst_path: Path | str = ".",
    data: dict[str, Any] | None = None,
    *,
    answers_file: Path | str | None = None,
    vcs_ref: str | VcsRef | None = None,
    settings: Settings | None = None,
    exclude: Sequence[str] = (),
    use_prereleases: bool = False,
    skip_if_exists: Sequence[str] = (),
    cleanup_on_error: bool = True,
    defaults: bool = False,
    user_defaults: dict[str, Any] | None = None,
    overwrite: bool = False,
    pretend: bool = False,
    quiet: bool = False,
    unsafe: bool = False,
    skip_tasks: bool = False,
    ask: Sequence[str] = (),
)
```

`run_copy` generates a destination project from `src_path`. `src_path` may be a local path, a Git URL, or a supported shortcut URL. If `dst_path` does not exist, Copier creates it. If it exists, it must be writable. Existing files are preserved unless `overwrite=True`, an interactive confirmation allows replacement, or the file is the answers file.

`data` supplies initial answers and takes precedence over prompted answers, previous answers, template defaults, and user defaults. `defaults=True` suppresses prompting by using defaults; any required question without a usable default must raise an error instead of silently choosing a value. `ask` contains glob-style question names that must be asked even if `data`, `defaults`, or skip behavior would otherwise bypass them.

`answers_file` is a relative path inside the destination project. If omitted, Copier uses the template setting and then `.copier-answers.yml`. `vcs_ref` selects the Git ref to copy; if omitted for a Git template, Copier chooses the latest PEP 440 release tag and ignores prereleases unless `use_prereleases=True`. `VcsRef.CURRENT` represents `:current:` and is meaningful when reusing the current template ref.

`exclude` extends template or default exclusion patterns. `skip_if_exists` extends template skip patterns. `cleanup_on_error=True` deletes a destination directory only when Copier created that directory during this failed copy operation. `pretend=True` performs the operation without making filesystem changes. `quiet=True` suppresses status and configured messages. `unsafe=True` explicitly allows unsafe template features. `skip_tasks=True` skips template tasks but does not itself trust unsafe features.

### `run_recopy`

```python
run_recopy(
    dst_path: Path | str = ".",
    data: dict[str, Any] | None = None,
    *,
    answers_file: Path | str | None = None,
    vcs_ref: str | VcsRef | None = None,
    settings: Settings | None = None,
    exclude: Sequence[str] = (),
    use_prereleases: bool = False,
    skip_if_exists: Sequence[str] = (),
    cleanup_on_error: bool = True,
    defaults: bool = False,
    user_defaults: dict[str, Any] | None = None,
    overwrite: bool = False,
    pretend: bool = False,
    quiet: bool = False,
    unsafe: bool = False,
    skip_answered: bool = False,
    skip_tasks: bool = False,
    ask: Sequence[str] = (),
)
```

`run_recopy` reapplies the original template recorded in the destination answers file. It keeps answers from the previous Copier execution but ignores project evolution since that execution. It is the recovery-oriented alternative to smart updates: it behaves like a fresh copy over the existing project while reusing the recorded source and answers.

`skip_answered=True` keeps previously recorded answers without asking those questions again, unless a matching `ask` pattern forces a question to be asked. Other parameters have the same meanings as in `run_copy`.

### `run_update`

```python
run_update(
    dst_path: Path | str = ".",
    data: dict[str, Any] | None = None,
    *,
    answers_file: Path | str | None = None,
    vcs_ref: str | VcsRef | None = None,
    settings: Settings | None = None,
    exclude: Sequence[str] = (),
    use_prereleases: bool = False,
    skip_if_exists: Sequence[str] = (),
    cleanup_on_error: bool = True,
    defaults: bool = False,
    user_defaults: dict[str, Any] | None = None,
    overwrite: bool = False,
    pretend: bool = False,
    quiet: bool = False,
    conflict: Literal["inline", "rej"] = "inline",
    context_lines: int = 3,
    unsafe: bool = False,
    skip_answered: bool = False,
    skip_tasks: bool = False,
    ask: Sequence[str] = (),
)
```

`run_update` updates an existing generated project using the source template and last answers recorded in the answers file. The destination should contain a valid answers file with template source metadata. When the destination is a Git project and the answers file records a previous template commit, Copier preserves project evolution by comparing a fresh rendering from the old template version with the current project, then applying that project diff after rendering the new template version.

`conflict="inline"` writes unresolved update hunks into the affected files with conflict markers. `conflict="rej"` writes unresolved hunks to `.rej` files. `context_lines` controls how many surrounding lines are used when detecting update conflicts. `skip_answered=True` keeps recorded answers without prompting, and `VcsRef.CURRENT` updates answers and rendering behavior without changing the template version.

### `Settings` and `load_settings`

```python
@dataclass(frozen=True)
class Settings:
    defaults: Mapping[str, Any] = {}
    trust: Sequence[str] = ()

def load_settings(settings_path: Path | None = None) -> Settings: ...
```

`Settings.defaults` contains reusable default answers keyed by question name. `Settings.trust` contains trusted template repositories or prefixes. Exact trust entries match exactly; entries ending in `/` match repositories or paths with that prefix after normal path or URL normalization.

`load_settings` reads YAML settings. If `settings_path` is omitted, Copier checks the `COPIER_SETTINGS_PATH` environment variable, then the platform-specific configuration path:

- Linux: `$XDG_CONFIG_HOME/copier/settings.yml`, usually `~/.config/copier/settings.yml`
- macOS: `~/Library/Application Support/copier/settings.yml`
- Windows: `%USERPROFILE%\AppData\Local\copier\settings.yml`

Missing default settings produce an empty `Settings`. If `COPIER_SETTINGS_PATH` names a missing file, Copier warns with `MissingSettingsWarning` and returns empty settings. Invalid YAML or invalid settings structure raises `SettingsError`.

### `Phase` and `VcsRef`

`Phase` is a string enum for current Copier execution phase values:

- `Phase.PROMPT`, string value `"prompt"`
- `Phase.TASKS`, string value `"tasks"`
- `Phase.MIGRATE`, string value `"migrate"`
- `Phase.RENDER`, string value `"render"`
- `Phase.UNDEFINED`, string value `"undefined"`

`Phase.current()` returns the current phase. `Phase.use(phase)` is a context manager that sets the phase for the duration of the context and restores the previous phase afterward.

`VcsRef.CURRENT` has value `":current:"`. It selects the template ref already recorded for the project.

## CLI Behavior

Shared CLI options for copy-like commands include:

- `-a, --answers-file PATH`: relative answers file path inside the destination.
- `-x, --exclude PATTERN`: additional gitignore-style exclusion pattern; may be repeated.
- `-r, --vcs-ref REF`: template Git ref; `:current:` maps to `VcsRef.CURRENT`.
- `-n, --pretend`: run without making changes.
- `-s, --skip PATTERN`: skip paths if they already exist; may be repeated.
- `-q, --quiet`: suppress status output.
- `-g, --prereleases`: include prerelease tags when selecting latest template versions.
- `--UNSAFE` or `--trust`: allow unsafe template features for this run.
- `-T, --skip-tasks`: skip normal template tasks.
- `-d, --data NAME=VALUE`: provide an answer; may be repeated. Values are parsed according to the corresponding question type.
- `--data-file PATH`: load answers from a YAML file. Explicit `--data` values take precedence over the file.

`copier copy` accepts `TEMPLATE_SRC DESTINATION_PATH`. It also supports `-C, --no-cleanup`, `-l, --defaults`, `-f, --force`, `-w, --overwrite`, and `--ask PATTERN`. `--force` means defaults plus overwrite for copy and recopy.

`copier recopy` accepts an optional destination path, defaulting to the current directory. It reads the template source from the answers file. It supports `-l, --defaults`, `-f, --force`, `-w, --overwrite`, `-A, --skip-answered`, and `--ask PATTERN`.

`copier update` accepts an optional destination path, defaulting to the current directory. It reads the template source from the answers file and treats overwrite as implicit for the API call. It supports `-l, -f, --defaults`, `-A, --skip-answered`, `--ask PATTERN`, `-o, --conflict {inline,rej}`, and `-c, --context-lines N`.

`copier check-update` accepts an optional destination path. It supports `-a, --answers-file`, `-q, --quiet`, `-g, --prereleases`, and `--output-format {plain,json}`. Plain output says the project is up to date or reports current and latest template versions. JSON output contains `update_available`, `current_version`, and `latest_version`. Quiet mode emits no output and exits with code `2` when an update is available, otherwise `0`.

User-facing CLI errors derived from `UserMessageError` exit with code `1`. Unsafe-template refusal exits with code `4`.

## Template Configuration

The root of a template may contain `copier.yml` or `copier.yaml`. If both are present, Copier raises `MultipleConfigFilesError`. A configuration file has two kinds of entries:

- Settings, whose keys begin with `_` in the YAML file.
- Questions, whose keys do not begin with `_`.

Settings precedence is:

1. CLI or API arguments.
2. Settings from the template configuration file.

Answers precedence is:

1. CLI or API `data`.
2. Interactive prompting.
3. Answers from the last Copier execution.
4. Template defaults.
5. User defaults from settings, where a question supports them.

Questions may use a short form where the value is the default answer, or an advanced mapping. Advanced question keys are:

- `type`: one of `bool`, `float`, `int`, `json`, `path`, `str`, or `yaml`; `yaml` is the default.
- `help`: explanatory prompt text.
- `choices`: list, mapping, or templated YAML choices. Choice values may differ from labels.
- `multiselect`: when true, the answer is a list of selected choice values.
- `default`: default answer. With choices, the default is the choice value, not its label.
- `secret`: hides prompt input and omits the answer from the answers file; secret questions require a default.
- `placeholder`: empty-input placeholder text.
- `qmark`: prompt mark.
- `multiline`: allows multiline input.
- `validator`: Jinja template that renders nothing for valid input and an error message for invalid input.
- `when`: boolean or templated condition that decides whether to ask the question.

Most prompt option values may be templated with Jinja if the option value is a string and the rendered result is valid for the option. Interactive answers themselves are not rendered with Jinja. A skipped question is not recorded; its default remains available in the render context unless the default renders the special `UNSET` value, in which case the variable is undefined.

Configuration files may contain multiple YAML documents and may use `!include` to include other YAML files. When multiple documents define the same question, the later definition wins. For the settings `exclude`, `skip_if_exists`, `jinja_extensions`, and `secret_questions`, values from multiple documents are concatenated. Other repeated settings are overwritten by the later document.

## Rendering Model

Copier copies every file and directory from the active template root into the destination unless an exclusion matches it. File and directory names are Jinja templates. File contents are rendered with Jinja only when the source path ends with the configured template suffix, `.jinja` by default. The rendered destination path drops that suffix.

If `templates_suffix` is an empty string, Copier attempts to render every file except default exclusions. Binary or otherwise unreadable files fall back to a simple copy in that mode. If `templates_suffix` is not empty and a suffixed template file cannot be read or rendered, the operation fails.

When a suffixed template file exists beside a same-named unsuffixed file, the unsuffixed file is ignored. Symlinks are followed by default. With `preserve_symlinks=True`, symlinks remain symlinks, and a symlink whose path ends with the template suffix has its target path rendered.

Rendered destination paths must stay within the destination project. Template symlinks that would copy content from outside the template root are forbidden unless symlink preservation makes the symlink itself the rendered object. External data paths outside the destination project are forbidden unless the run is trusted.

Copier provides Jinja2 plus filters and functions from `jinja2-ansible-filters`. The `pathjoin` global joins path parts using `mode="posix"`, `mode="windows"`, or `mode="native"`. The `to_json` filter can serialize Copier configuration values and paths.

File and directory names support a special yield tag. In a path, `{% yield item from items %}{{ item }}{% endyield %}` creates one rendered path per item and exposes the looped variable to the rendered file or directory contents for that path.

## Template Variables

These variables are available in template rendering:

- `_copier_answers`: answers that should be recorded for future updates. It excludes secret answers, non-JSON/YAML-friendly values, hidden skipped answers, and keys not declared as questions. It includes Copier metadata such as `_commit` and `_src_path` when available.
- `_copier_conf`: JSON-serializable runtime configuration for the operation. It exposes `answers_file`, `cleanup_on_error`, `conflict`, `context_lines`, `data`, `defaults`, `dst_path`, `exclude`, `os`, `overwrite`, `pretend`, `quiet`, `settings`, `skip_answered`, `skip_if_exists`, `skip_tasks`, `src_path`, `unsafe`, `use_prereleases`, `user_defaults`, `vcs_ref`, `vcs_ref_hash`, and `sep`.
- `_copier_python`: absolute path to the Python interpreter running Copier.
- `_external_data`: lazily loaded YAML or JSON data declared by `external_data`.
- `_folder_name`: name of the destination project root directory.
- `_copier_phase`: one of `"prompt"`, `"tasks"`, `"migrate"`, `"render"`, or `"undefined"`.
- `_copier_operation`: `"copy"` or `"update"` where the context supports operation-dependent rendering, notably exclusions and tasks.

Modifying `_copier_conf` from template code does not change the active Copier configuration.

## Settings Reference

The template setting names below are written without their YAML underscore prefix. In `copier.yml`, write them with `_`, for example `_answers_file`.

- `answers_file`: relative answers file path. Default `.copier-answers.yml`.
- `ask`: API/CLI-only list of glob patterns for questions that must be asked.
- `cleanup_on_error`: copy-only cleanup of a newly created destination after failure. Default `True`.
- `conflict`: update conflict output, `"inline"` or `"rej"`. Default `"inline"`.
- `context_lines`: update conflict matching context. Default `3`.
- `data`: API/CLI answers.
- `data_file`: CLI-only YAML file of answers. `--data` overrides it.
- `external_data`: mapping from namespace to destination-relative YAML/JSON path, exposed under `_external_data`.
- `envops`: Jinja environment options. Default keeps trailing newlines. `undefined` accepts `jinja2.Undefined` or `jinja2.StrictUndefined`.
- `exclude`: gitignore-style patterns evaluated against destination paths. Template-defined values replace default exclusions; CLI/API values extend template/default values. Default exclusions are `copier.yaml`, `copier.yml`, `~*`, `*.py[co]`, `__pycache__`, `.git`, `.DS_Store`, and `.svn`, except that an actual configured subdirectory template root starts with no default exclusions.
- `force`: CLI behavior equivalent to defaults plus overwrite for copy and recopy.
- `defaults`: use default answers instead of prompting.
- `overwrite`: overwrite existing files without prompting.
- `jinja_extensions`: Jinja extension import paths. This is unsafe unless trusted.
- `message_before_copy`, `message_after_copy`, `message_before_update`, `message_after_update`: Jinja-rendered messages emitted around successful operations unless quiet.
- `migrations`: update-only commands with optional `version`, `when`, and `working_directory`. Versioned migrations run only when `new version >= declared version > old version`. Migration commands are unsafe unless trusted.
- `min_copier_version`: PEP 440 minimum Copier version. Unsupported versions abort generation or update.
- `pretend`: run without writing changes.
- `preserve_symlinks`: keep symlinks instead of replacing them with targets. Default `False`.
- `quiet`: suppress status output and template messages.
- `secret_questions`: question names whose answers are hidden and omitted from the answers file.
- `skip_answered`: update-only behavior that keeps previously recorded answers without asking.
- `skip_if_exists`: gitignore-style patterns for files that are skipped only when already present. Missing matching files are recreated during update.
- `skip_tasks`: skip normal tasks. It does not skip migrations and does not imply trust.
- `subdirectory`: use a template subdirectory as the template root. The value may be templated.
- `tasks`: commands run after copy or update, in declaration order, with `STAGE=task`; unsafe unless trusted.
- `templates_suffix`: suffix for files rendered as Jinja templates. Default `.jinja`.
- `unsafe`: API/CLI trust for unsafe features.
- `use_prereleases`: include prerelease tags when selecting latest versions.
- `vcs_ref`: Git ref or `VcsRef.CURRENT`; if omitted, Copier chooses the latest PEP 440 release tag.

Exclusion and skip patterns use gitignore-style syntax, including negation with `!`.

## Answers Files

The default answers file is `.copier-answers.yml`. Templates that support updates should include a rendered answers file template named exactly `{{ _copier_conf.answers_file }}.jinja`, or the same path with the configured template suffix. Its content should render `_copier_answers` as YAML, commonly:

```yaml
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers|to_nice_yaml -}}
```

Answers file paths are relative to the project root. Each independent template applied to the same destination should use a different answers file, and each can be updated independently with `copier update -a PATH`.

The answers file stores Copier metadata under underscore-prefixed keys and question answers under their question names. Users must not edit it manually; update correctness depends on it representing the answers that produced the current project.

## Updates

A smart update requires a destination with a valid answers file, a Git-versioned template, and preferably a Git-versioned destination. Copier chooses the target template version from `vcs_ref`, from `VcsRef.CURRENT`, or from the latest PEP 440 release tag, with prerelease handling controlled by `use_prereleases`.

During update, deleted template-generated paths remain deleted in future updates. Paths matched by `skip_if_exists` are the exception: Copier ensures they exist, recreating them if missing.

`run_recopy` and `copier recopy` are the recovery path when smart update replay cannot work. They discard project evolution and render from the template again while keeping recorded answers.

`copier check-update` reports whether the project can move from its recorded template version to a newer version. In JSON mode, the result object has `update_available`, `current_version`, and `latest_version`.

## Unsafe Features

The following template features are unsafe:

- Custom Jinja extensions.
- Tasks.
- Migrations.

If a template uses unsafe features and the run is not trusted, Copier raises `UnsafeTemplateError`; the CLI exits with code `4`. A run is trusted when `unsafe=True`, `--trust`, `--UNSAFE`, or user settings mark the template repository or path as trusted. `skip_tasks=True` avoids normal task execution, but it does not trust the template and does not skip migrations.

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
- `InteractiveSessionError`: input would require an interactive session, such as prompting or overwrite confirmation, but none is available.
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

- A successful API copy and a successful CLI copy with equivalent options produce the same destination files, answers file, and recorded template metadata.
- An answer supplied through API `data` or CLI `--data` is visible in template rendering, suppresses prompting for that question unless `ask` matches it, and takes precedence over `--data-file`, previous answers, user defaults, and template defaults.
- The answers file path used for rendering, recording, recopy, update, and check-update is the same relative path selected by `answers_file` or the template default.
- A question marked secret, or listed in `secret_questions`, may affect rendering during the current operation but is not recorded in `_copier_answers` or the answers file.
- `exclude` prevents matching paths from being rendered at all, while `skip_if_exists` only preserves matching paths that already exist and recreates missing matching paths on update.
- `pretend=True` and `--pretend` preserve the same decision-making behavior as a real run while leaving destination files unchanged.
- `quiet=True` and `--quiet` suppress status and template messages but do not change rendering, answer precedence, unsafe checks, or update decisions.
- Unsafe features are allowed or rejected consistently across API and CLI according to explicit trust, user settings trust, and the presence of unsafe template configuration.
- `VcsRef.CURRENT` and CLI `--vcs-ref=:current:` both keep the recorded template ref instead of selecting the latest tag.
- `copier check-update --output-format json` reports the same update decision that quiet mode encodes as exit status `2` for update available and `0` for no update.

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

## Non-Goals

- This specification does not require compatibility with deprecated internal module import paths.
- It does not prescribe Copier's internal class layout, caching strategy, subprocess implementation, prompt toolkit integration, or Git command implementation.
- It does not require network access in tests; local paths and local Git repositories are sufficient to exercise the documented behavior.
- It does not require exact terminal colors, emoji rendering, progress wording, or full snapshot matching of help text.
- It does not require reproducing private test helpers, private attributes, or internal metadata structures beyond the documented answers file and public template variables.
- It does not require supporting template features that depend on third-party extensions unless those extensions are installed and explicitly trusted.

## Evaluation Notes

Evaluation focuses on public behavior through the documented Python API, CLI commands, generated destination trees, answers files, update/check-update outcomes, template configuration semantics, user settings, and documented error classes. Tests may compare API and CLI projections of the same operation, verify answer precedence, inspect rendered files and answers files, exercise local Git update flows, check unsafe-feature refusal and trust behavior, and validate documented exceptions and warnings.

Scoring should reward behavior that follows this specification from public inputs and outputs. It should not depend on private import paths, private class names, exact internal object layouts, network repositories, or terminal styling. Fixture templates are examples of the documented concepts rather than hidden requirements; a correct implementation should generalize from the documented contracts.
