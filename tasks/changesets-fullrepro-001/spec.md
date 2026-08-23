
# Changesets Release Graph Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`@changesets/*` is a release-graph toolkit that records package changes, validates repository configuration, computes coordinated versions, and applies a local release plan. A changeset is a Markdown document with YAML front matter that names packages and semantic-version bump types, followed by a human-readable summary.

The toolkit presents the same release state through parsing and writing functions, filesystem readers, normalized configuration, dependency-aware release plans, pre-release state, changelog callbacks, and small logging and error utilities. The package graph is local and deterministic; publishing to a registry is a separate concern.

## Non-Goals

- This specification does not require network access, registry authentication, package publishing, or remote Git hosting.
- This specification does not require vendor-specific drivers, hosted services, or a particular package manager beyond the repository metadata supplied to the APIs.
- This specification does not define private modules, private fields, internal helper names, dependency versions, or generated build files.
- This specification does not define exact human-readable error messages, log coloring, snapshot text, changelog whitespace, file ordering, or temporary file names.
- This specification does not require the interactive terminal prompts used by the command-line front end; programmatic APIs and non-interactive local workflows are the contract.
- This specification does not define publishing side effects, registry responses, remote GitHub lookups, or network-backed changelog enrichment.
- This specification does not require rollback after a release-plan file update has partially completed.

## Representative Workflows

### Record And Read A Change

```ts
import { writeChangeset } from "@changesets/write";
import { readChangesets } from "@changesets/read";

const rootDir = "/tmp/release-project";
const id = await writeChangeset(
  {
    summary: "Improve the command output",
    releases: [{ name: "widget-core", type: "minor" }],
  },
  rootDir,
  { format: false },
);

const changesets = await readChangesets(rootDir);
const recorded = changesets.find((item) => item.id === id);
```

The write operation creates the `.changeset` directory when necessary, emits one Markdown file, and returns its identifier. The read operation ignores repository helper Markdown files, parses each remaining changeset, and returns the identifier derived from the filename.

### Validate Configuration And Assemble A Plan

```ts
import { assembleReleasePlan } from "@changesets/assemble-release-plan";
import { defaultConfig } from "@changesets/config";

const packages = {
  rootDir: "/tmp/release-project",
  rootPackage: {
    dir: "/tmp/release-project",
    packageJson: { name: "workspace", version: "1.0.0", private: true },
  },
  packages: [
    { dir: "/tmp/release-project/packages/core", packageJson: { name: "widget-core", version: "1.0.0" } },
    { dir: "/tmp/release-project/packages/app", packageJson: { name: "widget-app", version: "1.0.0", dependencies: { "widget-core": "^1.0.0" } } },
  ],
  tool: { type: "pnpm" },
};

const plan = assembleReleasePlan(
  [{ id: "improve-output", summary: "Improve output", releases: [{ name: "widget-core", type: "minor" }] }],
  packages,
  defaultConfig,
  undefined,
);
```

The assembled plan contains the relevant changesets, one consolidated release record per package, calculated old and new versions, and the current pre-release state. Dependent packages are considered through the supplied package graph and configuration, so a plan is a projection of the whole workspace rather than an isolated file.

### Enter And Exit Pre-Release Mode

```ts
import { enterPre, exitPre, readPreState } from "@changesets/pre";

await enterPre("/tmp/release-project", "next");
const active = await readPreState("/tmp/release-project");
await exitPre("/tmp/release-project");
const pendingExit = await readPreState("/tmp/release-project");
```

Entering writes a pre-release state file with a tag. Exiting changes the state to an exit intent; versioning consumes that intent and removes the state file after the final release is applied.

## Changeset Documents And File Workflows

This section defines the document format and the local filesystem projection used to collect changes.

**Parsing.**

