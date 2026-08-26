package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import com.univocity.parsers.csv.CsvWriter;
import com.univocity.parsers.csv.CsvWriterSettings;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Session lifecycle: fresh parser state, writer accumulation, settings capture. */
class SessionsAtomicTest {

    /**
     * Verifies: State Model — a parser can run any number of sessions; each
     * parseAll call starts fresh state.
     */
    @Test
    void parserRunsMultipleFreshSessions() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        List<String[]> first = parser.parseAll(new StringReader("a,b\n"));
        List<String[]> second = parser.parseAll(new StringReader("c,d\ne,f\n"));
        assertEquals(List.of(Csv.row("a", "b")), Csv.lists(first));
        assertEquals(List.of(Csv.row("c", "d"), Csv.row("e", "f")), Csv.lists(second));
        assertEquals(2, parser.getContext().currentRecord());
    }

    /**
     * Verifies: State Model — writers accumulate output on their target
     * writer and close completes the document.
     */
    @Test
    void writerAccumulatesUntilClose() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeRow("1", "2");
        writer.writeRow("3", "4");
        writer.close();
        assertEquals("1,2\n3,4\n", out.toString());
    }

    /**
     * Verifies: State Model — a parser captures its settings at construction;
     * mutating the settings object affects only parsers constructed
     * afterwards, never one already built.
     */
    @Test
    void settingsCapturedAtConstruction() {
        CsvParserSettings settings = new CsvParserSettings();
        CsvParser early = new CsvParser(settings);
        assertNull(early.parseAll(new StringReader("x,,y\n")).get(0)[1]);

        settings.setNullValue("N/A");
        CsvParser late = new CsvParser(settings);
        assertEquals("N/A", late.parseAll(new StringReader("x,,y\n")).get(0)[1]);
        assertNull(early.parseAll(new StringReader("x,,y\n")).get(0)[1]);
    }
}
