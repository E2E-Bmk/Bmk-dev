# Pyparsing Specification

## Product Overview

Pyparsing is a pure Python library for constructing and running text parsers directly in Python code. A parser is built by composing `ParserElement` objects such as `Word`, `Literal`, `Regex`, `QuotedString`, `Group`, `Forward`, and repetition or alternative expressions. The same expression can then parse a whole string, scan through a larger string, transform matched text, or return structured parse results.

Pyparsing grammars are ordinary Python objects. Literal strings used in expression composition are automatically converted to literal parser elements, so grammar definitions can combine parser objects and string punctuation naturally. Parsing normally skips whitespace between expressions unless the grammar opts into whitespace-sensitive behavior.

## Scope

This specification covers the core public behavior needed to implement practical pyparsing grammars:

- parser expression construction and composition;
- token classes, expression classes, lookahead, repetition, grouping, suppression, and recursive grammar placeholders;
- parsing entry points such as `parse_string`, `parse_file`, `scan_string`, `search_string`, `transform_string`, `split`, and `run_tests`;
- result naming, parse actions, parse conditions, and the `ParseResults` container;
- parse exception classes and diagnostic attributes;
- common helper constructors and parse actions;
- `pyparsing.common`, `pyparsing.unicode`, and `pyparsing.testing` public helper namespaces;
- the `pyparsing.util` public utility submodule for source-location helpers;
- basic railroad diagram generation hooks when the optional diagram dependency is installed.

The specification focuses on user-visible behavior. It does not prescribe internal parser storage, cache layout, railroad object internals, exact debug text, or exact warning message wording.

## Installable Surface

The package import name is `pyparsing`. Users commonly import it as:

```python
import pyparsing as pp
```

The package must support `from pyparsing import Name` for the exported public names listed below.
Public helper submodules such as `pyparsing.util`, `pyparsing.testing`, `pyparsing.common`, `pyparsing.unicode`, and `pyparsing.diagram` are importable by module path as well as through their top-level aliases.

Core classes:

```text
ParserElement, Token, ParseExpression, ParseElementEnhance, TokenConverter
Literal, CaselessLiteral, Keyword, CaselessKeyword, Word, Char, Regex, QuotedString,
White, CharsNotIn, CloseMatch, Empty, NoMatch
And, MatchFirst, Or, Each
Opt, Optional, ZeroOrMore, OneOrMore, DelimitedList, SkipTo, Forward,
Group, Dict, Suppress, Combine, Located, Tag, IndentedBlock
FollowedBy, NotAny, PrecededBy, AtLineStart, AtStringStart
PositionToken, LineStart, LineEnd, StringStart, StringEnd, WordStart, WordEnd, GoToColumn
ParseResults
ParseBaseException, ParseException, ParseFatalException, ParseSyntaxException,
RecursiveGrammarException
OnlyOnce, OpAssoc
PyparsingWarning, PyparsingDeprecationWarning, PyparsingDiagnosticWarning
unicode_set, UnicodeRangeList, pyparsing_unicode, pyparsing_common, pyparsing_test, testing
```

Helper functions and parser constants:

```text
one_of, infix_notation, nested_expr, original_text_for, ungroup, counted_array,
dict_of, make_html_tags, make_xml_tags, match_previous_literal, match_previous_expr,
delimited_list, condition_as_parse_action, match_only_at_col,
remove_quotes, replace_with, replace_html_entity, with_attribute, with_class,
token_map, trace_parse_action, null_debug_action, autoname_elements, srange,
lineno, col, line, show_best_practices

alphas, nums, alphanums, alphas8bit, punc8bit, printables, hexnums,
identchars, identbodychars, empty, quoted_string, sgl_quoted_string,
dbl_quoted_string, unicode_string, rest_of_line,
line_start, line_end, string_start, string_end,
c_style_comment, cpp_style_comment, java_style_comment, python_style_comment,
dbl_slash_comment, html_comment, common_html_entity, any_open_tag, any_close_tag
```

