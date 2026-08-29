package atomic;

import ma.glasnost.orika.BoundMapperFacade;
import ma.glasnost.orika.MapperFacade;
import ma.glasnost.orika.MapperFactory;
import ma.glasnost.orika.impl.DefaultMapperFactory;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class UpstreamRewrittenAtomicTest {
    private static MapperFactory factory() {
        return new DefaultMapperFactory.Builder().build();
    }

    /** Verifies: ORK-EXP-001, ORK-FLD-001. */
    @Test void nestedElements() {
        MapperFactory f = factory();
        f.classMap(Person.class, PersonView.class).field("address.city", "city").byDefault().register();
        Person source = new Person("Ada", new Address("Paris"));
        PersonView view = f.getMapperFacade().map(source, PersonView.class);
        assertAll(() -> assertEquals("Ada", view.name), () -> assertEquals("Paris", view.city));
    }

    /** Verifies: ORK-FLD-001, ORK-FAC-004. */
    @Test void map() {
        MapperFactory f = factory();
        f.classMap(Person.class, RenamedPerson.class).field("name", "displayName").register();
        RenamedPerson result = f.getMapperFacade().map(new Person("Lin", null), RenamedPerson.class);
        assertEquals("Lin", result.displayName);
    }

    /** Verifies: ORK-TYP-003, ORK-MAP-001. */
    @Test void testSimplePrimitiveArray() {
        BytesDto result = factory().getMapperFacade().map(new Bytes(new byte[]{1, 2, 3}), BytesDto.class);
        assertArrayEquals(new byte[]{1, 2, 3}, result.buffer);
    }

    /** Verifies: ORK-TYP-003, ORK-MAP-001. */
    @Test void testSimplePrimitiveToWrapperArray() {
        BoxedBytes result = factory().getMapperFacade().map(new Bytes(new byte[]{4, 5}), BoxedBytes.class);
        assertArrayEquals(new Byte[]{4, 5}, result.buffer);
    }

    /** Verifies: ORK-TYP-003, ORK-MAP-001. */
    @Test void testArrayToList() {
        TagList result = factory().getMapperFacade().map(new Tags(new String[]{"a", "b"}), TagList.class);
        assertEquals(List.of("a", "b"), result.tags);
    }

    /** Verifies: ORK-TYP-003, ORK-MAP-001. */
    @Test void testWrapperArrayToList() {
        NumberList result = factory().getMapperFacade().map(new Numbers(new Integer[]{2, 7}), NumberList.class);
        assertEquals(List.of(2, 7), result.values);
    }

    /** Verifies: ORK-TYP-003, ORK-MAP-001. */
    @Test void testListToArray() {
        Tags result = factory().getMapperFacade().map(new TagList(Arrays.asList("x", "y")), Tags.class);
        assertArrayEquals(new String[]{"x", "y"}, result.tags);
    }

    /** Verifies: ORK-TYP-003, ORK-MAP-001. */
    @Test void testMappingArrayOfString() {
        Tags result = factory().getMapperFacade().map(new Tags(new String[]{"music", "sport"}), Tags.class);
        assertArrayEquals(new String[]{"music", "sport"}, result.tags);
    }

    /** Verifies: ORK-BND-001, ORK-BND-002. */
    @Test void testBidirectionalMapping() {
        MapperFactory f = factory();
        f.classMap(Person.class, PersonView.class).field("address.city", "city").byDefault().register();
        BoundMapperFacade<Person, PersonView> bound = f.getMapperFacade(Person.class, PersonView.class);
        PersonView view = bound.map(new Person("Sam", new Address("Rome")));
        Person reverse = bound.mapReverse(view);
        assertAll(() -> assertEquals("Sam", view.name), () -> assertEquals("Rome", reverse.address.city));
    }

    public static class Address { public String city; public Address() {} Address(String city) { this.city = city; } }
    public static class Person { public String name; public Address address; public Person() {} Person(String name, Address address) { this.name = name; this.address = address; } }
    public static class PersonView { public String name; public String city; }
    public static class RenamedPerson { public String displayName; }
    public static class Bytes { public byte[] buffer; public Bytes() {} Bytes(byte[] buffer) { this.buffer = buffer; } }
    public static class BytesDto { public byte[] buffer; }
    public static class BoxedBytes { public Byte[] buffer; }
    public static class Tags { public String[] tags; public Tags() {} public Tags(String[] tags) { this.tags = tags; } }
    public static class TagList { public List<String> tags; public TagList() {} public TagList(List<String> tags) { this.tags = tags; } }
    public static class Numbers { public Integer[] values; public Numbers() {} public Numbers(Integer[] values) { this.values = values; } }
    public static class NumberList { public List<Integer> values; }
}
