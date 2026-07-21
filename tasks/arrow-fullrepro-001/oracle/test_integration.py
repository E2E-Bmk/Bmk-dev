from __future__ import annotations

import time
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from zoneinfo import ZoneInfo

import arrow
from arrow import (
    FORMAT_ATOM,
    FORMAT_COOKIE,
    FORMAT_RFC822,
    FORMAT_RFC850,
    FORMAT_RFC1036,
    FORMAT_RFC1123,
    FORMAT_RFC2822,
    FORMAT_RFC3339,
    FORMAT_RFC3339_STRICT,
    Arrow,
    ArrowFactory,
    ParserError,
)
from arrow.formatter import DateTimeFormatter


def assert_datetime_close(actual: Arrow | datetime, expected: datetime) -> None:
    actual_datetime = actual.datetime if isinstance(actual, Arrow) else actual
    assert abs((actual_datetime - expected).total_seconds()) < 10


def formatter() -> DateTimeFormatter:
    return DateTimeFormatter()


def test_custom_factory_returns_custom_arrow_subclass() -> None:
    class CustomArrow(Arrow):
        pass

    custom_factory = arrow.api.factory(CustomArrow)
    assert isinstance(custom_factory, ArrowFactory)
    assert isinstance(custom_factory.utcnow(), CustomArrow)


def test_constructor_normalizes_pytz_timezone() -> None:
    pytz = pytest.importorskip("pytz")
    result = Arrow(2013, 2, 2, 12, 30, 45, 999_999, tzinfo=pytz.timezone("Europe/Paris"))
    expected = datetime(2013, 2, 2, 12, 30, 45, 999_999, tzinfo=ZoneInfo("Europe/Paris"))
    assert result.datetime == expected


def test_constructor_accepts_zoneinfo_timezone() -> None:
    expected = datetime(2024, 7, 10, 18, 55, 45, 999_999, tzinfo=ZoneInfo("Europe/Paris"))
    assert Arrow(2024, 7, 10, 18, 55, 45, 999_999, tzinfo=ZoneInfo("Europe/Paris")).datetime == expected


def test_constructor_accepts_dateutil_timezone() -> None:
    dateutil_tz = pytest.importorskip("dateutil.tz")
    result = Arrow(2024, 7, 10, 18, 55, 45, 999_999, tzinfo=dateutil_tz.gettz("Europe/Paris"))
    expected = datetime(2024, 7, 10, 18, 55, 45, 999_999, tzinfo=ZoneInfo("Europe/Paris"))
    assert result.datetime == expected


def test_arrow_now_matches_local_time() -> None:
    assert_datetime_close(Arrow.now(), datetime.now().astimezone())


def test_arrow_utcnow_is_utc() -> None:
    result = Arrow.utcnow()
    assert_datetime_close(result, datetime.now(timezone.utc))
    assert result.utcoffset() == timezone.utc.utcoffset(result.datetime)
    assert result.fold == 0


def test_arrow_fromtimestamp_accepts_timezone_and_rejects_text() -> None:
    timestamp = time.time()
    assert_datetime_close(Arrow.fromtimestamp(timestamp), datetime.now().astimezone())
    expected = datetime.fromtimestamp(timestamp, ZoneInfo("Europe/Paris"))
    assert_datetime_close(Arrow.fromtimestamp(timestamp, tzinfo="Europe/Paris"), expected)
    with pytest.raises(ValueError):
        Arrow.fromtimestamp("invalid timestamp")


def test_arrow_utcfromtimestamp_is_utc_and_rejects_text() -> None:
    timestamp = time.time()
    assert_datetime_close(Arrow.utcfromtimestamp(timestamp), datetime.now(timezone.utc))
    with pytest.raises(ValueError):
        Arrow.utcfromtimestamp("invalid timestamp")


def test_arrow_fromdatetime_defaults_naive_input_to_utc() -> None:
    value = datetime(2013, 2, 3, 12, 30, 45, 1)
    assert Arrow.fromdatetime(value).datetime == value.replace(tzinfo=timezone.utc)


