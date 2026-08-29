# ClassGraph Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`classgraph` is a local JVM classpath and module scanner that reads classfiles and resources into a queryable metadata graph without loading or initializing the discovered classes. The installable Maven artifact is `io.github.classgraph:classgraph`, the Java module is `io.github.classgraph`, and the exported package is `io.github.classgraph`.

A caller configures sources, accepted regions, and metadata capabilities through `ClassGraph`, obtains a closeable `ScanResult`, and reads the same snapshot through class relationships, member and annotation metadata, resource content, package/module views, and parsed type signatures.

## Non-Goals

- This specification does not require independent APIs from `classgraph-base`, `classgraph-vfs`, or `classgraph-classpath`; those artifacts are transitive implementation dependencies of the scanner artifact.
- This specification does not require the `classgraph-viz` artifact or graph-rendering output.
- This specification does not require remote URL retrieval, network services, framework-specific classloader compatibility, native reflection drivers, or external processes.
- This specification does not require private or package-private helpers, internal work queues, parser carriers, classloader handlers, or storage layout.
- This specification does not define exact log messages, exception message text, `toString()` layout, ordering that is not documented by a public list contract, or byte-for-byte visualization text.
- This specification does not require serialization of `ScanResult`; callers persist their own derived data when needed.

## Representative Workflows

### Scan one local classpath entry and query its class graph

```java
try (ScanResult result = new ClassGraph()
        .enableClasspathEntries(classesDirectory)
        .enableClassInfo()
        .acceptPackages("example.plugins")
        .scan()) {
    ClassInfoList implementations = result.getAllClassesImplementing("example.plugins.Plugin");
    List<String> names = implementations.getNames();
}
```

This workflow demonstrates an explicitly bounded local source, class metadata enablement, package acceptance, graph traversal, and a list projection.

### Read annotations and method signatures from one snapshot

```java
try (ScanResult result = new ClassGraph()
        .enableClasspathEntries(classesDirectory)
        .enableClassInfo()
        .enableMethodInfo()
        .enableAnnotationInfo()
        .acceptPackages("example.handlers")
        .scan()) {
    for (ClassInfo owner : result.getClassesWithMethodAnnotation("example.handlers.Route")) {
        for (MethodInfo method : owner.getMethodInfoWithAnnotation("example.handlers.Route")) {
            String resultType = method.getTypeSignatureOrTypeDescriptor().getResultType().toString();
        }
    }
}
```

This workflow demonstrates the relationship between enabled metadata capabilities, class-level queries, member metadata, annotations, and parsed signatures.

### Find and consume local resources

```java
try (ScanResult result = new ClassGraph()
        .enableClasspathEntries(resourcesDirectory)
        .acceptPaths("templates")
        .scan()) {
    ResourceList templates = result.getResourcesWithExtension("html");
    templates.forEachByteArray((resource, bytes) -> {
        String path = resource.getPath();
        int size = bytes.length;
    });
}
```

This workflow demonstrates resource acceptance, extension lookup, bulk content access, path metadata, and automatic resource closure.

## Scan Sources and Selection

This section covers how a caller chooses local scan inputs and narrows them before the immutable result snapshot is built.

**Builder and source accumulation.**

- The `ClassGraph` constructor must create an empty mutable scan configuration whose configuration methods return the same builder instance for chaining.
- When no classpath or module source has been enabled, `scan`, `getClasspath`, `getClasspathFiles`, `getClasspathURIs`, `getClasspathURLs`, `getModuleReferences`, and `getModulePathInfo` must observe no environment-derived scan source.
- When `enableClasspath`, `enableClassLoaders`, `enableClasspathEntries`, `enableSystemModules`, `enableNonSystemModules`, `enableModules`, or `enableModuleLayers` is called repeatedly, the builder must accumulate sources, preserve classpath-source call order, and place modules before classpath entries in scan order.
- When explicit class loaders or module layers are enabled without the corresponding environment-enabling call, the builder must restrict source discovery to those values and their reachable parents.
- While `ignoreParentClassLoaders` or `ignoreParentModuleLayers` is enabled, source discovery must omit parent loaders or layers that are ancestors of another enabled source.
- If `enableClassLoaders`, `enableClasspathEntries`, or `enableModuleLayers` receives no usable element, a null element, or an unsupported classpath element, then the builder must raise `IllegalArgumentException`.

**Acceptance and rejection.**

- When `acceptPackages` or `acceptPaths` receives a name, the scan must accept that region recursively; when the corresponding `NonRecursive` method is used, the scan must accept only that exact package or path.
- When `acceptClasses`, `acceptJars`, `acceptModules`, `acceptClasspathElementsContainingResourcePath`, or their rejection counterparts receive patterns, the scan must apply `*` within one segment, `**` across whole segments, and `?` to one character where the method documents glob support.
- When an item matches both an acceptance rule and a rejection rule, the scan must exclude the item.
- When no acceptance rule exists for a category, the scan must retain every non-rejected item in that category; when acceptance rules exist, the scan must retain only accepted, non-rejected items.
- When `disableJarScanning`, `disableNestedJarScanning`, or `disableDirScanning` is enabled, the scan must omit the corresponding classpath element kind while leaving other enabled kinds eligible.
- If a non-recursive package or path rule contains a glob, a jar rule contains a directory component, or a rejection names the root package/path, then the builder must raise `IllegalArgumentException`.

