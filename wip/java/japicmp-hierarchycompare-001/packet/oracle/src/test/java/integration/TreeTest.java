package integration;

import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.constructor;
import static fixtures.Model.constructorCount;
import static fixtures.Model.firstConstructor;
import static fixtures.Model.iface;
import static fixtures.Model.interfaceNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.superOf;
import static fixtures.Model.superclass;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks over whole comparison trees for the hierarchy surface. */
class TreeTest {

    private static CtClass k(String name) throws Exception {
        return publicClass(pool(), name);
    }

    // Depends-On: atomic::CompareTest::aSuperclassChangeIsModified
    // Depends-On: atomic::CompareTest::anAddedInterfaceIsNew
    @Test
    void aSuperclassChangeAndAddedInterfaceAreBothReflected() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.lang.ClassLoader");
        CtClass n = k("a.C"); superclass(n, "java.lang.ThreadLocal"); iface(n, "java.io.Serializable");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(superOf(c).getChangeStatus() == JApiChangeStatus.MODIFIED
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAddedConstructorIsNew
    // Depends-On: atomic::CompareTest::anAddedInterfaceIsNew
    @Test
    void anAddedConstructorAndInterfaceAreBothNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}"); iface(n, "java.io.Serializable");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(firstConstructor(c).getChangeStatus() == JApiChangeStatus.NEW
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSuperclassChangeIsModified
    // Depends-On: atomic::CompareTest::aSuperclassChangeMakesTheClassModified
    @Test
    void aSuperclassChangeShowsOnBothTheRecordAndTheClass() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.MODIFIED
                && superOf(c).getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesWithSameHierarchyIsUnchanged
    @Test
    void aFullyUnchangedHierarchyKeepsEveryOwnerUnchanged() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList"); iface(o, "java.io.Serializable"); constructor(o, "public C(int x){}");
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList"); iface(n, "java.io.Serializable"); constructor(n, "public C(int x){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.UNCHANGED
                && superOf(c).getChangeStatus() == JApiChangeStatus.UNCHANGED
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && firstConstructor(c).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anAddedInterfaceIsNew
    // Depends-On: atomic::CompareTest::aRemovedInterfaceIsRemoved
    @Test
    void oneAddedAndOneRemovedInterfaceReportBoth() throws Exception {
        CtClass o = k("a.C"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C"); iface(n, "java.lang.Cloneable");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.REMOVED
                && interfaceNamed(c, "java.lang.Cloneable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoDistinctClassesProduceTwoRecords
    // Depends-On: atomic::CompareTest::aBrandNewClassIsNew
    @Test
    void aSetWithOneAddedAndOneRemovedClassReportsBoth() throws Exception {
        List<JApiClass> r = compareAll(Arrays.asList(k("a.Old")), Arrays.asList(k("a.New")));
        assertTrue(classNamed(r, "a.Old").getChangeStatus() == JApiChangeStatus.REMOVED
                && classNamed(r, "a.New").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesWithSameHierarchyIsUnchanged
    // Depends-On: atomic::CompareTest::aSuperclassChangeMakesTheClassModified
    @Test
    void aSetWithAnUnchangedAndAModifiedClassClassifiesEachIndependently() throws Exception {
        CtClass sameO = k("a.Same");
        CtClass sameN = k("a.Same");
        CtClass modO = k("a.Mod"); superclass(modO, "java.util.ArrayList");
        CtClass modN = k("a.Mod"); superclass(modN, "java.util.LinkedList");
        List<JApiClass> r = compareAll(Arrays.asList(sameO, modO), Arrays.asList(sameN, modN));
        assertTrue(classNamed(r, "a.Same").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && classNamed(r, "a.Mod").getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::anAddedConstructorIsNew
    // Depends-On: atomic::CompareTest::addingAConstructorRaisesTheConstructorCount
    @Test
    void addingAConstructorFlagsItNewAndRaisesTheCount() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(firstConstructor(c).getChangeStatus() == JApiChangeStatus.NEW && constructorCount(c) == 1);
    }

    // Depends-On: atomic::CompareTest::aSuperclassChangeIsModified
    // Depends-On: atomic::CompareTest::anAddedConstructorIsNew
    @Test
    void aSuperclassChangeWithANewConstructorReflectsBoth() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList"); constructor(n, "public C(int x){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(superOf(c).getChangeStatus() == JApiChangeStatus.MODIFIED
                && firstConstructor(c).getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anInterfaceAddMakesTheClassModified
    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesWithSameHierarchyIsUnchanged
    @Test
    void addingAnInterfaceToOneOfTwoClassesModifiesOnlyThatClass() throws Exception {
        CtClass aO = k("a.A");
        CtClass aN = k("a.A");
        CtClass bO = k("a.B");
        CtClass bN = k("a.B"); iface(bN, "java.io.Serializable");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(classNamed(r, "a.A").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && classNamed(r, "a.B").getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aSuperclassChangeReportsOldName
    // Depends-On: atomic::CompareTest::aSuperclassChangeReportsNewName
    @Test
    void aSuperclassChangeCarriesBothOldAndNewNames() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(superOf(c).getSuperclassOld().equals("java.util.ArrayList")
                && superOf(c).getSuperclassNew().equals("java.util.LinkedList"));
    }

    // Depends-On: atomic::CompareTest::twoAddedInterfacesAreBothNew
    // Depends-On: atomic::CompareTest::anInterfaceAddMakesTheClassModified
    @Test
    void addingTwoInterfacesFlagsBothNewAndModifiesTheClass() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable"); iface(n, "java.lang.Cloneable");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.MODIFIED
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.NEW
                && interfaceNamed(c, "java.lang.Cloneable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aBrandNewClassIsNew
    // Depends-On: atomic::CompareTest::anAddedInterfaceIsNew
    @Test
    void aBrandNewClassWithAnInterfaceIsNewWithThatInterfaceNew() throws Exception {
        CtClass n = k("a.C"); iface(n, "java.io.Serializable");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.NEW
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aDeletedClassIsRemoved
    // Depends-On: atomic::CompareTest::aRemovedConstructorIsRemoved
    @Test
    void aDeletedClassWithAConstructorIsRemovedWithThatConstructorRemoved() throws Exception {
        CtClass o = k("a.C"); constructor(o, "public C(int x){}");
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.REMOVED
                && firstConstructor(c).getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aRemovedInterfaceIsRemoved
    // Depends-On: atomic::CompareTest::anInterfaceAddMakesTheClassModified
    @Test
    void removingAnInterfaceModifiesTheClass() throws Exception {
        CtClass o = k("a.C"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.MODIFIED
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::removingANonObjectSuperclassIsModified
    @Test
    void removingASuperclassModifiesBothRecordAndClass() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.MODIFIED
                && superOf(c).getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aClassNamedLookupFindsTheRecord
    @Test
    void eachRecordInASetKeepsItsOwnName() throws Exception {
        List<JApiClass> r = compareAll(
                Arrays.asList(k("a.One"), k("a.Two")),
                Arrays.asList(k("a.One"), k("a.Two")));
        assertTrue(classNamed(r, "a.One") != null && classNamed(r, "a.Two") != null);
    }

    // Depends-On: atomic::CompareTest::twoAddedConstructorsRaiseCountToTwo
    @Test
    void addingTwoOverloadedConstructorsRaisesCountToTwo() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}"); constructor(n, "public C(long y){}");
        assertEquals(2, constructorCount(onlyClass(compare(o, n))));
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesWithSameHierarchyIsUnchanged
    @Test
    void reorderingInterfaceDeclarationsDoesNotChangeTheClass() throws Exception {
        CtClass o = k("a.C"); iface(o, "java.io.Serializable"); iface(o, "java.lang.Cloneable");
        CtClass n = k("a.C"); iface(n, "java.lang.Cloneable"); iface(n, "java.io.Serializable");
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // Depends-On: atomic::CompareTest::aSuperclassChangeMakesTheClassModified
    // Depends-On: atomic::CompareTest::anInterfaceAddMakesTheClassModified
    @Test
    void aSimultaneousSuperclassAndInterfaceChangeModifiesTheClassOnce() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.lang.ClassLoader"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C"); superclass(n, "java.lang.ThreadLocal");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.MODIFIED
                && superOf(c).getChangeStatus() == JApiChangeStatus.MODIFIED
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesWithSameHierarchyIsUnchanged
    @Test
    void identicalMultiOwnerClassesAcrossASetAreAllUnchanged() throws Exception {
        CtClass o1 = k("a.One"); superclass(o1, "java.util.ArrayList");
        CtClass n1 = k("a.One"); superclass(n1, "java.util.ArrayList");
        CtClass o2 = k("a.Two"); iface(o2, "java.io.Serializable");
        CtClass n2 = k("a.Two"); iface(n2, "java.io.Serializable");
        List<JApiClass> r = compareAll(Arrays.asList(o1, o2), Arrays.asList(n1, n2));
        assertTrue(classNamed(r, "a.One").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && classNamed(r, "a.Two").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::addingANonObjectSuperclassIsModified
    @Test
    void addingASuperclassWhereThereWasNoneModifiesTheClass() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getChangeStatus() == JApiChangeStatus.MODIFIED
                && superOf(c).getSuperclassNew().equals("java.util.ArrayList"));
    }

    // Depends-On: atomic::CompareTest::anAddedConstructorIsNew
    // Depends-On: atomic::CompareTest::anUnchangedConstructorIsUnchanged
    @Test
    void aRetainedConstructorStaysUnchangedWhileANewOneIsFlagged() throws Exception {
        CtClass o = k("a.C"); constructor(o, "public C(int x){}");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}"); constructor(n, "public C(long y){}");
        assertEquals(2, constructorCount(onlyClass(compare(o, n))));
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesHasBothClassOptionals
    // Depends-On: atomic::CompareTest::aSuperclassChangeMakesTheClassModified
    @Test
    void aModifiedClassStillCarriesBothClassHandles() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(c.getOldClass().isPresent() && c.getNewClass().isPresent());
    }

    // Depends-On: atomic::CompareTest::anAddedInterfaceReportsItsFullyQualifiedName
    @Test
    void anAddedInterfaceRecordExposesItsName() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.lang.Cloneable");
        assertEquals("java.lang.Cloneable", interfaceNamed(onlyClass(compare(o, n)), "java.lang.Cloneable").getFullyQualifiedName());
    }

    // Depends-On: atomic::CompareTest::aSuperclassChangeIsModified
    // Depends-On: atomic::CompareTest::anAddedInterfaceIsNew
    // Depends-On: atomic::CompareTest::anAddedConstructorIsNew
    @Test
    void allThreeOwnersChangingTogetherAreEachReflected() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.lang.ClassLoader");
        CtClass n = k("a.C"); superclass(n, "java.lang.ThreadLocal"); iface(n, "java.io.Serializable"); constructor(n, "public C(int x){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(superOf(c).getChangeStatus() == JApiChangeStatus.MODIFIED
                && interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.NEW
                && firstConstructor(c).getChangeStatus() == JApiChangeStatus.NEW);
    }
}
