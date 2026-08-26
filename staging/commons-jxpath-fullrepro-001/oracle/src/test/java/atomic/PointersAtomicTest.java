package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.Pointer;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Pointers: canonical paths, live reads and writes, node access. */
class PointersAtomicTest {

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — bean
     * property, collection element, and map entry canonical forms.
     */
    @Test
    void canonicalFormsPerModel() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("/name", ctx.getPointer("name").asPath());
        assertEquals("/phones[2]", ctx.getPointer("phones[2]").asPath());
        assertEquals("/props[@name='grade']", ctx.getPointer("props/grade").asPath());
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — the context
     * root pointer renders as "/".
     */
    @Test
    void contextPointerIsRoot() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertEquals("/", ctx.getContextPointer().asPath());
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — a pointer
     * obtained through a filtering predicate canonicalizes to positional form.
     */
    @Test
    void predicateCanonicalizesToPosition() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        assertEquals("/employees[2]", ctx.getPointer("employees[name = 'Bob']").asPath());
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — getValue
     * returns the value at the pointer's location.
     */
    @Test
    void pointerReadsLocationValue() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        emp.setName("Grace");
        Pointer p = ctx.getPointer("name");
        assertEquals("Grace", p.getValue());
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — pointer
     * setValue writes through to the underlying object.
     */
    @Test
    void pointerWritesThrough() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.getPointer("phones[2]").setValue("999");
        assertEquals(List.of("111", "999", "333"), emp.getPhones());
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — getRootNode
     * returns the root object of the pointer's graph.
     */
    @Test
    void rootNodeIsGraphRoot() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        assertEquals(true, ctx.getPointer("phones[2]").getRootNode() == emp);
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — every
     * canonical path round-trips to the same value on the originating context.
     */
    @Test
    void canonicalPathRoundTrips() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        Pointer p = ctx.getPointer("employees[2]/name");
        assertEquals("/employees[2]/name", p.asPath());
        assertEquals("Bob", ctx.getValue(p.asPath()));
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — a relative
     * context evaluates paths from the pointer's location and walks outward
     * with the parent axis.
     */
    @Test
    void relativeContextEvaluatesFromPointer() {
        Graphs.Employee emp = Graphs.employee();
        emp.setAddress(new Graphs.Address("Oslo", "0150"));
        JXPathContext ctx = JXPathContext.newContext(emp);
        JXPathContext rel = ctx.getRelativeContext(ctx.getPointer("address"));
        assertEquals("Oslo", rel.getValue("city"));
        assertEquals("Ada", rel.getValue("../name"));
    }

    /**
     * Verifies: Pointers, Canonical Paths, and Relative Contexts — pointers
     * from a relative context report root-anchored canonical paths.
     */
    @Test
    void relativePointersAreRootAnchored() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.company());
        JXPathContext rel = ctx.getRelativeContext(ctx.getPointer("employees[2]"));
        assertEquals("/employees[2]/age", rel.getPointer("age").asPath());
    }
}
