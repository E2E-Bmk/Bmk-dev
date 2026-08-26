package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.univocity.parsers.csv.CsvWriter;
import com.univocity.parsers.csv.CsvWriterSettings;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/** CSV writer output: quoting rules, null substitution, row production. */
class CsvWritingAtomicTest {

    /**
     * Verifies: Writing — writeHeaders and writeRow produce one line each,
     * quoting the value containing the delimiter.
     */
    @Test
    void headersAndRowsProduceLines() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeHeaders("name", "age");
        writer.writeRow("Smith, John", 30);
        writer.close();
        assertEquals("name,age\n\"Smith, John\",30\n", out.toString());
    }

    /**
     * Verifies: Writing — a value is quoted only when it contains the
     * delimiter; an embedded quote alone stays unquoted.
     */
    @Test
    void quotingOnlyForDelimiterBearingValues() {
        String line = new CsvWriter(new CsvWriterSettings()).writeRowToString("a b", "c,d", "e\"f");
        assertEquals("a b,\"c,d\",e\"f", line);
    }

    /**
     * Verifies: Writing — inside a quoted value, embedded quotes are doubled
     * with the escape character.
     */
    @Test
    void embeddedQuoteDoubledWhenQuoted() {
        String line = new CsvWriter(new CsvWriterSettings()).writeRowToString("c,d\"e", "x");
        assertEquals("\"c,d\"\"e\",x", line);
    }

    /**
     * Verifies: Writing — a value containing a line separator is quoted.
     */
    @Test
    void lineBreakBearingValueIsQuoted() {
        String line = new CsvWriter(new CsvWriterSettings()).writeRowToString("l1\nl2", "x");
        assertEquals("\"l1\nl2\",x", line);
    }

    /**
     * Verifies: Writing — setQuoteAllFields quotes every value
     * unconditionally.
     */
    @Test
    void quoteAllFieldsQuotesEverything() {
        CsvWriterSettings settings = new CsvWriterSettings();
        settings.setQuoteAllFields(true);
        assertEquals("\"a\",\"b\"", new CsvWriter(settings).writeRowToString("a", "b"));
    }

    /**
     * Verifies: Writing — a null value is written as the empty field by
     * default and as the configured null value otherwise.
     */
    @Test
    void nullValueSubstitutionOnWrite() {
        assertEquals("x,", new CsvWriter(new CsvWriterSettings()).writeRowToString("x", null));
        CsvWriterSettings settings = new CsvWriterSettings();
        settings.setNullValue("?");
        assertEquals("x,?", new CsvWriter(settings).writeRowToString("x", null));
    }

    /**
     * Verifies: Writing — writeRows writes a collection of rows in order.
     */
    @Test
    void writeRowsWritesCollection() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        List<Object[]> rows = new ArrayList<>();
        rows.add(new Object[] {"1", "2"});
        rows.add(new Object[] {"3", "4"});
        writer.writeRows(rows);
        writer.close();
        assertEquals("1,2\n3,4\n", out.toString());
    }

    /**
     * Verifies: Writing — writeRowToString returns the formatted line without
     * a trailing line separator.
     */
    @Test
    void writeRowToStringHasNoLineSeparator() {
        assertEquals("a,b", new CsvWriter(new CsvWriterSettings()).writeRowToString("a", "b"));
    }
}
