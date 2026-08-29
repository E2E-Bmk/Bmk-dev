# Commons Configuration Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`commons-configuration2` is a Java configuration library that stores typed key-value state and projects it through mutable configurations, prefix and tree views, variable interpolation, ordered composition, lazy builders, and typed events.

The scoped library is an in-memory, programmatic API. Its central fact source is a set of keyed raw property values, while typed getters, subsets, hierarchical sub-configurations, interpolated results, composite precedence, combined trees, builder results, and event streams expose coordinated views of that state.

## Non-Goals

- This specification does not require file loading, file saving, URL resolution, format parsers, or serialization.
- This specification does not require reloading controllers, reloading builders, or external change detection.
- This specification does not require servlet, Spring, JXPath, VFS, Jackson, YAML, JNDI, database, or remote-service integrations.
- This specification does not define custom expression-engine implementations or merge-combiner semantics.
- This specification does not require built-in script, DNS, URL, XML, resource-bundle, or file interpolation lookups.
- This specification does not require private helper classes, internal map or node-model layouts, locking algorithms, or reflection-based implementation structure.
- This specification does not define exact exception messages, logging text, `toString()` formatting, serialization bytes, or clone behavior.

## Representative Workflows

The first workflow builds typed state, resolves a property reference, and edits the same state through a live subset.

```java
import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.Configuration;

BaseConfiguration config = new BaseConfiguration();
config.setProperty("service.host", "db.internal");
config.setProperty("service.port", "5432");
config.setProperty("service.endpoint", "${service.host}:${service.port}");

String endpoint = config.getString("service.endpoint");
int port = config.getInt("service.port");

Configuration service = config.subset("service");
service.setProperty("host", "db.example");

assert endpoint.equals("db.internal:5432");
assert port == 5432;
assert config.getString("service.host").equals("db.example");
```

The typed getters read interpolated values, while `getProperty()` remains the raw projection. The subset removes the `service.` prefix and writes through to the parent.

The second workflow applies first-source precedence and exposes later sources as defaults.

```java
import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.CompositeConfiguration;

BaseConfiguration user = new BaseConfiguration();
user.setProperty("theme", "dark");

BaseConfiguration defaults = new BaseConfiguration();
defaults.setProperty("theme", "light");
defaults.setProperty("pageSize", 25);

CompositeConfiguration layered = new CompositeConfiguration();
layered.addConfiguration(user);
layered.addConfiguration(defaults);

assert layered.getString("theme").equals("dark");
assert layered.getInt("pageSize") == 25;
assert layered.getSource("pageSize") == defaults;
```

The first child that defines a scalar key supplies the visible value. A later configuration supplies only keys absent from earlier children.

The third workflow observes lazy builder creation and replacement.

```java
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.builder.BasicConfigurationBuilder;
import org.apache.commons.configuration2.builder.ConfigurationBuilderEvent;
import org.apache.commons.configuration2.builder.ConfigurationBuilderResultCreatedEvent;

BasicConfigurationBuilder<BaseConfiguration> builder =
        new BasicConfigurationBuilder<>(BaseConfiguration.class);

List<Object> events = new ArrayList<>();
builder.addEventListener(ConfigurationBuilderEvent.ANY, events::add);

BaseConfiguration first = builder.getConfiguration();
BaseConfiguration again = builder.getConfiguration();
builder.resetResult();
BaseConfiguration second = builder.getConfiguration();

assert first == again;
assert first != second;
assert events.stream().anyMatch(e ->
        ((ConfigurationBuilderEvent) e).getEventType()
                == ConfigurationBuilderResultCreatedEvent.RESULT_CREATED);
```

Repeated access returns the same managed object until a reset. A reset invalidates that identity, and the next request creates and announces a replacement.

## Property State and Typed Access

Property state defines how raw values are mutated, enumerated, and converted for callers.

**Mutation and raw projection.**

The `BaseConfiguration` state must begin empty, with `isEmpty()` returning `true`, `size()` returning zero, and `getKeys()` returning no keys.

WHEN `setProperty(key, value)` is called, THEN the configuration must replace every prior value associated with `key` by the supplied value.

WHEN `addProperty(key, value)` is called for a missing key, THEN the configuration must store the value as that key's raw value.

