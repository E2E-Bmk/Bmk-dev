<!-- INTERNAL
task_id: similar-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: docs.rs/similar 2.7.0 (crate root docs, algorithms/udiff/utils module docs, public item docs), README.md at tag 2.7.0; reference behavior observed by running the pinned checkout
-->

# Text Diffing Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`similar` is a Rust diffing library that computes the differences between two
sequences and serves that result through several coordinated projections: raw
operation streams, per-item change iterators, clustered change groups, unified
diff text, similarity ratios, close-match ranking, and inline word-level
emphasis within line diffs.

The library is split into a low-level and a high-level half. The low level is
a generic algorithm layer: three interchangeable diff algorithms (Myers,
Patience, and LCS) walk two indexable sequences and report edit segments to a
caller-supplied hook, and composable hook adapters capture, merge, and clean
up those segments into a vector of operations. The high level is a text layer:
a text differ tokenizes two strings (into lines, words, characters, Unicode
words, or grapheme clusters), runs the algorithm layer over the tokens, and
exposes the captured operations together with text-aware conveniences such as
unified diff formatting and trailing-newline tracking. A utilities layer maps
tokenized results back onto the original input strings so callers receive
maximal connected slices instead of token fragments.

The installable crate name is `similar`. The crate compiles without any
mandatory dependency; the `unicode` cargo feature adds Unicode-aware
tokenization backed by a segmentation crate.

## Non-Goals

- This specification does not require byte-slice (`[u8]`) diffing support or
  a `bytes` cargo feature; only `str`-based text diffing is in scope.
- This specification does not require serde serialization or deserialization
  for any type.
- This specification does not require WebAssembly timer support or a
  `wasm32_web_time` cargo feature.
- This specification does not define the exact `Debug` output of any type.
- This specification does not define the exact segment boundaries the inline
  emphasis pass produces inside a replaced line group, nor the similarity
  threshold below which the pass falls back to unemphasized output; the
  guarantees in Inline Change Emphasis are the complete inline contract.
- This specification does not define the quality of the approximation
  produced when a deadline expires, beyond the correctness invariant that the
  reported operations remain a valid edit script.
- This specification does not define performance characteristics.

## Representative Workflows

**Rendering a line diff with change signs.** The text differ tokenizes both
inputs into lines and exposes one change per line:

```rust
use similar::{ChangeTag, TextDiff};

let diff = TextDiff::from_lines(
    "Hello World\nThis is the second line.\nThis is the third.",
    "Hallo Welt\nThis is the second line.\nThis is life.\nMoar and more",
);

for change in diff.iter_all_changes() {
    let sign = match change.tag() {
        ChangeTag::Delete => "-",
        ChangeTag::Insert => "+",
        ChangeTag::Equal => " ",
    };
    print!("{}{}", sign, change);
}
```

Each `Change` prints its text and supplies a virtual trailing newline when the
underlying line does not end in one, so the output is always line-shaped.

**Producing a unified diff.** The same diff object renders unified diff text
with configurable context and file header:

```rust
use similar::TextDiff;

let diff = TextDiff::from_lines("a\nb\nc\n", "a\nB\nc\n");
let udiff = diff
    .unified_diff()
    .context_radius(3)
    .header("old_file", "new_file")
    .to_string();
assert!(udiff.starts_with("--- old_file\n+++ new_file\n@@"));
```

**Capturing raw operations from the algorithm layer.** The generic layer works
on any indexable sequence and reports to a hook; stacking `Replace` over
`Capture` merges paired deletions and insertions into replacements:

```rust
use similar::algorithms::{Algorithm, Capture, Replace, diff_slices};

let a = vec![1, 2, 3, 4, 5];
let b = vec![1, 2, 3, 4, 7];
let mut d = Replace::new(Capture::new());
diff_slices(Algorithm::Myers, &mut d, &a, &b).unwrap();
let ops = d.into_inner().into_ops();
```

The same result is available in one call as
`similar::capture_diff_slices(Algorithm::Myers, &a, &b)`, which additionally
applies semantic cleanup to the operation stream.

**Word diff remapped onto the original strings.** Token-level diffs are
remapped to maximal slices of the original inputs:

```rust
use similar::{Algorithm, ChangeTag};
use similar::utils::diff_words;

assert_eq!(diff_words(Algorithm::Myers, "foo bar baz", "foo bor baz"), vec![
    (ChangeTag::Equal, "foo "),
    (ChangeTag::Delete, "bar"),
    (ChangeTag::Insert, "bor"),
    (ChangeTag::Equal, " baz"),
]);
```

