from decimal import Decimal

from conftest import (
    Author,
    Book,
    Tag,
    compact_json,
    run_db,
    seed_library,
    sqlite_file_url,
)
from tortoise import Tortoise


def test_model_classes_expose_public_field_metadata():
    async def check():
        author = Author.describe()
        book = Book.describe()
        assert author["name"] == "models.Author"
        assert author["table"] == "library_author"
        assert book["name"] == "models.Book"
        assert book["table"] == "library_book"
        assert {field["name"] for field in book["data_fields"]} >= {
            "title",
            "pages",
            "price",
            "published",
            "metadata",
        }

    run_db(check)


def test_describe_models_is_json_serializable():
    async def check():
        descriptions = Tortoise.describe_models([Author, Book, Tag])
        assert set(descriptions) == {"models.Author", "models.Book", "models.Tag"}
        assert compact_json(descriptions) == compact_json(descriptions)

    run_db(check)


def test_generate_schemas_allows_create():
    async def check():
        author = await Author.create(id=1, name="Alice")
        assert author.name == "Alice"
        assert await Author.all().count() == 1

    run_db(check)


def test_create_assigns_explicit_primary_key_and_reads_pk():
    async def check():
        author = await Author.create(id=7, name="Seven")
        assert author.pk == 7
        assert (await Author.get(pk=7)).name == "Seven"

    run_db(check)


def test_save_inserts_and_updates_single_row():
    async def check():
        author = Author(id=1, name="Before")
        await author.save()
        author.name = "After"
        await author.save(update_fields=["name"])
        assert (await Author.get(pk=1)).name == "After"

    run_db(check)


def test_filter_equality_selects_matching_rows():
    async def check():
        await seed_library()
        rows = await Book.filter(author_id=1).order_by("id").values_list("title", flat=True)
        assert rows == ["Alpha", "Beta"]

    run_db(check)


def test_filter_comparison_and_string_lookups():
    async def check():
        await seed_library()
        long_books = await Book.filter(pages__gte=200).order_by("id").values_list(
            "title", flat=True
        )
        matching = await Book.filter(title__icontains="a").order_by("id").values_list(
            "title", flat=True
        )
        assert long_books == ["Beta", "Delta"]
        assert matching == ["Alpha", "Beta", "Gamma", "Delta"]

    run_db(check)


def test_exclude_removes_matching_rows():
    async def check():
        await seed_library()
        titles = await Book.exclude(published=False).order_by("id").values_list(
            "title", flat=True
        )
        assert titles == ["Alpha", "Beta", "Delta"]

    run_db(check)


def test_order_by_supports_ascending_and_descending():
    async def check():
        await seed_library()
        ascending = await Book.all().order_by("pages").values_list("title", flat=True)
        descending = await Book.all().order_by("-pages").values_list("title", flat=True)
        assert ascending == ["Gamma", "Alpha", "Beta", "Delta"]
        assert descending == ["Delta", "Beta", "Alpha", "Gamma"]

    run_db(check)


def test_values_returns_selected_dict_fields():
    async def check():
        await seed_library()
        rows = await Book.filter(id=10).values("title", "pages")
        assert rows == [{"title": "Alpha", "pages": 100}]

    run_db(check)


def test_values_supports_alias_for_related_field():
    async def check():
        await seed_library()
        rows = await Book.filter(id=10).values(book_title="title", author_name="author__name")
        assert rows == [{"book_title": "Alpha", "author_name": "Alice"}]

    run_db(check)


def test_values_list_returns_tuples_and_flat_values():
    async def check():
        await seed_library()
        pair = await Book.filter(id=10).values_list("title", "pages")
        titles = await Book.all().order_by("id").values_list("title", flat=True)
        assert pair == [("Alpha", 100)]
        assert titles == ["Alpha", "Beta", "Gamma", "Delta"]

    run_db(check)


def test_count_and_exists_reflect_rows():
    async def check():
        await seed_library()
        assert await Book.all().count() == 4
        assert await Book.filter(title="Beta").exists()
        assert not await Book.filter(title="Missing").exists()

    run_db(check)


def test_first_and_get_or_none_return_expected_rows():
    async def check():
        await seed_library()
        first = await Book.all().order_by("id").first()
        missing = await Book.get_or_none(title="Missing")
        assert first.title == "Alpha"
        assert missing is None

    run_db(check)


def test_get_or_create_reports_created_flag():
    async def check():
        created, was_created = await Author.get_or_create(
            id=9, defaults={"active": False}, name="New"
        )
        existing, was_existing_created = await Author.get_or_create(
            id=9, defaults={"active": True}, name="New"
        )
        assert (created.pk, was_created) == (9, True)
        assert (existing.pk, was_existing_created) == (9, False)
        assert (await Author.get(pk=9)).active is False

    run_db(check)


