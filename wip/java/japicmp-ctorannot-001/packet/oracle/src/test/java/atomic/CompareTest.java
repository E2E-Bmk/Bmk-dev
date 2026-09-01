package atomic;

import static fixtures.Model.annoCountOnCtor;
import static fixtures.Model.annoOnCtor;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.ctorCount;
import static fixtures.Model.ctorOfArity;
import static fixtures.Model.elementNamed;
import static fixtures.Model.intAnnoCtor;
import static fixtures.Model.markerCtor;
import static fixtures.Model.onlyClass;
import static fixtures.Model.plainCtor;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.stringAnnoCtor;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;
import org.markline.model.JApiConstructor;

/** Single-owner checks over annotations carried by constructors, keyed by parameter arity. */
class CompareTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiConstructor c0(JApiClass c) throws Exception { return ctorOfArity(c, 0); }

    // ---- constructor annotation presence ----
    @Test void addedCtorAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.NEW, annoOnCtor(c0(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void removedCtorAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); plainCtor(n, 0);
        assertEquals(JApiChangeStatus.REMOVED, annoOnCtor(c0(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void unchangedCtorAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnCtor(c0(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void addingACtorAnnotationLeavesTheCtorUnchanged() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.UNCHANGED, c0(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aCtorAnnotationReportsItsFullyQualifiedName() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(D, annoOnCtor(c0(onlyClass(compare(o, n))), D).getFullyQualifiedName());
    }
    @Test void oneAddedCtorAnnotationCountsOne() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(1, annoCountOnCtor(c0(onlyClass(compare(o, n)))));
    }

    // ---- element values on a constructor annotation ----
    @Test void ctorAnnotationIntValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void ctorAnnotationIntValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 5);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 5);
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void ctorAnnotationStringValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoCtor(o, 0, D, "name", "x");
        CtClass n = k("a.C"); stringAnnoCtor(n, 0, D, "name", "y");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void ctorAnnotationStringValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); stringAnnoCtor(o, 0, D, "name", "same");
        CtClass n = k("a.C"); stringAnnoCtor(n, 0, D, "name", "same");
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void aCtorAnnotationValueChangeMakesTheAnnotationModified() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, annoOnCtor(c0(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aCtorAnnotationValueChangeLeavesTheCtorUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2);
        assertEquals(JApiChangeStatus.UNCHANGED, c0(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aCtorAnnotationElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "size", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "size", 2);
        assertEquals("size", elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "size").getName());
    }
    @Test void aSecondMemberValueChangeOnACtorAnnotation() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "level", 3);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "level", 4);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "level").getChangeStatus());
    }

    // ---- annotated-constructor presence (by arity) ----
    @Test void anAnnotatedCtorAddedIsNew() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); plainCtor(n, 0); markerCtor(n, 1, D);
        assertEquals(JApiChangeStatus.NEW, ctorOfArity(onlyClass(compare(o, n)), 1).getChangeStatus());
    }
    @Test void anAnnotatedCtorRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); markerCtor(o, 1, D);
        CtClass n = k("a.C"); plainCtor(n, 0);
        assertEquals(JApiChangeStatus.REMOVED, ctorOfArity(onlyClass(compare(o, n)), 1).getChangeStatus());
    }
    @Test void anUnchangedAnnotatedCtorIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.UNCHANGED, c0(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aPlainCtorPresentOnBothSidesIsUnchanged() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); plainCtor(n, 0);
        assertEquals(JApiChangeStatus.UNCHANGED, c0(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anAddedAnnotatedCtorCarriesItsAnnotationAsNew() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); plainCtor(n, 0); markerCtor(n, 1, D);
        assertEquals(JApiChangeStatus.NEW, annoOnCtor(ctorOfArity(onlyClass(compare(o, n)), 1), D).getChangeStatus());
    }

    // ---- multiple constructors ----
    @Test void addingAnAnnotationToOneOfTwoCtors() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnCtor(ctorOfArity(c, 0), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoCountOnCtor(ctorOfArity(c, 1)) == 0);
    }
    @Test void changingAMemberOnOneOfTwoCtors() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); plainCtor(o, 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 9); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnCtor(ctorOfArity(c, 0), D), "count").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnCtor(ctorOfArity(c, 1)) == 0);
    }

    // ---- multi-class ----
    @Test void aClassSetClassifiesEachCtorAnnotationChange() throws Exception {
        CtClass aO = k("a.A"); plainCtor(aO, 0);
        CtClass aN = k("a.A"); markerCtor(aN, 0, D);
        CtClass bO = k("a.B"); markerCtor(bO, 0, D);
        CtClass bN = k("a.B"); markerCtor(bN, 0, D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoOnCtor(ctorOfArity(classNamed(r, "a.A"), 0), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoOnCtor(ctorOfArity(classNamed(r, "a.B"), 0), D).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }
    @Test void twoClassesWithDistinctCtorAnnotationChanges() throws Exception {
        CtClass aO = k("a.A"); plainCtor(aO, 0);
        CtClass aN = k("a.A"); markerCtor(aN, 0, D);
        CtClass bO = k("a.B"); markerCtor(bO, 0, D);
        CtClass bN = k("a.B"); plainCtor(bN, 0);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoOnCtor(ctorOfArity(classNamed(r, "a.A"), 0), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoOnCtor(ctorOfArity(classNamed(r, "a.B"), 0), D).getChangeStatus() == JApiChangeStatus.REMOVED);
    }
    @Test void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); plainCtor(n, 0);
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }

    // ---- second annotation type / string ----
    @Test void aSecondAnnotationTypeOnACtorIsNew() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, I);
        assertEquals(JApiChangeStatus.NEW, annoOnCtor(c0(onlyClass(compare(o, n))), I).getChangeStatus());
    }
    @Test void aStringMemberAddedOnACtorAnnotation() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); stringAnnoCtor(n, 0, D, "name", "x");
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void aStringMemberRemovedOnACtorAnnotation() throws Exception {
        CtClass o = k("a.C"); stringAnnoCtor(o, 0, D, "name", "x");
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void anIntMemberAddedOnACtorAnnotation() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 1);
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void anIntMemberRemovedOnACtorAnnotation() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void aMarkerCtorAnnotationHasNoElements() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(0, annoOnCtor(c0(onlyClass(compare(o, n))), D).getElements().size());
    }
    @Test void aNewClassWithAnAnnotatedCtorMarksTheCtorNew() throws Exception {
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(JApiChangeStatus.NEW, c0(onlyClass(compare(null, n))).getChangeStatus());
    }
    @Test void aDeletedClassWithAnAnnotatedCtorMarksTheCtorRemoved() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        assertEquals(JApiChangeStatus.REMOVED, c0(onlyClass(compare(o, null))).getChangeStatus());
    }
    @Test void anIntValueZeroToOneIsModified() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 0);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 1);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void aStringMemberChangeMakesAnnotationModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoCtor(o, 0, D, "name", "a");
        CtClass n = k("a.C"); stringAnnoCtor(n, 0, D, "name", "b");
        assertEquals(JApiChangeStatus.MODIFIED, annoOnCtor(c0(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void anUnchangedIntMemberKeepsAnnotationUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 7);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 7);
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnCtor(c0(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aSecondArityCtorAnnotationIsAlsoTracked() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D); markerCtor(n, 1, D);
        assertEquals(JApiChangeStatus.NEW, annoOnCtor(ctorOfArity(onlyClass(compare(o, n)), 1), D).getChangeStatus());
    }
    @Test void anAnnotatedCtorOnTheOldSideOnlyIsRemovedWithItsAnnotation() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); markerCtor(o, 1, D);
        CtClass n = k("a.C"); plainCtor(n, 0);
        assertEquals(JApiChangeStatus.REMOVED, annoOnCtor(ctorOfArity(onlyClass(compare(o, n)), 1), D).getChangeStatus());
    }
    @Test void anIntMemberChangeOnASecondAnnotationType() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, I, "level", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, I, "level", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnCtor(c0(onlyClass(compare(o, n))), I), "level").getChangeStatus());
    }
    @Test void aCtorCountOfOneWhenASingleCtorIsPresent() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        assertEquals(1, ctorCount(onlyClass(compare(o, n))));
    }
}
