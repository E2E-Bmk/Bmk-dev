# @oclif/core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`@oclif/core` is a Node.js command-line framework that discovers command classes, parses argv into typed arguments and flags, and executes commands through a configured plugin graph. It projects the same invocation through command results, lifecycle hooks, generated help, structured errors, logging, and configuration inspection.

Commands declare their argument and flag definitions as static metadata. A `Config` loads a root package and its plugins, maps command identifiers to command classes, and supplies the context used by parsing, help, hooks, and execution. The package is usable from a generated CLI or directly from a Node.js script.

## Non-Goals

- This specification does not require remote plugin registries, automatic updates, or network access.
- This specification does not require the CLI generator, installer creation, autocomplete generation, or publishing integration.
- This specification does not define private module helpers, private fields, manifest file layouts, or dependency versions.
- This specification does not require performance reports, timing markers, or performance-specific output.
- This specification does not require vendor-specific plugins, plugin installation commands, or subprocess interoperability matrices.
- This specification does not define exact help wrapping, ANSI styling, warning wording, log formatting, or stack-trace text.
- This specification does not require browser runtimes or a runtime other than Node.js.

## Representative Workflows

### Parsing a Standalone Command Line

```ts
import {Args, Flags, Parser} from '@oclif/core'

const result = await Parser.parse(['world', '--from', 'oclif'], {
  args: {name: Args.string({required: true})},
  flags: {from: Flags.string({char: 'f', default: 'oclif'})},
})

console.log(`hello ${result.args.name} from ${result.flags.from}`)
```

The parser applies the declared definitions, resolves defaults, and returns typed `args`, `flags`, the remaining `argv`, raw parsing tokens, metadata, and names of non-existent flags. Invalid values or missing required inputs reject the promise with a library error.

### Running a Command Class

```ts
import {Command, Flags, flush, handle} from '@oclif/core'

class ListCommand extends Command {
  static description = 'List the selected directory.'
  static flags = {directory: Flags.string({char: 'd', default: '.'})}

  async run() {
    const {flags} = await this.parse(ListCommand)
    this.log(`directory=${flags.directory}`)
    return flags.directory
  }
}

ListCommand.run(process.argv.slice(2), {root: import.meta.dirname}).then(
  async () => flush(),
  async (error) => handle(error),
)
```

`Command.run` loads a `Config`, constructs the command with argv and config, invokes initialization, parses when the command requests it, runs the command body, and executes finalization even when an error is raised.

### Hooks and Help in a Local CLI

```ts
import {Config, Help, run} from '@oclif/core'

const config = await Config.load({root: process.cwd()})
await config.runHook('init', {argv: [], id: undefined})
const help = new Help(config)
await help.showHelp([])
await run(['--help'], config)
```

The configuration loads commands and plugins before hooks or help are invoked. A help request renders the configured command graph and returns without running a command; a normal request resolves the selected command and runs the lifecycle hooks around it.

## Argument and Flag Parsing

Argument and flag definitions turn tokenized argv into typed values while preserving enough metadata for help and diagnostics.

**Definitions and values.** The `Args` namespace must expose `custom`, `boolean`, `integer`, `directory`, `file`, `url`, `string`, and `option`. The `Flags` namespace must expose those builders plus `version` and `help`. A builder must return a definition function whose options merge with its defaults and whose resulting definition contains a parser, a name assigned by the parser, and an input-token list.

**Built-in conversions.** When an `Args` or `Flags` `boolean` parser receives a token, it must return a boolean using the framework's truthy/falsy rules. When an `integer` parser receives a non-integer token, it must raise `CLIError`; when `min` or `max` is present, values outside the inclusive bound must raise `CLIError`. When `url` receives an invalid URL string, it must raise `CLIError` and a valid value must return a `URL` object. When `directory` or `file` receives `exists: true`, it must resolve the path check and raise the underlying path error when the path is absent. Otherwise those builders must return the input string. The `string` builder must return the input unchanged.

**Choices and custom parsers.** When an `option` definition receives a value not in its readonly `options` list, the parser must raise `CLIError`. A `custom` definition must call its supplied asynchronous `parse` function with the input, command context, and options object. A custom parser rejection must reject the parse operation with the same error.

