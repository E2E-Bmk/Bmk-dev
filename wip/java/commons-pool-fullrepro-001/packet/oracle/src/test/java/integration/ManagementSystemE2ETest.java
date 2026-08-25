package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.management.ManagementFactory;
import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import javax.management.MBeanServer;
import javax.management.ObjectName;
import org.apache.commons.pool3.PooledObjectState;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.apache.commons.pool3.impl.GenericObjectPoolMXBean;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** System and integration tests for statistics and management projections. */
class ManagementSystemE2ETest {

    /**
     * Verifies: CP-OBS-001, CP-OBS-002, CP-OBS-013, CP-XVIEW-001, CP-XVIEW-002.
     * Seam: state consistency across operations, direct counters, and MXBean view. CVI-1, CVI-2.
     * Depends-On: makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount, returningThenDeallocatingRestoresIdleState.
     */
    @Test void mxBeanTracksBorrowAndReturnPopulationAndCounters() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 3, 3, false)) {
            GenericObjectPoolMXBean bean = pool;
            TestResource value = pool.borrowObject();
            assertEquals(pool.getNumActive(), bean.getNumActive());
            assertEquals(pool.getBorrowedCount(), bean.getBorrowedCount());
            pool.returnObject(value);
            assertEquals(pool.getNumIdle(), bean.getNumIdle());
            assertEquals(pool.getReturnedCount(), bean.getReturnedCount());
        }
    }

    /**
     * Verifies: CP-XVIEW-004, CP-OBS-013.
     * Seam: config interaction across ordering behavior, direct getter, and MXBean view. CVI-4.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void orderingSetterAndMxBeanRemainConsistent() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 3, 3, false)) {
            GenericObjectPoolMXBean bean = pool;
            pool.setLifo(false);
            TestResource first = pool.borrowObject();
            TestResource second = pool.borrowObject();
            pool.returnObject(first);
            pool.returnObject(second);
            assertFalse(pool.getLifo());
            assertFalse(bean.getLifo());
            assertSame(first, pool.borrowObject());
        }
    }

    /**
     * Verifies: CP-XVIEW-005, CP-OBS-013.
     * Seam: config interaction across capacity setters, replenishment, and MXBean getters. CVI-5.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, makeObjectWrapsCreatedValue.
     */
    @Test void capacitySettersConstrainPopulationAndMxBeanReportsThem() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 5, 5, false)) {
            GenericObjectPoolMXBean bean = pool;
            pool.setMaxTotal(3);
            pool.setMaxIdle(2);
            pool.setMinIdle(2);
            pool.preparePool();
            assertEquals(3, bean.getMaxTotal());
            assertEquals(2, bean.getMaxIdle());
            assertEquals(2, bean.getMinIdle());
            assertEquals(2, bean.getNumIdle());
        }
    }

    /**
     * Verifies: CP-OBS-006, CP-OBS-007, CP-STATE-002.
     * Seam: state consistency between mixed leases and per-wrapper management records.
     * Depends-On: infoProjectsBorrowedCount, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void listAllObjectsProjectsOneActiveAndOneIdleWrapper() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 3, 3, false)) {
            TestResource active = pool.borrowObject();
            TestResource idle = pool.borrowObject();
            pool.returnObject(idle);
            long allocated = pool.listAllObjects().stream()
                    .filter(info -> info.pooledObject().getState() == PooledObjectState.ALLOCATED).count();
            long queued = pool.listAllObjects().stream()
                    .filter(info -> info.pooledObject().getState() == PooledObjectState.IDLE).count();
            assertEquals(2, pool.listAllObjects().size());
            assertEquals(1L, allocated);
            assertEquals(1L, queued);
            assertTrue(pool.listAllObjects().stream()
                    .anyMatch(info -> info.pooledObject().getObject() == active));
        }
    }

    /**
     * Verifies: CP-OBS-011, CP-OBS-014, CP-XVIEW-007.
     * Seam: lifecycle crossing from JMX registration through pool close and unregistration. CVI-7.
     * Depends-On: defaultExhaustionAndFairnessValuesMatchContract, nullFactoryConstructorRaisesIllegalArgument, defaultCapacityValuesMatchContract.
     */
    @Test void registeredManagementNameIsRemovedOnClose() throws Exception {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(true);
        config.setJmxNamePrefix("oracle" + System.nanoTime());
        GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(new RecordingFactory(), config);
        ObjectName name = pool.getJmxName();
        MBeanServer server = ManagementFactory.getPlatformMBeanServer();
        assertNotNull(name);
        assertTrue(server.isRegistered(name));
        pool.close();
        assertFalse(server.isRegistered(name));
        assertTrue(pool.isClosed());
    }

    /**
     * Verifies: CP-POOL-021, CP-POOL-022, CP-XVIEW-007, CP-STATE-005.
     * Seam: lifecycle crossing from close cleanup through late outstanding return. CVI-7.
     * Depends-On: returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount, nullFactoryConstructorRaisesIllegalArgument, defaultCapacityValuesMatchContract.
     */
    @Test void closeDestroysIdleThenLateReturnDestroysOutstandingLease() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPool<TestResource, Exception> pool = pool(factory, 3, 3, false);
        TestResource active = pool.borrowObject();
        TestResource idle = pool.borrowObject();
        pool.returnObject(idle);
        pool.close();
        assertTrue(pool.isClosed());
        assertEquals(0, pool.getNumIdle());
        assertEquals(1L, pool.getDestroyedCount());
        pool.returnObject(active);
        assertEquals(0, pool.getNumActive());
        assertEquals(2L, pool.getDestroyedCount());
    }

    /**
     * Verifies: CP-POOL-008, CP-OBS-003, CP-XVIEW-007.
     * Seam: protocol handoff between waiting borrower, release, waiter estimate, and resumed lease. CVI-7.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount, returningThenDeallocatingRestoresIdleState.
     */
    @Test void waitingBorrowerIsCountedAndReceivesReleasedValue() throws Exception {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(false);
        config.setMaxTotal(1);
        config.setBlockWhenExhausted(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(new RecordingFactory(), config)) {
            TestResource held = pool.borrowObject();
            ExecutorService executor = Executors.newSingleThreadExecutor();
            try {
                Future<TestResource> waiting = executor.submit(() -> pool.borrowObject(Duration.ofSeconds(2)));
                long deadline = System.nanoTime() + Duration.ofSeconds(1).toNanos();
                while (pool.getNumWaiters() == 0 && System.nanoTime() < deadline) {
                    Thread.onSpinWait();
                }
                assertEquals(1, pool.getNumWaiters());
                pool.returnObject(held);
                TestResource resumed = waiting.get(1, TimeUnit.SECONDS);
                assertSame(held, resumed);
                assertEquals(0, pool.getNumWaiters());
                pool.returnObject(resumed);
            } finally {
                executor.shutdownNow();
            }
        }
    }

    private static GenericObjectPool<TestResource, Exception> pool(
            RecordingFactory factory, int maxTotal, int maxIdle, boolean jmx) {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(jmx);
        config.setMaxTotal(maxTotal);
        config.setMaxIdle(maxIdle);
        return new GenericObjectPool<>(factory, config);
    }
}
