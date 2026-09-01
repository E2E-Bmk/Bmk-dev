package oraclesupport;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.pf4j.Plugin;
import org.pf4j.PluginRuntimeException;
import org.pf4j.PluginWrapper;

public class RecordingPlugin extends Plugin {
    public RecordingPlugin(PluginWrapper wrapper) { super(wrapper); }
    private void record(String name) {
        try {
            Files.write(getWrapper().getPluginPath().resolve(name),
                getWrapper().getPluginId().getBytes(StandardCharsets.UTF_8));
        } catch (IOException exc) {
            throw new PluginRuntimeException(exc);
        }
    }
    @Override public void start() { record("started.marker"); }
    @Override public void stop() { record("stopped.marker"); }
    @Override public void delete() { record("deleted.marker"); }
}
