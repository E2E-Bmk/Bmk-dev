package atomic;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.pf4j.DefaultPluginDescriptor;
import org.pf4j.DefaultVersionManager;
import org.pf4j.DependencyResolver;
import org.pf4j.PluginDependency;
import org.pf4j.PluginState;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Public-only rewrites of four upstream behavior tests. */
class RewrittenUpstreamTest {
    /** Verifies: PF4J-LIFE-002. */
    @Test void pluginStateParseIsCaseInsensitive() {
        assertEquals(PluginState.STARTED, PluginState.parse("sTaRtEd"));
        assertEquals(PluginState.CREATED, PluginState.parse("created"));
        assertEquals(PluginState.DISABLED, PluginState.parse("DISABLED"));
        assertEquals(PluginState.RESOLVED, PluginState.parse("Resolved"));
        assertEquals(PluginState.STOPPED, PluginState.parse("stopped"));
        assertEquals(PluginState.FAILED, PluginState.parse("failed"));
        assertEquals(PluginState.UNLOADED, PluginState.parse("unloaded"));
    }

    /** Verifies: PF4J-DEP-001, PF4J-DEP-002. */
    @Test void pluginDependencyDefaultsVersion() {
        PluginDependency dependency = new PluginDependency("rewrite-base");
        assertEquals("rewrite-base", dependency.getPluginId());
        assertEquals("*", dependency.getPluginVersionSupport());
        PluginDependency optional = new PluginDependency("rewrite-cache?@>=1.5.0");
        assertEquals("rewrite-cache", optional.getPluginId());
        assertEquals(">=1.5.0", optional.getPluginVersionSupport());
        assertTrue(optional.isOptional());
    }

    /** Verifies: PF4J-DEP-014. */
    @Test void versionManagerComparesSemvers() {
        assertTrue(new DefaultVersionManager().compareVersions("2.3.1", "2.2.9") > 0);
    }

    /** Verifies: PF4J-DEP-005, PF4J-DEP-010. */
    @Test void resolverOrdersRequiredDependency() {
        DefaultPluginDescriptor base = new DefaultPluginDescriptor(
            "rewrite-base", "", "org.pf4j.Plugin", "2.4.0", "*", "", "");
        DefaultPluginDescriptor feature = new DefaultPluginDescriptor(
            "rewrite-feature", "", "org.pf4j.Plugin", "1.0.0", "*", "", "");
        feature.addDependency(new PluginDependency("rewrite-base@>=2.0.0 & <3.0.0"));
        DependencyResolver.Result result = new DependencyResolver(new DefaultVersionManager())
            .resolve(List.of(feature, base));
        assertTrue(result.isOK());
        assertEquals(List.of("rewrite-base", "rewrite-feature"), result.getSortedPlugins());
    }
}
