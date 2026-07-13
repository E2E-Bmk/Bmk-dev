# Spec2Repo oracle - atomic tests for coveragepy-fullrepro-001
import json

import os

import subprocess

import sys

import xml.etree.ElementTree as ET

from pathlib import Path

from coverage import Coverage, CoverageData

from coverage.exceptions import ConfigError, NoDataError, NoSource

from xml.etree import ElementTree

import pytest

import coverage

from coverage.exceptions import ConfigError, DataError, NoDataError, NoSource

def write_py(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def run_cli(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "coverage", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=run_env,
        timeout=30,
    )


def measured_file(data: CoverageData, suffix: str) -> str:
    return next(name for name in data.measured_files() if name.endswith(suffix))


def collect_file(tmp_path: Path, source: str, *, branch: bool = False, context: str | None = None) -> tuple[Coverage, Path]:
    program = write_py(tmp_path / "sample.py", source)
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)], branch=branch, context=context)
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()
    return cov, program


def test_installable_surface_imports_version_and_module_cli(tmp_path):
    import coverage

    assert isinstance(coverage.__version__, str)
    assert hasattr(coverage, "Coverage")
    assert hasattr(coverage, "CoverageData")

    result = run_cli(tmp_path, "--version")

    assert result.returncode == 0
    assert "Coverage.py" in result.stdout


def test_coverage_data_update_merges_line_data_objects(tmp_path):
    first = CoverageData(no_disk=True)
    second = CoverageData(no_disk=True)
    first.add_lines({str(tmp_path / "a.py"): {1, 2}})
    second.add_lines({str(tmp_path / "b.py"): {3}})

    first.update(second)

    measured = {Path(name).name for name in first.measured_files()}
    assert measured == {"a.py", "b.py"}
    assert first.lines(str(tmp_path / "b.py")) == [3]


def test_coverage_data_file_tracer_and_touch_file_roundtrip(tmp_path):
    data_file = tmp_path / ".coverage"
    source = tmp_path / "templated.txt"
    source.write_text("not python", encoding="utf-8")
    data = CoverageData(basename=str(data_file))
    data.add_lines({str(tmp_path / "seed.py"): {1}})
    data.touch_file(str(source), plugin_name="template-plugin")
    data.write()

    loaded = CoverageData(basename=str(data_file))
    loaded.read()

    assert loaded.lines(str(source)) == []
    assert loaded.file_tracer(str(source)) == "template-plugin"


def test_coverage_data_purge_files_removes_measured_file(tmp_path):
    data = CoverageData(no_disk=True)
    first = str(tmp_path / "first.py")
    second = str(tmp_path / "second.py")
    data.add_lines({first: {1}, second: {2}})

    data.purge_files([first])

    assert data.lines(first) == []
    assert data.lines(second) == [2]


def test_invalid_rcfile_reports_config_error_via_cli_and_api(tmp_path):
    bad = tmp_path / ".coveragerc"
    bad.write_text("[run\nbranch = true\n", encoding="utf-8")
    cli = run_cli(tmp_path, "debug", "config")

    def make_coverage():
        Coverage(config_file=str(bad))

    try:
        make_coverage()
    except ConfigError:
        api_error = True
    else:
        api_error = False

    assert cli.returncode != 0
    assert api_error is True


def test_report_without_data_raises_no_data_error(tmp_path):
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])

    try:
        cov.report()
    except NoDataError:
        raised = True
    else:
        raised = False

    assert raised is True


def test_missing_source_file_raises_no_source(tmp_path):
    program = write_py(tmp_path / "gone.py", "print('gone')\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()
    program.unlink()

    try:
        cov.report()
    except NoSource:
        raised = True
    else:
        raised = False

    assert raised is True


def test_cli_run_missing_script_fails_nonzero(tmp_path):
    result = run_cli(tmp_path, "run", "missing_script.py")

    assert result.returncode != 0


def test_coverage_current_tracks_collecting_instance(tmp_path):
    cov = Coverage(data_file=str(tmp_path / ".coverage"))
    assert Coverage.current() is None
    with cov.collect():
        assert Coverage.current() is cov
    assert Coverage.current() is None


def test_statement_measurement_records_executed_lines(tmp_path):
    cov, program = collect_file(tmp_path, "x = 1\nif x:\n    y = 2\n")
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    filename = measured_file(data, "sample.py")
    assert set(data.lines(filename)) >= {1, 2, 3}
    assert data.has_arcs() is False
    assert Path(cov.analysis(str(program))[0]).name == program.name


def test_branch_measurement_records_arcs(tmp_path):
    cov, program = collect_file(tmp_path, "flag = True\nif flag:\n    x = 1\nelse:\n    x = 2\n", branch=True)
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    filename = measured_file(data, "sample.py")
    assert data.has_arcs() is True
    assert data.arcs(filename)
    assert cov.branch_stats(str(program))[2] == (2, 1)


def test_data_file_none_keeps_measurement_in_memory(tmp_path):
    cov = Coverage(data_file=None, source=[str(tmp_path)])
    program = write_py(tmp_path / "memory_only.py", "value = 3\n")
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    data = cov.get_data()
    assert measured_file(data, "memory_only.py")
    assert not (tmp_path / ".coverage").exists()


def test_coverage_data_add_lines_round_trips_to_disk(tmp_path):
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    filename = str(tmp_path / "manual.py")
    data.add_lines({filename: {1, 3, 2}})
    data.write()
    reread = CoverageData(basename=str(tmp_path / ".coverage"))
    reread.read()
    assert reread.lines(filename) == [1, 2, 3]
    assert reread.has_arcs() is False


def test_coverage_data_add_arcs_round_trips_to_disk(tmp_path):
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    filename = str(tmp_path / "branchy.py")
    data.add_arcs({filename: {(1, 2), (2, -1), (-1, 1)}})
    data.write()
    reread = CoverageData(basename=str(tmp_path / ".coverage"))
    reread.read()
    assert sorted(reread.arcs(filename)) == [(-1, 1), (1, 2), (2, -1)]
    assert reread.has_arcs() is True


def test_coverage_data_dumps_and_loads_preserve_lines(tmp_path):
    filename = str(tmp_path / "serialized.py")
    data = CoverageData(no_disk=True)
    data.add_lines({filename: {4, 5}})
    blob = data.dumps()
    other = CoverageData(no_disk=True)
    other.loads(blob)
    assert other.lines(filename) == [4, 5]


def test_no_data_error_for_report_without_measurement(tmp_path):
    cov = Coverage(data_file=str(tmp_path / ".coverage"))
    with pytest.raises(NoDataError):
        cov.report()


def test_invalid_config_file_raises_config_error(tmp_path):
    rcfile = tmp_path / ".coveragerc"
    rcfile.write_text("[run]\nbranch = maybe\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        Coverage(config_file=str(rcfile))


def test_missing_source_raises_public_no_source(tmp_path):
    cov, program = collect_file(tmp_path, "x = 1\n")
    program.unlink()
    with pytest.raises(NoSource):
        cov.report()


def test_cli_help_and_version_exit_successfully(tmp_path):
    help_result = run_cli(tmp_path, "help")
    version_result = run_cli(tmp_path, "--version")
    assert help_result.returncode == 0
    assert "Coverage.py" in help_result.stdout
    assert version_result.returncode == 0
    assert "Coverage.py" in version_result.stdout


def test_cli_erase_removes_configured_data_file(tmp_path):
    write_py(tmp_path / "prog.py", "x = 1\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    assert (tmp_path / ".coverage").exists()
    assert run_cli(tmp_path, "erase").returncode == 0
    assert not (tmp_path / ".coverage").exists()
