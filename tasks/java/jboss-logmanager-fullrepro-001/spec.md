# JBoss Log Manager Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`org.jboss.logmanager` is a Java logging library that extends Java Util Logging with isolated logging contexts, named logger hierarchies, diagnostic-context snapshots, composable record filters, text and structured formatters, configurable handlers, and UTF-8 properties configuration. The installable Maven coordinate is `org.jboss.logmanager:jboss-logmanager`.

The central fact source is a logging context containing named logger configuration and records emitted through that hierarchy. Public projections expose the same facts as logger lookup and inheritance, filter decisions and record mutation, formatted text or structured data, handler queues and destinations, and properties-driven configuration.

## Non-Goals

- This specification does not require class-loader context selectors, global `LogManager` replacement, `System.LoggerFinder`, service-provider customization, or security-manager permission emulation.
- This specification does not require mutable configuration-resource graphs beyond applying a supplied `logging.properties` stream.
- This specification does not require color-terminal rendering, banner formatting, low-level format-step construction, or exact ANSI escape sequences.
- This specification does not require rotating, delayed, socket, syslog, TCP, UDP, TLS, or image-capable handlers.
- This specification does not require concrete error-manager throttling policies, exact diagnostic message text, exact `toString()` text, serialized byte compatibility, or private implementation layout.
- This specification does not define host names, process identifiers, timestamps, thread identifiers, source line numbers, or map iteration order as fixed values.

## Representative Workflows

The first workflow creates an isolated context, attaches a formatter and stream destination, records thread diagnostic data, and emits through a named logger.

```java
import java.io.ByteArrayOutputStream;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.jboss.logmanager.MDC;
import org.jboss.logmanager.NDC;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.handlers.OutputStreamHandler;

LogContext context = LogContext.create(true);
Logger logger = context.getLogger("service.checkout");
logger.setLevel(java.util.logging.Level.INFO);

ByteArrayOutputStream bytes = new ByteArrayOutputStream();
OutputStreamHandler handler = new OutputStreamHandler(
        bytes, new PatternFormatter("%p [%c] %X{requestId} %x %m%n"));
logger.addHandler(handler);

MDC.put("requestId", "r-17");
int depth = NDC.push("checkout");
logger.info("accepted");
handler.flush();
NDC.trimTo(depth - 1);
MDC.clear();
```

The emitted text reflects the record level, logger name, captured MDC/NDC values, formatted message, and line separator. Closing the handler releases its destination, and closing the context releases registered handlers and close resources.

The second workflow applies a supplied configuration stream, obtains the configured logger from the same context, and observes delivery to the declared file.

```java
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.Logger;
import org.jboss.logmanager.configuration.PropertyLogContextConfigurator;

String properties = """
        loggers=service.audit
        logger.service.audit.level=DEBUG
        logger.service.audit.handlers=FILE
        logger.service.audit.useParentHandlers=false
        handler.FILE=org.jboss.logmanager.handlers.FileHandler
        handler.FILE.level=DEBUG
        handler.FILE.formatter=TEXT
        handler.FILE.properties=fileName,autoFlush
        handler.FILE.fileName=target/audit.log
        handler.FILE.autoFlush=true
        formatter.TEXT=org.jboss.logmanager.formatters.PatternFormatter
        formatter.TEXT.properties=pattern
        formatter.TEXT.pattern=%p %c %m%n
        """;

LogContext context = LogContext.create(true);
new PropertyLogContextConfigurator().configure(
        context,
        new ByteArrayInputStream(properties.getBytes(StandardCharsets.UTF_8)));
Logger logger = context.getLogger("service.audit");
logger.fine("stored");
context.close();
```

The configured level accepts `FINE`/`DEBUG`, the named file handler receives the record without parent duplication, and the configured pattern determines the durable text.

## Logging Contexts and Named Logger Hierarchies

This section defines isolated logger trees and the inheritance rules that decide whether records reach configured handlers.

**Context creation and lookup.**

- A `LogContext` created by `create` must own a logger namespace isolated from every other created context.
- When `getLogger(name)` is called, the context must return the logger at `name`, creating the corresponding named hierarchy path when absent; repeated lookup in the same context returns the same logical logger.
- When `getLoggerIfExists(name)` is called for an absent node, the context must return `null`; after `getLogger(name)` creates that node, `getLoggerIfExists(name)` must return its logger.
- The `getLoggerNames` enumeration must contain the names of logger nodes that exist in the context.
- Each `Logger` returned by a context must return that context from `getLogContext`, and `getParent` must return the nearest named ancestor, with the empty-name root returning `null`.
- If `setParent` is called, then `Logger` must raise `SecurityException` because parentage is derived from the logger name hierarchy.

**Levels and loggability.**

