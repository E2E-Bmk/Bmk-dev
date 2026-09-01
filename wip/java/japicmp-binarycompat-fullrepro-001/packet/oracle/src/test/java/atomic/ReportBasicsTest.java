package atomic;

import fixtures.Bytecode;
import fixtures.Compare;
import javassist.ClassPool;
import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.plumbline.config.Options;
import org.plumbline.exception.JApiCompareException;
import org.plumbline.model.JApiClass;
import org.plumbline.output.semver.SemverOut;
import org.plumbline.output.stdout.StdoutOutputGenerator;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The reporting surface read one projection at a time: the difference description,
 * the sign group that prefixes every reported node, the semantic-version strings,
 * and the failure taxonomy.
 *
 * <p>Each test here reads a single projection. Agreement *between* projections is
 * the integration layer's subject, not this one's.
 */
class ReportBasicsTest {

    private static List<JApiClass> methodRemoved() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        return Compare.compare(before, after);
    }

    private static List<JApiClass> unchanged() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void run() {}");
        return Compare.compare(before, after);
    }

    /** Seam: an absent version label. Verifies: JAPI-RPT-001. */
    @Test
    void anUnsetVersionLabelRendersAsTheNotAvailablePlaceholder() {
        Options options = Options.newDefault();

        assertEquals("n.a.", Options.N_A);
        assertTrue(options.getDifferenceDescription().contains(Options.N_A));
    }

    /** Seam: both version labels set. Verifies: JAPI-RPT-002. */
    @Test
    void theDifferenceDescriptionNamesTheNewVersionBeforeTheOld() {
        Options options = Options.newDefault();
        options.setOldVersion("1.0.0");
        options.setNewVersion("2.0.0");

        assertEquals("Comparing source compatibility of 2.0.0 against 1.0.0",
                options.getDifferenceDescription());
    }

    /** Seam: the description follows the reporting mode. Verifies: JAPI-RPT-003. */
    @Test
    void onlyBinaryIncompatibleReportingDescribesBinaryCompatibility() {
        Options options = Options.newDefault();
        options.setOldVersion("1.0.0");
        options.setNewVersion("2.0.0");
        options.setOutputOnlyBinaryIncompatibleModifications(true);

        assertEquals("Comparing binary compatibility of 2.0.0 against 1.0.0",
                options.getDifferenceDescription());
    }

    /** Seam: a blank label is treated as absent. Verifies: JAPI-RPT-004. */
    @Test
    void aBlankVersionLabelRendersAsThePlaceholder() {
        Options options = Options.newDefault();
        options.setOldVersion("   ");
        options.setNewVersion("2.0.0");

        assertTrue(options.getDifferenceDescription().endsWith(Options.N_A));
    }

    /** Seam: the first report line. Verifies: JAPI-RPT-005. */
    @Test
    void theTextReportOpensWithTheDifferenceDescription() throws Exception {
        Options options = Options.newDefault();
        options.setOldVersion("1.0.0");
        options.setNewVersion("2.0.0");

        String report = new StdoutOutputGenerator(options, methodRemoved()).generate();

        assertTrue(report.startsWith(options.getDifferenceDescription()),
                "report began: " + report.substring(0, Math.min(80, report.length())));
    }

    /** Seam: a modified class line. Verifies: JAPI-RPT-006. */
    @Test
    void aModifiedNodeIsPrefixedByTheModifiedSignGroup() throws Exception {
        String report = new StdoutOutputGenerator(Options.newDefault(), methodRemoved()).generate();

        assertTrue(report.contains("***"), "expected a MODIFIED sign group in: " + report);
    }

    /** Seam: a binary-incompatible node carries the fourth sign character. Verifies: JAPI-RPT-007. */
    @Test
    void aBinaryIncompatibleNodeCarriesTheExclamationSign() throws Exception {
        String report = new StdoutOutputGenerator(Options.newDefault(), methodRemoved()).generate();

        assertTrue(report.contains("!"), "expected a binary-incompatible mark in: " + report);
    }

    /** Seam: an empty tree. Verifies: JAPI-RPT-008. */
    @Test
    void anEmptyTreeReportsNoChanges() {
        String report =
                new StdoutOutputGenerator(Options.newDefault(), Collections.emptyList()).generate();

        assertTrue(report.contains("No changes."), "report was: " + report);
    }


    /** Seam: a removed method drives the major level. Verifies: JAPI-RPT-010. */
    @Test
    void removingAPublicMethodYieldsTheMajorVersionString() throws Exception {
        String semver = new SemverOut(Options.newDefault(), methodRemoved()).generate();

        assertEquals(SemverOut.SEMVER_MAJOR, semver);
    }

    /** Seam: nothing changed. Verifies: JAPI-RPT-011. */
    @Test
    void anUnchangedTreeDoesNotYieldTheMajorVersionString() throws Exception {
        String semver = new SemverOut(Options.newDefault(), unchanged()).generate();

        assertNotEquals(SemverOut.SEMVER_MAJOR, semver);
    }

    /** Seam: an empty tree visits no node. Verifies: JAPI-RPT-012. */
    @Test
    void anEmptyTreeYieldsTheCompatibleVersionString() {
        String semver =
                new SemverOut(Options.newDefault(), Collections.emptyList()).generate();

        assertEquals(SemverOut.SEMVER_COMPATIBLE, semver);
    }

    /** Seam: the walk reports every visited node to a listener. Verifies: JAPI-RPT-013. */
    @Test
    void theSemanticVersionWalkNotifiesTheListenerForEveryVisitedNode() throws Exception {
        int[] visits = {0};
        new SemverOut(Options.newDefault(), methodRemoved(),
                (compatibility, level) -> visits[0]++).generate();

        assertTrue(visits[0] > 0, "the listener was never called");
    }

    /** Seam: a null listener is replaced rather than dereferenced. Verifies: JAPI-RPT-014. */
    @Test
    void aNullListenerIsAcceptedAndBehavesAsTheDoNothingListener() throws Exception {
        String semver = new SemverOut(Options.newDefault(), methodRemoved(), null).generate();

        assertEquals(SemverOut.SEMVER_MAJOR, semver);
    }

    /** Seam: the failure carries a reason. Verifies: JAPI-ERR-001. */
    @Test
    void theFactoryAppliesItsArgumentsToTheMessageFormat() {
        JApiCompareException failure =
                JApiCompareException.of(JApiCompareException.Reason.IllegalArgument, "bad %s", "input");

        assertEquals(JApiCompareException.Reason.IllegalArgument, failure.getReason());
        assertEquals("bad input", failure.getMessage());
    }

    /** Seam: the cli-error shorthand. Verifies: JAPI-ERR-002. */
    @Test
    void theCliErrorFactoryUsesTheCliErrorReason() {
        JApiCompareException failure = JApiCompareException.cliError("cannot parse %s", "x#y#z");

        assertEquals(JApiCompareException.Reason.CliError, failure.getReason());
        assertTrue(failure.getMessage().contains("x#y#z"));
    }



}
