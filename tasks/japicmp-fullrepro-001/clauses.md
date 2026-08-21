# japicmp v1 Clause Sidecar

Clause IDs are audit-only and do not appear in the candidate-facing specification body. Each quoted clause is verbatim from `wip/japicmp/spec_v1.md` and passed Q1, Q2, and Q3 in `public_api_surface.md`.

## Representative Workflows

- `JCMP-WF-001` — “WHEN both archive objects refer to readable local JARs, the comparison must return a deterministic class graph ordered by fully qualified class name.”
- `JCMP-WF-002` — “IF a referenced superclass or interface is required for compatibility analysis but is missing from the configured classpath, then comparison must raise `JApiCmpException` with reason `ClassLoading` unless the missing class policy ignores it.”
- `JCMP-WF-003` — “WHEN multiple generators receive the same comparison graph and logically equivalent report options, each projection must describe the same retained classes, members, change statuses, compatibility findings, and semantic-version level.”
- `JCMP-WF-004` — “IF output-only filtering removes every graph node, then the plain-text projection must report `No changes.` and the other projections must contain no class-detail entries.”
- `JCMP-WF-005` — “WHEN the required archive paths are valid, the command must write the selected report to standard output and exit successfully.”
- `JCMP-WF-006` — “IF an option is unknown, an option argument is missing, an archive is unreadable, or a required old/new archive is absent, then the command must write a concise error to standard error, print the help hint to standard output, and exit with status `1`.”

## Archive Inputs and Comparison

- `JCMP-ARCH-001` — “A `JApiCmpArchive` must accept either a local `File` plus a version string, or a JAR byte array plus a version string and display name.”
- `JCMP-ARCH-002` — “WHEN constructed from a file, `getFile()` must be present and `getBytes()` must be empty; WHEN constructed from bytes, `getBytes()` and `getName()` must be present and `getFile()` must be empty; in both cases `getVersion()` must preserve the supplied version text through `Version.getStringVersion()`.”
- `JCMP-ARCH-003` — “A `JarArchiveComparator` must accept `JarArchiveComparatorOptions` and expose comparison for either one old/new archive pair or two archive lists.”
- `JCMP-ARCH-004` — “WHEN comparison succeeds, it must return one `JApiClass` for every retained class present in either side, sort the class list case-insensitively by fully qualified name, and sort each class's methods case-insensitively by method name while preserving the comparison order of overloads with equal names.”
- `JCMP-ARCH-005` — “IF an archive contains no file and no bytes, cannot be opened as a JAR, or contains unreadable class bytes, then comparison must raise `JApiCmpException` with reason `IllegalArgument` or `IoException` matching the failure category.”
- `JCMP-ARCH-006` — “A new `JarArchiveComparatorOptions` must default to access level `PROTECTED`, one common classpath, excluded synthetic elements, annotation comparison enabled, and class-file-format reporting disabled.”
- `JCMP-ARCH-007` — “WHERE `ClassPathMode.ONE_COMMON_CLASSPATH` is selected, `getClassPathEntries()` must supply the shared dependency classpath; WHERE `TWO_SEPARATE_CLASSPATHS` is selected, `getOldClassPath()` and `getNewClassPath()` must supply their respective dependency classpaths.”
- `JCMP-ARCH-008` — “WHEN `setIncludeSynthetic(true)` is used, synthetic classes and members must remain eligible for the graph; WHEN `setNoAnnotations(true)` is used, annotation differences must not populate model annotation changes.”
- `JCMP-ARCH-009` — “WHEN `IgnoreMissingClasses.setIgnoreAllMissingClasses(true)` is active, unresolved inherited types must not abort comparison.”
- `JCMP-ARCH-010` — “WHERE regular-expression entries are added through `getIgnoreMissingClassRegularExpression()`, only matching unresolved class names must be ignored.”
- `JCMP-ARCH-011` — “IF an unresolved class matches neither policy, then the comparator must raise `JApiCmpException` with reason `ClassLoading`.”
- `JCMP-ARCH-012` — “WHEN an `OverrideCompatibilityChange` is added, its `compatibilityChange`, `binaryCompatible`, `sourceCompatible`, and `semanticVersionLevel` values must override that change type for the comparator instance's produced graph.”
- `JCMP-ARCH-013` — “WHEN a later comparator is constructed without the override, the default values in `JApiCompatibilityChangeType` must be restored.”

