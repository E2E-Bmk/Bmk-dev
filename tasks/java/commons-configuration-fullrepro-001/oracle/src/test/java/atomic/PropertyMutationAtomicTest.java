package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.configuration2.BaseConfiguration;
import org.junit.jupiter.api.Test;

class PropertyMutationAtomicTest {
    /** Verifies: CC-PROP-001 */
    @Test void emptyConfigurationHasNoState() {
        BaseConfiguration c = new BaseConfiguration();
        assertAll(() -> assertTrue(c.isEmpty()), () -> assertEquals(0, c.size()),
                () -> assertFalse(c.getKeys().hasNext()));
    }

    /** Verifies: CC-PROP-002 */
    @Test void setPropertyReplacesAllOldValues() {
        BaseConfiguration c = new BaseConfiguration();
        c.addProperty("k", "old1"); c.addProperty("k", "old2"); c.setProperty("k", "new");
        assertAll(() -> assertEquals("new", c.getProperty("k")),
                () -> assertEquals(Arrays.asList("new"), c.getList("k")));
    }

    /** Verifies: CC-PROP-003 */
    @Test void addPropertyStoresMissingScalar() {
        BaseConfiguration c = new BaseConfiguration(); c.addProperty("k", 7);
        assertEquals(7, c.getProperty("k"));
    }

    /** Verifies: CC-PROP-004 */
    @Test void addPropertyAppendsInOrder() {
        BaseConfiguration c = new BaseConfiguration();
        c.addProperty("k", "a"); c.addProperty("k", "b"); c.addProperty("k", "c");
        assertEquals(Arrays.asList("a", "b", "c"), c.getList("k"));
    }

    /** Verifies: CC-PROP-005, CC-STATE-001 */
    @Test void clearingMissingPropertyPreservesOtherState() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("kept", "v");
        c.clearProperty("absent");
        assertAll(() -> assertEquals(1, c.size()), () -> assertEquals("v", c.getString("kept")));
    }

    /** Verifies: CC-PROP-006 */
    @Test void clearRemovesEveryProperty() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("a", 1); c.setProperty("b", 2);
        c.clear();
        assertAll(() -> assertTrue(c.isEmpty()), () -> assertEquals(0, c.size()));
    }

    /** Verifies: CC-PROP-008 */
    @Test void keysFollowFirstInsertionOrderAndSizeCountsDistinctKeys() {
        BaseConfiguration c = new BaseConfiguration();
        c.setProperty("b", 1); c.setProperty("a", 2); c.addProperty("b", 3); c.setProperty("c", 4);
        List<String> keys = new ArrayList<>(); c.getKeys().forEachRemaining(keys::add);
        assertAll(() -> assertEquals(Arrays.asList("b", "a", "c"), keys), () -> assertEquals(3, c.size()));
    }
}
