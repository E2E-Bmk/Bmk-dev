# PF4J Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`org.pf4j:pf4j` is a Java plugin framework that discovers local plugin artifacts, materializes their descriptors, resolves inter-plugin dependencies, manages lifecycle state, isolates plugin classes, and exposes extension implementations to an application.

The framework accepts directory, JAR, and ZIP plugin layouts. Its shared registry is observable through manager queries, descriptor and dependency views, lifecycle events, class-loader ownership, status files, and extension lookup.

## Non-Goals

- This specification does not require downloading plugins, resolving Maven coordinates, or contacting remote services at runtime.
- This specification does not require concurrent use of one plugin manager; manager implementations are not thread-safe.
- This specification does not require deprecated wrappers, legacy extension finders, service-provider extension storage, or custom annotation-storage implementations.
- This specification does not require exact logging text, exact exception messages, object representations, or private registry layout.
- This specification does not define public contracts for `org.pf4j.asm`, general-purpose `org.pf4j.util` helpers, or extension-storage implementation classes.
- This specification does not require a command-line entry point.

## Representative Workflows

The first workflow loads mixed local artifacts, observes lifecycle changes, queries extensions, and releases every loaded plugin.

```java
Path plugins = Path.of("local-plugins");
PluginManager manager = new DefaultPluginManager(plugins);
List<PluginStateEvent> events = new ArrayList<>();
manager.addPluginStateListener(events::add);

manager.loadPlugins();
manager.startPlugins();

List<Greeting> greetings = manager.getExtensions(Greeting.class);
for (Greeting greeting : greetings) {
    System.out.println(greeting.text());
}

manager.stopPlugins();
manager.unloadPlugins();
```

The plugin root contains directory, JAR, or ZIP entries with descriptor metadata and extension indexes. This workflow demonstrates alignment among loaded wrappers, listener events, extension results, and class-loader queries.

The second workflow inspects dependency rules independently from plugin startup.

```java
DefaultPluginDescriptor base = new DefaultPluginDescriptor(
    "base", "Base services", Plugin.class.getName(), "2.1.0", "*", "provider", "Apache-2.0");
DefaultPluginDescriptor feature = new DefaultPluginDescriptor(
    "feature", "Feature services", Plugin.class.getName(), "1.0.0", "*", "provider", "Apache-2.0");
feature.addDependency(new PluginDependency("base@>=2.0.0 & <3.0.0"));

DependencyResolver resolver = new DependencyResolver(new DefaultVersionManager());
DependencyResolver.Result result = resolver.resolve(List.of(feature, base));
if (result.isOK()) {
    for (String pluginId : result.getSortedPlugins()) {
        System.out.println(pluginId);
    }
}
```

This workflow demonstrates dependency-first ordering and the resolver's missing, incompatible, and cyclic projections without loading plugin classes.

## Artifact Discovery and Descriptors

Artifact discovery defines how configured roots become validated plugin descriptors and registry entries.

**Manager roots and artifact selection.**

- A `DefaultPluginManager` must accept no root, one or more `Path` roots, or a `List<Path>` of roots.
- WHEN no root is supplied, THEN the manager must split the nonempty `pf4j.pluginsDir` system property on commas, trim each entry, and use the resulting paths in order.
- WHEN neither a root nor `pf4j.pluginsDir` is supplied, THEN the manager must use `plugins` in deployment mode and `../plugins` in development mode.
- `getPluginsRoots` must return an unmodifiable ordered view of every configured root, and `getPluginsRoot` must return the first root.
- IF no root exists when `getPluginsRoot` is called, THEN the manager must raise `IllegalStateException`.
- `DefaultPluginManager` must discover plugin directories, fat JAR files, and ZIP files immediately below every configured root.
- `JarPluginManager` must discover fat JAR plugins, and `ZipPluginManager` must discover ZIP or expanded-directory plugins.
- WHEN a ZIP plugin is selected, THEN the default manager must expand it to a sibling directory with the archive extension removed before descriptor and classpath loading.
- WHEN a configured root is missing or is not a directory, THEN bulk `loadPlugins` must treat that root as empty and continue with the other roots.

**Descriptor sources and fields.**

