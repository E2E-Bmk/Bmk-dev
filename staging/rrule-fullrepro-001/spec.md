<!-- INTERNAL
task_id: rrule-fullrepro-001
spec_version: v1
delta: initial version; contract details fixed by three probe rounds against
the pinned reference: UNTIL must be UTC whenever DTSTART carries a zone
(same-named-zone UNTIL is rejected); BYMONTHDAY zeros are pruned before
validation and never error; negative BYMONTHDAY steers iteration but is
absent from the getter and from Display; parse-path range violations are
parse errors while builder-path violations are validation errors; the
limit-hit flag is set whenever the cap is reached, including exactly;
merged streams preserve duplicates; an exclusion date removes every
occurrence at that instant; gap-hit occurrences shift forward one hour;
ambiguous fall-back times resolve to the earlier offset
source_boundary: docs.rs/rrule 0.14.0 (crate root property table, RRule,
RRuleSet, Frequency, NWeekday, Tz item docs), README, RFC 5545 §3.3.10 and
§3.8.5 recurrence semantics; reference behavior observed by running the
pinned checkout (probe binary, three rounds); floating (zone-free) datetime
literals and the host-local timezone are excluded from scope because they
resolve against the machine environment
-->

# rrule Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`rrule` is a calendar recurrence engine that implements the iCalendar
(RFC 5545) recurrence model for Rust programs. One recurrence description —
a start instant plus a bundle of rule properties such as frequency,
interval, count, terminal instant, and BY-part lists — is exposed through
four coordinated surfaces: a parser for RFC-style property strings, a typed
builder with a two-phase validation state, a canonical serializer, and a
timezone-aware occurrence iterator. A rule set combines any number of
recurrence rules with explicit extra dates and exclusion dates and yields
one merged, chronologically ordered stream of occurrences.

The library answers questions like "every second Tuesday and last Sunday of
the month at 09:00, New York time — what are the next twenty instants?"
while handling daylight-saving transitions, per-frequency defaulting of
missing BY-parts, and RFC-conformant validation of property combinations.
The installable package name is `rrule`.

## Non-Goals

- This specification does not require any serialization framework
  integration; rule and set values are exchanged as strings and as typed
  values only.
- This specification does not require a command-line tool; the crate is a
  library.
- This specification does not require evaluating exclusion rules: an
  `EXRULE` line in input must be accepted, but it is not recorded and has
  no effect on the occurrence stream, and no method for adding exclusion
  rules programmatically is defined.
- This specification does not define the interpretation of date or
  datetime literals that carry neither a `Z` suffix nor a `TZID`
  parameter, and it does not define any behavior tied to the host
  machine's local timezone.
- This specification does not define an Easter-offset extension or any
  other non-RFC recurrence property.
- This specification does not define exact error message text; error
  conditions are classified by error type only.
- This specification does not define safety caps for the unbounded
  iterator interface; bounded collection is provided by the capped
  collection method.

## Representative Workflows

**Parsing, inspecting, and listing occurrences.** A calendar string with a
`DTSTART` line and an `RRULE` line parses directly into a rule set. The
rules inside the parsed set are already validated, so their normalized
properties are observable through getters, and the set can be asked for a
bounded number of occurrences.

```rust
use rrule::RRuleSet;

let set: RRuleSet = "DTSTART;TZID=America/New_York:20260401T093000\n\
                     RRULE:FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1;COUNT=6"
    .parse()
    .unwrap();

// The parsed rule reports normalized properties.
let rule = &set.get_rrule()[0];
assert_eq!(rule.get_by_hour(), &[9]);
assert_eq!(rule.get_by_minute(), &[30]);

// Collect at most 100 occurrences: the last business day of each month.
let result = set.all(100);
assert_eq!(result.dates.len(), 6);
assert!(!result.limited);
```

**Building programmatically and composing a set.** A rule is assembled with
setter methods on an unvalidated value, validated against a start instant,
and combined with extra and excluded dates into a set.

