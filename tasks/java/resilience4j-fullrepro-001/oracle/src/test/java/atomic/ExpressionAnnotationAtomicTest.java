package atomic;

import io.github.resilience4j.spring6.spelresolver.DefaultSpelResolver;
import io.github.resilience4j.spring6.spelresolver.SpelRootObject;
import io.github.resilience4j.spring6.utils.AnnotationExtractor;
import java.lang.reflect.Proxy;
import org.junit.jupiter.api.Test;
import support.OracleFixtures;

import static org.junit.jupiter.api.Assertions.*;

/** Atomic contracts for expression and annotation resolution. */
public class ExpressionAnnotationAtomicTest {
    /** Verifies: R4J-SPE-006 */
    @Test public void rootProjectsDeclaringClassName() throws Exception {
        assertEquals(OracleFixtures.ExpressionService.class.getName(), new SpelRootObject(OracleFixtures.expressionMethod(), new Object[]{"zircon-13", 7}).getClassName());
    }

    /** Verifies: R4J-SPE-006 */
    @Test public void rootProjectsMethodName() throws Exception {
        assertEquals("combine", new SpelRootObject(OracleFixtures.expressionMethod(), new Object[]{"zircon-17", 9}).getMethodName());
    }

    /** Verifies: R4J-SPE-006 */
    @Test public void rootProjectsOriginalArgumentArray() throws Exception {
        Object[] args = {"zircon-19", 11};
        assertSame(args, new SpelRootObject(OracleFixtures.expressionMethod(), args).getArgs());
    }

    /** Verifies: R4J-SPE-001 */
    @Test public void resolverPreservesNull() throws Exception {
        assertNull(OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"opal-23", 1}, null));
    }

    /** Verifies: R4J-SPE-001 */
    @Test public void resolverPreservesEmptyText() throws Exception {
        assertEquals("", OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"opal-29", 2}, ""));
    }

    /** Verifies: R4J-SPE-001 */
    @Test public void resolverPreservesPlainText() throws Exception {
        assertEquals("plain-cobalt-31", OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"opal-31", 3}, "plain-cobalt-31"));
    }

    /** Verifies: R4J-SPE-002 */
    @Test public void resolverAppliesEmbeddedPlaceholderResolver() throws Exception {
        DefaultSpelResolver resolver = OracleFixtures.resolver();
        resolver.setEmbeddedValueResolver(value -> "${rare.key}".equals(value) ? "resolved-amber-37" : value);
        assertEquals("resolved-amber-37", resolver.resolve(OracleFixtures.expressionMethod(), new Object[]{"opal-37", 4}, "${rare.key}"));
    }

    /** Verifies: R4J-SPE-003 */
    @Test public void templateExpressionUsesInvocationArgument() throws Exception {
        assertEquals("prefix-topaz-41", OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"topaz-41", 5}, "prefix-#{#root.args[0]}"));
    }

    /** Verifies: R4J-SPE-004 */
    @Test public void rootExpressionUsesInvocationMethod() throws Exception {
        assertEquals("combine", OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"topaz-43", 6}, "#root.methodName"));
    }

    /** Verifies: R4J-SPE-005 */
    @Test public void beanExpressionReturnsStringProjection() throws Exception {
        assertEquals("ultraviolet-731", OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"topaz-47", 7}, "@chromaticName.value()"));
    }

    /** Verifies: R4J-SPE-007 */
    @Test public void extractorFindsDirectAnnotation() {
        assertEquals("direct-211", AnnotationExtractor.extract(OracleFixtures.DirectMarked.class, OracleFixtures.Marker.class).value());
    }

    /** Verifies: R4J-SPE-007 */
    @Test public void extractorFindsSuperclassAnnotation() {
        assertEquals("base-307", AnnotationExtractor.extract(OracleFixtures.MarkedChild.class, OracleFixtures.Marker.class).value());
    }

    /** Verifies: R4J-SPE-007 R4J-AOP-001 */
    @Test public void extractorPrefersDirectAnnotationOverSuperclassAnnotation() {
        assertEquals("child-401", AnnotationExtractor.extract(OracleFixtures.DirectMarkedChild.class, OracleFixtures.Marker.class).value());
    }

    /** Verifies: R4J-SPE-008 R4J-AOP-001 */
    @Test public void proxyExtractorFindsAnnotatedInterface() {
        Object proxy = Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{OracleFixtures.MarkedContract.class}, (p, m, a) -> "proxy-59");
        assertEquals("interface-419", AnnotationExtractor.extractAnnotationFromProxy(proxy, OracleFixtures.Marker.class).value());
    }

    /** Verifies: R4J-SPE-008 R4J-AOP-002 */
    @Test public void proxyExtractorReturnsNullForUnannotatedInterface() {
        Object proxy = Proxy.newProxyInstance(getClass().getClassLoader(), new Class<?>[]{OracleFixtures.PlainContract.class}, (p, m, a) -> "proxy-61");
        assertNull(AnnotationExtractor.extractAnnotationFromProxy(proxy, OracleFixtures.Marker.class));
    }
}