def test_arrow_fromdatetime_preserves_input_timezone() -> None:
    value = datetime(2013, 2, 3, 12, 30, 45, 1, tzinfo=ZoneInfo("US/Pacific"))
    assert Arrow.fromdatetime(value).datetime == value


def test_arrow_fromdatetime_accepts_explicit_timezone() -> None:
    value = datetime(2013, 2, 3, 12, 30, 45, 1)
    assert Arrow.fromdatetime(value, ZoneInfo("US/Pacific")).datetime == value.replace(
        tzinfo=ZoneInfo("US/Pacific")
    )


def test_arrow_fromdate_uses_midnight_and_timezone() -> None:
    result = Arrow.fromdate(date(2013, 2, 3), ZoneInfo("US/Pacific"))
    assert result.datetime == datetime(2013, 2, 3, tzinfo=ZoneInfo("US/Pacific"))


def test_arrow_strptime_accepts_timezone() -> None:
    text = "2013-02-03 12:30:45"
    assert Arrow.strptime(text, "%Y-%m-%d %H:%M:%S").datetime == datetime(
        2013, 2, 3, 12, 30, 45, tzinfo=timezone.utc
    )
    assert Arrow.strptime(text, "%Y-%m-%d %H:%M:%S", tzinfo="Europe/Paris").datetime == datetime(
        2013, 2, 3, 12, 30, 45, tzinfo=ZoneInfo("Europe/Paris")
    )


def test_arrow_fromordinal_validates_and_constructs() -> None:
    with pytest.raises(TypeError):
        Arrow.fromordinal(1_607_066_909.937968)
    with pytest.raises(ValueError):
        Arrow.fromordinal(1_607_066_909)
    ordinal = datetime.now().toordinal()
    with pytest.raises(TypeError):
        Arrow.fromordinal(str(ordinal))
    assert Arrow.fromordinal(ordinal).naive == datetime.fromordinal(ordinal)


def test_format_protocol_uses_arrow_tokens() -> None:
    assert f"{Arrow(2013, 2, 3):YYYY-MM-DD}" == "2013-02-03"


def test_bare_format_uses_default_pattern() -> None:
    assert Arrow(2013, 2, 3, 12, 30, 45).format() == "2013-02-03 12:30:45+00:00"


def test_empty_format_protocol_matches_str() -> None:
    value = Arrow(2013, 2, 3, 12, 30, 45)
    assert f"{value}" == str(value)


def test_factory_get_without_args_returns_current_utc() -> None:
    assert_datetime_close(ArrowFactory().get(), datetime.now(timezone.utc))


def test_factory_timestamp_matches_explicit_x_parse() -> None:
    factory = ArrowFactory()
    assert factory.get(1_406_430_900).timestamp() == factory.get("1406430900", "X").timestamp()


def test_factory_rejects_none() -> None:
    with pytest.raises(TypeError):
        ArrowFactory().get(None)


def test_factory_accepts_struct_time() -> None:
    assert_datetime_close(ArrowFactory().get(time.gmtime()), datetime.now(timezone.utc))


def test_factory_accepts_numeric_timestamps_and_rejects_numeric_strings() -> None:
    factory = ArrowFactory()
    integer = int(time.time())
    expected = datetime.fromtimestamp(integer, timezone.utc)
    assert factory.get(integer).datetime == expected
    with pytest.raises(ParserError):
        factory.get(str(integer))
    floating = time.time()
    assert_datetime_close(factory.get(floating), datetime.fromtimestamp(floating, timezone.utc))
    with pytest.raises(ParserError):
        factory.get(str(floating))


def test_factory_normalizes_millisecond_and_microsecond_timestamps() -> None:
    factory = ArrowFactory()
    assert factory.get(1_591_328_104_308).datetime == datetime.fromtimestamp(
        1_591_328_104.308, timezone.utc
    )
    assert factory.get(1_591_328_104_308_505).datetime == datetime.fromtimestamp(
        1_591_328_104.308505, timezone.utc
    )


