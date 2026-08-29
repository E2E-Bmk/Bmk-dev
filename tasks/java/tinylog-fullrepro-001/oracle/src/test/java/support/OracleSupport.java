package support;

import java.util.LinkedHashMap;
import java.util.Map;

import org.tinylog.Level;
import org.tinylog.core.LogEntry;

/** Shared construction helpers whose inputs are all declared by the specification. */
public final class OracleSupport {
    private OracleSupport() { }

    public static LogEntry entry(String message) {
        Map<String, String> context = new LinkedHashMap<>();
        context.put("request", "r-29");
        return new LogEntry(null, Thread.currentThread(), context,
                "example.alpha.Worker", "execute", "Worker.java", 73,
                "audit", Level.INFO, message, null);
    }

    public static Map<String, String> properties(String... pairs) {
        Map<String, String> values = new LinkedHashMap<>();
        for (int index = 0; index < pairs.length; index += 2) {
            values.put(pairs[index], pairs[index + 1]);
        }
        return values;
    }
}