## Change Graph and Compatibility

- `JCMP-MODEL-001` — “Each `JApiClass` must expose `getFullyQualifiedName()`, `getChangeStatus()`, `getClassType()`, `getSuperclass()`, `getInterfaces()`, `getConstructors()`, `getMethods()`, `getFields()`, `getAnnotations()`, `getGenericTemplates()`, `getClassFileFormatVersion()`, `getSerialVersionUid()`, `isBinaryCompatible()`, `isSourceCompatible()`, `getJavaObjectSerializationCompatible()`, and `getCompatibilityChanges()`.”
- `JCMP-MODEL-002` — “Each `JApiBehavior` must expose its name, parameters, exceptions, annotations, generic templates, modifier projections, change status, compatibility booleans, and compatibility changes; `JApiMethod` must additionally expose `getReturnType()`.”
- `JCMP-MODEL-003` — “Each `JApiField` must expose its name, type, generic types, annotations, modifiers, change status, compatibility booleans, and compatibility changes.”
- `JCMP-MODEL-004` — “WHEN an element exists only in the new archive, its `JApiChangeStatus` must be `NEW`; WHEN it exists only in the old archive, its status must be `REMOVED`; WHEN corresponding elements have no modeled difference, its status must be `UNCHANGED`; WHEN both sides exist and at least one modeled property differs, its status must be `MODIFIED`.”
- `JCMP-MODEL-005` — “A class must become `MODIFIED` when a retained constructor, method, field, superclass, interface, annotation, generic template, class type, modifier, or class-file-format value changes.”
- `JCMP-MODEL-006` — “A `JApiModifier`, `JApiType`, `JApiReturnType`, `JApiSuperclass`, `JApiClassType`, `JApiGenericTemplate`, and annotation element must retain old and new projections independently.”
- `JCMP-MODEL-007` — “WHEN one side is absent, its optional getter must be empty and its string projection must use the public not-available value rather than inventing a counterpart.”
- `JCMP-MODEL-008` — “WHEN both values are equal, the nested node's status must be `UNCHANGED`; WHEN both are present and unequal, its status must be `MODIFIED`.”
- `JCMP-MODEL-009` — “Access modifiers must use `PUBLIC`, `PROTECTED`, `PACKAGE_PROTECTED`, and `PRIVATE`; paired modifier projections must use `ABSTRACT`/`NON_ABSTRACT`, `FINAL`/`NON_FINAL`, `STATIC`/`NON_STATIC`, `TRANSIENT`/`NON_TRANSIENT`, `VOLATILE`/`NON_VOLATILE`, `SYNTHETIC`/`NON_SYNTHETIC`, `BRIDGE`/`NON_BRIDGE`, and `VARARGS`/`NON_VARARGS`.”
- `JCMP-MODEL-010` — “WHEN a modifier changes between old and new elements, its `JApiModifier.getChangeStatus()` must be `MODIFIED` and its old/new optional getters must preserve both enum values.”
- `JCMP-MODEL-011` — “Methods and constructors must be paired by declaring class, name, and erased parameter signature, while fields must be paired by declaring class and field name.”
- `JCMP-MODEL-012` — “WHEN a method return type changes without a parameter-signature change, the same `JApiMethod` node must carry a `JApiReturnType` whose status is `MODIFIED`.”
- `JCMP-MODEL-013` — “WHEN generic signature metadata changes without an erased descriptor change, the affected generic projections must change while the erased parameter or return type remains addressable.”
- `JCMP-MODEL-014` — “A node's `getCompatibilityChanges()` must list the applicable `JApiCompatibilityChange` values, and each value must expose its type plus binary, source, and semantic-version projections.”
- `JCMP-MODEL-015` — “A class's `isBinaryCompatible()` and `isSourceCompatible()` must be false when the class or any retained descendant finding is incompatible in the corresponding dimension.”
- `JCMP-MODEL-016` — “WHEN no incompatible finding exists in a dimension, that dimension must remain true even when compatible additions or metadata changes are present.”
- `JCMP-MODEL-017` — “WHEN a change type appears in the table, its `isBinaryCompatible()`, `isSourceCompatible()`, and `getSemanticVersionLevel()` must equal that row until explicitly overridden.”
- `JCMP-MODEL-018` — “IF a requested compatibility type is absent from the enum, then `valueOf` must follow normal Java enum failure behavior.”
- `JCMP-MODEL-019` — “A class implementing the serialization projection must return `NOT_SERIALIZABLE`, `SERIALIZABLE_COMPATIBLE`, or a `SERIALIZABLE_INCOMPATIBLE_*` status that identifies changes to `serialVersionUID`, class type, Serializable/Externalizable participation, serializable fields, class removal, default UID, or superclass.”
- `JCMP-MODEL-020` — “WHEN `JApiJavaObjectSerializationChangeStatus.isIncompatible()` is called, it must return false only for `NOT_SERIALIZABLE` and `SERIALIZABLE_COMPATIBLE` and true for every incompatible status.”

