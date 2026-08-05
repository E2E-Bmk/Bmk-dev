# nbformat Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`nbformat` is the Python reference implementation for reading, writing, validating, converting, constructing, and signing notebook JSON documents. A notebook document is durable JSON with top-level `metadata`, `nbformat`, `nbformat_minor`, and `cells` fields. The Python API returns nested `NotebookNode` objects that behave like dictionaries and expose the same keys as attributes.

The implementation must preserve notebook content across JSON strings, file paths, file-like objects, version conversion, and trust-signature checks. It must keep notebook data JSON-compatible and must treat trust metadata as transient state rather than durable notebook content.

## Non-Goals

- This specification does not require Exact formatting of validation error messages.
- This specification does not require Exact generated cell id strings.
- This specification does not require Exact JSON schema file contents or schema snapshot filenames.
- This specification does not require Private helper modules or undocumented carrier import paths.
- This specification does not require Reimplementation of the underlying JSON Schema libraries.
- This specification does not require Binary notebook formats outside JSON notebook documents.
- This specification does not require UI rendering behavior for notebook frontends.
- This specification does not require Network storage for notebook signatures.

## Representative Workflows

```python
import nbformat
from nbformat import v4
from nbformat.sign import MemorySignatureStore, NotebookNotary

nb = v4.new_notebook(
    cells=[
        v4.new_markdown_cell("# Analysis"),
        v4.new_code_cell(
            "print('ready')",
            outputs=[v4.new_output("stream", text="ready\n")],
        ),
    ]
)

nbformat.validate(nb)
text = nbformat.writes(nb)
round_tripped = nbformat.reads(text, as_version=4)

notary = NotebookNotary(store_factory=MemorySignatureStore, secret=b"local-secret")
notary.sign(round_tripped)
trusted = notary.check_signature(round_tripped)
notary.mark_cells(round_tripped, trusted)
all_cells_trusted = notary.check_cells(round_tripped)
```

This workflow must create a valid v4 notebook, serialize it to JSON, read it back as a v4 `NotebookNode`, sign the content in a local store, and report the code cells trusted.

## Notebook Format Behavior

This section covers the notebook document structure and how text fields are stored.

**Top-level structure.** The top-level notebook object must include `metadata`, `nbformat`, `nbformat_minor`, and `cells`. Metadata fields are optional unless a nested documented metadata object defines its own required keys.

**Cell structure.** Cell objects must include `cell_type`, `metadata`, and `source`. Code cells must include `execution_count` as an integer or `None`, plus `outputs`. Markdown and raw cells support `attachments` as a mapping from filename to mime-bundle.

**Multiline text handling.** Multiline text fields in notebook files must be accepted as either a string or a list of strings. Reading through the Python API must rejoin those lists into a single string in memory. Writing through v4 JSON with default settings must split cell sources, stream text, text mime data, JavaScript data, SVG data, and attachment text data into lists of lines. JSON mime values, including `application/json` and `application/*+json`, must remain JSON data rather than line-split strings.

**Cell ids.** Cell ids in v4.5 and later notebooks must be strings of length 1 through 64 using alphanumeric characters, hyphen, and underscore, and ids must be unique within a notebook. Constructors must provide ids for new v4 cells.

## NotebookNode and Dictionary Conversion

This section covers how notebook data is accessed and mutated in Python.

**Dictionary and attribute access.** `NotebookNode` must behave as a mutable dictionary whose keys are also available through attribute access. Reading `node["cells"]` and `node.cells` must return the same value. Assigning a mapping through item assignment or `update()` must recursively convert nested dictionaries into `NotebookNode` objects. Assigning a list or tuple containing dictionaries must recursively convert those contained dictionaries.

**Update method.** `NotebookNode.update` must accept the same single positional update source patterns as a dictionary: a mapping, an object with keys, or an iterable of key-value pairs. It must raise `TypeError` when more than one positional update source is supplied.

**from_dict conversion.** `from_dict` must return a recursively converted `NotebookNode` when the input is a dictionary. It must return a list of converted elements when the input is a list or tuple. It must return non-container values unchanged. It must not validate that the resulting object is a complete or valid notebook.

## Reading, Writing, and Conversion

This section covers how notebooks are serialized, deserialized, and converted between versions.

