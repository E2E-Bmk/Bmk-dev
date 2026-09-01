package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import org.apache.commons.pool3.DestroyMode;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** Integration tests for validation callbacks, invalidation, and eviction. */
class ValidationEvictionIntegrationTest {

    /**
     * Verifies: CP-VALID-003, CP-XVIEW-006.
     * Seam: protocol handoff from activation through borrow validation. CVI-6.
     * Depends-On: testOnBorrowFlagRoundTrips, baseFactoryDefaultsPreserveWrapperAndValidateTrue.
     */
    @Test void testOnBorrowRunsActivationBeforeValidation() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPoolConfig<TestResource> config = config();
        config.setTestOnBorrow(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            TestResource value = pool.borrowObject();
            assertEquals("resource-1", value.id());
            assertEquals(List.of("create", "wrap:resource-1", "activate:resource-1", "validate:resource-1"),
                    factory.callbacks());
        }
    }

    /**
     * Verifies: CP-VALID-005, CP-XVIEW-006.
     * Seam: protocol handoff from return validation into passivation. CVI-6.
     * Depends-On: testOnReturnFlagRoundTrips, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void testOnReturnRunsValidationBeforePassivation() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPoolConfig<TestResource> config = config();
        config.setTestOnReturn(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            TestResource value = pool.borrowObject();
            factory.clearCallbacks();
            pool.returnObject(value);
            assertEquals(List.of("validate:resource-1", "passivate:resource-1"), factory.callbacks());
            assertEquals(1, pool.getNumIdle());
        }
    }

    /**
     * Verifies: CP-VALID-006, CP-XVIEW-003, CP-XVIEW-006.
     * Seam: state consistency after return validation rejects a lease. CVI-3, CVI-6.
     * Depends-On: testOnReturnFlagRoundTrips, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void returnValidationFailureDestroysAndStillCountsReturn() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPoolConfig<TestResource> config = config();
        config.setTestOnReturn(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            TestResource value = pool.borrowObject();
            factory.setValid(false);
            pool.returnObject(value);
            assertEquals(0, pool.getNumActive());
            assertEquals(0, pool.getNumIdle());
            assertEquals(1L, pool.getReturnedCount());
            assertEquals(1L, pool.getDestroyedCount());
        }
    }

    /**
     * Verifies: CP-VALID-011, CP-VALID-012.
     * Seam: error propagation from passivation into destruction and swallowed listener.
     * Depends-On: returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue, baseFactoryDefaultsPreserveWrapperAndValidateTrue.
     */
    @Test void passivationFailureNotifiesListenerAndFreesCapacity() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        List<Exception> swallowed = new ArrayList<>();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config())) {
            pool.setSwallowedExceptionListener(swallowed::add);
            TestResource value = pool.borrowObject();
            factory.setFailPassivation(true);
            pool.returnObject(value);
            assertEquals(1, swallowed.size());
            assertEquals(1L, pool.getDestroyedCount());
            assertEquals(0, pool.getNumActive() + pool.getNumIdle());
        }
    }

    /**
     * Verifies: CP-VALID-007, CP-XVIEW-003.
     * Seam: state consistency across explicit invalidation, destroy mode, and projections. CVI-3.
     * Depends-On: destroyModeVocabularyDistinguishesNormalAndAbandoned, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void invalidationUsesSuppliedModeAndRemovesActiveLease() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config())) {
            TestResource value = pool.borrowObject();
            pool.invalidateObject(value, DestroyMode.ABANDONED);
            assertEquals(List.of(DestroyMode.ABANDONED), factory.destroyModes());
            assertEquals(0, pool.getNumActive());
            assertEquals(0, pool.listAllObjects().size());
            assertEquals(1L, pool.getDestroyedCount());
        }
    }

    /**
     * Verifies: CP-EVICT-002, CP-EVICT-005, CP-XVIEW-003.
     * Seam: lifecycle crossing from idle aging through eviction and counter removal. CVI-3.
     * Depends-On: hardThresholdEvictsOldIdleWrapper, maintenanceSettingsRoundTripExactValues.
     */
    @Test void customEvictionPolicyRemovesWrapperAndCountsReason() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPoolConfig<TestResource> config = config();
        config.setEvictionPolicy((evictionConfig, underTest, idleCount) -> true);
        config.setNumTestsPerEvictionRun(1);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            pool.addObject();
            pool.evict();
            assertEquals(0, pool.getNumIdle());
            assertEquals(1L, pool.getDestroyedCount());
            assertEquals(1L, pool.getDestroyedByEvictorCount());
        }
    }

    /**
     * Verifies: CP-EVICT-006, CP-XVIEW-006.
     * Seam: protocol handoff across eviction retention, activation, validation, and passivation. CVI-6.
     * Depends-On: testWhileIdleFlagRoundTrips, baseFactoryDefaultsPreserveWrapperAndValidateTrue.
     */
    @Test void retainedIdleValidationRunsFullCallbackCycle() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPoolConfig<TestResource> config = config();
        config.setTestWhileIdle(true);
        config.setNumTestsPerEvictionRun(1);
        config.setEvictionPolicy((evictionConfig, underTest, idleCount) -> false);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            pool.addObject();
            factory.clearCallbacks();
            pool.evict();
            assertEquals(List.of("activate:resource-1", "validate:resource-1", "passivate:resource-1"),
                    factory.callbacks());
            assertEquals(1, pool.getNumIdle());
        }
    }

    /**
     * Verifies: CP-EVICT-008, CP-VALID-012.
     * Seam: error propagation from custom policy failure to listener while retaining state.
     * Depends-On: concreteEvictionPolicyCanBeSelected, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void throwingEvictionPolicyIsSwallowedAndRetainsWrapper() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        List<Exception> swallowed = new ArrayList<>();
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config())) {
            pool.setSwallowedExceptionListener(swallowed::add);
            pool.setEvictionPolicy((evictionConfig, underTest, idleCount) -> {
                throw new IllegalStateException("policy failure from test fixture");
            });
            pool.addObject();
            pool.evict();
            assertEquals(1, swallowed.size());
            assertEquals(1, pool.getNumIdle());
            assertEquals(0L, pool.getDestroyedByEvictorCount());
        }
    }

    private static GenericObjectPoolConfig<TestResource> config() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(false);
        config.setMaxTotal(4);
        config.setMaxIdle(4);
        config.setDurationBetweenEvictionRuns(Duration.ZERO);
        return config;
    }
}
