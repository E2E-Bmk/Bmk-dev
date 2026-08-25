package atomic;

import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.jar.Attributes;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.pf4j.ClassLoadingStrategy;
import org.pf4j.DefaultExtensionFactory;
import org.pf4j.DefaultPluginDescriptor;
import org.pf4j.DefaultPluginManager;
import org.pf4j.DefaultPluginStatusProvider;
import org.pf4j.DefaultVersionManager;
import org.pf4j.DependencyResolver;
import org.pf4j.ExtensionDescriptor;
import org.pf4j.ExtensionFactory;
import org.pf4j.ExtensionWrapper;
import org.pf4j.ManifestPluginDescriptorFinder;
import org.pf4j.PluginClassLoader;
import org.pf4j.PluginDependency;
import org.pf4j.PluginDescriptor;
import org.pf4j.PluginRuntimeException;
import org.pf4j.PluginState;
import org.pf4j.PluginStateEvent;
import org.pf4j.PluginWrapper;
import org.pf4j.PropertiesPluginDescriptorFinder;
import org.pf4j.RuntimeMode;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Atomic public-contract tests for PF4J. */
class Pf4jAtomicTest {
    @TempDir Path temp;

    /** Verifies: PF4J-ART-001, PF4J-ART-004. */ @Test
    void managerKeepsOrderedRoots() {
        Path first = temp.resolve("root-one");
        Path second = temp.resolve("root-two");
        assertEquals(List.of(first, second), new DefaultPluginManager(first, second).getPluginsRoots());
    }

    /** Verifies: PF4J-ART-004. */ @Test
    void managerReturnsFirstRoot() {
        Path first = temp.resolve("root-a");
        assertEquals(first, new DefaultPluginManager(first, temp.resolve("root-b")).getPluginsRoot());
    }

    /** Verifies: PF4J-ART-004. */ @Test
    void managerRootViewIsUnmodifiable() {
        List<Path> roots = new DefaultPluginManager(temp).getPluginsRoots();
        assertThrows(UnsupportedOperationException.class, () -> roots.add(temp.resolve("other")));
    }

    /** Verifies: PF4J-DEP-015. */ @Test
    void managerDefaultsSystemVersion() {
        assertEquals("0.0.0", new DefaultPluginManager(temp).getSystemVersion());
    }

    /** Verifies: PF4J-ART-012, PF4J-ART-014. */ @Test
    void propertiesFinderReadsAllFields() throws IOException {
        Files.writeString(temp.resolve("plugin.properties"),
            "plugin.id=atomic-properties\nplugin.description=desc\nplugin.class=org.pf4j.Plugin\n"
            + "plugin.version=2.4.1\nplugin.requires=>=1.0.0\nplugin.dependencies=base@2.0.0\n"
            + "plugin.provider=provider-x\nplugin.license=MIT\n", StandardCharsets.UTF_8);
        PluginDescriptor descriptor = new PropertiesPluginDescriptorFinder().find(temp);
        assertEquals("atomic-properties", descriptor.getPluginId());
        assertEquals("desc", descriptor.getPluginDescription());
        assertEquals("2.4.1", descriptor.getVersion());
        assertEquals("provider-x", descriptor.getProvider());
        assertEquals("MIT", descriptor.getLicense());
        assertEquals("base", descriptor.getDependencies().get(0).getPluginId());
    }

    /** Verifies: PF4J-ART-013. */ @Test
    void propertiesFinderUsesCustomFile() throws IOException {
        Files.writeString(temp.resolve("custom.metadata"),
            "plugin.id=custom-file\nplugin.version=1.0.0\n", StandardCharsets.UTF_8);
        assertEquals("custom-file", new PropertiesPluginDescriptorFinder("custom.metadata").find(temp).getPluginId());
    }

    /** Verifies: PF4J-ART-015. */ @Test
    void propertiesFinderDefaultsOptionalFields() throws IOException {
        Files.writeString(temp.resolve("plugin.properties"),
            "plugin.id=defaults-case\nplugin.version=1.0.0\n", StandardCharsets.UTF_8);
        PluginDescriptor descriptor = new PropertiesPluginDescriptorFinder().find(temp);
        assertEquals("", descriptor.getPluginDescription());
        assertEquals("org.pf4j.Plugin", descriptor.getPluginClass());
        assertEquals("*", descriptor.getRequires());
        assertTrue(descriptor.getDependencies().isEmpty());
    }

    /** Verifies: PF4J-ART-010, PF4J-ERR-005. */ @Test
    void propertiesFinderMissingFileRaisesRuntime() {
        assertThrows(PluginRuntimeException.class, () -> new PropertiesPluginDescriptorFinder().find(temp));
    }

