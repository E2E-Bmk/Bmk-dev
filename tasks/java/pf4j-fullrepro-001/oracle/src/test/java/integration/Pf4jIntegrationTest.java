package integration;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.pf4j.DefaultPluginManager;
import org.pf4j.DefaultPluginStatusProvider;
import org.pf4j.InvalidPluginDescriptorException;
import org.pf4j.PluginAlreadyLoadedException;
import org.pf4j.PluginRuntimeException;
import org.pf4j.PluginNotFoundException;
import org.pf4j.PluginState;
import org.pf4j.PluginStateEvent;
import org.pf4j.PluginWrapper;
import oraclesupport.AlphaGreeting;
import oraclesupport.BetaGreeting;
import oraclesupport.FailingStartPlugin;
import oraclesupport.Greeting;
import oraclesupport.PluginFixtures;
import oraclesupport.RecordingPlugin;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Generated black-box workflows over documented local artifact formats. */
class Pf4jIntegrationTest {
    @TempDir Path temp;

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-ART-006, PF4J-ART-022, PF4J-LIFE-003, PF4J-LIFE-004, PF4J-STATE-001, PF4J-STATE-003, PF4J-INV-001. Depends-On: atomic::Pf4jAtomicTest::managerKeepsOrderedRoots. */
    @Test void directoryLoadAlignsRegistryViews() throws Exception {
        PluginFixtures.directory(temp, "directory-one");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        PluginWrapper wrapper = manager.getPlugin("directory-one");
        assertNotNull(wrapper);
        assertTrue(manager.getPlugins().contains(wrapper));
        assertTrue(manager.getResolvedPlugins().contains(wrapper));
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-ART-006, PF4J-ART-022, PF4J-LIFE-003, PF4J-LIFE-005, PF4J-INV-001. Depends-On: atomic::Pf4jAtomicTest::managerKeepsOrderedRoots. */
    @Test void jarLoadAlignsRegistryViews() throws Exception {
        Path artifact = PluginFixtures.jar(temp, "jar-one");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        PluginWrapper wrapper = manager.getPlugin("jar-one");
        assertEquals(artifact, wrapper.getPluginPath());
        assertEquals(PluginState.RESOLVED, wrapper.getPluginState());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-008, PF4J-INV-002. Depends-On: atomic::Pf4jAtomicTest::resolverOrdersRequiredDependencies. */
    @Test void dependencyStartOrderUsesBaseBeforeFeature() throws Exception {
        PluginFixtures.directory(temp, "base", RecordingPlugin.class, "2.0.0", "");
        PluginFixtures.directory(temp, "feature", RecordingPlugin.class, "1.0.0", "base");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        manager.startPlugins();
        assertEquals(List.of("base", "feature"), ids(manager.getStartedPlugins()));
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-015, PF4J-LIFE-016, PF4J-INV-002. Depends-On: atomic::Pf4jAtomicTest::resolverOrdersRequiredDependencies, atomic::Pf4jAtomicTest::pluginStateStoppedPredicate. */
    @Test void stoppingBaseCascadesToDependent() throws Exception {
        PluginFixtures.directory(temp, "base", RecordingPlugin.class, "2.0.0", "");
        PluginFixtures.directory(temp, "feature", RecordingPlugin.class, "1.0.0", "base");
        DefaultPluginManager manager = started(temp);
        manager.stopPlugin("base");
        assertEquals(PluginState.STOPPED, manager.getPlugin("base").getPluginState());
        assertEquals(PluginState.STOPPED, manager.getPlugin("feature").getPluginState());
    }

    /** Seam: protocol handoff across plugin ownership, class loading, and extension discovery. Verifies: PF4J-LIFE-013, PF4J-EXT-009, PF4J-STATE-002, PF4J-INV-003. Depends-On: atomic::Pf4jAtomicTest::pluginStateStartedPredicate. */
    @Test void startedPluginPublishesExtensionAndCallback() throws Exception {
        Path artifact = PluginFixtures.directory(temp, "started-one");
        DefaultPluginManager manager = started(temp);
        assertTrue(Files.exists(artifact.resolve("started.marker")));
        assertEquals(Set.of("alpha-value", "beta-value"), texts(manager.getExtensions(Greeting.class)));
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-008, PF4J-LIFE-013, PF4J-EXT-009, PF4J-INV-003. Depends-On: atomic::Pf4jAtomicTest::pluginStateStartedPredicate. */
    @Test void bulkStartMakesEveryResolvedPluginVisible() throws Exception {
        PluginFixtures.directory(temp, "first");
        PluginFixtures.directory(temp, "second");
        DefaultPluginManager manager = started(temp);
        assertEquals(2, manager.getStartedPlugins().size());
        assertEquals(4, manager.getExtensions(Greeting.class).size());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-016, PF4J-EXT-011, PF4J-INV-004. Depends-On: atomic::Pf4jAtomicTest::pluginStateStoppedPredicate. */
    @Test void stoppedPluginHidesExtensions() throws Exception {
        PluginFixtures.directory(temp, "stoppable");
        DefaultPluginManager manager = started(temp);
        manager.stopPlugin("stoppable");
        assertTrue(manager.getExtensions(Greeting.class).isEmpty());
        assertTrue(manager.getStartedPlugins().isEmpty());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-020, PF4J-LIFE-021, PF4J-EXT-011, PF4J-INV-004, PF4J-INV-006. Depends-On: atomic::Pf4jAtomicTest::pluginStateDisabledPredicate, atomic::Pf4jAtomicTest::statusProviderPersistsDisableEnable. */
    @Test void disabledPluginHidesExtensions() throws Exception {
        PluginFixtures.directory(temp, "disable-me");
        DefaultPluginManager manager = started(temp);
        manager.disablePlugin("disable-me");
        assertEquals(PluginState.DISABLED, manager.getPlugin("disable-me").getPluginState());
        assertFalse(manager.getStartedPlugins().contains(manager.getPlugin("disable-me")));
        assertTrue(manager.getExtensions(Greeting.class).isEmpty());
        assertTrue(new DefaultPluginStatusProvider(temp).isPluginDisabled("disable-me"));
    }

    /** Seam: state consistency across manager registries, wrappers, listeners, and status projections. Verifies: PF4J-LIFE-030, PF4J-LIFE-031, PF4J-INV-005. Depends-On: atomic::Pf4jAtomicTest::eventExposesTransitionFields. */
    @Test void listenerBridgesResolvedToStarted() throws Exception {
        PluginFixtures.directory(temp, "eventful");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        List<PluginStateEvent> events = new ArrayList<>();
        manager.addPluginStateListener(events::add);
        manager.loadPlugins();
        manager.startPlugins();
        assertTrue(events.stream().anyMatch(e -> e.getPluginState() == PluginState.STARTED
            && e.getPlugin() == manager.getPlugin("eventful")));
    }

    /** Seam: state consistency across manager registries, wrappers, listeners, and status projections. Verifies: PF4J-LIFE-030, PF4J-LIFE-031, PF4J-INV-005. Depends-On: atomic::Pf4jAtomicTest::eventExposesTransitionFields. */
    @Test void removedListenerStopsDelivery() throws Exception {
        PluginFixtures.directory(temp, "quiet");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        List<PluginStateEvent> events = new ArrayList<>();
        org.pf4j.PluginStateListener listener = events::add;
        manager.addPluginStateListener(listener);
        manager.loadPlugins();
        int before = events.size();
        assertTrue(before > 0);
        assertTrue(events.stream().allMatch(e -> e.getSource() == manager
            && e.getPlugin() == manager.getPlugin("quiet")));
        manager.removePluginStateListener(listener);
        manager.startPlugins();
        assertEquals(before, events.size());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-020, PF4J-LIFE-021, PF4J-INV-006. Depends-On: atomic::Pf4jAtomicTest::statusProviderPersistsDisableEnable. */
    @Test void disablePersistsManagerAndProviderProjection() throws Exception {
        PluginFixtures.directory(temp, "persist-off");
        DefaultPluginManager manager = started(temp);
        manager.disablePlugin("persist-off");
        assertTrue(new DefaultPluginStatusProvider(temp).isPluginDisabled("persist-off"));
        assertEquals(PluginState.DISABLED, manager.getPlugin("persist-off").getPluginState());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-021, PF4J-LIFE-025, PF4J-INV-006. Depends-On: atomic::Pf4jAtomicTest::statusProviderPersistsDisableEnable. */
    @Test void enableClearsStatusProjection() throws Exception {
        PluginFixtures.directory(temp, "persist-on");
        DefaultPluginManager manager = started(temp);
        manager.disablePlugin("persist-on");
        manager.enablePlugin("persist-on");
        assertFalse(new DefaultPluginStatusProvider(temp).isPluginDisabled("persist-on"));
        assertEquals(PluginState.CREATED, manager.getPlugin("persist-on").getPluginState());
    }

    /** Seam: protocol handoff across plugin ownership, class loading, and extension discovery. Verifies: PF4J-CL-001, PF4J-EXT-010, PF4J-INV-007. Depends-On: atomic::Pf4jAtomicTest::classLoadingPdaOrder. */
    @Test void extensionClassUsesPluginClassLoader() throws Exception {
        PluginFixtures.directory(temp, "owned");
        DefaultPluginManager manager = started(temp);
        Class<? extends Greeting> type = manager.getExtensionClasses(Greeting.class, "owned").get(0);
        assertSame(manager.getPluginClassLoader("owned"), type.getClassLoader());
    }

    /** Seam: protocol handoff across plugin ownership, class loading, and extension discovery. Verifies: PF4J-CL-009, PF4J-EXT-010, PF4J-INV-007. Depends-On: atomic::Pf4jAtomicTest::classLoadingPdaOrder. */
    @Test void whichPluginMatchesScopedExtensionClass() throws Exception {
        PluginFixtures.directory(temp, "owner");
        DefaultPluginManager manager = started(temp);
        Class<? extends Greeting> type = manager.getExtensionClasses(Greeting.class, "owner").get(0);
        assertSame(manager.getPlugin("owner"), manager.whichPlugin(type));
    }

    /** Seam: protocol handoff across plugin ownership, class loading, and extension discovery. Verifies: PF4J-EXT-009, PF4J-EXT-013, PF4J-INV-008. Depends-On: atomic::Pf4jAtomicTest::defaultFactoryCreatesFreshInstances. */
    @Test void extensionClassAndInstanceOrderAgree() throws Exception {
        PluginFixtures.directory(temp, "ordered");
        DefaultPluginManager manager = started(temp);
        List<String> names = manager.getExtensionClasses(Greeting.class).stream().map(Class::getName).collect(Collectors.toList());
        List<String> instances = manager.getExtensions(Greeting.class).stream().map(x -> x.getClass().getName()).collect(Collectors.toList());
        assertEquals(names, instances);
    }

    /** Seam: protocol handoff across plugin ownership, class loading, and extension discovery. Verifies: PF4J-EXT-009, PF4J-EXT-010, PF4J-EXT-013, PF4J-INV-008. Depends-On: atomic::Pf4jAtomicTest::defaultFactoryCreatesFreshInstances. */
    @Test void scopedAndGlobalExtensionOrderAgree() throws Exception {
        PluginFixtures.directory(temp, "scoped");
        DefaultPluginManager manager = started(temp);
        List<String> global = manager.getExtensions(Greeting.class).stream()
            .map(x -> x.getClass().getName()).collect(Collectors.toList());
        List<String> scoped = manager.getExtensions(Greeting.class, "scoped").stream()
            .map(x -> x.getClass().getName()).collect(Collectors.toList());
        assertEquals(global, scoped);
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-026, PF4J-CL-010, PF4J-STATE-002, PF4J-STATE-003, PF4J-INV-009. Depends-On: atomic::Pf4jAtomicTest::pluginStateUnloadedPredicate. */
    @Test void unloadRemovesAllProjections() throws Exception {
        PluginFixtures.directory(temp, "gone");
        DefaultPluginManager manager = started(temp);
        assertTrue(manager.unloadPlugin("gone"));
        assertNull(manager.getPlugin("gone"));
        assertNull(manager.getPluginClassLoader("gone"));
        assertTrue(manager.getStartedPlugins().isEmpty());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-026, PF4J-INV-009. Depends-On: atomic::Pf4jAtomicTest::pluginStateStartedPredicate. */
    @Test void unloadPreservesUnrelatedPlugin() throws Exception {
        PluginFixtures.directory(temp, "gone");
        PluginFixtures.directory(temp, "stays");
        DefaultPluginManager manager = started(temp);
        manager.unloadPlugin("gone");
        assertNotNull(manager.getPlugin("stays"));
        assertEquals(PluginState.STARTED, manager.getPlugin("stays").getPluginState());
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-DEP-018, PF4J-ERR-008, PF4J-INV-010. Depends-On: atomic::Pf4jAtomicTest::dependencyParsesVersionExpression. */
    @Test void dependencyMismatchCarriesSameIds() throws Exception {
        PluginFixtures.directory(temp, "base", RecordingPlugin.class, "1.0.0", "");
        PluginFixtures.directory(temp, "feature", RecordingPlugin.class, "1.0.0", "base@>=2.0.0");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        org.pf4j.DependencyResolver.DependenciesWrongVersionException error = assertThrows(
            org.pf4j.DependencyResolver.DependenciesWrongVersionException.class, manager::loadPlugins);
        assertEquals("base", error.getDependencies().get(0).getDependencyId());
        assertEquals("feature", error.getDependencies().get(0).getDependentId());
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-DEP-018, PF4J-ERR-007, PF4J-INV-010. Depends-On: atomic::Pf4jAtomicTest::resolverReportsMissingRequiredDependency. */
    @Test void missingDependencyCarriesSameIds() throws Exception {
        PluginFixtures.directory(temp, "feature", RecordingPlugin.class, "1.0.0", "absent");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        org.pf4j.DependencyResolver.DependenciesNotFoundException error = assertThrows(
            org.pf4j.DependencyResolver.DependenciesNotFoundException.class, manager::loadPlugins);
        assertEquals(List.of("absent"), error.getDependencies());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-ART-006, PF4J-ART-008, PF4J-ART-022. Depends-On: atomic::Pf4jAtomicTest::managerKeepsOrderedRoots. */
    @Test void mixedDirectoryJarZipDiscovery() throws Exception {
        PluginFixtures.directory(temp, "dir-mixed");
        PluginFixtures.jar(temp, "jar-mixed");
        PluginFixtures.zip(temp, "zip-mixed");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        assertEquals(Set.of("dir-mixed", "jar-mixed", "zip-mixed"), Set.copyOf(ids(manager.getPlugins())));
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-LIFE-019, PF4J-ERR-004. Depends-On: atomic::Pf4jAtomicTest::wrapperExposesIdentity. */
    @Test void unknownLifecycleOperationCarriesPluginId() throws Exception {
        PluginFixtures.directory(temp, "known");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        PluginNotFoundException error = assertThrows(PluginNotFoundException.class,
            () -> manager.startPlugin("absent"));
        assertEquals("absent", error.getPluginId());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-ART-008, PF4J-ART-022, PF4J-LIFE-003, PF4J-LIFE-005. Depends-On: atomic::Pf4jAtomicTest::managerKeepsOrderedRoots. */
    @Test void zipExpandsAndLoads() throws Exception {
        Path zip = PluginFixtures.zip(temp, "zip-only");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        PluginWrapper wrapper = manager.getPlugin("zip-only");
        assertNotNull(wrapper);
        assertFalse(wrapper.getPluginPath().equals(zip));
        assertTrue(Files.isDirectory(wrapper.getPluginPath()));
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-LIFE-014. Depends-On: atomic::Pf4jAtomicTest::pluginStateFailedPredicate. */
    @Test void failedStartRetainsCauseAndState() throws Exception {
        PluginFixtures.directory(temp, "failing", FailingStartPlugin.class, "1.0.0", "");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        manager.startPlugin("failing");
        assertEquals(PluginState.FAILED, manager.getPlugin("failing").getPluginState());
        assertNotNull(manager.getPlugin("failing").getFailedException());
    }

    /** Seam: lifecycle crossing across plugin discovery, loading, state transitions, and removal. Verifies: PF4J-LIFE-015, PF4J-LIFE-016. Depends-On: atomic::Pf4jAtomicTest::pluginStateStoppedPredicate. */
    @Test void stopCallbackAndStateAgree() throws Exception {
        Path artifact = PluginFixtures.directory(temp, "stopped-marker");
        DefaultPluginManager manager = started(temp);
        manager.stopPlugin("stopped-marker");
        assertTrue(Files.exists(artifact.resolve("stopped.marker")));
        assertEquals(PluginState.STOPPED, manager.getPlugin("stopped-marker").getPluginState());
    }

    /** Seam: protocol handoff across plugin ownership, class loading, and extension discovery. Verifies: PF4J-EXT-010, PF4J-CL-009. Depends-On: atomic::Pf4jAtomicTest::defaultFactoryCreatesFreshInstances. */
    @Test void scopedExtensionBelongsOnlyToNamedPlugin() throws Exception {
        PluginFixtures.directory(temp, "left");
        PluginFixtures.directory(temp, "right");
        DefaultPluginManager manager = started(temp);
        for (Class<? extends Greeting> type : manager.getExtensionClasses(Greeting.class, "left")) {
            assertEquals("left", manager.whichPlugin(type).getPluginId());
        }
        assertEquals(2, manager.getExtensionClasses(Greeting.class, "left").size());
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-ART-018, PF4J-ERR-001. Depends-On: atomic::Pf4jAtomicTest::managerKeepsOrderedRoots. */
    @Test void missingAndNullLoadPathsRaiseIllegalArgument() {
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        assertThrows(IllegalArgumentException.class, () -> manager.loadPlugin(null));
        assertThrows(IllegalArgumentException.class, () -> manager.loadPlugin(temp.resolve("missing")));
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-ART-017, PF4J-ART-019, PF4J-ERR-002. Depends-On: atomic::Pf4jAtomicTest::propertiesFinderReadsAllFields. */
    @Test void duplicatePathReportsPluginIdentity() throws Exception {
        Path artifact = PluginFixtures.directory(temp, "duplicate");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        assertEquals("duplicate", manager.loadPlugin(artifact));
        PluginAlreadyLoadedException error = assertThrows(PluginAlreadyLoadedException.class,
            () -> manager.loadPlugin(artifact));
        assertEquals("duplicate", error.getPluginId());
        assertEquals(artifact, error.getPluginPath());
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-ART-016, PF4J-ERR-003. Depends-On: atomic::Pf4jAtomicTest::propertiesFinderReadsAllFields. */
    @Test void emptyDescriptorIdRaisesInvalidDescriptor() throws Exception {
        Path artifact = PluginFixtures.directory(temp, "", RecordingPlugin.class, "1.0.0", "");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        assertThrows(InvalidPluginDescriptorException.class, () -> manager.loadPlugin(artifact));
    }

    /** Seam: error propagation across plugin discovery, dependency resolution, and manager operations. Verifies: PF4J-DEP-018, PF4J-ERR-006. Depends-On: atomic::Pf4jAtomicTest::resolverReportsCycle. */
    @Test void cyclicManagerDependenciesRaisePublicException() throws Exception {
        PluginFixtures.directory(temp, "cycle-left", RecordingPlugin.class, "1.0.0", "cycle-right");
        PluginFixtures.directory(temp, "cycle-right", RecordingPlugin.class, "1.0.0", "cycle-left");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        assertThrows(org.pf4j.DependencyResolver.CyclicDependencyException.class, manager::loadPlugins);
    }

    /** Seam: state consistency across manager registries, wrappers, listeners, and status projections. Verifies: PF4J-ART-022, PF4J-LIFE-027, PF4J-CL-001, PF4J-ERR-010, PF4J-ERR-011. Depends-On: atomic::Pf4jAtomicTest::managerKeepsOrderedRoots. */
    @Test void unknownLookupAndUnloadUseSentinelsAfterResolution() throws Exception {
        PluginFixtures.directory(temp, "known-sentinel");
        DefaultPluginManager manager = new DefaultPluginManager(temp);
        manager.loadPlugins();
        assertNotNull(manager.getPlugin("known-sentinel"));
        assertNull(manager.getPlugin("absent"));
        assertNull(manager.getPluginClassLoader("absent"));
        assertFalse(manager.unloadPlugin("absent"));
    }

    private static DefaultPluginManager started(Path root) {
        DefaultPluginManager manager = new DefaultPluginManager(root);
        manager.loadPlugins();
        manager.startPlugins();
        return manager;
    }

    private static List<String> ids(List<PluginWrapper> wrappers) {
        return wrappers.stream().map(PluginWrapper::getPluginId).collect(Collectors.toList());
    }

    private static Set<String> texts(List<Greeting> greetings) {
        return greetings.stream().map(Greeting::text).collect(Collectors.toSet());
    }
}
