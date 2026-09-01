"""Atomic layer tests for jrnl-journal-fullrepro-002.

Each test verifies ONE public API entry's ONE behavior.
Independent solvability: if only the tested API is correctly implemented,
the test must pass regardless of other APIs.
"""
from datetime import datetime
from pathlib import Path

import pytest

from conftest import make_config, make_journal, make_populated


# ---------------------------------------------------------------------------
# Package Metadata
# ---------------------------------------------------------------------------

def test_package_title_equals_jrnl():
    import jrnl

    assert jrnl.__title__ == "jrnl"


def test_package_version_is_nonempty_string():
    import jrnl

    assert isinstance(jrnl.__version__, str)
    assert len(jrnl.__version__) > 0


# ---------------------------------------------------------------------------
# Journal Construction / open()
# ---------------------------------------------------------------------------

def test_journal_open_creates_missing_file(tmp_path):
    path = tmp_path / "fresh_journal.txt"
    journal = make_journal(path)
    journal.open()
    assert path.exists()


def test_journal_open_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "deep" / "journal.txt"
    journal = make_journal(path)
    journal.open()
    assert path.exists()


def test_journal_open_returns_journal_instance(tmp_path):
    from jrnl.journals import Journal

    path = tmp_path / "journal.txt"
    journal = make_journal(path)
    result = journal.open()
    assert isinstance(result, Journal)
    assert result is journal
    assert result.path == path
    assert path.is_file()


def test_journal_open_empty_file_yields_no_entries(tmp_path):
    path = tmp_path / "empty.txt"
    journal = make_journal(path)
    journal.open()
    assert len(journal) == 0


# ---------------------------------------------------------------------------
# Journal write()
# ---------------------------------------------------------------------------

def test_journal_write_creates_nonempty_file(tmp_path):
    path = tmp_path / "journal.txt"
    journal = make_journal(path)
    journal.open()
    journal.new_entry("Persisted entry.", date=datetime(2024, 5, 12, 8, 30))
    journal.write()
    assert path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Entry Creation via new_entry()
# ---------------------------------------------------------------------------

def test_new_entry_returns_entry_object():
    from jrnl.journals import Entry

    journal = make_journal()
    entry = journal.new_entry("Surface text.", date=datetime(2024, 1, 1))
    assert isinstance(entry, Entry)
    assert entry.title == "Surface text."
    assert entry.date == datetime(2024, 1, 1)
    assert entry in journal


def test_new_entry_visible_through_iteration():
    journal = make_journal()
    entry = journal.new_entry("Surface", date=datetime(2024, 1, 1))
    assert list(journal) == [entry]


def test_new_entry_with_explicit_date():
    journal = make_journal()
    dt = datetime(2024, 6, 15, 14, 30)
    entry = journal.new_entry("Dated entry.", date=dt)
    assert entry.date == dt


def test_new_entry_sorts_by_default():
    journal = make_journal()
    journal.new_entry("Later", date=datetime(2024, 2, 1))
    journal.new_entry("Earlier", date=datetime(2024, 1, 1))
    assert [e.title for e in journal] == ["Earlier", "Later"]


def test_new_entry_sort_false_preserves_insertion_order():
    journal = make_journal()
    journal.new_entry("Second chronologically", date=datetime(2024, 2, 1), sort=False)
    journal.new_entry("First chronologically", date=datetime(2024, 1, 1), sort=False)
    assert [e.title for e in journal] == [
        "Second chronologically",
        "First chronologically",
    ]


# ---------------------------------------------------------------------------
# Iteration and Length
# ---------------------------------------------------------------------------

def test_journal_len_matches_entry_count():
    journal = make_journal()
    journal.new_entry("One.", date=datetime(2024, 1, 1))
    journal.new_entry("Two.", date=datetime(2024, 1, 2))
    assert len(journal) == 2


def test_journal_iteration_yields_entries_in_order():
    journal = make_journal()
    e1 = journal.new_entry("First.", date=datetime(2024, 1, 1))
    e2 = journal.new_entry("Second.", date=datetime(2024, 1, 2))
    assert list(journal) == [e1, e2]


# ---------------------------------------------------------------------------
# Sorting and Limiting
# ---------------------------------------------------------------------------

