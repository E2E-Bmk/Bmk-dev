# Behavioral Clause Traceability

This internal sidecar assigns stable identifiers to every behavioral clause in `spec_v1.md`. It is not candidate-visible.

## ATTR

- CQE-ATTR-001 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `Attribute.getObjectType()`, `getAttributeType()`, or `getAttributeName()` is called, THEN it must return the object type, value type, or name configured for that attribute.
- CQE-ATTR-002 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `SimpleAttribute.getValues(object, queryOptions)` is called, THEN it must return exactly the single non-null value produced by `getValue`.
- CQE-ATTR-003 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `SimpleNullableAttribute.getValue` returns null, THEN `getValues` must return an empty iterable; otherwise it must return a singleton iterable.
- CQE-ATTR-004 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `MultiValueAttribute.getValues` is called, THEN it must return the non-null iterable supplied by the application-defined attribute.
- CQE-ATTR-005 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `MultiValueNullableAttribute.getNullableValues` returns null, THEN `getValues` must return an empty iterable.
- CQE-ATTR-006 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHERE `componentValuesNullable` is true, `MultiValueNullableAttribute.getValues` must omit null components while preserving the non-null component order.
- CQE-ATTR-007 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `selfAttribute(objectType)` is used, THEN the resulting `SelfAttribute` must expose each queried object as its own single value.
- CQE-ATTR-008 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN an `attribute` or `nullableAttribute` overload receives explicit object and value classes, THEN the resulting functional attribute must report those classes and invoke the supplied function for values.
- CQE-ATTR-009 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> IF a functional-attribute overload without explicit classes cannot resolve its generic types, THEN attribute construction must raise `IllegalStateException`.
- CQE-ATTR-010 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `equal(attribute, value)` is evaluated, THEN an object must match if at least one projected attribute value equals `value`.
- CQE-ATTR-011 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `in(attribute, values)` is evaluated, THEN an object must match if at least one projected attribute value belongs to the supplied set.
- CQE-ATTR-012 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `in` receives no values, THEN it must return a query that matches no objects.
- CQE-ATTR-013 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `in` receives one value, THEN it must return behavior equivalent to `equal`.
- CQE-ATTR-014 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `lessThan`, `lessThanOrEqualTo`, `greaterThan`, or `greaterThanOrEqualTo` is evaluated, THEN an object must match according to the named exclusive or inclusive comparison against at least one projected value.
- CQE-ATTR-015 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `between` is created without inclusivity flags, THEN both bounds must be inclusive.
- CQE-ATTR-016 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `between` receives `lowerInclusive` and `upperInclusive`, THEN each boundary must be included exactly when its corresponding flag is true.
- CQE-ATTR-017 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `has(attribute)` is evaluated, THEN an object must match if the attribute projects at least one non-null value.
- CQE-ATTR-018 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `all(objectType)` or `none(objectType)` is evaluated, THEN it must match every object or no object respectively.
- CQE-ATTR-019 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> IF a simple or comparative query receives a null attribute, THEN construction must raise `IllegalArgumentException`.
- CQE-ATTR-020 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> IF an equality, range, or string query receives a null query value, THEN construction must raise `NullPointerException`.
- CQE-ATTR-021 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> IF `in(attribute, collection)` receives a null collection, THEN construction must raise `NullPointerException`.
- CQE-ATTR-022 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `startsWith`, `endsWith`, or `contains` is evaluated, THEN matching must be case-sensitive and must use the corresponding `CharSequence` prefix, suffix, or contiguous-fragment rule.
- CQE-ATTR-023 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN an empty fragment is supplied to `startsWith`, `endsWith`, or `contains`, THEN every non-null character sequence must match, including an empty sequence.
- CQE-ATTR-024 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `isContainedIn(attribute, container)` is evaluated, THEN an object must match if at least one projected character sequence occurs contiguously inside `container`.
- CQE-ATTR-025 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `isPrefixOf(attribute, container)` is evaluated, THEN an object must match if at least one projected character sequence is a prefix of `container`.
- CQE-ATTR-026 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `matchesRegex` is evaluated, THEN an object must match if at least one entire projected character sequence matches the supplied Java regular expression.
- CQE-ATTR-027 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> IF the string overload of `matchesRegex` receives invalid regular-expression syntax, THEN it must raise `PatternSyntaxException`.
- CQE-ATTR-028 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `and` is evaluated, THEN an object must match only if every child query matches it.
- CQE-ATTR-029 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `or` is evaluated, THEN an object must match if at least one child query matches it.
- CQE-ATTR-030 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `not` is evaluated, THEN an object must match exactly when its child query does not match it.
- CQE-ATTR-031 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> WHEN `Query.matches(object, queryOptions)` is called, THEN it must apply the same predicate semantics used by collection retrieval.
- CQE-ATTR-032 — [Attributes and Query Predicates](#attributes-and-query-predicates)

> IF a logical query receives a null child-query collection or `not` receives a null child query, THEN construction must raise `NullPointerException`.

## COLL

- CQE-COLL-001 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `ConcurrentIndexedCollection` is created without a persistence argument, THEN it must use `OnHeapPersistence.withoutPrimaryKey()` and begin empty.
- CQE-COLL-002 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN standard `Set` operations add, remove, retain, or clear objects, THEN `IndexedCollection` must return the standard mutation result and expose the resulting unique membership through `size`, `contains`, iteration, and array views.
- CQE-COLL-003 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `update(objectsToRemove, objectsToAdd)` completes, THEN it must apply the requested removals and additions and must return true exactly when collection membership changed.
- CQE-COLL-004 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `retrieve(query)` is called, THEN it must behave as `retrieve(query, noQueryOptions())` and return a `ResultSet` over matching collection objects.
- CQE-COLL-005 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> IF `retrieve` receives a null query, THEN it must raise `IllegalStateException` before returning a result.
- CQE-COLL-006 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `addIndex(index)` completes, THEN the index must contain the relevant values of objects already present and must appear in `getIndexes()`.
- CQE-COLL-007 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHILE an index is registered, every successful collection mutation must update that index before the mutating call returns.
- CQE-COLL-008 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `removeIndex(index)` completes, THEN the index must disappear from `getIndexes()` and later retrieval must remain behaviorally correct through other indexes or fallback evaluation.
- CQE-COLL-009 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN no registered index supports a query, THEN retrieval must still return the same matching objects through fallback evaluation.
- CQE-COLL-010 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> IF an index is incompatible with the collection persistence, THEN `addIndex` must raise `IllegalStateException`.
- CQE-COLL-011 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `HashIndex.onAttribute(attribute)` is registered, THEN it must support `equal`, `in`, and `has` queries for that attribute and provide unsorted key statistics.
- CQE-COLL-012 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `NavigableIndex.onAttribute(attribute)` is registered, THEN it must support equality, membership, presence, less-than, greater-than, and between queries and provide sorted key statistics.
- CQE-COLL-013 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `UniqueIndex.onAttribute(attribute)` is registered, THEN each indexed attribute value must identify at most one unequal object while supporting equality and membership queries.
- CQE-COLL-014 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> IF a `UniqueIndex` observes the same indexed value on two unequal objects, THEN the triggering registration or mutation must raise `UniqueIndex.UniqueConstraintViolatedException`.
- CQE-COLL-015 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `StandingQueryIndex.onQuery(query)` is registered, THEN retrieval of that same query or matching query fragment must preserve the ordinary predicate result while the collection changes.
- CQE-COLL-016 — [Indexed Collection and Index Maintenance](#indexed-collection-and-index-maintenance)

> WHEN `DiskIndex.onAttribute(attribute)` is registered on a disk-persisted collection, THEN it must support the same equality, membership, presence, and range query families as `NavigableIndex`.

## RES

- CQE-RES-001 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN a `ResultSet` is iterated, THEN it must yield objects matching its `getQuery()` under its `getQueryOptions()`.
- CQE-RES-002 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `size`, `isEmpty`, or `isNotEmpty` is called, THEN it must describe the objects that iteration of the same result would yield.
- CQE-RES-003 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `contains(object)` is called, THEN it must report whether that object is physically present in the result.
- CQE-RES-004 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `matches(object)` is called, THEN it must report whether the object satisfies the result query even if it is not stored in the collection.
- CQE-RES-005 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `uniqueResult()` is called on exactly one result, THEN it must return that object.
- CQE-RES-006 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> IF `uniqueResult()` is called on an empty result, THEN it must raise `NoSuchObjectException`.
- CQE-RES-007 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> IF `uniqueResult()` is called on multiple results, THEN it must raise `NonUniqueObjectException`.
- CQE-RES-008 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `stream()` is closed, THEN it must close its originating `ResultSet`.
- CQE-RES-009 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `ResultSet.close()` is called, THEN it must release request resources or transaction state associated with that result.
- CQE-RES-010 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHILE a collection result is closed, operations that consume or inspect its objects must raise `IllegalStateException`.
- CQE-RES-011 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN no deduplication option is supplied, THEN `DUPLICATES_ALLOWED` must apply and a union over overlapping branches or multi-valued matches must preserve duplicate encounters.
- CQE-RES-012 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHERE `DeduplicationStrategy.LOGICAL_ELIMINATION` is supplied and the collection is not modified during iteration, the result must emit each equal object at most once without requiring full materialization before the first item.
- CQE-RES-013 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHERE `DeduplicationStrategy.MATERIALIZE` is supplied, the result must emit each equal object at most once even while branch overlap exists.
- CQE-RES-014 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN an `in` query is created for a `SimpleAttribute`, THEN its branch results must be treated as disjoint.
- CQE-RES-015 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN an `in` query is created for a multi-value attribute, THEN the explicit `disjoint` argument must control whether branch-level duplicate elimination is skipped.
- CQE-RES-016 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `orderBy` contains `ascending(attribute)` or `descending(attribute)`, THEN result iteration must be ordered by that attribute in the requested direction.
- CQE-RES-017 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN multiple attribute orders are supplied, THEN later orders must break ties left by earlier orders.
- CQE-RES-018 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> WHEN `missingFirst(attribute)` or `missingLast(attribute)` wraps a nullable or multi-value attribute, THEN objects with no projected value must appear before or after objects with values respectively.
- CQE-RES-019 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> IF `orderBy` receives an empty list of attribute orders, THEN construction must raise `IllegalArgumentException`.
- CQE-RES-020 — [Result Views, Deduplication, and Ordering](#result-views-deduplication-and-ordering)

> IF `missingFirst` or `missingLast` wraps another order-control attribute, THEN construction must raise `IllegalArgumentException`.

## META

- CQE-META-001 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getMetadataEngine()` is called, THEN it must return a metadata view bound to that indexed collection.
- CQE-META-002 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getAttributeMetadata(attribute)` is called with a registered key-statistics index on the same attribute, THEN it must return an `AttributeMetadata` backed by that index.
- CQE-META-003 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getSortedAttributeMetadata(attribute)` is called with a registered sorted key-statistics index on the same attribute, THEN it must return a `SortedAttributeMetadata` backed by that index.
- CQE-META-004 — [Metadata and Statistics](#metadata-and-statistics)

> IF no suitable index on the requested attribute is registered, THEN metadata accessor creation must raise `IllegalStateException`.
- CQE-META-005 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getFrequencyDistribution()` is consumed, THEN each `KeyFrequency` must expose one distinct key through `getKey()` and its current object count through `getFrequency()`.
- CQE-META-006 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getDistinctKeys()` is consumed from `AttributeMetadata`, THEN it must emit every currently indexed distinct value without promising order.
- CQE-META-007 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getCountOfDistinctKeys()` or `getCountForKey(key)` is called, THEN it must return the current distinct-key count or the current number of indexed objects for that key.
- CQE-META-008 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN `getKeysAndValues()` is consumed, THEN it must emit one `KeyValue` pair for every indexed key-to-object association, including multiple pairs for a multi-value object.
- CQE-META-009 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN a no-range sorted metadata stream is requested, THEN keys or key-value pairs must be ordered ascending by default and descending for the corresponding `Descending` method.
- CQE-META-010 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN a ranged sorted metadata stream receives lower and upper bounds, THEN it must emit only keys inside the range and must honor each inclusivity flag; a null bound must leave that side unbounded.
- CQE-META-011 — [Metadata and Statistics](#metadata-and-statistics)

> WHEN a metadata stream is closed, THEN it must close its index iterator and request-scope resources.

## TX

- CQE-TX-001 — [Transaction Isolation](#transaction-isolation)

> WHEN `TransactionalIndexedCollection` is created with `objectType`, THEN it must begin empty and use read-committed isolation by default.
- CQE-TX-002 — [Transaction Isolation](#transaction-isolation)

> WHEN a read-committed `update` adds, removes, or replaces a batch, THEN readers must observe either the complete state before the batch or the complete state after the batch.
- CQE-TX-003 — [Transaction Isolation](#transaction-isolation)

> WHILE a read-committed `ResultSet` remains open, its snapshot must exclude partially committed additions and removals, and closing the result must release the snapshot.
- CQE-TX-004 — [Transaction Isolation](#transaction-isolation)

> WHEN `update` receives two empty iterables, THEN it must return false without changing collection state.
- CQE-TX-005 — [Transaction Isolation](#transaction-isolation)

> IF `objectsToRemove` and `objectsToAdd` contain equal objects under default validation, THEN `update` must raise `IllegalArgumentException` without committing the replacement.
- CQE-TX-006 — [Transaction Isolation](#transaction-isolation)

> WHERE `argumentValidation(SKIP)` is supplied, overlapping update sets must bypass the disjointness check.
- CQE-TX-007 — [Transaction Isolation](#transaction-isolation)

> WHERE `enableFlags(TransactionalIndexedCollection.STRICT_REPLACEMENT)` is supplied, `update` must return false without modifying the collection if any requested removal is absent.
- CQE-TX-008 — [Transaction Isolation](#transaction-isolation)

> WHERE `isolationLevel(READ_UNCOMMITTED)` is supplied, `update` and retrieval must bypass the MVCC snapshot guarantee while preserving ordinary collection and query semantics.

## PERS

- CQE-PERS-001 — [Local Persistence](#local-persistence)

> WHEN `OnHeapPersistence.withoutPrimaryKey()` is used, THEN the collection must store objects in memory and support on-heap indexes without exposing a primary-key attribute.
- CQE-PERS-002 — [Local Persistence](#local-persistence)

> WHEN `OnHeapPersistence.onPrimaryKey(attribute)` is used, THEN `getPrimaryKeyAttribute()` must return that attribute.
- CQE-PERS-003 — [Local Persistence](#local-persistence)

> WHEN `DiskPersistence.onPrimaryKey(attribute)` is used, THEN it must allocate a local temporary persistence file and `getFile()` must return it.
- CQE-PERS-004 — [Local Persistence](#local-persistence)

> WHEN `DiskPersistence.onPrimaryKeyInFile(attribute, file)` is used, THEN it must bind collection storage and compatible disk indexes to that file and primary-key attribute.
- CQE-PERS-005 — [Local Persistence](#local-persistence)

> IF a disk persistence operation cannot open or update its local database, THEN it must raise `IllegalStateException` wrapping the storage failure.
- CQE-PERS-006 — [Local Persistence](#local-persistence)

> WHEN one disk-backed collection commits objects and a new `DiskPersistence` is opened on the same file and primary-key attribute, THEN a new collection must expose the previously stored objects.
- CQE-PERS-007 — [Local Persistence](#local-persistence)

> WHEN a compatible `DiskIndex` is added after reopening, THEN it must index the durable population and return the same matches as fallback evaluation.
- CQE-PERS-008 — [Local Persistence](#local-persistence)

> WHEN `close()` is called, THEN it must release held persistence resources without deleting the caller-selected file or its committed objects.

## STATE

- CQE-STATE-001 — [State Model](#state-model)

> WHILE an index is registered, its query and metadata projections must agree with collection membership after every completed mutation.
- CQE-STATE-002 — [State Model](#state-model)

> WHILE a read-committed result remains open, it must represent one committed collection version and must not expose a partial bulk update.
- CQE-STATE-003 — [State Model](#state-model)

> WHEN a disk-backed population is reopened, THEN collection membership, later disk-index results, and metadata derived from those indexes must describe the same durable objects.
- CQE-STATE-004 — [State Model](#state-model)

> WHEN ordering or deduplication changes a result presentation, THEN predicate membership must remain unchanged except for explicitly permitted duplicate multiplicity.

## ERR

- CQE-ERR-001 — [Error Semantics](#error-semantics)

> IF a simple or comparative query receives a null attribute, THEN construction must raise `IllegalArgumentException`.
- CQE-ERR-002 — [Error Semantics](#error-semantics)

> IF an equality, range, or string query receives a null value, THEN construction must raise `NullPointerException`.
- CQE-ERR-003 — [Error Semantics](#error-semantics)

> IF the string regex is invalid, THEN `matchesRegex` must raise `PatternSyntaxException`.
- CQE-ERR-004 — [Error Semantics](#error-semantics)

> IF `orderBy` receives no attribute orders, THEN it must raise `IllegalArgumentException`.
- CQE-ERR-005 — [Error Semantics](#error-semantics)

> IF metadata is requested without a compatible index on the same attribute, THEN accessor creation must raise `IllegalStateException`.
- CQE-ERR-006 — [Error Semantics](#error-semantics)

> IF `uniqueResult()` sees no object, THEN it must raise `NoSuchObjectException`.
- CQE-ERR-007 — [Error Semantics](#error-semantics)

> IF `uniqueResult()` sees multiple objects, THEN it must raise `NonUniqueObjectException`.
- CQE-ERR-008 — [Error Semantics](#error-semantics)

> IF a `UniqueIndex` sees one key on unequal objects, THEN the mutation must raise `UniqueConstraintViolatedException`.
- CQE-ERR-009 — [Error Semantics](#error-semantics)

> IF validated removal and addition sets overlap by equality, THEN `update` must raise `IllegalArgumentException`.
- CQE-ERR-010 — [Error Semantics](#error-semantics)

> WHERE `STRICT_REPLACEMENT` is enabled, a missing removal must make `update` return false without mutation.
- CQE-ERR-011 — [Error Semantics](#error-semantics)

> IF an index requires a persistence type absent from the collection, THEN `addIndex` must raise `IllegalStateException`.
- CQE-ERR-012 — [Error Semantics](#error-semantics)

> IF local disk storage cannot be opened or updated, THEN the triggering persistence operation must raise `IllegalStateException`.

## CVI

- CQE-CVI-001 — [Cross-View Invariants](#crossview-invariants)

> A completed collection mutation must make collection membership, indexed retrieval, and index-derived metadata agree before the mutating call returns.
- CQE-CVI-002 — [Cross-View Invariants](#crossview-invariants)

> Removing an index must change only index registration and execution choice; query membership must remain equal to fallback evaluation.
- CQE-CVI-003 — [Cross-View Invariants](#crossview-invariants)

> `ResultSet.size()`, iteration, `isEmpty()`, `isNotEmpty()`, and `contains()` must describe the same result multiplicity and objects under the same query options.
- CQE-CVI-004 — [Cross-View Invariants](#crossview-invariants)

> Ordered and unordered retrieval of the same predicate must contain the same objects, while the ordered view must additionally honor requested attribute precedence and missing-value placement.
- CQE-CVI-005 — [Cross-View Invariants](#crossview-invariants)

> Deduplicated and duplicates-allowed retrieval must agree on the set of equal objects, while their iteration multiplicity must follow the selected strategy.
- CQE-CVI-006 — [Cross-View Invariants](#crossview-invariants)

> `AttributeMetadata` counts, frequency entries, distinct keys, and key-value pairs must be mutually consistent with the registered index and current collection.
- CQE-CVI-007 — [Cross-View Invariants](#crossview-invariants)

> A read-committed transaction snapshot and the collection after commit must each be internally consistent across iteration, size, query matching, and registered indexes, with no partially updated intermediate view.
- CQE-CVI-008 — [Cross-View Invariants](#crossview-invariants)

> Reopening a disk file must preserve collection membership, and rebuilding a compatible disk index must preserve query results and metadata counts for that membership.