**Metadata capabilities.**

- When `enableClassInfo`, `enableMethodInfo`, `enableFieldInfo`, `enableAnnotationInfo`, `enableStaticFinalFieldConstantInitializerValues`, or `enableInterClassDependencies` is called, the result must expose the corresponding metadata family.
- When `enableAllInfo` is called, the builder must enable class, method, field, annotation, static-final-value, and inter-class-dependency metadata together.
- While `ignoreClassVisibility`, `ignoreMethodVisibility`, or `ignoreFieldVisibility` is enabled, the scan must retain non-public metadata in the corresponding projection.
- While `enableExternalClasses` is enabled, relationship and dependency queries must include referenced classes outside accepted regions; otherwise those queries must restrict results to classes encountered within the accepted scan scope.
- When `disableRuntimeInvisibleAnnotations` is enabled, the scan must omit runtime-invisible annotation metadata while retaining enabled runtime-visible annotation metadata.
- When `enableMultiReleaseVersions` is enabled, the scan must expose eligible versioned classfile entries in addition to the runtime-selected multi-release view.
- When `filterClasspathElements` or `filterClasspathElementsByURL` is configured, the scan must retain only classpath elements accepted by every applicable predicate.
- When `verbose` or `enableRealtimeLogging` is enabled, scan progress must be emitted through the public logging channel without making exact message text part of the result contract.
- The `getVersion()` method must return the version of the scanner artifact that provides the running `ClassGraph` class.
- When `setMaxBufferedJarRAMSize`, `setWorkerTimeout`, or `removeTemporaryFilesAfterScan` is configured, scan execution must honor the selected memory-buffer, worker-timeout, or temporary-file-lifecycle policy, and the `workerTimeout` parameter of `setWorkerTimeout` must receive a `java.time.Duration` value.
- If a metadata query is called without its required enable method, then the query must raise `IllegalStateException` rather than return an incomplete successful projection.

## Scan Execution and Lifecycle

This section covers synchronous and asynchronous execution, result snapshots, provenance views, and resource ownership.

**Execution forms.**

- When `scan()` is called, the builder must execute with an internally managed executor and return one completed `ScanResult`.
- When `scan(int)` or `scan(ExecutorService, int)` is called, the builder must use the requested parallel-task count and return one completed `ScanResult` without taking ownership of a caller-supplied executor.
- When the future-returning `scanAsync` overload is called, the builder must return a `Future<ScanResult>` whose successful completion contains the same public snapshot produced by synchronous execution.
- When the callback `scanAsync` overload is called, successful completion must invoke the result consumer once, and failed completion must invoke the failure consumer once.
- If scan execution fails, then synchronous execution and future retrieval must raise `ClassGraphException` or surface the originating failure through the documented asynchronous failure channel.

**Snapshot projections.**

- When a scan completes, `ScanResult` must preserve the effective capability flags and expose the scanned source order through its classpath file, URI, URL, string, module-reference, and module-path projections.
- When no matching class, package, module, resource, annotation, field, or method exists, singular lookup methods must return `null` and plural lookup methods must return an empty typed list.
- When classpath contents change after scanning, `isClasspathContentsModifiedSinceScan` must report the change and `getClasspathContentsLastModifiedMillis` must reflect the latest observed modification time for the scanned entries.
- If a `ScanResult` lookup receives a null required name or an invalid class/annotation argument, then the lookup must raise `IllegalArgumentException`.

**Closure.**

- When `ScanResult.close()` is called, the result must release scan-owned open resources, become closed, and make `isClosed()` return true; repeated closure must have no additional effect.
- While a `ScanResult` is closed, every lookup that depends on its snapshot must raise `IllegalStateException`.
- When `ScanResult.closeAll()` is called, every currently open result tracked by the library must become closed.

## Class Graph Queries

This section covers class identity, kind predicates, hierarchy traversal, annotation-driven class selection, and relationship-aware class lists.

**Class identity and kinds.**

- When `getClassInfo` finds an accepted or externally retained class name, it must return one `ClassInfo` whose `getName`, `getSimpleName`, `getPackageName`, modifiers, classfile version, source file, classpath element, module, package, and resource projections describe the same classfile.
- The `ClassInfo` kind predicates must distinguish standard classes, interfaces, annotations, enums, records, array classes, inner/outer classes, anonymous classes, synthetic classes, and external classes according to the scanned classfile metadata.
- When a class has no superclass, outer class, module, package record, source file, defining resource, or generic signature, the corresponding singular metadata accessor must return `null`.
- If class metadata was not enabled or its owning result is closed, then a class graph query must raise `IllegalStateException`.

**Hierarchy and assignability.**

- When an `All` hierarchy query is used, `ScanResult` and `ClassInfo` must return the transitive relationship closure; when the corresponding `Direct` query is used, they must return only immediate relationships.
- When subclass, superclass, implemented-interface, class-implementing-interface, subinterface, or superinterface queries are made through `Class<?>` and `String` overloads naming the same type, both overloads must return equivalent `ClassInfoList` values.
- When `extendsSuperclass`, `implementsInterface`, or `isAssignableFrom`-equivalent list filtering is applied, the result must follow Java class/interface assignability, including transitive inheritance.
- If a `Class<?>` argument does not represent the relationship kind required by the query or is null, then the query must raise `IllegalArgumentException` or `NullPointerException` according to the public parameter contract.

