package integration;

import fixtures.Vs;
import org.eclipse.aether.version.VersionRange;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Union behavior over versions that lie in the overlap of two ranges (in every member) or
 * outside all members, so the outcome is stable regardless of any/all semantics. Crosses the
 * union owner and the range-containment owner.
 */
class UnionNativeTest {

    private VersionRange overlap() throws Exception {
        return Vs.union(Vs.range("[1.0,3.0]"), Vs.range("[2.0,4.0]"));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anOverlapInteriorVersionIsContained() throws Exception {
        assertTrue(overlap().containsVersion(Vs.v("2.5")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void theOverlapLowerEdgeIsContained() throws Exception {
        assertTrue(overlap().containsVersion(Vs.v("2.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void theOverlapUpperEdgeIsContained() throws Exception {
        assertTrue(overlap().containsVersion(Vs.v("3.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anotherOverlapInteriorVersionIsContained() throws Exception {
        assertTrue(overlap().containsVersion(Vs.v("2.9")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aVersionBelowAllMembersIsNotContained() throws Exception {
        assertFalse(overlap().containsVersion(Vs.v("0.5")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aVersionAboveAllMembersIsNotContained() throws Exception {
        assertFalse(overlap().containsVersion(Vs.v("5.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aFarBelowVersionIsNotContained() throws Exception {
        assertFalse(overlap().containsVersion(Vs.v("0.1")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aSingleRangeUnionContainsAnInteriorVersion() throws Exception {
        assertTrue(Vs.union(Vs.range("[1.0,2.0]")).containsVersion(Vs.v("1.5")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aSingleRangeUnionExcludesAnOutsideVersion() throws Exception {
        assertFalse(Vs.union(Vs.range("[1.0,2.0]")).containsVersion(Vs.v("3.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aSingleRangeUnionIncludesItsLowerEndpoint() throws Exception {
        assertTrue(Vs.union(Vs.range("[1.0,2.0]")).containsVersion(Vs.v("1.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anotherSingleRangeUnionContainsAnInteriorVersion() throws Exception {
        assertTrue(Vs.union(Vs.range("[2.0,5.0]")).containsVersion(Vs.v("4.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anEmptyOverlapVersionAboveIsNotContained() throws Exception {
        assertFalse(overlap().containsVersion(Vs.v("4.5")));
    }
}
