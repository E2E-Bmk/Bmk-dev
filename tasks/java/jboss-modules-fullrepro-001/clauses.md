# Clause Sidecar — Modular Class Loading v4

This WIP sidecar is not candidate-visible. Each ID maps to one verbatim behavioral sentence in `spec_v4.md`; Stage 3 Java test Javadocs must use `Verifies: <clause IDs>`. All entries passed the upstream-documentation ceiling, support a family of inputs, and state a rule rather than a fixture instance.

## Module Specification Construction

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-SPEC-001 | Module Specification Construction | “When `ModuleSpec.build(name)` receives a non-null name, it must return a `ModuleSpec.Builder` whose `getName()` returns that name.” |
| JMOD-SPEC-002 | Module Specification Construction | “If a normal or alias module name is null, then `ModuleSpec.build` or `ModuleSpec.buildAlias` must raise `IllegalArgumentException`.” |
| JMOD-SPEC-003 | Module Specification Construction | “Calling `create()` must return a `ModuleSpec` whose `getName()` returns the defined name.” |
| JMOD-SPEC-004 | Module Specification Construction | “A new normal builder must include the Java base module dependency before caller-added dependencies.” |
| JMOD-SPEC-005 | Module Specification Construction | “Calling `addResourceRoot` must preserve resource roots in insertion order, and calling `addDependency` must preserve dependencies in insertion order.” |
| JMOD-SPEC-006 | Module Specification Construction | “Calling `addProperty(name, value)` more than once for the same name must retain the last value.” |
| JMOD-SPEC-007 | Module Specification Construction | “Calling `setVersion(version)` must make `getVersion()` on both the builder and loaded module return that value, including null when the version is cleared.” |
| JMOD-SPEC-008 | Module Specification Construction | “Calling `setAssertionSetting(null)` must select `AssertionSetting.INHERIT`; explicit `ENABLED` and `DISABLED` values must control the module class loader's default assertion status.” |
| JMOD-SPEC-009 | Module Specification Construction | “Calling `addProvide(serviceTypeName, implementationName)` must expose the implementation through the module's service-resource view for that service type.” |
| JMOD-SPEC-010 | Module Specification Construction | “Calling `setMainClass(className)` must select the class used by `Module.run(args)`.” |
| JMOD-SPEC-011 | Module Specification Construction | “If the selected main class is absent or does not expose a public static `main(String[])`, then `Module.run` must raise `ClassNotFoundException` or `NoSuchMethodException`; if the main method fails, then `Module.run` must raise `InvocationTargetException` with the original failure as its cause.” |
| JMOD-SPEC-012 | Module Specification Construction | “When `ModuleSpec.buildAlias(aliasName, targetName).create()` is returned by a finder, loading the alias must resolve the target through the same loader.” |
| JMOD-SPEC-013 | Module Specification Construction | “A successfully loaded alias must return the same `Module` object as loading its target name.” |
| JMOD-SPEC-014 | Module Specification Construction | “If an alias target is absent, then loading the alias must raise `ModuleLoadException`.” |

