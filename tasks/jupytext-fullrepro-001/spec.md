# Jupytext Specification

## Product Overview

Jupytext is a local notebook conversion tool and Python library that reads and writes Jupyter notebooks as text files. It maps an `nbformat` notebook model to script, Markdown, MyST Markdown, R Markdown, Quarto Markdown, and `.ipynb` representations, and it keeps paired notebook files synchronized through file metadata, configuration files, and command line workflows.

## Scope

This specification covers the public Python import surface exposed from `jupytext`, the `jupytext` command line entry point, deterministic conversion among `.ipynb`, `.py`, `.md`, `.Rmd`, and `.qmd` notebook representations, notebook and cell metadata filtering, paired file metadata, and local configuration through `jupytext.toml` and `pyproject.toml`.

The covered Python symbols are `__version__`, `NOTEBOOK_EXTENSIONS`, `guess_format`, `get_format_implementation`, `read`, `reads`, `write`, `writes`, `TextFileContentsManager`, `AsyncTextFileContentsManager`, `build_sync_jupytext_contents_manager_class`, and `build_async_jupytext_contents_manager_class`. The covered format implementation attributes are `extension` and `format_name`.

## Installable Surface

The package must be importable as `jupytext`.

```python
import nbformat

from jupytext import (
    __version__,
    NOTEBOOK_EXTENSIONS,
    guess_format,
    get_format_implementation,
    read,
    reads,
    write,
    writes,
    TextFileContentsManager,
    AsyncTextFileContentsManager,
    build_sync_jupytext_contents_manager_class,
    build_async_jupytext_contents_manager_class,
)
```

| Name | Kind | Role |
|---|---|---|
| `__version__` | value | Installed package version string. |
| `NOTEBOOK_EXTENSIONS` | collection | Recognized notebook and text-notebook file extensions. |
| `guess_format` | function | Infer the Jupytext format name and options from text content and a file extension. |
| `get_format_implementation` | function | Resolve an extension and optional format name to a public format implementation object. |
| `read` | function | Read a notebook from a filesystem path and return an `nbformat` notebook object. |
| `reads` | function | Read a notebook from text and return an `nbformat` notebook object. |
| `write` | function | Write an `nbformat` notebook object to a filesystem path. |
| `writes` | function | Return a string representation of an `nbformat` notebook object. |
| `TextFileContentsManager` | class | Jupyter contents manager for text notebook files. |
| `AsyncTextFileContentsManager` | class | Async Jupyter contents manager for text notebook files. |
| `build_sync_jupytext_contents_manager_class` | function | Build a sync contents manager class that includes Jupytext behavior. |
| `build_async_jupytext_contents_manager_class` | function | Build an async contents manager class that includes Jupytext behavior. |

## Format Detection And Public API

THE `__version__` value SHALL be a non-empty string.

THE `NOTEBOOK_EXTENSIONS` collection SHALL include `.ipynb`, `.py`, `.md`, `.Rmd`, and `.qmd`.

WHEN `guess_format` receives a Python script containing percent cell markers, THE system SHALL identify the `percent` format and return an options mapping.

WHEN `guess_format` receives a plain Python text notebook without percent markers, THE system SHALL identify the `light` format.

WHEN `guess_format` receives Markdown with a MyST code-cell directive, THE system SHALL identify the `myst` format and return an options mapping.

WHEN `get_format_implementation` receives a recognized extension and format name, THE system SHALL return an object whose public `extension` and `format_name` attributes describe that resolved format.

WHEN `reads` receives `as_version`, THE system SHALL return a notebook object with the requested notebook major version when the input can be represented at that version.

WHEN `read` is called with a path and no explicit format, THE system SHALL use the path extension and text content to select the reader.

WHEN `write` is called with a path and no explicit format, THE system SHALL use the output path extension to select the writer.

WHEN `writes` is called with `fmt="ipynb"`, THE system SHALL return JSON text containing an `.ipynb` notebook structure with `nbformat`, `metadata`, and `cells`.

## Script Notebook Formats

WHEN reading `py:percent`, THE system SHALL split cells at commented `# %%` markers, support `[markdown]` and `[raw]` cell type markers, remove line-comment prefixes from markdown and raw sources, preserve code cell source text, and parse cell metadata such as `tags` and other JSON-compatible key values.

WHEN reading `py:percent`, THE system SHALL restore commented Python magic lines such as `%matplotlib` to their executable code-cell form.

