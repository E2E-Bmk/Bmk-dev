package fixtures;

import org.xmldiff.builder.DiffBuilder;
import org.xmldiff.diff.Comparison;
import org.xmldiff.diff.ComparisonResult;
import org.xmldiff.diff.ComparisonType;
import org.xmldiff.diff.DefaultNodeMatcher;
import org.xmldiff.diff.Diff;
import org.xmldiff.diff.Difference;
import org.xmldiff.diff.ElementSelectors;

/** Fixtures for the xmldiff oracle: run comparisons and read out difference types/results. */
public final class Xml {

    private Xml() {}

    /** A comparison recording both similar and different outcomes. */
    public static Diff diff(String control, String test) {
        return DiffBuilder.compare(control).withTest(test).checkForSimilar().build();
    }

    /** A default comparison (only different outcomes recorded). */
    public static Diff strictDiff(String control, String test) {
        return DiffBuilder.compare(control).withTest(test).build();
    }

    /** The result recorded for the first comparison of the given type, or null if none. */
    public static ComparisonResult resultOf(String control, String test, ComparisonType type) {
        for (Difference d : diff(control, test).getDifferences()) {
            if (d.getComparison().getType() == type) {
                return d.getResult();
            }
        }
        return null;
    }

    /** Whether any comparison of the given type was recorded (similar or different). */
    public static boolean hasType(String control, String test, ComparisonType type) {
        return resultOf(control, test, type) != null;
    }

    /** Count of recorded differences under checkForSimilar. */
    public static int diffCount(String control, String test) {
        int n = 0;
        for (Difference ignored : diff(control, test).getDifferences()) {
            n++;
        }
        return n;
    }

    /** Result for a comparison type, matching children by name so reordering is detected. */
    public static ComparisonResult resultOfSeq(String control, String test, ComparisonType type) {
        Diff d = DiffBuilder.compare(control).withTest(test)
                .withNodeMatcher(new DefaultNodeMatcher(ElementSelectors.byName)).checkForSimilar().build();
        for (Difference x : d.getDifferences()) {
            if (x.getComparison().getType() == type) {
                return x.getResult();
            }
        }
        return null;
    }

    /** hasDifferences with children matched by name (default recording of DIFFERENT only). */
    public static boolean seqStrictHasDiff(String control, String test) {
        return DiffBuilder.compare(control).withTest(test)
                .withNodeMatcher(new DefaultNodeMatcher(ElementSelectors.byName)).build().hasDifferences();
    }
}
