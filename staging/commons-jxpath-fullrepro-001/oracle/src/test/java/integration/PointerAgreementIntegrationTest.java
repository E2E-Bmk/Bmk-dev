package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Iterator;
import java.util.List;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.Pointer;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Agreement between the query views: values, pointers, nodes, counts. */
class PointerAgreementIntegrationTest {

    /**
     * Verifies: Cross-View Invariants — for a multi-match path, getValue
     * returns iterate's first value, selectSingleNode returns selectNodes's
     * first node, and getPointer's path equals iteratePointers' first path.
     * Depends-On: multiMatchReturnsFirst, canonicalFormsPerModel.
     */
    @Test
    void firstMatchAgreement() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        String path = "employees/name";
        assertEquals(Graphs.drain(ctx.iterate(path)).get(0), ctx.getValue(path));
        assertEquals(ctx.selectNodes(path).get(0), ctx.selectSingleNode(path));
        assertEquals(Graphs.paths(ctx.iteratePointers(path)).get(0), ctx.getPointer(path).asPath());
    }

    /**
     * Verifies: Cross-View Invariants — iterate, iteratePointers, selectNodes,
     * and count() agree on cardinality for bean, map, and DOM paths.
     * Depends-On: countReturnsDouble, mapEntryReadsByKey, elementValueIsText.
     */
    @Test
    void cardinalityAgreement() {
        JXPathContext beans = JXPathContext.newContext(Graphs.company());
        for (String path : List.of("employees", "employees/name", "employees/phones")) {
            int values = Graphs.drain(beans.iterate(path)).size();
            assertEquals(values, Graphs.paths(beans.iteratePointers(path)).size());
            assertEquals(values, beans.selectNodes(path).size());
            assertEquals((double) values, beans.getValue("count(" + path + ")"));
        }
        JXPathContext dom = JXPathContext.newContext(Graphs.companyXml());
        int names = Graphs.drain(dom.iterate("//name")).size();
        assertEquals(names, dom.selectNodes("//name").size());
        assertEquals((double) names, dom.getValue("count(//name)"));
    }

    /**
     * Verifies: Cross-View Invariants — every pointer produced by
     * iteratePointers round-trips its canonical path to its own value.
     * Depends-On: canonicalPathRoundTrips, mapEntryReadsByKey, elementValueIsText.
     */
    @Test
    void allPointersRoundTrip() {
        JXPathContext beans = JXPathContext.newContext(Graphs.company());
        Iterator<Pointer> pointers = beans.iteratePointers("employees/phones");
        while (pointers.hasNext()) {
            Pointer p = pointers.next();
            assertEquals(p.getValue(), beans.getValue(p.asPath()));
        }
        JXPathContext dom = JXPathContext.newContext(Graphs.companyXml());
        Iterator<Pointer> domPointers = dom.iteratePointers("//name");
        while (domPointers.hasNext()) {
            Pointer p = domPointers.next();
            assertEquals(p.getValue(), dom.getValue(p.asPath()));
        }
    }

    /**
     * Verifies: Cross-View Invariants — a write through a pointer is observed
     * by context reads, by the canonical path, and by the caller's object.
     * Depends-On: pointerWritesThrough, oneBasedIndexing.
     */
    @Test
    void pointerWriteVisibleEverywhere() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        Pointer p = ctx.getPointer("phones[2]");
        p.setValue("999");
        assertEquals("999", ctx.getValue("phones[2]"));
        assertEquals("999", ctx.getValue(p.asPath()));
        assertEquals("999", emp.getPhones().get(1));
        assertEquals("999", p.getValue());
    }

    /**
     * Verifies: Cross-View Invariants — strict and lenient contexts over the
     * same graph return identical results for every matching path.
     * Depends-On: strictIsDefaultAndRaises, lenientReturnsNull.
     */
    @Test
    void modeNeutralityForMatches() {
        Graphs.Employee shared = Graphs.employee();
        JXPathContext strict = JXPathContext.newContext(shared);
        JXPathContext lenient = JXPathContext.newContext(shared);
        lenient.setLenient(true);
        for (String path : List.of("name", "age", "phones[2]", "props/grade", "count(phones)")) {
            assertEquals(strict.getValue(path), lenient.getValue(path));
        }
        assertEquals(Graphs.paths(strict.iteratePointers("phones")),
                Graphs.paths(lenient.iteratePointers("phones")));
    }

    /**
     * Verifies: Cross-View Invariants — relative-context values agree with
     * base-context queries over the pointers' root-anchored paths, for every
     * element of an iteration.
     * Depends-On: relativeContextEvaluatesFromPointer, relativePointersAreRootAnchored.
     */
    @Test
    void relativeContextsAgreeWithBase() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        Iterator<Pointer> employees = ctx.iteratePointers("employees");
        List<Object> collected = new java.util.ArrayList<>();
        while (employees.hasNext()) {
            Pointer p = employees.next();
            JXPathContext rel = ctx.getRelativeContext(p);
            collected.add(rel.getValue("name"));
            assertEquals(rel.getValue("age"), ctx.getValue(p.asPath() + "/age"));
        }
        assertEquals(List.of("Ada", "Bob"), collected);
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — getNode and
     * getValue diverge exactly on DOM locations: the node is the Element, the
     * value its text; on bean locations both report the stored object.
     * Depends-On: pointerNodeVersusValue, selectionReturnsElements.
     */
    @Test
    void nodeValueDivergenceIsModelSpecific() {
        JXPathContext dom = JXPathContext.newContext(Graphs.companyXml());
        Pointer domName = dom.getPointer("/company/employee[1]/name");
        assertTrue(domName.getNode() instanceof org.w3c.dom.Element);
        assertEquals("Ada", domName.getValue());
        JXPathContext beans = JXPathContext.newContext(Graphs.company());
        Pointer beanName = beans.getPointer("employees[1]/name");
        assertEquals("Ada", beanName.getNode());
        assertEquals(beanName.getNode(), beanName.getValue());
    }

    /**
     * Verifies: Cross-View Invariants — selectNodes over a union agrees with
     * per-path iteration counts combined.
     * Depends-On: unionCombinesPaths, countReturnsDouble.
     */
    @Test
    void unionCardinalityAgreesWithParts() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        int union = ctx.selectNodes("phones | props/grade").size();
        int parts = Graphs.drain(ctx.iterate("phones")).size()
                + Graphs.drain(ctx.iterate("props/grade")).size();
        assertEquals(parts, union);
        assertEquals(4, union);
    }

    /**
     * Verifies: Cross-View Invariants — the context pointer, getContextBean,
     * and a "." query all report the same root object.
     * Depends-On: contextBeanIsRootReference, contextPointerIsRoot.
     */
    @Test
    void rootViewsAgree() {
        Graphs.Company company = Graphs.company();
        JXPathContext ctx = JXPathContext.newContext(company);
        assertTrue(ctx.getContextBean() == company);
        assertTrue(ctx.getValue(".") == company);
        assertTrue(ctx.getContextPointer().getValue() == company);
        assertTrue(ctx.getPointer(".").getRootNode() == company);
    }
}
