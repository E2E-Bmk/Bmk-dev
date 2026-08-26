# rrule Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`rrule` is a calendar recurrence engine for JavaScript and TypeScript. It models a recurrence definition — a frequency, an interval, optional count or end bounds, and a family of "by" constraints such as by-weekday, by-month-day, by-week-number, and by-set-position — and expands that definition into the concrete sequence of `Date` occurrences it denotes. The rule grammar and the expansion arithmetic follow the iCalendar `RRULE` model: a rule is built programmatically from an options object, parsed from an `RRULE`/`DTSTART` string, or derived from an English phrase, and every representation projects back out as occurrence lists, RFC-style strings, and natural-language text.

Beyond single rules, the package provides recurrence sets that combine multiple inclusion rules, explicit extra dates, exclusion rules, and explicit excluded dates into one merged, deduplicated, chronologically sorted occurrence stream with its own multi-line string form.

The installable package name is `rrule`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require timezone-aware expansion. The `tzid` option is reserved: it appears as a key in normalized options with a `null` default, and no behavior beyond that is defined here. All date arithmetic operates on the UTC fields of JavaScript `Date` values as described in Dates And The UTC Convention.
- This specification does not define daylight-saving adjustment of any kind.
- This specification does not require the `byeaster` extension beyond its presence as a normalized-options key defaulting to `null`.
- This specification does not define natural-language output in any language other than English, nor customization hooks for alternative locales or formatters.
- This specification does not define result caching behavior. Whether enumeration results are cached is unobservable through the public API and left to the implementation.
- This specification does not require a command-line interface.

## Representative Workflows

A rule is defined once and then projected several ways: enumeration, RFC string, and English text.

```ts
import { RRule, datetime } from 'rrule'

const rule = new RRule({
  freq: RRule.WEEKLY,
  dtstart: datetime(2031, 3, 4, 9, 0, 0), // 2031-03-04 09:00 UTC, a Tuesday
  count: 5,
  byweekday: [RRule.TU, RRule.FR],
})

rule.all()
// [2031-03-04T09:00, 2031-03-07T09:00, 2031-03-11T09:00,
//  2031-03-14T09:00, 2031-03-18T09:00]  (all UTC)

rule.toString()
// "DTSTART:20310304T090000Z\nRRULE:FREQ=WEEKLY;COUNT=5;BYDAY=TU,FR"

rule.toText()
// "every week on Tuesday, Friday for 5 times"
```

Recurrence strings parse back into equivalent rules, and sets layer exceptions over rules; the set is queried through the same enumeration methods.

```ts
import { RRule, RRuleSet, rrulestr, datetime } from 'rrule'

const set = new RRuleSet()
set.rrule(new RRule({
  freq: RRule.WEEKLY,
  dtstart: datetime(2031, 6, 2, 10, 0, 0),
  count: 4,
  byweekday: [RRule.MO],
}))
set.rdate(datetime(2031, 6, 20, 15, 0, 0))   // one extra occurrence
set.exdate(datetime(2031, 6, 9, 10, 0, 0))   // drop one generated occurrence

set.all()
// [2031-06-02T10:00, 2031-06-16T10:00, 2031-06-20T15:00, 2031-06-23T10:00]

const clone = rrulestr(set.toString())        // multi-line string -> RRuleSet
clone.between(datetime(2031, 6, 15), datetime(2031, 6, 21))
// [2031-06-16T10:00, 2031-06-20T15:00]
```

## Dates And The UTC Convention

The engine performs pure calendar arithmetic and needs a fixed, timezone-free interpretation of every `Date` it consumes and produces. All recurrence arithmetic must read and write the UTC fields of `Date` values: a rule input given as a `Date` is interpreted by its `getUTCFullYear`/`getUTCMonth`/`getUTCDate`/`getUTCHours`/`getUTCMinutes`/`getUTCSeconds` components, and every occurrence the engine returns must carry its calendar values in those same UTC fields.

**The datetime helper.** The `datetime` function builds dates in this convention: it accepts a year, a 1-based month, a day, and optional hour, minute, and second (each defaulting to 0), and returns a `Date` whose UTC fields equal exactly those values. `datetime(2031, 3, 8, 9, 30, 0)` denotes 2031-03-08 09:30:00 UTC.

