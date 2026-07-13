# MiniDynaconf Public Product Packet

## Overview

Build `minidynaconf.py`, a dependency-free Python module for layered application configuration. It is inspired by Dynaconf's public configuration-management model: settings can come from defaults, configuration files, environment variables, secrets files, and runtime overrides, then be accessed through one settings object.

The module must be importable from the solution directory:

```python
from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError
```

Use only the Python standard library.

Hidden tests are split into feature-pure unit tests and cross-feature system tests. Unit tests establish local primitives: source loading, environment parsing, explicit casts, nested attribute proxies, validator behavior, runtime mutation, import/export helpers, reload, and configure. System tests then exercise those primitives through one canonical configuration tree after configured layers, incremental imports, deletion, validator defaults, export views, reloads, and atomic failures have been applied. A missing primitive should be reported as a prerequisite failure, not multiplied across system rows unless the downstream canonical tree actually diverges.

## Feature Set

The product has seven feature modules:

1. Settings file loading.
2. Environment variable overrides.
3. Secrets file loading.
4. Type casting and nested-key addressing.
5. Validators.
6. Runtime settings API.
7. Lifecycle operations: import, export, reload, configure, and atomic recovery.

Each feature must work on its own, but all features share one canonical configuration tree. That tree is the product's fact source. Attribute access, item access, dotted lookup, `exists`, `as_dict`, `export`, validators, imported dictionaries, exported files, and reloads are derived views or operations over that same tree. A key produced by a file loader, a dotenv import, an environment variable, a secrets file, a validator default, a runtime override, or an imported dictionary must be observable through the same access API and must participate in the same casting and validation semantics.

## Data Model

Settings are stored as a nested mapping with case-insensitive top-level and nested key access. Public lookup must treat `database.host`, `DATABASE.HOST`, attribute access, item access, dotted lookup, and exported dictionary keys as references to the same logical setting. `as_dict()` exports a deep copy using uppercase canonical keys at every mapping level, so exported configuration can be written to JSON and loaded again without changing the logical settings state.

Nested keys are addressed with dot notation in the Python API and with double underscores in environment variable names. A nested assignment must merge into existing mappings instead of replacing unrelated sibling keys.

Values may be scalars, lists, or dictionaries. Supported scalar types are strings, integers, floats, booleans, and `None`. Lists and dictionaries may contain supported scalar values and nested containers.

Layer priority is:

1. constructor defaults;
2. settings files, in the order provided;
3. environment variables;
4. secrets files, in the order provided;
5. runtime overrides, imported dictionaries, and assignments.

Higher-priority layers override lower-priority layers for the same logical key. Nested dictionaries merge recursively, so overriding `DATABASE.PORT` does not remove `DATABASE.HOST`.

## Global Invariants

- One canonical configuration tree backs all public projections: attribute proxies, item access, dotted `get`, `exists`, validator inputs, `as_dict`, exported JSON, and reloaded settings.
- Dot-path access and dictionary-style access are aliases over the same case-insensitive logical path. A mutation through one path must be visible through every other public path.
- Layer priority is global and independent of source format: defaults < settings files < environment/dotenv < secrets files < runtime assignments.
- Nested mappings are merged recursively across files, environment variables, secrets, validator defaults, and runtime updates. Overriding one leaf must not delete unrelated siblings.
- Type casting is applied before values enter the canonical tree for text sources and explicit cast tokens, and validators inspect the cast final value.
- Validators inspect the fully merged settings object, not an individual source layer. Callable validators may rely on sibling values from other sources.
- Runtime assignments use the same casting, nested-key, recursive-merge, and validation behavior as initial loading.
- `as_dict()` and `export()` are export views, not live references. Mutating their returned dictionaries must not mutate settings.
- `load_file()` and `load_env_file()` are durable lifecycle imports for the settings object. Once a file or dotenv import succeeds, a later `reload()` rebuilds from configured sources plus those successful lifecycle imports.
- Runtime `set`, `update`, `import_dict`, and `delete` operations are overlays above configured and imported sources. A plain `reload()` discards those runtime-only overlays and deletion tombstones, then rebuilds from durable sources.
- Export/reload is a semantic round trip: writing `export()` or `as_dict()` to a supported file format and loading it into a new settings object must preserve logical keys, values, nested structure, and access behavior.
- `configure()` replaces loader configuration, clears prior lifecycle imports, runtime overlays, deletion tombstones, and derived validator defaults, then reloads from the new configuration.
- Failed validation, failed explicit casts, malformed file loads, malformed dotenv imports, failed validated imports, and failed configure attempts are atomic. After failure, all public projections and loader lifecycle state must still agree with the previous valid state.
- Missing keys, deleted keys, and default fallbacks must behave consistently across attribute access, item access, `get`, `exists`, and `as_dict`. Falsey values such as `False`, `0`, empty strings, empty lists, and empty dictionaries are existing settings.

