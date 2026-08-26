# Object-Graph XPath Engine Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`commons-jxpath` is an XPath query engine for Java object graphs. Callers wrap any Java object — a JavaBean, a `java.util.Map`, a collection, or a DOM `Document` — in an evaluation context and then read, write, create, and remove values anywhere in the graph using XPath 1.0 path expressions. One query language addresses every supported data model: the same path syntax that selects an XML element also selects a bean property, a map entry, or a list element, and mixed graphs (a map holding beans holding lists holding documents) are traversed uniformly.

Beyond value queries the engine exposes pointers — canonical, re-executable addresses of individual graph locations — plus declared variables usable inside expressions, extension functions that bridge into Java methods, factories that build out missing parts of the graph on demand, and compiled expressions that reuse one parsed query across many contexts. Lookup discipline is configurable per context: strict contexts raise when a path matches nothing, lenient contexts return null.

The installable artifact is the Maven coordinate `commons-jxpath:commons-jxpath`.

## Non-Goals

- This specification does not require any XML object model other than the JDK's DOM (`org.w3c.dom`); alternative tree models and their parsers are not part of the contract.
- This specification does not require XML namespace handling: no namespace registration, prefix resolution, or namespace-axis queries.
- This specification does not require lazily-parsed document containers or URL-based document loading; DOM inputs arrive already parsed.
- This specification does not require `id()` or `key()` resolution, nor the manager interfaces that back them.
- This specification does not require locale configuration or localized number formatting (`format-number`).
- This specification does not require a pluggable type-conversion registry or conversions beyond those documented in the behavior sections.
- This specification does not require exception-handler registration or servlet-scope contexts.
- This specification does not define thread-safety guarantees; each context is used single-threadedly by its caller.
- This specification does not define an introspection cache or custom dynamic-property handler registration beyond the documented map support.

## Representative Workflows

**Query and update a bean graph.**

```java
public class Employee {                       // caller-owned JavaBean
    private String name = "Ada";
    private int age = 36;
    private List<String> phones = new ArrayList<>(List.of("111", "222"));
    // getters and setters ...
}

JXPathContext ctx = JXPathContext.newContext(employee);
ctx.getValue("name");                          // "Ada"
ctx.getValue("age");                           // 36 (Integer, unconverted)
ctx.getValue("phones[2]");                     // "222" — indexing is 1-based
ctx.setValue("age", "41");                     // converts to the int property
Pointer p = ctx.getPointer("phones[2]");
p.asPath();                                    // "/phones[2]"
p.setValue("999");                             // writes through to the list
```

**One query language over maps, beans, and XML.**

```java
Map<String, Object> root = new HashMap<>();
root.put("boss", employee);
root.put("doc", domDocument);                  // org.w3c.dom.Document

JXPathContext ctx = JXPathContext.newContext(root);
ctx.getValue("boss/phones[1]");                // "111"
ctx.getValue("doc/company/employee[2]/name");  // element text
ctx.getVariables().declareVariable("min", 40);
ctx.getValue("count(doc/company/employee[age > $min])");   // 1.0

Iterator<Pointer> it = ctx.iteratePointers("boss/phones");
it.next().asPath();                            // "/.[@name='boss']/phones[1]"
```

## Contexts and Path Queries

A context binds one root object to the query engine; every read and write on the context is an XPath expression evaluated against the live graph.

**Creating contexts.** The static call `JXPathContext.newContext(contextBean)` returns a context over the given root object. The context stores a reference to the root — never a copy — and `getContextBean()` returns that same object. `getParentContext()` returns null for a context created this way. The two-argument form `newContext(parentContext, contextBean)` creates a child context: the child answers `getParentContext()` with the parent, resolves variables it does not hold locally through the parent's variable store, and inherits the parent's leniency setting at creation time.

**Reading values.** `getValue(xpath)` evaluates the expression and returns its value. When the expression is a location path, the result is the underlying Java value of the first matching location: bean property values are returned in their property type (an `int` property arrives as `Integer`, not a string), map values are returned as stored, list elements as stored, and a DOM element yields the concatenation of all its descendant text. When a path matches more than one location, `getValue` must return exactly the first element that `iterate` produces for the same path. When a path matches nothing, the strict/lenient discipline decides the outcome (see Leniency, Nested Contexts, and Compiled Expressions).

