package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import org.apache.commons.pool3.impl.DefaultEvictionPolicy;
import org.apache.commons.pool3.impl.DefaultPooledObject;
import org.apache.commons.pool3.impl.EvictionConfig;
import org.apache.commons.pool3.impl.GenericObjectPoolConfig;
import org.junit.jupiter.api.Test;

/** Atomic tests for idle maintenance and eviction policy behavior. */
class EvictionAtomicTest {

    /** Verifies: CP-EVICT-010. */
    @Test void evictionConfigPreservesPositiveThresholdsAndMinimum() {
        EvictionConfig config = new EvictionConfig(Duration.ofSeconds(17), Duration.ofSeconds(9), 4);
        assertEquals(Duration.ofSeconds(17), config.getIdleEvictDuration());
        assertEquals(Duration.ofSeconds(9), config.getIdleSoftEvictDuration());
        assertEquals(4, config.getMinIdle());
    }

    /** Verifies: CP-EVICT-010. */
    @Test void nonPositiveThresholdsBehaveAsUnlimited() throws Exception {
        DefaultPooledObject<String> wrapped = agedIdle("unlimited");
        EvictionConfig config = new EvictionConfig(Duration.ZERO, Duration.ofSeconds(-1), 0);
        assertFalse(new DefaultEvictionPolicy<String>().evict(config, wrapped, 12));
    }

    /** Verifies: CP-EVICT-005. */
    @Test void hardThresholdEvictsOldIdleWrapper() throws Exception {
        DefaultPooledObject<String> wrapped = agedIdle("hard");
        EvictionConfig config = new EvictionConfig(Duration.ofMillis(1), Duration.ofDays(1), 0);
        assertTrue(new DefaultEvictionPolicy<String>().evict(config, wrapped, 1));
    }

    /** Verifies: CP-EVICT-005. */
    @Test void hardThresholdRetainsYoungIdleWrapper() {
        DefaultPooledObject<String> wrapped = new DefaultPooledObject<>("young");
        EvictionConfig config = new EvictionConfig(Duration.ofDays(1), Duration.ofDays(1), 0);
        assertFalse(new DefaultEvictionPolicy<String>().evict(config, wrapped, 1));
    }

    /** Verifies: CP-EVICT-005. */
    @Test void softThresholdEvictsOnlyAboveMinimumIdle() throws Exception {
        DefaultPooledObject<String> wrapped = agedIdle("soft-above");
        EvictionConfig config = new EvictionConfig(Duration.ofDays(1), Duration.ofMillis(1), 2);
        assertTrue(new DefaultEvictionPolicy<String>().evict(config, wrapped, 3));
    }

    /** Verifies: CP-EVICT-005. */
    @Test void softThresholdRetainsAtMinimumIdle() throws Exception {
        DefaultPooledObject<String> wrapped = agedIdle("soft-minimum");
        EvictionConfig config = new EvictionConfig(Duration.ofDays(1), Duration.ofMillis(1), 2);
        assertFalse(new DefaultEvictionPolicy<String>().evict(config, wrapped, 2));
    }

    /** Verifies: CP-EVICT-011. */
    @Test void ordinaryCallerIsNotEvictionThread() {
        EvictionConfig config = new EvictionConfig(Duration.ofSeconds(2), Duration.ofSeconds(1), 0);
        assertFalse(config.isEvictionThread());
    }

    /** Verifies: CP-EVICT-001, CP-EVICT-002. */
    @Test void maintenanceSettingsRoundTripExactValues() {
        GenericObjectPoolConfig<String> config = new GenericObjectPoolConfig<>();
        config.setDurationBetweenEvictionRuns(Duration.ofMillis(47));
        config.setNumTestsPerEvictionRun(-4);
        assertEquals(Duration.ofMillis(47), config.getDurationBetweenEvictionRuns());
        assertEquals(-4, config.getNumTestsPerEvictionRun());
    }

    private static DefaultPooledObject<String> agedIdle(final String value) throws Exception {
        DefaultPooledObject<String> wrapped = new DefaultPooledObject<>(value);
        Thread.sleep(8L);
        return wrapped;
    }
}


