# ArchUnit Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`archunit` is a Java bytecode-analysis library that imports compiled classes into a connected domain graph and evaluates architectural rules over that graph. The Maven artifact is `com.tngtech.archunit:archunit`; its public projections include imported classes and packages, members and accesses, fluent and custom rule results, architecture-library views, metrics, and persistent frozen violations.

The library operates without a dedicated test runner. A caller imports local classes, directories, URLs, or JARs, inspects the resulting model, composes an `ArchRule`, and checks or evaluates that rule using any Java test framework.

## Non-Goals

- This specification does not require the separate JUnit 4, JUnit 5, or JUnit 6 runner and engine artifacts.
- This specification does not require experimental module-definition and generic cycle-detection APIs.
- This specification does not require classpath-wide scans, network resources, Maven plugins, or remote artifact resolution.
- This specification does not define private helpers, package-private state, bytecode-parser internals, cache layout, log text, exact exception messages, or exact failure-report prose.
- This specification does not require predefined coding-rule constants beyond the architecture, slice, PlantUML, metric, and freezing behaviors described below.

## Representative Workflows

### Import and inspect a local class graph

```java
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;

JavaClasses classes = new ClassFileImporter().importClasses(Service.class, Controller.class);
JavaClass service = classes.get(Service.class);
String packageName = service.getPackageName();
service.getMethods();
service.getDirectDependenciesFromSelf();
service.getAccessesFromSelf();
```

When classes are imported together, the returned graph must expose class metadata and directed relationships consistently from its collection, member, access, and dependency views.

### Define and evaluate a fluent rule

```java
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.EvaluationResult;

ArchRule rule = noClasses()
    .that().resideInAPackage("..service..")
    .should().dependOnClassesThat().resideInAPackage("..controller..");

EvaluationResult result = rule.evaluate(classes);
boolean violated = result.hasViolation();
```

The fluent expression must select the requested class subset, test dependencies using package-identifier semantics, and expose violations through both `evaluate` and `check`.

### Freeze an existing rule and compute component metrics

```java
import com.tngtech.archunit.library.freeze.FreezingArchRule;
import com.tngtech.archunit.library.metrics.ArchitectureMetrics;
import com.tngtech.archunit.library.metrics.LakosMetrics;
import com.tngtech.archunit.library.metrics.MetricsComponents;

FreezingArchRule frozen = FreezingArchRule.freeze(rule);
MetricsComponents<JavaClass> components = MetricsComponents.fromClasses(classes);
LakosMetrics metrics = ArchitectureMetrics.lakosMetrics(components);
```

The frozen rule must compare current violations with durable known violations, while the metric projection must derive stable graph measurements from the same imported class dependencies.

## Importing Bytecode and Selecting Locations

This section defines how callers select local bytecode and how imported inputs become one domain graph.

**Import sources and filters.**

- A `ClassFileImporter` must accept classes, packages, filesystem paths, URLs, `Location` values, and open JAR files as import sources.
- When a plural import method receives several sources, the importer must return one `JavaClasses` collection containing the classes selected from their union.
- When `withImportOption` or `withImportOptions` supplies filters, the importer must retain only locations for which every configured `ImportOption.includes` decision is true.
- `ImportOption.Predefined.DO_NOT_INCLUDE_JARS` must exclude JAR locations, and `DO_NOT_INCLUDE_TESTS` must exclude conventional Maven and Gradle test-output locations.
- A `Location` must represent a file, JAR, or runtime-image URI and expose URI conversion, containment, regular-expression matching, JAR classification, and archive classification.
- If an import source is null, malformed, unreadable, or not a supported local location, then importing must raise an ordinary Java argument, URI, or I/O-related runtime exception rather than returning fabricated classes.

**Missing classes and source metadata.**

- When referenced bytecode is absent from the requested sources and classpath resolution is enabled, the importer must attempt to resolve the missing class from the runtime classpath.
- When missing-class resolution is disabled or unsuccessful, the importer must create a name-preserving incomplete `JavaClass` stub and `isFullyImported` must return false for that stub.
- Where `enableMd5InClassSources` is true, an imported class source must expose an MD5 value; where it is false, the source must report that no digest is present.

## Domain Graph and Query Semantics

