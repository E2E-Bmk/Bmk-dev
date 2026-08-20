package atomic;

import jline.TerminalSupport;
import jline.UnsupportedTerminal;
import jline.console.CursorBuffer;
import jline.console.KeyMap;
import jline.console.Operation;
import jline.console.WCWidth;
import jline.console.completer.ArgumentCompleter.ArgumentList;
import jline.console.completer.EnumCompleter;
import jline.console.completer.NullCompleter;
import jline.console.completer.StringsCompleter;
import jline.console.history.History;
import jline.console.history.MemoryHistory;
import org.junit.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.ListIterator;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

public class GeneratedAtomicTest {
    private enum Shade {
        LIGHT_BLUE, DEEP_RED
    }

    private static KeyMap publicKeyMap() {
        return (KeyMap) KeyMap.keyMaps().get("emacs");
    }

    /** Verifies: JLINE-SESS-022, JLINE-SESS-023, JLINE-CVI-006. */
    @Test
    public void cursorBufferInsertsAtCursorAndAdvances() {
        CursorBuffer buffer = new CursorBuffer();
        buffer.write("acorn");
        buffer.cursor = 2;
        buffer.write("-mid-");
        assertEquals("ac-mid-orn", buffer.toString());
        assertEquals(7, buffer.cursor);
        assertEquals("ac-mid-", buffer.upToCursor());
    }

    /** Verifies: JLINE-SESS-022, JLINE-SESS-025, JLINE-CVI-006. */
    @Test
    public void cursorBufferBoundaryCharactersUseNullCharacter() {
        CursorBuffer buffer = new CursorBuffer();
        buffer.write("xy");
        buffer.cursor = 0;
        assertEquals('\0', buffer.current());
        assertEquals('x', buffer.nextChar());
        buffer.cursor = buffer.length();
        assertEquals('y', buffer.current());
        assertEquals('\0', buffer.nextChar());
    }

    /** Verifies: JLINE-SESS-022, JLINE-SESS-026, JLINE-CVI-006. */
    @Test
    public void cursorBufferClearReportsWhetherContentChanged() {
        CursorBuffer buffer = new CursorBuffer();
        buffer.write("erase-me");
        assertTrue(buffer.clear());
        assertEquals("", buffer.toString());
        assertEquals(0, buffer.cursor);
        assertFalse(buffer.clear());
    }

    /** Verifies: JLINE-SESS-022, JLINE-CVI-006. */
    @Test
    public void cursorBufferCopyHasIndependentState() {
        CursorBuffer original = new CursorBuffer();
        original.write("cedar");
        original.cursor = 3;
        CursorBuffer copy = original.copy();
        copy.write('X');
        assertEquals("cedar", original.toString());
        assertEquals(3, original.cursor);
        assertEquals("cedXar", copy.toString());
    }

    /** Verifies: JLINE-SESS-025, JLINE-ERR-003. */
    @Test(expected = NullPointerException.class)
    public void cursorBufferRejectsNullSequence() {
        new CursorBuffer().write((CharSequence) null);
    }

    /** Verifies: JLINE-SESS-039. */
    @Test
    public void keyMapReturnsNullForNullAndEmptySequences() {
        KeyMap map = publicKeyMap();
        assertNull(map.getBound(""));
        assertNull(map.getBound(null));
    }

    /** Verifies: JLINE-SESS-039. */
    @Test
    public void keyMapUsesSelfInsertAboveByteRange() {
        KeyMap map = publicKeyMap();
        assertEquals(Operation.SELF_INSERT, map.getBound("\u03bb"));
    }

    /** Verifies: JLINE-HIST-001, JLINE-HIST-002. */
    @Test
    public void memoryHistoryAutoTrimPrecedesDuplicateSuppression() {
        MemoryHistory history = new MemoryHistory();
        history.setAutoTrim(true);
        history.add("  violet  ");
        history.add("violet");
        assertEquals(1, history.size());
        assertEquals("violet", history.get(0).toString());
        assertEquals(1, history.index());
    }

