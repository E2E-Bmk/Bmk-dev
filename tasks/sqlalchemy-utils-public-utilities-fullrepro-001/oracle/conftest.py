import uuid

import pytest
import sqlalchemy as sa
from furl import furl
from sqlalchemy.orm import Session, declarative_base, relationship

from sqlalchemy_utils import (
    Choice,
    ChoiceType,
    JSONType,
    Password,
    PasswordType,
    ScalarListException,
    ScalarListType,
    URLType,
    UUIDType,
    force_auto_coercion,
)


force_auto_coercion()
Base = declarative_base()
STATUS_CHOICES = [("new", "New"), ("done", "Done")]


class Category(Base):
    __tablename__ = "category"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50), unique=True, nullable=False)

    records = relationship("Record", back_populates="category")


class Record(Base):
    __tablename__ = "record"

    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column("title_db", sa.String(80), nullable=False)
    token = sa.Column(UUIDType(binary=False), nullable=False)
    website = sa.Column(URLType, nullable=True)
    password = sa.Column(
        PasswordType(schemes=["pbkdf2_sha256"]),
        nullable=True,
    )
    status = sa.Column(ChoiceType(STATUS_CHOICES), nullable=False)
    labels = sa.Column(ScalarListType(), nullable=False)
    scores = sa.Column(ScalarListType(int), nullable=False)
    payload = sa.Column(JSONType, nullable=True)
    active = sa.Column(sa.Boolean, default=True, index=True, nullable=False)
    note = sa.Column(sa.String(80), nullable=True)
    category_id = sa.Column(sa.Integer, sa.ForeignKey("category.id"), nullable=False)

    category = relationship("Category", back_populates="records")


def make_engine(url="sqlite:///:memory:"):
    return sa.create_engine(url)


@pytest.fixture
def session():
    engine = make_engine()
    Base.metadata.create_all(engine)
    with Session(engine) as value:
        yield value
        value.rollback()
    engine.dispose()


def seed_records(session):
    first_category = Category(id=1, name="primary")
    second_category = Category(id=2, name="secondary")
    records = [
        Record(
            id=1,
            title="Alpha",
            token="00000000-0000-0000-0000-000000000001",
            website="https://example.com/start?x=1",
            password="alpha-secret",
            status="new",
            labels=["red", "blue"],
            scores=[3, 5],
            payload={"kind": "alpha", "rank": 1},
            active=True,
            category=first_category,
        ),
        Record(
            id=2,
            title="Beta",
            token="00000000-0000-0000-0000-000000000002",
            website="https://example.org/docs",
            password="beta-secret",
            status="done",
            labels=["green"],
            scores=[8],
            payload={"kind": "beta", "rank": 2},
            active=False,
            note="memo",
            category=first_category,
        ),
        Record(
            id=3,
            title="Gamma",
            token="00000000-0000-0000-0000-000000000003",
            website=None,
            password=None,
            status="new",
            labels=[],
            scores=[1, 2],
            payload={"kind": "gamma", "rank": 3},
            active=True,
            category=second_category,
        ),
    ]
    session.add_all([first_category, second_category, *records])
    session.commit()
    return {
        "primary": first_category,
        "secondary": second_category,
        "alpha": records[0],
        "beta": records[1],
        "gamma": records[2],
    }


def fresh_record(**overrides):
    values = {
        "id": 10,
        "title": "Fresh",
        "token": uuid.UUID("00000000-0000-0000-0000-000000000010"),
        "website": furl("https://fresh.example/path"),
        "password": Password("fresh-secret", secret=True),
        "status": Choice("new", "New"),
        "labels": ["one", "two"],
        "scores": [10, 20],
        "payload": {"kind": "fresh"},
        "active": True,
        "category_id": 1,
    }
    values.update(overrides)
    return Record(**values)


__all__ = [
    "Base",
    "Category",
    "Choice",
    "ChoiceType",
    "JSONType",
    "Password",
    "PasswordType",
    "Record",
    "ScalarListException",
    "ScalarListType",
    "STATUS_CHOICES",
    "URLType",
    "UUIDType",
    "fresh_record",
    "make_engine",
    "seed_records",
]


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")
