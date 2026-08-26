package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Streaming sessions: beginParsing, parseNext, iterate, context counters. */
class StreamingAtomicTest {

    /**
     * Verifies: CSV Parsing — parseNext returns rows one at a time and null at
     * the end of input.
     */
    @Test
    void parseNextStreamsRowsThenNull() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        parser.beginParsing(new StringReader("1,2\n3,4\n"));
        assertEquals(Csv.row("1", "2"), List.of(parser.parseNext()));
        assertEquals(Csv.row("3", "4"), List.of(parser.parseNext()));
        assertNull(parser.parseNext());
    }

    /**
     * Verifies: CSV Parsing — stopParsing ends a streaming session early
     * without error.
     */
    @Test
    void stopParsingEndsSession() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        parser.beginParsing(new StringReader("1,2\n3,4\n5,6\n"));
        assertEquals(Csv.row("1", "2"), List.of(parser.parseNext()));
        parser.stopParsing();
    }

    /**
     * Verifies: CSV Parsing — iterate yields the same rows as parseAll for use
     * in for-each loops.
     */
    @Test
    void iterateYieldsRows() {
        List<List<String>> seen = new ArrayList<>();
        for (String[] row : new CsvParser(new CsvParserSettings())
                .iterate(new StringReader("x,y\nz,w\n"))) {
            seen.add(List.of(row));
        }
        assertEquals(List.of(Csv.row("x", "y"), Csv.row("z", "w")), seen);
    }

    /**
     * Verifies: Headers and Column Selection — currentRecord reports the count
     * of rows produced so far.
     */
    @Test
    void currentRecordCountsRows() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        parser.beginParsing(new StringReader("1,2\n3,4\n"));
        parser.parseNext();
        assertEquals(1, parser.getContext().currentRecord());
        parser.parseNext();
        assertEquals(2, parser.getContext().currentRecord());
        parser.stopParsing();
    }

    /**
     * Verifies: Headers and Column Selection — without header extraction,
     * headers() reports the first row seen while the row still parses as data.
     */
    @Test
    void headersReportedWithoutExtraction() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        List<String[]> rows = parser.parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(3, rows.size());
        assertEquals(Csv.row("name", "age", "city"), List.of(parser.getContext().headers()));
    }
}