This section defines the public views of classes, packages, members, types, annotations, accesses, and dependencies.

**Collections, names, and packages.**

- `JavaClasses` must behave as a read-only collection, and `that` must return the subset accepted by a `DescribedPredicate` while preserving a derived description.
- `JavaClasses.contain` must test membership by reflected class or fully qualified name, and `get` must return the matching `JavaClass`.
- If `JavaClasses.get` or `getPackage` cannot find the requested item, then it must raise `IllegalArgumentException`; the corresponding `contain` or `containPackage` query must return false.
- A `JavaClass` must expose fully qualified name, full name, simple name, package name, `JavaPackage`, modifiers, class-kind flags, source location, and optional source metadata.
- A `JavaPackage` must expose its name, contained classes, direct subpackages, package-tree traversal, and lookup of relative package names.

**Types, hierarchy, and members.**

- A `JavaClass` must expose raw and generic superclass and interface views, direct and transitive subclasses, permitted subclasses, enclosing declarations, and assignability queries.
- Member views must distinguish declared `getFields`, `getMethods`, `getConstructors`, and `getCodeUnits` from inherited `getAllFields`, `getAllMethods`, `getAllConstructors`, and `getAllMembers`.
- Member lookup by name and parameter types must resolve the requested field, method, constructor, or code unit; `tryGet...` variants must return an empty `Optional` when absent.
- The `JavaClass.getMethod` and `tryGetMethod` families must each expose a distinct overload accepting only `name` for zero-parameter methods, beside overloads accepting `name` followed by either reflected `Class<?>` varargs or fully qualified parameter-type-name `String` varargs.
- If a non-optional member lookup is ambiguous or absent, then it must raise `IllegalArgumentException`.
- `JavaMember` and its field and code-unit subtypes must expose owner, name, full name, modifiers, annotations, and source location; `JavaMethod` must additionally expose return type and default value, and `JavaCodeUnit` must expose parameters and throws declarations.
- Annotation lookup by `Class` must return a typed runtime annotation when its type is loadable; lookup by type name must return a `JavaAnnotation` whose parameter values remain accessible without loading the annotation class.

**Accesses and dependencies.**

- A `JavaAccess` must expose origin code unit, target owner, target, source location, and line number, while field accesses must distinguish `GET` and `SET` through `JavaFieldAccess.AccessType`.
- A class's `getAccessesFromSelf` and typed call, reference, and field-access views must report accesses whose origin belongs to that class; the corresponding `...ToSelf` views must report graph accesses resolved to that class or member.
- Access targets must preserve the bytecode owner, member name, and parameter types even when no imported member resolves.
- Field and constructor targets must resolve to zero or one member, while method call targets must expose every matching method in ambiguous interface inheritance.
- `getDirectDependenciesFromSelf` and `getDirectDependenciesToSelf` must project type, member-signature, annotation, inheritance, and code-access relationships as directed `Dependency` values.
- `getTransitiveDependenciesFromSelf` must return the reachable dependency closure without treating the origin class as a new external dependency.
- The public domain projection chain must expose `Dependency.getOriginClass` and `getTargetClass` as the directed endpoint classes, `JavaAccess.getOriginOwner` and `getTargetOwner` as the origin code-unit owner and bytecode target owner, `JavaAccess.getTarget().getOwner` as that same target owner, and `JavaField.getRawType` as the erased declared field type.
- When `JavaClass.isEquivalentTo` receives a reflected `Class<?>`, it must return true exactly when the modeled class and reflected class have the same fully qualified name.

## Package Patterns and Predicate Composition

This section defines the library-specific package language and reusable described predicates and functions.

**Package identifiers.**