def test_update_or_create_updates_existing_row():
    async def check():
        await Author.create(id=1, name="Old", active=True)
        updated, was_created = await Author.update_or_create(
            defaults={"name": "New", "active": False}, id=1
        )
        assert updated.pk == 1
        assert was_created is False
        assert (await Author.get(pk=1)).name == "New"

    run_db(check)


def test_queryset_update_returns_affected_count():
    async def check():
        await seed_library()
        changed = await Book.filter(author_id=1).update(published=False)
        states = await Book.filter(author_id=1).order_by("id").values_list(
            "published", flat=True
        )
        assert changed == 2
        assert states == [False, False]

    run_db(check)


def test_queryset_delete_removes_rows():
    async def check():
        await seed_library()
        deleted = await Book.filter(published=False).delete()
        assert deleted > 0
        assert await Book.all().count() == 3

    run_db(check)


def test_bulk_create_inserts_multiple_rows():
    async def check():
        await Author.bulk_create(
            [Author(id=1, name="A"), Author(id=2, name="B"), Author(id=3, name="C")]
        )
        assert await Author.all().count() == 3
        assert await Author.all().order_by("id").values_list("name", flat=True) == [
            "A",
            "B",
            "C",
        ]

    run_db(check)


def test_bulk_update_changes_selected_fields():
    async def check():
        authors = [
            Author(id=1, name="A"),
            Author(id=2, name="B"),
        ]
        await Author.bulk_create(authors)
        authors[0].name = "Updated"
        authors[1].name = "Renamed"
        await Author.bulk_update(authors, fields=["name"])
        assert await Author.all().order_by("id").values_list("name", flat=True) == [
            "Updated",
            "Renamed",
        ]

    run_db(check)


def test_nullable_and_boolean_values_round_trip():
    async def check():
        data = await seed_library()
        book = await Book.get(pk=data["third"].pk)
        assert book.price is None
        assert book.published is False
        assert book.metadata is None

    run_db(check)


def test_json_values_round_trip():
    async def check():
        await seed_library()
        row = await Book.filter(id=10).values("metadata")
        assert row == [{"metadata": {"genre": "fiction", "rank": 1}}]
        assert compact_json(row[0]["metadata"]) == {"genre": "fiction", "rank": 1}

    run_db(check)


def test_foreign_key_filter_uses_related_field():
    async def check():
        await seed_library()
        titles = await Book.filter(author__name="Alice").order_by("id").values_list(
            "title", flat=True
        )
        assert titles == ["Alpha", "Beta"]

    run_db(check)


def test_prefetch_related_populates_forward_relation():
    async def check():
        await seed_library()
        book = await Book.filter(id=10).prefetch_related("author").first()
        assert book.author.name == "Alice"

    run_db(check)


def test_reverse_relation_prefetch_returns_children():
    async def check():
        await seed_library()
        author = await Author.filter(id=1).prefetch_related("books").first()
        assert [book.title for book in author.books] == ["Alpha", "Beta"]

    run_db(check)


def test_many_to_many_add_and_prefetch():
    async def check():
        await seed_library()
        book = await Book.filter(id=11).prefetch_related("tags").first()
        assert [tag.label for tag in book.tags] == ["fiction", "science"]

    run_db(check)


def test_many_to_many_remove_and_clear():
    async def check():
        data = await seed_library()
        await data["second"].tags.remove(data["science"])
        await data["second"].tags.clear()
        book = await Book.filter(id=11).prefetch_related("tags").first()
        assert list(book.tags) == []

    run_db(check)


def test_model_describe_names_fields_and_table():
    async def check():
        description = Book.describe()
        assert description["name"] == "models.Book"
        assert description["table"] == "library_book"
        assert description["pk_field"]["name"] == "id"
        assert {field["name"] for field in description["fk_fields"]} == {"author"}
        assert {field["name"] for field in description["m2m_fields"]} == {"tags"}

    run_db(check)


def test_tortoise_describe_models_names_registered_models():
    async def check():
        descriptions = Tortoise.describe_models()
        assert set(descriptions) == {"models.Author", "models.Tag", "models.Book"}
        assert descriptions["models.Book"]["table"] == "library_book"

    run_db(check)


def test_file_database_creates_persistent_sqlite_path(tmp_path):
    async def check():
        author = await Author.create(id=1, name="File Author")
        assert await Author.filter(pk=author.pk).exists()

    db_path = tmp_path / "library.sqlite3"
    run_db(check, db_url=sqlite_file_url(db_path))
    assert db_path.exists()
