# Spec2Repo oracle - integration tests for fastavro-fullrepro-001

from __future__ import annotations

import io
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from conftest import json_lines, run_fastavro_cli, write_avro_bytes, write_avro_file


@pytest.mark.depends_on("test_validate_accepts_matching_record")
def test_writer_reader_round_trip_preserves_records_and_reader_metadata(user_schema, user_records):
    """Verifies: FASTAVRO-CONTAINER-002, FASTAVRO-CVI-001."""
    import fastavro

    payload = write_avro_bytes(user_schema, user_records, metadata={"suite": "stage-two"}, codec="null")
    avro_reader = fastavro.reader(io.BytesIO(payload))
    assert list(avro_reader) == user_records
    assert avro_reader.codec == "null"
    assert avro_reader.metadata["suite"] == "stage-two"
    assert avro_reader.writer_schema["name"] == "demo.people.Profile"


@pytest.mark.depends_on("test_validate_many_accepts_all_matching_records")
def test_writer_accepts_generator_and_reader_replays_all_items(user_schema):
    """Verifies: FASTAVRO-CONTAINER-002."""
    import fastavro

    def record_source():
        for index in range(4):
            yield {"id": 100 + index, "name": f"user-{index}", "active": index % 2 == 0, "score": None, "tags": []}

    payload = write_avro_bytes(user_schema, record_source())
    assert [record["id"] for record in fastavro.reader(io.BytesIO(payload))] == [100, 101, 102, 103]


@pytest.mark.depends_on("test_validate_returns_false_when_raise_errors_is_false")
def test_writer_with_validator_rejects_invalid_record_before_reading(user_schema):
    """Verifies: FASTAVRO-CONTAINER-003, FASTAVRO-VALID-001."""
    import fastavro
    from fastavro.validation import ValidationError

    bad_records = [{"id": "wrong", "name": "Bad", "active": True, "score": None, "tags": []}]
    with pytest.raises(ValidationError):
        fastavro.writer(io.BytesIO(), user_schema, bad_records, validator=True)


@pytest.mark.depends_on("test_is_avro_returns_false_for_non_avro_buffer")
def test_is_avro_recognizes_file_written_by_writer(tmp_path, user_schema, user_records):
    """Verifies: FASTAVRO-CONTAINER-001, FASTAVRO-CVI-001."""
    import fastavro

    path = write_avro_file(tmp_path, user_schema, user_records)
    assert fastavro.is_avro(str(path)) is True
    with path.open("rb") as stream:
        assert list(fastavro.reader(stream)) == user_records


@pytest.mark.depends_on("test_schemaless_reader_applies_reader_schema_default")
def test_container_reader_schema_adds_default_field(user_schema, user_records):
    """Verifies: FASTAVRO-RESOLUTION-001."""
    import fastavro

    reader_schema = {
        **user_schema,
        "fields": user_schema["fields"] + [{"name": "country", "type": "string", "default": "CA"}],
    }
    payload = write_avro_bytes(user_schema, user_records)
    records = list(fastavro.reader(io.BytesIO(payload), reader_schema=reader_schema))
    assert {record["country"] for record in records} == {"CA"}
    assert [record["id"] for record in records] == [31, 32, 33]


@pytest.mark.depends_on("test_json_reader_applies_reader_schema_default")
def test_container_reader_schema_drops_writer_field(user_schema, user_records):
    """Verifies: FASTAVRO-RESOLUTION-001."""
    import fastavro

    reader_schema = {"type": "record", "name": "Profile", "namespace": "demo.people", "fields": [{"name": "name", "type": "string"}]}
    payload = write_avro_bytes(user_schema, user_records)
    assert list(fastavro.reader(io.BytesIO(payload), reader_schema=reader_schema)) == [
        {"name": "Ada"},
        {"name": "Ben"},
        {"name": "Cy"},
    ]


@pytest.mark.depends_on("test_parse_schema_preserves_aliases_and_field_defaults")
def test_reader_schema_uses_field_alias_to_read_renamed_field():
    """Verifies: FASTAVRO-RESOLUTION-002."""
    import fastavro

    writer_schema = {"type": "record", "name": "AliasRecord", "fields": [{"name": "old_code", "type": "string"}]}
    reader_schema = {
        "type": "record",
        "name": "AliasRecord",
        "fields": [{"name": "new_code", "type": "string", "aliases": ["old_code"]}],
    }
    payload = write_avro_bytes(writer_schema, [{"old_code": "A-17"}])
    assert list(fastavro.reader(io.BytesIO(payload), reader_schema=reader_schema)) == [{"new_code": "A-17"}]