```rust
use chrono::TimeZone;
use rrule::{Frequency, RRule, RRuleSet, Tz};

let start = Tz::UTC.with_ymd_and_hms(2026, 2, 1, 8, 0, 0).unwrap();
let rule = RRule::new(Frequency::Daily)
    .count(3)
    .validate(start)
    .unwrap();

let set = RRuleSet::new(start)
    .rrule(rule)
    .rdate(Tz::UTC.with_ymd_and_hms(2026, 1, 15, 8, 0, 0).unwrap())
    .exdate(Tz::UTC.with_ymd_and_hms(2026, 2, 2, 8, 0, 0).unwrap());

let dates = set.all(10).dates;
// Merged chronologically: the extra date precedes the start; the
// excluded instant is removed from the rule's output.
assert_eq!(dates.len(), 3);
```

## Recurrence Vocabulary and Rule Construction

This section defines the typed vocabulary of the recurrence model and the
builder that assembles a rule before validation; every other surface
(parser, serializer, iterator) is a projection of the property bundle
defined here.

**Frequency.** The `Frequency` enum has exactly seven variants — `Yearly`,
`Monthly`, `Weekly`, `Daily`, `Hourly`, `Minutely`, `Secondly` — naming the
base unit a rule advances by. `Frequency` values display as the uppercase
RFC keyword (`YEARLY`, `MONTHLY`, `WEEKLY`, `DAILY`, `HOURLY`, `MINUTELY`,
`SECONDLY`). Parsing a frequency from a string must be case-insensitive
(`"weekly"`, `"Secondly"`, and `"DAILY"` all parse); an unrecognized
keyword must produce an error.

**Weekdays and ordinals.** `Weekday` is the chronology library's
seven-variant weekday enum, re-exported at the crate root. `NWeekday`
wraps a weekday for use in `BYDAY` lists and has two variants: `Every`
(the weekday alone) and `Nth` (an ordinal plus a weekday, counting from
the start of the period when positive and from the end when negative).
The constructor `NWeekday::new` accepts an optional 16-bit ordinal and a
`Weekday`: with no ordinal it returns the `Every` form, with an ordinal it
returns the `Nth` form. `NWeekday` values display as the two-letter RFC
code preceded by the ordinal for the `Nth` form (`MO`, `2TU`, `-1SU`), and
parse from the same notation.

**The rule builder.** `RRule` is parameterized by a validation stage; the
two stage markers `Unvalidated` and `Validated` are public types. A fresh
rule is created with `RRule::new` from a `Frequency` and starts with:
interval 1, week start Monday, no count, no until, and every BY list
empty. Consuming setter methods return the modified rule: `interval` (a
16-bit count of base units between periods), `count` (a 32-bit occurrence
budget), `until` (a terminal instant), `week_start` (a `Weekday`),
`by_set_pos` (32-bit signed positions), `by_month` (a slice of the
chronology library's `Month` values), `by_week_no` (8-bit signed ISO week
numbers), `by_year_day` (16-bit signed day-of-year numbers),
`by_month_day` (8-bit signed day-of-month numbers), `by_weekday`
(`NWeekday` values), `by_hour`, `by_minute`, and `by_second` (8-bit
unsigned values).

**Two-phase validation.** An unvalidated rule carries raw properties.
Calling `validate` with a start instant normalizes the properties against
that instant (see Normalization and Derived Properties), checks them (see
Validation Rules), and returns a validated rule, or an error when a check
fails. `build` with a start instant is a convenience that validates the
rule and wraps it in a single-rule set with that start; it returns the set
or the validation error. Only validated rules can enter a set.

**Property getters.** Both stages expose read access: `get_freq`,
`get_interval`, `get_count` (optional), `get_until` (optional reference),
`get_week_start`, `get_by_set_pos`, `get_by_month` (month numbers 1–12),
`get_by_month_day`, `get_by_year_day`, `get_by_week_no`, `get_by_weekday`,
`get_by_hour`, `get_by_minute`, `get_by_second` (each a slice view of the
stored list). On a validated rule the getters report the normalized
properties, including values filled from the start instant.

**String form of a single rule.** An unvalidated rule parses from a
property string of semicolon-separated `NAME=VALUE` pairs — the string
form of the RRULE property value. A leading `RRULE:` prefix must be
accepted and stripped. Property names and keyword values are
case-insensitive. An unrecognized property name must produce a parse
error.

## Parsing Calendar Strings

