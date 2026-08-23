# Wireit Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`wireit` is a Node.js script runner that upgrades package-manager scripts into a dependency-aware local build graph. A project declares script behavior in the `wireit` object of `package.json`, replaces the corresponding `scripts` command with the `wireit` executable, and then keeps using package-manager commands such as `npm run build`, `pnpm run build`, `yarn build`, or `node --run build`.

The system projects the same package graph through command execution, dependency ordering, extra argument forwarding, file and lockfile fingerprints, output cleanup, local cache lookups, failure propagation, CLI logging categories, and a JSON Schema for `package.json` editing.

## Non-Goals

- This specification does not require network access, registry publishing, remote Git hosting, or remote cache service access.
- This specification does not require GitHub Actions cache uploads, downloads, reservation behavior, chunking behavior, or cache protocol compatibility.
- This specification does not require watch mode, filesystem event watching, polling reruns, persistent process loops, or debounce behavior.
- This specification does not define service scripts, service readiness, service restarts, service output policy, or service process lifetime.
- This specification does not require a VS Code extension runtime, language-server protocol transport, marketplace packaging, or editor UI rendering.
- This specification does not define private TypeScript modules, private helper classes, private data files below `.wireit`, internal event object names, or dependency versions.
- This specification does not define exact human-readable log text, ANSI color sequences, dynamic terminal redraw timing, stack traces, warning wording, or temporary filename choices.
- This specification does not require support for package managers beyond npm, pnpm, yarn, and `node --run`.
- This specification does not require Windows-specific command shell behavior beyond portable path handling described for configuration globs.
- This specification does not define behavior for scripts that mutate undeclared inputs, undeclared outputs, or external services without declaring the corresponding files, outputs, package locks, or external environment variables.

## Representative Workflows

### Run A Dependent Build

```json
{
  "scripts": {
    "build": "wireit",
    "bundle": "wireit"
  },
  "wireit": {
    "build": {
      "command": "tsc",
      "files": ["src/**/*.ts", "tsconfig.json"],
      "output": ["lib/**"]
    },
    "bundle": {
      "command": "rollup -c",
      "dependencies": ["build"],
      "files": ["rollup.config.json", "lib/**/*.js"],
      "output": ["dist/bundle.js"]
    }
  }
}
```

Running `npm run bundle` must analyze `bundle`, run `build` before `bundle`, skip fresh scripts when their fingerprints and outputs have not changed, and return a failing process status when any required script fails.

### Forward Arguments To A Script Command

```sh
npm run build -- --verbose
node --run build -- -- --verbose
```

Arguments after the package-manager separator must be forwarded to the configured `command`. Arguments interpreted as Wireit options must affect Wireit itself, and unrecognized Wireit arguments before the separator must not be forwarded silently.

### Reuse A Local Cache Entry

```json
{
  "scripts": {
    "test": "wireit"
  },
  "wireit": {
    "test": {
      "command": "node test.js",
      "files": ["test.js", "src/**"],
      "output": []
    }
  }
}
```

When local caching is enabled, a previously successful run with the same fingerprint must let the script complete successfully without re-running the command. When an input file, command string, extra argument, package lock, external environment value, clean setting, output pattern, platform, architecture, Node version, or cascade-relevant dependency fingerprint changes, the next run must not reuse the stale result.

## Package Configuration And Graph Analysis

Configuration analysis turns package manifests into a validated script graph rooted at the invoked package-manager script.

**Script declarations.** A script in `package.json` must be a Wireit script when its value is exactly `wireit`, `yarn run -TB wireit`, or a relative path to `node_modules/.bin/wireit` using the package-manager platform form. When a script is configured in the `wireit` object and is directly invoked from the `scripts` object, the corresponding `scripts` value must be a Wireit script. A `wireit` entry with no matching `scripts` entry must be valid only as a dependency target.

**Command and pass-through scripts.** When `wireit.<script>.command` is a non-empty string, the script must execute that shell command after its dependencies are complete. When a Wireit entry omits `command`, the script must act as a pass-through node whose dependencies and files still participate in graph analysis. If a pass-through script is the executable root and no dependency produces an executable outcome, the invocation must report a no-command failure.

