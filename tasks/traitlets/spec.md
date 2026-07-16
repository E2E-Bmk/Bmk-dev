# Traitlets Specification

## Product Overview

Traitlets provides typed attributes for Python classes. A class that inherits from `HasTraits` declares trait attributes as class attributes, and instances get runtime type validation, dynamic default values, metadata, change notifications, and custom validation hooks.

Traitlets also provides a configuration layer. `Config` stores hierarchical values, `Configurable` applies those values to traits tagged with `config=True`, and `Application` connects config files, command-line arguments, subcommands, and logging to a running program.

## Scope

This specification covers:

- Public imports from `traitlets` and `traitlets.config` used to define trait attributes, observe changes, validate values, introspect metadata, link objects, import names by string, and expose trait-aware constructor signatures.
- Built-in trait type behavior for scalar, string, enum, class, instance, container, union, callable, and TCP address traits.
- `Config`, Python and JSON config file loading, `Configurable`, `SingletonConfigurable`, `LoggingConfigurable`, and `Application` behavior.
- Command-line parsing for `--Class.trait`, aliases, flags, subcommands, repeated container options, repeated scalar options, and show-config options.

## Installable Surface

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
    import_item, signature_has_traits,
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

## Public API

### Trait Declaration

`TraitType(default_value=Undefined, allow_none=False, read_only=None, help=None, config=None, **metadata)` is the base descriptor for traits. A subclass of `HasTraits` must accept trait values as keyword arguments in its constructor. Passing an unknown trait name to `HasTraits` must raise `TraitError`. Passing a value rejected by the trait type or by a validator must raise `TraitError` and must leave the previous stored value unchanged.

Trait metadata supplied in the constructor or through `.tag(**metadata)` must be visible through the trait object and through `HasTraits.trait_metadata(name, key, default=None)`. `.tag()` returns the same trait object, so declarations such as `Unicode().tag(config=True)` must define a configurable trait. `trait_metadata` returns the requested metadata value when present and returns the provided default when absent; it raises `KeyError` or `TraitError` when the trait name is not defined.

`Undefined` represents an unspecified default. `All` represents all trait names or all notification types in APIs that accept it.

### Built-In Trait Types

`Integer`, `Int`, and `Long` must accept Python integers and must reject non-integers with `TraitError`. `Float` must accept floats and integers as numeric values and must reject non-numeric values with `TraitError`. `Complex` must accept complex-compatible numeric values and must reject invalid values with `TraitError`. `CInt`, `CLong`, `CFloat`, and `CComplex` must coerce by calling the corresponding Python constructor and must raise `TraitError` when conversion fails.

`Unicode` must accept `str` values and must reject non-string values with `TraitError`. `Bytes` must accept `bytes` values and must reject non-bytes values with `TraitError`. `CUnicode` and `CBytes` must coerce by calling the corresponding Python constructor but must not silently encode or decode between text and bytes unless that constructor accepts the input.

`Bool` must accept booleans and command-line strings for boolean values through `from_string`. `CBool` must coerce with `bool(value)`. `Enum(values, default_value=Undefined, allow_none=False, ...)` must accept only members of `values`; it must raise `TraitError` for a value outside the declared set. `CaselessStrEnum` must compare string values without case sensitivity. `FuzzyEnum` must support its declared case-sensitive and substring-matching modes and must raise `TraitError` when the input is ambiguous or not accepted. `UseEnum(enum_class, default_value=None, **kwargs)` must store members of the given enum class and must resolve allowed names and values according to that enum class.

`ObjectName` must accept a valid Python identifier string. `DottedObjectName` must accept dot-separated valid identifiers. `TCPAddress` must accept `(host, port)` values where the host is a string and the port is an integer in the TCP port range; it must raise `TraitError` for malformed addresses.

