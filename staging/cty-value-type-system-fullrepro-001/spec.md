# cty Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cty` is a dynamic type system for Go programs that manipulate configuration
values on behalf of end users. Every datum is a `cty.Value`: an immutable
pairing of a `cty.Type` with content that is either a concrete payload, the
distinguished null of that type, or an unknown placeholder that stands for a
value to be resolved later. Values also carry two optional annotations —
_marks_, which are caller-defined labels that propagate automatically through
operations, and _refinements_, which shrink the range of an unknown value so
that some operations on it produce known results anyway.

The same value model is projected through several cooperating surfaces that
must agree with each other: an operation API on `cty.Value` (equality,
arithmetic, comparison, indexing, attribute access, iteration), a type
inspection and conformance API on `cty.Type`, a conversion and type-unification
engine in the `convert` package, a type-aware JSON codec in the `json` package,
and a MessagePack codec in the `msgpack` package that additionally round-trips
unknown values and an approximation of their refinements. The installable
module path is `github.com/zclconf/go-cty`, and the four packages covered here
are `cty`, `cty/convert`, `cty/json`, and `cty/msgpack`.

Numbers are arbitrary-precision decimals backed by 512-bit binary floating
point, so integer arithmetic across the full `int64`/`uint64` range is exact
and decimal literals survive serialization round trips without drift. Strings
are sequences of Unicode codepoints normalized to NFC on construction. The
type system is structural: object and tuple types are equal exactly when their
attribute or element structures are equal, and collection types are equal when
their element types are equal.

## Non-Goals

- This specification does not require capsule types: `cty.Capsule`,
  `cty.CapsuleWithOps`, `cty.CapsuleVal`, `Value.EncapsulatedValue`, and the
  associated `Type` methods (`IsCapsuleType`, `EncapsulatedType`,
  `CapsuleOps`, `CapsuleExtensionData`) are out of scope.
- This specification does not require the function-call subsystem: the
  `cty/function` and `cty/function/stdlib` packages are out of scope.
- This specification does not require reflection bridging to native Go
  structs: the `cty/gocty` package is out of scope.
- This specification does not require the grapheme-cluster helper package
  `cty/ctystrings` beyond the behavior of `StringPrefix` refinement trimming
  described below.
- This specification does not require `encoding/gob` support for values or
  types.
- This specification does not require the `cty/planmerge` or `cty/set`
  packages as importable surfaces; set behavior is exercised through set-typed
  values and `cty.ValueSet`.
- This specification does not define Go language-version constraints beyond
  the environment described in Appendix A.

## Representative Workflows

**Workflow 1 — validate, convert, and serialize a configuration object.**
An application receives loosely-typed input, converts it to a declared schema
type, and stores it as JSON. Type mismatches surface as conversion errors
rather than panics; nulls pass through conversion unchanged; the JSON bytes
decode back to a value equal to the stored one when the same type is supplied.

```go
schema := cty.Object(map[string]cty.Type{
    "name":  cty.String,
    "port":  cty.Number,
    "tags":  cty.Set(cty.String),
})

input := cty.ObjectVal(map[string]cty.Value{
    "name": cty.StringVal("web"),
    "port": cty.StringVal("8080"),                  // string, needs conversion
    "tags": cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("a")}),
})

v, err := convert.Convert(input, schema)            // "8080" -> cty.Number, list -> set
if err != nil { /* user-facing type error */ }

buf, err := ctyjson.Marshal(v, schema)
restored, err := ctyjson.Unmarshal(buf, schema)
// restored.RawEquals(v) == true
```

**Workflow 2 — partial evaluation with unknowns, refinements, and marks.**
A static checker evaluates an expression tree before all inputs are known.
Unknown inputs flow through operations as unknown results with refinements
that narrow them; marks applied to inputs survive arithmetic and equality; a
MessagePack round trip preserves unknownness and refinements for a downstream
process that continues the evaluation.

```go
count := cty.UnknownVal(cty.Number).Refine().
    NotNull().
    NumberRangeInclusive(cty.Zero, cty.NumberIntVal(10)).
    NewValue()

over := count.GreaterThan(cty.NumberIntVal(20))     // cty.False — known from the range
sum := count.Add(cty.NumberIntVal(1)).Mark("audit") // unknown number, marked

buf, _ := ctymsgpack.Marshal(count, cty.Number)
later, _ := ctymsgpack.Unmarshal(buf, cty.Number)
// later is still unknown, still refined non-null with the numeric range

plain, marks := sum.Unmark()                        // integration boundary
_ = plain; _ = marks
```

## Type System