@pytest.mark.depends_on("test_parse_schema_preserves_aliases_and_field_defaults")
def test_reader_schema_uses_record_alias_to_match_writer_name():
    """Verifies: FASTAVRO-RESOLUTION-002."""
    import fastavro

    writer_schema = {"type": "record", "name": "LegacyOrder", "fields": [{"name": "id", "type": "int"}]}
    reader_schema = {"type": "record", "name": "Order", "aliases": ["LegacyOrder"], "fields": [{"name": "id", "type": "long"}]}
    payload = write_avro_bytes(writer_schema, [{"id": 17}])
    assert list(fastavro.reader(io.BytesIO(payload), reader_schema=reader_schema)) == [{"id": 17}]


@pytest.mark.depends_on("test_schemaless_reader_decodes_signed_integer_zigzag_bytes")
def test_schemaless_writer_reader_round_trip_nested_record():
    """Verifies: FASTAVRO-BINARY-001, FASTAVRO-BINARY-002."""
    import fastavro

    schema = {
        "type": "record",
        "name": "Nested",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "points", "type": {"type": "array", "items": "int"}},
            {"name": "props", "type": {"type": "map", "values": "string"}},
        ],
    }
    record = {"name": "N-1", "points": [3, 1, 4], "props": {"zone": "west"}}
    bio = io.BytesIO()
    fastavro.schemaless_writer(bio, schema, record)
    bio.seek(0)
    assert fastavro.schemaless_reader(bio, schema) == record


@pytest.mark.depends_on("test_validate_union_accepts_tuple_branch_hint")
def test_tuple_notation_selects_specific_record_union_branch():
    """Verifies: FASTAVRO-UNION-001."""
    import fastavro

    child = {"type": "record", "name": "Child", "fields": [{"name": "name", "type": "string"}, {"name": "grade", "type": "int", "default": 0}]}
    pet = {"type": "record", "name": "Pet", "fields": [{"name": "name", "type": "string"}, {"name": "species", "type": "string", "default": "cat"}]}
    schema = {"type": "record", "name": "Visit", "fields": [{"name": "guest", "type": [child, pet]}]}
    bio = io.BytesIO()
    fastavro.schemaless_writer(bio, schema, {"guest": ("Pet", {"name": "Pip", "species": "dog"})})
    bio.seek(0)
    assert fastavro.schemaless_reader(bio, schema, return_record_name=True) == {"guest": ("Pet", {"name": "Pip", "species": "dog"})}


@pytest.mark.depends_on("test_validate_union_accepts_tuple_branch_hint")
def test_record_type_hint_selects_record_branch_without_tuple():
    """Verifies: FASTAVRO-UNION-002."""
    import fastavro

    alpha = {"type": "record", "name": "Alpha", "fields": [{"name": "label", "type": "string"}]}
    beta = {"type": "record", "name": "Beta", "fields": [{"name": "label", "type": "string"}]}
    schema = {"type": "record", "name": "Choice", "fields": [{"name": "item", "type": [alpha, beta]}]}
    bio = io.BytesIO()
    fastavro.schemaless_writer(bio, schema, {"item": {"-type": "Beta", "label": "picked"}})
    bio.seek(0)
    assert fastavro.schemaless_reader(bio, schema, return_record_name=True) == {"item": ("Beta", {"label": "picked"})}


@pytest.mark.depends_on("test_validate_disable_tuple_notation_rejects_tuple_branch_hint")
def test_disable_tuple_notation_changes_writer_union_acceptance():
    """Verifies: FASTAVRO-UNION-003."""
    import fastavro

    one = {"type": "record", "name": "One", "fields": [{"name": "value", "type": "string"}]}
    two = {"type": "record", "name": "Two", "fields": [{"name": "value", "type": "string"}]}
    schema = {"type": "record", "name": "UnionHolder", "fields": [{"name": "payload", "type": [one, two]}]}
    with pytest.raises(ValueError):
        fastavro.schemaless_writer(io.BytesIO(), schema, {"payload": ("Two", {"value": "blocked"})}, disable_tuple_notation=True)


