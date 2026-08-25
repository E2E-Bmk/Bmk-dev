package integration;

import jline.DefaultTerminal2;
import jline.TerminalFactory;
import jline.TerminalSupport;
import jline.UnsupportedTerminal;
import jline.console.ConsoleReader;
import jline.console.CursorBuffer;
import jline.console.UserInterruptException;
import jline.console.completer.AggregateCompleter;
import jline.console.completer.ArgumentCompleter;
import jline.console.completer.CandidateListCompletionHandler;
import jline.console.completer.Completer;
import jline.console.completer.StringsCompleter;
import jline.console.history.FileHistory;
import jline.console.history.History;
import jline.console.history.MemoryHistory;
import org.junit.After;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import support.OracleSupport;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotSame;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

public class GeneratedIntegrationTest {
    @Rule
    public TemporaryFolder temporary = new TemporaryFolder();

    @After
    public void restoreTerminalFactory() {
        TerminalFactory.reset();
        TerminalFactory.configure("auto");
    }

    /**
     * Verifies: JLINE-SESS-005, JLINE-CVI-001.
     * Seam: state consistency across accepted line, history, and cursor buffer.
     * Depends-On: memoryAddsValueAndAdvancesIndex, cursorBufferClearReportsWhetherContentChanged
     */
    @Test
    public void acceptedLineMatchesHistoryAndResetsBuffer() throws Exception {
        OracleSupport.Session session = OracleSupport.session("topaz-line\n");
        MemoryHistory history = new MemoryHistory();
        session.reader.setHistory(history);
        assertEquals("topaz-line", session.reader.readLine());
        assertEquals(Collections.singletonList("topaz-line"), OracleSupport.values(history));
        assertEquals(history.size(), history.index());
        assertEquals("", session.reader.getCursorBuffer().toString());
        assertEquals(0, session.reader.getCursorBuffer().cursor);
    }

    /**
     * Verifies: JLINE-SESS-018, JLINE-CVI-001.
     * Seam: config interaction between literal event text and accepted-line history state.
     * Depends-On: memoryAddsValueAndAdvancesIndex, cursorBufferClearReportsWhetherContentChanged
     */
    @Test
    public void disabledExpansionPreservesEventMarkersAcrossViews() throws Exception {
        OracleSupport.Session session = OracleSupport.session("!quartz ^old^new^\n");
        MemoryHistory history = new MemoryHistory();
        session.reader.setHistory(history);
        session.reader.setExpandEvents(false);
        assertEquals("!quartz ^old^new^", session.reader.readLine());
        assertEquals(Collections.singletonList("!quartz ^old^new^"), OracleSupport.values(history));
        assertEquals("", session.reader.getCursorBuffer().toString());
    }

    /**
     * Verifies: JLINE-SESS-008, JLINE-CVI-008.
     * Seam: protocol handoff across CRLF boundaries on an unsupported terminal.
     * Depends-On: unsupportedTerminalDefaultFlagsAreStable, memoryAddsValueAndAdvancesIndex
     */
    @Test
    public void unsupportedTerminalConsumesPairedLineFeedOnce() throws Exception {
        OracleSupport.Session session = OracleSupport.session(
                "north\r\nsouth\n", new UnsupportedTerminal());
        MemoryHistory history = new MemoryHistory();
        session.reader.setHistory(history);
        assertEquals("north", session.reader.readLine());
        assertEquals("south", session.reader.readLine());
        assertEquals(Arrays.asList("north", "south"), OracleSupport.values(history));
    }

    /**
     * Verifies: JLINE-SESS-007, JLINE-CVI-008.
     * Seam: protocol handoff from stream EOF to returned line and buffer reset.
     * Depends-On: unsupportedTerminalDefaultFlagsAreStable, cursorBufferClearReportsWhetherContentChanged
     */
    @Test
    public void unsupportedTerminalReturnsFinalPartialLineAtEof() throws Exception {
        OracleSupport.Session session = OracleSupport.session(
                "final-ember", new UnsupportedTerminal());
        assertEquals("final-ember", session.reader.readLine());
        assertEquals("", session.reader.getCursorBuffer().toString());
        assertEquals(0, session.reader.getCursorBuffer().cursor);
    }