**Flag forms.** A boolean flag must consume no value and must default to `false` unless a default is supplied. Where `allowNo` is true, a `--no-<name>` token must produce the negated boolean value. An option flag must consume one value unless `multiple` is true. Where `multiple` is true, repeated occurrences must produce an array; where `delimiter` is present, one occurrence must split unescaped delimiters before parsing. A flag with `env` must use the named environment value when argv supplies no value. A flag or arg with a `default` must resolve a static value or await its default function; a `defaultHelp` function must contribute help metadata without replacing the parsed value. A flag with `allowStdin` must read trimmed stdin when the configured token is `-`.

**Argument forms.** Arguments are declared by an ordered object. The parser must assign positional tokens in declaration order, apply argument defaults for missing values, and collect the remaining values into the one argument marked `multiple`. When an argument has `options`, a value outside that list must raise `CLIError`. When `ignoreStdin` is false and no positional token is available, the parser must attempt stdin before applying the default.

**Parser contract.** `Parser.parse` must accept an argv string array and an input object containing `args`, `flags`, optional `baseFlags`, optional `constraints`, optional command `context`, optional `--` handling, and a strictness setting. It must return a promise of `ParserOutput` with `args`, `flags`, `argv`, `raw`, `metadata`, and `nonExistentFlags`. The returned flags object must include a `json` property whose value is boolean or `undefined`.

**Token boundaries.** When a token starts with `-` and does not match a declared flag, the parser must record it in `nonExistentFlags` and must raise a validation error when strict validation rejects unknown flags. A literal `--` must stop flag parsing when `--` handling is enabled and must remain in the returned argv ordering. A negative numeric token must remain available to an integer argument or flag rather than being treated as an unknown flag. Repeated non-greedy flags must consume one following value per occurrence.

**Relationships and validation.** The `Constraints` namespace must expose `flag`, `flags`, and `combinationOf`. A constraint must be evaluated against the parsed flags. If a required flag or argument is missing, if an exclusive or combinable relationship is violated, or if a custom validation rejects, the parser must raise a parser error with the offending definitions attached. `Parser.validate` must validate a previously produced parser input/output pair and must reject invalid relationships or required values.

**Usage metadata.** `Parser.flagUsages` must return one name/description tuple per supplied flag in declaration order. `Parser.validate` and all parser failures must preserve the parsed input/output context in the library error where that context is available.

## Commands, Configuration, and Plugins

Configuration establishes the command graph and supplies command instances with a stable execution context.

**Command declaration.** `Command` must be an abstract base class whose constructor accepts an argv string array and a `Config`. A subclass must implement an asynchronous `run` method. Static command metadata must include `id`, `aliases`, `hiddenAliases`, `description`, `summary`, `examples`, `usage`, `args`, `flags`, `baseFlags`, `constraints`, `strict`, `hidden`, `state`, and `enableJsonFlag` when those features are used. `Command.Class`, `Command.Loadable`, `Command.Cached`, `Command.Arg`, and `Command.Flag` must provide the documented type-level representations of those command forms.

**Command execution.** `Command.run` must accept an optional argv array and a load option. When the load option is a file URL, it must resolve it as a filesystem path. It must load a config, create the subclass instance, invoke `init`, await the command's `run`, invoke `finally` on both success and failure, and return the command result. A command that calls `parse` must receive the typed parser output and must mark itself parsed. A command that finishes without parsing outside production mode must emit the unparsed-command warning.

**Command context.** `Command.log` must write formatted output to stdout and `Command.logToStderr` must write formatted output to stderr. When `jsonEnabled` is true, these methods must suppress ordinary output. `jsonEnabled` must return true only when the command enables JSON, the scoped content-type environment variable is `json`, or a `--json` token occurs before `--`. `Command.warn` must forward warnings unless JSON output is active. `Command.error` must delegate to the error helper and `Command.exit` must raise an exit error with the supplied code.

