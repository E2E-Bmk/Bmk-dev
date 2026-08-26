package atomic;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Selector;
import org.junit.jupiter.api.Test;

/** Atomic tests for the CSS selector engine. */
class SelectorAtomicTest {

    private static Document twoDivs() {
        return Jsoup.parse("<div id=a class='c1 c2'><p>1</p><p title=t>2</p><span>3</span></div>"
                + "<div id=b><p>4</p></div>");
    }

    /** Verifies: CSS Selector Engine — id, class, and tag selectors. */
    @Test void idClassAndTagSelectors() {
        Document doc = twoDivs();
        assertEquals(2, doc.select("#a p").size());
        assertEquals("a", doc.select(".c1").attr("id"));
        assertEquals("3", doc.select("span").text());
    }

    /** Verifies: CSS Selector Engine — comma group returns document order. */
    @Test void commaGroupReturnsDocumentOrder() {
        Document doc = Jsoup.parse("<div><p>1<span>2</span></p></div><p>3</p>");
        assertEquals(List.of("12", "2", "3"), doc.select("p, span").eachText());
    }

    /** Verifies: CSS Selector Engine — attribute presence and exact-value selectors. */
    @Test void attributePresenceAndExactValue() {
        Document doc = Jsoup.parse("<a href='x' data-k='v'>1</a><b title='exact'>3</b>");
        assertEquals("1", doc.select("[href]").text());
        assertEquals("3", doc.select("[title=exact]").text());
    }

    /** Verifies: CSS Selector Engine — prefix, suffix, and substring attribute selectors. */
    @Test void attributePrefixSuffixSubstring() {
        Document doc = Jsoup.parse("<a href='https://one.com/x.png'>1</a>"
                + "<a href='http://two.org/y.gif'>2</a>");
        assertEquals("1", doc.select("[href^=https]").text());
        assertEquals("2", doc.select("[href$=.gif]").text());
        assertEquals("2", doc.select("[href*=two]").text());
    }

    /** Verifies: CSS Selector Engine — attribute-name prefix selector. */
    @Test void attributeNamePrefixSelector() {
        Document doc = Jsoup.parse("<a href='x' data-k='v'>1</a><a href='y'>2</a>");
        assertEquals("1", doc.select("[^data-]").text());
    }

    /** Verifies: CSS Selector Engine — child combinator with first-child pseudo. */
    @Test void childCombinatorScopesToDirectChildren() {
        assertEquals("1 4", twoDivs().select("div > p:first-child").text());
    }

    /** Verifies: CSS Selector Engine — sibling combinators. */
    @Test void siblingCombinators() {
        Document doc = twoDivs();
        assertEquals("2", doc.select("div p + p").text());
        assertEquals("3", doc.select("p ~ span").text());
    }

    /** Verifies: CSS Selector Engine — index pseudo-selectors lt, gt, eq. */
    @Test void indexPseudoSelectors() {
        Document doc = Jsoup.parse("<ul><li>a</li><li>b</li><li>c</li><li>d</li></ul>");
        assertEquals("a b", doc.select("li:lt(2)").text());
        assertEquals("c d", doc.select("li:gt(1)").text());
        assertEquals("2", twoDivs().select("p:eq(1)").text());
    }

    /** Verifies: CSS Selector Engine — structural pseudo-selectors. */
    @Test void structuralPseudoSelectors() {
        Document doc = Jsoup.parse("<ul><li>a</li><li>b</li><li>c</li><li>d</li></ul>");
        assertEquals("b d", doc.select("li:nth-child(2n)").text());
        assertEquals("d", doc.select("li:last-child").text());
        assertEquals("a", doc.select("li:first-of-type").text());
    }

    /** Verifies: CSS Selector Engine — only-child pseudo-selector. */
    @Test void onlyChildPseudoSelector() {
        Document doc = Jsoup.parse("<div><p>solo</p></div><div><p>a</p><p>b</p></div>");
        assertEquals("solo", doc.select("p:only-child").text());
    }

    /** Verifies: CSS Selector Engine — has and not pseudo-selectors. */
    @Test void hasAndNotPseudoSelectors() {
        Document doc = twoDivs();
        assertEquals("a", doc.select("div:has(span)").attr("id"));
        assertEquals("b", doc.select("div:not(#a)").attr("id"));
    }

    /** Verifies: CSS Selector Engine — contains and containsOwn pseudo-selectors. */
    @Test void containsAndContainsOwn() {
        Document doc = Jsoup.parse("<p>out <b>in</b></p>");
        assertEquals(1, doc.select("p:contains(in)").size());
        assertEquals(1, doc.select("p:containsOwn(out)").size());
        assertEquals(0, doc.select("p:containsOwn(in)").size());
    }

    /** Verifies: CSS Selector Engine — matches regular-expression pseudo-selector. */
    @Test void matchesRegexPseudoSelector() {
        Document doc = Jsoup.parse("<p>abc</p><p>123</p>");
        assertEquals("123", doc.select("p:matches(\\d+)").text());
    }

    /** Verifies: CSS Selector Engine — is reports whether the receiver matches. */
    @Test void isMatchesReceiver() {
        Element a = Jsoup.parse("<a href='x'>1</a>").selectFirst("a");
        assertTrue(a.is("a[href]"));
        assertFalse(a.is("p"));
    }

    /** Verifies: Error Semantics — selectFirst returns first match or null. */
    @Test void selectFirstReturnsFirstMatchOrNull() {
        Document doc = twoDivs();
        assertEquals("4", doc.selectFirst("div#b p").text());
        assertNull(doc.selectFirst("em"));
    }

    /** Verifies: Error Semantics — unparseable query raises SelectorParseException. */
    @Test void unknownPseudoRaisesSelectorParseException() {
        Document doc = twoDivs();
        Selector.SelectorParseException ex = assertThrows(
                Selector.SelectorParseException.class, () -> doc.select("p:unknown(3)"));
        assertTrue(ex.getMessage().contains("p:unknown(3)"));
        assertTrue(ex instanceof IllegalStateException);
    }
}
