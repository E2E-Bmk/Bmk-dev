# Cookiecutter Reconstruction Spec v2

Source: derived from official Cookiecutter documentation, API reference, and public README only.

---

## Product Overview

Build a Python package named `cookiecutter` plus a `cookiecutter` CLI entry point. The package generates new projects from project templates. A template is a directory (or archive) containing a `cookiecutter.json` prompt/defaults file and a project directory tree whose names and contents may contain Jinja2 template expressions.

Primary target: local, filesystem-based template generation. Remote repository cloning (GitHub/Bitbucket/GitLab/VCS) is out of scope for this slice. Local paths and local zip archives must work.

## Non-Goals

- No network fetching of remote templates (git clone, hg clone, URL download).
- No Mercurial support.
- No automatic installation of third-party Jinja2 extensions.
- No exact compatibility for undocumented exception message text, log format strings, or internal object shapes.
- Do not replicate private source architecture or private test fixture content.

---

## Public Interfaces

### CLI

Entry point command: `cookiecutter`

```
cookiecutter [OPTIONS] TEMPLATE [EXTRA_CONTEXT]...
```

`TEMPLATE` is a local directory path or a local zip archive path.

`EXTRA_CONTEXT` are zero or more `key=value` arguments that override values from `cookiecutter.json` and user configuration.

Options:

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

### Python API

```python
from cookiecutter.main import cookiecutter

result_path = cookiecutter(
    template,                    # str: local path or zip path
    checkout=None,               # str: VCS checkout ref (out of scope for this slice)
    no_input=False,              # bool
    extra_context=None,          # dict | None
    replay=False,                # bool | str: True uses default replay, str uses that file path
    overwrite_if_exists=False,   # bool
    output_dir='.',              # str
    config_file=None,            # str | None
    default_config=False,        # bool
    password=None,               # str | None: zip password
    directory=None,              # str | None: subdirectory inside archive/repo
    skip_if_file_exists=False,   # bool
    accept_hooks=True,           # bool
    keep_project_on_failure=False, # bool
)
```

Returns the absolute path to the generated project directory as a string.

### Supported Entry Points

The required callable Python entry point is `cookiecutter.main.cookiecutter(...)`, as described above. The required command-line entry point is `cookiecutter <template>`. The implementation may organize prompting, rendering, hooks, replay storage, configuration, and filesystem helpers in any internal module structure as long as the observable behavior in this specification is preserved.

---

## Template Structure

A local template directory has this layout:

```
template-root/
  cookiecutter.json              # required
  {{ cookiecutter.project_slug }}/ # required: one directory whose name is a template expression
    ... template files and subdirectories ...
  hooks/                         # optional
    pre_prompt.py  (or .sh)
    pre_gen_project.py  (or .sh)
    post_gen_project.py  (or .sh)
```

`cookiecutter.json` is a UTF-8 JSON file whose top-level keys are variable names and whose values define defaults and types. A `ContextDecodingException` is raised if it cannot be decoded.

The generated project root is the rendered name of the template directory (e.g., `{{ cookiecutter.project_slug }}` becomes `my_project`). Files and directories under that root are rendered recursively.

---

## cookiecutter.json Variable Types

### String Variables

A string value defines a plain text variable. The default is shown in the prompt. The user may enter any text.

### Choice Variables

A list value defines a choice variable. The first list item is the default. When prompting, choices are displayed as a numbered list:

```
Select license:
1 - MIT
2 - BSD-3
3 - GNU GPL v3.0
Choose from 1, 2, 3 [1]:
```

The user enters a number; the corresponding string value is stored. With `no_input=True` the first item is used. When `default_context` in user config contains a matching key whose value is one of the list items, that item moves to position 0 (becomes the new default).

### Boolean Variables

A JSON `true` or `false` value defines a boolean variable. The prompt shows `[True]` or `[False]` as default. Accepted input values (case-insensitive):

- True: `"1"`, `"true"`, `"t"`, `"yes"`, `"y"`, `"on"`
- False: `"0"`, `"false"`, `"f"`, `"no"`, `"n"`, `"off"`

Any other input prints `"Error: <value> is not a valid boolean"` and re-prompts. With `no_input=True` the default boolean is used. In template expressions the value is a Python `bool`.

### Dictionary Variables

A JSON object value defines a dictionary variable. When prompting, the current dict is shown as JSON and the user must enter valid JSON. Invalid JSON re-prompts. With `no_input=True` the default dict is used. In template expressions the value is a Python `dict` and can be iterated and accessed by key.

### Private Variables (Single Underscore Prefix)

A key beginning with a single underscore (e.g., `_copy_without_render`, `_extensions`, `_not_rendered`) is private. The user is never prompted for private variables. The value is preserved exactly as written in `cookiecutter.json` — it is **not** rendered through Jinja2. Private variables are available in the context for use by the implementation but are not exposed as user-facing prompt fields.

### Private Rendered Variables (Double Underscore Prefix)

A key beginning with a double underscore (e.g., `__project_slug`) is private and rendered. The user is never prompted. The value **is** rendered through Jinja2 using previously resolved context values before being stored. This allows derived computed values:

