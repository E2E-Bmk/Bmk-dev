package atomic;

import static fixtures.Model.annoCountOnMethod;
import static fixtures.Model.annoOnMethod;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.elementNamed;
import static fixtures.Model.intAnnoMethod;
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

/** Single-owner checks over annotations carried by methods. */
class CompareTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiMethod run(JApiClass c) { return methodNamed(c, "run"); }

    // ---- method annotation presence ----
    @Test void addedMethodAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void removedMethodAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.REMOVED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void unchangedMethodAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void addingAMethodAnnotationLeavesTheMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aMethodAnnotationReportsItsFullyQualifiedName() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(D, annoOnMethod(run(onlyClass(compare(o, n))), D).getFullyQualifiedName());
    }
    @Test void oneAddedMethodAnnotationCountsOne() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(1, annoCountOnMethod(run(onlyClass(compare(o, n)))));
    }

    // ---- element values on a method annotation ----
    @Test void methodAnnotationIntValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void methodAnnotationIntValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 5);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 5);
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void methodAnnotationStringValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "y");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void methodAnnotationStringValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "same");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "same");
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void aMethodAnnotationValueChangeMakesTheAnnotationModified() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aMethodAnnotationValueChangeLeavesTheMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aMethodAnnotationElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "size", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "size", 2);
        assertEquals("size", elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "size").getName());
    }
    @Test void aSecondMemberValueChangeOnAMethodAnnotation() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "level", 3);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "level", 4);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "level").getChangeStatus());
    }

    // ---- annotated-method presence ----
    @Test void anAnnotatedMethodAddedIsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.NEW, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anAnnotatedMethodRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anUnchangedAnnotatedMethodIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aPlainMethodPresentOnBothSidesIsUnchanged() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anAddedAnnotatedMethodCarriesItsAnnotationAsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }

    // ---- multiple methods ----
    @Test void addingAnAnnotationToOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnMethod(methodNamed(c, "run"), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoCountOnMethod(methodNamed(c, "stop")) == 0);
    }
    @Test void changingAMemberOnOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 9); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnMethod(methodNamed(c, "run"), D), "count").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "stop")) == 0);
    }

    // ---- multi-class ----
    @Test void aClassSetClassifiesEachMethodAnnotationChange() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); markerMethod(aN, "public void run(){}", D);
        CtClass bO = k("a.B"); markerMethod(bO, "public void run(){}", D);
        CtClass bN = k("a.B"); markerMethod(bN, "public void run(){}", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoOnMethod(methodNamed(classNamed(r, "a.A"), "run"), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoOnMethod(methodNamed(classNamed(r, "a.B"), "run"), D).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }
    @Test void twoClassesWithDistinctMethodAnnotationChanges() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); markerMethod(aN, "public void run(){}", D);
        CtClass bO = k("a.B"); markerMethod(bO, "public void run(){}", D);
        CtClass bN = k("a.B"); plainMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoOnMethod(methodNamed(classNamed(r, "a.A"), "run"), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoOnMethod(methodNamed(classNamed(r, "a.B"), "run"), D).getChangeStatus() == JApiChangeStatus.REMOVED);
    }
    @Test void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }

    // ---- second annotation type / string ----
    @Test void aSecondAnnotationTypeOnAMethodIsNew() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", I);
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(run(onlyClass(compare(o, n))), I).getChangeStatus());
    }
    @Test void aStringMemberAddedOnAMethodAnnotation() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "x");
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void aStringMemberRemovedOnAMethodAnnotation() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void anIntMemberAddedOnAMethodAnnotation() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 1);
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void anIntMemberRemovedOnAMethodAnnotation() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void aMarkerMethodAnnotationHasNoElements() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(0, annoOnMethod(run(onlyClass(compare(o, n))), D).getElements().size());
    }
    @Test void aNewClassWithAnAnnotatedMethodMarksTheMethodNew() throws Exception {
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        assertEquals(JApiChangeStatus.NEW, run(onlyClass(compare(null, n))).getChangeStatus());
    }
    @Test void aDeletedClassWithAnAnnotatedMethodMarksTheMethodRemoved() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        assertEquals(JApiChangeStatus.REMOVED, run(onlyClass(compare(o, null))).getChangeStatus());
    }
    @Test void anIntValueZeroToOneIsModified() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 0);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 4);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void aStringMemberChangeMakesAnnotationModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "a");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "b");
        assertEquals(JApiChangeStatus.MODIFIED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void anUnchangedIntMemberKeepsAnnotationUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 8);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 8);
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnMethod(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aStopMethodAnnotationIsAlsoTracked() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void stop(){}", D);
        assertEquals(JApiChangeStatus.NEW, annoOnMethod(methodNamed(onlyClass(compare(o, n)), "stop"), D).getChangeStatus());
    }
    @Test void anAnnotatedMethodOnTheOldSideOnlyIsRemovedWithItsAnnotation() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C");
        JApiMethod m = run(onlyClass(compare(o, n)));
        assertTrue(m.getChangeStatus() == JApiChangeStatus.REMOVED && annoOnMethod(m, D).getChangeStatus() == JApiChangeStatus.REMOVED);
    }
    @Test void anIntMemberChangeOnASecondAnnotationType() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", I, "level", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", I, "level", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnMethod(run(onlyClass(compare(o, n))), I), "level").getChangeStatus());
    }
}
