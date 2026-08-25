<!-- INTERNAL
task_id: textwrap-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: docs.rs/textwrap 0.16.2 (crate root guide; options, wrap, fill, refill, indentation, columns, line_ending, core, word_splitters, wrap_algorithms module and item docs), README at pinned commit; reference behavior observed by running the pinned checkout
-->

# Text Wrapping Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`textwrap` is a Rust library for wrapping, filling, and indenting monospace
text. It breaks paragraphs into lines that fit a target display width,
measured in terminal columns rather than bytes or characters, and it exposes
the machinery it is built from: a word-finding stage, a word-splitting
stage, an overlong-word breaking stage, and two line-breaking algorithms — a
greedy first-fit pass and an optimal-fit pass that minimizes a penalty
function over the whole paragraph. Configuration lives in a single `Options`
value covering width, indentation prefixes, line endings, word breaking, and
pluggable separator, splitter, and algorithm stages.

Around the core wrapping engine the crate provides utilities that operate on
already-formatted text: filling a paragraph into a single newline-joined
string, un-filling wrapped text back into one line while inferring its
indentation prefixes and line ending, re-filling wrapped text to a new
width, adding and removing indentation, and laying wrapped text out in
multiple columns. All stages of the engine are public, so callers must be
able to run the pipeline manually — find words, split them, break them,
choose line breaks — and get the same answer the high-level functions give.

## Non-Goals

- This specification does not require dictionary-based hyphenation: no
  language-specific hyphenation patterns, no splitter variant backed by
  hyphenation dictionaries, and no handling of soft-hyphen characters
  (U+00AD).
- This specification does not require terminal integration: no detection of
  the current terminal width and no function returning it.
- This specification does not require cargo feature gates. Every behavior
  described here must be available unconditionally when the crate is
  compiled with its default configuration.
- This specification does not require normalizing carriage returns in input
  text: input lines are delimited by `\n` alone, and a `\r` byte in the
  input is ordinary text content.
- This specification does not require a command-line interface.
- This specification does not define wrapping behavior for bidirectional
  text or for East Asian context-sensitive width tailoring beyond the
  display-width rules stated below.

## Representative Workflows

**Filling a paragraph with a hanging indent.** The caller builds an
`Options` value, sets the width and the two indentation prefixes, and fills
a paragraph. The first output line carries the initial indent, every other
output line carries the subsequent indent, and both prefixes count toward
the width:

```rust
use textwrap::{fill, Options};

let opts = Options::new(28)
    .initial_indent("* ")
    .subsequent_indent("  ");
let filled = fill("the quick brown fox jumps over the lazy dog", &opts);
// Every line starts with "* " or "  " and is at most 28 columns wide.
assert!(filled.lines().all(|l| l.starts_with("* ") || l.starts_with("  ")));
```

**Re-flowing a quoted block to a new width.** `unfill` recovers the
underlying single line of text from wrapped input, inferring the `"> "`
prefix and the line ending; `refill` composes `unfill` with `fill` so the
prefix survives the width change:

```rust
use textwrap::refill;

let quoted = "> one two\n> three four\n> five\n";
let wider = refill(quoted, 40);
assert_eq!(wider, "> one two three four five\n");
```

**Running the pipeline by hand.** The stages the high-level functions
compose are public. The caller finds words with a `WordSeparator`, splits
them at hyphens with a `WordSplitter`, breaks overlong words with
`break_words`, and picks line breaks with `wrap_first_fit` or
`wrap_optimal_fit`:

```rust
use textwrap::core::break_words;
use textwrap::word_splitters::{split_words, WordSplitter};
use textwrap::wrap_algorithms::wrap_first_fit;
use textwrap::WordSeparator;

let words = WordSeparator::AsciiSpace.find_words("porcelain tea-kettle handle");
let split = split_words(words, &WordSplitter::HyphenSplitter);
let broken = break_words(split, 9);
let lines = wrap_first_fit(&broken, &[9.0]);
// Each element of `lines` is a slice of fragments forming one line.
assert!(lines.len() >= 3);
```

