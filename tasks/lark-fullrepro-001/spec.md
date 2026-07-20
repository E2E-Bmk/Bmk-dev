# Lark Specification

## Product Overview

Lark is a pure-Python parsing toolkit for defining grammars, parsing text, and processing parse trees. It uses an EBNF-style grammar language, builds parse trees automatically, and exposes parsing engines for Earley, LALR(1), and CYK. The primary workflow is to write a grammar, parse input into `Tree` and `Token` objects, and then process that tree with visitors, transformers, interpreters, or application code.

Lark has no mandatory runtime dependencies. Optional extras enable specific integrations such as the third-party `regex` engine, regex-collision analysis through `interegular`, Nearley grammar import through `js2py`, and atomic cache writes.

## Scope

This specification covers the public behavior of:

- Lark grammar syntax: rules, terminals, EBNF operators, priorities, aliases, directives, imports, and tree-shaping prefixes.
- Parser construction and parsing through `Lark`.
- Lexer output, token metadata, parse-tree structure, and tree traversal helpers.
- Visitors, transformers, interpreters, `v_args`, `Discard`, and visitor error wrapping.
- Public parse and lex exception classes and their documented helper APIs.
- LALR interactive parsing, parser save/load, grammar loading from files and packages, indentation postlexers, AST utilities, reconstruction, and documented SPPF forest APIs.
- Optional tool workflows for standalone LALR parsers and Nearley import, when their dependencies are available.

Internal parser tables, scanner internals, grammar-loader internals, exact cache file naming, private helper classes, private attributes, exact exception message text, and undocumented representation details are outside the public contract.

## Installable Surface

The package is installed as `lark` and imports from the `lark` namespace.

Top-level public imports:

```python
from lark import (
    Discard,
    GrammarError,
    Lark,
    LarkError,
    LexError,
    ParseError,
    ParseTree,
    TextSlice,
    Token,
    Transformer,
    Transformer_NonRecursive,
    Tree,
    UnexpectedCharacters,
    UnexpectedEOF,
    UnexpectedInput,
    UnexpectedToken,
    Visitor,
    logger,
    v_args,
)
```

Documented public submodule imports include:

```python
from lark.ast_utils import AsList, Ast, WithMeta, create_transformer
from lark.exceptions import VisitError
from lark.grammar import Symbol
from lark.indenter import Indenter, PythonIndenter
from lark.lexer import BasicLexer, Lexer, Token
from lark.load_grammar import (
    FromPackageLoader,
    GRAMMAR_ERRORS,
    GrammarError,
    find_grammar_errors,
    list_grammar_imports,
)
from lark.parsers.earley_forest import (
    ForestTransformer,
    ForestVisitor,
    PackedNode,
    SymbolNode,
    TreeForestTransformer,
    handles_ambiguity,
)
from lark.parsers.lalr_interactive_parser import (
    ImmutableInteractiveParser,
    InteractiveParser,
)
from lark.reconstruct import Reconstructor
from lark.utils import TextSlice
from lark.visitors import (
    CollapseAmbiguities,
    Interpreter,
    Transformer_InPlace,
    Transformer_InPlaceRecursive,
    Visitor_Recursive,
    merge_transformers,
    visit_children_decor,
)
```

The standalone parser and Nearley converter are invoked as modules:

```bash
python -m lark.tools.standalone
python -m lark.tools.nearley <grammar.ne> <start_rule> <path_to_nearley_repo>
```

The optional `regex=True` parser mode uses the third-party regular-expression
engine when it is installed:

```python
import regex
```

## Public API

### `Lark(grammar, **options)`

`Lark` constructs a parser from a grammar string, a text file object, or a prebuilt grammar object. A file object is read completely during construction. If a file object has a `name`, Lark uses it as the grammar source path unless `source_path` is supplied.

Common options:

