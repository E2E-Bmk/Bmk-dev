package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;
import org.apache.commons.jxpath.JXPathContext;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Bean model: property steps, attribute form, predicates, enumeration order. */
class BeanQueryAtomicTest {

    /**
     * Verifies: Object Models — a child step named x reads the JavaBeans
     * property x; the value keeps its property type.
     */
    @Test
    void propertyStepReadsGetterWithType() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("Ada", ctx.getValue("name"));
        assertEquals(36, ctx.getValue("age"));
    }

    /**
     * Verifies: Object Models — nested steps chain through the graph.
     */
    @Test
    void nestedStepsChain() {
        Graphs.Employee emp = Graphs.employee();
        emp.setAddress(new Graphs.Address("Oslo", "0150"));
        JXPathContext ctx = JXPathContext.newContext(emp);
        assertEquals("Oslo", ctx.getValue("address/city"));
    }

    /**
     * Verifies: Object Models — the attribute form @x addresses the same bean
     * property as the child form x.
     */
    @Test
    void attributeFormEqualsChildForm() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals(ctx.getValue("name"), ctx.getValue("@name"));
        assertEquals(36, ctx.getValue("@age"));
    }

    /**
     * Verifies: Object Models — predicates filter bean collection elements on
     * property equality.
     */
    @Test
    void equalityPredicateSelectsElement() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals(45, ctx.getValue("employees[name = 'Bob']/age"));
    }

    /**
     * Verifies: Object Models — the suffixed form node[@name='p'] is a
     * property-access form reading the named property of the node.
     */
    @Test
    void attributeAccessFormReadsProperty() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("Ada", ctx.getValue(".[@name='name']"));
        JXPathContext company = JXPathContext.newContext(Graphs.company());
        assertEquals(36, company.getValue("employees[1][@name='age']"));
    }

    /**
     * Verifies: Object Models — comparison predicates select by numeric
     * property value.
     */
    @Test
    void comparisonPredicateSelectsElement() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals("Bob", ctx.getValue("employees[age > 40]/name"));
    }

    /**
     * Verifies: Object Models — wildcard enumeration visits bean properties in
     * ascending alphabetical order with collection elements expanded
     * individually.
     */
    @Test
    void wildcardEnumeratesAlphabeticallyWithExpansion() {
        Graphs.Employee emp = Graphs.employee();
        emp.setAddress(new Graphs.Address("Oslo", "0150"));
        JXPathContext ctx = JXPathContext.newContext(emp);
        assertEquals(
                List.of("/address", "/age", "/name", "/phones[1]", "/phones[2]", "/phones[3]", "/props"),
                Graphs.paths(ctx.iteratePointers("*")));
    }

    /**
     * Verifies: Object Models — a collection-valued property contributes each
     * element as one node to count(*) while a map-valued property contributes
     * itself as one node.
     */
    @Test
    void countStarCountsExpandedNodes() {
        Graphs.Employee emp = Graphs.employee();
        emp.setAddress(new Graphs.Address("Oslo", "0150"));
        JXPathContext ctx = JXPathContext.newContext(emp);
        assertEquals(7.0, ctx.getValue("count(*)"));
    }

    /**
     * Verifies: Contexts and Path Queries — getValue on a multi-match path
     * returns the value of the first matching location.
     */
    @Test
    void multiMatchReturnsFirst() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals("Ada", ctx.getValue("employees/name"));
    }

    /**
     * Verifies: Contexts and Path Queries — position() and last() are usable
     * in predicates over bean collections.
     */
    @Test
    void positionalPredicates() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals("Bob", ctx.getValue("employees[position() > 1]/name"));
        assertEquals("Bob", ctx.getValue("employees[last()]/name"));
    }

    /**
     * Verifies: Object Models — the descendant axis searches the whole bean
     * graph.
     */
    @Test
    void descendantAxisSearchesGraph() {
        Graphs.Company company = Graphs.company();
        company.getEmployees().get(0).setAddress(new Graphs.Address("Oslo", "0150"));
        JXPathContext ctx = JXPathContext.newContext(company);
        assertEquals("Oslo", ctx.getValue("//city"));
    }

    /**
     * Verifies: Contexts and Path Queries — getContextBean returns the exact
     * root object the context was created over.
     */
    @Test
    void contextBeanIsRootReference() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        assertEquals(true, ctx.getContextBean() == emp);
        assertEquals(true, ctx.getValue(".") == emp);
    }
}
