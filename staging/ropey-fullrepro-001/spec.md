<!-- INTERNAL
task_id: ropey-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: docs.rs/ropey 1.6.1 (crate root docs incl. "A Note About Line Breaks", Rope/RopeSlice/RopeBuilder/iter/str_utils item docs, Error docs), README.md and examples/ at tag v1.6.1; reference behavior observed by running the pinned checkout
-->

# Rope Text Storage Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`ropey` is a UTF-8 text rope library for Rust, built as the text-buffer
backbone of applications such as text editors that must edit and query large
texts efficiently. A `Rope` stores a single logical string and serves every
query and edit through coordinates in four unit systems — bytes, `char`s,
lines, and UTF-16 code units — with all conversions and lookups running in
logarithmic time.

The library exposes one shared fact — the text content — through several
coordinated projections: length metrics and coordinate conversions, indexed
accessors for single bytes/chars/lines, chunk-level access to contiguous
string segments, immutable `RopeSlice` views over arbitrary ranges,
bidirectional iterators over bytes, chars, lines, and chunks, in-place
editing operations, streaming construction and I/O, and content-based
comparison, ordering, and hashing against ropes, slices, and standard
string types.

`Rope` behaves as a value type with persistent-structure sharing: cloning is
a constant-time operation, clones share storage, and edits to one clone
never change the content observed through any other clone. All operations
uphold `char`-boundary correctness: no API ever splits a multi-byte UTF-8
scalar value, and byte-oriented entry points that would do so fail instead.

## Non-Goals

- This specification does not require grapheme-cluster segmentation,
  Unicode word segmentation, or any text-shaping facility.
- This specification does not require search, regular-expression, or
  pattern-matching APIs over rope content.
- This specification does not require serialization support beyond the
  string and I/O conversions described in this document.
- This specification does not require any locking or transactional facility
  for concurrent mutation of a shared rope; concurrency support is limited
  to the `Send`/`Sync` value semantics described in State Model.
- This specification does not define a stable in-memory chunk layout: the
  segmentation of text into chunks is an implementation choice, and no
  caller-visible behavior other than the chunk APIs themselves depends
  on it.
- This specification does not define panic message texts; failure
  identity is carried by the `Error` type and by which call panics, not
  by message wording.

## Representative Workflows

The two workflows below exercise the library end to end: loading, editing,
and saving a document, and navigating one document state through several
coordinate systems and views.

**Editing a document loaded from a reader.**

```rust
use std::io::Cursor;
use ropey::Rope;

// Load from any std::io::Read source.
let mut rope = Rope::from_reader(Cursor::new("One morning\nthe cat sat\n"))?;
assert_eq!(rope.len_lines(), 3); // "One morning\n", "the cat sat\n", ""

// Replace the word "cat" on line 1 with "heron".
let line_start = rope.line_to_char(1);
rope.remove(line_start + 4..line_start + 7);
rope.insert(line_start + 4, "heron");
assert_eq!(rope.line(1).as_str(), Some("the heron sat\n"));

// Save through any std::io::Write sink.
let mut out: Vec<u8> = Vec::new();
rope.write_to(&mut out)?;
assert_eq!(std::str::from_utf8(&out).unwrap(), "One morning\nthe heron sat\n");
# Ok::<(), Box<dyn std::error::Error>>(())
```

**One text, many projections.**

```rust
use ropey::Rope;

let rope = Rope::from_str("garden path\nsecond éclair\n");

// Metrics agree across unit systems.
let n_chars = rope.len_chars();
assert_eq!(rope.byte_to_char(rope.len_bytes()), n_chars);

// A slice is a first-class view with the same read surface.
let slice = rope.slice(rope.line_to_char(1)..n_chars);
assert_eq!(slice, "second éclair\n");
assert_eq!(slice.len_lines(), 2);

// Iterators walk the same facts in both directions.
let forward: String = slice.chars().collect();
let mut rev = slice.chars();
rev.reverse();
let backward: String = rev.collect();
assert_eq!(forward.chars().rev().collect::<String>(), backward);

// Chunk access exposes contiguous segments plus their start coordinates.
let (chunk, b, c, l) = rope.chunk_at_byte(0);
assert!(rope.len_bytes() >= chunk.len());
assert_eq!((b, c, l), (0, 0, 0));
```