- The `parseChangesetFile` function must accept a Markdown string and return an object with `summary` and `releases` fields.
- A valid changeset must contain a YAML front-matter block delimited by two `---` lines followed by a summary body.
- The front matter must map non-empty package-name strings to one of the version types `major`, `minor`, `patch`, or `none`.
- The returned `releases` array must preserve each package name and version type from the front matter, and the returned `summary` must contain the trimmed body.
- When the input is empty, lacks front matter, contains invalid YAML, has a non-object front matter value, or names an invalid release, the parser must raise an `Error`.
- The default export from `@changesets/parse` must reference the same parser behavior as the named `parseChangesetFile` export.

**Writing.**

- The `writeChangeset` function must accept a `Changeset` object, a root directory string, and optional formatting options, and it must return a promise of a generated identifier.
- A written file must live below `<root>/.changeset/`, use the returned identifier with a `.md` suffix, contain quoted package names and their version types in YAML front matter, and contain the supplied summary after the closing delimiter.
- The writer must create the `.changeset` directory and any missing parent directories before writing.
- When the formatting option is `false`, the writer must not invoke a formatter; when a supported formatter is selected, the writer must pass the new file to that formatter before resolving.
- The generated identifier must be non-empty and suitable for use as one filename component; callers must not depend on its exact text.
- The default export from `@changesets/write` must reference the same writer behavior as the named `writeChangeset` export.

**Reading.**

