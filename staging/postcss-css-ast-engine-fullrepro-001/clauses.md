# Clause sidecar — postcss-css-ast-engine-fullrepro-001

Clause IDs for traceability. Each quotes the governing spec statement (condensed where the
spec sentence is long). Section anchors refer to spec.md H2 headings.

## Parsing And Input (PC-PAR)

- PC-PAR-001 (Event-driven): "When `parse` receives CSS text, it must return a `Root` node."
- PC-PAR-002 (Optional feature): "Where the `from` option is given, `input.file` must hold the absolute resolved path and `input.from` returns the same path."
- PC-PAR-003 (State-driven): "While no `from` option was given, `input.from` returns a synthesized identifier string and `file` is undefined."
- PC-PAR-004 (Ubiquitous): "Every parsed node's `source.input` is an `Input` instance shared by the whole tree; its `css` holds the parsed text."
- PC-PAR-005 (Event-driven): "When the text begins with a BOM, the mark is stripped from `css`, `hasBOM` is `true`, and printing re-emits the mark."
- PC-PAR-006 (Ubiquitous): "Every parsed node carries `source.start`/`source.end` with 1-based `line`/`column` and 0-based `offset`; `end`'s line/column address the node's final character as written (closing brace; terminating semicolon when present) while `end.offset` is one past that character."
- PC-PAR-007 (Ubiquitous): "Whitespace between nodes belongs to the following node's `raws.before`."
- PC-PAR-008 (Ubiquitous): "Rules and braced at-rules receive a `nodes` array (empty for an empty block); a bodyless at-rule has no `nodes` property at all."
- PC-PAR-009 (Event-driven): "When a declaration's property starts with `--` or `$`, `variable` is `true` and the value text is preserved verbatim including whitespace."
- PC-PAR-010 (Ubiquitous): "CRLF sequences are preserved through the round trip."
- PC-PAR-011 (Ubiquitous): "`parse` is also reachable as a method of the default export; `Input` is directly constructible."

## Node Model And Raws (PC-NOD)

- PC-NOD-001 (Ubiquitous): "`type` is one of root/rule/atrule/decl/comment/document; Rule exposes `selector`, AtRule `name`+`params`, Declaration `prop`/`value`/`important`/`variable`, Comment `text`."
- PC-NOD-002 (Ubiquitous): "Every node exposes `parent` (undefined when detached)."
- PC-NOD-003 (Ubiquitous): "raws capture `before`, `between`, `after`, `semicolon`, `afterName`, `important`, `left`/`right` exactly as parsed."
- PC-NOD-004 (Event-driven): "When a selector, value, or params contains comments or unusual spacing, the node stores `{ raw, value }` under `raws.selector`/`raws.value`/`raws.params`; the property getter returns the cleaned `value`."
- PC-NOD-005 (Event-driven): "When the property is reassigned, printing uses the newly assigned value (the raw prints only while the cached cleaned value equals the property); untouched sibling caches keep printing verbatim."
- PC-NOD-006 (Event-driven): "When `!important` is parsed with nonstandard spacing/casing, `raws.important` holds the exact fragment and `important` is `true`."
- PC-NOD-007 (Ubiquitous): "`node.raw(name, defaultName?)` returns the captured raw, else a tree-inferred value, else the documented default."
- PC-NOD-008 (Event-driven): "When `cleanRaws()` is called, formatting raws of the node and descendants are deleted so the subtree reprints with defaults."
- PC-NOD-009 (Ubiquitous): "`assign(overrides)` applies each property and returns the node."

## Stringification (PC-STR)

- PC-STR-001 (Ubiquitous): "Printing a tree parsed from text and not modified since must reproduce the input byte for byte."
- PC-STR-002 (Ubiquitous): "`stringify(node, builder)` invokes the builder with successive parts (part, node, 'start'|'end' for container delimiters); concatenation equals `toString()`."
- PC-STR-003 (Ubiquitous): "Constructed declaration prints `prop: value`; important appends ` !important`; empty rule prints `sel {}`."
- PC-STR-004 (Ubiquitous): "Constructed children indent four spaces per level, one per line; declarations separated by semicolons with the final child omitting it unless `raws.semicolon` is true; top-level siblings separated by one newline."
- PC-STR-005 (Ubiquitous): "A constructed bodyless at-rule prints `@name params`; a comment prints `/* text */`; a declaration in a root prints `prop: value`."
- PC-STR-006 (Event-driven): "When a node is inserted into a parsed tree, missing raws are inferred from the tree's formatting (indentation pattern, trailing-semicolon style)."
- PC-STR-007 (Ubiquitous): "A Document prints the concatenation of its Root children with no separator; appending a root sets its `parent` to the document."

