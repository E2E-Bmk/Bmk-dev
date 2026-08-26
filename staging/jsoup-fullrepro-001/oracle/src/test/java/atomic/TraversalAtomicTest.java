package atomic;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.junit.jupiter.api.Test;

/** Atomic tests for DOM traversal accessors. */
class TraversalAtomicTest {

    private static Document threePs() {
        return Jsoup.parse("<div><p>a</p><p>b</p><p>c</p></div>");
    }

    /** Verifies: DOM Traversal and Manipulation — children and indexed child access. */
    @Test void childrenAndChildIndex() {
        Element div = threePs().selectFirst("div");
        assertEquals(3, div.children().size());
        assertEquals("c", div.child(2).text());
    }

    /** Verifies: DOM Traversal and Manipulation — childNodes covers all node types. */
    @Test void childNodesCountAllTypes() {
        Element div = Jsoup.parse("<div>text<!-- c --><p>e</p></div>").selectFirst("div");
        assertEquals(3, div.childNodeSize());
        assertEquals("#comment", div.childNode(1).nodeName());
        assertEquals(3, div.childNodes().size());
    }

    /** Verifies: DOM Traversal and Manipulation — parent and ancestor chain. */
    @Test void parentAndParentsChain() {
        Element mid = threePs().select("p").get(1);
        assertEquals("div", mid.parent().tagName());
        assertEquals(3, mid.parents().size());
        assertEquals("div", mid.parents().first().tagName());
        assertEquals("html", mid.parents().last().tagName());
    }

    /** Verifies: DOM Traversal and Manipulation — sibling navigation. */
    @Test void siblingNavigation() {
        Element mid = threePs().select("p").get(1);
        assertEquals("c", mid.nextElementSibling().text());
        assertEquals("a", mid.previousElementSibling().text());
    }

    /** Verifies: DOM Traversal and Manipulation — sibling index and sibling elements. */
    @Test void elementSiblingIndexAndSiblingElements() {
        Element mid = threePs().select("p").get(1);
        assertEquals(1, mid.elementSiblingIndex());
        assertEquals(2, mid.siblingElements().size());
    }

    /** Verifies: DOM Traversal and Manipulation — root and owner document. */
    @Test void rootAndOwnerDocument() {
        Document doc = threePs();
        Element leaf = doc.selectFirst("p");
        assertSame(doc, leaf.ownerDocument());
        assertEquals("#document", leaf.root().nodeName());
    }

    /** Verifies: DOM Traversal and Manipulation — cssSelector builds a unique path. */
    @Test void cssSelectorBuildsUniquePath() {
        Document doc = Jsoup.parse("<div id=q><p class='a b'>x</p><p>y</p></div>");
        assertEquals("html > body > div > p:nth-child(2)", doc.select("p").get(1).cssSelector());
    }

    /** Verifies: DOM Traversal and Manipulation — detached element has null parent. */
    @Test void detachedElementHasNullParent() {
        Element made = new Element("span");
        assertNull(made.parent());
        assertFalse(made.hasParent());
    }

    /** Verifies: Error Semantics — child index out of range raises. */
    @Test void childOutOfRangeRaises() {
        Element div = Jsoup.parse("<div></div>").selectFirst("div");
        assertThrows(IndexOutOfBoundsException.class, () -> div.child(5));
    }

    /** Verifies: CSS Selector Engine — classic getters return matching elements. */
    @Test void classicGettersReturnMatches() {
        Document doc = Jsoup.parse("<div id=main class=box><p class='box hint'>t</p></div>");
        assertEquals("div", doc.getElementById("main").tagName());
        assertEquals(1, doc.getElementsByTag("p").size());
        assertEquals(2, doc.getElementsByClass("box").size());
    }
}