- `PackageMatcher.of` must compile a package identifier where `*` matches one non-empty package segment and `..` matches any sequence of package segments, including none.
- In a package identifier, `(*)` must capture one segment, `(**)` must capture any segment sequence, and `[a|b]` must match either alternative.
- `PackageMatcher.matches` must test the package name rather than a fully qualified class name, and `match` must return an empty `Optional` when the package does not match.
- `PackageMatcher.Result.getGroup` must use one-based capture indexes in textual capture order.
- When `PackageMatcher.match` returns a result, `PackageMatcher.Result.getNumberOfGroups` must return the number of capture groups available through `getGroup`.
- `PackageMatchers.of` must create a described predicate that accepts a package when any supplied package identifier matches it.
- `PackageMatchers` must be the concrete final `DescribedPredicate<String>` returned by both `of` factory overloads, one accepting `packageIdentifiers` as `String` varargs and one accepting them as a `Collection<String>`; its public `test(String)` query must return whether any configured identifier matches the supplied package name.
- If a package identifier nests groups illegally, uses `(..)`, or requests an absent or zero capture index, then matching must raise `IllegalArgumentException`.

**Described values.**

- A `DescribedPredicate` must expose its description, test inputs, combine with `and`, `or`, and `negate`, adapt with `as` and `forSubtype`, and retain short-circuit boolean semantics.
- A `ChainableFunction` must apply its mapping and compose with `then`; a `DescribedFunction` must additionally expose and override its user-facing description.
- Predicates exposed by `HasName.Predicates` and `JavaClass.Predicates` must select names, class kinds, assignability, package residence, and member containment according to their method names and package-matcher semantics.
- `JavaClass.Predicates.resideInAPackage` and `resideOutsideOfPackage` must each accept one `packageIdentifier` string and return a `DescribedPredicate<JavaClass>` whose result follows the shared `PackageMatcher` language.

## Rule Definition, Evaluation, and Extension

This section defines rule entry points, fluent composition, custom predicates and conditions, and observable results.

**Rule entry points and fluent selection.**

- `ArchRuleDefinition` must expose `classes`, `noClasses`, `theClass`, `noClass`, `members`, `fields`, `codeUnits`, `constructors`, and `methods`, together with their plural negated forms and priority-bound variants.
- Fluent `that`, `and`, and `or` selectors must combine predicates over the selected class or member kind, and `should`, `andShould`, and `orShould` clauses must combine conditions over that same selected kind.
- The `fields`, `methods`, `constructors`, and `codeUnits` entry points must retain their concrete selected type through `that` and `should`: `JavaField`, `JavaMethod`, `JavaConstructor`, and `CODE_UNIT extends JavaCodeUnit`, respectively; their typed condition overloads must accept `ArchCondition<? super JavaField>`, `ArchCondition<? super JavaMethod>`, `ArchCondition<? super JavaConstructor>`, and `ArchCondition<? super CODE_UNIT>`, and must return the corresponding typed conjunctions.
- Class conditions must cover names, packages, modifiers, annotations, assignability, inheritance, access, dependency, containment, and only-accessed-by constraints exposed by the public fluent interfaces.
- Member conditions must cover names, modifiers, annotations, declaration packages, field types, code-unit parameter and return types, throws declarations, and calls exposed by the public fluent interfaces.
- Negated entry points must invert the final condition result rather than merely negating the selector.

**Evaluation and reporting.**

- `ArchRule.evaluate` must return an `EvaluationResult`, and `check` must raise `AssertionError` exactly when that result has at least one non-ignored violation.
- `ArchRule.as` must return a rule with the replacement description, `because` must return a rule with the appended reason, and neither operation must mutate the receiver; these semantics must hold for ordinary fluent, composite, layered, onion, and frozen rule values, while `allowEmptyShould` must override empty-selection handling for the returned rule.
- If an evaluated should-clause receives no selected objects and empty selections are forbidden, then evaluation must report a violation; where empty selections are allowed, it must not report a violation solely for being empty.
- `EvaluationResult` must expose priority, violation presence, a `FailureReport`, description filtering, result aggregation through `add`, and typed violation delivery through `handleViolations`.
- `FailureReport` and `FailureMessages` must expose violation-detail lines and violation counts without requiring callers to parse exact full report text.
- `EvaluationResult.getFailureReport` must return its associated `FailureReport`, and `FailureReport.getDetails` must return a `List<String>` with one entry for each violation-detail line without defining exact line wording.
- `Priority` must provide `LOW`, `MEDIUM`, and `HIGH`, and default fluent rule entry points must use `MEDIUM`.

**Custom conditions.**

