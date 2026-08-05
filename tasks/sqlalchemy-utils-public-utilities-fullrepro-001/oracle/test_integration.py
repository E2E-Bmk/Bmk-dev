from pathlib import Path

import pytest
import sqlalchemy as sa
from furl import furl
from sqlalchemy.orm import Session
from sqlalchemy_utils import (
    Choice,
    Password,
    database_exists,
    drop_database,
    get_bind,
    get_class_by_table,
    get_column_key,
    get_columns,
    get_mapper,
    get_primary_keys,
    get_tables,
    get_type,
    has_index,
    has_unique_index,
    identity,
    naturally_equivalent,
    escape_like,
    table_name,
)

from conftest import Base, Category, Record, fresh_record, make_engine, seed_records


@pytest.mark.depends_on(
    "test_uuid_type_coerces_string_to_uuid",
    "test_url_type_coerces_string_to_furl",
)
def test_coercion_types_survive_flush_expire_and_reload(session):
    record = fresh_record(id=30, category_id=None)
    record.category = Category(id=30, name="coerced")
    session.add(record)
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 30)
    assert str(loaded.token) == "00000000-0000-0000-0000-000000000010"
    assert isinstance(loaded.website, furl)
    assert loaded.website.host == "fresh.example"


@pytest.mark.depends_on(
    "test_uuid_type_round_trips_through_sqlite",
    "test_get_primary_keys_returns_ordered_primary_key",
)
def test_uuid_identity_and_primary_key_projection_agree(session):
    data = seed_records(session)
    loaded = session.get(Record, data["alpha"].id)
    assert identity(loaded) == (1,)
    assert get_primary_keys(loaded)["id"].name == "id"
    assert loaded.token.hex.endswith("0001")


@pytest.mark.depends_on(
    "test_url_type_round_trips_as_furl",
    "test_nullable_custom_values_round_trip_as_none",
)
def test_url_query_mutation_persists_as_public_url_object(session):
    data = seed_records(session)
    data["alpha"].website = "https://example.com/start?x=1&view=compact"
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 1)
    assert isinstance(loaded.website, furl)
    assert loaded.website.args["view"] == "compact"
    assert loaded.website.host == "example.com"


@pytest.mark.depends_on(
    "test_password_type_round_trips_and_verifies_secret",
    "test_nullable_custom_values_round_trip_as_none",
)
def test_password_update_rehashes_and_keeps_row_identity(session):
    data = seed_records(session)
    record = data["alpha"]
    assert isinstance(record.password, Password)
    old_identity = identity(record)
    record.password = "new-secret"
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 1)
    assert identity(loaded) == old_identity
    assert loaded.password == "new-secret"
    assert loaded.password != "alpha-secret"


@pytest.mark.depends_on(
    "test_choice_type_coerces_code_to_choice",
    "test_choice_type_round_trips_code_and_label",
)
def test_choice_filter_and_projection_agree_after_round_trip(session):
    seed_records(session)
    rows = (
        session.query(Record)
        .filter(Record.status == "new")
        .order_by(Record.id)
        .all()
    )
    assert [item.status.code for item in rows] == ["new", "new"]
    assert [item.status.value for item in rows] == ["New", "New"]


@pytest.mark.depends_on(
    "test_scalar_list_type_coerces_integer_items_on_load",
    "test_scalar_list_type_coerces_text_items_on_load",
)
def test_scalar_lists_update_as_typed_python_collections(session):
    seed_records(session)
    record = session.get(Record, 1)
    record.labels = ["cyan", "magenta"]
    record.scores = [13, 21]
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 1)
    assert loaded.labels == ["cyan", "magenta"]
    assert loaded.scores == [13, 21]
    assert all(isinstance(item, int) for item in loaded.scores)


@pytest.mark.depends_on(
    "test_json_type_round_trips_nested_data",
    "test_nullable_custom_values_round_trip_as_none",
)
def test_json_payload_update_is_visible_in_query_and_instance_views(session):
    seed_records(session)
    record = session.get(Record, 3)
    record.payload = {"kind": "gamma", "rank": 30}
    session.commit()
    row = session.query(Record.payload).filter(Record.id == 3).one()
    session.expire_all()
    assert row[0]["rank"] == 30
    assert session.get(Record, 3).payload["kind"] == "gamma"


