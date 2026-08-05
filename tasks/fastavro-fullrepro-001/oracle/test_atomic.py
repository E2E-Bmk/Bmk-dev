# Spec2Repo oracle - atomic tests for fastavro-fullrepro-001

from __future__ import annotations

import io
import json
from decimal import Decimal

import pytest


def test_fullname_combines_namespace_and_name():
    """Verifies: FASTAVRO-SCHEMA-001."""
    from fastavro.schema import fullname

    schema = {"type": "record", "name": "Event", "namespace": "sample.audit", "fields": []}
    assert fullname(schema) == "sample.audit.Event"


def test_fullname_preserves_already_qualified_name():
    """Verifies: FASTAVRO-SCHEMA-001."""
    from fastavro.schema import fullname

    schema = {"type": "record", "name": "external.Invoice", "namespace": "sample.audit", "fields": []}
    assert fullname(schema) == "external.Invoice"


def test_parse_schema_preserves_aliases_and_field_defaults():
    """Verifies: FASTAVRO-SCHEMA-002, FASTAVRO-SCHEMA-003."""
    from fastavro.schema import parse_schema

    parsed = parse_schema(
        {
            "type": "record",
            "name": "Widget",
            "aliases": ["LegacyWidget"],
            "fields": [{"name": "color", "type": "string", "default": "green"}],
        }
    )
    assert parsed["aliases"] == ["LegacyWidget"]
    assert parsed["fields"][0]["default"] == "green"


def test_parse_schema_resolves_named_reference_with_shared_mapping():
    """Verifies: FASTAVRO-SCHEMA-004."""
    from fastavro.schema import parse_schema

    named = {}
    address = parse_schema(
        {"type": "record", "name": "Address", "fields": [{"name": "city", "type": "string"}]},
        named,
    )
    envelope = parse_schema(
        {"type": "record", "name": "Envelope", "fields": [{"name": "destination", "type": "Address"}]},
        named,
    )
    assert named["Address"]["fields"][0]["name"] == address["fields"][0]["name"]
    assert envelope["fields"][0]["type"] == "Address"


def test_parse_schema_unknown_named_type_raises_unknown_type():
    """Verifies: FASTAVRO-SCHEMA-005, FASTAVRO-ERR-001."""
    from fastavro.schema import UnknownType, parse_schema

    with pytest.raises(UnknownType):
        parse_schema({"type": "record", "name": "Box", "fields": [{"name": "item", "type": "Missing"}]})


def test_parse_schema_rejects_duplicate_enum_symbols():
    """Verifies: FASTAVRO-SCHEMA-006, FASTAVRO-ERR-001."""
    from fastavro.schema import SchemaParseException, parse_schema

    schema = {"type": "enum", "name": "Signal", "symbols": ["GREEN", "AMBER", "GREEN"]}
    with pytest.raises(SchemaParseException):
        parse_schema(schema)


def test_parse_schema_rejects_decimal_scale_larger_than_precision():
    """Verifies: FASTAVRO-SCHEMA-007, FASTAVRO-ERR-001."""
    from fastavro.schema import SchemaParseException, parse_schema

    schema = {"type": "bytes", "logicalType": "decimal", "precision": 3, "scale": 5}
    with pytest.raises(SchemaParseException):
        parse_schema(schema)


def test_expand_schema_replaces_named_reference_with_record_body():
    """Verifies: FASTAVRO-SCHEMA-008."""
    from fastavro.schema import expand_schema, parse_schema

    parsed = parse_schema(
        {
            "type": "record",
            "name": "Outer",
            "fields": [
                {
                    "name": "left",
                    "type": {"type": "record", "name": "Inner", "fields": [{"name": "value", "type": "int"}]},
                },
                {"name": "right", "type": "Inner"},
            ],
        }
    )
    expanded = expand_schema(parsed)
    assert expanded["fields"][1]["type"]["name"] == "Inner"
    assert expanded["fields"][1]["type"]["fields"][0]["name"] == "value"


def test_canonical_form_omits_doc_alias_and_orders_record_keys():
    """Verifies: FASTAVRO-SCHEMA-009."""
    from fastavro.schema import to_parsing_canonical_form

    schema = {
        "doc": "not part of parsing canonical form",
        "type": "record",
        "name": "CanonicalUser",
        "aliases": ["OldUser"],
        "fields": [{"doc": "ignored", "default": 0, "type": "int", "name": "rank"}],
    }
    assert to_parsing_canonical_form(schema) == (
        '{"name":"CanonicalUser","type":"record","fields":[{"name":"rank","type":"int"}]}'
    )


def test_fingerprint_crc64_avro_returns_hex_string_for_canonical_form():
    """Verifies: FASTAVRO-SCHEMA-010."""
    from fastavro.schema import fingerprint, to_parsing_canonical_form

    canonical = to_parsing_canonical_form({"type": "record", "name": "Tiny", "fields": []})
    assert fingerprint(canonical, "CRC-64-AVRO") == "9954e82071447a39"


