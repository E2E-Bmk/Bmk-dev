"""Integration tests for schematics.

Each test exercises ≥2 public API boundaries or validates cross-view invariants.
"""
import datetime
import decimal

import pytest

from schematics.models import Model
from schematics.exceptions import (
    ConversionError, DataError, UnknownFieldError, UndefinedValueError, ValidationError,
)
from schematics.transforms import blacklist, whitelist
from schematics.types import (
    BooleanType, DateTimeType, DecimalType, DictType, IntType, ListType,
    ModelType, StringType, UUIDType,
)

from conftest import Child, Record


# ── CVI-1: attribute and mapping read same native value ──────────

@pytest.mark.depends_on("test_model_instance_exposes_converted_field_values")
def test_attribute_and_mapping_read_same_native_value():
    """CVI-1: Seam: state consistency — attribute access ↔ mapping access on same field."""
    item = Record({"name": "Ada", "amount": "4.5"})
    assert item.name == item["name"] == "Ada"
    assert item.amount == decimal.Decimal("4.5")


# ── CVI-2: attribute assignment → mapping + native export ────────

@pytest.mark.depends_on("test_model_instance_exposes_converted_field_values")
def test_attribute_assignment_updates_mapping_and_native_export():
    """CVI-2: Seam: state consistency — attribute assignment ↔ mapping and to_native export."""
    item = Record({"name": "Ada"})
    item.count = 9
    assert item["count"] == 9
    assert item.to_native()["count"] == 9


# ── CVI-3: mapping assignment → attribute + native export ────────

@pytest.mark.depends_on("test_model_instance_exposes_converted_field_values")
def test_mapping_assignment_updates_attribute_and_native_export():
    """CVI-3: Seam: state consistency — mapping assignment ↔ attribute and to_native export."""
    item = Record({"name": "Ada"})
    item["count"] = 8
    assert item.count == 8
    assert item.to_native()["count"] == 8


# ── CVI-4: serialized_name used in export ────────────────────────

@pytest.mark.depends_on("test_model_exports_native_and_primitive_mappings")
def test_export_uses_serialized_field_name():
    """CVI-4: Seam: state consistency — serialized_name ↔ to_native and to_primitive keys."""
    item = Record({"name": "Ada"})
    assert item.to_native()["label"] == "Ada"
    assert item.to_primitive()["label"] == "Ada"


# ── CVI-5: native vs primitive for scalars ────────────────────────

@pytest.mark.depends_on("test_decimal_has_native_decimal_and_primitive_text")
def test_primitive_export_uses_decimal_primitive_value():
    """CVI-5: Seam: state consistency — native Decimal ↔ primitive string export."""
    item = Record({"name": "Ada", "amount": "4.50"})
    assert item.to_native()["amount"] == decimal.Decimal("4.50")
    assert item.to_primitive()["amount"] == "4.50"


# ── CVI-6: nested model instance + export mappings ───────────────

@pytest.mark.depends_on("test_model_instance_exposes_converted_field_values")
def test_modeltype_turns_mapping_into_nested_model():
    """CVI-6: Seam: lifecycle crossing — mapping input ↔ nested ModelType instance."""
    class Parent(Model):
        child = ModelType(Child)

    parent = Parent({"child": {"count": "5"}})
    assert parent.child.count == 5
    assert parent.to_native()["child"] == {"count": 5}


def test_modeltype_accepts_nested_model_instance():
    """CVI-6: Seam: state consistency — nested model instance ↔ ModelType field binding."""
    class Parent(Model):
        child = ModelType(Child)

    child = Child({"count": 5})
    assert Parent({"child": child}).child.count == child.count


def test_modeltype_rejects_non_model_non_mapping_value():
    """CVI-6: Seam: error propagation — invalid ModelType value ↔ DataError."""
    class Parent(Model):
        child = ModelType(Child)

    with pytest.raises(DataError):
        Parent({"child": 3})


# ── CVI-7: role exclusion removes same field from both exports ────

@pytest.mark.depends_on("test_export_uses_serialized_field_name")
def test_whitelist_role_exports_only_named_fields():
    """CVI-7: Seam: config interaction — whitelist role ↔ filtered native and primitive exports."""
    class RoleModel(Record):
        class Options:
            roles = {"public": whitelist("name")}

    item = RoleModel({"name": "Ada", "count": 7})
    assert item.to_native(role="public") == {"label": "Ada"}
    assert item.to_primitive(role="public") == {"label": "Ada"}


def test_blacklist_role_omits_named_field_in_both_views():
    """CVI-7: Seam: config interaction — blacklist role ↔ omitted field in both exports."""
    class RoleModel(Record):
        class Options:
            roles = {"public": blacklist("count")}

    item = RoleModel({"name": "Ada", "count": 7})
    assert "count" not in item.to_native(role="public")
    assert "count" not in item.to_primitive(role="public")


def test_default_role_applies_when_no_role_is_requested():
    """CVI-7: Seam: config interaction — default role ↔ export without explicit role."""
    class RoleModel(Record):
        class Options:
            roles = {"default": whitelist("name")}

    assert RoleModel({"name": "Ada", "count": 7}).to_native() == {"label": "Ada"}