## Wrapping and Filling

This section defines the three entry points that turn a paragraph into
lines: `wrap`, which returns the lines; `fill`, which joins them; and
`fill_inplace`, a restricted allocation-free variant.

**The wrap function.** `wrap` accepts the text to wrap and a width-or-options
argument, and returns the wrapped lines as a `Vec<Cow<'_, str>>`. The second
argument accepts a plain `usize` width, an owned `Options`, or a borrowed
`&Options`; a plain width is equivalent to `Options::new(width)` with every
other setting at its default. The input is split into lines on `\n`
characters only, and each input line is wrapped independently; an input line
that produces multiple output lines contributes them in order. A `\r`
character is not treated as a line delimiter and passes through as word
content. Line-ending configuration has no effect on `wrap` output: returned
lines never contain the line-ending string.

**Whitespace discipline.** When an input line is wrapped, leading whitespace
of the input line is preserved at the start of its first output line.
Whitespace between two words that end up on the same output line is
preserved exactly. Whitespace falling at a line break is dropped, so no
output line carries trailing whitespace that resulted from wrapping. An
empty input line yields an empty output line, preserving paragraph breaks;
wrapping the empty string returns a vector containing one empty line.

**Indentation prefixes.** The `initial_indent` prefix is prepended to the
first output line of the whole call; the `subsequent_indent` prefix is
prepended to every other output line, including output lines produced by
later input lines and including otherwise-empty output lines. Prefixes are
prepended verbatim — `wrap` performs no trimming of an indent applied to an
empty line. The display width of the prefix counts toward the line width, so
the room available for text on a line is the configured width minus the
width of that line's indent.

**Borrowing.** An output line that consists purely of a contiguous slice of
the input text — no indent prefix was added — must be a borrowed `Cow`
pointing into the input; a line that carries a non-empty indent prefix is
owned.

**Overlong words.** When a single fragment is wider than the room available
on a line, behavior follows the `break_words` setting. While `break_words`
is true (the default), the fragment is broken into pieces at character
boundaries so that each piece fits; a piece always contains at least one
character, so when the width is smaller than one character's display width
the output lines each hold one character and exceed the width. While
`break_words` is false, the fragment is placed on a line of its own and the
line overflows the width.

**The fill function.** `fill` accepts the same arguments as `wrap` and
returns a single `String`: the wrapped lines joined with the configured line
ending (`\n` by default, `\r\n` when the options carry `LineEnding::CRLF`).
Empty input lines survive as empty output lines, so paragraph separation is
preserved.

**In-place filling.** `fill_inplace` accepts a mutable `String` and a plain
`usize` width, and rewrites the string in place by replacing a whitespace
character with `\n` at each chosen break point. It is deliberately
restricted: words are found by splitting on runs of ASCII space characters,
line breaks are chosen greedily (first-fit), overlong words are never
broken, and no indentation is applied. At each break falling on a run of
spaces, only the last space of the run is replaced with `\n`, so earlier
spaces of the run remain as trailing whitespace on the line before the
break. The function returns nothing; the modification is the result.

## Wrapping Configuration

This section defines the `Options` value that carries every wrapping
setting, and the `LineEnding` type.

**Construction and defaults.** `Options::new` accepts the target line width
in display columns and produces a configuration with: line ending
`LineEnding::LF`; empty initial and subsequent indents; `break_words` set to
true; word separator `WordSeparator::UnicodeBreakProperties`; wrap algorithm
`WrapAlgorithm::OptimalFit` carrying default penalties; and word splitter
`WordSplitter::HyphenSplitter`. `Options` is a struct with public fields
`width` (usize), `line_ending`, `initial_indent` (string slice),
`subsequent_indent` (string slice), `break_words` (bool), `wrap_algorithm`,
`word_separator`, and `word_splitter`; callers must be able to both read and
assign the fields directly and to use the chained builder methods
`line_ending`, `width`, `initial_indent`, `subsequent_indent`,
`break_words`, `word_separator`, `wrap_algorithm`, and `word_splitter`, each
of which consumes the options value, replaces one setting, and returns it.

