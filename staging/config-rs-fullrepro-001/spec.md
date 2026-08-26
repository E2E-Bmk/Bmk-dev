<!--
INTERNAL HEADER (stripped from candidate-visible copy)
task_id: config-rs-fullrepro-001
repo: rust-cli/config-rs @ 532ab4d827db199c1b0e9e457441fcc82b819fb9 (v0.15.11)
sources: docs.rs/config rustdoc (builder, Environment, File, Value, errors);
  README; examples/; behavior of edge cases confirmed by executing the pinned
  reference (532ab4d, tag v0.15.11)
-->

# Layered Configuration Engine Specification

This document specifies a Rust library crate named `config` that assembles an
application configuration from ordered layers — programmatic defaults, parsed
configuration texts, environment-style key/value sources, and programmatic
overrides — into one merged, hierarchical table, and serves that table back
through typed lookups and serde deserialization.

## Product Overview

The crate is a layered configuration system. A builder collects three
categories of input: defaults (set one key at a time), sources (objects that
produce a whole key/value tree at once, such as a parsed TOML/JSON/INI text,
an environment-variable snapshot, or another already-built configuration),
and overrides (set one key at a time). Building the configuration folds the
layers into a single hierarchical table: defaults first, then every source in
the order added, then overrides, with later layers winning on conflicts and
nested tables merging key-wise rather than being replaced wholesale.

The merged table is then read through two families of projections. Path-based
lookups (`get` and the typed convenience forms) address any value by a dotted
path with array subscripts and coerce scalars between kinds by a fixed
coercion table. Whole-configuration deserialization turns the entire table
into any `serde::Deserialize` target, applying the same coercions when a
concrete primitive type is requested and presenting values as their stored
kinds when the target is self-describing. All projections observe the same
merged facts: a value set by any layer must be visible, with identical
coercion behavior, through every read path.

## Non-Goals

- This specification does not require the YAML, RON, JSON5, or Corn file
  formats, nor the `preserve_order`, `convert-case`, or `async` cargo
  features; only the `toml`, `json`, and `ini` format features are in scope.
- This specification does not require loading configuration from files on
  disk, file-extension format detection, required/optional file handling, or
  directory search; configuration text enters through `File::from_str` only.
- This specification does not require asynchronous sources, file watching, or
  any network access.
- This specification does not require exact error-message text, `Display`
  formatting of error values, or `Debug` output of any public type; errors
  are asserted through their `ConfigError` variant kinds and carried keys.
- This specification does not require 128-bit integer conversion methods or
  the deprecated mutation API of an already-built configuration.
- This specification does not require integration with the `log` crate or
  date/time types; scalar leaves are booleans, integers, floats, and strings.
- There is no command-line interface in this deliverable; programmatic use is
  through the Rust library API only.

## Representative Workflows

### Workflow 1: Layered build with typed lookups

An application declares defaults, loads a configuration text, and applies an
override; each layer is visible through path lookups unless a later layer
shadows it.

```rust
use config::{Config, File, FileFormat};

let config = Config::builder()
    .set_default("server.port", 8080)?
    .set_default("server.host", "localhost")?
    .add_source(File::from_str(
        "[server]\nport = 9090\n", FileFormat::Toml))
    .set_override("server.debug", true)?
    .build()?;

assert_eq!(config.get::<i64>("server.port")?, 9090);   // source beats default
assert_eq!(config.get::<String>("server.host")?, "localhost"); // default survives
assert_eq!(config.get::<bool>("server.debug")?, true); // override
```

### Workflow 2: Environment-shaped source into a typed struct

A key/value snapshot is normalized (prefix stripped, separator translated to
nesting, values parsed) and the merged result deserializes into a struct.

```rust
use config::{Config, Environment, Map};
use serde::Deserialize;

#[derive(Deserialize)]
struct Settings { redis: Redis }
#[derive(Deserialize)]
struct Redis { port: u16 }

let mut vars = Map::new();
vars.insert("APP_REDIS_PORT".to_owned(), "6379".to_owned());

let settings: Settings = Config::builder()
    .add_source(
        Environment::with_prefix("APP")
            .separator("_")
            .try_parsing(true)
            .source(Some(vars)),
    )
    .build()?
    .try_deserialize()?;
assert_eq!(settings.redis.port, 6379);
```

### Workflow 3: The same document through two formats

The same logical document expressed in two syntaxes must produce identical
typed views once merged.

