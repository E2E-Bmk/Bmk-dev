import base64
import io
import json

import nbformat
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): document atomic public-contract facts used by an integration test",
    )


@pytest.fixture
def notebook_factory():
    def make_notebook(cells=None, metadata=None):
        return nbformat.v4.new_notebook(
            cells=list(cells or []),
            metadata=dict(metadata or {"language_info": {"name": "python"}}),
        )

    return make_notebook


@pytest.fixture
def code_cell():
    def make_code(source, outputs=None, metadata=None, execution_count=None):
        return nbformat.v4.new_code_cell(
            source,
            outputs=list(outputs or []),
            metadata=dict(metadata or {}),
            execution_count=execution_count,
        )

    return make_code


@pytest.fixture
def markdown_cell():
    def make_markdown(source, metadata=None, attachments=None):
        cell = nbformat.v4.new_markdown_cell(source, metadata=dict(metadata or {}))
        if attachments:
            cell.attachments = attachments
        return cell

    return make_markdown


@pytest.fixture
def stream_output():
    def make_stream(text, name="stdout"):
        return nbformat.v4.new_output("stream", name=name, text=text)

    return make_stream


@pytest.fixture
def png_output():
    def make_png(data=b"png-data", metadata=None):
        encoded = base64.b64encode(data).decode("ascii")
        return nbformat.v4.new_output(
            "display_data",
            data={"image/png": encoded, "text/plain": "image"},
            metadata=dict(metadata or {}),
        )

    return make_png


@pytest.fixture
def notebook_bytes():
    def serialize(nb):
        return io.StringIO(json.dumps(nbformat.from_dict(nb)))

    return serialize
