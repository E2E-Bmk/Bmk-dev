package integration;

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
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining class-value and nested-annotation records with method presence and sets of classes. */
class TreeTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";
    static final String N = "java.lang.annotation.Target";

    private static CtClass k(String s) throws Exception { return publicClass(pool(), s); }
    private static JApiChangeStatus annoStatus(JApiClass c, String method, String anno) {
        return annoOnMethod(methodNamed(c, method), anno).getChangeStatus();
    }
    private static JApiChangeStatus elemStatus(JApiClass c, String method, String anno, String member) {
        return elementNamed(annoOnMethod(methodNamed(c, method), anno), member).getChangeStatus();
    }
    private static JApiChangeStatus mStatus(JApiClass c, String method) {
        return methodNamed(c, method).getChangeStatus();
    }

    // Depends-On: atomic::CompareTest::classMemberChangeIsModified
    // Depends-On: atomic::CompareTest::nestedAnnotationValueChangeIsModified
    @Test void aClassChangeOnOneMethodAndANestedChangeOnAnother() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String"); nestedAnnoMethod(o, "public void stop(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer"); nestedAnnoMethod(n, "public void stop(){}", D, "inner", I, "count", 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "type") == JApiChangeStatus.MODIFIED
                && elemStatus(c, "stop", D, "inner") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::classMemberChangeIsModified
    @Test void aClassChangeWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Object"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "type") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::nestedAnnotationValueChangeIsModified
    @Test void aNestedChangeWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "inner") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::classMemberUnchangedIsUnchanged
    @Test void anUnchangedClassWithANewMethod() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "type") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::nestedAnnotationUnchangedIsUnchanged
    @Test void anUnchangedNestedWithARemovedMethod() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 5); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 5);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "inner") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::classMemberAddedIsNew
    @Test void aClassMemberAddedWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); markerMethod(o, "public void run(){}", D);
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "type") == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::nestedAnnotationMemberRemovedIsRemoved
    @Test void aNestedMemberRemovedWhileKeepingAPlainMethod() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "inner") == JApiChangeStatus.REMOVED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesClassMemberChanges
    @Test void perClassClassMemberClassification() throws Exception {
        CtClass aO = k("a.A"); classAnnoMethod(aO, "public void run(){}", D, "type", "java.lang.String");
        CtClass aN = k("a.A"); classAnnoMethod(aN, "public void run(){}", D, "type", "java.lang.Integer");
        CtClass bO = k("a.B"); markerMethod(bO, "public void run(){}", D);
        CtClass bN = k("a.B"); classAnnoMethod(bN, "public void run(){}", D, "type", "java.lang.String");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elemStatus(classNamed(r, "a.A"), "run", D, "type") == JApiChangeStatus.MODIFIED
                && elemStatus(classNamed(r, "a.B"), "run", D, "type") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoClassesWithDistinctNestedChanges
    @Test void perClassNestedClassification() throws Exception {
        CtClass aO = k("a.A"); nestedAnnoMethod(aO, "public void run(){}", D, "inner", I, "count", 1);
        CtClass aN = k("a.A"); nestedAnnoMethod(aN, "public void run(){}", D, "inner", I, "count", 2);
        CtClass bO = k("a.B"); nestedAnnoMethod(bO, "public void run(){}", D, "inner", I, "count", 3);
        CtClass bN = k("a.B"); markerMethod(bN, "public void run(){}", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elemStatus(classNamed(r, "a.A"), "run", D, "inner") == JApiChangeStatus.MODIFIED
                && elemStatus(classNamed(r, "a.B"), "run", D, "inner") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aClassMemberChangeMakesTheAnnotationModified
    @Test void anAnnotationModifiedByAClassWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Object"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aNestedAnnotationValueChangeMakesTheOuterModified
    @Test void anAnnotationModifiedByANestedWhileAnotherStaysUnchanged() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1); markerMethod(o, "public void keep(){}", I);
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2); markerMethod(n, "public void keep(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.MODIFIED && annoStatus(c, "keep", I) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aNewClassWithAClassAnnotatedMethodMarksTheMethodNew
    @Test void aBrandNewClassWithClassAndNestedMethods() throws Exception {
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String"); nestedAnnoMethod(n, "public void stop(){}", D, "inner", I, "count", 1);
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.NEW && elemStatus(c, "stop", D, "inner") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aDeletedClassWithANestedAnnotatedMethodMarksTheMethodRemoved
    @Test void aDeletedClassWithClassAndNestedMethods() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String"); nestedAnnoMethod(o, "public void stop(){}", D, "inner", I, "count", 1);
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.REMOVED && elemStatus(c, "stop", D, "inner") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::changingAClassOnOneOfTwoMethods
    @Test void classChangesOnTwoOfThreeMethods() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String"); classAnnoMethod(o, "public void stop(){}", D, "type", "java.lang.String"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer"); classAnnoMethod(n, "public void stop(){}", D, "type", "java.lang.Object"); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "type") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "type") == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::changingANestedOnOneOfTwoMethods
    @Test void nestedChangesOnTwoOfThreeMethods() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1); nestedAnnoMethod(o, "public void stop(){}", D, "inner", I, "count", 1); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", I, "count", 2); nestedAnnoMethod(n, "public void stop(){}", D, "inner", I, "count", 3); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "inner") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "inner") == JApiChangeStatus.MODIFIED
                && annoCountOnMethod(methodNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::stringMemberChangeIsModified
    // Depends-On: atomic::CompareTest::classMemberChangeIsModified
    @Test void aStringChangeAndAClassChangeOnTwoMethods() throws Exception {
        CtClass o = k("a.C"); stringAnnoMethod(o, "public void run(){}", D, "name", "x"); classAnnoMethod(o, "public void stop(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); stringAnnoMethod(n, "public void run(){}", D, "name", "y"); classAnnoMethod(n, "public void stop(){}", D, "type", "java.lang.Integer");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "type") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aNestedTypeSwapWithEqualMembersIsUnchanged
    @Test void aNestedTypeSwapWhileAnotherMethodGainsAnAnnotation() throws Exception {
        CtClass o = k("a.C"); nestedAnnoMethod(o, "public void run(){}", D, "inner", I, "count", 1); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); nestedAnnoMethod(n, "public void run(){}", D, "inner", N, "count", 1); markerMethod(n, "public void stop(){}", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "inner") == JApiChangeStatus.UNCHANGED && annoStatus(c, "stop", I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::classMemberUnchangedLeavesMethodUnchanged
    @Test void aClassChangeLeavesTheMethodUnchangedWhileAnotherIsAdded() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeWithClassMemberIsNew
    @Test void aSecondAnnotationTypeWithClassAddedWhileAMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); plainMethod(o, "public void stop(){}");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", I, "type", "java.lang.String");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", I) == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aClassMemberChangeOnASecondAnnotationType
    @Test void twoAnnotationTypesWithClassMembersOnDifferentMethods() throws Exception {
        CtClass o = k("a.C"); classAnnoMethod(o, "public void run(){}", D, "type", "java.lang.String"); classAnnoMethod(o, "public void stop(){}", I, "type", "java.util.List");
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.Integer"); classAnnoMethod(n, "public void stop(){}", I, "type", "java.util.List");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "type") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", I, "type") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesClassMemberChanges
    @Test void threeClassesEachClassifyAMemberValue() throws Exception {
        CtClass aO = k("a.A"); classAnnoMethod(aO, "public void run(){}", D, "type", "java.lang.String");
        CtClass aN = k("a.A"); classAnnoMethod(aN, "public void run(){}", D, "type", "java.lang.Integer");
        CtClass bO = k("a.B"); nestedAnnoMethod(bO, "public void run(){}", D, "inner", I, "count", 1);
        CtClass bN = k("a.B"); nestedAnnoMethod(bN, "public void run(){}", D, "inner", I, "count", 1);
        CtClass cO = k("a.K"); markerMethod(cO, "public void run(){}", D);
        CtClass cN = k("a.K"); nestedAnnoMethod(cN, "public void run(){}", D, "inner", I, "count", 9);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(elemStatus(classNamed(r, "a.A"), "run", D, "type") == JApiChangeStatus.MODIFIED
                && elemStatus(classNamed(r, "a.B"), "run", D, "inner") == JApiChangeStatus.UNCHANGED
                && elemStatus(classNamed(r, "a.K"), "run", D, "inner") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aMarkerHasNoElements
    @Test void aMarkerHasNoElementsWhileAnotherMethodCarriesANested() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); nestedAnnoMethod(o, "public void stop(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); markerMethod(n, "public void run(){}", D); nestedAnnoMethod(n, "public void stop(){}", D, "inner", I, "count", 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnMethod(methodNamed(c, "run"), D).getElements().size() == 0
                && elemStatus(c, "stop", D, "inner") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::anAddedAnnotationCarryingAClassMemberIsNew
    @Test void anAddedClassAnnotationWhileANestedAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}"); nestedAnnoMethod(o, "public void stop(){}", D, "inner", I, "count", 1);
        CtClass n = k("a.C"); classAnnoMethod(n, "public void run(){}", D, "type", "java.lang.String"); plainMethod(n, "public void stop(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && annoStatus(c, "stop", D) == JApiChangeStatus.REMOVED);
    }
}
