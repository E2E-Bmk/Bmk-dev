# EdgeGate Config Runtime

Implement the Python package `edgegate` according to `prd.md`.

You must implement the starter package in `starter/edgegate`. Keep the public
module names and public API stable. You may add internal helpers, but the scorer
will use only public APIs and CLI behavior.

Important constraints:

- Build a multi-module package; do not collapse the solution into one file.
- Preserve durable state, versions, digests, tombstones, reference graph,
  standalone generation, route matching, upstream selection, plugin merge, and
  reports as coherent public projections.
- Raise `EdgeGateError` with stable public `code` values.
- Do not use APISIX-specific names, exact error strings, private key layouts, or
  network proxy behavior.

See `prd.md` for the full product contract.
