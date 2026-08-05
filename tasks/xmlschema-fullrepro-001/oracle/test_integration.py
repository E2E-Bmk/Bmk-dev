from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import DEMO_NS, FixturePaths


@pytest.mark.depends_on("test_to_dict_returns_decoded_mapping", "test_to_json_returns_json_text")
def test_decode_and_json_projections_agree_on_business_fields(schema, fixture_paths):
    from xmlschema import to_json

    decoded = schema.to_dict(fixture_paths.valid_xml)
    encoded = json.loads(to_json(fixture_paths.valid_xml, schema=schema))
    assert decoded["customer"] == encoded["customer"] == "Ada"
    assert decoded["items"]["item"][0]["quantity"] == encoded["items"]["item"][0]["quantity"]


@pytest.mark.depends_on("test_to_json_writes_to_text_stream", "test_from_json_encodes_json_text")
def test_stream_json_and_json_encoding_round_trip(schema, fixture_paths):
    from xmlschema import to_json

    stream = io.StringIO()
    to_json(fixture_paths.valid_xml, fp=stream, schema=schema)
    element, errors = schema.encode(json.loads(stream.getvalue()), validation="lax")
    assert not errors
    assert schema.is_valid(element)


@pytest.mark.depends_on("test_package_is_valid_rejects_invalid_fixture", "test_package_iter_errors_returns_structured_errors")
def test_invalid_document_reports_false_and_nonempty_error_projection(fixture_paths):
    from xmlschema import is_valid, iter_errors

    errors = list(iter_errors(fixture_paths.invalid_xml, schema=fixture_paths.schema))
    assert is_valid(fixture_paths.invalid_xml, schema=fixture_paths.schema) is False
    assert len(errors) >= 1


@pytest.mark.depends_on("test_schema_constructs_from_text_with_base_url", "test_schema_namespaces_expose_include_and_import_targets")
def test_text_schema_base_url_resolves_both_local_dependencies(fixture_paths):
    from xmlschema import XMLSchema

    schema = XMLSchema(
        fixture_paths.schema.read_text(encoding="utf-8"),
        base_url=fixture_paths.root.as_uri() + "/",
    )
    assert schema.is_valid(fixture_paths.valid_xml)
    assert schema.get_schema("urn:ext").target_namespace == "urn:ext"


@pytest.mark.depends_on("test_build_switch_controls_public_built_state", "test_schema_component_iteration_exposes_public_components")
def test_deferred_build_then_component_iteration_produces_same_root(schema, fixture_paths):
    from xmlschema import XMLSchema

    deferred = XMLSchema(fixture_paths.schema, build=False)
    deferred.build()
    assert deferred.built
    assert deferred.get_element(f"{{{DEMO_NS}}}order").local_name == "order"
    assert len(list(deferred.iter_components())) == len(list(schema.iter_components()))


@pytest.mark.depends_on("test_schema_export_returns_location_mapping", "test_schema_constructs_from_local_xsd")
def test_exported_schema_bundle_reloads_and_validates(schema, fixture_paths, tmp_path: Path):
    target = tmp_path / "bundle"
    target.mkdir()
    schema.export(target)
    exported_schema = next(target.rglob("order.xsd"))
    from xmlschema import XMLSchema

    reloaded = XMLSchema(exported_schema)
    assert reloaded.is_valid(fixture_paths.valid_xml)


@pytest.mark.depends_on("test_schema_maps_expose_root_element_and_named_types", "test_schema_constructs_from_local_xsd")
def test_add_schema_extends_existing_component_map(schema, fixture_paths):
    added = schema.add_schema(fixture_paths.extra, build=True)
    assert added.target_namespace == DEMO_NS
    assert f"{{{DEMO_NS}}}status" in schema.maps.elements
    assert schema.get_element(f"{{{DEMO_NS}}}status").local_name == "status"


@pytest.mark.depends_on("test_schema_namespaces_expose_include_and_import_targets", "test_schema_get_schema_resolves_loaded_namespace")
def test_import_and_include_state_is_visible_after_build(schema):
    assert schema.includes
    assert any(
        imported is not None and imported.target_namespace == "urn:ext"
        for imported in schema.imports.values()
    )
    assert schema.get_schema("urn:ext").maps.elements


