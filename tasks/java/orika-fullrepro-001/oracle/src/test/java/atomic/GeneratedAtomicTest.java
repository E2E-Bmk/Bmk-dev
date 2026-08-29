package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;

import ma.glasnost.orika.BoundMapperFacade;
import ma.glasnost.orika.CustomConverter;
import ma.glasnost.orika.MapperFacade;
import ma.glasnost.orika.MapperFactory;
import ma.glasnost.orika.MappingContext;
import ma.glasnost.orika.MappingException;
import ma.glasnost.orika.NullFilter;
import ma.glasnost.orika.converter.ConverterFactory;
import ma.glasnost.orika.impl.DefaultMapperFactory;
import ma.glasnost.orika.metadata.ClassMapBuilder;
import ma.glasnost.orika.metadata.Type;
import ma.glasnost.orika.metadata.TypeBuilder;
import ma.glasnost.orika.metadata.TypeFactory;

class GeneratedAtomicTest {

    static class Source {
        public String name;
        public String note;
        public Integer number;
        public Nested nested;
        public List<String> values;

        Source() { }

        Source(String name, String note, Integer number) {
            this.name = name;
            this.note = note;
            this.number = number;
        }
    }

    static class Target {
        public String name;
        public String label;
        public String note;
        public Integer number;
        public String nestedValue;
    }

    static class Nested {
        public String value;

        Nested() { }

        Nested(String value) { this.value = value; }
    }

    static class ValueBox {
        public String value;
    }

    private static MapperFactory factory() {
        return new DefaultMapperFactory.Builder().build();
    }

    /**
     * Verifies: ORK-FAC-001
     * Difficulty: medium
     */
    @Test
    void defaultFactoryMapsMatchingBean() {
        Source source = new Source("Ada", "ready", 7);
        Target target = factory().getMapperFacade().map(source, Target.class);
        assertEquals("Ada", target.name);
        assertEquals(Integer.valueOf(7), target.number);
    }

    /**
     * Verifies: ORK-FAC-002
     * Difficulty: basic
     */
    @Test
    void disabledAutoMappingRejectsUnregisteredPair() {
        MapperFactory mapperFactory = new DefaultMapperFactory.Builder().useAutoMapping(false).build();
        assertThrows(MappingException.class,
                () -> mapperFactory.getMapperFacade().map(new Source("x", null, 1), Target.class));
    }

    /**
     * Verifies: ORK-FAC-003
     * Difficulty: basic
     */
    @Test
    void classMapAcceptsClassTokens() {
        ClassMapBuilder<Source, Target> builder = factory().classMap(Source.class, Target.class);
        assertNotNull(builder);
    }

