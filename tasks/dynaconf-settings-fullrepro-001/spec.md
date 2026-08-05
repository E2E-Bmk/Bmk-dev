# Dynaconf Core Settings Behavior Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`dynaconf` is a configuration-management library with a `dynaconf` CLI entry point. It manages configuration from local files and environment variables, optionally separates values by environment, validates the resulting settings, and exposes the same final state through Python accessors, validators, inspection/history utilities, and CLI commands.

The core scope is the local settings engine. Network-backed Redis or Vault behavior, and Django or Flask integrations, are not covered unless explicitly exercised through their public optional wrappers.

## Non-Goals

- Network-backed Redis or Vault behavior is outside the local core design.
- This specification does not require Django or Flask extension behaviorunless explicitly selected in a later scope.
- This specification does not require Upstream test helper packages or repository-local fixtures.
- This specification does not require Upstream internal implementation modules as required API.
- This specification does not require Undocumented private helpers or private attributes.
- This specification does not require Internet access.

## Representative Workflows

### Load settings, validate, and update at runtime

```python
import os
from dynaconf import Dynaconf, Validator

os.environ["DYNACONF_PORT"] = "@int 9000"

settings = Dynaconf(
    settings_files=["settings.toml"],
    environments=True,
    env="development",
    validators=[
        Validator("PORT", is_type_of=int, must_exist=True),
    ],
)

assert isinstance(settings.PORT, int)
assert settings.get("PORT") == 9000

settings.set("database.host", "localhost")
assert settings.get("database.host") == "localhost"
assert "database" in settings.as_dict()
```

Constructing `Dynaconf` with `settings_files` and `environments=True` loads the development section from `settings.toml`. The environment variable `DYNACONF_PORT` with `@int` casting overrides the file value. The validator confirms `PORT` is an integer. Runtime `set` updates a nested key accessible via dotted `get` and `as_dict()`.

### Inspect history and use the CLI

```python
from dynaconf import Dynaconf, get_history, inspect_settings

settings = Dynaconf(settings_files=["settings.toml"], environments=True, env="development")
history = get_history(settings, key="PORT")
assert len(history) >= 1

report = inspect_settings(settings, key="PORT")
assert "current" in report or "current_value" in report
```

`get_history` and `inspect_settings` expose loading provenance for any key. The equivalent CLI commands `dynaconf get PORT` and `dynaconf list` must report the same final values as the Python accessors. Switching environments with `settings.setenv("production")` exposes production-layer values without mutating previous development results.

## Constructing Settings

The settings constructor accepts configuration options that control loading sources, environment separation, casting, merge behavior, validation, and runtime behavior.

**Constructor options.** `Dynaconf(...)` accepts documented configuration options as keyword arguments. Public options include `envvar_prefix` for environment-variable matching, settings file paths, `root_path`, `environments` for environment separation, `env` for active environment name, environment switcher variable, `load_dotenv`, `encoding`, `auto_cast`, `dotted_lookup`, lowercase read, `merge_enabled`, nested separator, `preload` and `includes` lists, skip files, secrets paths, `fresh_vars`, loader lists, core loader formats, `validators`, `validate_on_update` mode, `apply_default_on_none`, `ignore_unknown_envvars`, `sysenv_fallback`, `post_hooks`, and filtering strategy.

**Environment-variable prefix.** When `envvar_prefix` is a string, environment variables with that prefix (followed by `_`) are loaded as settings. When `envvar_prefix` contains commas, each comma-separated prefix is loaded independently. When `envvar_prefix` is `False`, all environment variables are loaded without prefix filtering.

Configuration options may also be supplied through environment variables named as upper-case option names with `_FOR_DYNACONF` suffix, such as `ENVVAR_PREFIX_FOR_DYNACONF`, `SETTINGS_FILES_FOR_DYNACONF`, `ENVIRONMENTS_FOR_DYNACONF`, `LOAD_DOTENV_FOR_DYNACONF`, `ENV_SWITCHER_FOR_DYNACONF`, `AUTO_CAST_FOR_DYNACONF`, and `MERGE_ENABLED_FOR_DYNACONF`. Environment option values are parsed with the same casting rules used for setting values.

