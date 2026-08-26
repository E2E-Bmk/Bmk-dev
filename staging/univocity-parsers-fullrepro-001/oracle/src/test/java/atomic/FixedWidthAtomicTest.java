package atomic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.univocity.parsers.common.record.Record;
import com.univocity.parsers.fixed.FieldAlignment;
import com.univocity.parsers.fixed.FixedWidthFields;
import com.univocity.parsers.fixed.FixedWidthParser;
import com.univocity.parsers.fixed.FixedWidthParserSettings;
import com.univocity.parsers.fixed.FixedWidthWriter;
import com.univocity.parsers.fixed.FixedWidthWriterSettings;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Fixed-width layout: positional and named fields, padding, alignment. */
class FixedWidthAtomicTest {

    /**
     * Verifies: Fixed-Width Format — a positional layout cuts each line at
     * the configured boundaries.
     */
    @Test
    void positionalLayoutCutsAtBoundaries() {
        FixedWidthParser parser = new FixedWidthParser(
                new FixedWidthParserSettings(new FixedWidthFields(5, 5, 5)));
        List<String[]> rows = parser.parseAll(new StringReader("aa   bb   cc   \n"));
        assertEquals(List.of(Csv.row("aa", "bb", "cc")), Csv.lists(rows));
    }

    /**
     * Verifies: Fixed-Width Format — surrounding whitespace is trimmed from
     * each value by default.
     */
    @Test
    void surroundingWhitespaceTrimmed() {
        FixedWidthParser parser = new FixedWidthParser(
                new FixedWidthParserSettings(new FixedWidthFields(5, 5, 5)));
        List<String[]> rows = parser.parseAll(new StringReader("  x    y    z  \n"));
        assertEquals(List.of(Csv.row("x", "y", "z")), Csv.lists(rows));
    }

    /**
     * Verifies: Fixed-Width Format — named fields become the derived headers
     * reported by the parsing context.
     */
    @Test
    void namedFieldsBecomeDerivedHeaders() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("name", 8);
        fields.addField("age", 4);
        FixedWidthParser parser = new FixedWidthParser(new FixedWidthParserSettings(fields));
        parser.parseAll(new StringReader("Jane    25  \n"));
        assertArrayEquals(new String[] {"name", "age"}, parser.getContext().headers());
    }

    /**
     * Verifies: Fixed-Width Format — named fields are usable for record
     * access.
     */
    @Test
    void namedFieldsUsableForRecordAccess() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("name", 8);
        fields.addField("age", 4);
        FixedWidthParser parser = new FixedWidthParser(new FixedWidthParserSettings(fields));
        List<Record> records = parser.parseAllRecords(new StringReader("Jane    25  \nBob     41  \n"));
        assertEquals("Jane", records.get(0).getString("name"));
        assertEquals(41, records.get(1).getInt("age"));
    }

    /**
     * Verifies: Fixed-Width Format — with header extraction enabled the first
     * physical row is consumed as headers.
     */
    @Test
    void headerExtractionConsumesFirstPhysicalRow() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("col1", 5);
        fields.addField("col2", 5);
        FixedWidthParserSettings settings = new FixedWidthParserSettings(fields);
        settings.setHeaderExtractionEnabled(true);
        FixedWidthParser parser = new FixedWidthParser(settings);
        List<String[]> rows = parser.parseAll(new StringReader("col1 col2 \nv1   v2   \n"));
        assertArrayEquals(new String[] {"col1", "col2"}, parser.getContext().headers());
        assertEquals(List.of(Csv.row("v1", "v2")), Csv.lists(rows));
    }

    /**
     * Verifies: Fixed-Width Format — the writer pads every value to its exact
     * field length with spaces and left alignment by default.
     */
    @Test
    void writerPadsWithSpacesLeftByDefault() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("id", 4);
        fields.addField("val", 6);
        StringWriter out = new StringWriter();
        FixedWidthWriter writer = new FixedWidthWriter(out, new FixedWidthWriterSettings(fields));
        writer.writeRow("7", "ab");
        writer.close();
        assertEquals("7   ab    \n", out.toString());
    }

    /**
     * Verifies: Fixed-Width Format — a right-aligned field of length 6 padded
     * with 0 writes 42 as 000042.
     */
    @Test
    void rightAlignedZeroPaddedField() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("id", 4);
        fields.addField("num", 6, FieldAlignment.RIGHT, '0');
        StringWriter out = new StringWriter();
        FixedWidthWriter writer = new FixedWidthWriter(out, new FixedWidthWriterSettings(fields));
        writer.writeRow("a", "42");
        writer.close();
        assertEquals("a   000042\n", out.toString());
    }

    /**
     * Verifies: Fixed-Width Format — a center-aligned field distributes its
     * padding character on both sides of the value.
     */
    @Test
    void centerAlignedFieldPadsBothSides() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("c", 7, FieldAlignment.CENTER, '.');
        fields.addField("d", 3);
        StringWriter out = new StringWriter();
        FixedWidthWriter writer = new FixedWidthWriter(out, new FixedWidthWriterSettings(fields));
        writer.writeRow("mid", "x");
        writer.close();
        assertEquals("..mid..x  \n", out.toString());
    }

    /**
     * Verifies: Fixed-Width Format — with setHeaderWritingEnabled(true) the
     * writer first emits the field names, each padded to its field length.
     */
    @Test
    void headerWritingEmitsPaddedFieldNames() {
        FixedWidthFields fields = new FixedWidthFields();
        fields.addField("id", 4);
        fields.addField("val", 6);
        FixedWidthWriterSettings settings = new FixedWidthWriterSettings(fields);
        settings.setHeaderWritingEnabled(true);
        StringWriter out = new StringWriter();
        FixedWidthWriter writer = new FixedWidthWriter(out, settings);
        writer.writeRow("1", "x");
        writer.close();
        assertEquals("id  val   \n1   x     \n", out.toString());
    }
}
