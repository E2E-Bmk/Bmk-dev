# japicmp Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`japicmp` is a Java archive-comparison library and command-line tool that compares the public class-file APIs of old and new local JARs. It produces one structured change graph for classes, constructors, methods, fields, inheritance, annotations, generics, modifiers, compatibility findings, and Java serialization status, then projects that graph as plain text, a semantic-version recommendation, XML, HTML, or Markdown.

The installable Maven artifact is `com.github.siom79.japicmp:japicmp`. Comparison is local and bytecode based; dependency classpaths are inputs only when inherited or referenced types are not present in the compared archives or the running JDK.

## Non-Goals

- This specification does not require the Maven plugin, Ant task, online service, or integrations from other reactor modules.
- This specification does not require resolving artifacts from remote repositories or comparing non-class resources inside archives.
- This specification does not require private helpers, package-private implementation types, test-only bytecode builders, logging text, stack-trace text, or object `toString()` formatting.
- This specification does not define exact report timestamps, absolute temporary paths, stylesheet bytes, or whitespace beyond the structural and marker rules below.
- This specification does not require report customization types other than the generator option types named in the public interface.
- This specification does not define compatibility rules beyond the public change families and defaults stated below.

## Representative Workflows

### Compare two local archives through the library

```java
import java.io.File;
import java.util.List;
import japicmp.cmp.JApiCmpArchive;
import japicmp.cmp.JarArchiveComparator;
import japicmp.cmp.JarArchiveComparatorOptions;
import japicmp.model.JApiClass;

JarArchiveComparatorOptions comparison = new JarArchiveComparatorOptions();
JarArchiveComparator comparator = new JarArchiveComparator(comparison);
JApiCmpArchive oldJar = new JApiCmpArchive(new File("old.jar"), "1.0.0");
JApiCmpArchive newJar = new JApiCmpArchive(new File("new.jar"), "2.0.0");

List<JApiClass> changes = comparator.compare(oldJar, newJar);
for (JApiClass changedClass : changes) {
    System.out.println(changedClass.getFullyQualifiedName());
    System.out.println(changedClass.getChangeStatus());
    System.out.println(changedClass.isBinaryCompatible());
}
```

WHEN both archive objects refer to readable local JARs, the comparison must return a deterministic class graph ordered by fully qualified class name. IF a referenced superclass or interface is required for compatibility analysis but is missing from the configured classpath, then comparison must raise `JApiCmpException` with reason `ClassLoading` unless the missing class policy ignores it.

### Filter and render one comparison graph

```java
import java.util.List;
import japicmp.config.Options;
import japicmp.model.JApiClass;
import japicmp.output.html.HtmlOutput;
import japicmp.output.html.HtmlOutputGenerator;
import japicmp.output.html.HtmlOutputGeneratorOptions;
import japicmp.output.semver.SemverOut;
import japicmp.output.stdout.StdoutOutputGenerator;

Options reports = Options.newDefault();
reports.setOutputOnlyModifications(true);
String text = new StdoutOutputGenerator(reports, changes).generate();
String semver = new SemverOut(reports, changes).generate();

HtmlOutputGeneratorOptions htmlOptions = new HtmlOutputGeneratorOptions();
htmlOptions.setTitle("API changes");
htmlOptions.setSemanticVersioningInformation(semver);
HtmlOutput html = new HtmlOutputGenerator(changes, reports, htmlOptions).generate();
```

WHEN multiple generators receive the same comparison graph and logically equivalent report options, each projection must describe the same retained classes, members, change statuses, compatibility findings, and semantic-version level. IF output-only filtering removes every graph node, then the plain-text projection must report `No changes.` and the other projections must contain no class-detail entries.

### Run the local executable JAR

```bash
java -jar target/japicmp-0.26.2-SNAPSHOT-jar-with-dependencies.jar \
  --old old.jar --new new.jar --only-modified --markdown
```

WHEN the required archive paths are valid, the command must write the selected report to standard output and exit successfully. IF an option is unknown, an option argument is missing, an archive is unreadable, or a required old/new archive is absent, then the command must write a concise error to standard error, print the help hint to standard output, and exit with status `1`.

## Archive Inputs and Comparison

Archive comparison turns local JAR bytes into the shared public model while honoring access, classpath, annotation, synthetic-element, and missing-class policies.

**Archive values.** A `JApiCmpArchive` must accept either a local `File` plus a version string, or a JAR byte array plus a version string and display name. WHEN constructed from a file, `getFile()` must be present and `getBytes()` must be empty; WHEN constructed from bytes, `getBytes()` and `getName()` must be present and `getFile()` must be empty; in both cases `getVersion()` must preserve the supplied version text through `Version.getStringVersion()`.

**Comparator execution.** A `JarArchiveComparator` must accept `JarArchiveComparatorOptions` and expose comparison for either one old/new archive pair or two archive lists. WHEN comparison succeeds, it must return one `JApiClass` for every retained class present in either side, sort the class list case-insensitively by fully qualified name, and sort each class's methods case-insensitively by method name while preserving the comparison order of overloads with equal names. IF an archive contains no file and no bytes, cannot be opened as a JAR, or contains unreadable class bytes, then comparison must raise `JApiCmpException` with reason `IllegalArgument` or `IoException` matching the failure category.

**Comparison options.** A new `JarArchiveComparatorOptions` must default to access level `PROTECTED`, one common classpath, excluded synthetic elements, annotation comparison enabled, and class-file-format reporting disabled. WHERE `ClassPathMode.ONE_COMMON_CLASSPATH` is selected, `getClassPathEntries()` must supply the shared dependency classpath; WHERE `TWO_SEPARATE_CLASSPATHS` is selected, `getOldClassPath()` and `getNewClassPath()` must supply their respective dependency classpaths. WHEN `setIncludeSynthetic(true)` is used, synthetic classes and members must remain eligible for the graph; WHEN `setNoAnnotations(true)` is used, annotation differences must not populate model annotation changes.

