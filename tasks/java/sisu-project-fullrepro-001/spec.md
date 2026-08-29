# Qualified Component Runtime Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`org.eclipse.sisu.inject` is a JSR-330 container extension that discovers qualified classes, turns them into Guice bindings, locates ranked beans across injectors, completes unresolved wiring, and runs opt-in bean lifecycle callbacks. The retained artifact combines four public projections of the same component graph: class-space discovery, injector bindings, locator results and watcher events, and injected objects.

The installable Maven coordinate is `org.eclipse.sisu:org.eclipse.sisu.inject`. Guice supplies the underlying injector and binding model; this library supplies annotation-driven discovery, dynamic lookup, collection wiring, parameter aggregation, and lifecycle integration.

## Non-Goals

- This specification does not require the companion Plexus adapter artifact or any `org.codehaus.plexus` compatibility API.
- This specification does not require OSGi bundle integration, Eclipse extenders, Maven mojos, Peaberry leftovers, or launcher and injected-test support.
- This specification does not require low-level ASM visitor APIs, class-file event callbacks, resource globbing utilities, weak-reference collection utilities, or legacy `org.sonatype.inject` aliases.
- This specification does not require custom bean-property injection through `BeanBinder`, `PropertyBinder`, or reflective member iteration.
- This specification does not define private field layout, cache structures, thread scheduling algorithms, exact logging text, or exact `toString()` output.
- This specification does not require network services or runtime classpath downloads.

## Representative Workflows

### Discover and inject a named component

```java
import com.google.inject.Guice;
import com.google.inject.Injector;
import javax.inject.Named;
import org.eclipse.sisu.space.BeanScanning;
import org.eclipse.sisu.space.SpaceModule;
import org.eclipse.sisu.space.URLClassSpace;
import org.eclipse.sisu.wire.WireModule;

@Named("friendly")
final class FriendlyGreeting implements Greeting {
    public String text() { return "hello"; }
}

ClassLoader loader = FriendlyGreeting.class.getClassLoader();
SpaceModule discovered = new SpaceModule(new URLClassSpace(loader), BeanScanning.ON, true);
Injector injector = Guice.createInjector(new WireModule(discovered));
Greeting greeting = injector.getInstance(Greeting.class);
```

The class space supplies candidate bytecode, the space module binds the qualified implementation, and the wire module resolves the unqualified interface request to the default discovered component. If scanning cannot read a candidate in strict mode, injector creation must fail instead of silently producing a partial graph.

### Locate beans across live publishers

```java
import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.name.Named;
import org.eclipse.sisu.BeanEntry;
import org.eclipse.sisu.inject.DefaultBeanLocator;
import org.eclipse.sisu.inject.InjectorBindings;

DefaultBeanLocator locator = new DefaultBeanLocator();
Injector injector = Guice.createInjector(new GreetingModule());
InjectorBindings publisher = new InjectorBindings(injector);
locator.add(publisher);

Iterable<? extends BeanEntry<Named, Greeting>> entries =
    locator.locate(Key.get(Greeting.class, Named.class));

locator.remove(publisher);
```

The located iterable must present matching entries in descending rank order. An iterable obtained before a publisher change must reflect later additions and removals, while each entry must preserve its qualifier, provider, description, source, and rank projections.

### Run managed lifecycle callbacks

```java
import com.google.inject.Guice;
import com.google.inject.Injector;
import org.eclipse.sisu.PostConstruct;
import org.eclipse.sisu.PreDestroy;
import org.eclipse.sisu.bean.BeanManager;
import org.eclipse.sisu.bean.LifecycleModule;

final class ManagedService {
    boolean started;
    boolean stopped;

    @PostConstruct void start() { started = true; }
    @PreDestroy void stop() { stopped = true; }
}

Injector injector = Guice.createInjector(new LifecycleModule());
ManagedService service = injector.getInstance(ManagedService.class);
BeanManager manager = injector.getInstance(BeanManager.class);
manager.unmanage(service);
```

