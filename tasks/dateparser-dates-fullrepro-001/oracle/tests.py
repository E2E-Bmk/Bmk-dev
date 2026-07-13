from datetime import datetime, timedelta

import pytest

import dateparser
from dateparser import DateDataParser, parse
from dateparser.conf import SettingValidationError
from dateparser.date import DateData
from dateparser.search import search_dates


BASE = datetime(2020, 1, 15, 9, 30)
MIDYEAR = datetime(2020, 6, 16, 0, 0)


def test_parse_absolute_english_month_name():
    assert parse("12 December 2015", languages=["en"]) == datetime(2015, 12, 12)


def test_parse_numeric_default_mdy_order():
    assert parse("02-03-2016") == datetime(2016, 2, 3)


def test_parse_french_numeric_uses_locale_order_without_override():
    assert parse("le 02-03-2016") == datetime(2016, 3, 2)


def test_parse_explicit_date_order_overrides_locale_order():
    assert parse("le 02-03-2016", settings={"DATE_ORDER": "MDY"}) == datetime(2016, 2, 3)


def test_parse_prefer_locale_date_order_false_uses_configured_order():
    settings = {"DATE_ORDER": "MDY", "PREFER_LOCALE_DATE_ORDER": False}
    assert parse("le 02-03-2016", settings=settings) == datetime(2016, 2, 3)


def test_parse_custom_date_format_with_swapped_day_month():
    assert parse("2014/31/05", date_formats=["%Y/%d/%m"]) == datetime(2014, 5, 31)


def test_parse_spanish_with_explicit_language():
    assert parse("3 de marzo de 2020", languages=["es"]) == datetime(2020, 3, 3)


def test_parse_default_languages_fallback():
    assert parse("3 de marzo de 2020", settings={"DEFAULT_LANGUAGES": ["es"]}) == datetime(2020, 3, 3)


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


def test_parse_use_given_language_order_false_uses_default_priority():
    assert parse("11/12/2020", languages=["es", "en"]) == datetime(2020, 11, 12)


def test_parse_use_given_language_order_true_preserves_caller_order():
    settings = {"USE_GIVEN_LANGUAGE_ORDER": True}
    assert parse("11/12/2020", languages=["es", "en"], settings=settings) == datetime(2020, 12, 11)


def test_parse_relative_tomorrow_uses_relative_base_time():
    settings = {"RELATIVE_BASE": datetime(2020, 1, 1, 13, 45)}
    assert parse("tomorrow", settings=settings) == datetime(2020, 1, 2, 13, 45)


def test_parse_relative_yesterday_uses_relative_base_time():
    settings = {"RELATIVE_BASE": datetime(2020, 1, 1, 13, 45)}
    assert parse("yesterday", settings=settings) == datetime(2019, 12, 31, 13, 45)


def test_parse_relative_weeks_ago_uses_relative_base():
    assert parse("2 weeks ago", settings={"RELATIVE_BASE": BASE}) == datetime(2020, 1, 1, 9, 30)


def test_parse_relative_future_days_uses_relative_base():
    assert parse("in 3 days", settings={"RELATIVE_BASE": BASE}) == datetime(2020, 1, 18, 9, 30)


def test_parse_month_name_uses_current_day_from_relative_base():
    assert parse("March", settings={"RELATIVE_BASE": MIDYEAR}) == datetime(2020, 3, 16)


def test_parse_prefer_dates_from_future_moves_month_forward():
    settings = {"RELATIVE_BASE": MIDYEAR, "PREFER_DATES_FROM": "future"}
    assert parse("March", settings=settings) == datetime(2021, 3, 16)


def test_parse_prefer_dates_from_past_moves_month_backward():
    settings = {"RELATIVE_BASE": MIDYEAR, "PREFER_DATES_FROM": "past"}
    assert parse("August", settings=settings) == datetime(2019, 8, 16)


def test_parse_prefer_day_first_for_missing_day():
    settings = {"RELATIVE_BASE": MIDYEAR, "PREFER_DAY_OF_MONTH": "first"}
    assert parse("December 2015", settings=settings) == datetime(2015, 12, 1)