## Dependency and Visibility Filtering

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-FILT-001 | Dependency and Visibility Filtering | “A new `DependencySpecBuilder` must use `PathFilters.getDefaultImportFilter()` for path imports, `PathFilters.rejectAll()` for path exports, and accept-all filters for resource imports, resource exports, class imports, and class exports.” |
| JMOD-FILT-002 | Dependency and Visibility Filtering | “A new `LocalDependencySpecBuilder` must replace the path-import default with `PathFilters.acceptAll()`.” |
| JMOD-FILT-003 | Dependency and Visibility Filtering | “A new `ModuleDependencySpecBuilder` must be required, must use the current module's loader when no loader is set, and must raise `IllegalArgumentException` from `build()` until a non-null dependency name has been set.” |
| JMOD-FILT-004 | Dependency and Visibility Filtering | “Each `setImportFilter`, `setExportFilter`, `setResourceImportFilter`, `setResourceExportFilter`, `setClassImportFilter`, and `setClassExportFilter` call must be returned by the corresponding getter and by the built `DependencySpec`.” |
| JMOD-FILT-005 | Dependency and Visibility Filtering | “If any filter setter receives null, then it must raise `IllegalArgumentException`.” |
| JMOD-FILT-006 | Dependency and Visibility Filtering | “Calling `setExport(true)` must select an accept-all export filter, while `setExport(false)` must select a reject-all export filter.” |
| JMOD-FILT-007 | Dependency and Visibility Filtering | “Calling `setImportServices(true)` must select the default import filter that accepts `META-INF/services` and its children while rejecting other `META-INF` content; false must select the default import filter that rejects all `META-INF` content.” |
| JMOD-FILT-008 | Dependency and Visibility Filtering | “Calling `setOptional(true)` must make a missing dependency non-fatal during linking, while the module must omit content from that missing dependency.” |
| JMOD-FILT-009 | Dependency and Visibility Filtering | “If a required dependency is missing or fails to link, then loading the depending module must raise `ModuleNotFoundException` or the originating `ModuleLoadException`.” |
| JMOD-FILT-010 | Dependency and Visibility Filtering | “Calling `setModuleLoader(loader)` must resolve the named dependency through that loader; leaving it null must resolve through the loader of the module being defined.” |
| JMOD-FILT-011 | Dependency and Visibility Filtering | “Calling `LocalDependencySpecBuilder.setLocalLoader(loader)` with null must raise `IllegalArgumentException`.” |
| JMOD-FILT-012 | Dependency and Visibility Filtering | “Calling `setLoaderPaths(paths)` with null must raise `IllegalArgumentException`, and a built external local dependency must expose only the declared loader paths that pass its import filter.” |
| JMOD-FILT-013 | Dependency and Visibility Filtering | “A local builder without an external local loader must refer to the resource roots of the module being defined.” |
| JMOD-FILT-014 | Dependency and Visibility Filtering | “`PathFilters.acceptAll()` must accept every path, and `rejectAll()` must reject every path.” |
| JMOD-FILT-015 | Dependency and Visibility Filtering | “`all(filters)` must accept only when every nested filter accepts; `any(filters)` must accept when at least one nested filter accepts; `none(filters)` must accept only when no nested filter accepts; and `not(filter)` must invert its delegate.” |
| JMOD-FILT-016 | Dependency and Visibility Filtering | “`is(path)` must match exactly that path, `isChildOf(path)` must match descendants but not the path itself, `isOrIsChildOf(path)` must match both, and `in(paths)` must match only set members.” |
| JMOD-FILT-017 | Dependency and Visibility Filtering | “`PathFilters.match(glob)` must interpret `?` as one non-slash character, `*` as zero or more non-slash characters, `**` as zero or more characters including slashes, backslash as an escape, and repeated slashes as one separator.” |
| JMOD-FILT-018 | Dependency and Visibility Filtering | “A glob must also match descendants of a matched path, while a glob ending in `/` must match descendants without matching the directory itself.” |
| JMOD-FILT-019 | Dependency and Visibility Filtering | “`MultiplePathFilterBuilder` must return the include flag of the first added filter that matches and must return its configured default when none match.” |
| JMOD-FILT-020 | Dependency and Visibility Filtering | “An empty multiple-filter builder must create the accept-all or reject-all filter represented by its default.” |
| JMOD-FILT-021 | Dependency and Visibility Filtering | “`ClassFilters.acceptAll()` and `rejectAll()` must return constant class filters.” |
| JMOD-FILT-022 | Dependency and Visibility Filtering | “`ClassFilters.fromResourcePathFilter(pathFilter)` must test a binary class name after replacing dots with slashes and appending `.class`.” |
| JMOD-FILT-023 | Dependency and Visibility Filtering | “`PathFilters.filtered(filter, iterator)` must preserve source order and return only resources whose `Resource.getName()` is accepted.” |