    /** Verifies: JLINE-HIST-003, JLINE-HIST-004. */
    @Test
    public void memoryHistoryRetainsNewestDefaultWindow() {
        MemoryHistory history = new MemoryHistory();
        for (int i = 0; i < MemoryHistory.DEFAULT_MAX_SIZE + 2; i++) {
            history.add("entry-" + i);
        }
        assertEquals(MemoryHistory.DEFAULT_MAX_SIZE, history.size());
        assertEquals("entry-2", history.get(2).toString());
        assertEquals(MemoryHistory.DEFAULT_MAX_SIZE + 2, history.index());
    }

    /** Verifies: JLINE-HIST-005, JLINE-HIST-012. */
    @Test
    public void memoryHistoryClearResetsSequenceAndIndex() {
        MemoryHistory history = new MemoryHistory();
        history.add("one");
        history.add("two");
        history.clear();
        assertTrue(history.isEmpty());
        assertEquals(0, history.size());
        assertEquals(0, history.index());
        assertEquals("", history.current().toString());
    }

    /** Verifies: JLINE-HIST-012, JLINE-HIST-013, JLINE-HIST-014, JLINE-HIST-015. */
    @Test
    public void memoryHistoryNavigationHonorsBothBoundaries() {
        MemoryHistory history = new MemoryHistory();
        history.add("amber");
        history.add("bronze");
        assertTrue(history.previous());
        assertEquals("bronze", history.current().toString());
        assertTrue(history.previous());
        assertEquals("amber", history.current().toString());
        assertFalse(history.previous());
        assertTrue(history.next());
        assertTrue(history.next());
        assertEquals("", history.current().toString());
        assertFalse(history.next());
    }

    /** Verifies: JLINE-HIST-008, JLINE-ERR-003. */
    @Test(expected = NullPointerException.class)
    public void memoryHistoryRejectsNullItem() {
        new MemoryHistory().add(null);
    }

    /** Verifies: JLINE-HIST-009, JLINE-ERR-004. */
    @Test(expected = IndexOutOfBoundsException.class)
    public void memoryHistoryRejectsInvalidIndex() {
        new MemoryHistory().get(9);
    }

    /** Verifies: JLINE-HIST-010, JLINE-ERR-005. */
    @Test(expected = java.util.NoSuchElementException.class)
    public void memoryHistoryRejectsEmptyLastRemoval() {
        new MemoryHistory().removeLast();
    }

    /** Verifies: JLINE-HIST-011, JLINE-ERR-006. */
    @Test(expected = UnsupportedOperationException.class)
    public void memoryHistoryIteratorRejectsRemoval() {
        MemoryHistory history = new MemoryHistory();
        history.add("fixed");
        ListIterator<History.Entry> iterator = history.entries();
        iterator.next();
        iterator.remove();
    }

    /** Verifies: JLINE-COMP-005, JLINE-COMP-006. */
    @Test
    public void stringsCompleterSortsUniquelyAndMatchesPrefix() {
        StringsCompleter completer = new StringsCompleter("pearl", "pine", "pearl", "plum");
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(0, completer.complete("p", 1, candidates));
        assertEquals(Arrays.<CharSequence>asList("pearl", "pine", "plum"), candidates);
        assertEquals(Arrays.asList("pearl", "pine", "plum"),
                new ArrayList<String>(completer.getStrings()));
    }

    /** Verifies: JLINE-COMP-005, JLINE-COMP-006. */
    @Test
    public void stringsCompleterNullBufferReturnsEveryCandidate() {
        StringsCompleter completer = new StringsCompleter("zinc", "alder", "maple");
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(0, completer.complete(null, 0, candidates));
        assertEquals(Arrays.<CharSequence>asList("alder", "maple", "zinc"), candidates);
    }

    /** Verifies: JLINE-COMP-006. */
    @Test
    public void stringsCompleterNoMatchReturnsMinusOne() {
        StringsCompleter completer = new StringsCompleter("cedar", "birch");
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(-1, completer.complete("qu", 2, candidates));
        assertEquals(Collections.emptyList(), candidates);
    }

