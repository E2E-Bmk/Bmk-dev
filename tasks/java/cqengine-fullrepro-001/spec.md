# CQEngine Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cqengine` is a Java collection-query library that stores application objects in a `Set`-compatible collection, maintains attribute indexes as the collection changes, and evaluates typed predicates into closeable result views.

The same live object population is projected through collection membership, query results, registered indexes, index statistics, transaction snapshots, ordering and deduplication options, and optional local disk persistence. The Maven artifact is `com.googlecode.cqengine:cqengine`.

## Non-Goals

- This specification does not require SQL or CQN text parsers, generated grammar types, joins between collections, entity-map adapters, source or bytecode attribute generation, reflective attributes, or JVM-language-specific adapters.
- This specification does not require compound, partial, radix, suffix, inverted-radix, reversed-radix, quantized, off-heap, wrapping, or composite persistence features.
- This specification does not require `ObjectLockingIndexedCollection`, custom index-map factories, custom object stores, support-package iterators, internal query-engine types, or subclass extension hooks.
- This specification does not define exact retrieval-cost or merge-cost constants, index-selection algorithms, threshold heuristics, serialization format, SQLite schema, lock layout, or internal version numbers.
- This specification does not require disk-size reporting, preallocation, compaction, or database-property tuning.
- This specification does not require performance thresholds, synthetic throughput workloads, network access, external services, or concurrent timing assertions.
- This specification does not define exact exception messages, log text, `toString()` output, generated attribute names, iteration order when no ordering option is supplied, or tie order after all requested sort keys compare equal.
- This specification does not require Maven plugin goals, an executable main class, or a command-line application.

## Representative Workflows

The first workflow creates an application-defined attribute, indexes it, retrieves matching objects, and reads the same distribution through metadata.

```java
IndexedCollection<Book> books = new ConcurrentIndexedCollection<>();
books.addIndex(HashIndex.onAttribute(Book.AUTHOR));
books.addAll(List.of(first, second, third));

try (ResultSet<Book> result = books.retrieve(equal(Book.AUTHOR, "Ada"))) {
    result.forEach(System.out::println);
}
AttributeMetadata<String, Book> metadata =
    books.getMetadataEngine().getAttributeMetadata(Book.AUTHOR);
long distinctAuthors = metadata.getCountOfDistinctKeys();
```

This workflow introduces the collection, query-result, index, and metadata views whose synchronization rules are specified below.

The second workflow performs one atomic replacement and reads a committed snapshot.

```java
TransactionalIndexedCollection<Book> books =
    new TransactionalIndexedCollection<>(Book.class);
books.addAll(List.of(first, second));
books.update(List.of(second), List.of(revisedSecond));

try (ResultSet<Book> result = books.retrieve(all(Book.class))) {
    Set<Book> committed = result.stream().collect(Collectors.toSet());
}
```

This workflow introduces the atomic-replacement and snapshot lifecycle whose rules are specified below.

The third workflow persists a collection in a caller-selected local file and reopens it through a new collection instance.

```java
DiskPersistence<Book, Integer> store =
    DiskPersistence.onPrimaryKeyInFile(Book.ID, file);
IndexedCollection<Book> firstView = new ConcurrentIndexedCollection<>(store);
firstView.addAll(List.of(first, second));
store.close();

DiskPersistence<Book, Integer> reopened =
    DiskPersistence.onPrimaryKeyInFile(Book.ID, file);
IndexedCollection<Book> secondView = new ConcurrentIndexedCollection<>(reopened);
```

This workflow introduces the close, reopen, and disk-index lifecycle whose rules are specified below.

## Attributes and Query Predicates

This section defines how application objects expose typed values and how those values are matched by programmatic queries.

**Attribute projections.**