@pytest.mark.depends_on('test_validate_accepts_matching_record')
def test_block_reader_exposes_blocks_with_records_and_container_metadata(user_schema, user_records):
    """Verifies: FASTAVRO-BLOCK-001, FASTAVRO-CVI-002."""
    import fastavro

    payload = write_avro_bytes(user_schema, user_records, sync_interval=64, metadata={"batch": "B7"})
    block_iter = fastavro.block_reader(io.BytesIO(payload))
    blocks = list(block_iter)
    assert sum(block.num_records for block in blocks) == 3
    assert [record["name"] for block in blocks for record in block] == ["Ada", "Ben", "Cy"]
    assert block_iter.metadata["batch"] == "B7"
    assert {block.codec for block in blocks} == {"null"}


@pytest.mark.depends_on('test_validate_accepts_matching_record')
def test_deflate_codec_round_trip_uses_reader_codec_projection(user_schema, user_records):
    """Verifies: FASTAVRO-CONTAINER-004, FASTAVRO-CVI-002."""
    import fastavro

    payload = write_avro_bytes(user_schema, user_records, codec="deflate")
    avro_reader = fastavro.reader(io.BytesIO(payload))
    assert avro_reader.codec == "deflate"
    assert [record["tags"] for record in avro_reader] == [["core", "blue"], [], ["edge"]]


@pytest.mark.depends_on("test_json_writer_emits_one_json_object_per_record")
def test_json_writer_reader_round_trip_multiple_records(user_schema, user_records):
    """Verifies: FASTAVRO-JSON-001, FASTAVRO-JSON-003."""
    import fastavro

    out = io.StringIO()
    fastavro.json_writer(out, user_schema, user_records)
    assert list(fastavro.json_reader(io.StringIO(out.getvalue()), user_schema)) == user_records


@pytest.mark.depends_on("test_json_writer_wraps_union_values_by_default")
def test_json_union_wrapper_round_trip_with_reader_schema():
    """Verifies: FASTAVRO-JSON-002, FASTAVRO-JSON-004."""
    import fastavro

    writer_schema = {"type": "record", "name": "MaybeText2", "fields": [{"name": "value", "type": ["null", "string"]}]}
    reader_schema = {
        "type": "record",
        "name": "MaybeText2",
        "fields": [{"name": "value", "type": ["null", "string"]}, {"name": "seen", "type": "boolean", "default": True}],
    }
    out = io.StringIO()
    fastavro.json_writer(out, writer_schema, [{"value": "kept"}, {"value": None}])
    assert list(fastavro.json_reader(io.StringIO(out.getvalue()), writer_schema, reader_schema)) == [
        {"value": "kept", "seen": True},
        {"value": None, "seen": True},
    ]


@pytest.mark.depends_on("test_json_writer_can_omit_union_type_wrapper")
def test_unwrapped_union_json_is_readable_with_selected_branch_schema():
    """Verifies: FASTAVRO-JSON-002, FASTAVRO-CVI-004."""
    import fastavro

    schema = {"type": "record", "name": "MaybeText3", "fields": [{"name": "value", "type": ["null", "string"]}]}
    selected_branch_schema = {
        "type": "record",
        "name": "MaybeText3",
        "fields": [{"name": "value", "type": "string"}],
    }
    out = io.StringIO()
    fastavro.json_writer(out, schema, [{"value": "plain"}], write_union_type=False)
    assert list(fastavro.json_reader(io.StringIO(out.getvalue()), selected_branch_schema)) == [{"value": "plain"}]


