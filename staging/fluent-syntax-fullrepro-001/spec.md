<!-- INTERNAL
task_id: fluent-syntax-fullrepro-001
spec_version: v1
delta: initial version; contract details fixed by three probe rounds against
the pinned reference: common-indent dedent arithmetic (deeper lines keep the
excess, blank lines contribute a bare line-feed element, indentation before a
line-leading placeable vanishes and never participates in the common indent),
LF retained on a line's element while CRLF splits into a standalone line-feed
element, zero-column placeables continue a pattern while zero-column text ends
it, malformed comment lines junk in full mode but vanish in runtime mode,
term-attribute references legal as selectors but illegal as placeables,
named-argument values restricted to literals, junk spans absorbing trailing
blank lines, free comments serialized with a blank line on each side, and the
replacement-character rules of the unescaping helpers
source_boundary: docs.rs/fluent-syntax 0.12.0 (module docs and per-node doc
examples for ast, parser, serializer, unicode), projectfluent.org FTL syntax
semantics; reference behavior observed by running the pinned checkout (probe
binary, three rounds); the serde/json cargo features, the fixture-update
binary, and Slice implementations beyond &str and String are excluded
-->

# fluent-syntax Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`fluent-syntax` is the grammar layer of a localization system. It parses
Fluent Translation List ("FTL") text — a line-oriented format in which
translation units carry placeholders, attributes, and plural/case selection
logic — into a fully public abstract syntax tree, and serializes that tree
back to canonical FTL text.

One syntax model is exposed through four coordinated surfaces: a
tooling-grade parser that preserves comments and recovers from errors by
emitting structured junk entries with byte-precise error records, a
runtime-grade parser over the same grammar that strips comments, a
serializer that renders any tree in a canonical textual form, and a pair of
helpers that decode the escape sequences used inside string literals. The
AST is plain public data — every node type, field, and variant is part of
the contract — and is generic over the underlying string representation so
the same tree shape works for borrowed and owned text.

The installable package name is `fluent-syntax`.

## Non-Goals

- This specification does not require any serialization-framework
  integration for the AST, nor a JSON projection of it; trees are exchanged
  as typed values only.
- This specification does not require a command-line tool; the crate is a
  library.
- This specification does not define string representations beyond `&str`
  and `String`: the parsing and serialization interfaces are generic over a
  slice abstraction, and both of those implementations must exist, but no
  obligation is placed on user-supplied implementations.
- This specification does not define exact human-readable error message
  text; error conditions are classified by error kind, position, and span.
- This specification does not define the diagnostic payload text of the
  two escape-sequence error kinds (see Error Semantics); only the kind
  itself is contractual for those two.
- This specification does not define any depth or size limits for nested
  expressions.

## Representative Workflows

**Parsing and inspecting a resource.** FTL text parses into a `Resource`
whose `body` lists the entries in input order. Every node is plain data.

```rust
use fluent_syntax::ast;
use fluent_syntax::parser::parse;

let ftl = "welcome-back = Good to see you, { $crew }!\n";
let resource = parse(ftl).expect("clean parse");

assert_eq!(
    resource.body[0],
    ast::Entry::Message(ast::Message {
        id: ast::Identifier { name: "welcome-back" },
        value: Some(ast::Pattern {
            elements: vec![
                ast::PatternElement::TextElement { value: "Good to see you, " },
                ast::PatternElement::Placeable {
                    expression: ast::Expression::Inline(
                        ast::InlineExpression::VariableReference {
                            id: ast::Identifier { name: "crew" },
                        }
                    ),
                },
                ast::PatternElement::TextElement { value: "!" },
            ],
        }),
        attributes: vec![],
        comment: None,
    }),
);
```

**Recovering from errors and re-serializing.** Invalid spans become `Junk`
entries and byte-ranged error records; the rest of the input still parses.
The serializer renders the tree canonically, with junk included only on
request.

