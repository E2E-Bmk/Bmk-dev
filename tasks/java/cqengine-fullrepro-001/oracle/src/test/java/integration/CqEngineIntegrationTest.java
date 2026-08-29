package integration;

import com.googlecode.cqengine.ConcurrentIndexedCollection;
import com.googlecode.cqengine.IndexedCollection;
import com.googlecode.cqengine.TransactionalIndexedCollection;
import com.googlecode.cqengine.index.Index;
import com.googlecode.cqengine.index.disk.DiskIndex;
import com.googlecode.cqengine.index.hash.HashIndex;
import com.googlecode.cqengine.index.navigable.NavigableIndex;
import com.googlecode.cqengine.index.standingquery.StandingQueryIndex;
import com.googlecode.cqengine.index.support.KeyValue;
import com.googlecode.cqengine.index.unique.UniqueIndex;
import com.googlecode.cqengine.metadata.AttributeMetadata;
import com.googlecode.cqengine.metadata.KeyFrequency;
import com.googlecode.cqengine.metadata.SortedAttributeMetadata;
import com.googlecode.cqengine.persistence.disk.DiskPersistence;
import com.googlecode.cqengine.query.option.DeduplicationStrategy;
import com.googlecode.cqengine.query.option.IsolationLevel;
import com.googlecode.cqengine.resultset.ResultSet;
import org.junit.Test;
import support.Item;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static com.googlecode.cqengine.query.QueryFactory.*;
import static org.junit.Assert.*;

public class CqEngineIntegrationTest {
    private static final Item A = new Item(101, "amber", 7, "north", null, "red", "soft");
    private static final Item B = new Item(102, "basil", 11, "south", 2, "blue", "soft");
    private static final Item C = new Item(103, "cedar", 11, "north", 1, "red", "dense");
    private static final Item D = new Item(104, "dune", 19, "west", 3, "green");
    private static final Item E = new Item(106, "fern", 13, "north", 5, "green");

