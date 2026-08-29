package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.google.inject.AbstractModule;
import com.google.inject.ConfigurationException;
import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.Provides;
import com.google.inject.ProvisionException;
import com.google.inject.name.Named;
import com.google.inject.name.Names;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import javax.inject.Inject;
import org.eclipse.sisu.BeanEntry;
import org.eclipse.sisu.Mediator;
import org.eclipse.sisu.Parameters;
import org.eclipse.sisu.inject.BeanLocator;
import org.eclipse.sisu.inject.BindingPublisher;
import org.eclipse.sisu.inject.DefaultBeanLocator;
import org.eclipse.sisu.inject.DefaultRankingFunction;
import org.eclipse.sisu.inject.InjectorBindings;
import org.eclipse.sisu.inject.MutableBeanLocator;
import org.eclipse.sisu.space.BeanScanning;
import org.eclipse.sisu.space.IndexedClassFinder;
import org.eclipse.sisu.space.SpaceModule;
import org.eclipse.sisu.space.URLClassSpace;
import org.eclipse.sisu.wire.ChildWireModule;
import org.eclipse.sisu.wire.ParameterKeys;
import org.eclipse.sisu.wire.WireModule;
import org.junit.jupiter.api.Test;
import support.DiscoveredComponents;
import support.OracleFixtures;

class SisuCviOracleTest {
    static final class RankedTarget {
        @Inject OracleFixtures.Service single;
        @Inject List<OracleFixtures.Service> ordered;
    }

    static final class BadIntegerTarget {
        @Inject @javax.inject.Named("bad-count") Integer count;
    }

    static final class BadPropertiesModule extends AbstractModule {
        protected void configure() { bind(BadIntegerTarget.class); }
        @Provides @Parameters Map<String, String> properties() { return Collections.singletonMap("bad-count", "not-an-integer"); }
    }

    private static Injector discovered(BeanScanning scanning) {
        URL root = DiscoveredComponents.class.getProtectionDomain().getCodeSource().getLocation();
        URLClassSpace space = new URLClassSpace(DiscoveredComponents.class.getClassLoader(), new URL[] {root});
        return Guice.createInjector(new SpaceModule(space, scanning, true));
    }

    private static DefaultBeanLocator locatorFor(Injector injector) {
        DefaultBeanLocator locator = new DefaultBeanLocator();
        locator.add(new InjectorBindings(injector));
        return locator;
    }

    private static List<BeanEntry<Named, DiscoveredComponents.Contract>> discoveredEntries(BeanLocator locator) {
        List<BeanEntry<Named, DiscoveredComponents.Contract>> out = new ArrayList<BeanEntry<Named, DiscoveredComponents.Contract>>();
        for (BeanEntry<Named, DiscoveredComponents.Contract> entry : locator.<Named, DiscoveredComponents.Contract>locate(Key.get(DiscoveredComponents.Contract.class, Named.class))) out.add(entry);
        return out;
    }

    /** Verifies: SISU-CVI-001, SISU-DISC-004. Seam: protocol handoff from discovery to Guice and locator publication. Depends-On: urlClassSpaceFindsVisibleResource */
    @Test void discoveredBindingAppearsInGuiceAndLocator() {
        Injector injector = discovered(BeanScanning.ON);
        Key<DiscoveredComponents.Contract> key = Key.get(DiscoveredComponents.Contract.class, Names.named("indexed-alpha"));
        DiscoveredComponents.Contract direct = injector.getInstance(key);
        BeanEntry<Named, DiscoveredComponents.Contract> entry = locatorFor(injector).<Named, DiscoveredComponents.Contract>locate(key).iterator().next();
        assertEquals("indexed-alpha-61", direct.marker());
        assertEquals(direct.getClass(), entry.getValue().getClass());
    }

    /** Verifies: SISU-CVI-001, SISU-DISC-005. Seam: state consistency across discovered qualifier projections. Depends-On: descriptionAnnotationRetainsText */
    @Test void discoveredQualifierAgreesAcrossGuiceAndLocator() {
        Injector injector = discovered(BeanScanning.ON);
        assertEquals(DiscoveredComponents.IndexedAlpha.class, injector.getBinding(Key.get(DiscoveredComponents.Contract.class, Names.named("indexed-alpha"))).getProvider().get().getClass());
        assertTrue(discoveredEntries(locatorFor(injector)).stream().anyMatch(e -> "indexed-alpha".equals(e.getKey().value()) && e.getImplementationClass().equals(DiscoveredComponents.IndexedAlpha.class)));
    }

    /** Verifies: SISU-CVI-003, SISU-WIRE-001. Seam: protocol handoff from locator rank ordering to unresolved single wiring. Depends-On: rankingPartitionsNamedBindingBelowDefault */
    @Test void locatorTopRankAgreesWithWiredSingleValue() {
        Injector wired = Guice.createInjector(new WireModule(new AbstractModule() { protected void configure() {
            bind(RankedTarget.class);
            bind(OracleFixtures.Service.class).annotatedWith(Names.named("rank-low")).to(OracleFixtures.AlphaService.class);
            bind(OracleFixtures.Service.class).annotatedWith(Names.named("rank-high")).to(OracleFixtures.RankedService.class);
        }}));
        RankedTarget target = wired.getInstance(RankedTarget.class);
        assertEquals("ranked-73", target.single.value());
        assertEquals(target.single.getClass(), target.ordered.get(0).getClass());
    }