A rule set parses from a multi-line calendar fragment; this is the primary
entry point for RFC-formatted input, and every rule that comes out of it
is already validated against the fragment's start instant.

**Line grammar.** Lines are separated by newlines. The fragment must
contain a `DTSTART` line; its absence is a parse error. `RRULE:`-prefixed
lines each contribute one recurrence rule, and a line consisting of bare
`NAME=VALUE;...` properties without a line-name prefix must be treated as
an `RRULE` line. `RDATE` lines contribute extra dates and `EXDATE` lines
contribute exclusion dates; both accept a comma-separated list of datetime
values after the colon, and multiple such lines accumulate. An `EXRULE`
line must be accepted and ignored: the parsed set records no exclusion
rules and the occurrence stream is unaffected. A fragment with several
`RRULE` lines produces a set holding the rules in input order.

**Datetime literals.** A datetime value of the form `YYYYMMDDTHHMMSSZ`
denotes an instant in UTC. A line parameter `TZID=<zone name>` qualifies
the line's datetime value with an IANA zone (for example
`DTSTART;TZID=America/New_York:20260401T093000`), and the resulting
occurrences carry that zone. A malformed datetime or an unrecognized zone
name is a parse error.

**Parse-time range checking.** Numeric BY-part values are range-checked
during parsing, and a violation is a parse error (not a validation error):
`BYMONTH` values must lie in 1–12, `BYWEEKNO` in −53..53, `BYYEARDAY` in
−366..366, `BYMONTHDAY` in −31..31, `BYHOUR` in 0–23, `BYMINUTE` and
`BYSECOND` in 0–59. After the line parses, each rule is validated against
the fragment's start instant exactly as builder-constructed rules are, so
combination violations (for example `BYWEEKNO` under a non-yearly
frequency) surface as validation errors.

**Merging into an existing set.** `set_from_string` on an existing set
parses a fragment and merges its content: a `DTSTART` line, when present,
replaces the set's start; parsed rules, extra dates, and exclusion dates
are appended to the set's existing collections. The method returns the
updated set or the parse/validation error.

## Normalization and Derived Properties

Validation begins by normalizing the raw property bundle against the start
instant; the normalized form is what getters report, what the serializer
prints, and what the iterator executes, so this step is observable on
every surface.

**Zero pruning.** A `BYMONTHDAY` value of zero is discarded during
normalization. It never reaches validation, so a rule whose only
`BYMONTHDAY` entry is zero behaves exactly as if the list had been empty
(including triggering the date-level fill below).

**Negative month days.** Negative `BYMONTHDAY` values (counting from the
end of the month, −1 = last day) steer iteration but are moved out of the
positive-day list: after validation, `get_by_month_day` reports only the
non-negative values, and the serialized form omits a `BYMONTHDAY` part
whose values were all negative. Iteration must still honor them.

**Date-level fill.** When, after zero pruning, the rule has no date-level
selector — no `BYWEEKNO`, `BYYEARDAY`, `BYMONTHDAY`, and `BYDAY` entries —
the frequency determines a fill from the start instant: a `Yearly` rule
receives `BYMONTH` set to the start's month (only when `BYMONTH` was
empty) and `BYMONTHDAY` set to the start's day; a `Monthly` rule receives
`BYMONTHDAY` set to the start's day; a `Weekly` rule receives `BYDAY` set
to the start's weekday in `Every` form. Other frequencies receive no
date-level fill. When any date-level selector is present, no date-level
fill occurs (a yearly rule with only `BYDAY` set does not receive the
month/day fill).

**Time-level fill.** Independently of the date-level fill, empty
time-of-day lists are filled from the start instant for frequencies
coarser than the list's unit: `BYHOUR` receives the start's hour for
`Yearly`, `Monthly`, `Weekly`, and `Daily` rules; `BYMINUTE` receives the
start's minute for those plus `Hourly`; `BYSECOND` receives the start's
second for those plus `Minutely`. A `Secondly` rule receives no fill. A
non-empty list is never overwritten.

**Ordering.** Every BY list on a validated rule is sorted ascending with
duplicates removed; getters and the serialized form both reflect this
order regardless of the order in which values were supplied.

## Validation Rules

Validation checks the normalized bundle and rejects combinations the model
cannot execute; each rule below names the condition that must fail.

