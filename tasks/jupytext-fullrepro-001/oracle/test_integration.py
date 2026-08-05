# Spec2Repo oracle - integration tests for jupytext-fullrepro-001

import json
import os
from pathlib import Path

import nbformat
import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output

import jupytext
from conftest import cell_sources, cell_types, notebook_json, read_ipynb, run_cli, write_ipynb


@pytest.mark.depends_on("test_writes_percent_script_includes_cell_markers", "test_reads_percent_script_preserves_markdown_and_code_cells")
def test_percent_string_round_trip_preserves_cell_types_sources_and_tags(sample_notebook):
    """Seam: state consistency. CVI-1. Verifies: JTXT-INV-001, JTXT-SCR-001, JTXT-SCR-007."""
    text = jupytext.writes(sample_notebook, fmt="py:percent")
    round_trip = jupytext.reads(text, fmt="py:percent")
    assert cell_types(round_trip) == ["markdown", "code", "raw"]
    assert cell_sources(round_trip) == cell_sources(sample_notebook)
    assert round_trip.cells[1].metadata["tags"] == ["parameters"]


@pytest.mark.depends_on("test_writes_light_script_uses_plus_cell_markers", "test_reads_light_script_parses_explicit_cell_metadata")
def test_light_string_round_trip_preserves_cell_types_sources_and_tags(sample_notebook):
    """Seam: state consistency. CVI-1. Verifies: JTXT-INV-001, JTXT-SCR-005, JTXT-SCR-010."""
    text = jupytext.writes(sample_notebook, fmt="py:light")
    round_trip = jupytext.reads(text, fmt="py:light")
    assert cell_types(round_trip) == ["markdown", "code", "raw"]
    assert cell_sources(round_trip) == cell_sources(sample_notebook)
    assert round_trip.cells[1].metadata["tags"] == ["parameters"]


@pytest.mark.depends_on("test_writes_markdown_includes_yaml_header_and_python_fence", "test_reads_markdown_code_fence_with_cell_metadata")
def test_markdown_string_round_trip_preserves_cell_types_sources_and_tags(sample_notebook):
    """Seam: state consistency. CVI-2. Verifies: JTXT-INV-002, JTXT-MD-001, JTXT-MD-008."""
    text = jupytext.writes(sample_notebook, fmt="md")
    round_trip = jupytext.reads(text, fmt="md")
    assert cell_types(round_trip) == ["markdown", "code", "raw"]
    assert cell_sources(round_trip) == cell_sources(sample_notebook)
    assert round_trip.cells[1].metadata["tags"] == ["parameters"]


@pytest.mark.depends_on("test_writes_myst_uses_code_cell_directive", "test_reads_myst_code_cell_with_short_metadata")
def test_myst_string_round_trip_preserves_cell_types_sources_and_tags(sample_notebook):
    """Seam: state consistency. CVI-2. Verifies: JTXT-INV-002, JTXT-MD-005, JTXT-MD-010."""
    text = jupytext.writes(sample_notebook, fmt="md:myst")
    round_trip = jupytext.reads(text, fmt="md:myst")
    assert cell_types(round_trip) == ["markdown", "code", "raw"]
    assert cell_sources(round_trip) == cell_sources(sample_notebook)
    assert round_trip.cells[1].metadata["tags"] == ["parameters"]


@pytest.mark.depends_on("test_writes_rmarkdown_uses_chunk_options", "test_reads_rmarkdown_code_chunk_metadata")
def test_rmarkdown_string_round_trip_preserves_code_cell_metadata(sample_notebook):
    """Seam: state consistency. CVI-2. Verifies: JTXT-INV-002, JTXT-MD-007, JTXT-MD-011."""
    text = jupytext.writes(sample_notebook, fmt="Rmd")
    round_trip = jupytext.reads(text, fmt="Rmd")
    assert cell_types(round_trip) == ["markdown", "code", "raw"]
    assert cell_sources(round_trip) == cell_sources(sample_notebook)
    assert round_trip.cells[1].metadata["tags"] == ["parameters"]


