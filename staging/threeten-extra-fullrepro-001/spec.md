# threeten-extra Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`threeten-extra` is a date-and-time extension library layered over `java.time`. It supplies the value types the core platform leaves out: half-open time intervals and date ranges with a full relational algebra, single-unit temporal amounts, combined period-with-duration amounts, year-week and year-quarter partial dates, alternative calendar systems (Coptic, Julian, International Fixed) that interoperate with ISO dates through the `java.time.chrono` framework, and a mutable `Clock` for controlling time in tests.

Every type is an immutable value object except `MutableClock`, whose mutability is its purpose. All types integrate with the platform's temporal interfaces: amounts implement `TemporalAmount` and plug into `plus`/`minus` on ISO dates; partial dates implement `Temporal`; chronology dates implement `ChronoLocalDate` and convert to and from `LocalDate` via the standard `from` idiom.

## Non-Goals

- This specification does not define the Symmetry454, Symmetry010, Pax, Accounting, Discordian, Ethiopic, or British Cutover calendar systems.
- This specification does not define the UTC/TAI time-scale types or leap-second handling.
- This specification does not define packed date fields, day-of-month/day-of-year standalone types, half-of-year or hour-minute types, or the `AmountFormats` word-based formatter.
- This specification does not define `OffsetDate` or the `Temporals` utility methods.
- This specification does not require localized text output beyond the fixed `toString` forms stated here.
- This specification does not define serialization formats beyond the documented parse/`toString` round trips.

## Representative Workflows

The first workflow computes interval relations between two meetings and merges them when they touch.

```java
import org.threeten.extra.Interval;
import java.time.Instant;

Interval morning = Interval.of(Instant.parse("2020-01-01T09:00:00Z"),
                               Instant.parse("2020-01-01T12:00:00Z"));
Interval midday  = Interval.of(Instant.parse("2020-01-01T12:00:00Z"),
                               Instant.parse("2020-01-01T14:00:00Z"));

morning.abuts(midday);      // true  — they touch without overlapping
morning.overlaps(midday);   // false — a shared boundary instant is not overlap
Interval merged = morning.union(midday);
merged.toString();          // "2020-01-01T09:00:00Z/2020-01-01T14:00:00Z"
```

The second workflow converts an ISO date into an alternative calendar, applies calendar-aware arithmetic, and converts back.

```java
import org.threeten.extra.chrono.CopticDate;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

CopticDate coptic = CopticDate.from(LocalDate.of(2020, 9, 11));
coptic.toString();                       // "Coptic AM 1737-01-01" — Coptic New Year
CopticDate later = coptic.plus(1, ChronoUnit.MONTHS);
LocalDate back = LocalDate.from(later);  // ISO date one Coptic month later
```

The third workflow drives time-dependent code with a mutable clock.

```java
import org.threeten.extra.MutableClock;
import java.time.Duration;
import java.time.Instant;

MutableClock clock = MutableClock.epochUTC();
clock.setInstant(Instant.parse("2020-06-01T12:00:00Z"));
clock.add(Duration.ofHours(3));
clock.instant();                         // 2020-06-01T15:00:00Z
```

## Time Intervals

An `Interval` is an immutable half-open span between two `Instant`s: the start is inclusive, the end is exclusive. This section defines construction, queries, and the relational algebra every other view builds on.

**Construction and text form.** `Interval.of(Instant startInclusive, Instant endExclusive)` creates an interval; if the end is before the start it must raise `DateTimeException`. `Interval.of(Instant startInclusive, Duration duration)` derives the end by addition. `Interval.parse(CharSequence text)` reads the ISO form `start/end` produced by `toString()` (for example `2020-01-01T00:00:00Z/2020-01-02T00:00:00Z`); unparseable text must raise `DateTimeParseException`. The constant `Interval.ALL` is the interval over all of time: `isUnboundedStart()` and `isUnboundedEnd()` both return true on it.

**Accessors.** `getStart()` and `getEnd()` return the boundary instants. `isEmpty()` returns true exactly when start equals end. `toDuration()` returns `Duration.between(start, end)`.

**Instant queries.** `contains(Instant instant)` returns true when the instant is at or after the start and strictly before the end; the start of a non-empty interval is contained, the end is not, and an empty interval contains nothing — not even its own boundary instant. `isBefore(Instant instant)` and `isAfter(Instant instant)` compare the whole interval to the instant.

