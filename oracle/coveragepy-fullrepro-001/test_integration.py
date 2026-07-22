# Spec2Repo oracle - integration tests for coveragepy-fullrepro-001
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
        extra_env = dict(env)
        if "PYTHONPATH" in extra_env and run_env.get("PYTHONPATH"):
            extra_env["PYTHONPATH"] = extra_env["PYTHONPATH"] + os.pathsep + run_env["PYTHONPATH"]
        run_env.update(extra_env)
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


def test_cli_branch_context_json_and_total_report_agree(tmp_path):
    write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    print('yes')\n"
        "else:\n"
        "    print('no')\n",
    )

    run_result = run_cli(tmp_path, "run", "--branch", "--context=cli_ctx", "prog.py")
    assert run_result.returncode == 0
    assert run_result.stdout == "yes\n"

    json_result = run_cli(tmp_path, "json", "--show-contexts", "-o", "ctx.json")
    assert json_result.returncode == 0
    payload = json.loads((tmp_path / "ctx.json").read_text(encoding="utf-8"))
    file_payload = next(iter(payload["files"].values()))
    context_values = [ctx for contexts in file_payload["contexts"].values() for ctx in contexts]
    assert "cli_ctx" in context_values
    assert payload["totals"]["covered_lines"] == 3
    assert payload["totals"]["num_statements"] == 4
    assert payload["totals"]["covered_branches"] == 1
    assert payload["totals"]["missing_branches"] == 1

    total_result = run_cli(tmp_path, "report", "--format=total", "--precision=2")
    assert total_result.returncode == 0
    assert total_result.stdout.strip() == "66.67"


def test_cli_xml_report_exposes_branch_totals_and_missing_branch(tmp_path):
    write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    print('yes')\n"
        "else:\n"
        "    print('no')\n",
    )
    assert run_cli(tmp_path, "run", "--branch", "prog.py").returncode == 0

    xml_result = run_cli(tmp_path, "xml", "-o", "coverage.xml")
    assert xml_result.returncode == 0
    root = ET.parse(tmp_path / "coverage.xml").getroot()
    assert root.attrib["branches-valid"] == "2"
    assert root.attrib["branches-covered"] == "1"
    assert root.attrib["branch-rate"] == "0.5"
    branch_lines = [line.attrib for line in root.findall(".//line") if line.attrib.get("branch") == "true"]
    assert len(branch_lines) == 1
    assert branch_lines[0]["number"] == "2"
    assert branch_lines[0]["hits"] == "1"
    assert branch_lines[0]["condition-coverage"] == "50% (1/2)"
    assert branch_lines[0]["missing-branches"].isdigit()


def test_configured_data_file_is_shared_by_cli_and_coveragedata(tmp_path):
    write_py(tmp_path / "prog.py", "value = 7\nprint(value)\n")
    (tmp_path / ".coveragerc").write_text("[run]\ndata_file = envcov.dat\n", encoding="utf-8")

    run_result = run_cli(tmp_path, "run", "prog.py")
    assert run_result.returncode == 0
    data_file = tmp_path / "envcov.dat"
    assert data_file.exists()

    data = CoverageData(basename=str(data_file))
    data.read()
    assert {Path(name).name for name in data.measured_files()} == {"prog.py"}


def test_programmatic_branch_contexts_survive_serialization(tmp_path):
    program = write_py(
        tmp_path / "prog.py",
        "flag = False\n"
        "if flag:\n"
        "    value = 'yes'\n"
        "else:\n"
        "    value = 'no'\n",
    )
    cov = Coverage(data_file=str(tmp_path / ".coverage"), branch=True, source=[str(tmp_path)], context="api_ctx")
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    measured = next(name for name in data.measured_files() if name.endswith("prog.py"))
    assert data.has_arcs() is True
    assert data.arcs(measured)
    assert "api_ctx" in data.measured_contexts()

    blob = data.dumps()
    loaded = CoverageData(no_disk=True)
    loaded.loads(blob)
    loaded_measured = next(name for name in loaded.measured_files() if name.endswith("prog.py"))
    assert loaded.has_arcs() is True
    assert loaded.arcs(loaded_measured) == data.arcs(measured)


def test_coverage_collect_context_manager_records_lines(tmp_path):
    program = write_py(tmp_path / "prog.py", "a = 1\nb = 2\nc = a + b\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])

    with cov.collect():
        exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.save()

    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    measured = next(name for name in data.measured_files() if name.endswith("prog.py"))
    assert data.has_arcs() is False
    assert data.lines(measured) == [1, 2, 3]


def test_coverage_analysis_and_analysis2_report_missing_lines(tmp_path):
    program = write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    value = 1\n"
        "else:\n"
        "    value = 2\n",
    )
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    filename, statements, missing, missing_text = cov.analysis(str(program))
    analysis2 = cov.analysis2(str(program))

    assert Path(filename).name == "prog.py"
    assert statements == [1, 2, 3, 5]
    assert missing == [5]
    assert missing_text == "5"
    assert analysis2[3] == [5]


def test_exclude_and_clear_exclude_change_missing_line_analysis(tmp_path):
    program = write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    value = 1\n"
        "else:  # pragma: skip-branch\n"
        "    value = 2\n",
    )
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.exclude("pragma: skip-branch")
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    excluded = cov.analysis2(str(program))
    cov.clear_exclude()

    assert excluded[2] == [4, 5]
    assert 5 not in excluded[3]
    assert "pragma: skip-branch" not in cov.get_exclude_list("exclude")