| option | default | behavior |
|---|---:|---|
| `start` | `"start"` | Start symbol as a string, or multiple start symbols as a list. If multiple starts are configured, `parse(..., start=...)` selects one. |
| `parser` | `"earley"` | Parser engine: `"earley"`, `"lalr"`, `"cyk"`, or `None` for lexer-only construction. |
| `lexer` | `"auto"` | Lexer mode. `"auto"` chooses `"contextual"` for LALR, `"dynamic"` for Earley without `postlex`, `"basic"` for CYK, and `"basic"` for Earley with `postlex`. Explicit values include `"basic"`, `"contextual"`, `"dynamic"`, and `"dynamic_complete"`. |
| `ambiguity` | `"auto"` | Earley ambiguity handling. `"resolve"` returns a single derivation, `"explicit"` wraps alternatives in `_ambig` tree nodes, and `"forest"` returns the SPPF root. |
| `debug` | `False` | Emits extra debug information and warnings through `lark.logger`. Earley debug mode may produce an SPPF graph if graphing tools are installed. |
| `strict` | `False` | Raises on shift/reduce conflicts and regex collisions instead of accepting or warning about them. Regex collision checks require `interegular`. |
| `transformer` | `None` | Applies a transformer during parsing. Embedded transformers are supported with LALR and not with Earley. |
| `propagate_positions` | `False` | Populates tree `meta` with line, column, end-line, end-column, start/end offsets, and container positions. A callable may filter which nodes receive positions. |
| `maybe_placeholders` | `True` | Controls the `[]` grammar operator. When true, an unmatched optional group contributes `None`; when false, it behaves like `()?` and contributes no child. |
| `cache` | `False` | Caches LALR grammar analysis. `True` uses a generated cache path; a string uses that path. |
| `cache_grammar` | `False` | Includes the unanalyzed grammar in cached data. Requires `cache`. |
| `regex` | `False` | Uses the optional `regex` module instead of `re`; raises `ImportError` if requested without the dependency. |
| `g_regex_flags` | `0` | Regex flags applied to all terminal regexes and strings. |
| `keep_all_tokens` | `False` | Prevents automatic punctuation-token filtering in tree construction. |
| `tree_class` | `None` | Uses a custom tree class instead of `lark.Tree`. |
| `postlex` | `None` | Applies lexer post-processing. It works with basic and contextual lexers, not dynamic lexers. |
| `priority` | `"auto"` | Priority handling: `"normal"`, `"invert"`, `None`, or `"auto"`. |
| `lexer_callbacks` | `{}` | Maps token names to callbacks that may transform tokens during lexing. |
| `use_bytes` | `False` | Accepts `bytes` input. Grammar text must be ASCII when this is true. |
| `ordered_sets` | `True` | Uses stable ordered sets for Earley output. |
| `edit_terminals` | `None` | Callback that can modify terminal definitions before parser construction. |
| `import_paths` | `[]` | Search paths or loader functions for `%import` directives. |
| `source_path` | `None` | Overrides the grammar source path used for relative imports and diagnostics. |

Unknown options raise a configuration error. Invalid parser, lexer, ambiguity, or priority values raise configuration errors. `cache` is only supported for LALR. `postlex` cannot be used with dynamic lexers.

### Public Helper Classes and Grammar Utilities

`TextSlice` is importable both from `lark` and from `lark.utils`. It represents a slice-like view of text that can be parsed without first copying the selected substring.

`Token` is importable both from `lark` and from `lark.lexer`. `Lexer` is the public base/interface for custom lexer implementations; subclasses provide `lex(...)` and can be used with custom lexer workflows. `BasicLexer` is the standard basic lexer class importable from `lark.lexer`.

`find_grammar_errors(grammar, start)` analyzes grammar text and reports grammar problems without building a full parser. `list_grammar_imports(grammar, import_paths=None)` reports grammar imports referenced by `%import` directives. `FromPackageLoader(package, search_paths=...)` is a loader used with grammar imports that should resolve from package resources. `GRAMMAR_ERRORS` names grammar-error categories used by the grammar analysis helpers. `Symbol` is an importable grammar symbol value object used by public grammar helper workflows.

Public tree and visitor/transformer classes support normal Python typing use in annotations. `Tree`, `ParseTree`, `Transformer`, `Transformer_NonRecursive`, `Transformer_InPlace`, and `Transformer_InPlaceRecursive` may be subscripted in type hints, such as `Transformer[Token, int]`, without changing runtime behavior.

### Parser Methods

