<!-- INTERNAL
task_id: fst-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: docs.rs/fst 0.4.7 (crate root guide, set/map/raw/automaton/stream module and item docs), README at pinned commit; reference behavior observed by running the pinned checkout
-->

# Finite State Transducer Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`fst` is a Rust library for representing large ordered sets and maps of byte
keys as finite state transducers: compressed automata that answer membership
and value lookups, stream their keys in byte-lexicographic order, select
sub-ranges, filter through composable automata, and combine across multiple
containers with set operations — all over one immutable byte image per
container.

The library serves three container views of that image. `Set` holds keys
alone, `Map` associates each key with a `u64` value, and `raw::Fst` is the
value-carrying form both are built on, exposing the same query, stream,
range, search, and set-operation surface plus the byte image itself. Every
container is constructed either in one shot from pre-sorted input or
incrementally through a builder that enforces insertion in byte-lexicographic
key order, and every finished image round-trips losslessly through its
serialized bytes.

Queries and streams run directly over the compressed image without
deserializing it. Search accepts any implementation of the `Automaton`
trait, and the crate ships ready-made automata for exact-string and
subsequence matching along with combinators for prefix, complement,
intersection, and union composition.

## Non-Goals

- This specification does not require Levenshtein or regular-expression
  automata, memory-mapped file handling, or any optional cargo feature;
  no cargo feature is required at all.
- This specification does not require node-level introspection of the
  compressed automaton (nodes, transitions, addresses) beyond the container
  APIs described here.
- This specification does not define the internal encoding of the byte
  image beyond the round-trip, size, verification, and version behaviors
  described in this document.
- This specification does not require thread-safety guarantees beyond
  ordinary Rust `Send`/`Sync` auto-derivation for value types.
- This specification does not require streaming results to outlive their
  container; streams borrow the container they read from.

## Representative Workflows

The workflows below exercise the library end to end: building containers,
querying, streaming ranges, searching with automata, and combining
containers.

**Build a map, query it, and stream a range.**

```rust
use fst::{IntoStreamer, Map, MapBuilder, Streamer};

// One-shot construction from pre-sorted (key, value) pairs.
let map = Map::from_iter(vec![
    ("bramble", 7u64),
    ("fern", 0),
    ("moss", 22),
    ("willow", 4),
])?;
assert_eq!(map.get("moss"), Some(22));
assert_eq!(map.get("fern"), Some(0));
assert!(map.get("oak").is_none());
assert_eq!(map.len(), 4);

// Range selection: keys strictly after "bramble", up to and incl. "moss".
let mut stream = map.range().gt("bramble").le("moss").into_stream();
let mut found = vec![];
while let Some((key, value)) = stream.next() {
    found.push((key.to_vec(), value));
}
assert_eq!(found, vec![
    (b"fern".to_vec(), 0),
    (b"moss".to_vec(), 22),
]);

// Incremental construction with a builder writes the same image.
let mut builder = MapBuilder::memory();
builder.insert("bramble", 7)?;
builder.insert("fern", 0)?;
builder.insert("moss", 22)?;
builder.insert("willow", 4)?;
let built = builder.into_map();
assert_eq!(built.get("willow"), Some(4));
# Ok::<(), fst::Error>(())
```

**Search with automata and combine sets.**

```rust
use fst::automaton::{Str, Subsequence};
use fst::{Automaton, IntoStreamer, Set, Streamer};

let index = Set::from_iter(vec![
    "docs/guide/intro",
    "docs/reference/api",
    "src/lib",
    "src/tests/api",
])?;

// Subsequence automaton: characters must appear in order, gaps allowed.
let hits = index.search(Subsequence::new("dgi")).into_stream().into_strs()?;
assert_eq!(hits, vec!["docs/guide/intro"]);

// Prefix search via the starts_with combinator on an exact-string automaton.
let hits = index
    .search(Str::new("src/").starts_with())
    .into_stream()
    .into_strs()?;
assert_eq!(hits, vec!["src/lib", "src/tests/api"]);

// Set algebra across two containers.
let other = Set::from_iter(vec!["docs/reference/api", "src/lib", "vendor/pkg"])?;
let mut union = index.op().add(&other).union();
let mut all = vec![];
while let Some(key) = union.next() {
    all.push(String::from_utf8(key.to_vec()).unwrap());
}
assert_eq!(all.len(), 5);
assert_eq!(index.op().add(&other).intersection().into_stream().into_strs()?,
           vec!["docs/reference/api", "src/lib"]);
# Ok::<(), fst::Error>(())
```

