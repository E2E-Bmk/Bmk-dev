package integration;

import fixtures.Vs;
import org.eclipse.aether.version.VersionRange;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;

/**
 * F5 union containment: a union contains a version only when every member range does.
 * A version inside just one member is therefore NOT contained. Crosses the union owner
 * and the range-containment owner.
 */
class UnionContainTest {

    // MUTATED: VER-UNION-CONTAIN
    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aVersionInOnlyOneMemberIsNotContainedByTheUnion() throws Exception {
        VersionRange u = Vs.union(Vs.range("[1.0,1.5]"), Vs.range("[3.0,4.0]"));
        assertFalse(u.containsVersion(Vs.v("3.5")));
    }

    // MUTATED: VER-UNION-CONTAIN
    // Depends-On: atomic::VersionCompareNativeTest::aHigherMinorIsGreater
    @Test
    void aVersionInTheOtherLoneMemberIsAlsoNotContained() throws Exception {
        VersionRange u = Vs.union(Vs.range("[1.0,1.5]"), Vs.range("[3.0,4.0]"));
        assertFalse(u.containsVersion(Vs.v("1.2")));
    }
}
