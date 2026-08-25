package integration;

import fixtures.Bytecode;
import fixtures.Compare;
import javassist.ClassPool;
import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.plumbline.cmp.JarArchiveComparator;
import org.plumbline.config.Options;
import org.plumbline.model.AccessModifier;
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
 * Further agreement checks between projections, covering the option surface that
 * changes what each projection shows.
 *
 * <p>Split from {@link CrossViewTest} to keep one file per invariant family rather
 * than one file per test count.
 */
class OptionAgreementTest {

    private static final String CHANGED = "com.acme.Changed";
    private static final String STABLE = "com.acme.Stable";

    /** One class that changed and one that did not, in the same comparison. */
    private static List<JApiClass> mixedTree() throws Exception {
        ClassPool oldPool = Bytecode.pool();
        ClassPool newPool = Bytecode.pool();

        CtClass changedOld = Bytecode.publicClass(oldPool, CHANGED);
        Bytecode.method(changedOld, "public void gone() {}");
        CtClass changedNew = Bytecode.publicClass(newPool, CHANGED);

        CtClass stableOld = Bytecode.publicClass(oldPool, STABLE);
        Bytecode.method(stableOld, "public void stay() {}");
        CtClass stableNew = Bytecode.publicClass(newPool, STABLE);
        Bytecode.method(stableNew, "public void stay() {}");

        return new JarArchiveComparator(Compare.publicOnly()).compareClassLists(
                Compare.publicOnly(),
                List.of(changedOld, stableOld), List.of(changedNew, stableNew));
    }

    private static String text(Options options, List<JApiClass> tree) {
        return new StdoutOutputGenerator(options, tree).generate();
    }

    private static String xml(Options options, List<JApiClass> tree) {
        return new XmlOutputGenerator(tree, options, new XmlOutputGeneratorOptions()).generate();
    }

    /**
     * Seam: a field removal reaches the model, the text report and the XML alike.
     * Verifies: JAPI-INV-002.
     * Depends-On: removingAPublicFieldIsBinaryIncompatible, aRemovedFieldElementIsRemoved.
     */
    @Test
    void aRemovedFieldIsReportedIncompatibleByEveryProjection() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Holder");
        Bytecode.field(before, "public int count;");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Holder");
        List<JApiClass> tree = Compare.compare(before, after);

        assertFalse(Compare.only(tree).isBinaryCompatible());
        assertTrue(xml(Options.newDefault(), tree).contains("FIELD_REMOVED"));
        assertTrue(text(Options.newDefault(), tree).contains("!"));
        assertEquals(SemverOut.SEMVER_MAJOR, new SemverOut(Options.newDefault(), tree).generate());
    }

    /**
     * Seam: only-binary-incompatible reporting prunes the same class from both reports
     * while leaving the other in both.
     * Verifies: JAPI-INV-005.
     * Depends-On: removingAPublicMethodIsBinaryIncompatible, anUnchangedClassCarriesNoCompatibilityChange.
     */
    @Test
    void theSameClassSurvivesPruningInBothReportsAndTheOtherIsDroppedFromBoth() throws Exception {
        Options pruning = Options.newDefault();
        pruning.setOutputOnlyBinaryIncompatibleModifications(true);

        String report = text(pruning, mixedTree());
        String document = xml(pruning, mixedTree());

        assertTrue(report.contains(CHANGED));
        assertTrue(document.contains(CHANGED));
        assertFalse(report.contains(STABLE));
        assertFalse(document.contains(STABLE));
    }

    /**
     * Seam: only-modifications reporting prunes identically in both reports.
     * Verifies: JAPI-INV-005.
     * Depends-On: anUnchangedClassCarriesNoCompatibilityChange.
     */
    @Test
    void onlyModificationsReportingPrunesTheUnchangedClassFromBothReports() throws Exception {
        Options pruning = Options.newDefault();
        pruning.setOutputOnlyModifications(true);

        assertEquals(text(pruning, mixedTree()).contains(STABLE),
                xml(pruning, mixedTree()).contains(STABLE),
                "the two reports disagreed about pruning the unchanged class");
    }

    /**
     * Seam: the configured access level reaches the XML root attribute.
     * Verifies: JAPI-INV-008.
     * Depends-On: anUnsetVersionLabelRendersAsTheNotAvailablePlaceholder.
     */
    @Test
    void theXmlRootReportsTheConfiguredAccessLevel() throws Exception {
        Options options = Options.newDefault();
        options.setAccessModifier(AccessModifier.PUBLIC);

        assertTrue(xml(options, mixedTree()).contains("accessModifier=\"PUBLIC\""),
                "expected the configured level in the root attributes");
    }

    /**
     * Seam: the reporting-mode switch reaches the XML root attribute and the first
     * text line together.
     * Verifies: JAPI-INV-005.
     * Depends-On: onlyBinaryIncompatibleReportingDescribesBinaryCompatibility.
     */
    @Test
    void theReportingModeReachesBothTheXmlRootAndTheFirstTextLine() throws Exception {
        Options pruning = Options.newDefault();
        pruning.setOutputOnlyBinaryIncompatibleModifications(true);

        assertTrue(xml(pruning, mixedTree())
                .contains("onlyBinaryIncompatibleModifications=\"true\""));
        assertTrue(text(pruning, mixedTree()).split("\n", 2)[0].contains("binary"));
    }

    /**
     * Seam: tree order survives pruning in both reports.
     * Verifies: JAPI-INV-007.
     * Depends-On: eachComparedNameBecomesItsOwnElement.
     */
    @Test
    void treeOrderIsPreservedInBothReports() throws Exception {
        List<JApiClass> tree = mixedTree();
        List<String> names = new ArrayList<>();
        for (JApiClass each : tree) {
            names.add(each.getFullyQualifiedName());
        }
        List<String> expected = new ArrayList<>(names);
        expected.sort(String::compareToIgnoreCase);
        assertEquals(expected, names);

        String report = text(Options.newDefault(), tree);
        String document = xml(Options.newDefault(), tree);
        assertTrue(report.indexOf(names.get(0)) < report.indexOf(names.get(1)));
        assertTrue(document.indexOf(names.get(0)) < document.indexOf(names.get(1)));
    }

    /**
     * Seam: the emitted document must not disclose the upstream project name.
     * Verifies: JAPI-INV-008.
     * Depends-On: anEmptyTreeReportsNoChanges.
     */
    @Test
    void theEmittedDocumentNamesTheSpecifiedRootElement() throws Exception {
        String document = xml(Options.newDefault(), mixedTree());

        assertTrue(document.contains("<plumbline"),
                "expected the documented root element, document began: "
                        + document.substring(0, Math.min(200, document.length())));
    }

    /**
     * Seam: an unchanged class is compatible in the model and in both reports.
     * Verifies: JAPI-INV-002.
     * Depends-On: aClassPresentAndUnchangedInBothVersionsIsUnchanged.
     */
    @Test
    void theUnchangedClassIsCompatibleInTheModelAndBothReports() throws Exception {
        List<JApiClass> tree = mixedTree();
        JApiClass stable = Compare.named(tree, STABLE);

        assertEquals(JApiChangeStatus.UNCHANGED, stable.getChangeStatus());
        assertTrue(stable.isBinaryCompatible());

        String document = xml(Options.newDefault(), tree);
        int stableAt = document.indexOf(STABLE);
        assertTrue(stableAt >= 0);
        assertFalse(document.substring(stableAt, Math.min(stableAt + 200, document.length()))
                .contains("binaryCompatible=\"false\""));
    }
}