WHEN `addProperty(key, value)` is called for an existing key, THEN the configuration must preserve the existing value order and append the supplied value to the key's multi-value state.

WHEN `clearProperty(key)` is called, THEN the configuration must remove that key and all values associated with it; a missing key must leave the remaining state unchanged.

WHEN `clear()` is called, THEN the configuration must remove every key and value.

The `getProperty(key)` method must return the raw stored scalar or multi-value object without applying interpolation.

The `size()` result must equal the number of distinct keys, and `getKeys()` on `BaseConfiguration` must enumerate keys in first-insertion order.

**Typed scalar and container access.**

WHEN a stored value is compatible with a requested target, THEN `get(Class, key)` and the named getters for strings, booleans, numeric types, `BigInteger`, `BigDecimal`, `Duration`, and enums must return the converted value.

WHEN a key has multiple values and a scalar string getter is used, THEN `getString(key)` must return the first value converted to a string.

WHEN a typed list, collection, array, or string-array getter is used, THEN the getter must convert each represented element to the requested element type and preserve element order.

WHEN a typed getter has a `defaultValue` argument and the key is missing, THEN the getter must return that supplied default without adding the key.

WHEN an object-valued getter without a supplied default reads a missing key while strict missing-value mode is disabled, THEN the getter must return `null`.

WHEN `setThrowExceptionOnMissing(true)` is active and an object-valued getter without a supplied default reads a missing key, THEN the getter must raise `NoSuchElementException`.

WHEN a primitive-valued getter without a supplied default reads a missing key, THEN the getter must raise `NoSuchElementException` regardless of strict missing-value mode.

WHEN `getList(key)` or `getStringArray(key)` reads a missing key, THEN it must return an empty list or empty array regardless of strict missing-value mode.

IF a present value is incompatible with the requested target type, THEN the typed getter must raise `ConversionException`.

**List parsing and encoded strings.**

WHEN an array or collection is supplied to `addProperty` or `setProperty`, THEN the configured `ListDelimiterHandler` must expose its elements as an ordered multi-value property.

WHERE a `DefaultListDelimiterHandler` is installed, a string supplied by a later write must be split on that handler's delimiter while ordinary strings without the delimiter must remain scalar.

WHERE no explicit list delimiter handler is installed, string delimiter splitting must remain disabled.

WHEN `getEncodedString(key, decoder)` receives a non-null `ConfigurationDecoder`, THEN it must pass the selected string value to that decoder and return the decoded string.

IF `getEncodedString(key)` is called without a configured default decoder, THEN it must raise `IllegalStateException`.

IF `getEncodedString(key, decoder)` receives a null decoder, THEN it must raise `IllegalArgumentException`.

## Subset and Hierarchical Views

Subset and hierarchical APIs project selected regions of configuration state while making connection and detachment rules explicit.

**Prefix subsets.**

WHEN `subset(prefix)` is called, THEN the returned configuration must expose keys equal to `prefix` or beginning with `prefix` followed by the delimiter, and it must remove the selected prefix and delimiter from visible keys.

WHEN a parent key equals the subset prefix exactly, THEN the subset must expose that property under the empty-string key.

WHEN a key merely begins with the same characters but lacks the required delimiter boundary, THEN the subset must omit that key.

The default delimiter used by `Configuration.subset(prefix)` must be `"."`; a `SubsetConfiguration` constructed with another delimiter must apply that delimiter, and a null delimiter must concatenate prefix and child key directly.

WHEN a property is changed through a subset, THEN the parent must expose the same change under the translated parent key; WHEN the parent is changed under the selected prefix, THEN the subset must expose that change.

WHEN `clear()` is called on a subset, THEN it must remove only keys visible through that subset and must preserve unrelated parent keys.

WHEN `subset()` is called on an existing subset, THEN the resulting view must compose the prefixes and continue to address the original parent state.

A subset must inherit parent property interpolation, registered parent lookups, list delimiter handling, and strict missing-value policy when the parent exposes those facilities.

IF a `SubsetConfiguration` is constructed with a null parent, THEN construction must raise `NullPointerException`.

**Hierarchical subtree selection.**

The default hierarchical key syntax must use dot-separated child names and zero-based parenthesized indices for repeated children.

WHEN `getMaxIndex(key)` addresses existing repeated nodes, THEN it must return the greatest defined zero-based index for that key.

