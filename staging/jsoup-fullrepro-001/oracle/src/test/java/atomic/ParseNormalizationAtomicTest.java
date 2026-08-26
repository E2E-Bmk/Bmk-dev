package atomic;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.junit.jupiter.api.Test;
import support.Text;

/** Atomic tests for parse entry points and HTML normalization. */
class ParseNormalizationAtomicTest {

    /** Verifies: Parsing and Document Normalization — implicit html/head/body creation. */
    @Test void parseAddsImplicitHtmlHeadBody() {
        Document doc = Jsoup.parse("<p>One");
        doc.outputSettings().prettyPrint(false);
        assertEquals("<html><head></head><body><p>One</p></body></html>", doc.html());
    }

    /** Verifies: Parsing and Document Normalization — title element moves into head. */
    @Test void titleElementMovesIntoHead() {
        Document doc = Jsoup.parse("<TITLE>T</TITLE><P CLASS=Foo>x");
        assertEquals("<title>T</title>", doc.head().html());
        assertEquals("T", doc.title());
    }

    /** Verifies: Parsing and Document Normalization — tag and attribute names lowercased. */
    @Test void tagAndAttributeNamesAreLowercased() {
        Document doc = Jsoup.parse("<TITLE>T</TITLE><P CLASS=Foo>x");
        assertEquals("<p class=\"Foo\">x</p>", doc.body().html());
    }

    /** Verifies: Parsing and Document Normalization — attribute values keep their case. */
    @Test void attributeValuesKeepCase() {
        Element p = Jsoup.parse("<p CLASS=Foo>x</p>").selectFirst("p");
        assertEquals("Foo", p.attr("class"));
    }

    /** Verifies: Parsing and Document Normalization — parseBodyFragment places nodes in body. */
    @Test void parseBodyFragmentPlacesNodesInBody() {
        Document doc = Jsoup.parseBodyFragment("<b>bold</b> text");
        assertEquals("<b>bold</b> text", doc.body().html());
    }

    /** Verifies: Parsing and Document Normalization — createShell returns an empty normalized document. */
    @Test void createShellIsEmptyNormalizedDocument() {
        Document shell = Document.createShell("https://base/");
        assertEquals(Text.join(
                "<html>",
                " <head></head>",
                " <body></body>",
                "</html>"), shell.html());
    }

    /** Verifies: Parsing and Document Normalization — doctype preserved as first child. */
    @Test void doctypeIsPreservedAsFirstChild() {
        Document doc = Jsoup.parse("<!DOCTYPE html><p>x</p>");
        assertEquals("#doctype", doc.childNode(0).nodeName());
        assertEquals("<!doctype html>", doc.childNode(0).outerHtml());
    }

    /** Verifies: Parsing and Document Normalization — unclosed li elements are closed. */
    @Test void unclosedListItemsAreClosed() {
        Document doc = Jsoup.parse("<div><p>a<span>b</span></p><ul><li>1<li>2</ul></div>");
        assertEquals(Text.join(
                "<div>",
                " <p>a<span>b</span></p>",
                " <ul>",
                "  <li>1</li>",
                "  <li>2</li>",
                " </ul>",
                "</div>"), doc.body().html());
    }

    /** Verifies: Parsing and Document Normalization — table acquires implicit tbody. */
    @Test void tableAcquiresImplicitTbody() {
        Document doc = Jsoup.parse("<table><tr><td>ok</td></tr></table>");
        Element tbody = doc.selectFirst("tbody");
        assertNotNull(tbody);
        assertEquals("ok", tbody.selectFirst("td").text());
    }

    /** Verifies: Parsing and Document Normalization — script content is data, not text. */
    @Test void scriptContentIsDataNotText() {
        Element script = Jsoup.parse("<script>var a=1;</script>").selectFirst("script");
        assertEquals("var a=1;", script.data());
        assertEquals("", script.text());
    }

    /** Verifies: Parsing and Document Normalization — document node name and empty location. */
    @Test void documentNodeNameAndLocation() {
        Document doc = Jsoup.parse("<p>x</p>");
        assertEquals("#document", doc.nodeName());
        assertEquals("", doc.location());
    }
}
