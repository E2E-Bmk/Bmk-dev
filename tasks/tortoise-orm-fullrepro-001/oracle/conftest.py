import asyncio
import json
from decimal import Decimal
from pathlib import Path

import pytest

from tortoise import Tortoise, fields
from tortoise.models import Model


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50)
    active = fields.BooleanField(default=True)

    class Meta:
        table = "library_author"
        ordering = ["name"]


class Tag(Model):
    id = fields.IntField(primary_key=True)
    label = fields.CharField(max_length=40, unique=True)

    class Meta:
        table = "library_tag"


class Book(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=80)
    pages = fields.IntField()
    price = fields.DecimalField(max_digits=8, decimal_places=2, null=True)
    published = fields.BooleanField(default=True)
    metadata = fields.JSONField(null=True)
    author = fields.ForeignKeyField(
        "models.Author",
        related_name="books",
        on_delete=fields.CASCADE,
    )
    tags = fields.ManyToManyField(
        "models.Tag",
        related_name="books",
        through="library_book_tag",
    )

    class Meta:
        table = "library_book"


__models__ = [Author, Tag, Book]


def run_db(operation, db_url="sqlite://:memory:"):
    async def runner():
        await Tortoise.init(db_url=db_url, modules={"models": ["conftest"]})
        await Tortoise.generate_schemas()
        try:
            return await operation()
        finally:
            await Tortoise.close_connections()

    return asyncio.run(runner())


async def seed_library():
    alice = await Author.create(id=1, name="Alice", active=True)
    bob = await Author.create(id=2, name="Bob", active=False)
    carol = await Author.create(id=3, name="Carol", active=True)

    fiction = await Tag.create(id=100, label="fiction")
    science = await Tag.create(id=101, label="science")
    poetry = await Tag.create(id=102, label="poetry")

    first = await Book.create(
        id=10,
        title="Alpha",
        pages=100,
        price=Decimal("12.50"),
        published=True,
        metadata={"genre": "fiction", "rank": 1},
        author=alice,
    )
    second = await Book.create(
        id=11,
        title="Beta",
        pages=240,
        price=Decimal("18.00"),
        published=True,
        metadata={"genre": "science", "rank": 2},
        author=alice,
    )
    third = await Book.create(
        id=12,
        title="Gamma",
        pages=80,
        price=None,
        published=False,
        metadata=None,
        author=bob,
    )
    fourth = await Book.create(
        id=13,
        title="Delta",
        pages=320,
        price=Decimal("25.75"),
        published=True,
        metadata={"genre": "poetry", "rank": 3},
        author=carol,
    )

    await first.tags.add(fiction)
    await second.tags.add(science, fiction)
    await third.tags.add(poetry)
    await fourth.tags.add(poetry)
    return {
        "alice": alice,
        "bob": bob,
        "carol": carol,
        "fiction": fiction,
        "science": science,
        "poetry": poetry,
        "first": first,
        "second": second,
        "third": third,
        "fourth": fourth,
    }


def compact_json(value):
    return json.loads(json.dumps(value, sort_keys=True))


def sqlite_file_url(path: Path) -> str:
    return f"sqlite://{path}"


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")
