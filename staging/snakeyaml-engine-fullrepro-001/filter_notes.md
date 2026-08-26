repo: snakeyaml/snakeyaml-engine (bitbucket)
source_path: /tmp/refs (shallow clone at tag snakeyaml-engine-2.9)
commit: da5e518605eda2d52ff419bdb77f774a337555bd
src_loc: 14759
test_functions: 420
test_files: ~90 files under src/test/java/org/snakeyaml/engine (unit + spec suite harness)
dominant_test_styles: unit + YAML-test-suite golden events; some white-box internal (scanner/parser) tests
public_docs: https://bitbucket.org/snakeyaml/snakeyaml-engine/wiki/Documentation, javadoc
core_fact_source: node graph / event stream produced by the load pipeline and consumed by the dump pipeline
derived_views: Load (compose+construct to java objects); Dump (represent+serialize+present); low-level Compose to Node; settings builders (LoadSettings/DumpSettings) affecting both directions
external_deps: none at runtime
test_import_audit: HIGH_RISK ~50% — many upstream tests exercise internal scanner/parser classes; Track B generated-only oracle planned
docs_test_alignment: aligned — wiki documents load/dump settings and behavior the oracle asserts
contamination_note: snakeyaml-engine@2.9, released 2024-12, relative to training cutoff: before
decision: keep
reason: YAML 1.2 load/dump engine: two symmetric multi-stage pipelines over one node model with settings interactions; goyaml precedent on the go lane
risks: YAML is a public standard (partial memorization); mitigated by asserting engine-specific settings behavior (flow styles, scalar styles, anchors, canonical output)
scope_plan: target_subdomain=Load/Dump/Compose public API + settings (no low-level emitter/scanner API), expected_oracle_max=100
difficulty_shapes: rule reimplementation (YAML resolution + emission rules); round-trip equivalence judgements; >=3 cooperating objects (settings, Load, Dump, Node model)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