Injection must invoke the post-construction callback before the instance is returned for use. Explicit unmanagement must invoke the destruction callback once for that managed instance.

## Component Discovery and Binding

Component discovery turns class-space content or a named index into Guice bindings, which removes the need for explicit bindings for qualified implementation types.

**Scanning selection.** The `BeanScanning` values are `ON`, `OFF`, `CACHE`, `INDEX`, and `GLOBAL_INDEX`. When `BeanScanning.select(properties)` finds no value or a blank value under the key `org.eclipse.sisu.space.BeanScanning`, it must return `ON`. When the property has a nonblank value, selection must ignore letter case and return the matching enum value. If the value names no enum member, then selection must raise `IllegalArgumentException`.

When a `SpaceModule` receives `OFF`, it must bind its `ClassSpace` without scanning components. When it receives `ON`, it must scan the local class path. When it receives `CACHE`, it must scan once per class-space identity and replay equivalent binding elements for later modules. When it receives `INDEX`, it must read local `META-INF/sisu/javax.inject.Named` resources. When it receives `GLOBAL_INDEX`, it must read every matching named-index resource visible through the class space.

**Qualified types.** When scanning encounters a concrete class carrying `@Named` or another runtime `@Qualifier`, `SpaceModule` must make that class available through a compatible qualified lookup. When `@Named` has an explicit value, that value must be the bean name. When `@Named` is empty or a different qualifier is used, discovery must derive a stable canonical name from the implementation type.

When a qualified component uses `@Typed` with explicit classes, its discovered visibility must be restricted to those classes. When `@Typed` has an empty value, visibility must be restricted to the implementation's declared interfaces. When `@Typed` is absent, the wildcard binding must remain discoverable by compatible supertypes. If a qualified type carries `@Hidden`, then locator publication must omit it.

When a component is explicitly named `default` or its implementation simple name begins with `Default`, discovery must expose it as the unqualified default binding and rank it ahead of ordinary non-default components. When a component carries `@Priority`, the annotation value must determine its locator rank. When a component carries `@Description`, its `BeanEntry.getDescription()` result must equal the annotation value.

When a discovered component carries `@EagerSingleton`, injector creation must instantiate and inject that component before ordinary lazy lookup. If eager construction fails, then injector creation must propagate the corresponding Guice creation failure.

The component annotations must be retained at runtime. `Description`, `EagerSingleton`, `Hidden`, `Priority`, and `Typed` must target component types; `Dynamic` must target injection fields and parameters; `Parameters` must target injection fields, parameters, and provider methods; `PostConstruct` and `PreDestroy` must target lifecycle methods. `Dynamic` and `Parameters` must act as JSR-330 qualifiers.

**Providers, modules, and mediators.** When a discovered qualified class implements either the JSR-330 or Guice provider interface, discovery must bind the provider's produced type using the same naming and typing rules as components. When such a provider carries `@Singleton`, the produced binding must reuse one instance for that binding. If provider creation or provision fails, then Guice provisioning must propagate the corresponding runtime provisioning failure.

When a discovered qualified class implements Guice `Module`, discovery must install that module into the current binder. When a discovered qualified class implements `Mediator`, discovery must register it with the bean locator; the mediator class must have a public no-argument constructor and must act as a stateless translator.

**Class spaces and indices.** A `URLClassSpace` must load classes through its associated class loader and must return resources through that loader. When `loadClass(name)` cannot load or link the named class, it must raise `TypeNotPresentException`. When `getResources(name)` encounters an I/O failure, it must return an empty enumeration. The `getURLs()` result must be a defensive copy of the effective class path.

Calling `ClassSpace.getResource(name)` must return the first visible resource URL or `null` when none exists. Calling `ClassSpace.getResources(name)` must return every visible resource URL. Calling `findEntries(path, glob, recurse)` must restrict matching to the initial `path`, apply the filename `glob`, and descend into subdirectories only when `recurse` is `true`.