**Sub-second precision.** Recurrence arithmetic has second granularity. When a rule's start date is taken from the current clock because none was provided, the engine must truncate it to whole seconds (milliseconds set to zero). Occurrences generated from an explicit `dtstart` must reproduce its time-of-day fields.

## Defining A Recurrence

A recurrence is defined by constructing an `RRule` with a plain options object; the constructor validates, fills defaults, and normalizes the options into a canonical form while preserving the caller's original input separately.

**Frequency.** The `freq` option selects the recurrence frequency. The `Frequency` export is a numeric enumeration with members `YEARLY`, `MONTHLY`, `WEEKLY`, `DAILY`, `HOURLY`, `MINUTELY`, `SECONDLY` bound to the integer values 0 through 6 in that order, and reverse lookup from value to name. The same seven members are exposed as static properties of `RRule` (`RRule.YEARLY` … `RRule.SECONDLY`), and `RRule.FREQUENCIES` is the array of the seven frequency names in the same order. When `freq` is omitted, the rule must default to `YEARLY`.

**Core options.** The constructor accepts:

- `dtstart` — a `Date` giving the first instant from which recurrence is computed. When omitted or `null`, the engine must use the current time truncated to whole seconds. When provided, occurrences derive their time-of-day from it unless overridden by time-level by-rules.
- `interval` — a positive integer stride between frequency periods, defaulting to 1.
- `wkst` — the week-start day used by weekly expansion, given as a `Weekday`, or as an integer 0–6 in the recurrence weekday numbering; defaults to Monday.
- `count` — a positive integer limiting the total number of occurrences.
- `until` — a `Date` giving the last permitted occurrence instant. An occurrence exactly equal to `until` must be included.
- `bymonth`, `bymonthday`, `byyearday`, `byweekno`, `byhour`, `byminute`, `bysecond`, `bysetpos` — each a single integer or an array of integers constraining the corresponding calendar component.
- `byweekday` — a `Weekday`, an integer in the recurrence weekday numbering, a weekday token string such as `"TU"`, or an array mixing these forms.

**Weekday values.** The `Weekday` class represents a day of the week in the recurrence numbering, where Monday is 0 and Sunday is 6. The constants `RRule.MO`, `RRule.TU`, `RRule.WE`, `RRule.TH`, `RRule.FR`, `RRule.SA`, `RRule.SU` are `Weekday` instances, and the exported `ALL_WEEKDAYS` array holds the seven two-letter tokens `"MO"` through `"SU"` in Monday-first order. A `Weekday` exposes: `weekday`, its 0–6 number; `n`, an optional ordinal; `nth`, which returns a new `Weekday` with the given ordinal (so `RRule.FR.nth(2)` means the 2nd Friday and stringifies as `"+2FR"`); `equals`, true when both weekday number and ordinal match; `toString`, producing the token with a sign-prefixed ordinal when one is set; `getJsWeekday`, converting to JavaScript `Date.getDay` numbering where Sunday is 0 (so Monday maps to 1 and Sunday to 0); and the static `Weekday.fromStr`, converting a two-letter token back to a `Weekday`. Constructing a `Weekday` whose ordinal is 0, or calling `nth(0)`, must raise an `Error`; ordinals are nonzero.

**Original versus normalized options.** Every rule exposes two option views. `origOptions` must hold exactly the options the caller supplied — no defaults added, values as given. `options` must hold the fully normalized form, containing every recognized option key: `freq`, `dtstart`, `interval`, `wkst`, `count`, `until`, `tzid`, `bysetpos`, `bymonth`, `bymonthday`, `bynmonthday`, `byyearday`, `byweekno`, `byweekday`, `bynweekday`, `byhour`, `byminute`, `bysecond`, `byeaster`. Normalization must apply these rules:

- Scalar by-rule values are wrapped into arrays; unused list-valued by-rules become `null` (or an empty array where the split rules below apply); unset scalar options are `null`.
- `wkst` given as a `Weekday` or omitted normalizes to its integer weekday number (default 0, Monday).
- `byweekday` entries normalize to integer weekday numbers in `options.byweekday`, sorted by construction order, while ordinal-carrying entries (from `nth`) are split out into `options.bynweekday` as `[weekday, n]` pairs; when only ordinal entries are given, `options.byweekday` is `null`.
- `bymonthday` splits into `options.bymonthday` (positive values) and `options.bynmonthday` (negative values).
- When the frequency is coarser than the start date's precision and no explicit by-rule pins a component, the missing constraint derives from `dtstart`: a `YEARLY` rule with no `bymonth`/`bymonthday`/`byweekday`/`byyearday`/`byweekno` derives `bymonth` and `bymonthday` from the start date; a `MONTHLY` rule with no date-level by-rules derives `bymonthday`; a `WEEKLY` rule with no `bymonthday`/`byweekday` derives `byweekday` from the start date's weekday. Time components below the frequency granularity (`byhour`, `byminute`, `bysecond` for daily and coarser rules) likewise derive from `dtstart`.

**Cloning.** `clone` on a rule returns an independent `RRule` with the same original options and therefore the same projections.

## Occurrence Enumeration

Enumeration turns a rule (or set) into concrete occurrences; all five query methods share the same underlying sequence and inclusivity rules.

**Full expansion.** `all` returns every occurrence as an array of `Date` values in ascending order. When the rule is unbounded (neither `count` nor `until`), `all` accepts an iterator callback invoked as each occurrence is generated with the occurrence and its index; iteration must stop at the first occurrence for which the callback returns `false`, and that occurrence is excluded from the result. The callback form works on bounded rules as well.

**Windowed queries.** `between` accepts an `after` date, a `before` date, and an optional `inc` flag defaulting to `false`. It returns occurrences strictly between the two instants when `inc` is `false`, and includes occurrences falling exactly on either endpoint when `inc` is `true`. When `after` is not earlier than `before`, or no occurrences fall in the window, `between` returns an empty array. `before` returns the single latest occurrence at or before the argument (`inc` `true`) or strictly before it (`inc` `false`, the default), and `after` symmetrically returns the earliest occurrence at or after (or strictly after) the argument; both return `null` when no qualifying occurrence exists.

**Counting.** `count` (the method) returns the total number of occurrences, and must equal the length of the array `all` returns for the same finite rule or set.

**Argument validation.** The date arguments of `between`, `before`, and `after` must be valid `Date` values; if an argument is not a valid `Date`, then the method must raise an `Error`.

## Expansion Semantics

The heart of the engine is the arithmetic that expands a normalized rule into its occurrence sequence; the following rules must hold for every combination of options.

**Base sequence and interval.** Starting from `dtstart`, candidate periods advance by `interval` units of the frequency (`interval` 2 with `WEEKLY` means every second week). Within each period, by-rules select the matching instants; an occurrence earlier than `dtstart` is never emitted. Generation stops after `count` occurrences have been emitted, or once candidates pass `until` (occurrences equal to `until` are emitted), or at the engine's far horizon (year 9999) for unbounded rules.

**Constraint versus expansion.** A by-rule at a level coarser than or equal to the frequency filters candidates, while a by-rule at a finer level multiplies them. A `DAILY` rule with `byhour` set to two hours emits two occurrences per matching day; a `MONTHLY` rule with `bymonth` emits occurrences only in the listed months. Negative `bymonthday` values count backward from month end (-1 is the last day); negative `byyearday` values count backward from year end, honoring leap years. `byweekno` selects ISO 8601 week numbers (weeks governed by `wkst`), and negative week numbers count from the year's last week.

**Ordinal weekdays.** Inside a `MONTHLY` (or `bymonth`-constrained `YEARLY`) period, an ordinal weekday from `nth` selects the n-th matching weekday of the period from the start (positive n) or from the end (negative n, so `nth(-1)` is the last).

**Set positions.** After all other by-rules produce a period's candidate list, `bysetpos` selects elements by 1-based position from the start (positive) or end (negative) of that list. Values must lie in 1…366 or -366…-1; if a `bysetpos` value is 0 or out of range, then the constructor must raise an `Error`.

**Week start.** For `WEEKLY` rules with `interval` greater than 1, `wkst` determines the boundary at which a new week begins and therefore which occurrences share a week-period. Changing `wkst` between Monday and Sunday must change the emitted sequence of a biweekly multi-weekday rule accordingly.

