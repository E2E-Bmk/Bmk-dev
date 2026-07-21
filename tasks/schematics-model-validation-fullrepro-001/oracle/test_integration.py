"""Integration and end-to-end public-behavior conformance checks."""

# Spec2Repo oracle candidates rewritten from upstream public-behavior tests.
import datetime
import decimal
import uuid

import pytest

from schematics import Model
from schematics.exceptions import ConversionError, DataError, UnknownFieldError, ValidationError
from schematics.transforms import blacklist, whitelist
from schematics.types import (
    BooleanType, DateTimeType, DateType, DecimalType, DictType, EmailType,
    GeoPointType, IntType, IPv4Type, ListType, MD5Type, ModelType,
    StringType, TimedeltaType, UUIDType, URLType,
)


class Child(Model):
    count = IntType(required=True)


class Record(Model):
    name = StringType(required=True, serialized_name="label")
    count = IntType(default=3)
    amount = DecimalType()

def test_product_state_workflow_binds_instance_native_and_primitive_views():
    class Reading(Model):
        city = StringType(required=True)
        temperature = DecimalType()
        taken_at = DateTimeType()

    reading = Reading({"city": "NYC", "temperature": "18.50", "taken_at": "2024-01-02T03:04:05"})
    reading.validate()
    assert reading.city == reading["city"] == "NYC"
    assert reading.to_native()["temperature"] == decimal.Decimal("18.50")
    assert reading.to_primitive()["temperature"] == "18.50"

def test_representative_workflow_applies_role_to_both_export_views():
    class Report(Model):
        city = StringType(required=True)
        temperature = DecimalType()
        internal_note = StringType()

        class Options:
            roles = {"public": whitelist("city", "temperature")}

    report = Report({"city": "NYC", "temperature": "18.50", "internal_note": "calibrated"})
    report.validate()
    native = report.to_native(role="public")
    primitive = report.to_primitive(role="public")
    assert native == {"city": "NYC", "temperature": decimal.Decimal("18.50")}
    assert primitive == {"city": "NYC", "temperature": "18.50"}

def test_representative_workflow_exports_nested_state_after_validation():
    class Place(Model):
        name = StringType(required=True)

    class Visit(Model):
        place = ModelType(Place, required=True)
        readings = ListType(IntType())

    visit = Visit({"place": {"name": "station"}, "readings": ["1", 2]})
    visit.validate()
    assert visit.place.name == "station"
    assert visit.to_native()["place"] == {"name": "station"}
    assert visit.to_primitive() == {"place": {"name": "station"}, "readings": [1, 2]}

def test_representative_workflow_recovers_after_structured_validation_failure():
    class Request(Model):
        city = StringType(required=True)
        retries = IntType(default=0)

    with pytest.raises(DataError) as raised:
        Request({"retries": "1"}, validate=True, partial=False)
    assert raised.value.to_primitive()

    request = Request({"city": "NYC"})
    assert request.import_data({"retries": "2"}) is request
    request.validate()
    assert request.retries == request["retries"] == 2
    assert request.to_primitive()["retries"] == 2

def test_attribute_and_mapping_read_same_native_value():
    item = Record({"name": "Ada", "amount": "4.5"})
    assert item.name == item["name"] == "Ada"
    assert item.amount == decimal.Decimal("4.5")

def test_attribute_assignment_updates_mapping_and_native_export():
    item = Record({"name": "Ada"})
    item.count = 9
    assert item["count"] == 9
    assert item.to_native()["count"] == 9

def test_blacklist_role_omits_named_field_in_both_views():
    class RoleModel(Record):
        class Options:
            roles = {"public": blacklist("count")}
    item = RoleModel({"name": "Ada", "count": 7})
    assert "count" not in item.to_native(role="public")
    assert "count" not in item.to_primitive(role="public")

def test_boolean_accepts_numeric_true_value():
    assert BooleanType().to_native(1) is True

def test_callable_default_is_evaluated_for_each_model():
    class WithDefault(Model):
        value = IntType(default=lambda: 4)
    assert WithDefault().value == 4

def test_date_rejects_unparseable_value():
    with pytest.raises(ConversionError):
        DateType().to_native("not-a-date")

