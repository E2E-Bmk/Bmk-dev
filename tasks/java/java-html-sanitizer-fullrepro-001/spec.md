# Java HTML Sanitizer Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`owasp-java-html-sanitizer` is a Java library that transforms untrusted HTML fragments into normalized HTML accepted by an explicitly composed policy. It exposes reusable policy factories, custom element and attribute policies, a streaming event pipeline, safe rendering, and change notifications over the same sanitization decisions.

The installable Maven coordinate is `com.googlecode.owasp-java-html-sanitizer:owasp-java-html-sanitizer`. Programmatic APIs are in the exported `org.owasp.html` package.

## Non-Goals

- This specification does not require a boolean HTML-validity classifier or a promise that unchanged input was safe.
- This specification does not require browser execution, DOM construction, network retrieval, or an external service.
- This specification does not define package-private lexer, token, CSS-token, string, vector, generated-table, or policy-joiner APIs.
- This specification does not require public behavior for the `org.owasp.html.examples` or `org.owasp.shim` packages.
- This specification does not define exact diagnostic message text, object text representations, internal maps, or internal algorithms.

## Representative Workflows

### Compose prepackaged policies

```java
import org.owasp.html.PolicyFactory;
import org.owasp.html.Sanitizers;

PolicyFactory policy = Sanitizers.FORMATTING.and(Sanitizers.LINKS);
String safeHtml = policy.sanitize(untrustedHtml);
```

The example combines independent grants and sanitizes one fragment to a string. The sections below define composition, URL filtering, normalization, and rejection behavior.

### Build a custom policy with telemetry

```java
import org.owasp.html.HtmlChangeListener;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.PolicyFactory;

PolicyFactory policy = new HtmlPolicyBuilder()
    .allowElements("a", "p")
    .allowUrlProtocols("https")
    .allowAttributes("href").onElements("a")
    .requireRelNofollowOnLinks()
    .toFactory();

String safeHtml = policy.sanitize(input, new HtmlChangeListener<String>() {
  public void discardedTag(String context, String name) { }
  public void discardedAttributes(
      String context, String name, String... attributes) { }
}, "profile-body");
```

The example builds a reusable policy, restricts link destinations, and associates rejection notifications with caller context.

### Stream sanitized events

```java
import java.util.List;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.HtmlStreamEventReceiver;
import org.owasp.html.HtmlStreamEventReceiverWrapper;

HtmlStreamEventReceiver sink = obtainSink();
HtmlStreamEventReceiverWrapper observingSink =
    new HtmlStreamEventReceiverWrapper(sink) {
      @Override public void text(String text) {
        recordText(text);
        super.text(text);
      }
    };
new HtmlPolicyBuilder().allowElements("p").build(observingSink);
```

The example uses the same policy decisions through an event receiver instead of the string convenience path.

## Policy Construction and Composition

Policy construction defines the allowlist, compiles it into reusable factories, and combines independent grants.

**Default and element rules.**

- The `HtmlPolicyBuilder` constructor must create a builder that denies every element and attribute until an allow operation grants it.
- When `allowElements` receives element names, the builder must canonicalize the names and grant those elements.
- When the `allowElements` overload receives an `ElementPolicy`, the builder must apply that policy after attribute policies and must drop an element when the policy returns `null`.
- When an `ElementPolicy` returns a non-null name, the sanitizer must emit the returned element name with the policy-mutated alternating attribute list.
- When `disallowElements` follows an earlier grant for the same element, the builder must revoke that grant.
- When `allowCommonInlineFormattingElements` is called, the builder must grant the documented common inline formatting family.
- When `allowCommonBlockElements` is called, the builder must grant paragraphs, divisions, headings, lists, list items, and block quotations.
- When `allowTextIn` names an element, the compiled policy must retain text in that element.
- When `disallowTextIn` names an element, the compiled policy must drop text in that element even when the element itself is granted.
- The `DEFAULT_SKIP_IF_EMPTY` constant must contain `a`, `font`, `img`, `input`, and `span`.
- When an element in `DEFAULT_SKIP_IF_EMPTY` loses every attribute, the default policy must drop that otherwise granted element.
- When `allowWithoutAttributes` names an element, the policy must retain that granted element when it has no surviving attributes.
- When `disallowWithoutAttributes` names an element, the policy must drop that granted element when it has no surviving attributes.

**Compilation and composition.**

