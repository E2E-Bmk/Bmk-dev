from __future__ import annotations

import io
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from conftest import DEMO_NS, EXT_NS, FixturePaths


def test_schema_constructs_from_local_xsd(fixture_paths: FixturePaths):
    from xmlschema import XMLSchema

    schema = XMLSchema(fixture_paths.schema)
    assert schema.target_namespace == DEMO_NS
    assert schema.built


def test_schema_constructs_from_text_with_base_url(fixture_paths: FixturePaths):
    from xmlschema import XMLSchema

    schema = XMLSchema(
        fixture_paths.schema.read_text(encoding="utf-8"),
        base_url=fixture_paths.root.as_uri() + "/",
    )
    assert schema.target_namespace == DEMO_NS
    assert schema.built


def test_build_switch_controls_public_built_state(fixture_paths: FixturePaths):
    from xmlschema import XMLSchema

    schema = XMLSchema(fixture_paths.schema, build=False)
    assert not schema.built
    schema.build()
    assert schema.built


def test_schema_namespaces_expose_include_and_import_targets(schema):
    assert schema.namespaces["tns"] == DEMO_NS
    assert schema.namespaces["ext"] == EXT_NS
    assert any(
        imported.target_namespace == EXT_NS
        for imported in schema.imports.values()
        if imported is not None
    )


def test_schema_maps_expose_root_element_and_named_types(schema):
    assert f"{{{DEMO_NS}}}order" in schema.maps.elements
    assert f"{{{DEMO_NS}}}CodeType" in schema.maps.types
    assert schema.root_elements[0].local_name == "order"


def test_schema_component_lookup_returns_public_element(schema):
    element = schema.get_element(f"{{{DEMO_NS}}}order")
    assert element is schema.maps.elements[f"{{{DEMO_NS}}}order"]
    assert element.local_name == "order"


def test_schema_get_schema_resolves_loaded_namespace(schema):
    assert schema.get_schema(DEMO_NS) is schema
    assert schema.get_schema(EXT_NS).target_namespace == EXT_NS


def test_package_is_valid_accepts_valid_fixture(fixture_paths):
    from xmlschema import is_valid

    assert is_valid(fixture_paths.valid_xml, schema=fixture_paths.schema)


def test_package_is_valid_rejects_invalid_fixture(fixture_paths):
    from xmlschema import is_valid

    assert not is_valid(fixture_paths.invalid_xml, schema=fixture_paths.schema)


def test_package_validate_accepts_valid_fixture(fixture_paths):
    from xmlschema import validate

    assert validate(fixture_paths.valid_xml, schema=fixture_paths.schema) is None


def test_package_iter_errors_returns_structured_errors(fixture_paths):
    from xmlschema import iter_errors

    errors = list(iter_errors(fixture_paths.invalid_xml, schema=fixture_paths.schema))
    assert errors
    assert all(error.reason or error.path for error in errors)


def test_schema_validate_and_is_valid_share_result(schema, fixture_paths):
    schema.validate(fixture_paths.valid_xml)
    assert schema.is_valid(fixture_paths.valid_xml)
    assert not schema.is_valid(fixture_paths.invalid_xml)


def test_schema_iter_errors_is_empty_for_valid_fixture(schema, fixture_paths):
    assert list(schema.iter_errors(fixture_paths.valid_xml)) == []


def test_to_dict_returns_decoded_mapping(schema, fixture_paths):
    value = schema.to_dict(fixture_paths.valid_xml)
    assert isinstance(value, dict)
    assert value["customer"] == "Ada"
    assert value["items"]["item"][0]["sku"] == "CD34"


def test_to_json_returns_json_text(schema, fixture_paths):
    from xmlschema import to_json

    value = to_json(fixture_paths.valid_xml, schema=schema)
    decoded = json.loads(value)
    assert decoded["customer"] == "Ada"
    assert decoded["items"]["item"][1]["quantity"] == 1


def test_to_json_writes_to_text_stream(schema, fixture_paths):
    from xmlschema import to_json

    stream = io.StringIO()
    result = to_json(fixture_paths.valid_xml, fp=stream, schema=schema)
    assert result is None
    assert json.loads(stream.getvalue())["total"] == 19.95