`parse(text, start=None, on_error=None)` parses a `str`, `bytes`, `TextSlice`, or custom lexer input according to the configured grammar. Without an embedded transformer it returns a `Tree`; with an embedded transformer it returns the transformer result. Parse failures raise `UnexpectedCharacters`, `UnexpectedToken`, or `UnexpectedEOF`, all of which are subclasses of `UnexpectedInput`. The `on_error` callback is supported only for LALR; when provided, it receives an `UnexpectedInput` and may return true to resume parsing.

`lex(text, dont_ignore=False)` returns an iterator of `Token` objects without parsing. It is intended for lexer-visible behavior. With `dont_ignore=True`, ignored tokens are returned too. Lexing failures raise `UnexpectedCharacters`.

`parse_interactive(text=None, start=None)` starts a LALR interactive parsing session and returns an `InteractiveParser`. It is only available for LALR parsers.

`get_terminal(name)` returns public information for a named terminal. A missing name raises `KeyError`.

`open(grammar_filename, rel_to=None, **options)` reads a UTF-8 grammar file and constructs a parser. If `rel_to` is provided, the grammar filename is resolved relative to that file's directory.

`open_from_package(package, grammar_path, search_paths=[""], **options)` loads a grammar resource from a Python package and configures grammar imports to resolve through that package.

`save(f, exclude_options=())` serializes a LALR parser to a binary file object. `load(f)` loads a parser from a binary file object. Loaded parsers may accept a limited set of runtime options that do not require grammar reanalysis, such as `postlex`, `transformer`, `lexer_callbacks`, `use_bytes`, `debug`, `g_regex_flags`, `regex`, `propagate_positions`, and `tree_class`.

## Grammar Language

Lark grammars are EBNF-style text files. A grammar contains rules, terminals, directives, comments, priorities, imports, and tree-shaping annotations.

Rules use lowercase names:

```text
rule_name: item item
         | alternative -> alias
```

Terminals use uppercase names:

```text
TERMINAL: "literal" | /regular expression/ | "a".."z"
```

Supported grammar operators include:

- `item?`, `item*`, `item+`
- `item ~ n` and `item ~ n..m`
- grouping with `( ... )`
- optional groups with `[ ... ]`
- terminal and rule alternatives with `|`
- terminal/rule priorities using `.number`

Directives:

- `%ignore TERMINAL` removes terminal occurrences from parsing and tree construction.
- `%import module.NAME`, `%import module (A, B, rule)`, and `->` aliases import terminals and rules from built-in grammars, relative grammar files, or configured import paths.
- `%declare TERMINAL` declares a terminal without defining it.
- `%override name: ...` replaces a rule or terminal definition, including references from imported grammars.
- `%extend name: ...` adds alternatives to an existing rule or terminal.

Comments start with `//` or `#` and continue to the end of the line.

By convention and behavior, uppercase names define terminals and lowercase names define rules. This affects lexing, parsing, and the shape of the resulting tree.

The installed package includes built-in grammar resource files under `lark/grammars`: `common.lark`, `lark.lark`, `python.lark`, and `unicode.lark`. Absolute `%import` paths resolve from this built-in grammar directory. `common.lark` provides common terminals such as whitespace, numbers, names, and escaped strings. `lark.lark` describes Lark's own grammar syntax and is loadable with `Lark.open(...)`. `python.lark` and `unicode.lark` provide packaged grammar definitions used by documented examples and grammar imports.

## Parsing and Lexing Behavior

Earley can parse any context-free grammar and supports ambiguity handling. Its default dynamic lexer tries possible tokenizations while matching each terminal once by longest match. `lexer="dynamic_complete"` considers every matching variation and can reveal terminal-level ambiguity at a higher performance cost. Earley may return a resolved tree, explicit `_ambig` trees, or an SPPF forest depending on `ambiguity`.

LALR(1) is optimized for deterministic grammars. With `lexer="contextual"`, the lexer narrows token choices using parser state, which helps resolve common terminal collisions. LALR supports interactive parsing and embedded transformers.

CYK is available as a legacy parser for highly ambiguous grammars but is slow for ordinary grammars.

Terminal matching with basic/contextual lexers follows public precedence:

1. Highest terminal priority.
2. Longest theoretical regexp match.
3. Longest literal or pattern definition.
4. Terminal name.

With `strict=True`, Lark raises on shift/reduce conflicts and regex collisions instead of silently accepting them. Regex collision detection requires `interegular`; if strict mode needs it and it is unavailable, construction raises.

## Tree Construction

When parsing succeeds, Lark builds a tree automatically from grammar structure. Each matched rule normally becomes a `Tree` branch whose children are matched rules and terminals in order.

Terminal filtering:

- Unnamed string literals and terminals whose names start with `_` are omitted by default.
- Unnamed regular expressions and named terminals whose names start with a letter appear as `Token` values.
- Terminals composed from other terminals include the full match as one token.
- `keep_all_tokens=True` keeps punctuation tokens that would otherwise be filtered.
- A rule prefixed with `!` keeps all terminals matched by that rule.

Rule shaping:

- Rules prefixed with `_` are inlined into their parent.
- Rules prefixed with `?` are inlined when they have a single child after filtering.
- Rule alternatives with `-> alias` use the alias as the tree node's `data`.

The `[]` operator produces `None` for unmatched optional content when `maybe_placeholders=True`; with `maybe_placeholders=False`, it contributes no child.

## Tree and Token Model

`Tree(data, children, meta=None)` stores the rule or alias name in `data`, matched children in `children`, and optional source positions in `meta`. `Tree` objects compare equal when their `data` and `children` are equal, and hash from those values. Pattern matching exposes `(data, children)`.

Tree methods:

- `pretty(indent_str="  ")` returns an indented debug string.
- `iter_subtrees()` iterates over subtrees bottom-up without returning the same tree object twice.
- `iter_subtrees_topdown()` iterates top-down.
- `find_pred(pred)` yields subtrees where `pred(tree)` is true.
- `find_data(data)` yields subtrees with matching `data`.
- `find_token(token_type)` yields tokens with matching `type`.
- `scan_values(pred)` yields non-tree values satisfying a predicate.
- `copy()` returns a shallow copy with the same `children` list object.
- `set(data, children)` replaces the tree contents.
- `__rich__()` returns a Rich tree widget when the optional `rich` library is installed.

When positions are propagated, `tree.meta` may include `line`, `column`, `end_line`, `end_column`, `start_pos`, `end_pos`, and container position fields. Container positions include inlined or filtered symbols that contributed to the source span.

`Token(type, value, start_pos=None, line=None, column=None, end_line=None, end_column=None, end_pos=None)` is a subclass of `str`. Normal string operations work. `token.value == token` is true. Token equality requires matching token type when the other object is also a `Token`, and otherwise follows string equality. Pattern matching exposes `(type, value)`.

Token methods:

- `update(type=None, value=None)` returns a new token with changed type or value and borrowed position metadata.
- `new_borrow_pos(type_, value, borrow_t)` creates a token with position metadata copied from another token.

## Transformers, Visitors, and Interpreters

`Transformer(visit_tokens=True)` processes trees bottom-up. For each tree node it calls a method named after `tree.data`; for tokens it calls a method named after `token.type` when token visiting is enabled. A tree callback receives the children list by default and replaces the node with its return value. Missing tree callbacks call `__default__(data, children, meta)`, which returns `Tree(data, children, meta)`. Missing token callbacks call `__default_token__(token)`, which returns the token. Returning `Discard` removes that value from its parent.

`Transformer_NonRecursive` has the same public transformation semantics as `Transformer` but avoids recursion and does not modify the original tree. `Transformer_InPlace` and `Transformer_InPlaceRecursive` modify existing tree objects in place. The `*` operator chains transformers into a `TransformerChain`.

`Visitor` visits tree nodes without rebuilding the tree. `visit(tree)` visits bottom-up and returns the same tree object. `visit_topdown(tree)` visits root-first. `Visitor_Recursive` provides the same interface with recursive traversal. Missing callbacks call `__default__(tree)`, which returns the tree and otherwise does nothing.

`Interpreter` visits top-down but does not automatically descend into children. A method named after `tree.data` receives the tree object. `visit_children(tree)` visits all tree children and returns their results. `__default__(tree)` visits children.