- An `ArchCondition` must receive `init` once before item checks, `check` once for each selected item, and `finish` once after checks, with a shared `ConditionEvents` collector.
- The public `ArchCondition<T>` callback contract must pass a `Collection<T>` named `allObjectsToTest` to `init`, one `T` named `item` together with `ConditionEvents` named `events` to abstract `check`, and `ConditionEvents` named `events` to `finish`.
- External subclasses must initialize `DescribedPredicate` and `ArchCondition` through their public description-plus-format-arguments constructors and `DescribedFunction` through its protected description-plus-format-arguments constructor; each constructed value must expose the formatted description while leaving callback implementation to the subclass.
- `ArchCondition.and` and `or` must combine event outcomes, while `as` and `forSubtype` must preserve behavior and adjust description or generic type.
- `SimpleConditionEvent.satisfied` must create a non-violation event, `violated` must create a violation event, and `invert` must reverse that classification.
- A `CompositeArchRule` must evaluate every constituent rule and aggregate all of their violations, priorities, and descriptions under its configured description.
- `CompositeArchRule.of` must start a composite from one `ArchRule` or an iterable of rules, and `and` must return a composite containing the supplied additional rule while preserving evaluation of every constituent.

## Architecture, Slice, and Diagram Rules

This section defines the selected higher-level projections built from imported dependency relationships.

**Layered and onion architectures.**

- `Architectures.layeredArchitecture` must require an explicit dependency setting before layer definitions are evaluated.
- A layered architecture must define required or optional named layers by package identifiers or predicates and constrain incoming or outgoing access with `whereLayer` rules.
- `LayeredArchitecture.layer` and `optionalLayer` must each accept a layer `name` and return the public `LayerDefinition` carrier, whose `definedBy` overloads must accept either `packageIdentifiers` as `String` varargs or a `DescribedPredicate<? super JavaClass>` and return the `LayeredArchitecture`.
- `LayeredArchitecture.whereLayer` must accept a layer `name` and return the public `LayerDependencySpecification` carrier; `mayOnlyAccessLayers` must accept allowed `layerNames` as `String` varargs, `mayNotAccessAnyLayer` must accept no arguments, and both must return the `LayeredArchitecture`.
- `consideringAllDependencies` must consider all direct class dependencies, `consideringOnlyDependenciesInAnyPackage` must restrict both ends to selected packages, and `consideringOnlyDependenciesInLayers` must restrict both ends to defined layers.
- `ensureAllClassesAreContainedInArchitecture` must report imported classes outside all layers unless an explicit package or predicate exclusion matches them.
- If a layer name is duplicated or a constraint names an undefined layer, then evaluation must raise `IllegalArgumentException`.
- An onion architecture must enforce independence of domain models, inward dependency from domain services, application-to-domain dependency, adapter-to-inner-layer dependency, and independence between named adapters.
- Optional-layer, ignored-dependency, description, reason, and empty-selection options must affect architecture rules with the same observable semantics as ordinary `ArchRule` values.

**Slices.**

- `SlicesRuleDefinition.slices().matching` must group classes by package-pattern capture groups and use the captured values as slice identifiers.
- `assignedFrom` must group classes by `SliceAssignment.getIdentifierOf`, and `SliceIdentifier.ignore` must exclude a class from all slices.
- `SliceIdentifier.of` must accept either textual `parts` as `String` varargs or as a `List<String>` and return an included identifier; two identifiers must be equal exactly when their ordered parts are equal, and an empty parts sequence must raise `IllegalArgumentException`.
- A slice rule for `beFreeOfCycles` must report directed dependency cycles between distinct slices; `notDependOnEachOther` must report every dependency between distinct slices.
- Slice naming through `namingSlices` must substitute captured groups into the configured name pattern without changing membership or dependency results.

**PlantUML diagrams.**

- `PlantUmlArchCondition.adhereToPlantUmlDiagram` must read local component diagrams whose bracket components carry unique package-identifier stereotypes and whose directed arrows declare allowed dependencies.
- PlantUML dependency configuration must support all dependencies, only diagram-covered dependencies, or only dependencies in configured packages, and `ignoreDependencies` must remove matching origin-target pairs from consideration.
- If a diagram has an unsupported component declaration, missing or duplicate stereotype, invalid alias, invalid package identifier, or unsupported dependency arrow, then condition creation or evaluation must raise a runtime exception.