    /** Verifies: PF4J-ART-011, PF4J-ART-014. */ @Test
    void manifestFinderReadsAllFields() throws IOException {
        Path jar = temp.resolve("manifest-case.jar");
        Manifest manifest = new Manifest();
        Attributes attrs = manifest.getMainAttributes();
        attrs.put(Attributes.Name.MANIFEST_VERSION, "1.0");
        attrs.putValue("Plugin-Id", "manifest-case");
        attrs.putValue("Plugin-Version", "3.1.4");
        attrs.putValue("Plugin-Class", "org.pf4j.Plugin");
        attrs.putValue("Plugin-Requires", "*");
        attrs.putValue("Plugin-Description", "manifest-desc");
        attrs.putValue("Plugin-Provider", "manifest-provider");
        attrs.putValue("Plugin-License", "BSD-3-Clause");
        try (JarOutputStream ignored = new JarOutputStream(Files.newOutputStream(jar), manifest)) {}
        PluginDescriptor descriptor = new ManifestPluginDescriptorFinder().find(jar);
        assertEquals("manifest-case", descriptor.getPluginId());
        assertEquals("3.1.4", descriptor.getVersion());
        assertEquals("manifest-desc", descriptor.getPluginDescription());
        assertEquals("BSD-3-Clause", descriptor.getLicense());
    }

    /** Verifies: PF4J-DEP-004. */ @Test
    void descriptorRetainsOrderedDependencies() {
        DefaultPluginDescriptor descriptor = descriptor("order-case", "1.0.0");
        descriptor.addDependency(new PluginDependency("first@1.0.0"));
        descriptor.addDependency(new PluginDependency("second@2.0.0"));
        assertEquals(List.of("first", "second"), List.of(
            descriptor.getDependencies().get(0).getPluginId(),
            descriptor.getDependencies().get(1).getPluginId()));
    }

    /** Verifies: PF4J-DEP-001, PF4J-DEP-002. */ @Test
    void dependencyDefaultsWildcard() {
        PluginDependency dependency = new PluginDependency("plain-base");
        assertEquals("plain-base", dependency.getPluginId());
        assertEquals("*", dependency.getPluginVersionSupport());
        assertFalse(dependency.isOptional());
    }

    /** Verifies: PF4J-DEP-003. */ @Test
    void dependencyParsesOptionalMarker() {
        PluginDependency dependency = new PluginDependency("cache-layer?@>=2.0.0");
        assertEquals("cache-layer", dependency.getPluginId());
        assertTrue(dependency.isOptional());
    }

    /** Verifies: PF4J-DEP-001. */ @Test
    void dependencyParsesVersionExpression() {
        assertEquals(">=2.1.0 & <4.0.0",
            new PluginDependency("range-base@>=2.1.0 & <4.0.0").getPluginVersionSupport());
    }

    /** Verifies: PF4J-DEP-005, PF4J-DEP-010. */ @Test
    void resolverOrdersRequiredDependencies() {
        DefaultPluginDescriptor base = descriptor("resolver-base", "2.5.0");
        DefaultPluginDescriptor feature = descriptor("resolver-feature", "1.0.0");
        feature.addDependency(new PluginDependency("resolver-base@>=2.0.0"));
        DependencyResolver.Result result = resolver().resolve(List.of(feature, base));
        assertTrue(result.isOK());
        assertEquals(List.of("resolver-base", "resolver-feature"), result.getSortedPlugins());
    }

    /** Verifies: PF4J-DEP-006. */ @Test
    void resolverIgnoresMissingOptionalDependency() {
        DefaultPluginDescriptor feature = descriptor("optional-owner", "1.0.0");
        feature.addDependency(new PluginDependency("absent-helper?@1.0.0"));
        DependencyResolver.Result result = resolver().resolve(List.of(feature));
        assertTrue(result.isOK());
        assertEquals(List.of("optional-owner"), result.getSortedPlugins());
    }

    /** Verifies: PF4J-DEP-007. */ @Test
    void resolverReportsMissingRequiredDependency() {
        DefaultPluginDescriptor feature = descriptor("missing-owner", "1.0.0");
        feature.addDependency(new PluginDependency("missing-base"));
        DependencyResolver.Result result = resolver().resolve(List.of(feature));
        assertTrue(result.hasNotFoundDependencies());
        assertEquals(List.of("missing-base"), result.getNotFoundDependencies());
    }

    /** Verifies: PF4J-DEP-009. */ @Test
    void resolverReportsCycle() {
        DefaultPluginDescriptor left = descriptor("cycle-left", "1.0.0");
        DefaultPluginDescriptor right = descriptor("cycle-right", "1.0.0");
        left.addDependency(new PluginDependency("cycle-right"));
        right.addDependency(new PluginDependency("cycle-left"));
        DependencyResolver.Result result = resolver().resolve(List.of(left, right));
        assertTrue(result.hasCyclicDependency());
        assertTrue(result.getSortedPlugins().isEmpty());
    }

