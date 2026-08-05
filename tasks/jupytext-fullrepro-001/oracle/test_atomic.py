# Spec2Repo oracle - atomic tests for jupytext-fullrepro-001

import json
from pathlib import Path

import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_raw_cell

from conftest import cell_sources, cell_types, read_ipynb
from jupytext import NOTEBOOK_EXTENSIONS, __version__, get_format_implementation, guess_format, read, reads, write, writes


def test_public_version_is_string():
    """Verifies: JTXT-API-001."""
    assert isinstance(__version__, str)
    assert __version__


def test_notebook_extensions_include_core_text_and_ipynb_formats():
    """Verifies: JTXT-FMT-001."""
    for extension in [".ipynb", ".py", ".md", ".Rmd", ".qmd"]:
        assert extension in NOTEBOOK_EXTENSIONS


def test_guess_format_detects_percent_script_marker():
    """Verifies: JTXT-FMT-002."""
    name, options = guess_format("# %% [markdown]\n# Short note\n\n# %%\nx = 3\n", ".py")
    assert name == "percent"
    assert isinstance(options, dict)


def test_guess_format_uses_light_for_plain_python_script():
    """Verifies: JTXT-FMT-003."""
    name, options = guess_format("# A separated paragraph\n\nanswer = 5\n", ".py")
    assert name == "light"
    assert options == {}


def test_guess_format_detects_myst_code_cell_directive():
    """Verifies: JTXT-FMT-004."""
    name, options = guess_format("```{code-cell} ipython3\nz = 12\n```\n", ".md")
    assert name == "myst"
    assert isinstance(options, dict)


def test_get_format_implementation_resolves_extension_and_name():
    """Verifies: JTXT-FMT-005."""
    fmt = get_format_implementation(".py", "percent")
    assert fmt.extension == ".py"
    assert fmt.format_name == "percent"


def test_get_format_implementation_rejects_unknown_extension():
    """Verifies: JTXT-ERR-001."""
    with pytest.raises(ValueError):
        get_format_implementation(".story")


def test_reads_percent_script_preserves_markdown_and_code_cells():
    """Verifies: JTXT-SCR-001."""
    text = "# %% [markdown]\n# Fresh heading\n\n# %%\nvalue = 23\nvalue\n"
    nb = reads(text, fmt="py:percent")
    assert cell_types(nb) == ["markdown", "code"]
    assert cell_sources(nb) == ["Fresh heading", "value = 23\nvalue"]


def test_reads_percent_script_parses_title_type_and_metadata():
    """Verifies: JTXT-SCR-002."""
    text = '# %% Exploratory note [markdown] tags=["draft"] key="delta"\n# Body line\n'
    nb = reads(text, fmt="py:percent")
    assert nb.cells[0].cell_type == "markdown"
    assert nb.cells[0].source == "Body line"
    assert nb.cells[0].metadata["tags"] == ["draft"]
    assert nb.cells[0].metadata["key"] == "delta"


def test_reads_percent_script_restores_raw_cell_source():
    """Verifies: JTXT-SCR-003."""
    text = "# %% [raw]\n# <aside>raw text</aside>\n"
    nb = reads(text, fmt="py:percent")
    assert cell_types(nb) == ["raw"]
    assert nb.cells[0].source == "<aside>raw text</aside>"


def test_reads_percent_script_uncomments_python_magic_lines():
    """Verifies: JTXT-SCR-004."""
    nb = reads("# %%\n# %matplotlib inline\nplot_ready = True\n", fmt="py:percent")
    assert nb.cells[0].source.splitlines()[0] == "%matplotlib inline"


def test_reads_light_script_splits_markdown_and_code_paragraphs():
    """Verifies: JTXT-SCR-005."""
    text = "# Narrative block\n# with two lines\n\nfactor = 8\nresult = factor + 4\n"
    nb = reads(text, fmt="py:light")
    assert cell_types(nb) == ["markdown", "code"]
    assert cell_sources(nb) == ["Narrative block\nwith two lines", "factor = 8\nresult = factor + 4"]