## Building Trees (PC-BLD)

- PC-BLD-001 (Ubiquitous): "Factories `root`/`rule`/`atRule`/`decl`/`comment`/`document` and classes `Root`/`Rule`/`AtRule`/`Declaration`/`Comment`/`Document` build detached nodes from properties objects."
- PC-BLD-002 (Ubiquitous): "`append`/`prepend` accept nodes, arrays, object descriptors ({prop,value}→decl, {selector}→rule, {name}→atrule, {text}→comment), and CSS strings, in any mix; both return the container."
- PC-BLD-003 (Unwanted behavior): "If a declaration descriptor omits `value`, insertion throws an `Error`."
- PC-BLD-004 (Unwanted behavior): "If a descriptor matches no node shape, insertion throws an `Error`."
- PC-BLD-005 (Ubiquitous): "`insertBefore`/`insertAfter` take an existing child (or index) plus the same shapes and splice relative to it."
- PC-BLD-006 (Event-driven): "When an inserted node lives in another container, it is removed from its previous parent first."

## Traversal And Mutation (PC-TRV)

- PC-TRV-001 (Ubiquitous): "`each` iterates direct children with index, is mutation-safe (later-inserted children visited; removals do not skip survivors)."
- PC-TRV-002 (Event-driven): "When a callback returns false, `each`/walk methods stop and return false."
- PC-TRV-003 (Ubiquitous): "`walk` visits every descendant depth-first, parents before children."
- PC-TRV-004 (Ubiquitous): "`walkRules`/`walkDecls`/`walkAtRules`/`walkComments` visit only that type; optional string filter equals selector/prop/name, regexp filter tests it."
- PC-TRV-005 (Ubiquitous): "`first`/`last` are boundary children; `index` returns a child's position; `next`/`prev` return adjacent siblings or undefined; `root()` returns the tree root from any depth."
- PC-TRV-006 (Ubiquitous): "`replaceWith` replaces a node with one or more nodes/descriptors in place."
- PC-TRV-007 (Ubiquitous): "`remove()` detaches and clears `parent`; `removeChild` removes one child; `removeAll` empties `nodes`."
- PC-TRV-008 (Ubiquitous): "`every`/`some` evaluate a predicate over direct children."

## Values And Selectors (PC-VAL)

- PC-VAL-001 (Ubiquitous): "`rule.selectors` returns comma-separated parts trimmed; assigning joins with the existing separator style, defaulting to comma+space."
- PC-VAL-002 (Ubiquitous): "`list.space` splits on top-level whitespace and `list.comma` on top-level commas; parenthesized groups and quoted strings stay intact."
- PC-VAL-003 (Ubiquitous): "`list.split(string, separators, last)` generalizes splitting with a flag for the trailing item."
- PC-VAL-004 (Event-driven): "When `!important` is parsed, `important` is true and the fragment reproduces on printing."

## Cloning And JSON (PC-CLN)

- PC-CLN-001 (Ubiquitous): "`clone(overrides)` returns a deep detached copy applying overrides; clones share `source` and copy raws, printing identically when untouched."
- PC-CLN-002 (Ubiquitous): "`cloneBefore`/`cloneAfter` insert the copy as the corresponding sibling and return the copy."
- PC-CLN-003 (Ubiquitous): "`toJSON()` produces plain data with type, value properties, raws, nodes, and root-level `inputs`."
- PC-CLN-004 (Event-driven): "When `fromJSON` receives such data, it revives real nodes; the revived tree prints identically and `source.input.css` is restored."

## Processors And The Plugin Pipeline (PC-PRC)

- PC-PRC-001 (Ubiquitous): "`postcss(...plugins)` and `postcss([plugins])` return a `Processor` whose `plugins` holds the normalized plugins; `use` appends and returns the processor; `version` reports the version string."
- PC-PRC-002 (Ubiquitous): "A plugin is an object with `postcssPlugin` and listeners; a creator function with `.postcss === true` is invoked without arguments when passed uninvoked; calling it with options produces the configured plugin."
- PC-PRC-003 (Optional feature): "Where a plugin defines `prepare(result)`, its returned listeners are scoped to that run."
- PC-PRC-004 (Ubiquitous): "`process(css, opts)` returns a lazy thenable resolving to a `Result`; reading css/content/root/messages runs synchronously; `sync()` returns the Result; `async()` returns a promise."
- PC-PRC-005 (Unwanted behavior): "If any listener returns a promise, synchronous access (css/content/root/messages/sync()) throws an `Error`; awaiting succeeds."
- PC-PRC-006 (State-driven): "While the processor has no plugins and no custom options, reading `css`/`content` returns the input text unchanged without parsing; reading `root` parses and raises `CssSyntaxError` on invalid input; awaiting resolves to a full `Result`."
- PC-PRC-007 (Ubiquitous): "`Once`/`OnceExit` fire once per root per run before/after the walk; per-type enter events fire before children, exit events after; visits follow document order."
- PC-PRC-008 (Optional feature): "Where `Declaration`/`AtRule` listeners are objects keyed by prop/name, the keyed listener and the `\"*\"` listener both fire for a matching node."
- PC-PRC-009 (Ubiquitous): "Node listeners receive the node and a helper object including `result`."
- PC-PRC-010 (Event-driven): "When a listener mutates a node, the pipeline schedules it for re-visiting in the same run; final css reflects all mutations; inserted nodes are visited."
- PC-PRC-011 (Ubiquitous): "`root.toResult()` produces a Result synchronously; its `root` is the same node; its `css` equals the printed text."
- PC-PRC-012 (Event-driven): "When a listener throws a `node.error`-built CssSyntaxError, it propagates with `plugin` set to the plugin name."
- PC-PRC-013 (Ubiquitous): "`process` accepts an existing Root or any object with toString."

