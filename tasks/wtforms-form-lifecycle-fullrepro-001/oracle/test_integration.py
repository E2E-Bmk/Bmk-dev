"""Integration tests for wtforms-form-lifecycle-fullrepro-001."""

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
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
)
from wtforms import validators
from wtforms.csrf.core import CSRF
from wtforms.meta import DefaultMeta


from conftest import FormData


@pytest.mark.parametrize("submitted, expected", [("x", "x"), ("", ""), ("first", "first")])
def test_string_input_reaches_field_and_form_data(submitted, expected):
    """Seam: state consistency between submitted string and form.data."""
    class F(Form):
        value = StringField()

    form = F(FormData(value=[submitted]))
    assert form.value.data == expected
    assert form.data["value"] == expected

@pytest.mark.parametrize("value, valid", [("a", True), ("b", True), ("z", False)])
def test_select_field_selection_and_validation(value, valid):
    """Seam: lifecycle crossing from SelectField choice to validation."""
    class F(Form):
        choice = SelectField(choices=[("a", "A"), ("b", "B")])

    form = F(FormData(choice=[value]))
    assert form.validate() is valid
    if valid:
        assert [choice.value for choice in form.choice.iter_choices() if choice.selected] == [value]

@pytest.mark.parametrize("values, valid", [(["a"], True), (["a", "b"], True), (["a", "z"], False)])
def test_select_multiple_preserves_all_values_and_rejects_invalid_members(values, valid):
    """Seam: state consistency for SelectMultipleField multi-value submission."""
    class F(Form):
        choices = SelectMultipleField(choices=[("a", "A"), ("b", "B")])

    form = F(FormData(choices=values))
    assert form.validate() is valid
    assert form.choices.data == values

def test_select_can_disable_membership_validation():
    """Seam: config interaction when validate_choice=False accepts free text."""
    class F(Form):
        choice = SelectField(choices=[("a", "A")], validate_choice=False)

    form = F(FormData(choice=["other"]))
    assert form.validate() is True
    assert form.choice.data == "other"

def test_optional_stops_following_data_required_for_empty_input():
    """Seam: config interaction between Optional and DataRequired validators."""
    class F(Form):
        value = StringField(validators=[validators.Optional(), validators.DataRequired()])

    form = F(FormData(value=[""]))
    assert form.validate() is True
    assert form.errors == {}

@pytest.mark.parametrize("left, right, valid", [("x", "x", True), ("x", "y", False), ("", "", True)])
def test_equal_to_compares_named_field_data(left, right, valid):
    """Seam: state consistency between EqualTo and referenced field data."""
    class F(Form):
        first = StringField()
        second = StringField(validators=[validators.EqualTo("first")])

    assert F(FormData(first=[left], second=[right])).validate() is valid

def test_readonly_rejects_changed_value_and_sets_flag():
    """Seam: error propagation from ReadOnly validator on changed value."""
    class F(Form):
        value = StringField(validators=[validators.ReadOnly()])

    form = F(FormData(value=["changed"]), obj=type("Obj", (), {"value": "old"})())
    assert form.validate() is False
    assert form.value.flags.readonly is True

def test_disabled_rejects_submitted_value_and_sets_flag():
    """Seam: error propagation from Disabled validator on submitted value."""
    class F(Form):
        value = StringField(validators=[validators.Disabled()])

    form = F(FormData(value=["posted"]))
    assert form.validate() is False
    assert form.value.flags.disabled is True

def test_object_precedence_beats_kwargs_and_data():
    """Seam: config interaction for object over kwargs and data precedence."""
    class F(Form):
        value = StringField(default="default")

    obj = type("Obj", (), {"value": "object"})()
    assert F(obj=obj, data={"value": "data"}, value="kwargs").value.data == "object"

def test_kwargs_precedence_beats_data_and_default():
    """Seam: config interaction for kwargs over data and default precedence."""
    class F(Form):
        value = StringField(default="default")

    assert F(data={"value": "data"}, value="kwargs").value.data == "kwargs"

