package atomic;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

import org.jboss.modules.DependencySpec;
import org.jboss.modules.LocalDependencySpecBuilder;
import org.jboss.modules.ModuleDependencySpec;
import org.jboss.modules.ModuleDependencySpecBuilder;
import org.jboss.modules.ModuleSpec;
import org.jboss.modules.Resource;
import org.jboss.modules.ResourceLoader;
import org.jboss.modules.ResourceLoaders;
import org.jboss.modules.Version;
import org.jboss.modules.filter.ClassFilter;
import org.jboss.modules.filter.ClassFilters;
import org.jboss.modules.filter.PathFilter;
import org.jboss.modules.filter.PathFilters;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class GeneratedAtomicTest {
    /** Verifies: JMOD-SPEC-001. */
    @Test public void builderRetainsName() { assertEquals("atomic.name", ModuleSpec.build("atomic.name").getName()); }

    /** Verifies: JMOD-SPEC-003. */
    @Test public void createdSpecRetainsName() { assertEquals("atomic.created", ModuleSpec.build("atomic.created").create().getName()); }

    /** Verifies: JMOD-SPEC-002. */
    @Test public void normalBuilderRejectsNullName() { assertThrows(IllegalArgumentException.class, () -> ModuleSpec.build(null)); }

    /** Verifies: JMOD-SPEC-002. */
    @Test public void aliasBuilderRejectsNullAliasName() { assertThrows(IllegalArgumentException.class, () -> ModuleSpec.buildAlias(null, "target")); }

    /** Verifies: JMOD-SPEC-007. */
    @Test public void builderProjectsConfiguredVersion() {
        Version version = Version.parse("2.7");
        assertEquals(version, ModuleSpec.build("versioned").setVersion(version).getVersion());
    }

    /** Verifies: JMOD-SPEC-007. */
    @Test public void builderAllowsVersionToBeCleared() {
        ModuleSpec.Builder builder = ModuleSpec.build("cleared").setVersion(Version.parse("1.0"));
        assertNull(builder.setVersion(null).getVersion());
    }

    /** Verifies: JMOD-FILT-003. */
    @Test public void moduleDependencyRequiresName() {
        assertThrows(IllegalArgumentException.class, () -> new ModuleDependencySpecBuilder().build());
    }

    /** Verifies: JMOD-FILT-003, JMOD-FILT-008. */
    @Test public void moduleDependencyProjectsNameAndOptionalFlag() {
        ModuleDependencySpec dependency = new ModuleDependencySpecBuilder().setName("dep").setOptional(true).build();
        assertEquals("dep", dependency.getName());
        assertTrue(dependency.isOptional());
    }

    /** Verifies: JMOD-FILT-006. */
    @Test public void exportToggleSelectsConstantFilters() {
        ModuleDependencySpecBuilder builder = new ModuleDependencySpecBuilder().setName("dep");
        assertTrue(builder.setExport(true).getExportFilter().accept("anything"));
        assertFalse(builder.setExport(false).getExportFilter().accept("anything"));
    }

    /** Verifies: JMOD-FILT-007. */
    @Test public void serviceImportToggleControlsMetaInf() {
        ModuleDependencySpecBuilder builder = new ModuleDependencySpecBuilder().setName("dep");
        assertTrue(builder.setImportServices(true).getImportFilter().accept("META-INF/services/example.Service"));
        assertFalse(builder.getImportFilter().accept("META-INF/other"));
        assertFalse(builder.setImportServices(false).getImportFilter().accept("META-INF/services/example.Service"));
    }

    /** Verifies: JMOD-FILT-004. */
    @Test public void pathFilterSettersProjectIntoBuiltDependency() {
        PathFilter imports = PathFilters.isOrIsChildOf("api");
        PathFilter exports = PathFilters.is("api/public");
        DependencySpec dependency = new ModuleDependencySpecBuilder().setName("dep")
            .setImportFilter(imports).setExportFilter(exports).build();
        assertTrue(dependency.getImportFilter().accept("api/private"));
        assertFalse(dependency.getImportFilter().accept("other"));
        assertTrue(dependency.getExportFilter().accept("api/public"));
        assertFalse(dependency.getExportFilter().accept("api/private"));
    }

    /** Verifies: JMOD-FILT-004. */
    @Test public void resourceAndClassFilterSettersProjectIntoBuiltDependency() {
        PathFilter resourceImports = PathFilters.isOrIsChildOf("data");
        PathFilter resourceExports = PathFilters.is("data/public.txt");
        ClassFilter classImports = ClassFilters.fromResourcePathFilter(PathFilters.is("p/C.class"));
        ClassFilter classExports = ClassFilters.rejectAll();
        DependencySpec dependency = new ModuleDependencySpecBuilder().setName("dep")
            .setResourceImportFilter(resourceImports).setResourceExportFilter(resourceExports)
            .setClassImportFilter(classImports).setClassExportFilter(classExports).build();
        assertTrue(dependency.getResourceImportFilter().accept("data/item.txt"));
        assertTrue(dependency.getResourceExportFilter().accept("data/public.txt"));
        assertTrue(dependency.getClassImportFilter().accept("p.C"));
        assertFalse(dependency.getClassExportFilter().accept("p.C"));
    }

    /** Verifies: JMOD-FILT-005. */
    @Test public void pathFilterSettersRejectNull() {
        ModuleDependencySpecBuilder builder = new ModuleDependencySpecBuilder();
        assertThrows(IllegalArgumentException.class, () -> builder.setImportFilter(null));
        assertThrows(IllegalArgumentException.class, () -> builder.setExportFilter(null));
    }

    /** Verifies: JMOD-FILT-005. */
    @Test public void resourceAndClassFilterSettersRejectNull() {
        ModuleDependencySpecBuilder builder = new ModuleDependencySpecBuilder();
        assertThrows(IllegalArgumentException.class, () -> builder.setResourceImportFilter(null));
        assertThrows(IllegalArgumentException.class, () -> builder.setResourceExportFilter(null));
        assertThrows(IllegalArgumentException.class, () -> builder.setClassImportFilter(null));
        assertThrows(IllegalArgumentException.class, () -> builder.setClassExportFilter(null));
    }

    /** Verifies: JMOD-FILT-001, JMOD-FILT-002. */
    @Test public void dependencyBuilderDefaultsDifferForLocalPaths() {
        ModuleDependencySpecBuilder module = new ModuleDependencySpecBuilder();
        LocalDependencySpecBuilder local = new LocalDependencySpecBuilder();
        assertFalse(module.getImportFilter().accept("META-INF"));
        assertTrue(local.getImportFilter().accept("META-INF"));
        assertFalse(module.getExportFilter().accept("ordinary"));
        assertTrue(module.getResourceImportFilter().accept("ordinary"));
        assertTrue(module.getClassImportFilter().accept("example.Type"));
    }

    /** Verifies: JMOD-FILT-011. */
    @Test public void localDependencyRejectsNullLoader() {
        assertThrows(IllegalArgumentException.class, () -> new LocalDependencySpecBuilder().setLocalLoader(null));
    }

    /** Verifies: JMOD-FILT-012. */
    @Test public void localDependencyRejectsNullLoaderPaths() {
        assertThrows(IllegalArgumentException.class, () -> new LocalDependencySpecBuilder().setLoaderPaths(null));
    }

    /** Verifies: JMOD-FILT-014. */
    @Test public void constantPathFiltersReturnConstantDecisions() {
        for (String path : List.of("", "a", "a/b")) {
            assertTrue(PathFilters.acceptAll().accept(path));
            assertFalse(PathFilters.rejectAll().accept(path));
        }
    }

    /** Verifies: JMOD-FILT-015. */
    @Test public void allFilterRequiresEveryDelegate() {
        PathFilter filter = PathFilters.all(PathFilters.isOrIsChildOf("a"), PathFilters.not(PathFilters.is("a/private")));
        assertTrue(filter.accept("a/public"));
        assertFalse(filter.accept("a/private"));
        assertFalse(filter.accept("b"));
    }

    /** Verifies: JMOD-FILT-015. */
    @Test public void anyFilterRequiresOneDelegate() {
        PathFilter filter = PathFilters.any(PathFilters.is("a"), PathFilters.is("b"));
        assertTrue(filter.accept("a"));
        assertTrue(filter.accept("b"));
        assertFalse(filter.accept("c"));
    }

    /** Verifies: JMOD-FILT-015. */
    @Test public void noneFilterRejectsEveryDelegateMatch() {
        PathFilter filter = PathFilters.none(PathFilters.is("a"), PathFilters.is("b"));
        assertTrue(filter.accept("c"));
        assertFalse(filter.accept("a"));
        assertFalse(filter.accept("b"));
    }

    /** Verifies: JMOD-FILT-015. */
    @Test public void notFilterInvertsDelegate() {
        PathFilter filter = PathFilters.not(PathFilters.is("blocked"));
        assertFalse(filter.accept("blocked"));
        assertTrue(filter.accept("open"));
    }

    /** Verifies: JMOD-FILT-016. */
    @Test public void exactPathFilterMatchesOnlyExactPath() {
        PathFilter filter = PathFilters.is("a/b");
        assertTrue(filter.accept("a/b"));
        assertFalse(filter.accept("a/b/c"));
        assertFalse(filter.accept("a"));
    }

    /** Verifies: JMOD-FILT-016. */
    @Test public void childPathFilterExcludesParent() {
        PathFilter filter = PathFilters.isChildOf("a");
        assertFalse(filter.accept("a"));
        assertTrue(filter.accept("a/b"));
        assertTrue(filter.accept("a/b/c"));
    }

    /** Verifies: JMOD-FILT-016. */
    @Test public void parentOrChildPathFilterIncludesBoth() {
        PathFilter filter = PathFilters.isOrIsChildOf("a");
        assertTrue(filter.accept("a"));
        assertTrue(filter.accept("a/b"));
        assertFalse(filter.accept("ab"));
    }

    /** Verifies: JMOD-FILT-016. */
    @Test public void membershipPathFilterUsesSetMembership() {
        PathFilter filter = PathFilters.in(Set.of("a", "b/c"));
        assertTrue(filter.accept("a"));
        assertTrue(filter.accept("b/c"));
        assertFalse(filter.accept("b"));
    }

    /** Verifies: JMOD-FILT-017. */
    @Test public void questionGlobConsumesOneNonSlashCharacter() {
        PathFilter filter = PathFilters.match("a/?/c");
        assertTrue(filter.accept("a/b/c"));
        assertFalse(filter.accept("a/bb/c"));
        assertFalse(filter.accept("a//c"));
    }

    /** Verifies: JMOD-FILT-017. */
    @Test public void starGlobDoesNotCrossSlash() {
        PathFilter filter = PathFilters.match("a/*/c");
        assertTrue(filter.accept("a/b/c"));
        assertFalse(filter.accept("a/b/d/c"));
    }

    /** Verifies: JMOD-FILT-017, JMOD-FILT-018. */
    @Test public void doubleStarGlobCrossesSlashAndMatchesDescendants() {
        PathFilter filter = PathFilters.match("a/**");
        assertTrue(filter.accept("a/b"));
        assertTrue(filter.accept("a/b/c"));
        assertFalse(filter.accept("a"));
    }

    /** Verifies: JMOD-FILT-021. */
    @Test public void constantClassFiltersReturnConstantDecisions() {
        assertTrue(ClassFilters.acceptAll().accept("example.Type"));
        assertFalse(ClassFilters.rejectAll().accept("example.Type"));
    }

    /** Verifies: JMOD-FILT-022. */
    @Test public void classFilterAdaptsBinaryNameToResourcePath() {
        ClassFilter filter = ClassFilters.fromResourcePathFilter(PathFilters.is("example/Type.class"));
        assertTrue(filter.accept("example.Type"));
        assertFalse(filter.accept("example.Other"));
    }

    /** Verifies: JMOD-FILT-023, JMOD-RES-005, JMOD-RES-006. */
    @Test public void filteredResourcesPreserveAcceptedSourceOrder() throws Exception {
        Path root = Files.createTempDirectory("atomic-resources");
        Files.writeString(root.resolve("a.txt"), "a");
        Files.writeString(root.resolve("b.txt"), "bb");
        ResourceLoader loader = ResourceLoaders.createPathResourceLoader(root);
        List<Resource> resources = List.of(loader.getResource("b.txt"), loader.getResource("a.txt"));
        Iterator<Resource> filtered = PathFilters.filtered(PathFilters.is("b.txt"), resources.iterator());
        Resource resource = filtered.next();
        assertEquals("b.txt", resource.getName());
        assertFalse(filtered.hasNext());
        assertNull(loader.getResource("missing.txt"));
    }

    /** Verifies: JMOD-VER-001, JMOD-VER-003. */
    @Test public void versionParsingAppliesUnicodeNormalization() {
        assertEquals("12.A", Version.parse("\uFF11\uFF12.\uFF21").toString());
    }

    /** Verifies: JMOD-VER-004, JMOD-VER-005, JMOD-VER-006. */
    @Test public void versionOrderingCombinesPartAndSeparatorRules() {
        List<Version> versions = new ArrayList<>(List.of(
            Version.parse("1_a"), Version.parse("1+a"), Version.parse("1-a"), Version.parse("1.a"), Version.parse("1a")));
        versions.sort(Version::compareTo);
        assertEquals(List.of("1a", "1.a", "1-a", "1+a", "1_a"), versions.stream().map(Version::toString).toList());
    }

    /** Verifies: JMOD-VER-005. */
    @Test public void equalNumericValuesUseDigitRunLengthAsTieBreaker() {
        assertTrue(Version.parse("1.1").compareTo(Version.parse("1.01")) < 0);
    }
}
