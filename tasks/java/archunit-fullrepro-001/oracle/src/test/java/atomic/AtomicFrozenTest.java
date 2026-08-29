package atomic;

import com.tngtech.archunit.ArchConfiguration;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.library.freeze.FreezingArchRule;
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import support.InMemoryViolationStore;
import support.OracleSupport;

import static org.junit.jupiter.api.Assertions.*;

class AtomicFrozenTest {
    @AfterEach void resetConfiguration() {
        ArchConfiguration.get().reset();
    }

    private static void permitCreationAndUpdates() {
        ArchConfiguration.get().setProperty("freeze.store.default.allowStoreCreation", "true");
        ArchConfiguration.get().setProperty("freeze.store.default.allowStoreUpdate", "true");
    }

    /** Verifies: ARCH-FRZ-001, ARCH-RULE-007, ARCH-STATE-001 */
    @Test void frozenRulePreservesPriorityAndDescription() {
        permitCreationAndUpdates();
        ArchRule rule = ArchRuleDefinition.noClasses().should().resideInAPackage("..service").as("service boundary");
        FreezingArchRule frozen = FreezingArchRule.freeze(rule).persistIn(new InMemoryViolationStore());
        assertAll(() -> assertEquals(rule.getDescription(), frozen.getDescription()),
                () -> assertEquals(rule.evaluate(OracleSupport.graph()).getPriority(), frozen.evaluate(OracleSupport.graph()).getPriority()));
    }

    /** Verifies: ARCH-FRZ-002, ARCH-FRZ-006, ARCH-FRZ-007, ARCH-STATE-001 */
    @Test void firstEvaluationPersistsBaselineAndSuppressesKnownViolations() {
        permitCreationAndUpdates();
        InMemoryViolationStore store = new InMemoryViolationStore();
        ArchRule wrapped = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        FreezingArchRule frozen = FreezingArchRule.freeze(wrapped).persistIn(store);
        assertAll(() -> assertFalse(frozen.evaluate(OracleSupport.graph()).hasViolation()),
                () -> assertEquals(1, store.saves), () -> assertTrue(store.contains(wrapped)));
    }

    /** Verifies: ARCH-FRZ-003, ARCH-FRZ-006, ARCH-STATE-001 */
    @Test void repeatedEvaluationUsesStoredBaseline() {
        permitCreationAndUpdates();
        InMemoryViolationStore store = new InMemoryViolationStore();
        FreezingArchRule frozen = FreezingArchRule.freeze(ArchRuleDefinition.noClasses().should().resideInAPackage("..service")).persistIn(store);
        frozen.evaluate(OracleSupport.graph());
        int savesAfterFirst = store.saves;
        assertAll(() -> assertFalse(frozen.evaluate(OracleSupport.graph()).hasViolation()),
                () -> assertEquals(savesAfterFirst, store.saves));
    }
}
