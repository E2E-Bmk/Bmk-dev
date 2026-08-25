package atomic;

import com.oath.halodb.HaloDBOptions;
import org.junit.Test;

import static org.junit.Assert.*;

/** Coverage-guided checks for the public HaloDBOptions contract. */
public class GeneratedAtomicTest {

    /** Verifies: HALO-OPT-001. */
    @Test
    public void testDefaultCompactionThreshold() {
        assertEquals(0.75, new HaloDBOptions().getCompactionThresholdPerFile(), 0.0);
    }

    /** Verifies: HALO-OPT-001, HALO-OPT-002. */
    @Test
    public void testDefaultMaxFileAndTombstoneSize() {
        HaloDBOptions options = new HaloDBOptions();
        assertEquals(1024 * 1024, options.getMaxFileSize());
        assertEquals(options.getMaxFileSize(), options.getMaxTombstoneFileSize());
    }

    /** Verifies: HALO-OPT-001, HALO-OPT-027. */
    @Test
    public void testDefaultFlushThreshold() {
        assertEquals(-1L, new HaloDBOptions().getFlushDataSizeBytes());
    }

    /** Verifies: HALO-OPT-001. */
    @Test
    public void testDefaultRecordCapacityEstimate() {
        assertEquals(1_000_000, new HaloDBOptions().getNumberOfRecords());
    }

    /** Verifies: HALO-OPT-001. */
    @Test
    public void testDefaultCompactionJobRate() {
        assertEquals(1024 * 1024 * 1024, new HaloDBOptions().getCompactionJobRate());
    }

    /** Verifies: HALO-OPT-001. */
    @Test
    public void testDefaultMemoryPoolSizes() {
        HaloDBOptions options = new HaloDBOptions();
        assertEquals(127, options.getFixedKeySize());
        assertEquals(16 * 1024 * 1024, options.getMemoryPoolChunkSize());
    }

    /** Verifies: HALO-OPT-001. */
    @Test
    public void testDefaultSyncAndBuildSettings() {
        HaloDBOptions options = new HaloDBOptions();
        assertFalse(options.isSyncWrite());
        assertEquals(1, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-013. */
    @Test
    public void testSetCompactionThresholdRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setCompactionThresholdPerFile(0.42);
        assertEquals(0.42, options.getCompactionThresholdPerFile(), 0.0);
    }

    /** Verifies: HALO-OPT-003, HALO-OPT-002. */
    @Test
    public void testSetMaxFileSizeRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMaxFileSize(8192);
        assertEquals(8192, options.getMaxFileSize());
        assertEquals(8192, options.getMaxTombstoneFileSize());
    }

