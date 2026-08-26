<!-- INTERNAL
task_id: indexmap-fullrepro-001
spec_version: v1
delta: initial version; contract details fixed by three probe rounds against
the pinned reference: insert keeps position and the stored key instance while
replacing the value; swap_remove back-fill law (last entry moves into the
vacated slot) vs shift_remove closure law; deprecated remove/remove_entry
(map) and remove/take (set) aliasing the swap variants; move_index rotation
and swap_indices exchange with out-of-bounds panics; insert_before final
position index-1 when an existing key moves forward, boundary index == len
allowed; shift_insert exact-position law with 0..=len for new keys and 0..len
for existing keys (panic at len); insert_sorted keeps the index of an
existing key; truncate no-op beyond len; split_off panic beyond len; drain
and splice range panics (end > len, start > end); splice outside-range
collision law (existing key keeps position, value updated, pair not
reinserted into the range); append insert-each-in-order law; FromIterator /
Extend duplicate law (first occurrence fixes position, last value wins);
stable vs unstable sort families; binary_search Ok/Err values;
slice get_range None on invalid ranges; order-insensitive map/set equality
vs order-sensitive slice equality/ordering/hashing; Index<&Q>/Index<usize>
panics; Keys Index<usize>; entry state machine values (VacantEntry index ==
len, insert_entry, occupied move_index/swap_remove/shift_remove, IndexedEntry,
first_entry/last_entry); set value-identity laws (insert keeps stored value,
replace swaps it in place); set algebra iteration-order laws and operator
equivalents; try_reserve error on absurd capacities; Debug forms.
source_boundary: docs.rs/indexmap 2.7.1 (crate root, IndexMap and IndexSet
method docs, map::Entry/OccupiedEntry/VacantEntry/IndexedEntry, map::Slice,
set::Slice, set iterator docs, macros), README.md; reference behavior
observed by running the pinned checkout (probe binary, three rounds). The
serde/rayon/borsh/arbitrary/quickcheck features and the opt-in MutableKeys /
MutableValues / MutableEntryKey traits are excluded from scope.
-->

# indexmap Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`indexmap` is a hash table library whose map and set remember insertion
order. `IndexMap` stores key-value pairs and `IndexSet` stores values in
one contiguous sequence, while a hash index over the keys keeps lookup,
insertion, and removal at hash-map cost. Every entry therefore has two
addresses at once: its key (hash view) and its position (index view), and
the library's contract is precisely how each operation reads or rewrites
the sequence — which operations preserve order, which perturb it, and how.

The sequence behaves like a vector wherever that is cheap: entries are
addressable by `usize` position, ranges project out as slices, sorting and
binary search work in place, and callers choose between order-preserving
removal (`shift_remove`, linear cost) and constant-time removal that moves
the last entry into the vacated slot (`swap_remove`). An entry interface
combines lookup and insertion in one step, set algebra produces
deterministically ordered results, and `indexmap!` / `indexset!` macros
build literals.

The installable crate name is `indexmap`.

## Non-Goals

- This specification does not require serialization, parallel-iteration,
  or property-testing integrations of any kind.
- This specification does not require opt-in mutable access to stored keys
  or stored set values beyond the operations described here.
- This specification does not require a `no_std` build configuration.
- This specification does not define the hash function: any hasher
  compatible with the standard `BuildHasher` interface must be usable, and
  the default hasher is the standard library's `RandomState`.
- This specification does not define capacity values: `capacity()` reports
  an implementation-chosen figure at least as large as the length, and no
  test depends on its exact value.
- This specification does not define the result order of the `_unstable`
  sort variants between elements that compare equal, nor the outcome of
  binary searches on sequences that are not sorted by the search criterion
  (such calls return an unspecified index without panicking).

## Representative Workflows

Three workflows illustrate the map, the ordered views, and the set.

**A configuration registry.** Insertion order is presentation order;
lookups go by key, updates go through the entry interface, and removal
chooses its order law:

```rust
use indexmap::IndexMap;

let mut cfg = IndexMap::new();
cfg.insert("host".to_string(), "localhost".to_string());
cfg.insert("port".to_string(), "8080".to_string());
cfg.insert("debug".to_string(), "false".to_string());

// lookup by borrowed form; positions are stable under value updates
assert_eq!(cfg.get("port").map(String::as_str), Some("8080"));
cfg.insert("port".to_string(), "9090".to_string());
assert_eq!(cfg.get_index_of("port"), Some(1));

*cfg.entry("debug".to_string()).or_insert_with(String::new) = "true".to_string();

// order-preserving removal keeps the presentation sequence intact
cfg.shift_remove("host");
let names: Vec<&str> = cfg.keys().map(String::as_str).collect();
assert_eq!(names, ["port", "debug"]);
```

**A ranked leaderboard.** The same map re-sorted becomes a rank table with
positional access and binary search:

```rust
use indexmap::IndexMap;

let mut scores: IndexMap<&str, u32> =
    [("ada", 310), ("bob", 250), ("cy", 480)].into_iter().collect();

scores.sort_by(|_, a, _, b| b.cmp(a));            // descending by score
assert_eq!(scores.get_index(0), Some((&"cy", &480)));
assert_eq!(scores.get_index_of("ada"), Some(1));
assert_eq!(scores[1], 310);                        // position indexing yields the value

let podium = scores.get_range(0..2).unwrap();
assert_eq!(podium.keys().collect::<Vec<_>>(), [&"cy", &"ada"]);
```

**Tag sets with deterministic algebra.** Set operations iterate in a
documented order, so results are reproducible:

```rust
use indexmap::IndexSet;

let ours: IndexSet<&str> = ["rust", "cli", "async"].into_iter().collect();
let theirs: IndexSet<&str> = ["cli", "web", "rust"].into_iter().collect();

let shared: Vec<&&str> = ours.intersection(&theirs).collect();
assert_eq!(shared, [&"rust", &"cli"]);            // our order, filtered

let all = &ours | &theirs;
assert_eq!(all.iter().collect::<Vec<_>>(), [&"rust", &"cli", &"async", &"web"]);
```

## Construction, Hashing, and Capacity

This section defines how containers come into existence and which
allocation controls exist, none of which affect any content law.

**Constructors.** `IndexMap::new()` and `IndexSet::new()` return empty
containers over the default `RandomState` hasher; `with_capacity(n)`
additionally pre-allocates. `with_capacity_and_hasher(n, hasher)` and
`with_hasher(hasher)` accept a caller-supplied `BuildHasher`, and the
`Default` implementation exists for any hasher type that is itself
`Default`. Containers are also built from iterators of pairs (map) or
values (set), from fixed-size arrays via `From`, and from the `indexmap!`
and `indexset!` literal macros. WHEN a construction source contains a
duplicate key THEN the first occurrence fixes the position and the last
value wins (macros included); for sets, the first equal value is the one
stored.

**Equivalent lookups.** Every lookup-by-key accepts any borrowed form of
the key through the `Equivalent` trait (re-exported at the crate root): a
map keyed by `String` is queried with `&str`, and caller types opt into
custom equivalence relations by implementing `Equivalent` consistently
with their hashes.

**Capacity.** `len()` is the number of stored entries; `is_empty()` tests
zero. `capacity()`, `reserve`, `reserve_exact`, `shrink_to_fit`, and
`shrink_to` manage allocation only: they must leave length, content, and
order unchanged. `try_reserve` and `try_reserve_exact` return `Ok(())` on
success; IF the requested additional capacity cannot be allocated or
overflows THEN they return an `Err` carrying a `TryReserveError`.
`hasher()` returns a reference to the hash builder. `clear()` removes
every entry, leaving an empty container.

## Insertion and Lookup

This section defines the map's write path and its two read addresses.