**Class list algebra.**

- When `ClassInfoList.directOnly()` is called on a relationship result, it must retain only the directly related subset recorded by that result.
- When `union`, `intersect`, or `exclude` is called, the returned `ClassInfoList` must implement set union, set intersection, or left-hand set difference while preserving the list's documented ordering policy.
- When `filter`, `getStandardClasses`, `getInterfaces`, `getInterfacesAndAnnotations`, `getImplementedInterfaces`, `getAnnotations`, `getEnums`, `getRecords`, or `getAssignableTo` is called, the returned list must contain only elements satisfying the named predicate and must not mutate the source list.
- If class-list algebra receives a null list, null predicate, or null assignability target, then it must raise `IllegalArgumentException` or `NullPointerException` according to the public parameter contract.

## Member, Annotation, and Signature Metadata

This section covers fields, methods, parameters, annotations, values, and parsed JVM type information as coordinated views of one classfile.

**Fields and methods.**

- When `enableMethodInfo` is active, declared method queries must return members written by that class, inherited method queries must apply overriding, constructor queries must select constructors, and annotation/name filters must select matching methods.
- When `enableFieldInfo` is active, declared field queries must return fields written by that class, inherited field queries must apply hiding, enum-constant queries must return enum constants, and annotation/name filters must select matching fields.
- The `ClassMemberInfo`, `MethodInfo`, `FieldInfo`, and `MethodParameterInfo` views must expose names, declaring class identity, modifiers, annotation views, descriptors, signatures, and signature-or-descriptor fallback values that agree for the same member.
- When parameter metadata is present, `MethodInfo.getParameterInfo()` must return an ordered Java `List` of `MethodParameterInfo` values whose list positions agree with `MethodParameterInfo.getIndex()` and whose names, modifiers, annotations, descriptors, signatures, and varargs states align with the declaring method.
- When static-final initializer capture was enabled, `FieldInfo.getConstantInitializerValue()` must return the supported classfile constant value; when no supported constant was captured, it must return `null`.
- If method, field, annotation, or static-final metadata was not enabled before scanning, then the dependent accessor must raise `IllegalStateException`.

**Annotations.**

- When an `All` annotation query is used through `HasAnnotations`, `ClassInfo`, `ClassMemberInfo`, `MethodParameterInfo`, `PackageInfo`, or `ModuleInfo`, the returned `AnnotationInfoList` must include direct annotations plus reachable meta-annotations and inherited class annotations.
- When a `Direct` annotation query or `directOnly()` is used, the returned list must include only annotations written directly on the queried element.
- When a repeatable annotation query is used, the returned list must expand the repeatable container and preserve every matching annotation instance.
- When `AnnotationInfo.getParameterValues()` is called, the result must merge explicitly declared values with annotation defaults; `getDeclaredParameterValues()` must omit defaults, and `getDefaultParameterValues()` must contain only defaults known from the annotation class.
- The `AnnotationParameterValue.getValue()` and `AnnotationParameterValueList.getValue(name)` projections must return primitive/string values, primitive arrays, `AnnotationEnumValue`, `AnnotationClassRef`, nested `AnnotationInfo`, or arrays of these according to the classfile value kind.
- When a named annotation or parameter is absent, singular lookup must return `null` and repeatable/plural lookup must return an empty typed list.
- If a class-valued annotation argument is not an annotation type or a required annotation/parameter name is null, then the query must raise `IllegalArgumentException`.

**Descriptors and signatures.**

- When a field, method, or parameter has a generic signature, its `getTypeSignature()` must return the parsed signature, and when none is present it must return `null`; when a class has a generic declaration signature, `ClassInfo.getTypeSignature()` must return its parsed `ClassTypeSignature`, and when none is present it must return `null`; each corresponding `getTypeSignatureOrTypeDescriptor()` fallback must remain available independently and must return the parsed descriptor when no generic signature is present.
- The `BaseTypeSignature`, `ArrayTypeSignature`, `ClassRefTypeSignature`, `ClassTypeSignature`, `MethodTypeSignature`, `TypeArgument`, `TypeParameter`, and `TypeVariableSignature` views must preserve primitive names, array dimensions, nested class suffixes, type arguments, bounds, result types, throws types, receiver annotations, and referenced class identity represented by the classfile signature.
- When `TypeSignature.resolveTypeVariables(contextClass)` or `TypeVariableSignature.resolve()` is called, the returned signature or parameter must resolve variables against the requested class context while preserving unresolved variables that have no mapping.
- The `TypeArgument.Wildcard` value must distinguish `NONE`, `ANY`, `EXTENDS`, and `SUPER`.
- When `TypeArgument.getWildcard()` returns `ANY`, `getTypeSignature()` must return `null`; when it returns a bounded form, `getTypeSignature()` must return the associated bound.
- When an array signature is projected through `ArrayTypeSignature` and `ArrayClassInfo`, both views must agree on element type, nested type, dimension count, signature text, and array class metadata.
- If a stored signature is malformed or a type variable cannot be validly resolved against its context, then signature access must raise `IllegalArgumentException` rather than return unrelated metadata.

## Resources, Packages, Modules, and Lists

This section covers non-class resources, bulk reads, duplicate paths, package/module grouping, and common list projections.

**Resource discovery.**