PEP 8 snake_case names are the preferred public spelling. The package also exposes deprecated pre-PEP8 compatibility aliases such as `parseString`-style method aliases, `enablePackrat`, `enableLeftRecursion`, `disableMemoization`, `resetCache`, and module-level names including `oneOf`, `delimitedList`, `infixNotation`, `nestedExpr`, `originalTextFor`, `removeQuotes`, `replaceWith`, `withAttribute`, `withClass`, `lineStart`, `lineEnd`, `stringStart`, `stringEnd`, `restOfLine`, `cStyleComment`, `cppStyleComment`, `htmlComment`, `quotedString`, `sglQuotedString`, `dblQuotedString`, `pyparsing_common`/`common`, `pyparsing_unicode`/`unicode`, and `pyparsing_test`/`testing`. Compatibility aliases should behave like their snake_case counterparts, although applications should prefer the snake_case names.

The optional diagram module is importable as `pyparsing.diagram` when its external diagram dependency is available. It provides diagram conversion helpers such as `to_railroad` and `railroad_to_html`, and `ParserElement.create_diagram` can write HTML for a grammar.

The utility module is importable as `pyparsing.util`. It exposes `col`, `line`, and `lineno`; these are the same source-location helper functions exported at the top level.

`show_best_practices(file=sys.stdout)` prints pyparsing usage guidance to the given file object. If `file=None`, it returns the guidance text as a string. The same guidance is available from the command line with:

```bash
python -m pyparsing.ai.show_best_practices
```

## Public API

### ParserElement Lifecycle

`ParserElement` is the base object for grammar expressions. Users normally create subclasses and compose them into larger expressions, then run one of the parsing methods on the final expression.

Important methods include:

```python
parse_string(instring: str, parse_all: bool = False, **kwargs) -> ParseResults
parse_file(file_or_filename, encoding: str = "utf-8", parse_all: bool = False, **kwargs) -> ParseResults
scan_string(instring: str, max_matches=sys.maxsize, overlap: bool = False,
            always_skip_whitespace=True, *, debug: bool = False, **kwargs)
search_string(instring: str, max_matches=sys.maxsize, *, debug: bool = False, **kwargs) -> ParseResults
transform_string(instring: str, *, debug: bool = False) -> str
split(instring: str, maxsplit=sys.maxsize, include_separators: bool = False, **kwargs)
run_tests(tests, parse_all=True, comment="#", full_dump=True, print_results=True,
          failure_tests=False, post_parse=None, file=None, with_line_numbers=False) -> tuple[bool, list]
set_name(name: str) -> ParserElement
set_results_name(name: str, list_all_matches: bool = False) -> ParserElement
set_parse_action(*fns, call_during_try: bool = False, **kwargs) -> ParserElement
add_parse_action(*fns, call_during_try: bool = False, **kwargs) -> ParserElement
add_condition(*fns, call_during_try: bool = False, **kwargs) -> ParserElement
copy() -> ParserElement
suppress() -> ParserElement
ignore(expr) -> ParserElement
ignore_whitespace(recursive: bool = True) -> ParserElement
leave_whitespace(recursive: bool = True) -> ParserElement
set_whitespace_chars(chars, copy_defaults: bool = False) -> ParserElement
parse_with_tabs() -> ParserElement
enable_packrat(cache_size_limit=128, *, force=False) -> None
enable_left_recursion(cache_size_limit=None, *, force=False) -> None
disable_memoization() -> None
reset_cache() -> None
```

`parse_string` parses from the beginning of the input. When `parse_all=True`, it requires the expression to consume the full input and raises `ParseException` on trailing unmatched text. `parse_file` reads a filename, path object, or file-like object and parses its contents using the same `parse_all` behavior.

`scan_string` yields `(tokens, start, end)` triples for matches found throughout an input string. `search_string` returns the tokens from each scan match as a `ParseResults` collection. `transform_string` scans the input and replaces matched text with the output from parse actions. `split` yields the unmatched pieces of the input, optionally including matched separators.

`run_tests` accepts a multiline string or list of sample strings, parses each sample, prints readable success or failure output unless `print_results=False`, and returns `(success, results)`, where `success` is a boolean and `results` contains `(test_string, outcome)` pairs. Lines beginning with the comment marker are treated as comments in the test report.

