from pathlib import Path

import pytest

from conftest import (
    Author,
    Book,
    Tag,
    run_db,
    seed_library,
    sqlite_file_url,
)
from tortoise import Tortoise


@pytest.mark.depends_on(
    "test_create_assigns_explicit_primary_key_and_reads_pk",
    "test_values_returns_selected_dict_fields",
)
def test_create_save_filter_and_values_share_row_projection():
    async def check():
        author = await Author.create(id=1, name="Initial")
        await Author.filter(pk=author.pk).update(name="Saved")
        rows = await Author.filter(name="Saved").values("id", "name")
        assert rows == [{"id": 1, "name": "Saved"}]

    run_db(check)


@pytest.mark.depends_on(
    "test_order_by_supports_ascending_and_descending",
    "test_values_list_returns_tuples_and_flat_values",
)
def test_ordering_and_values_list_preserve_projection_order():
    async def check():
        await seed_library()
        books = await Book.all().order_by("-pages")
        rows = await Book.all().order_by("-pages").values_list("title", "pages")
        expected = [
            ("Delta", 320),
            ("Beta", 240),
            ("Alpha", 100),
            ("Gamma", 80),
        ]
        assert [(book.title, book.pages) for book in books] == expected
        assert rows == expected

    run_db(check)


@pytest.mark.depends_on(
    "test_exclude_removes_matching_rows",
    "test_nullable_and_boolean_values_round_trip",
)
def test_exclude_and_isnull_partition_nullable_rows():
    async def check():
        await seed_library()
        unpublished = await Book.filter(published=False).values_list("title", flat=True)
        priced = await Book.filter(price__isnull=False).order_by("id").values_list(
            "title", flat=True
        )
        no_metadata = await Book.filter(metadata__isnull=True).values_list("title", flat=True)
        assert unpublished == ["Gamma"]
        assert priced == ["Alpha", "Beta", "Delta"]
        assert no_metadata == ["Gamma"]

    run_db(check)


@pytest.mark.depends_on(
    "test_get_or_create_reports_created_flag",
    "test_update_or_create_updates_existing_row",
)
def test_get_or_create_then_update_or_create_preserve_identity():
    async def check():
        first, created = await Author.get_or_create(id=1, defaults={"active": True}, name="A")
        second, updated_created = await Author.update_or_create(
            defaults={"name": "A2"}, id=1
        )
        assert created is True
        assert updated_created is False
        assert first.pk == second.pk == 1
        assert (await Author.get(pk=1)).name == "A2"

    run_db(check)


@pytest.mark.depends_on(
    "test_bulk_create_inserts_multiple_rows",
    "test_bulk_update_changes_selected_fields",
)
def test_bulk_create_filter_and_bulk_update_workflow():
    async def check():
        authors = [Author(id=1, name="one"), Author(id=2, name="two")]
        await Author.bulk_create(authors)
        selected = await Author.filter(id__in=[1, 2]).order_by("id")
        selected[0].name = "ONE"
        selected[1].name = "TWO"
        await Author.bulk_update(selected, fields=["name"])
        assert await Author.all().order_by("id").values_list("name", flat=True) == [
            "ONE",
            "TWO",
        ]

    run_db(check)


@pytest.mark.depends_on(
    "test_queryset_delete_removes_rows",
    "test_count_and_exists_reflect_rows",
)
def test_delete_workflow_updates_count_and_exists():
    async def check():
        await seed_library()
        await Book.filter(id__in=[10, 11]).delete()
        assert await Book.all().count() == 2
        assert not await Book.filter(id=10).exists()
        assert await Book.filter(id=12).exists()

    run_db(check)


@pytest.mark.depends_on(
    "test_prefetch_related_populates_forward_relation",
    "test_values_supports_alias_for_related_field",
)
def test_forward_prefetch_and_values_related_name_agree():
    async def check():
        await seed_library()
        book = await Book.filter(id=10).prefetch_related("author").first()
        row = await Book.filter(id=10).values(author_name="author__name")
        assert book.author.name == row[0]["author_name"] == "Alice"

    run_db(check)


