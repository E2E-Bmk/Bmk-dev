import json
import os
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

import coverage
from coverage import Coverage, CoverageData
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


def test_coverage_data_update_merges_measured_files(tmp_path):
    left = CoverageData(no_disk=True)
    right = CoverageData(no_disk=True)
    a_file = str(tmp_path / "a.py")
    b_file = str(tmp_path / "b.py")
    left.add_lines({a_file: {1}})
    right.add_lines({b_file: {2}})
    left.update(right)
    assert {Path(name).name for name in left.measured_files()} == {"a.py", "b.py"}


def test_coverage_data_query_context_filters_lines(tmp_path):
    program = write_py(tmp_path / "ctx.py", "a = 1\nb = 2\nc = 3\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)], context="setup")
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.switch_context("phase-two")
    exec(compile("d = 4\n", str(program), "exec"), {})
    cov.stop()
    cov.save()
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    filename = measured_file(data, "ctx.py")
    assert data.measured_contexts() >= {"setup", "setup|phase-two"}
    data.set_query_context("setup")
    assert set(data.lines(filename)) >= {1, 2, 3}
    data.set_query_context("missing")
    assert data.lines(filename) == []


def test_exclusion_rules_remove_lines_from_missing_report(tmp_path):
    cov, program = collect_file(tmp_path, "x = 1\nif x:\n    y = 2\nelse:  # pragma: no cover\n    y = 3\n")
    analysis = cov.analysis2(str(program))
    assert 5 not in analysis[3]
    cov.exclude("raise NotImplementedError")
    assert "raise NotImplementedError" in cov.get_exclude_list("exclude")
    cov.clear_exclude()
    assert "raise NotImplementedError" not in cov.get_exclude_list("exclude")


def test_json_report_contains_totals_and_file_details(tmp_path):
    cov, _program = collect_file(tmp_path, "x = 1\nprint(x)\n", branch=True)
    outfile = tmp_path / "coverage.json"
    total = cov.json_report(outfile=str(outfile), pretty_print=True)
    payload = json.loads(outfile.read_text(encoding="utf-8"))
    assert payload["totals"]["percent_covered"] == total
    assert any(name.endswith("sample.py") for name in payload["files"])


def test_xml_report_writes_cobertura_style_document(tmp_path):
    cov, _program = collect_file(tmp_path, "x = 1\nprint(x)\n")
    outfile = tmp_path / "coverage.xml"
    assert cov.xml_report(outfile=str(outfile)) == 100.0
    root = ElementTree.parse(outfile).getroot()
    assert root.tag == "coverage"
    assert root.findall(".//class")


def test_html_report_writes_index_and_source_page(tmp_path):
    cov, _program = collect_file(tmp_path, "x = 1\nprint(x)\n")
    outdir = tmp_path / "htmlcov"
    total = cov.html_report(directory=str(outdir))
    assert total == 100.0
    assert (outdir / "index.html").exists()
    assert any(path.name.endswith(".html") for path in outdir.iterdir())


def test_lcov_report_mentions_source_file_and_lines(tmp_path):
    cov, _program = collect_file(tmp_path, "x = 1\nprint(x)\n")
    outfile = tmp_path / "coverage.lcov"
    assert cov.lcov_report(outfile=str(outfile)) == 100.0
    text = outfile.read_text(encoding="utf-8")
    assert "SF:" in text
    assert "DA:1,1" in text


def test_annotate_report_marks_missing_lines(tmp_path):
    cov, _program = collect_file(tmp_path, "flag = False\nif flag:\n    missed = 1\n")
    outdir = tmp_path / "annotated"
    cov.annotate(directory=str(outdir))
    annotated = next(outdir.glob("*sample.py,cover"))
    text = annotated.read_text(encoding="utf-8")
    assert "> flag = False" in text
    assert "!     missed = 1" in text


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


def test_cli_run_report_and_json_share_data_file(tmp_path):
    write_py(tmp_path / "prog.py", "x = 1\nprint(x)\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    report = run_cli(tmp_path, "report", "--format=total")
    assert report.returncode == 0
    assert float(report.stdout.strip()) == 100.0
    json_result = run_cli(tmp_path, "json", "-o", "out.json")
    assert json_result.returncode == 0
    assert json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))["totals"]["covered_lines"] == 2


