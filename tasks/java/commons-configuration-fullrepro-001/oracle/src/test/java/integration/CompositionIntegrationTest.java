package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.CombinedConfiguration;
import org.apache.commons.configuration2.CompositeConfiguration;
import org.apache.commons.configuration2.Configuration;
import org.apache.commons.configuration2.event.ConfigurationEvent;
import org.apache.commons.configuration2.ex.ConfigurationRuntimeException;
import org.apache.commons.configuration2.tree.OverrideCombiner;
import org.junit.jupiter.api.Test;

class CompositionIntegrationTest {
    /**
     * Verifies: CC-COMP-002, CC-COMP-006, CC-COMP-008, CC-CVI-004
     * Depends-On: addConfigurationFirstRaisesPriority, keysFollowFirstInsertionOrderAndSizeCountsDistinctKeys
     */
    @Test void compositePrecedenceAgreesAcrossRawTypedAndKeyViews() {
        BaseConfiguration first = new BaseConfiguration(); first.setProperty("shared", "first"); first.setProperty("a", 1);
        BaseConfiguration second = new BaseConfiguration(); second.setProperty("shared", "second"); second.setProperty("b", 2);
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(first); c.addConfiguration(second);
        List<String> keys = new ArrayList<>(); c.getKeys().forEachRemaining(keys::add);
        assertAll(() -> assertEquals("first", c.getProperty("shared")), () -> assertEquals("first", c.getString("shared")),
                () -> assertEquals(Arrays.asList("shared", "a", "b"), keys));
    }

    /**
     * Verifies: CC-COMP-010, CC-COMP-011, CC-CVI-004
     * Depends-On: compositeSourceRequiresUniqueDefiningChild, addConfigurationFirstRaisesPriority
     */
    @Test void compositeSourceIsReportedOnlyForUniqueDefinition() {
        BaseConfiguration first = new BaseConfiguration(); first.setProperty("unique", "u"); first.setProperty("shared", "a");
        BaseConfiguration second = new BaseConfiguration(); second.setProperty("shared", "b");
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(first); c.addConfiguration(second);
        assertAll(() -> assertSame(first, c.getSource("unique")),
                () -> assertThrows(IllegalArgumentException.class, () -> c.getSource("shared")),
                () -> assertEquals("a", c.getString("shared")));
    }

    /**
     * Verifies: CC-COMP-005, CC-COMP-007
     * Depends-On: newCompositeOwnsWriteTarget, addPropertyAppendsInOrder
     */
    @Test void selectedInMemoryChildReceivesWritesAndExtendsList() {
        BaseConfiguration defaults = new BaseConfiguration(); defaults.addProperty("k", "default");
        BaseConfiguration writable = new BaseConfiguration(); writable.addProperty("k", "memory");
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(defaults); c.addConfiguration(writable, true);
        c.addProperty("k", "written");
        assertAll(() -> assertSame(writable, c.getInMemoryConfiguration()),
                () -> assertEquals(Arrays.asList("default", "memory", "written"), c.getList("k")));
    }

    /**
     * Verifies: CC-COMP-009
     * Depends-On: newCompositeOwnsWriteTarget, addConfigurationFirstRaisesPriority
     */
    @Test void activeInMemoryConfigurationCannotBeRemoved() {
        BaseConfiguration child = new BaseConfiguration(); child.setProperty("child", 1);
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(child);
        Configuration memory = c.getInMemoryConfiguration(); c.removeConfiguration(memory); c.removeConfiguration(child);
        c.setProperty("still", "works");
        assertAll(() -> assertSame(memory, c.getInMemoryConfiguration()), () -> assertEquals("works", c.getString("still")),
                () -> assertFalse(c.containsKey("child")));
    }

    /**
     * Verifies: CC-COMP-013, CC-COMP-015
     * Depends-On: combinedConfigurationDefaultsToUnionCombiner, addConfigurationFirstRaisesPriority
     */
    @Test void namedMountedChildrenCombineWithEarlierPrecedence() {
        BaseConfiguration first = new BaseConfiguration(); first.setProperty("value", "first");
        BaseConfiguration second = new BaseConfiguration(); second.setProperty("value", "second"); second.setProperty("extra", "yes");
        CombinedConfiguration c = new CombinedConfiguration(new OverrideCombiner());
        c.addConfiguration(first, "first", "root"); c.addConfiguration(second, "second", "root");
        assertAll(() -> assertSame(first, c.getConfiguration("first")), () -> assertEquals("first", c.getString("root.value")),
                () -> assertEquals("yes", c.getString("root.extra")));
    }

    /**
     * Verifies: CC-COMP-017, CC-COMP-019, CC-STATE-002
     * Depends-On: combinedConfigurationRejectsNullChildWithoutStateChange, configurationAtMissingSelectionThrows
     */
    @Test void duplicateCombinedNameFailsWithoutReplacingOriginal() {
        BaseConfiguration original = new BaseConfiguration(); original.setProperty("k", "old");
        BaseConfiguration duplicate = new BaseConfiguration(); duplicate.setProperty("k", "new");
        CombinedConfiguration c = new CombinedConfiguration(); c.addConfiguration(original, "same");
        assertThrows(ConfigurationRuntimeException.class, () -> c.addConfiguration(duplicate, "same"));
        assertAll(() -> assertEquals(1, c.getNumberOfConfigurations()), () -> assertSame(original, c.getConfiguration("same")));
        c.removeConfiguration("same");
        assertAll(() -> assertEquals(0, c.getNumberOfConfigurations()), () -> assertNull(c.getSource("k")));
    }

    /**
     * Verifies: CC-COMP-018, CC-CVI-006
     * Depends-On: combinedConfigurationDefaultsToUnionCombiner, eventRegistrationRejectsNullArguments
     */
    @Test void childChangeInvalidatesAndRebuildsCombinedView() {
        BaseConfiguration child = new BaseConfiguration(); child.setProperty("k", "old");
        CombinedConfiguration c = new CombinedConfiguration(); c.addConfiguration(child, "child");
        List<ConfigurationEvent> events = new ArrayList<>(); c.addEventListener(CombinedConfiguration.COMBINED_INVALIDATE, events::add);
        assertEquals("old", c.getString("k")); child.setProperty("k", "new");
        assertAll(() -> assertEquals(1, events.size()), () -> assertEquals("new", c.getString("k")));
    }

    /**
     * Verifies: CC-COMP-020, CC-COMP-021, CC-COMP-022, CC-COMP-023, CC-CVI-006
     * Depends-On: combinedConfigurationDefaultsToUnionCombiner, setPropertyReplacesAllOldValues
     */
    @Test void directCombinedValueIsTemporaryAcrossChildRebuild() {
        BaseConfiguration child = new BaseConfiguration(); child.setProperty("child", "one");
        CombinedConfiguration c = new CombinedConfiguration(); c.addConfiguration(child, "child");
        c.setProperty("temporary", "owned");
        assertAll(() -> assertEquals("owned", c.getString("temporary")),
                () -> assertSame(c, c.getSource("temporary")), () -> assertNull(c.getSource("unknown")),
                () -> assertThrows(IllegalArgumentException.class, () -> c.getSource(null)));
        child.setProperty("child", "two");
        assertAll(() -> assertFalse(c.containsKey("temporary")), () -> assertEquals("two", c.getString("child")));
    }
}
