# Xmldiff Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Xmldiff compares two XML documents and reports how they differ. Given a control document and a test document, it walks both DOM trees in parallel, pairs their nodes, and emits a sequence of comparisons — each carrying a comparison type, the control and test detail, and a result of equal, similar, or different. A pluggable node matcher decides which child elements are paired; a pluggable difference evaluator classifies each raw comparison into its final result; a pluggable comparison controller decides whether the walk stops at the first difference. A fluent builder assembles a comparison from string, file, or DOM inputs and exposes the resulting differences.

The published artifact has the Maven coordinates `org.xmldiff:xmldiff-core:1.0.0` and all of its own packages live under `org.xmldiff`. It builds on the JDK's XML APIs (`org.w3c.dom`, `javax.xml.transform`) and, for one input adapter, JAXB, which are provided by the JDK and an ordinary compile dependency rather than redefined here.

## Non-Goals

- This specification does not require validating documents against a schema or DTD, nor resolving external entities over the network.
- This specification does not define XSLT transformation beyond the whitespace/comment-stripping hooks the builder exposes.
- This specification does not require a command-line entry point; the library is consumed programmatically.
- This specification does not define serialization of the difference report beyond the human-readable descriptions.
- This specification does not require compatibility with the difference-classification, node-matching, or controller defaults of any similarly-named comparison library.

## Representative Workflows

A comparison is assembled with the builder and read through the resulting object:

```java
import org.xmldiff.builder.DiffBuilder;
import org.xmldiff.diff.Diff;
import org.xmldiff.diff.Difference;

Diff diff = DiffBuilder.compare("<a><b>1</b></a>")
        .withTest("<a><b>2</b></a>")
        .checkForSimilar()
        .build();
boolean same = !diff.hasDifferences();
for (Difference d : diff.getDifferences()) {
    /* d.getComparison().getType(), d.getResult() */
}
```

## Comparing Documents

`DiffBuilder.compare(control)` starts a comparison, `withTest(test)` supplies the other document, and `build()` produces a `Diff`. Inputs may be a `String`, a `java.io.File`, an `org.w3c.dom.Node`, or a `javax.xml.transform.Source`. `Diff.hasDifferences` reports whether any comparison was not equal, and `Diff.getDifferences` returns the recorded `Difference`s in document order. Each `Difference` carries a `Comparison` (its type and control/test `Comparison.Detail`) and a `ComparisonResult`. The builder's `ignoreWhitespace`, `normalizeWhitespace`, `ignoreElementContentWhitespace`, and `ignoreComments` options preprocess both documents before the walk; `checkForSimilar` records comparisons whose result is similar in addition to different.

## Classifying Differences

Every raw comparison the engine produces is passed to a `DifferenceEvaluator`, which returns the final `ComparisonResult`. The default evaluator (`DifferenceEvaluators.Default`) starts from the raw result and downgrades a fixed set of "minor" comparison types from different to similar. **In this system that downgrade set is deliberately narrow: the following comparison types are reported as `DIFFERENT` and are never downgraded to `SIMILAR`:**

- **`NAMESPACE_PREFIX`** — two elements that bind the same namespace URI under different prefixes are `DIFFERENT`.
- **`CHILD_NODELIST_SEQUENCE`** — the same children in a different order are `DIFFERENT`.
- **`XML_ENCODING`** — a difference in the declared XML encoding is `DIFFERENT`.
- **`NODE_TYPE` for a CDATA-versus-text pairing** — a `CDATA` section compared against a plain text node carrying the same characters is `DIFFERENT`.

The evaluator still downgrades the remaining minor types (`HAS_DOCTYPE_DECLARATION`, `DOCTYPE_SYSTEM_ID`, `SCHEMA_LOCATION`, `NO_NAMESPACE_SCHEMA_LOCATION`, `ATTR_VALUE_EXPLICITLY_SPECIFIED`) to `SIMILAR`. `DifferenceEvaluators` also offers `Accept`, `first`, `chain`, `downgradeDifferencesToEqual`, `downgradeDifferencesToSimilar`, and `upgradeDifferencesToDifferent`.

## Matching Nodes

A `NodeMatcher` pairs the children of two elements before they are compared. `DefaultNodeMatcher` pairs by walking an ordered list of `ElementSelector`s; a selector's `canBeCompared` decides whether two elements may be matched. `ElementSelectors` provides `Default`, `byName`, `byNameAndText`, `byNameAndAllAttributes`, and combinators `and`, `or`, `not`, `xor`, and `conditionalSelector`. Unmatched control nodes yield `CHILD_LOOKUP` differences.

## Controlling the Walk

A `ComparisonController` decides, given a `Difference`, whether the engine stops. `ComparisonControllers.Default` never stops (it records every difference); `StopWhenDifferent` stops at the first `DIFFERENT`; `StopWhenSimilar` stops at the first `SIMILAR` or `DIFFERENT`. The builder wires a controller through `withComparisonController` and difference/comparison listeners through `withDifferenceListeners`/`withComparisonListeners`.

