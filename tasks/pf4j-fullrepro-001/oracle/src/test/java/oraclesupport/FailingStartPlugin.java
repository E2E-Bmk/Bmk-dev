package oraclesupport;

import org.pf4j.Plugin;
import org.pf4j.PluginRuntimeException;
import org.pf4j.PluginWrapper;

public class FailingStartPlugin extends Plugin {
    public FailingStartPlugin(PluginWrapper wrapper) { super(wrapper); }
    @Override public void start() { throw new PluginRuntimeException("fixture start failure"); }
}
