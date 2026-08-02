# pypdf Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`pypdf` is a pure Python PDF document library that reads local PDF files and streams, exposes document structure through Python objects, edits pages and document-level features, and writes serialized PDF output back to files or byte streams.

The covered state is a local PDF document viewed through public reader and writer APIs: page sequences, page boxes, transformations, extracted text and images, metadata, XMP packets, form fields, outlines, attachments, annotations, JavaScript actions, encryption state, and serialized round trips. The package name is `pypdf`; programmatic use is through Python imports.

## Non-Goals

- This specification does not require a complete implementation of every PDF standard feature.
- This specification does not require private parser, codec, font, crypt-provider, layout-engine, or utility modules.
- This specification does not require network downloads, remote sample-file fetching, external command-line PDF tools, performance measurement, or process resource-limit behavior.
- This specification does not require exact warning text, exact exception message text, exact `repr()` output, or internal object numbering.
- This specification does not define backend-specific cryptography behavior beyond the public password and algorithm contracts described here.
- This specification does not require OCR for scanned documents or visual rendering of pages.

## Representative Workflows

### Merge and Transform Local Pages

```python
from io import BytesIO
from pypdf import PdfReader, PdfWriter, Transformation

base = PdfReader("base.pdf")
stamp = PdfReader("stamp.pdf")
writer = PdfWriter()

first_page = writer.add_page(base.pages[0])
first_page.merge_transformed_page(
    stamp.pages[0],
    Transformation().scale(0.5).translate(tx=72, ty=72),
    expand=True,
)
writer.append("appendix.pdf", pages=(0, 2))

buffer = BytesIO()
writer.write(buffer)
buffer.seek(0)
round_trip = PdfReader(buffer)
assert len(round_trip.pages) == 3
```

This workflow constructs writer state from reader pages, applies a content transformation, imports a page range from another PDF, serializes to a byte stream, and reads the result again through the reader projection.

### Read, Edit, and Preserve Document Features

```python
from io import BytesIO
from pypdf import PdfReader, PdfWriter

reader = PdfReader("form-document.pdf")
writer = PdfWriter(clone_from=reader)

if writer.metadata is not None:
    writer.add_metadata({"/Title": "Updated title"})

writer.update_page_form_field_values(
    writer.pages[0],
    {"customer.name": "Ada Lovelace"},
    auto_regenerate=False,
)
writer.add_attachment("notes.txt", b"local bytes")
writer.add_outline_item("Start", page_number=0)
writer.encrypt("reader-password", algorithm="AES-256")

out = BytesIO()
writer.write(out)
out.seek(0)
encrypted = PdfReader(out)
assert encrypted.is_encrypted
```

This workflow clones an existing document, updates metadata and a form field, adds attachment and outline projections, encrypts the output, and verifies the resulting document state through a fresh reader.

## Document Reading and Navigation

Document reading turns local PDF bytes into reader state that exposes pages and document-level structures.

**Opening inputs.** A `PdfReader` accepts `stream` as a file path, `pathlib.Path`, binary file-like object, or seekable byte stream. The `strict` parameter controls tolerance for malformed PDF structures; the default reader behavior is non-strict. The `password` parameter supplies an initial password attempt for encrypted documents. The `root_object_recovery_limit` parameter bounds root-object recovery work for damaged inputs.

WHEN `stream` is an empty file or empty byte stream, the reader must raise `EmptyFileError`. WHEN the input bytes do not contain a readable PDF structure, the reader must raise `PdfReadError`, `PdfStreamError`, or `ParseError` according to the malformed structure encountered. WHEN `strict` is false, recoverable structural defects must be tolerated with warnings instead of failing the read.

**Pages and indexing.** The `pages` property returns a sequence-like object of `PageObject` instances. `len(reader.pages)`, iteration, positive indexing, and negative indexing must reflect the current page order. `get_num_pages()` returns the same count as `len(reader.pages)`. `get_page(page_number)` returns the page at a zero-based index. If the index is outside the page sequence, then normal Python index errors must be raised.

`get_page_number(page)` returns the zero-based index of a page object present in the document and returns `None` when the page is not present. Each page returned from `pages` must expose `page_number` as its current zero-based page position when it belongs to a document.