The type system distinguishes primitive types, collection kinds, structural
kinds, and one pseudo-type; a `cty.Type` value identifies one of these and
supports equality, conformance testing, and naming projections.

**Primitive types.** `cty.Number`, `cty.String`, and `cty.Bool` are package
variables. `Type.IsPrimitiveType` returns `true` exactly for these three.

**Collection kinds.** `cty.List`, `cty.Map`, and `cty.Set` each take a single
element type and return a collection type. `Type.IsCollectionType` returns
`true` for all three kinds; `IsListType`, `IsMapType`, and `IsSetType`
identify the specific kind. `Type.ElementType` returns the element type of a
collection type and panics for non-collection types. The kind-specific
accessors `ListElementType`, `MapElementType`, and `SetElementType` each
return a pointer to the element type when the receiver is of that kind and
nil otherwise, giving callers a one-step test-and-extract.

**Structural kinds.** `cty.Object` takes a map from attribute name to type;
`cty.Tuple` takes a slice of element types. `cty.EmptyObject` and
`cty.EmptyTuple` are the zero-attribute and zero-element types. For object
types, `AttributeTypes` returns the full name-to-type map, `AttributeType`
returns one attribute's type and panics when the attribute does not exist,
and `HasAttribute` reports existence without panicking. For tuple types,
`Type.Length` returns the element count and panics for non-tuple types;
`TupleElementType` returns the type at an index and `TupleElementTypes`
returns all of them in order.

**Optional attributes.** `cty.ObjectWithOptionalAttrs` builds an object type
in which a listed subset of attributes is annotated optional. The annotation
participates in type identity: an object type with an optional annotation is
not equal to the same attribute structure without it, and
`WithoutOptionalAttributesDeep` returns the annotation-free equivalent.
`AttributeOptional` reports whether a named attribute carries the annotation,
and `OptionalAttributes` returns the annotated set. The annotation changes
behavior only during conversion (see Conversion Engine); operations on values
ignore it.

**The dynamic pseudo-type.** `cty.DynamicPseudoType` is a placeholder for a
type not yet known. It has no known non-null values; `cty.DynamicVal` is the
unknown value of this type and `cty.NullVal(cty.DynamicPseudoType)` is its
null. `Type.HasDynamicTypes` returns `true` when the pseudo-type appears
anywhere inside a compound type. `cty.NilType` is the zero `cty.Type`,
returned by APIs that must report "no type".

**Equality and conformance.** `Type.Equals` implements exact structural
equality: object attribute maps and tuple element sequences must match
entirely, and attribute order in a constructor map is irrelevant.
`Type.TestConformance` implements a weaker relation: it returns nil when the
receiver conforms to the given type, treating `cty.DynamicPseudoType` in the
given type as a wildcard at any depth, and returns a non-empty `[]error`
describing each mismatch otherwise.

**Naming.** `Type.FriendlyName` returns a user-oriented name such as
`list of string`; for object types it returns `object`, and for the dynamic
pseudo-type it returns `dynamic`. `FriendlyNameForConstraint` differs in
naming the dynamic pseudo-type `any type`. `Type.GoString` returns the Go
constructor expression, such as `cty.Map(cty.Bool)`.

## Value Construction and Content Model

Every value is constructed through a typed factory, and every value is
exactly one of: known and non-null, null, or unknown. Construction failures
are panics — the factories enforce their preconditions rather than returning
errors.

**Primitives.** `cty.StringVal` builds a string value, normalizing the input
to Unicode NFC form (combining sequences become precomposed characters where
available). `AsString` returns the normalized native string and panics when
the receiver is not a known string. `cty.BoolVal` builds a boolean;
`cty.True` and `cty.False` are ready-made. `Value.True` and `Value.False`
return the native boolean and panic on non-boolean receivers.

**Numbers.** `cty.NumberIntVal`, `cty.NumberUIntVal`, and `cty.NumberFloatVal`
build numbers from native Go numerics; the full `int64` and `uint64` ranges
are represented exactly. `cty.ParseNumberVal` parses a decimal string and
returns an error for unparseable input with the message `a number is
required`; `cty.MustParseNumberVal` wraps it and panics on error.
`cty.NumberVal` accepts a caller-supplied `*big.Float`. A number constructed
from the string `"0.1"` and one constructed from the float64 `0.1` are equal —
decimal inputs are corrected to their decimal meaning rather than inheriting
binary float error, and arithmetic identities such as `0.1 + 0.2 == 0.3` hold
for parsed decimals. `cty.Zero`, `cty.PositiveInfinity`, and
`cty.NegativeInfinity` are package variables; the infinities compare greater
than and less than every finite number respectively. `AsBigFloat` returns the
numeric content and panics for non-number receivers. Negative zero parses to
a value equal to `cty.Zero`.

