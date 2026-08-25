package integration;

import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBException;
import com.oath.halodb.HaloDBOptions;
import org.junit.Test;
import support.OracleSupport;

import java.nio.file.Path;

import static org.junit.Assert.*;

public class HaloDBTestRewritten {
    private interface Scenario { void run(Path directory, HaloDBOptions options) throws Exception; }

    private void withDatabase(Scenario scenario) throws Exception {
        Path directory = OracleSupport.directory();
        try { scenario.run(directory, OracleSupport.options()); }
        finally { OracleSupport.remove(directory); }
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-OPS-001, HALO-OPS-004, HALO-INV-001. Depends-On: testDefaultOptions. */
    @Test public void testPutAndGetDB() throws Exception { withDatabase((dir, options) -> {
        HaloDB db = HaloDB.open(dir.toFile(), options);
        try { assertTrue(db.put(OracleSupport.bytes(1), OracleSupport.bytes(11))); assertArrayEquals(OracleSupport.bytes(11), db.get(OracleSupport.bytes(1))); assertEquals(1, db.size()); }
        finally { db.close(); }
    }); }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-OPS-002, HALO-OPS-011, HALO-INV-002. Depends-On: testDefaultOptions. */
    @Test public void testPutUpdateAndGetDB() throws Exception { withDatabase((dir, options) -> {
        HaloDB db = HaloDB.open(dir.toFile(), options);
        try { db.put(OracleSupport.bytes(2), OracleSupport.bytes(20)); db.put(OracleSupport.bytes(2), OracleSupport.bytes(21)); assertArrayEquals(OracleSupport.bytes(21), db.get(OracleSupport.bytes(2))); assertEquals(1, db.size()); }
        finally { db.close(); }
    }); }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-LIFE-002, HALO-LIFE-003, HALO-STATE-002. Depends-On: testDefaultOptions. */
    @Test public void testCreateCloseAndOpenDB() throws Exception { withDatabase((dir, options) -> {
        HaloDB first = HaloDB.open(dir.toFile(), options); first.put(OracleSupport.bytes(3), OracleSupport.bytes(30)); first.close();
        HaloDB second = HaloDB.open(dir.toFile(), options); try { assertArrayEquals(OracleSupport.bytes(30), second.get(OracleSupport.bytes(3))); assertEquals(1, second.size()); } finally { second.close(); }
    }); }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-OPT-009, HALO-INV-009. Depends-On: testDefaultOptions. */
    @Test public void testSyncWrite() throws Exception { withDatabase((dir, options) -> {
        options.enableSyncWrites(true); HaloDB first = HaloDB.open(dir.toFile(), options); first.put(OracleSupport.bytes(4), OracleSupport.bytes(40)); first.close();
        HaloDB second = HaloDB.open(dir.toFile(), options); try { assertArrayEquals(OracleSupport.bytes(40), second.get(OracleSupport.bytes(4))); assertTrue(second.stats().getOptions().isSyncWrite()); } finally { second.close(); }
    }); }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-OPS-002, HALO-LIFE-003, HALO-INV-004. Depends-On: testDefaultOptions. */
    @Test public void testToCheckThatLatestUpdateIsPickedAfterDBOpen() throws Exception { withDatabase((dir, options) -> {
        HaloDB first = HaloDB.open(dir.toFile(), options); first.put(OracleSupport.bytes(5), OracleSupport.bytes(50)); first.put(OracleSupport.bytes(5), OracleSupport.bytes(51)); first.close();
        HaloDB second = HaloDB.open(dir.toFile(), options); try { assertArrayEquals(OracleSupport.bytes(51), second.get(OracleSupport.bytes(5))); assertEquals(1, second.size()); } finally { second.close(); }
    }); }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-OPS-007, HALO-OPS-001, HALO-INV-002. Depends-On: testDefaultOptions. */
    @Test public void testDeleteAndInsert() throws Exception { withDatabase((dir, options) -> {
        HaloDB db = HaloDB.open(dir.toFile(), options); try { db.put(OracleSupport.bytes(8), OracleSupport.bytes(80)); db.delete(OracleSupport.bytes(8)); db.put(OracleSupport.bytes(8), OracleSupport.bytes(81)); assertArrayEquals(OracleSupport.bytes(81), db.get(OracleSupport.bytes(8))); assertEquals(1, db.size()); } finally { db.close(); }
    }); }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-COMP-007, HALO-LIFE-003, HALO-INV-004. Depends-On: testDefaultOptions. */
    @Test public void testDeleteInsertCloseAndOpen() throws Exception { withDatabase((dir, options) -> {
        HaloDB first = HaloDB.open(dir.toFile(), options); first.put(OracleSupport.bytes(9), OracleSupport.bytes(90)); first.delete(OracleSupport.bytes(9)); first.put(OracleSupport.bytes(9), OracleSupport.bytes(91)); first.close();
        HaloDB second = HaloDB.open(dir.toFile(), options); try { assertArrayEquals(OracleSupport.bytes(91), second.get(OracleSupport.bytes(9))); assertEquals(1, second.size()); } finally { second.close(); }
    }); }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-LIFE-008, HALO-ERR-003. Depends-On: testDefaultOptions. */
    @Test public void testMaxFileSize() throws Exception { withDatabase((dir, options) -> {
        HaloDB first = HaloDB.open(dir.toFile(), options); first.put(OracleSupport.bytes(10), OracleSupport.bytes(100)); first.close();
        HaloDBOptions changed = OracleSupport.options(); changed.setMaxFileSize(options.getMaxFileSize() * 2);
        try { HaloDB.open(dir.toFile(), changed); fail("incompatible file size must fail"); } catch (IllegalArgumentException expected) { assertTrue(dir.toFile().isDirectory()); }
    }); }

    /** Seam: lifecycle crossing across database creation, use, close, and reopen. Verifies: HALO-LIFE-005, HALO-LIFE-006, HALO-ERR-002. Depends-On: testDefaultOptions. */
    @Test public void testLock() throws Exception { withDatabase((dir, options) -> {
        HaloDB first = HaloDB.open(dir.toFile(), options);
        try { try { HaloDB.open(dir.toFile(), options); fail("second owner must fail"); } catch (HaloDBException expected) { assertEquals(0, first.size()); } }
        finally { first.close(); }
        HaloDB reopened = HaloDB.open(dir.toFile(), options); try { assertEquals(0, reopened.size()); } finally { reopened.close(); }
    }); }
}
