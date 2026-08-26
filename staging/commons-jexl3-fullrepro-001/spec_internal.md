<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — commons-jexl3-fullrepro-001

- task_id: commons-jexl3-fullrepro-001
- language: java
- repo: apache/commons-jexl (github)
- repo_commit: 1555adf4cb2b21d15c03b1bcb7e79b75529656ab (tag rel/commons-jexl-3.4.0)
- maven_coordinates: org.apache.commons:commons-jexl3
- package root: org.apache.commons.jexl3
- source boundary: JexlBuilder (strict/silent/safe/create), JexlEngine
  (createExpression/createScript), JexlExpression, JexlScript, JexlContext,
  MapContext, JexlException (+ nested Variable, Parsing). Excludes JXLT
  templates, sandbox/permissions/uberspect, custom arithmetic and operators,
  namespace functions, annotations, JSR-223 bridge, JexlFeatures,
  JexlOptions/JexlInfo/JexlOperator/JexlCache (Non-Goals).
- spec basis: commons-jexl syntax reference + apidocs public documentation
  and four empirical probe rounds against the pinned 3.4.0 artifact (probe
  programs under /tmp/probe during authoring): literal result types, integer
  truncation and Long widening, string concat associativity, coercing
  equality, elvis (truthiness) vs ?? (null-only) including undefined
  tolerance, matching operators, size/empty null handling, script scoping
  (var locals vs context write-through), parameter binding errors, and the
  strict/lenient/silent/safe divergence matrix (lenient 1/0 = 0.0; strict
  if(null) raises while ternary null condition selects the false branch).
- spec_version: v1
- delta: initial version.
