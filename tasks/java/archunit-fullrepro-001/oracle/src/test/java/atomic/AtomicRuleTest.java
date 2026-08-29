package atomic;

import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.CompositeArchRule;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.EvaluationResult;
import com.tngtech.archunit.lang.Priority;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition;
import org.junit.jupiter.api.Test;
import support.OracleSupport;

import java.util.Collection;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class AtomicRuleTest {
    /** Verifies: ARCH-RULE-001, ARCH-RULE-011 */
    @Test void defaultRuleUsesMediumPriority() {
        ArchRule rule = ArchRuleDefinition.classes().should().resideInAPackage("support.fixture..");
        assertEquals(Priority.MEDIUM, rule.evaluate(OracleSupport.graph()).getPriority());
    }

    /** Verifies: ARCH-RULE-003, ARCH-RULE-006 */
    @Test void violatingRuleReportsViolationAndCheckFails() {
        ArchRule rule = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        JavaClasses graph = OracleSupport.graph();
        assertAll(() -> assertTrue(rule.evaluate(graph).hasViolation()),
                () -> assertThrows(AssertionError.class, () -> rule.check(graph)));
    }

    /** Verifies: ARCH-RULE-007 */
    @Test void asReplacesDescriptionWithoutChangingOutcome() {
        ArchRule original = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        ArchRule renamed = original.as("renamed rule");
        assertAll(() -> assertEquals("renamed rule", renamed.getDescription()),
                () -> assertEquals(original.evaluate(OracleSupport.graph()).hasViolation(),
                        renamed.evaluate(OracleSupport.graph()).hasViolation()));
    }

    /** Verifies: ARCH-RULE-007 */
    @Test void becauseChangesDescriptionWithoutChangingOutcome() {
        ArchRule original = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        ArchRule explained = original.because("service isolation matters");
        assertAll(() -> assertNotEquals(original.getDescription(), explained.getDescription()),
                () -> assertEquals(original.evaluate(OracleSupport.graph()).hasViolation(),
                        explained.evaluate(OracleSupport.graph()).hasViolation()));
    }

    /** Verifies: ARCH-RULE-008 */
    @Test void explicitlyAllowedEmptySelectionDoesNotViolate() {
        ArchRule rule = ArchRuleDefinition.classes().that().resideInAPackage("never.present..")
                .should().resideInAPackage("never.present..").allowEmptyShould(true);
        assertFalse(rule.evaluate(OracleSupport.graph()).hasViolation());
    }

    /** Verifies: ARCH-RULE-014 */
    @Test void simpleConditionEventsInvertViolationClassification() {
        var violated = SimpleConditionEvent.violated("subject", "violation");
        var satisfied = SimpleConditionEvent.satisfied("subject", "satisfied");
        assertAll(() -> assertTrue(violated.isViolation()), () -> assertFalse(satisfied.isViolation()),
                () -> assertFalse(violated.invert().isViolation()), () -> assertTrue(satisfied.invert().isViolation()));
    }

    /** Verifies: ARCH-RULE-012, ARCH-RULE-015, ARCH-RULE-017, ARCH-RULE-019, ARCH-RULE-020 */
    @Test void customConditionLifecycleAndCompositeEvaluationAreObservable() {
        AtomicInteger init = new AtomicInteger();
        AtomicInteger checks = new AtomicInteger();
        AtomicInteger finish = new AtomicInteger();
        ArchCondition<JavaClass> condition = new ArchCondition<>("count lifecycle") {
            @Override public void init(Collection<JavaClass> allObjectsToTest) { init.incrementAndGet(); }
            @Override public void check(JavaClass item, ConditionEvents events) { checks.incrementAndGet(); events.add(SimpleConditionEvent.satisfied(item, item.getName())); }
            @Override public void finish(ConditionEvents events) { finish.incrementAndGet(); }
        };
        ArchRule first = ArchRuleDefinition.classes().should(condition);
        ArchRule second = ArchRuleDefinition.classes().should().resideInAPackage("support.fixture..");
        EvaluationResult result = CompositeArchRule.of(first).and(second).evaluate(OracleSupport.graph());
        assertAll(() -> assertFalse(result.hasViolation()), () -> assertEquals(1, init.get()),
                () -> assertEquals(OracleSupport.graph().size(), checks.get()), () -> assertEquals(1, finish.get()));
    }
}
