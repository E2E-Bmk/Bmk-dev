# postcss Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`postcss` is a CSS transformation engine that parses stylesheets into a mutable abstract syntax tree, lets programs inspect and rewrite that tree through a typed node API and a plugin pipeline, and prints the tree back to CSS text. Its defining property is formatting fidelity: every node records the exact whitespace, comments, and punctuation fragments that surrounded it in the source (its "raws"), so a stylesheet that is parsed and printed without modification is reproduced byte for byte, while nodes created or modified programmatically are printed with documented default formatting.

The engine exposes one fact source — a tree of typed nodes plus the raws and source positions captured at parse time — through several public projections: string printing, tree navigation and mutation methods, a processor pipeline with visitor-style plugin events and a result object carrying warnings and messages, a JSON serialization round trip, precise position and error reporting anchored to the original input, and small utilities for splitting CSS value lists.

## Non-Goals

- This specification does not require source map generation or consumption: the `map` processing option, output source maps, and reading of pre-existing source map comments are not part of the contract.
- This specification does not require support for custom syntaxes: the `parser`, `stringifier`, and `syntax` processing options are not exercised, and only the built-in CSS parser and printer are contracted.
- This specification does not require terminal color output; code frames are only contracted in their uncolored form.
- This specification does not define the exact wording of error or warning reason strings; only trigger conditions, error classes, and position fields are contracted.
- This specification does not define a command-line interface; the package is a library only.
- This specification does not require the legacy plugin-creation helper of older major versions beyond what the Processors section describes.

## Representative Workflows

**Workflow 1 — parse, inspect, mutate, print.** A stylesheet is parsed into a `Root`, inspected through traversal helpers, edited in place, and printed. Untouched regions keep their original formatting; the edited declaration is reprinted from its new value.

```ts
import { parse } from "postcss";

const root = parse("a {\n  color : red;\n}\n/* footer */\n");
root.toString() === "a {\n  color : red;\n}\n/* footer */\n"; // byte-exact

const rule = root.first;              // Rule node
rule.selector;                        // "a"
const decl = rule.first;              // Declaration node
decl.prop;                            // "color"
decl.value;                           // "red"
decl.raws.between;                    // " : "  (captured exactly)

decl.value = "blue";                  // edit in place
root.walkComments((c) => c.remove()); // drop comments
root.toString();                      // "a {\n  color : blue;\n}\n"
```

**Workflow 2 — a plugin pipeline with visitors and warnings.** A processor is built from plugin objects. Each plugin names itself with `postcssPlugin` and registers event listeners. Processing produces a lazy result that is a thenable; awaiting it (or reading `css` synchronously when every plugin is synchronous) runs the pipeline and yields a `Result` with the printed CSS and collected warnings.

```ts
import postcss from "postcss";

const noRed = {
  postcssPlugin: "no-red",
  Declaration(decl, { result }) {
    if (decl.value === "red") {
      decl.warn(result, "red is banned", { word: "red" });
      decl.value = "crimson";
    }
  },
};

const result = await postcss([noRed]).process("a{color:red}", { from: "app.css" });
result.css;                    // "a{color:crimson}"
result.warnings().length;      // 1
result.warnings()[0].plugin;   // "no-red"
```

**Workflow 3 — building a tree from scratch.** Factory helpers construct detached nodes; containers accept nodes, plain object descriptors, or CSS strings. Printing a constructed tree uses default formatting.

```ts
import postcss, { rule, decl } from "postcss";

const root = postcss.root();
const r = rule({ selector: "a" });
r.append(decl({ prop: "color", value: "red" }));
r.append({ prop: "top", value: "0" });
root.append(r);
root.toString(); // "a {\n    color: red;\n    top: 0\n}"
```

## Parsing And Input

Parsing turns CSS text into a tree of typed nodes anchored to an `Input` record, and is the sole source of raws and source positions.

**The parse entry point.** `parse` accepts CSS text (a string, or any object convertible to string such as a file buffer) and an optional options object, and returns a `Root` node. The `from` option names the source file: when given, the input's `file` property must hold the path resolved to an absolute path, and the input's `from` property returns the same path. When `from` is absent, the input must still be uniquely identifiable: `from` returns a synthesized identifier string and `file` is undefined. `parse` is also reachable as a method of the default export.

