package atomic;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Entities;
import org.junit.jupiter.api.Test;
import support.Text;

/** Atomic tests for serialization output settings. */
class OutputSettingsAtomicTest {

    /** Verifies: Serialization and Output Settings — pretty default with one-space indent. */
    @Test void prettyPrintIsDefaultWithOneSpaceIndent() {
        Document doc = Jsoup.parse("<p>One");
        assertEquals(Text.join(
                "<html>",
                " <head></head>",
                " <body>",
                "  <p>One</p>",
                " </body>",
                "</html>"), doc.html());
    }

    /** Verifies: Serialization and Output Settings — prettyPrint off serializes compact. */
    @Test void prettyPrintOffSerializesCompact() {
        Document doc = Jsoup.parse("<p>One");
        doc.outputSettings().prettyPrint(false);
        assertEquals("<html><head></head><body><p>One</p></body></html>", doc.html());
    }

    /** Verifies: Serialization and Output Settings — default settings projection. */
    @Test void defaultSettingsProjection() {
        Document.OutputSettings settings = Jsoup.parse("<p>x</p>").outputSettings();
        assertTrue(settings.prettyPrint());
        assertEquals(1, settings.indentAmount());
        assertFalse(settings.outline());
        assertEquals(Document.OutputSettings.Syntax.html, settings.syntax());
        assertEquals(Entities.EscapeMode.base, settings.escapeMode());
    }

    /** Verifies: Serialization and Output Settings — indentAmount controls indent width. */
    @Test void indentAmountControlsIndentWidth() {
        Document doc = Jsoup.parse("<div><p>a</p></div>");
        doc.outputSettings().indentAmount(4);
        assertEquals(Text.join(
                "<div>",
                "    <p>a</p>",
                "</div>"), doc.body().html());
    }

    /** Verifies: Serialization and Output Settings — nested blocks indent per depth. */
    @Test void nestedBlocksIndentPerDepth() {
        Document doc = Jsoup.parse("<div><div><p>deep</p></div></div>");
        assertEquals(Text.join(
                "<div>",
                " <div>",
                "  <p>deep</p>",
                " </div>",
                "</div>"), doc.body().html());
    }

    /** Verifies: Serialization and Output Settings — inline elements stay on parent line. */
    @Test void inlineElementsStayOnParentLine() {
        Document doc = Jsoup.parse("<div><span>in</span><a>line</a></div><p>para <b>bold</b> tail</p>");
        assertEquals(Text.join(
                "<div>",
                " <span>in</span><a>line</a>",
                "</div>",
                "<p>para <b>bold</b> tail</p>"), doc.body().html());
    }

    /** Verifies: Serialization and Output Settings — outline treats every element as block. */
    @Test void outlineTreatsInlineAsBlock() {
        Document doc = Jsoup.parse("<p>para <b>bold</b></p>");
        doc.outputSettings().outline(true);
        assertEquals(Text.join(
                "<p>",
                " para ",
                " <b>bold</b>",
                "</p>"), doc.body().html());
    }

    /** Verifies: Serialization and Output Settings — xml syntax self-closes void elements. */
    @Test void xmlSyntaxSelfClosesVoidElements() {
        Document doc = Jsoup.parse("<img src=x><br>");
        doc.outputSettings().syntax(Document.OutputSettings.Syntax.xml);
        assertEquals(Text.join(
                "<img src=\"x\" />",
                "<br />"), doc.body().html());
    }

    /** Verifies: Serialization and Output Settings — html syntax renders void bare. */
    @Test void htmlSyntaxRendersVoidBare() {
        Document doc = Jsoup.parse("<img src=a><input value=b>");
        assertEquals("<img src=\"a\"><input value=\"b\">", doc.body().html());
    }

    /** Verifies: Serialization and Output Settings — document outerHtml equals html. */
    @Test void outerHtmlEqualsHtmlOnDocument() {
        Document doc = Jsoup.parse("<p>One</p>");
        assertEquals(doc.html(), doc.outerHtml());
    }
}
