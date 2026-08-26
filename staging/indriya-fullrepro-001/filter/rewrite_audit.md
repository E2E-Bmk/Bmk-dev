# Rewrite Audit — indriya-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~928 test functions across ~120 files, heavy
on parameterized arithmetic/format matrices and internal numeric types such
as RationalNumber) was used only as a behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 2.2 artifact before being pinned
(five probe rounds; two spec clauses were tightened when probing contradicted
the draft — same-unit vs same-dimension division cancellation, and the scope
of the unit format round-trip guarantee):

- 80 atomic tests across nine files covering quantity construction (number/
  unit/scale factories, text factory, integral-vs-decimal value shapes,
  toString), exact numerics (0.1+0.2 exactly 0.3, /3*3 restoring integral 1,
  exact km→m integral conversions), quantity arithmetic (left-unit rule for
  mixed add/subtract, unit composition on multiply/divide, same-unit
  division cancelling to ONE, cross-unit division keeping the quotient unit,
  inverse/negate, asType checks), unit algebra (system singleton and
  constants, prefixes with null getSymbol, multiply/divide/pow/root
  identities, structural equality vs compatibility, dimension views),
  conversion (scale factors, offsets, compound units, self-conversion,
  converter objects with isIdentity/isLinear, checked
  IncommensurableException), the three comparison regimes (unit-sensitive
  equals, representation-insensitive values, cross-unit compareTo and
  helpers, symmetric equivalence), scale semantics (ABSOLUTE vs RELATIVE
  construction, factor-only delta conversion both directions, the
  ABS+ABS/ABS+REL/REL+REL addition matrix), formatting and parsing
  (rendering, round trips, entry-point agreement, unit symbol parsing), the
  declared error taxonomy, and the immutable state model.
- 26 integration tests across three files covering the seven cross-view
  invariants (equivalence–conversion agreement, ordering–equivalence
  coherence over a pair matrix, arithmetic–unit-algebra agreement,
  conversion–converter agreement across five unit pairs, format round-trip
  agreement with the algebra-reparse caveat, exactness chains, left-unit
  rule), multi-step workflows (parse→convert→compute→format pipeline, trip
  speed with construction-sensitive units, speed×time simplification, mass
  and length ledgers, dimensionless ratio with percent, converter chains,
  time staircases), scale lifecycles (delta ledgers, summed deltas, scale
  round-trip divergence, kelvin-agreement of absolute sums), entry-point
  measure agreement, error-path state integrity, and a four-view
  one-measure agreement matrix.

Assertions pin only behavior stated in the spec, including its documented
edge values (structural unit equality distinguishing KILO(METRE).divide(HOUR)
from KILOMETRE_PER_HOUR; SimpleQuantityFormat and the text factory agreeing
on measure but not construction for compound symbols; relative deltas
converting factor-only; BigDecimal-vs-Double representation differences are
deliberately not asserted either way).

Every test imports only `tech.units.indriya` symbols listed in the spec's
Public Interface (enforced by the import lint; see `lint_result.txt`).
