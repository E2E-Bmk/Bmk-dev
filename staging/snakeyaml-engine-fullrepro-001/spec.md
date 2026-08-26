# snakeyaml-engine Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`snakeyaml-engine` is a Java library for reading and writing YAML 1.2 documents. It offers two symmetric pipelines over one document model: a load pipeline that turns YAML text into plain Java objects (maps, lists, scalars), and a dump pipeline that turns Java objects into YAML text. A low-level compose entry point exposes the intermediate node graph — tagged scalar, sequence, and mapping nodes — that both pipelines share.

Each pipeline is configured by an immutable settings object built through a builder: `LoadSettings` selects the resolution schema, duplicate-key policy, alias limits, and error labeling; `DumpSettings` selects flow styles, scalar styles, document markers, canonical form, indentation, line width, and non-printable handling. The same input data yields different text projections under different settings while reloading to equal values.

## Non-Goals

- This specification does not define YAML 1.1 behavior (`yes`/`no`/`on`/`off` are not booleans under either schema in scope).
- This specification does not require comment round-tripping or comment-aware parsing.
- This specification does not define the event-level emitter/parser API or custom constructors and representers beyond the stock object mapping.
- This specification does not define resolution of timestamps: date-like scalars remain strings under both schemas in scope.
- This specification does not define thread-safety guarantees for sharing `Load` or `Dump` instances across threads.

## Representative Workflows

The first workflow loads configuration text into Java collections. Mappings load as insertion-ordered maps, sequences as lists, and scalars as the schema-resolved Java types.

```java
import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;

Load load = new Load(LoadSettings.builder().build());
Map<String, Object> config =
    (Map<String, Object>) load.loadFromString("a: 1\nb: text\nc: true\ne: 3.5");
// {a=1, b=text, c=true, e=3.5} — Integer, String, Boolean, Double
```

The second workflow dumps a Java structure under explicit presentation settings. Block style lays every collection out line by line; flow style uses bracketed inline form.

```java
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.common.FlowStyle;

Dump dump = new Dump(DumpSettings.builder().setDefaultFlowStyle(FlowStyle.BLOCK).build());
String text = dump.dumpToString(Map.of("a", 1));   // "a: 1\n"
```

The third workflow composes text into the node graph without constructing Java objects, for callers that need tags, anchors, or node structure.

```java
import org.snakeyaml.engine.v2.api.lowlevel.Compose;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.Node;

Compose compose = new Compose(LoadSettings.builder().build());
Optional<Node> root = compose.composeString("a: [1, two]");
MappingNode mapping = (MappingNode) root.get();     // tag tag:yaml.org,2002:map
```

## Loading YAML Documents

**Entry points.** `new Load(settings)` builds a loader. `loadFromString(text)` loads one document; `loadFromReader(reader)` and `loadFromInputStream(stream)` do the same from IO sources (streams are decoded as UTF-8 by default). `loadAllFromString(text)` returns an iterable over every document in a multi-document stream, in order, parsed lazily.

**Object mapping.** A mapping loads as an insertion-ordered `java.util.Map` (iteration follows document order); a sequence loads as a `java.util.List`; scalars load as the schema-resolved type. Keys are resolved like any scalar, so `1: one` produces an `Integer` key. An empty input loads as null. A document containing one plain scalar loads as that scalar.

**Integer widening.** An integer scalar loads as `Integer` when it fits, as `Long` when it exceeds `Integer` range, and as `BigInteger` beyond `Long` range.

**Anchors and aliases.** An alias resolves to the same object instance as its anchor: after loading `base: &b {x: 1}` and `ref: *b`, the values under `base` and `ref` are reference-identical. The number of aliases for collection nodes is capped by `setMaxAliasesForCollections` (default 50); exceeding the cap must raise `YamlEngineException` with a message naming the configured maximum.

**Duplicate keys.** With default settings, a mapping that repeats a key must raise `DuplicateKeyException`. With `setAllowDuplicateKeys(true)`, the last occurrence wins.

## Schemas and Scalar Resolution

`LoadSettings.builder().setSchema(schema)` selects how plain scalars resolve to Java types. Two schemas are in scope:

**JSON schema (the default).** Only JSON-shaped scalars resolve to non-string types:

| Scalar text | Loads as |
|---|---|
| `null` (exactly) or an empty value | Java null |
| `true`, `false` (exactly) | `Boolean` |
| Optional sign, digits only | `Integer`/`Long`/`BigInteger` |
| JSON-shaped decimals and exponents (`3.5`) | `Double` |
| `~`, `yes`, `no`, `True`, `0x1A`, `2020-01-01`, everything else | `String` |

**Core schema (`new CoreSchema()`).** YAML 1.2 core resolution: additionally resolves `~` and empty values to null, case-variant booleans (`True`), hexadecimal `0x1A` (26) and octal `0o17` (15) integers, exponent floats (`1e3` as 1000.0), and `.inf`/`.nan` floats. `yes`/`no` remain strings, and date-like scalars remain strings.

## Dumping Java Objects

**Entry points.** `new Dump(settings)` builds a dumper. `dumpToString(object)` renders one document. `dumpAllToString(iterator)` renders every object from an iterator into one stream: the first document is unmarked and each subsequent document is introduced by `---`.

**Default projection.** With default settings (`FlowStyle.AUTO`), a top-level mapping or sequence renders in block form and nested collections render in flow form: dumping `{a=1, b=[1, 2]}` yields `a: 1\nb: [1, 2]\n`. Scalars render plain when unambiguous and end with a newline (`hello\n`, `2.5\n`, `null\n` for a null document).

**Quoting of ambiguous strings.** A string whose plain form would resolve as another type must be quoted so the round trip preserves the string type: dumping the string `"true"` yields `'true'`, `"123"` yields `'123'`, a string containing `: ` yields `'a: b'`, and the empty string yields `''`.

**Non-string keys.** Map keys render through the same scalar rules: an `Integer` key 1 renders as `1: `, a `Boolean` key as `true: `.

## Dump Settings and Presentation

All settings are chosen on `DumpSettings.builder()` and frozen by `build()`:

- `setDefaultFlowStyle(FlowStyle)` — `BLOCK` renders every collection line by line (`a: 1\nb:\n- 1\n- 2\n`); `FLOW` renders every collection inline (`{a: 1, b: [1, 2]}\n`); `AUTO` is the mixed default described above.
- `setDefaultScalarStyle(ScalarStyle)` — `PLAIN` (default), `SINGLE_QUOTED` (`'a': 'text'`), `DOUBLE_QUOTED` (`"text"`), `LITERAL` (a multi-line string renders as `|-` followed by indented lines), `FOLDED`.
- `setExplicitStart(true)` / `setExplicitEnd(true)` — emit the `---` document-start and `...` document-end markers: `--- {a: 1}\n...\n`.
- `setCanonical(true)` — canonical form with explicit tags and quoting; dumping `{a=1}` yields exactly `---\n!!map {\n  ? !!str "a"\n  : !!int "1",\n}\n`.
- `setIndent(int)` — block indentation width.
- `setWidth(int)` — best-effort line-length limit; a long plain scalar wraps onto continuation lines indented by two spaces.
- `setMultiLineFlow(true)` — flow collections spread across lines: `k: [\n  1,\n  2\n]\n`.
- `setNonPrintableStyle(NonPrintableStyle)` — `ESCAPE` (default behavior forces a double-quoted scalar with escape sequences: a U+0001 renders as `"hi\x01there"`) or `BINARY` (the string's UTF-8 bytes render as a `!!binary` literal block scalar carrying base64 text).

## Composing Node Graphs

`new Compose(settings)` builds a composer over the same parsing pipeline. `composeString(text)` returns an `Optional<Node>`: empty for empty input, otherwise the root node of the single document is present.

The node model: `MappingNode.getValue()` returns the list of `NodeTuple` entries in document order, each with `getKeyNode()` and `getValueNode()`; `SequenceNode.getValue()` returns child nodes in order; `ScalarNode.getValue()` returns the scalar text and `getScalarStyle()` its presentation style (`ScalarStyle.PLAIN` for plain scalars). Every `Node` reports `getNodeType()` (`NodeType.MAPPING`, `SEQUENCE`, `SCALAR`), `getTag()`, and `getAnchor()` (an `Optional`, present exactly when the node carries an anchor, whose value's text form is the anchor name).

Resolution assigns standard tags during composition: `Tag.STR`, `Tag.INT`, `Tag.FLOAT`, `Tag.BOOL`, `Tag.NULL`, `Tag.MAP`, `Tag.SEQ`, whose text forms are `tag:yaml.org,2002:{str,int,float,bool,null,map,seq}`. In `a: [1, two]`, the key composes as a scalar tagged `str`, the value as a sequence whose children are tagged `int` and `str`.

## Load Settings

`LoadSettings.builder()` configures the load pipeline; `build()` freezes it:

- `setAllowDuplicateKeys(boolean)` — default false; see duplicate-key semantics above.
- `setMaxAliasesForCollections(int)` — alias budget for collection nodes; default 50.
- `setSchema(Schema)` — scalar resolution; see the schema section.
- `setLabel(String)` — a name for the input used in error messages; a parse error on a labeled loader must carry the label in its message.

## State Model

The core state is the document graph: tagged nodes composed from parsed events. Public projections of that one state are: the constructed Java objects (`Load` entry points); the node graph itself (`Compose`); and the presented text (`Dump` under its settings). Settings objects are immutable once built; a `Load`, `Dump`, or `Compose` instance applies its settings uniformly to every call.

- Loading is deterministic: the same text with the same settings loads to equal values, and map iteration order always follows document order.
- Dumping is deterministic: the same value with the same settings renders identical text.
- Style settings change only the text projection, never the data: reloading text dumped under any `FlowStyle` or `ScalarStyle` yields values equal to the original.
- The composed node graph and the loaded objects agree: every scalar node's tag names the Java type the loader would construct.

## Error Semantics

| Condition | Required result |
|---|---|
| Lexically malformed input (reserved indicator such as `@` starting a value) | Must raise `ScannerException`. |
| Syntactically malformed input (unclosed flow collection) | Must raise `ParserException`. |
| Duplicate mapping key under default settings | Must raise `DuplicateKeyException`. |
| Explicit tag naming a type the scalar cannot construct (`!!int notanint`) | Must raise `YamlEngineException`. |
| Alias count for collections exceeding the configured maximum | Must raise `YamlEngineException` with the maximum in the message. |

`ScannerException`, `ParserException`, and `DuplicateKeyException` are `MarkedYamlEngineException`s, which extend `YamlEngineException`; a marked exception exposes `getProblemMark()` as an `Optional<Mark>`, present when the failure has a position, whose `getLine()` is the zero-based line of the problem. A loader built with `setLabel` includes the label text in parse-error messages. Exception messages are otherwise informative only.

## Cross-View Invariants

1. Round trip: for any value graph loaded from text, dumping it and loading the dump must yield a value equal to the original (`loaded.equals(load(dump(loaded)))`), under default settings and under every `FlowStyle`.
2. `Compose` and `Load` agree: for the same input, each scalar node's tag corresponds to the loaded Java type (`Tag.INT` where an `Integer` is loaded, `Tag.STR` where a `String` is loaded), and mapping/sequence node structure mirrors the loaded map/list structure.
3. `dumpAllToString` over a one-element iterator produces the same text as `dumpToString` of that element; over several elements it concatenates the single-document forms with `---` introducing every document after the first.
4. Ambiguous-string quoting is exactly what keeps round trips type-faithful: any string that dumps quoted must reload as a `String` equal to the original.
5. Alias identity survives loading: reference-equal subtrees written as anchor/alias load as reference-equal objects.
6. An error mark's line number must point into the input: for a parse error on line n of the text, `getProblemMark().get().getLine()` returns n (zero-based).

## Public Interface

### Import Surface

```java
import org.snakeyaml.engine.v2.api.Dump;
import org.snakeyaml.engine.v2.api.DumpSettings;
import org.snakeyaml.engine.v2.api.Load;
import org.snakeyaml.engine.v2.api.LoadSettings;
import org.snakeyaml.engine.v2.api.lowlevel.Compose;
import org.snakeyaml.engine.v2.common.FlowStyle;
import org.snakeyaml.engine.v2.common.NonPrintableStyle;
import org.snakeyaml.engine.v2.common.ScalarStyle;
import org.snakeyaml.engine.v2.exceptions.DuplicateKeyException;
import org.snakeyaml.engine.v2.exceptions.Mark;
import org.snakeyaml.engine.v2.exceptions.MarkedYamlEngineException;
import org.snakeyaml.engine.v2.exceptions.ParserException;
import org.snakeyaml.engine.v2.exceptions.ScannerException;
import org.snakeyaml.engine.v2.exceptions.YamlEngineException;
import org.snakeyaml.engine.v2.nodes.MappingNode;
import org.snakeyaml.engine.v2.nodes.Node;
import org.snakeyaml.engine.v2.nodes.NodeTuple;
import org.snakeyaml.engine.v2.nodes.NodeType;
import org.snakeyaml.engine.v2.nodes.ScalarNode;
import org.snakeyaml.engine.v2.nodes.SequenceNode;
import org.snakeyaml.engine.v2.nodes.Tag;
import org.snakeyaml.engine.v2.schema.CoreSchema;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `Load` | constructor `Load(LoadSettings)`; `loadFromString`, `loadAllFromString`, `loadFromReader`, `loadFromInputStream` |
| `LoadSettings` | static `builder()`; builder: `setLabel`, `setAllowDuplicateKeys`, `setMaxAliasesForCollections`, `setSchema`, `build` |
| `Dump` | constructor `Dump(DumpSettings)`; `dumpToString`, `dumpAllToString` |
| `DumpSettings` | static `builder()`; builder: `setDefaultFlowStyle`, `setDefaultScalarStyle`, `setExplicitStart`, `setExplicitEnd`, `setCanonical`, `setIndent`, `setWidth`, `setMultiLineFlow`, `setNonPrintableStyle`, `build` |
| `Compose` | constructor `Compose(LoadSettings)`; `composeString` |
| `Node` | `getTag`, `getNodeType`, `getAnchor` |
| `ScalarNode` | `getValue`, `getTag`, `getScalarStyle` |
| `SequenceNode` | `getValue` |
| `MappingNode` | `getValue` |
| `NodeTuple` | `getKeyNode`, `getValueNode` |
| `NodeType` | enum constants `SCALAR`, `SEQUENCE`, `MAPPING` |
| `Tag` | constants `STR`, `INT`, `FLOAT`, `BOOL`, `NULL`, `MAP`, `SEQ`; `toString` |
| `FlowStyle` | enum constants `BLOCK`, `FLOW`, `AUTO` |
| `ScalarStyle` | enum constants `PLAIN`, `SINGLE_QUOTED`, `DOUBLE_QUOTED`, `LITERAL`, `FOLDED` |
| `NonPrintableStyle` | enum constants `BINARY`, `ESCAPE` |
| `YamlEngineException` | runtime exception root |
| `MarkedYamlEngineException` | `getProblemMark` |
| `ParserException`, `ScannerException`, `DuplicateKeyException` | marked exception subtypes |
| `Mark` | `getLine` |
| `CoreSchema` | constructor `CoreSchema()` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Load` | class | Load pipeline: YAML text to Java objects. |
| `LoadSettings` | class | Immutable load configuration built through its builder. |
| `Dump` | class | Dump pipeline: Java objects to YAML text. |
| `DumpSettings` | class | Immutable dump configuration built through its builder. |
| `Compose` | class | Low-level pipeline: YAML text to the node graph. |
| `Node` | class | Base of the composed node model. |
| `ScalarNode` | class | A tagged scalar with text and style. |
| `SequenceNode` | class | An ordered node list. |
| `MappingNode` | class | An ordered list of key/value node tuples. |
| `NodeTuple` | class | One mapping entry: key node and value node. |
| `NodeType` | enum | Structural classification of a node. |
| `Tag` | class | YAML tag; carries the standard tag constants. |
| `FlowStyle` | enum | Collection presentation: block, flow, or automatic. |
| `ScalarStyle` | enum | Scalar presentation: plain, quoted, literal, folded. |
| `NonPrintableStyle` | enum | Handling of non-printable characters on dump. |
| `YamlEngineException` | exception | Engine failure root type. |
| `MarkedYamlEngineException` | exception | Failure with positional marks. |
| `ParserException` | exception | Syntax-level failure. |
| `ScannerException` | exception | Lexical-level failure. |
| `DuplicateKeyException` | exception | Duplicate mapping key under strict settings. |
| `Mark` | class | A position in the parsed input. |
| `CoreSchema` | class | YAML 1.2 core scalar resolution. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; no third-party runtime library beyond the target artifact is guaranteed to the implementation. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.snakeyaml:snakeyaml-engine`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the public load, dump, compose, and settings surfaces. Tests compare loaded Java values and their runtime types, dumped text strings, node-graph structure and tags, exception classes and positional marks, and cross-view consistency between the pipelines; they do not require internal scanner, parser, or emitter classes, private fields, or exact exception message text beyond the documented label and alias-maximum requirements. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking round trips and settings interactions across complete load–dump workflows.