def test_to_etree_encodes_public_mapping(schema, fixture_paths):
    value = schema.to_dict(fixture_paths.valid_xml)
    element = schema.encode(value)
    assert element.tag == f"{{{DEMO_NS}}}order"
    assert element.attrib["id"] == "AB12"


def test_package_to_etree_encodes_using_schema(fixture_paths):
    from xmlschema import to_dict, to_etree

    value = to_dict(fixture_paths.valid_xml, schema=fixture_paths.schema)
    element = to_etree(value, schema=fixture_paths.schema)
    assert element.tag == f"{{{DEMO_NS}}}order"


def test_from_json_encodes_json_text(schema):
    from xmlschema import from_json

    element, errors = from_json(
        '{"@xmlns":"urn:demo","@id":"AB12","customer":"Ada","items":{"item":[{"sku":"CD34","quantity":2}]},"total":19.95}',
        schema=schema,
        validation="lax",
    )
    assert element.tag == f"{{{DEMO_NS}}}order"
    assert not errors


def test_default_converter_has_public_converter_contract(schema):
    converter = schema.get_converter()
    assert converter.__class__.__name__ == "XMLSchemaConverter"
    assert converter.lossy is True


def test_parker_converter_changes_root_projection(schema, fixture_paths):
    from xmlschema import ParkerConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=ParkerConverter)
    assert value["customer"] == "Ada"
    assert "items" in value


def test_badgerfish_converter_projects_attributes(schema, fixture_paths):
    from xmlschema import BadgerFishConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=BadgerFishConverter)
    assert value["order"]["@id"] == "AB12"
    assert value["order"]["customer"]["$"] == "Ada"


def test_jsonml_converter_projects_tagged_sequence(schema, fixture_paths):
    from xmlschema import JsonMLConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=JsonMLConverter)
    assert value[0].endswith("order")
    assert any(isinstance(item, list) and item[0].endswith("customer") for item in value)


def test_columnar_converter_projects_named_columns(schema, fixture_paths):
    from xmlschema import ColumnarConverter

    value = schema.to_dict(fixture_paths.valid_xml, converter=ColumnarConverter)
    assert "order" in value
    assert value["order"]["customer"] == "Ada"


def test_xml_resource_reports_local_url(fixture_paths: FixturePaths):
    from xmlschema import XMLResource

    resource = XMLResource(fixture_paths.valid_xml, allow="local")
    assert resource.url.startswith("file:")
    assert resource.root.tag.endswith("order")


def test_xml_resource_none_policy_blocks_local_file(fixture_paths: FixturePaths):
    from xmlschema import XMLResource
    from xmlschema.exceptions import XMLResourceBlocked

    with pytest.raises(XMLResourceBlocked):
        XMLResource(fixture_paths.valid_xml, allow="none")


def test_fetch_resource_normalizes_local_path(fixture_paths: FixturePaths):
    from xmlschema import fetch_resource

    result = fetch_resource(str(fixture_paths.valid_xml))
    assert result.startswith("file:")
    assert result.endswith("order.xml")


def test_fetch_schema_returns_local_schema_url(fixture_paths: FixturePaths):
    from xmlschema import fetch_schema

    result = fetch_schema(fixture_paths.hinted_xml)
    assert result.endswith("order.xsd")


def test_fetch_namespaces_reads_local_xml(fixture_paths: FixturePaths):
    from xmlschema import fetch_namespaces

    namespaces = fetch_namespaces(fixture_paths.valid_xml)
    assert namespaces[""] == DEMO_NS
    assert namespaces["ext"] == EXT_NS


def test_etree_element_is_accepted_as_document_source(schema, valid_xml):
    root = ElementTree.fromstring(valid_xml)
    assert schema.is_valid(root)


def test_schema_export_returns_location_mapping(schema, fixture_paths, tmp_path: Path):
    target = tmp_path / "exported"
    target.mkdir()
    locations = schema.export(target)
    assert isinstance(locations, dict)
    assert any(path.suffix == ".xsd" for path in target.rglob("*.xsd"))


def test_schema_component_iteration_exposes_public_components(schema):
    components = list(schema.iter_components())
    assert components[0] is schema
    assert any(
        getattr(component, "local_name", None) == "order"
        for component in components
    )
