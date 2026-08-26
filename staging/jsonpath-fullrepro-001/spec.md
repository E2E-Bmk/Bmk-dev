# json-path Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`json-path` is a Java library for querying and mutating JSON documents through path expressions. A path expression addresses values inside a parsed document — by property name, array index, slice, union, wildcard, deep scan, filter predicate, or aggregate function — and evaluates against an in-memory document model of ordered maps and lists.

The library exposes one evaluation engine through several projections: static one-shot reads (`JsonPath.read`), reusable compiled paths (`JsonPath.compile`), fluent document contexts with read and write operations (`JsonPath.parse`), and a configuration layer (`Configuration`, `Option`) whose flags change the result shape of the same query — list wrapping, path listing, null leaves, suppressed errors, and strict property requirements. Filter predicates are written inline in the path text or built programmatically with `Filter` and `Criteria`.

## Non-Goals

- This specification does not define alternative document providers or mapper backends; the default provider model (ordered maps, lists, boxed primitives, strings) is the only one in scope.
- This specification does not define caching behavior for compiled paths.
- This specification does not require streaming or partial-document parsing.
- This specification does not define evaluation listeners or read tracking.
- This specification does not define thread-safety guarantees for sharing document contexts across threads.

## Representative Workflows

The examples below use this document, called *store* throughout:

```json
{"store":{"book":[
  {"category":"reference","author":"Nigel Rees","title":"Sayings of the Century","price":8.95},
  {"category":"fiction","author":"Evelyn Waugh","title":"Sword of Honour","price":12.99},
  {"category":"fiction","author":"Herman Melville","title":"Moby Dick","isbn":"0-553-21311-3","price":8.99},
  {"category":"fiction","author":"J. R. R. Tolkien","title":"The Lord of the Rings","isbn":"0-395-19395-8","price":22.99}],
  "bicycle":{"color":"red","price":19.95}},"expensive":10}
```

The first workflow answers one-shot queries with the static entry point.

```java
import com.jayway.jsonpath.JsonPath;

String color = JsonPath.read(store, "$.store.bicycle.color");        // "red"
List<String> authors = JsonPath.read(store, "$..author");             // all four authors
List<String> cheap = JsonPath.read(store, "$.store.book[?(@.price < 10)].title");
```

The second workflow parses once and runs several reads and writes over the same context; write operations chain fluently and mutate the parsed model in place.

```java
import com.jayway.jsonpath.DocumentContext;

DocumentContext ctx = JsonPath.parse("{\"a\":{\"b\":1},\"list\":[1,2]}");
ctx.set("$.a.b", 42).put("$.a", "c", "new").add("$.list", 3);
int b = ctx.read("$.a.b");                                            // 42
```

The third workflow changes result shape purely through options.

```java
import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.Option;

Configuration cfg = Configuration.builder().options(Option.ALWAYS_RETURN_LIST).build();
List<String> one = JsonPath.using(cfg).parse(store).read("$.store.bicycle.color"); // ["red"]
```

## Path Grammar and Read Evaluation

A path starts at the document root `$`. Inside filter expressions, `@` names the current candidate item. Properties are addressed in dot form (`$.store.bicycle.color`) or bracket form (`$['store']['bicycle']['color']`); both address the same value.

The grammar in scope, with its evaluation semantics:

- Index: `$.store.book[0]`; a negative index counts from the end (`[-1]` is the last element).
- Slice: `[1:3]` selects indexes 1 and 2, half-open.
- Index union: `[0,2]` selects the listed indexes in the listed order.
- Property union: `['title','price']` projects the named properties of one object into an ordered map result.
- Wildcard: `[*]` or `.*` selects every element or every member value.
- Deep scan: `..name` selects every descendant value under any depth whose property matches.
- Filter: `[?(...)]` selects array elements satisfying the predicate.
- Function: a trailing `.length()`, `.min()`, `.max()`, `.sum()`, `.avg()`, or `.keys()` aggregates the addressed value.

**Definiteness and result shape.** A path is *definite* when it contains no wildcard, scan, slice, union, or filter; `isDefinite()` on a compiled path reports this. Under default options, a definite path evaluates to the addressed value itself (string, boxed number, boolean, null, map, or list), and an indefinite path evaluates to a list of every match (possibly empty for filters, in document order). On the store: `$.store.book[-1].title` yields `"The Lord of the Rings"`; `$..author` yields all four author strings in document order; `$.store.book[1:3].title` yields the two middle titles; `$.store.bicycle.*` yields `["red", 19.95]`.

**Document model.** JSON objects load as insertion-ordered maps, arrays as lists, numbers as `Integer`/`Double` (per shape), strings as `String`, `true`/`false` as `Boolean`, `null` as null. `$.expensive` reads as `Integer` 10; `$.store.bicycle.price` as `Double` 19.95.

## Filters and Criteria

An inline filter `[?(expr)]` evaluates its expression once per array element with `@` bound to the element:

- Existence: `[?(@.isbn)]` keeps elements that have the property.
- Comparisons: `==`, `<`, `>` and friends compare against literals (`[?(@.price < 10)]`, `[?(@.category == 'fiction')]`).
- Document references: the right side may reference the root (`[?(@.price > $.expensive)]`).
- Regular expressions: `[?(@.author =~ /.*Tolkien/)]` matches against a slash-delimited pattern.
- Membership: `[?(@.category in ['reference'])]`.

**Programmatic filters.** `Criteria.where(property)` starts a predicate; `is(value)`, `lt(value)`, `gt(value)` constrain it; `and(property)` chains a further constraint on another property. `Filter.filter(criteria)` wraps it as a filter usable in a path through the `[?]` placeholder: `JsonPath.read(store, "$.store.book[?]", filter)` binds the placeholder. A filter's `toString()` renders the equivalent inline form: `Filter.filter(Criteria.where("price").lt(10)).toString()` is `[?(@['price'] < 10)]`.

## Functions

Aggregate functions apply to the value addressed by the path prefix:

- `length()` on an array yields its size as `Integer` (`$.store.book.length()` is 4).
- `min()`, `max()`, `sum()`, `avg()` on a numeric sequence yield `Double` values: over `$..book[*].price` they are 8.95, 22.99, 53.92, and 13.48.
- `keys()` on an object yields its key set in document order (`$.store.bicycle.keys()` is `[color, price]`).

## Parsing and Document Contexts

`JsonPath.parse(jsonString)` parses to a `DocumentContext`; `JsonPath.using(configuration).parse(jsonString)` does the same under explicit configuration. `JsonPath.read(json, path, filters…)` is a one-shot convenience equal to `parse` + `read`.

A `DocumentContext` reads with `read(path, filters…)` and `read(path, type)`, where the type overload coerces the raw result (`read("$.expensive", String.class)` yields `"10"`; `Integer.class` yields 10). `json()` returns the live document model root; `jsonString()` serializes the current model state to JSON text.

## Compiled Paths

`JsonPath.compile(path, filters…)` parses the path text once into a reusable `JsonPath` object. `read(jsonString)` evaluates it against a document; `getPath()` returns the normalized bracket form of the path text (`$.store.book[0].title` normalizes to `$['store']['book'][0]['title']`); `isDefinite()` reports definiteness as defined above. Compiling and reading must produce exactly the value the static read produces for the same path and document.

## Write Operations

Write operations evaluate the path, mutate the addressed location in the live model, and return the same context for chaining:

- `set(path, value)` replaces the addressed value.
- `put(path, key, value)` adds or replaces a member of the addressed object.
- `add(path, value)` appends to the addressed array.
- `delete(path)` removes the addressed value from its parent.
- `renameKey(path, oldKey, newKey)` renames a member of the addressed object.
- `map(path, mapFunction)` replaces each matched value with the function's result; the function receives the current value and the configuration.

Every mutation is immediately visible through `read`, `json()`, and `jsonString()` on the same context.

## Configuration Options

`Configuration.defaultConfiguration()` carries no options; `addOptions(options…)` returns a configuration with options added; `Configuration.builder().options(options…).build()` constructs one directly; `getOptions()` exposes the resulting set. Options change result shape, not path syntax:

- `ALWAYS_RETURN_LIST` — indefinite results are unchanged; a definite result is wrapped in a one-element list (`["red"]`).
- `AS_PATH_LIST` — a query returns the normalized path strings of its matches instead of their values: `$..author` yields `$['store']['book'][0]['author']` through `$['store']['book'][3]['author']`.
- `DEFAULT_PATH_LEAF_TO_NULL` — a missing leaf property on an existing parent evaluates to null instead of raising.
- `SUPPRESS_EXCEPTIONS` — evaluation failures yield null; combined with `ALWAYS_RETURN_LIST` they yield an empty list.
- `REQUIRE_PROPERTIES` — indefinite evaluation raises `PathNotFoundException` when a referenced property is missing rather than skipping it; a definite read of a missing property raises it as well.

## State Model

The core state is the parsed document model held by a `DocumentContext`: insertion-ordered maps, lists, and boxed scalar values. Public projections of that one state are: evaluated reads under a configuration (values, wrapped lists, path lists, or nulls per the options); the live root through `json()`; the serialized text through `jsonString()`; and compiled-path evaluation against the same document. Write operations mutate the model in place; configurations and compiled paths are immutable and reusable across documents.

- Reads never mutate the document: repeated evaluation of any path yields equal results.
- Writes are immediately coherent: after a write, every read projection reflects it.
- The same path text evaluates identically through the static, compiled, and context entry points under the same configuration.

## Error Semantics

| Condition | Required result |
|---|---|
| Definite path addressing a missing property, an out-of-range index, or descending into a scalar | Must raise `PathNotFoundException`; the message names the failing normalized path. |
| Path text that cannot be parsed | `compile`/`read` must raise `InvalidPathException`. |
| Null or empty path text | Must raise `IllegalArgumentException`. |
| Input text that is not valid JSON | `parse` must raise `InvalidJsonException`. |
| `add` targeting a value that is not an array | Must raise `InvalidModificationException`. |
| Missing property under `REQUIRE_PROPERTIES` | Must raise `PathNotFoundException`. |