- When `build` receives an `HtmlStreamEventReceiver`, the builder must return an `HtmlSanitizer.Policy` that sends only approved events to that receiver.
- When the telemetry overload of `build` receives a listener and context, the returned policy must send rejection notifications with that context.
- When `toFactory` is called, the builder must return a reusable `PolicyFactory` reflecting all preceding configuration calls.
- The `PolicyFactory.apply` method must create a distinct policy backed by the supplied receiver.
- When the telemetry overload of `PolicyFactory.apply` receives a listener and context, the created policy must report rejected tags and attributes with that context.
- When `PolicyFactory.and` combines factories, the result must grant the union of independently granted elements and attributes.
- When both factories define policies for the same granted element or attribute, the combined factory must apply both policies in order and must reject when either rejects.
- The `AttributePolicy.Util.join` and `ElementPolicy.Util.join` methods must apply non-null component policies in argument order and must stop at the first `null` result.
- The `IDENTITY_ATTRIBUTE_POLICY` and `IDENTITY_ELEMENT_POLICY` constants must return their input value or element name unchanged.
- The `REJECT_ALL_ATTRIBUTE_POLICY` and `REJECT_ALL_ELEMENT_POLICY` constants must return `null` for every input.

**Parameter vocabulary.**

- The `HtmlPolicyBuilder` configuration methods must use `elementNames`, `policy`, `attributeNames`, `linkValues`, `protocols`, `whitelist`, `newStyleUrlPolicy`, and `pp` for the inputs described above.
- The policy creation methods must use `out`, `listener`, and `context`; `PolicyFactory.sanitize` must use `html`, `listener`, and `context`; and `PolicyFactory.and` must use `f` for the other factory.

**Policy misuse boundaries.**

- If an element or attribute name argument is `null`, then the builder must raise a runtime exception instead of creating an unnamed rule.
- If a required receiver, policy, processor, schema, predicate, or custom policy argument is `null`, then the receiving API must raise a runtime exception instead of silently bypassing filtering.

## Attribute, URL, Link, and Style Rules

Attribute rules bind value filters to element scopes and layer mandatory URL and style guards over custom code.

**Attribute scopes and matching.**

- When `allowAttributes` receives attribute names, it must return an `AttributeBuilder` for those canonicalized names.
- When `AttributeBuilder.globally` is called, its attributes must be eligible on every granted element.
- When `AttributeBuilder.onElements` is called, its attributes must be eligible only on the named granted elements.
- If neither `globally` nor `onElements` is called, then an `AttributeBuilder` must not change the compiled policy.
- When `disallowAttributes` is scoped globally or to elements, the compiled policy must reject those attributes in that scope.
- When `matching` receives an `AttributePolicy`, the builder must chain it after earlier matchers and must pass each transformed value to the next matcher.
- When `matching` receives a regular-expression `Pattern`, the builder must retain only values matched in full by that pattern.
- When `matching` receives a `Predicate`, the builder must retain only values for which the predicate returns `true`.
- When `matching` receives allowed strings with `ignoreCase` false, the builder must use exact membership.
- When `matching` receives allowed strings with `ignoreCase` true, the builder must use case-insensitive membership.
- The `AttributePolicy.apply` method must receive canonical lower-case element and attribute names plus an entity-decoded unquoted value, and it must return a replacement value or `null` to reject the attribute.
- The `ElementPolicy.apply` method must receive a canonical lower-case element name and a mutable alternating attribute-name/value list.

**URL policy.**

- When `allowUrlProtocols` receives protocol names, the builder must add their lower-case forms to the set accepted by guarded URL attributes.
- When `disallowUrlProtocols` receives protocol names, the builder must remove their lower-case forms from that set.
- When `allowStandardUrlProtocols` is called, the builder must allow `http`, `https`, and `mailto`.
- The `FilterUrlByProtocolAttributePolicy` constructor must treat its `protocols` values as lower-case protocol names without trailing colons.
- When `FilterUrlByProtocolAttributePolicy.apply` receives a same-origin relative URL, it must return a normalized URL regardless of the configured protocol set.
- When `FilterUrlByProtocolAttributePolicy.apply` receives a URL with a scheme outside the configured set, it must return `null`.
- When `FilterUrlByProtocolAttributePolicy.apply` receives a protocol-relative URL, it must return a non-null value only when both `http` and `https` are configured.
- When a URL survives protocol filtering, the URL policy must trim HTML spaces and percent-encode control characters, parentheses, braces, and colon-like characters that would make scheme interpretation ambiguous.
- When a custom attribute policy is attached to a guarded URL attribute, the mandatory protocol guard must still run and must not be weakened by the custom policy.

**Link relations and style.**