## Architecture Metrics

This section defines deterministic componentization and metric projections over dependency graphs.

**Components.**

- The two generic `MetricsComponent.of` factories must return a `MetricsComponent<T>` with the supplied `identifier` and elements, with one overload accepting `T` varargs and the other accepting a `Collection<T>`.
- `MetricsComponent.getIdentifier` must return the supplied component identifier, while `LakosMetrics.getCumulativeComponentDependency`, `getAverageComponentDependency`, `getRelativeAverageComponentDependency`, and `getNormalizedCumulativeComponentDependency` must return the CCD, ACD, RACD, and NCCD projections defined below.
- `MetricsComponent<T>` must implement the Java `Collection<T>` contract, so inherited operations including `size`, iteration, and membership must observe the same elements returned by `getElements`.
- `MetricsComponents.of` must preserve supplied component identifiers and elements; `from` must group elements by identifier function, and `fromPackages` and `fromClasses` must derive identifiers from package and class names.
- `tryGetComponent` must return an empty `Optional` for an unknown identifier, and metric queries for an unknown identifier must raise `IllegalArgumentException`.

**Metric families.**

- `ArchitectureMetrics.lakosMetrics` must expose a one-argument overload accepting `components` as `MetricsComponents<JavaClass>` and a generic two-argument overload accepting `components` as `MetricsComponents<T>` plus `getDependencies` as a `Function<T, Collection<T>>` that projects each element's outgoing dependencies for the calculation.
- Lakos `DependsOn` for a component must count the component itself and every transitively reachable component; CCD must sum those counts, ACD must divide CCD by component count, and RACD must divide ACD by component count.
- NCCD must divide CCD by the cumulative dependency value of a balanced binary tree with the same component count.
- Component dependency metrics must compute efferent coupling from distinct outgoing components, afferent coupling from distinct incoming components, instability as `Ce / (Ca + Ce)`, abstractness from public abstract classes divided by public classes, and normalized distance as `|A + I - 1|`.
- Visibility metrics must compute per-component relative visibility, the unweighted average of component relative visibility, and global visible elements divided by all elements.
- If a metric ratio has a zero denominator, then the metric must return `0.0` rather than a non-finite value.

## Frozen Violation State

This section defines how known rule violations are persisted, matched, updated, and refrozen.

**Freeze lifecycle.**

- `FreezingArchRule.freeze` must wrap an `ArchRule` while preserving its description, priority, `as`, `because`, and empty-selection behavior.
- When a frozen rule is evaluated for the first time, it must save all current violation lines and report no violation when store creation is allowed.
- When a frozen rule is evaluated after a baseline exists, it must report only current lines that do not match stored lines and must remove resolved lines from the store when updates are allowed.
- Where `freeze.refreeze` is true, evaluation must replace stored lines with all current lines and report no violation.
- If store creation or update is required but disabled, then evaluation must raise a runtime exception.

**Extension points and default store.**

- `persistIn` must use the supplied `ViolationStore`, and `associateViolationLinesVia` must use the supplied `ViolationLineMatcher` to pair stored and current lines.
- A `ViolationStore` must be initialized with properties, answer `contains`, save violation lines by rule, and return saved lines; configured `freeze.store.*` values must reach `initialize` without the namespace prefix.
- The default line matcher must ignore source line-number changes and generated anonymous-class or lambda number changes while requiring all other violation details to match.
- `TextFileBasedViolationStore` must persist rule identifiers and UTF-8 violation lines under `freeze.store.default.path`, honor creation and update permissions, and reload equivalent content across process-local instances.

## State Model

The core state is an imported directed graph. Nodes represent classes, packages, members, types, annotations, and access targets; edges represent containment, inheritance, signatures, annotations, bytecode accesses, and derived dependencies.

The public projections are the `JavaClasses` collection, package and member lookup views, from/to access views, dependency sets, predicate-filtered selections, rule evaluation and failure views, architecture slices and layers, component metrics, and durable frozen-violation files. Configuration state comes from the classpath-root `archunit.properties` resource and `archunit.`-prefixed system-property overrides; `ArchConfiguration` exposes reset, property, resolver, extension, MD5, and thread-local scope controls.