## Building Transducers

This section defines how containers come into existence and the ordering
contract every construction path enforces. A container's key set is fixed at
build time; there is no post-build mutation.

**Ordering contract.** Keys are byte strings. Every construction path
requires keys to arrive in ascending byte-lexicographic order. When a key
arrives that is less than the previously accepted key, the operation fails
with the out-of-order error carrying both the previous and offending keys.
When it equals the previously accepted key, the outcome depends on whether
the insertion carries a value: key-only insertion (`SetBuilder::insert`,
`raw::Builder::add`, `Set::from_iter`) treats the repeat as a no-op and
succeeds, leaving one copy of the key in the container; value-carrying
insertion (`MapBuilder::insert`, `raw::Builder::insert`, `Map::from_iter`)
fails with the duplicate-key error carrying the key. `Map` and `raw::Fst`
associate each accepted key with a `u64` value supplied at insertion;
values carry no ordering constraint.

**One-shot construction.** `Set::from_iter` accepts an iterator of
byte-string-convertible items and returns a memory-backed `Set`.
`Map::from_iter` accepts `(key, u64)` pairs. `raw::Fst::from_iter_set` and
`raw::Fst::from_iter_map` are the raw equivalents (the set form assigns
every key the value zero). Each returns the ordering errors above inside
`fst::Error` when the input violates the contract.

**Builders.** `SetBuilder`, `MapBuilder`, and `raw::Builder` construct a
container incrementally. Each type provides `memory()`, an infallible
constructor buffering into an in-memory byte vector, and `new(wtr)`, which
streams the image into any `std::io::Write` and returns `fst::Result`.
`SetBuilder::insert` and `raw::Builder::add` accept a key; the map form
`MapBuilder::insert` and `raw::Builder::insert` accept a key and a `u64`
value. `extend_iter` inserts every item of an iterator and `extend_stream`
inserts every item of a compatible stream, both under the same ordering
contract. For memory-backed builders, `into_set`, `into_map`, and
`into_fst` finish construction and return the container directly. For
writer-backed builders, `finish` completes the image and drops the writer,
`into_inner` completes it and returns the writer, `get_ref` borrows the
writer without finishing, and `bytes_written` reports the number of bytes
emitted so far. A finished image constructed through a writer, when handed
back to `Set::new`, `Map::new`, or `raw::Fst::new`, equals the container
built in memory from the same input.

**Opening images.** `Set::new`, `Map::new`, and `raw::Fst::new` accept any
`D: AsRef<[u8]>` holding a previously finished image and reconstruct the
container without copying. Handing them bytes that are not a finished image
fails with a format error carrying the byte length; handing them an image
whose encoded version does not match the crate's supported version fails
with a version error carrying both versions.

## Querying Containers

This section defines point lookups. All queries run over the immutable
image and never allocate a copy of it.

**Membership and values.** `Set::contains` returns whether a key is
present. `Map::get` returns `Some(value)` for a present key and `None`
otherwise; a stored value of zero is returned as `Some(0)`, fully
distinguishable from absence. `Map::contains_key` mirrors membership.
`raw::Fst::get` returns `Option<Output>` where `Output` wraps the stored
`u64`, and `raw::Fst::contains_key` mirrors membership. All key parameters
accept any `AsRef<[u8]>` value.

