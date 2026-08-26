# Clause register — rrule-recurrence-engine-fullrepro-001

Clause IDs are internal (sidecar); the candidate-visible spec body carries none of them.

## Dates And The UTC Convention (RRULE-DTC)

- RRULE-DTC-001 — "All recurrence arithmetic must read and write the UTC fields of `Date` values." (§Dates And The UTC Convention)
- RRULE-DTC-002 — "The `datetime` function ... accepts a year, a 1-based month, a day, and optional hour, minute, and second (each defaulting to 0), and returns a `Date` whose UTC fields equal exactly those values." (§Dates And The UTC Convention)
- RRULE-DTC-003 — "When a rule's start date is taken from the current clock because none was provided, the engine must truncate it to whole seconds." (§Dates And The UTC Convention)

## Defining A Recurrence (RRULE-DEF)

- RRULE-DEF-001 — "The `Frequency` export is a numeric enumeration with members `YEARLY` … `SECONDLY` bound to the integer values 0 through 6 in that order, and reverse lookup from value to name. The same seven members are exposed as static properties of `RRule`, and `RRule.FREQUENCIES` is the array of the seven frequency names in the same order. When `freq` is omitted, the rule must default to `YEARLY`." (§Defining A Recurrence)
- RRULE-DEF-002 — "`byweekday` — a `Weekday`, an integer in the recurrence weekday numbering, a weekday token string such as `\"TU\"`, or an array mixing these forms." (§Defining A Recurrence)
- RRULE-DEF-003 — "The `Weekday` class represents a day of the week in the recurrence numbering, where Monday is 0 and Sunday is 6 ... `getJsWeekday`, converting to JavaScript `Date.getDay` numbering where Sunday is 0 ... static `Weekday.fromStr`, converting a two-letter token back to a `Weekday`." (§Defining A Recurrence)
- RRULE-DEF-004 — "`nth`, which returns a new `Weekday` with the given ordinal (so `RRule.FR.nth(2)` means the 2nd Friday and stringifies as `\"+2FR\"`)." (§Defining A Recurrence)
- RRULE-DEF-005 — "`clone` on a rule returns an independent `RRule` with the same original options and therefore the same projections." (§Defining A Recurrence)

## Original versus normalized options (RRULE-NRM)

- RRULE-NRM-001 — "`origOptions` must hold exactly the options the caller supplied — no defaults added, values as given." (§Defining A Recurrence)
- RRULE-NRM-002 — "`options` must hold the fully normalized form, containing every recognized option key." (§Defining A Recurrence)
- RRULE-NRM-003 — "`byweekday` entries normalize to integer weekday numbers in `options.byweekday` ... while ordinal-carrying entries (from `nth`) are split out into `options.bynweekday` as `[weekday, n]` pairs; when only ordinal entries are given, `options.byweekday` is `null`." (§Defining A Recurrence)
- RRULE-NRM-004 — "`bymonthday` splits into `options.bymonthday` (positive values) and `options.bynmonthday` (negative values)." (§Defining A Recurrence)
- RRULE-NRM-005 — "When the frequency is coarser than the start date's precision and no explicit by-rule pins a component, the missing constraint derives from `dtstart` ... Time components below the frequency granularity likewise derive from `dtstart`." (§Defining A Recurrence)
- RRULE-NRM-006 — "`wkst` given as a `Weekday` or omitted normalizes to its integer weekday number (default 0, Monday)." (§Defining A Recurrence)

## Occurrence Enumeration (RRULE-ENM)

- RRULE-ENM-001 — "`all` returns every occurrence as an array of `Date` values in ascending order." (§Occurrence Enumeration)
- RRULE-ENM-002 — "`all` accepts an iterator callback invoked as each occurrence is generated with the occurrence and its index; iteration must stop at the first occurrence for which the callback returns `false`, and that occurrence is excluded from the result." (§Occurrence Enumeration)
- RRULE-ENM-003 — "`between` ... returns occurrences strictly between the two instants when `inc` is `false`, and includes occurrences falling exactly on either endpoint when `inc` is `true`. When `after` is not earlier than `before`, or no occurrences fall in the window, `between` returns an empty array." (§Occurrence Enumeration)
- RRULE-ENM-004 — "`before` returns the single latest occurrence at or before the argument (`inc` `true`) or strictly before it (`inc` `false`, the default), and `after` symmetrically returns the earliest occurrence at or after (or strictly after) the argument; both return `null` when no qualifying occurrence exists." (§Occurrence Enumeration)
- RRULE-ENM-005 — "`count` (the method) returns the total number of occurrences, and must equal the length of the array `all` returns for the same finite rule or set." (§Occurrence Enumeration)