WHEN `configurationAt(key)` selects exactly one node, THEN it must return an independent mutable configuration rooted at that node.

WHEN `configurationAt(key, true)` selects exactly one node, THEN it must return a connected mutable configuration whose updates are reflected in the parent and whose parent updates are reflected in the sub-configuration.

WHEN the parent removes the complete subtree backing a connected sub-configuration, THEN the sub-configuration must become permanently detached, remain usable, and stop exchanging later updates with the parent.

IF `configurationAt` selects zero nodes or more than one node, THEN it must raise `ConfigurationRuntimeException`.

WHEN `configurationsAt(key)` selects multiple nodes, THEN it must return one independent rooted configuration per selected node in selection order; a missing selection must return an empty list.

WHEN `configurationsAt(key, true)` selects multiple nodes, THEN it must return connected rooted configurations following the same update and detachment rules as `configurationAt(key, true)`.

WHEN `childConfigurationsAt(key)` addresses exactly one parent node, THEN it must return one independent rooted configuration for each direct child; a missing or non-unique parent selection must return an empty list.

WHEN the overload of `childConfigurationsAt` receives `supportUpdates=true`, THEN each returned child configuration must be connected to the parent until its backing subtree is removed.

WHEN `immutableConfigurationAt`, `immutableConfigurationsAt`, or `immutableChildConfigurationsAt` is used, THEN the returned projections must expose the same selected values without mutable configuration operations.

WHEN `clearTree(key)` is called, THEN the hierarchical configuration must remove the selected property and every descendant under that property.

## Interpolation and Lookup Resolution

Interpolation resolves variable references dynamically while preserving a raw property projection.

**Configuration-level interpolation.**

Every `AbstractConfiguration` instance must install an interpolator whose default lookup resolves unprefixed variables against properties of that configuration.

WHEN a typed property getter reads a string containing `${name}`, THEN the configuration must resolve `name` dynamically against current configuration state.

WHEN the referenced property changes, THEN a later typed read of the referencing property must reflect the new referenced value without rewriting the raw referencing property.

The `getProperty()` method must return the unresolved raw value, while typed string, scalar, list, and array getters must apply interpolation to their selected values.

WHEN `setInterpolator(null)` is called, THEN later typed reads must leave variable expressions unresolved.

WHEN `installInterpolator(prefixLookups, defaultLookups)` is called, THEN the configuration must install the supplied lookups and append a default lookup of its own property state.

WHEN `setInterpolator(interpolator)` is called with a non-null interpolator, THEN the configuration must use that object as supplied without inserting a configuration-state lookup.

**Lookup order and interpolation results.**

A prefixed variable must use the form `${prefix:name}`, with the first colon separating the lookup prefix from the name.

WHEN `resolve(var)` receives a prefixed variable name, THEN the interpolator must query the lookup registered for that prefix with the prefix removed.

WHEN the prefixed lookup is absent or returns `null`, THEN `resolve(var)` must query default lookups in registration order and return the first non-null result.

WHEN local prefix and default lookups do not resolve a variable and a parent interpolator exists, THEN `resolve(var)` must delegate to the parent; if no source resolves it, `resolve(var)` must return `null`.

WHEN `interpolate(value)` receives a non-string object, THEN it must return that same object unchanged.

WHEN an interpolated string consists of one variable expression and that variable resolves to a non-string object, THEN `interpolate` must return the raw resolved object.

WHEN a variable appears inside a larger string, THEN `interpolate` must convert the resolved value with the configured string converter and substitute the converted text.

WHERE the default string converter receives an iterable, iterator, or array for an embedded variable, it must use the first element as the string value; an empty container must contribute no value.

WHEN a variable remains unresolved during string interpolation, THEN its `${...}` expression must remain in the returned string.

**Lookup registration and exposed collections.**

WHEN `registerLookup(prefix, lookup)` is called with non-null arguments, THEN later resolution for that prefix must use the registered lookup.

IF `registerLookup` receives a null prefix or null lookup, THEN it must raise `IllegalArgumentException`.

WHEN `deregisterLookup(prefix)` is called, THEN it must return whether a mapping existed and remove an existing mapping.

Default lookups must be queried in insertion order, and `removeDefaultLookup(lookup)` must return whether the lookup existed.

