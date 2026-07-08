# SQLFluff Specification

## Product Overview

SQLFluff is a configurable SQL linter, formatter, parser, and fixer. It reads SQL text or files, applies a selected SQL dialect and templater, reports lexing, templating, parsing, and linting issues, and can apply safe source edits for fixable linting violations.

SQLFluff is designed for command-line use and for embedding in Python applications. The command line works over files, directories, or stdin. The simple Python API works over SQL strings. The documented advanced API exposes configuration, linting, lexing, parsing, and metadata objects for applications that need more control.

## Scope

This specification covers:

- Installation as the `sqlfluff` Python package and the `sqlfluff` console command.
- CLI behavior for `version`, `rules`, `dialects`, `lint`, `fix`, `format`, `parse`, and `render`.
- The simple Python API exposed from `sqlfluff` and `sqlfluff.api`.
- The documented advanced API exposed from `sqlfluff.core`, especially `FluffConfig`, `Linter`, `Lexer`, `Parser`, dialect metadata, rule metadata, errors, and timing summaries.
- Configuration discovery, nested configuration precedence, explicit overrides, inline configuration directives, `.sqlfluffignore`, `ignore_paths`, `noqa`, warnings, and rule selection.
- The built-in `raw`, `jinja`, `python`, and `placeholder` templating behavior needed for linting, parsing, rendering, and fixing.
- User-observable violation records, fix behavior, parse output shape, rendered output, rule metadata, and dialect metadata.

## Installable Surface

SQLFluff is installed as a Python package named `sqlfluff`.

```text
pip install sqlfluff
```

The installed package provides the `sqlfluff` console command. The public import paths are:

```python
import sqlfluff
from sqlfluff.api import APIParsingError, fix, lint, list_dialects, list_rules, parse
from sqlfluff.core import (
    FluffConfig,
    Lexer,
    Linter,
    Parser,
    SQLBaseError,
    SQLFluffUserError,
    SQLLexError,
    SQLLintError,
    SQLParseError,
    SQLTemplaterError,
    TimingSummary,
    dialect_readout,
    dialect_selector,
)
from sqlfluff.core.config import (
    ConfigLoader,
    clear_config_caches,
    load_config_at_path,
    load_config_file,
    load_config_resource,
    load_config_string,
    load_config_up_to_path,
)
```

`sqlfluff.__version__` is the installed package version. SQLFluff supports Python 3.10 and newer.

## Public API

The top-level package exposes the simple API:

```python
sqlfluff.lint(
    sql: str,
    dialect: str | None = None,
    rules: list[str] | None = None,
    exclude_rules: list[str] | None = None,
    config: FluffConfig | None = None,
    config_path: str | None = None,
) -> list[dict[str, object]]

sqlfluff.fix(
    sql: str,
    dialect: str | None = None,
    rules: list[str] | None = None,
    exclude_rules: list[str] | None = None,
    config: FluffConfig | None = None,
    config_path: str | None = None,
    fix_even_unparsable: bool | None = None,
) -> str

sqlfluff.parse(
    sql: str,
    dialect: str | None = None,
    config: FluffConfig | None = None,
    config_path: str | None = None,
) -> dict[str, object]

sqlfluff.list_rules() -> list[RuleTuple]
sqlfluff.list_dialects() -> list[DialectTuple]
```

The same functions are importable from `sqlfluff.api`; `sqlfluff.api` also exposes `APIParsingError`. The simple API defaults to the `ansi` dialect when no dialect is supplied and no supplied config sets one. When a `config` object is supplied, it controls the operation and takes precedence over `dialect`, `rules`, `exclude_rules`, and `config_path`. When no `config` object is supplied, `config_path` may provide an additional `.sqlfluff`-style config file, and local project discovery is ignored for the simple API string operation.

