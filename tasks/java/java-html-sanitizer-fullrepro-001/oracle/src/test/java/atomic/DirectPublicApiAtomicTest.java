package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.owasp.html.AttributePolicy;
import org.owasp.html.CssSchema;
import org.owasp.html.ElementPolicy;
import org.owasp.html.FilterUrlByProtocolAttributePolicy;
import org.owasp.html.Handler;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.HtmlStreamEventReceiverWrapper;
import org.owasp.html.TagBalancingHtmlStreamEventReceiver;
import support.RecordingReceiver;

/** Atomic tests that invoke one public behavior boundary directly. */
public class DirectPublicApiAtomicTest {
  /** Verifies: JHS-POL-010. */
  @Test public void defaultSkipSetContainsDocumentedFamily() {
    assertEquals(new java.util.HashSet<String>(Arrays.asList("a", "font", "img", "input", "span")),
        HtmlPolicyBuilder.DEFAULT_SKIP_IF_EMPTY);
  }

  /** Verifies: JHS-POL-024, JHS-ERR-001. */
  @Test public void nullElementNameRaisesRuntimeFailure() {
    assertThrows(RuntimeException.class,
        () -> new HtmlPolicyBuilder().allowElements(new String[] { null }));
  }

  /** Verifies: JHS-POL-024, JHS-ERR-001. */
  @Test public void nullAttributeNameRaisesRuntimeFailure() {
    assertThrows(RuntimeException.class,
        () -> new HtmlPolicyBuilder().allowAttributes(new String[] { null }));
  }

  /** Verifies: JHS-POL-022. */
  @Test public void identityAttributePolicyReturnsValue() {
    assertEquals("violet", AttributePolicy.IDENTITY_ATTRIBUTE_POLICY.apply("p", "title", "violet"));
  }

  /** Verifies: JHS-POL-023. */
  @Test public void rejectAllAttributePolicyReturnsNull() {
    assertNull(AttributePolicy.REJECT_ALL_ATTRIBUTE_POLICY.apply("p", "title", "violet"));
  }

  /** Verifies: JHS-POL-021. */
  @Test public void joinedAttributePoliciesTransformInOrder() {
    AttributePolicy joined = AttributePolicy.Util.join(
        (e, a, v) -> v + "-first", (e, a, v) -> v + "-second");
    assertEquals("seed-first-second", joined.apply("p", "data-x", "seed"));
  }

  /** Verifies: JHS-POL-021. */
  @Test public void joinedAttributePoliciesStopAfterRejection() {
    AtomicInteger calls = new AtomicInteger();
    AttributePolicy joined = AttributePolicy.Util.join(
        (e, a, v) -> null, (e, a, v) -> { calls.incrementAndGet(); return v; });
    assertNull(joined.apply("p", "data-x", "seed"));
    assertEquals(0, calls.get());
  }

  /** Verifies: JHS-POL-022. */
  @Test public void identityElementPolicyReturnsElementName() {
    List<String> attrs = new ArrayList<String>(Arrays.asList("title", "v"));
    assertEquals("p", ElementPolicy.IDENTITY_ELEMENT_POLICY.apply("p", attrs));
    assertEquals(Arrays.asList("title", "v"), attrs);
  }

  /** Verifies: JHS-POL-023. */
  @Test public void rejectAllElementPolicyReturnsNull() {
    assertNull(ElementPolicy.REJECT_ALL_ELEMENT_POLICY.apply("p", new ArrayList<String>()));
  }

  /** Verifies: JHS-POL-021. */
  @Test public void joinedElementPoliciesTransformInOrder() {
    ElementPolicy joined = ElementPolicy.Util.join(
        (name, attrs) -> "section", (name, attrs) -> name.equals("section") ? "article" : "wrong");
    assertEquals("article", joined.apply("p", new ArrayList<String>()));
  }

  /** Verifies: JHS-POL-021. */
  @Test public void joinedElementPoliciesStopAfterRejection() {
    AtomicInteger calls = new AtomicInteger();
    ElementPolicy joined = ElementPolicy.Util.join(
        (name, attrs) -> null,
        (name, attrs) -> { calls.incrementAndGet(); return name; });
    assertNull(joined.apply("p", new ArrayList<String>()));
    assertEquals(0, calls.get());
  }

  /** Verifies: JHS-ATTR-017. */
  @Test public void urlPolicyAcceptsRelativePath() {
    FilterUrlByProtocolAttributePolicy p =
        new FilterUrlByProtocolAttributePolicy(Collections.<String>emptyList());
    assertEquals("/docs/item?q=7", p.apply("a", "href", " /docs/item?q=7 "));
  }

  /** Verifies: JHS-ATTR-016, JHS-ATTR-020. */
  @Test public void urlPolicyAcceptsConfiguredHttpsScheme() {
    FilterUrlByProtocolAttributePolicy p =
        new FilterUrlByProtocolAttributePolicy(Collections.singletonList("https"));
    assertEquals("https://example.test/path", p.apply("a", "href", "https://example.test/path"));
  }

  /** Verifies: JHS-ATTR-018. */
  @Test public void urlPolicyRejectsUnconfiguredScheme() {
    FilterUrlByProtocolAttributePolicy p =
        new FilterUrlByProtocolAttributePolicy(Collections.singletonList("https"));
    assertNull(p.apply("a", "href", "javascript:alert(7)"));
  }

