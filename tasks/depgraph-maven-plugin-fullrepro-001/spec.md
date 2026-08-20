# Dependency Graph Maven Plugin Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`depgraph-maven-plugin` is a Maven plugin that projects resolved Maven dependencies and reactor relationships into graph documents. It exposes seven Maven goals, supports per-module, aggregated, group-oriented, arbitrary-artifact, reactor, and example views, and writes DOT, GML, PlantUML, JSON, or text output.

The installable Maven coordinates are `com.github.ferstl:depgraph-maven-plugin`. The plugin prefix is `depgraph`.

## Non-Goals

- This specification does not require a supported programmatic Java graph-building library beyond the public Mojo types listed in Public Interface.
- This specification does not define private renderer, formatter, graph-factory, style-model, or dependency-adapter classes.
- This specification does not require Graphviz, yEd, PlantUML, or a JavaScript visualization library to display generated source documents.
- This specification does not define exact log-message wording, exception-message wording, object representations, or internal collection order beyond ordering stated below.
- This specification does not require compatibility with private style-model fields absent from the documented JSON style workflow.
- This specification does not define artifact repository access beyond Maven's configured repositories and the offline environment described in Appendix A.

## Representative Workflows

### Per-module graph

```xml
<build>
  <plugins>
    <plugin>
      <groupId>com.github.ferstl</groupId>
      <artifactId>depgraph-maven-plugin</artifactId>
      <version>${depgraph.version}</version>
      <configuration>
        <graphFormat>text</graphFormat>
        <showGroupIds>true</showGroupIds>
        <showVersions>true</showVersions>
      </configuration>
    </plugin>
  </plugins>
</build>
```

```text
mvn depgraph:graph
```

This workflow resolves each visited project's dependencies, writes `target/dependency-graph.txt`, and reports the same text graph in Maven output.

### Aggregated filtered graph

```text
mvn depgraph:aggregate \
  -DgraphFormat=json \
  -Dincludes=com.acme:* \
  -Dexcludes=*:legacy-* \
  -DincludeParentProjects=true
```

This workflow writes one graph at the multimodule root. Its nodes and edges represent the union of accepted dependencies after include and exclude filtering.

### Graph for an artifact without a project

```text
mvn com.github.ferstl:depgraph-maven-plugin:${depgraph.version}:for-artifact \
  -Dartifact=org.example:sample:1.2.3 \
  -DgraphFormat=dot
```

This workflow resolves the requested artifact without a project POM and writes `dependency-graph.dot` in the current directory.

## Execution and Output Lifecycle

This section defines how every goal is invoked, skipped, named, written, and optionally rendered.

**Goal execution.**

- The plugin must expose the goal prefix `depgraph` for Maven invocation.
- When `depgraph.skip` is `true`, the selected goal must complete without resolving a graph or writing an output document.
- When `depgraph.skip` is `false`, the selected goal must resolve its public graph view, serialize it in the selected format, and write the resulting UTF-8 document.

**Output location and name.**

- When `outputDirectory` is absent for a project-based goal, the goal must write into the current project's build directory.
- When `outputDirectory` is absent for `for-artifact` outside a Maven project, the goal must write into the current working directory.
- The `outputFileName` parameter must default to `dependency-graph`.
- When `useArtifactIdInFileName` is `true`, the goal must use the current project's artifact ID instead of `outputFileName`.
- When the selected file name does not end with the selected format's extension, the goal must append `.dot`, `.gml`, `.puml`, `.json`, or `.txt` as appropriate.
- If an output directory does not exist, then the goal must create it before writing the graph document.
- If the graph document cannot be written, then the goal must fail the Maven execution.

**Image rendering.**

- Where `graphFormat` is `dot` and `createImage` is `true`, the goal must retain the DOT source and invoke Graphviz `dot` to create an image whose format is selected by `imageFormat` and defaults to `png`.
- Where `dotExecutable` is present, the goal must invoke that executable instead of resolving `dot` from `PATH`.
- Where `dotArguments` is present, the goal must pass its space-separated arguments to Graphviz in addition to the output format, output path, and DOT source path arguments.
- If the configured Graphviz executable is missing, is a directory, is not executable, or returns a nonzero status, then the goal must fail the Maven execution.