`lint()` returns one dictionary per surfaced violation. Violation dictionaries use serializable Python values and include the rule or error code, description, warning flag, start position, and rule name when present. Linting violations include fix records when fixes are available and may include end positions when SQLFluff can identify an affected range. `fix()` returns the fixed SQL string if safe fixes can be applied; otherwise it returns the original SQL string. `parse()` returns a JSON-like parse representation for the primary parsed variant and raises `APIParsingError` if templating, lexing, or parsing violations prevent a clean parse.

`list_rules()` returns `RuleTuple(code, name, description, groups, aliases)` values for the available rule set. Rule references accepted by configuration and CLI options may be rule codes, rule names, aliases, or groups. `list_dialects()` returns `DialectTuple(label, name, inherits_from, docstring)` values sorted by dialect label.

The documented advanced API includes:

```python
FluffConfig(
    configs: dict | None = None,
    extra_config_path: str | None = None,
    ignore_local_config: bool = False,
    overrides: dict | None = None,
    plugin_manager: object | None = None,
    require_dialect: bool = True,
)

FluffConfig.from_root(extra_config_path=None, ignore_local_config=False, overrides=None, require_dialect=True) -> FluffConfig
FluffConfig.from_string(config_string: str, overrides=None) -> FluffConfig
FluffConfig.from_strings(*config_strings: str, overrides=None) -> FluffConfig
FluffConfig.from_path(path: str, extra_config_path=None, ignore_local_config=False, overrides=None, plugin_manager=None, require_dialect=True) -> FluffConfig
FluffConfig.from_kwargs(dialect=None, rules=None, exclude_rules=None, require_dialect=True) -> FluffConfig
FluffConfig.get(val: str, section: str | Iterable[str] = "core", default=None) -> object
FluffConfig.get_section(section: str | Iterable[str]) -> object
FluffConfig.set_value(config_path: Iterable[str], val: object) -> None
FluffConfig.make_child_from_path(path: str, require_dialect=True) -> FluffConfig
FluffConfig.diff_to(other: FluffConfig) -> dict

load_config_file(file_dir: str, file_name: str, configs: dict | None = None) -> dict
load_config_resource(package: str, file_name: str) -> dict
load_config_string(config_string: str, configs: dict | None = None, working_path: str | None = None) -> dict
load_config_at_path(path: str) -> dict
load_config_up_to_path(path: str, extra_config_path: str | None = None, ignore_local_config: bool = False) -> dict
clear_config_caches() -> None

Linter(config=None, formatter=None, dialect=None, rules=None, user_rules=None, exclude_rules=None)
Linter.rule_tuples() -> list[RuleTuple]
Linter.render_string(in_str: str, fname: str, config: FluffConfig, encoding: str) -> RenderedFile
Linter.render_file(fname: str, root_config: FluffConfig) -> RenderedFile
Linter.parse_string(in_str: str, fname="<string>", config=None, encoding="utf-8", parse_statistics=False) -> ParsedString
Linter.parse_path(path: str, parse_statistics=False) -> Iterator[ParsedString]
Linter.lint_string(in_str="", fname="<string input>", fix=False, config=None, encoding="utf8") -> LintedFile
Linter.lint_string_wrapped(string: str, fname="<string input>", fix=False, stdin_filename=None) -> LintingResult
Linter.lint_path(path: str, fix=False, ignore_non_existent_files=False, ignore_files=True, processes=None) -> LintedDir
Linter.lint_paths(paths: tuple[str, ...], fix=False, ignore_non_existent_files=False, ignore_files=True, processes=None, apply_fixes=False, fixed_file_suffix="", fix_even_unparsable=False, retain_files=True) -> LintingResult

Lexer(config=None, last_resort_lexer=None, dialect=None)
Lexer.lex(raw: str | TemplatedFile) -> tuple[tuple[object, ...], list[SQLLexError]]

Parser(config=None, dialect=None)
Parser.parse(segments, fname=None, parse_statistics=False) -> parsed SQL representation | None

dialect_selector(name: str) -> Dialect
dialect_readout() -> Iterator[DialectTuple]
```