    /** Verifies: PF4J-DEP-011. */ @Test
    void resolverReturnsDirectRelations() {
        DefaultPluginDescriptor base = descriptor("direct-base", "1.0.0");
        DefaultPluginDescriptor child = descriptor("direct-child", "1.0.0");
        child.addDependency(new PluginDependency("direct-base"));
        DependencyResolver resolver = resolver();
        resolver.resolve(List.of(child, base));
        assertEquals(List.of("direct-base"), resolver.getDependencies("direct-child"));
        assertEquals(List.of("direct-child"), resolver.getDependents("direct-base"));
    }

    /** Verifies: PF4J-DEP-012. */ @Test
    void resolverBeforeResolveRaisesIllegalState() {
        assertThrows(IllegalStateException.class, () -> resolver().getDependencies("unresolved"));
    }

    /** Verifies: PF4J-DEP-013. */ @Test
    void versionManagerAcceptsWildcards() {
        DefaultVersionManager manager = new DefaultVersionManager();
        assertTrue(manager.checkVersionConstraint("2.7.0", null));
        assertTrue(manager.checkVersionConstraint("2.7.0", ""));
        assertTrue(manager.checkVersionConstraint("not-semver", "*"));
    }

    /** Verifies: PF4J-DEP-013. */ @Test
    void versionManagerEvaluatesRange() {
        DefaultVersionManager manager = new DefaultVersionManager();
        assertTrue(manager.checkVersionConstraint("2.7.0", ">=2.5.0 & <3.0.0"));
        assertFalse(manager.checkVersionConstraint("3.2.0", ">=2.5.0 & <3.0.0"));
    }

    /** Verifies: PF4J-DEP-014. */ @Test
    void versionManagerComparesOrdering() {
        DefaultVersionManager manager = new DefaultVersionManager();
        assertTrue(manager.compareVersions("2.0.1", "2.0.0") > 0);
        assertEquals(0, manager.compareVersions("4.1.0", "4.1.0"));
        assertTrue(manager.compareVersions("1.9.9", "2.0.0") < 0);
    }

    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateCreatedPredicate() { assertTrue(PluginState.CREATED.isCreated()); assertFalse(PluginState.STARTED.isCreated()); }
    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateDisabledPredicate() { assertTrue(PluginState.DISABLED.isDisabled()); assertFalse(PluginState.RESOLVED.isDisabled()); }
    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateResolvedPredicate() { assertTrue(PluginState.RESOLVED.isResolved()); assertFalse(PluginState.CREATED.isResolved()); }
    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateStartedPredicate() { assertTrue(PluginState.STARTED.isStarted()); assertFalse(PluginState.STOPPED.isStarted()); }
    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateStoppedPredicate() { assertTrue(PluginState.STOPPED.isStopped()); assertFalse(PluginState.STARTED.isStopped()); }
    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateFailedPredicate() { assertTrue(PluginState.FAILED.isFailed()); assertFalse(PluginState.DISABLED.isFailed()); }
    /** Verifies: PF4J-LIFE-001. */ @Test void pluginStateUnloadedPredicate() { assertTrue(PluginState.UNLOADED.isUnloaded()); assertFalse(PluginState.CREATED.isUnloaded()); }

    /** Verifies: PF4J-LIFE-002. */ @Test
    void stateParseCaseInsensitive() { assertEquals(PluginState.STARTED, PluginState.parse("StArTeD")); }

    /** Verifies: PF4J-LIFE-023, PF4J-LIFE-024. */ @Test
    void statusProviderReadsDisabledList() throws IOException {
        Files.writeString(temp.resolve("disabled.txt"), "# comment\n\nred-plugin\n", StandardCharsets.UTF_8);
        DefaultPluginStatusProvider provider = new DefaultPluginStatusProvider(temp);
        assertTrue(provider.isPluginDisabled("red-plugin"));
        assertFalse(provider.isPluginDisabled("green-plugin"));
    }

    /** Verifies: PF4J-LIFE-021. */ @Test
    void statusProviderPersistsDisableEnable() {
        DefaultPluginStatusProvider provider = new DefaultPluginStatusProvider(temp);
        provider.disablePlugin("toggle-plugin");
        assertTrue(provider.isPluginDisabled("toggle-plugin"));
        assertTrue(Files.exists(provider.getDisabledFilePath()));
        provider.enablePlugin("toggle-plugin");
        assertFalse(provider.isPluginDisabled("toggle-plugin"));
    }

