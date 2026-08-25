# Traitlets Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Traitlets provides typed attributes for Python classes. A class that inherits from `HasTraits` declares trait attributes as class attributes, and instances get runtime type validation, dynamic default values, metadata, change notifications, and custom validation hooks.

Traitlets also provides a configuration layer. `Config` stores hierarchical values, `Configurable` applies those values to traits tagged with `config=True`, and `Application` connects config files, command-line arguments, subcommands, and logging to a running program.

## Non-Goals

- Exact wording, spacing, and ordering of help text, warning text, logging output, generated RST, and generated config comments are outside this specification.
- Private modules, private helper functions, compatibility shims, and tests-only utilities are outside this specification.
- Static typing checker behavior is outside this specification except for runtime importability and runtime signatures described in behavior sections.
- Optional shell completion integration is outside this specification except that configured aliases, flags, and configurable traits must remain discoverable by the public application metadata APIs.
- Legacy observer naming conventions and legacy sentinel construction patterns are outside this specification.
- Binary compatibility with older releases is outside this specification.

## Representative Workflows

### Trait Object With Defaults, Validation, and Observation

```python
from traitlets import HasTraits, Int, Unicode, TraitError, default, observe, validate

class Account(HasTraits):
    name = Unicode()
    balance = Int()

    @default("name")
    def _default_name(self):
        return "guest"

    @validate("balance")
    def _valid_balance(self, proposal):
        if proposal["value"] < 0:
            raise TraitError("balance must be non-negative")
        return proposal["value"]

    @observe("balance")
    def _balance_changed(self, change):
        self.last_change = (change.old, change.new)

account = Account(balance=5)
account.name        # returns "guest"
account.balance = 7 # records (5, 7)
```

This workflow must reject `account.balance = -1` with `TraitError`, must keep `account.balance == 7`, and must not emit a successful change notification for the rejected value.

### Configurable Application

```python
from traitlets import Bool, Unicode
from traitlets.config import Application, Configurable

class Worker(Configurable):
    enabled = Bool(False, help="enable worker").tag(config=True)
    label = Unicode("default", help="worker label").tag(config=True)

class WorkerApp(Application):
    classes = [Worker]
    aliases = {"label": "Worker.label"}
    flags = {"enable-worker": ({"Worker": {"enabled": True}}, "enable worker")}

app = WorkerApp.instance()
app.initialize(["--label=cli", "--enable-worker"])
worker = Worker(config=app.config)
```

The worker must have `label == "cli"` and `enabled is True`. A config file value for `Worker.label` must be overridden by the command-line alias when both are loaded into the same application.

## Configuration Objects

This section covers `Config` dictionaries, lazy container updates, and config merging.

**Attribute and item access.** `Config` must behave as a dictionary with attribute access. Accessing an uppercase missing attribute such as `cfg.Section` must create and return a nested `Config` section. Accessing a lowercase missing attribute must raise `AttributeError`. `cfg.Section.name = value` and `cfg["Section"]["name"] = value` must refer to the same stored value.

**Merging and collisions.** `Config.merge(other)` must merge another config into the receiver. Values from `other` must override conflicting existing scalar values. Nested sections must merge recursively so non-conflicting keys are preserved. `collisions(other)` must return a dictionary describing keys where both configs define different values; it must return an empty dictionary when there are no conflicts.

**Lazy container updates.** `LazyConfigValue` must record container updates such as `append`, `extend`, `prepend`, `insert`, `update`, and `add`. `get_value(existing)` must apply the recorded operations to the supplied existing value and return the merged result. When applied to a list, `prepend` items must appear before the existing elements and `append` items must appear after them. When applied to a dictionary, `update` must merge key-value pairs into the existing mapping. When applied to a set, `add` must include new elements in the existing set. Invalid lazy operations for the target type must raise an exception instead of silently discarding the operation.

## Configurable Classes

This section covers how `Configurable` subclasses load trait values from `Config` objects and how singletons manage their lifecycle.

**Config-driven trait initialization.** `Configurable` is a `HasTraits` subclass with a `config` trait. A trait tagged with `config=True` must be loadable from a `Config` section named for the class. When a config contains a key for a known configurable trait, constructing or updating a `Configurable` must assign that value through normal trait validation. Invalid config values must raise `TraitError`. Config keys for traits that are not tagged `config=True` must not silently configure those traits; they must be ignored with a warning or rejected according to the same error policy used by the configurable object. Constructor keyword values must override values loaded from `config`.

