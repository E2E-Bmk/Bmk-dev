package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static support.HtmlAssertions.attributePairs;
import static support.HtmlAssertions.assertTagAbsent;
import static support.HtmlAssertions.assertTagPresent;

import java.util.Arrays;
import java.util.Collections;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.owasp.html.CssSchema;
import org.owasp.html.FilterUrlByProtocolAttributePolicy;
import org.owasp.html.Handler;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.HtmlSanitizer;
import org.owasp.html.HtmlStreamEventProcessor;
import org.owasp.html.HtmlStreamEventReceiverWrapper;
import org.owasp.html.HtmlStreamRenderer;
import org.owasp.html.PolicyFactory;
import org.owasp.html.TagBalancingHtmlStreamEventReceiver;
import support.RecordingListener;
import support.RecordingReceiver;

/** Two public-only integration probes for every specified cross-view invariant. */
public class CrossViewInvariantIntegrationTest {
  /** Verifies: JHS-INV-001, JHS-POL-017. Seam: state consistency. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void cvi1GrantedElementAgreesBetweenStringAndEvents() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    String out = f.sanitize("<p>quartz</p>");
    RecordingReceiver events = new RecordingReceiver();
    HtmlSanitizer.sanitize("<p>quartz</p>", f.apply(events));
    assertTagPresent(out, "p");
    assertTrue(events.events.contains("open:p:[]"));
    assertTrue(events.events.contains("text:quartz"));
  }

  /** Verifies: JHS-INV-001, JHS-ATTR-003. Seam: state consistency. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void cvi1GrantedAttributeAgreesBetweenStringAndEvents() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("title").onElements("p").toFactory();
    String out = f.sanitize("<p title='opal'>x</p>");
    RecordingReceiver events = new RecordingReceiver();
    HtmlSanitizer.sanitize("<p title='opal'>x</p>", f.apply(events));
    assertTrue(attributePairs(out).contains("title=opal"));
    assertTrue(events.events.contains("open:p:[title, opal]"));
  }

  /** Verifies: JHS-INV-002, JHS-TEL-001. Seam: state consistency. Depends-On: rejectAllElementPolicyReturnsNull. */
  @Test public void cvi2DroppedTagAgreesWithListenerNotice() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    RecordingListener listener = new RecordingListener();
    String out = f.sanitize("<nav>n</nav><p>p</p>", listener, "ctx-f");
    assertTagAbsent(out, "nav");
    assertEquals(Collections.singletonList("ctx-f:nav"), listener.tags);
  }

  /** Verifies: JHS-INV-002, JHS-TEL-002. Seam: state consistency. Depends-On: rejectAllAttributePolicyReturnsNull. */
  @Test public void cvi2DroppedAttributeAgreesWithListenerNotice() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    RecordingListener listener = new RecordingListener();
    String out = f.sanitize("<p title='discard'>p</p>", listener, "ctx-g");
    assertFalse(attributePairs(out).contains("title=discard"));
    assertEquals(Collections.singletonList("ctx-g:p:[title]"), listener.attributes);
  }

  /** Verifies: JHS-INV-003, JHS-POL-019. Seam: config interaction. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void cvi3FactoryUnionPreservesNonOverlappingGrants() {
    PolicyFactory p = new HtmlPolicyBuilder().allowElements("p").toFactory();
    PolicyFactory q = new HtmlPolicyBuilder().allowElements("blockquote").toFactory();
    String out = p.and(q).sanitize("<p>a</p><blockquote>b</blockquote>");
    assertTagPresent(out, "p");
    assertTagPresent(out, "blockquote");
  }

  /** Verifies: JHS-INV-003, JHS-POL-020. Seam: config interaction. Depends-On: joinedAttributePoliciesStopAfterRejection. */
  @Test public void cvi3FactoryOverlapEnforcesBothValuePolicies() {
    PolicyFactory left = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("data-key").matching(v -> v.startsWith("north"))
        .onElements("p").toFactory();
    PolicyFactory right = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("data-key").matching(v -> v.endsWith("47"))
        .onElements("p").toFactory();
    PolicyFactory both = left.and(right);
    assertTrue(both.sanitize("<p data-key='north47'>x</p>").contains("north47"));
    assertFalse(both.sanitize("<p data-key='north48'>x</p>").contains("data-key"));
  }

  /** Verifies: JHS-INV-004, JHS-EVT-008. Seam: protocol handoff. Depends-On: identityProcessorReturnsSameSink. */
  @Test public void cvi4PreprocessorInsertionStillPassesPolicy() {
    HtmlStreamEventProcessor insert = sink -> new HtmlStreamEventReceiverWrapper(sink) {
      @Override public void openDocument() {
        super.openDocument();
        super.openTag("p", Collections.<String>emptyList());
        super.text("inserted");
        super.closeTag("p");
        super.openTag("nav", Collections.<String>emptyList());
        super.text("blocked");
        super.closeTag("nav");
      }
    };
    String out = new HtmlPolicyBuilder().allowElements("p").withPreprocessor(insert)
        .toFactory().sanitize("base");
    assertTagPresent(out, "p");
    assertFalse(out.contains("<nav"));
    assertTrue(out.contains("inserted"));
  }

  /** Verifies: JHS-INV-004, JHS-EVT-009. Seam: protocol handoff. Depends-On: identityProcessorReturnsSameSink. */
  @Test public void cvi4PostprocessorInsertionFlowsToFinalSink() {
    HtmlStreamEventProcessor insert = sink -> new HtmlStreamEventReceiverWrapper(sink) {
      @Override public void closeDocument() {
        super.openTag("mark", Collections.<String>emptyList());
        super.text("post");
        super.closeTag("mark");
        super.closeDocument();
      }
    };
    String out = new HtmlPolicyBuilder().withPostprocessor(insert).toFactory().sanitize("base");
    assertTagPresent(out, "mark");
    assertTrue(out.contains("post"));
  }

  /** Verifies: JHS-INV-005, JHS-EVT-022. Seam: lifecycle crossing. Depends-On: rendererOpenCloseTransitionsAreObservable. */
  @Test public void cvi5SanitizerLifecycleLeavesRendererClosed() {
    StringBuilder out = new StringBuilder();
    HtmlStreamRenderer renderer = HtmlStreamRenderer.create(out, Handler.DO_NOTHING);
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    HtmlSanitizer.sanitize("<p>cycle</p>", f.apply(renderer));
    assertFalse(renderer.isDocumentOpen());
    assertTagPresent(out.toString(), "p");
  }

  /** Verifies: JHS-INV-005, JHS-EVT-018, JHS-EVT-020. Seam: lifecycle crossing. Depends-On: rendererOpenCloseTransitionsAreObservable. */
  @Test public void cvi5PolicyLifecycleTracksRendererTransitions() {
    StringBuilder out = new StringBuilder();
    HtmlStreamRenderer renderer = HtmlStreamRenderer.create(out, Handler.DO_NOTHING);
    HtmlSanitizer.Policy policy = new HtmlPolicyBuilder().allowElements("p").build(renderer);
    policy.openDocument();
    assertTrue(renderer.isDocumentOpen());
    policy.openTag("p", Collections.<String>emptyList());
    policy.text("manual");
    policy.closeTag("p");
    policy.closeDocument();
    assertFalse(renderer.isDocumentOpen());
    assertTrue(out.toString().contains("manual"));
  }

  /** Verifies: JHS-INV-006, JHS-SAN-010. Seam: protocol handoff. Depends-On: balancingLimitSuppressesDeeperStructure. */
  @Test public void cvi6ParserAndExplicitBalancerAgreeOnMisnestedSequence() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p", "b").toFactory();
    String parsed = f.sanitize("<p><b>nested</p>");
    StringBuilder manual = new StringBuilder();
    HtmlStreamRenderer renderer = HtmlStreamRenderer.create(manual, Handler.DO_NOTHING);
    TagBalancingHtmlStreamEventReceiver balancer = new TagBalancingHtmlStreamEventReceiver(renderer);
    balancer.openDocument();
    balancer.openTag("p", Collections.<String>emptyList());
    balancer.openTag("b", Collections.<String>emptyList());
    balancer.text("nested");
    balancer.closeTag("p");
    balancer.closeDocument();
    assertEquals(parsed, manual.toString());
  }

  /** Verifies: JHS-INV-006, JHS-EVT-011. Seam: lifecycle crossing. Depends-On: balancingLimitSuppressesDeeperStructure. */
  @Test public void cvi6BalancerCloseDocumentMatchesSanitizedAutoClose() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("blockquote").toFactory();
    String parsed = f.sanitize("<blockquote>tail");
    StringBuilder manual = new StringBuilder();
    HtmlStreamRenderer renderer = HtmlStreamRenderer.create(manual, Handler.DO_NOTHING);
    TagBalancingHtmlStreamEventReceiver balancer = new TagBalancingHtmlStreamEventReceiver(renderer);
    balancer.openDocument();
    balancer.openTag("blockquote", Collections.<String>emptyList());
    balancer.text("tail");
    balancer.closeDocument();
    assertEquals(parsed, manual.toString());
  }

  /** Verifies: JHS-INV-007, JHS-ATTR-017. Seam: state consistency. Depends-On: urlPolicyAcceptsRelativePath. */
  @Test public void cvi7RelativeUrlAgreementAcrossDirectAndStringViews() {
    FilterUrlByProtocolAttributePolicy direct =
        new FilterUrlByProtocolAttributePolicy(Collections.singletonList("https"));
    String accepted = direct.apply("a", "href", "/guide?q=9");
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("a")
        .allowUrlProtocols("https").allowAttributes("href").onElements("a").toFactory();
    String out = f.sanitize("<a href='/guide?q=9'>x</a>");
    assertEquals("/guide?q=9", accepted);
    assertTrue(attributePairs(out).stream().anyMatch(v -> v.startsWith("href=/guide?q")));
  }

  /** Verifies: JHS-INV-007, JHS-ATTR-018. Seam: state consistency. Depends-On: urlPolicyRejectsUnconfiguredScheme. */
  @Test public void cvi7RejectedUrlAgreementAcrossDirectAndStringViews() {
    FilterUrlByProtocolAttributePolicy direct =
        new FilterUrlByProtocolAttributePolicy(Collections.singletonList("https"));
    assertNull(direct.apply("a", "href", "ftp://example.test/x"));
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("a")
        .allowUrlProtocols("https").allowAttributes("href").onElements("a").toFactory();
    assertFalse(attributePairs(f.sanitize("<a href='ftp://example.test/x'>x</a>"))
        .contains("href=ftp://example.test/x"));
  }

  /** Verifies: JHS-INV-008, JHS-ATTR-028. Seam: config interaction. Depends-On: cssSchemaWithOneKnownPropertyHasExactProjection. */
  @Test public void cvi8RetainedStylePropertiesAreWithinSchema() {
    CssSchema schema = CssSchema.withProperties(Collections.singletonList("color"));
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").allowStyling(schema).toFactory();
    String out = f.sanitize("<p style='color: navy; position: fixed'>x</p>");
    assertTrue(out.contains("color"));
    assertFalse(out.contains("position"));
    assertEquals(Collections.singleton("color"), schema.allowedProperties());
  }

  /** Verifies: JHS-INV-008, JHS-ATTR-028. Seam: config interaction. Depends-On: cssSchemaWithMultipleKnownPropertiesHasExactProjection. */
  @Test public void cvi8MultiPropertyStyleRemainsSchemaSubset() {
    CssSchema schema = CssSchema.withProperties(Arrays.asList("color", "font-weight"));
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").allowStyling(schema).toFactory();
    String out = f.sanitize("<p style='font-weight: bold; color: teal; left: 3px'>x</p>");
    assertTrue(out.contains("font-weight"));
    assertTrue(out.contains("color"));
    assertFalse(out.contains("left"));
    assertEquals(2, schema.allowedProperties().size());
  }

  /** Verifies: JHS-INV-009, JHS-STATE-002. Seam: lifecycle crossing. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void cvi9RepeatedSanitizeIsDeterministic() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p").toFactory();
    String first = f.sanitize("<p>repeat</p>");
    String second = f.sanitize("<p>repeat</p>");
    assertEquals(first, second);
    assertTagPresent(second, "p");
  }

  /** Verifies: JHS-INV-009, JHS-STATE-002. Seam: lifecycle crossing. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void cvi9InterleavedDocumentsDoNotLeakState() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p", "blockquote").toFactory();
    String first = f.sanitize("<p>one");
    String middle = f.sanitize("<blockquote>two</blockquote>");
    String again = f.sanitize("<p>one");
    assertEquals(first, again);
    assertTagPresent(middle, "blockquote");
    assertTagAbsent(again, "blockquote");
  }
}
