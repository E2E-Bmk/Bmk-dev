repo: apache/commons-jxpath
source_path: /tmp/refs (shallow clone at tag rel/commons-jxpath-1.4.0)
commit: 146f2534e885fd7085fba4bf3fb658d434416504
src_loc: 28515
test_functions: 332
test_files: ~70 files under src/test/java
dominant_test_styles: unit; model-matrix tests (beans/maps/DOM/JDOM)
public_docs: https://commons.apache.org/proper/commons-jxpath/users-guide.html, apidocs
core_fact_source: object-graph context (beans, maps, collections, DOM) addressed by XPath expressions through JXPathContext
derived_views: getValue/getPointer/iterate/selectNodes queries; setValue/createPath mutation; Pointer.asPath canonical paths; lenient vs strict missing-path behavior; variables; multiple models over same query language
external_deps: none at runtime (DOM via JDK)
test_import_audit: HIGH_RISK ~35% — tests build on shared TestBean hierarchy (rebuilt as oracle support fixtures); Track B generated-only oracle planned
docs_test_alignment: aligned — users guide documents pointer/path semantics the oracle asserts
contamination_note: commons-jxpath@1.4.0, released 2024-08, relative to training cutoff: before
decision: keep
reason: XPath-over-object-graphs engine: applying path grammar to java bean/map/collection models with canonical pointer paths and creation rules is library-specific; multiple data models are true multi-projection
risks: dormant project (docs old but complete); XPath 1.0 core is a public standard — difficulty carried by the object-model mapping rules; scope excludes JDOM/servlet models
scope_plan: target_subdomain=JXPathContext over beans/maps/collections/DOM + pointers + write/create + variables (no JDOM, no servlet, no XML namespaces beyond defaults), expected_oracle_max=100
difficulty_shapes: rule reimplementation (path grammar over object models); canonical-form equivalence (Pointer.asPath); >=3 cooperating objects (context, pointer, variables, functions)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
