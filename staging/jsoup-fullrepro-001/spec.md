# jsoup Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`jsoup` is a Java library for parsing real-world HTML into an in-memory document tree and working with that tree: querying it with CSS-style selectors, traversing and mutating nodes and attributes, extracting text, sanitizing untrusted markup against a tag/attribute safelist, and serializing the tree back to HTML or XML text under configurable output settings.

The library is organized around one core fact — the parsed `Document` tree of `Element`, `TextNode`, `Comment`, `DataNode`, `DocumentType`, and `XmlDeclaration` nodes — and several public projections of it: the serialized markup (`html`, `outerHtml`), the extracted text (`text`, `ownText`, `wholeText`), selector result lists (`Elements`), attribute views (`Attributes`, `absUrl`), and sanitized copies produced by a `Cleaner`. Two parsers build the same tree shape: an HTML parser that applies HTML normalization rules, and an XML parser that preserves the input structure literally.

## Non-Goals

- This specification does not define an HTTP client or any network fetching; parsing starts from strings supplied by the caller.
- This specification does not require interoperability with `org.w3c.dom`, XPath evaluation, or streaming parse events.
- This specification does not define form extraction or submission helpers.
- This specification does not define incremental re-parsing; every parse entry point builds a complete new tree.
- This specification does not define thread-safety guarantees for documents shared across threads.

## Representative Workflows

The first workflow parses an HTML fragment, queries it with selectors, and reads text and attributes out of the matched elements.

```java
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

Document doc = Jsoup.parse(
    "<div id=a class='c1 c2'><p>1</p><p title=t>2</p><span>3</span></div>"
    + "<div id=b><p>4</p></div>");
Elements ps = doc.select("#a p");          // two elements
String second = doc.select("p:eq(1)").text();          // "2"
Element withSpan = doc.selectFirst("div:has(span)");   // div#a
String titled = doc.select("p[title]").text();         // "2"
```

The second workflow mutates the tree and serializes the result. Appended markup is parsed in context; the serializer pretty-prints block elements one per line, indented one space per depth level by default.

```java
Document doc = Jsoup.parse("<div><p>One</p></div>");
Element div = doc.selectFirst("div");
div.appendElement("p").text("Two");
div.prependElement("p").text("Zero");
// div.html() is now:
// <p>Zero</p>
// <p>One</p>
// <p>Two</p>
```

The third workflow sanitizes untrusted input against a safelist. Tags and attributes not admitted by the safelist are dropped while their inner text is preserved, and `basic()` forces `rel="nofollow"` onto kept links.

```java
import org.jsoup.safety.Safelist;

String clean = Jsoup.clean(
    "<p><a href='https://x.com/' onclick='y'>go</a></p><script>bad</script>",
    Safelist.basic());
// "<p><a href=\"https://x.com/\" rel=\"nofollow\">go</a></p>"
```

## Parsing and Document Normalization

**Entry points.** `Jsoup.parse(html)` parses a complete HTML document; `Jsoup.parse(html, baseUri)` additionally records a base URI used for resolving relative URLs; `Jsoup.parse(html, baseUri, parser)` selects the parser implementation. `Jsoup.parseBodyFragment(html)` and `Jsoup.parseBodyFragment(html, baseUri)` parse body-level fragments: the fragment's nodes become the children of the document's `body`. `Document.createShell(baseUri)` returns an empty normalized document (`html` containing empty `head` and `body`).

**Normalization rules.** The HTML parser must produce a normalized document regardless of what the input omits:

- The tree always contains `html`, `head`, and `body` elements; content is placed in the section HTML rules assign it (a `title` element moves into `head`; body-level text and elements go into `body`).
- Tag names and attribute names are lowercased (`<TITLE>` becomes `title`, `CLASS=Foo` becomes `class="Foo"`); attribute values keep their case.
- Unclosed elements are closed where HTML requires it: `<ul><li>1<li>2</ul>` produces two complete `li` elements; a `table` acquires an implicit `tbody` around its rows.
- A leading `<!DOCTYPE html>` is preserved as a `DocumentType` node, the document's first child, serialized as `<!doctype html>`.
- `script` and `style` element content is not HTML-parsed; it is held as a `DataNode` and returned by `Element.data()`, not by `text()`.

