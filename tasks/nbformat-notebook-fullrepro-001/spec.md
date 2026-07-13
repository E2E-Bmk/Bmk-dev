# nbformat Specification

## Product Overview

`nbformat` is the Python reference implementation for reading, writing, validating, converting, constructing, and signing Jupyter Notebook documents. A notebook document is durable JSON with top-level `metadata`, `nbformat`, `nbformat_minor`, and `cells` fields. The Python API returns nested `NotebookNode` objects that behave like dictionaries and expose the same keys as attributes.

The implementation must preserve notebook content across JSON strings, file paths, file-like objects, version conversion, and trust-signature checks. It must keep notebook data JSON-compatible and must treat trust metadata as transient state rather than durable notebook content.

## Scope

This specification covers:

- Top-level `nbformat` imports: `read`, `reads`, `write`, `writes`, `convert`, `validate`, `ValidationError`, `NBFormatError`, `NotebookNode`, `from_dict`, `NO_CONVERT`, `current_nbformat`, `current_nbformat_minor`, `version_info`, `versions`, and `Sentinel`.
- Public validation functions available from `nbformat.validator`: `validate`, `isvalid`, `iter_validate`, `normalize`, `get_validator`, `NotebookValidationError`, and `ValidationError`.
- Public v4 imports from `nbformat.v4`: `new_notebook`, `new_code_cell`, `new_markdown_cell`, `new_raw_cell`, `new_output`, `output_from_msg`, `reads`, `writes`, `to_notebook`, `upgrade`, `downgrade`, `nbformat`, `nbformat_minor`, and `nbformat_schema`.
- Legacy version package entry points exposed from `nbformat.v1`, `nbformat.v2`, and `nbformat.v3` for package-level constructors, package-level readers and writers, and package-level upgrade or downgrade functions.
- Notebook trust APIs from `nbformat.sign`: `NotebookNotary`, `SignatureStore`, `MemorySignatureStore`, and `SQLiteSignatureStore`.
- The `jupyter-trust` console script.

This specification excludes undocumented carrier modules, exact JSON schema snapshot contents, private helper names, exact validation message text, exact generated cell id values, and implementation-specific cache structures.

## Installable Surface

The package must be importable as `nbformat`. The package must expose versioned packages `nbformat.v1`, `nbformat.v2`, `nbformat.v3`, and `nbformat.v4`. The trust machinery must be importable from `nbformat.sign`. Validation helpers listed in Scope must be importable from `nbformat.validator`.

The `jupyter-trust` console script must launch the notebook trust application. `python -m nbformat` is not a supported invocation. Running the trust script with `--help` must describe signing notebooks, `--reset`, common Jupyter application flags, and an example using `jupyter trust`.

## Public API

### NotebookNode and Dictionary Conversion

`NotebookNode` must behave as a mutable dictionary whose keys are also available through attribute access. Reading `node["cells"]` and `node.cells` must return the same value when the key exists. Assigning a mapping through item assignment or `update()` must recursively convert nested dictionaries into `NotebookNode` objects. Assigning a list or tuple containing dictionaries must recursively convert those contained dictionaries.

`from_dict(d)` must return a recursively converted `NotebookNode` when `d` is a dictionary. It must return a list of converted elements when `d` is a list or tuple. It must return non-container values unchanged. It must not validate that the resulting object is a complete or valid notebook.

`NotebookNode.update(*args, **kwargs)` must accept the same single positional update source patterns as a dictionary: a mapping, an object with keys, or an iterable of key-value pairs. It must raise `TypeError` when more than one positional update source is supplied.

### Top-Level Reading and Writing

`reads(s, as_version, capture_validation_error=None, **kwargs)` must parse a notebook JSON string or bytes object, return a `NotebookNode`, and convert it to `as_version` unless `as_version is NO_CONVERT`. It must validate the resulting notebook after parsing and conversion. When validation fails and `capture_validation_error` is a dictionary, it must store the exception under the key `"ValidationError"` and still return the parsed notebook.

`read(fp, as_version, capture_validation_error=None, **kwargs)` must read from a file-like object with `read()` or from a filesystem path. It must delegate to `reads` with the same version and validation behavior. It must open path inputs with UTF-8 text decoding. It must raise the same parsing, version, conversion, and validation exceptions that `reads` raises when those failures are not captured.