**Relational algebra.** For intervals `a` and `b`:

- `a.encloses(b)` returns true when every instant of `b` lies within `a`; every interval encloses itself.
- `a.abuts(b)` returns true when the intervals touch at exactly one boundary instant without overlapping; an interval never abuts itself.
- `a.overlaps(b)` returns true when the intervals share at least one instant; two intervals meeting only at a boundary do not overlap.
- `a.isConnected(b)` returns true when the intervals abut or overlap — that is, when their union is a single interval.
- `a.union(b)` returns the smallest interval containing both; if the intervals are not connected it must raise `DateTimeException`.
- `a.intersection(b)` returns the largest interval contained in both; if the intervals are not connected it must raise `DateTimeException`.
- `a.span(b)` returns the smallest interval containing both regardless of connection, filling any gap.

Two intervals are equal when both boundaries are equal, and `parse` of a `toString` result reproduces the interval.

## Date Ranges

A `LocalDateRange` is the date-based counterpart of `Interval`: an immutable half-open range of `LocalDate`s with the same algebra plus date-specific projections.

**Construction and text form.** `LocalDateRange.of(LocalDate startInclusive, LocalDate endExclusive)` creates a range and must raise `DateTimeException` when the end is before the start. `LocalDateRange.ofClosed(LocalDate startInclusive, LocalDate endInclusive)` treats the second argument as the last included date, so the resulting exclusive end is one day later. `LocalDateRange.parse(CharSequence text)` reads the `start/end` form produced by `toString()` (for example `2020-01-01/2020-02-01`); bad text must raise `DateTimeParseException`.

**Accessors and projections.** `getStart()` and `getEnd()` return the boundaries; `getEndInclusive()` returns the last included date (one day before the exclusive end). `isEmpty()` is true when start equals end. `lengthInDays()` returns the number of included dates as an int. `toPeriod()` returns the range's length as a `Period`. `stream()` yields every included date in order — for the range `2020-01-01/2020-01-05` the stream is exactly the four dates January 1 through January 4.

**Queries and algebra.** `contains(LocalDate date)` includes the start and excludes the end. `encloses`, `abuts`, `overlaps`, `isConnected`, `union`, `intersection`, and `span` follow exactly the interval semantics above, with `union` and `intersection` raising `DateTimeException` on disconnected ranges.

## Single-Unit Amounts

`Days`, `Weeks`, `Months`, and `Years` each wrap a single int amount of one temporal unit and implement `TemporalAmount`. Their shared surface is uniform; this section states it once and notes the per-type differences.

**Construction and constants.** Each type has a static `of(int amount)` factory and constants `ZERO` and `ONE`. `getAmount()` returns the wrapped int.

**Text form and parsing.** `toString()` renders the ISO period style: `Days.of(3)` is `"P3D"`, `Weeks.of(2)` is `"P2W"`, `Months.of(5)` is `"P5M"`, `Years.of(7)` is `"P7Y"`. Each static `parse(CharSequence text)` accepts its own form, and `Days.parse` additionally accepts a weeks form, converting at 7 days per week — `Days.parse("P2W")` equals `Days.of(14)`. Unparseable text must raise `DateTimeParseException`.

**Between.** Each type has a static `between(Temporal startInclusive, Temporal endExclusive)` measuring the amount of its unit from start to end: `Days.between(2020-01-01, 2020-02-01)` is 31 days; `Weeks.between` counts complete weeks; `Months.between` and `Years.between` count complete months and years.

**Arithmetic.** `plus(...)` and `minus(...)` accept either an int or another amount of the same type; `multipliedBy(int scalar)`, `dividedBy(int divisor)` (integer division; dividing by zero must raise `ArithmeticException`), `negated()`, and `abs()` complete the arithmetic. `isNegative()`, `isZero()`, and `isPositive()` classify the sign. `compareTo` orders by amount.

**Temporal integration.** `addTo(Temporal temporal)` and `subtractFrom(Temporal temporal)` implement `TemporalAmount`, so `date.plus(Days.of(3))` and `Days.of(3).addTo(date)` produce the same date. `get(TemporalUnit unit)` returns the amount for the type's own unit, and `getUnits()` is a one-element list of that unit. `toPeriod()` converts to a `Period` — `Weeks.of(2).toPeriod()` is `P14D`, `Months.of(2).toPeriod()` is `P2M`, `Years.of(2).toPeriod()` is `P2Y`.