**The Input record.** Every parsed node's `source.input` is an `Input` instance shared by the whole tree. Its `css` property holds the parsed text. When the text begins with a byte-order mark, the mark must be stripped from `css`, `hasBOM` must be `true`, and printing the tree must re-emit the mark; otherwise `hasBOM` is `false`. An `Input` is directly constructible from CSS text and an options object.

**Source positions.** Every parsed node carries `source.start` and `source.end` objects with 1-based `line` and `column` and a 0-based character `offset`. `start` addresses the first character of the node. `end`'s line and column address the node's final character as written — a container's closing brace, and a declaration's terminating semicolon when one follows — while `end.offset` is the character index one past that character. Whitespace between nodes belongs to the following node's `raws.before`, not to the positions of either node.

**Node population rules.** Rules and braced at-rules receive a `nodes` array (empty for `a {}`). An at-rule terminated by a semicolon or end of input without a block (for example `@import "a.css";`) must have no `nodes` property at all — the bodyless and empty-bodied forms are distinguishable. Declarations whose property name starts with `--` or `$` are variable declarations: `variable` is `true` and the value text between the colon and the terminator is preserved verbatim, including interior and trailing whitespace. For all other declarations `variable` is `false`.

**Line endings and BOM.** Carriage-return/line-feed sequences are preserved through the round trip: they are captured into raws, and positions count each line ending correctly.

## Node Model And Raws

The tree is built from six node types, each exposing typed value properties plus a `raws` record of formatting fragments; raws are what make unmodified printing byte-exact.

**Node types and value properties.** `type` is one of `"root"`, `"rule"`, `"atrule"`, `"decl"`, `"comment"`, `"document"`. A `Rule` exposes `selector`; an `AtRule` exposes `name` (without the `@`) and `params`; a `Declaration` exposes `prop`, `value`, `important` (boolean), and `variable`; a `Comment` exposes `text` (trimmed of the comment delimiters and surrounding whitespace). Every node exposes `parent` (undefined when detached) and `source` when it originated from parsing.

**The raws record.** Raws captured at parse time include: `before` — the whitespace and comments preceding the node (empty string for a first node at the start of input); `between` — the text between a rule's selector and `{`, an at-rule's params and `{`, or a declaration's property and value including the colon; `after` — the whitespace before a container's closing brace (also present on `Root` for trailing text); `semicolon` — a boolean on containers recording whether the last child was followed by a semicolon; `afterName` — the text between an at-rule's `@name` and its params; `important` — the exact important fragment when it differs from the canonical form (for example `" ! important"`), with `important` still reporting `true`; and `left`/`right` — the whitespace inside a comment's delimiters around its text.

**Cached cleaned values.** When a selector, declaration value, or at-rule params contains comments or unusual spacing, the node stores a cache of the form `{ raw, value }` under `raws.selector`, `raws.value`, or `raws.params`: the `value` member is the cleaned text exposed through the property getter (comments removed), and the `raw` member is printed verbatim while the current property value still equals the cached cleaned value. Once the property is reassigned, printing must use the newly assigned value; raw caches of untouched sibling properties keep printing verbatim.

**Raw resolution.** `node.raw` takes a raw name and an optional default-lookup name and returns the effective fragment: the node's own captured raw when present, otherwise a value inferred from the surrounding tree, otherwise the documented default. `cleanRaws()` deletes the formatting raws of a node and all descendants so the subtree reprints with default formatting. `assign` accepts an object of property overrides, applies each, and returns the node for chaining.

## Stringification

Printing projects the tree back to CSS text, using captured raws when present and documented defaults when absent.

**Round-trip fidelity.** Printing a tree parsed from text and not modified since must reproduce the input byte for byte — including irregular whitespace, comments in selectors and values, unusual important fragments, CRLF line endings, and a byte-order mark.

**toString and stringify.** Every node's `toString()` prints that node (including its `raws.before` for non-root nodes only as part of a container print; a detached node prints without a leading `before`). The `stringify` export is the low-level printer: it takes a node and a builder callback and invokes the callback with successive string parts; each call passes the part, the node it belongs to, and for container delimiters a third argument `"start"` or `"end"`. Concatenating the parts equals `toString()`.

**Default formatting for constructed nodes.** Nodes created programmatically print with these defaults: a declaration prints as the property, a colon and one space, then the value (`color: black`); an important declaration appends one space and `!important`; a rule prints its selector, one space, and braces (`a {}` when empty); children are indented four spaces per nesting level, each on its own line; consecutive declarations are separated by semicolons, and the final child omits the semicolon unless the container's `raws.semicolon` is `true`; sibling top-level nodes are separated by a single newline; a bodyless at-rule prints as `@name` plus one space plus params; a comment prints as `/*`, one space, the text, one space, `*/`. A declaration appended directly to a root prints as property, colon, space, value.

