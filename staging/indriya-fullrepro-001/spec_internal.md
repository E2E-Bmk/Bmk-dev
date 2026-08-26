<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — indriya-fullrepro-001

- task_id: indriya-fullrepro-001
- language: java
- repo: unitsofmeasurement/indriya (github)
- repo_commit: tag 2.2 (release 2.2, Maven central tech.units:indriya:2.2)
- maven_coordinates: tech.units:indriya
- package root: tech.units.indriya
- source boundary: Quantities (getQuantity number/unit, number/unit/scale,
  text), ComparableQuantity (add/subtract/multiply/divide/inverse/negate/
  to/asType/compareTo/isGreaterThan/isLessThan/or-equal forms/
  isEquivalentTo/getValue/getUnit/getScale), Units system (getInstance/
  getName/getUnits + SI constants), AbstractUnit.ONE, unit algebra
  (multiply/divide/pow/root/getSystemUnit/getSymbol/getDimension/
  isCompatible/asType/getConverterTo/getConverterToAny), UnitConverter
  (convert/isIdentity/isLinear), MetricPrefix factories,
  Quantity.Scale ABSOLUTE/RELATIVE semantics, SimpleQuantityFormat and
  SimpleUnitFormat (getInstance/format/parse). Excludes locale/EBNF/
  delimiter formats, SPI/service lookup, mixed-radix and range types,
  non-metric systems, binary prefixes, internal numeric representation
  (Non-Goals).
- spec basis: unit-api javadocs + indriya public documentation and five
  empirical probe rounds against the pinned 2.2 artifact (probe programs
  under /tmp/probe during authoring): exact decimal arithmetic (0.1+0.2,
  /3*3, ten-tenths chains all exact; integral results render integral),
  left-unit rule for mixed add/subtract, unit composition on
  multiply/divide (m/s×s simplifies to m), same-unit division cancelling
  to ONE while cross-unit division keeps km/m (compatible with ONE,
  converts to plain ratio), structural unit equality (m·m == SQUARE_METRE,
  m/s == METRE_PER_SECOND, m³ == CUBIC_METRE but KILO(METRE).divide(HOUR)
  != KILOMETRE_PER_HOUR and N·m != JOULE, J/s != WATT — named derived
  constants beyond the product-formed ones are NOT asserted equal to
  algebra), prefixed getSymbol() null vs base "m", conversions (1 km →
  integral 1000 m; 36 km/h → exactly 10 m/s; 20 °C → 293.15 K), converter
  agreement and isIdentity/isLinear (K→°C answers false), scale matrix
  (ABS 10°C→283.15 K, REL 10°C→10 K factor-only both directions; ABS+ABS
  → 303.15 ℃, ABS+REL → 30 ℃ ABSOLUTE, REL+REL → 20 ℃ RELATIVE),
  comparison regimes (equals unit-sensitive/representation-insensitive,
  compareTo 0 across equivalent units, helper agreement), format round
  trips for all named constants + prefixed units (uf.parse("km/h")
  returns the KILOMETRE_PER_HOUR constant, not the algebra construction —
  invariant 5 scoped accordingly), parse equality across entry points
  (factory text == format parse == constructed), Celsius renders "℃"
  (tests avoid asserting temperature toString), error taxonomy
  (MeasurementParseException for garbage text/unknown symbol,
  ClassCastException for asType mismatch, checked IncommensurableException
  for getConverterToAny across dimensions).
- contamination_note: indriya 2.2 released 2023-11 — before training
  cutoff; mitigated by Specification Authority disclaimer and
  behavior-observed assertions.
- spec_version: v2
- delta: v2 tightens two clauses after probe round 4: same-unit (not
  same-dimension) division cancels to ONE, and the unit format round-trip
  invariant is scoped to named constants and prefixed base units.
- note: javax.measure:unit-api 2.2 and tech.uom.lib:uom-lib-common 2.2 are
  compile dependencies; API types (Quantity, Unit, UnitConverter,
  MetricPrefix, Scale, exceptions) come from unit-api and are outside the
  lint target root.
