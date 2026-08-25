# go-yaml Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`go-yaml` is a YAML processing engine for Go programs. It decodes YAML
documents into Go values, encodes Go values back into YAML text, and exposes
the intermediate representations — a token stream and a typed syntax tree —
as first-class public surfaces. One document model underlies every feature:
bytes are tokenized with full position information, tokens are parsed into a
syntax tree, and the tree is mapped onto Go values under YAML 1.2 typing
rules extended with engine-specific conventions for struct tags, anchors,
comments, and ordered maps.

Beyond plain decode and encode, the engine answers structured queries
against documents through a path language (`$.store.book[0].author`),
associates comments with the values they annotate so that a decode → encode
round trip preserves them, converts documents between YAML and JSON, and
reports every failure as a source-annotated error that points at the exact
line and column with a caret under the offending token. The installable
module path is `github.com/goccy/go-yaml`.

## Non-Goals

- This specification does not require a streaming (SAX-style) event API;
  documents are processed whole.
- This specification does not define network access, file-watching, or
  schema validation beyond the pluggable struct-validator hook described
  in Custom Hooks.
- This specification does not require resolving anchors that live in other
  files or directories; every alias resolves within its own document
  stream.
- This specification does not define a token- or tree-printing package;
  the only rendering surfaces are node `String` output, encoder output,
  and the annotated source excerpts embedded in errors and produced by
  path annotation.
- This specification does not require context-carrying variants of the
  encode, decode, or hook-registration entry points.
- This specification does not define automatic anchor generation from
  shared pointers, an anchor-emission callback, or field-prefix matching
  options.
- This specification does not require YAML 1.1 boolean spellings (`yes`,
  `on`, `y`) to decode as booleans; they decode as strings.

## Representative Workflows

The engine's features compose into pipelines. Two canonical workflows:

**Workflow 1: configuration loading with strict fields and validation.**
A service loads a config file into a tagged struct. Unknown keys must be
rejected, a validator checks field constraints, and any failure must print
an annotated excerpt of the offending source.

```go
type Server struct {
    Host string `yaml:"host"`
    Port int    `yaml:"port"`
}

var cfg Server
err := yaml.UnmarshalWithOptions(src, &cfg,
    yaml.DisallowUnknownField(),
    yaml.Validator(v), // any StructValidator implementation
)
if err != nil {
    // err.Error() begins with "[line:col] message" and includes a
    // source excerpt with a caret under the offending token
    fmt.Println(yaml.FormatError(err, false, true))
}
```

**Workflow 2: surgical document rewrite that preserves comments.**
A tool reads a YAML file, replaces one deeply nested value addressed by a
path, merges an extra mapping into a subtree, and writes the document back
without disturbing comments elsewhere.

```go
file, _ := parser.ParseBytes(src, parser.ParseComments)

p, _ := yaml.PathString("$.store.bicycle.color")
_ = p.ReplaceWithReader(file, strings.NewReader("blue"))

m, _ := yaml.PathString("$.store.bicycle")
_ = m.MergeFromReader(file, strings.NewReader("brand: acme"))

out := file.String() // rest of the document byte-identical, comments intact
```

A third recurring pattern chains decode and encode with a `CommentMap` to
carry comments across a value-level transformation; Comment Association
describes it.

## Decoding into Go Values

Decoding maps a YAML document onto a caller-supplied Go destination. The
entry points are `yaml.Unmarshal` (bytes and a destination pointer),
`yaml.UnmarshalWithOptions` (same plus decode options), and `yaml.NewDecoder`
over an `io.Reader` with its `Decode` method; `NewDecoder` accepts the same
options at construction. Every decode failure returns a source-annotated
error as defined in Error Semantics.

**Scalar typing into untyped destinations.** When the destination is
`interface{}` or a `map[string]interface{}` value slot, scalars resolve by
YAML 1.2 core-schema rules with the following engine-specific outcomes:

- Integer literals without a sign — including hexadecimal `0x…`, octal
  `0o…`, binary `0b…`, and underscore-separated forms like `1_000` —
  must decode as `uint64`. Negative integer literals must decode as
  `int64`.
- Floating literals containing a decimal point (including underscore
  separated and exponent forms such as `1.5e3`) must decode as `float64`.
  An exponent form without a decimal point, such as `1e3`, must decode as
  a string; when the destination is a typed numeric field the same
  literal must convert to that numeric type.
