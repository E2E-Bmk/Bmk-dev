package atomic;

import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.generic;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.templateCount;
import static fixtures.Model.templateNamed;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Single-owner checks over synthesised class-level generic type parameters. */
class CompareTest {

    // class X<T>, X<E>, X<K> (single, unbounded); bounded variants; multi-parameter.
    private static final String T = "<T:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String E = "<E:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String K = "<K:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String T_NUM = "<T:Ljava/lang/Number;>Ljava/lang/Object;";
    private static final String TU = "<T:Ljava/lang/Object;U:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String KV = "<K:Ljava/lang/Object;V:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String TUV = "<T:Ljava/lang/Object;U:Ljava/lang/Object;V:Ljava/lang/Object;>Ljava/lang/Object;";

    private static CtClass k(String name, String sig) throws Exception {
        CtClass c = publicClass(pool(), name);
        if (sig != null) {
            generic(c, sig);
        }
        return c;
    }

    @Test
    void anAddedTypeParameterTIsNew() throws Exception {
        assertEquals(JApiChangeStatus.NEW, templateNamed(onlyClass(compare(k("a.C", null), k("a.C", T))), "T").getChangeStatus());
    }

    @Test
    void aRemovedTypeParameterTIsRemoved() throws Exception {
        assertEquals(JApiChangeStatus.REMOVED, templateNamed(onlyClass(compare(k("a.C", T), k("a.C", null))), "T").getChangeStatus());
    }

    @Test
    void anUnchangedTypeParameterTIsUnchanged() throws Exception {
        assertEquals(JApiChangeStatus.UNCHANGED, templateNamed(onlyClass(compare(k("a.C", T), k("a.C", T))), "T").getChangeStatus());
    }

    @Test
    void anAddedTypeParameterEIsNew() throws Exception {
        assertEquals(JApiChangeStatus.NEW, templateNamed(onlyClass(compare(k("a.C", null), k("a.C", E))), "E").getChangeStatus());
    }

    @Test
    void aRemovedTypeParameterEIsRemoved() throws Exception {
        assertEquals(JApiChangeStatus.REMOVED, templateNamed(onlyClass(compare(k("a.C", E), k("a.C", null))), "E").getChangeStatus());
    }

    @Test
    void anUnchangedTypeParameterEIsUnchanged() throws Exception {
        assertEquals(JApiChangeStatus.UNCHANGED, templateNamed(onlyClass(compare(k("a.C", E), k("a.C", E))), "E").getChangeStatus());
    }

    @Test
    void anAddedTypeParameterKIsNew() throws Exception {
        assertEquals(JApiChangeStatus.NEW, templateNamed(onlyClass(compare(k("a.C", null), k("a.C", K))), "K").getChangeStatus());
    }

    @Test
    void aRemovedTypeParameterKIsRemoved() throws Exception {
        assertEquals(JApiChangeStatus.REMOVED, templateNamed(onlyClass(compare(k("a.C", K), k("a.C", null))), "K").getChangeStatus());
    }

    @Test
    void anUnchangedTypeParameterKIsUnchanged() throws Exception {
        assertEquals(JApiChangeStatus.UNCHANGED, templateNamed(onlyClass(compare(k("a.C", K), k("a.C", K))), "K").getChangeStatus());
    }

    @Test
    void anAddedParameterReportsItsNameT() throws Exception {
        assertEquals("T", templateNamed(onlyClass(compare(k("a.C", null), k("a.C", T))), "T").getName());
    }

    @Test
    void anAddedParameterReportsItsNameE() throws Exception {
        assertEquals("E", templateNamed(onlyClass(compare(k("a.C", null), k("a.C", E))), "E").getName());
    }

    @Test
    void anAddedUnboundedParameterReportsObjectBound() throws Exception {
        assertEquals("java.lang.Object", templateNamed(onlyClass(compare(k("a.C", null), k("a.C", T))), "T").getNewType());
    }

    @Test
    void anAddedNumberBoundedParameterReportsNumberBound() throws Exception {
        assertEquals("java.lang.Number", templateNamed(onlyClass(compare(k("a.C", null), k("a.C", T_NUM))), "T").getNewType());
    }

    @Test
    void aNewParameterHasEmptyOldTypeOptional() throws Exception {
        assertFalse(templateNamed(onlyClass(compare(k("a.C", null), k("a.C", T))), "T").getOldTypeOptional().isPresent());
    }

