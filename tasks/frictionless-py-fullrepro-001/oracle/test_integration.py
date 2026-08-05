from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path

import pytest
import yaml

from frictionless import (
    Detector,
    Dialect,
    Package,
    Pipeline,
    Resource,
    Schema,
    describe,
    extract,
    transform,
    validate,
)
from frictionless import fields, steps

from conftest import (
    INVALID_CSV,
    VALID_CSV,
    local_csv,
    normalized_rows,
    report_projection,
    rows_as_dicts,
    simple_schema,
    typed_inline_resource,
    valid_resource_with_schema,
    write_json,
    write_local,
)


@pytest.mark.depends_on(
    "test_resource_inline_descriptor_is_canonical",
    "test_resource_inline_rows_cast_to_declared_schema",
)
def test_inline_descriptor_round_trip_preserves_cast_rows():
    original = valid_resource_with_schema()
    restored = Resource.from_descriptor(original.to_descriptor())
    assert restored.to_descriptor() == original.to_descriptor()
    assert rows_as_dicts(restored) == rows_as_dicts(original)


@pytest.mark.depends_on(
    "test_resource_descriptor_json_round_trip",
    "test_resource_descriptor_yaml_round_trip",
)
def test_local_json_and_yaml_data_resources_preserve_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_json(tmp_path, "records.json", [{"id": 1, "name": "Ada"}])
    (tmp_path / "records.yaml").write_text(
        "- id: 1\n  name: Ada\n",
        encoding="utf-8",
    )
    json_resource = Resource("records.json")
    yaml_resource = Resource("records.yaml")
    assert json_resource.read_json() == [{"id": 1, "name": "Ada"}]
    assert yaml_resource.read_json() == [{"id": 1, "name": "Ada"}]
    assert json_resource.to_descriptor()["format"] == "json"
    assert yaml_resource.to_descriptor()["format"] == "yaml"


@pytest.mark.depends_on(
    "test_describe_infers_csv_schema",
    "test_extract_returns_named_rows_with_cast_values",
)
def test_describe_and_extract_share_a_csv_schema_projection(tmp_path, monkeypatch):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    described = describe(filename)
    extracted = extract(filename)
    assert described.schema.field_names == list(extracted["table"][0])
    assert described.schema.field_types == ["integer", "string", "boolean", "number"]
    assert extracted["table"][2]["id"] == 3


@pytest.mark.depends_on(
    "test_validate_valid_inline_resource_has_clean_report",
    "test_report_flatten_exposes_structured_error_columns",
)
def test_valid_csv_validation_has_stable_structured_report(tmp_path, monkeypatch):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    projection = report_projection(validate(filename))
    assert projection["valid"] is True
    assert projection["stats"] == {"tasks": 1, "errors": 0, "warnings": 0}
    assert projection["tasks"][0]["name"] == "table"
    assert projection["tasks"][0]["stats"]["rows"] == 3


@pytest.mark.depends_on(
    "test_validate_invalid_rows_exposes_structured_error",
    "test_report_flatten_exposes_structured_error_columns",
)
def test_invalid_csv_validation_projects_type_error_coordinates(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=INVALID_CSV)
    resource = Resource(path=filename, schema=simple_schema())
    projection = report_projection(resource.validate())
    errors = projection["tasks"][0]["errors"]
    assert projection["valid"] is False
    assert projection["stats"]["errors"] == 2
    assert errors[0]["type"] == "type-error"
    assert errors[0]["fieldName"] in {"id", "score"}
    assert errors[0]["rowNumber"] == 3