- `PluginDescriptorFinder.isApplicable` must report whether a finder accepts a supplied local path, and `find` must return its `PluginDescriptor` or raise `PluginRuntimeException` when the required descriptor resource is unreadable or absent.
- `ManifestPluginDescriptorFinder` must read `Plugin-Id`, `Plugin-Description`, `Plugin-Class`, `Plugin-Version`, `Plugin-Requires`, `Plugin-Dependencies`, `Plugin-Provider`, and `Plugin-License` from a JAR manifest, a ZIP `classes/META-INF/MANIFEST.MF`, or a directory manifest.
- `PropertiesPluginDescriptorFinder` must read `plugin.id`, `plugin.description`, `plugin.class`, `plugin.version`, `plugin.requires`, `plugin.dependencies`, `plugin.provider`, and `plugin.license` from `plugin.properties` at the plugin root.
- A `PropertiesPluginDescriptorFinder` constructed with `propertiesFileName` must use that file name instead of `plugin.properties`.
- A `DefaultPluginDescriptor` must expose `pluginId`, `pluginDescription`, `pluginClass`, `version`, `requires`, `provider`, `license`, and the ordered dependency list through its getters.
- WHEN either built-in finder sees optional descriptor text absent, THEN the descriptor must use an empty description, `org.pf4j.Plugin` as the plugin class, `*` as the application requirement, and an empty dependency list.
- IF a loaded descriptor has an empty plugin id or a null version, THEN the manager must raise `InvalidPluginDescriptorException`.

**Registry loading.**

- WHEN `loadPlugin` receives an existing applicable artifact, THEN it must load its descriptor and class loader, add a `PluginWrapper` to the registry, resolve the registry dependency graph, and return the descriptor plugin id.
- IF `loadPlugin` receives null or a nonexistent path, THEN it must raise `IllegalArgumentException`.
- IF a path is already loaded, THEN `loadPlugin` must raise `PluginAlreadyLoadedException` carrying the existing plugin id and path.
- IF another loaded artifact has the same descriptor plugin id, THEN `loadPlugin` must raise `PluginRuntimeException`.
- WHEN bulk `loadPlugins` encounters one artifact that raises `PluginRuntimeException` before dependency resolution, THEN it must skip that artifact and continue loading the remaining discovered artifacts.
- `getPlugins` must return a snapshot of all registered wrappers, `getPlugin(pluginId)` must return the matching wrapper, and `getPlugin(pluginId)` must return null for an unknown id.

## Dependency and Version Resolution

Dependency resolution converts descriptor declarations into ordering, compatibility, and failure projections.

**Dependency declarations.**

- A `PluginDependency` must parse `pluginId`, optional marker `?`, and version support separated by `@`.
- WHEN a dependency omits a version expression, THEN `getPluginVersionSupport` must return `*`.
- WHEN the plugin id ends in `?` before the optional version expression, THEN `isOptional` must return true and `getPluginId` must omit the marker.
- A descriptor must retain dependencies added through `addDependency` in insertion order.

**Resolver result.**

- WHEN `DependencyResolver.resolve` receives descriptors with satisfiable required dependencies, THEN `Result.getSortedPlugins` must list every plugin id with each required dependency before every dependent.
- Optional dependencies must not create graph edges, missing-dependency failures, or ordering requirements.
- WHEN a required dependency id is absent, THEN the result must report it through `hasNotFoundDependencies` and `getNotFoundDependencies`.
- WHEN a required dependency version does not satisfy its declared expression, THEN the result must report a `WrongDependencyVersion` containing `dependencyId`, `dependentId`, `existingVersion`, and `requiredVersion`.
- WHEN the required-dependency graph is cyclic, THEN `hasCyclicDependency` must return true and `getSortedPlugins` must return an empty list.
- `Result.isOK` must return true exactly when cyclic, missing, and wrong-version projections are all absent.
- WHEN `resolve` completes, THEN `getDependencies(pluginId)` and `getDependents(pluginId)` must return new lists of direct required relationships.
- IF `getDependencies` or `getDependents` is called before `resolve`, THEN the resolver must raise `IllegalStateException`.

**Version policy in managers.**

- `DefaultVersionManager.checkVersionConstraint` must return true for a null, empty, or `*` constraint and otherwise must apply semantic-version expressions.
- `DefaultVersionManager.compareVersions` must return a negative value, zero, or a positive value according to semantic-version ordering.
- A manager must default `systemVersion` to `0.0.0`, which disables descriptor `requires` rejection.
- WHEN `systemVersion` is not `0.0.0`, THEN a plugin whose `requires` expression is unsatisfied must remain disabled and its wrapper must expose a nonnull failure through `getFailedException`.
- WHILE `exactVersionAllowed` is false, a three-component exact `requires` value must behave as a minimum inclusive version; WHILE it is true, the same value must require equality.
- IF manager dependency resolution finds a cycle, missing required ids, or incompatible required versions, THEN it must raise `CyclicDependencyException`, `DependenciesNotFoundException`, or `DependenciesWrongVersionException` respectively.

