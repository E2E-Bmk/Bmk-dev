package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.univocity.parsers.tsv.TsvParser;
import com.univocity.parsers.tsv.TsvParserSettings;
import com.univocity.parsers.tsv.TsvWriter;
import com.univocity.parsers.tsv.TsvWriterSettings;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** TSV dialect: tab separation and backslash escape sequences. */
class TsvAtomicTest {

    /**
     * Verifies: TSV Format — rows split on tabs.
     */
    @Test
    void rowsSplitOnTabs() {
        List<String[]> rows = new TsvParser(new TsvParserSettings())
                .parseAll(new StringReader("a\tb\nc\td\n"));
        assertEquals(List.of(Csv.row("a", "b"), Csv.row("c", "d")), Csv.lists(rows));
    }

    /**
     * Verifies: TSV Format — the two-character sequence backslash-t decodes to
     * a real tab inside a value.
     */
    @Test
    void escapedTabDecodes() {
        List<String[]> rows = new TsvParser(new TsvParserSettings())
                .parseAll(new StringReader("a\tb\\tc\n"));
        assertEquals("b\tc", rows.get(0)[1]);
    }

    /**
     * Verifies: TSV Format — the two-character sequence backslash-n decodes to
     * a real line break inside a value.
     */
    @Test
    void escapedNewlineDecodes() {
        List<String[]> rows = new TsvParser(new TsvParserSettings())
                .parseAll(new StringReader("a\\nb\tc\n"));
        assertEquals("a\nb", rows.get(0)[0]);
    }

    /**
     * Verifies: TSV Format — the writer encodes real tabs and line breaks as
     * escape sequences, keeping one physical line per record.
     */
    @Test
    void writerEncodesTabAndNewline() {
        StringWriter out = new StringWriter();
        TsvWriter writer = new TsvWriter(out, new TsvWriterSettings());
        writer.writeRow("a\tb", "line1\nline2");
        writer.close();
        assertEquals("a\\tb\tline1\\nline2\n", out.toString());
    }

    /**
     * Verifies: TSV Format — writeHeaders and writeRow behave as in CSV over
     * the tab dialect.
     */
    @Test
    void headersAndRowsOverTabDialect() {
        StringWriter out = new StringWriter();
        TsvWriter writer = new TsvWriter(out, new TsvWriterSettings());
        writer.writeHeaders("h1", "h2");
        writer.writeRow("v1", "v2");
        writer.close();
        assertEquals("h1\th2\nv1\tv2\n", out.toString());
    }
}