**Dependency references.** A dependency string without a colon must refer to a script in the same package. A dependency string of the form `<relative-path>:<script-name>` must resolve the package at the relative path from the declaring package, and cross-package references must start with `.`. Object dependencies must contain `script` and must treat omitted `cascade` as enabled. Duplicate dependency references from one script must report a duplicate-dependency failure.

**Validation boundaries.** If a referenced `package.json` is missing, invalid JSON, lacks a `scripts` object where one is required, lacks the referenced script, has a non-object `wireit` entry, or contains a dependency cycle, graph analysis must fail before executing commands. If a property has the wrong JSON type, an empty string where a non-empty string is required, a dependency object without `script`, or an invalid dependency reference, graph analysis must fail before executing commands.

**Package manager context.** The CLI must determine the package directory from package-manager environment variables when present, otherwise by walking upward from the current directory until it finds `package.json`. If no package directory is found, the script name is unavailable, or the command was launched through `npx`, the invocation must fail as an incorrect launch. The `node --run` package-json path variable must be accepted as a package context.

## CLI Invocation, Options, And Environment

The CLI maps package-manager behavior, environment variables, and Wireit options into one deterministic invocation.

**Entry command.** The executable command is `wireit`. It must run as the command installed in package `scripts`, not as an independent task selector. When invoked successfully, the selected script must be the current package-manager lifecycle script name.

**Argument forwarding.** For npm, Wireit options before the separator must be read from npm configuration environment variables, and argv tokens must be forwarded according to npm's package-script rules. For pnpm, modern yarn, and `node --run`, Wireit must forward only tokens after the separator to the script command. For classic yarn, Wireit must use `npm_config_argv` when it is present and valid, and it must fall back to process argv with a warning when that metadata is absent or not usable.

**Execution controls.** `WIREIT_PARALLEL` must accept a positive integer, `infinity`, the empty string, or absence. Absence and the empty string must select twice the logical CPU count. Invalid non-empty values must fail before graph execution. `WIREIT_FAILURES` must accept `no-new`, `continue`, `kill`, or absence. Absence must select `no-new`; invalid values must fail before graph execution.

**Cache and logger controls.** `WIREIT_CACHE` must accept `local`, `none`, or absence. Absence must select `none` when `CI` is exactly `true`, otherwise local caching. Invalid cache values must fail before graph execution. `WIREIT_LOGGER` must accept `quiet`, `quiet-ci`, `simple`, `metrics`, or absence; absence must select a quiet logger for interactive output and quiet-ci for CI or non-TTY output. `WIREIT_DEBUG_LOG_FILE` must add detailed file logging without changing the main logger behavior.

**Child process environment.** A script's `env` object must set string-valued variables for that command only. An `env` entry with `external: true` must not set the variable, but its observed value or configured `default` must affect the script fingerprint. Environment settings must not apply transitively through dependencies unless those scripts declare the same setting.

## Files, Outputs, Freshness, And Local Cache

File declarations describe what affects a script and what the script produces.

**Input and output globs.** The `files`, `output`, and `packageLocks` properties must be arrays of non-empty strings when present. Paths must use forward slashes and must be interpreted relative to the package directory. A leading slash must still refer to the package directory. Input `files` must permit paths outside the package by using relative parent segments; `output` entries must remain inside the package. The order of negated patterns must affect the resulting match set.

**Default exclusions.** Unless `allowUsuallyExcludedPaths` is `true`, both input and output matching must exclude `.git/`, `.hg/`, `.svn/`, `.wireit/`, `.yarn/`, `CVS/`, and `node_modules/`. Hidden files must still match normal `*` and `**` patterns when they are not excluded by those default directories.

**Fingerprint inputs.** A script fingerprint must include the command string, extra arguments, clean setting, output patterns, hashes of matching input files, hashes of configured package lock files in the package and its parents, configured environment values, platform, CPU architecture, Node version, and transitive dependency fingerprints whose dependency edge has cascade enabled. A dependency with `cascade: false` must not contribute its full fingerprint to the dependent script, so the dependent must rely on explicitly declared file inputs for dependency outputs it consumes.

**Freshness.** When `files` or `output` is absent, the script must run because Wireit lacks enough information to prove freshness. When both are present and the current fingerprint and outputs match the previous successful run, the script must be reported fresh and its command must not execute. Empty `files` or empty `output` arrays must represent a known empty set rather than an unknown set. File content must affect freshness; a modified timestamp without content change must not by itself make a script stale.

