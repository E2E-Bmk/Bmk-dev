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


def test_core_create_insert_select_reflect_join_workflow():
    engine = sa.create_engine("sqlite://")
    metadata, users, addresses = user_address_tables()
    metadata.create_all(engine)

    with engine.begin() as conn:
        result = conn.execute(
            sa.insert(users).returning(users.c.id),
            [{"name": "sandy", "fullname": "Sandy Cheeks"}],
        )
        user_id = result.scalar_one()
        conn.execute(
            sa.insert(addresses),
            [{"user_id": user_id, "email_address": "sandy@example.org"}],
        )

    reflected = sa.Table("address", sa.MetaData(), autoload_with=engine)
    stmt = (
        sa.select(users.c.name, addresses.c.email_address)
        .join_from(users, addresses)
        .where(users.c.name == "sandy")
    )
    with engine.connect() as conn:
        row = conn.execute(stmt).one()

    assert row.name == "sandy"
    assert row.email_address == "sandy@example.org"
    assert reflected.c.user_id.foreign_keys


def test_connect_block_rolls_back_uncommitted_work():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "items",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
    )
    table.create(engine)

    with engine.connect() as conn:
        conn.execute(sa.insert(table), {"name": "temporary"})

    with engine.connect() as conn:
        count = conn.scalar(sa.select(sa.func.count()).select_from(table))

    assert count == 0


def test_engine_begin_commits_success_and_rolls_back_exception():
    engine = sa.create_engine("sqlite://")
    table = sa.Table("log", sa.MetaData(), sa.Column("name", sa.String, primary_key=True))
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), {"name": "committed"})

    def failing_block():
        with engine.begin() as conn:
            conn.execute(sa.insert(table), {"name": "rolled-back"})
            raise RuntimeError("leave block")

    assert_raises(RuntimeError, failing_block)
    with engine.connect() as conn:
        names = conn.execute(sa.select(table.c.name).order_by(table.c.name)).scalars().all()

    assert names == ["committed"]


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


def test_reflection_inspector_reports_columns_pk_fk_indexes_unique():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    parent = sa.Table("parent", metadata, sa.Column("id", sa.Integer, primary_key=True))
    child = sa.Table(
        "child",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("parent_id", sa.ForeignKey("parent.id"), nullable=False),
        sa.Column("code", sa.String, nullable=False),
        sa.UniqueConstraint("code", name="uq_child_code"),
        sa.Index("ix_child_parent_id", "parent_id"),
    )
    metadata.create_all(engine)

    inspector = sa.inspect(engine)
    column_names = [col["name"] for col in inspector.get_columns("child")]
    pk = inspector.get_pk_constraint("child")
    fks = inspector.get_foreign_keys("child")
    indexes = inspector.get_indexes("child")
    unique_constraints = inspector.get_unique_constraints("child")

    assert column_names == ["id", "parent_id", "code"]
    assert pk["constrained_columns"] == ["id"]
    assert fks[0]["referred_table"] == "parent"
    assert fks[0]["constrained_columns"] == ["parent_id"]
    assert any(index["name"] == "ix_child_parent_id" for index in indexes)
    assert any(uc["name"] == "uq_child_code" for uc in unique_constraints)
    assert child.c.parent_id.nullable is False


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


def test_boolean_expressions_text_and_literal_values_execute_with_parameters():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "flags",
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
                {"name": "alpha", "enabled": True, "score": 7},
                {"name": "beta", "enabled": False, "score": 9},
                {"name": "gamma", "enabled": True, "score": 3},
            ],
        )
        stmt = sa.select(table.c.name).where(
            sa.and_(
                table.c.enabled.is_(sa.true()),
                sa.or_(table.c.score >= 7, table.c.name.like("g%")),
                sa.not_(table.c.name == sa.literal("gamma")),
            )
        )
        names = conn.execute(stmt).scalars().all()
        text_value = conn.scalar(sa.text("select :left_value + :right_value"), {"left_value": 2, "right_value": 5})

    assert names == ["alpha"]
    assert text_value == 7


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