def test_parse_prefer_day_last_for_missing_day():
    settings = {"RELATIVE_BASE": MIDYEAR, "PREFER_DAY_OF_MONTH": "last"}
    assert parse("December 2015", settings=settings) == datetime(2015, 12, 31)


def test_parse_prefer_month_first_for_year_only():
    settings = {"RELATIVE_BASE": datetime(2020, 3, 27), "PREFER_MONTH_OF_YEAR": "first"}
    assert parse("2015", settings=settings) == datetime(2015, 1, 27)


def test_parse_prefer_month_last_for_year_only():
    settings = {"RELATIVE_BASE": datetime(2020, 3, 27), "PREFER_MONTH_OF_YEAR": "last"}
    assert parse("2015", settings=settings) == datetime(2015, 12, 27)


def test_parse_strict_parsing_rejects_incomplete_month():
    assert parse("March", settings={"RELATIVE_BASE": MIDYEAR, "STRICT_PARSING": True}) is None


def test_parse_require_month_rejects_year_only_input():
    assert parse("2012", settings={"RELATIVE_BASE": MIDYEAR, "REQUIRE_PARTS": ["month"]}) is None


def test_parse_require_day_rejects_month_year_input():
    settings = {"RELATIVE_BASE": MIDYEAR, "REQUIRE_PARTS": ["day"]}
    assert parse("March 2012", settings=settings) is None


def test_parse_require_all_parts_accepts_complete_date():
    settings = {"RELATIVE_BASE": MIDYEAR, "REQUIRE_PARTS": ["day", "month", "year"]}
    assert parse("March 12, 2012", settings=settings) == datetime(2012, 3, 12)


def test_parse_timestamp_in_utc():
    assert parse("1483228800", settings={"TIMEZONE": "UTC"}) == datetime(2017, 1, 1)


def test_parse_no_spaces_time_when_parser_enabled():
    settings = {"PARSERS": ["no-spaces-time"], "RELATIVE_BASE": datetime(2020, 1, 1)}
    assert parse("121994", settings=settings) == datetime(1994, 1, 2)


def test_parse_custom_parser_list_can_exclude_relative_time():
    settings = {"PARSERS": ["custom-formats"], "RELATIVE_BASE": datetime(2020, 1, 1)}
    assert parse("today", settings=settings) is None


def test_parse_unicode_normalization_true_accepts_unaccented_french():
    assert parse("4 decembre 2015", languages=["fr"], settings={"NORMALIZE": True}) == datetime(2015, 12, 4)


def test_parse_unicode_normalization_false_rejects_unaccented_french():
    assert parse("4 decembre 2015", languages=["fr"], settings={"NORMALIZE": False}) is None


def test_parse_timezone_abbreviation_returns_naive_when_requested():
    settings = {"RETURN_AS_TIMEZONE_AWARE": False}
    assert parse("12 Feb 2015 10:56 PM EST", settings=settings) == datetime(2015, 2, 12, 22, 56)


def test_parse_timezone_abbreviation_returns_aware_when_requested():
    settings = {"RETURN_AS_TIMEZONE_AWARE": True}
    result = parse("12 Feb 2015 10:56 PM EST", settings=settings)
    assert result.replace(tzinfo=None) == datetime(2015, 2, 12, 22, 56)
    assert result.tzinfo is not None
    assert result.tzname() == "EST"


def test_parse_timezone_setting_converts_to_target_zone():
    settings = {"TIMEZONE": "UTC", "TO_TIMEZONE": "US/Eastern"}
    assert parse("January 12, 2012 10:00 PM", settings=settings) == datetime(2012, 1, 12, 17, 0)


def test_parse_input_timezone_converts_to_target_zone_with_tzinfo():
    result = parse("January 12, 2012 10:00 PM UTC", settings={"TO_TIMEZONE": "US/Eastern"})
    assert result.replace(tzinfo=None) == datetime(2012, 1, 12, 17, 0)
    assert result.tzinfo is not None
    assert result.utcoffset() == timedelta(hours=-5)


def test_date_data_parser_returns_month_period_for_missing_day():
    data = DateDataParser(settings={"RELATIVE_BASE": MIDYEAR}).get_date_data("March 2015")
    assert data["date_obj"] == datetime(2015, 3, 16)
    assert data["period"] == "month"
    assert data["locale"] == "en"


