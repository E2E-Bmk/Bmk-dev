package integration;

import io.github.resilience4j.bulkhead.Bulkhead;
import io.github.resilience4j.bulkhead.BulkheadRegistry;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.ratelimiter.RateLimiterRegistry;
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.retry.RetryRegistry;
import io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfigurationProperties;
import io.github.resilience4j.spring6.bulkhead.configure.ReactorBulkheadAspectExt;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfigurationProperties;
import io.github.resilience4j.spring6.circuitbreaker.configure.ReactorCircuitBreakerAspectExt;
import io.github.resilience4j.spring6.fallback.FallbackExecutor;
import io.github.resilience4j.spring6.fallback.ReactorFallbackDecorator;
import io.github.resilience4j.spring6.micrometer.configure.ReactorTimerAspectExt;
import io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfigurationProperties;
import io.github.resilience4j.spring6.ratelimiter.configure.ReactorRateLimiterAspectExt;
import io.github.resilience4j.spring6.retry.configure.ReactorRetryAspectExt;
import io.github.resilience4j.spring6.retry.configure.RetryAspect;
import io.github.resilience4j.spring6.retry.configure.RetryConfiguration;
import io.github.resilience4j.spring6.retry.configure.RetryConfigurationProperties;
import io.github.resilience4j.spring6.spelresolver.SpelResolver;
import io.github.resilience4j.spring6.timelimiter.configure.ReactorTimeLimiterAspectExt;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterAspect;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfiguration;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfigurationProperties;
import io.github.resilience4j.timelimiter.TimeLimiterRegistry;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import support.OracleFixtures;

import static org.junit.jupiter.api.Assertions.*;