@pytest.mark.depends_on(
    "test_reverse_relation_prefetch_returns_children",
    "test_foreign_key_filter_uses_related_field",
)
def test_reverse_prefetch_and_related_filter_agree():
    async def check():
        await seed_library()
        author = await Author.filter(id=1).prefetch_related("books").first()
        filtered = await Book.filter(author__name="Alice").order_by("id").values_list(
            "title", flat=True
        )
        assert [book.title for book in author.books] == filtered == ["Alpha", "Beta"]

    run_db(check)


@pytest.mark.depends_on(
    "test_many_to_many_add_and_prefetch",
    "test_values_list_returns_tuples_and_flat_values",
)
def test_many_to_many_prefetch_and_values_list_agree():
    async def check():
        await seed_library()
        book = await Book.filter(id=11).prefetch_related("tags").first()
        rows = await Book.filter(id=11).values_list("title", "tags__label")
        assert [tag.label for tag in book.tags] == ["fiction", "science"]
        assert rows == [("Beta", "fiction"), ("Beta", "science")]

    run_db(check)


@pytest.mark.depends_on(
    "test_many_to_many_remove_and_clear",
    "test_many_to_many_add_and_prefetch",
)
def test_relation_mutations_change_prefetched_projection():
    async def check():
        data = await seed_library()
        await data["first"].tags.clear()
        await data["first"].tags.add(data["poetry"])
        book = await Book.filter(id=10).prefetch_related("tags").first()
        assert [tag.label for tag in book.tags] == ["poetry"]

    run_db(check)


@pytest.mark.depends_on(
    "test_filter_comparison_and_string_lookups",
    "test_order_by_supports_ascending_and_descending",
)
def test_nested_relation_filter_and_order_projection():
    async def check():
        await seed_library()
        rows = await Book.filter(author__active=True, pages__gte=100).order_by(
            "-author__name", "id"
        ).values("title", author_name="author__name")
        assert rows == [
            {"title": "Delta", "author_name": "Carol"},
            {"title": "Alpha", "author_name": "Alice"},
            {"title": "Beta", "author_name": "Alice"},
        ]

    run_db(check)


@pytest.mark.depends_on(
    "test_model_describe_names_fields_and_table",
    "test_foreign_key_filter_uses_related_field",
)
def test_model_metadata_matches_relation_projection():
    async def check():
        description = Book.describe()
        data = await seed_library()
        relation_rows = await Book.filter(id=data["first"].pk).values(
            "id", "title", "author_id"
        )
        assert description["table"] == "library_book"
        assert description["pk_field"]["name"] == "id"
        assert relation_rows == [{"id": 10, "title": "Alpha", "author_id": 1}]

    run_db(check)


@pytest.mark.depends_on(
    "test_generate_schemas_allows_create",
    "test_describe_models_is_json_serializable",
)
def test_schema_generation_supports_repeated_safe_initialization():
    async def check():
        await Tortoise.generate_schemas(safe=True)
        await Author.create(id=1, name="Safe")
        assert await Author.all().count() == 1

    run_db(check)


@pytest.mark.depends_on(
    "test_file_database_creates_persistent_sqlite_path",
    "test_values_returns_selected_dict_fields",
)
def test_file_database_round_trip_from_insert_to_read(tmp_path):
    db_path = tmp_path / "roundtrip.sqlite3"

    async def write():
        await Author.create(id=1, name="Persisted")
        await Book.create(id=10, title="File Book", pages=20, author_id=1)

    run_db(write, db_url=sqlite_file_url(db_path))

    async def read():
        rows = await Book.filter(pk=10).values("title", author_name="author__name")
        assert rows == [{"title": "File Book", "author_name": "Persisted"}]

    run_db(read, db_url=sqlite_file_url(db_path))
    assert Path(db_path).exists()


@pytest.mark.depends_on(
    "test_order_by_supports_ascending_and_descending",
    "test_first_and_get_or_none_return_expected_rows",
)
def test_first_last_and_limit_offset_share_ordered_rows():
    async def check():
        await seed_library()
        first = await Book.all().order_by("pages").first()
        last = await Book.all().order_by("pages").last()
        middle = await Book.all().order_by("pages").offset(1).limit(2).values_list(
            "title", flat=True
        )
        assert first.title == "Gamma"
        assert last.title == "Delta"
        assert middle == ["Alpha", "Beta"]

    run_db(check)