## Loading and Linking Modules

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-LOAD-001 | Loading and Linking Modules | “A `ModuleLoader` constructed with finders must query them in declared order and must use the first non-null specification.” |
| JMOD-LOAD-002 | Loading and Linking Modules | “If the finder array is null or empty, then the loader must behave as if it has no finders; if the array contains a null element, then construction must raise `IllegalArgumentException`.” |
| JMOD-LOAD-003 | Loading and Linking Modules | “Repeated successful `loadModule(name)` calls on one loader must return the same module object.” |
| JMOD-LOAD-004 | Loading and Linking Modules | “Concurrent successful loads of one name must converge on one module object.” |
| JMOD-LOAD-005 | Loading and Linking Modules | “When no finder supplies the requested name, `loadModule(name)` must raise `ModuleNotFoundException`.” |
| JMOD-LOAD-006 | Loading and Linking Modules | “If a finder returns a specification whose name differs from the requested name, then loading must raise `ModuleLoadException`.” |
| JMOD-LOAD-007 | Loading and Linking Modules | “Before `loadModule` returns, the module must be linked far enough for required dependency failures to be reported.” |
| JMOD-LOAD-008 | Loading and Linking Modules | “A failed load must not permanently reserve the name, so a later finder result for that name must be loadable.” |
| JMOD-LOAD-009 | Loading and Linking Modules | “`ModuleFinder.findModule(name, loader)` returns a matching specification or null when it does not recognize the name.” |
| JMOD-LOAD-010 | Loading and Linking Modules | “`IterableModuleFinder.iterateModules(baseName, recursive, loader)` returns names discoverable under the requested base.” |
| JMOD-LOAD-011 | Loading and Linking Modules | “`ModuleLoader.iterateModules(baseName, recursive)` must concatenate results from iterable finders in finder order and skip finders that do not implement `IterableModuleFinder`; calling `next()` after exhaustion must raise `NoSuchElementException`, and `remove()` must raise `UnsupportedOperationException`.” |
| JMOD-LOAD-012 | Loading and Linking Modules | “A loaded `Module` must return its defining name, creating loader, class loader, dependency specifications, properties, version, imported paths, and exported paths through `getName`, `getModuleLoader`, `getClassLoader`, `getDependencies`, `getProperty`, `getPropertyNames`, `getVersion`, `getImportedPaths`, and `getExportedPaths`.” |
| JMOD-LOAD-013 | Loading and Linking Modules | “`getDependencies()` must return a defensive array copy, `getProperty(name)` must return null for an absent name, and `getProperty(name, defaultValue)` must return the provided default for an absent name.” |
| JMOD-LOAD-014 | Loading and Linking Modules | “`getPropertyNames()` must return a copy in property insertion order.” |
| JMOD-LOAD-015 | Loading and Linking Modules | “`Module.forClass(type)` must return the owning module when the type was defined by a `ModuleClassLoader` and null otherwise.” |
| JMOD-LOAD-016 | Loading and Linking Modules | “`Module.forClassLoader(loader, false)` must inspect only that loader, while a true search flag must walk parent class loaders until it finds a module or reaches the root.” |
| JMOD-LOAD-017 | Loading and Linking Modules | “`ModuleLoader.forClass(type)` must accept exactly one `Class<?>` value and return that class's owning `ModuleLoader` or null when no owning module exists, while `ModuleLoader.forClassLoader(classLoader)` must accept exactly one `ClassLoader` value, search that loader and its parent delegation chain, and return the owning `ModuleLoader` or null when none is associated.” |