## Building and Persisting Text

This section covers every way a rope comes into existence, how text leaves
the rope again, and the storage guarantees that hold across those
transitions.

**Direct construction.** `Rope::new` returns an empty rope. `Rope::from_str`
builds a rope from a string slice in O(N) time. `Rope` also implements
`Default` (an empty rope) and `From` conversions from `&str`, `String`,
`Cow<str>`, and `RopeSlice`, plus `FromIterator` over `&str`, `String`, and
`Cow<str>` items, which concatenates the items in iteration order. In the
reverse direction, `String`, `Cow<str>` conversions exist `From` a `Rope`
and `From<&Rope>`; converting `&Rope` to `Cow<str>` returns a borrowed
string only when the rope's content is a single contiguous segment,
otherwise an owned string.

**Streaming construction.** `RopeBuilder` builds a rope incrementally from
in-order text pieces. `RopeBuilder::new` creates an empty builder, `append`
adds the next piece of text (called any number of times, with pieces of any
size including empty), and `finish` consumes the builder and returns the
completed rope. The finished rope must equal the concatenation of the
appended pieces; piece boundaries carry no observable meaning. The builder
implements `Default`.

**Reader and writer I/O.** `Rope::from_reader` consumes any `std::io::Read`
and returns `ropey::Rope` wrapped in `std::io::Result`. If the reader
returns an error, `from_reader` stops and returns that error. If the data
read is not valid UTF-8, `from_reader` returns an I/O error of kind
`InvalidData`. `Rope::write_to` writes the rope's entire content, in order,
to any `std::io::Write`, returning the first write error if one occurs.

**Value semantics and sharing.** Cloning a rope is O(1) and produces an
independent value that shares storage with the original. After an edit to
one clone, every other clone observes its original content unchanged.
`Rope::is_instance` reports whether two ropes are clones sharing the same
underlying storage instance: it returns `true` for un-edited clones of one
another and `false` for ropes built separately, even when their contents
are equal.

**Capacity.** `Rope::capacity` returns the total byte capacity of the
rope's allocated buffers, which is at least `len_bytes()`.
`Rope::shrink_to_fit` rebuilds storage to minimize unoccupied capacity,
preserving content exactly; after it returns, `capacity()` does not exceed
the previous capacity. Both are O(N) at worst and neither changes any
observable content.

## Metrics and Coordinate Conversion

This section defines the four coordinate systems and the conversion rules
between them; these rules are the foundation every other projection builds
on. All conversions exist on both `Rope` and `RopeSlice` (where they apply
to the view's own local coordinates), and each runs in O(log N) time.

**Length metrics.** `len_bytes` is the length of the content in UTF-8
bytes. `len_chars` is the length in Unicode scalar values. `len_utf16_cu`
is the length in UTF-16 code units, where every scalar value above
U+FFFF counts as two units. `len_lines` is the number of line-break
characters in the content plus one (see Line Semantics); an empty rope has
`len_lines() == 1`.

**In-bounds rule.** Every index-taking method on `Rope` and `RopeSlice`
accepts indices up to and including the length in that unit system when the
method's purpose is positional (conversions, `insert`, `split_off`,
iterator `*_at` constructors, `chunk_at_*`), and panics when the index
exceeds that length. The one-past-the-end position is a valid position; it
is not a valid element index (see Reading Content for element accessors).

**Byte ↔ char.** `byte_to_char` returns the char index of the char that
contains the given byte; a byte index interior to a multi-byte char resolves
to that char's index, and the one-past-the-end byte index returns the
one-past-the-end char index. `char_to_byte` returns the byte index at which
the given char begins. `try_byte_to_char` and `try_char_to_byte` are the
non-panicking twins returning `ropey::Result`.

