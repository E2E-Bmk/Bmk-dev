package atomic;

import fixtures.Bytecode;
import fixtures.Compare;
import javassist.ClassPool;
import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.plumbline.model.JApiChangeStatus;
import org.plumbline.model.JApiClass;
import org.plumbline.model.JApiCompatibilityChangeType;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The comparison tree: how a pair of versioned classes becomes one model, and what
 * status each element carries.
 *
 * <p>Every test drives the two declared entry points and reads declared
 * accessors, so a reimplementation that arranges its internals differently still
 * passes.
 */
class TreeTest {

    /** Seam: two identical shapes. Verifies: JAPI-TREE-001. */
    @Test
    void aClassPresentAndUnchangedInBothVersionsIsUnchanged() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void run() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertEquals(JApiChangeStatus.UNCHANGED, service.getChangeStatus());
        assertTrue(service.isBinaryCompatible());
    }

    /** Seam: a name only the old version declares. Verifies: JAPI-TREE-002. */
    @Test
    void aClassOnlyTheOldVersionDeclaresIsRemoved() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Gone");
        Bytecode.method(before, "public void run() {}");

        JApiClass gone = Compare.only(Compare.compare(before, null));

        assertEquals(JApiChangeStatus.REMOVED, gone.getChangeStatus());
        assertTrue(gone.getOldClass().isPresent());
        assertFalse(gone.getNewClass().isPresent());
        assertTrue(Compare.changeTypes(gone).contains(JApiCompatibilityChangeType.CLASS_REMOVED));
        assertFalse(gone.isBinaryCompatible());
    }

    /** Seam: a name only the new version declares. Verifies: JAPI-TREE-003. */
    @Test
    void aClassOnlyTheNewVersionDeclaresIsNew() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Fresh");
        Bytecode.method(after, "public void run() {}");

        JApiClass fresh = Compare.only(Compare.compare(null, after));

        assertEquals(JApiChangeStatus.NEW, fresh.getChangeStatus());
        assertFalse(fresh.getOldClass().isPresent());
        assertTrue(fresh.getNewClass().isPresent());
        assertTrue(fresh.isBinaryCompatible());
    }

    /** Seam: the fully qualified name is preserved on the merged element. Verifies: JAPI-TREE-004. */
    @Test
    void theComparedClassKeepsItsFullyQualifiedName() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.deep.Nested");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.deep.Nested");

        JApiClass nested = Compare.only(Compare.compare(before, after));

        assertEquals("com.acme.deep.Nested", nested.getFullyQualifiedName());
    }

    /** Seam: a removed method propagates MODIFIED up to its class. Verifies: JAPI-TREE-005. */
    @Test
    void removingAMethodMakesTheOwningClassModified() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        Bytecode.method(before, "public void stay() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void stay() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertEquals(JApiChangeStatus.MODIFIED, service.getChangeStatus());
    }

    /** Seam: the removed member itself carries REMOVED. Verifies: JAPI-TREE-006. */
    @Test
    void theRemovedMethodElementIsRemovedWhileItsSiblingIsUnchanged() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        Bytecode.method(before, "public void stay() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void stay() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertEquals(JApiChangeStatus.REMOVED, Compare.method(service, "run").orElseThrow().getChangeStatus());
        assertEquals(JApiChangeStatus.UNCHANGED, Compare.method(service, "stay").orElseThrow().getChangeStatus());
    }

    /** Seam: an added method is NEW on the member and MODIFIED on the class. Verifies: JAPI-TREE-007. */
    @Test
    void theAddedMethodElementIsNew() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void stay() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void stay() {}");
        Bytecode.method(after, "public void extra() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertEquals(JApiChangeStatus.MODIFIED, service.getChangeStatus());
        assertEquals(JApiChangeStatus.NEW, Compare.method(service, "extra").orElseThrow().getChangeStatus());
    }

    /** Seam: fields are compared alongside methods. Verifies: JAPI-TREE-008. */
    @Test
    void aRemovedFieldElementIsRemoved() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Holder");
        Bytecode.field(before, "public int count;");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Holder");

        JApiClass holder = Compare.only(Compare.compare(before, after));

        assertEquals(JApiChangeStatus.REMOVED, Compare.field(holder, "count").orElseThrow().getChangeStatus());
    }

    /** Seam: several names in one comparison stay separate elements. Verifies: JAPI-TREE-009. */
    @Test
    void eachComparedNameBecomesItsOwnElement() throws Exception {
        ClassPool oldPool = Bytecode.pool();
        ClassPool newPool = Bytecode.pool();
        CtClass keptOld = Bytecode.publicClass(oldPool, "com.acme.Kept");
        CtClass droppedOld = Bytecode.publicClass(oldPool, "com.acme.Dropped");
        CtClass keptNew = Bytecode.publicClass(newPool, "com.acme.Kept");

        List<JApiClass> tree = new org.plumbline.cmp.JarArchiveComparator(Compare.publicOnly())
                .compareClassLists(Compare.publicOnly(),
                        List.of(keptOld, droppedOld), List.of(keptNew));

        assertEquals(JApiChangeStatus.UNCHANGED, Compare.named(tree, "com.acme.Kept").getChangeStatus());
        assertEquals(JApiChangeStatus.REMOVED, Compare.named(tree, "com.acme.Dropped").getChangeStatus());
    }

    /** Seam: the compared elements expose the versions they came from. Verifies: JAPI-TREE-010. */
    @Test
    void anUnchangedClassExposesBothVersions() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertTrue(service.getOldClass().isPresent());
        assertTrue(service.getNewClass().isPresent());
    }
}
