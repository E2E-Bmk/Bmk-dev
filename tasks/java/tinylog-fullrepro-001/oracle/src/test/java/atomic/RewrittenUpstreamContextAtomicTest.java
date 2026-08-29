package atomic;

import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import org.junit.jupiter.api.Test;
import org.tinylog.core.TinylogContextProvider;

import static org.junit.jupiter.api.Assertions.*;

/** Public-API rewrites of the sole upstream file that survived carrier audit. */
class RewrittenUpstreamContextAtomicTest {
    /** Verifies: TINY-CONF-027. */
    @Test void newProviderHasEmptyMapping() {
        assertTrue(new TinylogContextProvider().getMapping().isEmpty());
    }

    /** Verifies: TINY-CONF-028. */
    @Test void putStoresStringValue() {
        TinylogContextProvider provider = new TinylogContextProvider();
        provider.put("ratio", 29.5);
        assertEquals("29.5", provider.get("ratio"));
    }

    /** Verifies: TINY-CONF-028. */
    @Test void putAppearsInMapping() {
        TinylogContextProvider provider = new TinylogContextProvider();
        provider.put("color", "violet");
        assertEquals(Map.of("color", "violet"), provider.getMapping());
    }

    /** Verifies: TINY-CONF-028. */
    @Test void putOverridesExistingValue() {
        TinylogContextProvider provider = new TinylogContextProvider();
        provider.put("mode", "cold");
        provider.put("mode", "warm");
        assertEquals("warm", provider.get("mode"));
    }

    /** Verifies: TINY-CONF-029. */
    @Test void nullPutRemovesExistingKey() {
        TinylogContextProvider provider = new TinylogContextProvider();
        provider.put("mode", "warm");
        provider.put("mode", null);
        assertNull(provider.get("mode"));
    }

    /** Verifies: TINY-CONF-027. */
    @Test void removeAndClearChangeCurrentMapping() {
        TinylogContextProvider provider = new TinylogContextProvider();
        provider.put("first", 1);
        provider.put("second", 2);
        provider.remove("first");
        assertEquals(Map.of("second", "2"), provider.getMapping());
        provider.clear();
        assertTrue(provider.getMapping().isEmpty());
    }

    /** Verifies: TINY-CONF-030. */
    @Test void childInheritsSnapshotWithoutLeakingMutation() throws Exception {
        TinylogContextProvider provider = new TinylogContextProvider();
        provider.put("parent", "visible");
        AtomicReference<Map<String, String>> childView = new AtomicReference<>();
        Thread child = new Thread(() -> {
            provider.put("child", "local");
            childView.set(provider.getMapping());
        });
        child.start();
        child.join();
        assertEquals(Map.of("parent", "visible", "child", "local"), childView.get());
        assertEquals(Map.of("parent", "visible"), provider.getMapping());
    }
}
