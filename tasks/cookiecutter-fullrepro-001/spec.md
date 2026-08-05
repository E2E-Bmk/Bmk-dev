# Cookiecutter Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cookiecutter` is a project-generation tool with a `cookiecutter` CLI entry point. It generates new projects from project templates. A template is a directory (or archive) containing a `cookiecutter.json` prompt/defaults file and a project directory tree whose names and contents may contain Jinja2 template expressions.

This specification covers local, filesystem-based template generation. Remote repository cloning is not covered. Local paths and local zip archives must work.

## Non-Goals

- This specification does not require Remote template fetching through version-control clones or URL downloads.
- This specification does not require Mercurial-based template sources.
- This specification does not require Automatic installation of third-party Jinja2 extensions.
- This specification does not require Exact compatibility with undocumented exception message text, log format strings, or internal object shapes.
- This specification does not require Private source architecture or private test fixture content.

## Representative Workflows

### Generate a project via the Python API

```python
from cookiecutter.main import cookiecutter

project_path = cookiecutter(
    "path/to/template",
    no_input=True,
    extra_context={"project_name": "hello_world", "license": "MIT"},
    output_dir="/tmp/output",
)
assert project_path.endswith("hello_world")
```

Calling `cookiecutter(template, no_input=True, extra_context=..., output_dir=...)` resolves defaults and overrides without prompting, runs accepted hooks around generation, writes the project under the requested output directory, saves replay data when enabled, and returns the absolute project path as a string.

### Generate the same project via the CLI

```console
$ cookiecutter path/to/template --no-input --output-dir /tmp/output project_name=hello_world license=MIT
```

Running the equivalent CLI command with `--no-input` and `key=value` overrides must produce the same file tree as the Python API invocation above. The template must contain a `cookiecutter.json` and a `{{ cookiecutter.project_name }}`-named project directory with renderable files.

## Template Structure and Variable Types

A local template directory contains a required `cookiecutter.json` and a required project directory whose name is a Jinja2 template expression referencing `cookiecutter`. An optional `hooks/` subdirectory may contain lifecycle scripts.

**cookiecutter.json format.** The file must be UTF-8 JSON. Its top-level keys are variable names and its values define defaults and types. When the file cannot be decoded, `ContextDecodingException` must be raised.

**String variables.** A string value defines a plain text variable with that default. The user may enter any text. An empty string default must render as empty content.

**Choice variables.** A list value defines a choice variable. The first list item is the default. When prompting, choices must be displayed as a numbered list and the user enters a number. With `no_input=True` the first item must be used. When `default_context` in user config contains a matching key whose value is one of the list items, that item must move to position 0 and become the new default.

**Boolean variables.** A JSON `true` or `false` value defines a boolean variable. Accepted input values are case-insensitive: `"1"`, `"true"`, `"t"`, `"yes"`, `"y"`, `"on"` for true and `"0"`, `"false"`, `"f"`, `"no"`, `"n"`, `"off"` for false. Any other input must re-prompt. With `no_input=True` the default boolean must be used. In template expressions the value must be a Python `bool`.

**Dictionary variables.** A JSON object value defines a dictionary variable. When prompting, the current dict is shown as JSON and the user must enter valid JSON. Nested dictionaries must be accessible in templates by dotted attribute access.

**Private variables (single underscore prefix).** A key beginning with a single underscore (e.g., `_copy_without_render`, `_extensions`) is private. The user must never be prompted for private variables. The value must be preserved exactly as written — it must not be rendered through Jinja2. Private variables must be available in the context for use by the implementation.

**Private rendered variables (double underscore prefix).** A key beginning with a double underscore (e.g., `__project_slug`) is private and rendered. The user must never be prompted. The value must be rendered through Jinja2 using previously resolved context values before being stored, allowing derived computed values.

**`__prompts__` key.** The special `__prompts__` key maps variable names to human-readable prompt labels. When present, the corresponding variable must use the mapped label as its prompt text instead of the raw variable name. `__prompts__` may contain nested dicts to provide labels for individual choice items.

**Templated default values.** Default values may contain Jinja2 expressions that reference earlier variables in `cookiecutter.json` key order. Each rendered default must be available to subsequent variable expressions. When an earlier variable is overridden by `extra_context`, templated defaults that depend on it must recompute from the overridden value.

**`_copy_without_render` key.** A private list of shell-style glob patterns. Files and directories whose paths match any pattern must have their contents copied byte-for-byte without Jinja2 rendering, while their path names must still be rendered.