**reads.** `reads` must parse a notebook JSON string or bytes object, return a `NotebookNode`, and convert it to the requested major version unless `NO_CONVERT` is supplied. It must validate the resulting notebook after parsing and conversion. When validation fails and the caller supplies a `capture_validation_error` dictionary, it must store the validation exception under the key `"ValidationError"` and still return the parsed notebook.

**read.** `read` must read from a file-like object with `read()` or from a filesystem path. It must open path inputs with UTF-8 text decoding. Missing paths must raise `OSError`. File-like read errors must propagate.

**writes.** `writes` must serialize a notebook to a JSON string. It must convert to the requested major version when one is supplied; otherwise it must use the notebook document's own major version. It must validate the notebook before serialization. When validation fails and the caller supplies a `capture_validation_error` dictionary, it must store the exception and still return serialized JSON. When `split_lines=True` is set, multiline text fields must be split into line lists according to v4 conventions.

**write.** `write` must write the JSON string from `writes` to a file-like object or to a filesystem path. It must write text, not bytes. It must append a final newline to file output when the serialized string does not already end with one. It must return `None` for successful writes.

**NO_CONVERT and version constants.** `NO_CONVERT` must be a public sentinel value accepted by read and write APIs. `current_nbformat` and `current_nbformat_minor` must reflect the current v4 major and minor format.

**convert.** `convert` must return the notebook unchanged (same object) when its current major version already equals the requested target. It must convert notebooks one major version at a time through the public version modules when the requested major version exists. It must raise `ValueError` when the requested major version is not implemented.

## Validation and Normalization

This section covers how notebooks and schema fragments are validated.

**validate.** `validate` must return `None` when the supplied notebook or schema fragment is valid. It must raise `ValidationError` or `NotebookValidationError` when validation fails. It must raise `TypeError` when neither a notebook object nor the legacy `nbjson` alias input is supplied. The `nbjson` keyword must remain a backward-compatible alias for the notebook object. Schema fragments can be validated by supplying `ref` and `version` parameters.

**Cell id validation.** For v4.5 and later notebooks, validation must check cell id presence and uniqueness. With default settings, validation must repair missing or duplicate cell ids. When cell id repair is explicitly disabled, duplicate ids must raise `ValidationError`.

**isvalid.** `isvalid` must return `True` when validation succeeds and `False` when validation raises `ValidationError`. It must leave the supplied object unchanged.

**iter_validate.** `iter_validate` must return an iterator of validation errors instead of raising the first one. It must accept the `nbjson` keyword alias.

**normalize.** `normalize` must return a change count and a deep-copied normalized notebook. Duplicate cell ids must be repaired in the normalized copy without changing the original.

## v4 Construction and Legacy Packages

This section covers how v4 cells, notebooks, and outputs are constructed, and how legacy version packages behave.

**v4 version constants.** `nbformat.v4.nbformat` must equal `4`. `nbformat.v4.nbformat_minor` must be the package's current v4 minor value.

**new_notebook.** `new_notebook` must return a valid notebook with `nbformat`, `nbformat_minor`, `metadata`, and `cells` fields, then apply keyword overrides before validation. An empty notebook must have an empty `cells` list and empty `metadata`.

**new_code_cell.** `new_code_cell` must return a valid code cell with an `id`, `cell_type="code"`, empty `metadata`, `execution_count=None`, the supplied source, and an empty `outputs` list. Keyword overrides including `execution_count` and `outputs` must be applied before validation.

**new_markdown_cell and new_raw_cell.** `new_markdown_cell` and `new_raw_cell` must return valid cells with appropriate `cell_type`, an `id`, the supplied source, and empty `metadata`.

**new_output.** `new_output` must construct v4 output objects by output type. For `"stream"`, defaults must include `name="stdout"` and `text=""`. For `"display_data"`, defaults must include empty `metadata` and empty `data`. A positional data argument after the output type must set `data` for display and execute_result outputs. For `"execute_result"`, defaults must include empty `metadata`, empty `data`, and `execution_count=None`. For `"error"`, defaults must include `ename="NotImplementedError"`, `evalue=""`, and an empty `traceback` list. Keyword overrides must be applied before validation. Invalid output shapes must raise validation errors.

**output_from_msg.** `output_from_msg` must accept kernel IOPub messages with header message types `"execute_result"`, `"stream"`, `"display_data"`, and `"error"`, and must return the corresponding v4 output node. It must raise `ValueError` for unrecognized output message types.