- WHEN `Attribute.getObjectType()`, `getAttributeType()`, or `getAttributeName()` is called, THEN it must return the object type, value type, or name configured for that attribute.
- WHEN `SimpleAttribute.getValues(object, queryOptions)` is called, THEN it must return exactly the single non-null value produced by `getValue`.
- WHEN `SimpleNullableAttribute.getValue` returns null, THEN `getValues` must return an empty iterable; otherwise it must return a singleton iterable.
- WHEN `MultiValueAttribute.getValues` is called, THEN it must return the non-null iterable supplied by the application-defined attribute.
- WHEN `MultiValueNullableAttribute.getNullableValues` returns null, THEN `getValues` must return an empty iterable.
- WHERE `componentValuesNullable` is true, `MultiValueNullableAttribute.getValues` must omit null components while preserving the non-null component order.
- WHEN `selfAttribute(objectType)` is used, THEN the resulting `SelfAttribute` must expose each queried object as its own single value.
- WHEN an `attribute` or `nullableAttribute` overload receives explicit object and value classes, THEN the resulting functional attribute must report those classes and invoke the supplied function for values.
- IF a functional-attribute overload without explicit classes cannot resolve its generic types, THEN attribute construction must raise `IllegalStateException`.

**Scalar and range predicates.**

- WHEN `equal(attribute, value)` is evaluated, THEN an object must match if at least one projected attribute value equals `value`.
- WHEN `in(attribute, values)` is evaluated, THEN an object must match if at least one projected attribute value belongs to the supplied set.
- WHEN `in` receives no values, THEN it must return a query that matches no objects.
- WHEN `in` receives one value, THEN it must return behavior equivalent to `equal`.
- WHEN `lessThan`, `lessThanOrEqualTo`, `greaterThan`, or `greaterThanOrEqualTo` is evaluated, THEN an object must match according to the named exclusive or inclusive comparison against at least one projected value.
- WHEN `between` is created without inclusivity flags, THEN both bounds must be inclusive.
- WHEN `between` receives `lowerInclusive` and `upperInclusive`, THEN each boundary must be included exactly when its corresponding flag is true.
- WHEN `has(attribute)` is evaluated, THEN an object must match if the attribute projects at least one non-null value.
- WHEN `all(objectType)` or `none(objectType)` is evaluated, THEN it must match every object or no object respectively.
- IF a simple or comparative query receives a null attribute, THEN construction must raise `IllegalArgumentException`.
- IF an equality, range, or string query receives a null query value, THEN construction must raise `NullPointerException`.
- IF `in(attribute, collection)` receives a null collection, THEN construction must raise `NullPointerException`.

**String predicates.**

- WHEN `startsWith`, `endsWith`, or `contains` is evaluated, THEN matching must be case-sensitive and must use the corresponding `CharSequence` prefix, suffix, or contiguous-fragment rule.
- WHEN an empty fragment is supplied to `startsWith`, `endsWith`, or `contains`, THEN every non-null character sequence must match, including an empty sequence.
- WHEN `isContainedIn(attribute, container)` is evaluated, THEN an object must match if at least one projected character sequence occurs contiguously inside `container`.
- WHEN `isPrefixOf(attribute, container)` is evaluated, THEN an object must match if at least one projected character sequence is a prefix of `container`.
- WHEN `matchesRegex` is evaluated, THEN an object must match if at least one entire projected character sequence matches the supplied Java regular expression.
- IF the string overload of `matchesRegex` receives invalid regular-expression syntax, THEN it must raise `PatternSyntaxException`.

**Logical composition.**

- WHEN `and` is evaluated, THEN an object must match only if every child query matches it.
- WHEN `or` is evaluated, THEN an object must match if at least one child query matches it.
- WHEN `not` is evaluated, THEN an object must match exactly when its child query does not match it.
- WHEN `Query.matches(object, queryOptions)` is called, THEN it must apply the same predicate semantics used by collection retrieval.
- IF a logical query receives a null child-query collection or `not` receives a null child query, THEN construction must raise `NullPointerException`.

## Indexed Collection and Index Maintenance

This section defines the set-compatible mutable population and the indexes that remain synchronized with it.

**Collection behavior.**

- WHEN `ConcurrentIndexedCollection` is created without a persistence argument, THEN it must use `OnHeapPersistence.withoutPrimaryKey()` and begin empty.
- WHEN standard `Set` operations add, remove, retain, or clear objects, THEN `IndexedCollection` must return the standard mutation result and expose the resulting unique membership through `size`, `contains`, iteration, and array views.
- WHEN `update(objectsToRemove, objectsToAdd)` completes, THEN it must apply the requested removals and additions and must return true exactly when collection membership changed.
- WHEN `retrieve(query)` is called, THEN it must behave as `retrieve(query, noQueryOptions())` and return a `ResultSet` over matching collection objects.
- IF `retrieve` receives a null query, THEN it must raise `IllegalStateException` before returning a result.