## Settings File Loading

`MiniDynaconf(settings_files=None, defaults=None, envvar_prefix="APP", environments=False, env=None, secrets_files=None, validators=None, load_dotenv=False)` constructs a settings object.

`settings_files` is a path or list of paths. Supported file formats are `.toml`, `.ini`, `.yaml`, `.yml`, `.json`, and `.py`. YAML support only needs a practical subset: mappings, nested mappings by indentation, lists in bracket form, and scalar values. Python settings files should execute in an isolated namespace and load public uppercase variables.

TOML and INI files may contain sections. Sections become nested dictionaries unless environment switching is enabled. JSON files load object values. Empty files load as no settings. Missing files are ignored unless explicitly loaded later with strict mode.

`load_file(path, *, env=None, silent=True)` loads one additional file after construction. A successful load becomes part of the object's durable source lifecycle: later `reload()` calls should read that file again, so changes on disk are observed. With `silent=False`, malformed files and missing paths should raise `SettingsError`. With `silent=True`, missing files are ignored, but malformed existing files should still raise `SettingsError`.

If `environments=True`, files may contain named top-level environments such as `default`, `development`, `testing`, and `production`. The active environment is chosen from the constructor `env` argument or the `ENV_FOR_DYNACONF` environment variable, falling back to `default`. Values from `default` load first; values from the active environment load over them.

## Environment Variable Overrides

Environment variables are read from `os.environ` using `envvar_prefix`. A variable belongs to the settings object when its name starts with the prefix followed by an underscore. The prefix itself is not part of the logical key.

The remainder of the variable name becomes the logical setting name. Double underscores indicate nested keys. Environment variable keys are case-insensitive.

Environment variable values are strings at the OS boundary but must be cast using the module's casting rules before storage. Environment variables have higher priority than settings files and lower priority than secrets and runtime assignments.

When `load_dotenv=True`, `.env` files may be loaded through `load_env_file(path)`. Explicit calls to `load_env_file(path)` should also be supported. The file format is one `KEY=VALUE` pair per line with optional surrounding quotes, blank lines, and comment lines. Values loaded from dotenv obey the same prefix, nested-key, priority, and casting rules as process environment variables. A successful dotenv import is durable for the object and should be replayed by later `reload()` calls.

## Secrets Loading

`secrets_files` is a path or list of paths loaded after environment variables. Secrets files support the same file formats and nested merge rules as normal settings files. Secrets are not exposed through a separate API; they become settings in the shared namespace.

Secrets override defaults, settings files, and environment variables. Runtime overrides can still override secrets.

## Type Casting

Values loaded from text sources should be cast into Python values before storage when their syntax unambiguously represents a supported type.

Supported casts:

- booleans from common true/false spellings and TOML-style boolean literals;
- integers and floats from numeric literals;
- `None` from TOML-style null-equivalent spellings accepted by this product;
- quoted strings with surrounding single or double quotes removed;
- lists and dictionaries from JSON/TOML-style bracket and brace literals;
- explicit tokens of the form `@int`, `@float`, `@bool`, `@json`, `@none`, and `@str` followed by a value.

`@str` prevents automatic numeric, boolean, list, dictionary, or null casting. Invalid explicit casts must raise `SettingsError` and must not change existing settings.

Programmatic Python values supplied through defaults or runtime setters should preserve their Python type unless an explicit casting helper is used.

## Validators

`Validator(name, *, required=False, default=None, is_type_of=None, eq=None, ne=None, gt=None, gte=None, lt=None, lte=None, condition=None, messages=None)` describes a validation rule for one logical key.

`validate()` runs all registered validators against the current fully merged settings object. Constructor validators run after initial loading. `register_validator(validator)` adds a validator. `validate(key=None)` may run all validators or only validators for one key.