- The `DEFAULT_RELS_ON_TARGETTED_LINKS` constant must contain `noopener` and `noreferrer`.
- When a retained link has a `target` attribute, the policy must add every default targeted-link relation except values selected by `skipRelsOnLinks`.
- When `requireRelNofollowOnLinks` is configured, the policy must add `nofollow` to retained links.
- When `requireRelsOnLinks` receives relation values, the policy must add those values to retained links without duplicating existing relation tokens.
- When `skipRelsOnLinks` receives relation values, the policy must suppress matching default or previously required relation values.
- When `allowStyling` is called without a schema, the builder must sanitize `style` values using `CssSchema.DEFAULT`.
- When `allowStyling` receives a schema, the builder must retain only declarations whose properties and value tokens that schema permits.
- When `allowUrlsInStyles` receives an attribute policy, CSS URLs that pass the configured protocol guard must also pass that policy.
- If styling has not been granted, then a `style` attribute must be rejected even when a caller applies an identity attribute policy to it.
- If style URL handling has not been granted, then URL-bearing CSS values must be rejected instead of being emitted unchanged.
- When `CssSchema.withProperties` receives documented built-in property names, it must return a schema containing exactly those properties.
- If `CssSchema.withProperties` receives an unknown property name, then it must raise `IllegalArgumentException`.
- When `CssSchema.union` receives schemas with compatible definitions, it must return a schema whose `allowedProperties` is their union.
- If `CssSchema.union` finds incompatible definitions for the same property name, then it must raise `IllegalArgumentException`.
- The `CssSchema.DEFAULT` constant must represent the built-in safe property set, and `allowedProperties` must return an immutable set.

**Parameter vocabulary.**

- The `AttributePolicy.apply` method must use `elementName`, `attributeName`, and `value`; the `ElementPolicy.apply` method must use `elementName` and `attrs`; and the join utilities must use `policies`.
- The CSS and URL APIs must use `propertyNames`, `cssSchemas`, `protocols`, `elementName`, `attributeName`, and `value` for the inputs described above.

## Sanitization and Normalized Output

Sanitization parses a fragment into canonical events, applies policy decisions, balances structure, and renders a context-safe HTML string or stream.

**String sanitization.**

- When `PolicyFactory.sanitize` receives `null`, it must return the empty string.
- When `PolicyFactory.sanitize` receives a fragment, it must return normalized HTML containing only policy-approved text, elements, and attributes.
- When the telemetry overload of `PolicyFactory.sanitize` receives a listener and context, it must return the same sanitized projection while reporting rejections through the listener.
- When `HtmlSanitizer.sanitize` receives `null`, it must process an empty document rather than raise `NullPointerException`.
- When `HtmlSanitizer.sanitize` processes a fragment, it must call `openDocument` before content events and `closeDocument` after them.
- When parsing tag or attribute names, the sanitizer must pass canonical lower-case non-namespaced names to the policy.
- When parsing text or attribute values, the sanitizer must decode HTML character references before policy callbacks.
- When parsing a valueless attribute, the sanitizer must supply that canonical attribute name as its value.
- When parsing comments, declarations, processing instructions, or unrecognized tag-body tokens, the sanitizer must omit them from policy events.
- When input tags are malformed or misnested, the sanitizer must emit a balanced event stream subject to the configured nesting limit.
- When the nesting depth exceeds the sanitizer limit, the sanitizer must omit deeper structural events instead of exhausting the call stack.

**Encoding helpers and output normalization.**

- When `Encoding.decodeHtml` receives HTML text, it must decode character references and remove code units that are not valid XML characters.
- When the `inAttribute` overload flag is true, `Encoding.decodeHtml` must apply attribute-context character-reference rules.
- When `Encoding.encodeRcdataOnto` receives plain text and an `Appendable`, it must append RCDATA-safe text without closing the surrounding title or textarea context.
- When the renderer emits ordinary text, it must escape tag-boundary characters and defang consecutive client-template opening braces.
- When the renderer emits attribute values, it must quote them, escape boundary characters, and normalize backtick-bearing values so reparsing does not create a new attribute.
- When the renderer emits a void element, it must produce a self-closing-compatible start tag and must not require a matching end event.

**Parameter vocabulary.**

- The `HtmlSanitizer.sanitize` overloads must use `html`, `policy`, and `preprocessor`, while the public encoding helpers must use `s`, `inAttribute`, `plainText`, and `output`.

## Event Processing and Rendering

The event APIs expose sanitization as a lifecycle-delimited stream and support wrappers, processors, balancing, and rendering sinks.