@pytest.mark.depends_on(
    "test_nullable_custom_values_round_trip_as_none",
    "test_uuid_type_round_trips_through_sqlite",
)
def test_nullable_values_can_be_cleared_without_losing_required_values(session):
    seed_records(session)
    record = session.get(Record, 1)
    record.website = None
    record.password = None
    record.payload = None
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 1)
    assert loaded.token is not None
    assert loaded.website is None
    assert loaded.password is None
    assert loaded.payload is None


@pytest.mark.depends_on(
    "test_model_table_exposes_public_columns",
    "test_get_columns_returns_mapped_columns",
)
def test_model_and_column_inspection_agree_on_schema(session):
    assert set(get_columns(Record).keys()) == {
        "id",
        "title",
        "token",
        "website",
        "password",
        "status",
        "labels",
        "scores",
        "payload",
        "active",
        "note",
        "category_id",
    }
    assert set(Record.__table__.c.keys()) >= {"id", "title_db", "token"}
    assert table_name(Record) == Record.__tablename__
    assert get_column_key(Record, Record.__table__.c.title_db) == "title"


@pytest.mark.depends_on(
    "test_get_type_handles_column_and_relationship",
    "test_get_tables_handles_model_and_attribute",
)
def test_inspection_reports_scalar_and_relationship_types_together(session):
    assert isinstance(get_type(Record.title), sa.String)
    assert get_type(Record.category) is Category
    assert get_tables(Record.category) == [Record.__table__]
    assert get_mapper(Record.category).class_ is Record


@pytest.mark.depends_on(
    "test_get_mapper_handles_class_instance_and_table",
    "test_get_class_by_table_finds_declarative_model",
)
def test_mapper_and_class_lookup_round_trip_through_table(session):
    assert get_mapper(Record.__table__) is sa.inspect(Record)
    assert get_class_by_table(Base, Record.__table__) is Record
    assert get_mapper(get_class_by_table(Base, Record.__table__)).class_ is Record


@pytest.mark.depends_on(
    "test_get_bind_returns_connection_bind",
    "test_database_exists_accepts_sqlite_memory_urls",
)
def test_bind_helper_matches_engine_used_for_sqlite_queries(session):
    engine = session.get_bind()
    with engine.connect() as connection:
        assert get_bind(connection) is connection
        assert connection.scalar(sa.select(sa.literal(1))) == 1


@pytest.mark.depends_on(
    "test_index_helpers_distinguish_indexed_and_unique_columns",
    "test_model_table_exposes_public_columns",
)
def test_index_helpers_match_declared_schema_constraints(session):
    assert has_index(Record.__table__.c.active)
    assert has_unique_index(Category.__table__.c.name)
    assert not has_index(Record.__table__.c.note)


@pytest.mark.depends_on(
    "test_database_exists_accepts_sqlite_memory_urls",
    "test_escape_like_escapes_wildcards_and_escape_character",
)
def test_sqlite_file_lifecycle_reports_exists_then_missing(tmp_path):
    path = tmp_path / "lifecycle.sqlite3"
    url = f"sqlite:///{path}"
    assert not database_exists(url)
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    engine.dispose()
    assert database_exists(url)
    drop_database(url)
    assert not Path(path).exists()


@pytest.mark.depends_on(
    "test_database_exists_accepts_sqlite_memory_urls",
    "test_model_table_exposes_public_columns",
)
def test_sqlite_database_helper_creates_a_usable_file(tmp_path):
    path = tmp_path / "created.sqlite3"
    url = f"sqlite:///{path}"
    from sqlalchemy_utils import create_database

    create_database(url)
    assert database_exists(url)
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = Category(id=40, name="created")
        session.add(category)
        session.commit()
        assert session.get(Category, 40).name == "created"
    engine.dispose()
    drop_database(url)


