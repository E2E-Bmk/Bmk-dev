# Bandit Specification

## Product Overview

Bandit is a local security linter for Python source. It parses each selected source file, applies installed security rules to the syntax tree, records issues and scan metrics, and projects that state through a command exit status and one selected report format.

The scanner must report common security patterns rather than prove exploitability. Each issue must identify the rule, severity, confidence, CWE, source location, explanatory text, and documentation link. A file that cannot be parsed must be recorded as skipped instead of terminating an otherwise valid scan.

## Scope

This contract covers:

- local files, directories, recursive discovery, and standard-input source;
- installed documented B1xx through B7xx rules and their semantic ratings;
- YAML, TOML, project INI, named-profile, command-line test selection, and plugin settings;
- path exclusions, severity/confidence thresholds, line-level `nosec`, and JSON baselines;
- the `bandit`, `bandit-config-generator`, and `bandit-baseline` console scripts;
- CSV, custom, HTML, JSON, SARIF, screen, text, XML, and YAML reports as semantic projections;
- the documented `bandit.plugins`, `bandit.blacklists`, and `bandit.formatters` extension entry contracts.

Invalid arguments, configuration, profiles, templates, or unavailable required files must follow the failures in Error Semantics and Invocation Protocol.

## Installable Surface

Installing `bandit` must provide these package-level names:

```python
from bandit import HIGH, LOW, MEDIUM, UNDEFINED
from bandit import Issue, checks, takes_config, test_id
```

The rating constants must be the uppercase strings named by each constant. `bandit` must expose its installed `__version__` and distribution author as `__author__`.

Installation must register these console scripts:

```text
bandit
bandit-config-generator
bandit-baseline
```

Installation must discover third-party entries in `bandit.plugins`, `bandit.blacklists`, and `bandit.formatters`. Direct imports from CLI, core, formatter, blacklist, or plugin implementation carriers are not part of this contract.

## Public API

### Plugin results and decorators

```python
Issue(
    severity,
    cwe=0,
    confidence=UNDEFINED,
    text="",
    ident=None,
    lineno=None,
    test_id="",
    col_offset=-1,
    end_col_offset=0,
)

checks(*node_types)
takes_config(function_or_name)
test_id(id_value)
```

An `Issue` returned by a test plugin must carry its supplied rating, CWE number, text, and optional location metadata. The scanner must attach the installed rule ID, rule name, filename, complete line range, and missing location data before exposing the issue in a report. Byte-valued issue text must be decoded as UTF-8. An omitted CWE must project as no CWE object rather than a fabricated identifier.

`checks` must declare one or more valid syntax-node names handled by a plugin. An unknown node name must not match a scanned AST node. `test_id` must declare the rule ID. A plugin without a declared ID must be skipped with a warning. `takes_config` must support both `@takes_config` and `@takes_config("shared_section")`; the scanner must pass the selected configuration dictionary to that plugin.

### Extension entry contracts

A `bandit.plugins` entry must resolve to a decorated callable receiving the scanner-provided context. It must return one `bandit.Issue` when the current syntax node matches or return `None` when it does not. The context object's internal storage and AST-manager state are not public contracts.

A configurable plugin module must expose `gen_config(plugin_name)` returning its built-in settings dictionary. The scanner must use those settings when the selected configuration has no section for that plugin. `bandit-config-generator` must use the same returned settings. When a plugin section is present, that section must supply the plugin settings instead of being merged with omitted built-in list values.

A `bandit.blacklists` entry must return a mapping whose supported keys are `Call` and `Import`. Each mapped list item must contain `name`, unique `id`, `qualnames`, `message`, and `level`; an optional CWE must become the issue CWE. Installed blacklist items must participate in normal `tests` and `skips` filtering by their B3xx or B4xx ID. An entry missing a required item key must be unusable and must not produce a partial security issue.

A `bandit.formatters` entry must resolve to a callable with the documented contract:

```python
report(manager, fileobj, sev_level, conf_level, lines=-1)
```

The callable must write its projection to `fileobj` using issues at or above both supplied thresholds. A formatter that cannot serialize the selected state must terminate the invocation nonzero without claiming a successful report. Built-in format names are CLI contracts, not promised direct-import module paths.

## Product State Model

One scan produces a single current state with three public projections:

1. **Issue projection:** selected and detected findings, each with rule identity, ratings, CWE, message, filename, source span, and optional code context.
2. **Run projection:** per-file and total metrics plus skipped-file errors. Metrics describe the selected scan before report thresholds and baseline suppression; `nosec` suppression is already reflected.
3. **Delivery projection:** the chosen report, baseline comparison view, and process exit status after severity, confidence, and baseline filtering.

The same current state must satisfy these top-level invariants:

- An issue present in two report formats must return the same rule ID, ratings, CWE, message, filename, and source span in both projections.
- Run totals must equal the sum of corresponding per-file metrics when all scanned files expose per-file metrics.
- Exit 1 must mean that the delivery projection contains at least one reportable issue, except when `--exit-zero` explicitly changes the status to 0.
- A skipped parse error must appear in the run projection and must not become an issue in the issue projection.

## Scanning and Selection

`bandit TARGET...` must scan explicit Python files. `-r/--recursive` must discover Python files below directory targets and must also enable automatic discovery of one project `.bandit` file. A target of `-` must scan Python source from standard input and report its filename as `<stdin>`. No target must print usage and exit 2.

Recursive discovery must exclude the default patterns `.svn`, `CVS`, `.bzr`, `.hg`, `.git`, `__pycache__`, `.tox`, `.eggs`, and `*.egg`. YAML/TOML `exclude_dirs` and CLI `-x/--exclude` glob lists must be additive. A file matched by either source must not contribute issues or file metrics. Multiple automatically discovered `.bandit` files must exit 2; `--ini PATH` must select one explicit INI file.

The effective test set must follow these rules:

- With neither `tests` nor `skips`, all discovered rules must run.
- With only `tests`, only those IDs must run. With only `skips`, every discovered ID except those listed must run.
- With both lists, the scanner must start from `tests` and remove `skips`. The same ID in both effective sets must exit 2.
- YAML/TOML config `tests` and CLI `-t` must be combined, and config `skips` and CLI `-s` must be combined.
- When `-p/--profile NAME` selects a legacy named profile, that profile's `include` and `exclude` sets must replace top-level config `tests` and `skips`; CLI `-t` and `-s` must then be added.
- For an INI option, an explicitly supplied CLI value must replace that corresponding INI value. An INI value must replace the CLI parser default when the CLI option is omitted.

Unknown rule IDs, an unknown named profile, a selection that leaves no runnable rules, or overlapping effective include/exclude sets must exit 2.

Severity and confidence each use `UNDEFINED < LOW < MEDIUM < HIGH`. Repeated `-l` and `-i` flags must select LOW, MEDIUM, and HIGH minimums; `--severity-level` and `--confidence-level` must accept `all`, `low`, `medium`, and `high`. An issue must appear only when it meets both minimums. `all` must include `UNDEFINED`; `low` must exclude `UNDEFINED`. Threshold filtering must not rewrite the underlying issue metrics. When filtering leaves no reportable issue, the scan must exit 0.

## Configuration and Suppression

YAML and TOML configuration must be loaded only through `-c/--configfile`. TOML settings must be read from `[tool.bandit]`; plugin settings must be read from corresponding nested tables. Project INI settings must be read from `[bandit]`. The documented selection keys are `tests` and `skips`; the documented exclusion key is `exclude_dirs` for YAML/TOML and `exclude` for INI. INI must additionally support `targets` and the documented CLI-equivalent options.

Malformed configuration, an unreadable explicit config, or a configuration whose required values have invalid types must exit 2. Unsupported config keys must not create new scanner behavior.

The generated/default configurable settings must include:

- `assert_used.skips`, defaulting to an empty list;
- `hardcoded_tmp_directory.tmp_dirs`, defaulting to `/tmp`, `/var/tmp`, and `/dev/shm`;
- shared shell-injection lists for `subprocess`, `shell`, and `no_shell` call names;
- `try_except_pass.check_typed_exception` and `try_except_continue.check_typed_exception`, both defaulting to false; when either setting is false, its rule must skip a narrower typed handler such as `ZeroDivisionError`, but a bare handler and the broad `Exception` handler must remain reportable;
- SSL bad-protocol lists covering SSLv2, SSLv3, TLSv1, TLSv1.1, SSLv23 method names, and their native/pyOpenSSL forms;
- DSA/RSA weak-key thresholds of 1024 for HIGH and 2048 for MEDIUM, and EC thresholds of 160 for HIGH and 224 for MEDIUM;
- `markupsafe_xss.extend_markup_names` and `allowed_calls`, both defaulting to empty lists.

