# jsonschema Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jsonschema` is an embedded Go library that compiles JSON Schema documents
into an executable schema graph and validates decoded JSON values against it.
A `Compiler` collects schema resources, resolves every reference between them
at compile time, and produces immutable `Schema` nodes. Validating an instance
against a compiled `Schema` either succeeds silently or returns a structured
error tree that is projected through several standardized output formats.

The module path is `github.com/santhosh-tekuri/jsonschema/v6`; the primary
package name is `jsonschema`. A companion package
`github.com/santhosh-tekuri/jsonschema/v6/kind` carries the typed error-kind
values that discriminate why a validation failed.

The library speaks JSON Schema draft 2020-12 by default and compiles
documents that declare earlier dialects through `$schema`. Numeric comparison
is exact: numbers are handled as arbitrary-precision rationals, never as
IEEE-754 floats.

## Non-Goals

- This specification does not require localized output: the methods accepting
  a `message.Printer` (`LocalizedError`, `LocalizedBasicOutput`,
  `LocalizedDetailedOutput`, `LocalizedGoString`) and the `GoString` method
  are present in the upstream surface but their behavior is not assessed.
- This specification does not require content assertions: `contentEncoding`,
  `contentMediaType`, `contentSchema`, `Compiler.AssertContent`,
  `RegisterContentEncoding`, and `RegisterContentMediaType` are not assessed.
- This specification does not require format assertion: the `format` keyword
  is collected as an annotation and must not reject instances unless a caller
  opts in; the opt-in (`AssertFormat`) and individual format rules are not
  assessed.
- This specification does not require custom vocabularies or extension hooks:
  `RegisterVocabulary`, `AssertVocabs`, `Vocabulary`, `SchemaExt`,
  `CompilerContext`, and `ValidatorContext` are not assessed.
- This specification does not require pluggable regexp engines
  (`UseRegexpEngine`); the default engine is Go's `regexp` package.
- This specification does not require network access of any kind: no URL is
  fetched over HTTP, and loading behavior beyond the local-file and
  caller-registered cases described below is not assessed.
- This specification does not define exact human-readable message text,
  `Error()` line layout, or `String()` formats; assessments check error
  types, structured fields, and output-unit shapes, never message wording.
- This specification does not require the `jv` command-line tool.

## Representative Workflows

**Compile and validate an in-memory schema.** A caller decodes a schema
document with `UnmarshalJSON`, registers it under a URL with
`Compiler.AddResource`, compiles that URL, and validates decoded instances.

```go
schema, err := jsonschema.UnmarshalJSON(strings.NewReader(`{
    "type": "object",
    "properties": {"count": {"type": "integer", "minimum": 3}},
    "required": ["count"]
}`))
// err is nil
c := jsonschema.NewCompiler()
err = c.AddResource("https://app.example/config.json", schema)
// err is nil
sch, err := c.Compile("https://app.example/config.json")
// err is nil
inst, _ := jsonschema.UnmarshalJSON(strings.NewReader(`{"count": 1}`))
err = sch.Validate(inst)
// err is a *jsonschema.ValidationError whose single cause reports the
// minimum violation at instance location /count
```

**Inspect a failure through the output formats.** After a failed validation,
the same error state is projected three ways.

```go
verr := err.(*jsonschema.ValidationError)
flag := verr.FlagOutput()      // FlagOutput{Valid: false}
basic := verr.BasicOutput()    // flat list of leaf failures
detailed := verr.DetailedOutput() // hierarchical failure tree
_ = flag; _ = basic; _ = detailed
```

**Cross-resource references.** Two documents registered on one compiler
reference each other by URL; compiling the referencing document resolves the
graph, and a dangling anchor or missing resource fails the compile with a
typed error.

```go
c := jsonschema.NewCompiler()
_ = c.AddResource("https://app.example/name.json",
    map[string]any{"type": "string", "minLength": 2})
_ = c.AddResource("https://app.example/person.json", map[string]any{
    "properties": map[string]any{
        "name": map[string]any{"$ref": "name.json"},
    },
})
sch := c.MustCompile("https://app.example/person.json")
err := sch.Validate(map[string]any{"name": "x"})
// err is non-nil: the referenced resource rejects one-character strings
```

## JSON Document Model

This section defines the value model every other section operates on; the
same model is used for schema documents and for instances.

