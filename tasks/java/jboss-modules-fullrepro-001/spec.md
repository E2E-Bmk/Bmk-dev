# Modular Class Loading Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`org.jboss.modules:jboss-modules` is a Java library that builds isolated modules from resource roots and explicit dependencies, resolves those modules lazily, and projects the resulting graph through class, resource, service, property, and version views. Each module owns a class loader, while a module loader locates specifications by name and links only the dependencies required by the requested module.

The scoped contract covers deterministic, local operation: programmatic module specifications, dependency and export filters, in-memory finders, filesystem repositories with local `module.xml` descriptors, directory and JAR resource roots, aliases, service declarations, module metadata, and version parsing. The Maven coordinate is `org.jboss.modules:jboss-modules`.

## Non-Goals

- This specification does not require Maven artifact resolution, remote repositories, proxy settings, or network-backed resources.
- This specification does not require command-line launchers, dependency-tree formatting, Java agents, logging integrations, management beans, or global URL handler installation.
- This specification does not require the deprecated reference utilities, security permission factories, custom class-loader factories, bytecode transformers, native-library lookup, or security-manager-specific authorization paths.
- This specification does not define private package layout, package-private linkage objects, private access bridges, cache structure, concurrency strategy, exact exception messages, logging text, or textual representations.
- This specification does not require exact compatibility behavior for deprecated factory overloads when the corresponding public builder expresses the same contract.
- This specification does not define XML artifact, native-artifact, permission, conditional-property, or non-default legacy slot selection. The default `main/module.xml` repository layout remains within scope.

## Representative Workflows

### Build and Load an In-Memory Module

```java
import java.util.Map;
import org.jboss.modules.Module;
import org.jboss.modules.ModuleFinder;
import org.jboss.modules.ModuleLoader;
import org.jboss.modules.ModuleSpec;
import org.jboss.modules.Version;

Map<String, ModuleSpec> specs = Map.of(
    "example.app",
    ModuleSpec.build("example.app")
        .addProperty("mode", "test")
        .setVersion(Version.parse("1.2.0"))
        .create()
);
ModuleFinder finder = (name, delegate) -> specs.get(name);
Module module = new ModuleLoader(finder).loadModule("example.app");

assert module.getName().equals("example.app");
assert module.getProperty("mode").equals("test");
assert module.getVersion().equals(Version.parse("1.2.0"));
```

The finder returns a specification only for the requested name. Loading constructs and links one stable module object, and the builder metadata is visible through that object.

### Link Filtered Dependencies

```java
import org.jboss.modules.ModuleDependencySpecBuilder;
import org.jboss.modules.ModuleSpec;
import org.jboss.modules.filter.PathFilters;

var dependency = new ModuleDependencySpecBuilder()
    .setName("example.library")
    .setImportFilter(PathFilters.isOrIsChildOf("org/example/api"))
    .setExport(true)
    .build();

ModuleSpec app = ModuleSpec.build("example.app")
    .addDependency(dependency)
    .create();
```

The importing module sees only accepted dependency paths. Because the dependency is exported, a downstream module depending on `example.app` receives the same accepted view, while rejected paths remain unavailable.

### Load a Local Descriptor Repository

```java
import java.io.File;
import org.jboss.modules.LocalModuleLoader;
import org.jboss.modules.Module;

try (LocalModuleLoader loader = new LocalModuleLoader(new File[] { repositoryRoot })) {
    Module module = loader.loadModule("example.app");
    assert module.getClassLoader().getResource("config/settings.txt") != null;
}
```

The repository maps the module name to a slash-separated module directory and its default `main/module.xml` descriptor, resolves relative resource roots against the descriptor directory, and exposes accepted local resources through the loaded module. Closing the loader releases opened resource roots.

## Module Specification Construction

Module specifications form the immutable input to module loading and preserve the public data needed to construct a module.

**Names and builders.** When `ModuleSpec.build(name)` receives a non-null name, it must return a `ModuleSpec.Builder` whose `getName()` returns that name. If a normal or alias module name is null, then `ModuleSpec.build` or `ModuleSpec.buildAlias` must raise `IllegalArgumentException`. Calling `create()` must return a `ModuleSpec` whose `getName()` returns the defined name. A new normal builder must include the Java base module dependency before caller-added dependencies.