`ArchConfiguration.get` must return the active thread-local configuration when one is in scope and otherwise the global configuration; `setProperty` must update the named string property, and `reset` must discard programmatic changes and reload the configured resource together with applicable system-property overrides.

## Error Semantics

| Condition | Required result |
|---|---|
| Missing class or package in non-optional lookup | If the requested graph item is absent, then the lookup must raise `IllegalArgumentException`. |
| Missing or ambiguous member in non-optional lookup | If no unique matching member exists, then the lookup must raise `IllegalArgumentException`. |
| Invalid package identifier or capture index | If pattern syntax or group access is invalid, then `PackageMatcher` must raise `IllegalArgumentException`. |
| Failed reflection bridge | If a modeled class, member, or annotation type is not loadable, then `reflect` or typed annotation access must raise the applicable reflection-related runtime exception. |
| Forbidden empty should-clause | If no selected objects reach a rule whose empty selection is forbidden, then evaluation must produce a violation and `check` must raise `AssertionError`. |
| Architecture definition error | If layers are duplicated or referenced before definition, then the architecture must raise `IllegalArgumentException`. |
| Invalid PlantUML architecture | If a diagram violates supported component or arrow rules, then the condition must raise a runtime exception. |
| Forbidden freeze-store mutation | If required store creation or update is disabled, then the frozen rule must raise a runtime exception. |

## Cross-View Invariants

1. A class returned by `JavaClasses.get` must be the same logical class represented by package containment, member ownership, access origins or targets, and dependency endpoints.
2. Every typed field access, method call, constructor call, or reference in a class's from-self view must also occur in its general `getAccessesFromSelf` view and must contribute the corresponding direct dependency when its target owner differs.
3. A dependency reported from class A to class B must occur in A's `getDirectDependenciesFromSelf` and B's `getDirectDependenciesToSelf` with the same origin and target.
4. Package predicates used by `JavaClass.Predicates`, fluent rules, slices, layers, and PlantUML stereotypes must share the `PackageMatcher` language.
5. A rule's `evaluate(classes).hasViolation` must be true exactly when `check(classes)` raises `AssertionError`, after ignore patterns and empty-selection policy are applied.
6. Calling `as` or `because` on an ordinary, composite, architecture, or frozen rule must leave the receiver description unchanged and return a rule with the transformed public rule and report description without changing selected objects or violation membership.
7. Layer, onion, slice, and PlantUML rules must derive their findings from the same direct class dependencies exposed by the imported graph after their declared dependency filters and exclusions.
8. Component metrics built from imported classes must use the same class-to-class dependency direction exposed by `getDirectDependenciesFromSelf`.
9. A frozen rule must compare and persist the same current violation set that its wrapped rule exposes through `EvaluationResult`, subject only to the configured line matcher.

## Public Interface

### Import Surface

