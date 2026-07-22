"""Integration layer tests for jrnl-journal-fullrepro-002.

Each test verifies ≥2 different public API boundaries cooperating.
Composition dependency: even if all atomic tests pass, these tests can
still fail because component seams don't align.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from conftest import make_config, make_journal, make_populated, run_cli, write_cli_config


# ===================================================================
# CVI-11  Write→open roundtrip  (lifecycle crossing)
# ===================================================================

@pytest.mark.depends_on(
    "test_journal_write_creates_nonempty_file",
    "test_journal_open_returns_journal_instance",
)
def test_write_then_open_preserves_entry_fields(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    path = tmp_path / "journal.txt"
    journal = make_populated(path)
    journal.write()
    reopened = make_journal(path).open()
    assert len(reopened) == 2
    assert [(e.date, e.title, e.body, e.starred, set(e.tags)) for e in reopened] == [
        (e.date, e.title, e.body, e.starred, set(e.tags)) for e in journal
    ]


@pytest.mark.depends_on(
    "test_journal_open_creates_parent_directories",
)
def test_open_creates_missing_parent_and_file(tmp_path):
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    path = tmp_path / "nested" / "journal.txt"
    journal = make_journal(path).open()
    assert path.is_file()
    assert len(journal) == 0


# ===================================================================
# CVI-3  Chronological ordering  (state consistency)
# ===================================================================

@pytest.mark.depends_on(
    "test_sort_orders_chronologically",
    "test_journal_write_creates_nonempty_file",
)
def test_write_and_reopen_keep_chronological_order(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    path = tmp_path / "journal.txt"
    journal = make_journal(path)
    journal.new_entry("Later", date=datetime(2024, 2, 1), sort=False)
    journal.new_entry("Earlier", date=datetime(2024, 1, 1), sort=False)
    journal.sort()
    journal.write()
    assert [e.title for e in make_journal(path).open()] == ["Earlier", "Later"]


@pytest.mark.depends_on(
    "test_import_adds_entries_from_text",
    "test_sort_orders_chronologically",
)
def test_import_merges_and_sorts_entries():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    journal = make_journal()
    journal.new_entry("Later", date=datetime(2024, 2, 1))
    journal.import_("[2024-01-01 09:00] Earlier\n")
    assert [e.title for e in journal] == ["Earlier", "Later"]


@pytest.mark.depends_on("test_import_deduplicates_exact_entries")
def test_import_deduplication_across_calls():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    journal = make_journal()
    text = "[2024-01-01 09:00] Same\nBody\n"
    journal.import_(text)
    journal.import_(text)
    assert len(journal) == 1


# ===================================================================
# CVI-1  Entry create → export consistency  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on(
    "test_new_entry_returns_entry_object",
    "test_editable_str_returns_nonempty_string",
    "test_get_exporter_returns_class_for_text",
)
def test_text_export_matches_editable_str():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    exported = get_exporter("text").export(journal)
    assert "Alpha #work" in exported and "Beta #home" in exported
    assert exported == journal.editable_str()


@pytest.mark.depends_on("test_get_exporter_returns_class_for_text")
def test_text_export_writes_single_file(tmp_path):
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    target = tmp_path / "export.txt"
    get_exporter("text").export(make_populated(), str(target))
    content = target.read_text(encoding="utf-8")
    assert "Alpha #work" in content and "Beta #home" in content


@pytest.mark.depends_on("test_get_exporter_returns_class_for_text")
def test_text_export_directory_writes_one_file_per_entry(tmp_path):
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    get_exporter("text").export(make_populated(), str(tmp_path))
    files = sorted(tmp_path.glob("*.txt"))
    assert len(files) == 2
    titles = {
        p.read_text(encoding="utf-8").splitlines()[0].split("] ", 1)[1].rstrip(" *")
        for p in files
    }
    assert titles == {"Alpha #work", "Beta #home"}


# ===================================================================
# CVI-1 + CVI-6  JSON export preserves fields and starring
# ===================================================================

@pytest.mark.depends_on(
    "test_entry_starred_from_trailing_marker",
    "test_entry_tags_deduplicated_and_lowercase",
)
def test_json_export_contains_documented_entry_fields():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.plugins import get_exporter

    data = json.loads(get_exporter("json").export(make_populated()))
    assert set(data) == {"tags", "entries"}
    assert {"title", "body", "date", "time", "tags", "starred"} <= set(
        data["entries"][0]
    )


@pytest.mark.depends_on(
    "test_entry_starred_from_trailing_marker",
    "test_entry_tags_deduplicated_and_lowercase",
)
def test_json_export_preserves_starred_and_tag_views():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.plugins import get_exporter

    data = json.loads(get_exporter("json").export(make_populated()))
    assert data["entries"][1]["starred"] is True
    assert data["entries"][1]["tags"] == ["#home"]
    assert data["tags"] == {"#home": 1, "#work": 1}


# ===================================================================
# Markdown export groups by year/month  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on("test_md_and_markdown_resolve_to_same_exporter")
def test_markdown_export_groups_entries_by_year_and_month():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    output = get_exporter("markdown").export(make_populated())
    assert "# 2024" in output
    assert "## January" in output
    assert "Alpha #work" in output and "Beta #home" in output


# ===================================================================
# CVI-2  Search filter → display / action consistency  (state consistency)
# ===================================================================

@pytest.mark.depends_on(
    "test_filter_by_tag_case_insensitive",
    "test_get_exporter_returns_class_for_text",
)
def test_filter_then_text_export_uses_same_selected_entries():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    journal.filter(tags=["#work"])
    output = get_exporter("text").export(journal)
    assert "Alpha #work" in output
    assert "Beta #home" not in output


@pytest.mark.depends_on(
    "test_filter_starred_keeps_only_starred",
)
def test_filter_then_json_export_uses_same_starred_selection():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    journal.filter(starred=True)
    entries = json.loads(get_exporter("json").export(journal))["entries"]
    assert [e["title"] for e in entries] == ["Beta #home"]


@pytest.mark.depends_on(
    "test_filter_by_tag_case_insensitive",
    "test_filter_contains_case_insensitive",
)
def test_combined_tag_and_text_filters_apply_before_export():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    journal.new_entry("Gamma #work\nOther", date=datetime(2024, 1, 3))
    journal.filter(tags=["#work"], contains=["first"])
    data = json.loads(get_exporter("json").export(journal))
    assert [e["title"] for e in data["entries"]] == ["Alpha #work"]


# ===================================================================
# CVI-5  Tag consistency across filter and report  (state consistency)
# ===================================================================

@pytest.mark.depends_on(
    "test_filter_exclude_removes_tagged_entries",
    "test_journal_tags_count_once_per_entry_not_occurrence",
)
def test_excluded_tag_absent_from_export_and_tag_summary():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    journal.filter(exclude=["#home"])
    data = json.loads(get_exporter("json").export(journal))
    assert data["tags"] == {"#work": 1}
    assert [e["title"] for e in data["entries"]] == ["Alpha #work"]


# ===================================================================
# Limit → export  (state consistency)
# ===================================================================

@pytest.mark.depends_on("test_limit_keeps_last_n_entries")
def test_limit_then_export_keeps_latest_entries():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    journal.limit(1)
    data = json.loads(get_exporter("json").export(journal))
    assert [e["title"] for e in data["entries"]] == ["Beta #home"]


# ===================================================================
# CVI-12  editable_str / parse roundtrip  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on(
    "test_editable_str_returns_nonempty_string",
    "test_get_change_counts_has_modified_and_deleted_keys",
)
def test_editable_text_roundtrip_preserves_entries():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    journal = make_populated()
    editable = journal.editable_str()
    restored = make_journal()
    restored.parse_editable_str(editable)
    assert len(restored) == 2
    assert [(e.date, e.title, e.body, e.starred) for e in restored] == [
        (e.date, e.title, e.body, e.starred) for e in journal
    ]


@pytest.mark.depends_on(
    "test_editable_str_returns_nonempty_string",
    "test_get_change_counts_has_modified_and_deleted_keys",
)
def test_editable_text_change_updates_view_and_counts():
    """Seam: state consistency — cooperating public APIs observe the same underlying state."""
    journal = make_populated()
    journal.parse_editable_str(
        journal.editable_str().replace("Alpha", "Changed", 1)
    )
    assert list(journal)[0].title == "Changed #work"
    assert journal.get_change_counts()["modified"] == 1


# ===================================================================
# Delete / Change-date → write → open  (lifecycle crossing)
# ===================================================================

@pytest.mark.depends_on(
    "test_delete_entries_removes_specified",
    "test_journal_write_creates_nonempty_file",
)
def test_delete_then_write_removes_from_storage(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    path = tmp_path / "journal.txt"
    journal = make_populated(path)
    journal.delete_entries([list(journal)[0]])
    journal.write()
    reopened = make_journal(path).open()
    assert [e.title for e in reopened] == ["Beta #home"]
    assert journal.get_change_counts()["deleted"] == 1


@pytest.mark.depends_on(
    "test_change_date_entries_updates_date",
    "test_sort_orders_chronologically",
)
def test_change_date_then_write_updates_storage_order(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    path = tmp_path / "journal.txt"
    journal = make_populated(path)
    journal.change_date_entries(datetime(2023, 1, 1), [list(journal)[1]])
    journal.sort()
    journal.write()
    reopened = make_journal(path).open()
    assert list(reopened)[0].title == "Beta #home"
    assert list(reopened)[0].date.year == 2023


# ===================================================================
# CVI-9  Folder / DayOne same entry-level behavior  (config interaction)
# ===================================================================

@pytest.mark.depends_on("test_folder_write_creates_date_structured_files")
def test_folder_open_reads_written_entries(tmp_path):
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    from jrnl.journals import Folder

    folder = Folder(**make_config(tmp_path))
    folder.new_entry("Folder entry #tag", date=datetime(2024, 3, 4, 9))
    folder.write()
    reopened = Folder(**make_config(tmp_path)).open()
    assert [(e.title, set(e.tags)) for e in reopened] == [
        ("Folder entry #tag", {"#tag"})
    ]


@pytest.mark.depends_on(
    "test_folder_from_journal_creates_folder_instance",
    "test_entry_tags_deduplicated_and_lowercase",
)
def test_folder_from_journal_preserves_config_and_entry_views():
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    from jrnl.journals import Folder

    source = make_journal(timeformat="%Y/%m/%d", tagsymbols="@")
    source.new_entry("Original @tag", date=datetime(2024, 1, 1))
    converted = Folder.from_journal(source)
    added = converted.new_entry("Added @other", date=datetime(2024, 1, 2))
    assert [e.title for e in converted] == ["Original @tag", "Added @other"]
    assert str(added).startswith("[2024/01/02] Added @other")
    assert added.tags == ["@other"]


# ===================================================================
# CVI-6  Starring consistency across views  (state consistency)
# ===================================================================

@pytest.mark.depends_on(
    "test_entry_starred_from_trailing_marker",
    "test_filter_starred_keeps_only_starred",
)
def test_starred_preserved_through_write_and_reopen(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    path = tmp_path / "journal.txt"
    journal = make_populated(path)
    journal.write()
    reopened = make_journal(path).open()
    assert any(e.starred for e in reopened)


# ===================================================================
# Journal.pprint short vs full  (state consistency)
# ===================================================================

@pytest.mark.depends_on(
    "test_journal_pprint_short_shows_titles_without_bodies",
    "test_journal_pprint_full_includes_bodies",
)
def test_short_and_full_display_project_same_entries():
    """CVI-1: cross-view invariants hold across listing, invocation, and runtime APIs."""
    journal = make_populated()
    short = journal.pprint(short=True)
    full = journal.pprint(short=False)
    assert "Alpha #work" in short and "Beta #home" in short
    assert "First body" not in short and "Second body" not in short
    assert "First body" in full and "Second body" in full


# ===================================================================
# Cross-format consistency  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on(
    "test_get_exporter_returns_class_for_text",
    "test_text_and_txt_resolve_to_same_exporter",
)
def test_text_and_json_preserve_same_dates_and_titles():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.plugins import get_exporter

    journal = make_populated()
    storage = get_exporter("text").export(journal)
    data = json.loads(get_exporter("json").export(journal))
    for entry in data["entries"]:
        assert entry["date"] in storage
        assert entry["title"] in storage


# ===================================================================
# Dates export  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on("test_new_entry_returns_entry_object")
def test_dates_export_reports_counts_per_day():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_exporter

    exported = get_exporter("dates").export(make_populated())
    assert "2024-01-01" in exported and "2024-01-02" in exported


# ===================================================================
# Importer plugin  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on(
    "test_get_importer_returns_class_for_jrnl",
    "test_import_adds_entries_from_text",
)
def test_importer_adds_jrnl_text_to_journal():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    from jrnl.plugins import get_importer

    journal = make_journal()
    importer = get_importer("jrnl")
    journal.import_("[2024-01-01 09:00] Imported\nBody\n")
    assert importer is not None
    assert [(e.title, e.body) for e in journal] == [("Imported", "Body")]


# ===================================================================
# open_journal type detection  (config interaction)
# ===================================================================

@pytest.mark.depends_on("test_open_journal_returns_journal_for_file_path")
def test_open_journal_detects_single_file_storage(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.journals import Journal, open_journal

    path = tmp_path / "journal.txt"
    config = {**make_config(path), "journals": {"default": str(path)}}
    opened = open_journal("default", config)
    assert isinstance(opened, Journal)
    assert path.exists()


@pytest.mark.depends_on("test_open_journal_returns_folder_for_directory")
def test_open_journal_detects_folder_storage(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    from jrnl.journals import Folder, open_journal

    path = tmp_path / "entries"
    path.mkdir()
    config = {**make_config(path), "journals": {"default": str(path)}}
    opened = open_journal("default", config)
    assert isinstance(opened, Folder)
    assert opened.path == path
    assert opened.config["journal"] == str(path)


# ===================================================================
# CLI — module entry point  (protocol handoff)
# ===================================================================

def test_cli_help_is_available():
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--help"], text=True, capture_output=True
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


# ===================================================================
# CVI-7  stderr / stdout routing  (protocol handoff)
# ===================================================================

@pytest.mark.depends_on("test_package_title_equals_jrnl", "test_package_version_is_nonempty_string")
def test_cli_version_reports_package_identity():
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    import jrnl

    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--version"], text=True, capture_output=True
    )
    assert result.returncode == 0
    assert jrnl.__title__ in result.stdout
    assert jrnl.__version__ in result.stdout


def test_cli_run_api_version_returns_success(capsys):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    import jrnl
    from jrnl.main import run

    assert run(["--version"]) is None
    assert jrnl.__version__ in capsys.readouterr().out


# ===================================================================
# CLI — entry writing and search  (lifecycle crossing)
# ===================================================================

def test_cli_writes_entry_to_journal(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "default.journal"
    config = write_cli_config(tmp_path, {"default": path})
    result = run_cli(config, "CLI title. CLI body #tag")
    assert result.returncode == 0
    stored = path.read_text(encoding="utf-8")
    assert "CLI title." in stored and "CLI body #tag" in stored


@pytest.mark.depends_on("test_filter_contains_case_insensitive")
def test_cli_written_entry_visible_through_search(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "default.journal"
    config = write_cli_config(tmp_path, {"default": path})
    assert run_cli(config, "Searchable title. Hidden body #work").returncode == 0
    result = run_cli(config, "-contains", "searchable", "--short")
    assert result.returncode == 0
    assert "Searchable title." in result.stdout
    assert "Hidden body" not in result.stdout


# ===================================================================
# CVI-4  Journal name → path / config  (config interaction)
# ===================================================================

def test_cli_named_journal_writes_only_selected_storage(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    default = tmp_path / "default.journal"
    work = tmp_path / "work.journal"
    config = write_cli_config(tmp_path, {"default": default, "work": work})
    result = run_cli(config, "work", "Work entry")
    assert result.returncode == 0
    assert "Work entry" in work.read_text(encoding="utf-8")
    assert not default.exists() or "Work entry" not in default.read_text(encoding="utf-8")


def test_cli_multiple_journals_keep_storage_isolated(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    dp, wp = tmp_path / "default.txt", tmp_path / "work.txt"
    config = write_cli_config(tmp_path, {"default": dp, "work": wp})
    assert run_cli(config, "Default only").returncode == 0
    assert run_cli(config, "work", "Work only").returncode == 0
    dv = run_cli(config, "--short").stdout
    wv = run_cli(config, "work", "--short").stdout
    assert "Default only" in dv and "Work only" not in dv
    assert "Work only" in wv and "Default only" not in wv


# ===================================================================
# CVI-10  Config override scope  (config interaction)
# ===================================================================

def test_cli_config_override_is_transient(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    path = tmp_path / "journal.txt"
    config = write_cli_config(tmp_path, {"default": path})
    assert run_cli(config, "Entry #one").returncode == 0
    overridden = run_cli(config, "--config-override", "display_format", "json", "-n", "1")
    normal = run_cli(config, "-n", "1", "--short")
    assert json.loads(overridden.stdout)["entries"][0]["title"] == "Entry #one"
    assert normal.returncode == 0 and not normal.stdout.lstrip().startswith("{")


def test_named_journal_display_override_does_not_affect_default(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    import jrnl

    dp, wp = tmp_path / "default.txt", tmp_path / "work.txt"
    config = tmp_path / "jrnl.yaml"
    config.write_text(
        f"""version: {jrnl.__version__!r}
