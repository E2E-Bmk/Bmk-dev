# sh-syntax Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`syntax` is a shell-language engine for Go programs. It parses POSIX Shell,
Bash, and mksh source into a fully positioned syntax tree, pretty-prints any
tree back into canonical shell text, and serializes trees to and from a typed
JSON form. One tree model underlies every feature: a parser turns bytes into
nodes that record the exact byte offset, line, and column of every token that
matters; a printer turns nodes back into text under a canonical formatting
style with configurable variations; a JSON codec round-trips the same nodes,
positions included, for interchange with other tools.

Around that core, the engine offers incremental parsing (statement by
statement, word by word, or interactively line by line), a depth-first tree
walker, a string quoter that renders arbitrary Go strings safe for use as
shell words, a brace-expansion splitter, and a simplifier that removes
redundant syntax. Errors are values that carry the failing position and
distinguish "this input is malformed" from "this input is valid in a
different shell dialect". The installable module path is `mvdan.cc/sh/v3`;
this document covers its `syntax` package and the `syntax/typedjson`
subpackage.

## Non-Goals

- This specification does not require executing or interpreting shell
  programs; the engine works on syntax alone and never runs commands.
- This specification does not require performing word expansion, globbing,
  or variable resolution; expansions are represented as tree nodes, not
  evaluated.
- This specification does not define zsh grammar support. The variant
  enumeration includes a `LangZsh` value whose name renders as `"zsh"`, but
  no parsing, printing, or tree behavior specific to zsh is required.