def test_sort_orders_chronologically():
    journal = make_journal()
    journal.new_entry("Later", date=datetime(2024, 2, 1), sort=False)
    journal.new_entry("Earlier", date=datetime(2024, 1, 1), sort=False)
    journal.sort()
    assert [e.title for e in journal] == ["Earlier", "Later"]


def test_limit_keeps_last_n_entries():
    journal = make_journal()
    for day in range(1, 5):
        journal.new_entry(f"Day {day}", date=datetime(2024, 1, day))
    journal.limit(2)
    assert [e.title for e in journal] == ["Day 3", "Day 4"]


def test_limit_zero_empties_journal():
    journal = make_journal()
    journal.new_entry("Something.", date=datetime(2024, 1, 1))
    journal.limit(0)
    assert len(journal) == 0


# ---------------------------------------------------------------------------
# Entry Structure: title / body / fulltext / starred
# ---------------------------------------------------------------------------

def test_entry_title_is_first_sentence():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="A title. Body text")
    assert e.title == "A title."
    assert e.body == "Body text"


def test_entry_title_with_question_mark():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Is this a question? Yes it is.")
    assert e.title == "Is this a question?"


def test_entry_body_empty_for_single_sentence():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Just a title.")
    assert e.body.strip() == ""


def test_entry_fulltext_combines_title_and_body():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Title\nBody")
    assert e.fulltext == "Title Body"


def test_entry_starred_from_trailing_marker():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Starred title *\nBody")
    assert e.title == "Starred title"
    assert e.starred is True


def test_entry_not_starred_by_default():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Plain title\nBody")
    assert e.starred is False


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def test_entry_tags_deduplicated_and_lowercase():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Title #Mixed @Other #mixed")
    assert set(e.tags) == {"#mixed", "@other"}


def test_entry_tags_excludes_email_addresses():
    from jrnl.journals import Entry

    e = Entry(make_journal(), text="Contact person@example.com and @owner")
    assert set(e.tags) == {"@owner"}


# ---------------------------------------------------------------------------
# Entry String Representation  (str(entry))
# ---------------------------------------------------------------------------

def test_entry_str_contains_timestamp_and_title():
    from jrnl.journals import Entry

    e = Entry(make_journal(), datetime(2024, 2, 3, 4, 5), "Title\nBody", starred=True)
    stored = str(e)
    assert stored.startswith("[2024-02-03 04:05] Title *")
    assert stored.endswith("Body\n")


def test_entry_str_no_star_when_not_starred():
    from jrnl.journals import Entry

    e = Entry(make_journal(), datetime(2024, 2, 3, 4, 5), "Title\nBody")
    first_line = str(e).split("\n")[0]
    assert "Title" in first_line
    assert not first_line.rstrip().endswith("*")


# ---------------------------------------------------------------------------
# Entry Display  (pprint)
# ---------------------------------------------------------------------------

def test_entry_pprint_short_omits_body():
    from jrnl.journals import Entry

    e = Entry(make_journal(), datetime(2024, 1, 1, 9), "Title\nBody")
    output = e.pprint(short=True)
    assert "Title" in output
    assert "Body" not in output


def test_entry_pprint_short_contains_date():
    from jrnl.journals import Entry

    e = Entry(make_journal(), datetime(2024, 3, 17, 11, 45), "Title\nBody")
    output = e.pprint(short=True)
    assert "2024" in output


# ---------------------------------------------------------------------------
# Journal Display  (Journal.pprint)
# ---------------------------------------------------------------------------

def test_journal_pprint_short_shows_titles_without_bodies():
    journal = make_populated()
    output = journal.pprint(short=True)
    assert "Alpha #work" in output and "Beta #home" in output
    assert "First body" not in output and "Second body" not in output


def test_journal_pprint_full_includes_bodies():
    journal = make_populated()
    output = journal.pprint(short=False)
    assert "First body" in output and "Second body" in output


# ---------------------------------------------------------------------------
# Tag Summaries  (Journal.tags)
# ---------------------------------------------------------------------------

def test_journal_tags_have_name_and_count_attrs():
    journal = make_journal()
    journal.new_entry("One #x #y", date=datetime(2024, 1, 1))
    assert all(hasattr(t, "name") and hasattr(t, "count") for t in journal.tags)


