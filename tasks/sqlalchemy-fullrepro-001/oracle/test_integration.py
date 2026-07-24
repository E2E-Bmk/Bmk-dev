# Spec2Repo oracle - integration tests for sqlalchemy-fullrepro-001
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

from conftest import (
    Address,
    User,
    UserBase,
    assert_raises,
    make_user_engine,
    seed_users,
    user_address_tables,
)


def test_core_create_insert_select_reflect_join_workflow():
    """Seam: state consistency — DDL create → insert → reflect → join select."""
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
    """Seam: lifecycle crossing — connect context exit rolls back uncommitted work."""
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
    """Seam: lifecycle crossing — engine.begin commits on success, rolls back on exception."""
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


def test_reflection_inspector_reports_columns_pk_fk_indexes_unique():
    """Seam: state consistency — declared schema ↔ inspector reflection metadata."""
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


def test_boolean_expressions_text_and_literal_values_execute_with_parameters():
    """Seam: protocol handoff — boolean/null expressions and bound text() execute correctly."""
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


def test_core_dml_update_delete_rowcount_and_inserted_primary_key():
    """Seam: state consistency — insert/update/delete DML ↔ row counts and PK visibility."""
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
    """Seam: state consistency — Python datetime ↔ SQLite TEXT storage ↔ typed query result."""
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
    assert typed[2] == values["t"]
    assert isinstance(raw.d, str)
    assert isinstance(raw.dt, str)
    assert isinstance(raw[2], str)


def test_sqlite_json_roundtrip_preserves_nested_python_values():
    """Seam: state consistency — Python dict ↔ SQLite JSON column ↔ query deserialization."""
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
    """Seam: protocol handoff — SQLite upsert dialect ↔ insert conflict resolution."""
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
    """Seam: config interaction — ON CONFLICT WHERE clause controls update vs skip."""
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
    """Seam: lifecycle crossing — session add → commit → get/identity map ↔ object_session."""
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
    """Seam: lifecycle crossing — sessionmaker.begin transaction commit/rollback."""
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
    """Seam: lifecycle crossing — flush/autoflush/no_autoflush ↔ rollback detaches instance."""
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
    """Seam: state consistency — session.delete → flush → commit ↔ durable row removal."""
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
    """Seam: state consistency — relationship back_populates ↔ cascade persist to DB."""
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
    """Seam: protocol handoff — selectinload vs joinedload yield equivalent loaded graphs."""
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
    """Seam: error propagation — raiseload/detached access raises InvalidRequestError/DetachedInstanceError."""
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
    """Seam: protocol handoff — contains_eager join populates filtered relationship collection."""
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
    """Seam: state consistency — Core insert ↔ ORM query over shared table."""
    engine = make_user_engine()

    with engine.begin() as conn:
        conn.execute(
            sa.insert(User.__table__),
            {"name": "sandy", "fullname": "Sandy Cheeks"},
        )

    with Session(engine) as session:
        user = session.scalars(sa.select(User).where(User.name == "sandy")).one()

    assert user.fullname == "Sandy Cheeks"


def test_integrity_error_and_session_recovery_after_rollback():
    """Seam: error propagation — IntegrityError → rollback → session usable for retry."""
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


def test_numeric_float_largebinary_and_null_roundtrip():
    """Seam: state consistency — Numeric/Float/LargeBinary/NULL roundtrip through SQLite."""
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


def test_metadata_collections_constraints_indexes_and_create_drop():
    """Seam: lifecycle crossing — metadata create_all ↔ inspector ↔ drop_all."""
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
    """Seam: protocol handoff — autoload reflected table usable for full CRUD."""
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


def test_table_column_key_label_and_row_mapping_views_agree():
    """Seam: state consistency — Column.key ↔ label ↔ reflection name mapping."""
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
    assert reflected.c.db_name.name == "db_name"


def test_primary_foreign_unique_and_check_constraints_reflect_from_sqlite():
    """Seam: state consistency — declared constraints ↔ inspector reflection."""
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
    """Seam: state consistency — executemany insert ↔ mappings() column names."""
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


def test_declarative_default_init_table_and_metadata_views_agree():
    """Seam: state consistency — Declarative class ↔ __table__ ↔ metadata.tables."""
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
    """Seam: lifecycle crossing — session close ↔ engine-persisted data readable in new session."""
    engine = make_user_engine()

    with Session(engine) as session:
        session.add(User(name="sandy", fullname="Sandy Cheeks"))
        session.commit()

    with Session(engine) as session:
        stored = session.scalars(sa.select(User.fullname)).one()

    assert stored == "Sandy Cheeks"


def test_expire_on_commit_refreshes_attributes_from_database():
    """Seam: state consistency — expire_on_commit ↔ DB update ↔ attribute refresh."""
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