The collections returned by `getLookups()` and `getDefaultLookups()` must be snapshots whose later modification does not alter the interpolator.

The `prefixSet()` result must be unmodifiable and must reflect the prefixes registered at the time it is observed.

WHERE substitution inside variable names is enabled through `setEnableSubstitutionInVariables(true)`, the interpolator must resolve nested expressions occurring in variable names.

## Layered and Hierarchical Composition

Composition exposes several child configurations as one projection with explicit ordering and rebuild rules.

**Flat composite precedence.**

A new `CompositeConfiguration` must contain an automatically created in-memory configuration used for writes.

WHEN ordinary child configurations are added with `addConfiguration`, THEN scalar lookup must inspect them in addition order and return the value from the first child containing the key.

WHEN `addConfigurationFirst(config)` is called, THEN the added configuration must become the highest-priority child for later reads.

The automatically created or constructor-supplied in-memory configuration must remain last in read order, and all writes through the composite must target that in-memory configuration.

WHEN an existing child is added with `asInMemory=true`, THEN it must become the write target and must retain the precedence position at which it was added.

WHEN `getProperty(key)` is called, THEN the composite must return the raw value from the first configuration containing the key.

WHEN `getList(key)` is called, THEN the composite must collect values from the first non-in-memory child containing the key and append values from the in-memory configuration.

The composite key iterator must return the ordered union of child keys, preserving the first occurrence of each key.

WHEN `removeConfiguration` receives the active in-memory configuration, THEN the composite must preserve it; another contained child must be removed.

WHEN `getSource(key)` finds exactly one defining child, THEN it must return that child; when no child defines the key, it must return `null`.

IF `getSource(key)` receives a null key or finds multiple defining children, THEN it must raise `IllegalArgumentException`.

**Hierarchical combination.**

A new `CombinedConfiguration` without an explicit combiner must use `UnionCombiner`.

WHEN `OverrideCombiner` combines children, THEN values and attributes from the earlier child must take precedence while later children must supply missing nodes, values, and attributes.

WHERE a node name is registered through `NodeCombiner.addListNode`, nodes with that name must remain separate instead of being combined.

WHEN `addConfiguration(config, name, at)` is called, THEN the combined view must register the child in addition order, expose a non-null unique `name` for lookup, and mount its properties beneath the dot-delimited `at` path when `at` is non-null.

IF a null child is added, THEN `CombinedConfiguration` must raise `IllegalArgumentException`.

IF a non-null child name duplicates an existing name, THEN `CombinedConfiguration` must raise `ConfigurationRuntimeException`.

WHEN a child configuration changes or `invalidate()` is called, THEN the combined configuration must mark its view stale, emit one `CombinedConfiguration.COMBINED_INVALIDATE` event after invalidation, and rebuild the view from current child state on the next property access.

WHEN a child is removed by object, name, or index, THEN the combined configuration must update its child, name, and source projections and invalidate the combined view.

Changes written directly to a combined view must remain temporary and must disappear when a later child change causes reconstruction unless the changed node belongs to and updates a child configuration.

WHEN `getSources(key)` is called, THEN it must return every child contributing the selected nodes, an empty set for an unknown key, or the combined configuration itself for directly owned nodes.

WHEN `getSource(key)` identifies exactly one source, THEN it must return that source; when no source exists, it must return `null`.

IF `getSource(key)` receives null or identifies multiple sources, THEN it must raise `IllegalArgumentException`.

IF `setNodeCombiner(null)` is called, THEN it must raise `IllegalArgumentException`; a non-null replacement must invalidate the existing combined view.

## Builder Lifecycle and Public Events

Builders and events expose creation, reset, mutation, and failure transitions without exposing internal storage.

**Managed builder results.**

A `BasicConfigurationBuilder` must accept a result configuration class and lazily create one managed instance.

WHEN `getConfiguration()` is called repeatedly without a result reset, THEN the builder must return the same managed object identity.

WHEN `resetResult()` is called, THEN the builder must discard the managed result and its current initialization declaration, and the next `getConfiguration()` call must create a different managed object.

WHEN `resetParameters()` is called, THEN the builder must remove initialization parameters without discarding an already managed result.

WHEN `reset()` is called, THEN the builder must clear initialization parameters and reset the managed result.

