import datetime as dt
from decimal import Decimal
from typing import List, Optional

import pytest
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
