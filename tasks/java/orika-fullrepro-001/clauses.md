# Clause Sidecar for `spec_v2.md`

This WIP-only sidecar gives Stage 3 stable identifiers. All v1 identifiers remain unchanged; v2 adds `ORK-FLT-005` through `ORK-FLT-007`. Quotes are candidate-spec clauses; anchors identify their visible section. IDs do not appear in the candidate body.

| ID | Anchor | Verbatim clause |
| --- | --- | --- |
| ORK-FAC-001 | Mapping Configuration and Field Rules | The `DefaultMapperFactory.Builder.build()` operation must return a usable factory whose auto-mapping, built-in converters, and null mapping are enabled unless their builder methods set a different value. |
| ORK-FAC-002 | Mapping Configuration and Field Rules | When `useAutoMapping(false)` is set and no compatible class map, mapper, or converter is registered, the mapping operation must raise `MappingException`. |
| ORK-FAC-003 | Mapping Configuration and Field Rules | The `MapperFactory.classMap()` operation must accept `Class` or `Type` tokens for both sides and return a builder tied to that factory. |
| ORK-FAC-004 | Mapping Configuration and Field Rules | The `ClassMapBuilder.register()` operation must activate accumulated rules for later facades; if the builder was not obtained from a factory, then `register()` must raise `IllegalStateException`. |
| ORK-FAC-005 | Product Overview | A configured factory and its facades must support concurrent shared application use after configuration. |
| ORK-FLD-001 | Mapping Configuration and Field Rules | The `field(a, b)` operation must create a bidirectional correspondence. |
| ORK-FLD-002 | Mapping Configuration and Field Rules | The `fieldAToB(a, b)` operation must apply only while mapping A to B, and `fieldBToA(a, b)` must apply only while mapping B to A. |
| ORK-FLD-003 | Mapping Configuration and Field Rules | The `exclude(name)` operation must prevent the named property from default mapping. |
| ORK-FLD-004 | Mapping Configuration and Field Rules | The `byDefault()` operation must add remaining readable/writable properties whose names match exactly and must not override explicit rules. |
| ORK-FLD-005 | Mapping Configuration and Field Rules | If a referenced property is absent or inaccessible, then configuration must raise `PropertyNotFoundException` or `MappingException`. |
| ORK-EXP-001 | Mapping Configuration and Field Rules | Dot-separated expressions must traverse nested properties. |
| ORK-EXP-002 | Mapping Configuration and Field Rules | Bracket expressions must address array or list indexes and quoted map keys. |
| ORK-EXP-003 | Mapping Configuration and Field Rules | Brace expressions must project elements; `key` and `value` must address map-entry parts, and empty braces must address the element itself. |
| ORK-EXP-004 | Mapping Configuration and Field Rules | If an expression is malformed or cannot resolve a public field or JavaBeans property, then configuration must raise `MappingException`. |
| ORK-NUL-001 | Mapping Configuration and Field Rules | Null source properties must overwrite destination properties by default. |
| ORK-NUL-002 | Mapping Configuration and Field Rules | When null mapping is disabled for a direction, a null source must leave the existing destination property unchanged, and the field setting must take precedence over the class-map setting, which must take precedence over the factory setting. |
| ORK-CON-001 | Mapping Configuration and Field Rules | The `constructorA(parameterNames)` and `constructorB(parameterNames)` operations must select the corresponding constructor by property names. |
| ORK-CON-002 | Mapping Configuration and Field Rules | If no accessible construction path, concrete type, converter, or object factory exists, then creation mapping must raise `MappingException`. |
| ORK-INH-001 | Mapping Configuration and Field Rules | The `use(parentA, parentB)` operation must reuse compatible registered parent rules; if the pair is incompatible, then registration or mapping must raise `MappingException`. |
| ORK-MAP-001 | Object, Collection, and Generic Mapping | When `MapperFacade.map(source, destinationClass)` receives a non-null source, it must create a destination and copy every applicable configured property. |
| ORK-MAP-002 | Object, Collection, and Generic Mapping | When an existing destination is supplied, `MapperFacade.map(source, destination)` must mutate and retain that same instance. |
| ORK-MAP-003 | Object, Collection, and Generic Mapping | When a creation-style `map` receives a null source, it must return null. |
| ORK-MAP-004 | Object, Collection, and Generic Mapping | If conversion or construction cannot be resolved, then the facade must raise `MappingException`. |
| ORK-BND-001 | Object, Collection, and Generic Mapping | A `BoundMapperFacade` obtained from `getMapperFacade(aType, bType)` must bind the same pair and rules used by the unbound facade. |
| ORK-BND-002 | Object, Collection, and Generic Mapping | Its `map()` operation must project A to B, its `mapReverse()` operation must project B to A, and existing-destination overloads must retain supplied instances. |
| ORK-BND-003 | Object, Collection, and Generic Mapping | When a value is incompatible with its bound side, the facade must raise a type-related runtime exception. |
| ORK-MUL-001 | Object, Collection, and Generic Mapping | The `mapAsList()`, `mapAsSet()`, `mapAsArray()`, and `mapAsCollection()` operations must map every element through the same element rule as single-object mapping. |
| ORK-MUL-002 | Object, Collection, and Generic Mapping | List and array results must preserve encounter order, set results must obey set uniqueness, and `mapAsCollection()` must add values to the supplied collection. |
| ORK-MUL-003 | Object, Collection, and Generic Mapping | If an element cannot be mapped, then the operation must raise `MappingException`. |
| ORK-TYP-001 | Object, Collection, and Generic Mapping | `TypeBuilder.build()` and `TypeFactory.valueOf()` must produce reusable `Type` tokens that retain raw and actual generic information and compare equal for equivalent declarations. |
| ORK-TYP-002 | Object, Collection, and Generic Mapping | When `Type` tokens are supplied, element and map key/value types must guide conversion rather than erasing to `Object`. |
| ORK-TYP-003 | Object, Collection, and Generic Mapping | Arrays, collections, maps, primitives, wrappers, strings, enums, public fields, and JavaBeans properties must participate in automatic mapping when compatible. |
| ORK-TYP-004 | Object, Collection, and Generic Mapping | If generic arity is wrong or conversion is incompatible, then type construction or mapping must raise `IllegalArgumentException` or `MappingException`. |
| ORK-CVT-001 | Conversion and Extension Policies | A `CustomConverter<S,D>` must infer its supported pair from concrete generic arguments and must invoke `convert(source, destinationType, mappingContext)` for a compatible registered conversion. |
| ORK-CVT-002 | Conversion and Extension Policies | If generic arguments cannot be inferred, then construction must raise `IllegalStateException`. |
| ORK-CVT-003 | Conversion and Extension Policies | Anonymous converters must be eligible by compatible pair, with the most specific selected before a broader converter. |
| ORK-CVT-004 | Conversion and Extension Policies | Identified converters must be retrievable by `getConverter(id)` and selected by `FieldMapBuilder.converter(id)` after `add()`. |
| ORK-CVT-005 | Conversion and Extension Policies | If the identifier is absent, then mapping must raise `MappingException`. |
| ORK-EXT-001 | Conversion and Extension Policies | A `BidirectionalConverter<S,D>` must dispatch S-to-D requests to `convertTo()` and D-to-S requests to `convertFrom()`, and `reverse()` must exchange those directions. |
| ORK-EXT-002 | Conversion and Extension Policies | A `CustomMapper<A,B>` attached through `customize()` must run after ordinary field mappings, using `mapAtoB()` forward and `mapBtoA()` in reverse. |
| ORK-EXT-003 | Conversion and Extension Policies | A mapper registered through `registerMapper()` must copy into an existing destination rather than replace it. |
| ORK-EXT-004 | Conversion and Extension Policies | If its generic pair is absent and not supplied by overrides, then type lookup must raise `IllegalStateException`. |
| ORK-OBJ-001 | Conversion and Extension Policies | An `ObjectFactory<D>` registered for a destination must create it before field rules copy properties. |
| ORK-OBJ-002 | Conversion and Extension Policies | Where a factory is registered for both destination and source types, it must take precedence only for compatible sources. |
| ORK-OBJ-003 | Conversion and Extension Policies | A type registered through `registerConcreteType(abstractType, concreteType)` must construct the concrete implementation when mapping to the abstract type. |
| ORK-OBJ-004 | Conversion and Extension Policies | If a factory or concrete registration returns an incompatible object, then mapping must raise a type-related runtime exception. |
| ORK-FLT-001 | Conversion and Extension Policies | A registered `Filter<A,B>` must apply only to property pairs accepted by `appliesTo()`. |
| ORK-FLT-002 | Conversion and Extension Policies | When `shouldMap()` returns false, the field must remain unmapped; when it returns true, enabled `filterSource()` and `filterDestination()` transformations must participate on their declared sides. |
| ORK-FLT-003 | Conversion and Extension Policies | `NullFilter` must leave both values unchanged and always permit mapping. |
| ORK-FLT-004 | Conversion and Extension Policies | If a filter returns an incompatible value, then mapping must raise a type-related runtime exception. |
| ORK-FLT-005 | Conversion and Extension Policies | The `shouldMap()` callback must declare method-level type variables `S extends A` and `D extends B`; in order, it must receive the source `Type<S>`, source property name as a `String`, source value as `S`, destination `Type<D>`, destination property name as a `String`, destination value as `D`, and the current `MappingContext`, and it must return the boolean mapping decision. |
| ORK-FLT-006 | Conversion and Extension Policies | The `filterSource()` callback must declare a method-level `S extends A`; in order, it must receive the source value as `S`, its `Type<S>`, source property name as a `String`, destination `Type<?>`, destination property name as a `String`, and the current `MappingContext`, and it must return the replacement as the same `S` type. |
| ORK-FLT-007 | Conversion and Extension Policies | The `filterDestination()` callback must declare a method-level `D extends B`; in order, it must receive the destination value as `D`, source `Type<?>`, source property name as a `String`, its destination `Type<D>`, destination property name as a `String`, and the current `MappingContext`, and it must return the replacement as the same `D` type. |
| ORK-CTX-001 | Conversion and Extension Policies | The `MappingContext` passed to extensions must represent the current operation and preserve cycle identity within it. |
| ORK-CVI-001 | Cross-View Invariants | A class map committed through `register()` must govern the unbound facade and every later bound facade for that pair. |
| ORK-CVI-002 | Cross-View Invariants | A bidirectional field rule must produce mutually consistent forward and reverse results, while a directional rule must affect only its declared direction. |
| ORK-CVI-003 | Cross-View Invariants | Existing-destination mapping must apply the same fields, converters, null policy, custom mapper, and filters as creation mapping for the same pair. |
| ORK-CVI-004 | Cross-View Invariants | Direct element mapping and mapping the same element inside a list, set, array, or supplied collection must produce equivalent property values. |
| ORK-CVI-005 | Cross-View Invariants | Equivalent `Type` tokens from `TypeBuilder` and `TypeFactory` must select the same class maps and converters. |
| ORK-CVI-006 | Cross-View Invariants | A field-level converter identifier must affect that field across single, bound, supported reverse, and multi-occurrence projections without affecting unrelated fields. |
| ORK-CVI-007 | Cross-View Invariants | A registered object factory or concrete type must determine construction consistently for unbound, bound, and multi-occurrence creation. |
| ORK-CVI-008 | Cross-View Invariants | A filter decision for an applicable property pair must agree across creation and existing-destination mapping while leaving unrelated pairs unchanged. |
| ORK-ENV-001 | Appendix A: Environment | The project must declare a root `pom.xml` with coordinate `ma.glasnost.orika:orika-core:1.6.0-SNAPSHOT` and produce the corresponding JAR through the standard Maven lifecycle. |

The eight Error Semantics table rows are indexed aliases of the corresponding failure clauses: `ORK-FLD-005`/`ORK-EXP-004`, `ORK-FAC-002`, `ORK-CON-002`/`ORK-MAP-004`, `ORK-FAC-004`, `ORK-CVT-002`/`ORK-EXT-004`, `ORK-CVT-005`, `ORK-TYP-004`, and `ORK-OBJ-004`/`ORK-FLT-004`.
