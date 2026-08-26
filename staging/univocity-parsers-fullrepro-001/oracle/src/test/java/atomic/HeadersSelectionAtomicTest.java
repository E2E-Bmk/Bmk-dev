package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import java.io.StringReader;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Header extraction and column selection in both reordering modes. */
class HeadersSelectionAtomicTest {

    /**
     * Verifies: Headers and Column Selection — header extraction consumes the
     * first row and reports it through headers().
     */
    @Test
    void headerExtractionConsumesFirstRow() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        CsvParser parser = new CsvParser(settings);
        List<String[]> rows = parser.parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(2, rows.size());
        assertEquals(Csv.row("Smith, John", "30", "NYC"), Csv.lists(rows).get(0));
        assertEquals(Csv.row("name", "age", "city"), List.of(parser.getContext().headers()));
    }

    /**
     * Verifies: Headers and Column Selection — selectFields restricts output
     * to the chosen columns in selection order.
     */
    @Test
    void selectFieldsReordersToSelectionOrder() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("city", "name");
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(Csv.row("NYC", "Smith, John"), Csv.lists(rows).get(0));
        assertEquals(Csv.row("LA", "Jane"), Csv.lists(rows).get(1));
    }

    /**
     * Verifies: Headers and Column Selection — selectIndexes selects by
     * zero-based position.
     */
    @Test
    void selectIndexesSelectsByPosition() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.selectIndexes(2, 0);
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(Csv.row("city", "name"), Csv.lists(rows).get(0));
        assertEquals(Csv.row("NYC", "Smith, John"), Csv.lists(rows).get(1));
    }

    /**
     * Verifies: Headers and Column Selection — with reordering disabled, rows
     * keep original positions and unselected columns are null.
     */
    @Test
    void reorderingDisabledKeepsPositions() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("city", "name");
        settings.setColumnReorderingEnabled(false);
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));
        String[] first = rows.get(0);
        assertEquals(3, first.length);
        assertEquals("Smith, John", first[0]);
        assertNull(first[1]);
        assertEquals("NYC", first[2]);
    }

    /**
     * Verifies: Headers and Column Selection — selecting an unknown field name
     * yields an empty projection without raising.
     */
    @Test
    void unknownSelectionYieldsEmptyProjection() {
        CsvParserSettings settings = new CsvParserSettings();
        settings.setHeaderExtractionEnabled(true);
        settings.selectFields("nope");
        List<String[]> rows = new CsvParser(settings).parseAll(new StringReader(Csv.PEOPLE));
        assertEquals(2, rows.size());
        for (String[] row : rows) {
            assertTrue(row.length == 0);
        }
    }
}