**Document projections.** `metadata` returns a `DocumentInformation` mapping-like object or `None`. `xmp_metadata` returns an `XmpInformation` object when an XMP packet exists and returns `None` when no XMP packet is present. `outline` returns a list where outline items are `Destination` objects and nested outline children are represented as nested lists. `named_destinations` returns a mapping from destination names to destinations. `page_labels` returns the display label string for each page in page order. `root_object` returns the reader-visible document catalog dictionary so catalog entries such as document-level JavaScript names are observable through public dictionary access.

WHEN a destination refers to a page in the document, `get_destination_page_number(destination)` returns its zero-based page index. WHEN a destination has no resolvable page in the document, the method returns `None`.

**Encryption state.** `is_encrypted` returns whether the input document is encrypted. `decrypt(password)` accepts a string or bytes password and returns a `PasswordType` value indicating the password result. `PasswordType.NOT_DECRYPTED` must have integer value `0`, `PasswordType.USER_PASSWORD` must have integer value `1`, and `PasswordType.OWNER_PASSWORD` must have integer value `2`, so decryption results must compare equal to those integer values. WHILE a document is encrypted and has not been successfully decrypted, operations that require protected content must raise `FileNotDecryptedError` or `WrongPasswordError` instead of returning misleading content.

## Writing, Merging, and Serialization

Document writing builds an output PDF from blank pages, cloned readers, imported pages, and document-level edits.

**Writer construction.** A `PdfWriter` starts as an empty document when created without input. A writer created with `clone_from` or a file input must initialize its state from the supplied reader, path, file-like object, or byte stream. The `incremental` parameter requests incremental writing against an existing source, while `full` requests full cloning behavior for source objects.

WHEN the source input is not readable as a PDF, writer construction must raise the same public read errors as `PdfReader`. WHEN `incremental` is requested without a usable existing source, writer construction must raise an error rather than emitting a corrupt incremental update.

**Page insertion and blank pages.** The `add_page` method accepts a `page` and optional `excluded_keys`, appends a cloned page, and returns the writer-owned `PageObject`. The `insert_page` method accepts a `page`, an `index`, and optional `excluded_keys`, inserts at the zero-based position, and returns the inserted page. The `add_blank_page` method appends a blank page with the supplied `width` and `height`. The `insert_blank_page` method inserts such a page at the requested `index`. If `insert_blank_page()` omits `width` or `height` and the writer already has pages, the new blank page must use the dimensions of the page currently at or before the insertion point according to the writer's page sequence. `remove_page(index)` must remove the page at the zero-based index and mutate both the writer page sequence and later serialized output.

WHEN blank page dimensions are omitted and no preceding page supplies a size, the writer must raise `PageSizeNotDefinedError`. WHEN a page insertion index is outside normal list insertion behavior, Python sequence errors must be raised.

**Merging source documents.** `append(fileobj, outline_item, pages, import_outline, excluded_fields)` imports pages at the end of the writer. `merge(position, fileobj, outline_item, pages, import_outline, excluded_fields)` imports pages beginning at `position`. The `fileobj` parameter accepts a path, `Path`, file-like object, byte stream, or `PdfReader`. The `pages` parameter accepts `None` for all pages, a `PageRange`, a Python slice-style tuple, or a list of page indexes or page objects. The `outline_item` parameter creates an outline item for imported pages when it is a string. The `import_outline` parameter controls whether source outlines are imported. The `excluded_fields` parameter names fields not imported from source page dictionaries.

WHEN a page range selects pages, the writer must preserve the selected order, including repeated indexes in a list. WHEN `import_outline` is true, named destinations and relevant outline entries for imported pages must be copied to the writer. WHEN `reset_translation(reader)` is called, later clone operations for that reader must no longer reuse previously translated object references.

**Encryption.** The `encrypt` method applies the PDF Standard encryption handler to the writer output. The `user_password` parameter supplies the password that opens the PDF with the configured restrictions. The `owner_password` parameter supplies the password that opens the PDF without those restrictions; WHEN `owner_password` is absent, the writer must use `user_password` as the owner password. The `permissions_flag` parameter accepts a `UserAccessPermissions` value; by default all document permissions exposed by `UserAccessPermissions.all()` are granted. The `UserAccessPermissions` flags include `PRINT`, `MODIFY`, `EXTRACT`, `ADD_OR_MODIFY`, `FILL_FORM_FIELDS`, `EXTRACT_TEXT_AND_GRAPHICS`, `ASSEMBLE_DOC`, and `PRINT_TO_REPRESENTATION`. `to_dict()` returns the eight lowercase permission names mapped to booleans, and `from_dict(mapping)` returns the permission value represented by those names. A mapping produced by `to_dict()` must round trip through `from_dict()`. If `from_dict()` receives any key outside those eight lowercase names, it must raise `ValueError`.

