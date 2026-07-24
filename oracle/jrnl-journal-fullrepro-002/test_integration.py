# Spec2Repo oracle - integration and end-to-end tests for jrnl-journal-fullrepro-002
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest


def _config(path=None, **overrides):
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
    if path is not None:
        config["journal"] = str(path)
    config.update(overrides)
    return config


def _journal(path=None, **overrides):
    from jrnl.journals import Journal

    return Journal(**_config(path, **overrides))


def _populated(path=None):
    journal = _journal(path)
    journal.new_entry("Alpha #work\nFirst body", date=datetime(2024, 1, 1, 9))
    second = journal.new_entry("Beta #home\nSecond body", date=datetime(2024, 1, 2, 10))
    second.starred = True
    return journal


def _write_config(tmp_path, journals):
    import jrnl

    config = tmp_path / "jrnl.yaml"
    journal_lines = []
    for name, path in journals.items():
        journal_lines.append(f"  {name}: {json.dumps(str(path))}")
    config.write_text(
        "\n".join(
            [
                f"version: {json.dumps(jrnl.__version__)}",
                "journals:",
                *journal_lines,
                "editor: ''",
                "encrypt: false",
                "template: false",
                "default_hour: 9",
                "default_minute: 0",
                "timeformat: '%Y-%m-%d %H:%M'",
                "tagsymbols: '#@'",
                "highlight: false",
                "linewrap: 79",
                "indent_character: '|'",
                "colors:",
                "  body: none",
                "  date: none",
                "  tags: none",
                "  title: none",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config


def _run_cli(config, *args):
    return subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(config), *args],
        text=True,
        capture_output=True,
    )


def test_cli_help_is_available_through_module_entrypoint():
    result = subprocess.run([sys.executable, "-m", "jrnl", "--help"], text=True, capture_output=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_cli_run_api_help_returns_success(capsys):
    from jrnl.main import run

    with pytest.raises(SystemExit) as exc_info:
        run(["--help"])
    assert exc_info.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_cli_run_api_version_returns_success(capsys):
    import jrnl
    from jrnl.main import run

    assert run(["--version"]) is None
    assert jrnl.__version__ in capsys.readouterr().out


def test_cli_run_api_handles_missing_config_as_failure(tmp_path, capsys):
    from jrnl.main import run

    assert run(["--config-file", str(tmp_path / "missing.yml"), "--list"]) == 1
    assert capsys.readouterr().err


def test_cli_missing_config_fails_before_journal_operations(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "jrnl", "--config-file", str(tmp_path / "missing.yaml"), "--list"],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert not list(tmp_path.glob("*.journal"))


def test_cli_writes_entry_to_alternate_config_default_journal(tmp_path):
    path = tmp_path / "default.journal"
    config = _write_config(tmp_path, {"default": path})
    result = _run_cli(config, "CLI title. CLI body #tag")
    assert result.returncode == 0
    stored = path.read_text(encoding="utf-8")
    assert "CLI title." in stored and "CLI body #tag" in stored


def test_cli_named_journal_writes_only_selected_storage(tmp_path):
    default = tmp_path / "default.journal"
    work = tmp_path / "work.journal"
    config = _write_config(tmp_path, {"default": default, "work": work})
    result = _run_cli(config, "work", "Work entry")
    assert result.returncode == 0
    assert "Work entry" in work.read_text(encoding="utf-8")
    assert not default.exists() or "Work entry" not in default.read_text(encoding="utf-8")


def test_cli_written_entry_is_visible_through_search_and_short_display(tmp_path):
    path = tmp_path / "default.journal"
    config = _write_config(tmp_path, {"default": path})
    assert _run_cli(config, "Searchable title. Hidden body #work").returncode == 0
    result = _run_cli(config, "-contains", "searchable", "--short")
    assert result.returncode == 0
    assert "Searchable title." in result.stdout
    assert "Hidden body" not in result.stdout


def test_cli_not_without_supported_operand_is_an_error(tmp_path):
    config = _write_config(tmp_path, {"default": tmp_path / "default.journal"})
    result = _run_cli(config, "-not")
    assert result.returncode != 0


def test_cli_yaml_export_without_directory_target_is_an_error(tmp_path):
    path = tmp_path / "default.journal"
    config = _write_config(tmp_path, {"default": path})
    assert _run_cli(config, "Export me").returncode == 0
    result = _run_cli(config, "--format", "yaml")
    assert result.returncode != 0


def test_cli_multiple_journal_export_import_workflow_preserves_entry(tmp_path):
    default = tmp_path / "default.journal"
    work = tmp_path / "work.journal"
    exported = tmp_path / "work.txt"
    config = _write_config(tmp_path, {"default": default, "work": work})
    assert _run_cli(config, "work", "Portable entry #work").returncode == 0
    export_result = _run_cli(config, "work", "--format", "text", "--file", str(exported))
    assert export_result.returncode == 0
    assert "Portable entry #work" in exported.read_text(encoding="utf-8")
    import_result = _run_cli(config, "--import", "jrnl", "--file", str(exported))
    assert import_result.returncode == 0
    assert "Portable entry #work" in default.read_text(encoding="utf-8")


def test_write_then_open_preserves_entry_fields(tmp_path):
    path = tmp_path / "journal.txt"
    journal = _populated(path)
    journal.write()
    reopened = _journal(path).open()
    assert len(reopened) == 2
    assert [(e.date, e.title, e.body, e.starred, set(e.tags)) for e in reopened] == [
        (e.date, e.title, e.body, e.starred, set(e.tags)) for e in journal
    ]


def test_open_creates_missing_parent_and_file(tmp_path):
    path = tmp_path / "nested" / "journal.txt"
    journal = _journal(path).open()
    assert path.is_file()
    assert len(journal) == 0


def test_write_and_reopen_keep_chronological_order(tmp_path):
    path = tmp_path / "journal.txt"
    journal = _journal(path)
    journal.new_entry("Later", date=datetime(2024, 2, 1), sort=False)
    journal.new_entry("Earlier", date=datetime(2024, 1, 1), sort=False)
    journal.sort()
    journal.write()
    assert [e.title for e in _journal(path).open()] == ["Earlier", "Later"]


def test_import_merges_and_sorts_entries():
    journal = _journal()
    journal.new_entry("Later", date=datetime(2024, 2, 1))
    journal.import_("[2024-01-01 09:00] Earlier\n")
    assert [e.title for e in journal] == ["Earlier", "Later"]


def test_import_deduplicates_equal_entries():
    journal = _journal()
    text = "[2024-01-01 09:00] Same\nBody\n"
    journal.import_(text)
    journal.import_(text)
    assert len(journal) == 1


def test_editable_text_roundtrip_preserves_entries():
    journal = _populated()
    editable = journal.editable_str()
    restored = _journal()
    restored.parse_editable_str(editable)
    assert len(restored) == 2
    assert [(e.date, e.title, e.body, e.starred) for e in restored] == [
        (e.date, e.title, e.body, e.starred) for e in journal
    ]


def test_editable_text_change_updates_public_entry_view():
    journal = _populated()
    journal.parse_editable_str(journal.editable_str().replace("Alpha", "Changed", 1))
    assert list(journal)[0].title == "Changed #work"
    assert journal.get_change_counts()["modified"] == 1


def test_delete_then_write_removes_entry_from_storage(tmp_path):
    path = tmp_path / "journal.txt"
    journal = _populated(path)
    journal.delete_entries([list(journal)[0]])
    journal.write()
    reopened = _journal(path).open()
    assert [e.title for e in reopened] == ["Beta #home"]
    assert journal.get_change_counts()["deleted"] == 1


def test_change_date_then_write_updates_storage_order(tmp_path):
    path = tmp_path / "journal.txt"
    journal = _populated(path)
    journal.change_date_entries(datetime(2023, 1, 1), [list(journal)[1]])
    journal.sort()
    journal.write()
    reopened = _journal(path).open()
    assert list(reopened)[0].title == "Beta #home"
    assert list(reopened)[0].date.year == 2023


def test_text_export_matches_single_file_storage_contract():
    from jrnl.plugins import get_exporter

    journal = _populated()
    exported = get_exporter("text").export(journal)
    assert "Alpha #work" in exported and "Beta #home" in exported
    assert exported == journal.editable_str()


def test_text_export_writes_one_requested_file(tmp_path):
    from jrnl.plugins import get_exporter

    target = tmp_path / "export.txt"
    get_exporter("text").export(_populated(), str(target))
    assert "Alpha #work" in target.read_text(encoding="utf-8")
    assert "Beta #home" in target.read_text(encoding="utf-8")


def test_text_export_directory_writes_one_file_per_entry(tmp_path):
    from jrnl.plugins import get_exporter

    get_exporter("text").export(_populated(), str(tmp_path))
    files = sorted(tmp_path.glob("*.txt"))
    assert len(files) == 2
    assert {"Alpha #work", "Beta #home"} == {
        path.read_text(encoding="utf-8").splitlines()[0].split("] ", 1)[1].rstrip(" *")
        for path in files
    }


def test_json_export_contains_documented_entry_fields():
    from jrnl.plugins import get_exporter

    data = json.loads(get_exporter("json").export(_populated()))
    assert set(data) == {"tags", "entries"}
    assert {"title", "body", "date", "time", "tags", "starred"} <= set(data["entries"][0])


def test_json_export_preserves_starred_and_tag_views():
    from jrnl.plugins import get_exporter

    data = json.loads(get_exporter("json").export(_populated()))
    assert data["entries"][1]["starred"] is True
    assert data["entries"][1]["tags"] == ["#home"]
    assert data["tags"] == {"#home": 1, "#work": 1}


def test_markdown_export_groups_entries_by_year_and_month():
    from jrnl.plugins import get_exporter

    output = get_exporter("markdown").export(_populated())
    assert "# 2024" in output
    assert "## January" in output
    assert "Alpha #work" in output and "Beta #home" in output


def test_filter_then_text_export_uses_same_selected_entries():
    from jrnl.plugins import get_exporter

    journal = _populated()
    journal.filter(tags=["#work"])
    output = get_exporter("text").export(journal)
    assert "Alpha #work" in output
    assert "Beta #home" not in output


def test_filter_then_json_export_uses_same_starred_selection():
    from jrnl.plugins import get_exporter

    journal = _populated()
    journal.filter(starred=True)
    entries = json.loads(get_exporter("json").export(journal))["entries"]
    assert [entry["title"] for entry in entries] == ["Beta #home"]


def test_combined_tag_and_text_filters_apply_before_export():
    from jrnl.plugins import get_exporter

    journal = _populated()
    journal.new_entry("Gamma #work\nOther", date=datetime(2024, 1, 3))
    journal.filter(tags=["#work"], contains=["first"])
    data = json.loads(get_exporter("json").export(journal))
    assert [entry["title"] for entry in data["entries"]] == ["Alpha #work"]


def test_excluded_tag_is_absent_from_export_and_tag_summary():
    from jrnl.plugins import get_exporter

    journal = _populated()
    journal.filter(exclude=["#home"])
    data = json.loads(get_exporter("json").export(journal))
    assert data["tags"] == {"#work": 1}
    assert [entry["title"] for entry in data["entries"]] == ["Alpha #work"]


def test_limit_then_export_keeps_latest_entries_only():
    from jrnl.plugins import get_exporter

    journal = _populated()
    journal.limit(1)
    data = json.loads(get_exporter("json").export(journal))
    assert [entry["title"] for entry in data["entries"]] == ["Beta #home"]


def test_from_journal_preserves_configuration_and_entry_views():
    from jrnl.journals import Folder

    source = _journal(timeformat="%Y/%m/%d", tagsymbols="@")
    source.new_entry("Original @tag", date=datetime(2024, 1, 1))
    converted = Folder.from_journal(source)
    added = converted.new_entry("Added @other", date=datetime(2024, 1, 2))
    assert [e.title for e in converted] == ["Original @tag", "Added @other"]
    assert str(added).startswith("[2024/01/02] Added @other")
    assert added.tags == ["@other"]


def test_importer_adds_jrnl_text_to_existing_journal():
    from jrnl.plugins import get_importer

    journal = _journal()
    importer = get_importer("jrnl")
    journal.import_("[2024-01-01 09:00] Imported\nBody\n")
    assert importer is not None
    assert [(e.title, e.body) for e in journal] == [("Imported", "Body")]


def test_open_journal_detects_single_file_storage(tmp_path):
    from jrnl.journals import Journal, open_journal

    path = tmp_path / "journal.txt"
    config = {**_config(path), "journals": {"default": str(path)}}
    opened = open_journal("default", config)
    assert isinstance(opened, Journal)
    assert path.exists()


def test_open_journal_detects_folder_storage(tmp_path):
    from jrnl.journals import Folder, open_journal

    path = tmp_path / "entries"
    path.mkdir()
    config = {**_config(path), "journals": {"default": str(path)}}
    opened = open_journal("default", config)
    assert isinstance(opened, Folder)


def test_folder_write_creates_date_organized_file(tmp_path):
    from jrnl.journals import Folder

    config = _config(tmp_path)
    folder = Folder(**config)
    folder.new_entry("Folder entry", date=datetime(2024, 3, 4, 9))
    folder.write()
    assert (tmp_path / "2024" / "03" / "04.txt").is_file()


def test_folder_open_reads_written_entry(tmp_path):
    from jrnl.journals import Folder

    config = _config(tmp_path)
    folder = Folder(**config)
    folder.new_entry("Folder entry #tag", date=datetime(2024, 3, 4, 9))
    folder.write()
    reopened = Folder(**config).open()
    assert [(e.title, set(e.tags)) for e in reopened] == [("Folder entry #tag", {"#tag"})]


def test_short_and_full_journal_displays_project_same_entries():
    journal = _populated()
    short = journal.pprint(short=True)
    full = journal.pprint(short=False)
    assert "Alpha #work" in short and "Beta #home" in short
    assert "First body" not in short and "Second body" not in short
    assert "First body" in full and "Second body" in full


def test_storage_text_and_json_preserve_same_dates_and_titles():
    from jrnl.plugins import get_exporter

    journal = _populated()
    storage = get_exporter("text").export(journal)
    data = json.loads(get_exporter("json").export(journal))
    for entry in data["entries"]:
        assert entry["date"] in storage
        assert entry["title"] in storage


def test_cli_version_reports_package_identity():
    import jrnl

    result = subprocess.run([sys.executable, "-m", "jrnl", "--version"], text=True, capture_output=True)
    assert result.returncode == 0
    assert jrnl.__title__ == "jrnl"
    assert jrnl.__version__
    assert jrnl.__title__ in result.stdout
    assert jrnl.__version__ in result.stdout


def test_cli_list_json_projects_configured_journal_names(tmp_path):
    config = _write_config(tmp_path, {"default": tmp_path / "default.txt", "work": tmp_path / "work.txt"})
    result = _run_cli(config, "--list", "--format", "json")
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)["journals"]) == {"default", "work"}


