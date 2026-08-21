package integration;

import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBException;
import com.oath.halodb.HaloDBIterator;
import com.oath.halodb.HaloDBOptions;
import com.oath.halodb.HaloDBStats;
import com.oath.halodb.Record;
import org.junit.Test;
import support.OracleSupport;

import java.nio.file.Path;
import java.util.Map;
import java.util.NoSuchElementException;

import static org.junit.Assert.*;

/**
     * Seam: state consistency across point lookup, iteration, size, options, and statistics. Coverage-guided cross-boundary tests for the documented HaloDB views. */
public class GeneratedIntegrationTest {

    /**
     * Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-INV-001, HALO-OPS-001, HALO-ITER-009, HALO-STAT-001. Depends-On: testDefaultMaxFileAndTombstoneSize, testSetRecordCapacityRoundTrip. */
    @Test
    public void testNewKeyAcrossPointIteratorSizeAndStats() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                assertTrue(database.put(bytes(1), bytes(11)));
                assertArrayEquals(bytes(11), database.get(bytes(1)));
                assertEquals(1, database.size());
                assertArrayEquals(bytes(11), OracleSupport.records(database).get("[1]"));
                assertEquals(database.size(), database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-INV-001, HALO-STATE-001, HALO-WF-001. Depends-On: testDefaultCompactionThreshold, testDefaultRecordCapacityEstimate. */
    @Test
    public void testTwoNewKeysAcrossAllLiveViews() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(2), bytes(20));
                database.put(bytes(3), bytes(30));
                Map<String, byte[]> records = OracleSupport.records(database);
                assertArrayEquals(bytes(20), database.get(bytes(2)));
                assertArrayEquals(bytes(30), records.get("[3]"));
                assertEquals(2, records.size());
                assertEquals(2, database.size());
                assertEquals(2, database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-INV-002, HALO-OPS-002, HALO-ITER-003. Depends-On: testSetPositiveFlushThresholdRoundTrip, testSetRecordCapacityRoundTrip. */
    @Test
    public void testUpdateAcrossPointIteratorSizeAndStats() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(4), bytes(40));
                database.put(bytes(4), bytes(41));
                Map<String, byte[]> records = OracleSupport.records(database);
                assertArrayEquals(bytes(41), database.get(bytes(4)));
                assertArrayEquals(bytes(41), records.get("[4]"));
                assertEquals(1, records.size());
                assertEquals(1, database.size());
                assertEquals(1, database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-INV-002, HALO-OPS-011, HALO-ITER-010. Depends-On: testSetCompactionThresholdRoundTrip, testSetCompactionJobRateRoundTrip. */
    @Test
    public void testRepeatedUpdatesExposeOnlyLatestValue() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                for (int value = 50; value <= 55; value++) {
                    database.put(bytes(5), bytes(value));
                }
                Map<String, byte[]> records = OracleSupport.records(database);
                assertArrayEquals(bytes(55), database.get(bytes(5)));
                assertArrayEquals(bytes(55), records.get("[5]"));
                assertEquals(1, records.size());
                assertEquals(database.size(), database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-003, HALO-OPS-007, HALO-ITER-004, HALO-STAT-003. Depends-On: testSetMaxTombstoneFileSizeRoundTrip, testSetMaxFileSizeRoundTrip. */
    @Test
    public void testDeleteAcrossPointIteratorSizeAndStats() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(6), bytes(60));
                database.delete(bytes(6));
                assertNull(database.get(bytes(6)));
                assertFalse(OracleSupport.records(database).containsKey("[6]"));
                assertEquals(0, database.size());
                HaloDBStats stats = database.stats();
                assertEquals(0, stats.getSize());
                assertTrue(stats.getNumberOfTombstoneFiles() >= 1);
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-003, HALO-OPS-012, HALO-STATE-001. Depends-On: testSetMaxTombstoneFileSizeRoundTrip, testSetRecordCapacityRoundTrip. */
    @Test
    public void testDeleteOneKeyKeepsOtherAcrossViews() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(7), bytes(70));
                database.put(bytes(8), bytes(80));
                database.delete(bytes(7));
                Map<String, byte[]> records = OracleSupport.records(database);
                assertNull(database.get(bytes(7)));
                assertArrayEquals(bytes(80), database.get(bytes(8)));
                assertFalse(records.containsKey("[7]"));
                assertArrayEquals(bytes(80), records.get("[8]"));
                assertEquals(1, database.size());
                assertEquals(1, database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-INV-004, HALO-WF-002, HALO-LIFE-003, HALO-STATE-002. Depends-On: testSetMaxFileSizeRoundTrip, testSetRecordCapacityRoundTrip. */
    @Test
    public void testReopenMixedStateAcrossViews() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB first = HaloDB.open(directory.toFile(), options);
            first.put(bytes(9), bytes(90));
            first.put(bytes(10), bytes(100));
            first.delete(bytes(9));
            first.close();

            HaloDB reopened = HaloDB.open(directory.toFile(), options);
            try {
                Map<String, byte[]> records = OracleSupport.records(reopened);
                assertNull(reopened.get(bytes(9)));
                assertArrayEquals(bytes(100), reopened.get(bytes(10)));
                assertFalse(records.containsKey("[9]"));
                assertArrayEquals(bytes(100), records.get("[10]"));
                assertEquals(1, reopened.size());
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-INV-004, HALO-LIFE-003, HALO-OPS-002, HALO-ITER-003. Depends-On: testSetPositiveFlushThresholdRoundTrip, testSetMaxFileSizeRoundTrip. */
    @Test
    public void testReopenExposesLatestValueInEveryView() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB first = HaloDB.open(directory.toFile(), options);
            first.put(bytes(11), bytes(110));
            first.put(bytes(11), bytes(111));
            first.close();

            HaloDB reopened = HaloDB.open(directory.toFile(), options);
            try {
                Map<String, byte[]> records = OracleSupport.records(reopened);
                assertArrayEquals(bytes(111), reopened.get(bytes(11)));
                assertArrayEquals(bytes(111), records.get("[11]"));
                assertEquals(1, records.size());
                assertEquals(reopened.size(), reopened.stats().getSize());
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-005, HALO-COMP-001, HALO-COMP-002, HALO-STAT-005. Depends-On: testSetCompactionThresholdRoundTrip, testSetCompactionJobRateRoundTrip. */
    @Test
    public void testHeavyUpdatesPreserveMappingAndCompactionViews() throws Exception {
        withDirectory((directory, options) -> {
            tuneForCompaction(options);
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                byte[] payload = new byte[256];
                for (int key = 0; key < 40; key++) {
                    payload[0] = (byte) key;
                    database.put(bytes(key), payload.clone());
                }
                for (int key = 0; key < 40; key++) {
                    payload[0] = (byte) (key + 1);
                    database.put(bytes(key), payload.clone());
                }
                database.pauseCompaction();
                Map<String, byte[]> records = OracleSupport.records(database);
                assertEquals(40, records.size());
                assertEquals(40, database.size());
                assertEquals(40, database.stats().getSize());
                for (int key = 0; key < 40; key++) {
                    assertEquals((byte) (key + 1), database.get(bytes(key))[0]);
                }
                HaloDBStats stats = database.stats();
                assertTrue(stats.getNumberOfDataFiles() > 0);
                assertTrue(stats.getNumberOfRecordsCopied() >= 0);
                assertTrue(stats.getSizeReclaimed() >= 0);
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-005, HALO-COMP-002, HALO-LIFE-003, HALO-STATE-004. Depends-On: testSetCompactionThresholdRoundTrip, testSetMaxFileSizeRoundTrip. */
    @Test
    public void testHeavyDeletesPreserveRemainingMappingAfterReopen() throws Exception {
        withDirectory((directory, options) -> {
            tuneForCompaction(options);
            HaloDB first = HaloDB.open(directory.toFile(), options);
            byte[] value = new byte[256];
            for (int key = 0; key < 50; key++) {
                value[0] = (byte) key;
                first.put(bytes(key), value.clone());
            }
            for (int key = 0; key < 30; key++) {
                first.delete(bytes(key));
            }
            first.pauseCompaction();
            assertEquals(20, first.size());
            first.close();

            HaloDB reopened = HaloDB.open(directory.toFile(), options);
            try {
                Map<String, byte[]> records = OracleSupport.records(reopened);
                assertEquals(20, records.size());
                assertNull(reopened.get(bytes(0)));
                assertEquals((byte) 49, reopened.get(bytes(49))[0]);
                assertEquals(reopened.size(), reopened.stats().getSize());
                assertTrue(reopened.stats().getNumberOfDataFiles() > 0);
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-006, HALO-COMP-009, HALO-STAT-009, HALO-STAT-010. Depends-On: testToggleCleanupTombstonesDuringOpen, testSetRecordCapacityRoundTrip. */
    @Test
    public void testCleanupEnabledPreservesRetainedKeyAndDeletion() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB first = HaloDB.open(directory.toFile(), options);
            first.put(bytes(13), bytes(130));
            first.put(bytes(14), bytes(140));
            first.delete(bytes(13));
            first.close();

            HaloDBOptions cleanup = compatibleOptions(options);
            cleanup.setCleanUpTombstonesDuringOpen(true);
            HaloDB reopened = HaloDB.open(directory.toFile(), cleanup);
            try {
                Map<String, byte[]> records = OracleSupport.records(reopened);
                HaloDBStats stats = reopened.stats();
                assertNull(reopened.get(bytes(13)));
                assertArrayEquals(bytes(140), reopened.get(bytes(14)));
                assertFalse(records.containsKey("[13]"));
                assertArrayEquals(bytes(140), records.get("[14]"));
                assertTrue(stats.getNumberOfTombstonesFoundDuringOpen() >= 0);
                assertTrue(stats.getNumberOfTombstonesCleanedUpDuringOpen() >= 0);
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-006, HALO-COMP-009, HALO-STAT-009, HALO-STAT-010. Depends-On: testToggleCleanupTombstonesDuringOpen, testSetRecordCapacityRoundTrip. */
    @Test
    public void testCleanupEnabledPreservesOneLiveKeyAmongMultipleDeletions() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB first = HaloDB.open(directory.toFile(), options);
            first.put(bytes(30), bytes(130));
            first.put(bytes(31), bytes(131));
            first.put(bytes(32), bytes(132));
            first.delete(bytes(30));
            first.delete(bytes(31));
            first.close();

            HaloDBOptions cleanup = compatibleOptions(options);
            cleanup.setCleanUpTombstonesDuringOpen(true);
            HaloDB reopened = HaloDB.open(directory.toFile(), cleanup);
            try {
                Map<String, byte[]> records = OracleSupport.records(reopened);
                HaloDBStats stats = reopened.stats();
                assertNull(reopened.get(bytes(30)));
                assertNull(reopened.get(bytes(31)));
                assertArrayEquals(bytes(132), reopened.get(bytes(32)));
                assertEquals(1, records.size());
                assertArrayEquals(bytes(132), records.get("[32]"));
                assertEquals(1, stats.getSize());
                assertTrue(stats.getNumberOfTombstonesFoundDuringOpen()
                    >= stats.getNumberOfTombstonesCleanedUpDuringOpen());
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-007, HALO-COMP-003, HALO-COMP-004, HALO-STAT-015. Depends-On: testSetCompactionThresholdRoundTrip, testSetCompactionJobRateRoundTrip. */
    @Test
    public void testPauseCompactionKeepsLiveViewsConsistent() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(15), bytes(150));
                database.pauseCompaction();
                database.pauseCompaction();
                assertFalse(database.stats().isCompactionRunning());
                assertArrayEquals(bytes(150), database.get(bytes(15)));
                assertArrayEquals(bytes(150), OracleSupport.records(database).get("[15]"));
                assertEquals(1, database.size());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-INV-007, HALO-COMP-006, HALO-COMP-010, HALO-STATE-004. Depends-On: testSetCompactionThresholdRoundTrip, testDefaultCompactionJobRate. */
    @Test
    public void testResumeCompactionKeepsLiveViewsConsistent() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(16), bytes(160));
                database.pauseCompaction();
                database.resumeCompaction();
                database.resumeCompaction();
                assertArrayEquals(bytes(160), database.get(bytes(16)));
                assertArrayEquals(bytes(160), OracleSupport.records(database).get("[16]"));
                assertEquals(database.size(), database.stats().getSize());
                assertTrue(database.stats().getNumberOfFilesPendingCompaction() >= 0);
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-INV-008, HALO-STAT-001, HALO-STAT-005, HALO-STAT-012. Depends-On: testSetMaxFileSizeRoundTrip, testSetRecordCapacityRoundTrip. */
    @Test
    public void testResetStatsPreservesLogicalAndPhysicalViews() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(17), bytes(170));
                HaloDBStats before = database.stats();
                database.resetStats();
                HaloDBStats after = database.stats();
                assertArrayEquals(bytes(170), database.get(bytes(17)));
                assertArrayEquals(bytes(170), OracleSupport.records(database).get("[17]"));
                assertEquals(database.size(), after.getSize());
                assertEquals(before.getNumberOfDataFiles(), after.getNumberOfDataFiles());
                assertEquals(before.getNumberOfTombstoneFiles(), after.getNumberOfTombstoneFiles());
                assertEquals(0, after.getRehashCount());
                assertEquals(0, after.getNumberOfRecordsCopied());
                assertEquals(0, after.getSizeReclaimed());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-INV-008, HALO-STAT-002, HALO-STAT-012, HALO-STAT-017. Depends-On: testSetCompactionJobRateRoundTrip, testIndependentConfigurationSettersCompose. */
    @Test
    public void testRepeatedResetKeepsOptionsAndCurrentViews() throws Exception {
        withDirectory((directory, options) -> {
            options.setCompactionJobRate(1234567);
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(18), bytes(180));
                database.resetStats();
                database.resetStats();
                HaloDBStats stats = database.stats();
                assertArrayEquals(bytes(180), database.get(bytes(18)));
                assertEquals(1, OracleSupport.records(database).size());
                assertEquals(database.size(), stats.getSize());
                assertEquals(1234567, stats.getOptions().getCompactionJobRate());
                assertTrue(stats.getCompactionRateSinceBeginning() >= 0);
            } finally {
                database.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-INV-009, HALO-OPT-009, HALO-LIFE-003. Depends-On: testToggleSynchronousWrites, testDefaultFlushThreshold. */
    @Test
    public void testSynchronousWriteSurvivesReopenAcrossViews() throws Exception {
        withDirectory((directory, options) -> {
            options.enableSyncWrites(true);
            options.setFlushDataSizeBytes(-1);
            HaloDB first = HaloDB.open(directory.toFile(), options);
            first.put(bytes(19), bytes(190));
            assertArrayEquals(bytes(190), first.get(bytes(19)));
            first.close();

            HaloDB reopened = HaloDB.open(directory.toFile(), options);
            try {
                assertArrayEquals(bytes(190), reopened.get(bytes(19)));
                assertArrayEquals(bytes(190), OracleSupport.records(reopened).get("[19]"));
                assertEquals(1, reopened.size());
                assertTrue(reopened.stats().getOptions().isSyncWrite());
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-WF-001, HALO-STATE-001, HALO-STAT-001, HALO-ITER-010. Depends-On: testSetMaxFileSizeRoundTrip, testSetPositiveFlushThresholdRoundTrip. */
    @Test
    public void testConfigureWriteReadIterateAndInspectWorkflow() throws Exception {
        withDirectory((directory, options) -> {
            options.setMaxFileSize(64 * 1024);
            options.setCompactionThresholdPerFile(0.70);
            options.setFlushDataSizeBytes(8 * 1024);
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                byte[] key = bytes(1, 2, 3);
                byte[] value = bytes(9, 8, 7);
                database.put(key, value);
                Map<String, byte[]> records = OracleSupport.records(database);
                assertArrayEquals(value, database.get(key));
                assertArrayEquals(value, records.get("[1, 2, 3]"));
                assertEquals(1, database.size());
                assertEquals(database.size(), database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-WF-002, HALO-LIFE-003, HALO-STATE-002, HALO-ITER-004. Depends-On: testToggleCleanupTombstonesDuringOpen, testSetMaxFileSizeRoundTrip. */
    @Test
    public void testDeleteCloseAndReopenWorkflow() throws Exception {
        withDirectory((directory, options) -> {
            options.setCleanUpTombstonesDuringOpen(true);
            HaloDB first = HaloDB.open(directory.toFile(), options);
            first.put(bytes(21), bytes(210));
            first.put(bytes(22), bytes(220));
            first.delete(bytes(21));
            first.close();

            HaloDB reopened = HaloDB.open(directory.toFile(), options);
            try {
                Map<String, byte[]> records = OracleSupport.records(reopened);
                assertNull(reopened.get(bytes(21)));
                assertArrayEquals(bytes(220), reopened.get(bytes(22)));
                assertFalse(records.containsKey("[21]"));
                assertArrayEquals(bytes(220), records.get("[22]"));
                assertEquals(1, reopened.size());
            } finally {
                reopened.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-LIFE-001, HALO-LIFE-002, HALO-WF-001. Depends-On: testDefaultMaxFileAndTombstoneSize, testSetRecordCapacityRoundTrip. */
    @Test
    public void testStringPathOpenWriteAndInspect() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toString(), options);
            try {
                database.put(bytes(23), bytes(230));
                assertArrayEquals(bytes(230), database.get(bytes(23)));
                assertArrayEquals(bytes(230), OracleSupport.records(database).get("[23]"));
                assertEquals(database.size(), database.stats().getSize());
            } finally {
                database.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-LIFE-005, HALO-LIFE-006, HALO-ERR-002. Depends-On: testSetMaxFileSizeRoundTrip, testSetRecordCapacityRoundTrip. */
    @Test
    public void testLockReleaseAllowsLaterWorkflow() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB owner = HaloDB.open(directory.toFile(), options);
            owner.put(bytes(24), bytes(240));
            try {
                try {
                    HaloDB.open(directory.toFile(), options);
                    fail("second owner must be rejected");
                } catch (HaloDBException expected) {
                    assertArrayEquals(bytes(240), owner.get(bytes(24)));
                }
            } finally {
                owner.close();
            }

            HaloDB later = HaloDB.open(directory.toFile(), options);
            try {
                assertArrayEquals(bytes(240), later.get(bytes(24)));
                assertArrayEquals(bytes(240), OracleSupport.records(later).get("[24]"));
                assertEquals(1, later.stats().getSize());
            } finally {
                later.close();
            }
        });
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-ITER-001, HALO-ITER-006, HALO-ITER-007, HALO-ITER-008, HALO-ERR-010. Depends-On: testSetRecordCapacityRoundTrip, testDefaultCompactionThreshold. */
    @Test
    public void testIteratorProtocolWithMultipleRecordsAndExhaustion() throws Exception {
        withDirectory((directory, options) -> {
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                database.put(bytes(25), bytes(250));
                database.put(bytes(26), bytes(251));
                HaloDBIterator iterator = database.newIterator();
                int count = 0;
                while (iterator.hasNext()) {
                    assertTrue(iterator.hasNext());
                    Record record = iterator.next();
                    assertNotNull(record.getKey());
                    assertNotNull(record.getValue());
                    count++;
                }
                assertEquals(2, count);
                assertFalse(iterator.hasNext());
                try {
                    iterator.next();
                    fail("exhausted iterator must fail");
                } catch (NoSuchElementException expected) {
                    assertEquals(2, database.size());
                }
            } finally {
                database.close();
            }
        });
    }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-OPT-020, HALO-OPT-022, HALO-STAT-001, HALO-STATE-003. Depends-On: testToggleMemoryPoolMode, testSetFixedKeySizeRoundTrip. */
    @Test
    public void testPooledIndexWriteAndStatsWorkflow() throws Exception {
        withDirectory((directory, options) -> {
            options.setUseMemoryPool(true);
            options.setFixedKeySize(8);
            options.setNumberOfRecords(128);
            HaloDB database = HaloDB.open(directory.toFile(), options);
            try {
                byte[] key = bytes(1, 2, 3, 4);
                database.put(key, bytes(42));
                assertArrayEquals(bytes(42), database.get(key));
                assertArrayEquals(bytes(42), OracleSupport.records(database).get("[1, 2, 3, 4]"));
                assertEquals(1, database.size());
                assertTrue(database.stats().getOptions().isUseMemoryPool());
                assertEquals(8, database.stats().getOptions().getFixedKeySize());
            } finally {
                database.close();
            }
        });
    }

    private interface Scenario {
        void run(Path directory, HaloDBOptions options) throws Exception;
    }

    private static void withDirectory(Scenario scenario) throws Exception {
        Path directory = OracleSupport.directory();
        try {
            scenario.run(directory, OracleSupport.options());
        } finally {
            OracleSupport.remove(directory);
        }
    }

    private static byte[] bytes(int... values) {
        return OracleSupport.bytes(values);
    }

    private static void tuneForCompaction(HaloDBOptions options) {
        options.setMaxFileSize(4096);
        options.setMaxTombstoneFileSize(2048);
        options.setCompactionThresholdPerFile(0.10);
        options.setCompactionJobRate(1024 * 1024 * 1024);
    }

    private static HaloDBOptions compatibleOptions(HaloDBOptions source) {
        HaloDBOptions result = OracleSupport.options();
        result.setMaxFileSize(source.getMaxFileSize());
        result.setMaxTombstoneFileSize(source.getMaxTombstoneFileSize());
        result.setNumberOfRecords(source.getNumberOfRecords());
        return result;
    }
}
