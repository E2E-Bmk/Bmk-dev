<!-- INTERNAL
task_id: avsc-avro-type-engine-fullrepro-001
spec_version: v1
delta: initial draft
source_boundary: avsc@5.7.9 npm package (executed via probes, wip/probe/avsc a1-a4), github.com/mtth/avsc wiki API reference and README, Apache Avro specification (binary encoding, schema resolution, IDL); every asserted behavior observed by executing the pinned release
-->

# avsc Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`avsc` is an Avro data-serialization library built around compiled type objects. A JSON schema — a primitive name, a record/enum/fixed/array/map definition, or a union — compiles through `Type.forSchema` into a `Type` instance: a self-contained codec that validates values, encodes them to compact binary buffers and JSON strings, decodes both formats back, infers schemas from sample values, and resolves data written under one schema into the shape expected by another (schema evolution).

All types built from one schema document share a name registry, so named types (records, enums, fixeds) can reference each other — including recursively — and the same graph powers every projection: validation, the binary codec, the JSON codec, canonical schema output, fingerprinting, equality, and resolver construction. A small IDL front end (`readSchema`, `readProtocol`) parses Avro IDL text into the same JSON schema shapes that `Type.forSchema` consumes.

The installable package name is `avsc`. All functionality is reachable through the package's main entry point.

## Non-Goals

- This specification does not require RPC services, message protocols, clients, or servers.
- This specification does not require Avro container files, block encoders/decoders, or any streaming or file-system interface.
- This specification does not require IDL `import` statement resolution or reading IDL from files; IDL input is provided as strings.
- This specification does not require deprecated aliases of the current API.
- This specification does not require 64-bit long support beyond JavaScript's exactly-representable integer range, nor pluggable long implementations.
- This specification does not define browser-specific behavior.

## Representative Workflows

**Compile a schema, validate, and round-trip binary data.** A record schema compiles to a type whose codec is byte-exact:

```ts
import { Type } from 'avsc';

const type = Type.forSchema({
  type: 'record',
  name: 'Person',
  fields: [
    { name: 'name', type: 'string' },
    { name: 'age', type: 'int', default: 25 },
  ],
});

type.isValid({ name: 'Ann', age: 30 });    // true
const buf = type.toBuffer({ name: 'Ann', age: 30 });
type.fromBuffer(buf);                      // Person { name: 'Ann', age: 30 }
```

**Evolve data across schema versions.** A resolver reads data written by an older schema into a newer one, applying promotions and defaults:

```ts
const writer = Type.forSchema({
  type: 'record', name: 'P',
  fields: [{ name: 'a', type: 'int' }],
});
const reader = Type.forSchema({
  type: 'record', name: 'P',
  fields: [
    { name: 'a', type: 'long' },
    { name: 'b', type: 'string', default: 'hey' },
  ],
});
const resolver = reader.createResolver(writer);
reader.fromBuffer(writer.toBuffer({ a: 5 }), resolver); // { a: 5, b: 'hey' }
```

## Type Construction And Names

`Type.forSchema(schema, opts)` compiles a JSON schema into a `Type`; every construction rule below is enforced at compile time.

**Primitives.** The eight primitive names — `"null"`, `"boolean"`, `"int"`, `"long"`, `"float"`, `"double"`, `"bytes"`, `"string"` — each compile to a type whose `typeName` equals the primitive name. A type is recognized by `Type.isType(value)`; `Type.isType(value, ...prefixes)` returns whether the value is a type whose `typeName` (or `branchName`) starts with at least one of the given prefixes.

**Records.** A record schema carries `type: "record"`, an optional `name`, and a `fields` array of `{ name, type }` objects with optional `default`, `order`, and `aliases`. The compiled type exposes `typeName` `"record"`, `name` (namespace-qualified), `fields` (each with `name`, `type`, `order`, `aliases`, and a `defaultValue()` method), a `field(name)` lookup, and a `recordConstructor` class named after the record whose instances the decoder produces; decoded records are instances of that class, and the constructor accepts field values in declaration order. A field default must be valid for the field's type; WHEN a field's schema declares a default, THEN `defaultValue()` returns it, and validation accepts objects that omit the field. If a declared default does not validate against the field type, then `forSchema` must raise an `Error`. A record schema with no `name` compiles with `name` undefined. WHERE `omitRecordMethods` is set on `forSchema`, THEN generated constructors carry no extra prototype methods.

