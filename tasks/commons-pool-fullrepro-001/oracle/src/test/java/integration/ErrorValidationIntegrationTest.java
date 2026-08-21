package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.util.NoSuchElementException;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;
import support.RecordingFactory;
import support.TestResource;

/** Integration tests for public failure paths across factories and pools. */
class ErrorValidationIntegrationTest {

    /**
     * Verifies: CP-FACT-005, CP-ERR-002.
     * Seam: error propagation from factory creation through pool borrow.
     * Depends-On: makeObjectRejectsNullCreation, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void nullFactoryProductPropagatesAsNullPointerException() {
        RecordingFactory factory = new RecordingFactory();
        factory.setCreateNull(true);
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, 1, true)) {
            assertThrows(NullPointerException.class, pool::borrowObject);
        }
    }

    /**
     * Verifies: CP-POOL-021, CP-ERR-003, CP-STATE-005.
     * Seam: lifecycle crossing from close into the borrow operation.
     * Depends-On: nullFactoryConstructorRaisesIllegalArgument, defaultCapacityValuesMatchContract.
     */
    @Test void borrowAfterCloseRaisesIllegalState() {
        GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 1, true);
        pool.close();
        assertTrue(pool.isClosed());
        assertThrows(IllegalStateException.class, pool::borrowObject);
    }

    /**
     * Verifies: CP-POOL-021, CP-ERR-003, CP-STATE-005.
     * Seam: lifecycle crossing from close into idle-object creation.
     * Depends-On: nullFactoryConstructorRaisesIllegalArgument, defaultCapacityValuesMatchContract.
     */
    @Test void addAfterCloseRaisesIllegalState() {
        GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 1, true);
        pool.close();
        assertEquals(0, pool.getNumIdle());
        assertThrows(IllegalStateException.class, pool::addObject);
    }

    /**
     * Verifies: CP-POOL-009, CP-ERR-004.
     * Seam: config interaction between non-blocking exhaustion and capacity.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void nonBlockingExhaustionRaisesNoSuchElement() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 1, false)) {
            pool.borrowObject();
            assertThrows(NoSuchElementException.class, pool::borrowObject);
            assertEquals(1, pool.getNumActive());
        }
    }

    /**
     * Verifies: CP-POOL-008, CP-POOL-010, CP-ERR-004.
     * Seam: config interaction between finite waiting and exhausted capacity.
     * Depends-On: settersRoundTripOrderingWaitAndCapacity, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void finiteBlockingWaitExpiresWithNoSuchElement() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(new RecordingFactory(), 1, true)) {
            pool.borrowObject();
            assertThrows(NoSuchElementException.class, () -> pool.borrowObject(Duration.ofMillis(12)));
        }
    }

    /**
     * Verifies: CP-VALID-010, CP-ERR-005, CP-XVIEW-006.
     * Seam: error propagation from activation failure to destruction and borrow result. CVI-6.
     * Depends-On: baseFactoryDefaultsPreserveWrapperAndValidateTrue, makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount.
     */
    @Test void activationFailureDestroysNewWrapperAndPreservesCause() {
        RecordingFactory factory = new RecordingFactory();
        factory.setFailActivation(true);
        try (GenericObjectPool<TestResource, Exception> pool = pool(factory, 1, true)) {
            NoSuchElementException failure = assertThrows(
                    NoSuchElementException.class, () -> pool.borrowObject(Duration.ofMillis(30)));
            assertNotNull(failure.getCause());
            assertEquals(1L, pool.getDestroyedCount());
            assertEquals(0, pool.getNumActive());
        }
    }

    /**
     * Verifies: CP-VALID-001, CP-VALID-002, CP-ERR-005, CP-XVIEW-006.
     * Seam: error propagation from create-time validation to population counters. CVI-6.
     * Depends-On: testOnCreateFlagRoundTrips, makeObjectWrapsCreatedValue.
     */
    @Test void createValidationFailureRejectsAndRemovesWrapper() {
        RecordingFactory factory = new RecordingFactory();
        factory.setValid(false);
        GenericObjectPoolConfig<TestResource> config = config(1, true);
        config.setTestOnCreate(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            assertThrows(NoSuchElementException.class, () -> pool.borrowObject(Duration.ofMillis(30)));
            assertEquals(0, pool.getNumActive());
            assertEquals(0, pool.getNumIdle());
            assertEquals(1L, factory.callbackCount("validate:"));
        }
    }

    /**
     * Verifies: CP-VALID-003, CP-VALID-004, CP-XVIEW-003, CP-XVIEW-006.
     * Seam: state consistency after borrow validation rejects an idle wrapper. CVI-3, CVI-6.
     * Depends-On: testOnBorrowFlagRoundTrips, returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void borrowValidationRejectionDestroysIdleWrapper() throws Exception {
        RecordingFactory factory = new RecordingFactory();
        GenericObjectPoolConfig<TestResource> config = config(1, true);
        config.setTestOnBorrow(true);
        try (GenericObjectPool<TestResource, Exception> pool = new GenericObjectPool<>(factory, config)) {
            pool.addObject();
            factory.setValid(false);
            assertThrows(NoSuchElementException.class, () -> pool.borrowObject(Duration.ofMillis(30)));
            assertEquals(0, pool.getNumIdle());
            assertEquals(0, pool.getNumActive());
            assertTrue(pool.getDestroyedByBorrowValidationCount() >= 1L);
        }
    }

    /**
     * Verifies: CP-VALID-008, CP-VALID-009, CP-ERR-006.
     * Seam: error propagation from identity membership checks through return and invalidation.
     * Depends-On: makeObjectWrapsCreatedValue, allocationUpdatesStateAndBorrowCount, destroyModeVocabularyDistinguishesNormalAndAbandoned.
     */
    @Test void unknownObjectReturnAndInvalidationRaiseIllegalState() {
        try (GenericObjectPool<TestResource, Exception> pool = pool(
                new RecordingFactory(), 2, true)) {
            TestResource outsider = new TestResource("outsider");
            assertThrows(IllegalStateException.class, () -> pool.returnObject(outsider));
            assertThrows(IllegalStateException.class, () -> pool.invalidateObject(outsider));
            assertEquals(0, pool.getNumActive() + pool.getNumIdle());
        }
    }

    /**
     * Verifies: CP-VALID-009, CP-ERR-007.
     * Seam: lifecycle crossing from successful return into duplicate-return rejection.
     * Depends-On: returningThenDeallocatingRestoresIdleState, makeObjectWrapsCreatedValue.
     */
    @Test void duplicateReturnRaisesIllegalStateWithoutChangingPopulation() throws Exception {
        try (GenericObjectPool<TestResource, Exception> pool = pool(
                new RecordingFactory(), 2, true)) {
            TestResource value = pool.borrowObject();
            pool.returnObject(value);
            assertThrows(IllegalStateException.class, () -> pool.returnObject(value));
            assertEquals(1, pool.getNumIdle());
            assertEquals(0, pool.getNumActive());
            assertEquals(1L, pool.getReturnedCount());
        }
    }

    private static GenericObjectPool<TestResource, Exception> pool(
            RecordingFactory factory, int maxTotal, boolean block) {
        return new GenericObjectPool<>(factory, config(maxTotal, block));
    }

    private static GenericObjectPoolConfig<TestResource> config(int maxTotal, boolean block) {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setJmxEnabled(false);
        config.setMaxTotal(maxTotal);
        config.setBlockWhenExhausted(block);
        return config;
    }
}
