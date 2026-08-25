package integration;

import static fixtures.Model.cmp;
import static fixtures.Model.rangeContains;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.versionway.util.version.GenericVersionScheme;
import org.versionway.version.Version;

/** Cross-owner checks combining several ordering decisions over one comparison chain. */
class TreeTest {

    private static final GenericVersionScheme S = new GenericVersionScheme();

    private static List<String> sorted(String... versions) throws Exception {
        List<Version> vs = new ArrayList<>();
        for (String s : versions) {
            vs.add(S.parseVersion(s));
        }
        Collections.sort(vs);
        List<String> out = new ArrayList<>();
        for (Version v : vs) {
            out.add(v.toString());
        }
        return out;
    }

    // ================= mutation-dependent cross-owner chains =================

    // Depends-On: atomic::CompareTest::snapshotAboveReleaseAtOne
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void alphaReleaseSnapshotSort() throws Exception {
        assertEquals(Arrays.asList("1.0-alpha", "1.0", "1.0-snapshot"), sorted("1.0", "1.0-snapshot", "1.0-alpha"));
    }

    // Depends-On: atomic::CompareTest::snapshotAboveReleaseAtOne
    // Depends-On: atomic::CompareTest::servicePackBelowReleaseAtOne
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotOutranksServicePack() throws Exception { assertEquals(1, cmp("1.0-snapshot", "1.0-sp")); }

    // Depends-On: atomic::CompareTest::servicePackBelowAlpha
    // MUTATED: QUAL-SP-PLACEMENT
    @Test void servicePackBelowAlphaBelowRelease() throws Exception {
        assertTrue(cmp("1.0-sp", "1.0-alpha") < 0 && cmp("1.0-alpha", "1.0") < 0);
    }

    // Depends-On: atomic::CompareTest::betaAboveMilestoneAtOne
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void alphaMilestoneBetaSort() throws Exception {
        assertEquals(Arrays.asList("1.0-alpha", "1.0-milestone", "1.0-beta"), sorted("1.0-beta", "1.0-alpha", "1.0-milestone"));
    }

    // Depends-On: atomic::CompareTest::finalBelowAlpha
    // MUTATED: QUAL-FINAL-PLACEMENT
    @Test void finalBelowAlphaBelowRelease() throws Exception {
        assertTrue(cmp("1.0-final", "1.0-alpha") < 0 && cmp("1.0-alpha", "1.0") < 0);
    }

    // Depends-On: atomic::CompareTest::crDistinctFromRcAtOne
    // MUTATED: QUAL-CR-ALIAS
    @Test void crAboveRcWhichIsBelowRelease() throws Exception {
        assertTrue(cmp("1.0-cr", "1.0-rc") > 0 && cmp("1.0-rc", "1.0") < 0);
    }

    // Depends-On: atomic::CompareTest::shortAlphaNotAliasAtOne
    // MUTATED: QUAL-SHORT-ALIAS
    @Test void shortAOutranksLongAlpha() throws Exception { assertTrue(cmp("1.0-a1", "1.0-alpha1") > 0); }

    // Depends-On: atomic::CompareTest::snapshotAboveReleaseAtOne
    // Depends-On: atomic::CompareTest::finalBelowReleaseAtOne
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void finalReleaseSnapshotSort() throws Exception {
        assertEquals(Arrays.asList("1.0-final", "1.0", "1.0-snapshot"), sorted("1.0-snapshot", "1.0", "1.0-final"));
    }

    // Depends-On: atomic::CompareTest::betaAboveMilestoneAtOne
    // Depends-On: atomic::CompareTest::betaBelowRelease
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void betaAboveMilestoneButBelowRelease() throws Exception {
        assertTrue(cmp("1.0-beta", "1.0-milestone") > 0 && cmp("1.0-beta", "1.0") < 0);
    }

    // Depends-On: atomic::CompareTest::finalBelowReleaseAtOne
    // Depends-On: atomic::CompareTest::servicePackBelowReleaseAtOne
    // MUTATED: QUAL-FINAL-PLACEMENT
    @Test void bothFinalAndServicePackBelowRelease() throws Exception {
        assertTrue(cmp("1.0-final", "1.0") < 0 && cmp("1.0-sp", "1.0") < 0);
    }

    // Depends-On: atomic::CompareTest::snapshotAboveReleaseAtTwo
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotSortAtBaseTwo() throws Exception {
        assertEquals(Arrays.asList("2.0-alpha", "2.0", "2.0-snapshot"), sorted("2.0-snapshot", "2.0-alpha", "2.0"));
    }