@pytest.mark.depends_on(
    "test_escape_like_escapes_wildcards_and_escape_character",
    "test_model_table_exposes_public_columns",
)
def test_escaped_like_pattern_selects_literal_wildcards(session):
    session.add(
        Category(id=50, name="100%_ready*")
    )
    session.commit()
    pattern = "%" + escape_like("100%_ready*") + "%"
    row = (
        session.query(Category)
        .filter(Category.name.like(pattern, escape="*"))
        .one()
    )
    assert row.name == "100%_ready*"


@pytest.mark.depends_on(
    "test_identity_and_naturally_equivalent_use_persisted_values",
    "test_uuid_type_round_trips_through_sqlite",
)
def test_natural_equivalence_compares_two_loaded_value_objects(session):
    data = seed_records(session)
    first = session.get(Record, 1)
    second = fresh_record(
        id=1,
        title=first.title,
        token=first.token,
        website=str(first.website),
        password=first.password,
        status=first.status,
        labels=list(first.labels),
        scores=list(first.scores),
        payload=dict(first.payload),
        active=first.active,
        note=first.note,
        category_id=first.category_id,
    )
    assert identity(first) == identity(second)
    assert naturally_equivalent(first, second)
    assert first.token == data["alpha"].token


@pytest.mark.depends_on(
    "test_choice_type_round_trips_code_and_label",
    "test_scalar_list_type_coerces_text_items_on_load",
)
def test_deterministic_projection_orders_choice_and_list_values(session):
    seed_records(session)
    rows = (
        session.query(Record)
        .order_by(Record.id)
        .with_entities(Record.title, Record.status, Record.labels)
        .all()
    )
    assert [(title, status.code, labels) for title, status, labels in rows] == [
        ("Alpha", "new", ["red", "blue"]),
        ("Beta", "done", ["green"]),
        ("Gamma", "new", []),
    ]


@pytest.mark.depends_on(
    "test_password_type_coerces_secret_to_password",
    "test_json_type_round_trips_nested_data",
)
def test_new_model_values_are_coerced_before_session_add(session):
    category = Category(id=60, name="new-values")
    record = fresh_record(
        id=60,
        category=category,
        category_id=None,
        password="before-add",
        payload={"stage": "new"},
    )
    assert isinstance(record.password, Password)
    assert record.password == "before-add"
    assert record.payload == {"stage": "new"}
    session.add(record)
    session.commit()
    assert session.get(Record, 60).password == "before-add"


@pytest.mark.depends_on(
    "test_get_bind_returns_connection_bind",
    "test_uuid_type_round_trips_through_sqlite",
)
def test_engine_and_session_bind_support_same_round_trip(session):
    data = seed_records(session)
    engine = session.get_bind()
    with Session(engine) as second_session:
        loaded = second_session.get(Record, data["beta"].id)
        assert loaded.title == "Beta"


@pytest.mark.depends_on(
    "test_get_primary_keys_returns_ordered_primary_key",
    "test_get_columns_returns_mapped_columns",
)
def test_primary_key_and_columns_remain_stable_after_flush(session):
    category = Category(id=70, name="stable")
    record = fresh_record(id=70, category=category, category_id=None)
    session.add(record)
    session.flush()
    assert list(get_primary_keys(record)) == ["id"]
    assert get_columns(record)["title"].name == "title_db"
    assert identity(record) == (70,)


@pytest.mark.depends_on(
    "test_database_exists_accepts_sqlite_memory_urls",
    "test_uuid_type_round_trips_through_sqlite",
)
def test_file_database_round_trip_preserves_custom_values(tmp_path):
    path = tmp_path / "records.sqlite3"
    url = f"sqlite:///{path}"
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = Category(id=80, name="file")
        session.add(category)
        session.add(fresh_record(id=80, category=category, category_id=None))
        session.commit()
    engine.dispose()
    assert database_exists(url)
    engine = make_engine(url)
    with Session(engine) as session:
        loaded = session.get(Record, 80)
        assert loaded.title == "Fresh"
        assert loaded.token.hex.endswith("0010")
        assert loaded.labels == ["one", "two"]
    engine.dispose()
    drop_database(url)


