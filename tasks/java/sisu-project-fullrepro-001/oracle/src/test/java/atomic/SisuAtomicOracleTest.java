package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.google.inject.AbstractModule;
import com.google.inject.Binding;
import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.name.Names;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import org.eclipse.sisu.Description;
import org.eclipse.sisu.Dynamic;
import org.eclipse.sisu.EagerSingleton;
import org.eclipse.sisu.Hidden;
import org.eclipse.sisu.Parameters;
import org.eclipse.sisu.PostConstruct;
import org.eclipse.sisu.PreDestroy;
import org.eclipse.sisu.Priority;
import org.eclipse.sisu.Typed;
import org.eclipse.sisu.bean.LifecycleManager;
import org.eclipse.sisu.inject.DefaultRankingFunction;
import org.eclipse.sisu.inject.DeferredClass;
import org.eclipse.sisu.space.BeanScanning;
import org.eclipse.sisu.space.URLClassSpace;
import org.eclipse.sisu.wire.ParameterKeys;
import org.junit.jupiter.api.Test;
import support.OracleFixtures;

class SisuAtomicOracleTest {
    private static Map<String, String> scanning(String value) {
        Map<String, String> map = new HashMap<String, String>();
        map.put(BeanScanning.class.getName(), value);
        return map;
    }

    /** Verifies: SISU-DISC-001 */
    @Test void scanningDefaultsToOnWhenMissing() { assertEquals(BeanScanning.ON, BeanScanning.select(Collections.emptyMap())); }
    /** Verifies: SISU-DISC-001 */
    @Test void scanningDefaultsToOnWhenBlank() { assertEquals(BeanScanning.ON, BeanScanning.select(scanning("  "))); }
    /** Verifies: SISU-DISC-002 */
    @Test void scanningSelectsOnIgnoringCase() { assertEquals(BeanScanning.ON, BeanScanning.select(scanning("oN"))); }
    /** Verifies: SISU-DISC-002 */
    @Test void scanningSelectsIndexIgnoringCase() { assertEquals(BeanScanning.INDEX, BeanScanning.select(scanning("InDeX"))); }
    /** Verifies: SISU-DISC-003, SISU-ERR-001 */
    @Test void scanningRejectsUnknownOption() { assertThrows(IllegalArgumentException.class, () -> BeanScanning.select(scanning("remote"))); }

    /** Verifies: SISU-LOC-017 */
    @Test void rankingDefaultHasMaximumRange() { assertEquals(Integer.MAX_VALUE, new DefaultRankingFunction().maxRank()); }
    /** Verifies: SISU-LOC-017 */
    @Test void rankingConfiguredHasMaximumRange() { assertEquals(Integer.MAX_VALUE, new DefaultRankingFunction(91).maxRank()); }
    /** Verifies: SISU-LOC-016, SISU-ERR-002 */
    @Test void rankingRejectsNegativePrimaryRank() { assertThrows(IllegalArgumentException.class, () -> new DefaultRankingFunction(-1)); }
    /** Verifies: SISU-LOC-016 */
    @Test void rankingUsesPrimaryRankForDefaultBinding() {
        Injector injector = Guice.createInjector(new AbstractModule() { protected void configure() { bind(OracleFixtures.Service.class).to(OracleFixtures.AlphaService.class); }});
        Binding<OracleFixtures.Service> binding = injector.getBinding(OracleFixtures.Service.class);
        assertEquals(47, new DefaultRankingFunction(47).rank(binding));
    }
    /** Verifies: SISU-LOC-016 */
    @Test void rankingPartitionsNamedBindingBelowDefault() {
        Injector injector = Guice.createInjector(new AbstractModule() { protected void configure() { bind(OracleFixtures.Service.class).annotatedWith(Names.named("side-83")).to(OracleFixtures.BetaService.class); }});
        Binding<OracleFixtures.Service> binding = injector.getBinding(Key.get(OracleFixtures.Service.class, Names.named("side-83")));
        assertTrue(new DefaultRankingFunction(47).rank(binding) < 0);
    }
    /** Verifies: SISU-LOC-016 */
    @Test void rankingReadsPriorityAnnotation() {
        Injector injector = Guice.createInjector(new AbstractModule() { protected void configure() { bind(OracleFixtures.Service.class).to(OracleFixtures.RankedService.class); }});
        assertEquals(73, new DefaultRankingFunction().rank(injector.getBinding(OracleFixtures.Service.class)));
    }

