package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import java.util.NoSuchElementException;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.BaseHierarchicalConfiguration;
import org.apache.commons.configuration2.Configuration;
import org.apache.commons.configuration2.HierarchicalConfiguration;
import org.apache.commons.configuration2.ImmutableConfiguration;
import org.apache.commons.configuration2.tree.ImmutableNode;
import org.junit.jupiter.api.Test;

class SubsetHierarchyIntegrationTest {
    /**
     * Verifies: CC-VIEW-005, CC-CVI-001, CC-STATE-001
     * Depends-On: subsetUsesDelimiterBoundaryAndStripsPrefix, setPropertyReplacesAllOldValues
     */
    @Test void subsetAndParentExchangeUpdatesBothWays() {
        BaseConfiguration parent = new BaseConfiguration(); parent.setProperty("service.host", "one");
        Configuration subset = parent.subset("service"); subset.setProperty("host", "two");
        assertEquals("two", parent.getString("service.host"));
        parent.setProperty("service.port", 5432); assertEquals(5432, subset.getInt("port"));
    }

    /**
     * Verifies: CC-VIEW-007, CC-CVI-001
     * Depends-On: subsetUsesDelimiterBoundaryAndStripsPrefix, keysFollowFirstInsertionOrderAndSizeCountsDistinctKeys
     */
    @Test void nestedSubsetsComposeAgainstOriginalParent() {
        BaseConfiguration parent = new BaseConfiguration();
        Configuration nested = parent.subset("service").subset("database"); nested.setProperty("host", "db");
        assertAll(() -> assertEquals("db", parent.getString("service.database.host")),
                () -> assertEquals("db", parent.subset("service").getString("database.host")));
    }

    /**
     * Verifies: CC-VIEW-006, CC-CVI-003
     * Depends-On: clearRemovesEveryProperty, subsetUsesDelimiterBoundaryAndStripsPrefix
     */
    @Test void clearingSubsetRemovesOnlyItsVisibleRegion() {
        BaseConfiguration parent = new BaseConfiguration();
        parent.setProperty("app.a", 1); parent.setProperty("app.b", 2); parent.setProperty("other", 3);
        parent.subset("app").clear();
        assertAll(() -> assertFalse(parent.containsKey("app.a")), () -> assertFalse(parent.containsKey("app.b")),
                () -> assertEquals(3, parent.getInt("other")), () -> assertEquals(1, parent.size()));
    }

    /**
     * Verifies: CC-VIEW-008
     * Depends-On: strictMissingObjectGetterThrows, delimiterHandlerControlsExpansion
     */
    @Test void subsetInheritsStrictMissingPolicy() {
        BaseConfiguration parent = new BaseConfiguration(); parent.setThrowExceptionOnMissing(true);
        Configuration subset = parent.subset("app");
        assertThrows(NoSuchElementException.class, () -> subset.getString("missing"));
    }

    /**
     * Verifies: CC-VIEW-012, CC-VIEW-013, CC-CVI-005
     * Depends-On: hierarchicalIndicesAreZeroBasedAndMaxIndexIsGreatest, setPropertyReplacesAllOldValues
     */
    @Test void independentAndConnectedSubtreesHaveDistinctUpdateBehavior() {
        BaseHierarchicalConfiguration parent = new BaseHierarchicalConfiguration(); parent.setProperty("app.value", "one");
        HierarchicalConfiguration<ImmutableNode> independent = parent.configurationAt("app");
        HierarchicalConfiguration<ImmutableNode> connected = parent.configurationAt("app", true);
        parent.setProperty("app.value", "two");
        assertAll(() -> assertEquals("one", independent.getString("value")),
                () -> assertEquals("two", connected.getString("value")));
        connected.setProperty("value", "three"); assertEquals("three", parent.getString("app.value"));
    }

    /**
     * Verifies: CC-VIEW-014, CC-CVI-005
     * Depends-On: clearTreeRemovesNodeAndDescendantsOnly, configurationAtMissingSelectionThrows
     */
    @Test void removedConnectedSubtreeDetachesPermanently() {
        BaseHierarchicalConfiguration parent = new BaseHierarchicalConfiguration(); parent.setProperty("app.value", "one");
        HierarchicalConfiguration<ImmutableNode> connected = parent.configurationAt("app", true);
        parent.clearTree("app"); connected.setProperty("value", "detached"); parent.setProperty("app.value", "new-parent");
        assertAll(() -> assertEquals("detached", connected.getString("value")),
                () -> assertEquals("new-parent", parent.getString("app.value")));
    }

    /**
     * Verifies: CC-VIEW-016, CC-VIEW-017
     * Depends-On: configurationsAtMissingSelectionIsEmpty, hierarchicalIndicesAreZeroBasedAndMaxIndexIsGreatest
     */
    @Test void configurationsAtReturnsOrderedIndependentRoots() {
        BaseHierarchicalConfiguration parent = new BaseHierarchicalConfiguration();
        parent.setProperty("items.item(0).name", "a"); parent.setProperty("items.item(1).name", "b");
        List<HierarchicalConfiguration<ImmutableNode>> views = parent.configurationsAt("items.item");
        assertAll(() -> assertEquals(2, views.size()), () -> assertEquals("a", views.get(0).getString("name")),
                () -> assertEquals("b", views.get(1).getString("name")));
        parent.setProperty("items.item(0).name", "changed"); assertEquals("a", views.get(0).getString("name"));
    }

    /**
     * Verifies: CC-VIEW-018, CC-VIEW-019, CC-VIEW-020
     * Depends-On: configurationsAtMissingSelectionIsEmpty, clearTreeRemovesNodeAndDescendantsOnly
     */
    @Test void immutableChildViewsExposeDirectChildValues() {
        BaseHierarchicalConfiguration parent = new BaseHierarchicalConfiguration();
        parent.setProperty("root.alpha.value", 1); parent.setProperty("root.beta.value", 2);
        List<HierarchicalConfiguration<ImmutableNode>> connected = parent.childConfigurationsAt("root", true);
        connected.get(0).setProperty("value", 10);
        List<? extends ImmutableConfiguration> children = parent.immutableChildConfigurationsAt("root");
        assertAll(() -> assertEquals(2, children.size()), () -> assertEquals(10, parent.getInt("root.alpha.value")),
                () -> assertEquals(10, children.get(0).getInt("value")),
                () -> assertEquals(2, children.get(1).getInt("value")));
    }
}