## Expansion Semantics (RRULE-EXP)

- RRULE-EXP-001 — "Starting from `dtstart`, candidate periods advance by `interval` units of the frequency." (§Expansion Semantics)
- RRULE-EXP-002 — "A by-rule at a level coarser than or equal to the frequency filters candidates, while a by-rule at a finer level multiplies them." (§Expansion Semantics)
- RRULE-EXP-003 — "Negative `bymonthday` values count backward from month end (-1 is the last day); negative `byyearday` values count backward from year end, honoring leap years." (§Expansion Semantics)
- RRULE-EXP-004 — "`byweekno` selects ISO 8601 week numbers (weeks governed by `wkst`), and negative week numbers count from the year's last week." (§Expansion Semantics)
- RRULE-EXP-005 — "Inside a `MONTHLY` (or `bymonth`-constrained `YEARLY`) period, an ordinal weekday from `nth` selects the n-th matching weekday of the period from the start (positive n) or from the end (negative n)." (§Expansion Semantics)
- RRULE-EXP-006 — "After all other by-rules produce a period's candidate list, `bysetpos` selects elements by 1-based position from the start (positive) or end (negative) of that list." (§Expansion Semantics)
- RRULE-EXP-007 — "For `WEEKLY` rules with `interval` greater than 1, `wkst` determines the boundary at which a new week begins ... Changing `wkst` between Monday and Sunday must change the emitted sequence of a biweekly multi-weekday rule accordingly." (§Expansion Semantics)
- RRULE-EXP-008 — "`HOURLY`, `MINUTELY`, and `SECONDLY` rules advance by hours, minutes, and seconds respectively, applying `interval` at that granularity and carrying finer components from `dtstart`." (§Expansion Semantics)
- RRULE-EXP-009 — "Generation stops after `count` occurrences have been emitted, or once candidates pass `until` (occurrences equal to `until` are emitted)." (§Expansion Semantics)

## RFC String Projection (RRULE-STR)

- RRULE-STR-001 — "`toString` on a rule must emit a `DTSTART:` line when the caller provided `dtstart`, followed by an `RRULE:` line listing only properties the caller provided ... A rule constructed without `dtstart` emits no `DTSTART:` line." (§RFC String Projection)
- RRULE-STR-002 — "Defaults that were not supplied ... must not appear, but explicitly supplied values equal to defaults must appear." (§RFC String Projection)
- RRULE-STR-003 — "Frequencies serialize by name; weekday lists as two-letter tokens; ordinal weekdays with sign and ordinal; `wkst` as `WKST=` with the token of its day even when supplied numerically." (§RFC String Projection)
- RRULE-STR-004 — "The static `RRule.optionsToString` performs the same serialization directly from an options object." (§RFC String Projection)
- RRULE-STR-005 — "`RRule.parseString` converts a string in the same grammar back to a partial options object containing exactly the properties present in the string." (§RFC String Projection)
- RRULE-STR-006 — "An `UNTIL` value in date-only form (`20310304`) denotes midnight UTC of that day." (§RFC String Projection)
- RRULE-STR-007 — "Input containing only a single rule parses to an `RRule`; input with `RDATE`, `EXDATE`, `EXRULE`, or multiple `RRULE` lines parses to an `RRuleSet`." (§RFC String Projection)
- RRULE-STR-008 — "Its options object supports: `dtstart`, a `Date` merged into parsed rules that lack their own `DTSTART`; and `forceset`, a boolean defaulting to `false` which when `true` always yields an `RRuleSet` even for a single plain rule." (§RFC String Projection)
- RRULE-STR-009 — "When the input contains more than one `DTSTART` line, the first `DTSTART` applies to every rule parsed from the text." (§RFC String Projection)

## Natural Language Projection (RRULE-NLP)