def test_journal_tags_count_once_per_entry_not_occurrence():
    journal = make_journal()
    journal.new_entry("One #x #x", date=datetime(2024, 1, 1))
    journal.new_entry("Two #x #y", date=datetime(2024, 1, 2))
    assert {t.name: t.count for t in journal.tags} == {"#x": 2, "#y": 1}


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_by_tag_case_insensitive():
    journal = make_journal()
    journal.new_entry("One #Mixed", date=datetime(2024, 1, 1))
    journal.new_entry("Two #other", date=datetime(2024, 1, 2))
    journal.filter(tags=["#MIXED"])
    assert [e.title for e in journal] == ["One #Mixed"]


def test_filter_strict_requires_all_tags():
    journal = make_journal()
    journal.new_entry("Both #x #y", date=datetime(2024, 1, 1))
    journal.new_entry("One #x", date=datetime(2024, 1, 2))
    journal.filter(tags=["#x", "#y"], strict=True)
    assert [e.title for e in journal] == ["Both #x #y"]


def test_filter_starred_keeps_only_starred():
    journal = make_journal()
    journal.new_entry("Plain", date=datetime(2024, 1, 1))
    starred_entry = journal.new_entry("Starred", date=datetime(2024, 1, 2))
    starred_entry.starred = True
    journal.filter(starred=True)
    assert [e.title for e in journal] == ["Starred"]


def test_filter_contains_case_insensitive():
    journal = make_journal()
    journal.new_entry("Alpha\nNeedle here", date=datetime(2024, 1, 1))
    journal.new_entry("Beta\nOther", date=datetime(2024, 1, 2))
    journal.filter(contains=["NEEDLE"])
    assert [e.title for e in journal] == ["Alpha"]


def test_filter_exclude_removes_tagged_entries():
    journal = make_journal()
    journal.new_entry("Keep #alpha", date=datetime(2024, 1, 1))
    journal.new_entry("Remove #beta", date=datetime(2024, 1, 2))
    journal.filter(exclude=["#beta"])
    assert [e.title for e in journal] == ["Keep #alpha"]


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def test_import_adds_entries_from_text():
    journal = make_journal()
    journal.import_("[2024-03-15 10:00] Imported entry.\nImported body.\n")
    assert len(journal) == 1
    assert list(journal)[0].title == "Imported entry."


def test_import_deduplicates_exact_entries():
    journal = make_journal()
    text = "[2024-01-01 09:00] Same\nBody\n"
    journal.import_(text)
    journal.import_(text)
    assert len(journal) == 1


# ---------------------------------------------------------------------------
# Editable String / Change Counts
# ---------------------------------------------------------------------------

def test_editable_str_returns_nonempty_string():
    journal = make_populated()
    s = journal.editable_str()
    assert isinstance(s, str)
    assert len(s) > 0
    assert journal.entries[0].title in s


def test_get_change_counts_has_modified_and_deleted_keys():
    journal = make_populated()
    journal.parse_editable_str(journal.editable_str())
    counts = journal.get_change_counts()
    assert "modified" in counts and "deleted" in counts


# ---------------------------------------------------------------------------
# Delete / Change Date
# ---------------------------------------------------------------------------

def test_delete_entries_removes_specified():
    journal = make_journal()
    journal.new_entry("Keep.", date=datetime(2024, 1, 1))
    journal.new_entry("Remove.", date=datetime(2024, 1, 2))
    journal.delete_entries([list(journal)[1]])
    assert len(journal) == 1
    assert list(journal)[0].title == "Keep."


def test_change_date_entries_updates_date():
    journal = make_journal()
    journal.new_entry("Original.", date=datetime(2024, 1, 1))
    new_dt = datetime(2025, 6, 15, 12, 0)
    journal.change_date_entries(new_dt, list(journal))
    assert list(journal)[0].date == new_dt


# ---------------------------------------------------------------------------
# Plugin Registry
# ---------------------------------------------------------------------------

def test_export_formats_contains_required_names():
    from jrnl.plugins import EXPORT_FORMATS

    required = {"pretty", "short", "text", "txt", "json", "md", "markdown"}
    assert required <= set(EXPORT_FORMATS)