**Config inheritance.** A config section for a base class must apply to subclasses. A subclass-specific section must override an inherited base-class config value for the same trait.

**Config updates and introspection.** `update_config(config)` must merge the new config into the instance config and must update currently configurable trait values. `section_names()` returns the config section names considered for the class, including inherited configurable class names. `class_get_help`, `class_print_help`, `class_config_section`, and `class_config_rst_doc` return or print human-readable documentation for configurable traits; they must raise normal trait or formatting errors for invalid class state.

**Logging configurable.** `LoggingConfigurable` must provide a `.log` trait containing a logger. Passing a non-logger value for `.log` must raise `TraitError`.

**Singleton lifecycle.** `SingletonConfigurable.instance()` returns the canonical instance for the singleton class. The first call must create it. Later calls with no arguments must return the same instance. Later calls with arguments after an instance already exists must raise `MultipleInstanceError`. `clear_instance()` must clear the canonical instance for that singleton class hierarchy. `initialized()` must return whether an instance currently exists.

## Application, Config Files, and CLI

This section covers how `Application` connects config files, command-line arguments, subcommands, and configurable classes into a running program.

**Initialization and launch.** `Application` is a `SingletonConfigurable`. `Application.initialize(argv=None)` must parse command-line arguments, initialize subcommands when present, and populate `cli_config`, `config`, and `extra_args`. `Application.launch_instance(argv=None, **kwargs)` must create or reuse the singleton, initialize it, and start it.

**Config file loading.** `Application.load_config_file(filename, path=None)` must load Python and JSON config files matching the requested base name from the search path. When both same-base Python and JSON files are present in the same directory, the JSON config values must override conflicting Python config values. When the same base name is found in multiple search directories, files from earlier directories in `path` must have higher priority than later directories. Command-line config already parsed into `cli_config` must override conflicting values read from config files. `Application.loaded_config_files` must return the loaded config file paths in the order they were loaded.

**Config file loaders.** `JSONFileConfigLoader`, `PyFileConfigLoader`, and `KVArgParseConfigLoader` must each expose a `load_config()` method that parses their respective config source and returns a `Config` object. `JSONFileConfigLoader` must accept a filename and an optional `path` for the search directory; when the requested file is not found and the loader requires it, it must raise `ConfigFileNotFound`. `PyFileConfigLoader` must execute Python config files with `get_config()` returning the active `Config` object as `c`. `load_subconfig(name)` inside a Python config file must load another Python config using the parent config file search path, and values assigned after `load_subconfig` must override conflicting values from the loaded subconfig. `KVArgParseConfigLoader` must accept a list of command-line arguments and a `classes` parameter listing configurable classes whose traits the loader must recognize.

**Config file errors.** `Application.load_config_environ()` must read supported environment variables and update application config accordingly. When a config file raises an error, the default behavior must log a warning and ignore that file; when `raise_config_file_errors` is true, the application must raise or exit on the file loading error.

**Command-line parsing.** The command-line form `--Class.trait=value` and the separated form `--Class.trait value` must set configurable traits. Aliases in `Application.aliases` must map shorter option names to `Class.trait`; flags in `Application.flags` must set one or more config values without consuming a value. `boolean_flag(name, configurable, set_help="", unset_help="")` must return paired flag definitions for enabling and disabling a boolean config value, producing both a `name` flag that sets the trait to `True` and a `no-name` flag that sets the trait to `False`.

**Repeated options.** Repeated scalar command-line options for the same trait must raise an initialization error. Repeated `List` options must accumulate values in order. Repeated `Dict` options must accept `key=value` items and merge them into a dictionary. Invalid option names, invalid values, or invalid repeated scalar usage must raise `ArgumentError`, `TraitError`, or terminate application initialization with a nonzero `SystemExit`.

**Subcommands.** `Application.subcommands` maps subcommand names to an application class, import string, or factory plus a help string. When the first positional argument names a subcommand, the parent application must instantiate the sub-application, store it on `subapp`, and initialize it with the remaining arguments. Unknown subcommands must remain normal extra arguments or raise the same command-line error used for unrecognized options, according to the parser path used by the application.