`set_results_name("name")` returns a copy of the expression with that result name; it does not mutate the original expression. Calling an expression as `expr("name")` is a shortcut for naming a copy. A name ending in `*` behaves as `list_all_matches=True`. Calling `expr()` with no arguments is a shortcut for `expr.copy()`.

`ParserElement.enable_packrat()` enables memoizing packrat parsing for subsequently parsed expressions. `ParserElement.enable_left_recursion()` enables support for left-recursive grammars using a separate cache; packrat parsing and left-recursion parsing are incompatible modes unless explicitly forced by the caller. `ParserElement.disable_memoization()` disables both memoization modes and clears parser caches. `ParserElement.reset_cache()` clears parser caches without changing the grammar definition.

`set_parse_action` replaces existing parse actions. `add_parse_action` appends to them. `set_parse_action(None)` clears parse actions. Parse action callables may use any of these signatures:

```python
fn(source_string, location, tokens)
fn(location, tokens)
fn(tokens)
fn()
```

Parse actions may return replacement tokens, mutate the supplied `ParseResults` in place, or raise a parse exception. `add_condition` attaches validators that return true or false; false conditions raise parse exceptions, or fatal parse exceptions when configured as fatal.

### Expression Construction

Token expressions match a piece of text at the current parse location:

- `Literal(match_string)` matches the exact string and returns that string.
- `CaselessLiteral(match_string)` matches without regard to case and returns the defining literal text.
- `Keyword(match_string, ident_chars=None, caseless=False)` matches a complete keyword only when the surrounding characters are not keyword characters.
- `CaselessKeyword` is the case-insensitive keyword form.
- `Word(init_chars, body_chars=None, min=1, max=0, exact=0, as_keyword=False, exclude_chars=None)` matches one contiguous word. `init_chars` controls the first character, `body_chars` controls following characters, `exact` overrides `min` and `max`, and `exclude_chars` removes characters from the accepted set.
- `Char(charset, as_keyword=False, exclude_chars=None)` is a single-character word.
- `CharsNotIn(not_chars, min=1, max=0, exact=0)` matches contiguous characters outside the excluded set.
- `CloseMatch(match_string, max_mismatches=None, caseless=False)` matches a string while allowing a bounded number of mismatched characters and reports mismatch locations in the returned tokens.
- `Regex(pattern, flags=0, as_group_list=False, as_match=False)` matches a Python regular expression at the current parse location. Named regex groups become named parse results unless `as_match=True` returns the match object.
- `QuotedString(quote_char, esc_char=None, esc_quote=None, multiline=False, unquote_results=True, end_quote_char=None, convert_whitespace_escapes=True)` parses quoted strings, supports distinct start/end delimiters, escaped delimiters, multiline strings when enabled, and optional unquoting.
- `White(ws=" \t\r\n", min=1, max=0, exact=0)` matches explicit whitespace. Ordinary grammars usually do not need it because whitespace is skipped by default.
- `Empty()` always matches without consuming input. `NoMatch()` never matches.

Expression classes combine other expressions:

- `And([...])` or `expr1 + expr2` requires all expressions in sequence.
- `expr1 - expr2` is a committed sequence: after the left expression matches, later mismatch raises `ParseSyntaxException` instead of backtracking to other alternatives.
- `MatchFirst([...])` or `expr1 | expr2` tries alternatives from left to right and uses the first successful match.
- `Or([...])` or `expr1 ^ expr2` evaluates alternatives and selects the one with the longest match; ties prefer the leftmost expression.
- `Each([...])` or `expr1 & expr2` requires all expressions but accepts them in any order.
- `Opt(expr, default=...)` and `Optional` make an expression optional. If a default is supplied, it is returned when the expression is absent.
- `ZeroOrMore(expr, stop_on=None)` and `OneOrMore(expr, stop_on=None)` repeat an expression. Slice syntax provides shorthand: `expr[...]` means zero or more, and `expr[1, ...]` means one or more.
- `expr * n` repeats an expression exactly `n` times. `expr[min, max]`, `expr[min, ...]`, and `expr[..., max]` build bounded or open-ended repetition. Repetition with a stop expression can be written with slice syntax such as `expr[...:end_expr]`.
- `DelimitedList(expr, delim=",", combine=False, min=None, max=None, allow_trailing_delim=False)` parses delimited lists. Delimiters are suppressed by default. With `combine=True`, the matched expressions and delimiters are returned as one combined token.
- `SkipTo(expr, include=False, ignore=None, fail_on=None)` consumes text up to another expression. `...` between expressions is shorthand for a `SkipTo` leading to the next expression.

