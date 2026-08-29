package atomic;

import com.googlecode.cqengine.ConcurrentIndexedCollection;
import com.googlecode.cqengine.IndexedCollection;
import com.googlecode.cqengine.index.Index;
import com.googlecode.cqengine.persistence.onheap.OnHeapPersistence;
import com.googlecode.cqengine.query.Query;
import com.googlecode.cqengine.query.logical.And;
import com.googlecode.cqengine.query.option.AttributeOrder;
import com.googlecode.cqengine.query.option.QueryOptions;
import com.googlecode.cqengine.resultset.ResultSet;
import com.googlecode.cqengine.resultset.common.NoSuchObjectException;
import com.googlecode.cqengine.resultset.common.NonUniqueObjectException;
import org.junit.Test;
import support.Item;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.regex.PatternSyntaxException;

import static com.googlecode.cqengine.query.QueryFactory.*;
import static org.junit.Assert.*;

public class CqEngineAtomicTest {
    private static final Item A = new Item(101, "amber", 7, "north", null, "red", "soft");
    private static final Item B = new Item(102, "basil", 11, "south", 2, "blue", "soft");
    private static final Item C = new Item(103, "cedar", 11, "north", 1, "red", "dense");

    private static <T> List<T> list(Iterable<T> values) {
        List<T> result = new ArrayList<T>();
        for (T value : values) result.add(value);
        return result;
    }

    /** Verifies: CQE-ATTR-001 */
    @Test public void attributeMetadataReportsConfiguredTypes() {
        assertEquals(Item.class, Item.ID.getObjectType());
        assertEquals(Integer.class, Item.ID.getAttributeType());
        assertEquals("id", Item.ID.getAttributeName());
    }

    /** Verifies: CQE-ATTR-002 */
    @Test public void simpleAttributeYieldsOneValue() {
        assertEquals(Collections.singletonList(101), list(Item.ID.getValues(A, noQueryOptions())));
    }

    /** Verifies: CQE-ATTR-003 */
    @Test public void nullableAttributeOmitsNull() {
        assertEquals(Collections.emptyList(), list(Item.RANK.getValues(A, noQueryOptions())));
    }

    /** Verifies: CQE-ATTR-003 */
    @Test public void nullableAttributeYieldsPresentValue() {
        assertEquals(Collections.singletonList(2), list(Item.RANK.getValues(B, noQueryOptions())));
    }

    /** Verifies: CQE-ATTR-004 */
    @Test public void multiAttributePreservesValues() {
        assertEquals(Arrays.asList("red", "soft"), list(Item.TAGS.getValues(A, noQueryOptions())));
    }