**Receiver lifecycle.**

- The `HtmlStreamEventReceiver` methods must represent one ordered stream of `openDocument`, tag or text events, and `closeDocument`.
- The `openTag` method must receive an element name and an even-length list alternating attribute names and values.
- The `HtmlStreamEventReceiverWrapper` constructor must retain an underlying receiver, and its event methods must delegate unchanged unless a subclass overrides them.
- When `HtmlStreamEventReceiverWrapper.close` is called and the underlying receiver implements `AutoCloseable`, the wrapper must close it.
- When `HtmlStreamEventProcessor.wrap` is called, it must return a receiver that ultimately forwards its processed events to the supplied sink.
- The `HtmlStreamEventProcessor.Processors.IDENTITY` constant must return its supplied sink unchanged.
- When `Processors.compose` receives processors `g` then `f`, the result must wrap a sink with `f` inside `g` so events traverse both processors in composition order.
- When `withPreprocessor` is configured, its processor must receive parsed events before tag balancing and policy filtering, so every inserted event must still pass through the policy.
- When `withPostprocessor` is configured, its processor must receive approved events after policy filtering and before the final sink.

**Balancing.**

- The `TagBalancingHtmlStreamEventReceiver` constructor must forward a stream to its underlying receiver after inserting required HTML open or close events.
- When `closeDocument` is called on the balancer, it must close every still-open recognized element before forwarding `closeDocument`.
- When a new recognized tag conflicts with currently open tags, the balancer must close or resume elements according to HTML containment rules.
- When `setNestingLimit` lowers the limit below the current open depth, it must raise `IllegalStateException`.
- When the configured nesting limit is reached, the balancer must suppress deeper emitted structure while continuing to accept the input stream.
- The `isInterElementWhitespace` method must return `true` only when every character is HTML inter-element whitespace.

**Rendering.**

- When `HtmlStreamRenderer.create` receives an `Appendable`, an I/O handler, and a bad-HTML handler, it must return a renderer that writes normalized HTML to that appendable and routes each problem to the corresponding handler.
- When the `StringBuilder` overload of `HtmlStreamRenderer.create` is used, the renderer must propagate impossible I/O failures and must send structurally invalid event reports to the supplied bad-HTML handler.
- When `openDocument` is called on a closed renderer, it must mark the document open.
- If `openDocument` is called while the renderer is open, then it must raise `IllegalStateException`.
- When `closeDocument` is called on an open renderer, it must finish pending literal content, flush a `Flushable` output, and mark the document closed.
- If `closeDocument`, `openTag`, `closeTag`, or `text` is called while the renderer is closed, then it must raise `IllegalStateException`.
- The `isDocumentOpen` method must return whether `openDocument` has occurred without a subsequent `closeDocument`.
- When a renderer created over a closeable output is closed through its returned closeable interface, it must close the underlying output.
- When event content has an invalid HTML name or impossible literal-text boundary, the renderer must call the bad-HTML handler and must not emit the invalid content.
- When output append or flush raises `IOException`, the renderer must pass that exception to the I/O handler.
- The `Handler.DO_NOTHING` constant must ignore every handled value.
- When `Handler.PROPAGATE` handles a runtime exception, it must rethrow that exception.
- When `Handler.PROPAGATE` handles a non-runtime throwable, it must raise `AssertionError` with that throwable as its cause.

**Parameter vocabulary.**

- The receiver event methods must use `elementName`, `attrs`, and `text`, and the processor method must use `sink`.
- The renderer factories must use `output`, `ioExHandler`, and `badHtmlHandler`, while balancing configuration must use `underlying` and `limit`.

## Rejection Telemetry

Telemetry projects policy rejection decisions without treating silence as proof that the input was safe.

**Listener callbacks.**

- When a policy drops a tag, the `HtmlChangeListener.discardedTag` method must receive the caller context and canonical element name.
- When a policy drops attributes but retains their containing tag, the `HtmlChangeListener.discardedAttributes` method must receive the context, canonical tag name, and discarded attribute names.
- When a whole tag is dropped, the listener must receive the tag callback instead of a redundant attribute callback for that tag.
- When sanitization produces no listener callback, callers must still use only the sanitized output as trusted HTML.

**Reporter wiring.**

- The `HtmlChangeReporter` constructor must bind a renderer, listener, and context into paired input and output channels.
- When `setPolicy` associates a policy created over `getWrappedRenderer`, `getWrappedPolicy` must return an input policy that compares pre-policy and post-policy events.
- The `getWrappedRenderer` method must return the receiver that the filtering policy uses as its output.
- The `getWrappedPolicy` method must return the policy that `HtmlSanitizer.sanitize` uses as its input.

