# Tinylog Implementation Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`tinylog-impl` is a Java logging implementation that turns immutable configuration and issued log-entry facts into formatted console output, structured JSON, durable files, and rolling file sets. The implementation is loaded behind the companion `tinylog-api` interfaces and coordinates severity selection, tags, thread context, formatting, throwable transformation, writer lifecycle, and rollover policy state.

The installable artifact has Maven coordinate `org.tinylog:tinylog-impl:2.8-SNAPSHOT` and Java module name `org.tinylog.impl`. Its runtime caller contract uses the separately supplied `org.tinylog:tinylog-api:2.8-SNAPSHOT` artifact.

## Non-Goals

- This specification does not require Android logcat behavior.
- This specification does not require JDBC schemas, database reconnection, or syslog transport behavior.
- This specification does not require cross-process shared-file locking or race-sensitive filesystem behavior.
- This specification does not define raw byte-writer decorators, socket transports, private helpers, or internal matrix layouts.
- This specification does not define exact diagnostic text, implementation stack traces, or object representation strings.
- This specification does not require wall-clock-fragile assertions for asynchronous scheduling or date-boundary timing.

## Representative Workflows

### Configure, write, and close a file

```java
Map<String, String> values = new LinkedHashMap<>();
values.put("writer", "file");
values.put("writer.file", "logs/application.log");
values.put("writer.format", "{level}|{message}");
values.put("level", "info");
Configuration.replace(values);
Logger.debug("not selected");
Logger.info("ready");
ProviderRegistry.getLoggingProvider().shutdown();
```

When this workflow runs in a fresh process, the pipeline must create parent directories, omit the `DEBUG` entry, write the formatted `INFO` entry, and close the file writer before shutdown returns.

### Change the dynamic rolling path

```java
Map<String, String> values = new LinkedHashMap<>();
values.put("writer", "rolling file");
values.put("writer.file", "logs/{dynamic}-{count}.log");
values.put("writer.format", "{message}");
values.put("writer.policies", "dynamic");
Configuration.replace(values);
DynamicSegment.setText("blue");
Logger.info("first");
DynamicSegment.setText("green");
DynamicPolicy.setReset();
Logger.info("second");
ProviderRegistry.getLoggingProvider().shutdown();
```

When `DynamicSegment.setText()` changes the active text and `DynamicPolicy.setReset()` is called, the next rolling entry must start a new path while earlier entries remain in the files selected before the reset.

## Configuration Resolution and Provider Activation

Configuration resolution establishes one immutable provider snapshot so that selection and output remain consistent for the lifetime of the provider.

**Sources and precedence.** When multiple standard resource files are present, configuration resolution must prefer `tinylog-dev.properties`, then `tinylog-test.properties`, then `tinylog.properties`. Where `tinylog.configuration` names a location, configuration resolution must load that resource or filesystem path. Where a system property uses `tinylog.` followed by a configuration key, its value must override the file value. Where `Configuration.set()` or `Configuration.replace()` supplies a key before first access, its unprefixed value must become active. When configuration is first read, a logger is created, or an entry is issued, the configuration must become immutable. If a mutation is attempted after the freeze, then the call must raise `UnsupportedOperationException`.

**Value expansion.** Where a value contains `${name}` or `#{key}`, the resolver must substitute the matching environment variable or Java system property. Where `${name:fallback}` or `#{key:fallback}` names an absent value, the resolver must substitute `fallback`.

**Writer discovery.** When no writer root exists, `TinylogLoggingProvider` must instantiate the runtime default writer. Where several roots such as `writer1` and `writerFile` exist, the provider must instantiate each root and pass its child properties to the selected `Writer` constructor. The passed map must contain the root key as `ID` and the effective global `writingthread` value as `writingthread`. If a writer service is unavailable, then provider construction must report the failure and exclude that writer.

