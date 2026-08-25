package integration;

import static fixtures.Model.annoCountOnCtor;
import static fixtures.Model.annoOnCtor;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.ctorOfArity;
import static fixtures.Model.elementNamed;
import static fixtures.Model.intAnnoCtor;
import static fixtures.Model.markerCtor;
import static fixtures.Model.onlyClass;
import static fixtures.Model.plainCtor;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.stringAnnoCtor;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining constructor-annotation records with constructor presence and sets of classes. */
class TreeTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiChangeStatus annoStatus(JApiClass c, int arity, String anno) throws Exception {
        return annoOnCtor(ctorOfArity(c, arity), anno).getChangeStatus();
    }
    private static JApiChangeStatus elemStatus(JApiClass c, int arity, String anno, String member) throws Exception {
        return elementNamed(annoOnCtor(ctorOfArity(c, arity), anno), member).getChangeStatus();
    }
    private static JApiChangeStatus cStatus(JApiClass c, int arity) throws Exception {
        return ctorOfArity(c, arity).getChangeStatus();
    }

    // Depends-On: atomic::CompareTest::addedCtorAnnotationIsNew
    // Depends-On: atomic::CompareTest::anAnnotatedCtorAddedIsNew
    @Test void anAnnotationAddedToOneCtorWhileAnotherCtorIsAdded() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D); markerCtor(n, 1, D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.NEW && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::ctorAnnotationIntValueChangeIsModified
    @Test void aMemberChangeOnOneCtorWhileAnotherStaysPlain() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); plainCtor(o, 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.MODIFIED && cStatus(c, 1) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::removedCtorAnnotationIsRemoved
    @Test void anAnnotationRemovedWhileACtorIsAdded() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); plainCtor(n, 0); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.REMOVED && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::unchangedCtorAnnotationIsUnchanged
    @Test void anUnchangedAnnotatedCtorWithANewCtor() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); markerCtor(n, 0, D); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.UNCHANGED && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::ctorAnnotationStringValueChangeIsModified
    // Depends-On: atomic::CompareTest::ctorAnnotationIntValueChangeIsModified
    @Test void memberChangesOnTwoDifferentCtors() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); stringAnnoCtor(o, 1, D, "name", "x");
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); stringAnnoCtor(n, 1, D, "name", "y");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, 1, D, "name") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachCtorAnnotationChange
    @Test void perClassCtorAnnotationClassification() throws Exception {
        CtClass aO = k("a.A"); plainCtor(aO, 0);
        CtClass aN = k("a.A"); markerCtor(aN, 0, D);
        CtClass bO = k("a.B"); markerCtor(bO, 0, D);
        CtClass bN = k("a.B"); plainCtor(bN, 0);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoStatus(classNamed(r, "a.A"), 0, D) == JApiChangeStatus.NEW
                && annoStatus(classNamed(r, "a.B"), 0, D) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeOnACtorIsNew
    @Test void oneCtorGainsAnnotationAnotherKeepsIt() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); markerCtor(o, 1, I);
        CtClass n = k("a.C"); markerCtor(n, 0, D); markerCtor(n, 1, I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.NEW && annoStatus(c, 1, I) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anIntMemberAddedOnACtorAnnotation
    @Test void addingAMemberOnOneCtorWhileAnotherIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D); intAnnoCtor(o, 1, D, "count", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 1); intAnnoCtor(n, 1, D, "count", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.NEW && elemStatus(c, 1, D, "count") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anAnnotatedCtorAddedIsNew
    @Test void aBrandNewClassWithTwoAnnotatedCtors() throws Exception {
        CtClass n = k("a.C"); markerCtor(n, 0, D); markerCtor(n, 1, I);
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(cStatus(c, 0) == JApiChangeStatus.NEW && annoStatus(c, 1, I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAnnotatedCtorRemovedIsRemoved
    @Test void aDeletedClassWithTwoAnnotatedCtors() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D); markerCtor(o, 1, I);
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(cStatus(c, 0) == JApiChangeStatus.REMOVED && annoStatus(c, 1, I) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aCtorAnnotationValueChangeMakesTheAnnotationModified
    @Test void anAnnotationModifiedByAMemberWhileACtorIsAdded() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.MODIFIED && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aStringMemberRemovedOnACtorAnnotation
    @Test void removingAMemberWhileACtorIsRemoved() throws Exception {
        CtClass o = k("a.C"); stringAnnoCtor(o, 0, D, "name", "x"); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "name") == JApiChangeStatus.REMOVED && cStatus(c, 1) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingAnAnnotationToOneOfTwoCtors
    @Test void addingAnnotationsToTwoOfThreeCtors() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); plainCtor(o, 1); plainCtor(o, 2);
        CtClass n = k("a.C"); markerCtor(n, 0, D); markerCtor(n, 1, D); plainCtor(n, 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.NEW && annoStatus(c, 1, D) == JApiChangeStatus.NEW
                && annoCountOnCtor(ctorOfArity(c, 2)) == 0);
    }

    // Depends-On: atomic::CompareTest::ctorAnnotationIntValueUnchangedIsUnchanged
    @Test void anUnchangedMemberWhileACtorIsRemoved() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 5); plainCtor(o, 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 5);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.UNCHANGED && cStatus(c, 1) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::twoClassesWithDistinctCtorAnnotationChanges
    @Test void twoClassesDistinctChangesOneGainsACtor() throws Exception {
        CtClass aO = k("a.A"); plainCtor(aO, 0);
        CtClass aN = k("a.A"); markerCtor(aN, 0, D); plainCtor(aN, 1);
        CtClass bO = k("a.B"); intAnnoCtor(bO, 0, D, "count", 1);
        CtClass bN = k("a.B"); intAnnoCtor(bN, 0, D, "count", 2);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoStatus(classNamed(r, "a.A"), 0, D) == JApiChangeStatus.NEW
                && cStatus(classNamed(r, "a.A"), 1) == JApiChangeStatus.NEW
                && elemStatus(classNamed(r, "a.B"), 0, D, "count") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::anIntMemberChangeOnASecondAnnotationType
    @Test void twoAnnotationTypesOnDifferentCtors() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); intAnnoCtor(o, 1, I, "level", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); intAnnoCtor(n, 1, I, "level", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, 1, I, "level") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aPlainCtorPresentOnBothSidesIsUnchanged
    @Test void aPlainCtorStaysUnchangedWhileAnotherGainsAnnotation() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); plainCtor(o, 2);
        CtClass n = k("a.C"); markerCtor(n, 0, D); plainCtor(n, 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.NEW && cStatus(c, 2) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aStringMemberAddedOnACtorAnnotation
    @Test void addingAStringMemberWhileAddingACtor() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D);
        CtClass n = k("a.C"); stringAnnoCtor(n, 0, D, "name", "x"); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "name") == JApiChangeStatus.NEW && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachCtorAnnotationChange
    @Test void threeClassesEachClassifyACtorAnnotation() throws Exception {
        CtClass aO = k("a.A"); plainCtor(aO, 0);
        CtClass aN = k("a.A"); markerCtor(aN, 0, D);
        CtClass bO = k("a.B"); markerCtor(bO, 0, D);
        CtClass bN = k("a.B"); plainCtor(bN, 0);
        CtClass cO = k("a.K"); markerCtor(cO, 0, D);
        CtClass cN = k("a.K"); markerCtor(cN, 0, D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(annoStatus(classNamed(r, "a.A"), 0, D) == JApiChangeStatus.NEW
                && annoStatus(classNamed(r, "a.B"), 0, D) == JApiChangeStatus.REMOVED
                && annoStatus(classNamed(r, "a.K"), 0, D) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::changingAMemberOnOneOfTwoCtors
    @Test void changingMembersOnTwoCtorsKeepingAThirdPlain() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); intAnnoCtor(o, 1, D, "count", 1); plainCtor(o, 2);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); intAnnoCtor(n, 1, D, "count", 2); plainCtor(n, 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, 1, D, "count") == JApiChangeStatus.MODIFIED
                && annoCountOnCtor(ctorOfArity(c, 2)) == 0);
    }

    // Depends-On: atomic::CompareTest::unchangedCtorAnnotationIsUnchanged
    @Test void anUnchangedAnnotatedCtorWithAnUnchangedPlainCtor() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.UNCHANGED && cStatus(c, 1) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::removedCtorAnnotationIsRemoved
    @Test void aMemberChangeAndAnAnnotationRemovalOnTwoCtors() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); markerCtor(o, 1, D);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.MODIFIED && annoStatus(c, 1, D) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingAnAnnotationToOneOfTwoCtors
    @Test void annotationsAddedToTwoDistinctlyAritiedCtors() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D); markerCtor(n, 1, I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, D) == JApiChangeStatus.NEW && annoStatus(c, 1, I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aCtorAnnotationValueChangeLeavesTheCtorUnchanged
    @Test void aMemberChangeLeavesCtorUnchangedWhileAnotherCtorIsAdded() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1);
        CtClass n = k("a.C"); intAnnoCtor(n, 0, D, "count", 2); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(cStatus(c, 0) == JApiChangeStatus.UNCHANGED && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aMarkerCtorAnnotationHasNoElements
    @Test void aMarkerCtorAnnotationHasNoElementsWhileACtorIsAdded() throws Exception {
        CtClass o = k("a.C"); plainCtor(o, 0);
        CtClass n = k("a.C"); markerCtor(n, 0, D); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnCtor(ctorOfArity(c, 0), D).getElements().size() == 0 && cStatus(c, 1) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anIntMemberRemovedOnACtorAnnotation
    @Test void removingAnIntMemberWhileKeepingAPlainCtor() throws Exception {
        CtClass o = k("a.C"); intAnnoCtor(o, 0, D, "count", 1); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, D); plainCtor(n, 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, 0, D, "count") == JApiChangeStatus.REMOVED && cStatus(c, 1) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aSecondArityCtorAnnotationIsAlsoTracked
    @Test void aSecondAnnotationTypeAddedWhileACtorIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerCtor(o, 0, D); plainCtor(o, 1);
        CtClass n = k("a.C"); markerCtor(n, 0, I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, 0, I) == JApiChangeStatus.NEW && cStatus(c, 1) == JApiChangeStatus.REMOVED);
    }
}
