package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.List;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.BaseHierarchicalConfiguration;
import org.apache.commons.configuration2.CompositeConfiguration;
import org.apache.commons.configuration2.Configuration;
import org.apache.commons.configuration2.HierarchicalConfiguration;
import org.apache.commons.configuration2.builder.BasicConfigurationBuilder;
import org.apache.commons.configuration2.builder.ConfigurationBuilderEvent;
import org.apache.commons.configuration2.builder.ConfigurationBuilderResultCreatedEvent;
import org.apache.commons.configuration2.event.ConfigurationEvent;
import org.apache.commons.configuration2.ex.ConfigurationRuntimeException;
import org.apache.commons.configuration2.ex.ConversionException;
import org.apache.commons.configuration2.tree.ImmutableNode;
import org.junit.jupiter.api.Test;

class WorkflowStateIntegrationTest {
    /**
     * Verifies: CC-PROP-009, CC-VIEW-005, CC-INTP-002, CC-STATE-001
     * Depends-On: compatibleScalarsConvertToRequestedTypes, subsetUsesDelimiterBoundaryAndStripsPrefix
     */
    @Test void typedInterpolationAndLiveSubsetWorkflow() {
        BaseConfiguration c = new BaseConfiguration();
        c.setProperty("service.host", "db.internal"); c.setProperty("service.port", "5432");
        c.setProperty("service.endpoint", "${service.host}:${service.port}");
        assertAll(() -> assertEquals("db.internal:5432", c.getString("service.endpoint")),
                () -> assertEquals(5432, c.getInt("service.port")));
        c.subset("service").setProperty("host", "db.example");
        assertEquals("db.example:5432", c.getString("service.endpoint"));
    }

    /**
     * Verifies: CC-COMP-002, CC-COMP-010, CC-STATE-001
     * Depends-On: addConfigurationFirstRaisesPriority, compositeSourceRequiresUniqueDefiningChild
     */
    @Test void layeredUserAndDefaultsWorkflow() {
        BaseConfiguration user = new BaseConfiguration(); user.setProperty("theme", "dark");
        BaseConfiguration defaults = new BaseConfiguration(); defaults.setProperty("theme", "light"); defaults.setProperty("pageSize", 25);
        CompositeConfiguration c = new CompositeConfiguration(); c.addConfiguration(user); c.addConfiguration(defaults);
        assertAll(() -> assertEquals("dark", c.getString("theme")), () -> assertEquals(25, c.getInt("pageSize")),
                () -> assertSame(defaults, c.getSource("pageSize")));
    }

    /**
     * Verifies: CC-BLDR-002, CC-BLDR-003, CC-BLDR-013, CC-STATE-001
     * Depends-On: emptyConfigurationHasNoState, clearRemovesEveryProperty
     */
    @Test void lazyBuilderReplacementWorkflow() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        List<ConfigurationBuilderEvent> events = new ArrayList<>(); b.addEventListener(ConfigurationBuilderEvent.ANY, events::add);
        BaseConfiguration first = b.getConfiguration(); BaseConfiguration again = b.getConfiguration(); b.resetResult();
        BaseConfiguration second = b.getConfiguration();
        long created = events.stream().filter(e -> e.getEventType() == ConfigurationBuilderResultCreatedEvent.RESULT_CREATED).count();
        assertAll(() -> assertSame(first, again), () -> assertNotSame(first, second), () -> assertEquals(2, created));
    }

    /**
     * Verifies: CC-VIEW-013, CC-STATE-001
     * Depends-On: configurationAtMissingSelectionThrows, hierarchicalIndicesAreZeroBasedAndMaxIndexIsGreatest
     */
    @Test void connectedHierarchyEditWorkflow() {
        BaseHierarchicalConfiguration parent = new BaseHierarchicalConfiguration(); parent.setProperty("database.host", "one");
        HierarchicalConfiguration<ImmutableNode> database = parent.configurationAt("database", true);
        database.setProperty("host", "two"); parent.setProperty("database.port", 5432);
        assertAll(() -> assertEquals("two", parent.getString("database.host")),
                () -> assertEquals(5432, database.getInt("port")));
    }

    /**
     * Verifies: CC-PROP-005, CC-VIEW-021, CC-CVI-003, CC-STATE-001
     * Depends-On: clearingMissingPropertyPreservesOtherState, clearTreeRemovesNodeAndDescendantsOnly
     */
    @Test void removalDisappearsFromAllRelevantProjections() {
        BaseHierarchicalConfiguration c = new BaseHierarchicalConfiguration();
        c.setProperty("root.item.value", "v");
        c.clearTree("root.item"); Configuration subset = c.subset("root");
        List<String> keys = new ArrayList<>(); c.getKeys().forEachRemaining(keys::add);
        assertAll(() -> assertNull(c.getProperty("root.item.value")),
                () -> assertNull(c.getString("root.item.value")), () -> assertFalse(c.containsKey("root.item.value")),
                () -> assertFalse(keys.contains("root.item.value")), () -> assertNull(subset.getString("item.value")));
    }

    /**
     * Verifies: CC-PROP-017, CC-STATE-002
     * Depends-On: incompatiblePresentValueRaisesConversionException, setPropertyReplacesAllOldValues
     */
    @Test void failedConversionLeavesRawStateUntouched() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("n", "bad");
        assertThrows(ConversionException.class, () -> c.getInt("n"));
        assertAll(() -> assertEquals("bad", c.getProperty("n")), () -> assertEquals(1, c.size()));
    }

    /**
     * Verifies: CC-VIEW-015, CC-STATE-002
     * Depends-On: configurationAtMissingSelectionThrows, clearTreeRemovesNodeAndDescendantsOnly
     */
    @Test void failedTreeSelectionLeavesExistingStateUntouched() {
        BaseHierarchicalConfiguration c = new BaseHierarchicalConfiguration(); c.setProperty("kept.value", "v");
        assertThrows(ConfigurationRuntimeException.class, () -> c.configurationAt("missing"));
        assertAll(() -> assertEquals("v", c.getString("kept.value")), () -> assertEquals(1, c.size()));
    }

    /**
     * Verifies: CC-EVT-002, CC-EVT-003, CC-EVT-004, CC-EVT-005, CC-CVI-008, CC-STATE-001
     * Depends-On: eventRegistrationRejectsNullArguments, clearingMissingPropertyPreservesOtherState
     */
    @Test void clearPropertyEventPairMatchesFinalState() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("k", "v");
        List<ConfigurationEvent> events = new ArrayList<>(); c.addEventListener(ConfigurationEvent.CLEAR_PROPERTY, events::add);
        c.clearProperty("k");
        assertAll(() -> assertEquals(2, events.size()), () -> assertTrue(events.get(0).isBeforeUpdate()),
                () -> assertFalse(events.get(1).isBeforeUpdate()),
                () -> assertTrue(events.stream().allMatch(e -> "k".equals(e.getPropertyName()))),
                () -> assertTrue(events.stream().allMatch(e -> e.getPropertyValue() == null)),
                () -> assertFalse(c.containsKey("k")));
        BaseConfiguration compound = new BaseConfiguration(); compound.setProperty("a", 1); compound.setProperty("b", 2);
        List<ConfigurationEvent> compoundEvents = new ArrayList<>();
        compound.addEventListener(ConfigurationEvent.ANY, compoundEvents::add); compound.clear();
        assertAll(() -> assertEquals(2, compoundEvents.size()),
                () -> assertTrue(compoundEvents.stream().allMatch(e -> e.getEventType() == ConfigurationEvent.CLEAR)));
    }
}
