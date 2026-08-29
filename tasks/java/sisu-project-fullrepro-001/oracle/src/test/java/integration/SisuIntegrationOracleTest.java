package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.google.inject.AbstractModule;
import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.Provides;
import com.google.inject.TypeLiteral;
import com.google.inject.name.Named;
import com.google.inject.name.Names;
import java.io.File;
import java.net.URL;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.inject.Inject;
import org.eclipse.sisu.BeanEntry;
import org.eclipse.sisu.Mediator;
import org.eclipse.sisu.Parameters;
import org.eclipse.sisu.bean.BeanManager;
import org.eclipse.sisu.bean.LifecycleManager;
import org.eclipse.sisu.bean.LifecycleModule;
import org.eclipse.sisu.inject.BindingPublisher;
import org.eclipse.sisu.inject.DefaultBeanLocator;
import org.eclipse.sisu.inject.DefaultRankingFunction;
import org.eclipse.sisu.inject.InjectorBindings;
import org.eclipse.sisu.inject.MutableBeanLocator;
import org.eclipse.sisu.inject.RankingFunction;
import org.eclipse.sisu.wire.ParameterKeys;
import org.eclipse.sisu.wire.WireModule;
import org.junit.jupiter.api.Test;
import support.OracleFixtures;

class SisuIntegrationOracleTest {
    private static Injector injector(final String name, final Class<? extends OracleFixtures.Service> impl) {
        return Guice.createInjector(new AbstractModule() {
            protected void configure() { bind(OracleFixtures.Service.class).annotatedWith(Names.named(name)).to(impl); }
        });
    }

    private static InjectorBindings publisher(Injector injector, int rank) {
        return new InjectorBindings(injector, new DefaultRankingFunction(rank));
    }

    private static List<BeanEntry<Named, OracleFixtures.Service>> entries(MutableBeanLocator locator) {
        List<BeanEntry<Named, OracleFixtures.Service>> out = new ArrayList<BeanEntry<Named, OracleFixtures.Service>>();
        for (BeanEntry<Named, OracleFixtures.Service> entry : locator.<Named, OracleFixtures.Service>locate(Key.get(OracleFixtures.Service.class, Named.class))) out.add(entry);
        return out;
    }

    private static int publisherCount(MutableBeanLocator locator) {
        int count = 0;
        for (BindingPublisher ignored : locator.publishers()) count++;
        return count;
    }

