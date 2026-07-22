# Dynaconf Core Settings Behavior Specification

## Product Overview

Implement a Python configuration management library compatible with Dynaconf's documented core behavior. A user creates a settings object, loads configuration from local files and environment variables, optionally separates values by environment, validates the resulting settings, and observes the same final state through Python accessors, validators, inspection/history utilities, and CLI commands.

The implementation must be usable without network services. Redis, Vault, Django, and Flask integrations are non-goals unless explicitly exercised through their public optional wrappers. The core scope is the local settings engine.

## Scope

This specification covers local file loading, environment variables, layered environments, dynamic casting tokens, Python accessors, runtime updates, merge behavior, validators, post-load hooks, inspection/history, and the local `dynaconf` CLI. Network-backed stores and framework integrations are outside the required core.

## Public Import Surface

The following names are public and importable:

```python
from dynaconf import Dynaconf, LazySettings, settings
from dynaconf import Validator, ValidationError
from dynaconf import add_converter, post_hook
from dynaconf import inspect_settings, get_history
```

`Dynaconf` and `LazySettings` construct settings objects. `settings` is a global backwards-compatible settings object. `Validator` describes validation rules. `ValidationError` is raised for validation failures and exposes accumulated details when all errors are collected. `add_converter` registers custom casting tokens. `post_hook` marks Python settings-file functions as hooks. `inspect_settings` and `get_history` report how values were loaded.

The package provides a console command named `dynaconf`.

## Product State Model

One settings object holds a canonical value view for its active environment. File loaders, environment variables, hooks, validator defaults/casts, and runtime updates contribute ordered values to that view. Attribute access, item access, dotted lookup, `as_dict()`, validation, inspection/history, and CLI reads are public projections of the same state.

Changing the active environment changes which layered contributions participate without creating contradictory accessor views. Merge markers and casting tokens control how source contributions are interpreted; they are not retained as ordinary user settings after loading.

## Constructing Settings

`Dynaconf(...)` accepts documented configuration options as keyword arguments. The following options are part of the public contract:

```python
settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_file=None,
    settings_files=None,
    root_path=None,
    environments=False,
    env="development",
    default_env="default",
    env_switcher="ENV_FOR_DYNACONF",
    load_dotenv=False,
    dotenv_path=".",
    dotenv_override=False,
    encoding="utf-8",
    auto_cast=True,
    dotted_lookup=True,
    lowercase_read=True,
    merge_enabled=False,
    nested_separator="__",
    preload=[],
    includes=[],
    skip_files=None,
    secrets=None,
    fresh_vars=[],
    loaders=["dynaconf.loaders.env_loader"],
    core_loaders=["YAML", "TOML", "INI", "JSON", "PY"],
    validators=[],
    validate_on_update=False,
    apply_default_on_none=False,
    ignore_unknown_envvars=False,
    sysenv_fallback=False,
    post_hooks=None,
    filtering_strategy=None,
)
```

Configuration options may also be supplied through environment variables named as upper-case option names with `_FOR_DYNACONF` suffix, such as `ENVVAR_PREFIX_FOR_DYNACONF`, `SETTINGS_FILES_FOR_DYNACONF`, `ENVIRONMENTS_FOR_DYNACONF`, `LOAD_DOTENV_FOR_DYNACONF`, `ENV_SWITCHER_FOR_DYNACONF`, `AUTO_CAST_FOR_DYNACONF`, and `MERGE_ENABLED_FOR_DYNACONF`. Environment option values are parsed with the same casting rules used for setting values.

`settings_file` and `settings_files` are aliases for one path or multiple paths. A multiple-path string may use comma or semicolon separators. A list is accepted directly.

## Source Loading Order

The final settings state is produced by loading sources in a deterministic order:

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

Supported local settings file formats are:

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

## Layered Environments

When `environments=False`, top-level file keys become settings directly.

When `environments=True`, the first-level sections or top-level mapping keys are environment names. The active environment is controlled by `env`, by the environment variable named by `env_switcher`, or by `ENV_FOR_DYNACONF` by default. Environment names are case-insensitive for selection.

`default_env` names the fallback environment. Values in the active environment override values in the default environment. `[global]` values apply across environments. Custom environment names such as `testing`, `staging`, or `anything` are accepted.