- When resource lookup is performed by exact path, leaf name, extension, regular-expression pattern, or wildcard, `ScanResult` must return every accepted matching resource in classpath resolution order.
- When `getResourcesWithPathIgnoringAccept` is called, the result must include matching non-rejected resources even when their paths were not accepted by an acceptance rule.
- The `Resource.getPath()` projection must return the path relative to the package root.
- The `Resource.getPathRelativeToClasspathElement()` projection must retain the full path within its classpath element.
- The URI, URL, classpath-element, module, length, modification-time, and POSIX-permission projections must describe the same resource as its path and content views.
- When multiple classpath elements contain one path, `ResourceList.asMap()` must group all definitions under that path and `findDuplicatePaths()` must return only groups containing more than one resource.
- If a required path, extension, wildcard, pattern, or predicate is null, then resource lookup or filtering must raise `IllegalArgumentException`.

**Content access and ownership.**

- When `Resource.open()`, `read()`, `load()`, or `loadAsString()` succeeds, the resource must expose the same content through a stream, closeable byte buffer, byte array, or decoded string respectively.
- When `loadAsString(Charset)` is called, the resource must decode the complete bytes with the supplied charset; the no-argument form must use UTF-8.
- When `Resource.close()` is called, it must close the active stream or release the active buffer, and repeated closure must have no additional effect.
- When a `ResourceList.forEachByteArray`, `forEachInputStream`, or `forEachByteBuffer` method is called, it must invoke the consumer once per resource, close each resource after its callback, and return the same list for chaining.
- When an `IgnoringIOException` bulk method encounters an `IOException`, it must skip that failure and continue with later resources; the corresponding non-ignoring method must raise the `IOException`.
- If resource content cannot be opened, read, loaded, or decoded, then the content accessor must raise `IOException`; if the resource is opened concurrently or used after its owning result is closed, then it must raise `IllegalStateException` or `IOException` according to the accessor.

**Package, module, and common list views.**

- When a public metadata-list constructor receives a collection, the new typed list must preserve that collection's iteration order and elements without mutating the source collection.
- The `ModuleInfo` view must project one module's name, reference, location, classes, packages, and annotations.
- The `PackageInfo` view must project one package's name, parent, children, direct classes, recursive classes, and annotations.
- When `InfoList.getNames`, `getAsStrings`, or `getAsStringsWithSimpleNames` is called, the returned value must preserve list order and project each element through its corresponding public name or string view.
- When `MappableInfoList.get(name)`, `containsName(name)`, or `asMap()` is called, all three projections must agree on the same name-to-element association; a missing name must return `null` or false.
- When an `emptyList()` factory is used, it must return an empty typed list that is safe for read-only queries.
- If a common list lookup or filter receives a null required name or predicate, then it must raise `IllegalArgumentException`.

## State Model

The core state is a mutable `ClassGraph` configuration followed by an immutable, closeable `ScanResult` snapshot. The snapshot contains ordered scanned sources, accepted resources, parsed classfiles, relationship edges, optional metadata families, package/module groupings, and owned resource handles.

The public projections are the builder configuration and source previews; `ScanResult` classpath/module/resource queries; `ClassInfo` relationship and member views; annotation and type-signature objects; list/map/string projections; and lifecycle state on `ScanResult`, `Resource`, and `ResourceList`.

- While a builder is mutable and no scan has completed, configuration calls must affect subsequent scans without mutating earlier `ScanResult` snapshots.
- When two public views refer to the same scanned classfile, resource, member, annotation, package, or module, their names, source location, and relationship identity must remain coherent.
- While a metadata capability is disabled, every dependent public projection must fail consistently rather than expose a partial graph.
- While a result is open, resources and metadata objects obtained from it must remain associated with that snapshot; while it is closed, snapshot-dependent access must fail consistently.

## Error Semantics

- If a required builder, lookup, callback, pattern, name, class, list, or predicate argument is null or empty where emptiness is invalid, then the receiving API must raise `IllegalArgumentException` or `NullPointerException` according to its declared Java parameter contract.
- If a non-recursive pattern contains a wildcard, a jar selector contains a directory path, or root rejection would reject everything, then `ClassGraph` must raise `IllegalArgumentException`.
- If a class, method, field, annotation, dependency, or constant-value query is used without the required enable method, then the query must raise `IllegalStateException`.
- If a snapshot-dependent operation is used after `ScanResult.close()`, then the operation must raise `IllegalStateException`.
- If resource bytes cannot be opened, read, loaded, or decoded, then the content API must raise `IOException`, except that an `IgnoringIOException` bulk method must continue after the failed resource.
- If synchronous or future-based scan execution fails, then the scan API must raise `ClassGraphException` or expose the original cause through the future contract; callback-based execution must pass the failure to its failure consumer.
- If a singular lookup has no matching public entity, then the lookup must return `null`; if a plural lookup has no matching entity, then it must return the corresponding empty typed list.

## Cross-View Invariants