`v_args(inline=False, meta=False, tree=False, wrapper=None)` changes callback signatures for transformers and interpreters. `inline=True` passes children as positional arguments. `meta=True` passes `meta` and children. `tree=True` passes a constructed tree object. `tree` cannot be combined with `inline` or `meta`; `wrapper` cannot be combined with those built-in modes.

`visit_children_decor` wraps an `Interpreter` method so it receives visited child results. `merge_transformers(base_transformer=None, **transformers)` attaches methods from each transformer to the base transformer under `prefix__method` names and raises `AttributeError` on collisions.

Callback exceptions other than grammar errors are wrapped in `VisitError`, which exposes `rule`, `obj`, and `orig_exc`.

`CollapseAmbiguities` transforms `_ambig` nodes into a list of unambiguous tree alternatives. The number of outputs grows with the product of ambiguity counts.

## Error Semantics

`LarkError` is the public base exception. `GrammarError`, `LexError`, and `ParseError` identify grammar, lexing, and parsing failures. `UnexpectedInput` is the public base class for parse-input failures.

`UnexpectedInput` exposes `line`, `column`, `pos_in_stream`, `state`, `get_context(text, span=40)`, and `match_examples(parse_fn, examples, token_type_match_fallback=False, use_accepts=True)`. `get_context` requires the original text because parsers do not retain it.

`UnexpectedCharacters` is raised when the lexer cannot match the next input. It exposes the unexpected `char`, source position attributes, `allowed`, `considered_tokens`, `considered_rules`, and token history when available.

`UnexpectedToken` is raised when the parser receives a token that cannot advance the current state. It exposes `token`, `expected`, `considered_rules`, `interactive_parser`, `token_history`, and an `accepts` property for token types accepted from the failure state.

`UnexpectedEOF` is raised when input ends while the parser expects more tokens. It exposes `expected` and an EOF token.

Exact exception message text is not part of the public contract. Exception classes, attributes, and helper method behavior are public.

## Advanced Public APIs

`InteractiveParser` gives advanced control over LALR parsing. `feed_token(token)` advances with a `Token`. `iter_parse()` yields tokens as it lexes and feeds them, setting `result` when parsing completes. `exhaust_lexer()` feeds remaining lexer tokens without feeding EOF. `feed_eof(last_token=None)` feeds an end token. `choices()` returns token choices for the current parser state. `accepts()` returns token types that can advance to a valid state. `copy(deepcopy_values=True)` creates an independent parser state. `as_immutable()` returns an `ImmutableInteractiveParser`. `pretty()` formats current choices. `resume_parse()` resumes automated parsing from the current state. `ImmutableInteractiveParser` returns new parser instances for mutating operations and can be converted back with `as_mutable()`.

When Earley parsing uses `ambiguity="forest"`, the SPPF API exposes `SymbolNode`, `PackedNode`, `ForestVisitor`, `ForestTransformer`, `TreeForestTransformer`, and `handles_ambiguity`. `SymbolNode.children` yields packed derivations sorted by public priority order and `is_ambiguous` indicates multiple derivations. `PackedNode.children` yields present left/right children. Forest visitors and transformers operate on the documented forest node types rather than parse trees.

`Indenter` is an abstract `postlex` helper for indentation-sensitive languages. Subclasses provide `NL_type`, `OPEN_PAREN_types`, `CLOSE_PAREN_types`, `INDENT_type`, `DEDENT_type`, and `tab_len`. It injects indent and dedent tokens outside parenthesized regions and raises a dedent error for inconsistent indentation. `PythonIndenter` uses Python-style `_NEWLINE`, `_INDENT`, `_DEDENT`, bracket tokens, and tab width 8.

`ast_utils.create_transformer(ast_module, transformer=None, decorator_factory=v_args)` collects public subclasses of `Ast` from a module and attaches transformer methods using snake_case names derived from class names. Classes inheriting `AsList` receive one list argument; classes inheriting `WithMeta` receive the tree meta. Classes whose names start with `_` are skipped.

