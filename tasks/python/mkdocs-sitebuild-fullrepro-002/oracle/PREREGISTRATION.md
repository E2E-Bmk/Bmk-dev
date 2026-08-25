# Qualification preregistration

- Authority: Synthetic Design Constitution 2026-08-14 v1 and Source-blank
  Anchor Predictiveness Findings 2026-08-15.
- Scoring formula: macro Atomic rate; macro Composition rate over Integration
  and System roots; Combined = their mean; Gap = Atomic - Composition.
- Roots: 12 Atomic, 14 Integration, 10 System.  Mutation roots: 26.
- M1 expected vector: all 36 roots pass.
- M2 expected vector: A01-A06 and I01-I04 pass; all other roots fail at a
  semantic assertion/call boundary.
- Dummy expected vector: no roots pass.  It must preserve public imports,
  classes, and call signatures and fail finitely only when semantics are used.
- Candidate-packet admission requires every public symbol imported by the
  semantic oracle to be named by the candidate-visible compatibility contract,
  including the public exception hierarchy and ordinary file/navigation
  helpers.  An AST operation audit must additionally account for every public
  call, attribute, type relationship, mapping/sequence operation, length,
  iteration, indexing, truth protocol, and return shape used by the oracle.
  Each operation must map to a generalized candidate-visible clause.  Static
  import or operation mismatch blocks freeze.
- Candidate-packet admission also requires a complete public schema for the
  envelope and body of every durable owner record.  A static key inventory must
  map every directly observed durable path to that schema and reject unchecked
  oracle subscripting or selection.  Missing keys, wrong record types, and
  unexpectedly empty selected lists are valid semantic failures.  Raw harness
  `KeyError`/`IndexError` remains invalid; `KeyError` attributable to a wrapped
  public MkDocs function/constructor or a candidate-tree public method is
  semantic.
- Anchor mode has no expected pass vector. It accepts an arbitrary candidate
  only with a gate-issued HMAC seal binding its canonical root, complete clean
  source tree, candidate-visible payload, evaluator protocol, and candidate
  identity. Reference, dummy, gate-contained, stale, mutated, symlinked, or
  structurally incomplete roots are rejected before semantic scoring.
- Orders: natural, reverse, and the fixed permutation in SCORER-CONFIG.json.
  Each order runs three rounds.  Every root receives a fresh interpreter.
- Invalid, never scored: import/attribute/signature/type/not-implemented error;
  warning; timeout; collection; setup/teardown; provenance; source-integrity;
  receipt; unattributed harness indexing; harness; or infrastructure failure.
- Every valid pass or fail receipt must reach `semantic-call`; a collection,
  provenance, import, or structural failure can never become a product score.
- Reference source and payload trees are hashed before and after every run.
  Patched M1 must match the exact registered patch; M2 must be clean at the
  pinned commit/tree.  Candidate payload is source-blank and contains only
  SPEC.md, TASK.md, and ENVIRONMENT.json.
- Anchors are forbidden until a later explicit authorization.  This gate stops
  at formally-frozen-pre-anchor.