WHEN `setParameters(params)` is called, THEN it must replace the parameter map with a defensive copy; a null map must clear the parameters.

WHEN `addParameters(params)` is called, THEN it must merge non-null entries over existing entries and retain a defensive copy; a null map must leave parameters unchanged.

Parameter changes must apply when the next result is created and must not mutate an already managed result.

IF the builder result class is null, THEN construction must raise `IllegalArgumentException`.

IF result creation or initialization fails while `allowFailOnInit` is false, THEN `getConfiguration()` must raise `ConfigurationException`.

WHERE `allowFailOnInit` is true, an initialization `ConfigurationException` must be suppressed and the newly created result object must be returned.

**Builder events and listener propagation.**

WHEN `getConfiguration()` is entered, THEN the builder must emit `ConfigurationBuilderEvent.CONFIGURATION_REQUEST` before accessing or creating its managed result.

WHEN `getConfiguration()` creates a result, THEN the builder must emit exactly one `ConfigurationBuilderResultCreatedEvent.RESULT_CREATED` carrying that result; reuse of an existing result must not emit this event.

WHEN `resetResult()` is called, THEN the builder must emit one `ConfigurationBuilderEvent.RESET`, including when no managed result existed.

WHEN a listener is registered on a builder, THEN the builder must retain the registration and register compatible configuration-event listeners on each managed result it creates.

WHEN a builder result is reset, THEN listeners propagated by that builder must be removed from the obsolete result before a replacement is exposed.

WHEN `removeEventListener(eventType, listener)` matches a registration, THEN it must remove the registration and return `true`; an absent registration must return `false`.

**Configuration update and error events.**

Event types must form an identity-based parent hierarchy in which a listener registered for a base type receives events of that type and all descendant types.

WHEN `addProperty`, `setProperty`, `clearProperty`, or `clear` changes an `AbstractConfiguration`, THEN the configuration must emit a matching `ConfigurationEvent` before the operation and another matching event after the operation.

The before event must report `isBeforeUpdate()` as `true`, and the after event must report it as `false`.

The `ADD_PROPERTY` and `SET_PROPERTY` events must carry the affected property name and supplied value; `CLEAR_PROPERTY` must carry the property name and a null value; `CLEAR` must carry a null property name and null value.

WHEN detailed events are suppressed during a compound public operation, THEN listeners must receive the public operation's event pair without duplicate nested mutation event pairs.

A `ConfigurationErrorEvent` must expose its cause, the affected property name and value, and the failed operation event type through `getErrorOperationType()`, which must return the operation event type supplied at construction; `READ` and `WRITE` must remain descendants of `ConfigurationErrorEvent.ANY`.

IF an event is constructed with a null source or null event type, THEN construction must raise `IllegalArgumentException`.

IF an event listener registration receives a null event type or listener, THEN registration must raise `IllegalArgumentException`.

## State Model

The core state is a collection of distinct property keys mapped to raw scalar or ordered multi-values. Composition adds an ordered set of child configurations, builders add a current result identity and initialization parameters, and event sources add typed listener registrations.

The public projections must be:

1. Raw state through `getProperty`, `getKeys`, `entrySet`, `size`, and `containsKey` containment queries.
2. Converted state through typed scalar, collection, list, array, and encoded-string getters.
3. Prefix and tree regions through subsets and hierarchical sub-configurations.
4. Resolved state through `ConfigurationInterpolator` and typed configuration reads.
5. Layered state through composite and combined source, precedence, child, and name queries.
6. Lifecycle state through builder result identity, reset operations, and event streams.

WHEN a mutation succeeds, THEN every affected projection must reflect the same resulting state according to its view rules.

IF a mutation or selection fails with a specified exception, THEN the prior configuration, composition, or builder state must remain observable except for events explicitly documented as occurring before an attempted update.

## Error Semantics