```rust
use config::{Config, File, FileFormat};

let from_toml = Config::builder()
    .add_source(File::from_str("debug = true\n", FileFormat::Toml))
    .build()?;
let from_json = Config::builder()
    .add_source(File::from_str(r#"{ "debug": true }"#, FileFormat::Json))
    .build()?;
assert_eq!(from_toml.get::<bool>("debug")?, from_json.get::<bool>("debug")?);
```

## Building a Configuration

This section defines the builder, the three layer categories, and the merge
that produces the final table.

**Builder construction.** `Config::builder` returns a `ConfigBuilder` in its
default state. The builder is a value type: layer-adding methods consume and
return it (`add_source`) or return it inside a `Result` (`set_default`,
`set_override`, `set_override_option`), so calls chain.

**Defaults and overrides.** `set_default(key, value)` records a default for
one path-expression key; `set_override(key, value)` records an override for
one key; `set_override_option(key, maybe_value)` records an override only
when the option holds a value. All three accept any value convertible into a
`Value` (booleans, signed and unsigned integers, floats, string types,
sequences, maps, and any user type with a `ValueKind` conversion) and return
an error only when the key fails to parse as a path expression.

**Sources.** `add_source(source)` appends an object implementing the `Source`
trait to the ordered source list. In-scope sources are `File::from_str`
string documents, `Environment` snapshots, and an already-built `Config`
(a `Config` is itself a `Source` that contributes its whole merged table).
A source is not read at registration time.

**Building.** `build` consumes the builder, reads every registered source,
and produces a `Config`; `build_cloned` does the same from a borrowed builder
by cloning, leaving the builder reusable for further layering. Errors raised
while reading a source (for example a parse failure) surface from the build
call. Two configurations built from independent builders share nothing:
a key present in one is absent from the other.

**Precedence and merge.** The merged table starts empty. Defaults apply
first, then each source's collected tree in registration order, then
overrides. Applying one key/value pair follows the path-expression write
rule (see Path Grammar); applying a whole tree merges recursively:

- When the incoming value and the present value are both tables, the
  incoming table's entries are applied key-wise into the present table, so
  sibling keys set by earlier layers survive.
- Any other incoming kind (scalar, array, or null) replaces the present
  value entirely; arrays are not element-merged.
- An empty incoming table merged over a populated table leaves the populated
  table unchanged, and a null merged under a later table is replaced by it.

A later layer therefore shadows exactly the leaves it names (or the subtrees
it replaces with non-table values), never an unrelated sibling.

## Sources and Formats

This section defines the string-document source.

**`File::from_str`.** `File::from_str(text, format)` wraps a configuration
text with an explicit `FileFormat`; the in-scope format variants are
`FileFormat::Toml`, `FileFormat::Json`, and `FileFormat::Ini`. Parsing occurs
during `build`. The parsed root must be a table; a syntactically valid
document whose root is not a table (for example a bare JSON scalar) must
produce an error naming the root-shape problem, and a syntax error must
surface as `ConfigError::FileParse` carrying the parser's cause.

**Kind mapping.** TOML documents produce typed leaves: TOML booleans,
integers, and floats arrive as boolean, integer, and float kinds; TOML arrays
and tables (including arrays of tables) arrive as arrays and tables. JSON
documents map numbers to integer or float kinds, `null` to the null kind, and
objects/arrays to tables/arrays. INI documents produce string leaves only:
every value in an INI document arrives as a string, top-level properties
become top-level keys, and each `[section]` becomes a nested table; typing is
recovered later through the coercion table at read time.

**Case preservation.** Keys arriving from string documents are stored
verbatim, preserving case: a document key `FooBar` is addressed as `FooBar`,
and a lookup of `foobar` does not find it.

## The Environment Source

This section defines the key/value-snapshot source and its normalization
pipeline.

**Construction and snapshot injection.** `Environment::default()` builds a
source over the process environment; `Environment::with_prefix(p)` (or the
equivalent builder method `prefix(p)`) additionally sets a prefix filter. The
`source(Some(map))` method replaces the process environment with an explicit
`Map<String, String>` snapshot, so behavior is observable without touching
process state; `source(None)` restores reading the process environment. All
configuration methods consume and return the source, so calls chain.

**Normalization pipeline.** Collecting the source (directly through
`Source::collect`, or implicitly during `build`) processes each key/value
pair as follows, in order:

1. Keys that are not valid Unicode are skipped silently.
2. When `ignore_empty(true)` is set, pairs whose value is the empty string
   are dropped.