**Content and metadata.** Calling `addResourceRoot` must preserve resource roots in insertion order, and calling `addDependency` must preserve dependencies in insertion order. Calling `addProperty(name, value)` more than once for the same name must retain the last value. Calling `setVersion(version)` must make `getVersion()` on both the builder and loaded module return that value, including null when the version is cleared. Calling `setAssertionSetting(null)` must select `AssertionSetting.INHERIT`; explicit `ENABLED` and `DISABLED` values must control the module class loader's default assertion status.

**Services and entry class.** Calling `addProvide(serviceTypeName, implementationName)` must expose the implementation through the module's service-resource view for that service type. Calling `setMainClass(className)` must select the class used by `Module.run(args)`. If the selected main class is absent or does not expose a public static `main(String[])`, then `Module.run` must raise `ClassNotFoundException` or `NoSuchMethodException`; if the main method fails, then `Module.run` must raise `InvocationTargetException` with the original failure as its cause.

**Aliases.** When `ModuleSpec.buildAlias(aliasName, targetName).create()` is returned by a finder, loading the alias must resolve the target through the same loader. A successfully loaded alias must return the same `Module` object as loading its target name. If an alias target is absent, then loading the alias must raise `ModuleLoadException`.

## Dependency and Visibility Filtering

Dependency specifications define which paths, classes, and resources flow into a module and which portion of that imported view flows to downstream modules.

**Builder defaults.** A new `DependencySpecBuilder` must use `PathFilters.getDefaultImportFilter()` for path imports, `PathFilters.rejectAll()` for path exports, and accept-all filters for resource imports, resource exports, class imports, and class exports. A new `LocalDependencySpecBuilder` must replace the path-import default with `PathFilters.acceptAll()`. A new `ModuleDependencySpecBuilder` must be required, must use the current module's loader when no loader is set, and must raise `IllegalArgumentException` from `build()` until a non-null dependency name has been set.

**Builder projection.** Each `setImportFilter`, `setExportFilter`, `setResourceImportFilter`, `setResourceExportFilter`, `setClassImportFilter`, and `setClassExportFilter` call must be returned by the corresponding getter and by the built `DependencySpec`. If any filter setter receives null, then it must raise `IllegalArgumentException`. Calling `setExport(true)` must select an accept-all export filter, while `setExport(false)` must select a reject-all export filter. Calling `setImportServices(true)` must select the default import filter that accepts `META-INF/services` and its children while rejecting other `META-INF` content; false must select the default import filter that rejects all `META-INF` content.

**Module dependencies.** Calling `setOptional(true)` must make a missing dependency non-fatal during linking, while the module must omit content from that missing dependency. If a required dependency is missing or fails to link, then loading the depending module must raise `ModuleNotFoundException` or the originating `ModuleLoadException`. Calling `setModuleLoader(loader)` must resolve the named dependency through that loader; leaving it null must resolve through the loader of the module being defined.

**Local dependencies.** Calling `LocalDependencySpecBuilder.setLocalLoader(loader)` with null must raise `IllegalArgumentException`. Calling `setLoaderPaths(paths)` with null must raise `IllegalArgumentException`, and a built external local dependency must expose only the declared loader paths that pass its import filter. A local builder without an external local loader must refer to the resource roots of the module being defined.

**Path filters.** `PathFilters.acceptAll()` must accept every path, and `rejectAll()` must reject every path. `all(filters)` must accept only when every nested filter accepts; `any(filters)` must accept when at least one nested filter accepts; `none(filters)` must accept only when no nested filter accepts; and `not(filter)` must invert its delegate. `is(path)` must match exactly that path, `isChildOf(path)` must match descendants but not the path itself, `isOrIsChildOf(path)` must match both, and `in(paths)` must match only set members.