A bare `# nosec` on an issue line must suppress every rule result on that line. `# nosec B602, B607` must suppress only the listed IDs, and full installed rule names must work in place of IDs. An unknown name in a selective comment must be ignored with a warning and must not suppress other rules. `--ignore-nosec` must disable bare and selective suppression. Bare suppressions must increment `nosec`; selectively suppressed matching results must increment `skipped_tests`. A mismatched selective ID must leave the issue reportable.

## Documented Rule Detection

Ratings below use `severity/confidence`. Every reported rule must return the listed CWE. A nonmatching construct must return no issue for that rule. Exact explanatory prose is not part of the contract.

### General and application rules

| ID | Required detection | Rating | CWE |
|---|---|---|---:|
| B101 | An `assert` statement, except files matched by `assert_used.skips`. | LOW/HIGH | 703 |
| B102 | Python `exec`. | MEDIUM/HIGH | 78 |
| B103 | `chmod` granting group write/execute or world execute; world write/execute must receive HIGH severity, less permissive flagged masks MEDIUM. | MEDIUM or HIGH/HIGH | 732 |
| B104 | The string literal `0.0.0.0`. | MEDIUM/MEDIUM | 605 |
| B105 | A string literal assigned to or compared with password-like names (`password`, `pass`, `passwd`, `pwd`, `secret`, `token`, `secrete`, including underscore-delimited forms). | LOW/MEDIUM | 259 |
| B106 | A string literal passed as a keyword value whose name is password-like. | LOW/MEDIUM | 259 |
| B107 | A non-`None` string default for a password-like function argument. | LOW/MEDIUM | 259 |
| B108 | A string starting with a configured temporary-directory prefix. | MEDIUM/MEDIUM | 377 |
| B110 | An exception handler whose body silently passes; when `check_typed_exception` is false, a narrower typed handler such as `ZeroDivisionError` must return no issue, while a bare handler or the broad `Exception` handler must report. | LOW/HIGH | 703 |
| B112 | An exception handler in a loop whose body silently continues; when `check_typed_exception` is false, a narrower typed handler such as `ZeroDivisionError` must return no issue, while a bare handler or the broad `Exception` handler must report. | LOW/HIGH | 703 |
| B113 | A `requests` or `httpx` request call with missing timeout or `timeout=None`. | MEDIUM/LOW | 400 |
| B201 | A Flask application `run` call with `debug=True`. | HIGH/MEDIUM | 94 |
| B202 | `tarfile.extractall`: no validation must be HIGH/HIGH, unknown non-callable `members` MEDIUM/MEDIUM, callable `members` LOW/LOW; `filter="data"` must return no issue. | variable | 22 |

### Blacklisted calls

Blacklist call matches must use HIGH confidence and the severity below.

| ID | Required qualified-call family | Severity | CWE |
|---|---|---|---:|
| B301 | `pickle`, `dill`, `shelve`, `jsonpickle`, and `pandas.read_pickle` deserialization calls. | MEDIUM | 502 |
| B302 | `marshal.load` and `marshal.loads`. | MEDIUM | 502 |
| B303 | PyCrypto/PyCryptodome MD2, MD4, MD5, SHA and cryptography MD5/SHA1 constructors. | MEDIUM | 327 |
| B304 | ARC2, ARC4, Blowfish, DES, XOR, CAST5, IDEA, SEED, or TripleDES constructors. | HIGH | 327 |
| B305 | ECB cipher mode. | MEDIUM | 327 |
| B306 | `tempfile.mktemp`. | MEDIUM | 377 |
| B307 | `eval`. | MEDIUM | 78 |
| B308 | `django.utils.safestring.mark_safe`. | MEDIUM | 79 |
| B310 | `urllib` URL-opening/retrieval helpers that accept unexpected schemes. | MEDIUM | 22 |
| B311 | Standard `random` generators used through documented constructors and sampling/value methods. | LOW | 330 |
| B312 | `telnetlib.Telnet`. | HIGH | 319 |
| B313-B319 | Unsafe cElementTree, ElementTree, expatreader, expatbuilder, SAX, minidom, and pulldom parsing calls respectively. | MEDIUM | 20 |
| B321 | `ftplib.FTP`. | HIGH | 319 |
| B323 | `ssl._create_unverified_context`. | MEDIUM | 295 |