3. The key is lowercased.
4. When a prefix is configured, the pattern `prefix + prefix_separator`
   (lowercased) must lead the key; keys without the pattern are skipped
   entirely. Unless `keep_prefix(true)` is set, the matched pattern is
   stripped from the key. The prefix comparison is case-insensitive because
   of step 3: prefixes `a`, `aB`, and `ab` all match a key beginning `AB_`.
   `prefix_separator` defaults to the level separator when one is set and to
   `_` otherwise.
5. When a level separator is configured through `separator(s)`, every
   occurrence of `s` in the remaining key is replaced by `.`, so the pair
   lands at a nested path; with no separator the whole remaining key is one
   top-level key (an underscore inside it stays an underscore).
6. The value is converted:
   - Without `try_parsing(true)`: the value stays a string.
   - With `try_parsing(true)`: the value becomes a boolean when its
     lowercased form is exactly `true` or `false`; otherwise an integer when
     it parses as one; otherwise a float when it parses as one; otherwise,
     when `list_separator(sep)` is configured, the value is split on `sep`
     into an array of strings — but when `with_list_parse_key(key)` has
     registered one or more keys, only pairs whose normalized key is in that
     list are split and all others stay whole strings; otherwise the value
     stays a string. The list-parse key comparison is exact against the
     normalized (lowercased) key.

A value that is not valid Unicode must produce an error at collect time
(`ConfigError::Message` kind) rather than being skipped, because the caller
did not restrict which keys matter.

## Path Grammar and Key Expansion

This section defines the path expressions used by lookups, defaults, and
overrides.

**Grammar.** A path expression is an identifier root followed by any number
of postfixes. An identifier is one or more ASCII letters, digits, `_` or `-`
characters. A postfix is either `.` followed by an identifier (table key
access) or a bracketed subscript `[n]` where `n` is an optionally negative
integer (array element access). Anything else fails to parse: `set_default`
and `set_override` report the parse failure as `ConfigError::PathParse` when
the key is malformed, and `get` on an unparsable key reports the key as not
found. Path identifiers are matched case-sensitively against stored keys.

**Read resolution.** On lookup, each `.key` step requires the current value
to be a table containing the key, and each `[n]` step requires the current
value to be an array. A non-negative subscript addresses from the front; a
negative subscript `-k` addresses `len - k` from the back (so `[-1]` is the
last element). A missing key, a step through the wrong kind, an
out-of-bounds subscript (in either direction), or a negative subscript whose
magnitude exceeds the length resolves to "not found", and `get` returns
`ConfigError::NotFound` carrying the requested key string.

**Write expansion.** `set_default` and `set_override` interpret their key
with the same grammar and create intermediate structure as needed
(auto-vivification): traversing `.key` through a non-table replaces it with
a table; traversing `[n]` through a non-array replaces it with an array. A
non-negative subscript beyond the current length grows the array with null
placeholders up to that index. A negative subscript resolves from the back
when the array is long enough; when it is not (including on an empty array),
the array is padded at the front with null placeholders and the write lands
at index 0 — so writing `[-1]` then `[-2]` into an empty array produces a
two-element array with the `[-2]` value first.

## Typed Access and Coercions

This section defines the read projections of one merged table.

**Generic lookup.** `get::<T>(key)` resolves the path and deserializes the
found value into any `T: Deserialize`. Primitive targets apply the coercion
table below; struct, map, sequence, and enum targets recurse per field or
element. Convenience forms fix the target: `get_string`, `get_int` (64-bit
signed), `get_float`, `get_bool`, `get_table` (map of `Value`), `get_array`
(vector of `Value`). The same coercions govern `Value`'s own conversion
methods `into_bool`, `into_int`, `into_float`, `into_string`, `into_table`,
`into_array`.

**Coercion table.** Requested kind × stored kind:

| requested | from boolean | from integer | from float | from string |
|---|---|---|---|---|
| boolean | itself | `!= 0` | `!= 0.0` | `1`/`true`/`on`/`yes` → true; `0`/`false`/`off`/`no` → false (case-insensitive); otherwise a type error |
| integer | 1/0 | itself | rounded to nearest | `true`/`on`/`yes` → 1; `false`/`off`/`no` → 0 (case-insensitive); otherwise parsed as an integer; unparsable → type error |
| float | 1.0/0.0 | exact | itself | `true`/`on`/`yes` → 1.0; `false`/`off`/`no` → 0.0 (case-insensitive); otherwise parsed as a float; unparsable → type error |
| string | `"true"`/`"false"` | decimal digits | decimal representation | itself |