Calling `deferLoadClass(name)` must return a `DeferredClass` whose `getName()` equals `name` without eagerly loading the class. Calling `DeferredClass.load()` must perform class loading and return the class or raise `TypeNotPresentException`. Calling `asProvider()` must return a `DeferredProvider` for the same deferred implementation class. When the deferred provider is injected and `get()` is called, it must obtain an instance of the loaded class from that injector; a loading or provisioning failure must propagate as a runtime failure.

When an `IndexedClassFinder` reads index resources, it must accept UTF-8 class names separated by `\n`, `\r`, or `\r\n`, trim surrounding whitespace, ignore blank lines and full-line comments, strip trailing `#` comments, and remove duplicate names while preserving first-seen order. When an indexed class resource is absent, `findClasses(space)` must skip that name. If no further class resource exists, then `nextElement()` must raise `NoSuchElementException`.

**Strictness and customization.** When the `isStrict` constructor argument is `false`, an unreadable or malformed class must be skipped and scanning must continue. When `isStrict` is `true`, the same scan failure must raise a runtime exception. Calling `SpaceModule.with(strategy)` must replace the visitor strategy and return the same module as a Guice `Module`; a null strategy must fail when configuration attempts to use it.

## Dynamic Location and Ranking

Dynamic location projects bindings from zero or more publishers as ordered bean entries and sends matching changes to live watchers.

**Lookup projection.** Calling `BeanLocator.locate(key)` must return an iterable of `BeanEntry` values whose binding type and qualifier match the Guice `Key`. If no publisher contributes a match, then iteration must be empty. Each entry's `getKey()` must return its qualifier, `getValue()` must lazily obtain and then reuse the same value for that entry, and `getProvider()` must expose the underlying provider. Each entry must expose its description, implementation class when determinable, binding source, and numeric rank without forcing value creation solely to determine metadata.

When no `@Description` is associated with a binding, `BeanEntry.getDescription()` must return `null`. When the implementation class cannot be determined without provisioning, `getImplementationClass()` must return `null`. Calling the inherited `setValue(value)` mutation must raise `UnsupportedOperationException`.

Located entries must be ordered from higher rank to lower rank. When two publishers or bindings have equal rank, their stable publication sequence must break the tie. A previously returned iterable must reflect later publisher additions and removals.

**Publisher lifecycle.** When `MutableBeanLocator.add(publisher)` receives a publisher not already registered, it must return `true`, include the publisher in `publishers()`, expose its matching bindings to existing located iterables, and subscribe existing watchers. When the same publisher is added again, it must return `false` without duplicating entries or events.

When `MutableBeanLocator.remove(publisher)` removes a registered publisher, it must return `true`, withdraw that publisher's bindings from located iterables, and deliver removal events to existing watchers. When the publisher is unknown, removal must return `false` without changing state. Calling `clear()` must remove every registered publisher and binding; calling it on an empty locator must leave an empty usable locator.

**Watcher delivery.** Calling `BeanLocator.watch(key, mediator, watcher)` must subscribe the mediator to current and future matching bindings while the watcher remains live. When a matching binding is added and at least one live watcher exists, `Mediator.add(entry, watcher)` must receive the addition. When that binding is removed, `Mediator.remove(entry, watcher)` must receive the removal. If no live watcher has requested the watcher type, then mediation must not create one solely to deliver events.

**Ranking.** A no-argument `DefaultRankingFunction` must use zero as its primary rank. A `DefaultRankingFunction(primaryRank)` must use the supplied nonnegative primary rank. If `primaryRank` is negative, then construction must raise `IllegalArgumentException`. A binding with `@Priority` must receive that explicit value; an unqualified default binding without explicit priority must receive the primary rank; another qualified binding without explicit priority must receive the corresponding negative rank partition. `maxRank()` must return `Integer.MAX_VALUE`.

