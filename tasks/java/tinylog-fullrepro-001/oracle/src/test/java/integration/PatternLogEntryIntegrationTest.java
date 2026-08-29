package integration;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.tinylog.Level;
import org.tinylog.core.LogEntry;
import org.tinylog.core.LogEntryValue;
import org.tinylog.pattern.FormatPatternParser;
import org.tinylog.pattern.Token;

import static org.junit.jupiter.api.Assertions.*;

class PatternLogEntryIntegrationTest {
    /**
     * Verifies: TINY-FMT-004, TINY-FMT-005, TINY-FMT-006, TINY-FMT-009, TINY-CVI-005.
     * Seam: protocol handoff
     * Depends-On: classProjectionPreservesInput, methodProjectionPreservesInput, messageProjectionPreservesInput
     */
    @Test void combinedPatternPreservesEntryProjectionOrder() {
        assertEquals("example.alpha.Worker|Worker|example.alpha|execute|Worker.java|73|audit|INFO|3|payload-29",
                render("{class}|{class-name}|{package}|{method}|{file}|{line}|{tag}|{level}|{level-code}|{message-only}", entry("payload-29", null)));
    }

    /**
     * Verifies: TINY-FMT-003, TINY-FMT-005, TINY-CVI-002.
     * Seam: protocol handoff
     * Depends-On: contextProjectionPreservesEntries, levelProjectionPreservesInput, messageProjectionPreservesInput
     */
    @Test void requiredValuesAgreeWithRenderedEntryFields() {
        Token token = new FormatPatternParser(null).parse("{context:request}|{level}|{message-only}");
        Collection<LogEntryValue> values = token.getRequiredLogEntryValues();
        assertAll(
                () -> assertTrue(values.contains(LogEntryValue.CONTEXT)),
                () -> assertTrue(values.contains(LogEntryValue.LEVEL)),
                () -> assertTrue(values.contains(LogEntryValue.MESSAGE)),
                () -> assertEquals("r-29|INFO|value", render(token, entry("value", null))));
    }

    /**
     * Verifies: TINY-FMT-009, TINY-CVI-003.
     * Seam: state consistency
     * Depends-On: contextProjectionPreservesEntries
     */
    @Test void contextKeyRendersTheEntrySnapshot() {
        assertEquals("request=r-29", render("request={context:request}", entry("ignored", null)));
    }

    /**
     * Verifies: TINY-FMT-010, TINY-CVI-002.
     * Seam: protocol handoff
     * Depends-On: contextProjectionPreservesEntries
     */
    @Test void missingContextKeyRendersConfiguredDefault() {
        assertEquals("none", render("{context:missing,none}", entry("ignored", null)));
    }

    /**
     * Verifies: TINY-FMT-006, TINY-FMT-009, TINY-CVI-005.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void literalPlaceholderTokensComposeAroundMessage() {
        assertEquals("{payload-29}|", render("{opening-curly-bracket}{message-only}{closing-curly-bracket}{pipe}", entry("payload-29", null)));
    }

    /**
     * Verifies: TINY-FMT-007, TINY-ERR-005.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void unknownPlaceholderRemainsRenderableBesideKnownToken() {
        String rendered = render("A{not-a-field}B{message-only}", entry("payload-29", null));
        assertEquals("Anot-a-fieldBpayload-29", rendered);
    }

    /**
     * Verifies: TINY-FMT-014, TINY-CVI-002.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void minimumSizePadsShortEntryProjection() {
        assertEquals("abc   !", render("{message-only|min-size=6}!", entry("abc", null)));
    }

    /**
     * Verifies: TINY-FMT-015, TINY-CVI-002.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void maximumSizeKeepsTrailingEntryProjection() {
        assertEquals("load-29", render("{message-only|max-size=7}", entry("payload-29", null)));
    }

    /**
     * Verifies: TINY-FMT-016, TINY-CVI-002.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void exactSizeTruncatesLongEntryProjection() {
        assertEquals("oad-29", render("{message-only|size=6}", entry("payload-29", null)));
    }

    /**
     * Verifies: TINY-FMT-017, TINY-CVI-005.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput
     */
    @Test void indentationStylesContinuationLines() {
        assertEquals("alpha\n   beta\n      gamma", render("{message-only|indent=3}", entry("alpha\nbeta\n\tgamma", null)));
    }

    /**
     * Verifies: TINY-FMT-013, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput, exceptionProjectionPreservesInput
     */
    @Test void messageOnlyOmitsAssociatedThrowable() {
        assertEquals("payload-29", render("{message-only}", entry("payload-29", new IllegalStateException("boom-visible"))));
    }

    /**
     * Verifies: TINY-FMT-013, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: messageProjectionPreservesInput, exceptionProjectionPreservesInput
     */
    @Test void messageIncludesAssociatedThrowableProjection() {
        String rendered = render("{message}", entry("payload-29", new IllegalStateException("boom-visible")));
        assertAll(
                () -> assertTrue(rendered.startsWith("payload-29")),
                () -> assertTrue(rendered.contains("IllegalStateException")),
                () -> assertTrue(rendered.contains("boom-visible")));
    }

    private static String render(String pattern, LogEntry logEntry) {
        return render(new FormatPatternParser(null).parse(pattern), logEntry);
    }

    private static String render(Token token, LogEntry logEntry) {
        StringBuilder builder = new StringBuilder();
        token.render(logEntry, builder);
        return builder.toString();
    }

    private static LogEntry entry(String message, Throwable exception) {
        Map<String, String> context = new LinkedHashMap<>();
        context.put("request", "r-29");
        return new LogEntry(null, Thread.currentThread(), context,
                "example.alpha.Worker", "execute", "Worker.java", 73,
                "audit", Level.INFO, message, exception);
    }
}