B324 must report HIGH/HIGH CWE-327 for `hashlib` MD4, MD5, SHA, or SHA1 constructors, including `hashlib.new` with those literal names, unless `usedforsecurity=False`. It must report MEDIUM/HIGH CWE-327 for `crypt.crypt` or `crypt.mksalt` with literal `METHOD_CRYPT`, `METHOD_MD5`, or `METHOD_BLOWFISH`.

### Blacklisted imports

Blacklist import matches must use HIGH confidence and must match direct imports, from-imports, and equivalent built-in import calls.

| ID | Required imported family | Severity | CWE |
|---|---|---|---:|
| B401 | `telnetlib`. | HIGH | 319 |
| B402 | `ftplib`. | HIGH | 319 |
| B403 | `pickle`, `cPickle`, `dill`, or `shelve`. | LOW | 502 |
| B404 | `subprocess`. | LOW | 78 |
| B405-B409 | cElementTree/ElementTree, SAX, expatbuilder, minidom, and pulldom respectively. | LOW | 20 |
| B411 | `xmlrpc`. | HIGH | 20 |
| B412 | documented CGI handler classes from `wsgiref` or Twisted. | HIGH | 284 |
| B413 | PyCrypto `Crypto` cipher, hash, IO, protocol, public-key, random, signature, or utility packages. | HIGH | 327 |
| B415 | `pyghmi`. | HIGH | 319 |

### Cryptography, injection, and framework rules

| ID | Required detection | Rating | CWE |
|---|---|---|---:|
| B501 | `requests`/`httpx` certificate verification explicitly disabled. | HIGH/HIGH | 295 |
| B502 | Native SSL or pyOpenSSL calls selecting a configured broken protocol. | HIGH/HIGH | 327 |
| B503 | Function defaults selecting a configured broken protocol. | MEDIUM/MEDIUM | 327 |
| B504 | SSL setup calls that omit a protocol version. | LOW/MEDIUM | 327 |
| B505 | DSA/RSA/EC key size below the HIGH threshold must be HIGH; a size below only the MEDIUM threshold must be MEDIUM. | variable/HIGH | 326 |
| B506 | Unsafe `yaml.load` rather than safe loading. | MEDIUM/HIGH | 20 |
| B507 | Paramiko missing-host-key policy set to automatic trust or warning policy. | HIGH/MEDIUM | 295 |
| B508 | SNMP v1/v2 community configuration. | MEDIUM/HIGH | 319 |
| B509 | SNMPv3 user data without authentication/privacy protection. | MEDIUM/HIGH | 319 |
| B601 | Paramiko `exec_command`. | MEDIUM/MEDIUM | 78 |
| B602 | Configured subprocess call with `shell=True`; a simple static command must be LOW/HIGH and a dynamic or shell-special command HIGH/HIGH. | variable | 78 |
| B603 | Configured subprocess call without `shell=True`. | LOW/HIGH | 78 |
| B604 | Any non-configured-subprocess wrapper called with `shell=True`. | MEDIUM/LOW | 78 |
| B605 | Configured shell-spawning function; a simple static command must be LOW/HIGH and a dynamic or shell-special command HIGH/HIGH. | variable | 78 |
| B606 | Configured process-spawning function that does not use a shell. | LOW/MEDIUM | 78 |
| B607 | Configured process call whose literal executable path is not absolute. | LOW/HIGH | 78 |
| B608 | String-built SQL-like text; DB-API `execute`/`executemany` use must raise confidence to MEDIUM unless `str.replace` is involved, otherwise confidence is LOW. | MEDIUM/LOW or MEDIUM | 89 |
| B609 | `chmod`, `chown`, `tar`, or `rsync` wildcard arguments passed to a configured process call. | HIGH/MEDIUM | 155 |
| B610 | Django `QuerySet.extra` with a non-literal risk-bearing argument. | MEDIUM/MEDIUM | 89 |
| B611 | Django `RawSQL` with a non-literal query. | MEDIUM/MEDIUM | 89 |
| B612 | `logging.config.listen`. | MEDIUM/HIGH | 94 |
| B613 | Unicode bidirectional control characters in a source file. | HIGH/MEDIUM | 838 |
| B614 | `torch.load` or `torch.serialization.load` without `weights_only=True`. | MEDIUM/HIGH | 502 |
| B615 | Hugging Face `from_pretrained`, `load_dataset`, hub download, snapshot download, or repository download without an immutable hexadecimal revision/commit of at least seven characters; local paths and non-literal revision expressions must return no issue. | MEDIUM/HIGH | 494 |
| B701 | Jinja `Environment` with missing or false `autoescape` must be HIGH/HIGH; an unrecognized non-true value must be HIGH/MEDIUM; true or `select_autoescape(...)` must return no issue. | variable | 94 |
| B702 | Construction of a Mako template. | MEDIUM/HIGH | 80 |
| B703 | Django `mark_safe` applied to data not proven to be a safe literal. | MEDIUM/HIGH | 80 |
| B704 | `markupsafe.Markup`, `flask.Markup`, or configured aliases applied to dynamic content unless it comes from an allowed configured call. | MEDIUM/HIGH | 79 |