## Inclusion and Exclusion Filters

- `JCMP-FILT-001` — “`Filters.getIncludes()` and `getExcludes()` must return mutable lists of `Filter` objects used by `includeClass`, `includeBehavior`, and `includeField`.”
- `JCMP-FILT-002` — “WHEN a matching exclusion exists for the requested element kind, exclusion must win.”
- `JCMP-FILT-003` — “WHEN at least one include filter exists for an element kind, a matching include must be required; WHEN no include filter exists for that kind, the element must remain included unless excluded.”
- `JCMP-FILT-004` — “A `JavaDocLikeClassFilter` must match a fully qualified class name, treat `*` as a wildcard, and include nested classes of a matched outer class.”
- `JCMP-FILT-005` — “A `JavadocLikePackageFilter` must match the named package plus subpackages by default; WHEN its `exclusive` constructor flag is true, it must match only the named package.”
- `JCMP-FILT-006` — “IF a class has no package, then package matching must use the empty package name.”
- `JCMP-FILT-007` — “A `JavadocLikeBehaviorFilter` must accept `fully.qualified.Class#member(parameter.Type,...)`, treat `*` as a wildcard, and require the declaring class, member name, parameter count, and each erased parameter type to match.”
- `JCMP-FILT-008` — “A `JavadocLikeFieldFilter` must accept `fully.qualified.Class#field`, treat `*` as a wildcard, and require both class and field patterns to match.”
- `JCMP-FILT-009` — “IF a behavior filter omits `#`, a method name, an opening parenthesis, or a closing parenthesis, or places the closing parenthesis before the opening parenthesis, then construction must raise `JApiCmpException` with reason `CliError`; IF a field filter does not split into exactly a class part and field part, then construction must raise the same exception type and reason.”
- `JCMP-FILT-010` — “An annotation filter string must begin with `@` followed by the annotation's fully qualified name.”
- `JCMP-FILT-011` — “WHEN an annotation class filter evaluates a nested class, an annotation on the declaring outer class must count as a match.”
- `JCMP-FILT-012` — “WHEN annotation behavior and field filters evaluate a member, an annotation on the member, its declaring class, or its declaring outer class must count as a match.”
- `JCMP-FILT-013` — “WHEN `Options.addIncludeFromArgument()` or `addExcludeFromArgument()` receives a semicolon-separated string, entries beginning with `@` must create class, behavior, and field annotation filters; entries containing `#` plus `(` must create behavior filters; entries containing `#` without `(` must create field filters; all other entries must create both class and package filters.”
- `JCMP-FILT-014` — “IF any entry has invalid syntax, then the method must raise `JApiCmpException` with reason `CliError`.”

## Semantic Versioning