`Instance(klass=None, args=None, kw=None, allow_none=False, ...)` must accept instances of `klass`. When `klass` is a string, it must resolve that class lazily. When `args` or `kw` are provided and no explicit default value is provided, the default value for an instance must be constructed from `klass(*args, **kw)`. `Type(default_value=Undefined, klass=None, ...)` must accept classes that are subclasses of `klass`. `This` must accept instances of the owning `HasTraits` class. Forward-declared class and instance traits must resolve their target class before validation and must raise `TraitError` when validation fails.

`List(trait=None, default_value=Undefined, minlen=0, maxlen=sys.maxsize, **kwargs)` must store a list. `Set` must store a set. `Tuple(*traits, **kwargs)` must store a tuple. Container traits must validate length bounds and element traits. They must raise `TraitError` when the value has the wrong container type, violates length bounds, or contains an invalid element. `Dict(value_trait=None, per_key_traits=None, key_trait=None, default_value=Undefined, **kwargs)` must store a dictionary, validate keys with `key_trait`, validate general values with `value_trait`, and validate named keys with `per_key_traits`.

`Union(trait_types, **kwargs)` must accept a value accepted by one of its member trait types and must raise `TraitError` only when all member traits reject the value. `Any` must accept any value except that `allow_none=False` still rejects `None` when a non-`None` default policy applies. `Callable` must accept callable values and must reject non-callable values with `TraitError`. `CRegExp` must accept or compile regular expression values and must raise `TraitError` for invalid regular expressions.

`TraitType.from_string(s)` returns a Python value parsed from a command-line string. Scalar traits must parse their own strings. `List.from_string_list(values)` and `Dict.from_string_list(values)` must parse repeated command-line occurrences; list items must be passed through item parsing, and dict items must use `key=value` strings. Invalid command-line strings must raise `TraitError` or `ArgumentError` through the config loader.

### Defaults, Observers, and Validators

`@default(name)` registers a method that returns the dynamic default for one trait. The method must be called only when the trait value is first needed and no value was supplied earlier. A constructor keyword value must override the dynamic default and must not call the default method for that trait.

`@observe(*names, type="change")` registers a method as an observer. `HasTraits.observe(handler, names=All, type="change")` must register a runtime observer. When a trait changes to a different value, observers for that name and notification type must receive a `Bunch` change object containing `owner`, `name`, `old`, `new`, and `type`. The same values must be available by key and by attribute. Assigning the current value again must not emit a change notification. `unobserve(handler, names=All, type="change")` must remove a matching observer. `unobserve_all(name=All)` must remove registered observers for the selected name or all names.

`@validate(*names)` registers a method that receives a proposal object with at least `owner`, `trait`, `value`, and `name`. The validator's return value must become the stored trait value. A validator that raises `TraitError` must reject the assignment and must leave the old stored value unchanged. A validator that returns `None` must store `None` when the trait accepts `None` and must otherwise fail validation.

`hold_trait_notifications()` returns a context manager. Inside the context, change notifications and cross-validation must be delayed. When the context exits successfully, delayed changes must be validated and notified. When validation fails at exit, the object must roll back to the values it had before the context and must raise `TraitError`.

### Introspection and Mutation

`HasTraits.has_trait(name)` returns `True` when the instance has a trait named `name`; otherwise it returns `False`. `trait_has_value(name)` returns whether a value is already stored for a trait without forcing dynamic default generation. `trait_names(**metadata)` returns a list of trait names filtered by metadata. `traits(**metadata)` returns a dictionary mapping names to trait objects. Class-level methods `class_trait_names`, `class_traits`, and `class_own_traits` must return the corresponding class-level views.

`trait_values()` returns current trait values and must force defaults for traits that need values. `trait_defaults(*names)` returns default values for the requested traits. `add_traits(**traits)` must add trait descriptors to an instance at runtime, initialize them for that instance, and make them visible through introspection. `set_trait(name, value)` must assign through the same validation and notification path as attribute assignment and must raise `TraitError` or `AttributeError` for an unknown trait.

### Linking

