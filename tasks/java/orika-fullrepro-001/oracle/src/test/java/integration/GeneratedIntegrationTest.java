package integration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.junit.jupiter.api.Test;

import ma.glasnost.orika.BoundMapperFacade;
import ma.glasnost.orika.CustomConverter;
import ma.glasnost.orika.CustomFilter;
import ma.glasnost.orika.CustomMapper;
import ma.glasnost.orika.MapperFacade;
import ma.glasnost.orika.MapperFactory;
import ma.glasnost.orika.MappingContext;
import ma.glasnost.orika.MappingException;
import ma.glasnost.orika.ObjectFactory;
import ma.glasnost.orika.converter.BidirectionalConverter;
import ma.glasnost.orika.impl.ConfigurableMapper;
import ma.glasnost.orika.impl.DefaultMapperFactory;
import ma.glasnost.orika.metadata.Type;
import ma.glasnost.orika.metadata.TypeBuilder;
import ma.glasnost.orika.metadata.TypeFactory;

class GeneratedIntegrationTest {

    static class Source {
        public String name;
        public String note;
        public Integer number;
        public Nested nested;
        public List<String> values;
        public Map<String, String> attributes;
        public List<Item> items;

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
        public String firstValue;
        public String city;
        public List<String> names;
        public String origin;
    }

    public static class Nested {
        public String value;

        public Nested() { }

        public Nested(String value) { this.value = value; }
    }

    static class StringMapHolder {
        public Map<String, String> values;
    }

    static class IntegerMapHolder {
        public Map<Integer, Integer> values;
    }

    static class Item {
        public String name;

        Item() { }

        Item(String name) { this.name = name; }
    }

    static class TextRecord {
        public String amount;
        public String untouched;
    }

    static class NumberRecord {
        public Integer amount;
        public String untouched;
    }

    static class ParentSource {
        public String id;
    }

    static class ChildSource extends ParentSource {
        public String detail;
    }

    static class ParentTarget {
        public String key;
    }

    static class ChildTarget extends ParentTarget {
        public String detail;
    }

    static class ImmutableTarget {
        private final String name;

        ImmutableTarget(String name) { this.name = name; }

        public String getName() { return name; }
    }

    interface NamedView {
        String getName();
        void setName(String name);
    }

    static class NamedViewImpl implements NamedView {
        private String name;

        @Override
        public String getName() { return name; }

        @Override
        public void setName(String name) { this.name = name; }
    }

    interface Unconstructable {
        String getName();
    }

    enum Status { NEW, DONE }

    static class StatusText { public String status; }
    static class StatusValue { public Status status; }

    private static MapperFactory factory() {
        return new DefaultMapperFactory.Builder().build();
    }

    private static Source source(String name) {
        return new Source(name, "note-" + name, name.length());
    }

    private static BidirectionalConverter<String, Integer> stringNumberConverter() {
        return new BidirectionalConverter<String, Integer>() {
            @Override
            public Integer convertTo(String source, Type<Integer> destinationType, MappingContext mappingContext) {
                return Integer.valueOf(source) + 10;
            }

            @Override
            public String convertFrom(Integer source, Type<String> destinationType, MappingContext mappingContext) {
                return String.valueOf(source - 10);
            }
        };
    }

    private static MapperFactory converterFactory() {
        MapperFactory mapperFactory = factory();
        mapperFactory.getConverterFactory().registerConverter("shift", stringNumberConverter());
        mapperFactory.classMap(TextRecord.class, NumberRecord.class)
                .fieldMap("amount", "amount").converter("shift").add()
                .byDefault().register();
        return mapperFactory;
    }

    private static CustomFilter<String, String> rejectingBlockedValues() {
        return new CustomFilter<String, String>() {
            @Override
            public <S extends String, D extends String> boolean shouldMap(Type<S> sourceType, String sourceName, S source,
                    Type<D> destinationType, String destinationName, D destination,
                    MappingContext mappingContext) {
                return !"blocked".equals(source);
            }

            @Override
            public boolean filtersSource() {
                return false;
            }

            @Override
            public boolean filtersDestination() {
                return false;
            }

            @Override
            public <S extends String> S filterSource(S source, Type<S> sourceType, String sourceName,
                    Type<?> destinationType, String destinationName, MappingContext mappingContext) {
                return source;
            }

            @Override
            public <D extends String> D filterDestination(D destination, Type<?> sourceType, String sourceName,
                    Type<D> destinationType, String destinationName, MappingContext mappingContext) {
                return destination;
            }
        };
    }

