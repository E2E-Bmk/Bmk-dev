# Pint Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`pint` is a physical-quantity library that binds numeric magnitudes to unit definitions, performs dimensional arithmetic, converts compatible units, and exposes the resulting registry state through Python objects, string parsing, string formatting, definition-file loading, context-aware conversions, unit systems, and a `pint-convert` command.

The core model is a `UnitRegistry` containing dimensions, units, prefixes, aliases, contexts, groups, and systems. Quantities and units created from a registry retain that registry relationship, so parsing, arithmetic, conversion, formatting, and serialization all project the same definition facts.

## Non-Goals

- This specification does not require pandas, xarray, dask, matplotlib plotting, or full array-library integration behavior.
- This specification does not require exact `repr()` strings, exact exception message text, logging output, performance caches, or private helper modules.
- This specification does not require network services, remote unit-definition sources, or online package installation.
- This specification does not define locale-specific Babel formatting beyond the core format-spec behavior described here.
- This specification does not require uncertainty-aware `pint-convert` results unless the `uncertainties` package is importable.

## Representative Workflows

```python
import pint

ureg = pint.UnitRegistry()
distance = 24.0 * ureg.meter
duration = 8.0 * ureg.second
speed = distance / duration

assert speed.magnitude == 3.0
assert speed.units == ureg.meter / ureg.second
assert speed.to("inch/minute").units == ureg.inch / ureg.minute
```

This workflow creates quantities through registry unit attributes, combines them arithmetically, and converts the result to another compatible compound unit. The original `speed` object remains in meter-per-second units because `to` returns a new quantity.

```python
import pint

ureg = pint.UnitRegistry()
ureg.define("dog_year = 52 * day = dy")
age = ureg.Quantity(10, "year")
dog_age = age.to("dog_years")

assert "dog_year" in ureg
assert dog_age.units == ureg.dog_year
```

This workflow mutates a registry with a programmatic definition, relies on plural parsing for the new unit name, and verifies that conversion, unit lookup, and membership all observe the same loaded definition.

```python
import pint

ureg = pint.UnitRegistry()
wavelength = 530 * ureg.nanometer
frequency = wavelength.to("hertz", "spectroscopy")

with ureg.context("spectroscopy", n=1.33):
    in_medium = frequency.to("nanometer")
```

This workflow uses a named context to permit a conversion between dimensions that are incompatible without an active transformation rule, then uses a parameterized context manager to apply a different relationship within a block.

## Registry Construction And Definitions

The registry is the authority for all unit names, dimensions, aliases, prefixes, systems, and contexts used by its objects.

**Construction And Definition Loading.** The `UnitRegistry` constructor must accept a `filename` input naming a definition file, an empty string that loads the bundled default definitions, `None` that leaves the registry empty, or an iterable of definition lines. When a registry is constructed with no `filename` value, the registry must load the bundled English default units, prefixes, dimensions, systems, constants, and contexts. When a registry is constructed with `filename=None`, the registry must start without the bundled definitions and must raise `UndefinedUnitError` for unit names that have not been defined. When `load_definitions` receives a path, string, or line iterable, the registry must add the parsed definitions to the existing registry and return the parsed definition project object. If a definition line has invalid syntax, then definition loading must raise `DefinitionSyntaxError`. If a definition reuses a unit, alias, dimension, prefix, context, group, or system name and the registry's `on_redefinition` policy is `raise`, then the registry must raise `RedefinitionError`. Where `on_redefinition` is `warn` or `ignore`, the registry must replace the previous definition while either emitting a warning or suppressing it according to that policy.