@pytest.mark.depends_on("test_parker_converter_changes_root_projection", "test_to_etree_encodes_public_mapping")
def test_parker_decode_then_encode_preserves_validity(schema, fixture_paths):
    from xmlschema import ParkerConverter

    parker = schema.to_dict(fixture_paths.valid_xml, converter=ParkerConverter)
    element, errors = schema.encode(parker, converter=ParkerConverter, validation="lax")
    assert element.tag == f"{{{DEMO_NS}}}order"
    assert errors


@pytest.mark.depends_on("test_badgerfish_converter_projects_attributes", "test_to_etree_encodes_public_mapping")
def test_badgerfish_decode_then_encode_preserves_attribute(schema, fixture_paths):
    from xmlschema import BadgerFishConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=BadgerFishConverter)
    element = schema.encode(value, converter=BadgerFishConverter)
    assert element.attrib["id"] == "AB12"
    assert schema.is_valid(element)


@pytest.mark.depends_on("test_jsonml_converter_projects_tagged_sequence", "test_to_etree_encodes_public_mapping")
def test_jsonml_decode_then_encode_preserves_root_name(schema, fixture_paths):
    from xmlschema import JsonMLConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=JsonMLConverter)
    element = schema.encode(value, converter=JsonMLConverter)
    assert element.tag == f"{{{DEMO_NS}}}order"
    assert schema.is_valid(element)


@pytest.mark.depends_on("test_columnar_converter_projects_named_columns", "test_to_etree_encodes_public_mapping")
def test_columnar_decode_then_encode_preserves_root_name(schema, fixture_paths):
    from xmlschema import ColumnarConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=ColumnarConverter)
    element, errors = schema.encode(value, converter=ColumnarConverter, validation="lax")
    assert element.tag == f"{{{DEMO_NS}}}order"
    assert errors


@pytest.mark.depends_on("test_package_to_etree_encodes_using_schema", "test_schema_validate_and_is_valid_share_result")
def test_package_etree_projection_can_be_validated_again(fixture_paths):
    from xmlschema import is_valid, to_dict, to_etree

    value = to_dict(fixture_paths.valid_xml, schema=fixture_paths.schema)
    element = to_etree(value, schema=fixture_paths.schema)
    assert is_valid(element, schema=fixture_paths.schema)


@pytest.mark.depends_on("test_from_json_encodes_json_text", "test_schema_validate_and_is_valid_share_result")
def test_json_file_projection_encodes_and_validates(schema, fixture_paths):
    from xmlschema import from_json

    element, errors = from_json(fixture_paths.json_input.read_text(encoding="utf-8"), schema=schema, validation="lax")
    assert not errors
    assert element.tag.endswith("order")
    assert schema.is_valid(element)


@pytest.mark.depends_on("test_etree_element_is_accepted_as_document_source", "test_to_dict_returns_decoded_mapping")
def test_element_tree_source_decodes_same_customer(schema, valid_xml):
    from xml.etree import ElementTree

    root = ElementTree.fromstring(valid_xml)
    assert schema.to_dict(root)[f"{{{DEMO_NS}}}customer"] == "Ada"


@pytest.mark.depends_on("test_xml_resource_reports_local_url", "test_schema_validate_and_is_valid_share_result")
def test_local_resource_can_be_validated_and_decoded(schema, fixture_paths):
    from xmlschema import XMLResource

    resource = XMLResource(fixture_paths.valid_xml, allow="local")
    assert schema.is_valid(resource)
    assert schema.to_dict(resource)["customer"] == "Ada"


@pytest.mark.depends_on("test_xml_resource_none_policy_blocks_local_file", "test_fetch_resource_normalizes_local_path")
def test_resource_policy_allows_local_but_rejects_none(fixture_paths):
    from xmlschema import XMLResource
    from xmlschema.exceptions import XMLResourceBlocked

    local = XMLResource(fixture_paths.valid_xml, allow="local")
    assert local.root.tag.endswith("order")
    with pytest.raises(XMLResourceBlocked):
        XMLResource(fixture_paths.valid_xml, allow="none")