## Goal Views

This section defines which Maven state each goal projects and whether the result is per-project or reactor-wide.

**Project dependency goals.**

- When `depgraph:graph` runs in a multimodule build, the goal must write a dependency graph for every Maven project on which Maven executes the goal.
- When `depgraph:by-groupid` runs, the goal must collapse artifacts to group-ID nodes, omit self-references created by that collapse, and retain dependency scope as part of node identity.
- When `depgraph:example` runs, the goal must create a deterministic built-in example dependency graph while honoring the same format, filtering, display, merge, output, and style parameters as `depgraph:graph`.

**Aggregated goals.**

- When `depgraph:aggregate` runs at a multimodule root, the goal must write one graph containing the union of accepted dependencies from projects in reactor build order.
- When `includeParentProjects` is `true` for `aggregate`, the graph must include parent POM projects and parent-to-child module edges.
- When `includeParentProjects` is `false` for `aggregate`, the graph must omit parent-project nodes that exist only to express module containment.
- When `depgraph:aggregate-by-groupid` runs, the goal must aggregate the reactor-wide dependency union into group-ID nodes and omit self-references created by that collapse.
- The group-ID aggregate must include reactor parent relationships as group-level edges.
- The `reduceEdges` parameter must default to `true` for aggregated goals.
- When `reduceEdges` is `true`, an aggregated goal must omit a non-parent edge whose target remains reachable through another dependency path, preferring paths associated with projects earlier in reactor build order.
- When `reduceEdges` is `false`, an aggregated goal must retain those redundant dependency edges.

**Reactor and external-artifact goals.**

- When `depgraph:reactor` runs, the goal must write one graph of Maven reactor project relationships rather than external dependency relationships.
- When `showGroupIds` or `showVersions` is `true` for `reactor`, the reactor nodes must include the corresponding coordinates.
- When `depgraph:for-artifact` runs, the goal must build a dependency graph rooted at the configured external artifact and must not require a Maven project.

## Artifact Selection and Filtering

This section defines the public filters applied to dependency goals before their selected graph view is serialized.

**Scope selection.**

- The `scopes` parameter must accept a list drawn from `compile`, `provided`, `runtime`, `system`, and `test`; when the list is empty, all scopes must be eligible.
- When `scopes` contains known entries, the graph must include dependencies whose effective Maven scope matches any selected entry.
- When `scopes` contains an unknown entry, the goal must ignore that entry and continue with the known entries.
- The `classpathScope` parameter must apply Maven classpath semantics: `compile` selects compile, provided, and system; `provided` selects provided; `runtime` selects compile and runtime; `system` selects system; and `test` selects all dependency scopes.
- When both `scopes` and `classpathScope` are configured, the goal must use `scopes` and ignore `classpathScope`.
- Where deprecated `scope` is present and `classpathScope` is absent, the goal must treat `scope` as `classpathScope`.

**Coordinate patterns.**

- The `includes`, `excludes`, `transitiveIncludes`, `transitiveExcludes`, and `targetIncludes` parameters must accept comma-separated Maven artifact patterns in `groupId:artifactId:type:classifier` order with omitted parts and wildcard matching.
- When `includes` is nonempty, an artifact must enter the graph only when it matches at least one include pattern.
- When an artifact matches `excludes`, the graph must omit it even when it matches `includes`.
- When a transitive artifact does not match `transitiveIncludes` or matches `transitiveExcludes`, the graph must omit that transitive artifact while retaining separately accepted direct dependencies.
- Where `targetIncludes` is present, the graph must retain dependency paths leading to matching target artifacts and omit branches that do not lead to a target.
- When `excludeOptionalDependencies` is `true`, dependency goals must omit optional artifacts.

## Artifact Identity and Display

This section defines how accepted Maven artifacts become graph nodes and how coordinate detail, conflicts, duplicates, and merging alter the view.

**Visible coordinates.**

- When `showGroupIds`, `showVersions`, `showTypes`, or `showClassifiers` is `true`, artifact nodes must expose the selected coordinate component.
- When `showOptional` is `true`, optional artifacts must carry an optional marker; when it is `false`, the marker must be absent without removing the artifact.
- Dependency graphs must expose effective Maven scope information for accepted artifacts.

