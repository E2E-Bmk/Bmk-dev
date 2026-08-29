package integration;

import io.github.classgraph.Resource;
import io.github.classgraph.ResourceList;
import io.github.classgraph.ScanResult;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import support.OracleSupport;

import java.nio.file.Path;
import java.util.List;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class ResourcesAtomicTest {
    /**
     * Verifies: CG-RES-001.
     * Seam: protocol handoff from accepted path configuration to exact resource lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void exactPathLookupReturnsOneResource(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of("templates/page.html"),
                    result.getResourcesWithPath("templates/page.html").getPaths());
        }
    }

    /**
     * Verifies: CG-RES-001.
     * Seam: protocol handoff from resource indexing to leaf-name lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void leafNameLookupReturnsConcretePath(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of("templates/page.html"), result.getResourcesWithLeafName("page.html").getPaths());
        }
    }

    /**
     * Verifies: CG-RES-001.
     * Seam: protocol handoff from resource indexing to extension lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void extensionLookupReturnsBothHtmlResources(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of("templates/page.html", "templates/admin/panel.html"),
                    result.getResourcesWithExtension("html").getPaths());
        }
    }

    /**
     * Verifies: CG-RES-001.
     * Seam: protocol handoff from resource indexing to regular-expression lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void patternLookupReturnsBothHtmlResources(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of("templates/page.html", "templates/admin/panel.html"),
                    result.getResourcesMatchingPattern(Pattern.compile("templates/.+\\.html")).getPaths());
        }
    }

    /**
     * Verifies: CG-RES-001.
     * Seam: protocol handoff from resource indexing to wildcard lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void wildcardLookupReturnsBothHtmlResources(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of("templates/page.html", "templates/admin/panel.html"),
                    result.getResourcesMatchingWildcard("templates/**/*.html").getPaths());
        }
    }

    /**
     * Verifies: CG-RES-002.
     * Seam: config interaction between accepted regions and ignoring-accept lookup.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void ignoringAcceptLookupFindsUnacceptedResource(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of("root.data"), result.getResourcesWithPathIgnoringAccept("root.data").getPaths());
        }
    }

    /**
     * Verifies: CG-RES-008, CG-RES-009.
     * Seam: protocol handoff from resource lookup to UTF-8 content loading.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void utf8StringLoadReturnsCompleteContent(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals("alpha-β", result.getResourcesWithPath("templates/page.html").get(0).loadAsString());
        }
    }

    /**
     * Verifies: CG-EXEC-007, CG-ERR-007.
     * Seam: state consistency between resource index absence and typed empty projection.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void missingResourceLookupReturnsTypedEmptyList(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertEquals(List.of(), result.getResourcesWithPath("templates/missing.html").getPaths());
        }
    }

    /**
     * Verifies: CG-RES-019.
     * Seam: protocol handoff from typed list factory to read-only path projection.
     * Depends-On: SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void emptyResourceFactorySupportsReadOnlyProjection() {
        assertEquals(List.of(), ResourceList.emptyList().getPaths());
    }

    /**
     * Verifies: CG-RES-007, CG-ERR-001.
     * Seam: error propagation from invalid resource lookup to the public exception contract.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void nullResourcePathIsRejected(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            assertThrows(NullPointerException.class, () -> result.getResourcesWithPath(null));
        }
    }

    /**
     * Verifies: CG-RES-013, CG-ERR-004, CG-ERR-005.
     * Seam: lifecycle crossing from ScanResult closure to retained Resource access.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void retainedResourceCannotLoadAfterResultClose(@TempDir final Path temp) throws Exception {
        ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp));
        Resource resource = result.getResourcesWithPath("templates/page.html").get(0);
        result.close();
        assertThrows(IllegalStateException.class, resource::load);
    }
}
