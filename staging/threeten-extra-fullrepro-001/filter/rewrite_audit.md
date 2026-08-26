# Rewrite Audit — threeten-extra-fullrepro-001

Oracle source: **generated_only** (Track B). No upstream test was copied or
rewritten; the upstream suite (~1739 test functions, dominated by large
arithmetic and boundary matrices) was used only as a behavior checklist.

Every oracle test was written directly against the spec's public surface and
validated empirically against the pinned 1.8.0 artifact before being pinned:

- 114 atomic tests across eleven files covering interval and date-range
  construction, half-open containment, the relational algebra (abuts /
  overlaps / encloses / isConnected / union / intersection / span),
  single-unit amounts and their arithmetic, combined period-duration
  amounts, year-week and year-quarter partials (including the week-53
  resolution rule), the Coptic / Julian / International Fixed calendar
  structures and leap rules, the mutable clock, and the declared error
  semantics.
- 25 integration tests across three files covering algebra consistency
  between intervals and ranges, ISO conversion round trips and epoch-day
  agreement across the three chronologies, and amount/partial round trips
  linking between/addTo, atDay/from, parse/toString, and clock stepping.

Assertions pin only behavior stated in the spec: fixed ISO correspondences
(Coptic 1737-01-01 = 2020-09-11, the Julian 13-day offset, the International
Fixed special days), leap-rule classifications, documented text forms, and
the declared exception classes (`DateTimeException`,
`DateTimeParseException`, `ArithmeticException`).

Every test imports only `org.threeten.extra` symbols listed in the spec's
Public Interface (enforced by the import lint; see `lint_result.txt`).
