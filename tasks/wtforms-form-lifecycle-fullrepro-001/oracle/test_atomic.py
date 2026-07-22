"""Atomic tests for wtforms-form-lifecycle-fullrepro-001."""

from __future__ import annotations

import datetime as dt
import decimal
import math
import uuid

import pytest

from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    FieldList,
    FloatField,
    Form,
    FormField,
    IntegerField,
    MonthField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TimeField,
)
from wtforms import validators
from wtforms.csrf.core import CSRF
from wtforms.meta import DefaultMeta


from conftest import FormData


@pytest.mark.parametrize("submitted, expected", [("1", 1), ("0", 0), ("-9", -9)])
def test_integer_input_is_coerced(submitted, expected):
    class F(Form):
        value = IntegerField()

    assert F(FormData(value=[submitted])).value.data == expected

@pytest.mark.parametrize("submitted", ["bad", "1.2", ""])
def test_invalid_integer_is_reported_by_validation(submitted):
    class F(Form):
        value = IntegerField()

    form = F(FormData(value=[submitted]))
    assert form.value.data is None
    assert form.validate() is False
    assert form.value.process_errors
    assert form.errors["value"]

@pytest.mark.parametrize("submitted, expected", [("false", False), ("", False), ("yes", True)])
def test_boolean_field_uses_documented_false_values(submitted, expected):
    class F(Form):
        value = BooleanField()

    assert F(FormData(value=[submitted])).value.data is expected

def test_submit_field_is_false_when_missing():
    class F(Form):
        submit = SubmitField()

    assert F().submit.data is False

@pytest.mark.parametrize("submitted, expected", [("1.5", 1.5), ("0", 0.0), ("-2", -2.0)])
def test_float_field_coerces_public_values(submitted, expected):
    class F(Form):
        value = FloatField()

    assert F(FormData(value=[submitted])).value.data == expected

@pytest.mark.parametrize("submitted, expected", [("1.20", decimal.Decimal("1.20")), ("0", decimal.Decimal("0")), ("-3.5", decimal.Decimal("-3.5"))])
def test_decimal_field_coerces_submitted_text(submitted, expected):
    class F(Form):
        value = DecimalField()

    assert F(FormData(value=[submitted])).value.data == expected

@pytest.mark.parametrize("submitted, expected", [("2024-01-02", dt.date(2024, 1, 2)), ("2000-12-31", dt.date(2000, 12, 31)), ("1999-01-01", dt.date(1999, 1, 1))])
def test_date_field_parses_documented_format(submitted, expected):
    class F(Form):
        value = DateField()

    assert F(FormData(value=[submitted])).value.data == expected

def test_password_field_keeps_submitted_data():
    class F(Form):
        value = PasswordField()

    assert F(FormData(value=["secret"])).value.data == "secret"

def test_missing_choices_raise_when_membership_is_required():
    class F(Form):
        choice = SelectField()

    with pytest.raises(TypeError):
        F(FormData(choice=["x"])).validate()

@pytest.mark.parametrize("data, valid", [("x", True), ("", False), ("   ", False)])
def test_data_required_uses_post_coercion_truthiness(data, valid):
    class F(Form):
        value = StringField(validators=[validators.DataRequired()])

    assert F(FormData(value=[data])).validate() is valid

@pytest.mark.parametrize("raw, obj_value, valid", [(["x"], None, True), ([""], None, False), (None, "default", False)])
def test_input_required_requires_nonempty_submitted_raw_data(raw, obj_value, valid):
    class F(Form):
        value = StringField(validators=[validators.InputRequired()], default=obj_value)

    form = F(FormData(value=raw) if raw is not None else None)
    assert form.validate() is valid

@pytest.mark.parametrize("value, valid", [("ab", True), ("a", False), ("abcd", False)])
def test_length_enforces_inclusive_bounds(value, valid):
    class F(Form):
        value = StringField(validators=[validators.Length(min=2, max=3)])

    assert F(FormData(value=[value])).validate() is valid

def test_length_rejects_unbounded_constructor():
    with pytest.raises(AssertionError):
        validators.Length()