**Byte/char ↔ line.** `byte_to_line` and `char_to_line` return the index of
the line containing the given position, equivalently the number of line
breaks strictly before it; the one-past-the-end position returns the last
line index. `line_to_byte` and `line_to_char` return the position at which
the given line begins; the index `len_lines()` is accepted and returns the
one-past-the-end position. Each has a `try_` twin.

**Char ↔ UTF-16.** `char_to_utf16_cu` returns the UTF-16 code-unit offset
of the given char, and `utf16_cu_to_char` maps a code-unit offset back to
the index of the char containing it; the one-past-the-end position maps to
the one-past-the-end position in the other system. Each has a `try_` twin.
A `utf16_cu_to_char` argument that lands between the two code units of a
surrogate pair resolves to the char containing the pair.

**Flat-string helpers.** The module `ropey::str_utils` exposes the same
conversion rules over plain `&str` values, for callers building
functionality on top of chunk access: `byte_to_char_idx`,
`char_to_byte_idx`, `byte_to_line_idx`, `line_to_byte_idx`,
`char_to_line_idx`, and `line_to_char_idx`. These functions clamp instead
of panicking: any past-the-end input index resolves to the corresponding
last valid output (the one-past-the-end index for position outputs, the
last line index for line outputs), and interior byte indices resolve to the
containing char or line exactly as above. They run in O(N) time over the
given slice.

## Reading Content

This section covers element accessors and chunk access — the read
primitives on which iteration and comparison are defined. Every accessor
exists on both `Rope` and `RopeSlice` in local coordinates.

**Element accessors.** `byte(byte_idx)` returns the byte at the given
index, `char(char_idx)` returns the char, and `line(line_idx)` returns the
line as a `RopeSlice` (including its terminating line break, if any). These
accessors take element indices, not positions: `byte` panics when
`byte_idx >= len_bytes()`, `char` when `char_idx >= len_chars()`, and
`line` when `line_idx >= len_lines()`. The last line (index
`len_lines() - 1`) is a valid element and its slice is empty when the
content ends in a line break. `get_byte`, `get_char`, and `get_line`
return `Option` instead of panicking.

**Chunk access.** Rope content is stored as contiguous UTF-8 segments
called chunks. `chunk_at_byte(byte_idx)` returns a four-tuple
`(chunk, chunk_byte_idx, chunk_char_idx, chunk_line_idx)`: the chunk
containing the given byte, plus the byte, char, and line indices at which
the chunk starts. `chunk_at_char` and `chunk_at_line_break` return the same
tuple shape, locating the chunk by char index or by line-break index. For
`chunk_at_line_break`, the beginning and end of the content count as
breaks for indexing: index 0 locates the chunk containing the first byte,
index `i` in `1..len_lines()` locates the chunk containing the `i`-th line
break, and index `len_lines()` locates the last chunk; the call panics
above `len_lines()`. A one-past-the-end index to `chunk_at_byte` and
`chunk_at_char` returns the last chunk. Every chunk of a non-empty rope is non-empty; a
multi-byte char is never split across a chunk boundary, and a CRLF pair is
never split across a chunk boundary. The concatenation of all chunks in
order equals the content exactly. The fallible twins are `get_chunk_at_byte`,
`get_chunk_at_char`, and `get_chunk_at_line_break` on `Rope` (returning
`Option`), and `try_chunk_at_byte`, `get_chunk_at_char`, and
`get_chunk_at_line_break` on `RopeSlice` (the byte form returns
`ropey::Result`, the other two return `Option`).

**Whole-content rendering.** `Rope` and `RopeSlice` implement `Display`,
producing exactly the content, and `Debug`, whose output reflects the
chunk segmentation and carries no cross-build format contract.
`RopeSlice::as_str` returns `Some(&str)` only when the
view's content is contiguous in memory — always true for slices obtained
`From<&str>` and for empty slices — and `None` otherwise.

## Editing

This section defines the mutating operations on `Rope`; all of them
preserve UTF-8 validity, the metrics/conversion rules, and clone
independence. Char indices address edit positions.

