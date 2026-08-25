package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.util.List;
import org.apache.commons.pool3.impl.DefaultEvictionPolicy;
import org.apache.commons.pool3.impl.GenericObjectPool;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;
import support.TestResource;

/** Atomic tests for borrowing, return, capacity, and ordering configuration. */
class PoolConfigurationAtomicTest {

    /** Verifies: CP-POOL-003. */
    @Test void defaultCapacityValuesMatchContract() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        assertEquals(8, config.getMaxTotal());
        assertEquals(8, config.getMaxIdle());
        assertEquals(0, config.getMinIdle());
        assertTrue(config.getLifo());
    }

    /** Verifies: CP-POOL-003. */
    @Test void defaultExhaustionAndFairnessValuesMatchContract() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        assertTrue(config.getBlockWhenExhausted());
        assertFalse(config.getFairness());
        assertTrue(config.getJmxEnabled());
    }

    /** Verifies: CP-POOL-003. */
    @Test void defaultEvictionValuesMatchContract() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        assertEquals(3, config.getNumTestsPerEvictionRun());
        assertTrue(config.getDurationBetweenEvictionRuns().isNegative());
    }

    /** Verifies: CP-POOL-003. */
    @Test void defaultValidationAndPolicyValuesMatchContract() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        assertFalse(config.getTestOnCreate());
        assertFalse(config.getTestOnBorrow());
        assertFalse(config.getTestOnReturn());
        assertFalse(config.getTestWhileIdle());
        assertEquals(DefaultEvictionPolicy.class.getName(), config.getEvictionPolicyClassName());
    }

    /** Verifies: CP-POOL-005. */
    @Test void cloneIsDistinctAndPreservesProperties() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setMaxTotal(13);
        config.setLifo(false);
        GenericObjectPoolConfig<TestResource> copy = config.clone();
        assertNotSame(config, copy);
        assertEquals(13, copy.getMaxTotal());
        assertFalse(copy.getLifo());
    }

    /** Verifies: CP-POOL-014. */
    @Test void negativeCapacityValuesArePreservedAsUnlimited() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setMaxTotal(-7);
        config.setMaxIdle(-3);
        assertEquals(-7, config.getMaxTotal());
        assertEquals(-3, config.getMaxIdle());
    }

    /** Verifies: CP-POOL-004. */
    @Test void settersRoundTripOrderingWaitAndCapacity() {
        GenericObjectPoolConfig<TestResource> config = new GenericObjectPoolConfig<>();
        config.setLifo(false);
        config.setBlockWhenExhausted(false);
        config.setMaxTotal(7);
        config.setMaxIdle(5);
        config.setMinIdle(2);
        assertAll(
                () -> assertFalse(config.getLifo()),
                () -> assertFalse(config.getBlockWhenExhausted()),
                () -> assertEquals(List.of(7, 5, 2), List.of(config.getMaxTotal(), config.getMaxIdle(), config.getMinIdle())));
    }

    /** Verifies: CP-POOL-002, CP-ERR-001. */
    @Test void nullFactoryConstructorRaisesIllegalArgument() {
        assertThrows(IllegalArgumentException.class,
                () -> new GenericObjectPool<TestResource, Exception>(null));
    }
}

