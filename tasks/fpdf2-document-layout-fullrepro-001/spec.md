# fpdf2 Document Layout Specification

## Product Overview
`fpdf2` is a Python library for creating PDF documents with the public
`fpdf.FPDF` class. This package covers deterministic document construction,
layout state, built-in fonts, text and drawing primitives, links, document
outlines, metadata, dependency-free tables, and lightweight parsed PDF views.

## Scope
The covered surface uses only local in-memory documents and built-in fonts:

- page formats, orientation, units, margins, effective dimensions, coordinates,
  page numbering, and automatic page breaks;
- built-in font selection, font metrics, text, cells, multi-line cells, writing,
  line breaks, colors, lines, and rectangles;
- external links, internal page links, named destinations, headings, and
  nested document outline entries;
- document information metadata, language, fixed creation dates, and page
  aliases;
- the public table context manager with headers, widths, alignment, wrapping,
  fills, borders, and page splitting;
- `BytesIO` output and semantic checks over PDF headers, page objects, content
  operators, annotations, metadata, and outline titles.

## Installable Surface
The target import is `fpdf`. Public symbols used here are `FPDF`, `FPDFException`,
`FontFace`, and `TextStyle`. The document methods are invoked through the public
`FPDF` surface.

## Product State Model
An `FPDF` instance retains page dimensions, orientation, unit scale, margins,
effective page dimensions, current coordinates, font state, colors, page
inventory, link destinations, outline entries, metadata fields, and the final
in-memory output buffer. Layout operations update coordinates and page state;
output closes the document and materializes its PDF representation.

## Error Semantics
Operations that require a font or an open document raise documented public
exception types. Invalid outline hierarchy raises `ValueError`. The package
checks exception classes and state outcomes, not incidental diagnostic prose.
Deprecation-prone aliases and deprecated parameters are excluded where they
would make a clean warning-free replay impossible.

## Cross-View Invariants
- Effective dimensions reflect the configured page format and margins.
- Text and drawing operations update public coordinates and create corresponding
  semantic content operators in the emitted PDF.
- A document with multiple pages emits the same page inventory observed before
  output.
- Link operations produce link annotations with the requested external URI,
  page destination, or named destination.
- Metadata and fixed creation dates appear in stable document information views.
- Outline operations preserve section titles and parent-child structure.
- Dry-run line planning can be followed by rendering the planned lines.
- A dependency-free table preserves row values while producing cell geometry,
  header styling, and page-splitting content.
- Page aliases resolve to the final page count without requiring a byte snapshot.

## Representative Workflows
1. Configure margins and a built-in font, render cells and multi-line text, and
   inspect coordinates, page count, and content operators.
2. Create a summary page with an internal or named link, add a later detail
   page, and inspect the resulting annotation destination.
3. Set metadata and a fixed creation date, add a nested outline, render a
   heading or table, and inspect the document information and outline views.
4. Plan wrapped lines with a dry run, render them into a table or page region,
   and verify semantic text and geometry across page breaks.

## Non-Goals
External fonts, images, remote resources, sockets, network access, encryption,
HTML, advanced PDF compliance profiles, terminal behavior, exact exception
messages, private implementation attributes, source-test imports, whole-file
byte snapshots, performance guarantees, and host-dependent timestamps are out
of scope. The dependency-free table surface is covered only for deterministic
text rows and basic styling.

## Invocation Protocol
Run the two packaged test modules with `pytest`. The target checkout is placed
on `PYTHONPATH`; test support packages are installed from
the packaged requirements file. The replay uses `-W error` and JSON reporting when
evidence is recorded. All documents use `BytesIO` and disable page-content
compression so semantic operators can be inspected locally.

## Environment
Reference execution uses Python 3.11 on Linux without network access. The
target package is not pre-installed; the fixed checkout is placed on
`PYTHONPATH`. The support and runtime requirements are `pytest`,
`pytest-json-report`, `defusedxml`, `Pillow`, and `fonttools`. Python 3.10 is
also used for a local compatibility replay. No external fonts, images, network
resources, or persistent files are required.

## Evaluation Notes
Assertions use public return values, public state, stable numeric relationships,
PDF headers, page-object counts, content operators, annotations, metadata
fields, and outline titles. They intentionally avoid exact object identifiers,
whole serialized documents, incidental exception strings, and timestamp values
that are not explicitly fixed. Each integration case composes multiple public
operations and declares dependencies on physical atomic test names.