**Terminal instant.** If an `until` instant is present and the start
instant carries any zone described by this specification (UTC or a named
IANA zone), then `until` must be expressed in UTC: a validation error is
produced when `until` carries any other zone, including the start's own
named zone. If `until` is earlier than the start instant, validation must
fail.

**Range checks.** The builder path re-checks the numeric ranges listed
under parse-time range checking, producing validation errors: hours 0–23;
minutes and seconds 0–59; month numbers 1–12; `BYMONTHDAY` within
−31..31; `BYYEARDAY` within −366..366 and not zero; `BYWEEKNO` within
−53..53 and not zero; `BYSETPOS` not zero and within a frequency-dependent
range (±366 for yearly and daily, ±31 for monthly, ±53 for weekly, ±24
for hourly, ±60 for minutely and secondly).

**Frequency compatibility.** If `BYMONTHDAY` is non-empty (after zero
pruning) under a `Weekly` frequency, validation must fail. If `BYYEARDAY`
is non-empty under a `Daily`, `Weekly`, or `Monthly` frequency, validation
must fail. If `BYWEEKNO` is non-empty under any frequency other than
`Yearly`, validation must fail. An `Nth`-form `BYDAY` entry is accepted
under every frequency.

**Companion rule.** If `BYSETPOS` is non-empty while every other BY list
is empty after normalization, validation must fail. Because the time-level
fill populates `BYHOUR`, `BYMINUTE`, or `BYSECOND` for every frequency
except `Secondly`, this failure is reachable only for `Secondly` rules
without explicit BY parts.

## Serialization

A rule and a set each render back to RFC property text; the rendered form
of a validated value is canonical, and re-parsing it reproduces the same
normalized properties.

**Rule rendering.** A rule displays as semicolon-joined `NAME=VALUE`
parts without any `RRULE:` prefix. Parts appear in this fixed order, each
included only when applicable: `FREQ` always; `UNTIL` when present,
rendered as `YYYYMMDDTHHMMSS` followed by `Z` for a zone-carrying instant;
`COUNT` when present; `INTERVAL` only when different from 1; `WKST` only
when different from Monday, as the two-letter code; then non-empty lists
as comma-joined values in stored order: `BYSETPOS`, `BYMONTH`,
`BYMONTHDAY`, `BYWEEKNO`, `BYHOUR`, `BYMINUTE`, `BYSECOND`, `BYYEARDAY`,
`BYDAY`. An unvalidated rule renders the properties exactly as set
(including negative `BYMONTHDAY` values and unsorted lists); a validated
rule renders the normalized bundle, so filled `BYHOUR`/`BYMINUTE`/
`BYSECOND` (and date-level fills) appear even though the input never
named them, an explicitly supplied `INTERVAL=1` or `WKST=MO` disappears,
and all-negative `BYMONTHDAY` lists are omitted.

**Set rendering.** A set displays as a multi-line fragment: a `DTSTART`
line first, rendering a UTC start as `DTSTART:YYYYMMDDTHHMMSSZ` and a
named-zone start as `DTSTART;TZID=<zone>:YYYYMMDDTHHMMSS`; one
`RRULE:`-prefixed line per rule in the set's rule order, each using the
validated rule rendering; then, when extra dates exist, a single line
`RDATE;VALUE=DATE-TIME:` followed by the comma-joined datetime values;
then, when exclusion dates exist, a single `EXDATE;VALUE=DATE-TIME:` line
of the same shape. A UTC datetime value in these lines renders as its
wall-clock digits followed by `Z`. A set with no rules, extra dates, or
exclusion dates renders as the `DTSTART` line alone.

## Occurrence Iteration

The occurrence stream is the executable projection of a set: all sources
are merged chronologically, exclusions are applied by instant, and
collection is bounded by an explicit cap.

**Bounded collection.** `all` accepts a 16-bit occurrence cap and returns
an `RRuleResult` with two public fields: `dates`, the collected
occurrences in chronological order, and `limited`, a flag that must be
`true` exactly when collection stopped because the cap was reached —
including the case where the cap equals the number of occurrences the set
would ever produce — and `false` when the stream ended on its own
(exhausted counts, terminal instants, and finite extra dates) before the
cap. `all_unchecked` collects the entire stream into a plain vector with
no cap and no flag; it must only terminate on finite sets.