**Decoding.** `UnmarshalJSON` reads one JSON document from an `io.Reader` and
returns it as `any`. Objects decode to `map[string]any`, arrays to `[]any`,
strings to `string`, booleans to `bool`, null to `nil`, and numbers to
`json.Number` so that no precision is lost. If the reader holds anything
other than exactly one JSON document — including trailing content after the
first document — `UnmarshalJSON` returns a non-nil error. Callers are free to
build instance values directly out of Go maps, slices, strings, `bool`,
`nil`, and native Go numeric types; validation must accept `json.Number`,
`int`/`int32`/`int64`, and `float32`/`float64` wherever a JSON number is
expected.

**JSON types.** A value has exactly one JSON type among `null`, `boolean`,
`string`, `number`, `object`, and `array`. The type keyword value `integer`
matches any `number` whose fractional part is zero: `2`, `2.0`, and
`json.Number("2.0")` all satisfy `{"type": "integer"}`, while `2.5` does not.

**Numeric equality and comparison.** All numeric comparison — `enum`,
`const`, `uniqueItems`, range keywords, and `multipleOf` — must be performed
with exact rational arithmetic. `1` and `1.0` are the same JSON value;
`0.3` must be accepted by `{"multipleOf": 0.1}` even though binary floating
point cannot represent these values exactly.

**String length.** String length is counted in Unicode code points, not
bytes: `"héé"` has length 3.

**JSON value equality.** Two values are equal when they have the same JSON
type and equal content: numbers by rational value, arrays element-wise in
order, objects by key set with equal values per key regardless of key order.

## Resource Registration and Compilation

A `Compiler` turns registered schema documents into compiled `Schema` nodes.
The compiler is created with `NewCompiler` and is not safe for concurrent
use.

**Registering resources.** `AddResource(url, doc)` registers a decoded schema
document under a URL. The `url` parameter accepts absolute URLs such as
`https://app.example/x.json`, `file://` URLs, and relative file paths (which
are resolved against the current directory into `file://` URLs). The fragment
must be empty. The `doc` parameter must be the decoded document (`any`), not
raw bytes. A schema document is either a `map[string]any` object or a `bool`
(boolean schema). WHEN a resource already exists at the same URL on the same
compiler, `AddResource` returns a `*ResourceExistsError`. WHEN `doc` is
neither an object nor a bool, the compile of that resource fails.

**Compiling.** `Compile(loc)` resolves the schema at location `loc` and
returns a `*Schema`. `loc` is a URL optionally followed by a fragment that is
either a JSON Pointer (`#/$defs/name`) or an anchor (`#name`). Compilation
walks every reference reachable from that location and compiles the full
graph; reference failures anywhere in the graph fail the compile. Compiling
the same location twice on one compiler returns the identical `*Schema`
pointer, and an anchor fragment and a JSON-Pointer fragment addressing the
same subschema return the identical pointer. `MustCompile(loc)` returns the
`*Schema` and panics in exactly the situations where `Compile` returns a
non-nil error.

**Compiled schema identity.** A compiled `Schema` exposes a `Location` field
— the absolute URL of the schema joined with its JSON-Pointer fragment, e.g.
`https://app.example/x.json#` for a root — and a `DraftVersion` field holding
the dialect number (4, 6, 7, 2019, or 2020).

**Dialect selection.** WHEN a schema document carries a `$schema` member, the
declared meta-schema URL selects the dialect for that resource: documents
declaring `http://json-schema.org/draft-07/schema#` compile with
`DraftVersion` 7, and the 2020-12 meta-schema URL selects 2020. WHEN
`$schema` is absent, the compiler's default draft applies; the initial
default is draft 2020-12. `DefaultDraft(d)` replaces the default; the
package-level variables `Draft4`, `Draft6`, `Draft7`, `Draft2019`, and
`Draft2020` are the accepted values. Under draft-07 semantics, `definitions`
plays the role of `$defs`, and an array-valued `items` constrains elements
positionally the way `prefixItems` does in 2020-12.

**Meta-schema validation.** Every registered document must itself be valid
against its dialect's meta-schema. WHEN a document violates its meta-schema —
for example `{"type": 1}` — `Compile` returns a `*SchemaValidationError`;
`AddResource` itself returns nil in this situation because validation happens
at compile time.