**Expression typing.** Non-path XPath expressions follow XPath 1.0 result typing: arithmetic and numeric functions return `Double` (`2 + 2` is 4.0, `count(phones)` is 2.0, `string-length(name)` is a `Double`, `sum(employees/age)` adds numerically), comparisons and boolean functions return `Boolean`, and string functions return `String`. Values drawn from the graph participate with coercion — `age + 1` on an integer property returns a `Double`; `string(age)` returns the decimal text. Arithmetic, `position()`, `last()`, variables, and nested function calls are all usable inside predicates: `phones[1 + 1]`, `phones[$i]`, `employees[position() > 1]`, and `employees[starts-with(name, 'B')]` must each select accordingly. The core XPath 1.0 function library (`count`, `sum`, `concat`, `substring`, `string-length`, `starts-with`, `contains`, `not`, `string`, `number`, `boolean`, `name`, `position`, `last`) must be available in every context regardless of any function-set installation, as must the union operator `|` and the wildcard step `*`.

**Typed reads.** `getValue(xpath, requiredType)` converts the result to the requested class: `Double` results convert to `Integer` when asked (`count(...)` as `Integer.class`), numeric strings convert to numeric wrappers (`"111"` to `Integer` 111), numbers convert to `String`, and a collection converts to a scalar by taking its first element, or to an array type by converting each element (`phones` to `String[]`). A conversion with no defined path for the actual value fails; conversion of a numeric-looking request over non-numeric text raises the underlying Java `NumberFormatException`.

**Multi-match reads.** `iterate(xpath)` returns an `Iterator` over the values of every matching location, in document order for DOM nodes, index order for collections, and name order for properties (see Object Models). A path matching a single value yields a one-element iterator. A path matching nothing yields an empty iterator in both strict and lenient contexts — iteration never raises for a missing path. `iteratePointers(xpath)` yields one `Pointer` per match in the same order. `selectNodes(xpath)` returns a `java.util.List` of the underlying node objects of every match — for DOM matches the `org.w3c.dom.Element` itself, not its text; for bean or map matches the raw stored object — and returns an empty list when nothing matches. `selectSingleNode(xpath)` returns the node of the first match, and applies the strict/lenient no-match discipline.

## Object Models

The engine maps each supported data model onto XPath's node abstraction; these mapping rules are the heart of the contract.

**Beans.** A child step named `x` on a bean reads the JavaBeans property `x` through its public getter; nested steps chain through the graph (`address/city`). The attribute form `@x` addresses the same property — `@name` and `name` are interchangeable on beans. The suffixed form `node[@name='p']` is a property-access form, not a filter: it reads the property (or map entry) named `p` of the node, on beans and maps alike, so `.[@name='name']` reads the root bean's `name` property. Filtering the elements of a bean collection on a property value uses the child-name predicate (`employees[name = 'Bob']`). Property enumeration — the wildcard `*`, unions across properties — visits bean properties in ascending alphabetical order of property name. A collection-valued property contributes each of its elements as an individual node: with a two-element `phones` list, `*` on the bean visits `age`, `name`, then `phones[1]`, `phones[2]`, and `count(*)` counts the elements, while a map-valued property contributes itself as one node.

**Maps.** A map anywhere in the graph exposes its entries as dynamic properties: the child step `k` reads the value at string key `k`, and the attribute-predicate form `props[@name='k']` addresses the same entry. Map keys are treated as always present: reading a missing key returns null even in a strict context, and `setValue` on a previously absent key inserts it without any factory. Enumeration of map entries (`*`, `props/*`) visits keys in ascending string order regardless of the map's own iteration order.

**Collections and arrays.** List and array values index from 1: `phones[1]` is the first element and `phones[last()]` the last. An index of 0, a negative index, or an index past the end is a no-match, handled by the strict/lenient discipline. Predicates filter collection elements — `employees[name = 'Bob']/age` selects the property of the matching element; `employees[age > 40]` selects by comparison. Writing a list element with `setValue` stores the given value as-is, without conversion, because a list carries no element-type information.