## Diff Algorithms and the Hook Protocol

This section defines the generic algorithm layer in `similar::algorithms`:
how algorithms report edit segments to hooks and how hook adapters compose.

**Algorithm selection.** The `Algorithm` enum has three variants: `Myers`,
`Patience`, and `Lcs`. `Algorithm` implements `Default`, and the default value
must be `Algorithm::Myers`. The enum supports equality comparison, hashing,
ordering, cloning, and copying. `Algorithm` is exported both at the crate root
and from `similar::algorithms`.

**The DiffHook trait.** A `DiffHook` receives the edit script as index-based
callbacks. The trait declares an associated `Error` type and five methods,
all returning a `Result` with that error type:

- `equal` receives `old_index`, `new_index`, and `len` when a section of
  `len` items starting at those indices is equal in both sequences.
- `delete` receives `old_index`, `old_len`, and `new_index` when a section of
  the old sequence must be removed; `new_index` is the position in the new
  sequence where the removal is anchored.
- `insert` receives `old_index`, `new_index`, and `new_len` when a section of
  the new sequence must be inserted; `old_index` is the position in the old
  sequence where the insertion is anchored.
- `replace` receives `old_index`, `old_len`, `new_index`, and `new_len` when
  an old section is replaced by a new section. The trait's default `replace`
  implementation must forward to `delete` followed by `insert` with the
  corresponding arguments.
- `finish` is called exactly once after the algorithm completes. The default
  implementations of `equal`, `delete`, `insert`, and `finish` do nothing and
  return `Ok(())`.

The trait is implemented for `&mut D` where `D` is a hook, forwarding every
method, so hooks compose by mutable reference.

**Running an algorithm.** The function `diff` in `similar::algorithms` takes
an `Algorithm`, a mutable hook reference, the old sequence with an index range
`old_range`, and the new sequence with an index range `new_range`; it walks
the two ranges and drives the hook. `diff_deadline` behaves identically and
additionally accepts an optional deadline instant; when the deadline passes
mid-run, the algorithm must stop refining and report an approximate but valid
edit script. `diff_slices` and `diff_slices_deadline` are shortcuts that diff
two full slices. The submodules `similar::algorithms::myers`,
`similar::algorithms::patience`, and `similar::algorithms::lcs` each export
`diff` and `diff_deadline` entry points for one specific algorithm, with the
same hook protocol. When any hook callback returns an error, the run must
abort and return that error unchanged; otherwise the run returns `Ok(())`
after `finish` succeeds.

**Edit script guarantees.** Every algorithm run must report a complete,
ordered, non-overlapping edit script: segment indices are non-decreasing
across callbacks, `equal` is only reported for item ranges that compare equal
pairwise, and applying the script — keeping equal sections, dropping deleted
sections, and splicing inserted sections — must transform the old range
exactly into the new range. `finish` must be called exactly once per run,
including runs over empty ranges and runs where both ranges are identical.
The Myers and LCS algorithms must produce a shortest edit script (a script
minimizing the total number of deleted plus inserted items) when no deadline
interrupts them. The Patience algorithm anchors the script on lines that are
unique in both inputs and recurses between anchors; its scripts are correct
but not required to be minimal.

**Capture.** `Capture` is a hook that records the reported segments as
`DiffOp` values in callback order. `Capture::new` creates an empty recorder;
`ops` returns the recorded operations as a slice; `into_ops` consumes the
recorder and returns the vector; `into_grouped_ops` consumes the recorder and
returns the operations grouped exactly as `group_diff_ops` would group them
with the given context size. `Capture`'s error type is infallible.

**Replace.** `Replace` wraps another hook and rewrites the segment stream so
the wrapped hook never observes a deletion immediately followed by an
insertion at the same position: such adjacent pairs must be merged into one
`replace` callback. All other segments are forwarded unchanged in order.
`Replace::new` wraps a hook and `into_inner` unwraps it; the wrapper forwards
the inner error type.

**Compact.** `Compact` wraps another hook together with references to the old
and new sequences and performs semantic cleanup on the finished segment
stream before forwarding it: adjacent compatible segments are merged, and
change hunks are shifted over equal runs where item values allow, so that
hunks connect where possible. Cleanup happens when `finish` is called; the
cleaned stream is then replayed into the inner hook followed by the inner
hook's `finish`. `Compact::new` takes the inner hook and the two sequences;
`into_inner` returns the inner hook. The cleaned stream must satisfy the same
edit script guarantees and reconstruct the same new sequence as the original
stream.