**Sizes.** `len` returns the number of keys and `is_empty` reports whether
it is zero, on all three containers. `raw::Fst::size` returns the byte
length of the image. An empty container is a valid image: zero keys, empty
streams, and every membership probe answering `false`/`None`.

**Output algebra.** `raw::Output` is a copyable wrapper over `u64` with
`new`, `zero`, `value`, and `is_zero`; `zero()` equals `new(0)`. `cat`
returns the sum of two outputs, `prefix` returns their minimum, and `sub`
returns the difference, panicking when the subtrahend exceeds the value.

**Reverse lookup.** `raw::Fst::get_key` maps a value back to
`Some(key)` for images whose values are monotonically increasing in key
order, and returns `None` when no key carries the value. For
non-monotonic images its result is unspecified and no behavior is promised.

## Streaming and Ranges

This section defines ordered iteration, the stream protocol every
projection shares, and range selection.

**The stream protocol.** `Streamer` is the crate's lending-iterator trait:
`next()` returns `Some(item)` while items remain and `None` at exhaustion,
where the item borrows from the stream. `IntoStreamer` converts a value
into a stream via `into_stream`; containers, range builders, search
builders, and set-operation results all implement it, and references to
`Set`/`Map`/`raw::Fst` convert into their full streams.

**Container streams.** `Set::stream` yields each key as `&[u8]` in strictly
ascending byte-lexicographic order. `Map::stream` yields `(&[u8], u64)`
pairs in the same key order; `Map::keys` yields keys alone and
`Map::values` yields values in key order. `raw::Fst::stream` yields
`(&[u8], Output)` pairs. Set streams provide `into_strs` (collecting keys
as `String`s, failing with the UTF-8 decoding error when a key is not valid
UTF-8) and `into_bytes` (collecting keys as byte vectors). Map streams
provide `into_byte_vec`, `into_str_vec`, `into_byte_keys`, `into_str_keys`,
and `into_values`, with the `str` forms failing the same way on non-UTF-8
keys.

**Ranges.** `range()` on any container returns a builder accepting `ge`,
`gt`, `le`, and `lt` bounds over byte keys; each bound is optional, later
calls of the same kind replace earlier ones, and the built stream yields
exactly the keys satisfying every bound, in order. An empty selection is a
valid stream that yields nothing. Range builders convert to streams through
`into_stream`.

## Automaton Search

This section defines the automaton contract and the shipped automata;
search is the projection that filters a container's ordered key space
through an automaton.

**The trait.** An `Automaton` declares an associated `State` type and five
operations: `start()` returns the initial state; `is_match(&state)` reports
whether a state is accepting; `accept(&state, byte)` returns the successor
state for one input byte; `can_match(&state)` reports whether any
continuation of the state could ever accept (returning `false` prunes the
subtree); and `will_always_match(&state)` reports whether every
continuation accepts. The last two have conservative defaults (`true` and
`false` respectively) that any implementation is permitted to keep.

**Shipped automata.** `automaton::Str::new(string)` matches exactly one
key: the given string's bytes. `automaton::Subsequence::new(string)`
matches any key that contains the given bytes in order, contiguously or
not; the empty subsequence matches every key. `automaton::AlwaysMatch`
matches every key.

**Combinators.** The trait provides consuming combinators:
`starts_with()` matches any key having a prefix the underlying automaton
accepts; `complement()` matches exactly the keys the underlying automaton
rejects; `a.intersection(b)` matches keys both accept; `a.union(b)` matches
keys either accepts. Combinators nest arbitrarily and their wrapper types
(`StartsWith`, `Complement`, `Intersection`, `Union`) are public.

**Search integration.** `search(aut)` on `Set`, `Map`, and `raw::Fst`
returns the same range builder used by `range()`, so automaton filtering
and `ge`/`gt`/`le`/`lt` bounds compose in one pass; the resulting stream
yields exactly the in-range keys the automaton accepts, in ascending
order, with the map and raw forms carrying their values.

## Set Operations Across Transducers