Converter and structural expressions shape returned tokens:

- `Suppress(expr)` or `expr.suppress()` matches but removes the expression's tokens from results.
- `Combine(expr, join_string="", adjacent=True)` combines tokens into a single string. With `adjacent=True`, intervening whitespace prevents the combined match.
- `Group(expr, aslist=False)` nests matched tokens. With `aslist=True`, the nested value is a plain list rather than `ParseResults`.
- `Dict(expr, asdict=False)` builds dictionary-style results from grouped rows whose first item is the key. With `asdict=True`, the returned grouped value is a plain dict.
- `Located(expr)` returns location metadata around the matched expression.
- `Tag(tag_name, value=True)` injects a named result without consuming input.
- `Forward()` creates a placeholder for recursive grammars. Assign the contained expression with `<<=`; this spelling is preferred over `<<` because Python operator precedence can otherwise surprise users.
- `IndentedBlock(expr, recursive=False, grouped=True)` parses indentation-based blocks of one or more statements.

Lookahead and position expressions control where matches can occur:

- `FollowedBy(expr)` requires the expression at the current location without consuming it.
- `NotAny(expr)` or `~expr` fails if the expression matches at the current location and does not consume input.
- `PrecededBy(expr, retreat=0)` requires an expression before the current location.
- `StringStart`, `StringEnd`, `LineStart`, `LineEnd`, `WordStart`, `WordEnd`, `AtStringStart`, `AtLineStart`, and `GoToColumn` enforce input, line, word, or column boundaries.

### Whitespace, Tabs, Comments, and Ignored Text

By default, parser elements skip spaces, tabs, newlines, and carriage returns before matching. `ParserElement.set_default_whitespace_chars(chars)` changes the default whitespace for expressions created afterward. `expr.set_whitespace_chars(chars)` changes whitespace for a specific expression. `expr.leave_whitespace(recursive=True)` disables pre-match whitespace skipping for an expression. `expr.ignore_whitespace(recursive=True)` re-enables pre-match whitespace skipping for an expression. For expression containers and enhanced expressions, the `recursive=True` default applies the whitespace setting to child expressions as well. `expr.parse_with_tabs()` prevents tab expansion before parsing.

`expr.ignore(comment_expr)` tells an expression to ignore matching comment or quoted-text patterns while parsing. It can be called repeatedly. Common comment expressions include `c_style_comment`, `cpp_style_comment`, `java_style_comment`, `python_style_comment`, `dbl_slash_comment`, and `html_comment`.

### ParseResults

`ParseResults` is the container returned by parsing. It behaves like a list of matched tokens, a mapping of named tokens, and an object with named attributes.

Important methods include:

```python
as_list(*, flatten: bool = False) -> list
as_dict() -> dict
dump(indent="", full=True, include_list=True) -> str
get(key, default_value=None)
keys()
items()
copy()
```

List behavior:

- `len(result)`, indexing, negative indexing, slicing, deletion, iteration, and `pop(index)` operate on positional tokens.
- `Group` creates nested `ParseResults` values unless constructed with `aslist=True`.
- `as_list()` converts the token tree to ordinary Python lists. With `flatten=True`, nested token lists are flattened into a single list.

Mapping and attribute behavior:

- Named results can be read with `result["name"]`, `result.name`, `result.get("name")`, `result.keys()`, and `result.items()`.
- Missing attribute-style access returns an empty string.
- `as_dict()` returns named results as a plain dictionary, recursively converting named nested results.
- Named values can be assigned or deleted using mapping syntax, including inside parse actions.
- If the same results name appears multiple times, the default visible named value is the last match. `list_all_matches=True` preserves all matches under that name.