## Results, Warnings, And Messages (PC-RES)

- PC-RES-001 (Ubiquitous): "Result exposes css, content (alias), root, opts (incl. from), processor, toString()===css."
- PC-RES-002 (Ubiquitous): "`messages` accumulates message objects; `warnings()` returns exactly those with type 'warning'."
- PC-RES-003 (Ubiquitous): "`node.warn(result, text, opts)` appends a Warning anchored to the node; `result.warn(text, opts)` appends one without a node."
- PC-RES-004 (Ubiquitous): "Warning exposes type 'warning', text, plugin (auto-filled inside a listener), node, and line/column/endLine/endColumn narrowed by word or index."
- PC-RES-005 (State-driven): "While a warning has no node, its position fields are undefined."
- PC-RES-006 (Ubiquitous): "Warning#toString() is plugin, ': ', then when anchored the input identifier with line and column, ': ', then the text."

## Positions And Error Construction (PC-POS)

- PC-POS-001 (Ubiquitous): "`positionBy({word})` returns the word's first-occurrence position; `{index}` offsets into the node; `{}` returns the node's start; positions carry 1-based line/column and 0-based offset."
- PC-POS-002 (Ubiquitous): "`rangeBy({word})` covers exactly the word; `rangeBy({})` covers the whole node."
- PC-POS-003 (Ubiquitous): "`input.fromOffset(offset)` converts a 0-based offset into 1-based `line` and `col`."
- PC-POS-004 (Ubiquitous): "`node.error(message, opts)` returns (never throws) a positioned CssSyntaxError, whole-node by default, narrowed by word/index."
- PC-POS-005 (Ubiquitous): "`input.error(message, line, column)` builds an error at an explicit position."
- PC-POS-006 (State-driven): "While a node has no source, `node.error` still returns a CssSyntaxError with undefined position fields."

## Error Semantics (PC-ERR)

- PC-ERR-001 (Unwanted behavior): "Parsing text with an unclosed block, unclosed comment, unclosed string, stray closing brace, or a word where a declaration is required throws CssSyntaxError with line/column at the offending token."
- PC-ERR-002 (Ubiquitous): "CssSyntaxError is an Error with name 'CssSyntaxError', reason, message = identifier:line:column: reason, file when known, source, 1-based line/column and endLine/endColumn when a range is known."
- PC-ERR-003 (Ubiquitous): "showSourceCode(false) renders an uncolored code frame with a '>' marker and caret; toString() combines name, message, and frame."

## Cross-View Invariants (PC-CVI)

- PC-CVI-001 (Ubiquitous): "parse(text).toString() === text for any text that parses; toJSON→fromJSON→toString produces the same text."
- PC-CVI-002 (Ubiquitous): "css read from a completed run (lazy css property or awaited Result) equals result.root.toString(); warnings() === messages filtered to type 'warning'."
- PC-CVI-003 (Ubiquitous): "For every walked node: node.root() is the tree root; parent.nodes[parent.index(node)] is the node; first/last equal boundary members."
- PC-CVI-004 (Ubiquitous): "positionBy({}) equals source.start; rangeBy({}) ends one column past source.end's column at source.end's offset; fromOffset(start.offset) reports start.line."
- PC-CVI-005 (Ubiquitous): "Reassigning one property changes only that property's printed form; untouched sibling properties keep raw text."
- PC-CVI-006 (Ubiquitous): "A clone of an unmodified node prints identically; structural edits leave the tree printing correctly."
- PC-CVI-007 (Ubiquitous): "One pipeline run delivers every reachable rule/decl/atrule/comment in the final tree to its enter listener, including nodes inserted or mutated during the run."
