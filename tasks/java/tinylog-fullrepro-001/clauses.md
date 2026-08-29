# Clause Sidecar

Clause IDs correspond to candidate-visible behavioral sentences in `spec/spec_v4.md`.

| Clause ID | Section anchor | Verbatim clause |
|---|---|---|
| TINY-WF-001 | `#representative-workflows` | &ldquo;When this workflow runs in a fresh process, the pipeline must create parent directories, omit the `DEBUG` entry, write the formatted `INFO` entry, and close the file writer before shutdown returns.&rdquo; |
| TINY-WF-002 | `#representative-workflows` | &ldquo;When `DynamicSegment.setText()` changes the active text and `DynamicPolicy.setReset()` is called, the next rolling entry must start a new path while earlier entries remain in the files selected before the reset.&rdquo; |
| TINY-CONF-001 | `#configuration-resolution-and-provider-activation` | &ldquo;**Sources and precedence.** When multiple standard resource files are present, configuration resolution must prefer `tinylog-dev.properties`, then `tinylog-test.properties`, then `tinylog.properties`.&rdquo; |
| TINY-CONF-002 | `#configuration-resolution-and-provider-activation` | &ldquo;Where `tinylog.configuration` names a location, configuration resolution must load that resource or filesystem path.&rdquo; |
| TINY-CONF-003 | `#configuration-resolution-and-provider-activation` | &ldquo;Where a system property uses `tinylog.` followed by a configuration key, its value must override the file value.&rdquo; |
| TINY-CONF-004 | `#configuration-resolution-and-provider-activation` | &ldquo;Where `Configuration.set()` or `Configuration.replace()` supplies a key before first access, its unprefixed value must become active.&rdquo; |
| TINY-CONF-005 | `#configuration-resolution-and-provider-activation` | &ldquo;When configuration is first read, a logger is created, or an entry is issued, the configuration must become immutable.&rdquo; |
| TINY-CONF-006 | `#configuration-resolution-and-provider-activation` | &ldquo;If a mutation is attempted after the freeze, then the call must raise `UnsupportedOperationException`.&rdquo; |
| TINY-CONF-007 | `#configuration-resolution-and-provider-activation` | &ldquo;**Value expansion.** Where a value contains `${name}` or `#{key}`, the resolver must substitute the matching environment variable or Java system property.&rdquo; |
| TINY-CONF-008 | `#configuration-resolution-and-provider-activation` | &ldquo;Where `${name:fallback}` or `#{key:fallback}` names an absent value, the resolver must substitute `fallback`.&rdquo; |
| TINY-CONF-009 | `#configuration-resolution-and-provider-activation` | &ldquo;**Writer discovery.** When no writer root exists, `TinylogLoggingProvider` must instantiate the runtime default writer.&rdquo; |
| TINY-CONF-010 | `#configuration-resolution-and-provider-activation` | &ldquo;Where several roots such as `writer1` and `writerFile` exist, the provider must instantiate each root and pass its child properties to the selected `Writer` constructor.&rdquo; |
| TINY-CONF-011 | `#configuration-resolution-and-provider-activation` | &ldquo;The passed map must contain the root key as `ID` and the effective global `writingthread` value as `writingthread`.&rdquo; |
| TINY-CONF-012 | `#configuration-resolution-and-provider-activation` | &ldquo;If a writer service is unavailable, then provider construction must report the failure and exclude that writer.&rdquo; |
| TINY-CONF-013 | `#configuration-resolution-and-provider-activation` | &ldquo;**Severity and tags.** The severity order must be `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, followed by `OFF`.&rdquo; |
| TINY-CONF-014 | `#configuration-resolution-and-provider-activation` | &ldquo;When `level` is absent, the global threshold must be `TRACE`.&rdquo; |
| TINY-CONF-015 | `#configuration-resolution-and-provider-activation` | &ldquo;Where `level@package.or.Class` entries exist, the provider must use the most specific matching class-or-parent-package threshold.&rdquo; |
| TINY-CONF-016 | `#configuration-resolution-and-provider-activation` | &ldquo;Where a writer has `level`, that threshold must restrict the writer independently.&rdquo; |
| TINY-CONF-017 | `#configuration-resolution-and-provider-activation` | &ldquo;Where a writer has no `tag`, it must receive tagged and untagged entries.&rdquo; |
| TINY-CONF-018 | `#configuration-resolution-and-provider-activation` | &ldquo;Where `tag=-`, the writer must receive only untagged entries.&rdquo; |
| TINY-CONF-019 | `#configuration-resolution-and-provider-activation` | &ldquo;Where `tag` is a comma-separated list, the writer must receive only listed tags.&rdquo; |
| TINY-CONF-020 | `#configuration-resolution-and-provider-activation` | &ldquo;Where a tag item has `@level`, the writer must apply that tag-specific threshold.&rdquo; |
| TINY-CONF-021 | `#configuration-resolution-and-provider-activation` | &ldquo;**Provider queries and lifecycle.** `TinylogLoggingProvider` must provide a no-argument constructor, `getContextProvider()`, both `getMinimumLevel()` forms, both `isEnabled()` forms, both `log()` forms, `shutdown()`, and all three `getWriters()` forms.&rdquo; |
| TINY-CONF-031 | `#configuration-resolution-and-provider-activation` | &ldquo;At the name-based Java boundary used by callers, `className` and `tag` are `String` values, `level` is the companion `Level`, and `isEnabled()` returns a boolean decision.&rdquo; |
| TINY-CONF-032 | `#configuration-resolution-and-provider-activation` | &ldquo;The corresponding `log()` form additionally receives a nullable `Throwable` named `exception`, a companion `MessageFormatter` named `formatter`, an `Object` named `message`, and trailing `Object... arguments`, and returns no value.&rdquo; |
| TINY-CONF-033 | `#configuration-resolution-and-provider-activation` | &ldquo;The tag-and-level `getWriters()` form returns a `Collection<Writer>`, while `shutdown()` returns no value and retains its declared interruption failure.&rdquo; |
| TINY-CONF-022 | `#configuration-resolution-and-provider-activation` | &ldquo;When `isEnabled()` is called, it must return whether caller threshold, tag, severity, and nonempty writer selection permit output.&rdquo; |
| TINY-CONF-023 | `#configuration-resolution-and-provider-activation` | &ldquo;When `getWriters(tag, level)` receives `OFF` or an unknown bound tag, it must return an empty collection.&rdquo; |
| TINY-CONF-024 | `#configuration-resolution-and-provider-activation` | &ldquo;When synchronous shutdown starts, the provider must close every writer before returning.&rdquo; |
| TINY-CONF-025 | `#configuration-resolution-and-provider-activation` | &ldquo;When asynchronous shutdown starts, the provider must drain queued entries, close writers, and wait for its writing thread.&rdquo; |
| TINY-CONF-026 | `#configuration-resolution-and-provider-activation` | &ldquo;If asynchronous shutdown is interrupted, then `shutdown()` must raise `InterruptedException`.&rdquo; |
| TINY-CONF-027 | `#configuration-resolution-and-provider-activation` | &ldquo;**Thread context.** `TinylogContextProvider` must provide no-argument construction and expose `getMapping()`, `get(key)`, `put(key, value)`, `remove(key)`, and `clear()`.&rdquo; |
| TINY-CONF-034 | `#configuration-resolution-and-provider-activation` | &ldquo;Its mapping projection is a `Map<String, String>`; `key` is a `String`; `get()` returns a nullable `String`; `put()` accepts `value` as an `Object`; and the mutation methods return no value.&rdquo; |
| TINY-CONF-028 | `#configuration-resolution-and-provider-activation` | &ldquo;When `put()` receives a non-null value, it must store `value.toString()` in the current-thread mapping.&rdquo; |
| TINY-CONF-029 | `#configuration-resolution-and-provider-activation` | &ldquo;When `put()` receives `null`, it must remove the key.&rdquo; |
| TINY-CONF-030 | `#configuration-resolution-and-provider-activation` | &ldquo;When a child thread is created, it must inherit the parent mapping snapshot while later mutations remain thread-local.&rdquo; |
| TINY-FMT-001 | `#entry-selection-and-format-patterns` | &ldquo;**Log-entry data.** `LogEntry` must expose constructor inputs through `getTimestamp()`, `getThread()`, `getContext()`, `getClassName()`, `getMethodName()`, `getFileName()`, `getLineNumber()`, `getTag()`, `getLevel()`, `getMessage()`, and `getException()`.&rdquo; |
| TINY-FMT-019 | `#entry-selection-and-format-patterns` | &ldquo;The named construction inputs use the companion `Timestamp` for `timestamp`, `Thread` for `thread`, `Map<String, String>` for `context`, `int` for `lineNumber`, the companion `Level` for `level`, and `String` for `className`, `methodName`, `fileName`, `tag`, and `message`.&rdquo; |
| TINY-FMT-020 | `#entry-selection-and-format-patterns` | &ldquo;The nullable `exception` input is a `Throwable`, and `getException()` must return that same nullable `Throwable` projection; every other getter returns the general type assigned to its correspondingly named input.&rdquo; |
| TINY-FMT-002 | `#entry-selection-and-format-patterns` | &ldquo;`LogEntryValue` must define `DATE`, `THREAD`, `CONTEXT`, `CLASS`, `METHOD`, `FILE`, `LINE`, `TAG`, `LEVEL`, `MESSAGE`, and `EXCEPTION`.&rdquo; |
| TINY-FMT-003 | `#entry-selection-and-format-patterns` | &ldquo;When writers return required values, the provider must populate those projections and avoid requiring unrelated caller-location data.&rdquo; |
| TINY-FMT-004 | `#entry-selection-and-format-patterns` | &ldquo;**Pattern parsing.** `FormatPatternParser` must accept optional comma-separated throwable filters as a `String` named `filters`, and `parse()` must accept a `String` named `pattern` and return a `Token`.&rdquo; |
| TINY-FMT-005 | `#entry-selection-and-format-patterns` | &ldquo;A `Token` must return a `Collection<LogEntryValue>` from `getRequiredLogEntryValues()`, append by accepting a `LogEntry` and `StringBuilder` in `render()`, and bind by accepting a `LogEntry`, `PreparedStatement`, and integer `index` in `apply()`; the latter two methods return no value, and binding retains its declared `SQLException` failure.&rdquo; |
| TINY-FMT-006 | `#entry-selection-and-format-patterns` | &ldquo;When a pattern combines text and placeholders, the token must preserve their order.&rdquo; |
| TINY-FMT-007 | `#entry-selection-and-format-patterns` | &ldquo;If a placeholder is unknown, then the parser must return a token that renders its name as literal text.&rdquo; |
| TINY-FMT-008 | `#entry-selection-and-format-patterns` | &ldquo;If a date pattern or style option is invalid, then the parser must report it and retain a renderable fallback token.&rdquo; |
| TINY-FMT-009 | `#entry-selection-and-format-patterns` | &ldquo;**Placeholder vocabulary.** Format patterns must support `{date}`, `{thread}`, `{thread-id}`, `{context:key}`, `{class}`, `{class-name}`, `{package}`, `{method}`, `{file}`, `{line}`, `{tag}`, `{level}`, `{level-code}`, `{message}`, `{message-only}`, `{exception}`, `{pid}`, `{uptime}`, `{opening-curly-bracket}`, `{closing-curly-bracket}`, and `{pipe}`.&rdquo; |
| TINY-FMT-010 | `#entry-selection-and-format-patterns` | &ldquo;When `{context:key,default}` names a missing key, it must render `default`.&rdquo; |
| TINY-FMT-011 | `#entry-selection-and-format-patterns` | &ldquo;When `{context}` omits a key, it must render all current entries in deterministic mapping form.&rdquo; |
| TINY-FMT-012 | `#entry-selection-and-format-patterns` | &ldquo;`{level-code}` must map `ERROR` through `TRACE` to integers `1` through `5`.&rdquo; |
| TINY-FMT-013 | `#entry-selection-and-format-patterns` | &ldquo;`{message}` must include the associated throwable, while `{message-only}` must omit it.&rdquo; |
| TINY-FMT-014 | `#entry-selection-and-format-patterns` | &ldquo;**Sizing and indentation.** Where `min-size=n` is present, the token must append spaces to width `n` and preserve longer values.&rdquo; |
| TINY-FMT-015 | `#entry-selection-and-format-patterns` | &ldquo;Where `max-size=n` is present, it must drop leading characters to width `n` and preserve shorter values.&rdquo; |
| TINY-FMT-016 | `#entry-selection-and-format-patterns` | &ldquo;Where `size=n` is present, it must combine both rules.&rdquo; |
| TINY-FMT-017 | `#entry-selection-and-format-patterns` | &ldquo;Where `indent=n` is present, it must indent continuation lines by `n` spaces and replace each leading tab by `n` spaces.&rdquo; |
| TINY-FMT-018 | `#entry-selection-and-format-patterns` | &ldquo;If a style value is negative or nonnumeric, then the parser must report it and render without that style.&rdquo; |
| TINY-THR-001 | `#throwable-transformation` | &ldquo;**Data model.** `ThrowableData` must return `String` values from `getClassName()` and `getMessage()`, a `List<StackTraceElement>` from `getStackTrace()`, a nullable `ThrowableData` from `getCause()`, and a `List<ThrowableData>` from `getSuppressed()`.&rdquo; |
| TINY-THR-002 | `#throwable-transformation` | &ldquo;`ThrowableStore` must accept `className` and `message` as `String`, `stackTrace` as `List<StackTraceElement>`, `cause` as nullable `ThrowableData`, and optional `suppressed` as `List<ThrowableData>`, and its getters must return those supplied projections.&rdquo; |
| TINY-THR-003 | `#throwable-transformation` | &ldquo;When `suppressed` is null or omitted, `getSuppressed()` must return an empty list.&rdquo; |
| TINY-THR-004 | `#throwable-transformation` | &ldquo;**Filter chain.** A `ThrowableFilter` must accept `origin` as `ThrowableData` and return the transformed `ThrowableData` from `filter()`.&rdquo; |
| TINY-THR-015 | `#throwable-transformation` | &ldquo;The built-in filters must provide no-argument construction and a configured form accepting one `String` argument.&rdquo; |
| TINY-THR-005 | `#throwable-transformation` | &ldquo;Where `exception` defines comma-separated filters, the pipeline must apply them in order.&rdquo; |
| TINY-THR-006 | `#throwable-transformation` | &ldquo;Where a writer defines `exception`, its chain must replace the global chain for that writer.&rdquo; |
| TINY-THR-007 | `#throwable-transformation` | &ldquo;If a filter service is unavailable, then pattern construction must report the failure and keep exception rendering usable.&rdquo; |
| TINY-THR-008 | `#throwable-transformation` | &ldquo;**Built-in filters.** `StripThrowableFilter` and `KeepThrowableFilter` must accept optional vertical-bar-separated class or package arguments.&rdquo; |
| TINY-THR-009 | `#throwable-transformation` | &ldquo;When a package matches, its subpackages must match.&rdquo; |
| TINY-THR-010 | `#throwable-transformation` | &ldquo;`StripThrowableFilter` must remove matching elements from roots, causes, and suppressed throwables.&rdquo; |
| TINY-THR-011 | `#throwable-transformation` | &ldquo;`KeepThrowableFilter` must retain only matching elements throughout that tree.&rdquo; |
| TINY-THR-012 | `#throwable-transformation` | &ldquo;`UnpackThrowableFilter` must replace a matching throwable with its cause and retain the original when no cause exists.&rdquo; |
| TINY-THR-013 | `#throwable-transformation` | &ldquo;`DropCauseThrowableFilter` must remove the cause while preserving all other projections.&rdquo; |
| TINY-THR-014 | `#throwable-transformation` | &ldquo;Where unpack or drop-cause arguments are empty, the filter must apply to every throwable class.&rdquo; |
| TINY-WRITE-001 | `#writer-output-and-lifecycle` | &ldquo;**Writer contract.** `Writer` must return a `Collection<LogEntryValue>` from `getRequiredLogEntryValues()`, accept a `LogEntry` named `logEntry` in `write()`, and return no value from `write()`, `flush()`, and `close()`.&rdquo; |
| TINY-WRITE-002 | `#writer-output-and-lifecycle` | &ldquo;A configured writer must provide a public constructor accepting `Map<String, String> properties`.&rdquo; |
| TINY-WRITE-003 | `#writer-output-and-lifecycle` | &ldquo;When a direct writer operation fails, it must propagate its declared exception.&rdquo; |
| TINY-WRITE-004 | `#writer-output-and-lifecycle` | &ldquo;When provider-dispatched output fails, the provider must report the failure and continue other selected writers.&rdquo; |
| TINY-WRITE-005 | `#writer-output-and-lifecycle` | &ldquo;**Format-pattern base.** `AbstractFormatPatternWriter` must accept `properties` as `Map<String, String>`, read `format` and `exception`, return pattern-derived required values as a `Collection<LogEntryValue>`, and expose a protected `render()` operation that accepts a `LogEntry` and returns a `String` to subclasses.&rdquo; |
| TINY-WRITE-006 | `#writer-output-and-lifecycle` | &ldquo;When `format` is absent, it must use `{date} [{thread}] {class}.{method}()` followed by a line break and `{level}: {message}`.&rdquo; |
| TINY-WRITE-007 | `#writer-output-and-lifecycle` | &ldquo;When rendering, it must append the platform line separator.&rdquo; |
| TINY-WRITE-008 | `#writer-output-and-lifecycle` | &ldquo;**Console output.** `ConsoleWriter` must provide no-argument and `properties` constructors and the `Writer` lifecycle.&rdquo; |
| TINY-WRITE-009 | `#writer-output-and-lifecycle` | &ldquo;When `stream` is absent, it must route `WARN` and `ERROR` to `System.err` and lower severities to `System.out`.&rdquo; |
| TINY-WRITE-010 | `#writer-output-and-lifecycle` | &ldquo;Where `stream=out` or `stream=err`, it must route all entries to that stream.&rdquo; |
| TINY-WRITE-011 | `#writer-output-and-lifecycle` | &ldquo;Where `stream=err@LEVEL`, it must route that level and higher to `System.err`.&rdquo; |
| TINY-WRITE-012 | `#writer-output-and-lifecycle` | &ldquo;If `stream` is unsupported, then it must report the value and keep usable severity routing.&rdquo; |
| TINY-WRITE-013 | `#writer-output-and-lifecycle` | &ldquo;**Text files.** `FileWriter` must provide no-argument and `properties` constructors plus `write()`, `flush()`, and `close()`.&rdquo; |
| TINY-WRITE-014 | `#writer-output-and-lifecycle` | &ldquo;Where `file` is nested, it must create parent directories.&rdquo; |
| TINY-WRITE-015 | `#writer-output-and-lifecycle` | &ldquo;Where `append` is false or absent, it must truncate an existing file.&rdquo; |
| TINY-WRITE-016 | `#writer-output-and-lifecycle` | &ldquo;Where `append=true`, it must continue the file.&rdquo; |
| TINY-WRITE-017 | `#writer-output-and-lifecycle` | &ldquo;Where `buffered=true`, entries must become durable by `flush()` or `close()`.&rdquo; |
| TINY-WRITE-018 | `#writer-output-and-lifecycle` | &ldquo;Where `charset` is absent, it must use the JVM default.&rdquo; |
| TINY-WRITE-019 | `#writer-output-and-lifecycle` | &ldquo;If `file` is absent, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-WRITE-020 | `#writer-output-and-lifecycle` | &ldquo;If `charset` is unavailable, then the writer must report it and use the JVM default.&rdquo; |
| TINY-WRITE-021 | `#writer-output-and-lifecycle` | &ldquo;**Structured JSON.** `JsonWriter` must provide no-argument and `properties` constructors plus the `Writer` lifecycle.&rdquo; |
| TINY-WRITE-022 | `#writer-output-and-lifecycle` | &ldquo;Where `field.<name>` properties exist, it must render each value with its pattern and use `<name>` as the key.&rdquo; |
| TINY-WRITE-023 | `#writer-output-and-lifecycle` | &ldquo;Where a field pattern is one placeholder name, braces must be optional.&rdquo; |
| TINY-WRITE-024 | `#writer-output-and-lifecycle` | &ldquo;Where `format` is absent or equals `JSON` case-insensitively, it must maintain a JSON array.&rdquo; |
| TINY-WRITE-025 | `#writer-output-and-lifecycle` | &ldquo;Where `format=LDJSON` case-insensitively, it must emit one object per line.&rdquo; |
| TINY-WRITE-026 | `#writer-output-and-lifecycle` | &ldquo;`JsonWriter` must escape backslash, quote, newline, tab, backspace, and form-feed in rendered field values.&rdquo; |
| TINY-WRITE-027 | `#writer-output-and-lifecycle` | &ldquo;When standard JSON is flushed or closed, the file must end as a complete array.&rdquo; |
| TINY-WRITE-028 | `#writer-output-and-lifecycle` | &ldquo;Where no `field.<name>` properties exist, `JsonWriter` must construct successfully, return an empty collection from `getRequiredLogEntryValues()`, and represent each written entry as an empty object in the selected JSON or LDJSON envelope.&rdquo; |
| TINY-WRITE-029 | `#writer-output-and-lifecycle` | &ldquo;If `file` is absent or structural ASCII has nonuniform encoded width, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-WRITE-030 | `#writer-output-and-lifecycle` | &ldquo;When a `{message}` or `{message-only}` JSON field receives a carriage-return line break, `JsonWriter` must emit that line break as `\n` rather than `\r`.&rdquo; |
| TINY-ROLL-001 | `#rolling-paths-conversion-and-policies` | &ldquo;**Path placeholders.** A rolling `file` pattern must support `{count}`, `{date}`, `{dynamic}`, and `{pid}` with plain text.&rdquo; |
| TINY-ROLL-002 | `#rolling-paths-conversion-and-policies` | &ldquo;`{count}` must start at `0` and increase for each matching prefix.&rdquo; |
| TINY-ROLL-003 | `#rolling-paths-conversion-and-policies` | &ldquo;Where `{date:pattern}` is present, the resolver must use that pattern; where omitted, it must use `yyyy-MM-dd_HH-mm-ss`.&rdquo; |
| TINY-ROLL-004 | `#rolling-paths-conversion-and-policies` | &ldquo;Where `{dynamic:initial}` is present before an update, it must use `initial`.&rdquo; |
| TINY-ROLL-005 | `#rolling-paths-conversion-and-policies` | &ldquo;`DynamicSegment.getText()` must return current global text as a `String`.&rdquo; |
| TINY-ROLL-006 | `#rolling-paths-conversion-and-policies` | &ldquo;When `DynamicSegment.setText()` receives a `String` named `text`, the method must update the current global text, return no value, and leave an existing `DynamicPolicy` continuation decision unchanged.&rdquo; |
| TINY-ROLL-007 | `#rolling-paths-conversion-and-policies` | &ldquo;If a path has an unknown placeholder, adjacent placeholders, or unbalanced braces, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-ROLL-008 | `#rolling-paths-conversion-and-policies` | &ldquo;**Policy contract.** `Policy.continueExistingFile()` must accept a `String` named `path` and return a boolean decision; `Policy.continueCurrentFile()` must accept the encoded pending entry as `byte[]` named `entry`, rather than a `LogEntry`, and return a boolean decision; `reset()` must return no value.&rdquo; |
| TINY-ROLL-009 | `#rolling-paths-conversion-and-policies` | &ldquo;Each built-in policy must provide no-argument construction, and a configured policy must also provide a constructor accepting one `String` named `argument`.&rdquo; |
| TINY-ROLL-010 | `#rolling-paths-conversion-and-policies` | &ldquo;When every policy permits continuation, the rolling writer must continue the current file.&rdquo; |
| TINY-ROLL-011 | `#rolling-paths-conversion-and-policies` | &ldquo;When any policy rejects continuation, the writer must close and convert the current file, open a newly resolved path, reset every policy, and write the pending entry there.&rdquo; |
| TINY-ROLL-012 | `#rolling-paths-conversion-and-policies` | &ldquo;**Built-in policies.** `StartupPolicy` must reject an existing file and permit current-process entries.&rdquo; |
| TINY-ROLL-013 | `#rolling-paths-conversion-and-policies` | &ldquo;`SizePolicy` must accept a positive count with optional `bytes`, `kb`, `mb`, or `gb`, and reject an entry that would exceed it.&rdquo; |
| TINY-ROLL-014 | `#rolling-paths-conversion-and-policies` | &ldquo;`DailyPolicy` must roll at its configured daily time, and `MonthlyPolicy` must roll at that time on each first day.&rdquo; |
| TINY-ROLL-015 | `#rolling-paths-conversion-and-policies` | &ldquo;Where a date argument contains `@ZoneId`, the policy must use that zone.&rdquo; |
| TINY-ROLL-016 | `#rolling-paths-conversion-and-policies` | &ldquo;When `DynamicPolicy.setReset()` is called, an existing `DynamicPolicy` must reject continuation until `reset()` is called; after `reset()`, it must permit continuation.&rdquo; |
| TINY-ROLL-017 | `#rolling-paths-conversion-and-policies` | &ldquo;If size, time, or zone is invalid, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-ROLL-018 | `#rolling-paths-conversion-and-policies` | &ldquo;**Rolling writer and conversion.** `RollingFileWriter` must provide no-argument and `properties` constructors plus `write()`, `flush()`, and `close()`.&rdquo; |
| TINY-ROLL-019 | `#rolling-paths-conversion-and-policies` | &ldquo;Where `policies` is absent, it must use startup policy.&rdquo; |
| TINY-ROLL-020 | `#rolling-paths-conversion-and-policies` | &ldquo;Where policies are comma-separated, it must combine all of them.&rdquo; |
| TINY-ROLL-021 | `#rolling-paths-conversion-and-policies` | &ldquo;Where `backups=n`, it must retain at most `n` older matching files.&rdquo; |
| TINY-ROLL-022 | `#rolling-paths-conversion-and-policies` | &ldquo;Where `latest` names a Linux path, it must replace that path with a hard link to the active file after rollover.&rdquo; |
| TINY-ROLL-023 | `#rolling-paths-conversion-and-policies` | &ldquo;Where `convert=gzip`, `GzipFileConverter` must provide no-argument construction, expose `.gz`, return active bytes from conversion, and compress the closed file before shutdown completes.&rdquo; |
| TINY-ROLL-024 | `#rolling-paths-conversion-and-policies` | &ldquo;`FileConverter.getBackupSuffix()` must return a `String`; `open()` must accept `fileName` as a `String`; `write()` must accept `data` as `byte[]` and return a `byte[]` containing the passed or replacement bytes to be written; and `open()`, `close()`, and `shutdown()` return no value in that lifecycle order per rolled file.&rdquo; |
| TINY-ROLL-025 | `#rolling-paths-conversion-and-policies` | &ldquo;If `file` is absent or `backups` is not an integer, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-STATE-001 | `#state-model` | &ldquo;When configuration is frozen, every projection must use the same writer, level, tag, formatting, filter, and policy snapshot until shutdown.&rdquo; |
| TINY-CVI-001 | `#cross-view-invariants` | &ldquo;An entry accepted by `isEnabled()` must be delivered only to writers returned by `getWriters(tag, level)` for the same tag and severity.&rdquo; |
| TINY-CVI-002 | `#cross-view-invariants` | &ldquo;A selected writer's required values must agree with non-null `LogEntry` projections and its rendered placeholders or fields; an exception projection must preserve the entry's nullable `Throwable` reference.&rdquo; |
| TINY-CVI-003 | `#cross-view-invariants` | &ldquo;A context value visible through `getMapping()` at issue time must agree with `{context:key}` in text and JSON projections.&rdquo; |
| TINY-CVI-004 | `#cross-view-invariants` | &ldquo;One configured throwable chain must produce the same transformed tree, including the ordered `List<StackTraceElement>` projection, for `{exception}` and `{message}` in every writer using it.&rdquo; |
| TINY-CVI-005 | `#cross-view-invariants` | &ldquo;One `LogEntry` and pattern must render equivalent text through `Token.render()`, console, file, and rolling-file projections.&rdquo; |
| TINY-CVI-006 | `#cross-view-invariants` | &ldquo;A JSON field configured with one placeholder must agree with that placeholder's text after JSON escaping.&rdquo; |
| TINY-CVI-007 | `#cross-view-invariants` | &ldquo;When dynamic text changes and `DynamicPolicy.setReset()` is called, provider selection must stay unchanged while rolling-path and file-tree projections move to the new path.&rdquo; |
| TINY-CVI-008 | `#cross-view-invariants` | &ldquo;When a policy rejects continuation, the pending `byte[]` entry must appear in the new file after any `byte[]` transformation returned by conversion, conversion must follow close, and retention must observe the resulting file set.&rdquo; |
| TINY-CVI-009 | `#cross-view-invariants` | &ldquo;When `flush()` or `shutdown()` returns, all previously accepted entries must be observable in their configured projection.&rdquo; |
| TINY-ENV-001 | `#appendix-a-environment` | &ldquo;The project must deliver one Maven project rooted at `pom.xml`.&rdquo; |
| TINY-ENV-002 | `#appendix-a-environment` | &ldquo;The POM must declare group ID `org.tinylog`, artifact ID `tinylog-impl`, version `2.8-SNAPSHOT`, and dependency `org.tinylog:tinylog-api:2.8-SNAPSHOT`.&rdquo; |
| TINY-ENV-003 | `#appendix-a-environment` | &ldquo;Production sources must live under `src/main/java`, compile with Java 9 language and bytecode compatibility on the provided JDK, and require no network access.&rdquo; |
| TINY-ERR-001 | `#error-semantics` | &ldquo;If mutation is attempted after configuration freeze, then the operation must raise `UnsupportedOperationException`.&rdquo; |
| TINY-ERR-002 | `#error-semantics` | &ldquo;If a writer omits its required file, or a rolling path has invalid grammar, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-ERR-003 | `#error-semantics` | &ldquo;If a size, date-policy argument, or backup count is invalid, then construction must raise `IllegalArgumentException`.&rdquo; |
| TINY-ERR-004 | `#error-semantics` | &ldquo;If the configured file charset is unavailable, then the writer must report it and use the JVM default.&rdquo; |
| TINY-ERR-005 | `#error-semantics` | &ldquo;If a format placeholder is unknown, then the parser must return a literal renderable token.&rdquo; |
| TINY-ERR-006 | `#error-semantics` | &ldquo;If a pattern style or date format is invalid, then the parser must report it and return a fallback token.&rdquo; |
| TINY-ERR-007 | `#error-semantics` | &ldquo;If a direct writer operation encounters an I/O failure, then it must propagate its declared exception.&rdquo; |
| TINY-ERR-008 | `#error-semantics` | &ldquo;If provider-dispatched writer output fails, then the provider must report it and continue the other writers.&rdquo; |
| TINY-ERR-009 | `#error-semantics` | &ldquo;If asynchronous shutdown is interrupted, then `shutdown()` must raise `InterruptedException`.&rdquo; |
| TINY-ERR-010 | `#error-semantics` | &ldquo;When the `LogEntry` exception input is null, construction must succeed and `getException()` must return null.&rdquo; |