**Insertion.** `insert(key, value)` appends a new key at the end and
returns `None`; WHEN the key is already present THEN the value is
replaced, the returned value is the old one, the entry keeps its position,
and the stored key instance is not replaced (only the value changes).
`insert_full(key, value)` behaves identically and returns the pair of the
entry's index and the old value.

**Lookup family.** `get(key)` returns the value; `get_key_value(key)`
returns the stored key and value; `get_full(key)` returns index, stored
key, and value; `get_index_of(key)` returns the index alone;
`contains_key(key)` tests presence. Each has the obvious absent-key
result: `None` or `false`. Mutable variants `get_mut` and `get_full_mut`
give write access to the value. Indexing a map with a borrowed key
(`map[&key]`) returns the value and must panic WHEN the key is absent.

**Positional access.** `get_index(i)` returns the key-value pair at
position `i`, `get_index_mut(i)` its mutable form, and both return `None`
out of bounds. `first()` and `last()` return the pairs at the two ends
(`None` when empty), with `first_mut` / `last_mut` counterparts. Indexing
a map with a `usize` (`map[i]`) returns the value at that position and
must panic WHEN `i` is out of bounds. The `Keys` iterator also supports
`usize` indexing (`map.keys()[i]` is the key at position `i`).

## Removal and Order Surgery

This section defines the two removal laws and the operations that move
entries between positions; these laws are the heart of the contract.

**Swap removal.** `swap_remove(key)` removes the entry and moves the
*last* entry of the sequence into the vacated position, changing that one
entry's index and no other; it returns the value. `swap_remove_entry`
returns the pair, and `swap_remove_full` returns index, key, and value.
`swap_remove_index(i)` performs the same law positionally and returns the
pair, `None` out of bounds. WHEN the removed entry is itself the last one
THEN no other entry moves.

**Shift removal.** `shift_remove(key)` removes the entry and shifts every
later entry one position toward the front, preserving relative order of
the remainder; variants `shift_remove_entry`, `shift_remove_full`, and
`shift_remove_index(i)` mirror the swap family. `pop()` removes and
returns the last pair (`None` when empty).

**Deprecated aliases.** `remove(key)` and `remove_entry(key)` are
deprecated aliases with exactly the semantics of `swap_remove` and
`swap_remove_entry`; both carry deprecation attributes steering callers to
the explicit names.

**Failed removals.** WHEN no stored key matches THEN every removal
returns its absent form (`None`) and the container is unchanged.

**Reordering.** `move_index(from, to)` moves the entry at `from` so it
ends at position `to`, shifting the entries between them one step toward
the vacated side; it must panic WHEN either position is out of bounds.
`swap_indices(a, b)` exchanges the entries at two positions (a no-op when
equal) and must panic WHEN either is out of bounds. `reverse()` reverses
the whole sequence in place.

**Positioned insertion.** `shift_insert(index, key, value)` places the
key exactly at `index`: a new key is inserted there (shifting later
entries back, valid indices `0..=len`), and an existing key is moved there
with its value updated (valid indices `0..len`); the return value is the
old value or `None`. It must panic WHEN the index exceeds the valid range
for the case — in particular, `shift_insert(len, existing_key, ..)`
panics. `insert_before(index, key, value)` instead guarantees the entry
ends up *before* the entry currently at `index` (valid indices `0..=len`,
where `len` means "at the end"): for a new key the final position is
`index` itself; WHEN an existing key currently sits before `index` THEN
moving it shifts the intervening entries and its final position is
`index - 1`. It returns the final index and the old value, and must panic
WHEN `index > len`. `insert_sorted(key, value)` assumes the map is sorted
by key and inserts at the binary-search position, returning index and old
value; an existing key keeps its index and only the value changes; on an
unsorted map the position is unspecified.

## Bulk Rewrites and Merging

This section defines the operations that rewrite whole regions of the
sequence.

**Truncation and splitting.** `truncate(n)` keeps the first `n` entries
and drops the rest; WHEN `n` is at least the current length THEN it is a
no-op. `split_off(at)` removes the tail starting at `at` and returns it as
a new container of the same type with order preserved; it must panic WHEN
`at > len`.