**Missing classes.** WHEN `IgnoreMissingClasses.setIgnoreAllMissingClasses(true)` is active, unresolved inherited types must not abort comparison. WHERE regular-expression entries are added through `getIgnoreMissingClassRegularExpression()`, only matching unresolved class names must be ignored. IF an unresolved class matches neither policy, then the comparator must raise `JApiCmpException` with reason `ClassLoading`.

**Compatibility overrides.** WHEN an `OverrideCompatibilityChange` is added, its `compatibilityChange`, `binaryCompatible`, `sourceCompatible`, and `semanticVersionLevel` values must override that change type for the comparator instance's produced graph. WHEN a later comparator is constructed without the override, the default values in `JApiCompatibilityChangeType` must be restored.

## Change Graph and Compatibility

The comparison result is a navigable old/new graph whose nodes expose structural status separately from binary, source, semantic-version, and serialization compatibility.

**Graph shape.** Each `JApiClass` must expose `getFullyQualifiedName()`, `getChangeStatus()`, `getClassType()`, `getSuperclass()`, `getInterfaces()`, `getConstructors()`, `getMethods()`, `getFields()`, `getAnnotations()`, `getGenericTemplates()`, `getClassFileFormatVersion()`, `getSerialVersionUid()`, `isBinaryCompatible()`, `isSourceCompatible()`, `getJavaObjectSerializationCompatible()`, and `getCompatibilityChanges()`. Each `JApiBehavior` must expose its name, parameters, exceptions, annotations, generic templates, modifier projections, change status, compatibility booleans, and compatibility changes; `JApiMethod` must additionally expose `getReturnType()`. Each `JApiField` must expose its name, type, generic types, annotations, modifiers, change status, compatibility booleans, and compatibility changes.

**Structural status.** WHEN an element exists only in the new archive, its `JApiChangeStatus` must be `NEW`; WHEN it exists only in the old archive, its status must be `REMOVED`; WHEN corresponding elements have no modeled difference, its status must be `UNCHANGED`; WHEN both sides exist and at least one modeled property differs, its status must be `MODIFIED`. A class must become `MODIFIED` when a retained constructor, method, field, superclass, interface, annotation, generic template, class type, modifier, or class-file-format value changes.

**Old/new values.** A `JApiModifier`, `JApiType`, `JApiReturnType`, `JApiSuperclass`, `JApiClassType`, `JApiGenericTemplate`, and annotation element must retain old and new projections independently. WHEN one side is absent, its optional getter must be empty and its string projection must use the public not-available value rather than inventing a counterpart. WHEN both values are equal, the nested node's status must be `UNCHANGED`; WHEN both are present and unequal, its status must be `MODIFIED`.

**Modifier vocabulary.** Access modifiers must use `PUBLIC`, `PROTECTED`, `PACKAGE_PROTECTED`, and `PRIVATE`; paired modifier projections must use `ABSTRACT`/`NON_ABSTRACT`, `FINAL`/`NON_FINAL`, `STATIC`/`NON_STATIC`, `TRANSIENT`/`NON_TRANSIENT`, `VOLATILE`/`NON_VOLATILE`, `SYNTHETIC`/`NON_SYNTHETIC`, `BRIDGE`/`NON_BRIDGE`, and `VARARGS`/`NON_VARARGS`. WHEN a modifier changes between old and new elements, its `JApiModifier.getChangeStatus()` must be `MODIFIED` and its old/new optional getters must preserve both enum values.

**Member identity.** Methods and constructors must be paired by declaring class, name, and erased parameter signature, while fields must be paired by declaring class and field name. WHEN a method return type changes without a parameter-signature change, the same `JApiMethod` node must carry a `JApiReturnType` whose status is `MODIFIED`. WHEN generic signature metadata changes without an erased descriptor change, the affected generic projections must change while the erased parameter or return type remains addressable.

**Compatibility aggregation.** A node's `getCompatibilityChanges()` must list the applicable `JApiCompatibilityChange` values, and each value must expose its type plus binary, source, and semantic-version projections. A class's `isBinaryCompatible()` and `isSourceCompatible()` must be false when the class or any retained descendant finding is incompatible in the corresponding dimension. WHEN no incompatible finding exists in a dimension, that dimension must remain true even when compatible additions or metadata changes are present.

**Default compatibility families.** The following public change types must retain these default projections:

| Default projection | `JApiCompatibilityChangeType` members |
|---|---|
| Binary incompatible, source incompatible, `MAJOR` | `CLASS_REMOVED`, `CLASS_NOW_ABSTRACT`, `CLASS_NOW_NOT_EXTENDABLE`, `CLASS_NO_LONGER_PUBLIC`, `CLASS_TYPE_CHANGED`, `CLASS_LESS_ACCESSIBLE`, `SUPERCLASS_REMOVED`, `SUPERCLASS_MODIFIED_INCOMPATIBLE`, `INTERFACE_REMOVED`, `METHOD_REMOVED`, `METHOD_REMOVED_IN_SUPERCLASS`, `METHOD_LESS_ACCESSIBLE`, `METHOD_LESS_ACCESSIBLE_THAN_IN_SUPERCLASS`, `METHOD_IS_STATIC_AND_OVERRIDES_NOT_STATIC`, `METHOD_RETURN_TYPE_CHANGED`, `METHOD_NOW_ABSTRACT`, `METHOD_NOW_FINAL`, `METHOD_NOW_STATIC`, `METHOD_NO_LONGER_STATIC`, `METHOD_ABSTRACT_NOW_DEFAULT`, `METHOD_NON_STATIC_IN_INTERFACE_NOW_STATIC`, `METHOD_STATIC_IN_INTERFACE_NO_LONGER_STATIC`, `FIELD_STATIC_AND_OVERRIDES_STATIC`, `FIELD_LESS_ACCESSIBLE_THAN_IN_SUPERCLASS`, `FIELD_NOW_FINAL`, `FIELD_NOW_STATIC`, `FIELD_NO_LONGER_STATIC`, `FIELD_TYPE_CHANGED`, `FIELD_REMOVED`, `FIELD_REMOVED_IN_SUPERCLASS`, `FIELD_LESS_ACCESSIBLE`, `CONSTRUCTOR_REMOVED`, `CONSTRUCTOR_LESS_ACCESSIBLE` |
| Binary compatible, source incompatible, `MINOR` | `CLASS_NOW_CHECKED_EXCEPTION`, `CLASS_GENERIC_TEMPLATE_CHANGED`, `CLASS_GENERIC_TEMPLATE_GENERICS_CHANGED`, `METHOD_RETURN_TYPE_GENERICS_CHANGED`, `METHOD_PARAMETER_GENERICS_CHANGED`, `METHOD_NO_LONGER_VARARGS`, `METHOD_ADDED_TO_INTERFACE`, `METHOD_NOW_THROWS_CHECKED_EXCEPTION`, `METHOD_NO_LONGER_THROWS_CHECKED_EXCEPTION`, `METHOD_ABSTRACT_ADDED_TO_CLASS`, `METHOD_ABSTRACT_ADDED_IN_SUPERCLASS`, `METHOD_ABSTRACT_ADDED_IN_IMPLEMENTED_INTERFACE`, `FIELD_GENERICS_CHANGED` |
| Binary compatible, source compatible, `MINOR` | `ANNOTATION_DEPRECATED_ADDED`, `SUPERCLASS_ADDED`, `INTERFACE_ADDED`, `METHOD_RETURN_TYPE_COVARIANT_CHANGED`, `METHOD_NOW_VARARGS`, `METHOD_DEFAULT_ADDED_IN_IMPLEMENTED_INTERFACE`, `METHOD_NEW_DEFAULT`, `METHOD_NEW_STATIC_ADDED_TO_INTERFACE` |
| Binary compatible, source compatible, `PATCH` | `ANNOTATION_ADDED`, `ANNOTATION_MODIFIED`, `ANNOTATION_REMOVED`, `METHOD_ADDED_TO_PUBLIC_CLASS`, `METHOD_MOVED_TO_SUPERCLASS`, `FIELD_NOW_TRANSIENT`, `FIELD_NOW_VOLATILE`, `FIELD_NO_LONGER_TRANSIENT`, `FIELD_NO_LONGER_VOLATILE` |

WHEN a change type appears in the table, its `isBinaryCompatible()`, `isSourceCompatible()`, and `getSemanticVersionLevel()` must equal that row until explicitly overridden. IF a requested compatibility type is absent from the enum, then `valueOf` must follow normal Java enum failure behavior.

**Serialization status.** A class implementing the serialization projection must return `NOT_SERIALIZABLE`, `SERIALIZABLE_COMPATIBLE`, or a `SERIALIZABLE_INCOMPATIBLE_*` status that identifies changes to `serialVersionUID`, class type, Serializable/Externalizable participation, serializable fields, class removal, default UID, or superclass. WHEN `JApiJavaObjectSerializationChangeStatus.isIncompatible()` is called, it must return false only for `NOT_SERIALIZABLE` and `SERIALIZABLE_COMPATIBLE` and true for every incompatible status.

## Inclusion and Exclusion Filters

Filters select classes and members before the public change graph is finalized, using the documented Javadoc-like syntax or annotation names.

**Filter collections.** `Filters.getIncludes()` and `getExcludes()` must return mutable lists of `Filter` objects used by `includeClass`, `includeBehavior`, and `includeField`. WHEN a matching exclusion exists for the requested element kind, exclusion must win. WHEN at least one include filter exists for an element kind, a matching include must be required; WHEN no include filter exists for that kind, the element must remain included unless excluded.

**Class and package patterns.** A `JavaDocLikeClassFilter` must match a fully qualified class name, treat `*` as a wildcard, and include nested classes of a matched outer class. A `JavadocLikePackageFilter` must match the named package plus subpackages by default; WHEN its `exclusive` constructor flag is true, it must match only the named package. IF a class has no package, then package matching must use the empty package name.

**Behavior and field patterns.** A `JavadocLikeBehaviorFilter` must accept `fully.qualified.Class#member(parameter.Type,...)`, treat `*` as a wildcard, and require the declaring class, member name, parameter count, and each erased parameter type to match. A `JavadocLikeFieldFilter` must accept `fully.qualified.Class#field`, treat `*` as a wildcard, and require both class and field patterns to match. IF a behavior filter omits `#`, a method name, an opening parenthesis, or a closing parenthesis, or places the closing parenthesis before the opening parenthesis, then construction must raise `JApiCmpException` with reason `CliError`; IF a field filter does not split into exactly a class part and field part, then construction must raise the same exception type and reason.

**Annotation patterns.** An annotation filter string must begin with `@` followed by the annotation's fully qualified name. WHEN an annotation class filter evaluates a nested class, an annotation on the declaring outer class must count as a match. WHEN annotation behavior and field filters evaluate a member, an annotation on the member, its declaring class, or its declaring outer class must count as a match.

**Option parsing into filters.** WHEN `Options.addIncludeFromArgument()` or `addExcludeFromArgument()` receives a semicolon-separated string, entries beginning with `@` must create class, behavior, and field annotation filters; entries containing `#` plus `(` must create behavior filters; entries containing `#` without `(` must create field filters; all other entries must create both class and package filters. IF any entry has invalid syntax, then the method must raise `JApiCmpException` with reason `CliError`.

## Semantic Versioning

Semantic-version projections reduce the graph's compatibility findings and archive-version strings to stable public values.

**Version parsing.** A `Version` must preserve the original string through `getStringVersion()` and expose `getSemanticVersion()` when the text contains a numeric `major.minor.patch` sequence, with arbitrary text before or after that sequence. IF the text contains no such sequence or a numeric component overflows an integer, then `getSemanticVersion()` must return an empty `Optional`.

**Version comparison.** A `SemanticVersion` must expose `getMajor()`, `getMinor()`, and `getPatch()`. WHEN `computeChangeType(other)` compares two semantic versions, it must return a present optional containing `MAJOR` for any major-component difference, otherwise `MINOR` for any minor-component difference, otherwise `PATCH` for any patch-component difference, and otherwise `UNCHANGED`; comparison direction must not change the selected component.