**Severity and tags.** The severity order must be `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, followed by `OFF`. When `level` is absent, the global threshold must be `TRACE`. Where `level@package.or.Class` entries exist, the provider must use the most specific matching class-or-parent-package threshold. Where a writer has `level`, that threshold must restrict the writer independently. Where a writer has no `tag`, it must receive tagged and untagged entries. Where `tag=-`, the writer must receive only untagged entries. Where `tag` is a comma-separated list, the writer must receive only listed tags. Where a tag item has `@level`, the writer must apply that tag-specific threshold.

**Provider queries and lifecycle.** `TinylogLoggingProvider` must provide a no-argument constructor, `getContextProvider()`, both `getMinimumLevel()` forms, both `isEnabled()` forms, both `log()` forms, `shutdown()`, and all three `getWriters()` forms. At the name-based Java boundary used by callers, `className` and `tag` are `String` values, `level` is the companion `Level`, and `isEnabled()` returns a boolean decision. The corresponding `log()` form additionally receives a nullable `Throwable` named `exception`, a companion `MessageFormatter` named `formatter`, an `Object` named `message`, and trailing `Object... arguments`, and returns no value. The tag-and-level `getWriters()` form returns a `Collection<Writer>`, while `shutdown()` returns no value and retains its declared interruption failure. When `isEnabled()` is called, it must return whether caller threshold, tag, severity, and nonempty writer selection permit output. When `getWriters(tag, level)` receives `OFF` or an unknown bound tag, it must return an empty collection. When synchronous shutdown starts, the provider must close every writer before returning. When asynchronous shutdown starts, the provider must drain queued entries, close writers, and wait for its writing thread. If asynchronous shutdown is interrupted, then `shutdown()` must raise `InterruptedException`.

**Thread context.** `TinylogContextProvider` must provide no-argument construction and expose `getMapping()`, `get(key)`, `put(key, value)`, `remove(key)`, and `clear()`. Its mapping projection is a `Map<String, String>`; `key` is a `String`; `get()` returns a nullable `String`; `put()` accepts `value` as an `Object`; and the mutation methods return no value. When `put()` receives a non-null value, it must store `value.toString()` in the current-thread mapping. When `put()` receives `null`, it must remove the key. When a child thread is created, it must inherit the parent mapping snapshot while later mutations remain thread-local.

## Entry Selection and Format Patterns

Entry selection creates only data requested by active writers, and format patterns project that data consistently into text and structured fields.

**Log-entry data.** `LogEntry` must expose constructor inputs through `getTimestamp()`, `getThread()`, `getContext()`, `getClassName()`, `getMethodName()`, `getFileName()`, `getLineNumber()`, `getTag()`, `getLevel()`, `getMessage()`, and `getException()`. The named construction inputs use the companion `Timestamp` for `timestamp`, `Thread` for `thread`, `Map<String, String>` for `context`, `int` for `lineNumber`, the companion `Level` for `level`, and `String` for `className`, `methodName`, `fileName`, `tag`, and `message`. The nullable `exception` input is a `Throwable`, and `getException()` must return that same nullable `Throwable` projection; every other getter returns the general type assigned to its correspondingly named input. `LogEntryValue` must define `DATE`, `THREAD`, `CONTEXT`, `CLASS`, `METHOD`, `FILE`, `LINE`, `TAG`, `LEVEL`, `MESSAGE`, and `EXCEPTION`. When writers return required values, the provider must populate those projections and avoid requiring unrelated caller-location data.

**Pattern parsing.** `FormatPatternParser` must accept optional comma-separated throwable filters as a `String` named `filters`, and `parse()` must accept a `String` named `pattern` and return a `Token`. A `Token` must return a `Collection<LogEntryValue>` from `getRequiredLogEntryValues()`, append by accepting a `LogEntry` and `StringBuilder` in `render()`, and bind by accepting a `LogEntry`, `PreparedStatement`, and integer `index` in `apply()`; the latter two methods return no value, and binding retains its declared `SQLException` failure. When a pattern combines text and placeholders, the token must preserve their order. If a placeholder is unknown, then the parser must return a token that renders its name as literal text. If a date pattern or style option is invalid, then the parser must report it and retain a renderable fallback token.

**Placeholder vocabulary.** Format patterns must support `{date}`, `{thread}`, `{thread-id}`, `{context:key}`, `{class}`, `{class-name}`, `{package}`, `{method}`, `{file}`, `{line}`, `{tag}`, `{level}`, `{level-code}`, `{message}`, `{message-only}`, `{exception}`, `{pid}`, `{uptime}`, `{opening-curly-bracket}`, `{closing-curly-bracket}`, and `{pipe}`. When `{context:key,default}` names a missing key, it must render `default`. When `{context}` omits a key, it must render all current entries in deterministic mapping form. `{level-code}` must map `ERROR` through `TRACE` to integers `1` through `5`. `{message}` must include the associated throwable, while `{message-only}` must omit it.

**Sizing and indentation.** Where `min-size=n` is present, the token must append spaces to width `n` and preserve longer values. Where `max-size=n` is present, it must drop leading characters to width `n` and preserve shorter values. Where `size=n` is present, it must combine both rules. Where `indent=n` is present, it must indent continuation lines by `n` spaces and replace each leading tab by `n` spaces. If a style value is negative or nonnumeric, then the parser must report it and render without that style.

## Throwable Transformation

Throwable transformation produces a public `ThrowableData` tree before exception placeholders render it.

**Data model.** `ThrowableData` must return `String` values from `getClassName()` and `getMessage()`, a `List<StackTraceElement>` from `getStackTrace()`, a nullable `ThrowableData` from `getCause()`, and a `List<ThrowableData>` from `getSuppressed()`. `ThrowableStore` must accept `className` and `message` as `String`, `stackTrace` as `List<StackTraceElement>`, `cause` as nullable `ThrowableData`, and optional `suppressed` as `List<ThrowableData>`, and its getters must return those supplied projections. When `suppressed` is null or omitted, `getSuppressed()` must return an empty list.

**Filter chain.** A `ThrowableFilter` must accept `origin` as `ThrowableData` and return the transformed `ThrowableData` from `filter()`. The built-in filters must provide no-argument construction and a configured form accepting one `String` argument. Where `exception` defines comma-separated filters, the pipeline must apply them in order. Where a writer defines `exception`, its chain must replace the global chain for that writer. If a filter service is unavailable, then pattern construction must report the failure and keep exception rendering usable.

**Built-in filters.** `StripThrowableFilter` and `KeepThrowableFilter` must accept optional vertical-bar-separated class or package arguments. When a package matches, its subpackages must match. `StripThrowableFilter` must remove matching elements from roots, causes, and suppressed throwables. `KeepThrowableFilter` must retain only matching elements throughout that tree. `UnpackThrowableFilter` must replace a matching throwable with its cause and retain the original when no cause exists. `DropCauseThrowableFilter` must remove the cause while preserving all other projections. Where unpack or drop-cause arguments are empty, the filter must apply to every throwable class.

## Writer Output and Lifecycle

Writers turn selected entries into observable streams or files while preserving formatting and lifecycle guarantees.

**Writer contract.** `Writer` must return a `Collection<LogEntryValue>` from `getRequiredLogEntryValues()`, accept a `LogEntry` named `logEntry` in `write()`, and return no value from `write()`, `flush()`, and `close()`. A configured writer must provide a public constructor accepting `Map<String, String> properties`. When a direct writer operation fails, it must propagate its declared exception. When provider-dispatched output fails, the provider must report the failure and continue other selected writers.

**Format-pattern base.** `AbstractFormatPatternWriter` must accept `properties` as `Map<String, String>`, read `format` and `exception`, return pattern-derived required values as a `Collection<LogEntryValue>`, and expose a protected `render()` operation that accepts a `LogEntry` and returns a `String` to subclasses. When `format` is absent, it must use `{date} [{thread}] {class}.{method}()` followed by a line break and `{level}: {message}`. When rendering, it must append the platform line separator.

**Console output.** `ConsoleWriter` must provide no-argument and `properties` constructors and the `Writer` lifecycle. When `stream` is absent, it must route `WARN` and `ERROR` to `System.err` and lower severities to `System.out`. Where `stream=out` or `stream=err`, it must route all entries to that stream. Where `stream=err@LEVEL`, it must route that level and higher to `System.err`. If `stream` is unsupported, then it must report the value and keep usable severity routing.

**Text files.** `FileWriter` must provide no-argument and `properties` constructors plus `write()`, `flush()`, and `close()`. Where `file` is nested, it must create parent directories. Where `append` is false or absent, it must truncate an existing file. Where `append=true`, it must continue the file. Where `buffered=true`, entries must become durable by `flush()` or `close()`. Where `charset` is absent, it must use the JVM default. If `file` is absent, then construction must raise `IllegalArgumentException`. If `charset` is unavailable, then the writer must report it and use the JVM default.

**Structured JSON.** `JsonWriter` must provide no-argument and `properties` constructors plus the `Writer` lifecycle. Where `field.<name>` properties exist, it must render each value with its pattern and use `<name>` as the key. Where a field pattern is one placeholder name, braces must be optional. Where `format` is absent or equals `JSON` case-insensitively, it must maintain a JSON array. Where `format=LDJSON` case-insensitively, it must emit one object per line. `JsonWriter` must escape backslash, quote, newline, tab, backspace, and form-feed in rendered field values. When a `{message}` or `{message-only}` JSON field receives a carriage-return line break, `JsonWriter` must emit that line break as `\n` rather than `\r`. When standard JSON is flushed or closed, the file must end as a complete array. Where no `field.<name>` properties exist, `JsonWriter` must construct successfully, return an empty collection from `getRequiredLogEntryValues()`, and represent each written entry as an empty object in the selected JSON or LDJSON envelope. If `file` is absent or structural ASCII has nonuniform encoded width, then construction must raise `IllegalArgumentException`.

## Rolling Paths, Conversion, and Policies

Rolling output combines dynamic path resolution, rollover decisions, backup retention, and conversion into one durable file-set projection.

**Path placeholders.** A rolling `file` pattern must support `{count}`, `{date}`, `{dynamic}`, and `{pid}` with plain text. `{count}` must start at `0` and increase for each matching prefix. Where `{date:pattern}` is present, the resolver must use that pattern; where omitted, it must use `yyyy-MM-dd_HH-mm-ss`. Where `{dynamic:initial}` is present before an update, it must use `initial`. `DynamicSegment.getText()` must return current global text as a `String`. When `DynamicSegment.setText()` receives a `String` named `text`, the method must update the current global text, return no value, and leave an existing `DynamicPolicy` continuation decision unchanged. If a path has an unknown placeholder, adjacent placeholders, or unbalanced braces, then construction must raise `IllegalArgumentException`.

**Policy contract.** `Policy.continueExistingFile()` must accept a `String` named `path` and return a boolean decision; `Policy.continueCurrentFile()` must accept the encoded pending entry as `byte[]` named `entry`, rather than a `LogEntry`, and return a boolean decision; `reset()` must return no value. Each built-in policy must provide no-argument construction, and a configured policy must also provide a constructor accepting one `String` named `argument`. When every policy permits continuation, the rolling writer must continue the current file. When any policy rejects continuation, the writer must close and convert the current file, open a newly resolved path, reset every policy, and write the pending entry there.

**Built-in policies.** `StartupPolicy` must reject an existing file and permit current-process entries. `SizePolicy` must accept a positive count with optional `bytes`, `kb`, `mb`, or `gb`, and reject an entry that would exceed it. `DailyPolicy` must roll at its configured daily time, and `MonthlyPolicy` must roll at that time on each first day. Where a date argument contains `@ZoneId`, the policy must use that zone. When `DynamicPolicy.setReset()` is called, an existing `DynamicPolicy` must reject continuation until `reset()` is called; after `reset()`, it must permit continuation. If size, time, or zone is invalid, then construction must raise `IllegalArgumentException`.

**Rolling writer and conversion.** `RollingFileWriter` must provide no-argument and `properties` constructors plus `write()`, `flush()`, and `close()`. Where `policies` is absent, it must use startup policy. Where policies are comma-separated, it must combine all of them. Where `backups=n`, it must retain at most `n` older matching files. Where `latest` names a Linux path, it must replace that path with a hard link to the active file after rollover. Where `convert=gzip`, `GzipFileConverter` must provide no-argument construction, expose `.gz`, return active bytes from conversion, and compress the closed file before shutdown completes. `FileConverter.getBackupSuffix()` must return a `String`; `open()` must accept `fileName` as a `String`; `write()` must accept `data` as `byte[]` and return a `byte[]` containing the passed or replacement bytes to be written; and `open()`, `close()`, and `shutdown()` return no value in that lifecycle order per rolled file. If `file` is absent or `backups` is not an integer, then construction must raise `IllegalArgumentException`.

## State Model

The core state is one immutable configuration snapshot plus issued entries, writer instances, thread-context snapshots, output resources, and rolling-policy state. Public projections are provider queries, `LogEntry` facts, format tokens and text, JSON fields, and durable file lifecycle state.

When configuration is frozen, every projection must use the same writer, level, tag, formatting, filter, and policy snapshot until shutdown.

## Error Semantics

| Condition | Required result |
|---|---|
| Mutation after configuration freeze | If mutation is attempted after configuration freeze, then the operation must raise `UnsupportedOperationException`. |
| Missing required file or invalid rolling grammar | If a writer omits its required file, or a rolling path has invalid grammar, then construction must raise `IllegalArgumentException`. |
| Invalid size, date-policy argument, or backup count | If a size, date-policy argument, or backup count is invalid, then construction must raise `IllegalArgumentException`. |
| Unsupported file charset | If the configured file charset is unavailable, then the writer must report it and use the JVM default. |
| Unknown placeholder | If a format placeholder is unknown, then the parser must return a literal renderable token. |
| Invalid pattern style or date format | If a pattern style or date format is invalid, then the parser must report it and return a fallback token. |
| Direct writer I/O failure | If a direct writer operation encounters an I/O failure, then it must propagate its declared exception. |
| Provider-dispatched writer failure | If provider-dispatched writer output fails, then the provider must report it and continue the other writers. |
| Interrupted asynchronous shutdown | If asynchronous shutdown is interrupted, then `shutdown()` must raise `InterruptedException`. |
| Absent log-entry exception | When the `LogEntry` exception input is null, construction must succeed and `getException()` must return null. |

## Cross-View Invariants

1. An entry accepted by `isEnabled()` must be delivered only to writers returned by `getWriters(tag, level)` for the same tag and severity.
2. A selected writer's required values must agree with non-null `LogEntry` projections and its rendered placeholders or fields; an exception projection must preserve the entry's nullable `Throwable` reference.
3. A context value visible through `getMapping()` at issue time must agree with `{context:key}` in text and JSON projections.
4. One configured throwable chain must produce the same transformed tree, including the ordered `List<StackTraceElement>` projection, for `{exception}` and `{message}` in every writer using it.
5. One `LogEntry` and pattern must render equivalent text through `Token.render()`, console, file, and rolling-file projections.
6. A JSON field configured with one placeholder must agree with that placeholder's text after JSON escaping.
7. When dynamic text changes and `DynamicPolicy.setReset()` is called, provider selection must stay unchanged while rolling-path and file-tree projections move to the new path.
8. When a policy rejects continuation, the pending `byte[]` entry must appear in the new file after any `byte[]` transformation returned by conversion, conversion must follow close, and retention must observe the resulting file set.
9. When `flush()` or `shutdown()` returns, all previously accepted entries must be observable in their configured projection.

## Public Interface

### Import Surface

```java
import org.tinylog.converters.FileConverter;
import org.tinylog.converters.GzipFileConverter;
import org.tinylog.core.LogEntry;
import org.tinylog.core.LogEntryValue;
import org.tinylog.core.TinylogContextProvider;
import org.tinylog.core.TinylogLoggingProvider;
import org.tinylog.path.DynamicSegment;
import org.tinylog.pattern.FormatPatternParser;
import org.tinylog.pattern.Token;
import org.tinylog.policies.AbstractDatePolicy;
import org.tinylog.policies.DailyPolicy;
import org.tinylog.policies.DynamicPolicy;
import org.tinylog.policies.MonthlyPolicy;
import org.tinylog.policies.Policy;
import org.tinylog.policies.SizePolicy;
import org.tinylog.policies.StartupPolicy;
import org.tinylog.throwable.DropCauseThrowableFilter;
import org.tinylog.throwable.KeepThrowableFilter;
import org.tinylog.throwable.StripThrowableFilter;
import org.tinylog.throwable.ThrowableData;
import org.tinylog.throwable.ThrowableFilter;
import org.tinylog.throwable.ThrowableStore;
import org.tinylog.throwable.UnpackThrowableFilter;
import org.tinylog.writers.AbstractFormatPatternWriter;
import org.tinylog.writers.ConsoleWriter;
import org.tinylog.writers.FileWriter;
import org.tinylog.writers.JsonWriter;
import org.tinylog.writers.RollingFileWriter;
import org.tinylog.writers.Writer;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `FileConverter` | interface | Transforms and returns rolling-file byte arrays across lifecycle events |
| `GzipFileConverter` | class | Compresses closed rolling files |
| `LogEntry` | class | Projects one selected logging fact and its nullable throwable |
| `LogEntryValue` | enum | Names entry projections requested by writers |
| `TinylogContextProvider` | class | Stores inheritable thread context |
| `TinylogLoggingProvider` | class | Selects and dispatches entries |
| `DynamicSegment` | class | Controls dynamic rolling-path text |
| `FormatPatternParser` | class | Produces a renderable pattern token |
| `Token` | interface | Renders or binds a pattern projection |
| `AbstractDatePolicy` | abstract class | Supplies date-boundary policy behavior |
| `DailyPolicy` | class | Rolls at a daily boundary |
| `DynamicPolicy` | class | Rolls after an explicit reset |
| `MonthlyPolicy` | class | Rolls at a monthly boundary |
| `Policy` | interface | Decides continuation from paths and encoded entry bytes |
| `SizePolicy` | class | Rolls at a size boundary |
| `StartupPolicy` | class | Rolls at provider startup |
| `DropCauseThrowableFilter` | class | Removes throwable causes |
| `KeepThrowableFilter` | class | Retains matching stack elements |
| `StripThrowableFilter` | class | Removes matching stack elements |
| `ThrowableData` | interface | Projects a throwable tree and ordered stack-element lists |
| `ThrowableFilter` | interface | Transforms throwable data |
| `ThrowableStore` | class | Stores throwable projections and ordered stack-element lists |
| `UnpackThrowableFilter` | class | Replaces throwables with causes |
| `AbstractFormatPatternWriter` | abstract class | Supplies rendering to extensions |
| `ConsoleWriter` | class | Writes to standard streams |
| `FileWriter` | class | Writes one text file |
| `JsonWriter` | class | Writes JSON or LDJSON fields |
| `RollingFileWriter` | class | Writes policy-controlled file sets |
| `Writer` | interface | Declares output lifecycle operations |

### CLI Entry Points

There is no console script for this artifact. Java execution is provided by an embedding application, and programmatic use is through the companion logging API and the public implementation types above.

## Appendix A: Environment

The working and assessment environments run Linux with OpenJDK 9 and Maven 3.9 in offline mode. The preinstalled runtime dependency is `org.tinylog:tinylog-api:2.8-SNAPSHOT`; no database, Android runtime, syslog server, or network service is provided. Both environments use the same JDK major version, Maven repository, and dependency set.

The project must deliver one Maven project rooted at `pom.xml`. The POM must declare group ID `org.tinylog`, artifact ID `tinylog-impl`, version `2.8-SNAPSHOT`, and dependency `org.tinylog:tinylog-api:2.8-SNAPSHOT`. Production sources must live under `src/main/java`, compile with Java 9 language and bytecode compatibility on the provided JDK, and require no network access.

## Appendix B: Assessment Notes

Assessment uses public Java contracts and local process resources. Checks cover configuration precedence and freeze behavior, selection, provider queries, thread context, entry projections, patterns, throwable filters, console/file/JSON output, rolling paths and policies, conversion, lifecycle, errors, and cross-view invariants. Exact internal organization, diagnostic wording, timing races, unsupported writers, and representation strings are not assessed.
