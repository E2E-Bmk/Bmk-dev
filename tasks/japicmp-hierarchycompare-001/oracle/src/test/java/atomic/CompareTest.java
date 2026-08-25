package atomic;

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
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Single-owner checks over synthesised class-hierarchy shapes. */
class CompareTest {

    private static CtClass k(String name) throws Exception {
        return publicClass(pool(), name);
    }

    // ---- superclass owner ----

    @Test
    void aSuperclassChangeIsModified() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        assertEquals(JApiChangeStatus.MODIFIED, superOf(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void aSuperclassChangeReportsOldName() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        assertEquals("java.util.ArrayList", superOf(onlyClass(compare(o, n))).getSuperclassOld());
    }

    @Test
    void aSuperclassChangeReportsNewName() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        assertEquals("java.util.LinkedList", superOf(onlyClass(compare(o, n))).getSuperclassNew());
    }

    @Test
    void anUnchangedSuperclassIsUnchanged() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList");
        assertEquals(JApiChangeStatus.UNCHANGED, superOf(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void addingANonObjectSuperclassIsModified() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList");
        assertEquals(JApiChangeStatus.MODIFIED, superOf(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void removingANonObjectSuperclassIsModified() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.MODIFIED, superOf(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void aDefaultObjectSuperclassOnBothSidesIsUnchanged() throws Exception {
        assertEquals(JApiChangeStatus.UNCHANGED, superOf(onlyClass(compare(k("a.C"), k("a.C")))).getChangeStatus());
    }

    @Test
    void anAddedSuperclassReportsTheNewName() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList");
        assertEquals("java.util.ArrayList", superOf(onlyClass(compare(o, n))).getSuperclassNew());
    }

    @Test
    void aSuperclassChangeMakesTheClassModified() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // ---- interface owner ----

    @Test
    void anAddedInterfaceIsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable");
        assertEquals(JApiChangeStatus.NEW, interfaceNamed(onlyClass(compare(o, n)), "java.io.Serializable").getChangeStatus());
    }

    @Test
    void aRemovedInterfaceIsRemoved() throws Exception {
        CtClass o = k("a.C"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, interfaceNamed(onlyClass(compare(o, n)), "java.io.Serializable").getChangeStatus());
    }

    @Test
    void anUnchangedInterfaceIsUnchanged() throws Exception {
        CtClass o = k("a.C"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable");
        assertEquals(JApiChangeStatus.UNCHANGED, interfaceNamed(onlyClass(compare(o, n)), "java.io.Serializable").getChangeStatus());
    }

    @Test
    void anAddedInterfaceReportsItsFullyQualifiedName() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable");
        assertEquals("java.io.Serializable", interfaceNamed(onlyClass(compare(o, n)), "java.io.Serializable").getFullyQualifiedName());
    }

    @Test
    void twoAddedInterfacesAreBothNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable"); iface(n, "java.lang.Cloneable");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.NEW
                && interfaceNamed(c, "java.lang.Cloneable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void anInterfaceAddMakesTheClassModified() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void oneAddedAndOneRetainedInterfaceClassifyIndependently() throws Exception {
        CtClass o = k("a.C"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable"); iface(n, "java.lang.Cloneable");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(interfaceNamed(c, "java.io.Serializable").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && interfaceNamed(c, "java.lang.Cloneable").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void aClassWithNoInterfacesOnBothSidesHasNoInterfaceRecords() throws Exception {
        assertTrue(onlyClass(compare(k("a.C"), k("a.C"))).getInterfaces().isEmpty());
    }

    // ---- constructor owner ----

    @Test
    void anAddedConstructorIsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}");
        assertEquals(JApiChangeStatus.NEW, firstConstructor(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void aRemovedConstructorIsRemoved() throws Exception {
        CtClass o = k("a.C"); constructor(o, "public C(int x){}");
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, firstConstructor(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void anUnchangedConstructorIsUnchanged() throws Exception {
        CtClass o = k("a.C"); constructor(o, "public C(int x){}");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}");
        assertEquals(JApiChangeStatus.UNCHANGED, firstConstructor(onlyClass(compare(o, n))).getChangeStatus());
    }

    @Test
    void addingAConstructorRaisesTheConstructorCount() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}");
        assertEquals(1, constructorCount(onlyClass(compare(o, n))));
    }

    @Test
    void aConstructorAddMakesTheClassModified() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void anAddedConstructorHasEmptyOldConstructorOptional() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}");
        assertFalse(firstConstructor(onlyClass(compare(o, n))).getOldConstructor().isPresent());
    }

    @Test
    void twoAddedConstructorsRaiseCountToTwo() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); constructor(n, "public C(int x){}"); constructor(n, "public C(long y){}");
        assertEquals(2, constructorCount(onlyClass(compare(o, n))));
    }

