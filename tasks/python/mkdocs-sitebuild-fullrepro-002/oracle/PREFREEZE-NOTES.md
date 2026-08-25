# Pre-freeze notes

MkDocs v11, v12, and v13 remain immutable retired evidence.  V14 is the clean
successor to qualified v13 after its first source-blank candidate reached the
A07 semantic-call boundary but the evaluator read `body["generation"]`
directly.  The candidate's missing public record field escaped as a harness
`KeyError`, invalidating the run and producing no product score.  V13's public
operation audit covered MkDocs objects but did not inventory the required keys
of the durable JSON records.

V14 preserves the six independently durable owners, the qualified 36-root
semantics, sizeable mutation across all six, native `load_config`/`build`
controls, the distinct System layer, and sealed arbitrary-candidate protocol.
The clean successor adds the ordinary OSS record schema to the candidate
packet, validates every complete owner shape before observation, replaces raw
dictionary/list indexing with presence/length-checked helpers, and freezes a
36-path record inventory.  It retains the public-operation AST audit, now with
the additional checked Page-list length observation.

The gate is intentionally not frozen until patched M1, exact clean M2, dummy,
public-surface, static, tree, provenance, payload, and nine-vector stability
checks all pass.
The public-operation and record-shape audits must pass without inspecting
candidate source.  The sealed arbitrary-candidate admission control must also
prove collection, provenance, semantic-call classification, invalid structural
rejection, and semantic classification of an attributable public-call
`KeyError`.  Those controls are known behavior-empty infrastructure, not
source-blank anchors.  No source-blank anchor is authorized or started by this
work.