This section defines the lattice operations that combine any number of
ordered streams — whole containers, ranges, or searches — into one ordered
result.

**Building an operation.** `op()` on a container returns an `OpBuilder`
seeded with that container's full stream; `OpBuilder::new()` starts empty.
`add` (consuming, chainable) and `push` (by reference) attach any
`IntoStreamer` whose items are compatible with the builder's family. The
set family accepts key streams; the map and raw families accept key-value
streams.

**Set-family results.** `union()` yields every key present in at least one
input stream, once. `intersection()` yields keys present in every input
stream. `difference()` yields keys present in the first stream and absent
from all others. `symmetric_difference()` yields keys present in an odd
number of input streams. All results are streams in ascending
byte-lexicographic order.

**Map-family results.** The same four operations on `Map`/`raw::Fst`
builders yield `(key, &[IndexedValue])` pairs, where each `IndexedValue`
carries the zero-based `index` of the input stream that produced the key
(in `add`/`push` order) and the `value` it stored; entries are sorted by
`index`, and the same key selection rules as the set family apply to which
keys appear.

**Whole-container comparisons.** `Set::is_disjoint`, `Set::is_subset`, and
`Set::is_superset` (and the same methods on `raw::Fst`, compared over
keys) accept any compatible stream and answer the standard set predicates
against the container's own key set.

## Raw Transducers and Byte Images

This section defines the raw layer: the value-carrying automaton every
container wraps, and the byte image as a first-class artifact.

**Raw containers.** `raw::Fst` supports `get`, `contains_key`, `get_key`,
`stream`, `range`, `search`, `op`, `len`, `is_empty`, `is_disjoint`,
`is_subset`, and `is_superset` with the semantics defined in the previous
sections, always carrying `Output` values. `Set` and `Map` expose their
underlying raw container through `as_fst` (borrowing) and `into_fst`
(consuming); the raw container observed this way answers every query
consistently with the wrapping container, with set keys carrying the
zero output.

**Byte images.** `raw::Fst::as_bytes` borrows the image, `to_vec` copies
it, `as_inner` borrows the underlying data value, and `into_inner` returns
it. Reopening any of these through `Set::new`/`Map::new`/`raw::Fst::new`
reproduces a container equal in every projection. `size()` equals
`as_bytes().len()`. The crate exposes its supported format version as
`raw::VERSION`, and `verify()` recomputes the image checksum, returning the
checksum-mismatch error when the image is corrupt and succeeding on any
image the crate built.

## State Model

The core state is one immutable byte image per container encoding an
ordered minimal automaton over byte keys with `u64` outputs. Public
projections of that single state:

- **Membership and value queries** (`contains`, `get`, `contains_key`,
  `get_key`) answer point questions.
- **Full streams** (`stream`, `keys`, `values`) enumerate the state in
  ascending key order.
- **Range and search streams** (`range`, `search`) enumerate the selected
  subset in the same order.
- **Set operations** (`op` + `union`/`intersection`/`difference`/
  `symmetric_difference`, `is_disjoint`/`is_subset`/`is_superset`) relate
  several states.
- **The byte image** (`as_bytes`, `to_vec`, `into_inner`, `size`,
  `verify`, `Set::new`/`Map::new`/`raw::Fst::new`) moves the state whole.
- **Builders** create the state under the ordering contract; a finished
  state never changes.

Streams borrow the container and follow Rust borrowing rules; containers
are plain values that move and clone (when their data type clones) without
affecting any image already built.

## Error Semantics

All fallible operations return `fst::Result<T>`, an alias for
`std::result::Result<T, fst::Error>`. `fst::Error` has two variants:
`Fst(raw::Error)` for transducer-domain failures and `Io(std::io::Error)`
for writer failures; both variants implement `From` conversion into
`fst::Error`, and the type implements `Display`, `Debug`, and
`std::error::Error` with `source()` returning the wrapped error.

`raw::Error` variants and their conditions:

| Variant | Payload | Condition |
|---------|---------|-----------|
| `Version` | `expected`, `got` (u64 fields) | opening an image whose encoded version differs from the crate's |
| `Format` | `size` (usize field) | opening bytes that are not a finished image |
| `ChecksumMismatch` | `expected`, `got` (u32 fields) | `verify()` on a corrupted image |
| `ChecksumMissing` | none | `verify()` on an image without a checksum |
| `DuplicateKey` | `got` (byte vector field) | value-carrying insertion of a key equal to the previously accepted key |
| `OutOfOrder` | `previous`, `got` (byte vector fields) | inserting a key smaller than the previously accepted key |
| `WrongType` | `expected`, `got` (u64 fields) | reserved for callers layering their own container types; never produced by the operations in this document |
| `FromUtf8` | wrapped `std::string::FromUtf8Error` | collecting keys as `String`s when a key is not valid UTF-8 |

`raw::Error` implements `Display`, `Debug`, and `std::error::Error`, and
converts into `fst::Error` via `From`. The enum reserves the right to grow;
matches over it require a wildcard arm. `Output::sub` panics on underflow
as described in Querying Containers; no other described operation panics on
well-typed input.

## Cross-View Invariants

1. For every container, the number of items its full stream yields equals
   `len()`, and every yielded key answers `true`/`Some` to the container's
   membership or value query — enumeration and point queries agree.
2. A range stream with any combination of `ge`/`gt`/`le`/`lt` bounds
   yields exactly the keys of the full stream that satisfy every bound, in
   the same relative order — selection never reorders or invents keys.
3. A search stream yields exactly the keys of the full stream the
   automaton accepts, and combinator algebra holds observably:
   `complement()` yields the set-difference of the full key set, and
   `a.intersection(b)` yields the intersection of the keys `a` and `b`
   yield alone.
4. Each set operation over containers equals the corresponding brute-force
   algebra over their streamed key sets: union, intersection,
   first-minus-rest difference, and odd-count symmetric difference —
   and the map family reports, for every yielded key, exactly the
   (stream index, value) pairs of the inputs holding that key.
5. Rebuilding a container from its byte image (`as_bytes`, `to_vec`, or
   `into_inner`) preserves every projection: length, membership, values,
   full stream, ranges, searches, and set-operation results.
6. Building the same sorted input through any construction path —
   one-shot `from_iter*`, a memory builder, or a writer-backed builder
   whose output is reopened — produces containers whose byte images are
   identical.
7. A `Map` and the `raw::Fst` obtained from it through `as_fst` agree on
   every key: `map.get(k) == Some(v)` exactly when
   `fst.get(k) == Some(Output::new(v))`.

## Public Interface

### Import Surface

