# go-git Repository Forks

> **Specification authority:** This document defines the supported public
> behavior of repository forks for this module version.

# Context

## Product overview

go-git projects a local repository through immutable objects, direct and
symbolic references, commit history, configuration, shallow boundaries, an
index, and (for non-bare repositories) a worktree. `Repository.Fork` captures
one coherent local generation into an independent in-memory repository.

A fork is useful for speculative changes, isolated analysis, test fixtures,
and handing a stable repository generation to another component. It uses the
ordinary go-git API after creation; callers do not need a fork-specific reader
or receipt format.

## Non-goals

- A fork is not a continuing replica and receives no later source changes.
- Forking does not fetch, push, contact remotes, invoke a system Git process,
  or initialize submodules.
- The contract does not preserve loose-versus-packed representation, storage
  paths, filesystem timestamps, cache entries, or other private encodings.
- Forking does not make an invalid source repository valid.

# Behavior

## Coherent generation

`Fork` selects one stable source generation. Objects and their identities,
direct and symbolic references, HEAD resolution, configuration, shallow
boundaries, index entries, and worktree observations in the child must agree
with that generation. A child must not combine a reference from one source
generation with index or worktree state from another.

All objects available through the source storer at the selected generation
remain available by the same type and hash in the child, including objects not
currently reachable from HEAD. Commit parent order, tree membership, blob
bytes, annotated tags, branch targets, tag targets, and detached or symbolic
HEAD behavior continue through the ordinary repository API.

For a non-bare source, the index and caller-visible worktree belong to the same
fork. Tracked, staged, unstaged, untracked, and ignored files retain their
ordinary status relationships. Directories, regular-file contents and modes,
and supported symbolic links remain observable. Repository-private `.git`
storage is represented by the child's storer rather than copied into its
worktree.

Configuration and shallow history boundaries continue semantically in the
child. Their public values are preserved without sharing mutable ownership
with the source.

## Independent repository

The returned repository owns an in-memory storer and, when the source is
non-bare, an in-memory worktree. A bare source produces a bare child. The child
is a normal `*Repository`: object lookup, reference and revision resolution,
logs, status, staging, commit, checkout, reset, tags, and configuration use the
existing public APIs.

Source and child are independent generations. Later commits, reference
updates, index changes, worktree edits, configuration changes, or shallow
updates in either repository do not change the other. Repeated forks around
different source generations retain their own histories and worktrees.

## Cancellation and unstable sources

The context must be non-nil. Cancellation is checked before publication and
remains discoverable with `errors.Is`. A nil repository or nil context returns
`ErrInvalidForkRequest` and no child.

If the source keeps changing and no coherent generation can be selected,
forking returns `ErrRepositoryChanged` and no child. A later call starts a new
attempt from current source state. Read or decode failures from the source are
returned as errors; a partial repository is never reported as a successful
fork.

# Contract

## State model

A call progresses through source observation, generation validation, private
child construction, and publication of the returned repository. Only a
successful return publishes the child. The source remains caller-owned and is
not modified by the operation.

The source and each successful child have separate reference, configuration,
shallow, index, object-container, and worktree ownership. Git object hashes
remain equal because object identity is content-derived, not because object
containers are shared.

## Cross-view invariants

1. HEAD, its selected reference, revision resolution, commit lookup, and log
   traversal identify one child history generation.
2. Commit, tree, blob, and annotated-tag views retain canonical object hashes
   and ordered lineage.
3. Index entries, worktree bytes, and both status columns describe one captured
   worktree generation.
4. Configuration values, reference namespaces, and shallow boundaries retain
   their source-generation relationships.
5. A bare source remains bare; a non-bare source exposes an independent normal
   worktree.
6. A later change in source or child cannot change any existing observation in
   its sibling generation.
7. Cancellation, invalid input, unstable observation, or source read failure
   never publishes a partial child.

# Reference

## Public interface

The feature is additive to the root package.

```go
import "context"

var ErrInvalidForkRequest error
var ErrRepositoryChanged error

func (r *Repository) Fork(ctx context.Context) (*Repository, error)
```

No option type, callback, manifest, receipt, artifact format, service, or
command-line entry point is added.

## Input-generation guidance

Compatibility suites should generate ordinary repository histories and
observe them only through public go-git and go-billy interfaces. Useful
families vary repository shape, reference topology, object reachability,
staging and worktree divergence, configuration and shallow state, bare versus
non-bare ownership, cancellation, repeated forks, and independent changes.

Generated workflows should combine multiple public views rather than encode a
single expected fixture. In particular, history and reference checks should
reconcile with object lookup; index checks should reconcile with worktree
bytes and status; and independence checks should make ordinary changes on both
sides of a fork.

# Meta

## Environment

The evaluation environment is Linux amd64 with Go 1.25.11 and a pinned offline
module closure. Each run uses fresh in-memory storers and filesystems. Network,
credentials, daemons, fixed ports, and a system Git executable are absent.

## Compatibility

The module path remains `github.com/go-git/go-git/v5` at tag `v5.19.2` and
commit `3eeb238da61eb9c7a324f3ee04f990ce89175642`. Existing APIs remain source
compatible. Public repository observations determine compatibility; private
storage representation and traversal order without a documented order do not.
