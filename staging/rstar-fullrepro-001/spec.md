<!-- INTERNAL
task_id: rstar-fullrepro-001
spec_version: v1
delta: initial version; contract details fixed by three probe rounds against
the pinned reference: AABB corner normalization and inclusive
containment/intersection boundaries, intersection_area clamping to zero for
touching and disjoint boxes, area/perimeter_value/center/distance_2/min_point
exact arithmetic, new_empty as the merge identity with zero area and empty
from_points behavior, point-element containment as exact equality
(locate_at_point on raw points), inclusive locate_within_distance boundary,
nearest_neighbors full tie sets, nearest_neighbor_iter nondecreasing distance
order with unspecified tie order, construction-path equivalence as
multiset/distance-sequence equality (exact orders diverge on ties), drain
iterators removing only what is consumed, one-of-many removal semantics for
remove/remove_at_point/pop_nearest_neighbor, parameter verification panic
conditions (MAX_SIZE >= 4, MIN_SIZE in [1, (MAX+1)/2], REINSERTION_COUNT <
MAX-MIN, dimension >= 2), Line/Rectangle nearest-point and distance formulas,
GeomWithData/CachedEnvelope/ObjectRef forwarding laws, internal-iteration
ControlFlow protocol, node inspection invariants (leaf multiset equals
content, child envelopes contained in parent envelope)
source_boundary: docs.rs/rstar 0.12.2 (crate root guide, RTree method docs
with examples, AABB/Envelope/RTreeObject/PointDistance/Point/RTreeParams
trait docs, primitives module docs), README.md; reference behavior observed
by running the pinned checkout (probe binary, three rounds). The serde and
mint cargo features and the geo-types ecosystem integrations are excluded
from scope.
-->

# rstar Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`rstar` is an n-dimensional spatial index library built around an R*-tree.
Callers insert objects that carry an axis-aligned bounding box — points,
lines, rectangles, or custom geometries — and then ask spatial questions
about the collection: which elements lie inside a box, which envelopes
intersect a region, which element is nearest to a query point, and which
elements fall within a given distance. Queries prune whole subtrees by
their bounding boxes, so lookups run in logarithmic time on typical data
while a naive scan would be linear.

The library separates four concerns that cooperate in every query: the
`Point` abstraction (fixed-arity coordinate tuples over a signed numeric
scalar), the envelope (`AABB` arithmetic: containment, intersection,
merging, distance), the object traits (`RTreeObject` supplies an envelope;
`PointDistance` supplies a distance metric), and the tree itself (`RTree`,
with incremental insertion, bulk loading, queries, removal, and draining).
A `primitives` module supplies ready-made object types, and compile-time
parameters (`RTreeParams`) tune node sizes without changing any query
result.

The installable crate name is `rstar`.

## Non-Goals

- This specification does not require serialization support for trees,
  envelopes, or primitives.
- This specification does not require interoperability layers for
  external geometry or math libraries.
- This specification does not require any performance target: complexity
  remarks in this document are context, and only the stated observable
  results are assessed.
- This specification does not define the internal partitioning of
  elements into nodes: node fan-out, tree depth, and the assignment of
  elements to subtrees are implementation choices, constrained only by
  the inspection invariants stated below.
- This specification does not define iteration order for any query whose
  order is described as unspecified, nor which element among equally
  eligible candidates a single-result operation picks.
- This specification does not require a `no_std` build configuration.

## Representative Workflows

Three workflows illustrate construction, queries, and mutation.

**Point cloud queries.** A tree is bulk-loaded from plain coordinate
arrays, then answers box and neighborhood queries:

```rust
use rstar::{RTree, AABB};

let tree = RTree::bulk_load(vec![
    [0.0, 0.0], [2.0, 0.0], [0.0, 2.0], [2.0, 2.0], [1.0, 1.0], [5.0, 5.0],
]);

let unit = AABB::from_corners([0.0, 0.0], [2.0, 2.0]);
assert_eq!(tree.locate_in_envelope(&unit).count(), 5);   // corners included

assert_eq!(tree.nearest_neighbor(&[4.0, 4.0]), Some(&[5.0, 5.0]));
assert_eq!(tree.locate_within_distance([0.0, 0.0], 2.0).count(), 2);
```

**Geometries with attached data.** `GeomWithData` pairs a geometry with a
payload; the payload rides along through every query:

```rust
use rstar::RTree;
use rstar::primitives::GeomWithData;

type Station = GeomWithData<[f64; 2], &'static str>;

let mut network = RTree::new();
network.insert(Station::new([0.0, 0.0], "central"));
network.insert(Station::new([5.0, 5.0], "airport"));

let nearest = network.nearest_neighbor(&[1.0, 1.0]).unwrap();
assert_eq!(nearest.data, "central");
assert_eq!(network.size(), 2);
```

**Custom objects with a custom metric.** Any type gains tree support by
implementing `RTreeObject`; implementing `PointDistance` unlocks metric
queries:

```rust
use rstar::{PointDistance, RTree, RTreeObject, AABB};

struct Circle { origin: [f64; 2], radius: f64 }

impl RTreeObject for Circle {
    type Envelope = AABB<[f64; 2]>;
    fn envelope(&self) -> Self::Envelope {
        AABB::from_corners(
            [self.origin[0] - self.radius, self.origin[1] - self.radius],
            [self.origin[0] + self.radius, self.origin[1] + self.radius],
        )
    }
}

impl PointDistance for Circle {
    fn distance_2(&self, point: &[f64; 2]) -> f64 {
        let dx = self.origin[0] - point[0];
        let dy = self.origin[1] - point[1];
        let gap = (dx * dx + dy * dy).sqrt() - self.radius;
        let gap = gap.max(0.0);
        gap * gap                       // squared distance to the boundary
    }
}

let tree = RTree::bulk_load(vec![
    Circle { origin: [0.0, 0.0], radius: 1.0 },
    Circle { origin: [10.0, 0.0], radius: 2.0 },
]);
// distance is measured by the object's own metric:
assert_eq!(tree.nearest_neighbor(&[7.0, 0.0]).unwrap().origin, [10.0, 0.0]);
```

## Points, Scalars, and Object Traits

This section defines the coordinate layer and the two traits every stored
object provides.

**Scalars.** A coordinate scalar implements `RTreeNum`: a signed numeric
type that is bounded, copyable, orderable, and debug-printable. Both
integer scalars (such as 32-bit and 64-bit signed integers) and
floating-point scalars (32-bit and 64-bit) must be usable; all envelope
and distance arithmetic below is exact in the scalar's own arithmetic.

**Points.** A point implements `Point`, which fixes an associated
`Scalar` type, a compile-time `DIMENSIONS` count, a `generate(generator)`
constructor that obtains each coordinate by calling the generator with
the dimension index, and per-dimension accessors `nth(index)` /
`nth_mut(index)`. Fixed-size arrays of any arity of at least two are
points, and fixed-arity tuples of one scalar type are points. Custom
point types are supported by implementing the trait. WHEN a tree is
created over a point type with fewer than two dimensions THEN
construction must panic (dimension verification).

**Objects.** A stored object implements `RTreeObject` by choosing an
`Envelope` type and returning its own envelope from `envelope()`. The
envelope of an object must not change while the object is inserted in a
tree; the library treats a changing envelope as a caller logic error
without any defined behavior. Points themselves are objects: a bare point
is its own zero-extent envelope.

**Distance metrics.** An object additionally implements `PointDistance`
to enable metric queries. `distance_2(point)` returns the *squared*
distance from the object to a point in the object's own metric.
`contains_point(point)` returns whether the point lies on or inside the
object; without an explicit implementation it must default to
`distance_2(point) <= 0`. `distance_2_if_less_or_equal(point, max_d2)`
returns `Some(distance_2)` WHEN the squared distance is at most `max_d2`
and `None` otherwise; without an explicit implementation it must first
prune using the envelope distance, then fall back to the exact metric.
For bare points, the metric is the squared Euclidean distance, and
`contains_point` is exact coordinate equality — a query point strictly
inside no stored point but numerically distinct from all of them
matches nothing.

## Envelopes and AABB Arithmetic

This section defines the axis-aligned bounding box, the only shipped
envelope, whose arithmetic drives every tree decision.

**Construction.** `AABB::from_point(p)` returns the zero-extent box whose
lower and upper corners are both `p`. `AABB::from_corners(p1, p2)`
accepts its corners in any order and normalizes them: `lower()` returns
the componentwise minimum and `upper()` the componentwise maximum.
`AABB::from_points(iterator)` folds point references into the smallest
box containing them all; WHEN the iterator is empty THEN the result
equals `AABB::new_empty()`. The empty envelope contains no point, has
zero `area()`, and is the identity of merging: `new_empty().merged(&b)`
must equal `b` for every box `b`.