    @Test
    void aRemovedConstructorHasEmptyNewConstructorOptional() throws Exception {
        CtClass o = k("a.C"); constructor(o, "public C(int x){}");
        CtClass n = k("a.C");
        assertFalse(firstConstructor(onlyClass(compare(o, n))).getNewConstructor().isPresent());
    }

    // ---- class-level status from hierarchy ----

    @Test
    void aClassPresentOnBothSidesWithSameHierarchyIsUnchanged() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList"); iface(o, "java.io.Serializable");
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList"); iface(n, "java.io.Serializable");
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void aBrandNewClassIsNew() throws Exception {
        assertEquals(JApiChangeStatus.NEW, onlyClass(compare(null, k("a.C"))).getChangeStatus());
    }

    @Test
    void aDeletedClassIsRemoved() throws Exception {
        assertEquals(JApiChangeStatus.REMOVED, onlyClass(compare(k("a.C"), null)).getChangeStatus());
    }

    @Test
    void theFullyQualifiedNameIsReported() throws Exception {
        assertEquals("a.C", onlyClass(compare(k("a.C"), k("a.C"))).getFullyQualifiedName());
    }

    @Test
    void aClassPresentOnBothSidesHasBothClassOptionals() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C"), k("a.C")));
        assertTrue(c.getOldClass().isPresent() && c.getNewClass().isPresent());
    }

    @Test
    void aNewClassHasEmptyOldClassOptional() throws Exception {
        assertFalse(onlyClass(compare(null, k("a.C"))).getOldClass().isPresent());
    }

    @Test
    void aRemovedClassHasEmptyNewClassOptional() throws Exception {
        assertFalse(onlyClass(compare(k("a.C"), null)).getNewClass().isPresent());
    }

    @Test
    void aNewClassWithASuperclassStillReportsNew() throws Exception {
        CtClass n = k("a.C"); superclass(n, "java.util.ArrayList");
        assertEquals(JApiChangeStatus.NEW, onlyClass(compare(null, n)).getChangeStatus());
    }

    @Test
    void twoDistinctClassesProduceTwoRecords() throws Exception {
        List<JApiClass> r = compareAll(Arrays.asList(k("a.B")), Arrays.asList(k("a.C")));
        assertEquals(2, r.size());
    }

    @Test
    void anAddedInterfaceAndConstructorTogetherMakeTheClassModified() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); iface(n, "java.io.Serializable"); constructor(n, "public C(int x){}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void aClassNamedLookupFindsTheRecord() throws Exception {
        List<JApiClass> r = compareAll(Arrays.asList(k("a.One"), k("a.Two")), Arrays.asList(k("a.One"), k("a.Two")));
        assertTrue(classNamed(r, "a.One") != null && classNamed(r, "a.Two") != null);
    }

    @Test
    void aClassTypeRecordIsPresent() throws Exception {
        assertTrue(onlyClass(compare(k("a.C"), k("a.C"))).getClassType() != null);
    }

    @Test
    void aSuperclassAndInterfaceChangeBothMakeTheClassModified() throws Exception {
        CtClass o = k("a.C"); superclass(o, "java.util.ArrayList");
        CtClass n = k("a.C"); superclass(n, "java.util.LinkedList"); iface(n, "java.io.Serializable");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }
}
