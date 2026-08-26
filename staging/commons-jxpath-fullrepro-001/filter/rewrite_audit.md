# Rewrite Audit — commons-jxpath-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~332 test functions, flagged HIGH_RISK in
screening because it builds on a shared TestBean hierarchy and reaches
model-internal pointers) was used only as a behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 1.4.0 artifact before being pinned:

- 101 atomic tests across ten files covering bean property steps and typed
  values, the attribute access form (@name and node[@name='p']), nested and
  descendant traversal, equality/comparison/positional/string-function
  predicates, alphabetical property enumeration with collection expansion,
  1-based collection indexing with strict out-of-range behavior, map dynamic
  properties (always-present keys, sorted enumeration, insert-on-write),
  XPath 1.0 result typing (Double arithmetic/count/sum, Boolean comparisons,
  String functions), typed reads and their conversion rules, canonical
  pointer paths per model with round-trips, relative contexts with
  root-anchored paths, setValue conversion and failure modes, the
  AbstractFactory contract (intermediate + leaf steps, declining-factory
  cause chain, declareVariable hook), removePath/removeAll semantics,
  variables (store lifecycle, $paths, predicates, reassignment), extension
  functions (ClassFunctions, PackageFunctions method calls, FunctionLibrary
  aggregation, replacement semantics, core-function survival), the DOM model
  (element text, attributes, indexed canonical paths, mutation, detachment),
  and the strict/lenient discipline with the placeholder-pointer write error.
- 27 integration tests across three files covering cross-model composition
  (map→bean, map→DOM, descendant search across boundaries, one query over
  bean and DOM twins), canonical-path round-trips across model boundaries,
  first-match/cardinality/round-trip agreement across the query views, write
  visibility across pointer/context/caller views, mode neutrality on
  matching paths, relative-context agreement with base contexts, full
  create→mutate→remove lifecycles (map entries, list reindexing, factory
  variable declaration), compiled-expression equivalence and context
  independence, context-chain variable resolution, and per-context setting
  independence over a shared graph.

Assertions pin only behavior stated in the spec, including its documented
edge values (map keys readable as null in strict mode; createPath requiring
factory handling for null leaf steps while createPathAndSetValue does not;
installing a function set replacing default method-call resolution).

Every test imports only `org.apache.commons.jxpath` symbols listed in the
spec's Public Interface (enforced by the import lint; see `lint_result.txt`).