**Boolean schemas.** The document `true` compiles to a schema that accepts
every instance. The document `false` compiles to a schema that rejects every
instance. The compiled `Schema` for a boolean schema exposes the value
through its `Bool` field (a `*bool` that is nil for non-boolean schemas).

**Loading unregistered URLs.** WHEN `Compile` needs a URL that was not
registered, the compiler consults its loader. The default loader is
`FileLoader`, which handles only `file://` URLs by reading and decoding the
file; `FileLoader.ToFile` converts a `file://` URL to a filesystem path.
WHEN the URL cannot be loaded — wrong scheme for the active loader, missing
file, or undecodable content — `Compile` returns a `*LoadURLError` wrapping
the cause. `UseLoader(l)` replaces the loader with any implementation of the
`URLLoader` interface, whose single method `Load(url)` returns the decoded
document for a URL. `SchemeURLLoader` is a ready-made loader: a map from URL
scheme (`"file"`, `"https"`, ...) to the `URLLoader` for that scheme; WHEN
the scheme of the requested URL has no entry, its `Load` method returns an
`*UnsupportedURLSchemeError`, and a `Compile` that hits this situation
surfaces it as a `*LoadURLError`.

## Reference Resolution

References make the compiled graph: a schema node reuses another node instead
of duplicating it, across documents and inside them.

**`$ref`.** A `$ref` member holds a URI reference resolved against the base
URI of the containing resource. It reaches: other registered resources
(`{"$ref": "name.json"}`), JSON-Pointer fragments (`{"$ref":
"#/$defs/name"}`), and anchor fragments (`{"$ref": "#name"}`). Validation
through a `$ref` applies the referenced subschema exactly as if it had been
compiled directly: an instance rejected by the target is rejected through the
reference.

**`$defs` and `$anchor`.** `$defs` holds named subschemas addressable by JSON
Pointer. A subschema carrying `$anchor: "name"` is addressable within its
resource as fragment `#name`. IF a `$ref` names an anchor that does not exist
in the target resource, THEN `Compile` returns an `*AnchorNotFoundError`. IF
a JSON-Pointer fragment does not resolve to a location in the document, THEN
`Compile` fails.

**Embedded resources with `$id`.** A subschema carrying an absolute `$id`
becomes a separate resource embedded in its parent document; sibling
references resolve against the embedded resource's URL. Registering a parent
document makes its embedded resources referenceable without separate
`AddResource` calls.

**Recursion and cycles.** Self-referential schemas — for example a tree node
whose `children` items reference the node schema itself — must compile and
validate; recursion terminates because instances are finite.

**Dynamic references.** A subschema carrying `$dynamicAnchor: "name"` is a
dynamic anchor. `{"$dynamicRef": "#name"}` re-resolves the anchor against the
dynamic scope at validation time, so a recursive schema extended by another
resource validates nested values against the extending resource's anchor.
For a lone resource whose dynamic anchor is defined at its own root, a
`$dynamicRef` behaves like a recursive self-reference.

## Instance Validation: Scalar Keywords

`Schema.Validate(v)` checks the decoded instance `v` and returns nil for a
valid instance or a `*ValidationError` describing every violated keyword.
Keywords not present in a schema constrain nothing. Every keyword listed in
this and the following sections applies only to instances of its subject type
and ignores instances of other types (e.g. `minimum` ignores strings).

**Type checking.** `type` accepts a single type name or an array of names;
the instance must match at least one. The `integer` name follows the
zero-fraction rule from the document model.

**`enum` and `const`.** `enum` lists permitted values; the instance must
equal at least one element under JSON value equality. `const` must behave as
a one-element enum; `{"const": 1}` accepts `1.0`.

**Numeric range.** `minimum` and `maximum` are inclusive bounds;
`exclusiveMinimum` and `exclusiveMaximum` are strict bounds. `multipleOf`
requires the instance divided by the keyword value to be an integer, decided
with rational arithmetic.

**String constraints.** `minLength` and `maxLength` bound length in code
points. `pattern` holds a regular expression that must match somewhere in the
string (it is not anchored); the expression uses Go `regexp` syntax.

## Instance Validation: Objects and Arrays