WHEN writing `py:percent`, THE system SHALL emit explicit `# %%` cell markers, include `[markdown]` and `[raw]` markers for non-code cells, encode public cell metadata such as `tags`, comment markdown and raw sources, and comment Python magic lines by default.

WHEN reading `py:light`, THE system SHALL turn separated comment paragraphs into markdown cells, code paragraphs into code cells, and explicit `# +` metadata markers into public cell metadata.

WHEN writing `py:light`, THE system SHALL use `# +` and `# -` cell markers when needed, include public cell metadata such as `tags`, and preserve code cell source text.

## Markdown Notebook Formats

WHEN reading Jupytext Markdown `md`, THE system SHALL keep ordinary Markdown paragraphs as markdown cells, convert language fences such as `python` into code cells, parse key/value cell metadata such as `tags`, `rank`, and `active`, and preserve explicit raw cells delimited by `<!-- #raw -->` and `<!-- #endraw -->`.

WHEN reading Jupytext Markdown `md`, THE system SHALL keep fences marked `.noeval` as markdown content rather than executable code cells. WHEN a code fence is marked `active="md"`, THE system SHALL represent it as a raw cell with `active` metadata.

WHEN writing Jupytext Markdown `md`, THE system SHALL include a YAML header for selected notebook metadata such as `kernelspec` and Jupytext text representation metadata, encode Python code cells as language fences with public cell metadata, and encode raw cells with raw-cell HTML comment markers.

WHEN reading MyST Markdown `md:myst`, THE system SHALL convert `{code-cell}` directives into code cells, parse short directive metadata such as `:tags:`, and convert `{raw-cell}` directives into raw cells with metadata such as `raw_mimetype`.

WHEN writing MyST Markdown `md:myst`, THE system SHALL use `{code-cell}` directives, include language lexer information when available from notebook metadata, and write short metadata lines for simple public cell metadata.

WHEN reading R Markdown `Rmd`, THE system SHALL convert fenced chunks such as `{python tags=c("parameters")}` into code cells and parse R-style chunk options into public cell metadata such as `tags`.

WHEN writing R Markdown `Rmd`, THE system SHALL encode code cells as R Markdown chunks and encode public tags using `tags=c(...)` chunk options.

## Command Line Conversion And Pairing

The console script name is `jupytext`. Running `jupytext --version` SHALL print the installed version and exit with status `0`.

WHEN invoked with `--to`, THE command SHALL convert each input notebook or text notebook to the requested destination format and write a sibling output file unless `--output -` requests standard output.

WHEN invoked with `--from` and `--to` and no input path, THE command SHALL read from standard input and write the converted representation to standard output.

WHEN invoked with `--set-formats`, THE command SHALL update notebook metadata under the public key path `metadata.jupytext.formats`.

WHEN invoked with `--sync`, THE command SHALL update all paired representations described by `metadata.jupytext.formats` or by local configuration. Missing paired text files SHALL be created from the available notebook representation.

WHEN a paired text file is newer than the `.ipynb` file, THE command SHALL use the text file as the source of input cells while retaining `.ipynb` outputs when those outputs are available and still associated with matching cells.

WHEN invoked with `--update --to ipynb`, THE command SHALL replace input cell content in the existing `.ipynb` target while preserving existing outputs and compatible notebook metadata.

WHEN invoked with `--test` or `--test-strict`, THE command SHALL perform the requested round-trip conversion check and exit with status `0` for stable conversions.

WHEN an unknown requested output format is supplied, THE command SHALL exit with a non-zero status and SHALL NOT create the normal converted output file.

## Configuration And Metadata Filters

WHEN `jupytext.toml` contains `formats = "ipynb,py:percent"`, THE command line synchronization workflow SHALL use that setting to create or update Python percent-format pairs for notebooks in that directory tree.

WHEN `pyproject.toml` contains `[tool.jupytext]` with `formats = "ipynb,py:percent"`, THE command line synchronization workflow SHALL use that setting to create or update Python percent-format pairs for notebooks in that directory tree.

WHEN configuration requests a Markdown pair with `formats = "ipynb,md"`, THE synchronization workflow SHALL create or update the Markdown pair using the Jupytext Markdown representation.

WHEN `--opt notebook_metadata_filter=-all` is supplied during Markdown conversion, THE written Markdown SHALL omit notebook metadata such as `kernelspec` from the YAML header while still preserving the converted cells.

By default, text formats SHALL include selected notebook metadata such as `kernelspec` and Jupytext text representation metadata while omitting unrelated custom top-level notebook metadata unless a metadata filter includes it.