`link(source, target, transform=None)` must keep two trait attributes synchronized in both directions. `source` and `target` are `(object, trait_name)` pairs. When either side changes, the other side must be assigned the transformed value. When `transform` is provided, it must contain a forward and reverse transform. Invalid endpoint tuples or unknown trait names must raise `TypeError`, `ValueError`, or `TraitError` before linking.

`directional_link(source, target, transform=None)` and `dlink` must synchronize only from source to target. `unlink()` must detach the observers created by a link. After `unlink()`, later source or target changes must no longer propagate through that link.

### Utility Objects

`Bunch` must behave like a dictionary whose keys are also available as attributes. Setting or deleting an attribute must affect the same value visible through item access. Missing attributes must raise `AttributeError`; missing keys must raise `KeyError`.

`import_item(name)` returns the object named by a dotted import string. It must import a module when `name` contains only a module path, and it must return an attribute when the final component names an object inside an imported module. It must raise `ImportError` when the module or item does not exist.

`signature_has_traits(cls)` returns the same class with a constructor signature that includes keyword-only parameters for trait names and their defaults. It must preserve the explicit parameters of the original `__init__`. It must raise the same errors as normal class construction when an invalid trait keyword or invalid trait value is passed.

## Product State Model

Traitlets exposes state through four public projections:

- Trait attribute projection: normal Python attribute access on `HasTraits` and `Configurable` instances.
- Descriptor and metadata projection: `TraitType` objects, class trait dictionaries, metadata tags, and default values.
- Event projection: observer, validator, link, and held-notification behavior.
- Configuration projection: `Config` dictionaries, config files, command-line arguments, and `Application.config`.

A value written through any public assignment path must pass the trait descriptor before it becomes visible in the attribute projection. A value rejected by validation must not become visible in any projection.

## Configuration Objects

`Config` must behave as a dictionary with attribute access. Accessing an uppercase missing attribute such as `cfg.Section` must create and return a nested `Config` section. Accessing a lowercase missing attribute must raise `AttributeError`. `cfg.Section.name = value` and `cfg["Section"]["name"] = value` must refer to the same stored value.

`Config.merge(other)` must merge another config into the receiver. Values from `other` must override conflicting existing scalar values. Nested sections must merge recursively so non-conflicting keys are preserved. `collisions(other)` returns a dictionary describing keys where both configs define different values; it returns an empty dictionary when there are no conflicts.

`LazyConfigValue` must record container updates such as `append`, `extend`, `prepend`, `insert`, `update`, and `add`. When merged into an existing value, list operations must produce the corresponding list order, dict updates must update mappings, and set additions must update sets. Invalid lazy operations for the target type must raise an exception instead of silently discarding the operation.

## Configurable Classes

`Configurable(**kwargs)` is a `HasTraits` subclass with a `config` trait. A trait tagged with `config=True` must be loadable from a `Config` section named for the class. A config section for a base class must apply to subclasses. A subclass-specific section must override an inherited base-class config value for the same trait. Constructor keyword values must override values loaded from `config`.

When a config contains a key for a known configurable trait, constructing or updating a `Configurable` must assign that value through normal trait validation. Invalid config values must raise `TraitError`. Config keys for traits that are not tagged `config=True` must not silently configure those traits; they must be ignored with a warning or rejected according to the same error policy used by the configurable object.

`update_config(config)` must merge the new config into the instance config and must update currently configurable trait values. `section_names()` returns the config section names considered for the class, including inherited configurable class names. `class_get_help`, `class_print_help`, `class_config_section`, and `class_config_rst_doc` return or print human-readable documentation for configurable traits; they must raise normal trait or formatting errors for invalid class state.

`LoggingConfigurable` must provide a `.log` trait containing a logger. Passing a non-logger value for `.log` must raise `TraitError`.

