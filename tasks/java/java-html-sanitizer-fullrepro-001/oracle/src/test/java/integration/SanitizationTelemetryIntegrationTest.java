package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Collections;
import org.junit.jupiter.api.Test;
import org.owasp.html.HtmlChangeReporter;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.HtmlSanitizer;
import org.owasp.html.PolicyFactory;
import support.RecordingListener;
import support.RecordingReceiver;

/** Integration tests for normalized output and rejection telemetry. */
public class SanitizationTelemetryIntegrationTest {
  /** Verifies: JHS-SAN-001, JHS-ERR-010. Seam: protocol handoff. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void nullConvenienceInputProducesEmptyString() {
    assertEquals("", new HtmlPolicyBuilder().toFactory().sanitize(null));
  }

  /** Verifies: JHS-SAN-009. Seam: protocol handoff. Depends-On: rendererEscapesOrdinaryTextBoundaries. */
  @Test public void sanitizerOmitsCommentsAndDeclarations() {
    String out = new HtmlPolicyBuilder().toFactory()
        .sanitize("alpha<!--secret--><!DOCTYPE html>omega");
    assertEquals("alphaomega", out);
  }

  /** Verifies: JHS-TEL-001. Seam: state consistency. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void telemetryReportsDroppedCanonicalTag() {
    RecordingListener listener = new RecordingListener();
    new HtmlPolicyBuilder().toFactory().sanitize("<ASIDE>x</ASIDE>", listener, "ctx-a");
    assertEquals(Collections.singletonList("ctx-a:aside"), listener.tags);
  }

  /** Verifies: JHS-TEL-002. Seam: state consistency. Depends-On: rejectAllAttributePolicyReturnsNull. */
  @Test public void telemetryReportsDiscardedAttributeOnRetainedTag() {
    RecordingListener listener = new RecordingListener();
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    f.sanitize("<p data-x='1'>x</p>", listener, "ctx-b");
    assertEquals(Collections.singletonList("ctx-b:p:[data-x]"), listener.attributes);
  }

  /** Verifies: JHS-TEL-003. Seam: state consistency. Depends-On: rejectAllElementPolicyReturnsNull. */
  @Test public void wholeTagDropSuppressesRedundantAttributeNotice() {
    RecordingListener listener = new RecordingListener();
    new HtmlPolicyBuilder().toFactory()
        .sanitize("<aside data-x='1'>x</aside>", listener, "ctx-c");
    assertEquals(Collections.singletonList("ctx-c:aside"), listener.tags);
    assertEquals(Collections.emptyList(), listener.attributes);
  }

  /** Verifies: JHS-TEL-001, JHS-TEL-002. Seam: state consistency. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void telemetryPreservesCallerContextAcrossCallbacks() {
    RecordingListener listener = new RecordingListener();
    new HtmlPolicyBuilder().allowElements("p").toFactory()
        .sanitize("<p bad='1'>x</p><nav>y</nav>", listener, "profile-47");
    assertTrue(listener.attributes.get(0).startsWith("profile-47:"));
    assertTrue(listener.tags.get(0).startsWith("profile-47:"));
  }

  /** Verifies: JHS-SAN-003, JHS-TEL-004. Seam: state consistency. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void telemetryOverloadReturnsSameSanitizedProjection() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    RecordingListener listener = new RecordingListener();
    String plain = f.sanitize("<p>x</p><nav>y</nav>");
    String observed = f.sanitize("<p>x</p><nav>y</nav>", listener, "ctx-d");
    assertEquals(plain, observed);
    assertEquals(Collections.singletonList("ctx-d:nav"), listener.tags);
  }

  /** Verifies: JHS-TEL-005, JHS-TEL-006, JHS-TEL-007, JHS-TEL-008. Seam: protocol handoff. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void changeReporterExposesPairedPublicChannels() {
    RecordingListener listener = new RecordingListener();
    RecordingReceiver sink = new RecordingReceiver();
    HtmlChangeReporter<String> reporter = new HtmlChangeReporter<String>(sink, listener, "ctx-e");
    HtmlSanitizer.Policy policy = new HtmlPolicyBuilder().allowElements("p")
        .build(reporter.getWrappedRenderer());
    reporter.setPolicy(policy);
    HtmlSanitizer.sanitize("<p>x</p><nav>y</nav>", reporter.getWrappedPolicy());
    assertTrue(sink.events.contains("open:p:[]"));
    assertEquals(Collections.singletonList("ctx-e:nav"), listener.tags);
  }
}