**Glob and ordered filters.** `PathFilters.match(glob)` must interpret `?` as one non-slash character, `*` as zero or more non-slash characters, `**` as zero or more characters including slashes, backslash as an escape, and repeated slashes as one separator. A glob must also match descendants of a matched path, while a glob ending in `/` must match descendants without matching the directory itself. `MultiplePathFilterBuilder` must return the include flag of the first added filter that matches and must return its configured default when none match. An empty multiple-filter builder must create the accept-all or reject-all filter represented by its default.

**Class and resource filtering.** `ClassFilters.acceptAll()` and `rejectAll()` must return constant class filters. `ClassFilters.fromResourcePathFilter(pathFilter)` must test a binary class name after replacing dots with slashes and appending `.class`. `PathFilters.filtered(filter, iterator)` must preserve source order and return only resources whose `Resource.getName()` is accepted.

## Loading and Linking Modules

Module loaders turn finder results into stable, lazily linked module objects and provide deterministic name iteration.

**Finder order and identity.** A `ModuleLoader` constructed with finders must query them in declared order and must use the first non-null specification. If the finder array is null or empty, then the loader must behave as if it has no finders; if the array contains a null element, then construction must raise `IllegalArgumentException`. Repeated successful `loadModule(name)` calls on one loader must return the same module object. Concurrent successful loads of one name must converge on one module object.

**Load failures and linking.** When no finder supplies the requested name, `loadModule(name)` must raise `ModuleNotFoundException`. If a finder returns a specification whose name differs from the requested name, then loading must raise `ModuleLoadException`. Before `loadModule` returns, the module must be linked far enough for required dependency failures to be reported. A failed load must not permanently reserve the name, so a later finder result for that name must be loadable.

**Finder contracts.** `ModuleFinder.findModule(name, loader)` returns a matching specification or null when it does not recognize the name. `IterableModuleFinder.iterateModules(baseName, recursive, loader)` returns names discoverable under the requested base. `ModuleLoader.iterateModules(baseName, recursive)` must concatenate results from iterable finders in finder order and skip finders that do not implement `IterableModuleFinder`; calling `next()` after exhaustion must raise `NoSuchElementException`, and `remove()` must raise `UnsupportedOperationException`.

**Module views.** A loaded `Module` must return its defining name, creating loader, class loader, dependency specifications, properties, version, imported paths, and exported paths through `getName`, `getModuleLoader`, `getClassLoader`, `getDependencies`, `getProperty`, `getPropertyNames`, `getVersion`, `getImportedPaths`, and `getExportedPaths`. `getDependencies()` must return a defensive array copy, `getProperty(name)` must return null for an absent name, and `getProperty(name, defaultValue)` must return the provided default for an absent name. `getPropertyNames()` must return a copy in property insertion order.

**Class-loader association.** `Module.forClass(type)` must return the owning module when the type was defined by a `ModuleClassLoader` and null otherwise. `Module.forClassLoader(loader, false)` must inspect only that loader, while a true search flag must walk parent class loaders until it finds a module or reaches the root. `ModuleLoader.forClass(type)` must accept exactly one `Class<?>` value and return that class's owning `ModuleLoader` or null when no owning module exists, while `ModuleLoader.forClassLoader(classLoader)` must accept exactly one `ClassLoader` value, search that loader and its parent delegation chain, and return the owning `ModuleLoader` or null when none is associated.

## Classes, Resources, and Services

The linked path graph determines the complete class, resource, and service view exposed by each module.

**Local and imported classes.** A module class loader must search the linked module view using accepted dependency paths and class filters. Local resource-root content must take precedence over dependency content for the same class path. `ModuleClassLoader.loadClassLocal(name)` must search only the current module's accepted local roots, return null when no local definition exists, and raise `ClassNotFoundException` when loading the matching definition fails. `getLocalPaths()` must return an unmodifiable set of accepted local paths, while `Module.getImportedPaths()` must include accepted local and dependency paths.

**Resources.** `Resource` must expose a relative name, URL, readable input stream, and size, returning zero when the size is unknown. `ResourceLoader.getResource(name)` must return null for an absent slash-separated resource name. `ResourceLoader.getClassSpec(fileName)` must return null for an absent class file and must raise `IOException` on an I/O failure. `ResourceLoader.getPackageSpec(name)` must return a package specification even when the package has no explicit metadata. `IterableResourceLoader.iterateResources(startPath, recursive)` must constrain enumeration to the normalized start path and must return an empty iterator when nothing matches.

