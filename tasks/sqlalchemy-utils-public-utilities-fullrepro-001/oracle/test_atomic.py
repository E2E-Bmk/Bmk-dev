import uuid

import pytest
import sqlalchemy as sa
from furl import furl
from sqlalchemy_utils import (
    Choice,
    ChoiceType,
    JSONType,
    Password,
    PasswordType,
    ScalarListType,
    URLType,
    UUIDType,
    database_exists,
    escape_like,
    get_bind,
    get_class_by_table,
    get_column_key,
    get_columns,
    get_declarative_base,
    get_mapper,
    get_primary_keys,
    get_tables,
    get_type,
    has_index,
    has_unique_index,
    identity,
    naturally_equivalent,
    table_name,
)
from sqlalchemy.orm import Session

from conftest import Base, Category, Record, STATUS_CHOICES, fresh_record, make_engine


def test_uuid_type_coerces_string_to_uuid():
    record = fresh_record(token="00000000-0000-0000-0000-000000000011")
    assert record.token == uuid.UUID("00000000-0000-0000-0000-000000000011")
    assert isinstance(record.token, uuid.UUID)


def test_uuid_type_round_trips_through_sqlite():
    engine = make_engine()
    Base.metadata.create_all(engine)
    token = uuid.UUID("00000000-0000-0000-0000-000000000012")
    with Session(engine) as session:
        session.add(fresh_record(id=12, token=token))
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 12)
        assert loaded.token == token
    engine.dispose()


def test_uuid_type_exposes_binary_storage_option():
    column_type = Record.__table__.c.token.type
    assert isinstance(column_type, UUIDType)
    assert column_type.binary is False


def test_url_type_coerces_string_to_furl():
    record = fresh_record(website="https://example.com/path?mode=full")
    assert isinstance(record.website, furl)
    assert record.website.args["mode"] == "full"


def test_url_type_round_trips_as_furl():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(fresh_record(id=13, website="https://example.com/a?x=1"))
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 13)
        assert isinstance(loaded.website, furl)
        assert str(loaded.website) == "https://example.com/a?x=1"
    engine.dispose()


def test_password_type_coerces_secret_to_password():
    record = fresh_record(password="secret-value")
    assert isinstance(record.password, Password)
    assert record.password == "secret-value"


def test_password_type_round_trips_and_verifies_secret():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(fresh_record(id=14, password="persisted-secret"))
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 14)
        assert isinstance(loaded.password, Password)
        assert loaded.password == "persisted-secret"
        assert loaded.password != "wrong-secret"
    engine.dispose()


def test_choice_type_coerces_code_to_choice():
    record = fresh_record(status="done")
    assert isinstance(record.status, Choice)
    assert record.status.code == "done"
    assert str(record.status) == "Done"


def test_choice_type_round_trips_code_and_label():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(fresh_record(id=15, status="done"))
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 15)
        assert loaded.status.code == "done"
        assert loaded.status.value == "Done"
    engine.dispose()


def test_scalar_list_type_coerces_text_items_on_load():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(fresh_record(id=16, labels=["first", "second"]))
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 16)
        assert loaded.labels == ["first", "second"]
    engine.dispose()


def test_scalar_list_type_coerces_integer_items_on_load():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(fresh_record(id=17, scores=[4, 9]))
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 17)
        assert loaded.scores == [4, 9]
        assert all(isinstance(item, int) for item in loaded.scores)
    engine.dispose()


def test_json_type_round_trips_nested_data():
    engine = make_engine()
    Base.metadata.create_all(engine)
    payload = {"items": [1, {"enabled": True}], "label": "nested"}
    with Session(engine) as session:
        session.add(fresh_record(id=18, payload=payload))
        session.commit()
        session.expire_all()
        assert session.get(Record, 18).payload == payload
    engine.dispose()


def test_nullable_custom_values_round_trip_as_none():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            fresh_record(
                id=19,
                website=None,
                password=None,
                payload=None,
                note=None,
            )
        )
        session.commit()
        session.expire_all()
        loaded = session.get(Record, 19)
        assert loaded.website is None
        assert loaded.password is None
        assert loaded.payload is None
        assert loaded.note is None
    engine.dispose()


def test_choice_type_rejects_unknown_code():
    with pytest.raises(KeyError):
        fresh_record(status="unknown")


def test_scalar_list_type_rejects_separator_in_item():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(fresh_record(id=20, labels=["ok", "bad,item"]))
        with pytest.raises(sa.exc.StatementError):
            session.flush()
    engine.dispose()


def test_model_table_exposes_public_columns():
    assert Record.__tablename__ == "record"
    assert {"id", "title_db", "token", "website", "password"} <= set(
        Record.__table__.c.keys()
    )


def test_get_columns_returns_mapped_columns():
    columns = get_columns(Record)
    assert {"id", "title", "token", "category_id"} <= set(columns.keys())


def test_get_primary_keys_returns_ordered_primary_key():
    primary_keys = get_primary_keys(Record)
    assert list(primary_keys) == ["id"]
    assert primary_keys["id"] is Record.__table__.c.id


def test_get_type_handles_column_and_relationship():
    assert isinstance(get_type(Record.title), sa.String)
    assert get_type(Record.category) is Category


def test_get_mapper_handles_class_instance_and_table():
    assert get_mapper(Record).class_ is Record
    assert get_mapper(Record()).class_ is Record
    assert get_mapper(Record.__table__).class_ is Record


def test_get_tables_handles_model_and_attribute():
    assert get_tables(Record) == [Record.__table__]
    assert get_tables(Record.title) == [Record.__table__]


def test_table_name_handles_model_and_attribute():
    assert table_name(Record) == "record"
    assert table_name(Record.title) == "record"


def test_get_column_key_resolves_database_column_alias():
    assert get_column_key(Record, Record.__table__.c.title_db) == "title"


def test_get_declarative_base_returns_registry_base():
    assert get_declarative_base(Record) is Base


def test_get_bind_returns_connection_bind():
    engine = make_engine()
    with engine.connect() as connection:
        assert get_bind(connection) is connection
    engine.dispose()


def test_index_helpers_distinguish_indexed_and_unique_columns():
    assert has_index(Record.__table__.c.active)
    assert not has_unique_index(Record.__table__.c.active)
    assert has_unique_index(Category.__table__.c.name)


def test_database_exists_accepts_sqlite_memory_urls():
    assert database_exists("sqlite://")
    assert database_exists("sqlite:///:memory:")


def test_escape_like_escapes_wildcards_and_escape_character():
    assert escape_like("a%b_c*d") == "a*%b*_c**d"


def test_identity_and_naturally_equivalent_use_persisted_values():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        record = fresh_record(id=21)
        session.add(record)
        session.flush()
        equivalent = fresh_record(id=21, password=record.password)
        equivalent.category_id = record.category_id
        assert identity(record) == (21,)
        assert naturally_equivalent(record, equivalent)
    engine.dispose()


def test_get_class_by_table_finds_declarative_model():
    assert get_class_by_table(Base, Record.__table__) is Record