**Definition Syntax.** A unit definition line must treat the first name as the canonical name, the expression after the first equals sign as the reference definition, the next optional field as the symbol, and later equals-separated fields as aliases. When the symbol placeholder is `_`, the definition must define aliases without assigning a symbol. Prefix definitions must be named with a trailing dash and must apply to compatible unit names during parsing. Dimension definitions must use bracketed names, and derived dimensions must be expressions of other dimensions. Alias directives written with `@alias` must add aliases for an already defined unit. If a definition references units that are defined later in the same loaded project, then the registry must resolve the dependency order before completing the registry cache. If a definition cannot be resolved to reference units and dimensions, then later parsing or conversion involving that name must raise the applicable definition or undefined-unit exception.

**Registry Lookup And Parsing.** Attribute access such as `ureg.meter`, item access such as `ureg["meter"]`, and explicit `parse_units` calls must return `Unit` objects bound to the registry. Calling a registry as a function must delegate to `parse_expression` and must return a `Quantity`. `parse_expression` must parse numbers, unit names, multiplication, division, powers, parentheses, implicit multiplication, `inf`, `infinity`, `nan`, and `dimensionless`. When parsing a mixed number-and-unit string, unit tokens must have the same operator precedence as numeric tokens. `parse_units` must accept only unit expressions and must raise `ValueError` when the expression includes a scale factor. If a unit token is unknown, then parsing must raise `UndefinedUnitError`. Where the registry is case-sensitive, parsing must distinguish names by case; where case sensitivity is disabled, parsing must resolve unit names without case distinctions unless the definitions are ambiguous.

**Registry Options.** The `force_ndarray` and `force_ndarray_like` options must convert magnitude inputs into array-like magnitudes according to their documented names. The `default_as_delta` option must control whether non-multiplicative units in compound unit expressions are interpreted as their delta counterparts. The `autoconvert_offset_to_baseunit` option must control whether offset units in multiplicative arithmetic are automatically converted to base units instead of raising offset-calculus errors. The `auto_reduce_dimensions` option must reduce units after arithmetic where dimensional reduction is valid. The `autoconvert_to_preferred` option must convert arithmetic results to preferred units where preferred units are configured. The `preprocessors` option must apply each callable to every parsed expression or unit string before parsing. The `non_int_type` option must control the numeric type used for parsed non-integer values. The `cache_folder` option must either disable persistent registry caches when absent, use an automatic user cache directory when set to `":auto:"`, or use the supplied filesystem path. If an option value is unsupported for the requested operation, then construction or the first affected operation must raise the corresponding Python or Pint exception instead of silently using unrelated behavior.

## Quantity, Unit, And Measurement Behavior

Quantities and units are the user-facing projections of registry definitions and numeric magnitudes.

**Object Creation And Public Attributes.** A `Quantity` must be constructible from a magnitude plus units, from another quantity with optional conversion units, or from a parseable string containing a magnitude and units. Multiplying a number by a registry `Unit` must return a `Quantity`. A `Quantity` must expose `magnitude` and `m` as the raw magnitude, `units` and `u` as the bound `Unit`, `dimensionality` as a mapping-like dimensional expression, `dimensionless` as whether root dimensionality is empty, and `unitless` as whether root units are empty. A `Unit` must be constructible from a unit expression and must expose arithmetic behavior for combining units. A `Measurement` must represent a quantity with uncertainty and must expose `value`, `error`, and `rel` as quantities or relative uncertainty. If a measurement is created with a negative error, then `Measurement` must raise `ValueError`.

**Arithmetic And Comparison.** Quantity multiplication, division, and powers must combine magnitudes and units according to dimensional algebra. Quantity addition, subtraction, comparison, and equality must convert compatible operands to common units before comparing or combining magnitudes. If operands come from different registries, then arithmetic and comparison operations that require shared definitions must raise `ValueError`. If addition, subtraction, comparison, or conversion is requested for incompatible dimensionalities without an enabled context that supplies a transformation, then the operation must raise `DimensionalityError`. If arithmetic with offset or logarithmic units is ambiguous under the active registry options, then the operation must raise `OffsetUnitCalculusError` or `LogarithmicUnitCalculusError`.