```rust
use fst::{Automaton, Error, IntoStreamer, Map, MapBuilder, Result, Set,
          SetBuilder, Streamer};
use fst::automaton::{AlwaysMatch, Complement, Intersection, StartsWith,
                     Str, Subsequence, Union};
use fst::set::{Difference, Intersection as SetIntersection, OpBuilder,
               Stream, StreamBuilder, SymmetricDifference,
               Union as SetUnion};
use fst::map::{Difference as MapDifference,
               Intersection as MapIntersection, IndexedValue, Keys,
               OpBuilder as MapOpBuilder, Stream as MapStream,
               StreamBuilder as MapStreamBuilder,
               SymmetricDifference as MapSymmetricDifference,
               Union as MapUnion, Values};
use fst::raw::{Builder, Fst, IndexedValue as RawIndexedValue, Output,
               VERSION};
```

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `Set` | struct | Ordered set of byte keys over one image; query, stream, range, search, ops |
| `SetBuilder` | struct | Ordered incremental set construction into memory or a writer |
| `Map` | struct | Ordered map from byte keys to `u64` over one image |
| `MapBuilder` | struct | Ordered incremental map construction into memory or a writer |
| `Streamer` | trait | Lending stream protocol: `next()` until `None` |
| `IntoStreamer` | trait | Conversion of containers/builders/ops into streams |
| `Automaton` | trait | Byte-automaton contract with prefix/complement/intersection/union combinators |
| `automaton::Str` | struct | Automaton matching one exact string |
| `automaton::Subsequence` | struct | Automaton matching keys containing a subsequence |
| `automaton::AlwaysMatch` | struct | Automaton matching every key |
| `automaton::StartsWith` | struct | Combinator wrapper produced by `starts_with()` |
| `automaton::Complement` | struct | Combinator wrapper produced by `complement()` |
| `automaton::Intersection` | struct | Combinator wrapper produced by `intersection()` |
| `automaton::Union` | struct | Combinator wrapper produced by `union()` |
| `set::Stream` | struct | Ordered key stream over a set |
| `set::StreamBuilder` | struct | Range/search bound builder over a set |
| `set::OpBuilder` | struct | Multi-stream set-operation builder over keys |
| `set::Union` | struct | Union result stream (set family) |
| `set::Intersection` | struct | Intersection result stream (set family) |
| `set::Difference` | struct | Difference result stream (set family) |
| `set::SymmetricDifference` | struct | Symmetric-difference result stream (set family) |
| `map::Stream` | struct | Ordered key-value stream over a map |
| `map::Keys` | struct | Key-only stream over a map |
| `map::Values` | struct | Value-only stream over a map |
| `map::StreamBuilder` | struct | Range/search bound builder over a map |
| `map::OpBuilder` | struct | Multi-stream set-operation builder over key-value streams |
| `map::Union` | struct | Union result stream with `IndexedValue` provenance |
| `map::Intersection` | struct | Intersection result stream with `IndexedValue` provenance |
| `map::Difference` | struct | Difference result stream with `IndexedValue` provenance |
| `map::SymmetricDifference` | struct | Symmetric-difference result stream with provenance |
| `map::IndexedValue` | struct | (stream index, value) pair in map-family op results |
| `raw::Fst` | struct | Value-carrying automaton underlying sets and maps |
| `raw::Builder` | struct | Raw ordered construction with explicit values |
| `raw::Output` | struct | Copyable `u64` wrapper with cat/prefix/sub algebra |
| `raw::VERSION` | constant | Image format version the crate reads and writes |
| `Error` | enum | Top-level error: transducer-domain or I/O |
| `raw::Error` | enum | Transducer-domain failure taxonomy |
| `Result` | type alias | `std::result::Result<T, fst::Error>` |

### CLI Entry Points

There is no executable entry point for this crate. Programmatic use is
through the Rust library interface alone.

## Appendix A: Environment

- Language: Rust, edition 2018-compatible (toolchain 1.83; the crate's
  declared minimum supported Rust version must not exceed it).
- The crate must build as `fst` with no cargo features required; the
  assessment suite depends on the crate as `fst = { version = "*" }` with
  default features.
- No third-party crates are required or provided at runtime; the automaton
  encoding, builders, streams, and set operations are the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the crate through its public interface only.
Dimensions covered:

- Construction paths (one-shot, memory builder, writer-backed builder,
  extend forms) converging on identical images, and ordering-contract
  failures with their error payloads.
- Membership and value queries, including zero values, empty containers,
  and the raw `Output` algebra.
- Full streams, key/value projections, and collection helpers including
  UTF-8 failure behavior.
- Range selection across all bound combinations and empty selections.
- Automaton search with the shipped automata and nested combinators,
  including agreement with brute-force filtering.
- Set operations across two and three containers, map-family provenance
  (`IndexedValue`), and whole-container predicates.
- Byte-image round trips, size, verification, and error taxonomy for
  malformed images.
- Cross-view invariants tying queries, streams, ranges, searches, ops,
  and images together on shared fixtures.

Scoring runs the suite against the delivered crate with cargo-nextest;
each test either passes or fails, and no partial credit is awarded within
a test.