def test_cli_run_module_passes_program_arguments(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    write_py(pkg / "__init__.py", "")
    write_py(pkg / "__main__.py", "import sys\nopen('args.txt', 'w', encoding='utf-8').write('|'.join(sys.argv[1:]))\n")
    result = run_cli(tmp_path, "run", "-m", "pkg", "a", "b")
    assert result.returncode == 0
    assert (tmp_path / "args.txt").read_text(encoding="utf-8") == "a|b"


def test_cli_report_fail_under_returns_status_two(tmp_path):
    write_py(tmp_path / "prog.py", "flag = True\nif flag:\n    x = 1\nelse:\n    x = 2\n")
    assert run_cli(tmp_path, "run", "--branch", "prog.py").returncode == 0
    result = run_cli(tmp_path, "report", "--fail-under=100")
    assert result.returncode == 2


def test_cli_combine_merges_parallel_data_files(tmp_path):
    write_py(tmp_path / "one.py", "a = 1\n")
    write_py(tmp_path / "two.py", "b = 2\n")
    assert run_cli(tmp_path, "run", "--parallel-mode", "one.py").returncode == 0
    assert run_cli(tmp_path, "run", "--parallel-mode", "two.py").returncode == 0
    assert run_cli(tmp_path, "combine").returncode == 0
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    assert {Path(name).name for name in data.measured_files()} >= {"one.py", "two.py"}


def test_cli_erase_removes_configured_data_file(tmp_path):
    write_py(tmp_path / "prog.py", "x = 1\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    assert (tmp_path / ".coverage").exists()
    assert run_cli(tmp_path, "erase").returncode == 0
    assert not (tmp_path / ".coverage").exists()


def test_coverage_file_environment_selects_data_file(tmp_path):
    write_py(tmp_path / "prog.py", "x = 1\n")
    env = {"COVERAGE_FILE": str(tmp_path / "custom.coverage")}
    assert run_cli(tmp_path, "run", "prog.py", env=env).returncode == 0
    assert (tmp_path / "custom.coverage").exists()
    assert not (tmp_path / ".coverage").exists()


def test_rcfile_config_controls_branch_and_report_output(tmp_path):
    write_py(tmp_path / "prog.py", "flag = True\nif flag:\n    x = 1\nelse:\n    x = 2\n")
    (tmp_path / ".coveragerc").write_text("[run]\nbranch = True\n[report]\nshow_missing = True\n", encoding="utf-8")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    report = run_cli(tmp_path, "report", "-m")
    assert report.returncode == 0
    assert "Branch" in report.stdout
    assert "4" in report.stdout


def test_public_report_methods_return_same_total_for_same_data(tmp_path):
    cov, _program = collect_file(tmp_path, "x = 1\nprint(x)\n")
    text_total = cov.report(file=open(os.devnull, "w", encoding="utf-8"))
    json_total = cov.json_report(outfile=str(tmp_path / "coverage.json"))
    xml_total = cov.xml_report(outfile=str(tmp_path / "coverage.xml"))
    assert text_total == json_total == xml_total == 100.0


def test_include_and_omit_filters_affect_measured_files(tmp_path):
    keep = write_py(tmp_path / "keep_me.py", "x = 1\n")
    skip = write_py(tmp_path / "skip_me.py", "y = 2\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)], omit=[str(skip)])
    cov.start()
    exec(compile(keep.read_text(encoding="utf-8"), str(keep), "exec"), {})
    exec(compile(skip.read_text(encoding="utf-8"), str(skip), "exec"), {})
    cov.stop()
    names = {Path(name).name for name in cov.get_data().measured_files()}
    assert "keep_me.py" in names
    assert "skip_me.py" not in names
