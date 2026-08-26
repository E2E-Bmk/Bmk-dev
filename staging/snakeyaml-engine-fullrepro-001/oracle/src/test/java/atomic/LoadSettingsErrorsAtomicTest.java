package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.exceptions.DuplicateKeyException;
import org.snakeyaml.engine.v2.exceptions.MarkedYamlEngineException;
import org.snakeyaml.engine.v2.exceptions.ParserException;
import org.snakeyaml.engine.v2.exceptions.ScannerException;
import org.snakeyaml.engine.v2.exceptions.YamlEngineException;
import support.Yaml;

/** Atomic tests for load settings and error semantics. */
class LoadSettingsErrorsAtomicTest {

    /** Verifies: Error Semantics — duplicate key raises under default settings. */
    @Test void duplicateKeyRaisesByDefault() {
        assertThrows(DuplicateKeyException.class,
                () -> Yaml.load().loadFromString("a: 1\na: 2"));
    }

    /** Verifies: Loading YAML Documents — allowed duplicate keys keep the last value. */
    @Test void allowedDuplicateKeysKeepLastValue() {
        Load lenient = new Load(LoadSettings.builder().setAllowDuplicateKeys(true).build());
        assertEquals(Map.of("a", 2), lenient.loadFromString("a: 1\na: 2"));
    }

    /** Verifies: Error Semantics — unclosed flow collection raises ParserException. */
    @Test void unclosedFlowCollectionRaisesParserException() {
        assertThrows(ParserException.class, () -> Yaml.load().loadFromString("a: [1, 2"));
    }

    /** Verifies: Error Semantics — reserved indicator raises ScannerException. */
    @Test void reservedIndicatorRaisesScannerException() {
        assertThrows(ScannerException.class, () -> Yaml.load().loadFromString("key: @bad"));
    }

    /** Verifies: Error Semantics — explicit tag on unconstructible scalar raises. */
    @Test void explicitTagOnUnconstructibleScalarRaises() {
        assertThrows(YamlEngineException.class,
                () -> Yaml.load().loadFromString("!!int notanint"));
    }

    /** Verifies: Loading YAML Documents — alias budget enforces the configured maximum. */
    @Test void aliasBudgetEnforcesConfiguredMaximum() {
        Load limited = new Load(LoadSettings.builder().setMaxAliasesForCollections(3).build());
        assertEquals(Map.of("a", java.util.List.of(1),
                        "b", java.util.List.of(java.util.List.of(1), java.util.List.of(1),
                                java.util.List.of(1))),
                limited.loadFromString("a: &a [1]\nb: [*a, *a, *a]"));
        YamlEngineException ex = assertThrows(YamlEngineException.class,
                () -> limited.loadFromString("a: &a [1]\nb: [*a, *a, *a, *a]"));
        assertTrue(ex.getMessage().contains("3"));
    }

    /** Verifies: Load Settings — label appears in parse-error messages. */
    @Test void labelAppearsInParseErrorMessages() {
        Load labeled = new Load(LoadSettings.builder().setLabel("my-config").build());
        MarkedYamlEngineException ex = assertThrows(MarkedYamlEngineException.class,
                () -> labeled.loadFromString("a: [1"));
        assertTrue(ex.getMessage().contains("my-config"));
    }

    /** Verifies: Error Semantics — problem marks carry zero-based line numbers. */
    @Test void problemMarksCarryZeroBasedLines() {
        MarkedYamlEngineException ex = assertThrows(MarkedYamlEngineException.class,
                () -> Yaml.load().loadFromString("a: [1,\n  2"));
        assertTrue(ex.getProblemMark().isPresent());
        assertEquals(1, ex.getProblemMark().get().getLine());
    }

    /** Verifies: Error Semantics — marked exceptions extend the engine root. */
    @Test void markedExceptionsExtendEngineRoot() {
        MarkedYamlEngineException ex = assertThrows(MarkedYamlEngineException.class,
                () -> Yaml.load().loadFromString("a: [1, 2"));
        assertTrue(ex instanceof YamlEngineException);
        assertTrue(ex instanceof ParserException);
    }

    /** Verifies: Error Semantics — duplicate key exception is a marked exception. */
    @Test void duplicateKeyExceptionIsMarked() {
        DuplicateKeyException ex = assertThrows(DuplicateKeyException.class,
                () -> Yaml.load().loadFromString("a: 1\na: 2"));
        assertTrue(ex instanceof MarkedYamlEngineException);
    }
}
