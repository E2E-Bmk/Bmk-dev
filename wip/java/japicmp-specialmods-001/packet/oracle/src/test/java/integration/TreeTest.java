package integration;

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
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.BridgeModifier;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;
import org.markline.model.SyntheticModifier;

/** Cross-owner checks combining bridge, synthetic and method-presence records. */
class TreeTest {

    private static CtClass k(String name) throws Exception {
        return publicClass(pool(), name);
    }

    // Depends-On: atomic::CompareTest::addingTheSyntheticFlagMakesTheSyntheticModifierModified
    // Depends-On: atomic::CompareTest::anAddedSyntheticMethodIsNew
    @Test
    void aSyntheticFlagChangeAndANewMethodAreBothReflected() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void a(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && methodNamed(c, "b").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSyntheticMethodOnBothSidesReportsSyntheticAsItsNewValue
    // Depends-On: atomic::CompareTest::aPlainMethodReportsNonSyntheticAsItsNewValue
    @Test
    void aSyntheticMethodAndAPlainMethodReportDistinctValues() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void a(){}"); plainMethod(o, "public void b(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); plainMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getNewModifier().get() == SyntheticModifier.SYNTHETIC
                && syntheticOf(methodNamed(c, "b")).getNewModifier().get() == SyntheticModifier.NON_SYNTHETIC);
    }

    // Depends-On: atomic::CompareTest::removingTheBridgeFlagMakesTheBridgeModifierRemoved
    // Depends-On: atomic::CompareTest::aPlainMethodPresentOnBothSidesIsUnchanged
    @Test
    void removingABridgeFlagWhileKeepingAPlainMethodUnchanged() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void a(){}"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void a(){}"); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(bridgeOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "keep").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::addingTheSyntheticFlagMakesTheSyntheticModifierModified
    // Depends-On: atomic::CompareTest::anAddedSyntheticMethodLeavesItsBridgeModifierUnchanged
    @Test
    void aSyntheticChangeLeavesBridgeUnchangedOnTheSameMethod() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "run")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && bridgeOf(methodNamed(c, "run")).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aBridgeMethodOnBothSidesReportsBridgeAsItsNewValue
    // Depends-On: atomic::CompareTest::anAddedSyntheticMethodIsNew
    @Test
    void anUnchangedBridgeMethodCoexistsWithANewSyntheticMethod() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void a(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(bridgeOf(methodNamed(c, "a")).getNewModifier().get() == BridgeModifier.BRIDGE
                && methodNamed(c, "b").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesSyntheticChangesPerClass
    @Test
    void perClassSyntheticChangeClassificationAcrossASet() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); syntheticMethod(aN, "public void run(){}");
        CtClass bO = k("a.B"); syntheticMethod(bO, "public void run(){}");
        CtClass bN = k("a.B"); plainMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(syntheticOf(methodNamed(classNamed(r, "a.A"), "run")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(classNamed(r, "a.B"), "run")).getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::anAddedBridgeMethodIsNew
    // Depends-On: atomic::CompareTest::anAddedBridgeMethodReportsBridgeAsItsNewValue
    @Test
    void anAddedBridgeMethodIsNewAndReportsBridge() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW
                && bridgeOf(methodNamed(c, "run")).getNewModifier().get() == BridgeModifier.BRIDGE);
    }

    // Depends-On: atomic::CompareTest::anAddedSyntheticMethodIsNew
    // Depends-On: atomic::CompareTest::anAddedSyntheticMethodReportsSyntheticAsItsNewValue
    @Test
    void anAddedSyntheticMethodIsNewAndReportsSynthetic() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW
                && syntheticOf(methodNamed(c, "run")).getNewModifier().get() == SyntheticModifier.SYNTHETIC);
    }

    // Depends-On: atomic::CompareTest::aSyntheticMethodOnBothSidesReportsSyntheticAsItsNewValue
    @Test
    void oneSyntheticMethodChangesWhileAnotherStaysSynthetic() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void a(){}"); syntheticMethod(o, "public void b(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(c, "b")).getNewModifier().get() == SyntheticModifier.SYNTHETIC);
    }

    // Depends-On: atomic::CompareTest::removingTheSyntheticFlagMakesTheSyntheticModifierModified
    // Depends-On: atomic::CompareTest::aRemovedBridgeMethodIsRemoved
    @Test
    void changingSyntheticOnOneMethodAndRemovingAnotherMethod() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void a(){}"); bridgeMethod(o, "public void b(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void a(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && methodNamed(c, "b").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingABridgeMethodMakesTheClassModified
    // Depends-On: atomic::CompareTest::aPlainMethodPresentOnBothSidesIsUnchanged
    @Test
    void addingABridgeMethodToOneOfTwoClassesModifiesOnlyThatClass() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void keep(){}");
        CtClass aN = k("a.A"); plainMethod(aN, "public void keep(){}");
        CtClass bO = k("a.B");
        CtClass bN = k("a.B"); bridgeMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(classNamed(r, "a.A").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && classNamed(r, "a.B").getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::removingTheBridgeFlagLeavesTheOldModifierBridge
    @Test
    void removingABridgeFlagReportsRemovedStatusAndOldBridgeValue() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(bridgeOf(methodNamed(c, "run")).getChangeStatus() == JApiChangeStatus.REMOVED
                && bridgeOf(methodNamed(c, "run")).getOldModifier().get() == BridgeModifier.BRIDGE);
    }

    // Depends-On: atomic::CompareTest::twoSyntheticMethodsUnchangedBothReportSynthetic
    // Depends-On: atomic::CompareTest::anAddedSyntheticMethodIsNew
    @Test
    void twoUnchangedSyntheticMethodsCoexistWithANewSyntheticMethod() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void a(){}"); syntheticMethod(o, "public void b(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}"); syntheticMethod(n, "public void c(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getNewModifier().get() == SyntheticModifier.SYNTHETIC
                && methodNamed(c, "c").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aBrandNewClassWithABridgeMethodMarksTheMethodNew
    @Test
    void aBrandNewClassWithBridgeAndSyntheticMethodsMarksBothNew() throws Exception {
        CtClass n = k("a.C"); bridgeMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(methodNamed(c, "a").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "b").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aDeletedClassWithASyntheticMethodMarksTheMethodRemoved
    @Test
    void aDeletedClassWithBridgeAndSyntheticMethodsMarksBothRemoved() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void a(){}"); syntheticMethod(o, "public void b(){}");
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(methodNamed(c, "a").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "b").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aBridgeMethodOnBothSidesReportsBridgeAsItsNewValue
    // Depends-On: atomic::CompareTest::aSyntheticMethodOnBothSidesReportsSyntheticAsItsNewValue
    @Test
    void aBridgeMethodAndASyntheticMethodBothUnchangedReportTheirValues() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void a(){}"); syntheticMethod(o, "public void b(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(bridgeOf(methodNamed(c, "a")).getNewModifier().get() == BridgeModifier.BRIDGE
                && syntheticOf(methodNamed(c, "b")).getNewModifier().get() == SyntheticModifier.SYNTHETIC);
    }

    // Depends-On: atomic::CompareTest::aSyntheticChangeOnOneMethodLeavesAnotherPlainMethodUnchanged
    @Test
    void changingSyntheticOnTwoOfThreeMethods() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void a(){}"); plainMethod(o, "public void b(){}"); plainMethod(o, "public void d(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); syntheticMethod(n, "public void b(){}"); plainMethod(n, "public void d(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(c, "b")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && syntheticOf(methodNamed(c, "d")).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesSyntheticChangesPerClass
    // Depends-On: atomic::CompareTest::twoClassesAddDistinctFlaggedMethods
    @Test
    void threeClassesEachClassifyTheirOwnChange() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); syntheticMethod(aN, "public void run(){}");
        CtClass bO = k("a.B");
        CtClass bN = k("a.B"); bridgeMethod(bN, "public void run(){}");
        CtClass cO = k("a.D"); syntheticMethod(cO, "public void run(){}");
        CtClass cN = k("a.D"); syntheticMethod(cN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(syntheticOf(methodNamed(classNamed(r, "a.A"), "run")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && methodNamed(classNamed(r, "a.B"), "run").getChangeStatus() == JApiChangeStatus.NEW
                && syntheticOf(methodNamed(classNamed(r, "a.D"), "run")).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::addingABridgeMethodMakesTheClassModified
    // Depends-On: atomic::CompareTest::addingASyntheticMethodLeavesTheClassUnchanged
    @Test
    void addingABridgeMethodModifiesItsClassWhileASyntheticAdditionDoesNot() throws Exception {
        CtClass aO = k("a.A");
        CtClass aN = k("a.A"); bridgeMethod(aN, "public void run(){}");
        CtClass bO = k("a.B");
        CtClass bN = k("a.B"); syntheticMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(classNamed(r, "a.A").getChangeStatus() == JApiChangeStatus.MODIFIED
                && classNamed(r, "a.B").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::keepingAPlainMethodWhileAddingASyntheticMethodClassifiesEach
    @Test
    void keepingTwoPlainMethodsWhileAddingASyntheticMethod() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void keep1(){}"); plainMethod(o, "public void keep2(){}");
        CtClass n = k("a.C"); plainMethod(n, "public void keep1(){}"); plainMethod(n, "public void keep2(){}"); syntheticMethod(n, "public void fresh(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "keep1").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "fresh").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aSyntheticChangeReportsBothOldAndNewModifierPresent
    @Test
    void aSyntheticChangeCarriesBothOldAndNewAcrossAClassWithANewMethod() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void a(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); plainMethod(n, "public void b(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getOldModifier().isPresent()
                && syntheticOf(methodNamed(c, "a")).getNewModifier().isPresent()
                && methodNamed(c, "b").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anUnchangedBridgeMethodIsUnchanged
    @Test
    void anUnchangedBridgeMethodKeepsMethodAndValueStable() throws Exception {
        CtClass o = k("a.C"); bridgeMethod(o, "public void run(){}");
        CtClass n = k("a.C"); bridgeMethod(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && bridgeOf(methodNamed(c, "run")).getNewModifier().get() == BridgeModifier.BRIDGE);
    }

    // Depends-On: atomic::CompareTest::anUnchangedSyntheticMethodIsUnchanged
    @Test
    void anUnchangedSyntheticMethodKeepsMethodAndValueStable() throws Exception {
        CtClass o = k("a.C"); syntheticMethod(o, "public void run(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && syntheticOf(methodNamed(c, "run")).getNewModifier().get() == SyntheticModifier.SYNTHETIC);
    }

    // Depends-On: atomic::CompareTest::aSyntheticChangeLeavesTheClassUnchanged
    @Test
    void aSyntheticOnlyChangeKeepsTheClassUnchangedWhileAMethodAddMakesAnotherModified() throws Exception {
        CtClass aO = k("a.A"); plainMethod(aO, "public void run(){}");
        CtClass aN = k("a.A"); syntheticMethod(aN, "public void run(){}");
        CtClass bO = k("a.B");
        CtClass bN = k("a.B"); plainMethod(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(classNamed(r, "a.A").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && classNamed(r, "a.B").getChangeStatus() == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aSyntheticChangeOnOneMethodLeavesAnotherPlainMethodUnchanged
    @Test
    void aSyntheticChangeAndAnUnchangedPlainMethodInOneClass() throws Exception {
        CtClass o = k("a.C"); plainMethod(o, "public void a(){}"); plainMethod(o, "public void keep(){}");
        CtClass n = k("a.C"); syntheticMethod(n, "public void a(){}"); plainMethod(n, "public void keep(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(syntheticOf(methodNamed(c, "a")).getChangeStatus() == JApiChangeStatus.MODIFIED
                && methodNamed(c, "keep").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }
}