The `algorithm` parameter accepts `"RC4-40"`, `"RC4-128"`, `"AES-128"`, `"AES-256-R5"`, and `"AES-256"`. WHEN `algorithm` is supplied, it must determine the encryption algorithm and the `use_128bit` parameter must be ignored. WHEN `algorithm` is absent and `use_128bit` is true, the writer must use 128-bit RC4 encryption. WHEN `algorithm` is absent and `use_128bit` is false, the writer must use 40-bit RC4 encryption. If `algorithm` is not one of the accepted values, then `encrypt` must raise `ValueError`. If incremental writing is active, then `encrypt` must raise `NotImplementedError`. Where an AES algorithm requires an optional cryptography dependency that is unavailable, encryption or later decryption must raise `DependencyError`.

WHEN encrypted output is written and read again, `PdfReader.is_encrypted` must return true. WHEN the correct user password is supplied to `decrypt`, the reader must expose content subject to the configured user permissions. WHEN the correct owner password is supplied to `decrypt`, the reader must expose the document without user restrictions. WHEN the supplied password is wrong, `decrypt` must return the failure `PasswordType` result or raise `WrongPasswordError` for operations requiring unlocked content.

**Serialization.** `write(stream)` accepts a path, `Path`, binary writable stream, or byte stream and writes a complete PDF representation of the writer state. It returns a tuple whose first value indicates that the write completed and whose second value is the stream object used. `write_stream(stream)` writes to an already opened binary stream. `close()` releases reader and writer file handles owned by the object.

WHEN serialized output is read again with `PdfReader`, the public page count, metadata, outlines, attachments, annotations, form values, page labels, encryption state, and page content changes described in this specification must be observable through the corresponding public reader APIs. WHEN the output stream rejects binary writes, normal stream exceptions must propagate.

## Page Geometry, Transformations, and Extraction

Page objects expose dictionary-style PDF data together with document-oriented page operations.

**Boxes and rotation.** A `PageObject` exposes `mediabox`, `cropbox`, `trimbox`, `bleedbox`, and `artbox` as `RectangleObject` instances with mutable `left`, `bottom`, `right`, `top`, `lower_left`, `lower_right`, `upper_left`, and `upper_right` coordinates. `width` and `height` return the rectangle dimensions. `rotation` returns the page rotation in degrees and setting it stores the page rotation. `rotate(angle)` rotates the page clockwise by a multiple of 90 degrees and returns the page itself.

WHEN `rotate(angle)` receives a value that is not a multiple of 90, it must raise `ValueError`. WHEN a rectangle coordinate setter receives an invalid coordinate shape, normal Python conversion or unpacking errors must be raised.

**Transformations and merging.** `Transformation` represents a six-value current transformation matrix. `translate(tx, ty)`, `scale(sx, sy)`, and `rotate(rotation)` return transformed `Transformation` objects. `matrix` returns a three-row matrix form. `apply_on(point, as_object)` applies the transformation to a two-coordinate point and returns numeric coordinates or PDF numeric objects according to `as_object`.

`merge_page(page2, expand, over)` merges another page's content into the receiver. `merge_transformed_page(page2, ctm, over, expand)` applies a `Transformation` or six-value matrix before merging. `merge_scaled_page`, `merge_rotated_page`, and `merge_translated_page` are convenience operations over the same merge behavior. WHEN `over` is true, merged content must be placed above existing content; WHEN false, merged content must be placed below existing content. WHEN `expand` is true, the target page box must expand to include the transformed merged content.

**Scaling and content streams.** `scale(sx, sy)` scales both page dimensions and page contents. `scale_by(factor)` scales both axes by the same factor. `scale_to(width, height)` scales the page to the requested dimensions. `add_transformation(ctm, expand)` transforms page contents without changing page boxes unless `expand` is true. `transfer_rotation_to_content()` moves page rotation into page content and page boxes, then leaves the page rotation at zero. `get_contents()` returns the page content stream or `None`; `replace_contents(content)` replaces page content with a content stream, encoded stream, array, or no content.

**Text and images.** `extract_text()` returns text extracted from the page. The `orientations` parameter restricts accepted text orientations; positional arguments for orientation remain accepted for documented compatibility. The `extraction_mode` parameter accepts `"plain"` and `"layout"`. The `visitor_text`, `visitor_operand_before`, and `visitor_operand_after` callbacks receive text or drawing operators with the current matrices and font information during extraction.