```rust
use fluent_syntax::parser::parse;
use fluent_syntax::serializer::{serialize, serialize_with_options, Options};

let ftl = "dock-a = Ready\n?!bad\ndock-b = Standby\n";
let (resource, errors) = parse(ftl).expect_err("junk present");
assert_eq!(errors.len(), 1);

assert_eq!(serialize(&resource), "dock-a = Ready\ndock-b = Standby\n");
assert_eq!(
    serialize_with_options(&resource, Options { with_junk: true }),
    "dock-a = Ready\n?!bad\ndock-b = Standby\n",
);
```

## Resource Grammar and Entry Model

An FTL resource is a sequence of entries separated by line breaks; blank
lines between entries are insignificant. `Resource<S>` holds the parsed
entries as `body: Vec<Entry<S>>` in input order. An empty input, or input
consisting only of blank lines, parses to an empty body.

**Entry kinds.** `Entry<S>` has exactly six variants: `Message(Message<S>)`,
`Term(Term<S>)`, `Comment(Comment<S>)`, `GroupComment(Comment<S>)`,
`ResourceComment(Comment<S>)`, and `Junk { content: S }`.

**Identifiers.** An identifier starts with an ASCII letter and continues
with ASCII letters, ASCII digits, `-`, and `_` (`crew-count_9` is one
identifier). A line that must start an entry but does not begin with a
legal starter is an error (see Error Recovery and Junk).

**Messages.** A message line is `identifier = pattern`. Spaces are allowed
around `=`. `Message<S>` carries `id: Identifier<S>`, `value:
Option<Pattern<S>>`, `attributes: Vec<Attribute<S>>`, and `comment:
Option<Comment<S>>`. The value may be omitted only when at least one
attribute follows; a message with neither value nor attributes is an error
of kind `ExpectedMessageField` carrying the message's identifier text.

**Terms.** A term is a message-shaped entry whose identifier is written
with a leading `-` (`-station-name = Meridian`). The `-` is not part of
`Term::id`. `Term<S>` carries `id`, `value: Pattern<S>` (not optional),
`attributes`, and `comment`. A term whose value is missing is an error of
kind `ExpectedTermField` carrying the term's identifier text, even when
attributes are present.

**Attributes.** After an entry's value line, each line consisting of
indentation, `.`, an identifier, `=`, and a pattern adds one
`Attribute<S> { id, value }` to the entry, in input order. Any positive
amount of leading indentation works, and consecutive attribute lines may be
indented differently. An attribute's pattern is required; attribute
patterns follow the full pattern grammar including multiline continuation.

**Line endings.** LF and CRLF are both accepted as line terminators
everywhere, including in comments and between entries.

## Pattern Text: Lines, Indentation, Dedent

A pattern is the value text of a message, term, attribute, or select
variant: `Pattern<S>` holds `elements: Vec<PatternElement<S>>` where each
element is either `TextElement { value: S }` or `Placeable { expression:
Expression<S> }`. Text elements never contain escape sequences; a literal
brace can only be produced through a string literal placeable.

**Inline start.** Text may begin on the `=` line itself; spaces after `=`
are skipped and the remaining text up to the line break forms the first
element verbatim.

**Continuation lines.** A pattern continues onto following lines under
these rules, checked at each line start:

- A line whose first non-space character position (its indent) is zero ends
  the pattern — unless that first character is `{`, which continues the
  pattern with a placeable.
- An indented line whose first non-space character is `.`, `[`, `*`, or `}`
  ends the pattern (`.` hands control to the attribute grammar; the others
  make the following text a new — usually invalid — entry).
- Any other indented line, and any blank line, continues the pattern.

**Common-indent stripping.** Over all continuation lines that begin with
text (not with `{`) and are not blank, the minimum indent is the pattern's
common indent. Exactly that many leading spaces are removed from each such
line; a line indented deeper keeps the excess spaces in its text. Blank
continuation lines contribute a text element holding the line feed (they do
not participate in the common indent, but spaces they carry beyond it stay
ahead of the line feed).
Indentation preceding a line-leading `{` is discarded entirely and does not
participate in the common indent; a `{` at column zero sets the common
indent to zero, so subsequent text lines keep all of their indentation.