**Windowing.** `after` and `before` set an inclusive collection window:
occurrences equal to the window edge instants are included. The window is
honored by `all` and `all_unchecked` only. Direct iteration (the set
implements `IntoIterator` yielding occurrences; its iterator type is
`RRuleSetIter`) ignores the window and the cap and yields the unbounded
merged stream from the beginning; bounding is the caller's responsibility
(for example with a take adapter).

**Stream composition.** Each rule generates occurrences starting at the
set's start instant: the start itself is emitted when and only when it
matches the rule's normalized pattern; otherwise generation begins at the
first matching instant after it. A rule's `count` budgets that rule's own
generated occurrences, and a rule's `until` cuts that rule's stream at
instants less than or equal to it (an occurrence exactly equal to `until`
is emitted). Extra dates join the merge as-is — an extra date earlier than
the start instant is emitted first. The merged stream is sorted by
instant, and duplicates are preserved: two rules producing the same
instant, an extra date duplicating a rule occurrence, or two equal extra
dates all yield repeated entries. Exclusion dates then remove every
occurrence whose instant equals an exclusion instant — all duplicates at
that instant are removed, from every source; instant equality is
timezone-independent (an exclusion expressed in another zone removes the
occurrence at the same absolute time). A rule's `count` is consumed by
generation before exclusions are applied, so excluding an occurrence
shortens the output rather than pulling in a replacement.