## Baselines

`-b/--baseline PATH` must read a Bandit JSON report. A current issue with the same filename, rule identity, text, ratings, and CWE as a baseline issue must be suppressed even when its line number moved. A semantically new issue must remain reportable. Current-run metrics must continue to count both baseline-matched and new current findings.

Baseline output must be accepted only by `custom`, `html`, `json`, `screen`, and `txt`. JSON and human baseline-capable reports must represent candidate locations when a new semantic issue cannot be assigned to one location unambiguously. Selecting another formatter with `-b` must exit 2. A missing baseline must exit 2. Readable malformed JSON must emit a warning, act as an empty baseline, and continue the current scan.

`bandit-baseline` must run only from a clean local Git repository with a current commit and parent. It must scan the parent commit into a temporary JSON baseline, restore and scan the current commit against it, restore the original current commit, and return the current Bandit run's status. Additional unknown arguments must be forwarded to both Bandit runs. Its default terminal mode must print text; `-f txt`, `html`, or `json` must select the result format, with non-terminal results written as `bandit_baseline_result.<format>`. Missing Git support, a non-repository directory, dirty worktree, missing parent, forbidden forwarded `-o`, an existing result file, or a colliding temporary baseline file must exit 2.

## Reports

All formats must project the same filtered issue facts. Exact bytes, whitespace, prose layout, timestamps, absolute versus relative rendering, path separators, item order, color codes, and styling are not stable contracts.

### JSON and YAML

JSON and YAML must return top-level `results`, `errors`, `metrics`, and `generated_at` values. Each result must contain:

```text
filename, test_name, test_id,
issue_severity, issue_confidence, issue_cwe,
issue_text, line_number, line_range,
col_offset, end_col_offset, code, more_info
```

`issue_cwe` must be either empty or a mapping with integer `id` and canonical CWE `link`. `line_number` and `line_range` must be one-based; `col_offset` and `end_col_offset` must retain scanner offsets. `code` must honor `-n/--number`; `more_info` must link to the installed rule documentation. `errors` must contain skipped filenames and reasons.

`metrics` must contain `_totals` and per-file entries. Totals must expose `loc`, `nosec`, `skipped_tests`, and counts for every `SEVERITY.{UNDEFINED,LOW,MEDIUM,HIGH}` and `CONFIDENCE.{UNDEFINED,LOW,MEDIUM,HIGH}`. YAML must carry the same semantic values as JSON. A serialization failure must terminate nonzero without a successful report.

### CSV and XML

CSV must return one issue row with columns `filename`, `test_name`, `test_id`, `issue_severity`, `issue_confidence`, `issue_cwe`, `issue_text`, `line_number`, `col_offset`, `end_col_offset`, `line_range`, and `more_info`. Its CWE field must be the CWE link. It must omit run metrics and skipped-file errors.

XML must return a `testsuite` named `bandit` whose `tests` count equals the filtered issue count. Each issue must return a `testcase` carrying the filename and rule name, with an `error` carrying severity type, message, documentation link, and semantic content for rule ID, confidence, CWE, and location. It must omit run metrics and skipped-file errors. An XML write failure must terminate nonzero without a successful report.

### SARIF