**Element splitting.** Each continuation line's text is its own element. A
line terminated by LF keeps the `\n` at the end of its element; a line
terminated by CRLF contributes its text without the terminator plus a
standalone `"\n"` element. Text on either side of a placeable within one
line forms separate elements. The concatenation of all element text is
therefore identical for LF and CRLF input.

**Trailing trim.** Elements after the last non-blank element are dropped,
and the final kept text element is trimmed of trailing spaces, carriage
returns, and line feeds. A value line containing only spaces yields no
pattern at all (for a message with no attributes this surfaces as
`ExpectedMessageField`).

**Stray closing brace.** A `}` encountered in pattern text outside any
placeable is an error of kind `UnbalancedClosingBrace`.

Example: parsing `"deck =\n    line1\n      line2\n\n    line3\n"` yields
elements `["line1\n", "  line2\n", "\n", "line3"]` — common indent 4, the
deeper line keeps 2 spaces, the blank line survives as `"\n"`, and the
final element is trimmed.

## Placeables and Expressions

A placeable embeds an expression in a pattern between `{` and `}`.
Whitespace, including line breaks, is allowed after `{` and around the
expression. `Expression<S>` has two variants: `Inline(InlineExpression<S>)`
and `Select { selector: InlineExpression<S>, variants: Vec<Variant<S>> }`.

`InlineExpression<S>` has exactly seven variants:

- **`StringLiteral { value: S }`** — written `"…"`. The stored value is
  the raw text between the quotes with escape sequences left intact. Legal
  escapes are `\\`, `\"`, `\{`, `\u` followed by exactly four hex digits,
  and `\U` followed by exactly six hex digits. Any other `\` sequence is an
  error of kind `UnknownEscapeSequence`; a `\u`/`\U` with too few hex
  digits is `InvalidUnicodeEscapeSequence`; a line break before the closing
  quote is `UnterminatedStringLiteral`.
- **`NumberLiteral { value: S }`** — an optional `-`, one or more digits,
  and optionally `.` followed by one or more digits. The raw spelling is
  preserved (`007`, `-0.50`). A `.` not followed by a digit is an error of
  kind `ExpectedCharRange` with range text `0-9`.
- **`VariableReference { id }`** — `$` followed by an identifier.
- **`MessageReference { id, attribute }`** — an identifier, optionally
  followed by `.` and an attribute identifier.
- **`TermReference { id, attribute, arguments }`** — `-` followed by an
  identifier, optionally `.attribute`, optionally call arguments. A term
  reference **with an attribute** may not be used as a placeable
  expression: kind `TermAttributeAsPlaceable`.
- **`FunctionReference { id, arguments }`** — an identifier immediately
  usable as a callee followed by call arguments. Every character of the
  callee must be an ASCII uppercase letter, digit, `_`, or `-`; otherwise
  the parse fails with kind `ForbiddenCallee`.
- **`Placeable { expression: Box<Expression<S>> }`** — a nested `{ … }`
  placeable used as an expression.

**Call arguments.** `CallArguments<S>` holds `positional:
Vec<InlineExpression<S>>` and `named: Vec<NamedArgument<S>>`, where
`NamedArgument<S>` is `{ name: Identifier<S>, value: InlineExpression<S> }`.
Arguments are comma-separated between `(` and `)`; blanks and line breaks
are allowed, a trailing comma is legal, and `()` yields empty vectors. A
named argument is written `name: value` and its value must be a string or
number literal — anything else is kind `ExpectedLiteral`. All positional
arguments must precede the first named argument
(`PositionalArgumentFollowsNamed`), and a named argument name may not
repeat (`DuplicatedNamedArgument` carrying the repeated name).

## Select Expressions

A select expression chooses between variant patterns: written as a
placeable whose inline selector is followed by `->`, a line break, and one
variant per line.

**Selector restrictions.** The selector must be a string literal, number
literal, variable reference, function reference, or a term reference
**with** an attribute. The failures are, in order of specificity: a message
reference without attribute → kind `MessageReferenceAsSelector`; a message
reference with attribute → `MessageAttributeAsSelector`; a term reference
without attribute → `TermReferenceAsSelector`; a nested placeable →
`ExpectedSimpleExpressionAsSelector`. Text (not a line break) after `->` is
an error of kind `ExpectedCharRange` with range text `\n | \r\n`.

**Variants.** Each variant line is an optional `*`, then `[`, a key, `]`,
and a pattern value. Variant lines may be indented arbitrarily, including
not at all. The key is an identifier or a number literal; spaces are
allowed inside the brackets. `Variant<S>` carries `key: VariantKey<S>`
(variants `Identifier { name: S }` and `NumberLiteral { value: S }`),
`value: Pattern<S>`, and `default: bool`. Variant values follow the full
pattern grammar, so a variant's value may itself be multiline and may nest
further select expressions. The variant list ends at the first line that
does not start (after optional blanks) with `[` or `*`.

**Default marking.** Exactly one variant must be marked default with `*`:
none marked → kind `MissingDefaultVariant`; more than one →
`MultipleDefaultVariants`. A variant with no value → `MissingValue`.
Variant order, including the position of the default, is preserved in the
AST and in serialization.

## Comments and Attachment

A comment line is `#`, `##`, or `###` at column zero, followed by either a
line end (empty comment line) or one space and the line's content. The
marker count selects the level: `#` regular, `##` group, `###` resource.
`Comment<S>` stores `content: Vec<S>`, one element per line, without the
marker or the single separating space; an empty comment line contributes an
empty string.

**Block merging.** Consecutive comment lines of the same level merge into
one comment. A level change ends the block and starts a new comment entry.

**Malformed comment lines.** A `#` immediately followed by anything other
than a space, another `#` within the marker, or a line end is invalid: in
the comment-preserving parser it ends any open comment block and the
offending line becomes junk with an error of kind `ExpectedToken(' ')`; the
runtime parser skips such a line silently (see below).

**Attachment.** A regular (`#`) comment whose block is immediately
followed — with no blank line — by a message or term entry does not appear
in `body`; it becomes that entry's `comment` field. With one or more blank
lines between, or when the next entry is anything else (including junk),
the comment stays in `body` as `Entry::Comment`. Group and resource
comments never attach; they always appear as their own entries.

**Runtime mode.** `parse_runtime` accepts the same grammar but records no
comments at all: no comment entries appear in `body`, and `comment` fields
are `None`. Malformed comment lines are skipped without error in this
mode. On comment-free input, `parse` and `parse_runtime` produce identical
resources and identical error lists.

## Error Recovery and Junk

Both parsers are non-fatal: they always produce a complete `Resource`.
The parse functions return `Result<S>`, an alias for
`std::result::Result<Resource<S>, (Resource<S>, Vec<ParserError>)>`: `Ok`
when no errors occurred, otherwise `Err` carrying the recovered tree
together with one `ParserError` per junk entry, in input order.

**Recovery.** When an entry fails to parse, the parser skips forward to
the next line whose column-zero character is an ASCII letter, `-`, or `#`
(or to end of input). Everything from the failed entry's start to that
point — including intervening blank lines — becomes one `Entry::Junk`
whose `content` is the verbatim input slice. Entries after the junk parse
normally.

**Error records.** `ParserError` has three public fields: `pos:
Range<usize>` — the byte range of the exact offending location; `slice:
Option<Range<usize>>` — the byte range of the whole junk span (always
present on reported errors, and equal to the span of the junk entry's
content); and `kind: ErrorKind`. `ParserError` values are cloneable and
comparable for equality, and both `ParserError` and `ErrorKind` implement
the standard error and display traits. For a missing-field error
(`ExpectedMessageField`/`ExpectedTermField`) `pos` spans the whole entry;
for single-character expectations it is the one-byte range at the failure
point.

Example: in the input `"ok = 1\n\n!bad line\n\n\nfin = 2\n"`, the junk
entry's content is `"!bad line\n\n\n"`, and the single error has `pos`
`8..9`, `slice` `Some(8..20)`, and kind `ExpectedCharRange` with range
text `a-zA-Z`.

## Serialization

`serialize` renders a resource to a `String`; it equals
`serialize_with_options` with default options. `Options` has one public
field, `with_junk: bool`, and the type is copyable, comparable, and
defaults to `false`. Serialization is total: any tree built from public
constructors serializes without error.

**Canonical form.** The serializer does not reproduce input formatting; it
renders each entry in one canonical shape:

- A message renders as `id =`, its value, then its attributes; a term the
  same with a `-` before the identifier. Indentation is four spaces per
  nesting level.
- A single-line pattern (no text element containing a line feed and no
  select expression) renders inline: one space after `=`, then the
  elements.
- A multiline pattern starts on a fresh line, indented one level, with
  each line indented to the current level. Exception: a pattern whose
  first element is a text element beginning with `.` renders inline even
  when multiline.
- Each attribute renders on its own line, one level deep: `.id =` plus its
  pattern (same inline/multiline rule).
- An inline placeable renders as `{ expression }`. A directly nested
  placeable collapses to double braces: `{{ inner }}`. A select placeable
  renders as `{ selector ->`, one variant per line one level deeper, then
  `}` on its own line at the placeable's level; the default variant's `*`
  is drawn into the indentation, replacing its last space (`   *[key]`
  next to `    [key]`). Variant values use the standard pattern rules at
  the variant's level.
- String literals render as `"` + stored raw value + `"` (escape
  sequences are not decoded). Number literals, variable (`$id`), message
  (`id`/`id.attr`), term (`-id`, with `.attr` and argument list when
  present), and function references render in their source notation; call
  arguments render comma-space separated with named arguments as
  `name: value`, and an empty argument list renders as `()`.
- An attached comment renders as `# line` lines directly above its entry.
  A free-standing comment renders with its level's marker, preceded by a
  blank line when a non-junk entry was serialized before it, and always
  followed by a blank line. A comment line with empty content renders as
  the bare marker with no trailing space.
- Junk is skipped unless `with_junk` is set, in which case its content is
  emitted verbatim.
- All output line breaks are LF; CRLF never appears in output for trees
  parsed from CRLF input.

**Stability.** Serializing any parsed tree and re-parsing the output
reproduces the same tree (for junk-free trees with the default options);
consequently serialize ∘ parse is a fixed point on canonical text.

## Unicode Unescaping

The escape sequences stored raw inside `StringLiteral` values are decoded
by two helpers. `unescape_unicode(w, input)` writes the decoded text to a
`fmt::Write` and returns the writer's `fmt::Result`;
`unescape_unicode_to_string(input)` returns `Cow<str>`, borrowing the
input when it contains no backslash and allocating otherwise.

Decoding rules, applied left to right:

- `\\` → `\` and `\"` → `"`.
- `\u` consumes exactly four following characters, `\U` exactly six;
  the consumed text is parsed as hex and produces that scalar value.
- Every failure — non-hex characters, a value that is not a valid scalar,
  or fewer characters than required before end of input — produces the
  replacement character U+FFFD instead.
- Any other escaped character (including `{`, which the *parser* accepts
  in literals) produces U+FFFD, consuming the escaped character. A lone
  trailing `\` also produces U+FFFD.
- Text outside escapes passes through unchanged.

The helpers operate on plain `&str` and do not validate that the input
came from a parsed literal.

## State Model

The core state is one syntax tree: a `Resource` owning a vector of
entries, each entry a plain-data node tree as defined above. All node
fields are public; every node type is cloneable, debug-printable, and
comparable for equality. Public projections of this state:

1. **`parse`** constructs the full tree from text: comments preserved and
   attached, invalid spans as junk plus error records.
2. **`parse_runtime`** constructs the comment-free projection of the same
   grammar.
3. **`serialize`/`serialize_with_options`** render any tree to canonical
   text, junk optional.
4. **`unescape_unicode`/`unescape_unicode_to_string`** decode the escape
   sequences that literal nodes store raw.

There are no hidden invariants: mutation is direct field manipulation, and
a hand-built tree is indistinguishable from a parsed one on every surface.

## Error Semantics

All parse-level failures are reported as `ParserError` records alongside
the recovered tree; nothing panics on malformed text. `ErrorKind` has
exactly the following twenty-one variants:

| Condition | `ErrorKind` |
|---|---|
| Entry line starts with an illegal character; identifier expected | `ExpectedCharRange { range }` with `range == "a-zA-Z"` |
| Digits expected (number literal body or fraction) | `ExpectedCharRange { range }` with `range == "0-9"` |
| Text follows `->` on the selector line | `ExpectedCharRange { range }` with `range == "\n \| \r\n"` |
| A specific token was required (`=`, `}`, `)`, `]`, space after comment marker, …) | `ExpectedToken(char)` carrying that character |
| Message has neither value nor attributes | `ExpectedMessageField { entry_id }` |
| Term has no value | `ExpectedTermField { entry_id }` |
| Call arguments attached to a non-uppercase callee | `ForbiddenCallee` |
| Select with no default variant | `MissingDefaultVariant` |
| Select with two default variants | `MultipleDefaultVariants` |
| Variant (or attribute) without a value where one is required | `MissingValue` |
| Message reference used as selector | `MessageReferenceAsSelector` |
| Message attribute used as selector | `MessageAttributeAsSelector` |
| Term reference (no attribute) used as selector | `TermReferenceAsSelector` |
| Term attribute used as a placeable | `TermAttributeAsPlaceable` |
| Nested placeable used as selector | `ExpectedSimpleExpressionAsSelector` |
| Line break inside a string literal | `UnterminatedStringLiteral` |
| Positional argument after a named argument | `PositionalArgumentFollowsNamed` |
| Named argument name repeated | `DuplicatedNamedArgument(String)` carrying the name |
| Unsupported `\` escape in a string literal | `UnknownEscapeSequence(String)` — payload text not contractual |
| Too few hex digits after `\u`/`\U` | `InvalidUnicodeEscapeSequence(String)` — payload text not contractual |
| `}` in pattern text outside a placeable | `UnbalancedClosingBrace` |
| Inline expression expected but not found | `ExpectedInlineExpression` |
| Named argument value is not a string/number literal | `ExpectedLiteral` |

`ErrorKind` values are cloneable and comparable for equality. The
unescaping helpers never fail on malformed escapes (they substitute
U+FFFD); `unescape_unicode` only propagates errors of the underlying
writer.

## Cross-View Invariants

1. **Canonical fixed point (parse ↔ serialize).** For canonical text `c`
   (text already in the serializer's shape), `serialize(parse(c)) == c`.
2. **Normalization idempotence (parse ↔ serialize).** For any text `t`
   that parses cleanly, `n = serialize(parse(t))` satisfies
   `serialize(parse(n)) == n`, and `parse(n) == parse(t)` up to the
   pattern re-slicing the canonical form implies (equal patterns
   element-for-element when `t` was already canonical).
3. **Junk fidelity (recovery ↔ serialization ↔ input).** Each junk
   entry's content equals the input slice at its error's `slice` range,
   and with-junk serialization embeds that content verbatim.
4. **Mode agreement (parse ↔ parse_runtime).** On comment-free input the
   two parsers return equal resources and equal error vectors; on any
   input, the runtime body equals the full body with comment entries
   removed and attached comments nulled, provided every comment line is
   well-formed.
5. **Builder equivalence (construction ↔ serialization ↔ parse).** A
   hand-constructed tree using only documented node shapes serializes to
   text that parses back to that same tree (junk-free trees, canonical
   pattern text).
6. **Literal round trip (parse ↔ unescape).** For a parsed
   `StringLiteral`, the stored value re-serializes verbatim inside
   quotes, and unescaping the stored value decodes exactly the `\\`,
   `\"`, `\u`, `\U` sequences the parser validated.
