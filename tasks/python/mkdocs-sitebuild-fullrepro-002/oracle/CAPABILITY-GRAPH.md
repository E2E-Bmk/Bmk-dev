# Capability graph

The evaluator has six durable owners plus ordinary MkDocs primitives.
Evaluator admission is a separate, non-scored control plane. Its sealed
arbitrary-candidate mode binds the complete source tree and evaluator protocol
before collection, requires every valid root to reach the semantic-call phase,
and revalidates the seal and tree after the nine order-round vectors.

Candidate-packet admission also statically maps every oracle import, public
call, attribute, collection operation, type check, and returned object protocol
to a generalized contract clause.  That audit covers object shape and resource
lifecycle without consulting candidate source.

Durable records have an independent shape graph.  Their shared envelope and
the required nested keys/types of all six owner bodies are candidate-visible;
the private registry maps every oracle-observed path to that public schema and
forbids unchecked dictionary/list indexing.  Missing fields and unexpectedly
empty selected collections therefore remain semantic observations rather than
harness exceptions.

| Owner | Independent state/mechanism | Public projections |
|---|---|---|
| C | normalized effective configuration generations | config record, plugin set, build generation |
| D | source discovery and acknowledged change journal | added/modified/removed sets, pending snapshot |
| L | page identity lineage and revisions | URI-to-identity map, rename transfer, retired identities |
| P | prepared and visible artifact generations | staging snapshot, visible manifest, stale-writer fence |
| S | search artifact and semantic page receipts | artifact digest, title/location/lineage receipts |
| O | durable event outbox | stable event IDs, pending/delivered state, attempt counts |

Ordinary public surfaces are configuration loading (Q), files (F), pages (A),
navigation (N), search output (X), build orchestration (B), and errors (E).

The scored graph covers primitive edges within Q/F/A/N/E; independent owner
transitions within C/D/L/P/S/O; cross-owner generation consistency; prepare to
publish handoff; acknowledgement ordering; fencing; event retry; owner
corruption; and multi-process reopen workflows.  Every Composition root has a
counterfactual implementation that can pass its prerequisites while failing
the seam—for example, stable lineage with eager acknowledgement, correct
publication without a fence, or a correct search artifact without lineage
receipts.
