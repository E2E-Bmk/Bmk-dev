package atomic;

import static fixtures.Model.cmp;
import static fixtures.Model.rangeContains;
import static fixtures.Model.constraintContains;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Single-owner checks pinning one ordering decision at a time. */
class CompareTest {

    // ================= F1: snapshot sorts ABOVE release (QUAL-SNAPSHOT-PLACEMENT) =================
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotAboveReleaseAtOne() throws Exception { assertEquals(1, cmp("1.0-snapshot", "1.0")); }
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotAboveReleaseAtTwo() throws Exception { assertEquals(1, cmp("2.0-snapshot", "2.0")); }
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotAboveGeneralAvailability() throws Exception { assertEquals(1, cmp("1.0-snapshot", "1.0-ga")); }
    // MUTATED: QUAL-SNAPSHOT-PLACEMENT
    @Test void snapshotAboveReleaseAtThreeFive() throws Exception { assertEquals(1, cmp("3.5-snapshot", "3.5")); }

    // ================= F2: service-pack sorts BELOW release (QUAL-SP-PLACEMENT) =================
    // MUTATED: QUAL-SP-PLACEMENT
    @Test void servicePackBelowReleaseAtOne() throws Exception { assertEquals(-1, cmp("1.0-sp", "1.0")); }
    // MUTATED: QUAL-SP-PLACEMENT
    @Test void servicePackBelowReleaseAtTwo() throws Exception { assertEquals(-1, cmp("2.0-sp", "2.0")); }
    // MUTATED: QUAL-SP-PLACEMENT
    @Test void servicePackBelowAlpha() throws Exception { assertEquals(-1, cmp("1.0-sp", "1.0-alpha")); }
    // MUTATED: QUAL-SP-PLACEMENT
    @Test void servicePackBelowReleaseAtThree() throws Exception { assertEquals(-1, cmp("3.0-sp", "3.0")); }

    // ================= F3: 'cr' is not an alias of 'rc' (QUAL-CR-ALIAS) =================
    // MUTATED: QUAL-CR-ALIAS
    @Test void crDistinctFromRcAtOne() throws Exception { assertEquals(1, cmp("1.0-cr", "1.0-rc")); }
    // MUTATED: QUAL-CR-ALIAS
    @Test void crDistinctFromRcAtTwo() throws Exception { assertEquals(1, cmp("2.0-cr", "2.0-rc")); }
    // MUTATED: QUAL-CR-ALIAS
    @Test void crDistinctFromRcAtOneFive() throws Exception { assertEquals(1, cmp("1.5-cr", "1.5-rc")); }
    // MUTATED: QUAL-CR-ALIAS
    @Test void crDistinctFromRcAtThree() throws Exception { assertEquals(1, cmp("3.0-cr", "3.0-rc")); }

    // ================= F4: 'final' is a pre-release qualifier (QUAL-FINAL-PLACEMENT) =================
    // MUTATED: QUAL-FINAL-PLACEMENT
    @Test void finalBelowReleaseAtOne() throws Exception { assertEquals(-1, cmp("1.0-final", "1.0")); }
    // MUTATED: QUAL-FINAL-PLACEMENT
    @Test void finalBelowReleaseAtTwo() throws Exception { assertEquals(-1, cmp("2.0-final", "2.0")); }
    // MUTATED: QUAL-FINAL-PLACEMENT
    @Test void finalBelowAlpha() throws Exception { assertEquals(-1, cmp("1.0-final", "1.0-alpha")); }
    // MUTATED: QUAL-FINAL-PLACEMENT
    @Test void finalBelowReleaseAtThree() throws Exception { assertEquals(-1, cmp("3.0-final", "3.0")); }

    // ================= F5: single-letter a/b/m are not aliases (QUAL-SHORT-ALIAS) =================
    // MUTATED: QUAL-SHORT-ALIAS
    @Test void shortAlphaNotAliasAtOne() throws Exception { assertEquals(1, cmp("1.0-a1", "1.0-alpha1")); }
    // MUTATED: QUAL-SHORT-ALIAS
    @Test void shortBetaNotAliasAtOne() throws Exception { assertEquals(1, cmp("1.0-b1", "1.0-beta1")); }
    // MUTATED: QUAL-SHORT-ALIAS
    @Test void shortAlphaNotAliasAtTwo() throws Exception { assertEquals(1, cmp("2.0-a1", "2.0-alpha1")); }
    // MUTATED: QUAL-SHORT-ALIAS
    @Test void shortBetaNotAliasAtTwo() throws Exception { assertEquals(1, cmp("2.0-b1", "2.0-beta1")); }

    // ================= F6: beta sorts ABOVE milestone (QUAL-BETA-MILESTONE-ORDER) =================
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void betaAboveMilestoneAtOne() throws Exception { assertEquals(1, cmp("1.0-beta", "1.0-milestone")); }
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void betaAboveMilestoneAtTwo() throws Exception { assertEquals(1, cmp("2.0-beta", "2.0-milestone")); }
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void milestoneBelowBetaAtOne() throws Exception { assertEquals(-1, cmp("1.0-milestone", "1.0-beta")); }
    // MUTATED: QUAL-BETA-MILESTONE-ORDER
    @Test void betaAboveMilestoneAtThree() throws Exception { assertEquals(1, cmp("3.0-beta", "3.0-milestone")); }

    // ================= controls (identical under upstream and this scheme) =================
    @Test void alphaBelowRelease() throws Exception { assertEquals(-1, cmp("1.0-alpha", "1.0")); }
    @Test void alphaBelowBeta() throws Exception { assertEquals(-1, cmp("1.0-alpha", "1.0-beta")); }
    @Test void alphaBelowMilestone() throws Exception { assertEquals(-1, cmp("1.0-alpha", "1.0-milestone")); }
    @Test void rcBelowRelease() throws Exception { assertEquals(-1, cmp("1.0-rc", "1.0")); }
    @Test void betaBelowRelease() throws Exception { assertEquals(-1, cmp("1.0-beta", "1.0")); }
    @Test void milestoneBelowRelease() throws Exception { assertEquals(-1, cmp("1.0-milestone", "1.0")); }
    @Test void generalAvailabilityEqualsRelease() throws Exception { assertEquals(0, cmp("1.0-ga", "1.0")); }
    @Test void trailingZeroEqualsBare() throws Exception { assertEquals(0, cmp("1.0", "1")); }
    @Test void twoTrailingZerosEqualBare() throws Exception { assertEquals(0, cmp("1.0.0", "1")); }
    @Test void higherPatchAbove() throws Exception { assertEquals(1, cmp("1.0.1", "1.0")); }
    @Test void higherMajorAboveLowerMinor() throws Exception { assertEquals(1, cmp("2.0", "1.9")); }
    @Test void lowerNumberBelow() throws Exception { assertEquals(-1, cmp("1", "2")); }
    @Test void identicalEqual() throws Exception { assertEquals(0, cmp("1.2.3", "1.2.3")); }
    @Test void aRangeContainsInterior() throws Exception { assertTrue(rangeContains("[1.0,2.0)", "1.5")); }
    @Test void aHalfOpenRangeExcludesUpper() throws Exception { assertFalse(rangeContains("[1.0,2.0)", "2.0")); }
    @Test void aConstraintRangeContainsInterior() throws Exception { assertTrue(constraintContains("[1.0,2.0)", "1.5")); }
}
