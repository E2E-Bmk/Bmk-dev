package atomic;

import japicmp.exception.JApiCmpException;
import japicmp.filter.JavaDocLikeClassFilter;
import japicmp.filter.JavadocLikeFieldFilter;
import japicmp.versioning.SemanticVersion;
import japicmp.versioning.Version;
import japicmp.versioning.VersionChange;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Collections;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

class RewrittenUpstreamTest {
    private static SemanticVersion semver(String value) {
        return Version.getSemanticVersion(value).orElseThrow(AssertionError::new);
    }

    private static CtClass ctClass(String name) {
        return new ClassPool(true).makeClass(name);
    }

    /** Verifies: JCMP-SEM-001, JCMP-SEM-003. */
    @Test void testSingleDigitSemanticVersionFromString() {
        SemanticVersion value = semver("4.7.2");
        assertAll(() -> assertEquals(4, value.getMajor()), () -> assertEquals(7, value.getMinor()), () -> assertEquals(2, value.getPatch()));
    }

    /** Verifies: JCMP-SEM-001, JCMP-SEM-003. */
    @Test void testMultidigitSemanticVersionFromString() {
        SemanticVersion value = semver("17.204.39");
        assertAll(() -> assertEquals(17, value.getMajor()), () -> assertEquals(204, value.getMinor()), () -> assertEquals(39, value.getPatch()));
    }

    /** Verifies: JCMP-SEM-001, JCMP-SEM-003. */
    @Test void testEmbeddedSemanticVersionFromString() {
        SemanticVersion value = semver("release-v12.8.41-candidate");
        assertAll(() -> assertEquals(12, value.getMajor()), () -> assertEquals(8, value.getMinor()), () -> assertEquals(41, value.getPatch()));
    }