**Collections.** `cty.ListVal` takes a non-empty `[]cty.Value` whose elements
all have one type and panics otherwise — with distinct messages for an empty
slice and for inconsistent element types; `cty.ListValEmpty` takes an element
type and builds the empty list. `cty.MapVal` and `cty.MapValEmpty` are the
map equivalents keyed by native strings. `cty.SetVal` takes a `[]cty.Value`,
deduplicates equal elements, and produces a set; `cty.SetValEmpty` builds an
empty set. `cty.TupleVal` and `cty.ObjectVal` derive their type from the
values supplied; `cty.EmptyTupleVal` and `cty.EmptyObjectVal` are the known
empty values of the empty structural types.

**Null and unknown.** `cty.NullVal` builds the null of any type;
`cty.UnknownVal` builds the unknown of any type. `cty.NilVal` is the zero
`cty.Value`. `IsNull` reports nullness. `IsKnown` reports whether the
receiver itself is known; `IsWhollyKnown` additionally requires every nested
value to be known, so a known list containing an unknown element is known but
not wholly known. `HasWhollyKnownType` reports whether the value's type
contains no dynamic placeholders anywhere. `cty.UnknownAsNull` returns a deep
copy of a value in which every unknown, at any depth, is replaced by the null
of its type.

## Value Operations

Operation methods stay inside the value model: they accept and return
`cty.Value`, they propagate unknownness and marks automatically, and they
panic when applied to a receiver of the wrong type — a type mismatch is a
programming error, not a runtime condition.

**The equality ladder.** Three distinct sameness relations exist and must not
be conflated. `Value.Equals` is the user-model relation: it returns a
`cty.Bool` value; when either operand is unknown or dynamically-typed the
result is an unknown boolean refined non-null rather than a known answer;
nulls of the same type are equal to each other, and a null compares unequal
(known `cty.False`) to any known non-null value of the same type; two values
of different known types are never equal (`cty.False`) rather than an error.
`Value.NotEqual` returns the negation. `Value.RawEquals` is the test-support
relation: it returns a native Go `bool`, treats two unknowns of the same type
with the same refinements as equal, and is sensitive to marks — a marked
value is not raw-equal to its unmarked twin. Mark presence does not affect
`Equals`: comparing a marked value applies the marks to the resulting boolean
instead. The third relation is type equality, described in Type System.

**Arithmetic and comparison.** Numbers support `Add`, `Subtract`,
`Multiply`, `Divide`, `Modulo`, `Negate`, `Absolute`, `GreaterThan`,
`GreaterThanOrEqualTo`, `LessThan`, and `LessThanOrEqualTo`. Division by zero
returns the appropriately-signed infinity; `Modulo` with a zero divisor
returns the dividend. Booleans support `And`, `Or`, and `Not`. When any
operand is unknown the result is unknown with the appropriate type, refined
non-null. Applying a numeric operation to a non-number panics with a type
mismatch message.

**Collection and structure access.** `Index` retrieves an element of a list,
map, or tuple by key value and panics for a key that is not present;
`HasIndex` returns a `cty.Bool` reporting whether `Index` would succeed, and
supports lists, maps, and tuples only — calling it on a set panics.
`HasElement` reports set membership, returns `cty.Bool`, and panics on
non-set receivers. `GetAttr` returns an object attribute by name and panics
when the attribute does not exist in the type; `GetAttr` on an unknown object
returns an unknown of the attribute's type. `Length` returns the element
count as a `cty.Number`; on a set containing unknown elements it returns an
unknown number refined non-null with an inclusive range from the count of
distinct known elements up to the total element count, because unknown set
members collapse together if they turn out equal once known. `Length` panics
on a null receiver. `LengthInt` returns a native `int` and requires a known
length.

**Iteration.** `CanIterateElements` reports whether the receiver's type
supports element iteration (lists, maps, sets, tuples, and object values).
`ElementIterator` yields key/value pairs in order — integer indices for lists
and tuples, lexicographically ordered keys for maps — and panics on an
unknown receiver. `ForEachElement` runs a callback per element in the same
order; the callback returning `true` stops the iteration early, and
`ForEachElement` returns `true` exactly when it was stopped early.
`AsValueSlice`, `AsValueMap`, and `AsValueSet` convert known collections to
native Go containers of `cty.Value`.

