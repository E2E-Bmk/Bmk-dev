# Arrow Specification

## Product Overview

Arrow provides a compact Python API for constructing, parsing, formatting, and inspecting timezone-aware dates and times. An `Arrow` value represents one instant together with its timezone. Factory helpers accept the common date/time shapes used by the standard library and preserve a consistent view across calendar attributes, timestamps, formatting, equality, and conversion.

## Scope

This document covers:

- component-based `Arrow` construction;
- module, class, and `ArrowFactory` construction routes;
- timestamps, `datetime`, `date`, `struct_time`, ISO text, ISO calendar triples, and timezone inputs;
- public calendar, timezone, naive-datetime, representation, equality, hash, and clone behavior;
- token formatting, bracket escaping, and the built-in internet date formats;
- parse, type, calendar, and timezone failures.

Locale registries, humanized relative time, ranges, spans, shifting, release tools, and private package state are outside this scope.

## Installable Surface

The distribution is installed as `arrow` and supports these imports:

```python
import arrow
from arrow import Arrow, ArrowFactory, ParserError
from arrow.formatter import DateTimeFormatter
```

The top-level package exports `get`, `now`, `utcnow`, `Arrow`, `ArrowFactory`, `ParserError`, `FORMAT_ATOM`, `FORMAT_COOKIE`, `FORMAT_RFC822`, `FORMAT_RFC850`, `FORMAT_RFC1036`, `FORMAT_RFC1123`, `FORMAT_RFC2822`, `FORMAT_RFC3339`, `FORMAT_RFC3339_STRICT`, `FORMAT_RSS`, and `FORMAT_W3C`.

The same factory surface is available through `arrow.api.get`, `arrow.api.now`, `arrow.api.utcnow`, and `arrow.api.factory`. `arrow.api.factory(ArrowSubclass)` returns an `ArrowFactory` whose construction methods create that subclass.

## Product State Model

An Arrow value has four public projections:

- Instant projection: `datetime`, `timestamp()`, equality, and hash describe the represented instant.
- Calendar projection: year, month, day, hour, minute, second, microsecond, week, quarter, and `naive` expose calendar fields.
- Timezone projection: `tzinfo`, `utcoffset()`, and `fold` expose timezone and ambiguous-time state.
- Text projection: `str`, `repr`, the format protocol, `format`, and `DateTimeFormatter.format` render the same value.

All construction routes that receive equivalent inputs must agree across these projections. Formatting and cloning must not change the represented instant. Supplying a different timezone to a factory route changes the timezone projection according to that route's documented replacement or conversion rule while preserving the specified wall-clock fields.

## Construction And Factory Behavior

### Component Construction

`Arrow(year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, **kwargs)` requires year, month, and day. Missing time components are zero. An omitted timezone means UTC. `tzinfo` accepts a `datetime.tzinfo` object or a recognized timezone name. Values from `zoneinfo`, `dateutil`, and `pytz` must represent the same wall-clock fields and offset for the requested zone.

Invalid component counts raise `TypeError`; impossible calendar or microsecond values raise `ValueError`. The optional `fold` value follows PEP 495. For an ambiguous wall time, fold `0` and fold `1` compare as the same wall time but expose different UTC offsets.

### Class Methods

`Arrow.now(tzinfo=None)` returns current local time when no timezone is supplied and current time in the supplied timezone otherwise. `Arrow.utcnow()` returns current UTC with fold `0`.

`Arrow.fromtimestamp(value, tzinfo=None)` accepts a numeric Unix timestamp and uses local time by default or the supplied timezone. `Arrow.utcfromtimestamp(value)` uses UTC. Non-numeric timestamp text raises `ValueError` on these class methods.

`Arrow.fromdatetime(value, tzinfo=None)` preserves an aware datetime's timezone when no override is given. A naive datetime defaults to UTC. An explicit timezone attaches that timezone to the supplied calendar fields. `Arrow.fromdate(value, tzinfo=None)` uses midnight and defaults to UTC. `Arrow.strptime(text, format, tzinfo=None)` uses standard `datetime.strptime` directives and defaults to UTC. `Arrow.fromordinal(value)` accepts a valid integer ordinal, returns midnight UTC for that date, raises `TypeError` for non-integers, and raises `ValueError` for out-of-range ordinals.

### General Factory

`arrow.get(*args, **kwargs)` and `ArrowFactory.get(*args, **kwargs)` share these rules:

- No arguments return current UTC.
- `None`, booleans, and unsupported objects raise `TypeError`.
- Integers, floats, and `Decimal` values are Unix timestamps. Values at second, millisecond, and microsecond scale are normalized to the represented instant.
- A numeric-looking string is parsed as date/time text and raises `ParserError` when it is not a supported date. Pair it with format token `X` to parse seconds explicitly.
- An existing `Arrow` returns an equivalent value.
- A `datetime` preserves its fields and existing timezone; a `date` uses midnight.
- A `time.struct_time` uses its calendar fields in UTC.
- A timezone object or timezone name by itself requests current time in that zone.
- A three-integer tuple is `(ISO year, ISO week, ISO weekday)` and follows `date.fromisocalendar`. Invalid tuple lengths raise `TypeError`; invalid ISO week/day values raise `ValueError`.
- An ISO date/time string is parsed without an explicit format.
- `normalize_whitespace=True` collapses repeated whitespace before parsing formatted or ISO-like text.

The `tzinfo` keyword sets the timezone for a `datetime`, `date`, existing `Arrow`, or ISO calendar input while retaining that input's wall-clock fields. A second positional timezone has the same behavior for `datetime` and `date`. A timezone name and the equivalent `tzinfo` object must produce the same result. Unknown timezone names raise `ParserError`; objects that are not valid timezone values raise `TypeError`.