**DOM documents.** A context over an `org.w3c.dom.Document` addresses the tree with standard XPath steps, starting at the document element (`/company/employee[1]/name`). `getValue` on an element returns its text content (all descendant text concatenated); `selectSingleNode` and `selectNodes` return the `Element` objects themselves; `text()` selects text nodes; `@attr` reads attributes; `name(node)` returns the element name. Element text participates in numeric coercion (`age + 1` over element text is a `Double`). `setValue` on an element replaces its text content, and on an attribute rewrites the attribute value. `//` descendant searches, positional predicates, and attribute predicates (`employee[@id='e2']`) must all operate on DOM as on every other model.

**Mixed graphs.** Models compose transparently: a map entry holding a bean is traversed with bean rules from that point on, a bean property holding a `Document` continues with DOM rules (`doc/company/employee[2]/name`), and pointers, variables, factories, and functions behave identically throughout. The descendant axis `//` searches across model boundaries.

## Pointers, Canonical Paths, and Relative Contexts

A pointer is a durable, canonical address of one graph location, usable to re-read, rewrite, and re-anchor queries.

**Obtaining pointers.** `getPointer(xpath)` returns the pointer of the first matching location; `iteratePointers(xpath)` yields all of them; `getContextPointer()` returns the pointer of the context root, whose `asPath()` is `"/"`. `getValue()` returns the value at the pointer's location, and `setValue(value)` writes through to the underlying object with the same conversion rules as context-level `setValue`; after a write through a pointer, that same pointer's `getValue()` must report the written value. `getNode()` returns the raw node object — for DOM locations the `Element` rather than its text, for bean and map locations the stored value. `getRootNode()` returns the root object of the graph the pointer belongs to.

**Canonical paths.** `asPath()` renders the canonical XPath of the location the pointer addresses. Canonical forms are: `/name` for a bean property of the root; `/phones[2]` for a collection element; `/props[@name='grade']` for a map entry reached through a bean property; `/.[@name='boss']` for an entry of a map that is itself the context root; `$v` for a variable location; and for DOM locations, an explicit index on every step (`/company[1]/employee[2]/name[1]`). A pointer obtained through a filtering predicate canonicalizes to the positional form: asking for `employees[name='Bob']` yields the pointer whose path is `/employees[2]`. Every canonical path must round-trip — evaluating `context.getValue(pointer.asPath())` on the originating context returns the same value the pointer reports.

**Relative contexts.** `getRelativeContext(pointer)` returns a new context rooted at the pointer's location: relative paths evaluate from there (`name` on a relative context over `/employees[2]`), the parent axis walks outward (`../name`), and the relative context answers `getParentContext()` with the context it was derived from and resolves variables through it. Pointers produced by a relative context report root-anchored canonical paths — `getPointer("age")` on a context relative to `/employees[2]` has the path `/employees[2]/age` — so paths remain valid against the base context.

## Writing, Creating, and Removing

Write operations mutate the caller's own objects in place; the graph is never copied.

**Setting values.** `setValue(xpath, value)` locates the path and stores the value with model-appropriate conversion: writing a string to an `int` bean property converts it (`"41"` becomes 41); writing to a map key inserts or overwrites the entry; writing to a list element stores the value unconverted; writing to a DOM element or attribute stores text; writing to `$var` reassigns a declared variable. The path must already match a writable location — `setValue` never builds missing structure, and leniency does not soften writes: a `setValue` whose path matches nothing raises `JXPathException` in strict and lenient contexts alike. A value that cannot convert to the target property type also raises `JXPathException`.