**Index lifecycle.**

- WHEN `addIndex(index)` completes, THEN the index must contain the relevant values of objects already present and must appear in `getIndexes()`.
- WHILE an index is registered, every successful collection mutation must update that index before the mutating call returns.
- WHEN `removeIndex(index)` completes, THEN the index must disappear from `getIndexes()` and later retrieval must remain behaviorally correct through other indexes or fallback evaluation.
- WHEN no registered index supports a query, THEN retrieval must still return the same matching objects through fallback evaluation.
- IF an index is incompatible with the collection persistence, THEN `addIndex` must raise `IllegalStateException`.

**Included index families.**

- WHEN `HashIndex.onAttribute(attribute)` is registered, THEN it must support `equal`, `in`, and `has` queries for that attribute and provide unsorted key statistics.
- WHEN `NavigableIndex.onAttribute(attribute)` is registered, THEN it must support equality, membership, presence, less-than, greater-than, and between queries and provide sorted key statistics.
- WHEN `UniqueIndex.onAttribute(attribute)` is registered, THEN each indexed attribute value must identify at most one unequal object while supporting equality and membership queries.
- IF a `UniqueIndex` observes the same indexed value on two unequal objects, THEN the triggering registration or mutation must raise `UniqueIndex.UniqueConstraintViolatedException`.
- WHEN `StandingQueryIndex.onQuery(query)` is registered, THEN retrieval of that same query or matching query fragment must preserve the ordinary predicate result while the collection changes.
- WHEN `DiskIndex.onAttribute(attribute)` is registered on a disk-persisted collection, THEN it must support the same equality, membership, presence, and range query families as `NavigableIndex`.

## Result Views, Deduplication, and Ordering

This section defines the observable result view, duplicate policy, ordering options, and resource lifecycle.

**Result-set operations.**

- WHEN a `ResultSet` is iterated, THEN it must yield objects matching its `getQuery()` under its `getQueryOptions()`.
- WHEN `size`, `isEmpty`, or `isNotEmpty` is called, THEN it must describe the objects that iteration of the same result would yield.
- WHEN `contains(object)` is called, THEN it must report whether that object is physically present in the result.
- WHEN `matches(object)` is called, THEN it must report whether the object satisfies the result query even if it is not stored in the collection.
- WHEN `uniqueResult()` is called on exactly one result, THEN it must return that object.
- IF `uniqueResult()` is called on an empty result, THEN it must raise `NoSuchObjectException`.
- IF `uniqueResult()` is called on multiple results, THEN it must raise `NonUniqueObjectException`.
- WHEN `stream()` is closed, THEN it must close its originating `ResultSet`.
- WHEN `ResultSet.close()` is called, THEN it must release request resources or transaction state associated with that result.
- WHILE a collection result is closed, operations that consume or inspect its objects must raise `IllegalStateException`.

**Duplicate policy.**

- WHEN no deduplication option is supplied, THEN `DUPLICATES_ALLOWED` must apply and a union over overlapping branches or multi-valued matches must preserve duplicate encounters.
- WHERE `DeduplicationStrategy.LOGICAL_ELIMINATION` is supplied and the collection is not modified during iteration, the result must emit each equal object at most once without requiring full materialization before the first item.
- WHERE `DeduplicationStrategy.MATERIALIZE` is supplied, the result must emit each equal object at most once even while branch overlap exists.
- WHEN an `in` query is created for a `SimpleAttribute`, THEN its branch results must be treated as disjoint.
- WHEN an `in` query is created for a multi-value attribute, THEN the explicit `disjoint` argument must control whether branch-level duplicate elimination is skipped.

**Ordering.**

