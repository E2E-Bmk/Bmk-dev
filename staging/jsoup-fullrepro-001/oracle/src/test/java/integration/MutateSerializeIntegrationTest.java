package integration;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.junit.jupiter.api.Test;
import support.Text;

/** Integration tests spanning DOM mutation and serialization. */
class MutateSerializeIntegrationTest {

    /**
     * Verifies: Representative Workflows — append and prepend render in order.
     * Depends-On: childrenAndChildIndex, prettyPrintIsDefaultWithOneSpaceIndent.
     */
    @Test void appendPrependRenderInOrder() {
        Document doc = Jsoup.parse("<div><p>One</p></div>");
        Element div = doc.selectFirst("div");
        div.appendElement("p").text("Two");
        div.prependElement("p").text("Zero");
        assertEquals(Text.join(
                "<p>Zero</p>",
                "<p>One</p>",
                "<p>Two</p>"), div.html());
    }

    /**
     * Verifies: DOM Traversal and Manipulation — wrap adds structure around an element.
     * Depends-On: childrenAndChildIndex, nestedBlocksIndentPerDepth.
     */
    @Test void wrapAddsStructureAroundElement() {
        Document doc = Jsoup.parse("<div><p>One</p><p>Two</p></div>");
        Element div = doc.selectFirst("div");
        div.select("p").last().wrap("<section></section>");
        assertEquals(Text.join(
                "<p>One</p>",
                "<section>",
                " <p>Two</p>",
                "</section>"), div.html());
    }

    /**
     * Verifies: DOM Traversal and Manipulation — before and after insert siblings.
     * Depends-On: siblingNavigation, childNodesCountAllTypes.
     */
    @Test void beforeAndAfterInsertSiblings() {
        Document doc = Jsoup.parse("<div><p>mid</p></div>");
        Element p = doc.selectFirst("p");
        p.before("<hr>");
        p.after("<span>tail</span>");
        Element div = doc.selectFirst("div");
        assertEquals("hr", div.childNode(0).nodeName());
        assertEquals("p", div.child(1).tagName());
        assertEquals("tail", div.child(2).text());
    }

    /**
     * Verifies: DOM Traversal and Manipulation — remove deletes and unwrap keeps children.
     * Depends-On: childrenAndChildIndex, textNormalizesWhitespace.
     */
    @Test void removeDeletesAndUnwrapKeepsChildren() {
        Document doc = Jsoup.parse("<div><span><b>keep</b> me</span><p>drop</p></div>");
        doc.selectFirst("p").remove();
        doc.selectFirst("span").unwrap();
        assertEquals("<b>keep</b> me", doc.selectFirst("div").html());
    }

    /**
     * Verifies: DOM Traversal and Manipulation — replaceWith swaps a node in place.
     * Depends-On: childrenAndChildIndex.
     */
    @Test void replaceWithSwapsNode() {
        Document doc = Jsoup.parse("<div><p>a</p><p>b</p></div>");
        doc.selectFirst("p").replaceWith(new Element("h1").text("H"));
        assertEquals(Text.join(
                "<h1>H</h1>",
                "<p>b</p>"), doc.selectFirst("div").html());
    }

    /**
     * Verifies: DOM Traversal and Manipulation — empty removes all children.
     * Depends-On: childNodesCountAllTypes.
     */
    @Test void emptyRemovesAllChildren() {
        Document doc = Jsoup.parse("<div><p>a</p>text</div>");
        Element div = doc.selectFirst("div");
        div.empty();
        assertEquals("", div.html());
        assertEquals(0, div.childNodeSize());
    }

    /**
     * Verifies: Text Extraction and Entities — text setter escapes markup on output.
     * Depends-On: textNormalizesWhitespace, entitiesEscapeDefaults.
     */
    @Test void textSetterEscapesMarkup() {
        Element div = Jsoup.parse("<div><b>old</b></div>").selectFirst("div");
        div.text("plain & new");
        assertEquals("plain &amp; new", div.html());
        div.appendText(" tail");
        assertEquals("plain &amp; new tail", div.html());
        assertEquals("plain & new tail", div.text());
    }

    /**
     * Verifies: DOM Traversal and Manipulation — html setter replaces children with markup.
     * Depends-On: childrenAndChildIndex.
     */
    @Test void htmlSetterReplacesChildren() {
        Element div = Jsoup.parse("<div>x</div>").selectFirst("div");
        div.html("<i>new</i>");
        assertEquals("<i>new</i>", div.html());
        assertEquals("i", div.child(0).tagName());
    }

    /**
     * Verifies: Cross-View Invariants — bulk Elements ops equal per-element ops.
     * Depends-On: classListManagement, idClassAndTagSelectors.
     */
    @Test void bulkClassOperationVisibleEverywhere() {
        Document doc = Jsoup.parse("<p class=x>1</p><p>2</p><p class=x>3</p>");
        Elements ps = doc.select("p");
        ps.addClass("added");
        for (Element p : ps) {
            assertTrue(p.hasClass("added"));
        }
        assertEquals(Text.join(
                "<p class=\"x added\">1</p>",
                "<p class=\"added\">2</p>",
                "<p class=\"x added\">3</p>"), doc.body().html());
    }

    /**
     * Verifies: State Model — clone is deep and independent.
     * Depends-On: textNormalizesWhitespace, childrenAndChildIndex.
     */
    @Test void cloneIsDeepAndIndependent() {
        Element orig = Jsoup.parse("<div><p>orig</p></div>").selectFirst("div");
        Element copy = orig.clone();
        copy.selectFirst("p").text("changed");
        assertEquals("orig", orig.text());
        assertEquals("changed", copy.text());
    }

    /**
     * Verifies: Cross-View Invariants — serialization fixpoint after mutation.
     * Depends-On: outerHtmlEqualsHtmlOnDocument, prettyPrintIsDefaultWithOneSpaceIndent.
     */
    @Test void serializationFixpointHoldsAfterMutation() {
        Document doc = Jsoup.parse("<div><p>keep</p></div>");
        doc.selectFirst("p").text("changed & escaped");
        String once = doc.html();
        assertEquals(once, Jsoup.parse(once).html());
        assertEquals(doc.html(), doc.outerHtml());
    }

    /**
     * Verifies: Cross-View Invariants — cssSelector round trips to the same element.
     * Depends-On: cssSelectorBuildsUniquePath.
     */
    @Test void cssSelectorRoundTripsToSameElement() {
        Document doc = Jsoup.parse("<div><p>a</p><p>b</p></div>");
        Element target = doc.select("p").get(1);
        assertSame(target, doc.selectFirst(target.cssSelector()));
    }

    /**
     * Verifies: DOM Traversal and Manipulation — tag rename and created nodes serialize.
     * Depends-On: detachedElementHasNullParent.
     */
    @Test void createdElementsRenameAndAttach() {
        Element made = new Element("span");
        made.text("made");
        assertEquals("<span>made</span>", made.outerHtml());
        made.tagName("em");
        assertEquals("<em>made</em>", made.outerHtml());
        Element div = Jsoup.parse("<div></div>").selectFirst("div");
        div.appendChild(made);
        assertEquals("<em>made</em>", div.html());
        assertEquals("div", made.parent().tagName());
    }
}
