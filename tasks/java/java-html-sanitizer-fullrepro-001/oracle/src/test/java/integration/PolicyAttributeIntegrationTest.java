package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static support.HtmlAssertions.assertContainsAttributes;
import static support.HtmlAssertions.assertTagAbsent;
import static support.HtmlAssertions.assertTagPresent;
import static support.HtmlAssertions.relTokens;

import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.PolicyFactory;

/** Atomic policy-construction and attribute-rule contracts. */
public class PolicyAttributeIntegrationTest {
  /** Verifies: JHS-POL-001, JHS-STATE-001. Seam: config interaction. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void denyAllBuilderRemovesUnlistedMarkup() {
    assertEquals("plain", new HtmlPolicyBuilder().toFactory().sanitize("<b>plain</b>"));
  }

  /** Verifies: JHS-POL-002. Seam: protocol handoff. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void allowElementsCanonicalizesNames() {
    String out = new HtmlPolicyBuilder().allowElements("P").toFactory().sanitize("<P>Hi</P>");
    assertTagPresent(out, "p");
    assertEquals("Hi", out.replaceAll("<[^>]+>", ""));
  }

  /** Verifies: JHS-POL-005. Seam: config interaction. Depends-On: rejectAllElementPolicyReturnsNull. */
  @Test public void disallowElementsRevokesEarlierGrant() {
    String out = new HtmlPolicyBuilder().allowElements("p").disallowElements("P")
        .toFactory().sanitize("<p>Hi</p>");
    assertEquals("Hi", out);
  }

  /** Verifies: JHS-POL-006. Seam: config interaction. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void commonInlineFormattingGrantsMultipleElements() {
    String out = new HtmlPolicyBuilder().allowCommonInlineFormattingElements()
        .toFactory().sanitize("<strong>x</strong><em>y</em>");
    assertTagPresent(out, "strong");
    assertTagPresent(out, "em");
  }

  /** Verifies: JHS-POL-007. Seam: config interaction. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void commonBlockGrantIncludesParagraphAndHeading() {
    String out = new HtmlPolicyBuilder().allowCommonBlockElements()
        .toFactory().sanitize("<p>x</p><h2>y</h2>");
    assertTagPresent(out, "p");
    assertTagPresent(out, "h2");
  }

  /** Verifies: JHS-POL-012. Seam: config interaction. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void allowWithoutAttributesRetainsEmptySpan() {
    String out = new HtmlPolicyBuilder().allowElements("span").allowWithoutAttributes("span")
        .toFactory().sanitize("<span></span>");
    assertTagPresent(out, "span");
  }

  /** Verifies: JHS-POL-011. Seam: config interaction. Depends-On: rejectAllElementPolicyReturnsNull. */
  @Test public void defaultSkipIfEmptyDropsAttributeLessSpan() {
    String out = new HtmlPolicyBuilder().allowElements("span")
        .toFactory().sanitize("<span></span>");
    assertEquals("", out);
  }

  /** Verifies: JHS-POL-009. Seam: config interaction. Depends-On: identityElementPolicyReturnsElementName. */
  @Test public void disallowTextInDropsTextButRetainsGrantedBlock() {
    String out = new HtmlPolicyBuilder().allowElements("p").disallowTextIn("p")
        .toFactory().sanitize("<p>hidden</p>");
    assertTagPresent(out, "p");
    assertFalse(out.contains("hidden"));
  }