**Enums, fixeds.** An enum schema declares `name` and `symbols`; the type exposes `symbols` and accepts exactly those strings. Symbols must be valid Avro identifiers; if a symbol contains invalid characters, then `forSchema` must raise an `Error`. A fixed schema declares `name` and `size`; the type exposes `size` and accepts only buffers of exactly that length.

**Arrays and maps.** An array schema declares `items`; a map schema declares `values`. Their types validate homogeneous JavaScript arrays and plain string-keyed objects respectively.

**Unions.** A JSON array of schemas compiles to a union. Union branches must be distinct — if two branches carry the same branch name, then `forSchema` must raise an `Error` — and unions must not directly contain unions (raising an `Error` otherwise). The `wrapUnions` option selects the representation: with `false`, the type's `typeName` is `"union:unwrapped"` and values are the branch values themselves; with `true`, the `typeName` is `"union:wrapped"` and non-null values are single-key objects keyed by branch name (`{ int: 1 }`); `null` is represented as `null` in both modes. The default mode (also selectable as `"auto"`) compiles unions as unwrapped except WHEN branch values would be indistinguishable to the decoder among multiple number-like branches (for example `["int", "float"]`), THEN the union compiles wrapped. In unwrapped mode a wrapped object such as `{ int: 1 }` is invalid; in wrapped mode a bare branch value is invalid. Decoded wrapped values expose an `unwrap()` method returning the bare branch value.

**Names, namespaces, aliases.** Record, enum, and fixed names may be qualified with dots or combined with a `namespace` attribute; the compiled `name` is always fully qualified. A nested named type inherits the enclosing namespace unless its own name is dotted. The `namespace` option of `forSchema` supplies a default namespace for unqualified top-level names. Named types register themselves: a later schema may reference a previously defined name as a plain string. WHERE a `registry` object is passed to `forSchema`, THEN compiled named types are recorded in it under their fully qualified names and are reused by later `forSchema` calls sharing the registry — the referencing field resolves to the identical `Type` instance. If a schema references a name with no definition in scope, then `forSchema` must raise an `Error`. Recursive references (a record field referring to its own record, directly or through a union) compile and validate correctly.

**Logical types.** A schema whose object form carries a `logicalType` attribute compiles to a logical type WHEN the `logicalTypes` option maps that name to a subclass of `types.LogicalType`; the compiled type's `typeName` is `"logical:"` plus the logical name, and `underlyingType` exposes the compiled underlying type. Subclasses implement `_fromValue` (decode direction), `_toValue` (encode direction; returning undefined marks the value invalid), and optionally `_resolve` for evolution. Validation, both codecs, and resolvers then operate on the logical (wrapped) values. WHEN no matching entry exists in `logicalTypes`, THEN the attribute is ignored and the schema compiles to the plain underlying type.

## Value Validation And Algebra

Every type answers value-domain questions and derives new values without touching encoders.

**Validation.** `isValid(value, opts)` returns whether a value belongs to the type's domain, without throwing. Value domains are exact: `"int"` accepts integers in the signed 32-bit range (fractions and out-of-range values are invalid); `"long"` accepts integers with magnitude at most 2^53 − 2; `"float"` and `"double"` accept any JavaScript number — fractions, and non-finite values such as `Infinity` and `NaN`, included — while rejecting non-numbers; `"bytes"` and fixeds accept `Buffer` instances only (a plain `Uint8Array` or string is invalid); `"string"` accepts strings; `"null"` accepts only `null`; enums accept exactly their declared symbols; records accept objects whose declared fields all validate — fields with defaults may be omitted, and undeclared extra properties are ignored. WHERE `noUndeclaredFields` is set in the options, THEN records with extra properties are invalid. WHERE an `errorHook` function is supplied, THEN it is invoked once per mismatch with the path (an array of field names) and the offending value.