**Configuration loading.** `Config.load` must accept an existing `Config`, an `Options` object, a root path, or a file URL. It must load the root package metadata, establish platform and architecture information, derive the bin name, version, channel, user agent, home/config/cache/data directories, topic separator, and theme, and load the configured plugins and commands. The root package must be marked as the root plugin and must occupy the plugin map by name.

**Command discovery.** A plugin command discovery configuration must use `pattern`, `single`, or `explicit` strategy. A pattern strategy must derive command IDs from command file paths; a single strategy must load the target command; an explicit strategy must load the target ID-to-command map. When a discovery strategy omits its required target, `Config.load` must raise `CLIError`. `Config.findCommand` must return the command with the normalized ID or `undefined`; when `must: true` is supplied and no command exists, it must raise a CLI error. `Config.findTopic` must provide the analogous topic lookup. `getAllCommands` and `getAllCommandIDs` must include valid flexible-taxonomy permutations when that mode is enabled.

**Plugin lifecycle.** `Plugin` must accept `PluginOptions`, load package metadata and hooks, discover command IDs, and expose `name`, `version`, `root`, `type`, `moduleType`, `valid`, `topics`, `commands`, and `commandIDs`. `Plugin.findCommand` must return a loaded command class or `undefined`, and `must: true` must raise a CLI error when the command is absent. `Plugin.load` must reject when the package root or package name cannot be resolved.

**Configuration projections.** `Config` must expose readonly projections for `name`, `version`, `channel`, `bin`, `root`, `pjson`, `plugins`, `commands`, `topics`, `platform`, `arch`, `shell`, `home`, `cacheDir`, `configDir`, `dataDir`, `userAgent`, `versionDetails`, `valid`, and `isSingleCommandCLI`. `getPluginsList` must return the plugin map values. `scopedEnvVarKey`, `scopedEnvVarKeys`, `scopedEnvVar`, and `scopedEnvVarTrue` must derive environment names from the bin and aliases; a true value must recognize the framework truthy vocabulary.

**Command identifiers.** `toStandardizedId` must replace the configured topic separator with `:`. `toConfiguredId` must replace `:` with the configured topic separator and must use `:` when no separator is configured. `Config.topicSeparator` must accept only `:` or a space; configured IDs and help output must use that separator.

## Execution Lifecycle and Hooks

The execution functions coordinate configuration, command lookup, hooks, help, version handling, and cleanup.

**Top-level execution.** `run` must accept an argv array and load options, load the configuration, run the `init` hook, and then choose one of version output, help output, or command execution. When the first argv value is a configured version flag, it must write the config user agent and resolve without running a command. When `helpAddition` returns true, it must render help and resolve without running a command. When no command is found, `run` must render topic help for a known topic or raise a `CLIError` for an unknown command.

**Command lifecycle.** `Config.runCommand` must load the selected command class, run the `prerun` hooks, await the command, run `postrun` only after successful completion, and return the command result. When a command raises, `runCommand` must reject with that error and must still let the outer `finally` hook run. When flexible taxonomy finds partial matches, `runCommand` must invoke `command_incomplete`; when no match exists, it must invoke `command_not_found`.

**Hook events.** `Config.runHook` must accept a hook event, its event-specific options, an optional timeout, and `captureErrors`. It must return a `Hook.Result` containing `successes` and `failures` with the contributing plugin and result or error. The `init`, `preparse`, `prerun`, `postrun`, `finally`, `command_not_found`, `command_incomplete`, `jit_plugin_not_installed`, `plugins:preinstall`, `preupdate`, and `update` event names must retain their documented option and return shapes. The `preparse` hook must run on the root plugin before parser invocation and must use its returned argv when a successful result supplies one.

**Hook failures.** When a hook rejects and `captureErrors` is false, `runHook` must rethrow failures whose exit code is nonzero and must preserve the plugin and error in the result. When `captureErrors` is true, it must collect the failure and resolve. When a timeout is supplied and the hook exceeds it, the hook result must contain an error stating that the timeout elapsed.

**Convenience execution.** `execute` must require `dir` or `loadOptions`; when both are absent it must raise `CLIError`. When `development` is true, it must set development mode and debug settings before calling `run`, and it must call `flush` after success or `handle` after failure. `flush` must wait for pending output for its optional millisecond interval and then resolve.