**Output cleaning.** When `output` is present, `clean` omitted or `true` must delete matching outputs before command execution and before cache restoration. When `clean` is `if-file-deleted`, output deletion before execution must occur only if a previous input file has been deleted; cache restoration still must clean first. When `clean` is `false`, command execution must not pre-delete outputs, but cache restoration still must replace affected outputs.

**Local cache.** Local caching must use package-local `.wireit` storage. A script whose previous successful run has the same fingerprint and declared outputs must restore outputs from local cache instead of executing when local cache is enabled. A script with `output: []` must still be cacheable as a successful no-output result. Cache restoration must preserve file contents, directories, and symlinks according to the declared output set. When `WIREIT_CACHE=none`, command execution must not read from or write to the local cache.

## Execution, Parallelism, And Failures

Execution turns a valid graph into commands, statuses, and process exit state.

**Ordering and concurrency.** A script must start only after all dependencies that affect it have completed successfully. Independent scripts whose dependency constraints are satisfied must run concurrently up to the `WIREIT_PARALLEL` limit. Simultaneous invocations of the same script must serialize when that script declares output files; when `output` is an empty array, that serialization restriction must be removed.

**Command execution.** Commands must run as package-manager scripts with package dependency binaries available on `PATH` according to the starting package-manager behavior. Extra arguments must be appended to the configured command. Standard output and standard error from commands must be passed through according to the selected logger category, and failure output must remain observable.

**Failure modes.** When a command exits with a nonzero status or signal, the overall invocation must eventually exit with a nonzero status. In `no-new` mode, already running scripts must finish and no new scripts must start after the first failure. In `continue` mode, unaffected scripts must still start and scripts that depend on a failed script must not start. In `kill` mode, running scripts must be terminated and no new scripts must start.

**Cancellation.** When the Wireit process receives SIGINT or SIGTERM, it must stop starting new scripts, terminate running scripts, and exit with a nonzero status when the interruption prevents successful completion.

**Metrics and logs.** The `metrics` logger must include a final summary projection after execution. Quiet loggers must suppress routine successful command output except where command failure requires passthrough. The contract covers categories and status outcomes, not exact terminal layout.

## Package JSON Schema Projection

The package includes a public schema file that documents the scoped `wireit` contribution to `package.json`.

**Schema entry.** The file `wireit/schema.json` must be present in the package and must validate the `wireit` object in `package.json` using JSON Schema draft-07. The root package JSON object must permit properties unrelated to Wireit.

**Schema properties.** The schema must describe `command`, `dependencies`, `dependencies[].script`, `dependencies[].cascade`, `files`, `output`, `clean`, `env`, `env.*.external`, `env.*.default`, `packageLocks`, and `allowUsuallyExcludedPaths`. The schema must reject empty strings in non-empty string fields and reject non-array values for list fields.

**Schema alignment.** Values accepted by the schema for the scoped public configuration fields must be values graph analysis accepts or reports through the same documented validation boundary. Values rejected by the schema for scoped public configuration fields must correspond to invalid package configuration rather than runtime failure after command execution starts.

## State Model

The core state is a package-script graph rooted at the currently invoked package-manager script. Each node contains the declaring package directory, script name, command or pass-through status, dependency edges, file globs, output globs, clean policy, environment policy, package lock policy, fingerprint, freshness result, cache result, execution result, and failures.

The public projections of this state are:

1. The process exit status and command side effects produced by `npm run`, `pnpm run`, `yarn`, or `node --run` when the script command is `wireit`.
2. The package graph projection defined by `package.json` `scripts` and `wireit` objects across one package or relative package dependencies.
3. The filesystem projection consisting of declared inputs, declared outputs, package locks, `.wireit` metadata, and local cache contents.
4. The execution projection consisting of running commands, dependency ordering, parallelism limits, failure mode decisions, and cancellation behavior.
5. The schema projection over the same public configuration keys and dependency references.

## Error Semantics