**Configuration display and help.** When `show_config` or `show_config_json` is true, `Application.start()` must print the current configuration in text or JSON form and must not run subclass-specific application work after showing the config. When `show_config_json` is true, the output must be valid JSON containing the current configurable trait values. `print_help`, `emit_help`, `print_version`, and related help methods must expose aliases, flags, subcommands, and configurable options for the classes known to the application.

## Trait Declaration and Types Behavior

This section covers how trait types validate, store, and expose typed attribute values on `HasTraits` instances, including dynamic defaults, change observers, custom validators, held notifications, introspection, and links.

**Base descriptor and constructor.** `TraitType` is the base descriptor for traits. A subclass of `HasTraits` must accept trait values as keyword arguments in its constructor. Passing an unknown trait name to `HasTraits` must raise `TraitError`. Passing a value rejected by the trait type or by a validator must raise `TraitError` and must leave the previous stored value unchanged.

**Trait metadata.** Trait metadata supplied in the constructor or through `.tag(**metadata)` must be visible through the trait object and through `HasTraits.trait_metadata(name, key, default=None)`. `.tag()` must return the same trait object, so declarations such as `Unicode().tag(config=True)` must define a configurable trait. `trait_metadata` must return the requested metadata value when present and must return the provided default when absent; it must raise `KeyError` or `TraitError` when the trait name is not defined.

**Sentinels.** `Undefined` represents an unspecified default. `All` represents all trait names or all notification types in APIs that accept it.

**Numeric types.** `Integer`, `Int`, and `Long` must accept Python integers and must reject non-integers with `TraitError`. `Float` must accept floats and integers as numeric values and must reject non-numeric values with `TraitError`. `Complex` must accept complex-compatible numeric values and must reject invalid values with `TraitError`. `CInt`, `CLong`, `CFloat`, and `CComplex` must coerce by calling the corresponding Python constructor and must raise `TraitError` when conversion fails.

**String types.** `Unicode` must accept `str` values and must reject non-string values with `TraitError`. `Bytes` must accept `bytes` values and must reject non-bytes values with `TraitError`. `CUnicode` and `CBytes` must coerce by calling the corresponding Python constructor but must not silently encode or decode between text and bytes unless that constructor accepts the input.

**Boolean and enumeration types.** `Bool` must accept booleans and must reject non-boolean values with `TraitError`; command-line strings for boolean values must be accepted through `from_string`. `CBool` must coerce with `bool(value)`. `Enum(values)` must accept only members of `values`; it must raise `TraitError` for a value outside the declared set. `CaselessStrEnum` must compare string values without case sensitivity and must store the lowercased canonical form. `FuzzyEnum` must support substring-matching modes; when `case_sensitive` is true, matching must be case-exact. When an input prefix matches a single declared value unambiguously, the full value must be stored. When the input is ambiguous or does not match any declared value, it must raise `TraitError`. `UseEnum(enum_class)` must store members of the given enum class and must resolve allowed names and values according to that enum class.

**Identifier and address types.** `ObjectName` must accept a valid Python identifier string and must reject strings containing spaces or other non-identifier characters with `TraitError`. `DottedObjectName` must accept dot-separated valid identifiers. `TCPAddress` must accept `(host, port)` values where the host is a string and the port is an integer in the valid TCP port range; it must raise `TraitError` for malformed addresses including out-of-range ports.

**Instance, type, and reference types.** `Instance(klass)` must accept instances of `klass`. When `klass` is a string, it must resolve that class lazily. When `args` or `kw` are provided and no explicit default value is provided, the default value must be constructed from `klass(*args, **kw)`. `Type(klass=klass)` must accept classes that are subclasses of `klass`. `This` must accept instances of the owning `HasTraits` class; when `allow_none=True` is set, it must also accept `None`. Forward-declared class and instance traits must resolve their target class before validation and must raise `TraitError` when validation fails.

**Container types.** `List` must store a list, `Set` must store a set, and `Tuple` must store a tuple. Container traits must validate element traits when provided. When `minlen` is set, the container must reject values with fewer elements than the minimum; when `maxlen` is set, it must reject values exceeding the maximum. They must raise `TraitError` when the value has the wrong container type, violates length bounds, or contains an invalid element. `Dict` must store a dictionary, validate keys with the configured `key_trait`, validate general values with `value_trait`, and validate named keys with `per_key_traits`.

**Composite and utility types.** `Union(trait_types)` must accept a value accepted by one of its member trait types and must raise `TraitError` only when all member traits reject the value. `Any` must accept any value except that `allow_none=False` still rejects `None` when a non-`None` default policy applies. `Callable` must accept callable values and must reject non-callable values with `TraitError`. `CRegExp` must accept or compile regular expression values and must raise `TraitError` for invalid regular expressions.

