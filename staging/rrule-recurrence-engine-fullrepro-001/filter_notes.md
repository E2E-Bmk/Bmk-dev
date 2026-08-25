# filter_notes — rrule-recurrence-engine-fullrepro-001

```
repo: jkbrzt/rrule (npm name rrule)
source_path: https://github.com/jkbrzt/rrule (local mirror wip/repo-cache/rrule)
commit: 9f2061febeeb363d03352efe33d30c33073a0242 (master HEAD 2023-11-10, matches npm rrule@2.8.1 publish time)
language: typescript
src_loc: 4369 (src/**/*.ts excluding tests)
test_functions: 109 top-level it() call sites, but the dominant helper testRecurring() expands to several hundred assertion groups (test/rrule.test.ts alone drives ~2500 expectations)
test_files: test/*.test.ts (12 files: rrule, rruleset, rrulestr, parseoptions, parsestring, optionstostring, nlp, cache, datewithzone, dateutil, helpers)
dominant_test_styles: unit + integration through the public API (jest); expected values are concrete Date lists via a shared testRecurring helper; no snapshot files
public_docs: README.md (jkbrzt/rrule) — full API documentation: constructor options table, occurrence methods, string parsing (rrulestr / fromString / parseString / optionsToString), natural language (toText / fromText / parseText), RRuleSet API, Weekday, datetime helper; RFC 5545 recurrence semantics as background
core_fact_source: one recurrence definition (normalized option set: freq/interval/wkst/count/until + by-rules) shared by every projection
derived_views: (1) occurrence enumeration all()/between()/before()/after()/count(), (2) RFC 5545 string round-trip toString()/fromString()/rrulestr(), (3) parsed option introspection origOptions vs normalized options, (4) natural-language text toText()/fromText()/parseText(), (5) set algebra RRuleSet (rrule/rdate/exrule/exdate) with merged, deduped, sorted output and its own string/valueOf projection
external_deps: tslib only (runtime); oracle needs only vitest/typescript
test_import_audit: HIGH_RISK for direct reuse — upstream tests import from '../src/index' relative paths and lean on jest-specific helpers (test/lib/utils.ts) that themselves import '../../src'; not portable to a clean npm install; oracle is Track B generated (precedent: orama-search-engine-fullrepro-001, oracle_source=generated_only)
docs_test_alignment: aligned — README documents exactly the library-API projections the tests exercise
contamination_note: rrule@2.8.1, released 2023-11-10; public since 2012 → treat as known; anti-memorization via novel dtstart/fixture values (2030-2033 dates) distinct from upstream tests and README examples
decision: keep
reason: recurrence rule engine (reimplementation of RFC 5545 expansion rules — the candidate-selector difficulty shape "reimplementation of a language or format rule") with 5 independent public projections over one shared fact source; BYSETPOS/WKST/BYWEEKNO interactions resist pattern-matching even for models that know the API shape
risks: RFC 5545 is a public standard (API shape is memorizable — mitigated by novel fixtures and by the difficulty living in expansion arithmetic, not API recall); dual projection surface is large -> scope plan; local-time "UTC-as-local" date convention must be stated precisely or every date assertion is unfair
scope_plan: target_subdomain=recurrence expansion + string round-trip + options normalization + natural-language text + RRuleSet algebra, all in the UTC date convention; expected_oracle_max=90. Excluded: tzid/timezone conversion (environment-dependent), byeaster, custom NLP locales/getText, cache internals, DateWithZone.
difficulty_shapes: reimplementation-of-format-rule (RFC 5545 expansion); equivalence judgement (string round-trip must reproduce only caller-provided options); integration tests spanning >=3 projections (parse -> enumerate -> serialize -> text)
```