- The library levels must expose names and numerical severities `FATAL=1100`, `ERROR=1000`, `WARN=900`, `INFO=800`, `DEBUG=500`, and `TRACE=400`.
- A new context must resolve the standard JUL levels and the library level names through `getLevelForName`.
- When `registerLevel(level, strong)` is called, the context must make that instance discoverable by its name; a later registration of the same name replaces the prior lookup result.
- When `unregisterLevel(level)` removes the currently registered instance, subsequent lookup by that otherwise unknown name must raise `IllegalArgumentException`.
- If `getLevelForName(name)` receives an unknown or `null` name, then it must raise `IllegalArgumentException`.
- When a logger has an explicit level, `getLevel` must return it and `getEffectiveLevel` must return its numerical value.
- While a logger level is `null`, `getEffectiveLevel` and `isLoggable` must use the nearest ancestor's effective level.
- When `setLevelName(name)` is called, the logger must resolve the name through its owning context and apply that level; an unknown name must raise `IllegalArgumentException`.

**Filters, handlers, and propagation.**

- A logger must store and return its direct filter through `setFilter` and `getFilter`.
- While `useParentFilters` is true, a record must satisfy the logger's filter and every applicable ancestor filter; while it is false, ancestor filters must not decide the logger's acceptance.
- The handler mutators must maintain an ordered snapshot: `addHandler` appends, `removeHandler` removes the matching handler, `setHandlers` replaces the snapshot, `getAndSetHandlers` returns the prior snapshot, `clearHandlers` returns and removes all handlers, and `compareAndSetHandlers` replaces only when the current sequence equals `expected`.
- Returned handler arrays must be independent copies whose modification does not alter logger state.
- If a handler array contains `null`, then `setHandlers`, `getAndSetHandlers`, or the replacement side of `compareAndSetHandlers` must raise `IllegalArgumentException`; `addHandler(null)` must raise `NullPointerException`.
- While `useParentHandlers` is true, an accepted record must be published to direct handlers and then ancestor handlers; while it is false, publication must stop before ancestor handlers.
- When a log method receives a level below the effective level, the logger must neither evaluate message suppliers nor publish a record.
- When a record passes the effective level and filters, the logger must set its logger name and publish it through the configured handler path.

**Attachments and lifecycle.**

- A new `Logger.AttachmentKey` must identify one attachment slot independently of every other key.
- When `attach(key, value)` stores a value, it must return the previous value or `null`; `getAttachment` must return the current value, and `detach` must return and remove it.
- When `attachIfAbsent(key, value)` sees no mapping, it must store the value and return `null`; when a mapping exists, it must preserve and return the existing value.
- Context attachments and root-logger attachments must project the same root attachment state.
- If `LogContext.attach(key, value)` receives a non-null `key` and a `null` `value`, then it must raise `IllegalArgumentException`.
- When `close` is called, a context must close its configured logger handlers and registered close handlers; repeated close-resource registration must preserve insertion order without duplicate resources.

## Diagnostic Context and Extended Records

This section defines thread diagnostic state and the stable record snapshot consumed by filters, formatters, queues, and asynchronous handlers.

**Mapped diagnostic context.**

- `MDC` must maintain a map local to the current thread.
- When `put` or `putObject` stores a key, it must return the previous mapping or `null`; `get` must return the string projection and `getObject` must return the object projection.
- When `remove` or `removeObject` removes a key, it must return the previous mapping or `null`.
- `copy` and `copyObject` must return independent maps whose later modification does not change the thread context.
- When `clear` is called, `isEmpty` must return true and lookups must return `null`.

**Nested diagnostic context.**

- `NDC` must maintain a stack local to the current thread.
- When `push(context)` is called, it must append the value and return the new depth.
- `getDepth` must return the current depth. When the stack contains entries, `get()` must join them from bottom to top with one period (`.`) between adjacent entries; when no entry exists, it must return the empty string. Indexed `get(n)` must return the entry counted from the bottom or `null` when absent.
- When `pop` is called on a nonempty stack, it must remove and return the top entry; on an empty stack it must return the empty string.
- When `trimTo(size)` is called, the stack must retain at most the bottom `size` entries; a negative size must produce an empty stack.
- When `clear` is called, the stack must become empty.

**Record construction and snapshots.**