**BY-part combinatorics.** Within one period (one year, month, week, day,
hour, or minute, per the frequency and interval), the normalized BY lists
select occurrence instants: date-level selectors choose days, time-level
lists produce one instant per combination of listed hour, minute, and
second, in chronological order. `BYSETPOS` then keeps only the instants at
the listed positions within the period's candidate list (1-based from the
start, negative from the end). Day selectors that name days a month lacks
(day 31 in a 30-day month, February 29 in a non-leap year) simply
contribute nothing for that period; the period is skipped without error.
Negative selectors count from the end (`BYMONTHDAY=-1` is the last day of
the month; `BYYEARDAY=-1` is December 31; a `-1SU` `BYDAY` entry under a
monthly frequency is the month's last Sunday). `BYWEEKNO` uses ISO week
numbering adjusted to the rule's week start; the `WKST` property changes
which weeks the interval steps over for weekly rules with an interval
greater than 1.

**Empty and rule-free sets.** A set with no rules and no extra dates
produces an empty stream (`dates` empty, `limited` false). A set with only
extra dates yields exactly those instants, sorted. A rule whose `count` is
zero contributes nothing.

## Set Composition

A set is assembled around one start instant and holds independent
collections of rules, extra dates, and exclusion dates; every collection
is observable through a getter.

**Construction.** `RRuleSet::new` takes the start instant and returns an
empty set. Consuming builder methods append one element and return the
set: `rrule` (a validated rule), `rdate` (an extra instant), `exdate` (an
exclusion instant). Bulk setters replace the whole collection:
`set_rrules`, `set_rdates`, `set_exdates`. Rules keep insertion order;
extra and exclusion dates keep insertion order in storage (the merge
sorts occurrences, not the stored lists).

**Observation.** `get_dt_start` returns a reference to the start instant.
`get_rrule`, `get_rdate`, and `get_exdate` return references to the
stored collections. `get_exrule` returns the exclusion-rule collection,
which is always empty under this specification (the parser ignores
`EXRULE` lines and no method adds one).

**Start replacement.** The start instant is set at construction and
replaced only by a `DTSTART` line arriving through `set_from_string`.
Rules already in the set keep the normalization derived from the start
they were validated against.

## Timezone and Daylight-Saving Behavior

Occurrence instants are zone-aware, and rules generate wall-clock-stable
streams in the start instant's zone across daylight-saving transitions.

**The zone type.** `Tz` is the crate's timezone type, a wrapper over the
IANA zone database. `Tz::UTC` is the UTC constant, and every named zone is
available as an associated constant whose name replaces `/` with a double
underscore (`Tz::America__New_York`, `Tz::Europe__Paris`). A `Tz`
converts from the chronology library's zone type via `From`, reports its
IANA name through `name()`, and constructs zone-aware datetimes through
the standard chronology `TimeZone` interface. All datetimes the crate
accepts and returns are the chronology library's `DateTime` values
parameterized by this `Tz`.

**Zone of yielded occurrences.** Occurrences generated by a rule carry
the start instant's zone. Extra dates keep the zone they were supplied
in; the merge compares absolute instants and never converts a value into
another zone.

**Wall-clock stability.** For frequencies of a day or coarser, a rule in
a named zone holds the local wall-clock time constant across
daylight-saving transitions: a daily 09:00 rule yields 09:00 in the old
offset before the transition and 09:00 in the new offset after it.

**Nonexistent local times.** When a generated local time falls in a
spring-forward gap and does not exist, the occurrence shifts forward by
one hour (a 02:30 daily rule yields 03:30 on the gap day and returns to
02:30 afterwards). Under sub-daily frequencies this shift can land on the
instant of the following occurrence; both occurrences are emitted.

**Ambiguous local times.** When a generated local time falls in a
fall-back overlap and exists twice, the earlier instant (the
pre-transition offset) is chosen.

**Terminal comparisons.** `until` bounds and window edges compare by
absolute instant, so a UTC `until` cuts a named-zone stream at the
corresponding local time.

## State Model

The core state is one recurrence description: a start instant plus, per
rule, the normalized property bundle (frequency, interval, optional
count, optional until, week start, and the eleven BY lists), together
with the set's extra-date and exclusion-date collections. Public
projections of this state:

1. **Getters** report the bundle field-by-field (normalized, on validated
   rules).
2. **Serialization** renders the bundle as canonical RFC property text
   (defaults omitted, lists sorted, derived fills visible).
3. **Iteration** executes the bundle into a merged, exclusion-filtered,
   chronologically ordered occurrence stream.
4. **Parsing** constructs the same state from RFC text, running the same
   normalization and validation as the builder path.

A mutation is one of: builder setters (pre-validation), set append/replace
methods, or a fragment merge via `set_from_string`. No other operation
changes the state; `all`, `all_unchecked`, and display take the value and
leave equivalents observable through re-construction.

## Error Semantics

All fallible operations return `RRuleError`, an enum with exactly two
public variants wrapping the two error domains.

| Condition | Error |
|---|---|
| Calendar fragment without a `DTSTART` line | `RRuleError::ParserError` wrapping a `ParseError` |
| Unrecognized property name in an `RRULE` line | `ParserError` |
| Unrecognized frequency keyword | `ParserError` |
| Malformed datetime literal or unknown `TZID` zone name | `ParserError` |
| BY-part numeric value out of range in parsed text | `ParserError` |
| `until` not in UTC while the start carries a zone | `RRuleError::ValidationError` wrapping a `ValidationError` |
| `until` earlier than the start instant | `ValidationError` |
| BY-part numeric value out of range via builder setters | `ValidationError` |
| Zero in `BYYEARDAY`, `BYWEEKNO`, or `BYSETPOS` via builder setters | `ValidationError` |
| `BYMONTHDAY` under weekly frequency | `ValidationError` |
| `BYYEARDAY` under daily, weekly, or monthly frequency | `ValidationError` |
| `BYWEEKNO` under non-yearly frequency | `ValidationError` |
| `BYSETPOS` with every other BY list empty after normalization | `ValidationError` |

`ParseError` and `ValidationError` are public types; both they and
`RRuleError` implement the standard error and display traits, and
`RRuleError` values convert from both domain types. Single-rule parsing
(`RRule` from a string) reports `RRuleError` too. Error display text is
human-readable and not part of this contract.

## Cross-View Invariants

1. **Canonical round trip (serialization ↔ parsing ↔ iteration).**
   Rendering a parsed set and re-parsing the rendered text must yield a
   set with the same start instant, the same getter-visible rule
   properties, the same extra and exclusion dates, and an identical
   occurrence stream under the same cap.
2. **Builder–parser equivalence (construction ↔ parsing).** A rule built
   with setters and validated against start X must report the same
   getter values, render the same property text, and generate the same
   occurrence stream as the equivalent `NAME=VALUE` text parsed in a
   fragment whose `DTSTART` is X.
3. **Getter–serialization agreement (observation ↔ serialization).** For
   a validated rule, every list a getter reports non-empty must appear in
   the rendered text comma-joined in the same order, and `INTERVAL`/
   `WKST` must appear in the text exactly when the getter reports a
   non-default value.
4. **Fill visibility (normalization ↔ observation ↔ iteration).** The
   time-of-day (and frequency-dependent date-level) values filled from
   the start instant during validation must be identical in the getters,
   in the rendered text, and in the wall-clock components of every
   generated occurrence.
5. **Cap accounting (iteration ↔ composition).** For a set whose only
   rule carries count n and which has no extra or exclusion dates,
   `all(m)` must return min(n, m) occurrences with `limited` true exactly
   when m ≤ n; appending an exclusion matching one occurrence must
   shorten the output by the number of matching entries without changing
   the flag's dependence on the cap.
6. **Window consistency (iteration ↔ iteration).** The occurrences
   returned under an `after`/`before` window must equal the unwindowed
   stream filtered to instants within the inclusive window, in the same
   order.
7. **Instant-based exclusion (composition ↔ timezone handling).** An
   exclusion date expressed in any zone must remove exactly the merged
   occurrences whose absolute instant it equals, independent of the zone
   the occurrences carry.

## Public Interface

### Import Surface

```rust
use rrule::{
    Frequency, NWeekday, ParseError, RRule, RRuleError, RRuleResult,
    RRuleSet, RRuleSetIter, Tz, Unvalidated, Validated, ValidationError,
    Weekday,
};
```

`Weekday` is the chronology library's weekday enum re-exported at the
crate root. Datetime values are the chronology library's `DateTime`
parameterized by `Tz`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `RRule` | struct (stage-parameterized) | one recurrence rule; builder, getters, string form |
| `Unvalidated` / `Validated` | stage marker types | rule validation state |
| `Frequency` | enum | seven base recurrence units; RFC keyword display/parse |
| `NWeekday` | enum | `BYDAY` entry: plain or ordinal-qualified weekday |
| `Weekday` | enum (re-export) | day of week |
| `RRuleSet` | struct | start instant + rules + extra/exclusion dates; parse, render, iterate |
| `RRuleResult` | struct | capped collection output: `dates` and `limited` |
| `RRuleSetIter` | struct | unbounded merged occurrence iterator |
| `Tz` | enum | IANA timezone wrapper; `UTC` and named constants |
| `RRuleError` | enum | top-level error: parser or validation variant |
| `ParseError` | enum | text-domain failure |
| `ValidationError` | enum | property-domain failure |

### CLI Entry Points

There is no console script for this package. Programmatic use is through
the Rust crate API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `rrule` with its default configuration
  providing every behavior described here; the assessment suite depends
  on the crate as `rrule = { version = "*" }`.
- The `chrono` (0.4 line) and `chrono-tz` (0.10 line) crates are
  available and provide the datetime and zone-database vocabulary the
  public API exchanges; the recurrence model — parsing, normalization,
  validation, serialization, and iteration — is the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Vocabulary: frequency display/parse, ordinal weekday construction,
  display and parse notation, builder defaults.
- Parsing: fragment grammar (DTSTART forms, prefixed and bare rule lines,
  multi-value and repeated RDATE/EXDATE lines, inert EXRULE), single-rule
  strings, parse-time range rejection, error classification.
- Normalization: zero pruning, date-level and time-level fills, list
  ordering, negative month-day visibility rules.
- Validation: until-zone and until-ordering rules, builder-path range
  checks, frequency-compatibility rules, the companion rule.
- Serialization: canonical property order, default omission, validated
  vs. unvalidated rendering, set fragment shape, round-trip stability.
- Iteration: capped collection and the limit flag, inclusive windows,
  merged ordering with preserved duplicates, per-rule count/until,
  BY-part selection including negative ordinals and set positions,
  skipped impossible days, unbounded iteration.
- Timezone behavior: zone of yielded instants, wall-clock stability
  across transitions, gap and overlap resolution, instant-based
  exclusion and windowing.

Atomic tests target one surface at a time; integration tests combine at
least two surfaces (for example parse → getters → render → re-parse →
iterate) against a shared recurrence description.