## Help, Errors, and Terminal Output

Help and error helpers project parser and configuration state into user-facing terminal behavior.

**Help rendering.** `HelpBase` must accept a `Config` and help options and must define asynchronous `showCommandHelp` and `showHelp`. `Help` must render root commands, topics, command descriptions, usage, args, flags, examples, and configured themes. Hidden commands and topics must be omitted unless the `all` option is true. `formatRoot` must return the complete root help string. `CommandHelp` and `HelpFormatter` must provide the documented formatter and section-renderer interfaces. `loadHelpClass` must return the configured help class or the default `Help` class.

**Help flags and argv.** `getHelpFlagAdditions` must return configured help flag aliases. `normalizeArgv` must normalize command IDs and preserve argument tokens. `standardizeIDFromArgv` must derive a standardized command ID from argv and configuration. `helpAddition` must return true for an empty multi-command argv, a configured help flag, or a `help` token before `--`, and must return false when `--` terminates option parsing first. `versionAddition` must return true for `--version` or a configured additional version flag in the first argv position.

**Structured errors.** `CLIError` must extend `Error`, expose an exit code and optional oclif metadata, and preserve a supplied message. `ExitError` must represent process termination with its code. `ModuleLoadError` must represent a module-loading failure and retain the original cause. `Errors.error` must log and either return when `exit: false` or raise an error with the requested exit code. `Errors.exit` must raise an `ExitError` with the requested code, defaulting to zero. `Errors.warn` must emit a warning without terminating. `Errors.handle` and the root `handle` export must asynchronously handle an error and set the process exit projection according to its exit metadata.

**Terminal helpers.** `ux.stdout` and `ux.stderr` must write strings or string arrays using Node formatting arguments. `ux.colorize` must return a colorized string for a standard ANSI color or color code. `ux.colorizeJson` must return formatted JSON text using the requested pretty and theme options. The `ux.action` object must expose start, stop, and status behavior for simple or spinner actions, and `ux` must expose the action and all terminal helper functions.

## State Model

The core state is a configured command graph plus one active invocation. The graph contains a root `Plugin`, zero or more child plugins, command and topic indexes, package metadata, environment-derived settings, and hook registrations. The invocation contains argv tokens, parser definitions and output, the selected command, hook results, terminal output, and an optional error.

The public projections of this state are:

1. `Config` and `Plugin` inspection properties for roots, commands, topics, metadata, and environment settings.
2. `Parser.parse` and `Command.parse` results for typed args, flags, raw tokens, metadata, and unknown flags.
3. `run`, `execute`, `Config.runCommand`, and `Command.run` results or errors.
4. `Config.runHook` results containing per-plugin successes and failures.
5. `Help` and `CommandHelp` output strings rendered from the same command graph.
6. `CLIError`, `ExitError`, and `ModuleLoadError` projections carrying messages, causes, and exit metadata.
7. `ux`, logger, and settings projections for terminal output and debug configuration.

## Error Semantics

| Condition | Required result |
|---|---|
| A required argument or flag is absent | The parser must raise a parser error carrying the missing definition. |
| An option value is outside its declared choices | The parser must raise `CLIError`. |
| An integer value is malformed or outside `min`/`max` | The integer parser must raise `CLIError`. |
| A URL value is malformed | The URL parser must raise `CLIError`. |
| A command or topic is absent with `must: true` | The lookup must raise `CLIError`. |
| A plugin root or package name cannot be found | `Plugin.load` must reject with `CLIError`. |
| `execute` has neither `dir` nor `loadOptions` | `execute` must raise `CLIError`. |
| A command ID is unknown and no hook handles it | `run` or `Config.runCommand` must reject with `CLIError`. |
| A hook exceeds its timeout | `runHook` must record a timeout error. |
| A command fails | The failure must propagate and the `finally` hook must still run. |
| `Errors.exit` is called | It must raise `ExitError` with the supplied code. |

## Cross-View Invariants