- WHEN `orderBy` contains `ascending(attribute)` or `descending(attribute)`, THEN result iteration must be ordered by that attribute in the requested direction.
- WHEN multiple attribute orders are supplied, THEN later orders must break ties left by earlier orders.
- WHEN `missingFirst(attribute)` or `missingLast(attribute)` wraps a nullable or multi-value attribute, THEN objects with no projected value must appear before or after objects with values respectively.
- IF `orderBy` receives an empty list of attribute orders, THEN construction must raise `IllegalArgumentException`.
- IF `missingFirst` or `missingLast` wraps another order-control attribute, THEN construction must raise `IllegalArgumentException`.

## Metadata and Statistics

This section defines read-only projections derived from registered indexes and kept aligned with collection mutations.

**Metadata selection.**

- WHEN `getMetadataEngine()` is called, THEN it must return a metadata view bound to that indexed collection.
- WHEN `getAttributeMetadata(attribute)` is called with a registered key-statistics index on the same attribute, THEN it must return an `AttributeMetadata` backed by that index.
- WHEN `getSortedAttributeMetadata(attribute)` is called with a registered sorted key-statistics index on the same attribute, THEN it must return a `SortedAttributeMetadata` backed by that index.
- IF no suitable index on the requested attribute is registered, THEN metadata accessor creation must raise `IllegalStateException`.

**Unsorted and sorted projections.**

- WHEN `getFrequencyDistribution()` is consumed, THEN each `KeyFrequency` must expose one distinct key through `getKey()` and its current object count through `getFrequency()`.
- WHEN `getDistinctKeys()` is consumed from `AttributeMetadata`, THEN it must emit every currently indexed distinct value without promising order.
- WHEN `getCountOfDistinctKeys()` or `getCountForKey(key)` is called, THEN it must return the current distinct-key count or the current number of indexed objects for that key.
- WHEN `getKeysAndValues()` is consumed, THEN it must emit one `KeyValue` pair for every indexed key-to-object association, including multiple pairs for a multi-value object.
- WHEN a no-range sorted metadata stream is requested, THEN keys or key-value pairs must be ordered ascending by default and descending for the corresponding `Descending` method.
- WHEN a ranged sorted metadata stream receives lower and upper bounds, THEN it must emit only keys inside the range and must honor each inclusivity flag; a null bound must leave that side unbounded.
- WHEN a metadata stream is closed, THEN it must close its index iterator and request-scope resources.

## Transaction Isolation

This section defines committed snapshots and atomic bulk mutation in `TransactionalIndexedCollection`.

**Committed updates.**

- WHEN `TransactionalIndexedCollection` is created with `objectType`, THEN it must begin empty and use read-committed isolation by default.
- WHEN a read-committed `update` adds, removes, or replaces a batch, THEN readers must observe either the complete state before the batch or the complete state after the batch.
- WHILE a read-committed `ResultSet` remains open, its snapshot must exclude partially committed additions and removals, and closing the result must release the snapshot.
- WHEN `update` receives two empty iterables, THEN it must return false without changing collection state.
- IF `objectsToRemove` and `objectsToAdd` contain equal objects under default validation, THEN `update` must raise `IllegalArgumentException` without committing the replacement.
- WHERE `argumentValidation(SKIP)` is supplied, overlapping update sets must bypass the disjointness check.
- WHERE `enableFlags(TransactionalIndexedCollection.STRICT_REPLACEMENT)` is supplied, `update` must return false without modifying the collection if any requested removal is absent.
- WHERE `isolationLevel(READ_UNCOMMITTED)` is supplied, `update` and retrieval must bypass the MVCC snapshot guarantee while preserving ordinary collection and query semantics.

## Local Persistence

This section defines deterministic on-heap storage and caller-controlled local disk storage.

**On-heap and disk creation.**

- WHEN `OnHeapPersistence.withoutPrimaryKey()` is used, THEN the collection must store objects in memory and support on-heap indexes without exposing a primary-key attribute.
- WHEN `OnHeapPersistence.onPrimaryKey(attribute)` is used, THEN `getPrimaryKeyAttribute()` must return that attribute.
- WHEN `DiskPersistence.onPrimaryKey(attribute)` is used, THEN it must allocate a local temporary persistence file and `getFile()` must return it.
- WHEN `DiskPersistence.onPrimaryKeyInFile(attribute, file)` is used, THEN it must bind collection storage and compatible disk indexes to that file and primary-key attribute.
- IF a disk persistence operation cannot open or update its local database, THEN it must raise `IllegalStateException` wrapping the storage failure.