def test_cli_diagnostic_reports_runtime_and_package_versions():
    import jrnl

    result = subprocess.run([sys.executable, "-m", "jrnl", "--diagnostic"], text=True, capture_output=True)
    assert result.returncode == 0
    assert jrnl.__version__ in result.stdout
    assert str(sys.version_info.major) in result.stdout


def test_cli_explicit_date_and_star_are_persisted_in_storage(tmp_path):
    journal_path = tmp_path / "journal.txt"
    config = _write_config(tmp_path, {"default": journal_path})
    result = _run_cli(config, "2024-01-02 10:00 *: Planned #work")
    assert result.returncode == 0, result.stderr
    assert "[2024-01-02 10:00] Planned #work *" in journal_path.read_text(encoding="utf-8")


def test_cli_literal_newline_becomes_entry_body(tmp_path):
    journal_path = tmp_path / "journal.txt"
    config = _write_config(tmp_path, {"default": journal_path})
    result = _run_cli(config, r"Title line\nBody line")
    stored = journal_path.read_text(encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert "Title line" in stored and "Body line" in stored


def test_delete_action_persists_only_remaining_entries(tmp_path):
    journal = _populated(tmp_path / "journal.txt")
    journal.write()
    journal.delete_entries([entry for entry in journal if entry.title.startswith("Alpha")])
    journal.write()
    assert [entry.title for entry in _journal(tmp_path / "journal.txt").open()] == ["Beta #home"]


def test_change_time_action_persists_and_resorts_storage(tmp_path):
    journal = _populated(tmp_path / "journal.txt")
    journal.write()
    journal.change_date_entries(datetime(2023, 12, 31, 8), [entry for entry in journal if entry.title.startswith("Beta")])
    journal.write()
    assert [entry.title for entry in _journal(tmp_path / "journal.txt").open()] == ["Beta #home", "Alpha #work"]


def test_dates_export_reports_counts_for_each_selected_day():
    from jrnl.plugins import get_exporter

    exported = get_exporter("dates").export(_populated())
    assert "2024-01-01" in exported
    assert "2024-01-02" in exported


def test_cli_config_override_changes_only_current_display_format(tmp_path):
    journal_path = tmp_path / "journal.txt"
    config = _write_config(tmp_path, {"default": journal_path})
    assert _run_cli(config, "Entry #one").returncode == 0
    overridden = _run_cli(config, "--config-override", "display_format", "json", "-n", "1")
    normal = _run_cli(config, "-n", "1", "--short")
    assert json.loads(overridden.stdout)["entries"][0]["title"] == "Entry #one"
    assert normal.returncode == 0 and not normal.stdout.lstrip().startswith("{")


def test_named_journal_override_controls_display_without_affecting_default(tmp_path):
    import jrnl

    default_path, work_path = tmp_path / "default.txt", tmp_path / "work.txt"
    config = tmp_path / "jrnl.yaml"
    config.write_text(
        f"""version: {jrnl.__version__!r}
journals:
  default: {str(default_path)!r}
  work:
    journal: {str(work_path)!r}
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
    assert _run_cli(config, "Default entry").returncode == 0
    assert _run_cli(config, "work", "Work entry").returncode == 0
    assert json.loads(_run_cli(config, "work", "-n", "1").stdout)["entries"][0]["title"] == "Work entry"
    assert "Default entry" in _run_cli(config, "-n", "1", "--short").stdout


def test_daily_workflow_write_search_and_tag_report_share_entry(tmp_path):
    config = _write_config(tmp_path, {"default": tmp_path / "journal.txt"})
    written = _run_cli(config, "2024-01-03 09:00: Morning note #health")
    searched = _run_cli(config, "#health", "--short")
    tags = _run_cli(config, "--tags")
    assert written.returncode == searched.returncode == tags.returncode == 0
    assert "Morning note #health" in searched.stdout and "#health" in tags.stdout


def test_daily_workflow_filter_then_export_preserves_selected_body(tmp_path):
    config = _write_config(tmp_path, {"default": tmp_path / "journal.txt"})
    assert _run_cli(config, r"Alpha #work\nFirst body").returncode == 0
    assert _run_cli(config, r"Beta #home\nSecond body").returncode == 0
    payload = json.loads(_run_cli(config, "#work", "--format", "json").stdout)
    assert [entry["title"] for entry in payload["entries"]] == ["Alpha #work"]
    assert payload["entries"][0]["body"] == "First body"


def test_multiple_journal_workflow_exports_to_archive_folder(tmp_path):
    work_path, archive_path = tmp_path / "work.txt", tmp_path / "archive"
    archive_path.mkdir()
    config = _write_config(tmp_path, {"default": work_path, "work": work_path, "archive": archive_path})
    assert _run_cli(config, "work", "2024-01-04 10:00: Meeting @team").returncode == 0
    exported = tmp_path / "export.txt"
    assert _run_cli(config, "work", "--format", "text", "--file", str(exported)).returncode == 0
    assert _run_cli(config, "archive", "--import", "jrnl", "--file", str(exported)).returncode == 0
    assert "Meeting @team" in _run_cli(config, "archive", "--short").stdout


def test_multiple_journal_workflow_keeps_named_storage_isolated(tmp_path):
    default_path, work_path = tmp_path / "default.txt", tmp_path / "work.txt"
    config = _write_config(tmp_path, {"default": default_path, "work": work_path})
    assert _run_cli(config, "Default only").returncode == 0
    assert _run_cli(config, "work", "Work only").returncode == 0
    default_view, work_view = _run_cli(config, "--short").stdout, _run_cli(config, "work", "--short").stdout
    assert "Default only" in default_view and "Work only" not in default_view
    assert "Work only" in work_view and "Default only" not in work_view