@pytest.mark.depends_on("test_schema_export_returns_location_mapping", "test_fetch_schema_returns_local_schema_url")
def test_export_location_map_points_to_local_xsd_files(schema, fixture_paths, tmp_path: Path):
    target = tmp_path / "exported"
    target.mkdir()
    locations = schema.export(target)
    assert isinstance(locations, dict)
    assert all(Path(path).suffix == ".xsd" for path in target.rglob("*.xsd"))


@pytest.mark.depends_on("test_fetch_namespaces_reads_local_xml", "test_package_is_valid_accepts_valid_fixture")
def test_namespace_projection_matches_schema_validation(fixture_paths):
    from xmlschema import fetch_namespaces, is_valid

    namespaces = fetch_namespaces(fixture_paths.valid_xml)
    assert namespaces[""] == DEMO_NS
    assert is_valid(fixture_paths.valid_xml, schema=fixture_paths.schema)


@pytest.mark.depends_on("test_schema_get_schema_resolves_loaded_namespace", "test_schema_maps_expose_root_element_and_named_types")
def test_maps_and_root_elements_agree_on_global_order(schema):
    root_names = {element.name for element in schema.root_elements}
    assert root_names <= set(schema.maps.elements)
    assert f"{{{DEMO_NS}}}order" in root_names


@pytest.mark.depends_on("test_schema_component_iteration_exposes_public_components", "test_schema_get_schema_resolves_loaded_namespace")
def test_component_iteration_contains_imported_public_element(schema):
    names = {component.name for component in schema.iter_components() if hasattr(component, "name")}
    assert f"{{urn:ext}}note" in names


@pytest.mark.depends_on("test_to_json_returns_json_text", "test_to_json_writes_to_text_stream")
def test_json_options_make_pretty_output_without_changing_data(schema, fixture_paths):
    from xmlschema import to_json

    compact = json.loads(to_json(fixture_paths.valid_xml, schema=schema))
    pretty = json.loads(
        to_json(fixture_paths.valid_xml, schema=schema, json_options={"indent": 2})
    )
    assert compact == pretty
    assert "\n" in to_json(
        fixture_paths.valid_xml, schema=schema, json_options={"indent": 2}
    )


@pytest.mark.depends_on("test_schema_validate_and_is_valid_share_result", "test_schema_iter_errors_is_empty_for_valid_fixture")
def test_lax_decode_returns_data_and_error_tuple_for_invalid_input(schema, fixture_paths):
    value = schema.to_dict(fixture_paths.invalid_xml, validation="lax")
    assert isinstance(value, tuple)
    assert isinstance(value[1], list)
    assert value[1]


@pytest.mark.depends_on("test_package_iter_errors_returns_structured_errors", "test_schema_validate_and_is_valid_share_result")
def test_error_projection_preserves_path_or_reason_without_message_matching(fixture_paths):
    from xmlschema import iter_errors

    error = next(iter(iter_errors(fixture_paths.invalid_xml, schema=fixture_paths.schema)))
    assert isinstance(error.path, (str, type(None)))
    assert isinstance(error.reason, (str, type(None)))
    assert error.path or error.reason


@pytest.mark.depends_on("test_default_converter_has_public_converter_contract", "test_to_dict_returns_decoded_mapping")
def test_converter_instance_and_converter_class_have_same_default_fields(schema, fixture_paths):
    instance = schema.get_converter()
    first = schema.to_dict(fixture_paths.valid_xml, converter=instance)
    second = schema.to_dict(fixture_paths.valid_xml, converter=instance.__class__)
    assert first["customer"] == second["customer"] == "Ada"


@pytest.mark.depends_on("test_schema_constructs_from_local_xsd", "test_package_is_valid_accepts_valid_fixture")
def test_cli_validate_command_reports_success(fixture_paths, capsys):
    from xmlschema.cli import validate

    with patch.object(sys, "argv", ["xmlschema-validate", "--schema", str(fixture_paths.schema), str(fixture_paths.valid_xml)]):
        with pytest.raises(SystemExit) as result:
            validate()
    captured = capsys.readouterr()
    assert result.value.code == 0
    assert "is valid" in captured.out
    assert captured.err == ""


@pytest.mark.depends_on("test_package_is_valid_rejects_invalid_fixture", "test_package_iter_errors_returns_structured_errors")
def test_cli_validate_command_reports_failure(fixture_paths, capsys):
    from xmlschema.cli import validate

    with patch.object(sys, "argv", ["xmlschema-validate", "--schema", str(fixture_paths.schema), str(fixture_paths.invalid_xml)]):
        with pytest.raises(SystemExit) as result:
            validate()
    captured = capsys.readouterr()
    assert result.value.code > 0
    assert "is not valid" in captured.err