- `JCMP-SEM-001` — “A `Version` must preserve the original string through `getStringVersion()` and expose `getSemanticVersion()` when the text contains a numeric `major.minor.patch` sequence, with arbitrary text before or after that sequence.”
- `JCMP-SEM-002` — “IF the text contains no such sequence or a numeric component overflows an integer, then `getSemanticVersion()` must return an empty `Optional`.”
- `JCMP-SEM-003` — “A `SemanticVersion` must expose `getMajor()`, `getMinor()`, and `getPatch()`.”
- `JCMP-SEM-004` — “WHEN `computeChangeType(other)` compares two semantic versions, it must return a present optional containing `MAJOR` for any major-component difference, otherwise `MINOR` for any minor-component difference, otherwise `PATCH` for any patch-component difference, and otherwise `UNCHANGED`; comparison direction must not change the selected component.”
- `JCMP-SEM-005` — “A `VersionChange` must compare old and new semantic-version lists pairwise and return the highest ranked `SemanticVersion.ChangeType`; WHEN every value within each side is identical, it must compare the first old value with the first new value.”
- `JCMP-SEM-006` — “IF either list is empty and its respective ignore flag is false, then `computeChangeType()` must raise `JApiCmpException` with reason `IllegalArgument`; WHEN an empty side is ignored, the method must return an empty optional.”
- `JCMP-SEM-009` — “IF both lists are nonempty, are not each internally identical, and have different sizes, then the method must raise `JApiCmpException` with reason `IllegalArgument`.”
- `JCMP-SEM-007` — “A `SemverOut` must inspect all retained class, superclass, interface, constructor, method, field, and annotation findings and return `1.0.0` when any applicable finding has level `MAJOR`, otherwise `0.1.0` when any has level `MINOR`, otherwise `0.0.1` when the nonempty graph has only `PATCH` findings, and `0.0.0` when the retained graph is empty.”
- `JCMP-SEM-008` — “WHERE a finding belongs to a non-public and non-protected element, it must contribute no level above `PATCH`.”

## Report Projections

- `JCMP-RPT-001` — “WHEN `generate()` is called on the plain-text, HTML, XML, or Markdown generator, output-only flags in `Options` must filter the supplied graph before rendering.”
- `JCMP-RPT-002` — “Classes and methods must retain the comparator's deterministic order, and projections that sort member tables must use member names as their stable key.”
- `JCMP-RPT-003` — “WHERE `outputOnlyModifications` is true, unchanged-only nodes must be omitted; WHERE `outputOnlyBinaryIncompatibleModifications` is true, compatible-only nodes must be omitted; WHERE `reportOnlySummary` is true, detailed member sections must be omitted.”
- `JCMP-RPT-004` — “`StdoutOutputGenerator.generate()` must begin with `Options.getDifferenceDescription()`.”
- `JCMP-RPT-005` — “Each rendered node must use `+++` for `NEW`, `---` for `REMOVED`, `***` for `MODIFIED`, and `===` for `UNCHANGED`, followed by `!` for binary incompatibility, `*` for source-only incompatibility, or a space when both dimensions are compatible.”
- `JCMP-RPT-006` — “WHEN the retained graph is empty, the output must contain `No changes.`.”
- `JCMP-RPT-007` — “`HtmlOutputGenerator.generate()` must return an `HtmlOutput` whose `getHtml()` value is a complete HTML document containing the configured title, comparison metadata, class summary, and, unless summary-only mode is active, sections for the retained class details and members.”
- `JCMP-RPT-008` — “WHERE a custom title is set through `HtmlOutputGeneratorOptions.setTitle()`, both the document title and visible title must use it; WHERE semantic-version information is set, report metadata must expose it.”
- `JCMP-RPT-009` — “IF a configured stylesheet path cannot be read, then generation must raise `JApiCmpException` with an I/O-related reason.”
- `JCMP-RPT-010` — “`XmlOutputGenerator.generate()` must return an `XmlOutput` containing both a `JApiCmpXmlRoot` model and, when stream generation succeeds, XML bytes obtainable from `getXmlOutputStream()`.”
- `JCMP-RPT-011` — “The root must expose retained classes, old/new archive descriptions and versions, access level, filters, missing-class settings, output flags, title, and semantic-version information.”
- `JCMP-RPT-012` — “WHERE schema creation is enabled, `writeToFiles()` must write the XML report and companion schema beside the configured XML path.”
- `JCMP-RPT-013` — “IF XML binding or file writing fails, then generation must raise `JApiCmpException` with reason `JaxbException` or `IoException`.”
- `JCMP-RPT-014` — “`MarkdownOutputGenerator.generate()` must return a report with a summary, comparison options, a class table, and detailed sections for retained classes unless summary-only mode is active.”
- `JCMP-RPT-015` — “The default Markdown options must sort classes by fully qualified name and expose configurable title, header, message, and sort projections.”
- `JCMP-RPT-016` — “WHEN old/new target versions are set in `MarkdownOptions`, the summary must use those values as the compared version labels.”
- `JCMP-RPT-017` — “WHEN generators receive equivalent model graphs and options, status markers, class/member identities, compatibility-change names, and semantic-version content must agree across projections.”
- `JCMP-RPT-018` — “Report creation timestamps and absolute archive paths must be treated as metadata; WHERE `reportOnlyFilename` is true, archive descriptions must use filenames rather than absolute paths.”