**Document accessors.** `title()` returns the text of the `head`'s `title` element or the empty string; `title(text)` creates or updates that element. `head()` and `body()` return the respective elements. `createElement(tagName)` returns a new detached element owned by the document. `location()` returns the empty string for string-parsed documents. A `Document`'s `nodeName()` is `#document`; a text node's is `#text`.

**Base URIs.** The `baseUri` given at parse time propagates to every node (`Node.baseUri()`). `absUrl(attributeKey)` resolves the attribute's value against the base URI (`/path` against `https://example.com/dir/` gives `https://example.com/path`); it returns the empty string when no base URI is set and the value is relative. `attr("abs:key")` is equivalent to `absUrl("key")`.

## CSS Selector Engine

`Element.select(query)` evaluates a CSS-style query over the receiver's subtree and returns an `Elements` list in document order; `selectFirst(query)` returns the first match or null; `is(query)` reports whether the receiver itself matches. `Elements.select(query)` evaluates over every element in the list. The classic getters `getElementById(id)`, `getElementsByTag(name)`, and `getElementsByClass(name)` must agree with the equivalent queries `#id`, `tag`, and `.class`.

The query grammar must support at least:

- Simple selectors: `tag`, `#id`, `.class`, `*`.
- Attribute selectors: `[attr]` (present), `[^prefix]` (attribute name starts with prefix, e.g. `[^data-]`), `[attr=value]`, `[attr^=prefix]`, `[attr$=suffix]`, `[attr*=substring]`.
- Combinators: descendant (space), child `>`, immediately preceding sibling `+`, preceding sibling `~`, and the group comma `,`.
- Index pseudo-selectors on the matched list: `:lt(n)`, `:gt(n)`, `:eq(n)` (zero-based sibling index among matches of the preceding selector).
- Structural pseudo-selectors: `:first-child`, `:last-child`, `:nth-child(an+b)`, `:first-of-type`, `:only-child`.
- Content pseudo-selectors: `:has(subquery)`, `:not(subquery)`, `:contains(text)` (case-insensitive, whole subtree), `:containsOwn(text)` (own text only), `:matches(regex)` (subtree text matches the regular expression).

A query that cannot be parsed must raise `Selector.SelectorParseException`, a subclass of `IllegalStateException`, whose message names the offending query.

**Result lists.** `Elements` is a `java.util.ArrayList` of `Element` with aggregate views: `text()` joins the elements' texts with single spaces; `eachText()` returns the per-element texts; `attr(key)` returns the first present attribute value; `eachAttr(key)` collects per-element values; `html()` and `outerHtml()` join markup; `first()` and `last()` return boundary elements or null; `eq(index)` narrows to the element at an index; `not(query)` filters matches out. Mutators (`addClass`, `removeClass`, `attr(key, value)`, `remove()`) apply to every element in the list and must be observable through the owning document.

## DOM Traversal and Manipulation

**Traversal.** `children()` returns an element's child elements; `child(i)` returns the child element at a zero-based index; `childNodes()` and `childNodeSize()` cover all node types; `parent()` returns the parent element; `parents()` returns ancestors from nearest to root (`body` and `html` included); `siblingElements()` returns the other children of the parent; `elementSiblingIndex()` is the receiver's position among element siblings; `nextElementSibling()` and `previousElementSibling()` return adjacent element siblings or null. `Node.root()` returns the tree root (the document when attached), and `ownerDocument()` returns the containing `Document`. `cssSelector()` returns a unique selector for the element built from ids, classes, and `:nth-child` positions (for example `html > body > div > p:nth-child(2)`).