**Set values as native sets.** `cty.ValueSet` is a mutable native-Go set of
`cty.Value` with one fixed element type: `cty.NewValueSet` creates one,
`Add`/`Remove`/`Has`/`Values`/`Length`/`Copy`/`ElementType` behave as their
names suggest, `Union`, `Intersection`, `Subtract`, and `SymmetricDifference`
combine two sets, and adding a value of the wrong element type panics.
`cty.SetValFromValueSet` converts a `ValueSet` back into a set value. Set
element identity is value equality: two independently-built equal objects
occupy one slot.

**Traversal.** `cty.Walk` visits a value and every nested value in
depth-first order, invoking a callback with the `cty.Path` to each node
(the root path is empty); the callback returning `false` prunes descent into
that node, and a callback error aborts the walk with that error. `cty.Transform`
rebuilds a value bottom-up by applying a callback to every leaf and node,
returning the transformed value or the first callback error.

## Paths

A `cty.Path` is a sequence of steps addressing a nested position inside a
value, built fluently and applied dynamically.

**Construction.** `cty.GetAttrPath` and `cty.IndexPath` begin a path with an
attribute step or an index step; `cty.IndexIntPath` and `cty.IndexStringPath`
are convenience starters for numeric and string keys. The methods `GetAttr`,
`Index`, `IndexInt`, and `IndexString` append further steps and return the
extended path. `Path.Copy` returns an independent copy.

**Application and comparison.** `Path.Apply` traverses a starting value step
by step and returns the addressed value, or an error identifying the failing
step: applying an attribute step for a missing attribute reports `at step N:
object has no attribute "name"`; an index step whose key is absent reports
`at step N: value does not have given index key`; traversing into a null
value reports `at step N: cannot access attributes on a null value`.
`Path.Equals` compares two paths step-by-step, and `Path.HasPrefix` reports
whether the receiver begins with the given path. The step types
`cty.GetAttrStep` (field `Name`) and `cty.IndexStep` (field `Key`) are public,
as is the `cty.PathStep` interface they implement.

## Marks

Marks attach caller-defined metadata to a value; they propagate through
operation methods automatically and block integration methods until removed.

**Attaching and inspecting.** `Value.Mark` returns the receiver with one mark
added; repeated marking accumulates distinct marks. `cty.NewValueMarks`
builds a `cty.ValueMarks` set from mark values, `Value.WithMarks` applies
such sets, and `Value.Marks` returns the current mark set. `IsMarked`
reports marks on the receiver itself; `ContainsMarked` reports marks anywhere
within; `HasMark` tests one mark; `HasMarkDeep` tests one mark at any depth;
`HasSameMarks` compares the mark sets of two values.

**Propagation.** When any operand of an operation method is marked, the
result carries the union of the operand marks: arithmetic on a marked number
yields a marked number, `Equals` on a marked operand yields a marked boolean,
and `GetAttr`/`Index` through a marked container yield marked elements.
Integration methods (`AsString`, `AsBigFloat`, `True`, `LengthInt`,
`AsValueSlice`, and the other native-Go extractors) panic on a marked
receiver with a message stating the value must be unmarked first.

**Removal and reapplication.** `Value.Unmark` returns the unmarked value and
its mark set. `UnmarkDeep` removes marks at all depths, returning the
aggregate set. `UnmarkDeepWithPaths` instead returns a `[]cty.PathValueMarks`
recording which path carried which marks — `cty.PathValueMarks` is a public
struct pairing `Path` with `Marks` — and `MarkWithPaths` reapplies such a
record.

**Sets flatten element marks.** A set value never contains marked elements:
`cty.SetVal` unmarks any marked inputs and applies the union of their marks
to the set value as a whole, so element access through a set-level mark
still observes marked data.

## Unknown Values and Refinements

An unknown value carries a type constraint and, optionally, refinements that
shrink its possible range; refinements let some operations return known
results from unknown inputs.

**The refinement builder.** `Value.Refine` returns a `*cty.RefinementBuilder`;
chained calls declare refinements and `NewValue` produces the refined value.
`NotNull` declares the final value non-null (`Value.RefineNotNull` is the
one-call shorthand); `Null` declares it null, which collapses to the known
null of the type. For strings, `StringPrefix` declares a known prefix but
quietly drops trailing code units of the given prefix that would combine with
a following combining character (so a prefix ending in a plain letter is shortened by one
character), while `StringPrefixFull` keeps the prefix exactly as given. For
numbers, `NumberRangeLowerBound` and `NumberRangeUpperBound` declare bounds
with a per-bound inclusive flag, and `NumberRangeInclusive` declares both
inclusive bounds at once. For lists, sets, and maps,
`CollectionLengthLowerBound`, `CollectionLengthUpperBound`, and the
both-bounds shorthand `CollectionLength` constrain element counts.