**Command-line string parsing.** `TraitType.from_string(s)` must return a Python value parsed from a command-line string. Scalar traits must parse their own strings. `List.from_string_list(values)` and `Dict.from_string_list(values)` must parse repeated command-line occurrences; list items must be passed through item parsing, and dict items must use `key=value` strings. When a dict item lacks the `key=value` separator, `Dict.from_string_list` must raise an exception. Invalid command-line strings must raise `TraitError` or `ArgumentError` through the config loader.

**Dynamic defaults.** `@default(name)` registers a method that returns the dynamic default for one trait. The method must be called only when the trait value is first needed and no value was supplied earlier. A constructor keyword value must override the dynamic default and must not call the default method for that trait.

**Change observers.** `@observe(*names, type="change")` registers a method as an observer. `HasTraits.observe(handler, names=All, type="change")` must register a runtime observer. When a trait changes to a different value, observers for that name and notification type must receive a `Bunch` change object containing `owner`, `name`, `old`, `new`, and `type`. The same values must be available by key and by attribute. Assigning the current value again must not emit a change notification. `unobserve(handler, names=All, type="change")` must remove a matching observer. `unobserve_all(name=All)` must remove registered observers for the selected name or all names.

**Custom validators.** `@validate(*names)` registers a method that receives a proposal object with at least `owner`, `trait`, `value`, and `name`. The validator's return value must become the stored trait value. A validator that raises `TraitError` must reject the assignment and must leave the old stored value unchanged. A validator that returns `None` must store `None` when the trait accepts `None` and must otherwise fail validation.

**Held notifications.** `hold_trait_notifications()` returns a context manager. Inside the context, change notifications and cross-validation must be delayed. When the context exits successfully, delayed changes must be validated and notified. When validation fails at exit, the object must roll back to the values it had before the context and must raise `TraitError`.

**Trait introspection.** `HasTraits.has_trait(name)` must return `True` when the instance has a trait named `name`; otherwise it must return `False`. `trait_has_value(name)` must return whether a value is already stored for a trait without forcing dynamic default generation. `trait_names(**metadata)` must return a list of trait names filtered by metadata. `traits(**metadata)` must return a dictionary mapping names to trait objects. Class-level methods `class_trait_names`, `class_traits`, and `class_own_traits` must return the corresponding class-level views. `trait_values()` must return current trait values and must force defaults for traits that need values. `trait_defaults(*names)` must return default values for the requested traits.

**Runtime trait manipulation.** `add_traits(**traits)` must add trait descriptors to an instance at runtime, initialize them for that instance, and make them visible through introspection. `set_trait(name, value)` must assign through the same validation and notification path as attribute assignment and must raise `TraitError` or `AttributeError` for an unknown trait.

**Trait links.** `link(source, target, transform=None)` must keep two trait attributes synchronized in both directions. `source` and `target` are `(object, trait_name)` pairs. When either side changes, the other side must be assigned the transformed value. When `transform` is provided, it must contain a forward and reverse transform as a two-element tuple; a source change must apply the forward transform to compute the target value, and a target change must apply the reverse transform to compute the source value. `directional_link(source, target, transform=None)` and `dlink` must synchronize only from source to target. `unlink()` must detach the observers created by a link; after `unlink()`, later source or target changes must no longer propagate through that link. Invalid endpoint tuples or unknown trait names must raise `TypeError`, `ValueError`, or `TraitError` before linking.

**Bunch.** `Bunch` must behave like a dictionary whose keys are also available as attributes. Setting or deleting an attribute must affect the same value visible through item access. Missing attributes must raise `AttributeError`; missing keys must raise `KeyError`.

**Utility functions.** `import_item(name)` must return the object named by a dotted import string. It must import a module when `name` contains only a module path, and it must return an attribute when the final component names an object inside an imported module. It must raise `ImportError` when the module or item does not exist. `signature_has_traits(cls)` returns the same class with a constructor signature that includes keyword-only parameters for trait names and their defaults. It must preserve the explicit parameters of the original constructor. It must raise the same errors as normal class construction when an invalid trait keyword or invalid trait value is passed.

## State Model

Traitlets exposes state through four public projections:

