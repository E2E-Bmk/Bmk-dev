repo: json-path/JsonPath
source_path: /tmp/refs (shallow clone at tag json-path-2.9.0)
commit: af7e516c69df680a6584fca7180ef082eb67c96c
src_loc: 12231
test_functions: 593
test_files: ~60 files under json-path/src/test/java (unit + operator + provider matrices)
dominant_test_styles: unit; provider-parameterized matrices; some exact-string reprs
public_docs: README (path syntax, operators, filters, options), javadoc
core_fact_source: parsed JSON document model queried/mutated through compiled JsonPath expressions under Configuration options
derived_views: JsonPath.read/parse fluent API; compiled JsonPath objects; filter/criteria API; write operations (set/add/put/delete/renameKey/map); Option flags changing result shape
external_deps: json-smart (default provider), slf4j-api — both resolved by Maven as runtime deps of the target
test_import_audit: HIGH_RISK ~30% — tests import internal path token classes in places; Track B generated-only oracle planned
docs_test_alignment: aligned — README documents the exact operator/option semantics the oracle asserts
contamination_note: json-path@2.9.0, released 2024-01-30, relative to training cutoff: before
decision: keep
reason: query-language rule engine: grammar + evaluation semantics + option flags (ALWAYS_RETURN_LIST, DEFAULT_PATH_LEAF_TO_NULL, AS_PATH_LIST, SUPPRESS_EXCEPTIONS) form library-specific factor product
risks: jayway syntax partially memorizable from README; option interaction matrix and write-API semantics are not; deep-scan ordering is implementation-defined (avoid order-sensitive assertions on deep scan)
scope_plan: target_subdomain=read/compile/options/filters/write ops via public com.jayway.jsonpath surface (no spi/internal), expected_oracle_max=100
difficulty_shapes: rule reimplementation (path grammar + evaluation); configuration factor product (Option set); >=3 cooperating objects (Configuration, ParseContext, JsonPath, Criteria)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