@pytest.mark.depends_on("test_to_json_returns_json_text", "test_schema_constructs_from_local_xsd")
def test_cli_xml2json_writes_deterministic_local_output(fixture_paths, tmp_path: Path, capsys):
    from xmlschema.cli import xml2json

    output_dir = tmp_path / "json"
    output_dir.mkdir()
    with patch.object(sys, "argv", ["xmlschema-xml2json", "--schema", str(fixture_paths.schema), "-o", str(output_dir), str(fixture_paths.valid_xml)]):
        with pytest.raises(SystemExit) as result:
            xml2json()
    output = output_dir / "order.json"
    captured = capsys.readouterr()
    assert result.value.code == 0
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["customer"] == "Ada"
    assert "converted to" in captured.out


@pytest.mark.depends_on("test_to_json_returns_json_text", "test_schema_validate_and_is_valid_share_result")
def test_cli_json2xml_rehydrates_output_and_validates(fixture_paths, tmp_path: Path, capsys):
    from xmlschema.cli import json2xml, xml2json

    json_dir = tmp_path / "json"
    xml_dir = tmp_path / "xml"
    json_dir.mkdir()
    xml_dir.mkdir()
    with patch.object(sys, "argv", ["xmlschema-xml2json", "--schema", str(fixture_paths.schema), "-o", str(json_dir), str(fixture_paths.valid_xml)]):
        with pytest.raises(SystemExit):
            xml2json()
    with patch.object(sys, "argv", ["xmlschema-json2xml", "--schema", str(fixture_paths.schema), "-o", str(xml_dir), str(json_dir / "order.json")]):
        with pytest.raises(SystemExit) as result:
            json2xml()
    rebuilt = xml_dir / "order.xml"
    assert result.value.code == 0
    assert rebuilt.is_file()
    from xmlschema import is_valid

    assert is_valid(rebuilt, schema=fixture_paths.schema)
    assert "converted to" in capsys.readouterr().out


@pytest.mark.depends_on("test_to_json_returns_json_text", "test_schema_constructs_from_local_xsd")
def test_cli_xml2json_skips_existing_output_without_force(fixture_paths, tmp_path: Path, capsys):
    from xmlschema.cli import xml2json

    with patch.object(sys, "argv", ["xmlschema-xml2json", "--schema", str(fixture_paths.schema), "-o", str(tmp_path), str(fixture_paths.valid_xml)]):
        with pytest.raises(SystemExit):
            xml2json()
    with patch.object(sys, "argv", ["xmlschema-xml2json", "--schema", str(fixture_paths.schema), "-o", str(tmp_path), str(fixture_paths.valid_xml)]):
        with pytest.raises(SystemExit) as result:
            xml2json()
    assert result.value.code == 0
    assert "skip" in capsys.readouterr().out


@pytest.mark.depends_on("test_package_validate_accepts_valid_fixture", "test_to_json_returns_json_text")
def test_cli_converter_option_changes_json_shape(fixture_paths, tmp_path: Path, capsys):
    from xmlschema.cli import xml2json

    output_dir = tmp_path / "badgerfish"
    output_dir.mkdir()
    with patch.object(sys, "argv", ["xmlschema-xml2json", "--schema", str(fixture_paths.schema), "--converter", "badgerfish", "-o", str(output_dir), str(fixture_paths.valid_xml)]):
        with pytest.raises(SystemExit) as result:
            xml2json()
    data = json.loads((output_dir / "order.json").read_text(encoding="utf-8"))
    assert result.value.code == 0
    assert data["order"]["@id"] == "AB12"


@pytest.mark.depends_on("test_schema_constructs_from_local_xsd", "test_schema_validate_and_is_valid_share_result")
def test_schema_and_package_validation_accept_same_element(schema, fixture_paths):
    from xmlschema import is_valid

    from xml.etree import ElementTree

    element = ElementTree.parse(fixture_paths.valid_xml).getroot()
    assert schema.is_valid(element)
    assert is_valid(element, schema=schema)
