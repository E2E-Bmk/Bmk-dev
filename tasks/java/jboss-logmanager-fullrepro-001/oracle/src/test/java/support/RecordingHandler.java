package support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.jboss.logmanager.ExtHandler;
import org.jboss.logmanager.ExtLogRecord;

/** In-memory public-handler test double. */
public final class RecordingHandler extends ExtHandler {
    private final List<ExtLogRecord> records = Collections.synchronizedList(new ArrayList<>());
    private volatile boolean closed;
    private volatile int flushCount;

    @Override protected void doPublish(final ExtLogRecord record) { records.add(record); }
    @Override public void flush() { flushCount++; }
    @Override public void close() { closed = true; super.close(); }
    public List<ExtLogRecord> records() { synchronized (records) { return List.copyOf(records); } }
    public boolean closed() { return closed; }
    public int flushCount() { return flushCount; }
}