**Cloning.** `clone(value, opts)` returns a deep copy after validating; if the value is invalid, then `clone` must raise an `Error`. WHERE `coerceBuffers` is set, THEN JSON-shaped buffer objects (`{ type: "Buffer", data: [...] }`) are converted into buffers during the copy. WHERE `stripUndeclaredFields` is set, THEN properties absent from the record's field list are dropped rather than copied. Undeclared properties are dropped from the clone in every mode.

**Ordering.** `compare(a, b)` returns −1, 0, or 1 following the Avro order for the type; record fields participate in declaration order and a field's `order` attribute of `"descending"` inverts its contribution while `"ignore"` skips it. `compareBuffers(buf1, buf2)` orders encoded values identically to comparing the decoded values with `compare`.

**Generation.** `random()` returns a value that satisfies `isValid`. `wrap(value)` returns the value boxed in its branch shape.

## Binary Encoding

The binary codec is byte-exact Avro: every encoding decision below is observable through buffers.

**Round trip.** `toBuffer(value)` validates and encodes; if the value is invalid, then `toBuffer` must raise an `Error` identifying the offending value. `fromBuffer(buffer)` decodes a complete buffer; if the buffer ends before the value is complete, then `fromBuffer` must raise an `Error` (truncated buffer); if decoding finishes before the buffer's end, then `fromBuffer` must raise an `Error` (trailing data). For every valid value, `fromBuffer(toBuffer(v))` returns a value equal to `v` (decoded records are constructor instances equal field-by-field).

**Formats.** `int` and `long` use zigzag variable-length encoding: 1 encodes to `02`, −1 to `01`, 64 to `80 01`. `string` and `bytes` are length-prefixed with a zigzag varint (the two-character string `"hi"` encodes to `04 68 69`); strings are UTF-8. `float` is 4 bytes and `double` 8 bytes, little-endian IEEE 754. `boolean` is one byte; `null` encodes to zero bytes. Enums encode the symbol's declaration index as a zigzag varint. Fixeds copy exactly `size` bytes with no prefix. Arrays and maps encode as blocks: a zigzag count, that many items (map entries are key then value), then a zero terminator — `[1, 2]` under `array<int>` encodes to `04 02 04 00`. Unions encode the zigzag branch index followed by the branch encoding; `null` in a `["null", "int"]` union is the single byte `00`, and `1` is `02 02`. Records encode their fields in declaration order with no field markers.

**Precision.** Encoding a JavaScript number through `float` loses precision beyond 32-bit floats: the round trip returns the nearest single-precision value, not the original double.

## JSON Encoding And Schema Projection

Types serialize both their values and themselves.

**Value JSON.** `toString(value)` returns the Avro JSON encoding of a value: records become JSON objects, `bytes`/fixed values become strings of code points from the buffer's bytes, and union values (in every union mode) become `null` or a single-key object keyed by branch name — `toString(1)` on a `["null", "int"]` union returns `{"int":1}`. `fromString(text)` parses that representation back into a value (buffers restored, union branches unwrapped according to the type's mode).

**Schema JSON.** `schema(opts)` returns the type's schema as JSON-compatible data, with attributes canonicalized and non-canonical attributes (defaults, `logicalType`, orders, docs) omitted; WHERE `exportAttrs` is set, THEN defaults and logical-type attributes are included. WHERE `noDeref` is set, THEN a named type is returned as its name string. `toJSON()` equals `schema()`. Calling `toString()` with no argument returns the JSON text of the schema with named types dereferenced at most once — for a named type this is the JSON-quoted fully qualified name.

**Identity.** `fingerprint(algorithm)` returns a buffer digest of the canonical schema (16 bytes for the default algorithm); two independently compiled types with identical canonical schemas produce identical fingerprints. `equals(other)` returns whether two types have the same canonical schema — a record differing only in one field's type is not equal.

## Schema Evolution

`reader.createResolver(writer)` compiles the Avro resolution rules into a resolver that `fromBuffer` accepts as its second argument.

