repo: apache/commons-jexl
source_path: /tmp/refs (shallow clone at tag rel/commons-jexl-3.4.0)
commit: 1555adf4cb2b21d15c03b1bcb7e79b75529656ab
src_loc: 30619
test_functions: 843
test_files: ~80 files under src/test/java/org/apache/commons/jexl3
dominant_test_styles: unit; heavy engine-option matrices
public_docs: https://commons.apache.org/proper/commons-jexl/reference/syntax.html + apidocs
core_fact_source: parsed script AST evaluated against JexlContext variable state under JexlEngine options
derived_views: JexlEngine createExpression/createScript evaluate; JxltEngine templates; JexlContext state before/after; getVariables/getParameters introspection; JexlException error taxonomy (strict vs lenient, silent)
external_deps: commons-logging (runtime dep of target)
test_import_audit: HIGH_RISK ~25% — some tests reach parser internals; Track B generated-only oracle planned
docs_test_alignment: aligned — syntax reference documents operators/coercion the oracle asserts
contamination_note: commons-jexl3@3.4.0, released 2024-06, relative to training cutoff: before
decision: keep
reason: expression-language engine: JexlArithmetic coercion rules, strict/lenient/silent axes, side-effect operators, and script scoping are library-specific and non-memorizable as a whole
risks: reference build uses javacc codegen (Docker reference install must warm ph-javacc-maven-plugin); scope excludes JexlSandbox/Uberspect customization and JXLT templates beyond basics
scope_plan: target_subdomain=expression/script evaluation + arithmetic coercion + context interaction + error taxonomy (no sandbox/permissions/introspection SPI), expected_oracle_max=110
difficulty_shapes: rule reimplementation (coercion + operator semantics); configuration factor product (strict x lenient x silent); >=3 cooperating objects (engine, script, context, arithmetic)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
