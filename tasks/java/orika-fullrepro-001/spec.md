# Orika Core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

This Java object-mapping library is a component that copies data between structurally different object graphs through runtime mapping rules. Applications configure type pairs, property expressions, conversion policies, and construction hooks through a `MapperFactory`, then project the same configuration through unbound, bound, forward, reverse, single-object, and multi-occurrence mapping APIs.

The contract covers JavaBeans properties, public fields, nested paths, arrays, collections, maps, generic type tokens, directional rules, null policy, converters, custom mappers, object factories, and filters. A configured factory and its facades must support concurrent shared application use after configuration.

## Non-Goals

- This specification does not require command-line tools, services, or persistent storage.
- This specification does not require generated source text, generated class names, compiler internals, cache layout, logging text, or exact `toString()` output.
- This specification does not require package-private helpers, test support types, reflection into private state, or public implementation classes absent from the documented import surface.
- This specification does not define Spring, Hibernate proxy, JAXB, Guava Optional, alternate compiler, or custom property-resolver integrations.
- This specification does not define ad-hoc inline getter/setter expression syntax.
- This specification does not require deprecated APIs, compatibility aliases, or the separate Janino adapter.

## Representative Workflows

### Configure and Apply a Bidirectional Class Map

```java
import ma.glasnost.orika.MapperFacade;
import ma.glasnost.orika.MapperFactory;
import ma.glasnost.orika.impl.DefaultMapperFactory;

MapperFactory factory = new DefaultMapperFactory.Builder().build();
factory.classMap(Person.class, PersonDto.class)
       .field("name.first", "firstName")
       .field("name.last", "lastName")
       .byDefault()
       .register();
MapperFacade mapper = factory.getMapperFacade();
PersonDto dto = mapper.map(person, PersonDto.class);
Person roundTrip = mapper.map(dto, Person.class);
```

This workflow records nested-property correspondences, adds exact-name properties, commits the pair, and observes it in both directions.

### Reuse a Bound Facade and Generic Type Tokens

```java
import java.util.List;
import ma.glasnost.orika.BoundMapperFacade;
import ma.glasnost.orika.MapperFactory;
import ma.glasnost.orika.impl.DefaultMapperFactory;
import ma.glasnost.orika.metadata.Type;
import ma.glasnost.orika.metadata.TypeBuilder;

MapperFactory factory = new DefaultMapperFactory.Builder().build();
BoundMapperFacade<Person, PersonDto> bound =
    factory.getMapperFacade(Person.class, PersonDto.class);
PersonDto dto = bound.map(person);
Person restored = bound.mapReverse(dto);
Type<List<Person>> peopleType = new TypeBuilder<List<Person>>() {}.build();
```

This workflow reuses one pair-specific facade and retains generic element information that a raw `Class` token lacks.

## Mapping Configuration and Field Rules

Mapping configuration defines how a factory interprets source and destination properties before any facade projects the result.

**Factory construction and activation.** The `DefaultMapperFactory.Builder.build()` operation must return a usable factory whose auto-mapping, built-in converters, and null mapping are enabled unless their builder methods set a different value. When `useAutoMapping(false)` is set and no compatible class map, mapper, or converter is registered, the mapping operation must raise `MappingException`. The `MapperFactory.classMap()` operation must accept `Class` or `Type` tokens for both sides and return a builder tied to that factory. The `ClassMapBuilder.register()` operation must activate accumulated rules for later facades; if the builder was not obtained from a factory, then `register()` must raise `IllegalStateException`.

**Property selection and direction.** The `field(a, b)` operation must create a bidirectional correspondence. The `fieldAToB(a, b)` operation must apply only while mapping A to B, and `fieldBToA(a, b)` must apply only while mapping B to A. The `exclude(name)` operation must prevent the named property from default mapping. The `byDefault()` operation must add remaining readable/writable properties whose names match exactly and must not override explicit rules. If a referenced property is absent or inaccessible, then configuration must raise `PropertyNotFoundException` or `MappingException`.

**Property-expression grammar.** Dot-separated expressions must traverse nested properties. Bracket expressions must address array or list indexes and quoted map keys. Brace expressions must project elements; `key` and `value` must address map-entry parts, and empty braces must address the element itself. If an expression is malformed or cannot resolve a public field or JavaBeans property, then configuration must raise `MappingException`.

