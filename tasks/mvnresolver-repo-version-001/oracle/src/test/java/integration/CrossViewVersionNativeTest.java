package integration;

import fixtures.Vs;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Agreement between the version, range, constraint and union projections over the same inputs. */
class CrossViewVersionNativeTest {

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void constraintContainmentMatchesItsRangeInside() throws Exception {
        assertEquals(Vs.range("[1.0,3.0]").containsVersion(Vs.v("2.0")),
                Vs.constraint("[1.0,3.0]").containsVersion(Vs.v("2.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void constraintContainmentMatchesItsRangeOutside() throws Exception {
        assertEquals(Vs.range("[1.0,3.0]").containsVersion(Vs.v("5.0")),
                Vs.constraint("[1.0,3.0]").containsVersion(Vs.v("5.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void singleRangeUnionMatchesItsMemberInside() throws Exception {
        assertEquals(Vs.range("[1.0,3.0]").containsVersion(Vs.v("2.0")),
                Vs.union(Vs.range("[1.0,3.0]")).containsVersion(Vs.v("2.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void singleRangeUnionMatchesItsMemberOutside() throws Exception {
        assertEquals(Vs.range("[1.0,2.0]").containsVersion(Vs.v("5.0")),
                Vs.union(Vs.range("[1.0,2.0]")).containsVersion(Vs.v("5.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anInteriorVersionExceedsTheLowerBound() throws Exception {
        assertTrue(Vs.v("2.0").compareTo(Vs.range("[1.0,3.0]").getLowerBound().getVersion()) > 0);
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anInteriorVersionPrecedesTheUpperBound() throws Exception {
        assertTrue(Vs.v("2.0").compareTo(Vs.range("[1.0,3.0]").getUpperBound().getVersion()) < 0);
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aConstraintRangeReportsItsLowerBoundVersion() throws Exception {
        assertEquals(Vs.v("1.0"), Vs.constraint("[1.0,3.0]").getRange().getLowerBound().getVersion());
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void anOverlapVersionIsInBothTheUnionAndAMember() throws Exception {
        assertTrue(Vs.union(Vs.range("[1.0,3.0]"), Vs.range("[2.0,4.0]")).containsVersion(Vs.v("2.5"))
                && Vs.range("[1.0,3.0]").containsVersion(Vs.v("2.5")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aVersionAboveTheRangeAlsoComparesGreaterThanTheUpperBound() throws Exception {
        assertTrue(!Vs.range("[1.0,3.0]").containsVersion(Vs.v("5.0"))
                && Vs.v("5.0").compareTo(Vs.v("3.0")) > 0);
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void constraintContainsItsLowerEdgeLikeItsRange() throws Exception {
        assertEquals(Vs.range("[1.0,3.0]").containsVersion(Vs.v("1.0")),
                Vs.constraint("[1.0,3.0]").containsVersion(Vs.v("1.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void bareConstraintsOrderByTheirRecommendedVersions() throws Exception {
        assertTrue(Vs.constraint("2.0").getVersion().compareTo(Vs.constraint("1.0").getVersion()) > 0);
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void everyEndpointAndInteriorIsWithinTheRange() throws Exception {
        assertTrue(Vs.range("[1.0,3.0]").containsVersion(Vs.v("1.0"))
                && Vs.range("[1.0,3.0]").containsVersion(Vs.v("2.0"))
                && Vs.range("[1.0,3.0]").containsVersion(Vs.v("3.0")));
    }

    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aVersionOutsideASingleRangeUnionIsAbsentLikeInTheRange() throws Exception {
        assertFalse(Vs.union(Vs.range("[1.0,2.0]")).containsVersion(Vs.v("9.0")));
    }
}