**Resolution rules.** A reader type resolves a writer type WHEN the Avro match rules hold: identical primitives; promotions `int` → `long` → `float` → `double` (each step also accepting all earlier types), `string` ↔ `bytes`; arrays and maps resolve WHEN their element types resolve; fixeds resolve WHEN name (or alias) and `size` match; enums resolve WHEN the names match and every writer symbol is known to the reader — WHERE the reader enum declares a `default` symbol, THEN unknown writer symbols decode to that default instead. Records match by name or through the reader's `aliases`; each writer field maps to the reader field with the same name or a name listed in the reader field's `aliases`; reader fields absent from the writer take their defaults. If a reader field has no default and no matching writer field, then `createResolver` must raise an `Error`. If no rule matches, then `createResolver` must raise an `Error` ("cannot read" the writer as the reader).

**Unions.** A reader union resolves a writer non-union by resolving any one branch, and decoding returns the value in the reader's representation. A reader non-union resolves a writer union only WHEN every writer branch resolves; a single unresolvable branch (such as `"null"` when reading into `"int"`) makes `createResolver` raise an `Error`.

**Effects.** Decoding with a resolver applies promotions (an `int`-written value reads as a `long`/`double` number), fills reader defaults, follows aliases, and reorders record fields to the reader's declaration order. A resolver is bound to the reader instance that created it: if a different type instance — even one compiled from the identical schema — passes it to `fromBuffer`, then `fromBuffer` must raise an `Error` ("invalid resolver").

## Type Inference

Types can be derived from values and combined.

**From values.** `Type.forValue(value)` infers a type: integer samples infer `"int"`, non-integer numbers infer `"float"`, strings `"string"`, booleans `"boolean"`, `null` `"null"`, buffers `"bytes"`, arrays an array type over the combined item type, and plain objects an anonymous record whose fields follow the object's properties.

**Combining.** `Type.forTypes(types)` returns a type accepting every input type's values: number types combine to the widest (`int` with `long` yields `"long"`), and incompatible types (such as `int` with `string`) combine into a union.

## IDL Parsing

The IDL front end turns Avro IDL text into the JSON schema shapes `Type.forSchema` accepts.

**Schemas.** `readSchema(text)` parses one IDL type declaration: `record Person { string name; int age = 25; }` yields the record schema JSON with the default attached; `union { null, string }` yields a two-branch array; `map<int>` and `array<string>` yield map and array schema objects. The output compiles through `Type.forSchema` without modification.

**Protocols.** `readProtocol(text)` parses a protocol declaration into an object with the `protocol` name, a `types` array of contained type schemas, and a `messages` object mapping each message name to its `request` parameter list and `response` schema. If the IDL text is malformed, then both functions must raise an `Error`.

## State Model

The core state is one compiled type graph per schema document:

- **Type graph** — `Type` instances (one per schema node) with named types registered under fully qualified names, unions holding branch arrays, records holding field lists with defaults and generated constructors, and logical types wrapping underlying types.

Public projections of that graph:

1. **Validation** — `isValid` with hooks and strictness options.
2. **Binary codec** — `toBuffer` / `fromBuffer`, byte-exact Avro encoding.
3. **JSON codec** — `toString(value)` / `fromString`.
4. **Schema output** — `schema()` / `toJSON()` / `toString()`, fingerprints, equality.
5. **Evolution** — `createResolver` + resolver-aware decoding.
6. **Inference** — `Type.forValue`, `Type.forTypes`.
7. **Value algebra** — `clone`, `compare`, `compareBuffers`, `random`, `wrap`, record constructors.
8. **IDL** — `readSchema` / `readProtocol` producing `forSchema`-ready shapes.

Every projection reads the same graph: what validates is exactly what encodes; what the schema output describes is exactly what the fingerprint digests; what the resolver promises is exactly what resolver-aware decoding performs.

## Error Semantics

