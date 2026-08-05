# oslo.config Public Configuration Projections Specification

## Product Overview

oslo.config is a local Python configuration library for declaring option
schemas, registering those options with a configuration manager, parsing argv
and INI-style files, validating typed values, tracking where selected values
came from, exporting configuration state, generating sample configuration
data, and validating local configuration files against generated option data.

The covered behavior uses generated options, generated config files, and
generated entry-point metadata. It does not use source test modules, service
processes, remote configuration drivers, network access, sleeps, host
configuration, or complete output snapshots.

## Scope

This specification covers public behavior reachable through:

- `from oslo_config import cfg`
- `python -m oslo_config.generator`
- `python -m oslo_config.validator`

The covered model includes `ConfigOpts`, `Opt`, `OptGroup`, `StrOpt`,
`BoolOpt`, `IntOpt`, `PortOpt`, `ListOpt`, `DictOpt`, `MultiStrOpt`,
`URIOpt`, `HostAddressOpt`, registration in the default group and named
groups, CLI option registration, local config files and config directories,
defaults, application defaults, application overrides, typed conversion,
locations, state export/import, pickle round trips, generator JSON/YAML/INI
outputs, and validator return codes for local files.

## Public Import Surface

The primary public import is:

```python
from oslo_config import cfg
```

The checks also execute the documented local command modules through Python:

```bash
python -m oslo_config.generator
python -m oslo_config.validator
```

Generated entry-point metadata is used only to expose a temporary
`oslo.config.opts` namespace to the generator in the same way an installed
application would expose option discovery.

## Product State Model

An `Opt` records public metadata such as `name`, `dest`, `default`, `help`,
`secret`, `mutable`, and `advanced`. An `OptGroup` records its name and help
metadata. A `ConfigOpts` instance stores registered options in the default
group and named groups, exposes values through attributes and mapping access,
and can parse command-line arguments and local INI files.

Values are selected by source precedence. Command-line arguments override
values from config directories and config files. Config directory files are
read in sorted order after explicitly supplied config files, so later
directory files can override earlier values. Config-file values override
application defaults set with `set_default`, while `set_override` forces a
value until `clear_override` removes it.

Typed option classes convert strings to booleans, integers, ports, lists,
dictionaries, repeated strings, URIs, and host addresses. Required options
must be present before parsing succeeds. String substitution in INI files
can feed later typed values.

The location projection reports whether a value came from an option default,
an application default, an application override, a user-controlled config
file, or the command line. Exported state and pickle serialization preserve
registered options, groups, parsed values, defaults, overrides, setup
metadata, and value locations needed for normal access after import.

The generator projects the same option declarations into JSON, YAML, and INI
sample data. Machine-readable output records groups, option names, dest names,
types, choices, min/max bounds, defaults, sample defaults, secret flags,
advanced flags, and deprecated replacement metadata. The validator consumes
machine-readable option data and local config files and returns success for
known options and failure for unknown options unless an excluded dynamic group
is specified.

## Error Semantics

The checks assert public exception classes for missing required values and
invalid typed values. They do not assert exact exception wording.

For validator execution, the deterministic contract is the process return
code for local inputs. Diagnostic text is not part of the covered behavior.
Generator checks compare structured fields or targeted stable snippets rather
than full emitted files.

## Cross-View Invariants

The same option declarations must agree across registration, parsing,
location, state, generator, and validator views. Group names used by
`ConfigOpts` must be the group names emitted by generated sample data. Option
metadata such as type names, choices, min/max bounds, sample defaults, secret
flags, advanced flags, and deprecated replacements must appear in generated
machine-readable output consistently with the public option objects.

Values parsed from local files must survive export/import and pickle round
trips. Application overrides must survive state export/import and keep their
override location. Generated YAML option data must validate matching local
config files and reject unknown local options. Excluding a dynamic group in
the validator must agree with `ConfigOpts.list_all_sections()` seeing that
same section in a parsed file.

## Representative Workflow

A representative client declares a default group and named group, registers
typed options, parses a local config file and argv, inspects values and
locations, changes defaults and overrides, exports state for another process,
generates machine-readable sample data from an application entry point, and
validates an operator-supplied local config file against that generated data.

## Non-Goals

This package excludes remote configuration drivers, network-backed sources,
source test modules, private modules, patched internal helpers, Sphinx builds,
services, subprocesses that contact external systems, sleeps, timing-sensitive
behavior, host configuration discovery, host environment values, complete
output snapshots, exact diagnostic text, Docker, signatures, and delivery or
qualification claims.

## Invocation Protocol

Install the required packages, make the target `oslo_config` implementation
importable, and run:

```bash
python -m pytest <test-directory> -q -W error
```

The implementation root may be supplied with `--target-root` or the
`TARGET_ROOT` environment variable. If a target root is supplied, it is added
to the front of `sys.path` before tests run. All option modules, entry-point
metadata, config files, and generated outputs are created under pytest
temporary directories.

## Environment

The intended environment is Linux with Python 3.11, without network access.
The target package is not pre-installed; the implementation root is supplied
at runtime or otherwise made importable by the runner.

Required local packages:

- `pytest`
- `pytest-json-report`
- `PyYAML`
- `stevedore`
- `oslo.i18n`
- `netaddr`
- `rfc3986`
- `pbr`

## Evaluation Notes

The package contains 37 atomic cases and 25 integration cases. Integration
cases combine independently checked atomic facts across argv parsing, local
INI parsing, source precedence, value locations, exported state, generator
outputs, and validator return codes. The generated data is intentionally small
and deterministic so implementations must reconstruct real oslo.config
behavior rather than only import the package name.