## Lifecycle, Status, and Events

Lifecycle operations coordinate plugin callbacks, dependency order, registry views, status persistence, and listener events.

**States and projections.**

- `PluginState` must define `CREATED`, `DISABLED`, `RESOLVED`, `STARTED`, `STOPPED`, `FAILED`, and `UNLOADED`, and each `isCreated`, `isDisabled`, `isResolved`, `isStarted`, `isStopped`, `isFailed`, or `isUnloaded` method must match only its corresponding value.
- `PluginState.parse` must match state names case-insensitively and must return null for an unknown name.
- A newly loaded wrapper must begin in `CREATED`, then must become `RESOLVED` after successful dependency resolution unless status or application-version policy leaves it `DISABLED`.
- `getResolvedPlugins`, `getUnresolvedPlugins`, and `getStartedPlugins` must reflect the registry's current dependency and lifecycle projections.
- A `PluginWrapper` must expose its manager, descriptor, artifact path, plugin class loader, plugin state, runtime mode, plugin id, plugin instance, and failure cause through the named getters.
- WHEN a manager-created wrapper has not been unloaded, THEN its first `getPlugin` call must create and cache the plugin instance through its `PluginFactory`.
- WHILE a wrapper is `UNLOADED`, `getPlugin` must not create a new plugin instance.

**Starting and stopping.**

- WHEN `startPlugins` runs, THEN it must start resolved, non-disabled plugins in dependency order and must leave already started plugins unchanged.
- WHEN `startPlugin(pluginId)` targets a resolved plugin, THEN it must start loaded dependencies before invoking that plugin's `start` callback.
- WHEN manual start targets a disabled but valid plugin, THEN the manager must enable it before starting it.
- WHEN manual `startPlugin(pluginId)` finds a required dependency that does not reach `STARTED`, THEN the dependent must become `FAILED`, must retain a `PluginRuntimeException` failure cause, and must not invoke its own `start` callback.
- WHEN an optional dependency is absent or fails to start, THEN the dependent plugin must still proceed to its own `start` callback.
- WHEN a plugin `start` callback completes, THEN its state must become `STARTED`, its prior failure cause must be cleared, and it must appear in `getStartedPlugins`.
- IF a plugin `start` callback raises an exception or linkage error, THEN its state must become `FAILED` and `getFailedException` must return that cause.
- WHEN `stopPlugin(pluginId)` targets a started plugin, THEN it must stop started dependents before invoking the target plugin's `stop` callback.
- WHEN a plugin `stop` callback completes, THEN its state must become `STOPPED` and it must be absent from `getStartedPlugins`.
- IF a plugin `stop` callback raises `PluginRuntimeException`, THEN its state must become `FAILED` and its wrapper must retain that exception.
- WHEN start or stop targets a plugin already in the requested terminal state, THEN the operation must return the existing state without repeating the lifecycle callback.
- IF start, stop, enable, disable, or delete targets an unknown id, THEN the manager must raise `PluginNotFoundException` carrying that id.

**Disable, enable, unload, and delete.**

- WHEN `disablePlugin` targets a started plugin, THEN it must stop the plugin and its started dependents before setting the target to `DISABLED`.
- WHEN disabling or enabling succeeds, THEN `DefaultPluginStatusProvider` must persist the id in `disabled.txt` or update `enabled.txt` according to the active status-file mode.
- WHERE a nonempty `enabled.txt` exists, the status provider must treat only listed ids as enabled and must ignore `disabled.txt`.
- WHERE no enabled-list mode is active, the status provider must treat ids listed in `disabled.txt` as disabled.
- Status-file parsing must ignore blank lines and lines beginning with `#`.
- WHEN `enablePlugin` targets a valid disabled plugin, THEN it must remove the disabled status and move the wrapper to `CREATED`.
- WHEN `unloadPlugin(pluginId)` targets a loaded plugin, THEN it must unload dependents, stop the plugin, move it to `UNLOADED`, remove it from registry projections, close a closeable plugin class loader, and return true.
- WHEN `unloadPlugin(pluginId)` targets an unknown id, THEN it must return false.
- WHEN `deletePlugin(pluginId)` succeeds, THEN it must stop and unload the plugin, invoke its `delete` callback, delete its repository artifact, and return true.
- IF stop or unload fails during deletion, THEN `deletePlugin` must return false and must retain a failure cause on the wrapper.