    /** Verifies: JCMP-SEM-004. */
    @Test void testOneVersionNoChange() {
        VersionChange value = new VersionChange(Collections.singletonList(new SemanticVersion(3, 8, 5)), Collections.singletonList(new SemanticVersion(3, 8, 5)), false, false);
        assertEquals(SemanticVersion.ChangeType.UNCHANGED, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-004, JCMP-SEM-005. */
    @Test void testOneVersionPatchChange() {
        VersionChange value = new VersionChange(Collections.singletonList(new SemanticVersion(3, 8, 5)), Collections.singletonList(new SemanticVersion(3, 8, 9)), false, false);
        assertEquals(SemanticVersion.ChangeType.PATCH, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-004, JCMP-SEM-005. */
    @Test void testOneVersionMinorChange() {
        VersionChange value = new VersionChange(Collections.singletonList(new SemanticVersion(3, 8, 5)), Collections.singletonList(new SemanticVersion(3, 11, 0)), false, false);
        assertEquals(SemanticVersion.ChangeType.MINOR, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-004, JCMP-SEM-005. */
    @Test void testOneVersionMajorChange() {
        VersionChange value = new VersionChange(Collections.singletonList(new SemanticVersion(3, 8, 5)), Collections.singletonList(new SemanticVersion(6, 0, 0)), false, false);
        assertEquals(SemanticVersion.ChangeType.MAJOR, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-005. */
    @Test void testTwoVersionsNoChange() {
        VersionChange value = new VersionChange(Arrays.asList(new SemanticVersion(7, 1, 4), new SemanticVersion(7, 1, 4)), Arrays.asList(new SemanticVersion(7, 1, 4), new SemanticVersion(7, 1, 4)), false, false);
        assertEquals(SemanticVersion.ChangeType.UNCHANGED, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-005. */
    @Test void testTwoVersionsPatchChange() {
        VersionChange value = new VersionChange(Arrays.asList(new SemanticVersion(7, 1, 4), new SemanticVersion(7, 1, 4)), Arrays.asList(new SemanticVersion(7, 1, 6), new SemanticVersion(7, 1, 6)), false, false);
        assertEquals(SemanticVersion.ChangeType.PATCH, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-005. */
    @Test void testTwoVersionsMinorChange() {
        VersionChange value = new VersionChange(Arrays.asList(new SemanticVersion(7, 1, 4), new SemanticVersion(7, 1, 4)), Arrays.asList(new SemanticVersion(7, 3, 0), new SemanticVersion(7, 3, 0)), false, false);
        assertEquals(SemanticVersion.ChangeType.MINOR, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-005. */
    @Test void testTwoVersionsMajorChange() {
        VersionChange value = new VersionChange(Arrays.asList(new SemanticVersion(7, 1, 4), new SemanticVersion(7, 1, 4)), Arrays.asList(new SemanticVersion(9, 0, 0), new SemanticVersion(9, 0, 0)), false, false);
        assertEquals(SemanticVersion.ChangeType.MAJOR, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-005. */
    @Test void testTwoVersionsMajorChangeNotAllVersionsTheSame() {
        VersionChange value = new VersionChange(Arrays.asList(new SemanticVersion(5, 2, 0), new SemanticVersion(5, 2, 0)), Arrays.asList(new SemanticVersion(5, 2, 0), new SemanticVersion(5, 9, 0)), false, false);
        assertEquals(SemanticVersion.ChangeType.MINOR, value.computeChangeType().orElseThrow(AssertionError::new));
    }

    /** Verifies: JCMP-SEM-006, JCMP-SEM-009. */
    @Test void testTwoVersionsMajorChangeNotAllVersionsTheSameAndDifferentNumberofArchives() {
        VersionChange value = new VersionChange(Arrays.asList(new SemanticVersion(2, 1, 0), new SemanticVersion(2, 1, 1)), Arrays.asList(new SemanticVersion(2, 1, 0), new SemanticVersion(2, 4, 0), new SemanticVersion(2, 7, 0)), false, false);
        assertEquals(JApiCmpException.Reason.IllegalArgument, assertThrows(JApiCmpException.class, value::computeChangeType).getReason());
    }

    /** Verifies: JCMP-SEM-006, JCMP-ERR-001. */
    @Test void testMissingOldVersion() {
        VersionChange value = new VersionChange(Collections.emptyList(), Collections.singletonList(new SemanticVersion(8, 3, 1)), false, false);
        assertEquals(JApiCmpException.Reason.IllegalArgument, assertThrows(JApiCmpException.class, value::computeChangeType).getReason());
    }

    /** Verifies: JCMP-SEM-006. */
    @Test void testIgnoreMissingOldVersion() {
        VersionChange value = new VersionChange(Collections.emptyList(), Collections.singletonList(new SemanticVersion(8, 3, 1)), true, false);
        assertEquals(Optional.empty(), value.computeChangeType());
    }

    /** Verifies: JCMP-SEM-006, JCMP-ERR-001. */
    @Test void testMissingNewVersion() {
        VersionChange value = new VersionChange(Collections.singletonList(new SemanticVersion(8, 3, 1)), Collections.emptyList(), false, false);
        assertEquals(JApiCmpException.Reason.IllegalArgument, assertThrows(JApiCmpException.class, value::computeChangeType).getReason());
    }

    /** Verifies: JCMP-SEM-006. */
    @Test void testIgnoreMissingNewVersion() {
        VersionChange value = new VersionChange(Collections.singletonList(new SemanticVersion(8, 3, 1)), Collections.emptyList(), false, true);
        assertEquals(Optional.empty(), value.computeChangeType());
    }

    /** Verifies: JCMP-SEM-006, JCMP-ERR-001. */
    @Test void testNoParameter() {
        VersionChange value = new VersionChange(Collections.emptyList(), Collections.emptyList(), false, false);
        assertEquals(JApiCmpException.Reason.IllegalArgument, assertThrows(JApiCmpException.class, value::computeChangeType).getReason());
    }

    /** Verifies: JCMP-FILT-004. */
    @Test void testOneClassMatches() {
        assertTrue(new JavaDocLikeClassFilter("sample.api.Widget").matches(ctClass("sample.api.Widget")));
    }

    /** Verifies: JCMP-FILT-004. */
    @Test void testOneClassMatchesNot() {
        assertFalse(new JavaDocLikeClassFilter("sample.api.Widget").matches(ctClass("sample.api.Gadget")));
    }

    /** Verifies: JCMP-FILT-004. */
    @Test void testInnerClass() {
        assertTrue(new JavaDocLikeClassFilter("sample.api.Widget").matches(ctClass("sample.api.Widget$Part")));
    }

    /** Verifies: JCMP-FILT-004. */
    @Test void testInnerClassAsFilter() {
        assertTrue(new JavaDocLikeClassFilter("sample.api.Widget$Part").matches(ctClass("sample.api.Widget$Part")));
    }

    /** Verifies: JCMP-FILT-008. */
    @Test void testOneFieldMatches() throws Exception {
        CtClass owner = ctClass("sample.api.Record");
        CtField field = new CtField(CtClass.longType, "sequence", owner);
        owner.addField(field);
        assertTrue(new JavadocLikeFieldFilter("sample.api.Record#sequence").matches(field));
    }

    /** Verifies: JCMP-FILT-008. */
    @Test void testOneFieldMatchesNot() throws Exception {
        CtClass owner = ctClass("sample.api.Record");
        CtField field = new CtField(CtClass.longType, "sequence", owner);
        owner.addField(field);
        assertFalse(new JavadocLikeFieldFilter("sample.api.Record#revision").matches(field));
    }

    /** Verifies: JCMP-FILT-009, JCMP-ERR-004. */
    @Test void testTwoHashSigns() {
        JApiCmpException error = assertThrows(JApiCmpException.class, () -> new JavadocLikeFieldFilter("sample.api.Record##sequence"));
        assertEquals(JApiCmpException.Reason.CliError, error.getReason());
    }
}
