package atomic;

import static fixtures.Model.annoCountOnMethod;
import static fixtures.Model.annoOnMethod;
import static fixtures.Model.arrayAnnoMethod;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.elementNamed;
import static fixtures.Model.enumAnnoMethod;
import static fixtures.Model.markerMethod;
import static fixtures.Model.methodNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.plainMethod;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.stringAnnoMethod;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;
import org.markline.model.JApiMethod;

/** Single-owner checks over annotation members whose values are enum constants or arrays. */
class CompareTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";
    static final String E = "java.lang.annotation.RetentionPolicy";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }
    private static JApiMethod run(JApiClass c) { return methodNamed(c, "run"); }

    // ---- enum member values ----
    @Test void enumMemberChangeIsModified() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "policy").getChangeStatus());
    }
    @Test void enumMemberUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "policy").getChangeStatus());
    }
    @Test void anEnumMemberChangeMakesTheAnnotationModified() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "CLASS");
        assertEquals(JApiChangeStatus.MODIFIED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void anEnumMemberElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE");
        assertEquals("policy", elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "policy").getName());
    }
    @Test void enumMemberAddedIsNew() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "policy").getChangeStatus());
    }
    @Test void enumMemberRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "policy").getChangeStatus());
    }
    @Test void aThirdEnumConstantChangeIsModified() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "CLASS");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "policy").getChangeStatus());
    }
    @Test void enumMemberUnchangedLeavesMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE");
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }

    // ---- array member values ----
    @Test void arrayMemberChangeIsModified() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1, 3);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getChangeStatus());
    }
    @Test void arrayMemberUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1, 2);
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getChangeStatus());
    }
    @Test void arrayMemberLengthChangeIsModified() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1, 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getChangeStatus());
    }
    @Test void anArrayMemberChangeMakesTheAnnotationModified() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 4, 5);
        assertEquals(JApiChangeStatus.MODIFIED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void arrayMemberAddedIsNew() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1, 2);
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getChangeStatus());
    }
    @Test void arrayMemberRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getChangeStatus());
    }
    @Test void anEmptyArrayVsNonEmptyIsModified() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getChangeStatus());
    }
    @Test void anArrayMemberElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 2);
        assertEquals("ids", elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "ids").getName());
    }
    @Test void arrayMemberUnchangedLeavesMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1, 9);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }

    // ---- string member values ----
    @Test void stringMemberChangeIsModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "y");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void stringMemberUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "same");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "same");
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void stringMemberAddedIsNew() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "x");
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void stringMemberRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }

    // ---- annotation / method presence ----
    @Test void anAnnotationWithEnumMemberReportsItsFqn() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE");
        assertEquals(D, annoOnMethod(run(onlyClass(compare(o, n))), D).getFullyQualifiedName());
    }
    @Test void anAddedAnnotationCarryingAnEnumMemberIsNew() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aRemovedAnnotationCarryingAnArrayMemberIsRemoved() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.REMOVED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void anUnchangedAnnotationWithEnumMemberIsUnchanged() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }
    @Test void oneAnnotationWithMemberCountsOne() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(1, annoCountOnMethod(run(onlyClass(compare(o, n)))));
    }
    @Test void aMarkerHasNoElements() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(0, annoOnMethod(run(onlyClass(compare(o, n))), D).getElements().size());
    }

    // ---- multiple methods ----
    @Test void changingAnEnumOnOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnMethod(methodNamed(c, "run"), D), "policy").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "stop")) == 0);
    }
    @Test void changingAnArrayOnOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 2); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnMethod(methodNamed(c, "run"), D), "ids").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "stop")) == 0);
    }

    // ---- multi-class ----
    @Test void aClassSetClassifiesEnumChanges() throws Exception {
        CtClass aO = k("a.A"); enumAnnoMethod(aO, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass aN = k("a.A"); enumAnnoMethod(aN, "public void run(){}", D, "policy", E, "SOURCE");
        CtClass bO = k("a.B"); enumAnnoMethod(bO, "public void run(){}", D, "policy", E, "CLASS");
        CtClass bN = k("a.B"); enumAnnoMethod(bN, "public void run(){}", D, "policy", E, "CLASS");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.A"), "run"), D), "policy").getChangeStatus() == JApiChangeStatus.MODIFIED
                && elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.B"), "run"), D), "policy").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }
    @Test void twoClassesWithDistinctArrayChanges() throws Exception {
        CtClass aO = k("a.A"); arrayAnnoMethod(aO, "public void run(){}", D, "ids", 1);
        CtClass aN = k("a.A"); arrayAnnoMethod(aN, "public void run(){}", D, "ids", 2);
        CtClass bO = k("a.B"); arrayAnnoMethod(bO, "public void run(){}", D, "ids", 7, 8);
        CtClass bN = k("a.B"); arrayAnnoMethod(bN, "public void run(){}", D, "ids", 7, 8);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.A"), "run"), D), "ids").getChangeStatus() == JApiChangeStatus.MODIFIED
                && elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.B"), "run"), D), "ids").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // ---- new / deleted class ----
    @Test void aNewClassWithAnEnumAnnotatedMethodMarksTheMethodNew() throws Exception {
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME");
        assertEquals(JApiChangeStatus.NEW, run(onlyClass(compare(null, n))).getChangeStatus());
    }
    @Test void aDeletedClassWithAnArrayAnnotatedMethodMarksTheMethodRemoved() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2);
        assertEquals(JApiChangeStatus.REMOVED, run(onlyClass(compare(o, null))).getChangeStatus());
    }

    // ---- second annotation type ----
    @Test void aSecondAnnotationTypeWithArrayMemberIsNew() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", I, "ids", 1);
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), I).getChangeStatus());
    }
    @Test void anEnumMemberChangeOnASecondAnnotationType() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", I, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", I, "policy", E, "SOURCE");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), I), "policy").getChangeStatus());
    }
}