- An `ExtLogRecord` constructor must capture the current NDC, thread name, host name, process name, and process identifier immediately, while MDC capture remains deferred until first MDC copy or lookup snapshot.
- A `null` constructor `formatStyle` must select `MESSAGE_FORMAT`.
- `wrap(null)` must return `null`; wrapping an existing `ExtLogRecord` must return the same instance; wrapping a plain `LogRecord` must return an extended view preserving its standard public fields.
- When `copyMdc` is called, the record must freeze an independent copy of the current thread MDC, and later thread-context changes must not alter record MDC values.
- When `copyAll` is called, the record must freeze MDC and caller/source information and repeated calls must leave the same snapshot.
- Record MDC mutators must first establish a record-local copy; `setMdc(sourceMap)` must ignore entries with `null` keys or values and convert non-string keys to strings.
- `getMdcCopy` must return an independent string-valued map, converting non-null object values through their string representation.
- `setMessage(message)` must select `MESSAGE_FORMAT`; `setMessage(message, style)` must select the supplied style or `MESSAGE_FORMAT` when style is `null`.
- `getFormattedMessage` and `ExtFormatter.formatMessage` must resolve a resource bundle key when present, then use `MessageFormat` for `MESSAGE_FORMAT`, `String.format` for `PRINTF`, and the raw message for `NO_FORMAT`; without parameters they must return the resolved message unchanged.
- Calling a source setter must disable deferred caller calculation for that source projection, and later getters must return the assigned value.
- `disableCallerCalculation` must preserve already calculated source values; otherwise it must expose unknown source values as `null` and line number `-1`.
- Public marker, thread, host, process, NDC, module, and long-thread-ID setters must update the corresponding getters.

## Filtering and Filter Expressions

This section defines composable record acceptance, record mutation, and the documented expression grammar used by configuration.

**Direct filters.**

- `AcceptAllFilter.getInstance().isLoggable(record)` must return true, and `DenyAllFilter.getInstance().isLoggable(record)` must return false.
- An `AllFilter` must evaluate constituent filters in order and stop at the first false result; an empty chain must return true.
- An `AnyFilter` must evaluate constituent filters in order and stop at the first true result; an empty chain must return false.
- If an iterator-backed `AllFilter` or `AnyFilter` receives a `null` constituent, then construction must raise `NullPointerException`.
- An `InvertFilter` must return the logical inverse of its target filter.
- A `LevelFilter` must return true exactly when the record's level equals one of its configured level objects.
- A `LevelRangeFilter` must compare numerical level values and honor `minInclusive` and `maxInclusive` independently.
- If a `LevelRangeFilter` receives a maximum numerical level below its minimum, then construction must raise `IllegalArgumentException`.
- When `LevelChangingFilter.isLoggable(record)` is called, it must set the record to `newLevel` and return true.
- A `RegexFilter` must search the record's formatted message for a matching substring rather than require a whole-string match.
- When `SubstituteFilter` is configured with `replaceAll=false`, it must replace the first match in the formatted message; when `replaceAll=true`, it must replace every match.
- After substitution, the filter must store the replacement as the record message, select `NO_FORMAT` for an `ExtLogRecord`, and return true.
- If a string constructor receives an invalid regular expression, then construction must raise `PatternSyntaxException`.

**Expression grammar.**

- `FilterExpressions.parse(logContext, expression)` must recognize `accept`, `deny`, `not(...)`, `all(...)`, `any(...)`, `levelChange(...)`, `levels(...)`, `levelRange(...)`, `match(...)`, `substitute(...)`, and `substituteAll(...)`.
- An empty expression must return `null`.
- `not` must accept one nested expression; `all` and `any` must accept comma-delimited nested expressions and preserve short-circuit order.
- `levelChange`, `levels`, and `levelRange` must resolve level names through the supplied `LogContext`.
- `levelRange` must interpret `[` and `]` as inclusive endpoints and `(` and `)` as exclusive endpoints.
- `match`, `substitute`, and `substituteAll` must accept double-quoted strings with escapes for backslash, quote, apostrophe, backspace, form feed, newline, carriage return, and tab.
- If the expression has an unknown operator, unknown level, malformed delimiter, missing argument, truncated string, or unsupported escape, then `parse` must raise `IllegalArgumentException`.

## Text and Structured Formatting

This section defines conversion of the same extended record into pattern text, JSON, or XML while retaining configurable field and exception policies.

**Extended and pattern formatting.**

- `ExtFormatter.format(LogRecord)` must wrap the supplied record as an `ExtLogRecord` and delegate to `format(ExtLogRecord)`.
- When `ExtFormatter.wrap(formatter, false)` receives an existing `ExtFormatter`, it must return that formatter; otherwise it must return an extended wrapper that delegates head, tail, and record formatting.
- A `PatternFormatter` constructed with a pattern must return that pattern from `getPattern` and apply it to subsequent records.
- When `setPattern(null)` is called, the formatter must emit an empty string for records; setting a later non-null pattern must replace the active conversion sequence.
- Pattern words must support `%d{pattern}` for record time, `%p` for level name, `%c` for logger name, `%c{n}` for the rightmost logger-name segments, `%t` for thread name, `%s` and `%m` for formatted message, `%e` for a thrown stack trace, `%X{key}` for one MDC value, `%x` for NDC, `%n` for the platform line separator, and `%%` for a literal percent sign.
- Pattern width and alignment modifiers must pad a rendered field to its minimum width, and a leading minus sign must left-align that field.
- If a pattern ends with an incomplete conversion, then construction or `setPattern` must raise `IllegalArgumentException`.

