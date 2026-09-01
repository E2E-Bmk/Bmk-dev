package atomic;

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
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;

import javassist.CtClass;
import org.junit.jupiter.api.Test;
import org.markline.model.JApiChangeStatus;
import org.markline.model.JApiClass;
import org.markline.model.JApiField;

/** Single-owner checks over annotations carried by fields. */
class CompareTest {

    static final String D = "java.lang.annotation.Documented";
    static final String I = "java.lang.annotation.Inherited";

    private static CtClass k(String n) throws Exception { return publicClass(pool(), n); }

    private static JApiField run(JApiClass c) { return fieldNamed(c, "run"); }

    // ---- field annotation presence ----
    @Test void addedFieldAnnotationIsNew() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.NEW, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void removedFieldAnnotationIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); plainField(n, "public int run;");
        assertEquals(JApiChangeStatus.REMOVED, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void unchangedFieldAnnotationIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void addingAFieldAnnotationLeavesTheFieldUnchanged() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aFieldAnnotationReportsItsFullyQualifiedName() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(D, annoOnField(run(onlyClass(compare(o, n))), D).getFullyQualifiedName());
    }
    @Test void oneAddedFieldAnnotationCountsOne() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(1, annoCountOnField(run(onlyClass(compare(o, n)))));
    }

    // ---- element values on a field annotation ----
    @Test void fieldAnnotationIntValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void fieldAnnotationIntValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 5);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 5);
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void fieldAnnotationStringValueChangeIsModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoField(o, "public int run;", D, "name", "x");
        CtClass n = k("a.C"); stringAnnoField(n, "public int run;", D, "name", "y");
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void fieldAnnotationStringValueUnchangedIsUnchanged() throws Exception {
        CtClass o = k("a.C"); stringAnnoField(o, "public int run;", D, "name", "same");
        CtClass n = k("a.C"); stringAnnoField(n, "public int run;", D, "name", "same");
        assertEquals(JApiChangeStatus.UNCHANGED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void aFieldAnnotationValueChangeMakesTheAnnotationModified() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2);
        assertEquals(JApiChangeStatus.MODIFIED, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aFieldAnnotationValueChangeLeavesTheFieldUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 2);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aFieldAnnotationElementReportsItsName() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "size", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "size", 2);
        assertEquals("size", elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "size").getName());
    }
    @Test void aSecondMemberValueChangeOnAFieldAnnotation() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "level", 3);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "level", 4);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "level").getChangeStatus());
    }

    // ---- annotated-field presence ----
    @Test void anAnnotatedFieldAddedIsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.NEW, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anAnnotatedFieldRemovedIsRemoved() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C");
        assertEquals(JApiChangeStatus.REMOVED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anUnchangedAnnotatedFieldIsUnchanged() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void aPlainFieldPresentOnBothSidesIsUnchanged() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); plainField(n, "public int run;");
        assertEquals(JApiChangeStatus.UNCHANGED, run(onlyClass(compare(o, n))).getChangeStatus());
    }
    @Test void anAddedAnnotatedFieldCarriesItsAnnotationAsNew() throws Exception {
        CtClass o = k("a.C");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.NEW, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }

    // ---- multiple fields ----
    @Test void addingAnAnnotationToOneOfTwoFields() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;"); plainField(o, "public int stop;");
        CtClass n = k("a.C"); markerField(n, "public int run;", D); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(annoOnField(fieldNamed(c, "run"), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoCountOnField(fieldNamed(c, "stop")) == 0);
    }
    @Test void changingAMemberOnOneOfTwoFields() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1); plainField(o, "public int stop;");
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 9); plainField(n, "public int stop;");
        JApiClass c = onlyClass(compare(o, n));
        assertTrue(elementNamed(annoOnField(fieldNamed(c, "run"), D), "count").getChangeStatus() == JApiChangeStatus.MODIFIED
                && annoCountOnField(fieldNamed(c, "stop")) == 0);
    }

    // ---- multi-class ----
    @Test void aClassSetClassifiesEachFieldAnnotationChange() throws Exception {
        CtClass aO = k("a.A"); plainField(aO, "public int run;");
        CtClass aN = k("a.A"); markerField(aN, "public int run;", D);
        CtClass bO = k("a.B"); markerField(bO, "public int run;", D);
        CtClass bN = k("a.B"); markerField(bN, "public int run;", D);
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoOnField(fieldNamed(classNamed(r, "a.A"), "run"), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoOnField(fieldNamed(classNamed(r, "a.B"), "run"), D).getChangeStatus() == JApiChangeStatus.UNCHANGED);
    }
    @Test void twoClassesWithDistinctFieldAnnotationChanges() throws Exception {
        CtClass aO = k("a.A"); plainField(aO, "public int run;");
        CtClass aN = k("a.A"); markerField(aN, "public int run;", D);
        CtClass bO = k("a.B"); markerField(bO, "public int run;", D);
        CtClass bN = k("a.B"); plainField(bN, "public int run;");
        List<JApiClass> r = compareAll(Arrays.asList(aO, bO), Arrays.asList(aN, bN));
        assertTrue(annoOnField(fieldNamed(classNamed(r, "a.A"), "run"), D).getChangeStatus() == JApiChangeStatus.NEW
                && annoOnField(fieldNamed(classNamed(r, "a.B"), "run"), D).getChangeStatus() == JApiChangeStatus.REMOVED);
    }
    @Test void theFullyQualifiedNameIsReported() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); plainField(n, "public int run;");
        assertEquals("a.C", onlyClass(compare(o, n)).getFullyQualifiedName());
    }

    // ---- second annotation type / string ----
    @Test void aSecondAnnotationTypeOnAFieldIsNew() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int run;");
        CtClass n = k("a.C"); markerField(n, "public int run;", I);
        assertEquals(JApiChangeStatus.NEW, annoOnField(run(onlyClass(compare(o, n))), I).getChangeStatus());
    }
    @Test void aStringMemberAddedOnAFieldAnnotation() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); stringAnnoField(n, "public int run;", D, "name", "x");
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void aStringMemberRemovedOnAFieldAnnotation() throws Exception {
        CtClass o = k("a.C"); stringAnnoField(o, "public int run;", D, "name", "x");
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "name").getChangeStatus());
    }
    @Test void anIntMemberAddedOnAFieldAnnotation() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 1);
        assertEquals(JApiChangeStatus.NEW, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void anIntMemberRemovedOnAFieldAnnotation() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 1);
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.REMOVED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void aMarkerFieldAnnotationHasNoElements() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(0, annoOnField(run(onlyClass(compare(o, n))), D).getElements().size());
    }
    @Test void aNewClassWithAnAnnotatedFieldMarksTheFieldNew() throws Exception {
        CtClass n = k("a.C"); markerField(n, "public int run;", D);
        assertEquals(JApiChangeStatus.NEW, run(onlyClass(compare(null, n))).getChangeStatus());
    }
    @Test void aDeletedClassWithAnAnnotatedFieldMarksTheFieldRemoved() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        assertEquals(JApiChangeStatus.REMOVED, run(onlyClass(compare(o, null))).getChangeStatus());
    }
    @Test void anIntValueZeroToOneIsModified() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 0);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 4);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), D), "count").getChangeStatus());
    }
    @Test void aStringMemberChangeMakesAnnotationModified() throws Exception {
        CtClass o = k("a.C"); stringAnnoField(o, "public int run;", D, "name", "a");
        CtClass n = k("a.C"); stringAnnoField(n, "public int run;", D, "name", "b");
        assertEquals(JApiChangeStatus.MODIFIED, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void anUnchangedIntMemberKeepsAnnotationUnchanged() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", D, "count", 8);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", D, "count", 8);
        assertEquals(JApiChangeStatus.UNCHANGED, annoOnField(run(onlyClass(compare(o, n))), D).getChangeStatus());
    }
    @Test void aStopFieldAnnotationIsAlsoTracked() throws Exception {
        CtClass o = k("a.C"); plainField(o, "public int stop;");
        CtClass n = k("a.C"); markerField(n, "public int stop;", D);
        assertEquals(JApiChangeStatus.NEW, annoOnField(fieldNamed(onlyClass(compare(o, n)), "stop"), D).getChangeStatus());
    }
    @Test void anAnnotatedFieldOnTheOldSideOnlyIsRemovedWithItsAnnotation() throws Exception {
        CtClass o = k("a.C"); markerField(o, "public int run;", D);
        CtClass n = k("a.C");
        JApiField m = run(onlyClass(compare(o, n)));
        assertTrue(m.getChangeStatus() == JApiChangeStatus.REMOVED && annoOnField(m, D).getChangeStatus() == JApiChangeStatus.REMOVED);
    }
    @Test void anIntMemberChangeOnASecondAnnotationType() throws Exception {
        CtClass o = k("a.C"); intAnnoField(o, "public int run;", I, "level", 1);
        CtClass n = k("a.C"); intAnnoField(n, "public int run;", I, "level", 2);
        assertEquals(JApiChangeStatus.MODIFIED, elementNamed(annoOnField(run(onlyClass(compare(o, n))), I), "level").getChangeStatus());
    }
}
