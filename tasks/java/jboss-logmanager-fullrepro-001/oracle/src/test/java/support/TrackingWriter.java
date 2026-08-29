package support;

import java.io.StringWriter;

/** String writer exposing close and flush observations. */
public final class TrackingWriter extends StringWriter {
    private boolean closed;
    private int flushCount;
    @Override public void flush() { flushCount++; super.flush(); }
    @Override public void close() { closed = true; }
    public boolean closed() { return closed; }
    public int flushCount() { return flushCount; }
}