**State events.**

- `addPluginStateListener` and `removePluginStateListener` must control delivery to `PluginStateListener.pluginStateChanged`.
- WHEN a plugin state changes, THEN each registered listener must receive one `PluginStateEvent` whose source is the manager, whose plugin is the changed wrapper, whose `oldState` is the preceding state, and whose `pluginState` is the wrapper's new state.
- WHEN an operation leaves a plugin in the same state, THEN the manager must not emit a state event.

## Extension Publication and Lookup

Extension publication and lookup connect compile-time declarations to runtime classes and instances.

**Declaration and indexing.**

- An extension point must be an interface or abstract class implementing the `ExtensionPoint` marker.
- `@Extension` must target classes at runtime and must expose `ordinal`, explicit `points`, and required plugin ids through `plugins`.
- WHEN `points` is empty, THEN annotation processing must associate an extension class with the extension-point interfaces or superclass it directly implements or extends.
- WHEN `points` is nonempty, THEN annotation processing must use those explicit extension points instead of automatic detection.
- IF an annotated concrete type does not implement or extend `ExtensionPoint`, THEN `ExtensionAnnotationProcessor` must report a compilation error.
- WHEN annotation processing succeeds, THEN it must merge existing entries and write every extension binary name to `META-INF/extensions.idx`, including an empty generated resource when no extension exists.
- Indexed extension parsing must ignore comments beginning with `#`, remove whitespace, discard empty lines, and deduplicate class names.

**Lookup visibility and ordering.**

- `getExtensionClassNames(pluginId)` must return indexed extension binary names associated with that plugin.
- `getExtensionClasses(type)` and `getExtensions(type)` must combine system extensions with extensions from started plugins whose classes are assignable to `type`.
- `getExtensionClasses(type, pluginId)` and `getExtensions(type, pluginId)` must restrict results to the named plugin.
- WHILE a plugin is not `STARTED`, its indexed classes must not appear in typed or plugin-scoped extension results.
- System extensions indexed on the application classpath must remain discoverable without loading or starting a plugin.
- Extension results must be ordered by ascending `@Extension.ordinal`, with an omitted ordinal treated as zero.
- WHERE required-plugin checking is enabled, an extension declaring `plugins` must appear only while every named plugin exists and is `STARTED`.
- WHEN a plugin state event occurs, THEN extension lookup must invalidate cached index membership before the next query.

**Instantiation.**

- `DefaultExtensionFactory.create` must instantiate an extension through its accessible no-argument constructor and must wrap construction failure in `PluginRuntimeException`.
- WHEN the default extension factory is active, THEN separate manager `getExtensions` calls must return newly created extension instances.
- An `ExtensionWrapper` must create its extension lazily on the first `getExtension` call and must return that same instance on later calls to that wrapper.
- A `SingletonExtensionFactory` with no class-name filter must return one instance per extension class and class loader across lookup calls.
- A `SingletonExtensionFactory` with class-name filters must reuse instances only for the named extension classes.
- WHEN a plugin leaves `STARTED`, THEN `SingletonExtensionFactory` must discard cached instances owned by that plugin class loader.

## Class Loading and Ownership

Class loading isolates plugin code while preserving application and dependency visibility.

**Loader creation and lookup.**

- Each loaded plugin must receive a distinct plugin class loader, and `getPluginClassLoader(pluginId)` must return it or null for an unknown id.
- A directory plugin must load classes from `classes` and recursively load JAR files below `lib`; a fat JAR plugin must add the artifact itself to its loader.
- A `PluginClassLoader` must support `addURL`, `addFile`, `loadClass`, `getResource`, `getResources`, `close`, and `isClosed` as public operations.
- WHEN `close` completes, THEN `isClosed` must return true.

**Delegation.**

- The default class-loading strategy must be `PDA`: plugin source first, required plugin dependencies second, and application source last.
- WHEN a requested class belongs to `java.*` or `org.pf4j.*`, THEN the plugin class loader must delegate it to the application source before applying the configured strategy.
- `ClassLoadingStrategy` must expose `APD`, `ADP`, `PAD`, `DAP`, `DPA`, and `PDA`, and `getSources` must preserve the configured source order.
- WHEN plugin code requests a class or resource supplied by a required dependency, THEN its loader must search that dependency's plugin class loader.

