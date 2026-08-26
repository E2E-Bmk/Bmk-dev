package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.univocity.parsers.csv.CsvParser;
import com.univocity.parsers.csv.CsvParserSettings;
import com.univocity.parsers.csv.CsvWriter;
import com.univocity.parsers.csv.CsvWriterSettings;
import com.univocity.parsers.fixed.FieldAlignment;
import com.univocity.parsers.fixed.FixedWidthFields;
import com.univocity.parsers.fixed.FixedWidthParser;
import com.univocity.parsers.fixed.FixedWidthParserSettings;
import com.univocity.parsers.fixed.FixedWidthWriter;
import com.univocity.parsers.fixed.FixedWidthWriterSettings;
import com.univocity.parsers.tsv.TsvParser;
import com.univocity.parsers.tsv.TsvParserSettings;
import com.univocity.parsers.tsv.TsvWriter;
import com.univocity.parsers.tsv.TsvWriterSettings;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.List;
import org.junit.jupiter.api.Test;
import support.Csv;

/** Write-then-parse round trips across the three dialects. */
class RoundTripIntegrationTest {

    private static List<List<String>> csvReparse(String document) {
        return Csv.lists(new CsvParser(new CsvParserSettings()).parseAll(new StringReader(document)));
    }

    /**
     * Verifies: Cross-View Invariants — rows written by a CSV writer parse
     * back to the original values under matching settings.
     * Depends-On: headersAndRowsProduceLines, parseAllReturnsEveryRow.
     */
    @Test
    void csvRoundTripRestoresValues() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeRow("plain", "second");
        writer.writeRow("third", "fourth");
        writer.close();
        assertEquals(List.of(Csv.row("plain", "second"), Csv.row("third", "fourth")),
                csvReparse(out.toString()));
    }

    /**
     * Verifies: Cross-View Invariants — a value quoted because it contains
     * the delimiter parses back to the identical unquoted value.
     * Depends-On: quotingOnlyForDelimiterBearingValues, quotedValueWithDelimiterIsRead.
     */
    @Test
    void csvQuotedDelimiterValueRoundTrips() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeRow("a,b", "x");
        writer.close();
        assertEquals(List.of(Csv.row("a,b", "x")), csvReparse(out.toString()));
    }

    /**
     * Verifies: Cross-View Invariants — an embedded quote doubled on write
     * decodes back to a single quote on parse.
     * Depends-On: embeddedQuoteDoubledWhenQuoted, doubledQuoteDecodesInsideQuotedValue.
     */
    @Test
    void csvEmbeddedQuoteRoundTrips() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeRow("say \"hi\", now", "x");
        writer.close();
        assertEquals(List.of(Csv.row("say \"hi\", now", "x")), csvReparse(out.toString()));
    }

    /**
     * Verifies: Cross-View Invariants — a value containing a line separator
     * survives the write-then-parse round trip.
     * Depends-On: lineBreakBearingValueIsQuoted, parseAllReturnsEveryRow.
     */
    @Test
    void csvLineBreakValueRoundTrips() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeRow("line1\nline2", "x");
        writer.writeRow("tail", "y");
        writer.close();
        assertEquals(List.of(Csv.row("line1\nline2", "x"), Csv.row("tail", "y")),
                csvReparse(out.toString()));
    }

    /**
     * Verifies: Cross-View Invariants — the documented null/empty collapse is
     * the round trip's only exception: a null written as the empty field
     * parses back as null.
     * Depends-On: nullValueSubstitutionOnWrite, defaultSubstitutionsAreNull.
     */
    @Test
    void csvNullCollapsesAcrossRoundTrip() {
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, new CsvWriterSettings());
        writer.writeRow("a", null, "c");
        writer.close();
        String[] back = new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader(out.toString())).get(0);
        assertEquals("a", back[0]);
        assertNull(back[1]);
        assertEquals("c", back[2]);
    }

    /**
     * Verifies: Cross-View Invariants — quoteAllFields output parses back to
     * the same values.
     * Depends-On: quoteAllFieldsQuotesEverything, quotedValueWithDelimiterIsRead.
     */
    @Test
    void csvQuoteAllFieldsRoundTrips() {
        CsvWriterSettings settings = new CsvWriterSettings();
        settings.setQuoteAllFields(true);
        StringWriter out = new StringWriter();
        CsvWriter writer = new CsvWriter(out, settings);
        writer.writeRow("a", "b c", "d");
        writer.close();
        assertEquals(List.of(Csv.row("a", "b c", "d")), csvReparse(out.toString()));
    }

    /**
     * Verifies: Cross-View Invariants — a TSV escape sequence written for a
     * tab decodes to the identical character on parse.
     * Depends-On: writerEncodesTabAndNewline, escapedTabDecodes.
     */
    @Test
    void tsvTabEscapeRoundTrips() {
        StringWriter out = new StringWriter();
        TsvWriter writer = new TsvWriter(out, new TsvWriterSettings());
        writer.writeRow("a\tb", "x");
        writer.close();
        List<String[]> back = new TsvParser(new TsvParserSettings())
                .parseAll(new StringReader(out.toString()));
        assertEquals(List.of(Csv.row("a\tb", "x")), Csv.lists(back));
    }

    /**
     * Verifies: Cross-View Invariants — a TSV escape sequence written for a
     * line break decodes to the identical character on parse.
     * Depends-On: writerEncodesTabAndNewline, escapedNewlineDecodes.
     */
    @Test
    void tsvNewlineEscapeRoundTrips() {
        StringWriter out = new StringWriter();
        TsvWriter writer = new TsvWriter(out, new TsvWriterSettings());
        writer.writeRow("line1\nline2", "x");
        writer.close();
        List<String[]> back = new TsvParser(new TsvParserSettings())
                .parseAll(new StringReader(out.toString()));
        assertEquals(List.of(Csv.row("line1\nline2", "x")), Csv.lists(back));
    }

    /**
     * Verifies: Cross-View Invariants — the fixed-width writer emits lines
     * whose length equals the sum of the field lengths, and the parser over
     * the same layout recovers the trimmed values.
     * Depends-On: writerPadsWithSpacesLeftByDefault, positionalLayoutCutsAtBoundaries, surroundingWhitespaceTrimmed.
     */
    @Test
    void fixedWidthRoundTripAndLineLengths() {
        StringWriter out = new StringWriter();
        FixedWidthWriter writer = new FixedWidthWriter(out,
                new FixedWidthWriterSettings(new FixedWidthFields(6, 6)));
        writer.writeRow("hello", "world");
        writer.writeRow("a", "b");
        writer.close();
        for (String line : out.toString().split("\n")) {
            assertEquals(12, line.length());
        }
        List<String[]> back = new FixedWidthParser(
                new FixedWidthParserSettings(new FixedWidthFields(6, 6)))
                .parseAll(new StringReader(out.toString()));
        assertEquals(List.of(Csv.row("hello", "world"), Csv.row("a", "b")), Csv.lists(back));
    }

    /**
     * Verifies: Cross-View Invariants — a value written into a right-aligned
     * zero-padded field parses back to the original value under the same
     * layout.
     * Depends-On: rightAlignedZeroPaddedField, positionalLayoutCutsAtBoundaries.
     */
    @Test
    void fixedWidthPaddedFieldRoundTrips() {
        FixedWidthFields layout = new FixedWidthFields();
        layout.addField("id", 4);
        layout.addField("num", 6, FieldAlignment.RIGHT, '0');
        StringWriter out = new StringWriter();
        FixedWidthWriter writer = new FixedWidthWriter(out, new FixedWidthWriterSettings(layout));
        writer.writeRow("a", "42");
        writer.close();

        FixedWidthFields parseLayout = new FixedWidthFields();
        parseLayout.addField("id", 4);
        parseLayout.addField("num", 6, FieldAlignment.RIGHT, '0');
        List<String[]> back = new FixedWidthParser(new FixedWidthParserSettings(parseLayout))
                .parseAll(new StringReader(out.toString()));
        assertEquals(List.of(Csv.row("a", "42")), Csv.lists(back));
    }

    /**
     * Verifies: Cross-View Invariants — values parsed from one dialect and
     * rewritten through another dialect's writer survive that dialect's own
     * round trip.
     * Depends-On: parseAllReturnsEveryRow, rowsSplitOnTabs, writerEncodesTabAndNewline.
     */
    @Test
    void crossDialectRewriteRoundTrips() {
        List<String[]> csvRows = new CsvParser(new CsvParserSettings())
                .parseAll(new StringReader("a,\"b,c\"\nd,e\n"));
        StringWriter out = new StringWriter();
        TsvWriter writer = new TsvWriter(out, new TsvWriterSettings());
        for (String[] row : csvRows) {
            writer.writeRow((Object[]) row);
        }
        writer.close();
        List<String[]> back = new TsvParser(new TsvParserSettings())
                .parseAll(new StringReader(out.toString()));
        assertEquals(Csv.lists(csvRows), Csv.lists(back));
    }
}