1. The class returned by a `ScanResult` relationship query must have the same name, package, module, classpath element, and defining resource when reached through the corresponding `ClassInfo`, `PackageInfo`, `ModuleInfo`, and resource projections.
2. The transitive relationship returned by an `All` query must contain its corresponding `Direct` relationship, and `ClassInfoList.directOnly()` must recover the direct subset recorded for that query.
3. The member returned through `ClassInfo` must report the same declaring class, name, modifiers, descriptor/signature fallback, annotations, and referenced-class dependencies when viewed through `ClassMemberInfo`, `MethodInfo`, `FieldInfo`, or `MethodParameterInfo` as applicable.
4. The annotation selected by a class, method, field, parameter, package, or module query must be retrievable by the same name from its `HasAnnotations` and `AnnotationInfo` projections, and its `AnnotationParameterValueList` merged and declared views must agree on explicitly supplied values.
5. The resource returned by any path, extension, pattern, wildcard, map, or duplicate-path projection must expose identical bytes and classpath/module identity through direct `Resource` access and `ResourceList` bulk access.
6. The capability booleans on `ScanResult` must agree with which `ClassInfo`, `FieldInfo`, `MethodInfo`, annotation, dependency, external-class, and visibility projections succeed.
7. The parsed `TypeSignature` for a class, method, field, parameter, or array must agree with its descriptor fallback, referenced `ClassInfo` values, array dimensions, generic bounds, and annotation metadata across every corresponding signature object.
8. When a `ScanResult` is closed, its owned `Resource` values must close or become invalid and every later `ClassInfo`, metadata-list, and resource query must fail consistently.

## Public Interface

### Import Surface

The Maven artifact `io.github.classgraph:classgraph` exports Java module and package `io.github.classgraph`.

```java
import io.github.classgraph.AnnotationClassRef;
import io.github.classgraph.AnnotationEnumValue;
import io.github.classgraph.AnnotationInfo;
import io.github.classgraph.AnnotationInfoList;
import io.github.classgraph.AnnotationParameterValue;
import io.github.classgraph.AnnotationParameterValueList;
import io.github.classgraph.ArrayClassInfo;
import io.github.classgraph.ArrayTypeSignature;
import io.github.classgraph.BaseTypeSignature;
import io.github.classgraph.ClassGraph;
import io.github.classgraph.ClassGraphException;
import io.github.classgraph.ClassInfo;
import io.github.classgraph.ClassInfoList;
import io.github.classgraph.ClassMemberInfo;
import io.github.classgraph.ClassRefOrTypeVariableSignature;
import io.github.classgraph.ClassRefTypeSignature;
import io.github.classgraph.ClassTypeSignature;
import io.github.classgraph.FieldInfo;
import io.github.classgraph.FieldInfoList;
import io.github.classgraph.HasAnnotations;
import io.github.classgraph.HasName;
import io.github.classgraph.HierarchicalTypeSignature;
import io.github.classgraph.InfoList;
import io.github.classgraph.MappableInfoList;
import io.github.classgraph.MethodInfo;
import io.github.classgraph.MethodInfoList;
import io.github.classgraph.MethodParameterInfo;
import io.github.classgraph.MethodTypeSignature;
import io.github.classgraph.ModuleInfo;
import io.github.classgraph.ModuleInfoList;
import io.github.classgraph.PackageInfo;
import io.github.classgraph.PackageInfoList;
import io.github.classgraph.ReferenceTypeSignature;
import io.github.classgraph.Resource;
import io.github.classgraph.ResourceList;
import io.github.classgraph.ScanResult;
import io.github.classgraph.TypeArgument;
import io.github.classgraph.TypeParameter;
import io.github.classgraph.TypeSignature;
import io.github.classgraph.TypeVariableSignature;
```

Declared public member families are indexed below; overloads share one family name and inherited members are indexed at their declaring ClassGraph type.