`writes(nb, version=NO_CONVERT, capture_validation_error=None, **kwargs)` must serialize a notebook to a JSON string. It must convert to `version` when `version is not NO_CONVERT`; otherwise it must use the notebook document's own major version. It must validate the notebook before serialization. When validation fails and `capture_validation_error` is a dictionary, it must store the exception under `"ValidationError"` and still return serialized JSON.

`write(nb, fp, version=NO_CONVERT, capture_validation_error=None, **kwargs)` must write the JSON string from `writes` to a file-like object with `write()` or to a filesystem path. It must write text, not bytes. It must append a final newline to file output when the serialized string does not already end with one. It must return `None` for successful top-level writes.

`NO_CONVERT` must be a public sentinel value accepted by read and write APIs to preserve the notebook's supplied major version. `current_nbformat` and `current_nbformat_minor` must reflect the current v4 major and minor format supported by the package.

### Conversion

`convert(nb, to_version)` must return `nb` unchanged when the notebook's current major version already equals `to_version`. It must convert notebooks one major version at a time through the public version modules when the requested major version exists. It must ignore minor versions for the conversion target.

`convert` must raise `ValueError` when the requested major version is not implemented. It must raise `ValueError` when a conversion step fails to change the notebook's major version. It must raise `ValidationError` when a conversion step cannot run because the input notebook is missing a required attribute.

### Validation

`validate(nbdict=None, ref=None, version=None, version_minor=None, relax_add_props=False, nbjson=None, repair_duplicate_cell_ids=..., strip_invalid_metadata=...)` must return `None` when the supplied notebook or schema fragment is valid. It must raise `ValidationError` or `NotebookValidationError` when validation fails. It must raise `TypeError` when neither `nbdict` nor `nbjson` is supplied.

When `ref is None`, `validate` must infer `version` and `version_minor` from the notebook if they are not supplied. When `ref` is supplied and `version` is not supplied, validation must use version `1.0` for that fragment. `nbjson` must remain a backward-compatible alias for `nbdict` when `nbdict` is omitted.

For v4.5 and later notebooks, validation must check cell id presence and uniqueness for a whole notebook. With default settings, validation must repair missing or duplicate cell ids and issue the public warning category for that condition. When cell id repair is explicitly disabled, duplicate ids must raise `ValidationError`.

`isvalid(nbjson, ref=None, version=None, version_minor=None)` must return `True` when validation succeeds and `False` when validation raises `ValidationError`. It must leave the supplied object unchanged; if validation mutates the supplied object, `isvalid` must raise `AssertionError`.

`iter_validate(...)` must return an iterator of validation errors instead of raising the first one. `normalize(nbdict, version=None, version_minor=None, *, relax_add_props=False, strip_invalid_metadata=False)` must return `(changes, notebook)` where `changes` is the count of normalization edits and `notebook` is a deep-copy result.

### v4 Notebook Construction and JSON Functions

`nbformat.v4.nbformat` must equal `4`. `nbformat.v4.nbformat_minor` must be the package's current v4 minor value. `nbformat.v4.new_notebook(**kwargs)` must return a valid notebook with `nbformat`, `nbformat_minor`, `metadata`, and `cells` fields, then apply keyword overrides before validation.

`new_code_cell(source="", **kwargs)` must return a valid code cell with an id, `cell_type="code"`, empty metadata, `execution_count=None`, the supplied source, and an empty outputs list, then apply keyword overrides before validation.

`new_markdown_cell(source="", **kwargs)` must return a valid markdown cell with an id, `cell_type="markdown"`, the supplied source, and empty metadata, then apply keyword overrides before validation.

`new_raw_cell(source="", **kwargs)` must return a valid raw cell with an id, `cell_type="raw"`, the supplied source, and empty metadata, then apply keyword overrides before validation.

`new_output(output_type, data=None, **kwargs)` must construct v4 output objects by output type. For `"stream"`, defaults must include `name="stdout"` and `text=""`. For `"display_data"`, defaults must include empty `metadata` and empty `data`. For `"execute_result"`, defaults must include empty `metadata`, empty `data`, and `execution_count=None`. For `"error"`, defaults must include `ename="NotImplementedError"`, `evalue=""`, and an empty `traceback` list. Keyword overrides must be applied before validation. Unsupported or invalid output shapes must raise validation errors.

`output_from_msg(msg)` must accept kernel IOPub messages with header message types `"execute_result"`, `"stream"`, `"display_data"`, and `"error"`, and must return the corresponding v4 output node. It must raise `ValueError` for unrecognized output message types.

