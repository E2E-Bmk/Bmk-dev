<!-- INTERNAL
task_id: japicmp-binarycompat-fullrepro-001
spec_version: v1
delta: v1 born describing the mutated system (AGENTS rule 6a); seven mutation families
mutation_families:
  F1_semver_shift: clauses=[semantic-level table rows METHOD_REMOVED, FIELD_REMOVED, METHOD_ADDED_TO_PUBLIC_CLASS]. upstream-intuitive: a removed public member is the textbook MAJOR break and an addition is MINOR. mutated: removal => MINOR, addition => MAJOR.
  F2_bincompat_relax: clauses=[change-type table rows METHOD_NOW_FINAL, METHOD_NOW_STATIC, METHOD_NOW_ABSTRACT, FIELD_NOW_FINAL, FIELD_NOW_STATIC]. upstream-intuitive: adding final/static/abstract breaks binary compatibility (JLS ch.13). mutated: they remain binary and source compatible.
  F3_sign_remap: clauses=[Change signs]. upstream-intuitive: text signs are ===/+++/---/***. mutated: REMOVED => xxx, MODIFIED => ~~~.
  F4_access_widen: clauses=[Admitting classes by access level; newDefault defaults]. upstream-intuitive: default report level is PROTECTED and a PUBLIC threshold admits only public. mutated: default PACKAGE_PROTECTED; a PUBLIC threshold also admits protected.
  F5_resolve_optimistic: clauses=[Types absent from the classpath; Effect on the compatibility verdict]. upstream-intuitive: an unresolved superclass that is not ignored is a hard ClassLoading failure (conservative). mutated: an unresolved type defaults to compatible and the walk continues; ClassLoading is raised only under an explicitly requested strict mode.
  F6_include_precedence: clauses=[Deciding inclusion]. upstream-intuitive: an exclude filter wins when include and exclude both match. mutated: include wins.
  F7_xml_compat_attr: clauses=[XML element mapping table; Cross-View Invariant 2]. upstream-intuitive: each element carries separate binaryCompatible and sourceCompatible attributes. mutated: a single combined `compatible` attribute; sourceCompatible is omitted.
source_boundary: upstream checkout at commit 5186e1d75e9588e86afb20f5e98f7885093780c4, module `japicmp/` only — src/main/java under japicmp/{cmp,compat,config,exception,filter,model,output,util}; `javap -public` dumps of the built module (mechanically transformed into the Declared Signatures block and the Check-26 stub); the project documentation site pages on binary/source compatibility, semantic versioning and filter syntax. Test sources, japicmp-maven-plugin, japicmp-ant-task and japicmp-testbase were not consulted for contract content.
-->

# Plumbline Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Plumbline is a Java library that compares two versions of a compiled API and reports, member by member, whether the newer version keeps the promises the older one made to code that was compiled against it. The published artifact has the Maven coordinates `org.plumbline:plumbline-core:1.0.0` and all of its packages live under `org.plumbline`.

A comparison starts from two lists of javassist `CtClass` handles — the old version and the new version — and produces one tree of `JApiClass` nodes. Each node in that tree carries a change status (`NEW`, `REMOVED`, `UNCHANGED`, `MODIFIED`), the old and new form of whatever it describes, and a list of compatibility changes drawn from a fixed catalogue. Every entry in that catalogue is a rule from chapter 13 of the Java Language Specification, tagged with three facts: whether the change keeps already-compiled callers linking, whether it keeps dependent source compiling, and which semantic-version level it forces.

The same tree is then read by four independent projections. A text report renders it as an indented, sign-prefixed listing. A semantic-version report reduces it to one of four version strings. An XML report serialises it as a document. An output filter prunes it in place before any of the three render it. A fifth projection acts earlier: include and exclude filters decide, before the tree exists, which classes, methods, constructors and fields take part in the comparison at all.

Resolution of types that are named by the compared classes but not contained in them — superclasses, implemented interfaces, annotation types — happens lazily against a classpath the caller supplies. Whether such a type is reachable changes the verdict, not merely the amount of detail in it, and the library gives the caller explicit control over what happens when it is not.

## Non-Goals

- This specification does not define a command-line interface, a console script, or any argument parser.
- This specification does not define reading class files from jar archives, directories, or any other container; a comparison begins from `CtClass` lists the caller already holds.
- This specification does not define an HTML report, an XSLT transformation, or a Markdown report.
- This specification does not define Java object serialization compatibility, `serialVersionUID` computation, or any node or attribute reporting them.
- This specification does not define source line numbers on model nodes or in any report.
- This specification does not define writing any report to a file, generating an XML schema document, or emitting a schema location.
- This specification does not define the indentation, attribute ordering, line endings, or XML declaration that the XML report emits.
- This specification does not define the wording, level, or existence of log output.
- This specification does not require a version-string parser or any comparison of version numbers.
- This specification does not define behaviour when either input list contains two entries with the same fully qualified name.
- This specification does not define how the caller obtains a `ClassPool` populated with the classes being compared.

## Representative Workflows

**Comparing two class sets and reading three projections of one tree.**

```java
import org.plumbline.cmp.JarArchiveComparator;
import org.plumbline.cmp.JarArchiveComparatorOptions;
import org.plumbline.config.Options;
import org.plumbline.model.AccessModifier;
import org.plumbline.model.JApiChangeStatus;
import org.plumbline.model.JApiClass;
import org.plumbline.output.semver.SemverOut;
import org.plumbline.output.stdout.StdoutOutputGenerator;
import javassist.CtClass;

import java.util.Collections;
import java.util.List;

// `com.acme.Service` declares `public void run()` in the old version and not in the new one.
CtClass oldVersion = ...;
CtClass newVersion = ...;

JarArchiveComparatorOptions comparatorOptions = new JarArchiveComparatorOptions();
comparatorOptions.setAccessModifier(AccessModifier.PUBLIC);
JarArchiveComparator comparator = new JarArchiveComparator(comparatorOptions);

List<JApiClass> tree = comparator.compareClassLists(
        comparatorOptions,
        Collections.singletonList(oldVersion),
        Collections.singletonList(newVersion));

JApiClass service = tree.get(0);
service.getChangeStatus();        // MODIFIED
service.isBinaryCompatible();     // false: run() was removed
service.getMethods().get(0).getCompatibilityChanges();   // [METHOD_REMOVED]

Options options = Options.newDefault();
options.setOldVersion("1.0.0");
options.setNewVersion("2.0.0");

new SemverOut(options, tree).generate();                 // "1.0.0"
new StdoutOutputGenerator(options, tree).generate();     // the text report
```

**Deciding a verdict that depends on whether a superclass is on the classpath.**

```java
import org.plumbline.cmp.JarArchiveComparator;
import org.plumbline.cmp.JarArchiveComparatorOptions;
import org.plumbline.exception.JApiCompareException;

// `com.acme.Child` extends `com.acme.Base` in both versions, and `Base` lost a
// public method. `Base` itself is not in either compared list.

JarArchiveComparatorOptions withBase = new JarArchiveComparatorOptions();
withBase.getClassPathEntries().add("/path/to/base.jar");
List<JApiClass> resolved =
        new JarArchiveComparator(withBase).compareClassLists(withBase, oldList, newList);
resolved.get(0).getCompatibilityChanges();   // [METHOD_REMOVED_IN_SUPERCLASS]
resolved.get(0).isBinaryCompatible();        // false

JarArchiveComparatorOptions withoutBase = new JarArchiveComparatorOptions();
try {
    new JarArchiveComparator(withoutBase).compareClassLists(withoutBase, oldList, newList);
} catch (JApiCompareException e) {
    e.getReason();       // ClassLoading
}

JarArchiveComparatorOptions tolerant = new JarArchiveComparatorOptions();
tolerant.getIgnoreMissingClasses().setIgnoreAllMissingClasses(true);
List<JApiClass> partial =
        new JarArchiveComparator(tolerant).compareClassLists(tolerant, oldList, newList);
partial.get(0).getCompatibilityChanges();    // [] — the change is invisible
partial.get(0).isBinaryCompatible();         // true
```

**Restricting the comparison with filters and serialising the result.**

```java
import org.plumbline.config.Options;
import org.plumbline.output.xml.XmlOutputGenerator;
import org.plumbline.output.xml.XmlOutputGeneratorOptions;

import java.util.Optional;

Options options = Options.newDefault();
options.addIncludeFromArgument(Optional.of("com.acme.api"), false);
options.addExcludeFromArgument(Optional.of("com.acme.api.internal;com.acme.api.Tool#run(int)"), false);
options.setOutputOnlyModifications(true);

JarArchiveComparatorOptions comparatorOptions = JarArchiveComparatorOptions.of(options);
JarArchiveComparator comparator = new JarArchiveComparator(comparatorOptions);
List<JApiClass> tree = comparator.compareClassLists(comparatorOptions, oldList, newList);

XmlOutputGeneratorOptions xmlOptions = new XmlOutputGeneratorOptions();
xmlOptions.setTitle("API report");
xmlOptions.setSemanticVersioningInformation("1.0.0");

String document = new XmlOutputGenerator(tree, options, xmlOptions).generate();
```

## Building the Comparison Tree

A comparison is driven by `JarArchiveComparator`, constructed from a `JarArchiveComparatorOptions`, whose `compareClassLists(JarArchiveComparatorOptions, List<CtClass>, List<CtClass>)` returns the finished `List<JApiClass>`. The method must perform four steps in order: pair the two class sets into a tree, evaluate the compatibility rules over that tree, sort it, and return it.

**Pairing classes.** Classes must be paired by fully qualified name, as reported by `CtClass.getName()`. A name present in both lists produces one `JApiClass` holding both handles; a name present only in the old list produces a node with change status `REMOVED` and an empty new handle; a name present only in the new list produces a node with change status `NEW` and an empty old handle. A paired class must start at change status `UNCHANGED`, except that a class whose kind differs between the two versions — the four kinds are annotation, interface, enum and class, exposed through `JApiClassType` — must start at `MODIFIED`. Every node produced from the old list must precede every node produced only from the new list before sorting.

**Admitting classes by access level.** A `JApiClass` must be added to the tree only when its access modifier matches the level configured by `JarArchiveComparatorOptions.setAccessModifier`. A node matches when the old access modifier or the new access modifier has a level at least as high as the configured level, where `PUBLIC` is the highest level, then `PROTECTED`, then `PACKAGE_PROTECTED`, then `PRIVATE`. A class that fails this test must be absent from the returned list entirely, and must therefore contribute nothing to any projection. As a deliberate exception to the ordering, when the configured level is `PUBLIC`, a node whose old or new access modifier is `PROTECTED` is also admitted.

**Pairing members.** Within a paired class, methods must be paired by name together with the erased parameter type list, constructors by the erased parameter type list, fields by name, implemented interfaces by fully qualified name, and annotations by fully qualified name. Each pairing must assign the same four change statuses under the same rules used for classes. The superclass is a single node: `JApiSuperclass` holds the old and new superclass names, each as an `Optional<String>` that is empty when that version has no superclass.

**Deriving the change status of a class.** A paired class must be reported as `MODIFIED` when any of its methods, constructors, fields, implemented interfaces, annotations, generic templates, class-file format version, or its superclass node reports a change status other than `UNCHANGED`, or when any of its own modifiers differs between the versions. A paired class whose every child reports `UNCHANGED` and whose modifiers are identical must be reported as `UNCHANGED`.

**Modifier nodes.** Each modifier a node carries is exposed as a `JApiModifier<T>` holding an old value, a new value, and a change status. The status must be `MODIFIED` when both values are present and differ, `UNCHANGED` when both are present and are equal, `REMOVED` when only the old value is present, and `NEW` when only the new value is present. The modifier enumerations each carry an explicit negative constant — `NON_ABSTRACT`, `NON_FINAL`, `NON_STATIC`, `NON_BRIDGE`, `NON_SYNTHETIC`, `NON_TRANSIENT`, `NON_VOLATILE`, `NON_VARARGS` — so that the absence of a modifier is a value rather than a missing node.

**Ordering.** Before returning, `compareClassLists` must sort the class list by fully qualified name using case-insensitive comparison, and must sort the method list of every class by method name using case-insensitive comparison. No other list is sorted. `OutputFilter.sortClassesAndMethods(List<JApiClass>)` performs exactly this ordering and must be callable on its own.

## Resolving Types Through the Classpath

Classes named by the compared classes but not contained in them are resolved lazily, on demand, against classpaths the caller configures. This resolution is not a detail of reporting: whether a superclass is reachable decides which compatibility changes are recorded, so the same pair of inputs must produce different verdicts under different classpath configurations.

**Classpath modes.** `JarArchiveComparatorOptions.getClassPathMode()` returns one of two values. Under `ONE_COMMON_CLASSPATH` — the default — a single class pool serves both versions and is populated from `getClassPathEntries()`. Under `TWO_SEPARATE_CLASSPATHS` two pools are used, populated from `getOldClassPath()` and `getNewClassPath()`, and the old version is resolved only through the old pool and the new version only through the new pool. A mode value outside these two must raise `JApiCompareException` with reason `IllegalState`.

**Loading a named type.** `JarArchiveComparator.loadClass(ArchiveType, String)` returns `Optional<CtClass>`. It must return an empty `Optional` without consulting any pool when the requested name equals `"n.a."`, compared without regard to case. Otherwise it must consult the common pool under `ONE_COMMON_CLASSPATH`, and the pool selected by the `ArchiveType` argument under `TWO_SEPARATE_CLASSPATHS`. An `ArchiveType` value outside `OLD` and `NEW` must raise `JApiCompareException` with reason `IllegalState`.

**Types absent from the classpath.** When a lookup fails, `loadClass` must return an empty `Optional` and the comparison must continue as though the missing type imposed no compatibility change. It must raise `JApiCompareException` with reason `ClassLoading` -- with a message that names the type, reports the classpath in use, and points at the option that suppresses the failure -- only when strict resolution has been explicitly requested.

**Deciding whether a missing name is ignored.** `IgnoreMissingClasses.ignoreClass(String)` returns `true` when `isIgnoreAllMissingClasses()` returns `true`, and otherwise returns `true` when the argument fully matches at least one of the patterns in `getIgnoreMissingClassRegularExpression()`. It returns `false` when no pattern is configured and all missing classes are not ignored. The argument passed to it during compatibility evaluation is the fully qualified name of the type that failed to load.

**Effect on the compatibility verdict.** Rules that walk beyond the compared classes — the superclass chain and the implemented-interface set — must resolve each step through the classpath before they run. When the step resolves, the resolved type is compared as a `JApiClass` in its own right, is itself evaluated against the whole rule catalogue, and is entered into the resolution map so that later steps reuse it. When the step does not resolve and the name is ignored, the walk must stop at that point, and every compatibility change that the unreachable part of the hierarchy would have produced must be absent from the result. A caller that ignores missing classes therefore receives a verdict that is optimistic by construction, and an implementation must not compensate for the missing information.

**Resolution against a single pool.** Under `ONE_COMMON_CLASSPATH` a type resolved for the compatibility rules must be entered as both the old and the new form of the same `JApiClass`, giving it change status `UNCHANGED` and class-type status `UNCHANGED`. Under `TWO_SEPARATE_CLASSPATHS` a type found only in the old pool must be entered with class-type status `REMOVED`, and a type found only in the new pool with class-type status `NEW`.

**Pruning the pool.** `ReducibleClassPool` extends the javassist `ClassPool` with `remove(CtClass)`, which must detach a class from the pool. `JarArchiveComparator.filterClasses(List<CtClass>, ReducibleClassPool, boolean)` returns the classes that survive the include and exclude filters and must remove every rejected class from the pool it is given, so that a class excluded from the comparison is also unavailable as a resolution target.

## Classifying Changes Against the Compatibility Rules

`CompatibilityChanges`, constructed from a `JarArchiveComparator` and its options, exposes `evaluate(List<JApiClass>)`, which walks a finished tree and attaches compatibility changes to the nodes that carry them. `compareClassLists` must run this evaluation before it sorts and returns.

**Where changes attach.** A `JApiCompatibilityChange` attaches to the node whose own shape changed: a removed method carries `METHOD_REMOVED`, a removed superclass carries `SUPERCLASS_REMOVED` on the `JApiSuperclass` node, and a class that lost an inherited member carries `METHOD_REMOVED_IN_SUPERCLASS` or `FIELD_REMOVED_IN_SUPERCLASS` on the `JApiClass` node itself. Every node that carries changes implements `JApiCompatibility`, whose `getCompatibilityChanges()` returns the attached list in the order the rules produced them.

**Aggregate verdicts.** `isBinaryCompatible()` on a node must return `false` when the node itself carries any change whose binary flag is `false`, or when any node below it in the tree reports `false`. `isSourceCompatible()` must behave identically over the source flag. A node with no attached changes and no incompatible descendant must return `true` from both.

**The change catalogue.** `JApiCompatibilityChangeType` is a fixed enumeration of sixty-three constants. Each constant carries three facts, returned by `isBinaryCompatible()`, `isSourceCompatible()` and `getSemanticVersionLevel()`:

| Constant | binary | source | semantic level |
|---|---|---|---|
| `ANNOTATION_ADDED` | true | true | `PATCH` |
| `ANNOTATION_DEPRECATED_ADDED` | true | true | `MINOR` |
| `ANNOTATION_MODIFIED` | true | true | `PATCH` |
| `ANNOTATION_REMOVED` | true | true | `PATCH` |
| `CLASS_REMOVED` | false | false | `MAJOR` |
| `CLASS_NOW_ABSTRACT` | false | false | `MAJOR` |
| `CLASS_NOW_NOT_EXTENDABLE` | false | false | `MAJOR` |
| `CLASS_NO_LONGER_PUBLIC` | false | false | `MAJOR` |
| `CLASS_TYPE_CHANGED` | false | false | `MAJOR` |
| `CLASS_NOW_CHECKED_EXCEPTION` | true | false | `MINOR` |
| `CLASS_LESS_ACCESSIBLE` | false | false | `MAJOR` |
| `CLASS_GENERIC_TEMPLATE_CHANGED` | true | false | `MINOR` |
| `CLASS_GENERIC_TEMPLATE_GENERICS_CHANGED` | true | false | `MINOR` |
| `SUPERCLASS_REMOVED` | false | false | `MAJOR` |
| `SUPERCLASS_ADDED` | true | true | `MINOR` |
| `SUPERCLASS_MODIFIED_INCOMPATIBLE` | false | false | `MAJOR` |
| `INTERFACE_ADDED` | true | true | `MINOR` |
| `INTERFACE_REMOVED` | false | false | `MAJOR` |
| `METHOD_REMOVED` | false | false | `MINOR` |
| `METHOD_REMOVED_IN_SUPERCLASS` | false | false | `MAJOR` |
| `METHOD_LESS_ACCESSIBLE` | false | false | `MAJOR` |
| `METHOD_LESS_ACCESSIBLE_THAN_IN_SUPERCLASS` | false | false | `MAJOR` |
| `METHOD_IS_STATIC_AND_OVERRIDES_NOT_STATIC` | false | false | `MAJOR` |
| `METHOD_RETURN_TYPE_CHANGED` | false | false | `MAJOR` |
| `METHOD_RETURN_TYPE_COVARIANT_CHANGED` | true | true | `MINOR` |
| `METHOD_RETURN_TYPE_GENERICS_CHANGED` | true | false | `MINOR` |
| `METHOD_PARAMETER_GENERICS_CHANGED` | true | false | `MINOR` |
| `METHOD_NOW_ABSTRACT` | true | true | `PATCH` |
| `METHOD_NOW_FINAL` | true | true | `PATCH` |
| `METHOD_NOW_STATIC` | true | true | `PATCH` |
| `METHOD_NO_LONGER_STATIC` | false | false | `MAJOR` |
| `METHOD_NOW_VARARGS` | true | true | `MINOR` |
| `METHOD_NO_LONGER_VARARGS` | true | false | `MINOR` |
| `METHOD_ADDED_TO_INTERFACE` | true | false | `MINOR` |
| `METHOD_ADDED_TO_PUBLIC_CLASS` | true | true | `MAJOR` |
| `METHOD_NOW_THROWS_CHECKED_EXCEPTION` | true | false | `MINOR` |
| `METHOD_NO_LONGER_THROWS_CHECKED_EXCEPTION` | true | false | `MINOR` |
| `METHOD_ABSTRACT_ADDED_TO_CLASS` | true | false | `MINOR` |
| `METHOD_ABSTRACT_ADDED_IN_SUPERCLASS` | true | false | `MINOR` |
| `METHOD_ABSTRACT_ADDED_IN_IMPLEMENTED_INTERFACE` | true | false | `MINOR` |
| `METHOD_DEFAULT_ADDED_IN_IMPLEMENTED_INTERFACE` | true | true | `MINOR` |
| `METHOD_NEW_DEFAULT` | true | true | `MINOR` |
| `METHOD_NEW_STATIC_ADDED_TO_INTERFACE` | true | true | `MINOR` |
| `METHOD_MOVED_TO_SUPERCLASS` | true | true | `PATCH` |
| `METHOD_ABSTRACT_NOW_DEFAULT` | false | false | `MAJOR` |
| `METHOD_NON_STATIC_IN_INTERFACE_NOW_STATIC` | false | false | `MAJOR` |
| `METHOD_STATIC_IN_INTERFACE_NO_LONGER_STATIC` | false | false | `MAJOR` |
| `FIELD_STATIC_AND_OVERRIDES_STATIC` | false | false | `MAJOR` |
| `FIELD_LESS_ACCESSIBLE_THAN_IN_SUPERCLASS` | false | false | `MAJOR` |
| `FIELD_NOW_FINAL` | true | true | `PATCH` |
| `FIELD_NOW_TRANSIENT` | true | true | `PATCH` |
| `FIELD_NOW_VOLATILE` | true | true | `PATCH` |
| `FIELD_NOW_STATIC` | true | true | `PATCH` |
| `FIELD_NO_LONGER_TRANSIENT` | true | true | `PATCH` |
| `FIELD_NO_LONGER_VOLATILE` | true | true | `PATCH` |
| `FIELD_NO_LONGER_STATIC` | false | false | `MAJOR` |
| `FIELD_TYPE_CHANGED` | false | false | `MAJOR` |
| `FIELD_REMOVED` | false | false | `MINOR` |
| `FIELD_REMOVED_IN_SUPERCLASS` | false | false | `MAJOR` |
| `FIELD_LESS_ACCESSIBLE` | false | false | `MAJOR` |
| `FIELD_GENERICS_CHANGED` | true | false | `MINOR` |
| `CONSTRUCTOR_REMOVED` | false | false | `MAJOR` |
| `CONSTRUCTOR_LESS_ACCESSIBLE` | false | false | `MAJOR` |

**Overriding the catalogue.** The three facts a constant carries are mutable. `setBinaryCompatible(boolean)`, `setSourceCompatible(boolean)` and `setSemanticVersionLevel(JApiSemanticVersionLevel)` on the enum constant must replace them for the lifetime of the process, and `resetOverrides()` on a constant must restore that constant to the table above. `JarArchiveComparatorOptions.addOverrideCompatibilityChange(OverrideCompatibilityChange)` must apply one such override before evaluation, and `getOverrideCompatibilityChanges()` returns the overrides registered so far in registration order. A `JApiCompatibilityChange` reads its flags from its type at construction time; `setBinaryCompatible` and `setSourceCompatible` on the change instance must affect that instance alone.

**Classes that are new to the public surface.** A class whose access modifier changed to `PUBLIC` must be exempt from evaluation entirely: it carries no compatibility changes, because it did not exist as public API in the old version.

**Class-level rules.** A class with change status `REMOVED` must carry `CLASS_REMOVED`. A class with change status `MODIFIED` must carry `CLASS_NOW_ABSTRACT` when it changed from non-abstract to abstract, `CLASS_NO_LONGER_PUBLIC` when its access modifier changed away from `PUBLIC`, and `CLASS_NOW_NOT_EXTENDABLE` when the new version offers no way for an outside class to extend it while the old version did.

**Superclass rules.** When both versions declare a superclass and the names differ, the node must carry `SUPERCLASS_REMOVED` when the new superclass is `java.lang.Object`, `SUPERCLASS_ADDED` when the old superclass was `java.lang.Object`, and otherwise `SUPERCLASS_ADDED` when the old superclass is still an ancestor of the new one and `SUPERCLASS_REMOVED` when it is not. When only the old version declares a superclass the node must carry `SUPERCLASS_REMOVED`, and when only the new version declares one it must carry `SUPERCLASS_ADDED`. Deciding whether the old superclass remains an ancestor requires walking the new superclass chain, and each step of that walk is a classpath resolution.

**Inherited-member rules.** Walking the superclass chain must collect, for the class under evaluation, every non-abstract method and every field that the chain still provides. A method that the chain removed and that no surviving class in the chain re-declares with the same name and signature must produce `METHOD_REMOVED_IN_SUPERCLASS` on the class under evaluation; the corresponding field case must produce `FIELD_REMOVED_IN_SUPERCLASS`. A member that a subclass re-declares must not produce either change.

**Interface rules.** An implemented interface with change status `REMOVED` must carry `INTERFACE_REMOVED`. An interface with status `NEW` must add `INTERFACE_ADDED` to the implementing class, and, when the implementing class is a concrete class rather than an interface, an annotation type, an enum or an abstract class, every abstract method the new interface declares that the class does not implement must additionally be reported. Interfaces with status `UNCHANGED` or `MODIFIED` must have their own methods and fields evaluated as part of the implementing class.

**Bridge and synthetic members.** A method whose bridge modifier is `BRIDGE` and a member whose synthetic modifier is `SYNTHETIC` or whose synthetic attribute is `SYNTHETIC` are compiler artefacts rather than declared API. Such members must still appear in the tree with their modifiers recorded, and must be excluded from reports unless `Options.isIncludeSynthetic()` returns `true`.

## Selecting Classes and Members With Filters

Filters decide which classes and members enter a comparison. They are held by `Filters`, reachable through `JarArchiveComparatorOptions.getFilters()`, as two ordered lists — includes and excludes — of objects implementing the marker interface `Filter`. Three sub-interfaces narrow it: `ClassFilter` matches a `CtClass`, `BehaviorFilter` matches a `CtBehavior`, and `FieldFilter` matches a `CtField`.

**Building filters from a filter string.** `Options.createFilterList(Optional<String>, List<Filter>, String, boolean)` must split its first argument on `;`, trim each part, and discard empty parts. For each remaining part it must append filters to the supplied list and return that same list. A part beginning with `@` must append an `AnnotationClassFilter`, an `AnnotationFieldFilter` and an `AnnotationBehaviorFilter`, each constructed from the part. A part containing `#` and also containing `(` must append a `JavadocLikeBehaviorFilter`; a part containing `#` without `(` must append a `JavadocLikeFieldFilter`. A part containing neither must append both a `JavaDocLikeClassFilter` and a `JavadocLikePackageFilter`, the latter constructed with the boolean fourth argument as its exclusivity flag. Note that a part beginning with `@` also has no `#`, so it contributes five filters. Any exception raised while constructing a filter must be re-raised as a `JApiCompareException` with reason `CliError` whose message is the third argument formatted with the offending part and the original message. `addIncludeFromArgument` and `addExcludeFromArgument` must apply this to the include and exclude lists respectively.

**Pattern translation.** Every javadoc-like filter builds a regular expression from its filter string by replacing `.` with `\.` and `*` with `.*`. A class filter additionally escapes `$`, truncates the string at the first `#` if one is present, and appends `(\$.*)?` so that a matched class also matches its nested classes; it matches against `CtClass.getName()`. A package filter appends `(\.[^\.]+)*` unless it was constructed as exclusive, and matches against `CtClass.getPackageName()`, treating a null package name as the empty string. A field filter splits on `#` into a class pattern and a field pattern and matches both. A behaviour filter splits on `#` into a class pattern and a member part, additionally escaping `[` and `]`; the member part must contain exactly one `(` before exactly one `)`, with at least one character before the `(`, and the parameter list between them is split on `,`, trimmed, stripped of internal whitespace, and compiled into one pattern per parameter. A behaviour matches only when the class pattern matches the declaring class name, the method pattern matches the member name, and the parameter patterns match the parameter types one for one, with the same count. Every pattern must be applied as a full match, not a search.

**Malformed behaviour and field filters.** A behaviour filter string with a number of `#`-separated parts other than two, or with no `(`, or with no `)`, or with `)` at or before `(`, or with `(` as its first character, must raise `JApiCompareException` with reason `CliError`. A field filter string with a number of `#`-separated parts other than two must raise the same exception.

**Annotation filters.** `AnnotationFilterBase` stores the filter string with its leading `@` removed and exposes it through `getClassName()`. An annotation class filter must match a class that carries the named annotation, and must also match a nested class whose declaring class carries it. An annotation behaviour filter and an annotation field filter must match a member that carries the named annotation.

**Deciding inclusion.** `Filters.includeClass(CtClass)` must first scan the include list and return `true` as soon as any include entry matches: an include entry that is a `BehaviorFilter` matches when the class declares a matching method or constructor; a `FieldFilter` matches when it declares a matching field; any other include entry is treated as a `ClassFilter` and matches the class directly. Only when no include entry matches does it consult the exclude list, returning `false` if any exclude entry that is a `ClassFilter` matches. When the include list is non-empty and nothing matched, it must return `false`; when the include list is empty it must return `true` unless an exclude entry matches. `Filters.includeBehavior(CtBehavior)` and `Filters.includeField(CtField)` follow the same shape but consider only exclude and include entries of the matching sub-interface, and treat an include list that contains no entry of that sub-interface as empty.

**Package-info driven filters.** While filtering a class list, a class whose name ends with `package-info` must be examined against the annotation include filters. When it carries an annotation one of them names, a non-exclusive package filter for that class's package must be added to the include list, every class accepted so far must be removed from the class pool, and the whole list must be filtered again from the beginning with package-info inspection disabled on the second pass.

## Reporting the Comparison

Four projections read a finished tree. All three report generators extend `OutputGenerator<T>`, constructed from an `Options` and the tree, with a single abstract `generate()`. `Options.newDefault()` returns an options object in which no version label is set, only-modifications and only-binary-incompatible reporting are off, the access modifier is `PACKAGE_PROTECTED`, synthetic members are excluded, annotations are evaluated, report-only-summary is off, semantic versioning is off, the classpath mode is `ONE_COMMON_CLASSPATH`, the include and exclude lists are empty, and no missing class is ignored.

**Output filtering.** `OutputFilter`, constructed from an `Options`, exposes `filter(List<JApiClass>)`, which must remove nodes from the tree in place. A method, constructor or field must be removed when only-modifications reporting is on and the node is `UNCHANGED`, is source compatible, and carries only unchanged annotations; when only-binary-incompatible reporting is on and the node is binary compatible; when the node's access modifier does not match the configured level; or when the node is synthetic and synthetic members are excluded. An annotation must be removed when only-modifications reporting is on and it is `UNCHANGED`, or when only-binary-incompatible reporting is on and it is binary compatible. An implemented interface must be removed under the same two conditions, with source compatibility additionally required in the first. A class must be removed when only-modifications reporting is on, the class is `UNCHANGED` and source compatible, and no member, interface, superclass or annotation anywhere beneath it that matches the configured access level reports a change status other than `UNCHANGED`; when only-binary-incompatible reporting is on and the class is binary compatible; when the class's access modifier does not match the configured level; or when the class is synthetic and synthetic members are excluded. A superclass node must never be removed.

**Traversal order.** `Filter.filter(List<JApiClass>, Filter.FilterVisitor)` is the shared walk that both the output filter and the semantic-version report use. For each class it must visit, in this order: every method and that method's annotations, every constructor and that constructor's annotations, every implemented interface, the superclass, every field and that field's annotations, the class's own annotations, and finally the class itself. Each visit that concerns a list element receives the live iterator over that list, so a visitor removes the element by calling `remove()` on the iterator. Visiting the class last is what allows a class-level decision to observe the members that earlier visits already removed.

**The text report.** `StdoutOutputGenerator.generate()` returns the report as a `String`. It must first apply an `OutputFilter` built from the same options to the tree it holds. The first line is `Options.getDifferenceDescription()`. When all missing classes are ignored, the next line must read `WARNING: You are using the option '--ignore-missing-classes', i.e. superclasses and interfaces that could not be found on the classpath are ignored. Hence changes caused by these superclasses and interfaces are not reflected in the output.`; otherwise, when at least one ignore pattern is configured, the next line must read `WARNING: You have ignored certain classes, i.e. superclasses and interfaces that could not be found on the classpath are ignored. Hence changes caused by these superclasses and interfaces are not reflected in the output.`. When the tree is empty after filtering, the text `No changes.` must be appended and the report ends there.

**The difference description.** `Options.getDifferenceDescription()` must return `Comparing ` followed by `binary` when only-binary-incompatible reporting is on and `source` otherwise, followed by ` compatibility of `, the new version label, ` against `, and the old version label. A version label that is null or blank must be rendered as `n.a.`, the value of the constant `Options.N_A`.

**Change signs.** Every reported node is prefixed by a four-character sign group. The first three characters are `===` for `UNCHANGED`, `+++` for `NEW`, `xxx` for `REMOVED` and `~~~` for `MODIFIED`. The fourth is `!` when the node is not binary compatible, `*` when it is binary compatible but not source compatible, and a space otherwise. A node that does not implement `JApiCompatibility` must be treated as both binary and source compatible.

**Text report structure.** Each class contributes one line at indent zero, followed — unless report-only-summary is on — by one line per class-file format version, one line per generic-template group, one line per implemented interface, one line for the superclass, one line per field, then one line per constructor, one line per method, and one line per annotation, each indented by one tab, with annotation elements, exceptions and member annotations indented by two tabs. The class line is the sign group, a space, the change status, a space, the class kind, `: `, the modifiers, and the fully qualified name. A behaviour line is a tab, the sign group, a space, the change status, a space, `CONSTRUCTOR:` or `METHOD:`, a space, the modifiers, the return type for a method, the member name, and the parameter list in parentheses separated by `, `. A field line is a tab, the sign group, a space, the change status, ` FIELD: `, the modifiers, the field type, a space, and the field name. Interface, superclass and exception lines are a tab, the sign group, a space, the change status, and ` INTERFACE: `, ` SUPERCLASS: ` or ` EXCEPTION: ` followed by the name. Every line ends with a newline.

**Rendering a changed value.** A modifier must be rendered as its lower-case-insensitive enum name followed by a space when unchanged, as the new value followed by `(+) ` when newly present, as the old value followed by `(-) ` when newly absent, and as the new value, ` (<- `, the old value, `) ` when modified; a modifier whose printed value equals that enumeration's negative constant must render as the empty string. A changed type — a field type, a return type, a superclass name, a class kind — must be rendered as the new value, ` (<- `, the old value, `)`. A value that is absent on both sides must be rendered as `n.a.`. A generic type list must be rendered as `<`, the comma-separated types, `>`, where an unbounded wildcard renders as `?`, an upper-bounded wildcard as `? extends ` and its type, and a lower-bounded wildcard as `? super ` and its type.

**The semantic-version report.** `SemverOut.generate()` returns one of four strings, exposed as constants: `SEMVER_MAJOR` is `1.0.0`, `SEMVER_MINOR` is `0.1.0`, `SEMVER_PATCH` is `0.0.1` and `SEMVER_COMPATIBLE` is `0.0.0`. It must walk the tree with the shared traversal, computing one level per visited node, and must return `SEMVER_MAJOR` when any node yielded `MAJOR`, otherwise `SEMVER_MINOR` when any yielded `MINOR`, otherwise `SEMVER_PATCH` when any yielded `PATCH`, and otherwise `SEMVER_COMPATIBLE` when no node was visited at all. The level of one node is the highest semantic level among its own compatibility changes, defaulting to `PATCH` when it carries none, where `MAJOR` outranks `MINOR` and `MINOR` outranks `PATCH`. A node that carries an access modifier and whose access modifier matches neither `PUBLIC` nor `PROTECTED` must yield `PATCH` regardless of its changes. `SemverOut` must not apply an output filter.

**Observing the semantic-version walk.** The three-argument `SemverOut` constructor accepts a `Listener`, whose `onChange(JApiCompatibility, JApiSemanticVersionLevel)` must be called once for every node the walk visits, with the level that node yielded. A null listener argument must be replaced by `Listener.NULL`, which does nothing, and the two-argument constructor must behave as if `Listener.NULL` had been passed.

**The XML report.** `XmlOutputGenerator.generate()` returns the document as a `String`. It must read the option values for the root element before it filters, then apply an `OutputFilter` built from the same options, then serialise. The document has a single root element `plumbline` carrying these attributes:

| Attribute | Value |
|---|---|
| `oldVersion` | `Options.getOldVersion()`, or `n.a.` when null or blank |
| `newVersion` | `Options.getNewVersion()`, or `n.a.` when null or blank |
| `accessModifier` | the name of `Options.getAccessModifier()` |
| `onlyModifications` | `Options.isOutputOnlyModifications()` |
| `onlyBinaryIncompatibleModifications` | `Options.isOutputOnlyBinaryIncompatibleModifications()` |
| `packagesInclude` | the include filters joined with `;` using their `toString()`, or `all` when the list is empty |
| `packagesExclude` | the exclude filters joined with `;` using their `toString()`, or `n.a.` when the list is empty |
| `ignoreMissingClasses` | `IgnoreMissingClasses.isIgnoreAllMissingClasses()` |
| `ignoreMissingClassesByRegularExpressions` | the configured patterns joined with `;` using their `toString()` |
| `title` | `XmlOutputGeneratorOptions.getTitle()`, present only when that `Optional` is non-empty |
| `semanticVersioning` | `XmlOutputGeneratorOptions.getSemanticVersioningInformation()` |

**XML element mapping.** The root element contains one wrapper element `classes` holding one `class` element per node in the filtered tree, in tree order. Every element below follows the same shape: scalar accessors become attributes, list accessors become a wrapper element holding repeated children, and single-node accessors become a single child element. A boolean attribute renders as `true` or `false`; an enum attribute renders as the constant name; an `Optional` accessor is not represented.

| Element | Attributes | Child elements |
|---|---|---|
| `class` | `changeStatus`, `fullyQualifiedName`, `compatible` | `modifiers`/`modifier`, `superclass`, `interfaces`/`interface`, `constructors`/`constructor`, `methods`/`method`, `fields`/`field`, `classType`, `attributes`/`attribute`, `annotations`/`annotation`, `compatibilityChanges`/`compatibilityChange`, `classFileFormatVersion`, `genericTemplates`/`genericTemplate` |
| `method`, `constructor` | `name`, `changeStatus`, `compatible` | `modifiers`/`modifier`, `parameters`/`parameter`, `attributes`/`attribute`, `compatibilityChanges`/`compatibilityChange`, `annotations`/`annotation`, `exceptions`/`exception`, `genericTemplates`/`genericTemplate`, and for a method also `returnType` |
| `field` | `changeStatus`, `name`, `compatible` | `modifiers`/`modifier`, `attributes`/`attribute`, `type`, `compatibilityChanges`/`compatibilityChange`, `annotations`/`annotation`, `oldGenericTypes`/`oldGenericType`, `newGenericTypes`/`newGenericType` |
| `superclass` | `changeStatus`, `superclassOld`, `superclassNew`, `compatible` | `compatibilityChanges`/`compatibilityChange` |
| `interface` | `fullyQualifiedName`, `changeStatus`, `compatible` | `compatibilityChanges`/`compatibilityChange` |
| `modifier`, `attribute` | `changeStatus`, `oldValue`, `newValue` | none |
| `classType` | `oldType`, `newType`, `changeStatus` | none |
| `classFileFormatVersion` | `changeStatus`, `majorVersionOld`, `minorVersionOld`, `majorVersionNew`, `minorVersionNew` | none |
| `compatibilityChange` | `type`, `compatible` | none |
| `parameter` | `changeStatus`, `type`, `templateName`, `compatible` | `oldGenericTypes`/`oldGenericType`, `newGenericTypes`/`newGenericType`, `compatibilityChanges`/`compatibilityChange` |
| `returnType` | `changeStatus`, `oldValue`, `newValue`, `compatible` | `oldGenericTypes`/`oldGenericType`, `newGenericTypes`/`newGenericType`, `compatibilityChanges`/`compatibilityChange` |
| `type` | `changeStatus`, `oldValue`, `newValue` | none |
| `exception` | `name`, `changeStatus` | none |
| `genericTemplate` | `changeStatus`, `name`, `oldType`, `newType`, `compatible` | `oldGenericTypes`/`oldGenericType`, `newGenericTypes`/`newGenericType`, `oldInterfaceTypes`/`oldInterfaceType`, `newInterfaceTypes`/`newInterfaceType`, `compatibilityChanges`/`compatibilityChange` |
| `genericType`, `oldGenericType`, `newGenericType`, `oldInterfaceType`, `newInterfaceType` | `type`, `genericWildCard` | `genericTypes`/`genericType` |
| `annotation` | `changeStatus`, `fullyQualifiedName`, `compatible` | `elements`/`element`, `compatibilityChanges`/`compatibilityChange` |
| `element` | `name`, `changeStatus`, `compatible` | `oldElementValues`/`oldElementValue`, `newElementValues`/`newElementValue`, `compatibilityChanges`/`compatibilityChange` |
| `oldElementValue`, `newElementValue`, `value` | `type`, `value`, `fullyQualifiedName`, `name` | `values`/`value` |

## State Model

The library holds three kinds of state, and the boundaries between them decide what a caller observes.

**Per-comparison state.** A `JarArchiveComparator` owns the class pools built from its options at construction time. Those pools accumulate every type resolved during a comparison, and a class rejected by the filters is removed from them. Two comparators built from equal options must not share pool state.

**Per-tree state.** A `List<JApiClass>` returned by `compareClassLists` is mutable and is mutated in place by the projections that prune it. `OutputFilter.filter` removes nodes; `StdoutOutputGenerator.generate` and `XmlOutputGenerator.generate` each apply an output filter to the tree they hold. Generating two reports from the same tree therefore composes their filtering, and the second report observes the first report's removals.

**Process-wide state.** The three facts each `JApiCompatibilityChangeType` constant carries are enum state, shared by every comparison in the process. An override applied through `JarArchiveComparatorOptions` or through the setters on the constant stays in force until `resetOverrides()` restores the published table.

**Lazily populated links.** `JApiSuperclass.getJApiClass()` and `JApiImplementedInterface.getCorrespondingJApiClass()` return empty until compatibility evaluation resolves and attaches the corresponding node, and return that node afterwards. A tree that was never evaluated therefore reports empty links.

## Error Semantics

Every failure the library raises is a `JApiCompareException`, an unchecked exception carrying a `Reason` returned by `getReason()`. The reasons are `CliError`, `IoException`, `JaxbException`, `ClassLoading`, `IllegalState` and `IllegalArgument`.

- A filter string that cannot be parsed must raise reason `CliError`, with a message that names the offending filter string and the underlying cause.
- A type that is named by a compared class, is absent from the configured classpath, and is not covered by the ignore configuration must raise reason `ClassLoading`, with a message that names the type, reports the classpath in use, and names the option that suppresses the failure. Under `TWO_SEPARATE_CLASSPATHS` the message must report the old and the new classpath separately.
- A classpath mode or archive type outside its enumeration must raise reason `IllegalState`.
- `JApiCompareException.of(Reason, String, Object...)` returns an exception whose message is the format string applied to the arguments, and `JApiCompareException.cliError(String, Object...)` returns the same with reason `CliError`.
- The two `forClassLoading` factories return an exception with reason `ClassLoading`, built from the comparator so that the message carries the classpath.
- A failure to serialise the XML document must raise reason `JaxbException`.

Beyond these, a public method must not raise a checked exception, and `JApiCompareException` must be the only exception type the library declares.

## Cross-View Invariants

1. A class removed from the tree by an include or exclude filter must be absent from the model tree, from the text report, from the XML document, and from the semantic-version computation, and must also be absent from the class pool, so that it cannot later be resolved as a superclass or interface of a class that survived.
2. The sign group in the text report must agree with the model: the first three characters must equal the mapping of `getChangeStatus()`, and the fourth must be derivable from `isBinaryCompatible()` and `isSourceCompatible()` on the same node. A node the XML document reports with `compatible="false"` must carry `!` in the text report.
3. The string `SemverOut.generate()` returns must equal `SEMVER_MAJOR` exactly when some node reachable by the shared traversal carries a compatibility change whose type has semantic level `MAJOR` and whose node is public or protected; the same node must appear in the XML document with a `compatibilityChange` child naming that type.
4. Applying an override to a `JApiCompatibilityChangeType` must move together in all four projections: the `binaryCompatible` attribute in XML, the fourth sign character in the text report, the value `isBinaryCompatible()` returns on every node carrying that change, and the string the semantic-version report returns.
5. Turning on only-binary-incompatible reporting must produce the same pruning in the text report and in the XML document, because both apply the same output filter to the same tree; the semantic-version report must be unaffected by it, because it applies no output filter.
6. A verdict must not improve when a type becomes reachable: adding the classpath entry that resolves a superclass must never turn an incompatible node compatible, and ignoring missing classes must never introduce a compatibility change that resolution would not also have produced.
7. Sorting is settled once, inside `compareClassLists`: the order of `class` elements in the XML document, the order of class blocks in the text report, and the order of nodes in the returned list must be the same case-insensitive order by fully qualified name, and the order of `method` elements and of method lines must be the same case-insensitive order by method name.
8. Every value the text report renders as `n.a.` must correspond to an absent `Optional` in the model, and the XML document must omit the corresponding attribute or render the same placeholder rather than inventing a value.

## Public Interface

### Import Surface

Everything in this specification is reachable from the Maven coordinate `org.plumbline:plumbline-core:1.0.0`. The public packages are:

| Package | Contents |
|---|---|
| `org.plumbline.cmp` | the comparator, its options, the class-pool wrapper |
| `org.plumbline.compat` | the compatibility-rule evaluator |
| `org.plumbline.config` | the reporting options and the missing-class policy |
| `org.plumbline.exception` | the exception type and its reasons |
| `org.plumbline.filter` | the filter interfaces and their implementations |
| `org.plumbline.model` | the comparison tree and the change catalogue |
| `org.plumbline.output` | the shared traversal, the output filter, the generator base class |
| `org.plumbline.output.semver` | the semantic-version report |
| `org.plumbline.output.stdout` | the text report |
| `org.plumbline.output.xml` | the XML report and its options |

No other package is part of the published surface. Types from `javassist` — `ClassPool`, `CtClass`, `CtBehavior`, `CtMethod`, `CtConstructor`, `CtField` and `javassist.bytecode.annotation.MemberValue` — appear in the declared signatures below and are supplied by the `org.javassist:javassist` dependency.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, type parameter, bound, parameter type, return type and enum constant does.

#### `org.plumbline.model`

```java
public enum AbstractModifier implements JApiModifierBase {
    ABSTRACT, NON_ABSTRACT;
}

public enum AccessModifier implements JApiModifierBase {
    PUBLIC, PROTECTED, PACKAGE_PROTECTED, PRIVATE;
    public int getLevel();
    public static java.util.Optional<AccessModifier> toModifier(java.lang.String name);
}

public enum BridgeModifier implements JApiModifierBase {
    BRIDGE, NON_BRIDGE;
}

public enum FinalModifier implements JApiModifierBase {
    FINAL, NON_FINAL;
}

public class JApiAnnotation implements JApiHasChangeStatus, JApiCompatibility {
    public JApiAnnotation(java.lang.String name, java.util.Optional<javassist.bytecode.annotation.Annotation> oldOption, java.util.Optional<javassist.bytecode.annotation.Annotation> newOption, JApiChangeStatus jApiChangeStatus);
    public java.lang.String toString();
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getFullyQualifiedName();
    public void setJApiClass(JApiClass jApiClass);
    public java.util.Optional<JApiClass> getCorrespondingJApiClass();
    public java.util.Optional<javassist.bytecode.annotation.Annotation> getOldAnnotation();
    public java.util.Optional<javassist.bytecode.annotation.Annotation> getNewAnnotation();
    public java.util.List<JApiAnnotationElement> getElements();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
}

public class JApiAnnotationElement implements JApiHasChangeStatus, JApiCompatibility {
    public JApiAnnotationElement(java.lang.String name, java.util.Optional<javassist.bytecode.annotation.MemberValue> oldOption, java.util.Optional<javassist.bytecode.annotation.MemberValue> newOption, JApiChangeStatus jApiChangeStatus);
    public java.lang.String toString();
    public java.lang.String getName();
    public java.util.Optional<javassist.bytecode.annotation.MemberValue> getOldValue();
    public java.util.Optional<javassist.bytecode.annotation.MemberValue> getNewValue();
    public JApiChangeStatus getChangeStatus();
    public java.util.List<JApiAnnotationElementValue> getOldElementValues();
    public java.util.List<JApiAnnotationElementValue> getNewElementValues();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
}

public class JApiAnnotationElementValue {
    public enum Type {
        Double, Char, Long, Integer, Float, Byte, Enum, Annotation, Class, Short, Boolean, UnsupportedType, Array, String;
    }
    public JApiAnnotationElementValue(JApiAnnotationElementValue.Type type, java.lang.Object object, java.lang.String name);
    public JApiAnnotationElementValue.Type getType();
    public java.lang.String getTypeString();
    public java.lang.Object getValue();
    public java.lang.String getValueString();
    public java.util.List<JApiAnnotationElementValue> getValues();
    public boolean equals(java.lang.Object object);
    public int hashCode();
    public java.lang.String getFullyQualifiedName();
    public java.util.Optional<java.lang.String> getName();
    public java.lang.String getNameString();
    public void setName(java.util.Optional<java.lang.String> option);
}

public class JApiAttribute<T> implements JApiHasChangeStatus {
    public JApiAttribute(JApiChangeStatus jApiChangeStatus, java.util.Optional<T> oldOption, java.util.Optional<T> newOption);
    public java.util.Optional<T> getOldAttribute();
    public java.util.Optional<T> getNewAttribute();
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getOldValue();
    public java.lang.String getNewValue();
}

public abstract class JApiBehavior implements JApiHasModifiers, JApiHasChangeStatus, JApiHasAccessModifier, JApiHasStaticModifier, JApiHasFinalModifier, JApiHasAbstractModifier, JApiCompatibility, JApiHasAnnotations, JApiHasBridgeModifier, JApiCanBeSynthetic, JApiHasGenericTemplates {
    public JApiBehavior(JApiClass jApiClass, java.lang.String name, java.util.Optional<? extends javassist.CtBehavior> oldOption, java.util.Optional<? extends javassist.CtBehavior> newOption, JApiChangeStatus jApiChangeStatus, org.plumbline.cmp.JarArchiveComparator jarArchiveComparator);
    public void setChangeStatus(JApiChangeStatus jApiChangeStatus);
    public boolean hasSameParameter(JApiMethod jApiMethod);
    public java.util.List<? extends JApiModifier<? extends java.lang.Enum<? extends java.lang.Enum<?>>>> getModifiers();
    public java.lang.String getName();
    public JApiChangeStatus getChangeStatus();
    public java.util.List<JApiParameter> getParameters();
    public void addParameter(JApiParameter jApiParameter);
    public JApiModifier<AccessModifier> getAccessModifier();
    public JApiModifier<FinalModifier> getFinalModifier();
    public JApiModifier<StaticModifier> getStaticModifier();
    public JApiModifier<AbstractModifier> getAbstractModifier();
    public java.util.List<JApiAttribute<? extends java.lang.Enum<?>>> getAttributes();
    public JApiModifier<BridgeModifier> getBridgeModifier();
    public JApiModifier<SyntheticModifier> getSyntheticModifier();
    public JApiAttribute<SyntheticAttribute> getSyntheticAttribute();
    public JApiModifier<VarargsModifier> getVarargsModifier();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public java.util.List<JApiAnnotation> getAnnotations();
    public java.util.List<JApiException> getExceptions();
    public JApiClass getjApiClass();
    public java.util.List<JApiGenericTemplate> getGenericTemplates();
    public abstract void enhanceGenericTypeToParameters();
}

public interface JApiCanBeSynthetic {
}

public enum JApiChangeStatus {
    NEW, REMOVED, UNCHANGED, MODIFIED;
    public boolean isNotNewOrRemoved();
}

public class JApiClass implements JApiHasModifiers, JApiHasChangeStatus, JApiHasAccessModifier, JApiHasStaticModifier, JApiHasFinalModifier, JApiHasAbstractModifier, JApiCompatibility, JApiHasAnnotations, JApiCanBeSynthetic, JApiHasGenericTemplates {
    public JApiClass(org.plumbline.cmp.JarArchiveComparator jarArchiveComparator, java.lang.String name, java.util.Optional<javassist.CtClass> oldOption, java.util.Optional<javassist.CtClass> newOption, JApiChangeStatus jApiChangeStatus, JApiClassType jApiClassType);
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getFullyQualifiedName();
    public java.util.Optional<javassist.CtClass> getNewClass();
    public java.util.Optional<javassist.CtClass> getOldClass();
    public java.util.List<? extends JApiModifier<? extends java.lang.Enum<? extends java.lang.Enum<?>>>> getModifiers();
    public JApiSuperclass getSuperclass();
    public java.util.List<JApiImplementedInterface> getInterfaces();
    public java.util.List<JApiConstructor> getConstructors();
    public java.util.List<JApiMethod> getMethods();
    public java.util.List<JApiField> getFields();
    public JApiClassType getClassType();
    public JApiModifier<FinalModifier> getFinalModifier();
    public JApiModifier<StaticModifier> getStaticModifier();
    public JApiModifier<AccessModifier> getAccessModifier();
    public JApiModifier<AbstractModifier> getAbstractModifier();
    public JApiModifier<SyntheticModifier> getSyntheticModifier();
    public JApiAttribute<SyntheticAttribute> getSyntheticAttribute();
    public java.util.List<JApiAttribute<? extends java.lang.Enum<?>>> getAttributes();
    public boolean isOldClassExtendable();
    public boolean isNewClassExtendable();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiAnnotation> getAnnotations();
    public boolean isChangeCausedByClassElement();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public JApiClassFileFormatVersion getClassFileFormatVersion();
    public java.util.List<JApiGenericTemplate> getGenericTemplates();
    public java.lang.String toString();
}

public class JApiClassFileFormatVersion implements JApiHasChangeStatus, JApiCompatibility {
    public JApiClassFileFormatVersion(int oldValue, int newValue, int oldValue2, int newValue2);
    public JApiChangeStatus getChangeStatus();
    public int getMajorVersionOld();
    public int getMinorVersionOld();
    public int getMajorVersionNew();
    public int getMinorVersionNew();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public java.lang.String toString();
}

public class JApiClassType implements JApiHasChangeStatus {
    public enum ClassType {
        ANNOTATION, INTERFACE, CLASS, ENUM;
    }
    public JApiClassType(java.util.Optional<JApiClassType.ClassType> oldOption, java.util.Optional<JApiClassType.ClassType> newOption, JApiChangeStatus jApiChangeStatus);
    public java.lang.String getOldType();
    public java.lang.String getNewType();
    public JApiChangeStatus getChangeStatus();
    public java.util.Optional<JApiClassType.ClassType> getOldTypeOptional();
    public java.util.Optional<JApiClassType.ClassType> getNewTypeOptional();
}

public interface JApiCompatibility {
    public abstract boolean isBinaryCompatible();
    public abstract boolean isSourceCompatible();
    public abstract java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
}

public class JApiCompatibilityChange {
    public JApiCompatibilityChange(JApiCompatibilityChangeType jApiCompatibilityChangeType);
    public JApiCompatibilityChangeType getType();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public void setBinaryCompatible(boolean flag);
    public void setSourceCompatible(boolean flag);
    public JApiSemanticVersionLevel getSemanticVersionLevel();
    public boolean equals(java.lang.Object object);
    public int hashCode();
    public java.lang.String toString();
}

public enum JApiCompatibilityChangeType {
    ANNOTATION_ADDED, ANNOTATION_DEPRECATED_ADDED, ANNOTATION_MODIFIED, ANNOTATION_REMOVED, CLASS_REMOVED, CLASS_NOW_ABSTRACT, CLASS_NOW_NOT_EXTENDABLE, CLASS_NO_LONGER_PUBLIC, CLASS_TYPE_CHANGED, CLASS_NOW_CHECKED_EXCEPTION, CLASS_LESS_ACCESSIBLE, CLASS_GENERIC_TEMPLATE_CHANGED, CLASS_GENERIC_TEMPLATE_GENERICS_CHANGED, SUPERCLASS_REMOVED, SUPERCLASS_ADDED, SUPERCLASS_MODIFIED_INCOMPATIBLE, INTERFACE_ADDED, INTERFACE_REMOVED, METHOD_REMOVED, METHOD_REMOVED_IN_SUPERCLASS, METHOD_LESS_ACCESSIBLE, METHOD_LESS_ACCESSIBLE_THAN_IN_SUPERCLASS, METHOD_IS_STATIC_AND_OVERRIDES_NOT_STATIC, METHOD_RETURN_TYPE_CHANGED, METHOD_RETURN_TYPE_COVARIANT_CHANGED, METHOD_RETURN_TYPE_GENERICS_CHANGED, METHOD_PARAMETER_GENERICS_CHANGED, METHOD_NOW_ABSTRACT, METHOD_NOW_FINAL, METHOD_NOW_STATIC, METHOD_NO_LONGER_STATIC, METHOD_NOW_VARARGS, METHOD_NO_LONGER_VARARGS, METHOD_ADDED_TO_INTERFACE, METHOD_ADDED_TO_PUBLIC_CLASS, METHOD_NOW_THROWS_CHECKED_EXCEPTION, METHOD_NO_LONGER_THROWS_CHECKED_EXCEPTION, METHOD_ABSTRACT_ADDED_TO_CLASS, METHOD_ABSTRACT_ADDED_IN_SUPERCLASS, METHOD_ABSTRACT_ADDED_IN_IMPLEMENTED_INTERFACE, METHOD_DEFAULT_ADDED_IN_IMPLEMENTED_INTERFACE, METHOD_NEW_DEFAULT, METHOD_NEW_STATIC_ADDED_TO_INTERFACE, METHOD_MOVED_TO_SUPERCLASS, METHOD_ABSTRACT_NOW_DEFAULT, METHOD_NON_STATIC_IN_INTERFACE_NOW_STATIC, METHOD_STATIC_IN_INTERFACE_NO_LONGER_STATIC, FIELD_STATIC_AND_OVERRIDES_STATIC, FIELD_LESS_ACCESSIBLE_THAN_IN_SUPERCLASS, FIELD_NOW_FINAL, FIELD_NOW_TRANSIENT, FIELD_NOW_VOLATILE, FIELD_NOW_STATIC, FIELD_NO_LONGER_TRANSIENT, FIELD_NO_LONGER_VOLATILE, FIELD_NO_LONGER_STATIC, FIELD_TYPE_CHANGED, FIELD_REMOVED, FIELD_REMOVED_IN_SUPERCLASS, FIELD_LESS_ACCESSIBLE, FIELD_GENERICS_CHANGED, CONSTRUCTOR_REMOVED, CONSTRUCTOR_LESS_ACCESSIBLE;
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public JApiSemanticVersionLevel getSemanticVersionLevel();
    public void setBinaryCompatible(boolean flag);
    public void setSourceCompatible(boolean flag);
    public void setSemanticVersionLevel(JApiSemanticVersionLevel jApiSemanticVersionLevel);
    public void resetOverrides();
}

public class JApiConstructor extends JApiBehavior {
    public JApiConstructor(JApiClass jApiClass, java.lang.String name, JApiChangeStatus jApiChangeStatus, java.util.Optional<javassist.CtConstructor> oldOption, java.util.Optional<javassist.CtConstructor> newOption, org.plumbline.cmp.JarArchiveComparator jarArchiveComparator);
    public java.util.Optional<javassist.CtConstructor> getNewConstructor();
    public java.util.Optional<javassist.CtConstructor> getOldConstructor();
    public java.lang.String toString();
    public void enhanceGenericTypeToParameters();
    public boolean isSourceCompatible();
}

public class JApiException implements JApiHasChangeStatus {
    public JApiException(org.plumbline.cmp.JarArchiveComparator jarArchiveComparator, java.lang.String name, java.util.Optional<javassist.CtClass> option, JApiChangeStatus jApiChangeStatus);
    public java.lang.String getName();
    public JApiChangeStatus getChangeStatus();
    public boolean isCheckedException();
}

public class JApiField implements JApiHasChangeStatus, JApiHasModifiers, JApiHasAccessModifier, JApiHasStaticModifier, JApiHasFinalModifier, JApiHasTransientModifier, JApiHasVolatileModifier, JApiCompatibility, JApiHasAnnotations, JApiCanBeSynthetic, JApiHasGenericTypes {
    public JApiField(JApiClass jApiClass, JApiChangeStatus jApiChangeStatus, java.util.Optional<javassist.CtField> oldOption, java.util.Optional<javassist.CtField> newOption, org.plumbline.cmp.JarArchiveComparatorOptions jarArchiveComparatorOptions);
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getName();
    public java.util.Optional<javassist.CtField> getOldFieldOptional();
    public java.util.Optional<javassist.CtField> getNewFieldOptional();
    public java.util.List<? extends JApiModifier<? extends java.lang.Enum<? extends java.lang.Enum<?>>>> getModifiers();
    public JApiModifier<StaticModifier> getStaticModifier();
    public JApiModifier<FinalModifier> getFinalModifier();
    public JApiModifier<TransientModifier> getTransientModifier();
    public JApiModifier<VolatileModifier> getVolatileModifier();
    public JApiModifier<AccessModifier> getAccessModifier();
    public java.util.List<JApiAttribute<? extends java.lang.Enum<?>>> getAttributes();
    public JApiModifier<SyntheticModifier> getSyntheticModifier();
    public JApiAttribute<SyntheticAttribute> getSyntheticAttribute();
    public JApiType getType();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public java.util.List<JApiAnnotation> getAnnotations();
    public JApiClass getjApiClass();
    public java.lang.String toString();
    public java.util.List<JApiGenericType> getOldGenericTypes();
    public java.util.List<JApiGenericType> getNewGenericTypes();
}

public class JApiGenericTemplate implements JApiHasChangeStatus, JApiHasGenericTypes, JApiCompatibility {
    public JApiGenericTemplate(JApiChangeStatus jApiChangeStatus, java.lang.String name, java.util.Optional<java.lang.String> oldOption, java.util.Optional<java.lang.String> newOption);
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getName();
    public java.util.Optional<java.lang.String> getOldTypeOptional();
    public java.util.Optional<java.lang.String> getNewTypeOptional();
    public java.lang.String getOldType();
    public java.lang.String getNewType();
    public java.util.List<JApiGenericType> getOldGenericTypes();
    public java.util.List<JApiGenericType> getNewGenericTypes();
    public java.lang.String toString();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public java.util.List<JApiGenericType> getOldInterfaceTypes();
    public java.util.List<JApiGenericType> getNewInterfaceTypes();
}

public class JApiGenericType {
    public enum JApiGenericWildCard {
        NONE, EXTENDS, SUPER, UNBOUNDED;
    }
    public JApiGenericType(java.lang.String name, JApiGenericType.JApiGenericWildCard jApiGenericWildCard);
    public java.lang.String getType();
    public JApiGenericType.JApiGenericWildCard getGenericWildCard();
    public java.util.List<JApiGenericType> getGenericTypes();
    public java.lang.String toString();
}

public interface JApiHasAbstractModifier {
    public abstract JApiModifier<AbstractModifier> getAbstractModifier();
}

public interface JApiHasAccessModifier {
    public abstract JApiModifier<AccessModifier> getAccessModifier();
}

public interface JApiHasAnnotations extends JApiCompatibility {
    public abstract java.util.List<JApiAnnotation> getAnnotations();
}

public interface JApiHasBridgeModifier {
    public abstract JApiModifier<BridgeModifier> getBridgeModifier();
}

public interface JApiHasChangeStatus {
    public abstract JApiChangeStatus getChangeStatus();
}

public interface JApiHasFinalModifier {
    public abstract JApiModifier<FinalModifier> getFinalModifier();
}

public interface JApiHasGenericTemplates extends JApiCompatibility {
    public abstract java.util.List<JApiGenericTemplate> getGenericTemplates();
}

public interface JApiHasGenericTypes {
    public abstract java.util.List<JApiGenericType> getOldGenericTypes();
    public abstract java.util.List<JApiGenericType> getNewGenericTypes();
}

public interface JApiHasModifier extends JApiHasChangeStatus {
    public abstract java.util.List<JApiModifier<? extends java.lang.Enum<?>>> getModifiers();
}

public interface JApiHasModifiers extends JApiHasChangeStatus {
    public abstract java.util.List<? extends JApiModifier<? extends java.lang.Enum<? extends java.lang.Enum<?>>>> getModifiers();
}

public interface JApiHasStaticModifier {
    public abstract JApiModifier<StaticModifier> getStaticModifier();
}

public interface JApiHasSyntheticAttribute {
    public abstract JApiAttribute<SyntheticAttribute> getSyntheticAttribute();
}

public interface JApiHasSyntheticModifier {
    public abstract JApiModifier<SyntheticModifier> getSyntheticModifier();
}

public interface JApiHasTransientModifier {
    public abstract JApiModifier<TransientModifier> getTransientModifier();
}

public interface JApiHasVolatileModifier {
    public abstract JApiModifier<VolatileModifier> getVolatileModifier();
}

public class JApiImplementedInterface implements JApiHasChangeStatus, JApiCompatibility {
    public JApiImplementedInterface(javassist.CtClass ctClass, java.lang.String name, JApiChangeStatus jApiChangeStatus);
    public java.lang.String getFullyQualifiedName();
    public JApiChangeStatus getChangeStatus();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public void setJApiClass(JApiClass jApiClass);
    public java.util.Optional<JApiClass> getCorrespondingJApiClass();
    public javassist.CtClass getCtClass();
    public java.lang.String toString();
}

public class JApiMethod extends JApiBehavior {
    public JApiMethod(JApiClass jApiClass, java.lang.String name, JApiChangeStatus jApiChangeStatus, java.util.Optional<javassist.CtMethod> oldOption, java.util.Optional<javassist.CtMethod> newOption, org.plumbline.cmp.JarArchiveComparator jarArchiveComparator);
    public void enhanceGenericTypeToParameters();
    public boolean hasSameReturnType(JApiMethod jApiMethod);
    public boolean hasSameSignature(JApiMethod jApiMethod);
    public java.util.Optional<javassist.CtMethod> getNewMethod();
    public java.util.Optional<javassist.CtMethod> getOldMethod();
    public JApiReturnType getReturnType();
    public java.lang.String toString();
    public static java.lang.String toString(java.util.Optional<javassist.CtMethod> option);
    public boolean isSourceCompatible();
}

public class JApiModifier<T> implements JApiHasChangeStatus {
    public JApiModifier(java.util.Optional<T> oldOption, java.util.Optional<T> newOption, JApiChangeStatus jApiChangeStatus);
    public java.util.Optional<T> getOldModifier();
    public java.util.Optional<T> getNewModifier();
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getValueOld();
    public java.lang.String getValueNew();
    public boolean hasChangedFromTo(T oldT, T newT);
    public boolean hasChangedFrom(T t);
    public boolean hasChangedTo(T t);
    public boolean hasChangedToMoreVisible();
}

public interface JApiModifierBase {
}

public class JApiParameter implements JApiHasGenericTypes, JApiHasChangeStatus, JApiCompatibility {
    public JApiParameter(java.lang.String name, java.util.Optional<java.lang.String> option);
    public void setType(java.lang.String name);
    public void setTemplateName(java.util.Optional<java.lang.String> option);
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getType();
    public java.lang.String getTemplateName();
    public java.util.Optional<java.lang.String> getTemplateNameOptional();
    public java.util.List<JApiGenericType> getOldGenericTypes();
    public java.util.List<JApiGenericType> getNewGenericTypes();
    public boolean equals(java.lang.Object object);
    public int hashCode();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
}

public class JApiReturnType implements JApiHasGenericTypes, JApiHasChangeStatus, JApiCompatibility {
    public JApiReturnType(JApiChangeStatus jApiChangeStatus, java.util.Optional<java.lang.String> oldOption, java.util.Optional<java.lang.String> newOption);
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getOldReturnType();
    public java.lang.String getNewReturnType();
    public java.util.List<JApiGenericType> getOldGenericTypes();
    public java.util.List<JApiGenericType> getNewGenericTypes();
    public java.lang.String toString();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
}

public enum JApiSemanticVersionLevel {
    MAJOR, MINOR, PATCH;
    public int getLevel();
}

public class JApiSuperclass implements JApiHasChangeStatus, JApiCompatibility {
    public JApiSuperclass(JApiClass jApiClass, java.util.Optional<javassist.CtClass> oldOption, java.util.Optional<javassist.CtClass> newOption, JApiChangeStatus jApiChangeStatus, org.plumbline.cmp.JarArchiveComparator jarArchiveComparator);
    public java.util.Optional<JApiClass> getJApiClass();
    public java.util.Optional<javassist.CtClass> getOldSuperclass();
    public java.util.Optional<javassist.CtClass> getNewSuperclass();
    public java.util.Optional<java.lang.String> getOldSuperclassName();
    public java.util.Optional<java.lang.String> getNewSuperclassName();
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getSuperclassOld();
    public java.lang.String getSuperclassNew();
    public boolean isBinaryCompatible();
    public boolean isSourceCompatible();
    public java.util.List<JApiCompatibilityChange> getCompatibilityChanges();
    public void setJApiClass(JApiClass jApiClass);
    public java.util.Optional<JApiClass> getCorrespondingJApiClass();
    public JApiClass getJApiClassOwning();
    public java.lang.String toString();
}

public class JApiType implements JApiHasChangeStatus {
    public JApiType(java.util.Optional<java.lang.String> oldOption, java.util.Optional<java.lang.String> newOption, JApiChangeStatus jApiChangeStatus);
    public java.util.Optional<java.lang.String> getOldTypeOptional();
    public java.util.Optional<java.lang.String> getNewTypeOptional();
    public JApiChangeStatus getChangeStatus();
    public java.lang.String getOldValue();
    public java.lang.String getNewValue();
    public boolean hasChanged();
}

public enum StaticModifier implements JApiModifierBase {
    STATIC, NON_STATIC;
}

public enum SyntheticAttribute {
    SYNTHETIC, NON_SYNTHETIC;
}

public enum SyntheticModifier implements JApiModifierBase {
    SYNTHETIC, NON_SYNTHETIC;
}

public enum TransientModifier implements JApiModifierBase {
    TRANSIENT, NON_TRANSIENT;
}

public enum VarargsModifier implements JApiModifierBase {
    VARARGS, NON_VARARGS;
}

public enum VolatileModifier implements JApiModifierBase {
    VOLATILE, NON_VOLATILE;
}
```

#### `org.plumbline.cmp`

```java
public class ClassesComparator {
    public ClassesComparator(JarArchiveComparator jarArchiveComparator, JarArchiveComparatorOptions jarArchiveComparatorOptions);
    public void compare(java.util.List<javassist.CtClass> oldList, java.util.List<javassist.CtClass> newList);
    public java.util.List<org.plumbline.model.JApiClass> getClasses();
}

public class JarArchiveComparator {
    public enum ArchiveType {
        OLD, NEW;
    }
    public JarArchiveComparator(JarArchiveComparatorOptions jarArchiveComparatorOptions);
    public java.util.List<javassist.CtClass> filterClasses(java.util.List<javassist.CtClass> list, ReducibleClassPool reducibleClassPool, boolean flag);
    public JarArchiveComparatorOptions getJarArchiveComparatorOptions();
    public ReducibleClassPool getCommonClassPool();
    public javassist.ClassPool getOldClassPool();
    public javassist.ClassPool getNewClassPool();
    public java.util.Optional<javassist.CtClass> loadClass(JarArchiveComparator.ArchiveType archiveType, java.lang.String name);
    public java.util.List<org.plumbline.model.JApiClass> compareClassLists(JarArchiveComparatorOptions jarArchiveComparatorOptions, java.util.List<javassist.CtClass> oldList, java.util.List<javassist.CtClass> newList);
}

public class JarArchiveComparatorOptions {
    public enum ClassPathMode {
        ONE_COMMON_CLASSPATH, TWO_SEPARATE_CLASSPATHS;
    }
    public static class OverrideCompatibilityChange {
        public OverrideCompatibilityChange(org.plumbline.model.JApiCompatibilityChangeType jApiCompatibilityChangeType, boolean oldFlag, boolean newFlag, org.plumbline.model.JApiSemanticVersionLevel jApiSemanticVersionLevel);
        public org.plumbline.model.JApiCompatibilityChangeType getCompatibilityChange();
        public boolean isBinaryCompatible();
        public boolean isSourceCompatible();
        public org.plumbline.model.JApiSemanticVersionLevel getSemanticVersionLevel();
    }
    public JarArchiveComparatorOptions();
    public static JarArchiveComparatorOptions of(org.plumbline.config.Options options);
    public org.plumbline.filter.Filters getFilters();
    public java.util.List<java.lang.String> getClassPathEntries();
    public void setAccessModifier(org.plumbline.model.AccessModifier accessModifier);
    public org.plumbline.model.AccessModifier getAccessModifier();
    public void setIncludeSynthetic(boolean flag);
    public boolean isIncludeSynthetic();
    public void setClassPathMode(JarArchiveComparatorOptions.ClassPathMode classPathMode);
    public JarArchiveComparatorOptions.ClassPathMode getClassPathMode();
    public void setOldClassPath(java.util.List<java.lang.String> list);
    public java.util.List<java.lang.String> getOldClassPath();
    public void setNewClassPath(java.util.List<java.lang.String> list);
    public java.util.List<java.lang.String> getNewClassPath();
    public void setNoAnnotations(boolean flag);
    public boolean isNoAnnotations();
    public org.plumbline.config.IgnoreMissingClasses getIgnoreMissingClasses();
    public boolean isIncludeClassFileFormatVersion();
    public void addOverrideCompatibilityChange(JarArchiveComparatorOptions.OverrideCompatibilityChange overrideCompatibilityChange);
    public java.util.List<JarArchiveComparatorOptions.OverrideCompatibilityChange> getOverrideCompatibilityChanges();
}

public class ReducibleClassPool extends javassist.ClassPool {
    public ReducibleClassPool();
    public void remove(javassist.CtClass ctClass);
}
```

#### `org.plumbline.compat`

```java
public class CompatibilityChanges {
    public CompatibilityChanges(org.plumbline.cmp.JarArchiveComparator jarArchiveComparator, org.plumbline.cmp.JarArchiveComparatorOptions jarArchiveComparatorOptions);
    public void evaluate(java.util.List<org.plumbline.model.JApiClass> list);
}
```

#### `org.plumbline.config`

```java
public class IgnoreMissingClasses {
    public IgnoreMissingClasses();
    public boolean isIgnoreAllMissingClasses();
    public java.util.List<java.util.regex.Pattern> getIgnoreMissingClassRegularExpression();
    public void setIgnoreAllMissingClasses(boolean flag);
    public void setIgnoreMissingClassRegularExpression(java.util.List<java.util.regex.Pattern> list);
    public boolean ignoreClass(java.lang.String name);
}

public class Options {
    public static final java.lang.String N_A = "n.a.";
    public static Options newDefault();
    public java.lang.String getOldVersion();
    public void setOldVersion(java.lang.String name);
    public java.lang.String getNewVersion();
    public void setNewVersion(java.lang.String name);
    public boolean isOutputOnlyModifications();
    public void setOutputOnlyModifications(boolean flag);
    public boolean isOutputOnlyBinaryIncompatibleModifications();
    public void setOutputOnlyBinaryIncompatibleModifications(boolean flag);
    public org.plumbline.model.AccessModifier getAccessModifier();
    public void setAccessModifier(org.plumbline.model.AccessModifier accessModifier);
    public boolean isIncludeSynthetic();
    public void setIncludeSynthetic(boolean flag);
    public boolean isNoAnnotations();
    public void setNoAnnotations(boolean flag);
    public boolean isReportOnlySummary();
    public void setReportOnlySummary(boolean flag);
    public boolean isSemanticVersioning();
    public void setSemanticVersioning(boolean flag);
    public org.plumbline.cmp.JarArchiveComparatorOptions.ClassPathMode getClassPathMode();
    public void setClassPathMode(org.plumbline.cmp.JarArchiveComparatorOptions.ClassPathMode classPathMode);
    public java.util.List<org.plumbline.filter.Filter> getIncludes();
    public java.util.List<org.plumbline.filter.Filter> getExcludes();
    public void addIncludeFromArgument(java.util.Optional<java.lang.String> option, boolean flag);
    public void addExcludeFromArgument(java.util.Optional<java.lang.String> option, boolean flag);
    public java.util.List<org.plumbline.filter.Filter> createFilterList(java.util.Optional<java.lang.String> option, java.util.List<org.plumbline.filter.Filter> list, java.lang.String name, boolean flag);
    public void setIgnoreMissingClasses(boolean flag);
    public void addIgnoreMissingClassRegularExpression(java.lang.String name);
    public IgnoreMissingClasses getIgnoreMissingClasses();
    public java.lang.String getDifferenceDescription();
}
```

#### `org.plumbline.filter`

```java
public class AnnotationBehaviorFilter extends AnnotationFilterBase implements BehaviorFilter {
    public AnnotationBehaviorFilter(java.lang.String name);
    public boolean matches(javassist.CtBehavior ctBehavior);
    public java.lang.String toString();
}

public class AnnotationClassFilter extends AnnotationFilterBase implements ClassFilter {
    public AnnotationClassFilter(java.lang.String name);
    public boolean matches(javassist.CtClass ctClass);
    public java.lang.String toString();
}

public class AnnotationFieldFilter extends AnnotationFilterBase implements FieldFilter {
    public AnnotationFieldFilter(java.lang.String name);
    public boolean matches(javassist.CtField ctField);
    public java.lang.String toString();
}

public class AnnotationFilterBase {
    public AnnotationFilterBase(java.lang.String name);
    public java.lang.String getClassName();
}

public interface BehaviorFilter extends Filter {
    public abstract boolean matches(javassist.CtBehavior ctBehavior);
}

public interface ClassFilter extends Filter {
    public abstract boolean matches(javassist.CtClass ctClass);
}

public interface FieldFilter extends Filter {
    public abstract boolean matches(javassist.CtField ctField);
}

public interface Filter {
}

public class Filters {
    public Filters();
    public java.util.List<Filter> getIncludes();
    public java.util.List<Filter> getExcludes();
    public boolean includeClass(javassist.CtClass ctClass);
    public boolean includeBehavior(javassist.CtBehavior ctBehavior);
    public boolean includeField(javassist.CtField ctField);
}

public class JavaDocLikeClassFilter implements ClassFilter {
    public JavaDocLikeClassFilter(java.lang.String name);
    public java.lang.String toString();
    public boolean matches(javassist.CtClass ctClass);
}

public class JavadocLikeBehaviorFilter implements BehaviorFilter {
    public JavadocLikeBehaviorFilter(java.lang.String name);
    public boolean matches(javassist.CtBehavior ctBehavior);
    public java.lang.String toString();
}

public class JavadocLikeFieldFilter implements FieldFilter {
    public JavadocLikeFieldFilter(java.lang.String name);
    public boolean matches(javassist.CtField ctField);
    public java.lang.String toString();
}

public class JavadocLikePackageFilter implements ClassFilter {
    public JavadocLikePackageFilter(java.lang.String name, boolean flag);
    public java.lang.String toString();
    public boolean matches(javassist.CtClass ctClass);
}
```

#### `org.plumbline.exception`

```java
public class JApiCompareException extends java.lang.RuntimeException {
    public enum Reason {
        CliError, IoException, JaxbException, ClassLoading, IllegalState, IllegalArgument;
    }
    public JApiCompareException(JApiCompareException.Reason reason, java.lang.String name);
    public JApiCompareException(JApiCompareException.Reason reason, java.lang.String name, java.lang.Throwable cause);
    public JApiCompareException.Reason getReason();
    public static JApiCompareException cliError(java.lang.String name, java.lang.Object... args);
    public static JApiCompareException of(JApiCompareException.Reason reason, java.lang.String name, java.lang.Object... args);
    public static JApiCompareException forClassLoading(java.lang.Exception exception, java.lang.String name, org.plumbline.cmp.JarArchiveComparator jarArchiveComparator);
    public static JApiCompareException forClassLoading(java.lang.String name, org.plumbline.cmp.JarArchiveComparator jarArchiveComparator);
}
```

#### `org.plumbline.output`

```java
public class Filter {
    public interface FilterVisitor {
        public abstract void visit(java.util.Iterator<org.plumbline.model.JApiClass> iterator, org.plumbline.model.JApiClass jApiClass);
        public abstract void visit(java.util.Iterator<org.plumbline.model.JApiMethod> iterator, org.plumbline.model.JApiMethod jApiMethod);
        public abstract void visit(java.util.Iterator<org.plumbline.model.JApiConstructor> iterator, org.plumbline.model.JApiConstructor jApiConstructor);
        public abstract void visit(java.util.Iterator<org.plumbline.model.JApiImplementedInterface> iterator, org.plumbline.model.JApiImplementedInterface jApiImplementedInterface);
        public abstract void visit(java.util.Iterator<org.plumbline.model.JApiField> iterator, org.plumbline.model.JApiField jApiField);
        public abstract void visit(java.util.Iterator<org.plumbline.model.JApiAnnotation> iterator, org.plumbline.model.JApiAnnotation jApiAnnotation);
        public abstract void visit(org.plumbline.model.JApiSuperclass jApiSuperclass);
    }
    public Filter();
    public static void filter(java.util.List<org.plumbline.model.JApiClass> list, Filter.FilterVisitor filterVisitor);
}

public class OutputFilter extends Filter {
    public OutputFilter(org.plumbline.config.Options options);
    public void filter(java.util.List<org.plumbline.model.JApiClass> list);
    public static void sortClassesAndMethods(java.util.List<org.plumbline.model.JApiClass> list);
}

public abstract class OutputGenerator<T> {
    public OutputGenerator(org.plumbline.config.Options options, java.util.List<org.plumbline.model.JApiClass> list);
    public abstract T generate();
}
```

#### `org.plumbline.output.semver`

```java
public class SemverOut extends org.plumbline.output.OutputGenerator<java.lang.String> {
    public interface Listener {
        public static final SemverOut.Listener NULL;
        public abstract void onChange(org.plumbline.model.JApiCompatibility jApiCompatibility, org.plumbline.model.JApiSemanticVersionLevel jApiSemanticVersionLevel);
    }
    public static final java.lang.String SEMVER_MAJOR;
    public static final java.lang.String SEMVER_MINOR;
    public static final java.lang.String SEMVER_PATCH;
    public static final java.lang.String SEMVER_COMPATIBLE;
    public SemverOut(org.plumbline.config.Options options, java.util.List<org.plumbline.model.JApiClass> list);
    public SemverOut(org.plumbline.config.Options options, java.util.List<org.plumbline.model.JApiClass> list, SemverOut.Listener listener);
    public java.lang.String generate();
}
```

#### `org.plumbline.output.stdout`

```java
public class StdoutOutputGenerator extends org.plumbline.output.OutputGenerator<java.lang.String> {
    public StdoutOutputGenerator(org.plumbline.config.Options options, java.util.List<org.plumbline.model.JApiClass> list);
    public java.lang.String generate();
}
```

#### `org.plumbline.output.xml`

```java
public class XmlOutputGenerator extends org.plumbline.output.OutputGenerator<java.lang.String> {
    public XmlOutputGenerator(java.util.List<org.plumbline.model.JApiClass> list, org.plumbline.config.Options options, XmlOutputGeneratorOptions xmlOutputGeneratorOptions);
    public java.lang.String generate();
}

public class XmlOutputGeneratorOptions {
    public XmlOutputGeneratorOptions();
    public java.util.Optional<java.lang.String> getTitle();
    public void setTitle(java.lang.String name);
    public java.lang.String getSemanticVersioningInformation();
    public void setSemanticVersioningInformation(java.lang.String name);
}
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `org.plumbline.cmp.JarArchiveComparator` | class | Entry point; owns the class pools and turns two `CtClass` lists into one comparison tree. |
| `JarArchiveComparator.ArchiveType` | enum | Selects the old or the new side when resolving a type. |
| `org.plumbline.cmp.JarArchiveComparatorOptions` | class | Comparison-time configuration: classpaths, classpath mode, access level, synthetic and annotation handling, filters, rule overrides. |
| `JarArchiveComparatorOptions.ClassPathMode` | enum | One shared classpath, or one classpath per side. |
| `JarArchiveComparatorOptions.OverrideCompatibilityChange` | class | One replacement of the three facts a change type carries. |
| `org.plumbline.cmp.ClassesComparator` | class | Pairs two class lists into `JApiClass` nodes and exposes the result. |
| `org.plumbline.cmp.ReducibleClassPool` | class | A class pool a class can be removed from, so a filtered-out class stops being resolvable. |
| `org.plumbline.compat.CompatibilityChanges` | class | Applies the compatibility-rule catalogue to a finished tree. |
| `org.plumbline.config.Options` | class | Reporting-time configuration shared by the three report generators. |
| `org.plumbline.config.IgnoreMissingClasses` | class | Policy deciding whether a type absent from the classpath is tolerated. |
| `org.plumbline.exception.JApiCompareException` | class | The single unchecked exception type, carrying a reason. |
| `JApiCompareException.Reason` | enum | Why a comparison failed. |
| `org.plumbline.filter.Filter` | interface | Marker for anything that selects part of the compared surface. |
| `org.plumbline.filter.ClassFilter` | interface | A filter that decides about a `CtClass`. |
| `org.plumbline.filter.BehaviorFilter` | interface | A filter that decides about a `CtBehavior`. |
| `org.plumbline.filter.FieldFilter` | interface | A filter that decides about a `CtField`. |
| `org.plumbline.filter.Filters` | class | The include and exclude lists and the three inclusion decisions over them. |
| `org.plumbline.filter.JavaDocLikeClassFilter` | class | Matches a class, and its nested classes, by a wildcard name pattern. |
| `org.plumbline.filter.JavadocLikePackageFilter` | class | Matches a package, optionally excluding sub-packages. |
| `org.plumbline.filter.JavadocLikeBehaviorFilter` | class | Matches a method or constructor by class, name and parameter types. |
| `org.plumbline.filter.JavadocLikeFieldFilter` | class | Matches a field by class and field-name pattern. |
| `org.plumbline.filter.AnnotationFilterBase` | class | Base holding the annotation name an annotation filter matches. |
| `org.plumbline.filter.AnnotationClassFilter` | class | Matches a class carrying a named annotation, or nested in one that does. |
| `org.plumbline.filter.AnnotationBehaviorFilter` | class | Matches a method or constructor carrying a named annotation. |
| `org.plumbline.filter.AnnotationFieldFilter` | class | Matches a field carrying a named annotation. |
| `org.plumbline.model.JApiClass` | class | One compared class: status, modifiers, members, interfaces, superclass, annotations, changes. |
| `org.plumbline.model.JApiBehavior` | class | Shared shape of a compared method or constructor. |
| `org.plumbline.model.JApiMethod` | class | One compared method, with its return type. |
| `org.plumbline.model.JApiConstructor` | class | One compared constructor. |
| `org.plumbline.model.JApiField` | class | One compared field, with its type. |
| `org.plumbline.model.JApiParameter` | class | One parameter of a compared behaviour. |
| `org.plumbline.model.JApiReturnType` | class | The old and new return type of a compared method. |
| `org.plumbline.model.JApiType` | class | The old and new form of a field type. |
| `org.plumbline.model.JApiException` | class | One declared checked exception of a compared behaviour. |
| `org.plumbline.model.JApiSuperclass` | class | The old and new superclass of a compared class. |
| `org.plumbline.model.JApiImplementedInterface` | class | One interface a compared class implements. |
| `org.plumbline.model.JApiAnnotation` | class | One annotation on a compared node. |
| `org.plumbline.model.JApiAnnotationElement` | class | One member of a compared annotation, with its old and new values. |
| `org.plumbline.model.JApiAnnotationElementValue` | class | One value of an annotation member, including nested values. |
| `org.plumbline.model.JApiGenericTemplate` | class | One type parameter of a compared class or behaviour, with its bounds. |
| `org.plumbline.model.JApiGenericType` | class | One generic type argument, including its wildcard form. |
| `JApiGenericType.JApiGenericWildCard` | enum | Unbounded, upper-bounded or lower-bounded wildcard. |
| `org.plumbline.model.JApiClassType` | class | The old and new kind of a compared class. |
| `JApiClassType.ClassType` | enum | Annotation, interface, class or enum. |
| `org.plumbline.model.JApiClassFileFormatVersion` | class | The old and new class-file major and minor version. |
| `org.plumbline.model.JApiAttribute<T>` | class | An old and new attribute value with a change status. |
| `org.plumbline.model.JApiModifier<T>` | class | An old and new modifier value with a change status. |
| `org.plumbline.model.JApiModifierBase` | interface | Common shape of the modifier enumerations. |
| `org.plumbline.model.AbstractModifier` | enum | `ABSTRACT` and `NON_ABSTRACT`. |
| `org.plumbline.model.AccessModifier` | enum | `PUBLIC`, `PROTECTED`, `PACKAGE_PROTECTED`, `PRIVATE`, ordered by level. |
| `org.plumbline.model.BridgeModifier` | enum | `BRIDGE` and `NON_BRIDGE`. |
| `org.plumbline.model.FinalModifier` | enum | `FINAL` and `NON_FINAL`. |
| `org.plumbline.model.StaticModifier` | enum | `STATIC` and `NON_STATIC`. |
| `org.plumbline.model.SyntheticModifier` | enum | `SYNTHETIC` and `NON_SYNTHETIC`. |
| `org.plumbline.model.SyntheticAttribute` | enum | `SYNTHETIC` and `NON_SYNTHETIC` as a class-file attribute. |
| `org.plumbline.model.TransientModifier` | enum | `TRANSIENT` and `NON_TRANSIENT`. |
| `org.plumbline.model.VolatileModifier` | enum | `VOLATILE` and `NON_VOLATILE`. |
| `org.plumbline.model.VarargsModifier` | enum | `VARARGS` and `NON_VARARGS`. |
| `org.plumbline.model.JApiChangeStatus` | enum | `NEW`, `REMOVED`, `UNCHANGED`, `MODIFIED`. |
| `org.plumbline.model.JApiSemanticVersionLevel` | enum | `MAJOR`, `MINOR`, `PATCH`, each with a numeric level. |
| `org.plumbline.model.JApiCompatibilityChangeType` | enum | The sixty-three rules, each with its binary flag, source flag and semantic level. |
| `org.plumbline.model.JApiCompatibilityChange` | class | One rule attached to one node, with per-instance flags. |
| `org.plumbline.model.JApiCompatibility` | interface | A node that carries compatibility changes and aggregate verdicts. |
| `org.plumbline.model.JApiHasChangeStatus` | interface | A node with a change status. |
| `org.plumbline.model.JApiHasModifiers` | interface | A node with a list of modifiers. |
| `org.plumbline.model.JApiHasModifier` | interface | A node that carries modifier nodes. |
| `org.plumbline.model.JApiHasAccessModifier` | interface | A node with an access modifier. |
| `org.plumbline.model.JApiHasAbstractModifier` | interface | A node with an abstract modifier. |
| `org.plumbline.model.JApiHasFinalModifier` | interface | A node with a final modifier. |
| `org.plumbline.model.JApiHasStaticModifier` | interface | A node with a static modifier. |
| `org.plumbline.model.JApiHasBridgeModifier` | interface | A node with a bridge modifier. |
| `org.plumbline.model.JApiHasSyntheticModifier` | interface | A node with a synthetic modifier. |
| `org.plumbline.model.JApiHasSyntheticAttribute` | interface | A node with a synthetic class-file attribute. |
| `org.plumbline.model.JApiHasTransientModifier` | interface | A node with a transient modifier. |
| `org.plumbline.model.JApiHasVolatileModifier` | interface | A node with a volatile modifier. |
| `org.plumbline.model.JApiHasAnnotations` | interface | A node that carries annotations. |
| `org.plumbline.model.JApiHasGenericTemplates` | interface | A node that declares type parameters. |
| `org.plumbline.model.JApiHasGenericTypes` | interface | A node that carries old and new generic type arguments. |
| `org.plumbline.model.JApiCanBeSynthetic` | interface | A node whose synthetic status is decidable from either the modifier or the attribute. |
| `org.plumbline.output.Filter` | class | The shared depth-first traversal of a comparison tree. |
| `Filter.FilterVisitor` | interface | Receiver of each visited node, holding the live iterator so a node is removable. |
| `org.plumbline.output.OutputFilter` | class | Prunes a tree according to the reporting options, and sorts it. |
| `org.plumbline.output.OutputGenerator<T>` | class | Base class of the three report generators. |
| `org.plumbline.output.stdout.StdoutOutputGenerator` | class | The indented, sign-prefixed text report. |
| `org.plumbline.output.semver.SemverOut` | class | The four-valued semantic-version report. |
| `SemverOut.Listener` | interface | Observer of the level computed for each visited node. |
| `org.plumbline.output.xml.XmlOutputGenerator` | class | The XML report. |
| `org.plumbline.output.xml.XmlOutputGeneratorOptions` | class | Title and semantic-version attribute of the XML root element. |

### CLI Entry Points

There is no console script, no `main` method and no argument parser. Every behaviour in this document is reached by calling the types listed above from Java code.

## Appendix A: Environment

The working environment runs Temurin OpenJDK 21 and Maven 3.9 on Linux without network access. Two third-party artifacts are available on the compile classpath: `org.javassist:javassist:3.30.2-GA`, which supplies the `ClassPool`, `CtClass`, `CtBehavior`, `CtMethod`, `CtConstructor`, `CtField` and `javassist.bytecode.annotation.MemberValue` types named in the Declared Signatures, and `org.slf4j:slf4j-api:2.0.16` with no logging provider bound to it. The JDK's own class library supplies everything else, and JUnit 5 is available for tests. There is no XML binding library on the classpath; the XML report is produced as a `String` by the implementation itself. The assessment environment provides the same JDK, the same Maven version and the same set of artifacts, and resolves dependencies from a pre-populated local repository rather than from a remote one, so a build must not declare any dependency beyond those listed here.

The project must declare its packaging metadata in a Maven `pom.xml` at the project root, producing a single `jar` artifact with the group id `org.plumbline`, the artifact id `plumbline-core` and the version `1.0.0`, compiled with `maven.compiler.source` and `maven.compiler.target` set to `21` and UTF-8 sources, so that `mvn install` publishes it to the local repository under those coordinates. Java sources belong under `src/main/java` and resources under `src/main/resources`, following the standard Maven layout. The whole library is delivered as that one module; no multi-module reactor, plugin or task adapter is part of it.

Automated tests are a separate single Maven project that depends on the artifact above by those coordinates. Its sources live under `src/test/java`, one package per test suite, and each suite is one or more source files inside its package. Tests reach the library only through the public packages listed in the Import Surface, and construct their `CtClass` inputs with the javassist API directly.

## Appendix B: Assessment Notes

Automated tests exercise the library through the public packages listed in the Import Surface, in three layers.

The first layer covers single behaviours in isolation: the pairing of two class lists into nodes and the change status each pairing produces; the change status of a modifier node under each of the four combinations of present and absent values; the three facts each compatibility-change constant carries, and the effect of overriding and resetting them; the regular expression each filter kind builds from a filter string and the strings it then matches and rejects; the classification of a filter string into filter objects; the inclusion decision of `Filters` under empty, include-only, exclude-only and mixed lists; the string `getDifferenceDescription` returns for set and unset version labels; the four strings the semantic-version report returns; the sign group the text report emits for each change status and each compatibility combination; and the exception reason each documented failure raises.

The second layer covers behaviour that spans components: a comparison whose verdict depends on a superclass being reachable, run once with the classpath entry present and once without it, and once more with missing classes ignored; a comparison restricted by include and exclude filters, checked both in the returned tree and in the class pool; a rule override observed simultaneously in the model, the text report, the XML document and the semantic-version string; the composition of two report generators over one tree, where the second observes the first's pruning; and the agreement of ordering across the returned list, the text report and the XML document.

The third layer covers the compatibility-rule catalogue itself: for each rule that this document names, one pair of class versions that triggers it and one that does not, asserting the change attached to the expected node and the aggregate binary and source verdicts that follow from it.

Tests build their inputs as javassist classes of their own and never read a class file from disk or from an archive. All assertions use only the names and behaviours this document describes; nothing that is unspecified here is asserted, and no test depends on log output, on element ordering the document leaves open, or on whitespace in the XML report.