    /** Verifies: PF4J-LIFE-031. */ @Test
    void eventExposesTransitionFields() {
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        PluginWrapper wrapper = new PluginWrapper(manager, descriptor("event-plugin", "1.0.0"), temp,
            getClass().getClassLoader());
        wrapper.setPluginState(PluginState.STARTED);
        PluginStateEvent event = new PluginStateEvent(manager, wrapper, PluginState.RESOLVED);
        assertSame(manager, event.getSource());
        assertSame(wrapper, event.getPlugin());
        assertEquals(PluginState.RESOLVED, event.getOldState());
        assertEquals(PluginState.STARTED, event.getPluginState());
    }

    /** Verifies: PF4J-EXT-016, PF4J-EXT-017. */ @Test
    void defaultFactoryCreatesFreshInstances() {
        DefaultExtensionFactory factory = new DefaultExtensionFactory();
        FreshExtension first = factory.create(FreshExtension.class);
        FreshExtension second = factory.create(FreshExtension.class);
        assertEquals("fresh", first.value());
        assertNotSame(first, second);
    }

    /** Verifies: PF4J-EXT-016, PF4J-ERR-009. */ @Test
    void defaultFactoryWrapsConstructorFailure() {
        assertThrows(PluginRuntimeException.class,
            () -> new DefaultExtensionFactory().create(BrokenExtension.class));
    }

    /** Verifies: PF4J-EXT-018. */ @Test
    void extensionWrapperCachesLazily() {
        ExtensionWrapper<FreshExtension> wrapper = new ExtensionWrapper<>(
            new ExtensionDescriptor(7, FreshExtension.class), new DefaultExtensionFactory());
        FreshExtension first = wrapper.getExtension();
        assertSame(first, wrapper.getExtension());
        assertEquals(7, wrapper.getOrdinal());
    }

    /** Verifies: PF4J-CL-005, PF4J-CL-007. */ @Test
    void classLoadingPdaOrder() {
        assertEquals(List.of(ClassLoadingStrategy.Source.PLUGIN,
            ClassLoadingStrategy.Source.DEPENDENCIES, ClassLoadingStrategy.Source.APPLICATION),
            ClassLoadingStrategy.PDA.getSources());
    }

    /** Verifies: PF4J-CL-007. */ @Test
    void classLoadingApdOrder() {
        assertEquals(List.of(ClassLoadingStrategy.Source.APPLICATION,
            ClassLoadingStrategy.Source.PLUGIN, ClassLoadingStrategy.Source.DEPENDENCIES),
            ClassLoadingStrategy.APD.getSources());
    }

    /** Verifies: PF4J-CL-007. */ @Test
    void classLoadingAllStrategiesHaveThreeSources() {
        List<ClassLoadingStrategy> strategies = List.of(ClassLoadingStrategy.APD, ClassLoadingStrategy.ADP,
            ClassLoadingStrategy.PAD, ClassLoadingStrategy.DAP, ClassLoadingStrategy.DPA, ClassLoadingStrategy.PDA);
        assertTrue(strategies.stream().allMatch(strategy -> strategy.getSources().size() == 3));
        assertTrue(strategies.stream().allMatch(strategy -> strategy.getSources().stream().distinct().count() == 3));
    }

    /** Verifies: PF4J-CL-003, PF4J-CL-004. */ @Test
    void pluginClassLoaderCloses() throws IOException {
        PluginClassLoader loader = pluginLoader("close-case");
        assertFalse(loader.isClosed());
        loader.close();
        assertTrue(loader.isClosed());
    }

    /** Verifies: PF4J-CL-006. */ @Test
    void pluginClassLoaderDelegatesJavaClass() throws ClassNotFoundException {
        PluginClassLoader loader = pluginLoader("delegate-case");
        assertSame(String.class, loader.loadClass("java.lang.String"));
    }

    /** Verifies: PF4J-LIFE-005. */ @Test
    void wrapperExposesIdentity() {
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        DefaultPluginDescriptor descriptor = descriptor("wrapper-id", "5.0.0");
        PluginWrapper wrapper = new PluginWrapper(manager, descriptor, temp, getClass().getClassLoader());
        assertSame(manager, wrapper.getPluginManager());
        assertSame(descriptor, wrapper.getDescriptor());
        assertEquals("wrapper-id", wrapper.getPluginId());
        assertEquals(temp, wrapper.getPluginPath());
        assertSame(getClass().getClassLoader(), wrapper.getPluginClassLoader());
    }

    static DefaultPluginDescriptor descriptor(String id, String version) {
        return new DefaultPluginDescriptor(id, "", "org.pf4j.Plugin", version, "*", "", "");
    }

    static DependencyResolver resolver() { return new DependencyResolver(new DefaultVersionManager()); }

    PluginClassLoader pluginLoader(String id) {
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        return new PluginClassLoader(manager, descriptor(id, "1.0.0"), getClass().getClassLoader());
    }

    public static class FreshExtension { public FreshExtension() {} public String value() { return "fresh"; } }
    public static class BrokenExtension { private BrokenExtension() { throw new IllegalStateException(); } }
}
