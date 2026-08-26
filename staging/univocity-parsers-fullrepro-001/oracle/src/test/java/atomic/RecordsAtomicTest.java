package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.univocity.parsers.common.record.Record;
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Typed record views keyed by document headers. */
class RecordsAtomicTest {

    private static CsvParser headerParser() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        return new CsvParser(settings);
    }

    /**
     * Verifies: Records — getString and getInt convert the addressed value by
     * header name.
     */
    @Test
    void stringAndIntAccessors() {
        Record record = headerParser().parseAllRecords(new StringReader(Csv.PEOPLE)).get(0);
        assertEquals("Smith, John", record.getString("name"));
        assertEquals(30, record.getInt("age"));
    }

    /**
     * Verifies: Records — getDouble, getLong, and getBoolean convert their
     * value types.
     */
    @Test
    void numericAndBooleanAccessors() {
        Record record = headerParser()
                .parseAllRecords(new StringReader("a,b,c\n1.5,true,900000000000\n")).get(0);
        assertEquals(1.5, record.getDouble("a"));
        assertEquals(Boolean.TRUE, record.getBoolean("b"));
        assertEquals(900000000000L, record.getLong("c"));
    }

    /**
     * Verifies: Records — getValues returns the underlying row values.
     */
    @Test
    void getValuesReturnsUnderlyingRow() {
        Record record = headerParser().parseAllRecords(new StringReader(Csv.PEOPLE)).get(0);
        assertEquals(Csv.row("Smith, John", "30", "NYC"), List.of(record.getValues()));
    }

    /**
     * Verifies: Records — getValue returns the stored value when present and
     * the default when the stored value is null.
     */
    @Test
    void getValueAppliesDefaultOnNull() {
        Record present = headerParser().parseAllRecords(new StringReader("a,b\n1.5,x\n")).get(0);
        assertEquals("1.5", present.getValue("a", "dflt"));
        Record absent = headerParser().parseAllRecords(new StringReader("a,b\n,x\n")).get(0);
        assertEquals("dflt", absent.getValue("a", "dflt"));
    }

    /**
     * Verifies: Records — iterateRecords streams typed records.
     */
    @Test
    void iterateRecordsStreams() {
        List<String> names = new ArrayList<>();
        for (Record record : headerParser().iterateRecords(new StringReader(Csv.PEOPLE))) {
            names.add(record.getString("name"));
        }
        assertEquals(List.of("Smith, John", "Jane"), names);
    }

    /**
     * Verifies: Records — record metadata reports headers and column
     * membership.
     */
    @Test
    void metadataReportsSchema() {
        CsvParser parser = headerParser();
        parser.parseAllRecords(new StringReader(Csv.PEOPLE));
        assertEquals(Csv.row("name", "age", "city"), List.of(parser.getRecordMetadata().headers()));
        assertTrue(parser.getRecordMetadata().containsColumn("age"));
        assertFalse(parser.getRecordMetadata().containsColumn("nope"));
    }

    /**
     * Verifies: Error Semantics — a numeric accessor on a non-numeric value
     * raises NumberFormatException.
     */
    @Test
    void numericAccessorOnTextRaises() {
        Record record = headerParser().parseAllRecords(new StringReader(Csv.PEOPLE)).get(0);
        assertThrows(NumberFormatException.class, () -> record.getInt("name"));
    }

    /**
     * Verifies: Error Semantics — addressing a header outside the schema
     * raises IllegalArgumentException.
     */
    @Test
    void unknownHeaderRaisesIllegalArgument() {
        Record record = headerParser().parseAllRecords(new StringReader(Csv.PEOPLE)).get(0);
        assertThrows(IllegalArgumentException.class, () -> record.getString("nope"));
    }
}