Null, table, and array kinds never coerce to a scalar: requesting a scalar
from them is a type error, as is requesting a table or array from any
scalar. Unsigned integer targets additionally range-check: a stored integer
that fits the requested width deserializes (66000 into `u32`), one that does
not (66000 into `u16`, or any negative value into an unsigned target) is a
type error. All type errors are `ConfigError::Type`; when the failure occurs
while resolving a keyed lookup or deserializing a named field, the error
carries the offending key.

**Value and ValueKind.** A `Value` pairs an origin description with a
`ValueKind`; the kind enum has variants `Boolean`, `I64`, `U64`, `I128`,
`U128`, `Float`, `String`, `Table`, `Array`, and `Nil`. `Value` implements
`From` for the scalar primitives, strings, sequences, and maps, and any type
with a `ValueKind` conversion is accepted by `set_default`/`set_override`.
`Map<K, V>` is the crate's table type, with the standard-library hash-map
API (`new`, `insert`, `len`, indexing, iteration; iteration order is not
specified).

## Whole-Configuration Deserialization

This section defines the serde projection of the merged table.

**`try_deserialize`.** `Config::try_deserialize::<T>()` consumes the
configuration and deserializes the whole merged table into `T`. Struct
fields whose declared type is a primitive apply the coercion table (a
boolean leaf deserializes into an `f64` field as 1.0; a boolean leaf
deserializes into an `Option<String>` field as `"false"`); fields declared
as maps or sequences require the stored kind to match. Field names are
matched exactly as stored, so mixed-case field names and
`#[serde(rename = "...")]` attributes work verbatim, including names
containing `:`, `/`, or `\` characters. Enum targets and other
self-describing targets are driven by the stored kind itself: a string leaf
arrives at the visitor as a string (so an externally tagged or adjacently
shaped enum deserializes from the natural table/string shapes, and a string
`"42"` does not satisfy an `i64` field of a self-describing target — that is
a type error reported through the serde error path).

**Empty and defaulted targets.** `Config::default()` is an empty
configuration: deserializing it into a struct whose fields are all skipped
or defaulted succeeds with the default values, and looking up any key in it
is a not-found error.

**`try_from`.** `Config::try_from(&value)` serializes any `T: Serialize`
into a configuration whose table mirrors the value's fields; round-tripping
a struct through `try_from` then `try_deserialize` reproduces the struct.
`set_default`/`set_override` accept a custom struct directly when the struct
provides a `ValueKind` conversion, and the stored table then deserializes
back into the struct.

**Cloning.** `Config` implements `Clone`; a clone deserializes and resolves
identically to the original and independently of it.

## State Model

The single fact source is the merged hierarchical table (a table-kinded
`Value`) held by a built `Config`. Its public projections are:

1. path lookups (`get` and the typed forms) with coercions;
2. whole-table deserialization (`try_deserialize`);
3. re-contribution as a layer: a built `Config` added to another builder via
   `add_source` contributes its entire table under the merge rules;
4. source-level observation: `Source::collect` on an `Environment` (or any
   source) exposes the normalized flat map that the build merge consumes.

A builder is reusable through `build_cloned` without consuming registered
layers; `build` consumes the builder. Nothing about a built configuration
changes after `build` in the in-scope API.

## Error Semantics

All fallible operations return `Result<_, ConfigError>`. In-scope variant
kinds and when they must arise:

| Condition | `ConfigError` kind |
|---|---|
| Lookup of an absent key, out-of-bounds subscript, or step through the wrong kind | `NotFound` (carries the requested key string) |
| Malformed path expression in `set_default`/`set_override` | `PathParse` |
| Syntax error while parsing a string document | `FileParse` (carries the parser's cause; the URI is absent for string documents) |
| Value not convertible to the requested kind, wrong stored kind for a field, or unsigned range violation | `Type` (carries the offending key when one is known, the unexpected kind, and the expected description) |
| Non-Unicode value in an environment snapshot | `Message` |
| Error raised inside a foreign serializer/deserializer | `Foreign` |
| Type error annotated with the path at which it occurred | `At` (wraps another error with origin and key) |

`ConfigError::Frozen` exists in the taxonomy for the out-of-scope mutation
API and is not raised by any in-scope operation. Exact rendered messages are
not part of this contract; tests assert kinds and carried keys.

## Cross-View Invariants

1. A value contributed by any layer (default, string document, environment
   snapshot, override) must be readable with the same result through
   `get::<T>`, the typed `get_*` form of the matching kind, and a
   deserialized struct field of that type.
2. Layer precedence must be total and stable: for any key set by multiple
   layers, the visible value comes from the latest layer in
   defaults → sources (in order) → overrides, through every read projection.
3. The same logical document expressed as TOML, as JSON, and (for
   string-leafed content) as INI must produce configurations whose typed
   lookups agree pairwise on every shared path.
4. A built `Config` re-added as a source must reproduce every one of its
   keys in the receiving configuration, subject to the same precedence rules
   as any other source.
5. The flat map visible through `Source::collect` on an `Environment` must
   equal what a build using that source merges: every collected key resolves
   through `get` on the built configuration, with the same parsed kind.
6. Coercions must agree across access forms: `get_string` on a boolean leaf,
   `get::<String>` on it, and a `String`-typed field deserialized from it
   must all produce the same text.
7. `Config::try_from(&s)` followed by `try_deserialize` must reproduce `s`
   for any in-scope serializable struct.

## Public Interface

### Import Surface

Test and application code uses these imports (all from the crate root):

```rust
use config::{
    Config, ConfigBuilder, ConfigError,
    Environment, File, FileFormat, FileSourceString,
    Map, Source, Value, ValueKind,
};
```

The glob import `use config::*;` must provide all names above.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Config` | struct | Built configuration: merged table plus read projections |
| `Config::builder` | fn | Start a `ConfigBuilder` |
| `Config::default` | fn | Empty configuration |
| `Config::try_from` | fn | Serialize a value into a configuration |
| `get` / `get_string` / `get_int` / `get_float` / `get_bool` / `get_table` / `get_array` | methods | Path lookups with coercion |
| `try_deserialize` | method | Whole-table serde deserialization |
| `ConfigBuilder` | struct | Ordered layer collector |
| `set_default` / `set_override` / `set_override_option` | methods | Single-key layers (path-expression keys) |
| `add_source` | method | Append a `Source` layer |
| `build` / `build_cloned` | methods | Fold layers into a `Config` |
| `File` | struct | Document source; `File::from_str(text, format)` in scope |
| `FileFormat` | enum | `Toml`, `Json`, `Ini` in scope |
| `FileSourceString` | struct | Source-type parameter of a string-backed `File` |
| `Environment` | struct | Key/value snapshot source with normalization pipeline |
| `Environment::default` / `with_prefix` | fns | Construction |
| `prefix` / `prefix_separator` / `separator` / `list_separator` / `with_list_parse_key` / `try_parsing` / `ignore_empty` / `keep_prefix` / `source` | methods | Pipeline configuration |
| `Source` | trait | Layer contract; `collect` yields the flat map |
| `Value` | struct | Origin-tagged configuration value |
| `into_bool` / `into_int` / `into_float` / `into_string` / `into_table` / `into_array` | methods | Kind coercions |
| `ValueKind` | enum | `Boolean`, `I64`, `U64`, `I128`, `U128`, `Float`, `String`, `Table`, `Array`, `Nil` |
| `Map` | type alias | Table type with hash-map API |
| `ConfigError` | enum | Error taxonomy (see Error Semantics) |

### CLI Entry Points

There is no console entry point in this deliverable.

## Appendix A: Environment

- Language: Rust, edition 2018-compatible (toolchain 1.83; the crate's
  declared minimum supported Rust version must not exceed it).
- The crate must build as `config` with cargo features `toml`, `json`, and
  `ini` available; the assessment suite depends on the crate as
  `config = { version = "*", default-features = false, features = ["toml", "json", "ini"] }`.
- Format parsing may use third-party parser crates (TOML, JSON, INI parsers
  and serde integrations); the layering, path, coercion, environment, and
  deserialization engines are the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process. Test
  code depends on `serde` with the `derive` feature.
- No network access at test time.

## Appendix B: Assessment Notes

Assessment exercises layer precedence and deep-merge behavior, string
document parsing for three formats, environment-snapshot normalization
(prefix, separators, case handling, empty-value handling, value parsing and
list splitting), path-expression reads and auto-vivifying writes including
negative subscripts, the scalar coercion table across all read projections,
whole-table deserialization into structs, maps, sequences and enums, and the
`ConfigError` kind taxonomy. Tests assert produced values, deserialized
structs, and error kinds with carried keys; they do not assert rendered
error text, `Debug` output, or private structure. Behavior is asserted
through the public API in all cases.