SARIF must return a SARIF 2.1.0 document with one run. The driver must identify Bandit and its installed version. Each distinct reported rule must have a descriptor with rule ID, rule name, documentation URI, security/CWE tags, and confidence-derived precision. Each result must reference that descriptor, map HIGH severity to `error`, MEDIUM to `warning`, LOW to `note`, and other severity to `warning`, and carry message, severity/confidence properties, artifact URI, one-based region, and source snippet.

SARIF run properties must carry the same metrics mapping as JSON. Skipped files must become error-level tool-configuration notifications. Missing SARIF optional dependencies must make the format unavailable, and a serialization failure must terminate nonzero without a successful report.

### Human and custom formats

HTML, screen, and text must expose each filtered issue's rule ID/name, message, severity, confidence, CWE, documentation link, filename, line/column location, and requested code context. They must expose lines-of-code and `nosec` totals and skipped-file information. Text and screen must expose counts by rating. HTML must escape source and issue content; exact markup and styling are not contracts. Screen output requested with `-o` must not write a report file and must notify the user to select text output.

Custom output must accept Python `str.format` field syntax for the documented tags `{abspath}`, `{relpath}`, `{line}`, `{col}`, `{test_id}`, `{severity}`, `{msg}`, `{confidence}`, and `{range}`. It must return one expanded line per filtered issue and must honor width, alignment, and other standard field format specifications. An unknown tag must remain literal and emit a warning. A malformed template or a template containing no fields must exit 2. `--msg-template` used with any non-custom format must exit 2.

## Error Semantics

Bandit is a console-first tool. Operational failures must return process status rather than expose internal exception classes.

| Condition | Required result |
|---|---|
| No target, invalid argument choice, invalid custom-template use, unknown profile/ID, overlapping selection, no runnable tests, malformed config, unsupported baseline formatter | Exit 2 and emit a diagnostic. |
| Source cannot be parsed or decoded | Record the file/reason in skipped-file output, continue other files, and determine exit from remaining reportable issues. |
| Output cannot be opened or a required optional formatter dependency is unavailable | Exit nonzero without claiming a successful report; argument-level unavailability must exit 2. |
| Findings remain after threshold and baseline filtering | Exit 1 unless `--exit-zero` was supplied. |
| No findings remain after threshold and baseline filtering | Exit 0, including a run containing only skipped-file errors. |
| Plugin returns `None` for a node | Record no issue and continue scanning. |

`bandit-config-generator` must print help and exit 1 when neither `--show-defaults` nor `-o` is supplied. It must exit 2 when the output path already exists. An unknown `-t`/`-s` ID encountered while creating a new file must emit an error and leave no usable profile; the command returns 0 for this logged generation failure, and callers must inspect both status and output usability.

## Cross-View Invariants

1. A finding returned by JSON must return the same rule ID, rule name, severity, confidence, CWE, message, filename, and source span in CSV, YAML, XML, SARIF, HTML, text, screen, and custom projections that expose that field.
2. The filtered issue count must equal JSON/YAML `results` length, CSV data-row count, XML `tests`, SARIF result count, and the number of human/custom issue records for the same invocation.
3. A severity or confidence threshold must remove the same issue identities from every report format and must leave pre-filter issue metrics unchanged.
4. A bare or matching selective `nosec` must remove the same issue identity from every report and must update the corresponding suppression metric before totals are projected.
5. A baseline-matched issue must disappear from every baseline-capable result view, must remain counted in current-run metrics, and must not by itself cause exit 1.
6. A skipped file must return the same filename/reason through JSON/YAML errors, SARIF notifications, and human skipped-file views, and must never appear as a security issue.
7. The process must return exit 1 exactly when at least one issue survives both report thresholds and baseline comparison, unless `--exit-zero` forces 0.
8. Config, profile, and CLI selection must determine one effective rule set that is shared by issue detection, metrics, every formatter, baseline comparison, and process status.
9. JSON and YAML metrics must return equal semantic totals, and SARIF run metrics must return those same totals for the same invocation.
10. Code context length selected by `-n` must affect only context/snippet projections and must not change issue identity, metrics, baseline matching, or exit status.

## Representative Workflows

### Configure, scan, and consume JSON

Create `bandit.yaml`:

```yaml
exclude_dirs: [tests]
tests: [B101, B102, B506]
skips: [B101]
```