@pytest.mark.depends_on("test_write_with_explicit_format_creates_text_file", "test_read_uses_path_extension_to_select_script_format")
def test_file_write_then_read_percent_script_uses_same_notebook_inputs(tmp_path, sample_notebook):
    """Seam: protocol handoff. CVI-3. Verifies: JTXT-INV-003, JTXT-API-004, JTXT-API-006."""
    path = tmp_path / "paired_inputs.py"
    jupytext.write(sample_notebook, path, fmt="py:percent")
    loaded = jupytext.read(path)
    assert cell_types(loaded) == ["markdown", "code", "raw"]
    assert cell_sources(loaded) == cell_sources(sample_notebook)


@pytest.mark.depends_on("test_write_uses_output_extension_when_format_is_absent", "test_writes_ipynb_returns_json_notebook_text")
def test_ipynb_file_write_then_read_preserves_outputs(tmp_path, notebook_with_output):
    """Seam: protocol handoff. CVI-4. Verifies: JTXT-INV-004, JTXT-API-002, JTXT-API-005."""
    path = tmp_path / "with_output.ipynb"
    jupytext.write(notebook_with_output, path)
    loaded = jupytext.read(path)
    assert loaded.cells[1].outputs[0].data["text/plain"] == "42"
    assert loaded.cells[1].execution_count == 3


@pytest.mark.depends_on("test_guess_format_detects_percent_script_marker", "test_reads_percent_script_preserves_markdown_and_code_cells")
def test_guess_format_result_can_drive_reads_for_percent_text():
    """Seam: protocol handoff. CVI-5. Verifies: JTXT-INV-005, JTXT-FMT-002."""
    text = "# %% [markdown]\n# Guessed note\n\n# %%\nflag = 'ok'\n"
    name, _options = jupytext.guess_format(text, ".py")
    nb = jupytext.reads(text, fmt=f"py:{name}")
    assert cell_types(nb) == ["markdown", "code"]
    assert nb.cells[1].source == "flag = 'ok'"


@pytest.mark.depends_on("test_get_format_implementation_resolves_extension_and_name", "test_writes_percent_script_includes_cell_markers")
def test_format_implementation_metadata_matches_written_text_representation(sample_notebook):
    """Seam: protocol handoff. CVI-6. Verifies: JTXT-INV-006, JTXT-FMT-005."""
    fmt = jupytext.get_format_implementation(".py", "percent")
    text = jupytext.writes(sample_notebook, fmt=f"{fmt.extension.removeprefix('.')}:{fmt.format_name}")
    assert "format_name: percent" in text
    assert "extension: .py" in text


@pytest.mark.depends_on("test_writes_markdown_includes_yaml_header_and_python_fence", "test_reads_markdown_code_fence_with_cell_metadata")
def test_markdown_metadata_filter_round_trip_keeps_kernelspec_but_omits_custom_top_level(sample_notebook):
    """Seam: config interaction. CVI-7. Verifies: JTXT-META-001, JTXT-INV-007."""
    text = jupytext.writes(sample_notebook, fmt="md")
    loaded = jupytext.reads(text, fmt="md")
    assert loaded.metadata.kernelspec.name == "python3"
    assert "author" not in loaded.metadata


@pytest.mark.depends_on("test_writes_percent_script_comments_magic_by_default", "test_reads_percent_script_uncomments_python_magic_lines")
def test_magic_line_round_trip_restores_original_code_source(make_notebook):
    """Seam: state consistency. CVI-1. Verifies: JTXT-SCR-004, JTXT-SCR-009."""
    nb = make_notebook([new_code_cell("%matplotlib inline\nseries = [1, 3, 5]")])
    text = jupytext.writes(nb, fmt="py:percent")
    loaded = jupytext.reads(text, fmt="py:percent")
    assert loaded.cells[0].source == "%matplotlib inline\nseries = [1, 3, 5]"


@pytest.mark.depends_on("test_writes_markdown_uses_raw_cell_comment_markers", "test_reads_markdown_raw_cell_markers")
def test_raw_markdown_cell_round_trip_preserves_source_and_metadata(make_notebook):
    """Seam: state consistency. CVI-2. Verifies: JTXT-MD-002, JTXT-MD-009, JTXT-INV-002."""
    nb = make_notebook([new_markdown_cell("Visible"), nbformat.v4.new_raw_cell("<b>opaque</b>", metadata={"mime": "text/html"})])
    text = jupytext.writes(nb, fmt="md")
    loaded = jupytext.reads(text, fmt="md")
    assert cell_types(loaded) == ["markdown", "raw"]
    assert loaded.cells[1].source == "<b>opaque</b>"
    assert loaded.cells[1].metadata["mime"] == "text/html"