    /** Verifies: SISU-WIRE-015 */
    @Test void parameterPropertiesKeyMatchesContract() { assertEquals(Key.get(Map.class, Parameters.class), ParameterKeys.PROPERTIES); }
    /** Verifies: SISU-WIRE-016 */
    @Test void parameterArgumentsKeyMatchesContract() { assertEquals(Key.get(String[].class, Parameters.class), ParameterKeys.ARGUMENTS); }
    /** Verifies: SISU-WIRE-015 */
    @Test void parameterPropertiesKeyUsesParametersQualifier() { assertEquals(Parameters.class, ParameterKeys.PROPERTIES.getAnnotationType()); }
    /** Verifies: SISU-WIRE-016 */
    @Test void parameterArgumentsKeyExposesArrayRawType() { assertEquals(String[].class, ParameterKeys.ARGUMENTS.getTypeLiteral().getRawType()); }

    /** Verifies: SISU-DISC-022 */
    @Test void urlClassSpaceLoadsVisibleClass() { assertSame(String.class, new URLClassSpace(getClass().getClassLoader()).loadClass("java.lang.String")); }
    /** Verifies: SISU-DISC-022, SISU-ERR-003 */
    @Test void urlClassSpaceRejectsMissingClass() { assertThrows(TypeNotPresentException.class, () -> new URLClassSpace(getClass().getClassLoader()).loadClass("missing.oracle.Type91")); }
    /** Verifies: SISU-DISC-023 */
    @Test void urlClassSpaceFindsVisibleResource() { assertNotNull(new URLClassSpace(getClass().getClassLoader()).getResource("atomic/SisuAtomicOracleTest.class")); }
    /** Verifies: SISU-DISC-023 */
    @Test void urlClassSpaceReturnsNullForMissingResource() { assertNull(new URLClassSpace(getClass().getClassLoader()).getResource("missing/oracle/resource-103")); }
    /** Verifies: SISU-DISC-023 */
    @Test void urlClassSpaceEnumeratesVisibleResource() { assertTrue(new URLClassSpace(getClass().getClassLoader()).getResources("atomic/SisuAtomicOracleTest.class").hasMoreElements()); }
    /** Verifies: SISU-DISC-023 */
    @Test void urlClassSpaceReturnsEmptyEnumerationOnIoFailure() {
        ClassLoader loader = new ClassLoader(null) { public java.util.Enumeration<URL> getResources(String name) throws java.io.IOException { throw new java.io.IOException(); }};
        assertFalse(new URLClassSpace(loader).getResources("probe").hasMoreElements());
    }
    /** Verifies: SISU-DISC-024 */
    @Test void urlClassSpaceReturnsDefensiveUrlCopy() throws Exception {
        URL first = new URL("file:/oracle-alpha/");
        URLClassSpace space = new URLClassSpace(URLClassLoader.newInstance(new URL[] { first }, null));
        URL[] copy = space.getURLs(); copy[0] = new URL("file:/oracle-beta/");
        assertEquals(first, space.getURLs()[0]);
    }
    /** Verifies: SISU-DISC-026 */
    @Test void deferredClassExposesNameWithoutLoad() { assertEquals("java.lang.Integer", new URLClassSpace(getClass().getClassLoader()).deferLoadClass("java.lang.Integer").getName()); }
    /** Verifies: SISU-DISC-027 */
    @Test void deferredClassLoadsVisibleClass() { assertSame(Long.class, new URLClassSpace(getClass().getClassLoader()).deferLoadClass("java.lang.Long").load()); }
    /** Verifies: SISU-DISC-027 */
    @Test void deferredClassPropagatesMissingType() { DeferredClass<?> type = new URLClassSpace(getClass().getClassLoader()).deferLoadClass("missing.oracle.Type107"); assertThrows(TypeNotPresentException.class, type::load); }
    /** Verifies: SISU-DISC-028 */
    @Test void deferredClassCreatesProviderForSameType() { DeferredClass<?> type = new URLClassSpace(getClass().getClassLoader()).deferLoadClass("java.lang.StringBuilder"); assertNotNull(type.asProvider()); }