**Creating paths.** `createPath(xpath)` builds out the missing portion of a path and returns the pointer of the resulting location. Building bean structure requires an `AbstractFactory` installed with `setFactory(factory)`: the engine calls `createObject(context, pointer, parent, name, index)` once for each missing or null step — including a null leaf property — and the factory must make the named child real (instantiate and attach it through the parent's setter) and return true. When no factory is installed and creation is needed, `createPath` raises `JXPathException`; when the installed factory returns false for a step, `createPath` raises `JXPathException` whose cause is `JXPathAbstractFactoryException`. Creating a null-valued map key also consults the factory, and `createPath("$name")` for an undeclared variable consults the factory's `declareVariable(context, varName)` hook, which must declare the variable on the context and return true. `getFactory()` returns the installed factory.

**Creating with a value.** `createPathAndSetValue(xpath, value)` builds intermediate structure exactly like `createPath` and then assigns the leaf, so the leaf step itself needs no factory handling: with a factory that only knows how to attach the intermediate bean, `createPathAndSetValue("address/city", "Tromso")` succeeds. On maps it inserts the key with the given value without any factory at all.

**Removing.** `removePath(xpath)` deletes the single location the path matches: a map key is removed from the map, a list element is removed and the list shrinks, a DOM element is detached from its parent. A `removePath` whose path matches nothing raises `JXPathException`. `removeAll(xpath)` removes every location the path matches — `removeAll("phones")` empties the list, `removeAll("phones[position() > 1]")` keeps only the first element, `removeAll("props/*")` clears the map — and is a silent no-op when nothing matches.

## Variables and Extension Functions

Expressions reach beyond the graph through declared variables and installed function sets.

**Variables.** Each context owns a variable store reachable with `getVariables()` and replaceable with `setVariables(vars)`; the default store is a `BasicVariables` instance. `declareVariable(varName, value)` binds a name (a null value is a legal binding), `getVariable(varName)` returns the bound value, `isDeclaredVariable(varName)` tests the binding, and `undeclareVariable(varName)` removes it, silently tolerating absent names. `BasicVariables.getVariable` on an undeclared name raises `IllegalArgumentException`. Inside expressions `$name` reads a variable, `$name[2]` indexes a collection-valued variable, and variables participate in arithmetic and predicates (`$bonus + age` is a `Double`; `phones[$i]` selects by the variable's value). The pointer of a variable location has the canonical path `$name`. Reading `$name` for an undeclared name in an expression raises `JXPathException` in every mode — `JXPathNotFoundException` in a strict context. `setValue("$name", value)` reassigns a declared variable and raises `JXPathException` for an undeclared one.

**Function sets.** `setFunctions(functions)` installs a `Functions` set on the context and `getFunctions()` returns it. `ClassFunctions(functionClass, namespace)` exposes the public static methods of one class under a namespace prefix: with `new ClassFunctions(Util.class, "t")` installed, the expression `t:shout(name)` calls `Util.shout(String)` with the property value, and arguments convert to the declared parameter types (`t:triple('9')` and `t:triple(2.0)` both reach an `int` parameter). `PackageFunctions(classPrefix, namespace)` maps namespaced calls onto classes located by name prefix; constructed as `new PackageFunctions("", null)` it provides unprefixed method-call functions, where `size(phones)` invokes the Java method `size()` on the argument object and returns its actual result (an `Integer`, unlike the XPath `count` function's `Double`). `FunctionLibrary` aggregates multiple sets through `addFunctions(functions)` and dispatches by namespace; `removeFunctions(functions)` detaches a set. Each set answers `getUsedNamespaces()` with the namespaces it serves — a `ClassFunctions` reports exactly its one prefix.

**Resolution and replacement.** A context with no installed set resolves unprefixed non-core function names as method-call functions, so `size(phones)` works out of the box. Installing any function set replaces this default entirely: after `setFunctions(new ClassFunctions(...))`, `size(phones)` raises `JXPathFunctionNotFoundException` unless the installed set is a `FunctionLibrary` that also contains a `new PackageFunctions("", null)`. Core XPath functions are not affected by installation and remain callable always. Any function call that no installed set and no core function resolves raises `JXPathFunctionNotFoundException`.

## Leniency, Nested Contexts, and Compiled Expressions

Lookup discipline, context chaining, and expression reuse are per-context concerns that leave path semantics untouched.

**Strict and lenient lookup.** A fresh context is strict: `isLenient()` returns false, and `getValue`, `getPointer`, and `selectSingleNode` raise `JXPathNotFoundException` when their path matches nothing — including an out-of-range collection index. After `setLenient(true)`, the same three calls return null instead — except that `getPointer` returns a non-null placeholder pointer whose `asPath()` renders the requested path and whose `getValue()` and `getNode()` are null. Writing through such a placeholder raises `JXPathInvalidAccessException`. Leniency changes nothing else: `iterate`, `iteratePointers`, and `selectNodes` produce empty results for missing paths in both modes; map keys read as null in both modes; writes, creates, and removes behave identically in both modes; and every path that does match returns identical results under either setting.

**Context chains.** A child context made with `newContext(parentContext, contextBean)` reads variables through its parent when its own store lacks the name, and starts with the parent's leniency. A relative context (see Pointers) behaves as a child of the context it came from. `getContextBean()` always returns the context's own root object; `getParentContext()` returns the parent or null at the top of the chain.

**Compiled expressions.** The static `JXPathContext.compile(xpath)` parses an expression once and returns a `CompiledExpression`; syntax errors surface at compile time as `JXPathInvalidSyntaxException`. The compiled form is context-independent and reusable: `getValue(context)`, `getValue(context, requiredType)`, `setValue(context, value)`, `getPointer(context, xpath)`, `iterate(context)`, `iteratePointers(context)`, `createPath(context)`, `createPathAndSetValue(context, value)`, `removePath(context)`, and `removeAll(context)` each apply the parsed expression to the given context with exactly the semantics of the same-named context method, so one compiled query evaluated against two different graphs reports each graph's own values.

## State Model

The engine's state is the caller's object graph plus per-context interpretation settings; nothing is snapshotted.

A context wraps its root object by reference. Every query walks the live graph at call time, so external mutation of the graph is visible to the next query, and every write (`setValue`, `createPath`, `createPathAndSetValue`, `removePath`, `removeAll`, `Pointer.setValue`) mutates the caller's objects directly and is immediately visible both to subsequent queries and to the caller's own code. Discarding a context does not affect the graph; a new context over the same root sees all prior mutations.

Per-context settings — the leniency flag, the variable store, the installed factory, and the installed function set — are consulted at each call and never alter the graph. Pointers and relative contexts stay anchored at graph locations and write through: a value written through a pointer is immediately visible to that pointer, to context queries, and to the caller's objects. Compiled expressions hold only parsed syntax and no context or graph state.

Contexts form chains: child contexts delegate variable resolution upward and copy the parent's leniency at creation; a relative context is a child anchored at a pointer's location whose reported paths stay root-anchored.

## Error Semantics

| Condition | Raised |
|---|---|
| Expression text that does not parse (any operation, including `compile` and the empty string) | `JXPathInvalidSyntaxException` |
| Strict-mode `getValue` / `getPointer` / `selectSingleNode` on a path matching nothing | `JXPathNotFoundException` |
| Reading an undeclared variable in an expression (strict context) | `JXPathNotFoundException` |
| Reading an undeclared variable in an expression (lenient context) | `JXPathException` |
| `BasicVariables.getVariable` on an undeclared name | `IllegalArgumentException` |
| `setValue` on a path matching no writable location (any mode), or on an undeclared variable | `JXPathException` |
| `setValue` with a value that cannot convert to the target property type | `JXPathException` |
| `Pointer.setValue` on a lenient placeholder pointer | `JXPathInvalidAccessException` |
| Function call no function set resolves | `JXPathFunctionNotFoundException` |
| `createPath` / `createPathAndSetValue` needing creation with no factory installed | `JXPathException` |
| `createPath` step the installed factory declines (returns false) | `JXPathException` with a `JXPathAbstractFactoryException` cause |
| `removePath` on a path matching nothing | `JXPathException` |
| `getValue(xpath, type)` converting non-numeric text to a numeric type | `NumberFormatException` |

`JXPathNotFoundException`, `JXPathInvalidSyntaxException`, `JXPathFunctionNotFoundException`, `JXPathInvalidAccessException`, and `JXPathAbstractFactoryException` all extend `JXPathException`, which extends `RuntimeException`; none are checked.

## Cross-View Invariants

1. **Pointer round-trip.** For every pointer produced by `getPointer` or `iteratePointers` on any model — bean, map, collection, DOM, or variable — `context.getValue(pointer.asPath())` on the originating context must return the same value as `pointer.getValue()`.
2. **First-match agreement.** For any path that matches at least one location, `getValue` must return the first value produced by `iterate`, `selectSingleNode` must return the first node in `selectNodes`'s list, and `getPointer(...).asPath()` must equal the `asPath()` of the first pointer from `iteratePointers`.
3. **Cardinality agreement.** For any path, the number of elements produced by `iterate`, the number of pointers produced by `iteratePointers`, the size of `selectNodes`'s list, and the numeric value of `count(path)` must all be equal.
4. **Write–read coherence.** After a successful write through any channel — `setValue`, `createPathAndSetValue`, `Pointer.setValue`, or `CompiledExpression.setValue` — reading the same path on the same context must return the stored value (converted per the target's rules), and the caller's underlying Java object must observe the mutation directly.
5. **Compiled equivalence.** For any expression string and any context, each `CompiledExpression` operation must produce the same value, pointer path, mutation, or exception type as the same-named operation invoked directly on the context with the same expression text.
6. **Relative-root agreement.** For any pointer `p` of a context, every pointer obtained from `getRelativeContext(p)` must report a root-anchored `asPath()` that, evaluated on the base context, returns the value the relative context reports.
7. **Mode neutrality for matches.** For every path that matches at least one location, a strict context and a lenient context over the same graph must return identical results from every read operation; the two modes differ only in the documented no-match outcomes.

## Public Interface

### Import Surface

```java
import org.apache.commons.jxpath.AbstractFactory;
import org.apache.commons.jxpath.BasicVariables;
import org.apache.commons.jxpath.ClassFunctions;
import org.apache.commons.jxpath.CompiledExpression;
import org.apache.commons.jxpath.FunctionLibrary;
import org.apache.commons.jxpath.Functions;
import org.apache.commons.jxpath.JXPathAbstractFactoryException;
import org.apache.commons.jxpath.JXPathContext;
import org.apache.commons.jxpath.JXPathException;
import org.apache.commons.jxpath.JXPathFunctionNotFoundException;
import org.apache.commons.jxpath.JXPathInvalidAccessException;
import org.apache.commons.jxpath.JXPathInvalidSyntaxException;
import org.apache.commons.jxpath.JXPathNotFoundException;
import org.apache.commons.jxpath.PackageFunctions;
import org.apache.commons.jxpath.Pointer;
import org.apache.commons.jxpath.Variables;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `JXPathContext` | `static JXPathContext newContext(Object contextBean)`; `static JXPathContext newContext(JXPathContext parentContext, Object contextBean)`; `static CompiledExpression compile(String xpath)`; `Object getValue(String xpath)`; `Object getValue(String xpath, Class requiredType)`; `void setValue(String xpath, Object value)`; `Pointer getPointer(String xpath)`; `Pointer getContextPointer()`; `Pointer createPath(String xpath)`; `Pointer createPathAndSetValue(String xpath, Object value)`; `void removePath(String xpath)`; `void removeAll(String xpath)`; `<E> Iterator<E> iterate(String xpath)`; `Iterator<Pointer> iteratePointers(String xpath)`; `List selectNodes(String xpath)`; `Object selectSingleNode(String xpath)`; `JXPathContext getRelativeContext(Pointer pointer)`; `Object getContextBean()`; `JXPathContext getParentContext()`; `Variables getVariables()`; `void setVariables(Variables vars)`; `boolean isLenient()`; `void setLenient(boolean lenient)`; `void setFactory(AbstractFactory factory)`; `AbstractFactory getFactory()`; `void setFunctions(Functions functions)`; `Functions getFunctions()` |
| `Pointer` | interface; `String asPath()`; `Object getValue()`; `void setValue(Object value)`; `Object getNode()`; `Object getRootNode()` |
| `Variables` | interface; `void declareVariable(String varName, Object value)`; `Object getVariable(String varName)`; `boolean isDeclaredVariable(String varName)`; `void undeclareVariable(String varName)` |
| `BasicVariables` | `BasicVariables()`; implements `Variables` |
| `AbstractFactory` | abstract class; `AbstractFactory()`; `boolean createObject(JXPathContext context, Pointer pointer, Object parent, String name, int index)` (base returns false); `boolean declareVariable(JXPathContext context, String varName)` (base returns false) |
| `CompiledExpression` | interface; `Object getValue(JXPathContext context)`; `Object getValue(JXPathContext context, Class requiredType)`; `void setValue(JXPathContext context, Object value)`; `Pointer getPointer(JXPathContext context, String xpath)`; `Iterator iterate(JXPathContext context)`; `Iterator<Pointer> iteratePointers(JXPathContext context)`; `Pointer createPath(JXPathContext context)`; `Pointer createPathAndSetValue(JXPathContext context, Object value)`; `void removePath(JXPathContext context)`; `void removeAll(JXPathContext context)` |
| `Functions` | interface; `Set<String> getUsedNamespaces()` |
| `ClassFunctions` | `ClassFunctions(Class functionClass, String namespace)`; implements `Functions` |
| `PackageFunctions` | `PackageFunctions(String classPrefix, String namespace)`; implements `Functions` |
| `FunctionLibrary` | `FunctionLibrary()`; `void addFunctions(Functions functions)`; `void removeFunctions(Functions functions)`; implements `Functions` |
| `JXPathException` | unchecked; base of the engine's error family; `JXPathException(String message)` |
| `JXPathNotFoundException` | strict-mode no-match reads; extends `JXPathException` |
| `JXPathInvalidSyntaxException` | unparseable expression text; extends `JXPathException` |
| `JXPathFunctionNotFoundException` | unresolvable function calls; extends `JXPathException` |
| `JXPathInvalidAccessException` | writes through unwritable locations; extends `JXPathException` |
| `JXPathAbstractFactoryException` | factory declined a creation step; extends `JXPathException` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `JXPathContext` | class | Evaluation context over one graph root; all queries and writes. |
| `Pointer` | interface | Canonical, live address of one graph location. |
| `Variables` | interface | Variable store contract. |
| `BasicVariables` | class | Default map-backed variable store. |
| `AbstractFactory` | class | Caller-supplied builder of missing graph structure. |
| `CompiledExpression` | interface | One parsed expression reusable across contexts. |
| `Functions` | interface | A set of named extension functions. |
| `ClassFunctions` | class | Static methods of one class under a namespace prefix. |
| `PackageFunctions` | class | Name-prefix-located functions; unprefixed method calls. |
| `FunctionLibrary` | class | Aggregates function sets by namespace. |
| `JXPathException` | exception | Engine error base. |
| `JXPathNotFoundException` | exception | No match in strict mode. |
| `JXPathInvalidSyntaxException` | exception | Unparseable expression. |
| `JXPathFunctionNotFoundException` | exception | Unresolvable function. |
| `JXPathInvalidAccessException` | exception | Write to an unwritable location. |
| `JXPathAbstractFactoryException` | exception | Factory declined creation. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library — including the JDK's DOM implementation under `org.w3c.dom` and `javax.xml.parsers` — is available; the target artifact's own declared dependencies resolve through Maven. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `commons-jxpath:commons-jxpath`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the documented behaviors through the public API: path queries and expression typing over bean, map, collection, DOM, and mixed graphs; canonical pointer paths and their round-trips; write, create, and remove operations including factory cooperation; variables and function sets; strict and lenient lookup; context chains and relative contexts; compiled-expression equivalence; and the declared error taxonomy. Tests construct their own graph fixtures (plain JavaBeans, standard collections, and DOM documents parsed with the JDK), query and mutate them through contexts, and observe returned values, canonical paths, mutations on the underlying objects, and raised exception types. Both single behaviors and multi-step scenarios across several views of the same graph are measured.