@pytest.mark.depends_on("test_public_version_is_string")
def test_cli_version_reports_installed_package_version(tmp_path):
    """Seam: protocol handoff. Verifies: JTXT-CLI-001."""
    result = run_cli(["--version"], cwd=tmp_path)
    assert result.returncode == 0
    assert jupytext.__version__ in result.stdout


@pytest.mark.depends_on("test_writes_ipynb_returns_json_notebook_text", "test_writes_percent_script_includes_cell_markers")
def test_cli_converts_ipynb_file_to_percent_script(tmp_path, sample_notebook):
    """Seam: protocol handoff. CVI-8. Verifies: JTXT-CLI-002, JTXT-INV-008."""
    ipynb = tmp_path / "analysis.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--to", "py:percent", str(ipynb)], cwd=tmp_path)
    script = tmp_path / "analysis.py"
    assert result.returncode == 0
    assert script.exists()
    assert "# %% [markdown]" in script.read_text(encoding="utf-8")


@pytest.mark.depends_on("test_read_uses_path_extension_to_select_script_format", "test_write_uses_output_extension_when_format_is_absent")
def test_cli_converts_percent_script_to_ipynb_file(tmp_path):
    """Seam: protocol handoff. CVI-8. Verifies: JTXT-CLI-003, JTXT-INV-008."""
    script = tmp_path / "cli_source.py"
    script.write_text("# %% [markdown]\n# CLI markdown\n\n# %%\nlevel = 64\n", encoding="utf-8")
    result = run_cli(["--to", "ipynb", str(script)], cwd=tmp_path)
    ipynb = tmp_path / "cli_source.ipynb"
    assert result.returncode == 0
    loaded = read_ipynb(ipynb)
    assert cell_types(loaded) == ["markdown", "code"]
    assert loaded.cells[1].source == "level = 64"


@pytest.mark.depends_on("test_writes_markdown_includes_yaml_header_and_python_fence")
def test_cli_output_dash_writes_converted_text_to_stdout(tmp_path, sample_notebook):
    """Seam: protocol handoff. Verifies: JTXT-CLI-004."""
    ipynb = tmp_path / "stdout_source.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--to", "md", "--output", "-", str(ipynb)], cwd=tmp_path)
    assert result.returncode == 0
    assert "```python tags=[\"parameters\"]" in result.stdout
    assert not (tmp_path / "stdout_source.md").exists()


@pytest.mark.depends_on("test_writes_ipynb_returns_json_notebook_text", "test_writes_percent_script_includes_cell_markers")
def test_cli_reads_ipynb_from_stdin_and_writes_percent_to_stdout(tmp_path, sample_notebook):
    """Seam: protocol handoff. Verifies: JTXT-CLI-005."""
    result = run_cli(["--from", "ipynb", "--to", "py:percent"], cwd=tmp_path, input_text=notebook_json(sample_notebook))
    assert result.returncode == 0
    assert "# %% [markdown]" in result.stdout
    assert "value = 17" in result.stdout


