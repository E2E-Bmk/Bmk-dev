package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.NonPrintableStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;

/** Atomic tests for dump presentation settings. */
class DumpSettingsAtomicTest {

    private static Map<String, Object> sample() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("a", 1);
        data.put("b", List.of(1, 2));
        return data;
    }

    /** Verifies: Dump Settings and Presentation — block style lays out line by line. */
    @Test void blockStyleLaysOutLineByLine() {
        Dump dump = new Dump(DumpSettings.builder().setDefaultFlowStyle(FlowStyle.BLOCK).build());
        assertEquals("a: 1\nb:\n- 1\n- 2\n", dump.dumpToString(sample()));
    }

    /** Verifies: Dump Settings and Presentation — flow style renders inline. */
    @Test void flowStyleRendersInline() {
        Dump dump = new Dump(DumpSettings.builder().setDefaultFlowStyle(FlowStyle.FLOW).build());
        assertEquals("{a: 1, b: [1, 2]}\n", dump.dumpToString(sample()));
    }

    /** Verifies: Dump Settings and Presentation — explicit start and end markers. */
    @Test void explicitStartAndEndMarkers() {
        Dump dump = new Dump(DumpSettings.builder()
                .setExplicitStart(true).setExplicitEnd(true).build());
        assertEquals("--- {a: 1}\n...\n", dump.dumpToString(Map.of("a", 1)));
    }

    /** Verifies: Dump Settings and Presentation — canonical form with explicit tags. */
    @Test void canonicalFormWithExplicitTags() {
        Dump dump = new Dump(DumpSettings.builder().setCanonical(true).build());
        assertEquals("---\n!!map {\n  ? !!str \"a\"\n  : !!int \"1\",\n}\n",
                dump.dumpToString(Map.of("a", 1)));
    }

    /** Verifies: Dump Settings and Presentation — single-quoted scalar style. */
    @Test void singleQuotedScalarStyle() {
        Dump dump = new Dump(DumpSettings.builder()
                .setDefaultScalarStyle(ScalarStyle.SINGLE_QUOTED).build());
        assertEquals("'a': 'text'\n", dump.dumpToString(Map.of("a", "text")));
    }

    /** Verifies: Dump Settings and Presentation — double-quoted scalar style. */
    @Test void doubleQuotedScalarStyle() {
        Dump dump = new Dump(DumpSettings.builder()
                .setDefaultScalarStyle(ScalarStyle.DOUBLE_QUOTED).build());
        assertEquals("\"text\"\n", dump.dumpToString("text"));
    }

    /** Verifies: Dump Settings and Presentation — literal style for multi-line strings. */
    @Test void literalStyleForMultiLineStrings() {
        Dump dump = new Dump(DumpSettings.builder()
                .setDefaultScalarStyle(ScalarStyle.LITERAL).build());
        assertEquals("|-\n  line1\n  line2\n", dump.dumpToString("line1\nline2"));
    }

    /** Verifies: Dump Settings and Presentation — indent width applies to block nesting. */
    @Test void indentWidthAppliesToBlockNesting() {
        Map<String, Object> nested = new LinkedHashMap<>();
        nested.put("k", Map.of("x", 1));
        Dump two = new Dump(DumpSettings.builder().setDefaultFlowStyle(FlowStyle.BLOCK).build());
        assertEquals("k:\n  x: 1\n", two.dumpToString(nested));
        Dump four = new Dump(DumpSettings.builder()
                .setDefaultFlowStyle(FlowStyle.BLOCK).setIndent(4).build());
        assertEquals("k:\n    x: 1\n", four.dumpToString(nested));
    }

    /** Verifies: Dump Settings and Presentation — width wraps long plain scalars. */
    @Test void widthWrapsLongPlainScalars() {
        StringBuilder words = new StringBuilder();
        for (int i = 0; i < 12; i++) {
            words.append("word").append(i).append(' ');
        }
        Dump dump = new Dump(DumpSettings.builder().setWidth(20).build());
        assertEquals("word0 word1 word2 word3\n  word4 word5 word6 word7\n"
                + "  word8 word9 word10 word11\n", dump.dumpToString(words.toString().trim()));
    }

    /** Verifies: Dump Settings and Presentation — multi-line flow spreads flow collections. */
    @Test void multiLineFlowSpreadsFlowCollections() {
        Dump dump = new Dump(DumpSettings.builder().setMultiLineFlow(true).build());
        assertEquals("k: [\n  1,\n  2\n]\n", dump.dumpToString(Map.of("k", List.of(1, 2))));
    }

    /** Verifies: Dump Settings and Presentation — escape style renders escapes. */
    @Test void escapeStyleRendersEscapes() {
        Dump dump = new Dump(DumpSettings.builder()
                .setNonPrintableStyle(NonPrintableStyle.ESCAPE).build());
        assertEquals("\"hi\\x01there\"\n", dump.dumpToString("hi\u0001there"));
    }

    /** Verifies: Dump Settings and Presentation — binary style renders base64 block. */
    @Test void binaryStyleRendersBase64Block() {
        Dump dump = new Dump(DumpSettings.builder()
                .setNonPrintableStyle(NonPrintableStyle.BINARY).build());
        assertEquals("!!binary |-\n  aGkBdGhlcmU=\n", dump.dumpToString("hi\u0001there"));
    }

    /** Verifies: Dump Settings and Presentation — settings object is reusable. */
    @Test void settingsObjectIsReusable() {
        DumpSettings settings = DumpSettings.builder().setDefaultFlowStyle(FlowStyle.FLOW).build();
        Dump first = new Dump(settings);
        Dump second = new Dump(settings);
        assertEquals(first.dumpToString(sample()), second.dumpToString(sample()));
    }
}