**Nulls, constructors, and inherited rules.** Null source properties must overwrite destination properties by default. When null mapping is disabled for a direction, a null source must leave the existing destination property unchanged, and the field setting must take precedence over the class-map setting, which must take precedence over the factory setting. The `constructorA(parameterNames)` and `constructorB(parameterNames)` operations must select the corresponding constructor by property names. If no accessible construction path, concrete type, converter, or object factory exists, then creation mapping must raise `MappingException`. The `use(parentA, parentB)` operation must reuse compatible registered parent rules; if the pair is incompatible, then registration or mapping must raise `MappingException`.

## Object, Collection, and Generic Mapping

Facade operations project one configured rule graph across new objects, existing objects, reverse mappings, and multi-occurrence containers.

**Single objects.** When `MapperFacade.map(source, destinationClass)` receives a non-null source, it must create a destination and copy every applicable configured property. When an existing destination is supplied, `MapperFacade.map(source, destination)` must mutate and retain that same instance. When a creation-style `map` receives a null source, it must return null. If conversion or construction cannot be resolved, then the facade must raise `MappingException`.

**Bound projections.** A `BoundMapperFacade` obtained from `getMapperFacade(aType, bType)` must bind the same pair and rules used by the unbound facade. Its `map()` operation must project A to B, its `mapReverse()` operation must project B to A, and existing-destination overloads must retain supplied instances. When a value is incompatible with its bound side, the facade must raise a type-related runtime exception.

**Multi-occurrence results.** The `mapAsList()`, `mapAsSet()`, `mapAsArray()`, and `mapAsCollection()` operations must map every element through the same element rule as single-object mapping. List and array results must preserve encounter order, set results must obey set uniqueness, and `mapAsCollection()` must add values to the supplied collection. If an element cannot be mapped, then the operation must raise `MappingException`.

**Generic tokens and automatic shapes.** `TypeBuilder.build()` and `TypeFactory.valueOf()` must produce reusable `Type` tokens that retain raw and actual generic information and compare equal for equivalent declarations. When `Type` tokens are supplied, element and map key/value types must guide conversion rather than erasing to `Object`. Arrays, collections, maps, primitives, wrappers, strings, enums, public fields, and JavaBeans properties must participate in automatic mapping when compatible. If generic arity is wrong or conversion is incompatible, then type construction or mapping must raise `IllegalArgumentException` or `MappingException`.

## Conversion and Extension Policies

Extension APIs refine conversion, copying, construction, and per-field decisions without exposing generated-code internals.

**Converters.** A `CustomConverter<S,D>` must infer its supported pair from concrete generic arguments and must invoke `convert(source, destinationType, mappingContext)` for a compatible registered conversion. If generic arguments cannot be inferred, then construction must raise `IllegalStateException`. Anonymous converters must be eligible by compatible pair, with the most specific selected before a broader converter. Identified converters must be retrievable by `getConverter(id)` and selected by `FieldMapBuilder.converter(id)` after `add()`. If the identifier is absent, then mapping must raise `MappingException`.

**Bidirectional converters and custom mappers.** A `BidirectionalConverter<S,D>` must dispatch S-to-D requests to `convertTo()` and D-to-S requests to `convertFrom()`, and `reverse()` must exchange those directions. A `CustomMapper<A,B>` attached through `customize()` must run after ordinary field mappings, using `mapAtoB()` forward and `mapBtoA()` in reverse. A mapper registered through `registerMapper()` must copy into an existing destination rather than replace it. If its generic pair is absent and not supplied by overrides, then type lookup must raise `IllegalStateException`.

**Object factories and concrete types.** An `ObjectFactory<D>` registered for a destination must create it before field rules copy properties. Where a factory is registered for both destination and source types, it must take precedence only for compatible sources. A type registered through `registerConcreteType(abstractType, concreteType)` must construct the concrete implementation when mapping to the abstract type. If a factory or concrete registration returns an incompatible object, then mapping must raise a type-related runtime exception.

