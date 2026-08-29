package atomic;

import io.github.resilience4j.spring6.fallback.CompletionStageFallbackDecorator;
import io.github.resilience4j.spring6.fallback.DefaultFallbackDecorator;
import io.github.resilience4j.spring6.fallback.FallbackMethod;
import java.util.concurrent.CompletionStage;
import org.junit.jupiter.api.Test;
import support.OracleFixtures;

import static org.junit.jupiter.api.Assertions.*;

/** Atomic contracts for fallback discovery, selection, and decorators. */
public class FallbackAtomicTest {
    /** Verifies: R4J-FAL-002 */
    @Test public void fallbackReportsOriginalReturnType() throws Exception {
        assertEquals(String.class, OracleFixtures.stringFallback("recover").getReturnType());
    }

    /** Verifies: R4J-FAL-005 */
    @Test public void nearestExceptionOverloadWins() throws Throwable {
        assertEquals("specific:quartz-481", OracleFixtures.stringFallback("recover").fallback(new IllegalArgumentException("fault-67")));
    }

    /** Verifies: R4J-FAL-005 */
    @Test public void runtimeOverloadWinsForDifferentRuntimeSubtype() throws Throwable {
        assertEquals("runtime:quartz-481", OracleFixtures.stringFallback("recover").fallback(new IllegalStateException("fault-71")));
    }

    /** Verifies: R4J-FAL-008 */
    @Test public void throwableOnlyFallbackReceivesOnlyFailure() throws Throwable {
        assertEquals("only:IllegalStateException", OracleFixtures.stringFallback("throwableOnly").fallback(new IllegalStateException("fault-73")));
    }

    /** Verifies: R4J-FAL-008 */
    @Test public void argumentAwareFallbackReceivesOriginalArgument() throws Throwable {
        assertEquals("specific:quartz-481", OracleFixtures.stringFallback("recover").fallback(new IllegalArgumentException("fault-79")));
    }

    /** Verifies: R4J-FAL-006 */
    @Test public void unmatchedFailureIsRethrownByIdentity() throws Exception {
        IllegalArgumentException failure = new IllegalArgumentException("identity-83");
        Throwable observed = assertThrows(IllegalArgumentException.class, () -> OracleFixtures.stringFallback("stateOnly").fallback(failure));
        assertSame(failure, observed);
    }

    /** Verifies: R4J-FAL-004 */
    @Test public void missingFallbackNameIsRejected() throws Exception {
        assertThrows(NoSuchMethodException.class, () -> OracleFixtures.stringFallback("absentRecovery887"));
    }

    /** Verifies: R4J-FAL-004 */
    @Test public void incompatibleFallbackReturnTypeIsRejected() throws Exception {
        assertThrows(NoSuchMethodException.class, () -> OracleFixtures.stringFallback("wrongReturn"));
    }

    /** Verifies: R4J-FAL-007 */
    @Test public void duplicateExceptionCoverageIsRejected() throws Exception {
        assertThrows(IllegalStateException.class, () -> OracleFixtures.stringFallback("duplicate"));
    }

    /** Verifies: R4J-FAL-010 R4J-TIM-004 */
    @Test public void completionDecoratorSupportsStageFamily() {
        assertTrue(new CompletionStageFallbackDecorator().supports(CompletionStage.class));
    }

    /** Verifies: R4J-TIM-004 */
    @Test public void defaultDecoratorSupportsOrdinaryFamily() {
        assertTrue(new DefaultFallbackDecorator().supports(String.class));
    }
}
