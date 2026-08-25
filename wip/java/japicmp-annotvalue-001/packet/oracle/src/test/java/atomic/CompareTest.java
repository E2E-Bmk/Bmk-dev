package atomic;

import static fixtures.Model.annotationNamed;
import static fixtures.Model.boolMember;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.elementCount;
import static fixtures.Model.elementNamed;
import static fixtures.Model.intMember;
import static fixtures.Model.marker;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.stringMember;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiAnnotation;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Single-owner checks over synthesised annotation member values. */
class CompareTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception {
        return publicClass(pool(), n);
    }

    private static JApiChangeStatus elem(JApiClass c, String anno, String member) {
        return elementNamed(annotationNamed(c, anno), member).getChangeStatus();
    }

    // ---- int member ----
    @Test void intValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), D, "count"));
    }
    @Test void intValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 5);
        CtClass n = k("a.C"); intMember(n, D, "count", 5);
        assertEquals(JApiChangeStatus.UNCHANGED, elem(onlyClass(compare(o, n)), D, "count"));
    }
    @Test void addedIntMemberIsNew() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); intMember(n, D, "count", 1);
        assertEquals(JApiChangeStatus.NEW, elem(onlyClass(compare(o, n)), D, "count"));
    }
    @Test void removedIntMemberIsRemoved() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); marker(n, D);
        assertEquals(JApiChangeStatus.REMOVED, elem(onlyClass(compare(o, n)), D, "count"));
    }
    @Test void intValueChangeMakesAnnotationModified() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, annotationNamed(onlyClass(compare(o, n)), D).getChangeStatus());
    }
    @Test void intMemberNameIsReported() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2);
        assertEquals("count", elementNamed(annotationNamed(onlyClass(compare(o, n)), D), "count").getName());
    }
    @Test void intValueChangeAtDifferentMember() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "size", 10);
        CtClass n = k("a.C"); intMember(n, D, "size", 20);
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), D, "size"));
    }
    @Test void intZeroToNonZeroIsModified() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 0);
        CtClass n = k("a.C"); intMember(n, D, "count", 3);
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), D, "count"));
    }

    // ---- string member ----
    @Test void stringValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); stringMember(n, D, "name", "y");
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), D, "name"));
    }
    @Test void stringValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); stringMember(o, D, "name", "same");
        CtClass n = k("a.C"); stringMember(n, D, "name", "same");
        assertEquals(JApiChangeStatus.UNCHANGED, elem(onlyClass(compare(o, n)), D, "name"));
    }
    @Test void addedStringMemberIsNew() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); stringMember(n, D, "name", "x");
        assertEquals(JApiChangeStatus.NEW, elem(onlyClass(compare(o, n)), D, "name"));
    }
    @Test void removedStringMemberIsRemoved() throws Exception {
        CtClass o = k("a.C"); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); marker(n, D);
        assertEquals(JApiChangeStatus.REMOVED, elem(onlyClass(compare(o, n)), D, "name"));
    }
    @Test void stringMemberNameIsReported() throws Exception {
        CtClass o = k("a.C"); stringMember(o, D, "label", "a");
        CtClass n = k("a.C"); stringMember(n, D, "label", "b");
        assertEquals("label", elementNamed(annotationNamed(onlyClass(compare(o, n)), D), "label").getName());
    }

    // ---- boolean member ----
    @Test void boolValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); boolMember(n, D, "flag", false);
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), D, "flag"));
    }
    @Test void boolValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); boolMember(n, D, "flag", true);
        assertEquals(JApiChangeStatus.UNCHANGED, elem(onlyClass(compare(o, n)), D, "flag"));
    }
    @Test void addedBoolMemberIsNew() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); boolMember(n, D, "flag", true);
        assertEquals(JApiChangeStatus.NEW, elem(onlyClass(compare(o, n)), D, "flag"));
    }
    @Test void removedBoolMemberIsRemoved() throws Exception {
        CtClass o = k("a.C"); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); marker(n, D);
        assertEquals(JApiChangeStatus.REMOVED, elem(onlyClass(compare(o, n)), D, "flag"));
    }

    // ---- counts and multiple members ----
    @Test void singleMemberCountIsOne() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2);
        assertEquals(1, elementCount(annotationNamed(onlyClass(compare(o, n)), D)));
    }
    @Test void twoMembersCountIsTwo() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 2); stringMember(n, D, "name", "x");
        assertEquals(2, elementCount(annotationNamed(onlyClass(compare(o, n)), D)));
    }
    @Test void addingSecondMemberLeavesFirstUnchanged() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 1); stringMember(n, D, "name", "x");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.UNCHANGED && elem(c, D, "name") == JApiChangeStatus.NEW);
    }
    @Test void removingOneOfTwoMembers() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.UNCHANGED && elem(c, D, "name") == JApiChangeStatus.REMOVED);
    }
    @Test void changingOneOfTwoMembers() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 9); stringMember(n, D, "name", "x");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED && elem(c, D, "name") == JApiChangeStatus.UNCHANGED);
    }

    // ---- annotation-level status ----
    @Test void annotationWithUnchangedMembersIsUnchanged() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 7);
        CtClass n = k("a.C"); intMember(n, D, "count", 7);
        assertEquals(JApiChangeStatus.UNCHANGED, annotationNamed(onlyClass(compare(o, n)), D).getChangeStatus());
    }
    @Test void annotationWithAddedMemberIsModified() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); intMember(n, D, "count", 1);
        assertEquals(JApiChangeStatus.MODIFIED, annotationNamed(onlyClass(compare(o, n)), D).getChangeStatus());
    }
    @Test void annotationWithRemovedMemberIsModified() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); marker(n, D);
        assertEquals(JApiChangeStatus.MODIFIED, annotationNamed(onlyClass(compare(o, n)), D).getChangeStatus());
    }
    @Test void aMarkerAnnotationOnBothSidesHasNoElements() throws Exception {
        CtClass o = k("a.C"); marker(o, D);
        CtClass n = k("a.C"); marker(n, D);
        assertEquals(0, elementCount(annotationNamed(onlyClass(compare(o, n)), D)));
    }

    // ---- multi-class ----
    @Test void aClassSetClassifiesEachMemberChange() throws Exception {
        CtClass aO = k("a.A"); intMember(aO, D, "count", 1);
        CtClass aN = k("a.A"); intMember(aN, D, "count", 2);
        CtClass bO = k("a.B"); stringMember(bO, D, "name", "x");
        CtClass bN = k("a.B"); stringMember(bN, D, "name", "x");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elem(classNamed(r, "a.A"), D, "count") == JApiChangeStatus.MODIFIED
                && elem(classNamed(r, "a.B"), D, "name") == JApiChangeStatus.UNCHANGED);
    }
    @Test void twoClassesWithDistinctMemberChanges() throws Exception {
        CtClass aO = k("a.A"); marker(aO, D);
        CtClass aN = k("a.A"); intMember(aN, D, "count", 1);
        CtClass bO = k("a.B"); stringMember(bO, D, "name", "x");
        CtClass bN = k("a.B"); marker(bN, D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(elem(classNamed(r, "a.A"), D, "count") == JApiChangeStatus.NEW
                && elem(classNamed(r, "a.B"), D, "name") == JApiChangeStatus.REMOVED);
    }
    @Test void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 1);
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }

    // ---- mixed / second annotation type ----
    @Test void intAndStringMembersBothChange() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 2); stringMember(n, D, "name", "y");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED && elem(c, D, "name") == JApiChangeStatus.MODIFIED);
    }
    @Test void aSecondAnnotationTypeTracksItsOwnMember() throws Exception {
        CtClass o = k("a.C"); intMember(o, I, "level", 1);
        CtClass n = k("a.C"); intMember(n, I, "level", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), I, "level"));
    }
    @Test void addedMemberAmongUnchangedOnes() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x");
        CtClass n = k("a.C"); intMember(n, D, "count", 1); stringMember(n, D, "name", "x"); boolMember(n, D, "flag", true);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "flag") == JApiChangeStatus.NEW && elem(c, D, "count") == JApiChangeStatus.UNCHANGED);
    }
    @Test void changedMemberAmongUnchangedOnes() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x"); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); intMember(n, D, "count", 1); stringMember(n, D, "name", "z"); boolMember(n, D, "flag", true);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "name") == JApiChangeStatus.MODIFIED && elem(c, D, "flag") == JApiChangeStatus.UNCHANGED);
    }
    @Test void aThreeMemberAnnotationCountsThree() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); stringMember(o, D, "name", "x"); boolMember(o, D, "flag", true);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); stringMember(n, D, "name", "x"); boolMember(n, D, "flag", true);
        assertEquals(3, elementCount(annotationNamed(onlyClass(compare(o, n)), D)));
    }
    @Test void aStringMemberUnchangedAcrossValue() throws Exception {
        CtClass o = k("a.C"); stringMember(o, D, "name", "hello");
        CtClass n = k("a.C"); stringMember(n, D, "name", "hello");
        assertEquals(JApiChangeStatus.UNCHANGED, elem(onlyClass(compare(o, n)), D, "name"));
    }
    @Test void aBoolFalseToTrueIsModified() throws Exception {
        CtClass o = k("a.C"); boolMember(o, D, "flag", false);
        CtClass n = k("a.C"); boolMember(n, D, "flag", true);
        assertEquals(JApiChangeStatus.MODIFIED, elem(onlyClass(compare(o, n)), D, "flag"));
    }
    @Test void anIntMemberOnSecondAnnotationUnchanged() throws Exception {
        CtClass o = k("a.C"); intMember(o, I, "level", 4);
        CtClass n = k("a.C"); intMember(n, I, "level", 4);
        assertEquals(JApiChangeStatus.UNCHANGED, elem(onlyClass(compare(o, n)), I, "level"));
    }
    @Test void twoAnnotationTypesEachWithAMember() throws Exception {
        CtClass o = k("a.C"); intMember(o, D, "count", 1); intMember(o, I, "level", 1);
        CtClass n = k("a.C"); intMember(n, D, "count", 2); intMember(n, I, "level", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elem(c, D, "count") == JApiChangeStatus.MODIFIED && elem(c, I, "level") == JApiChangeStatus.UNCHANGED);
    }
}