`dump()` produces a readable display containing the positional list and named fields. The exact formatting of `dump()` is for human inspection; program logic should use list, dict, and attribute access instead.

### Helper Constructors

`one_of(choices, caseless=False, use_regex=True, as_keyword=False)` builds an efficient alternative expression from a list of strings or a whitespace-delimited string. Longer alternatives are attempted before shorter alternatives so that a prefix token does not mask a longer token. With `caseless=True`, alternatives match case-insensitively. With `as_keyword=True`, alternatives are keyword expressions instead of literals.

`infix_notation(base_expr, op_list, lpar=Suppress("("), rpar=Suppress(")"))` builds a parser for operator-precedence expressions. Each operator tuple describes the operator expression, arity `1`, `2`, or `3`, associativity `OpAssoc.LEFT` or `OpAssoc.RIGHT`, and an optional parse action. `lpar` and `rpar` may be strings, which are converted to suppressed literals, or parser expressions, which are retained according to their own behavior.

`nested_expr(opener="(", closer=")", content=None, ignore_expr=quoted_string)` parses nested delimiter pairs. When `content` is omitted, whitespace-delimited content is returned in nested lists. `ignore_expr` prevents delimiters inside quoted strings or other ignored expressions from affecting nesting; pass `None` to disable ignored expressions.

`counted_array(expr, int_expr=None)` parses a leading count followed by exactly that many occurrences of `expr`; the count is suppressed from returned tokens. `dict_of(key, value)` builds a dictionary-style repeated key/value parser. `original_text_for(expr, as_string=True)` returns the original text matched by an expression, preserving text that may otherwise be suppressed or transformed. `ungroup(expr)` removes a grouping layer from returned tokens.

`make_html_tags(tag)` and `make_xml_tags(tag)` return `(start_tag, end_tag)` expressions. Opening tags return attributes as named results. The HTML helper is less strict about case and syntax than the XML helper.

`match_previous_literal(expr)` matches the exact literal text previously matched by `expr`. `match_previous_expr(expr)` reparses and compares expression results, so it can distinguish cases where literal prefix matching would be too permissive.

### Helper Parse Actions

`remove_quotes` removes the first and last characters from a quoted token. `replace_with(value)` returns a parse action that replaces matched tokens with `value`. `token_map(func, *args)` maps a callable over matched tokens. `trace_parse_action(fn)` wraps a parse action and reports calls, returns, and exceptions for debugging. `match_only_at_col(n)` validates that a match occurs at a specific 1-based column and raises `ParseException` otherwise.

`with_attribute(*args, **attr_dict)` creates a validating parse action for tags returned by `make_html_tags` or `make_xml_tags`. It accepts keyword attribute requirements or `(name, value)` tuples. `with_attribute.ANY_VALUE` requires the attribute to exist regardless of value. `with_class(classname, namespace="")` is a shortcut for matching an HTML/XML class attribute.

`OnlyOnce(fn)` wraps a parse action so it can be called successfully only once until reset. `condition_as_parse_action(fn, message=None, fatal=False)` converts a boolean validation function into a parse action that raises a parse exception when false.

### Common Constants and Namespaces

String constants:

- `alphas` is ASCII letters.
- `nums` is ASCII digits.
- `alphanums` is `alphas + nums`.
- `hexnums` is hexadecimal digit characters.
- `printables` is printable ASCII without space.
- `identchars` and `identbodychars` are identifier-start and identifier-body character sets.

Parser constants:

- `empty` is a global `Empty()`.
- `quoted_string` matches single- or double-quoted strings; `sgl_quoted_string` and `dbl_quoted_string` are the corresponding individual forms.
- `rest_of_line` matches printable text up to the next newline.
- `line_start`, `line_end`, `string_start`, and `string_end` are global boundary expressions.
- `common_html_entity`, `any_open_tag`, and `any_close_tag` support simple HTML/XML scanning.

`pyparsing.common` and its aliases `common` and `pyparsing_common` provide reusable parser expressions and parse actions:

- numeric expressions: `integer`, `signed_integer`, `hex_integer`, `fraction`, `mixed_integer`, `real`, `sci_real`, `number`, `fnumber`, and `ieee_float`;
- identifiers and separated data: `identifier` and `comma_separated_list`;
- network and structured strings: `ipv4_address`, `ipv6_address`, `mac_address`, `url`, and `uuid`;
- date/time expressions: `iso8601_date`, `iso8601_datetime`, `iso8601_date_validated`, and `iso8601_datetime_validated`;
- parse actions: `convert_to_integer`, `convert_to_float`, `convert_to_date`, `convert_to_datetime`, `strip_html_tags`, `downcase_tokens`, and `upcase_tokens`.

Common numeric expressions convert returned tokens to the documented Python numeric type. Date and datetime conversion helpers return `datetime.date` or `datetime.datetime` objects for inputs matching the configured format.

`pyparsing.unicode` and its aliases `unicode` and `pyparsing_unicode` provide Unicode character ranges with `.alphas`, `.nums`, `.alphanums`, `.identchars`, `.identbodychars`, `.printables`, and `.identifier` helpers. Named ranges include `Latin1`, `LatinA`, `LatinB`, `Greek`, `Cyrillic`, `Chinese`, `Japanese`, `Korean`, `CJK`, `Arabic`, `Hebrew`, `Devanagari`, `Thai`, `Hangul`, `BMP`, and `BasicMultilingualPlane`, plus documented native-name aliases.

`pyparsing.util` provides source-location helpers for parser diagnostics. `lineno(loc, strg)` returns the 1-based line number containing the zero-based character location `loc`. `col(loc, strg)` returns the 1-based column number within that line. `line(loc, strg)` returns the full text of the line containing `loc`, without the trailing newline. The same functions are available as top-level `pyparsing.lineno`, `pyparsing.col`, and `pyparsing.line`.

`pyparsing.testing` and its aliases `pyparsing_test` and `testing` provide testing helpers for parser development. `reset_pyparsing_context` is a context manager that restores global pyparsing parser settings after a test block, including whitespace, keyword characters, parser cache mode, literal auto-conversion, and diagnostic flags.

`pyparsing_test.reset_pyparsing_context()` also supports explicit saved-context lifecycle methods. `save()` captures the current global parser settings and returns the context object. `restore()` restores the most recently saved settings and returns the context object. `copy()` returns an independent context object with the same saved settings. Entering the object as a context manager is equivalent to calling `save()`, and exiting it calls `restore()`.

`pyparsing_test.TestParseResultsAsserts` is a `unittest.TestCase` mixin for parser tests. It provides assertion helpers that parse an expression and compare the resulting `ParseResults` by public list and dict views:

```python
assertParseResultsEquals(result, expected_list=None, expected_dict=None, msg=None)
assertParseAndCheckList(expr, test_string, expected_list, msg=None, verbose=True)
assertParseAndCheckDict(expr, test_string, expected_dict, msg=None, verbose=True)
assertRunTestResults(run_tests_report, expected_parse_results=None, msg=None)
```

These helpers use `parse_string(..., parse_all=True)`, `ParseResults.as_list()`, and `ParseResults.as_dict()` for comparison. They do not require callers to inspect private parser state.

### Diagrams

When the optional diagram dependency is installed, `ParserElement.create_diagram(output_html=..., embed=False, **kwargs)` writes railroad diagram HTML for an expression. With `embed=False`, it writes a complete HTML document. With `embed=True`, it writes embeddable body content rather than a full document. `pyparsing.diagram.to_railroad(expr, show_results_names=False, **kwargs)` converts an expression to named diagram objects, and `railroad_to_html(diagrams, **kwargs)` renders them as HTML.

Diagram APIs should preserve grammar names and results-name annotations at a behavioral level. Exact HTML formatting, generated CSS, object graph layout from the external railroad package, and incidental counts of internal diagram nodes are not part of the parsing contract.

## Error Semantics

`ParseBaseException` is the base for parsing exceptions and exposes:

```python
loc
msg
line
lineno
column
mark_input_line(marker_string=None, **kwargs) -> str
explain(depth=16) -> str
```