@pytest.mark.depends_on("test_writes_ipynb_returns_json_notebook_text")
def test_cli_set_formats_updates_notebook_pairing_metadata(tmp_path, sample_notebook):
    """Seam: config interaction. CVI-9. Verifies: JTXT-PAIR-001, JTXT-CLI-006."""
    ipynb = tmp_path / "paired.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--set-formats", "ipynb,py:percent", str(ipynb)], cwd=tmp_path)
    loaded = read_ipynb(ipynb)
    assert result.returncode == 0
    assert loaded.metadata.jupytext.formats == "ipynb,py:percent"


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers')
def test_cli_sync_creates_missing_text_pair_from_ipynb(tmp_path, sample_notebook):
    """Seam: lifecycle crossing. CVI-9. Verifies: JTXT-PAIR-002, JTXT-CLI-007."""
    ipynb = tmp_path / "sync_missing.ipynb"
    write_ipynb(ipynb, sample_notebook)
    set_result = run_cli(["--set-formats", "ipynb,py:percent", str(ipynb)], cwd=tmp_path)
    sync_result = run_cli(["--sync", str(ipynb)], cwd=tmp_path)
    script = tmp_path / "sync_missing.py"
    assert set_result.returncode == 0
    assert sync_result.returncode == 0
    assert script.exists()
    assert "value = 17" in script.read_text(encoding="utf-8")


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers', 'test_read_uses_path_extension_to_select_script_format', 'test_write_uses_output_extension_when_format_is_absent')
def test_cli_sync_uses_newer_text_pair_to_update_ipynb_inputs(tmp_path, sample_notebook):
    """Seam: lifecycle crossing. CVI-10. Verifies: JTXT-PAIR-003, JTXT-INV-009."""
    ipynb = tmp_path / "sync_newer.ipynb"
    write_ipynb(ipynb, sample_notebook)
    assert run_cli(["--set-formats", "ipynb,py:percent", str(ipynb)], cwd=tmp_path).returncode == 0
    assert run_cli(["--sync", str(ipynb)], cwd=tmp_path).returncode == 0
    script = tmp_path / "sync_newer.py"
    script.write_text("# %% [markdown]\n# Updated from text\n\n# %%\nchanged = 81\n", encoding="utf-8")
    os.utime(ipynb, (1000, 1000))
    os.utime(script, (2000, 2000))
    result = run_cli(["--sync", str(ipynb)], cwd=tmp_path)
    loaded = read_ipynb(ipynb)
    assert result.returncode == 0
    assert cell_sources(loaded) == ["Updated from text", "changed = 81"]


@pytest.mark.depends_on('test_read_uses_path_extension_to_select_script_format', 'test_write_uses_output_extension_when_format_is_absent', 'test_writes_ipynb_returns_json_notebook_text')
def test_cli_update_to_ipynb_preserves_existing_outputs_while_replacing_inputs(tmp_path, notebook_with_output):
    """Seam: state consistency. CVI-10. Verifies: JTXT-CLI-008, JTXT-INV-010."""
    ipynb = tmp_path / "preserve_outputs.ipynb"
    write_ipynb(ipynb, notebook_with_output)
    script = tmp_path / "preserve_outputs.py"
    script.write_text("# %% [markdown]\n# New heading\n\n# %%\ntotal = 9 * 9\ntotal\n", encoding="utf-8")
    result = run_cli(["--update", "--to", "ipynb", str(script)], cwd=tmp_path)
    loaded = read_ipynb(ipynb)
    assert result.returncode == 0
    assert loaded.cells[0].source == "New heading"
    assert loaded.cells[1].source == "total = 9 * 9\ntotal"
    assert loaded.cells[1].outputs[0].data["text/plain"] == "42"


@pytest.mark.depends_on('test_writes_percent_script_includes_cell_markers', 'test_reads_percent_script_preserves_markdown_and_code_cells')
def test_cli_test_round_trip_percent_conversion_exits_success(tmp_path, sample_notebook):
    """Seam: protocol handoff. Verifies: JTXT-CLI-009."""
    ipynb = tmp_path / "round_trip_check.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--test", "--to", "py:percent", str(ipynb)], cwd=tmp_path)
    assert result.returncode == 0


