package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.LinkedHashMap;
import java.util.Map;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.Pointer;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** One query language composed across bean, map, collection, and DOM models. */
class CrossModelIntegrationTest {

    private static Map<String, Object> mixedRoot() {
        Map<String, Object> root = new LinkedHashMap<>();
        Graphs.Employee boss = Graphs.employee();
        boss.setAddress(new Graphs.Address("Kyoto", "600"));
        root.put("boss", boss);
        root.put("doc", Graphs.companyXml());
        return root;
    }

    /**
     * Verifies: Object Models — a map entry holding a bean traverses with bean
     * rules from that point on.
     * Depends-On: mapEntryReadsByKey, propertyStepReadsGetterWithType, nestedStepsChain.
     */
    @Test
    void mapToBeanTraversal() {
        JXPathContext ctx = JXPathContext.newContext(mixedRoot());
        assertEquals("Kyoto", ctx.getValue("boss/address/city"));
        assertEquals("111", ctx.getValue("boss/phones[1]"));
    }

    /**
     * Verifies: Object Models — a map entry holding a DOM document continues
     * with DOM rules.
     * Depends-On: mapEntryReadsByKey, elementValueIsText.
     */
    @Test
    void mapToDomTraversal() {
        JXPathContext ctx = JXPathContext.newContext(mixedRoot());
        assertEquals("Bob", ctx.getValue("doc/company/employee[2]/name"));
        assertEquals("e1", ctx.getValue("doc/company/employee[1]/@id"));
    }

    /**
     * Verifies: Cross-View Invariants — pointer round-trip holds across model
     * boundaries: canonical paths through map, bean, and DOM segments re-query
     * to the pointer's value.
     * Depends-On: canonicalPathRoundTrips, rootMapEntryCanonicalForm, domCanonicalPathsAreFullyIndexed.
     */
    @Test
    void mixedCanonicalPathsRoundTrip() {
        JXPathContext ctx = JXPathContext.newContext(mixedRoot());
        Pointer bean = ctx.getPointer("boss/address/city");
        assertEquals("/.[@name='boss']/address/city", bean.asPath());
        assertEquals(bean.getValue(), ctx.getValue(bean.asPath()));
        Pointer dom = ctx.getPointer("doc/company/employee[2]/name");
        assertEquals("/.[@name='doc']/company[1]/employee[2]/name[1]", dom.asPath());
        assertEquals(dom.getValue(), ctx.getValue(dom.asPath()));
    }

    /**
     * Verifies: Object Models — the descendant axis searches across model
     * boundaries.
     * Depends-On: descendantAxisSearchesGraph, elementValueIsText.
     */
    @Test
    void descendantSearchCrossesModels() {
        JXPathContext ctx = JXPathContext.newContext(mixedRoot());
        assertEquals("Kyoto", ctx.getValue("//city"));
        assertEquals(2.0, ctx.getValue("count(//employee)"));
    }

    /**
     * Verifies: Contexts and Path Queries — one logical query phrased against
     * a bean graph and a DOM graph of the same shape reports the same facts.
     * Depends-On: equalityPredicateSelectsElement, attributesReadAndFilter, sumAddsNumerically.
     */
    @Test
    void sameQueryAgreesAcrossModels() {
        JXPathContext beans = JXPathContext.newContext(Graphs.company());
        JXPathContext dom = JXPathContext.newContext(Graphs.companyXml());
        assertEquals(String.valueOf(beans.getValue("employees[name = 'Bob']/age")),
                dom.getValue("/company/employee[name = 'Bob']/age"));
        assertEquals(beans.getValue("sum(employees/age)"), dom.getValue("sum(//employee/age)"));
        assertEquals(beans.getValue("count(employees)"), dom.getValue("count(//employee)"));
    }

    /**
     * Verifies: Variables and Extension Functions — variables drive DOM
     * predicates exactly as bean predicates.
     * Depends-On: variableInPredicate, attributesReadAndFilter.
     */
    @Test
    void variablesDrivePredicatesInBothModels() {
        JXPathContext beans = JXPathContext.newContext(Graphs.company());
        beans.getVariables().declareVariable("min", 40);
        JXPathContext dom = JXPathContext.newContext(Graphs.companyXml());
        dom.getVariables().declareVariable("min", 40);
        assertEquals(1.0, beans.getValue("count(employees[age > $min])"));
        assertEquals(1.0, dom.getValue("count(//employee[age > $min])"));
        assertEquals("Bob", beans.getValue("employees[age > $min]/name"));
        assertEquals("Bob", dom.getValue("//employee[age > $min]/name"));
    }

    /**
     * Verifies: State Model — writes deep in a mixed graph mutate the caller's
     * own objects and are visible to later queries on the same context.
     * Depends-On: setValueConvertsToPropertyType, setValueWritesTextAndAttributes, mapEntryReadsByKey.
     */
    @Test
    void deepWritesMutateCallersObjects() {
        Map<String, Object> root = mixedRoot();
        JXPathContext ctx = JXPathContext.newContext(root);
        ctx.setValue("boss/age", "50");
        assertEquals(50, ((Graphs.Employee) root.get("boss")).getAge());
        ctx.setValue("doc/company/employee[1]/name", "Grace");
        assertEquals("Grace", ctx.getValue("doc/company/employee[1]/name"));
    }

    /**
     * Verifies: State Model — external mutation of the graph is visible to the
     * next query; a new context over the same root sees all prior mutations.
     * Depends-On: propertyStepReadsGetterWithType, setValueConvertsToPropertyType.
     */
    @Test
    void contextsObserveExternalMutation() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext first = JXPathContext.newContext(emp);
        assertEquals("Ada", first.getValue("name"));
        emp.setName("Grace");
        assertEquals("Grace", first.getValue("name"));
        first.setValue("age", 50);
        JXPathContext second = JXPathContext.newContext(emp);
        assertEquals(50, second.getValue("age"));
    }

    /**
     * Verifies: Cross-View Invariants — relative contexts anchored inside a
     * mixed graph report root-anchored paths that agree with base queries.
     * Depends-On: relativePointersAreRootAnchored, elementValueIsText.
     */
    @Test
    void relativeContextsInsideMixedGraph() {
        JXPathContext ctx = JXPathContext.newContext(mixedRoot());
        JXPathContext rel = ctx.getRelativeContext(ctx.getPointer("doc/company/employee[2]"));
        assertEquals("Bob", rel.getValue("name"));
        String anchored = rel.getPointer("name").asPath();
        assertEquals("/.[@name='doc']/company[1]/employee[2]/name[1]", anchored);
        assertEquals("Bob", ctx.getValue(anchored));
        assertTrue(rel.getParentContext() == ctx);
    }
}