`Reconstructor(parser, term_subs=None).reconstruct(tree, postproc=None, insert_spaces=True)` reconstructs source text from a parse tree using a Lark parser's grammar. It cannot invent values for discarded regular expressions; callers provide `term_subs` when such terminals need output text.

The standalone tool emits a Python module for a fixed LALR grammar. The Nearley converter requires the `nearley` extra and a local Nearley repository; it can import Nearley grammars into Python modules but does not export Lark grammars to Nearley.

## Cross-View Invariants

1. A grammar's rules, terminals, aliases, and tree-shaping prefixes determine parse-tree node names and token presence consistently across `parse()`, tree traversal, visitors, and transformers.
2. For the same parser instance and same input, repeated parsing produces equivalent public results unless user callbacks or custom classes intentionally introduce side effects.
3. Every token returned by `lex()` or included in a parse tree has a `type` corresponding to a matched terminal and a string value corresponding to matched input text.
4. When position propagation is enabled, token positions and tree meta positions refer to the same original input coordinate system used by `UnexpectedInput.get_context()`.
5. A transformer embedded in a LALR parser and the same transformer applied after parsing are expected to produce behaviorally equivalent transformed results for callbacks without external side effects.
6. `Visitor.visit()` and `Visitor.visit_topdown()` return the visited tree object; any structural changes come from user callback mutation, not from the visitor framework rebuilding the tree.
7. LALR interactive parsing exposes the same parser state used by normal parsing. Feeding equivalent tokens and completing the parse yields the same public result as batch parsing, modulo user callbacks and error recovery choices.
8. Save/load round trips for LALR parsers preserve grammar analysis and produce equivalent parsing behavior when supplied with compatible runtime options.
9. Cache use changes parser construction cost, not successful parse-tree semantics, for the same grammar, options, version, and Python version.
10. Error objects, `accepts()`, `choices()`, and `match_examples()` describe the same grammar/input failure surface observed through batch parsing and interactive parsing.
11. Tree traversal helpers, visitors, transformers, and `scan_values()` all observe the same `Tree.children` contents produced by tree construction and token filtering.
12. Optional extras extend specific behavior only when available; the absence of an optional dependency should either raise the documented construction/import error for that feature or leave unrelated core parsing behavior unaffected.

## Representative Workflows

Basic parsing:

```python
from lark import Lark

grammar = """
    start: "hello" WORD
    %import common.WORD
    %ignore " "
"""

parser = Lark(grammar)
tree = parser.parse("hello world")
print(tree.data)
print(tree.pretty())
```

Transforming parse results:

```python
from lark import Lark, Transformer, v_args

grammar = """
    start: sum
    sum: NUMBER "+" NUMBER
    %import common.NUMBER
    %ignore " "
"""

@v_args(inline=True)
class Eval(Transformer):
    def NUMBER(self, token):
        return int(token)

    def sum(self, left, right):
        return left + right

parser = Lark(grammar, parser="lalr", transformer=Eval())
assert parser.parse("3 + 5") == 8
```

Handling parse errors:

```python
from lark import Lark, UnexpectedInput

parser = Lark('start: "a" "b"', parser="lalr")

try:
    parser.parse("a c")
except UnexpectedInput as exc:
    print(exc.line, exc.column)
    print(exc.get_context("a c"))
```

Interactive parsing:

```python
from lark import Lark

parser = Lark('start: "a" "b"', parser="lalr")
interactive = parser.parse_interactive("a b")
for token in interactive.iter_parse():
    print(token.type, token.value)
result = interactive.feed_eof()
```

Loading a grammar from a package:

```python
from lark import Lark

parser = Lark.open_from_package(__name__, "grammar.lark", search_paths=("grammars",), parser="lalr")
```

## Non-Goals

- Reproducing private parser table structures, scanner internals, grammar loader state, cache filename formulas, or source-file organization.
- Guaranteeing exact `repr()` output, exact exception message wording, or debug-log text unless a documented public example explicitly relies on it.
- Implementing Nearley import without the `nearley` extra and external Nearley resources.
- Requiring external visualization tools such as `pydot` or Graphviz for core parsing behavior.
- Treating CYK performance or internal ambiguity data structures as core behavior beyond the documented public APIs.
- Treating undocumented private names as public merely because Python can import them.
