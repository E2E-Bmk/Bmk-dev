package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import org.junit.jupiter.api.Test;
import org.owasp.html.Encoding;
import org.owasp.html.Handler;
import org.owasp.html.HtmlStreamEventProcessor;
import org.owasp.html.HtmlStreamEventReceiverWrapper;
import org.owasp.html.HtmlStreamRenderer;
import org.owasp.html.TagBalancingHtmlStreamEventReceiver;
import support.CloseableRecordingReceiver;
import support.RecordingReceiver;

/** Atomic sanitization, event, renderer, and telemetry contracts. */
public class SanitizationEventTelemetryAtomicTest {
  /** Verifies: JHS-SAN-012. */
  @Test public void decodeHtmlResolvesNamedReferences() {
    assertEquals("salt & pepper ©", Encoding.decodeHtml("salt &amp; pepper &copy;"));
  }

  /** Verifies: JHS-SAN-012. */
  @Test public void decodeHtmlResolvesNumericAndRemovesInvalidXmlUnits() {
    assertEquals("A B", Encoding.decodeHtml("&#65;\u0000 B"));
  }

  /** Verifies: JHS-SAN-013. */
  @Test public void attributeContextDoesNotConsumeAmbiguousReference() {
    assertEquals("&notit=1", Encoding.decodeHtml("&notit=1", true));
  }

  /** Verifies: JHS-SAN-014. */
  @Test public void rcdataEncodingDefangsClosingBoundary() throws IOException {
    StringBuilder out = new StringBuilder();
    Encoding.encodeRcdataOnto("alpha</title>omega &", out);
    assertFalse(out.toString().contains("</title>"));
    assertTrue(out.toString().contains("alpha"));
    assertTrue(out.toString().contains("omega"));
  }

  /** Verifies: JHS-SAN-015. */
  @Test public void rendererEscapesOrdinaryTextBoundaries() {
    StringBuilder out = new StringBuilder();
    HtmlStreamRenderer r = HtmlStreamRenderer.create(out, Handler.DO_NOTHING);
    r.openDocument();
    r.text("left < right & {{template");
    r.closeDocument();
    assertFalse(out.toString().contains("left < right"));
    assertFalse(out.toString().contains("{{template"));
    assertTrue(out.toString().contains("left"));
  }

  /** Verifies: JHS-EVT-025, JHS-ERR-007. */
  @Test public void rendererRoutesAppendFailureToIoHandler() {
    java.util.List<IOException> problems = new java.util.ArrayList<IOException>();
    Appendable failing = new Appendable() {
      @Override public Appendable append(CharSequence csq) throws IOException { throw new IOException("boom"); }
      @Override public Appendable append(CharSequence csq, int start, int end) throws IOException {
        throw new IOException("boom");
      }
      @Override public Appendable append(char c) throws IOException { throw new IOException("boom"); }
    };
    HtmlStreamRenderer r = HtmlStreamRenderer.create(failing, problems::add, Handler.DO_NOTHING);
    r.openDocument();
    r.text("payload");
    r.closeDocument();
    assertEquals(1, problems.size());
    assertEquals(IOException.class, problems.get(0).getClass());
  }

  /** Verifies: JHS-EVT-022, JHS-STATE-004. */
  @Test public void rendererStartsClosed() {
    HtmlStreamRenderer r = HtmlStreamRenderer.create(new StringBuilder(), Handler.DO_NOTHING);
    assertFalse(r.isDocumentOpen());
  }

  /** Verifies: JHS-EVT-018, JHS-EVT-020, JHS-EVT-022. */
  @Test public void rendererOpenCloseTransitionsAreObservable() {
    HtmlStreamRenderer r = HtmlStreamRenderer.create(new StringBuilder(), Handler.DO_NOTHING);
    r.openDocument();
    assertTrue(r.isDocumentOpen());
    r.closeDocument();
    assertFalse(r.isDocumentOpen());
  }

  /** Verifies: JHS-EVT-019, JHS-ERR-005. */
  @Test public void rendererRejectsDoubleOpen() {
    HtmlStreamRenderer r = HtmlStreamRenderer.create(new StringBuilder(), Handler.DO_NOTHING);
    r.openDocument();
    assertThrows(IllegalStateException.class, r::openDocument);
  }

  /** Verifies: JHS-EVT-021, JHS-ERR-005. */
  @Test public void rendererRejectsTextWhileClosed() {
    HtmlStreamRenderer r = HtmlStreamRenderer.create(new StringBuilder(), Handler.DO_NOTHING);
    assertThrows(IllegalStateException.class, () -> r.text("outside"));
  }

  /** Verifies: JHS-EVT-027. */
  @Test public void propagateRethrowsRuntimeExceptionIdentity() {
    IllegalArgumentException problem = new IllegalArgumentException("marker");
    IllegalArgumentException seen = assertThrows(IllegalArgumentException.class,
        () -> Handler.PROPAGATE.handle(problem));
    assertSame(problem, seen);
  }

  /** Verifies: JHS-EVT-028, JHS-ERR-008. */
  @Test public void propagateWrapsCheckedThrowableAsAssertionError() {
    IOException problem = new IOException("marker");
    AssertionError seen = assertThrows(AssertionError.class,
        () -> Handler.PROPAGATE.handle(problem));
    assertSame(problem, seen.getCause());
  }

  /** Verifies: JHS-EVT-003. */
  @Test public void receiverWrapperDelegatesAllEventKinds() throws Exception {
    RecordingReceiver sink = new RecordingReceiver();
    HtmlStreamEventReceiverWrapper wrapper = new HtmlStreamEventReceiverWrapper(sink) {};
    wrapper.openDocument();
    wrapper.openTag("p", Collections.emptyList());
    wrapper.text("delta");
    wrapper.closeTag("p");
    wrapper.closeDocument();
    assertEquals(Arrays.asList("openDocument", "open:p:[]", "text:delta", "close:p", "closeDocument"),
        sink.snapshot());
  }

  /** Verifies: JHS-EVT-004. */
  @Test public void receiverWrapperClosesAutoCloseableSink() throws Exception {
    CloseableRecordingReceiver sink = new CloseableRecordingReceiver();
    new HtmlStreamEventReceiverWrapper(sink) {}.close();
    assertTrue(sink.closed);
  }

  /** Verifies: JHS-EVT-006. */
  @Test public void identityProcessorReturnsSameSink() {
    RecordingReceiver sink = new RecordingReceiver();
    assertSame(sink, HtmlStreamEventProcessor.Processors.IDENTITY.wrap(sink));
  }

  /** Verifies: JHS-EVT-015. */
  @Test public void interElementWhitespaceRecognizesOnlyHtmlWhitespace() {
    assertTrue(TagBalancingHtmlStreamEventReceiver.isInterElementWhitespace(" \t\r\n\f"));
    assertFalse(TagBalancingHtmlStreamEventReceiver.isInterElementWhitespace(" \u00a0"));
  }

}
