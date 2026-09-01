# jpeek Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jpeek` is a static Java bytecode analysis tool that projects compiled classes into structural XML and class-cohesion metric reports. Callers invoke an executable JAR or the public Java facade with an input directory, an output directory, and a metric selection.

The installable Maven coordinates are `org.jpeek:jpeek`. Analysis reads `.class` files, builds one skeleton view of classes and their members, and derives one XML report for every selected metric.

## Non-Goals

- This specification does not require hosted-service deployment, HTTP routes, Sentry integration, or external DynamoDB tables.
- This specification does not define the separately distributed Maven plugin mentioned by the project documentation.
- This specification does not require package-private report builders, XML visitors, index builders, matrix builders, or other internal carrier types.
- This specification does not require the explicitly unfinished Java-only `Lcom4` and `Ccm` calculator implementations.
- This specification does not define exact log text, exception-message text, stack-trace layout, help-text formatting, or object representation strings.
- This specification does not define exact auxiliary HTML, SVG, CSS, XSL, or XSD asset contents.
- This specification does not require source-level recovery of field reads that the Java compiler has inlined for constant variables.

## Representative Workflows

### Analyze compiled classes with default metrics

```text
java -jar jpeek-jar-with-dependencies.jar \
  --sources target/classes \
  --target target/jpeek
```

The invocation analyzes compiled classes under `target/classes`, writes `skeleton.xml`, and writes XML reports for the default metric selection into the fresh `target/jpeek` directory.

### Select metrics and included member categories

```text
java -jar jpeek-jar-with-dependencies.jar \
  --sources build/classes \
  --target build/cohesion \
  --metrics LCOM4,MMAC \
  --include-ctors \
  --include-static-methods \
  --include-private-methods
```

The selected reports derive from a skeleton that retains constructors, static methods, and private methods instead of applying the default exclusions.

### Use the programmatic facade with a guarded target

```java
import java.io.File;
import java.nio.file.Path;
import org.jpeek.App;
import org.jpeek.FileTarget;

Path input = Path.of("target/classes");
Path output = new FileTarget(new File("target/jpeek"), true).toPath();
new App(input, output).analyze();
```

The target guard replaces an existing output path because overwrite is enabled, and the facade writes the analysis projections to the resulting path.

## Input Discovery and Member Selection

This section defines which compiled program elements enter analysis before any metric is calculated.

**Compiled input.** The analysis input must be a filesystem tree containing Java `.class` files. When a `DefaultBase` is constructed with `path`, its `files()` method must recursively enumerate the paths available under that root. If the root cannot be traversed, then `files()` must raise `IOException`.

**Base composition.** A `Base` must return its input paths from `files()`. When `Base.Concat` receives `one` and `two`, its `files()` result must concatenate the left base followed by the right base. If either base raises `IOException`, then the composed call must propagate that failure.

**Class selection.** When a skeleton is built, the analyzer must process compiled classes and must ignore Java interfaces. When no classes are discovered, the skeleton must remain a valid empty analysis document instead of fabricating class entries.

**Member selection.** Constructors, static methods, and private methods must be excluded from metric input by default. When `include-ctors`, `include-static-methods`, or `include-private-methods` is present in programmatic parameters or its corresponding CLI switch is supplied, the analyzer must retain that member category for every selected metric.

**Compiler limitation.** When the Java compiler has inlined a constant variable access, the analyzer must derive metrics from the remaining bytecode and must not invent a field-access operation that is absent from the compiled class.

## Metric Selection and Configuration

This section defines the public metric vocabulary and how callers select report families.

**Metric identifiers.** The `Metrics` enum must expose `LCOM`, `CAMC`, `MMAC`, `LCOM5`, `LCOM4`, `NHD`, `LCOM2`, `LCOM3`, `SCOM`, `OCC`, `PCC`, `TCC`, `LCC`, `CCM`, and `MWE`. For `LCOM`, `CAMC`, `MMAC`, `LCOM5`, `LCOM4`, `LCOM2`, `LCOM3`, `SCOM`, and `OCC`, `isIncludeParams()` must return `true`. For `NHD`, `PCC`, `TCC`, `LCC`, `CCM`, and `MWE`, `isIncludeParams()` must return `false`. For `MMAC`, `getMean()` and `getSigma()` must return `0.5` and `0.1`. For `LCOM5` and `LCOM4`, those methods must return `0.5` and `-0.1`. For every other member, `getMean()` and `getSigma()` must return `null`.