`SingletonConfigurable.instance(*args, **kwargs)` returns the canonical instance for the singleton class. The first call must create it. Later calls with no arguments must return the same instance. Later calls with arguments after an instance already exists must raise `MultipleInstanceError`. `clear_instance()` must clear the canonical instance for that singleton class hierarchy. `initialized()` returns whether an instance currently exists.

## Application, Config Files, and CLI

`Application` is a `SingletonConfigurable`. `Application.initialize(argv=None)` must parse command-line arguments, initialize subcommands when present, and populate `cli_config`, `config`, and `extra_args`. `Application.launch_instance(argv=None, **kwargs)` must create or reuse the singleton, initialize it, and start it.

`Application.load_config_file(filename, path=None)` must load Python and JSON config files matching the requested base name from the search path. When both same-base Python and JSON files are present in the same directory, the JSON config values must override conflicting Python config values. When the same base name is found in multiple search directories, files from earlier directories in `path` must have higher priority than later directories. Command-line config already parsed into `cli_config` must override conflicting values read from config files.

Python config files must execute with `get_config()` returning the active `Config` object as `c`. `load_subconfig(name)` inside a Python config file must load another Python config using the parent config file search path, and values assigned after `load_subconfig` must override conflicting values from the loaded subconfig.

`Application.loaded_config_files` returns the loaded config file paths in the order they were loaded. `Application.load_config_environ()` must read supported environment variables and update application config accordingly. When a config file raises an error, the default behavior must log a warning and ignore that file; when `raise_config_file_errors=True`, the application must raise or exit on the file loading error.

The command-line form `--Class.trait=value` and the separated form `--Class.trait value` must set configurable traits. Aliases in `Application.aliases` must map shorter option names to `Class.trait`; flags in `Application.flags` must set one or more config values without consuming a value. `boolean_flag(name, configurable, set_help="", unset_help="")` returns paired flag definitions for enabling and disabling a boolean config value.

Repeated scalar command-line options for the same trait must raise an initialization error. Repeated `List` options must accumulate values in order. Repeated `Dict` options must accept `key=value` items and merge them into a dictionary. Invalid option names, invalid values, or invalid repeated scalar usage must raise `ArgumentError`, `TraitError`, or terminate application initialization with a nonzero `SystemExit`.

`Application.subcommands` maps subcommand names to an application class, import string, or factory plus a help string. When the first positional argument names a subcommand, the parent application must instantiate the sub-application, store it on `subapp`, and initialize it with the remaining arguments. Unknown subcommands must remain normal extra arguments or raise the same command-line error used for unrecognized options, according to the parser path used by the application.

When `show_config` or `show_config_json` is true, `Application.start()` must print the current configuration in text or JSON form and must not run subclass-specific application work after showing the config. `print_help`, `emit_help`, `print_version`, and related help methods must expose aliases, flags, subcommands, and configurable options for the classes known to the application.

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

## Non-Goals

- Exact wording, spacing, and ordering of help text, warning text, logging output, generated RST, and generated config comments are outside this specification.
- Private modules, private helper functions, compatibility shims, and tests-only utilities are outside this specification.
- Static typing checker behavior is outside this specification except for runtime importability and runtime signatures described above.
- Optional shell completion integration with `argcomplete` is outside this specification except that configured aliases, flags, and configurable traits must remain discoverable by the public application metadata APIs.
- Deprecated magic observer method names and deprecated top-level `Sentinel` construction are outside this specification.
- Binary compatibility with older traitlets releases is outside this specification.

## Evaluation Notes

A complete implementation should be checked through the public imports and runtime behaviors described in this specification. Compatibility should be assessed across trait declaration, assignment validation, dynamic defaults, metadata introspection, observers, validators, held notifications, links, config object views, configurable inheritance, singleton lifecycle, config file loading, command-line parsing, and application workflows.

Formatting-only differences in help text, warnings, logging text, generated documentation, or generated config comments are not part of this contract unless they change a runtime behavior described above. Private helpers, deprecated compatibility shims, and static type checker behavior are outside the compatibility surface.
