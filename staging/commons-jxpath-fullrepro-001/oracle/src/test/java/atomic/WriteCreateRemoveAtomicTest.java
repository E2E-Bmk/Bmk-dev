package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;
import org.apache.commons.jxpath.AbstractFactory;
import org.apache.commons.jxpath.JXPathAbstractFactoryException;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathException;
import org.apache.commons.jxpath.Pointer;
import org.junit.jupiter.api.Test;
import support.Graphs;

/** Writing, creating with factories, and removing graph structure. */
class WriteCreateRemoveAtomicTest {

    /** Factory that can attach the address bean and initialize its city. */
    static class AddressFactory extends AbstractFactory {
        @Override
        public boolean createObject(JXPathContext context, Pointer pointer, Object parent,
                String name, int index) {
            if (parent instanceof Graphs.Employee && name.equals("address")) {
                ((Graphs.Employee) parent).setAddress(new Graphs.Address());
                return true;
            }
            if (parent instanceof Graphs.Address && name.equals("city")) {
                ((Graphs.Address) parent).setCity("");
                return true;
            }
            return false;
        }
    }

    /** Factory that only knows the intermediate address step. */
    static class IntermediateOnlyFactory extends AbstractFactory {
        @Override
        public boolean createObject(JXPathContext context, Pointer pointer, Object parent,
                String name, int index) {
            if (parent instanceof Graphs.Employee && name.equals("address")) {
                ((Graphs.Employee) parent).setAddress(new Graphs.Address());
                return true;
            }
            return false;
        }
    }

    /**
     * Verifies: Writing, Creating, and Removing — setValue converts a string
     * to the int property type.
     */
    @Test
    void setValueConvertsToPropertyType() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setValue("age", "41");
        assertEquals(41, emp.getAge());
    }

    /**
     * Verifies: Writing, Creating, and Removing — setValue on a map key
     * inserts or overwrites the entry.
     */
    @Test
    void setValueOverwritesMapEntry() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setValue("props/grade", "principal");
        assertEquals("principal", emp.getProps().get("grade"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — setValue never builds
     * missing structure; a no-match write raises JXPathException in strict and
     * lenient contexts alike.
     */
    @Test
    void setValueOnMissingPathRaisesInBothModes() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathException.class, () -> ctx.setValue("nosuch", 1));
        ctx.setLenient(true);
        assertThrows(JXPathException.class, () -> ctx.setValue("nosuch", 1));
    }

    /**
     * Verifies: Writing, Creating, and Removing — a value that cannot convert
     * to the target property type raises JXPathException.
     */
    @Test
    void setValueBadConversionRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathException.class, () -> ctx.setValue("age", "notanumber"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — createPath consults the
     * factory for each missing step, including a null leaf property, and
     * returns the pointer of the created location.
     */
    @Test
    void createPathBuildsThroughFactory() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setFactory(new AddressFactory());
        Pointer created = ctx.createPath("address/city");
        assertEquals("/address/city", created.asPath());
        assertEquals("", emp.getAddress().getCity());
    }

    /**
     * Verifies: Writing, Creating, and Removing — createPath with no factory
     * installed raises JXPathException when creation is needed.
     */
    @Test
    void createPathWithoutFactoryRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathException.class, () -> ctx.createPath("address/city"));
    }

    /**
     * Verifies: Error Semantics — a factory that declines a step produces a
     * JXPathException whose cause is JXPathAbstractFactoryException.
     */
    @Test
    void decliningFactoryReportsCause() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        ctx.setFactory(new AbstractFactory() { });
        JXPathException raised =
                assertThrows(JXPathException.class, () -> ctx.createPath("address/city"));
        assertTrue(raised.getCause() instanceof JXPathAbstractFactoryException);
    }

    /**
     * Verifies: Writing, Creating, and Removing — createPathAndSetValue needs
     * factory handling only for intermediate structure, not the leaf.
     */
    @Test
    void createPathAndSetValueNeedsIntermediatesOnly() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.setFactory(new IntermediateOnlyFactory());
        ctx.createPathAndSetValue("address/city", "Tromso");
        assertEquals("Tromso", emp.getAddress().getCity());
    }

    /**
     * Verifies: Writing, Creating, and Removing — createPathAndSetValue on a
     * map key succeeds without any factory.
     */
    @Test
    void createPathAndSetValueOnMapNeedsNoFactory() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.createPathAndSetValue("props/team", "core");
        assertEquals("core", emp.getProps().get("team"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — removePath deletes a map
     * entry.
     */
    @Test
    void removePathDeletesMapEntry() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.removePath("props/grade");
        assertEquals(Map.of(), emp.getProps());
    }

    /**
     * Verifies: Writing, Creating, and Removing — removePath removes a list
     * element and the list shrinks.
     */
    @Test
    void removePathShrinksList() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.removePath("phones[2]");
        assertEquals(List.of("111", "333"), emp.getPhones());
    }

    /**
     * Verifies: Error Semantics — removePath on a path matching nothing raises
     * JXPathException.
     */
    @Test
    void removePathMissingRaises() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertThrows(JXPathException.class, () -> ctx.removePath("nosuch"));
    }

    /**
     * Verifies: Writing, Creating, and Removing — removeAll removes every
     * match and tolerates an empty match set.
     */
    @Test
    void removeAllRemovesEveryMatch() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.removeAll("phones[position() > 1]");
        assertEquals(List.of("111"), emp.getPhones());
        ctx.removeAll("phones");
        assertEquals(List.of(), emp.getPhones());
        ctx.removeAll("nosuch");
    }

    /**
     * Verifies: Writing, Creating, and Removing — removeAll with a wildcard
     * clears a map.
     */
    @Test
    void removeAllWildcardClearsMap() {
        Graphs.Employee emp = Graphs.employee();
        JXPathContext ctx = JXPathContext.newContext(emp);
        ctx.removeAll("props/*");
        assertEquals(Map.of(), emp.getProps());
    }

    /**
     * Verifies: Writing, Creating, and Removing — getFactory returns the
     * installed factory.
     */
    @Test
    void factoryAccessorReturnsInstalled() {
        JXPathContext ctx = JXPathContext.newContext(Graphs.employee());
        assertNull(ctx.getFactory());
        AddressFactory factory = new AddressFactory();
        ctx.setFactory(factory);
        assertEquals(true, ctx.getFactory() == factory);
    }
}