`nbformat.v4.reads(s, **kwargs)` must parse v4 JSON and return a `NotebookNode` without top-level version conversion. `nbformat.v4.to_notebook(d, **kwargs)` must convert a disk-format dictionary into a `NotebookNode`, rejoin split multiline text fields, and strip transient trust and signature metadata. `nbformat.v4.writes(nb, **kwargs)` must serialize notebook content as JSON, must default to one-space indentation, sorted keys, `ensure_ascii=False`, and split multiline text fields into line lists unless `split_lines=False` is supplied.

### Legacy Version Packages

`nbformat.v1`, `nbformat.v2`, and `nbformat.v3` must expose their package-level constructors and package-level read/write aliases as importable names. Their package-level JSON readers and writers must return `NotebookNode` objects and JSON strings for that version's document structure. Version packages with Python notebook text reader or writer aliases must preserve those package-level imports.

`nbformat.v2.parse_filename(fname)` and `nbformat.v3.parse_filename(fname)` must return `(filename, notebook_name, format)` where `.ipynb` and `.json` inputs use `"json"`, `.py` inputs use `"py"`, and extensionless inputs append `.ipynb` and use `"json"`.

## Notebook JSON State Model

The durable notebook state is the JSON document. The in-memory state is a nested `NotebookNode` projection of the same document. The trust state is a local signature-store projection plus transient cell metadata used while deciding whether rich output is trusted.

The durable JSON projection must contain notebook content and persistent metadata. It must not persist `metadata.signature`, top-level original-format markers used during conversion, or `cell.metadata.trusted`.

The in-memory projection must preserve the same notebook content with attribute access, recursive node conversion, and normalized multiline text values. It must support mutation through both dictionary and attribute views.

The trust projection must record signatures outside the notebook JSON. Signing and unsigning must change whether a notary recognizes the notebook content, without requiring a durable `metadata.signature` field in the notebook file.

## Notebook Format Behavior

The top-level notebook object must include `metadata`, `nbformat`, `nbformat_minor`, and `cells`. Metadata fields are optional unless a nested documented metadata object defines its own required keys.

Cell objects must include `cell_type`, `metadata`, and `source`. Code cells must include `execution_count` as an integer or `None`, plus `outputs`. Markdown and raw cells support `attachments` as a mapping from filename to mime-bundle.

Multiline text fields in notebook files must be accepted as either a string or a list of strings. Reading through the Python API must rejoin those lists into a single string in memory. Writing through v4 JSON with default settings must split cell sources, stream text, text mime data, JavaScript data, SVG data, and attachment text data into lists of lines. JSON mime values, including `application/json` and `application/*+json`, must remain JSON data rather than line-split strings.

Cell ids in v4.5 and later notebooks must be strings of length 1 through 64 using alphanumeric characters, hyphen, and underscore, and ids must be unique within a notebook. Constructors must provide ids for new v4 cells. Validation must report or repair missing and duplicate ids according to the validation settings.

## Trust and Signatures

`NotebookNotary` must compute content signatures using its configured HMAC algorithm and secret. It must ignore any previous notebook signature metadata while computing the digest. The default algorithm must be `sha256`.

`NotebookNotary.sign(nb)` must store the notebook's signature in its signature store when the notebook major version is 3 or later. It must return without signing notebooks older than major version 3. `check_signature(nb)` must return `True` only when the current notebook content signature is present in the store, and `False` otherwise. `unsign(nb)` must remove the current notebook content signature from the store.

`mark_cells(nb, trusted)` must set `cell.metadata.trusted` to the supplied boolean on code cells for notebook major versions 3 and later. It must return without changing notebooks older than major version 3.

`check_cells(nb)` must return `False` for notebooks older than major version 3. For notebooks version 3 or later, it must return `True` when every code cell is trusted. A code cell must be trusted when its metadata contains a truthy transient `trusted` field or when it has no unsafe rich output. A v4 code cell output of type `"execute_result"` or `"display_data"` with data payload beyond the safe structural keys must make the cell untrusted unless the transient trusted marker is present. `check_cells` must remove the transient trusted marker as it checks cells.