**`_extensions` key.** A private list of Jinja2 extension import paths. Each extension must be imported and added to the rendering environment. If an extension cannot be imported, `UnknownExtension` must be raised.

**`templates` key (nested config).** When `cookiecutter.json` contains a top-level `"templates"` key whose value is a dict of named template entries, the user must be prompted to select one. Each entry has a `"path"` (relative subdirectory), a `"title"` (display name), and an optional `"description"`. After selection, cookiecutter must continue with the `cookiecutter.json` in the chosen subdirectory. With `no_input=True` the first entry must be selected.

**`template` key (legacy format).** When `cookiecutter.json` contains a `"template"` key whose value is a list of strings in the form `"Title (./path)"`, the user must be prompted to select one. The path inside parentheses must be used as the subdirectory. With `no_input=True` the first entry must be selected.

## Context Resolution and Rendering

Context resolution determines how variable values are combined from multiple sources before rendering begins.

**Precedence chain.** Template defaults from `cookiecutter.json` form the base. User configuration `default_context` values override those defaults. `extra_context` values supplied through the Python API or CLI override both. When prompting is enabled and replay mode is not active, interactive answers have final precedence. With `no_input=True`, all prompts must be skipped and defaults plus overrides must be used.

**Replay mode.** With `replay=True`, context must be loaded from the replay file for this template and prompts must be skipped. With `replay=<file_path>` (a string), context must be loaded from the specified JSON file. The replay file must contain a `"cookiecutter"` key mapping variable names to values.

**Replay persistence.** On successful generation, cookiecutter must save a replay file at `<replay_dir>/<template_name>.json` where `replay_dir` defaults to `~/.cookiecutter_replay/` and `template_name` is the base name of the template directory.

**Jinja2 rendering.** All template rendering must use strict Jinja2 undefined-variable behavior: an undefined variable must raise `UndefinedVariableInTemplate`. Rendering applies to the project directory name, all file and subdirectory names under the project directory, and all text file contents unless the file path matches `_copy_without_render`. Binary files must be detected and copied without rendering.

**File generation.** The rendered project directory must be placed under `output_dir`. When the output directory already exists, the default behavior must raise `OutputDirExistsException`. When `overwrite_if_exists=True`, the operation must proceed and overwrite existing files. When `skip_if_file_exists=True`, existing files must be preserved and only new files must be generated.

**UTF-8 support.** Context values containing Unicode characters must round-trip correctly through rendered directory names, file names, and file contents.

## Hooks and Lifecycle

Hook scripts control pre- and post-generation behavior and live in `hooks/` inside the template directory. Supported file extensions are `.py` and `.sh`.

**Hook timing and working directory.** `pre_prompt` runs before any variable is rendered, in a temporary copy of the repository directory. `pre_gen_project` runs after context is resolved and before files are generated, in the root of the generated project directory. `post_gen_project` runs after all project files are generated, in the root of the generated project directory. Hook script contents for `pre_gen_project` and `post_gen_project` must be rendered through Jinja2 before execution.

**Hook ordering.** When both pre- and post-generation hooks are present, `pre_gen_project` must run before project files are generated and `post_gen_project` must run after. The post-generation hook must be able to read files produced during generation.

**Hook failure.** When a hook exits with a nonzero status, `FailedHookException` must be raised and generation must halt. When `keep_project_on_failure=False` and a hook fails after the project directory was created, the project directory must be deleted. When `keep_project_on_failure=True`, the partially generated project must be preserved.

**Hook acceptance.** `accept_hooks=False` must skip all hooks. `accept_hooks=True` (default) must run hooks. `accept_hooks='ask'` must prompt the user before running.

## User Configuration

Cookiecutter reads user preferences from a YAML configuration file.

**Default config file.** The default location is `~/.cookiecutterrc`. The `COOKIECUTTER_CONFIG` environment variable may specify an alternative path. When `default_config=True`, all user config files must be ignored and built-in defaults must be used.

**Config file loading.** When `config_file` is given, that YAML file must be read; `ConfigDoesNotExistException` must be raised if it does not exist. Otherwise, `~/.cookiecutterrc` and then `COOKIECUTTER_CONFIG` are tried. When neither exists, built-in defaults must be used.

**Config keys.** `default_context` is a dict of key/value pairs injected into every generation as defaults. `replay_dir` is where replay files are stored. `cookiecutters_dir` is where cloned template repos are stored. `abbreviations` is a dict of shorthand aliases for template URLs/paths.

## Template Directories and Archives

Templates may reside in subdirectories within a repository or inside zip archives.

