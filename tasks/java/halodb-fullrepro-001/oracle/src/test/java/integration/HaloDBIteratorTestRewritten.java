package integration;

import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBIterator;
import com.oath.halodb.Record;
import org.junit.Test;
import support.OracleSupport;

import java.nio.file.Path;
import java.util.Map;
import java.util.NoSuchElementException;

import static org.junit.Assert.*;

public class HaloDBIteratorTestRewritten {
    private interface Scenario { void run(HaloDB database) throws Exception; }
    private void run(Scenario scenario) throws Exception { Path dir = OracleSupport.directory(); HaloDB db = null; try { db = HaloDB.open(dir.toFile(), OracleSupport.options()); scenario.run(db); } finally { OracleSupport.close(db); OracleSupport.remove(dir); } }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-ITER-004, HALO-INV-003. Depends-On: testDefaultOptions. */
    @Test public void testWithDelete() throws Exception { run(db -> { db.put(OracleSupport.bytes(1), OracleSupport.bytes(2)); db.put(OracleSupport.bytes(3), OracleSupport.bytes(4)); db.delete(OracleSupport.bytes(1)); Map<String, byte[]> rows = OracleSupport.records(db); assertEquals(1, rows.size()); assertArrayEquals(OracleSupport.bytes(4), rows.get("[3]")); }); }
    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-ITER-001, HALO-ITER-009, HALO-INV-001. Depends-On: testDefaultOptions. */
    @Test public void testPutAndGetDB() throws Exception { run(db -> { db.put(OracleSupport.bytes(5), OracleSupport.bytes(6)); HaloDBIterator iterator = db.newIterator(); assertTrue(iterator.hasNext()); Record record = iterator.next(); assertArrayEquals(OracleSupport.bytes(5), record.getKey()); assertArrayEquals(OracleSupport.bytes(6), record.getValue()); assertFalse(iterator.hasNext()); }); }
    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-ITER-003, HALO-ITER-010, HALO-INV-002. Depends-On: testDefaultOptions. */
    @Test public void testPutUpdateAndGetDB() throws Exception { run(db -> { db.put(OracleSupport.bytes(7), OracleSupport.bytes(8)); db.put(OracleSupport.bytes(7), OracleSupport.bytes(9)); Map<String, byte[]> rows = OracleSupport.records(db); assertEquals(1, rows.size()); assertArrayEquals(db.get(OracleSupport.bytes(7)), rows.get("[7]")); }); }
    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-COMP-002, HALO-ITER-003, HALO-INV-005. Depends-On: testDefaultOptions. */
    @Test public void testPutUpdateCompactAndGetDB() throws Exception { run(db -> { for (int i = 0; i < 16; i++) { db.put(OracleSupport.bytes(i), OracleSupport.bytes(i)); db.put(OracleSupport.bytes(i), OracleSupport.bytes(i + 1)); } Map<String, byte[]> rows = OracleSupport.records(db); assertEquals(16, rows.size()); for (int i = 0; i < 16; i++) assertArrayEquals(OracleSupport.bytes(i + 1), rows.get("[" + i + "]")); }); }
}