**CLI selection.** The `--metrics` parameter must accept a comma-separated sequence of metric identifiers. When `--metrics` is absent, the executable must select `LCOM5`, `NHD`, `MMAC`, `SCOM`, and `CAMC`. If a metric token contains characters outside uppercase ASCII letters followed by at most one decimal digit, then the invocation must fail with `IllegalArgumentException` before analysis.

**Programmatic selection.** The `App` constructor accepting `args` must treat metric-name keys present in that map as the selected reports. The same constructor must treat the three `include-*` keys as member-selection switches. When the two-path `App` constructor is used, it must select `LCOM`, `LCOM2`, `LCOM3`, `LCOM4`, `LCOM5`, `SCOM`, `NHD`, `MMAC`, `OCC`, `PCC`, `TCC`, `LCC`, `CCM`, and `MWE` and apply the default member exclusions.

## Skeleton and Metric Projections

This section defines the stable XML views produced from one analysis state and their caller-visible meaning.

**Skeleton root and grouping.** A `Skeleton` must accept a `Base`. Its `xml()` method must return a schema-valid `com.jcabi.xml.XML` document rooted at `skeleton`. The root must expose generation date, implementation version, and schema identity. Its `app` child must identify the analyzed base and group discovered classes by Java package. Each class entry must use the class's simple name.

**Class structure.** Every skeleton class projection must describe its fields and methods using bytecode type descriptors. Field entries must expose name, type, final, public, and static properties. Method entries must expose name, descriptor, constructor, abstract, visibility, static, and bridge properties, together with return type, argument types, and observed field-access or method-call operations.

**Report metadata.** A `Header` must return an iterator of directives that supplies the report generation date as an ISO-8601 instant and the package version from `Version.value()`. If the version cannot be read, then `Header.iterator()` must raise `IllegalStateException`. A `Version` must return the package's `org.jpeek.version` resource value from `value()`. If that resource cannot be read, then `Version.value()` must raise `IOException`.

**Metric reports.** For every selected metric, analysis must write a `<METRIC>.xml` report in the target directory. Each metric report must identify the metric, carry class-level values where the metric defines them, retain package and class identity from the skeleton, and expose aggregate range, color, bar, and statistics projections defined by the report schema.

**Report abstraction.** A `Report` must save its projection under the supplied `target` path. When saving succeeds, `save()` must return `true`. If the report cannot be written, then `save()` must raise `IOException`.

## Analysis and Target Lifecycle

This section defines how CLI and Java callers prepare output, execute analysis, and handle target safety.

**Facade execution.** An `App` must accept `source` and `target` paths, with an optional `args` map, and `analyze()` must derive one skeleton followed by all selected metric reports from the same input state. If input reading or output writing fails, then `analyze()` must raise `IOException`.

**Fresh target.** A `FileTarget` must accept a target `File` and an `overwrite` flag. When the target does not exist, `toPath()` must return its path without creating unrelated filesystem entries. When the target exists and overwrite is false, `toPath()` must raise `IllegalStateException` and must preserve the existing path. When the target exists and overwrite is true, `toPath()` must recursively remove the existing file or directory and return the now-available path.

**Input protection.** If CLI source and target paths are equal while `--overwrite` is supplied, then the invocation must raise `IllegalArgumentException` before deleting or analyzing either path.

**Quiet mode.** When `--quiet` is supplied, the executable must suppress its normal console logging and must preserve report generation and failure behavior.

**Help mode.** When `--help` is supplied with otherwise parseable arguments, the executable must print usage information and must return without analyzing classes or writing reports.

## Method Graphs and Connected Components

This section defines the optional public graph view derived from skeleton method relationships.

**Graph vocabulary.** A `Graph` must return its nodes from `nodes()`. A `Node` must return a stable identifier from `name()` and its ingoing and outgoing neighbors from `connections()`. A `Node.Simple` must retain the constructor's `name` and return it from `name()`. Its `connections()` method must expose a mutable connection set whose changes are visible through later calls.