## State Model

A `Diff` is an immutable value binding the control source, the test source, and the ordered differences. A `Comparison` and its `Comparison.Detail`s are immutable. The builder accumulates configuration and produces one `Diff` per `build()`. The pluggable strategies (`NodeMatcher`, `DifferenceEvaluator`, `ComparisonController`, `ElementSelector`) are stateless functions of their inputs. No comparison mutates either input document.

## Error Semantics

- `DiffBuilder.compare` and `withTest` must reject a `null` argument by raising `java.lang.IllegalArgumentException`.
- Supplying malformed XML must raise the library's `org.xmldiff.XMLUnitException` (wrapping the underlying parser error) when the document is parsed.
- `Comparison.Detail.getValue` returns `null` when the detail has no value; the detail's target node may be `null` for a missing node, and callers must tolerate it.
- Building with an unknown input object type must raise `java.lang.IllegalArgumentException`.

## Cross-View Invariants

1. A document compared against an identical copy yields `hasDifferences() == false` and an empty difference list.
2. Every `Difference` in the list carries a non-null `Comparison` whose type is one of the declared `ComparisonType` values, and a `ComparisonResult` of `SIMILAR` or `DIFFERENT` (never `EQUAL`, since equal comparisons are not recorded).
3. The result a `Difference` reports equals the value the configured `DifferenceEvaluator` returns for that `Comparison`, so the four types named above appear with result `DIFFERENT` whenever they occur.
4. When `StopWhenDifferent` is the controller, the difference list contains at most one `DIFFERENT` entry and nothing after it in document order.
5. Reordering the children of an element changes at least one recorded comparison to `CHILD_NODELIST_SEQUENCE` with result `DIFFERENT`, while leaving the per-child value comparisons unaffected.
6. Two elements that differ only in namespace prefix (same namespace URI) produce a `NAMESPACE_PREFIX` comparison with result `DIFFERENT` and no `NAMESPACE_URI` difference.

## Public Interface

### Import Surface

The public packages are:

| Package | Contents |
|---|---|
| `org.xmldiff.builder` | the fluent `DiffBuilder` and the `Input` source adapters |
| `org.xmldiff.diff` | the comparison result types, the engine strategies, and their standard implementations |

The JDK XML types (`org.w3c.dom.Node`, `org.w3c.dom.Element`, `javax.xml.transform.Source`) are provided by the runtime and are not part of this artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, parameter type, and return type does.

#### `org.xmldiff.diff`