**Object members.** `properties` maps member names to subschemas applied to
the corresponding member values. `patternProperties` maps regular expressions
to subschemas applied to every member whose name matches. A member matched by
both is validated against both. `additionalProperties` applies to members
matched by neither `properties` nor any `patternProperties` expression; the
value `false` rejects such members, and a subschema value validates them.
`propertyNames` applies its subschema to every member name as a string
instance.

**Object obligations.** `required` lists member names that must be present.
`minProperties` and `maxProperties` bound the member count.
`dependentRequired` maps a member name to further names that must be present
whenever that member is present. `dependentSchemas` maps a member name to a
subschema the whole object must satisfy whenever that member is present.

**Array shape.** In 2020-12 dialect, `prefixItems` holds positional
subschemas for the first elements, and `items` holds one subschema applied to
every element after the prefix; with no `prefixItems`, `items` covers every
element. `minItems` and `maxItems` bound the element count. `uniqueItems:
true` rejects arrays containing two equal elements under JSON value equality
— `[1, 1.0]` is rejected.

**`contains`.** `contains` requires at least one element matching its
subschema; `minContains` and `maxContains` bound the count of matching
elements, and `minContains: 0` makes an empty match acceptable.

**Unevaluated members.** `unevaluatedProperties` applies to object members
not evaluated by `properties`, `patternProperties`, `additionalProperties`,
or by those keywords inside successfully applied in-place applicators
(`allOf`, `anyOf`, `oneOf`, `if`/`then`/`else`, `$ref`) at the same instance
location. `unevaluatedItems` is the array analogue. Evaluation state is
shared across in-place applicators: a member accepted by a branch's
`properties` counts as evaluated for the parent's `unevaluatedProperties`.

## Schema Composition and Conditionals

**In-place applicators.** `allOf` requires every subschema to accept the
instance. `anyOf` requires at least one. `oneOf` requires exactly one:
zero matches and two-or-more matches are both violations. `not` inverts its
subschema. Applicators nest arbitrarily and compose with sibling keywords:
all sibling constraints apply in conjunction.

**Conditionals.** WHEN `if` accepts the instance, `then` (if present) must
also accept it; WHEN `if` rejects the instance, `else` (if present) must
accept it. `if` without `then`/`else` constrains nothing. `then`/`else`
without `if` constrain nothing.

**Boolean subschemas.** `true` and `false` are valid anywhere a subschema is
expected — `{"additionalProperties": false}`, `{"not": true}`, `{"items":
false}` — with the accept-all / reject-all semantics from the compilation
section.

## Validation Errors and Output Formats

A failed validation returns one `*ValidationError` for the schema root; the
full story of the failure is inside it.

**Error tree.** `ValidationError` exposes four fields. `SchemaURL` is the
absolute URL of the schema whose keyword failed. `InstanceLocation` is the
path of the offending value inside the instance as a `[]string` of member
names and array indices (empty for the instance root). `ErrorKind` is a typed
value from the `kind` package identifying the failed rule. `Causes` holds the
nested `*ValidationError` values that explain a composite failure. The root
error returned by `Validate` carries the `*kind.Schema` kind; leaf causes
carry the specific keyword kinds. One `Validate` call reports all violated
keywords, not only the first: an object missing two required members and
carrying a type violation produces causes for both.

**Error kinds.** Each keyword failure is represented by a dedicated struct in
package `kind`, asserted by type: `kind.Type` (fields `Got` string, `Want`
[]string), `kind.Enum`, `kind.Const`, `kind.Minimum`, `kind.Maximum`,
`kind.ExclusiveMinimum`, `kind.ExclusiveMaximum`, `kind.MultipleOf`,
`kind.MinLength`, `kind.MaxLength`, `kind.Pattern`, `kind.Required` (field
`Missing` []string listing exactly the absent members), `kind.MinProperties`,
`kind.MaxProperties`, `kind.DependentRequired`, `kind.MinItems`,
`kind.MaxItems`, `kind.UniqueItems`, `kind.Contains`, `kind.MinContains`,
`kind.MaxContains`, `kind.AdditionalProperties`, `kind.PropertyNames`,
`kind.AllOf`, `kind.AnyOf`, `kind.OneOf`, `kind.Not`, `kind.FalseSchema`,
`kind.Reference`, `kind.Schema`, and `kind.Group`.

**Flag output.** `FlagOutput()` returns `*FlagOutput` with a single `Valid`
bool field; on a `ValidationError` it is `false`. Its JSON form is
`{"valid":false}`.