7. **Line-ending equivalence (parse LF ↔ parse CRLF).** Replacing every
   LF in a clean input with CRLF leaves entry structure, identifiers,
   comment content, and the concatenated text of every pattern unchanged,
   and the serialized output of both parses is identical LF text.

## Public Interface

### Import Surface

```rust
use fluent_syntax::ast::{
    Attribute, CallArguments, Comment, Entry, Expression, Identifier,
    InlineExpression, Message, NamedArgument, Pattern, PatternElement,
    Resource, Term, Variant, VariantKey,
};
use fluent_syntax::parser::{
    parse, parse_runtime, ErrorKind, ParserError, Result, Slice,
};
use fluent_syntax::serializer::{serialize, serialize_with_options, Options};
use fluent_syntax::unicode::{unescape_unicode, unescape_unicode_to_string};
```

All AST types are generic over the string representation `S`; the parse
functions accept any `S` implementing the `Slice` abstraction, which is
provided for `&str` (borrowing) and `String` (owning).

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `ast::Resource<S>` | struct | parsed resource; `body: Vec<Entry<S>>` |
| `ast::Entry<S>` | enum | message / term / 3 comment levels / junk |
| `ast::Message<S>` | struct | `id`, optional `value`, `attributes`, `comment` |
| `ast::Term<S>` | struct | `id`, required `value`, `attributes`, `comment` |
| `ast::Attribute<S>` | struct | `.id = pattern` unit |
| `ast::Identifier<S>` | struct | `name: S` |
| `ast::Pattern<S>` | struct | `elements: Vec<PatternElement<S>>` |
| `ast::PatternElement<S>` | enum | `TextElement { value }` / `Placeable { expression }` |
| `ast::Expression<S>` | enum | `Inline(...)` / `Select { selector, variants }` |
| `ast::InlineExpression<S>` | enum | seven expression forms |
| `ast::Variant<S>` | struct | `key`, `value`, `default` |
| `ast::VariantKey<S>` | enum | `Identifier { name }` / `NumberLiteral { value }` |
| `ast::Comment<S>` | struct | `content: Vec<S>`, one line per element |
| `ast::CallArguments<S>` | struct | `positional`, `named` |
| `ast::NamedArgument<S>` | struct | `name`, literal `value` |
| `parser::parse` | fn | full parse, comments preserved |
| `parser::parse_runtime` | fn | comment-stripping parse |
| `parser::Result<S>` | type alias | `Ok(Resource)` / `Err((Resource, Vec<ParserError>))` |
| `parser::ParserError` | struct | `pos`, `slice`, `kind` |
| `parser::ErrorKind` | enum | twenty-one failure classifications |
| `parser::Slice` | trait | string-representation abstraction (`&str`, `String`) |
| `serializer::serialize` | fn | canonical text, junk skipped |
| `serializer::serialize_with_options` | fn | canonical text with `Options` |
| `serializer::Options` | struct | `with_junk: bool`; `Copy`, `Default`, `PartialEq` |
| `unicode::unescape_unicode` | fn | decode escapes into a writer |
| `unicode::unescape_unicode_to_string` | fn | decode escapes into `Cow<str>` |