    private static IndexedCollection<Item> populated() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B, C, D));
        return collection;
    }

    private static List<Integer> ids(Iterable<Item> values) {
        List<Integer> result = new ArrayList<Integer>();
        for (Item value : values) result.add(value.id);
        return result;
    }

    private static Set<Integer> idSet(Iterable<Item> values) {
        return new HashSet<Integer>(ids(values));
    }

    private static int indexCount(IndexedCollection<Item> collection) {
        int count = 0;
        for (Index<Item> ignored : collection.getIndexes()) count++;
        return count;
    }

    /**
     * Verifies: CQE-COLL-006, CQE-COLL-011, CQE-CVI-001
     * Seam: state consistency
     * CVI-1: collection membership and a newly registered hash index agree.
     * Depends-On: collectionSetOperationsReportMutation, equalMatchesAnyMultiValue
     */
    @Test public void hashIndexBackfillsExistingPopulation() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(HashIndex.onAttribute(Item.CATEGORY));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 103)), idSet(collection.retrieve(equal(Item.CATEGORY, "north"))));
        assertEquals(1, indexCount(collection));
    }

    /**
     * Verifies: CQE-COLL-007, CQE-META-007, CQE-CVI-001
     * Seam: state consistency
     * CVI-1: mutation, indexed retrieval, and metadata become visible together.
     * Depends-On: collectionSetOperationsReportMutation, metadataRequiresCompatibleIndex
     */
    @Test public void hashIndexTracksCompletedMutations() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(HashIndex.onAttribute(Item.CATEGORY));
        AttributeMetadata<String, Item> metadata = collection.getMetadataEngine().getAttributeMetadata(Item.CATEGORY);
        collection.add(E);
        assertEquals(3L, integralCount(metadata.getCountForKey("north")));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 103, 106)), idSet(collection.retrieve(equal(Item.CATEGORY, "north"))));
    }

    /**
     * Verifies: CQE-COLL-008, CQE-COLL-009, CQE-CVI-002
     * Seam: lifecycle crossing
     * CVI-2: equality membership survives index removal and fallback handoff.
     * Depends-On: equalMatchesAnyMultiValue, collectionSetOperationsReportMutation
     */
    @Test public void removingHashIndexPreservesEqualityResults() {
        IndexedCollection<Item> collection = populated();
        Index<Item> index = HashIndex.onAttribute(Item.CATEGORY);
        collection.addIndex(index);
        Set<Integer> before = idSet(collection.retrieve(equal(Item.CATEGORY, "north")));
        collection.removeIndex(index);
        assertEquals(before, idSet(collection.retrieve(equal(Item.CATEGORY, "north"))));
        assertEquals(0, indexCount(collection));
    }

    /**
     * Verifies: CQE-COLL-008, CQE-COLL-012, CQE-CVI-002
     * Seam: protocol handoff
     * CVI-2: range membership is independent of the registered execution path.
     * Depends-On: betweenHonorsBoundaryFlags, collectionSetOperationsReportMutation
     */
    @Test public void removingNavigableIndexPreservesRangeResults() {
        IndexedCollection<Item> collection = populated();
        Index<Item> index = NavigableIndex.onAttribute(Item.SCORE);
        collection.addIndex(index);
        Set<Integer> before = idSet(collection.retrieve(between(Item.SCORE, 7, false, 19, true)));
        collection.removeIndex(index);
        assertEquals(before, idSet(collection.retrieve(between(Item.SCORE, 7, false, 19, true))));
    }

    /**
     * Verifies: CQE-RES-001, CQE-RES-002, CQE-RES-003, CQE-CVI-003
     * Seam: state consistency
     * CVI-3: all result projections describe the same non-empty result.
     * Depends-On: equalMatchesAnyMultiValue, resultContainsAndMatchesAreDistinctViews
     */
    @Test public void resultMetricsAgreeWithIteration() {
        IndexedCollection<Item> collection = populated();
        ResultSet<Item> result = collection.retrieve(equal(Item.CATEGORY, "north"));
        assertEquals(2, result.size());
        assertEquals(result.size(), ids(result).size());
        assertFalse(result.isEmpty());
        assertTrue(result.isNotEmpty());
        assertTrue(result.contains(A));
        result.close();
    }

    /**
     * Verifies: CQE-RES-002, CQE-RES-003, CQE-CVI-003
     * Seam: state consistency
     * CVI-3: empty iteration, counts, flags, and containment agree.
     * Depends-On: emptyInMatchesNothing, resultContainsAndMatchesAreDistinctViews
     */
    @Test public void emptyResultMetricsAgree() {
        IndexedCollection<Item> collection = populated();
        ResultSet<Item> result = collection.retrieve(equal(Item.ID, 999));
        assertEquals(Collections.emptyList(), ids(result));
        assertEquals(0, result.size());
        assertTrue(result.isEmpty());
        assertFalse(result.isNotEmpty());
        assertFalse(result.contains(A));
        result.close();
    }

    /**
     * Verifies: CQE-RES-016, CQE-STATE-004, CQE-CVI-004
     * Seam: config interaction
     * CVI-4: ascending presentation preserves unordered predicate membership.
     * Depends-On: attributeOrderReportsDirection, allAndNoneAreComplements
     */
    @Test public void ascendingOrderPreservesMembership() {
        IndexedCollection<Item> collection = populated();
        Set<Integer> unordered = idSet(collection.retrieve(all(Item.class)));
        List<Integer> ordered = ids(collection.retrieve(all(Item.class), queryOptions(orderBy(ascending(Item.SCORE)))));
        assertEquals(Arrays.asList(101, 102, 103, 104), ordered);
        assertEquals(unordered, new HashSet<Integer>(ordered));
    }

    /**
     * Verifies: CQE-RES-016, CQE-RES-017, CQE-CVI-004
     * Seam: config interaction
     * CVI-4: a later key breaks equal-score ties without changing membership.
     * Depends-On: attributeOrderReportsDirection, collectionSetOperationsReportMutation
     */
    @Test public void multiKeyOrderingBreaksTies() {
        IndexedCollection<Item> collection = populated();
        List<Integer> ordered = ids(collection.retrieve(all(Item.class), queryOptions(orderBy(ascending(Item.SCORE), descending(Item.ID)))));
        assertEquals(Arrays.asList(101, 103, 102, 104), ordered);
        assertEquals(idSet(collection), new HashSet<Integer>(ordered));
    }

    /**
     * Verifies: CQE-RES-012, CQE-STATE-004, CQE-CVI-005
     * Seam: config interaction
     * CVI-5: logical elimination preserves the set selected by overlapping branches.
     * Depends-On: orAcceptsAnyChild, multiAttributePreservesValues
     */
    @Test public void logicalDeduplicationPreservesSelectedSet() {
        IndexedCollection<Item> collection = populated();
        ResultSet<Item> raw = collection.retrieve(or(equal(Item.CATEGORY, "north"), in(Item.TAGS, "red", "soft")));
        ResultSet<Item> dedup = collection.retrieve(or(equal(Item.CATEGORY, "north"), in(Item.TAGS, "red", "soft")), queryOptions(deduplicate(DeduplicationStrategy.LOGICAL_ELIMINATION)));
        assertEquals(idSet(raw), idSet(dedup));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 102, 103)), idSet(dedup));
        raw.close(); dedup.close();
    }

    /**
     * Verifies: CQE-RES-013, CQE-STATE-004, CQE-CVI-005
     * Seam: config interaction
     * CVI-5: materialization emits every equal object at most once.
     * Depends-On: orAcceptsAnyChild, multiAttributePreservesValues
     */
    @Test public void materializedDeduplicationEliminatesOverlap() {
        IndexedCollection<Item> collection = populated();
        ResultSet<Item> result = collection.retrieve(or(equal(Item.CATEGORY, "north"), in(Item.TAGS, "red", "soft")), queryOptions(deduplicate(DeduplicationStrategy.MATERIALIZE)));
        List<Integer> values = ids(result);
        assertEquals(values.size(), new HashSet<Integer>(values).size());
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 102, 103)), new HashSet<Integer>(values));
        result.close();
    }

    /**
     * Verifies: CQE-RES-011, CQE-RES-012, CQE-CVI-005
     * Seam: protocol handoff
     * CVI-5: the configured duplicate policy changes multiplicity only, not membership.
     * Depends-On: singletonInBehavesLikeEqual, queryOptionsPutGetRemoveRoundTrip
     */
    @Test public void duplicatePoliciesAgreeOnMembership() {
        IndexedCollection<Item> collection = populated();
        Set<Integer> allowed = idSet(collection.retrieve(or(equal(Item.CATEGORY, "north"), in(Item.TAGS, "red", "soft"))));
        Set<Integer> logical = idSet(collection.retrieve(or(equal(Item.CATEGORY, "north"), in(Item.TAGS, "red", "soft")), queryOptions(deduplicate(DeduplicationStrategy.LOGICAL_ELIMINATION))));
        Set<Integer> materialized = idSet(collection.retrieve(or(equal(Item.CATEGORY, "north"), in(Item.TAGS, "red", "soft")), queryOptions(deduplicate(DeduplicationStrategy.MATERIALIZE))));
        assertEquals(allowed, logical);
        assertEquals(logical, materialized);
    }

    /**
     * Verifies: CQE-META-005, CQE-META-007, CQE-CVI-006
     * Seam: state consistency
     * CVI-6: frequency entries and direct counts agree.
     * Depends-On: collectionSetOperationsReportMutation, metadataRequiresCompatibleIndex
     */
    @Test public void metadataCountsAgreeWithFrequencyDistribution() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(HashIndex.onAttribute(Item.CATEGORY));
        AttributeMetadata<String, Item> metadata = collection.getMetadataEngine().getAttributeMetadata(Item.CATEGORY);
        Map<String, Integer> frequencies = new HashMap<String, Integer>();
        try (Stream<KeyFrequency<String>> stream = metadata.getFrequencyDistribution()) {
            stream.forEach(kf -> frequencies.put(kf.getKey(), kf.getFrequency()));
        }
        assertEquals(frequencies.get("north").longValue(), integralCount(metadata.getCountForKey("north")));
        assertEquals(Integer.valueOf(2), frequencies.get("north"));
    }

    /**
     * Verifies: CQE-META-006, CQE-META-007, CQE-CVI-006
     * Seam: state consistency
     * CVI-6: distinct key enumeration agrees with its count.
     * Depends-On: collectionSetOperationsReportMutation, metadataRequiresCompatibleIndex
     */
    @Test public void metadataDistinctKeysAgreeWithCount() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(HashIndex.onAttribute(Item.CATEGORY));
        AttributeMetadata<String, Item> metadata = collection.getMetadataEngine().getAttributeMetadata(Item.CATEGORY);
        Set<String> keys;
        try (Stream<String> stream = metadata.getDistinctKeys()) { keys = stream.collect(Collectors.toSet()); }
        assertEquals(new HashSet<String>(Arrays.asList("north", "south", "west")), keys);
        assertEquals((long) keys.size(), integralCount(metadata.getCountOfDistinctKeys()));
    }

    /**
     * Verifies: CQE-META-008, CQE-CVI-006
     * Seam: state consistency
     * Depends-On: multiAttributePreservesValues, collectionSetOperationsReportMutation
     */
    @Test public void metadataKeyValuePairsReflectIndexedAssociations() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(HashIndex.onAttribute(Item.TAGS));
        AttributeMetadata<String, Item> metadata = collection.getMetadataEngine().getAttributeMetadata(Item.TAGS);
        List<KeyValue<String, Item>> pairs;
        try (Stream<KeyValue<String, Item>> stream = metadata.getKeysAndValues()) { pairs = stream.collect(Collectors.toList()); }
        assertEquals(7, pairs.size());
        assertEquals(2L, integralCount(metadata.getCountForKey("red")));
    }

    /**
     * Verifies: CQE-META-003, CQE-META-009
     * Seam: protocol handoff
     * Depends-On: attributeOrderReportsDirection, metadataRequiresCompatibleIndex
     */
    @Test public void sortedMetadataProvidesBothDirections() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(NavigableIndex.onAttribute(Item.SCORE));
        SortedAttributeMetadata<Integer, Item> metadata = collection.getMetadataEngine().getSortedAttributeMetadata(Item.SCORE);
        List<Integer> ascending;
        List<Integer> descending;
        try (Stream<Integer> stream = metadata.getDistinctKeys()) { ascending = stream.collect(Collectors.toList()); }
        try (Stream<Integer> stream = metadata.getDistinctKeysDescending()) { descending = stream.collect(Collectors.toList()); }
        assertEquals(Arrays.asList(7, 11, 19), ascending);
        assertEquals(Arrays.asList(19, 11, 7), descending);
    }

    /**
     * Verifies: CQE-META-010
     * Seam: config interaction
     * Depends-On: betweenHonorsBoundaryFlags, metadataRequiresCompatibleIndex
     */
    @Test public void sortedMetadataHonorsRangeInclusivity() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(NavigableIndex.onAttribute(Item.SCORE));
        SortedAttributeMetadata<Integer, Item> metadata = collection.getMetadataEngine().getSortedAttributeMetadata(Item.SCORE);
        List<Integer> keys;
        try (Stream<Integer> stream = metadata.getDistinctKeys(7, false, 19, false)) { keys = stream.collect(Collectors.toList()); }
        assertEquals(Collections.singletonList(11), keys);
    }

    /**
     * Verifies: CQE-COLL-011
     * Seam: protocol handoff
     * Depends-On: singletonInBehavesLikeEqual, collectionSetOperationsReportMutation
     */
    @Test public void hashIndexSupportsMembershipQuery() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(HashIndex.onAttribute(Item.CATEGORY));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 102, 103)), idSet(collection.retrieve(in(Item.CATEGORY, "north", "south"))));
    }

    /**
     * Verifies: CQE-COLL-012
     * Seam: protocol handoff
     * Depends-On: betweenHonorsBoundaryFlags, collectionSetOperationsReportMutation
     */
    @Test public void navigableIndexSupportsRangeQueries() {
        IndexedCollection<Item> collection = populated();
        collection.addIndex(NavigableIndex.onAttribute(Item.SCORE));
        assertEquals(new HashSet<Integer>(Arrays.asList(102, 103, 104)), idSet(collection.retrieve(between(Item.SCORE, 7, false, 19, true))));
        assertEquals(Collections.singleton(104), idSet(collection.retrieve(greaterThan(Item.SCORE, 11))));
    }

    /**
     * Verifies: CQE-COLL-013
     * Seam: protocol handoff
     * Depends-On: equalMatchesAnyMultiValue, singletonInBehavesLikeEqual
     */
    @Test public void uniqueIndexSupportsEqualityAndMembership() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        collection.addIndex(UniqueIndex.onAttribute(Item.CATEGORY));
        assertSame(A, collection.retrieve(equal(Item.CATEGORY, "north")).uniqueResult());
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 102)), idSet(collection.retrieve(in(Item.CATEGORY, "north", "south"))));
    }

    /**
     * Verifies: CQE-COLL-014, CQE-ERR-008
     * Seam: error propagation
     * Depends-On: collectionSetOperationsReportMutation, equalMatchesAnyMultiValue
     */
    @Test public void uniqueIndexRejectsUnequalObjectsWithSameKey() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        collection.addIndex(UniqueIndex.onAttribute(Item.CATEGORY));
        assertThrows(UniqueIndex.UniqueConstraintViolatedException.class, () -> collection.add(C));
    }

    /**
     * Verifies: CQE-COLL-015
     * Seam: lifecycle crossing
     * Depends-On: exclusiveAndInclusiveRangesDiffer, collectionSetOperationsReportMutation
     */
    @Test public void standingQueryIndexBackfillsMatchingObjects() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        collection.addIndex(StandingQueryIndex.onQuery(greaterThan(Item.SCORE, 8)));
        assertEquals(Collections.singletonList(102), ids(collection.retrieve(greaterThan(Item.SCORE, 8))));
    }

    /**
     * Verifies: CQE-COLL-007, CQE-COLL-015
     * Seam: lifecycle crossing
     * Depends-On: exclusiveAndInclusiveRangesDiffer, collectionSetOperationsReportMutation
     */
    @Test public void standingQueryIndexTracksAddsAndRemoves() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        collection.addIndex(StandingQueryIndex.onQuery(greaterThan(Item.SCORE, 8)));
        collection.add(D);
        collection.remove(B);
        assertEquals(Collections.singletonList(104), ids(collection.retrieve(greaterThan(Item.SCORE, 8))));
    }

    /**
     * Verifies: CQE-TX-001, CQE-TX-002
     * Seam: lifecycle crossing
     * Depends-On: collectionUpdateReplacesMembership, collectionSetOperationsReportMutation
     */
    @Test public void transactionReplacementCommitsCompleteBatch() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.addAll(Arrays.asList(A, B));
        assertTrue(collection.update(Collections.singleton(B), Collections.singleton(C)));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 103)), idSet(collection));
    }

    /**
     * Verifies: CQE-TX-004
     * Seam: lifecycle crossing
     * Depends-On: collectionUpdateReplacesMembership, collectionSetOperationsReportMutation
     */
    @Test public void emptyTransactionUpdateDoesNotMutate() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.addAll(Arrays.asList(A, B));
        assertFalse(collection.update(Collections.emptyList(), Collections.emptyList()));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 102)), idSet(collection));
    }

    /**
     * Verifies: CQE-TX-005, CQE-ERR-009
     * Seam: error propagation
     * Depends-On: collectionUpdateReplacesMembership, collectionSetOperationsReportMutation
     */
    @Test public void validatedTransactionRejectsOverlappingSets() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.add(A);
        assertThrows(IllegalArgumentException.class, () -> collection.update(Collections.singleton(A), Collections.singleton(A)));
        assertEquals(Collections.singleton(101), idSet(collection));
    }

    /**
     * Verifies: CQE-TX-007, CQE-ERR-010
     * Seam: config interaction
     * Depends-On: queryOptionsPutGetRemoveRoundTrip, collectionUpdateReplacesMembership
     */
    @Test public void strictReplacementRejectsMissingRemovalWithoutMutation() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.add(A);
        Item missing = new Item(999, "void", 0, "none", null);
        assertFalse(collection.update(Collections.singleton(missing), Collections.singleton(D), queryOptions(enableFlags(TransactionalIndexedCollection.STRICT_REPLACEMENT))));
        assertEquals(Collections.singleton(101), idSet(collection));
    }

    /**
     * Verifies: CQE-TX-008
     * Seam: config interaction
     * Depends-On: queryOptionsPutGetRemoveRoundTrip, collectionUpdateReplacesMembership
     */
    @Test public void readUncommittedUpdatePreservesCollectionSemantics() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.add(C);
        assertTrue(collection.update(Collections.singleton(C), Collections.singleton(D), queryOptions(isolationLevel(IsolationLevel.READ_UNCOMMITTED))));
        assertEquals(Collections.singleton(104), idSet(collection));
    }

    /**
     * Verifies: CQE-TX-002, CQE-STATE-002, CQE-CVI-007
     * Seam: state consistency
     * CVI-7: the committed collection and its index agree after replacement.
     * Depends-On: collectionUpdateReplacesMembership, equalMatchesAnyMultiValue
     */
    @Test public void committedTransactionKeepsIndexConsistent() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.addAll(Arrays.asList(A, B));
        collection.addIndex(HashIndex.onAttribute(Item.CATEGORY));
        collection.update(Collections.singleton(B), Collections.singleton(C));
        assertEquals(idSet(collection), idSet(collection.retrieve(all(Item.class))));
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 103)), idSet(collection.retrieve(equal(Item.CATEGORY, "north"))));
    }

    /**
     * Verifies: CQE-TX-002, CQE-STATE-002, CQE-CVI-007
     * Seam: state consistency
     * CVI-7: a post-commit result is internally consistent across views.
     * Depends-On: resultContainsAndMatchesAreDistinctViews, collectionUpdateReplacesMembership
     */
    @Test public void committedTransactionResultViewsAgree() {
        TransactionalIndexedCollection<Item> collection = new TransactionalIndexedCollection<Item>(Item.class);
        collection.addAll(Arrays.asList(A, B));
        collection.update(Collections.singleton(B), Collections.singleton(C));
        ResultSet<Item> result = collection.retrieve(all(Item.class));
        assertEquals(2, result.size());
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 103)), idSet(result));
        assertTrue(result.contains(C));
        result.close();
    }

    /**
     * Verifies: CQE-COLL-010, CQE-ERR-011
     * Seam: error propagation
     * Depends-On: collectionSetOperationsReportMutation, metadataRequiresCompatibleIndex
     */
    @Test public void onHeapCollectionRejectsDiskIndex() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        assertThrows(IllegalStateException.class, () -> collection.addIndex(DiskIndex.onAttribute(Item.SCORE)));
    }

    /**
     * Verifies: CQE-PERS-003, CQE-PERS-004, CQE-PERS-008
     * Seam: lifecycle crossing
     * Depends-On: onHeapPersistenceReportsPrimaryKey, collectionSetOperationsReportMutation
     */
    @Test public void diskPersistenceUsesCallerSelectedFile() throws Exception {
        File file = freshDiskFile();
        DiskPersistence<Item, Integer> persistence = DiskPersistence.onPrimaryKeyInFile(Item.ID, file);
        try {
            IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>(persistence);
            collection.add(A);
            assertEquals(file.getAbsoluteFile(), persistence.getFile().getAbsoluteFile());
            assertTrue(file.exists());
        } finally {
            persistence.close();
            file.delete();
        }
    }

    /**
     * Verifies: CQE-PERS-006, CQE-STATE-003, CQE-CVI-008
     * Seam: lifecycle crossing
     * CVI-8: reopening preserves durable collection membership.
     * Depends-On: onHeapPersistenceReportsPrimaryKey, collectionSetOperationsReportMutation
     */
    @Test public void diskPopulationSurvivesReopen() throws Exception {
        File file = freshDiskFile();
        DiskPersistence<Item, Integer> first = DiskPersistence.onPrimaryKeyInFile(Item.ID, file);
        try {
            new ConcurrentIndexedCollection<Item>(first).addAll(Arrays.asList(A, B, C));
        } finally { first.close(); }
        DiskPersistence<Item, Integer> second = DiskPersistence.onPrimaryKeyInFile(Item.ID, file);
        try {
            assertEquals(new HashSet<Integer>(Arrays.asList(101, 102, 103)), idSet(new ConcurrentIndexedCollection<Item>(second)));
        } finally { second.close(); file.delete(); }
    }

    /**
     * Verifies: CQE-PERS-006, CQE-PERS-007, CQE-STATE-003, CQE-CVI-008
     * Seam: state consistency
     * CVI-8: rebuilt disk index query and metadata agree with reopened membership.
     * Depends-On: betweenHonorsBoundaryFlags, metadataRequiresCompatibleIndex
     */
    @Test public void reopenedDiskIndexAndMetadataAgree() throws Exception {
        File file = freshDiskFile();
        DiskPersistence<Item, Integer> first = DiskPersistence.onPrimaryKeyInFile(Item.ID, file);
        try { new ConcurrentIndexedCollection<Item>(first).addAll(Arrays.asList(A, B, C)); }
        finally { first.close(); }
        DiskPersistence<Item, Integer> second = DiskPersistence.onPrimaryKeyInFile(Item.ID, file);
        try {
            IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>(second);
            collection.addIndex(DiskIndex.onAttribute(Item.SCORE));
            assertEquals(new HashSet<Integer>(Arrays.asList(101, 102, 103)), idSet(collection.retrieve(between(Item.SCORE, 7, 11))));
            assertEquals(2L, integralCount(collection.getMetadataEngine().getSortedAttributeMetadata(Item.SCORE).getCountOfDistinctKeys()));
        } finally { second.close(); file.delete(); }
    }

    /**
     * Verifies: CQE-PERS-005, CQE-ERR-012
     * Seam: error propagation
     * Depends-On: onHeapPersistenceReportsPrimaryKey, collectionSetOperationsReportMutation
     */
    @Test public void inaccessibleDiskLocationRaisesIllegalState() throws Exception {
        File base = freshDiskFile();
        base.delete();
        File impossible = new File(new File(base.getParentFile(), "missing-parent-" + System.nanoTime()), "items.db");
        assertThrows(IllegalStateException.class, () -> {
            DiskPersistence<Item, Integer> persistence = DiskPersistence.onPrimaryKeyInFile(Item.ID, impossible);
            new ConcurrentIndexedCollection<Item>(persistence).add(A);
        });
    }

    /**
     * Verifies: CQE-COLL-016, CQE-PERS-007
     * Seam: protocol handoff
     * Depends-On: betweenHonorsBoundaryFlags, collectionSetOperationsReportMutation
     */
    @Test public void diskIndexSupportsInclusiveRangeQuery() throws Exception {
        File file = freshDiskFile();
        DiskPersistence<Item, Integer> persistence = DiskPersistence.onPrimaryKeyInFile(Item.ID, file);
        try {
            IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>(persistence);
            collection.addAll(Arrays.asList(A, B, C));
            collection.addIndex(DiskIndex.onAttribute(Item.SCORE));
            assertEquals(new HashSet<Integer>(Arrays.asList(101, 102, 103)), idSet(collection.retrieve(between(Item.SCORE, 7, 11))));
        } finally { persistence.close(); file.delete(); }
    }

    /**
     * Verifies: CQE-RES-008, CQE-RES-010
     * Seam: lifecycle crossing
     * Depends-On: closedResultRejectsInspection, allAndNoneAreComplements
     */
    @Test public void closingStreamClosesOriginatingResult() {
        IndexedCollection<Item> collection = populated();
        ResultSet<Item> result = collection.retrieve(all(Item.class));
        Stream<Item> stream = result.stream();
        assertEquals(4L, stream.count());
        stream.close();
        assertThrows(IllegalStateException.class, result::size);
    }

    /**
     * Verifies: CQE-COLL-006, CQE-COLL-007, CQE-COLL-008
     * Seam: lifecycle crossing
     * Depends-On: collectionSetOperationsReportMutation, equalMatchesAnyMultiValue
     */
    @Test public void removedAndReaddedIndexResynchronizesPopulation() {
        IndexedCollection<Item> collection = populated();
        Index<Item> index = HashIndex.onAttribute(Item.CATEGORY);
        collection.addIndex(index);
        collection.removeIndex(index);
        collection.add(E);
        collection.addIndex(index);
        assertEquals(new HashSet<Integer>(Arrays.asList(101, 103, 106)), idSet(collection.retrieve(equal(Item.CATEGORY, "north"))));
        assertEquals(1, indexCount(collection));
    }

    private static File freshDiskFile() throws Exception {
        File file = File.createTempFile("cqengine-oracle-", ".db");
        if (!file.delete()) throw new IllegalStateException("could not prepare temporary database path");
        return file;
    }

    private static long integralCount(long count) {
        return count;
    }

    private static long integralCount(Number count) {
        return count.longValue();
    }
}