**Shared structured fields.**

- `JsonFormatter` and `XmlFormatter` must project timestamp, sequence, logger class name, logger name, level, formatted message, thread name, thread identifier, MDC, and NDC for each record.
- By default, every `StructuredFormatter.Key` must return and select the external name shown below; a key override must replace only the selected external name without changing its value.

  | `StructuredFormatter.Key` | Default external name |
  |---|---|
  | `TIMESTAMP` | `timestamp` |
  | `SEQUENCE` | `sequence` |
  | `LOGGER_CLASS_NAME` | `loggerClassName` |
  | `LOGGER_NAME` | `loggerName` |
  | `LEVEL` | `level` |
  | `MESSAGE`, `EXCEPTION_MESSAGE` | `message` |
  | `THREAD_NAME` | `threadName` |
  | `THREAD_ID` | `threadId` |
  | `MDC` | `mdc` |
  | `NDC` | `ndc` |
  | `HOST_NAME` | `hostName` |
  | `PROCESS_NAME` | `processName` |
  | `PROCESS_ID` | `processId` |
  | `RECORD` | `record` |
  | `SOURCE_CLASS_NAME` | `sourceClassName` |
  | `SOURCE_FILE_NAME` | `sourceFileName` |
  | `SOURCE_METHOD_NAME` | `sourceMethodName` |
  | `SOURCE_LINE_NUMBER` | `sourceLineNumber` |
  | `SOURCE_MODULE_NAME` | `sourceModuleName` |
  | `SOURCE_MODULE_VERSION` | `sourceModuleVersion` |
  | `EXCEPTION` | `exception` |
  | `EXCEPTION_CAUSED_BY` | `causedBy` |
  | `EXCEPTION_CIRCULAR_REFERENCE` | `circularReference` |
  | `EXCEPTION_TYPE` | `exceptionType` |
  | `EXCEPTION_FRAME` | `frame` |
  | `EXCEPTION_FRAME_CLASS` | `class` |
  | `EXCEPTION_FRAME_LINE` | `line` |
  | `EXCEPTION_FRAME_METHOD` | `method` |
  | `EXCEPTION_FRAMES` | `frames` |
  | `EXCEPTION_REFERENCE_ID` | `refId` |
  | `EXCEPTION_SUPPRESSED` | `suppressed` |
  | `STACK_TRACE` | `stackTrace` |
- Structured output must include host name and process name only when nonempty and process identifier only when nonnegative.
- The default record delimiter must be a single newline; when `setRecordDelimiter(null)` is called, formatting must append no delimiter.
- `setDateFormat(pattern)` must use a `DateTimeFormatter` pattern and preserve the current zone; a `null` pattern must restore ISO offset date-time formatting.
- `setZoneId(zoneId)` must apply the named zone to timestamp formatting, and `null` must select the system default zone.
- If a date pattern or zone identifier is invalid, then its setter must raise `IllegalArgumentException` or `DateTimeException`.
- When `setPrintDetails(true)` is active, structured output must include source class, file, method, line, module name, and module version; while false, those fields must be omitted.
- `setMetaData` must parse comma-separated `key=value` entries and merge them into each structured record; `null` must remove configured metadata.
- Key overrides supplied at construction must replace the corresponding default `StructuredFormatter.Key` names without changing their values.
- `setExceptionOutputType(null)` must select `DETAILED`; `DETAILED` must emit structured exception type, message, frames, causes, and suppressed exceptions, `FORMATTED` must emit printable stack-trace text, and `DETAILED_AND_FORMATTED` must emit both projections.

**JSON and XML projections.**

- `JsonFormatter` must emit one JSON object per record and preserve MDC and detailed exception structures as nested objects and arrays.
- While JSON pretty printing is false, the formatter must emit compact JSON; while true, it must emit whitespace-formatted JSON with equivalent data.
- `XmlFormatter` must emit one element named by the `RECORD` key per record, represent each scalar field as an element named by its structured key, represent each MDC entry as a child of the `MDC` element whose element name is that entry's map key, and represent repeated exception frames as repeated elements.
- `XmlFormatter.DEFAULT_NAMESPACE` must equal `urn:jboss:logmanager:formatter:1.0`.
- While `printNamespace` is true and `namespaceUri` is non-null, the record element must declare that URI as the default namespace; while false or while the URI is `null`, it must omit the namespace declaration.
- A default `XmlFormatter` must retain `DEFAULT_NAMESPACE` as its namespace URI, and constructing it with nonempty key overrides must default the namespace URI to `null`.

