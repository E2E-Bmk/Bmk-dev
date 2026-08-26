package integration;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

import com.univocity.parsers.common.record.Record;
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import com.univocity.parsers.fixed.FixedWidthFields;
import com.univocity.parsers.fixed.FixedWidthParser;
import com.univocity.parsers.fixed.FixedWidthParserSettings;
import com.univocity.parsers.tsv.TsvParser;
import com.univocity.parsers.tsv.TsvParserSettings;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Agreement between the projections of one parsing session. */
class ProjectionAgreementIntegrationTest {

    private static final String DOC = "name,age,city\n\"Smith, John\",30,NYC\nJane,25,\"LA\"\nBob,41,SF\n";

    /**
     * Verifies: Cross-View Invariants — parseAll and the parseNext stream
     * produce the same rows in the same order.
     * Depends-On: parseAllReturnsEveryRow, parseNextStreamsRowsThenNull.
     */
    @Test
    void parseAllAndParseNextAgree() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        List<String[]> all = parser.parseAll(new StringReader(DOC));

        CsvParser streaming = new CsvParser(new CsvParserSettings());
        streaming.beginParsing(new StringReader(DOC));
        List<String[]> streamed = new ArrayList<>();
        String[] row;
        while ((row = streaming.parseNext()) != null) {
            streamed.add(row);
        }
        assertEquals(Csv.lists(all), Csv.lists(streamed));
    }

    /**
     * Verifies: Cross-View Invariants — parseAll and iterate produce the same
     * rows in the same order.
     * Depends-On: parseAllReturnsEveryRow, iterateYieldsRows.
     */
    @Test
    void parseAllAndIterateAgree() {
        List<String[]> all = new CsvParser(new CsvParserSettings()).parseAll(new StringReader(DOC));
        List<String[]> iterated = new ArrayList<>();
        for (String[] row : new CsvParser(new CsvParserSettings()).iterate(new StringReader(DOC))) {
            iterated.add(row);
        }
        assertEquals(Csv.lists(all), Csv.lists(iterated));
    }

    /**
     * Verifies: Cross-View Invariants — for every record, getValues() equals
     * the String[] row that parseAll produces at the same position.
     * Depends-On: getValuesReturnsUnderlyingRow, parseAllReturnsEveryRow.
     */
    @Test
    void recordValuesMatchRowsPositionally() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(DOC));

        CsvParserSettings recordSettings = new CsvParserSettings();
        recordSettings.setHeaderExtractionEnabled(true);
        List<Record> records = new CsvParser(recordSettings).parseAllRecords(new StringReader(DOC));

        assertEquals(rows.size(), records.size());
        for (int i = 0; i < rows.size(); i++) {
            assertArrayEquals(rows.get(i), records.get(i).getValues());
        }
    }

    /**
     * Verifies: Cross-View Invariants — getContext().headers() and
     * getRecordMetadata().headers() agree.
     * Depends-On: headerExtractionConsumesFirstRow, metadataReportsSchema.
     */
    @Test
    void contextAndMetadataHeadersAgree() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        CsvParser parser = new CsvParser(settings);
        parser.parseAllRecords(new StringReader(DOC));
        assertArrayEquals(parser.getContext().headers(), parser.getRecordMetadata().headers());
        assertArrayEquals(new String[] {"name", "age", "city"}, parser.getContext().headers());
    }

    /**
     * Verifies: Cross-View Invariants — with header extraction enabled the
     * header row does not appear among the parsed rows.
     * Depends-On: headerExtractionConsumesFirstRow, parseAllReturnsEveryRow.
     */
    @Test
    void headerRowNotAmongParsedRows() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(DOC));
        assertEquals(3, rows.size());
        for (String[] row : rows) {
            assertFalse(Csv.row("name", "age", "city").equals(Csv.row(row)));
        }
    }

    /**
     * Verifies: Cross-View Invariants — currentRecord() after consuming n
     * rows is n in the CSV format.
     * Depends-On: currentRecordCountsRows, parseAllReturnsEveryRow.
     */
    @Test
    void currentRecordCountsCsv() {
        CsvParser parser = new CsvParser(new CsvParserSettings());
        List<String[]> rows = parser.parseAll(new StringReader(DOC));
        assertEquals(rows.size(), parser.getContext().currentRecord());
    }

    /**
     * Verifies: Cross-View Invariants — currentRecord() after consuming n
     * rows is n in the TSV format.
     * Depends-On: currentRecordCountsRows, rowsSplitOnTabs.
     */
    @Test
    void currentRecordCountsTsv() {
        TsvParser parser = new TsvParser(new TsvParserSettings());
        List<String[]> rows = parser.parseAll(new StringReader("a\tb\nc\td\ne\tf\n"));
        assertEquals(3, rows.size());
        assertEquals(3, parser.getContext().currentRecord());
    }

    /**
     * Verifies: Cross-View Invariants — currentRecord() after consuming n
     * rows is n in the fixed-width format.
     * Depends-On: currentRecordCountsRows, positionalLayoutCutsAtBoundaries.
     */
    @Test
    void currentRecordCountsFixedWidth() {
        FixedWidthParser parser = new FixedWidthParser(
                new FixedWidthParserSettings(new FixedWidthFields(3, 3)));
        List<String[]> rows = parser.parseAll(new StringReader("aa bb \ncc dd \n"));
        assertEquals(2, rows.size());
        assertEquals(2, parser.getContext().currentRecord());
    }

    /**
     * Verifies: Cross-View Invariants — the projections agree in the TSV
     * dialect: parseAll and iterate produce the same rows.
     * Depends-On: rowsSplitOnTabs, iterateYieldsRows.
     */
    @Test
    void tsvProjectionsAgree() {
        String doc = "a\tb\nc\td\n";
        List<String[]> all = new TsvParser(new TsvParserSettings()).parseAll(new StringReader(doc));
        List<String[]> iterated = new ArrayList<>();
        for (String[] row : new TsvParser(new TsvParserSettings()).iterate(new StringReader(doc))) {
            iterated.add(row);
        }
        assertEquals(Csv.lists(all), Csv.lists(iterated));
    }

    /**
     * Verifies: Cross-View Invariants — the projections agree in the
     * fixed-width dialect: parseAll and the parseNext stream produce the same
     * rows.
     * Depends-On: positionalLayoutCutsAtBoundaries, parseNextStreamsRowsThenNull.
     */
    @Test
    void fixedWidthProjectionsAgree() {
        String doc = "aa bb \ncc dd \n";
        FixedWidthFields layout = new FixedWidthFields(3, 3);
        List<String[]> all = new FixedWidthParser(new FixedWidthParserSettings(layout))
                .parseAll(new StringReader(doc));

        FixedWidthParser streaming = new FixedWidthParser(
                new FixedWidthParserSettings(new FixedWidthFields(3, 3)));
        streaming.beginParsing(new StringReader(doc));
        List<String[]> streamed = new ArrayList<>();
        String[] row;
        while ((row = streaming.parseNext()) != null) {
            streamed.add(row);
        }
        assertEquals(Csv.lists(all), Csv.lists(streamed));
    }

    /**
     * Verifies: Cross-View Invariants — iterateRecords and parseAllRecords
     * present the same values in the same order.
     * Depends-On: iterateRecordsStreams, getValuesReturnsUnderlyingRow.
     */
    @Test
    void recordStreamsAgree() {
        CsvParserSettings first = new CsvParserSettings();
        first.setHeaderExtractionEnabled(true);
        List<Record> all = new CsvParser(first).parseAllRecords(new StringReader(DOC));

        CsvParserSettings second = new CsvParserSettings();
        second.setHeaderExtractionEnabled(true);
        List<List<String>> iterated = new ArrayList<>();
        for (Record record : new CsvParser(second).iterateRecords(new StringReader(DOC))) {
            iterated.add(Csv.row(record.getValues()));
        }
        List<List<String>> expected = new ArrayList<>();
        for (Record record : all) {
            expected.add(Csv.row(record.getValues()));
        }
        assertEquals(expected, iterated);
    }
}