    /**
     * Verifies: JLINE-SESS-014, JLINE-ERR-002.
     * Seam: error propagation from the terminal interrupt binding through the reader to its public exception payload.
     * Depends-On: cursorBufferInsertsAtCursorAndAdvances, terminalSupportExposesDeterministicDefaults
     */
    @Test
    public void handledUserInterruptCarriesPartialLine() throws Exception {
        OracleSupport.Session session = OracleSupport.session("partial-ember\u0003");
        session.reader.setHandleUserInterrupt(true);
        try {
            session.reader.readLine();
            fail("handled Ctrl-C must raise UserInterruptException");
        } catch (UserInterruptException expected) {
            assertEquals("partial-ember", expected.getPartialLine());
        }
    }

    /**
     * Verifies: JLINE-HIST-016, JLINE-HIST-020, JLINE-CVI-003.
     * Seam: lifecycle crossing from in-memory additions through file flush and reload.
     * Depends-On: memoryAddsValueAndAdvancesIndex, memoryHistoryNavigationHonorsBothBoundaries
     */
    @Test
    public void fileHistoryFlushReloadsValuesInOrder() throws Exception {
        File target = new File(temporary.getRoot(), "nested/a/history.txt");
        FileHistory writer = new FileHistory(target, false);
        writer.add("silver");
        writer.add("cobalt");
        writer.flush();
        FileHistory reader = new FileHistory(target);
        assertEquals(Arrays.asList("silver", "cobalt"), OracleSupport.values(reader));
        assertEquals(target.getAbsoluteFile(), reader.getFile());
    }

    /**
     * Verifies: JLINE-HIST-018, JLINE-HIST-020, JLINE-CVI-003.
     * Seam: state consistency when a later flush replaces the prior file projection.
     * Depends-On: memoryRemoveChangesOrder, memoryHistoryClearResetsSequenceAndIndex
     */
    @Test
    public void fileHistorySecondFlushReplacesPriorProjection() throws Exception {
        File target = temporary.newFile("replace-history.txt");
        FileHistory history = new FileHistory(target, false);
        history.add("obsolete");
        history.flush();
        history.clear();
        history.add("current-a");
        history.add("current-b");
        history.flush();
        assertEquals(Arrays.asList("current-a", "current-b"),
                Files.readAllLines(target.toPath(), StandardCharsets.UTF_8));
        assertEquals(Arrays.asList("current-a", "current-b"),
                OracleSupport.values(new FileHistory(target)));
    }

    /**
     * Verifies: JLINE-HIST-005, JLINE-HIST-007, JLINE-HIST-020, JLINE-CVI-003.
     * Seam: an in-memory last-entry replacement must survive flush and construction reload.
     * Depends-On: memoryAddsValueAndAdvancesIndex, memoryReplaceChangesLastValue
     */
    @Test
    public void fileHistoryReplacePersistsThroughReload() throws Exception {
        File target = temporary.newFile("replace-entry-history.txt");
        FileHistory history = new FileHistory(target, false);
        history.add("anchor");
        history.add("old-tail");
        history.replace("new-tail");
        assertEquals(Arrays.asList("anchor", "new-tail"), OracleSupport.values(history));
        history.flush();

        FileHistory reloaded = new FileHistory(target);
        assertEquals(Arrays.asList("anchor", "new-tail"), OracleSupport.values(reloaded));
        assertEquals("new-tail", reloaded.get(1).toString());
    }

    /**
     * Verifies: JLINE-HIST-021, JLINE-CVI-003.
     * Seam: lifecycle crossing from persisted history to purge of both views.
     * Depends-On: memoryHistoryClearResetsSequenceAndIndex, memoryAddsValueAndAdvancesIndex
     */
    @Test
    public void fileHistoryPurgeClearsMemoryAndDeletesFile() throws Exception {
        File target = temporary.newFile("purge-history.txt");
        FileHistory history = new FileHistory(target, false);
        history.add("temporary-entry");
        history.flush();
        assertTrue(target.isFile());
        history.purge();
        assertEquals(0, history.size());
        assertFalse(target.exists());
    }

    /**
     * Verifies: JLINE-COMP-022, JLINE-CVI-004.
     * Seam: protocol handoff from completion candidate and offset to reader buffer state.
     * Depends-On: stringsCompleterSortsUniquelyAndMatchesPrefix, cursorBufferInsertsAtCursorAndAdvances
     */
    @Test
    public void singleCandidateHandlerUpdatesBufferAndCursor() throws Exception {
        OracleSupport.Session session = OracleSupport.session("");
        session.reader.getCursorBuffer().write("ra");
        CandidateListCompletionHandler handler = new CandidateListCompletionHandler();
        assertTrue(handler.complete(session.reader,
                Collections.<CharSequence>singletonList("raven"), 0));
        assertEquals("raven ", session.reader.getCursorBuffer().toString());
        assertEquals(6, session.reader.getCursorBuffer().cursor);
    }

