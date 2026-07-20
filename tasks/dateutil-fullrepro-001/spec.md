# python-dateutil Compatibility Specification

## Product Overview

Provide a pure-Python `dateutil` package for calendar calculations and parsing
human-oriented and ISO-8601 date/time strings. The package must expose the
module layout and public callables described below and must work from the
solution directory without relying on another installed copy of
`python-dateutil`.

## Installable Surface

The following imports must succeed:

```python
import dateutil
from dateutil import easter, parser, relativedelta, rrule, tz, utils, zoneinfo
from dateutil.easter import EASTER_JULIAN, EASTER_ORTHODOX, EASTER_WESTERN
from dateutil.easter import easter
from dateutil.parser import ParserError, isoparse, isoparser, parse, parserinfo
from dateutil.tz import UTC, tzoffset
```

`dateutil.__version__` is a string. The named submodules are importable both
directly and through `from dateutil import ...`.

## Easter Dates

`easter(year, method=EASTER_WESTERN)` returns a `datetime.date`:

- `EASTER_WESTERN` uses the Western Gregorian calculation.
- `EASTER_ORTHODOX` returns the Orthodox date in the Gregorian calendar.
- `EASTER_JULIAN` returns the Julian-calendar month and day without converting
  it to the Gregorian calendar.
- A method outside the three constants raises `ValueError`.

Representative results include Western Easter on 1990-04-15, 2000-04-23,
2018-04-01, and 2025-04-20; Orthodox Easter on 1991-04-07, 2000-04-30,
2018-04-08, and 2024-05-05; and Julian Easter on 326-04-03, 725-04-08,
1242-04-20, and 1555-04-14.

## ISO-8601 Parsing

`isoparse(value)` accepts ASCII `str` and `bytes` values. It returns a
`datetime.datetime` and supports:

- calendar years (`YYYY`), year-month values (`YYYY-MM`), basic calendar dates
  (`YYYYMMDD`), and extended calendar dates (`YYYY-MM-DD`);
- hour, hour-minute, and hour-minute-second time portions in basic or extended
  form;
- a period or comma before fractional seconds;
- `Z`, signed hour offsets, and signed hour-minute offsets, with or without a
  colon;
- midnight represented as either `00` on the target date or `24` on the
  preceding date;
- any single ASCII separator between a complete date and time when using the
  default `isoparse` helper;
- truncation of fractional-second digits beyond six places, rather than
  rounding.

Missing month, day, minute, second, and microsecond fields default to their
earliest valid values. A zero offset is represented by a timezone equivalent
to UTC. Non-zero offsets must report the correct `utcoffset()`.

`isoparser(sep=None)` provides the same parsing through its `isoparse` method.
When `sep` is supplied, it must be one ASCII non-numeric character and only
that separator is accepted between date and time.

Malformed or inconsistent ISO forms raise `ValueError`. Examples include a
three-digit year, mixed basic and extended separators, incomplete timezone
offsets, offsets with invalid hours or minutes, and non-ASCII input.

## General Date Parsing

`parse(text, default=None, dayfirst=False, yearfirst=False, ignoretz=False,
**kwargs)` recognizes common date and date/time forms, including:

- weekday and month-name forms such as `Thu Sep 25 10:36:28 2003`;
- ISO-like basic and extended forms;
- numeric dates separated by `-`, `.`, `/`, or spaces;
- month names, AM/PM markers, ordinal suffixes, and fractional seconds;
- numeric timezone offsets in `-HHMM` and `-HH:MM` forms.

Unspecified fields are copied from `default`; when no default is supplied,
the current date supplies missing calendar fields. Explicit fields always
replace fields from `default`.

For ambiguous three-number dates, `dayfirst=True` interprets the first number
as the day, while `yearfirst=True` interprets the first number as the year.
`ignoretz=True` discards recognized timezone names and offsets and returns a
naive datetime. Without `ignoretz`, a numeric offset produces an aware
datetime with the stated UTC displacement.

An empty string and input with no recognizable date/time data raise
`ParserError`, which is a `ValueError` subclass.

## Behavioral Invariants

- Parsing the same input with the same options is deterministic.
- Basic and extended spellings of the same ISO value produce equal datetimes.
- Equivalent offset spellings such as `-0300` and `-03:00` report the same UTC
  displacement.
- Values returned by the general parser and ISO parser use standard-library
  `date`, `datetime`, `time`, `timedelta`, and `tzinfo` protocols.
- Public parser failures use the documented public exception hierarchy rather
  than leaking internal parser exceptions.

## Non-Goals

Repository tooling, documentation builders, private modules, internal token
classes, exact cache organization, and network retrieval of timezone data are
outside this compatibility surface.
