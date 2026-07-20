from datetime import date, datetime, timedelta

import pytest

from dateutil import tz
from dateutil.easter import EASTER_JULIAN, EASTER_ORTHODOX, EASTER_WESTERN, easter
from dateutil.parser import isoparse, isoparser


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        (1990, date(1990, 4, 15)),
        (2000, date(2000, 4, 23)),
        (2018, date(2018, 4, 1)),
        (2025, date(2025, 4, 20)),
    ],
    ids=["1990", "2000", "2018", "2025"],
)
def test_western_easter_dates(year, expected):
    assert easter(year, EASTER_WESTERN) == expected


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        (1991, date(1991, 4, 7)),
        (2000, date(2000, 4, 30)),
        (2018, date(2018, 4, 8)),
        (2024, date(2024, 5, 5)),
    ],
    ids=["1991", "2000", "2018", "2024"],
)
def test_orthodox_easter_dates(year, expected):
    assert easter(year, EASTER_ORTHODOX) == expected


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        (326, date(326, 4, 3)),
        (725, date(725, 4, 8)),
        (1242, date(1242, 4, 20)),
        (1555, date(1555, 4, 14)),
    ],
    ids=["326", "725", "1242", "1555"],
)
def test_julian_easter_dates(year, expected):
    assert easter(year, EASTER_JULIAN) == expected


def test_easter_rejects_unknown_method():
    with pytest.raises(ValueError):
        easter(1975, 4)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1996", datetime(1996, 1, 1)),
        ("2017-04", datetime(2017, 4, 1)),
        ("20160229", datetime(2016, 2, 29)),
        ("2018-03-15", datetime(2018, 3, 15)),
        (b"20140204", datetime(2014, 2, 4)),
        (b"2014-02-04", datetime(2014, 2, 4)),
    ],
    ids=["year", "year-month", "basic-date", "extended-date", "bytes-basic", "bytes-extended"],
)
def test_isoparse_calendar_forms(value, expected):
    assert isoparse(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("19980416T12", datetime(1998, 4, 16, 12)),
        ("2012-01-06T09:37", datetime(2012, 1, 6, 9, 37)),
        ("20030902T221402", datetime(2003, 9, 2, 22, 14, 2)),
        ("2003-08-08T14:09:14", datetime(2003, 8, 8, 14, 9, 14)),
        ("2017-11-27T06:14:30.123", datetime(2017, 11, 27, 6, 14, 30, 123000)),
        ("2017-11-27T06:14:30,123456", datetime(2017, 11, 27, 6, 14, 30, 123456)),
        ("2018-07-03T14:07:00.123456000001", datetime(2018, 7, 3, 14, 7, 0, 123456)),
        ("2018-07-03T14:07:00.123456999999", datetime(2018, 7, 3, 14, 7, 0, 123456)),
    ],
    ids=["hour", "minute", "basic-second", "extended-second", "millisecond", "comma", "truncate-low", "truncate-high"],
)
def test_isoparse_time_and_fraction_forms(value, expected):
    assert isoparse(value) == expected


@pytest.mark.parametrize(
    ("value", "offset"),
    [
        ("2017-11-27T06:14:30Z", timedelta(0)),
        ("2017-11-27T06:14:30+05", timedelta(hours=5)),
        ("2017-11-27T06:14:30-05:30", -timedelta(hours=5, minutes=30)),
        ("2017-11-27T06:14:30+1130", timedelta(hours=11, minutes=30)),
    ],
    ids=["zulu", "hours", "colon", "basic"],
)
def test_isoparse_timezone_offsets(value, offset):
    parsed = isoparse(value)
    assert parsed.utcoffset() == offset
    assert parsed.tzinfo is not None


@pytest.mark.parametrize(
    "value",
    [
        "2014-04-11T00",
        "2014-04-10T24",
        "2014-04-11T00:00",
        "2014-04-10T24:00:00.000000",
    ],
    ids=["zero-hour", "hour-24", "zero-minute", "hour-24-full"],
)
def test_isoparse_midnight_forms(value):
    assert isoparse(value) == datetime(2014, 4, 11)


@pytest.mark.parametrize("separator", [" ", "a", "T", "_", "-"], ids=["space", "letter", "tee", "underscore", "dash"])
def test_default_isoparser_accepts_single_separator(separator):
    assert isoparse(f"2014-01-01{separator}14:33:09") == datetime(2014, 1, 1, 14, 33, 9)


def test_configured_isoparser_separator():
    parser = isoparser(sep=" ")
    assert parser.isoparse("2014-01-01 14:33:09") == datetime(2014, 1, 1, 14, 33, 9)
    with pytest.raises(ValueError):
        parser.isoparse("2014-01-01T14:33:09")


@pytest.mark.parametrize(
    "value",
    [
        "201",
        "2012-0425",
        "201204-25",
        "20120425T0120:00",
        "20120411T03:30+",
        "20120411T03:30-25:40",
        "20120411T03:30+00:60",
        "2012-1a",
    ],
    ids=["short-year", "mixed-date-a", "mixed-date-b", "mixed-time", "short-zone", "zone-hour", "zone-minute", "bad-month"],
)
def test_isoparse_rejects_malformed_values(value):
    with pytest.raises(ValueError):
        isoparse(value)


def test_zero_offset_is_utc_equivalent():
    parsed = isoparse("2020-01-02T03:04:05+00:00")
    assert parsed.utcoffset() == timedelta(0)
    assert parsed.astimezone(tz.UTC) == datetime(2020, 1, 2, 3, 4, 5, tzinfo=tz.UTC)