def test_declared_input_key_wins_over_alternate_keys():
    class Aliased(Model):
        title = StringType(serialized_name="label", deserialize_from="legacy")
    assert Aliased({"title": "declared", "label": "serialized", "legacy": "old"}).title == "declared"

def test_default_role_applies_when_no_role_is_requested():
    class RoleModel(Record):
        class Options:
            roles = {"default": whitelist("name")}
    assert RoleModel({"name": "Ada", "count": 7}).to_native() == {"label": "Ada"}

def test_export_uses_serialized_field_name():
    item = Record({"name": "Ada"})
    assert item.to_native()["label"] == "Ada"
    assert item.to_primitive()["label"] == "Ada"

def test_import_data_updates_and_returns_same_instance():
    item = Record({"name": "Ada"})
    assert item.import_data({"count": "6"}) is item
    assert item.count == 6

def test_list_of_models_exports_nested_primitive_mapping():
    class Parent(Model):
        children = ListType(ModelType(Child))
    assert Parent({"children": [{"count": "2"}]}).to_primitive() == {"children": [{"count": 2}]}

def test_literal_default_is_available_in_native_export():
    assert Record({"name": "Ada"}).to_native()["count"] == 3

def test_mapping_assignment_updates_attribute_and_native_export():
    item = Record({"name": "Ada"})
    item["count"] = 8
    assert item.count == 8
    assert item.to_native()["count"] == 8

def test_model_validate_returns_instance_when_valid():
    item = Record({"name": "Ada"})
    item.validate()
    assert item.to_native()["label"] == "Ada"

def test_modeltype_accepts_nested_model_instance():
    class Parent(Model):
        child = ModelType(Child)
    child = Child({"count": 5})
    assert Parent({"child": child}).child.count == child.count

def test_modeltype_rejects_non_model_non_mapping_value():
    class Parent(Model):
        child = ModelType(Child)
    with pytest.raises(DataError):
        Parent({"child": 3})

def test_modeltype_turns_mapping_into_nested_model():
    class Parent(Model):
        child = ModelType(Child)
    parent = Parent({"child": {"count": "5"}})
    assert parent.child.count == 5
    assert parent.to_native()["child"] == {"count": 5}

def test_non_partial_validation_reports_missing_required_field():
    with pytest.raises(DataError) as raised:
        Record({"count": 2}, validate=True, partial=False)
    assert raised.value.to_primitive()

def test_partial_constructor_allows_missing_required_field():
    assert Record({"count": 2}, validate=True, partial=True).count == 2

def test_primitive_export_is_mapping_with_scalar_values():
    item = Record({"name": "Ada", "count": "3"})
    assert item.serialize()["count"] == 3

def test_primitive_export_uses_decimal_primitive_value():
    item = Record({"name": "Ada", "amount": "4.50"})
    assert item.to_native()["amount"] == decimal.Decimal("4.50")
    assert item.to_primitive()["amount"] == "4.50"

def test_serialized_input_key_wins_over_deserialize_from_key():
    class Aliased(Model):
        title = StringType(serialized_name="label", deserialize_from="legacy")
    assert Aliased({"label": "serialized", "legacy": "old"}).title == "serialized"

def test_strict_constructor_rejects_unknown_input_key():
    with pytest.raises(DataError):
        Record({"name": "Ada", "extra": 1}, validate=True)

def test_unknown_mapping_assignment_raises_documented_error():
    item = Record({"name": "Ada"})
    with pytest.raises(UnknownFieldError):
        item["extra"] = 1

def test_validate_reports_nested_field_errors_structurally():
    class Parent(Model):
        child = ModelType(Child, required=True)
    with pytest.raises(DataError) as raised:
        Parent({"child": {}}, validate=True, partial=False)
    assert "child" in raised.value.to_primitive()

def test_whitelist_role_exports_only_named_field_in_both_views():
    class RoleModel(Record):
        class Options:
            roles = {"public": whitelist("name")}
    item = RoleModel({"name": "Ada", "count": 7})
    assert item.to_native(role="public") == {"label": "Ada"}
    assert item.to_primitive(role="public") == {"label": "Ada"}