- Trait attribute projection: normal Python attribute access on `HasTraits` and `Configurable` instances.
- Descriptor and metadata projection: `TraitType` objects, class trait dictionaries, metadata tags, and default values.
- Event projection: observer, validator, link, and held-notification behavior.
- Configuration projection: `Config` dictionaries, config files, command-line arguments, and `Application.config`.

A value written through any public assignment path must pass the trait descriptor before it becomes visible in the attribute projection. A value rejected by validation must not become visible in any projection.

## Error Semantics

- `TraitError` must be raised for invalid trait assignment, invalid custom validation, invalid container elements, invalid enum choices, invalid TCP addresses, and invalid configurable values.
- `KeyError`, `AttributeError`, or `TraitError` must be raised for unknown trait or metadata names according to the public method being called.
- `ImportError` must be raised by `import_item` when the requested import path or final item does not exist.
- `ConfigFileNotFound` must be raised by file config loaders when a requested config file is not found and the loader is required to find it.
- `ConfigError`, `ConfigLoaderError`, and `ArgumentError` must represent config loading and command-line parsing failures.
- `MultipleInstanceError` must be raised when singleton creation is requested with new arguments after the singleton instance already exists.
- `ApplicationError` must represent application-level failures raised by the application layer.
- `SystemExit` with a nonzero status must be raised when application command-line initialization terminates due to a fatal config parsing error.

## Cross-View Invariants

1. A trait value assigned by normal attribute access must be the same value returned by `getattr`, `trait_values()`, observer `new`, and any linked target after validation succeeds.
2. A trait value assigned by constructor keyword must override a dynamic default for that trait, must be visible through attribute access, and must not invoke the registered default method for that trait.
3. A trait metadata value set by `.tag(config=True, help=...)` must be visible in the trait object, in `trait_metadata`, in `traits(config=True)`, and in configurable help/config-section output.
4. A value rejected by a trait validator must remain absent from attribute access, `trait_values`, observer notifications, links, and configurable instance state.
5. A value accepted and transformed by a validator must be the stored attribute value, the value seen by observers as `new`, and the value propagated through links.
6. A value set in `Config` through `cfg.Class.trait` must be the same value visible through `cfg["Class"]["trait"]` and must configure a matching `Configurable` trait tagged with `config=True`.
7. A `Config` value inherited from a base class section must configure subclass instances unless the subclass section provides a conflicting value for the same trait.
8. A constructor keyword on a `Configurable` must override the value loaded from `Config`, and the resulting attribute value must be the value seen by trait introspection and observers registered during later changes.
9. An `Application` command-line value must override a conflicting config-file value in `Application.config`, and a `Configurable` constructed from that config must receive the command-line value.
10. A config value loaded from a JSON file must override a conflicting value from the same-base Python config file in the same directory, and the resulting `Configurable` attribute must match the JSON value.
11. A linked trait update must pass through the target trait's validation before the target attribute changes; if validation fails, the source assignment must raise or leave the target unchanged according to the same assignment path used without a link.

## Public Interface

### Import Surface

The package must be importable as `traitlets`. The top-level package returns these documented public names:

```python
from traitlets import (
    All, Undefined, TraitError, TraitType, HasTraits, HasDescriptors,
    Any, Bool, Bytes, CBool, CBytes, CComplex, CFloat, CInt, CLong,
    CRegExp, CUnicode, Callable, CaselessStrEnum, Complex, Container,
    Dict, DottedObjectName, Enum, Float, FuzzyEnum, Instance, Int,
    Integer, List, Long, ObjectName, Set, TCPAddress, This, Tuple,
    Type, Unicode, Union, UseEnum, default, observe, observe_compat,
    parse_notifier_name, link, directional_link, dlink, Bunch,
    import_item, signature_has_traits, validate,
)
```

The configuration package must be importable as `traitlets.config` and returns:

```python
from traitlets.config import (
    Config, Application, ApplicationError, Configurable,
    ConfigurableError, MultipleInstanceError, LoggingConfigurable,
    SingletonConfigurable,
)
```