@pytest.mark.depends_on(
    "test_detector_field_names_control_described_schema",
    "test_describe_infers_csv_schema",
)
def test_detector_field_names_and_field_type_compose_on_local_csv(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(
        tmp_path,
        monkeypatch,
        content="first,second\n1,2\n",
    )
    detector = Detector(field_names=["left", "right"], field_type="string")
    resource = describe(filename, detector=detector)
    assert resource.schema.field_names == ["left", "right"]
    assert resource.schema.field_types == ["string", "string"]
    assert rows_as_dicts(resource) == [{"left": "1", "right": "2"}]


@pytest.mark.depends_on(
    "test_detector_options_are_public_and_configurable",
    "test_describe_infers_csv_schema",
)
def test_custom_csv_dialect_drives_describe_extract_and_validate(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(
        tmp_path,
        monkeypatch,
        content="id;name\n1;Ada\n2;Bob\n",
    )
    dialect = Dialect.from_descriptor({"csv": {"delimiter": ";"}})
    resource = describe(filename, dialect=dialect)
    assert resource.dialect.to_descriptor() == {"csv": {"delimiter": ";"}}
    assert extract(filename, dialect=dialect)["table"][1]["name"] == "Bob"
    assert validate(filename, dialect=dialect).valid is True


@pytest.mark.depends_on(
    "test_detector_options_are_public_and_configurable",
    "test_describe_infers_csv_schema",
)
def test_detector_missing_values_flow_into_rows_and_schema(tmp_path, monkeypatch):
    filename = local_csv(
        tmp_path,
        monkeypatch,
        content="id,name\n1,na\n2,\n",
    )
    resource = describe(
        filename,
        detector=Detector(field_missing_values=["", "na"]),
    )
    assert resource.schema.missing_values == ["", "na"]
    assert rows_as_dicts(resource) == [
        {"id": 1, "name": None},
        {"id": 2, "name": None},
    ]


@pytest.mark.depends_on(
    "test_field_constraints_return_structured_notes",
    "test_validate_invalid_rows_exposes_structured_error",
)
def test_schema_constraints_produce_validation_errors_with_coordinates():
    schema = Schema(
        fields=[
            fields.StringField(
                name="name",
                constraints={"required": True, "minLength": 3},
            )
        ]
    )
    resource = Resource(name="constrained", data=[["name"], ["Al"]], schema=schema)
    projection = report_projection(resource.validate())
    assert projection["valid"] is False
    assert projection["tasks"][0]["errors"][0]["type"] == "constraint-error"
    assert projection["tasks"][0]["errors"][0]["fieldName"] == "name"
    assert projection["tasks"][0]["errors"][0]["rowNumber"] == 2


@pytest.mark.depends_on(
    "test_schema_constraints_are_preserved_in_descriptor",
    "test_validate_invalid_rows_exposes_structured_error",
)
def test_primary_key_validation_reports_duplicate_row_structure():
    schema = Schema.from_descriptor(
        {
            "fields": [{"name": "id", "type": "integer"}],
            "primaryKey": ["id"],
        }
    )
    resource = Resource(name="duplicates", data=[["id"], [1], [1]], schema=schema)
    projection = report_projection(resource.validate())
    assert projection["valid"] is False
    error = projection["tasks"][0]["errors"][0]
    assert error["type"] == "primary-key"
    assert error["rowNumber"] == 3


@pytest.mark.depends_on(
    "test_resource_descriptor_json_round_trip",
    "test_describe_infers_csv_schema",
)
def test_resource_json_descriptor_round_trip_reopens_local_csv(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    (tmp_path / filename).write_text(
        "id,name,score\n1,Ada,2.5\n2,Bob,3.0\n",
        encoding="utf-8",
    )
    descriptor_name = write_json(
        tmp_path,
        "resource.json",
        {
            "name": "table",
            "path": filename,
            "schema": simple_schema().to_descriptor(),
        },
    )
    restored = Resource.from_descriptor(descriptor_name)
    assert restored.to_descriptor()["path"] == filename
    assert rows_as_dicts(restored)[:2] == [
        {"id": 1, "name": "Ada", "score": Decimal("2.5")},
        {"id": 2, "name": "Bob", "score": Decimal("3.0")},
    ]


@pytest.mark.depends_on(
    "test_resource_descriptor_yaml_round_trip",
    "test_describe_infers_csv_schema",
)
def test_resource_yaml_descriptor_round_trip_reopens_local_csv(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    (tmp_path / filename).write_text(
        "id,name,score\n1,Ada,2.5\n2,Bob,3.0\n",
        encoding="utf-8",
    )
    resource = Resource(
        name="table",
        path=filename,
        schema=simple_schema(),
    )
    descriptor_name = "resource.yaml"
    resource.to_yaml(descriptor_name)
    restored = Resource.from_descriptor(descriptor_name)
    assert restored.to_descriptor() == resource.to_descriptor()
    assert rows_as_dicts(restored)[0]["name"] == "Ada"


@pytest.mark.depends_on(
    "test_package_descriptor_manages_named_resources",
    "test_extract_returns_named_rows_with_cast_values",
)
def test_package_local_resources_extract_by_name_after_management(
    tmp_path,
    monkeypatch,
):
    first = local_csv(
        tmp_path,
        monkeypatch,
        filename="first.csv",
        content="id,name\n1,Ada\n",
    )
    second = write_json(tmp_path, "second.json", [{"id": 2, "name": "Bob"}])
    package = Package(
        name="bundle",
        resources=[
            Resource(name="first", path=first),
            Resource(name="second", path=second),
        ],
    )
    package.set_resource(Resource(name="first", path=first))
    assert package.resource_names == ["first", "second"]
    extracted = package.extract(name="first")
    assert extracted["first"][0]["name"] == "Ada"


@pytest.mark.depends_on(
    "test_package_descriptor_json_round_trip",
    "test_resource_descriptor_json_round_trip",
)
def test_package_json_descriptor_round_trip_reopens_csv_resource(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    (tmp_path / filename).write_text(
        "id,name,score\n1,Ada,2.5\n2,Bob,3.0\n",
        encoding="utf-8",
    )
    package = Package(
        name="bundle",
        resources=[Resource(name="table", path=filename, schema=simple_schema())],
    )
    package.to_json("datapackage.json")
    restored = Package.from_descriptor("datapackage.json")
    assert restored.to_descriptor() == package.to_descriptor()
    assert restored.extract()["table"][0]["id"] == 1


@pytest.mark.depends_on(
    "test_package_descriptor_yaml_round_trip",
    "test_resource_descriptor_yaml_round_trip",
)
def test_package_yaml_descriptor_round_trip_reopens_csv_resource(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    (tmp_path / filename).write_text(
        "id,name,score\n1,Ada,2.5\n2,Bob,3.0\n",
        encoding="utf-8",
    )
    package = Package(
        name="bundle",
        resources=[Resource(name="table", path=filename, schema=simple_schema())],
    )
    package.to_yaml("datapackage.yaml")
    restored = Package.from_descriptor("datapackage.yaml")
    assert restored.to_descriptor() == package.to_descriptor()
    assert restored.extract()["table"][1]["name"] == "Bob"


@pytest.mark.depends_on(
    "test_package_descriptor_manages_named_resources",
    "test_validate_valid_inline_resource_has_clean_report",
)
def test_package_validation_aggregates_two_local_resource_tasks(
    tmp_path,
    monkeypatch,
):
    first = local_csv(
        tmp_path,
        monkeypatch,
        filename="first.csv",
        content="id\n1\n",
    )
    second = write_local(tmp_path, "second.csv", "id\n2\n")
    package = Package(
        name="bundle",
        resources=[
            Resource(name="first", path=first),
            Resource(name="second", path=second),
        ],
    )
    projection = report_projection(package.validate())
    assert projection["valid"] is True
    assert projection["stats"]["tasks"] == 2
    assert [task["name"] for task in projection["tasks"]] == ["first", "second"]


@pytest.mark.depends_on(
    "test_package_extract_applies_name_and_limit",
    "test_extract_returns_named_rows_with_cast_values",
)
def test_package_extract_supports_all_resources_name_and_limit():
    package = Package(
        resources=[
            Resource(name="first", data=[["id"], [1], [2]]),
            Resource(name="second", data=[["id"], [3], [4]]),
        ]
    )
    assert set(package.extract()) == {"first", "second"}
    assert package.extract(name="first")["first"] == [{"id": 1}, {"id": 2}]
    assert package.extract(limit_rows=1) == {
        "first": [{"id": 1}],
        "second": [{"id": 3}],
    }


@pytest.mark.depends_on(
    "test_analyzer_summary_reports_rows_and_fields",
    "test_describe_infers_csv_schema",
)
def test_csv_analysis_matches_described_resource_shape(tmp_path, monkeypatch):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    resource = describe(filename)
    analysis = resource.analyze()
    assert analysis["rows"] == 3
    assert analysis["fields"] == 4
    assert analysis["notNullRows"] == 3
    assert analysis["rowsWithNullValues"] == 0


@pytest.mark.depends_on(
    "test_analyzer_detailed_reports_variable_types_and_field_stats",
    "test_describe_infers_csv_schema",
)
def test_detailed_csv_analysis_projects_numeric_and_categorical_fields(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    analysis = describe(filename).analyze(detailed=True)
    assert analysis["variableTypes"] == {
        "integer": 1,
        "string": 1,
        "boolean": 1,
        "number": 1,
    }
    assert analysis["fieldStats"]["name"]["type"] == "categorical"
    assert analysis["fieldStats"]["score"]["type"] == "numeric"
    assert analysis["fieldStats"]["score"]["uniqueValues"] == 3


@pytest.mark.depends_on(
    "test_describe_infers_csv_schema",
    "test_package_descriptor_manages_named_resources",
)
def test_describe_can_build_a_package_from_two_local_csv_files(
    tmp_path,
    monkeypatch,
):
    first = local_csv(
        tmp_path,
        monkeypatch,
        filename="first.csv",
        content="id\n1\n",
    )
    second = "second.csv"
    (tmp_path / second).write_text("id\n2\n", encoding="utf-8")
    package = describe([first, second], type="package")
    assert package.resource_names == ["first", "second"]
    assert [resource.schema.field_names for resource in package.resources] == [
        ["id"],
        ["id"],
    ]


@pytest.mark.depends_on(
    "test_extract_returns_named_rows_with_cast_values",
    "test_detector_field_names_control_described_schema",
)
def test_extract_action_composes_filter_and_process_callbacks(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    result = extract(
        filename,
        filter=lambda row: row["active"],
        process=lambda row: {"id": row["id"], "label": row["name"].upper()},
    )
    assert result == {
        "table": [
            {"id": 1, "label": "ADA"},
            {"id": 3, "label": "CLEO"},
        ]
    }


@pytest.mark.depends_on(
    "test_validate_invalid_rows_exposes_structured_error",
    "test_report_flatten_exposes_structured_error_columns",
)
def test_validate_action_applies_explicit_schema_and_error_filter(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=INVALID_CSV)
    report = validate(
        filename,
        schema=simple_schema(),
        pick_errors=["type-error"],
    )
    projection = report_projection(report)
    assert projection["valid"] is False
    assert projection["stats"]["errors"] == 2
    assert all(
        error["type"] == "type-error"
        for error in projection["tasks"][0]["errors"]
    )


@pytest.mark.depends_on(
    "test_transform_action_adds_a_field",
    "test_transform_action_filters_rows",
)
def test_transform_pipeline_composes_field_add_and_row_filter():
    pipeline = Pipeline(
        steps=[
            steps.field_add(name="bucket", value="selected"),
            steps.row_filter(formula="id > 1"),
        ]
    )
    target = transform(typed_inline_resource(), pipeline=pipeline)
    assert normalized_rows(target) == [
        {"id": 2, "name": "Bob", "score": "3.0", "bucket": "selected"}
    ]


@pytest.mark.depends_on(
    "test_transform_action_filters_rows",
    "test_pipeline_descriptor_round_trip_preserves_step_types",
)
def test_transform_pipeline_sorts_rows_after_filtering():
    pipeline = Pipeline(
        steps=[
            steps.row_filter(formula="id != 2"),
            steps.row_sort(field_names=["score"], reverse=True),
        ]
    )
    target = transform(typed_inline_resource(), pipeline=pipeline)
    assert [row["id"] for row in rows_as_dicts(target)] == [1]


@pytest.mark.depends_on(
    "test_pipeline_descriptor_round_trip_preserves_step_types",
    "test_transform_action_normalizes_string_cells",
)
def test_transform_action_accepts_pipeline_descriptor():
    pipeline = Pipeline.from_descriptor(
        {"steps": [{"type": "row-filter", "formula": "id == 2"}]}
    )
    target = transform(
        Resource(data=[["id"], [1], [2]], name="items"),
        pipeline=pipeline,
    )
    assert rows_as_dicts(target) == [{"id": 2}]


@pytest.mark.depends_on(
    "test_resource_copy_preserves_descriptor_and_rows",
    "test_describe_infers_csv_schema",
)
def test_local_csv_can_be_converted_to_inline_and_back(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    described = describe(filename)
    inline_target = described.write(Resource(data=[]))
    inline = Resource(name="inline-copy", data=inline_target.data)
    assert normalized_rows(inline) == normalized_rows(described)
    assert inline.to_descriptor()["format"] == "inline"


@pytest.mark.depends_on(
    "test_resource_descriptor_json_round_trip",
    "test_resource_descriptor_yaml_round_trip",
)
def test_local_json_and_yaml_resources_round_trip_through_write_json(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    write_json(
        tmp_path,
        "records.json",
        [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}],
    )
    source = Resource(
        path="records.json",
        format="json",
    )
    json_target = Resource(path="copy.json", format="json")
    yaml_target = Resource(path="records.yaml", format="yaml")
    source.write_json(json_target)
    source.write_json(yaml_target)
    assert Resource("copy.json").read_json() == [
        {"id": 1, "name": "Ada"},
        {"id": 2, "name": "Bob"},
    ]
    assert Resource("records.yaml").read_json() == [
        {"id": 1, "name": "Ada"},
        {"id": 2, "name": "Bob"},
    ]


@pytest.mark.depends_on(
    "test_schema_field_management_and_cell_projection",
    "test_resource_inline_rows_cast_to_declared_schema",
)
def test_schema_json_projection_rehydrates_resource_casting(tmp_path):
    schema = simple_schema()
    path = tmp_path / "schema.json"
    schema.to_json(str(path))
    restored_schema = Schema.from_descriptor(str(path))
    resource = Resource(
        name="restored",
        data=[["id", "name", "score"], ["5", "Eve", "4.5"]],
        schema=restored_schema,
    )
    assert rows_as_dicts(resource) == [
        {"id": 5, "name": "Eve", "score": Decimal("4.5")}
    ]


@pytest.mark.depends_on(
    "test_detector_options_are_public_and_configurable",
    "test_pipeline_descriptor_round_trip_preserves_step_types",
)
def test_dialect_descriptor_round_trip_keeps_csv_control(tmp_path, monkeypatch):
    filename = local_csv(
        tmp_path,
        monkeypatch,
        content="id;name\n1;Ada\n",
    )
    dialect = Dialect.from_descriptor({"csv": {"delimiter": ";"}})
    restored = Dialect.from_descriptor(dialect.to_descriptor())
    resource = describe(filename, dialect=restored)
    assert restored.to_descriptor() == {"csv": {"delimiter": ";"}}
    assert rows_as_dicts(resource) == [{"id": 1, "name": "Ada"}]


@pytest.mark.depends_on(
    "test_validate_invalid_rows_exposes_structured_error",
    "test_report_flatten_exposes_structured_error_columns",
)
def test_report_descriptor_round_trip_preserves_structured_projection():
    resource = Resource(
        name="broken",
        data=[["id"], ["bad"]],
        schema=Schema.from_descriptor(
            {"fields": [{"name": "id", "type": "integer"}]}
        ),
    )
    original = validate(resource)
    restored = original.from_descriptor(original.to_descriptor())
    assert report_projection(restored) == report_projection(original)


@pytest.mark.depends_on(
    "test_validate_invalid_rows_exposes_structured_error",
    "test_resource_copy_preserves_descriptor_and_rows",
)
def test_error_descriptor_round_trip_keeps_public_coordinates():
    resource = Resource(
        name="broken",
        data=[["id"], ["bad"]],
        schema=Schema.from_descriptor(
            {"fields": [{"name": "id", "type": "integer"}]}
        ),
    )
    error = validate(resource).task.errors[0]
    restored = error.__class__.from_descriptor(error.to_descriptor())
    assert restored.to_descriptor()["type"] == error.to_descriptor()["type"]
    assert restored.to_descriptor()["rowNumber"] == 2
    assert restored.to_descriptor()["fieldName"] == "id"


@pytest.mark.depends_on(
    "test_describe_infers_csv_schema",
    "test_transform_action_adds_a_field",
    "test_validate_valid_inline_resource_has_clean_report",
)
def test_local_data_workflow_describe_transform_extract_validate(
    tmp_path,
    monkeypatch,
):
    filename = local_csv(tmp_path, monkeypatch, content=VALID_CSV)
    described = describe(filename)
    described_field_names = list(described.schema.field_names)
    target = transform(
        described,
        steps=[
            steps.row_filter(function=lambda row: int(row["id"]) > 1),
            steps.field_add(name="source", value="local"),
        ],
    )
    extracted = extract(target)
    report = validate(target)
    assert described_field_names == ["id", "name", "active", "score"]
    assert [row["id"] for row in extracted["table"]] == [2, 3]
    assert [row["source"] for row in extracted["table"]] == ["local", "local"]
    assert report.valid is True