def test_switch_context_filters_coveragedata_queries(tmp_path):
    first = write_py(tmp_path / "first.py", "value = 1\n")
    second = write_py(tmp_path / "second.py", "value = 2\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)], context="static")
    cov.start()
    cov.switch_context("first")
    exec(compile(first.read_text(encoding="utf-8"), str(first), "exec"), {})
    cov.switch_context("second")
    exec(compile(second.read_text(encoding="utf-8"), str(second), "exec"), {})
    cov.stop()
    cov.save()

    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    first_file = next(name for name in data.measured_files() if name.endswith("first.py"))
    second_file = next(name for name in data.measured_files() if name.endswith("second.py"))
    data.set_query_contexts(["first"])
    assert data.lines(first_file) == [1]
    assert data.lines(second_file) == []


def test_include_omit_measurement_controls_measured_files(tmp_path):
    keep = write_py(tmp_path / "keep.py", "value = 'keep'\n")
    skip = write_py(tmp_path / "skip.py", "value = 'skip'\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), include=[str(keep)], omit=[str(skip)])
    cov.start()
    exec(compile(keep.read_text(encoding="utf-8"), str(keep), "exec"), {})
    exec(compile(skip.read_text(encoding="utf-8"), str(skip), "exec"), {})
    cov.stop()
    cov.save()

    measured = {Path(name).name for name in cov.get_data().measured_files()}
    assert measured == {"keep.py"}


def test_programmatic_json_xml_html_and_lcov_reports_share_total(tmp_path):
    program = write_py(tmp_path / "prog.py", "print('hello')\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    json_total = cov.json_report(outfile=str(tmp_path / "coverage.json"))
    xml_total = cov.xml_report(outfile=str(tmp_path / "coverage.xml"))
    html_total = cov.html_report(directory=str(tmp_path / "htmlcov"))
    lcov_total = cov.lcov_report(outfile=str(tmp_path / "coverage.lcov"))

    assert json_total == xml_total == html_total == lcov_total == 100.0
    assert (tmp_path / "coverage.json").exists()
    assert (tmp_path / "coverage.xml").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert (tmp_path / "coverage.lcov").exists()


def test_combine_keep_preserves_parallel_input_files(tmp_path):
    write_py(tmp_path / "one.py", "print('one')\n")
    write_py(tmp_path / "two.py", "print('two')\n")
    assert run_cli(tmp_path, "run", "--parallel-mode", "one.py").returncode == 0
    assert run_cli(tmp_path, "run", "--parallel-mode", "two.py").returncode == 0
    parallel_files = sorted(tmp_path.glob(".coverage.*"))

    combine = run_cli(tmp_path, "combine", "--keep")
    assert combine.returncode == 0
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    measured = {Path(name).name for name in data.measured_files()}

    assert {path.name for path in parallel_files}.issubset({path.name for path in tmp_path.glob(".coverage.*")})
    assert measured == {"one.py", "two.py"}


def test_cli_erase_removes_coverage_file_and_report_has_no_data(tmp_path):
    write_py(tmp_path / "prog.py", "print('hello')\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    assert (tmp_path / ".coverage").exists()

    erase = run_cli(tmp_path, "erase")
    report = run_cli(tmp_path, "report")

    assert erase.returncode == 0
    assert not (tmp_path / ".coverage").exists()
    assert report.returncode != 0


def test_cli_run_module_passes_program_arguments(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    write_py(package / "__init__.py", "")
    write_py(
        package / "__main__.py",
        "import sys\n"
        "from pathlib import Path\n"
        "Path('args.json').write_text(__import__('json').dumps(sys.argv[1:]), encoding='utf-8')\n",
    )

    result = run_cli(tmp_path, "run", "-m", "pkg", "left", "right", env={"PYTHONPATH": str(tmp_path)})

    assert result.returncode == 0
    assert json.loads((tmp_path / "args.json").read_text(encoding="utf-8")) == ["left", "right"]


def test_cli_debug_data_reports_measured_file(tmp_path):
    write_py(tmp_path / "prog.py", "print('hello')\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0

    debug = run_cli(tmp_path, "debug", "data")

    assert debug.returncode == 0
    assert "prog.py" in debug.stdout


def test_coverage_file_environment_is_used_by_report_command(tmp_path):
    write_py(tmp_path / "prog.py", "print('hello')\n")
    env = {"COVERAGE_FILE": str(tmp_path / "custom.dat")}
    assert run_cli(tmp_path, "run", "prog.py", env=env).returncode == 0

    report = run_cli(tmp_path, "report", "--format=total", env=env)

    assert report.returncode == 0
    assert report.stdout.strip() == "100"


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


def test_cli_run_report_and_json_share_data_file(tmp_path):
    write_py(tmp_path / "prog.py", "x = 1\nprint(x)\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    report = run_cli(tmp_path, "report", "--format=total")
    assert report.returncode == 0
    assert float(report.stdout.strip()) == 100.0
    json_result = run_cli(tmp_path, "json", "-o", "out.json")
    assert json_result.returncode == 0
    assert json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))["totals"]["covered_lines"] == 2


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
