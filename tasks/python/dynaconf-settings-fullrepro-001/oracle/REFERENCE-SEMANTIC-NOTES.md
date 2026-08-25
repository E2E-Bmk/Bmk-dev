# Dynaconf v5 reference semantic notes

The clean upstream authority is commit
`32f38478350a80020e7aab60a3cbd29dd7f8d9ea`, tree
`4a018399bfbb635abc4dc956c4a4cf17749ac54e`, installed distribution
`dynaconf==3.3.0.dev0`. It remains unmodified and must be Git-clean for M2.

The patched reference is a mechanical whole-tree copy of that source followed
by the v3 compatibility changes, v4 durable resources, and v5 recoverable
publication extension:

- `dynaconf/_spec2repo_v3.py` adds the nine preregistered public lifecycle
  mechanisms;
- `dynaconf/__init__.py` installs and exports that coherent synthetic surface.
- `dynaconf/_spec2repo_v4.py` adds the independent durable store, append-only
  lineage/watcher, and acknowledged artifact transport protocols;
- `dynaconf/__init__.py` also exports the v4 surface.
- `dynaconf/_spec2repo_v5.py` adds prepared-generation fencing, phase receipts,
  compensating recovery, duplicate suppression, and lineage reconciliation;
- `dynaconf/__init__.py` also exports the v5 surface.

The patch intentionally keeps ordinary source, environment, conversion,
validator, hook, and console behavior delegated to the pinned project. It does
not modify the evaluator, test fixtures, expected values, or scoring process.
Patch membership and hashes are fixed by `REFERENCE-PATCH-MANIFEST.json`.

The principal semantic divergences are public product laws: environment
contexts yield owned leases, explicit loads return transactional receipts,
snapshots are immutable generations, file bindings reevaluate owned resources,
validation transactions publish once, reload is a recoverable generation,
explicit hook pipelines own cleanup, history/inspection expose committed
generation identity, and artifact bundle/report publication preserves prior
bytes on late failure.

v4 adds process-durable fenced ownership with explicit crash adoption,
append-only source observations with rejected-revision recovery, and an outbox
whose delivery, acknowledgement, rollback, and replay are separate public
states. System observations cross these three resource owners rather than
reusing the in-memory settings transaction.

v5 adds a protocol ledger that crosses lineage, store, outbox, artifact, and
publisher ownership. The paired reference proves phase reopen in fresh
processes, stale-cursor rejection, post-commit/pre-ack compensation, publisher
replacement, duplicate delivery/ack idempotence, and divergence reconciliation.

The source-copy `.git` directory and generated caches are excluded from the
candidate tree digest. The patch source itself is score-bearing evidence. No
historical anchor candidate, score, or implementation is used by M1.
