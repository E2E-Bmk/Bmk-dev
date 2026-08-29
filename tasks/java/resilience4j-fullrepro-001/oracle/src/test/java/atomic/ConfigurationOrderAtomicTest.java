package atomic;

import io.github.resilience4j.spring6.bulkhead.configure.BulkheadConfigurationProperties;
import io.github.resilience4j.spring6.circuitbreaker.configure.CircuitBreakerConfigurationProperties;
import io.github.resilience4j.spring6.micrometer.configure.TimerConfigurationProperties;
import io.github.resilience4j.spring6.ratelimiter.configure.RateLimiterConfigurationProperties;
import io.github.resilience4j.spring6.retry.configure.RetryConfigurationProperties;
import io.github.resilience4j.spring6.timelimiter.configure.TimeLimiterConfigurationProperties;
import org.junit.jupiter.api.Test;
import org.springframework.core.Ordered;

import static org.junit.jupiter.api.Assertions.assertEquals;

/** Atomic contracts for default and configured aspect precedence. */
public class ConfigurationOrderAtomicTest {
    /** Verifies: R4J-CFG-007 */
    @Test public void retryDefaultOrderIsLowestMinusFive() {
        assertEquals(Ordered.LOWEST_PRECEDENCE - 5, new RetryConfigurationProperties().getRetryAspectOrder());
    }

    /** Verifies: R4J-CFG-007 */
    @Test public void circuitBreakerDefaultOrderIsLowestMinusFour() {
        assertEquals(Ordered.LOWEST_PRECEDENCE - 4, new CircuitBreakerConfigurationProperties().getCircuitBreakerAspectOrder());
    }

    /** Verifies: R4J-CFG-007 */
    @Test public void rateLimiterDefaultOrderIsLowestMinusThree() {
        assertEquals(Ordered.LOWEST_PRECEDENCE - 3, new RateLimiterConfigurationProperties().getRateLimiterAspectOrder());
    }

    /** Verifies: R4J-CFG-007 */
    @Test public void timeLimiterDefaultOrderIsLowestMinusTwo() {
        assertEquals(Ordered.LOWEST_PRECEDENCE - 2, new TimeLimiterConfigurationProperties().getTimeLimiterAspectOrder());
    }

    /** Verifies: R4J-CFG-007 */
    @Test public void bulkheadDefaultOrderIsLowestMinusOne() {
        assertEquals(Ordered.LOWEST_PRECEDENCE - 1, new BulkheadConfigurationProperties().getBulkheadAspectOrder());
    }

    /** Verifies: R4J-CFG-007 R4J-TIM-001 */
    @Test public void timerDefaultOrderIsLowest() {
        assertEquals(Ordered.LOWEST_PRECEDENCE, new TimerConfigurationProperties().getTimerAspectOrder());
    }

    /** Verifies: R4J-CFG-008 */
    @Test public void retryConfiguredOrderRoundTrips() {
        RetryConfigurationProperties p = new RetryConfigurationProperties(); p.setRetryAspectOrder(1411); assertEquals(1411, p.getRetryAspectOrder());
    }

    /** Verifies: R4J-CFG-008 */
    @Test public void circuitBreakerConfiguredOrderRoundTrips() {
        CircuitBreakerConfigurationProperties p = new CircuitBreakerConfigurationProperties(); p.setCircuitBreakerAspectOrder(1423); assertEquals(1423, p.getCircuitBreakerAspectOrder());
    }

    /** Verifies: R4J-CFG-008 */
    @Test public void rateLimiterConfiguredOrderRoundTrips() {
        RateLimiterConfigurationProperties p = new RateLimiterConfigurationProperties(); p.setRateLimiterAspectOrder(1433); assertEquals(1433, p.getRateLimiterAspectOrder());
    }

    /** Verifies: R4J-CFG-008 */
    @Test public void timeLimiterConfiguredOrderRoundTrips() {
        TimeLimiterConfigurationProperties p = new TimeLimiterConfigurationProperties(); p.setTimeLimiterAspectOrder(1447); assertEquals(1447, p.getTimeLimiterAspectOrder());
    }

    /** Verifies: R4J-CFG-008 */
    @Test public void bulkheadConfiguredOrderRoundTrips() {
        BulkheadConfigurationProperties p = new BulkheadConfigurationProperties(); p.setBulkheadAspectOrder(1451); assertEquals(1451, p.getBulkheadAspectOrder());
    }

    /** Verifies: R4J-CFG-008 R4J-TIM-001 */
    @Test public void timerConfiguredOrderRoundTrips() {
        TimerConfigurationProperties p = new TimerConfigurationProperties(); p.setTimerAspectOrder(1459); assertEquals(1459, p.getTimerAspectOrder());
    }
}