1. A command's static `args` and `flags` definitions must produce the same parsed values through `Parser.parse` and `Command.parse` when they receive identical argv and context.
2. A command returned by `Config.findCommand` must be the command class loaded by `Config.runCommand` for the same standardized ID.
3. A plugin listed in `Config.plugins` must contribute the command IDs returned by `Config.getAllCommandIDs` and the topics returned by `Config.topics`.
4. A successful `preparse` hook result must be the argv consumed by the parser and visible in the command's `argv` property.
5. A successful command must produce a `postrun` hook success and a `finally` hook success, while a failed command must omit `postrun` and still produce `finally`.
6. A help request recognized by `helpAddition` must render `Help` output and must not invoke the selected command's `run` method.
7. A version request recognized by `versionAddition` must write `Config.userAgent` and must not invoke command lookup or execution.
8. A parser error represented by `CLIError` must retain the same message and exit metadata when it passes through `Command.catch`, `run`, and `handle`.
9. A configured topic separator must be used consistently by `toConfiguredId`, `normalizeArgv`, command lookup, and help command labels.
10. A value written with `Command.log` or `ux.stdout` must be suppressed from ordinary stdout when JSON mode is enabled, while structured JSON output remains available.

## Public Interface

### Import Surface

The package is installed as `@oclif/core` and exposes the following module entry points:

```ts
import {Args, Command, Config, Plugin, Constraints, Errors, Flags, Help, HelpBase, CommandHelp, Parser, execute as executeRoot, run as runRoot, flush as flushRoot, handle as handleRoot, getLogger, settings as settingsRoot, toConfiguredId, toStandardizedId, ux} from '@oclif/core'
import {custom, boolean, integer, directory, file, url, string, option} from '@oclif/core/args'
import {Command as CommandClass} from '@oclif/core/command'
import {Config as ConfigClass, Plugin as PluginClass} from '@oclif/core/config'
import {CLIError, ExitError, ModuleLoadError, error, exit, warn, handle as handleError} from '@oclif/core/errors'
import {execute} from '@oclif/core/execute'
import {custom as flagCustom, boolean as flagBoolean, integer as flagInteger, directory as flagDirectory, file as flagFile, url as flagUrl, string as flagString, version, help as helpFlag, option as flagOption} from '@oclif/core/flags'
import {flush} from '@oclif/core/flush'
import {handle} from '@oclif/core/handle'
import {Help as HelpClass, HelpBase as HelpBaseClass, CommandHelp as CommandHelpClass, HelpFormatter, getHelpFlagAdditions, loadHelpClass, normalizeArgv, standardizeIDFromArgv} from '@oclif/core/help'
import type {Hook} from '@oclif/core/hooks'
import * as Interfaces from '@oclif/core/interfaces'
import {getLogger as getLoggerFromModule} from '@oclif/core/logger'
import {parse, validate, flagUsages} from '@oclif/core/parser'
import {Performance} from '@oclif/core/performance'
import {run} from '@oclif/core/run'
import {settings} from '@oclif/core/settings'
import {toConfiguredId as configuredId, toStandardizedId as standardizedId} from '@oclif/core/util/ids'
import {ux as uxModule, stdout, stderr, colorize, colorizeJson, action} from '@oclif/core/ux'
```