```json
{
  "project_name": "Project Name",
  "__project_slug": "{{ cookiecutter.project_name|lower|replace(' ', '-') }}"
}
```

### `__prompts__` Key

The special `__prompts__` key is a dict that maps variable names to human-readable prompt labels. When present, the corresponding variable uses the mapped label as its prompt text instead of the raw variable name. `__prompts__` may also contain nested dicts to provide labels for individual choice items.

### Templated Default Values

String (and other) default values may themselves contain Jinja2 expressions that reference earlier variables in the `cookiecutter.json` ordering:

```json
{
  "project_name": "My Project",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}"
}
```

Variables are processed in `cookiecutter.json` key order. Each rendered default is available to subsequent variable expressions.

### `_copy_without_render` Key

A private list of shell-style glob patterns. Files and directories whose paths (relative to the template directory) match any pattern have their **contents** copied byte-for-byte without Jinja2 rendering. Their **path names** are still rendered. Matching uses `fnmatch`-style patterns.

### `_extensions` Key

A private list of Jinja2 extension import paths. On invocation, each extension is imported and added to the rendering environment. If an extension cannot be imported, an `UnknownExtension` exception is raised.

### `templates` Key (Nested Config, v2.5+)

If `cookiecutter.json` contains a top-level `"templates"` key whose value is a dict of named template entries, the user is prompted to select one of the named templates. Each entry has a `"path"` (relative subdirectory), a `"title"` (display name), and an optional `"description"`. After selection, cookiecutter continues with the `cookiecutter.json` in the chosen subdirectory.

Display format:
```
Select template:
1 - Title One (description)
2 - Title Two (description)
Choose from 1, 2 [1]:
```

### `template` Key (Nested Config, v2.2 Old Format)

If `cookiecutter.json` contains a `"template"` key whose value is a list of strings in the form `"Title (./path)"`, the user is prompted to select one. The path inside parentheses is used as the subdirectory.

---

## Context Resolution

Context uses template defaults from `cookiecutter.json` as its base. User configuration `default_context` values override those defaults, and `extra_context` values supplied through the Python API or CLI override both. When prompting is enabled and replay mode is not active, interactive answers have final precedence.

With `no_input=True`: skip all prompts, use defaults plus overrides.

With `replay=True`: load context from the replay file for this template; skip prompts. Replay mode is mutually exclusive with extra context from CLI.

With `replay=<file_path>` (a string): load context from the specified JSON file.

---

## Rendering and File Generation

All template rendering uses strict Jinja2 undefined-variable behavior: an undefined variable raises `UndefinedVariableInTemplate`.

Rendering applies to:
- The project directory name (rendered to produce the output directory name)
- All file and subdirectory names under the project directory
- All text file contents, unless the file path matches `_copy_without_render`

Binary files are detected and copied without rendering. Text files use UTF-8 encoding by default.

Generation renders the top-level project directory name under `output_dir`, renders names and contents throughout the template tree, and preserves the documented hook ordering. A `pre_gen_project` hook runs before project files are produced, and a `post_gen_project` hook runs after generation. If a hook fails and `keep_project_on_failure=False`, the partially generated project directory is removed.

Existing output directory behavior:
- Default: raise `OutputDirExistsException`.
- `overwrite_if_exists=True`: proceed and overwrite files.
- `skip_if_file_exists=True`: skip files that already exist, generate only new ones.

---

## Hooks

Hook scripts live in `hooks/` inside the template directory. Supported file extensions: `.py`, `.sh` (Unix), `.bat` (Windows).

| Hook | Timing | Working directory | Template variables available |
|------|--------|-------------------|------------------------------|
| `pre_prompt` | Before any variable is rendered | A temporary copy of the repository directory | No |
| `pre_gen_project` | After context is resolved, before files are generated | Root of the generated project directory | Yes (Jinja2-rendered) |
| `post_gen_project` | After all project files are generated | Root of the generated project directory | Yes (Jinja2-rendered) |

Hook execution details:
- Python hooks are run with the same Python interpreter in use.
- Shell hooks are executed by the OS shell.
- Hook script contents may contain Jinja2 expressions for `pre_gen_project` and `post_gen_project`; these are rendered before execution.
- If a hook exits with a nonzero status, `FailedHookException` is raised and generation halts.
- If `keep_project_on_failure=False` and a hook fails after the project directory was created, the project directory is deleted.
- `pre_prompt` runs in a temporary copy of the template directory; this allows the hook to modify `cookiecutter.json` before prompting without mutating the original template.
- `accept_hooks=False` skips all hooks. `accept_hooks=True` (default) runs hooks. `accept_hooks='ask'` prompts the user before running.

---

## Replay

On successful generation, cookiecutter saves a replay file so the same context can be reused later.

Replay file location: `<replay_dir>/<template_name>.json`
- `replay_dir` defaults to `~/.cookiecutter_replay/` unless overridden in user config.
- `template_name` is the base name of the template directory.

Replay file format:
```json
{
  "cookiecutter": {
    "variable1": "value1",
    "variable2": "value2"
  }
}
```