**NoFinishHook.** `NoFinishHook` wraps another hook, forwards `equal`,
`delete`, `insert`, and `replace`, and swallows `finish` without forwarding
it. It is constructed with `new` and unwrapped with `into_inner`. It exists
so one inner hook survives across multiple algorithm runs.

**IdentifyDistinct.** `IdentifyDistinct` converts two indexable sequences
into compact integer token sequences that diff identically to the originals.
Its constructor takes the old sequence with a range and the new sequence with
a range; the type parameter selects the integer width. The accessors
`old_lookup` and `new_lookup` return indexable token sequences, and
`old_range` and `new_range` return the corresponding index ranges, suitable
for passing directly to the `diff` functions. Equal items map to equal
tokens and distinct items map to distinct tokens, so an algorithm run over
the token sequences must report the same segment structure as a run over the
original sequences.

## Captured Operation Streams

This section defines the operation vocabulary shared by every projection:
the `DiffOp` type, its expansions into changes and slices, and the one-call
capture functions.

**The DiffOp type.** `DiffOp` is an enum with four variants describing one
segment of an edit script, each carrying named index fields:

- `Equal` with `old_index`, `new_index`, and `len`.
- `Delete` with `old_index`, `old_len`, and `new_index`.
- `Insert` with `old_index`, `new_index`, and `new_len`.
- `Replace` with `old_index`, `old_len`, `new_index`, and `new_len`.

`DiffOp` values support equality comparison, hashing, cloning, and copying.
The `DiffTag` enum names the four corresponding tags `Equal`, `Delete`,
`Insert`, and `Replace`, and supports equality, ordering, hashing, cloning,
and copying.

**Tag and range projections.** `DiffOp::tag` returns the operation's
`DiffTag`. `DiffOp::old_range` and `DiffOp::new_range` return the operation's
index ranges in the old and new sequences. `DiffOp::as_tag_tuple` returns the
tag together with both ranges, computed as: `Equal` spans `old_index..old_index+len`
and `new_index..new_index+len`; `Delete` spans `old_index..old_index+old_len`
and the empty range `new_index..new_index`; `Insert` spans the empty range
`old_index..old_index` and `new_index..new_index+new_len`; `Replace` spans
`old_index..old_index+old_len` and `new_index..new_index+new_len`.
`DiffOp::apply_to_hook` replays the operation into a `DiffHook`, invoking the
callback matching its variant.

**Expanding an op into changes.** `DiffOp::iter_changes` takes the old and
new indexable sequences and yields one `Change` per affected item: an `Equal`
op yields `Equal` changes carrying both the old and new index of each item;
a `Delete` op yields `Delete` changes carrying only old indices; an `Insert`
op yields `Insert` changes carrying only new indices; a `Replace` op yields
all its `Delete` changes first, then all its `Insert` changes. Indices in the
yielded changes increase item by item from the op's range starts. The
returned iterator type is `ChangesIter`, exported from `similar::iter`.

**Expanding an op into slices.** `DiffOp::iter_slices` takes the old and new
sequences and yields `(ChangeTag, slice)` tuples covering the op's ranges
wholesale: `Equal` yields one `Equal` tuple with the old slice, `Delete` one
`Delete` tuple with the old slice, `Insert` one `Insert` tuple with the new
slice, and `Replace` a `Delete` tuple with the old slice followed by an
`Insert` tuple with the new slice.

**One-call capture.** `capture_diff` runs the selected algorithm over two
indexable sequences with explicit ranges and returns the operations as a
vector; it must behave as the composition of semantic cleanup (`Compact`),
replace-merging (`Replace`), and recording (`Capture`) over a plain algorithm
run. `capture_diff_slices` is the slice shortcut. `capture_diff_deadline` and
`capture_diff_slices_deadline` accept an optional deadline instant and are
otherwise identical. The captured stream must satisfy: operations are ordered
with non-decreasing indices; the old ranges of `Equal`, `Delete`, and
`Replace` ops partition the old range exactly; the new ranges of `Equal`,
`Insert`, and `Replace` ops partition the new range exactly; no operation is
empty on both sides; and no `Delete` op is immediately followed by an
`Insert` op at the same position (such pairs appear as `Replace`). Two equal
inputs produce a single `Equal` op covering both, and two empty inputs
produce an empty vector.

**The Change type.** `Change` describes one expanded item. `Change::tag`
returns its `ChangeTag`; `Change::old_index` and `Change::new_index` return
optional indices (present as described above); `Change::value` returns the
underlying item by clone, `Change::value_ref` by reference, and
`Change::value_mut` by mutable reference. `Change` values support equality
comparison, hashing, cloning, and copying. The `ChangeTag` enum has the three
variants `Equal`, `Delete`, and `Insert`, supports equality, ordering,
hashing, cloning, and copying, and implements `Display` by rendering a single
character: a space for `Equal`, `-` for `Delete`, and `+` for `Insert`.

