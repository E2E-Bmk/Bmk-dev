package support;

import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;

/** Shared pipeline factories for the load/dump tests. */
public final class Yaml {
    private Yaml() {}

    /** A loader with default settings. */
    public static Load load() {
        return new Load(LoadSettings.builder().build());
    }

    /** A dumper with default settings. */
    public static Dump dump() {
        return new Dump(DumpSettings.builder().build());
    }

    /** Joins the given lines with {@code \n}, appending a trailing newline. */
    public static String doc(String... lines) {
        return String.join("\n", lines) + "\n";
    }
}