`Linter` may be constructed with a `FluffConfig` or with convenience arguments such as `dialect`, `rules`, and `exclude_rules`, but not both at the same time. `Lexer` and `Parser` may be constructed with a `FluffConfig` or a dialect name, but not both. `Lexer.lex()` returns lexed SQL segments plus lexing violations for text that cannot be tokenized under the active dialect. `FluffConfig` requires a dialect by default; callers may defer that requirement with `require_dialect=False` when a later path-specific config is expected to provide the dialect.

The config loading functions return nested dictionaries suitable for constructing a `FluffConfig`. `load_config_file()` treats `pyproject.toml` as TOML and other supported file names as ini-style SQLFluff config. `load_config_resource()` loads a config file from an importable package resource and resolves any config paths relative to the current working directory. `load_config_string()` parses an ini-style config string and resolves relative paths against `working_path` or the current working directory. `load_config_at_path()` loads every supported config file in a directory, with `pyproject.toml` taking highest precedence, followed by `.sqlfluff`, `pep8.ini`, `tox.ini`, and `setup.cfg`. `load_config_up_to_path()` layers user, project, path, and extra config in the same precedence order used by file operations. `clear_config_caches()` clears cached config reads so subsequent loads see changed files.

`ConfigLoader` remains importable from `sqlfluff.core.config` for compatibility. New code should use the module-level config loading functions directly.

`LintedFile`, `LintedDir`, `LintingResult`, `ParsedString`, `ParsedVariant`, `RenderedFile`, `RuleTuple`, and `DialectTuple` are public result objects used by the advanced API. They provide user-facing methods such as `get_violations()`, `num_violations()`, `is_clean()`, `fix_string()`, `as_records()`, `stats()`, `persist_changes()`, `check_tuples()`, `root_variant()`, and `violations`.

`TimingSummary` collects timing dictionaries and returns per-step summaries with count, sum, minimum, maximum, and average.

## Command-Line Behavior

The command line is invoked as:

```text
sqlfluff [OPTIONS] COMMAND [ARGS]...
```

The public commands are:

- `sqlfluff version`: prints the installed version. With verbosity, it also shows the effective configuration.
- `sqlfluff rules`: prints the current rule metadata using the active configuration.
- `sqlfluff dialects`: prints available dialect labels, display names, inheritance, and descriptions.
- `sqlfluff lint [PATHS]...`: lints files, directories, or `-` for stdin.
- `sqlfluff fix [PATHS]...`: lints and applies safe fixes to files, directories, or stdin.
- `sqlfluff format [PATHS]...`: applies a curated formatting-focused subset of fixable rules; explicit `--rules` is not accepted for this command, while exclusions still apply.
- `sqlfluff parse PATH`: parses one file, directory, or `-` for stdin and prints the parse result.
- `sqlfluff render PATH`: renders one file or stdin through the configured templater and prints the rendered SQL.

Common command options include verbosity (`-v`, stackable), color control, dialect, templater, rules, excluded rules, additional config path, ignoring local config, encoding, ignored error families, logger selection, `--disable-noqa`, `--disable-noqa-except`, `--library-path`, and `--stdin-filename`. Linting and fixing commands accept process-count, progress-bar, timing, unused-ignore warning, and `.sqlfluffignore` bypass options.

`lint` supports output formats `human`, `json`, `yaml`, `sarif`, `github-annotation`, `github-annotation-native`, and `none`. `--write-output` writes the serialized output to a file. `--nofail` makes lint exit successfully even when violations are found. GitHub annotation output respects configured warnings by emitting warning-only rules as notices.

`parse` supports `human`, `json`, `yaml`, and `none`. `--code-only` omits non-code elements from the parse projection. `--include-meta` includes meta segments and, in JSON/YAML output, position fields for segments. `--nofail` makes parse exit successfully even when violations are found.

