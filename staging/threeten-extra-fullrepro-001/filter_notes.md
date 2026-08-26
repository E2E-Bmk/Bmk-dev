repo: ThreeTen/threeten-extra
source_path: /tmp/refs (shallow clone at tag v1.8.0)
commit: 583ef319e8ee09c0799b9d5cac4a779fd7f9fd99
src_loc: 29542
test_functions: 1739
test_files: ~80 files under src/test/java/org/threeten/extra
dominant_test_styles: unit; arithmetic/boundary matrices (JUnit 5)
public_docs: https://www.threeten.org/threeten-extra/ (user guide + javadoc)
core_fact_source: date-time values in alternative calendar systems and range/amount types layered over java.time
derived_views: Interval/LocalDateRange algebra (abuts/overlaps/encloses/union/intersection); amount types (Days/Weeks/Months/Years/PeriodDuration) arithmetic and parsing; YearWeek/YearQuarter field access and arithmetic; alternative chronologies (Coptic/Ethiopic/Julian/International Fixed) date conversion round trips; MutableClock
external_deps: none at runtime (java.time only)
test_import_audit: clean ~5% — upstream tests are public-API value assertions
docs_test_alignment: aligned — the project site documents each class's contract; javadoc is the primary reference
contamination_note: threeten-extra@1.8.0, released 2024-06, relative to training cutoff: before
decision: keep
reason: calendar rule reimplementation (leap rules and epoch alignment of Coptic/Julian/International Fixed chronologies are documented but not memorizable in aggregate) plus interval algebra with genuine equivalence judgements (abuts vs overlaps vs encloses)
risks: ISO parts (Days/Weeks arithmetic) are derivable — difficulty carried by chronology conversion and interval algebra; scope excludes Symmetry454/Pax/Accounting chronologies and packed YearWeek edge fields to keep the surface honest
scope_plan: target_subdomain=Interval+LocalDateRange+amount types+YearWeek/YearQuarter+Coptic/Julian/InternationalFixed chronologies+MutableClock, expected_oracle_max=110
difficulty_shapes: rule reimplementation (calendar leap/epoch rules); equivalence judgements (interval relations); cross-view consistency (chronology date <-> LocalDate round trips, range <-> interval)
oracle_plan: Track B generated-only Maven oracle (upstream suite used as a behavior checklist only), mirroring the shipped wip/java fullrepro packets.
