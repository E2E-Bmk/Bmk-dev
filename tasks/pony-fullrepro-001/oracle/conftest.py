from decimal import Decimal
from types import SimpleNamespace

import pytest
from pony.orm import (
    Database,
    Json,
    Optional,
    PrimaryKey,
    Required,
    Set,
)


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


def make_library():
    db = Database("sqlite", ":memory:")

    class Author(db.Entity):
        id = PrimaryKey(int, auto=False)
        name = Required(str, unique=True)
        active = Required(bool, default=True)
        books = Set("Book", reverse="author")
        edited_books = Set("Book", reverse="editor")

    class Tag(db.Entity):
        id = PrimaryKey(int, auto=False)
        label = Required(str, unique=True)
        books = Set("Book", reverse="tags")

    class Book(db.Entity):
        id = PrimaryKey(int, auto=False)
        code = Required(str, unique=True)
        title = Required(str)
        pages = Required(int)
        price = Optional(Decimal, precision=8, scale=2)
        published = Required(bool, default=True)
        metadata = Optional(Json)
        author = Required(Author, reverse="books")
        editor = Optional(Author, reverse="edited_books")
        tags = Set(Tag, reverse="books")

    class AutoRecord(db.Entity):
        id = PrimaryKey(int, auto=True)
        label = Required(str)

    db.generate_mapping(create_tables=True)
    return SimpleNamespace(
        db=db,
        Author=Author,
        Tag=Tag,
        Book=Book,
        AutoRecord=AutoRecord,
    )


def seed_library(lib):
    authors = {
        "alice": lib.Author(id=1, name="Alice", active=True),
        "bob": lib.Author(id=2, name="Bob", active=False),
        "carol": lib.Author(id=3, name="Carol"),
    }
    tags = {
        "fiction": lib.Tag(id=100, label="fiction"),
        "science": lib.Tag(id=101, label="science"),
        "poetry": lib.Tag(id=102, label="poetry"),
    }
    books = {
        "alpha": lib.Book(
            id=10,
            code="B10",
            title="Alpha",
            pages=100,
            price=Decimal("12.50"),
            published=True,
            metadata={"genre": "fiction", "rank": 1},
            author=authors["alice"],
            editor=authors["carol"],
        ),
        "beta": lib.Book(
            id=11,
            code="B11",
            title="Beta",
            pages=240,
            price=Decimal("18.00"),
            published=True,
            metadata={"genre": "science", "rank": 2},
            author=authors["alice"],
            editor=authors["bob"],
        ),
        "gamma": lib.Book(
            id=12,
            code="B12",
            title="Gamma",
            pages=80,
            price=None,
            published=False,
            metadata={},
            author=authors["bob"],
        ),
        "delta": lib.Book(
            id=13,
            code="B13",
            title="Delta",
            pages=320,
            price=Decimal("25.75"),
            published=True,
            metadata={"genre": "poetry", "rank": 3},
            author=authors["carol"],
            editor=authors["alice"],
        ),
    }
    books["alpha"].tags.add(tags["fiction"])
    books["beta"].tags.add(tags["science"])
    books["beta"].tags.add(tags["fiction"])
    books["gamma"].tags.add(tags["poetry"])
    books["delta"].tags.add(tags["poetry"])
    return SimpleNamespace(authors=authors, tags=tags, books=books)
