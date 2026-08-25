package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** Integration tests for pool population, capacity, ordering, and projections. */
class BorrowReturnIntegrationTest {

    /**
     * Verifies: CP-POOL-006, CP-XVIEW-001, CP-STATE-002.
     * Seam: state consistency between borrowing and population/counter views. CVI-1.
     * Depends-On: makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void preloadedBorrowMovesExactlyOneIdleObjectToActive() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 8, 8, 0)) {
            pool.addObject();
            long before = pool.getBorrowedCount();
            TestResource value = pool.borrowObject();
            assertEquals("resource-1", value.id());
            assertEquals(1, pool.getNumActive());
            assertEquals(0, pool.getNumIdle());
            assertEquals(before + 1, pool.getBorrowedCount());
            assertEquals(1, pool.listAllObjects().size());
        }
    }

    /**
     * Verifies: CP-POOL-007, CP-XVIEW-001, CP-OBS-002.
     * Seam: protocol handoff from factory creation into an allocated pool lease. CVI-1.
     * Depends-On: makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void emptyPoolBorrowCreatesActivatesAndCountsOneLease() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 8, 8, 0)) {
            TestResource value = pool.borrowObject();
            assertEquals("resource-1", value.id());
            assertEquals(1L, pool.getCreatedCount());
            assertEquals(1L, pool.getBorrowedCount());
            assertEquals(List.of("create", "wrap:resource-1", "activate:resource-1"), factory.callbacks());
        }
    }

    /**
     * Verifies: CP-POOL-012, CP-XVIEW-002, CP-STATE-002.
     * Seam: state consistency between return processing and idle/list views. CVI-2.
     * Depends-On: returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void successfulReturnMovesLeaseToIdleAndCountsIt() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 8, 8, 0)) {
            TestResource value = pool.borrowObject();
            pool.returnObject(value);
            assertEquals(0, pool.getNumActive());
            assertEquals(1, pool.getNumIdle());
            assertEquals(1L, pool.getReturnedCount());
            assertEquals(1, pool.listAllObjects().size());
            assertEquals(1L, factory.callbackCount("passivate:"));
        }
    }

    /**
     * Verifies: CP-POOL-015, CP-XVIEW-004.
     * Seam: config interaction between LIFO policy, idle order, and direct getter. CVI-4.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void lifoReturnsMostRecentlyReturnedValue() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 4, 4, 0)) {
            TestResource first = pool.borrowObject();
            TestResource second = pool.borrowObject();
            pool.returnObject(first);
            pool.returnObject(second);
            assertTrue(pool.getLifo());
            assertSame(second, pool.borrowObject());
        }
    }

    /**
     * Verifies: CP-POOL-015, CP-XVIEW-004.
     * Seam: config interaction between FIFO policy, idle order, and direct getter. CVI-4.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void fifoReturnsOldestReturnedValue() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, false, 4, 4, 0)) {
            TestResource first = pool.borrowObject();
            TestResource second = pool.borrowObject();
            pool.returnObject(first);
            pool.returnObject(second);
            assertFalse(pool.getLifo());
            assertSame(first, pool.borrowObject());
        }
    }

    /**
     * Verifies: CP-POOL-013, CP-XVIEW-003, CP-XVIEW-005.
     * Seam: state consistency between idle overflow, destruction, and capacity views. CVI-3, CVI-5.
     * Depends-On: negativeCapacityValuesArePreservedAsUnlimited, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void maxIdleOverflowDestroysReturnedValue() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 3, 1, 0)) {
            TestResource first = pool.borrowObject();
            TestResource second = pool.borrowObject();
            pool.returnObject(first);
            pool.returnObject(second);
            assertEquals(1, pool.getNumIdle());
            assertEquals(0, pool.getNumActive());
            assertEquals(1L, pool.getDestroyedCount());
            assertEquals(1L, factory.callbackCount("destroy:"));
        }
    }

    /**
     * Verifies: CP-POOL-019, CP-XVIEW-005, CP-STATE-004.
     * Seam: config interaction from min/max capacity into replenished idle state. CVI-5.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, makeObjectWrapsCreatedValue.
     */
    @Test void preparePoolHonorsEffectiveMinimumAndMaximum() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 3, 2, 4)) {
            pool.preparePool();
            assertEquals(2, pool.getMinIdle());
            assertEquals(2, pool.getNumIdle());
            assertEquals(2L, pool.getCreatedCount());
        }
    }

    /**
     * Verifies: CP-POOL-020, CP-XVIEW-003, CP-STATE-003.
     * Seam: lifecycle crossing from mixed active/idle population through clear. CVI-3.
     * Depends-On: returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void clearDestroysIdleObjectsButPreservesActiveLease() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, true, 4, 4, 0)) {
            TestResource active = pool.borrowObject();
            TestResource idle = pool.borrowObject();
            pool.returnObject(idle);
            pool.clear();
            assertEquals(1, pool.getNumActive());
            assertEquals(0, pool.getNumIdle());
            assertEquals(1L, pool.getDestroyedCount());
            assertSame(active, pool.listAllObjects().iterator().next().pooledObject().getObject());
        }
    }

    private static GenericObjectPool<TestResource, Exception> pool(
            RecordingFactory factory, boolean lifo, int maxTotal, int maxIdle, int minIdle) {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(false);
        config.setLifo(lifo);
        config.setMaxTotal(maxTotal);
        config.setMaxIdle(maxIdle);
        config.setMinIdle(minIdle);
        return new GenericObjectPool<>(factory, config);
    }
}