**Refinement rules.** Refining a known value is a self-check: consistent
refinements return the value unchanged and contradictory ones panic
(a known string that does not start with a declared `StringPrefixFull`
panics with a message that the refined prefix is inconsistent with the known
value). Declaring a refinement that contradicts an existing refinement on an
unknown value panics. Refining the null of a type as non-null panics.
`cty.DynamicVal` ignores all refinement attempts and remains exactly itself.

**Refinements at work.** A number refined to an inclusive range returns known
comparison results against values wholly outside the range — a value refined
to at most 10 is known not to be greater than 20 — and an unknown refined
non-null compares definitively unequal to null. A collection refined to one
exact length reports that length as a known `cty.Number` from `Length` even
though the collection itself remains unknown. Unknown results of operations
on non-null operands are refined non-null.

**Value ranges.** `Value.Range` returns a `cty.ValueRange` describing a
superset of the possible final values, for known and unknown receivers alike:
`DefinitelyNotNull` is `true` for any known non-null value and for unknowns
refined non-null; `CouldBeNull` is its complement; `TypeConstraint`,
`StringPrefix`, `NumberLowerBound`, `NumberUpperBound`,
`LengthLowerBound`, and `LengthUpperBound` expose the refined bounds, and
`Includes` reports whether a candidate value falls inside the range as a
`cty.Bool`.

## Conversion Engine

The `convert` package turns a value of one type into a value of another type
under explicit safety rules, and unifies multiple types into one common type.

**Safe and unsafe.** `GetConversion` returns a `Conversion` — a function from
value to value-or-error — when a _safe_ conversion exists from one type to
another, meaning every source value is representable; `GetConversionUnsafe`
additionally admits conversions that only accept a subset of source values.
Both return nil when no conversion exists, and no conversion exists from a
type to itself. `Convert` is the convenience entry point: it converts a value
to a target type using the unsafe tier, returning the converted value or an
error, and returns the input as-is semantics for nulls and unknowns — the
null of the source type becomes the null of the target type, and an unknown
source becomes an unknown of the target type.

**Primitive matrix.** Number-to-string and bool-to-string conversions are
safe; string-to-number and string-to-bool are unsafe; number and bool do not
interconvert. Number-to-string renders the full-precision decimal form
without exponent notation (`1e21` becomes `1000000000000000000000`, `1e-3`
becomes `0.001`). String-to-bool accepts exactly `"true"` and `"false"`;
the error for `"True"` states that lowercase `"true"` is required; the error
for a non-numeric string is `a number is required`; a failed bool conversion
without a near-miss is `a bool is required`. Converting number to bool
reports `bool required, but have number`.

**Collection and structural matrix.** Conversions between collection kinds
and from structural kinds to collection kinds exist when the element paths
admit conversion: list-to-set and set-to-list are available in both
directions, map-to-object and object-to-map likewise, tuple-to-list and
tuple-to-set convert by unifying the element types, and a heterogeneous tuple
whose elements cannot unify fails with `all list elements must have the same
type`. The empty tuple converts to an empty list of the target element type.
Converting a list to a tuple type is not available and fails with `tuple
required`. Element-level conversions apply recursively, so a list of numbers
converts to a list of strings element-by-element.

**Object structural typing.** Conversion between object types treats the
target as a structural constraint: source attributes absent from the target
type are silently discarded; a target attribute missing from the source is an
error `attribute "name" is required`, unless the target type marks that
attribute optional (via `cty.ObjectWithOptionalAttrs`), in which case the
result carries a typed null for it. Attribute values convert recursively.

**Dynamic placeholders.** Converting _to_ `cty.DynamicPseudoType` passes the
value through unchanged. A conversion _from_ `cty.DynamicPseudoType`
(obtained through the unsafe tier) performs the conversion at call time based
on the actual runtime type of the argument — it converts convertible values
and returns an error such as `string required, but have list of string` when
the runtime type does not convert. Converting the value `cty.DynamicVal`
to any type yields the unknown of that type.

**Marks under conversion.** Conversions propagate marks: a marked scalar
converts to a marked result, a marked element inside a converted container
stays marked in place, and converting a structure into a set lifts element
marks onto the set as a whole.

**Unification.** `Unify` and `UnifyUnsafe` take a `[]cty.Type` and return a
single type all inputs convert to plus one `Conversion` per input (nil where
the input already has the result type), or `cty.NilType` and nil when no
common type exists. Safe unification uses only safe conversions;
`UnifyUnsafe` also uses unsafe ones. Number and string unify to string;
number and bool do not unify in either tier. Object types unify
attribute-by-attribute when their attribute sets match. A list and a set of
one element type unify to the list type. Any input containing
`cty.DynamicPseudoType` draws the unification toward the pseudo-type. An
empty input slice yields `cty.NilType` and a nil conversion slice.