**Parameter vocabulary.**

- The telemetry APIs must use `renderer`, `listener`, `context`, `policy`, `elementName`, `tagName`, and `attributeNames` for the inputs described above.

## State Model

The core state is an immutable compiled allow policy plus transient per-document stream state. The public projections are the sanitized string, approved receiver events, renderer output, listener notifications, and composed-policy results.

- A new `HtmlPolicyBuilder` must start in a deny-all configuration and must accumulate explicit configuration until compilation.
- A `PolicyFactory` must preserve a compiled configuration across multiple `sanitize` or `apply` calls without sharing per-document open-tag state.
- A created `HtmlSanitizer.Policy` must own one document stream lifecycle and one output receiver projection.
- A `HtmlStreamRenderer` must expose only closed or open document states through `isDocumentOpen`.
- A `TagBalancingHtmlStreamEventReceiver` must track open elements only for the current document and must clear that state on `closeDocument`.
- A `HtmlChangeReporter` must correlate one pre-policy stream with one post-policy stream and one caller context.

## Error Semantics

| Condition | Required result |
|---|---|
| Required object argument is `null` | If a required policy, receiver, processor, schema, predicate, or handler argument is `null`, then the receiving operation must raise a runtime exception. |
| Unknown built-in CSS property | If `CssSchema.withProperties` receives an unknown built-in property name, then the method must raise `IllegalArgumentException`. |
| Conflicting CSS definitions | If `CssSchema.union` receives conflicting definitions for one property name, then the method must raise `IllegalArgumentException`. |
| Nesting limit below current depth | If `TagBalancingHtmlStreamEventReceiver.setNestingLimit` receives a limit below the current depth, then the method must raise `IllegalStateException`. |
| Invalid renderer lifecycle transition | If a renderer lifecycle method is called in the wrong open or closed state, then the method must raise `IllegalStateException`. |
| Structurally invalid render event | If the renderer receives structurally invalid HTML events, then the renderer must invoke the bad-HTML handler and must omit the invalid content. |
| Output failure | If an output append or flush raises `IOException`, then the renderer must invoke the I/O handler with the exception. |
| Checked throwable propagation | If `Handler.PROPAGATE` receives a checked throwable, then the handler must raise `AssertionError` with the throwable as its cause. |
| Custom policy rejection | If a custom attribute or element policy returns `null`, then the sanitizer must reject that attribute or element without treating rejection as an exceptional failure. |
| Null HTML convenience input | If `PolicyFactory.sanitize` receives `null` HTML, then the method must return the empty string. |

## Cross-View Invariants

1. A grant configured through `HtmlPolicyBuilder` must agree with the elements and attributes visible in both `PolicyFactory.sanitize` output and events from `PolicyFactory.apply`.
2. A rejection visible as an omitted output construct must agree with `HtmlChangeListener` tag or attribute notifications when a listener is present.
3. A factory produced by `PolicyFactory.and` must preserve every non-overlapping grant from either input while enforcing both value policies on overlaps.
4. A preprocessor-inserted event must appear in output only when the compiled policy grants it, while a postprocessor-inserted event must flow directly to the final sink.
5. The document lifecycle observed by a custom receiver must agree with `HtmlStreamRenderer.isDocumentOpen` transitions when that renderer is the receiver.
6. A balanced stream emitted by `HtmlSanitizer.sanitize` must agree with the explicit balancing projection produced by `TagBalancingHtmlStreamEventReceiver` for the same event sequence.
7. URL acceptance in sanitized string output must agree with direct `FilterUrlByProtocolAttributePolicy.apply` results under the same configured protocol set.
8. CSS properties retained in style output must be a subset of `CssSchema.allowedProperties` for the schema supplied to `allowStyling`.
9. Calling `PolicyFactory.sanitize` repeatedly with the same input and policy must return the same string and must not retain stream state from an earlier call.

## Public Interface

### Import Surface

```java
import org.owasp.html.AttributePolicy;
import org.owasp.html.CssSchema;
import org.owasp.html.Encoding;
import org.owasp.html.ElementPolicy;
import org.owasp.html.FilterUrlByProtocolAttributePolicy;
import org.owasp.html.Handler;
import org.owasp.html.HtmlChangeListener;
import org.owasp.html.HtmlChangeReporter;
import org.owasp.html.HtmlPolicyBuilder;
import org.owasp.html.HtmlSanitizer;
import org.owasp.html.HtmlStreamEventProcessor;
import org.owasp.html.HtmlStreamEventReceiver;
import org.owasp.html.HtmlStreamEventReceiverWrapper;
import org.owasp.html.HtmlStreamRenderer;
import org.owasp.html.PolicyFactory;
import org.owasp.html.Sanitizers;
import org.owasp.html.TagBalancingHtmlStreamEventReceiver;
```

