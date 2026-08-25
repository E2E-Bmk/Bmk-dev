<!-- INTERNAL
task_id: prosemirror-model-doc-tree-fullrepro-001
spec_version: v1
delta: initial draft
source_boundary: prosemirror-model@1.25.11 npm package (executed via probes, wip/probe/pm), prosemirror.net reference manual #model section and guide (document, schema, content expressions, slices, indexing); every asserted behavior observed by executing the pinned release
-->

# prosemirror-model Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`prosemirror-model` is a document-model library for structured text. A document is an immutable (persistent) tree of `Node` values: each node has a type, an attribute object, an ordered `Fragment` of children, and — for inline content — a set of `Mark` values such as emphasis or links. Which trees are valid is governed by a `Schema`: a compiled table of node types and mark types whose content rules are written in a small expression language and enforced by a match automaton.

Because nodes are immutable, every update produces a new tree that shares unchanged sub-structure with the old one. The library supplies the algebra for those updates: flat integer positions addressing any point in the tree, resolved position objects for navigating ancestry, slices that capture a range with "open" ends, and a replace operation that splices a slice between two positions while enforcing schema validity. Documents, fragments, marks, and slices all serialize to plain JSON and reconstruct through the schema.

The installable package name is `prosemirror-model`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require HTML or DOM parsing and serialization, parse rules, or any browser/DOM integration.
- This specification does not require whitespace-normalization options or editor-oriented spec flags (selectability, draggability, defining/isolating behavior).
- This specification does not require dynamic schema mutation after construction.
- This specification does not require attribute value validation beyond presence and defaulting.
- This specification does not define behavior for content expressions that reference undeclared node names.

## Representative Workflows

**Define a schema, build a document, round-trip it.** A schema compiles node specs into types; documents are built through the schema and serialize to JSON:

```ts
import { Schema, Node } from 'prosemirror-model';

const schema = new Schema({
  nodes: {
    doc:       { content: 'block+' },
    paragraph: { group: 'block', content: 'inline*' },
    heading:   { group: 'block', content: 'inline*', attrs: { level: { default: 1 } } },
    text:      { group: 'inline' },
  },
  marks: { em: {} },
});

const doc = schema.node('doc', null, [
  schema.node('heading', { level: 2 }, [schema.text('Title')]),
  schema.node('paragraph', null, [schema.text('Body ', [schema.mark('em')]), schema.text('text')]),
]);

const restored = Node.fromJSON(schema, doc.toJSON());
restored.eq(doc); // true
```

**Resolve positions and replace a range.** Flat positions address points in the tree; slices cut from one place splice into another:

```ts
const $pos = doc.resolve(9);
$pos.parent.type.name;    // the textblock at position 9
$pos.start(); $pos.end(); // boundaries of that textblock's content

const slice = doc.slice(9, 12);
const updated = doc.replace(9, 12, slice); // replacing a range with itself
updated.eq(doc); // true
```

## Schemas And Node Types

A schema turns declarative node and mark specs into compiled type objects that govern every document built with it.

**Construction.** A `Schema` accepts a spec object with a `nodes` map (node name to node spec), an optional `marks` map (mark name to mark spec), and an optional `topNode` naming the top-level node type (defaulting to `"doc"`). The compiled schema exposes `nodes` and `marks` — maps from name to `NodeType` / `MarkType` — plus `topNodeType` and the original `spec`. Each `NodeType` and `MarkType` carries its `name` and a `schema` back-reference.

**Node specs.** A node spec's `content` is a content expression (see Content Rules) over child node names and group names; `group` assigns the node to space-separated groups usable in expressions; `inline: true` makes the node inline; the node named `text` is the built-in text node and belongs to whatever groups its spec declares. A node spec's `marks` string names the mark types (or groups, or `"_"` for all) allowed on the node's inline content; WHEN `marks` is omitted, THEN nodes with inline content allow every mark and other nodes allow none. A `NodeType` reports `isBlock`, `isInline`, `isText`, `isLeaf`, `isAtom`, `isTextblock` (a block type with inline content), `inlineContent`, and `hasRequiredAttrs()`.

**Attributes.** A node or mark spec's `attrs` object maps attribute names to attribute specs; an attribute spec with a `default` property is optional, one without is required. WHEN a node or mark is created with a `null` attribute argument, THEN every attribute is filled from its default, and attributes with no default are filled with `null`. If an attribute object is supplied that omits a required attribute, then creation must raise a `RangeError`. Attribute names absent from the spec are dropped from the created node. `hasRequiredAttrs()` returns `true` exactly when some attribute has no default.

