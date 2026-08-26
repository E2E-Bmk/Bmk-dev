package integration;

import static org.junit.jupiter.api.Assertions.*;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.parser.Parser;
import org.jsoup.safety.Cleaner;
import org.jsoup.safety.Safelist;
import org.junit.jupiter.api.Test;
import support.Text;

/** Integration tests for sanitization and the XML parsing mode. */
class CleanXmlIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — static clean equals the Cleaner composition.
     * Depends-On: parseBodyFragmentPlacesNodesInBody, idClassAndTagSelectors.
     */
    @Test void cleanStaticEqualsCleanerComposition() {
        String dirty = "<p onclick=x>keep <b>b</b></p><script>no</script><a href='http://x/'>l</a>";
        String viaStatic = Jsoup.clean(dirty, Safelist.basic());
        String viaCleaner = new Cleaner(Safelist.basic())
                .clean(Jsoup.parseBodyFragment(dirty)).body().html();
        assertEquals(viaCleaner, viaStatic);
        assertEquals("<p>keep <b>b</b></p><a href=\"http://x/\" rel=\"nofollow\">l</a>", viaStatic);
    }

    /**
     * Verifies: Cross-View Invariants — isValid agrees between string and document forms.
     * Depends-On: parseBodyFragmentPlacesNodesInBody.
     */
    @Test void isValidAgreesBetweenProjections() {
        assertTrue(Jsoup.isValid("<p>fine</p>", Safelist.basic()));
        assertFalse(Jsoup.isValid("<script>x</script>", Safelist.basic()));
        Cleaner cleaner = new Cleaner(Safelist.basic());
        assertTrue(cleaner.isValid(Jsoup.parseBodyFragment("<p>fine</p>")));
        assertFalse(cleaner.isValid(Jsoup.parseBodyFragment("<script>x</script>")));
    }

    /**
     * Verifies: Sanitization — basic safelist keeps links and adds nofollow.
     * Depends-On: attrGetSetAndChaining, parseBodyFragmentPlacesNodesInBody.
     */
    @Test void basicSafelistKeepsLinksWithNofollow() {
        String clean = Jsoup.clean(
                "<p><a href='https://x.com/' onclick='y'>go</a></p><script>bad</script>",
                Safelist.basic());
        assertEquals("<p><a href=\"https://x.com/\" rel=\"nofollow\">go</a></p>", clean);
    }

    /**
     * Verifies: Sanitization — none and simpleText safelists.
     * Depends-On: textNormalizesWhitespace.
     */
    @Test void noneAndSimpleTextSafelists() {
        assertEquals("text b", Jsoup.clean("<p>text <b>b</b></p>", Safelist.none()));
        assertEquals("text <b>b</b> <i>i</i>",
                Jsoup.clean("<p>text <b>b</b> <i>i</i></p>", Safelist.simpleText()));
    }

    /**
     * Verifies: Sanitization — image safelist enforces URL protocols.
     * Depends-On: attrGetSetAndChaining, absUrlWithoutBaseIsEmpty.
     */
    @Test void basicWithImagesEnforcesProtocols() {
        assertEquals("<p><img src=\"https://x/i.png\" alt=\"a\"></p>",
                Jsoup.clean("<p><img src='https://x/i.png' alt=a onload=x></p>",
                        Safelist.basicWithImages()));
        assertEquals("<img>", Jsoup.clean("<img src='/rel.png'>", Safelist.basicWithImages()));
    }

    /**
     * Verifies: Sanitization — custom safelist admits configured tags and attributes only.
     * Depends-On: attrGetSetAndChaining, textNormalizesWhitespace.
     */
    @Test void customSafelistAdmitsConfiguredTagsOnly() {
        Safelist custom = Safelist.none().addTags("p", "span").addAttributes("span", "title");
        assertEquals("<p>a <span title=\"t\">s</span></p>d",
                Jsoup.clean("<p>a <span title=t other=x>s</span></p><div>d</div>", custom));
    }

    /**
     * Verifies: Sanitization — removeTags narrows a stock safelist.
     * Depends-On: textNormalizesWhitespace.
     */
    @Test void removeTagsNarrowsStockSafelist() {
        assertEquals("<p>a gone</p>",
                Jsoup.clean("<p>a <b>gone</b></p>", Safelist.basic().removeTags("b")));
    }

    /**
     * Verifies: Sanitization — base URI resolves cleaned links; relative links preservable.
     * Depends-On: absUrlResolvesAgainstBase, attrGetSetAndChaining.
     */
    @Test void baseUriResolvesCleanedLinks() {
        assertEquals("<a href=\"https://base.com/rel\" rel=\"nofollow\">r</a>",
                Jsoup.clean("<a href='/rel'>r</a>", "https://base.com/", Safelist.basic()));
        assertEquals("<a href=\"/rel\" rel=\"nofollow\">r</a>",
                Jsoup.clean("<a href='/rel'>r</a>", "https://base.com/",
                        Safelist.basic().preserveRelativeLinks(true)));
    }

    /**
     * Verifies: Sanitization — relaxed keeps table structure and Cleaner leaves input intact.
     * Depends-On: tableAcquiresImplicitTbody, nestedBlocksIndentPerDepth.
     */
    @Test void relaxedKeepsTableStructure() {
        Document dirty = Jsoup.parse("<table><tr><td>ok</td></tr></table><iframe src=x></iframe>");
        Cleaner cleaner = new Cleaner(Safelist.relaxed());
        Document cleaned = cleaner.clean(dirty);
        assertEquals(Text.join(
                "<table>",
                " <tbody>",
                "  <tr>",
                "   <td>ok</td>",
                "  </tr>",
                " </tbody>",
                "</table>"), cleaned.body().html());
        assertFalse(cleaner.isValid(dirty));
        assertNotNull(dirty.selectFirst("iframe"));
    }

    /**
     * Verifies: XML Parsing Mode — literal structure, declaration node, xml serialization.
     * Depends-On: tagAndAttributeNamesAreLowercased, xmlSyntaxSelfClosesVoidElements,
     * parseAddsImplicitHtmlHeadBody.
     */
    @Test void xmlParserPreservesStructureLiterally() {
        Document xml = Jsoup.parse("<Camel attr='A'><self/></Camel>", "", Parser.xmlParser());
        assertEquals("<Camel attr=\"A\"><self /></Camel>", xml.html());
        Document noImplicit = Jsoup.parse("<root><p>One", "", Parser.xmlParser());
        assertEquals("<root><p>One</p></root>", noImplicit.html());
        assertNull(noImplicit.selectFirst("body"));
        Document decl = Jsoup.parse("<?xml version='1.0'?><root/>", "", Parser.xmlParser());
        assertEquals("#declaration", decl.childNode(0).nodeName());
        assertEquals("<?xml version=\"1.0\"?><root />", decl.html());
    }

    /**
     * Verifies: XML Parsing Mode — html parser named by htmlParser applies HTML rules.
     * Depends-On: parseAddsImplicitHtmlHeadBody, tagAndAttributeNamesAreLowercased.
     */
    @Test void htmlParserAppliesHtmlRulesWhenNamed() {
        Document html = Jsoup.parse("<Camel><p>One", "", Parser.htmlParser());
        assertNotNull(html.selectFirst("body"));
        assertEquals("camel", html.body().child(0).tagName());
    }
}
