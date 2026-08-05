# anytree Tree Structure Public Behavior Specification

## Product Overview

anytree is a Python library for building and inspecting rooted trees. A tree
node has a parent reference and an ordered tuple of children. The public
surface also provides traversal iterators, search helpers, path resolution,
semantic rendering rows, and dictionary or JSON serialization.

## Scope

This package covers `Node`, `AnyNode`, `NodeMixin`, and `LightNodeMixin`;
parent and children mutation; path, ancestry, descendant, sibling, root,
leaf, height, depth, and size properties; pre-order, post-order, level-order,
grouped level-order, and zigzag traversal; search and cardinality checks;
`Resolver`; `RenderTree`; and the public dictionary and JSON exporters and
importers. Composed mutation, lookup, rendering, and serialization workflows
are included.

## Public Import Surface

Applications may import the node classes, tree exceptions, iterators, search
functions, `Resolver`, and `RenderTree` from `anytree`. `DictExporter` and
`JsonExporter` are imported from `anytree.exporter`; `DictImporter` and
`JsonImporter` are imported from `anytree.importer`. Tests use no
implementation-only modules and no source test helpers.

## Product State Model

Each node is either a root or attached to one parent. Children retain insertion
order and are exposed as a tuple. A node's path starts at its root and ends at
the node; reverse path iteration walks toward the root. Tree metrics and
relationship projections are derived from the current attachment graph.
`Node` supplies a `name`; `AnyNode` stores arbitrary attributes; mixins add the
same tree behavior to user classes, with `LightNodeMixin` supporting slots.

## Error Semantics

Invalid parent or child objects and duplicate children raise public tree
errors. Self-parenting and attaching an ancestor below its descendant raise
`LoopError`. Search cardinality violations raise `CountError`. Resolver
failures use its public resolver error classes. Assertions check exception
types and resulting tree state, not incidental message wording.

## Cross-View Invariants

Parent and children views agree after attach, detach, reorder, and reparent
operations. Paths, roots, depths, sizes, leaves, and descendants agree with
the traversal order. Search and resolver results identify the same node objects
as traversal results. Render rows preserve node order and attribute values.
Exported structures and imported trees preserve public attributes, child order,
and parent links.

## Representative Workflow

A representative workflow constructs a small named tree, moves a leaf between
branches, verifies paths and metrics, searches by a public attribute, resolves
relative and wildcard paths, renders semantic rows, exports parsed dictionary
or JSON data, imports it again, and verifies that the restored tree can be
mutated and exported again. Additional workflows cover custom mixin classes,
slots, filtered traversal, custom path attributes, file-like JSON buffers,
and deterministic child ordering.

## Non-Goals

The package does not require network access, sockets, sleeps, timing
measurements, ambient host state, external executables, GraphViz, filesystem
fixtures, private modules, source tests, exact exception text, or whole-output
rendering snapshots. Unicode branch glyphs are not used as a portability
contract; rendering checks focus on row structure and semantic values.

## Invocation Protocol

Install the requirements listed for this package, make the target implementation
importable as `anytree`, and run:

```bash
python -m pytest <test-directory> -q -W error
```

The tests are deterministic and local. JSON file-like behavior uses an in-memory
text buffer only.

## Environment

The intended evaluation environment is Linux with Python 3.11 and without network access
during the test run. The target package is not pre-installed; the implementation
under evaluation must provide the `anytree` package. Required runtime and test
packages are `pytest` and `pytest-json-report`.

## Evaluation Notes

The tests are split into atomic checks for individual public behaviors and
integration checks that combine multiple tree operations and projections.
Integration dependency markers document atomic prerequisites and refer only to
physical atomic test names. A minimal import-only implementation may collect
the tests but should pass well below ten percent because the suite exercises
substantive tree behavior.