## Arrow Value Views

`datetime` returns the aware standard-library datetime represented by the value. `naive` returns the same fields with no timezone. The datetime-style component properties expose year, month, day, hour, minute, second, and microsecond. `week` is the ISO week number, and `quarter` is 1 for January through March, 2 for April through June, 3 for July through September, and 4 for October through December.

`timestamp()` equals the standard datetime timestamp for `datetime`. `tzinfo`, `utcoffset()`, and `fold` reflect the value's timezone state. Accessing an unknown attribute raises `AttributeError`.

`str(value)` is `value.datetime.isoformat()`. `repr(value)` is `<Arrow [ISO_VALUE]>`. An Arrow value hashes like its equivalent aware datetime. `clone()` returns a distinct Arrow object with equal public state.

The format protocol delegates a non-empty format specifier to Arrow token formatting, so `f"{value:YYYY-MM-DD}"` renders a calendar date. An empty format specifier matches `str(value)`. Calling `value.format()` with no pattern uses `YYYY-MM-DD HH:mm:ssZZ`.

## Token Formatting

`DateTimeFormatter(locale="en-us").format(datetime_value, pattern)` and `Arrow.format(pattern, locale="en-us")` apply the same token rules. English output includes:

- `YYYY` and `YY`: four- and two-digit year;
- `MMMM`, `MMM`, `MM`, and `M`: full month name, abbreviated month, padded month, and numeric month;
- `DDDD`, `DDD`, `DD`, `D`, and `Do`: padded ordinal day, ordinal day, padded day, day, and ordinal day text;
- `dddd`, `ddd`, and `d`: full weekday name, abbreviated weekday, and ISO weekday number;
- `HH` and `H`: padded and plain 24-hour time;
- `hh` and `h`: padded and plain 12-hour time, with midnight rendered as 12;
- `mm`/`m` and `ss`/`s`: padded/plain minute and second;
- one through six `S` characters: the corresponding leading microsecond digits, retaining zero padding;
- `X`: Unix seconds as text; `x`: integer Unix microseconds;
- `ZZ` and `Z`: timezone offset with and without a colon;
- `ZZZ`: timezone abbreviation;
- `a` and `A`: lower- and upper-case meridiem;
- `W`: `YYYY-Www-d` ISO week date.

Recognized tokens are replaced wherever they occur, including inside otherwise literal text. For example, formatting 11:00 on 2012-01-01 with `NONSENSE` returns `NON0EN0E` because both `S` characters are fractional-second tokens. Text inside square brackets is literal: `MMMM D, YYYY [at] h:mma` renders `December 10, 2015 at 5:09pm` for 2015-12-10 17:09.

For 1975-12-25 14:15:16 in `America/New_York`, the built-in constants render as follows:

| Constant | Result |
|---|---|
| `FORMAT_ATOM` | `1975-12-25 14:15:16-05:00` |
| `FORMAT_COOKIE` | `Thursday, 25-Dec-1975 14:15:16 EST` |
| `FORMAT_RFC822` | `Thu, 25 Dec 75 14:15:16 -0500` |
| `FORMAT_RFC850` | `Thursday, 25-Dec-75 14:15:16 EST` |
| `FORMAT_RFC1036` | `Thu, 25 Dec 75 14:15:16 -0500` |
| `FORMAT_RFC1123` | `Thu, 25 Dec 1975 14:15:16 -0500` |
| `FORMAT_RFC2822` | `Thu, 25 Dec 1975 14:15:16 -0500` |
| `FORMAT_RFC3339` | `1975-12-25 14:15:16-05:00` |
| `FORMAT_RFC3339_STRICT` | `1975-12-25T14:15:16-05:00` |

## Error Semantics

- Parse failures from the general text factory raise `ParserError`.
- Invalid constructor components and ordinals follow standard `TypeError` and `ValueError` distinctions.
- Unsupported general-factory input shapes raise `TypeError`.
- Booleans are not numeric timestamp inputs and raise `TypeError`.
- Unknown timezone names raise `ParserError`; non-timezone objects raise `TypeError`.
- Error message wording is not part of this contract.

## Cross-View Invariants

- Module helpers, `ArrowFactory`, and `Arrow` class methods must agree for equivalent inputs.
- `datetime`, component attributes, `naive`, `timestamp()`, and formatted output must describe the same value.
- Equivalent timezone names and timezone objects must produce matching calendar fields and offsets.
- Formatting options must change only text and must not mutate the Arrow value.
- `clone()` must retain equality, hash, calendar, timezone, and timestamp behavior.
- Equivalent Arrow values must compare and hash consistently without depending on object identity.
- ISO text and ISO calendar construction must agree with standard-library date/time rules.

## Representative Workflow

```python
import arrow

created = arrow.get("2024-01-07T09:30:00+00:00")
assert created.datetime.year == 2024
assert created.timestamp() == created.datetime.timestamp()
assert created.format("YYYY-MM-DD [at] HH:mm ZZ") == "2024-01-07 at 09:30 +00:00"

same_day = arrow.get((2024, 1, 7), tzinfo="UTC")
assert same_day.date() == created.date()
```

## Non-Goals

Private attributes, private helper functions, source layout, caches, repository configuration, release tooling, and exact error-message wording are not public requirements. Network access is not required.

## Invocation Protocol

Arrow is a Python library. No console command and no `python -m arrow` entry point are required.

## Environment

Runtime dependencies must be declared in `requirements.txt` or `pyproject.toml` at the project root. The implementation may use packages available from PyPI.