    /**
     * Verifies: JLINE-COMP-002, JLINE-COMP-022, JLINE-CVI-004.
     * Seam: protocol handoff from completer through handler to accepted-line history.
     * Depends-On: stringsCompleterSortsUniquelyAndMatchesPrefix, memoryAddsValueAndAdvancesIndex
     */
    @Test
    public void tabCompletionFlowsIntoAcceptedLineAndHistory() throws Exception {
        OracleSupport.Session session = OracleSupport.session("ru\t\n");
        MemoryHistory history = new MemoryHistory();
        session.reader.setHistory(history);
        session.reader.addCompleter(new StringsCompleter("ruby"));
        assertEquals("ruby ", session.reader.readLine());
        assertEquals(Collections.singletonList("ruby "), OracleSupport.values(history));
        assertEquals("", session.reader.getCursorBuffer().toString());
    }

    /**
     * Verifies: JLINE-COMP-023, JLINE-CVI-004.
     * Seam: state consistency when an identical sole candidate leaves the reader unchanged.
     * Depends-On: stringsCompleterSortsUniquelyAndMatchesPrefix, cursorBufferInsertsAtCursorAndAdvances
     */
    @Test
    public void identicalCandidateLeavesBufferUnchanged() throws Exception {
        OracleSupport.Session session = OracleSupport.session("");
        session.reader.getCursorBuffer().write("cedar");
        CandidateListCompletionHandler handler = new CandidateListCompletionHandler();
        handler.setPrintSpaceAfterFullCompletion(false);
        assertFalse(handler.complete(session.reader,
                Collections.<CharSequence>singletonList("cedar"), 0));
        assertEquals("cedar", session.reader.getCursorBuffer().toString());
        assertEquals(5, session.reader.getCursorBuffer().cursor);
    }

    /**
     * Verifies: JLINE-HIST-005, JLINE-HIST-013, JLINE-CVI-002.
     * Seam: state consistency across entry iteration, indexed access, and navigation.
     * Depends-On: memoryAddsValueAndAdvancesIndex, memoryHistoryNavigationHonorsBothBoundaries
     */
    @Test
    public void historyEntriesAgreeWithIndexedAccessAndNavigation() {
        MemoryHistory history = OracleSupport.history("fir", "fable", "frost");
        for (History.Entry entry : history) {
            assertEquals(entry.value().toString(), history.get(entry.index()).toString());
        }
        assertTrue(history.previous());
        assertEquals("frost", history.current().toString());
        assertEquals("frost", history.get(history.index()).toString());
    }

    /**
     * Verifies: JLINE-HIST-005, JLINE-CVI-002.
     * Seam: state consistency after removal across iteration, public entry indices, and indexed access.
     * Depends-On: memoryRemoveFirstRetainsTail, memoryAddsValueAndAdvancesIndex
     */
    @Test
    public void retainedEntryIndicesDriveNavigationAfterRemoval() {
        MemoryHistory history = OracleSupport.history("red", "green", "blue");
        history.removeFirst();
        for (History.Entry entry : history) {
            assertEquals(entry.value().toString(), history.get(entry.index()).toString());
        }
        assertEquals(Arrays.asList("green", "blue"), OracleSupport.values(history));
    }

    /**
     * Verifies: JLINE-SESS-027, JLINE-SESS-029, JLINE-CVI-006.
     * Seam: state consistency between reader backspace and cursor-buffer projections.
     * Depends-On: cursorBufferInsertsAtCursorAndAdvances, cursorBufferBoundaryCharactersUseNullCharacter
     */
    @Test
    public void readerBackspaceKeepsCursorBufferViewsConsistent() throws Exception {
        OracleSupport.Session session = OracleSupport.session("");
        CursorBuffer buffer = session.reader.getCursorBuffer();
        buffer.write("abcd");
        buffer.cursor = 2;
        assertTrue(session.reader.backspace());
        assertEquals("acd", buffer.toString());
        assertEquals(1, buffer.cursor);
        assertEquals("a", buffer.upToCursor());
        assertEquals('a', buffer.current());
        assertEquals('c', buffer.nextChar());
    }