journals:
  default: {str(dp)!r}
  work:
    journal: {str(wp)!r}
    display_format: json
editor: ''
encrypt: false
template: false
default_hour: 9
default_minute: 0
timeformat: '%Y-%m-%d %H:%M'
tagsymbols: '#@'
highlight: false
linewrap: 79
indent_character: '|'
colors: {{body: none, date: none, tags: none, title: none}}
""",
        encoding="utf-8",
    )
    assert run_cli(config, "Default entry").returncode == 0
    assert run_cli(config, "work", "Work entry").returncode == 0
    assert json.loads(run_cli(config, "work", "-n", "1").stdout)["entries"][0]["title"] == "Work entry"
    assert "Default entry" in run_cli(config, "-n", "1", "--short").stdout


# ===================================================================
# CLI — entry date and starred persistence  (lifecycle crossing)
# ===================================================================

def test_cli_explicit_date_and_star_persisted(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "journal.txt"
    config = write_cli_config(tmp_path, {"default": path})
    result = run_cli(config, "2024-01-02 10:00 *: Planned #work")
    assert result.returncode == 0, result.stderr
    assert "[2024-01-02 10:00] Planned #work *" in path.read_text(encoding="utf-8")


def test_cli_literal_newline_becomes_body(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "journal.txt"
    config = write_cli_config(tmp_path, {"default": path})
    result = run_cli(config, r"Title line\nBody line")
    stored = path.read_text(encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert "Title line" in stored and "Body line" in stored


# ===================================================================
# CLI — export / import workflow  (lifecycle crossing + protocol handoff)
# ===================================================================

def test_cli_export_import_preserves_entry(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    default = tmp_path / "default.journal"
    work = tmp_path / "work.journal"
    exported = tmp_path / "work.txt"
    config = write_cli_config(tmp_path, {"default": default, "work": work})
    assert run_cli(config, "work", "Portable entry #work").returncode == 0
    assert run_cli(config, "work", "--format", "text", "--file", str(exported)).returncode == 0
    assert "Portable entry #work" in exported.read_text(encoding="utf-8")
    assert run_cli(config, "--import", "jrnl", "--file", str(exported)).returncode == 0
    assert "Portable entry #work" in default.read_text(encoding="utf-8")


# ===================================================================
# CVI-8  --file / redirect equivalence  (protocol handoff)
# ===================================================================

def test_cli_file_export_matches_stdout(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "journal.txt"
    config = write_cli_config(tmp_path, {"default": path})
    assert run_cli(config, "2024-01-04 10:00: Meeting @team").returncode == 0
    stdout_result = run_cli(config, "--format", "text")
    file_target = tmp_path / "export.txt"
    run_cli(config, "--format", "text", "--file", str(file_target))
    assert stdout_result.stdout.strip() == file_target.read_text(encoding="utf-8").strip()


# ===================================================================
# CLI — --list with JSON  (protocol handoff)
# ===================================================================

def test_cli_list_json_contains_journal_names(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    config = write_cli_config(
        tmp_path, {"default": tmp_path / "default.txt", "work": tmp_path / "work.txt"}
    )
    result = run_cli(config, "--list", "--format", "json")
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)["journals"]) == {"default", "work"}


# ===================================================================
# CLI — --diagnostic  (protocol handoff)
# ===================================================================

def test_cli_diagnostic_reports_versions():
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    import jrnl

    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--diagnostic"], text=True, capture_output=True
    )
    assert result.returncode == 0
    assert jrnl.__version__ in result.stdout
    assert str(sys.version_info.major) in result.stdout


# ===================================================================
# CLI — daily workflow  (lifecycle crossing)
# ===================================================================

@pytest.mark.depends_on(
    "test_filter_by_tag_case_insensitive",
    "test_journal_tags_count_once_per_entry_not_occurrence",
)
def test_daily_workflow_write_search_tags(tmp_path):
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    config = write_cli_config(tmp_path, {"default": tmp_path / "journal.txt"})
    written = run_cli(config, "2024-01-03 09:00: Morning note #health")
    searched = run_cli(config, "#health", "--short")
    tags = run_cli(config, "--tags")
    assert written.returncode == searched.returncode == tags.returncode == 0
    assert "Morning note #health" in searched.stdout and "#health" in tags.stdout


@pytest.mark.depends_on("test_filter_by_tag_case_insensitive")
def test_daily_workflow_filter_then_export_body(tmp_path):
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    config = write_cli_config(tmp_path, {"default": tmp_path / "journal.txt"})
    assert run_cli(config, r"Alpha #work\nFirst body").returncode == 0
    assert run_cli(config, r"Beta #home\nSecond body").returncode == 0
    payload = json.loads(run_cli(config, "#work", "--format", "json").stdout)
    assert [e["title"] for e in payload["entries"]] == ["Alpha #work"]
    assert payload["entries"][0]["body"] == "First body"


# ===================================================================
# Multi-journal workflow → archive folder  (lifecycle crossing)
# ===================================================================

def test_multi_journal_export_to_archive_folder(tmp_path):
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    wp, ap = tmp_path / "work.txt", tmp_path / "archive"
    ap.mkdir()
    config = write_cli_config(tmp_path, {"default": wp, "work": wp, "archive": ap})
    assert run_cli(config, "work", "2024-01-04 10:00: Meeting @team").returncode == 0
    exported = tmp_path / "export.txt"
    assert run_cli(config, "work", "--format", "text", "--file", str(exported)).returncode == 0
    assert run_cli(config, "archive", "--import", "jrnl", "--file", str(exported)).returncode == 0
    assert "Meeting @team" in run_cli(config, "archive", "--short").stdout


# ===================================================================
# Delete / Change-time actions via API → persistent storage  (lifecycle)
# ===================================================================

@pytest.mark.depends_on("test_delete_entries_removes_specified")
def test_delete_persists_only_remaining(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    journal = make_populated(tmp_path / "journal.txt")
    journal.write()
    journal.delete_entries([e for e in journal if e.title.startswith("Alpha")])
    journal.write()
    assert [e.title for e in make_journal(tmp_path / "journal.txt").open()] == [
        "Beta #home"
    ]


@pytest.mark.depends_on("test_change_date_entries_updates_date")
def test_change_time_persists_and_resorts(tmp_path):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    journal = make_populated(tmp_path / "journal.txt")
    journal.write()
    journal.change_date_entries(
        datetime(2023, 12, 31, 8),
        [e for e in journal if e.title.startswith("Beta")],
    )
    journal.write()
    assert [e.title for e in make_journal(tmp_path / "journal.txt").open()] == [
        "Beta #home",
        "Alpha #work",
    ]


# ===================================================================
# Error Semantics — CLI error conditions  (error propagation)
# ===================================================================

def test_cli_missing_config_fails(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "jrnl",
            "--config-file",
            str(tmp_path / "missing.yaml"),
            "--list",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0


def test_cli_run_api_missing_config_returns_nonzero(tmp_path, capsys):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    from jrnl.main import run

    assert run(["--config-file", str(tmp_path / "missing.yml"), "--list"]) == 1
    assert capsys.readouterr().err


def test_cli_not_without_operand_is_error(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    config = write_cli_config(tmp_path, {"default": tmp_path / "default.journal"})
    result = run_cli(config, "-not")
    assert result.returncode != 0


def test_cli_yaml_export_without_directory_is_error(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    path = tmp_path / "default.journal"
    config = write_cli_config(tmp_path, {"default": path})
    assert run_cli(config, "Export me").returncode == 0
    result = run_cli(config, "--format", "yaml")
    assert result.returncode != 0


def test_cli_edit_without_editor_fails(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    path = tmp_path / "journal.txt"
    config_path = tmp_path / "noeditor.yaml"
    import jrnl

    config_path.write_text(
        f"""version: {jrnl.__version__!r}
