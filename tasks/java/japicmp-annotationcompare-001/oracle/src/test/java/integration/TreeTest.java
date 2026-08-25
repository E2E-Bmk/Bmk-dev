package integration;

import static fixtures.Model.annotationCount;
import static fixtures.Model.annotationNamed;
import static fixtures.Model.classAnnotation;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.method;
import static fixtures.Model.methodNamed;
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

/** Cross-owner checks combining annotation records with method records and sets of classes. */
class TreeTest {

    private static final String DEP = "java.lang.Deprecated";
    private static final String FUN = "java.lang.FunctionalInterface";
    private static final String DOC = "java.lang.annotation.Documented";

    private static CtClass k(String name) throws Exception {
        return publicClass(pool(), name);
    }

    // Depends-On: atomic::CompareTest::anAddedDeprecatedAnnotationIsNew
    @Test
    void anAnnotationAndAMethodAreBothNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C"); classAnnotation(n, DEP); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAddedDeprecatedAnnotationIsNew
    @Test
    void anAddedAnnotationWithAnUnchangedMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C"); method(o, "public void run(){}");
        CtClass n = k("a.C"); method(n, "public void run(){}"); classAnnotation(n, DEP);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anUnchangedDeprecatedAnnotationIsUnchanged
    @Test
    void anUnchangedAnnotationWithANewMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, DEP); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedDeprecatedAnnotationIsRemoved
    @Test
    void aRemovedAnnotationWithAnAddedMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedDeprecatedAnnotationIsRemoved
    @Test
    void aRemovedAnnotationWithARemovedMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); method(o, "public void run(){}");
        CtClass n = k("a.C");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aDistinctClassSetKeepsEachClassOwnAnnotations
    @Test
    void oneClassGainsAnAnnotationWhileAnotherGainsAMethod() throws Exception {
        CtClass aO = k("a.A"); CtClass aN = k("a.A"); classAnnotation(aN, DEP);
        CtClass bO = k("a.B"); CtClass bN = k("a.B"); method(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annotationNamed(classNamed(r, "a.A"), DEP).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.B"), "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aDistinctClassSetKeepsEachClassOwnAnnotations
    @Test
    void perClassAnnotationClassificationAcrossASet() throws Exception {
        CtClass aO = k("a.A"); CtClass aN = k("a.A"); classAnnotation(aN, DEP);
        CtClass bO = k("a.B"); classAnnotation(bO, DEP); CtClass bN = k("a.B");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annotationNamed(classNamed(r, "a.A"), DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(classNamed(r, "a.B"), DEP).getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::anAddedDeprecatedAnnotationIsNew
    @Test
    void addingAnAnnotationToOneOfTwoClassesLeavesTheOtherUnannotated() throws Exception {
        CtClass aO = k("a.A"); CtClass aN = k("a.A");
        CtClass bO = k("a.B"); CtClass bN = k("a.B"); classAnnotation(bN, DEP);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annotationCount(classNamed(r, "a.A")) == 0
                && annotationNamed(classNamed(r, "a.B"), DEP).getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoAddedAnnotationsAreBothNew
    @Test
    void aClassWithAMethodAndTwoAnnotationsHasEveryOwnerNew() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C");
        classAnnotation(n, DEP); classAnnotation(n, FUN); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anUnchangedDeprecatedAnnotationIsUnchanged
    @Test
    void anUnchangedAnnotationSurvivesAlongsideARemovedMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); method(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnotation(n, DEP);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::oneRetainedAndOneAddedClassifyIndependently
    @Test
    void aRetainedAndAnAddedAnnotationCoexistWithANewMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aNewClassAnnotationIsNew
    @Test
    void aBrandNewClassWithAnAnnotationAndAMethodHasBothNew() throws Exception {
        CtClass n = k("a.C"); classAnnotation(n, DEP); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedClassAnnotationIsRemoved
    @Test
    void aDeletedClassWithAnAnnotationAndAMethodHasBothRemoved() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); method(o, "public void run(){}");
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::twoUnchangedAnnotationsAreBothUnchanged
    @Test
    void twoUnchangedAnnotationsCoexistWithANewMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::oneAddedAndOneRemovedProduceTwoRecords
    @Test
    void anAddedAndARemovedAnnotationCoexistWithAnUnchangedMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); method(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnotation(n, FUN); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::theCountReflectsTheUnionOfBothSides
    @Test
    void theAnnotationCountHoldsWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, FUN); method(n, "public void run(){}");
        assertEquals(2, annotationCount(onlyClass(compare(o, n))));
    }

    // Depends-On: atomic::CompareTest::aDistinctClassSetKeepsEachClassOwnAnnotations
    @Test
    void threeClassesEachClassifyTheirOwnAnnotationChange() throws Exception {
        CtClass aO = k("a.A"); CtClass aN = k("a.A"); classAnnotation(aN, DEP);
        CtClass bO = k("a.B"); classAnnotation(bO, FUN); CtClass bN = k("a.B");
        CtClass cO = k("a.D"); classAnnotation(cO, DOC); CtClass cN = k("a.D"); classAnnotation(cN, DOC);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(annotationNamed(classNamed(r, "a.A"), DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(classNamed(r, "a.B"), FUN).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(classNamed(r, "a.D"), DOC).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aNewClassWithTwoAnnotationsHasBothNew
    @Test
    void aNewClassCarryingTwoAnnotationsAndAMethodMarksEveryOwnerNew() throws Exception {
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, DOC); method(n, "public int size(){return 0;}");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(c, DOC).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "size").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRetainedAnnotationStaysUnchangedWhileAnotherIsAdded
    @Test
    void aRetainedAnnotationAndANewAnnotationCoexistWithAnUnchangedMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); method(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, DOC); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, DOC).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesReportsItsName
    @Test
    void eachClassInAnAnnotatedSetKeepsItsOwnName() throws Exception {
        CtClass aO = k("a.One"); classAnnotation(aO, DEP);
        CtClass aN = k("a.One"); classAnnotation(aN, DEP);
        CtClass bO = k("a.Two"); CtClass bN = k("a.Two"); classAnnotation(bN, FUN);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(classNamed(r, "a.One") != null && classNamed(r, "a.Two") != null);
    }

    // Depends-On: atomic::CompareTest::threeAnnotationsWithMixedStatusesEachClassifyCorrectly
    @Test
    void threeMixedAnnotationsCoexistWithANewMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP); classAnnotation(n, DOC); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, DOC).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoRemovedAnnotationsAreBothRemoved
    @Test
    void twoRemovedAnnotationsCoexistWithARemovedMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN); method(o, "public void run(){}");
        CtClass n = k("a.C");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingTwoAnnotationsRaisesCountToTwo
    @Test
    void aTwoAnnotationCountHoldsAcrossAClassGainingAMethod() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C");
        classAnnotation(n, DEP); classAnnotation(n, FUN); method(n, "public void run(){}");
        assertEquals(2, annotationCount(onlyClass(compare(o, n))));
    }

    // Depends-On: atomic::CompareTest::oneRetainedAndOneRemovedClassifyIndependently
    @Test
    void aRetainedAndARemovedAnnotationCoexistWithAnAddedMethod() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); classAnnotation(o, FUN);
        CtClass n = k("a.C"); classAnnotation(n, DEP); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && annotationNamed(c, FUN).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoClassesEachGainingADistinctAnnotationClassifyThem
    @Test
    void twoClassesGainDistinctAnnotationsAndOneGainsAMethod() throws Exception {
        CtClass aO = k("a.A"); CtClass aN = k("a.A"); classAnnotation(aN, DEP); method(aN, "public void run(){}");
        CtClass bO = k("a.B"); CtClass bN = k("a.B"); classAnnotation(bN, DOC);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annotationNamed(classNamed(r, "a.A"), DEP).getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.A"), "run").getChangeStatus() == JApiChangeStatus.NEW
                && annotationNamed(classNamed(r, "a.B"), DOC).getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anUnchangedAnnotationStillProducesARecord
    @Test
    void anUnchangedAnnotatedClassWithAnUnchangedMethodKeepsBoth() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP); method(o, "public void run(){}");
        CtClass n = k("a.C"); classAnnotation(n, DEP); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::threeAddedAnnotationsAreAllNew
    @Test
    void threeAddedAnnotationsCoexistWithANewMethod() throws Exception {
        CtClass o = k("a.C"); CtClass n = k("a.C");
        classAnnotation(n, DEP); classAnnotation(n, FUN); classAnnotation(n, DOC); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationCount(c) == 3 && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::removingTheOnlyAnnotationLeavesOneRemovedRecord
    @Test
    void removingTheOnlyAnnotationWhileAddingAMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C"); classAnnotation(o, DEP);
        CtClass n = k("a.C"); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, DEP).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }
}