def test_core_dml_update_delete_rowcount_and_inserted_primary_key():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "todo",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
        sa.Column("done", sa.Boolean, nullable=False),
    )
    table.create(engine)

    with engine.begin() as conn:
        insert_result = conn.execute(sa.insert(table), {"name": "write tests", "done": False})
        update_result = conn.execute(
            sa.update(table).where(table.c.name == "write tests").values(done=True)
        )
        delete_result = conn.execute(sa.delete(table).where(table.c.done.is_(sa.true())))
        remaining = conn.scalar(sa.select(sa.func.count()).select_from(table))

    assert insert_result.inserted_primary_key == (1,)
    assert update_result.rowcount == 1
    assert delete_result.rowcount == 1
    assert remaining == 0


def test_sqlite_datetime_date_time_roundtrip_and_raw_storage():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "temporal",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("d", sqlite.DATE),
        sa.Column("dt", sqlite.DATETIME),
        sa.Column("t", sqlite.TIME),
    )
    table.create(engine)
    values = {
        "d": dt.date(2024, 2, 3),
        "dt": dt.datetime(2024, 2, 3, 4, 5, 6, 123456),
        "t": dt.time(7, 8, 9, 987654),
    }

    with engine.begin() as conn:
        conn.execute(sa.insert(table), values)
        typed = conn.execute(sa.select(table.c.d, table.c.dt, table.c.t)).one()
        raw = conn.execute(sa.text("select d, dt, t from temporal")).one()

    assert typed.d == values["d"]
    assert typed.dt == values["dt"]
    assert typed._mapping["t"] == values["t"]
    assert isinstance(raw.d, str)
    assert isinstance(raw.dt, str)
    assert isinstance(raw._mapping["t"], str)


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


def test_sqlite_json_roundtrip_preserves_nested_python_values():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "documents",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("payload", sqlite.JSON),
    )
    table.create(engine)

    with engine.begin() as conn:
        payload = {"name": "sandy", "numbers": [1, 2], "nested": {"flag": True}}
        conn.execute(
            sa.insert(table),
            {"payload": payload},
        )
        row = conn.execute(sa.select(table.c.payload)).one()

    assert row.payload == payload
    assert row.payload["nested"]["flag"] is True
    assert row.payload["numbers"] == [1, 2]


def test_sqlite_insert_on_conflict_do_nothing_and_do_update():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "accounts",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, unique=True),
        sa.Column("visits", sa.Integer, nullable=False),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), {"name": "sandy", "visits": 1})
        skipped = conn.execute(
            sqlite.insert(table)
            .values(name="sandy", visits=100)
            .on_conflict_do_nothing(index_elements=[table.c.name])
        )
        upsert = sqlite.insert(table).values(name="sandy", visits=5)
        updated = conn.execute(
            upsert.on_conflict_do_update(
                index_elements=[table.c.name],
                set_={"visits": 5},
            )
        )
        row = conn.execute(sa.select(table.c.name, table.c.visits)).one()

    assert skipped.rowcount == 0
    assert updated.rowcount == 1
    assert row.name == "sandy"
    assert row.visits == 5


def test_sqlite_insert_on_conflict_where_clause_controls_update():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "inventory",
        sa.MetaData(),
        sa.Column("sku", sa.String, primary_key=True),
        sa.Column("quantity", sa.Integer, nullable=False),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), {"sku": "abc", "quantity": 5})
        stmt = sqlite.insert(table).values(sku="abc", quantity=2)
        result = conn.execute(
            stmt.on_conflict_do_update(
                index_elements=[table.c.sku],
                set_={"quantity": stmt.excluded.quantity},
                where=table.c.quantity < 3,
            )
        )
        quantity = conn.scalar(sa.select(table.c.quantity))

    assert result.rowcount == 0
    assert quantity == 5


def test_session_add_commit_get_identity_and_object_session():
    engine = make_user_engine()

    with Session(engine, expire_on_commit=False) as session:
        user = User(name="sandy", fullname="Sandy Cheeks")
        session.add(user)
        session.commit()
        first = session.get(User, user.id)
        second = session.scalars(sa.select(User).where(User.id == user.id)).one()

        assert user.id == 1
        assert first is user
        assert second is user
        assert object_session(user) is session


def test_sessionmaker_begin_commits_and_rolls_back_on_exception():
    engine = make_user_engine()
    SessionFactory = sessionmaker(engine, expire_on_commit=False)

    with SessionFactory.begin() as session:
        session.add(User(name="committed", fullname="Committed User"))

    def failing_unit():
        with SessionFactory.begin() as session:
            session.add(User(name="rolledback", fullname="Rolled Back"))
            raise RuntimeError("rollback")

    assert_raises(RuntimeError, failing_unit)
    with Session(engine) as session:
        names = session.scalars(sa.select(User.name).order_by(User.name)).all()

    assert names == ["committed"]


