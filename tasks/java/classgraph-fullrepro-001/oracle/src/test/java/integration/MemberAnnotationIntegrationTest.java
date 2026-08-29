package integration;

import io.github.classgraph.AnnotationInfo;
import io.github.classgraph.ClassInfo;
import io.github.classgraph.FieldInfo;
import io.github.classgraph.HasAnnotations;
import io.github.classgraph.MethodInfo;
import io.github.classgraph.MethodParameterInfo;
import io.github.classgraph.ScanResult;
import org.junit.jupiter.api.Test;
import support.FixtureTypes;
import support.OracleSupport;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class MemberAnnotationIntegrationTest {
    /**
     * Verifies: CG-CVI-003, CG-META-001, CG-META-003.
     * Seam: state consistency across ClassInfo and MethodInfo ownership views.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void methodOwnerAgreesWithDeclaringClassProjection() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            MethodInfo method = owner.getDeclaredMethodInfo("indexed").get(0);
            assertEquals(List.of(owner.getName(), "indexed"), List.of(method.getClassInfo().getName(), method.getName()));
            assertEquals(owner.getName(), method.getClassName());
        }
    }

    /**
     * Verifies: CG-CVI-003, CG-META-002, CG-META-003.
     * Seam: state consistency across ClassInfo and FieldInfo ownership views.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void fieldOwnerAgreesWithDeclaringClassProjection() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            FieldInfo field = owner.getDeclaredFieldInfo("MAGIC");
            assertEquals(List.of(owner.getName(), "MAGIC", 41),
                    List.of(field.getClassInfo().getName(), field.getName(), field.getConstantInitializerValue()));
        }
    }

    /**
     * Verifies: CG-CVI-003, CG-META-003, CG-META-004.
     * Seam: protocol handoff from MethodInfo to MethodParameterInfo.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void parameterViewRetainsMethodIdentityAndPosition() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            MethodInfo method = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getDeclaredMethodInfo("indexed").get(0);
            MethodParameterInfo parameter = method.getParameterInfo().get(1);
            assertEquals(List.of(method.getName(), 1, "values"),
                    List.of(parameter.getMethodInfo().getName(), parameter.getIndex(), parameter.getName()));
            assertEquals(method.isVarArgs(), parameter.isVarArgs());
        }
    }

    /**
     * Verifies: CG-CVI-003, CG-META-003, CG-META-014.
     * Seam: protocol handoff from field metadata to signature fallback.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void fieldSignatureFallbackAgreesAcrossMemberViews() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            FieldInfo field = owner.getDeclaredFieldInfo("matrix");
            assertEquals(field.getTypeSignatureOrTypeDescriptor(),
                    owner.getFieldInfo("matrix").getTypeSignatureOrTypeDescriptor());
            assertEquals(2, ((io.github.classgraph.ArrayTypeSignature) field.getTypeSignatureOrTypeDescriptor())
                    .getNumDimensions());
        }
    }

    /**
     * Verifies: CG-CVI-004, CG-META-007, CG-META-010.
     * Seam: state consistency between HasAnnotations and AnnotationInfo projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void classAnnotationIsNameAddressableThroughBothViews() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            HasAnnotations annotated = owner;
            AnnotationInfo annotation = annotated.getAllAnnotationInfo().get(FixtureTypes.Tagged.class.getName());
            assertEquals(FixtureTypes.Tagged.class.getName(), annotation.getName());
            assertEquals("direct", annotation.getParameterValues().getValue("value"));
        }
    }

    /**
     * Verifies: CG-CVI-004, CG-META-007, CG-META-008.
     * Seam: protocol handoff from annotation-driven method selection to member annotation lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void methodAnnotationSelectionAgreesWithMethodView() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            MethodInfo method = owner.getDeclaredMethodInfoWithAnnotation(FixtureTypes.Tagged.class.getName()).stream()
                    .filter(candidate -> candidate.getName().equals("convert")).findFirst().orElseThrow();
            assertTrue(method.hasAnnotation(FixtureTypes.Tagged.class.getName()));
            assertEquals("override", method.getAllAnnotationInfo().get(FixtureTypes.Tagged.class.getName())
                    .getParameterValues().getValue("value"));
        }
    }

    /**
     * Verifies: CG-CVI-004, CG-META-007, CG-META-010.
     * Seam: protocol handoff from annotation-driven field selection to parameter values.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void fieldAnnotationSelectionAgreesWithMergedAndDeclaredValues() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassInfo(FixtureTypes.BasePlugin.class.getName());
            FieldInfo field = owner.getDeclaredFieldInfoWithAnnotation(FixtureTypes.Tagged.class.getName()).get(0);
            AnnotationInfo annotation = field.getAllAnnotationInfo().get(FixtureTypes.Tagged.class.getName());
            assertEquals(List.of("value"), annotation.getDeclaredParameterValues().getNames());
            assertEquals(List.of("base-field", 7), List.of(annotation.getParameterValues().getValue("value"),
                    annotation.getParameterValues().getValue("rank")));
        }
    }

    /**
     * Verifies: CG-CVI-004, CG-META-007, CG-META-010.
     * Seam: state consistency between parameter annotation selection and parameter metadata.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void parameterAnnotationSelectionAgreesWithParameterView() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo owner = result.getClassesWithMethodParameterAnnotation(FixtureTypes.Tagged.class.getName())
                    .get(FixtureTypes.DirectPlugin.class.getName());
            MethodInfo method = owner.getDeclaredMethodInfo("convert").stream()
                    .filter(candidate -> candidate.hasParameterAnnotation(FixtureTypes.Tagged.class.getName()))
                    .findFirst().orElseThrow();
            AnnotationInfo annotation = method.getParameterInfo().get(0).getAllAnnotationInfo()
                    .get(FixtureTypes.Tagged.class.getName());
            assertEquals("child-input", annotation.getParameterValues().getValue("value"));
            assertEquals(7, annotation.getParameterValues().getValue("rank"));
        }
    }
}