    /**
     * Verifies: ORK-FAC-004
     * Difficulty: basic
     */
    @Test
    void registeredRuleBecomesActive() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        Target target = mapperFactory.getMapperFacade().map(new Source("active", null, 2), Target.class);
        assertEquals("active", target.label);
    }

    /**
     * Verifies: ORK-FLD-001
     * Difficulty: basic
     */
    @Test
    void bidirectionalFieldWorksBothWays() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        MapperFacade mapper = mapperFactory.getMapperFacade();
        Target target = mapper.map(new Source("forward", null, null), Target.class);
        Source restored = mapper.map(target, Source.class);
        assertEquals("forward", target.label);
        assertEquals("forward", restored.name);
    }

    /**
     * Verifies: ORK-FLD-002
     * Difficulty: basic
     */
    @Test
    void forwardOnlyFieldDoesNotApplyInReverse() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).fieldAToB("name", "label").register();
        Target target = mapperFactory.getMapperFacade().map(new Source("one-way", null, null), Target.class);
        assertEquals("one-way", target.label);
        target.label = "reverse-value";
        Source restored = mapperFactory.getMapperFacade().map(target, Source.class);
        assertNull(restored.name);
    }

    /**
     * Verifies: ORK-FLD-002
     * Difficulty: basic
     */
    @Test
    void reverseOnlyFieldAppliesFromBToA() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).fieldBToA("label", "name").register();
        Target target = new Target();
        target.label = "back";
        Source restored = mapperFactory.getMapperFacade().map(target, Source.class);
        assertEquals("back", restored.name);
    }

    /**
     * Verifies: ORK-FLD-003
     * Difficulty: basic
     */
    @Test
    void excludedPropertyIsNotDefaultMapped() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).exclude("note").byDefault().register();
        Target target = mapperFactory.getMapperFacade().map(new Source("Ada", "secret", 4), Target.class);
        assertEquals("Ada", target.name);
        assertNull(target.note);
    }

    /**
     * Verifies: ORK-FLD-004
     * Difficulty: basic
     */
    @Test
    void byDefaultKeepsExplicitRename() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").byDefault().register();
        Target target = mapperFactory.getMapperFacade().map(new Source("explicit", "default", 8), Target.class);
        assertEquals("explicit", target.label);
        assertEquals("default", target.note);
    }

    /**
     * Verifies: ORK-FLD-005
     * Difficulty: basic
     */
    @Test
    void missingPropertyFailsDuringConfiguration() {
        MapperFactory mapperFactory = factory();
        assertThrows(MappingException.class,
                () -> mapperFactory.classMap(Source.class, Target.class).field("missing", "label"));
    }

    /**
     * Verifies: ORK-EXP-001
     * Difficulty: basic
     */
    @Test
    void nestedExpressionTraversesObject() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("nested.value", "nestedValue").register();
        Source source = new Source();
        source.nested = new Nested("inside");
        assertEquals("inside", mapperFactory.getMapperFacade().map(source, Target.class).nestedValue);
    }

    /**
     * Verifies: ORK-NUL-001
     * Difficulty: hard
     */
    @Test
    void nullOverwritesExistingValueByDefault() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).byDefault().register();
        Source source = new Source("name", null, 1);
        Target target = new Target();
        target.note = "old";
        mapperFactory.getMapperFacade().map(source, target);
        assertNull(target.note);
    }

    /**
     * Verifies: ORK-NUL-002
     * Difficulty: medium
     */
    @Test
    void classNullPolicyPreservesExistingValue() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).mapNulls(false).byDefault().register();
        Target target = new Target();
        target.note = "kept";
        mapperFactory.getMapperFacade().map(new Source("n", null, 1), target);
        assertEquals("kept", target.note);
    }

    /**
     * Verifies: ORK-NUL-002
     * Difficulty: medium
     */
    @Test
    void fieldNullPolicyOverridesClassPolicy() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class)
                .mapNulls(false).fieldMap("note", "note").mapNulls(true).add().byDefault().register();
        Target target = new Target();
        target.note = "old";
        mapperFactory.getMapperFacade().map(new Source("n", null, 1), target);
        assertNull(target.note);
    }

    /**
     * Verifies: ORK-MAP-001
     * Difficulty: hard
     */
    @Test
    void creationMapCopiesConfiguredProperties() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").byDefault().register();
        Target target = mapperFactory.getMapperFacade().map(new Source("created", "memo", 3), Target.class);
        assertEquals("created", target.label);
        assertEquals("memo", target.note);
    }

    /**
     * Verifies: ORK-MAP-002
     * Difficulty: medium
     */
    @Test
    void existingDestinationIsRetained() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).byDefault().register();
        Target supplied = new Target();
        mapperFactory.getMapperFacade().map(new Source("same", null, 9), supplied);
        assertEquals("same", supplied.name);
        assertEquals(Integer.valueOf(9), supplied.number);
    }

    /**
     * Verifies: ORK-MAP-003
     * Difficulty: medium
     */
    @Test
    void creationMapReturnsNullForNullSource() {
        assertNull(factory().getMapperFacade().map(null, Target.class));
    }

    /**
     * Verifies: ORK-BND-001
     * Difficulty: medium
     */
    @Test
    void boundFacadeUsesRegisteredPair() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        BoundMapperFacade<Source, Target> bound = mapperFactory.getMapperFacade(Source.class, Target.class);
        assertEquals("bound", bound.map(new Source("bound", null, null)).label);
    }

    /**
     * Verifies: ORK-BND-002
     * Difficulty: medium
     */
    @Test
    void boundFacadeMapsInReverse() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        Target target = new Target();
        target.label = "restored";
        assertEquals("restored", mapperFactory.getMapperFacade(Source.class, Target.class).mapReverse(target).name);
    }

    /**
     * Verifies: ORK-MUL-001
     * Difficulty: hard
     */
    @Test
    void listMappingMapsEveryElement() {
        List<Source> source = Arrays.asList(new Source("a", null, 1), new Source("b", null, 2));
        List<Target> targets = factory().getMapperFacade().mapAsList(source, Target.class);
        assertEquals(Arrays.asList("a", "b"), Arrays.asList(targets.get(0).name, targets.get(1).name));
    }

    /**
     * Verifies: ORK-MUL-002
     * Difficulty: medium
     */
    @Test
    void setMappingUsesSetSemantics() {
        Source repeated = new Source("same", null, 1);
        LinkedHashSet<Source> source = new LinkedHashSet<>(Arrays.asList(repeated, repeated));
        assertEquals(1, factory().getMapperFacade().mapAsSet(source, Target.class).size());
    }

    /**
     * Verifies: ORK-MUL-002
     * Difficulty: medium
     */
    @Test
    void arrayMappingPreservesOrder() {
        Source[] source = { new Source("first", null, 1), new Source("second", null, 2) };
        Target[] destination = factory().getMapperFacade().mapAsArray(new Target[source.length], source, Target.class);
        assertEquals("first", destination[0].name);
        assertEquals("second", destination[1].name);
    }

    /**
     * Verifies: ORK-MUL-002
     * Difficulty: medium
     */
    @Test
    void collectionMappingAddsToSuppliedCollection() {
        List<Target> destination = new ArrayList<>();
        factory().getMapperFacade().mapAsCollection(
                Arrays.asList(new Source("added", null, 1)), destination, Target.class);
        assertEquals(1, destination.size());
        assertEquals("added", destination.get(0).name);
    }

    /**
     * Verifies: ORK-CVT-001
     * Difficulty: hard
     */
    @Test
    void customConverterHandlesCompatiblePair() {
        MapperFactory mapperFactory = factory();
        mapperFactory.getConverterFactory().registerConverter(new CustomConverter<String, ValueBox>() {
            @Override
            public ValueBox convert(String source, Type<? extends ValueBox> destinationType,
                    MappingContext mappingContext) {
                ValueBox box = new ValueBox();
                box.value = source.toUpperCase();
                return box;
            }
        });
        ValueBox box = mapperFactory.getMapperFacade().map("signal", ValueBox.class);
        assertEquals("SIGNAL", box.value);
    }

    /**
     * Verifies: ORK-CVT-004
     * Difficulty: hard
     */
    @Test
    void identifiedConverterCanBeRetrieved() {
        MapperFactory mapperFactory = factory();
        CustomConverter<String, Integer> converter = new CustomConverter<String, Integer>() {
            @Override
            public Integer convert(String source, Type<? extends Integer> destinationType,
                    MappingContext mappingContext) {
                return Integer.valueOf(source) + 1;
            }
        };
        ConverterFactory registry = mapperFactory.getConverterFactory();
        registry.registerConverter("increment", converter);
        assertSame(converter, registry.getConverter("increment"));
        assertTrue(registry.hasConverter("increment"));
    }

}