## Handler Delivery, Buffering, and Lifecycle

This section defines how accepted records are written, retained, delegated, drained, and closed across deterministic handler projections.

**Common handler policy.**

- An `ExtHandler` must publish only non-null records while enabled and while its level and filter accept the record.
- A plain `LogRecord` accepted by an `ExtHandler` must be wrapped as an `ExtLogRecord` before extended publication.
- Setting `enabled=false` must suppress publication without changing the configured level, filter, formatter, or children.
- A new `ExtHandler` must use level `ALL`, UTF-8 charset, auto-flush enabled, and close-children enabled.
- `setEncoding(null)` must restore UTF-8; an unsupported encoding name must raise `UnsupportedEncodingException`; `setCharset(null)` must raise `NullPointerException`.
- Setting auto-flush from false to true must flush immediately, and while true every successful physical write must be followed by a flush.
- Child-handler snapshots returned by `getHandlers`, `setHandlers`, and `clearHandlers` must be independent arrays.
- When `close` is called while close-children is true, every child handler must be closed; while false, children must remain open.
- If formatter, level, error manager, or a required child handler is `null`, then the corresponding setter must raise `NullPointerException` or `IllegalArgumentException`.

**Writer, stream, and file destinations.**

- A `WriterHandler` must apply its formatter, ignore an empty formatted result, write nonempty results in publication order, and flush according to auto-flush.
- When `setWriter` installs a new writer, the handler must write the formatter head to the new writer and write the formatter tail to, flush, and close the previous writer.
- When `setWriter(null)` is called, the handler must disable destination writes after closing the prior writer.
- An `OutputStreamHandler` must encode output with its current charset and own the installed stream; replacing its stream or writer must flush and close the prior destination.
- When the output-stream handler charset changes, subsequent bytes must use the new charset without replacing the underlying stream.
- A `FileHandler` constructed without a file must remain inactive until `setFile` or `setFileName` selects a destination.
- When a file destination is selected, the handler must create missing parent directories, overwrite by default, and append when `append` is true.
- When `setFile(null)` or `setFileName(null)` is called, the file handler must disable output and `getFile` must return `null`.
- If the file cannot be opened, then construction or destination replacement must raise `FileNotFoundException`.

**Bounded and asynchronous delegation.**

- A new `QueueHandler` must retain at most 10 accepted records; a positive constructor `limit` or `setLimit` must replace that bound.
- If a queue limit is less than one, then construction or `setLimit` must raise `IllegalArgumentException`.
- When the queue is full and another accepted record arrives, the handler must discard the oldest record and append the newest.
- `getQueue` must return an oldest-to-newest snapshot independent of future queue mutations.
- `getQueueAsStrings` must format the queue snapshot in oldest-to-newest order with the handler formatter.
- `replay` must publish every retained record in oldest-to-newest order to every current child handler.
- When `addHandler(handler, true)` is called, the queue handler must atomically attach the child, replay retained records in order, and then deliver subsequent records without a replay/live gap.
- A new `AsyncHandler` must use queue length 512 and overflow action `BLOCK`; an explicit positive queue length must be returned unchanged by `getQueueLength`.
- While overflow action is `BLOCK`, publication must wait for queue capacity; while it is `DISCARD`, publication must drop a record that does not fit without blocking.
- Before cross-thread delivery, the async handler must freeze MDC and must freeze caller data only when a formatter or child requires it.
- When `close` is called, the async handler must stop accepting new records, drain already queued records to child handlers, and close its children according to common close policy.
- If the async thread factory returns `null`, then construction must raise `IllegalArgumentException`; if `setOverflowAction(null)` is called, then it must raise `NullPointerException`.

## Properties Configuration

This section defines the UTF-8 property vocabulary that materializes logger, filter, formatter, and handler state in a supplied context.

**Configuration input and logger declarations.**

- When `PropertyLogContextConfigurator.configure(logContext, inputStream)` receives a non-null stream, it must read Java properties as UTF-8 and apply them to the supplied context; a `null` context must select the currently active context.
- If the supplied stream cannot be read, then configuration must raise `RuntimeException` with the I/O failure as its cause.
- The `loggers` property must declare the comma-delimited non-root logger names eligible for subsequent `logger.<name>.*` configuration; the empty-name root must use `logger.*` properties.
- `logger.<name>.level` must resolve a documented level name, with an unspecified named-logger level inheriting from its nearest configured ancestor.
- `logger.<name>.handlers` must attach the named configured handlers in declaration order.
- `logger.<name>.filter` must parse the documented filter expression, and `logger.<name>.useParentHandlers` must default to true when absent.
- If a logger references an undeclared handler, unknown level, or malformed filter expression, then configuration must raise `IllegalArgumentException` or `RuntimeException` rather than silently create a different setting.

