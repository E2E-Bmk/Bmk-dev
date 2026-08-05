# nbconvert Public Package Specification

## Product Overview

`nbconvert` converts Jupyter notebook documents into local output formats. A caller supplies an `nbformat` notebook, an input file, or a file-like stream, and receives a converted body plus a resources mapping. Public exporters, preprocessors, filters, and writers project the same notebook facts through text, HTML, notebook JSON, resource files, and filesystem output.

The package state is local and explicit: notebooks contain cells, metadata, outputs, attachments, and language facts; resources contain output extensions, extracted files, metadata, and template-facing values. Conversions are deterministic for generated notebooks when no execution kernel or external converter route is used.

## Scope

This specification covers local use of public Python APIs for Markdown, Python script, notebook JSON, and HTML conversion; public exporter lookup and dispatch; generated in-memory notebooks and temporary notebook files; public preprocessors for cell removal, output clearing, metadata clearing, stream coalescing, magic-language metadata, extracted outputs, and extracted attachments; public string, ANSI, markdown, metadata, and display-data filters; and public writers that write conversion bodies and resource files.

The expected behavior is limited to deterministic local facts visible through public imports. Tests may create notebooks, write temporary notebooks, convert them, inspect returned body/resources pairs, and write returned resources with a public writer.

## Public Import Surface

The required imports are:

```python
from nbconvert import HTMLExporter, MarkdownExporter, NotebookExporter, PythonExporter, export
from nbconvert.exporters import Exporter, ResourcesDict, get_export_names, get_exporter
from nbconvert.filters import DataTypeFilter, add_anchor, add_prompts, ansi2html, ascii_only
from nbconvert.filters import comment_lines, get_lines, get_metadata, markdown2html
from nbconvert.filters import path2url, posix_path, strip_ansi, strip_files_prefix
from nbconvert.filters import strip_trailing_newline, text_base64, wrap_text
from nbconvert.preprocessors import ClearMetadataPreprocessor, ClearOutputPreprocessor
from nbconvert.preprocessors import CoalesceStreamsPreprocessor, ExtractAttachmentsPreprocessor
from nbconvert.preprocessors import ExtractOutputPreprocessor, HighlightMagicsPreprocessor
from nbconvert.preprocessors import RegexRemovePreprocessor, TagRemovePreprocessor
from nbconvert.writers import FilesWriter, StdoutWriter, WriterBase
```

## Notebook JSON State Model

The central input is an `nbformat` version 4 notebook node. Notebook-level metadata may include `language_info`; cells have stable ordered positions, cell types, sources, metadata, outputs, and optional attachments. Code outputs may be streams or rich display values. Rich output binary data is base64 text in notebook state and bytes in extracted resources.

Resources are mappings passed into and returned from exporters and preprocessors. Required public keys include `metadata`, `outputs`, `attachments`, `output_files_dir`, `unique_key`, and `output_extension` when relevant. `ResourcesDict` returns an empty string for missing keys.

## Error Semantics

Unsupported public writer base use raises `NotImplementedError`. A display-data selector that cannot find a configured mimetype emits `UserWarning` and returns an empty list. Writer use without a concrete output destination or invalid resource shape may raise public Python errors. Exact exception prose is not required.

The local package is not required to execute notebook code, run kernels, invoke command-line converters, or resolve optional binary dependencies for PDF, TeX, Qt, browser, or Pandoc paths.

## Cross-View Invariants

1. Cell order is preserved across Markdown, Python script, HTML, and notebook JSON projections unless a public preprocessor removes cells.
2. A removed cell, source, output, or metadata value is absent from every downstream body or notebook JSON view produced after that preprocessor runs.
3. Clearing outputs removes stream and rich output entries and resets code execution counts while preserving source.
4. Extracted output and attachment resources must agree with rewritten cell metadata or rewritten cell references.
5. A writer receiving a body/resources pair must write the main output with the declared extension and persist resource files at the declared relative paths.
6. Public exporter lookup must return classes usable by the public export dispatch function.
7. Public filters must transform strings, paths, markdown, ANSI text, metadata, and mimetype priority independently of exporter internals.
8. File and stream export routes must project the same notebook cell facts as notebook-node export routes.
9. Template exporters must initialize missing resource metadata and output-extension facts.
10. HTML and Python exporters may format code differently, but the same code facts must remain visible through their public bodies.

## Representative Workflows

Create a notebook and export it to Markdown:

```python
import nbformat
from nbconvert import MarkdownExporter

nb = nbformat.v4.new_notebook(
    cells=[
        nbformat.v4.new_markdown_cell("# Title"),
        nbformat.v4.new_code_cell("answer = 42"),
    ],
    metadata={"language_info": {"name": "python"}},
)
body, resources = MarkdownExporter().from_notebook_node(nb)
assert resources["output_extension"] == ".md"
```

Register a public preprocessor and write resource files:

```python
from nbconvert import MarkdownExporter
from nbconvert.preprocessors import ExtractOutputPreprocessor
from nbconvert.writers import FilesWriter

exporter = MarkdownExporter()
exporter.register_preprocessor(ExtractOutputPreprocessor(), enabled=True)
body, resources = exporter.from_notebook_node(nb, resources={"metadata": {}, "outputs": {}})
FilesWriter(build_directory="build").write(body, resources, notebook_name="notebook")
```

## Non-Goals

PDF, WebPDF, Qt image or PDF export, browser automation, Playwright, live kernels, notebook execution, Pandoc conversion routes, TeX, command-line app behavior, networking, remote services, interactive widgets, timing behavior, logging text, exact exception text, private modules, private attributes, source-test helpers, and upstream test fixtures are outside this specification.

## Invocation Protocol

Run the tests from the package directory with the candidate package importable on `PYTHONPATH`:

```bash
python -m pytest -q
```

The working directory may be a temporary copy of this package. The tests create only temporary notebooks and temporary output directories through pytest fixtures. They do not require pre-existing notebooks, external services, or internet access.

## Environment

The intended environment is Linux with Python 3.11, without network access, and with the target package not pre-installed. The target package is supplied by the runner through the import path.

Install these support requirements before running: pytest, pytest-json-report, nbformat, traitlets, jinja2, beautifulsoup4, bleach with its CSS extra, defusedxml, markupsafe, mistune, pygments, jupyter-core, jupyterlab-pygments, nbclient, packaging, pandocfilters, and IPython.

## Evaluation Notes

Use only public imports and public return values. Do not import source tests or private modules. Keep all notebooks generated inside the test process or inside pytest temporary directories. Do not assert exact exception text, log text, object representations, generated cell identifiers, elapsed time, or optional external converter availability.
