import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import nbformat
from nbformat import (
    NO_CONVERT,
    NotebookNode,
    ValidationError,
    from_dict,
    v4,
    convert,
    read,
    reads,
    validate,
    write,
    writes,
)
from nbformat.sign import MemorySignatureStore, NotebookNotary
from nbformat.validator import isvalid, iter_validate, normalize
from nbformat.v4 import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_output,
    new_raw_cell,
)


def make_notebook(source="print('ready')", output_text="ready\n"):
    return v4.new_notebook(
        cells=[
            v4.new_markdown_cell("# Analysis"),
            v4.new_code_cell(
                source,
                outputs=[v4.new_output("stream", text=output_text)],
            ),
        ]
    )


def make_notary(secret=b"secret"):
    return NotebookNotary(store_factory=MemorySignatureStore, secret=secret)