**Containment and intersection.** `contains_point(p)` is inclusive: a
point on a face or corner is contained. `contains_envelope(other)`
returns whether `other` lies entirely within `self`, boundaries included.
`intersects(other)` is also inclusive — two boxes sharing only a face or
a corner intersect. `merge(&other)` grows `self` in place to cover
`other`; `merged(&other)` returns the grown copy without mutating.

**Measures.** `area()` returns the product over dimensions of the side
lengths, clamping each side at zero (an empty box reports zero area, and
a zero-extent box reports zero area). `intersection_area(other)` returns
the area of the overlap region; WHEN the boxes only touch or do not
intersect THEN it returns zero. `center()` returns the componentwise
midpoint of the corners. `perimeter_value()` returns a value proportional
to the perimeter: the sum of the side lengths, clamped at zero — a box
spanning `[1, -1]` to `[3, 4]` reports `7`.

**Point distance.** `min_point(p)` returns the point inside the box
closest to `p` — `p` itself WHEN `p` is contained, otherwise `p` clamped
componentwise to the box. `distance_2(p)` returns the squared Euclidean
distance from `p` to `min_point(p)`, hence zero for contained points.
`min_max_dist_2(p)` returns the squared "min-max" bound used by
nearest-neighbor pruning: the smallest, over dimensions, of the squared
distance to the box's farthest corner when that dimension is clamped to
its nearer face; its value must equal the plain squared distance to the
equivalent min-max corner point.

**Value semantics.** `AABB` values are copyable, comparable for equality
and order, and hashable; two boxes constructed from the same corner pair
in either order compare equal. The `Envelope` trait names this contract
(`new_empty`, `contains_point`, `contains_envelope`, `merge`, `merged`,
`intersects`, `intersection_area`, `area`, `distance_2`,
`min_max_dist_2`, `center`, `perimeter_value`, plus envelope sorting and
partitioning hooks used by tree construction); it is implemented by
`AABB` and is not designed for caller implementations.

## Tree Construction and Population

This section defines how trees are created and what the population
counters report.

**Constructors.** `RTree::new()` returns an empty tree over the default
parameters; the `Default` implementation is equivalent.
`RTree::bulk_load(elements)` consumes a vector and builds a tree
containing exactly those elements, duplicates included.
`RTree::new_with_params()` and `RTree::bulk_load_with_params(elements)`
do the same over caller-chosen parameters. A bulk load of an empty
vector returns an empty tree.

**Parameters.** A parameter type implements `RTreeParams` with three
associated constants — `MIN_SIZE`, `MAX_SIZE`, `REINSERTION_COUNT` — and
an insertion strategy type (`RStarInsertionStrategy`, the only shipped
strategy, selected by `DefaultParams` whose values are minimum 3,
maximum 6, reinsertion count 2). Parameters change performance
characteristics only: every query result described in this document must
be identical under any valid parameter set. WHEN a tree is constructed
with `MAX_SIZE` less than 4, with `MIN_SIZE` of zero, with `MIN_SIZE`
exceeding half of `MAX_SIZE` rounded up, or with `REINSERTION_COUNT` not
smaller than `MAX_SIZE - MIN_SIZE` THEN construction must panic. The
`InsertionStrategy` trait is public vocabulary but is not designed for
caller implementations.

**Population.** `size()` returns the number of stored elements, counting
duplicates. Inserting an element already present stores it a second
time. `contains(&element)` returns whether some stored element compares
equal (`==`) to the argument; it requires element equality and is only
correct when equal elements share equal envelopes. `iter()` visits every
stored element exactly once in unspecified order; `iter_mut()` is the
mutable variant. Trees iterate by reference, by mutable reference, and
by value: consuming a tree yields its elements.

**Construction-path equivalence.** A tree built by `bulk_load` and a
tree built by inserting the same elements one at a time must agree on
every query in this document up to the stated order guarantees: equal
result multisets for set-valued queries, equal distance sequences for
distance-ordered queries, and equal single results wherever the result
is uniquely determined. Only the relative order of equally distant
elements is allowed to differ between the two construction paths.

## Spatial Queries

This section defines the box- and predicate-driven selection surface.
All query iterators return elements in unspecified order.