@pytest.mark.depends_on(
    "test_filter_comparison_and_string_lookups",
    "test_filter_equality_selects_matching_rows",
)
def test_range_in_and_case_insensitive_filters_compose():
    async def check():
        await seed_library()
        rows = await Book.filter(
            pages__range=[80, 240],
            title__in=["Alpha", "Beta", "Gamma"],
        ).order_by("id").values_list("title", flat=True)
        ci_rows = await Book.filter(title__iexact="alpha").values_list("id", flat=True)
        assert rows == ["Alpha", "Beta", "Gamma"]
        assert ci_rows == [10]

    run_db(check)


@pytest.mark.depends_on(
    "test_filter_comparison_and_string_lookups",
    "test_nullable_and_boolean_values_round_trip",
)
def test_boolean_and_numeric_filters_compose():
    async def check():
        await seed_library()
        books = await Book.filter(published=True, pages__lt=300).order_by("id")
        rows = await Book.filter(published=True, pages__lt=300).order_by("id").values_list(
            "title", flat=True
        )
        assert [book.title for book in books] == rows == ["Alpha", "Beta"]

    run_db(check)


@pytest.mark.depends_on(
    "test_save_inserts_and_updates_single_row",
    "test_values_returns_selected_dict_fields",
)
def test_save_update_refreshes_filtered_values():
    async def check():
        await Author.create(id=1, name="Author")
        book = await Book.create(id=1, title="Draft", pages=10, author_id=1)
        book.title = "Published"
        await book.save(update_fields=["title"])
        rows = await Book.filter(pk=1).values("title", "pages")
        assert rows == [{"title": "Published", "pages": 10}]

    run_db(check)


@pytest.mark.depends_on(
    "test_queryset_delete_removes_rows",
    "test_reverse_relation_prefetch_returns_children",
)
def test_instance_delete_removes_from_relation_projection():
    async def check():
        data = await seed_library()
        await data["first"].delete()
        author = await Author.filter(pk=1).prefetch_related("books").first()
        assert [book.title for book in author.books] == ["Beta"]

    run_db(check)


@pytest.mark.depends_on(
    "test_first_and_get_or_none_return_expected_rows",
    "test_count_and_exists_reflect_rows",
)
def test_get_or_none_returns_none_for_missing_row():
    async def check():
        await seed_library()
        assert await Book.filter(id=999).get_or_none() is None
        assert await Book.filter(id=999).count() == 0

    run_db(check)


@pytest.mark.depends_on(
    "test_values_returns_selected_dict_fields",
    "test_model_describe_names_fields_and_table",
)
def test_values_default_projection_contains_database_fields():
    async def check():
        await seed_library()
        book = await Book.get(id=10)
        row = (await Book.filter(id=10).values())[0]
        assert set(row) >= {"id", "title", "pages", "price", "published", "metadata", "author_id"}
        assert (row["id"], row["title"], row["pages"], row["author_id"]) == (
            book.pk,
            book.title,
            book.pages,
            book.author_id,
        )

    run_db(check)


@pytest.mark.depends_on(
    "test_values_list_returns_tuples_and_flat_values",
    "test_model_describe_names_fields_and_table",
)
def test_values_list_default_projection_contains_database_fields():
    async def check():
        await seed_library()
        book = await Book.get(id=10)
        rows = await Book.filter(id=10).values_list()
        assert len(rows) == 1
        assert len(rows[0]) >= 7
        assert rows[0][0] == book.pk == 10

    run_db(check)


@pytest.mark.depends_on(
    "test_prefetch_related_populates_forward_relation",
    "test_reverse_relation_prefetch_returns_children",
)
def test_prefetch_then_instance_fetch_related_keeps_relations():
    async def check():
        data = await seed_library()
        book = await Book.get(pk=data["first"].pk)
        await book.fetch_related("author", "tags")
        author = await Author.get(pk=data["alice"].pk)
        await author.fetch_related("books")
        assert book.author.name == "Alice"
        assert [tag.label for tag in book.tags] == ["fiction"]
        assert [child.title for child in author.books] == ["Alpha", "Beta"]

    run_db(check)