**Frequencies below daily.** `HOURLY`, `MINUTELY`, and `SECONDLY` rules advance by hours, minutes, and seconds respectively, applying `interval` at that granularity and carrying finer components from `dtstart`.

## RFC String Projection

Rules and strings convert in both directions using the iCalendar property grammar; the string form is the persistence format.

**Serialization.** `toString` on a rule must emit a `DTSTART:` line when the caller provided `dtstart`, followed by an `RRULE:` line listing only properties the caller provided, in the grammar `KEY=VALUE` joined by `;`. Dates serialize as UTC compact timestamps (`20310304T090000Z`). Frequencies serialize by name (`FREQ=WEEKLY`); weekday lists as two-letter tokens (`BYDAY=TU,FR`); ordinal weekdays with sign and ordinal (`BYDAY=+2FR`); `wkst` as `WKST=` with the token of its day even when supplied numerically. Defaults that were not supplied (for example `interval` 1 or `wkst` Monday) must not appear, but explicitly supplied values equal to defaults must appear. A rule constructed without `dtstart` emits no `DTSTART:` line. The static `RRule.optionsToString` performs the same serialization directly from an options object.

**Parsing.** `RRule.parseString` converts a string in the same grammar back to a partial options object containing exactly the properties present in the string (frequency names back to their numeric values, `BYDAY` tokens back to `Weekday` values, timestamps back to `Date`s). It accepts a bare property list (`FREQ=DAILY;COUNT=2`), an `RRULE:`-prefixed line, or `DTSTART` plus `RRULE` on separate lines. An `UNTIL` value in date-only form (`20310304`) denotes midnight UTC of that day. If the string contains an unknown property name, then `parseString` must raise an `Error`; if a `DTSTART` or `UNTIL` timestamp does not match the timestamp grammar, then parsing must raise an `Error`. `RRule.fromString` composes parsing and construction, returning a ready `RRule`; round-tripping `RRule.fromString(rule.toString())` must reproduce the same occurrence sequence.

**The rrulestr entry point.** The `rrulestr` function parses a full recurrence text spanning one or more lines. Input containing only a single rule parses to an `RRule`; input with `RDATE`, `EXDATE`, `EXRULE`, or multiple `RRULE` lines parses to an `RRuleSet`. Its options object supports: `dtstart`, a `Date` merged into parsed rules that lack their own `DTSTART`; and `forceset`, a boolean defaulting to `false` which when `true` always yields an `RRuleSet` even for a single plain rule. `RDATE` and `EXDATE` lines carry comma-separated UTC timestamps. When the input contains more than one `DTSTART` line, the first `DTSTART` applies to every rule parsed from the text.

## Natural Language Projection

Rules also project to and from a constrained English phrase language covering common recurrence shapes.

**To text.** `toText` renders the rule as a lowercase English phrase: frequency and interval ("every week", "every 3 days"), weekday lists ("on Tuesday, Friday"), ordinal weekdays ("on the 2nd Friday"), month days ("on the 12th"), week numbers ("in week 11"), a count bound ("for 5 times"), and an until bound ("until October 1, 2031"). `isFullyConvertibleToText` returns `true` when every option of the rule is expressible in the phrase language and `false` otherwise.

**From text.** `RRule.parseText` converts such a phrase to a partial options object (for example "every day for 3 times" yields daily frequency with a count of 3); when the phrase cannot be interpreted, `parseText` must return `null` rather than raising. `RRule.fromText` composes `parseText` with construction and returns an `RRule`. For a rule whose options all lie in the phrase language, `RRule.fromText(rule.toText())` must define the same recurrence properties as the original.

## Recurrence Sets

A recurrence set combines inclusion and exclusion sources into one occurrence stream and supports the same queries as a single rule.

**Building a set.** `RRuleSet` is constructed with no arguments. `rrule` adds an inclusion `RRule`; `exrule` adds an exclusion `RRule`; `rdate` adds one explicit occurrence `Date`; `exdate` adds one explicit exclusion `Date`. If a non-`RRule` value is passed to `rrule`/`exrule` or a non-`Date` value is passed to `rdate`/`exdate`, then the method must raise an `Error`. The accessors `rrules`, `exrules`, `rdates`, and `exdates` return arrays reflecting what was added.