**Formatting inheritance.** When a node is inserted into a parsed tree, missing raws are inferred from the tree's existing formatting: indentation follows the indentation pattern of sibling and ancestor nodes, and a container whose `raws.semicolon` is `true` prints a trailing semicolon after newly appended declarations.

**Documents.** A `Document` is a container whose children are `Root` nodes; printing a document concatenates the prints of its roots with no separator of its own. Appending a root to a document sets the root's `parent` to the document.

## Building Trees

Detached nodes are created through classes or factory helpers, and containers accept several input shapes for insertion.

**Factories and classes.** The default export carries factory methods `root`, `rule`, `atRule`, `decl`, `comment`, and `document`, each accepting a properties object and returning a new detached node of the corresponding class; the classes `Root`, `Rule`, `AtRule`, `Declaration`, `Comment`, `Document`, `Container`, and `Node` are also exported and directly constructible with the same properties objects.

**Insertion input shapes.** `append` and `prepend` accept, in any mix and any count: existing nodes (which are re-parented), arrays of nodes, plain object descriptors, and CSS strings that are parsed and spliced in. A descriptor with a `prop` member builds a declaration (its `value` is required), a descriptor with a `selector` member builds a rule, one with a `name` member builds an at-rule, and one with a `text` member builds a comment. Both methods return the container for chaining. `insertBefore` and `insertAfter` take an existing child (or its index) plus the same input shapes and splice relative to that child.

**Insertion validation.** If a declaration descriptor omits `value`, then insertion must throw an `Error`. If a descriptor matches no known node shape, then insertion must throw an `Error`.

## Traversal And Mutation

Containers expose iteration that remains safe under mutation, filtered deep walks, and structural editing methods.

**Direct iteration.** `each` invokes a callback with each direct child and its index. The iteration is mutation-safe: children inserted after the currently visited position are visited in the same pass, and removing already-visited children does not skip survivors. Returning `false` from the callback stops the iteration and makes `each` return `false`. `every` and `some` evaluate a predicate over direct children and return a boolean.

**Deep walks.** `walk` visits every descendant in document order (depth-first, parents before children). `walkRules`, `walkDecls`, `walkAtRules`, and `walkComments` visit only the corresponding node type anywhere in the subtree; each accepts an optional filter before the callback — a string that must equal the rule's selector, the declaration's property, or the at-rule's name, or a regular expression tested against it. Returning `false` from any walk callback halts the entire walk and makes the walk method return `false`.

**Structural reads.** `first` and `last` return the boundary children; `index` returns a child's position (accepting the node or an index); `next` and `prev` return the adjacent sibling of a node within its parent, or undefined at the boundary; `root()` returns the tree's root from any depth.

**Editing.** `replaceWith` replaces a node with one or more nodes or descriptors in place. `remove()` detaches a node and clears its `parent`. `removeChild` removes one child; `removeAll` empties the container, leaving `nodes` an empty array. Inserting a node that currently lives in another container must remove it from its previous parent first.

## Values And Selectors

Small projections expose structured views of selector lists and value lists.

**Selector lists.** `rule.selectors` returns the comma-separated selector parts with surrounding whitespace trimmed. Assigning an array to `selectors` joins the parts back into `selector`, reusing the comma-and-whitespace separator style already present in the rule and defaulting to a comma followed by one space.

**Value splitting.** The `list` export provides `space`, which splits a value on top-level whitespace, and `comma`, which splits on top-level commas — both keep parenthesized groups and quoted strings intact as single items — and `split`, which takes a string, an array of separator characters, and a flag controlling whether an empty trailing item is kept.

**Important.** Parsing `!important` (in any spacing or casing captured by `raws.important`) sets `important` to `true`, and the fragment is reproduced on printing while the declaration is untouched.

## Cloning And JSON Round Trips

Trees and subtrees are duplicated in memory through cloning and serialized to plain JSON for revival.

**Cloning.** `clone` returns a deep copy that is detached (`parent` undefined) and accepts an overrides object applied to the copy. Clones share the original's `source` reference and copy its raws, so a clone of an untouched node prints identically. `cloneBefore` and `cloneAfter` clone the node, insert the copy as the corresponding sibling of the original, and return the copy.

