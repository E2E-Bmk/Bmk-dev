package atomic;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Parsing, string forms, and bare-version constraints — stable across the mutated families. */
class ParseConstraintNativeTest {

    @Test
    void aBareVersionConstraintRecommendsItself() throws Exception {
        assertEquals(Vs.v("1.5"), Vs.constraint("1.5").getVersion());
    }

    @Test
    void aBareVersionConstraintHasNoRange() throws Exception {
        assertNull(Vs.constraint("1.5").getRange());
    }

    @Test
    void aBareVersionConstraintContainsItself() throws Exception {
        assertTrue(Vs.constraint("1.5").containsVersion(Vs.v("1.5")));
    }

    @Test
    void aBareVersionConstraintExcludesADifferentVersion() throws Exception {
        assertFalse(Vs.constraint("1.5").containsVersion(Vs.v("2.0")));
    }

    @Test
    void aRangeConstraintExposesItsRange() throws Exception {
        assertNotNull(Vs.constraint("[1.0,3.0]").getRange());
    }

    @Test
    void aRangeConstraintContainsAnInteriorVersion() throws Exception {
        assertTrue(Vs.constraint("[1.0,3.0]").containsVersion(Vs.v("2.0")));
    }

    @Test
    void aRangeConstraintExcludesAVersionBelow() throws Exception {
        assertFalse(Vs.constraint("[1.0,3.0]").containsVersion(Vs.v("0.5")));
    }

    @Test
    void theStringFormRoundTrips() throws Exception {
        assertEquals("1.2.3", Vs.v("1.2.3").asString());
    }

    @Test
    void theItemListIsNonEmpty() throws Exception {
        assertTrue(Vs.v("1.2.3").asItems().size() > 0);
    }

    @Test
    void equalVersionsShareAHashCode() throws Exception {
        assertEquals(Vs.v("1.2.3").hashCode(), Vs.v("1.2.3").hashCode());
    }
}