| Condition | Required result |
|---|---|
| A present value is incompatible with a requested type | The typed getter must raise `ConversionException`. |
| A primitive getter reads a missing key without a supplied default | The getter must raise `NoSuchElementException`. |
| Strict missing-value mode is active and an object getter reads a missing key without a supplied default | The getter must raise `NoSuchElementException`. |
| `getEncodedString(key)` has no configured decoder | The method must raise `IllegalStateException`. |
| An explicit decoder, interpolation prefix, interpolation lookup, event type, event listener, combined child, node combiner, event source, or builder result class violates a documented non-null requirement | The receiving operation must raise `IllegalArgumentException`, except a null `SubsetConfiguration` parent must raise `NullPointerException`. |
| `configurationAt` selects zero or multiple nodes | The method must raise `ConfigurationRuntimeException`. |
| A combined child name duplicates an existing non-null name | The add operation must raise `ConfigurationRuntimeException`. |
| `getSource` receives null or identifies multiple defining sources | The method must raise `IllegalArgumentException`. |
| Builder creation or initialization fails while failure suppression is disabled | `getConfiguration()` must raise `ConfigurationException`. |

## Cross-View Invariants

1. A value written through a subset must be returned through the translated parent key, and a value written through the selected parent prefix must be returned through the subset key.
2. A raw variable expression returned by `getProperty()` must resolve through typed getters using the current interpolator and current referenced property state.
3. A key removed through `clearProperty()` or `clearTree()` must disappear from raw lookup, typed lookup, key iteration, size, relevant subsets, and relevant hierarchical views.
4. The first child selected by composite precedence must agree with `getProperty()`, typed scalar getters, and ordered key iteration; `getSource()` must return it only when it is the unique defining child.
5. A connected hierarchical sub-configuration must exchange updates with its parent until detachment, while an independent sub-configuration must preserve its own snapshot across parent changes.
6. A child change observed by `CombinedConfiguration` must produce invalidation and make the next combined read agree with current child state and the configured `NodeCombiner`.
7. A builder must return one stable result identity between resets, and each newly exposed identity must correspond to one `RESULT_CREATED` event.
8. A successful configuration mutation must produce matching before and after events whose property payload agrees with the state visible before and after the operation.

## Public Interface

### Import Surface

```java
import org.apache.commons.configuration2.AbstractConfiguration;
import org.apache.commons.configuration2.BaseConfiguration;
import org.apache.commons.configuration2.BaseHierarchicalConfiguration;
import org.apache.commons.configuration2.CombinedConfiguration;
import org.apache.commons.configuration2.CompositeConfiguration;
import org.apache.commons.configuration2.Configuration;
import org.apache.commons.configuration2.ConfigurationDecoder;
import org.apache.commons.configuration2.HierarchicalConfiguration;
import org.apache.commons.configuration2.ImmutableConfiguration;
import org.apache.commons.configuration2.ImmutableHierarchicalConfiguration;
import org.apache.commons.configuration2.SubsetConfiguration;
```

```java
import org.apache.commons.configuration2.builder.BasicConfigurationBuilder;
import org.apache.commons.configuration2.builder.BuilderParameters;
import org.apache.commons.configuration2.builder.ConfigurationBuilder;
import org.apache.commons.configuration2.builder.ConfigurationBuilderEvent;
import org.apache.commons.configuration2.builder.ConfigurationBuilderResultCreatedEvent;
```

```java
import org.apache.commons.configuration2.event.ConfigurationErrorEvent;
import org.apache.commons.configuration2.event.ConfigurationEvent;
import org.apache.commons.configuration2.event.Event;
import org.apache.commons.configuration2.event.EventListener;
import org.apache.commons.configuration2.event.EventSource;
import org.apache.commons.configuration2.event.EventType;
```

```java
import org.apache.commons.configuration2.interpol.ConfigurationInterpolator;
import org.apache.commons.configuration2.interpol.Lookup;
```

```java
import org.apache.commons.configuration2.convert.DefaultListDelimiterHandler;
import org.apache.commons.configuration2.convert.DisabledListDelimiterHandler;
import org.apache.commons.configuration2.convert.ListDelimiterHandler;
```

```java
import org.apache.commons.configuration2.ex.ConfigurationException;
import org.apache.commons.configuration2.ex.ConfigurationRuntimeException;
import org.apache.commons.configuration2.ex.ConversionException;
```

