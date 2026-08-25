repo: prosemirror/prosemirror-model
source_path: https://code.haverbeke.berlin/prosemirror/prosemirror-model (wip/repo-cache/prosemirror-model-src; GitHub mirror ProseMirror/prosemirror-model lags at 1.25.4)
commit: 09098e3b00a2e36843040bcde1b7af9adf76816e (tag 1.25.11)
language: typescript
src_loc: 3582 (src/*.ts excl. README)
test_functions: 309 (it() callbacks in test/*.ts)
test_files: 8 (test-content, test-diff, test-dom, test-mark, test-node, test-replace, test-resolve, test-slice)
dominant_test_styles: unit + integration over documents built with prosemirror-test-builder; ist assertions; jsdom for DOM suite
public_docs: https://prosemirror.net/docs/ref/#model (full module reference), https://prosemirror.net/docs/guide/#doc (document guide: structure, indexing, slices, schema, content expressions)
core_fact_source: one persistent (immutable) document tree - Node objects owning Fragment children, Mark sets, and attrs, all governed by a Schema whose compiled NodeType/MarkType tables and content-expression automata decide which trees are valid
derived_views: (1) tree construction/algebra projection (schema.node/text, create/createChecked/createAndFill, copy/mark/cut/slice/replace);
  (2) JSON serialization projection (toJSON/fromJSON round trips for Node/Fragment/Mark);
  (3) position projection (flat integer positions: resolve/ResolvedPos navigation, nodeAt/childAfter/childBefore, NodeRange);
  (4) content-rule projection (ContentMatch: matchType/matchFragment/validEnd/fillBefore/findWrapping/defaultType over compiled content expressions);
  (5) text projection (textContent/textBetween with block separators and leaf text);
  (6) equality/diff projection (eq/sameMarkup/Mark.sameSet/findDiffStart/findDiffEnd);
  (7) validity projection (check(), createChecked errors, canReplace/canReplaceWith/canAppend, ReplaceError).
external_deps: none at runtime (orderedmap vendored dependency); DOM projection needs a DOM - excluded from scope
test_import_audit: HIGH_RISK for direct reuse - every suite imports prosemirror-test-builder (a published package that itself depends on the real prosemirror-model, so installing it beside a candidate breaks scorer isolation) plus ist and jsdom -> Track B generated oracle using only the target package's public API
docs_test_alignment: aligned - the reference manual documents the same classes and methods the tests exercise (content expressions, replace algebra, resolution, JSON)
contamination_note: prosemirror-model@1.25.11, released 2026-07-11, relative to training cutoff: likely before for the API line (stable since 2017); difficulty rests on precise content-expression, replace-depth, and position-arithmetic semantics rather than surface novelty
decision: keep
reason: rule-engine reimplementation (content-expression automaton, replace algebra with open depths, position arithmetic, mark-set algebra) with 7 public projections over one immutable tree fact source; griffe-shape difficulty (equivalence judgements via eq/sameSet, language-rule reimplementation via content expressions, >=3-projection integration).
risks: (1) upstream tests non-portable without breaking isolation -> generated_only oracle, every expected value observed by executing 1.25.11;
  (2) DOM parsing/serialization needs jsdom and a large parse-rule surface -> excluded from scope (spec non-goal);
  (3) position arithmetic is easy to assert wrongly -> probe every resolved-position value before asserting;
  (4) content expressions have subtle compilation corners (nested sequences, counted repeats) -> spec states the expression language precisely; oracle sticks to documented operators.
scope_plan: target_subdomain=Schema construction (node/mark specs, attrs, groups, content expressions, marks constraints), Node/Fragment/Mark/Slice algebra (create/createChecked/createAndFill, copy/mark/cut/slice/replace/append/eq/diff), JSON round trips, ResolvedPos/NodeRange navigation, ContentMatch queries, text projections, validity checks (check/canReplace/canReplaceWith/canAppend/ReplaceError); expected_oracle_max=100
excluded: DOMParser/DOMSerializer and all parse/serialize DOM rules, whitespace parsing options, prosemirror-test-builder helpers, schema-basic/schema-list packages, linebreakReplacement, dynamic schema mutation
