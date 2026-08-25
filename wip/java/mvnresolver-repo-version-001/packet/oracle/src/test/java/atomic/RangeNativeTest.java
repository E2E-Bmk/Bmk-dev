package atomic;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Range membership and bounds that hold regardless of the round-upper convention. */
class RangeNativeTest {

    @Test
    void anInteriorVersionIsContained() throws Exception {
        assertTrue(Vs.range("[1.0,2.0]").containsVersion(Vs.v("1.5")));
    }

    @Test
    void aVersionBelowTheLowerBoundIsNotContained() throws Exception {
        assertFalse(Vs.range("[1.0,2.0]").containsVersion(Vs.v("0.9")));
    }

    @Test
    void aVersionAboveTheUpperBoundIsNotContained() throws Exception {
        assertFalse(Vs.range("[1.0,2.0]").containsVersion(Vs.v("2.5")));
    }

    @Test
    void aSquareLowerBoundIncludesItsEndpoint() throws Exception {
        assertTrue(Vs.range("[1.0,2.0]").containsVersion(Vs.v("1.0")));
    }

    @Test
    void aSquareUpperBoundIncludesItsEndpoint() throws Exception {
        assertTrue(Vs.range("[1.0,2.0]").containsVersion(Vs.v("2.0")));
    }

    @Test
    void aRoundLowerBoundExcludesItsEndpoint() throws Exception {
        assertFalse(Vs.range("(1.0,2.0]").containsVersion(Vs.v("1.0")));
    }

    @Test
    void theLowerBoundVersionIsReported() throws Exception {
        assertEquals(Vs.v("1.0"), Vs.range("[1.0,2.0]").getLowerBound().getVersion());
    }

    @Test
    void theUpperBoundVersionIsReported() throws Exception {
        assertEquals(Vs.v("2.0"), Vs.range("[1.0,2.0]").getUpperBound().getVersion());
    }

    @Test
    void aSquareLowerBoundIsInclusive() throws Exception {
        assertTrue(Vs.range("[1.0,2.0]").getLowerBound().isInclusive());
    }

    @Test
    void aRoundLowerBoundIsNotInclusive() throws Exception {
        assertFalse(Vs.range("(1.0,2.0]").getLowerBound().isInclusive());
    }
}