WHEN `extraction_mode` is `"layout"`, layout-specific keyword parameters such as `layout_mode_space_vertically`, `layout_mode_scale_weight`, and `layout_mode_strip_rotated` must affect whitespace and rotated-text handling. WHEN extraction cannot decode text for a fragment, extraction must continue for other fragments unless the underlying content stream failure is unrecoverable.

The `images` property returns an indexable and iterable view of page image files. Each image object exposes at least `name`, binary `data`, optional Pillow `image`, and `replace()` for replacing image contents where supported. `inline_images` returns images embedded inline in content streams. WHEN optional image dependencies are absent or image data is invalid, image access must raise `DependencyError`, `EmptyImageDataError`, or the relevant decoding exception rather than returning incorrect bytes.

## Metadata, Forms, Outlines, Attachments, and Annotations

Document feature APIs expose high-level views over PDF dictionaries while preserving round-trip behavior through writer output.

**Metadata and XMP.** `DocumentInformation` exposes `title`, `author`, `subject`, `creator`, `producer`, `creation_date`, `modification_date`, and `keywords`, plus corresponding raw properties. Missing fields return `None`. Parsed date properties return Python datetime objects when the stored value has a valid PDF date form and return `None` or the raw value projection when parsing fails.

`PdfWriter.add_metadata(infos)` merges slash-prefixed metadata keys into the document information dictionary. Assigning `writer.metadata` to a dictionary replaces the metadata dictionary. Assigning `None` removes the document information entry. `XmpInformation.create()` returns a new editable XMP packet. XMP Dublin Core, PDF, XMP, XMP Media Management, and PDF/A properties must be readable and writable through their documented property names.

WHEN writer metadata or XMP metadata is serialized and read again, the reader must return the same public metadata values through `metadata` and `xmp_metadata`. WHEN an XMP packet is malformed, XMP access must raise `XmpDocumentError` or return `None` according to whether the packet is unreadable or absent.

**Forms.** `get_fields()` returns a mapping of fully qualified field names to field objects when AcroForm fields exist and returns `None` or an empty mapping when no fields exist. `get_form_text_fields(full_qualified_name)` returns text field names mapped to their string values. `add_form_topname(name)` groups existing form fields under a top-level name; `rename_form_topname(name)` renames an existing top-level group.

`update_page_form_field_values(page, fields, flags, auto_regenerate, flatten)` updates field values on one page, multiple pages, or the writer's relevant pages. WHEN `auto_regenerate` is false, the writer must clear the need-appearances regeneration flag. WHEN `flatten` is true, visible field values must become regular page content. `reattach_fields(page)` must discover widget annotations and attach missing fields where the PDF structure permits it. `get_pages_showing_field(field)` returns every page showing the supplied field or widget.

**Outlines and page labels.** `add_outline_item(title, page_number, parent, before, color, bold, italic, fit, is_open)` creates an outline destination and returns a reference usable as `parent` for nested entries. The `fit` parameter accepts `Fit` helpers such as full-page fit, horizontal fit, vertical fit, rectangle fit, box fit, and XYZ zoom. `find_outline_item(outline_item)` returns the nested index path to an outline item or `None`. `set_page_label(page_index_from, page_index_to, style, prefix, start)` defines page labels for an inclusive page range.

WHEN an outline is written and read again, `reader.outline` must preserve title order, nesting, and destination page mapping. WHEN page labels are written and read again, `reader.page_labels` must return one display label per page in page order.

**Attachments, annotations, and actions.** `add_attachment(filename, data)` adds an embedded file and returns an `EmbeddedFile`. `attachments` returns a mapping from attachment names to lists of byte contents because names are not unique. `attachment_list` returns object-oriented `EmbeddedFile` entries with `name`, `alternative_name`, `description`, `subtype`, `content`, `size`, date, checksum, relationship, and `delete()` behavior.