**Insertion.** `insert(char_idx, text)` inserts the string at the given
char position; `char_idx` ranges over `0..=len_chars()`. Inserting an empty
string is a no-op. `insert_char(char_idx, ch)` inserts a single char.
After insertion, content before the position is unchanged, the inserted
text occupies char positions `char_idx..char_idx + inserted_chars`, and
prior content from `char_idx` onward is shifted by the inserted length.
Both panic when `char_idx > len_chars()`; `try_insert` and
`try_insert_char` return `ropey::Result` instead.

**Removal.** `remove(char_range)` removes the chars in the given range,
accepting any `RangeBounds<usize>` form over char indices (`a..b`, `a..`,
`..b`, `..`, and inclusive forms). Removing an empty range is a no-op;
`remove(..)` empties the rope. The method panics when the range start
exceeds its end or the end exceeds `len_chars()`; `try_remove` returns
`ropey::Result` instead.

**Splitting and joining.** `split_off(char_idx)` removes everything from
the char position onward and returns it as a new rope, leaving the prefix
in place; index 0 moves the whole content into the returned rope, and index
`len_chars()` returns an empty rope. It panics when
`char_idx > len_chars()`; `try_split_off` returns `ropey::Result`.
`append(other)` consumes another rope and attaches its content at the end;
appending an empty rope, or appending onto an empty rope, is exact
concatenation like every other case.

## Slicing

This section defines immutable views. A `RopeSlice` is a zero-copy view
into a rope (or into another slice) carrying the full read surface —
metrics, conversions, accessors, chunk access, iterators, comparison, and
re-slicing — in coordinates local to the view.

**Char-range slicing.** `slice(char_range)` on `Rope` or `RopeSlice`
returns the view over the given char range, accepting all
`RangeBounds<usize>` forms. `slice(..)` is the whole content. An empty
range yields an empty slice. The call panics when the range is reversed
(start greater than end) or its end exceeds `len_chars()`. `get_slice`
returns `Option` instead.

**Byte-range slicing.** `byte_slice(byte_range)` returns the view over the
given byte range under the same range-form rules, with one additional
requirement: both endpoints must fall on char boundaries. The call panics
on a reversed range, an out-of-bounds end, or an endpoint interior to a
multi-byte char. `get_byte_slice` returns `Option` instead.