- This specification does not require a column-preserving ("padding
  keeping") formatting mode.
- This specification does not require a command-line tool; all functionality
  is exposed as a Go library.
- This specification does not require concurrency safety on a single parser
  or printer instance; each instance is reused sequentially.

## Representative Workflows

**Parsing and inspecting a script.** A caller builds a parser, feeds it a
reader, and receives the root `*File` node. The tree is inspected either
directly through typed fields or generically through `Walk`.

```go
src := "foo bar | baz\n"
parser := syntax.NewParser()
file, err := parser.Parse(strings.NewReader(src), "example.sh")
if err != nil {
    log.Fatal(err) // e.g. "example.sh:1:5: ..." with position info
}
syntax.Walk(file, func(node syntax.Node) bool {
    if word, ok := node.(*syntax.Word); ok {
        fmt.Println(word.Lit(), word.Pos().Line(), word.Pos().Col())
    }
    return true
})
```

**Reformatting under options.** The same tree prints under different
formatting policies. Printing is deterministic: equal trees and equal
options produce identical bytes.

```go
file, _ := syntax.NewParser().Parse(strings.NewReader(
    "if true;then foo;fi\n"), "")
var out strings.Builder
syntax.NewPrinter().Print(&out, file)
// out: "if true; then foo; fi\n"
out.Reset()
syntax.NewPrinter(syntax.Minify(true)).Print(&out, file)
// out: "if true;then foo;fi\n"
```

**JSON interchange.** A parsed tree encodes to typed JSON and decodes back
to an equal tree, positions included, so external tooling consumes or
produces syntax trees without linking the parser.

```go
file, _ := syntax.NewParser().Parse(strings.NewReader("x=1\n"), "")
var buf bytes.Buffer
typedjson.Encode(&buf, file)              // {"Type":"File",...}
node, err := typedjson.Decode(&buf)       // node is a *syntax.File again
```

**Quoting arbitrary strings.** Programs that generate shell code quote
untrusted strings first, choosing a dialect; the result parses back as a
single word meaning the original string.

```go
quoted, err := syntax.Quote("foo bar", syntax.LangBash) // "'foo bar'"
```

## Language Variants

Shell dialect selection drives both tokenizing and parsing, and several
tree shapes exist only under particular dialects.

**The variant enumeration.** `LangVariant` is an integer enumeration with
values `LangBash`, `LangPOSIX`, `LangMirBSDKorn`, `LangBats`, `LangZsh`, and
`LangAuto`, in that order, carrying the numeric values 1, 2, 4, 8, 16, and
32 respectively. The zero value of the type behaves as `LangBash`, and
`LangBash` is the parser's default dialect. The `String` method returns
`"bash"`, `"posix"`, `"mksh"`, `"bats"`, `"zsh"`, and `"auto"` for those
values.

**Selecting by name.** `LangVariant` has a pointer-receiver `Set` method
accepting a string so the type serves as a command-line flag value.
`Set` must accept `"bash"`, `"posix"`, `"sh"` (an alias that selects
`LangPOSIX`), `"mksh"`, `"bats"`, `"zsh"`, and `"auto"`. If any other
string is given, then `Set` must return an error whose text is
`unknown shell language variant: "NAME"` (with the rejected name quoted)
and must leave the receiver unmodified.

**Variant gating.** When the parser meets a construct that its configured
dialect does not support but another dialect does, it must fail with a
`LangError` naming the feature and the dialects that accept it (see Error
Semantics). Representative gates: array literals (`a=(1 2)`) and extended
globs (`@(a|b)`) are rejected under `LangPOSIX`; the `function` keyword is
rejected under `LangPOSIX`; the `;|` case operator is accepted only under
`LangMirBSDKorn`; `@test` blocks are accepted only under `LangBats`.
Constructs that merely look exotic but are ordinary words in a dialect
parse as plain commands there — under `LangPOSIX`, `[[ -n $x ]]` parses as
a call whose first word is `[[`, and `let x=1` parses as a call named
`let`, with no error in either case.

**Bats.** `LangBats` is a superset of Bash. When the dialect is `LangBats`
and a line begins with the word `@test`, the parser must produce a
`TestDecl` node whose `Description` is the following word and whose `Body`
is the following statement. Under any other dialect the same input must
fail to parse.

**Auto detection is not a parser mode.** If the `Variant` parser option is
given `LangAuto`, then it must panic with the message
`LangAuto is not supported by the parser at this time`.

## Parsing Shell Programs

Parsing converts a byte stream into a `*File` and reports the first
unrecoverable problem as an error value with an exact position.

**Construction and options.** `NewParser` allocates a parser and applies
any number of `ParserOption` values. A `ParserOption` is a function that
mutates a parser, so applying an option to an existing parser is done by
calling it directly, as in `syntax.KeepComments(true)(parser)`. The options
are `Variant` (dialect selection), `KeepComments` (retain comments in the
tree instead of discarding them), `StopAt` (treat a word as end-of-input),
and `RecoverErrors` (tolerate up to a maximum number of missing-token
errors). A parser is reusable: successive `Parse` calls on one instance
must each behave as on a fresh instance, though never concurrently.

**Parse.** `Parse` reads a reader to completion and returns the parsed
`*File` together with an error. The name argument is recorded in
`File.Name` and prefixes error messages; when the name is empty, error
messages carry no name prefix and begin directly with the position. An
empty input yields a `*File` with no statements whose `Pos` and `End` are
invalid positions. Reads are buffered; the reader is consumed as needed.

**Statements and separators.** A `File` holds a slice of `*Stmt`.
`Stmt.Position` is the statement's first character. `Stmt.Semicolon`
records the position of a closing `;`, `&`, or `|&` token when one ended
the statement; otherwise it is an invalid position. A trailing `&` also
sets `Stmt.Background` to true; a leading `!` sets `Stmt.Negated`; under
`LangMirBSDKorn` a closing `|&` sets `Stmt.Coprocess`. Redirections attach
to the statement's `Redirs` slice in source order.

**Comments.** By default comments are discarded. Where `KeepComments` is
enabled, the parser must attach each comment to the tree: comments on the
lines immediately preceding a statement and the comment trailing a
statement on its own line join that statement's `Comments` slice, and
comments that follow every statement in the file (or in a block) join the
enclosing node's `Last` slice. A `Comment` stores the position of its `#`
in `Hash` and the text after the `#` — excluding the `#` itself but
including any interior leading whitespace — in `Text`. A comment `# hi`
therefore has `Text` equal to `" hi"`.

**Here-documents.** A redirection with operator `<<` or `<<-` carries the
delimiter in `Word` and the body in `Hdoc`. The body word ends just before
the closing delimiter line and participates in expansion: an unquoted
delimiter yields a body with `Lit`, `ParamExp`, and other word parts, while
a quoted delimiter (`<<'EOF'`) yields a body that is a single literal part.
With `<<-`, leading tab characters are preserved in the body's literal
value. The enclosing statement's `End` extends through the here-document
body. The `<<<` operator ("here-string") sets `Word` only and leaves
`Hdoc` nil. If end of input arrives before the closing delimiter, then
parsing must fail with text ``unclosed here-document `EOF` `` (the
delimiter quoted in backquotes) and that error must report incomplete.

**Stopping early.** Where `StopAt` is configured with a word, the lexer
must treat that word — when it follows whitespace or a separating token,
matching by prefix — as the end of the input, discarding it and everything
after it. Quoted occurrences do not stop the parser. The stop word accepts
any characters except whitespace and must not exceed four bytes.

**Error recovery.** Where `RecoverErrors(n)` is configured, the parser must
tolerate up to `n` missing mandatory tokens, producing in their place nodes
or position fields whose positions report `IsRecovered()` true (and
`IsValid()` false). For example, `(foo |` parses under recovery into a
subshell whose `Rparen` is recovered and whose pipe's right operand
statement has a recovered position. With `RecoverErrors(0)` the same input
must fail with an error.

## Incremental and Fragment Parsing

Beyond whole files, the parser exposes iterator-based and callback-based
entry points for streams and for isolated fragments.

**Statement iteration.** `StmtsSeq` returns an iterator over
statement/error pairs, parsing one top-level statement at a time.
`Stmts` is the equivalent pre-iterator API: it invokes a callback per
statement and returns the terminal error, stopping early when the callback
returns false. A syntax error mid-stream ends the iteration with the
statements parsed so far followed by the error.

**Word iteration.** `WordsSeq` returns an iterator over word/error pairs,
skipping newlines between words, so multi-line input works. `Words` is the
callback form. If a token that is not a word is met — a `;`, for example —
then iteration must end with an error of text `` `;` is not a valid word ``
(the offending token quoted in backquotes).

**Fragment entry points.** `Document` parses the entire input as one
here-document body and returns the resulting `*Word` — the input behaves
as if it followed a `<<EOF` redirection, so parameter expansions are
recognized but double quotes need no escaping. `Arithmetic` parses the
entire input as one arithmetic expression, as if it appeared inside
`$((` and `))`, returning an `ArithmExpr`. Both report malformed input
with the same positioned errors as `Parse` — for example, an arithmetic
input ending after `3 +` must fail with text
``\`+\` must be followed by an expression``.

**Interactive parsing.** `InteractiveSeq` yields batches of statements as
complete lines arrive from the reader. When a line ends with all its
statements complete, the accumulated statements are yielded; when a line
ends mid-statement, an empty batch is yielded and `Incomplete` (a method
on the parser) reports true until the statement completes. `Interactive`
is the callback form: the callback receives each batch and returns whether
to continue. `Incomplete` is only meaningful while the parser is blocked
on a read.

**Incomplete input classification.** The package-level `IsIncomplete`
reports whether an error from any parsing entry point could have been
avoided by more input bytes — an unclosed quote, an unterminated `${`,
an `if` without `fi`, and similar conditions. It must return true exactly
for `ParseError` values (or pointers to them) whose `Incomplete` field is
true; it does not unwrap wrapped errors.

## The Syntax Tree

Every construct the parser recognizes has a dedicated node type; nodes
compose through small interfaces, and every node knows its exact source
extent.

**Interfaces.** `Node` is the root interface: `Pos()` returns the position
of the node's first character and `End()` returns the position immediately
after the node. Comments are ignored by both except on `*File`. When the
character after a node is a newline, `End` stays on the node's own line
rather than crossing into the next. `Command` is implemented by
`*CallExpr`, `*IfClause`, `*WhileClause`, `*ForClause`, `*CaseClause`,
`*Block`, `*Subshell`, `*BinaryCmd`, `*FuncDecl`, `*ArithmCmd`,
`*TestClause`, `*DeclClause`, `*LetClause`, `*TimeClause`,
`*CoprocClause`, and `*TestDecl`. `WordPart` is implemented by `*Lit`,
`*SglQuoted`, `*DblQuoted`, `*ParamExp`, `*CmdSubst`, `*ArithmExp`,
`*ProcSubst`, `*ExtGlob`, and `*BraceExp`. `ArithmExpr` is implemented by
`*BinaryArithm`, `*UnaryArithm`, `*ParenArithm`, and `*Word`. `TestExpr`
is implemented by `*BinaryTest`, `*UnaryTest`, `*ParenTest`, and `*Word`.
`Loop` is implemented by `*WordIter` and `*CStyleLoop`.

**Positions.** `Pos` is an opaque value constructed by
`NewPos(offset, line, column)`. `Offset()` is the byte offset starting at
0; `Line()` and `Col()` start at 1 and count bytes. A position whose line
is 0 is invalid: `IsValid()` reports false, and all three accessors return
0 for it. `String()` renders `"line:col"`, with `?` substituted for
zero-valued components — an invalid position renders `"?:?"`. `After`
reports strict positional order and returns false when the receiver is
invalid or when comparing a position to itself. `IsRecovered()` reports
true only for positions fabricated by error recovery, and such positions
are not valid.

**Files and statements.** `File` has `Name` (the string given to `Parse`),
`Stmts`, and `Last` (trailing comments). `Stmt` has `Comments`, `Cmd` (a
`Command`, nil when the statement is only redirections), `Position`,
`Semicolon`, the booleans `Negated`, `Background`, and `Coprocess`, and
`Redirs`.

**Simple commands and assignments.** `CallExpr` has `Assigns` (prefix
assignments) and `Args` (words); when `Args` is empty the assignments
stand alone. `Assign` has `Append` (`+=`), `Naked` (no `=`, as in a bare
name passed to `declare`), `Name` (a `*Lit`), `Index` (an `ArithmExpr`
for `a[i]=`), `Value` (a `*Word`), and `Array` (an `*ArrayExpr`). An
indexed assignment such as `c[1]=x` is accepted as a standalone statement;
if an inline (call-prefix) assignment uses an index, then parsing must
fail with text `inline variables cannot be arrays`. `ArrayExpr` holds
`Lparen`/`Rparen` positions, `Elems` (`*ArrayElem` with optional `Index`,
`Value`, and `Comments`), and trailing `Last` comments.

**Words and word parts.** `Word` holds contiguous `Parts`. Its `Lit`
method returns the concatenated value when every part is a `*Lit` and the
empty string otherwise — a word containing any quoted or expanded part has
no literal value. `Lit` stores `Value` plus `ValuePos`/`ValueEnd`; a
literal split by an escaped newline (`fo\` at end of line continuing with
`o`) has `Value` equal to the joined text `foo` while `ValueEnd` still
points past the original multi-line extent. `SglQuoted` stores the raw
`Value` between the quotes and a `Dollar` flag for `$'...'` (escape
sequences inside are preserved verbatim in `Value`, not decoded).
`DblQuoted` stores inner `Parts`, its `Left`/`Right` quote positions, and
a `Dollar` flag for `$"..."`. `CmdSubst` stores `Stmts`, `Last`,
`Left`/`Right`, and the booleans `Backquotes` (`` `foo` ``), `TempFile`
(`${ foo;}`), and `ReplyVar` (`${|foo;}`); the latter two forms parse
under `LangBash` and `LangMirBSDKorn`. `ArithmExp` stores `X` plus the
booleans `Bracket` (the deprecated `$[expr]` form) and `Unsigned` (mksh's
`$((# expr))`). `ProcSubst` (`<(cmd)` and `>(cmd)`, Bash only) stores
`Op`, `Rparen`, `Stmts`, and `Last`. `ExtGlob` (Bash and mksh) stores
`Op`, `OpPos`, and the raw `Pattern` literal. `BraceExp` appears only
after `SplitBraces` and stores `Sequence` plus `Elems`.

**Parameter expansions.** `ParamExp` has `Dollar` and `Rbrace` positions,
a `Short` flag (`$a` as opposed to `${a}`), the mutually exclusive flags
`Excl` (`${!a}`), `Length` (`${#a}`), and `Width` (mksh's `${%a}`), the
`Param` literal, and exactly one of the following detail fields when the
expansion has a suffix: `Index` (an `ArithmExpr` for `${a[i]}`), `Slice`
(`Offset` and `Length` expressions for `${a:x:y}`), `Repl` (a `Replace`
with `All`, `Orig`, `With` for `${a/x/y}`, `All` set by `${a//x/y}`),
`Names` (a `ParNamesOperator` for `${!prefix*}` or `${!prefix@}`, which
also sets `Excl`), or `Exp` (an `Expansion` with an operator and an
optional `Word` for `${a:-b}`, `${a##pat}`, `${a^^}`, and relatives; the
`Word` is nil when the operator takes none, as in `${a^^}`). If an
unknown operator follows the parameter — `${a!}` — then parsing must fail
with text ``not a valid parameter expansion operator: `!` ``.

**Redirections.** `Redirect` has `OpPos`, `Op`, `N` (the optional fd
literal or `{varname}` in Bash), `Word`, and `Hdoc`. In `foo 2>err`, `N`
is `2`; in `foo {fd}>named`, `N` is `{fd}`; in `foo >&2`, `N` is nil and
`Word` is `2`.

**Control flow.** `IfClause` represents `if`/`elif`/`else` chains
recursively: `Cond` and `Then` hold statement lists with `CondLast` and
`ThenLast` comment slices, `Else` points to the next `IfClause` in the
chain (an `elif` has a valid `ThenPos`, a final `else` has an invalid
one), and `FiPos` is shared by every link of the chain. `WhileClause`
covers `while` and, with `Until` set, `until`. `ForClause` covers `for`
and, with `Select` set, Bash's `select`; its `Loop` is either a
`WordIter` (`Name`, `InPos`, `Items` — an invalid `InPos` means the `in`
token was absent and the loop ranges over the positional parameters,
which is distinct from an empty `in` list where `InPos` is valid) or a
`CStyleLoop` (`Init`, `Cond`, `Post`, each possibly nil, Bash only).
`CaseClause` has `Case`/`In`/`Esac` positions, the selector `Word`, and
`Items`; each `CaseItem` has `Patterns`, `Stmts`, an `Op` — `;;`
(`Break`), `;&` (`Fallthrough`), `;;&` (`Resume`), or mksh's `;|`
(`ResumeKorn`) — and an `OpPos` that is invalid when `esac` closed the
item without an explicit operator. `Block` and `Subshell` hold `Stmts`
plus `Last` with brace and parenthesis positions. `BinaryCmd` links two
statements with `&&` (`AndStmt`), `||` (`OrStmt`), `|` (`Pipe`), or `|&`
(`PipeAll`).

**Functions and declarations.** `FuncDecl` has `RsrvWord` (declared with
the `function` keyword), `Parens` (declared with `()`; always true when
`RsrvWord` is false), `Name`, and `Body` (a statement whose command is the
function body, such as a block or subshell). `DeclClause` (Bash) has a `Variant` literal — one of `declare`,
`local`, `export`, `readonly`, `typeset`, or `nameref` — and `Args`, a
mix of regular and naked assignments where option words like `-a` appear
as naked assignments without a name. `LetClause` holds arithmetic `Exprs`.
`TimeClause` has a `PosixFormat` flag for `-p` and the timed `Stmt`.
`CoprocClause` (Bash) has an optional `Name` word — nil in `coproc foo
bar`, where the whole tail is the command — and the coprocess `Stmt`.
`TestDecl` (Bats) has `Description` and `Body`.

**Arithmetic.** `BinaryArithm` has `Op`, `OpPos`, `X`, and `Y`; operands
are themselves `ArithmExpr` values, with plain variables and numbers
appearing as `*Word`. The ternary `a ? b : c` is a `BinaryArithm` with
`Op` `TernQuest` whose `Y` is another `BinaryArithm` with `Op`
`TernColon`; `TernColon` appears in no other position. Assignment
operators require a name on the left: `$((1 += 2))` must fail with text
``\`+=\` must follow a name``. `UnaryArithm` has `Op`, `OpPos`, `Post`
(operator written after the operand, for `++` and `--`), and `X`.
`ParenArithm` wraps an expression in `Lparen`/`Rparen`.

**Test expressions.** Inside `[[ ... ]]` (`TestClause`, Bash and mksh),
`BinaryTest` and `UnaryTest` carry `Op`, `OpPos`, and operands, and
`ParenTest` wraps with parentheses. `&&` binds tighter than `||`: the
expression `a && b || c` produces a top-level `&&` node whose right
operand holds the `||`. Unary file and string operators (`-n`, `-e`, and
relatives) apply to word operands.

**Keyword and name classification.** `ValidName` reports whether a string
is a valid shell name per POSIX: it must start with a letter or
underscore and continue with letters, digits, or underscores; the empty
string is not valid. `IsKeyword` reports whether a string is a language
keyword of POSIX Shell or Bash — `if`, `then`, `elif`, `else`, `fi`,
`while`, `until`, `do`, `done`, `for`, `in`, `case`, `esac`, `function`,
`select`, `coproc`, `time`, `{`, `}`, `[[`, `]]`, and `!` are keywords;
ordinary command names are not.

## Canonical Printing

The printer renders any supported node into deterministic, canonical shell
text; formatting options vary the style without changing meaning.

**Construction and supported nodes.** `NewPrinter` allocates a printer and
applies `PrinterOption` values, which — like parser options — are
functions applicable directly to an existing printer. `Print` writes a
node to a writer, buffered. The supported node types are `*File`,
`*Stmt`, `*Word`, `*Assign`, any `Command`, and any `WordPart`. A
trailing newline is printed only for `*File`. If any other node type is
given, then `Print` must return an error whose text names the type, in
the form `unsupported node type: *syntax.Redirect`.

**Canonical style.** With no options, printing must apply these rules.
Statements that were on separate lines stay on separate lines, and a `;`
separating two statements on one line is replaced by a newline. Runs of
blank lines collapse to a single blank line. Indentation uses one tab per
nesting level. Keywords are separated by single spaces (`if true; then`,
`for x in a b; do`), and redundant whitespace between words collapses to
one space. Redirection operators attach directly to their word (`>a`),
and file-descriptor duplications keep their digits (`2>&1`). Backquoted
command substitutions are rewritten to `$(...)`. Subshells print without
inner padding (`(foo)`); braces keep their mandatory spaces (`{ foo; }`).
A multi-command block or subshell that must span lines prints one
statement per line, indented. Case items print as `pattern) body ;;` with
items on their own lines when the source spanned lines. A pipeline that
spans lines keeps the operator at the end of the line and indents the
continuation with one tab. Comments (when the tree holds them) print one
space after the code, preserving the comment text exactly, including its
interior spacing. Trailing `&` prints with a space before it. A negated
statement prints `! ` before the command. Here-document bodies and their
delimiters print verbatim on their own lines. The empty parts of the
source do not survive: printing is a projection of the tree, so two
sources that parse to equal trees print identically.

**Idempotence.** Printing must be a fixpoint under default options:
parsing canonical output and printing again yields byte-identical text.

**Indent.** `Indent(n)` switches indentation to `n` spaces per level; 0
(the default) uses tabs.

**BinaryNextLine.** Where enabled, a multi-line binary command places the
operator at the start of the continuation line, escaping the preceding
newline with a backslash: `foo \` newline, tab, `| bar`.

**SwitchCaseIndent.** Where enabled, case items are indented one level
deeper than the `case` keyword, and `esac` stays at the outer level.

**SpaceRedirects.** Where enabled, redirection operators print with a
space before their word (`foo > a`, `< in`, `>> app`); the operators `>&`,
`<&`, `>(`, and `<(` are the exceptions and stay attached to their word.

**FunctionNextLine.** Where enabled, a function's opening brace moves to
the line after the declaration: `f()`, newline, `{`, indented body, `}`.

**Minify.** Where enabled, printing must save bytes: comments are dropped,
indentation disappears, spaces around arithmetic operators vanish
(`$((x+y))`), the space after control keywords compresses (`if
true;then`), the final case item's `;;` terminator compresses to a single
`;` before `esac` while earlier items keep their operators unspaced
(`a)b;;c)d;esac`), and binary command operators join their operands
without spaces (`foo|bar&&baz`). Statements still print one per line, and
the `*File` trailing newline remains.

**SingleLine.** Where enabled, statement lists join on one line with `;`
instead of newlines; here-document bodies are the exception and still
force newlines (`cat <<EOF; foo` followed by the body on later lines).
The trailing newline for a `*File` remains.

## Word Utilities and Rewrites

Free functions inspect and rewrite words and trees outside the
parse/print cycle.

**Walk.** `Walk(node, f)` traverses depth-first: it calls `f(node)` (the
node must not be nil), and when `f` returns true it recurses into each
non-nil child and then calls `f(nil)` to mark the end of that node's
children. Every node of a parsed file is reachable this way, including
`*Word` and `*Lit` leaves.

**Quote.** `Quote(s, lang)` returns a string that any shell of the given
dialect reads back as exactly `s`. Strings that need no quoting return
unchanged. Strings with spaces or metacharacters wrap in single quotes
(`'foo bar'`, `'$foo'`, `'a=b'`, `'~foo'`); the empty string returns
`''`. A string containing a single quote switches to double quotes
(`"foo'bar"`). Under `LangBash` and `LangMirBSDKorn`, strings with
control bytes or invalid UTF-8 use dollar-quoting with escapes
(`$'foo\nbar'`, `$'\xff'`). Two failure classes exist, both returned as
`*QuoteError`: any string containing a NUL byte must be rejected with
message `shell strings cannot contain null bytes`, and under `LangPOSIX`
a string needing escape sequences must be rejected with message
`POSIX shell lacks escape sequences`. Valid multi-byte UTF-8 needs no
escaping and passes through unchanged in every dialect.

**SplitBraces.** `SplitBraces(word)` parses brace expansions within a
word's literal parts, replacing each valid expansion with a `*BraceExp`
node in place: `foo{bar,baz}` becomes a `foo` literal followed by a brace
expression with elements `bar` and `baz`. A sequence expression
`{1..10..2}` produces a `BraceExp` with `Sequence` true and the bounds
and increment as elements. Nested and repeated expansions all split
(`a{b,c}d{e,f}`). The function returns whether it changed the word's
parts at all; malformed fragments such as `a{b`, `{}`, or `{a}` produce
no `BraceExp` node — their brace characters remain as literal text, though
the literal parts they sit in are re-tokenized. A word containing no
brace character returns false and is untouched.

**Simplify.** `Simplify(node)` rewrites the tree in place to remove
redundant syntax and returns whether any change was made. The rewrites
are exactly: removing useless parentheses in arithmetic (`$(( (expr) ))`
to `$((expr))`); removing `$` from variables in arithmetic contexts
(`(($var))` to `((var))`); flattening a subshell that is the sole command
of a command substitution (`$( (stmts) )` to `$(stmts)`); removing quotes
around a variable compared inside `[[ ... ]]` (`[[ "$var" == str ]]` to
`[[ $var == str ]]`); merging a negation into a unary test operator
(`[[ ! -n $var ]]` to `[[ -z $var ]]`); and replacing a double-quoted
literal whose only escape is `\$` with a single-quoted one (`"\$foo"` to
`'$foo'`). A tree with none of these patterns returns false unchanged.

## Typed JSON Interchange

The `typedjson` subpackage (import path `mvdan.cc/sh/v3/syntax/typedjson`)
converts between syntax trees and a JSON form that annotates node types.

**Encoding.** `Encode(w, node)` writes the node as one JSON object;
`EncodeOptions` with an `Indent` string field (for example two spaces)
produces indented output via its `Encode` method, and the package-level
function is the zero-options shortcut. Every object carries its Go field
names as JSON keys. A `"Type"` key holding the node's type name (
`"File"`, `"CallExpr"`, `"Lit"`, `"Word"`, and so on) appears first in
the object for the root node and for any node stored in an
interface-typed field of its parent (a statement's `Cmd`, a word's
`Parts` elements); nodes whose concrete type is fixed by context — a
`*Stmt` inside `File.Stmts`, a `*Word` value field — carry no `"Type"`
key. Positions serialize as objects with `"Offset"`, `"Line"`, and
`"Col"` keys. `Pos` and `End` appear for every node. Zero-valued and
empty fields are omitted entirely: an invalid `Semicolon` position, a
false boolean, an empty comment slice, and an empty `Name` all leave no
key.

**Decoding.** `Decode(r)` reads one JSON object and rebuilds the typed
tree, returning it as a `Node`; `DecodeOptions` carries its `Decode`
method as the configurable form. The root object must carry `"Type"`.
Whitespace and indentation in the input are irrelevant. If the `"Type"`
value names no known node type, then decoding must fail with an error of
text `unknown type: "Nope"` (the offending name quoted). A decoded tree
is deep-equal to the tree that was encoded, positions included, and both
print identically.

## State Model

The engine's single fact source is the positioned syntax tree rooted at a
node (usually a `*File`). Every public surface is a projection of, or a
constructor for, that tree:

- **Parse** (text to tree): `Parse`, `StmtsSeq`/`Stmts`,
  `WordsSeq`/`Words`, `Document`, `Arithmetic`, `InteractiveSeq`/
  `Interactive`, governed by the dialect and parser options.
- **Print** (tree to text): `Print` under formatting options; canonical,
  deterministic, and idempotent.
- **JSON** (tree to bytes and back): `typedjson.Encode` and
  `typedjson.Decode`, lossless for structure and positions.
- **Traversal** (tree to visit sequence): `Walk`.
- **Rewrite** (tree to tree): `Simplify`, `SplitBraces`.
- **Word building** (string to shell text): `Quote`, with `ValidName` and
  `IsKeyword` as classification helpers.

Positions are the glue: every node records byte-exact `Pos`/`End`
positions derived from the original source, and both the JSON projection
and the error values expose them unchanged.

## Error Semantics

| Condition | Result |
|---|---|
| Grammar violation during any parse entry point | `ParseError` value with `Filename`, `Pos`, `Text`, `Incomplete`; message `name:line:col: text`, or `line:col: text` when the name is empty |
| Input ends where more bytes could complete the construct (unclosed quote, `${`, `$((`, `$(`, here-document, `then` without body) | same `ParseError` with `Incomplete` true; `IsIncomplete` reports true |
| Construct valid only in other dialects (array literals, extended globs, or `function f` under `LangPOSIX`) | `LangError` value with `Filename`, `Pos`, `Feature`, `Langs`, `LangUsed`; message `name:line:col: FEATURE are a bash/mksh/zsh feature; tried parsing as posix` (verb and language list per feature, e.g. `the "function" builtin is a bash feature`) |
| Keyword out of place (`then` alone, `fi` alone, `;;` outside case, `esac` outside case, `do` outside loop) | `ParseError` with texts `` `then` can only be used in an `if` ``, `` `fi` can only be used to end an `if` ``, `` `;;` can only be used in a case clause ``, `` `esac` can only be used to end a `case` ``, `` `do` can only be used in a loop `` |
| Non-word token where a word is required in `WordsSeq`/`Words` | error text `` `;` is not a valid word `` (offending token shown) |
| `;` with no preceding statement (`foo & ; bar`) | `ParseError` text `` `;` can only immediately follow a statement `` |
| Unknown parameter-expansion operator | `ParseError` text ``not a valid parameter expansion operator: `!` `` |
| Assignment operator without a name on the left in arithmetic | `ParseError` text `` `+=` must follow a name `` |
| Inline call-prefix assignment with an array index | `ParseError` text `inline variables cannot be arrays` |
| `Quote` with a NUL byte anywhere, any dialect | `*QuoteError` with `ByteOffset`, `Message` `shell strings cannot contain null bytes`; `Error()` renders `cannot quote character at byte N: MESSAGE` |
| `Quote` needing escapes under `LangPOSIX` | `*QuoteError`, `Message` `POSIX shell lacks escape sequences`, same rendering |
| `Print` on a node type outside the supported set | error text `unsupported node type: *syntax.Redirect` (the given type) |
| `typedjson.Decode` with an unknown `"Type"` value | error text `unknown type: "Nope"` (the given name) |
| `LangVariant.Set` with an unknown name | error text `unknown shell language variant: "fish"` (the given name) |
| `Variant(LangAuto)` | panic with message `LangAuto is not supported by the parser at this time` |

`ParseError` and `LangError` are returned as plain (non-pointer) error
values; `QuoteError` is returned as a pointer.

## Cross-View Invariants

1. **Print/parse round trip**: for any tree obtained from `Parse`,
   printing it and parsing the printed text must succeed and yield a tree
   that prints byte-identically — canonical output is a fixpoint of the
   parse-print cycle under any fixed set of printer options.
2. **Position/source agreement**: for every node of a tree returned by
   `Parse`, `End()` must not be positioned before `Pos()`, both positions
   must be valid for non-empty constructs, and each position's `Line` and
   `Col` must agree with counting lines and bytes up to its `Offset` in
   the original source.
3. **JSON round trip**: `typedjson.Decode` applied to the output of
   `typedjson.Encode` must reconstruct a tree deep-equal to the original,
   including every position's offset, line, and column, for any node kind
   the printer supports; printing original and reconstruction yields the
   same bytes.
4. **Walk/tree agreement**: walking a parsed file with a function that
   always returns true must invoke the function once per node and once
   with nil per node (the counts match), and every visited node's extent
   must lie within the file's extent.
5. **Quote/parse agreement**: for any string accepted by `Quote` under a
   dialect, parsing the quoted form as a shell word under that dialect
   must succeed and produce exactly one word containing no expansion
   parts; for strings quoted without escape sequences, the word's quoted
   or literal content must equal the original string.
6. **Error/position agreement**: a `ParseError`'s rendered message must be
   exactly its `Filename` (when non-empty), the `Line` and `Col` of its
   `Pos`, and its `Text`, joined with colons; the `Filename` must equal
   the name passed to `Parse`, which must equal the resulting `File.Name`.
7. **Incomplete classification**: `IsIncomplete(err)` must report true
   exactly when `err` is a `ParseError` (value or pointer) whose
   `Incomplete` field is true, across all parse entry points.
8. **Minify preserves meaning**: text printed with `Minify` enabled must
   re-parse successfully into a tree whose default-options print equals
   the default-options print of the original tree.

## Public Interface

### Import Surface

```go
import (
    "mvdan.cc/sh/v3/syntax"
    "mvdan.cc/sh/v3/syntax/typedjson"
)
```

Package `syntax` exports: functions `NewParser`, `NewPrinter`, `NewPos`,
`Walk`, `Quote`, `Simplify`, `SplitBraces`, `ValidName`, `IsKeyword`,
`IsIncomplete`; types `Parser`, `Printer`, `ParserOption`,
`PrinterOption`, `Pos`, `LangVariant`, `ParseError`, `LangError`,
`QuoteError`; parser options `Variant`, `KeepComments`, `StopAt`,
`RecoverErrors`; printer options `Indent`, `BinaryNextLine`,
`SwitchCaseIndent`, `SpaceRedirects`, `FunctionNextLine`, `Minify`,
`SingleLine`; variant constants `LangBash`, `LangPOSIX`,
`LangMirBSDKorn`, `LangBats`, `LangZsh`, `LangAuto`; the node interfaces
`Node`, `Command`, `WordPart`, `ArithmExpr`, `TestExpr`, `Loop`; the node
types listed in the API Catalog; the operator types `RedirOperator`,
`ProcOperator`, `GlobOperator`, `BinCmdOperator`, `CaseOperator`,
`ParNamesOperator`, `ParExpOperator`, `UnAritOperator`,
`BinAritOperator`, `UnTestOperator`, `BinTestOperator`, each with a
`String` method returning the operator's source text; and the operator
constants given below.

Operator constants. Redirection: `RdrOut` (`>`), `AppOut` (`>>`), `RdrIn`
(`<`), `RdrInOut` (`<>`), `DplIn` (`<&`), `DplOut` (`>&`), `RdrClob`
(`>|`), `Hdoc` (`<<`), `DashHdoc` (`<<-`), `WordHdoc` (`<<<`), `RdrAll`
(`&>`), `AppAll` (`&>>`). Process substitution: `CmdIn` (`<(`), `CmdOut`
(`>(`). Extended globs: `GlobZeroOrOne` (`?(`), `GlobZeroOrMore` (`*(`),
`GlobOneOrMore` (`+(`), `GlobOne` (`@(`), `GlobExcept` (`!(`). Binary
commands: `AndStmt` (`&&`), `OrStmt` (`||`), `Pipe` (`|`), `PipeAll`
(`|&`). Case items: `Break` (`;;`), `Fallthrough` (`;&`), `Resume`
(`;;&`), `ResumeKorn` (`;|`). Name listing: `NamesPrefix` (`*`),
`NamesPrefixWords` (`@`). Parameter expansion: `AlternateUnset` (`+`),
`AlternateUnsetOrNull` (`:+`), `DefaultUnset` (`-`), `DefaultUnsetOrNull`
(`:-`), `ErrorUnset` (`?`), `ErrorUnsetOrNull` (`:?`), `AssignUnset`
(`=`), `AssignUnsetOrNull` (`:=`), `RemSmallSuffix` (`%`),
`RemLargeSuffix` (`%%`), `RemSmallPrefix` (`#`), `RemLargePrefix` (`##`),
`UpperFirst` (`^`), `UpperAll` (`^^`), `LowerFirst` (`,`), `LowerAll`
(`,,`), `OtherParamOps` (`@`). Unary arithmetic: `Not` (`!`),
`BitNegation` (`~`), `Inc` (`++`), `Dec` (`--`), `Plus` (`+`), `Minus`
(`-`). Binary arithmetic: `Add`, `Sub`, `Mul`, `Quo`, `Rem`, `Pow`
(`**`), `Eql` (`==`), `Gtr`, `Lss`, `Neq`, `Leq`, `Geq`, `And`, `Or`,
`Xor`, `Shr` (`>>`), `Shl` (`<<`), `AndArit` (`&&`), `OrArit` (`||`),
`Comma`, `TernQuest` (`?`), `TernColon` (`:`), `Assgn` (`=`), `AddAssgn`
(`+=`), `SubAssgn`, `MulAssgn`, `QuoAssgn`, `RemAssgn`, `AndAssgn`,
`OrAssgn`, `XorAssgn`, `ShlAssgn`, `ShrAssgn`. Unary test: `TsExists`
(`-e`), `TsRegFile` (`-f`), `TsDirect` (`-d`), `TsCharSp` (`-c`),
`TsBlckSp` (`-b`), `TsNmPipe` (`-p`), `TsSocket` (`-S`), `TsSmbLink`
(`-L`), `TsSticky` (`-k`), `TsGIDSet` (`-g`), `TsUIDSet` (`-u`),
`TsGrpOwn` (`-G`), `TsUsrOwn` (`-O`), `TsModif` (`-N`), `TsRead` (`-r`),
`TsWrite` (`-w`), `TsExec` (`-x`), `TsNoEmpty` (`-s`), `TsFdTerm`
(`-t`), `TsEmpStr` (`-z`), `TsNempStr` (`-n`), `TsOptSet` (`-o`),
`TsVarSet` (`-v`), `TsRefVar` (`-R`), `TsNot` (`!`), `TsParen` (`(`).
Binary test: `TsReMatch` (`=~`), `TsNewer` (`-nt`), `TsOlder` (`-ot`),
`TsDevIno` (`-ef`), `TsEql` (`-eq`), `TsNeq` (`-ne`), `TsLeq` (`-le`),
`TsGeq` (`-ge`), `TsLss` (`-lt`), `TsGtr` (`-gt`), `AndTest` (`&&`),
`OrTest` (`||`), `TsMatchShort` (`=`), `TsMatch` (`==`), `TsNoMatch`
(`!=`), `TsBefore` (`<`), `TsAfter` (`>`).

Package `typedjson` exports the functions `Encode` and `Decode` and the
types `EncodeOptions` (field `Indent`) and `DecodeOptions`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `NewParser` | function | build a parser with options |
| `Parser` | struct | parsing state; methods `Parse`, `Stmts`, `StmtsSeq`, `Words`, `WordsSeq`, `Document`, `Arithmetic`, `Interactive`, `InteractiveSeq`, `Incomplete` |
| `ParserOption` | function type | parser configuration value |
| `Variant` | function | option: select the shell dialect |
| `KeepComments` | function | option: retain comments in the tree |
| `StopAt` | function | option: treat a word as end of input |
| `RecoverErrors` | function | option: tolerate missing tokens |
| `NewPrinter` | function | build a printer with options |
| `Printer` | struct | printing state; method `Print` |
| `PrinterOption` | function type | printer configuration value |
| `Indent` | function | option: spaces per indent level |
| `BinaryNextLine` | function | option: operators lead continuation lines |
| `SwitchCaseIndent` | function | option: indent case items |
| `SpaceRedirects` | function | option: space after redirect operators |
| `FunctionNextLine` | function | option: opening brace on next line |
| `Minify` | function | option: print with minimal bytes |
| `SingleLine` | function | option: join statements on one line |
| `Pos` | struct | source position; methods `Offset`, `Line`, `Col`, `After`, `IsValid`, `IsRecovered`, `String` |
| `NewPos` | function | build a position from offset, line, column |
| `LangVariant` | int type | shell dialect; methods `String`, `Set` |
| `ParseError` | struct | positioned parse failure; method `Error` |
| `LangError` | struct | dialect-gated feature failure; method `Error` |
| `QuoteError` | struct | quoting failure; method `Error` |
| `IsIncomplete` | function | classify an error as needing more input |
| `Walk` | function | depth-first traversal with nil terminators |
| `Quote` | function | render a string as a safe shell word |
| `Simplify` | function | remove redundant syntax in place |
| `SplitBraces` | function | expand brace syntax into `BraceExp` nodes |
| `ValidName` | function | POSIX name check |
| `IsKeyword` | function | shell keyword check |
| `Node` | interface | `Pos`/`End` pair on every node |
| `Command` | interface | statement command nodes |
| `WordPart` | interface | word component nodes |
| `ArithmExpr` | interface | arithmetic expression nodes |
| `TestExpr` | interface | test expression nodes |
| `Loop` | interface | for-clause loop kinds |
| `File` | struct | root node: `Name`, `Stmts`, `Last` |
| `Stmt` | struct | statement with redirections and flags |
| `Comment` | struct | one comment: `Hash`, `Text` |
| `CallExpr` | struct | simple command: `Assigns`, `Args` |
| `Assign` | struct | variable assignment |
| `Redirect` | struct | input/output redirection |
| `Word` | struct | contiguous word parts; method `Lit` |
| `Lit` | struct | literal text with value positions |
| `SglQuoted` | struct | single-quoted string, optional `$'...'` |
| `DblQuoted` | struct | double-quoted parts, optional `$"..."` |
| `ParamExp` | struct | parameter expansion |
| `Slice` | struct | `${a:x:y}` offset/length pair |
| `Replace` | struct | `${a/x/y}` search and replace |
| `Expansion` | struct | operator-plus-word expansion detail |
| `CmdSubst` | struct | command substitution |
| `ArithmExp` | struct | `$((expr))` expansion |
| `ArithmCmd` | struct | `((expr))` command |
| `ProcSubst` | struct | process substitution |
| `ExtGlob` | struct | extended glob pattern |
| `BraceExp` | struct | brace expansion after `SplitBraces` |
| `IfClause` | struct | if/elif/else chain |
| `WhileClause` | struct | while/until loop |
| `ForClause` | struct | for/select loop |
| `WordIter` | struct | `for x in ...` iteration |
| `CStyleLoop` | struct | `for ((init; cond; post))` |
| `CaseClause` | struct | case selector and items |
| `CaseItem` | struct | one case pattern list |
| `Block` | struct | `{ ...; }` command list |
| `Subshell` | struct | `( ... )` command list |
| `FuncDecl` | struct | function declaration |
| `BinaryCmd` | struct | and/or/pipe operators between two statements |
| `DeclClause` | struct | declare/local/export/readonly/typeset/nameref |
| `LetClause` | struct | `let` arithmetic expressions |
| `TimeClause` | struct | `time` wrapper |
| `CoprocClause` | struct | `coproc` declaration |
| `TestClause` | struct | `[[ ... ]]` test command |
| `TestDecl` | struct | Bats `@test` declaration |
| `BinaryArithm` | struct | binary/ternary arithmetic |
| `UnaryArithm` | struct | unary arithmetic, pre or post |
| `ParenArithm` | struct | parenthesized arithmetic |
| `BinaryTest` | struct | binary test expression |
| `UnaryTest` | struct | unary test expression |
| `ParenTest` | struct | parenthesized test expression |
| `ArrayExpr` | struct | array literal |
| `ArrayElem` | struct | one array element |
| `RedirOperator` | token type | redirection operators |
| `ProcOperator` | token type | process substitution operators |
| `GlobOperator` | token type | extended glob operators |
| `BinCmdOperator` | token type | binary command operators |
| `CaseOperator` | token type | case item terminators |
| `ParNamesOperator` | token type | `${!p*}` vs `${!p@}` |
| `ParExpOperator` | token type | parameter expansion operators |
| `UnAritOperator` | token type | unary arithmetic operators |
| `BinAritOperator` | token type | binary arithmetic operators |
| `UnTestOperator` | token type | unary test operators |
| `BinTestOperator` | token type | binary test operators |
| `typedjson.Encode` | function | tree to typed JSON |
| `typedjson.Decode` | function | typed JSON to tree |
| `typedjson.EncodeOptions` | struct | encoding options: `Indent` |
| `typedjson.DecodeOptions` | struct | decoding options |

### CLI Entry Points

There is no console script for this module. Programmatic use is through Go
imports.

## Appendix A: Environment

The working environment runs Go 1.25 or newer on Linux without network
access beyond the Go module proxy. The delivery must be a Go module with
module path `mvdan.cc/sh/v3` so that callers import
`mvdan.cc/sh/v3/syntax` and `mvdan.cc/sh/v3/syntax/typedjson` as shown in
this document. No third-party runtime dependencies are required; the
standard library suffices.

## Appendix B: Assessment Notes

Correctness is exercised through compiled Go test programs that import the
module by its public paths. Tests are grouped in two suites: one asserts
single behaviors in isolation (one node shape, one position value, one
error's text and type, one printer rule, one quoting case), the other
drives multi-step workflows spanning several projections (parse, print,
re-parse, JSON encode and decode, walk, and quote together) and checks the
cross-view invariants above. Expected values in tests come from this
document's stated behavior; error-message assertions use the exact shapes
given in Error Semantics, and position assertions count bytes and lines in
the test's own input strings. Shell sources used by tests are
self-contained string literals — no fixture files.