```java
import org.apache.commons.configuration2.tree.ImmutableNode;
import org.apache.commons.configuration2.tree.NodeCombiner;
import org.apache.commons.configuration2.tree.OverrideCombiner;
import org.apache.commons.configuration2.tree.UnionCombiner;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `ImmutableConfiguration` | interface | Defines read-only raw, typed, collection, enumeration, and subset projections. |
| `Configuration` | interface | Adds property mutation, interpolator control, and mutable subsets. |
| `AbstractConfiguration` | abstract class | Supplies shared typed conversion, interpolation, list handling, missing-value policy, and update events. |
| `BaseConfiguration` | class | Stores mutable in-memory key and ordered multi-value state. |
| `ConfigurationDecoder` | interface | Decodes values requested through encoded-string access. |
| `SubsetConfiguration` | class | Provides a live prefix-translating decorator over a parent configuration. |
| `ImmutableHierarchicalConfiguration` | interface | Defines read-only tree selection and subtree projections. |
| `HierarchicalConfiguration` | interface | Adds mutable, optionally connected hierarchical projections. |
| `BaseHierarchicalConfiguration` | class | Provides the scoped in-memory hierarchical configuration. |
| `ConfigurationInterpolator` | class | Resolves variables through prefix, default, and parent lookups. |
| `Lookup` | interface | Maps a variable name to a resolved object. |
| `CompositeConfiguration` | class | Layers flat child configurations using ordered first-match precedence and an in-memory write target. |
| `CombinedConfiguration` | class | Builds an invalidatable hierarchical view over named or mounted child configurations. |
| `NodeCombiner` | abstract class | Defines hierarchical combination and list-node declarations. |
| `OverrideCombiner` | class | Applies earlier-child precedence while filling missing structure from later children. |
| `UnionCombiner` | class | Supplies the default union strategy for combined configurations. |
| `ImmutableNode` | class | Serves as the public node type used by in-memory hierarchical configurations and combiners. |
| `ConfigurationBuilder` | interface | Exposes managed configuration acquisition and listener registration. |
| `BasicConfigurationBuilder` | class | Lazily creates, initializes, caches, resets, and announces one managed result. |
| `BuilderParameters` | interface | Supplies public initialization parameter maps to builders. |
| `ConfigurationBuilderEvent` | class | Reports builder request and reset transitions. |
| `ConfigurationBuilderResultCreatedEvent` | class | Reports a newly created managed configuration and carries its identity. |
| `Event` | class | Carries a source and hierarchical event type. |
| `EventType` | class | Represents an event filter and its parent type. |
| `EventSource` | interface | Registers and removes typed listeners. |
| `EventListener` | interface | Receives matching typed events. |
| `ConfigurationEvent` | class | Reports property and hierarchical configuration updates. |
| `ConfigurationErrorEvent` | class | Reports configuration access failures and their causes. |
| `ListDelimiterHandler` | interface | Defines how written values are expanded into list elements. |
| `DisabledListDelimiterHandler` | class | Preserves string values without delimiter splitting. |
| `DefaultListDelimiterHandler` | class | Splits written strings using one configured delimiter. |
| `ConversionException` | exception | Reports incompatible typed property conversion. |
| `ConfigurationException` | exception | Reports checked configuration creation or initialization failure. |
| `ConfigurationRuntimeException` | exception | Reports public configuration failures that use unchecked semantics. |

### CLI Entry Points

There is no console script for this package. There is no supported executable JAR entry point. Programmatic use is through Java imports.

## Appendix A: Environment

The working environment runs JDK 17 on Linux without network access, and source must remain compatible with Java 8 language and bytecode targets. Maven and the Java standard library are available. The scoped offline dependency set includes `org.apache.commons:commons-lang3:3.20.0`, `org.apache.commons:commons-text:1.15.0`, `commons-logging:commons-logging:1.4.0`, and `commons-beanutils:commons-beanutils:1.11.0`. The assessment environment provides the same JDK and staged dependency policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.apache.commons:commons-configuration2`. Source must compile through the standard Maven lifecycle using only locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises public construction and method calls across property mutation, typed conversion, missing-value handling, list projection, subsets, hierarchical connection and detachment, lookup ordering, interpolation, composite and combined precedence, builder identity and reset, and event filtering and payloads.

Checks compare observable values, object identity where lifecycle semantics require it, exception classes, event sequences, and consistency across public projections. They do not require private field layout, exact messages, diagnostic formatting, file or network integration, or a particular locking or tree-storage algorithm. Results reflect independently passing behavior cases, with integration cases covering complete state transitions across multiple views.
