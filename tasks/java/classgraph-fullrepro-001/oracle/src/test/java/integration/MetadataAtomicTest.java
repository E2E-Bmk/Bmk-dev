package integration;

import io.github.classgraph.AnnotationInfo;
import io.github.classgraph.ArrayTypeSignature;
import io.github.classgraph.ClassInfo;
import io.github.classgraph.ClassRefTypeSignature;
import io.github.classgraph.FieldInfo;
import io.github.classgraph.MethodInfo;
import io.github.classgraph.ScanResult;
import io.github.classgraph.TypeArgument;
import org.junit.jupiter.api.Test;
import support.FixtureTypes;
import support.OracleSupport;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class MetadataAtomicTest {
    /**
     * Verifies: CG-META-001.
     * Seam: protocol handoff from all-info configuration to declared method selection.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void declaredMethodNameFilterSelectsOneMethod() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            assertEquals(List.of("indexed"), result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getDeclaredMethodInfo("indexed").getNames());
        }
    }

    /**
     * Verifies: CG-META-002.
     * Seam: config interaction between all-info and ignored field visibility.
     * Depends-On: SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#ignoreFieldVisibilityReturnsSameBuilder.
     */
    @Test
    void declaredFieldsPreserveClassfileOrder() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo().ignoreFieldVisibility().scan()) {
            assertEquals(List.of("MAGIC", "LABEL", "names", "matrix", "hidden"),
                    result.getClassInfo(FixtureTypes.DirectPlugin.class.getName()).getDeclaredFieldInfo().getNames());
        }
    }

    /**
     * Verifies: CG-META-005.
     * Seam: protocol handoff from static-final capture configuration to FieldInfo value projection.
     * Depends-On: SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableStaticFinalValuesReturnsSameBuilder.
     */
    @Test
    void staticFinalConstantInitializerIsCaptured() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            FieldInfo field = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getDeclaredFieldInfo("MAGIC");
            assertEquals(41, field.getConstantInitializerValue());
        }
    }

    /**
     * Verifies: CG-META-004.
     * Seam: state consistency between method metadata and parameter projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void methodParametersPreserveNamesAndIndexes() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            MethodInfo method = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getDeclaredMethodInfo("indexed").get(0);
            assertEquals(List.of("prefix", "values"),
                    method.getParameterInfo().stream().map(parameter -> parameter.getName()).toList());
            assertEquals(List.of(0, 1), method.getParameterInfo().stream().map(parameter -> parameter.getIndex()).toList());
        }
    }

    /**
     * Verifies: CG-META-004.
     * Seam: state consistency between method varargs state and parameter varargs state.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void methodAndLastParameterAgreeOnVarargs() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            MethodInfo method = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getDeclaredMethodInfo("indexed").get(0);
            assertEquals(List.of(true, true),
                    List.of(method.isVarArgs(), method.getParameterInfo().get(1).isVarArgs()));
        }
    }

    /**
     * Verifies: CG-META-010, CG-META-011.
     * Seam: protocol handoff from annotation scanning to merged parameter values.
     * Depends-On: SourceSelectionAtomicTest#enableAnnotationInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void annotationMergedValuesExposeConcreteParameters() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            AnnotationInfo annotation = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getAllAnnotationInfo().get(FixtureTypes.Tagged.class.getName());
            assertEquals(List.of("direct", 13), List.of(annotation.getParameterValues().getValue("value"),
                    annotation.getParameterValues().getValue("rank")));
        }
    }

    /**
     * Verifies: CG-META-010.
     * Seam: state consistency between declared and defaulted annotation values.
     * Depends-On: SourceSelectionAtomicTest#enableAnnotationInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void annotationDefaultsAppearOnlyInMergedValues() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            AnnotationInfo annotation = result.getClassInfo(FixtureTypes.BasePlugin.class.getName())
                    .getDeclaredFieldInfo("baseField").getAllAnnotationInfo().get(FixtureTypes.Tagged.class.getName());
            assertEquals(List.of("value"), annotation.getDeclaredParameterValues().getNames());
            assertEquals(7, annotation.getParameterValues().getValue("rank"));
        }
    }

    /**
     * Verifies: CG-META-009.
     * Seam: protocol handoff from repeatable container scanning to expanded annotations.
     * Depends-On: SourceSelectionAtomicTest#enableAnnotationInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void repeatableAnnotationQueryExpandsBothInstances() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            List<Object> values = result.getClassInfo(FixtureTypes.RepeatableTarget.class.getName())
                    .getAllAnnotationInfoRepeatable(FixtureTypes.Label.class.getName()).stream()
                    .map(annotation -> annotation.getParameterValues().getValue("value")).toList();
            assertEquals(Set.of("north", "south"), new LinkedHashSet<>(values));
        }
    }

    /**
     * Verifies: CG-META-015.
     * Seam: protocol handoff from classfile signature parsing to type-parameter bounds.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void genericClassTypeParameterPreservesBounds() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo generic = result.getClassInfo(FixtureTypes.GenericBox.class.getName());
            assertEquals("T", generic.getTypeSignature().getTypeParameters().get(0).getName());
            assertEquals(1, generic.getTypeSignature().getTypeParameters().get(0).getInterfaceBounds().size());
        }
    }

    /**
     * Verifies: CG-META-017, CG-META-018.
     * Seam: protocol handoff from field signature parsing to wildcard projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void genericFieldWildcardsPreserveDirectionAndBounds() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo generic = result.getClassInfo(FixtureTypes.GenericBox.class.getName());
            TypeArgument upper = ((ClassRefTypeSignature) generic.getDeclaredFieldInfo("upper").getTypeSignature())
                    .getTypeArguments().get(0);
            TypeArgument lower = ((ClassRefTypeSignature) generic.getDeclaredFieldInfo("lower").getTypeSignature())
                    .getTypeArguments().get(0);
            assertEquals(List.of(TypeArgument.Wildcard.EXTENDS, TypeArgument.Wildcard.SUPER),
                    List.of(upper.getWildcard(), lower.getWildcard()));
            assertEquals(List.of("java.lang.Number", "java.lang.Integer"), List.of(
                    ((ClassRefTypeSignature) upper.getTypeSignature()).getFullyQualifiedClassName(),
                    ((ClassRefTypeSignature) lower.getTypeSignature()).getFullyQualifiedClassName()));
        }
    }

    /**
     * Verifies: CG-META-019.
     * Seam: state consistency between parsed array dimensions and element signature.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void arrayTypePreservesDimensionsAndElement() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ArrayTypeSignature signature = (ArrayTypeSignature) result
                    .getClassInfo(FixtureTypes.DirectPlugin.class.getName()).getDeclaredFieldInfo("matrix")
                    .getTypeSignatureOrTypeDescriptor();
            assertEquals(2, signature.getNumDimensions());
            assertEquals("java.lang.String",
                    ((ClassRefTypeSignature) signature.getElementTypeSignature()).getFullyQualifiedClassName());
        }
    }

    /**
     * Verifies: CG-META-006, CG-ERR-003.
     * Seam: error propagation from disabled method capability to metadata query.
     * Depends-On: SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void methodQueryWithoutCapabilityIsRejected() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            assertThrows(IllegalStateException.class, info::getMethodInfo);
        }
    }
}
