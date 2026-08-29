package integration;

import io.github.classgraph.ClassInfo;
import io.github.classgraph.ClassInfoList;
import io.github.classgraph.ScanResult;
import org.junit.jupiter.api.Test;
import support.FixtureTypes;
import support.OracleSupport;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ClassGraphAtomicTest {
    /**
     * Verifies: CG-GRAPH-001.
     * Seam: state consistency between scan selection and class identity projection.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void classIdentityReportsFixtureName() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            assertEquals(FixtureTypes.DirectPlugin.class.getName(),
                    result.getClassInfo(FixtureTypes.DirectPlugin.class.getName()).getName());
        }
    }

    /**
     * Verifies: CG-GRAPH-001.
     * Seam: state consistency between class identity and name projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void classIdentityReportsSimpleAndPackageNames() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            assertEquals(List.of("DirectPlugin", "support"), List.of(info.getSimpleName(), info.getPackageName()));
        }
    }

    /**
     * Verifies: CG-GRAPH-002.
     * Seam: protocol handoff from classfile scanning to kind predicates.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void standardClassKindIsDistinguished() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            assertEquals(List.of(true, false, false),
                    List.of(info.isStandardClass(), info.isInterface(), info.isAnnotation()));
        }
    }

    /**
     * Verifies: CG-GRAPH-002.
     * Seam: protocol handoff from classfile scanning to interface predicates.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void interfaceKindIsDistinguished() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.Plugin.class.getName());
            assertTrue(info.isInterface());
            assertFalse(info.isAnnotation());
        }
    }

    /**
     * Verifies: CG-GRAPH-002.
     * Seam: protocol handoff from classfile scanning to annotation predicates.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void annotationKindIsDistinguished() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.Tagged.class.getName());
            assertEquals(List.of(true, true), List.of(info.isAnnotation(), info.isInterfaceOrAnnotation()));
        }
    }

    /**
     * Verifies: CG-GRAPH-002.
     * Seam: config interaction between all-info enablement and enum field projection.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void enumKindAndConstantsAreDistinguished() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.Shade.class.getName());
            assertTrue(info.isEnum());
            assertEquals(List.of("RED", "GREEN"), info.getFieldInfo().filter(field -> field.isEnum()).getNames());
        }
    }

    /**
     * Verifies: CG-GRAPH-002.
     * Seam: protocol handoff from classfile scanning to record predicates.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void recordKindIsDistinguished() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            assertTrue(result.getClassInfo(FixtureTypes.Point.class.getName()).isRecord());
        }
    }

    /**
     * Verifies: CG-GRAPH-005.
     * Seam: state consistency between scanned inheritance edges and transitive traversal.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void allSubclassQueryReturnsTransitiveDescendants() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            Set<String> names = new LinkedHashSet<>(result.getAllSubclasses(FixtureTypes.BasePlugin.class).getNames());
            assertEquals(Set.of(FixtureTypes.DirectPlugin.class.getName(), FixtureTypes.ChildPlugin.class.getName(),
                    FixtureTypes.LeafPlugin.class.getName()), names);
        }
    }

    /**
     * Verifies: CG-GRAPH-005.
     * Seam: state consistency between scanned inheritance edges and direct traversal.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void directSubclassQueryReturnsImmediateDescendant() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            assertEquals(List.of(FixtureTypes.DirectPlugin.class.getName()),
                    result.getDirectSubclasses(FixtureTypes.BasePlugin.class).getNames());
        }
    }

    /**
     * Verifies: CG-GRAPH-010, CG-GRAPH-011.
     * Seam: protocol handoff from relationship queries to list algebra.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void classListAlgebraProducesConcreteSetRelations() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfoList all = result.getAllSubclasses(FixtureTypes.BasePlugin.class);
            ClassInfoList direct = result.getDirectSubclasses(FixtureTypes.BasePlugin.class);
            assertEquals(direct.getNames(), all.intersect(direct).getNames());
            assertEquals(2, all.exclude(direct).size());
            assertEquals(new LinkedHashSet<>(all.getNames()), new LinkedHashSet<>(direct.union(all).getNames()));
        }
    }
}