## Combined Period and Duration

A `PeriodDuration` combines a date-based `Period` with a time-based `Duration` in one `TemporalAmount`.

**Construction and text form.** `PeriodDuration.of(Period period, Duration duration)`, `of(Period period)`, and `of(Duration duration)` construct instances; the constant `ZERO` has both parts zero and renders as `"PT0S"`. `toString()` concatenates the parts in ISO style — the combination of `Period.of(1, 2, 3)` and four hours renders `"P1Y2M3DT4H"` — and `parse(CharSequence text)` reads that form back, raising `DateTimeParseException` on bad text.

**Accessors and arithmetic.** `getPeriod()` and `getDuration()` return the parts. `plus(TemporalAmount amount)` and `minus(TemporalAmount amount)` combine part-wise. `normalizedStandardDays()` moves whole 24-hour blocks from the duration into the period's days: thirty hours normalizes to `"P1DT6H"`. `PeriodDuration.between(Temporal startInclusive, Temporal endExclusive)` measures the calendar difference in the period part and the remaining time in the duration part.

## Year-Based Partials

`YearWeek` and `YearQuarter` are immutable partial dates addressing one ISO week or one quarter of a specific year; `Quarter` is the enum of the four quarters.

**YearWeek.** `YearWeek.of(int weekBasedYear, int week)` addresses a week of the ISO week-based year. `toString()` renders `2020-W53` and `parse` reads that form. Week 53 is valid only in a 53-week year, reported by `is53WeekYear()`; 2020 has 53 weeks, 2019 does not. When week 53 is requested in a 52-week year, `of` must resolve to week 1 of the following week-based year rather than raising — `YearWeek.of(2019, 53)` is `2020-W01`. A week outside 1–53 must raise `DateTimeException`. `atDay(DayOfWeek dayOfWeek)` returns the `LocalDate` of that day in the week; `YearWeek.from(TemporalAccessor temporal)` derives the year-week of a date. `withYear(int weekBasedYear)` and `withWeek(int week)` replace one component; `plusWeeks(long weeksToAdd)` and `minusWeeks(long weeksToSubtract)` step sequentially, rolling across year boundaries (`2020-W53` plus one week is `2021-W01`). `lengthOfYear()` returns 364 or 371 days. `compareTo` orders chronologically.

**YearQuarter and Quarter.** `Quarter.of(int quarterOfYear)` maps 1–4 to `Q1`–`Q4` and must raise `DateTimeException` outside that range; `Quarter.from(TemporalAccessor temporal)` derives the quarter of a date. `YearQuarter.of(int year, Quarter quarter)` and `of(int year, int quarterOfYear)` address one quarter; `toString()` renders `2020-Q1` and `parse` reads it back. `atDay(int dayOfQuarter)` returns the date of the given day within the quarter and must raise `DateTimeException` when the day exceeds `lengthOfQuarter()`; `isValidDay(int dayOfQuarter)` reports the same test as a boolean. `atEndOfQuarter()` returns the last date of the quarter. `lengthOfQuarter()` reflects the leap status of the year — quarter 1 has 91 days in 2020 and 90 in 2019 — and `isLeapYear()` reports it. `plusQuarters(long quartersToAdd)`, `minusQuarters(long quartersToSubtract)`, `withQuarter(int quarterOfYear)`, and `withYear(int year)` navigate; `YearQuarter.from(TemporalAccessor temporal)` derives the quarter of a date.

## Alternative Chronologies

Three calendar systems implement the `java.time.chrono` framework: Coptic, Julian, and International Fixed. Each has a singleton chronology (`INSTANCE`), a date class implementing `ChronoLocalDate`, and an era enum. Dates convert losslessly to and from `LocalDate`: `LocalDate.from(chronoDate)` and `ChronoDate.from(localDate)` invert each other, and both directions agree with epoch-day equality.