`settings_file` and `settings_files` are aliases for one path or multiple paths. A multiple-path string may use comma or semicolon separators. A list is accepted directly.

## Source Loading Order

Source loading establishes the final configuration state by layering contributions from files, environment variables, hooks, and runtime updates in a deterministic order.

1. Explicit constructor defaults and Dynaconf defaults.
2. `preload` files.
3. `settings_file` or `settings_files`.
4. `.secrets.*` files when configured or discovered as settings files.
5. Automatically discovered local files matching `name.local.extension` for configured files; local files are read at the end of the file-loading order for their corresponding configured files.
6. `includes` declared in constructor options, environment options, or `dynaconf_include` inside files.
7. Post-load hooks from `dynaconf_hooks.py`, Python settings-file decorators, and constructor `post_hooks`.
8. Environment variables from the configured prefix, provided the default env loader remains last in the configured loaders list.
9. Runtime assignments made with public update/set APIs.

Later sources override earlier scalar values. Dictionary and list values merge only when global merge mode or per-value merge markers request merging. The documented default loader list keeps `dynaconf.loaders.env_loader` last so environment variables have final override priority. If users customize `loaders`, keeping the env loader last preserves this priority; disabling or reordering loaders changes the configured source order.

Environment variables have priority over file values. Runtime updates have priority over previously loaded values until the object is reloaded or overwritten.

## File Loading

File loading reads configuration values from local files in supported formats, discovering files through path resolution and loading companion local files automatically.

**Supported formats.** Supported local settings file formats are:

- TOML: `.toml`
- YAML: `.yaml`, `.yml`
- JSON: `.json`
- INI/properties-style files: `.ini`, `.cfg`, `.properties` when the required parser is available
- Python settings modules/files: `.py`
- `.env` files when `load_dotenv=True`

File contents are loaded as settings keys. Python settings files expose only upper-case variables as settings. File text is decoded with the configured `encoding`, defaulting to UTF-8.

Relative `settings_files` are searched from the entry-point folder upward through parent directories and each visited `config/` directory. When `root_path` is set, search starts from that path. Absolute paths are loaded directly. Globs are accepted. For every configured file such as `settings.toml`, the loader also attempts `settings.local.toml` after the main file.

`preload` files are loaded before regular settings files. `includes` are loaded after regular settings files. Relative `preload` and `includes` paths are resolved against `root_path` when set, otherwise against the last discovered settings directory or current working directory according to the documented fallback.

Inside a settings file, `dynaconf_include` may be a string or list of strings and causes the referenced files/globs to be loaded as includes.

## Casting Tokens and Lazy Values

Casting tokens transform string values from files and environment variables into typed Python objects at access time.

**Available tokens.** When `auto_cast` is set to `True`, string values from files and environment variables can use casting tokens:

- `@int value`
- `@float value`
- `@bool value`
- `@json value`
- `@none value`
- `@str value`
- `@empty`
- `@format template`
- `@jinja template`
- `@get key [default] [cast]`
- `@read_file path [default]`
- string utilities: `@upper`, `@lower`, `@title`, `@capitalize`, `@strip`, `@lstrip`, `@rstrip`, `@split`, `@casefold`, `@swapcase`
- `@merge value`
- `@insert [index] value`
- `@del`

`@format` templates can interpolate from the process environment and from the current settings object, using names such as `{env[HOME]}` and `{this.DB_NAME}`. `@jinja` templates use Jinja-style expressions such as `{{env.HOME}}` and `{{this.DB_NAME}}` and may use documented filters such as `abspath`.

`@get` aliases another settings key lazily and preserves the referenced value's data type. It can provide a default and a cast token; malformed `@get` expressions raise the documented Dynaconf format error. `@read_file` reads text from an absolute path or a path relative to the current working directory and can provide a fallback default. Without a default, unreadable or missing files raise `FileNotFoundError` on access. `@read_file` composes with `@format`, `@jinja`, `@get`, and string utilities.