**Injector publication.** An `InjectorBindings` created for an injector must publish exact type matches, compatible generic matches, and compatible wildcard component bindings while excluding `@Hidden` bindings. `adapt(Injector.class)` must return the wrapped injector, and adapting to another type must return `null`. `findBindingPublisher(injector)` must prefer an explicit publisher binding and otherwise return an injector-backed publisher. `findRankingFunction(injector)` must prefer an explicit ranking-function binding and otherwise return the default ranking function.

When a `DefaultBeanLocator` is bound directly in an injector, Guice member injection must publish that injector automatically. Binding the same locator behind a provider must suppress automatic publication. Calling `setBeanEntryPredicateSupplier(supplier)` with a non-null supplier must filter subsequent located entry views through predicates returned by that supplier; passing `null` must remove this filtering.

## Automatic Wiring and Parameters

Automatic wiring fills unresolved Guice dependencies from the bean locator and provides live collection views over the same ranked component graph.

**Module composition.** A `WireModule` must analyze all enclosed modules as one binding set and preserve their explicit bindings. When an unresolved request is supported by locator wiring, the module must synthesize the missing binding from the locator. Calling `WireModule.with(strategy)` must replace the wiring strategy and return the same module as a Guice `Module`; a null strategy must fail when configuration attempts to use it.

A `ChildWireModule` must ignore keys already available from its parent injector, analyze only unresolved child dependencies, and publish the child injector to an inherited default locator. Calling `ChildWireModule.with(strategy)` must apply the same strategy contract as `WireModule.with(strategy)`.

**Single values and providers.** When an unresolved dependency requests an unqualified component type, wiring must select the highest-ranked compatible default bean. When it requests `@Named("name")` or another runtime qualifier, wiring must select a compatible bean with that qualifier. When it requests `Provider<T>`, wiring must preserve lazy provider access rather than eagerly create `T`. If no compatible bean satisfies a required single-valued dependency, then injector creation or provisioning must raise Guice's missing-binding configuration failure.

When an unresolved interface or non-final class dependency carries `@Dynamic`, wiring must inject a proxy that delegates each ordinary method call to the currently highest-ranked compatible bean. When publisher changes alter the highest-ranked compatible bean, an existing dynamic proxy must redirect later calls to the new selection. If no compatible bean exists when an ordinary method is invoked, then the proxy must raise `IllegalStateException`.

**Dynamic collections.** When an unresolved dependency requests `List<T>`, `List<Provider<T>>`, or `Iterable<BeanEntry<Q,T>>`, wiring must supply a thread-safe, rank-ordered, dynamic view. The view must reflect publishers added or removed after injection. Values must be created lazily on access and reused within the same injected collection view.

When an unresolved dependency requests `Map<String,T>` or `Map<String,Provider<T>>`, map keys must come from `@Named` values. When it requests `Map<Q,T>` for another qualifier annotation type, keys must be the qualifier annotation instances. If multiple visible entries have the same map key, then the highest-ranked entry must determine the map value while the full `BeanEntry` iterable must retain all distinct entries.

**Application parameters.** `ParameterKeys.PROPERTIES` must equal the Guice key for `Map` qualified by `@Parameters`, and `ParameterKeys.ARGUMENTS` must equal the key for `String[]` qualified by `@Parameters`. When no parameter maps or arrays are bound, wiring must provide an empty map and an empty string array. When multiple `@Parameters` maps are bound, the injected map must be an aggregate view over their entries. When multiple `@Parameters` arrays are bound, the injected array must append their elements in module binding order.

**Property placeholders and conversion.** When a `@Named` string uses `${property}`, wiring must resolve the name through the merged parameter map. When it uses `${property:-fallback}` and the property is absent, wiring must use `fallback`. A plain `@Named("property")` request for a scalar convertible type must use the property of that name. Resolved strings must support Guice's installed conversion plus built-in conversion to `File`, `Path`, and `URL`. If a required placeholder is unresolved or conversion fails, then provisioning must raise a Guice configuration or provisioning exception.

## Managed Bean Lifecycle