**Archive-set change.** A `VersionChange` must compare old and new semantic-version lists pairwise and return the highest ranked `SemanticVersion.ChangeType`; WHEN every value within each side is identical, it must compare the first old value with the first new value. IF either list is empty and its respective ignore flag is false, then `computeChangeType()` must raise `JApiCmpException` with reason `IllegalArgument`; WHEN an empty side is ignored, the method must return an empty optional. IF both lists are nonempty, are not each internally identical, and have different sizes, then the method must raise `JApiCmpException` with reason `IllegalArgument`.

**Graph recommendation.** A `SemverOut` must inspect all retained class, superclass, interface, constructor, method, field, and annotation findings and return `1.0.0` when any applicable finding has level `MAJOR`, otherwise `0.1.0` when any has level `MINOR`, otherwise `0.0.1` when the nonempty graph has only `PATCH` findings, and `0.0.0` when the retained graph is empty. WHERE a finding belongs to a non-public and non-protected element, it must contribute no level above `PATCH`.

## Report Projections

Report generators project the same filtered graph into deterministic content while preserving each node's status and compatibility meaning.

**Shared filtering and ordering.** WHEN `generate()` is called on the plain-text, HTML, XML, or Markdown generator, output-only flags in `Options` must filter the supplied graph before rendering. Classes and methods must retain the comparator's deterministic order, and projections that sort member tables must use member names as their stable key. WHERE `outputOnlyModifications` is true, unchanged-only nodes must be omitted; WHERE `outputOnlyBinaryIncompatibleModifications` is true, compatible-only nodes must be omitted; WHERE `reportOnlySummary` is true, detailed member sections must be omitted.

**Plain text.** `StdoutOutputGenerator.generate()` must begin with `Options.getDifferenceDescription()`. Each rendered node must use `+++` for `NEW`, `---` for `REMOVED`, `***` for `MODIFIED`, and `===` for `UNCHANGED`, followed by `!` for binary incompatibility, `*` for source-only incompatibility, or a space when both dimensions are compatible. WHEN the retained graph is empty, the output must contain `No changes.`.

**HTML.** `HtmlOutputGenerator.generate()` must return an `HtmlOutput` whose `getHtml()` value is a complete HTML document containing the configured title, comparison metadata, class summary, and, unless summary-only mode is active, sections for the retained class details and members. WHERE a custom title is set through `HtmlOutputGeneratorOptions.setTitle()`, both the document title and visible title must use it; WHERE semantic-version information is set, report metadata must expose it. IF a configured stylesheet path cannot be read, then generation must raise `JApiCmpException` with an I/O-related reason.

**XML.** `XmlOutputGenerator.generate()` must return an `XmlOutput` containing both a `JApiCmpXmlRoot` model and, when stream generation succeeds, XML bytes obtainable from `getXmlOutputStream()`. The root must expose retained classes, old/new archive descriptions and versions, access level, filters, missing-class settings, output flags, title, and semantic-version information. WHERE schema creation is enabled, `writeToFiles()` must write the XML report and companion schema beside the configured XML path. IF XML binding or file writing fails, then generation must raise `JApiCmpException` with reason `JaxbException` or `IoException`.

**Markdown.** `MarkdownOutputGenerator.generate()` must return a report with a summary, comparison options, a class table, and detailed sections for retained classes unless summary-only mode is active. The default Markdown options must sort classes by fully qualified name and expose configurable title, header, message, and sort projections. WHEN old/new target versions are set in `MarkdownOptions`, the summary must use those values as the compared version labels.

**Deterministic comparison content.** WHEN generators receive equivalent model graphs and options, status markers, class/member identities, compatibility-change names, and semantic-version content must agree across projections. Report creation timestamps and absolute archive paths must be treated as metadata; WHERE `reportOnlyFilename` is true, archive descriptions must use filenames rather than absolute paths.

## Command-Line Behavior

The executable JAR exposes one command that compares local old and new archives and selects a projection or build-breaking policy.

**Required inputs and help.** The command must accept `-o`/`--old` and `-n`/`--new`, each containing one or more local JAR paths separated by semicolons. WHEN `-h` or `--help` appears, the command must print the synopsis and option descriptions and exit successfully without requiring archive arguments. IF either archive option is absent outside help mode, a file does not exist, a file is unreadable, or a file is not a JAR, then the command must exit with status `1`.

**Selection options.** The command must accept `-a` with the case-insensitive enum names `public`, `protected`, `package_protected`, or `private`; the help text must describe the package-level choice as `package`. The command must accept `-m`/`--only-modified`; `-b`/`--only-incompatible`; `-i`/`--include`; `-e`/`--exclude`; `--include-exclusively`; `--exclude-exclusively`; `--include-synthetic`; `--no-annotations`; `--ignore-missing-classes`; and `--ignore-missing-classes-by-regex`. IF `-a` receives any other value or a filter has invalid syntax, then the command must exit with status `1`.

**Classpath options.** WHERE dependencies differ between versions, the command must accept both `--old-classpath` and `--new-classpath`; WHERE neither is supplied, it must use one common runtime classpath. IF exactly one of the two classpath options is supplied, then the command must exit with status `1`.

**Projection options.** The command must accept `-s`/`--semantic-versioning`, `--markdown`, `-x`/`--xml-file`, `--html-file`, `--html-stylesheet`, `--report-only-filename`, and `--report-only-summary`. WHEN semantic-versioning mode is selected, standard output must contain only the semantic recommendation plus line termination. WHEN Markdown mode is selected, standard output must contain Markdown instead of plain text. WHERE XML or HTML paths are supplied, those files must be written in addition to the standard output projection. IF a stylesheet is supplied without an HTML output path or does not exist, then the command must exit with status `1`.

**Error policies.** The command must accept `--error-on-binary-incompatibility`, `--error-on-source-incompatibility`, `--error-on-modifications`, `--no-error-on-exclusion-incompatibility`, `--error-on-semantic-incompatibility`, `--ignore-missing-old-version`, and `--ignore-missing-new-version`. WHEN an enabled error policy detects its corresponding retained condition, the command must exit with status `1`; WHEN no enabled error policy is violated, it must exit successfully even if the report contains ordinary compatible changes.