String utility tokens transform strings at access time. `@split` returns a list of words. `@strip`, `@lstrip`, and `@rstrip` remove whitespace as named. Case utilities perform the corresponding Python string transformation.

`add_converter(name, callable)` registers a custom token. For example `add_converter("path", Path)` makes `@path /tmp/file` return `Path("/tmp/file")`. Converters compose with other lazy tokens, so `@path @format {env[HOME]}/child` first resolves the format expression and then applies the converter.

**Disabled auto-cast.** When `auto_cast` is set to `False`, casting tokens are not interpreted and string values remain as raw strings. However, plain numeric environment-variable values are still parsed into their natural types (integers and floats). Explicit token syntax such as `@int 9900` remains as the literal string `"@int 9900"` when auto-cast is disabled.

## Accessing Settings

A settings object supports multiple access styles over the same state:

```python
settings.NAME
settings.name
settings["NAME"]
settings["database.host"]
settings.get("database.host", default=None)
settings("database.host", default=None)
settings.as_dict()
```

`get(key, default=None, dotted_lookup=True, sysenv_fallback=None)` returns the setting value or default. Dotted lookup traverses nested dictionaries when enabled. `dotted_lookup=False` treats dots as literal key characters. Files may disable dotted lookup for set operations with top-level `dynaconf_dotted_lookup: false`.

Nested dictionaries are exposed through attribute access and dictionary access. A nested mapping loaded as `DATABASE = {"HOST": "server.com"}` can be read as `settings.DATABASE.HOST`, `settings.database.host`, `settings["DATABASE"]["HOST"]`, and `settings.get("database.host")` when case-insensitive first-level access and dotted lookup are enabled.

Missing attribute access raises the normal missing-key error for settings. `get` returns the provided default.

**Dictionary representation.** `as_dict()` returns a dictionary representation of loaded user settings for the active environment. Internal Dynaconf settings are excluded unless the caller asks for all/internal values through the relevant public API or CLI option.

**Environment switching.** When `environments=True`, multiple environments can be active. The `env` argument accepts a single environment name or a comma-separated list of environment names; when comma-separated, environments are loaded in listed order so later environments override earlier ones. `setenv(env_name)` switches the active environment persistently. `using_env(env_name)` is a context manager that temporarily switches the active environment and restores the previous environment on exit. `from_env(env_name)` returns an isolated settings object for the specified environment without changing the original settings object's active environment. When `keep` is set to true on `from_env`, existing values from the current environment are preserved and the new environment's values overlay them.

**System-environment fallback.** When `sysenv_fallback` is set to `True`, missing keys fall back to reading unprefixed system environment variables. When `sysenv_fallback` is a list of names, only those named environment variables are allowed as fallbacks.

**Unknown environment variables.** When `ignore_unknown_envvars` is set to `True`, only environment variables matching keys already defined in files are loaded; unknown prefixed environment variables are silently ignored.

## Runtime Updates

Settings can be updated at runtime with public dictionary-like and settings-like operations such as:

```python
settings.set("KEY", value)
settings.update({"KEY": value}, validate=False)
settings.load_file(path, validate=False, run_hooks=True)
```

Runtime updates use the same key normalization, dotted lookup, nested structure, merge markers, and validation-on-update behavior as loaded sources. When `validate_on_update=False`, updates do not validate by default. When `validate_on_update=True`, updates validate and raise on the first validation failure. When `validate_on_update="all"`, updates accumulate all validation errors.

Per-call `validate=True` triggers first-error validation. Per-call `validate="all"` triggers accumulated validation.

Variables listed in `fresh_vars` are reloaded from source whenever accessed rather than being served only from cached state.

`load_file(path=...)` accepts a single path, a list of paths, or a comma/semicolon-separated string. Relative paths use `root_path` resolution. Data loaded by `load_file` is not persistent across `setenv`, `using_env`, `reload`, or `configure` unless the program loads it again or makes it part of configured includes. `load_file(env=False)` loads top-level file variables without interpreting environment sections. Calls to `load_file` are visible in inspection history.