**Coptic.** `CopticChronology.INSTANCE` has calendar id `"Coptic"`. A Coptic year has 13 months: months 1–12 have 30 days; month 13 has 5 days in a normal year and 6 in a leap year. A proleptic year is a leap year exactly when `year % 4 == 3`, reported by `isLeapYear(long prolepticYear)`; the year length is 365 or 366 accordingly. `CopticDate.of(int prolepticYear, int month, int dayOfMonth)` validates its components and must raise `DateTimeException` for an invalid combination (such as day 6 of month 13 in a non-leap year). The single era in use is `CopticEra.AM`, and `prolepticYear(Era era, int yearOfEra)` maps era-year to proleptic year. Coptic New Year 1737-01-01 corresponds to ISO 2020-09-11, and ISO 2020-01-01 corresponds to Coptic 1736-04-22. `dateEpochDay(long epochDay)`, `date(int prolepticYear, int month, int dayOfMonth)`, and `date(TemporalAccessor temporal)` construct dates through the chronology. Date arithmetic (`plus`, `minus` with `ChronoUnit`) and `until` operate in Coptic calendar units, with `until` returning a chronology-aware `ChronoPeriod`.

**Julian.** `JulianChronology.INSTANCE` has calendar id `"Julian"`. The Julian leap rule is every fourth year without century exception, so proleptic year 1900 is a Julian leap year and `JulianDate.of(1900, 2, 29)` is valid; February has 29 days in a Julian leap year and 28 otherwise, and an invalid date must raise `DateTimeException`. In the twentieth and twenty-first centuries the Julian calendar runs 13 days behind ISO: Julian 2020-02-29 corresponds to ISO 2020-03-13. The eras are `JulianEra.BC` and `JulianEra.AD`, and `eras()` lists both. Adding a year to a Julian leap day lands on February 28 of the following year.

**International Fixed.** `InternationalFixedChronology.INSTANCE` has calendar id `"Ifc"`. A year has 13 months of 28 days each plus one or two special days carried inside months: day 29 of month 13 is the year day present in every year, and day 29 of month 6 is the leap day present only in leap years. The leap rule is the ISO (Gregorian) rule — 2020 is a leap year, 1900 is not — so the year length is 365 or 366. `InternationalFixedDate.of(int prolepticYear, int month, int dayOfMonth)` must raise `DateTimeException` for the leap day in a non-leap year. Month lengths report 28, or 29 for month 13 and for month 6 in a leap year. The date renders as `Ifc CE 2020/01/01`. January 1 aligns in both calendars: Ifc 2020/01/01 is ISO 2020-01-01; the year day 2020/13/29 is ISO 2020-12-31; the leap day 2020/06/29 is ISO 2020-06-17. Month arithmetic from a special day lands on the last ordinary day of the target month (the year day plus one month is day 28 of month 1 of the following year).

## Mutable Clock

`MutableClock` extends `java.time.Clock` with in-place control of the current instant, for driving time-dependent code deterministically.

**Construction.** `MutableClock.of(Instant instant, ZoneId zone)` sets the initial instant and zone; `MutableClock.epochUTC()` starts at the epoch instant in UTC.

**Reading and mutating.** `instant()` returns the current instant and `getZone()` the zone. `setInstant(Instant instant)` replaces the instant. `add(TemporalAmount amount)` advances the clock by a duration or period. `set(TemporalAdjuster adjuster)` adjusts the current zoned time — setting a `LocalDate` moves the clock to the start of that day in the clock's zone. `toString()` renders `MutableClock[instant,zone]`.

**Shared state across views.** `withZone(ZoneId zone)` returns a view with a different zone over the same underlying instant state: mutations through either the original or the view are visible through both.

## State Model

Every type in this library except `MutableClock` is an immutable value object: operations return new instances and never modify the receiver. Equality is by value; `parse` and `toString` are inverse projections of the same value; arithmetic and navigation methods are pure functions.

- Intervals and ranges expose one half-open span through boundary accessors, containment and relational queries, algebraic combinations, streams (ranges), and text.
- Amounts expose one integer quantity through `getAmount`, arithmetic, temporal addition, `Period` conversion, and text.
- Partials and chronology dates expose one calendar position through component accessors, navigation, `LocalDate` conversion, and text.
- `MutableClock` holds the only mutable state: a current instant shared by every zone view derived from the same clock.

## Error Semantics

