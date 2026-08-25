package atomic;

import fixtures.Bytecode;
import fixtures.Compare;
import javassist.ClassPool;
import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.plumbline.model.JApiClass;
import org.plumbline.model.JApiCompatibilityChangeType;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Classifying a change against the compatibility rules: which change type a shape
 * difference yields, and whether it leaves the API binary compatible.
 *
 * <p>The library decides these itself rather than delegating to a compiler, so the
 * verdicts are the behaviour under test.
 */
class RuleTest {

    /** Seam: a removed public method. Verifies: JAPI-RULE-001. */
    @Test
    void removingAPublicMethodIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(Compare.method(service, "run").orElseThrow())
                .contains(JApiCompatibilityChangeType.METHOD_REMOVED));
        assertFalse(service.isBinaryCompatible());
    }

    /** Seam: a removed public field. Verifies: JAPI-RULE-002. */
    @Test
    void removingAPublicFieldIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Holder");
        Bytecode.field(before, "public int count;");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Holder");

        JApiClass holder = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(Compare.field(holder, "count").orElseThrow())
                .contains(JApiCompatibilityChangeType.FIELD_REMOVED));
        assertFalse(holder.isBinaryCompatible());
    }

    /** Seam: a class that stops being extendable. Verifies: JAPI-RULE-003. */
    @Test
    void makingAClassFinalIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Base");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Base");
        Bytecode.method(after, "public void run() {}");
        Bytecode.makeFinal(after);

        JApiClass base = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(base)
                .contains(JApiCompatibilityChangeType.CLASS_NOW_NOT_EXTENDABLE));
        assertFalse(base.isBinaryCompatible());
    }

    /** Seam: a class that stops being public. Verifies: JAPI-RULE-004. */
    @Test
    void makingAClassPackagePrivateIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Exposed");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Exposed");
        Bytecode.method(after, "public void run() {}");
        Bytecode.makePackagePrivate(after);

        JApiClass exposed = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(exposed)
                .contains(JApiCompatibilityChangeType.CLASS_NO_LONGER_PUBLIC));
        assertFalse(exposed.isBinaryCompatible());
    }

    /** Seam: an added method keeps callers linking. Verifies: JAPI-RULE-005. */
    @Test
    void addingAMethodToAClassStaysBinaryCompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void run() {}");
        Bytecode.method(after, "public void extra() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertTrue(service.isBinaryCompatible());
    }

    /** Seam: a method that becomes final. Verifies: JAPI-RULE-006. */
    @Test
    void makingAMethodFinalIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public final void run() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(Compare.method(service, "run").orElseThrow())
                .contains(JApiCompatibilityChangeType.METHOD_NOW_FINAL));
        assertFalse(service.isBinaryCompatible());
    }

    /** Seam: a method that becomes static. Verifies: JAPI-RULE-007. */
    @Test
    void makingAMethodStaticIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public static void run() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(Compare.method(service, "run").orElseThrow())
                .contains(JApiCompatibilityChangeType.METHOD_NOW_STATIC));
        assertFalse(service.isBinaryCompatible());
    }

    /** Seam: a field whose declared type changes. Verifies: JAPI-RULE-008. */
    @Test
    void changingAFieldTypeIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Holder");
        Bytecode.field(before, "public int count;");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Holder");
        Bytecode.field(after, "public long count;");

        JApiClass holder = Compare.only(Compare.compare(before, after));

        assertTrue(Compare.changeTypes(Compare.field(holder, "count").orElseThrow())
                .contains(JApiCompatibilityChangeType.FIELD_TYPE_CHANGED));
        assertFalse(holder.isBinaryCompatible());
    }

    /** Seam: a method whose return type changes. Verifies: JAPI-RULE-009. */
    @Test
    void changingAMethodReturnTypeIsBinaryIncompatible() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public int size() { return 0; }");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public long size() { return 0L; }");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertFalse(service.isBinaryCompatible());
    }

    /** Seam: an unchanged class carries no change entry at all. Verifies: JAPI-RULE-010. */
    @Test
    void anUnchangedClassCarriesNoCompatibilityChange() throws Exception {
        ClassPool[] pools = Compare.pools();
        CtClass before = Bytecode.publicClass(pools[0], "com.acme.Service");
        Bytecode.method(before, "public void run() {}");
        CtClass after = Bytecode.publicClass(pools[1], "com.acme.Service");
        Bytecode.method(after, "public void run() {}");

        JApiClass service = Compare.only(Compare.compare(before, after));

        assertEquals(0, service.getCompatibilityChanges().size());
        assertTrue(service.isSourceCompatible());
    }
}
