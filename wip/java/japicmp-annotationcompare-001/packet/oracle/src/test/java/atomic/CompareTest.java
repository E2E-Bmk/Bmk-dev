package atomic;

import static fixtures.Model.annotationCount;
import static fixtures.Model.annotationNamed;
import static fixtures.Model.classAnnotation;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Single-owner checks over synthesised runtime-visible annotation sets. */
class CompareTest {

    private static final String DEP = "java.lang.Deprecated";
    private static final String FUN = "java.lang.FunctionalInterface";
    private static final String DOC = "java.lang.annotation.Documented";
    private static final String INH = "java.lang.annotation.Inherited";

    private static CtClass k(String name) throws Exception {
        return publicClass(pool(), name);
    }

    @Test
    void anAddedDeprecatedAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertEquals(JApiChangeStatus.NEW, annotationNamed(onlyClass(compare(o, n)), DEP).getChangeStatus());
    }

    @Test
    void aRemovedDeprecatedAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, annotationNamed(onlyClass(compare(o, n)), DEP).getChangeStatus());
    }

    @Test
    void anUnchangedDeprecatedAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertEquals(JApiChangeStatus.UNCHANGED, annotationNamed(onlyClass(compare(o, n)), DEP).getChangeStatus());
    }

    @Test
    void anAddedFunctionalInterfaceAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, FUN);
        assertEquals(JApiChangeStatus.NEW, annotationNamed(onlyClass(compare(o, n)), FUN).getChangeStatus());
    }

    @Test
    void aRemovedFunctionalInterfaceAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, FUN); CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, annotationNamed(onlyClass(compare(o, n)), FUN).getChangeStatus());
    }

    @Test
    void anUnchangedFunctionalInterfaceAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, FUN); CtClass n = k("a.C"); classAnnotation(n, FUN);
        assertEquals(JApiChangeStatus.UNCHANGED, annotationNamed(onlyClass(compare(o, n)), FUN).getChangeStatus());
    }

    @Test
    void anAddedDocumentedAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DOC);
        assertEquals(JApiChangeStatus.NEW, annotationNamed(onlyClass(compare(o, n)), DOC).getChangeStatus());
    }

    @Test
    void aRemovedDocumentedAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DOC); CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, annotationNamed(onlyClass(compare(o, n)), DOC).getChangeStatus());
    }

    @Test
    void anUnchangedDocumentedAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DOC); CtClass n = k("a.C"); classAnnotation(n, DOC);
        assertEquals(JApiChangeStatus.UNCHANGED, annotationNamed(onlyClass(compare(o, n)), DOC).getChangeStatus());
    }

    @Test
    void anAddedInheritedAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, INH);
        assertEquals(JApiChangeStatus.NEW, annotationNamed(onlyClass(compare(o, n)), INH).getChangeStatus());
    }

    @Test
    void aRemovedInheritedAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, INH); CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, annotationNamed(onlyClass(compare(o, n)), INH).getChangeStatus());
    }

    @Test
    void anUnchangedInheritedAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, INH); CtClass n = k("a.C"); classAnnotation(n, INH);
        assertEquals(JApiChangeStatus.UNCHANGED, annotationNamed(onlyClass(compare(o, n)), INH).getChangeStatus());
    }

    @Test
    void anAddedAnnotationReportsItsFullyQualifiedName() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertEquals(DEP, annotationNamed(onlyClass(compare(o, n)), DEP).getFullyQualifiedName());
    }

    @Test
    void aSecondAnnotationReportsItsOwnName() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, FUN);
        assertEquals(FUN, annotationNamed(onlyClass(compare(o, n)), FUN).getFullyQualifiedName());
    }

    @Test
    void addingOneAnnotationRaisesCountToOne() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertEquals(1, annotationCount(onlyClass(compare(o, n))));
    }

    @Test
    void addingTwoAnnotationsRaisesCountToTwo() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN);
        assertEquals(2, annotationCount(onlyClass(compare(o, n))));
    }

    @Test
    void noAnnotationsOnEitherSideYieldsNoRecords() throws Exception {
        assertEquals(0, annotationCount(onlyClass(compare(k("a.C"), k("a.C")))));
    }

    @Test
    void twoAddedAnnotationsAreBothNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void twoRemovedAnnotationsAreBothRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN); CtClass n = k("a.C");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void twoUnchangedAnnotationsAreBothUnchanged() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    @Test
    void oneRetainedAndOneAddedClassifyIndependently() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void oneRetainedAndOneRemovedClassifyIndependently() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void oneAddedAndOneRemovedProduceTwoRecords() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, FUN);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void aNewClassAnnotationIsNew() throws Exception {
        CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertEquals(JApiChangeStatus.NEW, annotationNamed(onlyClass(compare(null, n)), DEP).getChangeStatus());
    }

    @Test
    void aRemovedClassAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        assertEquals(JApiChangeStatus.REMOVED, annotationNamed(onlyClass(compare(o, null)), DEP).getChangeStatus());
    }

    @Test
    void aNewClassWithTwoAnnotationsHasBothNew() throws Exception {
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN);
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void aRemovedClassWithTwoAnnotationsHasBothRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void aRetainedAnnotationStaysUnchangedWhileAnotherIsAdded() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, DOC);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, DOC).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void theCountReflectsTheUnionOfBothSides() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN);
        assertEquals(2, annotationCount(onlyClass(compare(o, n))));
    }

    @Test
    void theCountIncludesRemovedAnnotations() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertEquals(2, annotationCount(onlyClass(compare(o, n))));
    }

    @Test
    void aDistinctClassSetKeepsEachClassOwnAnnotations() throws Exception {
        CtClass aO = k("a.A"); classAnnotation(aO, DEP);
        CtClass aN = k("a.A"); classAnnotation(aN, DEP);
        CtClass bO = k("a.B"); CtClass bN = k("a.B"); classAnnotation(bN, FUN);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annotationNamed(classNamed(r, "a.A"), DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(classNamed(r, "a.B"), FUN).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void anUnchangedAnnotationStillProducesARecord() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); CtClass n = k("a.C"); classAnnotation(n, DEP);
        assertTrue(annotationNamed(onlyClass(compare(o, n)), DEP) != null);
    }

    @Test
    void threeAddedAnnotationsAreAllNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C");
        classAnnotation(n, DEP); classAnnotation(n, FUN); classAnnotation(n, DOC);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(c, DOC).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void threeAnnotationsWithMixedStatusesEachClassifyCorrectly() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, DOC);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, DOC).getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void removingTheOnlyAnnotationLeavesOneRemovedRecord() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); CtClass n = k("a.C");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationCount(c) == 1 && annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void aClassPresentOnBothSidesReportsItsName() throws Exception {
        assertEquals("a.C", onlyClass(compare(k("a.C"), k("a.C"))).getFullyQualifiedName());
    }

    @Test
    void anAddedInheritedAnnotationReportsItsName() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, INH);
        assertEquals(INH, annotationNamed(onlyClass(compare(o, n)), INH).getFullyQualifiedName());
    }

    @Test
    void twoClassesEachGainingADistinctAnnotationClassifyThem() throws Exception {
        CtClass aO = k("a.A"); CtClass aN = k("a.A"); classAnnotation(aN, DEP);
        CtClass bO = k("a.B"); CtClass bN = k("a.B"); classAnnotation(bN, DOC);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annotationNamed(classNamed(r, "a.A"), DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(classNamed(r, "a.B"), DOC).getChangeStatus() == JApiChangeStatus.NEW);
    }
}