- The `readChangesets` function must accept a repository root directory and an optional Git reference string, and it must return a promise of `NewChangeset` records.
- The reader must inspect `.changeset/*.md` and `.changeset/pre/*.md` when those directories exist, parse each selected file, and derive `id` by removing the `.md` suffix from its relative filename.
- The reader must ignore dotfiles, `README.md`, and repository instruction files named `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.
- When a `sinceRef` is supplied, the reader must retain only changeset files reported as changed since that reference.
- When `.changeset` does not exist, the reader must reject with an `Error` rather than return an empty collection.
- The default export from `@changesets/read` must reference the same reader behavior as the named `readChangesets` export.

## Configuration And Repository Policy

Configuration turns a permissive JSON document into the normalized policy consumed by release planning.

**Defaults and normalization.**

- `defaultWrittenConfig` must provide defaults for the base branch, registry access, ignore/fixed/linked groups, formatter, internal dependency update policy, commit behavior, and changelog module.
- `defaultConfig` must be the normalized form of `defaultWrittenConfig`, with empty package-name input producing empty expanded groups.
- `validateConfig` must accept an unknown JSON value and a `Packages` object, and it must return `{ config, warnings, errors }` with exactly one of `config` or `errors` populated.
- `readConfig` must read `.changeset/config.json` below the supplied working directory or current directory, obtain package metadata when it is not supplied, and return the same normalized result as `validateConfig`.
- A string `changelog` or `commit` setting must normalize to a two-element module-and-options tuple; a boolean `commit` value of `true` must select the built-in commit generator.
- A boolean `privatePackages` setting must normalize to matching `version` and `tag` flags; an object setting must fill omitted flags with `false`.
- Ignore, fixed, and linked glob expressions must expand against package names before they reach the normalized `Config`.
- Omitted settings must receive documented defaults, while an explicitly supplied `false`, empty array, or empty string must remain an explicit value where the schema accepts it.

**Validation rules.**

- The `access` setting must be `public` or `restricted`.
- The `format` setting must be `auto`, `prettier`, `oxfmt`, `deno`, `dprint`, or `false`.
- The `updateInternalDependencies` setting must be `patch` or `minor`.
- `fixed` and `linked` must be arrays of package-name arrays, and `ignore` must be an array of strings.
- The snapshot policy must contain a boolean `useCalculatedVersion` and an optional non-empty `prereleaseTemplate`.
- Invalid schema input must produce structured error entries with a path and message; repository-policy violations must be returned as errors or warnings rather than silently normalized.
- A valid configuration must expose `changelog`, `commit`, `fixed`, `linked`, `access`, `baseBranch`, `changedFilePatterns`, `format`, `privatePackages`, `updateInternalDependencies`, `ignore`, experimental options, and snapshot settings.

## Release Graph And Version Planning

The release graph combines changesets, package metadata, dependency relationships, grouping policy, and pre-release state into a deterministic plan.

**Dependency graph.**

- `getDependentsGraph` must accept `Packages` and optional dependency-graph options and must return a `Map` from every known package name to the names that depend on it.
- The graph must include the root package when one is supplied and must return an empty map when the package set has no root package.
- When `ignoreDevDependencies` is true, development-only edges must be omitted; when `bumpVersionsWithWorkspaceProtocolOnly` is true, only workspace-protocol ranges must participate in workspace bump propagation.

**Release assembly.**

- `assembleReleasePlan` must accept changesets, packages, normalized config, a pre-release state or `undefined`, and optional snapshot parameters, and it must return a `ReleasePlan`.
- The plan must retain relevant changesets and flatten multiple entries for one package into one release with the highest required bump type.
- Version types must order as `major` above `minor`, `minor` above `patch`, `patch` above `none`; a `none` release must preserve its old version.
- A package selected by a changeset must resolve in `Packages`; an unknown package name must raise an `Error`.
- A changeset mixing ignored and non-ignored packages must raise an `Error`.
- A pre-release state in `pre` mode must exclude changesets whose identifiers begin with `pre/`; an exit state must add patch releases for packages that had a prior pre-release but no regular release.
- Fixed package groups must converge to one compatible version bump and linked package groups must converge to a shared release version according to the configured semver rules.
- A dependent package must be added or upgraded when the changed dependency range would no longer contain the new version, subject to the internal-dependency policy and private-package policy.
- When snapshot parameters are supplied, released packages must receive a prerelease suffix using the configured placeholders; an absent tag must not satisfy a `{tag}` placeholder.
- `getReleasePlan` must load packages, configuration, changesets, and pre-release state from a working directory, optionally filter by a reference, and delegate to the same assembly rules.
- The default export from `@changesets/assemble-release-plan` and `@changesets/get-release-plan` must reference the corresponding named behavior.

**Small graph utilities.**

- `getVersionRangeType` must return the first matching range operator from `^`, `~`, `>=`, `<=`, `>`, or `""` for an unprefixed or otherwise unsupported range.
- `shouldSkipPackage` must return `true` for an ignored package, for a private package when private versioning is disabled, or for a package without a version; it must return `false` otherwise.

## Pre-Release State And Local Application

Pre-release state and plan application turn a computed graph into durable local files.

**Pre-release lifecycle.**

- `readPreState` must read `.changeset/pre.json`, return its parsed `PreState`, and return `undefined` when the file is absent.
- `enterPre` must resolve the repository root, reject when an existing state is already in `pre` mode, and write a `pre.json` state with mode `pre` and the requested tag.
- `exitPre` must reject when no pre-release state exists and otherwise write the same state with mode `exit`.
- Legacy state containing `initialVersions` or a `changesets` list must be migrated by removing obsolete fields, attempting to move each listed changeset file into `.changeset/pre/`, and preserving the state when a listed file is absent.
- `PreEnterButInPreModeError` and `PreExitButNotInPreModeError` must be the library-specific error classes for the corresponding lifecycle violations.

**Applying a plan.**

- `applyReleasePlan` must accept a `ReleasePlan`, `Packages`, normalized config, optional snapshot parameters, and an optional context directory, and it must return the absolute paths of touched files.
- For each release with a new version, the application must update that package's `package.json` while preserving unrelated JSON content and must update dependency ranges according to the plan policy.
- When a release has changelog text, the application must prepend or create `CHANGELOG.md` content under that package directory; when no changelog generator is configured, it must not invent one.
- After a normal release, applied changeset files must be removed; while in pre mode they must move into `.changeset/pre/`; skipped-package changesets must remain when the package is intentionally ignored.
- When a release plan exits pre mode without a snapshot, the application must remove `.changeset/pre.json` and report that path as touched.
- If a release refers to a package absent from `Packages`, the application must reject with an `Error` before changing that package's files.
- The application must return every package manifest, changelog, changeset, and pre-state path that it actually changes, with no duplicate requirement on callers.

## Changelog And Logging Projections

The local projections expose deterministic callbacks and categorized messages for callers that assemble their own release tooling.

**Changelog callbacks.**

- The default export from `@changesets/changelog-git` must provide `getReleaseLine` and `getDependencyReleaseLine` functions.
- `getReleaseLine` must render the first summary line as a bullet, prepend the first seven commit characters when a commit exists, and indent continuation summary lines by two spaces.
- `getDependencyReleaseLine` must return an empty string when no dependencies changed; otherwise it must list updated dependencies and include a commit reference when one exists.

**Messages and errors.**

- The logger must export `prefix`, `error`, `info`, `log`, `success`, and `warn`; each logger function must forward all supplied arguments to its corresponding console channel without changing argument order.
- `GitError` must expose a numeric `code`, `ExitError` must expose a numeric `code`, and both error classes must retain their `Error` identity.
- `PreEnterButInPreModeError`, `PreExitButNotInPreModeError`, and `InternalError` must be constructible as `Error` subclasses.

## State Model

The public state model has one workspace graph and several projections that must agree.

- The core state must consist of a set of package manifests, a root package projection, changeset documents, normalized configuration, dependency edges, release groups, and optional pre-release state.
- The document projection must expose parsed `NewChangeset` records with stable identifiers and summaries.
- The policy projection must expose a normalized `Config` with expanded package groups and resolved defaults.
- The graph projection must expose dependent relationships and a `ReleasePlan` with consolidated releases and calculated versions.
- The filesystem projection must expose updated package manifests, changelogs, changeset moves/removals, and pre-release state files after application.
- The callback projection must expose changelog functions and logger/error categories without exposing private module state.

## Error Semantics

| Condition | Required result |
|---|---|
| Empty, malformed, or semantically invalid changeset text | The parser must raise an `Error`. |
| Missing `.changeset` directory | `readChangesets` must reject with an `Error`. |
| Invalid configuration schema | `validateConfig` must return `config: undefined` and non-empty `errors`. |
| Repository configuration rule violation | `readConfig` or `validateConfig` must return the reported errors and must not expose a usable `config`. |
| Unknown package referenced by a changeset or release | Release assembly or application must raise an `Error` before reporting success. |
| Mixed ignored and non-ignored packages in one changeset | Release assembly must raise an `Error`. |
| Entering pre mode while already in pre mode | `enterPre` must reject with `PreEnterButInPreModeError`. |
| Exiting pre mode while no state exists | `exitPre` must reject with `PreExitButNotInPreModeError`. |
| Snapshot template uses a missing placeholder value | Release assembly must raise an `Error`. |
| Release application cannot resolve a package | `applyReleasePlan` must reject and must not report the unresolved package as touched. |
| A configured changelog or commit module lacks the required callback | The consuming operation must reject with an `Error`. |

## Cross-View Invariants

1. A parsed changeset written by `writeChangeset` and then returned by `readChangesets` must preserve every package release, version type, summary, and generated identifier.
2. A configuration accepted by `validateConfig` and loaded by `readConfig` must expose the same normalized defaults, expanded groups, and policy fields.
3. Every release in a `ReleasePlan` must refer to a package in `Packages`, and every calculated `newVersion` must be compatible with its `type` and `oldVersion`.
4. A dependency edge reported by `getDependentsGraph` must be the edge considered when release assembly decides whether a dependent package needs a release.
5. Fixed and linked package groups must produce mutually compatible release records in the assembled plan, and applying that plan must write the corresponding package versions.
6. A pre-release state written by `enterPre` or `exitPre` must be the state read by `readPreState` until version application consumes it.
7. Applying a release plan must update the same package manifests and changeset files that the plan's touched-file result names.
8. A changeset moved into `.changeset/pre/` during pre mode must be read again by `readChangesets` with an `id` prefixed by `pre/`.
9. The named and default exports of each package must expose equivalent behavior for the same public inputs.
10. A logger call must preserve its arguments and category, and a corresponding error object must remain identifiable through normal `instanceof Error` checks.

## Public Interface

### Import Surface

```ts
import parseChangesetFile from "@changesets/parse";
import { parseChangesetFile as parseChangesetFileNamed } from "@changesets/parse";
import readChangesets from "@changesets/read";
import { readChangesets as readChangesetsNamed } from "@changesets/read";
import writeChangeset, { writeChangeset as writeChangesetNamed } from "@changesets/write";