# ── CVI-8: DataError.to_primitive structured error ────────────────

def test_non_partial_validation_reports_missing_required_field():
    """CVI-8: Seam: error propagation — missing required field ↔ DataError.to_primitive structure."""
    with pytest.raises(DataError) as raised:
        Record({"count": 2}, validate=True, partial=False)
    assert raised.value.to_primitive()


def test_validate_reports_nested_field_errors_structurally():
    """CVI-8: Seam: error propagation — nested validation failure ↔ structured DataError."""
    class Parent(Model):
        child = ModelType(Child, required=True)

    with pytest.raises(DataError) as raised:
        Parent({"child": {}}, validate=True, partial=False)
    assert "child" in raised.value.to_primitive()


# ── Validation ────────────────────────────────────────────────────

def test_model_validate_populates_validated_projection():
    """Seam: state consistency — validate() ↔ to_native validated projection."""
    item = Record({"name": "Ada"})
    item.validate()
    assert item.to_native()["label"] == "Ada"


def test_partial_constructor_allows_missing_required_field():
    """Seam: config interaction — partial=True ↔ tolerance for missing required fields."""
    assert Record({"count": 2}, validate=True, partial=True).count == 2


def test_strict_constructor_rejects_unknown_input_key():
    """Seam: error propagation — unknown input key ↔ DataError on construction."""
    with pytest.raises(DataError):
        Record({"name": "Ada", "extra": 1}, validate=True)


# ── Error paths ──────────────────────────────────────────────────

def test_unknown_mapping_assignment_raises_documented_error():
    """Seam: error propagation — unknown field assignment ↔ UnknownFieldError."""
    item = Record({"name": "Ada"})
    with pytest.raises(UnknownFieldError):
        item["extra"] = 1


# ── Field naming: serialized_name + deserialize_from ──────────────

@pytest.mark.depends_on("test_export_uses_serialized_field_name")
def test_declared_input_key_wins_over_alternate_keys():
    """Seam: config interaction — declared field key ↔ deserialize precedence over aliases."""
    class Aliased(Model):
        title = StringType(serialized_name="label", deserialize_from="legacy")

    assert Aliased({"title": "declared", "label": "serialized", "legacy": "old"}).title == "declared"


def test_serialized_input_key_wins_over_deserialize_from_key():
    """Seam: config interaction — serialized_name key ↔ precedence over deserialize_from."""
    class Aliased(Model):
        title = StringType(serialized_name="label", deserialize_from="legacy")

    assert Aliased({"label": "serialized", "legacy": "old"}).title == "serialized"


# ── Defaults ──────────────────────────────────────────────────────

def test_literal_default_is_available_in_native_export():
    """Seam: state consistency — literal field default ↔ to_native export value."""
    assert Record({"name": "Ada"}).to_native()["count"] == 3


def test_callable_default_is_evaluated_for_each_model():
    """Seam: lifecycle crossing — callable default ↔ per-instance evaluation."""
    class WithDefault(Model):
        value = IntType(default=lambda: 4)

    assert WithDefault().value == 4


# ── import_data ──────────────────────────────────────────────────

@pytest.mark.depends_on("test_model_instance_exposes_converted_field_values")
def test_import_data_updates_and_returns_same_instance():
    """Seam: state consistency — import_data mutation ↔ same model instance identity."""
    item = Record({"name": "Ada"})
    assert item.import_data({"count": "6"}) is item
    assert item.count == 6


# ── serialize ─────────────────────────────────────────────────────

def test_serialize_returns_primitive_mapping():
    """Seam: state consistency — serialize() ↔ to_primitive mapping agreement."""
    item = Record({"name": "Ada", "count": "3"})
    assert item.serialize()["count"] == 3


# ── List of models ───────────────────────────────────────────────

@pytest.mark.depends_on("test_modeltype_turns_mapping_into_nested_model")
def test_list_of_models_exports_nested_primitive_mapping():
    """Seam: state consistency — ListType(ModelType) ↔ nested primitive export."""
    class Parent(Model):
        children = ListType(ModelType(Child))

    assert Parent({"children": [{"count": "2"}]}).to_primitive() == {"children": [{"count": 2}]}


# ── Representative workflow: full lifecycle ──────────────────────

def test_representative_workflow_binds_instance_native_and_primitive():
    """Seam: state consistency — validated instance ↔ native and primitive export agreement."""
    class Reading(Model):
        city = StringType(required=True)
        temperature = DecimalType()
        taken_at = DateTimeType()

    reading = Reading({"city": "NYC", "temperature": "18.50", "taken_at": "2024-01-02T03:04:05"})
    reading.validate()
    assert reading.city == reading["city"] == "NYC"
    assert reading.to_native()["temperature"] == decimal.Decimal("18.50")
    assert reading.to_primitive()["temperature"] == "18.50"


def test_representative_workflow_applies_role_to_both_exports():
    """Seam: config interaction — public role ↔ consistent native and primitive filtering."""
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
    """Seam: lifecycle crossing — nested validation ↔ nested export state consistency."""
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
    """Seam: error propagation — validation failure recovery ↔ import_data and re-validate."""
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