**Attributes and classes.** `attr(key)` returns the attribute value or the empty string; `attr(key, value)` sets it and returns the element for chaining; `hasAttr(key)` tests presence; `removeAttr(key)` deletes; `attributes()` returns the element's `Attributes` collection, iterable as `Attribute` entries in document order with `getKey()`/`getValue()`, and supporting `size()` and `hasKey(key)`. A boolean attribute (`checked`) has the empty string as its value, reports `hasAttr` true, and serializes without `="…"`. `id()` returns the `id` attribute or the empty string. `className()` returns the literal `class` attribute; `classNames()` returns the set of names; `hasClass(name)`, `addClass(name)`, `removeClass(name)`, and `toggleClass(name)` manage individual names while preserving the order of the remaining ones. `dataset()` returns a map view of `data-*` attributes keyed by the name after the prefix.

**Mutation.** `append(html)` and `prepend(html)` parse the markup and add the produced nodes at the end/beginning of the element's children; `appendElement(tag)` and `prependElement(tag)` create and attach one element and return it; `appendText(text)` appends a text node; `appendChild(node)` attaches an existing node. `before(html)` and `after(html)` insert siblings around the receiver. `wrap(html)` wraps the receiver in the supplied markup; `unwrap()` removes the receiver but keeps its children in place. `remove()` deletes the node from its parent; `empty()` removes all children; `replaceWith(node)` swaps the receiver for another node. `text(text)` replaces the children with one text node (markup characters in the text are escaped on output); `html(html)` replaces the children with parsed markup. `tagName(newName)` renames the element. `new Element(tag)` and `new TextNode(text)` construct detached nodes; a detached element's `parent()` is null. `clone()` produces a deep copy whose subsequent mutation must not affect the original.

## Text Extraction and Entities

`text()` returns the element's whole subtree text with whitespace normalized: runs of whitespace collapse to single spaces, and boundaries between block-level elements contribute a single separating space. `ownText()` applies the same normalization to the element's own text nodes only. `wholeText()` returns the subtree text with original whitespace preserved. `hasText()` reports whether any non-blank text exists. `Document.text()` spans head and body (title text included). Text inside `pre` keeps its whitespace in serialized output.

**Entities.** On output, markup-significant characters in text are escaped (`&` as `&amp;`, `<` as `&lt;`, `>` as `&gt;` where required). `Entities.escape(text)` escapes a string with the default settings (`< > & " '` become `&lt; &gt; &amp; &quot; &apos;`); `Entities.unescape(text)` resolves named and numeric references (`&lt;p&gt; &amp;amp; &eacute;` becomes `<p> &amp; é`).

The escape repertoire is governed by `Entities.EscapeMode` together with the output charset:

- `base` (default): the base named-entity set. A character outside the output charset is emitted as a named entity when the base set has one (`é` as `&eacute;` under an ASCII charset) and as a numeric reference otherwise (`™` as `&#x2122;`).
- `extended`: the full named-entity set (`™` becomes `&trade;` under an ASCII charset).
- `xhtml`: minimal XML entities only; a non-breaking space is emitted numerically as `&#xa0;` rather than `&nbsp;`.

Under the default UTF-8 charset, characters representable in the charset are emitted literally (`é` stays `é`), while a non-breaking space is still emitted as `&nbsp;` in the default mode.

## Serialization and Output Settings

`Document.outputSettings()` returns the document's mutable `Document.OutputSettings`, which govern every serialization (`html()`, `outerHtml()`, `toString()`):

- `prettyPrint(boolean)` — on by default. Pretty printing places each block element on its own line, indented by one indent unit per depth level; inline elements (`span`, `a`, `b`, …) stay on their parent's line. With `prettyPrint(false)` the tree serializes with no added whitespace: `<html><head></head><body><p>One</p></body></html>`.
- `indentAmount(int)` — the indent unit width in spaces; the default is 1.
- `outline(boolean)` — off by default; when on, every element is treated as block-level for layout.
- `syntax(Document.OutputSettings.Syntax)` — `html` (default) or `xml`. HTML syntax renders void elements bare (`<img src="a">`, `<br>`); XML syntax renders them self-closed (`<img src="a" />`, `<br />`).
- `escapeMode(Entities.EscapeMode)` and `charset(String)` — select the escape repertoire as described above.