import {
  readConfig,
  validateConfig,
  defaultWrittenConfig,
  defaultConfig,
} from "@changesets/config";

import assembleReleasePlan, {
  assembleReleasePlan as assembleReleasePlanNamed,
} from "@changesets/assemble-release-plan";
import getReleasePlan, {
  getReleasePlan as getReleasePlanNamed,
} from "@changesets/get-release-plan";
import { applyReleasePlan } from "@changesets/apply-release-plan";
import { enterPre, exitPre, readPreState } from "@changesets/pre";
import { getDependentsGraph } from "@changesets/get-dependents-graph";
import getVersionRangeType, {
  getVersionRangeType as getVersionRangeTypeNamed,
} from "@changesets/get-version-range-type";
import { shouldSkipPackage } from "@changesets/should-skip-package";
import {
  GitError,
  ExitError,
  PreEnterButInPreModeError,
  PreExitButNotInPreModeError,
  InternalError,
} from "@changesets/errors";
import changelogGit from "@changesets/changelog-git";
import {
  prefix,
  error,
  info,
  log,
  success,
  warn,
} from "@changesets/logger";

import type {
  VersionType,
  DependencyType,
  AccessType,
  Release,
  ComprehensiveRelease,
  Changeset,
  NewChangeset,
  ReleasePlan,
  PackageJSON,
  PackageGroup,
  Fixed,
  Linked,
  PrivatePackages,
  Config,
  WrittenConfig,
  ExperimentalOptions,
  NewChangesetWithCommit,
  ModCompWithPackage,
  GetReleaseLine,
  GetDependencyReleaseLine,
  ChangelogFunctions,
  GetAddMessage,
  GetVersionMessage,
  CommitFunctions,
  PreState,
  Package,
  Packages,
} from "@changesets/types";
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `parseChangesetFile` | function | Parses a Markdown changeset into a summary and release records. |
| `readChangesets` | function | Reads and filters changeset files from a repository. |
| `writeChangeset` | function | Writes one changeset file and returns its generated identifier. |
| `readConfig` | function | Reads and normalizes repository configuration. |
| `validateConfig` | function | Validates and normalizes an in-memory configuration value. |
| `defaultWrittenConfig` | constant | Supplies the documented JSON configuration defaults. |
| `defaultConfig` | constant | Supplies the normalized configuration defaults. |
| `assembleReleasePlan` | function | Builds a dependency-aware release plan. |
| `getReleasePlan` | function | Loads repository inputs and builds a release plan. |
| `applyReleasePlan` | function | Applies versions, dependency edits, changelogs, and changeset moves. |
| `enterPre` | function | Enters pre-release mode in a repository. |
| `exitPre` | function | Marks pre-release mode for exit. |
| `readPreState` | function | Reads the current pre-release state. |
| `getDependentsGraph` | function | Builds the reverse dependency graph. |
| `getVersionRangeType` | function | Extracts the leading semver range operator. |
| `shouldSkipPackage` | function | Decides whether a package is excluded from release work. |
| `changelogGit` | object | Provides deterministic Git-oriented changelog callbacks. |
| `prefix` | constant | Provides the logger prefix string. |
| `error` | function | Emits an error-category log message. |
| `info` | function | Emits an info-category log message. |
| `log` | function | Emits a general log message. |
| `success` | function | Emits a success-category log message. |
| `warn` | function | Emits a warning-category log message. |
| `GitError` | class | Represents a Git command failure with an exit code. |
| `ExitError` | class | Represents an intentional process exit with an exit code. |
| `PreEnterButInPreModeError` | class | Identifies an invalid repeated pre-release entry. |
| `PreExitButNotInPreModeError` | class | Identifies an exit request without pre-release state. |
| `InternalError` | class | Represents an internal invariant failure. |
| `VersionType` | type | Enumerates semantic-version release bump types. |
| `DependencyType` | type | Enumerates package dependency fields. |
| `AccessType` | type | Enumerates registry access policies. |
| `Release` | type | Describes a package name and requested bump. |
| `ComprehensiveRelease` | type | Describes a calculated release with old and new versions. |
| `Changeset` | type | Describes a summary and release list. |
| `NewChangeset` | type | Adds a stable identifier to a changeset. |
| `ReleasePlan` | type | Describes changesets, releases, and pre-release state. |
| `PackageJSON` | type | Describes package manifest fields used by planning. |
| `PackageGroup` | type | Describes a group of package names. |
| `Fixed` | type | Describes fixed package groups. |
| `Linked` | type | Describes linked package groups. |
| `PrivatePackages` | interface | Describes private-package version and tag policy. |
| `Config` | type | Describes normalized configuration. |
| `WrittenConfig` | type | Describes user-authored configuration. |
| `ExperimentalOptions` | type | Describes the explicitly supported experimental policy fields. |
| `NewChangesetWithCommit` | type | Adds optional commit metadata to a changeset. |
| `ModCompWithPackage` | type | Combines a release record with package metadata. |
| `GetReleaseLine` | type | Describes a release-line callback. |
| `GetDependencyReleaseLine` | type | Describes a dependency-release-line callback. |
| `ChangelogFunctions` | type | Describes the pair of changelog callbacks. |
| `GetAddMessage` | type | Describes an add-command commit message callback. |
| `GetVersionMessage` | type | Describes a version-command commit message callback. |
| `CommitFunctions` | type | Describes optional commit callbacks. |
| `PreState` | type | Describes pre-release mode and tag. |
| `Package` | interface | Describes a package directory and manifest. |
| `Packages` | interface | Describes the workspace package collection and tool. |