`--replay` on the CLI (or `replay=True` in the Python API) loads this file and uses its `cookiecutter` dict as the context without prompting.

`--replay-file PATH` (or `replay=<path_string>`) loads context from an explicit JSON file rather than the default replay location.

---

## User Configuration

Default config file: `~/.cookiecutterrc` (YAML format).

Override with:
- CLI `--config-file PATH`
- CLI `--default-config` (ignore all user config, use built-in defaults)
- `COOKIECUTTER_CONFIG` environment variable (path to a YAML config file)

Built-in defaults:
```python
{
  'cookiecutters_dir': '~/.cookiecutters/',
  'replay_dir': '~/.cookiecutter_replay/',
  'default_context': {},
  'abbreviations': {
    'gh': 'https://github.com/{0}.git',
    'bb': 'https://bitbucket.org/{0}',
    'gl': 'https://gitlab.com/{0}.git',
  },
}
```

User config keys:
- `default_context`: dict of key/value pairs injected into every generation as defaults.
- `cookiecutters_dir`: where cloned template repos are stored.
- `replay_dir`: where replay files are stored.
- `abbreviations`: dict of shorthand aliases for template URLs/paths. Values may contain `{0}` as a placeholder for a suffix.

Configuration loading behavior:
- If `default_config=True`, use built-in defaults without reading any file.
- If `config_file` is given, read that YAML file; raise `ConfigDoesNotExistException` if it does not exist.
- Otherwise, try `~/.cookiecutterrc` then the `COOKIECUTTER_CONFIG` environment variable. If neither exists, use built-in defaults.

---

## Template Directories and Archives

### `--directory` Option

If a template repo or archive contains multiple templates, `--directory NAME` (or `directory=NAME` in the Python API) selects which subdirectory to use as the template root. The selected subdirectory must contain its own `cookiecutter.json` and a `{{ cookiecutter.* }}`-named project directory.

### Zip Archives

A local `.zip` file path is a valid template argument. The archive is extracted to a temporary directory and treated as a template repo. The zip must unpack into a top-level directory containing the template.

### Password-Protected Zip Files

If the zip archive is password-protected, the `password` argument (Python API) or the `COOKIECUTTER_REPO_PASSWORD` environment variable provides the password. If neither is set, the user is prompted for the password.

---

## Built-in Template Extensions

These extensions are always available in the rendering environment without listing them in `_extensions`:

### JSON Filter
Provides a `jsonify` filter. Converts a Python object to a JSON string.
- `{{ value | jsonify }}` — default indent 4.
- `{{ value | jsonify(2) }}` — custom indent.

### Random String Global
Provides `random_ascii_string(length, punctuation=False)` as a global function.
- Generates a random ASCII string of the given length.
- With `punctuation=True`, includes punctuation characters `!"#$%&'()*+,-./:;<=>?@[\]^_\`{|}~`.

### Slugify Filter
Provides a `slugify` filter. Converts a string to a lowercase hyphen-separated slug. Handles special characters (e.g., apostrophes). Accepts all keyword arguments of `python-slugify`'s `slugify` function (e.g., `separator`).

### Time Tag
Provides a `{% now '<timezone>', '<format>' %}` tag. Returns the current time formatted by strftime. Example: `{% now 'utc', '%Y' %}`.

### UUID Global
Provides `uuid4()` as a global function. Returns a UUID4 string.

### Custom Extensions via `_extensions`

Templates may list additional Jinja2 extension import paths in `_extensions`. Cookiecutter imports them at render time. If an extension cannot be imported, `UnknownExtension` is raised.

### Local Extensions

A template may include local Python extension modules in its root directory (e.g., `local_extensions.py` or `local_extensions/__init__.py`). These are listed in `_extensions` by module and class name (e.g., `"local_extensions.FoobarExtension"`).

Custom Jinja2 extensions may register additional filters, globals, and tags. Their import paths come from `_extensions`; the internal helper used to register them is not prescribed.

---

## Exceptions

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

---

## Logging

Verbose mode (`--verbose`) enables DEBUG-level logging to stdout. Implementations may also write diagnostic logs to a file, but no internal logging helper or module layout is prescribed.

---

## Cross-View Invariants

1. CLI and Python API invocations with identical inputs (template path, context, output dir, hook policy) must produce identical generated file trees.
2. Context values must be consistent across: prompt display, generated file names, generated file contents, hook script rendering, and the saved replay file.
3. `_copy_without_render` patterns must preserve matched file contents byte-for-byte while still rendering their path names.
4. User `default_context` overrides and `extra_context` overrides must appear in the saved replay file.
5. Hook failure must not leave a successfully-appearing output project when `keep_project_on_failure=False`.
6. `--directory` selection must apply the same rendering, hook, and replay behavior as a root-level template.
7. Replay round-trip: `dump` then `load` must return a context equal to the original.
8. With `no_input=True`, no interactive prompt may be issued; defaults and overrides are used silently.

---

## Implementation Guidance

Hidden tests use only public APIs, CLI invocations, generated file inspection, replay JSON content, exception classes, and observable CLI exit codes. They do not require access to private internals, private fixture shapes, or undocumented exception message text.