Annotation classes are dictionary-like objects that represent PDF annotations. `FreeText`, `Text`, `Line`, `Rectangle`, `Ellipse`, `Polygon`, `PolyLine`, `Highlight`, `Link`, and `Popup` must populate the subtype and supplied public fields from constructor parameters such as `text`, `rect`, vertices, points, colors, flags, URL, target page index, and fit. `Text(rect=..., text=..., open=True)` must store subtype `/Text`, the text content, and an `/Open` entry set to true. `FreeText(text=..., rect=..., font=..., bold=True, italic=True, font_size=..., font_color=...)` must store subtype `/FreeText` and a default-style string reflecting italic, bold, font size, font family, and font color. `PolyLine(vertices=...)` must require at least one vertex and raise `ValueError` for an empty vertex list. `PdfWriter.add_annotation(page_number, annotation)` attaches an annotation to the selected page and returns the attached dictionary. `remove_annotations(subtypes)` removes annotations of the selected subtype or subtypes; `remove_links()` removes link annotations.

`JavaScript` represents a JavaScript action dictionary with subtype `/JavaScript`. `PdfWriter.add_js(javascript)` adds document-level JavaScript under the document catalog names dictionary. `PageObject.add_action(trigger, action)` attaches a page action to a trigger from `PageTrigger` in the page additional-actions dictionary, and `delete_action(trigger)` removes the action for that trigger.

## Page Ranges, Generic Objects, and Constants

Supporting public objects provide the vocabulary used by reader and writer workflows.

**Page ranges.** `PageRange` accepts a Python `slice`, another `PageRange`, or a string using slice-like page syntax. `valid(input)` returns whether an input has valid page-range syntax. `to_slice()` returns the equivalent Python slice. `indices(n)` returns normalized start, stop, and step values for a document with `n` pages. Two `PageRange` instances must compare equal when their underlying slices are equal. `parse_filename_page_ranges(args)` parses command-style filename and page-range arguments into filename and `PageRange` pairs. During parsing, a token that is valid page-range syntax must be treated as a range for the preceding filename; all other tokens must be treated as filenames. A filename with no following page-range token must use `PageRange(":")`.

WHEN page-range syntax is invalid, construction must raise `ParseError`. WHEN a parsed filename is followed by a page-range expression, the returned pair must associate that page range with that filename; otherwise the filename must use a range selecting all pages. WHEN parsing begins with a page-range token before any filename has appeared, `parse_filename_page_ranges()` must raise `ValueError`.

**Generic PDF objects.** Public generic classes are Python objects for PDF primitives and containers. `NullObject`, `BooleanObject`, `NumberObject`, `FloatObject`, `NameObject`, `TextStringObject`, `ByteStringObject`, `ArrayObject`, `DictionaryObject`, `StreamObject`, `DecodedStreamObject`, `EncodedStreamObject`, `ContentStream`, `TreeObject`, `Destination`, `OutlineItem`, `Field`, `RectangleObject`, `Fit`, `EmbeddedFile`, and `ViewerPreferences` must behave as dictionary, list, bytes, string, numeric, stream, or tree objects appropriate to their PDF role. `Destination` must expose its title, page reference, fit type, and fit arguments such as `left`, `top`, and `zoom` as public properties. `Fit` helpers must create fit objects whose type and supplied coordinates are observable through destinations; for example, horizontal fit must store type `/FitH` and the supplied `top` coordinate. `PAGE_FIT` is the default full-page fit object used by outline and destination workflows.

`create_string_object()` returns a text or byte string PDF object from Python text or bytes. When the input is bytes, the returned byte-string object must expose the original byte sequence through `original_bytes`. `decode_pdfdocencoding()` and `encode_pdfdocencoding()` convert between PDFDocEncoding bytes and text. `hex_to_rgb()` converts a six-digit hexadecimal color string, with or without a leading hash mark, into three normalized float channel values. `is_null_or_none()` returns true for Python `None`, `NullObject`, and indirect references that resolve to null. `read_object()` reads one PDF object from a binary stream using the supplied PDF context. `read_string_from_stream()` and `read_hex_string_from_stream()` read literal and hexadecimal PDF strings from binary streams and return text or byte string objects.

`extract_links(new_page, old_page)` returns pairs of link-reference objects extracted from corresponding new and old pages. Non-link annotations must be ignored during pairing. If either page has no annotation array or has a null annotation array, the function must treat it as an empty annotation list. If an annotation collection is not an array, the function must return an empty list. `NamedReferenceLink`, `DirectReferenceLink`, and `ReferenceLink` represent named and direct page references while copied links are resolved in a writer.

WHEN a generic object is cloned into a writer, the clone must belong to the destination writer and must preserve the public value of the object. WHEN the same source object is cloned repeatedly without a translation reset, the writer must reuse the existing clone reference. WHEN generic parsing receives malformed object bytes, it must raise `PdfReadError`, `PdfStreamError`, `ParseError`, or `ValueError` according to the public failure mode.