**Formatter and handler declarations.**

- `formatter.<name>` and `handler.<name>` must name public implementation classes, and referenced names must be declared in the same properties input.
- `formatter.<name>.properties` and `handler.<name>.properties` must list comma-delimited JavaBean property names whose values come from `formatter.<name>.<property>` and `handler.<name>.<property>`.
- `formatter.<name>.constructorProperties` and `handler.<name>.constructorProperties` must list properties passed to a matching public constructor in that order.
- `handler.<name>.level`, `.encoding`, `.filter`, and `.formatter` must configure the corresponding public handler policy.
- Property conversion must support strings, booleans, integral numbers, character sets, levels, files, enums, and references to declared formatter or handler objects when the destination property type requires them.
- If a declared class is absent, a listed property has no compatible setter or constructor parameter, a value cannot be converted, or a named formatter/filter reference is absent, then configuration must raise `IllegalArgumentException` or `RuntimeException`.
- Applying a new configuration to a context must replace configured logger/handler relationships consistently and close resources displaced by the prior attached context configuration.

## State Model

The core state is an isolated named logger tree plus its level registry, logger configuration, attachments, diagnostic snapshots, configured formatter/handler graph, and external destinations. The public projections are:

1. Context lookup, logger enumeration, parent links, levels, filters, handlers, and attachments.
2. MDC/NDC thread state and the frozen diagnostic/source fields of each `ExtLogRecord`.
3. Direct filter results and mutations, including objects produced by expression parsing.
4. Pattern text, JSON objects, and XML elements derived from a record.
5. Stream bytes, file contents, retained queue snapshots, replay, and asynchronous child delivery.
6. The logger/formatter/handler graph created from a supplied properties stream.

While a record remains mutable in the caller thread, its public setters must update later filter and formatter projections. Once a queue or asynchronous boundary freezes the required fields, later thread-context changes must not alter that queued record.

## Error Semantics

| Condition | Required result |
|---|---|
| Unknown or `null` level name | If a level name is unknown or `null`, then `LogContext.getLevelForName` and `Logger.setLevelName` must raise `IllegalArgumentException`. |
| Explicit logger parent replacement | If explicit parent replacement is requested, then `Logger.setParent` must raise `SecurityException`. |
| `null` handler added or contained in a replacement array | If a required handler is `null`, then the logger or handler mutator must raise `NullPointerException` or `IllegalArgumentException`. |
| `LogContext.attach` receives a `null` value with a non-null key | If `LogContext.attach(key, value)` receives a non-null `key` and a `null` `value`, then it must raise `IllegalArgumentException`. |
| Reversed level range | If a level range is reversed, then `LevelRangeFilter` construction must raise `IllegalArgumentException`. |
| Invalid regular expression | If a regular expression is invalid, then the string filter constructor must raise `PatternSyntaxException`. |
| Malformed filter expression or unknown expression level | If a filter expression is malformed or names an unknown level, then `FilterExpressions.parse` must raise `IllegalArgumentException`. |
| Invalid date pattern or zone identifier | If a date pattern or zone identifier is invalid, then the structured formatter setter must raise `IllegalArgumentException` or `DateTimeException`. |
| Unsupported handler encoding | If a handler encoding is unsupported, then `setEncoding` must raise `UnsupportedEncodingException`. |
| `null` charset, formatter, level, error manager, or async overflow action | If a required handler policy value is `null`, then the relevant setter must raise `NullPointerException`. |
| Queue limit below one | If a queue limit is below one, then queue handler construction or `setLimit` must raise `IllegalArgumentException`. |
| Async thread factory returns `null` | If an async thread factory returns `null`, then async handler construction must raise `IllegalArgumentException`. |
| File destination cannot be opened | If a file destination cannot be opened, then file handler construction or destination replacement must raise `FileNotFoundException`. |
| Supplied properties stream cannot be read | If a supplied properties stream cannot be read, then configuration must raise `RuntimeException` retaining the I/O cause. |
| Invalid configured class, property, reference, or converted value | If a configured class, property, reference, or converted value is invalid, then configuration must raise `IllegalArgumentException` or `RuntimeException`. |

## Cross-View Invariants