- `.inf`, `.Inf`, and `-.inf` must decode as the positive and negative
  infinities; `.nan` and `.NaN` must decode as a floating NaN. The form
  `+.inf` is not an infinity spelling and must decode as a string.
- `true` and `True` must decode as booleans. The YAML 1.1 spellings
  `yes`, `no`, `on`, `off`, `y`, and `n` must decode as strings.
- `null`, `~`, and an empty value must decode as an untyped nil.
- Quoted scalars must always decode as strings regardless of content.
- Date-like unquoted scalars such as `2024-01-15` must decode as strings
  when the destination is untyped.

Mappings decoded into an untyped destination must produce
`map[string]interface{}` at every nesting level, and sequences must produce
`[]interface{}`.

**Struct destinations and field matching.** The struct tag key is `yaml`
(the exported constant `StructTagName`). A tag's first comma-separated
element names the key; without a tag the key defaults to the field name
lowercased in full (field `Count` maps to key `count`, field `FooBar` to
`foobar`). When a field has no `yaml` tag but has a `json` tag, the `json`
tag's name must be used. Matching is exact and case-sensitive against the
derived key: a document key `FooBar` must not populate an untagged field
`FooBar` (whose derived key is `foobar`), and unmatched document keys are
ignored without error by default. A tag value of `-` excludes the field.
The tag option `inline` on an embedded or named struct field must splice
the inner struct's keys into the parent mapping namespace for both decode
and encode.

**Decode options.** `DisallowUnknownField()` makes a document key that
matches no destination field an error; `Strict()` must behave identically
to `DisallowUnknownField()`. `AllowDuplicateMapKey()` lifts the default
duplicate-key rejection so that the last occurrence wins.
`UseOrderedMap()` changes the untyped mapping representation from
`map[string]interface{}` to `yaml.MapSlice`, preserving document order.
`UseJSONUnmarshaler()` lets destination types that implement
`json.Unmarshaler` participate in decoding. `CommentToMap(cm)` collects
comments as described in Comment Association. `Validator(v)` and
`CustomUnmarshaler[T](fn)` are described in Custom Hooks.

**Ordered maps.** `yaml.MapSlice` is a slice of `yaml.MapItem`, each
holding a `Key` and a `Value` (both untyped). Decoding with
`UseOrderedMap()` must yield `MapSlice` values whose item order equals
document order, `MapSlice.ToMap()` must project the slice to a
`map[interface{}]interface{}`, and encoding a `MapSlice` must emit keys in
slice order rather than sorted order.

**Raw subtrees.** A field of type `yaml.RawMessage` must capture the raw
YAML text of its value — exactly the source bytes of the subtree — on
decode, and must splice its content verbatim (re-indented to the insertion
point) on encode.

**Multiple documents.** A stream containing `---` separators holds several
documents. A `Decoder` must return one document per `Decode` call, in
order, and must return `io.EOF` after the final document.

**Decoding through the tree.** `yaml.NodeToValue(node, dst, opts...)`
must decode any syntax-tree node into a destination exactly as if the
node's text had been passed to `UnmarshalWithOptions` with the same
options, and `Decoder.DecodeFromNode(node, dst)` must do the same on a
constructed decoder. Both must accept nodes obtained from parsing or from
`ValueToNode`.

## Anchors, Aliases, and Merge Keys

Anchor resolution is a reference graph inside the document: an anchor
definition (`&name`) registers a node, and every alias (`*name`) resolves
to the registered node's value.

**Resolution.** When a document defines `a: &x <value>` and later uses
`b: *x`, both keys must decode to equal values. When the anchored value is
a mapping or sequence and the destination is untyped, the alias and the
anchor must decode to the same shared Go value, not an independent copy:
mutating the map decoded for `a` must be observable through the value
decoded for `b`.

**Failure path.** If an alias names an anchor that no preceding node in
the document defined, then decode must fail with a source-annotated error
whose message contains `could not find alias` and the quoted alias name.

**Merge keys.** The merge key `<<: *anchor` inside a mapping must splice
the anchored mapping's entries into the host mapping; entries defined
explicitly in the host mapping must win over merged entries with the same
key. Merge keys must also resolve during YAML-to-JSON conversion.

**Encoding anchors.** The struct tag option `anchor` (as in
`yaml:"p,anchor"`) must emit the field's value with an anchor named after
the tag name (or `anchor=name` for an explicit name), and the tag option
`alias` (or `alias=name`) on another field holding the same pointer must
emit an alias reference instead of repeating the value. The emitted
document must decode back to shared values as described above.