**Provided resource roots.** `ResourceLoaders.createPathResourceLoader(path)` must create an iterable directory-backed loader whose resource names are relative slash-separated paths and whose location identifies the root. `ResourceLoaders.createJarResourceLoader(jarFile)` must create an iterable JAR-backed loader with `jar:` resource URLs and no nested-JAR or native-library behavior. `createJarResourceLoader(jarFile, relativePath)` must treat that relative JAR directory as its root. `createFilteredResourceLoader(filter, loader)` must preserve the loader interface and must hide classes and resources rejected by the filter. If a resource-root path filter rejects a loader path, then that path must be absent from the module's local and imported path projections.

**Resource lookup and iteration.** `Module.getExportedResource(name)` returns the first visible matching URL or null, and `getExportedResources(name)` returns every visible matching URL in loader order. `Module.iterateResources(filter)` must apply the filter to containing paths and must visit only iterable loaders. `Module.globResources(glob)` must apply its glob to complete resource names. `ModuleClassLoader.iterateResources(startName, recurse)` must visit accepted local iterable roots only, and recursive false must restrict results to the named directory.

**Services.** A service declared by `ModuleSpec.Builder.addProvide` must be discoverable through `Module.loadService(serviceType)`. `loadService` must search the module's linked class-loader view, while `loadServiceDirectly` must search service-configuration resources only in the module's local resource view and must not search dependencies. `ResourceLoaders.createServiceResourceLoader(serviceMap)` must expose one `META-INF/services/<service-type>` resource per map entry with implementation names in list order. If a service type, provider predicate, or class loader passed to `Module.findServices` is null, then the method must raise `IllegalArgumentException`.

**Custom loaders.** A `LocalLoader` must return null for an absent local class or package and an empty list for absent resources. `LocalLoaders` path, class, and combined filtered wrappers must delegate accepted requests and hide rejected requests without reordering resource results. `ClassSpec` must preserve either class bytes or a byte buffer, code source, and assertion setting through its public getters and setters. `PackageSpec` must preserve specification metadata, implementation metadata, seal base, and assertion setting through its public getters and setters.

## Filesystem Repositories and Descriptors

Local repositories map module names to descriptor directories and translate supported descriptor elements into the same specification model used by programmatic builders.

**Repository mapping.** `LocalModuleFinder` constructed with repository roots must search roots in declared order. A dot-separated module name must map to a slash-separated module directory followed by the default `main/module.xml` descriptor; a name that cannot be mapped safely must return no specification. Direct lookup must return no specification when the descriptor exists only directly under the module directory rather than under its default `main` directory. `parseModuleXmlFile(name, delegateLoader, roots)` must return the first matching parsed specification or null when no root contains one. `LocalModuleLoader` must use a local finder plus the platform-module delegate and must release finder-owned resource loaders when closed.

**Iteration and closure.** `LocalModuleFinder.iterateModules(baseName, recursive, loader)` must return each descriptor-defined module name at most once across its roots. With recursive false, iteration must inspect only the immediate base directory; with recursive true, it must inspect descendants. A name returned by descriptor iteration must not imply direct lookup eligibility; direct lookup must still require the default `main/module.xml` location. Closing a local finder or loader more than once must be harmless. After closure, operations that need a newly opened resource root must raise `IllegalStateException` or `ModuleLoadException` rather than returning a partially usable module.

**Descriptor roots.** `ModuleXmlParser.parseModuleXml` must accept namespaces `urn:jboss:module:1.0`, `1.1`, `1.2`, `1.3`, `1.5`, `1.6`, `1.7`, `1.8`, and `1.9`. A regular `module` root must define the requested name and must translate optional version, main class, properties, resources, dependencies, exports, and provided services into a `ModuleSpec`. A `module-alias` root must translate its name and target name into an alias specification. If the descriptor name conflicts with a non-null requested name, then parsing must raise `ModuleLoadException`.