Command-line exit codes are part of the public CLI contract: `0` means the operation completed and no failing issues were found, `1` means the operation completed but issues were found, and `2` means the operation could not be completed because of a user-facing or internal error.

## Configuration Behavior

SQLFluff accepts configuration from command-line options, configuration files, explicit Python config objects, and in-file directives. Configuration files may be `setup.cfg`, `tox.ini`, `pep8.ini`, `.sqlfluff`, or `pyproject.toml`.

For cfg-style files, SQLFluff reads sections beginning with `sqlfluff`, using colons to represent nested sections such as `[sqlfluff:rules:capitalisation.keywords]`. For `pyproject.toml`, SQLFluff reads sections under `tool.sqlfluff`, using dots for nested paths such as `[tool.sqlfluff.rules.capitalisation.keywords]`.

For a file operation, SQLFluff builds the effective configuration in this order, with later values overriding earlier values:

1. Built-in default configuration.
2. User app configuration directory.
3. User home directory.
4. Directories between the user home directory and current working directory, when applicable.
5. Current working directory.
6. Directories between the current working directory and the SQL file being processed.
7. The directory containing the SQL file.
8. Any explicit extra config path.
9. Explicit overrides from CLI options or Python API `overrides`.

Configuration files closer to the linted file patch or replace values from earlier files. `rules` and `exclude_rules` are each overwritten as whole values when set in a child config; the active rule set for a file is computed by applying `rules` first and then subtracting `exclude_rules`.

The `templater` setting is special: it may be set at the working-directory level, but it is not changed by config files in subdirectories of the working directory. This keeps a single templater active for a run while still allowing other settings to vary by file.

Inline SQL comments beginning with `-- sqlfluff:` set configuration for the whole file before parsing. The colon-separated address after `sqlfluff` maps to the same nested configuration path used in `.sqlfluff` files.

`.sqlfluffignore` files use gitignore-style path patterns and may appear in subdirectories of the linted path. `pyproject.toml` may also provide `ignore_paths` in `[tool.sqlfluff.core]`; those patterns use the same matching rules. The CLI option `--disregard-sqlfluffignores` disables ignore-file filtering for that operation.

`-- noqa` ignores all violations on a line. `-- noqa: CODE,CATEGORY` ignores specific rules or error families on a line. `-- noqa: disable=<rule>[,...]` starts an ignored range, and `-- noqa: enable=<rule>[,...]` ends it; `all` applies to all rules. `--disable-noqa` ignores inline `noqa` comments, and `--disable-noqa-except` allows only selected inline ignores to remain active.

Rules may be downgraded to warnings using the `warnings` configuration value. Warning violations remain visible in output and serialized records but do not by themselves cause a failing status or exit code.

## Dialects, Rules, and Metadata

SQLFluff ships dialect definitions for ANSI SQL and many named dialects, including Athena, BigQuery, ClickHouse, Databricks, Db2, Doris, DuckDB, Exasol, Flink, Greenplum, Hive, Impala, MariaDB, Materialize, MySQL, Oracle, Postgres, Redshift, Snowflake, SOQL, SparkSQL, SQLite, StarRocks, Teradata, Trino, T-SQL, and Vertica.

`dialect_readout()` and `list_dialects()` expose the canonical dialect list for the installed package. `dialect_selector(label)` returns an expanded dialect object for a known label. Unknown dialect labels fail. Legacy labels that have been renamed or merged fail with user-facing migration guidance rather than silently selecting a different dialect.

Rules are identified by a code, a stable name, a description, groups, and aliases. Rule selection accepts any mix of codes, names, aliases, and groups. The `core` rule group contains broadly applicable, stable rules suitable for initial project rollout. Some rules may be disabled by default for particular dialects and can expose a `force_enable` configuration option.

Lint violations are tied to rule metadata. Serialized lint records must preserve enough metadata for a caller to identify the rule, location, description, warning status, and available fixes without inspecting internal rule objects.