## Merge Semantics

By default, later sources override earlier values with the same key. Only dictionaries and lists can merge. Scalars always override.

Global `merge_enabled=True` makes later dictionaries and lists merge into existing values by default. Without global merge mode, values can request merging with local markers:

- A dictionary may include `dynaconf_merge=true`.
- A dictionary may include `dynaconf_merge={...}` to contribute only the marked nested data.
- A list may include `"dynaconf_merge"` to append/merge list values.
- A list may include `"dynaconf_merge_unique"` to merge without duplicates.
- Environment variables may start with `@merge`, such as `DYNACONF_DATABASE='@merge {password=1234}'` or `DYNACONF_PLUGINS='@merge plugin_a,plugin_b'`.
- Dunder keys such as `DATABASE__password=1234` merge nested dictionary levels rather than replacing the whole parent object.
- `@insert [index] value` inserts an item into an existing list. Omitting the index inserts at position 0. The inserted value may be a scalar, TOML-like dictionary, or explicit `@json` value.
- `@del` deletes a nested value when used in a nested environment variable such as `DYNACONF_DATABASES__default__ARGS='@del'`.

Merge marker keys and marker list items are not part of the final user-visible value.

Local files matching `*.local.*` load after their corresponding base files. They override by default. A top-level `dynaconf_merge=true` in a local file marks the entire local file for merge. Environment-level `dynaconf_merge=true` marks that environment section for merge.

For unique list merge, duplicate values are not repeated; the resulting order follows Dynaconf's documented merge behavior where uniqueness can change simple append order.

## Validators

`Validator(*names, **rules)` creates validation rules for one or more keys. Names may use dotted paths such as `"DATABASE.PORT"`.

Documented validation rules include:

- existence: `must_exist=True` and `must_exist=False`; `required=True` is an alias for `must_exist=True`
- equality: `eq`, `ne`
- comparisons: `gt`, `gte`, `lt`, `lte`
- type, identity, and membership: `is_type_of`, `identity`, `is_in`, `is_not_in`, `cont`
- length: `len_eq`, `len_ne`, `len_min`, `len_max`
- string predicates: `startswith`, `endswith`
- custom `condition=callable`
- conditional validation: `when=Validator(...)`
- `cast=callable`
- `default=value_or_callable`
- `env=...` to target an environment
- `messages={...}` for custom messages
- `apply_default_on_none=True`
- `description=...`

Validators passed to `Dynaconf(validators=[...])` are registered on the settings object. They are evaluated lazily on first access to settings, on explicit validation calls, or on updates when validation-on-update is enabled.

`settings.validators.register(...)` registers additional validators. `settings.validators.validate()` raises `ValidationError` on the first error. `settings.validators.validate_all()` evaluates all possible errors and raises one `ValidationError` whose `details` contains accumulated error data.

Validators compose with `|` and `&`. `a | b` succeeds if either validator succeeds. `a & b` succeeds only if both validators succeed.

Selective validation is public behavior. `Dynaconf(validate_only=...)`, `Dynaconf(validate_exclude=...)`, `settings.validators.validate(only=..., exclude=...)`, and `settings.validators.validate_all(only=..., exclude=...)` limit validation to settings paths. Exclusions apply after selections. Path matching starts at the top-level setting and matches descendants by prefix. `validate_only_current_env=True` or equivalent validator-list arguments skip validators for environments other than the active one.

Validator defaults set missing values. Static defaults are assigned directly. Callable defaults that accept `(settings, validator)` are evaluated during validation. Lazy defaults can receive context containing `env` and `this` according to documented lazy-value behavior.

When a validator has `cast`, the callable receives the current value and the returned value is written back to the same setting path before later validators for that path run. Multiple casts for the same field are cumulative and order-sensitive.

Validation error messages include the key name, failed operation, expected value where relevant, actual value where relevant, and environment. Custom messages may interpolate documented variables such as `{name}`, `{env}`, `{operation}`, `{op_value}`, and `{value}`.

