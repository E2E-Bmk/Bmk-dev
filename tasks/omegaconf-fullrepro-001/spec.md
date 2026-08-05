# OmegaConf Public Behavior Specification

## Product Overview

OmegaConf is a Python configuration library for building nested configuration
graphs from Python mappings and sequences, YAML text and files, dotlist
arguments, command-line-style arguments, and dataclass structured schemas.
The resulting `DictConfig` and `ListConfig` objects support attribute or item
access, typed updates, interpolation, merging, YAML serialization, and
conversion back to ordinary Python containers or structured objects.

## Scope

This package covers the documented public workflow for configuration
construction and access; dotlist and explicit CLI input; `OmegaConf.select`
and `OmegaConf.update`; mapping and list merging; node interpolations and
custom or built-in resolvers; structured dataclass validation; readonly and
struct flags; YAML loading, saving, and `OmegaConf.to_yaml`; and
`OmegaConf.to_container` and `OmegaConf.to_object`.

The covered construction and utility entry points are
`OmegaConf.create`, `OmegaConf.structured`, `OmegaConf.from_dotlist`,
`OmegaConf.from_cli`, `OmegaConf.merge`, `OmegaConf.select`,
`OmegaConf.can_select`, `OmegaConf.update`, `OmegaConf.resolve`,
`OmegaConf.missing_keys`, `OmegaConf.save`, `OmegaConf.load`,
`OmegaConf.to_yaml`, `OmegaConf.to_container`, `OmegaConf.to_object`,
`OmegaConf.structural_equality`, `OmegaConf.is_missing`,
`OmegaConf.is_interpolation`, `OmegaConf.is_config`, `OmegaConf.is_dict`,
`OmegaConf.is_list`, `OmegaConf.get_type`, `OmegaConf.register_resolver`,
`OmegaConf.has_resolver`, `OmegaConf.clear_resolver`,
`OmegaConf.clear_resolvers`, `OmegaConf.typed_list`, and
`OmegaConf.typed_dict`.

## Public Import Surface

Applications may import `OmegaConf`, `DictConfig`, `ListConfig`,
`ListMergeMode`, `SCMode`, `MISSING`, `SI`, `II`, `open_dict`, and
`read_write` from `omegaconf`. Public validation classes used here are
`MissingMandatoryValue`, `ValidationError`, and `ReadonlyConfigError` from
`omegaconf`, plus `ConfigAttributeError` and `ConfigKeyError` from
`omegaconf.errors`.

The supported container operations are attribute and item access, `get`,
iteration, list comparison and mutation, and mapping or sequence conversion
through the documented `OmegaConf` methods. Resolver functions may use the
documented `_parent_` keyword context.

## Product State Model

A mapping creates a `DictConfig`; a sequence creates a `ListConfig`; nested
values remain addressable through the same public container model. Scalar
values retain their parsed Python types. YAML text and YAML files parse
booleans, numbers, strings, nulls, mappings, and sequences. Dotlist and
explicit CLI arguments create nested paths using dot or bracket notation, and
backslash escaping makes `.`, `[`, `]`, or `=` literal key characters.

Interpolation expressions are retained in an unresolved conversion and are
resolved lazily on access. Node interpolation can select scalar or container
values, can use relative paths, and can contain nested selections. Resolver
interpolations evaluate registered functions and the documented `oc.select`,
`oc.decode`, `oc.create`, `oc.dict.keys`, and `oc.dict.values` resolvers.

Structured dataclasses produce `DictConfig` values whose public access and
updates follow the dataclass field types. Compatible scalar strings can be
converted, optional fields accept `None`, enum names are converted to enum
members, literal values are restricted, and `MISSING` fields require a value
before access. `OmegaConf.to_container` supports `SCMode.DICT`,
`SCMode.DICT_CONFIG`, and `SCMode.INSTANTIATE`; `OmegaConf.to_object`
instantiates structured dataclasses and resolves their interpolations.

## Validation And Error Reporting

Accessing a missing mandatory value raises `MissingMandatoryValue`.
Assignments that violate a structured field type or literal restriction raise
`ValidationError`. A readonly node rejects mutation with
`ReadonlyConfigError`. Struct mode rejects creation of an unknown attribute
with `ConfigAttributeError` or `ConfigKeyError`. Tests require these public
exception types and observable values, not exact traceback or error wording.

## Cross-Component Invariants

Equivalent values created from Python data, YAML, dotlist input, and explicit
CLI input remain equivalent when projected with `OmegaConf.select`,
`OmegaConf.to_container`, or `OmegaConf.to_yaml`. `OmegaConf.merge` preserves
mapping values, applies its documented list modes, and does not mutate its
ordinary merge inputs. `OmegaConf.update` uses the same key-path syntax as
selection and can merge or replace mapping values.

Unresolved and resolved projections distinguish raw interpolation text from
computed values. `OmegaConf.resolve` changes the configuration in place to the
same resolved values exposed by a resolved container conversion. YAML
save/load and file-object load produce the same public projection. Structured
schema merging, structured validation, flag context managers, resolver
registration, and conversion modes operate over the same configuration graph.

## Representative Workflows

A client can construct a base service configuration, apply dotlist or explicit
CLI overrides, merge the sources, update an escaped key path, and select the
resulting values. A client can load YAML, inspect unresolved and resolved
interpolations, save the configuration, reload it, and compare its plain
container projection.

A client can create a structured dataclass schema, merge plain values into it,
observe runtime conversion and validation, temporarily use `read_write` and
`open_dict`, and convert the final graph to a plain mapping, a retained
`DictConfig`, or a dataclass object. A client can register a deterministic
resolver, use nested arguments or `_parent_`, and combine it with the
documented built-in resolvers.

## Non-Goals

This package does not require private target modules or attributes, metadata
or node internals, the vendored ANTLR implementation, environment-variable
leakage, live services, network access, timing behavior, machine-specific
paths, or exact traceback and exception-message formatting. It does not test
undocumented implementation details or deprecated resolver registration APIs.

## Invocation Protocol

Install the requirements listed in the accompanying requirements file and
make an OmegaConf implementation importable as `omegaconf`. Run:

```bash
python -m pytest <test-directory>/test_atomic.py <test-directory>/test_integration.py -q -W error
```

The tests use only deterministic in-memory values and pytest temporary
directories for file workflows. They do not require a database, external
process, live service, or network connection during the test run.

## Environment

The intended test environment is Linux with Python 3.11 without network access
during the test run. The target package is not pre-installed; the
implementation under evaluation must provide the `omegaconf` package.
Required runtime and test packages are `pytest` and `PyYAML>=5.1.0`.

## Evaluation Notes

The tests are split into atomic API checks and integration checks. Integration
checks combine multiple public operations or independent projections of the
same configuration graph. The physical test inventory, node identifiers,
layer taxonomy, and section map are kept in the accompanying package files.
A deliberately weak importable implementation should collect the complete
inventory while passing well below ten percent.