**Durability and maintenance.**

- WHEN one disk-backed collection commits objects and a new `DiskPersistence` is opened on the same file and primary-key attribute, THEN a new collection must expose the previously stored objects.
- WHEN a compatible `DiskIndex` is added after reopening, THEN it must index the durable population and return the same matches as fallback evaluation.
- WHEN `close()` is called, THEN it must release held persistence resources without deleting the caller-selected file or its committed objects.

## State Model

The core state is a unique set of objects, zero or more registered indexes, optional query options, and one persistence strategy. A transactional collection adds a sequence of committed versions; a disk strategy adds a durable file projection.

The public projections are collection membership, `ResultSet` contents, index registration, metadata streams and counts, transaction snapshots, and persistence reopen results.

- WHILE an index is registered, its query and metadata projections must agree with collection membership after every completed mutation.
- WHILE a read-committed result remains open, it must represent one committed collection version and must not expose a partial bulk update.
- WHEN a disk-backed population is reopened, THEN collection membership, later disk-index results, and metadata derived from those indexes must describe the same durable objects.
- WHEN ordering or deduplication changes a result presentation, THEN predicate membership must remain unchanged except for explicitly permitted duplicate multiplicity.

## Error Semantics

| Condition | Required result |
|---|---|
| Null query attribute | IF a simple or comparative query receives a null attribute, THEN construction must raise `IllegalArgumentException`. |
| Null query value | IF an equality, range, or string query receives a null value, THEN construction must raise `NullPointerException`. |
| Invalid regular expression | IF the string regex is invalid, THEN `matchesRegex` must raise `PatternSyntaxException`. |
| Empty order list | IF `orderBy` receives no attribute orders, THEN it must raise `IllegalArgumentException`. |
| No suitable metadata index | IF metadata is requested without a compatible index on the same attribute, THEN accessor creation must raise `IllegalStateException`. |
| Empty unique result | IF `uniqueResult()` sees no object, THEN it must raise `NoSuchObjectException`. |
| Non-unique result | IF `uniqueResult()` sees multiple objects, THEN it must raise `NonUniqueObjectException`. |
| Duplicate unique key | IF a `UniqueIndex` sees one key on unequal objects, THEN the mutation must raise `UniqueConstraintViolatedException`. |
| Overlapping transactional replacement | IF validated removal and addition sets overlap by equality, THEN `update` must raise `IllegalArgumentException`. |
| Strict replacement misses an object | WHERE `STRICT_REPLACEMENT` is enabled, a missing removal must make `update` return false without mutation. |
| Incompatible index persistence | IF an index requires a persistence type absent from the collection, THEN `addIndex` must raise `IllegalStateException`. |
| Local storage failure | IF local disk storage cannot be opened or updated, THEN the triggering persistence operation must raise `IllegalStateException`. |

## Cross-View Invariants

1. A completed collection mutation must make collection membership, indexed retrieval, and index-derived metadata agree before the mutating call returns.
2. Removing an index must change only index registration and execution choice; query membership must remain equal to fallback evaluation.
3. `ResultSet.size()`, iteration, `isEmpty()`, `isNotEmpty()`, and `contains()` must describe the same result multiplicity and objects under the same query options.
4. Ordered and unordered retrieval of the same predicate must contain the same objects, while the ordered view must additionally honor requested attribute precedence and missing-value placement.
5. Deduplicated and duplicates-allowed retrieval must agree on the set of equal objects, while their iteration multiplicity must follow the selected strategy.
6. `AttributeMetadata` counts, frequency entries, distinct keys, and key-value pairs must be mutually consistent with the registered index and current collection.
7. A read-committed transaction snapshot and the collection after commit must each be internally consistent across iteration, size, query matching, and registered indexes, with no partially updated intermediate view.
8. Reopening a disk file must preserve collection membership, and rebuilding a compatible disk index must preserve query results and metadata counts for that membership.

## Public Interface

### Import Surface