Managed lifecycle support connects post-construction and pre-destruction annotations to Guice injection and explicit unmanagement.

**Activation.** A `LifecycleModule` created without arguments must install a new `LifecycleManager`; a module created with `manager` must bind that exact `BeanManager` instance. When an injected bean type has an `org.eclipse.sisu.PostConstruct` or available JSR-250 `PostConstruct` method, the manager must invoke the callback after dependency injection and before the bean is put into service. A bean type without lifecycle methods must not be scheduled for lifecycle work.

**Deactivation.** When a managed bean has an `org.eclipse.sisu.PreDestroy` or available JSR-250 `PreDestroy` method, the manager must remember it for explicit shutdown. Calling `unmanage(bean)` must invoke that bean's destruction callback when the bean is currently managed and must return `true`. Calling `unmanage()` must invoke destruction callbacks for all remembered beans in reverse management order and must return `true`. Calling either unmanagement form for an unknown or already-unmanaged bean must not invoke a callback twice.

**Manager SPI.** `BeanManager.manage(clazz)` must return whether instances of the class require manager reporting. `BeanManager.manage(property)` must return a `PropertyBinding` when the manager handles that property and `null` otherwise. `BeanManager.manage(bean)` must register and activate the supplied instance according to its known lifecycle and return whether it was handled. `LifecycleManager.manage(property)` must return `null` because lifecycle management does not define custom property bindings.

A `BeanProperty` must expose its annotation lookup, reified Guice type, normalized name, and `set(bean, value)` mutation. Calling `PropertyBinding.injectProperty(bean)` must apply that binding's current value to the represented bean property. If property mutation fails, then the surrounding injection must propagate a runtime provisioning failure.

Calling `LifecycleManager.flushCacheFor(tester)` must remove cached lifecycle descriptions for every class for which `tester.shouldFlush(clazz)` returns `true`. If a lifecycle callback throws, then the surrounding injection, management, or unmanagement operation must propagate a runtime failure instead of reporting successful completion.

## State Model

The core state is a dynamic component graph. Each component fact combines an implementation type, qualifier, provider, rank, description, source, visibility restriction, and owning publisher. The public projections are:

1. `SpaceModule` discovery and the Guice bindings installed for qualified components, providers, modules, and mediators.
2. `BeanLocator` iterables and `BeanEntry` metadata ordered across all registered publishers.
3. Watcher callbacks delivered by `Mediator` as matching bindings enter and leave the graph.
4. Values, providers, lists, maps, and parameter aggregates injected by `WireModule` or `ChildWireModule`.
5. Lifecycle state projected through post-construction callbacks, `BeanManager`, and pre-destruction callbacks.

Adding or removing a publisher must transition all live locator, watcher, and wired-collection projections to the same graph membership. Discovery and ranking metadata must remain stable for a binding until its publisher is removed.

## Error Semantics

| Condition | Required result |
|---|---|
| `BeanScanning.select` receives an unknown nonblank option | Raise `IllegalArgumentException` |
| `DefaultRankingFunction` receives a negative primary rank | Raise `IllegalArgumentException` |
| `URLClassSpace.loadClass` cannot load or link the named class | Raise `TypeNotPresentException` |
| Strict scanning encounters unreadable or malformed bytecode | Raise a runtime exception |
| Lenient scanning encounters unreadable or malformed bytecode | Skip the affected class and continue |
| An indexed enumeration has no next class resource | Raise `NoSuchElementException` |
| A required single-valued dependency has no compatible bean | Raise Guice's missing-binding configuration failure |
| A required property placeholder is unresolved or conversion fails | Raise a Guice configuration or provisioning exception |
| A provider or lifecycle callback fails | Propagate a runtime provisioning or lifecycle failure |
| Removing an unknown publisher | Return `false` without changing locator state |

## Cross-View Invariants