    /** Verifies: SISU-CVI-005, SISU-DISC-008. Seam: state consistency between hidden discovery and locator publication. Depends-On: hiddenIsRuntimeAnnotation */
    @Test void hiddenComponentIsAbsentFromLocatorResults() {
        DefaultBeanLocator locator = locatorFor(discovered(BeanScanning.ON));
        assertFalse(locator.<Named, DiscoveredComponents.Contract>locate(Key.get(DiscoveredComponents.Contract.class, Names.named("hidden-contract"))).iterator().hasNext());
    }

    /** Verifies: SISU-CVI-005, SISU-LOC-013. Seam: protocol handoff excludes hidden components from watcher events. Depends-On: hiddenIsRuntimeAnnotation */
    @Test void hiddenComponentIsAbsentFromWatcherEvents() {
        DefaultBeanLocator locator = new DefaultBeanLocator();
        final List<String> events = new ArrayList<String>();
        locator.watch(Key.get(DiscoveredComponents.Contract.class, Names.named("hidden-contract")), new Mediator<Named, DiscoveredComponents.Contract, List<String>>() {
            public void add(BeanEntry<Named, DiscoveredComponents.Contract> entry, List<String> watcher) { watcher.add(entry.getKey().value()); }
            public void remove(BeanEntry<Named, DiscoveredComponents.Contract> entry, List<String> watcher) { watcher.add("-" + entry.getKey().value()); }
        }, events);
        locator.add(new InjectorBindings(discovered(BeanScanning.ON)));
        assertTrue(events.isEmpty());
    }

    /** Verifies: SISU-CVI-006, SISU-DISC-006, SISU-ERR-007. Seam: protocol handoff preserves typed visibility and missing-binding failure in discovered Guice keys. Depends-On: typedAnnotationRetainsDeclaredClasses */
    @Test void typedComponentIsVisibleThroughDeclaredContractOnly() {
        Injector injector = discovered(BeanScanning.ON);
        assertEquals(DiscoveredComponents.TypedContract.class, injector.getInstance(Key.get(DiscoveredComponents.Contract.class, Names.named("typed-contract"))).getClass());
        assertThrows(ConfigurationException.class, () -> injector.getInstance(Key.get(DiscoveredComponents.Extra.class, Names.named("typed-contract"))));
    }

    /** Verifies: SISU-CVI-006, SISU-LOC-001. Seam: state consistency preserves typed visibility in locator compatibility. Depends-On: typedAnnotationRetainsDeclaredClasses */
    @Test void typedComponentLocatorVisibilityMatchesDeclaredContract() {
        DefaultBeanLocator locator = locatorFor(discovered(BeanScanning.ON));
        assertTrue(locator.<Named, DiscoveredComponents.Contract>locate(Key.get(DiscoveredComponents.Contract.class, Names.named("typed-contract"))).iterator().hasNext());
        assertFalse(locator.<Named, DiscoveredComponents.Extra>locate(Key.get(DiscoveredComponents.Extra.class, Names.named("typed-contract"))).iterator().hasNext());
    }

    /** Verifies: SISU-CVI-007, SISU-DISC-011, SISU-DISC-012. Seam: state consistency between full scan and named-index qualifier projection. Depends-On: scanningSelectsIndexIgnoringCase */
    @Test void indexedAndFullScanningExposeEquivalentQualifier() {
        Injector full = discovered(BeanScanning.ON);
        Injector index = discovered(BeanScanning.INDEX);
        Key<DiscoveredComponents.Contract> key = Key.get(DiscoveredComponents.Contract.class, Names.named("indexed-alpha"));
        assertEquals(full.getInstance(key).marker(), index.getInstance(key).marker());
    }

    /** Verifies: SISU-CVI-007, SISU-DISC-010. Seam: state consistency between full scan and named-index metadata projection. Depends-On: priorityAnnotationRetainsNumericValue */
    @Test void indexedAndFullScanningExposeEquivalentMetadata() {
        BeanEntry<Named, DiscoveredComponents.Contract> full = locatorFor(discovered(BeanScanning.ON)).<Named, DiscoveredComponents.Contract>locate(Key.get(DiscoveredComponents.Contract.class, Names.named("indexed-alpha"))).iterator().next();
        BeanEntry<Named, DiscoveredComponents.Contract> index = locatorFor(discovered(BeanScanning.INDEX)).<Named, DiscoveredComponents.Contract>locate(Key.get(DiscoveredComponents.Contract.class, Names.named("indexed-alpha"))).iterator().next();
        assertEquals(full.getDescription(), index.getDescription());
        assertEquals(full.getRank(), index.getRank());
        assertEquals(full.getImplementationClass(), index.getImplementationClass());
    }