| Condition | Required result |
|---|---|
| Interval or range constructed with end before start | Must raise `DateTimeException`. |
| `union` or `intersection` on disconnected intervals or ranges | Must raise `DateTimeException`. |
| Unparseable text for any `parse` in this library | Must raise `DateTimeParseException`. |
| `dividedBy(0)` on an amount type | Must raise `ArithmeticException`. |
| `Quarter.of` outside 1–4, or `YearWeek.of` week outside 1–53 | Must raise `DateTimeException`. |
| `atDay` beyond the quarter length | Must raise `DateTimeException`. |
| Invalid chronology date (Coptic month-13 overflow, Julian February 29 in a non-leap year, International Fixed leap day in a non-leap year) | Must raise `DateTimeException`. |

Week 53 of a 52-week year is not an error: `YearWeek.of` must resolve it to week 1 of the following year.

## Cross-View Invariants

1. For every value type with a text form (`Interval`, `LocalDateRange`, `Days`, `Weeks`, `Months`, `Years`, `PeriodDuration`, `YearWeek`, `YearQuarter`), `parse(x.toString())` must equal `x`.
2. Two intervals or ranges are connected exactly when they abut or overlap, and `union` equals `span` whenever it is defined.
3. A non-empty interval or range must contain its start and must not contain its end; an empty one contains nothing.
4. For every date in a range's `stream()`, `contains` returns true, the stream's count equals `lengthInDays()`, and `Days.between(getStart(), getEnd())` carries the same number.
5. For each chronology, `LocalDate.from(ChronoDate.from(isoDate))` must return `isoDate`, and the chronology's `dateEpochDay(isoDate.toEpochDay())` must equal `ChronoDate.from(isoDate)`.
6. `date.plus(amount)` must equal `amount.addTo(date)` for every amount type, and `between(a, b).addTo(a)` must return `b` when measured in the amount's own unit.
7. `YearWeek.from(yw.atDay(d))` must return `yw` for every day of the week, and `YearQuarter.from(yq.atDay(n))` must return `yq` for every valid day of the quarter.
8. A `MutableClock` and every view obtained from `withZone` must observe the same instant after any mutation through either object.

## Public Interface

### Import Surface