@pytest.mark.depends_on("test_writes_markdown_includes_yaml_header_and_python_fence")
def test_cli_option_notebook_metadata_filter_controls_markdown_header(tmp_path, sample_notebook):
    """Seam: config interaction. CVI-7. Verifies: JTXT-META-002, JTXT-CLI-010."""
    ipynb = tmp_path / "metadata_filter.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--to", "md", "--opt", "notebook_metadata_filter=-all", str(ipynb)], cwd=tmp_path)
    markdown = (tmp_path / "metadata_filter.md").read_text(encoding="utf-8")
    assert result.returncode == 0
    assert "kernelspec:" not in markdown
    assert "```python tags=[\"parameters\"]" in markdown


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers')
def test_jupytext_toml_global_formats_drive_sync_pair_creation(tmp_path, sample_notebook):
    """Seam: config interaction. CVI-9. Verifies: JTXT-CONF-001, JTXT-PAIR-002."""
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,py:percent"\n', encoding="utf-8")
    ipynb = tmp_path / "configured.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--sync", str(ipynb)], cwd=tmp_path)
    script = tmp_path / "configured.py"
    assert result.returncode == 0
    assert script.exists()
    assert "value = 17" in script.read_text(encoding="utf-8")


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers')
def test_pyproject_tool_jupytext_formats_drive_sync_pair_creation(tmp_path, sample_notebook):
    """Seam: config interaction. CVI-9. Verifies: JTXT-CONF-002, JTXT-PAIR-002."""
    (tmp_path / "pyproject.toml").write_text('[tool.jupytext]\nformats = "ipynb,py:percent"\n', encoding="utf-8")
    ipynb = tmp_path / "pyproject_pair.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--sync", str(ipynb)], cwd=tmp_path)
    script = tmp_path / "pyproject_pair.py"
    assert result.returncode == 0
    assert script.exists()
    assert "value = 17" in script.read_text(encoding="utf-8")


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers', 'test_writes_markdown_includes_yaml_header_and_python_fence')
def test_configured_markdown_pair_sync_uses_requested_format(tmp_path, sample_notebook):
    """Seam: config interaction. CVI-9. Verifies: JTXT-CONF-003, JTXT-PAIR-002."""
    (tmp_path / "jupytext.toml").write_text('formats = "ipynb,md"\n', encoding="utf-8")
    ipynb = tmp_path / "configured_md.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--sync", str(ipynb)], cwd=tmp_path)
    markdown = tmp_path / "configured_md.md"
    assert result.returncode == 0
    assert markdown.exists()
    assert "```python tags=[\"parameters\"]" in markdown.read_text(encoding="utf-8")


@pytest.mark.depends_on("test_reads_myst_code_cell_with_short_metadata", "test_writes_myst_uses_code_cell_directive")
def test_cli_converts_myst_markdown_to_ipynb(tmp_path):
    """Seam: protocol handoff. CVI-8. Verifies: JTXT-CLI-003, JTXT-MD-005."""
    myst = tmp_path / "myst_doc.md"
    myst.write_text("# Demo\n\n```{code-cell} ipython3\n:tags: [run]\n\nsample = 144\n```\n", encoding="utf-8")
    result = run_cli(["--to", "ipynb", "--from", "md:myst", str(myst)], cwd=tmp_path)
    loaded = read_ipynb(tmp_path / "myst_doc.ipynb")
    assert result.returncode == 0
    assert cell_types(loaded) == ["markdown", "code"]
    assert loaded.cells[1].metadata["tags"] == ["run"]


@pytest.mark.depends_on("test_reads_rmarkdown_code_chunk_metadata", "test_writes_rmarkdown_uses_chunk_options")
def test_cli_converts_rmarkdown_to_ipynb(tmp_path):
    """Seam: protocol handoff. CVI-8. Verifies: JTXT-CLI-003, JTXT-MD-007."""
    rmd = tmp_path / "analysis.Rmd"
    rmd.write_text('Narrative\n\n```{python tags=c("imported")}\nvector = [2, 4]\n```\n', encoding="utf-8")
    result = run_cli(["--to", "ipynb", str(rmd)], cwd=tmp_path)
    loaded = read_ipynb(tmp_path / "analysis.ipynb")
    assert result.returncode == 0
    assert cell_types(loaded) == ["markdown", "code"]
    assert loaded.cells[1].metadata["tags"] == ["imported"]


@pytest.mark.depends_on('test_writes_markdown_includes_yaml_header_and_python_fence', 'test_reads_markdown_code_fence_with_cell_metadata')
def test_cli_stdout_markdown_can_be_read_by_python_api(tmp_path, sample_notebook):
    """Seam: protocol handoff. CVI-8. Verifies: JTXT-INV-008, JTXT-CLI-004."""
    ipynb = tmp_path / "stdout_roundtrip.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--to", "md", "--output", "-", str(ipynb)], cwd=tmp_path)
    loaded = jupytext.reads(result.stdout, fmt="md")
    assert result.returncode == 0
    assert cell_sources(loaded) == cell_sources(sample_notebook)


