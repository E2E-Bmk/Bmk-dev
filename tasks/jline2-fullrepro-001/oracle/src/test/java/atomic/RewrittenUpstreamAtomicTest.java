package atomic;

import jline.console.KillRing;
import jline.console.history.History;
import jline.console.history.MemoryHistory;
import org.junit.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

public class RewrittenUpstreamAtomicTest {
    private static List<String> values(MemoryHistory history) {
        List<String> values = new ArrayList<String>();
        for (History.Entry entry : history) {
            values.add(entry.value().toString());
        }
        return values;
    }

    /** Verifies: JLINE-HIST-001, JLINE-HIST-004. */
    @Test
    public void memoryAddsValueAndAdvancesIndex() {
        MemoryHistory history = new MemoryHistory();
        history.add("opal-entry");
        assertEquals(Arrays.asList("opal-entry"), values(history));
        assertEquals(1, history.index());
    }

    /** Verifies: JLINE-HIST-007. */
    @Test
    public void memoryReplaceChangesLastValue() {
        MemoryHistory history = new MemoryHistory();
        history.add("north");
        history.add("south");
        history.replace("west");
        assertEquals(Arrays.asList("north", "west"), values(history));
    }

    /** Verifies: JLINE-HIST-006. */
    @Test
    public void memorySetChangesIndexedValue() {
        MemoryHistory history = new MemoryHistory();
        history.add("zero");
        history.add("one");
        history.add("two");
        history.set(1, "middle");
        assertEquals(Arrays.asList("zero", "middle", "two"), values(history));
    }

    /** Verifies: JLINE-HIST-006. */
    @Test
    public void memoryRemoveChangesOrder() {
        MemoryHistory history = new MemoryHistory();
        history.add("red");
        history.add("green");
        history.add("blue");
        history.remove(1);
        assertEquals(Arrays.asList("red", "blue"), values(history));
    }

    /** Verifies: JLINE-HIST-006. */
    @Test
    public void memoryRemoveFirstRetainsTail() {
        MemoryHistory history = new MemoryHistory();
        history.add("first-x");
        history.add("second-x");
        history.add("third-x");
        history.removeFirst();
        assertEquals(Arrays.asList("second-x", "third-x"), values(history));
    }

    /** Verifies: JLINE-HIST-006. */
    @Test
    public void memoryRemoveLastRetainsPrefix() {
        MemoryHistory history = new MemoryHistory();
        history.add("first-y");
        history.add("second-y");
        history.add("third-y");
        history.removeLast();
        assertEquals(Arrays.asList("first-y", "second-y"), values(history));
    }

    /** Verifies: JLINE-SESS-036. */
    @Test
    public void emptyKillRingYankReturnsNull() {
        assertNull(new KillRing().yank());
    }

    /** Verifies: JLINE-SESS-035. */
    @Test
    public void consecutiveKillsConcatenateForward() {
        KillRing ring = new KillRing();
        ring.add("copper");
        ring.add("-trail");
        assertEquals("copper-trail", ring.yank());
    }

    /** Verifies: JLINE-SESS-036. */
    @Test
    public void yankPopWithoutYankReturnsNull() {
        KillRing ring = new KillRing();
        ring.add("stored-kill");
        assertNull(ring.yankPop());
    }

}