The documented loader helpers must be importable from `traitlets.config.loader`, including `JSONFileConfigLoader`, `PyFileConfigLoader`, `KVArgParseConfigLoader`, `LazyConfigValue`, `ConfigError`, `ConfigLoaderError`, `ConfigFileNotFound`, and `ArgumentError`. The helper functions `boolean_flag` and `get_config` must be importable from `traitlets.config.application`.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| HasTraits | class | Base class for objects with typed trait attributes |
| HasDescriptors | class | Base class for descriptor-aware trait containers |
| TraitType | class | Base descriptor for trait declarations |
| Undefined | sentinel | Represents an unspecified default value |
| All | sentinel | Represents all trait names or notification types |
| TraitError | exception | Raised for invalid trait assignment or validation |
| default | decorator | Register a dynamic default provider for one trait |
| observe | decorator | Register a change observer for one or more traits |
| observe_compat | decorator | Compatibility wrapper for observer registration |
| validate | decorator | Register a custom validator for one or more traits |
| link | function | Bidirectionally synchronize two trait attributes |
| directional_link | function | Synchronize one trait attribute from another |
| dlink | function | Alias for directional_link |
| Bunch | class | Attribute-and-item mapping for change notifications |
| import_item | function | Import an object from a dotted import string |
| signature_has_traits | function | Expose trait defaults on a class constructor signature |
| parse_notifier_name | function | Parse observer notification names |
| Integer | trait type | Integer-valued trait |
| Int | trait type | Integer-valued trait alias |
| Long | trait type | Long integer-valued trait |
| Float | trait type | Floating-point trait |
| Complex | trait type | Complex-number trait |
| CInt | trait type | Coercing integer trait |
| CLong | trait type | Coercing long integer trait |
| CFloat | trait type | Coercing float trait |
| CComplex | trait type | Coercing complex trait |
| Unicode | trait type | Text trait |
| Bytes | trait type | Bytes trait |
| CUnicode | trait type | Coercing text trait |
| CBytes | trait type | Coercing bytes trait |
| Bool | trait type | Boolean trait |
| CBool | trait type | Coercing boolean trait |
| Enum | trait type | Fixed-set enumeration trait |
| CaselessStrEnum | trait type | Case-insensitive string enumeration trait |
| FuzzyEnum | trait type | Substring-matching enumeration trait |
| UseEnum | trait type | Python enum-backed trait |
| ObjectName | trait type | Python identifier string trait |
| DottedObjectName | trait type | Dot-separated identifier string trait |
| TCPAddress | trait type | Host and port address trait |
| Instance | trait type | Instance-of-class trait |
| Type | trait type | Subclass-of-class trait |
| This | trait type | Instance-of-owning-class trait |
| List | trait type | List container trait |
| Set | trait type | Set container trait |
| Tuple | trait type | Tuple container trait |
| Dict | trait type | Dictionary container trait |
| Union | trait type | Accept-any-member trait |
| Any | trait type | Accept-any-value trait |
| Callable | trait type | Callable-value trait |
| CRegExp | trait type | Regular-expression trait |
| Container | trait type | Base container trait type |
| Config | class | Hierarchical configuration mapping |
| Configurable | class | HasTraits subclass loadable from Config |
| LoggingConfigurable | class | Configurable with a logger trait |
| SingletonConfigurable | class | Configurable with a canonical instance |
| Application | class | Configurable application with CLI and config files |
| ApplicationError | exception | Application-layer failure |
| ConfigurableError | exception | Configurable-object failure |
| MultipleInstanceError | exception | Raised on invalid singleton re-creation |
| LazyConfigValue | class | Deferred container update for config merge |
| JSONFileConfigLoader | class | Load JSON configuration files |
| PyFileConfigLoader | class | Load Python configuration files |
| KVArgParseConfigLoader | class | Parse command-line config arguments |
| ConfigError | exception | Configuration error |
| ConfigLoaderError | exception | Config loader failure |
| ConfigFileNotFound | exception | Missing required config file |
| ArgumentError | exception | Command-line parsing failure |
| boolean_flag | function | Build paired boolean CLI flag definitions |
| get_config | function | Return the active Config during config file execution |

### CLI Entry Points

There is no console script for this package. `python -m traitlets` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

A complete implementation should be checked through the public imports and runtime behaviors described in this specification. Compatibility should be assessed across trait declaration, assignment validation, dynamic defaults, metadata introspection, observers, validators, held notifications, links, config object views, configurable inheritance, singleton lifecycle, config file loading, command-line parsing, and application workflows.

Formatting-only differences in help text, warnings, logging text, generated documentation, or generated config comments are not part of this contract unless they change a runtime behavior described above. Private helpers, deprecated compatibility shims, and static type checker behavior are outside the compatibility surface.
