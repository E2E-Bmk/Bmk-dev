package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Arrays;
import java.util.Map;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.interpol.ConfigurationInterpolator;
import org.apache.commons.configuration2.interpol.Lookup;
import org.junit.jupiter.api.Test;

class InterpolationAtomicTest {
    /** Verifies: CC-INTP-001, CC-INTP-002 */
    @Test void configurationDefaultsResolveOwnProperties() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("host", "db"); c.setProperty("url", "jdbc:${host}");
        assertEquals("jdbc:db", c.getString("url"));
    }

    /** Verifies: CC-INTP-003 */
    @Test void interpolationTracksReferencedPropertyChanges() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("ref", "one"); c.setProperty("v", "${ref}");
        assertEquals("one", c.getString("v")); c.setProperty("ref", "two"); assertEquals("two", c.getString("v"));
    }

    /** Verifies: CC-PROP-007, CC-INTP-004 */
    @Test void rawProjectionRemainsUnresolvedWhileTypedProjectionResolves() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("x", "ok"); c.setProperty("v", "${x}");
        assertAll(() -> assertEquals("${x}", c.getProperty("v")), () -> assertEquals("ok", c.getString("v")));
    }

    /** Verifies: CC-INTP-005 */
    @Test void nullInterpolatorDisablesResolution() {
        BaseConfiguration c = new BaseConfiguration(); c.setProperty("x", "ok"); c.setProperty("v", "${x}");
        c.setInterpolator(null);
        assertEquals("${x}", c.getString("v"));
    }

    /** Verifies: CC-INTP-008, CC-INTP-009, CC-INTP-017 */
    @Test void prefixedLookupReceivesNameWithoutPrefix() {
        ConfigurationInterpolator i = new ConfigurationInterpolator();
        i.registerLookup("p", key -> "seen-" + key);
        assertEquals("seen-name", i.resolve("p:name"));
    }

    /** Verifies: CC-INTP-010, CC-INTP-020 */
    @Test void defaultLookupsUseInsertionOrderAndCanBeRemoved() {
        ConfigurationInterpolator i = new ConfigurationInterpolator();
        Lookup first = key -> "first"; Lookup second = key -> "second";
        i.addDefaultLookup(first); i.addDefaultLookup(second);
        assertEquals("first", i.resolve("x")); assertTrue(i.removeDefaultLookup(first));
        assertEquals("second", i.resolve("x"));
    }

    /** Verifies: CC-INTP-012, CC-INTP-013, CC-INTP-014, CC-INTP-015 */
    @Test void interpolationPreservesObjectsAndConvertsEmbeddedContainers() {
        ConfigurationInterpolator i = new ConfigurationInterpolator();
        Object marker = new Object(); i.registerLookup("v", key -> marker);
        i.registerLookup("list", key -> Arrays.asList("first", "second"));
        assertAll(() -> assertSame(marker, i.interpolate(marker)), () -> assertSame(marker, i.interpolate("${v:x}")),
                () -> assertEquals("value=first", i.interpolate("value=${list:x}")));
    }

    /** Verifies: CC-INTP-016, CC-INTP-018, CC-INTP-019, CC-INTP-021 */
    @Test void unresolvedVariablesStayVisibleAndRegistrationRejectsNulls() {
        ConfigurationInterpolator i = new ConfigurationInterpolator(); i.registerLookup("p", key -> "v");
        Map<String, Lookup> snapshot = i.getLookups(); snapshot.clear();
        assertAll(() -> assertEquals("${missing}", i.interpolate("${missing}")),
                () -> assertEquals("v", i.resolve("p:x")),
                () -> assertThrows(IllegalArgumentException.class, () -> i.registerLookup(null, key -> key)),
                () -> assertThrows(IllegalArgumentException.class, () -> i.registerLookup("x", null)),
                () -> assertTrue(i.deregisterLookup("p")));
    }
}