| Condition | Outcome |
|---|---|
| Schema references an undefined type name | `forSchema` raises `Error` |
| Duplicate union branch names, or union directly containing a union | `forSchema` raises `Error` |
| Enum symbol not a valid identifier | `forSchema` raises `Error` |
| Record field default invalid for the field's type (including a union default not matching the first branch) | `forSchema` raises `Error` |
| `toBuffer` / `clone` / `toString(value)` on an invalid value | raises `Error` naming the invalid value |
| `fromBuffer` on a truncated buffer | raises `Error` |
| `fromBuffer` leaving trailing bytes | raises `Error` |
| `createResolver` with unresolvable schemas | raises `Error` |
| `fromBuffer` with a resolver created by a different type instance | raises `Error` |
| Malformed IDL text in `readSchema` / `readProtocol` | raises `Error` |
| `isValid` on any value | returns `false`, never throws |

Error message wording is not part of this contract; assertions rely on the throwing behavior and error class.

## Cross-View Invariants

1. Codec agreement: for every value accepted by `isValid`, `fromBuffer(toBuffer(v))` and `fromString(toString(v))` must return equal values, and for every rejected value `toBuffer`, `clone`, and `toString(value)` must raise.
2. Schema round trip: `Type.forSchema(t.schema())` must compile to a type for which `equals(t)` is true and whose `fingerprint()` equals `t.fingerprint()`.
3. Evolution consistency: WHEN `reader.createResolver(writer)` succeeds, THEN every buffer produced by `writer.toBuffer` from a writer-valid value must decode through the resolver into a reader-valid value, with promotions widening numbers and reader defaults filled.
4. Inference closure: `Type.forValue(v)` must produce a type for which `isValid(v)` is true, and `Type.forTypes` must produce a type accepting every value its inputs accept.
5. Ordering agreement: for any two valid values, `compareBuffers(toBuffer(a), toBuffer(b))` must equal `compare(a, b)`.
6. IDL agreement: `Type.forSchema(readSchema(text))` must behave identically to compiling the equivalent hand-written JSON schema — same validation domain, same encodings, same canonical schema.
7. Registry identity: WHEN two schemas compiled with a shared registry reference the same fully qualified name, THEN they must observe the identical `Type` instance, and its behavior is the same through either reference.

## Public Interface

### Import Surface

```ts
import { Type, types, readSchema, readProtocol } from 'avsc';
// types namespace: types.LogicalType, types.RecordType, types.EnumType,
// types.FixedType, types.ArrayType, types.MapType, plus primitive type classes.
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Type` | class | Compiled schema; statics `forSchema`, `forValue`, `forTypes`, `isType`; codec, validation, evolution, and schema-projection methods |
| `types` | namespace | Built-in type classes: `LogicalType` (subclass to add logical types), `RecordType` (`fields`, `field`, `recordConstructor`), `EnumType` (`symbols`), `FixedType` (`size`), `ArrayType` (`itemsType`), `MapType` (`valuesType`) |
| `readSchema` | function | Parse one IDL type declaration into schema JSON |
| `readProtocol` | function | Parse an IDL protocol declaration into a protocol object |

### CLI Entry Points

There is no console script for this package. Programmatic use is through TypeScript/JavaScript imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The test toolchain is `vitest` with TypeScript; tests import the package under test by its package name `avsc`. Node's built-in `Buffer` is available; no other third-party runtime packages are available or needed.

The project must declare its packaging metadata in a standard `package.json` at the project root, exposing the package's public entry point under the name `avsc`, so the test suite can resolve `import { Type } from 'avsc'`. TypeScript type declarations for the public surface must be included so the test suite type-checks.

## Appendix B: Assessment Notes

Assessment exercises the public surface described in this document across several dimensions: schema compilation for every category (primitives, records with defaults and constructors, enums, fixeds, arrays, maps, unions in each `wrapUnions` mode, named types with namespaces and registries, logical types) including construction-time errors; validation domains and hooks; byte-exact binary encoding and both decode error paths; JSON value encoding; schema output, fingerprints, and equality; schema evolution through resolvers covering promotions, defaults, aliases, enums, and union rules; type inference and combination; and IDL parsing. Tests are split into an atomic tier, each verifying a single behavior, and an integration tier composing several projections against shared type graphs. Expected values in tests were produced by executing this specification's reference behavior — matching the letter of this document is the only reliable strategy.