Validator behavior:

- if a key is missing and the validator has `default`, the default is set before the remaining checks;
- if a key is missing and `required=True`, validation fails;
- type checks use `is_type_of`;
- comparisons use Python comparison semantics against the cast value;
- `condition` is an optional callable that receives the value and the settings object and returns truthy for valid;
- failures raise `ValidationError`;
- exact exception message text is not public API, but the exception should identify the failed logical key.

A failed validation must not apply partial default values from later validators. A failed runtime update with validation enabled must leave the previous settings state unchanged.

## Runtime Settings API

The settings object must support:

- attribute access for valid Python identifier keys;
- item access with simple or dotted keys;
- `get(key, default=None, cast=None)`;
- `set(key, value, *, validate=False)`;
- `update(mapping, *, validate=False)`;
- `exists(key)`;
- `delete(key)`;
- `import_dict(mapping, *, validate=True, replace=False)`;
- `as_dict()`;
- `export(path=None)`;
- `reload()`;
- `configure(**kwargs)` for replacing loader options and reloading.

`get(..., cast=...)` can cast the returned value without mutating stored state. `as_dict()` returns a deep copy, not the live internal mapping. `export(path=None)` returns the same semantic deep-copy view and, when `path` is provided, writes JSON bytes that can be loaded again as a settings file. `import_dict(mapping, validate=True, replace=False)` applies a runtime overlay through the same normalization, casting, recursive merge, and validation path as other runtime updates. With `replace=True`, existing runtime overlays are replaced, but configured defaults/files/env/secrets remain underneath.

`delete(key)` removes the logical key from the current canonical projection, including keys supplied by lower-priority sources. Deletions are runtime-only tombstones: `reload()` clears them and rebuilds from durable sources.

`reload()` rebuilds settings from configured defaults, files, environment variables, secrets, and successful incremental imports from `load_file()` and `load_env_file()`. It preserves no ad hoc runtime assignments, `import_dict()` overlays, or `delete()` tombstones unless they were written back into a configured or imported source. `configure()` changes configuration options, clears previous incremental imports and derived state, and reloads from the new configuration.

Round-trip export uses the existing API: callers may serialize `as_dict()` or call `export(path)` and pass that JSON file back through `settings_files`. The reloaded object must expose the same logical settings through attribute, item, dotted, validator, and export views, even if file parsing and key normalization happen again.

## Error Behavior

All public product errors should use `SettingsError`, `ValidationError`, or a meaningful Python exception subclass. Exact error strings are not public API.

Malformed files, invalid explicit casts, failed validators, invalid runtime updates, failed validated imports, and failed configure attempts must be atomic: the settings object and its loader lifecycle remain in the previous valid state.

Missing values should not be confused with falsey values. `False`, `0`, empty strings, empty lists, and empty dictionaries are existing settings.

## Non-Goals

Do not implement every Dynaconf feature. Do not implement Redis/Vault integrations, Flask/Django extensions, remote loaders, plugin discovery, encryption, command-line tools, live file watchers, or full YAML/TOML language coverage beyond the compatibility subset described here.

## Evaluation Style

Unit tests exercise one feature module or primitive cluster at a time and set up state using only that module's operations or direct constructor inputs. Source loading, environment parsing, runtime mutation, explicit cast behavior, validator behavior, import/export helpers, reload, and configure are tested locally so the system layer does not repeat one primitive root across many rows.

System tests exercise interactions across at least two modules and focus on invariants over the canonical configuration tree: projection consistency, recursive merge behavior, priority ordering, casting before validation, validator visibility, export/reload round trip, durable source replay, runtime-overlay clearing, configure replacement, deletion tombstones, failed-lifecycle atomicity, and consistent public access. System tests should compare observable semantics rather than private storage choices or exact exception text. Lifecycle rows should prefer semantic access through `get`, `exists`, `as_dict`, `export`, validators, and reloaded objects so they reach the shared-tree invariant even when a separately unit-tested projection primitive such as nested attribute proxying is missing. A system row may assume the local primitives it depends on have passed, then assert that public access, validators, import/export, reload, source precedence, configure, and atomic failed updates all see the same logical tree.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`

The benchmark does not inspect private implementation details.
