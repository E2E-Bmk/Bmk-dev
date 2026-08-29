package integration;

import io.github.resilience4j.bulkhead.BulkheadRegistry;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.consumer.EventConsumerRegistry;
import io.github.resilience4j.ratelimiter.RateLimiterConfig;
import io.github.resilience4j.ratelimiter.RateLimiterRegistry;
import io.github.resilience4j.retry.RetryConfig;
import io.github.resilience4j.retry.RetryRegistry;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfiguration;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfigurationProperties;
import io.github.resilience4j.spring6.retry.configure.RetryConfiguration;
import io.github.resilience4j.spring6.retry.configure.RetryConfigurationProperties;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import support.OracleFixtures;

import static org.junit.jupiter.api.Assertions.*;

/** Cross-view tests joining expression-selected names to registry projections. */
public class NameRegistryIntegrationTest {
    /** Verifies: R4J-AOP-003 R4J-CVI-001
     * Depends-On: templateExpressionUsesInvocationArgument, rootProjectsOriginalArgumentArray
     * Seam: state consistency / CVI-1 */
    @Test public void expressionNameEqualsCircuitBreakerRegistryName() throws Exception {
        String name = OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"cb-nebula-101", 1}, "#{#root.args[0]}");
        assertEquals(name, CircuitBreakerRegistry.ofDefaults().circuitBreaker(name).getName());
    }

    /** Verifies: R4J-AOP-003 R4J-CVI-001
     * Depends-On: templateExpressionUsesInvocationArgument, rootProjectsOriginalArgumentArray
     * Seam: state consistency / CVI-1 */
    @Test public void expressionNameEqualsRetryRegistryName() throws Exception {
        String name = OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"retry-nebula-103", 2}, "#{#root.args[0]}");
        assertEquals(name, RetryRegistry.ofDefaults().retry(name).getName());
    }

    /** Verifies: R4J-AOP-003 R4J-CVI-001
     * Depends-On: rootExpressionUsesInvocationMethod, resolverPreservesPlainText
     * Seam: state consistency / CVI-1 */
    @Test public void expressionNameEqualsRateLimiterRegistryName() throws Exception {
        String suffix = OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"unused-107", 3}, "#root.methodName");
        String name = "rate-nebula-" + suffix;
        assertEquals(name, RateLimiterRegistry.ofDefaults().rateLimiter(name).getName());
    }

    /** Verifies: R4J-AOP-003 R4J-CVI-001
     * Depends-On: beanExpressionReturnsStringProjection, resolverPreservesPlainText
     * Seam: state consistency / CVI-1 */
    @Test public void beanExpressionNameEqualsBulkheadRegistryName() throws Exception {
        String name = OracleFixtures.resolver().resolve(OracleFixtures.expressionMethod(), new Object[]{"unused-109", 4}, "@chromaticName.value()");
        assertEquals(name, BulkheadRegistry.ofDefaults().bulkhead(name).getName());
    }

    /** Verifies: R4J-AOP-003 R4J-AOP-005 R4J-AOP-006 R4J-CVI-002
     * Depends-On: templateExpressionUsesInvocationArgument, circuitBreakerConfiguredOrderRoundTrips
     * Seam: config interaction / CVI-2 */
    @Test public void resolvedCircuitBreakerNameUsesIndependentConfiguration() throws Exception {
        String name = OracleFixtures.resolver().resolve(
            OracleFixtures.expressionMethod(), new Object[]{"cb-instance-127", 5}, "#{#root.args[0]}");
        CircuitBreakerConfig config = CircuitBreakerConfig.custom().slidingWindowSize(17).minimumNumberOfCalls(3).build();
        var component = CircuitBreakerRegistry.of(Map.of("cb-config-113", config)).circuitBreaker(name, "cb-config-113");
        assertAll(() -> assertEquals(name, component.getName()), () -> assertEquals(17, component.getCircuitBreakerConfig().getSlidingWindowSize()));
    }

    /** Verifies: R4J-AOP-003 R4J-AOP-005 R4J-AOP-006 R4J-CVI-002
     * Depends-On: templateExpressionUsesInvocationArgument, retryConfiguredOrderRoundTrips
     * Seam: config interaction / CVI-2 */
    @Test public void resolvedRetryNameUsesIndependentConfiguration() throws Exception {
        String name = OracleFixtures.resolver().resolve(
            OracleFixtures.expressionMethod(), new Object[]{"retry-instance-137", 6}, "#{#root.args[0]}");
        RetryConfig config = RetryConfig.custom().maxAttempts(7).build();
        var component = RetryRegistry.of(Map.of("retry-config-131", config)).retry(name, "retry-config-131");
        assertAll(() -> assertEquals(name, component.getName()), () -> assertEquals(7, component.getRetryConfig().getMaxAttempts()));
    }

    /** Verifies: R4J-AOP-003 R4J-AOP-005 R4J-AOP-006 R4J-CVI-002
     * Depends-On: templateExpressionUsesInvocationArgument, rateLimiterConfiguredOrderRoundTrips
     * Seam: config interaction / CVI-2 */
    @Test public void resolvedRateLimiterNameUsesIndependentConfiguration() throws Exception {
        String name = OracleFixtures.resolver().resolve(
            OracleFixtures.expressionMethod(), new Object[]{"rate-instance-149", 7}, "#{#root.args[0]}");
        RateLimiterConfig config = RateLimiterConfig.custom().limitForPeriod(19).build();
        var component = RateLimiterRegistry.of(Map.of("rate-config-139", config)).rateLimiter(name, "rate-config-139");
        assertAll(() -> assertEquals(name, component.getName()), () -> assertEquals(19, component.getRateLimiterConfig().getLimitForPeriod()));
    }

    /** Verifies: R4J-CFG-003 R4J-CFG-004 R4J-CVI-006
     * Depends-On: circuitBreakerDefaultOrderIsLowestMinusFour, resolverPreservesPlainText
     * Seam: config interaction / CVI-6 */
    @Test public void circuitBreakerSpringConfigurationExposesRegistryAndEventBuffer() {
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(CircuitBreakerConfigurationProperties.class, CircuitBreakerConfigurationProperties::new);
            context.register(CircuitBreakerConfiguration.class);
            context.refresh();
            CircuitBreakerRegistry registry = context.getBean(CircuitBreakerRegistry.class);
            EventConsumerRegistry<?> events = context.getBean(EventConsumerRegistry.class);
            var component = registry.circuitBreaker("configured-cb-163");
            assertAll(() -> assertSame(component, registry.circuitBreaker("configured-cb-163")),
                () -> assertNotNull(events.getEventConsumer("configured-cb-163")));
        }
    }

    /** Verifies: R4J-CFG-003 R4J-CFG-004 R4J-CVI-006
     * Depends-On: retryDefaultOrderIsLowestMinusFive, resolverPreservesPlainText
     * Seam: config interaction / CVI-6 */
    @Test public void retrySpringConfigurationExposesRegistryAndEventBuffer() {
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(RetryConfigurationProperties.class, RetryConfigurationProperties::new);
            context.register(RetryConfiguration.class);
            context.refresh();
            RetryRegistry registry = context.getBean(RetryRegistry.class);
            EventConsumerRegistry<?> events = context.getBean(EventConsumerRegistry.class);
            var component = registry.retry("configured-retry-167");
            assertAll(() -> assertSame(component, registry.retry("configured-retry-167")),
                () -> assertNotNull(events.getEventConsumer("configured-retry-167")));
        }
    }

}