**String changes.** When the underlying value is a diffable string, `Change`
additionally provides: `as_str`, returning the value as `&str` when it is
valid UTF-8; `to_string_lossy`, returning a lossily decoded string; and
`missing_newline`, returning `true` when the value does not end in a newline
character. `Change` implements `Display` for string values by writing the
lossy value followed by a newline if and only if `missing_newline` is true.

## Grouping and Similarity

This section defines how operation streams are clustered for contextual
display and how similarity is measured and ranked.

**Grouping.** `group_diff_ops` takes an operation vector and a context size
`n` and isolates clusters of changes separated by long equal runs. Its rules:
a leading `Equal` op is trimmed so that at most its last `n` items remain; a
trailing `Equal` op is trimmed so that at most its first `n` items remain; an
interior `Equal` op longer than `2 * n` items ends the current group with an
`Equal` op holding its first `n` items and starts the next group with an
`Equal` op holding its last `n` items; all other ops pass through unchanged
into the current group. A trailing group containing nothing or only a single
`Equal` op is dropped, and an empty input produces an empty result. For an
operation stream with no changes at all, the result is therefore empty.
`TextDiff::grouped_ops` applies the same function to the text differ's own
operations.

**Similarity ratio.** `get_diff_ratio` takes an operation slice together
with the old and new sequence lengths and returns `2.0 * M / T` as `f32`,
where `M` is the total length of all `Equal` ops and `T` is the sum of both
sequence lengths. When `T` is zero the ratio must be `1.0`. A complete match
yields `1.0` and fully distinct inputs yield `0.0`. `TextDiff::ratio` must
equal `get_diff_ratio` applied to the differ's operations and token counts.

**Close matches.** `get_close_matches` takes a word, a slice of candidate
words, a maximum result count `n`, and a `cutoff` ratio. It computes the
character-level diff ratio between the word and each candidate and returns up
to `n` candidates whose ratio is at least `cutoff`, ordered from most to
least similar; candidates with equal ratios are ordered lexicographically
ascending. When no candidate reaches the cutoff the result is empty.

## Text Diffing

This section defines the string tokenization contract and the `TextDiff`
type that projects captured operations over tokenized text.

**Diffable strings.** The `DiffableStr` trait abstracts the string type the
text layer works on; this specification requires it for `str`. Its methods
define the tokenization and inspection contract:

- `tokenize_lines` splits into lines with their line endings attached. A
  `\r\n` pair is one ending, a lone `\n` is an ending, and a lone `\r` is an
  ending. A final segment without a trailing ending is its own line. The
  empty string produces no tokens.
- `tokenize_lines_and_newlines` splits into alternating runs of newline
  characters and non-newline characters, each run one token.
- `tokenize_words` splits into alternating runs of whitespace and
  non-whitespace characters, each run one token.
- `tokenize_chars` splits into single characters.
- `tokenize_unicode_words` splits at Unicode word boundaries (requires the
  `unicode` cargo feature); every boundary-delimited segment, including
  whitespace and punctuation segments, is a token.
- `tokenize_graphemes` splits into extended grapheme clusters (requires the
  `unicode` cargo feature).
- `as_str` returns the value as `&str` when valid UTF-8; `to_string_lossy`
  decodes lossily; `ends_with_newline` returns whether the value ends with
  `\r` or `\n`; `len` returns the byte length; `slice` returns a subrange;
  `as_bytes` returns the raw bytes; `is_empty` returns whether `len` is zero.

The companion trait `DiffableStrRef` resolves reference-like types to their
diffable string form via `as_diffable_str`; it is implemented for diffable
strings themselves, for `String`, and for `Cow` of a diffable string, so
owned and borrowed strings are accepted interchangeably by the text entry
points.

**Configuring a text diff.** `TextDiffConfig` is a builder created by
`TextDiff::configure` (it also implements `Default`). Its setters, each
returning the builder for chaining: `algorithm` selects the diff algorithm
(default `Algorithm::Myers`); `deadline` sets an absolute deadline instant;
`timeout` sets a relative duration converted to a deadline; and
`newline_terminated` overrides the newline termination flag described below.
Its build methods run the tokenization and diff: `diff_lines`, `diff_words`,
`diff_chars`, `diff_unicode_words` (requires `unicode`), `diff_graphemes`
(requires `unicode`), and `diff_slices`, which diffs caller-provided token
slices without tokenizing. `TextDiff` offers matching one-call constructors
`from_lines`, `from_words`, `from_chars`, `from_unicode_words`,
`from_graphemes`, and `from_slices`, each equivalent to configuring with
defaults and calling the corresponding build method.