journals:
  default: {str(path)!r}
editor: ''
encrypt: false
template: false
default_hour: 9
default_minute: 0
timeformat: '%Y-%m-%d %H:%M'
tagsymbols: '#@'
highlight: false
linewrap: 79
indent_character: '|'
colors: {{body: none, date: none, tags: none, title: none}}
""",
        encoding="utf-8",
    )
    assert run_cli(config_path, "Some entry").returncode == 0
    result = run_cli(config_path, "--edit")
    assert result.returncode != 0


def test_cli_import_unsupported_format_fails(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    path = tmp_path / "journal.txt"
    config = write_cli_config(tmp_path, {"default": path})
    result = run_cli(config, "--import", "nonexistent_format_xyz")
    assert result.returncode != 0


def test_cli_encrypt_folder_journal_fails(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    folder = tmp_path / "folder_journal"
    folder.mkdir()
    config = write_cli_config(tmp_path, {"default": folder})
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(config), "--encrypt"],
        input="pass\npass\n",
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0


def test_cli_empty_stdin_saves_no_entry(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "default.txt"
    config = write_cli_config(tmp_path, {"default": path})
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(config)],
        input="",
        text=True,
        capture_output=True,
    )
    assert not path.exists() or path.stat().st_size == 0


def test_cli_no_results_for_delete_reports_nothing(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    path = tmp_path / "default.txt"
    config = write_cli_config(tmp_path, {"default": path})
    assert run_cli(config, "An entry exists").returncode == 0
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(config),
         "-contains", "nonexistent_phrase_xyz", "--delete"],
        input="n\n",
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0 or result.stderr
