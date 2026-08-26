package atomic;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Attribute;
import org.jsoup.nodes.Attributes;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.junit.jupiter.api.Test;

/** Atomic tests for attribute and class management. */
class AttributesAtomicTest {

    /** Verifies: DOM Traversal and Manipulation — attr set with chaining and serialization. */
    @Test void attrGetSetAndChaining() {
        Element a = Jsoup.parse("<a href='/x' class='one'>t</a>").selectFirst("a");
        a.attr("href", "/y").attr("data-k", "v").addClass("two");
        assertEquals("<a href=\"/y\" class=\"one two\" data-k=\"v\">t</a>", a.outerHtml());
        assertEquals("/y", a.attr("href"));
    }

    /** Verifies: Error Semantics — absent attribute reads as empty string. */
    @Test void missingAttributeIsEmptyString() {
        Element a = Jsoup.parse("<a>t</a>").selectFirst("a");
        assertEquals("", a.attr("nope"));
    }

    /** Verifies: DOM Traversal and Manipulation — hasAttr and removeAttr. */
    @Test void hasAttrAndRemoveAttr() {
        Element p = Jsoup.parse("<p one=1 two=2>x</p>").selectFirst("p");
        assertTrue(p.hasAttr("one"));
        p.removeAttr("one");
        assertFalse(p.hasAttr("one"));
        assertEquals("<p two=\"2\">x</p>", p.outerHtml());
    }

    /** Verifies: DOM Traversal and Manipulation — attributes collection iterates in order. */
    @Test void attributesCollectionIterationOrder() {
        Attributes attrs = Jsoup.parse("<p one=1 two=2>x</p>").selectFirst("p").attributes();
        assertEquals(2, attrs.size());
        StringBuilder sb = new StringBuilder();
        for (Attribute attr : attrs) {
            sb.append(attr.getKey()).append('=').append(attr.getValue()).append(';');
        }
        assertEquals("one=1;two=2;", sb.toString());
        assertTrue(attrs.hasKey("one"));
        assertFalse(attrs.hasKey("three"));
    }

    /** Verifies: DOM Traversal and Manipulation — boolean attribute value and rendering. */
    @Test void booleanAttributeValueAndRendering() {
        Element cb = Jsoup.parse("<input type=checkbox checked>").selectFirst("input");
        assertEquals("", cb.attr("checked"));
        assertTrue(cb.hasAttr("checked"));
        assertEquals("<input type=\"checkbox\" checked>", cb.outerHtml());
    }

    /** Verifies: DOM Traversal and Manipulation — id accessor. */
    @Test void idAccessor() {
        assertEquals("main", Jsoup.parse("<div id=main></div>").selectFirst("div").id());
        assertEquals("", Jsoup.parse("<div></div>").selectFirst("div").id());
    }

    /** Verifies: DOM Traversal and Manipulation — class list management preserves order. */
    @Test void classListManagement() {
        Element e = Jsoup.parse("<p class='one two'>x</p>").selectFirst("p");
        assertTrue(e.hasClass("one"));
        assertEquals("one two", e.className());
        e.removeClass("one");
        assertEquals("two", e.className());
        e.addClass("three");
        assertEquals("two three", e.className());
        assertEquals(2, e.classNames().size());
    }

    /** Verifies: DOM Traversal and Manipulation — toggleClass adds and removes. */
    @Test void toggleClassAddsAndRemoves() {
        Element e = Jsoup.parse("<p class='two'>x</p>").selectFirst("p");
        e.toggleClass("one");
        assertEquals("two one", e.className());
        e.toggleClass("one");
        assertEquals("two", e.className());
    }

    /** Verifies: DOM Traversal and Manipulation — dataset exposes data-* attributes. */
    @Test void datasetExposesDataAttributes() {
        Element d = Jsoup.parse("<div data-role='m' data-x='1'>t</div>").selectFirst("div");
        assertEquals("m", d.dataset().get("role"));
        assertEquals("1", d.dataset().get("x"));
        assertEquals(2, d.dataset().size());
    }

    /** Verifies: Parsing and Document Normalization — absUrl resolves against base URI. */
    @Test void absUrlResolvesAgainstBase() {
        Document doc = Jsoup.parse("<a href='/path'>x</a>", "https://example.com/dir/");
        assertEquals("https://example.com/path", doc.selectFirst("a").absUrl("href"));
        assertEquals("https://example.com/dir/", doc.selectFirst("a").baseUri());
    }

    /** Verifies: Cross-View Invariants — abs: attribute prefix equals absUrl. */
    @Test void absPrefixEqualsAbsUrl() {
        Document doc = Jsoup.parse("<a href='/path'>x</a>", "https://example.com/dir/");
        Element a = doc.selectFirst("a");
        assertEquals(a.absUrl("href"), a.attr("abs:href"));
    }

    /** Verifies: Parsing and Document Normalization — absUrl without base is empty. */
    @Test void absUrlWithoutBaseIsEmpty() {
        Element a = new Element("a").attr("href", "/x");
        assertEquals("", a.absUrl("href"));
    }

    /** Verifies: Error Semantics — empty attribute key raises IllegalArgumentException. */
    @Test void emptyAttributeKeyRaises() {
        Element a = new Element("a").attr("k", "v");
        assertThrows(IllegalArgumentException.class, () -> a.absUrl(""));
    }
}