1. A qualified class discovered by `SpaceModule` must appear as a compatible Guice binding and as a matching `BeanEntry` after its injector is published to a locator.
2. A bean's qualifier, description, implementation class, source, and rank in `BeanEntry` must describe the same binding that supplies `getProvider()` and `getValue()`.
3. Rank ordering in a locator iterable must agree with the selected value for an unresolved single injection and with ordering in an injected list.
4. Adding a publisher must add the same matching component to existing locator iterables, watcher callbacks, and dynamic injected collections; removing it must withdraw the component from all three projections.
5. A class hidden with `@Hidden` must be absent from injector publication, locator results, watcher events, and locator-backed collection wiring.
6. A `@Typed` visibility restriction must agree across discovered Guice keys, locator compatibility checks, and injected collection element types.
7. Named-index discovery and full scanning over the same qualified classes must produce equivalent qualifiers, compatible types, descriptions, and ranks.
8. A property selected from merged `@Parameters` maps must agree with placeholder resolution and with the value exposed through `ParameterKeys.PROPERTIES`.
9. A bean returned after lifecycle-enabled injection must already reflect its post-construction callback, and its explicit unmanagement must later reflect exactly one pre-destruction callback.
10. A child injector wired through `ChildWireModule` must preserve parent bindings while publishing only the child's additional graph facts to the inherited locator.

## Public Interface

### Import Surface

```java
import org.eclipse.sisu.BeanEntry;
import org.eclipse.sisu.Description;
import org.eclipse.sisu.Dynamic;
import org.eclipse.sisu.EagerSingleton;
import org.eclipse.sisu.Hidden;
import org.eclipse.sisu.Mediator;
import org.eclipse.sisu.Parameters;
import org.eclipse.sisu.PostConstruct;
import org.eclipse.sisu.PreDestroy;
import org.eclipse.sisu.Priority;
import org.eclipse.sisu.Typed;
```

```java
import org.eclipse.sisu.inject.BeanLocator;
import org.eclipse.sisu.inject.BindingPublisher;
import org.eclipse.sisu.inject.BindingSubscriber;
import org.eclipse.sisu.inject.DefaultBeanLocator;
import org.eclipse.sisu.inject.DefaultRankingFunction;
import org.eclipse.sisu.inject.DeferredClass;
import org.eclipse.sisu.inject.DeferredProvider;
import org.eclipse.sisu.inject.InjectorBindings;
import org.eclipse.sisu.inject.MutableBeanLocator;
import org.eclipse.sisu.inject.RankingFunction;
```

```java
import org.eclipse.sisu.space.BeanScanning;
import org.eclipse.sisu.space.ClassFinder;
import org.eclipse.sisu.space.ClassSpace;
import org.eclipse.sisu.space.IndexedClassFinder;
import org.eclipse.sisu.space.SpaceModule;
import org.eclipse.sisu.space.URLClassSpace;
```

```java
import org.eclipse.sisu.wire.ChildWireModule;
import org.eclipse.sisu.wire.ParameterKeys;
import org.eclipse.sisu.wire.WireModule;
```

```java
import org.eclipse.sisu.bean.BeanProperty;
import org.eclipse.sisu.bean.BeanManager;
import org.eclipse.sisu.bean.LifecycleManager;
import org.eclipse.sisu.bean.LifecycleModule;
import org.eclipse.sisu.bean.PropertyBinding;
```

### Public Member Surface

