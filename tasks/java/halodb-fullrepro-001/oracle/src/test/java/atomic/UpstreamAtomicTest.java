package atomic;

import com.oath.halodb.HaloDBOptions;
import org.junit.Test;

import static org.junit.Assert.*;

public class UpstreamAtomicTest {
    /** Verifies: HALO-OPT-001, HALO-OPT-002. */
    @Test
    public void testDefaultOptions() {
        HaloDBOptions options = new HaloDBOptions();
        assertEquals(0.75, options.getCompactionThresholdPerFile(), 0.0);
        assertEquals(1024 * 1024, options.getMaxFileSize());
        assertEquals(options.getMaxFileSize(), options.getMaxTombstoneFileSize());
        assertEquals(-1L, options.getFlushDataSizeBytes());
        assertEquals(1_000_000, options.getNumberOfRecords());
        assertEquals(1024 * 1024 * 1024, options.getCompactionJobRate());
        assertFalse(options.isCleanUpInMemoryIndexOnClose());
        assertFalse(options.isCleanUpTombstonesDuringOpen());
        assertFalse(options.isUseMemoryPool());
        assertEquals(127, options.getFixedKeySize());
        assertEquals(16 * 1024 * 1024, options.getMemoryPoolChunkSize());
        assertFalse(options.isSyncWrite());
        assertEquals(1, options.getBuildIndexThreads());
    }

    /** Verifies: HALO-OPT-016, HALO-OPT-017, HALO-ERR-007. */
    @Test
    public void testSetBuildIndexThreads() {
        HaloDBOptions options = new HaloDBOptions();
        int processors = Runtime.getRuntime().availableProcessors();
        options.setBuildIndexThreads(processors);
        assertEquals(processors, options.getBuildIndexThreads());
        try {
            options.setBuildIndexThreads(0);
            fail("zero workers must be rejected");
        } catch (IllegalArgumentException expected) {
            assertEquals(processors, options.getBuildIndexThreads());
        }
        try {
            options.setBuildIndexThreads(processors + 1);
            fail("too many workers must be rejected");
        } catch (IllegalArgumentException expected) {
            assertEquals(processors, options.getBuildIndexThreads());
        }
    }
}