def test_session_flush_autoflush_no_autoflush_and_rollback():
    engine = make_user_engine()

    with Session(engine, expire_on_commit=False) as session:
        user = User(name="sandy", fullname="Sandy Cheeks")
        session.add(user)
        with session.no_autoflush:
            assert session.scalar(sa.select(sa.func.count()).select_from(User)) == 0
        assert session.scalar(sa.select(sa.func.count()).select_from(User)) == 1
        assert user.id == 1
        session.rollback()
        assert user.id == 1
        assert object_session(user) is None

    with Session(engine) as session:
        assert session.scalar(sa.select(sa.func.count()).select_from(User)) == 0


def test_session_delete_marks_row_for_delete_on_flush():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        user = session.scalars(sa.select(User).where(User.name == "patrick")).one()
        session.delete(user)
        session.flush()
        names_inside_txn = session.scalars(sa.select(User.name).order_by(User.name)).all()
        session.commit()

    with Session(engine) as session:
        names_after_commit = session.scalars(sa.select(User.name).order_by(User.name)).all()

    assert names_inside_txn == ["sandy"]
    assert names_after_commit == ["sandy"]


def test_relationship_back_populates_and_cascade_persist_children():
    engine = make_user_engine()

    user = User(name="sandy", fullname="Sandy Cheeks")
    address = Address(email_address="sandy@example.org")
    user.addresses.append(address)

    assert address.user is user
    assert user.addresses == [address]

    with Session(engine, expire_on_commit=False) as session:
        session.add(user)
        session.commit()
        address_id = address.id
        user_id = user.id

    with Session(engine) as session:
        stored = session.get(Address, address_id)
        assert stored.user_id == user_id
        assert stored.user.name == "sandy"


def test_selectinload_and_joinedload_return_same_primary_objects():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        selectin_users = session.scalars(
            sa.select(User).options(selectinload(User.addresses)).order_by(User.name)
        ).all()
        joined_users = session.scalars(
            sa.select(User).options(joinedload(User.addresses)).order_by(User.name)
        ).unique().all()

    assert [user.name for user in selectin_users] == ["patrick", "sandy"]
    assert [user.name for user in joined_users] == ["patrick", "sandy"]
    assert [len(user.addresses) for user in selectin_users] == [0, 2]
    assert [len(user.addresses) for user in joined_users] == [0, 2]


def test_lazyload_raiseload_and_detached_lazy_load_errors():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        user = session.scalars(
            sa.select(User).options(raiseload(User.addresses)).where(User.name == "sandy")
        ).one()
        assert_raises(exc.InvalidRequestError, lambda: user.addresses)

    with Session(engine) as session:
        detached = session.scalars(sa.select(User).where(User.name == "sandy")).one()
    assert_raises(orm_exc.DetachedInstanceError, lambda: detached.addresses)


def test_contains_eager_uses_explicit_join_to_populate_filtered_collection():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        user = session.scalars(
            sa.select(User)
            .join(User.addresses)
            .options(contains_eager(User.addresses))
            .where(Address.email_address.like("%work%"))
            .execution_options(populate_existing=True)
        ).unique().one()

        assert user.name == "sandy"
        assert [address.email_address for address in user.addresses] == [
            "sandy@work.example"
        ]


def test_core_insert_then_orm_query_over_same_table():
    engine = make_user_engine()

    with engine.begin() as conn:
        conn.execute(
            sa.insert(User.__table__),
            {"name": "sandy", "fullname": "Sandy Cheeks"},
        )

    with Session(engine) as session:
        user = session.scalars(sa.select(User).where(User.name == "sandy")).one()

    assert user.fullname == "Sandy Cheeks"


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


def test_integrity_error_and_session_recovery_after_rollback():
    engine = make_user_engine()

    with Session(engine) as session:
        session.add_all(
            [
                User(id=1, name="first", fullname="First"),
                User(id=1, name="duplicate", fullname="Duplicate"),
            ]
        )
        assert_raises(exc.IntegrityError, session.commit)
        session.rollback()
        session.add(User(name="second", fullname="Second"))
        session.commit()

    with Session(engine) as session:
        names = session.scalars(sa.select(User.name)).all()

    assert names == ["second"]