  /** Verifies: JHS-ATTR-019. */
  @Test public void protocolRelativeUrlRequiresBothWebSchemes() {
    FilterUrlByProtocolAttributePolicy p =
        new FilterUrlByProtocolAttributePolicy(Arrays.asList("http", "https"));
    assertEquals("//cdn.example.test/a", p.apply("img", "src", "//cdn.example.test/a"));
  }

  /** Verifies: JHS-ATTR-019. */
  @Test public void protocolRelativeUrlRejectsSingleWebSchemeSet() {
    FilterUrlByProtocolAttributePolicy p =
        new FilterUrlByProtocolAttributePolicy(Collections.singletonList("https"));
    assertNull(p.apply("img", "src", "//cdn.example.test/a"));
  }

  /** Verifies: JHS-ATTR-020. */
  @Test public void acceptedUrlEncodesParenthesesAndTrimsHtmlSpace() {
    FilterUrlByProtocolAttributePolicy p =
        new FilterUrlByProtocolAttributePolicy(Collections.singletonList("https"));
    String value = p.apply("a", "href", "  https://example.test/a(b)  ");
    assertEquals("https://example.test/a%28b%29", value);
  }

  /** Verifies: JHS-ATTR-032. */
  @Test public void cssSchemaWithOneKnownPropertyHasExactProjection() {
    assertEquals(Collections.singleton("color"),
        CssSchema.withProperties(Collections.singletonList("color")).allowedProperties());
  }

  /** Verifies: JHS-ATTR-032. */
  @Test public void cssSchemaWithMultipleKnownPropertiesHasExactProjection() {
    Set<String> actual = CssSchema.withProperties(Arrays.asList("color", "font-weight"))
        .allowedProperties();
    assertEquals(2, actual.size());
    assertTrue(actual.containsAll(Arrays.asList("color", "font-weight")));
  }

  /** Verifies: JHS-ATTR-032. */
  @Test public void cssSchemaAcceptsEmptyPropertySelection() {
    assertEquals(Collections.emptySet(),
        CssSchema.withProperties(Collections.<String>emptyList()).allowedProperties());
  }

  /** Verifies: JHS-ATTR-034. */
  @Test public void cssSchemaUnionCombinesCompatiblePropertySets() {
    CssSchema a = CssSchema.withProperties(Collections.singletonList("color"));
    CssSchema b = CssSchema.withProperties(Collections.singletonList("font-weight"));
    Set<String> actual = CssSchema.union(a, b).allowedProperties();
    assertEquals(2, actual.size());
    assertTrue(actual.containsAll(Arrays.asList("color", "font-weight")));
  }

  /** Verifies: JHS-ATTR-036. */
  @Test public void allowedPropertiesProjectionIsImmutable() {
    Set<String> actual = CssSchema.withProperties(Collections.singletonList("color"))
        .allowedProperties();
    assertThrows(UnsupportedOperationException.class, () -> actual.add("display"));
    assertEquals(Collections.singleton("color"), actual);
  }

  /** Verifies: JHS-ATTR-033, JHS-ERR-002. */
  @Test public void unknownCssPropertyRaisesIllegalArgumentException() {
    assertThrows(IllegalArgumentException.class,
        () -> CssSchema.withProperties(Collections.singletonList("made-up-property-47")));
  }

  /** Verifies: JHS-EVT-024, JHS-ERR-006. */
  @Test public void rendererRoutesInvalidNameAndOmitsContent() {
    StringBuilder output = new StringBuilder();
    List<String> problems = new ArrayList<String>();
    org.owasp.html.HtmlStreamRenderer renderer =
        org.owasp.html.HtmlStreamRenderer.create(output, problems::add);
    renderer.openDocument();
    renderer.openTag("bad name", Collections.<String>emptyList());
    renderer.closeDocument();
    assertFalse(problems.isEmpty());
    assertFalse(output.toString().contains("bad name"));
  }

  /** Verifies: JHS-EVT-004. */
  @Test public void wrapperCloseLeavesNonCloseableSinkUsable() throws Exception {
    RecordingReceiver sink = new RecordingReceiver();
    HtmlStreamEventReceiverWrapper wrapper = new HtmlStreamEventReceiverWrapper(sink) {};
    wrapper.close();
    wrapper.text("after-close");
    assertEquals(Collections.singletonList("text:after-close"), sink.snapshot());
  }

  /** Verifies: JHS-EVT-014. */
  @Test public void balancingLimitSuppressesDeeperStructure() {
    RecordingReceiver sink = new RecordingReceiver();
    TagBalancingHtmlStreamEventReceiver balancer = new TagBalancingHtmlStreamEventReceiver(sink);
    balancer.setNestingLimit(1);
    balancer.openDocument();
    balancer.openTag("div", Collections.<String>emptyList());
    balancer.openTag("p", Collections.<String>emptyList());
    balancer.closeDocument();
    assertTrue(sink.events.contains("open:div:[]"));
    assertFalse(sink.events.contains("open:p:[]"));
  }

  /** Verifies: JHS-EVT-013, JHS-ERR-004. */
  @Test public void balancingRejectsLimitBelowCurrentDepth() {
    RecordingReceiver sink = new RecordingReceiver();
    TagBalancingHtmlStreamEventReceiver balancer = new TagBalancingHtmlStreamEventReceiver(sink);
    balancer.openDocument();
    balancer.openTag("div", Collections.<String>emptyList());
    assertThrows(IllegalStateException.class, () -> balancer.setNestingLimit(0));
    assertTrue(sink.events.contains("open:div:[]"));
  }
}
