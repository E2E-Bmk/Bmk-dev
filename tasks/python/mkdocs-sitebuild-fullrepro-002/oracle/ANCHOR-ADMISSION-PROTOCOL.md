# Sealed arbitrary-candidate anchor admission

MkDocs v14 freezes an `anchor` scorer mode before any source-blank anchor is
started. An evaluator operator first runs `anchor_admission.py` against the
finished candidate tree. The resulting JSON seal binds:

- the v14 suite and seal-domain identifiers;
- a public candidate identity and canonical candidate root;
- every admitted source file and its SHA-256 digest;
- the exact candidate-visible payload;
- the scorer, root registry, semantic oracle, fresh-process driver, public
  operation registry, and durable-record shape/key registry.

The seal is authenticated with a key kept in the evaluator payload and never
included in the candidate-visible packet. It is an admission capability, not
a product score. The scorer recomputes every bound fact before collection and
again after all roots. It rejects reference, dummy, evaluator-contained,
symlinked, cache-bearing, structurally incomplete, moved, or modified trees.

Anchor mode runs the same natural, reverse, and fixed-permuted orders for three
rounds, with a fresh interpreter and fresh project root for every semantic
root. Unlike qualification controls, it has no registered expected pass
vector. It reports Atomic, Integration, System, Composition, conditional,
adjusted, native, mutation, and non-mutation rates for the observed stable
vector.

A root is scoreable only after it reaches the semantic public-call phase.
Ordinary assertion mismatches, missing or wrongly typed required public record
fields, empty collections observed through a required non-empty operation,
public `mkdocs.exceptions` failures, and `KeyError` attributable to a wrapped
public MkDocs constructor/function or a candidate-tree public method are valid
product failures.  A raw
`KeyError` or `IndexError` escaping evaluator code remains an invalid harness
failure.  Collection, provenance, import, missing attribute, signature or type
errors, `NotImplementedError`, warnings, timeout, receipt, harness, and
infrastructure failures invalidate the run and produce no product score.

The pre-anchor admission control uses a temporary copy of the preregistered
behavior-empty dummy. It is deliberately known evaluator material and is not
an anchor. The control must collect all roots, pass seal provenance, reach the
semantic-call phase for every root, and score zero. Separate negative controls
must reject a missing required module, a tree changed after sealing, and a
structurally present candidate whose public call boundary is broken.  A
separate sealed control proves that a public-call `KeyError` produces a stable
zero semantic vector rather than invalidating the scorer.