**Draining.** `drain(range)` removes the entries in a positional range
and returns an iterator yielding them in order; the range is removed even
if the iterator is dropped early. It must panic WHEN the range end exceeds
the length or the start exceeds the end. `drain(..)` empties the
container.

**Splicing.** `splice(range, replace_with)` removes the positional range
(returning those entries through the resulting iterator, in order) and
inserts the replacement pairs in its place. WHEN a replacement key already
exists *outside* the range THEN that entry keeps its current position and
only its value is updated — the pair is not inserted into the range. WHEN
a replacement key matches a key *inside* the removed range THEN it is
inserted at the splice position like a new key (the removed entry still
comes out of the returned iterator with its old value). The range panics
follow the same law as `drain`.

**Appending and merging.** `append(&mut other)` moves every entry out of
`other` (leaving it empty, in its original capacity) into `self`,
equivalent to inserting each pair in order: new keys append at the end in
`other`'s order, and keys already present keep their position with values
updated. `extend(iterable)` applies the same per-pair insertion law, and
building from an iterator (`collect`) starts from empty with the duplicate
law of the construction section.

**Filtering.** `retain(predicate)` keeps exactly the entries for which
the predicate answers true, preserving their relative order; the map form
passes the key and a mutable value reference.

## Sorting and Ordered Search

This section defines in-place ordering and the searches that assume it.

**Stable sorts.** `sort_keys()` sorts entries by key; `sort_by(cmp)`
sorts by a caller comparison over key-value pairs;
`sort_by_cached_key(f)` sorts by a derived sort key computed once per
entry. All stable sorts must preserve the relative order of entries that
compare equal. `sorted_by(cmp)` consumes the container and returns an
iterator over the sorted pairs without mutating in place.

**Unstable sorts.** `sort_unstable_keys()`, `sort_unstable_by(cmp)`, and
`sorted_unstable_by(cmp)` produce the same multiset in a sorted order,
with the relative order of equal elements unspecified.

**Binary search.** On a sequence sorted by the relevant criterion,
`binary_search_keys(&k)` (map) returns `Ok(index)` for a present key and
`Err(insertion_index)` for an absent one; `binary_search_by(f)` and
`binary_search_by_key(&b, f)` generalize the comparison.
`partition_point(pred)` returns the index of the first entry for which
the predicate answers false, assuming the predicate is monotone over the
sequence. The set offers the same family (`sort`, `sort_by`, `sorted_by`,
`sort_unstable`, `sort_unstable_by`, `sorted_unstable_by`,
`sort_by_cached_key`, `binary_search`, `binary_search_by`,
`binary_search_by_key`, `partition_point`, `reverse`).

## Slices and Indexed Views

This section defines the borrowed positional projections of a container.

**Obtaining slices.** `as_slice()` borrows the whole sequence as a
`Slice` (`as_mut_slice()` mutably for maps); `get_range(range)` borrows a
positional sub-range and returns `None` WHEN the range is reversed or its
end exceeds the length (`get_range_mut` for maps). `into_boxed_slice()`
consumes the container into an owned boxed slice. Containers and slices
also support direct range indexing (`&map.as_slice()[1..3]`, `&set[0..2]`),
which must panic on an invalid range.

**Slice API.** A slice knows its `len` / `is_empty`, yields entries by
position (`get_index`, `first`, `last`, and `usize` indexing that returns
the map value or set value and panics out of bounds), splits
(`split_at`, `split_first`, `split_last`), iterates (`iter`, plus map
`keys` / `values` / `values_mut` / `iter_mut`, and boxed `into_keys` /
`into_values`), and searches exactly like its container
(`binary_search_keys`, `binary_search_by`, `binary_search_by_key`,
`partition_point`).