**Merged enumeration.** `all` on a set must return the union of all inclusion-rule occurrences and explicit `rdate`s, minus every instant produced by an exclusion rule or listed as an `exdate`, deduplicated (an instant contributed twice appears once) and sorted ascending. `between`, `before`, `after`, and `count` operate on this merged sequence with the same inclusivity semantics as on a single rule. Exclusion applies by instant equality: an `exdate` equal to a generated occurrence removes it.

**Set serialization.** `valueOf` on a set returns an array of iCalendar lines: each inclusion rule contributes its `DTSTART:` (when present) and `RRULE:` lines, each exclusion rule an `EXRULE:` line, and explicit dates contribute consolidated `RDATE:` and `EXDATE:` lines of comma-separated UTC timestamps. `toString` must equal those lines joined with newlines. Because parsing applies the first `DTSTART` to every rule, `rrulestr(set.toString())` must reproduce a set with the same merged occurrence sequence whenever the set's inclusion rules share a single start date. `clone` returns an independent set with the same sources.

## State Model

The engine's single fact source is the normalized recurrence definition — for a rule, the canonical option set; for a set, the collection of inclusion/exclusion rules and dates. Every public surface is a projection of that definition:

1. **Enumeration view** — `all`, `between`, `before`, `after`, `count` expose the occurrence sequence.
2. **Options view** — `origOptions` exposes caller intent; `options` exposes the normalized definition.
3. **RFC string view** — `toString`/`optionsToString` serialize caller intent; `parseString`/`fromString`/`rrulestr` rebuild definitions from strings.
4. **Text view** — `toText`/`parseText`/`fromText` map the definition to and from English phrases.
5. **Set view** — `RRuleSet` composes definitions and projects the merged sequence through the same enumeration and string views.

A rule is immutable once constructed: no public method mutates the definition, and repeated queries must return consistent results.

## Error Semantics

| Condition | Outcome |
|---|---|
| Constructor option `dtstart` is an invalid `Date` (for example `new Date(NaN)`) | `Error` raised at construction |
| `Weekday` constructed with ordinal 0, or `nth(0)` called | `Error` raised |
| `parseString`/`fromString`/`rrulestr` input contains an unknown property name | `Error` raised |
| `DTSTART`/`UNTIL`/`RDATE`/`EXDATE` timestamp fails the timestamp grammar | `Error` raised |
| `freq` outside the 0–6 enumeration | `Error` raised at construction |
| `bysetpos` value 0 or outside ±1…±366 | `Error` raised at construction |
| Non-`Date` argument to `between`, `before`, or `after` | `Error` raised |
| Non-`RRule` passed to `RRuleSet.rrule`/`exrule` | `Error` raised |
| Non-`Date` passed to `RRuleSet.rdate`/`exdate` | `Error` raised |
| `parseText` given an uninterpretable phrase | returns `null` (no error) |
| `between` window empty or inverted | returns `[]` (no error) |
| `before`/`after` finds no qualifying occurrence | returns `null` (no error) |

Error message wording is not part of this contract; the raised type is `Error`.

## Cross-View Invariants

1. For every rule with a provided `dtstart`, `RRule.fromString(rule.toString())` must enumerate exactly the same occurrence sequence as the original rule.
2. `toString` must reflect only caller-supplied options (`origOptions`), while `options` must contain every recognized key with defaults and derived values filled; the two views must never disagree on a caller-supplied value.
3. Every date returned by `between`, `before`, or `after` must be an element of the sequence `all` returns, and `count()` must equal the length of `all()` for every finite rule and set.
4. An `RRuleSet`'s merged sequence must equal the union of its inclusion sources minus its exclusion sources, deduplicated and ascending — and for a set whose inclusion rules share a single start date, `rrulestr(set.toString())` must rebuild a set whose merged sequence is identical.
5. For a rule fully expressible in the phrase language (`isFullyConvertibleToText` returns `true`), `RRule.fromText(rule.toText())` must produce a rule defining the same recurrence properties, and for count/interval/weekday shapes the same occurrence sequence given the same `dtstart`.
6. Every occurrence emitted by any enumeration method must satisfy all of the rule's by-constraints and must not precede `dtstart`.
7. `clone` (on rules and sets) must produce an object whose every projection — enumeration, string, text — equals the original's.