## Templating Behavior

SQLFluff templates SQL before lexing and parsing. Linting and fixing operate on the rendered SQL, then map violations and source edits back to the original source file where possible.

The built-in templaters are:

- `raw`: leaves SQL text unrendered.
- `jinja`: renders Jinja templates using configured context, macros, library functions, filters, include paths, and optional built-in dbt-style mock macros.
- `python`: renders Python format strings using configured context.
- `placeholder`: replaces database parameter placeholders with configured sample values.

Generic templater variables are read from a templater-specific context section. For example, Jinja context lives under `[sqlfluff:templater:jinja:context]`, Python context under `[sqlfluff:templater:python:context]`, and placeholder context under `[sqlfluff:templater:placeholder:context]`.

Jinja context values are case-sensitive and may be interpreted as native Python literal types such as lists, tuples, and dictionaries. Jinja macros may be defined directly in configuration under `[sqlfluff:templater:jinja:macros]`. The config key naming a macro block is used for config overriding; the macro name inside the block is what SQL uses.

`load_macros_from_path` is a comma-separated list of files or directories, resolved relative to the config file that declares it. Macros loaded from those paths are available globally to SQL files without explicit Jinja imports. `exclude_macros_from_path` excludes selected macro paths. `loader_search_path` is also relative to the declaring config file and is used for Jinja `include` and `import`; it does not automatically load macros into the global namespace. Paths listed in `load_macros_from_path` also contribute to the Jinja loader search path.

The Jinja `library_path` setting loads Python modules from the configured directory so their functions and nested modules can be called from templates. A library may expose Jinja filters by defining a `SQLFLUFF_JINJA_FILTERS` dictionary mapping filter names to callables. Setting `--library-path none` disables the configured library path for a run.

When `--ignore=templating` or the equivalent config is active, undefined Jinja variables and missing includes are replaced with placeholder-like values derived from their names where possible. This behavior helps SQLFluff continue linting partially configured templates, but it does not guarantee that every template becomes fixable or parsable.

The Python templater uses Python format-string syntax. Because config files cannot create arbitrary Python objects, a variable name containing a dot is rewritten as a lookup on the special fixed context key `sqlfluff`; for example `{foo.bar}` is interpreted as a lookup equivalent to `sqlfluff["foo.bar"]`.

The placeholder templater supports named and positional parameter styles including `colon`, `colon_nospaces`, `colon_optional_quotes`, `numeric_colon`, `pyformat`, `dollar`, `dollar_surround`, `question_mark`, `numeric_dollar`, `percent`, and `ampersand`. `param_style` selects a built-in style. `param_regex` supplies a custom regex; a named group `param_name` identifies named parameters, and missing names are treated positionally. If no sample value is provided for a placeholder, SQLFluff uses the parameter name itself as the replacement. Positional placeholders are numbered from `1` in encounter order.

Template variant rendering may produce multiple rendered variants for a single source file. `render_variant_limit` caps the number of variants, including the primary render. A value of `1` restores single-render behavior. Additional variants improve lint coverage for templated branches but do not promise exhaustive branch enumeration. Alternate variants can surface additional lint violations; parse or lex failures in alternate variants are not fatal when there is a valid root variant.

## Linting, Fixing, Parsing, and Rendering

Linting reads SQL, resolves configuration for each file, templates the SQL, lexes and parses it with the selected dialect, applies the active rule set, and reports violations sorted by source location and code. Human CLI output groups violations by file. Serialized output contains one record per file with filepath, violations, statistics, and timings when available.

Fixing uses the same linting pipeline with fix generation enabled. Fixes are only applied for violations with available source edits. SQLFluff avoids applying fixes to files with templating or parsing errors unless `fix_even_unparsable` is enabled in configuration or `--FIX-EVEN-UNPARSABLE` is supplied to the CLI. Ignoring parse or templating errors hides or downgrades those errors but does not by itself make unsafe fixing allowed.