@pytest.mark.parametrize("value, valid", [("3", True), ("2", True), ("5", False)])
def test_number_range_is_inclusive(value, valid):
    class F(Form):
        value = IntegerField(validators=[validators.NumberRange(min=2, max=3)])

    assert F(FormData(value=[value])).validate() is valid

def test_number_range_rejects_nan():
    class F(Form):
        value = FloatField(validators=[validators.NumberRange(min=0)])

    assert F(FormData(value=[str(math.nan)])).validate() is False

@pytest.mark.parametrize("value, valid", [("abc", True), ("xabc", False), ("", False)])
def test_regexp_uses_prefix_matching_by_default(value, valid):
    class F(Form):
        value = StringField(validators=[validators.Regexp(r"abc")])

    assert F(FormData(value=[value])).validate() is valid

@pytest.mark.parametrize("value, valid", [("127.0.0.1", True), ("::1", False), ("not-ip", False)])
def test_ip_address_honors_enabled_family(value, valid):
    class F(Form):
        value = StringField(validators=[validators.IPAddress(ipv4=True, ipv6=False)])

    assert F(FormData(value=[value])).validate() is valid

def test_ip_address_requires_an_enabled_family():
    with pytest.raises(ValueError):
        validators.IPAddress(ipv4=False, ipv6=False)

@pytest.mark.parametrize("value, valid", [("aa:bb:cc:dd:ee:ff", True), ("aa-bb-cc-dd-ee-ff", False), ("xx:bb:cc:dd:ee:ff", False)])
def test_mac_address_requires_colon_hex_octets(value, valid):
    class F(Form):
        value = StringField(validators=[validators.MacAddress()])

    assert F(FormData(value=[value])).validate() is valid

@pytest.mark.parametrize("value, valid", [("https://example.com", True), ("https://example.com:bad", False), ("example.com", False)])
def test_url_requires_scheme_host_and_valid_port(value, valid):
    class F(Form):
        value = StringField(validators=[validators.URL()])

    assert F(FormData(value=[value])).validate() is valid

@pytest.mark.parametrize("value, valid", [("123e4567-e89b-12d3-a456-426614174000", True), ("not-a-uuid", False), ("", False)])
def test_uuid_accepts_parseable_uuid_text(value, valid):
    class F(Form):
        value = StringField(validators=[validators.UUID()])

    assert F(FormData(value=[value])).validate() is valid

@pytest.mark.parametrize("value, valid", [("a", True), ("z", False), (["z", "a"], True)])
def test_any_of_accepts_members_and_list_intersection(value, valid):
    class F(Form):
        value = StringField(validators=[validators.AnyOf(["a", "b"])])

    form = F()
    form.value.data = value
    assert form.validate() is valid

@pytest.mark.parametrize("value, valid", [("z", True), ("a", False), (["z", "a"], False)])
def test_none_of_rejects_members_and_list_intersection(value, valid):
    class F(Form):
        value = StringField(validators=[validators.NoneOf(["a", "b"])])

    form = F()
    form.value.data = value
    assert form.validate() is valid

def test_form_item_access_and_missing_key_behavior():
    class F(Form):
        value = StringField()

    form = F()
    assert form["value"] is form.value
    with pytest.raises(KeyError):
        form["missing"]

def test_rendering_returns_html_safe_value_without_exact_markup_contract():
    class F(Form):
        value = StringField("Visible label")

    rendered = F().value()
    assert hasattr(rendered, "__html__")
    assert str(rendered)


# --- composition fix additions (2026-07-20) ---


def test_string_field_retains_first_submitted_value():
    class F(Form):
        value = StringField()

    form = F(FormData(value=["first", "second"]))
    assert form.value.data == "first"
    assert form.value.raw_data == ["first", "second"]


def test_month_field_parses_month_storing_day_one():
    class F(Form):
        value = MonthField()

    assert F(FormData(value=["2024-05"])).value.data == dt.date(2024, 5, 1)


def test_time_field_parses_documented_format():
    class F(Form):
        value = TimeField()

    assert F(FormData(value=["13:30"])).value.data == dt.time(13, 30)