**Basic and detailed output.** `BasicOutput()` and `DetailedOutput()` return
`*OutputUnit` trees. An `OutputUnit` has fields `Valid` (bool),
`KeywordLocation` (JSON Pointer from the validating schema root to the failed
keyword, e.g. `/properties/count/minimum`), `AbsoluteKeywordLocation` (set
when it differs informatively, e.g. across `$ref`), `InstanceLocation` (JSON
Pointer into the instance, e.g. `/count`, empty string for the root),
`Error` (the leaf's error value, absent on units that only group children),
and `Errors` (child units). The JSON member names are `valid`,
`keywordLocation`, `instanceLocation`, `error`, and `errors`. Basic output
flattens the tree: the root unit's `Errors` holds one unit per reported
failure, including group markers for composite keywords. Detailed output
preserves nesting: a composite failure such as `anyOf` appears as one child
unit whose own `Errors` holds the per-branch failures. Both projections
report `Valid: false` on the root for any failed validation, and both locate
the same leaf failures by the same `keywordLocation` and `instanceLocation`
values.

## State Model

The compiler owns mutable registration state: a map from absolute resource
URL to registered document, plus the compiled-root cache. `AddResource`
appends to it; `Compile` reads it, consults the loader for gaps, and installs
compiled roots into the cache. Compiled `Schema` values are immutable and
independent of later compiler mutations. Validation reads the compiled graph
and never mutates it, so one compiled `Schema` validates any number of
instances, and distinct instances validated against the same `Schema` cannot
influence one another. The public projections of one compilation are:
(1) the compiled `Schema` (identity, `Location`, `DraftVersion`, `Bool`);
(2) `Validate` results; (3) the output-format projections of a
`ValidationError`; (4) the typed compile-error values.

## Error Semantics

| Condition | Required result |
|-----------|-----------------|
| `AddResource` for a URL already registered on the compiler | `*ResourceExistsError` |
| `Compile` reaching a `$ref` anchor absent from the target resource | `*AnchorNotFoundError` |
| `Compile` of a document violating its dialect meta-schema | `*SchemaValidationError` |
| `Compile` needing a URL the active loader cannot load | `*LoadURLError` |
| `SchemeURLLoader.Load` called with a URL whose scheme has no entry | `*UnsupportedURLSchemeError` |
| `MustCompile` in any situation where `Compile` errors | panic |
| `Schema.Validate` on a non-conforming instance | `*ValidationError` |
| `Schema.Validate` on a conforming instance | nil |
| `UnmarshalJSON` on malformed input or trailing content | non-nil error |

All error structs above implement `error`. Assessments match error types
(via type assertion or `errors.As`), never message text.

## Cross-View Invariants

1. `Schema.Validate` returns nil exactly when the instance conforms; for any
   non-nil result, `FlagOutput().Valid`, `BasicOutput().Valid`, and
   `DetailedOutput().Valid` must all be `false`.
2. Every leaf cause in the `ValidationError` tree must appear in
   `BasicOutput().Errors` as a unit with `Valid: false` whose
   `InstanceLocation` is the JSON-Pointer encoding of the cause's
   `InstanceLocation` slice.
3. Compiling the same location twice on one compiler, or addressing one
   subschema through an anchor fragment and through its JSON-Pointer
   fragment, must return the identical `*Schema` pointer, and that pointer
   must validate identically however it was obtained.
4. An instance rejected by a directly compiled subschema must also be
   rejected when the same subschema is reached through `$ref` from another
   resource on the same compiler.
5. `MustCompile` must panic for exactly the locations where `Compile`
   returns an error, and return the identical `*Schema` for locations where
   `Compile` succeeds.
6. The rational-arithmetic equality used by `enum`/`const` and the one used
   by `uniqueItems` must agree: any pair of values equal for `const` is a
   duplicate for `uniqueItems`.
7. A document registered via `AddResource` and the same document served
   through a caller-registered `URLLoader` must compile to schemas with
   identical validation behavior.

## Public Interface

### Import Surface

```go
import (
    jsonschema "github.com/santhosh-tekuri/jsonschema/v6"
    "github.com/santhosh-tekuri/jsonschema/v6/kind"
)
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `NewCompiler` | function | Create an empty compiler |
| `Compiler` | struct | Registry of resources; compiles locations into schemas |
| `Compiler.AddResource` | method | Register a decoded schema document under a URL |
| `Compiler.Compile` | method | Resolve and compile a location into a `*Schema` |
| `Compiler.MustCompile` | method | `Compile` that panics on error |
| `Compiler.DefaultDraft` | method | Set the dialect used when `$schema` is absent |
| `Compiler.UseLoader` | method | Replace the loader for unregistered URLs |
| `UnmarshalJSON` | function | Decode one JSON document preserving number precision |
| `Schema` | struct | Compiled schema node; fields `Location`, `DraftVersion`, `Bool` |
| `Schema.Validate` | method | Validate one decoded instance |
| `Draft` | struct | Dialect descriptor |
| `Draft4`, `Draft6`, `Draft7`, `Draft2019`, `Draft2020` | variables | The supported dialects |
| `URLLoader` | interface | `Load(url string) (any, error)` |
| `FileLoader` | struct | Loader for `file://` URLs; also `ToFile` conversion |
| `SchemeURLLoader` | map type | Dispatch loader by URL scheme |
| `ValidationError` | struct | Failure tree: `SchemaURL`, `InstanceLocation`, `ErrorKind`, `Causes` |
| `ValidationError.FlagOutput` | method | Project to `*FlagOutput` |
| `ValidationError.BasicOutput` | method | Project to flat `*OutputUnit` list |
| `ValidationError.DetailedOutput` | method | Project to hierarchical `*OutputUnit` tree |
| `FlagOutput` | struct | `Valid` bool |
| `OutputUnit` | struct | `Valid`, `KeywordLocation`, `AbsoluteKeywordLocation`, `InstanceLocation`, `Error`, `Errors` |
| `OutputError` | struct | JSON-marshalable leaf error carrier inside `OutputUnit` |
| `ResourceExistsError` | error struct | Duplicate `AddResource` URL |
| `AnchorNotFoundError` | error struct | `$ref` anchor missing from target resource |
| `SchemaValidationError` | error struct | Document fails its meta-schema |
| `LoadURLError` | error struct | Loader failure for a URL |
| `UnsupportedURLSchemeError` | error struct | Scheme without a registered loader |
| `kind.Schema`, `kind.Group`, `kind.Reference` | error-kind structs | Structural kinds on non-leaf errors |
| `kind.Type`, `kind.Enum`, `kind.Const` | error-kind structs | Type and value-set violations |
| `kind.Minimum`, `kind.Maximum`, `kind.ExclusiveMinimum`, `kind.ExclusiveMaximum`, `kind.MultipleOf` | error-kind structs | Numeric violations |
| `kind.MinLength`, `kind.MaxLength`, `kind.Pattern` | error-kind structs | String violations |
| `kind.Required`, `kind.MinProperties`, `kind.MaxProperties`, `kind.DependentRequired`, `kind.AdditionalProperties`, `kind.PropertyNames` | error-kind structs | Object violations |
| `kind.MinItems`, `kind.MaxItems`, `kind.UniqueItems`, `kind.Contains`, `kind.MinContains`, `kind.MaxContains` | error-kind structs | Array violations |
| `kind.AllOf`, `kind.AnyOf`, `kind.OneOf`, `kind.Not`, `kind.FalseSchema` | error-kind structs | Composition violations |

### CLI Entry Points

There is no console command in this module's assessed surface. Programmatic
use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.22 or newer on Linux. Module dependencies
declared in `go.mod` are downloaded once during environment preparation;
tests then run without network access. The permitted third-party dependency
is `golang.org/x/text` (used by the localization surface, which is not
assessed); everything else must come from the Go standard library.

The project must declare `module github.com/santhosh-tekuri/jsonschema/v6`
in a `go.mod` at the project root so the package resolves through a module
`replace` directive, with the `jsonschema` package at the module root and
the `kind` package in the `kind/` subdirectory.

## Appendix B: Assessment Notes

Assessment exercises the public API only, in two dimensions: single-behavior
checks (one keyword, one compiler operation, or one error condition at a
time) and cross-component checks (reference graphs spanning resources,
agreement between the error tree and the output formats, dialect interop,
and loader participation in compilation). Expected values are structured —
error types, kind types and their declared fields, output-unit locations,
boolean validity — never message wording. Schemas and instances used in
checks are built from the documented value model; no fixture files are
involved.