## Encoding from Go Values

Encoding renders a Go value as YAML text. The entry points are
`yaml.Marshal`, `yaml.MarshalWithOptions`, and `yaml.NewEncoder` over an
`io.Writer` with `Encode` and `Close`; encode options apply to all three.
The default indentation is two spaces (the exported constant
`DefaultIndentSpaces`).

**Key derivation and ordering.** Struct fields encode under the same
derived keys used for decoding (tag name, `json`-tag fallback, else
lowercased field name). Go map keys must be emitted in sorted order;
`MapSlice` keys must be emitted in slice order. Nil values (untyped nil or
nil pointer) must encode as `null`.

**Quoting rules.** A string scalar must be double-quoted exactly when its
plain rendering would read as something other than that string, in these
families: spellings of other scalar types — `null`, `~`, integer literal
forms including signed and hexadecimal (`123`, `-3`, `0x1F`), and float
literal forms containing a decimal point (`1.5`) — and the boolean-like
words `y`, `n`, `yes`, `no`, `on`, `off`, `true`, `false` in their
lowercase, Title-case, and all-uppercase spellings (mixed casings such as
`yEs` are not boolean-like and must stay unquoted); strings that begin a
YAML construct (`a: b` with a colon-space, a leading `- `, or a leading
`#`, `%`, `&`, `*`, `!`, `|`, `>`, `[`, `{`, `@`, `` ` ``, `"`, or `'`);
empty strings; and strings with leading or trailing spaces. An exponent
form without a decimal point such as `1e3` reads as a string to the
decoder and must stay unquoted. Other plain strings, including strings
with interior spaces, version-like forms (`v1.2`, `3.0.1`), and non-ASCII
text, must be emitted unquoted. With `UseSingleQuote(true)` quoting must
use single quotes instead. A string containing newlines must be emitted
as a literal block scalar (`|` when the string ends with a newline, `|-`
when it does not) rather than a quoted scalar.

**Styles and layout options.** `Flow(true)` must render mappings and
sequences in flow style (`{a: [1, 2]}`). `JSON()` must produce valid JSON
output (quoted keys and strings, flow collections). `Indent(n)` sets the
indent width. `IndentSequence(true)` must indent block-sequence dashes one
level under their key; without it dashes align flush with the parent key
column. `UseLiteralStyleIfMultiline(true)` forces literal blocks for
multiline strings even where quoting would otherwise apply.

**Value shaping options.** `AutoInt()` must render a float with an
integral value as an integer (`3.0` encodes as `3`, `3.5` stays `3.5`).
`OmitEmpty()` and `OmitZero()` must drop struct fields holding empty
(respectively zero) values from the output document as if every field
carried the corresponding tag option; a struct whose fields are all
dropped must encode as `{}`. The per-field tag options `omitempty` and
`omitzero` have the same meaning field-locally.

**Multiple documents.** Consecutive `Encode` calls on one `Encoder` must
separate documents with a `---` line, and `Close` must flush the stream.

**Value-to-tree.** `yaml.ValueToNode(v, opts...)` must build a syntax-tree
node rendering identically to `Marshal` output for the same value and
options, usable wherever nodes are accepted (path replacement, merging,
`NodeToValue`).

## Comment Association

Comments attach to values through a `yaml.CommentMap`, keyed by the path
of the annotated value in the same `$.` syntax used by path queries.

**Collecting.** Decoding with `CommentToMap(cm)` must populate `cm` with
one entry per commented node. A comment on the line(s) above a value maps
to a `Comment` with position `Head`; a comment on the same line after a
value maps to position `Line`. Comment text preserves everything after the
`#`, including the leading space. Nested values key by their full path
(`$.b.c` for key `c` inside mapping `b`).

**Emitting.** Encoding with `WithComment(cm)` must render head comments on
their own line(s) immediately above the annotated value and line comments
after the value on the same line. The constructors `HeadComment(texts...)`,
`LineComment(text)`, and `FootComment(texts...)` build `Comment` values;
`CommentPosition` exposes the position kind of a collected comment.

**Round trip.** For a document whose comments sit in head or line
position, decode with `CommentToMap` followed by encode with `WithComment`
of the same map must reproduce every comment at its original position.

## Path Queries

A `yaml.Path` addresses one node in a document with a JSONPath-like
string: `$` is the document root, `.name` descends into a mapping key, and
`[n]` indexes a sequence (zero-based). `yaml.PathString(s)` parses the
string form; a `yaml.PathBuilder` builds the same paths programmatically
via `Root()`, `Child(name)`, and `Index(n)` followed by `Build()`, and a
built path's `String()` must render the canonical string form.

**Reading.** `Path.Read(io.Reader, dst)` must decode the addressed node
into the destination under normal decoding rules. `Path.ReadNode(reader)`
must return the addressed syntax-tree node. `Path.Filter(source, dst)`
must project a plain Go value (previously decoded or constructed) instead
of a document, and `Path.FilterFile(file)` / `Path.FilterNode(node)` must
address into an already-parsed tree.

**Rewriting.** `Path.ReplaceWithReader(file, src)` must replace the
addressed node inside a parsed file with the content read from `src`,
leaving every other byte of the rendered document unchanged.
`Path.ReplaceWithFile` and `Path.ReplaceWithNode` accept already-parsed
replacements. `Path.MergeFromReader(dst, src)` must merge a mapping or
sequence into the addressed node (appending new keys after existing ones);
`MergeFromFile` and `MergeFromNode` are the parsed-input forms.

**Annotation.** `Path.AnnotateSource(source, colored)` must return the
source bytes rendered as a numbered excerpt with a caret marking the
addressed node — the same rendering style errors use — with ANSI colors
exactly when `colored` is true.

**Failure paths.** If a path string is malformed, then `PathString` must
return an error satisfying `yaml.IsInvalidPathStringError`. If a
syntactically valid path addresses a node absent from the document, then
read and filter operations must return an error satisfying
`yaml.IsNotFoundNodeError`. Both checks must also hold through
`errors.Is`-style wrapped chains.

## Syntax Tree and Tokens

The token stream and the syntax tree are public projections of the same
parse.

**Tokenizing.** `lexer.Tokenize(src)` must return the ordered
`token.Tokens` for the source. Every `token.Token` carries `Type`,
`Value` (the cleaned scalar text), `Origin` (the exact source text
including surrounding whitespace and newlines, so that concatenating all
origins reproduces the input), and `Position` with 1-based `Line` and
`Column`, byte `Offset`, and `IndentNum`. Structural tokens report types
such as `MappingValue` for `:`, `SequenceStart` for `[`, `CollectEntry`
for `,`, and `SequenceEnd` for `]`; scalar tokens report their resolved
kind (`String`, `Integer`, `Bool`, `Comment`, and the other scalar kinds).

**Parsing.** `parser.ParseBytes(src, mode, opts...)` must return an
`*ast.File` holding one `DocumentNode` per document in the stream (a
`---` header starts a new document). `parser.Parse` accepts an existing
token stream, and `parser.ParseFile` reads a file by name. The mode flag
`parser.ParseComments` must preserve comments as tree nodes; without it
comments are dropped from the tree. The parser option
`parser.AllowDuplicateMapKey()` must lift the duplicate-key parse error.

**Nodes.** Every node implements `ast.Node`, whose `Type()` returns an
`ast.NodeType` (mappings report `Mapping`, documents `Document`, and the
node-kind names follow the YAML construct they represent), `String()`
renders the node as YAML text, and `GetToken()` exposes the underlying
token with its position. `File.String()` must render the whole stream,
reproducing `---` separators. Rendering a file parsed with
`ParseComments` must include the comments. `ast.Walk(visitor, node)` must
visit the subtree, calling the visitor's `Visit` on each node and
descending only while the returned visitor is non-nil. `ast.Merge(dst,
src)` must merge mapping nodes at the tree level.

**Tree/value agreement.** For any document, decoding the parsed tree with
`NodeToValue` must equal decoding the source bytes directly, and a
`ValueToNode` result must render (via `String()`) exactly as `Marshal`
renders the same value.

## Format Conversion

Two converters translate whole documents between YAML and JSON without an
intermediate caller-visible value.

**YAML to JSON.** `yaml.YAMLToJSON(bytes)` must convert a YAML document to
JSON bytes, resolving anchors, aliases, and merge keys before conversion,
rendering mappings as JSON objects in document key order and scalars under
their decoded types.

**JSON to YAML.** `yaml.JSONToYAML(bytes)` must convert JSON to YAML block
style. If the input to either converter fails to parse, then the converter
must return a source-annotated error. Converting a document with
`YAMLToJSON` and feeding the result to `JSONToYAML` must produce a
document that decodes to the same value as the original.

## Custom Hooks

The engine dispatches to caller-supplied logic at well-defined points.

**Marshaling interfaces.** A type implementing `MarshalYAML() ([]byte,
error)` (the `yaml.BytesMarshaler` interface) must be encoded by splicing
the returned bytes at the value's position. A type implementing
`MarshalYAML() (interface{}, error)` (`yaml.InterfaceMarshaler`) must be
encoded by encoding the returned value in its place.

**Unmarshaling interfaces.** A type implementing `UnmarshalYAML([]byte)
error` (`yaml.BytesUnmarshaler`) must receive the raw YAML text of its
value. A type implementing `UnmarshalYAML(func(interface{}) error) error`
(`yaml.InterfaceUnmarshaler`) must receive a decode function that fills a
destination from the value. A type implementing `UnmarshalYAML(ast.Node)
error` (`yaml.NodeUnmarshaler`) must receive the value's syntax-tree node.

**Registration.** `yaml.RegisterCustomMarshaler[T](fn)` and
`yaml.RegisterCustomUnmarshaler[T](fn)` install process-global hooks for
type `T`; the options `CustomMarshaler[T](fn)` (encode) and
`CustomUnmarshaler[T](fn)` (decode) install the same hooks for a single
call and must take precedence over the global registration for that call.
Marshaler hooks return the bytes to splice; unmarshaler hooks receive the
destination pointer and the raw value bytes.

**Validation.** `Validator(v)` accepts any `yaml.StructValidator` — a
type with a `Struct(interface{}) error` method, invoked with each decoded
struct value. If the validator returns an error, then decoding must fail
with that error; when the error implements `yaml.FieldError` (a
`StructField() string` method) and the offending field is present in the
source, the failure must be source-annotated at that field.

**JSON interop.** `UseJSONMarshaler()` (encode) and `UseJSONUnmarshaler()`
(decode) must let types implementing the standard-library
`json.Marshaler` / `json.Unmarshaler` interfaces participate as if they
implemented the YAML interfaces.

## State Model

The engine's state is the document model at four public granularities:
source bytes, token stream, syntax tree, and Go values. Every public
surface is a projection of one of these:

1. **Bytes → tokens** (`lexer.Tokenize`): loss-free; token origins
   concatenate back to the source.
2. **Tokens → tree** (`parser.Parse*`): positions survive on every node's
   token; comments survive when parsed with `ParseComments`.
3. **Tree → values** (`Unmarshal`, `NodeToValue`, `Path.Read`): applies
   typing rules, struct-tag mapping, anchor resolution; alias nodes
   resolve to shared values.
4. **Values → text/tree** (`Marshal`, `ValueToNode`, `Encoder`): applies
   key derivation, ordering, and quoting rules.

Decoders and encoders are stateful only in stream position (documents
consumed or emitted so far) and configured options; parsed files own their
tree, and path rewrite operations mutate that tree in place. Global
marshaler registrations are process-wide. Everything else is pure: the
same input and options must produce the same output on every call.

## Error Semantics

Every decode-side failure is source-annotated: the message begins with
`[line:column]` (1-based) followed by the description, and — through
`yaml.FormatError(err, colored, inclSource)` with `inclSource` true, and
in the default `Error()` text — includes a numbered source excerpt with a
`^` caret under the offending token and a `>` marker on its line. Colors
appear exactly when `colored` is true.

| Condition | Result |
|---|---|
| Malformed YAML (unclosed flow sequence, bad structure) | error satisfying `errors.As` with `*yaml.SyntaxError`; carries the offending `Token` and a `Message` |
| Duplicate mapping key (default options) | source-annotated error whose message names the key and the position of the earlier definition (`mapping key "a" already defined at [1:1]`) |
| Alias to an undefined anchor | source-annotated error containing `could not find alias "name"` |
| Document key with no matching struct field under `DisallowUnknownField()`/`Strict()` | error satisfying `errors.As` with `*yaml.UnknownFieldError`, message `unknown field "key"` |
| Scalar that does not convert to the destination field type | error satisfying `errors.As` with `*yaml.TypeError`; carries `DstType`, `SrcType`, `StructFieldName`, and the offending `Token`; message `cannot unmarshal <src> into Go struct field <name> of type <dst>` |
| Integer literal exceeding the destination integer type's range | error satisfying `errors.As` with `*yaml.OverflowError` |
| Malformed path string | error from `PathString` satisfying `yaml.IsInvalidPathStringError` |
| Valid path addressing an absent node | error satisfying `yaml.IsNotFoundNodeError` |
| Validator rejection | the validator's error; source-annotated at the field when it implements `yaml.FieldError` and the field is present |
| `Decode` after the last document | `io.EOF` |

`yaml.Error` is the interface every engine error satisfies through
`errors.As`. `yaml.FieldError`, `yaml.StructValidator`, and the typed
errors above are exported for callers to match on.

## Cross-View Invariants

1. **Token origins reproduce the source.** For any input accepted by
   `lexer.Tokenize`, concatenating every token's `Origin` in order must
   reproduce the input bytes exactly; each token's `Position` (`Line`,
   `Column`, `Offset`) must agree with the location of its origin text in
   those bytes.