For stdin, `lint -`, `fix -`, `parse -`, and `render -` read SQL from standard input. `--stdin-filename` makes SQLFluff resolve configuration as if the stdin content came from the supplied path. `fix -` writes the fixed SQL to stdout and sends diagnostic messages to stderr.

`parse` returns or prints a parse projection rather than lint rule results. In JSON/YAML output, each parsed file has a filepath and a `segments` value; `segments` is null when parsing fails. When parsing succeeds, the projection preserves nested SQL structure and raw text without making the Python parser object model part of the public contract.

`render` prints the templated SQL. If rendering creates multiple variants, the CLI labels and prints each variant. If templating errors occur, render reports them as violations and fails.

`Linter.render_string()` returns a `RenderedFile` with rendered variants, templater violations, active config, timing, filename, encoding, and source string. `Linter.parse_string()` returns a `ParsedString`, whose `violations` property combines templating violations with lexing and parsing violations for the root parsed variant when available. `ParsedString.root_variant()` returns the first successfully parsed variant or `None`.

`LintedFile.get_violations()` filters by rule, error type, ignored status, warning status, and fixability. `LintedFile.fix_string()` returns `(fixed_sql, success)` for successfully templated and parsed string linting results. `LintingResult.as_records()` returns file records sorted by filepath. `LintingResult.stats(fail_code, success_code)` reports file counts, violation counts, clean and unclean rates, status, and the appropriate exit code.

## Error Semantics

`SQLBaseError` is the base class for user-visible SQLFluff violations. It carries a description, source position, ignored status, fatal status, and warning status, and serializes to a dictionary with code, description, position, name, and warning fields.

`SQLTemplaterError` reports templating failures and uses code `TMP` and category `templating`.

`SQLLexError` reports lexing failures and uses code `LXR` and category `lexing`.

`SQLParseError` reports parsing failures and uses code `PRS` and category `parsing`. Its serialized form includes the base violation fields and any available affected source range.

`SQLLintError` reports rule violations and uses the triggering rule's code and name. Its serialized form includes the base violation fields, any available affected source range, and fix records. It is fixable when it has at least one fix.

`SQLFluffUserError` reports user-facing configuration, dialect, or invocation errors. The CLI catches these errors, prints a user error, and exits with error code `2`.

`APIParsingError` is raised by the simple `parse()` API when parsing a SQL string finds violations. It is a `ValueError` with a `violations` attribute containing the collected `SQLBaseError` instances, and its message summarizes the count and string form of each violation.

Unknown dialect names fail before linting proceeds. Missing dialect configuration fails when a config requires a dialect and none is available; the error includes available dialect labels and guidance to set a dialect in config or on the command line.

## Cross-View Invariants

1. For the same SQL, dialect, templater, rule selection, and configuration, simple API linting and CLI linting report the same user-observable violation codes, descriptions, warning status, and source positions, apart from filepath and output formatting.

2. `sqlfluff.fix()` on a string and `sqlfluff fix -` on stdin apply the same safe fixes under the same effective configuration and return the fixed SQL rather than a serialized violation record.

3. `lint`, `fix`, `parse`, and `render` all resolve dialect, templater, rule selection, ignores, and inline directives through the same effective `FluffConfig` rules for a file.

4. `rules`, `list_rules()`, and `Linter.rule_tuples()` expose the same rule identities and metadata for the active installed rule set.

5. `dialects`, `list_dialects()`, and `dialect_readout()` expose the same dialect labels, names, inheritance labels, and descriptions; every listed label is accepted by `dialect_selector()`.

6. Rule selection is deterministic across views: `rules` narrows the active set first, then `exclude_rules` subtracts from it, and references may be codes, names, aliases, or groups in either source.

7. Warning configuration is consistent across CLI and Python APIs: warning violations remain visible when warnings are included, but warnings alone do not make a file unclean or produce a failing CLI status.

