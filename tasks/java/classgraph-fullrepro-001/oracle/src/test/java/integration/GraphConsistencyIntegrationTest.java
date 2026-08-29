package integration;

import io.github.classgraph.ClassInfo;
import io.github.classgraph.ClassInfoList;
import io.github.classgraph.PackageInfo;
import io.github.classgraph.Resource;
import io.github.classgraph.ScanResult;
import org.junit.jupiter.api.Test;
import support.FixtureTypes;
import support.OracleSupport;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GraphConsistencyIntegrationTest {
    /**
     * Verifies: CG-CVI-001, CG-GRAPH-001, CG-RES-016.
     * Seam: state consistency across relationship and package projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void relationshipClassAgreesWithPackageProjection() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo related = result.getAllSubclasses(FixtureTypes.BasePlugin.class)
                    .get(FixtureTypes.ChildPlugin.class.getName());
            PackageInfo packageInfo = related.getPackageInfo();
            ClassInfo packaged = packageInfo.getClassInfoRecursive().get(related.getName());
            assertEquals(List.of(related.getName(), related.getClasspathElementURI()),
                    List.of(packaged.getName(), packaged.getClasspathElementURI()));
        }
    }

    /**
     * Verifies: CG-CVI-001, CG-GRAPH-001, CG-RES-003.
     * Seam: state consistency across class relationship and defining-resource views.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void relationshipClassAgreesWithDefiningResourceProjection() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo related = result.getAllSubclasses(FixtureTypes.BasePlugin.class)
                    .get(FixtureTypes.DirectPlugin.class.getName());
            Resource fromClass = related.getResource();
            Resource fromResult = result.getResourcesWithPath(fromClass.getPath()).get(0);
            assertEquals(List.of(fromClass.getPath(), fromClass.getURI()),
                    List.of(fromResult.getPath(), fromResult.getURI()));
        }
    }

    /**
     * Verifies: CG-CVI-001, CG-RES-016, CG-STATE-002.
     * Seam: protocol handoff from ScanResult class lookup to package recursion.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void scanLookupAndPackageLookupIdentifySameClassfile() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo scanned = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            ClassInfo packaged = result.getPackageInfo("support").getClassInfoRecursive().get(scanned.getName());
            assertEquals(List.of(scanned.getName(), scanned.getSourceFile(), scanned.getClassfileMajorVersion()),
                    List.of(packaged.getName(), packaged.getSourceFile(), packaged.getClassfileMajorVersion()));
        }
    }

    /**
     * Verifies: CG-CVI-001, CG-RES-005, CG-STATE-002.
     * Seam: protocol handoff from package class membership to classpath resource identity.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void packageClassAndResourceShareClasspathIdentity() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo packaged = result.getPackageInfo("support").getClassInfoRecursive()
                    .get(FixtureTypes.LeafPlugin.class.getName());
            Resource resource = result.getResourcesWithPath(packaged.getResource().getPath()).get(0);
            assertEquals(packaged.getClasspathElementURI(), resource.getClasspathElementURI());
            assertEquals(packaged.getName().replace('.', '/') + ".class", resource.getPath());
        }
    }

    /**
     * Verifies: CG-CVI-002, CG-GRAPH-005, CG-GRAPH-009.
     * Seam: protocol handoff between transitive and direct subclass projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void allSubclassesContainAndRecoverDirectSubclasses() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfoList all = result.getAllSubclasses(FixtureTypes.BasePlugin.class);
            ClassInfoList direct = result.getDirectSubclasses(FixtureTypes.BasePlugin.class);
            assertTrue(all.getNames().containsAll(direct.getNames()));
            assertEquals(direct.getNames(), all.directOnly().getNames());
        }
    }

    /**
     * Verifies: CG-CVI-002, CG-GRAPH-005, CG-GRAPH-009.
     * Seam: protocol handoff between transitive and direct implementation projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void allImplementationsContainAndRecoverDirectImplementations() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfoList all = result.getAllClassesImplementing(FixtureTypes.Plugin.class);
            ClassInfoList direct = result.getDirectClassesImplementing(FixtureTypes.Plugin.class);
            assertTrue(all.getNames().containsAll(direct.getNames()));
            assertEquals(new LinkedHashSet<>(direct.getNames()), new LinkedHashSet<>(all.directOnly().getNames()));
        }
    }

    /**
     * Verifies: CG-CVI-002, CG-GRAPH-005, CG-GRAPH-009.
     * Seam: state consistency across ClassInfo superclass and ScanResult relationship views.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void superclassAndSubclassViewsAreMutuallyConsistent() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfo leaf = result.getClassInfo(FixtureTypes.LeafPlugin.class.getName());
            Set<String> ancestors = new LinkedHashSet<>(leaf.getAllSuperclasses().getNames());
            ClassInfoList descendants = result.getAllSubclasses(FixtureTypes.BasePlugin.class);
            assertTrue(ancestors.contains(FixtureTypes.BasePlugin.class.getName()));
            assertTrue(descendants.containsName(leaf.getName()));
        }
    }

    /**
     * Verifies: CG-CVI-002, CG-GRAPH-005, CG-GRAPH-009.
     * Seam: state consistency between all and direct subinterface views.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void allSubinterfacesContainAndRecoverDirectSubinterfaces() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            ClassInfoList all = result.getAllSubinterfaces(FixtureTypes.Plugin.class);
            ClassInfoList direct = result.getDirectSubinterfaces(FixtureTypes.Plugin.class);
            assertEquals(Set.of(FixtureTypes.AdvancedPlugin.class.getName(), FixtureTypes.ExpertPlugin.class.getName()),
                    new LinkedHashSet<>(all.getNames()));
            assertEquals(direct.getNames(), all.directOnly().getNames());
        }
    }
}