**Conversion Methods.** `to` must return a new quantity expressed in destination units, and `ito` must update the original quantity in place and return `None`. `to_base_units` and `ito_base_units` must use the registry default system unless a `system` parameter names a different system. `to_root_units` and `ito_root_units` must convert to the primitive units from definition references before system-level base-unit substitutions. `to_reduced_units` and `ito_reduced_units` must reduce compound units to one unit per dimensionality where reduction is possible without expanding named derived units unnecessarily. `to_compact` and `ito_compact` must rescale to a human-readable prefixed unit, and a supplied unit parameter must restrict compaction to that unit family. `to_unprefixed` and `ito_unprefixed` must remove SI prefixes while staying in the same unit family. `to_preferred` and `ito_preferred` must express a quantity in a composition of preferred units supplied by the caller or configured on the registry. If a conversion target is missing, unknown, or dimensionally incompatible, then the conversion method must raise `UndefinedUnitError` or `DimensionalityError` according to the failing precondition.

**Serialization Helpers And Compatibility Queries.** `to_tuple` must return a tuple containing the magnitude and ordered unit-name exponent pairs, and `Quantity.from_tuple` must reconstruct an equivalent quantity from that tuple. `to_timedelta` must convert time-dimensional quantities to `datetime.timedelta` and must raise `DimensionalityError` for non-time dimensions. `m_as` must return only the magnitude expressed in destination units. `compatible_units` must return the set of named units with compatible dimensionality under optional contexts. `is_compatible_with` must return `True` for compatible quantities, units, strings, and dimensionless non-quantity objects, and must return `False` rather than raising `DimensionalityError` for incompatible dimensionality checks.

## Conversion Contexts And Unit Systems

Contexts and systems alter conversion behavior without changing the ordinary registry API used by quantities and units.

**Contexts.** A `Context` must accept an optional `name`, aliases, and default keyword parameters. `Context.add_transformation` must register a callable transformation from a source dimensionality to a destination dimensionality. `Context.redefine` must register a context-local redefinition for an existing unit. `UnitRegistry.add_context` must make a `Context` available by name and aliases. When a conversion receives context names or context objects, the conversion must apply those transformations for that operation only. When `UnitRegistry.context` is used as a context manager, the registry must enable the named contexts on entry and must restore the prior active-context stack on exit. When `enable_contexts` is called, the registry must leave the named contexts active until `disable_contexts` removes them. If multiple active contexts define a transformation for the same dimensionality pair, then the last enabled context must take precedence. If a named context is unknown, then enabling it or converting through it must raise `KeyError`. If a context transformation callable raises, then the conversion must propagate that exception.

**Parameterized And File-Defined Contexts.** Context defaults must be overridden by keyword arguments supplied to `to`, `ito`, `context`, `enable_contexts`, or `with_context`. Context definitions loaded from definition files must use `@context` to begin the context and `@end` to finish it. Context transformation expressions must receive the source quantity as `value`, must resolve other names first from context parameters and then from the registry, and must support one-way arrows and bidirectional arrows. Context redefinitions must affect conversions only while the context is active. If a context redefinition tries to create a brand-new unit, change dimensionality, redefine a prefixed unit, redefine a base unit, change aliases, change a symbol, redefine dimensions, or redefine prefixes, then enabling or using that context must raise an error.

**Systems And Groups.** A registry must expose available systems through `ureg.sys`, and each system projection must expose its member units through attribute lookup and `dir`. The `default_system` property must control which system is used by `to_base_units` when no explicit system is supplied. Setting `default_system` to a known system name must change later base-unit conversions without mutating existing quantity magnitudes until those quantities are converted. If `default_system` or a conversion `system` parameter names an unknown system, then the registry must raise `ValueError` or `KeyError`. A `Group` must represent a named set of units whose members include units from nested groups, and group membership loaded from definition files must be visible through registry group and system projections.

## Formatting And Text Output

Formatting turns registry-bound objects into strings while preserving the same unit definitions used for parsing and conversion.

