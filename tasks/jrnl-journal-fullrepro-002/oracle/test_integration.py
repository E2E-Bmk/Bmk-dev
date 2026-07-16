# Spec2Repo oracle - integration tests for jrnl-journal-fullrepro-002
import subprocess
import sys
from types import SimpleNamespace


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
