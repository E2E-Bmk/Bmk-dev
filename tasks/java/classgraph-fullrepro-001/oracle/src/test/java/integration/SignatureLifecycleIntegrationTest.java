package integration;

import io.github.classgraph.ArrayClassInfo;
import io.github.classgraph.ArrayTypeSignature;
import io.github.classgraph.ClassInfo;
import io.github.classgraph.ClassRefTypeSignature;
import io.github.classgraph.FieldInfo;
import io.github.classgraph.MethodInfo;
import io.github.classgraph.MethodTypeSignature;
import io.github.classgraph.Resource;
import io.github.classgraph.ScanResult;
import io.github.classgraph.TypeArgument;
import io.github.classgraph.TypeParameter;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import support.FixtureTypes;
import support.OracleSupport;

import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SignatureLifecycleIntegrationTest {
    /**
     * Verifies: CG-CVI-007, CG-META-014, CG-META-015.
     * Seam: protocol handoff from field generic signature to referenced ClassInfo.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableExternalClassesReturnsSameBuilder.
     */
    @Test
    void genericFieldBoundAgreesWithReferencedClassInfo() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo().enableInterClassDependencies()
                .enableExternalClasses().scan()) {
            FieldInfo field = result.getClassInfo(FixtureTypes.GenericBox.class.getName()).getDeclaredFieldInfo("upper");
            TypeArgument argument = ((ClassRefTypeSignature) field.getTypeSignature()).getTypeArguments().get(0);
            ClassRefTypeSignature bound = (ClassRefTypeSignature) argument.getTypeSignature();
            assertEquals("java.lang.Number", bound.getFullyQualifiedClassName());
            assertEquals(bound.getFullyQualifiedClassName(), bound.getClassInfo().getName());
        }
    }

    /**
     * Verifies: CG-CVI-007, CG-META-014, CG-META-015.
     * Seam: protocol handoff from MethodInfo descriptor fallback to result-type ClassInfo.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableExternalClassesReturnsSameBuilder.
     */
    @Test
    void methodResultSignatureAgreesWithReferencedClassInfo() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo().enableExternalClasses().scan()) {
            MethodInfo method = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName())
                    .getDeclaredMethodInfo("box").get(0);
            MethodTypeSignature signature = method.getTypeSignatureOrTypeDescriptor();
            ClassRefTypeSignature resultType = (ClassRefTypeSignature) signature.getResultType();
            assertEquals(FixtureTypes.GenericBox.class.getName(), resultType.getFullyQualifiedClassName());
            assertEquals(resultType.getFullyQualifiedClassName(),
                    result.getClassInfo(resultType.getFullyQualifiedClassName()).getName());
        }
    }

    /**
     * Verifies: CG-CVI-007, CG-META-019.
     * Seam: state consistency between ArrayTypeSignature and ArrayClassInfo.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableExternalClassesReturnsSameBuilder.
     */
    @Test
    void arraySignatureAgreesWithArrayClassProjection() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo().enableExternalClasses().scan()) {
            ArrayTypeSignature signature = (ArrayTypeSignature) result
                    .getClassInfo(FixtureTypes.DirectPlugin.class.getName()).getDeclaredFieldInfo("matrix")
                    .getTypeSignatureOrTypeDescriptor();
            ArrayClassInfo arrayClass = signature.getArrayClassInfo();
            assertEquals(signature.getNumDimensions(), arrayClass.getNumDimensions());
            assertEquals(signature.getElementTypeSignature(), arrayClass.getElementTypeSignature());
            assertEquals("java.lang.String", arrayClass.getElementClassInfo().getName());
        }
    }

    /**
     * Verifies: CG-CVI-007, CG-META-015.
     * Seam: state consistency between class type parameters and referenced bound classes.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableExternalClassesReturnsSameBuilder.
     */
    @Test
    void classTypeParameterBoundsAgreeWithReferencedClasses() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo().enableExternalClasses().scan()) {
            TypeParameter parameter = result.getClassInfo(FixtureTypes.GenericBox.class.getName())
                    .getTypeSignature().getTypeParameters().get(0);
            ClassRefTypeSignature classBound = (ClassRefTypeSignature) parameter.getClassBound();
            ClassRefTypeSignature interfaceBound = (ClassRefTypeSignature) parameter.getInterfaceBounds().get(0);
            assertEquals(List.of("java.lang.Number", "java.lang.Comparable"),
                    List.of(classBound.getClassInfo().getName(), interfaceBound.getClassInfo().getName()));
        }
    }

    /**
     * Verifies: CG-CVI-008, CG-EXEC-011, CG-STATE-004.
     * Seam: lifecycle crossing from open class metadata to a closed snapshot.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void retainedClassCannotBeReachedThroughClosedResult() {
        ScanResult result = OracleSupport.scanAllInfo();
        ClassInfo retained = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
        assertEquals(List.of("indexed"), retained.getDeclaredMethodInfo("indexed").getNames());
        result.close();
        assertThrows(IllegalStateException.class, () -> result.getClassInfo(retained.getName()));
    }

    /**
     * Verifies: CG-CVI-008, CG-RES-013, CG-STATE-004.
     * Seam: error propagation across ScanResult closure and retained Resource content access.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void retainedResourceLoadFailsAfterClose(@TempDir final Path temp) throws Exception {
        ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp));
        Resource retained = result.getResourcesWithPath("templates/page.html").get(0);
        assertEquals("alpha-β", retained.loadAsString());
        result.close();
        assertThrows(IllegalStateException.class, retained::load);
    }

    /**
     * Verifies: CG-CVI-008, CG-EXEC-011, CG-ERR-004.
     * Seam: error propagation across closure to class and resource result queries.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void closedResultRejectsClassAndResourceQueries() {
        ScanResult result = OracleSupport.scanAllInfo();
        assertTrue(result.getAllClasses().containsName(FixtureTypes.DirectPlugin.class.getName()));
        result.close();
        assertThrows(IllegalStateException.class, result::getAllClasses);
        assertThrows(IllegalStateException.class, result::getAllResources);
    }

    /**
     * Verifies: CG-CVI-008, CG-EXEC-012, CG-STATE-004.
     * Seam: lifecycle crossing from global closeAll to two snapshots and retained metadata.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void closeAllInvalidatesQueriesOnMultipleSnapshots() {
        ScanResult first = OracleSupport.scanAllInfo();
        ScanResult second = OracleSupport.scanAllInfo();
        ClassInfo retained = first.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
        ScanResult.closeAll();
        assertEquals(List.of(true, true), List.of(first.isClosed(), second.isClosed()));
        assertThrows(IllegalStateException.class, () -> first.getClassInfo(retained.getName()));
        assertThrows(IllegalStateException.class, second::getAllResources);
    }
}