**Format Specifications.** `str(quantity)` and `str(unit)` must use the registry formatter's default format. Python f-string formatting for `Quantity`, `Unit`, and `Measurement` must accept Pint format-spec components in any order: a magnitude format, the `~` short-unit modifier, the `^` negative-exponent modifier, the `#` compact-quantity modifier, and a Pint format type. The supported Pint format types must include default text `D`, pretty text `P`, HTML `H`, LaTeX `L`, LaTeX siunitx `Lx`, and compact text `C`. The `~` modifier must use symbols where symbols are defined. The `^` modifier must render denominator units as negative exponents. The `#` modifier on quantities must format the result after applying `to_compact`. If a format specification is invalid or unsupported, then formatting must raise `ValueError` or the corresponding formatting exception.

**Formatter Configuration.** The registry `formatter.default_format` value must fill in omitted Pint format-spec components. The registry `formatter.default_sort_func` must control ordering for compound units, and the default ordering must sort units alphabetically by name. Changing `formatter.dim_order` and assigning a dimensionality-based sort function must change the display order of later formatted compound units. `register_unit_format` must be usable as a decorator that registers a new unit format name. If a registered name already exists, then `register_unit_format` must raise `ValueError`. The top-level `formatter` function must format numerator and denominator `(name, exponent)` items with caller-supplied product, division, power, parenthesis, exponent, and ratio options. If the item structure is invalid for the requested formatting operation, then the formatter must raise the corresponding Python exception rather than inventing a unit string.

## Application Registry And Utility APIs

The top-level helpers provide shared registry behavior and dimensional-analysis utilities.

**Application Registry.** `pint.Quantity`, `pint.Unit`, and `pint.Measurement` must use the active application registry when invoked directly from the top-level package. `get_application_registry` must return the current application registry object, initially backed by a lazily created registry with the bundled default definitions. `set_application_registry` must replace the application registry used by top-level `Quantity`, `Unit`, `Measurement`, and unpickling. If `set_application_registry` receives an object that is not a `UnitRegistry`, a lazy registry, or another application-registry wrapper, then it must raise `TypeError`. When a pickled quantity, unit, or measurement is reconstructed, all referenced units must exist in the application registry or reconstruction must raise the applicable undefined-unit error.

**Utilities.** `pi_theorem` must accept a mapping of variable names to unit expressions, dimension expressions, quantities, or dimensionality mappings and must return a list of dimensionless products represented as dictionaries from variable name to exponent. `UnitRegistry.pi_theorem` must produce the same result while resolving dimensions through that registry. The result dictionaries must use the input variable names as keys and numeric exponents as values. If the input mapping cannot be resolved to dimensionalities, then `pi_theorem` must raise the corresponding parsing or dimensionality exception. `__version__` must be importable from `pint` and must be a string.

## Pint-Convert CLI

The `pint-convert` command exposes the registry parser and converter from a shell command.

**Invocation And Options.** The command must accept one required `from` argument containing a unit or quantity expression and one optional `to` argument containing destination units. When `to` is omitted, the command must convert the input quantity to base units in the selected system. The `--system` option and `-s` alias must select the unit system used for base-unit conversion and must default to `SI`. The `--prec` option and `-p` alias must set the maximum significant figures and must default to twelve. The `--prec-unc` option and `-u` alias must set the maximum uncertainty digits for uncertainty-aware output and must default to two. The `--with-unc` option and `-U` alias must request uncertainty-aware physical constants. The `--no-corr` option and `-C` alias must disable correlations between measured constants when uncertainty-aware output is active. If argument parsing fails, then the command must print help text and exit with argparse's usage-error status.