`dynaconf_validators.toml` files define validators for the CLI and settings folder. They support environment sections, dotted key names, and the same TOML parsing used by settings values.

YAML empty values parse as `None`. Validator defaults are not applied to `None` unless `apply_default_on_none=True` globally or on the validator. YAML value `@empty` represents Dynaconf's empty sentinel for default handling.

## Hooks

Hooks run after regular loading and can contribute data based on the settings already loaded.

A module named `dynaconf_hooks.py` in the same path as a settings file may define:

```python
def post(settings):
    return {"KEY": "value", "dynaconf_merge": True}
```

The `post` function receives a read-only settings object and returns a dictionary to merge into settings.

Constructor `post_hooks` accepts one callable or a list of callables. Each callable receives settings and returns data to merge.

Python settings files may use:

```python
from dynaconf import post_hook

@post_hook
def hook(settings):
    return {"KEY": "value"}
```

Decorated hooks are collected when the Python settings file is loaded. `load_file(..., run_hooks=False)` collects without immediately running hooks. `run_hooks=True` executes collected hooks. Hooks already executed are not run again unless explicitly made callable again according to public hook behavior.

## Inspection and History

Every loaded data contribution records source metadata sufficient for public inspection:

- loader name such as `toml`, `yaml`, `py`, `env_global`, `validation_default`, or `set_method`
- identifier such as filename, environment variable source, or update source
- environment name
- whether the contribution was merged
- contributed value data

`get_history(settings, key=None, env=None, ...)` returns a list of history records. `inspect_settings(settings, key=None, env=None, print_report=False, dumper=None, to_file=None, ...)` returns a report dictionary containing filtering header data, current value information, and history records. With `print_report=True`, it prints the report using a selected dumper such as JSON or YAML. With `to_file`, it writes the dumped report.

History can be ordered newest-first or oldest-first and can be limited. Internal loaders are excluded unless requested. Filtering by key or environment narrows both the current value and the history.

The CLI `dynaconf inspect` exposes the same information with options for key, environment, output format, limit, ordering, internal inclusion, and debug mode.

## CLI Behavior

The console command `dynaconf` accepts:

```text
dynaconf [OPTIONS] COMMAND [ARGS]...
```

Global options include:

- `-i, --instance TEXT`: import path to a settings instance, required by commands except `init` unless supplied through `INSTANCE_FOR_DYNACONF`
- `--version`
- `--docs`
- `--banner`
- `--help`

`dynaconf init` creates a project configuration in the current directory or `--path`. It writes a settings file and `.secrets` file in the requested format (`ini`, `toml`, `yaml`, `json`, `py`, or `env`), writes `-v/--vars` entries to the settings file, writes `-s/--secrets` entries to the secrets file, and updates `.gitignore` to ignore `.secrets.*`. `-i/--instance` is not valid for `init`.

`dynaconf get KEY` prints the raw value for a single key. If the value is a dict, list, or tuple, it is printed as valid JSON. `--default` provides a fallback. `--env` selects an environment. `--unparse` prints values with Dynaconf marker syntax where applicable. Missing keys without defaults exit with status 1.

`dynaconf list` prints user-defined settings by default. `--all` includes internal settings. `--env`, `--key`, and `--loader` filter output. `--json` prints valid JSON. `--output FILE` writes the listed values in the format inferred from the file extension (`yaml`, `toml`, `ini`, `json`, or `py`). `--output-flat` writes flat Python output instead of nesting by environment where applicable.

`dynaconf write FORMAT` writes values to a configured source. Required local file formats are `ini`, `toml`, `yaml`, `json`, `py`, and `env`. `-v/--vars` writes regular values. `-s/--secrets` writes secret values. `--path` selects the output path. `--env` selects the environment section for file output. The documented Redis and Vault write targets are optional integration targets and are non-goals for the local core scope.

`dynaconf validate` reads validators from `dynaconf_validators.toml` in the settings folder and validates the selected settings instance. It exits with status 0 on success and nonzero on validation failure.

