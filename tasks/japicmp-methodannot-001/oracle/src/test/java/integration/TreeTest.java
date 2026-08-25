package integration;

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
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining method-annotation records with method presence and sets of classes. */
class TreeTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiChangeStatus annoStatus(JApiClass c, String method, String anno) {
        return annoOnMethod(methodNamed(c, method), anno).getChangeStatus();
    }
    private static JApiChangeStatus elemStatus(JApiClass c, String method, String anno, String member) {
        return elementNamed(annoOnMethod(methodNamed(c, method), anno), member).getChangeStatus();
    }
    private static JApiChangeStatus mStatus(JApiClass c, String method) {
        return methodNamed(c, method).getChangeStatus();
    }

    // Depends-On: atomic::CompareTest::addedMethodAnnotationIsNew
    // Depends-On: atomic::CompareTest::anAnnotatedMethodAddedIsNew
    @Test void anAnnotationAddedToOneMethodWhileAnotherMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); markerMethod(n, "public void stop(){}", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::methodAnnotationIntValueChangeIsModified
    @Test void aMemberChangeOnOneMethodWhileAnotherStaysPlain() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::removedMethodAnnotationIsRemoved
    @Test void anAnnotationRemovedWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.REMOVED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::unchangedMethodAnnotationIsUnchanged
    @Test void anUnchangedAnnotatedMethodWithANewMethod() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::methodAnnotationStringValueChangeIsModified
    // Depends-On: atomic::CompareTest::methodAnnotationIntValueChangeIsModified
    @Test void memberChangesOnTwoDifferentMethods() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1); stringAnnoMethod(o, "public void stop(){}", D, "name", "x");
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2); stringAnnoMethod(n, "public void stop(){}", D, "name", "y");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "name") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachMethodAnnotationChange
    @Test void perClassMethodAnnotationClassification() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); markerMethod(aN, "public void run(){}", D);
        CtClass bO = k("a.B"); markerMethod(bO, "public void run(){}", D);
        CtClass bN = k("a.B"); plainMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoStatus(classNamed(r, "a.A"), "run", D) == JApiChangeStatus.NEW
                && annoStatus(classNamed(r, "a.B"), "run", D) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeOnAMethodIsNew
    @Test void oneMethodGainsAnnotationAnotherKeepsIt() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); markerMethod(o, "public void stop(){}", I);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); markerMethod(n, "public void stop(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && annoStatus(c, "stop", I) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anIntMemberAddedOnAMethodAnnotation
    @Test void addingAMemberOnOneMethodWhileAnotherIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D); intAnnoMethod(o, "public void stop(){}", D, "count", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 1); intAnnoMethod(n, "public void stop(){}", D, "count", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.NEW && elemStatus(c, "stop", D, "count") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anAnnotatedMethodAddedIsNew
    @Test void aBrandNewClassWithTwoAnnotatedMethods() throws Exception {
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); markerMethod(n, "public void stop(){}", I);
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.NEW && annoStatus(c, "stop", I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAnnotatedMethodRemovedIsRemoved
    @Test void aDeletedClassWithTwoAnnotatedMethods() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D); markerMethod(o, "public void stop(){}", I);
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.REMOVED && annoStatus(c, "stop", I) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aMethodAnnotationValueChangeMakesTheAnnotationModified
    @Test void anAnnotationModifiedByAMemberWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aStringMemberRemovedOnAMethodAnnotation
    @Test void removingAMemberWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.REMOVED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingAnAnnotationToOneOfTwoMethods
    @Test void addingAnnotationsToTwoOfThreeMethods() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void stop(){}"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); markerMethod(n, "public void stop(){}", D); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && annoStatus(c, "stop", D) == JApiChangeStatus.NEW
                && annoCountOnMethod(methodNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::methodAnnotationIntValueUnchangedIsUnchanged
    @Test void anUnchangedMemberWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 5); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 5);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::twoClassesWithDistinctMethodAnnotationChanges
    @Test void twoClassesDistinctChangesOneGainsAMethod() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); markerMethod(aN, "public void run(){}", D); plainMethod(aN, "public void extra(){}");
        CtClass bO = k("a.B"); intAnnoMethod(bO, "public void run(){}", D, "count", 1);
        CtClass bN = k("a.B"); intAnnoMethod(bN, "public void run(){}", D, "count", 2);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoStatus(classNamed(r, "a.A"), "run", D) == JApiChangeStatus.NEW
                && mStatus(classNamed(r, "a.A"), "extra") == JApiChangeStatus.NEW
                && elemStatus(classNamed(r, "a.B"), "run", D, "count") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::anIntMemberChangeOnASecondAnnotationType
    @Test void twoAnnotationTypesOnDifferentMethods() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1); intAnnoMethod(o, "public void stop(){}", I, "level", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2); intAnnoMethod(n, "public void stop(){}", I, "level", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", I, "level") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aPlainMethodPresentOnBothSidesIsUnchanged
    @Test void aPlainMethodStaysUnchangedWhileAnotherGainsAnnotation() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aStringMemberAddedOnAMethodAnnotation
    @Test void addingAStringMemberWhileAddingAMethod() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "x"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachMethodAnnotationChange
    @Test void threeClassesEachClassifyAMethodAnnotation() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); markerMethod(aN, "public void run(){}", D);
        CtClass bO = k("a.B"); markerMethod(bO, "public void run(){}", D);
        CtClass bN = k("a.B"); plainMethod(bN, "public void run(){}");
        CtClass cO = k("a.E"); markerMethod(cO, "public void run(){}", D);
        CtClass cN = k("a.E"); markerMethod(cN, "public void run(){}", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(annoStatus(classNamed(r, "a.A"), "run", D) == JApiChangeStatus.NEW
                && annoStatus(classNamed(r, "a.B"), "run", D) == JApiChangeStatus.REMOVED
                && annoStatus(classNamed(r, "a.E"), "run", D) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::changingAMemberOnOneOfTwoMethods
    @Test void changingMembersOnTwoMethodsKeepingAThirdPlain() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1); intAnnoMethod(o, "public void stop(){}", D, "count", 1); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 2); intAnnoMethod(n, "public void stop(){}", D, "count", 3); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED
                && elemStatus(c, "stop", D, "count") == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::unchangedMethodAnnotationIsUnchanged
    @Test void anUnchangedAnnotatedMethodWithAnUnchangedPlainMethod() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.UNCHANGED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aSecondMemberValueChangeOnAMethodAnnotation
    @Test void aMemberChangeAndAnAnnotationRemovalOnTwoMethods() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "level", 3); markerMethod(o, "public void stop(){}", I);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "level", 4); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "level") == JApiChangeStatus.MODIFIED && annoStatus(c, "stop", I) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aStopMethodAnnotationIsAlsoTracked
    @Test void annotationsAddedToTwoDistinctlyNamedMethods() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void alpha(){}"); plainMethod(o, "public void beta(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void alpha(){}", D); markerMethod(n, "public void beta(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "alpha", D) == JApiChangeStatus.NEW && annoStatus(c, "beta", I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aMethodAnnotationValueChangeLeavesTheMethodUnchanged
    @Test void aMemberChangeLeavesMethodUnchangedWhileAnotherMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1);
        CtClass n = k("a.C"); intAnnoMethod(n, "public void run(){}", D, "count", 7); markerMethod(n, "public void stop(){}", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aMarkerMethodAnnotationHasNoElements
    @Test void aMarkerMethodAnnotationHasNoElementsWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnMethod(methodNamed(c, "run"), D).getElements().size() == 0 && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anIntMemberRemovedOnAMethodAnnotation
    @Test void removingAnIntMemberWhileKeepingAPlainMethod() throws Exception {
        CtClass o = k("a.C"); intAnnoMethod(o, "public void run(){}", D, "count", 1); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.REMOVED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeOnAMethodIsNew
    @Test void aSecondAnnotationTypeAddedWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", I) == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }
}
