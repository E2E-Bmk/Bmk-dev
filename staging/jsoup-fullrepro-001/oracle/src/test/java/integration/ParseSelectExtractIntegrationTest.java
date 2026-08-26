package integration;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.junit.jupiter.api.Test;

/** Integration tests spanning parsing, selection, and extraction. */
class ParseSelectExtractIntegrationTest {

    private static Document sample() {
        return Jsoup.parse("<div id=a class='c1 c2'><p>1</p><p title=t>2</p><span>3</span></div>"
                + "<div id=b><p>4</p></div>");
    }

    /**
     * Verifies: Representative Workflows — parse, query, and extract in one pass.
     * Depends-On: idClassAndTagSelectors, indexPseudoSelectors, hasAndNotPseudoSelectors,
     * attributePresenceAndExactValue.
     */
    @Test void parseQueryExtractWorkflow() {
        Document doc = sample();
        assertEquals(2, doc.select("#a p").size());
        assertEquals("2", doc.select("p:eq(1)").text());
        assertEquals("a", doc.selectFirst("div:has(span)").id());
        assertEquals("2", doc.select("p[title]").text());
    }

    /**
     * Verifies: Cross-View Invariants — classic getters agree with selector queries.
     * Depends-On: classicGettersReturnMatches, idClassAndTagSelectors.
     */
    @Test void selectResultsAgreeWithClassicGetters() {
        Document doc = Jsoup.parse("<div id=main class=box><p class='box hint'>t</p></div>");
        assertEquals(doc.select("#main").first(), doc.getElementById("main"));
        assertEquals(doc.select("p"), doc.getElementsByTag("p"));
        assertEquals(doc.select(".box"), doc.getElementsByClass("box"));
    }

    /**
     * Verifies: CSS Selector Engine — Elements aggregates project the matched set.
     * Depends-On: idClassAndTagSelectors, textNormalizesWhitespace.
     */
    @Test void elementsAggregatesProjectMatchedSet() {
        Document doc = sample();
        Elements ps = doc.select("p");
        assertEquals(List.of("1", "2", "4"), ps.eachText());
        assertEquals("1 2 4", ps.text());
        assertEquals("t", ps.attr("title"));
    }

    /**
     * Verifies: CSS Selector Engine — Elements filtering narrows a selection.
     * Depends-On: idClassAndTagSelectors.
     */
    @Test void elementsFilteringNarrowsSelection() {
        Document doc = Jsoup.parse("<p class=x>1</p><p>2</p><p class=x>3</p>");
        Elements ps = doc.select("p");
        assertEquals("2", ps.not(".x").text());
        assertEquals("3", ps.eq(2).text());
        assertEquals("1", ps.first().text());
        assertEquals("3", ps.last().text());
    }

    /**
     * Verifies: CSS Selector Engine — nested select scopes to the receiver subtree.
     * Depends-On: idClassAndTagSelectors, childrenAndChildIndex.
     */
    @Test void nestedSelectScopesToSubtree() {
        Document doc = sample();
        Elements inA = doc.select("#a").select("p");
        assertEquals(2, inA.size());
        assertEquals("1 2", inA.text());
        assertEquals(1, doc.select("#b").select("p").size());
    }

    /**
     * Verifies: CSS Selector Engine — comma groups and combinators keep document order.
     * Depends-On: commaGroupReturnsDocumentOrder, siblingCombinators.
     */
    @Test void groupAndCombinatorQueriesKeepDocumentOrder() {
        Document doc = Jsoup.parse("<div><p>1<span>2</span></p></div><p>3</p>");
        assertEquals(List.of("12", "2", "3"), doc.select("p, span").eachText());
        Document two = sample();
        assertEquals("2", two.select("div p + p").text());
    }

    /**
     * Verifies: CSS Selector Engine — has and not compose over one tree.
     * Depends-On: hasAndNotPseudoSelectors.
     */
    @Test void hasAndNotComposeAcrossTree() {
        assertEquals("b", sample().select("div:has(p):not(#a)").attr("id"));
    }

    /**
     * Verifies: Parsing and Document Normalization — base URI flows from parse to absUrl.
     * Depends-On: absUrlResolvesAgainstBase, absPrefixEqualsAbsUrl.
     */
    @Test void baseUriFlowsFromParseToAbsUrl() {
        Document doc = Jsoup.parse("<div><a href='x'>l</a></div>", "https://ex.com/a/");
        Element a = doc.selectFirst("a");
        assertEquals("https://ex.com/a/", a.baseUri());
        assertEquals("https://ex.com/a/x", a.absUrl("href"));
        assertEquals(a.absUrl("href"), a.attr("abs:href"));
    }

    /**
     * Verifies: Parsing and Document Normalization — fragment parsing keeps the base URI.
     * Depends-On: parseBodyFragmentPlacesNodesInBody, absUrlResolvesAgainstBase.
     */
    @Test void fragmentParsingKeepsBaseUri() {
        Document doc = Jsoup.parseBodyFragment("<a href='/x'>l</a>", "https://frag.com/");
        assertEquals("https://frag.com/x", doc.selectFirst("a").absUrl("href"));
    }
}
