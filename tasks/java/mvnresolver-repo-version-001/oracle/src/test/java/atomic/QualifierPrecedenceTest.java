package atomic;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/** F1 qualifier precedence: a milestone qualifier ranks above rc. */
class QualifierPrecedenceTest {

    // MUTATED: VER-QUALIFIER-ORDER
    @Test
    void milestoneRanksAboveRc() throws Exception {
        assertTrue(Vs.v("1-milestone").compareTo(Vs.v("1-rc")) > 0);
    }

    // MUTATED: VER-QUALIFIER-ORDER
    @Test
    void milestoneBuildRanksAboveRcBuild() throws Exception {
        assertTrue(Vs.v("2.1-milestone-3").compareTo(Vs.v("2.1-rc-3")) > 0);
    }
}
