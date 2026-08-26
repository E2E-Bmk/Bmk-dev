package atomic;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.Entities;
import org.jsoup.nodes.TextNode;
import org.junit.jupiter.api.Test;

/** Atomic tests for text extraction and entity escaping. */
class TextEntitiesAtomicTest {

    private static Element mixed() {
        return Jsoup.parse("<div> Hello   <b>there</b>\n now </div>").selectFirst("div");
    }

    /** Verifies: Text Extraction and Entities — text normalizes whitespace. */
    @Test void textNormalizesWhitespace() {
        assertEquals("Hello there now", mixed().text());
    }

    /** Verifies: Text Extraction and Entities — ownText excludes child elements. */
    @Test void ownTextExcludesChildElements() {
        assertEquals("Hello now", mixed().ownText());
    }

    /** Verifies: Text Extraction and Entities — wholeText preserves whitespace. */
    @Test void wholeTextPreservesWhitespace() {
        assertEquals(" Hello   there\n now ", mixed().wholeText());
    }

    /** Verifies: Text Extraction and Entities — hasText ignores blank content. */
    @Test void hasTextIgnoresBlank() {
        assertFalse(Jsoup.parse("<div> </div>").selectFirst("div").hasText());
        assertTrue(mixed().hasText());
    }

    /** Verifies: Text Extraction and Entities — document text spans head and body. */
    @Test void documentTextSpansHeadAndBody() {
        assertEquals("T B", Jsoup.parse("<head><title>T</title></head><body><p>B</p></body>").text());
    }

    /** Verifies: Text Extraction and Entities — pre element keeps whitespace on output. */
    @Test void preElementKeepsWhitespace() {
        Document doc = Jsoup.parse("<pre>  keep   me\nplease</pre>");
        assertEquals("<pre>  keep   me\nplease</pre>", doc.body().html());
    }

    /** Verifies: Text Extraction and Entities — TextNode carries character data. */
    @Test void textNodeCarriesCharacterData() {
        TextNode tn = new TextNode("some text");
        assertEquals("some text", tn.text());
        assertEquals("#text", tn.nodeName());
    }

    /** Verifies: Text Extraction and Entities — Entities.escape default repertoire. */
    @Test void entitiesEscapeDefaults() {
        assertEquals("&lt; &gt; &amp; &quot; &apos;", Entities.escape("< > & \" '"));
    }

    /** Verifies: Text Extraction and Entities — Entities.unescape named and numeric. */
    @Test void entitiesUnescapeNamedAndNumeric() {
        assertEquals("<p> &amp; \u00e9", Entities.unescape("&lt;p&gt; &amp;amp; &eacute;"));
    }

    /** Verifies: Text Extraction and Entities — UTF-8 default emits literals and nbsp entity. */
    @Test void defaultCharsetEmitsLiteralsAndNbspEntity() {
        Document doc = Jsoup.parse("<p>\u00a0 \u00e9 &lt;</p>");
        assertEquals("&nbsp; \u00e9 &lt;", doc.selectFirst("p").html());
    }

    /** Verifies: Text Extraction and Entities — xhtml mode uses numeric nbsp. */
    @Test void xhtmlModeUsesNumericNbsp() {
        Document doc = Jsoup.parse("<p>\u00a0 \u00e9 &lt;</p>");
        doc.outputSettings().escapeMode(Entities.EscapeMode.xhtml);
        assertEquals("&#xa0; \u00e9 &lt;", doc.selectFirst("p").html());
    }

    /** Verifies: Text Extraction and Entities — ascii charset uses base named entities. */
    @Test void asciiCharsetUsesBaseEntities() {
        Document doc = Jsoup.parse("<p>\u00e9 \u2122</p>");
        doc.outputSettings().charset("ascii");
        assertEquals("&eacute; &#x2122;", doc.selectFirst("p").html());
    }

    /** Verifies: Text Extraction and Entities — extended mode uses full entity names. */
    @Test void asciiExtendedModeUsesFullNames() {
        Document doc = Jsoup.parse("<p>\u00e9 \u2122</p>");
        doc.outputSettings().charset("ascii");
        doc.outputSettings().escapeMode(Entities.EscapeMode.extended);
        assertEquals("&eacute; &trade;", doc.selectFirst("p").html());
    }
}
