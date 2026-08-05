# FontTools In-Memory Font Projections Specification

## Product Overview

FontTools is a Python font-engineering library that exposes local font state through public Python APIs. The covered behavior uses tiny generated TrueType-flavored fonts and checks how one in-memory font is projected through table dictionaries, glyph order, Unicode maps, horizontal and vertical metrics, glyph drawing pens, binary save/load streams, TTX XML import/export, and subsetting.

The durable facts are generated during each run: glyph names, cmap entries, glyf outlines, metrics, name records, table tags, XML table fragments, and subset closure. The checks use no bundled font fixtures, platform fonts, external commands, network access, or timestamp-sensitive byte comparisons.

## Scope

This specification covers public in-process behavior for:

- Building a small TrueType font with `fontTools.fontBuilder.FontBuilder`.
- Inspecting and mutating the font through `fontTools.ttLib.TTFont`, `newTable`, table dictionaries, glyph order, and `getBestCmap()`.
- Drawing glyphs through public pen protocols from `fontTools.pens`.
- Saving to bytes, reloading from byte streams, and reordering tables without asserting complete binary identity.
- Exporting selected tables as TTX XML and importing generated XML back into a font.
- Subsetting an in-memory font with `fontTools.subset.Options` and `fontTools.subset.Subsetter`.

## Public Import Surface

The package import name is `fontTools`. The covered public imports are:

```python
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont, newTable, reorderFontTables, sortedTagList, tagToXML, xmlToTag
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.subset import Options, Subsetter
```

No private module import is part of the covered contract.

## Product State Model

A generated font has a glyph order, Unicode character map, glyph outlines, horizontal metrics, vertical metrics, name records, OS/2 fields, post data, and table tags. Glyphs may be empty, simple contour glyphs, or composite glyphs that reference other glyph names.

The public table projection exposes table tags through the font object, table-specific attributes such as `head.unitsPerEm`, `hhea.ascent`, `OS/2.achVendID`, and `hmtx.metrics`, and helper projections such as sorted tag order and XML-safe tag names.

The public glyph projection exposes glyph order, glyph set entries, glyph widths, left side bearings, contour bounds, component references, and pen-recorded drawing operations.

The public serialization projection exposes a saved SFNT byte stream that can be loaded by `TTFont`, plus generated TTX XML fragments for selected tables that can be imported into a new font object.

The public subset projection starts from requested text, Unicode values, or glyph names and produces a reduced in-memory font that keeps requested glyphs and required component dependencies while removing unrelated glyphs and character-map entries.

## Error Semantics

A TrueType glyf build using cubic outlines with the default quadratic glyph format SHALL reject that glyph through a specific public exception type. The covered behavior asserts the exception class only, not the exact message text.

Subsetting and XML import/export SHALL preserve valid generated data without warnings. The covered checks avoid undocumented exact errors, broad exception matching, and comparisons of timestamp-sensitive full binary output.

## Cross-View Invariants

A font saved to bytes and loaded through `TTFont` SHALL preserve glyph order, table membership, cmap mappings, horizontal metrics, name records, glyph bounds, and vertical metric relationships for the generated sample font.

A glyph drawn through a glyph set and a glyph stored in the glyf table SHALL agree on contour bounds for simple glyphs. Composite glyph drawing SHALL expose component references through the public recording pen protocol.

Selected TTX XML export and import SHALL preserve table fields such as head units and name records. Binary-to-XML-to-binary workflows SHALL preserve inspectable public table projections rather than exact complete byte strings.

Subsetting by text, Unicode, and glyph names SHALL agree with the generated cmap and glyf dependency graph. Requested component glyphs SHALL keep their base components, and unrelated glyphs or Unicode mappings SHALL be removed.

## Representative Workflow

A representative workflow constructs a tiny local font in memory, saves it to a byte stream, reloads it as a `TTFont`, inspects table and glyph projections, exports selected tables to TTX XML, imports generated XML into another font, and subsets a copy for requested text. The same generated facts are observed through table access, glyph drawing pens, XML, binary reload, and subset results.

## Non-Goals

The covered behavior excludes command-line tools, real installed fonts, bundled binary fixtures, platform font discovery, optional compression extras, variable-font shaping, exact complete binary snapshots, broad TTX fixture comparisons, private table classes, and exact wording of exception messages.

It also excludes any workflow that requires network access, external executables, sleeping, wall-clock-sensitive output, or persistent global font caches.

## Invocation Protocol

The verifier SHALL run the provided pytest files against an implementation root supplied by `--target-root` or by the `TARGET_ROOT` environment variable. That root must contain the `fontTools` package or a `Lib/fontTools` package tree. The implementation root is added to the front of `sys.path` before the checks run.

The run command may use:

```bash
python -m pytest --rootdir=<workspace-root> <test-directory> -q --target-root <implementation-root>
```

JSON reporting may be enabled with `pytest-json-report` when local evidence is being recorded.

## Environment

The target environment is Linux with Python 3.11, without network access. The target package is not pre-installed; the implementation root is supplied at runtime.

Required local packages:

- `pytest`
- `pytest-json-report`

The checks create tiny generated fonts and temporary XML files under pytest-managed temporary directories. They do not rely on bundled font files, platform fonts, external programs, Docker, network access, credentials, wall-clock timing, or full binary snapshot identity.

## Evaluation Notes

All covered behavior is public library behavior reachable through documented imports. The generated font data is intentionally small so the same font facts can be checked across independent public views without relying on source tests or bundled fixtures.

The checks combine multiple views of the same facts: in-memory table access, glyph set drawing, binary reload, selected XML export/import, and subset closure.