**Local resources and filters.** A `resource-root` path must resolve relative to the descriptor directory, while its optional name must identify the loader without changing resource names. A nested resource filter must use ordered include and exclude rules; absent filtering must accept all paths. Module-level exports must filter the local dependency that is visible to downstream modules. Dependency import and export rules must compose with resource and class filters rather than bypassing them.

**Descriptor dependencies and services.** A descriptor module dependency must preserve its name, optional flag, export flag, import rules, export rules, and service-import selection. Properties must preserve declaration order with the last duplicate value visible. A provided service declaration must create the same service-resource projection as `ModuleSpec.Builder.addProvide`. If a required descriptor attribute, supported namespace, or element ordering rule is violated, then parsing must raise `ModuleLoadException`; if descriptor bytes cannot be read, then parsing must raise `IOException` or a `ModuleLoadException` whose cause represents that I/O failure.

**Resource-root factories.** `ModuleXmlParser.ResourceRootFactory.getDefault()` must create path-backed loaders for local descriptor roots. When a custom resource-root factory is passed to `parseModuleXml`, every descriptor resource root must be created through that factory using the descriptor root path, loader path, and loader name. If the factory fails with `IOException`, then parsing must propagate that failure.

## Version and Metadata Semantics

Module versions are normalized, comparable sequences of letter, digit, and separator tokens used for diagnostics rather than dependency selection.

**Parsing and normalization.** `Version.parse(text)` must apply Unicode NFKC normalization and must accept non-empty sequences of Unicode letters and decimal digits separated by `.`, `-`, `+`, or `_`; transitions between letter and digit runs must act as empty separators. If the input is null, empty, contains another character, begins with an invalid token, or ends with a separator, then parsing must raise `IllegalArgumentException`. `toString()` must return the normalized text.

**Ordering and identity.** Version comparison must compare token sequences from left to right. Alphabetic parts must sort before numeric parts; alphabetic parts must compare case-sensitively by Unicode code point; numeric parts must compare by numeric value and then place the shorter equal-valued digit run first. Empty separators must sort before `.`, then `-`, then `+`, then `_`, and an otherwise equal shorter token sequence must sort first. `equals` must agree with `compareTo` returning zero, and equal versions must return equal hash codes.

**Token iteration.** `Version.iterator()` must return a cursor initially positioned before the first token. `hasNext()` must report whether another token exists, and `next()` after exhaustion must raise `NoSuchElementException`. After `next()`, `isAlphaPart`, `isNumberPart`, `isEmptySeparator`, and `isNonEmptySeparator` must identify the current token, while `isPart` and `isSeparator` must group those categories. Calling a typed accessor for the wrong token kind must raise `IllegalStateException`. Numeric accessors must return the current digits as a string, low-order `int` or `long`, or exact `BigInteger`; `length()` must return the current token's character length.

**Module metadata.** A version attached through a builder or descriptor must be returned unchanged by `Module.getVersion()` and must not affect module identity, finder selection, dependency linking, or alias resolution. The module name must remain the sole lookup key within one module loader.

## State Model

The core state is a lazily materialized graph keyed by module name. Finder results create module specifications; module specifications create stable module objects; linking derives imported and exported path-to-loader views; resource roots hold local class and resource content.

The public projections are the module-loader name view, the module metadata view, the module class-loader view, the dependency-filter view, the resource and service view, the local descriptor view, and the version token view. Builder mutation is visible only in specifications created after that mutation. Loaded module metadata and linked views remain stable unless a new loader is used to load a new specification.

## Error Semantics

| Condition | Required result |
|---|---|
| Null normal or alias module name | Raise `IllegalArgumentException` |
| Module dependency built without a name | Raise `IllegalArgumentException` |
| Null dependency filter, local loader, or loader-path set | Raise `IllegalArgumentException` |
| Missing requested module | Raise `ModuleNotFoundException` |
| Finder returns a specification with a different name | Raise `ModuleLoadException` |
| Missing required dependency or alias target | Raise `ModuleNotFoundException` or `ModuleLoadException` |
| Missing optional dependency | Link without that dependency's content |
| Missing class definition | Return null from local lookup or raise `ClassNotFoundException` from normal class loading |
| Missing resource | Return null or an empty enumeration/iterator according to the called method |
| Malformed or unsupported local descriptor | Raise `ModuleLoadException` |
| Descriptor or resource-root I/O failure | Raise `IOException` or a causally linked `ModuleLoadException` |
| Invalid version text | Raise `IllegalArgumentException` |
| Version iterator advanced after exhaustion | Raise `NoSuchElementException` |
| Version token accessor used for the wrong token kind | Raise `IllegalStateException` |
| Module main class absent or lacks the required entry method | Raise `ClassNotFoundException` or `NoSuchMethodException` |
| Module main method fails | Raise `InvocationTargetException` with the original failure as cause |