1. A logger returned by `LogContext.getLogger(name)` must report that context and the same name-derived parent hierarchy visible through `getParent` and `getLoggerNames`.
2. A level assigned by `setLevelName` must be the instance resolved by the owning context, and its numerical value must determine both `getEffectiveLevel` and downstream publication.
3. A logger attachment placed on the empty-name root must be visible through the corresponding context attachment projection, and detaching it through either view must remove it from both.
4. MDC and NDC values present when a record is frozen must remain equal across the record getters, pattern `%X`/`%x` text, JSON/XML fields, queue snapshots, and asynchronous delivery.
5. A level-changing or substituting filter mutation accepted by a logger must be visible in every later formatter and handler projection of that same record.
6. The handler order visible through `getHandlers` must be the publication order for direct logger delivery and the replay order across each queued record.
7. A pattern formatter attached through properties configuration must produce the same text as a programmatically constructed formatter with the same pattern and record state.
8. Logger level, filter, handler, and parent-propagation values applied from properties must equal the values returned through the programmatic logger and handler APIs.
9. Structured key overrides, metadata, detail policy, time policy, delimiter, and exception policy must affect JSON and XML consistently while retaining their respective syntax.
10. Closing a context must make formatter tails, stream/file flushes, queued async drainage, handler-child closure, and registered close resources observe one coherent shutdown of that context.

## Public Interface

### Java Import Surface

```java
import org.jboss.logmanager.ExtFormatter;
import org.jboss.logmanager.ExtHandler;
import org.jboss.logmanager.ExtLogRecord;
import org.jboss.logmanager.Level;
import org.jboss.logmanager.LogContext;
import org.jboss.logmanager.LogContextConfigurator;
import org.jboss.logmanager.Logger;
import org.jboss.logmanager.MDC;
import org.jboss.logmanager.NDC;
import org.jboss.logmanager.configuration.PropertyLogContextConfigurator;
import org.jboss.logmanager.configuration.filters.FilterExpressions;
import org.jboss.logmanager.filters.AcceptAllFilter;
import org.jboss.logmanager.filters.AllFilter;
import org.jboss.logmanager.filters.AnyFilter;
import org.jboss.logmanager.filters.DenyAllFilter;
import org.jboss.logmanager.filters.InvertFilter;
import org.jboss.logmanager.filters.LevelChangingFilter;
import org.jboss.logmanager.filters.LevelFilter;
import org.jboss.logmanager.filters.LevelRangeFilter;
import org.jboss.logmanager.filters.RegexFilter;
import org.jboss.logmanager.filters.SubstituteFilter;
import org.jboss.logmanager.formatters.JsonFormatter;
import org.jboss.logmanager.formatters.PatternFormatter;
import org.jboss.logmanager.formatters.StructuredFormatter;
import org.jboss.logmanager.formatters.XmlFormatter;
import org.jboss.logmanager.handlers.AsyncHandler;
import org.jboss.logmanager.handlers.FileHandler;
import org.jboss.logmanager.handlers.OutputStreamHandler;
import org.jboss.logmanager.handlers.QueueHandler;
import org.jboss.logmanager.handlers.WriterHandler;
```

The scoped public members are:

