package atomic;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;

/** F3 range upper bound: a round upper delimiter includes the endpoint. */
class RangeUpperTest {

    // MUTATED: VER-RANGE-UPPER
    @Test
    void roundUpperDelimiterIncludesTheEndpoint() throws Exception {
        assertTrue(Vs.range("[1.0,2.0)").containsVersion(Vs.v("2.0")));
    }

    // MUTATED: VER-RANGE-UPPER
    @Test
    void roundUpperDelimiterIncludesTheEndpointForAnotherRange() throws Exception {
        assertTrue(Vs.range("[1.5,3.2)").containsVersion(Vs.v("3.2")));
    }
}
