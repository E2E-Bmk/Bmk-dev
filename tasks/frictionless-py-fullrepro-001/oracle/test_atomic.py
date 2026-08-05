from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import json

import pytest

from frictionless import (
    Analyzer,
    Detector,
    Field,
    Package,
    Pipeline,
    Report,
    Resource,
    Schema,
    describe,
    extract,
    list as list_resources,
    transform,
    validate,
)
from frictionless import fields, steps

from conftest import (
    VALID_CSV,
    local_csv,
    normalized_rows,
    report_projection,
    rows_as_dicts,
    simple_schema,
    typed_inline_resource,
    valid_resource_with_schema,
)


def test_public_imports_expose_core_types():
    assert Resource.__name__ == "Resource"
    assert Package.__name__ == "Package"
    assert Schema.__name__ == "Schema"
    assert Field.__name__ == "Field"
    assert Detector.__name__ == "Detector"
    assert Analyzer.__name__ == "Analyzer"
    assert Report.__name__ == "Report"
    assert callable(describe)
    assert callable(extract)
    assert callable(list_resources)
    assert callable(transform)
    assert callable(validate)


def test_resource_inline_descriptor_is_canonical():
    descriptor = typed_inline_resource().to_descriptor()
    assert descriptor["name"] == "scores"
    assert descriptor["type"] == "table"
    assert descriptor["format"] == "inline"
    assert descriptor["data"][0] == ["id", "name", "score"]


def test_resource_inline_rows_cast_to_declared_schema():
    rows = rows_as_dicts(valid_resource_with_schema())
    assert rows == [
        {"id": 1, "name": "Ada", "score": Decimal("2.5")},
        {"id": 2, "name": "Bob", "score": Decimal("3.0")},
    ]


def test_integer_field_casts_and_writes_public_values():
    field = fields.IntegerField(name="id")
    assert field.read_cell(" 7 ") == (7, None)
    assert field.read_cell("bad")[0] is None
    assert field.write_cell(7) == ("7", None)


def test_number_field_supports_decimal_and_float_modes():
    decimal_field = fields.NumberField(name="amount")
    float_field = fields.NumberField(name="amount", float_number=True)
    decimal_value, decimal_notes = decimal_field.read_cell("2.50")
    float_value, float_notes = float_field.read_cell("2.50")
    assert decimal_value == Decimal("2.50")
    assert isinstance(float_value, float)
    assert decimal_notes is None
    assert float_notes is None


def test_boolean_field_accepts_custom_true_and_false_values():
    field = fields.BooleanField(
        name="enabled",
        true_values=["yes"],
        false_values=["no"],
    )
    assert field.read_cell("yes") == (True, None)
    assert field.read_cell("no") == (False, None)
    assert field.write_cell(True) == ("yes", None)


def test_date_and_datetime_fields_cast_iso_values():
    day = fields.DateField(name="day")
    moment = fields.DatetimeField(name="moment")
    assert day.read_cell("2024-01-02") == (date(2024, 1, 2), None)
    value, notes = moment.read_cell("2024-01-02T03:04:05+00:00")
    assert value == datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert notes is None


def test_array_and_object_fields_parse_json_cells():
    array = fields.ArrayField(name="items")
    obj = fields.ObjectField(name="attributes")
    assert array.read_cell("[1, 2]") == ([1, 2], None)
    assert obj.read_cell('{"kind": "sample"}') == ({"kind": "sample"}, None)


def test_field_constraints_return_structured_notes():
    field = fields.StringField(name="name", constraints={"minLength": 3})
    value, notes = field.read_cell("Al")
    assert value == "Al"
    assert notes is not None
    assert "minLength" in notes


