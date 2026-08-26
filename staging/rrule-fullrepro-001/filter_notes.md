# Stage 1 screening — rrule-fullrepro-001

repo: fmeringdal/rust-rrule (workspace member rrule)
source_path: https://github.com/fmeringdal/rust-rrule (local clone /tmp/refs/rust-rrule)
commit: 1c3420e356e4a89b1e10ff4ea1ab9cf6da42c3ab (release v0.14.0)
src_loc: ~9000 non-test (15123 total in rrule/src minus 6031 in src/tests minus 68 bin; remaining in-file #[cfg(test)] mods small)
test_functions: 317 in-crate (src/tests: rrule.rs 173, rfc_tests.rs 39, rruleset.rs 24, regression 5, serde 2, daylight_saving 2, datetime 2; plus ~70 unit tests in iter/parser/validator modules); zero external test files
test_files: all under rrule/src (in-crate #[cfg(test)] mods only)
dominant_test_styles: property-of-occurrence-stream checks (expected datetime vectors), parser round-trips, validation error checks
public_docs: docs.rs/rrule 0.14.0 (crate root with RFC-referenced property table, RRule/RRuleSet/Frequency/NWeekday/Tz item docs), README, RFC 5545 §3.3.10/§3.8.5 recurrence semantics
core_fact_source: one recurrence model — DTSTART + a set of RRULE properties (FREQ, INTERVAL, COUNT, UNTIL, WKST, BYMONTH, BYWEEKNO, BYYEARDAY, BYMONTHDAY, BYDAY with ordinals, BYHOUR, BYMINUTE, BYSECOND, BYSETPOS) plus RDATE/EXRULE/EXDATE sets
derived_views: (1) RFC 5545 string parser (RRuleSet::from_str / set_from_string, RRule<Unvalidated> FromStr); (2) typed builder (RRule::new + by_* setters) with validate(dt_start) two-phase typestate; (3) Display/ToString serialization back to property strings; (4) the iterator engine (RRuleSet::all(limit) -> RRuleResult, all_unchecked, IntoIterator) producing timezone-aware occurrence streams with DST handling; (5) RRuleSet composition algebra (rrule+exrule+rdate+exdate, before/after windows); (6) getter surface (get_freq/get_by_*/get_dt_start) exposing normalized properties
external_deps: chrono 0.4, chrono-tz 0.10, regex 1.11, thiserror 2.0, log — all pure; builds clean on cargo 1.83 (MSRV 1.74, edition 2021); serde and cli-tool are non-default features (scoped out)
test_import_audit: all 317 upstream tests are in-crate (super::/crate:: imports) — structurally unavailable to an external oracle; generated-only oracle expected, upstream as behavioral checklist
docs_test_alignment: aligned — docs.rs + RFC describe exactly the parse/validate/iterate behavior the tests exercise
contamination_note: rrule@0.14.0, released 2025-01; recurrence algorithms are classic (python-dateutil lineage) and upstream fixtures (1997 dateutil dates) are memorization-prone — oracle uses fresh dates/timezones/assertion angles
decision: keep
reason: a language-rule reimplementation task (RFC 5545 recurrence semantics: BYxxx expansion vs limitation per frequency, BYSETPOS filtering, WKST-dependent week numbering, DST-aware timezone iteration) projected through four independent surfaces — string parser, typed builder with typestate validation, serializer, and the occurrence iterator — with a composition algebra (exrules/exdates) on top; resistant to pattern-matching because occurrence streams are jointly determined by many interacting properties.
risks: DST/timezone assertions must pin explicit named timezones (chrono-tz stable data; avoid Tz::LOCAL); iterator safety limits (MAX_ITER_LOOP) are implementation tuning — spec only the documented limit behavior; upstream validation error taxonomy is fine-grained — spec declares only the three public error types and their Display-independent conditions; 173-test rrule.rs is a checklist, not a source (in-crate)
scope_plan: target_subdomain = default-feature surface: parse/build/validate/serialize + iteration + set algebra + getters; scope out serde feature, cli-tool binary, Tz::Local/is_local, by_easter (non-RFC extension, feature-independent but documented as dateutil extension — keep only if probe-stable; decide in Stage 2), exact ParseError variant taxonomy; expected_oracle_max = 120

Difficulty shapes (selection rationale): reimplementation of a format rule (RFC 5545 recurrence dialect — expansion vs limitation semantics per FREQ, negative ordinals, week-numbering with WKST); equivalence judgement (parse -> normalize -> Display round-trips where distinct inputs normalize to one canonical form); integration tests spanning >=3 projections (string -> typed properties -> occurrence stream -> serialized form on one fixture).