    /** Verifies: CQE-ATTR-007 */
    @Test public void selfAttributeReturnsObject() {
        assertSame(A, selfAttribute(Item.class).getValue(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-010, CQE-ATTR-031 */
    @Test public void equalMatchesAnyMultiValue() {
        assertTrue(equal(Item.TAGS, "red").matches(A, noQueryOptions()));
        assertFalse(equal(Item.TAGS, "red").matches(B, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-012 */
    @Test public void emptyInMatchesNothing() {
        assertFalse(in(Item.ID, Collections.<Integer>emptyList()).matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-013 */
    @Test public void singletonInBehavesLikeEqual() {
        assertEquals(equal(Item.ID, 101).matches(A, noQueryOptions()), in(Item.ID, 101).matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-014 */
    @Test public void exclusiveAndInclusiveRangesDiffer() {
        assertFalse(lessThan(Item.SCORE, 11).matches(B, noQueryOptions()));
        assertTrue(lessThanOrEqualTo(Item.SCORE, 11).matches(B, noQueryOptions()));
        assertTrue(greaterThanOrEqualTo(Item.SCORE, 11).matches(B, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-015, CQE-ATTR-016 */
    @Test public void betweenHonorsBoundaryFlags() {
        assertTrue(between(Item.SCORE, 7, 19).matches(A, noQueryOptions()));
        assertFalse(between(Item.SCORE, 7, false, 19, false).matches(A, noQueryOptions()));
        assertTrue(between(Item.SCORE, 7, false, 19, false).matches(B, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-017 */
    @Test public void hasObservesNullableProjection() {
        assertFalse(has(Item.RANK).matches(A, noQueryOptions()));
        assertTrue(has(Item.RANK).matches(B, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-018 */
    @Test public void allAndNoneAreComplements() {
        assertTrue(all(Item.class).matches(A, noQueryOptions()));
        assertFalse(none(Item.class).matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-022 */
    @Test public void stringPrefixSuffixAndContainsMatch() {
        assertTrue(startsWith(Item.NAME, "am").matches(A, noQueryOptions()));
        assertTrue(endsWith(Item.NAME, "il").matches(B, noQueryOptions()));
        assertTrue(contains(Item.NAME, "eda").matches(C, noQueryOptions()));
        assertFalse(startsWith(Item.NAME, "Am").matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-023 */
    @Test public void emptyStringFragmentsMatch() {
        assertTrue(startsWith(Item.NAME, "").matches(A, noQueryOptions()));
        assertTrue(endsWith(Item.NAME, "").matches(A, noQueryOptions()));
        assertTrue(contains(Item.NAME, "").matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-024 */
    @Test public void inverseContainmentWorks() {
        assertTrue(isContainedIn(Item.NAME, "xxamberyy").matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-025 */
    @Test public void inversePrefixWorks() {
        assertTrue(isPrefixOf(Item.NAME, "amberlight").matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-026 */
    @Test public void regexMatchesEntireValue() {
        assertTrue(matchesRegex(Item.NAME, "a.*r").matches(A, noQueryOptions()));
        assertFalse(matchesRegex(Item.NAME, "mbe").matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-028 */
    @Test public void andRequiresEveryChild() {
        assertTrue(and(equal(Item.CATEGORY, "north"), greaterThan(Item.SCORE, 6)).matches(A, noQueryOptions()));
        assertFalse(and(equal(Item.CATEGORY, "north"), greaterThan(Item.SCORE, 9)).matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-029 */
    @Test public void orAcceptsAnyChild() {
        assertTrue(or(equal(Item.ID, 102), equal(Item.ID, 103)).matches(B, noQueryOptions()));
        assertFalse(or(equal(Item.ID, 101), equal(Item.ID, 103)).matches(B, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-030 */
    @Test public void notNegatesChild() {
        assertTrue(not(equal(Item.CATEGORY, "south")).matches(A, noQueryOptions()));
        assertFalse(not(equal(Item.CATEGORY, "north")).matches(A, noQueryOptions()));
    }

    /** Verifies: CQE-ATTR-031 */
    @Test public void queryOptionsPutGetRemoveRoundTrip() {
        QueryOptions options = noQueryOptions();
        options.put(String.class, "token");
        assertEquals("token", options.get(String.class));
        options.remove(String.class);
        assertNull(options.get(String.class));
    }

    /** Verifies: CQE-RES-016 */
    @Test public void attributeOrderReportsDirection() {
        AttributeOrder<Item> ascending = ascending(Item.ID);
        AttributeOrder<Item> descending = descending(Item.ID);
        assertSame(Item.ID, ascending.getAttribute());
        assertFalse(ascending.isDescending());
        assertTrue(descending.isDescending());
    }

    /** Verifies: CQE-COLL-001, CQE-COLL-002 */
    @Test public void collectionSetOperationsReportMutation() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        assertTrue(collection.add(A));
        assertFalse(collection.add(A));
        assertTrue(collection.addAll(Arrays.asList(B, C)));
        assertEquals(3, collection.size());
        assertTrue(collection.remove(B));
        assertEquals(2, collection.toArray().length);
    }

    /** Verifies: CQE-COLL-003 */
    @Test public void collectionUpdateReplacesMembership() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        assertTrue(collection.update(Collections.singleton(A), Collections.singleton(C)));
        assertEquals(new java.util.HashSet<Item>(Arrays.asList(B, C)), new java.util.HashSet<Item>(collection));
    }

    /** Verifies: CQE-PERS-001, CQE-PERS-002 */
    @Test public void onHeapPersistenceReportsPrimaryKey() {
        assertNull(OnHeapPersistence.withoutPrimaryKey().getPrimaryKeyAttribute());
        assertSame(Item.ID, OnHeapPersistence.onPrimaryKey(Item.ID).getPrimaryKeyAttribute());
    }

    /** Verifies: CQE-RES-005 */
    @Test public void uniqueResultReturnsSingleObject() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        assertSame(B, collection.retrieve(equal(Item.ID, 102)).uniqueResult());
    }

    /** Verifies: CQE-RES-003, CQE-RES-004 */
    @Test public void resultContainsAndMatchesAreDistinctViews() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.add(A);
        ResultSet<Item> result = collection.retrieve(equal(Item.CATEGORY, "north"));
        Item unstoredMatch = new Item(999, "fir", 5, "north", null);
        assertFalse(result.contains(unstoredMatch));
        assertTrue(result.matches(unstoredMatch));
        result.close();
    }

    /** Verifies: CQE-ATTR-019, CQE-ERR-001 */
    @Test public void nullAttributeIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> equal(null, 1));
    }

    /** Verifies: CQE-ATTR-020, CQE-ERR-002 */
    @Test public void nullEqualityValueIsRejected() {
        assertThrows(NullPointerException.class, () -> equal(Item.ID, null));
    }

    /** Verifies: CQE-ATTR-021, CQE-ERR-002 */
    @Test public void nullInCollectionIsRejected() {
        assertThrows(NullPointerException.class, () -> in(Item.ID, (Collection<Integer>) null));
    }

    /** Verifies: CQE-ATTR-027, CQE-ERR-003 */
    @Test public void invalidRegexIsRejected() {
        assertThrows(PatternSyntaxException.class, () -> matchesRegex(Item.NAME, "["));
    }

    /** Verifies: CQE-ATTR-032 */
    @Test public void nullLogicalChildrenAreRejected() {
        assertThrows(NullPointerException.class, () -> new And<Item>((Collection<Query<Item>>) null));
    }

    /** Verifies: CQE-RES-019, CQE-ERR-004 */
    @Test public void emptyOrderListIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> orderBy(Collections.<AttributeOrder<Item>>emptyList()));
    }

    /** Verifies: CQE-RES-006, CQE-ERR-006 */
    @Test public void emptyUniqueResultIsRejected() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        assertThrows(NoSuchObjectException.class, () -> collection.retrieve(all(Item.class)).uniqueResult());
    }

    /** Verifies: CQE-RES-007, CQE-ERR-007 */
    @Test public void multipleUniqueResultIsRejected() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.addAll(Arrays.asList(A, B));
        assertThrows(NonUniqueObjectException.class, () -> collection.retrieve(all(Item.class)).uniqueResult());
    }

    /** Verifies: CQE-META-004, CQE-ERR-005 */
    @Test public void metadataRequiresCompatibleIndex() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        assertThrows(IllegalStateException.class, () -> collection.getMetadataEngine().getAttributeMetadata(Item.CATEGORY));
    }

    /** Verifies: CQE-RES-009, CQE-RES-010 */
    @Test public void closedResultRejectsInspection() {
        IndexedCollection<Item> collection = new ConcurrentIndexedCollection<Item>();
        collection.add(A);
        ResultSet<Item> result = collection.retrieve(all(Item.class));
        result.close();
        assertThrows(IllegalStateException.class, result::size);
    }

}