## Cross-View Invariants

1. A specification name returned by a finder must equal the name exposed by the loaded module and the key used by that loader for repeated lookup.
2. A property and version placed on a `ModuleSpec.Builder` must be visible through the loaded `Module` without affecting dependency selection or module identity.
3. A local resource-root path accepted by its root filter must appear in `ModuleClassLoader.getLocalPaths()` and in `Module.getImportedPaths()`, while a rejected path must appear in neither view.
4. A dependency path must be visible to the importing module only when every applicable path import, class import, resource import, and resource-root filter accepts the requested view.
5. A dependency path visible through an exported dependency must be visible to a downstream module only when every import and export filter along the complete chain accepts it.
6. A class or resource found through a module class loader must originate from a path present in that module's linked imported-path view.
7. A service added through `addProvide` must be represented by a local service resource and must be discoverable through downstream `loadService` only when service and export filters permit the path.
8. Loading an alias and its target through the same loader must return one module object whose metadata, class loader, resources, properties, and version projections are identical.
9. A module parsed from `module.xml` must behave the same as a programmatically built specification with equivalent resources, dependencies, filters, properties, services, name, and version.
10. A version's normalized string, iterator token stream, comparison result, equality result, and hash behavior must describe one consistent normalized token sequence.
11. A name exposed by local descriptor iteration must not be treated as directly loadable unless direct lookup resolves that name through its default `main/module.xml` descriptor.

## Public Interface

### Import Surface

```java
import org.jboss.modules.AssertionSetting;
import org.jboss.modules.ClassSpec;
import org.jboss.modules.DependencySpec;
import org.jboss.modules.DependencySpecBuilder;
import org.jboss.modules.IterableLocalLoader;
import org.jboss.modules.IterableModuleFinder;
import org.jboss.modules.IterableResourceLoader;
import org.jboss.modules.LocalDependencySpecBuilder;
import org.jboss.modules.LocalLoader;
import org.jboss.modules.LocalLoaders;
import org.jboss.modules.LocalModuleFinder;
import org.jboss.modules.LocalModuleLoader;
import org.jboss.modules.Module;
import org.jboss.modules.ModuleClassLoader;
import org.jboss.modules.ModuleDependencySpec;
import org.jboss.modules.ModuleDependencySpecBuilder;
import org.jboss.modules.ModuleFinder;
import org.jboss.modules.ModuleLoadException;
import org.jboss.modules.ModuleLoader;
import org.jboss.modules.ModuleNotFoundException;
import org.jboss.modules.ModuleSpec;
import org.jboss.modules.PackageSpec;
import org.jboss.modules.Resource;
import org.jboss.modules.ResourceLoader;
import org.jboss.modules.ResourceLoaderSpec;
import org.jboss.modules.ResourceLoaders;
import org.jboss.modules.Version;
import org.jboss.modules.ModuleSpec.AliasBuilder;
import org.jboss.modules.ModuleSpec.Builder;
import org.jboss.modules.Version.Iterator;
```

```java
import org.jboss.modules.filter.ClassFilter;
import org.jboss.modules.filter.ClassFilters;
import org.jboss.modules.filter.MultiplePathFilterBuilder;
import org.jboss.modules.filter.PathFilter;
import org.jboss.modules.filter.PathFilters;
```