A document's `outerHtml()` must equal its `html()`. Serialization must be a fixpoint: re-parsing a document's `html()` with the same parser and serializing again yields the same string.

## XML Parsing Mode

`Parser.xmlParser()` selects XML rules for `Jsoup.parse(html, baseUri, parser)`; `Parser.htmlParser()` names the default. The XML parser must:

- Preserve tag-name and attribute-name case (`<Camel attr='A'>` stays `Camel`).
- Insert no implicit structure: no `html`/`head`/`body` wrapper; unclosed elements close at the end of input without HTML-specific rules.
- Represent an XML declaration `<?xml version="1.0"?>` as an `XmlDeclaration` node with `nodeName()` `#declaration`, serialized back in place.
- Serialize empty elements self-closed (`<self />`), and documents parsed as XML serialize with XML syntax by default.

## Sanitization

A `Cleaner` is constructed over a `Safelist` and offers two operations on body fragments: `clean(document)` returns a new document whose body contains only admitted markup, and `isValid(document)` reports whether the input body contains only admitted markup already (no document mutation). `Jsoup.clean(html, safelist)` must equal the composition `new Cleaner(safelist).clean(Jsoup.parseBodyFragment(html)).body().html()`; `Jsoup.clean(html, baseUri, safelist)` resolves admitted URL attributes against the base URI first. `Jsoup.isValid(html, safelist)` is the string-level counterpart of `Cleaner.isValid`.

Cleaning must drop disallowed elements while keeping their inner text, drop disallowed attributes from kept elements, and enforce URL protocol rules on admitted URL attributes (a relative `src` on an image is removed under the stock image-bearing safelists unless relative links are explicitly preserved via `preserveRelativeLinks(true)`; with a base URI present, relative admitted URLs are resolved absolute).

Stock safelists, from narrowest to widest:

- `Safelist.none()` — text only; all tags dropped.
- `Safelist.simpleText()` — simple inline formatting (`b`, `em`, `i`, `strong`, `u`).
- `Safelist.basic()` — common body text tags plus links; kept `a[href]` elements acquire `rel="nofollow"`, and `href` admits only `ftp`, `http`, `https`, `mailto`.
- `Safelist.basicWithImages()` — `basic()` plus `img` with dimension/`src`/`alt`/`title` attributes; `src` admits only `http`, `https`.
- `Safelist.relaxed()` — a full body-text set including tables, headings, and lists (still no scripts or frames), without enforcing `rel="nofollow"`.

Safelists are customizable and chainable: `addTags(tags…)`, `addAttributes(tag, keys…)`, `removeTags(tags…)`, `preserveRelativeLinks(flag)`.

## State Model

The core state is the mutable node tree rooted at a `Document`: elements with ordered child nodes and ordered attribute collections, plus the document's `OutputSettings`. Public projections of that one state are: serialized markup (`html`, `outerHtml`, `toString`); extracted text (`text`, `ownText`, `wholeText`, `data`); selector results (`select`, `selectFirst`, the `getElementsBy*` getters); attribute views (`attr`, `attributes`, `absUrl`, `dataset`, class queries); structural views (`children`, `parents`, sibling accessors, `cssSelector`); and sanitized copies through `Cleaner.clean`.

- Every mutation through one API must be immediately visible through every projection: after `Elements.addClass`, each element's own `className()` reflects the addition and the serialized markup carries it.
- Reading projections must not mutate the tree: `text()`, `select(...)`, and `html()` may be called repeatedly with identical results.
- `clone()` decouples state: mutations on the copy never appear in the original, and vice versa.
- `Cleaner.clean` returns a new document; the dirty input document is not modified.

## Error Semantics