**Creation helpers.** `schema.node(type, attrs, content, marks)` builds a node from a type name or `NodeType` — content may be a `Fragment`, a single node, an array of nodes, or null — and raises a `RangeError` for an unknown type name. `schema.text(string, marks)` builds a text node; empty text nodes must raise a `RangeError`. `schema.mark(type, attrs)` builds a mark from a name or `MarkType`. `NodeType.create` builds a node of that type without content validation; `createChecked` additionally validates content and marks and raises a `RangeError` on violation; `createAndFill` synthesizes required boundary content (see Content Rules) and returns `null` when the content cannot be completed.

**Type queries.** `validContent(fragment)` reports whether a fragment satisfies the type's content rule (including mark validity). `compatibleContent(other)` reports whether two types share any allowed content. `allowsMarkType(markType)` reports whether the node's inline content may carry the mark; `allowedMarks(marks)` filters a mark set down to the allowed ones. `contentMatch` exposes the type's content automaton start state.

**Schema-construction failures.** If a content expression mixes inline and block child types, then schema construction must raise a `SyntaxError`. If a node type with required attributes occupies a required (non-optional) position in a content expression, then schema construction must raise a `SyntaxError` — such nodes cannot be generated automatically, so the expression would create unfillable holes.

## Documents, Nodes, And Fragments

Nodes are immutable values; all update methods return new nodes, and fragments are immutable child sequences.

**Node anatomy.** A node exposes `type`, `attrs`, `content` (a `Fragment`), `marks` (an array, empty for unmarked nodes), and — for text nodes — `text`. Child access goes through `childCount`, `child(index)` (raising `RangeError` when out of range), `maybeChild(index)` (returning `null`), `firstChild`/`lastChild` (`null` when empty), and `forEach(fn)` which passes each child with its offset and index. `descendants(fn)` visits every descendant with its position; returning `false` from the callback must prevent descending into that node's children. `nodesBetween(from, to, fn)` visits the nodes touching a range the same way.

**Size arithmetic.** A text node's `nodeSize` is its text length. A leaf node's `nodeSize` is 1. Every other node's `nodeSize` is the size of its content plus 2 — one token for entering and one for leaving. A fragment's `size` is the sum of its children's sizes. These numbers are the basis of the position scheme in Positions And Resolution.

**Node flags.** `isText`, `isLeaf` (no content allowed), `isAtom` (leaf, or spec-marked atomic), `isBlock`/`isInline`, and `isTextblock` (block with inline content) mirror the type-level flags on each node instance.

**Text projections.** `textContent` concatenates all text in the subtree. `textBetween(from, to, blockSeparator, leafText)` extracts the text in a range: WHERE `blockSeparator` is given, THEN it is inserted between block-level nodes; WHERE `leafText` is given as a string or as a function of the leaf node, THEN non-text leaves contribute that text; otherwise leaves contribute nothing.

**Derived nodes.** `copy(content)` returns a node with the same type, attributes, and marks but new content (empty when omitted). `mark(marks)` returns the node with its mark set replaced. `cut(from, to)` returns the sub-node between two content offsets — on text nodes it slices the string and keeps the marks. `slice` and `replace` are covered in Slices And Replacement.

**Equality.** `eq` is deep structural equality over type, attributes, marks, and content. `sameMarkup` compares type, attributes, and marks while ignoring content; `hasMarkup(type, attrs, marks)` checks a node against explicit markup. `toString` renders a debugging tree such as `doc(paragraph("ab"), horizontal_rule)` with mark names wrapping marked text.

**Fragments.** `Fragment.from` accepts `null` (yielding the shared `Fragment.empty`), a single node, an array of nodes, or a fragment (returned unchanged). WHEN adjacent text nodes with identical mark sets meet while building or appending fragments, THEN they must be merged into one text node. Fragments expose `size`, `childCount`, `child`/`maybeChild`, `firstChild`/`lastChild`, `forEach`, `append` (merging adjacent compatible text), `cut(from, to)`, `replaceChild(index, node)`, `addToStart(node)`, `addToEnd(node)`, `eq`, and `toString`. `findDiffStart(other)` returns the first position where two fragments differ, or `null` when they are equal; `findDiffEnd(other)` returns an object with positions `a` and `b` where the difference ends in each fragment, or `null`.

**Validity.** `check()` walks the tree and raises a `RangeError` when any node's content or marks violate its type's rules; a tree built entirely through validated paths must pass `check()`.

## Positions And Resolution

