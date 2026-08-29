package integration;

import java.io.File;
import java.io.InputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;

import org.jboss.modules.IterableModuleFinder;
import org.jboss.modules.IterableResourceLoader;
import org.jboss.modules.IterableLocalLoader;
import org.jboss.modules.ClassSpec;
import org.jboss.modules.LocalDependencySpecBuilder;
import org.jboss.modules.LocalLoader;
import org.jboss.modules.PackageSpec;
import org.jboss.modules.LocalModuleFinder;
import org.jboss.modules.LocalModuleLoader;
import org.jboss.modules.Module;
import org.jboss.modules.ModuleDependencySpecBuilder;
import org.jboss.modules.ModuleFinder;
import org.jboss.modules.ModuleLoadException;
import org.jboss.modules.ModuleLoader;
import org.jboss.modules.ModuleNotFoundException;
import org.jboss.modules.ModuleSpec;
import org.jboss.modules.Resource;
import org.jboss.modules.ResourceLoader;
import org.jboss.modules.ResourceLoaderSpec;
import org.jboss.modules.ResourceLoaders;
import org.jboss.modules.Version;
import org.jboss.modules.filter.PathFilter;
import org.jboss.modules.filter.PathFilters;
import org.junit.jupiter.api.Test;
import support.services.ListProvider;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class GeneratedIntegrationTest {
    static {
        String handlers = System.getProperty("java.protocol.handler.pkgs");
        if (handlers == null || handlers.isBlank()) System.setProperty("java.protocol.handler.pkgs", "support.protocol");
        else if (!List.of(handlers.split("\\|")).contains("support.protocol"))
            System.setProperty("java.protocol.handler.pkgs", handlers + "|support.protocol");
    }

    /** Verifies: JMOD-LOAD-003, JMOD-LOAD-012, JMOD-CVI-001. Depends-On: builderRetainsName, createdSpecRetainsName. */
    @Test public void finderNameBecomesStableLoadedIdentity() throws Exception {
        ModuleLoader loader = loader(Map.of("graph.one", ModuleSpec.build("graph.one").create()));
        Module first = loader.loadModule("graph.one");
        assertEquals("graph.one", first.getName());
        assertSame(loader, first.getModuleLoader());
        assertSame(first, loader.loadModule("graph.one"));
    }

    /** Verifies: JMOD-LOAD-001, JMOD-LOAD-003, JMOD-CVI-001. Depends-On: builderRetainsName, moduleIterationPreservesIterableFinderOrder. */
    @Test public void firstFinderWinsAndCacheAvoidsLaterFinders() throws Exception {
        AtomicInteger firstCalls = new AtomicInteger();
        AtomicInteger secondCalls = new AtomicInteger();
        ModuleFinder firstFinder = (name, delegate) -> { firstCalls.incrementAndGet(); return ModuleSpec.build(name).addProperty("source", "first").create(); };
        ModuleFinder secondFinder = (name, delegate) -> { secondCalls.incrementAndGet(); return ModuleSpec.build(name).addProperty("source", "second").create(); };
        ModuleLoader loader = new ModuleLoader(new ModuleFinder[] { firstFinder, secondFinder });
        Module module = loader.loadModule("ordered");
        assertEquals("first", module.getProperty("source"));
        assertSame(module, loader.loadModule("ordered"));
        assertEquals(1, firstCalls.get());
        assertEquals(0, secondCalls.get());
    }

    /** Verifies: JMOD-SPEC-006, JMOD-SPEC-007, JMOD-LOAD-012, JMOD-LOAD-014, JMOD-CVI-002. Depends-On: builderProjectsConfiguredVersion, builderRetainsName. */
    @Test public void builderMetadataProjectsThroughLoadedModule() throws Exception {
        ModuleSpec spec = ModuleSpec.build("metadata")
            .addProperty("first", "one").addProperty("second", "two").addProperty("first", "last")
            .setVersion(Version.parse("2.5")).create();
        Module module = loader(Map.of("metadata", spec)).loadModule("metadata");
        assertEquals("last", module.getProperty("first"));
        assertEquals(List.of("first", "second"), new ArrayList<>(module.getPropertyNames()));
        assertEquals(Version.parse("2.5"), module.getVersion());
    }

    /** Verifies: JMOD-SPEC-007, JMOD-LOAD-003, JMOD-LOAD-013, JMOD-CVI-002. Depends-On: builderAllowsVersionToBeCleared, createdSpecRetainsName. */
    @Test public void clearedVersionAndMissingPropertyDoNotChangeIdentity() throws Exception {
        ModuleSpec spec = ModuleSpec.build("cleared.loaded").setVersion(Version.parse("9")).setVersion(null).create();
        ModuleLoader loader = loader(Map.of("cleared.loaded", spec));
        Module module = loader.loadModule("cleared.loaded");
        assertNull(module.getVersion());
        assertNull(module.getProperty("missing"));
        assertEquals("fallback", module.getProperty("missing", "fallback"));
        assertSame(module, loader.loadModule("cleared.loaded"));
    }

    /** Verifies: JMOD-RES-004, JMOD-RES-014, JMOD-CVI-003. Depends-On: parentOrChildPathFilterIncludesBoth, filteredResourcesPreserveAcceptedSourceOrder. */
    @Test public void acceptedRootPathAppearsInLocalAndImportedViews() throws Exception {
        Path repository = Files.createTempDirectory("root-accept");
        Path descriptor = writeDescriptor(repository, "root.accept", true, moduleXml("root.accept",
            "<resources><resource-root path=\"content\"><filter><include path=\"accepted\"/><exclude path=\"**\"/></filter></resource-root></resources>"));
        Files.createDirectories(descriptor.resolve("content/accepted"));
        Files.createDirectories(descriptor.resolve("content/rejected"));
        Files.writeString(descriptor.resolve("content/accepted/value.txt"), "yes");
        Files.writeString(descriptor.resolve("content/rejected/value.txt"), "no");
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { repository.toFile() })) {
            Module module = loader.loadModule("root.accept");
            assertTrue(module.getClassLoader().getLocalPaths().contains("accepted"));
            assertTrue(module.getImportedPaths().contains("accepted"));
            assertNotNull(module.getClassLoader().getResource("accepted/value.txt"));
        }
    }

    /** Verifies: JMOD-XML-014, JMOD-FILT-017, JMOD-FILT-018, JMOD-RES-004, JMOD-RES-014, JMOD-CVI-003. Depends-On: notFilterInvertsDelegate, filteredResourcesPreserveAcceptedSourceOrder, doubleStarGlobCrossesSlashAndMatchesDescendants. */
    @Test public void rejectedRootPathIsHiddenFromBothPathViews() throws Exception {
        Path repository = Files.createTempDirectory("root-reject");
        Path descriptor = writeDescriptor(repository, "root.reject", true, moduleXml("root.reject",
            "<resources><resource-root path=\"content\"><filter><exclude path=\"secret\"/><include path=\"**\"/></filter></resource-root></resources>"));
        Files.createDirectories(descriptor.resolve("content/visible"));
        Files.createDirectories(descriptor.resolve("content/secret"));
        Files.writeString(descriptor.resolve("content/visible/value.txt"), "yes");
        Files.writeString(descriptor.resolve("content/secret/value.txt"), "no");
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { repository.toFile() })) {
            Module module = loader.loadModule("root.reject");
            assertTrue(module.getImportedPaths().contains("visible"));
            assertFalse(module.getClassLoader().getLocalPaths().contains("secret"));
            assertFalse(module.getImportedPaths().contains("secret"));
            assertNull(module.getClassLoader().getResource("secret/value.txt"));
        }
    }

    /** Verifies: JMOD-FILT-004, JMOD-RES-001, JMOD-CVI-004. Depends-On: pathFilterSettersProjectIntoBuiltDependency, parentOrChildPathFilterIncludesBoth. */
    @Test public void dependencyPathFilterControlsResourceAndPathVisibility() throws Exception {
        ModuleSpec library = localContentSpec("library", Map.of("api/value.txt", "api", "impl/value.txt", "impl"));
        ModuleSpec application = ModuleSpec.build("application").addDependency(new ModuleDependencySpecBuilder()
            .setName("library").setImportFilter(PathFilters.isOrIsChildOf("api")).build()).create();
        Module module = loader(Map.of("library", library, "application", application)).loadModule("application");
        assertNotNull(module.getClassLoader().getResource("api/value.txt"));
        assertNull(module.getClassLoader().getResource("impl/value.txt"));
        assertTrue(module.getImportedPaths().contains("api"));
        assertFalse(module.getImportedPaths().contains("impl"));
    }

    /** Verifies: JMOD-FILT-004, JMOD-RES-001, JMOD-CVI-004. Depends-On: resourceAndClassFilterSettersProjectIntoBuiltDependency, exactPathFilterMatchesOnlyExactPath. */
    @Test public void resourceImportFilterNarrowsAnAcceptedDependencyPath() throws Exception {
        ModuleSpec library = localContentSpec("res.library", Map.of("api/allowed.txt", "yes", "api/blocked.txt", "no"));
        ModuleSpec application = ModuleSpec.build("res.application").addDependency(new ModuleDependencySpecBuilder()
            .setName("res.library").setImportFilter(PathFilters.isOrIsChildOf("api"))
            .setResourceImportFilter(PathFilters.is("api/allowed.txt")).build()).create();
        Module module = loader(Map.of("res.library", library, "res.application", application)).loadModule("res.application");
        assertNotNull(module.getClassLoader().getResource("api/allowed.txt"));
        assertNull(module.getClassLoader().getResource("api/blocked.txt"));
    }

    /** Verifies: JMOD-FILT-006, JMOD-RES-001, JMOD-CVI-005. Depends-On: exportToggleSelectsConstantFilters, parentOrChildPathFilterIncludesBoth. */
    @Test public void exportedDependencyContentFlowsToDownstreamModule() throws Exception {
        ModuleSpec library = localContentSpec("transitive.lib", Map.of("api/value.txt", "visible"));
        ModuleSpec middle = ModuleSpec.build("transitive.middle").addDependency(new ModuleDependencySpecBuilder()
            .setName("transitive.lib").setImportFilter(PathFilters.isOrIsChildOf("api")).setExport(true).build()).create();
        ModuleSpec downstream = ModuleSpec.build("transitive.downstream").addDependency(new ModuleDependencySpecBuilder()
            .setName("transitive.middle").build()).create();
        Module module = loader(Map.of("transitive.lib", library, "transitive.middle", middle, "transitive.downstream", downstream))
            .loadModule("transitive.downstream");
        assertEquals("visible", read(module.getClassLoader().getResource("api/value.txt")));
        assertTrue(module.getImportedPaths().contains("api"));
    }

    /** Verifies: JMOD-FILT-006, JMOD-RES-001, JMOD-CVI-005. Depends-On: exportToggleSelectsConstantFilters, constantPathFiltersReturnConstantDecisions. */
    @Test public void nonExportedDependencyContentStopsAtMiddleModule() throws Exception {
        ModuleSpec library = localContentSpec("private.lib", Map.of("api/value.txt", "hidden"));
        ModuleSpec middle = ModuleSpec.build("private.middle").addDependency(new ModuleDependencySpecBuilder()
            .setName("private.lib").setImportFilter(PathFilters.isOrIsChildOf("api")).setExport(false).build()).create();
        ModuleSpec downstream = ModuleSpec.build("private.downstream").addDependency(new ModuleDependencySpecBuilder()
            .setName("private.middle").build()).create();
        ModuleLoader loader = loader(Map.of("private.lib", library, "private.middle", middle, "private.downstream", downstream));
        assertNotNull(loader.loadModule("private.middle").getClassLoader().getResource("api/value.txt"));
        assertNull(loader.loadModule("private.downstream").getClassLoader().getResource("api/value.txt"));
    }

    /** Verifies: JMOD-RES-004, JMOD-RES-006, JMOD-CVI-006. Depends-On: filteredResourcesPreserveAcceptedSourceOrder, parentOrChildPathFilterIncludesBoth. */
    @Test public void localResourceOriginHasMatchingImportedPath() throws Exception {
        Module module = loader(Map.of("origin.local", localContentSpec("origin.local", Map.of("config/settings.txt", "local"))))
            .loadModule("origin.local");
        assertEquals("local", read(module.getClassLoader().getResource("config/settings.txt")));
        assertTrue(module.getImportedPaths().contains("config"));
    }

    /** Verifies: JMOD-RES-001, JMOD-RES-004, JMOD-CVI-006. Depends-On: pathFilterSettersProjectIntoBuiltDependency, filteredResourcesPreserveAcceptedSourceOrder. */
    @Test public void importedResourceOriginHasMatchingDependencyPath() throws Exception {
        ModuleSpec library = localContentSpec("origin.lib", Map.of("shared/data.txt", "dependency"));
        ModuleSpec application = ModuleSpec.build("origin.app").addDependency(new ModuleDependencySpecBuilder()
            .setName("origin.lib").setImportFilter(PathFilters.isOrIsChildOf("shared")).build()).create();
        Module module = loader(Map.of("origin.lib", library, "origin.app", application)).loadModule("origin.app");
        assertEquals("dependency", read(module.getClassLoader().getResource("shared/data.txt")));
        assertTrue(module.getImportedPaths().contains("shared"));
    }

    /** Verifies: JMOD-FILT-007, JMOD-RES-019, JMOD-RES-020, JMOD-CVI-007. Depends-On: serviceImportToggleControlsMetaInf, moduleDependencyProjectsNameAndOptionalFlag. */
    @Test public void serviceImportMakesProviderDiscoverableThroughDependency() throws Exception {
        ModuleSpec provider = serviceSpec("service.provider");
        ModuleSpec consumer = ModuleSpec.build("service.consumer").addDependency(new ModuleDependencySpecBuilder()
            .setName("service.provider").setImportServices(true).build()).create();
        Module module = loader(Map.of("service.provider", provider, "service.consumer", consumer)).loadModule("service.consumer");
        assertEquals(ListProvider.class, module.loadService(List.class).iterator().next().getClass());
        assertNotNull(module.getClassLoader().getResource("META-INF/services/" + List.class.getName()));
    }

    /** Verifies: JMOD-SPEC-009, JMOD-XML-019, JMOD-RES-019, JMOD-RES-020, JMOD-CVI-007. Depends-On: serviceImportToggleControlsMetaInf, filteredResourcesPreserveAcceptedSourceOrder. */
    @Test public void descriptorAndProgrammaticServiceResourcesAgreeWhileDirectSearchStaysLocal() throws Exception {
        Path repository = Files.createTempDirectory("descriptor-service");
        writeDescriptor(repository, "service.descriptor", true, moduleXml("service.descriptor",
            "<provides><service name=\"java.util.List\"><with-class name=\"support.services.ListProvider\"/></service></provides>"));

        ModuleSpec provider = serviceSpec("service.programmatic");
        ModuleSpec consumer = ModuleSpec.build("service.consumer.direct.boundary")
            .addDependency(new ModuleDependencySpecBuilder().setName("service.programmatic").setImportServices(true).build())
            .create();
        ModuleLoader graphLoader = loader(Map.of("service.programmatic", provider, "service.consumer.direct.boundary", consumer));
        Module providerModule = graphLoader.loadModule("service.programmatic");
        Module consumerModule = graphLoader.loadModule("service.consumer.direct.boundary");

        try (LocalModuleLoader descriptorLoader = new LocalModuleLoader(new File[] { repository.toFile() })) {
            Module descriptorModule = descriptorLoader.loadModule("service.descriptor");
            String serviceResource = "META-INF/services/" + List.class.getName();
            assertEquals(ListProvider.class.getName(), read(providerModule.getClassLoader().getResource(serviceResource)).trim());
            assertEquals(ListProvider.class.getName(), read(descriptorModule.getClassLoader().getResource(serviceResource)).trim());
            assertEquals(ListProvider.class, consumerModule.loadService(List.class).iterator().next().getClass());
            assertFalse(consumerModule.loadServiceDirectly(List.class).iterator().hasNext());
        }
    }

    /** Verifies: JMOD-SPEC-012, JMOD-SPEC-013, JMOD-CVI-008. Depends-On: createdSpecRetainsName, builderProjectsConfiguredVersion. */
    @Test public void programmaticAliasSharesTargetIdentityAndMetadata() throws Exception {
        ModuleSpec target = ModuleSpec.build("alias.target").addProperty("mode", "target").setVersion(Version.parse("3.1")).create();
        ModuleSpec alias = ModuleSpec.buildAlias("alias.name", "alias.target").create();
        ModuleLoader loader = loader(Map.of("alias.target", target, "alias.name", alias));
        Module targetModule = loader.loadModule("alias.target");
        Module aliasModule = loader.loadModule("alias.name");
        assertSame(targetModule, aliasModule);
        assertSame(targetModule.getClassLoader(), aliasModule.getClassLoader());
        assertEquals("target", aliasModule.getProperty("mode"));
        assertEquals(Version.parse("3.1"), aliasModule.getVersion());
    }

    /** Verifies: JMOD-XML-011, JMOD-SPEC-013, JMOD-CVI-008, JMOD-CVI-009. Depends-On: createdSpecRetainsName, builderRetainsName. */
    @Test public void descriptorAliasSharesTargetIdentityLikeProgrammaticAlias() throws Exception {
        Path root = Files.createTempDirectory("descriptor-alias");
        writeDescriptor(root, "xml.target", true, moduleXml("xml.target", ""));
        writeDescriptor(root, "xml.alias", true, "<module-alias xmlns=\"urn:jboss:module:1.9\" name=\"xml.alias\" target-name=\"xml.target\"/>");
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { root.toFile() })) {
            Module target = loader.loadModule("xml.target");
            Module alias = loader.loadModule("xml.alias");
            assertSame(target, alias);
            assertEquals("xml.target", alias.getName());
            assertSame(target.getClassLoader(), alias.getClassLoader());
        }
    }

    /** Verifies: JMOD-XML-010, JMOD-CVI-009. Depends-On: builderProjectsConfiguredVersion, createdSpecRetainsName. */
    @Test public void descriptorAndProgrammaticSpecsProjectEquivalentMetadataAndResource() throws Exception {
        Path repository = Files.createTempDirectory("descriptor-equivalent");
        writeDescriptor(repository, "equivalent.xml", true, moduleXml("equivalent.xml", " version=\"4.2\">"));
        Module programmatic = loader(Map.of("equivalent.programmatic",
            ModuleSpec.build("equivalent.programmatic")
                .setVersion(Version.parse("4.2")).create())).loadModule("equivalent.programmatic");
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { repository.toFile() })) {
            Module descriptor = loader.loadModule("equivalent.xml");
            assertEquals(programmatic.getVersion(), descriptor.getVersion());
            assertNull(programmatic.getClassLoader().getResource("absent.txt"));
            assertNull(descriptor.getClassLoader().getResource("absent.txt"));
            assertEquals("equivalent.xml", descriptor.getName());
        }
    }

    /** Verifies: JMOD-VER-001, JMOD-VER-004, JMOD-VER-010, JMOD-VER-013, JMOD-CVI-010. Depends-On: versionParsingAppliesUnicodeNormalization, versionOrderingCombinesPartAndSeparatorRules. */
    @Test public void loadedVersionAgreesWithNormalizationTokensAndComparison() throws Exception {
        Version version = Version.parse("１２.A");
        Module module = loader(Map.of("version.graph", ModuleSpec.build("version.graph").setVersion(version).create())).loadModule("version.graph");
        assertEquals("12.A", module.getVersion().toString());
        Version.Iterator iterator = module.getVersion().iterator();
        iterator.next();
        assertTrue(iterator.isNumberPart());
        assertEquals(2, iterator.length());
        assertEquals(0, module.getVersion().compareTo(Version.parse("12.A")));
        assertEquals(module.getVersion(), Version.parse("12.A"));
    }

    /** Verifies: JMOD-VER-005, JMOD-VER-007, JMOD-VER-013, JMOD-CVI-010. Depends-On: equalNumericValuesUseDigitRunLengthAsTieBreaker, equalityAndHashingAgreeWithComparison. */
    @Test public void aliasVersionIdentityPreservesComparisonAndHashRules() throws Exception {
        Version version = Version.parse("1.01");
        ModuleSpec target = ModuleSpec.build("version.target").setVersion(version).create();
        ModuleSpec alias = ModuleSpec.buildAlias("version.alias", "version.target").create();
        ModuleLoader loader = loader(Map.of("version.target", target, "version.alias", alias));
        Module targetModule = loader.loadModule("version.target");
        Module aliasModule = loader.loadModule("version.alias");
        assertSame(targetModule, aliasModule);
        assertTrue(aliasModule.getVersion().compareTo(Version.parse("1.1")) > 0);
        assertEquals(version, aliasModule.getVersion());
    }

    /** Verifies: JMOD-XML-024, JMOD-XML-025, JMOD-CVI-011. Depends-On: moduleIterationPreservesIterableFinderOrder, createdSpecRetainsName. */
    @Test public void flatDescriptorMayIterateButCannotResolveDirectly() throws Exception {
        Path root = Files.createTempDirectory("flat-iteration");
        writeDescriptor(root, "flat.visible", false, moduleXml("flat.visible", ""));
        try (LocalModuleFinder finder = new LocalModuleFinder(new File[] { root.toFile() })) {
            List<String> names = strings(finder.iterateModules(null, true, emptyLoader()));
            assertTrue(names.contains("flat.visible"));
            assertNull(finder.findModule("flat.visible", emptyLoader()));
        }
    }

    /** Verifies: JMOD-LOAD-005, JMOD-XML-024, JMOD-XML-025, JMOD-CVI-011. Depends-On: moduleIterationPreservesIterableFinderOrder, createdSpecRetainsName. */
    @Test public void flatIteratedNameStillFailsLocalLoaderLoad() throws Exception {
        Path root = Files.createTempDirectory("flat-load");
        writeDescriptor(root, "flat.unloadable", false, moduleXml("flat.unloadable", ""));
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { root.toFile() })) {
            List<String> names = strings(loader.iterateModules(null, true));
            assertTrue(names.contains("flat.unloadable"));
            assertThrows(ModuleNotFoundException.class, () -> loader.loadModule("flat.unloadable"));
        }
    }

    /** Verifies: JMOD-XML-002, JMOD-XML-003, JMOD-LOAD-012. Depends-On: createdSpecRetainsName, builderRetainsName. */
    @Test public void defaultMainDescriptorSupportsLookupAndLoad() throws Exception {
        Path root = Files.createTempDirectory("main-layout");
        writeDescriptor(root, "default.main", true, moduleXml("default.main", ""));
        try (LocalModuleFinder finder = new LocalModuleFinder(new File[] { root.toFile() })) {
            assertEquals("default.main", finder.findModule("default.main", emptyLoader()).getName());
        }
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { root.toFile() })) {
            assertEquals("default.main", loader.loadModule("default.main").getName());
        }
    }

    /** Verifies: JMOD-XML-001, JMOD-XML-003, JMOD-RES-006. Depends-On: filteredResourcesPreserveAcceptedSourceOrder, createdSpecRetainsName. */
    @Test public void repositoryRootsUseFirstMatchingDescriptor() throws Exception {
        Path first = Files.createTempDirectory("repo-first");
        Path second = Files.createTempDirectory("repo-second");
        Path firstDir = writeDescriptor(first, "ordered.repo", true, moduleXml("ordered.repo", "<resources><resource-root path=\"content\"/></resources>"));
        Path secondDir = writeDescriptor(second, "ordered.repo", true, moduleXml("ordered.repo", "<resources><resource-root path=\"content\"/></resources>"));
        Files.createDirectories(firstDir.resolve("content"));
        Files.createDirectories(secondDir.resolve("content"));
        Files.writeString(firstDir.resolve("content/value.txt"), "first");
        Files.writeString(secondDir.resolve("content/value.txt"), "second");
        try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { first.toFile(), second.toFile() })) {
            assertEquals("first", read(loader.loadModule("ordered.repo").getClassLoader().getResource("value.txt")));
        }
    }

    /** Verifies: JMOD-XML-005, JMOD-XML-006. Depends-On: moduleIterationPreservesIterableFinderOrder, createdSpecRetainsName. */
    @Test public void repositoryIterationHonorsImmediateAndRecursiveBoundaries() throws Exception {
        Path root = Files.createTempDirectory("iteration-boundary");
        writeDescriptor(root, "base.child", false, moduleXml("base.child", ""));
        writeDescriptor(root, "base.child.grand", false, moduleXml("base.child.grand", ""));
        try (LocalModuleFinder finder = new LocalModuleFinder(new File[] { root.toFile() })) {
            List<String> immediate = strings(finder.iterateModules(null, false, emptyLoader()));
            List<String> recursive = strings(finder.iterateModules(null, true, emptyLoader()));
            assertTrue(immediate.isEmpty());
            assertTrue(recursive.containsAll(List.of("base.child", "base.child.grand")));
        }
    }

    /** Verifies: JMOD-FILT-008, JMOD-FILT-009, JMOD-LOAD-007. Depends-On: moduleDependencyProjectsNameAndOptionalFlag, moduleDependencyRequiresName. */
    @Test public void optionalMissingDependencyLinksWhileRequiredOneFails() throws Exception {
        ModuleSpec optional = ModuleSpec.build("optional.owner").addDependency(new ModuleDependencySpecBuilder()
            .setName("missing.optional").setOptional(true).build()).create();
        ModuleSpec required = ModuleSpec.build("required.owner").addDependency(new ModuleDependencySpecBuilder()
            .setName("missing.required").build()).create();
        ModuleLoader loader = loader(Map.of("optional.owner", optional, "required.owner", required));
        assertEquals("optional.owner", loader.loadModule("optional.owner").getName());
        assertThrows(ModuleNotFoundException.class, () -> loader.loadModule("required.owner"));
    }

    /** Verifies: JMOD-LOAD-006, JMOD-LOAD-008. Depends-On: createdSpecRetainsName, builderRetainsName. */
    @Test public void failedMismatchedLoadCanRetryWithCorrectSpec() throws Exception {
        AtomicInteger attempts = new AtomicInteger();
        ModuleFinder finder = (name, delegate) -> attempts.getAndIncrement() == 0
            ? ModuleSpec.build("wrong.name").create() : ModuleSpec.build(name).create();
        ModuleLoader loader = new ModuleLoader(finder);
        assertThrows(ModuleLoadException.class, () -> loader.loadModule("retry.name"));
        assertEquals("retry.name", loader.loadModule("retry.name").getName());
        assertEquals(2, attempts.get());
    }

    /** Verifies: JMOD-LOAD-004. Depends-On: createdSpecRetainsName, builderRetainsName. */
    @Test public void concurrentLoadsConvergeOnOneModuleObject() throws Exception {
        ModuleLoader loader = loader(Map.of("concurrent", ModuleSpec.build("concurrent").create()));
        ExecutorService executor = Executors.newFixedThreadPool(6);
        try {
            List<Future<Module>> futures = new ArrayList<>();
            for (int i = 0; i < 12; i++) futures.add(executor.submit(() -> loader.loadModule("concurrent")));
            Module first = futures.get(0).get();
            for (Future<Module> future : futures) assertSame(first, future.get());
        } finally {
            executor.shutdownNow();
        }
    }

    /** Verifies: JMOD-LOAD-015, JMOD-LOAD-016, JMOD-LOAD-017. Depends-On: createdSpecRetainsName, builderRetainsName. */
    @Test public void moduleClassLoaderAssociationProjectsModuleAndLoader() throws Exception {
        ModuleLoader loader = loader(Map.of("associated", ModuleSpec.build("associated").create()));
        Module module = loader.loadModule("associated");
        assertSame(module, Module.forClassLoader(module.getClassLoader(), false));
        assertSame(loader, ModuleLoader.forClassLoader(module.getClassLoader()));
        assertNull(Module.forClass(String.class));
        assertNull(ModuleLoader.forClass(String.class));
    }

    /** Verifies: JMOD-RES-009, JMOD-RES-010. Depends-On: filteredResourcesPreserveAcceptedSourceOrder, parentOrChildPathFilterIncludesBoth. */
    @Test public void iterablePathLoaderConstrainsStartAndRecursion() throws Exception {
        Path root = resourceTree(Map.of("a/top.txt", "top", "a/nested/deep.txt", "deep", "other.txt", "other"));
        IterableResourceLoader loader = (IterableResourceLoader) ResourceLoaders.createPathResourceLoader(root);
        List<String> immediate = resourceNames(loader.iterateResources("a", false));
        List<String> recursive = resourceNames(loader.iterateResources("a", true));
        assertEquals(List.of("a/top.txt"), immediate);
        assertTrue(recursive.containsAll(List.of("a/top.txt", "a/nested/deep.txt")));
        assertFalse(recursive.contains("other.txt"));
        assertFalse(loader.iterateResources("missing", true).hasNext());
    }

    /** Verifies: JMOD-RES-005, JMOD-RES-011, JMOD-RES-012. Depends-On: filteredResourcesPreserveAcceptedSourceOrder, exactPathFilterMatchesOnlyExactPath. */
    @Test public void jarAndRelativeJarRootsExposeObservableResources() throws Exception {
        Path jarPath = Files.createTempFile("resources", ".jar");
        try (JarOutputStream output = new JarOutputStream(Files.newOutputStream(jarPath))) {
            output.putNextEntry(new JarEntry("root/value.txt")); output.write("jar-value".getBytes(StandardCharsets.UTF_8)); output.closeEntry();
            output.putNextEntry(new JarEntry("outside.txt")); output.write("outside".getBytes(StandardCharsets.UTF_8)); output.closeEntry();
        }
        try (JarFile jar = new JarFile(jarPath.toFile())) {
            ResourceLoader full = ResourceLoaders.createJarResourceLoader(jar);
            ResourceLoader relative = ResourceLoaders.createJarResourceLoader(jar, "root");
            Resource fullResource = full.getResource("root/value.txt");
            Resource relativeResource = relative.getResource("value.txt");
            assertEquals("jar", fullResource.getURL().getProtocol());
            assertEquals("jar-value", read(fullResource.getURL()));
            assertEquals("jar-value", read(relativeResource.getURL()));
            assertNull(relative.getResource("outside.txt"));
        }
    }

    private static ModuleLoader loader(Map<String, ModuleSpec> specs) {
        return new ModuleLoader((name, delegate) -> specs.get(name));
    }

    private static ModuleLoader emptyLoader() {
        return loader(Map.of());
    }

    private static ModuleSpec localContentSpec(String name, Map<String, String> content) throws Exception {
        MemoryLocalLoader localLoader = new MemoryLocalLoader(content);
        Set<String> paths = new java.util.LinkedHashSet<>();
        paths.add("");
        for (String resourceName : content.keySet()) {
            String path = containingPath(resourceName);
            while (!path.isEmpty()) {
                paths.add(path);
                path = containingPath(path);
            }
        }
        return ModuleSpec.build(name).addDependency(new LocalDependencySpecBuilder()
            .setLocalLoader(localLoader).setLoaderPaths(paths)
            .setImportFilter(PathFilters.acceptAll()).setExportFilter(PathFilters.acceptAll())
            .setResourceImportFilter(PathFilters.acceptAll()).setResourceExportFilter(PathFilters.acceptAll()).build()).create();
    }

    private static ModuleSpec serviceSpec(String name) {
        LocalDependencySpecBuilder serviceRoot = new LocalDependencySpecBuilder()
            .setImportFilter(PathFilters.acceptAll()).setExportFilter(PathFilters.acceptAll());
        LocalDependencySpecBuilder serviceClass = new LocalDependencySpecBuilder()
            .setLocalLoader(new ServiceClassLocalLoader()).setLoaderPaths(Set.of("support/services"))
            .setImportFilter(PathFilters.acceptAll()).setExportFilter(PathFilters.acceptAll())
            .setClassImportFilter(org.jboss.modules.filter.ClassFilters.acceptAll())
            .setClassExportFilter(org.jboss.modules.filter.ClassFilters.acceptAll());
        return ModuleSpec.build(name).addProvide(List.class.getName(), ListProvider.class.getName())
            .addDependency(serviceRoot.build()).addDependency(serviceClass.build()).create();
    }

    private static Path resourceTree(Map<String, String> entries) throws Exception {
        Path root = Files.createTempDirectory("module-resources");
        for (Map.Entry<String, String> entry : entries.entrySet()) {
            Path file = root.resolve(entry.getKey());
            Files.createDirectories(file.getParent());
            Files.writeString(file, entry.getValue());
        }
        return root;
    }

    private static String read(URL url) throws Exception {
        assertNotNull(url);
        try (InputStream input = url.openStream()) {
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static Path writeDescriptor(Path root, String name, boolean main, String xml) throws Exception {
        Path directory = root.resolve(name.replace('.', File.separatorChar));
        if (main) directory = directory.resolve("main");
        Files.createDirectories(directory);
        Files.writeString(directory.resolve("module.xml"), xml, StandardCharsets.UTF_8);
        return directory;
    }

    private static String moduleXml(String name, String bodyOrAttributes) {
        if (bodyOrAttributes.startsWith(" version=")) {
            int close = bodyOrAttributes.indexOf('>');
            return "<module xmlns=\"urn:jboss:module:1.9\" name=\"" + name + "\"" + bodyOrAttributes.substring(0, close + 1)
                + bodyOrAttributes.substring(close + 1) + "</module>";
        }
        return "<module xmlns=\"urn:jboss:module:1.9\" name=\"" + name + "\">" + bodyOrAttributes + "</module>";
    }

    private static List<String> strings(Iterator<String> iterator) {
        List<String> result = new ArrayList<>();
        iterator.forEachRemaining(result::add);
        return result;
    }

    private static List<String> resourceNames(Iterator<Resource> iterator) {
        List<String> result = new ArrayList<>();
        iterator.forEachRemaining(resource -> result.add(resource.getName()));
        return result;
    }

    private static String containingPath(String name) {
        int slash = name.lastIndexOf('/');
        return slash < 0 ? "" : name.substring(0, slash);
    }

    private static final class MemoryLocalLoader implements IterableLocalLoader {
        private final Map<String, Resource> resources = new LinkedHashMap<>();

        MemoryLocalLoader(Map<String, String> content) throws Exception {
            for (Map.Entry<String, String> entry : content.entrySet()) {
                Path file = Files.createTempFile("memory-local", ".resource");
                Files.writeString(file, entry.getValue());
                resources.put(entry.getKey(), new FileResource(entry.getKey(), file));
            }
        }

        @Override public Class<?> loadClassLocal(String name, boolean resolve) { return null; }
        @Override public Package loadPackageLocal(String name) { return null; }
        @Override public List<Resource> loadResourceLocal(String name) {
            Resource resource = resources.get(name);
            return resource == null ? List.of() : List.of(resource);
        }
        @Override public Iterator<Resource> iterateResources(String startPath, boolean recursive) {
            String prefix = startPath.isEmpty() ? "" : startPath + "/";
            return resources.values().stream().filter(resource -> {
                String resourceName = resource.getName();
                if (!resourceName.startsWith(prefix)) return false;
                String remainder = resourceName.substring(prefix.length());
                return recursive || !remainder.contains("/");
            }).iterator();
        }
    }

    private static final class ServiceClassLocalLoader implements LocalLoader {
        @Override public Class<?> loadClassLocal(String name, boolean resolve) {
            return ListProvider.class.getName().equals(name) ? ListProvider.class : null;
        }
        @Override public Package loadPackageLocal(String name) { return null; }
        @Override public List<Resource> loadResourceLocal(String name) { return List.of(); }
    }

    private record FileResource(String name, Path path) implements Resource {
        @Override public String getName() { return name; }
        @Override public URL getURL() {
            try { return path.toUri().toURL(); }
            catch (Exception e) { throw new IllegalStateException(e); }
        }
        @Override public InputStream openStream() throws java.io.IOException { return Files.newInputStream(path); }
        @Override public long getSize() { try { return Files.size(path); } catch (Exception ignored) { return 0; } }
    }
}
