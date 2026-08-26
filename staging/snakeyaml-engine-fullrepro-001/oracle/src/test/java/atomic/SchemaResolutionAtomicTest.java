package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.schema.CoreSchema;
import support.Yaml;

/** Atomic tests for scalar resolution under the two schemas in scope. */
class SchemaResolutionAtomicTest {

    private static Load core() {
        return new Load(LoadSettings.builder().setSchema(new CoreSchema()).build());
    }

    /** Verifies: Schemas and Scalar Resolution — JSON schema resolves the null literal. */
    @Test void jsonSchemaResolvesNullLiteral() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load().loadFromString("k: null");
        assertTrue(map.containsKey("k"));
        assertNull(map.get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — JSON schema resolves empty value to null. */
    @Test void jsonSchemaResolvesEmptyValueToNull() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load().loadFromString("k:");
        assertTrue(map.containsKey("k"));
        assertNull(map.get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — tilde stays a string under JSON schema. */
    @Test void tildeStaysStringUnderJsonSchema() {
        assertEquals("~", ((Map<?, ?>) Yaml.load().loadFromString("k: ~")).get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — YAML 1.1 booleans stay strings. */
    @Test void yamlOneOneBooleansStayStrings() {
        assertEquals("yes", ((Map<?, ?>) Yaml.load().loadFromString("k: yes")).get("k"));
        assertEquals("yes", ((Map<?, ?>) core().loadFromString("k: yes")).get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — hex stays string under JSON schema. */
    @Test void hexStaysStringUnderJsonSchema() {
        assertEquals("0x1A", ((Map<?, ?>) Yaml.load().loadFromString("k: 0x1A")).get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — core schema resolves tilde and empty to null. */
    @Test void coreSchemaResolvesTildeToNull() {
        assertNull(((Map<?, ?>) core().loadFromString("k: ~")).get("k"));
        assertNull(((Map<?, ?>) core().loadFromString("k:")).get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — core schema resolves hex and octal integers. */
    @Test void coreSchemaResolvesHexAndOctal() {
        Map<?, ?> map = (Map<?, ?>) core().loadFromString("hex: 0x1A\noct: 0o17");
        assertEquals(26, map.get("hex"));
        assertEquals(15, map.get("oct"));
    }

    /** Verifies: Schemas and Scalar Resolution — core schema resolves exponent and inf floats. */
    @Test void coreSchemaResolvesExponentAndInfinity() {
        Map<?, ?> map = (Map<?, ?>) core().loadFromString("exp: 1e3\ninf: .inf");
        assertEquals(1000.0, map.get("exp"));
        assertEquals(Double.POSITIVE_INFINITY, map.get("inf"));
    }

    /** Verifies: Schemas and Scalar Resolution — core schema resolves case-variant booleans. */
    @Test void coreSchemaResolvesCaseVariantBooleans() {
        assertEquals(Boolean.TRUE, ((Map<?, ?>) core().loadFromString("k: True")).get("k"));
    }

    /** Verifies: Schemas and Scalar Resolution — date-like scalars stay strings in both schemas. */
    @Test void dateLikeScalarsStayStrings() {
        assertEquals(String.class,
                ((Map<?, ?>) Yaml.load().loadFromString("d: 2020-01-01")).get("d").getClass());
        assertEquals(String.class,
                ((Map<?, ?>) core().loadFromString("d: 2020-01-01")).get("d").getClass());
    }
}