    /**
     * Verifies: JLINE-SESS-023, JLINE-SESS-030, JLINE-CVI-006.
     * Seam: state consistency from reader kill operation through public buffer restoration.
     * Depends-On: consecutiveKillsConcatenateForward, cursorBufferInsertsAtCursorAndAdvances
     */
    @Test
    public void readerKillAndPublicBufferRestoreOneState() throws Exception {
        OracleSupport.Session session = OracleSupport.session("");
        CursorBuffer buffer = session.reader.getCursorBuffer();
        buffer.write("stonework");
        buffer.cursor = 5;
        assertTrue(session.reader.killLine());
        assertEquals("stone", buffer.toString());
        buffer.write("work");
        assertEquals("stonework", buffer.toString());
        assertEquals(9, buffer.cursor);
    }

    /**
     * Verifies: JLINE-TERM-005, JLINE-TERM-006, JLINE-CVI-007.
     * Seam: state consistency between wrapped terminal projections and adapter projections.
     * Depends-On: terminalSupportExposesDeterministicDefaults
     */
    @Test
    public void defaultTerminalAdapterPreservesBaseProjections() {
        RecordingTerminal base = new RecordingTerminal();
        DefaultTerminal2 adapter = new DefaultTerminal2(base);
        assertEquals(base.isSupported(), adapter.isSupported());
        assertEquals(base.getWidth(), adapter.getWidth());
        assertEquals(base.getHeight(), adapter.getHeight());
        assertEquals(base.isEchoEnabled(), adapter.isEchoEnabled());
        assertEquals(base.getOutputEncoding(), adapter.getOutputEncoding());
        assertEquals(null, adapter.getNumericCapability("columns"));
    }

    /**
     * Verifies: JLINE-TERM-005, JLINE-CVI-007.
     * Seam: state consistency across base and adapter echo mutations.
     * Depends-On: terminalSupportExposesDeterministicDefaults
     */
    @Test
    public void defaultTerminalAdapterSharesEchoStateWithBase() {
        RecordingTerminal base = new RecordingTerminal();
        DefaultTerminal2 adapter = new DefaultTerminal2(base);
        adapter.setEchoEnabled(true);
        assertTrue(base.isEchoEnabled());
        base.setEchoEnabled(false);
        assertFalse(adapter.isEchoEnabled());
    }

    /**
     * Verifies: JLINE-COMP-010.
     * Seam: protocol handoff chooses candidates from children sharing the greatest offset.
     * Depends-On: stringsCompleterNoMatchReturnsMinusOne, nullCompleterAlwaysDeclinesWithoutCandidates
     */
    @Test
    public void aggregateCompleterKeepsOnlyGreatestOffsetCandidates() {
        Completer fromStart = new Completer() {
            public int complete(String buffer, int cursor, List<CharSequence> candidates) {
                candidates.add("root-choice");
                return 0;
            }
        };
        Completer fromSuffix = new Completer() {
            public int complete(String buffer, int cursor, List<CharSequence> candidates) {
                candidates.add("suffix-choice");
                return 2;
            }
        };
        AggregateCompleter aggregate = new AggregateCompleter(fromStart, fromSuffix);
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(2, aggregate.complete("xxs", 3, candidates));
        assertEquals(Collections.<CharSequence>singletonList("suffix-choice"), candidates);
    }

    /**
     * Verifies: JLINE-COMP-012, JLINE-COMP-013, JLINE-COMP-014, JLINE-COMP-016.
     * Seam: config interaction between argument tokenization and ordered child completers.
     * Depends-On: stringsCompleterSortsUniquelyAndMatchesPrefix, stringsCompleterNoMatchReturnsMinusOne
     */
    @Test
    public void argumentCompleterGatesLaterCandidateOnExactEarlierArgument() {
        ArgumentCompleter completer = new ArgumentCompleter(
                new StringsCompleter("git"), new StringsCompleter("stash", "status"));
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(4, completer.complete("git st", 6, candidates));
        assertEquals(Arrays.<CharSequence>asList("stash", "status"), candidates);
        candidates.clear();
        assertEquals(-1, completer.complete("g st", 4, candidates));
        assertEquals(Collections.emptyList(), candidates);
    }