**Point location.** `locate_at_point(&p)` returns one element whose
`contains_point(p)` holds, or `None`; WHEN several elements contain `p`
THEN any one of them is returned. `locate_all_at_point(&p)` returns all
of them. Both have mutable variants (`locate_at_point_mut`,
`locate_all_at_point_mut`) through which an element's non-spatial data
is mutated in place.

**Box containment.** `locate_in_envelope(&envelope)` returns the
elements whose envelopes are *fully contained* in the query box,
boundaries included: a point element lying on the query box's face or
corner is contained. `locate_in_envelope_intersecting(&envelope)`
returns the elements whose envelopes intersect the query box, including
elements that merely touch it and elements fully inside it. Both have
`_mut` variants.

**Metric selection.** `locate_within_distance(query_point, max_d2)`
returns every element whose squared distance to `query_point` (by the
object's `PointDistance` metric) is less than or equal to `max_d2` — the
boundary is inclusive.

**Internal iteration.** Every location query has a callback variant
suffixed `_int` (and `_int_mut`) that drives the traversal internally:
the visitor receives each selected element and returns a `ControlFlow`;
WHEN the visitor returns `Break(value)` THEN traversal stops immediately
and the method returns `Break(value)`; WHEN the visitor always continues
THEN the method returns `Continue(())` after visiting every selected
element. `locate_at_point_int` / `locate_at_point_int_mut` return
`Option` directly, resolving to the first containing element found or
`None`.

**Custom selection.** A caller-defined search implements
`SelectionFunction<T>` with `should_unpack_parent(&envelope)` — whether
a subtree whose envelope is given can contain matches — and an optional
`should_unpack_leaf(&element)` refinement that defaults to accepting
every leaf. `locate_with_selection_function(function)` iterates over
exactly the elements for which both hooks answer true, provided the
parent hook is consistent with the leaf hook (a selection function that
prunes a subtree containing matches loses them; this is the caller's
contract). A mutable variant exists.

**Cross-tree candidates.** `intersection_candidates_with_other_tree(&other)`
iterates over every pair `(a, b)` — `a` from `self`, `b` from `other` —
whose *envelopes* intersect. No geometric intersection test beyond the
envelope test is performed. The element types of the two trees are
allowed to differ as long as they share one envelope type.

## Nearest-Neighbor Queries

This section defines the distance-ordered query surface, driven entirely
by `PointDistance::distance_2`.

**Single neighbor.** `nearest_neighbor(&query)` returns an element with
minimal squared distance, or `None` WHEN the tree is empty. WHEN several
elements tie for minimal distance THEN any one of them is returned.

**Tie sets.** `nearest_neighbors(&query)` returns a vector of *all*
elements whose distance equals the minimum — every returned element has
exactly the same squared distance to the query — and an empty vector for
an empty tree. The set of returned elements must not depend on how the
tree was constructed.

**Ordered iteration.** `nearest_neighbor_iter(&query)` yields every
stored element exactly once, in nondecreasing order of squared distance;
the relative order of equally distant elements is unspecified.
`nearest_neighbor_iter_with_distance_2(&query)` yields
`(element, squared_distance)` pairs in the same order, and the reported
distance must equal the element's own `distance_2(query)`. The method
`nearest_neighbor_iter_with_distance` is a deprecated alias with the
identical contract.

**Destructive neighbor.** `pop_nearest_neighbor(&query)` removes a
nearest element and returns it by value, `None` on an empty tree. WHEN
several elements tie THEN exactly one of them — any one — is removed.
Repeated popping drains the tree in nondecreasing distance order.

## Mutation and Removal

This section defines the operations that change the stored multiset and
their bookkeeping.

**Insertion.** `insert(element)` adds one element under the tree's
insertion strategy and increments `size()` by one. Duplicate insertions
accumulate: each stored copy is independently locatable and removable.

**Single removal.** `remove(&element)` removes and returns one stored
element equal (`==`) to the argument, or returns `None` WHEN no stored
element compares equal; WHEN duplicates exist THEN exactly one copy is
removed per call. `remove_at_point(&p)` removes and returns one element
containing `p` (by `contains_point`), or `None`.
`remove_with_selection_function(function)` removes and returns one
element accepted by a `SelectionFunction`, or `None` WHEN nothing
matches. Each successful removal decrements `size()` by exactly one.

**Draining.** `drain_with_selection_function(function)` returns an
iterator that removes each selected element as it is yielded — removal
is lazy: WHEN the iterator is dropped after yielding some elements THEN
only the yielded elements have been removed, and the remaining selected
elements stay in the tree. `drain()` drains everything;
`drain_in_envelope(envelope)` drains elements fully contained in a box;
`drain_in_envelope_intersecting(envelope)` drains elements whose
envelopes intersect a box; `drain_within_distance(query, max_d2)` drains
elements within an inclusive squared distance. Fully consuming a drain
iterator leaves `size()` reduced by exactly the number of yielded
elements, and the drained elements are returned by value.

## Tree Inspection

This section defines the read-only structural view offered for advanced
algorithms.

**Nodes.** `root()` returns the root `ParentNode`. A `ParentNode`
exposes `children()` — a slice of `RTreeNode` values — and `envelope()`.
An `RTreeNode` is either `Leaf(element)` or `Parent(parent_node)`, and
`is_leaf()` reports which. The root of an empty tree has no children and
an empty envelope.

**Structural invariants.** The multiset of `Leaf` elements reachable
from the root must equal the multiset of stored elements. Every node's
envelope must contain the envelopes of all its children (for a leaf, the
element's envelope; for a parent, that node's envelope), and the root's
envelope must equal the minimal merged envelope of all stored elements.
Node fan-out, depth, and the grouping of elements into subtrees are
otherwise unspecified.

## Geometric Primitives

This section defines the ready-made object types in the `primitives`
module. All of them implement `RTreeObject` and `PointDistance` and are
insertable.

**Line.** A `Line` is constructed from two endpoint points, exposed as
public fields `from` and `to`. Its envelope is the corner-normalized box
of the endpoints. `length_2()` returns the squared endpoint distance.
`nearest_point(&query)` returns the point on the segment closest to the
query — an interior projection point WHEN the perpendicular foot lies
within the segment, otherwise the nearer endpoint. `distance_2(&query)`
returns the squared distance to that nearest point.

**Rectangle.** A `Rectangle` is a solid axis-aligned box as a tree
element. `from_corners(c1, c2)` normalizes its corners like an envelope
does; `from_aabb(aabb)` and the `From<AABB>` conversion wrap an existing
envelope; `lower()` and `upper()` report the normalized corners.
`nearest_point(&query)` returns the query itself WHEN contained,
otherwise the componentwise clamp onto the box; `distance_2` is the
squared distance to that point, zero for contained points. Envelope
boxes themselves are not tree elements; a `Rectangle` is the insertable
counterpart.

**Attached data.** `GeomWithData` wraps a geometry together with a
payload: `new(geom, data)` constructs it, the payload is the public
field `data`, and `geom()` borrows the geometry. Envelope and distance
calls forward to the wrapped geometry, so queries are driven by the
geometry alone while the payload rides along (and is mutable through the
`_mut` query surface). `PointWithData` is the deprecated
point-restricted predecessor: `new(data, point)` constructs it (the
constructor itself carries a deprecation attribute), `data` is public,
and `position()` borrows the point.

**Envelope caching.** `CachedEnvelope` wraps an object and computes its
envelope once at construction: `new(inner)` captures the envelope,
envelope queries return the cached copy, and the wrapper dereferences to
the inner object. Distance calls forward to the inner object.

**By-reference storage.** `ObjectRef` wraps a shared reference to an
object living outside the tree: `new(&inner)` constructs it, envelope
and distance calls forward to the referent, and the wrapper dereferences
to it. Trees of `ObjectRef` values answer every query exactly as a tree
of the referents would.

## State Model

The library's entire state is one multiset of elements per tree, indexed
by envelopes:

1. **content state** — the stored element multiset, changed only by
   `insert`, the `remove_*` family, the `drain_*` family,
   `pop_nearest_neighbor`, and by-value iteration; `size()` always
   equals its cardinality;
2. **selection projection** — `iter`, the `locate_*` family, and custom
   selection functions enumerate subsets of the content, without ever
   inventing or duplicating elements;
3. **metric projection** — the `nearest_neighbor*` family and
   `locate_within_distance` order or filter the same content by
   `PointDistance::distance_2`;
4. **structural projection** — `root()` exposes a node hierarchy whose
   leaves are exactly the content and whose envelopes are merged
   summaries of it;
5. **envelope algebra** — `AABB` values are pure: no envelope operation
   reads or mutates tree state.

Compile-time parameters select node-size bounds and the insertion
strategy at construction; they are not observable through any query
result.

## Error Semantics

| Condition | Result |
|---|---|
| Tree constructed with `MAX_SIZE` < 4 | panic (parameter verification) |
| Tree constructed with `MIN_SIZE` = 0 | panic (parameter verification) |
| Tree constructed with `MIN_SIZE` > (`MAX_SIZE`+1)/2 | panic (parameter verification) |
| Tree constructed with `REINSERTION_COUNT` >= `MAX_SIZE` - `MIN_SIZE` | panic (parameter verification) |
| Tree constructed over a point type with fewer than 2 dimensions | panic (dimension verification) |
| `nearest_neighbor` / `pop_nearest_neighbor` on an empty tree | `None` |
| `nearest_neighbors` on an empty tree | empty vector |
| `remove` / `remove_at_point` / `remove_with_selection_function` with no match | `None`; tree unchanged |
| `locate_at_point` with no containing element | `None` |

Queries never panic on an empty tree, and no query allocates an error
type: absence is always expressed through `None`, an empty vector, or an
empty iterator.

## Cross-View Invariants

1. `size()` must equal `iter().count()`, the number of leaves reachable
   from `root()`, and the element count of a full `drain()`, at every
   point in any insert/remove sequence.
2. For every element `e` in a tree, `locate_in_envelope(&e.envelope())`
   must yield `e` (envelope queries are inclusive of their boundaries),
   and `root()`'s envelope must contain `e.envelope()`.
3. `nearest_neighbor(&q)` must return an element whose `distance_2(q)`
   equals the first distance yielded by
   `nearest_neighbor_iter_with_distance_2(&q)`, and that iterator's
   distance sequence must be nondecreasing and identical for a
   bulk-loaded and an incrementally built tree over the same elements.
4. Every element yielded by `locate_within_distance(q, m)` must satisfy
   `distance_2(q) <= m`, and the yielded set must equal the set of
   elements of `nearest_neighbor_iter(&q)` taken while their distance is
   at most `m`.
5. A successful `remove`-family call must decrement `size()` by exactly
   one and reduce the multiset by exactly the returned element; a failed
   one must leave every query result unchanged.
6. A partially consumed drain iterator must remove exactly the yielded
   elements: after yielding `k` of `n` selected elements and being
   dropped, `size()` has decreased by `k` and the other `n - k` selected
   elements are still locatable.
7. Wrapper primitives must be query-transparent: a tree of
   `CachedEnvelope`/`ObjectRef`/`GeomWithData` wrappers must produce the
   same envelopes, distances, and query outcomes as the wrapped
   geometries produce directly.

## Public Interface

### Import Surface

```rust
// crate root
use rstar::{RTree, AABB, Envelope};
use rstar::{RTreeObject, PointDistance, SelectionFunction};
use rstar::{RTreeParams, DefaultParams, InsertionStrategy, RStarInsertionStrategy};
use rstar::{Point, RTreeNum};
use rstar::{ParentNode, RTreeNode};

// ready-made object types
use rstar::primitives::{Line, Rectangle, GeomWithData, PointWithData,
                        CachedEnvelope, ObjectRef};

// iterator types (return types of the query surface)
use rstar::iterators::{RTreeIterator, RTreeIteratorMut, LocateAllAtPoint,
                       LocateAllAtPointMut, LocateInEnvelope, LocateInEnvelopeMut,
                       LocateInEnvelopeIntersecting, LocateInEnvelopeIntersectingMut,
                       LocateWithinDistanceIterator, SelectionIterator,
                       SelectionIteratorMut, DrainIterator, IntersectionIterator,
                       IntoIter};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `RTree` | struct | The spatial index over one element multiset |
| `RTree::new` / `new_with_params` | fn | Empty-tree constructors |
| `RTree::bulk_load` / `bulk_load_with_params` | fn | Vector-consuming constructors |
| `RTree::size` / `iter` / `iter_mut` / `contains` | fn | Population access |
| `RTree::insert` | fn | Single insertion |
| `RTree::locate_at_point` / `locate_all_at_point` (+ `_mut`, `_int`, `_int_mut`) | fn | Point-containment queries |
| `RTree::locate_in_envelope` / `locate_in_envelope_intersecting` (+ `_mut`, `_int`, `_int_mut`) | fn | Box queries |
| `RTree::locate_within_distance` | fn | Inclusive metric filter |
| `RTree::locate_with_selection_function` (+ `_mut`) | fn | Custom searches |
| `RTree::nearest_neighbor` / `nearest_neighbors` | fn | Minimal-distance queries |
| `RTree::nearest_neighbor_iter` / `nearest_neighbor_iter_with_distance_2` / `nearest_neighbor_iter_with_distance` | fn | Distance-ordered iteration |
| `RTree::pop_nearest_neighbor` | fn | Destructive nearest query |
| `RTree::remove` / `remove_at_point` / `remove_with_selection_function` | fn | Single removals |
| `RTree::drain` / `drain_in_envelope` / `drain_in_envelope_intersecting` / `drain_within_distance` / `drain_with_selection_function` | fn | Lazy removing iterators |
| `RTree::intersection_candidates_with_other_tree` | fn | Cross-tree envelope pairs |
| `RTree::root` | fn | Structural inspection entry |
| `AABB` | struct | Axis-aligned bounding box |
| `AABB::from_point` / `from_corners` / `from_points` | fn | Envelope constructors |
| `AABB::lower` / `upper` / `center` | fn | Corner and midpoint access |
| `AABB::min_point` / `distance_2` | fn | Point-distance arithmetic |
| `Envelope` | trait | Envelope algebra contract (implemented by `AABB`) |
| `RTreeObject` | trait | Envelope supplier for insertable types |
| `PointDistance` | trait | Squared-distance metric for metric queries |
| `SelectionFunction` | trait | Caller-defined search predicate |
| `RTreeParams` | trait | Compile-time node-size parameters |
| `DefaultParams` | struct | Default parameters (min 3, max 6, reinsertion 2) |
| `InsertionStrategy` | trait | Insertion strategy vocabulary |
| `RStarInsertionStrategy` | struct | The shipped insertion strategy |
| `Point` | trait | Fixed-arity coordinate abstraction |
| `RTreeNum` | trait | Scalar bound for coordinates |
| `ParentNode` | struct | Inner node: children + envelope |
| `RTreeNode` | enum | `Leaf(element)` or `Parent(node)` |
| `Line` | struct | Segment primitive with endpoints `from`/`to` |
| `Rectangle` | struct | Solid-box primitive |
| `GeomWithData` | struct | Geometry with attached payload `data` |
| `PointWithData` | struct | Deprecated point-with-payload predecessor |
| `CachedEnvelope` | struct | Envelope-caching wrapper |
| `ObjectRef` | struct | By-reference element wrapper |
| `RTreeIterator` / `SelectionIterator` / `DrainIterator` / `IntersectionIterator` / `IntoIter` (+ aliases) | struct/type | Query and drain iterator types |

### CLI Entry Points

There is no console script for this crate. Programmatic use is through
the Rust library API.

## Appendix A: Environment

- Language: Rust, edition 2018 or later (toolchain 1.83; the crate's
  declared minimum supported Rust version must not exceed it).
- The crate must build as `rstar` with its default configuration
  providing every behavior described here; the assessment suite depends
  on the crate as `rstar = { version = "*" }` and uses only the standard
  library besides it.
- Tests are run with cargo-nextest; each test runs in its own process.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Envelope algebra: corner normalization, inclusive containment and
  intersection, merge identity and empty-envelope laws, area and
  intersection-area clamping, center/perimeter arithmetic, point
  clamping and squared distances, min-max distance consistency, value
  semantics (equality, ordering, hashing).
- Construction and population: constructors with default and custom
  parameters, duplicate accounting, parameter-verification panics,
  dimension panics, construction-path equivalence up to tie order.
- Spatial queries: point location by containment (exact equality for
  bare points), contained-in-box vs intersecting-box selection with
  boundary cases, inclusive within-distance filtering, internal
  iteration with early break, custom selection functions, cross-tree
  intersection candidates.
- Nearest neighbors: single results, exact tie sets, nondecreasing
  distance iteration with per-element distance agreement, destructive
  popping.
- Mutation: one-of-many removal semantics across the removal family,
  drain laziness and bookkeeping, mutation through the `_mut` surface.
- Inspection: leaf/content agreement, envelope containment up the tree,
  root envelope minimality, empty-tree structure.
- Primitives: segment and box geometry (nearest points, squared
  distances, envelopes), payload attachment, wrapper transparency, and
  custom object/metric implementations driving every query family.

Scoring is per test at two granularities: focused behavioral tests and
multi-step workflow tests that chain several projections. Iteration
order beyond the documented guarantees is never asserted.