### CLI Entry Points

The `changeset` executable is the local command-line entry point. The `init`, `add`, `status`, `version`, `pre`, and `git-tag` commands operate on the current repository and use the same file and release-graph rules described above. The `publish` command and registry side effects are not part of this specification.

| Command | Required local behavior | Exit behavior |
|---|---|---|
| `changeset init` | Create `.changeset/README.md`, `.changeset/config.json`, and the default configuration. | Return zero after successful creation. |
| `changeset add --empty` | Create an empty changeset document without interactive input. | Return zero after the file is written. |
| `changeset status` | Read local changesets and report the calculated release state; an output path writes a structured JSON projection. | Return non-zero when repository policy reports a missing required changeset. |
| `changeset version` | Assemble and apply the local release plan, including optional ignore and snapshot settings. | Return non-zero when plan assembly or application fails. |
| `changeset pre enter <tag>` | Write pre-release state with the supplied tag. | Return non-zero for an invalid lifecycle transition. |
| `changeset pre exit` | Mark the current pre-release state for exit. | Return non-zero when no pre-release state exists. |
| `changeset git-tag` | Create local tags from package names and versions without publishing packages. | Return non-zero when the local Git command fails. |

## Appendix A: Environment

The working environment runs Node.js 22 on Debian Linux with npm and pnpm available and without network access during behavioral checks. The assessment environment provides TypeScript 5.7.2, Vitest 4.1.10, tsx 4.19.2, `yaml`, `semver`, `valibot`, and `@manypkg/get-packages` as installable dependencies. The target modules listed in Import Surface are not preinstalled from a registry.

The project must declare its package names, ECMAScript module mode, exports, executable entry point, and every runtime dependency in `package.json`. Each module entry point listed above must be reachable after a local install. Local Git operations must use temporary repositories and must not require a network.

## Appendix B: Assessment Notes

Assessment checks cover document parsing and writing, filesystem filtering, configuration defaults and validation, dependency graphs, release-version calculation, fixed and linked groups, pre-release transitions, local plan application, changelog callbacks, logging categories, error classes, and the CLI's local commands. Checks compare structured values, state transitions, and documented files; they do not require private module layout, exact error text, exact log color, remote services, or registry access.