**Newline termination.** Every text diff carries a `newline_terminated`
flag, readable through `TextDiff::newline_terminated`. When a diff is built
with `diff_lines`/`from_lines`, the flag must be `true`; every other build
method sets it to `false`; a `newline_terminated` call on the builder
overrides the automatic value. The flag controls unified diff rendering:
when it is `false` line endings are synthesized after each change, and when
it is `true` the endings already contained in the tokens are reused and
missing trailing newlines are reported through `Change::missing_newline`.

**Reading a text diff.** `TextDiff::algorithm` returns the algorithm that
produced the diff. `TextDiff::old_slices` and `TextDiff::new_slices` return
the token sequences the differ compared. `TextDiff::ops` returns the captured
operation stream, which must be identical to what `capture_diff_slices`
would produce for the same token sequences and algorithm (regardless of
input size). `TextDiff::grouped_ops` clusters that stream as described in
Grouping and Similarity. `TextDiff::iter_changes` expands one op against the
token sequences exactly as `DiffOp::iter_changes` does.
`TextDiff::iter_all_changes` yields the changes of every op in order; its
iterator type is `AllChangesIter`, exported from `similar::iter`.
`TextDiff::ratio` returns the similarity ratio of the token sequences.
`TextDiff::unified_diff` returns the unified diff formatter described in the
next section.

## Unified Diff Output

This section defines the unified diff rendering rules; they are format rules
a delivery must reproduce exactly.

**The formatter.** `UnifiedDiff` is created by `TextDiff::unified_diff` or
`UnifiedDiff::from_text_diff`. Its setters, each returning the formatter for
chaining: `context_radius` sets the number of context items around change
clusters and defaults to `3`; `header` sets the two file names emitted as a
diff header; `missing_newline_hint` controls the missing newline marker and
defaults to `true`. The formatter implements `Display`, and `to_writer`
writes the same output as raw bytes to an `io::Write` target, returning any
I/O error.

**Hunks.** `UnifiedDiff::iter_hunks` yields one `UnifiedDiffHunk` per group
returned by `grouped_ops(context_radius)`. `UnifiedDiffHunk::new` builds a
hunk from an operation vector, a text diff reference, and a missing newline
hint flag; `ops` returns the hunk's operations; `iter_changes` iterates the
hunk's changes in order; `missing_newline_hint` returns the flag; and
`header` returns the hunk's `UnifiedHunkHeader`. `UnifiedHunkHeader::new`
derives the header from a non-empty operation slice: the old range spans from
the first op's old start to the last op's old end, and likewise for the new
range. The hunk also implements `Display` and `to_writer`.

**Header line format.** A `UnifiedHunkHeader` displays as `@@ -A +B @@`
where `A` and `B` render one range each. A range of length 1 renders as its
1-based start line number alone. Any other length renders as
`start,len` where `start` is 1-based; a range of length 0 renders the line
number of the line before the range (the 0-based start unchanged) followed by
`,0`.

**Full rendering.** Rendering a `UnifiedDiff` concatenates its hunks in
order. When a header was set, the two lines `--- {old name}` and
`+++ {new name}`, each terminated by a newline, are emitted before the first
hunk only; a diff with no hunks emits nothing at all, including no header
lines. Each hunk renders its header line terminated by a newline, then each
change in order as: the change's tag character (space, `-`, or `+`)
immediately followed by the change value. When the diff is not
newline-terminated, a newline is appended after every change value. When the
diff is newline-terminated, values carry their own endings; a change whose
value lacks a trailing newline is followed by a newline, then — only when the
missing newline hint is enabled — the marker line
`\ No newline at end of file` terminated by a newline.

**Quick function.** `similar::udiff::unified_diff` takes an algorithm, the
old and new text, a context radius, and an optional `(old name, new name)`
header pair, and returns the unified diff string of the corresponding line
diff in one call.

## Inline Change Emphasis

This section defines the additional per-line emphasis projection available
with the `inline` cargo feature.

