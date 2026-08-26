repo: square/javapoet
source_path: /tmp/refs (shallow clone at tag javapoet-1.13.0)
commit: 714e05ca60179285746604452324262b126dcb2d
src_loc: 4426
test_functions: 365
test_files: ~20 files under src/test/java/com/squareup/javapoet
dominant_test_styles: unit; output-string assertions against generated source (behavioral: the produced source IS the product)
public_docs: https://github.com/square/javapoet README (format-string mini-language), javadoc
core_fact_source: immutable spec model (TypeSpec/MethodSpec/FieldSpec/CodeBlock) emitted as Java source with import resolution
derived_views: builder API validation; emitted source text of JavaFile; toString of each spec; name/import resolution decisions; format-string placeholders ($L/$S/$T/$N) expansion
external_deps: none at runtime
test_import_audit: clean ~5% — upstream tests are public-API string assertions
docs_test_alignment: aligned — README documents the $-placeholder language and builder contracts
contamination_note: javapoet@1.13.0, released 2020-05, relative to training cutoff: before
decision: keep
reason: code-generation engine with a self-defined format mini-language, import-collision resolution rules, and validation rules on modifiers — one model, several textual projections
risks: smallest candidate (4.4k non-blank LOC, above the 3k floor); emitted-text assertions must pin only documented formatting rules (2-space indent default, import ordering)
scope_plan: target_subdomain=full library minus javax.lang.model mirrors (no annotation-processor Elements interop), expected_oracle_max=100
difficulty_shapes: rule reimplementation (format language + import resolution); validation rules (modifier legality); >=3 cooperating objects (TypeSpec, MethodSpec, CodeBlock, JavaFile)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