The root entry point re-exports `Args`, `Command`, `Config`, `Plugin`, `Constraints`, `Errors`, `handle`, `execute`, `Flags`, `flush`, `CommandHelp`, `Help`, `HelpBase`, `Interfaces`, `Hook`, `getLogger`, `run`, `ModuleLoader`, `Parser`, `Performance`, `Settings`, `settings`, `toConfiguredId`, `toStandardizedId`, and `ux`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Args | namespace | Built-in argument builders and custom argument definitions. |
| Flags | namespace | Built-in flag builders and custom flag definitions. |
| Constraints | namespace | Flag relationship constructors. |
| Command | class | Base class for executable CLI commands. |
| Config | class | Loaded command, topic, plugin, and environment configuration. |
| Plugin | class | Plugin package loader and command provider. |
| Parser | namespace | Standalone argv parser, validation, and flag usage helpers. |
| Interfaces | namespace | Public configuration, parser, plugin, hook, theme, and error types. |
| Hook | type | Typed lifecycle hook function and event result vocabulary. |
| Help | class | Default command and topic help renderer. |
| HelpBase | class | Abstract help renderer contract. |
| CommandHelp | class | Formatter for one command's help. |
| HelpFormatter | class | Shared help sections and rendering operations. |
| execute | function | Load and run a CLI from a directory or load options. |
| run | function | Dispatch argv to version, help, or command execution. |
| flush | function | Wait for pending terminal output. |
| handle | function | Handle a command error asynchronously. |
| Errors.error | function | Log or raise a structured CLI error. |
| Errors.exit | function | Raise an exit error with a code. |
| Errors.warn | function | Emit a warning. |
| Errors.handle | function | Handle an error from a CLI entry point. |
| Errors.CLIError | exception | User-facing CLI error with exit metadata. |
| Errors.ExitError | exception | Process-exit error carrying a code. |
| Errors.ModuleLoadError | exception | Module discovery or loading error. |
| Args.custom | function | Build a custom argument definition. |
| Args.boolean | constant | Boolean argument definition. |
| Args.integer | constant | Integer argument definition with bounds. |
| Args.directory | constant | Directory argument definition. |
| Args.file | constant | File argument definition. |
| Args.url | constant | URL argument definition. |
| Args.string | constant | String argument definition. |
| Args.option | function | Choice-restricted argument definition. |
| Flags.custom | function | Build a custom option flag definition. |
| Flags.boolean | function | Boolean flag definition. |
| Flags.integer | constant | Integer flag definition with bounds. |
| Flags.directory | constant | Directory flag definition. |
| Flags.file | constant | File flag definition. |
| Flags.url | constant | URL flag definition. |
| Flags.string | constant | String flag definition. |
| Flags.version | function | Built-in flag that prints the user agent and exits. |
| Flags.help | function | Built-in flag that renders help and exits. |
| Flags.option | function | Choice-restricted flag definition. |
| Constraints.flag | function | Require or relate one named flag. |
| Constraints.flags | function | Relate a set of named flags. |
| Constraints.combinationOf | function | Build a composite flag relationship. |
| Parser.parse | function | Parse argv using argument and flag definitions. |
| Parser.validate | function | Validate parser input/output relationships. |
| Parser.flagUsages | function | Produce display names and descriptions for flags. |
| Help.getHelpFlagAdditions | function | Read configured help aliases. |
| Help.normalizeArgv | function | Normalize command identifiers in argv. |
| Help.standardizeIDFromArgv | function | Derive a standardized command ID. |
| Help.loadHelpClass | function | Load the configured or default help class. |
| getLogger | function | Return the logger for a namespace. |
| settings | object | Global debug, column, transpilation, and performance settings. |
| Settings | type | Shape of the global settings object. |
| toConfiguredId | function | Convert a standardized ID to the configured separator. |
| toStandardizedId | function | Convert a configured ID to colon notation. |
| ux | object | Terminal action, color, output, error, exit, and warning helpers. |

### CLI Entry Points

The package does not provide a standalone console script. A generated CLI invokes `execute`, `run`, or `Command.run` from a Node.js entry file; `node` module invocation is not required by this specification.

## Appendix A: Environment

- The working environment must run Node.js 22 on Debian Linux with npm available.
- The environment must provide TypeScript 5.7.2, tsx 4, and Vitest 4 as preinstalled JavaScript tooling.
- The target `@oclif/core` package must not be preinstalled in the working environment.
- The project must provide a root `package.json` with package metadata and expose every module entry point shown in Import Surface after `npm install`.
- The project must declare every additional runtime or build dependency in `package.json` so npm installs it during setup.
- During behavioral checks, the container must be disconnected from all networks; command fixtures, hooks, and plugin packages must use temporary local files.

## Appendix B: Assessment Notes

Assessment checks import only the documented module entry points. They exercise standalone argument and flag parsing, command execution, configuration and plugin discovery, hook ordering and failures, help and version dispatch, structured errors, identifier conversion, logger and UX projections, and integrations that compose those views over a local command graph. Checks compare typed values, hook results, exit metadata, and state transitions without requiring private module layout, exact text wrapping, network services, or excluded performance and vendor surfaces.