def test_unmapped_instance_errors():
    class Plain:
        pass

    engine = make_user_engine()

    with Session(engine) as session:
        assert_raises(orm_exc.UnmappedInstanceError, lambda: session.add(Plain()))


def test_numeric_float_largebinary_and_null_roundtrip():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "typed_values",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("amount", sa.Numeric(10, 2)),
        sa.Column("ratio", sa.Float),
        sa.Column("payload", sa.LargeBinary),
        sa.Column("optional_text", sa.Text),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(
            sa.insert(table),
            {
                "amount": Decimal("12.50"),
                "ratio": 0.25,
                "payload": b"abc",
                "optional_text": None,
            },
        )
        row = conn.execute(
            sa.select(table.c.amount, table.c.ratio, table.c.payload, table.c.optional_text)
        ).one()
        null_check = conn.scalar(sa.select(sa.null().is_(None)))

    assert row.amount == Decimal("12.50")
    assert row.ratio == 0.25
    assert row.payload == b"abc"
    assert row.optional_text is None
    assert null_check is True


def test_top_level_import_surface_exposes_common_core_and_orm_names():
    assert callable(sa.create_engine)
    assert callable(sa.inspect)
    assert sa.Integer is not None
    assert sa.String is not None
    assert sa.orm.Session is Session
    assert callable(sa.orm.relationship)
    assert sqlite.insert is not None


def test_metadata_collections_constraints_indexes_and_create_drop():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    table = sa.Table(
        "account",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False),
        sa.UniqueConstraint("email", name="uq_account_email"),
        sa.CheckConstraint("length(email) > 3", name="ck_email_len"),
        sa.Index("ix_account_active", "active"),
    )

    metadata.create_all(engine)
    inspector = sa.inspect(engine)
    assert "account" in inspector.get_table_names()
    assert table.c.email.nullable is False
    assert table.primary_key.columns.keys() == ["id"]
    assert any(index["name"] == "ix_account_active" for index in inspector.get_indexes("account"))

    metadata.drop_all(engine)
    inspector = sa.inspect(engine)
    assert "account" not in inspector.get_table_names()


def test_reflected_table_can_be_used_for_insert_select_update_delete():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    table = sa.Table(
        "reflected_user",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
    )
    metadata.create_all(engine)
    reflected = sa.Table("reflected_user", sa.MetaData(), autoload_with=engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(reflected), {"name": "sandy"})
        conn.execute(sa.update(reflected).values(name="patrick"))
        names = conn.execute(sa.select(reflected.c.name)).scalars().all()
        deleted = conn.execute(sa.delete(reflected).where(reflected.c.name == "patrick"))

    assert names == ["patrick"]
    assert deleted.rowcount == 1


def test_textual_statement_and_bound_parameters_do_not_interpolate_values():
    engine = sa.create_engine("sqlite://")

    with engine.connect() as conn:
        value = conn.scalar(sa.text("select :name"), {"name": "sandy"})
        dangerous = conn.scalar(sa.text("select :payload"), {"payload": "1; drop table nope"})

    assert value == "sandy"
    assert dangerous == "1; drop table nope"


def test_table_column_key_label_and_row_mapping_views_agree():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    table = sa.Table(
        "labels",
        metadata,
        sa.Column("db_name", sa.String, key="python_name"),
    )
    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), {"python_name": "stored"})
        row = conn.execute(sa.select(table.c.python_name.label("visible_name"))).one()
        reflected = sa.Table("labels", sa.MetaData(), autoload_with=engine)

    assert row.visible_name == "stored"
    assert row._mapping["visible_name"] == "stored"
    assert reflected.c.db_name.name == "db_name"


def test_primary_foreign_unique_and_check_constraints_reflect_from_sqlite():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    parent = sa.Table("cv_parent", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "cv_child",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("parent_id", sa.ForeignKey(parent.c.id), nullable=False),
        sa.Column("code", sa.String, nullable=False),
        sa.UniqueConstraint("code", name="uq_cv_child_code"),
        sa.CheckConstraint("length(code) > 1", name="ck_cv_child_code"),
    )
    metadata.create_all(engine)
    inspector = sa.inspect(engine)

    assert inspector.get_pk_constraint("cv_child")["constrained_columns"] == ["id"]
    assert inspector.get_foreign_keys("cv_child")[0]["referred_table"] == "cv_parent"
    assert any(uc["name"] == "uq_cv_child_code" for uc in inspector.get_unique_constraints("cv_child"))
    assert any(cc["name"] == "ck_cv_child_code" for cc in inspector.get_check_constraints("cv_child"))