    /**
     * Verifies: ORK-CVI-001, ORK-FAC-004, ORK-BND-001
     * Depends-On: registeredRuleBecomesActive, boundFacadeUsesRegisteredPair
     */
    @Test
    void registeredRuleGovernsUnboundAndBoundFacades() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        Source source = source("shared");
        assertEquals("shared", mapperFactory.getMapperFacade().map(source, Target.class).label);
        assertEquals("shared", mapperFactory.getMapperFacade(Source.class, Target.class).map(source).label);
    }

    /**
     * Verifies: ORK-CVI-001, ORK-FAC-003
     * Depends-On: classMapAcceptsClassTokens, registeredRuleBecomesActive
     */
    @Test
    void laterBoundFacadeObservesCommittedRules() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").byDefault().register();
        MapperFacade unbound = mapperFactory.getMapperFacade();
        assertEquals("first", unbound.map(source("first"), Target.class).label);
        BoundMapperFacade<Source, Target> later = mapperFactory.getMapperFacade(Source.class, Target.class);
        assertEquals("later", later.map(source("later")).label);
    }

    /**
     * Verifies: ORK-CVI-002, ORK-FLD-001, ORK-BND-002
     * Depends-On: bidirectionalFieldWorksBothWays, boundFacadeMapsInReverse
     */
    @Test
    void bidirectionalRuleRoundTripsAcrossBoundFacade() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        BoundMapperFacade<Source, Target> bound = mapperFactory.getMapperFacade(Source.class, Target.class);
        Target projected = bound.map(source("cycle"));
        assertEquals("cycle", projected.label);
        assertEquals("cycle", bound.mapReverse(projected).name);
    }

    /**
     * Verifies: ORK-CVI-002, ORK-FLD-002
     * Depends-On: forwardOnlyFieldDoesNotApplyInReverse, reverseOnlyFieldAppliesFromBToA
     */
    @Test
    void directionalRulesRemainDirectionalAcrossViews() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class)
                .fieldAToB("name", "label").fieldBToA("name", "note").register();
        Target forward = mapperFactory.getMapperFacade().map(source("east"), Target.class);
        assertEquals("east", forward.label);
        Target reverseInput = new Target();
        reverseInput.name = "west";
        Source reverse = mapperFactory.getMapperFacade(Source.class, Target.class).mapReverse(reverseInput);
        assertEquals("west", reverse.note);
        assertNull(reverse.name);
    }

    /**
     * Verifies: ORK-CVI-003, ORK-MAP-001, ORK-MAP-002, ORK-NUL-002
     * Depends-On: creationMapCopiesConfiguredProperties, existingDestinationIsRetained
     */
    @Test
    void creationAndExistingMappingShareFieldsAndNullPolicy() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).mapNulls(false).field("name", "label").byDefault().register();
        Source input = new Source("consistent", null, 6);
        Target created = mapperFactory.getMapperFacade().map(input, Target.class);
        Target existing = new Target();
        existing.note = "preserved";
        mapperFactory.getMapperFacade().map(input, existing);
        assertEquals(created.label, existing.label);
        assertEquals("preserved", existing.note);
    }

    /**
     * Verifies: ORK-CVI-003, ORK-EXT-002
     * Depends-On: existingDestinationIsRetained, byDefaultKeepsExplicitRename
     */
    @Test
    void customMapperRunsForCreationAndExistingDestination() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).byDefault()
                .customize(new CustomMapper<Source, Target>() {
                    @Override
                    public void mapAtoB(Source a, Target b, MappingContext context) {
                        b.label = "custom-" + a.name;
                    }
                }).register();
        Source input = source("hook");
        Target created = mapperFactory.getMapperFacade().map(input, Target.class);
        Target existing = new Target();
        mapperFactory.getMapperFacade().map(input, existing);
        assertEquals("custom-hook", created.label);
        assertEquals(created.label, existing.label);
    }

    /**
     * Verifies: ORK-CVI-004, ORK-MUL-001
     * Depends-On: creationMapCopiesConfiguredProperties, listMappingMapsEveryElement
     */
    @Test
    void directAndListElementMappingAreEquivalent() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").byDefault().register();
        Source input = source("element");
        Target direct = mapperFactory.getMapperFacade().map(input, Target.class);
        Target listed = mapperFactory.getMapperFacade().mapAsList(Arrays.asList(input), Target.class).get(0);
        assertEquals(direct.label, listed.label);
        assertEquals(direct.note, listed.note);
    }

    /**
     * Verifies: ORK-CVI-004, ORK-MUL-001, ORK-MUL-002
     * Depends-On: setMappingUsesSetSemantics, arrayMappingPreservesOrder
     */
    @Test
    void setArrayAndSuppliedCollectionUseSameElementRule() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        Source input = source("many");
        MapperFacade mapper = mapperFactory.getMapperFacade();
        Target direct = mapper.map(input, Target.class);
        Target fromSet = mapper.mapAsSet(new LinkedHashSet<>(Arrays.asList(input)), Target.class).iterator().next();
        Target fromArray = mapper.mapAsArray(new Target[1], new Source[] { input }, Target.class)[0];
        List<Target> supplied = new ArrayList<>();
        mapper.mapAsCollection(Arrays.asList(input), supplied, Target.class);
        assertEquals(direct.label, fromSet.label);
        assertEquals(direct.label, fromArray.label);
        assertEquals(direct.label, supplied.get(0).label);
    }

    /**
     * Verifies: ORK-CVI-005, ORK-TYP-001, ORK-FAC-003
     * Depends-On: boundFacadeUsesRegisteredPair, classMapAcceptsClassTokens
     */
    @Test
    void equivalentTypeTokensSelectRegisteredClassMap() {
        MapperFactory mapperFactory = factory();
        Type<Source> builtSource = new TypeBuilder<Source>() { }.build();
        Type<Target> builtTarget = new TypeBuilder<Target>() { }.build();
        mapperFactory.classMap(builtSource, builtTarget).field("name", "label").register();
        Type<Source> factorySource = TypeFactory.valueOf(Source.class);
        Type<Target> factoryTarget = TypeFactory.valueOf(Target.class);
        Target target = mapperFactory.getMapperFacade().map(source("typed"), factorySource, factoryTarget);
        assertEquals("typed", target.label);
    }

    /**
     * Verifies: ORK-CVI-005, ORK-TYP-001, ORK-CVT-001
     * Depends-On: identifiedConverterCanBeRetrieved, customConverterHandlesCompatiblePair
     */
    @Test
    void equivalentTypeTokensSelectSameConverter() {
        MapperFactory mapperFactory = factory();
        mapperFactory.getConverterFactory().registerConverter(new CustomConverter<String, Target>() {
            @Override
            public Target convert(String source, Type<? extends Target> destinationType, MappingContext context) {
                Target target = new Target();
                target.label = source.toUpperCase();
                return target;
            }
        });
        Type<String> built = new TypeBuilder<String>() { }.build();
        Target target = mapperFactory.getMapperFacade().map("token", built, TypeFactory.valueOf(Target.class));
        assertEquals("TOKEN", target.label);
    }

    /**
     * Verifies: ORK-CVI-006, ORK-CVT-004, ORK-EXT-001
     * Depends-On: identifiedConverterCanBeRetrieved, boundFacadeMapsInReverse
     */
    @Test
    void identifiedConverterWorksForSingleBoundAndReverseViews() {
        MapperFactory mapperFactory = converterFactory();
        TextRecord text = new TextRecord();
        text.amount = "7";
        text.untouched = "plain";
        NumberRecord unbound = mapperFactory.getMapperFacade().map(text, NumberRecord.class);
        BoundMapperFacade<TextRecord, NumberRecord> bound = mapperFactory.getMapperFacade(TextRecord.class, NumberRecord.class);
        NumberRecord bounded = bound.map(text);
        assertEquals(Integer.valueOf(17), unbound.amount);
        assertEquals(unbound.amount, bounded.amount);
        assertEquals("7", bound.mapReverse(bounded).amount);
    }

    /**
     * Verifies: ORK-CVI-006, ORK-MUL-001, ORK-CVT-004
     * Depends-On: identifiedConverterCanBeRetrieved, listMappingMapsEveryElement
     */
    @Test
    void identifiedConverterWorksForMultipleElementsWithoutTouchingOtherFields() {
        MapperFactory mapperFactory = converterFactory();
        TextRecord first = new TextRecord();
        first.amount = "1";
        first.untouched = "alpha";
        TextRecord second = new TextRecord();
        second.amount = "2";
        second.untouched = "beta";
        List<NumberRecord> mapped = mapperFactory.getMapperFacade().mapAsList(Arrays.asList(first, second), NumberRecord.class);
        assertEquals(Arrays.asList(11, 12), Arrays.asList(mapped.get(0).amount, mapped.get(1).amount));
        assertEquals(Arrays.asList("alpha", "beta"), Arrays.asList(mapped.get(0).untouched, mapped.get(1).untouched));
    }

    /**
     * Verifies: ORK-CVI-007, ORK-OBJ-001
     * Depends-On: creationMapCopiesConfiguredProperties, boundFacadeUsesRegisteredPair
     */
    @Test
    void objectFactoryControlsUnboundAndBoundConstruction() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerObjectFactory(new ObjectFactory<Target>() {
            @Override
            public Target create(Object source, MappingContext mappingContext) {
                Target target = new Target();
                target.origin = "factory";
                return target;
            }
        }, Target.class);
        Target unbound = mapperFactory.getMapperFacade().map(source("one"), Target.class);
        Target bound = mapperFactory.getMapperFacade(Source.class, Target.class).map(source("two"));
        assertEquals("factory", unbound.origin);
        assertEquals("factory", bound.origin);
        assertEquals("two", bound.name);
    }

    /**
     * Verifies: ORK-CVI-007, ORK-OBJ-001, ORK-MUL-001
     * Depends-On: collectionMappingAddsToSuppliedCollection, creationMapCopiesConfiguredProperties
     */
    @Test
    void objectFactoryControlsMultiOccurrenceConstruction() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerObjectFactory((source, context) -> {
            Target target = new Target();
            target.origin = "batch";
            return target;
        }, Target.class);
        List<Target> targets = mapperFactory.getMapperFacade().mapAsList(
                Arrays.asList(source("a"), source("b")), Target.class);
        assertEquals(Arrays.asList("batch", "batch"), Arrays.asList(targets.get(0).origin, targets.get(1).origin));
        assertEquals(Arrays.asList("a", "b"), Arrays.asList(targets.get(0).name, targets.get(1).name));
    }

    /**
     * Verifies: ORK-CVI-008, ORK-FLT-001, ORK-FLT-002, ORK-FLT-005, ORK-FLT-006, ORK-FLT-007
     * Depends-On: classNullPolicyPreservesExistingValue, existingDestinationIsRetained
     */
    @Test
    void filterDecisionMatchesCreationAndExistingMapping() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerFilter(rejectingBlockedValues());
        mapperFactory.classMap(Source.class, Target.class).byDefault().register();
        Source blocked = new Source("blocked", "allowed", 2);
        Target created = mapperFactory.getMapperFacade().map(blocked, Target.class);
        Target existing = new Target();
        existing.name = "keep";
        mapperFactory.getMapperFacade().map(blocked, existing);
        assertNull(created.name);
        assertEquals("keep", existing.name);
        assertEquals("allowed", created.note);
        assertEquals("allowed", existing.note);
    }

    /**
     * Verifies: ORK-CVI-008, ORK-FLT-001, ORK-FLT-002, ORK-FLT-005, ORK-FLT-006, ORK-FLT-007
     * Depends-On: fieldNullPolicyOverridesClassPolicy, creationMapCopiesConfiguredProperties
     */
    @Test
    void filterLeavesNonApplicablePropertyTypesUnchanged() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerFilter(rejectingBlockedValues());
        Source input = new Source("blocked", "open", 41);
        Target target = mapperFactory.getMapperFacade().map(input, Target.class);
        assertNull(target.name);
        assertEquals("open", target.note);
        assertEquals(Integer.valueOf(41), target.number);
    }

    /**
     * Verifies: ORK-EXP-002, ORK-MAP-001
     * Depends-On: nestedExpressionTraversesObject, creationMapCopiesConfiguredProperties
     */
    @Test
    void listIndexExpressionMapsSelectedValue() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("values[1]", "firstValue").register();
        Source input = new Source();
        input.values = Arrays.asList("zero", "one");
        assertEquals("one", mapperFactory.getMapperFacade().map(input, Target.class).firstValue);
    }

    /**
     * Verifies: ORK-EXP-002, ORK-MAP-001
     * Depends-On: nestedExpressionTraversesObject, registeredRuleBecomesActive
     */
    @Test
    void quotedMapKeyExpressionMapsSelectedValue() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("attributes['city']", "city").register();
        Source input = new Source();
        input.attributes = new LinkedHashMap<>();
        input.attributes.put("city", "Paris");
        assertEquals("Paris", mapperFactory.getMapperFacade().map(input, Target.class).city);
    }

    /**
     * Verifies: ORK-EXP-003, ORK-MUL-001
     * Depends-On: listMappingMapsEveryElement, nestedExpressionTraversesObject
     */
    @Test
    void braceExpressionProjectsElementProperties() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("items{name}", "names{}").register();
        Source input = new Source();
        input.items = Arrays.asList(new Item("red"), new Item("blue"));
        assertEquals(Arrays.asList("red", "blue"), mapperFactory.getMapperFacade().map(input, Target.class).names);
    }

    /**
     * Verifies: ORK-EXP-003, ORK-TYP-003
     * Depends-On: classMapAcceptsClassTokens, listMappingMapsEveryElement
     */
    @Test
    void braceExpressionProjectsMapKeys() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("attributes{key}", "names{}").register();
        Source input = new Source();
        input.attributes = new LinkedHashMap<>();
        input.attributes.put("first", "1");
        input.attributes.put("second", "2");
        assertEquals(Arrays.asList("first", "second"), mapperFactory.getMapperFacade().map(input, Target.class).names);
    }

    /**
     * Verifies: ORK-EXP-001, ORK-FLD-001, ORK-BND-002
     * Depends-On: nestedExpressionTraversesObject, bidirectionalFieldWorksBothWays
     */
    @Test
    void nestedBidirectionalWorkflowRoundTrips() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerObjectFactory((source, context) -> new Nested(), Nested.class);
        mapperFactory.classMap(Source.class, Target.class).field("nested.value", "nestedValue").register();
        Source input = new Source();
        input.nested = new Nested("deep");
        Target target = mapperFactory.getMapperFacade().map(input, Target.class);
        Source restored = mapperFactory.getMapperFacade().map(target, Source.class);
        assertEquals("deep", target.nestedValue);
        assertNotNull(restored.nested);
        assertEquals("deep", restored.nested.value);
    }

    /**
     * Verifies: ORK-FLD-003, ORK-FLD-004, ORK-MAP-001
     * Depends-On: excludedPropertyIsNotDefaultMapped, byDefaultKeepsExplicitRename
     */
    @Test
    void defaultAndExcludeWorkflowCombinesSelectionRules() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").exclude("note").byDefault().register();
        Target target = mapperFactory.getMapperFacade().map(source("rules"), Target.class);
        assertEquals("rules", target.label);
        assertEquals(Integer.valueOf(5), target.number);
        assertNull(target.note);
    }

    /**
     * Verifies: ORK-NUL-002, ORK-FAC-001
     * Depends-On: classNullPolicyPreservesExistingValue, defaultFactoryMapsMatchingBean
     */
    @Test
    void classNullPolicyOverridesFactoryNullPolicy() {
        MapperFactory mapperFactory = new DefaultMapperFactory.Builder().mapNulls(true).build();
        mapperFactory.classMap(Source.class, Target.class).mapNulls(false).byDefault().register();
        Target target = new Target();
        target.note = "class-wins";
        mapperFactory.getMapperFacade().map(new Source("x", null, 1), target);
        assertEquals("class-wins", target.note);
    }

    /**
     * Verifies: ORK-NUL-002, ORK-BND-002
     * Depends-On: fieldNullPolicyOverridesClassPolicy, boundFacadeMapsInReverse
     */
    @Test
    void reverseFieldNullPolicyPreservesDestination() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class)
                .fieldMap("name", "label").mapNullsInReverse(false).add().register();
        Target input = new Target();
        input.label = null;
        Source existing = source("keep");
        Source alias = existing;
        mapperFactory.getMapperFacade(Source.class, Target.class).mapReverse(input, existing);
        assertSame(alias, existing);
        assertEquals("keep", existing.name);
    }

    /**
     * Verifies: ORK-CON-001, ORK-MAP-001
     * Depends-On: registeredRuleBecomesActive, creationMapCopiesConfiguredProperties
     */
    @Test
    void selectedDestinationConstructorReceivesMappedProperty() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, ImmutableTarget.class)
                .field("name", "name").constructorB("name").register();
        ImmutableTarget target = mapperFactory.getMapperFacade().map(source("ctor"), ImmutableTarget.class);
        assertEquals("ctor", target.getName());
    }

    /**
     * Verifies: ORK-INH-001, ORK-FLD-004
     * Depends-On: registeredRuleBecomesActive, byDefaultKeepsExplicitRename
     */
    @Test
    void childMapReusesRegisteredParentRules() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(ParentSource.class, ParentTarget.class).field("id", "key").register();
        mapperFactory.classMap(ChildSource.class, ChildTarget.class)
                .use(ParentSource.class, ParentTarget.class).byDefault().register();
        ChildSource input = new ChildSource();
        input.id = "parent";
        input.detail = "child";
        ChildTarget target = mapperFactory.getMapperFacade().map(input, ChildTarget.class);
        assertEquals("parent", target.key);
        assertEquals("child", target.detail);
    }

    /**
     * Verifies: ORK-CVT-003, ORK-CVT-001
     * Depends-On: customConverterHandlesCompatiblePair, identifiedConverterCanBeRetrieved
     */
    @Test
    void specificAnonymousConverterWinsOverBroaderConverter() {
        MapperFactory mapperFactory = factory();
        mapperFactory.getConverterFactory().registerConverter(new CustomConverter<Object, Target>() {
            @Override
            public Target convert(Object source, Type<? extends Target> destinationType, MappingContext context) {
                Target target = new Target();
                target.label = "broad";
                return target;
            }
        });
        mapperFactory.getConverterFactory().registerConverter(new CustomConverter<String, Target>() {
            @Override
            public Target convert(String source, Type<? extends Target> destinationType, MappingContext context) {
                Target target = new Target();
                target.label = "specific-" + source;
                return target;
            }
        });
        assertEquals("specific-choice", mapperFactory.getMapperFacade().map("choice", Target.class).label);
    }

    /**
     * Verifies: ORK-EXT-001, ORK-CVT-001
     * Depends-On: customConverterHandlesCompatiblePair, identifiedConverterCanBeRetrieved
     */
    @Test
    void bidirectionalConverterDispatchesBothDirections() {
        MapperFactory mapperFactory = converterFactory();
        TextRecord text = new TextRecord();
        text.amount = "5";
        BoundMapperFacade<TextRecord, NumberRecord> bound = mapperFactory.getMapperFacade(TextRecord.class, NumberRecord.class);
        NumberRecord number = bound.map(text);
        TextRecord restored = bound.mapReverse(number);
        assertEquals(Integer.valueOf(15), number.amount);
        assertEquals("5", restored.amount);
    }

    /**
     * Verifies: ORK-EXT-002, ORK-BND-002
     * Depends-On: boundFacadeMapsInReverse, byDefaultKeepsExplicitRename
     */
    @Test
    void customMapperRunsAfterOrdinaryFieldsInBothDirections() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).byDefault()
                .customize(new CustomMapper<Source, Target>() {
                    @Override
                    public void mapAtoB(Source a, Target b, MappingContext context) {
                        b.note = b.note + "-forward";
                    }

                    @Override
                    public void mapBtoA(Target b, Source a, MappingContext context) {
                        a.note = a.note + "-reverse";
                    }
                }).register();
        BoundMapperFacade<Source, Target> bound = mapperFactory.getMapperFacade(Source.class, Target.class);
        Target target = bound.map(source("hook"));
        Source restored = bound.mapReverse(target);
        assertEquals("note-hook-forward", target.note);
        assertEquals("note-hook-forward-reverse", restored.note);
    }

    /**
     * Verifies: ORK-EXT-003, ORK-MAP-002
     * Depends-On: existingDestinationIsRetained, creationMapCopiesConfiguredProperties
     */
    @Test
    void registeredCustomMapperCopiesIntoExistingDestination() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerMapper(new CustomMapper<Source, Target>() {
            @Override
            public void mapAtoB(Source a, Target b, MappingContext context) {
                b.label = "registered-" + a.name;
            }
        });
        Target supplied = new Target();
        Target alias = supplied;
        mapperFactory.getMapperFacade().map(source("mapper"), supplied);
        assertSame(alias, supplied);
        assertEquals("registered-mapper", supplied.label);
    }

    /**
     * Verifies: ORK-OBJ-003, ORK-MAP-001
     * Depends-On: creationMapCopiesConfiguredProperties, classMapAcceptsClassTokens
     */
    @Test
    void concreteTypeRegistrationConstructsInterfaceDestination() {
        MapperFactory mapperFactory = factory();
        mapperFactory.registerConcreteType(NamedView.class, NamedViewImpl.class);
        NamedView target = mapperFactory.getMapperFacade().map(source("concrete"), NamedView.class);
        assertInstanceOf(NamedViewImpl.class, target);
        assertEquals("concrete", target.getName());
    }

    /**
     * Verifies: ORK-CTX-001, ORK-CVT-001
     * Depends-On: customConverterHandlesCompatiblePair, registeredRuleBecomesActive
     */
    @Test
    void converterReceivesCurrentMappingContext() {
        MapperFactory mapperFactory = factory();
        boolean[] contextSeen = { false };
        mapperFactory.getConverterFactory().registerConverter(new CustomConverter<String, Target>() {
            @Override
            public Target convert(String source, Type<? extends Target> destinationType, MappingContext context) {
                contextSeen[0] = context != null;
                Target target = new Target();
                target.label = source;
                return target;
            }
        });
        Target target = mapperFactory.getMapperFacade().map("context", Target.class);
        assertTrue(contextSeen[0]);
        assertEquals("context", target.label);
    }

    /**
     * Verifies: ORK-TYP-002, ORK-TYP-003
     * Depends-On: classMapAcceptsClassTokens, listMappingMapsEveryElement
     */
    @Test
    void genericListTokensGuideElementConversion() {
        Type<String> strings = new TypeBuilder<String>() { }.build();
        Type<Integer> integers = TypeFactory.valueOf(Integer.class);
        List<Integer> result = factory().getMapperFacade().mapAsList(Arrays.asList("3", "4"), strings, integers);
        assertEquals(Arrays.asList(3, 4), result);
    }

    /**
     * Verifies: ORK-TYP-002, ORK-TYP-003
     * Depends-On: classMapAcceptsClassTokens, defaultFactoryMapsMatchingBean
     */
    @Test
    void genericMapTokensGuideKeyAndValueConversion() {
        StringMapHolder input = new StringMapHolder();
        input.values = new LinkedHashMap<>();
        input.values.put("6", "7");
        Type<Map<String, String>> strings = new TypeBuilder<Map<String, String>>() { }.build();
        assertEquals(strings, TypeFactory.valueOf(Map.class, String.class, String.class));
        IntegerMapHolder result = factory().getMapperFacade().map(input, IntegerMapHolder.class);
        assertEquals(Integer.valueOf(7), result.values.get(6));
    }

    /**
     * Verifies: ORK-TYP-003, ORK-MAP-001
     * Depends-On: defaultFactoryMapsMatchingBean, creationMapCopiesConfiguredProperties
     */
    @Test
    void automaticMappingConvertsStringAndEnumProperties() {
        StatusText input = new StatusText();
        input.status = "DONE";
        StatusValue target = factory().getMapperFacade().map(input, StatusValue.class);
        assertEquals(Status.DONE, target.status);
    }

    /**
     * Verifies: ORK-FAC-001, ORK-MAP-001
     * Depends-On: defaultFactoryMapsMatchingBean, registeredRuleBecomesActive
     */
    @Test
    void configurableMapperExposesConfiguredFacadeWorkflow() {
        ConfigurableMapper mapper = new ConfigurableMapper() {
            @Override
            protected void configure(MapperFactory mapperFactory) {
                mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
            }
        };
        assertEquals("configured", mapper.map(source("configured"), Target.class).label);
    }

    /**
     * Verifies: ORK-FLD-005
     * Depends-On: missingPropertyFailsDuringConfiguration, classMapAcceptsClassTokens
     */
    @Test
    void unresolvedDestinationPropertyRaisesMappingException() {
        MapperFactory mapperFactory = factory();
        assertThrows(MappingException.class,
                () -> mapperFactory.classMap(Source.class, Target.class).field("name", "absent"));
    }

    /**
     * Verifies: ORK-EXP-004
     * Depends-On: missingPropertyFailsDuringConfiguration, nestedExpressionTraversesObject
     */
    @Test
    void malformedExpressionRaisesMappingException() {
        MapperFactory mapperFactory = factory();
        assertThrows(MappingException.class,
                () -> mapperFactory.classMap(Source.class, Target.class).field("values[", "label"));
    }

    /**
     * Verifies: ORK-FAC-002
     * Depends-On: disabledAutoMappingRejectsUnregisteredPair, defaultFactoryMapsMatchingBean
     */
    @Test
    void disabledAutoMappingRejectsUnregisteredWorkflow() {
        MapperFactory mapperFactory = new DefaultMapperFactory.Builder().useAutoMapping(false).build();
        assertThrows(MappingException.class,
                () -> mapperFactory.getMapperFacade().map(source("no-path"), Target.class));
    }

    /**
     * Verifies: ORK-CVT-005
     * Depends-On: identifiedConverterCanBeRetrieved, registeredRuleBecomesActive
     */
    @Test
    void missingFieldConverterRaisesMappingException() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(TextRecord.class, NumberRecord.class)
                .fieldMap("amount", "amount").converter("absent").add().register();
        TextRecord input = new TextRecord();
        input.amount = "9";
        assertThrows(MappingException.class,
                () -> mapperFactory.getMapperFacade().map(input, NumberRecord.class));
    }

    /**
     * Verifies: ORK-CON-002, ORK-MAP-004
     * Depends-On: creationMapCopiesConfiguredProperties, disabledAutoMappingRejectsUnregisteredPair
     */
    @Test
    void missingConstructionPathRaisesMappingException() {
        MapperFactory mapperFactory = factory();
        assertThrows(MappingException.class,
                () -> mapperFactory.getMapperFacade().map(source("interface"), Unconstructable.class));
    }

    /**
     * Verifies: ORK-FAC-005, ORK-CVI-001
     * Depends-On: registeredRuleBecomesActive, boundFacadeUsesRegisteredPair
     */
    @Test
    void configuredFactorySupportsConcurrentSharedUse() throws Exception {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").register();
        BoundMapperFacade<Source, Target> bound = mapperFactory.getMapperFacade(Source.class, Target.class);
        ExecutorService executor = Executors.newFixedThreadPool(3);
        try {
            List<Callable<String>> work = Arrays.asList(
                    () -> bound.map(source("one")).label,
                    () -> bound.map(source("two")).label,
                    () -> mapperFactory.getMapperFacade().map(source("three"), Target.class).label);
            List<Future<String>> results = executor.invokeAll(work);
            Set<String> labels = new LinkedHashSet<>();
            for (Future<String> result : results) {
                labels.add(result.get());
            }
            assertEquals(new LinkedHashSet<>(Arrays.asList("one", "two", "three")), labels);
        } finally {
            executor.shutdownNow();
        }
    }

    /**
     * Verifies: ORK-BND-002, ORK-CVI-003
     * Depends-On: existingDestinationIsRetained, boundFacadeUsesRegisteredPair
     */
    @Test
    void boundExistingDestinationRetainsIdentityAndRules() {
        MapperFactory mapperFactory = factory();
        mapperFactory.classMap(Source.class, Target.class).field("name", "label").byDefault().register();
        BoundMapperFacade<Source, Target> bound = mapperFactory.getMapperFacade(Source.class, Target.class);
        Target supplied = new Target();
        Target alias = supplied;
        bound.map(source("existing"), supplied);
        assertSame(alias, supplied);
        assertEquals("existing", supplied.label);
        assertEquals("note-existing", supplied.note);
    }
}
