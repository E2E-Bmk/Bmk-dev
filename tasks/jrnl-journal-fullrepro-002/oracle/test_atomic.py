# Spec2Repo oracle - atomic tests for jrnl-journal-fullrepro-002
import subprocess
import sys
from types import SimpleNamespace


def test_installable_surface_exposes_title_version_and_run_entrypoint():
    import jrnl
    from jrnl.main import run

    assert jrnl.__title__ == "jrnl"
    assert isinstance(jrnl.__version__, str)
    assert callable(run)


def test_journal_entry_parses_title_body_star_and_tags():
    from jrnl.journals import Entry

    entry = Entry(SimpleNamespace(config={"tagsymbols": "@"}), text="A title\nBody with @tag")

    assert entry.title == "A title"
    assert "Body" in entry.body
    assert "@tag" in entry.tags


def test_entry_fulltext_combines_title_and_body():
    from jrnl.journals import Entry

    entry = Entry(SimpleNamespace(config={"tagsymbols": "#"}), text="Title line\nBody line")

    assert entry.fulltext == "Title line Body line"


def test_display_export_plugins_are_publicly_importable():
    from jrnl.plugins import JSONExporter, MarkdownExporter, TextExporter

    assert JSONExporter.__name__ == "JSONExporter"
    assert MarkdownExporter.__name__ == "MarkdownExporter"
    assert TextExporter.__name__ == "TextExporter"


def test_import_version_is_public_nonempty_string():
    import jrnl

    assert isinstance(jrnl.__version__, str)
    assert jrnl.__version__


def test_journal_package_exposes_documented_public_objects():
    from jrnl.journals import DayOne, Entry, Folder, Journal, open_journal

    assert DayOne.__name__ == "DayOne"
    assert Entry.__name__ == "Entry"
    assert Folder.__name__ == "Folder"
    assert Journal.__name__ == "Journal"
    assert callable(open_journal)


def test_plugin_registry_exposes_documented_builtin_formats():
    from jrnl.plugins import EXPORT_FORMATS, IMPORT_FORMATS

    expected_exports = {"pretty", "short", "text", "json", "md", "markdown", "tags"}

    assert expected_exports.issubset(set(EXPORT_FORMATS))
    assert "jrnl" in IMPORT_FORMATS


def test_get_exporter_maps_documented_public_format_names():
    from jrnl.plugins import JSONExporter, MarkdownExporter, TextExporter, get_exporter

    assert get_exporter("json") is JSONExporter
    assert get_exporter("md") is MarkdownExporter
    assert get_exporter("text") is TextExporter
    assert get_exporter("pretty") is None
    assert get_exporter("not-a-format") is None


def test_entry_tags_are_normalized_for_configured_symbols():
    from jrnl.journals import Entry

    entry = Entry(
        SimpleNamespace(config={"tagsymbols": "#@"}),
        text="Title #Mixed @Other #mixed",
    )

    assert set(entry.tags) == {"#mixed", "@other"}
