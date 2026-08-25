# Dynaconf v5 synthetic evaluator

This directory is the pre-anchor frozen evaluator for the local Dynaconf
settings and durable publication system described in `SPEC.md`. The roster is
case-native: 22 Atomic, 40 Integration, and 28 System/E2E roots. Composition is Integration plus
System/E2E, and Combined is the mean of the Atomic and Composition rates.

The evaluator uses the pinned clean source at commit
`32f38478350a80020e7aab60a3cbd29dd7f8d9ea`, a mechanically copied source with
the preregistered settings patch plus v4 durable resources and v5 recoverable
cross-owner publication, and an importable callable dummy. All roots
run in separate fresh pytest processes with UTF-8, warning-as-error, isolated
temporary directories, package provenance checks, candidate-tree checks, and
manifest-bound gate verification. Timeouts, collection failures, provenance
failures, non-call-phase failures, and unexpected process statuses invalidate a
run and never become low scores.

The candidate packet is limited to the clean product specification and runtime
contract recorded by `STRICT-PAYLOAD-MANIFEST.json`. Root maps, mutation labels,
tests, reference patch, reference outcomes, and calibration evidence are
evaluator-only.
