package support;

/** Recording receiver whose close state is publicly observable to the test. */
public final class CloseableRecordingReceiver extends RecordingReceiver implements AutoCloseable {
  @Override public void close() { closed = true; }
}