**Ownership.**

- `whichPlugin(clazz)` must return the resolved wrapper whose plugin class loader loaded `clazz` and must return null for application or unknown class loaders.
- WHEN a plugin unloads, THEN its class loader must be removed from manager lookup and closed when it implements `Closeable`.

## State Model

The core state is an ordered set of configured roots plus a registry keyed by plugin id. Each registry entry combines an artifact path, descriptor, dependency relationships, runtime mode, lifecycle state, plugin instance, class loader, failure cause, status-file projection, and indexed extensions.

The public projections are manager registry lists and lookups, descriptor and resolver values, `PluginWrapper` getters, lifecycle return states, listener events, enabled or disabled files, extension classes and instances, and class-loader ownership queries.

- WHILE a wrapper is registered, its plugin id, descriptor id, dependency-graph vertex, status entry, event identity, and extension ownership must refer to the same plugin.
- WHEN a lifecycle transition completes, THEN manager state lists, wrapper state, emitted event state, extension visibility, and class-loader availability must reflect that transition together.
- WHEN dependency resolution changes after loading or unloading, THEN resolved and unresolved projections must agree with the current descriptor graph.

## Error Semantics

Error outcomes use public exception types or explicit return values.

| Condition | Required result |
|---|---|
| `loadPlugin` receives null or a missing path | IF `loadPlugin` receives null or a missing path, THEN it must raise `IllegalArgumentException`. |
| A path is already loaded | IF a path is already loaded, THEN `loadPlugin` must raise `PluginAlreadyLoadedException` with plugin id and path getters. |
| A descriptor id is empty or its version is null | IF a descriptor id is empty or its version is null, THEN loading must raise `InvalidPluginDescriptorException`. |
| A lifecycle operation requiring an id receives an unknown id | IF a lifecycle operation requiring an id receives an unknown id, THEN it must raise `PluginNotFoundException` with `getPluginId`. |
| A descriptor resource or plugin class loader cannot be read or created | IF a descriptor resource or plugin class loader cannot be read or created, THEN loading must raise `PluginRuntimeException` unless bulk loading explicitly skips that artifact. |
| Required dependencies form a cycle | IF required dependencies form a cycle, THEN manager resolution must raise `DependencyResolver.CyclicDependencyException`. |
| Required dependency ids are absent | IF required dependency ids are absent, THEN manager resolution must raise `DependencyResolver.DependenciesNotFoundException`, whose `getDependencies` returns those ids. |
| Required dependency versions are incompatible | IF required dependency versions are incompatible, THEN manager resolution must raise `DependencyResolver.DependenciesWrongVersionException`, whose `getDependencies` returns the mismatch records. |
| An extension constructor fails | IF an extension constructor fails, THEN its factory must raise `PluginRuntimeException`. |
| Unloading an unknown id | WHEN an unknown id is unloaded, THEN `unloadPlugin` must return false. |
| Looking up an unknown plugin id through `getPlugin`, `getPluginClassLoader`, or `whichPlugin` | WHEN an unknown plugin id is queried through `getPlugin`, `getPluginClassLoader`, or `whichPlugin`, THEN the lookup must return null. |

## Cross-View Invariants

1. A plugin returned by `getPlugin(pluginId)` must expose the same id, descriptor, artifact path, state, and class loader as the corresponding entries in manager lists and class-loader lookup.
2. A required dependency must precede its dependent in `DependencyResolver.Result.getSortedPlugins`, manager resolution order, start order, and the reverse stop order.
3. A wrapper in `getStartedPlugins` must report `STARTED`, must have completed its `Plugin.start` callback, and must be eligible to contribute indexed extensions.
4. A wrapper outside `STARTED` must be absent from `getStartedPlugins`, and its plugin-owned extension classes and instances must be absent from typed and plugin-scoped extension results.
5. Every delivered `PluginStateEvent` must identify the same wrapper held by the manager and must bridge that wrapper's immediately preceding and current states.
6. Disabling or enabling a plugin through the manager must agree with `DefaultPluginStatusProvider.isPluginDisabled` and the active enabled or disabled status file.
7. An extension class returned by `getExtensionClasses(type, pluginId)` must use the same plugin class loader returned by `getPluginClassLoader(pluginId)`, and `whichPlugin` for that class must return the same wrapper.
8. The class order and instance order returned for the same extension point must agree with ascending ordinal and plugin visibility.
9. Unloading a plugin must remove its registry, resolved, started, extension, ownership, and class-loader projections together while preserving unrelated plugins.
10. Descriptor dependency text, parsed `PluginDependency` values, resolver mismatch records, and lifecycle dependency failures must identify the same dependency and dependent ids.