**Iterating inline changes.** `TextDiff::iter_inline_changes` expands one op
into `InlineChange` values. For `Equal`, `Delete`, and `Insert` ops it must
yield exactly one `InlineChange` per plain change, carrying the same tag and
indices and a single unemphasized value equal to the plain change's value.
For a `Replace` op it re-diffs the replaced lines at word level and yields
one `Delete` inline change per old line (old indices ascending from the op's
old start) followed by one `Insert` inline change per new line (new indices
ascending from the op's new start). The concatenated values of each inline
change must reproduce the corresponding line exactly. Segments made of
newline characters must never be emphasized. When the two sides of a
replacement are too dissimilar, the iterator must fall back to yielding the
plain changes converted to unemphasized inline changes. The method applies an
internal deadline of 500 milliseconds to the inner word-level diff;
`iter_inline_changes_deadline` behaves identically with an explicit optional
deadline instant.

**The InlineChange type.** `InlineChange::tag`, `old_index`, and `new_index`
mirror `Change`. `InlineChange::values` returns the value segments as a slice
of `(emphasized, value)` tuples, where `emphasized` marks segments that
differ from the other side. `iter_strings_lossy` yields the same segments
with lossily decoded strings. `missing_newline` returns `true` when the last
segment does not end in a newline. `InlineChange` supports equality
comparison, hashing, and cloning, and implements `From` over `Change`,
producing a single unemphasized segment. Its `Display` implementation
writes each segment in order, wrapping emphasized segments in `-` markers for
deletions and `+` markers for insertions (equal-tagged segments are never
wrapped), and appends a newline when `missing_newline` is true.

## Convenience Diff Functions and Remapping

This section defines `similar::utils`: one-call diff functions returning
tag/value vectors, and the remapper that translates token-level results back
to the original inputs.

**Remapping.** `TextDiffRemapper` maps operation ranges expressed over token
sequences back onto the original strings. `TextDiffRemapper::new` takes the
old token slice, the new token slice, and the two original strings;
`from_text_diff` builds the same remapper from a `TextDiff` and the two
original strings. `slice_old` and `slice_new` map a token index range to the
covering slice of the respective original string, returning `None` when the
range does not fit the token sequence. `iter_slices` expands one op into
`(ChangeTag, slice)` tuples exactly like `DiffOp::iter_slices`, but with the
slices taken from the original strings; it panics when the op's ranges do not
fit the remapper's token sequences (which arises only when the remapper was
built from inputs inconsistent with the diffed tokens).

**One-call diff functions.** Each function takes an algorithm and the two
inputs and returns a `Vec<(ChangeTag, slice)>`:

- `diff_lines` performs a line diff and returns one tuple per line, with the
  line ending attached when present.
- `diff_chars`, `diff_words`, `diff_unicode_words` (requires `unicode`), and
  `diff_graphemes` (requires `unicode`) perform the corresponding token diff
  and return maximal connected slices of the original strings, one tuple per
  operation side, remapped as by `TextDiffRemapper`.
- `diff_slices` diffs two token slices directly and returns one tuple per
  operation side, each holding a subslice of the corresponding input slice.

Across all of these, concatenating the values of `Equal` and `Delete` tuples
must reproduce the old input, and concatenating the values of `Equal` and
`Insert` tuples must reproduce the new input.

## State Model

The library is a stateless computation engine; each diff is an independent
value. The core fact produced by every entry point is a captured operation
stream: an ordered `DiffOp` vector over two token sequences, produced by one
of three algorithms and normalized by replace-merging and semantic cleanup.
Every public projection reads that stream:

1. `TextDiff::ops` / `capture_diff*` — the stream itself.
2. `TextDiff::iter_changes` / `iter_all_changes` / `DiffOp::iter_changes` —
   per-item changes.
3. `TextDiff::grouped_ops` / `group_diff_ops` — context-trimmed clusters.
4. `unified_diff` output — text rendering of the clusters.
5. `TextDiff::ratio` / `get_diff_ratio` / `get_close_matches` — similarity.
6. `iter_inline_changes` — per-line emphasis refinement.
7. `TextDiffRemapper` / `utils` functions — original-string slices.

For fixed inputs, a fixed algorithm, and no deadline, the stream is
deterministic, and every projection of the same stream must agree with every
other as stated in Cross-View Invariants.

## Error Semantics

Diffing itself is infallible; failures propagate only from caller-supplied
hooks, I/O targets, and misuse of the remapper.