**Resolution outcomes.**

- When `showDuplicates` is `true` for `graph` or `example`, the graph must include dependencies omitted by Maven as duplicates and distinguish those edges from included edges.
- When `showConflicts` is `true` for `graph` or `example`, the graph must include dependencies omitted by Maven for version conflicts and distinguish those edges from included edges.
- When `showVersions` is combined with duplicate or conflict display, the graph must expose the selected and omitted version information needed to compare resolution outcomes.
- Aggregated goals must represent included dependencies only and must not synthesize duplicate or conflict resolution across module perspectives.

**Node merging.**

- When `mergeTypes` is `true`, nodes that differ only by Maven artifact type must merge and expose the combined type set where the selected format carries type detail.
- When `mergeClassifiers` is `true`, nodes that differ only by classifier must merge and expose the combined classifier set where the selected format carries classifier detail.
- When `mergeScopes` is `true` for an aggregated goal, nodes that differ only by scope must merge and expose the combined scope set where the selected format carries scope detail.
- When a merge parameter is `false`, the corresponding coordinate component must remain part of node identity.

## Format Projections

This section defines the five serializations of the same selected node-and-edge state.

**Format selection.**

- The `graphFormat` parameter must accept `dot`, `gml`, `puml`, `json`, and `text` without case sensitivity and must default to `dot`.
- If `graphFormat` has any other value, then the goal must fail the Maven execution.
- The DOT projection must return a directed Graphviz source document containing one graph node per selected node and one directed edge per selected dependency relationship.
- The GML projection must return a GML document with numeric node references and directed edges that preserve the selected graph relationships.
- The PlantUML projection must return a PlantUML component diagram source whose component aliases and arrows preserve the selected graph relationships.
- The text projection must return a tree-like dependency listing rooted at the selected project or artifact and must mark optional dependencies when optional display is enabled.
- Each text node label must join its enabled coordinate components with colons in this order: group ID, artifact ID, version, slash-joined types, slash-joined classifiers, and effective scope.
- When scope display is enabled and a project root or dependency node has no explicit scope, its text label must use `compile` as the effective scope.
- When `graphFormat` is `text`, the goal must write the `.txt` document and report the same dependency graph through Maven logging.

**JSON data contract.**

- The JSON projection must return an object with `graphName`, `artifacts`, and `dependencies` properties.
- Each JSON `artifacts` entry must contain stable string `id` and numeric `numericId` references plus the enabled coordinate fields among `groupId`, `artifactId`, `version`, `optional`, `classifiers`, `scopes`, and `types`.
- Each JSON `dependencies` entry must contain `from`, `to`, `numericFrom`, `numericTo`, and `resolution`, and must contain an omitted version when conflict-version display requires it.
- When `showAllAttributesForJson` is `true`, JSON dependency goals must enable group ID, version, type, and classifier fields regardless of the corresponding display flags.
- The `showAllAttributesForJson` parameter must not enable `showDuplicates` or `showConflicts`.
- When `showAllAttributesForJson` is `false`, the JSON projection must honor the ordinary display flags.

**Aggregated text traversal.**

- When `repeatTransitiveDependenciesInTextGraph` is `false`, an aggregated text graph must expand a repeated transitive subtree only on its first occurrence.
- When `repeatTransitiveDependenciesInTextGraph` is `true`, an aggregated text graph must expand that subtree at every occurrence.

## DOT Styling

This section defines how DOT-specific style configuration and effective-style reporting alter graph presentation without changing graph membership.

**Style sources.**

- The DOT projection must begin with a built-in default style that distinguishes included, duplicate, conflict, and parent relationships.
- The group-ID goals must apply the built-in group-ID style after the default style.
- The reactor goal must apply the built-in reactor style after the default style.
- Where `customStyleConfiguration` names a filesystem path, the DOT projection must load that JSON document after the built-in styles and use it as an override.
- Where `customStyleConfiguration` begins with `classpath:`, the DOT projection must load the remaining resource name from the plugin classpath and use it as an override.
- The documented style JSON must recognize the top-level object keys `graph`, `default-node`, `default-edge`, `edge-scope-styles`, `edge-resolution-styles`, and `node-styles`.
- The `graph`, `default-node`, and `default-edge` values must be JSON objects containing their respective DOT graph, node, and edge attributes, with node and edge font attributes nested inside font objects.
- The `edge-scope-styles` and `edge-resolution-styles` values must map scope or resolution names to nested edge-style objects.
- The `node-styles` value must map coordinate patterns to nested node-style objects.
- Where multiple style sources define the same effective attribute, the later source must override the earlier value while unrelated defaults remain effective.
- If `customStyleConfiguration` does not exist or cannot be parsed as a supported style document, then the goal must fail the Maven execution.