## Classes, Resources, and Services

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-RES-001 | Classes, Resources, and Services | “A module class loader must search the linked module view using accepted dependency paths and class filters.” |
| JMOD-RES-002 | Classes, Resources, and Services | “Local resource-root content must take precedence over dependency content for the same class path.” |
| JMOD-RES-003 | Classes, Resources, and Services | “`ModuleClassLoader.loadClassLocal(name)` must search only the current module's accepted local roots, return null when no local definition exists, and raise `ClassNotFoundException` when loading the matching definition fails.” |
| JMOD-RES-004 | Classes, Resources, and Services | “`getLocalPaths()` must return an unmodifiable set of accepted local paths, while `Module.getImportedPaths()` must include accepted local and dependency paths.” |
| JMOD-RES-005 | Classes, Resources, and Services | “`Resource` must expose a relative name, URL, readable input stream, and size, returning zero when the size is unknown.” |
| JMOD-RES-006 | Classes, Resources, and Services | “`ResourceLoader.getResource(name)` must return null for an absent slash-separated resource name.” |
| JMOD-RES-007 | Classes, Resources, and Services | “`ResourceLoader.getClassSpec(fileName)` must return null for an absent class file and must raise `IOException` on an I/O failure.” |
| JMOD-RES-008 | Classes, Resources, and Services | “`ResourceLoader.getPackageSpec(name)` must return a package specification even when the package has no explicit metadata.” |
| JMOD-RES-009 | Classes, Resources, and Services | “`IterableResourceLoader.iterateResources(startPath, recursive)` must constrain enumeration to the normalized start path and must return an empty iterator when nothing matches.” |
| JMOD-RES-010 | Classes, Resources, and Services | “`ResourceLoaders.createPathResourceLoader(path)` must create an iterable directory-backed loader whose resource names are relative slash-separated paths and whose location identifies the root.” |
| JMOD-RES-011 | Classes, Resources, and Services | “`ResourceLoaders.createJarResourceLoader(jarFile)` must create an iterable JAR-backed loader with `jar:` resource URLs and no nested-JAR or native-library behavior.” |
| JMOD-RES-012 | Classes, Resources, and Services | “`createJarResourceLoader(jarFile, relativePath)` must treat that relative JAR directory as its root.” |
| JMOD-RES-013 | Classes, Resources, and Services | “`createFilteredResourceLoader(filter, loader)` must preserve the loader interface and must hide classes and resources rejected by the filter.” |
| JMOD-RES-014 | Classes, Resources, and Services | “If a resource-root path filter rejects a loader path, then that path must be absent from the module's local and imported path projections.” |
| JMOD-RES-015 | Classes, Resources, and Services | “`Module.getExportedResource(name)` returns the first visible matching URL or null, and `getExportedResources(name)` returns every visible matching URL in loader order.” |
| JMOD-RES-016 | Classes, Resources, and Services | “`Module.iterateResources(filter)` must apply the filter to containing paths and must visit only iterable loaders.” |
| JMOD-RES-017 | Classes, Resources, and Services | “`Module.globResources(glob)` must apply its glob to complete resource names.” |
| JMOD-RES-018 | Classes, Resources, and Services | “`ModuleClassLoader.iterateResources(startName, recurse)` must visit accepted local iterable roots only, and recursive false must restrict results to the named directory.” |
| JMOD-RES-019 | Classes, Resources, and Services | “A service declared by `ModuleSpec.Builder.addProvide` must be discoverable through `Module.loadService(serviceType)`.” |
| JMOD-RES-020 | Classes, Resources, and Services | “`loadService` must search the module's linked class-loader view, while `loadServiceDirectly` must search service-configuration resources only in the module's local resource view and must not search dependencies.” |
| JMOD-RES-021 | Classes, Resources, and Services | “`ResourceLoaders.createServiceResourceLoader(serviceMap)` must expose one `META-INF/services/<service-type>` resource per map entry with implementation names in list order.” |
| JMOD-RES-022 | Classes, Resources, and Services | “If a service type, provider predicate, or class loader passed to `Module.findServices` is null, then the method must raise `IllegalArgumentException`.” |
| JMOD-RES-023 | Classes, Resources, and Services | “A `LocalLoader` must return null for an absent local class or package and an empty list for absent resources.” |
| JMOD-RES-024 | Classes, Resources, and Services | “`LocalLoaders` path, class, and combined filtered wrappers must delegate accepted requests and hide rejected requests without reordering resource results.” |
| JMOD-RES-025 | Classes, Resources, and Services | “`ClassSpec` must preserve either class bytes or a byte buffer, code source, and assertion setting through its public getters and setters.” |
| JMOD-RES-026 | Classes, Resources, and Services | “`PackageSpec` must preserve specification metadata, implementation metadata, seal base, and assertion setting through its public getters and setters.” |