**Conversions.** A `usize` converts into an `Options` via `From`, equivalent
to `Options::new(width)`. A `&Options` converts into an owned `Options` by
copying every setting. The width-or-options parameters of `wrap`, `fill`,
`refill`, and `wrap_columns` accept anything convertible into `Options`.

**Line endings.** `LineEnding` is an enum with variants `LF` and `CRLF`. Its
`as_str` method returns `"\n"` for `LF` and `"\r\n"` for `CRLF`. The
configured line ending controls only how `fill` (and functions built on it)
join output lines; it does not affect how input text is divided into lines.

**Width semantics.** All widths are display widths measured in terminal
columns as defined by `display_width` below, not byte counts and not
character counts. A width of zero is legal: every word then lands on its own
line, and word pieces of one character are emitted when `break_words` is
true.

## Refilling and Indentation

This section defines the inverse operations on already-wrapped text and the
line-prefix utilities.

**Unfilling.** `unfill` accepts a string holding one wrapped paragraph and
returns a pair of the recovered single-line text and an `Options` value
describing what it inferred. Inference works as follows. The recognized
prefix of each line is its longest leading run of the characters space,
`-`, `+`, `*`, `>`, `#`, and `/`. The prefix of the first line is reported
as `initial_indent`; the longest common prefix of all remaining lines is
reported as `subsequent_indent`. The reported `width` is the largest display
width among the input lines, measured before prefix removal. The recovered
text is built by stripping each line's reported prefix and joining the lines
with single spaces; whitespace inside a line is preserved exactly. When
every line ending in the input is `\r\n`, the reported line ending is
`CRLF`; when line endings are absent or mixed, it is `LF`. When the input
ends with the detected line ending, the recovered text keeps one trailing
copy of it.

**Refilling.** `refill` accepts wrapped text and a width-or-options argument
and returns the text re-wrapped at the new width. It must behave as: unfill
the input; carry the inferred `initial_indent` and `subsequent_indent` into
the caller's options (all other caller settings win, including the line
ending); fill the recovered text with those options. When the input ended
with a line ending, the output ends with the caller's configured line
ending; converting between `LF` and `CRLF` is therefore a supported use.

**Indenting.** `indent` accepts text and a prefix string and returns a new
string with the prefix added to lines. A line containing a non-whitespace
character receives the full prefix. A line that is empty or contains only
whitespace receives the prefix with its trailing whitespace trimmed, so
indenting with a prefix like `"# "` turns an empty line into `"#"` rather
than `"# "`, and indenting with a whitespace-only prefix leaves empty lines
empty. Existing content of every line, including leading and trailing
whitespace, is kept unchanged after the prefix. A trailing newline on the
input is preserved; no trailing newline is invented.

**Dedenting.** `dedent` accepts text and returns it with the longest common
leading whitespace prefix removed from every line. The common prefix is
computed over lines that contain at least one non-whitespace character;
whitespace-only lines neither contribute to nor constrain the prefix, and
each whitespace-only line is replaced by an empty line in the output. A
trailing newline on the input is preserved.

## Column Layout

This section defines multi-column layout of wrapped text.

**The wrap_columns function.** `wrap_columns` accepts the text, the number
of columns, a width-or-options argument giving the total layout width, and
three gap strings placed before the first column (`left_gap`), between
adjacent columns (`middle_gap`), and after the last column (`right_gap`). It
returns the assembled rows as a `Vec<String>`. If the column count is zero,
the call must panic.

**Layout algorithm as contract.** The inner width is the configured width
minus the display widths of the left gap, the right gap, and the middle gap
times one less than the column count, saturating at zero. The per-column
width is the inner width divided by the column count, and at least 1. The
text is wrapped with the caller's options except that the width is replaced
by the per-column width. The wrapped lines are then distributed column-major:
with `n` wrapped lines and `c` columns, each column holds `ceil(n / c)`
consecutive lines, the first column taking the first block. Every cell is
padded with spaces to the per-column width; cells past the end of the
wrapped lines are all spaces. Any remainder of the inner width not divisible
by the per-column width is appended as extra spaces at the end of the last
column, before the right gap. Every returned row therefore has the same
display width. Wrapping the empty string yields one all-blank row.