## Public Interface

### Import Surface

```java
import org.pf4j.AbstractPluginManager;
import org.pf4j.ClassLoadingStrategy;
import org.pf4j.DefaultExtensionFactory;
import org.pf4j.DefaultPluginDescriptor;
import org.pf4j.DefaultPluginFactory;
import org.pf4j.DefaultPluginManager;
import org.pf4j.DefaultPluginStatusProvider;
import org.pf4j.DefaultVersionManager;
import org.pf4j.DependencyResolver;
import org.pf4j.Extension;
import org.pf4j.ExtensionDescriptor;
import org.pf4j.ExtensionFactory;
import org.pf4j.ExtensionFinder;
import org.pf4j.ExtensionPoint;
import org.pf4j.ExtensionWrapper;
import org.pf4j.InvalidPluginDescriptorException;
import org.pf4j.JarPluginManager;
import org.pf4j.ManifestPluginDescriptorFinder;
import org.pf4j.Plugin;
import org.pf4j.PluginAlreadyLoadedException;
import org.pf4j.PluginClassLoader;
import org.pf4j.PluginDependency;
import org.pf4j.PluginDescriptor;
import org.pf4j.PluginDescriptorFinder;
import org.pf4j.PluginFactory;
import org.pf4j.PluginLoader;
import org.pf4j.PluginManager;
import org.pf4j.PluginNotFoundException;
import org.pf4j.PluginRepository;
import org.pf4j.PluginRuntimeException;
import org.pf4j.PluginState;
import org.pf4j.PluginStateEvent;
import org.pf4j.PluginStateListener;
import org.pf4j.PluginStatusProvider;
import org.pf4j.PluginWrapper;
import org.pf4j.PropertiesPluginDescriptorFinder;
import org.pf4j.RuntimeMode;
import org.pf4j.SingletonExtensionFactory;
import org.pf4j.VersionManager;
import org.pf4j.ZipPluginManager;
import org.pf4j.processor.ExtensionAnnotationProcessor;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `PluginManager` | interface | Coordinates discovery, lifecycle, state queries, extensions, and class-loader ownership. |
| `AbstractPluginManager` | abstract class | Supplies the common manager state machine and customization hooks. |
| `DefaultPluginManager` | class | Loads mixed directory, JAR, and ZIP plugins. |
| `JarPluginManager` | class | Loads fat JAR plugins. |
| `ZipPluginManager` | class | Loads ZIP or expanded-directory plugins. |
| `PluginDescriptor` | interface | Exposes plugin metadata. |
| `DefaultPluginDescriptor` | class | Provides a constructible descriptor. |
| `PluginDescriptorFinder` | interface | Locates descriptor metadata for an artifact. |
| `ManifestPluginDescriptorFinder` | class | Reads manifest descriptor attributes. |
| `PropertiesPluginDescriptorFinder` | class | Reads property-file descriptor fields. |
| `PluginDependency` | class | Parses one required or optional plugin dependency. |
| `DependencyResolver` | class | Resolves dependency order and incompatibilities. |
| `DependencyResolver.Result` | class | Exposes dependency resolution projections. |
| `DependencyResolver.WrongDependencyVersion` | class | Describes one version mismatch. |
| `VersionManager` | interface | Compares versions and evaluates constraints. |
| `DefaultVersionManager` | class | Applies semantic-version rules. |
| `Plugin` | class | Supplies optional lifecycle callbacks for a plugin. |
| `PluginWrapper` | class | Exposes one registered plugin and its runtime projections. |
| `PluginFactory` | interface | Creates plugin instances. |
| `DefaultPluginFactory` | class | Creates declared plugin classes reflectively. |
| `PluginState` | enum | Names lifecycle states. |
| `PluginStateEvent` | class | Describes one lifecycle transition. |
| `PluginStateListener` | interface | Receives lifecycle events. |
| `PluginStatusProvider` | interface | Reads and changes persistent enabled status. |
| `DefaultPluginStatusProvider` | class | Stores enabled status in text files. |
| `RuntimeMode` | enum | Selects development or deployment behavior. |
| `ExtensionPoint` | interface | Marks application extension contracts. |
| `Extension` | annotation | Marks and configures extension classes. |
| `ExtensionAnnotationProcessor` | class | Publishes annotated extension names at compilation. |
| `ExtensionFinder` | interface | Finds extension wrappers and class names. |
| `ExtensionFactory` | interface | Creates extension instances. |
| `DefaultExtensionFactory` | class | Creates a fresh extension instance. |
| `SingletonExtensionFactory` | class | Reuses selected extension instances. |
| `ExtensionDescriptor` | class | Pairs an extension class with its ordinal. |
| `ExtensionWrapper` | class | Lazily exposes one described extension. |
| `PluginRepository` | interface | Lists and deletes local plugin artifacts. |
| `PluginLoader` | interface | Creates a plugin class loader for an artifact. |
| `PluginClassLoader` | class | Loads isolated plugin classes and resources. |
| `ClassLoadingStrategy` | class | Describes application, plugin, and dependency delegation order. |
| `PluginRuntimeException` | exception | Reports generic plugin failures. |
| `PluginNotFoundException` | exception | Reports an unknown lifecycle plugin id. |
| `PluginAlreadyLoadedException` | exception | Reports a duplicate artifact path. |
| `InvalidPluginDescriptorException` | exception | Reports missing required descriptor data. |

### Public Members

| Name | Kind | Role |
|---|---|---|
| `DefaultPluginManager`, `JarPluginManager`, `ZipPluginManager` | constructors | Create managers for configured plugin roots. |
| `PluginManager.loadPlugins`, `loadPlugin` | methods | Load discovered or selected artifacts. |
| `PluginManager.startPlugins`, `startPlugin`, `stopPlugins`, `stopPlugin` | methods | Run lifecycle callbacks. |
| `PluginManager.unloadPlugins`, `unloadPlugin`, `deletePlugin` | methods | Release or delete plugins. |
| `PluginManager.disablePlugin`, `enablePlugin` | methods | Change persistent enabled status. |
| `PluginManager.getPlugins`, `getPlugin`, `getResolvedPlugins`, `getUnresolvedPlugins`, `getStartedPlugins` | methods | Query registry projections. |
| `PluginManager.getPluginClassLoader`, `whichPlugin` | methods | Query class-loader ownership. |
| `PluginManager.getExtensionClasses`, `getExtensions`, `getExtensionClassNames` | methods | Query extension classes, instances, and names. |
| `PluginManager.addPluginStateListener`, `removePluginStateListener` | methods | Manage lifecycle listeners. |
| `PluginManager.getRuntimeMode`, `isDevelopment`, `isNotDevelopment` | methods | Query runtime mode. |
| `PluginManager.setSystemVersion`, `getSystemVersion`, `getVersionManager` | methods | Configure application-version compatibility. |
| `PluginManager.getPluginsRoot`, `getPluginsRoots` | methods | Query configured roots. |
| `AbstractPluginManager.getPluginLoader`, `getVersion`, `isExactVersionAllowed`, `setExactVersionAllowed` | methods | Expose manager services and version policy. |
| `PluginDescriptor` getters | methods | Return id, description, class, version, requirement, provider, license, and dependencies. |
| `DefaultPluginDescriptor` | constructors | Create empty or populated descriptors. |
| `DefaultPluginDescriptor.addDependency`, `setLicense` | methods | Modify public descriptor fields. |
| `PluginDescriptorFinder.isApplicable`, `find` | methods | Select and read descriptor sources. |
| `PluginDependency` | constructor | Parse one dependency declaration. |
| `PluginDependency.getPluginId`, `getPluginVersionSupport`, `isOptional` | methods | Return parsed dependency fields. |
| `DependencyResolver.resolve`, `getDependencies`, `getDependents` | methods | Build and query dependency graphs. |
| `DependencyResolver.Result` getters | methods | Return cyclic, missing, mismatched, success, and sorted-order projections. |
| `DependencyResolver.WrongDependencyVersion` getters | methods | Return dependency, dependent, existing, and required versions. |
| `VersionManager.checkVersionConstraint`, `compareVersions` | methods | Evaluate and compare versions. |
| `Plugin` | constructors | Create a plugin with no context or a wrapper context. |
| `Plugin.getWrapper`, `start`, `stop`, `delete` | methods | Expose context and lifecycle callbacks. |
| `PluginWrapper` | constructor | Create a wrapper around manager, descriptor, path, and class loader. |
| `PluginWrapper` getters | methods | Return manager, descriptor, path, class loader, plugin, state, mode, id, and failure. |
| `PluginWrapper.setPluginState`, `setPluginFactory`, `setFailedException` | methods | Update framework-owned wrapper projections. |
| `PluginFactory.create` | method | Create a plugin from its wrapper. |
| `PluginState` constants and predicates | enum members | Represent and test lifecycle values. |
| `PluginState.parse` | method | Parse a state name. |
| `PluginStateEvent` | constructor | Create a transition event. |
| `PluginStateEvent.getSource`, `getPlugin`, `getPluginState`, `getOldState` | methods | Return event projections. |
| `PluginStateListener.pluginStateChanged` | method | Receive a transition event. |
| `PluginStatusProvider.isPluginDisabled`, `disablePlugin`, `enablePlugin` | methods | Query and change enabled status. |
| `DefaultPluginStatusProvider` | constructor | Bind status files to a plugin root. |
| `DefaultPluginStatusProvider.getEnabledFilePath`, `getDisabledFilePath` | methods | Return status-file paths. |
| `RuntimeMode.DEVELOPMENT`, `DEPLOYMENT`, `byName` | enum members | Represent and parse runtime modes. |
| `Extension.ordinal`, `points`, `plugins` | annotation members | Configure ordering, extension points, and plugin prerequisites. |
| `ExtensionFinder.find`, `findClassNames` | methods | Return extension wrappers or names. |
| `ExtensionFactory.create` | method | Create an extension instance. |
| `SingletonExtensionFactory` | constructor | Select singleton behavior by optional class names. |
| `ExtensionDescriptor` | constructor and fields | Expose ordinal and extension class. |
| `ExtensionWrapper` | constructor | Bind a descriptor to a factory. |
| `ExtensionWrapper.getExtension`, `getDescriptor`, `getOrdinal`, `compareTo` | methods | Expose lazy instance and ordering. |
| `PluginRepository.getPluginPaths`, `deletePluginPath` | methods | List and delete local artifacts. |
| `PluginLoader.isApplicable`, `loadPlugin` | methods | Select and load an artifact. |
| `PluginClassLoader` | constructors | Create a loader with default or configured delegation. |
| `PluginClassLoader.addURL`, `addFile`, `loadClass`, `getResource`, `getResources`, `close`, `isClosed` | methods | Manage plugin definitions and resources. |
| `ClassLoadingStrategy.APD`, `ADP`, `PAD`, `DAP`, `DPA`, `PDA` | constants | Supply predefined delegation orders. |
| `ClassLoadingStrategy.Source.APPLICATION`, `PLUGIN`, `DEPENDENCIES` | enum members | Name delegation sources. |
| `ClassLoadingStrategy.getSources` | method | Return configured source order. |
| `PluginNotFoundException.getPluginId` | method | Return the unknown id. |
| `PluginAlreadyLoadedException.getPluginId`, `getPluginPath` | methods | Return duplicate path details. |
| Nested dependency exception `getDependencies` methods | methods | Return missing ids or wrong-version records. |

### CLI Entry Points

There is no console script for this package. `java -jar pf4j.jar` is not supported. Programmatic use is through Java imports.

## Appendix A: Environment

The working environment runs JDK 17 and Maven on Linux without network access. The local Maven repository contains `org.slf4j:slf4j-api:2.0.6`, `com.github.zafarkhaja:java-semver:0.10.2`, optional `org.ow2.asm:asm:9.1`, `org.slf4j:slf4j-simple:2.0.6`, `org.hamcrest:hamcrest:2.1`, `org.hamcrest:hamcrest-core:2.1`, `org.junit.jupiter:junit-jupiter-engine:5.4.0`, `org.mockito:mockito-core:5.14.2`, `com.google.testing.compile:compile-testing:0.21.0`, and `org.jetbrains.kotlin:kotlin-stdlib:2.0.21`, together with their cached transitive dependencies. The assessment environment provides the same JDK, Maven tooling, and dependency cache. The target artifact is not preinstalled, and dependency downloads are unavailable.

The project must declare Maven packaging in a root `pom.xml`, use coordinates `org.pf4j:pf4j`, and produce Java 8-compatible main classes while running under the provided JDK.

## Appendix B: Assessment Notes

Automated checks exercise public Java APIs with temporary local directory, JAR, and ZIP artifacts. Checks cover descriptor sources and defaults, dependency order and incompatibilities, lifecycle transitions and failures, status persistence, listener events, extension indexing and lookup, instance policy, class-loader ownership, and consistency among all public projections. Each independent check contributes equally. Private fields, exact logs, exact exception text, and object representations are not inspected.