**Style reporting.**

- When `printStyleConfiguration` is `true` for a DOT graph, the goal must report the effective merged style configuration through Maven logging.
- When `graphFormat` is not `dot`, DOT-specific custom style, style printing, and image-rendering parameters must not alter the serialized graph state.

## Arbitrary Artifact Resolution

This section defines the coordinate forms, defaults, profiles, and validation rules of `depgraph:for-artifact`.

**Coordinate forms.**

- The `artifact` parameter must accept `groupId:artifactId:version`, with optional `packaging` and `classifier` parts in that order.
- Where `artifact` is absent, `groupId`, `artifactId`, and `version` must all be present.
- Where the long coordinate form omits `type`, the `type` parameter must default to `jar`.
- Where the long coordinate form omits `classifier`, the `classifier` parameter must default to the empty classifier.
- Where `profiles` is present, the goal must activate those profile IDs while building the artifact's Maven project model.

**Validation and resolution.**

- If `artifact` and any of `groupId`, `artifactId`, or `version` are both configured, then the goal must fail the Maven execution.
- If `artifact` contains fewer than three coordinate parts, then the goal must fail the Maven execution.
- If `artifact` is absent and any of `groupId`, `artifactId`, or `version` is missing, then the goal must fail the Maven execution.
- If Maven cannot resolve or build the configured artifact, then the goal must fail the Maven execution.

## State Model

The core state is a selected directed graph whose nodes represent Maven artifacts, group IDs, or reactor projects and whose edges represent dependency, parent, or reactor relationships.

The public projections are the goal view, the selected node and edge membership after filtering and merging, the chosen serialization, the output file path, Maven log output for text and reporting modes, and an optional Graphviz image.

- The selected graph state must remain independent of output serialization except for documented format-specific attribute expansion.
- The output path state must derive from the active project, output parameters, and selected format.
- The style state must affect DOT presentation without changing selected graph membership.
- The resolution state must distinguish included, duplicate, conflict, and parent relationships only in goal views that define those outcomes.

## Error Semantics

The following failures are part of the public Maven-execution contract.

| Condition | Required result |
|---|---|
| Unsupported `graphFormat` | If `graphFormat` is unsupported, then the goal must fail the Maven execution. |
| Invalid arbitrary-artifact coordinate combination | If the `for-artifact` coordinate parameters are mixed or incomplete, then the goal must fail the Maven execution. |
| Unresolvable arbitrary artifact | If Maven cannot build the requested artifact model, then the goal must fail the Maven execution. |
| Missing or invalid custom style | If the configured custom style resource is unavailable or invalid, then the goal must fail the Maven execution. |
| Output write failure | If the output document cannot be written, then the goal must fail the Maven execution. |
| Graphviz failure | If requested image rendering cannot execute successfully, then the goal must fail the Maven execution. |
| Unknown entry in `scopes` | If `scopes` contains an unknown entry alongside known entries, then the goal must ignore the unknown entry and continue. |

## Cross-View Invariants

1. The per-project `graph`, `by-groupid`, and example views must apply the same common output, format, filtering, and DOT-style parameters to their respective selected graphs.
2. A dependency accepted by scope and coordinate filters must appear consistently as a node and connected edge in DOT, GML, PlantUML, JSON, and text projections of the same goal state.
3. A dependency removed by `excludes`, transitive filtering, target filtering, or `excludeOptionalDependencies` must be absent from every format projection of the same goal state.
4. Enabling a merge parameter must change node identity consistently across graph membership, displayed coordinate sets, and every selected output format.
5. An aggregated graph with edge reduction enabled must preserve reachability between retained nodes even though redundant edges are absent.
6. Changing `outputFileName`, `outputDirectory`, or `useArtifactIdInFileName` must change only the output path and must not change selected graph membership or serialization content.
7. A custom DOT style must change matching DOT attributes and must not change nodes or dependency relationships visible through non-DOT projections.
8. When `createImage` succeeds, the retained DOT document and rendered image must derive from the same selected graph execution.
9. The `for-artifact` goal must apply the same dependency filtering, display, format, output, and style contracts as `graph` after its external artifact model is built.