/** Cross-view tests for adapter selection, aspect precedence, and scheduler lifecycle. */
public class AdapterLifecycleIntegrationTest {
    /** Verifies: R4J-CFG-008 R4J-CVI-005
     * Depends-On: retryConfiguredOrderRoundTrips, circuitBreakerConfiguredOrderRoundTrips
     * Seam: config interaction / CVI-5 */
    @Test public void retryConfigurationBeanProjectsConfiguredRelativeOrder() {
        RetryConfigurationProperties retryProperties = new RetryConfigurationProperties();
        retryProperties.setRetryAspectOrder(601);
        CircuitBreakerConfigurationProperties circuitProperties = new CircuitBreakerConfigurationProperties();
        circuitProperties.setCircuitBreakerAspectOrder(607);
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(RetryConfigurationProperties.class, () -> retryProperties);
            context.registerBean(RetryRegistry.class, RetryRegistry::ofDefaults);
            context.registerBean(FallbackExecutor.class, OracleFixtures::fallbackExecutor);
            context.registerBean(SpelResolver.class, () -> (method, args, value) -> value);
            context.register(RetryConfiguration.class);
            context.refresh();
            RetryAspect aspect = context.getBean(RetryAspect.class);
            assertAll(() -> assertEquals(retryProperties.getRetryAspectOrder(), aspect.getOrder()),
                () -> assertTrue(aspect.getOrder() < circuitProperties.getCircuitBreakerAspectOrder()));
        }
    }

    /** Verifies: R4J-CFG-008 R4J-CVI-005
     * Depends-On: timeLimiterConfiguredOrderRoundTrips, bulkheadConfiguredOrderRoundTrips
     * Seam: config interaction / CVI-5 */
    @Test public void timeLimiterConfigurationBeanProjectsConfiguredRelativeOrder() {
        TimeLimiterConfigurationProperties timeProperties = new TimeLimiterConfigurationProperties();
        timeProperties.setTimeLimiterAspectOrder(701);
        BulkheadConfigurationProperties bulkProperties = new BulkheadConfigurationProperties();
        bulkProperties.setBulkheadAspectOrder(709);
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(TimeLimiterConfigurationProperties.class, () -> timeProperties);
            context.registerBean(TimeLimiterRegistry.class, TimeLimiterRegistry::ofDefaults);
            context.registerBean(FallbackExecutor.class, OracleFixtures::fallbackExecutor);
            context.registerBean(SpelResolver.class, () -> (method, args, value) -> value);
            context.register(TimeLimiterConfiguration.class);
            context.refresh();
            TimeLimiterAspect aspect = context.getBean(TimeLimiterAspect.class);
            assertAll(() -> assertEquals(timeProperties.getTimeLimiterAspectOrder(), aspect.getOrder()),
                () -> assertTrue(aspect.getOrder() < bulkProperties.getBulkheadAspectOrder()));
        }
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-TIM-004 R4J-CVI-007
     * Depends-On: completionDecoratorSupportsStageFamily, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-7 */
    @Test public void circuitBreakerExtensionAndFallbackAgreeOnMonoFamily() {
        assertAll(() -> assertTrue(new ReactorCircuitBreakerAspectExt().canHandleReturnType(Mono.class)), () -> assertTrue(new ReactorFallbackDecorator().supports(Mono.class)));
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-TIM-004 R4J-CVI-007
     * Depends-On: completionDecoratorSupportsStageFamily, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-7 */
    @Test public void retryExtensionAndFallbackAgreeOnFluxFamily() {
        assertAll(() -> assertTrue(new ReactorRetryAspectExt().canHandleReturnType(Flux.class)), () -> assertTrue(new ReactorFallbackDecorator().supports(Flux.class)));
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-TIM-004 R4J-CVI-007
     * Depends-On: completionDecoratorSupportsStageFamily, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-7 */
    @Test public void rateLimiterExtensionAndFallbackAgreeOnMonoFamily() {
        assertAll(() -> assertTrue(new ReactorRateLimiterAspectExt().canHandleReturnType(Mono.class)), () -> assertTrue(new ReactorFallbackDecorator().supports(Mono.class)));
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-TIM-004 R4J-CVI-007
     * Depends-On: completionDecoratorSupportsStageFamily, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-7 */
    @Test public void bulkheadExtensionAndFallbackAgreeOnFluxFamily() {
        assertAll(() -> assertTrue(new ReactorBulkheadAspectExt().canHandleReturnType(Flux.class)), () -> assertTrue(new ReactorFallbackDecorator().supports(Flux.class)));
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-TIM-004 R4J-CVI-007
     * Depends-On: completionDecoratorSupportsStageFamily, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-7 */
    @Test public void timeLimiterExtensionAndFallbackAgreeOnMonoFamily() {
        assertAll(() -> assertTrue(new ReactorTimeLimiterAspectExt().canHandleReturnType(Mono.class)), () -> assertTrue(new ReactorFallbackDecorator().supports(Mono.class)));
    }

    /** Verifies: R4J-TIM-001 R4J-TIM-003 R4J-TIM-004 R4J-CVI-007
     * Depends-On: timerDefaultOrderIsLowest, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-7 */
    @Test public void timerExtensionAndFallbackAgreeOnFluxFamily() {
        assertAll(() -> assertTrue(new ReactorTimerAspectExt().canHandleReturnType(Flux.class)), () -> assertTrue(new ReactorFallbackDecorator().supports(Flux.class)));
    }

    /** Verifies: R4J-CFG-009 R4J-CVI-008
     * Depends-On: retryDefaultOrderIsLowestMinusFive, completionDecoratorSupportsStageFamily
     * Seam: lifecycle crossing / CVI-8 */
    @Test public void retryContextManagedAspectClosePreservesInterruptAndCompletedValue() throws Exception {
        CompletableFuture<String> completed = CompletableFuture.completedFuture("completed-retry-263");
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(RetryConfigurationProperties.class, RetryConfigurationProperties::new);
            context.registerBean(RetryRegistry.class, RetryRegistry::ofDefaults);
            context.registerBean(FallbackExecutor.class, OracleFixtures::fallbackExecutor);
            context.registerBean(SpelResolver.class, () -> (method, args, value) -> value);
            context.register(RetryConfiguration.class);
            context.refresh();
            RetryAspect aspect = context.getBean(RetryAspect.class);
            try {
                Thread.currentThread().interrupt();
                aspect.close();
                assertAll(() -> assertTrue(Thread.currentThread().isInterrupted()),
                    () -> assertEquals("completed-retry-263", completed.join()));
            } finally { Thread.interrupted(); }
        }
    }

    /** Verifies: R4J-CFG-009 R4J-CVI-008
     * Depends-On: timeLimiterDefaultOrderIsLowestMinusTwo, completionDecoratorSupportsStageFamily
     * Seam: lifecycle crossing / CVI-8 */
    @Test public void timeLimiterContextManagedAspectClosePreservesInterruptAndCompletedValue() throws Exception {
        CompletableFuture<String> completed = CompletableFuture.completedFuture("completed-time-269");
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean(TimeLimiterConfigurationProperties.class, TimeLimiterConfigurationProperties::new);
            context.registerBean(TimeLimiterRegistry.class, TimeLimiterRegistry::ofDefaults);
            context.registerBean(FallbackExecutor.class, OracleFixtures::fallbackExecutor);
            context.registerBean(SpelResolver.class, () -> (method, args, value) -> value);
            context.register(TimeLimiterConfiguration.class);
            context.refresh();
            TimeLimiterAspect aspect = context.getBean(TimeLimiterAspect.class);
            try {
                Thread.currentThread().interrupt();
                aspect.close();
                assertAll(() -> assertTrue(Thread.currentThread().isInterrupted()),
                    () -> assertEquals("completed-time-269", completed.join()));
            } finally { Thread.interrupted(); }
        }
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-CVI-007
     * Depends-On: proxyExtractorFindsAnnotatedInterface, resolverPreservesPlainText
     * Seam: protocol handoff / CVI-7 */
    @Test public void circuitBreakerExtensionHandlePreservesMonoAndValue() throws Throwable {
        CircuitBreaker component = CircuitBreakerRegistry.ofDefaults().circuitBreaker("reactor-cb-271");
        Object projection = new ReactorCircuitBreakerAspectExt().handle(OracleFixtures.proceedingJoinPoint(Mono.just("mono-value-271")), component, "reactorMethod271");
        assertAll(() -> assertInstanceOf(Mono.class, projection), () -> assertEquals("mono-value-271", ((Mono<?>) projection).block()));
    }

    /** Verifies: R4J-EXE-003 R4J-EXE-010 R4J-CVI-007
     * Depends-On: proxyExtractorFindsAnnotatedInterface, resolverPreservesPlainText
     * Seam: protocol handoff / CVI-7 */
    @Test public void retryExtensionHandlePreservesFluxAndValues() throws Throwable {
        Retry component = RetryRegistry.ofDefaults().retry("reactor-retry-277");
        Object projection = new ReactorRetryAspectExt().handle(OracleFixtures.proceedingJoinPoint(Flux.just("flux-a-277", "flux-b-277")), component, "reactorMethod277");
        assertAll(() -> assertInstanceOf(Flux.class, projection), () -> assertEquals(List.of("flux-a-277", "flux-b-277"), ((Flux<?>) projection).collectList().block()));
    }
}
