# Spec2Repo oracle - integration tests for dateparser-dates-fullrepro-001
from datetime import datetime, timedelta

import pytest

import dateparser
from dateparser import DateDataParser, parse
from dateparser.conf import SettingValidationError
from dateparser.date import DateData
from dateparser.search import search_dates


BASE = datetime(2020, 1, 15, 9, 30)
MIDYEAR = datetime(2020, 6, 16, 0, 0)


def test_parse_custom_language_detector_for_top_level_parse():
    calls = []

    def detector(text, confidence_threshold):
        calls.append((text, confidence_threshold))
        return ["es"]

    assert parse("3 de marzo de 2020", detect_languages_function=detector) == datetime(2020, 3, 3)
    assert calls == [("3 de marzo de 2020", 0.5)]


def test_parse_languages_argument_prevents_custom_detector_call():
    calls = []

    def detector(*args, **kwargs):
        calls.append((args, kwargs))
        return ["fr"]

    assert parse("3 de marzo de 2020", languages=["es"], detect_languages_function=detector) == datetime(2020, 3, 3)
    assert calls == []


def test_search_dates_finds_documented_satellite_date():
    result = search_dates("The first artificial Earth satellite was launched on 4 October 1957.", languages=["en"])
    assert result is not None
    assert len(result) == 1
    match, date_obj = result[0]
    assert date_obj == datetime(1957, 10, 4)
    assert parse(match, languages=["en"]) == date_obj


def test_search_dates_adds_detected_language_without_changing_datetime():
    result = search_dates(
        "The first artificial Earth satellite was launched on 4 October 1957.",
        languages=["en"],
        add_detected_language=True,
    )
    assert result is not None
    assert len(result) == 1
    match, date_obj, language = result[0]
    assert date_obj == datetime(1957, 10, 4)
    assert parse(match, languages=["en"]) == date_obj
    assert language == "en"


def test_search_dates_extracts_multiple_dates_in_order():
    text = "The client arrived on March 3rd, 2004 and returned on May 6th 2004."
    result = search_dates(text, languages=["en"])
    assert result is not None
    assert [date_obj for _, date_obj in result] == [
        datetime(2004, 3, 3),
        datetime(2004, 5, 6),
    ]
    assert [parse(match, languages=["en"]) for match, _ in result] == [date_obj for _, date_obj in result]


def test_search_dates_with_explicit_spanish_language():
    result = search_dates("Llego el 3 de marzo de 2020.", languages=["es"])
    assert result is not None
    assert len(result) == 1
    match, date_obj = result[0]
    assert date_obj == datetime(2020, 3, 3)
    assert parse(match, languages=["es"]) == date_obj


def test_search_dates_custom_language_detector():
    calls = []

    def detector(text, confidence_threshold):
        calls.append((text, confidence_threshold))
        return ["es"]

    result = search_dates("Llego el 3 de marzo de 2020.", detect_languages_function=detector)
    assert result is not None
    assert len(result) == 1
    match, date_obj = result[0]
    assert date_obj == datetime(2020, 3, 3)
    assert parse(match, languages=["es"]) == date_obj
    assert calls == [("Llego el 3 de marzo de 2020.", 0.5)]


def test_search_dates_languages_argument_prevents_detector_call():
    calls = []

    def detector(*args, **kwargs):
        calls.append((args, kwargs))
        return ["fr"]

    result = search_dates("Llego el 3 de marzo de 2020.", languages=["es"], detect_languages_function=detector)
    assert result is not None
    assert len(result) == 1
    match, date_obj = result[0]
    assert date_obj == datetime(2020, 3, 3)
    assert parse(match, languages=["es"]) == date_obj
    assert calls == []


def test_search_dates_relative_and_absolute_with_fixed_base():
    result = search_dates(
        "Review it tomorrow and on 17 January 2020.",
        languages=["en"],
        settings={"RELATIVE_BASE": BASE},
    )
    assert result is not None
    assert [date_obj for _, date_obj in result] == [
        datetime(2020, 1, 16, 9, 30),
        datetime(2020, 1, 17),
    ]
    assert [
        parse(match, languages=["en"], settings={"RELATIVE_BASE": BASE}) for match, _ in result
    ] == [date_obj for _, date_obj in result]


def test_search_dates_return_time_span_for_past_month():
    settings = {"RELATIVE_BASE": datetime(2020, 5, 15, 12, 0), "RETURN_TIME_SPAN": True}
    assert search_dates("Report covers past month.", languages=["en"], settings=settings) == [
        ("past month (start)", datetime(2020, 4, 15, 12, 0)),
        ("past month (end)", datetime(2020, 5, 15, 12, 0)),
    ]


def test_search_dates_return_time_span_for_past_week_default_monday():
    settings = {"RELATIVE_BASE": datetime(2020, 5, 15, 12, 0), "RETURN_TIME_SPAN": True}
    assert search_dates("Report covers past week.", languages=["en"], settings=settings) == [
        ("past week (start)", datetime(2020, 5, 4, 12, 0)),
        ("past week (end)", datetime(2020, 5, 10, 12, 0)),
    ]


def test_search_dates_return_time_span_respects_sunday_week_start():
    settings = {
        "RELATIVE_BASE": datetime(2020, 5, 15, 12, 0),
        "RETURN_TIME_SPAN": True,
        "DEFAULT_START_OF_WEEK": "sunday",
    }
    assert search_dates("Report covers past week.", languages=["en"], settings=settings) == [
        ("past week (start)", datetime(2020, 5, 3, 12, 0)),
        ("past week (end)", datetime(2020, 5, 9, 12, 0)),
    ]


def test_cross_view_parse_matches_date_data_parser():
    settings = {"RELATIVE_BASE": MIDYEAR, "PREFER_DAY_OF_MONTH": "last"}
    parser = DateDataParser(settings=settings)
    assert parse("December 2015", settings=settings) == parser.get_date_data("December 2015")["date_obj"]


def test_cross_view_search_result_matches_direct_parse():
    settings = {"RELATIVE_BASE": BASE}
    result = search_dates("Review it on 17 January 2020.", languages=["en"], settings=settings)
    assert result[0][1] == parse("17 January 2020", languages=["en"], settings=settings)


def test_cross_view_add_detected_language_preserves_search_payload():
    text = "The satellite launched on 4 October 1957."
    without_language = search_dates(text, languages=["en"])
    with_language = search_dates(text, languages=["en"], add_detected_language=True)
    assert [(match, date) for match, date, language in with_language] == without_language
    assert with_language[0][2] == "en"


def test_cross_view_timezone_parse_matches_date_data_parser():
    settings = {"TIMEZONE": "UTC", "TO_TIMEZONE": "US/Eastern"}
    parser = DateDataParser(settings=settings)
    assert parse("January 12, 2012 10:00 PM", settings=settings) == parser.get_date_data(
        "January 12, 2012 10:00 PM"
    )["date_obj"]


def test_cross_view_strict_parsing_none_matches_date_data_parser_none():
    settings = {"RELATIVE_BASE": MIDYEAR, "STRICT_PARSING": True}
    data = DateDataParser(settings=settings).get_date_data("March")
    assert parse("March", settings=settings) is None
    assert data["date_obj"] is None
