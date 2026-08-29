package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Arrays;
import java.util.Collections;
import java.util.Map;
import java.util.Set;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.Configuration;
import org.apache.commons.configuration2.interpol.ConfigurationInterpolator;
import org.apache.commons.configuration2.interpol.Lookup;
import org.junit.jupiter.api.Test;

class InterpolationIntegrationTest {
    /**
     * Verifies: CC-INTP-003, CC-INTP-004, CC-CVI-002
     * Depends-On: rawProjectionRemainsUnresolvedWhileTypedProjectionResolves, interpolationTracksReferencedPropertyChanges
     */
    @Test void rawExpressionAndDynamicTypedValueRemainCoherent() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("host", "one"); c.setProperty("url", "http://${host}");
        assertEquals("${host}", ((String) c.getProperty("url")).substring(7, 14));
        assertEquals("http://one", c.getString("url")); c.setProperty("host", "two");
        assertAll(() -> assertEquals("http://${host}", c.getProperty("url")),
                () -> assertEquals("http://two", c.getString("url")));
    }

    /**
     * Verifies: CC-INTP-004, CC-CVI-002
     * Depends-On: scalarUsesFirstValueAndContainersPreserveAllOrder, configurationDefaultsResolveOwnProperties
     */
    @Test void interpolationAppliesAcrossListAndStringArrayProjections() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("x", "resolved");
        c.addProperty("values", "${x}"); c.addProperty("values", "tail-${x}");
        assertAll(() -> assertEquals(Arrays.asList("resolved", "tail-resolved"), c.getList(String.class, "values")),
                () -> assertArrayEquals(new String[] {"resolved", "tail-resolved"}, c.getStringArray("values")));
    }

    /**
     * Verifies: CC-INTP-006, CC-INTP-008
     * Depends-On: prefixedLookupReceivesNameWithoutPrefix, configurationDefaultsResolveOwnProperties
     */
    @Test void installedLookupsIncludeExplicitPrefixAndConfigurationFallback() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("local", "inside");
        c.installInterpolator(Collections.singletonMap("ext", key -> "outside-" + key), Collections.emptyList());
        c.setProperty("both", "${ext:x}/${local}");
        assertEquals("outside-x/inside", c.getString("both"));
    }

    /**
     * Verifies: CC-INTP-007
     * Depends-On: nullInterpolatorDisablesResolution, prefixedLookupReceivesNameWithoutPrefix
     */
    @Test void suppliedInterpolatorDoesNotGainConfigurationFallback() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("local", "inside"); c.setProperty("v", "${local}");
        c.setInterpolator(new ConfigurationInterpolator());
        assertEquals("${local}", c.getString("v"));
    }

    /**
     * Verifies: CC-INTP-010, CC-INTP-011
     * Depends-On: defaultLookupsUseInsertionOrderAndCanBeRemoved, prefixedLookupReceivesNameWithoutPrefix
     */
    @Test void unresolvedLocalLookupDelegatesToParent() {
        ConfigurationInterpolator parent = new ConfigurationInterpolator(); parent.registerLookup("p", key -> "parent-" + key);
        ConfigurationInterpolator child = new ConfigurationInterpolator(); child.addDefaultLookup(key -> null);
        child.setParentInterpolator(parent);
        assertAll(() -> assertEquals("parent-x", child.resolve("p:x")), () -> assertNull(child.resolve("missing")));
    }

    /**
     * Verifies: CC-INTP-021, CC-INTP-022
     * Depends-On: unresolvedVariablesStayVisibleAndRegistrationRejectsNulls, prefixedLookupReceivesNameWithoutPrefix
     */
    @Test void exposedLookupCollectionsCannotMutateRegistration() {
        ConfigurationInterpolator i = new ConfigurationInterpolator(); Lookup lookup = key -> "ok";
        i.registerLookup("p", lookup); i.addDefaultLookup(lookup);
        Map<String, Lookup> lookups = i.getLookups(); lookups.clear();
        i.getDefaultLookups().clear(); Set<String> prefixes = i.prefixSet();
        assertAll(() -> assertEquals("ok", i.resolve("p:x")), () -> assertEquals("ok", i.resolve("x")),
                () -> assertThrows(UnsupportedOperationException.class, () -> prefixes.remove("p")));
    }

    /**
     * Verifies: CC-INTP-016
     * Depends-On: interpolationPreservesObjectsAndConvertsEmbeddedContainers, unresolvedVariablesStayVisibleAndRegistrationRejectsNulls
     */
    @Test void unresolvedEmbeddedExpressionRemainsVisible() {
        ConfigurationInterpolator i = new ConfigurationInterpolator();
        assertEquals("left-${unknown}-right", i.interpolate("left-${unknown}-right"));
    }

    /**
     * Verifies: CC-INTP-023
     * Depends-On: prefixedLookupReceivesNameWithoutPrefix, defaultLookupsUseInsertionOrderAndCanBeRemoved
     */
    @Test void substitutionInsideVariableNamesCanBeEnabled() {
        ConfigurationInterpolator i = new ConfigurationInterpolator();
        i.registerLookup("name", key -> "target"); i.registerLookup("value", key -> "resolved-" + key);
        i.setEnableSubstitutionInVariables(true);
        assertEquals("resolved-target", i.interpolate("${value:${name:x}}"));
    }
}