| Declaring type | Public member families |
|---|---|
| `AnnotationClassRef` | `getClassInfo`, `getName` |
| `AnnotationEnumValue` | `getClassName`, `getName`, `getValueName` |
| `AnnotationInfo` | `getClassInfo`, `getDeclaredParameterValues`, `getDefaultParameterValues`, `getName`, `getParameterValues`, `isInherited` |
| `AnnotationInfoList` | `AnnotationInfoList`, `directOnly`, `emptyList`, `filter`, `getRepeatable` |
| `AnnotationParameterValue` | `getName`, `getValue` |
| `AnnotationParameterValueList` | `AnnotationParameterValueList`, `emptyList`, `getValue` |
| `ArrayClassInfo` | `getArrayTypeSignature`, `getElementClassInfo`, `getElementTypeSignature`, `getNumDimensions`, `getTypeSignature`, `getTypeSignatureString` |
| `ArrayTypeSignature` | `equalsIgnoringTypeParams`, `getArrayClassInfo`, `getElementTypeSignature`, `getNestedType`, `getNumDimensions`, `getTypeAnnotationInfo`, `getTypeSignatureString` |
| `BaseTypeSignature` | `equalsIgnoringTypeParams`, `getType`, `getTypeName`, `getTypeSignatureChar` |
| `ClassGraph` | `acceptClasses`, `acceptClasspathElementsContainingResourcePath`, `acceptJars`, `acceptModules`, `acceptPackages`, `acceptPackagesNonRecursive`, `acceptPaths`, `acceptPathsNonRecursive`, `ClassGraph`, `disableDirScanning`, `disableJarScanning`, `disableNestedJarScanning`, `disableRuntimeInvisibleAnnotations`, `enableAllInfo`, `enableAnnotationInfo`, `enableClassInfo`, `enableClassLoaders`, `enableClasspath`, `enableClasspathEntries`, `enableExternalClasses`, `enableFieldInfo`, `enableInterClassDependencies`, `enableMethodInfo`, `enableModuleLayers`, `enableModules`, `enableMultiReleaseVersions`, `enableNonSystemModules`, `enableRealtimeLogging`, `enableStaticFinalFieldConstantInitializerValues`, `enableSystemJars`, `enableSystemModules`, `filterClasspathElements`, `filterClasspathElementsByURL`, `getClasspath`, `getClasspathFiles`, `getClasspathURIs`, `getClasspathURLs`, `getModulePathInfo`, `getModuleReferences`, `getVersion`, `ignoreClassVisibility`, `ignoreFieldVisibility`, `ignoreMethodVisibility`, `ignoreParentClassLoaders`, `ignoreParentModuleLayers`, `rejectClasses`, `rejectClasspathElementsContainingResourcePath`, `rejectJars`, `rejectModules`, `rejectPackages`, `rejectPaths`, `removeTemporaryFilesAfterScan`, `scan`, `scanAsync`, `setMaxBufferedJarRAMSize`, `setWorkerTimeout`, `verbose` |
| `ClassGraphException` | *(none declared)* |
| `ClassInfo` | `extendsSuperclass`, `getAllAnnotationInfo`, `getAllAnnotations`, `getAllClassesImplementing`, `getAllSubclasses`, `getAllSubinterfaces`, `getAllSuperclasses`, `getAllSuperinterfaces`, `getAnnotationDefaultParameterValues`, `getClassDependencies`, `getClassesWithAnnotation`, `getClassesWithFieldAnnotation`, `getClassesWithMethodAnnotation`, `getClassesWithMethodParameterAnnotation`, `getClassfileMajorVersion`, `getClassfileMinorVersion`, `getClassLoaderString`, `getClasspathElementFile`, `getClasspathElementURI`, `getClasspathElementURL`, `getConstructorInfo`, `getDeclaredConstructorInfo`, `getDeclaredFieldInfo`, `getDeclaredFieldInfoWithAnnotation`, `getDeclaredMethodAndConstructorInfo`, `getDeclaredMethodInfo`, `getDeclaredMethodInfoWithAnnotation`, `getDirectAnnotations`, `getDirectClassesImplementing`, `getDirectSubclasses`, `getDirectSubinterfaces`, `getDirectSuperinterfaces`, `getEnumConstants`, `getFieldAnnotations`, `getFieldInfo`, `getFieldInfoWithAnnotation`, `getFullyQualifiedDefiningMethodName`, `getInnerClasses`, `getMethodAndConstructorInfo`, `getMethodAnnotations`, `getMethodInfo`, `getMethodInfoWithAnnotation`, `getMethodParameterAnnotations`, `getModifiers`, `getModifiersString`, `getModuleInfo`, `getModuleReference`, `getName`, `getOuterClasses`, `getPackageInfo`, `getPackageName`, `getResource`, `getSimpleName`, `getSourceFile`, `getSuperclass`, `getTypeDescriptor`, `getTypeSignature`, `getTypeSignatureOrTypeDescriptor`, `getTypeSignatureString`, `hasAnnotation`, `hasDeclaredField`, `hasDeclaredFieldAnnotation`, `hasDeclaredMethod`, `hasDeclaredMethodAnnotation`, `hasDeclaredMethodParameterAnnotation`, `hasField`, `hasFieldAnnotation`, `hasMethod`, `hasMethodAnnotation`, `hasMethodParameterAnnotation`, `implementsInterface`, `isAbstract`, `isAnnotation`, `isAnonymousInnerClass`, `isArrayClass`, `isEnum`, `isExternalClass`, `isFinal`, `isImplementedInterface`, `isInnerClass`, `isInterface`, `isInterfaceOrAnnotation`, `isOuterClass`, `isPackageVisible`, `isPrivate`, `isProtected`, `isPublic`, `isRecord`, `isStandardClass`, `isStatic`, `isSynthetic` |
| `ClassInfoList` | `ClassInfoList`, `directOnly`, `emptyList`, `exclude`, `filter`, `getAnnotations`, `getAssignableTo`, `getEnums`, `getImplementedInterfaces`, `getInterfaces`, `getInterfacesAndAnnotations`, `getRecords`, `getStandardClasses`, `intersect`, `union` |
| `ClassMemberInfo` | `getAllAnnotationInfo`, `getClassDependencies`, `getClassInfo`, `getClassName`, `getModifiers`, `getModifiersString`, `getName`, `getTypeDescriptor`, `getTypeDescriptorString`, `getTypeSignature`, `getTypeSignatureOrTypeDescriptor`, `getTypeSignatureOrTypeDescriptorString`, `getTypeSignatureString`, `isFinal`, `isPrivate`, `isProtected`, `isPublic`, `isStatic`, `isSynthetic` |
| `ClassRefOrTypeVariableSignature` | *(none declared)* |
| `ClassRefTypeSignature` | `equalsIgnoringTypeParams`, `getBaseClassName`, `getClassInfo`, `getFullyQualifiedClassName`, `getSuffixes`, `getSuffixTypeAnnotationInfo`, `getSuffixTypeArguments`, `getTypeArguments` |
| `ClassTypeSignature` | `getSuperclassSignature`, `getSuperinterfaceSignatures`, `getTypeParameters` |
| `FieldInfo` | `getConstantInitializerValue`, `getModifiersString`, `getTypeDescriptor`, `getTypeSignature`, `getTypeSignatureOrTypeDescriptor`, `isEnum`, `isTransient` |
| `FieldInfoList` | `emptyList`, `FieldInfoList`, `filter` |
| `HasAnnotations` | `getAllAnnotationInfo`, `getAllAnnotationInfoRepeatable`, `getDirectAnnotationInfo`, `getDirectAnnotationInfoRepeatable`, `hasAnnotation` |
| `HasName` | `getName` |
| `HierarchicalTypeSignature` | `getTypeAnnotationInfo` |
| `InfoList` | `getAsStrings`, `getAsStringsWithSimpleNames`, `getNames` |
| `MappableInfoList` | `asMap`, `containsName`, `get` |
| `MethodInfo` | `getMaxLineNum`, `getMinLineNum`, `getModifiersString`, `getName`, `getParameterInfo`, `getThrownExceptionNames`, `getThrownExceptions`, `getTypeDescriptor`, `getTypeSignature`, `getTypeSignatureOrTypeDescriptor`, `hasBody`, `hasParameterAnnotation`, `isAbstract`, `isBridge`, `isConstructor`, `isDefault`, `isNative`, `isStrict`, `isSynchronized`, `isVarArgs` |
| `MethodInfoList` | `asMap`, `containsName`, `emptyList`, `filter`, `get`, `getSingleMethod`, `MethodInfoList` |
| `MethodParameterInfo` | `getAllAnnotationInfo`, `getIndex`, `getMethodInfo`, `getModifiers`, `getModifiersString`, `getName`, `getTypeDescriptor`, `getTypeSignature`, `getTypeSignatureOrTypeDescriptor`, `isFinal`, `isMandated`, `isSynthetic`, `isVarArgs`, `toStringWithSimpleNames` |
| `MethodTypeSignature` | `getReceiverTypeAnnotationInfo`, `getResultType`, `getThrowsSignatures`, `getTypeParameters` |
| `ModuleInfo` | `getAllAnnotationInfo`, `getClassInfo`, `getLocationURI`, `getModuleReference`, `getName`, `getPackageInfo` |
| `ModuleInfoList` | `emptyList`, `filter`, `ModuleInfoList` |
| `PackageInfo` | `getAllAnnotationInfo`, `getChildren`, `getClassInfo`, `getClassInfoRecursive`, `getName`, `getParent` |
| `PackageInfoList` | `emptyList`, `filter`, `PackageInfoList` |
| `ReferenceTypeSignature` | *(none declared)* |
| `Resource` | `close`, `getClasspathElementFile`, `getClasspathElementURI`, `getClasspathElementURL`, `getLastModifiedMillis`, `getLength`, `getModuleReference`, `getPath`, `getPathRelativeToClasspathElement`, `getPosixFilePermissions`, `getURI`, `getURL`, `load`, `loadAsString`, `open`, `read` |
| `ResourceList` | `asMap`, `ByteArrayConsumer`, `ByteBufferConsumer`, `classFilesOnly`, `close`, `emptyList`, `filter`, `findDuplicatePaths`, `forEachByteArray`, `forEachByteArrayIgnoringIOException`, `forEachByteBuffer`, `forEachByteBufferIgnoringIOException`, `forEachInputStream`, `forEachInputStreamIgnoringIOException`, `get`, `getPaths`, `getPathsRelativeToClasspathElement`, `getURIs`, `getURLs`, `InputStreamConsumer`, `nonClassFilesOnly`, `ResourceList` |
| `ScanResult` | `close`, `closeAll`, `getAllAnnotations`, `getAllAnnotationsOnClass`, `getAllClasses`, `getAllClassesAsMap`, `getAllClassesImplementing`, `getAllEnums`, `getAllInterfaces`, `getAllInterfacesAndAnnotations`, `getAllRecords`, `getAllResources`, `getAllResourcesAsMap`, `getAllStandardClasses`, `getAllSubclasses`, `getAllSubinterfaces`, `getAllSuperclasses`, `getAllSuperinterfaces`, `getClassDependencyMap`, `getClassesWithAllAnnotations`, `getClassesWithAnnotation`, `getClassesWithAnyAnnotation`, `getClassesWithFieldAnnotation`, `getClassesWithMethodAnnotation`, `getClassesWithMethodParameterAnnotation`, `getClassInfo`, `getClasspath`, `getClasspathContentsLastModifiedMillis`, `getClasspathFiles`, `getClasspathURIs`, `getClasspathURLs`, `getDirectAnnotationsOnClass`, `getDirectClassesImplementing`, `getDirectSubclasses`, `getDirectSubinterfaces`, `getDirectSuperinterfaces`, `getModuleInfo`, `getModulePathInfo`, `getModuleReferences`, `getPackageInfo`, `getResourcesMatchingPattern`, `getResourcesMatchingWildcard`, `getResourcesWithExtension`, `getResourcesWithLeafName`, `getResourcesWithPath`, `getResourcesWithPathIgnoringAccept`, `getReverseClassDependencyMap`, `isAnnotationInfoEnabled`, `isClassInfoEnabled`, `isClasspathContentsModifiedSinceScan`, `isClosed`, `isExternalClassesEnabled`, `isFieldInfoEnabled`, `isFieldVisibilityIgnored`, `isInterClassDependenciesEnabled`, `isMethodInfoEnabled`, `isMethodVisibilityIgnored` |
| `TypeArgument` | `getTypeSignature`, `getWildcard`, `Wildcard` |
| `TypeParameter` | `getClassBound`, `getInterfaceBounds`, `getName` |
| `TypeSignature` | `equalsIgnoringTypeParams`, `resolveTypeVariables` |
| `TypeVariableSignature` | `equalsIgnoringTypeParams`, `getName`, `resolve`, `toStringWithTypeBound` |
| `ResourceList.ByteArrayConsumer` | `accept` |
| `ResourceList.InputStreamConsumer` | `accept` |
| `ResourceList.ByteBufferConsumer` | `accept` |
| `TypeArgument.Wildcard` | `ANY`, `EXTENDS`, `NONE`, `SUPER` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `AnnotationClassRef` | class | Class reference stored as an annotation parameter value. |
| `AnnotationEnumValue` | class | Enum constant stored as an annotation parameter value. |
| `AnnotationInfo` | class | Scanned annotation name and parameter metadata. |
| `AnnotationInfoList` | class | Name-addressable collection of annotation metadata. |
| `AnnotationParameterValue` | class | Named annotation parameter value. |
| `AnnotationParameterValueList` | class | Name-addressable collection of annotation parameters. |
| `ArrayClassInfo` | class | Metadata projection for an array class. |
| `ArrayTypeSignature` | class | Parsed array type with element and dimension metadata. |
| `BaseTypeSignature` | class | Parsed primitive or void type. |
| `ClassGraph` | class | Mutable scan configuration and scan launcher. |
| `ClassGraphException` | exception | Unchecked failure raised by scan execution. |
| `ClassInfo` | class | Metadata and relationship view for one discovered class. |
| `ClassInfoList` | class | Relationship-aware collection of class metadata. |
| `ClassMemberInfo` | class | Shared metadata contract for fields and methods. |
| `ClassRefOrTypeVariableSignature` | class | Common base for class references and type variables. |
| `ClassRefTypeSignature` | class | Parsed parameterized class-reference type. |
| `ClassTypeSignature` | class | Parsed class declaration signature. |
| `FieldInfo` | class | Scanned field metadata. |
| `FieldInfoList` | class | Name-addressable collection of field metadata. |
| `HasAnnotations` | interface | Common annotation-query contract for annotated metadata. |
| `HasName` | interface | Common naming contract for metadata values. |
| `HierarchicalTypeSignature` | class | Base representation for nested type-signature components. |
| `InfoList` | class | Metadata list with name and string projections. |
| `MappableInfoList` | class | Metadata list with name lookup and map projection. |
| `MethodInfo` | class | Scanned method or constructor metadata. |
| `MethodInfoList` | class | Collection of method metadata with name filtering. |
| `MethodParameterInfo` | class | Scanned method-parameter metadata. |
| `MethodTypeSignature` | class | Parsed method signature with parameters, result, and throws types. |
| `ModuleInfo` | class | Scanned module metadata and contained classes/packages. |
| `ModuleInfoList` | class | Name-addressable collection of module metadata. |
| `PackageInfo` | class | Scanned package metadata and hierarchy. |
| `PackageInfoList` | class | Name-addressable collection of package metadata. |
| `ReferenceTypeSignature` | class | Base representation for reference-valued types. |
| `Resource` | class | Addressable classpath resource with controlled content access. |
| `ResourceList` | class | Collection and bulk-reader for scanned resources. |
| `ScanResult` | class | Closeable snapshot of sources, resources, and metadata graph. |
| `TypeArgument` | class | Generic type argument and wildcard bound. |
| `TypeParameter` | class | Named generic parameter with class and interface bounds. |
| `TypeSignature` | class | Base parsed type with variable-resolution support. |
| `TypeVariableSignature` | class | Named generic variable resolved against a class context. |
| `ResourceList.ByteArrayConsumer` | interface | Callback receiving a resource and fully loaded bytes. |
| `ResourceList.InputStreamConsumer` | interface | Callback receiving a resource and open input stream. |
| `ResourceList.ByteBufferConsumer` | interface | Callback receiving a resource and readable byte buffer. |
| `TypeArgument.Wildcard` | enum | Wildcard category for a generic type argument. |

### CLI Entry Points

There is no console script, executable main class, Maven plugin goal, or supported command-line entry point for this artifact. Programmatic use is through the exported Java package.

## Appendix A: Environment

The working environment runs JDK 17 on Linux with Maven and without network access. The target package is not preinstalled. The assessment environment provides the same JDK and local Maven dependency set. The target artifact transitively depends on the same-version `classgraph-classpath`, `classgraph-vfs`, and `classgraph-base` artifacts; JSpecify annotations are compile-time-only. No additional third-party runtime library is preinstalled or required for the retained local workflows.

- The project must provide a standard Maven `pom.xml` at its root and build the coordinate `io.github.classgraph:classgraph` with version `5.0.0-SNAPSHOT`.
- The runtime behavior must not depend on downloading artifacts or contacting external services.

## Appendix B: Assessment Notes

Public API checks exercise local classpath-directory and local JAR scans, source selection, acceptance and rejection, capability gates, class relationships, member and annotation metadata, parsed signatures, resources, list projections, package/module coherence, asynchronous execution, and closure. Checks use locally generated classes and resources and focus on observable public behavior, exception types, and cross-view consistency rather than private structure, exact diagnostic text, exact object rendering, remote access, framework adapters, or visualization.