```java
import org.jboss.modules.xml.ModuleXmlParser;
import org.jboss.modules.xml.ModuleXmlParser.ResourceRootFactory;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `ModuleSpec` | class | Defines a normal or alias module before loading |
| `ModuleSpec.Builder` | interface | Accumulates normal-module dependencies, resource roots, metadata, and services |
| `ModuleSpec.AliasBuilder` | interface | Creates an alias specification for a target module name |
| `AssertionSetting` | enum | Selects enabled, disabled, or inherited assertion status |
| `DependencySpec` | class | Immutable dependency filter contract and compatibility factories |
| `DependencySpecBuilder` | class | Common builder for dependency filters |
| `ModuleDependencySpec` | class | Exposes a named module dependency's loader, name, and optional flag |
| `ModuleDependencySpecBuilder` | class | Builds named module dependencies |
| `LocalDependencySpecBuilder` | class | Builds dependencies on module-local or external local-loader content |
| `ModuleFinder` | interface | Resolves a module name to a specification |
| `IterableModuleFinder` | interface | Adds name iteration to a finder |
| `ModuleLoader` | class | Loads, caches, links, and iterates modules through finders |
| `Module` | class | Exposes the loaded module's metadata, class loader, resources, and services |
| `ModuleClassLoader` | class | Exposes the complete linked class/resource view of one module |
| `ModuleLoadException` | exception | Reports module discovery, definition, or linking failure |
| `ModuleNotFoundException` | exception | Reports absence of a required named module |
| `Resource` | interface | Exposes one named readable resource |
| `ResourceLoader` | interface | Supplies class, package, resource, path, and location data for one root |
| `IterableResourceLoader` | interface | Adds resource enumeration to a resource loader |
| `ResourceLoaderSpec` | class | Associates a resource loader with a path filter |
| `ResourceLoaders` | class | Creates directory, JAR, filtered, and service resource loaders |
| `LocalLoader` | interface | Supplies local classes, packages, and resources |
| `IterableLocalLoader` | interface | Adds resource enumeration to a local loader |
| `LocalLoaders` | class | Creates path-, class-, and combined-filtered local-loader views |
| `ClassSpec` | class | Carries class bytes or a buffer plus definition metadata |
| `PackageSpec` | class | Carries package specification, implementation, sealing, and assertion metadata |
| `LocalModuleFinder` | class | Finds and iterates filesystem `module.xml` specifications |
| `LocalModuleLoader` | class | Loads modules from filesystem repositories and closes their resource roots |
| `Version` | class | Parses, normalizes, compares, hashes, and tokenizes module versions |
| `Version.Iterator` | class | Traverses version parts and separators |
| `PathFilter` | interface | Accepts or rejects slash-separated paths |
| `PathFilters` | class | Creates and combines path filters and filtered resource iterators |
| `MultiplePathFilterBuilder` | class | Builds first-match ordered include/exclude filters |
| `ClassFilter` | interface | Accepts or rejects binary class names |
| `ClassFilters` | class | Creates constant and resource-path-backed class filters |
| `ModuleXmlParser` | class | Parses supported local module descriptors into specifications |
| `ModuleXmlParser.ResourceRootFactory` | interface | Creates descriptor resource roots from resolved local paths |

### CLI Entry Points

This scoped contract defines no console script or `java -jar` protocol. Programmatic use is through the Java packages and public types listed above.

## Appendix A: Environment

The working environment runs Eclipse Temurin Java 17 with Maven 3.9.12 on Linux without network access. Java SE 17 APIs are preinstalled. The target library is not preinstalled, and no additional runtime library is available unless its artifact already exists in the provided offline Maven repository. The assessment environment provides the same JDK, Maven, and offline dependency set.

The project must declare `org.jboss.modules:jboss-modules` in a standard root `pom.xml`, use Java 17-compatible source, and produce its implementation with the coordinate version supplied by the build invocation. Runtime behavior must not require network access or external services.

## Appendix B: Assessment Notes

Implementations are exercised through the public Java surface described above. Checks cover builder projections, filter truth tables, module identity and failure paths, lazy linking, required and optional dependencies, transitive exports, class/resource/service visibility, aliases, local repository descriptors, resource roots, properties, versions, and cross-view consistency. Temporary directories and locally constructed JARs provide deterministic content. The focus is observable behavior rather than private fields, exact messages, logs, or textual representations.