| Condition | Required result |
|-----------|-----------------|
| A caller-supplied `DiffHook` callback returns an error during `diff`, `diff_deadline`, `diff_slices`, or `diff_slices_deadline` | The run aborts and returns that error unchanged |
| `UnifiedDiff::to_writer` or `UnifiedDiffHunk::to_writer` hits a write failure | Returns the `io::Error` |
| `TextDiffRemapper::slice_old` / `slice_new` called with a token range outside the token sequence | Returns `None` |
| `TextDiffRemapper::iter_slices` called with an op whose ranges do not fit the remapper's token sequences | Panics |
| `get_close_matches` finds no candidate at or above the cutoff | Returns an empty vector |
| `group_diff_ops` called with an empty op vector | Returns an empty vector |
| `capture_diff_slices` called with two empty slices | Returns an empty op vector |

## Cross-View Invariants

1. **Reconstruction.** For any two inputs, any algorithm, and any entry point
   (generic capture or text diff), keeping the old side of `Equal` ops,
   dropping `Delete`/`Replace` old sides, and splicing `Insert`/`Replace` new
   sides must reproduce the new token sequence exactly, and the old ranges of
   `Equal`, `Delete`, and `Replace` ops must partition the old sequence.
2. **Changes agree with ops.** `TextDiff::iter_all_changes` must yield
   exactly the concatenation, in order, of `iter_changes(op)` over
   `TextDiff::ops`, and each change's tag and indices must follow the
   expansion rules of `DiffOp::iter_changes`.
3. **Text and generic layers agree.** `TextDiff::ops` must equal the vector
   `capture_diff_slices` returns for the same algorithm over
   `old_slices()`/`new_slices()`, for inputs of any size.
4. **Unified rendering agrees with grouping.** The unified diff output must
   contain exactly one hunk per group of `grouped_ops(context_radius)`, each
   hunk header derived from its group's first and last ops, and one rendered
   line per change of that group, prefixed by the change's tag character.
5. **Ratio agrees across views.** `TextDiff::ratio` must equal
   `get_diff_ratio(diff.ops(), old token count, new token count)`, and every
   word returned by `get_close_matches` must have a character-level diff
   ratio at or above the cutoff, in non-increasing ratio order.
6. **Remapped output covers the inputs.** For every `utils` diff function
   and for `TextDiffRemapper::iter_slices` over a full op stream, the
   concatenated `Equal` + `Delete` values must equal the old input and the
   concatenated `Equal` + `Insert` values must equal the new input.
7. **Inline changes cover the lines.** For every op of a line diff, the
   concatenated segment values of the inline changes must equal the
   concatenated values of the plain changes for that op, per line and side.

## Public Interface

### Import Surface

