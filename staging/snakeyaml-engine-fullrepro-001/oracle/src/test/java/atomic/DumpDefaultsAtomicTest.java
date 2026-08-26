package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Yaml;

/** Atomic tests for the default dump projection. */
class DumpDefaultsAtomicTest {

    /** Verifies: Dumping Java Objects — auto style blocks the top level, flows nested. */
    @Test void autoStyleBlocksTopLevelFlowsNested() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("a", 1);
        data.put("b", List.of(1, 2));
        assertEquals("a: 1\nb: [1, 2]\n", Yaml.dump().dumpToString(data));
    }

    /** Verifies: Dumping Java Objects — top-level list renders in flow under auto. */
    @Test void topLevelListRendersFlow() {
        assertEquals("[1, two]\n", Yaml.dump().dumpToString(List.of(1, "two")));
    }

    /** Verifies: Dumping Java Objects — plain scalar renders with trailing newline. */
    @Test void plainScalarRendersWithNewline() {
        assertEquals("hello\n", Yaml.dump().dumpToString("hello"));
        assertEquals("2.5\n", Yaml.dump().dumpToString(2.5));
    }

    /** Verifies: Dumping Java Objects — nested mapping renders in flow under auto. */
    @Test void nestedMappingRendersFlow() {
        assertEquals("k: {x: 1}\n", Yaml.dump().dumpToString(Map.of("k", Map.of("x", 1))));
    }

    /** Verifies: Dumping Java Objects — null document renders as null text. */
    @Test void nullDocumentRendersNullText() {
        assertEquals("null\n", Yaml.dump().dumpToString(null));
    }

    /** Verifies: Dumping Java Objects — booleans, integers, floats render plain. */
    @Test void scalarTypesRenderPlain() {
        assertEquals("[true, 7, 2.5]\n", Yaml.dump().dumpToString(List.of(true, 7, 2.5)));
    }

    /** Verifies: Dumping Java Objects — boolean-shaped string is quoted. */
    @Test void booleanShapedStringIsQuoted() {
        assertEquals("'true'\n", Yaml.dump().dumpToString("true"));
    }

    /** Verifies: Dumping Java Objects — numeric-shaped string is quoted. */
    @Test void numericShapedStringIsQuoted() {
        assertEquals("'123'\n", Yaml.dump().dumpToString("123"));
    }

    /** Verifies: Dumping Java Objects — mapping-shaped string is quoted. */
    @Test void mappingShapedStringIsQuoted() {
        assertEquals("'a: b'\n", Yaml.dump().dumpToString("a: b"));
    }

    /** Verifies: Dumping Java Objects — empty string renders quoted empty. */
    @Test void emptyStringRendersQuotedEmpty() {
        assertEquals("''\n", Yaml.dump().dumpToString(""));
    }

    /** Verifies: Dumping Java Objects — big integers render plain. */
    @Test void bigIntegersRenderPlain() {
        assertEquals("92233720368547758070\n",
                Yaml.dump().dumpToString(new BigInteger("92233720368547758070")));
    }

    /** Verifies: Dumping Java Objects — non-string keys render through scalar rules. */
    @Test void nonStringKeysRenderThroughScalarRules() {
        Map<Object, Object> data = new LinkedHashMap<>();
        data.put(1, "one");
        data.put(true, "yes");
        assertEquals("{1: one, true: yes}\n", Yaml.dump().dumpToString(data));
    }

    /** Verifies: Dumping Java Objects — dumpAll marks documents after the first. */
    @Test void dumpAllMarksDocumentsAfterFirst() {
        assertEquals("one\n--- two\n--- three\n",
                Yaml.dump().dumpAllToString(List.<Object>of("one", "two", "three").iterator()));
    }
}