`dynaconf inspect` reports loading history and debug information. Options include `--key`, `--env`, `--format yaml|json|json-compact`, `--old-first`, `--limit`, `--all`, `--report-mode inspect|debug`, and `--verbose`.

## State Model

One settings object holds a canonical value view for its active environment. File loaders, environment variables, hooks, validator defaults/casts, and runtime updates contribute ordered values to that view. Attribute access, item access, dotted lookup, `as_dict()`, validation, inspection/history, and CLI reads are public projections of the same state.

Changing the active environment changes which layered contributions participate without creating contradictory accessor views. Merge markers and casting tokens control how source contributions are interpreted; they are not retained as ordinary user settings after loading.

## Error Semantics

Invalid dynamic token expressions raise the documented Dynaconf format error where public docs specify it, such as malformed `@get`. Invalid file syntax or unsupported formats must fail with a clear parse/format exception rather than silently producing partial settings.

Validation failures raise `ValidationError`. `validate()` raises the first failure. `validate_all()` raises after collecting all failures and exposes accumulated details.

Missing CLI keys without defaults return process status 1. Successful CLI validation returns status 0. Failed CLI validation returns nonzero status and reports validation failure text.

Unsupported optional integrations such as Redis, Vault, Django, and Flask should fail gracefully with import/configuration errors unless those integrations are explicitly implemented. They are not required for the local core behavior.

## Cross-View Invariants

1. A setting loaded from any source has one canonical final value for the active environment. Attribute access, item access, dotted `get`, `as_dict`, validators, CLI `get/list`, and inspection current value must agree.
2. Source precedence is observable: defaults are overridden by files, files by local/secrets/includes according to load order, and all file values by matching environment variables. Runtime updates override prior loaded values until reloaded or overwritten.
3. Casting happens before validators and before user-visible final access. An environment string such as `DYNACONF_PORT=9900` must validate as an integer when the validator expects numeric comparison.
4. Environment switching changes the same underlying settings object view consistently. Accessors, validators, CLI `--env`, and history must identify the active or requested environment.
5. Merge markers affect only merge behavior and never appear as user settings. Merged dictionaries/lists must be visible identically through nested attributes, item access, `as_dict`, validators, and CLI output.
6. Validator casts and defaults mutate the same settings state observed by later validators and readers. A cast pipeline cannot be local only to validation.
7. Hooks run after their prerequisite sources are loaded and their returned data participates in the same merge, validation, access, and history behavior as file data.
8. Inspection history must explain the currently visible value with enough source metadata to distinguish file, envvar, validation default, hook, and runtime update contributions.

## Public Interface

### Import Surface

The following names are public and importable:

```python
from dynaconf import Dynaconf, LazySettings, settings
from dynaconf import Validator, ValidationError
from dynaconf import add_converter, post_hook
from dynaconf import inspect_settings, get_history
```

The package provides a console command named `dynaconf`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Dynaconf` | class | Primary settings object constructor |
| `LazySettings` | class | Lazy settings object constructor |
| `settings` | object | Global backwards-compatible settings object |
| `Validator` | class | Validation rule descriptor |
| `ValidationError` | exception | Raised for validation failures |
| `add_converter` | function | Register a custom casting token |
| `post_hook` | decorator | Mark a Python settings-file function as a post-load hook |
| `inspect_settings` | function | Return a loading-history report for a settings object |
| `get_history` | function | Return source history records for a settings object |

Settings objects support attribute access, item access, dotted `get`, callable access, `as_dict()`, runtime `set` and `update`, `load_file`, `setenv`, `using_env`, `from_env`, environment switching, validator registration, and validation calls as described in the behavior sections above.

### CLI Entry Points

The installed `dynaconf` console command is supported. `python -m dynaconf` is not part of this contract. Successful `get`, `list`, `write`, `init`, `inspect`, and validation operations return status `0`; missing keys without defaults and failed validation return nonzero status as described above.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Source loading, environment switching, runtime updates, validation, hooks, history, and CLI output should all derive from the same canonical settings state. File parser choices and internal loader classes may differ as long as the public precedence, casting, merge, error, and cross-view behavior remains consistent.