## Public Interface

### Import Surface

```ts
import {
  RRule,
  RRuleSet,
  rrulestr,
  Weekday,
  Frequency,
  ALL_WEEKDAYS,
  datetime,
} from 'rrule'
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `RRule` | class | A single recurrence rule: construction from options, enumeration, string and text projections |
| `RRule.YEARLY` … `RRule.SECONDLY` | constant | Frequency values 0–6 mirrored from `Frequency` |
| `RRule.MO` … `RRule.SU` | constant | `Weekday` instances for the seven weekdays |
| `RRule.FREQUENCIES` | constant | Array of the seven frequency names in value order |
| `RRule.fromString` | static function | Parse a `DTSTART`/`RRULE` string into an `RRule` |
| `RRule.parseString` | static function | Parse a `DTSTART`/`RRULE` string into a partial options object |
| `RRule.optionsToString` | static function | Serialize an options object to the string grammar |
| `RRule.fromText` | static function | Parse an English phrase into an `RRule` |
| `RRule.parseText` | static function | Parse an English phrase into a partial options object or `null` |
| `RRule#all` | method | All occurrences, optional iterator callback |
| `RRule#between` | method | Occurrences within a window, optional inclusivity |
| `RRule#before` | method | Latest occurrence before (or at) an instant |
| `RRule#after` | method | Earliest occurrence after (or at) an instant |
| `RRule#count` | method | Total number of occurrences |
| `RRule#toString` | method | RFC-style string of caller-supplied options |
| `RRule#toText` | method | English phrase rendering |
| `RRule#isFullyConvertibleToText` | method | Whether the phrase rendering is lossless |
| `RRule#clone` | method | Independent copy with identical projections |
| `RRule#options` | property | Normalized options (all keys, defaults filled) |
| `RRule#origOptions` | property | Caller-supplied options, unmodified |
| `RRuleSet` | class | Combines rules, dates, exclusion rules, and excluded dates into one stream |
| `RRuleSet#rrule` / `#exrule` | method | Add an inclusion / exclusion rule |
| `RRuleSet#rdate` / `#exdate` | method | Add an explicit / excluded date |
| `RRuleSet#rrules` / `#exrules` / `#rdates` / `#exdates` | method | Accessors for the added sources |
| `RRuleSet#valueOf` | method | Array of iCalendar lines for the set |
| `rrulestr` | function | Parse single- or multi-line recurrence text into `RRule` or `RRuleSet` |
| `Weekday` | class | Weekday with optional ordinal; `nth`, `equals`, `toString`, `getJsWeekday`, static `fromStr` |
| `Frequency` | enum | Numeric frequency enumeration `YEARLY`=0 … `SECONDLY`=6 |
| `ALL_WEEKDAYS` | constant | `["MO","TU","WE","TH","FR","SA","SU"]` |
| `datetime` | function | Build a `Date` from UTC calendar components (1-based month) |

### CLI Entry Points

There is no console script for this package. Programmatic use is through the package's named exports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. Tests execute with `vitest` under TypeScript (`typescript`, `@types/node` available). No third-party runtime dependencies are required or available to the implementation at runtime; the package must function self-contained.

The project must be an installable npm package named `rrule` whose root entry point provides the named exports listed in Public Interface, resolvable by Node.js under both ESM `import` and TypeScript `NodeNext` resolution. The assessment environment provides the same runtime and module resolution.

## Appendix B: Assessment Notes

Assessment exercises the public API only, in three dimensions: (1) atomic behavior — constructor normalization, single by-rule expansion, enumeration methods, string and text conversion primitives, weekday arithmetic, and declared error semantics; (2) integration — combinations that span projections, such as parse → enumerate → serialize round-trips, multi-by-rule expansion (ordinal weekdays, set positions, week starts), and recurrence sets layering rules with exceptions; (3) end-to-end workflows — building, persisting, restoring, and querying rules and sets across all views. Expected values are concrete occurrence lists and strings computed from the definitions in this document. Dates in fixtures use the UTC convention throughout. Each test is assessed independently.