    // Depends-On: atomic::CompareTest::betaAboveMilestoneAtTwo
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void betaAboveMilestoneAtBaseTwo() throws Exception { assertEquals(1, cmp("2.0-beta", "2.0-milestone")); }

    // Depends-On: atomic::CompareTest::servicePackBelowReleaseAtTwo
    // MUTATED: QUAL-SP-PLACEMENT
    @Test void servicePackBelowAlphaAtBaseTwo() throws Exception { assertEquals(-1, cmp("2.0-sp", "2.0-alpha")); }

    // Depends-On: atomic::CompareTest::crDistinctFromRcAtTwo
    // MUTATED: QUAL-CR-ALIAS
    @Test void crAboveRcAtBaseTwo() throws Exception { assertTrue(cmp("2.0-cr", "2.0-rc") > 0); }

    // Depends-On: atomic::CompareTest::shortBetaNotAliasAtOne
    // MUTATED: QUAL-SHORT-ALIAS
    @Test void shortBOutranksLongBeta() throws Exception { assertTrue(cmp("1.0-b1", "1.0-beta1") > 0); }

    // Depends-On: atomic::CompareTest::snapshotAboveReleaseAtOne
    // Depends-On: atomic::CompareTest::finalBelowReleaseAtOne
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotOutranksBothFinalAndServicePack() throws Exception {
        assertTrue(cmp("1.0-snapshot", "1.0-final") > 0 && cmp("1.0-snapshot", "1.0-sp") > 0);
    }

    // ================= controls (unaffected multi-comparison chains) =================

    // Depends-On: atomic::CompareTest::alphaBelowRelease
    @Test void alphaBetaReleaseChain() throws Exception {
        assertTrue(cmp("1.0-alpha", "1.0-beta") < 0 && cmp("1.0-beta", "1.0") < 0);
    }

    // Depends-On: atomic::CompareTest::higherPatchAbove
    @Test void patchReleasesAscending() throws Exception {
        assertEquals(Arrays.asList("1.0", "1.0.1", "1.0.2"), sorted("1.0.2", "1.0", "1.0.1"));
    }

    // Depends-On: atomic::CompareTest::higherMajorAboveLowerMinor
    @Test void majorMinorNumericSort() throws Exception {
        assertEquals(Arrays.asList("1.9", "2.0", "10.0"), sorted("10.0", "2.0", "1.9"));
    }

    // Depends-On: atomic::CompareTest::trailingZeroEqualsBare
    @Test void trailingZeroFormsEqual() throws Exception {
        assertTrue(cmp("1", "1.0") == 0 && cmp("1.0", "1.0.0") == 0);
    }

    // Depends-On: atomic::CompareTest::rcBelowRelease
    @Test void rcBelowReleaseBelowPatch() throws Exception {
        assertTrue(cmp("1.0-rc", "1.0") < 0 && cmp("1.0", "1.0.1") < 0);
    }

    // Depends-On: atomic::CompareTest::generalAvailabilityEqualsRelease
    @Test void gaInterchangeableWithRelease() throws Exception {
        assertTrue(cmp("1.0-ga", "1.0") == 0 && cmp("1.0-ga", "1.0.0") == 0);
    }

    // Depends-On: atomic::CompareTest::aRangeContainsInterior
    // Depends-On: atomic::CompareTest::aHalfOpenRangeExcludesUpper
    @Test void rangeIncludesInteriorAndLowerNotUpper() throws Exception {
        assertTrue(rangeContains("[1.0,2.0)", "1.5") && rangeContains("[1.0,2.0)", "1.0") && !rangeContains("[1.0,2.0)", "2.0"));
    }

    // Depends-On: atomic::CompareTest::aRangeContainsInterior
    @Test void rangeExcludesOutsideEnds() throws Exception {
        assertTrue(!rangeContains("[1.0,2.0)", "0.9") && !rangeContains("[1.0,2.0)", "2.5"));
    }

    // Depends-On: atomic::CompareTest::higherPatchAbove
    @Test void minorVersionsAscending() throws Exception {
        assertEquals(Arrays.asList("1.1", "1.2", "1.3"), sorted("1.3", "1.1", "1.2"));
    }

    // Depends-On: atomic::CompareTest::alphaBelowRelease
    @Test void patchOutranksPreRelease() throws Exception {
        assertTrue(cmp("1.0.1", "1.0-alpha") > 0 && cmp("1.0.1", "1.0-beta") > 0);
    }
}