def test_many_to_one_lazy_load_can_use_identity_map():
    """Seam: protocol handoff — lazy many-to-one load resolves via identity map."""
    engine = make_user_engine()
    seed_users(engine)

    with Session(engine) as session:
        user = session.scalars(sa.select(User).where(User.name == "sandy")).one()
        address = session.scalars(sa.select(Address).where(Address.email_address == "sandy@example.org")).one()
        related = address.user

    assert related is user


def test_joinedload_collection_requires_unique_for_duplicate_primary_rows():
    """Seam: protocol handoff — joinedload duplicate rows require unique() before scalars."""
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


def test_core_and_orm_share_transaction_visibility_until_commit():
    """Seam: state consistency — Core connection and ORM Session share uncommitted txn visibility."""
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
    """Seam: lifecycle crossing — Core insert → ORM append/commit → reflection count."""
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


def test_metadata_table_and_column_collections_expose_declared_schema():
    """Seam: state consistency — metadata.tables/columns ↔ declared Table schema."""
    metadata, users, addresses = user_address_tables()

    assert list(metadata.tables) == ["user_account", "address"]
    assert list(users.c.keys()) == ["id", "name", "fullname"]
    assert users.primary_key.columns.keys() == ["id"]
    assert addresses.c.user_id.foreign_keys


def test_reflected_metadata_reconstructs_declared_tables_and_foreign_keys():
    """Seam: state consistency — metadata.reflect ↔ declared tables and FK targets."""
    engine = sa.create_engine("sqlite://")
    metadata, users, addresses = user_address_tables()
    metadata.create_all(engine)

    reflected = sa.MetaData()
    reflected.reflect(bind=engine)

    assert set(reflected.tables) == {users.name, addresses.name}
    reflected_address = reflected.tables[addresses.name]
    target = next(iter(reflected_address.c.user_id.foreign_keys)).target_fullname
    assert target == "user_account.id"


def test_declarative_mapping_projects_table_columns_and_shared_metadata():
    """Seam: state consistency — Declarative mapping ↔ shared metadata table/FK wiring."""
    assert User.__table__ is UserBase.metadata.tables["orm_user"]
    assert Address.__table__ is UserBase.metadata.tables["orm_address"]
    assert list(User.__table__.c.keys()) == ["id", "name", "fullname"]
    assert next(iter(Address.__table__.c.user_id.foreign_keys)).target_fullname == "orm_user.id"


def test_core_insert_orm_update_and_reflection_observe_same_row():
    """Seam: state consistency — Core insert → ORM update → reflection sees same row."""
    engine = make_user_engine()
    with engine.begin() as connection:
        user_id = connection.scalar(
            sa.insert(User.__table__).returning(User.__table__.c.id),
            {"name": "sandy", "fullname": "Sandy Cheeks"},
        )

    with Session(engine) as session:
        user = session.get(User, user_id)
        user.fullname = "Sandy Squirrel"
        session.commit()

    reflected = sa.Table("orm_user", sa.MetaData(), autoload_with=engine)
    with engine.connect() as connection:
        row = connection.execute(sa.select(reflected)).mappings().one()

    assert row["id"] == user_id
    assert row["name"] == "sandy"
    assert row["fullname"] == "Sandy Squirrel"


def test_session_rollback_and_core_query_agree_on_durable_state():
    """Seam: state consistency — session rollback ↔ Core query durable state agreement."""
    engine = make_user_engine()
    with Session(engine) as session:
        session.add(User(name="durable", fullname="Durable User"))
        session.commit()
        session.add(User(name="temporary", fullname="Temporary User"))
        session.flush()
        session.rollback()

    with engine.connect() as connection:
        names = connection.scalars(sa.select(User.__table__.c.name).order_by(User.__table__.c.name)).all()

    assert names == ["durable"]


def test_relationship_update_is_visible_through_core_join_and_orm_loader():
    """Seam: state consistency — relationship persist ↔ Core join ↔ ORM loader views."""
    engine = make_user_engine()
    with Session(engine) as session:
        user = User(name="sandy", fullname="Sandy Cheeks")
        user.addresses.append(Address(email_address="one@example.org"))
        session.add(user)
        session.commit()
        user_id = user.id

    with engine.connect() as connection:
        joined = connection.execute(
            sa.select(User.__table__.c.name, Address.__table__.c.email_address).join(Address.__table__)
        ).one()

    with Session(engine) as session:
        loaded = session.scalars(sa.select(User).options(selectinload(User.addresses))).one()

    assert joined == ("sandy", "one@example.org")
    assert loaded.id == user_id
    assert [address.email_address for address in loaded.addresses] == ["one@example.org"]
