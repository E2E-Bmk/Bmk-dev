repo: jhy/jsoup
source_path: /tmp/refs (shallow clone at tag jsoup-1.18.3)
commit: 7c56eb26c8cc772c5c3d0e052dc076a128173c85
src_loc: 21869
test_functions: 1263
test_files: ~120 files under src/test/java/org/jsoup (unit + integration + fuzz)
dominant_test_styles: unit + integration; many string-golden HTML serializations
public_docs: https://jsoup.org/cookbook/, https://jsoup.org/apidocs/, README
core_fact_source: parsed Document tree (nodes, attributes, output settings) built by the HTML/XML parsers
derived_views: parse entry points; DOM traversal/manipulation API; CSS selector engine; cleaner/safelist; serialized HTML/XML output; text extraction
external_deps: none at runtime; tests use gson/jetty for fuzz+website tests (excluded)
test_import_audit: HIGH_RISK ~40% — upstream tests are same-package white-box (TokeniserTest, parser internals); Track B generated-only oracle planned
docs_test_alignment: aligned — cookbook/apidocs cover parse/select/manipulate/clean/output, same projections the oracle exercises
contamination_note: jsoup@1.18.3, released 2024-12-02, relative to training cutoff: before
decision: keep
reason: HTML parsing rule engine with 5+ public projections over one Document tree; whitespace/pretty-print and entity rules are library-specific
risks: high-popularity API (memorization); HTML5 parsing is a public standard — mitigated by asserting jsoup-specific output/normalization rules; scope excludes network Connection API
scope_plan: target_subdomain=parse+DOM+select+clean+serialize (no org.jsoup.Connection/HttpConnection), expected_oracle_max=110
difficulty_shapes: rule reimplementation (tree-construction + serialization rules); >=3 cooperating objects (Parser, Document/Element, OutputSettings, Selector, Cleaner); cross-view state (same tree projected as HTML, text, selector results)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
