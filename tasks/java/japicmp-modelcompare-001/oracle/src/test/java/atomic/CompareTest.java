package atomic;

import static fixtures.Model.compare;
import static fixtures.Model.field;
import static fixtures.Model.fieldNamed;
import static fixtures.Model.method;
import static fixtures.Model.methodNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import javassist.ClassPool;
import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.AccessModifier;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;
import org.markline.model.JApiField;
import org.markline.model.JApiMethod;

/** Single-owner checks for the comparison model over synthesised bytecode shapes. */
class CompareTest {

    private static CtClass klass(String name) throws Exception {
        return publicClass(pool(), name);
    }

    @Test
    void aClassPresentOnBothSidesIsUnchanged() throws Exception {
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(klass("a.B"), klass("a.B"))).getChangeStatus());
    }

    @Test
    void aClassOnlyOnTheNewSideIsNew() throws Exception {
        assertEquals(JApiChangeStatus.NEW, onlyClass(compare(null, klass("a.B"))).getChangeStatus());
    }

    @Test
    void aClassOnlyOnTheOldSideIsRemoved() throws Exception {
        assertEquals(JApiChangeStatus.REMOVED, onlyClass(compare(klass("a.B"), null)).getChangeStatus());
    }

    @Test
    void anAddedMethodIsNew() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.NEW, methodNamed(c, "run").getChangeStatus());
    }

    @Test
    void aRemovedMethodIsRemoved() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.REMOVED, methodNamed(c, "run").getChangeStatus());
    }

    @Test
    void aMethodPresentOnBothSidesUnchangedIsUnchanged() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.UNCHANGED, methodNamed(c, "run").getChangeStatus());
    }

    @Test
    void aClassWithAnAddedMethodIsModified() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void anAddedFieldIsNew() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.NEW, fieldNamed(c, "count").getChangeStatus());
    }

    @Test
    void aRemovedFieldIsRemoved() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.REMOVED, fieldNamed(c, "count").getChangeStatus());
    }

    @Test
    void aFieldPresentOnBothSidesUnchangedIsUnchanged() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.UNCHANGED, fieldNamed(c, "count").getChangeStatus());
    }

    @Test
    void aMethodAccessChangeIsModified() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "protected void run() {}");
        JApiClass c = onlyClass(compare(o, n));
        assertEquals(JApiChangeStatus.MODIFIED, methodNamed(c, "run").getChangeStatus());
    }

    @Test
    void aMethodAccessModifierRecordsOldAndNewValues() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "protected void run() {}");
        JApiMethod m = methodNamed(onlyClass(compare(o, n)), "run");
        assertEquals(AccessModifier.PUBLIC, m.getAccessModifier().getOldModifier().get());
        assertEquals(AccessModifier.PROTECTED, m.getAccessModifier().getNewModifier().get());
    }

    @Test
    void aMethodAccessModifierStatusIsModifiedOnChange() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "protected void run() {}");
        JApiMethod m = methodNamed(onlyClass(compare(o, n)), "run");
        assertEquals(JApiChangeStatus.MODIFIED, m.getAccessModifier().getChangeStatus());
    }

    @Test
    void anUnchangedMethodAccessModifierIsUnchanged() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        JApiMethod m = methodNamed(onlyClass(compare(o, n)), "run");
        assertEquals(JApiChangeStatus.UNCHANGED, m.getAccessModifier().getChangeStatus());
    }

    @Test
    void aStaticFieldToInstanceFieldIsModified() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public static int count;");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        JApiField f = fieldNamed(onlyClass(compare(o, n)), "count");
        assertEquals(JApiChangeStatus.MODIFIED, f.getStaticModifier().getChangeStatus());
    }

    @Test
    void aFinalFieldChangeIsRecordedOnTheFinalModifier() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public final int count = 1;");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        JApiField f = fieldNamed(onlyClass(compare(o, n)), "count");
        assertEquals(JApiChangeStatus.MODIFIED, f.getFinalModifier().getChangeStatus());
    }

    @Test
    void aMethodReturnTypeChangeIsModified() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public int run() { return 0; }");
        CtClass n = klass("a.B");
        method(n, "public long run() { return 0; }");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "run") != null);
    }

    @Test
    void aReturnTypeRecordCarriesTheNewType() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public int val() { return 0; }");
        CtClass n = klass("a.B");
        method(n, "public int val() { return 0; }");
        JApiMethod m = methodNamed(onlyClass(compare(o, n)), "val");
        assertEquals(JApiChangeStatus.UNCHANGED, m.getReturnType().getChangeStatus());
    }

    @Test
    void anUnchangedEmptyClassHasNoMethods() throws Exception {
        assertTrue(onlyClass(compare(klass("a.B"), klass("a.B"))).getMethods().isEmpty());
    }

    @Test
    void aNewClassAccessModifierIsNew() throws Exception {
        JApiClass c = onlyClass(compare(null, klass("a.B")));
        assertEquals(JApiChangeStatus.NEW, c.getAccessModifier().getChangeStatus());
    }

    @Test
    void aNewClassHasEmptyOldClassOptional() throws Exception {
        assertFalse(onlyClass(compare(null, klass("a.B"))).getOldClass().isPresent());
    }

    @Test
    void aRemovedClassHasEmptyNewClassOptional() throws Exception {
        assertFalse(onlyClass(compare(klass("a.B"), null)).getNewClass().isPresent());
    }

    @Test
    void aClassPresentOnBothSidesHasBothClassOptionals() throws Exception {
        JApiClass c = onlyClass(compare(klass("a.B"), klass("a.B")));
        assertTrue(c.getOldClass().isPresent() && c.getNewClass().isPresent());
    }

    @Test
    void anAddedMethodHasEmptyOldMethodOptional() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        assertFalse(methodNamed(onlyClass(compare(o, n)), "run").getOldMethod().isPresent());
    }

    @Test
    void aRemovedMethodHasEmptyNewMethodOptional() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        assertFalse(methodNamed(onlyClass(compare(o, n)), "run").getNewMethod().isPresent());
    }

    @Test
    void theFullyQualifiedNameIsReported() throws Exception {
        assertEquals("a.B", onlyClass(compare(klass("a.B"), klass("a.B"))).getFullyQualifiedName());
    }

    @Test
    void twoDistinctClassesProduceTwoRecords() throws Exception {
        JApiClass ignore = onlyClass(compare(klass("a.B"), klass("a.B")));
        List<JApiClass> r = fixtures.Model.compareAll(
                java.util.Arrays.asList(klass("a.B")), java.util.Arrays.asList(klass("a.C")));
        assertEquals(2, r.size());
    }

    @Test
    void anAddedOverloadIsNew() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        method(n, "public void run(int x) {}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void aClassWithOnlyUnchangedMembersIsUnchanged() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        field(n, "public int count;");
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void aStaticModifierRecordsNonStaticToStatic() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        field(n, "public static int count;");
        JApiField f = fieldNamed(onlyClass(compare(o, n)), "count");
        assertEquals(JApiChangeStatus.MODIFIED, f.getStaticModifier().getChangeStatus());
    }

    @Test
    void aFieldAccessModifierRecordsValues() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        field(n, "public int count;");
        JApiField f = fieldNamed(onlyClass(compare(o, n)), "count");
        assertEquals(AccessModifier.PUBLIC, f.getAccessModifier().getNewModifier().get());
    }

    @Test
    void aRemovedFieldModifierIsNotModified() throws Exception {
        CtClass o = klass("a.B");
        field(o, "public int count;");
        CtClass n = klass("a.B");
        JApiField f = fieldNamed(onlyClass(compare(o, n)), "count");
        assertFalse(f.getAccessModifier().getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    @Test
    void aNewMethodModifierIsNew() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        method(n, "public void run() {}");
        JApiMethod m = methodNamed(onlyClass(compare(o, n)), "run");
        assertEquals(JApiChangeStatus.NEW, m.getAccessModifier().getChangeStatus());
    }

    @Test
    void aRemovedMethodHasEmptyNewOptionalAndRemovedStatus() throws Exception {
        CtClass o = klass("a.B");
        method(o, "public void run() {}");
        CtClass n = klass("a.B");
        JApiMethod m = methodNamed(onlyClass(compare(o, n)), "run");
        assertTrue(m.getChangeStatus() == JApiChangeStatus.REMOVED && !m.getNewMethod().isPresent());
    }

    @Test
    void aClassTypeRecordIsPresent() throws Exception {
        assertTrue(onlyClass(compare(klass("a.B"), klass("a.B"))).getClassType() != null);
    }

    @Test
    void severalAddedFieldsAreEachNew() throws Exception {
        CtClass o = klass("a.B");
        CtClass n = klass("a.B");
        field(n, "public int a;");
        field(n, "public int b;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(fieldNamed(c, "a").getChangeStatus() == JApiChangeStatus.NEW
                && fieldNamed(c, "b").getChangeStatus() == JApiChangeStatus.NEW);
    }
}
