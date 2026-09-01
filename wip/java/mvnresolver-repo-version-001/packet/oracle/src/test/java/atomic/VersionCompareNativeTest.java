package atomic;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Version ordering facts that hold regardless of the qualifier/snapshot policy. */
class VersionCompareNativeTest {

    @Test
    void aHigherMinorIsGreater() throws Exception {
        assertTrue(Vs.v("1.1").compareTo(Vs.v("1.0")) > 0);
    }

    @Test
    void aHigherMajorIsGreater() throws Exception {
        assertTrue(Vs.v("2.0").compareTo(Vs.v("1.9")) > 0);
    }

    @Test
    void aTrailingZeroCompareEqual() throws Exception {
        assertEquals(0, Vs.v("1.0").compareTo(Vs.v("1.0.0")));
    }

    @Test
    void aMorePreciseVersionIsGreater() throws Exception {
        assertTrue(Vs.v("1.0.1").compareTo(Vs.v("1.0")) > 0);
    }

    @Test
    void doubleDigitSegmentComparesNumerically() throws Exception {
        assertTrue(Vs.v("1.10").compareTo(Vs.v("1.9")) > 0);
    }

    @Test
    void alphaPrecedesBeta() throws Exception {
        assertTrue(Vs.v("1-alpha").compareTo(Vs.v("1-beta")) < 0);
    }

    @Test
    void alphaPrecedesRelease() throws Exception {
        assertTrue(Vs.v("1-alpha").compareTo(Vs.v("1")) < 0);
    }

    @Test
    void spFollowsRelease() throws Exception {
        assertTrue(Vs.v("1-sp").compareTo(Vs.v("1")) > 0);
    }

    @Test
    void equalStringsCompareEqual() throws Exception {
        assertEquals(0, Vs.v("1.2.3").compareTo(Vs.v("1.2.3")));
    }

    @Test
    void comparisonIsAntisymmetric() throws Exception {
        int ab = Vs.v("1.0").compareTo(Vs.v("2.0"));
        int ba = Vs.v("2.0").compareTo(Vs.v("1.0"));
        assertTrue(ab < 0 && ba > 0);
    }
}
