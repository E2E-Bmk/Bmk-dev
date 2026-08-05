# Spec2Repo oracle shared fixtures for jupytext-fullrepro-001

import json
import os
import subprocess
import sys
from pathlib import Path

import nbformat
import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output, new_raw_cell


@pytest.fixture
def make_notebook():
    def _make_notebook(cells=None, *, kernelspec=True, metadata=None):
        nb = new_notebook(cells=cells or [])
        if kernelspec:
            nb.metadata.kernelspec = {"name": "python3", "display_name": "Python 3"}
            nb.metadata.language_info = {"name": "python", "pygments_lexer": "ipython3"}
        if metadata:
            for key, value in metadata.items():
                nb.metadata[key] = value
        return nb

    return _make_notebook


@pytest.fixture
def sample_notebook(make_notebook):
    return make_notebook(
        [
            new_markdown_cell("Alpha **note**"),
            new_code_cell("value = 17\nprint(value)", metadata={"tags": ["parameters"], "trusted": True}),
            new_raw_cell("<section>raw-fragment</section>"),
        ],
        metadata={"author": "Casey"},
    )


@pytest.fixture
def notebook_with_output(make_notebook):
    cell = new_code_cell("total = 6 * 7\ntotal", execution_count=3)
    cell.outputs = [new_output("execute_result", data={"text/plain": "42"}, execution_count=3)]
    return make_notebook([new_markdown_cell("Kept heading"), cell])


def cell_types(nb):
    return [cell.cell_type for cell in nb.cells]


def cell_sources(nb):
    return [cell.source for cell in nb.cells]


def write_ipynb(path: Path, notebook):
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, path)


def read_ipynb(path: Path):
    return nbformat.read(path, as_version=4)


def run_cli(args, *, cwd, input_text=None):
    command_prefix = os.environ.get("JUPYTEXT_CLI")
    command = ([command_prefix] if command_prefix else [sys.executable, "-m", "jupytext"]) + list(args)
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def notebook_json(notebook):
    return json.dumps(nbformat.from_dict(notebook), sort_keys=True)


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): declares atomic behaviors used by an integration test")