**`--directory` option.** When `directory=NAME` is supplied, the named subdirectory must be used as the template root. It must contain its own `cookiecutter.json` and a templated project directory. All rendering, hook, and replay behavior must apply as for a root-level template.

**Zip archives.** A local `.zip` file path must be accepted as a valid template argument. The archive must be extracted to a temporary directory and treated as a template repo. When the archive is password-protected, the `password` argument or the `COOKIECUTTER_REPO_PASSWORD` environment variable must supply the password. A wrong password must raise `InvalidZipRepository`. The `--directory` option must work inside zip archives.

## Built-in Template Extensions

These extensions must always be available in the rendering environment without listing them in `_extensions`.

**JSON filter.** The `jsonify` filter must convert a Python object to a JSON string. Default indent must be 4 spaces. `{{ value | jsonify(2) }}` must use a custom indent of 2 spaces.

**Random string global.** `random_ascii_string(length, punctuation=False)` must generate a random ASCII string of the given length. Without punctuation, the string must contain only letters and digits. With `punctuation=True`, the string must include punctuation characters.

**Slugify filter.** The `slugify` filter must convert a string to a lowercase hyphen-separated slug. It must handle special characters such as apostrophes. It must accept keyword arguments such as `separator`.

**Time tag.** `{% now '<timezone>', '<format>' %}` must return the current time formatted by strftime.

**UUID global.** `uuid4()` must return a UUID4 string. Multiple calls must each produce valid UUID4 strings. The function must be usable in both file content and file name rendering.

**Custom and local extensions.** Templates may list additional Jinja2 extension import paths in `_extensions`. A template may include local Python extension modules in its root directory. Custom extensions may register additional filters, globals, and tags. When an extension cannot be imported, `UnknownExtension` must be raised.

## Logging

Verbose mode (`--verbose` or `-v`) must enable DEBUG-level logging to stdout. Generation must succeed normally while verbose logging is active.

## State Model

A generation run has one resolved template source, one ordered context, one selected template directory, one generated project tree, and optionally one replay record. The CLI and Python API are two entry views over this same state.

- A resolved context value must be identical wherever it appears in a rendered directory name, file name, file body, hook environment, and replay data.
- CLI options and equivalent Python arguments must produce the same selected template, context precedence, file tree, overwrite behavior, and replay semantics.
- Files matched by `_copy_without_render` must preserve their contents while their path names still use the resolved context.
- A saved replay record must reproduce the same resolved answers unless explicitly overridden by a higher-precedence input.

Returns the absolute path to the generated project directory as a string.

## Error Semantics

All exceptions inherit from `CookiecutterException(Exception)`.

| Class | When raised |
|-------|-------------|
| `NonTemplatedInputDirException` | Template directory has no `{{ cookiecutter.* }}`-named project directory. |
| `UnknownTemplateDirException` | Multiple `{{ cookiecutter.* }}`-named directories found in template root. |
| `MissingProjectDir` | The expected generated project directory does not exist after generation. |
| `ConfigDoesNotExistException` | Specified config file path does not exist. |
| `InvalidConfiguration` | Config file content is malformed or missing required keys. |
| `UnknownRepoType` | Template path does not match any known repository type. |
| `VCSNotInstalled` | Required VCS tool (e.g., git) is not installed. |
| `ContextDecodingException` | `cookiecutter.json` cannot be decoded (invalid JSON or encoding). |
| `OutputDirExistsException` | Output project directory already exists and overwrite is not enabled. |
| `EmptyDirNameException` | Rendered project directory name is empty. |
| `InvalidModeException` | Incompatible combination of options (e.g., `replay` and `no_input` together, or `replay` and `extra_context` together). |
| `FailedHookException` | A hook script exited with a nonzero status. |
| `UndefinedVariableInTemplate` | A template expression references an undefined variable. Attributes: `message`, `error`, `context`. |
| `UnknownExtension` | A listed Jinja2 extension could not be imported. |
| `RepositoryNotFound` | The given template path does not exist or is not a valid repository. |
| `RepositoryCloneFailed` | VCS clone of the template repository failed. |
| `InvalidZipRepository` | The zip archive does not contain a valid template structure. |

## Cross-View Invariants