| Condition | Required result |
|---|---|
| Selector query that cannot be parsed (unknown pseudo-selector, dangling token) | `select`/`selectFirst`/`is` must raise `Selector.SelectorParseException` (a subclass of `IllegalStateException`). |
| Null query string, null attribute key, or null input HTML where a value is required | Must raise `IllegalArgumentException` or `NullPointerException`. |
| Empty string where a non-empty selector, attribute key, or wrap markup is required | Must raise `IllegalArgumentException`. |
| `child(index)` outside the range of child elements | Must raise `IndexOutOfBoundsException`. |
| Absent attribute read through `attr(key)` | Must return the empty string, not null and not an exception. |
| `selectFirst` with no match | Must return null. |

Exception messages are informative only; their exact wording is not part of this contract, except that a `SelectorParseException` message must contain the offending query text.

## Cross-View Invariants

1. `Document.outerHtml()` equals `Document.html()`, and re-parsing that string with the same parser and serializing again reproduces it exactly (serialization fixpoint).
2. `getElementById("x")`, `getElementsByTag("t")`, and `getElementsByClass("c")` must return the same elements as `select("#x")`, `select("t")`, and `select(".c")` respectively.
3. `Jsoup.clean(html, safelist)` must equal `new Cleaner(safelist).clean(Jsoup.parseBodyFragment(html)).body().html()`, and `Jsoup.isValid(html, safelist)` must agree with `Cleaner.isValid` on the parsed fragment.
4. A bulk operation on an `Elements` list must leave every member element in the same state as the equivalent per-element calls, observable both through element accessors and through the owning document's serialized markup.
5. `element.text()` must equal the whitespace-normalized reading of the text nodes reachable in its subtree; `wholeText()` preserves exactly the original characters of those text nodes.
6. For any element in a document, `document.selectFirst(element.cssSelector())` must return that same element.
7. `attr("abs:key")` must equal `absUrl("key")` for every element and attribute key.

## Public Interface

### Import Surface

```java
import org.jsoup.Jsoup;
import org.jsoup.nodes.Attribute;
import org.jsoup.nodes.Attributes;
import org.jsoup.nodes.Comment;
import org.jsoup.nodes.DataNode;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.DocumentType;
import org.jsoup.nodes.Element;
import org.jsoup.nodes.Entities;
import org.jsoup.nodes.Node;
import org.jsoup.nodes.TextNode;
import org.jsoup.nodes.XmlDeclaration;
import org.jsoup.parser.Parser;
import org.jsoup.safety.Cleaner;
import org.jsoup.safety.Safelist;
import org.jsoup.select.Elements;
import org.jsoup.select.Selector;
```

### Public Members