**JSON codec.** `toJSON()` produces a plain-data object carrying `type`, value properties, `raws`, `nodes`, and `source` references; the root-level object additionally carries an `inputs` array describing each distinct `Input` (its `css`, `hasBOM`, and `file` or synthesized identifier). `fromJSON` revives such data into real node instances: the revived tree prints identically to the original, and revived nodes' `source.input.css` is restored.

## Processors And The Plugin Pipeline

A processor bundles plugins and runs them over a parsed tree through a lazy, awaitable result.

**Building processors.** The default export is callable: `postcss(pluginA, pluginB)` and `postcss([pluginA, pluginB])` both return a `Processor` whose `plugins` array holds the normalized plugins. `Processor` is also directly constructible. `use` appends one plugin and returns the processor. `version` reports the engine version string.

**Plugin shapes.** A plugin is an object with a `postcssPlugin` name string and event listeners. The processor must also accept a creator function carrying a `postcss` property set to `true`: passing the creator itself invokes it without arguments, while calling it with options first produces the configured plugin object. Where a plugin object defines `prepare` — a function receiving the `Result` — the listeners it returns run scoped to that run (closing over per-run state such as the options in `result.opts`).

**Processing.** `process` accepts CSS text (or an object with a `toString` method, or an existing `Root`) plus an options object, and returns a lazy result. The `from` option flows into parsing and `result.opts`. The lazy result is a thenable: awaiting it (or calling `then`/`catch`/`finally`) runs the pipeline asynchronously and resolves to a `Result`. Reading `css`, `content`, `root`, or `messages` on the lazy result runs the pipeline synchronously first. `sync()` runs synchronously and returns the `Result`; `async()` returns a promise of it. If any plugin listener returns a promise (an asynchronous plugin), then synchronous access — reading `css`/`content`/`root`/`messages` or calling `sync()` — must throw an `Error`; awaiting still succeeds.

**The plugin-free fast path.** When the processor has no plugins and no custom processing options, reading `css` or `content` on the returned lazy object returns the input text unchanged without parsing it — even text that is not valid CSS. Reading `root` on that object parses the input and raises `CssSyntaxError` on invalid input. Awaiting it resolves to a full `Result`.

**Visitor events.** Listeners are keyed by event name: `Once` and `OnceExit` fire exactly once per root per run, before and after the tree walk; `Root`/`RootExit`, `Rule`/`RuleExit`, `AtRule`/`AtRuleExit`, `Declaration`/`DeclarationExit`, and `Comment`/`CommentExit` fire per matching node — the enter event before the node's children are visited, the exit event after. Where a `Declaration` or `AtRule` listener (or its exit form) is given as an object keying listeners by property name or at-rule name, the entry whose key matches the node and the `"*"` entry must both fire for that node. Every node listener receives the node and a helper object that includes the `result`. The pipeline visits the tree in document order.

