# participle Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`participle` is a parser-builder library for Go. A grammar is expressed as a
tree of tagged Go struct types: each struct is one production, each field's
tag holds a grammar fragment, and parsing populates the structs directly, so
the grammar and the abstract syntax tree are the same declaration. From one
grammar definition the library derives several projections that must stay
consistent with each other: a compiled parser that recognises input and
captures values into fields, an EBNF rendering of the accepted language, a
family of build-time grammar errors, and parse-time errors that carry source
positions.

Lexing is pluggable. A default lexer tokenises Go-like source text with no
configuration; a simple lexer is built from an ordered list of named regular
expression rules; a stateful lexer generalises this to named rule-sets with
push/pop transitions for context-sensitive input such as string
interpolation. The parser consumes any of these through one lexer-definition
interface, and options control token-level transformations (eliding,
unquoting, case-insensitive literal matching, arbitrary token mapping) as
well as branch lookahead.

Internally the parser is recursive-descent with backtracking. Grammars must
therefore not be left-recursive; left recursion is detected and rejected when
the parser is built.

The installable module path is `github.com/alecthomas/participle/v2`; the
grammar/parser package import path is `github.com/alecthomas/participle/v2`
and the lexer package import path is
`github.com/alecthomas/participle/v2/lexer`.

## Non-Goals

- This specification does not cover the standalone `ebnf` subpackage, code
  generation for lexers, railroad-diagram tooling, or any command-line
  programs.
- This specification does not define the output written by the `Trace` parse
  option; only that the option exists and does not alter parse results.
- This specification does not define backreference support inside stateful
  lexer patterns, checkpoint/rewind methods of `PeekingLexer` beyond those
  listed in the API catalog, or the `BytesDefinition`/`StringDefinition`
  fast-path interfaces.
- This specification does not require production-grade performance.
- This specification does not define a stable order for the key set of
  `Symbols()` maps; only the name-to-type associations are contractual.
- This specification does not require a console interface of any kind.

## Representative Workflows

**Defining a grammar and parsing into it.** The struct declaration is the
grammar; parse results arrive as populated structs.

```go
type Property struct {
    Key   string `@Ident "="`
    Value string `@String`
}

type INI struct {
    Properties []Property `@@*`
}

parser := participle.MustBuild[INI](participle.Unquote())
ast, err := parser.ParseString("config.ini", `size = "10"`)
// ast.Properties[0] == Property{Key: "size", Value: "10"}
fmt.Println(parser.String())
// INI = Property* .
// Property = <ident> "=" <string> .
```

**A stateful lexer for interpolated strings.** Rule-sets are pushed and
popped as the lexer crosses context boundaries.