**Conversion Output.** The CLI must parse the `from` argument with `UnitRegistry.Quantity`, enable automatic dimensional reduction, enable offset conversion to base units, enable the `Gau`, `ESU`, `sp`, `energy`, and `boltzmann` contexts, and set `default_system` from the selected system. The command must print one line in the form `<source quantity> = <converted magnitude> <short pretty units>`. If `to` is supplied, then the converted quantity must use those units. If the input omits a numeric magnitude, then the source quantity must use magnitude one. If parsing, system lookup, context conversion, or dimensional conversion fails, then the command must terminate with a nonzero exception path. If `--with-unc` is requested while `uncertainties` is not importable, then the command must raise an exception instead of silently producing non-uncertainty output.

## State Model

The system maintains registry state: loaded definitions, parsed unit aliases, prefixes, dimensions, systems, groups, contexts, formatter configuration, preferred-unit settings, and application-registry selection. The public projections are:

1. Registry construction, membership, attribute lookup, item lookup, `define`, and `load_definitions`.
2. `Quantity`, `Unit`, and `Measurement` objects bound to a registry.
3. Conversion results from `to`, `ito`, base/root/reduced/compact/preferred conversions, contexts, and systems.
4. String parsing and formatting results from registry parsers, f-strings, `str`, registered unit formats, and the top-level formatter utility.
5. Context, group, and system projections exposed through `Context`, `ureg.context`, `enable_contexts`, `disable_contexts`, `ureg.sys`, and `default_system`.
6. Top-level application registry helpers and the `pint-convert` command.

## Error Semantics

| Condition | Required result |
|---|---|
| Unknown unit name during attribute lookup, item lookup, expression parsing, unit parsing, conversion target parsing, or unpickling | Raise `UndefinedUnitError` |
| Conversion, addition, subtraction, or comparison across incompatible dimensionalities without an active context transformation | Raise `DimensionalityError` |
| Ambiguous arithmetic involving offset units while automatic offset conversion is disabled | Raise `OffsetUnitCalculusError` |
| Inappropriate arithmetic involving logarithmic units | Raise `LogarithmicUnitCalculusError` |
| Invalid definition-file syntax or invalid single-line definition syntax | Raise `DefinitionSyntaxError` |
| Redefinition while the registry `on_redefinition` policy is `raise` | Raise `RedefinitionError` |
| Creating a `Measurement` with negative error magnitude | Raise `ValueError` |
| Calling `Quantity.from_list` or `Quantity.from_sequence` with an empty sequence and no `units` value | Raise `ValueError` |
| Registering a custom unit format name that already exists | Raise `ValueError` |
| Passing a non-registry object to `set_application_registry` | Raise `TypeError` |
| Requesting an unknown context by name | Raise `KeyError` |
| Requesting an unknown system for `default_system`, `to_base_units`, or `pint-convert --system` | Raise `ValueError` or `KeyError` |
| Passing CLI arguments that argparse rejects | Print help text and exit with argparse's usage-error status |
| Requesting `pint-convert --with-unc` without an importable `uncertainties` package | Raise an exception and terminate nonzero |

## Cross-View Invariants

1. A unit defined through `UnitRegistry.define` or `load_definitions` must be visible through registry membership, attribute lookup, item lookup, parsing, quantity construction, conversion, and formatting.
2. A quantity produced by multiplication, `Quantity`, registry call parsing, or `parse_expression` must carry the same registry-bound `Unit` behavior for arithmetic, conversion, dimensionality, and formatting.
3. `to` and `ito` must compute the same converted magnitude and units for the same source quantity and destination, while `to` returns a new quantity and `ito` mutates the original quantity.
4. Base-unit conversion must reflect `default_system` in registry-level conversions, quantity conversion methods, and `pint-convert` output when the CLI system option names the same system.
5. An enabled context must affect `Quantity.to`, `Quantity.ito`, `compatible_units`, `is_compatible_with`, and registry conversions consistently, and disabling that context must restore the previous dimensionality rules.
6. Formatter configuration on a registry must affect `str`, f-string formatting, `Quantity`, `Unit`, and `Measurement` projections for objects bound to that registry.
7. The application registry selected by `set_application_registry` must be the registry used by top-level `pint.Quantity`, `pint.Unit`, `pint.Measurement`, and unpickling.
8. A serialized quantity tuple from `to_tuple` must reconstruct through `Quantity.from_tuple` into a quantity with equivalent magnitude, units, conversion behavior, and formatting.
9. A unit system exposed through `ureg.sys` must use the same system definitions as `default_system` and `to_base_units`.
10. The `pint-convert` command must produce the same destination units and compatible converted magnitude as the Python API using the same input expression, destination units, system, precision policy, and enabled contexts.