```java
import com.tngtech.archunit.ArchConfiguration;
import com.tngtech.archunit.base.ChainableFunction;
import com.tngtech.archunit.base.DescribedFunction;
import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.base.HasDescription;
import com.tngtech.archunit.core.domain.AccessTarget;
import com.tngtech.archunit.core.domain.Dependency;
import com.tngtech.archunit.core.domain.JavaAccess;
import com.tngtech.archunit.core.domain.JavaAnnotation;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.domain.JavaCodeUnit;
import com.tngtech.archunit.core.domain.JavaConstructor;
import com.tngtech.archunit.core.domain.JavaConstructorCall;
import com.tngtech.archunit.core.domain.JavaConstructorReference;
import com.tngtech.archunit.core.domain.JavaField;
import com.tngtech.archunit.core.domain.JavaFieldAccess;
import com.tngtech.archunit.core.domain.JavaGenericArrayType;
import com.tngtech.archunit.core.domain.JavaMember;
import com.tngtech.archunit.core.domain.JavaMethod;
import com.tngtech.archunit.core.domain.JavaMethodCall;
import com.tngtech.archunit.core.domain.JavaMethodReference;
import com.tngtech.archunit.core.domain.JavaModifier;
import com.tngtech.archunit.core.domain.JavaPackage;
import com.tngtech.archunit.core.domain.JavaParameter;
import com.tngtech.archunit.core.domain.JavaParameterizedType;
import com.tngtech.archunit.core.domain.JavaStaticInitializer;
import com.tngtech.archunit.core.domain.JavaType;
import com.tngtech.archunit.core.domain.JavaTypeVariable;
import com.tngtech.archunit.core.domain.JavaWildcardType;
import com.tngtech.archunit.core.domain.PackageMatcher;
import com.tngtech.archunit.core.domain.PackageMatchers;
import com.tngtech.archunit.core.domain.Source;
import com.tngtech.archunit.core.domain.SourceCodeLocation;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.core.importer.Location;
import com.tngtech.archunit.core.importer.Locations;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.CompositeArchRule;
import com.tngtech.archunit.lang.ConditionEvent;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.EvaluationResult;
import com.tngtech.archunit.lang.FailureMessages;
import com.tngtech.archunit.lang.FailureReport;
import com.tngtech.archunit.lang.Priority;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition;
import com.tngtech.archunit.library.Architectures;
import com.tngtech.archunit.library.dependencies.Slice;
import com.tngtech.archunit.library.dependencies.SliceAssignment;
import com.tngtech.archunit.library.dependencies.SliceIdentifier;
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition;
import com.tngtech.archunit.library.freeze.FreezingArchRule;
import com.tngtech.archunit.library.freeze.TextFileBasedViolationStore;
import com.tngtech.archunit.library.freeze.ViolationLineMatcher;
import com.tngtech.archunit.library.freeze.ViolationStore;
import com.tngtech.archunit.library.metrics.ArchitectureMetrics;
import com.tngtech.archunit.library.metrics.ComponentDependencyMetrics;
import com.tngtech.archunit.library.metrics.LakosMetrics;
import com.tngtech.archunit.library.metrics.MetricsComponent;
import com.tngtech.archunit.library.metrics.MetricsComponents;
import com.tngtech.archunit.library.metrics.VisibilityMetrics;
import com.tngtech.archunit.library.plantuml.rules.PlantUmlArchCondition;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `ArchConfiguration` | class | Reads, overrides, resets, and scopes importer, rule, and extension properties. |
| `HasDescription` | interface | Exposes a user-facing description. |
| `DescribedPredicate` | abstract class | Composable described predicate with subtype adaptation. |
| `ChainableFunction` | abstract class | Composable mapping function. |
| `DescribedFunction` | abstract class | Mapping function with a replaceable description. |
| `ClassFileImporter` | class | Imports local bytecode into a connected `JavaClasses` graph. |
| `ImportOption` | interface | Decides whether an import location is included. |
| `ImportOption.Predefined` | enum | Supplies standard JAR, test, archive, and package-info location filters. |
| `Location` | class | URI-backed import root and class-entry view. |
| `Locations` | class | Discovers classpath, package, class, and JAR locations. |
| `JavaClasses` | class | Read-only imported class collection with lookup and predicate filtering. |
| `JavaPackage` | class | Package tree, class membership, annotation, and traversal view. |
| `JavaClass` | class | Imported class metadata, hierarchy, members, accesses, and dependencies. |
| `JavaType` | interface | Common imported type protocol with name, erasure, and signature traversal. |
| `JavaParameterizedType` | interface | Parameterized raw type, owner, and type-argument view. |
| `JavaTypeVariable` | class | Named type variable with upper bounds. |
| `JavaWildcardType` | class | Wildcard type with upper and lower bounds. |
| `JavaGenericArrayType` | class | Generic array type with component and erasure views. |
| `JavaMember` | abstract class | Common owner, name, modifier, annotation, and source view for members. |
| `JavaField` | class | Imported field and incoming field-access view. |
| `JavaCodeUnit` | abstract class | Executable member with parameters, throws declarations, and accesses. |
| `JavaMethod` | class | Imported method with return, default-value, reflection, and incoming-call views. |
| `JavaConstructor` | class | Imported constructor and incoming-call view. |
| `JavaStaticInitializer` | class | Imported class-initialization code unit. |
| `JavaParameter` | class | Code-unit parameter with index, type, and annotations. |
| `JavaAnnotation` | class | Annotation type, owner, raw values, conversion, and visitor view. |
| `JavaAccess` | abstract class | Common origin, target, location, and line-number view for accesses. |
| `JavaFieldAccess` | class | Field read or write access. |
| `JavaMethodCall` | class | Method invocation access. |
| `JavaConstructorCall` | class | Constructor invocation access. |
| `JavaMethodReference` | class | Method-reference access. |
| `JavaConstructorReference` | class | Constructor-reference access. |
| `AccessTarget` | class | Bytecode target identity and member-resolution view. |
| `Dependency` | class | Directed class dependency with origin, target, and description. |
| `Source` | class | Import URI, optional file name, and optional MD5 metadata. |
| `SourceCodeLocation` | class | Source owner and line-number location. |
| `JavaModifier` | enum | Java visibility and declaration modifiers. |
| `PackageMatcher` | class | Compiles and applies the shared package-identifier language. |
| `PackageMatchers` | class | Matches any of several package identifiers. |
| `ArchRuleDefinition` | class | Static entry point for fluent class and member rules. |
| `ArchRule` | interface | Described check and evaluation contract. |
| `ArchCondition` | abstract class | Extensible lifecycle condition over selected objects. |
| `ConditionEvent` | interface | One condition outcome with inversion and violation handling. |
| `ConditionEvents` | interface | Mutable event collector exposed to custom conditions. |
| `SimpleConditionEvent` | class | Standard satisfied or violated condition event. |
| `EvaluationResult` | class | Aggregated priority and violation projection. |
| `FailureReport` | class | Rule details and failure-message projection. |
| `FailureMessages` | class | Collection of violation detail lines and counts. |
| `Priority` | enum | `LOW`, `MEDIUM`, and `HIGH` rule priorities. |
| `CompositeArchRule` | class | Aggregates several rules into one rule. |
| `Architectures` | class | Creates layered and onion architecture rules. |
| `SlicesRuleDefinition` | class | Creates package-pattern or assignment-based slice rules. |
| `Slice` | class | One named class slice and its dependencies. |
| `SliceAssignment` | interface | Maps a class to a slice identifier. |
| `SliceIdentifier` | class | Included or ignored slice identity. |
| `MetricsComponent` | class | Identified component and element collection. |
| `MetricsComponents` | class | Component collection and standard component factories. |
| `ArchitectureMetrics` | class | Creates Lakos, component-dependency, and visibility metrics. |
| `LakosMetrics` | class | CCD, ACD, RACD, and NCCD projection. |
| `ComponentDependencyMetrics` | class | Coupling, instability, abstractness, and distance projection. |
| `VisibilityMetrics` | class | Component, average, and global visibility projection. |
| `FreezingArchRule` | class | Baselines current rule violations and reports only regressions. |
| `ViolationStore` | interface | Persistent known-violation extension point. |
| `ViolationLineMatcher` | interface | Equivalence policy for stored and current violation lines. |
| `TextFileBasedViolationStore` | class | Default file-backed known-violation store. |
| `PlantUmlArchCondition` | class | Creates dependency conditions from local PlantUML component diagrams. |

### CLI Entry Points

There is no console script or executable main class for this package. Programmatic use is through Java imports and the Maven dependency.

## Appendix A: Environment

The working environment runs Java 17 on Linux with Maven 3 and without network access. The local Maven repository provides SLF4J API 2.0.18, JUnit Jupiter, and the task's test support dependencies with their cached transitive artifacts. The target artifact is not preinstalled, and dependency downloads are unavailable. The assessment environment provides the same JDK, Maven tooling, and dependency cache.

The project must declare Maven packaging in a root `pom.xml`, use `com.tngtech.archunit` as `groupId`, `archunit` as `artifactId`, and `1.6.0-SNAPSHOT` as `version`, and produce a JAR from the conventional `src/main/java` and `src/main/resources` roots.

## Appendix B: Assessment Notes

Assessment invokes public Java APIs through local Maven tests. Coverage spans local bytecode import, graph and package queries, members and accesses, package matching, predicate and condition composition, fluent rules, evaluation results, layered and onion architectures, slices, diagrams, component metrics, configuration, and frozen-state round trips. Checks focus on public behavior and cross-view consistency; private structure, exact diagnostic wording, classpath-wide nondeterminism, and representation-only text are not assessed.