@pytest.mark.depends_on(
    "test_choice_type_rejects_unknown_code",
    "test_model_table_exposes_public_columns",
)
def test_invalid_choice_does_not_insert_a_partial_row(session):
    with pytest.raises(KeyError):
        session.add(fresh_record(id=81, status="bad"))
    session.rollback()
    assert session.query(Record).count() == 0


@pytest.mark.depends_on(
    "test_scalar_list_type_rejects_separator_in_item",
    "test_scalar_list_type_coerces_text_items_on_load",
)
def test_scalar_list_validation_keeps_existing_rows_intact(session):
    session.add(
        Category(id=82, name="list-validation")
    )
    session.add(fresh_record(id=82, category_id=82))
    session.commit()
    session.get(Record, 82).labels = ["valid", "invalid,value"]
    with pytest.raises(sa.exc.StatementError):
        session.flush()
    session.rollback()
    assert session.get(Record, 82).labels == ["one", "two"]


@pytest.mark.depends_on(
    "test_nullable_custom_values_round_trip_as_none",
    "test_model_table_exposes_public_columns",
)
def test_default_active_value_is_persisted_alongside_custom_types(session):
    category = Category(id=83, name="defaults")
    record = Record(
        id=83,
        title="Defaulted",
        token="00000000-0000-0000-0000-000000000083",
        website=None,
        password=None,
        status="new",
        labels=[],
        scores=[83],
        payload=None,
        category=category,
    )
    session.add(record)
    session.commit()
    loaded = session.get(Record, 83)
    assert loaded.active is True
    assert loaded.token is not None
    assert loaded.status.code == "new"


@pytest.mark.depends_on(
    "test_uuid_type_round_trips_through_sqlite",
    "test_json_type_round_trips_nested_data",
)
def test_update_and_reload_preserve_uuid_and_json_contract(session):
    seed_records(session)
    record = session.get(Record, 1)
    record.payload = {"kind": "changed", "items": [2, 4]}
    record.token = "00000000-0000-0000-0000-000000000099"
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 1)
    assert str(loaded.token).endswith("0099")
    assert loaded.payload == {"kind": "changed", "items": [2, 4]}


@pytest.mark.depends_on(
    "test_get_class_by_table_finds_declarative_model",
    "test_table_name_handles_model_and_attribute",
)
def test_category_relationship_uses_public_class_and_table_helpers(session):
    data = seed_records(session)
    category = session.get(Category, data["primary"].id)
    assert get_class_by_table(Base, category.__table__) is Category
    assert table_name(category.__class__) == "category"
    assert [record.title for record in category.records] == ["Alpha", "Beta"]


@pytest.mark.depends_on(
    "test_index_helpers_distinguish_indexed_and_unique_columns",
    "test_get_columns_returns_mapped_columns",
)
def test_schema_helpers_agree_after_metadata_creation(session):
    Base.metadata.create_all(session.get_bind())
    assert list(get_primary_keys(Category)) == ["id"]
    assert has_unique_index(Category.__table__.c.name)
    assert "active" in get_columns(Record)


@pytest.mark.depends_on(
    "test_password_type_round_trips_and_verifies_secret",
    "test_choice_type_round_trips_code_and_label",
)
def test_end_to_end_public_utility_workflow(session):
    data = seed_records(session)
    record = data["alpha"]
    record.website = "https://example.net/final?mode=full"
    record.password = "final-secret"
    record.status = "done"
    record.labels = ["final", "checked"]
    record.payload = {"complete": True, "rank": 10}
    session.commit()
    session.expire_all()
    loaded = session.get(Record, 1)
    assert loaded.website.host == "example.net"
    assert loaded.password == "final-secret"
    assert loaded.status == "done"
    assert loaded.labels == ["final", "checked"]
    assert loaded.payload["complete"] is True


@pytest.mark.depends_on(
    "test_get_bind_returns_connection_bind",
    "test_model_table_exposes_public_columns",
)
def test_connection_bind_and_schema_inspection_share_sqlite_state(session):
    engine = session.get_bind()
    with engine.connect() as connection:
        assert get_bind(connection) is connection
        tables = set(sa.inspect(connection).get_table_names())
    assert {"category", "record"} <= tables
    assert Record.__table__.name in tables
