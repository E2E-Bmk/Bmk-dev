package integration;

import com.oath.halodb.HaloDB;
import org.junit.Test;
import support.OracleSupport;

import java.nio.file.Path;

import static org.junit.Assert.*;

public class HaloDBCompactionTestRewritten {
    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-COMP-001, HALO-COMP-002, HALO-INV-005. Depends-On: testDefaultOptions. */
    @Test public void testCompaction() throws Exception { exerciseUpdates(false); }
    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-COMP-002, HALO-LIFE-003, HALO-INV-005. Depends-On: testDefaultOptions. */
    @Test public void testReOpenDBAfterCompaction() throws Exception { exerciseUpdates(true); }
    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-COMP-002, HALO-STATE-004. Depends-On: testDefaultOptions. */
    @Test public void testUpdatesToSameFile() throws Exception { exerciseSingleKeyUpdates(); }
    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-COMP-003, HALO-COMP-006, HALO-INV-007. Depends-On: testDefaultOptions. */
    @Test public void testPauseAndResumeCompaction() throws Exception {
        Path dir = OracleSupport.directory(); HaloDB db = null;
        try { db = HaloDB.open(dir.toFile(), OracleSupport.options()); db.put(OracleSupport.bytes(1), OracleSupport.bytes(2)); db.pauseCompaction(); assertArrayEquals(OracleSupport.bytes(2), db.get(OracleSupport.bytes(1))); db.pauseCompaction(); assertEquals(1, db.size()); db.resumeCompaction(); db.resumeCompaction(); assertArrayEquals(OracleSupport.bytes(2), db.get(OracleSupport.bytes(1))); }
        finally { OracleSupport.close(db); OracleSupport.remove(dir); }
    }
    private void exerciseUpdates(boolean reopen) throws Exception {
        Path dir = OracleSupport.directory(); HaloDB db = null;
        try { db = HaloDB.open(dir.toFile(), OracleSupport.options()); for (int i = 0; i < 24; i++) { db.put(OracleSupport.bytes(i), new byte[] {(byte) i}); db.put(OracleSupport.bytes(i), new byte[] {(byte) (i + 1)}); } assertEquals(24, db.size()); if (reopen) { db.close(); db = HaloDB.open(dir.toFile(), OracleSupport.options()); } for (int i = 0; i < 24; i++) assertArrayEquals(new byte[] {(byte) (i + 1)}, db.get(OracleSupport.bytes(i))); assertEquals(24, OracleSupport.records(db).size()); }
        finally { OracleSupport.close(db); OracleSupport.remove(dir); }
    }
    private void exerciseSingleKeyUpdates() throws Exception {
        Path dir = OracleSupport.directory(); HaloDB db = null;
        try { db = HaloDB.open(dir.toFile(), OracleSupport.options()); for (int i = 0; i < 20; i++) db.put(OracleSupport.bytes(7), OracleSupport.bytes(i)); assertEquals(1, db.size()); assertArrayEquals(OracleSupport.bytes(19), db.get(OracleSupport.bytes(7))); assertEquals(1, OracleSupport.records(db).size()); }
        finally { OracleSupport.close(db); OracleSupport.remove(dir); }
    }
}