`env` may be a comma-separated list. Multiple active environments are loaded in the order specified; later active environments override earlier ones unless merge rules apply.

The active environment can be changed at runtime with public environment-switching behavior such as `setenv(...)` or by constructing a new settings object with a different `env`. Accessors, validators, CLI output, and history must reflect the active environment.

`from_env(name, keep=False, **options)` returns a new isolated settings object for another environment and leaves the original object unchanged. With `keep=True`, previously loaded values are chained into the new object and later environments override earlier ones. `setenv(name=None)` changes the existing settings object in place; calling it without a name returns to the previous/default working environment. `using_env(name)` is a context manager that temporarily switches the existing object for the context scope and restores it afterwards.

## Environment Variables

Environment variables override settings when their names match the configured prefix. With `envvar_prefix="DYNACONF"`, `DYNACONF_PORT=9900` sets `PORT`. Custom prefixes are accepted. A comma-separated prefix list is accepted, and variables from all listed prefixes are loaded. With `envvar_prefix=False`, unprefixed environment variables are considered setting variables.

Only upper-case prefixed environment variables are loaded. First-level setting access is case-insensitive by default, so `settings.PORT`, `settings.port`, `settings["PORT"]`, and `settings.get("port")` observe the same first-level key when lowercase reads are enabled.

Environment variable values are parsed as TOML-like values:

- `42` becomes an integer.
- `42.1` becomes a float.
- `true` and `false` become booleans.
- `['red', 'green']` becomes a list.
- `{name='Bruno'}` becomes a dictionary.
- quoted strings remain strings; double quoting can force strings such as `"'42'"`.

Boolean strings `True` and `False` are normalized to TOML booleans for top-level envvar values unless forced to strings.

Nested keys are expressed with the nested separator, default `__`. For example `DYNACONF_DATABASE__ARGS__timeout=30` produces `DATABASE = {"ARGS": {"timeout": 30}}`. List indexes can be expressed with the documented index separator `___`, such as `WORKERS___0__Address`.

When `ignore_unknown_envvars=True`, prefixed environment variables are loaded only for keys already introduced by files, preload, or includes. When `sysenv_fallback=True`, `settings.get()` may fall back to unprefixed system environment variables for missing keys. A list value for `sysenv_fallback` restricts which names can fall back.

When `load_dotenv=True`, `.env` files are loaded. `dotenv_override` controls whether `.env` values override already exported environment variables.

## Casting Tokens and Lazy Values

When `auto_cast=True`, string values from files and environment variables can use casting tokens:

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

When `auto_cast=False`, casting tokens are not interpreted except where a public API explicitly requests parsing.

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

`as_dict()` returns a dictionary representation of loaded user settings for the active environment. Internal Dynaconf settings are excluded unless the caller asks for all/internal values through the relevant public API or CLI option.

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

## Representative Workflow

Create `settings.toml` with a default service name and development port, then set `DYNACONF_PORT` to a different integer. Construct `Dynaconf(settings_files=["settings.toml"], environments=True, env="development")`, validate that `PORT` is an integer, and update a nested runtime key with `set`. Attribute access, dotted `get`, `as_dict()`, `get_history`, `inspect_settings`, and `dynaconf get/list` must report the same final values. Switching to another declared environment must expose that layer without mutating the original development values.

## Invocation Protocol

The installed `dynaconf` console command is supported. `python -m dynaconf` is not part of this contract. Successful `get`, `list`, `write`, `init`, `inspect`, and validation operations return status `0`; missing keys without defaults and failed validation return nonzero status as described above.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Non-Goals

- Do not implement network-backed Redis or Vault behavior for the local core scope.
- Do not implement Django or Flask extension behavior unless explicitly selected in a later scope.
- Do not recreate upstream test helper packages or repository-local fixtures.
- Do not expose upstream internal implementation modules as required API.
- Do not implement undocumented private helpers or private attributes.
- Do not require internet access.

## Implementation Guidance

Source loading, environment switching, runtime updates, validation, hooks, history, and CLI output should all derive from the same canonical settings state. File parser choices and internal loader classes may differ as long as the public precedence, casting, merge, error, and cross-view behavior remains consistent.

