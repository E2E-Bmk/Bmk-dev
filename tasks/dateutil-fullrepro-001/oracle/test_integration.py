from datetime import datetime, timedelta

import pytest

from dateutil.parser import ParserError, parse


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Thu Sep 25 10:36:28 2003", datetime(2003, 9, 25, 10, 36, 28)),
        ("Thu Sep 25 2003", datetime(2003, 9, 25)),
        ("2003-09-25T10:49:41", datetime(2003, 9, 25, 10, 49, 41)),
        ("20030925T104941", datetime(2003, 9, 25, 10, 49, 41)),
        ("2003-09-25 10:49:41,502", datetime(2003, 9, 25, 10, 49, 41, 502000)),
        ("25-09-2003", datetime(2003, 9, 25)),
        ("2003.09.25", datetime(2003, 9, 25)),
        ("2003/09/25", datetime(2003, 9, 25)),
        ("July 4, 1976 12:01:02 am", datetime(1976, 7, 4, 0, 1, 2)),
        ("3rd of May 2001", datetime(2001, 5, 3)),
        ("Jan 1 1999 11:23:34.578", datetime(1999, 1, 1, 11, 23, 34, 578000)),
        ("13NOV2017", datetime(2017, 11, 13)),
    ],
    ids=["date-command", "month-name", "iso", "basic-iso", "logger", "day-first-unambiguous", "dots", "slashes", "ampm", "ordinal", "fraction", "compact-month"],
)
def test_general_parser_formats(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Thu Sep 25 10:36:28", datetime(2003, 9, 25, 10, 36, 28)),
        ("Thu Sep 10:36:28", datetime(2003, 9, 25, 10, 36, 28)),
        ("Thu 10:36:28", datetime(2003, 9, 25, 10, 36, 28)),
    ],
    ids=["missing-year", "missing-day-year", "time-only"],
)
def test_parse_default_fills_missing_components(value, expected):
    default = datetime(2003, 9, 25)
    assert parse(value, default=default) == expected


@pytest.mark.parametrize("separator", ["-", ".", "/"], ids=["dash", "dot", "slash"])
def test_parse_dayfirst(separator):
    value = separator.join(("10", "09", "2003"))
    assert parse(value, dayfirst=True) == datetime(2003, 9, 10)


@pytest.mark.parametrize("separator", ["-", ".", "/"], ids=["dash", "dot", "slash"])
def test_parse_yearfirst(separator):
    value = separator.join(("10", "09", "03"))
    assert parse(value, yearfirst=True) == datetime(2010, 9, 3)


@pytest.mark.parametrize(
    "value",
    [
        "Thu Sep 25 10:36:28 BRST 2003",
        "1996.07.10 AD at 15:08:56 PDT",
        "Tuesday, April 12, 1952 AD 3:30:42pm PST",
    ],
    ids=["brst", "pdt", "pst"],
)
def test_parse_ignoretz_returns_naive(value):
    parsed = parse(value, ignoretz=True)
    assert parsed.tzinfo is None


@pytest.mark.parametrize(
    ("value", "expected", "offset"),
    [
        ("20030925T104941-0300", datetime(2003, 9, 25, 10, 49, 41), -timedelta(hours=3)),
        ("Thu, 25 Sep 2003 10:49:41 -0300", datetime(2003, 9, 25, 10, 49, 41), -timedelta(hours=3)),
        ("2003-09-25T10:49:41.5-03:00", datetime(2003, 9, 25, 10, 49, 41, 500000), -timedelta(hours=3)),
    ],
    ids=["basic", "rfc-like", "colon"],
)
def test_parse_numeric_timezone_offsets(value, expected, offset):
    parsed = parse(value)
    assert parsed.replace(tzinfo=None) == expected
    assert parsed.utcoffset() == offset


@pytest.mark.parametrize("value", ["", "not a date at all"], ids=["empty", "unrecognized"])
def test_parse_invalid_input_raises_parser_error(value):
    with pytest.raises(ParserError):
        parse(value)


def test_parser_error_is_value_error():
    assert issubclass(ParserError, ValueError)