One flat integer scheme addresses every point in a document, and resolved positions expose the ancestry at a point.

**The position scheme.** Position 0 is before the first child of the document. Entering a non-leaf node costs one token, so the first position inside a node is one more than the position before it. Each character of a text node counts one token, each leaf node counts one token, and leaving a non-leaf node costs one token. `nodeAt(pos)` returns the node starting at or covering a position (`null` past the end); `childAfter(pos)` and `childBefore(pos)` return an object with the direct child at that side (`node`, possibly `null`), its `index`, and its starting `offset`.

**Resolution.** `resolve(pos)` returns a `ResolvedPos` and must raise a `RangeError` for positions outside `0..content.size`. A resolved position exposes `pos`, `depth` (0 at the top level), and `doc`, plus per-depth accessors that default to its own depth: `node(depth)` (the ancestor at a depth), `index(depth)`, `indexAfter(depth)`, `start(depth)` / `end(depth)` (the boundaries of that ancestor's content), and `before(depth)` / `after(depth)` (positions immediately outside the ancestor). If `before` or `after` is asked at depth 0, then a `RangeError` must be raised — there is no position around the top node. `parent` is the node at the position's own depth, `parentOffset` the offset within it, and `textOffset` the distance into a text node (0 at node boundaries). `nodeBefore` and `nodeAfter` return the adjacent nodes, splitting text nodes at the position, or `null` at parent boundaries. `posAtIndex(index, depth)` maps an index in an ancestor back to a flat position. `marks()` returns the marks at the position (taken from the preceding inline content). `sameParent(other)` reports whether two positions live in the same parent; `sharedDepth(pos)` returns the deepest depth whose node contains both positions; `min(other)` / `max(other)` return the lesser and greater position object.

**Block ranges.** `blockRange(other)` returns a `NodeRange` spanning the block-level ancestry that covers both positions — exposing `start`, `end`, `depth`, `parent`, `startIndex`, and `endIndex` — and `NodeRange` is directly constructible from two resolved positions and a depth.

## Slices And Replacement

A slice captures a range of a document with open ends, and replace splices one between two positions.

**Slicing.** `slice(from, to)` returns a `Slice` whose `content` holds the covered material and whose `openStart` and `openEnd` count how many node boundaries at each end were cut through rather than included whole. WHEN a range covers exactly the inside of one textblock, THEN the slice is the inline fragment with both open depths 0. A slice's `size` is its content size minus the open depths. `Slice.empty` is the shared empty slice. `Slice.maxOpen(fragment)` builds a slice with the maximum possible open depths along the fragment's edges — leaf edges contribute no openness. Slices serialize with `toJSON` (returning `null` for the empty slice) and rebuild with `Slice.fromJSON`, where `null` input yields the empty slice.

**Replacement.** `replace(from, to, slice)` returns a new document in which the slice replaces the range. The open sides of the slice must be joined with the cut-open sides of the surrounding document: replacing the text range of two adjacent paragraphs with a slice of two open paragraphs merges the outer halves with the slice halves. WHEN the range and slice come from the same document region — `doc.replace(a, b, doc.slice(a, b))` — THEN the result equals the original document. If the joined result violates a node's content rule, then a `ReplaceError` must be raised; if the slice is opened deeper than the insertion point's depth, then a `ReplaceError` must be raised. `ReplaceError` is an `Error` subclass exposed by the package.

**Feasibility queries.** `canReplace(from, to, fragment)` reports whether a child-index range of a node can be replaced by a fragment (the empty fragment tests deletion). `canReplaceWith(from, to, type)` tests a single replacement type. `canAppend(other)` reports whether the other node's content can be appended — for an empty other node it falls back to type content compatibility. `cut(from, to)` returns the document region between two positions as a standalone node.

## Content Rules

Each node type's content expression compiles into a match automaton that answers validity, completion, and wrapping queries.

**The expression language.** A content expression is a sequence of terms separated by whitespace, where each term names a node type or group and takes an optional modifier: `?` (zero or one), `*` (zero or more), `+` (one or more), `{n}` (exactly n), or `{n,m}` (n through m). Parentheses group sub-expressions and `|` separates alternatives. An empty expression allows no content.

**Match states.** `NodeType.contentMatch` is the automaton's start state, a `ContentMatch` value. `matchType(type)` returns the state after consuming one child type, or `null` when the child is not allowed there. `matchFragment(fragment)` consumes a whole fragment. `validEnd` reports whether the state may end the content. `defaultType` returns the first generatable type at the state (one constructible without required attributes), or `null`. `edgeCount` and `edge(index)` enumerate the outgoing transitions. `node.contentMatchAt(index)` returns the state reached after the node's first `index` children.

**Completion.** `fillBefore(after, toEnd)` returns a fragment of synthesized nodes that lets the state continue with `after` — and WHERE `toEnd` is true, THEN also reach a valid end — or `null` when impossible. `findWrapping(target)` returns the (possibly empty) array of node types that must wrap a `target` child to make it placeable at the state, or `null` when no wrapping exists. `createAndFill` on a node type uses these rules: it synthesizes content before and after the given fragment so the node is valid, skipping optional positions whose types cannot be generated, and returns `null` when completion fails.

## Marks

Marks are immutable annotations on inline nodes, kept in normalized sets.

**Creation and identity.** `MarkType.create(attrs)` and `schema.mark` build marks; attribute defaulting and the required-attribute `RangeError` follow the same rules as nodes. `mark.eq(other)` compares type and attributes, so two marks of one type with different attributes are distinct.

**Set algebra.** A mark set is an ordered array. `mark.addToSet(set)` returns a set with the mark inserted in schema declaration order, without duplicates (adding an equal mark returns an equal set). `mark.removeFromSet(set)` removes equal marks. `mark.isInSet(set)` tests membership by equality. `Mark.none` is the shared empty set; `Mark.setFrom` accepts `null`, a single mark, or an array (which it sorts into schema order); `Mark.sameSet(a, b)` compares two sets element-wise.

**Exclusion.** A mark spec's `excludes` string names mark types or groups the mark expels, with `"_"` meaning every mark. WHEN a mark is added to a set containing marks it excludes, THEN those marks are removed; WHEN a set contains a mark that excludes the added mark, THEN the addition returns the set unchanged. `MarkType.excludes(other)` exposes the relation; a mark does not exclude itself unless the spec says so.

**Marks on nodes.** Text nodes carry the marks given at creation; `node.mark(marks)` returns the node with the set replaced. Node specs constrain which marks may appear (see Schemas And Node Types); `createChecked` and `check()` must raise a `RangeError` when content carries a disallowed mark. `rangeHasMark(from, to, markOrType)` reports whether any inline content in a range carries the mark.

## JSON Serialization

Every model value serializes to schema-independent JSON and reconstructs through a schema.

**Shapes.** A node serializes to an object with `type`, plus `attrs` when it has attributes, `content` when it has children, `marks` when marked, and `text` for text nodes. A mark serializes to `type` plus optional `attrs`. A fragment serializes to an array of node JSON. A slice serializes to an object with `content`, `openStart`, and `openEnd`.

**Reconstruction.** `Node.fromJSON(schema, json)`, `Fragment.fromJSON(schema, json)`, `Mark.fromJSON(schema, json)`, and `Slice.fromJSON(schema, json)` rebuild values, resolving type names through the schema. A serialize-then-parse round trip must produce a value `eq` to the original.

## State Model

The core state is one immutable document tree per document value, governed by one compiled schema:

- **Schema tables** — name-keyed `NodeType` and `MarkType` objects, each type carrying attribute specs, group membership, mark constraints, and a compiled content automaton.
- **Document trees** — persistent `Node` values owning `Fragment` children and `Mark` sets; all mutation-shaped methods return new values sharing unchanged sub-structure.

Public projections of that state:

1. **Tree algebra** — creation helpers, `copy`/`mark`/`cut`/`slice`/`replace`, fragment operations.
2. **Flat positions** — integer addressing, `nodeAt`/`childAfter`/`childBefore`, `resolve` with per-depth navigation, `NodeRange`.
3. **Content rules** — `ContentMatch` queries, `createChecked`/`createAndFill`/`check`, feasibility tests.
4. **Text projection** — `textContent` and `textBetween`.
5. **Equality and diffing** — `eq`, `sameMarkup`, `Mark.sameSet`, `findDiffStart`/`findDiffEnd`.
6. **JSON round trips** — `toJSON`/`fromJSON` on nodes, fragments, marks, and slices.

All projections read the same tree: sizes reported by the algebra are the positions the resolver navigates, and validity decided by the content automaton is what creation and replacement enforce.

## Error Semantics

| Condition | Outcome |
|---|---|
| Content expression mixes inline and block types | `Schema` constructor raises `SyntaxError` |
| Type with required attributes in a required content-expression position | `Schema` constructor raises `SyntaxError` |
| Unknown node type name in `schema.node` | raises `RangeError` |
| Attribute object omits a required attribute at node or mark creation | raises `RangeError` |
| Empty text node (`schema.text("")` or empty string) | raises `RangeError` |
| `createChecked` or `check()` on content violating the content rule or mark constraints | raises `RangeError` |
| `child(index)` out of range | raises `RangeError`; `maybeChild` returns `null` |
| `resolve(pos)` outside the document | raises `RangeError` |
| `before(0)` / `after(0)` on a resolved position | raises `RangeError` |
| `replace` producing invalid content, or slice deeper than the insertion point | raises `ReplaceError` |
| `matchType` / `matchFragment` on disallowed content | returns `null`; no throw |
| `fillBefore` / `findWrapping` / `createAndFill` when completion is impossible | returns `null`; no throw |

Error message text is not part of this contract; assertions rely on error class and behavior.

## Cross-View Invariants

1. For every valid tree, `Node.fromJSON(schema, node.toJSON())` must be `eq` to the original, and the same round-trip law holds for fragments, marks, and slices through their own `fromJSON` entry points.
2. Size arithmetic and positions must agree: a non-leaf node's `nodeSize` equals its content size plus 2, a fragment's size equals the sum of child sizes, and the positions visited by `descendants` are exactly those where `nodeAt` returns that node.
3. Replacement must be consistent with slicing: for any valid range, `doc.replace(from, to, doc.slice(from, to))` is `eq` to `doc`, and `cut` agrees with the content of the corresponding slice.
4. The content automaton, creation, and checking must agree: a fragment for which `matchFragment` reaches a `validEnd` state (with allowed marks) is accepted by `validContent` and `createChecked` and passes `check()`; a fragment rejected by the automaton makes `createChecked` and `check()` raise.
5. `eq` and diffing must agree: `findDiffStart` returns `null` exactly when two fragments are `eq`, and `sameMarkup` holds exactly when type, attributes, and marks all match.
6. Mark algebra must be consistent across views: sets built with `addToSet` are in schema order and respect exclusion, `Mark.sameSet` treats them as equal to any equally-built set, text nodes report those sets through `marks`, resolved positions report them through `marks()`, and `rangeHasMark` agrees with membership.
7. Resolution must agree with child access: for any resolved position, `node(depth)`, `index(depth)`, and `posAtIndex` return values consistent with `child`, `childAfter`, and `childBefore` on the same tree.

## Public Interface

### Import Surface

```ts
import {
  Schema, Node, Fragment, Slice, Mark,
  NodeType, MarkType, ContentMatch,
  ResolvedPos, NodeRange, ReplaceError,
} from 'prosemirror-model';
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Schema` | class | Compiles node/mark specs into type tables; creation helpers `node`, `text`, `mark` |
| `Node` | class | Immutable document node; algebra, positions, text, JSON; static `fromJSON` |
| `Fragment` | class | Immutable child sequence; `from`, `empty`, append/cut/diff operations |
| `Slice` | class | Range of content with open ends; `empty`, `maxOpen`, JSON |
| `Mark` | class | Inline annotation; set algebra statics `none`, `setFrom`, `sameSet`, `fromJSON` |
| `NodeType` | class | Compiled node type; creation, flags, content and mark queries |
| `MarkType` | class | Compiled mark type; `create`, `excludes` |
| `ContentMatch` | class | Content automaton state; match, completion, and wrapping queries |
| `ResolvedPos` | class | Position with ancestry accessors returned by `resolve` |
| `NodeRange` | class | Block-level range between two resolved positions |
| `ReplaceError` | class | Error subclass raised by invalid `replace` calls |

### CLI Entry Points

There is no console script for this package. Programmatic use is through TypeScript/JavaScript imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The test toolchain is `vitest` with TypeScript; tests import the package under test by its package name `prosemirror-model`. No other third-party runtime packages are available or needed; no DOM is present.

The project must declare its packaging metadata in a standard `package.json` at the project root, exposing the package's public entry point under the name `prosemirror-model`, so the test suite can resolve `import { ... } from 'prosemirror-model'`.

## Appendix B: Assessment Notes

Assessment exercises the public surface described in this document across several dimensions: schema compilation including attribute defaulting and construction-time expression validation; node, fragment, and mark construction with size arithmetic and flags; the flat position scheme and resolved-position navigation; slicing and replacement with open depths and error cases; content-automaton queries and content completion; mark-set algebra with exclusion; text extraction; and JSON round trips. Tests are split into an atomic tier, each verifying a single behavior, and an integration tier composing several projections against shared trees. Expected values in tests were produced by executing this specification's reference behavior — matching the letter of this document is the only reliable strategy.