    /** Verifies: JLINE-COMP-011, JLINE-ERR-003. */
    @Test(expected = NullPointerException.class)
    public void stringsCompleterRejectsNullCandidateList() {
        new StringsCompleter("elm").complete("e", 1, null);
    }

    /** Verifies: JLINE-COMP-008. */
    @Test
    public void enumCompleterUsesLowerCaseByDefault() {
        EnumCompleter completer = new EnumCompleter(Shade.class);
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(0, completer.complete("d", 1, candidates));
        assertEquals(Arrays.<CharSequence>asList("deep_red"), candidates);
    }

    /** Verifies: JLINE-COMP-008. */
    @Test
    public void enumCompleterCanPreserveConstantCase() {
        EnumCompleter completer = new EnumCompleter(Shade.class, false);
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(0, completer.complete("L", 1, candidates));
        assertEquals(Arrays.<CharSequence>asList("LIGHT_BLUE"), candidates);
    }

    /** Verifies: JLINE-COMP-009. */
    @Test
    public void nullCompleterAlwaysDeclinesWithoutCandidates() {
        List<CharSequence> candidates = new ArrayList<CharSequence>();
        assertEquals(-1, NullCompleter.INSTANCE.complete("anything", 4, candidates));
        assertEquals(Collections.emptyList(), candidates);
    }

    /** Verifies: JLINE-COMP-017, JLINE-COMP-018. */
    @Test
    public void argumentListAccessorsTrackUpdatedProjection() {
        ArgumentList list = new ArgumentList(new String[]{"oak", "ash"}, 1, 2, 6);
        assertArrayEquals(new String[]{"oak", "ash"}, list.getArguments());
        assertEquals(1, list.getCursorArgumentIndex());
        assertEquals("ash", list.getCursorArgument());
        assertEquals(2, list.getArgumentPosition());
        assertEquals(6, list.getBufferPosition());
        list.setCursorArgumentIndex(4);
        assertNull(list.getCursorArgument());
    }

    /** Verifies: JLINE-TERM-002. */
    @Test
    public void terminalSupportExposesDeterministicDefaults() {
        TerminalSupport terminal = new TerminalSupport(true) { };
        assertTrue(terminal.isSupported());
        assertEquals(80, terminal.getWidth());
        assertEquals(24, terminal.getHeight());
        assertNull(terminal.getOutputEncoding());
    }

    /** Verifies: JLINE-TERM-004. */
    @Test
    public void unsupportedTerminalDefaultFlagsAreStable() {
        UnsupportedTerminal terminal = new UnsupportedTerminal();
        assertFalse(terminal.isSupported());
        assertFalse(terminal.isAnsiSupported());
        assertTrue(terminal.isEchoEnabled());
    }

    /** Verifies: JLINE-TERM-004. */
    @Test
    public void unsupportedTerminalHonorsExplicitFlags() {
        UnsupportedTerminal terminal = new UnsupportedTerminal(true, false);
        assertFalse(terminal.isSupported());
        assertTrue(terminal.isAnsiSupported());
        assertFalse(terminal.isEchoEnabled());
        terminal.setEchoEnabled(true);
        assertTrue(terminal.isEchoEnabled());
    }

    /** Verifies: JLINE-TERM-013. */
    @Test
    public void wcWidthDistinguishesNullControlsAndPrintableText() {
        assertEquals(0, WCWidth.wcwidth(0));
        assertEquals(-1, WCWidth.wcwidth(0x1f));
        assertEquals(-1, WCWidth.wcwidth(0x7f));
        assertEquals(1, WCWidth.wcwidth('Q'));
    }

    /** Verifies: JLINE-TERM-013. */
    @Test
    public void wcWidthDistinguishesCombiningAndWideCodePoints() {
        assertEquals(0, WCWidth.wcwidth(0x0301));
        assertEquals(2, WCWidth.wcwidth(0x4e2d));
        assertEquals(1, WCWidth.wcwidth(0x03bb));
    }
}