1. CLI and Python API invocations with identical inputs (template path, context, output dir, hook policy) must produce identical generated file trees.
2. Context values must be consistent across: prompt display, generated file names, generated file contents, hook script rendering, and the saved replay file.
3. `_copy_without_render` patterns must preserve matched file contents byte-for-byte while still rendering their path names.
4. User `default_context` overrides and `extra_context` overrides must appear in the saved replay file.
5. Hook failure must not leave a successfully-appearing output project when `keep_project_on_failure=False`.
6. `--directory` selection must apply the same rendering, hook, and replay behavior as a root-level template.
7. Replay round-trip: `dump` then `load` must return a context equal to the original.
8. With `no_input=True`, no interactive prompt may be issued; defaults and overrides are used silently.

## Public Interface

### Import Surface

```python
from cookiecutter.main import cookiecutter
from cookiecutter.exceptions import (
    CookiecutterException,
    NonTemplatedInputDirException,
    UnknownTemplateDirException,
    MissingProjectDir,
    ConfigDoesNotExistException,
    InvalidConfiguration,
    UnknownRepoType,
    VCSNotInstalled,
    ContextDecodingException,
    OutputDirExistsException,
    EmptyDirNameException,
    InvalidModeException,
    FailedHookException,
    UndefinedVariableInTemplate,
    UnknownExtension,
    RepositoryNotFound,
    RepositoryCloneFailed,
    InvalidZipRepository,
)
```

The required command-line entry point is `cookiecutter <template>`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| cookiecutter | function | Generate a project from a local template and return the absolute output path |
| CookiecutterException | exception | Base exception for all cookiecutter errors |
| NonTemplatedInputDirException | exception | Template has no templated project directory |
| UnknownTemplateDirException | exception | Multiple templated directories found in template root |
| MissingProjectDir | exception | Generated project directory does not exist after generation |
| ConfigDoesNotExistException | exception | Specified config file path does not exist |
| InvalidConfiguration | exception | Config file content is malformed or missing required keys |
| UnknownRepoType | exception | Template path does not match any known repository type |
| VCSNotInstalled | exception | Required VCS tool is not installed |
| ContextDecodingException | exception | cookiecutter.json cannot be decoded |
| OutputDirExistsException | exception | Output directory exists and overwrite is not enabled |
| EmptyDirNameException | exception | Rendered project directory name is empty |
| InvalidModeException | exception | Incompatible combination of options |
| FailedHookException | exception | Hook script exited with nonzero status |
| UndefinedVariableInTemplate | exception | Template expression references an undefined variable |
| UnknownExtension | exception | Jinja2 extension could not be imported |
| RepositoryNotFound | exception | Template path does not exist or is not valid |
| RepositoryCloneFailed | exception | VCS clone of template repository failed |
| InvalidZipRepository | exception | Zip archive does not contain valid template structure |

### CLI Entry Points

Entry point command: `cookiecutter`

```
cookiecutter [OPTIONS] TEMPLATE [EXTRA_CONTEXT]...
```

`TEMPLATE` is a local directory path or a local zip archive path. `EXTRA_CONTEXT` are zero or more `key=value` arguments that override values from `cookiecutter.json` and user configuration.

| Option | Description |
|--------|-------------|
| `--no-input` | Do not prompt; use template defaults plus any overrides. |
| `-o, --output-dir PATH` | Write the generated project under PATH (default: current directory). |
| `--overwrite-if-exists` | Overwrite the contents of an existing output directory. |
| `--skip-if-file-exists` | Skip files that already exist in the output directory instead of overwriting. |
| `--replay` | Reuse the last saved replay context for this template without prompting. |
| `--replay-file PATH` | Use a specific JSON file as the replay context. |
| `--config-file PATH` | Load user configuration from this YAML file instead of the default location. |
| `--default-config` | Do not load any user config file; use built-in defaults only. |
| `-d, --directory NAME` | Select a named subdirectory inside a repository or archive as the template root. |
| `--accept-hooks [yes\|ask\|no]` | Control whether hook scripts are executed (default: yes). |
| `--keep-project-on-failure` | Do not delete a partially generated project if a hook fails. |
| `--verbose / -v` | Enable verbose logging. |
| `--version` | Print version and exit. |

The Python entry point accepts the same options: template source, output directory, context overrides, replay mode, overwrite and skip policies, configuration sources, zip password, subdirectory selection, hook acceptance, and failure cleanup behavior.

The CLI must also be invocable via `python -m cookiecutter`.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Compatibility covers context types and precedence, rendering, hooks, replay, user configuration, directories and archives, built-in extensions, error conditions, and CLI/API agreement. It observes public files, returned paths, prompts, documented logging behavior, replay data, exceptions, and exit statuses. Private helpers, prompt-library internals, caches, temporary-directory strategy, exact diagnostic wording, and source organization are not part of this contract.