## Command-Line Behavior

- `JCMP-CLI-001` — “The command must accept `-o`/`--old` and `-n`/`--new`, each containing one or more local JAR paths separated by semicolons.”
- `JCMP-CLI-002` — “WHEN `-h` or `--help` appears, the command must print the synopsis and option descriptions and exit successfully without requiring archive arguments.”
- `JCMP-CLI-003` — “IF either archive option is absent outside help mode, a file does not exist, a file is unreadable, or a file is not a JAR, then the command must exit with status `1`.”
- `JCMP-CLI-004` — “The command must accept `-a` with the case-insensitive enum names `public`, `protected`, `package_protected`, or `private`; the help text must describe the package-level choice as `package`.”
- `JCMP-CLI-015` — “The command must accept `-m`/`--only-modified`; `-b`/`--only-incompatible`; `-i`/`--include`; `-e`/`--exclude`; `--include-exclusively`; `--exclude-exclusively`; `--include-synthetic`; `--no-annotations`; `--ignore-missing-classes`; and `--ignore-missing-classes-by-regex`.”
- `JCMP-CLI-005` — “IF `-a` receives any other value or a filter has invalid syntax, then the command must exit with status `1`.”
- `JCMP-CLI-006` — “WHERE dependencies differ between versions, the command must accept both `--old-classpath` and `--new-classpath`; WHERE neither is supplied, it must use one common runtime classpath.”
- `JCMP-CLI-007` — “IF exactly one of the two classpath options is supplied, then the command must exit with status `1`.”
- `JCMP-CLI-008` — “The command must accept `-s`/`--semantic-versioning`, `--markdown`, `-x`/`--xml-file`, `--html-file`, `--html-stylesheet`, `--report-only-filename`, and `--report-only-summary`.”
- `JCMP-CLI-009` — “WHEN semantic-versioning mode is selected, standard output must contain only the semantic recommendation plus line termination.”
- `JCMP-CLI-010` — “WHEN Markdown mode is selected, standard output must contain Markdown instead of plain text.”
- `JCMP-CLI-011` — “WHERE XML or HTML paths are supplied, those files must be written in addition to the standard output projection.”
- `JCMP-CLI-012` — “IF a stylesheet is supplied without an HTML output path or does not exist, then the command must exit with status `1`.”
- `JCMP-CLI-013` — “The command must accept `--error-on-binary-incompatibility`, `--error-on-source-incompatibility`, `--error-on-modifications`, `--no-error-on-exclusion-incompatibility`, `--error-on-semantic-incompatibility`, `--ignore-missing-old-version`, and `--ignore-missing-new-version`.”
- `JCMP-CLI-014` — “WHEN an enabled error policy detects its corresponding retained condition, the command must exit with status `1`; WHEN no enabled error policy is violated, it must exit successfully even if the report contains ordinary compatible changes.”

## Maven Build Surface