**Slice value semantics.** Slice equality, ordering (`PartialOrd` /
`Ord` lexicographic over entries), and hashing are *order-sensitive*:
two slices are equal only when the same entries appear in the same
sequence, and equal slices hash equally. Slices print with the Debug form
of an entry list (`[("a", 1), ("b", 2)]` for maps, `[3, 1]` for sets).

## The Entry Interface

This section defines the combined lookup-or-insert state machine of the
map.

**Entry.** `entry(key)` returns an `Entry` that is either `Occupied` or
`Vacant`. On either variant, `index()` reports the entry's position — for
a vacant entry, the position it *would* occupy after insertion, which is
the current length — and `key()` borrows the key. `or_insert(default)`,
`or_insert_with(f)`, `or_insert_with_key(f)`, and `or_default()` insert
the computed value only WHEN vacant and return a mutable value reference
either way. `and_modify(f)` applies `f` to the value only WHEN occupied,
then returns the entry for chaining. `insert_entry(value)` inserts or
replaces and returns an `OccupiedEntry`.

**OccupiedEntry.** Exposes `index()`, `key()`, `get()`, `get_mut()`,
`into_mut()`; `insert(value)` swaps in a new value and returns the old
one. Removal mirrors the container laws: `swap_remove()` /
`shift_remove()` return the value, `swap_remove_entry()` /
`shift_remove_entry()` return the pair, and the deprecated `remove()` /
`remove_entry()` alias the swap forms. `move_index(to)` and
`swap_indices(other)` reposition the entry with the container's panic
laws.

**VacantEntry.** Exposes `index()` (the would-be position), `key()`, and
`into_key()`; `insert(value)` appends and returns the mutable value
reference; `insert_entry(value)` appends and returns an `OccupiedEntry`;
`shift_insert(index, value)` inserts at an exact position like the
container method; `insert_sorted(value)` inserts at the binary-search
position among sorted keys and returns the index with the value
reference.

**IndexedEntry.** `get_index_entry(i)` returns an `IndexedEntry` for the
pair at a position (`None` out of bounds), with `index()`, `key()`,
`get()`, `get_mut()`, `into_mut()`, value replacement via
`insert(value)`, both removal laws (`swap_remove`, `shift_remove`,
`swap_remove_entry`, `shift_remove_entry`), and `move_index` /
`swap_indices`. `first_entry()` and `last_entry()` return the indexed
entries at the ends.

## Sets: Membership and Value Identity

This section defines the set's insertion identity laws — which stored
instance survives — and its removal families.

**Membership writes.** `insert(value)` returns `true` WHEN the value was
absent and appends it at the end; WHEN an equal value is already stored
THEN it returns `false` and the *original* stored instance is kept
unchanged. `insert_full(value)` additionally reports the index.
`replace(value)` is the complement: it keeps the position but swaps in
the *new* instance, returning the old one (`None` and an append when
absent); `replace_full` adds the index. `insert_sorted`,
`insert_before(index, value)`, and `shift_insert(index, value)` follow
exactly the map's positioned-insertion laws with boolean/new-flag returns
in place of old values.

**Membership reads.** `contains(value)` tests membership; `get(value)`
returns the stored instance; `get_full(value)` adds the index;
`get_index_of(value)` returns the index; `get_index(i)`, `first()`,
`last()`, and `usize` indexing read positionally (indexing panics out of
bounds; the accessors return `None`).

**Removal families.** `swap_remove(value)` and `shift_remove(value)`
return booleans and follow the map's two order laws; `swap_take(value)`
and `shift_take(value)` return the stored instance instead;
`swap_remove_full` / `shift_remove_full` return index and instance;
`swap_remove_index(i)` / `shift_remove_index(i)` work positionally and
return the instance. `pop()` removes and returns the last value. The
deprecated `remove(value)` and `take(value)` alias the swap forms. The
bulk surface mirrors the map: `truncate`, `split_off`, `drain`, `splice`
(replacement values colliding with values outside the range keep their
position), `append`, `extend`, `retain`, `clear`, `move_index`,
`swap_indices`, `reverse`, slices, and the sort/search family — all with
the same order laws and panic conditions.