def test_declared_extra_and_inline_filters_run_in_order():
    """Seam: lifecycle crossing through extra, declared, and inline filters."""
    class F(Form):
        value = StringField(filters=[lambda value: value + "d"])

        def filter_value(self, value):
            return value + "i"

    form = F(FormData(value=["x"]), extra_filters={"value": [lambda value: value + "e"]})
    assert form.value.data == "xdei"

def test_filter_value_error_becomes_processing_error():
    """Seam: error propagation from filter ValueError to process_errors."""
    class F(Form):
        value = StringField(filters=[lambda value: int(value)])

    form = F(FormData(value=["not-number"]))
    assert form.validate() is False
    assert form.value.process_errors

def test_field_list_compacts_sparse_input_indices():
    """Seam: state consistency when FieldList compacts sparse indices."""
    class F(Form):
        items = FieldList(StringField(), min_entries=0)

    form = F(FormData(**{"items-1": ["a"], "items-3": ["b"]}))
    assert form.items.data == ["a", "b"]
    assert [entry.name for entry in form.items] == ["items-0", "items-1"]

def test_field_list_min_entries_creates_blank_entries():
    """Seam: lifecycle crossing when min_entries creates blank FieldList rows."""
    class F(Form):
        items = FieldList(StringField(), min_entries=2)

    assert len(F().items) == 2

def test_field_list_append_insert_and_pop_preserve_order():
    """Seam: lifecycle crossing through FieldList append, insert, and pop."""
    class F(Form):
        items = FieldList(StringField())

    field = F().items
    field.append_entry("a")
    field.insert_entry(0, "b")
    assert field.data == ["b", "a"]
    assert field.pop_entry().data == "a"

def test_default_meta_disables_translations_for_false_locales():
    """Seam: config interaction when Meta.locales=False disables translations."""
    class F(Form):
        class Meta:
            locales = False

        value = StringField()

    assert F().meta.get_translations(F()) is None

def test_default_meta_rejects_plain_mapping_formdata():
    """Seam: error propagation when plain dict formdata is rejected."""
    class F(Form):
        value = StringField()

    with pytest.raises(TypeError):
        F({"value": "x"})

def test_default_meta_accepts_getlist_adapter():
    """Seam: protocol handoff from getlist formdata adapter to field data."""
    class F(Form):
        value = StringField()

    assert F(FormData(value=["x"])).value.data == "x"

def test_invalid_extra_validator_raises_type_error_before_field_validation():
    """Seam: error propagation from invalid extra_validators before validation."""
    called = []

    def declared_validator(form, field):
        called.append(True)

    class F(Form):
        value = StringField(validators=[declared_validator])

    form = F()
    with pytest.raises(TypeError):
        form.validate(extra_validators={"value": [validators.DataRequired]})
    assert called == []

def test_form_data_precedence_beats_object_kwargs_and_data():
    """Seam: config interaction for formdata over object, kwargs, and data."""
    class F(Form):
        value = StringField(default="default")

    obj = type("Obj", (), {"value": "object"})()
    form = F(FormData(value=["submitted"]), obj=obj, data={"value": "data"}, value="kwargs")
    assert form.value.data == "submitted"

def test_populate_obj_overwrites_matching_attribute():
    """Seam: protocol handoff from validated form data to object attribute."""
    class F(Form):
        value = IntegerField()

    obj = type("Obj", (), {"value": 1})()
    form = F(FormData(value=["4"]))
    form.populate_obj(obj)
    assert obj.value == 4

def test_form_field_projects_nested_data_and_errors():
    """Seam: state consistency between FormField nested data and errors."""
    class Inner(Form):
        value = IntegerField(validators=[validators.NumberRange(min=2)])

    class Outer(Form):
        inner = FormField(Inner)

    form = Outer(FormData(**{"inner-value": ["1"]}))
    assert form.validate() is False
    assert form.inner.data == {"value": 1}
    assert form.inner.errors == {"value": form.inner.form.value.errors}
