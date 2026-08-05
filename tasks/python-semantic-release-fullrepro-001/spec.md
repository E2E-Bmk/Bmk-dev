# Python Semantic Release Specification

## Product Overview

Python Semantic Release (PSR) determines semantic versions from a Git repository's
documented commit history and projects that decision into version declarations,
changelog content, release commits, and Git tags. Its public command line interface
also reports the current release, the next release, and the configured tag form.

The central state is a local project containing a `pyproject.toml` or JSON release
configuration, a version declaration, a changelog file, and Git history. Conventional
commit messages provide the primary change descriptions. The same parsed history drives
the version bump and the human-readable release history.

## Scope

This specification covers the installed package version, public `Version` and
`LevelBump` exports, generated TOML and JSON configuration, CLI help, conventional
commit parsing, patch/minor/major and prerelease decisions, custom tag formats,
matching release-history lookup, JSON configuration loading, version stamping,
version-variable replacement, changelog rendering, no-op and strict modes, and local
Git commit/tag projections.

The behavior is exercised with local temporary Git repositories. The test data uses
fixed identities, dates, branches, locale, timezone, and Git configuration. Assertions
focus on public values, file state, Git state, and selected changelog entries.

## Public Import Surface

The installed distribution exposes `semantic_release.__version__`, `semantic_release.Version`,
and `semantic_release.LevelBump`. `python -m semantic_release` is the command execution
surface used for release operations. The package metadata reports version `10.6.1` for
the fixed source revision.

## Product State Model

A project starts with a version declaration and a matching semantic version tag. New
commits are added after that tag. A conventional `fix` or `perf` commit requests a
patch bump, `feat` requests a minor bump, and a `BREAKING CHANGE:` paragraph requests
a major bump. Documentation, chores, unknown messages, and other non-release changes
do not create a release under the default parser configuration.

The next version may be projected without changing the repository. A release operation
can then update `pyproject.toml`, configured version-variable files, and the changelog,
create a release commit, and create a configured Git tag. A JSON release file provides
the same semantic-release settings beneath its `semantic_release` key. A custom tag
format determines both release-history matching and the next tag projection.

## Error Semantics

Invalid configuration, an invalid release context, or a strict-mode condition produces
a non-zero CLI exit status. Strict mode treats no-release history and a non-release
branch as failures; ordinary mode leaves the project unchanged for those cases.

The default parser accepts documented conventional commit forms and represents an
unrecognized subject as non-release history. A malformed or unsupported command is
reported through the CLI's non-zero result. Exact diagnostic wording is not part of
this contract.

## Cross-View Invariants

- `version --print` equals the version written to the configured project declaration.
- `version --print-tag` equals the Git tag created by a matching local release.
- Version-variable replacements agree with the project declaration after a release.
- The highest matching release tag supplies the release-history baseline.
- A custom `tag_format` is used consistently for history lookup and tag creation.
- Changelog sections reflect the commit type, scope, description, breaking changes,
  release notices, and configured exclusions represented in the same history.
- `--noop` leaves version files, changelog content, commits, and tags unchanged.
- `--no-commit`, `--no-tag`, and `--no-changelog` suppress only their documented local
  projections while retaining the other requested projections.
- A printed projection and a subsequent local release agree on the resulting version.

## Representative Workflows

To inspect a planned release without changing a repository:

```text
python -m semantic_release version --print
python -m semantic_release version --print-tag
```

To apply a local release while avoiding publishing and build execution:

```text
python -m semantic_release version --no-push --no-vcs-release --skip-build
```

To inspect the last matching release:

```text
python -m semantic_release version --print-last-released
python -m semantic_release version --print-last-released-tag
```

## Non-Goals

- Publishing commits, tags, assets, or release notes to a remote service.
- Credentials, tokens, environment-secret handling, or remote service APIs.
- Build tools, package uploads, network services, and wall-clock release metadata.
- Private implementation modules, source-test imports, and exact logger formatting.
- Full coverage of every built-in parser, custom parser loading, monorepo release groups,
  or remote VCS behavior.
- Full console snapshots; only stable command results and selected content are compared.

## Invocation Protocol

Each case runs from a fresh temporary directory with a local Git repository initialized
on the `main` branch. Repository configuration is set locally for identity, signing,
line endings, hooks, and detached-head advice. Commit author and committer dates are
fixed. Commands run through the installed package using `python -m semantic_release`.
Local filesystem-only release context is used where PSR requires remote configuration;
no command performs a push or remote publication.

## Environment

Reference execution uses Python 3.10 and Python 3.11 on Linux without network access.
The target package is not pre-installed in the base environment; the reference
environment provisions `python-semantic-release` from the fixed local source revision.
The test runner requirements are `pytest`, `pytest-json-report`, and
`python-semantic-release`. Locale is `C.UTF-8`, timezone is UTC, and Git system/global
configuration is disabled.

## Evaluation Notes

The cases are split into atomic public projections and integration workflows. Atomic
cases isolate one documented CLI, parser, version, configuration, or history behavior.
Integration cases connect commit history to version output, changelog content, stamped
files, release commits, tags, and no-op or strict-mode outcomes.

Assertions use parsed JSON for generated configuration, exact version/tag values,
Git-derived lists, file contents, and stable changelog phrases. Temporary paths,
commit hashes, remote links, logging verbosity, and full console layouts are not
compared.
