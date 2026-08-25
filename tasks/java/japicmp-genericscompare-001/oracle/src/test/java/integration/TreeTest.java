package integration;

import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.generic;
import static fixtures.Model.method;
import static fixtures.Model.methodNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.templateCount;
import static fixtures.Model.templateNamed;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining generic-parameter records with method records and sets of classes. */
class TreeTest {

    private static final String T = "<T:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String E = "<E:Ljava/lang/Object;>Ljava/lang/Object;";
    private static final String TU = "<T:Ljava/lang/Object;U:Ljava/lang/Object;>Ljava/lang/Object;";

    private static CtClass k(String name, String sig) throws Exception {
        CtClass c = publicClass(pool(), name);
        if (sig != null) {
            generic(c, sig);
        }
        return c;
    }

    // Depends-On: atomic::CompareTest::anAddedTypeParameterTIsNew
    @Test
    void aTypeParameterAndAMethodAreBothNew() throws Exception {
        CtClass o = k("a.C", null);
        CtClass n = k("a.C", T); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAddedTypeParameterTIsNew
    @Test
    void anAddedParameterWithAnUnchangedMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C", null); method(o, "public void run(){}");
        CtClass n = k("a.C", T); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anUnchangedTypeParameterTIsUnchanged
    @Test
    void anUnchangedParameterWithANewMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C", T);
        CtClass n = k("a.C", T); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedTypeParameterTIsRemoved
    @Test
    void aRemovedParameterWithAnAddedMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C", T);
        CtClass n = k("a.C", null); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedTypeParameterTIsRemoved
    @Test
    void aRemovedParameterWithARemovedMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C", T); method(o, "public void run(){}");
        CtClass n = k("a.C", null);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachClassParametersIndependently
    @Test
    void oneClassGainsAParameterWhileAnotherGainsAMethod() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T);
        CtClass bO = k("a.B", null); CtClass bN = k("a.B", null); method(bN, "public void run(){}");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.B"), "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoAddedParametersAreBothNew
    @Test
    void twoAddedParametersCoexistWithANewMethod() throws Exception {
        CtClass o = k("a.C", null);
        CtClass n = k("a.C", TU); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::addingASecondParameterKeepsTheFirstUnchanged
    @Test
    void aRetainedAndAnAddedParameterCoexistWithANewMethod() throws Exception {
        CtClass o = k("a.C", T);
        CtClass n = k("a.C", TU); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAddedTypeParameterTIsNew
    @Test
    void aBrandNewClassWithAParameterAndAMethodHasBothNew() throws Exception {
        CtClass n = k("a.C", T); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aRemovedTypeParameterTIsRemoved
    @Test
    void aDeletedClassWithAParameterAndAMethodHasBothRemoved() throws Exception {
        CtClass o = k("a.C", T); method(o, "public void run(){}");
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::renamingTheOnlyParameterRemovesTheOldAndAddsTheNew
    @Test
    void renamingAParameterWhileAddingAMethodClassifiesEach() throws Exception {
        CtClass o = k("a.C", T);
        CtClass n = k("a.C", E); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && templateNamed(c, "E").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoUnchangedParametersAreBothUnchanged
    @Test
    void twoUnchangedParametersCoexistWithARemovedMethod() throws Exception {
        CtClass o = k("a.C", TU); method(o, "public void run(){}");
        CtClass n = k("a.C", TU);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::removingTheSecondParameterKeepsTheFirstUnchanged
    @Test
    void aRetainedAndARemovedParameterCoexistWithAnUnchangedMethod() throws Exception {
        CtClass o = k("a.C", TU); method(o, "public void run(){}");
        CtClass n = k("a.C", T); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachClassParametersIndependently
    @Test
    void perClassParameterClassificationAcrossASet() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T);
        CtClass bO = k("a.B", T); CtClass bN = k("a.B", null);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(classNamed(r, "a.B"), "T").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingTwoParametersMakesTheCountTwo
    @Test
    void theParameterCountHoldsWhileAMethodIsAdded() throws Exception {
        CtClass o = k("a.C", null);
        CtClass n = k("a.C", TU); method(n, "public void run(){}");
        assertEquals(2, templateCount(onlyClass(compare(o, n))));
    }

    // Depends-On: atomic::CompareTest::twoClassesGainDistinctlyNamedParameters
    @Test
    void twoClassesGainDistinctParametersAndOneGainsAMethod() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T); method(aN, "public void run(){}");
        CtClass bO = k("a.B", null); CtClass bN = k("a.B", E);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.A"), "run").getChangeStatus() == JApiChangeStatus.NEW
                && templateNamed(classNamed(r, "a.B"), "E").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anUnchangedTypeParameterTIsUnchanged
    @Test
    void anUnchangedParameterAndAnUnchangedMethodBothStaySame() throws Exception {
        CtClass o = k("a.C", T); method(o, "public void run(){}");
        CtClass n = k("a.C", T); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::threeAddedParametersAreAllNew
    @Test
    void addingASecondParameterAndAMethodTogether() throws Exception {
        CtClass o = k("a.C", T);
        CtClass n = k("a.C", TU); method(n, "public int size(){return 0;}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "size").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassPresentOnBothSidesReportsItsName
    @Test
    void eachClassInAGenericSetKeepsItsOwnName() throws Exception {
        CtClass aO = k("a.One", T); CtClass aN = k("a.One", T);
        CtClass bO = k("a.Two", null); CtClass bN = k("a.Two", E);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(classNamed(r, "a.One") != null && classNamed(r, "a.Two") != null);
    }

    // Depends-On: atomic::CompareTest::aRemovedTypeParameterTIsRemoved
    @Test
    void removingAParameterAndAddingAMethodOnTheSameClass() throws Exception {
        CtClass o = k("a.C", T);
        CtClass n = k("a.C", null); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateCount(c) == 1
                && templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoAddedParametersAreBothNew
    @Test
    void twoClassesEachGainTwoParameters() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", TU);
        CtClass bO = k("a.B", null); CtClass bN = k("a.B", TU);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateCount(classNamed(r, "a.A")) == 2 && templateCount(classNamed(r, "a.B")) == 2);
    }

    // Depends-On: atomic::CompareTest::addingASecondParameterKeepsTheFirstUnchanged
    @Test
    void aRetainedParameterAndANewParameterWithAnUnchangedMethod() throws Exception {
        CtClass o = k("a.C", T); method(o, "public void run(){}");
        CtClass n = k("a.C", TU); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.UNCHANGED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anAddedTypeParameterEIsNew
    @Test
    void aNewClassWithParameterEAndAMethodMarksBothNew() throws Exception {
        CtClass n = k("a.C", E); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(templateNamed(c, "E").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::twoRemovedParametersAreBothRemoved
    @Test
    void twoRemovedParametersCoexistWithARemovedMethod() throws Exception {
        CtClass o = k("a.C", TU); method(o, "public void run(){}");
        CtClass n = k("a.C", null);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateNamed(c, "T").getChangeStatus() == JApiChangeStatus.REMOVED
                && templateNamed(c, "U").getChangeStatus() == JApiChangeStatus.REMOVED
                && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::renamingProducesTwoRecords
    @Test
    void renamingProducesTwoRecordsWhileAMethodStaysUnchanged() throws Exception {
        CtClass o = k("a.C", T); method(o, "public void run(){}");
        CtClass n = k("a.C", E); method(n, "public void run(){}");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(templateCount(c) == 2 && methodNamed(c, "run").getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::oneClassGainsAParameterWhileAnotherStaysNonGeneric
    @Test
    void oneClassGainsAParameterAndAMethodWhileAnotherIsUntouched() throws Exception {
        CtClass aO = k("a.A", null); CtClass aN = k("a.A", T); method(aN, "public void run(){}");
        CtClass bO = k("a.B", null); CtClass bN = k("a.B", null);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(templateNamed(classNamed(r, "a.A"), "T").getChangeStatus() == JApiChangeStatus.NEW
                && methodNamed(classNamed(r, "a.A"), "run").getChangeStatus() == JApiChangeStatus.NEW
                && templateCount(classNamed(r, "a.B")) == 0);
    }
}
