package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.StringReader;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import support.Yaml;

/** Atomic tests for loading documents into Java objects. */
class LoadScalarsAtomicTest {

    /** Verifies: Loading YAML Documents — mapping loads as insertion-ordered map. */
    @Test void mappingLoadsAsInsertionOrderedMap() {
        Object loaded = Yaml.load().loadFromString("a: 1\nb: text\nc: true");
        assertEquals(LinkedHashMap.class, loaded.getClass());
        Map<?, ?> map = (Map<?, ?>) loaded;
        assertEquals(List.of("a", "b", "c"), new ArrayList<>(map.keySet()));
    }

    /** Verifies: Loading YAML Documents — scalar values resolve to schema types. */
    @Test void scalarValuesResolveToSchemaTypes() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load().loadFromString("a: 1\nb: text\nc: true\ne: 3.5");
        assertEquals(1, map.get("a"));
        assertEquals("text", map.get("b"));
        assertEquals(Boolean.TRUE, map.get("c"));
        assertEquals(3.5, map.get("e"));
    }

    /** Verifies: Loading YAML Documents — sequence loads as list. */
    @Test void sequenceLoadsAsList() {
        Object loaded = Yaml.load().loadFromString("- 1\n- two\n- [a, b]");
        assertEquals(ArrayList.class, loaded.getClass());
        assertEquals(List.of(1, "two", List.of("a", "b")), loaded);
    }

    /** Verifies: Loading YAML Documents — nested structures load recursively. */
    @Test void nestedStructuresLoadRecursively() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load()
                .loadFromString("outer:\n  inner: [1, 2]\n  other: {k: v}");
        Map<?, ?> outer = (Map<?, ?>) map.get("outer");
        assertEquals(List.of(1, 2), outer.get("inner"));
        assertEquals(Map.of("k", "v"), outer.get("other"));
    }

    /** Verifies: Loading YAML Documents — empty input loads as null. */
    @Test void emptyInputLoadsAsNull() {
        assertNull(Yaml.load().loadFromString(""));
    }

    /** Verifies: Loading YAML Documents — plain scalar document loads as that scalar. */
    @Test void plainScalarDocumentLoadsAsScalar() {
        assertEquals("just text", Yaml.load().loadFromString("just text"));
    }

    /** Verifies: Loading YAML Documents — integer widening across ranges. */
    @Test void integerWideningAcrossRanges() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load().loadFromString(
                "small: 3\nlong: 9223372036854775807\nbig: 92233720368547758070");
        assertEquals(Integer.class, map.get("small").getClass());
        assertEquals(Long.class, map.get("long").getClass());
        assertEquals(BigInteger.class, map.get("big").getClass());
        assertEquals(new BigInteger("92233720368547758070"), map.get("big"));
    }

    /** Verifies: Loading YAML Documents — keys resolve like any scalar. */
    @Test void keysResolveLikeScalars() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load().loadFromString("1: one");
        assertEquals(Integer.class, map.keySet().iterator().next().getClass());
        assertEquals("one", map.get(1));
    }

    /** Verifies: Loading YAML Documents — reader and stream entry points agree. */
    @Test void readerAndStreamEntryPointsAgree() {
        assertEquals(Map.of("a", 1), Yaml.load().loadFromReader(new StringReader("a: 1")));
        assertEquals(Map.of("b", 2), Yaml.load().loadFromInputStream(
                new ByteArrayInputStream("b: 2".getBytes(StandardCharsets.UTF_8))));
    }

    /** Verifies: Loading YAML Documents — loadAll iterates documents in order. */
    @Test void loadAllIteratesDocumentsInOrder() {
        List<Object> all = new ArrayList<>();
        for (Object doc : Yaml.load().loadAllFromString("first\n--- !!str\nsecond\n---\n- 3")) {
            all.add(doc);
        }
        assertEquals(List.of("first", "second", List.of(3)), all);
    }

    /** Verifies: Loading YAML Documents — alias resolves to the anchored instance. */
    @Test void aliasResolvesToAnchoredInstance() {
        Map<?, ?> map = (Map<?, ?>) Yaml.load().loadFromString("base: &b {x: 1}\nref: *b");
        assertSame(map.get("base"), map.get("ref"));
        assertEquals(Map.of("x", 1), map.get("ref"));
    }
}