## Set Algebra and Comparisons

This section defines the deterministic order of set operations, a
distinguishing contract of this library.

**Lazy iterators.** `intersection(&other)` yields the elements of `self`
that are also in `other`, *in `self`'s order*. `difference(&other)`
yields the elements of `self` not in `other`, in `self`'s order.
`union(&other)` yields all of `self` in order, then the elements of
`other` not in `self`, in `other`'s order.
`symmetric_difference(&other)` yields `self`'s exclusive elements in
`self`'s order, then `other`'s exclusive elements in `other`'s order.

**Operators.** `&`, `|`, `^`, and `-` on set references build new sets
whose content and order equal the corresponding lazy iterator collected.

**Predicates.** `is_subset(&other)`, `is_superset(&other)`, and
`is_disjoint(&other)` test containment relations without ordering
significance.

**Container equality.** Map equality and set equality are
*order-insensitive*: two containers are equal exactly WHEN they have the
same length and the same key-value associations (or the same members),
regardless of sequence. Order-sensitive comparison is the slices' job.
Containers implement `Clone` (preserving order) and Debug-print in
map/set notation (`{"a": 1, "b": 2}` and `{3, 1}`).

## Iteration

This section defines the iterator surface shared by both containers.

**Order and views.** All iterators traverse in sequence order: `iter()`
(pairs / values), map `iter_mut()`, `keys()`, `values()`, `values_mut()`,
and the consuming `into_keys()`, `into_values()`, and `into_iter()`.
Containers iterate by reference, by mutable reference (map), and by
value.

**Iterator contracts.** These iterators are double-ended (`next_back`
yields from the tail), exact-size (`len()` reports the remainder), and
continue to return `None` after exhaustion. `drain`, `splice`, and the
set-algebra iterators yield in the orders their sections define.

## State Model

The library's entire state is, per container, one ordered sequence of
entries plus a hash index over the keys:

1. **sequence state** — the ordered entries; changed by insertion,
   removal, reordering, bulk rewrites, and sorting; `len()` always equals
   its cardinality;
2. **hash view** — key-based reads (`get*`, `contains*`, `entry`,
   `Equivalent` lookups) resolve a key to its unique sequence position
   without ever mutating;
3. **index view** — position-based reads (`get_index*`, `first`, `last`,
   `usize` indexing, `keys()[i]`) read the sequence directly;
4. **slice view** — `as_slice` / `get_range` / boxed slices borrow
   contiguous sub-sequences with order-sensitive value semantics;
5. **algebra view** — set operations derive new sequences from two
   containers with documented order;
6. **allocation state** — capacity and hasher choice, observable only
   through `capacity()` / `hasher()` and never through any content law.

Every operation's effect on views 2-5 is fully determined by its effect
on the sequence (view 1).

## Error Semantics

| Condition | Result |
|---|---|
| Lookup / removal by absent key or value | `None` / `false`; container unchanged |
| `get_index` / `get_index_of` / positional removal out of bounds | `None` |
| `get_range` with reversed range or end beyond length | `None` |
| Map or slice indexing (`[&key]`, `[usize]`, `[range]`) with absent key / out-of-bounds index or range | panic |
| `move_index` / `swap_indices` with any position out of bounds | panic |
| `split_off(at)` with `at > len` | panic |
| `shift_insert` with index beyond `len` (new key) or beyond `len - 1` (existing key) | panic |
| `insert_before` with index beyond `len` | panic |
| `drain` / `splice` with range end beyond length or start beyond end | panic |
| `try_reserve` / `try_reserve_exact` on unsatisfiable capacity | `Err` with a `TryReserveError` |
| `truncate(n)` with `n >= len` | no-op, no error |

Absence is always expressed through `None`, `false`, or an empty
iterator; panics are reserved for positional contract violations.

## Cross-View Invariants