| Public type | Public members in scope |
|---|---|
| `Level` | Constants `FATAL`, `ERROR`, `WARN`, `INFO`, `DEBUG`, `TRACE`. |
| `LogContext` | `create`, `getLogger`, `getLoggerIfExists`, `getLoggerNames`, `getLevelForName`, `registerLevel`, `unregisterLevel`, `getAttachment`, `attach`, `attachIfAbsent`, `detach`, `addCloseHandler`, `getCloseHandlers`, `setCloseHandlers`, `close`. |
| `Logger` | `getLogger`, filter/level/attachment/handler getters and mutators, parent-handler and parent-filter flags, `getParent`, `setParent`, `getLogContext`, JUL logging overloads, `logRaw`, resource-bundle access, and public `AttachmentKey` construction. |
| `ExtLogRecord` | Public constructors; `wrap`; copy controls; MDC/NDC, format-style, source, message, resource, thread, host, process, marker, module, and long-thread-ID accessors; `FormatStyle` constants `MESSAGE_FORMAT`, `PRINTF`, `NO_FORMAT`. |
| `MDC`, `NDC` | All public static map/stack operations described above. |
| `ExtFormatter` | Constructor, `wrap`, both `format` entry points, `formatMessage`, `isCallerCalculationRequired`. |
| Filter classes | Public constructors, singleton accessors where present, and `isLoggable`; `FilterExpressions.parse`. |
| `PatternFormatter` | Public constructors, `getPattern`, `setPattern`, `getColors`, `setColors`, inherited formatting operations. |
| `StructuredFormatter` | Structured policy getters/setters and formatting operation; all public `Key` and `ExceptionOutputType` enum constants; `Key.getKey`. |
| `JsonFormatter`, `XmlFormatter` | Public constructors, pretty-print settings, inherited structured settings; XML namespace constant and settings. |
| `ExtHandler` | Public publication, child-handler, auto-flush, enabled, close-child, lifecycle, formatter, filter, charset/encoding, error-manager, level, and caller-requirement members. |
| `WriterHandler`, `OutputStreamHandler`, `FileHandler` | Public constructors and destination/lifecycle members described above. |
| `QueueHandler` | Public constructors, publication, limit, queue snapshots, replay, and child attachment with replay. |
| `AsyncHandler` | Public constructors, queue-length and overflow accessors, `close`; `OverflowAction.BLOCK` and `DISCARD`. |
| `LogContextConfigurator`, `PropertyLogContextConfigurator` | `configure` and public concrete constructor. |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Level` | class | Supplies library-specific JUL-compatible severity constants. |
| `LogContext` | class | Owns one isolated named logger tree, level registry, attachments, and lifecycle. |
| `Logger` | class | Configures and emits through one named node in a context hierarchy. |
| `Logger.AttachmentKey` | class | Provides typed identity for logger and context attachments. |
| `ExtLogRecord` | class | Carries extended diagnostic, source, formatting, process, and marker data. |
| `ExtLogRecord.FormatStyle` | enum | Selects message, printf, or no parameter formatting. |
| `MDC` | class | Exposes the current thread's mapped diagnostic context. |
| `NDC` | class | Exposes the current thread's nested diagnostic stack. |
| `ExtFormatter` | abstract class | Converts standard or extended records with extended message semantics. |
| `AcceptAllFilter` | class | Accepts every record. |
| `DenyAllFilter` | class | Rejects every record. |
| `AllFilter` | class | Applies short-circuit conjunction over filters. |
| `AnyFilter` | class | Applies short-circuit disjunction over filters. |
| `InvertFilter` | class | Inverts another filter decision. |
| `LevelFilter` | class | Accepts configured level objects. |
| `LevelRangeFilter` | class | Accepts a numerical severity interval with independent endpoint inclusion. |
| `LevelChangingFilter` | class | Mutates record level and accepts the record. |
| `RegexFilter` | class | Searches formatted record messages with a regular expression. |
| `SubstituteFilter` | class | Replaces message matches and prevents a second parameter-format pass. |
| `FilterExpressions` | class | Parses the documented filter-expression language. |
| `PatternFormatter` | class | Renders extended records from percent conversion patterns. |
| `StructuredFormatter` | abstract class | Defines common structured fields and formatting policies. |
| `StructuredFormatter.Key` | enum | Names each overridable structured field and returns its default external name through `getKey`. |
| `StructuredFormatter.ExceptionOutputType` | enum | Selects detailed, formatted, or combined exception output. |
| `JsonFormatter` | class | Emits structured records as JSON objects. |
| `XmlFormatter` | class | Emits structured records as XML record elements. |
| `ExtHandler` | abstract class | Applies common acceptance, child delegation, encoding, flushing, and close policy. |
| `WriterHandler` | class | Owns a writer and writes formatter head, records, and tail. |
| `OutputStreamHandler` | class | Encodes formatted records into an owned output stream. |
| `FileHandler` | class | Projects formatted records into an overwrite or append file destination. |
| `QueueHandler` | class | Retains a bounded recent-record snapshot and replays it to children. |
| `AsyncHandler` | class | Moves accepted records across a bounded asynchronous queue to children. |
| `AsyncHandler.OverflowAction` | enum | Selects blocking or discarding behavior for a full async queue. |
| `LogContextConfigurator` | interface | Defines application of configuration to a logging context. |
| `PropertyLogContextConfigurator` | class | Materializes context state from a UTF-8 properties stream. |

### CLI Entry Points

There is no console script or standalone main-class entry point for this library. Programmatic use is through Java imports, Maven dependency resolution, and the optional JVM logging-manager system property.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. Maven builds execute from the repository root and must produce the coordinate `org.jboss.logmanager:jboss-logmanager` as a JAR. The local dependency cache provides `org.jboss.logging:jboss-logging:3.6.3.Final`, `org.jboss.modules:jboss-modules:2.3.0`, SmallRye Common `constraint`, `cpu`, `expression`, `net`, `os`, and `ref` modules at `2.19.0`, `jakarta.json:jakarta.json-api:2.1.3`, and `org.eclipse.parsson:parsson:1.1.9`; JUnit `6.1.3` is available to the assessment suite. The assessment environment provides the same runtime and cached artifact set.

The project must declare standard Maven metadata in a root `pom.xml`, compile with release 17, use the coordinate above, and resolve entirely from the preloaded cache.

## Appendix B: Assessment Notes

Assessment covers public symbol availability, isolated context and hierarchy behavior, level and attachment state, diagnostic snapshots, filter decisions and mutations, pattern/JSON/XML projections, handler destination and lifecycle behavior, bounded and asynchronous delivery, properties configuration, documented errors, and cross-view consistency. Atomic checks exercise individual rules; integration checks compose at least three projections of the same context or record. Assessment rewards observable behavioral coverage and does not depend on private field layout, internal helper names, exact error text, machine-specific identifiers, or undocumented extensions.
