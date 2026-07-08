# Stage 3 Filter Notes

Track A was used. Track B was not triggered because the upstream kept set is well above 30 nodeids and includes atomic, integration, and system-style cross-view coverage.

Total nodeids: 3214
Covered kept: 1312
Spec gaps: 0
Source-only: 265
Excluded: 1637
Final scoreable: 1312

Layer counts:
- atomic: 766
- integration: 518
- system_e2e: 28

Global exclusions/source-only rules:
- Development tooling checks in `test_codestyle.py` are excluded.
- Private helper tests for `listify`, `_prep_ordered_arg`, `_identify_callback`, direct `__getattr__`, private queue containers, and exact repr strings are source-only.
- Exact backend graph style/cache/import-shape assertions are source-only.
- Markup `rep()` exact callback-reference string formatting is source-only.

Dummy gate policy:
- Kept nodeids must fail a dummy public-surface stub; any nodeid observed passing the stub is excluded.

Reference gate:
- Passed nodeids retained as scoreable: 1323
- Skipped nodeids excluded as environment/optional-dependency gated: 1620

Dummy gate:
- Nodeids that passed the dummy stub and were excluded: 11
