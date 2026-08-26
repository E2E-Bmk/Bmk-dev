repo: uniVocity/univocity-parsers
source_path: /tmp/refs (shallow clone at tag v2.9.1)
commit: 943a542c909709b5e4e7ccd97831bc2d6b8673f4
src_loc: 35724
test_functions: 564
test_files: ~90 files under src/test/java (unit + example-driven; testng)
dominant_test_styles: unit + tutorial-style examples; TestNG upstream
public_docs: https://github.com/uniVocity/univocity-parsers README + tutorial, javadoc
core_fact_source: parser engine state over character streams: format detection, row records, headers, processed beans
derived_views: CsvParser/TsvParser/FixedWidthParser parseAll/iterate; Record API (typed access by header); writers (CsvWriter etc.) round-trip; settings objects (format, header extraction, selection of columns); annotation-driven bean processors
external_deps: none at runtime
test_import_audit: HIGH_RISK ~30% — upstream TestNG + internal helpers; Track B generated-only oracle planned
docs_test_alignment: aligned — tutorial documents settings/processor semantics the oracle asserts
contamination_note: univocity-parsers@2.9.1, released 2021-01, relative to training cutoff: before
decision: keep
reason: configurable flat-file engine: quote/escape/comment/null-value rules x column selection x header mapping x fixed-width fields form a large behavioral product with writer/parser duality
risks: CSV basics are common knowledge; difficulty carried by settings interactions (unescaped quote handling, value trimming, padding, column reordering) and Record typed views
scope_plan: target_subdomain=CSV/TSV/fixed-width parse+write+records+column selection (no routines/JDBC/annotations), expected_oracle_max=110
difficulty_shapes: configuration factor product; writer/parser round-trip equivalence; >=3 cooperating objects (settings, format, parser, record metadata)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
