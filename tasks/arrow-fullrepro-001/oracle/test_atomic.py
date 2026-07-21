from __future__ import annotations

from datetime import datetime, timezone

import pytest

from arrow import Arrow


def test_constructor_rejects_missing_and_invalid_components() -> None:
    with pytest.raises(TypeError):
        Arrow(2013)
    with pytest.raises(TypeError):
        Arrow(2013, 2)
    with pytest.raises(ValueError):
        Arrow(2013, 2, 2, 12, 30, 45, 9_999_999)


def test_constructor_defaults_and_explicit_components() -> None:
    assert Arrow(2013, 2, 2).datetime == datetime(2013, 2, 2, tzinfo=timezone.utc)
    assert Arrow(2013, 2, 2, 12).datetime == datetime(
        2013, 2, 2, 12, tzinfo=timezone.utc
    )
    assert Arrow(2013, 2, 2, 12, 30, 45, 999_999).datetime == datetime(
        2013, 2, 2, 12, 30, 45, 999_999, tzinfo=timezone.utc
    )


def test_constructor_preserves_fold_for_ambiguous_time() -> None:
    before = Arrow(2017, 10, 29, 2, 0, tzinfo="Europe/Stockholm")
    after = Arrow(2017, 10, 29, 2, 0, tzinfo="Europe/Stockholm", fold=1)
    assert before == after
    assert before.fold == 0
    assert after.fold == 1
    assert before.utcoffset() != after.utcoffset()


def test_repr_uses_arrow_wrapper() -> None:
    value = Arrow(2013, 2, 3, 12, 30, 45, 1)
    assert repr(value) == f"<Arrow [{value.datetime.isoformat()}]>"


def test_str_uses_iso_format() -> None:
    value = Arrow(2013, 2, 3, 12, 30, 45, 1)
    assert str(value) == value.datetime.isoformat()


def test_hash_matches_equivalent_datetime() -> None:
    value = Arrow(2013, 2, 3, 12, 30, 45, 1)
    assert hash(value) == hash(value.datetime)


def test_clone_returns_equal_distinct_value() -> None:
    value = Arrow(2013, 2, 3, 12, 30, 45, 1)
    clone = value.clone()
    assert clone is not value
    assert clone == value
    assert clone.datetime == value.datetime


def test_unknown_attribute_raises_attribute_error() -> None:
    with pytest.raises(AttributeError):
        getattr(Arrow(2013, 1, 1), "property_that_does_not_exist")


def test_week_attribute_uses_iso_week() -> None:
    assert Arrow(2013, 1, 1).week == 1


def test_quarter_attribute_covers_boundaries() -> None:
    expectations = {
        (1, 1): 1,
        (3, 31): 1,
        (4, 1): 2,
        (6, 30): 2,
        (7, 1): 3,
        (9, 30): 3,
        (10, 1): 4,
        (12, 31): 4,
    }
    for (month, day), expected in expectations.items():
        assert Arrow(2013, month, day).quarter == expected


def test_datetime_component_attributes_are_exposed() -> None:
    value = Arrow(2013, 1, 1, 2, 3, 4, 5)
    assert (value.year, value.month, value.day) == (2013, 1, 1)
    assert (value.hour, value.minute, value.second, value.microsecond) == (2, 3, 4, 5)


def test_tzinfo_defaults_to_utc() -> None:
    assert Arrow(2013, 1, 1).tzinfo == timezone.utc


def test_naive_removes_timezone_without_changing_fields() -> None:
    value = Arrow(2013, 1, 1, 2, 3, 4)
    assert value.naive == value.datetime.replace(tzinfo=None)


def test_timestamp_matches_datetime_timestamp() -> None:
    value = Arrow(2013, 1, 1, 2, 3, 4)
    assert value.timestamp() == value.datetime.timestamp()