**Constants and enums.** `PasswordType` identifies decryption result classes. `UserAccessPermissions` identifies allowed operations for encrypted documents. `ObjectDeletionFlag` identifies page-object categories removed by writer cleanup APIs. `ImageType` identifies image categories removed by `remove_images()`. `OutlineFontFlag` identifies outline text style flags. `PaperSize` must expose named page-size constants whose values provide `width` and `height` attributes. `PaperSize.A4` must have positive dimensions and its height must be greater than its width. Public error classes in `pypdf.errors` are the exception vocabulary for read, stream, image, password, dependency, deprecation, page-size, and XMP failures.

## State Model

The core state is a PDF document graph backed by local bytes or writer-owned objects. That graph contains a page tree, indirect objects, document catalog entries, metadata dictionaries, XMP packets, outlines, named destinations, page labels, form fields, annotations, attachments, content streams, encryption dictionaries, and serialized file identifiers.

The public projections of this state are:

1. Reader projections: `pages`, `metadata`, `xmp_metadata`, `outline`, `named_destinations`, `page_labels`, `attachments`, `attachment_list`, form APIs, encryption flags, and destination-page mapping.
2. Writer projections: mutable page sequence, metadata, XMP metadata, form updates, outlines, labels, attachments, annotations, JavaScript actions, encryption settings, and serialized output.
3. Page projections: page boxes, rotation, content streams, extracted text, image views, annotations, and transformation results.
4. Generic-object projections: dictionary/list/numeric/string/stream values, cloned object identity, destinations, fields, rectangles, fits, and embedded files.
5. File projections: bytes written to a path or stream and then read by `PdfReader`.

## Error Semantics

| Condition | Required public result |
|---|---|
| Empty PDF input | raises `EmptyFileError` |
| Malformed PDF structure that cannot be recovered | raises `PdfReadError`, `PdfStreamError`, or `ParseError` |
| Protected content is accessed before successful decryption | raises `FileNotDecryptedError` or `WrongPasswordError` |
| Unsupported writer encryption algorithm is requested | raises `ValueError` |
| Encryption is requested for incremental output | raises `NotImplementedError` |
| Blank page dimensions are unavailable | raises `PageSizeNotDefinedError` |
| Page rotation angle is not a multiple of 90 degrees | raises `ValueError` |
| Page-range syntax is invalid | raises `ParseError` |
| Optional image or encryption dependency is required but unavailable | raises `DependencyError` |
| Image data is empty or undecodable through the public image API | raises `EmptyImageDataError` or the relevant decoding exception |
| XMP metadata XML is present but cannot be parsed as XMP | raises `XmpDocumentError` |
| Deprecated public aliases or removed behaviors are invoked | raises `DeprecationError` |

## Cross-View Invariants

1. A page added to a writer from a reader must be observable in `writer.pages`, in the writer's serialized bytes, and in a fresh reader created from those bytes.
2. A page transformation applied through `PageObject` must affect the serialized page content or page boxes consistently with the same page's later reader projection.
3. Metadata written through `PdfWriter.add_metadata()` or `writer.metadata` must be returned through `PdfReader.metadata` after serialization without requiring access to writer internals.
4. XMP metadata written through `writer.xmp_metadata` must be returned through `PdfReader.xmp_metadata` after serialization with the same public property values.
5. A form value updated through `update_page_form_field_values()` must be reflected by form-field reader APIs after serialization for the affected field names.
6. An attachment added through `add_attachment()` must appear both in the name-to-content `attachments` mapping and in the object-oriented `attachment_list` projection after serialization.
7. An outline item added with a parent reference must preserve reader-visible nesting and destination page mapping after serialization.
8. A document encrypted by `PdfWriter.encrypt()` must read back as encrypted, and successful `decrypt()` must expose the protected pages and metadata through the ordinary reader APIs.
9. A page label range set through `set_page_label()` must produce a `page_labels` list whose length matches the page count and whose entries align with page order.
10. Generic object cloning into a writer must preserve public object values while making serialized references belong to the destination document.

## Public Interface

### Import Surface

```python
from pypdf import (
    DocumentInformation,
    ImageType,
    ObjectDeletionFlag,
    PageObject,
    PageRange,
    PaperSize,
    PasswordType,
    PdfReader,
    PdfWriter,
    Transformation,
    __version__,
    mult,
    parse_filename_page_ranges,
)
```

