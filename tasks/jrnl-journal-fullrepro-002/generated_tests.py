import subprocess
import sys
from types import SimpleNamespace


def test_installable_surface_exposes_title_version_and_run_entrypoint():
    import jrnl
    from jrnl.main import run

    assert jrnl.__title__ == "jrnl"
    assert isinstance(jrnl.__version__, str)
    assert callable(run)


def test_cli_entry_help_returns_success():
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_journal_entry_parses_title_body_star_and_tags():
    from jrnl.journals.Entry import Entry

    entry = Entry(SimpleNamespace(config={"tagsymbols": "@"}), text="A title\nBody with @tag")

    assert entry.title == "A title"
    assert "Body" in entry.body
    assert "@tag" in entry.tags


def test_entry_fulltext_combines_title_and_body():
    from jrnl.journals.Entry import Entry

    entry = Entry(SimpleNamespace(config={"tagsymbols": "#"}), text="Title line\nBody line")

    assert entry.fulltext == "Title line Body line"


def test_display_export_plugins_are_publicly_importable():
    from jrnl.plugins.json_exporter import JSONExporter
    from jrnl.plugins.markdown_exporter import MarkdownExporter
    from jrnl.plugins.text_exporter import TextExporter

    assert JSONExporter.__name__ == "JSONExporter"
    assert MarkdownExporter.__name__ == "MarkdownExporter"
    assert TextExporter.__name__ == "TextExporter"


def test_missing_config_path_reports_handled_cli_error(tmp_path):
    missing = tmp_path / "missing.yaml"
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(missing), "--list"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode != 0
    assert "config" in (result.stdout + result.stderr).lower()


def test_import_version_is_public_nonempty_string():
    import jrnl

    assert isinstance(jrnl.__version__, str)
    assert jrnl.__version__


def test_daily_journaling_dry_run_help_surfaces_write_and_search_options():
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    help_text = result.stdout.lower()
    assert "--config-file" in help_text
    assert "--format" in help_text
    assert "search" in help_text or "filter" in help_text