def test_import_formats_contains_jrnl():
    from jrnl.plugins import IMPORT_FORMATS

    assert "jrnl" in IMPORT_FORMATS


def test_get_exporter_returns_class_for_text():
    from jrnl.plugins import get_exporter

    assert get_exporter("text") is not None


def test_get_exporter_returns_none_for_unknown():
    from jrnl.plugins import get_exporter

    assert get_exporter("nonexistent_fmt_xyz") is None


def test_get_exporter_returns_none_for_pretty():
    from jrnl.plugins import get_exporter

    assert get_exporter("pretty") is None


def test_get_importer_returns_class_for_jrnl():
    from jrnl.plugins import get_importer

    assert get_importer("jrnl") is not None


def test_get_importer_returns_none_for_unknown():
    from jrnl.plugins import get_importer

    assert get_importer("nonexistent_fmt_xyz") is None


def test_text_and_txt_resolve_to_same_exporter():
    from jrnl.plugins import get_exporter

    assert get_exporter("text") == get_exporter("txt")


def test_md_and_markdown_resolve_to_same_exporter():
    from jrnl.plugins import get_exporter

    assert get_exporter("md") == get_exporter("markdown")


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

def test_encryption_true_maps_to_jrnlv2():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method(True) == determine_encryption_method("jrnlv2")


def test_encryption_false_is_distinct_from_true():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method(False) != determine_encryption_method(True)


def test_encryption_labels_case_insensitive():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method("JRNLV1") == determine_encryption_method("jrnlv1")


def test_v1_and_v2_are_distinct_methods():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method("jrnlv1") != determine_encryption_method("jrnlv2")


# ---------------------------------------------------------------------------
# JrnlException
# ---------------------------------------------------------------------------

def test_jrnl_exception_is_exception_subclass():
    from jrnl.exception import JrnlException

    assert issubclass(JrnlException, Exception)


def test_jrnl_exception_can_be_raised_and_caught():
    from jrnl.exception import JrnlException

    with pytest.raises(JrnlException):
        raise JrnlException("test error")


# ---------------------------------------------------------------------------
# open_journal() — type detection
# ---------------------------------------------------------------------------

def test_open_journal_returns_journal_for_file_path(tmp_path):
    from jrnl.journals import Journal, open_journal

    path = tmp_path / "alpha_journal.txt"
    config = {**make_config(path), "journals": {"alpha": str(path)}}
    opened = open_journal("alpha", config)
    assert isinstance(opened, Journal)
    assert opened.path == path
    assert opened.config["journal"] == str(path)


def test_open_journal_returns_folder_for_directory(tmp_path):
    from jrnl.journals import Folder, open_journal

    folder = tmp_path / "folder_entries"
    folder.mkdir()
    config = {**make_config(folder), "journals": {"alpha": str(folder)}}
    opened = open_journal("alpha", config)
    assert isinstance(opened, Folder)
    assert opened.path == folder
    assert opened.config["journal"] == str(folder)


def test_open_journal_returns_dayone_for_dotdayone_dir(tmp_path):
    from jrnl.journals import DayOne, open_journal

    dayone = tmp_path / "test.dayone"
    dayone.mkdir()
    (dayone / "entries").mkdir()
    config = {**make_config(dayone), "journals": {"alpha": str(dayone)}}
    opened = open_journal("alpha", config)
    assert isinstance(opened, DayOne)
    assert opened.path == dayone
    assert (dayone / "entries").is_dir()


# ---------------------------------------------------------------------------
# Folder journal — storage structure
# ---------------------------------------------------------------------------

def test_folder_write_creates_date_structured_files(tmp_path):
    from jrnl.journals import Folder

    folder = Folder(**make_config(tmp_path))
    folder.new_entry("Folder entry", date=datetime(2024, 3, 4, 9))
    folder.write()
    assert (tmp_path / "2024" / "03" / "04.txt").is_file()


def test_folder_from_journal_creates_folder_instance():
    from jrnl.journals import Folder

    source = make_journal(timeformat="%Y/%m/%d", tagsymbols="@")
    source.new_entry("Original @tag", date=datetime(2024, 1, 1))
    converted = Folder.from_journal(source)
    assert isinstance(converted, Folder)
    assert len(converted) == 1