**v4 reader and writer.** The v4 `reads` must parse v4 JSON and return a `NotebookNode`, rejoining split multiline text fields. The v4 `writes` must serialize notebook content as JSON, must default to one-space indentation, sorted keys, `ensure_ascii=False`, and split multiline text fields into line lists unless line splitting is explicitly disabled. The v4 writer must strip transient trust and signature metadata (`metadata.signature` and `cell.metadata.trusted`).

**Legacy packages.** `nbformat.v1`, `nbformat.v2`, and `nbformat.v3` must expose their package-level constructors and read/write aliases as importable names. `parse_filename` in the v2 and v3 packages must return the filename, notebook name, and format where `.ipynb` and `.json` inputs use `"json"`, `.py` inputs use `"py"`, and extensionless inputs append `.ipynb` and use `"json"`.

## Trust and Signatures

This section covers how notebooks are signed and how cell trust is determined.

**Notary signing.** `NotebookNotary` must compute content signatures using its configured HMAC algorithm and `secret`. The default algorithm must be `sha256`. `compute_signature(nb)` must return the content digest. Different secrets must produce different signatures for the same notebook. `sign(nb)` must store the notebook's signature in the signature store. `check_signature(nb)` must return `True` only when the current content signature is present in the store. `unsign(nb)` must remove the current signature from the store. Changing notebook content must invalidate a previously stored signature.

**Cell trust marking.** `mark_cells(nb, trusted)` must set `cell.metadata.trusted` to the supplied boolean on code cells for notebook major versions 3 and later. `check_cells(nb)` must return `True` when every code cell is trusted. A code cell must be trusted when its metadata contains a truthy transient `trusted` field or when it has no unsafe rich output. A code cell with only safe or empty outputs must be considered trusted even when not explicitly marked. `check_cells` must remove the transient trusted marker as it checks cells, so the marker does not survive a subsequent JSON round trip.

**Signature stores.** `SignatureStore` subclasses must implement `store_signature`, `check_signature`, `remove_signature`, and `close`. `MemorySignatureStore` must keep signatures for the current process only and must return `True` for known signatures, `False` for unknown, and remove entries silently when absent. `SQLiteSignatureStore` must persist signatures in an SQLite database file.

**Trust CLI.** The `jupyter-trust` script must sign notebooks supplied as path arguments. With no path arguments, it must read a notebook from standard input. With `--reset`, it must remove the trusted signature cache and generate a new signing key. Missing notebook paths must exit nonzero. `--help` must describe signing, `--reset`, and show example usage.

## State Model

The durable notebook state is the JSON document. The in-memory state is a nested `NotebookNode` projection of the same document. The trust state is a local signature-store projection plus transient cell metadata.

The durable JSON projection must contain notebook content and persistent metadata. It must not persist `metadata.signature`, top-level original-format markers, or `cell.metadata.trusted`.

The in-memory projection must preserve the same notebook content with attribute access, recursive node conversion, and normalized multiline text values.

The trust projection must record signatures outside the notebook JSON. Signing and unsigning must change whether a notary recognizes the notebook content, without requiring a durable `metadata.signature` field.

## Error Semantics

Invalid JSON passed to notebook readers must raise a value error subclass indicating that the notebook does not appear to be JSON. Unsupported notebook major versions passed to the generic reader must raise `NBFormatError`. Conversion to an unknown major version must raise `ValueError`. Conversion from a malformed notebook that lacks required attributes must raise `ValidationError`.

Validation failures must raise `ValidationError` or `NotebookValidationError` when using `validate`. `isvalid` must convert validation failure into `False`. v4 constructors must validate constructed objects and must raise validation errors for invalid override combinations.

Path-based `read` must raise `OSError` when the path cannot be opened. Path-based `write` must raise errors when the destination cannot be written. File-like read and write calls must propagate errors raised by the supplied object.

`output_from_msg` must raise `ValueError` for unsupported kernel message types. `NotebookNode.update` must raise `TypeError` for more than one positional update source.

## Cross-View Invariants