Locations are zero-based offsets into the input string. `lineno` and `column` are 1-based user-facing positions. `line` is the input line containing the error. `mark_input_line()` returns that line annotated at the error column, and `explain()` returns a readable diagnostic with context.

`ParseException` is raised for ordinary parse failures. `ParseFatalException` signals a semantic or fatal parse error and stops alternative searching. `ParseSyntaxException` is a fatal syntax exception produced by committed sequences built with `-`. `RecursiveGrammarException` is raised by deprecated grammar validation for grammars that contain infinitely recursive constructs.

Parse actions may raise parse exceptions directly. Unexpected `IndexError` or `KeyError` from parse actions is treated as a parse failure and reraised as `ParseException` by parsing methods.

## Cross-View Invariants

- A grammar that succeeds through `parse_string` returns the same token values that its `scan_string` match reports for the same span.
- A result name assigned with `expr("name")` is visible through item access, attribute access, `get`, `keys`/`items`, `as_dict`, and `dump`.
- Suppressed punctuation can still be required for matching while remaining absent from `ParseResults.as_list()` and `ParseResults.as_dict()`.
- A parse action that converts tokens affects `parse_string`, `scan_string`, `search_string`, and `transform_string` consistently for the same expression.
- Whitespace rules attached to an expression affect every parsing entry point that uses that expression.
- `Group` and `Dict` change the visible result structure without changing the input span that the underlying expression matches.
- `MatchFirst` and `Or` may accept the same alternatives but differ observably when more than one alternative can match; `MatchFirst` uses first success, while `Or` prefers longest match.
- `Forward` expressions behave like the expression assigned with `<<=` once assigned; result names and parse actions applied to the placeholder remain part of the public grammar behavior.
- Common helper expressions are ordinary parser elements: they can be named, grouped, repeated, suppressed, combined, used in larger expressions, and given parse actions.

## Representative Workflows

### Greeting Parser

```python
import pyparsing as pp

greet = pp.Word(pp.alphas)("salutation") + "," + pp.Word(pp.alphas)("addressee") + "!"
result = greet.parse_string("Hello, World!", parse_all=True)

assert result.as_list() == ["Hello", ",", "World", "!"]
assert result.salutation == "Hello"
assert result["addressee"] == "World"
```

### Parsing and Transforming Values

```python
import pyparsing as pp

integer = pp.Word(pp.nums).set_parse_action(lambda tokens: int(tokens[0]))
assignment = pp.Word(pp.alphas)("name") + pp.Suppress("=") + integer("value")

result = assignment.parse_string("count = 42", parse_all=True)
assert result.as_dict() == {"name": "count", "value": 42}

macro_name = pp.Word(pp.alphas)
macro = pp.Suppress("${") + macro_name + pp.Suppress("}")
macro = macro.set_parse_action(lambda tokens: tokens[0].upper())
assert macro.transform_string("hello ${name}") == "hello NAME"
```

### Recursive Expression

```python
import pyparsing as pp

expr = pp.Forward()
integer = pp.common.integer
term = integer | pp.Group(pp.Suppress("(") + expr + pp.Suppress(")"))
expr <<= pp.infix_notation(
    term,
    [
        (pp.one_of("* /"), 2, pp.OpAssoc.LEFT),
        (pp.one_of("+ -"), 2, pp.OpAssoc.LEFT),
    ],
)

parsed = expr.parse_string("2 + 3 * (4 + 5)", parse_all=True)
assert parsed.as_list()
```

## Non-Goals

- This specification does not require the same internal class hierarchy, cache implementation, recursion algorithm, or optimization strategy as any existing implementation.
- Exact exception message wording, warning message wording, debug trace formatting, `dump()` whitespace, and generated diagram HTML formatting are not part of the contract unless a caller checks a documented attribute or structured return value.
- Private helpers, private attributes, and private modules are not part of the public API.
- The examples directory is documentation for how to use the library; implementing every example application as a supported public module is not required.
- Deprecated compatibility aliases should exist and behave like their preferred names, but deprecation warning categories and exact warning text are not a reconstruction target.
- Optional integrations that require unavailable third-party packages may raise normal import errors when those dependencies are absent.