    /** Verifies: SISU-DISC-015 */
    @Test void descriptionIsRuntimeAnnotation() { assertEquals(RetentionPolicy.RUNTIME, Description.class.getAnnotation(Retention.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void priorityIsRuntimeAnnotation() { assertEquals(RetentionPolicy.RUNTIME, Priority.class.getAnnotation(Retention.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void typedIsRuntimeAnnotation() { assertEquals(RetentionPolicy.RUNTIME, Typed.class.getAnnotation(Retention.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void hiddenIsRuntimeAnnotation() { assertEquals(RetentionPolicy.RUNTIME, Hidden.class.getAnnotation(Retention.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void eagerSingletonTargetsTypes() { assertArrayEquals(new ElementType[] {ElementType.TYPE}, EagerSingleton.class.getAnnotation(Target.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void postConstructTargetsMethods() { assertArrayEquals(new ElementType[] {ElementType.METHOD}, PostConstruct.class.getAnnotation(Target.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void preDestroyTargetsMethods() { assertArrayEquals(new ElementType[] {ElementType.METHOD}, PreDestroy.class.getAnnotation(Target.class).value()); }
    /** Verifies: SISU-DISC-015 */
    @Test void dynamicTargetsFieldsAndParameters() { assertTrue(java.util.Arrays.asList(Dynamic.class.getAnnotation(Target.class).value()).containsAll(java.util.Arrays.asList(ElementType.FIELD, ElementType.PARAMETER))); }
    /** Verifies: SISU-DISC-015 */
    @Test void parametersTargetsFieldsParametersAndMethods() { assertTrue(java.util.Arrays.asList(Parameters.class.getAnnotation(Target.class).value()).containsAll(java.util.Arrays.asList(ElementType.FIELD, ElementType.PARAMETER, ElementType.METHOD))); }
    /** Verifies: SISU-DISC-006 */
    @Test void typedAnnotationRetainsDeclaredClasses() { assertArrayEquals(new Class<?>[] {OracleFixtures.Service.class}, OracleFixtures.TypedService.class.getAnnotation(Typed.class).value()); }
    /** Verifies: SISU-DISC-009 */
    @Test void priorityAnnotationRetainsNumericValue() { assertEquals(73, OracleFixtures.RankedService.class.getAnnotation(Priority.class).value()); }
    /** Verifies: SISU-DISC-010 */
    @Test void descriptionAnnotationRetainsText() { assertEquals("ranked-service-73", OracleFixtures.RankedService.class.getAnnotation(Description.class).value()); }

    /** Verifies: SISU-LIFE-008 */
    @Test void lifecycleRecognizesManagedClass() { assertTrue(new LifecycleManager().manage(OracleFixtures.ManagedService.class)); }
    /** Verifies: SISU-LIFE-008 */
    @Test void lifecycleRejectsPlainClassForReporting() { assertFalse(new LifecycleManager().manage(OracleFixtures.PlainService.class)); }
    /** Verifies: SISU-LIFE-011 */
    @Test void lifecycleHasNoCustomPropertyBinding() { assertNull(new LifecycleManager().manage((org.eclipse.sisu.bean.BeanProperty<?>) null)); }
    /** Verifies: SISU-LIFE-005 */
    @Test void lifecycleManagerReportsDirectBeanHandled() { LifecycleManager m=new LifecycleManager(); assertTrue(m.manage(new OracleFixtures.ManagedService())); }
}
