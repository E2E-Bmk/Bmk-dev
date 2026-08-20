package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.time.Instant;
import org.apache.commons.pool3.DestroyMode;
import org.apache.commons.pool3.impl.AbandonedConfig;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** Integration tests for abandoned-lease detection and recovery. */
class AbandonmentIntegrationTest {

    /**
     * Verifies: CP-POOL-001, CP-ABAND-002.
     * Seam: config interaction between constructor snapshot and pool getters.
     * Depends-On: copyIsDistinctAndPreservesAllPolicyValues, defaultRemovalTriggersAreDisabled.
     */
    @Test void constructorCopiesAbandonedConfiguration() {
        RecordingFactory factory = new RecordingFactory();
        AbandonedConfig abandoned = abandonment(Duration.ofSeconds(37), true, false);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config(3), abandoned)) {
            abandoned.setRemoveAbandonedOnBorrow(false);
            abandoned.setRemoveAbandonedTimeout(Duration.ofSeconds(91));
            assertTrue(pool.getRemoveAbandonedOnBorrow());
            assertEquals(Duration.ofSeconds(37), pool.getRemoveAbandonedTimeoutDuration());
        }
    }

    /**
     * Verifies: CP-ABAND-002.
     * Seam: config interaction between setter snapshot and later caller mutation.
     * Depends-On: copyIsDistinctAndPreservesAllPolicyValues, removalTriggerSettersRoundTripIndependently.
     */
    @Test void setterCopiesAbandonedConfiguration() {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config(3))) {
            AbandonedConfig abandoned = abandonment(Duration.ofSeconds(29), false, true);
            pool.setAbandonedConfig(abandoned);
            abandoned.setRemoveAbandonedOnMaintenance(false);
            abandoned.setRemoveAbandonedTimeout(Duration.ofSeconds(72));
            assertTrue(pool.getRemoveAbandonedOnMaintenance());
            assertEquals(Duration.ofSeconds(29), pool.getRemoveAbandonedTimeoutDuration());
        }
    }

    /**
     * Verifies: CP-ABAND-004, CP-ABAND-005, CP-XVIEW-008.
     * Seam: lifecycle crossing from expired active lease through maintenance destruction. CVI-8.
     * Depends-On: defaultTimeoutIsFiveMinutes, destroyModeVocabularyDistinguishesNormalAndAbandoned, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void maintenanceRemovesExpiredLeaseWithAbandonedMode() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        AbandonedConfig abandoned = abandonment(Duration.ZERO, false, true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config(2), abandoned)) {
            pool.borrowObject();
            Thread.sleep(3L);
            pool.evict();
            assertEquals(0, pool.getNumActive());
            assertEquals(1L, pool.getDestroyedCount());
            assertEquals(DestroyMode.ABANDONED, factory.destroyModes().get(0));
            assertEquals(0, pool.listAllObjects().size());
        }
    }

    /**
     * Verifies: CP-ABAND-008, CP-XVIEW-008.
     * Seam: error propagation is suppressed for late return after abandonment. CVI-8.
     * Depends-On: defaultTimeoutIsFiveMinutes, destroyModeVocabularyDistinguishesNormalAndAbandoned, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount, returningThenDeallocatingRestoresIdleState.
     */
    @Test void lateReturnAfterAbandonmentIsTolerated() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(
                factory, config(2), abandonment(Duration.ZERO, false, true))) {
            TestResource value = pool.borrowObject();
            Thread.sleep(3L);
            pool.evict();
            long destroyed = pool.getDestroyedCount();
            pool.returnObject(value);
            assertEquals(destroyed, pool.getDestroyedCount());
            assertEquals(0, pool.getNumActive() + pool.getNumIdle());
        }
    }

    /**
     * Verifies: CP-ABAND-008, CP-XVIEW-008.
     * Seam: error propagation is suppressed for late invalidation after abandonment. CVI-8.
     * Depends-On: defaultTimeoutIsFiveMinutes, destroyModeVocabularyDistinguishesNormalAndAbandoned, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void lateInvalidationAfterAbandonmentIsTolerated() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(
                factory, config(2), abandonment(Duration.ZERO, false, true))) {
            TestResource value = pool.borrowObject();
            Thread.sleep(3L);
            pool.evict();
            long destroyed = pool.getDestroyedCount();
            pool.invalidateObject(value);
            assertEquals(destroyed, pool.getDestroyedCount());
            assertEquals(0, pool.listAllObjects().size());
        }
    }

    /**
     * Verifies: CP-ABAND-003, CP-ABAND-005, CP-XVIEW-008.
     * Seam: config interaction from borrow-time trigger to capacity recovery. CVI-8.
     * Depends-On: removalTriggerSettersRoundTripIndependently, settersRoundTripOrderingWaitAndCapacity, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void borrowTriggerRecoversCapacityFromExpiredLeases() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(
                factory, config(2), abandonment(Duration.ZERO, true, false))) {
            pool.borrowObject();
            pool.borrowObject();
            Thread.sleep(3L);
            TestResource replacement = pool.borrowObject(Duration.ofMillis(40));
            assertEquals("resource-3", replacement.id());
            assertEquals(1, pool.getNumActive());
            assertEquals(2L, pool.getDestroyedCount());
            assertEquals(2, factory.destroyModes().stream().filter(mode -> mode == DestroyMode.ABANDONED).count());
        }
    }

    /**
     * Verifies: CP-ABAND-007, CP-XVIEW-008.
     * Seam: state consistency between usage tracking and wrapper last-used projection. CVI-8.
     * Depends-On: usageAndTraceOptionsRoundTripExactValues, newWrapperStartsIdleWithCoincidentInstants.
     */
    @Test void poolUseUpdatesManagedWrapperLastUsedProjection() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        AbandonedConfig abandoned = abandonment(Duration.ofSeconds(5), false, false);
        abandoned.setUseUsageTracking(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config(2), abandoned)) {
            TestResource value = pool.borrowObject();
            Instant before = pool.listAllObjects().iterator().next().pooledObject().getLastUsedInstant();
            Thread.sleep(3L);
            pool.use(value);
            Instant after = pool.listAllObjects().iterator().next().pooledObject().getLastUsedInstant();
            assertTrue(after.isAfter(before));
            assertEquals(1, pool.getNumActive());
        }
    }

    private static GenericObjectPoolConfig<TestResource> config(final int maxTotal) {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(false);
        config.setMaxTotal(maxTotal);
        config.setMaxIdle(maxTotal);
        config.setDurationBetweenEvictionRuns(Duration.ZERO);
        return config;
    }

    private static AbandonedConfig abandonment(
            final Duration timeout, final boolean onBorrow, final boolean onMaintenance) {
        AbandonedConfig config = new AbandonedConfig();
        config.setRemoveAbandonedTimeout(timeout);
        config.setRemoveAbandonedOnBorrow(onBorrow);
        config.setRemoveAbandonedOnMaintenance(onMaintenance);
        return config;
    }
}