**Skeleton graph.** An `XmlGraph` must accept a `Skeleton`, a package name `pname`, and a class name `cname`. Its `nodes()` projection must represent non-constructor, non-abstract methods. When the skeleton records an intra-graph call, the projection must connect the caller and callee. Repeated `nodes()` calls must return the same computed graph state.

**Method identity.** An `XmlMethodSignature` must accept skeleton class and method elements as `com.jcabi.xml.XML` values. Its `asString()` member must return a textual identity composed from the class identifier, method name, and ordered argument type descriptors. A `QualifiedName` must accept field `owner` and `attr`, convert slash-separated owner segments to dot-separated segments, and append the field name with one dot.

**Components.** A `Disjoint` must accept a `Graph`. Its `value()` method must return a list of sets that partitions the graph nodes into connected components. Every graph node must occur in exactly one returned set. Directly or transitively connected nodes must share a set. Disconnected nodes must occur in different sets. When the graph is empty, `value()` must return an empty list.

## Metric Calculus

This section defines the public transformation boundary between skeleton XML and a metric XML projection.

**Calculus contract.** The public `node()` member of a `Calculus` must accept the metric name as a `String`, `params` as a `Map<String,Object>`, and `skeleton` as a `com.jcabi.xml.XML`, and must return a `com.jcabi.xml.XML` document containing class metric values derived from that skeleton. If the transformation cannot read its resource or data, then `node()` must raise `IOException`.

**XSL transformation.** An `XslCalculus` must resolve the selected metric's bundled stylesheet, apply the supplied parameter map, and transform the supplied skeleton without mutating it. If the requested stylesheet is unavailable, then the call must fail instead of returning an unrelated metric document.

## State Model

The core state is one discovered set of compiled classes, filtered member metadata, and selected metric identifiers. The public projections are the `Base` path view, skeleton XML, per-metric XML reports, target filesystem, method graph, connected-component partition, and CLI result.

- The discovered class state must be shared by the skeleton and every metric report produced by one `App.analyze()` call.
- The member-selection state must be applied before all selected metric calculations.
- The selected metric state must determine which metric report family is written.
- The target state must be resolved before analysis writes any report.
- The graph and calculus projections must derive from skeleton XML without changing the skeleton state.

## Error Semantics

The following failures are part of the public contract.

| Condition | Required result |
|---|---|
| Missing required CLI source or target | If `--sources` or `--target` is missing, then argument parsing must fail before analysis. |
| Malformed metric token | If a metric token violates the documented identifier syntax, then the executable must raise `IllegalArgumentException`. |
| Existing target without overwrite | If the target exists and overwrite is false, then `FileTarget.toPath()` must raise `IllegalStateException` without changing the target. |
| Equal source and target with overwrite | If source and target are equal while overwrite is enabled, then the executable must raise `IllegalArgumentException` before deletion. |
| Unreadable input tree | If the input tree cannot be traversed, then the programmatic input or analysis call must raise `IOException`. |
| Unwritable output | If a report cannot be written, then `Report.save()` or `App.analyze()` must raise `IOException`. |
| Missing metric transformation | If `XslCalculus` cannot resolve the requested metric stylesheet, then `node()` must fail without returning another metric's output. |

## Cross-View Invariants

1. A CLI execution and an `App` execution with equivalent source, target, metric, and member-selection settings must produce equivalent skeleton and metric XML projections.
2. Every class represented in a metric report must correspond to a class in the skeleton produced by the same analysis, with matching package and class identity.
3. A constructor, static method, or private method excluded from the skeleton's metric input must not influence any selected metric report, while enabling its switch must make the same member category available to every selected metric.
4. Every selected metric identifier must correspond to one `Metrics` member and one same-named metric XML report; an unselected metric must not acquire a metric XML report through that selection.
5. Resolving a fresh or overwritten `FileTarget` must affect only target availability and must not alter input discovery or metric selection.
6. Every node returned by an `XmlGraph` must identify a method represented by its source skeleton, and every component returned by `Disjoint` must contain only nodes from that graph.
7. The connected-component sets returned by `Disjoint` must be mutually disjoint and their union must equal the graph's `nodes()` view.
8. Metric XML returned by `Calculus.node()` and metric XML saved for the same metric and skeleton must preserve the same package, class, and class-value projection.

## Public Interface

### Import Surface