## Public Interface

### Import Surface

The artifact exposes the following public Mojo implementation types for its documented goals:

```java
import com.github.ferstl.depgraph.DependencyGraphMojo;
import com.github.ferstl.depgraph.DependencyGraphByGroupIdMojo;
import com.github.ferstl.depgraph.AggregatingDependencyGraphMojo;
import com.github.ferstl.depgraph.AggregatingDependencyGraphByGroupIdMojo;
import com.github.ferstl.depgraph.ForArtifactDependencyGraphMojo;
import com.github.ferstl.depgraph.ReactorGraphMojo;
import com.github.ferstl.depgraph.ExampleDependencyGraphMojo;
```

Direct construction of these types is not a supported invocation protocol; Maven invokes them through the goals below.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `DependencyGraphMojo` | class | Implements the per-project `graph` goal. |
| `DependencyGraphByGroupIdMojo` | class | Implements the per-project `by-groupid` goal. |
| `AggregatingDependencyGraphMojo` | class | Implements the reactor-wide `aggregate` goal. |
| `AggregatingDependencyGraphByGroupIdMojo` | class | Implements the reactor-wide `aggregate-by-groupid` goal. |
| `ForArtifactDependencyGraphMojo` | class | Implements the project-optional `for-artifact` goal. |
| `ReactorGraphMojo` | class | Implements the reactor relationship goal. |
| `ExampleDependencyGraphMojo` | class | Implements the deterministic example goal. |
| `depgraph:graph` | goal | Generates a dependency graph for each executed Maven project. |
| `depgraph:by-groupid` | goal | Generates a per-project dependency graph collapsed by group ID. |
| `depgraph:aggregate` | goal | Generates one dependency union for a multimodule reactor. |
| `depgraph:aggregate-by-groupid` | goal | Generates one group-ID dependency union for a multimodule reactor. |
| `depgraph:for-artifact` | goal | Generates a dependency graph for an arbitrary Maven artifact. |
| `depgraph:reactor` | goal | Generates a graph of Maven reactor project relationships. |
| `depgraph:example` | goal | Generates a built-in example graph for format and style exploration. |

### CLI Entry Points

Maven invokes the plugin by short prefix after plugin-group configuration or by fully qualified coordinates:

```text
mvn depgraph:<goal>
mvn com.github.ferstl:depgraph-maven-plugin:<version>:<goal>
```

| Exit | Meaning |
|---:|---|
| 0 | The goal completed successfully, including an explicitly skipped execution. |
| nonzero | Maven rejected configuration, dependency resolution failed, graph creation failed, output writing failed, or requested Graphviz rendering failed. |

## Appendix A: Environment

The working environment runs Linux with a Java runtime and Maven, without network access during assessment. The task-local Maven repository contains the plugin API, Maven core and resolver libraries, Maven artifact filters, Jackson Databind, Guava, Apache Commons Lang, JUnit, and the Maven plugin tooling required by the supplied project. The assessment environment provides the same runtime and offline artifact set.

The project must declare Maven packaging metadata in `pom.xml` at the project root. The POM must use coordinates `com.github.ferstl:depgraph-maven-plugin`, packaging `maven-plugin`, Java 8-compatible source and target levels, and all runtime dependencies needed by the implementation.

## Appendix B: Assessment Notes

Assessment invokes the public Maven goals against local single-module, multimodule, reactor, and no-project inputs. Checks cover goal registration, file placement, format selection, graph membership, scope and coordinate filtering, aggregation, edge reduction, merge options, optional and resolution views, JSON and text semantics, arbitrary-artifact validation, style overrides, and failure behavior. Assertions focus on observable goal results and cross-format graph meaning rather than private helper classes or exact diagnostic wording.
