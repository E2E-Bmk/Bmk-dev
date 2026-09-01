package integration;

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
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining enum and array member-value records with method presence and sets of classes. */
class TreeTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";
    static final String E = "java.lang.annotation.RetentionPolicy";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiChangeStatus elemStatus(JApiClass c, String method, String anno, String member) {
        return elementNamed(annoOnMethod(methodNamed(c, method), anno), member).getChangeStatus();
    }
    private static JApiChangeStatus annoStatus(JApiClass c, String method, String anno) {
        return annoOnMethod(methodNamed(c, method), anno).getChangeStatus();
    }
    private static JApiChangeStatus mStatus(JApiClass c, String method) {
        return methodNamed(c, method).getChangeStatus();
    }

    // Depends-On: atomic::CompareTest::enumMemberChangeIsModified
    // Depends-On: atomic::CompareTest::arrayMemberChangeIsModified
    @Test void anEnumChangeOnOneMethodAndAnArrayChangeOnAnother() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME"); arrayAnnoMethod(o, "public void stop(){}", D, "ids", 1);
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE"); arrayAnnoMethod(n, "public void stop(){}", D, "ids", 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "policy") == JApiChangeStatus.MODIFIED
                && elemStatus(c, "stop", D, "ids") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::enumMemberChangeIsModified
    @Test void anEnumChangeWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "CLASS"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "policy") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::arrayMemberChangeIsModified
    @Test void anArrayChangeWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1, 2); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 3, 4);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::enumMemberUnchangedIsUnchanged
    @Test void anUnchangedEnumWithANewMethod() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "policy") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::arrayMemberUnchangedIsUnchanged
    @Test void anUnchangedArrayWithARemovedMethod() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 5, 6); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 5, 6);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::enumMemberAddedIsNew
    @Test void anEnumMemberAddedWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "policy") == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::arrayMemberRemovedIsRemoved
    @Test void anArrayMemberRemovedWhileKeepingAPlainMethod() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.REMOVED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEnumChanges
    @Test void perClassEnumClassification() throws Exception {
        CtClass aO = k("a.A"); enumAnnoMethod(aO, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass aN = k("a.A"); enumAnnoMethod(aN, "public void run(){}", D, "policy", E, "SOURCE");
        CtClass bO = k("a.B"); markerMethod(bO, "public void run(){}", D);
        CtClass bN = k("a.B"); enumAnnoMethod(bN, "public void run(){}", D, "policy", E, "CLASS");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elemStatus(classNamed(r, "a.A"), "run", D, "policy") == JApiChangeStatus.MODIFIED
                && elemStatus(classNamed(r, "a.B"), "run", D, "policy") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoClassesWithDistinctArrayChanges
    @Test void perClassArrayClassification() throws Exception {
        CtClass aO = k("a.A"); arrayAnnoMethod(aO, "public void run(){}", D, "ids", 1);
        CtClass aN = k("a.A"); arrayAnnoMethod(aN, "public void run(){}", D, "ids", 1, 2);
        CtClass bO = k("a.B"); arrayAnnoMethod(bO, "public void run(){}", D, "ids", 3);
        CtClass bN = k("a.B"); markerMethod(bN, "public void run(){}", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elemStatus(classNamed(r, "a.A"), "run", D, "ids") == JApiChangeStatus.MODIFIED
                && elemStatus(classNamed(r, "a.B"), "run", D, "ids") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::anEnumMemberChangeMakesTheAnnotationModified
    @Test void anAnnotationModifiedByAnEnumWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anArrayMemberChangeMakesTheAnnotationModified
    @Test void anAnnotationModifiedByAnArrayWhileAnotherStaysUnchanged() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1); markerMethod(o, "public void keep(){}", I);
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 2); markerMethod(n, "public void keep(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.MODIFIED && annoStatus(c, "keep", I) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aNewClassWithAnEnumAnnotatedMethodMarksTheMethodNew
    @Test void aBrandNewClassWithEnumAndArrayMethods() throws Exception {
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME"); arrayAnnoMethod(n, "public void stop(){}", D, "ids", 1);
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.NEW && elemStatus(c, "stop", D, "ids") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aDeletedClassWithAnArrayAnnotatedMethodMarksTheMethodRemoved
    @Test void aDeletedClassWithEnumAndArrayMethods() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME"); arrayAnnoMethod(o, "public void stop(){}", D, "ids", 1);
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.REMOVED && elemStatus(c, "stop", D, "ids") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::changingAnEnumOnOneOfTwoMethods
    @Test void enumChangesOnTwoOfThreeMethods() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME"); enumAnnoMethod(o, "public void stop(){}", D, "policy", E, "RUNTIME"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE"); enumAnnoMethod(n, "public void stop(){}", D, "policy", E, "CLASS"); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "policy") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "policy") == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::changingAnArrayOnOneOfTwoMethods
    @Test void arrayChangesOnTwoOfThreeMethods() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1); arrayAnnoMethod(o, "public void stop(){}", D, "ids", 1); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 2); arrayAnnoMethod(n, "public void stop(){}", D, "ids", 3); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "ids") == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::stringMemberChangeIsModified
    // Depends-On: atomic::CompareTest::enumMemberChangeIsModified
    @Test void aStringChangeAndAnEnumChangeOnTwoMethods() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x"); enumAnnoMethod(o, "public void stop(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "y"); enumAnnoMethod(n, "public void stop(){}", D, "policy", E, "SOURCE");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "policy") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::arrayMemberLengthChangeIsModified
    @Test void anArrayGrowsWhileAnotherMethodGainsAnAnnotation() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1, 2); markerMethod(n, "public void stop(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.MODIFIED && annoStatus(c, "stop", I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anEmptyArrayVsNonEmptyIsModified
    @Test void anEmptyArrayBecomesPopulatedWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); arrayAnnoMethod(o, "public void run(){}", D, "ids");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::enumMemberUnchangedLeavesMethodUnchanged
    @Test void anEnumChangeLeavesTheMethodUnchangedWhileAnotherIsAdded() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeWithArrayMemberIsNew
    @Test void aSecondAnnotationTypeWithArrayAddedWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", I, "ids", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", I) == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::anEnumMemberChangeOnASecondAnnotationType
    @Test void twoAnnotationTypesWithEnumMembersOnDifferentMethods() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME"); enumAnnoMethod(o, "public void stop(){}", I, "policy", E, "CLASS");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "SOURCE"); enumAnnoMethod(n, "public void stop(){}", I, "policy", E, "CLASS");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "policy") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", I, "policy") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEnumChanges
    @Test void threeClassesEachClassifyAMemberValue() throws Exception {
        CtClass aO = k("a.A"); enumAnnoMethod(aO, "public void run(){}", D, "policy", E, "RUNTIME");
        CtClass aN = k("a.A"); enumAnnoMethod(aN, "public void run(){}", D, "policy", E, "SOURCE");
        CtClass bO = k("a.B"); arrayAnnoMethod(bO, "public void run(){}", D, "ids", 1);
        CtClass bN = k("a.B"); arrayAnnoMethod(bN, "public void run(){}", D, "ids", 1);
        CtClass cO = k("a.K"); markerMethod(cO, "public void run(){}", D);
        CtClass cN = k("a.K"); arrayAnnoMethod(cN, "public void run(){}", D, "ids", 9);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(elemStatus(classNamed(r, "a.A"), "run", D, "policy") == JApiChangeStatus.MODIFIED
                && elemStatus(classNamed(r, "a.B"), "run", D, "ids") == JApiChangeStatus.UNCHANGED
                && elemStatus(classNamed(r, "a.K"), "run", D, "ids") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aMarkerHasNoElements
    @Test void aMarkerHasNoElementsWhileAnotherMethodCarriesAnArray() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); arrayAnnoMethod(o, "public void stop(){}", D, "ids", 1);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); arrayAnnoMethod(n, "public void stop(){}", D, "ids", 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnMethod(methodNamed(c, "run"), D).getElements().size() == 0
                && elemStatus(c, "stop", D, "ids") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::stringMemberAddedIsNew
    @Test void aStringMemberAddedWhileAnEnumStaysUnchanged() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D); enumAnnoMethod(o, "public void stop(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "x"); enumAnnoMethod(n, "public void stop(){}", D, "policy", E, "RUNTIME");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.NEW && elemStatus(c, "stop", D, "policy") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anAddedAnnotationCarryingAnEnumMemberIsNew
    @Test void anAddedEnumAnnotationWhileAnArrayAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); arrayAnnoMethod(o, "public void stop(){}", D, "ids", 1);
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && annoStatus(c, "stop", D) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::anUnchangedAnnotationWithEnumMemberIsUnchanged
    @Test void anUnchangedEnumAnnotationWithAnUnchangedPlainMethod() throws Exception {
        CtClass o = k("a.C"); enumAnnoMethod(o, "public void run(){}", D, "policy", E, "RUNTIME"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME"); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.UNCHANGED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::arrayMemberAddedIsNew
    @Test void anArrayMemberAddedWhileAnEnumMemberIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D); enumAnnoMethod(o, "public void stop(){}", D, "policy", E, "RUNTIME");
        CtClass n = k("a.C"); arrayAnnoMethod(n, "public void run(){}", D, "ids", 1); markerMethod(n, "public void stop(){}", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "ids") == JApiChangeStatus.NEW && elemStatus(c, "stop", D, "policy") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::oneAnnotationWithMemberCountsOne
    @Test void oneAnnotationEachOnTwoMethods() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); enumAnnoMethod(n, "public void run(){}", D, "policy", E, "RUNTIME"); arrayAnnoMethod(n, "public void stop(){}", I, "ids", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoCountOnMethod(methodNamed(c, "run")) == 1 && annoCountOnMethod(methodNamed(c, "stop")) == 1);
    }
}
