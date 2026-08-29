package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.List;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.builder.BasicConfigurationBuilder;
import org.apache.commons.configuration2.builder.ConfigurationBuilderEvent;
import org.apache.commons.configuration2.builder.ConfigurationBuilderResultCreatedEvent;
import org.apache.commons.configuration2.event.ConfigurationEvent;
import org.apache.commons.configuration2.event.EventListener;
import org.junit.jupiter.api.Test;

class BuilderEventIntegrationTest {
    /**
     * Verifies: CC-BLDR-001, CC-BLDR-002, CC-CVI-007
     * Depends-On: eventRegistrationRejectsNullArguments, emptyConfigurationHasNoState
     */
    @Test void builderCreatesLazilyAndKeepsStableIdentity() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        BaseConfiguration first = b.getConfiguration(); first.setProperty("k", "v");
        assertAll(() -> assertSame(first, b.getConfiguration()), () -> assertEquals("v", b.getConfiguration().getString("k")));
    }

    /**
     * Verifies: CC-BLDR-003, CC-BLDR-005, CC-CVI-007
     * Depends-On: emptyConfigurationHasNoState, clearRemovesEveryProperty
     */
    @Test void resetOperationsReplaceManagedIdentity() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        BaseConfiguration first = b.getConfiguration(); b.resetResult(); BaseConfiguration second = b.getConfiguration();
        b.reset(); BaseConfiguration third = b.getConfiguration();
        assertAll(() -> assertNotSame(first, second), () -> assertNotSame(second, third));
    }

    /**
     * Verifies: CC-BLDR-004, CC-BLDR-008
     * Depends-On: emptyConfigurationHasNoState, setPropertyReplacesAllOldValues
     */
    @Test void resetParametersDoesNotDiscardManagedResult() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        BaseConfiguration managed = b.getConfiguration(); managed.setProperty("live", true); b.resetParameters();
        assertAll(() -> assertSame(managed, b.getConfiguration()), () -> assertTrue(b.getConfiguration().getBoolean("live")));
    }

    /**
     * Verifies: CC-BLDR-012
     * Depends-On: emptyConfigurationHasNoState, eventRegistrationRejectsNullArguments
     */
    @Test void everyConfigurationRequestEmitsRequestEvent() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        List<ConfigurationBuilderEvent> events = new ArrayList<>();
        b.addEventListener(ConfigurationBuilderEvent.CONFIGURATION_REQUEST, events::add);
        b.getConfiguration(); b.getConfiguration();
        assertAll(() -> assertEquals(2, events.size()),
                () -> assertTrue(events.stream().allMatch(e -> e.getEventType() == ConfigurationBuilderEvent.CONFIGURATION_REQUEST)));
    }

    /**
     * Verifies: CC-BLDR-013, CC-CVI-007
     * Depends-On: eventRegistrationRejectsNullArguments, emptyConfigurationHasNoState
     */
    @Test void oneResultCreatedEventCarriesEachNewIdentity() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        List<ConfigurationBuilderResultCreatedEvent> events = new ArrayList<>();
        b.addEventListener(ConfigurationBuilderResultCreatedEvent.RESULT_CREATED, events::add);
        BaseConfiguration first = b.getConfiguration(); b.getConfiguration();
        assertAll(() -> assertEquals(1, events.size()), () -> assertSame(first, events.get(0).getConfiguration()));
        b.resetResult(); BaseConfiguration second = b.getConfiguration();
        assertAll(() -> assertEquals(2, events.size()), () -> assertSame(second, events.get(1).getConfiguration()));
    }

    /**
     * Verifies: CC-BLDR-014, CC-BLDR-017
     * Depends-On: eventRegistrationRejectsNullArguments, emptyConfigurationHasNoState
     */
    @Test void resetEventFiresWithoutResultAndListenerCanBeRemoved() {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        List<ConfigurationBuilderEvent> events = new ArrayList<>(); EventListener<ConfigurationBuilderEvent> listener = events::add;
        b.addEventListener(ConfigurationBuilderEvent.RESET, listener); b.resetResult();
        assertEquals(1, events.size()); assertTrue(b.removeEventListener(ConfigurationBuilderEvent.RESET, listener));
        b.resetResult();
        assertAll(() -> assertEquals(1, events.size()),
                () -> assertFalse(b.removeEventListener(ConfigurationBuilderEvent.RESET, listener)));
    }

    /**
     * Verifies: CC-BLDR-015, CC-BLDR-016
     * Depends-On: emptyConfigurationHasNoState, eventRegistrationRejectsNullArguments
     */
    @Test void propagatedConfigurationListenerMovesToReplacementResult() throws Exception {
        BasicConfigurationBuilder<BaseConfiguration> b = new BasicConfigurationBuilder<>(BaseConfiguration.class);
        List<ConfigurationEvent> events = new ArrayList<>(); b.addEventListener(ConfigurationEvent.ANY, events::add);
        BaseConfiguration old = b.getConfiguration(); old.setProperty("a", 1); assertEquals(2, events.size());
        b.resetResult(); old.setProperty("old", 2); assertEquals(2, events.size());
        b.getConfiguration().setProperty("new", 3); assertEquals(4, events.size());
    }

    /**
     * Verifies: CC-EVT-001, CC-EVT-002, CC-EVT-003, CC-EVT-004, CC-CVI-008
     * Depends-On: eventRegistrationRejectsNullArguments, setPropertyReplacesAllOldValues
     */
    @Test void baseEventListenerSeesMatchingBeforeAfterPayload() {
        BaseConfiguration c = new BaseConfiguration(); List<ConfigurationEvent> events = new ArrayList<>();
        c.addEventListener(ConfigurationEvent.ANY, events::add); c.setProperty("key", "value");
        assertAll(() -> assertEquals(2, events.size()), () -> assertTrue(events.get(0).isBeforeUpdate()),
                () -> assertFalse(events.get(1).isBeforeUpdate()),
                () -> assertTrue(events.stream().allMatch(e -> e.getEventType() == ConfigurationEvent.SET_PROPERTY)),
                () -> assertTrue(events.stream().allMatch(e -> "key".equals(e.getPropertyName()))),
                () -> assertTrue(events.stream().allMatch(e -> "value".equals(e.getPropertyValue()))));
    }
}