def test_fingerprint_unknown_algorithm_raises_value_error():
    """Verifies: FASTAVRO-SCHEMA-010, FASTAVRO-ERR-002."""
    from fastavro.schema import fingerprint

    with pytest.raises(ValueError):
        fingerprint('"int"', "not-a-real-digest")


def test_flat_dict_repository_loads_schema_by_name(tmp_path):
    """Verifies: FASTAVRO-REPO-001."""
    from fastavro.repository import FlatDictRepository

    (tmp_path / "Address.avsc").write_text(
        json.dumps({"type": "record", "name": "Address", "fields": [{"name": "zip", "type": "string"}]})
    )
    assert FlatDictRepository(str(tmp_path)).load("Address")["fields"][0]["name"] == "zip"


def test_flat_dict_repository_missing_file_raises_repository_error(tmp_path):
    """Verifies: FASTAVRO-REPO-002, FASTAVRO-ERR-003."""
    from fastavro.repository import FlatDictRepository, SchemaRepositoryError

    with pytest.raises(SchemaRepositoryError):
        FlatDictRepository(str(tmp_path)).load("Ghost")


def test_validate_accepts_matching_record(user_schema):
    """Verifies: FASTAVRO-VALID-001."""
    from fastavro import validate

    assert validate({"id": 7, "name": "Nia", "active": True, "score": None, "tags": []}, user_schema)


def test_validate_returns_false_when_raise_errors_is_false(user_schema):
    """Verifies: FASTAVRO-VALID-002."""
    from fastavro import validate

    assert validate({"id": "bad", "name": "Nia", "active": True, "score": None, "tags": []}, user_schema, raise_errors=False) is False


def test_validate_raises_for_invalid_record_by_default(user_schema):
    """Verifies: FASTAVRO-VALID-002, FASTAVRO-ERR-004."""
    from fastavro import validate
    from fastavro.validation import ValidationError

    with pytest.raises(ValidationError):
        validate({"id": "bad", "name": "Nia", "active": True, "score": None, "tags": []}, user_schema)


def test_validate_accepts_extra_field_not_declared_in_schema(user_schema):
    """Verifies: FASTAVRO-VALID-003."""
    from fastavro import validate

    record = {"id": 8, "name": "Ola", "active": True, "score": None, "tags": [], "bonus": 1}
    assert validate(record, user_schema)


def test_validate_accepts_missing_defaulted_fields(user_schema):
    """Verifies: FASTAVRO-VALID-004."""
    from fastavro import validate

    record = {"id": 8, "name": "Ola"}
    assert validate(record, user_schema)


def test_validate_many_accepts_all_matching_records(user_schema, user_records):
    """Verifies: FASTAVRO-VALID-005."""
    from fastavro.validation import validate_many

    assert validate_many(user_records, user_schema)


def test_validate_many_returns_false_when_any_record_is_invalid(user_schema, user_records):
    """Verifies: FASTAVRO-VALID-005."""
    from fastavro.validation import validate_many

    records = user_records + [{"id": 34, "name": 900, "active": True, "score": None, "tags": []}]
    assert validate_many(records, user_schema, raise_errors=False) is False


def test_validate_union_accepts_tuple_branch_hint():
    """Verifies: FASTAVRO-VALID-006."""
    from fastavro import validate

    child = {"type": "record", "name": "Child", "fields": [{"name": "name", "type": "string"}]}
    pet = {"type": "record", "name": "Pet", "fields": [{"name": "name", "type": "string"}]}
    schema = {"type": "record", "name": "Visit", "fields": [{"name": "guest", "type": [child, pet]}]}
    assert validate({"guest": ("Pet", {"name": "Miso"})}, schema)


def test_validate_disable_tuple_notation_rejects_tuple_branch_hint():
    """Verifies: FASTAVRO-VALID-006."""
    from fastavro import validate

    child = {"type": "record", "name": "Child", "fields": [{"name": "name", "type": "string"}]}
    pet = {"type": "record", "name": "Pet", "fields": [{"name": "name", "type": "string"}]}
    schema = {"type": "record", "name": "Visit", "fields": [{"name": "guest", "type": [child, pet]}]}
    assert validate({"guest": ("Pet", {"name": "Miso"})}, schema, raise_errors=False, disable_tuple_notation=True) is False


def test_schemaless_writer_encodes_signed_integer_zigzag_bytes():
    """Verifies: FASTAVRO-BINARY-001."""
    from fastavro import schemaless_writer

    bio = io.BytesIO()
    schemaless_writer(bio, "int", -37)
    assert bio.getvalue() == b"I"


def test_schemaless_reader_decodes_signed_integer_zigzag_bytes():
    """Verifies: FASTAVRO-BINARY-002."""
    from fastavro import schemaless_reader

    assert schemaless_reader(io.BytesIO(b"I"), "int") == -37


def test_schemaless_writer_encodes_utf8_string_with_length_prefix():
    """Verifies: FASTAVRO-BINARY-001."""
    from fastavro import schemaless_writer

    bio = io.BytesIO()
    schemaless_writer(bio, "string", "café")
    assert bio.getvalue() == b"\x0acaf\xc3\xa9"


