package integration;

import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBStats;
import org.junit.Test;
import support.OracleSupport;

import java.nio.file.Path;

import static org.junit.Assert.*;

public class HaloDBStatsTestRewritten {
    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-STAT-001, HALO-STATE-005, HALO-INV-001. Depends-On: testDefaultOptions. */
    @Test public void testOptions() throws Exception {
        Path dir = OracleSupport.directory(); HaloDB db = null;
        try { db = HaloDB.open(dir.toFile(), OracleSupport.options()); db.put(OracleSupport.bytes(1), OracleSupport.bytes(2)); HaloDBStats stats = db.stats(); assertEquals(db.size(), stats.getSize()); assertEquals(OracleSupport.options().getMaxFileSize(), stats.getOptions().getMaxFileSize()); assertEquals(1, stats.getSize()); }
        finally { OracleSupport.close(db); OracleSupport.remove(dir); }
    }

    /** Seam: state consistency across point lookup, iteration, size, options, and statistics. Verifies: HALO-STAT-012, HALO-INV-008. Depends-On: testDefaultOptions. */
    @Test public void testIndexStats() throws Exception {
        Path dir = OracleSupport.directory(); HaloDB db = null;
        try { db = HaloDB.open(dir.toFile(), OracleSupport.options()); db.put(OracleSupport.bytes(3), OracleSupport.bytes(4)); long size = db.size(); db.resetStats(); HaloDBStats stats = db.stats(); assertEquals(size, stats.getSize()); assertEquals(db.size(), stats.getSize()); assertTrue(stats.getNumberOfSegments() > 0); assertTrue(stats.getMaxSizePerSegment() > 0); }
        finally { OracleSupport.close(db); OracleSupport.remove(dir); }
    }
}