## Public Interface

### Import Surface

```python
import pint
from pint import (
    Context,
    DefinitionSyntaxError,
    DimensionalityError,
    Group,
    LogarithmicUnitCalculusError,
    Measurement,
    OffsetUnitCalculusError,
    PintError,
    Quantity,
    RedefinitionError,
    Unit,
    UnitRegistry,
    UnitStrippedWarning,
    UndefinedUnitError,
    __version__,
    formatter,
    get_application_registry,
    pi_theorem,
    register_unit_format,
    set_application_registry,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Context` | class | Represents named or anonymous conversion transformations and context-local unit redefinitions. |
| `DefinitionSyntaxError` | exception | Reports invalid textual definition syntax. |
| `DimensionalityError` | exception | Reports operations or conversions between incompatible dimensionalities. |
| `Group` | class | Represents a named set of units used by group and system definitions. |
| `LogarithmicUnitCalculusError` | exception | Reports invalid arithmetic involving logarithmic units. |
| `Measurement` | class | Represents a quantity with uncertainty and exposes value, error, and relative uncertainty projections. |
| `OffsetUnitCalculusError` | exception | Reports ambiguous arithmetic involving offset units. |
| `PintError` | exception | Base exception type for Pint-specific errors. |
| `Quantity` | class | Represents a magnitude bound to units from a registry. |
| `RedefinitionError` | exception | Reports forbidden redefinition of an existing registry name. |
| `Unit` | class | Represents a unit expression bound to a registry. |
| `UnitRegistry` | class | Stores unit definitions and creates, parses, converts, and formats registry-bound objects. |
| `UnitStrippedWarning` | warning | Warns when an operation strips units from a quantity. |
| `UndefinedUnitError` | exception | Reports names that are absent from a registry. |
| `__version__` | constant | Exposes the installed package version string or an unknown-version string. |
| `formatter` | function | Formats numerator and denominator unit terms into a textual compound-unit expression. |
| `get_application_registry` | function | Returns the registry wrapper used by top-level quantity, unit, measurement, and unpickling operations. |
| `pi_theorem` | function | Computes dimensionless products from a mapping of variable names to dimensional inputs. |
| `register_unit_format` | function | Registers a custom unit format under a format-spec name. |
| `set_application_registry` | function | Replaces the registry used by top-level quantity, unit, measurement, and unpickling operations. |

### CLI Entry Points

Console script: `pint-convert`

| Exit | Meaning |
|---:|---|
| 0 | Arguments parsed successfully and conversion output was printed. |
| 2 | Argument parsing failed and argparse printed help text. |
| nonzero | Parsing, unit lookup, context, system, dimensionality, or optional uncertainty handling failed by exception. |

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access.
The following third-party packages are preinstalled and importable:
`flexcache`, `flexparser`, `platformdirs`, and `typing_extensions`.
The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard
`pyproject.toml` (or `setup.py`) at the project root so the package
is installable with pip.

## Appendix B: Assessment Notes

Assessment focuses on observable behavior across the documented public API: registry construction, definition loading, parsing, quantity and unit arithmetic, conversions, contexts, systems, formatting, application registry helpers, error types, and the `pint-convert` command. Tests use public imports, public methods, public attributes, and command-line execution.

Assessment does not depend on private module layout, exact `repr()` output, exact exception message text, cache internals, timing, or optional ecosystem integrations. Correct implementations are expected to satisfy rule-level behavior across families of inputs rather than memorizing individual example values.