```java
import org.threeten.extra.Days;
import org.threeten.extra.Interval;
import org.threeten.extra.LocalDateRange;
import org.threeten.extra.Months;
import org.threeten.extra.MutableClock;
import org.threeten.extra.PeriodDuration;
import org.threeten.extra.Quarter;
import org.threeten.extra.Weeks;
import org.threeten.extra.YearQuarter;
import org.threeten.extra.YearWeek;
import org.threeten.extra.Years;
import org.threeten.extra.chrono.CopticChronology;
import org.threeten.extra.chrono.CopticDate;
import org.threeten.extra.chrono.CopticEra;
import org.threeten.extra.chrono.InternationalFixedChronology;
import org.threeten.extra.chrono.InternationalFixedDate;
import org.threeten.extra.chrono.InternationalFixedEra;
import org.threeten.extra.chrono.JulianChronology;
import org.threeten.extra.chrono.JulianDate;
import org.threeten.extra.chrono.JulianEra;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `Interval` | static `of(Instant, Instant)`, `of(Instant, Duration)`, `parse(CharSequence)`, constant `ALL`; `getStart()`, `getEnd()`, `isEmpty()`, `isUnboundedStart()`, `isUnboundedEnd()`, `toDuration()`, `contains(Instant)`, `isBefore(Instant)`, `isAfter(Instant)`, `encloses(Interval)`, `abuts(Interval)`, `overlaps(Interval)`, `isConnected(Interval)`, `union(Interval)`, `intersection(Interval)`, `span(Interval)`, `equals`, `toString` |
| `LocalDateRange` | static `of(LocalDate, LocalDate)`, `ofClosed(LocalDate, LocalDate)`, `parse(CharSequence)`; `getStart()`, `getEnd()`, `getEndInclusive()`, `isEmpty()`, `lengthInDays()`, `toPeriod()`, `stream()`, `contains(LocalDate)`, `encloses`, `abuts`, `overlaps`, `isConnected`, `union`, `intersection`, `span`, `equals`, `toString` |
| `Days`, `Weeks`, `Months`, `Years` | static `of(int)`, `parse(CharSequence)`, `between(Temporal, Temporal)`, constants `ZERO`, `ONE`; `getAmount()`, `plus`, `minus`, `multipliedBy(int)`, `dividedBy(int)`, `negated()`, `abs()`, `isNegative()`, `isZero()`, `isPositive()`, `addTo(Temporal)`, `subtractFrom(Temporal)`, `get(TemporalUnit)`, `getUnits()`, `toPeriod()`, `compareTo`, `toString` |
| `PeriodDuration` | static `of(Period, Duration)`, `of(Period)`, `of(Duration)`, `parse(CharSequence)`, `between(Temporal, Temporal)`, constant `ZERO`; `getPeriod()`, `getDuration()`, `plus(TemporalAmount)`, `minus(TemporalAmount)`, `normalizedStandardDays()`, `equals`, `toString` |
| `YearWeek` | static `of(int, int)`, `parse(CharSequence)`, `from(TemporalAccessor)`; `is53WeekYear()`, `atDay(DayOfWeek)`, `withYear(int)`, `withWeek(int)`, `plusWeeks(long)`, `minusWeeks(long)`, `lengthOfYear()`, `compareTo`, `equals`, `toString` |
| `YearQuarter` | static `of(int, Quarter)`, `of(int, int)`, `parse(CharSequence)`, `from(TemporalAccessor)`; `atDay(int)`, `atEndOfQuarter()`, `isValidDay(int)`, `lengthOfQuarter()`, `isLeapYear()`, `plusQuarters(long)`, `minusQuarters(long)`, `withYear(int)`, `withQuarter(int)`, `compareTo`, `equals`, `toString` |
| `Quarter` | enum constants `Q1`–`Q4`; static `of(int)`, `from(TemporalAccessor)` |
| `MutableClock` | static `of(Instant, ZoneId)`, `epochUTC()`; `instant()`, `getZone()`, `withZone(ZoneId)`, `setInstant(Instant)`, `add(TemporalAmount)`, `set(TemporalAdjuster)`, `toString` |
| `CopticChronology`, `JulianChronology`, `InternationalFixedChronology` | singleton `INSTANCE`; `getId()`, `date(int, int, int)`, `date(TemporalAccessor)`, `dateEpochDay(long)`, `isLeapYear(long)`, `prolepticYear(Era, int)`, `eras()` |
| `CopticDate`, `JulianDate`, `InternationalFixedDate` | static `of(int, int, int)`, `from(TemporalAccessor)`; `lengthOfMonth()`, `lengthOfYear()`, `getEra()`, `plus(long, TemporalUnit)`, `minus(long, TemporalUnit)`, `until(ChronoLocalDate)`, `equals`, `toString` |
| `CopticEra`, `JulianEra`, `InternationalFixedEra` | era enum constants (`AM`; `BC`, `AD`; `CE`) |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Interval` | class | Half-open instant interval with relational algebra. |
| `LocalDateRange` | class | Half-open date range with algebra and date stream. |
| `Days` | class | Amount of days. |
| `Weeks` | class | Amount of weeks. |
| `Months` | class | Amount of months. |
| `Years` | class | Amount of years. |
| `PeriodDuration` | class | Combined period and duration amount. |
| `YearWeek` | class | ISO week-based year plus week partial. |
| `YearQuarter` | class | Year plus quarter partial. |
| `Quarter` | enum | The four quarters. |
| `MutableClock` | class | Clock with settable, shared instant state. |
| `CopticChronology` | class | Coptic calendar system. |
| `CopticDate` | class | Date in the Coptic calendar. |
| `CopticEra` | enum | Coptic era. |
| `JulianChronology` | class | Julian calendar system. |
| `JulianDate` | class | Date in the Julian calendar. |
| `JulianEra` | enum | Julian eras. |
| `InternationalFixedChronology` | class | International Fixed (13-month) calendar system. |
| `InternationalFixedDate` | class | Date in the International Fixed calendar. |
| `InternationalFixedEra` | enum | International Fixed era. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library, including the complete `java.time` framework, is available; the target artifact's own declared dependencies resolve through Maven. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.threeten:threeten-extra`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the public interval, range, amount, partial-date, chronology, and clock surfaces. Tests compare boundary and containment semantics, relational classifications (abuts versus overlaps versus encloses), algebraic results and their failure conditions, parse/`toString` round trips, calendar conversion round trips against fixed ISO correspondences, leap-rule classifications, arithmetic results in each calendar, and shared-state visibility of the mutable clock; they do not require internal field access, private constructors, or formatting beyond the documented text forms. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking that relational algebra, conversion, and arithmetic stay mutually consistent across views.