| Condition | Required result |
|---|---|
| Wireit is launched without a package directory, without a package-manager script name, or through `npx` | The invocation must fail before graph execution. |
| `WIREIT_PARALLEL`, `WIREIT_CACHE`, `WIREIT_FAILURES`, or `WIREIT_LOGGER` has an unsupported value | The invocation must fail before graph execution. |
| A referenced package JSON file is missing or has invalid JSON | Graph analysis must fail before command execution. |
| A direct Wireit script has no matching valid `scripts` entry | Graph analysis must fail before command execution. |
| A dependency references a missing script or missing package | Graph analysis must fail before command execution. |
| The dependency graph contains a cycle | Graph analysis must fail before command execution. |
| A configuration property has an invalid type, empty disallowed string, or invalid dependency shape | Graph analysis must fail before command execution. |
| A script command exits nonzero or by signal | The invocation must report the script failure and exit nonzero. |
| An expected input or output file disappears during fingerprinting, command execution, or cache restoration | The invocation must report the corresponding file-deleted failure and exit nonzero. |
| Local cache restoration cannot provide the declared outputs for a matching fingerprint | The script command must run or the invocation must report a cache-related failure; it must not report success with missing declared outputs. |

## Cross-View Invariants

1. A dependency declared in `package.json` must affect graph execution order, fingerprint calculation when cascade is enabled, and schema-valid dependency vocabulary for the same script reference.
2. A script that is fresh by fingerprint must skip command execution, leave declared outputs intact, and report a successful invocation status equivalent to a command that ran successfully.
3. A script restored from local cache must produce the same declared output filesystem projection as the successful run that populated the cache, and the script command must not execute during the restore.
4. A changed input file, configured external environment value, package lock, extra argument, platform, architecture, Node version, command string, clean policy, output pattern, or cascade-relevant dependency fingerprint must make the affected script not fresh.
5. A dependency with `cascade: false` must be ignored by the dependent fingerprint and freshness decision unless the dependent declares the dependency output through `files`.
6. Default excluded paths must apply consistently to freshness, output cleanup, local cache capture, local cache restore, and input matching.
7. Extra arguments forwarded from npm, pnpm, yarn, or `node --run` must be included in the script command invocation and in the script fingerprint.
8. A configuration accepted by `wireit/schema.json` for the scoped fields must be analyzable by the CLI unless it refers to missing local packages, missing scripts, dependency cycles, or runtime-only filesystem state.

## Public Interface

### Import Surface

The package is installed as `wireit` and exposes these public entry points:

```ts
// package executable
wireit

// package data file
import schema from "wireit/schema.json" assert { type: "json" }
```

There is no supported programmatic JavaScript or TypeScript module API. Programmatic use is through package-manager invocation of the executable and through JSON Schema consumption.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `wireit` | executable | Runs the current package-manager script according to the `wireit` configuration in `package.json`. |
| `wireit/schema.json` | data file | Provides the JSON Schema for the scoped public `wireit` package JSON configuration object. |
| `package.json#wireit` | configuration object | Declares commands, dependencies, files, outputs, cleaning, environment policies, package locks, and path-exclusion policy for scripts. |

### CLI Entry Points

Console script: `wireit`

| Exit | Meaning |
|---:|---|
| 0 | The selected graph completed successfully, was fresh, or restored required outputs from local cache. |
| 1 | Launch validation, graph analysis, command execution, filesystem freshness, local cache restoration, or cancellation failed. |

The executable must be launched from a package-manager script context. It does not accept a script name positional argument.

## Appendix A: Environment

The working environment runs Node.js 22 on Debian Linux with npm and pnpm available and without network access during behavioral checks. The assessment environment provides TypeScript 5.7.2, tsx 4.19.2, Vitest 4.1.10, Ajv 8, and local temporary filesystem support. The target `wireit` package is not preinstalled from a registry.

The project must provide a root `package.json` with `type: "module"`, a `bin` entry exposing `wireit`, the packaged `schema.json` file, and every runtime dependency needed by the executable. Dependencies must be declared in `package.json` so npm installs them during setup. Command fixtures, package fixtures, cache fixtures, and schema checks must use local files and local processes.

## Appendix B: Assessment Notes

Assessment checks exercise the documented executable and schema file only. They cover package JSON validation, CLI launch context, package-manager argument handling, dependency graph analysis, cross-package dependencies, extra arguments, parallel execution, freshness, output cleanup, local cache restore, failure modes, local environment-variable effects, package-lock effects, and schema alignment. Checks compare structured filesystem state, process statuses, command side effects, and schema validation results without requiring private module imports, exact log wording, real network services, watch loops, service lifecycle behavior, real editor integration, or undeclared internal storage layout.