def test_schemaless_reader_decodes_utf8_string_payload():
    """Verifies: FASTAVRO-BINARY-002."""
    from fastavro import schemaless_reader

    assert schemaless_reader(io.BytesIO(b"\x0acaf\xc3\xa9"), "string") == "café"


def test_schemaless_reader_applies_reader_schema_default():
    """Verifies: FASTAVRO-BINARY-003."""
    from fastavro import schemaless_reader

    writer_schema = {"type": "record", "name": "Small", "fields": [{"name": "id", "type": "int"}]}
    reader_schema = {
        "type": "record",
        "name": "Small",
        "fields": [{"name": "id", "type": "int"}, {"name": "flag", "type": "boolean", "default": True}],
    }
    assert schemaless_reader(io.BytesIO(b"\x12"), writer_schema, reader_schema) == {"id": 9, "flag": True}


def test_schemaless_writer_strict_rejects_missing_required_field():
    """Verifies: FASTAVRO-BINARY-004, FASTAVRO-ERR-005."""
    from fastavro import schemaless_writer

    schema = {"type": "record", "name": "StrictOne", "fields": [{"name": "id", "type": "int"}]}
    with pytest.raises(ValueError):
        schemaless_writer(io.BytesIO(), schema, {}, strict=True)


def test_json_writer_emits_one_json_object_per_record(user_schema):
    """Verifies: FASTAVRO-JSON-001."""
    from fastavro import json_writer

    out = io.StringIO()
    json_writer(out, user_schema, [{"id": 5, "name": "Ivy", "active": True, "score": None, "tags": ["x"]}])
    assert json.loads(out.getvalue()) == {"id": 5, "name": "Ivy", "active": True, "score": None, "tags": ["x"]}


def test_json_writer_wraps_union_values_by_default():
    """Verifies: FASTAVRO-JSON-002."""
    from fastavro import json_writer

    schema = {"type": "record", "name": "MaybeText", "fields": [{"name": "value", "type": ["null", "string"]}]}
    out = io.StringIO()
    json_writer(out, schema, [{"value": "present"}])
    assert json.loads(out.getvalue()) == {"value": {"string": "present"}}


def test_json_writer_can_omit_union_type_wrapper():
    """Verifies: FASTAVRO-JSON-002."""
    from fastavro import json_writer

    schema = {"type": "record", "name": "MaybeText", "fields": [{"name": "value", "type": ["null", "string"]}]}
    out = io.StringIO()
    json_writer(out, schema, [{"value": "present"}], write_union_type=False)
    assert json.loads(out.getvalue()) == {"value": "present"}


def test_json_reader_reads_union_wrapper_payload():
    """Verifies: FASTAVRO-JSON-003."""
    from fastavro import json_reader

    schema = {"type": "record", "name": "MaybeText", "fields": [{"name": "value", "type": ["null", "string"]}]}
    records = list(json_reader(io.StringIO('{"value": {"string": "present"}}'), schema))
    assert records == [{"value": "present"}]


def test_json_reader_applies_reader_schema_default():
    """Verifies: FASTAVRO-JSON-004."""
    from fastavro import json_reader

    writer_schema = {"type": "record", "name": "SmallJson", "fields": [{"name": "id", "type": "int"}]}
    reader_schema = {
        "type": "record",
        "name": "SmallJson",
        "fields": [{"name": "id", "type": "int"}, {"name": "label", "type": "string", "default": "fresh"}],
    }
    assert list(json_reader(io.StringIO('{"id": 44}'), writer_schema, reader_schema)) == [{"id": 44, "label": "fresh"}]


def test_is_avro_returns_false_for_non_avro_buffer():
    """Verifies: FASTAVRO-CONTAINER-001."""
    from fastavro import is_avro

    assert is_avro(io.BytesIO(b"not an avro object container")) is False


def test_is_avro_recognizes_object_container_magic_prefix():
    """Verifies: FASTAVRO-CONTAINER-001."""
    from fastavro import is_avro

    assert is_avro(io.BytesIO(b"Obj\x01rest of header")) is True


def test_version_is_importable_string():
    """Verifies: FASTAVRO-API-001."""
    import fastavro

    version = fastavro.__version__
    assert isinstance(version, str)
    assert version.count(".") >= 2


def test_public_logical_type_registries_are_mutable_mappings():
    """Verifies: FASTAVRO-LOGICAL-001."""
    from fastavro.read import LOGICAL_READERS
    from fastavro.write import LOGICAL_WRITERS

    writer_key = "string-stage2probe"
    reader_key = "string-stage2probe"
    LOGICAL_WRITERS[writer_key] = lambda datum, schema: datum
    LOGICAL_READERS[reader_key] = lambda datum, writer_schema, reader_schema: datum
    assert writer_key in LOGICAL_WRITERS
    assert reader_key in LOGICAL_READERS
    del LOGICAL_WRITERS[writer_key]
    del LOGICAL_READERS[reader_key]