## Product State Model

The core state is an `nbformat` notebook object with notebook-level metadata, an ordered `cells` list, cell `cell_type`, cell `source`, cell `metadata`, optional execution counts, and optional outputs. Public projections of that state are:

1. Python API projections from `read`, `reads`, `write`, and `writes`.
2. Text-file projections in `py:percent`, `py:light`, `md`, `md:myst`, and `Rmd`.
3. `.ipynb` JSON projections read and written through files or strings.
4. Command line projections through converted files, standard input, standard output, process exit status, and paired-file metadata.
5. Configuration projections through `jupytext.toml`, `pyproject.toml`, `metadata.jupytext.formats`, `notebook_metadata_filter`, and `cell_metadata_filter`.

## Error Semantics

| Condition | Required result |
|---|---|
| `get_format_implementation` receives an unknown notebook extension | Raise `ValueError`. |
| `reads` receives an unknown text format name | Raise `ValueError`. |
| `read` receives a missing filesystem path | Raise `FileNotFoundError`. |
| The command receives an unknown requested output format | Exit with a non-zero status and do not create the normal output file. |

Error message wording, warning wording, and displayed object representations are not part of this specification.

## Cross-View Invariants

1. A notebook written with `writes(..., fmt="py:percent")` and read with `reads(..., fmt="py:percent")` must preserve ordered cell types, sources, and public cell metadata required by the percent format.
2. A notebook written with `writes` and read with `reads` through `md`, `md:myst`, or `Rmd` must preserve ordered cell types, sources, and supported public cell metadata for those formats.
3. A notebook written to a filesystem path with `write` and read back with `read` must preserve the same input-cell projection selected by the path or explicit `fmt`.
4. A notebook written as `.ipynb` text or file JSON must preserve outputs and execution counts when those fields are present in the source notebook.
5. A format name returned by `guess_format` must be usable as part of a `fmt` string accepted by `reads` for the same content family.
6. A public format implementation returned by `get_format_implementation` must describe a format that `writes` can use to emit matching text representation metadata.
7. Metadata filter configuration must affect text headers consistently through the Python conversion path and command line conversion path.
8. A file produced by the command line interface must be readable by the Python API for the same format, and text emitted to standard output must be readable by the Python API when it represents a supported text format.
9. Pairing metadata set by `--set-formats`, `jupytext.toml`, or `[tool.jupytext]` must drive `--sync` to create or update the same paired paths.
10. Pair synchronization from a newer text representation to `.ipynb` must update input cells while preserving compatible existing outputs from the `.ipynb` representation.

## Representative Workflows

```python
import jupytext

nb = jupytext.read("analysis.py")
markdown = jupytext.writes(nb, fmt="md")
round_trip = jupytext.reads(markdown, fmt="md")
jupytext.write(round_trip, "analysis.ipynb")
```

This workflow reads a text notebook, converts it to Markdown text, reads that Markdown back to a notebook object, and writes an `.ipynb` file.

```bash
jupytext --set-formats ipynb,py:percent analysis.ipynb
jupytext --sync analysis.ipynb
jupytext --test --to py:percent analysis.ipynb
```

This workflow marks a notebook as paired, creates or updates the Python percent-format pair, and verifies that the percent conversion is stable.

## Non-Goals

- This specification does not require JupyterLab frontend assets, browser integration, or visual commands.
- This specification does not require Pandoc, Quarto, Marimo, Black, isort, pytest execution through `--check`, notebook kernel execution, live Jupyter servers, or external services.
- This specification does not require private helper modules, private attributes, internal parser classes, internal storage layout, exact warning text, exact error-message text, exact log text, or exact object representation text.
- This specification does not require network access.

## Invocation Protocol

Console script: `jupytext`.

`python -m jupytext` SHALL provide the same command line behavior as the `jupytext` console script.

| Exit | Meaning |
|---:|---|
| `0` | Requested conversion, synchronization, version display, or round-trip check succeeded. |
| non-zero | Command line usage, conversion, format, file, or round-trip check failed. |

## Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `pytest`, `nbformat`, `pyyaml`, `markdown-it-py`, and `mdit-py-plugins`.

The target package is not pre-installed. The project must declare standard packaging metadata in `pyproject.toml` or `setup.py` at the project root so the package can be installed with pip.

## Evaluation Notes

Assessment focuses on deterministic local conversion behavior, public Python APIs, command line conversions, file synchronization, and metadata consistency. It does not depend on optional external command integrations or live notebook servers.
