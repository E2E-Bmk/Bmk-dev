package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.univocity.parsers.common.TextParsingException;
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import java.io.StringReader;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Null/empty substitutions and parsing safety limits. */
class ValuesAndLimitsAtomicTest {

    /**
     * Verifies: CSV Parsing — an unquoted zero-length value parses as the
     * configured null value.
     */
    @Test
    void nullValueSubstitutesAbsentValues() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setNullValue("N/A");
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader("a,,b\n"));
        assertEquals(Csv.row("a", "N/A", "b"), Csv.lists(rows).get(0));
    }

    /**
     * Verifies: CSV Parsing — a quoted zero-length value parses as the
     * configured empty value, independently of the null value.
     */
    @Test
    void emptyValueSubstitutesQuotedEmpties() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setNullValue("N/A");
        settings.setEmptyValue("<empty>");
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader("a,,\"\"\n"));
        assertEquals(Csv.row("a", "N/A", "<empty>"), Csv.lists(rows).get(0));
    }

    /**
     * Verifies: CSV Parsing — with default settings both absent and quoted
     * empty values parse as null.
     */
    @Test
    void defaultSubstitutionsAreNull() {
        List<String[]> rows = new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader("a,,\"\"\n"));
        assertEquals("a", rows.get(0)[0]);
        assertNull(rows.get(0)[1]);
        assertNull(rows.get(0)[2]);
    }

    /**
     * Verifies: CSV Parsing — a value at exactly the maxCharsPerColumn bound
     * parses normally.
     */
    @Test
    void maxCharsBoundaryParses() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setMaxCharsPerColumn(4);
        assertEquals("abcd", new CsvParser(settings).parseLine("abcd,x")[0]);
    }

    /**
     * Verifies: Error Semantics — a value exceeding maxCharsPerColumn raises
     * TextParsingException.
     */
    @Test
    void maxCharsViolationRaisesTextParsing() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setMaxCharsPerColumn(4);
        assertThrows(TextParsingException.class,
                () -> new CsvParser(settings).parseAll(new StringReader("abcdefghij,b\n")));
    }
}
