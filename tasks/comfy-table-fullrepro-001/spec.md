
# Comfy Table Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`comfy-table` is a Rust library that builds terminal-oriented text tables from rows, cells, column settings, style presets, and width-arrangement rules. A table owns optional header content, data rows, generated columns, a table style, optional width, delimiter settings, truncation settings, and terminal styling mode; those facts are projected through formatted strings, line iteration, row and column accessors, count methods, style getters, and column-cell iterators.

The library focuses on ordinary rectangular tables where each row contains one cell per visible column. It supports ASCII and UTF-8 border presets, user-built border styles, cell and column alignment, dynamic wrapping to a target width, column constraints, hidden columns, multiline cell content, Unicode-aware width accounting, optional ANSI color and attribute styling, and deterministic programmatic use without a command-line interface.

## Non-Goals

- This specification does not require nested tables, cells spanning multiple columns, or cells spanning multiple rows.
- This specification does not require CSV import, CSV export, or automatic conversion from external tabular file formats.
- This specification does not define private module layout, private helper functions, private fields, or `_integration_test` feature APIs.
- This specification does not require exact `Debug` output, exact panic message text, or compatibility with private upstream test helpers.
- This specification does not require live terminal detection in assessments that set table width explicitly or call `force_no_tty`.
- This specification does not define behavior for malformed ANSI escape sequences beyond preserving ordinary string content and applying documented styling APIs.

## Representative Workflows

### Basic Table Rendering

```rust
use comfy_table::Table;

let mut table = Table::new();
table
    .set_header(vec!["Name", "Role"])
    .add_row(vec!["Ada", "engineer"])
    .add_row(vec!["Lin", "reviewer"]);

let rendered = table.to_string();
let lines: Vec<String> = table.lines().collect();

assert_eq!(table.row_count(), 2);
assert_eq!(table.column_count(), 2);
assert_eq!(rendered, lines.join("\n"));
```

A caller builds a table by adding a header and rows through values convertible into `Row` and `Cell`. The table must generate enough columns for the widest header or data row, and every rendered projection must reflect the same table state.

### Dynamic Width With Column Controls

```rust
use comfy_table::{ColumnConstraint::*, ContentArrangement, Table, Width::*};

let mut table = Table::new();
table
    .set_content_arrangement(ContentArrangement::Dynamic)
    .set_width(32)
    .set_header(vec!["Column A", "Column B"])
    .add_row(vec!["short", "long words that wrap"]);

table
    .column_mut(0)
    .expect("column exists")
    .set_constraint(LowerBoundary(Fixed(8)));
table
    .column_mut(1)
    .expect("column exists")
    .set_constraint(UpperBoundary(Percentage(70)));

let lines: Vec<String> = table.lines().collect();
assert!(lines.iter().all(|line| unicode_width::UnicodeWidthStr::width(line.as_str()) <= 32));
```

Dynamic arrangement must use the explicit table width as the wrapping budget, respect visible columns and column constraints, and keep every rendered line within the target width when the content is splittable under the configured delimiters.

### Custom Style And Alignment

```rust
use comfy_table::{Cell, CellAlignment, ContentLineStyle, LineStyle, Table, TableStyle};

const STYLE: TableStyle = TableStyle::new()
    .top_border(LineStyle::new('[', '-', '+', ']'))
    .header_lines(ContentLineStyle::new('|', '|', '|'))
    .header_separator(LineStyle::new('|', '=', '+', '|'))
    .content_lines(ContentLineStyle::new('|', '|', '|'))
    .bottom_border(LineStyle::new('[', '-', '+', ']'));

let mut table = Table::new();
table
    .load_style(STYLE)
    .set_header(vec![Cell::new("State").set_alignment(CellAlignment::Center)])
    .add_row(vec!["ready"]);

assert_eq!(table.style(), STYLE);
```

Styles are value objects that describe the visible border and separator characters. Loading a style must replace the table's current style, and cell-level alignment must override column-level alignment for the same rendered cell.

## Table Construction And Data Access

Table construction turns caller-provided values into an internal rectangular table state and exposes that state through stable public accessors.

**Cells and rows.** The `Cell::new` and `Cell::new_owned` constructors must accept content that converts to a string. When the input contains newline characters, the cell must preserve those line breaks and `Cell::content()` returns the original logical content joined by newline separators. The `From<T> for Cell` conversion must produce the same logical content as `Cell::new` for string-like and numeric values.