- RRULE-NLP-001 — "`toText` renders the rule as a lowercase English phrase: frequency and interval, weekday lists, ordinal weekdays, month days, week numbers, a count bound, and an until bound." (§Natural Language Projection)
- RRULE-NLP-002 — "`isFullyConvertibleToText` returns `true` when every option of the rule is expressible in the phrase language and `false` otherwise." (§Natural Language Projection)
- RRULE-NLP-003 — "`RRule.parseText` converts such a phrase to a partial options object ... when the phrase cannot be interpreted, `parseText` must return `null` rather than raising." (§Natural Language Projection)
- RRULE-NLP-004 — "`RRule.fromText` composes `parseText` with construction and returns an `RRule`. For a rule whose options all lie in the phrase language, `RRule.fromText(rule.toText())` must define the same recurrence properties as the original." (§Natural Language Projection)

## Recurrence Sets (RRULE-SET)

- RRULE-SET-001 — "`rrule` adds an inclusion `RRule`; `exrule` adds an exclusion `RRule`; `rdate` adds one explicit occurrence `Date`; `exdate` adds one explicit exclusion `Date` ... The accessors `rrules`, `exrules`, `rdates`, and `exdates` return arrays reflecting what was added." (§Recurrence Sets)
- RRULE-SET-002 — "`all` on a set must return the union of all inclusion-rule occurrences and explicit `rdate`s, minus every instant produced by an exclusion rule or listed as an `exdate`, deduplicated ... and sorted ascending." (§Recurrence Sets)
- RRULE-SET-003 — "`valueOf` on a set returns an array of iCalendar lines ... `toString` must equal those lines joined with newlines." (§Recurrence Sets)

## Error Semantics (RRULE-ERR)

- RRULE-ERR-001 — "Constructor option `dtstart` is an invalid `Date` → `Error` raised at construction." (§Error Semantics)
- RRULE-ERR-003 — "`Weekday` constructed with ordinal 0, or `nth(0)` called → `Error` raised." (§Error Semantics)
- RRULE-ERR-004 — "`parseString`/`fromString`/`rrulestr` input contains an unknown property name → `Error` raised." (§Error Semantics)
- RRULE-ERR-005 — "`DTSTART`/`UNTIL`/`RDATE`/`EXDATE` timestamp fails the timestamp grammar → `Error` raised." (§Error Semantics)
- RRULE-ERR-006 — "`freq` outside the 0–6 enumeration → `Error` raised at construction." (§Error Semantics)
- RRULE-ERR-007 — "`bysetpos` value 0 or outside ±1…±366 → `Error` raised at construction." (§Error Semantics)
- RRULE-ERR-008 — "Non-`Date` argument to `between`, `before`, or `after` → `Error` raised." (§Error Semantics)
- RRULE-ERR-009 — "Non-`RRule` passed to `RRuleSet.rrule`/`exrule` → `Error` raised." (§Error Semantics)
- RRULE-ERR-010 — "Non-`Date` passed to `RRuleSet.rdate`/`exdate` → `Error` raised." (§Error Semantics)
- RRULE-ERR-011 — "`parseText` given an uninterpretable phrase → returns `null` (no error)." (§Error Semantics)
- RRULE-ERR-012 — "`between` window empty or inverted → returns `[]` (no error)." (§Error Semantics)
- RRULE-ERR-013 — "`before`/`after` finds no qualifying occurrence → returns `null` (no error)." (§Error Semantics)

(RRULE-ERR-002 withdrawn: the draft claimed a non-`Date` `until` raises at construction; reference execution showed it is accepted silently, so the claim was removed rather than specified.)

## Cross-View Invariants (RRULE-CVI)

- RRULE-CVI-001 — invariant 1 (string round trip reproduces the occurrence sequence). (§Cross-View Invariants)
- RRULE-CVI-002 — invariant 2 (toString reflects origOptions; options fills all keys; views agree on caller-supplied values). (§Cross-View Invariants)
- RRULE-CVI-003 — invariant 3 (windowed queries are elements of all(); count() equals all().length). (§Cross-View Invariants)
- RRULE-CVI-004 — invariant 4 (set merged sequence = union minus exclusions, deduped ascending; shared-start sets round-trip through rrulestr). (§Cross-View Invariants)
- RRULE-CVI-005 — invariant 5 (fully text-convertible rules survive toText/fromText). (§Cross-View Invariants)
- RRULE-CVI-006 — invariant 6 (every emitted occurrence satisfies all by-constraints and does not precede dtstart). (§Cross-View Invariants)
- RRULE-CVI-007 — invariant 7 (clone preserves every projection). (§Cross-View Invariants)