def test_date_data_parser_returns_year_period_for_year_only():
    data = DateDataParser(settings={"RELATIVE_BASE": MIDYEAR}).get_date_data("2014")
    assert data["date_obj"] == datetime(2014, 6, 16)
    assert data["period"] == "year"
    assert data["locale"] == "en"


def test_date_data_parser_known_languages_selects_dutch_locale():
    parser = DateDataParser(languages=["de", "nl"])
    data = parser.get_date_data("vr jan 24, 2014 12:49")
    assert data["date_obj"] == datetime(2014, 1, 24, 12, 49)
    assert data["period"] == "day"
    assert data["locale"] == "nl"


def test_date_data_parser_known_languages_selects_german_locale():
    parser = DateDataParser(languages=["de", "nl"])
    data = parser.get_date_data("18.10.14 um 22:56 Uhr")
    assert data["date_obj"] == datetime(2014, 10, 18, 22, 56)
    assert data["locale"] == "de"


def test_date_data_parser_known_languages_rejects_outside_language():
    parser = DateDataParser(languages=["de", "nl"])
    data = parser.get_date_data("11 July 2012")
    assert data["date_obj"] is None
    assert data["locale"] is None


def test_date_data_parser_return_time_as_period():
    data = DateDataParser(settings={"RETURN_TIME_AS_PERIOD": True}).get_date_data("vr jan 24, 2014 12:49")
    assert data["date_obj"] == datetime(2014, 1, 24, 12, 49)
    assert data["period"] == "time"
    assert data["locale"] == "nl"


def test_date_data_parser_date_formats_report_month_period():
    parser = DateDataParser(settings={"RELATIVE_BASE": MIDYEAR})
    data = parser.get_date_data("2015-12", date_formats=["%Y-%m"])
    assert data["date_obj"] is not None
    assert data["date_obj"].year == 2015
    assert data["date_obj"].month == 12
    assert data["period"] == "month"


def test_date_data_supports_dictionary_style_read():
    data = DateData(date_obj=datetime(2020, 5, 17), period="day", locale="en")
    assert data["date_obj"] == datetime(2020, 5, 17)
    assert data["period"] == "day"
    assert data["locale"] == "en"


def test_date_data_supports_dictionary_style_write():
    data = DateData(date_obj=None, period="day", locale=None)
    data["date_obj"] = datetime(2020, 5, 17)
    data["locale"] = "en"
    assert data.date_obj == datetime(2020, 5, 17)
    assert data.locale == "en"


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


def test_invalid_setting_name_raises_setting_validation_error():
    with pytest.raises(SettingValidationError):
        parse("2020", settings={"NOT_A_SETTING": True})


def test_invalid_date_order_raises_setting_validation_error():
    with pytest.raises(SettingValidationError):
        parse("2020", settings={"DATE_ORDER": "BAD"})


def test_unknown_parser_name_raises_setting_validation_error():
    with pytest.raises(SettingValidationError):
        parse("2020", settings={"PARSERS": ["bad-parser"]})


def test_invalid_languages_type_raises_type_error():
    with pytest.raises(TypeError):
        parse("2020", languages="en")


def test_unknown_language_raises_value_error():
    with pytest.raises(ValueError):
        parse("2020", languages=["xx"])


def test_invalid_locales_type_raises_type_error():
    with pytest.raises(TypeError):
        parse("2020", locales="en-US")


def test_unknown_locale_raises_value_error():
    with pytest.raises(ValueError):
        parse("2020", locales=["xx-YY"])


def test_invalid_region_type_raises_type_error():
    with pytest.raises(TypeError):
        parse("2020", region=1)


def test_use_given_order_without_languages_or_locales_raises_value_error():
    with pytest.raises(ValueError):
        DateDataParser(use_given_order=True)


def test_get_date_data_non_string_input_raises_type_error():
    with pytest.raises(TypeError):
        DateDataParser().get_date_data(1)


def test_date_data_unknown_key_read_raises_key_error():
    with pytest.raises(KeyError):
        DateData()["missing"]


def test_date_data_unknown_key_write_raises_key_error():
    data = DateData()
    with pytest.raises(KeyError):
        data["missing"] = "value"