## Words, Fragments, and Measurement

This section defines the public text model underneath the wrapping engine:
display-width measurement, the fragment abstraction, the concrete word type,
word finding, word splitting, and overlong-word breaking. The high-level
functions must be consistent with these pieces (see Cross-View Invariants).

**Display width.** `display_width` in the `core` module accepts a string
slice and returns its width in terminal columns. Emoji and CJK characters
count as two columns; combining marks in decomposed form count as zero, so a
base letter plus combining accent measures one column. ANSI escape sequences
contribute zero width: a CSI sequence (introduced by ESC `[`) is skipped
through its final byte in the range `@` to `~`, and an OSC sequence
(introduced by ESC `]`) is skipped through the string terminator ESC `\` or
a BEL character.

**The fragment abstraction.** `Fragment` in the `core` module is a trait for
units that line-breaking arranges. It requires three methods returning
`f64`: `width`, the displayed width of the fragment's content;
`whitespace_width`, the width of the whitespace that follows the fragment
when it is not last on its line; and `penalty_width`, the width of the
penalty text inserted when the fragment is last on its line. The
line-breaking algorithms are generic over any `Fragment` implementor.

**Words.** `Word` in the `core` module is the concrete fragment used by the
crate: a copyable, equality-comparable struct with public string-slice
fields `word` (the content), `whitespace` (the whitespace to render after
the word when mid-line), and `penalty` (the text to render when the word
ends a line, empty for an unhyphenated word). A `Word` dereferences to its
`word` content as a string slice. `Word::from` accepts a string slice and
splits it into content and trailing whitespace: the content is everything up
to the trailing whitespace run, the whitespace field holds that run, and the
penalty is empty. `Word` implements `Fragment` with widths measured by
`display_width`. The `break_apart` method accepts a line width and returns
an iterator of `Word` pieces, each at most that many columns wide (always at
least one character), all with empty whitespace and penalty except that the
final piece keeps the original word's whitespace and penalty.

**Finding words.** `WordSeparator` is an enum reachable at the crate root
with variants `AsciiSpace`, `UnicodeBreakProperties`, and
`Custom(fn(&str) -> Box<dyn Iterator<Item = Word<'_>> + '_>)`. Its
`find_words` method accepts one line of text and returns a boxed iterator of
`Word` values. `AsciiSpace` splits on runs of ASCII space characters: each
word carries the run of spaces that follows it in its `whitespace` field,
and characters such as `\t` or `\r` are word content, not separators.
`UnicodeBreakProperties` finds break opportunities according to the Unicode
line-breaking algorithm, so it additionally yields breaks between characters
with no intervening whitespace — for example each emoji or CJK ideograph in
a run becomes its own word — with two divergences from the raw algorithm:
no break is produced at a hyphen-minus (hyphen breaking belongs to the word
splitter), and a word-joiner character (U+2060) suppresses the break it
covers. `Custom` delegates to the wrapped function. Named variants of the
enum compare equal to themselves; `Custom` values never compare equal.

**Splitting words.** `WordSplitter` is an enum defined in the
`word_splitters` module and re-exported at the crate root, with variants
`NoHyphenation`, `HyphenSplitter`, and `Custom(fn(&str) -> Vec<usize>)`. Its
`split_points` method accepts a word and returns the byte offsets at which
the word is allowed to break, in ascending order. `NoHyphenation` returns no
offsets for any word. `HyphenSplitter` returns the offset immediately after
each `-` character that has an alphanumeric character both before and after
it, so leading or doubled hyphens produce no split points. `Custom`
delegates to the wrapped function. Named variants compare equal to
themselves; `Custom` values never compare equal. The free function
`split_words` in the same module accepts an iterator of `Word` values and a
`&WordSplitter` reference and returns an iterator of `Word` values in which
every input word is replaced by its pieces at the split points; each
non-final piece receives a `"-"` penalty unless it already ends with `-`,
and the final piece keeps the original whitespace and penalty.

**Breaking overlong words.** `break_words` in the `core` module accepts an
iterator of `Word` values and a line width, and returns a `Vec<Word>` in
which every word wider than the line width is replaced by the pieces of its
`break_apart`; words that fit pass through unchanged.

## Line-Breaking Algorithms and the Penalty Model

This section defines the two line-breaking strategies and the algorithm
selector stored in the options.

**The selector.** `WrapAlgorithm` is an enum defined in the
`wrap_algorithms` module and re-exported at the crate root, with variants
`FirstFit`, `OptimalFit(Penalties)`, and a `Custom` variant carrying a
function from a word slice and usize line widths to line assignments. The
constructor `WrapAlgorithm::new` returns the optimal-fit variant with
default penalties, and `WrapAlgorithm::new_optimal_fit` returns the same;
`FirstFit` and `OptimalFit` values compare equal to structurally equal
values, and `Custom` values never compare equal. The `wrap` method accepts a
slice of `Word` values and a slice of `usize` line widths, and returns the
lines as a vector of sub-slices of the input; the first width applies to the
first line and so on, with the last width repeated for all remaining lines —
this is the hook by which the high-level `wrap` implements indentation of
differing widths.

**Line width slices.** The two free algorithm functions accept the fragment
slice and a `&[f64]` of line widths with the same repeat-the-last-element
rule. Both return the chosen lines as consecutive sub-slices of the fragment
slice, in order, covering every fragment exactly once.

**First-fit.** `wrap_first_fit` in the `wrap_algorithms` module is the
greedy single-pass strategy: fragments are appended to the current line
while the line's accumulated width — each fragment's width plus its
whitespace width when further fragments follow on that line, plus the final
fragment's penalty width — stays within the target; otherwise a new line
begins. A fragment wider than the target occupies a line alone. The function
is generic over `Fragment`, so callers must be able to run it on their own
fragment types.

**Optimal-fit.** `wrap_optimal_fit` in the `wrap_algorithms` module accepts
the fragment slice, the line-width slice, and a `&Penalties` value, and
returns `Result<Vec<&[T]>, OverflowError>`. It chooses the line breaks that
minimize the total cost over the whole paragraph, where the cost is the sum
of: the squared gap between the target width and the line's width, for every
line except the last; `nline_penalty` for every line after the first;
`overflow_penalty` per column of overflow for a line wider than the target;
`short_last_line_penalty` when the final line holds a single word narrower
than the target width divided by `short_last_line_fraction`; and
`hyphen_penalty` for every line ending in a `-`. Because gap costs are
squared, the optimal-fit layout evens out line lengths where the greedy pass
would leave one very short line. If the cost computation overflows — as with
non-finite or absurdly large widths and multiple fragments — the function
returns the error instead of panicking.

**Penalties.** `Penalties` is a copyable, equality-comparable struct in the
`wrap_algorithms` module with public `usize` fields `nline_penalty`,
`overflow_penalty`, `short_last_line_fraction`, `short_last_line_penalty`,
and `hyphen_penalty`. `Penalties::new` and the `Default` implementation
produce the tuning used by default options: `nline_penalty` 1000,
`overflow_penalty` 2500, `short_last_line_fraction` 4,
`short_last_line_penalty` 25, `hyphen_penalty` 25. Setting
`short_last_line_penalty` to zero disables the short-last-line adjustment;
raising `short_last_line_fraction` narrows what counts as short. With
default penalties, a one-column overflow (cost 2500) ties a 50-column gap
(cost 2500) and the tie is broken toward fewer lines by `nline_penalty`.

**OverflowError.** `OverflowError` is a unit struct in the
`wrap_algorithms` module that is debug-printable, equality-comparable, and
implements the standard error and display traits.

## State Model

The library is a pure function family over one configuration value: an
`Options` is the single fact source, and every public entry point is a
projection of the same pipeline run against it. The pipeline for one input
line is: the `word_separator` turns the line into `Word` fragments; the
`word_splitter` refines each word at its split points via `split_words`;
when `break_words` is true, fragments wider than the available room are
broken via `break_words`; the `wrap_algorithm` chooses line breaks over the
fragment sequence, given per-line widths equal to the configured width minus
each line's indent width; the chosen fragments are re-joined with their
inter-fragment whitespace, trailing break whitespace is dropped, and indent
prefixes are attached.

Public projections of that one run: `wrap` returns the lines;
`fill` joins them with the line ending; `fill_inplace` is a restricted
first-fit/ASCII-space projection writing into the input buffer; `refill`
composes `unfill` with `fill`; `wrap_columns` re-targets the width to a
computed column width and arranges the lines column-major. The stages
themselves (`find_words`, `split_points`, `split_words`, `break_apart`,
`break_words`, `wrap_first_fit`, `wrap_optimal_fit`, the `WrapAlgorithm`
selector) are public and must agree with the high-level projections. There
is no hidden mutable state anywhere: every function is deterministic in its
arguments.

## Error Semantics

The API is total almost everywhere: wrapping, filling, refilling,
indentation, and measurement never fail on any string input. The failure
surface is confined to the following.

| Condition | Outcome |
|---|---|
| `wrap_columns` called with a column count of zero | panic |
| `wrap_optimal_fit` cost computation overflows (non-finite or enormous widths/fragments) | returns `Err(OverflowError)` |
| `Word::break_apart` or `break_words` with a width smaller than one character | pieces of one character are produced; no error |
| Width of zero passed to `wrap`/`fill` | every word on its own line; no error |

`OverflowError` implements the standard error trait and `Display`;
`wrap_optimal_fit` is the only fallible function in the crate.

## Cross-View Invariants

1. For every text and options value, `fill(text, opts)` must equal the
   lines returned by `wrap(text, opts)` joined with
   `opts.line_ending.as_str()`.
2. For every text and width, `wrap` configured with
   `WrapAlgorithm::FirstFit`, `WordSeparator::AsciiSpace`, and
   `WordSplitter::NoHyphenation` must place words on the same lines as the
   manual pipeline — `find_words`, then `break_words` at the width, then
   `wrap_first_fit` with that width — applied to the same input line.
3. For a single-paragraph text whose words are separated by single spaces
   and start with non-prefix characters, `unfill(fill(text, w))` must
   return the original text, and `refill(fill(text, w1), w2)` must equal
   `fill(text, w2)`.
4. For a single-paragraph text and a prefix `p`, `fill` with both
   `initial_indent` and `subsequent_indent` set to `p` at width `w` must
   equal `indent(fill(text, w - display_width(p)), p)`.
5. For text whose lines each either are empty or start with a
   non-whitespace character, `dedent(indent(text, pad))` must equal the
   text for any whitespace-only `pad`.
6. Every row returned by one `wrap_columns` call must have the same
   display width, and each row must contain the left gap at its start and
   the right gap at its end.
7. When `break_words` is true, both indents are empty, and the width is at
   least the display width of the widest character in the text, every line
   returned by `wrap` must satisfy `display_width(line) <= width`.
8. `Options::new(w)` converted from the plain width `w` (via `From<usize>`)
   and built by the constructor must behave identically in every projection,
   and a `&Options` argument must wrap identically to its owned copy.

## Public Interface

### Import Surface

```rust
// crate root
use textwrap::{dedent, fill, fill_inplace, indent, refill, unfill, wrap, wrap_columns};
use textwrap::{LineEnding, Options, WordSeparator, WordSplitter, WrapAlgorithm};