def test_reads_light_script_parses_explicit_cell_metadata():
    """Verifies: JTXT-SCR-006."""
    text = '# + tags=["alpha"] priority=2\nscore = 19\n\n# -\n'
    nb = reads(text, fmt="py:light")
    assert cell_types(nb) == ["code"]
    assert nb.cells[0].metadata["tags"] == ["alpha"]
    assert nb.cells[0].metadata["priority"] == 2


def test_reads_markdown_code_fence_with_cell_metadata():
    """Verifies: JTXT-MD-001."""
    text = 'Opening paragraph\n\n```python tags=["clean"] rank=4\nanswer = 31\n```\n'
    nb = reads(text, fmt="md")
    assert cell_types(nb) == ["markdown", "code"]
    assert nb.cells[1].source == "answer = 31"
    assert nb.cells[1].metadata["tags"] == ["clean"]
    assert nb.cells[1].metadata["rank"] == 4


def test_reads_markdown_raw_cell_markers():
    """Verifies: JTXT-MD-002."""
    text = "<!-- #raw mime=\"text/html\"-->\n<strong>raw</strong>\n<!-- #endraw -->\n"
    nb = reads(text, fmt="md")
    assert cell_types(nb) == ["raw"]
    assert nb.cells[0].source == "<strong>raw</strong>"
    assert nb.cells[0].metadata["mime"] == "text/html"


def test_reads_markdown_noeval_fence_as_markdown():
    """Verifies: JTXT-MD-003."""
    nb = reads("```python .noeval\nshadow = 1\n```\n", fmt="md")
    assert cell_types(nb) == ["markdown"]
    assert "shadow = 1" in nb.cells[0].source


def test_reads_markdown_active_md_fence_as_raw_cell():
    """Verifies: JTXT-MD-004."""
    nb = reads('```python active="md"\nprint("shown in markdown")\n```\n', fmt="md")
    assert cell_types(nb) == ["raw"]
    assert nb.cells[0].metadata["active"] == "md"


def test_reads_myst_code_cell_with_short_metadata():
    """Verifies: JTXT-MD-005."""
    text = "```{code-cell} ipython3\n:tags: [parameters, hide-output]\n\nthreshold = 0.42\n```\n"
    nb = reads(text, fmt="md:myst")
    assert cell_types(nb) == ["code"]
    assert nb.cells[0].source == "threshold = 0.42"
    assert nb.cells[0].metadata["tags"] == ["parameters", "hide-output"]


def test_reads_myst_raw_cell_with_metadata_option():
    """Verifies: JTXT-MD-006."""
    text = "```{raw-cell}\n:raw_mimetype: text/html\n\n<b>kept</b>\n```\n"
    nb = reads(text, fmt="md:myst")
    assert cell_types(nb) == ["raw"]
    assert nb.cells[0].source == "<b>kept</b>"
    assert nb.cells[0].metadata["raw_mimetype"] == "text/html"


def test_reads_rmarkdown_code_chunk_metadata():
    """Verifies: JTXT-MD-007."""
    text = '```{python tags=c("parameters", "fresh")}\nrate = 2.5\n```\n'
    nb = reads(text, fmt="Rmd")
    assert cell_types(nb) == ["code"]
    assert nb.cells[0].source == "rate = 2.5"
    assert nb.cells[0].metadata["tags"] == ["parameters", "fresh"]


def test_writes_percent_script_includes_cell_markers(sample_notebook):
    """Verifies: JTXT-SCR-007."""
    text = writes(sample_notebook, fmt="py:percent")
    assert "# %% [markdown]" in text
    assert "# %% tags=[\"parameters\"]" in text
    assert "# %% [raw]" in text


def test_writes_percent_script_comments_markdown_and_raw_sources(sample_notebook):
    """Verifies: JTXT-SCR-008."""
    text = writes(sample_notebook, fmt="py:percent")
    assert "# Alpha **note**" in text
    assert "# <section>raw-fragment</section>" in text


