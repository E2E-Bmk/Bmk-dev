package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import org.apache.commons.pool3.impl.AbandonedConfig;
import org.junit.jupiter.api.Test;

/** Atomic tests for abandoned-lease recovery configuration. */
class AbandonedAtomicTest {

    /** Verifies: CP-ABAND-001. */
    @Test void defaultRemovalTriggersAreDisabled() {
        AbandonedConfig config = new AbandonedConfig();
        assertFalse(config.getRemoveAbandonedOnBorrow());
        assertFalse(config.getRemoveAbandonedOnMaintenance());
    }

    /** Verifies: CP-ABAND-001. */
    @Test void defaultLoggingAndUsageTrackingAreDisabled() {
        AbandonedConfig config = new AbandonedConfig();
        assertFalse(config.getLogAbandoned());
        assertFalse(config.getUseUsageTracking());
        assertTrue(config.getRequireFullStackTrace());
    }

    /** Verifies: CP-ABAND-001. */
    @Test void defaultTimeoutIsFiveMinutes() {
        AbandonedConfig config = new AbandonedConfig();
        assertEquals(Duration.ofMinutes(5), config.getRemoveAbandonedTimeoutDuration());
    }

    /** Verifies: CP-ABAND-002. */
    @Test void copyOfNullRemainsNull() {
        assertNull(AbandonedConfig.copy(null));
    }

    /** Verifies: CP-ABAND-002. */
    @Test void copyIsDistinctAndPreservesAllPolicyValues() {
        AbandonedConfig source = new AbandonedConfig();
        source.setRemoveAbandonedOnBorrow(true);
        source.setRemoveAbandonedOnMaintenance(true);
        source.setRemoveAbandonedTimeout(Duration.ofSeconds(41));
        source.setUseUsageTracking(true);
        AbandonedConfig copy = AbandonedConfig.copy(source);
        assertNotSame(source, copy);
        assertTrue(copy.getRemoveAbandonedOnBorrow());
        assertTrue(copy.getRemoveAbandonedOnMaintenance());
        assertEquals(Duration.ofSeconds(41), copy.getRemoveAbandonedTimeoutDuration());
        assertTrue(copy.getUseUsageTracking());
    }

    /** Verifies: CP-ABAND-003, CP-ABAND-004. */
    @Test void removalTriggerSettersRoundTripIndependently() {
        AbandonedConfig config = new AbandonedConfig();
        config.setRemoveAbandonedOnBorrow(true);
        assertTrue(config.getRemoveAbandonedOnBorrow());
        assertFalse(config.getRemoveAbandonedOnMaintenance());
        config.setRemoveAbandonedOnMaintenance(true);
        assertTrue(config.getRemoveAbandonedOnMaintenance());
    }

    /** Verifies: CP-ABAND-007. */
    @Test void usageAndTraceOptionsRoundTripExactValues() {
        AbandonedConfig config = new AbandonedConfig();
        config.setUseUsageTracking(true);
        config.setRequireFullStackTrace(false);
        assertTrue(config.getUseUsageTracking());
        assertFalse(config.getRequireFullStackTrace());
    }
}

