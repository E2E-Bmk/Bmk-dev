package integration;

import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.field;
import static fixtures.Model.fieldNamed;
import static fixtures.Model.method;
import static fixtures.Model.methodNamed;
import static fixtures.Model.classNamed;
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

/** Cross-owner checks over whole comparison trees. */
class TreeTest {

    private static CtClass klass(String name) throws Exception {
        return publicClass(pool(), name);
    }

    // Depends-On: atomic::CompareTest::aClassWithAnAddedMethodIsModified
    @Test
    void aClassWithAnAddedMethodAndFieldIsModifiedWithBothMembersNew() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        method(n, "public void stop() {}");
        field(n, "public int count;");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.MODIFIED, c.getChangeStatus());
        assertEquals(JApiChangeStatus.NEW, methodNamed(c, "stop").getChangeStatus());
        assertEquals(JApiChangeStatus.NEW, fieldNamed(c, "count").getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aMethodPresentOnBothSidesUnchangedIsUnchanged
    @Test
    void anUnchangedClassHasEveryMemberUnchanged() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        field(n, "public int count;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && fieldNamed(c, "count").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::twoDistinctClassesProduceTwoRecords
    @Test
    void aSetWithOneAddedAndOneRemovedClassReportsBoth() throws Exception {
        List<JApiClass> r = compareAll(Arrays.asList(klass("a.Old")), Arrays.asList(klass("a.New")));
        assertEquals(JApiChangeStatus.REMOVED, classNamed(r, "a.Old").getChangeStatus());
        assertEquals(JApiChangeStatus.NEW, classNamed(r, "a.New").getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesIsUnchanged
    @Test
    void aSetWithAnUnchangedAndAModifiedClassClassifiesEachIndependently() throws Exception {
        CtClass sameO = klass("a.Same");
        CtClass sameN = klass("a.Same");
        CtClass modO = klass("a.Mod");
        CtClass modN = klass("a.Mod");
        method(modN, "public void x() {}");
        List<JApiClass> r = compareAll(Arrays.asList(sameO, modO), Arrays.asList(sameN, modN));
        assertEquals(JApiChangeStatus.UNCHANGED, classNamed(r, "a.Same").getChangeStatus());
        assertEquals(JApiChangeStatus.MODIFIED, classNamed(r, "a.Mod").getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aMethodAccessChangeIsModified
    @Test
    void aMethodAccessChangeMakesTheEnclosingClassModified() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "protected void run() {}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::anAddedMethodIsNew
    @Test
    void aMixedClassKeepsUnchangedMembersUnchangedWhileFlaggingNewOnes() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void keep() {}");
        CtClass n = klass("a.B");
        method(n, "public void keep() {}");
        method(n, "public void add() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "keep").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "add").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedMethodIsRemoved
    @Test
    void aClassLosingAMethodIsModifiedAndTheMethodRemoved() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        method(o, "public void keep() {}");
        CtClass n = klass("a.B");
        method(n, "public void keep() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.MODIFIED, c.getChangeStatus());
        assertEquals(JApiChangeStatus.REMOVED, methodNamed(c, "run").getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::anAddedFieldIsNew
    @Test
    void addingAFieldAndAMethodInOneClassFlagsBothNew() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        field(n, "public int f;");
        method(n, "public void m() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(fieldNamed(c, "f").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "m").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aStaticFieldToInstanceFieldIsModified
    @Test
    void aFieldStaticChangeMakesTheClassModified() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public static int count;");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aClassWithOnlyUnchangedMembersIsUnchanged
    @Test
    void aClassWithManyUnchangedMembersStaysUnchanged() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        for (CtClass cc : new CtClass[] {o, n}) {
            method(cc, "public void a() {}");
            method(cc, "public void b() {}");
            field(cc, "public int f;");
        }
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aClassOnlyOnTheNewSideIsNew
    @Test
    void aBrandNewClassWithMembersHasEveryMemberNew() throws Exception {
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        field(n, "public int count;");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW
                && fieldNamed(c, "count").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassOnlyOnTheOldSideIsRemoved
    @Test
    void aDeletedClassWithMembersHasEveryMemberRemoved() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        field(o, "public int count;");
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED
                && fieldNamed(c, "count").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aMethodAccessModifierRecordsOldAndNewValues
    @Test
    void anAccessWideningIsReflectedInBothModifierAndClassStatus() throws Exception {
        CtClass o = klass("a.B");
        method(o, "protected void run() {}");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.MODIFIED, c.getChangeStatus());
        assertEquals(JApiChangeStatus.MODIFIED, methodNamed(c, "run").getAccessModifier().getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::severalAddedFieldsAreEachNew
    @Test
    void addingThreeFieldsFlagsAllThreeNew() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        field(n, "public int a;");
        field(n, "public int b;");
        field(n, "public int c;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(fieldNamed(c, "a").getChangeStatus() == JApiChangeStatus.NEW
                && fieldNamed(c, "b").getChangeStatus() == JApiChangeStatus.NEW
                && fieldNamed(c, "c").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesHasBothClassOptionals
    @Test
    void aModifiedClassStillCarriesBothClassHandles() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getOldClass().isPresent() && c.getNewClass().isPresent());
    }

    // Depends-On: atomic::CompareTest::aFinalFieldChangeIsRecordedOnTheFinalModifier
    @Test
    void aFinalToNonFinalFieldChangeModifiesTheClass() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public final int count = 1;");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::theFullyQualifiedNameIsReported
    @Test
    void eachRecordInASetKeepsItsOwnName() throws Exception {
        List<JApiClass> r = compareAll(
                Arrays.asList(klass("a.One"), klass("a.Two")),
                Arrays.asList(klass("a.One"), klass("a.Two")));
        assertTrue(classNamed(r, "a.One") != null && classNamed(r, "a.Two") != null);
    }

    // Depends-On: atomic::CompareTest::aMethodPresentOnBothSidesUnchangedIsUnchanged
    @Test
    void anOverloadSetWithOneChangedOverloadModifiesTheClass() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        method(o, "public void run(int x) {}");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        method(n, "protected void run(int x) {}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::anUnchangedEmptyClassHasNoMethods
    @Test
    void twoEmptyClassesCompareAsUnchangedWithNoMembers() throws Exception {
        JApiClass c = onlyClass(compare(klass("a.B"), klass("a.B")));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.UNCHANGED
                && c.getMethods().isEmpty() && c.getFields().isEmpty());
    }

    // Depends-On: atomic::CompareTest::aClassWithAnAddedMethodIsModified
    @Test
    void addingAMethodToOneOfTwoClassesModifiesOnlyThatClass() throws Exception {
        CtClass aO = klass("a.A");
        CtClass aN = klass("a.A");
        CtClass bO = klass("a.B");
        CtClass bN = klass("a.B");
        method(bN, "public void run() {}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertEquals(JApiChangeStatus.UNCHANGED, classNamed(r, "a.A").getChangeStatus());
        assertEquals(JApiChangeStatus.MODIFIED, classNamed(r, "a.B").getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::anAddedMethodHasEmptyOldMethodOptional
    @Test
    void anAddedMethodInAModifiedClassHasNoOldHandle() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void keep() {}");
        CtClass n = klass("a.B");
        method(n, "public void keep() {}");
        method(n, "public void fresh() {}");
        assertTrue(!methodNamed(onlyClass(compare(o, n)), "fresh").getOldMethod().isPresent());
    }

    // Depends-On: atomic::CompareTest::aRemovedFieldIsRemoved
    @Test
    void removingOneOfTwoFieldsModifiesTheClass() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int a;");
        field(o, "public int b;");
        CtClass n = klass("a.B");
        field(n, "public int a;");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.MODIFIED, c.getChangeStatus());
        assertEquals(JApiChangeStatus.REMOVED, fieldNamed(c, "b").getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aNewClassHasEmptyOldClassOptional
    @Test
    void aNewClassInASetHasNoOldHandle() throws Exception {
        List<JApiClass> r = compareAll(java.util.Collections.<CtClass>emptyList(), Arrays.asList(klass("a.Fresh")));
        assertTrue(!classNamed(r, "a.Fresh").getOldClass().isPresent());
    }

    // Depends-On: atomic::CompareTest::aClassWithOnlyUnchangedMembersIsUnchanged
    @Test
    void reorderingMemberDeclarationsDoesNotChangeTheClass() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void a() {}");
        method(o, "public void b() {}");
        CtClass n = klass("a.B");
        method(n, "public void b() {}");
        method(n, "public void a() {}");
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aStaticModifierRecordsNonStaticToStatic
    @Test
    void makingAFieldStaticIsRecordedOnTheModifierAndClass() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        field(n, "public static int count;");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.MODIFIED, c.getChangeStatus());
        assertEquals(JApiChangeStatus.MODIFIED, fieldNamed(c, "count").getStaticModifier().getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesIsUnchanged
    @Test
    void anIdenticalMultiMemberClassSetIsAllUnchanged() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        for (CtClass cc : new CtClass[] {o, n}) {
            method(cc, "public int compute(int x) { return x; }");
            field(cc, "public String name;");
        }
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.UNCHANGED, c.getChangeStatus());
    }
}