| Type | Public members in the retained contract |
|---|---|
| `BeanEntry<Q,T>` | `getKey()`, `getValue()`, `setValue(T)`, `getProvider()`, `getDescription()`, `getImplementationClass()`, `getSource()`, `getRank()` |
| `Description` | `value()` |
| `Dynamic` | marker annotation |
| `EagerSingleton` | marker annotation |
| `Hidden` | marker annotation |
| `Mediator<Q,T,W>` | `add(BeanEntry<Q,T>, W)`, `remove(BeanEntry<Q,T>, W)` |
| `Parameters` | marker qualifier annotation |
| `PostConstruct` | marker method annotation |
| `PreDestroy` | marker method annotation |
| `Priority` | `value()` |
| `Typed` | `value()` |
| `BeanLocator` | `locate(Key<T>)`, `watch(Key<T>, Mediator<Q,T,W>, W)` |
| `MutableBeanLocator` | inherited locator members, `add(BindingPublisher)`, `remove(BindingPublisher)`, `publishers()`, `clear()` |
| `DefaultBeanLocator` | public no-argument constructor, locator members, `setBeanEntryPredicateSupplier(Supplier<Predicate>)` |
| `BindingPublisher` | `subscribe(BindingSubscriber<T>)`, `unsubscribe(BindingSubscriber<T>)`, `maxBindingRank()`, `adapt(Class<T>)` |
| `BindingSubscriber<T>` | `type()`, `add(Binding<T>, int)`, `remove(Binding<T>)`, `bindings()` |
| `RankingFunction` | `maxRank()`, `rank(Binding<T>)` |
| `DefaultRankingFunction` | no-argument constructor, constructor accepting `primaryRank`, ranking members |
| `DeferredClass<T>` | `load()`, `getName()`, `asProvider()` |
| `DeferredProvider<T>` | inherited `get()`, `getImplementationClass()` |
| `InjectorBindings` | constructors accepting `Injector` and optionally `RankingFunction`; `findBindingPublisher(Injector)`, `findRankingFunction(Injector)`, publisher members |
| `BeanScanning` | `ON`, `OFF`, `CACHE`, `INDEX`, `GLOBAL_INDEX`, `select(Map<?,?>)` |
| `ClassSpace` | `loadClass(String)`, `deferLoadClass(String)`, `getResource(String)`, `getResources(String)`, `findEntries(String,String,boolean)` |
| `URLClassSpace` | constructors accepting a `ClassLoader` and optionally a `URL[]`; class-space members; `getURLs()` |
| `ClassFinder` | `findClasses(ClassSpace)` |
| `IndexedClassFinder` | constructor accepting index `name` and `global`; `indexedNames(ClassSpace)`, `findClasses(ClassSpace)` |
| `SpaceModule` | `LOCAL_INDEX`, `GLOBAL_INDEX`, `LOCAL_SCAN`; constructors accepting `ClassSpace` with `ClassFinder` or `BeanScanning` and strictness; `with(SpaceModule.Strategy)`, `configure(Binder)` |
| `SpaceModule.Strategy` | `DEFAULT`, `DEFAULT_STRICT`, `visitor(Binder)` |
| `WireModule` | constructors accepting `Module...` or `Iterable<Module>`; `with(WireModule.Strategy)`, `configure(Binder)` |
| `WireModule.Strategy` | `DEFAULT`, `wiring(Binder)` |
| `ChildWireModule` | constructors accepting a parent `Injector` plus `Module...` or `Iterable<Module>`; `with(WireModule.Strategy)`, `configure(Binder)` |
| `ParameterKeys` | `PROPERTIES`, `ARGUMENTS` |
| `BeanProperty<T>` | `getAnnotation(Class<A>)`, `getType()`, `getName()`, `set(B,T)` |
| `PropertyBinding` | `injectProperty(B)` |
| `BeanManager` | `manage(Class<?>)`, `manage(BeanProperty<?>)`, `manage(Object)`, `unmanage(Object)`, `unmanage()` |
| `LifecycleManager` | public no-argument constructor; manager members; `flushCacheFor(ClassTester)` |
| `LifecycleManager.ClassTester` | `shouldFlush(Class<?>)` |
| `LifecycleModule` | no-argument constructor, constructor accepting `BeanManager`, `configure(Binder)` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `BeanEntry` | interface | Projects a qualified binding as lazy value and metadata |
| `Description` | annotation | Supplies human-readable bean metadata |
| `Dynamic` | annotation | Marks a dependency for dynamic proxy behavior |
| `EagerSingleton` | annotation | Marks a discovered bean for eager singleton creation |
| `Hidden` | annotation | Excludes a binding from locator visibility |
| `Mediator` | interface | Translates binding additions and removals to watcher updates |
| `Parameters` | annotation | Qualifies application argument arrays and property maps |
| `PostConstruct` | annotation | Marks an opt-in post-injection lifecycle callback |
| `PreDestroy` | annotation | Marks an opt-in pre-destruction lifecycle callback |
| `Priority` | annotation | Supplies an explicit binding rank |
| `Typed` | annotation | Restricts the public types of a discovered bean |
| `BeanLocator` | interface | Locates and watches qualified beans |
| `MutableBeanLocator` | interface | Adds and removes binding publishers dynamically |
| `DefaultBeanLocator` | class | Provides the standard dynamic locator implementation |
| `BindingPublisher` | interface | Publishes ranked Guice bindings |
| `BindingSubscriber` | interface | Receives matching ranked Guice bindings |
| `RankingFunction` | interface | Assigns numeric precedence to bindings |
| `DefaultRankingFunction` | class | Partitions default and non-default binding ranks |
| `DeferredClass` | interface | Defers loading of a named class |
| `DeferredProvider` | interface | Obtains injected instances backed by a deferred class |
| `InjectorBindings` | class | Publishes visible bindings from one injector |
| `BeanScanning` | enum | Selects full, cached, disabled, or indexed discovery |
| `ClassSpace` | interface | Abstracts related classes and resources |
| `URLClassSpace` | class | Implements class-space access over a class loader and URL path |
| `ClassFinder` | interface | Selects class resources from a class space |
| `IndexedClassFinder` | class | Reads class names from named-index resources |
| `SpaceModule` | class | Discovers and binds qualified types |
| `SpaceModule.Strategy` | interface | Selects the visitor used by a space module |
| `WireModule` | class | Synthesizes locator-backed unresolved bindings |
| `WireModule.Strategy` | interface | Selects unresolved-dependency wiring behavior |
| `ChildWireModule` | class | Wires child-only unresolved dependencies |
| `ParameterKeys` | interface | Provides canonical Guice keys for application parameters |
| `BeanProperty` | interface | Projects annotation, type, name, and mutation for a bean property |
| `PropertyBinding` | interface | Applies a bound value to a bean property |
| `BeanManager` | interface | Controls bean lifecycle reporting and shutdown |
| `LifecycleManager` | class | Runs and tracks lifecycle callbacks |
| `LifecycleManager.ClassTester` | interface | Selects cached lifecycle descriptions for removal |
| `LifecycleModule` | class | Installs lifecycle management into Guice |