    /** Verifies: SISU-ERR-004, SISU-DISC-030. Seam: error propagation from strict bytecode scanning into injector creation. Depends-On: urlClassSpaceRejectsMissingClass */
    @Test void strictScanningRejectsMalformedBytecode() throws Exception {
        URLClassSpace malformed = malformedSpace();
        assertThrows(RuntimeException.class, () -> Guice.createInjector(new SpaceModule(malformed, BeanScanning.ON, true)));
    }

    /** Verifies: SISU-ERR-005, SISU-DISC-030. Seam: error propagation is suppressed by lenient component scanning. Depends-On: urlClassSpaceReturnsEmptyEnumerationOnIoFailure */
    @Test void lenientScanningSkipsMalformedBytecode() throws Exception {
        URLClassSpace malformed = malformedSpace();
        assertNotNull(Guice.createInjector(new SpaceModule(malformed, BeanScanning.ON, false)));
    }

    /** Verifies: SISU-ERR-006, SISU-DISC-020. Seam: protocol handoff preserves indexed-enumeration exhaustion semantics. Depends-On: scanningSelectsIndexIgnoringCase */
    @Test void indexedEnumerationRejectsReadPastEnd() {
        IndexedClassFinder finder = new IndexedClassFinder("missing-oracle-index", false);
        Enumeration<?> classes = finder.findClasses(new URLClassSpace(new ClassLoader(null) {}));
        assertThrows(NoSuchElementException.class, classes::nextElement);
    }

    /** Verifies: SISU-ERR-008, SISU-WIRE-023. Seam: error propagation carries failed property conversion through wiring. Depends-On: parameterPropertiesKeyUsesParametersQualifier */
    @Test void wiringRejectsInvalidIntegerProperty() {
        Injector injector = Guice.createInjector(new WireModule(new BadPropertiesModule()));
        assertEquals("not-an-integer", injector.getInstance(ParameterKeys.PROPERTIES).get("bad-count"));
        assertThrows(RuntimeException.class, () -> injector.getInstance(BadIntegerTarget.class));
    }

    /** Verifies: SISU-ERR-009, SISU-LIFE-003. Seam: lifecycle crossing propagates a post-construction callback failure. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleCallbackFailurePropagatesFromProvisioning() {
        assertThrows(ProvisionException.class, () -> Guice.createInjector(new org.eclipse.sisu.bean.LifecycleModule()).getInstance(OracleFixtures.FailingManagedService.class));
    }

    /** Verifies: SISU-CVI-010, SISU-WIRE-024. Seam: lifecycle crossing from parent bindings into child wiring. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void childWireModulePreservesParentBinding() {
        Injector parent = Guice.createInjector(new WireModule(new AbstractModule() { protected void configure() {} @Provides @Named("parent-value") String parentValue() { return "parent-191"; } }));
        Injector child = parent.createChildInjector(new ChildWireModule(parent, new AbstractModule() { protected void configure() { bind(Key.get(OracleFixtures.Service.class, Names.named("child-service"))).to(OracleFixtures.AlphaService.class); }}));
        assertEquals("parent-191", child.getInstance(Key.get(String.class, Names.named("parent-value"))));
    }

    /** Verifies: SISU-CVI-010, SISU-WIRE-024. Seam: state consistency publishes child-only graph facts to the inherited locator. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void childWireModulePublishesChildGraphToInheritedLocator() {
        Injector parent = Guice.createInjector(new WireModule(new AbstractModule() { protected void configure() {} @Provides @Named("parent-only") String parentOnly() { return "parent-193"; } }));
        MutableBeanLocator locator = parent.getInstance(MutableBeanLocator.class);
        int parentBefore = count(locator.locate(Key.get(String.class, Names.named("parent-only"))));
        parent.createChildInjector(new ChildWireModule(parent, new AbstractModule() { protected void configure() { bind(Key.get(OracleFixtures.Service.class, Names.named("child-published"))).to(OracleFixtures.BetaService.class); }}));
        assertTrue(locator.<Named, OracleFixtures.Service>locate(Key.get(OracleFixtures.Service.class, Names.named("child-published"))).iterator().hasNext());
        assertEquals(parentBefore, count(locator.locate(Key.get(String.class, Names.named("parent-only")))));
    }

    private static int count(Iterable<?> values) {
        int count = 0;
        for (Object ignored : values) count++;
        return count;
    }

    private static URLClassSpace malformedSpace() throws Exception {
        java.nio.file.Path root = Files.createTempDirectory("sisu-malformed-");
        java.nio.file.Path resource = root.resolve("broken/Corrupt.class");
        Files.createDirectories(resource.getParent());
        Files.write(resource, "not-bytecode".getBytes(StandardCharsets.UTF_8));
        URL url = root.toUri().toURL();
        return new URLClassSpace(URLClassLoader.newInstance(new URL[] {url}, DiscoveredComponents.class.getClassLoader()), new URL[] {url});
    }
}