### CLI Entry Points

There is no console script for this package. Programmatic use is through
the Rust crate API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `fluent-syntax` with its default configuration
  providing every behavior described here; the assessment suite depends on
  the crate as `fluent-syntax = { version = "*" }`.
- No serialization-framework or JSON features are enabled or required.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Entry grammar: messages, terms, attributes, identifier rules,
  value/attribute presence requirements.
- Pattern text: inline and continuation lines, common-indent stripping
  with deeper-line excess, blank-line elements, placeable-line indent
  rules, trailing trim, LF/CRLF element splitting.
- Expressions: all seven inline forms, raw literal retention, callee
  restrictions, call-argument ordering and literal-value rules, nesting.
- Select expressions: selector legality matrix, variant keys, default
  marking, multiline and nested variants.
- Comments: three levels, block merging, level splits, empty lines,
  attachment rules, runtime stripping, malformed-line asymmetry.
- Error recovery: junk spans, error pos/slice arithmetic, multi-error
  inputs, kind classification.
- Serialization: canonical shapes for every construct, junk toggle, free
  comment blank lines, fixed points and round trips.
- Unescaping: supported escapes, replacement-character rules, borrowing
  behavior.

Atomic tests target one surface at a time; integration tests combine at
least two surfaces (for example text → AST → canonical text → AST, or
error records ↔ junk ↔ with-junk serialization) against one input.
