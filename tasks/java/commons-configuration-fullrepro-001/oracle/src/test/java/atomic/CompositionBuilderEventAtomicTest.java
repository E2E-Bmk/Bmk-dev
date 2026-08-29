package atomic;

import static org.junit.jupiter.api.Assertions.*;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.CombinedConfiguration;
import org.apache.commons.configuration2.CompositeConfiguration;
import org.apache.commons.configuration2.builder.BasicConfigurationBuilder;
import org.apache.commons.configuration2.event.ConfigurationErrorEvent;
import org.apache.commons.configuration2.event.ConfigurationEvent;
import org.apache.commons.configuration2.tree.UnionCombiner;
import org.junit.jupiter.api.Test;

class CompositionBuilderEventAtomicTest {
    /** Verifies: CC-COMP-001, CC-COMP-004 */
    @Test void newCompositeOwnsWriteTarget() {
        CompositeConfiguration c = new CompositeConfiguration(); c.setProperty("written", "yes");
        assertAll(() -> assertNotNull(c.getInMemoryConfiguration()),
                () -> assertEquals("yes", c.getInMemoryConfiguration().getString("written")));
    }

    /** Verifies: CC-COMP-003 */
    @Test void addConfigurationFirstRaisesPriority() {
        BaseConfiguration low = new BaseConfiguration(); low.setProperty("k", "low");
        BaseConfiguration high = new BaseConfiguration(); high.setProperty("k", "high");
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(low); c.addConfigurationFirst(high);
        assertEquals("high", c.getString("k"));
    }

    /** Verifies: CC-COMP-010, CC-COMP-011 */
    @Test void compositeSourceRequiresUniqueDefiningChild() {
        BaseConfiguration one = new BaseConfiguration(); one.setProperty("unique", 1); one.setProperty("shared", 1);
        BaseConfiguration two = new BaseConfiguration(); two.setProperty("shared", 2);
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(one); c.addConfiguration(two);
        assertAll(() -> assertSame(one, c.getSource("unique")), () -> assertNull(c.getSource("absent")),
                () -> assertThrows(IllegalArgumentException.class, () -> c.getSource("shared")),
                () -> assertThrows(IllegalArgumentException.class, () -> c.getSource(null)));
    }

    /** Verifies: CC-COMP-012, CC-COMP-024 */
    @Test void combinedConfigurationDefaultsToUnionCombiner() {
        CombinedConfiguration c = new CombinedConfiguration();
        assertTrue(c.getNodeCombiner() instanceof UnionCombiner);
        assertThrows(IllegalArgumentException.class, () -> c.setNodeCombiner(null));
    }

    /** Verifies: CC-COMP-016, CC-STATE-002 */
    @Test void combinedConfigurationRejectsNullChildWithoutStateChange() {
        CombinedConfiguration c = new CombinedConfiguration();
        assertThrows(IllegalArgumentException.class, () -> c.addConfiguration(null));
        assertEquals(0, c.getNumberOfConfigurations());
    }

    /** Verifies: CC-EVT-006, CC-EVT-007, CC-EVT-008 */
    @Test void eventRegistrationRejectsNullArguments() {
        BaseConfiguration c = new BaseConfiguration();
        RuntimeException cause = new RuntimeException("cause-object");
        ConfigurationErrorEvent error = new ConfigurationErrorEvent(c, ConfigurationErrorEvent.WRITE,
                ConfigurationEvent.SET_PROPERTY, "k", "v", cause);
        assertAll(() -> assertThrows(IllegalArgumentException.class, () -> c.addEventListener(null, e -> { })),
                () -> assertThrows(IllegalArgumentException.class, () -> c.addEventListener(ConfigurationEvent.ANY, null)),
                () -> assertThrows(IllegalArgumentException.class,
                        () -> new ConfigurationEvent(null, ConfigurationEvent.ADD_PROPERTY, "k", "v", true)),
                () -> assertThrows(IllegalArgumentException.class,
                        () -> new ConfigurationEvent(c, null, "k", "v", true)),
                () -> assertSame(cause, error.getCause()), () -> assertEquals("k", error.getPropertyName()),
                () -> assertEquals("v", error.getPropertyValue()),
                () -> assertSame(ConfigurationEvent.SET_PROPERTY, error.getErrorOperationType()));
    }
}