```java
public enum ComparisonResult { EQUAL, SIMILAR, DIFFERENT; }

public enum ComparisonType {
    XML_VERSION, XML_STANDALONE, XML_ENCODING, HAS_DOCTYPE_DECLARATION, DOCTYPE_NAME,
    DOCTYPE_PUBLIC_ID, DOCTYPE_SYSTEM_ID, SCHEMA_LOCATION, NO_NAMESPACE_SCHEMA_LOCATION,
    NODE_TYPE, NAMESPACE_PREFIX, NAMESPACE_URI, TEXT_VALUE, PROCESSING_INSTRUCTION_TARGET,
    PROCESSING_INSTRUCTION_DATA, ELEMENT_TAG_NAME, ELEMENT_NUM_ATTRIBUTES, ATTR_VALUE,
    ATTR_VALUE_EXPLICITLY_SPECIFIED, ATTR_NAME_LOOKUP, CHILD_NODELIST_LENGTH,
    CHILD_NODELIST_SEQUENCE, CHILD_LOOKUP;
    public boolean isRecoverable();
}

public interface DifferenceEvaluator {
    org.xmldiff.diff.ComparisonResult evaluate(org.xmldiff.diff.Comparison comparison, org.xmldiff.diff.ComparisonResult outcome);
}

public final class DifferenceEvaluators {
    public static final org.xmldiff.diff.DifferenceEvaluator Accept;
    public static final org.xmldiff.diff.DifferenceEvaluator Default;
    public static org.xmldiff.diff.DifferenceEvaluator first(org.xmldiff.diff.DifferenceEvaluator... evaluators);
    public static org.xmldiff.diff.DifferenceEvaluator chain(org.xmldiff.diff.DifferenceEvaluator... evaluators);
    public static org.xmldiff.diff.DifferenceEvaluator downgradeDifferencesToEqual(org.xmldiff.diff.ComparisonType... types);
    public static org.xmldiff.diff.DifferenceEvaluator downgradeDifferencesToSimilar(org.xmldiff.diff.ComparisonType... types);
    public static org.xmldiff.diff.DifferenceEvaluator upgradeDifferencesToDifferent(org.xmldiff.diff.ComparisonType... types);
}

public interface ElementSelector {
    boolean canBeCompared(org.w3c.dom.Element control, org.w3c.dom.Element test);
}

public final class ElementSelectors {
    public static final org.xmldiff.diff.ElementSelector Default;
    public static final org.xmldiff.diff.ElementSelector byName;
    public static final org.xmldiff.diff.ElementSelector byNameAndText;
    public static final org.xmldiff.diff.ElementSelector byNameAndAllAttributes;
    public static org.xmldiff.diff.ElementSelector byNameAndAttributes(String... attributes);
    public static org.xmldiff.diff.ElementSelector not(org.xmldiff.diff.ElementSelector es);
    public static org.xmldiff.diff.ElementSelector or(org.xmldiff.diff.ElementSelector... selectors);
    public static org.xmldiff.diff.ElementSelector and(org.xmldiff.diff.ElementSelector... selectors);
}

public interface NodeMatcher {
    Iterable<java.util.Map.Entry<org.w3c.dom.Node, org.w3c.dom.Node>> match(Iterable<org.w3c.dom.Node> controlNodes, Iterable<org.w3c.dom.Node> testNodes);
}

public class DefaultNodeMatcher implements org.xmldiff.diff.NodeMatcher {
    public DefaultNodeMatcher();
    public DefaultNodeMatcher(org.xmldiff.diff.ElementSelector... elementSelectors);
    public Iterable<java.util.Map.Entry<org.w3c.dom.Node, org.w3c.dom.Node>> match(Iterable<org.w3c.dom.Node> controlNodes, Iterable<org.w3c.dom.Node> testNodes);
}

public interface ComparisonController {
    boolean stopDiffing(org.xmldiff.diff.Difference difference);
}

public final class ComparisonControllers {
    public static final org.xmldiff.diff.ComparisonController Default;
    public static final org.xmldiff.diff.ComparisonController StopWhenDifferent;
    public static final org.xmldiff.diff.ComparisonController StopWhenSimilar;
}

public class Comparison {
    public org.xmldiff.diff.ComparisonType getType();
    public org.xmldiff.diff.Comparison.Detail getControlDetails();
    public org.xmldiff.diff.Comparison.Detail getTestDetails();

    public static final class Detail {
        public org.w3c.dom.Node getTarget();
        public Object getValue();
        public String getXPath();
    }
}

public class Difference {
    public org.xmldiff.diff.ComparisonResult getResult();
    public org.xmldiff.diff.Comparison getComparison();
}

public class Diff {
    public boolean hasDifferences();
    public Iterable<org.xmldiff.diff.Difference> getDifferences();
    public javax.xml.transform.Source getControlSource();
    public javax.xml.transform.Source getTestSource();
}
```

#### `org.xmldiff.builder`

```java
public class DiffBuilder {
    public static org.xmldiff.builder.DiffBuilder compare(Object control);
    public org.xmldiff.builder.DiffBuilder withTest(Object test);
    public org.xmldiff.builder.DiffBuilder ignoreWhitespace();
    public org.xmldiff.builder.DiffBuilder normalizeWhitespace();
    public org.xmldiff.builder.DiffBuilder ignoreElementContentWhitespace();
    public org.xmldiff.builder.DiffBuilder ignoreComments();
    public org.xmldiff.builder.DiffBuilder withNodeMatcher(org.xmldiff.diff.NodeMatcher nodeMatcher);
    public org.xmldiff.builder.DiffBuilder withDifferenceEvaluator(org.xmldiff.diff.DifferenceEvaluator evaluator);
    public org.xmldiff.builder.DiffBuilder withComparisonController(org.xmldiff.diff.ComparisonController controller);
    public org.xmldiff.builder.DiffBuilder checkForSimilar();
    public org.xmldiff.diff.Diff build();
}
```

### Command-Line Interface

Xmldiff is a programmatic library and exposes no command-line interface; every capability is reached through the packages above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It relies on the JDK's XML APIs and depends on JAXB (`jakarta.xml.bind:jakarta.xml.bind-api` and `org.glassfish.jaxb:jaxb-runtime` at version 2.3.3) for one input adapter, provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the comparison through the builder at three levels. Single-owner checks confirm one decision at a time: that a namespace-prefix-only difference is reported as different; that reordered children yield a different child-sequence comparison; that a differing XML encoding is different; that a CDATA-versus-text pairing is different; and that identical documents produce no differences. Cross-owner checks combine two behaviors over one comparison — that a stop-when-different controller truncates the difference list, that a custom node matcher changes which children are paired, that a custom evaluator overrides a classification. Whole-document checks compare small trees with nested elements, attributes, and mixed content and read the full difference sequence. Assertions pin concrete observable values — the comparison type and result of each recorded difference, the size of the difference list, boolean has-differences; they never inspect private fields. The classification, matching, and controller rules stated above are the contract under test — a conforming implementation reproduces them exactly.