### CLI Entry Points

There is no console script for this package. Programmatic use is through Java imports and Maven dependency resolution.

## Appendix A: Environment

The working environment runs JDK 17 on Linux with Maven and without network access. The local Maven dependency set contains Guice, `javax.inject`, ASM, and the standard annotation API needed by the retained contract. SLF4J and OSGi APIs are optional to the upstream artifact but are not required by the retained workflows. The assessment environment provides the same JDK and offline dependency set.

The project must provide a standard Maven `pom.xml` at its root and build the single coordinate `org.eclipse.sisu:org.eclipse.sisu.inject` as a JAR. Production bytecode must remain Java 8 compatible. Every runtime dependency required by the implementation must be declared in the POM and resolvable from the provided local Maven repository.

## Appendix B: Assessment Notes

Assessment exercises public Java imports, constructors, annotations, discovery modes, type visibility, provider and module handling, locator membership and ordering, watcher delivery, dynamic wiring, parameter aggregation, placeholder conversion, and lifecycle transitions. Checks compare observable return values, exception classes, callback events, binding metadata, and consistency across complete workflows. Private storage, low-level bytecode visitors, exact diagnostics, logging, OSGi adapters, and the companion Plexus artifact are not assessed. Results reflect independently passing public behavior cases, including integration cases that require multiple projections to remain consistent.