Because the same ID must not appear in effective include and exclude sets, this example must exit 2 until B101 is removed from one list. A valid profile is:

```yaml
exclude_dirs: [tests]
tests: [B102, B506]
```

Run:

```console
bandit -r src -c bandit.yaml -f json -o bandit.json
```

The command must discover Python files below `src`, exclude configured paths, run only B102 and B506, write parsed issues/errors/metrics to `bandit.json`, and return 1 when either rule remains reportable or 0 when neither remains. An unreadable source must appear in `errors` without preventing valid files from being reported.

### Establish and apply a baseline

```console
bandit -r src -f json -o baseline.json
bandit -r src -b baseline.json -f json -o current.json
```

The first command must return 1 when it records existing findings. The second command must suppress semantically matching findings even after line movement, retain new findings, keep current metrics, and return status from only the retained result set. Replacing the second format with YAML must exit 2 because YAML is not baseline-capable.

### Add a rule plugin

```python
import bandit

@bandit.test_id("B900")
@bandit.checks("Call")
def prohibit_unsafe_deserialization(context):
    if "unsafe_load" in context.call_function_name_qual:
        return bandit.Issue(
            severity=bandit.HIGH,
            confidence=bandit.HIGH,
            text="Unsafe deserialization detected.",
        )
    return None
```

Register the callable under the `bandit.plugins` entry-point group. A matching call must become a B900 issue in every selected report; a nonmatching call must return no issue. Registration without an ID must skip the plugin with a warning.

## Non-Goals

- Direct use of CLI/core carrier modules, private helpers, manager fields, AST context storage, or plugin implementation helpers is not supported.
- Exact report bytes, prose, whitespace, timestamps, ordering, path separator style, terminal color, HTML structure/style, and absolute-path normalization are not specified.
- Full reconstruction of internal AST visitor state or manager mutation APIs is not required.
- Removed B109 and B111 rules are not active scanning contracts.
- CI services, pre-commit behavior, containers, remote repositories, hosted integrations, and network services are excluded.
- Git operations beyond the local two-commit `bandit-baseline` workflow are excluded.
- Security correctness beyond the documented rule patterns is excluded; Bandit does not promise absence of vulnerabilities.

## Invocation Protocol

`python -m bandit` is not supported. Use the installed console scripts.

### `bandit`

```text
bandit [options] [targets ...]
```

The documented report choices must be `csv`, `custom`, `html`, `json`, `sarif`, `screen`, `txt`, `xml`, and `yaml`. The default must be screen on an interactive color-capable terminal and text otherwise. `-o/--output` must write formats that support files. `-a file|vuln` must select aggregation/sorting perspective without changing issue identity or count. `-n` must select maximum context lines. `-q` must suppress normal human output when there are no results; `-v` must include in-scope and excluded-file details.

| Exit | Meaning |
|---:|---|
| 0 | Valid invocation with no reportable issue, or any valid scan with `--exit-zero`. |
| 1 | One or more issues survive selection, suppression, thresholds, and baseline comparison. |
| 2 | Usage, configuration, profile, output, dependency, template, or baseline setup failure. |

### `bandit-config-generator`

```text
bandit-config-generator [--show-defaults] [-o PATH] [-t IDS] [-s IDS]
```

`--show-defaults` must print discovered configurable plugin defaults without writing a profile. `-o` must create a YAML template containing the discovered ID/name catalog, optional selected/skipped ID lists, and all configurable defaults. Existing output must not be overwritten. Success must return 0; no requested action must return 1; argument or existing-output failure must return 2. The logged unknown-ID generation case described in Error Semantics returns 0 but must not produce a usable profile.

### `bandit-baseline`

```text
bandit-baseline [-f {txt,html,json}] targets... [additional bandit options]
```

The script must return 0 or 1 from the current comparison scan and 2 for baseline setup failure. It must not leave the repository checked out at the parent commit after success or failure.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Evaluation Notes

Assessment exercises public console scripts, package-level plugin symbols, documented extension entry groups, and parsed report outputs. It compares semantic issue identity, ratings, CWE, locations, metrics, suppression, selection, baseline behavior, skipped-file errors, and exit status across formats. Exact presentation, timestamps, ordering, platform-specific path spelling, terminal color, HTML styling, internal manager classes, and registry layout are not assessed.
