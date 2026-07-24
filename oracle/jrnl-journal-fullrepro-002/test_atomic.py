# Spec2Repo oracle - atomic tests for jrnl-journal-fullrepro-002
from datetime import datetime


def _journal(**overrides):
    from jrnl.journals import Journal

    config = {
        "encrypt": False,
        "timeformat": "%Y-%m-%d %H:%M",
        "tagsymbols": "#@",
        "default_hour": 9,
        "default_minute": 0,
        "highlight": False,
        "linewrap": 79,
        "indent_character": "|",
        "colors": {"body": "none", "date": "none", "tags": "none", "title": "none"},
    }
    config.update(overrides)
    return Journal(**config)


def test_installable_surface_exposes_metadata_and_run_entrypoint():
    import jrnl
    from jrnl.main import run

    assert jrnl.__title__ == "jrnl"
    assert isinstance(jrnl.__version__, str) and jrnl.__version__
    assert callable(run)


def test_journal_surface_exposes_documented_objects():
    from jrnl.journals import DayOne, Entry, Folder, Journal, open_journal

    assert all(callable(value) for value in (DayOne, Entry, Folder, Journal, open_journal))
    journal = Journal()
    entry = journal.new_entry("Surface", date=datetime(2024, 1, 1))
    assert list(journal) == [entry]
    assert issubclass(Folder, Journal)
    assert issubclass(DayOne, Journal)


def test_entry_splits_title_and_body():
    from jrnl.journals import Entry

    entry = Entry(_journal(), text="A title. Body text")
    assert entry.title == "A title."
    assert entry.body == "Body text"


def test_entry_fulltext_combines_title_and_body():
    from jrnl.journals import Entry

    entry = Entry(_journal(), text="Title\nBody")
    assert entry.fulltext == "Title Body"


def test_entry_parses_trailing_star_marker():
    from jrnl.journals import Entry

    entry = Entry(_journal(), text="Starred title *\nBody")
    assert entry.title == "Starred title"
    assert entry.starred is True


def test_entry_tags_are_normalized_and_deduplicated():
    from jrnl.journals import Entry

    entry = Entry(_journal(), text="Title #Mixed @Other #mixed")
    assert set(entry.tags) == {"#mixed", "@other"}


def test_entry_does_not_treat_email_address_as_tag():
    from jrnl.journals import Entry

    entry = Entry(_journal(), text="Contact person@example.com and @owner")
    assert set(entry.tags) == {"@owner"}


def test_entry_string_uses_timestamp_and_starred_storage_contract():
    from jrnl.journals import Entry

    entry = Entry(
        _journal(), datetime(2024, 2, 3, 4, 5), "Title\nBody", starred=True
    )
    stored = str(entry)
    assert stored.startswith("[2024-02-03 04:05] Title *")
    assert stored.endswith("Body\n")


def test_entry_short_display_omits_body():
    from jrnl.journals import Entry

    entry = Entry(_journal(), datetime(2024, 1, 1, 9), "Title\nBody")
    output = entry.pprint(short=True)
    assert "Title" in output
    assert "Body" not in output


def test_journal_len_and_iteration_reflect_entries():
    journal = _journal()
    first = journal.new_entry("First", date=datetime(2024, 1, 1))
    second = journal.new_entry("Second", date=datetime(2024, 1, 2))
    assert len(journal) == 2
    assert list(journal) == [first, second]


def test_journal_sort_orders_entries_chronologically():
    journal = _journal()
    journal.new_entry("Later", date=datetime(2024, 2, 1), sort=False)
    journal.new_entry("Earlier", date=datetime(2024, 1, 1), sort=False)
    journal.sort()
    assert [entry.title for entry in journal] == ["Earlier", "Later"]


def test_journal_limit_keeps_latest_entries():
    journal = _journal()
    for day in range(1, 4):
        journal.new_entry(f"Day {day}", date=datetime(2024, 1, day))
    journal.limit(2)
    assert [entry.title for entry in journal] == ["Day 2", "Day 3"]


def test_journal_tag_summaries_count_each_tag_once_per_entry():
    journal = _journal()
    journal.new_entry("One #x #x", date=datetime(2024, 1, 1))
    journal.new_entry("Two #x #y", date=datetime(2024, 1, 2))
    assert {tag.name: tag.count for tag in journal.tags} == {"#x": 2, "#y": 1}


def test_journal_filter_selects_tags_case_insensitively():
    journal = _journal()
    journal.new_entry("One #Mixed", date=datetime(2024, 1, 1))
    journal.new_entry("Two #other", date=datetime(2024, 1, 2))
    journal.filter(tags=["#MIXED"])
    assert [entry.title for entry in journal] == ["One #Mixed"]


def test_journal_filter_strict_requires_all_tags():
    journal = _journal()
    journal.new_entry("Both #x #y", date=datetime(2024, 1, 1))
    journal.new_entry("One #x", date=datetime(2024, 1, 2))
    journal.filter(tags=["#x", "#y"], strict=True)
    assert [entry.title for entry in journal] == ["Both #x #y"]


def test_journal_filter_selects_starred_entries():
    journal = _journal()
    journal.new_entry("Plain", date=datetime(2024, 1, 1))
    starred = journal.new_entry("Starred", date=datetime(2024, 1, 2))
    starred.starred = True
    journal.filter(starred=True)
    assert [entry.title for entry in journal] == ["Starred"]


def test_journal_filter_selects_containing_text_case_insensitively():
    journal = _journal()
    journal.new_entry("Alpha\nNeedle here", date=datetime(2024, 1, 1))
    journal.new_entry("Beta\nOther", date=datetime(2024, 1, 2))
    journal.filter(contains=["NEEDLE"])
    assert [entry.title for entry in journal] == ["Alpha"]


def test_plugin_registry_and_lookup_cover_documented_aliases():
    from jrnl.plugins import EXPORT_FORMATS, IMPORT_FORMATS, get_exporter, get_importer

    assert {"pretty", "short", "text", "txt", "json", "md", "markdown"} <= set(EXPORT_FORMATS)
    assert "jrnl" in IMPORT_FORMATS
    assert get_exporter("text") is get_exporter("txt")
    assert get_exporter("md") is get_exporter("markdown")
    assert get_exporter("pretty") is None
    assert get_importer("jrnl") is not None


def test_unknown_plugin_names_return_none():
    from jrnl.plugins import get_exporter, get_importer

    assert get_exporter("unknown") is None
    assert get_importer("unknown") is None


def test_encryption_selector_true_uses_jrnl_v2():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method(True) is determine_encryption_method("jrnlv2")
    assert determine_encryption_method(True) is not determine_encryption_method(False)


def test_encryption_selector_false_disables_encryption():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method(False) is not determine_encryption_method(True)


def test_encryption_selector_is_case_insensitive_for_legacy_mode():
    from jrnl.encryption import determine_encryption_method

    assert determine_encryption_method("JRNLV1") is determine_encryption_method("jrnlv1")
    assert determine_encryption_method("jrnlv1") is not determine_encryption_method("jrnlv2")


def test_encryption_methods_exposes_disabled_mode():
    from jrnl.encryption import EncryptionMethods

    assert EncryptionMethods.NONE.value == "NoEncryption"


def test_encryption_methods_exposes_legacy_mode():
    from jrnl.encryption import EncryptionMethods

    assert EncryptionMethods.JRNLV1.value == "Jrnlv1Encryption"


def test_encryption_methods_exposes_current_mode():
    from jrnl.encryption import EncryptionMethods

    assert EncryptionMethods.JRNLV2.value == "Jrnlv2Encryption"
