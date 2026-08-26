package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.apache.commons.jxpath.JXPathContext;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Element;
import support.Graphs;

/** DOM model: element text, attributes, canonical paths, mutation. */
class DomAtomicTest {

    /**
     * Verifies: Object Models — getValue on a DOM element returns its text
     * content.
     */
    @Test
    void elementValueIsText() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertEquals("Ada", ctx.getValue("/company/employee[1]/name"));
        assertEquals("45", ctx.getValue("//employee[2]/age"));
    }

    /**
     * Verifies: Object Models — getValue on an element with children returns
     * all descendant text concatenated.
     */
    @Test
    void elementValueConcatenatesDescendantText() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertEquals("Ada36", ctx.getValue("//employee[1]"));
    }

    /**
     * Verifies: Object Models — @attr reads attributes and attribute
     * predicates filter elements.
     */
    @Test
    void attributesReadAndFilter() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertEquals("e1", ctx.getValue("/company/employee[1]/@id"));
        assertEquals("Bob", ctx.getValue("/company/employee[@id = 'e2']/name"));
    }

    /**
     * Verifies: Object Models — text() selects text nodes and name() returns
     * the element name.
     */
    @Test
    void textAndNameFunctions() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertEquals("Ada", ctx.getValue("/company/employee[1]/name/text()"));
        assertEquals("employee", ctx.getValue("name(/company/employee[1])"));
    }

    /**
     * Verifies: Object Models — selectSingleNode and selectNodes return the
     * Element objects themselves.
     */
    @Test
    void selectionReturnsElements() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertTrue(ctx.selectSingleNode("/company/employee[1]") instanceof Element);
        List<?> nodes = ctx.selectNodes("//employee");
        assertEquals(2, nodes.size());
        assertTrue(nodes.get(1) instanceof Element);
    }

    /**
     * Verifies: Object Models — element text participates in numeric coercion.
     */
    @Test
    void elementTextCoercesNumerically() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertEquals(37.0, ctx.getValue("//employee[1]/age + 1"));
        assertEquals(2.0, ctx.getValue("count(//employee)"));
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — DOM
     * canonical paths carry an explicit index on every step, for elements and
     * attributes.
     */
    @Test
    void domCanonicalPathsAreFullyIndexed() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertEquals("/company[1]/employee[2]/name[1]", ctx.getPointer("//employee[2]/name").asPath());
        assertEquals("/company[1]/employee[1]/@id", ctx.getPointer("/company/employee[1]/@id").asPath());
    }

    /**
     * Verifies: Writing, Creating, and Removing — setValue replaces element
     * text and rewrites attribute values.
     */
    @Test
    void setValueWritesTextAndAttributes() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        ctx.setValue("/company/employee[1]/name", "Grace");
        assertEquals("Grace", ctx.getValue("/company/employee[1]/name"));
        ctx.setValue("/company/employee[1]/@id", "e9");
        assertEquals("e9", ctx.getValue("/company/employee[1]/@id"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — removePath detaches a DOM
     * element from its parent.
     */
    @Test
    void removePathDetachesElement() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        ctx.removePath("/company/employee[2]");
        assertEquals(1.0, ctx.getValue("count(//employee)"));
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — on DOM
     * locations getNode returns the Element while getValue returns its text.
     */
    @Test
    void pointerNodeVersusValue() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.companyXml());
        assertTrue(ctx.getPointer("/company/employee[1]/name").getNode() instanceof Element);
        assertEquals("Ada", ctx.getPointer("/company/employee[1]/name").getValue());
    }
}