All of these except `IllegalArgumentException` are subclasses of `JsonPathException`. With `SUPPRESS_EXCEPTIONS` set, evaluation failures follow the option's null/empty-list contract instead of raising.

## Cross-View Invariants

1. For any path and document, `JsonPath.read(json, path)`, `JsonPath.compile(path).read(json)`, and `JsonPath.parse(json).read(path)` must return equal results.
2. `compile(p).getPath()` re-compiles to an equivalent path: evaluating the normalized form returns the same result as the original text.
3. Under `AS_PATH_LIST`, each returned path string, read back individually against the same document, must yield exactly the values the plain query returns, in the same order.
4. `ALWAYS_RETURN_LIST` never changes match content: for a definite path, the single wrapped element equals the unwrapped read; for an indefinite path, the result equals the default read.
5. The `[?]` placeholder bound to `Filter.filter(criteria)` must select exactly the elements the equivalent inline filter text selects.
6. Write-then-read coherence: after any sequence of write operations, `read`, `json()`, and re-parsing `jsonString()` all present the same values.
7. `isDefinite()` predicts result shape under default options: definite paths return the addressed value, indefinite paths return a list.

## Public Interface

### Import Surface

```java
import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.Criteria;
import com.jayway.jsonpath.DocumentContext;
import com.jayway.jsonpath.Filter;
import com.jayway.jsonpath.InvalidJsonException;
import com.jayway.jsonpath.InvalidModificationException;
import com.jayway.jsonpath.InvalidPathException;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.JsonPathException;
import com.jayway.jsonpath.MapFunction;
import com.jayway.jsonpath.Option;
import com.jayway.jsonpath.ParseContext;
import com.jayway.jsonpath.PathNotFoundException;
import com.jayway.jsonpath.Predicate;
import com.jayway.jsonpath.ReadContext;
import com.jayway.jsonpath.WriteContext;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `JsonPath` | static `read(String, String, Predicate...)`, `parse(String)`, `using(Configuration)`, `compile(String, Predicate...)`; instance `read(String)`, `read(String, Configuration)`, `getPath`, `isDefinite` |
| `DocumentContext` | `read(String, Predicate...)`, `read(String, Class)`, `json`, `jsonString`, `set`, `put`, `add`, `delete`, `renameKey`, `map`, `configuration` |
| `ParseContext` | `parse(String)` |
| `ReadContext` / `WriteContext` | the read/write halves of `DocumentContext` |
| `Configuration` | static `defaultConfiguration()`, `builder()`; `addOptions`, `getOptions`; builder: `options`, `build` |
| `Option` | enum constants `ALWAYS_RETURN_LIST`, `AS_PATH_LIST`, `DEFAULT_PATH_LEAF_TO_NULL`, `SUPPRESS_EXCEPTIONS`, `REQUIRE_PROPERTIES` |
| `Filter` | static `filter(Criteria)`; `toString` |
| `Criteria` | static `where(String)`; `is`, `lt`, `gt`, `and` |
| `Predicate` | filter contract accepted by path evaluation |
| `MapFunction` | value-transform contract for `map` |
| `JsonPathException` | exception root |
| `PathNotFoundException`, `InvalidPathException`, `InvalidJsonException`, `InvalidModificationException` | failure subtypes |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `JsonPath` | class | Static entry points and compiled path objects. |
| `DocumentContext` | interface | Fluent read/write view over one parsed document. |
| `ParseContext` | interface | Parse entry point bound to a configuration. |
| `ReadContext` | interface | Read operations of a document context. |
| `WriteContext` | interface | Write operations of a document context. |
| `Configuration` | class | Immutable option set for evaluation. |
| `Option` | enum | Result-shape flags. |
| `Filter` | class | Programmatic filter predicate. |
| `Criteria` | class | Fluent predicate builder. |
| `Predicate` | interface | Filter contract bound to `[?]` placeholders. |
| `MapFunction` | interface | Transform applied by `map`. |
| `JsonPathException` | exception | Library failure root. |
| `PathNotFoundException` | exception | Path evaluation found nothing. |
| `InvalidPathException` | exception | Path text unparseable. |
| `InvalidJsonException` | exception | Input text unparseable. |
| `InvalidModificationException` | exception | Write operation illegal for the addressed value. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; the target artifact's own declared runtime dependencies resolve through Maven. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `com.jayway.jsonpath:json-path`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the public read, compile, context, write, filter, function, and option surfaces. Tests compare evaluated values and their runtime types, result containers and order, normalized path strings, mutated document projections, exception classes, and cross-view consistency between the static, compiled, and context entry points under varying option sets; they do not require internal token or provider classes, private fields, or exact exception message text beyond the documented normalized-path naming. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking that option combinations and write sequences keep every projection consistent.
