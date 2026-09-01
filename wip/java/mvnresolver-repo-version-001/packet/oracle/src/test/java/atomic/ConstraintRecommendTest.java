package atomic;

import fixtures.Vs;
import org.eclipse.aether.version.VersionConstraint;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

/** F4 constraint recommendation: a range constraint recommends its lower bound. */
class ConstraintRecommendTest {

    // MUTATED: VER-CONSTRAINT-RECOMMEND
    @Test
    void aRangeConstraintRecommendsItsLowerBound() throws Exception {
        VersionConstraint c = Vs.constraint("[1.0,2.0)");
        assertNotNull(c.getVersion());
        assertEquals(Vs.v("1.0"), c.getVersion());
    }

    // MUTATED: VER-CONSTRAINT-RECOMMEND
    @Test
    void anotherRangeConstraintRecommendsItsLowerBound() throws Exception {
        VersionConstraint c = Vs.constraint("[2.5,9.0]");
        assertNotNull(c.getVersion());
        assertEquals(Vs.v("2.5"), c.getVersion());
    }
}