**Cell collections.** `Cells` must wrap a vector of `Cell` values. When a caller converts any iterable whose items convert into `Cell`, the resulting `Cells` must contain one converted cell per input item in input order. `Row::from` must accept any value convertible into `Cells` and must preserve the same cell order.

**Row mutation.** `Row::new` returns an empty row. When `Row::add_cell` receives a `Cell`, the row must append it after existing cells and return the same mutable row for chaining. `Row::cell_count()` returns the number of cells currently stored in the row, and `Row::cell_iter()` returns shared cell references in row order. When `Row::max_height` receives `lines`, the row must store at least one visible line, treating zero as one.

**Table population.** `Table::new` and `Table::default` return an empty table with no header, no data rows, no generated columns, disabled content arrangement, ASCII full styling, no explicit width, space word splitting, and the default truncation indicator. When `set_header` receives a row-like value, the table must replace the current header and generate missing columns up to the header's cell count. When `add_row` receives a row-like value, the table must append it after existing rows, assign it the next row position, and generate missing columns up to that row's cell count.

**Conditional and bulk insertion.** When `add_row_if` receives a predicate that returns `true`, the table must append the row exactly as `add_row` does. When the predicate returns `false`, the table must leave rows and columns unchanged. When `add_rows` receives an iterable of row-like values, the table must append each row in iterator order. When `add_rows_if` receives a predicate that returns `true`, the table must append all rows from the iterable; when the predicate returns `false`, it must not consume the iterable for insertion and must leave the table unchanged.

**Counts and emptiness.** `row_count()` returns the number of data rows and must not count the header. `is_empty()` returns `true` only while the table contains no data rows. `column_count()` must discover columns from the current header and all data rows before returning the number of known columns.

**Indexed access.** `header()` returns `Some(&Row)` after a header has been set and `None` otherwise. `row(index)` and `row_mut(index)` return the data row at zero-based position `index`, or `None` when the index is out of range. `column(index)` and `column_mut(index)` return the generated column at zero-based position `index`, or `None` when the index is out of range. The row and column iterators must yield entries in display order.

**Column discovery after mutation.** If a caller mutates a stored row so it contains more cells than the table currently has columns, `discover_columns()` must generate the missing columns. Any method that reports the column count must also discover missing columns before reporting.

## Rendering, Width, And Content Arrangement

Rendering projects the same table state as strings, individual lines, and trimmed lines while applying width, wrapping, delimiter, truncation, and Unicode display-width rules.

**String projections.** `Table`'s display implementation must return the same content as `table.lines().collect::<Vec<_>>().join("\n")`. `lines()` must return one string per rendered output line in top-to-bottom order. `trim_fmt()` must render the same lines as `lines()` and remove trailing whitespace from each line before joining with newline separators.

**Default rendering.** A new table must use the ASCII full style. Header rows, if present, must render before data rows and must be separated from data rows by the style's header separator when that separator is visible. Data rows must render in insertion order. Multiline cells must expand the physical height of their row so that each logical cell line appears in order.

**Missing cells.** When a visible row has fewer cells than the known column count, rendering must leave the missing cells empty while preserving the column positions established by the header and other rows. When a row has more cells than existing columns, rendering must first discover enough columns to make those cells visible.

**Width selection.** When `set_width` receives a width, `width()` returns that explicit width. Without an explicit width, `width()` returns the detected terminal width only when terminal support is enabled and the selected output stream is a terminal; otherwise it returns `None`. In builds without terminal support, `width()` returns only the explicit width.

**Arrangement modes.** `ContentArrangement::Disabled` must avoid dynamic wrapping except where column constraints impose a fixed or bounded content width. `ContentArrangement::Dynamic` must wrap cell content to fit the available width when a width exists. `ContentArrangement::DynamicFullWidth` must behave like dynamic arrangement and must distribute surplus width across visible columns so the rendered table uses the available width.

**Width fallback.** When the arrangement is `Dynamic` or `DynamicFullWidth` and no width is available, the table must fall back to disabled arrangement for percentage-based behavior and must not fail during rendering. Percentage constraints must be ignored under this fallback.