def test_factory_timestamp_accepts_timezone() -> None:
    timestamp = time.time()
    expected = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(ZoneInfo("US/Pacific"))
    assert_datetime_close(ArrowFactory().get(timestamp, tzinfo=ZoneInfo("US/Pacific")), expected)


def test_factory_accepts_existing_arrow() -> None:
    value = Arrow.utcnow()
    assert ArrowFactory().get(value) == value


def test_factory_accepts_datetime() -> None:
    value = datetime.now(timezone.utc)
    assert ArrowFactory().get(value) == value


def test_factory_accepts_date() -> None:
    value = date.today()
    assert ArrowFactory().get(value).datetime == datetime(value.year, value.month, value.day, tzinfo=timezone.utc)


def test_factory_accepts_tzinfo_as_current_time_request() -> None:
    expected = datetime.now(timezone.utc).astimezone(ZoneInfo("US/Pacific"))
    assert_datetime_close(ArrowFactory().get(ZoneInfo("US/Pacific")), expected)


def test_factory_accepts_dateparser_datetime() -> None:
    dateparser = pytest.importorskip("dateparser")
    parsed = dateparser.parse("1990-01-01T00:00:00+00:00")
    assert parsed is not None
    assert ArrowFactory().get(parsed).to("UTC").datetime == datetime(
        1990, 1, 1, tzinfo=timezone.utc
    )


def test_factory_accepts_tzinfo_keyword_without_positional_value() -> None:
    expected = datetime.now(timezone.utc).astimezone(ZoneInfo("US/Pacific"))
    assert_datetime_close(ArrowFactory().get(tzinfo=ZoneInfo("US/Pacific")), expected)


def test_factory_accepts_timezone_name_and_rejects_unknown_name() -> None:
    expected = datetime.now(timezone.utc).astimezone(ZoneInfo("US/Pacific"))
    assert_datetime_close(ArrowFactory().get(tzinfo="US/Pacific"), expected)
    with pytest.raises(ParserError):
        ArrowFactory().get(tzinfo="US/PacificInvalidTzinfo")


def test_factory_normalizes_whitespace_when_requested() -> None:
    factory = ArrowFactory()
    result = factory.get(
        "Jun 1 2005  1:33PM", "MMM D YYYY H:mmA", tzinfo="UTC", normalize_whitespace=True
    )
    assert result.datetime == datetime(2005, 6, 1, 13, 33, tzinfo=timezone.utc)
    result = factory.get("\t 2013-05-05T12:30:45.123456 \t \n", normalize_whitespace=True)
    assert result.datetime == datetime(2013, 5, 5, 12, 30, 45, 123456, tzinfo=timezone.utc)


def test_factory_datetime_timezone_keyword_replaces_timezone() -> None:
    result = ArrowFactory().get(datetime(2021, 4, 29, 6), tzinfo="America/Chicago")
    assert result.datetime == datetime(2021, 4, 29, 6, tzinfo=ZoneInfo("America/Chicago"))


def test_factory_arrow_timezone_keyword_replaces_timezone() -> None:
    result = ArrowFactory().get(Arrow(2021, 4, 29, 6), tzinfo="America/Chicago")
    assert result.datetime == datetime(2021, 4, 29, 6, tzinfo=ZoneInfo("America/Chicago"))


def test_factory_date_timezone_keyword_sets_timezone() -> None:
    result = ArrowFactory().get(date(2021, 4, 29), tzinfo="America/Chicago")
    assert result.date() == date(2021, 4, 29)
    assert result.tzinfo == ZoneInfo("America/Chicago")


def test_factory_iso_calendar_timezone_keyword_sets_timezone() -> None:
    result = ArrowFactory().get((2004, 1, 7), tzinfo="America/Chicago")
    assert result.datetime == datetime(2004, 1, 4, tzinfo=ZoneInfo("America/Chicago"))


def test_factory_accepts_iso_string() -> None:
    value = datetime.now(timezone.utc).replace(microsecond=123456)
    assert ArrowFactory().get(value.isoformat()).datetime == value