```python
from pypdf.annotations import (
    NO_FLAGS,
    AnnotationDictionary,
    Ellipse,
    FreeText,
    Highlight,
    Line,
    Link,
    MarkupAnnotation,
    PolyLine,
    Polygon,
    Popup,
    Rectangle,
    Text,
)
```

```python
from pypdf.actions import Action, JavaScript, PageTrigger
```

```python
from pypdf.generic import (
    PAGE_FIT,
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    ContentStream,
    DecodedStreamObject,
    Destination,
    DictionaryObject,
    DirectReferenceLink,
    EmbeddedFile,
    EncodedStreamObject,
    Field,
    Fit,
    FloatObject,
    IndirectObject,
    NameObject,
    NamedReferenceLink,
    NullObject,
    NumberObject,
    OutlineFontFlag,
    OutlineItem,
    PdfObject,
    RectangleObject,
    ReferenceLink,
    StreamObject,
    TextStringObject,
    TreeObject,
    ViewerPreferences,
    create_string_object,
    decode_pdfdocencoding,
    encode_pdfdocencoding,
    extract_links,
    hex_to_rgb,
    is_null_or_none,
    read_hex_string_from_stream,
    read_object,
    read_string_from_stream,
)
```

```python
from pypdf.constants import UserAccessPermissions
```

```python
from pypdf.xmp import XmpInformation
```