**Mismatch explanation.** `MismatchMessage` renders a human-oriented
explanation of why one type does not fit another: `number required` for a
primitive mismatch, `attribute "b" is required` for a missing object
attribute, `incorrect list element type: number required, but have bool` for
an element mismatch, and `element 0: number required, but have bool` when a
tuple's element blocks conversion to a list.

## JSON Codec

The `json` package serializes values against a caller-supplied type and
recovers them losslessly when the same type is supplied for decoding.

**Marshal.** `Marshal` takes a value and a type and returns JSON bytes.
Lists, sets, and tuples lower to JSON arrays; maps and objects lower to JSON
objects; null values of any type lower to JSON `null`; numbers render at full
precision without quotation. A value whose type differs from the given type
is first converted, so marshaling a number against `cty.String` produces a
JSON string; an inconvertible value returns the conversion error. Marshaling
any unknown value returns an error stating the value is not known. Marshaling
a marked value returns an error stating the value has marks so it cannot be
serialized as JSON. Wherever `cty.DynamicPseudoType` appears in the given
type, the encoding at that position becomes a two-property JSON object with
`"value"` and `"type"` properties, embedding the runtime type that decoding
uses to recover it.

**Unmarshal.** `Unmarshal` decodes JSON bytes against a given type and
returns the typed value. A JSON object decoded against an object type
tolerates missing attributes by filling typed nulls, and rejects extraneous
properties with an error naming the unsupported attribute. A JSON `null`
document decodes to the typed null. Where the given type embeds
`cty.DynamicPseudoType`, the decoder expects the two-property wrapper and
restores the embedded type. Scalar mismatches surface the primitive
conversion errors (for example `a number is required`).

**Type introspection and serialization.** `ImpliedType` inspects raw JSON
bytes and returns the most specific type under the standard mapping — JSON
strings, numbers, and booleans to the primitives, arrays to tuple types,
objects to object types, and `null` to `cty.DynamicPseudoType` — or an error
for malformed JSON. `MarshalType` and `UnmarshalType` serialize a `cty.Type`
itself to JSON (primitives as name strings such as `"string"`, compound
types as tagged arrays such as `["list",["object",{"a":"string"}]]`) and back.

**SimpleJSONValue.** `SimpleJSONValue` is a struct wrapper embedding a
`cty.Value` that plugs into the standard library `encoding/json`: marshaling
writes the type-lossy JSON form, and unmarshaling applies the standard
mapping, producing tuple types for arrays, object types for JSON objects,
and `cty.NullVal(cty.DynamicPseudoType)` for `null`.

## MessagePack Codec

The `msgpack` package mirrors the JSON codec's type-directed model and
additionally represents unknown values, which lets partially-evaluated data
move between processes.

**Round trips.** `Marshal` takes a value and a type and returns MessagePack
bytes; `Unmarshal` reverses it with the same type. Known values, nulls, and
full-precision numbers round-trip to values raw-equal to the originals.
Wherever the given type embeds `cty.DynamicPseudoType`, the runtime type is
embedded at that position and restored on decode. `ImpliedType` inspects
MessagePack bytes and returns a type under the same mapping rules as the
JSON codec's `ImpliedType`.

**Unknowns and refinements.** Marshaling an unknown value succeeds, encoding
an unknown placeholder as a MessagePack extension. Refinements on the
unknown are approximated in the encoding: non-nullness, string prefixes, and
numeric range bounds survive a round trip, and the decoded range is never
narrower than the original. Marshaling a marked value returns an error
stating the value has marks so it cannot be serialized.

## State Model

A value is an immutable record of five facts: a type; a nullness flag; a
knownness flag; for unknown values, a refinement record (non-nullness, string
prefix, numeric bounds, or length bounds as applicable to the type); and a
mark set. Every public surface is a projection of these five facts:

- Operation methods on `Value` consume and produce whole records —
  unknownness, refinements, and marks flow through them.
- Integration methods project the payload out to native Go and refuse
  receivers whose record still carries marks or unknownness (panic).
- `Type` methods project only the type fact.
- `convert` rewrites the type fact while preserving nullness, unknownness,
  and marks.
- The `json` codec projects known unmarked records to bytes and back;
  the `msgpack` codec projects known and unknown unmarked records to bytes
  and back, approximating refinements.

Values never mutate: every operation returns a new value, and `ValueSet` is
the only mutable container in the covered surface.