**Filters and context.** A registered `Filter<A,B>` must apply only to property pairs accepted by `appliesTo()`. When `shouldMap()` returns false, the field must remain unmapped; when it returns true, enabled `filterSource()` and `filterDestination()` transformations must participate on their declared sides. The `shouldMap()` callback must declare method-level type variables `S extends A` and `D extends B`; in order, it must receive the source `Type<S>`, source property name as a `String`, source value as `S`, destination `Type<D>`, destination property name as a `String`, destination value as `D`, and the current `MappingContext`, and it must return the boolean mapping decision. The `filterSource()` callback must declare a method-level `S extends A`; in order, it must receive the source value as `S`, its `Type<S>`, source property name as a `String`, destination `Type<?>`, destination property name as a `String`, and the current `MappingContext`, and it must return the replacement as the same `S` type. The `filterDestination()` callback must declare a method-level `D extends B`; in order, it must receive the destination value as `D`, source `Type<?>`, source property name as a `String`, its destination `Type<D>`, destination property name as a `String`, and the current `MappingContext`, and it must return the replacement as the same `D` type. `NullFilter` must leave both values unchanged and always permit mapping. If a filter returns an incompatible value, then mapping must raise a type-related runtime exception. The `MappingContext` passed to extensions must represent the current operation and preserve cycle identity within it.

## State Model

The core state is a runtime registration graph owned by a `MapperFactory`: class maps, field rules, converters, custom mappers, object factories, concrete types, filters, and factory-wide policies.

Its public projections are configuration builders committed by `register()`; the unbound `MapperFacade`; pair-specific `BoundMapperFacade` instances; returned or mutated destination graphs; converter lookups and `Type` tokens; and extension callbacks receiving the current `MappingContext`.

## Error Semantics

| Condition | Required result |
|---|---|
| A property expression is missing, inaccessible, or malformed | Configuration must raise `PropertyNotFoundException` or `MappingException`. |
| Auto-mapping is disabled and no registered path exists | Mapping must raise `MappingException`. |
| No construction or conversion path creates the destination | Mapping must raise `MappingException`. |
| A factory-less builder calls `register()` | The builder must raise `IllegalStateException`. |
| An extension cannot infer its generic pair | Construction or lookup must raise `IllegalStateException`. |
| A requested converter identifier is absent | Mapping must raise `MappingException`. |
| Generic type arity is wrong | Type construction must raise `IllegalArgumentException`. |
| An extension returns an incompatible value | Mapping must raise a type-related runtime exception. |

## Cross-View Invariants

1. A class map committed through `register()` must govern the unbound facade and every later bound facade for that pair.
2. A bidirectional field rule must produce mutually consistent forward and reverse results, while a directional rule must affect only its declared direction.
3. Existing-destination mapping must apply the same fields, converters, null policy, custom mapper, and filters as creation mapping for the same pair.
4. Direct element mapping and mapping the same element inside a list, set, array, or supplied collection must produce equivalent property values.
5. Equivalent `Type` tokens from `TypeBuilder` and `TypeFactory` must select the same class maps and converters.
6. A field-level converter identifier must affect that field across single, bound, supported reverse, and multi-occurrence projections without affecting unrelated fields.
7. A registered object factory or concrete type must determine construction consistently for unbound, bound, and multi-occurrence creation.
8. A filter decision for an applicable property pair must agree across creation and existing-destination mapping while leaving unrelated pairs unchanged.

## Public Interface

### Import Surface

