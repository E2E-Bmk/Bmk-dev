package atomic;

import static fixtures.Model.annoCountOnMethod;
import static fixtures.Model.annoOnMethod;
import static fixtures.Model.classAnnoMethod;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.elementNamed;
import static fixtures.Model.markerMethod;
import static fixtures.Model.methodNamed;
import static fixtures.Model.nestedAnnoMethod;
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

/** Single-owner checks over annotation members whose values are Class literals or nested annotations. */
class CompareTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";
    static final String N = "java.lang.annotation.Target";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }
    private static JApiMethod run(JApiClass c) { return methodNamed(c, "run"); }

    // ---- class member values ----
    @Test void classMemberChangeIsModified() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getChangeStatus());
    }
    @Test void classMemberUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String");
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getChangeStatus());
    }
    @Test void classMemberAddedIsNew() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String");
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getChangeStatus());
    }
    @Test void classMemberRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getChangeStatus());
    }
    @Test void aClassMemberChangeMakesTheAnnotationModified() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Object");
        assertEquals(JApiChangeStatus.MODIFIED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aClassMemberElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer");
        assertEquals("type", elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getName());
    }
    @Test void classMemberUnchangedLeavesMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer");
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aDifferentClassLiteralIsModified() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.util.List");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.util.Map");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getChangeStatus());
    }

    // ---- nested annotation member values ----
    @Test void nestedAnnotationValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getChangeStatus());
    }
    @Test void nestedAnnotationUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 5);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 5);
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getChangeStatus());
    }
    @Test void aNestedTypeSwapWithEqualMembersIsUnchanged() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", N, "count", 1);
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getChangeStatus());
    }
    @Test void nestedAnnotationMemberAddedIsNew() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 1);
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getChangeStatus());
    }
    @Test void nestedAnnotationMemberRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getChangeStatus());
    }
    @Test void aNestedAnnotationValueChangeMakesTheOuterModified() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 9);
        assertEquals(JApiChangeStatus.MODIFIED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aNestedAnnotationElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2);
        assertEquals("inner", elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getName());
    }
    @Test void nestedAnnotationUnchangedLeavesMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }

    // ---- string member (mixed with class/nested) ----
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

    // ---- annotation / method presence ----
    @Test void anAnnotationWithClassMemberReportsItsFqn() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer");
        assertEquals(D, annoOnMethod(run(onlyClass(compare(o, n))), D).getFullyQualifiedName());
    }
    @Test void anAddedAnnotationCarryingAClassMemberIsNew() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String");
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aRemovedAnnotationCarryingANestedMemberIsRemoved() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.REMOVED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void anUnchangedAnnotationWithClassMemberIsUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String");
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }
    @Test void oneAnnotationWithClassMemberCountsOne() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String");
        assertEquals(1, annoCountOnMethod(run(onlyClass(compare(o, n)))));
    }
    @Test void aMarkerHasNoElements() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(0, annoOnMethod(run(onlyClass(compare(o, n))), D).getElements().size());
    }

    // ---- multiple methods ----
    @Test void changingAClassOnOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnMethod(methodNamed(c, "run"), D), "type").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "stop")) == 0);
    }
    @Test void changingANestedOnOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnMethod(methodNamed(c, "run"), D), "inner").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "stop")) == 0);
    }

    // ---- multi-class ----
    @Test void aClassSetClassifiesClassMemberChanges() throws Exception {
        CtClass aO = k("a.A"); classAnnoMethod(aO, "public void run(){}", D, "type", "java.lang.String");
        CtClass aN = k("a.A"); classAnnoMethod(aN, "public void run(){}", D, "type", "java.lang.Integer");
        CtClass bO = k("a.B"); classAnnoMethod(bO, "public void run(){}", D, "type", "java.util.List");
        CtClass bN = k("a.B"); classAnnoMethod(bN, "public void run(){}", D, "type", "java.util.List");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.A"), "run"), D), "type").getChangeStatus() == JApiChangeStatus.MODIFIED
                && elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.B"), "run"), D), "type").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }
    @Test void twoClassesWithDistinctNestedChanges() throws Exception {
        CtClass aO = k("a.A"); nestedAnnoMethod(aO, "public void run(){}", D, "inner", I, "count", 1);
        CtClass aN = k("a.A"); nestedAnnoMethod(aN, "public void run(){}", D, "inner", I, "count", 2);
        CtClass bO = k("a.B"); nestedAnnoMethod(bO, "public void run(){}", D, "inner", I, "count", 8);
        CtClass bN = k("a.B"); markerMethod(bN, "public void run(){}", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.A"), "run"), D), "inner").getChangeStatus() == JApiChangeStatus.MODIFIED
                && elementNamed(annoOnMethod(methodNamed(classNamed(r, "a.B"), "run"), D), "inner").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // ---- new / deleted class ----
    @Test void aNewClassWithAClassAnnotatedMethodMarksTheMethodNew() throws Exception {
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String");
        assertEquals(JApiChangeStatus.NEW, run(onlyClass(compare(null, n))).getChangeStatus());
    }
    @Test void aDeletedClassWithANestedAnnotatedMethodMarksTheMethodRemoved() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1);
        assertEquals(JApiChangeStatus.REMOVED, run(onlyClass(compare(o, null))).getChangeStatus());
    }

    // ---- second annotation type ----
    @Test void aSecondAnnotationTypeWithClassMemberIsNew() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", I, "type", "java.lang.String");
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), I).getChangeStatus());
    }
    @Test void aClassMemberChangeOnASecondAnnotationType() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", I, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", I, "type", "java.lang.Integer");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), I), "type").getChangeStatus());
    }
    @Test void aClassMemberChangeToARelatedTypeIsModified() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.util.ArrayList");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.util.LinkedList");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "type").getChangeStatus());
    }
    @Test void aNestedMemberChangeToADifferentPrimitiveIsModified() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 0);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 100);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "inner").getChangeStatus());
    }
}