```python
from pypdf.errors import (
    DependencyError,
    DeprecationError,
    EmptyFileError,
    EmptyImageDataError,
    FileNotDecryptedError,
    LimitReachedError,
    PageSizeNotDefinedError,
    ParseError,
    PdfReadError,
    PdfReadWarning,
    PdfStreamError,
    PyPdfError,
    WrongPasswordError,
    XmpDocumentError,
)
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `PdfReader` | class | Reads local PDF bytes and exposes pages, metadata, forms, outlines, attachments, labels, destinations, and encryption state. |
| `PdfWriter` | class | Builds and serializes PDF documents from blank pages, source readers, page edits, document features, and encryption settings. |
| `PageObject` | class | Represents a PDF page with boxes, rotation, content streams, text extraction, images, annotations, and merge operations. |
| `Transformation` | class | Represents affine transformations used for page content placement and coordinate conversion. |
| `DocumentInformation` | class | Exposes document information metadata through named properties and raw fields. |
| `PageRange` | class | Parses and normalizes page-range expressions. |
| `parse_filename_page_ranges` | function | Converts command-style filename and page-range arguments into filename/range pairs. |
| `PaperSize` | class | Provides named paper-size constants. |
| `PasswordType` | enum | Describes password-decryption results. |
| `UserAccessPermissions` | enum | Selects allowed operations for encrypted documents. |
| `ObjectDeletionFlag` | enum | Selects object categories for writer cleanup operations. |
| `ImageType` | enum | Selects image categories for image removal. |
| `mult` | function | Multiplies two PDF transformation matrices represented as six-value lists. |
| `AnnotationDictionary` | class | Base dictionary type for public annotation objects. |
| `MarkupAnnotation` | class | Base class for markup annotations with reply and title metadata. |
| `FreeText` | class | Creates a free-text annotation dictionary. |
| `Text` | class | Creates a text annotation dictionary. |
| `Line` | class | Creates a line annotation dictionary. |
| `Rectangle` | class | Creates a square-annotation dictionary represented as a rectangle. |
| `Ellipse` | class | Creates a circle-annotation dictionary represented as an ellipse. |
| `Polygon` | class | Creates a polygon annotation dictionary. |
| `PolyLine` | class | Creates a polyline annotation dictionary. |
| `Highlight` | class | Creates a highlight annotation dictionary. |
| `Link` | class | Creates a link annotation targeting a URL or page destination. |
| `Popup` | class | Creates a popup annotation dictionary. |
| `Action` | class | Base dictionary type for public action objects. |
| `JavaScript` | class | Creates a JavaScript action dictionary. |
| `PageTrigger` | enum | Names page-level trigger events for actions. |
| `XmpInformation` | class | Reads, creates, edits, and serializes XMP metadata packets. |
| `PAGE_FIT` | constant | Provides the default full-page fit destination. |
| `PdfObject` | class | Base object for public generic PDF values. |
| `NullObject` | class | Represents the PDF null object. |
| `BooleanObject` | class | Represents a PDF boolean object. |
| `NumberObject` | class | Represents a PDF integer numeric object. |
| `FloatObject` | class | Represents a PDF floating-point numeric object. |
| `NameObject` | class | Represents a PDF name object. |
| `TextStringObject` | class | Represents a decoded PDF text string. |
| `ByteStringObject` | class | Represents a binary PDF string. |
| `ArrayObject` | class | Represents a PDF array with list-like behavior. |
| `DictionaryObject` | class | Represents a PDF dictionary with mapping behavior. |
| `StreamObject` | class | Represents a PDF stream dictionary and stream data. |
| `DecodedStreamObject` | class | Represents decoded stream data. |
| `EncodedStreamObject` | class | Represents encoded stream data. |
| `ContentStream` | class | Represents parsed page content stream operations. |
| `TreeObject` | class | Represents linked PDF tree structures such as outlines. |
| `Destination` | class | Represents a named or outline destination. |
| `OutlineItem` | class | Represents an outline item destination written into an outline tree. |
| `Field` | class | Represents a form field with property access. |
| `RectangleObject` | class | Represents a mutable PDF rectangle. |
| `Fit` | class | Builds destination view-fit modes. |
| `EmbeddedFile` | class | Represents an embedded file attachment. |
| `ViewerPreferences` | class | Represents document viewer-preference settings. |
| `NamedReferenceLink` | class | Tracks a named link destination while copied page links are resolved. |
| `DirectReferenceLink` | class | Tracks a direct page-reference link while copied page links are resolved. |
| `ReferenceLink` | type | Names the public union of named and direct reference-link objects. |
| `OutlineFontFlag` | enum | Selects bold and italic styling for outline items. |
| `create_string_object` | function | Creates a PDF text or byte string object from Python input. |
| `decode_pdfdocencoding` | function | Decodes PDFDocEncoding bytes into text. |
| `encode_pdfdocencoding` | function | Encodes text into PDFDocEncoding bytes. |
| `extract_links` | function | Extracts corresponding link references from two matching pages. |
| `hex_to_rgb` | function | Converts hexadecimal color text into normalized RGB channel values. |
| `is_null_or_none` | function | Tests whether a value is null, an indirect null, or Python `None`. |
| `read_hex_string_from_stream` | function | Reads a hexadecimal PDF string object from a binary stream. |
| `read_object` | function | Reads one public PDF object from a binary stream. |
| `read_string_from_stream` | function | Reads a literal PDF string object from a binary stream. |
| `PyPdfError` | exception | Base exception for package-specific errors. |
| `PdfReadError` | exception | Signals unrecoverable PDF read failures. |
| `PdfStreamError` | exception | Signals malformed PDF stream data. |
| `ParseError` | exception | Signals parse failures in PDF object syntax. |
| `EmptyFileError` | exception | Signals an empty input file or stream. |
| `FileNotDecryptedError` | exception | Signals protected content access before decryption. |
| `WrongPasswordError` | exception | Signals a password that does not unlock a document. |
| `PageSizeNotDefinedError` | exception | Signals blank-page creation without available dimensions. |
| `DependencyError` | exception | Signals a missing optional runtime dependency. |
| `DeprecationError` | exception | Signals use of a removed public alias or behavior. |
| `PdfReadWarning` | exception | Warning category for tolerated read defects. |
| `EmptyImageDataError` | exception | Signals image extraction with no usable image bytes. |
| `LimitReachedError` | exception | Signals a configured safety limit reached during parsing or recovery. |
| `XmpDocumentError` | exception | Signals malformed XMP metadata. |

### CLI Entry Points

There is no console script for this package. `python -m pypdf` is not supported. Programmatic use is through Python imports.

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `pytest`, `pytest-socket`, `pytest-timeout`, `Pillow`, `cryptography`, `PyCryptodome`, and `fonttools`. The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so the package is installable with pip.

## Appendix B: Assessment Notes

Assessment exercises public behavior through local files and in-memory streams. Tests cover reader construction, page sequence behavior, writer page insertion and serialization, page range parsing, page transformations, text extraction modes, image access with installed image dependencies, metadata and XMP round trips, forms, outlines, page labels, attachments, annotations, JavaScript actions, encryption/decryption, generic object behavior, and public exception classes.

Scoring uses observable behavior only. Tests do not require private modules, private helper functions, remote downloads, external PDF command-line tools, exact warning text, exact exception text, exact object numbers, or exact `repr()` output.
