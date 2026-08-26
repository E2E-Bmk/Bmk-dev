<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — threeten-extra-fullrepro-001

- task_id: threeten-extra-fullrepro-001
- language: java
- repo: ThreeTen/threeten-extra (github)
- repo_commit: 583ef319e8ee09c0799b9d5cac4a779fd7f9fd99 (tag v1.8.0)
- maven_coordinates: org.threeten:threeten-extra
- package root: org.threeten.extra
- source boundary: Interval, LocalDateRange, Days/Weeks/Months/Years,
  PeriodDuration, YearWeek/YearQuarter/Quarter, Coptic/Julian/International
  Fixed chronologies, MutableClock; excludes Symmetry454/Symmetry010/Pax/
  Accounting/Discordian/Ethiopic/BritishCutover chronologies, UTC/TAI scale
  types, PackedFields, DayOfMonth/DayOfYear/AmPm/Half/HourMinute/YearHalf,
  AmountFormats, OffsetDate, Temporals (Non-Goals).
- spec basis: threeten.org user guide/javadoc public documentation and two
  empirical probe rounds against the pinned 1.8.0 artifact (probe programs
  under /tmp/probe during authoring); fixed ISO correspondences (Coptic
  1737-01-01 = 2020-09-11, Julian +13 days, Ifc special days) verified by
  probe before being pinned.
- oracle: generated-only (Track B); upstream suite (~1739 test functions,
  large arithmetic matrices) used as a behavior checklist only.
