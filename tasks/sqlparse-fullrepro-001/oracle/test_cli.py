import subprocess
import sys

import pytest

import sqlparse


def run_cli(*args, input_text=None):
    return subprocess.run(
        [sys.executable, "-m", "sqlparse", *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def test_parser_exposes_expected_positional_argument():
    parser = sqlparse.cli.create_parser()
    args = parser.parse_args(["input.sql"])
    assert args.filename == ["input.sql"]


def test_help_is_available():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_version_is_available():
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout.strip() == sqlparse.__version__


@pytest.mark.parametrize("args", [["--unknown"], ["-k", "invalid", "-"]])
def test_invalid_cli_arguments_fail(args):
    result = run_cli(*args)
    assert result.returncode != 0


@pytest.mark.parametrize(
    "args, expected",
    [
        (["-k", "upper", "-"], "SELECT 1"),
        (["-k", "lower", "-"], "select 1"),
        (["-r", "-",], "from foo"),
        (["--strip-comments", "-"], "select 1"),
    ],
)
def test_cli_formats_stdin(args, expected):
    result = run_cli(*args, input_text="select 1 -- note\nfrom foo")
    assert result.returncode == 0
    assert expected in result.stdout


def test_cli_writes_outfile(tmp_path):
    source = tmp_path / "input.sql"
    target = tmp_path / "output.sql"
    source.write_text("select 1", encoding="utf-8")
    result = run_cli(str(source), "-o", str(target), "-k", "upper")
    assert result.returncode == 0
    assert target.read_text(encoding="utf-8") == "SELECT 1"


def test_cli_in_place_updates_file(tmp_path):
    source = tmp_path / "input.sql"
    source.write_text("select 1", encoding="utf-8")
    result = run_cli(str(source), "--in-place", "-k", "upper")
    assert result.returncode == 0
    assert source.read_text(encoding="utf-8") == "SELECT 1"


def test_cli_multiple_files_requires_in_place(tmp_path):
    first = tmp_path / "first.sql"
    second = tmp_path / "second.sql"
    first.write_text("select 1", encoding="utf-8")
    second.write_text("select 2", encoding="utf-8")
    result = run_cli(str(first), str(second))
    assert result.returncode != 0


def test_cli_in_place_rejects_stdin():
    result = run_cli("-", "--in-place", input_text="select 1")
    assert result.returncode != 0


def test_cli_missing_file_fails(tmp_path):
    result = run_cli(str(tmp_path / "missing.sql"))
    assert result.returncode != 0


def test_cli_preserves_utf8_file(tmp_path):
    source = tmp_path / "utf8.sql"
    source.write_text("select 'cafe'", encoding="utf-8")
    result = run_cli(str(source), "--encoding", "utf-8")
    assert result.returncode == 0
    assert "cafe" in result.stdout
