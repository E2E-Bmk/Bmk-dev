package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Arrays;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.BaseHierarchicalConfiguration;
import org.apache.commons.configuration2.Configuration;
import org.apache.commons.configuration2.SubsetConfiguration;
import org.apache.commons.configuration2.ex.ConfigurationRuntimeException;
import org.junit.jupiter.api.Test;

class ViewAtomicTest {
    /** Verifies: CC-VIEW-001, CC-VIEW-003 */
    @Test void subsetUsesDelimiterBoundaryAndStripsPrefix() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("app.name", "good"); c.setProperty("apple", "bad");
        Configuration s = c.subset("app");
        assertAll(() -> assertEquals("good", s.getString("name")), () -> assertFalse(s.containsKey("le")));
    }

    /** Verifies: CC-VIEW-002 */
    @Test void exactPrefixAppearsAsEmptyKey() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("app", "root");
        assertEquals("root", c.subset("app").getString(""));
    }

    /** Verifies: CC-VIEW-004 */
    @Test void customAndNullSubsetDelimitersTranslateKeys() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("app/name", "slash"); c.setProperty("appname", "joined");
        assertAll(() -> assertEquals("slash", new SubsetConfiguration(c, "app", "/").getString("name")),
                () -> assertEquals("joined", new SubsetConfiguration(c, "app", null).getString("name")));
    }

    /** Verifies: CC-VIEW-010, CC-VIEW-011 */
    @Test void hierarchicalIndicesAreZeroBasedAndMaxIndexIsGreatest() {
        BaseHierarchicalConfiguration c = new BaseHierarchicalConfiguration();
        c.setProperty("servers.server(0).name", "a"); c.setProperty("servers.server(1).name", "b");
        assertAll(() -> assertEquals(1, c.getMaxIndex("servers.server")),
                () -> assertEquals("b", c.getString("servers.server(1).name")));
    }

    /** Verifies: CC-VIEW-015 */
    @Test void configurationAtMissingSelectionThrows() {
        BaseHierarchicalConfiguration c = new BaseHierarchicalConfiguration(); c.setProperty("kept", "v");
        assertAll(() -> assertThrows(ConfigurationRuntimeException.class, () -> c.configurationAt("missing")),
                () -> assertEquals("v", c.getString("kept")));
    }

    /** Verifies: CC-VIEW-016 */
    @Test void configurationsAtMissingSelectionIsEmpty() {
        BaseHierarchicalConfiguration c = new BaseHierarchicalConfiguration();
        assertTrue(c.configurationsAt("missing").isEmpty());
    }

    /** Verifies: CC-VIEW-021 */
    @Test void clearTreeRemovesNodeAndDescendantsOnly() {
        BaseHierarchicalConfiguration c = new BaseHierarchicalConfiguration();
        c.setProperty("root.child.value", 1); c.setProperty("other", 2); c.clearTree("root.child");
        ArrayList<String> keys = new ArrayList<>(); c.getKeys().forEachRemaining(keys::add);
        assertAll(() -> assertEquals(Arrays.asList("other"), keys), () -> assertEquals(2, c.getInt("other")));
    }
}
