package atomic;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/** F2 snapshot ordering: a SNAPSHOT ranks after its released version. */
class SnapshotOrderTest {

    // MUTATED: VER-SNAPSHOT-ORDER
    @Test
    void snapshotRanksAfterRelease() throws Exception {
        assertTrue(Vs.v("1.0-SNAPSHOT").compareTo(Vs.v("1.0")) > 0);
    }

    // MUTATED: VER-SNAPSHOT-ORDER
    @Test
    void aLaterSnapshotAlsoRanksAfterItsRelease() throws Exception {
        assertTrue(Vs.v("2.3.1-SNAPSHOT").compareTo(Vs.v("2.3.1")) > 0);
    }
}
