package atomic;

import static fixtures.Model.bridgeMethod;
import static fixtures.Model.bridgeOf;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.methodNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.plainMethod;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.syntheticMethod;
import static fixtures.Model.syntheticOf;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.BridgeModifier;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;
import org.markline.model.SyntheticModifier;

/** Single-owner checks over synthesised bridge/synthetic access flags. */
class CompareTest {

    private static CtClass k(String name) throws Exception {
        return publicClass(pool(), name);
    }

    // ---- bridge value reads on a method present on both sides ----

    @Test
    void aBridgeMethodOnBothSidesReportsBridgeAsItsNewValue() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void aBridgeMethodOnBothSidesReportsBridgeAsItsOldValue() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getOldModifier().get());
    }

    @Test
    void aBridgeMethodOnBothSidesHasUnchangedBridgeModifier() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void aPlainMethodReportsNonBridgeAsItsNewValue() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.NON_BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void aPlainMethodHasUnchangedBridgeModifier() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void removingTheBridgeFlagMakesTheBridgeModifierRemoved() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.REMOVED, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void removingTheBridgeFlagLeavesTheOldModifierBridge() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getOldModifier().get());
    }

    // ---- synthetic value reads and change on a method present on both sides ----

    @Test
    void aSyntheticMethodOnBothSidesReportsSyntheticAsItsNewValue() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(SyntheticModifier.SYNTHETIC, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void aSyntheticMethodOnBothSidesReportsSyntheticAsItsOldValue() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(SyntheticModifier.SYNTHETIC, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getOldModifier().get());
    }

    @Test
    void aSyntheticMethodOnBothSidesHasUnchangedSyntheticModifier() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void aPlainMethodReportsNonSyntheticAsItsNewValue() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(SyntheticModifier.NON_SYNTHETIC, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void aPlainMethodHasUnchangedSyntheticModifier() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void addingTheSyntheticFlagMakesTheSyntheticModifierModified() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.MODIFIED, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void removingTheSyntheticFlagMakesTheSyntheticModifierModified() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.MODIFIED, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getChangeStatus());
    }

    @Test
    void aSyntheticChangeLeavesTheClassUnchanged() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    // ---- method presence carrying a special flag ----

    @Test
    void anAddedBridgeMethodIsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.NEW, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void aRemovedBridgeMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void anAddedSyntheticMethodIsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.NEW, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void aRemovedSyntheticMethodIsRemoved() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void anUnchangedBridgeMethodIsUnchanged() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void anUnchangedSyntheticMethodIsUnchanged() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void aPlainMethodPresentOnBothSidesIsUnchanged() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void anAddedBridgeMethodReportsBridgeAsItsNewValue() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void anAddedSyntheticMethodReportsSyntheticAsItsNewValue() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(SyntheticModifier.SYNTHETIC, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    // ---- class-level and multi-owner-lite ----

    @Test
    void addingABridgeMethodMakesTheClassModified() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.MODIFIED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void addingASyntheticMethodLeavesTheClassUnchanged() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, onlyClass(compare(o, n)).getChangeStatus());
    }

    @Test
    void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }

    @Test
    void aSyntheticChangeOnOneMethodLeavesAnotherPlainMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void a(){}"); plainMethod(o, "public void b(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); plainMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(c, "b")).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    @Test
    void removingSyntheticFromOneOfTwoMethods() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void a(){}"); syntheticMethod(o, "public void b(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(c, "b")).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    @Test
    void twoBridgeMethodsUnchangedBothReportBridge() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void a(){}"); bridgeMethod(o, "public void b(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void a(){}"); bridgeMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(bridgeOf(methodNamed(c, "a")).getNewModifier().get() == BridgeModifier.BRIDGE
                && bridgeOf(methodNamed(c, "b")).getNewModifier().get() == BridgeModifier.BRIDGE);
    }

    @Test
    void aClassSetClassifiesSyntheticChangesPerClass() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); syntheticMethod(aN, "public void run(){}");
        CtClass bO = k("a.B"); syntheticMethod(bO, "public void run(){}");
        CtClass bN = k("a.B"); syntheticMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(syntheticOf(methodNamed(classNamed(r, "a.A"), "run")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(classNamed(r, "a.B"), "run")).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    @Test
    void twoClassesAddDistinctFlaggedMethods() throws Exception {
        CtClass aO = k("a.A");
        CtClass aN = k("a.A"); bridgeMethod(aN, "public void run(){}");
        CtClass bO = k("a.B");
        CtClass bN = k("a.B"); syntheticMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(methodNamed(classNamed(r, "a.A"), "run").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.B"), "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void anAddedSyntheticMethodLeavesItsBridgeModifierUnchanged() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.NON_BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void anAddedBridgeMethodReportsNonSyntheticValue() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(SyntheticModifier.NON_SYNTHETIC, syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().get());
    }

    @Test
    void twoSyntheticMethodsUnchangedBothReportSynthetic() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void a(){}"); syntheticMethod(o, "public void b(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getNewModifier().get() == SyntheticModifier.SYNTHETIC
                && syntheticOf(methodNamed(c, "b")).getNewModifier().get() == SyntheticModifier.SYNTHETIC);
    }

    @Test
    void aBrandNewClassWithABridgeMethodMarksTheMethodNew() throws Exception {
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.NEW, methodNamed(onlyClass(compare(null, n)), "run").getChangeStatus());
    }

    @Test
    void aDeletedClassWithASyntheticMethodMarksTheMethodRemoved() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        assertEquals(JApiChangeStatus.REMOVED, methodNamed(onlyClass(compare(o, null)), "run").getChangeStatus());
    }

    @Test
    void aRemovedBridgeMethodReportsBridgeOnItsOldValue() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        assertEquals(BridgeModifier.BRIDGE, bridgeOf(methodNamed(onlyClass(compare(o, n)), "run")).getOldModifier().get());
    }

    @Test
    void aSyntheticMethodPresentOnBothSidesKeepsTheMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertEquals(JApiChangeStatus.UNCHANGED, methodNamed(onlyClass(compare(o, n)), "run").getChangeStatus());
    }

    @Test
    void keepingAPlainMethodWhileAddingASyntheticMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void keep(){}"); syntheticMethod(n, "public void fresh(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "keep").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "fresh").getChangeStatus() == JApiChangeStatus.NEW);
    }

    @Test
    void aSyntheticChangeReportsBothOldAndNewModifierPresent() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        assertTrue(syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getOldModifier().isPresent()
                && syntheticOf(methodNamed(onlyClass(compare(o, n)), "run")).getNewModifier().isPresent());
    }
}
