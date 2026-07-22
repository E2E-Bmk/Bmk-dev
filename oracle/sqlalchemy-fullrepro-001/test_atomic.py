# Spec2Repo oracle - atomic tests for sqlalchemy-fullrepro-001
import datetime as dt
from decimal import Decimal
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import exc
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    contains_eager,
    joinedload,
    mapped_column,
    object_session,
    raiseload,
    relationship,
    selectinload,
    sessionmaker,
)
from sqlalchemy.orm import exc as orm_exc


def assert_raises(expected, fn):
    try:
        fn()
    except expected:
        return
    except Exception as err:
        raise AssertionError(f"expected {expected}, got {type(err)}") from err
    raise AssertionError(f"expected {expected} to be raised")


def user_address_tables():
    metadata = sa.MetaData()
    users = sa.Table(
        "user_account",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(30), nullable=False, unique=True),
        sa.Column("fullname", sa.String),
    )
    addresses = sa.Table(
        "address",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.ForeignKey("user_account.id"), nullable=False),
        sa.Column("email_address", sa.String, nullable=False),
    )
    return metadata, users, addresses


class UserBase(DeclarativeBase):
    pass


class User(UserBase):
    __tablename__ = "orm_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(30))
    fullname: Mapped[Optional[str]]
    addresses: Mapped[List["Address"]] = relationship(back_populates="user")


class Address(UserBase):
    __tablename__ = "orm_address"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("orm_user.id"))
    email_address: Mapped[str]
    user: Mapped[User] = relationship(back_populates="addresses")


def make_user_engine():
    engine = sa.create_engine("sqlite://")
    UserBase.metadata.create_all(engine)
    return engine


def seed_users(engine):
    with Session(engine) as session:
        sandy = User(
            name="sandy",
            fullname="Sandy Cheeks",
            addresses=[
                Address(email_address="sandy@example.org"),
                Address(email_address="sandy@work.example"),
            ],
        )
        patrick = User(name="patrick", fullname="Patrick Star")
        session.add_all([sandy, patrick])
        session.commit()


def test_result_rows_support_positions_attributes_and_mappings():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "people",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), [{"name": "sandy"}, {"name": "patrick"}])
        row = conn.execute(sa.select(table.c.id, table.c.name).order_by(table.c.id)).first()
        mapping = conn.execute(
            sa.select(table.c.name.label("person_name")).where(table.c.name == "patrick")
        ).mappings().one()

    id_value, name_value = row
    assert id_value == 1
    assert name_value == "sandy"
    assert row[1] == "sandy"
    assert row.name == "sandy"
    assert row._mapping["id"] == 1
    assert mapping["person_name"] == "patrick"


def test_select_where_bindparams_order_by_limit_offset():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "numbers",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("value", sa.Integer),
        sa.Column("name", sa.String),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(
            sa.insert(table),
            [
                {"value": 1, "name": "one"},
                {"value": 2, "name": "two"},
                {"value": 3, "name": "three"},
                {"value": 4, "name": "four"},
            ],
        )
        stmt = (
            sa.select(table.c.name)
            .where(table.c.value > sa.bindparam("minimum"))
            .order_by(sa.desc(table.c.value))
            .limit(2)
            .offset(1)
        )
        names = conn.execute(stmt, {"minimum": 1}).scalars().all()

    assert names == ["three", "two"]


def test_functions_cast_type_coerce_and_labels_return_expected_values():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "metrics",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("amount", sa.String),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), [{"amount": "10"}, {"amount": "20"}])
        stmt = sa.select(
            sa.func.count().label("row_count"),
            sa.cast(sa.func.sum(sa.cast(table.c.amount, sa.Integer)), sa.String).label("total_text"),
            sa.type_coerce(sa.literal("plain"), sa.String).label("coerced"),
        )
        row = conn.execute(stmt).one()

    assert row.row_count == 2
    assert row.total_text == "30"
    assert row.coerced == "plain"


def test_sqlite_dialect_date_datetime_time_type_roundtrip():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "dialect_temporal",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("d", sqlite.DATE),
        sa.Column("dt", sqlite.DATETIME),
        sa.Column("t", sqlite.TIME),
    )
    table.create(engine)

    with engine.begin() as conn:
        values = {
            "id": 1,
            "d": dt.date(2024, 12, 31),
            "dt": dt.datetime(2024, 12, 31, 5, 6, 7, 890123),
            "t": dt.time(5, 6, 7, 890123),
        }
        conn.execute(sa.insert(table), values)
        typed = conn.execute(sa.select(table.c.d, table.c.dt, table.c.t)).one()
        raw = conn.execute(sa.text("select d, dt, t from dialect_temporal")).one()

    assert typed.d == dt.date(2024, 12, 31)
    assert typed.dt == dt.datetime(2024, 12, 31, 5, 6, 7, 890123)
    assert typed._mapping["t"] == dt.time(5, 6, 7, 890123)
    assert isinstance(raw.d, str)


def test_declarative_base_function_and_inferred_nullable_types():
    Base = sa.orm.declarative_base()

    class Thing(Base):
        __tablename__ = "thing"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]
        note: Mapped[Optional[str]]

    thing = Thing(name="widget", note=None)
    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        session.add(thing)
        session.commit()

    assert Thing.__table__.c.name.nullable is False
    assert Thing.__table__.c.note.nullable is True
    assert thing.id == 1