2. **Tree rendering agrees with the encoder.** For any Go value,
   `ValueToNode(v).String()` must equal the text `Marshal(v)` produces
   (up to the trailing newline), and parsing that text back must yield a
   tree whose `NodeToValue` decode equals the value `Unmarshal` produces
   from the same text.
3. **Decode/encode round trip is stable for untyped data.** For any
   document decoded into untyped destinations with `UseOrderedMap()`,
   re-encoding the result must produce a document that decodes to the
   same value with keys in the same order.
4. **Path reads agree with full decodes.** For any document and any path
   built solely from mapping keys and sequence indexes present in it,
   `Path.Read` must produce the same value that a full `Unmarshal`
   followed by navigation along the same keys and indexes produces, and
   `Path.ReadNode(...).String()` must render the same subtree the parsed
   file exposes at that address via `FilterFile`.
5. **Rewrites are local.** After `ReplaceWithReader` on a parsed file,
   the rendered document must differ from the original rendering only at
   the addressed node's text, and re-reading the same path must return
   the replacement value; after `MergeFromReader` of a mapping, every
   pre-existing key must remain readable at its original path.
6. **Comments survive the value round trip.** For a document with head
   and line comments, `CommentToMap` decode followed by `WithComment`
   encode of the unchanged value must emit every comment with its
   original position and text, and the emitted document must decode to
   the same value as the original.
