package integration;

import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBOptions;
import org.junit.Test;
import support.OracleSupport;

import java.nio.file.Path;
import java.util.Map;

import static org.junit.Assert.*;

public class HaloDBDeletionTestRewritten {
    private interface Scenario { void run(Path directory, HaloDBOptions options) throws Exception; }
    private void run(Scenario scenario) throws Exception { Path dir = OracleSupport.directory(); try { scenario.run(dir, OracleSupport.options()); } finally { OracleSupport.remove(dir); } }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-ITER-004, HALO-INV-003. Depends-On: testDefaultOptions. */
    @Test public void testDeleteWithIterator() throws Exception { run((dir, options) -> { HaloDB db = HaloDB.open(dir.toFile(), options); try { db.put(OracleSupport.bytes(1), OracleSupport.bytes(2)); db.put(OracleSupport.bytes(3), OracleSupport.bytes(4)); db.delete(OracleSupport.bytes(1)); Map<String, byte[]> records = OracleSupport.records(db); assertEquals(1, records.size()); assertArrayEquals(OracleSupport.bytes(4), records.get("[3]")); } finally { db.close(); } }); }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-OPS-007, HALO-OPS-001, HALO-INV-002. Depends-On: testDefaultOptions. */
    @Test public void testDeleteAndInsert() throws Exception { run((dir, options) -> { HaloDB db = HaloDB.open(dir.toFile(), options); try { db.put(OracleSupport.bytes(5), OracleSupport.bytes(6)); db.delete(OracleSupport.bytes(5)); db.put(OracleSupport.bytes(5), OracleSupport.bytes(7)); assertArrayEquals(OracleSupport.bytes(7), db.get(OracleSupport.bytes(5))); assertEquals(1, db.size()); } finally { db.close(); } }); }

    /** Seam: state consistency across persisted records, compaction, and public database views. Verifies: HALO-COMP-001, HALO-COMP-002, HALO-INV-005. Depends-On: testDefaultOptions. */
    @Test public void testDeleteAndMerge() throws Exception { run((dir, options) -> { options.setCompactionThresholdPerFile(0.1); HaloDB db = HaloDB.open(dir.toFile(), options); try { for (int i = 0; i < 40; i++) db.put(OracleSupport.bytes(i), new byte[512]); for (int i = 0; i < 20; i++) db.delete(OracleSupport.bytes(i)); assertEquals(20, db.size()); for (int i = 20; i < 40; i++) assertNotNull(db.get(OracleSupport.bytes(i))); } finally { db.close(); } }); }

}