@pytest.mark.depends_on("test_parse_schema_rejects_decimal_scale_larger_than_precision")
def test_decimal_logical_type_round_trips_through_binary_container():
    """Verifies: FASTAVRO-LOGICAL-002."""
    import fastavro

    schema = {
        "type": "record",
        "name": "Price",
        "fields": [{"name": "amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 8, "scale": 2}}],
    }
    records = [{"amount": Decimal("123.45")}, {"amount": Decimal("-6.70")}]
    payload = write_avro_bytes(schema, records)
    assert list(fastavro.reader(io.BytesIO(payload))) == records


@pytest.mark.depends_on("test_parse_schema_resolves_named_reference_with_shared_mapping")
def test_uuid_and_date_logical_types_round_trip_through_json():
    """Verifies: FASTAVRO-LOGICAL-002, FASTAVRO-JSON-001."""
    import fastavro

    identifier = uuid4()
    schema = {
        "type": "record",
        "name": "LogicalJson",
        "fields": [
            {"name": "id", "type": {"type": "string", "logicalType": "uuid"}},
            {"name": "day", "type": {"type": "int", "logicalType": "date"}},
        ],
    }
    out = io.StringIO()
    fastavro.json_writer(out, schema, [{"id": identifier, "day": date(2024, 2, 29)}])
    assert list(fastavro.json_reader(io.StringIO(out.getvalue()), schema)) == [
        {"id": UUID(str(identifier)), "day": date(2024, 2, 29)}
    ]


@pytest.mark.depends_on("test_public_logical_type_registries_are_mutable_mappings")
def test_custom_logical_type_hooks_apply_to_writer_and_reader():
    """Verifies: FASTAVRO-LOGICAL-001, FASTAVRO-LOGICAL-003."""
    import fastavro
    from fastavro.read import LOGICAL_READERS
    from fastavro.write import LOGICAL_WRITERS

    writer_key = "string-stageevent"
    reader_key = "string-stageevent"
    LOGICAL_WRITERS[writer_key] = lambda datum, schema: datum.isoformat() if isinstance(datum, datetime) else datum
    LOGICAL_READERS[reader_key] = lambda datum, writer_schema, reader_schema: datetime.fromisoformat(datum)
    schema = {
        "type": "record",
        "name": "CustomTime",
        "fields": [{"name": "created", "type": {"type": "string", "logicalType": "stageevent"}}],
    }
    try:
        payload = write_avro_bytes(schema, [{"created": datetime(2024, 5, 17, 8, 9, tzinfo=timezone.utc)}])
        assert list(fastavro.reader(io.BytesIO(payload))) == [{"created": datetime(2024, 5, 17, 8, 9, tzinfo=timezone.utc)}]
    finally:
        del LOGICAL_WRITERS[writer_key]
        del LOGICAL_READERS[reader_key]


@pytest.mark.depends_on("test_canonical_form_omits_doc_alias_and_orders_record_keys")
def test_parse_canonical_form_and_fingerprint_stay_stable_after_round_trip(user_schema, user_records):
    """Verifies: FASTAVRO-SCHEMA-009, FASTAVRO-SCHEMA-010, FASTAVRO-CVI-003."""
    import fastavro
    from fastavro.schema import fingerprint, to_parsing_canonical_form

    payload = write_avro_bytes(user_schema, user_records)
    read_schema = fastavro.reader(io.BytesIO(payload)).writer_schema
    assert to_parsing_canonical_form(read_schema) == to_parsing_canonical_form(user_schema)
    assert fingerprint(to_parsing_canonical_form(read_schema), "md5") == fingerprint(to_parsing_canonical_form(user_schema), "md5")


@pytest.mark.depends_on("test_flat_dict_repository_loads_schema_by_name")
def test_load_schema_with_flat_dict_repository_resolves_references(tmp_path):
    """Verifies: FASTAVRO-REPO-001, FASTAVRO-SCHEMA-004."""
    import fastavro
    from fastavro.repository import FlatDictRepository
    from fastavro.schema import load_schema

    (tmp_path / "Address.avsc").write_text(json.dumps({"type": "record", "name": "Address", "fields": [{"name": "city", "type": "string"}]}))
    (tmp_path / "Customer.avsc").write_text(
        json.dumps({"type": "record", "name": "Customer", "fields": [{"name": "address", "type": "Address"}]})
    )
    loaded = load_schema("Customer", repo=FlatDictRepository(str(tmp_path)))
    payload = write_avro_bytes(loaded, [{"address": {"city": "Oslo"}}])
    assert list(fastavro.reader(io.BytesIO(payload))) == [{"address": {"city": "Oslo"}}]


@pytest.mark.depends_on("test_parse_schema_resolves_named_reference_with_shared_mapping")
def test_load_schema_ordered_resolves_later_schema_files(tmp_path):
    """Verifies: FASTAVRO-REPO-003, FASTAVRO-SCHEMA-004."""
    import fastavro
    from fastavro.schema import load_schema_ordered

    child = tmp_path / "Child.avsc"
    parent = tmp_path / "Parent.avsc"
    child.write_text(json.dumps({"type": "record", "name": "Child", "fields": [{"name": "value", "type": "int"}]}))
    parent.write_text(json.dumps({"type": "record", "name": "Parent", "fields": [{"name": "child", "type": "Child"}]}))
    schema = load_schema_ordered([str(child), str(parent)])
    payload = write_avro_bytes(schema, [{"child": {"value": 23}}])
    assert list(fastavro.reader(io.BytesIO(payload))) == [{"child": {"value": 23}}]


@pytest.mark.depends_on("test_flat_dict_repository_missing_file_raises_repository_error")
def test_load_schema_missing_repository_reference_propagates_repository_error(tmp_path):
    """Verifies: FASTAVRO-REPO-002, FASTAVRO-ERR-003."""
    from fastavro.repository import FlatDictRepository
    from fastavro.schema import UnknownType
    from fastavro.schema import load_schema

    (tmp_path / "UsesMissing.avsc").write_text(
        json.dumps({"type": "record", "name": "UsesMissing", "fields": [{"name": "child", "type": "MissingChild"}]})
    )
    with pytest.raises(UnknownType):
        load_schema("UsesMissing", repo=FlatDictRepository(str(tmp_path)))


@pytest.mark.depends_on('test_validate_accepts_matching_record')
def test_cli_record_output_matches_reader_projection(tmp_path, user_schema, user_records):
    """Verifies: FASTAVRO-CLI-001, FASTAVRO-CVI-004."""
    import fastavro

    path = write_avro_file(tmp_path, user_schema, user_records, "cli-records.avro")
    result = run_fastavro_cli([path])
    assert result.returncode == 0
    with path.open("rb") as stream:
        assert json_lines(result.stdout.decode()) == list(fastavro.reader(stream))


@pytest.mark.depends_on('test_validate_accepts_matching_record')
def test_cli_pretty_print_outputs_json_array_style_records(tmp_path, user_schema, user_records):
    """Verifies: FASTAVRO-CLI-002."""
    path = write_avro_file(tmp_path, user_schema, user_records, "cli-pretty.avro")
    result = run_fastavro_cli(["--pretty", path])
    assert result.returncode == 0
    pretty = result.stdout.decode()
    assert '"name": "Ada"' in pretty
    assert pretty.count("{") >= 3


@pytest.mark.depends_on("test_canonical_form_omits_doc_alias_and_orders_record_keys")
def test_cli_schema_output_matches_container_schema(tmp_path, user_schema, user_records):
    """Verifies: FASTAVRO-CLI-003, FASTAVRO-CVI-004."""
    import fastavro
    from fastavro.schema import to_parsing_canonical_form

    path = write_avro_file(tmp_path, user_schema, user_records, "cli-schema.avro")
    result = run_fastavro_cli(["--schema", path])
    assert result.returncode == 0
    with path.open("rb") as stream:
        container_schema = fastavro.reader(stream).writer_schema
    assert to_parsing_canonical_form(json.loads(result.stdout.decode())) == to_parsing_canonical_form(container_schema)


@pytest.mark.depends_on('test_validate_accepts_matching_record')
def test_cli_metadata_output_includes_user_metadata_and_codec(tmp_path, user_schema, user_records):
    """Verifies: FASTAVRO-CLI-004, FASTAVRO-CVI-004."""
    path = write_avro_file(tmp_path, user_schema, user_records, "cli-meta.avro", metadata={"owner": "quality"}, codec="null")
    result = run_fastavro_cli(["--metadata", path])
    assert result.returncode == 0
    metadata = json.loads(result.stdout.decode())
    assert metadata["owner"] == "quality"
    assert metadata["avro.codec"] == "null"


@pytest.mark.depends_on("test_version_is_importable_string")
def test_cli_codecs_lists_required_builtin_codecs():
    """Verifies: FASTAVRO-CLI-005."""
    result = run_fastavro_cli(["--codecs"])
    assert result.returncode == 0
    codecs = set(result.stdout.decode().split())
    assert {"null", "deflate", "bzip2", "xz"}.issubset(codecs)


@pytest.mark.depends_on('test_validate_accepts_matching_record')
def test_cli_can_read_container_from_stdin(user_schema, user_records):
    """Verifies: FASTAVRO-CLI-006."""
    payload = write_avro_bytes(user_schema, user_records)
    result = run_fastavro_cli([], input_bytes=payload)
    assert result.returncode == 0
    assert [record["id"] for record in json_lines(result.stdout.decode())] == [31, 32, 33]


@pytest.mark.depends_on("test_version_is_importable_string")
def test_cli_version_uses_importable_package_version():
    """Verifies: FASTAVRO-CLI-007."""
    import fastavro

    result = run_fastavro_cli(["--version"])
    assert result.returncode == 0
    assert fastavro.__version__ in result.stdout.decode()


@pytest.mark.depends_on("test_parse_schema_unknown_named_type_raises_unknown_type")
def test_schema_parse_error_prevents_container_write():
    """Verifies: FASTAVRO-SCHEMA-005, FASTAVRO-CONTAINER-003."""
    import fastavro
    from fastavro.schema import UnknownType

    schema = {"type": "record", "name": "BadContainer", "fields": [{"name": "child", "type": "UnknownChild"}]}
    with pytest.raises(UnknownType):
        fastavro.writer(io.BytesIO(), schema, [{"child": {}}])


@pytest.mark.depends_on("test_validate_accepts_missing_defaulted_fields")
def test_writer_strict_allow_default_serializes_defaulted_field(user_schema):
    """Verifies: FASTAVRO-CONTAINER-003, FASTAVRO-VALID-004."""
    import fastavro

    payload = write_avro_bytes(user_schema, [{"id": 80, "name": "Defaulted"}], strict_allow_default=True)
    assert list(fastavro.reader(io.BytesIO(payload))) == [{"id": 80, "name": "Defaulted", "active": True, "score": None, "tags": []}]


@pytest.mark.depends_on("test_schemaless_writer_strict_rejects_missing_required_field")
def test_writer_strict_rejects_missing_defaulted_field_when_not_allowed(user_schema):
    """Verifies: FASTAVRO-CONTAINER-003, FASTAVRO-VALID-003."""
    import fastavro

    with pytest.raises(ValueError):
        fastavro.writer(io.BytesIO(), user_schema, [{"id": 80, "name": "Defaulted"}], strict=True)


@pytest.mark.depends_on("test_json_reader_reads_union_wrapper_payload")
def test_return_named_type_marks_selected_named_union_member():
    """Verifies: FASTAVRO-UNION-004."""
    import fastavro

    first = {"type": "record", "name": "FirstUnion", "fields": [{"name": "value", "type": "int"}]}
    second = {"type": "record", "name": "SecondUnion", "fields": [{"name": "value", "type": "int"}]}
    schema = {"type": "record", "name": "ContainerUnion", "fields": [{"name": "payload", "type": [first, second]}]}
    payload = write_avro_bytes(schema, [{"payload": ("SecondUnion", {"value": 81})}])
    assert list(fastavro.reader(io.BytesIO(payload), return_named_type=True)) == [
        {"payload": ("SecondUnion", {"value": 81})}
    ]


@pytest.mark.depends_on("test_parse_schema_preserves_aliases_and_field_defaults")
def test_enum_reader_schema_uses_default_for_unknown_writer_symbol():
    """Verifies: FASTAVRO-RESOLUTION-003."""
    import fastavro

    writer_schema = {
        "type": "record",
        "name": "EnumMove",
        "fields": [{"name": "status", "type": {"type": "enum", "name": "WriterStatus", "symbols": ["NEW", "OLD"]}}],
    }
    reader_schema = {
        "type": "record",
        "name": "EnumMove",
        "fields": [{"name": "status", "type": {"type": "enum", "name": "WriterStatus", "symbols": ["NEW"], "default": "NEW"}}],
    }
    payload = write_avro_bytes(writer_schema, [{"status": "OLD"}])
    assert list(fastavro.reader(io.BytesIO(payload), reader_schema=reader_schema)) == [{"status": "NEW"}]