@pytest.mark.depends_on('test_read_uses_path_extension_to_select_script_format', 'test_write_uses_output_extension_when_format_is_absent', 'test_reads_markdown_code_fence_with_cell_metadata')
def test_cli_chained_conversion_py_to_ipynb_to_markdown_preserves_inputs(tmp_path):
    """Seam: lifecycle crossing. CVI-8. Verifies: JTXT-INV-008, JTXT-CLI-002, JTXT-CLI-003."""
    script = tmp_path / "chain.py"
    script.write_text("# %% [markdown]\n# Chain note\n\n# %%\namount = 121\n", encoding="utf-8")
    first = run_cli(["--to", "ipynb", str(script)], cwd=tmp_path)
    second = run_cli(["--to", "md", str(tmp_path / "chain.ipynb")], cwd=tmp_path)
    markdown = (tmp_path / "chain.md").read_text(encoding="utf-8")
    loaded = jupytext.reads(markdown, fmt="md")
    assert first.returncode == 0
    assert second.returncode == 0
    assert cell_sources(loaded) == ["Chain note", "amount = 121"]


@pytest.mark.depends_on('test_writes_percent_script_includes_cell_markers', 'test_reads_percent_script_preserves_markdown_and_code_cells')
def test_cli_test_strict_reports_success_for_stable_percent_conversion(tmp_path, sample_notebook):
    """Seam: protocol handoff. Verifies: JTXT-CLI-009."""
    ipynb = tmp_path / "strict_round_trip.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--test-strict", "--to", "py:percent", str(ipynb)], cwd=tmp_path)
    assert result.returncode == 0


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers')
def test_cli_invalid_requested_format_exits_nonzero_without_output_file(tmp_path, sample_notebook):
    """Seam: error propagation. Verifies: JTXT-ERR-004, JTXT-CLI-011."""
    ipynb = tmp_path / "bad_format.ipynb"
    write_ipynb(ipynb, sample_notebook)
    result = run_cli(["--to", "py:not-a-real-format", str(ipynb)], cwd=tmp_path)
    assert result.returncode != 0
    assert not (tmp_path / "bad_format.py").exists()


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text')
def test_cli_set_formats_to_single_ipynb_disables_text_pair_metadata(tmp_path, sample_notebook):
    """Seam: config interaction. CVI-9. Verifies: JTXT-PAIR-004, JTXT-CLI-006."""
    ipynb = tmp_path / "single_format.ipynb"
    write_ipynb(ipynb, sample_notebook)
    assert run_cli(["--set-formats", "ipynb,py:percent", str(ipynb)], cwd=tmp_path).returncode == 0
    result = run_cli(["--set-formats", "ipynb", str(ipynb)], cwd=tmp_path)
    loaded = read_ipynb(ipynb)
    assert result.returncode == 0
    assert loaded.metadata.jupytext.formats == "ipynb"


@pytest.mark.depends_on('test_writes_ipynb_returns_json_notebook_text', 'test_writes_percent_script_includes_cell_markers', 'test_write_uses_output_extension_when_format_is_absent')
def test_paired_sync_keeps_ipynb_outputs_when_text_inputs_are_newer(tmp_path, notebook_with_output):
    """Seam: lifecycle crossing. CVI-10. Verifies: JTXT-PAIR-003, JTXT-INV-010."""
    ipynb = tmp_path / "paired_outputs.ipynb"
    write_ipynb(ipynb, notebook_with_output)
    assert run_cli(["--set-formats", "ipynb,py:percent", str(ipynb)], cwd=tmp_path).returncode == 0
    assert run_cli(["--sync", str(ipynb)], cwd=tmp_path).returncode == 0
    script = tmp_path / "paired_outputs.py"
    script.write_text("# %% [markdown]\n# Output heading changed\n\n# %%\ntotal = 10\n", encoding="utf-8")
    os.utime(ipynb, (1000, 1000))
    os.utime(script, (2000, 2000))
    result = run_cli(["--sync", str(ipynb)], cwd=tmp_path)
    loaded = read_ipynb(ipynb)
    assert result.returncode == 0
    assert loaded.cells[0].source == "Output heading changed"
    assert loaded.cells[1].outputs[0].data["text/plain"] == "42"