    @Test
    void aNewParameterHasPresentNewTypeOptional() throws Exception {
        assertTrue(templateNamed(onlyClass(compare(k("a.C", null), k("a.C", T))), "T").getNewTypeOptional().isPresent());
    }

    @Test
    void addingOneParameterMakesTheCountOne() throws Exception {
        assertEquals(1, templateCount(onlyClass(compare(k("a.C", null), k("a.C", T)))));
    }

    @Test
    void addingTwoParametersMakesTheCountTwo() throws Exception {
        assertEquals(2, templateCount(onlyClass(compare(k("a.C", null), k("a.C", TU)))));
    }

    @Test
    void aNonGenericClassOnBothSidesHasNoTemplates() throws Exception {
        assertEquals(0, templateCount(onlyClass(compare(k("a.C", null), k("a.C", null)))));
    }

    @Test
    void removingTheOnlyParameterLeavesOneRemovedRecord() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", T), k("a.C", null)));
        assertTrue(templateCount(c) == 1 && templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void twoAddedParametersAreBothNew() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", null), k("a.C", TU)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void twoRemovedParametersAreBothRemoved() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", TU), k("a.C", null)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void twoUnchangedParametersAreBothUnchanged() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", TU), k("a.C", TU)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    @Test
    void addingASecondParameterKeepsTheFirstUnchanged() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", T), k("a.C", TU)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void removingTheSecondParameterKeepsTheFirstUnchanged() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", TU), k("a.C", T)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void twoParametersAreEachAddressableByName() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", null), k("a.C", TU)));
        assertTrue(templateNamed(c, "T") != null && templateNamed(c, "U") != null);
    }

    @Test
    void aClassSetClassifiesEachClassParametersIndependently() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T);
        CtClass bO = k("a.B", T); CtClass bN = k("a.B", null);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(classNamed(r, "a.B"), "T").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    @Test
    void twoClassesGainDistinctlyNamedParameters() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T);
        CtClass bO = k("a.B", null); CtClass bN = k("a.B", E);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(classNamed(r, "a.B"), "E").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void oneClassGainsAParameterWhileAnotherStaysNonGeneric() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T);
        CtClass bO = k("a.B", null); CtClass bN = k("a.B", null);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateCount(classNamed(r, "a.B")) == 0);
    }

    @Test
    void aClassPresentOnBothSidesReportsItsName() throws Exception {
        assertEquals("a.C", onlyClass(compare(k("a.C", T), k("a.C", T))).getFullyQualifiedName());
    }

    @Test
    void anAddedObjectBoundedParameterReportsObjectBoundExactly() throws Exception {
        assertEquals("java.lang.Object", templateNamed(onlyClass(compare(k("a.C", null), k("a.C", K))), "K").getNewType());
    }

    @Test
    void aNumberBoundedParameterUnchangedIsUnchanged() throws Exception {
        assertEquals(JApiChangeStatus.UNCHANGED, templateNamed(onlyClass(compare(k("a.C", T_NUM), k("a.C", T_NUM))), "T").getChangeStatus());
    }

    @Test
    void renamingTheOnlyParameterRemovesTheOldAndAddsTheNew() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", T), k("a.C", E)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && templateNamed(c, "E").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void renamingProducesTwoRecords() throws Exception {
        assertEquals(2, templateCount(onlyClass(compare(k("a.C", T), k("a.C", E)))));
    }

    @Test
    void threeAddedParametersAreAllNew() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", null), k("a.C", TUV)));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(c, "V").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void threeAddedParametersMakeTheCountThree() throws Exception {
        assertEquals(3, templateCount(onlyClass(compare(k("a.C", null), k("a.C", TUV)))));
    }

    @Test
    void aRemovedParameterHasEmptyNewTypeOptional() throws Exception {
        assertFalse(templateNamed(onlyClass(compare(k("a.C", T), k("a.C", null))), "T").getNewTypeOptional().isPresent());
    }

    @Test
    void aTwoParameterSetUsesKandVNames() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", null), k("a.C", KV)));
        assertTrue(templateNamed(c, "K").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(c, "V").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void anUnchangedParameterKeepsBothTypeOptionalsPresent() throws Exception {
        JApiClass c = onlyClass(compare(k("a.C", T), k("a.C", T)));
        assertTrue(templateNamed(c, "T").getOldTypeOptional().isPresent()
                && templateNamed(c, "T").getNewTypeOptional().isPresent());
    }
}