def test_insert_executemany_and_select_mappings_preserve_column_names():
    engine = sa.create_engine("sqlite://")
    table = sa.Table(
        "batch_items",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String),
    )
    table.create(engine)

    with engine.begin() as conn:
        conn.execute(sa.insert(table), [{"name": "one"}, {"name": "two"}])
        rows = conn.execute(sa.select(table.c.id, table.c.name).order_by(table.c.id)).mappings().all()

    assert rows == [{"id": 1, "name": "one"}, {"id": 2, "name": "two"}]


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


def test_declarative_default_init_table_and_metadata_views_agree():
    class LocalBase(DeclarativeBase):
        pass

    class Widget(LocalBase):
        __tablename__ = "widget"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(sa.String(20))

    widget = Widget(name="gear")
    engine = sa.create_engine("sqlite://")
    LocalBase.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        session.add(widget)
        session.commit()

    assert Widget.__table__ is LocalBase.metadata.tables["widget"]
    assert widget.id == 1
    assert widget.name == "gear"


def test_session_context_manager_closes_but_engine_data_persists():
    engine = make_user_engine()

    with Session(engine) as session:
        session.add(User(name="sandy", fullname="Sandy Cheeks"))
        session.commit()

    with Session(engine) as session:
        stored = session.scalars(sa.select(User.fullname)).one()

    assert stored == "Sandy Cheeks"


def test_expire_on_commit_refreshes_attributes_from_database():
    engine = make_user_engine()

    with Session(engine) as session:
        user = User(name="sandy", fullname="Sandy Cheeks")
        session.add(user)
        session.commit()
        user_id = user.id
        with engine.begin() as conn:
            conn.execute(sa.update(User.__table__).values(fullname="Updated").where(User.__table__.c.id == user_id))
        session.expire(user, ["fullname"])
        refreshed = user.fullname

    assert refreshed == "Updated"


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


def test_many_to_one_lazy_load_can_use_identity_map():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        user = session.scalars(sa.select(User).where(User.name == "sandy")).one()
        address = session.scalars(sa.select(Address).where(Address.email_address == "sandy@example.org")).one()
        related = address.user

    assert related is user


def test_joinedload_collection_requires_unique_for_duplicate_primary_rows():
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        result = session.execute(sa.select(User).options(joinedload(User.addresses)).where(User.name == "sandy"))
        users = result.unique().scalars().all()

    assert len(users) == 1
    assert [address.email_address for address in users[0].addresses] == [
        "sandy@example.org",
        "sandy@work.example",
    ]


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


def test_core_and_orm_share_transaction_visibility_until_commit():
    engine = make_user_engine()
    conn = engine.connect()
    trans = conn.begin()
    conn.execute(sa.insert(User.__table__), {"name": "sandy", "fullname": "Sandy Cheeks"})

    with Session(bind=conn) as session:
        same_transaction_names = session.scalars(sa.select(User.name)).all()

    trans.rollback()
    conn.close()

    with Session(engine) as session:
        after_rollback_names = session.scalars(sa.select(User.name)).all()

    assert same_transaction_names == ["sandy"]
    assert after_rollback_names == []


def test_full_core_orm_reflection_workflow_with_second_address():
    engine = make_user_engine()
    with engine.begin() as conn:
        result = conn.execute(sa.insert(User.__table__).returning(User.__table__.c.id), {"name": "sandy", "fullname": "Sandy Cheeks"})
        user_id = result.scalar_one()
        conn.execute(sa.insert(Address.__table__), [{"user_id": user_id, "email_address": "one@example.org"}])

    with Session(engine) as session:
        user = session.scalars(sa.select(User).options(selectinload(User.addresses))).one()
        user.addresses.append(Address(email_address="two@example.org"))
        session.commit()

    reflected = sa.Table("orm_address", sa.MetaData(), autoload_with=engine)
    with engine.connect() as conn:
        count = conn.scalar(sa.select(sa.func.count()).select_from(reflected))

    assert count == 2