def test_factory_accepts_iso_calendar_and_validates_shape() -> None:
    factory = ArrowFactory()
    pairs = [
        (datetime(2004, 1, 4), (2004, 1, 7)),
        (datetime(2008, 12, 30), (2009, 1, 2)),
        (datetime(2010, 1, 2), (2009, 53, 6)),
        (datetime(2000, 2, 29), (2000, 9, 2)),
    ]
    for expected, iso_value in pairs:
        assert factory.get(iso_value) == factory.get(expected)
    with pytest.raises(TypeError):
        factory.get((2014, 7, 1, 4))
    with pytest.raises(TypeError):
        factory.get((2014, 7))
    with pytest.raises(ValueError):
        factory.get((2014, 70, 1))
    with pytest.raises(ValueError):
        factory.get((2014, 7, 10))


def test_factory_rejects_unknown_single_argument() -> None:
    with pytest.raises(TypeError):
        ArrowFactory().get(object())


def test_factory_rejects_boolean_timestamp() -> None:
    with pytest.raises(TypeError):
        ArrowFactory().get(False)
    with pytest.raises(TypeError):
        ArrowFactory().get(True)


def test_factory_accepts_decimal_timestamp() -> None:
    result = ArrowFactory().get(Decimal("1577836800.268430"))
    assert result.datetime == datetime(2020, 1, 1, 0, 0, 0, 268_430, tzinfo=timezone.utc)


def test_factory_datetime_and_tzinfo_pair() -> None:
    result = ArrowFactory().get(datetime(2013, 1, 1), ZoneInfo("US/Pacific"))
    assert result.datetime == datetime(2013, 1, 1, tzinfo=ZoneInfo("US/Pacific"))


def test_factory_datetime_and_timezone_name_pair() -> None:
    result = ArrowFactory().get(datetime(2013, 1, 1), "US/Pacific")
    assert result.datetime == datetime(2013, 1, 1, tzinfo=ZoneInfo("US/Pacific"))


def test_factory_date_and_tzinfo_pair() -> None:
    result = ArrowFactory().get(date(2013, 1, 1), ZoneInfo("US/Pacific"))
    assert result.datetime == datetime(2013, 1, 1, tzinfo=ZoneInfo("US/Pacific"))


def test_factory_date_and_timezone_name_pair() -> None:
    result = ArrowFactory().get(date(2013, 1, 1), "US/Pacific")
    assert result.datetime == datetime(2013, 1, 1, tzinfo=ZoneInfo("US/Pacific"))


def test_factory_rejects_datetime_with_invalid_timezone_object() -> None:
    with pytest.raises(TypeError):
        ArrowFactory().get(datetime.now(timezone.utc), object())


def test_factory_rejects_date_with_invalid_timezone_object() -> None:
    with pytest.raises(TypeError):
        ArrowFactory().get(date.today(), object())


def test_formatter_formats_combined_pattern() -> None:
    assert formatter().format(datetime(2013, 2, 5, 12, 32, 51), "MM-DD-YYYY hh:mm:ss a") == "02-05-2013 12:32:51 pm"


def test_formatter_year_tokens() -> None:
    value = datetime(2013, 1, 1)
    assert formatter().format(value, "YYYY YY") == "2013 13"


def test_formatter_month_tokens() -> None:
    assert formatter().format(datetime(2013, 1, 1), "MMMM MMM MM M") == "January Jan 01 1"


def test_formatter_day_tokens() -> None:
    value = datetime(2013, 2, 1)
    assert formatter().format(value, "DDDD DDD DD D Do dddd ddd d") == "032 32 01 1 1st Friday Fri 5"


def test_formatter_hour_tokens() -> None:
    assert formatter().format(datetime(2013, 1, 1, 2), "HH H hh h") == "02 2 02 2"
    assert formatter().format(datetime(2013, 1, 1, 13), "HH H hh h") == "13 13 01 1"
    assert formatter().format(datetime(2013, 1, 1, 0), "hh h") == "12 12"


def test_formatter_minute_tokens() -> None:
    assert formatter().format(datetime(2013, 1, 1, 0, 1), "mm m") == "01 1"