1. A notebook parsed by `reads(..., as_version=4)` and then serialized by `writes(..., version=NO_CONVERT)` must preserve notebook content.
2. A notebook written with `write` to a path and then read with `read` from that path must return the same notebook content and must include a final newline in the file.
3. A nested mapping assigned through `NotebookNode` item assignment must be visible through attribute access as a nested `NotebookNode`.
4. A multiline source stored on disk as a list of strings must return as one string through the Python read APIs.
5. A multiline source held in memory as a string must be written by v4 JSON defaults as line lists and must read back as the original string.
6. A notebook converted to its existing major version must return the same object.
7. A notebook signed by a `NotebookNotary` must return `True` from `check_signature` until the same notary unsigns that notebook content or the content changes.
8. A cell marked trusted by `mark_cells` must be reported trusted by `check_cells`, and that transient trust marker must not survive `check_cells` or a JSON write/read round trip.
9. Validation through `validate` and serialization through `writes` must agree on schema validity.

## Public Interface

### Import Surface

The package must be importable as `nbformat`.

```python
import nbformat
from nbformat import (
    NotebookNode, from_dict, reads, read, writes, write,
    NO_CONVERT, current_nbformat, current_nbformat_minor, convert,
)
from nbformat import v1, v2, v3, v4
from nbformat.validator import validate, isvalid, iter_validate, normalize
from nbformat.sign import (
    NotebookNotary, MemorySignatureStore, SQLiteSignatureStore, SignatureStore,
)
from nbformat.v4 import (
    new_notebook, new_code_cell, new_markdown_cell, new_raw_cell,
    new_output, output_from_msg,
)
from nbformat.v2 import parse_filename
from nbformat.v3 import parse_filename
```

The `jupyter-trust` console script must launch the notebook trust application. `python -m nbformat` is not a supported invocation.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `NotebookNode` | class | Mutable dict-like notebook node with attribute access |
| `from_dict` | function | Recursively converts mappings into `NotebookNode` objects |
| `reads` | function | Parses notebook JSON text or bytes |
| `read` | function | Reads a notebook from a path or file-like object |
| `writes` | function | Serializes a notebook to JSON text |
| `write` | function | Writes serialized notebook JSON to a path or file-like object |
| `NO_CONVERT` | constant | Sentinel to preserve the notebook's current major version |
| `current_nbformat` | constant | Current supported notebook major version |
| `current_nbformat_minor` | constant | Current supported notebook minor version |
| `convert` | function | Converts a notebook between major format versions |
| `validate` | function | Validates a notebook or schema fragment |
| `isvalid` | function | Returns boolean validation result without raising |
| `iter_validate` | function | Iterates validation errors instead of raising the first |
| `normalize` | function | Normalizes a notebook and reports edit count |
| `NotebookNotary` | class | Signs notebooks and checks trust state |
| `MemorySignatureStore` | class | In-process signature store |
| `SQLiteSignatureStore` | class | SQLite-backed signature store |
| `SignatureStore` | class | Base signature-store contract |
| `new_notebook` | function | Constructs a valid v4 notebook |
| `new_code_cell` | function | Constructs a valid v4 code cell |
| `new_markdown_cell` | function | Constructs a valid v4 markdown cell |
| `new_raw_cell` | function | Constructs a valid v4 raw cell |
| `new_output` | function | Constructs a valid v4 output object |
| `output_from_msg` | function | Converts kernel IOPub messages into v4 outputs |
| `parse_filename` | function | Parses notebook filename and format for legacy packages |

### CLI Entry Points

| Invocation | Successful behavior | Failure behavior |
| --- | --- | --- |
| `jupyter-trust notebook.ipynb` | Signs the notebook, then exits with status 0 | Missing path exits nonzero |
| `jupyter-trust` with stdin | Reads and signs notebook JSON from stdin, exits 0 | Invalid stdin JSON exits nonzero |
| `jupyter-trust --reset` | Removes signature cache and writes new key, exits 0 | Filesystem errors exit nonzero |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Notebook, signature, and command workflows use local strings, streams, and temporary files.

## Appendix B: Assessment Notes

Compatibility covers the documented imports, notebook construction, dictionary and attribute projections, JSON string and file round trips, conversion, validation paths, v4 readers and writers, trust-store transitions, and `jupyter-trust`. It checks user-visible outcomes, returned objects, public exception classes, durable file contents, and trust state without requiring private helpers, exact schema snapshots, exact error prose, or exact generated identifiers.