    /**
     * Verifies: JLINE-COMP-003.
     * Seam: state consistency across reader mutation and unmodifiable completer view.
     * Depends-On: stringsCompleterNoMatchReturnsMinusOne
     */
    @Test
    public void readerCompleterCollectionReportsChangesAndProtectsView() throws Exception {
        OracleSupport.Session session = OracleSupport.session("");
        StringsCompleter completer = new StringsCompleter("iris");
        assertTrue(session.reader.addCompleter(completer));
        Collection<Completer> view = session.reader.getCompleters();
        assertEquals(Collections.<Completer>singletonList(completer), new ArrayList<Completer>(view));
        try {
            view.add(new StringsCompleter("lily"));
            fail("completer view must reject mutation");
        } catch (UnsupportedOperationException expected) {
            assertEquals(1, session.reader.getCompleters().size());
        }
        assertTrue(session.reader.removeCompleter(completer));
        assertFalse(session.reader.removeCompleter(completer));
    }

    /**
     * Verifies: JLINE-SESS-011.
     * Seam: config interaction between returned line and disabled history projection.
     * Depends-On: memoryHistoryClearResetsSequenceAndIndex
     */
    @Test
    public void disabledHistoryReturnsLineWithoutRecordingIt() throws Exception {
        OracleSupport.Session session = OracleSupport.session("untracked\n");
        MemoryHistory history = new MemoryHistory();
        session.reader.setHistory(history);
        session.reader.setHistoryEnabled(false);
        assertEquals("untracked", session.reader.readLine());
        assertEquals(Collections.emptyList(), OracleSupport.values(history));
        assertEquals("", session.reader.getCursorBuffer().toString());
    }

    /**
     * Verifies: JLINE-SESS-009, JLINE-SESS-010.
     * Seam: config interaction between masked echo, returned text, and history exclusion.
     * Depends-On: memoryHistoryClearResetsSequenceAndIndex
     */
    @Test
    public void maskedLineEchoesMaskAndSkipsHistory() throws Exception {
        OracleSupport.Session session = OracleSupport.session("secret\n");
        MemoryHistory history = new MemoryHistory();
        session.reader.setHistory(history);
        assertEquals("secret", session.reader.readLine('*'));
        assertEquals(Collections.emptyList(), OracleSupport.values(history));
        assertTrue(new String(session.output.toByteArray(), StandardCharsets.UTF_8).contains("******"));
    }

    /**
     * Verifies: JLINE-SESS-014, JLINE-SESS-021.
     * Seam: config interaction between bell setting and observable output stream.
     * Depends-On: terminalSupportExposesDeterministicDefaults
     */
    @Test
    public void bellSettingControlsOutputSideEffect() throws Exception {
        OracleSupport.Session session = OracleSupport.session("");
        session.reader.setBellEnabled(false);
        session.reader.beep();
        assertEquals(0, session.output.size());
        session.reader.setBellEnabled(true);
        session.reader.beep();
        byte[] bytes = session.output.toByteArray();
        assertEquals(1, bytes.length);
        assertEquals((byte) ConsoleReader.KEYBOARD_BELL, bytes[0]);
    }

    /**
     * Verifies: JLINE-TERM-007, JLINE-TERM-008.
     * Seam: config interaction from factory selector to constructed terminal behavior.
     * Depends-On: unsupportedTerminalDefaultFlagsAreStable
     */
    @Test
    public void terminalFactoryOffSelectorCreatesUnsupportedTerminal() {
        TerminalFactory.configure("off");
        assertTrue(TerminalFactory.create() instanceof UnsupportedTerminal);
    }

    /**
     * Verifies: JLINE-TERM-010.
     * Seam: lifecycle crossing across factory cache lookup and conditional reset.
     * Depends-On: unsupportedTerminalDefaultFlagsAreStable
     */
    @Test
    public void terminalFactoryResetIfReplacesOnlyCachedInstance() {
        TerminalFactory.configure("none");
        jline.Terminal first = TerminalFactory.get();
        assertSame(first, TerminalFactory.get());
        TerminalFactory.resetIf(new UnsupportedTerminal());
        assertSame(first, TerminalFactory.get());
        TerminalFactory.resetIf(first);
        assertNotSame(first, TerminalFactory.get());
    }

    private static final class RecordingTerminal extends TerminalSupport {
        private RecordingTerminal() {
            super(true);
            setEchoEnabled(false);
        }

        @Override
        public int getWidth() {
            return 93;
        }

        @Override
        public int getHeight() {
            return 41;
        }

        @Override
        public String getOutputEncoding() {
            return "UTF-8";
        }
    }
}


