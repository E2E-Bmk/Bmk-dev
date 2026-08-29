package atomic;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.library.Architectures;
import com.tngtech.archunit.library.dependencies.SliceIdentifier;
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition;
import org.junit.jupiter.api.Test;
import support.OracleSupport;
import support.fixture.cycle.alpha.Alpha;
import support.fixture.cycle.beta.Beta;

import static org.junit.jupiter.api.Assertions.*;

class AtomicArchitectureTest {
    /** Verifies: ARCH-LIB-001, ARCH-LIB-002, ARCH-LIB-015, ARCH-LIB-016 */
    @Test void configuredLayerRuleEvaluatesDefinedPackages() {
        ArchRule rule = Architectures.layeredArchitecture().consideringOnlyDependenciesInAnyPackage("support.fixture..")
                .layer("Web").definedBy("..web")
                .layer("Api").definedBy("..api")
                .whereLayer("Web").mayOnlyAccessLayers("Api");
        assertFalse(rule.evaluate(OracleSupport.graph()).hasViolation());
    }

    /** Verifies: ARCH-LIB-005, ARCH-ERR-006, ARCH-LIB-015, ARCH-LIB-016 */
    @Test void undefinedLayerNameRaisesArgumentError() {
        var architecture = Architectures.layeredArchitecture().consideringAllDependencies()
                .layer("Defined").definedBy("..service");
        assertThrows(IllegalArgumentException.class, () -> architecture.whereLayer("Missing"));
    }

    /** Verifies: ARCH-LIB-009, ARCH-LIB-017 */
    @Test void sliceIdentifierDistinguishesIncludedAndIgnoredClasses() {
        assertAll(() -> assertNotEquals(SliceIdentifier.of("one"), SliceIdentifier.of("two")),
                () -> assertNotEquals(SliceIdentifier.of("one"), SliceIdentifier.ignore()));
    }

    /** Verifies: ARCH-LIB-008, ARCH-LIB-010 */
    @Test void packageSlicesDetectDirectedCycle() {
        JavaClasses cycle = new com.tngtech.archunit.core.importer.ClassFileImporter().importClasses(Alpha.class, Beta.class);
        ArchRule rule = SlicesRuleDefinition.slices().matching("support.fixture.cycle.(*)..").should().beFreeOfCycles();
        assertTrue(rule.evaluate(cycle).hasViolation());
    }
}