  /** Verifies: JHS-POL-003, JHS-ERR-009. Seam: error propagation. Depends-On: rejectAllElementPolicyReturnsNull. */
  @Test public void customElementRejectionIsNonExceptionalAndLocalized() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowElements((name, attrs) -> null, "span").toFactory();
    String out = f.sanitize("<p>outer<span>inner</span></p>");
    assertTagPresent(out, "p");
    assertTagAbsent(out, "span");
    assertTrue(out.contains("outer"));
  }

  /** Verifies: JHS-ATTR-002. Seam: config interaction. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void globalAttributeRuleAppliesAcrossGrantedElements() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p", "div")
        .allowAttributes("title").globally().toFactory();
    String out = f.sanitize("<p title='north'>a</p><div title='south'>b</div>");
    assertContainsAttributes(out, "title=north", "title=south");
  }

  /** Verifies: JHS-ATTR-003. Seam: config interaction. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void elementScopedAttributeDoesNotLeakToOtherElement() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p", "div")
        .allowAttributes("title").onElements("p").toFactory();
    String out = f.sanitize("<p title='north'>a</p><div title='south'>b</div>");
    assertTrue(out.contains("north"));
    assertFalse(out.contains("south"));
  }

  /** Verifies: JHS-ATTR-004. Seam: config interaction. Depends-On: rejectAllAttributePolicyReturnsNull. */
  @Test public void unscopedAttributeBuilderMakesNoGrant() {
    HtmlPolicyBuilder b = new HtmlPolicyBuilder().allowElements("p");
    b.allowAttributes("title");
    String out = b.toFactory().sanitize("<p title='unused'>x</p>");
    assertFalse(out.contains("title"));
  }

  /** Verifies: JHS-ATTR-005. Seam: config interaction. Depends-On: rejectAllAttributePolicyReturnsNull. */
  @Test public void disallowAttributesOverridesGlobalGrant() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("title").globally()
        .disallowAttributes("title").onElements("p").toFactory();
    String out = f.sanitize("<p title='gone'>x</p>");
    assertFalse(out.contains("title"));
  }

  /** Verifies: JHS-ATTR-007. Seam: protocol handoff. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void patternMatcherRequiresFullMatch() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("data-zone").matching(Pattern.compile("[A-Z]{2}[0-9]"))
        .onElements("p").toFactory();
    assertTrue(f.sanitize("<p data-zone='AB7'>x</p>").contains("AB7"));
    assertFalse(f.sanitize("<p data-zone='xAB7y'>x</p>").contains("data-zone"));
  }

  /** Verifies: JHS-ATTR-008. Seam: protocol handoff. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void predicateMatcherControlsEligibility() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("data-rank").matching(v -> v.length() == 4)
        .onElements("p").toFactory();
    assertTrue(f.sanitize("<p data-rank='four'>x</p>").contains("four"));
    assertFalse(f.sanitize("<p data-rank='sixxx'>x</p>").contains("data-rank"));
  }

  /** Verifies: JHS-ATTR-009. Seam: config interaction. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void exactMembershipMatcherIsCaseSensitive() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("dir").matching(false, "ltr").onElements("p").toFactory();
    assertTrue(f.sanitize("<p dir='ltr'>x</p>").contains("dir"));
    assertFalse(f.sanitize("<p dir='LTR'>x</p>").contains("dir"));
  }

  /** Verifies: JHS-ATTR-010. Seam: config interaction. Depends-On: identityAttributePolicyReturnsValue. */
  @Test public void ignoreCaseMembershipAcceptsMixedCase() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("dir").matching(true, "ltr").onElements("p").toFactory();
    assertTrue(f.sanitize("<p dir='LtR'>x</p>").contains("dir"));
  }

  /** Verifies: JHS-ATTR-006. Seam: protocol handoff. Depends-On: joinedAttributePoliciesTransformInOrder. */
  @Test public void chainedMatchersSeeTransformedValue() {
    PolicyFactory f = new HtmlPolicyBuilder().allowElements("p")
        .allowAttributes("data-code").matching((e, a, v) -> v.trim())
        .matching(v -> v.equals("ok")).onElements("p").toFactory();
    String out = f.sanitize("<p data-code='  ok  '>x</p>");
    assertContainsAttributes(out, "data-code=ok");
  }

  /** Verifies: JHS-ATTR-024. Seam: config interaction. Depends-On: urlPolicyAcceptsRelativePath. */
  @Test public void nofollowConfigurationAddsRelationToken() {
    String out = new HtmlPolicyBuilder().allowElements("a")
        .allowAttributes("href").onElements("a").requireRelNofollowOnLinks()
        .toFactory().sanitize("<a href='/local'>x</a>");
    assertTrue(relTokens(out).contains("nofollow"));
  }

  /** Verifies: JHS-ATTR-023, JHS-ATTR-026. Seam: config interaction. Depends-On: urlPolicyAcceptsRelativePath. */
  @Test public void skippedDefaultRelationIsAbsentFromTargetedLink() {
    String out = new HtmlPolicyBuilder().allowElements("a")
        .allowAttributes("href", "target").onElements("a")
        .skipRelsOnLinks("noreferrer").toFactory()
        .sanitize("<a href='/local' target='_blank'>x</a>");
    assertTrue(relTokens(out).contains("noopener"));
    assertFalse(relTokens(out).contains("noreferrer"));
  }
}