```java
import com.googlecode.cqengine.IndexedCollection;
import com.googlecode.cqengine.ConcurrentIndexedCollection;
import com.googlecode.cqengine.TransactionalIndexedCollection;
import com.googlecode.cqengine.attribute.Attribute;
import com.googlecode.cqengine.attribute.SimpleAttribute;
import com.googlecode.cqengine.attribute.SimpleNullableAttribute;
import com.googlecode.cqengine.attribute.MultiValueAttribute;
import com.googlecode.cqengine.attribute.MultiValueNullableAttribute;
import com.googlecode.cqengine.attribute.SelfAttribute;
import com.googlecode.cqengine.index.Index;
import com.googlecode.cqengine.index.hash.HashIndex;
import com.googlecode.cqengine.index.navigable.NavigableIndex;
import com.googlecode.cqengine.index.unique.UniqueIndex;
import com.googlecode.cqengine.index.standingquery.StandingQueryIndex;
import com.googlecode.cqengine.index.disk.DiskIndex;
```

```java
import com.googlecode.cqengine.metadata.MetadataEngine;
import com.googlecode.cqengine.metadata.AttributeMetadata;
import com.googlecode.cqengine.metadata.SortedAttributeMetadata;
import com.googlecode.cqengine.metadata.KeyFrequency;
import com.googlecode.cqengine.index.support.KeyValue;
import com.googlecode.cqengine.persistence.Persistence;
import com.googlecode.cqengine.persistence.onheap.OnHeapPersistence;
import com.googlecode.cqengine.persistence.disk.DiskPersistence;
import com.googlecode.cqengine.query.Query;
import com.googlecode.cqengine.query.QueryFactory;
import com.googlecode.cqengine.query.logical.And;
import com.googlecode.cqengine.query.logical.Or;
import com.googlecode.cqengine.query.logical.Not;
```

```java
import com.googlecode.cqengine.query.simple.Equal;
import com.googlecode.cqengine.query.simple.In;
import com.googlecode.cqengine.query.simple.LessThan;
import com.googlecode.cqengine.query.simple.GreaterThan;
import com.googlecode.cqengine.query.simple.Between;
import com.googlecode.cqengine.query.simple.Has;
import com.googlecode.cqengine.query.simple.All;
import com.googlecode.cqengine.query.simple.None;
import com.googlecode.cqengine.query.simple.StringStartsWith;
import com.googlecode.cqengine.query.simple.StringEndsWith;
import com.googlecode.cqengine.query.simple.StringContains;
import com.googlecode.cqengine.query.simple.StringIsContainedIn;
import com.googlecode.cqengine.query.simple.StringIsPrefixOf;
import com.googlecode.cqengine.query.simple.StringMatchesRegex;
```

