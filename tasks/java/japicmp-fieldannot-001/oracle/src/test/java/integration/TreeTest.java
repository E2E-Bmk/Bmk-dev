package integration;

import static fixtures.Model.annoCountOnField;
import static fixtures.Model.annoOnField;
import static fixtures.Model.classNamed;
import static fixtures.Model.compare;
import static fixtures.Model.compareAll;
import static fixtures.Model.elementNamed;
import static fixtures.Model.intAnnoField;
import static fixtures.Model.markerField;
import static fixtures.Model.fieldNamed;
import static fixtures.Model.onlyClass;
import static fixtures.Model.plainField;
import static fixtures.Model.pool;
import static fixtures.Model.publicClass;
import static fixtures.Model.stringAnnoField;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;

/** Cross-owner checks combining field-annotation records with field presence and sets of classes. */
class TreeTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiChangeStatus annoStatus(JApiClass c, String field, String anno) {
        return annoOnField(fieldNamed(c, field), anno).getChangeStatus();
    }
    private static JApiChangeStatus elemStatus(JApiClass c, String field, String anno, String member) {
        return elementNamed(annoOnField(fieldNamed(c, field), anno), member).getChangeStatus();
    }
    private static JApiChangeStatus mStatus(JApiClass c, String field) {
        return fieldNamed(c, field).getChangeStatus();
    }

    // Depends-On: atomic::CompareTest::addedFieldAnnotationIsNew
    // Depends-On: atomic::CompareTest::anAnnotatedFieldAddedIsNew
    @Test void anAnnotationAddedToOneFieldWhileAnotherFieldIsAdded() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D); markerField(n, "public int stop;", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::fieldAnnotationIntValueChangeIsModified
    @Test void aMemberChangeOnOneFieldWhileAnotherStaysPlain() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1); plainField(o, "public int stop;");
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::removedFieldAnnotationIsRemoved
    @Test void anAnnotationRemovedWhileAFieldIsAdded() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); plainField(n, "public int run;"); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.REMOVED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::unchangedFieldAnnotationIsUnchanged
    @Test void anUnchangedAnnotatedFieldWithANewField() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); markerField(n, "public int run;", D); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::fieldAnnotationStringValueChangeIsModified
    // Depends-On: atomic::CompareTest::fieldAnnotationIntValueChangeIsModified
    @Test void memberChangesOnTwoDifferentFields() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1); stringAnnoField(o, "public int stop;", D, "name", "x");
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2); stringAnnoField(n, "public int stop;", D, "name", "y");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", D, "name") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachFieldAnnotationChange
    @Test void perClassFieldAnnotationClassification() throws Exception {
        CtClass aO = k("a.A"); plainField(aO, "public int run;");
        CtClass aN = k("a.A"); markerField(aN, "public int run;", D);
        CtClass bO = k("a.B"); markerField(bO, "public int run;", D);
        CtClass bN = k("a.B"); plainField(bN, "public int run;");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoStatus(classNamed(r, "a.A"), "run", D) == JApiChangeStatus.NEW
                && annoStatus(classNamed(r, "a.B"), "run", D) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeOnAFieldIsNew
    @Test void oneFieldGainsAnnotationAnotherKeepsIt() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;"); markerField(o, "public int stop;", I);
        CtClass n = k("a.C"); markerField(n, "public int run;", D); markerField(n, "public int stop;", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && annoStatus(c, "stop", I) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anIntMemberAddedOnAFieldAnnotation
    @Test void addingAMemberOnOneFieldWhileAnotherIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D); intAnnoField(o, "public int stop;", D, "count", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 1); intAnnoField(n, "public int stop;", D, "count", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.NEW && elemStatus(c, "stop", D, "count") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::anAnnotatedFieldAddedIsNew
    @Test void aBrandNewClassWithTwoAnnotatedFields() throws Exception {
        CtClass n = k("a.C"); markerField(n, "public int run;", D); markerField(n, "public int stop;", I);
        JApiClass c = onlyClass(compare(null, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.NEW && annoStatus(c, "stop", I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anAnnotatedFieldRemovedIsRemoved
    @Test void aDeletedClassWithTwoAnnotatedFields() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D); markerField(o, "public int stop;", I);
        JApiClass c = onlyClass(compare(o, null));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.REMOVED && annoStatus(c, "stop", I) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aFieldAnnotationValueChangeMakesTheAnnotationModified
    @Test void anAnnotationModifiedByAMemberWhileAFieldIsAdded() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.MODIFIED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aStringMemberRemovedOnAFieldAnnotation
    @Test void removingAMemberWhileAFieldIsRemoved() throws Exception {
        CtClass o = k("a.C"); stringAnnoField(o, "public int run;", D, "name", "x"); plainField(o, "public int stop;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.REMOVED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::addingAnAnnotationToOneOfTwoFields
    @Test void addingAnnotationsToTwoOfThreeFields() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;"); plainField(o, "public int stop;"); plainField(o, "public int keep;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D); markerField(n, "public int stop;", D); plainField(n, "public int keep;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && annoStatus(c, "stop", D) == JApiChangeStatus.NEW
                && annoCountOnField(fieldNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::fieldAnnotationIntValueUnchangedIsUnchanged
    @Test void anUnchangedMemberWhileAFieldIsRemoved() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 5); plainField(o, "public int stop;");
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 5);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::twoClassesWithDistinctFieldAnnotationChanges
    @Test void twoClassesDistinctChangesOneGainsAField() throws Exception {
        CtClass aO = k("a.A"); plainField(aO, "public int run;");
        CtClass aN = k("a.A"); markerField(aN, "public int run;", D); plainField(aN, "public int extra;");
        CtClass bO = k("a.B"); intAnnoField(bO, "public int run;", D, "count", 1);
        CtClass bN = k("a.B"); intAnnoField(bN, "public int run;", D, "count", 2);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoStatus(classNamed(r, "a.A"), "run", D) == JApiChangeStatus.NEW
                && mStatus(classNamed(r, "a.A"), "extra") == JApiChangeStatus.NEW
                && elemStatus(classNamed(r, "a.B"), "run", D, "count") == JApiChangeStatus.MODIFIED);
    }

    // Depends-On: atomic::CompareTest::anIntMemberChangeOnASecondAnnotationType
    @Test void twoAnnotationTypesOnDifferentFields() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1); intAnnoField(o, "public int stop;", I, "level", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2); intAnnoField(n, "public int stop;", I, "level", 1);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED && elemStatus(c, "stop", I, "level") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aPlainFieldPresentOnBothSidesIsUnchanged
    @Test void aPlainFieldStaysUnchangedWhileAnotherGainsAnnotation() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;"); plainField(o, "public int keep;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D); plainField(n, "public int keep;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.NEW && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aStringMemberAddedOnAFieldAnnotation
    @Test void addingAStringMemberWhileAddingAField() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); stringAnnoField(n, "public int run;", D, "name", "x"); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "name") == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aClassSetClassifiesEachFieldAnnotationChange
    @Test void threeClassesEachClassifyAFieldAnnotation() throws Exception {
        CtClass aO = k("a.A"); plainField(aO, "public int run;");
        CtClass aN = k("a.A"); markerField(aN, "public int run;", D);
        CtClass bO = k("a.B"); markerField(bO, "public int run;", D);
        CtClass bN = k("a.B"); plainField(bN, "public int run;");
        CtClass cO = k("a.E"); markerField(cO, "public int run;", D);
        CtClass cN = k("a.E"); markerField(cN, "public int run;", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO, cO), Arrays.asList(aN, bN, cN));
        assertTrue(annoStatus(classNamed(r, "a.A"), "run", D) == JApiChangeStatus.NEW
                && annoStatus(classNamed(r, "a.B"), "run", D) == JApiChangeStatus.REMOVED
                && annoStatus(classNamed(r, "a.E"), "run", D) == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::changingAMemberOnOneOfTwoFields
    @Test void changingMembersOnTwoFieldsKeepingAThirdPlain() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1); intAnnoField(o, "public int stop;", D, "count", 1); plainField(o, "public int keep;");
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2); intAnnoField(n, "public int stop;", D, "count", 3); plainField(n, "public int keep;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.MODIFIED
                && elemStatus(c, "stop", D, "count") == JApiChangeStatus.MODIFIED
                && annoCountOnField(fieldNamed(c, "keep")) == 0);
    }

    // Depends-On: atomic::CompareTest::unchangedFieldAnnotationIsUnchanged
    @Test void anUnchangedAnnotatedFieldWithAnUnchangedPlainField() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D); plainField(o, "public int keep;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D); plainField(n, "public int keep;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", D) == JApiChangeStatus.UNCHANGED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aSecondMemberValueChangeOnAFieldAnnotation
    @Test void aMemberChangeAndAnAnnotationRemovalOnTwoFields() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "level", 3); markerField(o, "public int stop;", I);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "level", 4); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "level") == JApiChangeStatus.MODIFIED && annoStatus(c, "stop", I) == JApiChangeStatus.REMOVED);
    }

    // Depends-On: atomic::CompareTest::aStopFieldAnnotationIsAlsoTracked
    @Test void annotationsAddedToTwoDistinctlyNamedFields() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int alpha;"); plainField(o, "public int beta;");
        CtClass n = k("a.C"); markerField(n, "public int alpha;", D); markerField(n, "public int beta;", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "alpha", D) == JApiChangeStatus.NEW && annoStatus(c, "beta", I) == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aFieldAnnotationValueChangeLeavesTheFieldUnchanged
    @Test void aMemberChangeLeavesFieldUnchangedWhileAnotherFieldIsAdded() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 7); markerField(n, "public int stop;", D);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(mStatus(c, "run") == JApiChangeStatus.UNCHANGED && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::aMarkerFieldAnnotationHasNoElements
    @Test void aMarkerFieldAnnotationHasNoElementsWhileAFieldIsAdded() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); markerField(n, "public int run;", D); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnField(fieldNamed(c, "run"), D).getElements().size() == 0 && mStatus(c, "stop") == JApiChangeStatus.NEW);
    }

    // Depends-On: atomic::CompareTest::anIntMemberRemovedOnAFieldAnnotation
    @Test void removingAnIntMemberWhileKeepingAPlainField() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1); plainField(o, "public int keep;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D); plainField(n, "public int keep;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elemStatus(c, "run", D, "count") == JApiChangeStatus.REMOVED && mStatus(c, "keep") == JApiChangeStatus.UNCHANGED);
    }

    // Depends-On: atomic::CompareTest::aSecondAnnotationTypeOnAFieldIsNew
    @Test void aSecondAnnotationTypeAddedWhileAFieldIsRemoved() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;"); plainField(o, "public int stop;");
        CtClass n = k("a.C"); markerField(n, "public int run;", I);
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoStatus(c, "run", I) == JApiChangeStatus.NEW && mStatus(c, "stop") == JApiChangeStatus.REMOVED);
    }
}