def test_schema_field_management_and_cell_projection():
    schema = simple_schema()
    assert schema.field_names == ["id", "name", "score"]
    schema.add_field(fields.BooleanField(name="active"))
    assert schema.has_field("active")
    schema.set_field_type("name", "any")
    assert schema.get_field("name").type == "any"
    removed = schema.remove_field("active")
    assert removed.name == "active"
    cells, notes = schema.read_cells(["4", "Dana", "3.5"])
    assert cells == [4, "Dana", Decimal("3.5")]
    assert notes == [None, None, None]


def test_detector_options_are_public_and_configurable():
    detector = Detector(
        sample_size=7,
        buffer_size=31,
        field_confidence=1,
        field_float_numbers=True,
        field_missing_values=["", "na"],
    )
    assert detector.sample_size == 7
    assert detector.buffer_size == 31
    assert detector.field_confidence == 1
    assert detector.field_float_numbers is True
    assert detector.field_missing_values == ["", "na"]


def test_detector_field_names_control_described_schema(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(
        tmp_path,
        monkeypatch,
        content="first,second\n1,2\n",
    )
    resource = describe(filename, detector=Detector(field_names=["left", "right"]))
    assert resource.schema.field_names == ["left", "right"]


def test_resource_descriptor_json_round_trip():
    original = typed_inline_resource()
    restored = Resource.from_descriptor(json.loads(original.to_json()))
    assert restored.to_descriptor() == original.to_descriptor()


def test_resource_descriptor_yaml_round_trip(tmp_path):
    original = typed_inline_resource()
    path = tmp_path / "resource.yaml"
    original.to_yaml(str(path))
    restored = Resource.from_descriptor(str(path))
    assert restored.to_descriptor() == original.to_descriptor()


def test_package_descriptor_manages_named_resources():
    package = Package(
        name="bundle",
        resources=[
            Resource(name="first", data=[["id"], [1]]),
            Resource(name="second", data=[["id"], [2]]),
        ],
    )
    assert package.resource_names == ["first", "second"]
    assert package.has_resource("first")
    assert package.get_resource("second").name == "second"
    removed = package.remove_resource("first")
    assert removed.name == "first"
    assert package.resource_names == ["second"]


def test_package_descriptor_json_round_trip():
    original = Package(
        name="bundle",
        resources=[Resource(name="first", data=[["id"], [1]])],
    )
    restored = Package.from_descriptor(json.loads(original.to_json()))
    assert restored.to_descriptor() == original.to_descriptor()


def test_package_descriptor_yaml_round_trip(tmp_path):
    original = Package(
        name="bundle",
        resources=[Resource(name="first", data=[["id"], [1]])],
    )
    path = tmp_path / "package.yaml"
    original.to_yaml(str(path))
    restored = Package.from_descriptor(str(path))
    assert restored.to_descriptor() == original.to_descriptor()


def test_describe_infers_csv_schema(tmp_path, monkeypatch):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    resource = describe(filename)
    assert resource.schema.field_names == ["id", "name", "active", "score"]
    assert resource.schema.field_types == ["integer", "string", "boolean", "number"]


def test_extract_returns_named_rows_with_cast_values(tmp_path, monkeypatch):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    result = extract(filename, limit_rows=2)
    assert list(result) == ["table"]
    assert result["table"][0]["id"] == 1
    assert result["table"][0]["active"] is True
    assert str(result["table"][1]["score"]) == "3.0"


def test_validate_valid_inline_resource_has_clean_report():
    projection = report_projection(validate(valid_resource_with_schema()))
    assert projection["valid"] is True
    assert projection["stats"] == {"tasks": 1, "errors": 0, "warnings": 0}
    assert projection["tasks"][0]["stats"]["rows"] == 2


def test_validate_invalid_rows_exposes_structured_error():
    resource = Resource(
        name="broken",
        data=[["id"], ["not-an-integer"]],
        schema=Schema.from_descriptor(
            {"fields": [{"name": "id", "type": "integer"}]}
        ),
    )
    projection = report_projection(validate(resource))
    errors = projection["tasks"][0]["errors"]
    assert projection["valid"] is False
    assert projection["stats"]["errors"] == 1
    assert errors[0]["type"] == "type-error"
    assert errors[0]["fieldName"] == "id"
    assert errors[0]["rowNumber"] == 2


def test_report_flatten_exposes_structured_error_columns():
    resource = Resource(
        name="broken",
        data=[["id"], ["bad"]],
        schema=Schema.from_descriptor(
            {"fields": [{"name": "id", "type": "integer"}]}
        ),
    )
    flattened = validate(resource).flatten(["rowNumber", "fieldName", "type"])
    assert flattened == [[2, "id", "type-error"]]


def test_analyzer_summary_reports_rows_and_fields():
    analysis = typed_inline_resource().analyze()
    assert analysis["rows"] == 2
    assert analysis["fields"] == 3
    assert analysis["notNullRows"] == 2
    assert analysis["rowsWithNullValues"] == 0
    assert "timeTaken" in analysis


def test_analyzer_detailed_reports_variable_types_and_field_stats():
    analysis = typed_inline_resource().analyze(detailed=True)
    assert analysis["variableTypes"] == {
        "integer": 1,
        "string": 1,
        "number": 1,
    }
    assert analysis["fieldStats"]["id"]["type"] == "numeric"
    assert analysis["fieldStats"]["name"]["type"] == "categorical"
    assert analysis["fieldStats"]["score"]["uniqueValues"] == 2


def test_pipeline_descriptor_round_trip_preserves_step_types():
    pipeline = Pipeline(
        steps=[
            steps.table_normalize(),
            steps.field_add(name="tag", value="x"),
        ]
    )
    restored = Pipeline.from_descriptor(pipeline.to_descriptor())
    assert restored.step_types == ["table-normalize", "field-add"]
    assert restored.to_descriptor() == pipeline.to_descriptor()


def test_transform_action_adds_a_field():
    target = transform(
        typed_inline_resource(),
        steps=[steps.field_add(name="tag", value="x")],
    )
    rows = normalized_rows(target)
    assert target.schema.field_names == ["id", "name", "score", "tag"]
    assert [row["tag"] for row in rows] == ["x", "x"]


def test_transform_action_filters_rows():
    target = transform(
        typed_inline_resource(),
        steps=[steps.row_filter(formula="id > 1")],
    )
    assert [row["id"] for row in rows_as_dicts(target)] == [2]


def test_transform_action_normalizes_string_cells():
    resource = Resource(data=[["id", "score"], ["1", "2.5"]], name="raw")
    target = transform(resource, steps=[steps.table_normalize()])
    rows = rows_as_dicts(target)
    assert rows == [{"id": 1, "score": Decimal("2.5")}]


def test_list_action_returns_local_resource(tmp_path, monkeypatch):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    resources = list_resources(filename)
    assert len(resources) == 1
    assert resources[0].name == "table"
    assert resources[0].format == "csv"


def test_package_extract_applies_name_and_limit():
    package = Package(
        resources=[
            Resource(name="first", data=[["id"], [1], [2]]),
            Resource(name="second", data=[["id"], [3], [4]]),
        ]
    )
    extracted = package.extract(name="second", limit_rows=1)
    assert extracted == {"second": [{"id": 3}]}


def test_schema_constraints_are_preserved_in_descriptor():
    schema = Schema.from_descriptor(
        {
            "fields": [
                {
                    "name": "name",
                    "type": "string",
                    "constraints": {"required": True, "minLength": 2},
                }
            ],
            "primaryKey": ["name"],
        }
    )
    descriptor = schema.to_descriptor()
    assert descriptor["fields"][0]["constraints"] == {
        "required": True,
        "minLength": 2,
    }
    assert descriptor["primaryKey"] == ["name"]


def test_resource_copy_preserves_descriptor_and_rows():
    original = valid_resource_with_schema()
    copied = original.to_copy()
    assert copied is not original
    assert copied.to_descriptor() == original.to_descriptor()
    assert rows_as_dicts(copied) == rows_as_dicts(original)
