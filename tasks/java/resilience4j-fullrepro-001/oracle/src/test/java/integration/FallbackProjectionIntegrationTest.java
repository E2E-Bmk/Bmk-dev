package integration;

import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerRegistry;
import io.github.resilience4j.core.functions.CheckedSupplier;
import io.github.resilience4j.spring6.fallback.CompletionStageFallbackDecorator;
import io.github.resilience4j.spring6.fallback.DefaultFallbackDecorator;
import io.github.resilience4j.spring6.fallback.ReactorFallbackDecorator;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.CompletionStage;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import support.OracleFixtures;

import static org.junit.jupiter.api.Assertions.*;

/** Cross-view tests joining primary policy failures to fallback projections. */
public class FallbackProjectionIntegrationTest {
    /** Verifies: R4J-AOP-008 R4J-FAL-008 R4J-CVI-003
     * Depends-On: nearestExceptionOverloadWins, argumentAwareFallbackReceivesOriginalArgument
     * Seam: error propagation / CVI-3 */
    @Test public void synchronousFallbackReturnsRecoveryWhileCircuitBreakerCountsFailure() throws Throwable {
        CircuitBreaker component = CircuitBreakerRegistry.ofDefaults().circuitBreaker("fallback-cb-191");
        CheckedSupplier<Object> primary = CircuitBreaker.decorateCheckedSupplier(component, () -> { throw new IllegalArgumentException("primary-191"); });
        Object value = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("recover"), primary).get();
        assertAll(() -> assertEquals("specific:quartz-481", value), () -> assertEquals(1, component.getMetrics().getNumberOfFailedCalls()));
    }

    /** Verifies: R4J-EXE-001 R4J-FAL-005 R4J-CVI-003
     * Depends-On: runtimeOverloadWinsForDifferentRuntimeSubtype, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-3 */
    @Test public void runtimeSpecificRecoveryAgreesWithRecordedPrimaryFailure() throws Throwable {
        CircuitBreaker component = CircuitBreakerRegistry.ofDefaults().circuitBreaker("fallback-cb-193");
        CheckedSupplier<Object> primary = CircuitBreaker.decorateCheckedSupplier(component, () -> { throw new IllegalStateException("primary-193"); });
        Object value = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("recover"), primary).get();
        assertAll(() -> assertEquals("runtime:quartz-481", value), () -> assertEquals(1, component.getMetrics().getNumberOfFailedCalls()));
    }

    /** Verifies: R4J-AOP-008 R4J-FAL-008 R4J-CVI-003
     * Depends-On: throwableOnlyFallbackReceivesOnlyFailure, defaultDecoratorSupportsOrdinaryFamily
     * Seam: error propagation / CVI-3 */
    @Test public void throwableOnlyRecoveryDoesNotEraseComponentFailureAccounting() throws Throwable {
        CircuitBreaker component = CircuitBreakerRegistry.ofDefaults().circuitBreaker("fallback-cb-197");
        CheckedSupplier<Object> primary = CircuitBreaker.decorateCheckedSupplier(component, () -> { throw new IllegalStateException("primary-197"); });
        Object value = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("throwableOnly"), primary).get();
        assertAll(() -> assertEquals("only:IllegalStateException", value), () -> assertEquals(1, component.getMetrics().getNumberOfFailedCalls()));
    }

    /** Verifies: R4J-TIM-002 R4J-FAL-005 R4J-CVI-003
     * Depends-On: nearestExceptionOverloadWins, timerDefaultOrderIsLowest
     * Seam: state consistency / CVI-3 */
    @Test public void selectedRecoveryAndFailureMetricRemainConsistentAcrossCalls() throws Throwable {
        CircuitBreaker component = CircuitBreakerRegistry.ofDefaults().circuitBreaker("fallback-cb-199");
        CheckedSupplier<Object> one = CircuitBreaker.decorateCheckedSupplier(component, () -> { throw new IllegalArgumentException("primary-199a"); });
        CheckedSupplier<Object> two = CircuitBreaker.decorateCheckedSupplier(component, () -> { throw new IllegalArgumentException("primary-199b"); });
        Object first = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("recover"), one).get();
        Object second = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("recover"), two).get();
        assertAll(() -> assertEquals(first, second), () -> assertEquals(2, component.getMetrics().getNumberOfFailedCalls()));
    }

    /** Verifies: R4J-EXE-002 R4J-FAL-010 R4J-CVI-004
     * Depends-On: completionDecoratorSupportsStageFamily, argumentAwareFallbackReceivesOriginalArgument
     * Seam: protocol handoff / CVI-4 */
    @Test public void exceptionalStagePreservesFamilyAndCompletesWithFallback() throws Throwable {
        CheckedSupplier<Object> decorated = new CompletionStageFallbackDecorator().decorate(OracleFixtures.stageFallback("stageRecover"),
            () -> CompletableFuture.failedFuture(new IllegalArgumentException("stage-primary-211")));
        Object projection = decorated.get();
        assertAll(() -> assertInstanceOf(CompletionStage.class, projection), () -> assertEquals("stage-fallback:quartz-481", ((CompletionStage<?>) projection).toCompletableFuture().join()));
    }

    /** Verifies: R4J-STA-003 R4J-FAL-010 R4J-CVI-004
     * Depends-On: completionDecoratorSupportsStageFamily, fallbackReportsOriginalReturnType
     * Seam: lifecycle crossing / CVI-4 */
    @Test public void incompleteStageRemainsIncompleteUntilTerminalFailure() throws Throwable {
        CompletableFuture<String> primary = new CompletableFuture<>();
        CompletionStage<?> projection = (CompletionStage<?>) new CompletionStageFallbackDecorator().decorate(OracleFixtures.stageFallback("stageRecover"), () -> primary).get();
        assertFalse(projection.toCompletableFuture().isDone());
        primary.completeExceptionally(new IllegalArgumentException("stage-primary-223"));
        assertEquals("stage-fallback:quartz-481", projection.toCompletableFuture().join());
    }

    /** Verifies: R4J-FAL-010 R4J-CVI-004
     * Depends-On: completionDecoratorSupportsStageFamily, nearestExceptionOverloadWins
     * Seam: error propagation / CVI-4 */
    @Test public void asynchronousFallbackFailureStaysTerminalInStageFamily() throws Throwable {
        CompletionStage<?> projection = (CompletionStage<?>) new CompletionStageFallbackDecorator().decorate(OracleFixtures.stageFallback("stageExplode"),
            () -> CompletableFuture.failedFuture(new IllegalArgumentException("stage-primary-227"))).get();
        CompletionException terminal = assertThrows(CompletionException.class, () -> projection.toCompletableFuture().join());
        assertInstanceOf(UnsupportedOperationException.class, terminal.getCause());
    }

    /** Verifies: R4J-EXE-010 R4J-FAL-011 R4J-CVI-004
     * Depends-On: nearestExceptionOverloadWins, defaultDecoratorSupportsOrdinaryFamily
     * Seam: protocol handoff / CVI-4 */
    @Test public void reactorFailurePreservesMonoFamilyAndCompletesWithFallback() throws Throwable {
        Object projection = new ReactorFallbackDecorator().decorate(OracleFixtures.monoFallback("monoRecover"),
            () -> Mono.error(new IllegalArgumentException("mono-primary-229"))).get();
        assertAll(() -> assertInstanceOf(Mono.class, projection), () -> assertEquals("mono-fallback:quartz-481", ((Mono<?>) projection).block()));
    }

    /** Verifies: R4J-FAL-006
     * Depends-On: unmatchedFailureIsRethrownByIdentity, defaultDecoratorSupportsOrdinaryFamily
     * Seam: error propagation */
    @Test public void defaultProjectionRethrowsUnacceptedPrimaryFailureByIdentity() throws Exception {
        IllegalArgumentException primaryFailure = new IllegalArgumentException("identity-233");
        CheckedSupplier<Object> projection = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("stateOnly"), () -> { throw primaryFailure; });
        assertSame(primaryFailure, assertThrows(IllegalArgumentException.class, projection::get));
    }

    /** Verifies: R4J-FAL-009
     * Depends-On: defaultDecoratorSupportsOrdinaryFamily, nearestExceptionOverloadWins
     * Seam: error propagation */
    @Test public void defaultProjectionPropagatesFallbackFailureTypeDirectly() throws Exception {
        CheckedSupplier<Object> projection = new DefaultFallbackDecorator().decorate(OracleFixtures.stringFallback("explode"), () -> { throw new IllegalArgumentException("primary-239"); });
        assertThrows(UnsupportedOperationException.class, projection::get);
    }

    /** Verifies: R4J-FAL-010 R4J-FAL-009
     * Depends-On: completionDecoratorSupportsStageFamily, nearestExceptionOverloadWins
     * Seam: error propagation */
    @Test public void stageProjectionCarriesFallbackFailureAsTerminalCause() throws Throwable {
        CompletionStage<?> projection = (CompletionStage<?>) new CompletionStageFallbackDecorator().decorate(OracleFixtures.stageFallback("stageExplode"),
            () -> CompletableFuture.failedFuture(new IllegalArgumentException("primary-241"))).get();
        assertInstanceOf(UnsupportedOperationException.class, assertThrows(CompletionException.class, () -> projection.toCompletableFuture().join()).getCause());
    }

    /** Verifies: R4J-FAL-004 R4J-AOP-008
     * Depends-On: missingFallbackNameIsRejected, incompatibleFallbackReturnTypeIsRejected
     * Seam: config interaction */
    @Test public void invalidFallbackConfigurationCannotBuildProjection() {
        assertThrows(NoSuchMethodException.class, () -> OracleFixtures.stringFallback("missing-projection-251"));
    }
}
