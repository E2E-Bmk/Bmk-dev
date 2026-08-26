# Rewrite Audit — commons-jexl3-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~843 test functions, flagged HIGH_RISK in
screening because a share reaches parser internals) was used only as a
behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 3.4.0 artifact before being pinned:

- 60 atomic tests across seven files covering literal result types (Integer /
  Long / Double / String / int[] array / Map / Set literals), arithmetic
  coercion (integer truncation, Long widening on overflow, floating
  promotion, string concatenation with left-to-right associativity),
  comparison and coercing equality with the eq/ne aliases, truthiness-driven
  logic including the ternary, elvis (truthiness-based) versus ?? (null-only)
  with undefined tolerance, matching operators (=~ regex and containment, !~,
  =^, =$), size/empty including null handling, navigation and method calls,
  assignment write-through and the compound form, script statements and
  scoping (var locals versus context writes, if/while/for over collections
  and ranges, return, lambdas), parameter binding and introspection
  (getParameters, getVariables), the engine discipline axes, and the declared
  error taxonomy (JexlException, .Variable with getVariable, .Parsing).
- 27 integration tests across three files covering the strict/lenient/silent
  divergence matrix over identical source and context (undefined variables,
  division by zero, null operands, null conditions), the safe-axis flip,
  truthiness uniformity across constructs, assignment/context agreement,
  wrapped-map single-store behavior, parsed-object reuse across contexts,
  expression/script agreement on shared formulas, introspection predicting
  strict errors, and multi-feature pipelines (lambdas + loops, fallback
  chains, coercion over context values).

Assertions pin only behavior stated in the spec, including its documented
edge values (lenient 1/0 = 0.0; strict if(null) raises while the ternary
treats a null condition as false).

Every test imports only `org.apache.commons.jexl3` symbols listed in the
spec's Public Interface (enforced by the import lint; see `lint_result.txt`).