**Word splitting.** The table delimiter, column delimiter, and cell delimiter define where text splits for wrapping. A cell delimiter overrides its column delimiter, a column delimiter overrides the table delimiter, and the default delimiter is a space. Long words that cannot fit on a line must split by Unicode display width rather than byte count.

**Unicode width.** Rendering and width calculations must use displayed character width, not UTF-8 byte length. Combining marks, CJK characters, emoji sequences, and other multi-codepoint graphemes must not cause line-width calculations to undercount visible output.

**Truncation.** When a row has a maximum height lower than its rendered content height, rendering must keep the allowed number of visible lines and indicate truncated content with the table's truncation indicator. `set_truncation_indicator` must replace the default indicator for subsequent rendering. If the maximum height is zero, the effective maximum remains one visible line.

## Columns, Constraints, And Alignment

Columns hold per-column rendering controls that affect every cell in the same display column unless a more specific cell setting overrides them.

**Column lifecycle.** `Column::new` creates a column with the supplied zero-based index, default padding of one space on the left and one space on the right, no delimiter, no constraint, and no default cell alignment. Generated table columns must use indexes that match their display order.

**Padding and delimiter.** `Column::set_padding` must replace the left and right padding for every rendered cell in the column. `padding_width()` returns the saturating sum of left and right padding. `Column::set_delimiter` sets the default word delimiter for cells in that column unless a cell supplies its own delimiter.

**Constraint assignment.** `Column::set_constraint` stores the column constraint, `constraint()` returns the current constraint by reference, and `remove_constraint()` clears it. `Table::set_constraints` must assign constraints to existing columns from left to right and ignore extra constraints after the last column.

**Constraint meanings.** `ColumnConstraint::Hidden` must remove the column from rendered output and `Column::is_hidden()` returns `true` exactly for that constraint. `ContentWidth` must keep the column as wide as its content. `Absolute` must force the column to the supplied width. `LowerBoundary` must make the column at least the supplied width when possible. `UpperBoundary` must make the column at most the supplied width when possible. `Boundaries` must apply both lower and upper limits.

**Width values.** `Width::Fixed` represents a fixed displayed character width. `Width::Percentage` represents a percentage of available table width, capped at one hundred. Percentage values must affect layout only under dynamic arrangements with a known table width.

**Alignment precedence.** `Column::set_cell_alignment` sets the default alignment for cells in that column. `Cell::set_alignment` sets alignment for one cell. When both are present, the cell-level alignment must override the column-level alignment. `CellAlignment::Left`, `CellAlignment::Right`, and `CellAlignment::Center` must position visible content within the cell's allocated content width after padding and wrapping are applied.

## Styles, Presets, And Terminal Styling

Styles describe every border and separator character used by rendering, and terminal styling decorates cell text when terminal styling support is active.

**Line style values.** `LineStyle::new` must create a horizontal line style with left, fill, junction, and right characters present. `LineStyle::none` must create a line style with no visible parts. The builder methods `left`, `fill`, `junction`, and `right` must return a copy with the corresponding part present and all other parts preserved.

**Content line style values.** `ContentLineStyle::new` must create a content-line style with left, junction, and right characters present. `ContentLineStyle::none` must create a content-line style with no visible parts. The builder methods `left`, `junction`, and `right` must return a copy with the corresponding part present and all other parts preserved.

**Table style values.** `TableStyle::new` must create a style that draws no borders, no separators, and no content-line border characters. The builder methods `top_border`, `header_lines`, `header_separator`, `content_lines`, `row_separator`, and `bottom_border` must return a copy with the corresponding component replaced and all other components preserved.

**Style loading and mutation.** `Table::load_style` must replace the table's style. `style()` returns a copy of the current style. `style_mut()` returns a mutable reference that changes subsequent rendering. Style values must compare by their component characters.

**Preset styles.** The `presets` namespace must export ASCII presets, UTF-8 presets, and `NOTHING`. ASCII presets must use ASCII characters for visible borders and separators. UTF-8 presets must use Unicode box-drawing characters for visible borders and separators. Condensed presets must omit row separators between ordinary data rows. Border-only presets must omit inner vertical separators. Horizontal-only presets must omit side borders. `NOTHING` must draw no borders or separators.

**Style modifiers.** `TableStyle::with_rounded_corners` must replace the outer corner characters with rounded UTF-8 corner characters while preserving non-corner style components. `TableStyle::with_solid_inner_borders` must replace inner content junctions and row separator fill with solid vertical and horizontal line characters while preserving outer borders.