**Re-visiting on mutation.** When a listener mutates a node (for example reassigns a declaration's value), the pipeline must schedule the mutated node to be visited again in the same run, so listeners observe the post-mutation state; the final `Result.css` reflects all mutations. Newly inserted nodes are likewise visited.

**Direct result production.** `root.toResult()` produces a `Result` synchronously without a processor run; its `root` is the same node the method was called on, and its `css` equals the tree's printed text.

**Errors raised by plugins.** When a listener throws a `CssSyntaxError` built via `node.error`, the error surfaces to the caller with its `plugin` property set to the throwing plugin's `postcssPlugin` name.

## Results, Warnings, And Messages

A `Result` is the terminal projection of a pipeline run, carrying the printed CSS, the final tree, and a message stream.

**Result fields.** `css` holds the printed stylesheet; `content` is an alias for `css`; `root` holds the final tree; `opts` echoes the processing options (including `from`); `processor` references the producing processor; `toString()` returns `css`. `messages` is an array of message objects appended during the run; `warnings()` returns the messages whose `type` is `"warning"`.

**Raising warnings.** `node.warn(result, text, opts)` appends a `Warning` anchored to that node; `result.warn(text, opts)` appends one without a node. A `Warning` exposes `type` (`"warning"`), `text`, `plugin` (filled automatically with the active plugin's name when raised inside a listener), `node` when anchored, and position fields `line`, `column`, `endLine`, `endColumn` computed from the anchor node — narrowed to a word with the `word` option or to an offset with the `index` option. A warning without a node has undefined position fields. `Warning#toString()` returns the plugin name, a colon and space, then — when anchored — the input identifier with line and column, a colon and space, then the text.

## Positions And Error Construction

Nodes and inputs pinpoint locations in the original text and manufacture positioned errors.

**Position projection.** `node.positionBy` accepts an options object: with `word` it returns the position of that word's first occurrence inside the node's text; with `index` it returns the position that many characters into the node; with neither it returns the node's start. Positions are objects with 1-based `line` and `column` and 0-based `offset`. `node.rangeBy` returns a `{ start, end }` pair: with `word` the range covers exactly that word; with no options it covers the whole node.

**Offset conversion.** `input.fromOffset` converts a 0-based character offset into an object with 1-based `line` and `col` members.

**Manufacturing errors.** `node.error(message, opts)` returns (does not throw) a `CssSyntaxError` positioned within the node — by default covering the whole node, narrowed by `word` or `index` like `positionBy`. `input.error(message, line, column)` builds one at an explicit position. A node with no `source` still produces a `CssSyntaxError`, with undefined position fields and the message carrying only the identifier and the text.

**Error anatomy.** A `CssSyntaxError` is an `Error` whose `name` is `"CssSyntaxError"`. `reason` is the bare description; `message` is the input identifier (the resolved file path when `from` was given, a generic input marker otherwise), a colon, the line, a colon, the column, a colon and space, then the reason. `file` holds the absolute path when known. `source` holds the CSS text. `line`, `column`, and — when a range is known — `endLine` and `endColumn` are 1-based. `showSourceCode(false)` renders an uncolored code frame of the surrounding lines with a `>` marker on the error line and a caret column pointer; `toString()` combines the name, the message, and the code frame.

## State Model

The engine's single fact source is one mutable tree: typed nodes with value properties, a raws record per node, and source positions tied to a shared `Input`. Every public behavior is a projection of that tree:

- **Printing** projects the tree to text through raws-or-default resolution (`toString`, `stringify`, `Result.css`).
- **Navigation and mutation** project and rewrite the node graph (`walk` family, `each`, insertion and removal, `first`/`last`/`index`/`next`/`prev`, `root()`).
- **The pipeline** projects the tree through per-node visitor events and accumulates messages onto a `Result`.
- **The JSON codec** projects the tree to plain data and back (`toJSON`/`fromJSON`).
- **Positions and errors** project node extents back onto the original text (`source`, `positionBy`, `rangeBy`, `fromOffset`, `CssSyntaxError`).
- **Value utilities** project selector and value strings into lists (`list`, `selectors`).

Mutations through any projection are immediately visible to all others: after an edit, printing reflects the new value, walks visit the new structure, and positions of untouched nodes still reference the original input.

## Error Semantics

| Condition | Outcome |
|---|---|
| Parsing text with an unclosed block, unclosed comment, unclosed string, a stray closing brace, or a word where a declaration or rule is required | throws `CssSyntaxError` with `line`/`column` at the offending token |
| Reading `root` on the plugin-free lazy object when the input is invalid CSS | throws `CssSyntaxError` |
| Reading `css`, `content`, `root`, or `messages` (or calling `sync()`) on a lazy result whose plugins are asynchronous | throws `Error` |
| Inserting a declaration descriptor without a `value` member | throws `Error` |
| Inserting a descriptor matching no node shape | throws `Error` |
| A plugin listener throws an error built by `node.error` | the error propagates to the pipeline caller with `plugin` set to the plugin name |
| `node.error(...)` on any node | returns a `CssSyntaxError` (never throws); position fields undefined when the node has no `source` |

Exact reason wording is not contracted; error classes, trigger conditions, and position fields are.

## Cross-View Invariants

1. **Round trip**: for any text that parses successfully, `parse(text).toString()` must equal `text` byte for byte, and `toJSON` followed by `fromJSON` followed by `toString()` must produce that same text.
2. **Result/print agreement**: the `css` produced by a completed pipeline run — read through the lazy result's `css` property or from an awaited `Result` — must equal `result.root.toString()`, and `result.warnings()` must equal exactly the members of `result.messages` whose `type` is `"warning"`.
3. **Tree coherence**: for every node visited by `walk`, `node.root()` must return the tree's root, `node.parent.nodes[node.parent.index(node)]` must be the node itself, and `first`/`last` must equal the boundary members of `nodes`.
4. **Position agreement**: for a parsed node, `positionBy({})` must equal its `source.start`, `rangeBy({})` must span from `source.start` to an end whose column is one past `source.end`'s column at `source.end`'s offset, and `input.fromOffset(source.start.offset)` must report the same line as `source.start.line`.
5. **Selective raw invalidation**: reassigning one property changes only that property's printed form — after editing a declaration's value, printing must use the new value while the untouched selector of the same rule still prints its original raw text.
6. **Clone equivalence**: a clone of an unmodified node must print identically to the original, while `remove`, `replaceWith`, and insertion of the clone leave the original tree printing correctly with the change applied.
7. **Visitor completeness**: one pipeline run must deliver every rule, declaration, at-rule, and comment reachable in the final tree to the corresponding enter listener, including nodes inserted and nodes mutated during the run.

## Public Interface

### Import Surface

The package root is the module `postcss`. Its default export is the callable processor builder, which also carries every named export as a property. The named ESM exports:

```ts
import postcss, {
  parse, stringify, fromJSON, list,
  root, rule, atRule, decl, comment, document,
  Root, Rule, AtRule, Declaration, Comment, Document,
  Container, Node, Processor, Result, Warning, Input,
  CssSyntaxError,
} from "postcss";
```

The module must also be loadable with CommonJS `require("postcss")`, yielding the same callable with the same properties.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `postcss` (default) | function | builds a `Processor` from plugins; carries all named exports as properties |
| `parse` | function | parses CSS text into a `Root` |
| `stringify` | function | low-level printer driving a builder callback |
| `fromJSON` | function | revives `toJSON` data into node instances |
| `list` | object | `space`, `comma`, and `split` value-list helpers |
| `root` / `rule` / `atRule` / `decl` / `comment` / `document` | function | factory helpers returning detached nodes |
| `Node` | class | base node: `type`, `parent`, `source`, `raws`, `toString`, `clone` family, `error`, `warn`, `positionBy`, `rangeBy`, `raw`, `assign`, `cleanRaws`, `remove`, `replaceWith`, `next`, `prev`, `root`, `toJSON` |
| `Container` | class | node with children: `nodes`, `first`, `last`, `index`, `each`, `every`, `some`, walk family, `append`, `prepend`, `insertBefore`, `insertAfter`, `removeChild`, `removeAll` |
| `Root` | class | tree root; adds `toResult` |
| `Rule` | class | selector-bearing container; adds `selectors` |
| `AtRule` | class | at-rule node: `name`, `params`; container when braced |
| `Declaration` | class | property node: `prop`, `value`, `important`, `variable` |
| `Comment` | class | comment node: `text` |
| `Document` | class | container of `Root` nodes |
| `Processor` | class | plugin bundle: `plugins`, `use`, `process`, `version` |
| `Result` | class | run output: `css`, `content`, `root`, `messages`, `warnings`, `opts`, `processor` |
| `Warning` | class | positioned warning message |
| `Input` | class | source text record: `css`, `hasBOM`, `file`, `from`, `fromOffset`, `error` |
| `CssSyntaxError` | class | positioned syntax error with code-frame rendering |

### CLI Entry Points

There is no console script for this package. Programmatic use is through module imports only.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The test runner is `vitest`, executing TypeScript test files that import the package under its published name. No third-party runtime packages are promised beyond the Node.js standard library; the package must be self-contained.

The project must declare its packaging metadata in a standard `package.json` at the project root and expose the package root as `postcss` with the named ESM exports listed under Import Surface, loadable from both ESM `import` and CommonJS `require`.

## Appendix B: Assessment Notes

Assessment exercises the documented behavior through the public module surface only. Dimensions covered include: parsing and input records (positions, BOM, bodyless at-rules, variable declarations); the raws model and byte-exact round trips; default formatting of constructed trees and formatting inheritance; tree building, insertion shapes, and validation errors; traversal (mutation-safe `each`, filtered walks, early termination) and structural editing; selector and value list utilities; cloning and the JSON codec; processor construction, plugin shapes, the lazy result lifecycle (thenable, synchronous access, the plugin-free fast path, asynchronous-plugin restrictions), visitor event ordering and re-visiting on mutation; results, warnings, and messages; position projection and error construction; and the cross-view invariants above. Tests assert observable values, returned references, thrown error classes, and cross-view equivalences; they do not assert reason wording, colored output, or private state.
