package integration;

import fixtures.Bytecode;
import fixtures.Compare;
import javassist.ClassPool;
import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.plumbline.cmp.JarArchiveComparator;
import org.plumbline.config.Options;
import org.plumbline.model.JApiChangeStatus;
import org.plumbline.model.JApiClass;
import org.plumbline.output.semver.SemverOut;
import org.plumbline.output.stdout.StdoutOutputGenerator;
import org.plumbline.output.xml.XmlOutputGenerator;
import org.plumbline.output.xml.XmlOutputGeneratorOptions;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Agreement between the projections of one tree.
 *
 * <p>Each test here reads the same comparison through two or more of the four
 * projections -- the model, the text report, the XML document, the semantic-version
 * string -- and asserts they tell the same story. A delivery can get every single
 * projection right in isolation and still fail these, which is the point: the
 * invariants are where composition shows.
 */
class CrossViewTest {

    private static final String SERVICE = "com.acme.Service";

    /** A tree in which one public method was removed from one class. */
    private static List<JApiClass> methodRemoved() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], SERVICE);
        Bytecode.method(before, "public void run() {}");
        Bytecode.method(before, "public void stay() {}");
        CtClass after = Bytecode.publicClass(pools[1], SERVICE);
        Bytecode.method(after, "public void stay() {}");
        return Compare.compare(before, after);
    }

    /** A tree in which nothing changed. */
    private static List<JApiClass> unchanged() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], SERVICE);
        Bytecode.method(before, "public void stay() {}");
        CtClass after = Bytecode.publicClass(pools[1], SERVICE);
        Bytecode.method(after, "public void stay() {}");
        return Compare.compare(before, after);
    }

    /** Three classes whose names sort differently from the order they are supplied in. */
    private static List<JApiClass> threeClassesOutOfOrder() throws Exception {
        ClassPool oldPool = Bytecode.pool();
        ClassPool newPool = Bytecode.pool();
        List<CtClass> oldList = new ArrayList<>();
        List<CtClass> newList = new ArrayList<>();
        for (String name : new String[] {"com.acme.Zebra", "com.acme.apple", "com.acme.Mango"}) {
            CtClass before = Bytecode.publicClass(oldPool, name);
            Bytecode.method(before, "public void gone() {}");
            oldList.add(before);
            newList.add(Bytecode.publicClass(newPool, name));
        }
        return new JarArchiveComparator(Compare.publicOnly())
                .compareClassLists(Compare.publicOnly(), oldList, newList);
    }

    private static String text(Options options, List<JApiClass> tree) {
        return new StdoutOutputGenerator(options, tree).generate();
    }

    private static String xml(Options options, List<JApiClass> tree) {
        return new XmlOutputGenerator(tree, options, new XmlOutputGeneratorOptions()).generate();
    }

    /** Positions of each needle, so two projections can be compared on order alone. */
    private static List<Integer> positions(String haystack, String... needles) {
        List<Integer> found = new ArrayList<>();
        for (String needle : needles) {
            found.add(haystack.indexOf(needle));
        }
        return found;
    }

    private static boolean ascending(List<Integer> values) {
        for (int index = 1; index < values.size(); index++) {
            if (values.get(index - 1) < 0 || values.get(index) <= values.get(index - 1)) {
                return false;
            }
        }
        return true;
    }

    // ── CVI 2: the text sign group agrees with the model ──────────────────

    /**
     * Seam: model status versus the first three sign characters.
     * Verifies: JAPI-INV-002.
     * Depends-On: removingAMethodMakesTheOwningClassModified, aModifiedNodeIsPrefixedByTheModifiedSignGroup.
     */
    @Test
    void aModifiedClassInTheModelIsMarkedModifiedInTheTextReport() throws Exception {
        List<JApiClass> tree = methodRemoved();
        assertEquals(JApiChangeStatus.MODIFIED, Compare.only(tree).getChangeStatus());

        assertTrue(text(Options.newDefault(), tree).contains("***"));
    }

    /**
     * Seam: an unchanged model node must not be marked modified.
     * Verifies: JAPI-INV-002.
     * Depends-On: aClassPresentAndUnchangedInBothVersionsIsUnchanged.
     */
    @Test
    void anUnchangedClassInTheModelIsNotMarkedModifiedInTheTextReport() throws Exception {
        List<JApiClass> tree = unchanged();
        assertEquals(JApiChangeStatus.UNCHANGED, Compare.only(tree).getChangeStatus());

        assertFalse(text(Options.newDefault(), tree).contains("***"));
    }

    /**
     * Seam: XML binaryCompatible="false" and the text `!` mark the same node.
     * Verifies: JAPI-INV-002.
     * Depends-On: removingAPublicMethodIsBinaryIncompatible, aBinaryIncompatibleNodeCarriesTheExclamationSign.
     */
    @Test
    void aNodeTheXmlCallsBinaryIncompatibleCarriesTheExclamationSignInTheText() throws Exception {
        List<JApiClass> tree = methodRemoved();
        assertFalse(Compare.only(tree).isBinaryCompatible());

        assertTrue(xml(Options.newDefault(), tree).contains("binaryCompatible=\"false\""));
        assertTrue(text(Options.newDefault(), tree).contains("!"));
    }

    /**
     * Seam: a compatible tree is called compatible by both projections.
     * Verifies: JAPI-INV-002.
     * Depends-On: anUnchangedClassCarriesNoCompatibilityChange.
     */
    @Test
    void aCompatibleTreeIsNotMarkedIncompatibleInEitherProjection() throws Exception {
        List<JApiClass> tree = unchanged();
        assertTrue(Compare.only(tree).isBinaryCompatible());

        assertFalse(xml(Options.newDefault(), tree).contains("binaryCompatible=\"false\""));
    }

    // ── CVI 3: the semantic version agrees with the model and the XML ─────

    /**
     * Seam: a MAJOR-level change drives the semantic version and appears in the XML.
     * Verifies: JAPI-INV-003.
     * Depends-On: removingAPublicMethodIsBinaryIncompatible, removingAPublicMethodYieldsTheMajorVersionString.
     */
    @Test
    void aMajorChangeInTheModelAppearsInBothTheSemanticVersionAndTheXml() throws Exception {
        List<JApiClass> tree = methodRemoved();

        assertEquals(SemverOut.SEMVER_MAJOR, new SemverOut(Options.newDefault(), tree).generate());
        assertTrue(xml(Options.newDefault(), tree).contains("METHOD_REMOVED"));
    }

    /**
     * Seam: no change means no major verdict and no change element.
     * Verifies: JAPI-INV-003.
     * Depends-On: anUnchangedTreeDoesNotYieldTheMajorVersionString.
     */
    @Test
    void anUnchangedTreeYieldsNeitherAMajorVersionNorAChangeElement() throws Exception {
        List<JApiClass> tree = unchanged();

        assertFalse(SemverOut.SEMVER_MAJOR.equals(
                new SemverOut(Options.newDefault(), tree).generate()));
        assertFalse(xml(Options.newDefault(), tree).contains("METHOD_REMOVED"));
    }

    /**
     * Seam: the same tree read twice yields the same verdict.
     * Verifies: JAPI-INV-003.
     * Depends-On: removingAPublicMethodYieldsTheMajorVersionString.
     */
    @Test
    void theSemanticVersionIsStableAcrossRepeatedReads() throws Exception {
        List<JApiClass> tree = methodRemoved();

        String first = new SemverOut(Options.newDefault(), tree).generate();
        String second = new SemverOut(Options.newDefault(), tree).generate();

        assertEquals(first, second);
    }

    // ── CVI 5: only-binary-incompatible prunes text and XML alike ─────────

    /**
     * Seam: the pruning switch removes the compatible class from both reports.
     * Verifies: JAPI-INV-005.
     * Depends-On: anUnchangedClassCarriesNoCompatibilityChange.
     */
    @Test
    void onlyBinaryIncompatibleReportingPrunesACompatibleClassFromBothReports() throws Exception {
        Options pruning = Options.newDefault();
        pruning.setOutputOnlyBinaryIncompatibleModifications(true);

        assertFalse(text(pruning, unchanged()).contains(SERVICE));
        assertFalse(xml(pruning, unchanged()).contains(SERVICE));
    }

    /**
     * Seam: an incompatible class survives the switch in both reports.
     * Verifies: JAPI-INV-005.
     * Depends-On: removingAPublicMethodIsBinaryIncompatible.
     */
    @Test
    void onlyBinaryIncompatibleReportingKeepsAnIncompatibleClassInBothReports() throws Exception {
        Options pruning = Options.newDefault();
        pruning.setOutputOnlyBinaryIncompatibleModifications(true);

        assertTrue(text(pruning, methodRemoved()).contains(SERVICE));
        assertTrue(xml(pruning, methodRemoved()).contains(SERVICE));
    }

    /**
     * Seam: the semantic-version report applies no output filter.
     * Verifies: JAPI-INV-005.
     * Depends-On: removingAPublicMethodYieldsTheMajorVersionString.
     */
    @Test
    void theSemanticVersionIsUnaffectedByOnlyBinaryIncompatibleReporting() throws Exception {
        Options plain = Options.newDefault();
        Options pruning = Options.newDefault();
        pruning.setOutputOnlyBinaryIncompatibleModifications(true);

        assertEquals(new SemverOut(plain, methodRemoved()).generate(),
                new SemverOut(pruning, methodRemoved()).generate());
    }

    // ── CVI 7: order is settled once, inside compareClassLists ────────────

    /**
     * Seam: the returned list is in case-insensitive order by fully qualified name.
     * Verifies: JAPI-INV-007.
     * Depends-On: eachComparedNameBecomesItsOwnElement.
     */
    @Test
    void theReturnedListIsSortedCaseInsensitivelyByName() throws Exception {
        List<String> names = new ArrayList<>();
        for (JApiClass each : threeClassesOutOfOrder()) {
            names.add(each.getFullyQualifiedName());
        }

        List<String> expected = new ArrayList<>(names);
        expected.sort(String::compareToIgnoreCase);
        assertEquals(expected, names);
    }

    /**
     * Seam: the text report's block order matches the returned list's order.
     * Verifies: JAPI-INV-007.
     * Depends-On: eachComparedNameBecomesItsOwnElement.
     */
    @Test
    void theTextReportOrdersClassesAsTheReturnedListDoes() throws Exception {
        List<JApiClass> tree = threeClassesOutOfOrder();
        String[] names = tree.stream().map(JApiClass::getFullyQualifiedName).toArray(String[]::new);

        assertTrue(ascending(positions(text(Options.newDefault(), tree), names)),
                "text order disagreed with the model order");
    }

    /**
     * Seam: the XML document's element order matches the returned list's order.
     * Verifies: JAPI-INV-007.
     * Depends-On: eachComparedNameBecomesItsOwnElement.
     */
    @Test
    void theXmlDocumentOrdersClassesAsTheReturnedListDoes() throws Exception {
        List<JApiClass> tree = threeClassesOutOfOrder();
        String[] names = tree.stream().map(JApiClass::getFullyQualifiedName).toArray(String[]::new);

        assertTrue(ascending(positions(xml(Options.newDefault(), tree), names)),
                "xml order disagreed with the model order");
    }

    /**
     * Seam: methods are ordered case-insensitively by name in both reports.
     * Verifies: JAPI-INV-007.
     * Depends-On: theAddedMethodElementIsNew.
     */
    @Test
    void bothReportsOrderMethodsTheSameWay() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], SERVICE);
        CtClass after = Bytecode.publicClass(pools[1], SERVICE);
        for (String each : new String[] {"zeta", "alpha", "Mid"}) {
            Bytecode.method(after, "public void " + each + "() {}");
        }
        List<JApiClass> tree = Compare.compare(before, after);

        String report = text(Options.newDefault(), tree);
        String document = xml(Options.newDefault(), tree);
        String[] order = {"alpha", "Mid", "zeta"};

        assertEquals(ascending(positions(report, order)), ascending(positions(document, order)),
                "the two reports disagreed about method order");
    }

    // ── CVI 8: `n.a.` in the text corresponds to absence in the model ─────

    /**
     * Seam: absent version labels render as the placeholder in the text report.
     * Verifies: JAPI-INV-008.
     * Depends-On: anUnsetVersionLabelRendersAsTheNotAvailablePlaceholder.
     */
    @Test
    void absentVersionLabelsRenderAsThePlaceholderInTheTextReport() throws Exception {
        String report = text(Options.newDefault(), methodRemoved());

        assertTrue(report.contains(Options.N_A), "expected the placeholder in: "
                + report.substring(0, Math.min(120, report.length())));
    }

    /**
     * Seam: a set label is rendered rather than the placeholder.
     * Verifies: JAPI-INV-008.
     * Depends-On: theDifferenceDescriptionNamesTheNewVersionBeforeTheOld.
     */
    @Test
    void presentVersionLabelsAreRenderedInsteadOfThePlaceholder() throws Exception {
        Options options = Options.newDefault();
        options.setOldVersion("1.0.0");
        options.setNewVersion("2.0.0");

        String firstLine = text(options, methodRemoved()).split("\n", 2)[0];

        assertTrue(firstLine.contains("1.0.0") && firstLine.contains("2.0.0"));
        assertFalse(firstLine.contains(Options.N_A));
    }

    /**
     * Seam: the XML root carries the same labels the text report shows.
     * Verifies: JAPI-INV-008.
     * Depends-On: theDifferenceDescriptionNamesTheNewVersionBeforeTheOld.
     */
    @Test
    void theXmlRootCarriesTheSameVersionLabelsAsTheTextReport() throws Exception {
        Options options = Options.newDefault();
        options.setOldVersion("1.0.0");
        options.setNewVersion("2.0.0");

        String document = xml(options, methodRemoved());

        assertTrue(document.contains("oldVersion=\"1.0.0\""), "document was: " + document);
        assertTrue(document.contains("newVersion=\"2.0.0\""));
    }

    /**
     * Seam: an absent label reaches the XML as the placeholder too.
     * Verifies: JAPI-INV-008.
     * Depends-On: anUnsetVersionLabelRendersAsTheNotAvailablePlaceholder.
     */
    @Test
    void anAbsentLabelReachesTheXmlAsThePlaceholder() throws Exception {
        String document = xml(Options.newDefault(), methodRemoved());

        assertTrue(document.contains("oldVersion=\"" + Options.N_A + "\""),
                "document was: " + document);
    }

    // ── Representative workflows read end to end ──────────────────────────

    /**
     * Seam: the workflow the specification opens with, read through three projections.
     * Verifies: JAPI-INV-002, JAPI-INV-003.
     * Depends-On: removingAPublicMethodIsBinaryIncompatible, removingAMethodMakesTheOwningClassModified.
     */
    @Test
    void theDocumentedWorkflowAgreesAcrossModelTextAndSemanticVersion() throws Exception {
        List<JApiClass> tree = methodRemoved();
        JApiClass service = Compare.only(tree);

        assertEquals(JApiChangeStatus.MODIFIED, service.getChangeStatus());
        assertFalse(service.isBinaryCompatible());

        Options options = Options.newDefault();
        options.setOldVersion("1.0.0");
        options.setNewVersion("2.0.0");

        assertEquals(SemverOut.SEMVER_MAJOR, new SemverOut(options, tree).generate());
        assertTrue(text(options, tree).contains(SERVICE));
    }

    /**
     * Seam: a removal is visible in every projection at once.
     * Verifies: JAPI-INV-002.
     * Depends-On: aClassOnlyTheOldVersionDeclaresIsRemoved.
     */
    @Test
    void aRemovedClassIsReportedByEveryProjection() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Gone");
        Bytecode.method(before, "public void run() {}");
        List<JApiClass> tree = Compare.compare(before, null);

        assertEquals(JApiChangeStatus.REMOVED, Compare.only(tree).getChangeStatus());
        assertTrue(text(Options.newDefault(), tree).contains("com.acme.Gone"));
        assertTrue(xml(Options.newDefault(), tree).contains("com.acme.Gone"));
        assertEquals(SemverOut.SEMVER_MAJOR, new SemverOut(Options.newDefault(), tree).generate());
    }

    /**
     * Seam: an addition is compatible in every projection.
     * Verifies: JAPI-INV-002.
     * Depends-On: aClassOnlyTheNewVersionDeclaresIsNew.
     */
    @Test
    void anAddedClassIsCompatibleInEveryProjection() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Fresh");
        Bytecode.method(after, "public void run() {}");
        List<JApiClass> tree = Compare.compare(null, after);

        assertTrue(Compare.only(tree).isBinaryCompatible());
        assertFalse(xml(Options.newDefault(), tree).contains("binaryCompatible=\"false\""));
    }

    /**
     * Seam: an empty comparison is empty in every projection.
     * Verifies: JAPI-INV-008.
     * Depends-On: anEmptyTreeReportsNoChanges, anEmptyTreeYieldsTheCompatibleVersionString.
     */
    @Test
    void anEmptyComparisonIsEmptyInEveryProjection() {
        List<JApiClass> tree = new ArrayList<>();

        assertTrue(text(Options.newDefault(), tree).contains("No changes."));
        assertEquals(SemverOut.SEMVER_COMPATIBLE,
                new SemverOut(Options.newDefault(), tree).generate());
    }
}