7. **Conversion agrees with decoding.** `YAMLToJSON` output parsed as
   JSON must equal the value produced by decoding the YAML directly
   (with anchors, aliases, and merge keys resolved), and
   `JSONToYAML(YAMLToJSON(doc))` must decode to that same value.
8. **Errors point into the real source.** For any decode failure, the
   `[line:column]` in the message and the caret line in
   `FormatError(err, false, true)` must locate the offending token in
   the original input — the line number shown beside the caret must be
   the line the token occupies in the input bytes.

## Public Interface

### Import Surface

```go
import (
    "github.com/goccy/go-yaml"        // package yaml
    "github.com/goccy/go-yaml/ast"    // package ast
    "github.com/goccy/go-yaml/lexer"  // package lexer
    "github.com/goccy/go-yaml/parser" // package parser
    "github.com/goccy/go-yaml/token"  // package token
)
```

### API Catalog — yaml

| Name | Kind | Role |
|---|---|---|
| `Marshal`, `MarshalWithOptions` | functions | encode a Go value to YAML bytes |
| `Unmarshal`, `UnmarshalWithOptions` | functions | decode YAML bytes into a destination |
| `NewEncoder`, `Encoder` | function/type | streaming multi-document encoder (`Encode`, `Close`) |
| `NewDecoder`, `Decoder` | function/type | streaming multi-document decoder (`Decode`, `DecodeFromNode`) |
| `NodeToValue` | function | decode a syntax-tree node into a destination |
| `ValueToNode` | function | build a syntax-tree node from a Go value |
| `YAMLToJSON`, `JSONToYAML` | functions | format converters |
| `FormatError` | function | render an error with optional color and source excerpt |
| `PathString`, `Path` | function/type | parse and evaluate document paths (`Read`, `ReadNode`, `Filter`, `FilterFile`, `FilterNode`, `ReplaceWithReader`, `ReplaceWithFile`, `ReplaceWithNode`, `MergeFromReader`, `MergeFromFile`, `MergeFromNode`, `AnnotateSource`, `String`) |
| `PathBuilder` | type | build paths programmatically (`Root`, `Child`, `Index`, `Build`) |
| `CommentMap`, `Comment`, `CommentPosition` | types | comment association model |
| `HeadComment`, `LineComment`, `FootComment` | functions | comment constructors |
| `MapSlice`, `MapItem` | types | order-preserving mapping representation (`ToMap`) |
| `RawMessage` | type | raw YAML subtree carrier |
| `StructTagName`, `DefaultIndentSpaces` | constants | struct tag key; default indent width |
| `AllowDuplicateMapKey`, `DisallowUnknownField`, `Strict`, `UseOrderedMap`, `UseJSONUnmarshaler`, `CommentToMap`, `Validator`, `CustomUnmarshaler` | functions | decode options |
| `Flow`, `Indent`, `IndentSequence`, `JSON`, `AutoInt`, `OmitEmpty`, `OmitZero`, `UseSingleQuote`, `UseLiteralStyleIfMultiline`, `UseJSONMarshaler`, `WithComment`, `CustomMarshaler` | functions | encode options |
| `DecodeOption`, `EncodeOption` | types | option function types |
| `RegisterCustomMarshaler`, `RegisterCustomUnmarshaler` | functions | process-global type hooks |
| `BytesMarshaler`, `InterfaceMarshaler`, `BytesUnmarshaler`, `InterfaceUnmarshaler`, `NodeUnmarshaler` | interfaces | marshaling hook contracts |
| `StructValidator`, `FieldError` | interfaces | validation hook contracts |
| `Error`, `SyntaxError`, `TypeError`, `UnknownFieldError`, `OverflowError` | types | matchable error kinds |
| `IsInvalidPathStringError`, `IsNotFoundNodeError` | functions | path error predicates |