```java
import org.owasp.html.AttributePolicy.Util;
import org.owasp.html.HtmlPolicyBuilder.AttributeBuilder;
import org.owasp.html.HtmlSanitizer.Policy;
import org.owasp.html.HtmlStreamEventProcessor.Processors;
```

```java
import org.owasp.html.ElementPolicy.Util;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `AttributePolicy` | interface | Filters or transforms one decoded attribute value. |
| `AttributePolicy.apply` | method | Returns a replacement value or rejects the attribute. |
| `AttributePolicy.Util` | class | Composes attribute policies. |
| `AttributePolicy.Util.join` | method | Joins policies in order with early rejection. |
| `AttributePolicy.IDENTITY_ATTRIBUTE_POLICY` | constant | Accepts an attribute value unchanged. |
| `AttributePolicy.REJECT_ALL_ATTRIBUTE_POLICY` | constant | Rejects every attribute value. |
| `CssSchema` | class | Defines safe CSS properties and value-token grammars. |
| `CssSchema.withProperties` | method | Creates a schema from built-in property names. |
| `CssSchema.union` | method | Combines compatible schemas. |
| `CssSchema.allowedProperties` | method | Returns the immutable allowed property set. |
| `CssSchema.DEFAULT` | constant | Provides the built-in safe schema. |
| `Encoding` | class | Exposes public HTML entity decoding and RCDATA encoding helpers. |
| `Encoding.decodeHtml` | method | Decodes HTML text with text or attribute context rules. |
| `Encoding.encodeRcdataOnto` | method | Appends text safe for RCDATA content. |
| `ElementPolicy` | interface | Filters, renames, or augments one element. |
| `ElementPolicy.apply` | method | Returns a replacement element name or rejects the element. |
| `ElementPolicy.Util` | class | Composes element policies. |
| `ElementPolicy.Util.join` | method | Joins policies in order with early rejection. |
| `ElementPolicy.IDENTITY_ELEMENT_POLICY` | constant | Accepts an element unchanged. |
| `ElementPolicy.REJECT_ALL_ELEMENT_POLICY` | constant | Rejects every element. |
| `FilterUrlByProtocolAttributePolicy` | class | Filters URL attributes by scheme and normalizes accepted URLs. |
| `FilterUrlByProtocolAttributePolicy.FilterUrlByProtocolAttributePolicy` | constructor | Creates a filter from allowed lower-case protocols. |
| `FilterUrlByProtocolAttributePolicy.apply` | method | Accepts, normalizes, or rejects a URL value. |
| `Handler` | interface | Receives a rendering problem. |
| `Handler.handle` | method | Handles one problem value. |
| `Handler.DO_NOTHING` | constant | Ignores problems. |
| `Handler.PROPAGATE` | constant | Converts handled throwables into raised failures. |
| `HtmlChangeListener` | interface | Receives dropped-tag and dropped-attribute notifications. |
| `HtmlChangeListener.discardedTag` | method | Reports one discarded tag with context. |
| `HtmlChangeListener.discardedAttributes` | method | Reports discarded attributes on a retained tag. |
| `HtmlChangeReporter` | class | Correlates input and output streams to produce notifications. |
| `HtmlChangeReporter.HtmlChangeReporter` | constructor | Binds a renderer, listener, and context. |
| `HtmlChangeReporter.setPolicy` | method | Associates the filtering policy. |
| `HtmlChangeReporter.getWrappedRenderer` | method | Returns the output-side receiver. |
| `HtmlChangeReporter.getWrappedPolicy` | method | Returns the input-side policy. |
| `HtmlPolicyBuilder` | class | Builds custom allow policies. |
| `HtmlPolicyBuilder.HtmlPolicyBuilder` | constructor | Creates a deny-all builder. |
| `HtmlPolicyBuilder.DEFAULT_SKIP_IF_EMPTY` | constant | Names elements dropped by default after all attributes disappear. |
| `HtmlPolicyBuilder.DEFAULT_RELS_ON_TARGETTED_LINKS` | constant | Names default relations for targeted links. |
| `HtmlPolicyBuilder.allowElements` | method | Grants elements with identity or custom element policy behavior. |
| `HtmlPolicyBuilder.disallowElements` | method | Revokes element grants. |
| `HtmlPolicyBuilder.allowCommonInlineFormattingElements` | method | Grants the common inline formatting family. |
| `HtmlPolicyBuilder.allowCommonBlockElements` | method | Grants the common block family. |
| `HtmlPolicyBuilder.allowTextIn` | method | Grants text in named elements. |
| `HtmlPolicyBuilder.disallowTextIn` | method | Rejects text in named elements. |
| `HtmlPolicyBuilder.allowWithoutAttributes` | method | Retains named granted elements after all attributes disappear. |
| `HtmlPolicyBuilder.disallowWithoutAttributes` | method | Drops named granted elements after all attributes disappear. |
| `HtmlPolicyBuilder.allowAttributes` | method | Starts an attribute-grant builder. |
| `HtmlPolicyBuilder.disallowAttributes` | method | Starts an attribute-rejection builder. |
| `HtmlPolicyBuilder.requireRelNofollowOnLinks` | method | Requires the `nofollow` link relation. |
| `HtmlPolicyBuilder.requireRelsOnLinks` | method | Requires caller-selected link relations. |
| `HtmlPolicyBuilder.skipRelsOnLinks` | method | Suppresses selected required relations. |
| `HtmlPolicyBuilder.allowUrlProtocols` | method | Adds allowed URL protocols. |
| `HtmlPolicyBuilder.disallowUrlProtocols` | method | Removes allowed URL protocols. |
| `HtmlPolicyBuilder.allowStandardUrlProtocols` | method | Grants HTTP, HTTPS, and mail links. |
| `HtmlPolicyBuilder.allowStyling` | method | Grants sanitized style attributes under a schema. |
| `HtmlPolicyBuilder.allowUrlsInStyles` | method | Adds a policy for URLs in CSS values. |
| `HtmlPolicyBuilder.withPreprocessor` | method | Adds a pre-policy event processor. |
| `HtmlPolicyBuilder.withPostprocessor` | method | Adds a post-policy event processor. |
| `HtmlPolicyBuilder.build` | method | Builds a one-receiver policy with optional telemetry. |
| `HtmlPolicyBuilder.toFactory` | method | Compiles a reusable factory. |
| `HtmlPolicyBuilder.AttributeBuilder` | class | Binds matchers and scopes to selected attributes. |
| `HtmlPolicyBuilder.AttributeBuilder.matching` | method | Chains a custom, pattern, predicate, or membership matcher. |
| `HtmlPolicyBuilder.AttributeBuilder.globally` | method | Applies selected attributes to every granted element. |
| `HtmlPolicyBuilder.AttributeBuilder.onElements` | method | Applies selected attributes to named granted elements. |
| `HtmlSanitizer` | class | Parses HTML and dispatches balanced events through a policy. |
| `HtmlSanitizer.sanitize` | method | Sanitizes with an optional preprocessor. |
| `HtmlSanitizer.Policy` | interface | Receives parsed events and enforces policy decisions. |
| `HtmlSanitizer.Policy.openDocument` | method | Begins one policy document stream. |
| `HtmlSanitizer.Policy.closeDocument` | method | Ends one policy document stream. |
| `HtmlSanitizer.Policy.openTag` | method | Receives a canonical start tag and decoded attributes. |
| `HtmlSanitizer.Policy.closeTag` | method | Receives a canonical end tag. |
| `HtmlSanitizer.Policy.text` | method | Receives decoded text. |
| `HtmlStreamEventProcessor` | interface | Wraps an event sink with stream processing. |
| `HtmlStreamEventProcessor.wrap` | method | Returns the processed receiver. |
| `HtmlStreamEventProcessor.Processors` | class | Provides processor composition utilities. |
| `HtmlStreamEventProcessor.Processors.IDENTITY` | constant | Leaves a sink unchanged. |
| `HtmlStreamEventProcessor.Processors.compose` | method | Composes two processors. |
| `HtmlStreamEventReceiver` | interface | Receives lifecycle, tag, and text events. |
| `HtmlStreamEventReceiver.openDocument` | method | Begins an event document. |
| `HtmlStreamEventReceiver.closeDocument` | method | Ends an event document. |
| `HtmlStreamEventReceiver.openTag` | method | Receives a start tag with alternating attributes. |
| `HtmlStreamEventReceiver.closeTag` | method | Receives an end tag. |
| `HtmlStreamEventReceiver.text` | method | Receives a text node. |
| `HtmlStreamEventReceiverWrapper` | class | Delegates event methods to an underlying receiver. |
| `HtmlStreamEventReceiverWrapper.HtmlStreamEventReceiverWrapper` | constructor | Creates a delegating wrapper. |
| `HtmlStreamEventReceiverWrapper.openDocument` | method | Delegates document opening. |
| `HtmlStreamEventReceiverWrapper.closeDocument` | method | Delegates document closing. |
| `HtmlStreamEventReceiverWrapper.openTag` | method | Delegates start tags. |
| `HtmlStreamEventReceiverWrapper.closeTag` | method | Delegates end tags. |
| `HtmlStreamEventReceiverWrapper.text` | method | Delegates text. |
| `HtmlStreamEventReceiverWrapper.close` | method | Closes an auto-closeable underlying receiver. |
| `HtmlStreamRenderer` | class | Renders normalized event streams to an appendable. |
| `HtmlStreamRenderer.create` | method | Creates a renderer with problem handlers. |
| `HtmlStreamRenderer.openDocument` | method | Opens the renderer lifecycle. |
| `HtmlStreamRenderer.closeDocument` | method | Closes and flushes the renderer lifecycle. |
| `HtmlStreamRenderer.isDocumentOpen` | method | Reports renderer lifecycle state. |
| `HtmlStreamRenderer.openTag` | method | Renders a normalized start tag. |
| `HtmlStreamRenderer.closeTag` | method | Renders a normalized end tag. |
| `HtmlStreamRenderer.text` | method | Renders context-escaped text. |
| `PolicyFactory` | class | Reuses and composes compiled policies. |
| `PolicyFactory.apply` | method | Creates a stream policy with optional telemetry. |
| `PolicyFactory.sanitize` | method | Sanitizes to a string with optional telemetry. |
| `PolicyFactory.and` | method | Composes two policy factories. |
| `Sanitizers` | class | Provides prepackaged reusable policies. |
| `Sanitizers.FORMATTING` | constant | Grants common inline formatting. |
| `Sanitizers.BLOCKS` | constant | Grants common block elements. |
| `Sanitizers.STYLES` | constant | Grants safe style declarations. |
| `Sanitizers.LINKS` | constant | Grants safe links with standard protocols and relations. |
| `Sanitizers.TABLES` | constant | Grants common table structure and attributes. |
| `Sanitizers.IMAGES` | constant | Grants HTTP, HTTPS, and relative images with selected attributes. |
| `TagBalancingHtmlStreamEventReceiver` | class | Repairs event structure before forwarding it. |
| `TagBalancingHtmlStreamEventReceiver.TagBalancingHtmlStreamEventReceiver` | constructor | Creates a balancing wrapper. |
| `TagBalancingHtmlStreamEventReceiver.setNestingLimit` | method | Sets maximum emitted nesting depth. |
| `TagBalancingHtmlStreamEventReceiver.openDocument` | method | Begins forwarding a document. |
| `TagBalancingHtmlStreamEventReceiver.closeDocument` | method | Closes open tags and ends the document. |
| `TagBalancingHtmlStreamEventReceiver.openTag` | method | Opens or repairs structure for a start tag. |
| `TagBalancingHtmlStreamEventReceiver.closeTag` | method | Closes matching in-scope structure. |
| `TagBalancingHtmlStreamEventReceiver.text` | method | Forwards text after preparing valid containment. |
| `TagBalancingHtmlStreamEventReceiver.isInterElementWhitespace` | method | Classifies HTML inter-element whitespace. |

### CLI Entry Points

There is no console script for this package. `java -jar` execution is not supported. Programmatic use is through Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. Maven and the JDK are preinstalled, and the assessment environment provides the same toolchain. No third-party runtime library is preinstalled or importable beyond the JDK; compile-only annotation classes and Maven plugins required by the build are supplied through the offline Maven cache. The target library itself is not preinstalled.

The project must declare standard Maven metadata in a root `pom.xml`. The produced main artifact must use group ID `com.googlecode.owasp-java-html-sanitizer` and artifact ID `owasp-java-html-sanitizer`, and every declared dependency or plugin must resolve without network access.

## Appendix B: Assessment Notes

Assessment exercises only the public Java interfaces listed above. Checks cover policy construction, element and attribute decisions, URL and CSS guards, factory composition, normalized string output, event ordering, balancing, rendering lifecycle, preprocessing and postprocessing order, telemetry, reusable state, and failure semantics. Checks use local strings, receivers, appendables, and listeners rather than browsers, network access, or private package structures.