- `JCMP-BUILD-001` — “The root `pom.xml` must define Maven coordinates `com.github.siom79.japicmp:japicmp` and package Java sources under `src/main/java`.”
- `JCMP-BUILD-002` — “The build must compile against Java 8 language and bytecode compatibility or a newer toolchain configured to emit Java 8-compatible classes.”
- `JCMP-BUILD-003` — “The build must declare Javassist and Guava for archive analysis and filtering, plus the Jakarta XML Bind API and a JAXB runtime for XML projection.”
- `JCMP-BUILD-004` — “IF Maven builds without network access, then dependency declarations must resolve exclusively from the provided local Maven repository.”
- `JCMP-BUILD-005` — “WHEN `mvn package` succeeds, it must produce a normal library JAR and a dependency-inclusive executable JAR whose manifest main class is `japicmp.JApiCmp`.”
- `JCMP-BUILD-006` — “The executable JAR filename must carry the `jar-with-dependencies` classifier so the documented `java -jar` workflow remains available.”

## State Model and Error Semantics

- `JCMP-STATE-001` — “The graph must preserve old and new values on each paired element while keeping selection filters separate from output-only filtering.”
- `JCMP-STATE-002` — “Comparison filters determine which bytecode elements enter the graph; output-only flags determine which existing graph nodes appear in a report.”
- `JCMP-ERR-001` — “IF a library archive has neither file bytes nor in-memory bytes, THEN comparison must raise `JApiCmpException` with reason `IllegalArgument`.”
- `JCMP-ERR-002` — “IF a local archive cannot be opened or a report file cannot be written, THEN the operation must raise `JApiCmpException` with reason `IoException`.”
- `JCMP-ERR-003` — “IF a required referenced class cannot be resolved and is not ignored, THEN comparison must raise `JApiCmpException` with reason `ClassLoading`.”
- `JCMP-ERR-004` — “IF a filter string or command option has invalid syntax or a required command argument is missing, THEN parsing must raise `JApiCmpException` with reason `CliError`.”
- `JCMP-ERR-005` — “IF XML binding fails, THEN XML generation must raise `JApiCmpException` with reason `JaxbException`.”
- `JCMP-ERR-006` — “IF an enabled incompatibility policy finds a prohibited change, THEN generation must raise `JApiCmpException` with reason `IncompatibleChange`, which the command maps to exit status `1`.”
- `JCMP-ERR-007` — “IF `--help` is requested, THEN the command must print help and terminate successfully without reporting an error.”

## Cross-View Invariants

- `JCMP-INV-001` — “A class retained by `JarArchiveComparator.compare()` must have the same fully qualified name and `JApiChangeStatus` in the model graph, plain text, XML root, HTML class entry, and Markdown class entry.”
- `JCMP-INV-002` — “A compatibility finding attached to a class or member must drive the same binary/source booleans, semantic-version level, plain-text incompatibility marker, and named XML/HTML/Markdown finding.”
- `JCMP-INV-003` — “A class or member excluded by comparison filters must be absent from the model graph and every report projection, while a node hidden only by output filtering must remain present in the original comparison graph.”
- `JCMP-INV-004` — “The `SemverOut` recommendation must equal the highest semantic-version level among retained public or protected findings and must equal the semantic-version metadata supplied to XML, HTML, and Markdown reports.”
- `JCMP-INV-005` — “A `JApiClass` marked binary incompatible because of a retained descendant must appear binary incompatible in every generated report even when the class node has no direct class-level compatibility change.”
- `JCMP-INV-006` — “Changing the access threshold must change model membership and all report projections consistently, with `PUBLIC` narrower than `PROTECTED`, `PROTECTED` narrower than `PACKAGE_PROTECTED`, and `PACKAGE_PROTECTED` narrower than `PRIVATE`.”
- `JCMP-INV-007` — “Enabling synthetic-element inclusion or annotation suppression must change both the model graph and every report generated from that graph consistently.”
- `JCMP-INV-008` — “An archive version preserved by `JApiCmpArchive` must agree with `Version`, archive descriptions, semantic-policy checks, and report metadata wherever that projection is present.”
- `JCMP-INV-009` — “`reportOnlyFilename` must change archive path presentation in plain text, XML, HTML, and Markdown without changing comparison membership, statuses, or compatibility results.”
- `JCMP-INV-010` — “Error policies must inspect the same retained graph that report generators describe, so a successful exit must not coexist with a prohibited retained condition under an enabled policy.”