## Maven Build Surface

The project build supplies the library artifact and executable JAR used by programmatic and command-line workflows.

**Project metadata.** The root `pom.xml` must define Maven coordinates `com.github.siom79.japicmp:japicmp` and package Java sources under `src/main/java`. The build must compile against Java 8 language and bytecode compatibility or a newer toolchain configured to emit Java 8-compatible classes.

**Dependencies.** The build must declare Javassist and Guava for archive analysis and filtering, plus the Jakarta XML Bind API and a JAXB runtime for XML projection. IF Maven builds without network access, then dependency declarations must resolve exclusively from the provided local Maven repository.

**Artifacts.** WHEN `mvn package` succeeds, it must produce a normal library JAR and a dependency-inclusive executable JAR whose manifest main class is `japicmp.JApiCmp`. The executable JAR filename must carry the `jar-with-dependencies` classifier so the documented `java -jar` workflow remains available.

## State Model

The core state is an ordered change graph derived from an old archive set, a new archive set, and comparison options. Its public projections are the library's `List<JApiClass>`, compatibility booleans and named findings on graph nodes, semantic-version strings, plain text, XML, HTML, Markdown, and the command's exit outcome.

The graph must preserve old and new values on each paired element while keeping selection filters separate from output-only filtering. Comparison filters determine which bytecode elements enter the graph; output-only flags determine which existing graph nodes appear in a report.

## Error Semantics

| Condition | Required result |
|---|---|
| Archive value has neither file nor bytes | IF a library archive has neither file bytes nor in-memory bytes, THEN comparison must raise `JApiCmpException` with reason `IllegalArgument`. |
| Archive read or report write fails | IF a local archive cannot be opened or a report file cannot be written, THEN the operation must raise `JApiCmpException` with reason `IoException`. |
| Referenced class is unresolved | IF a required referenced class cannot be resolved and is not ignored, THEN comparison must raise `JApiCmpException` with reason `ClassLoading`. |
| Filter or command syntax is invalid | IF a filter string or command option has invalid syntax or a required command argument is missing, THEN parsing must raise `JApiCmpException` with reason `CliError`. |
| XML binding fails | IF XML binding fails, THEN XML generation must raise `JApiCmpException` with reason `JaxbException`. |
| Enabled error policy is violated | IF an enabled incompatibility policy finds a prohibited change, THEN generation must raise `JApiCmpException` with reason `IncompatibleChange`, which the command maps to exit status `1`. |
| Help is requested | IF `--help` is requested, THEN the command must print help and terminate successfully without reporting an error. |

## Cross-View Invariants

1. A class retained by `JarArchiveComparator.compare()` must have the same fully qualified name and `JApiChangeStatus` in the model graph, plain text, XML root, HTML class entry, and Markdown class entry.
2. A compatibility finding attached to a class or member must drive the same binary/source booleans, semantic-version level, plain-text incompatibility marker, and named XML/HTML/Markdown finding.
3. A class or member excluded by comparison filters must be absent from the model graph and every report projection, while a node hidden only by output filtering must remain present in the original comparison graph.
4. The `SemverOut` recommendation must equal the highest semantic-version level among retained public or protected findings and must equal the semantic-version metadata supplied to XML, HTML, and Markdown reports.
5. A `JApiClass` marked binary incompatible because of a retained descendant must appear binary incompatible in every generated report even when the class node has no direct class-level compatibility change.
6. Changing the access threshold must change model membership and all report projections consistently, with `PUBLIC` narrower than `PROTECTED`, `PROTECTED` narrower than `PACKAGE_PROTECTED`, and `PACKAGE_PROTECTED` narrower than `PRIVATE`.
7. Enabling synthetic-element inclusion or annotation suppression must change both the model graph and every report generated from that graph consistently.
8. An archive version preserved by `JApiCmpArchive` must agree with `Version`, archive descriptions, semantic-policy checks, and report metadata wherever that projection is present.
9. `reportOnlyFilename` must change archive path presentation in plain text, XML, HTML, and Markdown without changing comparison membership, statuses, or compatibility results.
10. Error policies must inspect the same retained graph that report generators describe, so a successful exit must not coexist with a prohibited retained condition under an enabled policy.

## Public Interface

### Import Surface