1. `len()` must equal `iter().count()`, `keys().count()`,
   `as_slice().len()`, and the element count of a full `drain(..)`, after
   every operation in this document.
2. For every position `i < len()`: `get_index(i)` returns the pair whose
   key `k` satisfies `get_index_of(&k) == Some(i)`, and `map[i]` equals
   that pair's value — the hash view and the index view must never
   disagree.
3. `get_full(&k)` must equal the triple assembled from `get_index_of`,
   `get_key_value`, and `get` for every present key, including the stored
   key instance (which insertion never replaces).
4. After any sequence of `swap_remove*`, `shift_remove*`, `move_index`,
   `swap_indices`, `insert_before`, `shift_insert`, and sorting calls,
   `iter()`, `keys()`, `as_slice()`, and `into_iter()` must all present
   the identical order predicted by the stated laws.
5. Two containers with equal content must compare equal regardless of
   order, while their `as_slice()` views compare equal only in matching
   order — and a sorted copy of each must then have equal slices.
6. Every set-algebra operator result (`&`, `|`, `^`, `-`) must equal its
   lazy-iterator counterpart collected into a set, in both content and
   iteration order, and each yielded element must satisfy the
   corresponding membership predicates.
7. On a map sorted by key, `binary_search_keys(&k)` must return
   `Ok(get_index_of(&k).unwrap())` for every present key and
   `Err(partition_point(|key, _| key < &k))` for every absent one.

## Public Interface

### Import Surface

