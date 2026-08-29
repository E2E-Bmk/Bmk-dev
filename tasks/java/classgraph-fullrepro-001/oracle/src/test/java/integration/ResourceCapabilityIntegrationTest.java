package integration;

import io.github.classgraph.ClassInfo;
import io.github.classgraph.Resource;
import io.github.classgraph.ResourceList;
import io.github.classgraph.ScanResult;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import support.FixtureTypes;
import support.OracleSupport;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ResourceCapabilityIntegrationTest {
    /**
     * Verifies: CG-CVI-005, CG-RES-001, CG-RES-008.
     * Seam: state consistency between exact-path and extension resource projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void exactPathAndExtensionViewsExposeSameResource(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            Resource exact = result.getResourcesWithPath("templates/page.html").get(0);
            Resource extension = result.getResourcesWithExtension("html").get("templates/page.html").get(0);
            assertEquals(List.of(exact.getURI(), exact.loadAsString()),
                    List.of(extension.getURI(), extension.loadAsString()));
        }
    }

    /**
     * Verifies: CG-CVI-005, CG-RES-001, CG-RES-008.
     * Seam: state consistency between wildcard and regular-expression projections.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void wildcardAndPatternViewsExposeSamePathsAndBytes(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            ResourceList wildcard = result.getResourcesMatchingWildcard("templates/**/*.html");
            ResourceList pattern = result.getResourcesMatchingPattern(Pattern.compile("templates/.+\\.html"));
            assertEquals(wildcard.getPaths(), pattern.getPaths());
            assertEquals(wildcard.get(0).loadAsString(), pattern.get(0).loadAsString());
        }
    }

    /**
     * Verifies: CG-CVI-005, CG-RES-008, CG-RES-011.
     * Seam: protocol handoff from ResourceList bulk loading to direct Resource loading.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void bulkByteArraysAgreeWithDirectResourceLoads(@TempDir final Path temp) throws Exception {
        try (ScanResult result = OracleSupport.scanResources(OracleSupport.writeResourceTree(temp))) {
            ResourceList resources = result.getResourcesWithExtension("html");
            Map<String, byte[]> bulk = new LinkedHashMap<>();
            ResourceList returned = resources.forEachByteArray((resource, bytes) -> bulk.put(resource.getPath(), bytes));
            assertEquals(resources, returned);
            for (Resource resource : resources) {
                assertTrue(Arrays.equals(resource.load(), bulk.get(resource.getPath())));
            }
        }
    }

    /**
     * Verifies: CG-CVI-005, CG-RES-006, CG-RES-008.
     * Seam: protocol handoff from duplicate-path grouping to direct content access.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#acceptPathsReturnsSameBuilder.
     */
    @Test
    void duplicatePathGroupsRetainBothResourceContents(@TempDir final Path temp) throws Exception {
        Path first = Files.createDirectories(temp.resolve("first/shared"));
        Path second = Files.createDirectories(temp.resolve("second/shared"));
        Files.writeString(first.resolve("value.txt"), "first-value", StandardCharsets.UTF_8);
        Files.writeString(second.resolve("value.txt"), "second-value", StandardCharsets.UTF_8);
        try (ScanResult result = new io.github.classgraph.ClassGraph()
                .enableClasspathEntries(temp.resolve("first").toFile(), temp.resolve("second").toFile())
                .acceptPaths("shared").scan()) {
            ResourceList exact = result.getResourcesWithPath("shared/value.txt");
            ResourceList mapped = result.getAllResourcesAsMap().get("shared/value.txt");
            List<String> contents = new ArrayList<>();
            for (Resource resource : mapped) {
                contents.add(resource.loadAsString());
            }
            assertEquals(2, exact.size());
            assertEquals(List.of("first-value", "second-value"), contents);
            assertEquals(1, result.getAllResources().findDuplicatePaths().size());
        }
    }

    /**
     * Verifies: CG-CVI-006, CG-SRC-014, CG-EXEC-006.
     * Seam: config interaction between enableAllInfo and capability booleans.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder.
     */
    @Test
    void enableAllInfoSetsEveryExposedCapabilityBoolean() {
        try (ScanResult result = OracleSupport.scanAllInfo()) {
            assertEquals(List.of(true, true, true, true), List.of(result.isClassInfoEnabled(),
                    result.isMethodInfoEnabled(), result.isFieldInfoEnabled(), result.isAnnotationInfoEnabled()));
        }
    }

    /**
     * Verifies: CG-CVI-006, CG-SRC-013, CG-STATE-003.
     * Seam: config interaction between class-only configuration and disabled metadata views.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder, SourceSelectionAtomicTest#enableClassInfoReturnsSameBuilder.
     */
    @Test
    void classOnlyScanExposesClassCapabilityAndRejectsMethodView() {
        try (ScanResult result = OracleSupport.scanClassInfo()) {
            assertEquals(List.of(true, false, false, false), List.of(result.isClassInfoEnabled(),
                    result.isMethodInfoEnabled(), result.isFieldInfoEnabled(), result.isAnnotationInfoEnabled()));
            ClassInfo info = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            org.junit.jupiter.api.Assertions.assertThrows(IllegalStateException.class, info::getMethodInfo);
        }
    }

    /**
     * Verifies: CG-CVI-006, CG-SRC-015, CG-EXEC-006.
     * Seam: config interaction between visibility policies and member projections.
     * Depends-On: SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#ignoreMethodVisibilityReturnsSameBuilder, SourceSelectionAtomicTest#ignoreFieldVisibilityReturnsSameBuilder.
     */
    @Test
    void visibilityPoliciesAgreeWithHiddenMemberProjections() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo()
                .ignoreMethodVisibility().ignoreFieldVisibility().scan()) {
            ClassInfo info = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            assertEquals(List.of(true, true),
                    List.of(result.isMethodVisibilityIgnored(), result.isFieldVisibilityIgnored()));
            assertTrue(info.getDeclaredMethodInfo().containsName("hiddenMethod"));
            assertTrue(info.getDeclaredFieldInfo().containsName("hidden"));
        }
    }

    /**
     * Verifies: CG-CVI-006, CG-SRC-016, CG-SRC-013.
     * Seam: config interaction between external-class retention and dependency projection.
     * Depends-On: SourceSelectionAtomicTest#enableAllInfoReturnsSameBuilder, SourceSelectionAtomicTest#enableInterClassDependenciesReturnsSameBuilder, SourceSelectionAtomicTest#enableExternalClassesReturnsSameBuilder.
     */
    @Test
    void externalClassCapabilityAgreesWithDependencyProjection() {
        try (ScanResult result = OracleSupport.fixtureGraph().enableAllInfo().enableInterClassDependencies()
                .enableExternalClasses().scan()) {
            ClassInfo direct = result.getClassInfo(FixtureTypes.DirectPlugin.class.getName());
            assertTrue(result.isExternalClassesEnabled());
            assertTrue(direct.getClassDependencies().containsName("java.util.Map"));
            assertTrue(result.getClassInfo("java.util.Map").isExternalClass());
        }
    }
}