The artifact exposes these public Java types:

```java
import org.jpeek.Main;
import org.jpeek.App;
import org.jpeek.Base;
import org.jpeek.DefaultBase;
import org.jpeek.Target;
import org.jpeek.FileTarget;
import org.jpeek.Report;
import org.jpeek.Metrics;
import org.jpeek.Header;
import org.jpeek.Version;
import org.jpeek.skeleton.Skeleton;
import org.jpeek.skeleton.QualifiedName;
import org.jpeek.graph.Graph;
import org.jpeek.graph.Node;
import org.jpeek.graph.Disjoint;
import org.jpeek.graph.XmlGraph;
import org.jpeek.graph.XmlMethodSignature;
import org.jpeek.calculus.Calculus;
import org.jpeek.calculus.xsl.XslCalculus;
```

`Base.Concat` and `Node.Simple` are public nested implementations of their enclosing interfaces.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Main` | class | Provides the executable-JAR entry point. |
| `App` | class | Runs one complete bytecode-to-report analysis. |
| `Base` | interface | Supplies paths belonging to an analysis input. |
| `Base.Concat` | class | Combines two analysis inputs in order. |
| `DefaultBase` | class | Supplies paths from a filesystem tree. |
| `Target` | interface | Resolves an output location. |
| `FileTarget` | class | Resolves a filesystem target with overwrite protection. |
| `Report` | interface | Saves one report projection. |
| `Metrics` | enum | Defines runnable metric identifiers and metric configuration metadata. |
| `Header` | class | Supplies generation date and package version report metadata. |
| `Version` | class | Reads the current package version. |
| `Skeleton` | class | Projects compiled classes into structural XML. |
| `QualifiedName` | class | Produces an unambiguous dot-separated field name. |
| `Graph` | interface | Exposes a list of method graph nodes. |
| `Node` | interface | Exposes one method identity and its neighbors. |
| `Node.Simple` | class | Provides a mutable basic graph node. |
| `Disjoint` | class | Partitions a graph into connected components. |
| `XmlGraph` | class | Derives a method graph from skeleton XML. |
| `XmlMethodSignature` | class | Produces a text identity for a skeleton method. |
| `Calculus` | interface | Transforms skeleton XML into metric XML. |
| `XslCalculus` | class | Performs metric transformations with bundled XSL. |

### CLI Entry Points

The executable assembly uses `org.jpeek.Main` and is invoked as follows:

```text
java -jar <jpeek-jar-with-dependencies.jar> --sources <path> --target <path> [options]
```

| Option | Role |
|---|---|
| `-s`, `--sources` | Required compiled-class input directory. |
| `-t`, `--target` | Required report output directory. |
| `--metrics` | Comma-separated metric selection. |
| `--include-ctors` | Retain constructors for every formula. |
| `--include-static-methods` | Retain static methods for every formula. |
| `--include-private-methods` | Retain private methods for every formula. |
| `--overwrite` | Replace an existing target. |
| `--quiet` | Suppress normal logging. |
| `--help` | Print usage and skip analysis. |

| Exit | Meaning |
|---:|---|
| 0 | Help completed or analysis completed successfully. |
| nonzero | Argument parsing, target safety, input traversal, transformation, or output writing failed. |

## Appendix A: Environment

The working environment runs Java 17 and Maven on Linux without network access. The offline Maven repository provides Cactoos, Takes, Xembly, JCommander, Javassist, ASM, jcabi-xml, jcabi-log, Log4j/SLF4J, Saxon-HE, JUnit, and the remaining transitive artifacts required by the declared build. The assessment environment provides the same runtime and offline artifact set.

The project must declare Maven metadata in `pom.xml` at the project root. The POM must use coordinates `org.jpeek:jpeek`, JAR packaging, a Java 17-compatible build, and all runtime dependencies required by the implementation.

## Appendix B: Assessment Notes

Assessment invokes the executable entry point and public Java interfaces against local compiled-class trees and temporary output paths. Checks cover input discovery, member-category switches, metric selection, target overwrite safety, skeleton structure, metric report identity, graph components, calculus transformation, error behavior, and consistency across CLI, XML, filesystem, graph, and Java API views. Assertions focus on observable public behavior rather than package-private types, exact diagnostics, or presentation markup.