8. `noqa`, ignored error families, `.sqlfluffignore`, and `ignore_paths` affect whether violations and files participate in linting and fixing, but they do not change dialect parsing or rule definitions.

9. Fixing never depends on the human output renderer. Human, JSON, YAML, SARIF, and GitHub annotation views are different projections of the same linting result.

10. Template rendering is the shared input to linting, parsing, and fixing. Violations found in rendered SQL are mapped back to source locations before being exposed to users.

11. Parse output is a projection of the same configured dialect parse used before linting. A SQL string that cannot be parsed cleanly by the simple `parse()` API reports parse-related violations rather than returning a successful parse projection.

12. Timing and statistics records are supplemental metadata. Their presence or output destination does not change lint, parse, or fix decisions.

## Representative Workflows

A first-time CLI workflow:

```text
pip install sqlfluff
sqlfluff lint test.sql --dialect ansi
sqlfluff fix test.sql --rules LT02,LT12,CP01 --dialect ansi
sqlfluff parse test.sql --dialect ansi --format yaml
sqlfluff rules
sqlfluff dialects
```

The lint command reports file-level violations with line, position, code, description, and rule name. The fix command applies only available fixes for the selected rules. The parse command shows how SQLFluff interpreted the file under the selected dialect. The metadata commands show the installed rule and dialect surface.

A simple Python workflow:

```python
import sqlfluff

sql = "SeLEct  *, 1, blah as  fOO  from mySchema.myTable"

violations = sqlfluff.lint(sql, dialect="bigquery")
fixed = sqlfluff.fix(sql, dialect="bigquery", rules=["CP01", "CP02"])
tree = sqlfluff.parse(fixed, dialect="bigquery")
rules = sqlfluff.list_rules()
dialects = sqlfluff.list_dialects()
```

The lint result is a list of serializable violation dictionaries. The fixed SQL is a string. The parse result is a nested JSON-like structure suitable for walking by segment names.

An advanced configuration workflow:

```python
from sqlfluff.core import FluffConfig, Linter

config = FluffConfig.from_strings(
    "[sqlfluff]\ndialect=bigquery\nrules=layout,capitalisation\n",
    "[sqlfluff]\nexclude_rules=LT08\n",
)
linter = Linter(config=config)
linted_file = linter.lint_string("SELECT  1", fix=True)
fixed_sql, success = linted_file.fix_string()
records = linter.lint_string_wrapped("SELECT  1").as_records()
```

Later config strings take precedence over earlier strings. The `Linter` uses the supplied `FluffConfig` for parsing, linting, fixing, rule selection, and serialization.

A templated SQL workflow:

```text
# .sqlfluff
[sqlfluff]
dialect = ansi
templater = jinja

[sqlfluff:templater:jinja:context]
table_name = my_table

# query.sql
SELECT * FROM {{ table_name }}

sqlfluff render query.sql
sqlfluff lint query.sql
```

The render command prints the SQL after templating. The lint command lints the rendered SQL and reports violations in source coordinates where possible.

## Non-Goals

- dbt templater plugin behavior, dbt project/profile loading, dbt network access, database access, and dbt adapter behavior are outside this core specification.
- The optional Rust-backed parser and lexer are not required. Python behavior is the reference surface here.
- SQLFluff does not promise a stable Python object model for parsed SQL beyond the documented result objects and serialized parse projections.
- Reconstructing every dialect's complete grammar is not required by this specification; dialect behavior is covered through public parsing, linting, and metadata behavior.
- Custom rule authoring internals, plugin hook implementation details, reflow internals, and low-level parser grammar constructors are not required except where their effects are visible through public linting, fixing, parsing, or metadata APIs.
- Dependency pin details, packaging metadata beyond the installable package and console command, development tooling, and repository maintenance workflows are not part of the runtime behavior contract.
- Exact human CLI spacing, color, progress-bar rendering, and decorative completion text are not semantic requirements except where an option explicitly selects a serialized output format.