**Slice provenance and conversion.** `RopeSlice` implements `From<&str>`,
producing a view over borrowed flat text with identical behavior to a
rope-backed slice. `From<RopeSlice>` conversions produce a `String`, a
`Cow<str>` (borrowed only when the slice is contiguous), and a `Rope`
(an independent rope equal to the slice's content). Slicing a slice
composes: `s.slice(a..b).slice(c..d)` equals `s.slice(a + c..a + d)`.

## Line Semantics

This section defines what counts as a line break and how content divides
into lines; every line-indexed API on `Rope` and `RopeSlice` follows these
rules. Line-break recognition is a build-time property of the crate,
selected by cargo features.

**Recognized line breaks.** The crate always recognizes LF (`U+000A`) and
the CRLF pair (`U+000D` followed by `U+000A`). Where the `cr_lines` feature
is enabled, a lone CR (`U+000D`) is also a line break. Where the
`unicode_lines` feature is enabled (which implies `cr_lines` and is enabled
by default), the following are additionally recognized: VT (`U+000B`), FF
(`U+000C`), NEL (`U+0085`), Line Separator (`U+2028`), and Paragraph
Separator (`U+2029`). A CRLF pair always counts as a single line break.

**Line partition.** The start of the content and each position immediately
after a line break begin a line; each line break belongs to the line it
terminates. Content of `"alpha\nbeta"` has two lines, `"alpha\n"` and
`"beta"`; `"alpha\nbeta\n"` has three lines, the last one empty. An empty
rope or slice has exactly one line, the empty line. `len_lines` equals the
number of line breaks plus one, and the `line`, `lines`, `*_to_line`, and
`line_to_*` APIs all agree with this partition.

**Slicing across CRLF.** Slicing at a char boundary between a CR and an LF
is permitted; each side of such a split counts its own line-break
characters as found in its visible text.

## Iterators

This section defines the four iterator families. All iterators are
bidirectional, cheap to construct at any valid position, and defined
entirely by the read surface: iterating never mutates the underlying text.

**Families and items.** On both `Rope` and `RopeSlice`: `bytes()` yields
`u8`, `chars()` yields `char`, `lines()` yields each line as a `RopeSlice`
(terminators included), and `chunks()` yields each chunk as `&str`. The
iterator types live in `ropey::iter` as `Bytes`, `Chars`, `Lines`, and
`Chunks`. `Bytes`, `Chars`, and `Lines` implement `ExactSizeIterator`
(their `len()` reports the number of items remaining in the current
direction); `Chunks` implements `Iterator` only.

**Positioned construction.** `bytes_at(byte_idx)`, `chars_at(char_idx)`,
and `lines_at(line_idx)` start iteration at the given position; each
accepts positions up to and including the corresponding length metric, and
an at-the-end iterator's `next()` returns `None`. Each panics past that
bound, with `get_bytes_at`, `get_chars_at`, and `get_lines_at` returning
`Option` instead. `chunks_at_byte`, `chunks_at_char`, and
`chunks_at_line_break` return a four-tuple
`(chunks, chunk_byte_idx, chunk_char_idx, chunk_line_idx)`: an iterator
positioned at the chunk containing the given position plus that chunk's
start coordinates, under the same index rules as `chunk_at_*`; when the
input index is one-past-the-end, the iterator is positioned past the last
chunk (its `next()` returns `None`) and the returned coordinates are the
content's total lengths. Their fallible twins are `get_chunks_at_byte`,
`get_chunks_at_char`, and `get_chunks_at_line_break`.

**Bidirectional movement.** Every iterator has `prev()`, which moves one
item backward and returns it, or returns `None` at the start; `next()` and
`prev()` are exact inverses, so alternating them revisits the same item.
An iterator constructed at the end position walks the whole content
backward via `prev()`.

**Direction reversal.** Every iterator has `reverse()`, which flips the
meaning of `next()` and `prev()` in place at the current position, and
`reversed()`, which does the same but consumes and returns the iterator.
After a reversal, `next()` yields exactly what `prev()` would have yielded
before it. Reversing twice restores the original direction.

## Comparison, Ordering, and Hashing

This section defines content-based equivalence across every pairing of
rope, slice, and standard string types; these comparisons never depend on
chunk layout, construction path, or shared storage.

**Equality.** `Rope` and `RopeSlice` implement `Eq` and `PartialEq` in
every direction against themselves, each other, `str`, `&str`, `String`,
and `Cow<str>`. Equality holds exactly when the byte content is identical.
Two ropes built differently (for example, one via `from_str` and one via a
builder or many small edits) compare equal whenever their content matches.

**Ordering.** `Rope` and `RopeSlice` implement `Ord` and `PartialOrd`
against their own type, comparing content lexicographically by bytes —
the same ordering `str` comparison produces on the flattened content.

**Hashing.** `Rope` and `RopeSlice` implement `Hash` such that equal
content produces an identical hash stream, regardless of chunk layout or
construction history, and a rope hashes identically to its full slice.
With any given `Hasher`, `hash(rope_a) == hash(rope_b)` whenever
`rope_a == rope_b`.

## State Model

The core state is one UTF-8 string per `Rope` value, stored as a balanced
tree of non-empty chunks with cached byte/char/line-break/UTF-16 counts.
Every public projection reads that single state:

- **Metrics** (`len_*`) report cached totals.
- **Conversions** (`*_to_*`, `str_utils` helpers) map between the four
  coordinate systems.
- **Accessors** (`byte`/`char`/`line`, `chunk_at_*`) read elements and
  segments.
- **Views** (`slice`, `byte_slice`, `RopeSlice`) narrow the visible range
  without copying.
- **Iterators** (`bytes`/`chars`/`lines`/`chunks` and `*_at` forms) stream
  the state in either direction.
- **Edits** (`insert*`, `remove`, `split_off`, `append`) replace the state
  with a new value; views and iterators borrow the rope, so Rust's
  borrowing rules sequence edits between reads.
- **I/O and conversions** (`from_reader`, `write_to`, `From`/`FromIterator`
  impls) move whole contents in and out.
- **Comparison/order/hash** project the state alone, never identity —
  identity is observable only through `is_instance`.

`Rope`, `RopeSlice`, and all four iterators are `Send` and `Sync`; a clone
moved to another thread observes the content it was cloned with. Edits
never invalidate other clones (persistent copy-on-write semantics), and
every edited rope upholds the same invariants as a freshly built one:
non-empty chunks, chars and CRLF pairs never split across chunk
boundaries, and cached metrics consistent with the content.

## Error Semantics

Failure surfaces in two coordinated forms: panicking methods for
programming errors, and fallible twins that report the same conditions as
values. For every panicking indexed method, the `try_` twin returns
`ropey::Result<T>` (an alias for `Result<T, ropey::Error>`) and the `get_`
twin returns `Option<T>`; the twin returns `Err`/`None` under exactly the
conditions listed as panics for the base method, and the base method's
success value otherwise. I/O entry points return `std::io::Result` and are
described in Building and Persisting Text.

`ropey::Error` is a non-exhaustive enum implementing `std::error::Error`,
`Display`, `Debug`, `Copy`, and `Clone`. Its variants and payloads:

| Variant | Payload | Condition |
|---------|---------|-----------|
| `ByteIndexOutOfBounds` | attempted index, byte length | byte index > `len_bytes()` |
| `CharIndexOutOfBounds` | attempted index, char length | char index > `len_chars()` |
| `LineIndexOutOfBounds` | attempted index, line count | line index out of the method's accepted range |
| `Utf16IndexOutOfBounds` | attempted index, UTF-16 length | UTF-16 offset > `len_utf16_cu()` |
| `ByteIndexNotCharBoundary` | attempted index | byte index interior to a multi-byte char where a boundary is required |
| `ByteRangeNotCharBoundary` | optional start, optional end | a `byte_slice` endpoint interior to a multi-byte char |
| `ByteRangeInvalid` | start, end | reversed byte range (end < start) |
| `CharRangeInvalid` | start, end | reversed char range (end < start) |
| `ByteRangeOutOfBounds` | optional start, optional end, byte length | byte range end past `len_bytes()` |
| `CharRangeOutOfBounds` | optional start, optional end, char length | char range end past `len_chars()` |

Range-payload `Option` fields are `None` for endpoints the caller left
open (half-open range forms). When a range is both reversed and out of
bounds, the `*RangeInvalid` variant takes precedence. `Display` for each
variant names the failing index or range and the relevant length;
`Debug` output carries the same information.

## Cross-View Invariants

1. For every rope and every slice of it, `chars().count()` equals
   `len_chars()`, `bytes().count()` equals `len_bytes()`, and
   `lines().count()` equals `len_lines()` — iteration and metrics agree.
2. For every valid char index `i`, `byte_to_char(char_to_byte(i)) == i`,
   and for every valid line index `l`,
   `byte_to_line(line_to_byte(l)) == l` — conversions round-trip through
   every unit pair that starts from an exact position.
3. The concatenation of `chunks()` equals the `String` conversion of the
   same rope or slice, and the concatenation of `lines()` equals it as
   well — segment projections reassemble to the whole.
4. After `insert(i, t)` on any rope, the new content equals
   `old.slice(..i) + t + old.slice(i..)` rendered as strings, and after
   `remove(a..b)` it equals `old.slice(..a) + old.slice(b..)` — editing
   agrees with slicing.
5. `rope.slice(..) == rope`, and for any nested slice,
   `s.slice(a..b).slice(c..d) == s.slice(a + c..a + d)` — views compose
   and preserve equality.
6. For any two ropes with equal content, every metric, every conversion,
   every element and line accessor, the `bytes`/`chars`/`lines` item
   sequences, `Ord` comparisons against a third rope, and the `Hash`
   stream are identical regardless of how each rope was built — content
   determines every projection except chunk segmentation.
7. A clone taken before an edit compares equal to the pre-edit content
   after the edit, while `is_instance` distinguishes shared-storage clones
   from independently built equals — persistence and identity are
   separate facts.

## Public Interface

### Import Surface

```rust
use ropey::{Rope, RopeSlice, RopeBuilder, Error, Result};
use ropey::iter::{Bytes, Chars, Chunks, Lines};
use ropey::str_utils::{
    byte_to_char_idx, byte_to_line_idx, char_to_byte_idx,
    char_to_line_idx, line_to_byte_idx, line_to_char_idx,
};
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Rope` | struct | Mutable UTF-8 text rope; construction, metrics, conversions, accessors, edits, slicing, iteration, I/O, comparison |
| `RopeSlice` | struct | Immutable view over a rope range or `&str`; full read surface in local coordinates |
| `RopeBuilder` | struct | Incremental in-order rope construction via `append` and `finish` |
| `iter::Bytes` | struct | Bidirectional byte iterator with `prev`, `reverse`, `reversed`; exact-size |
| `iter::Chars` | struct | Bidirectional char iterator with `prev`, `reverse`, `reversed`; exact-size |
| `iter::Lines` | struct | Bidirectional line iterator yielding `RopeSlice` items; exact-size |
| `iter::Chunks` | struct | Bidirectional chunk iterator yielding `&str` segments |
| `Error` | enum | Index/range failure taxonomy returned by `try_` methods |
| `Result` | type alias | `std::result::Result<T, ropey::Error>` |
| `str_utils::byte_to_char_idx` | function | Byte index to char index on a `&str`, clamping past-the-end |
| `str_utils::char_to_byte_idx` | function | Char index to byte index on a `&str`, clamping past-the-end |
| `str_utils::byte_to_line_idx` | function | Byte index to line index on a `&str`, clamping past-the-end |
| `str_utils::line_to_byte_idx` | function | Line index to byte index on a `&str`, clamping past-the-end |
| `str_utils::char_to_line_idx` | function | Char index to line index on a `&str`, clamping past-the-end |
| `str_utils::line_to_char_idx` | function | Line index to char index on a `&str`, clamping past-the-end |

### CLI Entry Points

There is no executable entry point for this crate. Programmatic use is
through the Rust library interface alone.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `ropey` and must define the cargo features
  `cr_lines` (lone CR recognized as a line break), `unicode_lines`
  (implies `cr_lines`; full Unicode line-break set as listed in Line
  Semantics), and `simd` (performance only, no observable behavior), with
  `unicode_lines` and `simd` enabled by default. The assessment suite
  depends on the crate as `ropey = { version = "*" }` with default
  features.
- The `smallvec` crate and the `str_indices` crate (flat-string index
  conversion primitives, including its line-break tables) are available;
  the rope structure, chunk management, editing, views, iterators, and
  error taxonomy are the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the crate through its public interface only.
Dimensions covered:

- Construction equivalence: `from_str`, `From`/`FromIterator` conversions,
  `RopeBuilder` with varied piece sizes, and `from_reader`, all yielding
  content-equal ropes.
- Metrics and conversions across all four unit systems, including
  one-past-the-end positions, interior-byte resolution, surrogate-pair
  offsets, and the clamping `str_utils` helpers.
- Element, line, and chunk accessors, including tuple start-coordinates
  and boundary indices.
- Editing sequences (insert/remove/split_off/append) checked against
  slice-based reassembly and clone independence.
- Slicing in both unit systems, nested slicing, `as_str` contiguity,
  and conversions out of slices.
- Iterator families in both directions, positioned starts, reversal
  semantics, and exact-size behavior.
- Line partition rules across the full recognized line-break set,
  including CRLF as a single break.
- Cross-type equality, ordering, and hash agreement.
- Failure paths through `try_`/`get_` twins and `Error` variant identity,
  payloads, and `Display`/`Debug` rendering.

Scoring runs the suite against the delivered crate with cargo-nextest;
each test either passes or fails, and no partial credit is awarded within
a test.
