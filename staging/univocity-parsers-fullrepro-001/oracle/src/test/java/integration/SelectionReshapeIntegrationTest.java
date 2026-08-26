package integration;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.univocity.parsers.common.record.Record;
import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import com.univocity.parsers.csv.CsvWriter;
import com.univocity.parsers.csv.CsvWriterSettings;
import com.univocity.parsers.fixed.FixedWidthFields;
import com.univocity.parsers.fixed.FixedWidthParser;
import com.univocity.parsers.fixed.FixedWidthParserSettings;
import com.univocity.parsers.tsv.TsvParser;
import com.univocity.parsers.tsv.TsvParserSettings;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Option-driven reshaping: selection, reordering, detection, records. */
class SelectionReshapeIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — with column reordering enabled, each
     * output row contains exactly the selected columns in selection order.
     * Depends-On: selectFieldsReordersToSelectionOrder, headerExtractionConsumesFirstRow.
     */
    @Test
    void reorderedSelectionShapesEveryRow() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("city", "name");
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(List.of(Csv.row("NYC", "Smith, John"), Csv.row("LA", "Jane")),
                Csv.lists(rows));
    }

    /**
     * Verifies: Cross-View Invariants — with reordering disabled, the same
     * values appear at their original indexes with null elsewhere.
     * Depends-On: reorderingDisabledKeepsPositions, selectFieldsReordersToSelectionOrder.
     */
    @Test
    void reorderingDisabledPreservesIndexes() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("city", "name");
        settings.setColumnReorderingEnabled(false);
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));
        for (String[] row : rows) {
            assertEquals(3, row.length);
            assertNull(row[1]);
        }
        assertEquals("Smith, John", rows.get(0)[0]);
        assertEquals("NYC", rows.get(0)[2]);
        assertEquals("Jane", rows.get(1)[0]);
        assertEquals("LA", rows.get(1)[2]);
    }

    /**
     * Verifies: Cross-View Invariants — records under a reordered selection
     * report the projected values while header access still resolves the
     * selected columns.
     * Depends-On: selectFieldsReordersToSelectionOrder, stringAndIntAccessors, getValuesReturnsUnderlyingRow.
     */
    @Test
    void recordsFollowSelectionProjection() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("city", "name");
        List<Record> records = new CsvParser(settings).parseAllRecords(new StringReader(Csv.PEOPLE));
        assertArrayEquals(new String[] {"NYC", "Smith, John"}, records.get(0).getValues());
        assertEquals("NYC", records.get(0).getString("city"));
        assertEquals("Smith, John", records.get(0).getString("name"));
    }

    /**
     * Verifies: Cross-View Invariants — selectIndexes produces the same
     * projection discipline as selectFields over the same positions.
     * Depends-On: selectIndexesSelectsByPosition, selectFieldsReordersToSelectionOrder.
     */
    @Test
    void indexAndNameSelectionAgree() {
        CsvParserSettings byName = new CsvParserSettings();
        byName.setHeaderExtractionEnabled(true);
        byName.selectFields("city", "name");
        List<String[]> named = new CsvParser(byName).parseAll(new StringReader(Csv.PEOPLE));

        CsvParserSettings byIndex = new CsvParserSettings();
        byIndex.setHeaderExtractionEnabled(true);
        byIndex.selectIndexes(2, 0);
        List<String[]> indexed = new CsvParser(byIndex).parseAll(new StringReader(Csv.PEOPLE));

        assertEquals(Csv.lists(named), Csv.lists(indexed));
    }

    /**
     * Verifies: Cross-View Invariants — a selected projection written out and
     * reparsed presents the same values under header access.
     * Depends-On: selectFieldsReordersToSelectionOrder, headersAndRowsProduceLines, stringAndIntAccessors.
     */
    @Test
    void selectedProjectionRewriteReadsBack() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("city", "name");
        List<String[]> projected = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));

        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeHeaders("city", "name");
        for (String[] row : projected) {
            writer.writeRow((Object[]) row);
        }
        writer.close();

        CsvParserSettings reread = new CsvParserSettings();
        reread.setHeaderExtractionEnabled(true);
        List<Record> records = new CsvParser(reread).parseAllRecords(new StringReader(out.toString()));
        assertEquals("NYC", records.get(0).getString("city"));
        assertEquals("Smith, John", records.get(0).getString("name"));
        assertEquals("LA", records.get(1).getString("city"));
    }

    /**
     * Verifies: Cross-View Invariants — selection applies over the tab
     * dialect with the same reordering discipline.
     * Depends-On: rowsSplitOnTabs, selectFieldsReordersToSelectionOrder.
     */
    @Test
    void selectionAppliesOverTsv() {
        TsvParserSettings settings = new TsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("c", "a");
        List<String[]> rows = new TsvParser(settings)
                .parseAll(new StringReader("a\tb\tc\n1\t2\t3\n4\t5\t6\n"));
        assertEquals(List.of(Csv.row("3", "1"), Csv.row("6", "4")), Csv.lists(rows));
    }

    /**
     * Verifies: Cross-View Invariants — the detected dialect of one document
     * configures a writer whose output reparses to the same rows.
     * Depends-On: formatDetectionChoosesDelimiter, customDelimiterAndQuote, headersAndRowsProduceLines.
     */
    @Test
    void detectedFormatFeedsWriterRoundTrip() {
        CsvParserSettings detect = new CsvParserSettings();
        detect.detectFormatAutomatically();
        CsvParser detector = new CsvParser(detect);
        List<String[]> rows = detector.parseAll(new StringReader("1;2\n3;4\n"));
        char delimiter = detector.getDetectedFormat().getDelimiter();
        assertEquals(';', delimiter);

        CsvWriterSettings writerSettings = new CsvWriterSettings();
        writerSettings.getFormat().setDelimiter(delimiter);
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, writerSettings);
        for (String[] row : rows) {
            writer.writeRow((Object[]) row);
        }
        writer.close();

        CsvParserSettings reread = new CsvParserSettings();
        reread.getFormat().setDelimiter(';');
        List<String[]> back = new CsvParser(reread).parseAll(new StringReader(out.toString()));
        assertEquals(Csv.lists(rows), Csv.lists(back));
    }

    /**
     * Verifies: Cross-View Invariants — fixed-width records over a named
     * layout report values equal to the parseAll rows at the same positions.
     * Depends-On: namedFieldsUsableForRecordAccess, positionalLayoutCutsAtBoundaries, getValuesReturnsUnderlyingRow.
     */
    @Test
    void fixedWidthRecordsMatchRows() {
        String doc = "Jane    25  \nBob     41  \n";
        FixedWidthFields layout = new FixedWidthFields();
        layout.addField("name", 8);
        layout.addField("age", 4);
        List<String[]> rows = new FixedWidthParser(new FixedWidthParserSettings(layout))
                .parseAll(new StringReader(doc));

        FixedWidthFields layout2 = new FixedWidthFields();
        layout2.addField("name", 8);
        layout2.addField("age", 4);
        List<Record> records = new FixedWidthParser(new FixedWidthParserSettings(layout2))
                .parseAllRecords(new StringReader(doc));

        assertEquals(rows.size(), records.size());
        for (int i = 0; i < rows.size(); i++) {
            assertArrayEquals(rows.get(i), records.get(i).getValues());
        }
        assertEquals(41, records.get(1).getInt("age"));
    }

    /**
     * Verifies: Cross-View Invariants — an unknown selection yields an empty
     * projection consistently across parseAll and the record view.
     * Depends-On: unknownSelectionYieldsEmptyProjection, getValuesReturnsUnderlyingRow.
     */
    @Test
    void unknownSelectionEmptyInBothViews() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("missing");
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));

        CsvParserSettings recordSettings = new CsvParserSettings();
        recordSettings.setHeaderExtractionEnabled(true);
        recordSettings.selectFields("missing");
        List<Record> records = new CsvParser(recordSettings)
                .parseAllRecords(new StringReader(Csv.PEOPLE));

        assertEquals(rows.size(), records.size());
        for (int i = 0; i < rows.size(); i++) {
            assertEquals(0, rows.get(i).length);
            assertEquals(0, records.get(i).getValues().length);
        }
    }
}