### API Catalog — parser

| Name | Kind | Role |
|---|---|---|
| `ParseBytes`, `Parse`, `ParseFile` | functions | parse source, tokens, or a named file into a tree |
| `Mode`, `ParseComments` | type/constant | parse mode flags |
| `Option`, `AllowDuplicateMapKey` | type/function | parser options |

### API Catalog — ast

| Name | Kind | Role |
|---|---|---|
| `Node` | interface | tree node (`Type`, `String`, `GetToken`) |
| `NodeType` | type | node kind enumeration (`String()` names the kind) |
| `File`, `DocumentNode` | types | parsed stream and per-document nodes |
| `MappingNode`, `MappingValueNode`, `SequenceNode`, `StringNode`, `IntegerNode`, `FloatNode`, `BoolNode`, `NullNode`, `AnchorNode`, `AliasNode`, `CommentGroupNode` | types | concrete node kinds |
| `Walk`, `Visitor` | function/interface | subtree traversal |
| `Merge` | function | tree-level mapping merge |

### API Catalog — lexer

| Name | Kind | Role |
|---|---|---|
| `Tokenize` | function | produce the token stream for source text |

### API Catalog — token

| Name | Kind | Role |
|---|---|---|
| `Token`, `Tokens` | types | token with `Type`, `Value`, `Origin`, `Position` |
| `Position` | type | 1-based `Line`/`Column`, byte `Offset`, `IndentNum` |
| `Type` | type | token kind enumeration |

### CLI Entry Points

There is no console script for this module. Programmatic use is through
Go imports.

## Appendix A: Environment

The working environment runs Go 1.21 or newer on Linux without network
access. The module under construction must declare the module path
`github.com/goccy/go-yaml` in its `go.mod`. No third-party dependencies
are required; the standard library suffices. The assessment environment
provides the same toolchain and compiles the module with standard `go
test` tooling against packages that import the module path above.

## Appendix B: Assessment Notes

Assessment exercises the public behaviors in this document at two
granularities. Unit-level checks target one surface at a time: scalar
typing outcomes, struct-tag mapping, quoting decisions, comment
collection, token fields and positions, node rendering, path parsing, and
each error family in Error Semantics with `errors.As` matching and
message shape. Integration-level checks compose surfaces: decode → encode
round trips with ordered maps and comments, path rewrites verified
through re-parsing and re-reading, tree/value agreement between
`NodeToValue`/`ValueToNode` and `Unmarshal`/`Marshal`, converter
round trips, anchor sharing observed through decoded values, and the
Cross-View Invariants above. Tests bind to observable results — returned
values, rendered text, error text and types — never to internal state.
Scoring is per test; each behavior family carries multiple independent
tests.