def test_writes_percent_script_comments_magic_by_default(make_notebook):
    """Verifies: JTXT-SCR-009."""
    nb = make_notebook([new_code_cell("%timeit sum(range(3))\nplain = 1")])
    text = writes(nb, fmt="py:percent")
    assert "# %timeit sum(range(3))" in text
    assert "plain = 1" in text


def test_writes_light_script_uses_plus_cell_markers(sample_notebook):
    """Verifies: JTXT-SCR-010."""
    text = writes(sample_notebook, fmt="py:light")
    assert "# + tags=[\"parameters\"]" in text
    assert "# + active=\"\"" in text
    assert "value = 17" in text


def test_writes_markdown_includes_yaml_header_and_python_fence(sample_notebook):
    """Verifies: JTXT-MD-008."""
    text = writes(sample_notebook, fmt="md")
    assert text.startswith("---\n")
    assert "kernelspec:" in text
    assert "```python tags=[\"parameters\"]" in text


def test_writes_markdown_uses_raw_cell_comment_markers(sample_notebook):
    """Verifies: JTXT-MD-009."""
    text = writes(sample_notebook, fmt="md")
    assert "<!-- #raw -->" in text
    assert "<section>raw-fragment</section>" in text
    assert "<!-- #endraw -->" in text


def test_writes_myst_uses_code_cell_directive(sample_notebook):
    """Verifies: JTXT-MD-010."""
    text = writes(sample_notebook, fmt="md:myst")
    assert "```{code-cell} ipython3" in text
    assert ":tags: [parameters]" in text


def test_writes_rmarkdown_uses_chunk_options(sample_notebook):
    """Verifies: JTXT-MD-011."""
    text = writes(sample_notebook, fmt="Rmd")
    assert '```{python tags=c("parameters")}' in text
    assert "value = 17" in text


def test_writes_ipynb_returns_json_notebook_text(sample_notebook):
    """Verifies: JTXT-API-002."""
    data = json.loads(writes(sample_notebook, fmt="ipynb"))
    assert data["nbformat"] == 4
    assert [cell["cell_type"] for cell in data["cells"]] == ["markdown", "code", "raw"]


def test_reads_with_as_version_returns_requested_notebook_version():
    """Verifies: JTXT-API-003."""
    nb = reads("# %%\nvalue = 37\n", fmt="py:percent", as_version=4)
    assert nb.nbformat == 4
    assert nb.cells[0].source == "value = 37"


def test_reads_rejects_unknown_text_format():
    """Verifies: JTXT-ERR-002."""
    with pytest.raises(ValueError):
        reads("content", fmt="py:unknown")


def test_read_uses_path_extension_to_select_script_format(tmp_path):
    """Verifies: JTXT-API-004."""
    path = tmp_path / "fresh_script.py"
    path.write_text("# %%\nalpha = 41\n", encoding="utf-8")
    nb = read(path)
    assert cell_types(nb) == ["code"]
    assert nb.cells[0].source == "alpha = 41"


def test_read_rejects_missing_file(tmp_path):
    """Verifies: JTXT-ERR-003."""
    with pytest.raises(FileNotFoundError):
        read(tmp_path / "missing_notebook.py")


def test_write_uses_output_extension_when_format_is_absent(tmp_path, sample_notebook):
    """Verifies: JTXT-API-005."""
    target = tmp_path / "exported_notebook.ipynb"
    write(sample_notebook, target)
    loaded = read_ipynb(target)
    assert cell_types(loaded) == ["markdown", "code", "raw"]


def test_write_with_explicit_format_creates_text_file(tmp_path, sample_notebook):
    """Verifies: JTXT-API-006."""
    target = tmp_path / "explicit_percent.py"
    write(sample_notebook, target, fmt="py:percent")
    text = target.read_text(encoding="utf-8")
    assert "# %% [markdown]" in text
    assert "value = 17" in text