## Error Semantics

Failures split into three families: panics for caller programming errors,
Go errors for data-dependent failures, and unknown/null propagation for
absent information. The table lists the required classifications.

| Condition | Result |
|---|---|
| Operation method on wrong-typed receiver (e.g. `Add` on strings, `HasIndex` on a set, `HasElement` on a list, `AsString` on a number, `True` on a number) | panic with a type-mismatch message |
| `cty.ListVal` with empty slice | panic (`must not call ListVal with empty slice`) |
| `cty.ListVal`/`cty.MapVal` with inconsistent element types | panic naming both types |
| `GetAttr`/`AttributeType` for a missing attribute; `Index` for a missing key | panic |
| `Length` on a null value; `ElementIterator` on an unknown value | panic |
| Integration method on a marked value | panic stating the value is marked and must be unmarked first |
| `Type.ElementType` on non-collection; `Type.Length` on non-tuple | panic |
| Refining a known value contradictorily; contradicting an earlier refinement; refining a null as non-null; `ValueSet.Add` with mismatched element type | panic |
| `cty.ParseNumberVal` with a non-numeric string | error `a number is required` (`MustParseNumberVal` panics) |
| `convert.Convert` failure | error with the messages given in Conversion Engine |
| `json.Marshal` of unknown | error `value is not known` |
| `json.Marshal` of marked value | error `value has marks, so it cannot be serialized as JSON` |
| `msgpack.Marshal` of marked value | error `value has marks, so it cannot be serialized` |
| `json.Unmarshal` extraneous object property | error naming the unsupported attribute |
| `json.ImpliedType` of malformed JSON | error |
| `Path.Apply` step failure | error prefixed `at step N:` with the step-specific message |
| Operation on unknown operands | unknown result of the proper type, refined non-null — never an error |

## Cross-View Invariants

1. **Conversion preserves equality classes.** When `convert.Convert`
   succeeds on two values of one type and `Equals` returns known `cty.True`
   for them, the converted results must also be equal under `Equals`; nulls
   convert to nulls and unknowns to unknowns of the target type.
2. **JSON round trip is the identity.** For any known, unmarked value and
   its type, `json.Unmarshal(json.Marshal(v, t), t)` must return a value
   raw-equal to `v`, including full numeric precision; and the bytes must
   decode under `ImpliedType` to a type whose value content, after
   `convert.Convert` to `t`, equals `v`.
3. **Msgpack extends the JSON contract to unknowns.** For any unmarked value
   including unknowns, msgpack round trip must preserve knownness, nullness,
   and type; a refined unknown must decode to a range no narrower and no
   wider than a superset of the original range as observed through
   `Value.Range`.
4. **Refined answers agree with eventual values.** Any known result an
   operation produces from refined unknowns (comparisons outside a numeric
   range, `Length` of an exact-length collection, non-null inequality to
   null) must equal the result the same operation produces after the unknown
   is replaced by any concrete value satisfying the refinement.
5. **Marks never alter data, only annotate it.** For any operation, the
   unmarked content of the result of the marked inputs must raw-equal the
   result of the same operation on unmarked inputs, and the result's mark
   set must be the union of the operand mark sets — across value operations
   and conversions alike.
6. **Type projections agree.** For every value, `v.Type().Equals` the type
   reported through any other surface: the element type of `AsValueSet`,
   the type recovered by `json.UnmarshalType(json.MarshalType(t))`, and the
   `TypeConstraint` of `v.Range()` must all equal it.
7. **Iteration agrees with access.** For lists, maps, and tuples, every
   key/value pair produced by `ElementIterator` or `ForEachElement` must
   satisfy `HasIndex` = `cty.True` and `Index` returning that element, and
   the pair count must equal `LengthInt`.

## Public Interface

### Import Surface

```go
import (
    "github.com/zclconf/go-cty/cty"
    "github.com/zclconf/go-cty/cty/convert"
    ctyjson "github.com/zclconf/go-cty/cty/json"
    ctymsgpack "github.com/zclconf/go-cty/cty/msgpack"
)
```

### API Catalog — cty