**Cell styling.** When terminal styling support is enabled, `Cell::fg`, `Cell::bg`, `Cell::add_attribute`, and `Cell::add_attributes` must attach foreground color, background color, and text attributes to that cell for rendering. These methods must return updated cells so they compose with `Cell::new`. `Color` must include reset, sixteen base terminal colors, RGB colors, and ANSI 256-color values. `Attribute` must include reset, intensity, italic, underline variants, blink, reverse, conceal, strikeout, frame, encircle, and overline variants.

**Terminal mode.** When terminal styling support is enabled, `force_no_tty()` must make `is_tty()` return `false` and must disable automatic terminal-width lookup. `use_stderr()` must make terminal detection inspect standard error instead of standard output. `enforce_styling()` must make `should_style()` return `true` even when terminal detection is false. `style_text_only()` must restrict ANSI styling to non-padding text content for subsequent rendering.

## State Model

The core state is a table document containing optional header row, ordered data rows, generated columns, style value, content arrangement mode, explicit width, delimiter hierarchy, truncation indicator, and terminal styling flags. Cells contain logical string content split into newline-separated logical lines plus optional delimiter, alignment, and styling metadata.

The public projections of this state are:

- The formatted table string returned by `Display`.
- The ordered rendered lines returned by `lines()`.
- The trimmed formatted string returned by `trim_fmt()`.
- The row, column, header, count, emptiness, style, width, arrangement, and terminal-mode getters.
- The row, column, and column-cell iterators.
- The public style values, preset constants, alignment values, constraint values, width values, colors, and attributes used to build future renderings.

## Error Semantics

| Condition | Required behavior |
|---|---|
| A row, column, or iterator accessor receives an out-of-range index | The accessor must return `None` or end iteration without panicking. |
| `column_cells_iter` or `column_cells_with_header_iter` is created for a column index that does not exist in some rows | The iterator must represent missing cells as `None` for those rows. |
| A table is rendered with dynamic arrangement but no width is available | Rendering must fall back to non-dynamic behavior instead of raising or panicking. |
| A percentage width exceeds one hundred | The effective percentage must be capped at one hundred. |
| A row maximum height of zero is requested | The effective maximum height must be one. |
| More constraints are supplied than the table has columns | Extra constraints must be ignored. |
| A table has no header | `header()` returns `None`, and rendering must omit header lines and header separator content. |
| A table has no data rows | `row_count()` returns zero and `is_empty()` returns `true`; rendering must not invent data rows. |

## Cross-View Invariants

1. The display string must equal the `lines()` projection joined by newline separators for the same table state.
2. The `trim_fmt()` projection must contain the same number of lines as `lines()` and must equal those lines after trailing whitespace is removed from each line.
3. A header or data row that increases the visible cell count must increase the discovered column count, and the corresponding column iterators must expose the generated columns in display order.
4. A row added by `add_row`, `add_rows`, `add_row_if` with a true predicate, or `add_rows_if` with a true predicate must appear in `row_iter()` and in rendered output in insertion order.
5. A column hidden by `ColumnConstraint::Hidden` must be reported as hidden by `is_hidden()` and must be omitted from rendered output while preserving the relative order of remaining visible columns.
6. The style returned by `style()` and the style visible in rendered borders must reflect the last successful `load_style` call or in-place mutation through `style_mut()`.
7. A cell's delimiter and alignment must override the corresponding column-level setting in the rendered projection for that cell, while other cells in the column continue to use the column setting.
8. When an explicit width is set under dynamic arrangement, every rendered line whose content is splittable under the active delimiter hierarchy must fit within the explicit width by displayed character width.
9. A row maximum height must affect the rendered string and `lines()` projection consistently; both projections must show the same truncated physical lines and truncation indicator.
10. Terminal styling flags must affect ANSI decoration only in rendered projections and must not change row counts, column counts, cell content returned by `Cell::content()`, or style value equality.

## Public Interface

### Import Surface

The Cargo package is named `comfy-table` and exposes the Rust library crate `comfy_table`.