```rust
// crate root
use indexmap::{IndexMap, IndexSet, Equivalent, TryReserveError};
use indexmap::{indexmap, indexset};

// map sub-surface
use indexmap::map::{Entry, OccupiedEntry, VacantEntry, IndexedEntry};
use indexmap::map::{Iter, IterMut, IntoIter, Keys, IntoKeys, Values,
                    ValuesMut, IntoValues, Drain, Splice, Slice};

// set sub-surface
use indexmap::set::{Iter as SetIter, IntoIter as SetIntoIter,
                    Drain as SetDrain, Splice as SetSplice,
                    Slice as SetSlice};
use indexmap::set::{Difference, Intersection, SymmetricDifference, Union};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `IndexMap` | struct | Ordered key-value map with hash lookup |
| `IndexSet` | struct | Ordered value set with hash lookup |
| `Equivalent` | trait | Borrowed-form key equivalence for lookups |
| `TryReserveError` | struct | Error carried by failed capacity requests |
| `indexmap!` / `indexset!` | macro | Literal constructors with the duplicate law |
| `IndexMap::new` / `with_capacity` / `with_hasher` / `with_capacity_and_hasher` | fn | Constructors |
| `IndexMap::insert` / `insert_full` | fn | Append-or-update insertion |
| `IndexMap::get` / `get_key_value` / `get_full` / `get_index_of` / `contains_key` (+ `_mut` forms) | fn | Key-view lookups |
| `IndexMap::get_index` / `first` / `last` (+ `_mut` forms) | fn | Index-view lookups |
| `IndexMap::swap_remove` / `shift_remove` (+ `_entry`, `_full`, `_index` forms) | fn | The two removal laws |
| `IndexMap::remove` / `remove_entry` | fn | Deprecated aliases of the swap forms |
| `IndexMap::pop` / `retain` / `clear` | fn | Tail removal, filtering, reset |
| `IndexMap::move_index` / `swap_indices` / `reverse` | fn | Reordering |
| `IndexMap::insert_before` / `shift_insert` / `insert_sorted` | fn | Positioned insertion |
| `IndexMap::truncate` / `split_off` / `drain` / `splice` / `append` | fn | Bulk rewrites |
| `IndexMap::sort_keys` / `sort_by` / `sorted_by` / `sort_unstable_keys` / `sort_unstable_by` / `sorted_unstable_by` / `sort_by_cached_key` | fn | Sort families |
| `IndexMap::binary_search_keys` / `binary_search_by` / `binary_search_by_key` / `partition_point` | fn | Ordered search |
| `IndexMap::as_slice` / `as_mut_slice` / `get_range` (+ `_mut`) / `into_boxed_slice` | fn | Slice projections |
| `IndexMap::entry` / `get_index_entry` / `first_entry` / `last_entry` | fn | Entry interface access |
| `IndexMap::iter` / `iter_mut` / `keys` / `values` / `values_mut` / `into_keys` / `into_values` | fn | Iteration views |
| `IndexMap::len` / `is_empty` / `capacity` / `hasher` / `reserve` / `reserve_exact` / `try_reserve` / `try_reserve_exact` / `shrink_to_fit` / `shrink_to` | fn | Size and allocation |
| `map::Entry` | enum | `Occupied` or `Vacant` lookup result |
| `map::OccupiedEntry` / `map::VacantEntry` / `map::IndexedEntry` | struct | Entry-interface handles |
| `map::Slice` / `set::Slice` | struct | Borrowed positional sub-sequence |
| `map::Iter` / `IterMut` / `IntoIter` / `Keys` / `IntoKeys` / `Values` / `ValuesMut` / `IntoValues` / `Drain` / `Splice` | struct | Map iterator types |
| `IndexSet::insert` / `insert_full` / `replace` / `replace_full` | fn | Membership writes and identity laws |
| `IndexSet::contains` / `get` / `get_full` / `get_index_of` / `get_index` / `first` / `last` | fn | Membership and positional reads |
| `IndexSet::swap_remove` / `shift_remove` / `swap_take` / `shift_take` (+ `_full`, `_index` forms) / `pop` | fn | Removal families |
| `IndexSet::remove` / `take` | fn | Deprecated aliases of the swap forms |
| `IndexSet::intersection` / `union` / `difference` / `symmetric_difference` | fn | Ordered set algebra |
| `IndexSet::is_subset` / `is_superset` / `is_disjoint` | fn | Containment predicates |
| `IndexSet::insert_before` / `shift_insert` / `insert_sorted` / `move_index` / `swap_indices` / `reverse` / `truncate` / `split_off` / `drain` / `splice` / `append` / `retain` / `sort` families / `binary_search` families / slices / capacity | fn | Mirrors of the map surface |
| `set::Iter` / `IntoIter` / `Drain` / `Splice` | struct | Set iterator types |
| `set::Difference` / `Intersection` / `SymmetricDifference` / `Union` | struct | Set-algebra iterator types |

### CLI Entry Points

There is no console script for this crate. Programmatic use is through
the Rust library API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `indexmap` with its default configuration
  providing every behavior described here; the assessment suite depends
  on the crate as `indexmap = { version = "*" }` and uses only the
  standard library besides it.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Construction and capacity: constructors, macros, array/iterator
  sources with the duplicate law, capacity neutrality, custom hashers,
  `Equivalent` lookups, try_reserve failures.
- Insertion and lookup: append-or-update law with key-instance
  preservation, the full lookup family, positional reads, indexing
  panics.
- Removal and order surgery: swap vs shift laws across all variants,
  deprecated aliases, move/swap/reverse, positioned insertion boundary
  conditions and panics, insert_sorted.
- Bulk rewrites: truncate/split_off/drain/splice (including the
  outside-range collision law), append/extend merge laws, retain.
- Sorting and search: stable vs unstable families, consuming sorts,
  binary search Ok/Err values, partition points.
- Slices: range projections and their `None` conditions, slice API,
  order-sensitive equality/ordering/hashing versus order-insensitive
  container equality.
- Entry interface: occupied/vacant state machine, index reporting,
  in-place modification, entry-level removal and repositioning, indexed
  entries.
- Sets: identity laws (insert vs replace), take families, algebra
  iteration order, operators, predicates.
- Iteration: order agreement across views, double-ended and exact-size
  contracts.

Scoring is per test at two granularities: focused behavioral tests and
multi-step workflow tests that chain several views of one container.
Sequence order beyond the documented guarantees is never asserted.