| Name | Kind | Role |
|---|---|---|
| `Type` | struct type | identity of a type; equality, conformance, naming, kind tests |
| `Value` | struct type | immutable typed value with null/unknown/marks/refinements |
| `Number`, `String`, `Bool` | variables | the primitive types |
| `List`, `Map`, `Set` | functions | collection type constructors |
| `Object`, `Tuple` | functions | structural type constructors |
| `ObjectWithOptionalAttrs` | function | object type with optional-attribute annotations |
| `EmptyObject`, `EmptyTuple` | variables | zero-attribute / zero-element structural types |
| `DynamicPseudoType` | variable | placeholder type |
| `NilType` | variable | zero `Type` |
| `StringVal`, `BoolVal` | functions | primitive value constructors |
| `NumberVal`, `NumberIntVal`, `NumberUIntVal`, `NumberFloatVal` | functions | number constructors |
| `ParseNumberVal`, `MustParseNumberVal` | functions | decimal-string number constructors |
| `Zero`, `PositiveInfinity`, `NegativeInfinity` | variables | ready-made numbers |
| `True`, `False` | variables | ready-made booleans |
| `ListVal`, `ListValEmpty`, `MapVal`, `MapValEmpty`, `SetVal`, `SetValEmpty`, `TupleVal`, `ObjectVal` | functions | compound value constructors |
| `EmptyObjectVal`, `EmptyTupleVal` | variables | known empty structural values |
| `NullVal`, `UnknownVal` | functions | null / unknown constructors |
| `NilVal` | variable | zero `Value` |
| `DynamicVal` | variable | unknown value of the dynamic pseudo-type |
| `UnknownAsNull` | function | deep unknown-to-null rewrite |
| `Walk`, `Transform` | functions | path-aware traversal and rewrite |
| `Path`, `PathStep`, `GetAttrStep`, `IndexStep` | types | value addressing |
| `GetAttrPath`, `IndexPath`, `IndexIntPath`, `IndexStringPath` | functions | path starters |
| `ValueMarks`, `NewValueMarks`, `PathValueMarks` | type/function/type | mark sets and per-path mark records |
| `ValueRange` | struct type | range projection of a value |
| `RefinementBuilder` | struct type | fluent refinement construction |
| `ValueSet`, `NewValueSet`, `SetValFromValueSet` | type/functions | mutable native set of values |
| `ElementIterator`, `ElementCallback` | types | iteration protocol |

### API Catalog — convert

| Name | Kind | Role |
|---|---|---|
| `Convert` | function | value conversion to a target type (unsafe tier) |
| `Conversion` | function type | reusable conversion from value to value-or-error |
| `GetConversion`, `GetConversionUnsafe` | functions | conversion lookup by type pair |
| `Unify`, `UnifyUnsafe` | functions | common-type inference over a type slice |
| `MismatchMessage` | function | human-oriented type-mismatch explanation |

### API Catalog — json

| Name | Kind | Role |
|---|---|---|
| `Marshal`, `Unmarshal` | functions | type-directed value serialization |
| `MarshalType`, `UnmarshalType` | functions | type serialization |
| `ImpliedType` | function | most-specific type of raw JSON bytes |
| `SimpleJSONValue` | struct type | type-lossy bridge to `encoding/json` |

### API Catalog — msgpack

| Name | Kind | Role |
|---|---|---|
| `Marshal`, `Unmarshal` | functions | type-directed serialization with unknown support |
| `ImpliedType` | function | most-specific type of MessagePack bytes |

### CLI Entry Points

There is no console script for this module. Programmatic use is through Go
imports only.

## Appendix A: Environment

The working environment runs Go 1.25 on Linux with module-proxy access for
dependency download at build time. The delivery is a Go module named
`github.com/zclconf/go-cty` exposing the four packages in the Import Surface.
The packages `github.com/vmihailenco/msgpack/v5`,
`github.com/apparentlymart/go-textseg/v17`, and `golang.org/x/text` are
available from the module proxy for use as dependencies. Tests build the
delivery as a module dependency; no system-installed copy of the module is
consulted.

## Appendix B: Assessment Notes

Functional assessment exercises the documented behavior through the public
API only. Dimensions covered:

- type construction, identity, conformance, and naming projections;
- value construction preconditions and the known/null/unknown content model;
- the equality ladder (`Equals` vs `RawEquals` vs type equality) including
  unknown and dynamic operands;
- arithmetic, comparison, indexing, attribute access, iteration order, and
  panic classifications;
- marks: propagation through operations and conversions, integration-method
  refusal, deep unmark/remark records, set flattening;
- refinements: builder behavior, self-check panics, known answers from
  refined unknowns, range projection;
- conversion: the primitive and structural matrices, object structural
  typing with optional attributes, dynamic placeholders, mark propagation,
  unification tiers, and mismatch messages;
- JSON and MessagePack codecs: round trips, dynamic type embedding, implied
  types, type serialization, unknown/refinement encoding (msgpack), and
  serialization refusals.

Scoring runs the accompanying test suites against the delivered module;
each test passes or fails independently, and both per-behavior checks and
multi-surface integration scenarios contribute to the result.