// core text model
use textwrap::core::{break_words, display_width, Fragment, Word};

// word splitting (WordSplitter is defined here and re-exported at the root)
use textwrap::word_splitters::{split_words, WordSplitter as WsAlias};

// line-breaking algorithms (WrapAlgorithm is defined here and re-exported at the root)
use textwrap::wrap_algorithms::{wrap_first_fit, wrap_optimal_fit, OverflowError, Penalties, WrapAlgorithm as WaAlias};
```

`WordSeparator` is reachable only at the crate root. `WordSplitter` and
`WrapAlgorithm` are reachable both at the crate root and in their defining
modules. The `core`, `word_splitters`, and `wrap_algorithms` modules are the
only public modules.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `wrap` | function | wrap text into a vector of lines |
| `fill` | function | wrap text and join lines with the line ending |
| `fill_inplace` | function | greedy in-place fill of a mutable string |
| `refill` | function | re-wrap already-wrapped text at a new width |
| `unfill` | function | recover single-line text and inferred options from wrapped text |
| `indent` | function | add a prefix to every line |
| `dedent` | function | remove the common leading whitespace of all lines |
| `wrap_columns` | function | lay wrapped text out in columns between gap strings |
| `Options` | struct | wrapping configuration: width, indents, line ending, stages |
| `LineEnding` | enum | output line ending: `LF` or `CRLF` |
| `WordSeparator` | enum | word-finding stage: ASCII spaces, Unicode breaks, or custom |
| `WordSplitter` | enum | word-splitting stage: none, hyphens, or custom |
| `WrapAlgorithm` | enum | line-breaking stage: first-fit, optimal-fit, or custom |
| `core::display_width` | function | terminal-column width of a string, skipping ANSI sequences |
| `core::Fragment` | trait | width/whitespace/penalty measurement of a wrappable unit |
| `core::Word` | struct | concrete fragment: content, trailing whitespace, penalty |
| `core::break_words` | function | break fragments wider than the line width into pieces |
| `word_splitters::split_words` | function | apply a splitter across an iterator of words |
| `wrap_algorithms::wrap_first_fit` | function | greedy line breaking over fragments |
| `wrap_algorithms::wrap_optimal_fit` | function | penalty-minimizing line breaking over fragments |
| `wrap_algorithms::Penalties` | struct | tuning knobs of the optimal-fit cost model |
| `wrap_algorithms::OverflowError` | struct | cost-overflow error of optimal-fit |

### CLI Entry Points

There is no console script for this package. Programmatic use is through
the Rust crate API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `textwrap`; the assessment suite depends on the
  crate as `textwrap = { version = "*" }` with its default configuration.
- The `unicode-linebreak` crate (Unicode line-breaking properties), the
  `unicode-width` crate (terminal display widths), and the `smawk` crate
  (matrix column-minima searching) are available as dependencies; the
  wrapping engine — options plumbing, fragment pipeline, whitespace and
  indent discipline, first-fit and optimal-fit strategies with the penalty
  model, refill/unfill inference, indentation utilities, and column layout —
  is the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Wrapping and filling: width discipline in display columns, whitespace
  preservation and dropping rules, indentation prefixes, `break_words` on
  and off, `Cow` borrowing, empty-line and empty-string handling, LF-only
  input splitting, `fill_inplace` restrictions.
- Configuration: `Options` defaults, builder methods and public field
  access, conversions from widths and references, `LineEnding` joining.
- Refilling and indentation: prefix inference of `unfill` (character set,
  first vs. common prefix, width and line-ending report), `refill`
  composition and line-ending conversion, `indent` trimmed-prefix rule on
  blank lines, `dedent` common-prefix computation.
- Column layout: column width arithmetic, column-major distribution,
  padding, gap placement, zero-column panic.
- Text model: `display_width` (double-width characters, combining marks,
  ANSI skipping), `Word` construction, deref and `break_apart`,
  `WordSeparator` variants and their divergences, `WordSplitter` split
  points, `split_words` penalties, `break_words`.
- Algorithms: first-fit greediness vs. optimal-fit evening, the penalty
  model's documented tuning effects, line-width slices with hanging
  indents, `Fragment` genericity, `OverflowError`.
- Cross-view consistency: the invariants listed above, exercised jointly
  across wrapping, refilling, indentation, columns, and the manual
  pipeline.

Scoring runs the suite against the delivered crate; each test either passes
or fails, and the score is the fraction passed. Tests use fresh fixture
text; memorized outputs from any similarly-named library will not match.