```java
import ma.glasnost.orika.BoundMapperFacade;
import ma.glasnost.orika.CustomConverter;
import ma.glasnost.orika.CustomFilter;
import ma.glasnost.orika.CustomMapper;
import ma.glasnost.orika.Filter;
import ma.glasnost.orika.MapperFacade;
import ma.glasnost.orika.MapperFactory;
import ma.glasnost.orika.MappingContext;
import ma.glasnost.orika.MappingException;
import ma.glasnost.orika.NullFilter;
import ma.glasnost.orika.ObjectFactory;
import ma.glasnost.orika.PropertyNotFoundException;
import ma.glasnost.orika.converter.BidirectionalConverter;
import ma.glasnost.orika.converter.ConverterFactory;
import ma.glasnost.orika.impl.ConfigurableMapper;
import ma.glasnost.orika.impl.DefaultMapperFactory;
import ma.glasnost.orika.metadata.ClassMapBuilder;
import ma.glasnost.orika.metadata.FieldMapBuilder;
import ma.glasnost.orika.metadata.Type;
import ma.glasnost.orika.metadata.TypeBuilder;
import ma.glasnost.orika.metadata.TypeFactory;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `DefaultMapperFactory` | class | Default owner of registrations and facades. |
| `DefaultMapperFactory.Builder` | class | Configures and builds the default factory. |
| `Builder.build` | method | Creates the configured factory. |
| `Builder.useAutoMapping` | method | Controls unregistered-pair mapping. |
| `Builder.useBuiltinConverters` | method | Controls built-in converters. |
| `Builder.mapNulls` | method | Sets factory null policy. |
| `MapperFactory` | interface | Configures pairs and exposes facades. |
| `MapperFactory.classMap` | method | Starts a pair definition. |
| `MapperFactory.getMapperFacade` | method | Returns an unbound or pair-bound facade. |
| `MapperFactory.getConverterFactory` | method | Returns the converter registry. |
| `MapperFactory.registerMapper` | method | Registers a custom mapper. |
| `MapperFactory.registerObjectFactory` | method | Registers destination construction. |
| `MapperFactory.registerConcreteType` | method | Associates abstract and concrete types. |
| `MapperFactory.registerFilter` | method | Registers a field filter. |
| `ClassMapBuilder` | class | Accumulates class-map rules. |
| `field / fieldAToB / fieldBToA` | method | Adds bidirectional or directional fields. |
| `fieldMap / exclude / byDefault` | method | Refines property selection. |
| `mapNulls / mapNullsInReverse` | method | Sets directional null policy. |
| `constructorA / constructorB / use` | method | Selects constructors and inherited rules. |
| `customize / register` | method | Attaches custom copying and commits rules. |
| `FieldMapBuilder` | class | Refines one field rule. |
| `aToB / bToA / converter / exclude / add` | method | Sets field direction, conversion, exclusion, and commitment. |
| `MapperFacade` | interface | Maps objects through factory state. |
| `map` | method | Creates or updates one destination. |
| `mapAsList / mapAsSet / mapAsArray / mapAsCollection` | method | Maps multi-occurrence inputs. |
| `BoundMapperFacade` | interface | Reuses one pair in both directions. |
| `map / mapReverse` | method | Applies forward or reverse bound mapping. |
| `ConverterFactory` | interface | Registers and resolves converters. |
| `registerConverter / getConverter / hasConverter / canConvert` | method | Manages converter registrations. |
| `CustomConverter` | abstract class | Base for one-direction conversion. |
| `BidirectionalConverter` | abstract class | Base for paired conversion. |
| `convertTo / convertFrom / reverse` | method | Implements and reverses paired conversion. |
| `CustomMapper` | abstract class | Base for custom copying into existing objects. |
| `mapAtoB / mapBtoA` | method | Applies directional custom copying. |
| `ObjectFactory` | interface | Constructs mapping destinations. |
| `ObjectFactory.create` | method | Creates a destination in context. |
| `Filter` | interface | Controls applicable field mapping. |
| `appliesTo / shouldMap` | method | Selects property pairs and runtime decisions. |
| `filtersSource / filterSource` | method | Declares and applies source transformation. |
| `filtersDestination / filterDestination` | method | Declares and applies destination transformation. |
| `CustomFilter` | abstract class | Infers filter types. |
| `NullFilter` | class | No-op filter base. |
| `Type` | class | Retains raw and generic type information. |
| `TypeBuilder / TypeBuilder.build` | class | Captures a generic type declaration. |
| `TypeFactory / TypeFactory.valueOf` | class | Creates canonical type tokens. |
| `MappingContext` | class | Carries operation-local identity and extension context. |
| `MappingException` | exception | Reports mapping failure. |
| `PropertyNotFoundException` | exception | Reports an unresolved property. |
| `ConfigurableMapper` | class | Shareable facade configured through subclass hooks. |

### CLI Entry Points

There is no console script for this library. No `main` entry point is supported. Programmatic use is through the Java imports listed above.

## Appendix A: Environment

The working environment runs Java 17 and Maven 3.9 on Linux without network access. The following artifacts are preinstalled and resolvable: `org.javassist:javassist`, `com.thoughtworks.paranamer:paranamer`, `org.slf4j:slf4j-api`, and `com.google.guava:guava`. The assessment environment provides the same runtime and artifact set.

The project must declare a root `pom.xml` with coordinate `ma.glasnost.orika:orika-core:1.6.0-SNAPSHOT` and produce the corresponding JAR through the standard Maven lifecycle.

## Appendix B: Assessment Notes

Implementations are exercised through documented public Java types and members. Checks cover configuration precedence, field rules, expressions, new and existing destinations, bound and reverse facades, nulls, generic tokens, extensions, error paths, and cross-view consistency. The focus is observable behavior rather than generated code, private layout, messages, or exact textual representations.