    /** Verifies: SISU-LOC-008, SISU-STATE-001. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void addingPublisherExposesIt() { MutableBeanLocator l=new DefaultBeanLocator(); BindingPublisher p=publisher(injector("add-11", OracleFixtures.AlphaService.class),11); assertTrue(l.add(p)); assertSame(p,l.publishers().iterator().next()); }
    /** Verifies: SISU-LOC-009. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void duplicatePublisherIsRejected() { MutableBeanLocator l=new DefaultBeanLocator(); BindingPublisher p=publisher(injector("dup-13", OracleFixtures.AlphaService.class),13); assertTrue(l.add(p)); assertFalse(l.add(p)); }
    /** Verifies: SISU-LOC-010, SISU-STATE-001. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void removingPublisherWithdrawsIt() { MutableBeanLocator l=new DefaultBeanLocator(); BindingPublisher p=publisher(injector("remove-17", OracleFixtures.AlphaService.class),17); l.add(p); assertTrue(l.remove(p)); assertEquals(0,publisherCount(l)); }
    /** Verifies: SISU-LOC-011, SISU-ERR-010. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void removingUnknownPublisherIsFalse() { MutableBeanLocator l=new DefaultBeanLocator(); assertFalse(l.remove(publisher(injector("unknown-19", OracleFixtures.AlphaService.class),19))); assertEquals(0,publisherCount(l)); }
    /** Verifies: SISU-LOC-012. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void clearWithdrawsAllPublishers() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("clear-a", OracleFixtures.AlphaService.class),23)); l.add(publisher(injector("clear-b", OracleFixtures.BetaService.class),29)); l.clear(); assertEquals(0,publisherCount(l)); }
    /** Verifies: SISU-LOC-001. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void emptyLocatorHasNoMatches() { assertTrue(entries(new DefaultBeanLocator()).isEmpty()); }
    /** Verifies: SISU-LOC-001, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryCarriesQualifier() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("qualifier-31", OracleFixtures.AlphaService.class),31)); assertEquals(Names.named("qualifier-31"), entries(l).get(0).getKey()); }
    /** Verifies: SISU-LOC-002, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryReturnsBoundValue() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("value-37", OracleFixtures.AlphaService.class),37)); assertEquals("alpha-37", entries(l).get(0).getValue().value()); }
    /** Verifies: SISU-LOC-002. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryReusesValue() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("reuse-41", OracleFixtures.AlphaService.class),41)); BeanEntry<Named,OracleFixtures.Service> e=entries(l).get(0); assertSame(e.getValue(),e.getValue()); }
    /** Verifies: SISU-LOC-002, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryProviderSuppliesValue() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("provider-43", OracleFixtures.BetaService.class),43)); BeanEntry<Named,OracleFixtures.Service> e=entries(l).get(0); assertEquals("beta-41",e.getProvider().get().value()); }
    /** Verifies: SISU-LOC-004, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryExposesImplementationClass() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("impl-47", OracleFixtures.BetaService.class),47)); assertEquals(OracleFixtures.BetaService.class, entries(l).get(0).getImplementationClass()); }
    /** Verifies: SISU-LOC-004, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryExposesBindingSource() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("source-53", OracleFixtures.BetaService.class),53)); assertNotNull(entries(l).get(0).getSource()); }
    /** Verifies: SISU-LOC-004, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: priorityAnnotationRetainsNumericValue */
    @Test void locatedEntryExposesPriorityRank() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("ranked-59", OracleFixtures.RankedService.class),0)); assertEquals(73, entries(l).get(0).getRank()); }
    /** Verifies: SISU-LOC-003, SISU-CVI-002. Seam: state consistency across composed public projections. Depends-On: descriptionAnnotationRetainsText */
    @Test void locatedEntryExposesDescription() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("described-61", OracleFixtures.RankedService.class),0)); assertEquals("ranked-service-73", entries(l).get(0).getDescription()); }
    /** Verifies: SISU-LOC-003. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void undescribedEntryHasNullDescription() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("plain-67", OracleFixtures.AlphaService.class),0)); assertNull(entries(l).get(0).getDescription()); }
    /** Verifies: SISU-LOC-005. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void locatedEntryRejectsMutation() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("immutable-71", OracleFixtures.AlphaService.class),0)); BeanEntry<Named,OracleFixtures.Service> e=entries(l).get(0); assertThrows(UnsupportedOperationException.class,()->e.setValue(new OracleFixtures.BetaService())); }
    /** Verifies: SISU-LOC-007, SISU-STATE-001. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void liveIterableReflectsLaterAddition() { MutableBeanLocator l=new DefaultBeanLocator(); Iterable<? extends BeanEntry<Named,OracleFixtures.Service>> live=l.locate(Key.get(OracleFixtures.Service.class,Named.class)); assertFalse(live.iterator().hasNext()); l.add(publisher(injector("live-add-73",OracleFixtures.AlphaService.class),0)); assertTrue(live.iterator().hasNext()); }
    /** Verifies: SISU-LOC-007, SISU-STATE-001. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void liveIterableReflectsLaterRemoval() { MutableBeanLocator l=new DefaultBeanLocator(); BindingPublisher p=publisher(injector("live-remove-79",OracleFixtures.AlphaService.class),0); l.add(p); Iterable<? extends BeanEntry<Named,OracleFixtures.Service>> live=l.locate(Key.get(OracleFixtures.Service.class,Named.class)); assertTrue(live.iterator().hasNext()); l.remove(p); assertFalse(live.iterator().hasNext()); }
    /** Verifies: SISU-LOC-006, SISU-CVI-003. Seam: state consistency across composed public projections. Depends-On: rankingPartitionsNamedBindingBelowDefault */
    @Test void locatedEntriesFollowPublisherRank() { MutableBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("lower-83",OracleFixtures.AlphaService.class),3)); l.add(publisher(injector("higher-89",OracleFixtures.BetaService.class),17)); List<BeanEntry<Named,OracleFixtures.Service>> es=entries(l); assertEquals("higher-89",es.get(0).getKey().value()); assertEquals("lower-83",es.get(1).getKey().value()); }
    /** Verifies: SISU-LOC-018. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void injectorPublisherAdaptsToInjector() { Injector i=injector("adapt-97",OracleFixtures.AlphaService.class); assertSame(i,new InjectorBindings(i).adapt(Injector.class)); }
    /** Verifies: SISU-LOC-018. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void injectorPublisherRejectsUnrelatedAdaptation() { assertNull(new InjectorBindings(injector("adapt-null-101",OracleFixtures.AlphaService.class)).adapt(String.class)); }
    /** Verifies: SISU-LOC-019. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void findBindingPublisherFallsBackToInjector() { Injector i=injector("fallback-pub-103",OracleFixtures.AlphaService.class); assertSame(i,InjectorBindings.findBindingPublisher(i).adapt(Injector.class)); }
    /** Verifies: SISU-LOC-020. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void findRankingFunctionFallsBackToDefault() { Injector i=injector("fallback-rank-107",OracleFixtures.AlphaService.class); assertTrue(InjectorBindings.findRankingFunction(i) instanceof DefaultRankingFunction); }
    /** Verifies: SISU-LOC-022. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void predicateSupplierFiltersLocatedEntries() { DefaultBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("filtered-109",OracleFixtures.AlphaService.class),0)); l.setBeanEntryPredicateSupplier(()->entry->false); assertTrue(entries(l).isEmpty()); }
    /** Verifies: SISU-LOC-022. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void nullPredicateRestoresLocatedEntries() { DefaultBeanLocator l=new DefaultBeanLocator(); l.add(publisher(injector("restored-113",OracleFixtures.AlphaService.class),0)); l.setBeanEntryPredicateSupplier(()->entry->false); l.setBeanEntryPredicateSupplier(null); assertFalse(entries(l).isEmpty()); }

    static final class RecordingMediator implements Mediator<Named,OracleFixtures.Service,OracleFixtures.EventWatcher> {
        public void add(BeanEntry<Named,OracleFixtures.Service> entry,OracleFixtures.EventWatcher watcher){ watcher.events.add("+"+entry.getKey().value()); }
        public void remove(BeanEntry<Named,OracleFixtures.Service> entry,OracleFixtures.EventWatcher watcher){ watcher.events.add("-"+entry.getKey().value()); }
    }
    /** Verifies: SISU-LOC-013, SISU-CVI-004. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void watcherReceivesPublisherAddition() { MutableBeanLocator l=new DefaultBeanLocator(); OracleFixtures.EventWatcher w=new OracleFixtures.EventWatcher(); l.watch(Key.get(OracleFixtures.Service.class,Named.class),new RecordingMediator(),w); l.add(publisher(injector("watch-add-127",OracleFixtures.AlphaService.class),0)); assertEquals(Collections.singletonList("+watch-add-127"),w.events); }
    /** Verifies: SISU-LOC-014, SISU-CVI-004. Seam: state consistency across composed public projections. Depends-On: rankingConfiguredHasMaximumRange */
    @Test void watcherReceivesPublisherRemoval() { MutableBeanLocator l=new DefaultBeanLocator(); OracleFixtures.EventWatcher w=new OracleFixtures.EventWatcher(); BindingPublisher p=publisher(injector("watch-remove-131",OracleFixtures.AlphaService.class),0); l.add(p); l.watch(Key.get(OracleFixtures.Service.class,Named.class),new RecordingMediator(),w); l.remove(p); assertEquals(Arrays.asList("+watch-remove-131","-watch-remove-131"),w.events); }

    static class ParameterTarget { @Inject @Parameters Map<String,String> properties; @Inject @Parameters String[] arguments; }
    static class ParameterModule extends AbstractModule {
        protected void configure(){ bind(ParameterTarget.class); }
        @Provides @Parameters Map<String,String> properties(){ Map<String,String> m=new LinkedHashMap<String,String>(); m.put("port","4317"); m.put("mode","probe"); return m; }
        @Provides @Parameters String[] arguments(){ return new String[]{"--alpha","29"}; }
    }
    /** Verifies: SISU-WIRE-017, SISU-CVI-008. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleProvidesEmptyProperties() { ParameterTarget t=Guice.createInjector(new WireModule(new AbstractModule(){protected void configure(){bind(ParameterTarget.class);}})).getInstance(ParameterTarget.class); assertTrue(t.properties.isEmpty()); }
    /** Verifies: SISU-WIRE-017. Seam: state consistency across composed public projections. Depends-On: parameterArgumentsKeyMatchesContract */
    @Test void wireModuleProvidesEmptyArguments() { ParameterTarget t=Guice.createInjector(new WireModule(new AbstractModule(){protected void configure(){bind(ParameterTarget.class);}})).getInstance(ParameterTarget.class); assertArrayEquals(new String[0],t.arguments); }
    /** Verifies: SISU-WIRE-018, SISU-CVI-008. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleInjectsParameterProperties() { ParameterTarget t=Guice.createInjector(new WireModule(new ParameterModule())).getInstance(ParameterTarget.class); assertEquals("4317",t.properties.get("port")); assertEquals("probe",t.properties.get("mode")); }
    /** Verifies: SISU-WIRE-019. Seam: state consistency across composed public projections. Depends-On: parameterArgumentsKeyMatchesContract */
    @Test void wireModuleInjectsParameterArguments() { ParameterTarget t=Guice.createInjector(new WireModule(new ParameterModule())).getInstance(ParameterTarget.class); assertArrayEquals(new String[]{"--alpha","29"},t.arguments); }

    static class NamedStringTarget { @Inject @javax.inject.Named("endpoint") String endpoint; @Inject @javax.inject.Named("count") Integer count; @Inject @javax.inject.Named("file") File file; @Inject @javax.inject.Named("path") Path path; @Inject @javax.inject.Named("url") URL url; }
    static class NamedStringModule extends AbstractModule {
        protected void configure(){ bind(NamedStringTarget.class); bind(ParameterKeys.PROPERTIES).toInstance(parameterMap()); }
        @SuppressWarnings({"rawtypes","unchecked"}) private Map parameterMap(){ Map m=new LinkedHashMap(); m.put("endpoint","tcp://host-137"); m.put("count","137"); m.put("file","relative-139.txt"); m.put("path","relative-149"); m.put("url","https://example.test/item-151"); return m; }
    }
    /** Verifies: SISU-WIRE-022, SISU-CVI-008. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleResolvesNamedStringProperty() { NamedStringTarget t=Guice.createInjector(new WireModule(new NamedStringModule())).getInstance(NamedStringTarget.class); assertEquals("tcp://host-137",t.endpoint); }
    /** Verifies: SISU-WIRE-022, SISU-WIRE-023. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleConvertsNamedIntegerProperty() { NamedStringTarget t=Guice.createInjector(new WireModule(new NamedStringModule())).getInstance(NamedStringTarget.class); assertEquals(Integer.valueOf(137),t.count); }
    /** Verifies: SISU-WIRE-023. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleConvertsNamedFileProperty() { NamedStringTarget t=Guice.createInjector(new WireModule(new NamedStringModule())).getInstance(NamedStringTarget.class); assertEquals(new File("relative-139.txt"),t.file); }
    /** Verifies: SISU-WIRE-023. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleConvertsNamedPathProperty() { NamedStringTarget t=Guice.createInjector(new WireModule(new NamedStringModule())).getInstance(NamedStringTarget.class); assertEquals(java.nio.file.Paths.get("relative-149"),t.path); }
    /** Verifies: SISU-WIRE-023. Seam: state consistency across composed public projections. Depends-On: parameterPropertiesKeyMatchesContract */
    @Test void wireModuleConvertsNamedUrlProperty() { NamedStringTarget t=Guice.createInjector(new WireModule(new NamedStringModule())).getInstance(NamedStringTarget.class); assertEquals("https://example.test/item-151",t.url.toString()); }

    /** Verifies: SISU-LIFE-001, SISU-LIFE-002, SISU-CVI-009. Seam: state consistency across composed public projections. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleModuleStartsInjectedBean() { Injector i=Guice.createInjector(new LifecycleModule()); OracleFixtures.ManagedService bean=i.getInstance(OracleFixtures.ManagedService.class); assertEquals(1,bean.starts); }
    /** Verifies: SISU-LIFE-001. Seam: state consistency across composed public projections. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleModuleExposesBeanManager() { Injector i=Guice.createInjector(new LifecycleModule()); assertTrue(i.getInstance(BeanManager.class) instanceof LifecycleManager); }
    /** Verifies: SISU-LIFE-001. Seam: state consistency across composed public projections. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleModuleBindsSuppliedManager() { LifecycleManager manager=new LifecycleManager(); Injector i=Guice.createInjector(new LifecycleModule(manager)); assertSame(manager,i.getInstance(BeanManager.class)); }
    /** Verifies: SISU-LIFE-005, SISU-CVI-009. Seam: state consistency across composed public projections. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleManagerStopsSpecificInjectedBean() { Injector i=Guice.createInjector(new LifecycleModule()); OracleFixtures.ManagedService bean=i.getInstance(OracleFixtures.ManagedService.class); assertTrue(i.getInstance(BeanManager.class).unmanage(bean)); assertEquals(1,bean.stops); }
    /** Verifies: SISU-LIFE-007, SISU-CVI-009. Seam: state consistency across composed public projections. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleManagerDoesNotStopBeanTwice() { Injector i=Guice.createInjector(new LifecycleModule()); OracleFixtures.ManagedService bean=i.getInstance(OracleFixtures.ManagedService.class); BeanManager m=i.getInstance(BeanManager.class); m.unmanage(bean); m.unmanage(bean); assertEquals(1,bean.stops); }
    /** Verifies: SISU-LIFE-006. Seam: state consistency across composed public projections. Depends-On: lifecycleRecognizesManagedClass */
    @Test void lifecycleManagerStopsAllInReverseOrder() { Injector i=Guice.createInjector(new LifecycleModule()); OracleFixtures.ManagedService a=i.getInstance(OracleFixtures.ManagedService.class); OracleFixtures.ManagedService b=i.getInstance(OracleFixtures.ManagedService.class); assertTrue(i.getInstance(BeanManager.class).unmanage()); assertEquals(1,a.stops); assertEquals(1,b.stops); }
}