```rust
use comfy_table::{
    Attribute, Cell, CellAlignment, Cells, Color, Column, ColumnCellIter,
    ColumnConstraint, ContentArrangement, ContentLineStyle, LineStyle, Row,
    Table, TableStyle, Width,
};
use comfy_table::presets::{
    ASCII_BORDERS_ONLY, ASCII_BORDERS_ONLY_CONDENSED, ASCII_FULL,
    ASCII_FULL_CONDENSED, ASCII_HORIZONTAL_ONLY, ASCII_MARKDOWN,
    ASCII_NO_BORDERS, NOTHING, UTF8_BORDERS_ONLY, UTF8_FULL,
    UTF8_FULL_CONDENSED, UTF8_HORIZONTAL_ONLY, UTF8_NO_BORDERS,
};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Table` | struct | Main builder and renderer for tabular output. |
| `ColumnCellIter` | struct | Iterator over cells in one data-column projection. |
| `Cell` | struct | Stylable unit of table content. |
| `Cells` | struct | Wrapper that converts iterables into cell vectors. |
| `Row` | struct | Ordered collection of cells with optional maximum rendered height. |
| `Column` | struct | Per-column padding, delimiter, constraint, and alignment controls. |
| `CellAlignment` | enum | Horizontal alignment choice for cell content. |
| `ColumnConstraint` | enum | Constraint applied to a column during layout. |
| `Width` | enum | Fixed or percentage width value used by constraints. |
| `ContentArrangement` | enum | Layout mode for disabled, dynamic, or full-width dynamic arrangement. |
| `LineStyle` | struct | Horizontal border or separator style parts. |
| `ContentLineStyle` | struct | Left, junction, and right style parts for content lines. |
| `TableStyle` | struct | Complete table border and separator style. |
| `Color` | enum | Terminal foreground or background color value. |
| `Attribute` | enum | Terminal text attribute value. |
| `presets::ASCII_FULL` | constant | Full ASCII border style with row separators. |
| `presets::ASCII_FULL_CONDENSED` | constant | Full ASCII border style without row separators. |
| `presets::ASCII_NO_BORDERS` | constant | ASCII separator style without outer borders. |
| `presets::ASCII_BORDERS_ONLY` | constant | ASCII outer-border style without inner vertical separators. |
| `presets::ASCII_BORDERS_ONLY_CONDENSED` | constant | Condensed ASCII outer-border style. |
| `presets::ASCII_HORIZONTAL_ONLY` | constant | ASCII horizontal-line style without side borders. |
| `presets::ASCII_MARKDOWN` | constant | Markdown-like ASCII table style. |
| `presets::UTF8_FULL` | constant | Full UTF-8 box-drawing style with row separators. |
| `presets::UTF8_FULL_CONDENSED` | constant | Full UTF-8 box-drawing style without row separators. |
| `presets::UTF8_NO_BORDERS` | constant | UTF-8 separator style without outer borders. |
| `presets::UTF8_BORDERS_ONLY` | constant | UTF-8 outer-border style without inner vertical separators. |
| `presets::UTF8_HORIZONTAL_ONLY` | constant | UTF-8 horizontal-line style without side borders. |
| `presets::NOTHING` | constant | Style that draws no borders or separators. |

### CLI Entry Points

There is no console script for this crate. Programmatic use is through Rust imports from the `comfy_table` crate.

## Appendix A: Environment

The working environment runs Rust on Linux without network access during assessment. The crate must provide a root `Cargo.toml` for the package named `comfy-table`, whose Rust library crate is imported as `comfy_table`.

The assessment environment provides the dependencies declared by the assessment Cargo manifests and lockfile. Non-target crates used by the public tests include `unicode-width`, `unicode-segmentation`, `pretty_assertions`, `proptest`, `rand`, and `rstest`; terminal styling builds also use `crossterm`, and custom styling builds use `ansi-str` and `console`. Test execution uses Cargo metadata and `cargo-nextest`.

## Appendix B: Assessment Notes

Assessment covers public behavior through Rust tests that compile against the `comfy_table` crate. The test dimensions include table construction, row and cell conversion, display and line projections, trim formatting, style presets, custom styles, content arrangement, explicit width handling, constraints, hidden columns, alignment precedence, truncation, Unicode display widths, terminal styling modes, and cross-view consistency between rendered output and public accessors.

The assessment favors reusable behavior families over one-off examples. Tests exercise observable API results, rendered strings for documented style and layout behavior, public enum and constant availability, and state consistency across multiple projections of the same table.