    /** Verifies: HALO-OPT-005. */
    @Test
    public void testSetMaxTombstoneFileSizeRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMaxTombstoneFileSize(4096);
        assertEquals(4096, options.getMaxTombstoneFileSize());
    }

    /** Verifies: HALO-OPT-007. */
    @Test
    public void testSetPositiveFlushThresholdRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setFlushDataSizeBytes(2048L);
        assertEquals(2048L, options.getFlushDataSizeBytes());
    }

    /** Verifies: HALO-OPT-010. */
    @Test
    public void testSetRecordCapacityRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setNumberOfRecords(3210);
        assertEquals(3210, options.getNumberOfRecords());
    }

    /** Verifies: HALO-OPT-014. */
    @Test
    public void testSetCompactionJobRateRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setCompactionJobRate(987654);
        assertEquals(987654, options.getCompactionJobRate());
    }

    /** Verifies: HALO-OPT-019. */
    @Test
    public void testToggleCleanupInMemoryIndex() {
        HaloDBOptions options = new HaloDBOptions();
        options.setCleanUpInMemoryIndexOnClose(true);
        assertTrue(options.isCleanUpInMemoryIndexOnClose());
        options.setCleanUpInMemoryIndexOnClose(false);
        assertFalse(options.isCleanUpInMemoryIndexOnClose());
    }

    /** Verifies: HALO-OPT-018. */
    @Test
    public void testToggleCleanupTombstonesDuringOpen() {
        HaloDBOptions options = new HaloDBOptions();
        options.setCleanUpTombstonesDuringOpen(true);
        assertTrue(options.isCleanUpTombstonesDuringOpen());
        options.setCleanUpTombstonesDuringOpen(false);
        assertFalse(options.isCleanUpTombstonesDuringOpen());
    }

    /** Verifies: HALO-OPT-020. */
    @Test
    public void testToggleMemoryPoolMode() {
        HaloDBOptions options = new HaloDBOptions();
        options.setUseMemoryPool(true);
        assertTrue(options.isUseMemoryPool());
        options.setUseMemoryPool(false);
        assertFalse(options.isUseMemoryPool());
    }

    /** Verifies: HALO-OPT-021. */
    @Test
    public void testSetFixedKeySizeRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setFixedKeySize(31);
        assertEquals(31, options.getFixedKeySize());
    }

    /** Verifies: HALO-OPT-021. */
    @Test
    public void testSetMemoryPoolChunkSizeRoundTrip() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMemoryPoolChunkSize(2 * 1024 * 1024);
        assertEquals(2 * 1024 * 1024, options.getMemoryPoolChunkSize());
    }

    /** Verifies: HALO-OPT-009, HALO-OPT-028. */
    @Test
    public void testToggleSynchronousWrites() {
        HaloDBOptions options = new HaloDBOptions();
        options.enableSyncWrites(true);
        assertTrue(options.isSyncWrite());
        options.enableSyncWrites(false);
        assertFalse(options.isSyncWrite());
    }

    /** Verifies: HALO-OPT-016. */
    @Test
    public void testSetBuildThreadsToOne() {
        HaloDBOptions options = new HaloDBOptions();
        options.setBuildIndexThreads(1);
        assertEquals(1, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-016. */
    @Test
    public void testSetBuildThreadsToProcessorCount() {
        HaloDBOptions options = new HaloDBOptions();
        int processors = Runtime.getRuntime().availableProcessors();
        options.setBuildIndexThreads(processors);
        assertEquals(processors, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-003. */
    @Test
    public void testMinimumPositiveMaxFileSize() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMaxFileSize(1);
        assertEquals(1, options.getMaxFileSize());
    }

    /** Verifies: HALO-OPT-005. */
    @Test
    public void testMinimumPositiveTombstoneFileSize() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMaxTombstoneFileSize(1);
        assertEquals(1, options.getMaxTombstoneFileSize());
    }

    /** Verifies: HALO-OPT-002, HALO-OPT-003, HALO-OPT-005. */
    @Test
    public void testExplicitTombstoneSizeRemainsIndependent() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMaxTombstoneFileSize(2048);
        options.setMaxFileSize(8192);
        assertEquals(2048, options.getMaxTombstoneFileSize());
        assertEquals(8192, options.getMaxFileSize());
    }

    /** Verifies: HALO-OPT-007, HALO-OPT-027. */
    @Test
    public void testRestoreDisabledFlushThreshold() {
        HaloDBOptions options = new HaloDBOptions();
        options.setFlushDataSizeBytes(512L);
        options.setFlushDataSizeBytes(-1L);
        assertEquals(-1L, options.getFlushDataSizeBytes());
    }

    /** Verifies: HALO-OPT-013, HALO-OPT-014, HALO-OPT-016. */
    @Test
    public void testIndependentConfigurationSettersCompose() {
        HaloDBOptions options = new HaloDBOptions();
        options.setCompactionThresholdPerFile(0.2);
        options.setCompactionJobRate(123456);
        options.setBuildIndexThreads(1);
        assertEquals(0.2, options.getCompactionThresholdPerFile(), 0.0);
        assertEquals(123456, options.getCompactionJobRate());
        assertEquals(1, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-004, HALO-ERR-006. */
    @Test
    public void testRejectZeroMaxFileSizeWithoutMutation() {
        HaloDBOptions options = new HaloDBOptions();
        int original = options.getMaxFileSize();
        assertIllegalArgument(() -> options.setMaxFileSize(0));
        assertEquals(original, options.getMaxFileSize());
    }

    /** Verifies: HALO-OPT-004, HALO-ERR-006. */
    @Test
    public void testRejectNegativeMaxFileSizeWithoutMutation() {
        HaloDBOptions options = new HaloDBOptions();
        int original = options.getMaxFileSize();
        assertIllegalArgument(() -> options.setMaxFileSize(-7));
        assertEquals(original, options.getMaxFileSize());
    }

    /** Verifies: HALO-OPT-006, HALO-ERR-006. */
    @Test
    public void testRejectZeroTombstoneFileSizeWithoutMutation() {
        HaloDBOptions options = new HaloDBOptions();
        int original = options.getMaxTombstoneFileSize();
        assertIllegalArgument(() -> options.setMaxTombstoneFileSize(0));
        assertEquals(original, options.getMaxTombstoneFileSize());
    }

    /** Verifies: HALO-OPT-006, HALO-ERR-006. */
    @Test
    public void testRejectNegativeTombstoneFileSizeWithoutMutation() {
        HaloDBOptions options = new HaloDBOptions();
        int original = options.getMaxTombstoneFileSize();
        assertIllegalArgument(() -> options.setMaxTombstoneFileSize(-9));
        assertEquals(original, options.getMaxTombstoneFileSize());
    }

    /** Verifies: HALO-OPT-017, HALO-ERR-007. */
    @Test
    public void testRejectZeroBuildThreadsWithoutMutation() {
        HaloDBOptions options = new HaloDBOptions();
        int original = options.getBuildIndexThreads();
        assertIllegalArgument(() -> options.setBuildIndexThreads(0));
        assertEquals(original, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-017, HALO-ERR-007. */
    @Test
    public void testRejectExcessBuildThreadsWithoutMutation() {
        HaloDBOptions options = new HaloDBOptions();
        int original = options.getBuildIndexThreads();
        assertIllegalArgument(() -> options.setBuildIndexThreads(Runtime.getRuntime().availableProcessors() + 1));
        assertEquals(original, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-002, HALO-OPT-003, HALO-OPT-005. */
    @Test
    public void testFileSizeFallbackAndOverrideSequence() {
        HaloDBOptions options = new HaloDBOptions();
        options.setMaxFileSize(16384);
        assertEquals(16384, options.getMaxTombstoneFileSize());
        options.setMaxTombstoneFileSize(3072);
        options.setMaxFileSize(32768);
        assertEquals(3072, options.getMaxTombstoneFileSize());
        assertEquals(32768, options.getMaxFileSize());
    }

    private interface ThrowingAction {
        void run();
    }

    private static void assertIllegalArgument(ThrowingAction action) {
        try {
            action.run();
            fail("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            assertNotNull(expected);
        }
    }
}