def test_formatter_second_tokens() -> None:
    assert formatter().format(datetime(2013, 1, 1, 0, 0, 1), "ss s") == "01 1"


def test_formatter_fraction_tokens() -> None:
    value = datetime(2013, 1, 1, 0, 0, 0, 123456)
    assert formatter().format(value, "SSSSSS SSSSS SSSS SSS SS S") == "123456 12345 1234 123 12 1"
    value = datetime(2013, 1, 1, 0, 0, 0, 2000)
    assert formatter().format(value, "SSSSSS SSSSS SSSS SSS SS S") == "002000 00200 0020 002 00 0"


def test_formatter_timestamp_tokens() -> None:
    value = datetime.now(tz=timezone.utc)
    assert formatter().format(value, "X") == str(value.timestamp())
    assert formatter().format(value, "x") == str(int(value.timestamp() * 1_000_000))


def test_formatter_timezone_offset_tokens() -> None:
    value = datetime(2013, 1, 1, tzinfo=ZoneInfo("US/Pacific"))
    assert formatter().format(value, "ZZ Z") == "-08:00 -0800"


def test_formatter_timezone_name_alaska() -> None:
    value = datetime(1986, 2, 14, tzinfo=ZoneInfo("US/Alaska"))
    assert formatter().format(value, "ZZZ") == value.tzname()


def test_formatter_timezone_name_utc() -> None:
    value = datetime(1986, 2, 14, tzinfo=ZoneInfo("UTC"))
    assert formatter().format(value, "ZZZ") == value.tzname()


def test_formatter_timezone_name_mariehamn() -> None:
    value = datetime(1986, 2, 14, tzinfo=ZoneInfo("Europe/Mariehamn"))
    assert formatter().format(value, "ZZZ") == value.tzname()


def test_formatter_am_pm_tokens() -> None:
    assert formatter().format(datetime(2012, 1, 1, 11), "a A") == "am AM"
    assert formatter().format(datetime(2012, 1, 1, 13), "a A") == "pm PM"


def test_formatter_iso_week_token() -> None:
    assert formatter().format(datetime(2017, 5, 19), "W") == "2017-W20-5"
    assert formatter().format(datetime(2011, 1, 20), "W") == "2011-W03-4"


def test_formatter_scans_tokens_inside_literal_text() -> None:
    assert formatter().format(datetime(2012, 1, 1, 11), "NONSENSE") == "NON0EN0E"


def test_formatter_bracket_escaping() -> None:
    value = datetime(2015, 12, 10, 17, 9)
    assert formatter().format(value, "MMMM D, YYYY [at] h:mma") == "December 10, 2015 at 5:09pm"
    assert formatter().format(value, "[MMMM] M D, YYYY [at] h:mma") == "MMMM 12 10, 2015 at 5:09pm"


BUILTIN_VALUE = datetime(1975, 12, 25, 14, 15, 16, tzinfo=ZoneInfo("America/New_York"))


def test_builtin_atom_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_ATOM) == "1975-12-25 14:15:16-05:00"


def test_builtin_cookie_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_COOKIE) == "Thursday, 25-Dec-1975 14:15:16 EST"


def test_builtin_rfc822_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC822) == "Thu, 25 Dec 75 14:15:16 -0500"


def test_builtin_rfc850_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC850) == "Thursday, 25-Dec-75 14:15:16 EST"


def test_builtin_rfc1036_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC1036) == "Thu, 25 Dec 75 14:15:16 -0500"


def test_builtin_rfc1123_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC1123) == "Thu, 25 Dec 1975 14:15:16 -0500"


def test_builtin_rfc2822_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC2822) == "Thu, 25 Dec 1975 14:15:16 -0500"


def test_builtin_rfc3339_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC3339) == "1975-12-25 14:15:16-05:00"


def test_builtin_rfc3339_strict_format() -> None:
    assert formatter().format(BUILTIN_VALUE, FORMAT_RFC3339_STRICT) == "1975-12-25T14:15:16-05:00"