def test_result_cardinality_errors_for_scalar_one():
    engine = sa.create_engine("sqlite://")
    table = sa.Table("cardinality", sa.MetaData(), sa.Column("value", sa.Integer))
    table.create(engine)

    with engine.begin() as conn:
        assert_raises(exc.NoResultFound, lambda: conn.execute(sa.select(table.c.value)).scalars().one())
        conn.execute(sa.insert(table), [{"value": 1}, {"value": 2}])
        assert_raises(
            exc.MultipleResultsFound,
            lambda: conn.execute(sa.select(table.c.value)).scalars().one(),
        )


def test_missing_table_and_broken_foreign_key_errors():
    engine = sa.create_engine("sqlite://")

    assert_raises(
        exc.NoSuchTableError,
        lambda: sa.Table("missing", sa.MetaData(), autoload_with=engine),
    )

    broken = sa.Table(
        "broken",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("other_id", sa.Integer, sa.ForeignKey("missing.id")),
    )
    assert_raises(exc.NoReferencedTableError, lambda: broken.create(engine))


def test_join_inference_errors_for_missing_and_ambiguous_foreign_keys():
    no_fk_metadata = sa.MetaData()
    left = sa.Table("left_t", no_fk_metadata, sa.Column("id", sa.Integer, primary_key=True))
    right = sa.Table("right_t", no_fk_metadata, sa.Column("id", sa.Integer, primary_key=True))
    assert_raises(exc.NoForeignKeysError, lambda: sa.select(left).join_from(left, right).compile())

    ambiguous_metadata = sa.MetaData()
    parent = sa.Table("parent_t", ambiguous_metadata, sa.Column("id", sa.Integer, primary_key=True))
    child = sa.Table(
        "child_t",
        ambiguous_metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("mother_id", sa.ForeignKey("parent_t.id")),
        sa.Column("father_id", sa.ForeignKey("parent_t.id")),
    )
    assert_raises(exc.AmbiguousForeignKeysError, lambda: sa.select(parent).join_from(parent, child).compile())


def test_unmapped_instance_errors():
    class Plain:
        pass

    engine = make_user_engine()

    with Session(engine) as session:
        assert_raises(orm_exc.UnmappedInstanceError, lambda: session.add(Plain()))


def test_top_level_import_surface_exposes_common_core_and_orm_names():
    assert callable(sa.create_engine)
    assert callable(sa.inspect)
    assert sa.Integer is not None
    assert sa.String is not None
    assert sa.orm.Session is Session
    assert callable(sa.orm.relationship)
    assert sqlite.insert is not None


def test_textual_statement_and_bound_parameters_do_not_interpolate_values():
    engine = sa.create_engine("sqlite://")

    with engine.connect() as conn:
        value = conn.scalar(sa.text("select :name"), {"name": "sandy"})
        dangerous = conn.scalar(sa.text("select :payload"), {"payload": "1; drop table nope"})

    assert value == "sandy"
    assert dangerous == "1; drop table nope"


def test_boolean_true_false_null_and_between_expressions_execute():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "boolean_cases",
        sa.MetaData(),
        sa.Column("name", sa.String, primary_key=True),
        sa.Column("enabled", sa.Boolean),
        sa.Column("score", sa.Integer),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(
            sa.insert(table),
            [
                {"name": "inside", "enabled": True, "score": 5},
                {"name": "outside", "enabled": False, "score": None},
            ],
        )
        names = conn.execute(
            sa.select(table.c.name).where(
                table.c.enabled.is_(sa.true()),
                table.c.score.between(1, 10),
                table.c.score.is_not(sa.null()),
            )
        ).scalars().all()

    assert names == ["inside"]


def test_session_get_accepts_tuple_for_composite_primary_key():
    engine = sa.create_engine("sqlite://")
    Base = sa.orm.declarative_base()

    class Pair(Base):
        __tablename__ = "pair"
        left_id: Mapped[int] = mapped_column(primary_key=True)
        right_id: Mapped[int] = mapped_column(primary_key=True)
        label: Mapped[str]

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Pair(left_id=1, right_id=2, label="joined"))
        session.commit()
        loaded = session.get(Pair, (1, 2))

    assert loaded.label == "joined"


def test_raiseload_option_raises_for_many_to_one_access():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        address = session.scalars(sa.select(Address).options(raiseload(Address.user)).where(Address.email_address == "sandy@example.org")).one()
        assert_raises(exc.InvalidRequestError, lambda: address.user)


def test_sqlite_uppercase_type_names_compile_and_roundtrip():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "uppercase_types",
        sa.MetaData(),
        sa.Column("id", sqlite.INTEGER, primary_key=True),
        sa.Column("body", sqlite.TEXT),
        sa.Column("flag", sqlite.BOOLEAN),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), {"body": "hello", "flag": True})
        row = conn.execute(sa.select(table.c.body, table.c.flag)).one()

    assert row.body == "hello"
    assert row.flag is True


def test_metadata_sorted_tables_places_referenced_table_first():
    metadata = sa.MetaData()
    parent = sa.Table("parent", metadata, sa.Column("id", sa.Integer, primary_key=True))
    child = sa.Table(
        "child",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("parent_id", sa.ForeignKey("parent.id")),
    )

    assert metadata.sorted_tables == [parent, child]


def test_result_mappings_exposes_column_names_and_values():
    engine = sa.create_engine("sqlite:///:memory:")

    with engine.connect() as connection:
        row = connection.execute(sa.select(sa.literal(7).label("answer"))).mappings().one()

    assert row["answer"] == 7
    assert dict(row) == {"answer": 7}