```rust
// crate root
use similar::{
    Algorithm, Change, ChangeTag, DiffOp, DiffTag,
    DiffableStr, DiffableStrRef, InlineChange,
    TextDiff, TextDiffConfig,
    capture_diff, capture_diff_deadline,
    capture_diff_slices, capture_diff_slices_deadline,
    get_close_matches, get_diff_ratio, group_diff_ops,
};

// algorithm layer
use similar::algorithms::{
    Algorithm, Capture, Compact, DiffHook, IdentifyDistinct, NoFinishHook,
    Replace, diff, diff_deadline, diff_slices, diff_slices_deadline,
};
use similar::algorithms::lcs;      // lcs::diff, lcs::diff_deadline
use similar::algorithms::myers;    // myers::diff, myers::diff_deadline
use similar::algorithms::patience; // patience::diff, patience::diff_deadline

// iterators
use similar::iter::{AllChangesIter, ChangesIter};

// unified diff
use similar::udiff::{UnifiedDiff, UnifiedDiffHunk, UnifiedHunkHeader, unified_diff};

// utilities
use similar::utils::{
    TextDiffRemapper, diff_chars, diff_graphemes, diff_lines,
    diff_slices, diff_unicode_words, diff_words,
};
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Algorithm` | enum | Selects Myers, Patience, or Lcs; defaults to Myers |
| `ChangeTag` | enum | Equal/Delete/Insert tag of an expanded change; displays as space/`-`/`+` |
| `DiffTag` | enum | Equal/Delete/Insert/Replace tag of a diff operation |
| `DiffOp` | enum | One edit script segment with index fields; expands to changes and slices |
| `Change` | struct | One expanded item change with tag, optional indices, and value |
| `InlineChange` | struct | Line change with emphasized/unemphasized value segments |
| `TextDiff` | struct | Captured text diff over tokenized inputs; hub of the text layer |
| `TextDiffConfig` | struct | Builder for text diffs: algorithm, deadline, newline flag |
| `DiffableStr` | trait | Tokenization and inspection contract for diffable strings |
| `DiffableStrRef` | trait | Resolves owned/borrowed string types to a diffable string |
| `capture_diff` | function | Runs an algorithm over indexed ranges, returns cleaned ops |
| `capture_diff_deadline` | function | `capture_diff` with an optional deadline |
| `capture_diff_slices` | function | Runs an algorithm over two slices, returns cleaned ops |
| `capture_diff_slices_deadline` | function | `capture_diff_slices` with an optional deadline |
| `get_diff_ratio` | function | Similarity ratio `2M/T` from ops and lengths |
| `group_diff_ops` | function | Clusters ops around changes with n context items |
| `get_close_matches` | function | Ranks candidate words by char-level similarity |
| `algorithms::DiffHook` | trait | Callback receiver for edit script segments |
| `algorithms::Capture` | struct | Hook recording segments as `DiffOp`s |
| `algorithms::Replace` | struct | Hook adapter merging delete+insert pairs into replace |
| `algorithms::Compact` | struct | Hook adapter applying semantic cleanup on finish |
| `algorithms::NoFinishHook` | struct | Hook adapter swallowing `finish` |
| `algorithms::IdentifyDistinct` | struct | Re-tokenizes sequences as compact integers |
| `algorithms::diff` | function | Runs the selected algorithm against a hook |
| `algorithms::diff_deadline` | function | `diff` with an optional deadline |
| `algorithms::diff_slices` | function | `diff` over two full slices |
| `algorithms::diff_slices_deadline` | function | `diff_slices` with an optional deadline |
| `algorithms::lcs::diff` / `diff_deadline` | function | LCS algorithm entry points |
| `algorithms::myers::diff` / `diff_deadline` | function | Myers algorithm entry points |
| `algorithms::patience::diff` / `diff_deadline` | function | Patience algorithm entry points |
| `iter::ChangesIter` | struct | Iterator behind `DiffOp::iter_changes` |
| `iter::AllChangesIter` | struct | Iterator behind `TextDiff::iter_all_changes` |
| `udiff::UnifiedDiff` | struct | Unified diff formatter with radius/header/hint settings |
| `udiff::UnifiedDiffHunk` | struct | One rendered hunk with header, ops, and changes |
| `udiff::UnifiedHunkHeader` | struct | `@@ -A +B @@` header formatter |
| `udiff::unified_diff` | function | One-call unified diff string for a line diff |
| `utils::TextDiffRemapper` | struct | Maps token-range ops back to original string slices |
| `utils::diff_lines` | function | One-call line diff as tag/value tuples |
| `utils::diff_chars` | function | One-call char diff remapped to original slices |
| `utils::diff_words` | function | One-call word diff remapped to original slices |
| `utils::diff_unicode_words` | function | One-call Unicode-word diff remapped to original slices |
| `utils::diff_graphemes` | function | One-call grapheme diff remapped to original slices |
| `utils::diff_slices` | function | One-call slice diff as tag/subslice tuples |

### CLI Entry Points

There is no console script for this package. The crate is a Rust library;
all functionality is reached through the imports above.

## Appendix A: Environment

- Language: Rust, edition 2018-compatible (toolchain 1.83; the crate's
  declared minimum supported Rust version must not exceed it).
- The crate must build as `similar` and must define the cargo features
  `text` (enabled by default; gates the text layer: `TextDiff`,
  `TextDiffConfig`, `DiffableStr`, `DiffableStrRef`, `udiff`, `utils`,
  `get_close_matches`, and the string methods of `Change`), `unicode`
  (implies `text`; gates `tokenize_unicode_words`, `tokenize_graphemes`,
  `diff_unicode_words`, `diff_graphemes`, `from_unicode_words`,
  `from_graphemes`), and `inline` (implies `unicode`; gates `InlineChange`
  and the inline iteration methods). The assessment suite depends on the
  crate as `similar = { version = "*", features = ["unicode", "inline"] }`.
- The `unicode-segmentation` crate is available for Unicode word and
  grapheme segmentation; the diff algorithms, hook adapters, tokenizers for
  lines/words/chars, grouping, rendering, and remapping are the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API only, in two layers. Atomic checks
target one entry point at a time: tokenization rules, `DiffOp` range and
expansion semantics, capture stream shape on small unambiguous inputs, the
grouping rules, ratio arithmetic, close-match ranking, hunk header
formatting, and newline handling. Integration checks span projections:
reconstruction of inputs from op streams across algorithms, agreement between
the text and generic layers, agreement between unified output, grouped ops,
and change streams, remapped slice coverage of the original inputs, and
inline change coverage of replaced lines. Expected values are stated
explicitly in the tests; `Debug` formatting, private helpers, and performance
are not assessed. Deadline-accepting entry points are exercised only for
script validity, not for approximation quality.