| Type | Public members in scope |
|---|---|
| `Jsoup` | static `parse(String)`, `parse(String, String)`, `parse(String, String, Parser)`, `parseBodyFragment(String)`, `parseBodyFragment(String, String)`, `clean(String, Safelist)`, `clean(String, String, Safelist)`, `isValid(String, Safelist)` |
| `Document` | static `createShell`; `title()`, `title(String)`, `head`, `body`, `createElement`, `location`, `outputSettings`, `nodeName`, `text`, `html`, `outerHtml`, `clone`; nested `OutputSettings` |
| `Document.OutputSettings` | `prettyPrint(boolean)`, `prettyPrint()`, `indentAmount(int)`, `indentAmount()`, `outline(boolean)`, `outline()`, `syntax(Syntax)`, `syntax()`, `escapeMode(Entities.EscapeMode)`, `escapeMode()`, `charset(String)`, `charset()`; nested enum `Syntax` with `html`, `xml` |
| `Element` | constructor `Element(String)`; `tagName()`, `tagName(String)`, `id`, `className`, `classNames`, `hasClass`, `addClass`, `removeClass`, `toggleClass`, `attr(String)`, `attr(String, String)`, `hasAttr`, `removeAttr`, `attributes`, `absUrl`, `baseUri`, `dataset`, `select`, `selectFirst`, `is`, `getElementById`, `getElementsByTag`, `getElementsByClass`, `children`, `child`, `childNodes`, `childNodeSize`, `childNode`, `parent`, `parents`, `hasParent`, `siblingElements`, `elementSiblingIndex`, `nextElementSibling`, `previousElementSibling`, `text()`, `text(String)`, `ownText`, `wholeText`, `hasText`, `data`, `html()`, `html(String)`, `outerHtml`, `append`, `prepend`, `appendText`, `appendElement`, `prependElement`, `appendChild`, `before(String)`, `after(String)`, `wrap`, `unwrap`, `empty`, `remove`, `replaceWith`, `clone`, `cssSelector`, `root`, `ownerDocument` |
| `Node` | `nodeName`, `outerHtml`, `remove`, `baseUri`, `childNode`, `childNodes`, `childNodeSize`, `parent`, `root`, `ownerDocument`, `absUrl`, `attr` |
| `TextNode` | constructor `TextNode(String)`; `text()`, `nodeName` |
| `Comment` | node type for `<!-- … -->` content; `nodeName` |
| `DataNode` | node type for `script`/`style` content |
| `DocumentType` | node type for doctypes; `nodeName` |
| `XmlDeclaration` | node type for `<?…?>` declarations; `nodeName` |
| `Attribute` | `getKey`, `getValue` |
| `Attributes` | `size`, `hasKey`, `get`, iterable over `Attribute` |
| `Entities` | static `escape(String)`, `unescape(String)`; nested enum `EscapeMode` with `xhtml`, `base`, `extended` |
| `Parser` | static `htmlParser()`, `xmlParser()` |
| `Elements` | extends `java.util.ArrayList<Element>`; `text`, `eachText`, `html`, `outerHtml`, `attr(String)`, `attr(String, String)`, `eachAttr`, `first`, `last`, `eq`, `not`, `select`, `addClass`, `removeClass`, `remove` |
| `Selector` | nested `SelectorParseException` (extends `IllegalStateException`) |
| `Cleaner` | constructor `Cleaner(Safelist)`; `clean(Document)`, `isValid(Document)` |
| `Safelist` | static `none()`, `simpleText()`, `basic()`, `basicWithImages()`, `relaxed()`; `addTags`, `addAttributes`, `removeTags`, `preserveRelativeLinks` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Jsoup` | class | Static entry points: parse documents and fragments, clean and validate untrusted HTML. |
| `Document` | class | Root of a parsed tree; owns the output settings and document-level accessors. |
| `Document.OutputSettings` | class | Serialization configuration: pretty-printing, indent, outline, syntax, escaping, charset. |
| `Element` | class | One markup element: attributes, classes, traversal, selection, mutation, text, serialization. |
| `Node` | class | Base of all tree nodes. |
| `TextNode` | class | A run of character data. |
| `Comment` | class | A comment node. |
| `DataNode` | class | Unparsed content of `script`/`style`. |
| `DocumentType` | class | A doctype node. |
| `XmlDeclaration` | class | An XML declaration node. |
| `Attribute` | class | One key/value attribute entry. |
| `Attributes` | class | Ordered attribute collection of an element. |
| `Entities` | class | Entity escaping and unescaping; escape-mode repertoires. |
| `Parser` | class | Parser selection: HTML rules or literal XML rules. |
| `Elements` | class | Document-ordered element result list with aggregate and bulk operations. |
| `Selector` | class | Query evaluation; declares the query-parse failure exception. |
| `Cleaner` | class | Applies a safelist to body fragments; validates already-clean input. |
| `Safelist` | class | Tag/attribute/protocol admission policy with stock configurations. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The Java standard library is available; no third-party runtime library beyond the target artifact is guaranteed to the implementation. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `org.jsoup:jsoup`. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the public parsing, selection, traversal, mutation, extraction, sanitization, and serialization surfaces. Tests compare serialized markup strings, extracted text, selector result contents and order, attribute views, exception classes, and cross-view consistency between projections of one tree; they do not require internal tokenizer or tree-builder classes, private fields, or exact exception message text beyond the documented query-name requirement. Assessment outcomes reflect the proportion of independently passing public behavior cases, with integration cases checking that complete parse–query–mutate–serialize and clean workflows keep every projection consistent.