```java
import japicmp.JApiCmp;
import japicmp.cmp.JApiCmpArchive;
import japicmp.cmp.JarArchiveComparator;
import japicmp.cmp.JarArchiveComparatorOptions;
import japicmp.config.IgnoreMissingClasses;
import japicmp.config.Options;
import japicmp.exception.JApiCmpException;
import japicmp.filter.AnnotationBehaviorFilter;
import japicmp.filter.AnnotationClassFilter;
import japicmp.filter.AnnotationFieldFilter;
import japicmp.filter.BehaviorFilter;
import japicmp.filter.ClassFilter;
import japicmp.filter.FieldFilter;
import japicmp.filter.Filter;
import japicmp.filter.Filters;
import japicmp.filter.JavaDocLikeClassFilter;
import japicmp.filter.JavadocLikeBehaviorFilter;
import japicmp.filter.JavadocLikeFieldFilter;
import japicmp.filter.JavadocLikePackageFilter;
import japicmp.model.AccessModifier;
import japicmp.model.AbstractModifier;
import japicmp.model.BridgeModifier;
import japicmp.model.FinalModifier;
import japicmp.model.JApiAnnotation;
import japicmp.model.JApiAnnotationElement;
import japicmp.model.JApiAnnotationElementValue;
import japicmp.model.JApiAttribute;
import japicmp.model.JApiBehavior;
import japicmp.model.JApiChangeStatus;
import japicmp.model.JApiClass;
import japicmp.model.JApiClassFileFormatVersion;
import japicmp.model.JApiClassType;
import japicmp.model.JApiCompatibility;
import japicmp.model.JApiCompatibilityChange;
import japicmp.model.JApiCompatibilityChangeType;
import japicmp.model.JApiConstructor;
import japicmp.model.JApiException;
import japicmp.model.JApiField;
import japicmp.model.JApiGenericTemplate;
import japicmp.model.JApiGenericType;
import japicmp.model.JApiHasAbstractModifier;
import japicmp.model.JApiHasAccessModifier;
import japicmp.model.JApiHasAnnotations;
import japicmp.model.JApiHasBridgeModifier;
import japicmp.model.JApiHasChangeStatus;
import japicmp.model.JApiHasFinalModifier;
import japicmp.model.JApiHasGenericTemplates;
import japicmp.model.JApiHasGenericTypes;
import japicmp.model.JApiHasLineNumber;
import japicmp.model.JApiHasModifiers;
import japicmp.model.JApiHasStaticModifier;
import japicmp.model.JApiHasSyntheticAttribute;
import japicmp.model.JApiHasSyntheticModifier;
import japicmp.model.JApiHasTransientModifier;
import japicmp.model.JApiHasVolatileModifier;
import japicmp.model.JApiImplementedInterface;
import japicmp.model.JApiJavaObjectSerializationCompatibility;
import japicmp.model.JApiMethod;
import japicmp.model.JApiModifier;
import japicmp.model.JApiParameter;
import japicmp.model.JApiReturnType;
import japicmp.model.JApiSemanticVersionLevel;
import japicmp.model.JApiSerialVersionUid;
import japicmp.model.JApiSuperclass;
import japicmp.model.JApiType;
import japicmp.model.StaticModifier;
import japicmp.model.SyntheticAttribute;
import japicmp.model.SyntheticModifier;
import japicmp.model.TransientModifier;
import japicmp.model.VarargsModifier;
import japicmp.model.VolatileModifier;
import japicmp.output.html.HtmlOutput;
import japicmp.output.html.HtmlOutputGenerator;
import japicmp.output.html.HtmlOutputGeneratorOptions;
import japicmp.output.markdown.MarkdownOutputGenerator;
import japicmp.output.markdown.config.MarkdownOptions;
import japicmp.output.semver.SemverOut;
import japicmp.output.stdout.StdoutOutputGenerator;
import japicmp.output.xml.XmlOutput;
import japicmp.output.xml.XmlOutputGenerator;
import japicmp.output.xml.XmlOutputGeneratorOptions;
import japicmp.output.xml.model.JApiCmpXmlRoot;
import japicmp.versioning.SemanticVersion;
import japicmp.versioning.Version;
import japicmp.versioning.VersionChange;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `JApiCmp` | class | Executable JAR main entry point |
| `JApiCmpArchive` | class | File-backed or byte-backed archive value with version metadata |
| `JarArchiveComparator` | class | Compares old and new archive sets into a change graph |
| `JarArchiveComparatorOptions` | class | Configures comparison access, filters, classpaths, annotations, and synthetic elements |
| `JarArchiveComparatorOptions.OverrideCompatibilityChange` | class | Overrides one compatibility type's public projections |
| `JarArchiveComparatorOptions.ClassPathMode` | enum | Selects shared or separate dependency classpaths |
| `Options` | class | Holds command and report options |
| `IgnoreMissingClasses` | class | Holds all-class and regular-expression missing-class policies |
| `JApiCmpException` | exception | Reports categorized comparison, parsing, and output failures |
| `JApiCmpException.Reason` | enum | Names public failure categories |
| `Filter` | interface | Marker for comparison filters |
| `ClassFilter` | interface | Matches bytecode classes |
| `BehaviorFilter` | interface | Matches methods and constructors |
| `FieldFilter` | interface | Matches fields |
| `Filters` | class | Applies include and exclude collections by element kind |
| `JavaDocLikeClassFilter` | class | Matches class-name wildcard expressions |
| `JavadocLikePackageFilter` | class | Matches package wildcard expressions |
| `JavadocLikeBehaviorFilter` | class | Matches Javadoc-style method and constructor expressions |
| `JavadocLikeFieldFilter` | class | Matches Javadoc-style field expressions |
| `AnnotationClassFilter` | class | Matches classes by annotation |
| `AnnotationBehaviorFilter` | class | Matches behaviors by annotation |
| `AnnotationFieldFilter` | class | Matches fields by annotation |
| `JApiClass` | class | Root class node in the public change graph |
| `JApiBehavior` | abstract class | Shared constructor and method change node |
| `JApiConstructor` | class | Constructor change node |
| `JApiMethod` | class | Method change node |
| `JApiField` | class | Field change node |
| `JApiSuperclass` | class | Superclass change node |
| `JApiImplementedInterface` | class | Implemented-interface change node |
| `JApiAnnotation` | class | Annotation change node |
| `JApiAnnotationElement` | class | Annotation element change node |
| `JApiAnnotationElementValue` | class | Structured annotation value projection |
| `JApiGenericTemplate` | class | Generic declaration change node |
| `JApiGenericType` | class | Nested generic type and wildcard projection |
| `JApiParameter` | class | Behavior parameter projection |
| `JApiReturnType` | class | Method return-type change projection |
| `JApiType` | class | Old/new field-type projection |
| `JApiModifier` | class | Old/new modifier projection |
| `JApiAttribute` | class | Old/new class-file attribute projection |
| `JApiClassType` | class | Old/new class-kind projection |
| `JApiClassFileFormatVersion` | class | Old/new class-file version projection |
| `JApiSerialVersionUid` | class | Explicit and computed serialization UID projection |
| `JApiCompatibility` | interface | Common compatibility contract for graph nodes |
| `JApiCompatibilityChange` | class | One named compatibility finding |
| `JApiCompatibilityChangeType` | enum | Public vocabulary of compatibility rules |
| `JApiChangeStatus` | enum | Structural status vocabulary |
| `JApiSemanticVersionLevel` | enum | Graph finding severity vocabulary |
| `JApiJavaObjectSerializationCompatibility` | interface | Serialization compatibility projection |
| `AccessModifier` | enum | Access threshold and modifier vocabulary |
| `AbstractModifier` | enum | Abstract and non-abstract modifier vocabulary |
| `BridgeModifier` | enum | Bridge and non-bridge modifier vocabulary |
| `FinalModifier` | enum | Final and non-final modifier vocabulary |
| `StaticModifier` | enum | Static and non-static modifier vocabulary |
| `SyntheticModifier` | enum | Synthetic and non-synthetic modifier vocabulary |
| `SyntheticAttribute` | enum | Synthetic class-file attribute vocabulary |
| `TransientModifier` | enum | Transient and non-transient modifier vocabulary |
| `VarargsModifier` | enum | Variable-arity and fixed-arity modifier vocabulary |
| `VolatileModifier` | enum | Volatile and non-volatile modifier vocabulary |
| `JApiHasChangeStatus` | interface | Common structural-status projection |
| `JApiHasModifiers` | interface | Common ordered modifier projection |
| `JApiHasAccessModifier` | interface | Common access-modifier projection |
| `JApiHasAbstractModifier` | interface | Common abstract-modifier projection |
| `JApiHasBridgeModifier` | interface | Common bridge-modifier projection |
| `JApiHasFinalModifier` | interface | Common final-modifier projection |
| `JApiHasStaticModifier` | interface | Common static-modifier projection |
| `JApiHasSyntheticAttribute` | interface | Common synthetic-attribute projection |
| `JApiHasSyntheticModifier` | interface | Common synthetic-modifier projection |
| `JApiHasTransientModifier` | interface | Common transient-modifier projection |
| `JApiHasVolatileModifier` | interface | Common volatile-modifier projection |
| `JApiHasAnnotations` | interface | Common annotation and compatibility projection |
| `JApiHasGenericTemplates` | interface | Common generic-template and compatibility projection |
| `JApiHasGenericTypes` | interface | Common old/new generic-type projection |
| `JApiHasLineNumber` | interface | Common old/new source line projection |
| `Version` | class | Original and parsed archive-version value |
| `SemanticVersion` | class | Numeric semantic-version value and change type |
| `VersionChange` | class | Aggregates archive-set version changes |
| `SemverOut` | class | Reduces graph findings to a version increment string |
| `StdoutOutputGenerator` | class | Renders the plain-text diff |
| `HtmlOutputGenerator` | class | Renders an HTML report |
| `HtmlOutputGeneratorOptions` | class | Configures HTML title and semantic metadata |
| `HtmlOutput` | class | Holds generated HTML text |
| `XmlOutputGenerator` | class | Builds and writes XML and schema projections |
| `XmlOutputGeneratorOptions` | class | Configures XML title, schema, and semantic metadata |
| `XmlOutput` | class | Holds generated XML bytes and root model |
| `JApiCmpXmlRoot` | class | Public XML report root model |
| `MarkdownOutputGenerator` | class | Renders a Markdown report |
| `MarkdownOptions` | class | Configures Markdown version labels and report projections |

### Public Member Index

This index names the public members used by the documented surface; parameter and return contracts remain in the behavior sections.

| Type | Public members |
|---|---|
| `JApiCmp` | `main` |
| `JApiCmpArchive` | constructors, `getFile`, `getVersion`, `getBytes`, `getName` |
| `JarArchiveComparator` | constructor, `compare`, `getCommonClasspathAsString`, `getOldClassPathAsString`, `getNewClassPathAsString`, `getJarArchiveComparatorOptions` |
| `JarArchiveComparatorOptions` | `of`, `getFilters`, `getClassPathEntries`, `setAccessModifier`, `getAccessModifier`, `setIncludeSynthetic`, `isIncludeSynthetic`, `setClassPathMode`, `getClassPathMode`, `setOldClassPath`, `getOldClassPath`, `setNewClassPath`, `getNewClassPath`, `setNoAnnotations`, `isNoAnnotations`, `getIgnoreMissingClasses`, `isIncludeClassFileFormatVersion`, `addOverrideCompatibilityChange`, `getOverrideCompatibilityChanges` |
| `OverrideCompatibilityChange` | constructor, `getCompatibilityChange`, `isBinaryCompatible`, `isSourceCompatible`, `getSemanticVersionLevel` |
| `Options` | `newDefault`, `verify`, archive getters/setters, report-option getters/setters, filter getters/builders, classpath getters/setters, missing-class getters/setters, error-policy getters/setters, `getDifferenceDescription`, `joinOldArchives`, `joinNewArchives`, `joinOldVersions`, `joinNewVersions` |
| `IgnoreMissingClasses` | `isIgnoreAllMissingClasses`, `getIgnoreMissingClassRegularExpression`, `setIgnoreAllMissingClasses`, `setIgnoreMissingClassRegularExpression`, `ignoreClass` |
| `JApiCmpException` | constructors, `getReason`, `cliError`, `of`, `forClassLoading` |
| `JApiCmpException.Reason` | `CliError`, `NormalTermination`, `IoException`, `JaxbException`, `ClassLoading`, `IllegalState`, `IllegalArgument`, `XsltError`, `IncompatibleChange`, `ResourceNotFound` |
| `Filters` | `getIncludes`, `getExcludes`, `includeClass`, `includeBehavior`, `includeField` |
| `ClassFilter`, `BehaviorFilter`, `FieldFilter` | `matches` |
| Javadoc-like and annotation filters | constructors, `matches` |
| `JApiClass` | `getJavaObjectSerializationCompatible`, `getJavaObjectSerializationCompatibleAsString`, `getSerialVersionUid`, `getChangeStatus`, `getFullyQualifiedName`, `getNewClass`, `getOldClass`, `getModifiers`, `getSuperclass`, `getInterfaces`, `getConstructors`, `getMethods`, `getFields`, `getClassType`, modifier getters, `getAttributes`, `isOldClassExtendable`, `isNewClassExtendable`, `isBinaryCompatible`, `isSourceCompatible`, `getAnnotations`, `isChangeCausedByClassElement`, `getCompatibilityChanges`, `getClassFileFormatVersion`, `getGenericTemplates` |
| `JApiBehavior` | `getName`, `getChangeStatus`, `getParameters`, modifier getters, `getAttributes`, `isBinaryCompatible`, `isSourceCompatible`, `getCompatibilityChanges`, `getAnnotations`, old/new line getters, `getExceptions`, `getGenericTemplates` |
| `JApiMethod` | inherited behavior members, `getNewMethod`, `getOldMethod`, `getReturnType`, `hasSameReturnType`, `hasSameSignature` |
| `JApiConstructor` | inherited behavior members, `getNewConstructor`, `getOldConstructor` |
| `JApiField` | `getChangeStatus`, `getName`, old/new field getters, `getModifiers`, individual modifier getters, `getAttributes`, `getType`, compatibility getters, `getAnnotations`, `getOldGenericTypes`, `getNewGenericTypes` |
| `JApiSuperclass` | old/new superclass getters, `getChangeStatus`, `isBinaryCompatible`, `isSourceCompatible`, `getCompatibilityChanges`, corresponding/owning class getters |
| `JApiImplementedInterface` | `getFullyQualifiedName`, `getChangeStatus`, `isBinaryCompatible`, `isSourceCompatible`, `getCompatibilityChanges`, `getCorrespondingJApiClass` |
| `JApiAnnotation` | `getChangeStatus`, `getFullyQualifiedName`, old/new annotation getters, `getElements`, compatibility getters, `getCorrespondingJApiClass` |
| `JApiAnnotationElement` | `getName`, old/new value getters, old/new element-value getters, `getChangeStatus`, compatibility getters |
| `JApiAnnotationElementValue` | `getType`, `getName`, `getValue`, `getValueString`, `getFullyQualifiedName`, `getValues` |
| `JApiGenericTemplate` | `getChangeStatus`, `getName`, old/new type getters, old/new generic-type getters, old/new interface-type getters, compatibility getters |
| `JApiGenericType` | `getType`, `getGenericWildCard`, `getGenericTypes` |
| `JApiParameter` | `getChangeStatus`, `getType`, template-name getters, old/new generic-type getters, compatibility getters |
| `JApiReturnType` | `getChangeStatus`, old/new return-type getters, old/new generic-type getters, compatibility getters |
| `JApiType` | old/new type optional getters, `getChangeStatus`, `getOldValue`, `getNewValue`, `hasChanged` |
| `JApiModifier` | old/new modifier getters, `getChangeStatus`, `getValueOld`, `getValueNew`, change predicates |
| `JApiAttribute` | old/new attribute getters, `getChangeStatus`, old/new value strings |
| `JApiClassType` | old/new type getters and optionals, `getChangeStatus` |
| `JApiClassFileFormatVersion` | old/new major/minor getters, `getChangeStatus`, compatibility getters |
| `JApiSerialVersionUid` | old/new serializable flags, explicit/default UID getters and string getters |
| `JApiCompatibility` | `isBinaryCompatible`, `isSourceCompatible`, `getCompatibilityChanges` |
| `JApiCompatibilityChange` | constructor, `getType`, `isBinaryCompatible`, `isSourceCompatible`, binary/source setters, `getSemanticVersionLevel` |
| `JApiCompatibilityChangeType` | enum constants listed under Default compatibility families, compatibility getters/setters, `resetOverrides` |
| Modifier and status enums | constants listed under Structural status and Modifier vocabulary; level, conversion, and incompatibility predicates described above |
| `Version` | constructor, instance and static `getSemanticVersion`, `getStringVersion` |
| `SemanticVersion` | constructor, `getMajor`, `getMinor`, `getPatch`, `computeChangeType` |
| `SemanticVersion.ChangeType` | `MAJOR`, `MINOR`, `PATCH`, `UNCHANGED`, `getRank` |
| `VersionChange` | constructor, `computeChangeType`, `isAllMajorVersionsZero` |
| `SemverOut` | constructors, `SEMVER_MAJOR`, `SEMVER_MINOR`, `SEMVER_PATCH`, `SEMVER_COMPATIBLE`, `generate` |
| `StdoutOutputGenerator` | constructor, `generate` |
| `HtmlOutputGenerator` | constructor, `generate` |
| `HtmlOutputGeneratorOptions` | `getTitle`, `setTitle`, `getSemanticVersioningInformation`, `setSemanticVersioningInformation` |
| `HtmlOutput` | constructor, `getHtml` |
| `XmlOutputGenerator` | constructors, `generate`, `writeToFiles` |
| `XmlOutputGeneratorOptions` | `isCreateSchemaFile`, `setCreateSchemaFile`, title and semantic-information getters/setters |
| `XmlOutput` | XML stream and root getters/setters, `close` |
| `JApiCmpXmlRoot` | classes, archive, version, timestamp, access, output flag, filter, missing-class, title, and semantic-information getters/setters |
| `MarkdownOutputGenerator` | constructors, `generate` |
| `MarkdownOptions` | `newDefault`, target-version setters, `options`, `targetOldVersion`, `targetNewVersion`, `title`, `header`, `sort`, `message` |

### CLI Entry Points

The executable entry point is `japicmp.JApiCmp`, invoked through the dependency-inclusive JAR with `java -jar`. It has no subcommands.

| Exit | Meaning |
|---:|---|
| `0` | Help was printed, or comparison and all enabled error policies completed successfully |
| `1` | Parsing, validation, class loading, comparison, report writing, or an enabled incompatibility policy failed |

## Appendix A: Environment

The working environment runs a Java toolchain and Maven on Linux without network access. The local Maven repository provides Javassist, Guava, Jakarta XML Bind API, JAXB runtime, JUnit Jupiter, Hamcrest, Mockito, and jsoup. The assessment environment provides the same toolchain and dependency set.

The project must declare Maven metadata in a root `pom.xml`, must use the standard `src/main/java` and `src/test/java` layout, and must resolve all declared dependencies from the provided local Maven repository.

## Appendix B: Assessment Notes

Checks exercise the Maven build, public Java packages and members, local file-backed and byte-backed JAR comparison, model graph structure, compatibility classification, filter precedence and syntax, semantic-version reduction, command-line options and exits, and deterministic semantic content in plain-text, XML, HTML, and Markdown projections. Inputs use local generated class files and JARs; no external service or remote repository is required. Exact timestamps, absolute temporary paths, private fields, private helper types, log wording, exception-message wording, and object representation text are not assessed.
