package integration;

import static fixtures.Model.annotationNamed;
import static fixtures.Model.boolMember;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.elementCount;
import static fixtures.Model.elementNamed;
import static fixtures.Model.intMember;
import static fixtures.Model.marker;
import static fixtures.Model.method;
import static fixtures.Model.methodNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.stringMember;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining annotation member-value records with methods and sets of classes. */
class TreeTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception {
        return publicClass(pool(), n);
    }

    private static JApiChangeStatus elem(JApiClass c, String anno, String member) {
        return elementNamed(annotationNamed(c, anno), member).getChangeStatus();
    }

    // Depends-On: atomic::CompareTest::intValueChangeIsModified
    @Test void aMemberChangeAndANewMethodAreBothReflected() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::intValueUnchangedIsUnchanged
    @Test void anUnchangedMemberWithANewMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 5);
        CtClass n = k("a.C"); intMember(n, D, "count", 5); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::addedIntMemberIsNew
    @Test void anAddedMemberWithAnUnchangedMethod() throws Exception {
        CtClass o = k("a.C"); marker(o, D); method(o, "public void run(){}");
        CtClass n = k("a.C"); intMember(n, D, "count", 1); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::removedIntMemberIsRemoved
    @Test void aRemovedMemberWithARemovedMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); method(o, "public void run(){}");
        CtClass n = k("a.C"); marker(n, D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::stringValueChangeIsModified
    // Depends-On: atomic::CompareTest::intValueChangeIsModified
    @Test void twoMembersChangeAndAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 2); stringMember(n, D, "name", "y"); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED
                && elem(c, D, "name") == JApiChangeStatus.MODIFIED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeTracksItsOwnMember
    @Test void twoAnnotationTypesOneChangedOneUnchanged() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); intMember(o, I, "level", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); intMember(n, I, "level", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED && elem(c, I, "level") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachMemberChange
    @Test void oneClassMemberChangesWhileAnotherGainsAMethod() throws Exception {
        CtClass aO = k("a.A"); intMember(aO, D, "count", 1);
        CtClass aN = k("a.A"); intMember(aN, D, "count", 2);
        CtClass bO = k("a.B"); marker(bO, D);
        CtClass bN = k("a.B"); marker(bN, D); method(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elem(classNamed(r, "a.A"), D, "count") == JApiChangeStatus.MODIFIED
                && methodNamed(classNamed(r, "a.B"), "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::addingSecondMemberLeavesFirstUnchanged
    @Test void addingASecondMemberAndAMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 1); stringMember(n, D, "name", "x"); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.UNCHANGED
                && elem(c, D, "name") == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::boolValueChangeIsModified
    @Test void aBoolMemberChangeWithARemovedMethod() throws Exception {
        CtClass o = k("a.C"); boolMember(o, D, "flag", true); method(o, "public void run(){}");
        CtClass n = k("a.C"); boolMember(n, D, "flag", false);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "flag") == JApiChangeStatus.MODIFIED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::annotationWithAddedMemberIsModified
    @Test void annotationModifiedByMemberAndClassGetsANewMethod() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); intMember(n, D, "count", 1); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, D).getChangeStatus() == JApiChangeStatus.MODIFIED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::changingOneOfTwoMembers
    @Test void oneMemberChangesOneStaysAndAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 9); stringMember(n, D, "name", "x"); method(n, "public int size(){return 0;}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED
                && elem(c, D, "name") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "size").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachMemberChange
    @Test void perClassMemberClassificationAcrossASet() throws Exception {
        CtClass aO = k("a.A"); intMember(aO, D, "count", 1);
        CtClass aN = k("a.A"); intMember(aN, D, "count", 2);
        CtClass bO = k("a.B"); stringMember(bO, D, "name", "x");
        CtClass bN = k("a.B"); marker(bN, D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elem(classNamed(r, "a.A"), D, "count") == JApiChangeStatus.MODIFIED
                && elem(classNamed(r, "a.B"), D, "name") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::intValueChangeIsModified
    @Test void aNewClassCarryingAnnotatedMembersAndAMethod() throws Exception {
        CtClass n = k("a.C"); intMember(n, D, "count", 1); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::removedIntMemberIsRemoved
    @Test void aDeletedClassWithAnnotatedMembersAndAMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); method(o, "public void run(){}");
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::twoMembersCountIsTwo
    @Test void memberCountHoldsWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 2); stringMember(n, D, "name", "x"); method(n, "public void run(){}");
        assertTrue(elementCount(annotationNamed(onlyClass(compare(o, n)), D)) == 2);
    }

    // Depends-On: atomic::CompareTest::stringValueChangeIsModified
    @Test void aStringChangeOnTwoClasses() throws Exception {
        CtClass aO = k("a.A"); stringMember(aO, D, "name", "x");
        CtClass aN = k("a.A"); stringMember(aN, D, "name", "y");
        CtClass bO = k("a.B"); stringMember(bO, D, "name", "p");
        CtClass bN = k("a.B"); stringMember(bN, D, "name", "q");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elem(classNamed(r, "a.A"), D, "name") == JApiChangeStatus.MODIFIED
                && elem(classNamed(r, "a.B"), D, "name") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::annotationWithUnchangedMembersIsUnchanged
    @Test void anUnchangedAnnotationCoexistsWithAModifiedOne() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); intMember(o, I, "level", 5);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); intMember(n, I, "level", 5);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annotationNamed(c, D).getChangeStatus() == JApiChangeStatus.MODIFIED
                && annotationNamed(c, I).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::addedMemberAmongUnchangedOnes
    @Test void anAddedMemberAmongUnchangedWithANewMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 1); stringMember(n, D, "name", "x"); boolMember(n, D, "flag", true); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "flag") == JApiChangeStatus.NEW
                && elem(c, D, "count") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::boolValueChangeIsModified
    // Depends-On: atomic::CompareTest::intValueChangeIsModified
    @Test void aBoolAndIntMemberBothChangeWithAMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); boolMember(n, D, "flag", false); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED
                && elem(c, D, "flag") == JApiChangeStatus.MODIFIED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::removingOneOfTwoMembers
    @Test void removingOneMemberAndAddingAMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 1); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "name") == JApiChangeStatus.REMOVED
                && elem(c, D, "count") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeTracksItsOwnMember
    @Test void twoAnnotationTypesBothChangeMembers() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); intMember(o, I, "level", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); intMember(n, I, "level", 2);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED && elem(c, I, "level") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::intValueUnchangedIsUnchanged
    @Test void anUnchangedAnnotatedClassWithAnUnchangedMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 7); method(o, "public void run(){}");
        CtClass n = k("a.C"); intMember(n, D, "count", 7); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::changedMemberAmongUnchangedOnes
    @Test void aChangedMemberAmongUnchangedWithANewMethod() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x"); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); intMember(n, D, "count", 1); stringMember(n, D, "name", "z"); boolMember(n, D, "flag", true); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "name") == JApiChangeStatus.MODIFIED
                && elem(c, D, "flag") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoClassesWithDistinctMemberChanges
    @Test void twoClassesDistinctChangesOneAlsoGainsMethod() throws Exception {
        CtClass aO = k("a.A"); marker(aO, D);
        CtClass aN = k("a.A"); intMember(aN, D, "count", 1); method(aN, "public void run(){}");
        CtClass bO = k("a.B"); stringMember(bO, D, "name", "x");
        CtClass bN = k("a.B"); marker(bN, D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elem(classNamed(r, "a.A"), D, "count") == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.A"), "run").getChangeStatus() == JApiChangeStatus.NEW
                && elem(classNamed(r, "a.B"), D, "name") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aMarkerAnnotationOnBothSidesHasNoElements
    @Test void aMarkerAnnotationUnchangedWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); marker(n, D); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementCount(annotationNamed(c, D)) == 0
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::intValueChangeIsModified
    @Test void aMemberChangeWithAnUnchangedMethodAndAnUnchangedSecondAnnotation() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); intMember(o, I, "level", 3); method(o, "public void run(){}");
        CtClass n = k("a.C"); intMember(n, D, "count", 2); intMember(n, I, "level", 3); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED
                && elem(c, I, "level") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::stringValueUnchangedIsUnchanged
    @Test void anUnchangedStringMemberWithARemovedMethod() throws Exception {
        CtClass o = k("a.C"); stringMember(o, D, "name", "same"); method(o, "public void run(){}");
        CtClass n = k("a.C"); stringMember(n, D, "name", "same");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "name") == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }
}