## Filesystem Repositories and Descriptors

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-XML-001 | Filesystem Repositories and Descriptors | “`LocalModuleFinder` constructed with repository roots must search roots in declared order.” |
| JMOD-XML-002 | Filesystem Repositories and Descriptors | “A dot-separated module name must map to a slash-separated module directory followed by the default `main/module.xml` descriptor; a name that cannot be mapped safely must return no specification.” |
| JMOD-XML-003 | Filesystem Repositories and Descriptors | “`parseModuleXmlFile(name, delegateLoader, roots)` must return the first matching parsed specification or null when no root contains one.” |
| JMOD-XML-004 | Filesystem Repositories and Descriptors | “`LocalModuleLoader` must use a local finder plus the platform-module delegate and must release finder-owned resource loaders when closed.” |
| JMOD-XML-005 | Filesystem Repositories and Descriptors | “`LocalModuleFinder.iterateModules(baseName, recursive, loader)` must return each descriptor-defined module name at most once across its roots.” |
| JMOD-XML-006 | Filesystem Repositories and Descriptors | “With recursive false, iteration must inspect only the immediate base directory; with recursive true, it must inspect descendants.” |
| JMOD-XML-007 | Filesystem Repositories and Descriptors | “Closing a local finder or loader more than once must be harmless.” |
| JMOD-XML-008 | Filesystem Repositories and Descriptors | “After closure, operations that need a newly opened resource root must raise `IllegalStateException` or `ModuleLoadException` rather than returning a partially usable module.” |
| JMOD-XML-009 | Filesystem Repositories and Descriptors | “`ModuleXmlParser.parseModuleXml` must accept namespaces `urn:jboss:module:1.0`, `1.1`, `1.2`, `1.3`, `1.5`, `1.6`, `1.7`, `1.8`, and `1.9`.” |
| JMOD-XML-010 | Filesystem Repositories and Descriptors | “A regular `module` root must define the requested name and must translate optional version, main class, properties, resources, dependencies, exports, and provided services into a `ModuleSpec`.” |
| JMOD-XML-011 | Filesystem Repositories and Descriptors | “A `module-alias` root must translate its name and target name into an alias specification.” |
| JMOD-XML-012 | Filesystem Repositories and Descriptors | “If the descriptor name conflicts with a non-null requested name, then parsing must raise `ModuleLoadException`.” |
| JMOD-XML-013 | Filesystem Repositories and Descriptors | “A `resource-root` path must resolve relative to the descriptor directory, while its optional name must identify the loader without changing resource names.” |
| JMOD-XML-014 | Filesystem Repositories and Descriptors | “A nested resource filter must use ordered include and exclude rules; absent filtering must accept all paths.” |
| JMOD-XML-015 | Filesystem Repositories and Descriptors | “Module-level exports must filter the local dependency that is visible to downstream modules.” |
| JMOD-XML-016 | Filesystem Repositories and Descriptors | “Dependency import and export rules must compose with resource and class filters rather than bypassing them.” |
| JMOD-XML-017 | Filesystem Repositories and Descriptors | “A descriptor module dependency must preserve its name, optional flag, export flag, import rules, export rules, and service-import selection.” |
| JMOD-XML-018 | Filesystem Repositories and Descriptors | “Properties must preserve declaration order with the last duplicate value visible.” |
| JMOD-XML-019 | Filesystem Repositories and Descriptors | “A provided service declaration must create the same service-resource projection as `ModuleSpec.Builder.addProvide`.” |
| JMOD-XML-020 | Filesystem Repositories and Descriptors | “If a required descriptor attribute, supported namespace, or element ordering rule is violated, then parsing must raise `ModuleLoadException`; if descriptor bytes cannot be read, then parsing must raise `IOException` or a `ModuleLoadException` whose cause represents that I/O failure.” |
| JMOD-XML-021 | Filesystem Repositories and Descriptors | “`ModuleXmlParser.ResourceRootFactory.getDefault()` must create path-backed loaders for local descriptor roots.” |
| JMOD-XML-022 | Filesystem Repositories and Descriptors | “When a custom resource-root factory is passed to `parseModuleXml`, every descriptor resource root must be created through that factory using the descriptor root path, loader path, and loader name.” |
| JMOD-XML-023 | Filesystem Repositories and Descriptors | “If the factory fails with `IOException`, then parsing must propagate that failure.” |
| JMOD-XML-024 | Filesystem Repositories and Descriptors | “Direct lookup must return no specification when the descriptor exists only directly under the module directory rather than under its default `main` directory.” |
| JMOD-XML-025 | Filesystem Repositories and Descriptors | “A name returned by descriptor iteration must not imply direct lookup eligibility; direct lookup must still require the default `main/module.xml` location.” |