```java
import com.googlecode.cqengine.query.option.QueryOptions;
import com.googlecode.cqengine.query.option.DeduplicationStrategy;
import com.googlecode.cqengine.query.option.IsolationLevel;
import com.googlecode.cqengine.query.option.ArgumentValidationStrategy;
import com.googlecode.cqengine.query.option.AttributeOrder;
import com.googlecode.cqengine.query.option.OrderByOption;
import com.googlecode.cqengine.resultset.ResultSet;
import com.googlecode.cqengine.resultset.common.NoSuchObjectException;
import com.googlecode.cqengine.resultset.common.NonUniqueObjectException;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `IndexedCollection` | `retrieve`, `update`, `addIndex`, `removeIndex`, `getIndexes`, `getPersistence`, `getMetadataEngine`, and inherited `Set` operations |
| `ConcurrentIndexedCollection` | no-argument and persistence constructors; all `IndexedCollection` members |
| `TransactionalIndexedCollection` | object-type and persistence constructors; `STRICT_REPLACEMENT`; transactional overrides of retrieval, update, and `Set` mutations |
| `Attribute` | `getObjectType`, `getAttributeType`, `getAttributeName`, `getValues` |
| `SimpleAttribute`, `SimpleNullableAttribute` | public constructors; `getValue`, `getValues` |
| `MultiValueAttribute` | public constructors; `getValues` |
| `MultiValueNullableAttribute` | public constructors; `getNullableValues`, `getValues` |
| `SelfAttribute` | public constructors; `getValue` |
| `Index` | `retrieve`, `supportsQuery`, `isMutable`, `isQuantized`, `getEffectiveIndex`, `init`, `destroy`, `clear` |
| `HashIndex` | `onAttribute`, `onSemiUniqueAttribute`; inherited index and key-statistics members |
| `NavigableIndex` | `onAttribute`; inherited index and sorted key-statistics members |
| `UniqueIndex` | `onAttribute`; inherited index members; nested `UniqueConstraintViolatedException` |
| `StandingQueryIndex` | constructor, `onQuery`, `getStandingQuery`; inherited index members |
| `DiskIndex` | `onAttribute`; inherited index and sorted key-statistics members |
| `Query` | `matches` |
| `QueryFactory` | `equal`, `in`, `lessThan`, `lessThanOrEqualTo`, `greaterThan`, `greaterThanOrEqualTo`, `between`, `startsWith`, `endsWith`, `contains`, `isContainedIn`, `isPrefixOf`, `matchesRegex`, `has`, `and`, `or`, `not`, `all`, `none`, `ascending`, `descending`, `orderBy`, `missingFirst`, `missingLast`, `deduplicate`, `isolationLevel`, `argumentValidation`, `enableFlags`, `queryOptions`, `noQueryOptions`, `selfAttribute`, `attribute`, `nullableAttribute` |
| `Equal`, `In`, `LessThan`, `GreaterThan`, `Between`, `Has`, string-query types | public constructors; value, bound, inclusivity, disjointness, attribute, and `matches` accessors exposed by each type |
| `And`, `Or`, `Not` | public constructors; child-query accessors; `Or.isDisjoint`; `Not.getNegatedQuery`; `matches` |
| `QueryOptions` | constructors; `getOptions`, typed and keyed `get`, `put`, `remove` |
| `DeduplicationStrategy` | `DUPLICATES_ALLOWED`, `LOGICAL_ELIMINATION`, `MATERIALIZE` |
| `IsolationLevel` | `READ_COMMITTED`, `READ_UNCOMMITTED` |
| `ArgumentValidationStrategy` | `VALIDATE`, `SKIP` |
| `AttributeOrder`, `OrderByOption` | constructors; `getAttribute`, `isDescending`, `getAttributeOrders` |
| `ResultSet` | `iterator`, `contains`, `matches`, `getQuery`, `getQueryOptions`, `uniqueResult`, `getRetrievalCost`, `getMergeCost`, `size`, `isEmpty`, `isNotEmpty`, `spliterator`, `stream`, `close` |
| `MetadataEngine` | `getAttributeMetadata`, `getSortedAttributeMetadata` |
| `AttributeMetadata` | `getFrequencyDistribution`, `getDistinctKeys`, `getCountOfDistinctKeys`, `getCountForKey`, `getKeysAndValues` |
| `SortedAttributeMetadata` | inherited metadata members plus descending and ranged distinct-key, frequency, and key-value stream methods |
| `KeyFrequency` | `getKey`, `getFrequency` |
| `KeyValue` | `getKey`, `getValue` |
| `Persistence` | `supportsIndex`, `createObjectStore`, `getPrimaryKeyAttribute`, request-scope resource methods |
| `OnHeapPersistence` | public constructors; `onPrimaryKey`, `withoutPrimaryKey`; inherited persistence members |
| `DiskPersistence` | `onPrimaryKey`, `onPrimaryKeyInFile`, `createTempFile`, `getFile`, `close`; inherited persistence members |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `IndexedCollection` | interface | Combines mutable set membership, index registration, typed retrieval, persistence, and metadata access. |
| `ConcurrentIndexedCollection` | class | Provides the ordinary concurrent indexed set implementation. |
| `TransactionalIndexedCollection` | class | Adds read-committed MVCC snapshots and atomic bulk updates. |
| `Attribute` | interface | Projects typed values from stored objects. |
| `SimpleAttribute` | class | Projects exactly one non-null value per object. |
| `SimpleNullableAttribute` | class | Projects zero or one non-null value per object. |
| `MultiValueAttribute` | class | Projects multiple non-null values per object. |
| `MultiValueNullableAttribute` | class | Projects a nullable iterable with optional nullable components. |
| `SelfAttribute` | class | Projects the stored object itself. |
| `Index` | interface | Defines an index lifecycle and query-retrieval contract. |
| `HashIndex` | class | Indexes equality, membership, and presence with unsorted statistics. |
| `NavigableIndex` | class | Indexes equality and ranges with sorted statistics. |
| `UniqueIndex` | class | Enforces one unequal object per indexed key. |
| `UniqueConstraintViolatedException` | exception | Reports a duplicate key observed by a unique index. |
| `StandingQueryIndex` | class | Maintains membership for one fixed query or query fragment. |
| `DiskIndex` | class | Stores a navigable-style index in configured local disk persistence. |
| `Query` | interface | Tests an object under query options. |
| `QueryFactory` | class | Builds public predicates, attributes, ordering, deduplication, isolation, flags, and option containers. |
| `Equal`, `In`, `LessThan`, `GreaterThan`, `Between`, `Has` | classes | Represent scalar, membership, range, and presence predicates. |
| `StringStartsWith`, `StringEndsWith`, `StringContains` | classes | Represent case-sensitive character-sequence predicates. |
| `StringIsContainedIn`, `StringIsPrefixOf`, `StringMatchesRegex` | classes | Represent inverse containment, inverse prefix, and full-regex predicates. |
| `All`, `None` | classes | Represent predicates that match every object or no object. |
| `And`, `Or`, `Not` | classes | Compose child predicates with Boolean semantics. |
| `QueryOptions` | class | Carries request-scoped behavior options by key and option type. |
| `DeduplicationStrategy` | enum | Selects duplicate-preserving, logical, or materializing result behavior. |
| `IsolationLevel` | enum | Selects read-committed or read-uncommitted transactional behavior. |
| `ArgumentValidationStrategy` | enum | Selects validated or skipped transactional argument checks. |
| `AttributeOrder` | class | Pairs an attribute with one sort direction. |
| `OrderByOption` | class | Carries an ordered sequence of attribute orders. |
| `ResultSet` | class | Exposes closeable query results, membership tests, counts, streams, and query identity. |
| `NoSuchObjectException` | exception | Reports that a unique result was requested from an empty result. |
| `NonUniqueObjectException` | exception | Reports that a unique result was requested from multiple results. |
| `MetadataEngine` | class | Selects metadata accessors backed by registered indexes. |
| `AttributeMetadata` | class | Exposes unsorted key frequencies, counts, distinct keys, and key-value associations. |
| `SortedAttributeMetadata` | class | Adds ascending, descending, and ranged metadata streams. |
| `KeyFrequency` | interface | Exposes a distinct key and its frequency. |
| `KeyValue` | interface | Exposes one indexed key-to-object association. |
| `Persistence` | interface | Supplies object storage and declares index compatibility. |
| `OnHeapPersistence` | class | Stores the collection on the Java heap. |
| `DiskPersistence` | class | Stores collection identity and compatible indexes in a local file. |

### CLI Entry Points

There is no console script, executable main class, Maven plugin goal, or supported `java -jar` entry point for this artifact. Programmatic use is through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs JDK 17 and Maven on Linux without network access. The offline Maven repository contains the Java standard library support plus concurrent-trees, Javassist, SQLite JDBC, Kryo, Kryo serializers, ANTLR runtime, TypeTools, and JUnit Jupiter with their cached transitive dependencies. The target artifact is not preinstalled. The assessment environment provides the same JDK, Maven tooling, dependency cache, and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `com.googlecode.cqengine:cqengine`, JAR packaging, and Java 8-compatible main classes. All runtime dependencies required by the public behavior must be declared in that POM.

## Appendix B: Assessment Notes

Assessment exercises public Java construction, attribute projection, predicate matching, query composition, set mutation, index registration and maintenance, result operations, duplicate and ordering options, metadata streams and counts, transaction replacement and snapshot isolation, and local disk reopen behavior. Checks compare returned objects, counts, key/value projections, exception classes, durable effects, and cross-view consistency. They do not inspect private state, exact diagnostics, internal plan choices, serialization bytes, or timing. Each independently passing public behavior case contributes equally, with integration cases covering complete workflows across multiple projections.
