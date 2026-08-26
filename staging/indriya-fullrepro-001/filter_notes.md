repo: unitsofmeasurement/indriya
source_path: /tmp/refs (shallow clone at tag 2.2)
commit: 88d2ebeba8264fcbc748414de8e36c2e24fd199a
src_loc: 18581
test_functions: 928
test_files: ~120 files under src/test/java/tech/units/indriya
dominant_test_styles: unit; arithmetic/format matrices
public_docs: https://unitsofmeasurement.github.io/indriya/ site + javadoc; JSR-385 spec for the API artifact
core_fact_source: quantity values bound to units within a unit dimensional system (Units system of units)
derived_views: quantity arithmetic (add/subtract/multiply/divide/to conversions); unit algebra (multiply/divide/pow/prefix/transform); comparison/equivalence (isEquivalentTo vs equals); SimpleQuantityFormat/NumberDelimiterQuantityFormat parse/format round-trip; getters (value/unit/scale)
external_deps: javax.measure:unit-api + tech.uom.lib:uom-lib-common (compile deps of target, stay available to the candidate)
test_import_audit: clean ~15% — most tests go through public API/facade
docs_test_alignment: aligned — javadoc + JSR-385 document conversion/scale semantics asserted
contamination_note: indriya@2.2, released 2023-11, relative to training cutoff: before
decision: keep
reason: reference implementation of a measurement algebra: unit conversion graphs, prefix arithmetic, ABSOLUTE vs RELATIVE scale rules, and equivalence-vs-equality judgements; pint precedent on the python lane
risks: numeric representation internals (RationalNumber) are implementation detail — oracle asserts numeric values via doubleValue/compareTo/isEquivalentTo, not internal types; scope excludes spi/format edge providers
scope_plan: target_subdomain=Quantities/Units factories + arithmetic + conversion + comparison + SimpleQuantityFormat (no spi/ObjectFormat/EBNF format), expected_oracle_max=100
difficulty_shapes: equivalence judgements (isEquivalentTo across prefixes/transformations); rule reimplementation (dimensional algebra, scale semantics); >=3 cooperating objects (unit, quantity, format, system-of-units)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