## Version and Metadata Semantics

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-VER-001 | Version and Metadata Semantics | “`Version.parse(text)` must apply Unicode NFKC normalization and must accept non-empty sequences of Unicode letters and decimal digits separated by `.`, `-`, `+`, or `_`; transitions between letter and digit runs must act as empty separators.” |
| JMOD-VER-002 | Version and Metadata Semantics | “If the input is null, empty, contains another character, begins with an invalid token, or ends with a separator, then parsing must raise `IllegalArgumentException`.” |
| JMOD-VER-003 | Version and Metadata Semantics | “`toString()` must return the normalized text.” |
| JMOD-VER-004 | Version and Metadata Semantics | “Version comparison must compare token sequences from left to right.” |
| JMOD-VER-005 | Version and Metadata Semantics | “Alphabetic parts must sort before numeric parts; alphabetic parts must compare case-sensitively by Unicode code point; numeric parts must compare by numeric value and then place the shorter equal-valued digit run first.” |
| JMOD-VER-006 | Version and Metadata Semantics | “Empty separators must sort before `.`, then `-`, then `+`, then `_`, and an otherwise equal shorter token sequence must sort first.” |
| JMOD-VER-007 | Version and Metadata Semantics | “`equals` must agree with `compareTo` returning zero, and equal versions must return equal hash codes.” |
| JMOD-VER-008 | Version and Metadata Semantics | “`Version.iterator()` must return a cursor initially positioned before the first token.” |
| JMOD-VER-009 | Version and Metadata Semantics | “`hasNext()` must report whether another token exists, and `next()` after exhaustion must raise `NoSuchElementException`.” |
| JMOD-VER-010 | Version and Metadata Semantics | “After `next()`, `isAlphaPart`, `isNumberPart`, `isEmptySeparator`, and `isNonEmptySeparator` must identify the current token, while `isPart` and `isSeparator` must group those categories.” |
| JMOD-VER-011 | Version and Metadata Semantics | “Calling a typed accessor for the wrong token kind must raise `IllegalStateException`.” |
| JMOD-VER-012 | Version and Metadata Semantics | “Numeric accessors must return the current digits as a string, low-order `int` or `long`, or exact `BigInteger`; `length()` must return the current token's character length.” |
| JMOD-VER-013 | Version and Metadata Semantics | “A version attached through a builder or descriptor must be returned unchanged by `Module.getVersion()` and must not affect module identity, finder selection, dependency linking, or alias resolution.” |
| JMOD-VER-014 | Version and Metadata Semantics | “The module name must remain the sole lookup key within one module loader.” |

## Cross-View Invariants

| ID | Section anchor | Verbatim clause |
|---|---|---|
| JMOD-CVI-001 | Cross-View Invariants | “A specification name returned by a finder must equal the name exposed by the loaded module and the key used by that loader for repeated lookup.” |
| JMOD-CVI-002 | Cross-View Invariants | “A property and version placed on a `ModuleSpec.Builder` must be visible through the loaded `Module` without affecting dependency selection or module identity.” |
| JMOD-CVI-003 | Cross-View Invariants | “A local resource-root path accepted by its root filter must appear in `ModuleClassLoader.getLocalPaths()` and in `Module.getImportedPaths()`, while a rejected path must appear in neither view.” |
| JMOD-CVI-004 | Cross-View Invariants | “A dependency path must be visible to the importing module only when every applicable path import, class import, resource import, and resource-root filter accepts the requested view.” |
| JMOD-CVI-005 | Cross-View Invariants | “A dependency path visible through an exported dependency must be visible to a downstream module only when every import and export filter along the complete chain accepts it.” |
| JMOD-CVI-006 | Cross-View Invariants | “A class or resource found through a module class loader must originate from a path present in that module's linked imported-path view.” |
| JMOD-CVI-007 | Cross-View Invariants | “A service added through `addProvide` must be represented by a local service resource and must be discoverable through downstream `loadService` only when service and export filters permit the path.” |
| JMOD-CVI-008 | Cross-View Invariants | “Loading an alias and its target through the same loader must return one module object whose metadata, class loader, resources, properties, and version projections are identical.” |
| JMOD-CVI-009 | Cross-View Invariants | “A module parsed from `module.xml` must behave the same as a programmatically built specification with equivalent resources, dependencies, filters, properties, services, name, and version.” |
| JMOD-CVI-010 | Cross-View Invariants | “A version's normalized string, iterator token stream, comparison result, equality result, and hash behavior must describe one consistent normalized token sequence.” |
| JMOD-CVI-011 | Cross-View Invariants | “A name exposed by local descriptor iteration must not be treated as directly loadable unless direct lookup resolves that name through its default `main/module.xml` descriptor.” |

Clause count: 14 specification + 23 filtering + 17 loading + 26 resource/service + 25 descriptor + 14 version + 11 invariant = **130 stable clauses**.