@pytest.mark.depends_on(
    "test_many_to_many_add_and_prefetch",
    "test_many_to_many_remove_and_clear",
)
def test_many_to_many_duplicate_add_is_idempotent():
    async def check():
        data = await seed_library()
        await data["first"].tags.add(data["fiction"])
        book = await Book.filter(pk=10).prefetch_related("tags").first()
        assert [tag.label for tag in book.tags] == ["fiction"]

    run_db(check)


@pytest.mark.depends_on(
    "test_create_assigns_explicit_primary_key_and_reads_pk",
    "test_reverse_relation_prefetch_returns_children",
)
def test_related_creation_sets_foreign_key():
    async def check():
        author = await Author.create(id=1, name="Alice")
        created = await author.books.create(id=10, title="Child", pages=1)
        rows = await Book.filter(author_id=author.pk).values("id", "title")
        assert created.author_id == author.pk
        assert rows == [{"id": 10, "title": "Child"}]

    run_db(check)


@pytest.mark.depends_on(
    "test_model_describe_names_fields_and_table",
    "test_tortoise_describe_models_names_registered_models",
)
def test_model_describe_and_tortoise_describe_models_agree():
    async def check():
        one = Book.describe()
        many = Tortoise.describe_models([Book])["models.Book"]
        assert one == many

    run_db(check)


@pytest.mark.depends_on(
    "test_file_database_creates_persistent_sqlite_path",
    "test_model_describe_names_fields_and_table",
)
def test_file_database_schema_and_query_are_independent_views(tmp_path):
    db_path = tmp_path / "views.sqlite3"

    async def check():
        await Author.create(id=1, name="File Author")
        await Book.create(id=10, title="File Row", pages=10, author_id=1)
        description = Book.describe()
        rows = await Book.filter(pk=10).values("title", "author_id")
        assert description["table"] == "library_book"
        assert rows == [{"title": "File Row", "author_id": 1}]

    run_db(check, db_url=sqlite_file_url(db_path))
    assert db_path.exists()


@pytest.mark.depends_on(
    "test_filter_equality_selects_matching_rows",
    "test_count_and_exists_reflect_rows",
)
def test_chained_queryset_is_lazy_until_awaited():
    async def check():
        await Author.create(id=1, name="Alice")
        query = Author.filter(name="Later").values_list("name", flat=True)
        await Author.create(id=2, name="Later")
        assert await query == ["Later"]

    run_db(check)


@pytest.mark.depends_on(
    "test_values_list_returns_tuples_and_flat_values",
    "test_filter_equality_selects_matching_rows",
)
def test_queryset_reuse_produces_same_values():
    async def check():
        await seed_library()
        query = Book.filter(published=True).order_by("id").values_list("title", flat=True)
        first = await query
        second = await query
        assert first == second == ["Alpha", "Beta", "Delta"]

    run_db(check)


@pytest.mark.depends_on(
    "test_model_describe_names_fields_and_table",
    "test_prefetch_related_populates_forward_relation",
    "test_many_to_many_add_and_prefetch",
)
def test_end_to_end_library_projection():
    async def check():
        await seed_library()
        descriptions = Tortoise.describe_models([Author, Book, Tag])
        books = await Book.filter(author__active=True).order_by("id").prefetch_related(
            "author", "tags"
        )
        rows = await Book.filter(author__active=True).order_by("id").values(
            "id", "title", author_name="author__name"
        )
        assert descriptions["models.Book"]["table"] == "library_book"
        assert [book.title for book in books] == ["Alpha", "Beta", "Delta"]
        assert rows == [
            {"id": 10, "title": "Alpha", "author_name": "Alice"},
            {"id": 11, "title": "Beta", "author_name": "Alice"},
            {"id": 13, "title": "Delta", "author_name": "Carol"},
        ]

    run_db(check)