```go
def := lexer.MustStateful(lexer.Rules{
    "Root": {
        {Name: "String", Pattern: `"`, Action: lexer.Push("String")},
        {Name: "Ident", Pattern: `\w+`},
        {Name: "WS", Pattern: `\s+`},
    },
    "String": {
        {Name: "Expr", Pattern: `\${`, Action: lexer.Push("Expr")},
        {Name: "StringEnd", Pattern: `"`, Action: lexer.Pop()},
        {Name: "Chars", Pattern: `[^"$]+`},
    },
    "Expr": {
        {Name: "ExprEnd", Pattern: `}`, Action: lexer.Pop()},
        lexer.Include("Root"),
    },
})
// Tokens for `"a${b}c"` arrive as String, Chars("a"), Expr, Ident("b"),
// ExprEnd, Chars("c"), StringEnd.
```

## Grammar Definition Language

This section defines the tag mini-language that grammar structs are written
in. Every struct type reachable from the root grammar type is one production;
its fields are matched in declaration order.

**Tag selection.** When a struct field carries a tag in the form
`parser:"..."`, the parser must use that tag value as the field's grammar
fragment. When no `parser:` key is present, the entire raw tag body must be
used as the fragment. Inside a `parser:"..."` tag, the fragment language
must accept single quotes in place of double quotes for literals.

**Expression forms.** The fragment language must support these forms:

- `<identifier>` — match one token of the named lexer token type, without
  capturing it.
- `"..."` (or `'...'`) — match one token whose value equals the literal
  exactly.
- `"...":<identifier>` — match one token whose value equals the literal and
  whose type is the named token type. If the named type does not exist in
  the lexer, then `Build` must fail with an error identifying the unknown
  token type in a literal type constraint.
- `@<expr>` — match `<expr>` and capture the matched token values into the
  field (see Value Capture).
- `@@` — recursively match the field's own struct (or union/custom) type as
  a sub-production and capture the result into the field.
- `<expr> <expr> ...` — sequence; each element must match in order.
- `<expr> | <expr> | ...` — alternation; alternatives are tried in order and
  the first match wins.
- `( ... )` — grouping.
- `~<expr>` — negation: match any single token that is not the start of
  `<expr>`.
- `(?= ... )` — positive lookahead: require the contents to match upcoming
  input without consuming any of it.
- `(?! ... )` — negative lookahead: require the contents not to match
  upcoming input, consuming nothing.

**Modifiers.** The fragment language must support four postfix modifiers on
any expression: `*` (zero or more), `+` (one or more), `?` (zero or one),
and `!` (the expression must consume at least one token). If a `!`-marked expression matches without consuming any
tokens, then parsing must fail with an error whose message states that the
sub-expression cannot be empty.

**Well-formedness.** If a tag fragment is syntactically malformed (for
example an unclosed group), then `Build` must fail with an error naming the
offending field. If a token-type reference names a type the lexer does not
define, then `Build` must fail with an error of the form `<field>: unknown
token type "<name>"`.

**Left recursion.** If a production can invoke itself without first
consuming a token, then `Build` must fail with an error whose message
contains `left recursion detected` and renders the offending production.

**Repetition guard.** While evaluating `*` or `+` over an expression that
can match without consuming input, the parser must abort after a bounded
number of iterations and report an error mentioning `too many iterations`.
The bound is the package variable `MaxIterations` (default 1,000,000).

## Grammar Compilation

This section defines how parsers are constructed and what they expose.

**Construction.** `Build[G](options...)` must compile the grammar rooted at
struct type `G` and return a `*Parser[G]` or an error. `MustBuild[G]` must
return the parser or panic with the corresponding build error. When `G` is
not a struct (and does not implement custom parsing), `Build` must fail with
an error whose message contains `should be a struct or should implement the
Parseable interface`. When `G` is a struct with no capturing or matching
content, `Build` must fail with an error stating it cannot parse into an
empty struct.

**Sub-parsers.** `ParserForProduction[P, G](parser)` must return a parser
whose root is production `P` of the already-built grammar `G`, sharing the
same lexer and options. Parsing with the returned parser must accept exactly
the language of production `P`.

**Union types.** Where the option `Union[T](m1, m2, ...)` is given for an
interface type `T`, a field of type `T` written as `@@` must try each member
production in the declared order and capture the first that matches, so the
concrete dynamic type of the field value identifies the winning member. In
the EBNF projection a union renders as its own production defined as the
alternation of its member productions. If `T` is not an interface type, then
`Build` must fail with an error stating the union type must be an interface.

**Custom parse functions.** Where the option `ParseTypeWith[T](fn)` is given,
a grammar field of interface type `T` must be parsed by calling `fn` with the
parser's `*lexer.PeekingLexer`; the returned value becomes the captured field
value and a returned error aborts the parse. If `T` is not an interface
type, then `Build` must fail with an error stating `T must be an interface
type` and naming the offending type.

**Parseable types.** When a field's type implements the `Parseable`
interface (`Parse(*lexer.PeekingLexer) error` on the pointer receiver), the
parser must call that method to parse the node. The method must return the
sentinel `NextMatch` to signal "this branch does not match; try the next
alternative", and nil on success.

**Introspection.** `Parser.Lexer()` must return the lexer definition the
parser was built with. `Parser.Lex(filename, reader)` must return the raw
token stream for the input, including an EOF token, without parsing it.

## Parsing and Options

This section defines how a compiled parser consumes input.

**Entry points.** `ParseString(filename, text)`, `ParseBytes(filename,
data)`, and `Parse(filename, reader)` must behave identically for identical
input bytes: lex, parse from the root production, and return a fully
populated `*G`. `ParseFromLexer(peekingLexer)` must parse from an existing
`*lexer.PeekingLexer` (obtained by `lexer.Upgrade` over a `lexer.Lexer`).
The filename argument must appear as the `Filename` component of every
position produced for that input, including positions inside errors.

**Complete-consumption rule.** When a parse of the root production succeeds
but unconsumed tokens remain, the parse must fail with an unexpected-token
error at the first remaining token. Where the parse option
`AllowTrailing(true)` is given, the parse must instead succeed and leave the
remaining tokens unconsumed.

**Partial results.** When a parse fails, the parser must still return the
value pointer with whatever fields were populated before the failure point,
together with the non-nil error; success is signalled only by a nil error.

**Elision.** Where the option `Elide(types...)` is given, tokens of those
types must be dropped from the stream the grammar sees, at every grammar
position. An explicit token-type reference for an elided type must still
match: a fragment such as `@Comment?` must capture an elided comment token
when one is present at that point, and must match empty otherwise.

**Token mapping.** Where the option `Map(fn, symbols...)` is given, `fn`
must be applied to every token of the listed symbol types before matching;
with no symbols listed, it must be applied to every token. Where
`Unquote(types...)` is given, tokens of the listed types (defaulting to
`String` when none are listed) must have Go quoting removed from their
values before matching; if a token of a listed type is not a valid quoted
string, the parse must fail with an error whose message begins `invalid
quoted string`. Where `Upper(types...)` is given, values of the listed token
types must be upper-cased before matching. Mappings apply in option order.

**Case-insensitive literals.** Where the option `CaseInsensitive(types...)`
is given, literal terminals in the grammar must match tokens of the listed
types case-insensitively. The token value captured into the field must be
the original input spelling, not the literal's spelling.

**Lookahead.** The parser must decide between alternatives by trying them
in order with backtracking, under a bounded branch-decision depth that
defaults to 1 token. Where `UseLookahead(n)` is given, the parser must
accept a decision depth of up to `n` tokens; raising the depth must never
reject an input that a lower depth accepts. The constant `MaxLookahead`
provides a practically unbounded depth.

## Value Capture

This section defines how matched tokens become field values. A capture
happens only under `@`; matching without `@` consumes input but stores
nothing.

- **string fields**: every captured token's value must be appended to the
  field's current string content with no separator, so repeated captures
  into one string field concatenate.
- **integer / unsigned / floating-point fields**: the captured text must be
  converted with Go integer/float parsing semantics; a value that does not
  parse must fail the parse with an error whose message contains `failed to
  conform` and the underlying conversion failure, positioned at the token.
- **bool fields**: a successful capture must set the field to `true`
  regardless of the token text — including the literal text `false`. (To
  parse boolean literals by value, a custom `Capture` type is required.)
- **slice fields**: each capture must append one element, converted by the
  element type's rules; struct-element slices accumulate one struct per
  `@@` match.
- **pointer fields**: a matched capture must allocate and populate the
  pointee; an unmatched optional capture must leave the field nil.
- **struct fields via `@@`**: the field's struct type is parsed as a
  sub-production and stored.
- **`lexer.Token` fields**: the captured token itself must be stored.
- **`Capture` implementers**: when the field's type implements `Capture`
  (`Capture(values []string) error`), that method must be called with the
  captured token values instead of any built-in conversion; its error, if
  any, fails the parse.
- **`encoding.TextUnmarshaler` implementers**: when the field's type
  implements `TextUnmarshaler` (and not `Capture`), `UnmarshalText` must be
  called once per captured token, in order.

**Positional side-channels.** Fields with these exact names and types must
be populated automatically and are not part of the grammar:

- `Pos lexer.Position` — the position of the first token consumed by the
  node.
- `EndPos lexer.Position` — the position of the first token following the
  node's consumed input (the EOF position when input is exhausted).
- `Tokens []lexer.Token` — every token consumed by the node, including
  elided tokens.

## Lexing

This section defines the lexer engines and their shared interface. A lexer
definition exposes `Symbols() map[string]lexer.TokenType` naming every token
type it can produce, and `Lex(filename, reader)` returning a token stream. A
token carries its type, its matched text, and its start position (filename,
byte offset, 1-based line and column). Streams terminate with an EOF token
whose type is the constant `lexer.EOF`; `Token.EOF()` reports it.

**Default lexer.** With no `Lexer` option, parsers must use the built-in
text-scanner definition (`lexer.TextScannerLexer`), which tokenises Go-like
source: identifiers, integers, floats, character literals, interpreted and
raw string literals, and comments, with whitespace skipped and never
delivered as tokens. Its `Symbols()` table must map `EOF` to `lexer.EOF` and
the classes `Ident`, `Int`, `Float`, `Char`, `String`, `RawString`,
`Comment` to distinct negative token types in that descending order
(`Ident` = EOF−1, `Int` = EOF−2, and so on). Any other input rune must be
delivered as a single-rune token whose type is the rune's code point.
`lexer.NewTextScannerLexer(configure)` must produce a definition with a
caller-configured underlying scanner, and the package-level `lexer.Lex`,
`lexer.LexString`, and `lexer.LexBytes` helpers must produce token streams
of that same shape.

**Simple lexer.** `lexer.MustSimple(rules)` / `lexer.NewSimple(rules)` must
build a definition from an ordered list of `SimpleRule{Name, Pattern}`. At
each position the rules are tried in order and the first whose regular
expression matches at the current position emits a token of that rule's
name; the rule list order therefore resolves ambiguity. Rule patterns are
anchored at the current position. If no rule matches, lexing must fail with
a `lexer.Error` whose message contains `invalid input text` followed by a
quoted sample of the remaining input, positioned at the failure point.
Symbol values must be assigned from `lexer.EOF` downward in rule order
(first rule = EOF−1, next = EOF−2, ...), with `EOF` itself included in the
table. If a rule's pattern is not a valid regular expression, then
`NewSimple`/`New` must return an error identifying the offending rule and
`MustSimple`/`MustStateful` must panic with it.

**Stateful lexer.** `lexer.MustStateful(rules)` / `lexer.New(rules)` must
build a definition from named rule-sets. Lexing begins in the rule-set named
`Root`. Each rule accepts an optional action: `lexer.Push("State")` switches to the
named rule-set after emitting the token; `lexer.Pop()` returns to the
previous rule-set after emitting the token. `lexer.Include("State")` splices
another rule-set's rules in place, and `lexer.Return()` / `lexer.ReturnRule`
pops without emitting. Rules within the active set are tried in order, as in
the simple lexer, and a position where no rule of the active set matches is
a `lexer.Error` as above.

**Upgrading.** `lexer.Upgrade(lex, elideTypes...)` must read the full token
stream into a `*lexer.PeekingLexer` supporting `Peek()` (next non-elided
token without consuming) and `Next()` (consume and return next non-elided
token), with elided-type tokens skipped by both but retained in the
underlying stream. `lexer.ConsumeAll(lex)` must return every remaining
token, including the terminating EOF token. `lexer.SymbolsByRune(def)` must
return the inverse mapping of `def.Symbols()`.

## EBNF Projection

`Parser.String()` must render the compiled grammar as EBNF text with these
properties:

- One production per line, in the form `Name = body .`, where `Name` is the
  producing struct (or union interface) type's name with its first rune
  upper-cased. The root production comes first; referenced productions
  follow, each rendered once.
- References to token types render as the token name lower-cased inside
  angle brackets (for example `<ident>`); literal terminals render
  double-quoted; sequences separate elements with single spaces; groups are
  parenthesised; alternation uses `|`.
- Modifiers `*`, `+`, `?`, `!` render postfix on their expression; negation
  renders as prefix `~`; lookahead groups render as `(?= ... )` and
  `(?! ... )`.
- Capture markers (`@`) are invisible: a captured and an uncaptured match of
  the same expression render identically. Struct and union references render
  as the production name.
- A union production renders as the `|`-joined list of its member
  production names, followed by each member's own production.

## Error Semantics

All parse-time errors must implement the `Error` interface: `Message()`
returning the message without position, `Position()` returning a
`lexer.Position`, and `Error()` returning the position-prefixed form. The
position-prefixed form is `<pos>: <message>` where `<pos>` renders as
`file:line:column` (the filename part is omitted when empty).

| condition | error | required content |
|---|---|---|
| input token cannot be matched by the grammar | `*UnexpectedTokenError` | message begins `unexpected token "<value>"` and, when the parser has an expectation to report, appends `(expected <expr>)`; `Unexpected` field holds the offending token; position = token position |
| trailing tokens after a complete root parse (without `AllowTrailing`) | `*UnexpectedTokenError` | message `unexpected token "<value>"` at the first trailing token |
| no lexer rule matches input | `*lexer.Error` | `Msg` contains `invalid input text` and a quoted input sample; `Pos` = failure position |
| captured text does not convert to a numeric field | parse error | message contains `failed to conform`; position = capturing token |
| `!`-modified expression matches empty | parse error | message contains `cannot be empty` and renders the sub-expression |
| repetition exceeds `MaxIterations` | parse error | message contains `too many iterations` |
| invalid quoted string under `Unquote` | parse error | message begins `invalid quoted string` |

**Build-time errors** are plain errors (not the `Error` interface):
unknown token type references (`<field>: unknown token type "<name>"`,
with `in literal type constraint` appended for the `"...":Type` form),
malformed fragments naming the field, `left recursion detected`, empty
struct grammars, non-struct roots, non-interface `Union`/`ParseTypeWith`
type arguments. `MustBuild` panics with the same text.

**Constructors.** `Errorf(pos, format, args...)` must build an `Error` from
a position and a format string. `Wrapf(pos, err, format, args...)` must
build an `Error` whose message is `<format-result>: <wrapped message>`; when
the wrapped error is itself an `Error`, the new error must keep the wrapped
error's position; otherwise it uses the given position. `FormatError(err)`
must render `<pos>: <message>`, omitting the position prefix entirely when
the position is the zero value.

## State Model

A `*Parser[G]` is immutable once built: every `Parse*` call must run
independently, and a single parser instance must be safe for concurrent use
by multiple goroutines. A lexer definition is likewise reusable and
concurrency-safe, while an individual `lexer.Lexer` token stream is a
single-use, single-goroutine object. `MaxIterations` is a package-level
variable read at parse time.

## Cross-View Invariants

1. **Grammar/EBNF agreement.** For any grammar that builds successfully,
   every input accepted by `Parse*` is derivable from the EBNF that
   `String()` renders, and modifier/negation/lookahead markers in the EBNF
   correspond one-to-one to the tag fragments they came from.
2. **Entry-point equivalence.** `ParseString`, `ParseBytes`, `Parse`, and
   `ParseFromLexer` over the same bytes must produce identical ASTs and
   identical errors (up to the reader-supplied filename).
3. **Lex/parse agreement.** The token stream returned by `Parser.Lex` is
   exactly the stream the grammar matches after elision and mapping: a
   grammar with a `Tokens []lexer.Token` root field captures a subsequence
   of it.
4. **Position coherence.** For a successful parse, root `Pos` equals the
   position of the first non-elided token; `EndPos` never precedes `Pos`;
   every error position points into the parsed input and carries the
   caller's filename.
5. **Error interface coherence.** For every parse-time error `e`,
   `e.Error()` equals `FormatError(e)` composed of `e.Position()` and
   `e.Message()`.
6. **Sub-parser consistency.** A `ParserForProduction` parser accepts
   exactly the fragments that the parent parser accepts for that production
   and returns structurally equal sub-ASTs.
7. **Capture neutrality.** Adding or removing a `@` capture marker never
   changes whether an input is accepted — only whether values are stored.

## Public Interface

### Import Surface

```go
import (
    "github.com/alecthomas/participle/v2"
    "github.com/alecthomas/participle/v2/lexer"
)
```

Package names are `participle` and `lexer`.

### API Catalog — participle

| Name | Kind | Role |
|---|---|---|
| `Build` | generic function | Compile grammar struct type `G` with options; returns `*Parser[G]` or error |
| `MustBuild` | generic function | As `Build` but panics on error |
| `ParserForProduction` | generic function | Derive a parser rooted at production `P` from a built `*Parser[G]` |
| `Parser` | generic struct | Compiled, immutable, concurrency-safe parser for one grammar |
| `Parser.Parse` | method | Parse from an `io.Reader` under a filename |
| `Parser.ParseString` | method | Parse a string |
| `Parser.ParseBytes` | method | Parse a byte slice |
| `Parser.ParseFromLexer` | method | Parse from an existing `*lexer.PeekingLexer` |
| `Parser.Lex` | method | Return the raw token stream (with EOF token) without parsing |
| `Parser.Lexer` | method | Return the lexer definition the parser was built with |
| `Parser.String` | method | Render the grammar as EBNF text |
| `Option` | function type | Build-time configuration accepted by `Build` |
| `Lexer` | function | Option: use the given lexer definition |
| `UseLookahead` | function | Option: allow branch lookahead up to n tokens (default 1) |
| `CaseInsensitive` | function | Option: match grammar literals against listed token types case-insensitively |
| `Elide` | function | Option: drop listed token types from the parsed stream |
| `Map` | function | Option: apply a `Mapper` to tokens of listed types (all types when none listed) |
| `Unquote` | function | Option: strip Go quoting from listed token types (default `String`) |
| `Upper` | function | Option: upper-case values of listed token types |
| `Union` | generic function | Option: register member productions for an interface type |
| `ParseTypeWith` | generic function | Option: register a custom parse function for an interface type |
| `Mapper` | function type | Token transformation `func(lexer.Token) (lexer.Token, error)` |
| `ParseOption` | function type | Per-parse configuration accepted by `Parse*` |
| `AllowTrailing` | function | ParseOption: accept unconsumed trailing tokens |
| `Trace` | function | ParseOption: write parse trace to a writer (output unspecified) |
| `Capture` | interface | `Capture(values)` — custom conversion of captured token values |
| `Parseable` | interface | `Parse(lex)` — self-parsing grammar node; returns `NextMatch` on no-match |
| `NextMatch` | error variable | Sentinel returned by `Parseable.Parse` to try the next alternative |
| `Error` | interface | Positioned error: `Message()`, `Position()`, `Error()` |
| `Errorf` | function | Construct an `Error` from position and format string |
| `Wrapf` | function | Wrap an error with a message prefix, keeping an inner `Error` position |
| `FormatError` | function | Render `pos: message`, omitting a zero position |
| `ParseError` | struct | Positioned parse error with public `Msg`, `Pos` fields; pointer implements `Error` |
| `UnexpectedTokenError` | struct | Parse error carrying the offending `Unexpected lexer.Token` and an `Expect` string; pointer implements `Error` |
| `MaxLookahead` | constant | Practically unbounded lookahead depth for `UseLookahead` |
| `MaxIterations` | variable | Repetition guard bound, default 1,000,000 |

### API Catalog — lexer

| Name | Kind | Role |
|---|---|---|
| `TokenType` | integer type | Token class identifier; negative for named classes, rune value for single-rune tokens |
| `EOF` | constant | Token type of the end-of-stream token (−1) |
| `Position` | struct | `Filename`, `Offset`, `Line`, `Column` (1-based line/column); `String()` renders `file:line:column`, omitting an empty filename |
| `Token` | struct | `Type`, `Value`, `Pos`; `EOF()` reports the end token; `String()` returns the value |
| `EOFToken` | function | Construct an EOF token at a position |
| `Definition` | interface | Lexer factory: `Symbols()` name→type table and `Lex(filename, reader)` |
| `Lexer` | interface | Token stream: `Next()` returns the next token or an error |
| `TextScannerLexer` | variable | Default Go-like source definition |
| `NewTextScannerLexer` | function | Text-scanner definition with caller configuration |
| `Lex` / `LexString` / `LexBytes` | functions | Package-level text-scanner token streams over reader/string/bytes |
| `SimpleRule` | struct | `Name`, `Pattern` — one ordered rule of a simple lexer |
| `MustSimple` / `NewSimple` | functions | Build a single-state definition from ordered simple rules (panic/error forms) |
| `Rule` | struct | `Name`, `Pattern`, `Action` — one rule of a stateful lexer |
| `Rules` | map type | State name → ordered rule list; lexing starts at `Root` |
| `Action` | interface | Post-match state transition attached to a rule |
| `Push` | function | Action: enter a named state after emitting the token |
| `Pop` | function | Action: return to the previous state after emitting the token |
| `Include` | function | Pseudo-rule: splice another state's rules in place |
| `Return` / `ReturnRule` | function / variable | Pseudo-rule: pop the state without emitting a token |
| `MustStateful` / `New` | functions | Build a stateful definition from `Rules` (panic/error forms) |
| `StatefulDefinition` | struct | Definition produced by simple/stateful constructors; also offers `LexString` |
| `Must` | function | Panic-on-error wrapper around a `(Definition, error)` pair |
| `PeekingLexer` | struct | Fully-read stream with `Peek()`/`Next()` over non-elided tokens |
| `Upgrade` | function | Read a `Lexer` into a `*PeekingLexer`, marking elided token types |
| `ConsumeAll` | function | Drain a `Lexer` into a token slice ending with the EOF token |
| `SymbolsByRune` | function | Inverse of a definition's `Symbols()` map |
| `Error` | struct | Lexing error with public `Msg`, `Pos` fields; pointer implements the participle `Error` interface |

### CLI Entry Points

There is no console script for this module. Use is through the Go package
API only.

## Appendix A: Environment

The working environment runs Go 1.21 or newer on Linux without network
access. The module under construction must declare the module path
`github.com/alecthomas/participle/v2` in its `go.mod`, with the packages at
`github.com/alecthomas/participle/v2` and
`github.com/alecthomas/participle/v2/lexer`, so consuming builds wire it in
with a standard `replace` directive. No third-party libraries are available
or required; the implementation uses only the Go standard library. No
fixture files are involved: all behavior is observable with in-memory
strings and readers.

## Appendix B: Assessment Notes

Functional coverage is verified by compiled test suites that import the two
packages above and exercise the documented public surface only: grammar
compilation outcomes, parse results and captured field values, EBNF
renderings, token streams, and the error taxonomy above. Tests construct
grammars as Go structs inline and never inspect unexported state. Where this
specification pins message fragments (`unexpected token`, `left recursion
detected`, `invalid input text`, `failed to conform`, `cannot be empty`,
`too many iterations`, `invalid quoted string`, `unknown token type`), tests
match those fragments, not entire renderings, unless the full form is given
here. Scoring counts each passing test function; partial credit accrues per
test, so a correct subset of behaviors earns its share even when other areas
are incomplete.