`SignatureStore` subclasses must implement `store_signature(digest, algorithm)`, `check_signature(digest, algorithm)`, `remove_signature(digest, algorithm)`, and `close()`. `MemorySignatureStore` must keep signatures for the current process only, return `True` for known signatures, return `False` for unknown signatures, and remove entries without raising when absent. `SQLiteSignatureStore` must persist signatures in an SQLite database file and must cull older entries when the cache size is exceeded.

The `jupyter-trust` script must sign notebooks supplied as path arguments. With no path arguments, it must read a notebook from standard input and sign that notebook. With `--reset`, it must remove the trusted signature cache when it exists and generate a new notebook signing key.

## Error Semantics

Invalid JSON passed to notebook readers must raise a value error subclass indicating that the notebook does not appear to be JSON. Unsupported notebook major versions passed to the generic reader must raise `NBFormatError`. Conversion to an unknown major version must raise `ValueError`. Conversion from a malformed notebook that lacks required attributes must raise `ValidationError`.

Validation failures must raise `ValidationError` or `NotebookValidationError` when using `validate`. `isvalid` must convert validation failure into `False` and must not hide unexpected mutation of the caller's object. v4 constructors must validate constructed objects and must raise validation errors for invalid override combinations.

Path-based `read` must raise file opening errors from the underlying filesystem when the path cannot be opened. Path-based `write` must raise file opening or write errors from the underlying filesystem when the destination cannot be written. File-like read and write calls must propagate errors raised by the supplied object.

`output_from_msg` must raise `ValueError` for unsupported kernel message types. `NotebookNode.update` must raise `TypeError` for more than one positional update source. `jupyter-trust` must exit with a nonzero status when a requested notebook path is missing.

## Cross-View Invariants

1. A notebook parsed by `reads(..., as_version=4)` and then serialized by `writes(..., version=NO_CONVERT)` must preserve notebook content, while allowing the JSON text layout to differ.
2. A notebook written with `write` to a path and then read with `read` from that path must return the same notebook content and must include a final newline in the file.
3. A nested mapping assigned through `NotebookNode` item assignment must be visible through attribute access as a nested `NotebookNode`.
4. A multiline source stored on disk as a list of strings must return as one string through the Python read APIs.
5. A multiline source held in memory as a string must be written by v4 JSON defaults as line lists and must read back as the original string.
6. A notebook converted to its existing major version must return the same object, so in-memory mutations before and after that no-op conversion are made to the same object.
7. A notebook signed by a `NotebookNotary` must return `True` from `check_signature` until the same notary unsigns that notebook content or the content changes.
8. A cell marked trusted by `mark_cells` must be reported trusted by `check_cells`, and that transient trust marker must not survive `check_cells` or a JSON write/read round trip.
9. Validation through `validate` and serialization through `writes` must agree on schema validity: invalid notebooks must surface validation failure during explicit validation and during write validation unless the caller captures the error.

## Representative Workflow

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

## Non-Goals

- Exact formatting of validation error messages.
- Exact generated cell id strings.
- Exact JSON schema file contents or schema snapshot filenames.
- Private helper modules and undocumented carrier import paths.
- Reimplementation of the underlying JSON Schema libraries.
- Binary notebook formats outside JSON notebook documents.
- UI rendering behavior for notebook frontends.
- Network storage for notebook signatures.

## Invocation Protocol

Python API usage must import `nbformat` or documented subpackages directly. The supported command-line entry point is `jupyter-trust`. `python -m nbformat` is not supported.

Exit behavior:

| Invocation | Successful behavior | Failure behavior |
| --- | --- | --- |
| `jupyter-trust notebook.ipynb` | Signs the notebook or reports that it is already signed, then exits with status 0. | Missing path exits nonzero. Invalid notebook input exits nonzero through the application error path. |
| `jupyter-trust` with stdin | Reads notebook JSON from standard input, signs it, then exits with status 0. | Invalid stdin JSON exits nonzero through the application error path. |
| `jupyter-trust --reset` | Removes the trusted signature cache when present, writes a new signing key, then exits with status 0. | Filesystem errors exit nonzero through the application error path. |

## Evaluation Notes

Assessment exercises the documented public API through observable behavior: import availability, notebook construction, dictionary and attribute projections, JSON string and file round trips, version conversion, validation success and failure paths, v4 reader and writer behavior, trust-store state transitions, and `jupyter-trust` invocation. Scoring is based on user-visible outcomes, returned objects, raised exception classes, durable file contents, and trust-state transitions. Tests do not require private helper modules, exact schema snapshot data, exact error message strings, or exact generated ids.
