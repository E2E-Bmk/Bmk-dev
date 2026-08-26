package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.univocity.parsers.csv.CsvFormat;
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import java.io.StringReader;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** CSV dialect, quoting, comments, trimming, and reading entry points. */
class CsvParsingAtomicTest {

    /**
     * Verifies: CSV Parsing — parseAll returns every row, including the first
     * row when header extraction is off.
     */
    @Test
    void parseAllReturnsEveryRow() {
        List<String[]> rows = new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(3, rows.size());
        assertEquals(Csv.row("name", "age", "city"), Csv.lists(rows).get(0));
        assertEquals(Csv.row("Smith, John", "30", "NYC"), Csv.lists(rows).get(1));
    }

    /**
     * Verifies: CSV Parsing — a value containing the delimiter is read from
     * its quoted form.
     */
    @Test
    void quotedValueWithDelimiterIsRead() {
        String[] row = new CsvParser(new CsvParserSettings()).parseLine("a,\"b,c\",d");
        assertEquals(Csv.row("a", "b,c", "d"), List.of(row));
    }

    /**
     * Verifies: CSV Parsing — the escape character doubles the quote inside a
     * quoted value.
     */
    @Test
    void doubledQuoteDecodesInsideQuotedValue() {
        String[] row = new CsvParser(new CsvParserSettings())
                .parseLine("\"he said \"\"hi\"\"\",x");
        assertEquals("he said \"hi\"", row[0]);
    }

    /**
     * Verifies: CSV Parsing — the default dialect is comma, double quote,
     * double-quote escape, and hash comment.
     */
    @Test
    void defaultDialectCharacters() {
        CsvFormat format = new CsvParserSettings().getFormat();
        assertEquals(',', format.getDelimiter());
        assertEquals('"', format.getQuote());
        assertEquals('"', format.getQuoteEscape());
        assertEquals('#', format.getComment());
    }

    /**
     * Verifies: CSV Parsing — setDelimiter and setQuote change the dialect.
     */
    @Test
    void customDelimiterAndQuote() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.getFormat().setDelimiter(';');
        settings.getFormat().setQuote('\'');
        List<String[]> rows = new CsvParser(settings)
                .parseAll(new StringReader("x;'a;b';z\n"));
        assertEquals(Csv.row("x", "a;b", "z"), Csv.lists(rows).get(0));
    }

    /**
     * Verifies: CSV Parsing — comment lines and empty lines are skipped by
     * default.
     */
    @Test
    void commentsAndEmptyLinesAreSkipped() {
        List<String[]> rows = new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader("#comment\na,b\n\nc,d\n"));
        assertEquals(List.of(Csv.row("a", "b"), Csv.row("c", "d")), Csv.lists(rows));
    }

    /**
     * Verifies: CSV Parsing — surrounding whitespace is trimmed by default.
     */
    @Test
    void whitespaceTrimmedByDefault() {
        List<String[]> rows = new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader("  a  , b \n"));
        assertEquals(Csv.row("a", "b"), Csv.lists(rows).get(0));
    }

    /**
     * Verifies: CSV Parsing — trimValues(false) preserves surrounding
     * whitespace.
     */
    @Test
    void trimValuesFalsePreservesWhitespace() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.trimValues(false);
        List<String[]> rows = new CsvParser(settings)
                .parseAll(new StringReader("  a  , b \n"));
        assertEquals(Csv.row("  a  ", " b "), Csv.lists(rows).get(0));
    }

    /**
     * Verifies: CSV Parsing — line separator detection accepts CRLF input.
     */
    @Test
    void lineSeparatorDetectionAcceptsCrlf() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setLineSeparatorDetectionEnabled(true);
        List<String[]> rows = new CsvParser(settings)
                .parseAll(new StringReader("a,b\r\nc,d\r\n"));
        assertEquals(List.of(Csv.row("a", "b"), Csv.row("c", "d")), Csv.lists(rows));
    }

    /**
     * Verifies: CSV Parsing — detectFormatAutomatically chooses the delimiter
     * and getDetectedFormat reports it.
     */
    @Test
    void formatDetectionChoosesDelimiter() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.detectFormatAutomatically();
        CsvParser parser = new CsvParser(settings);
        List<String[]> rows = parser.parseAll(new StringReader("a;b;c\n1;2;3\n4;5;6\n"));
        assertEquals(Csv.row("1", "2", "3"), Csv.lists(rows).get(1));
        assertEquals(';', parser.getDetectedFormat().getDelimiter());
    }

    /**
     * Verifies: CSV Parsing — empty input parses to an empty list.
     */
    @Test
    void emptyInputParsesToEmptyList() {
        assertTrue(new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader("")).isEmpty());
    }
}
