# Test Taxonomy

Use this skill when an upstream repository or benchmark does not already
separate tests into the layers needed by SWE-E2E.

## Layer Definitions

### Atomic

Tests one primitive or one public surface in isolation.

Good examples:

- parser accepts one valid expression
- config loader reads one file
- CLI `--help` exits successfully
- serializer round-trips one object

Atomic tests should not set up a full product workflow or assert multiple
derived views.

### Integration

Tests two or more components working together in one bounded workflow.

Good examples:

- create a record through CLI, then query it through the API
- load config and render one generated artifact
- mutate a database and export one report
- parse a file tree and build an index

Integration tests may cross modules, but should still focus on one workflow.

### System/E2E

Tests cross-view consistency over a shared fact source.

Good examples:

- after create/update/delete, CLI list, JSON export, stats, and persistent DB
  agree
- generated paths, rendered contents, hooks, and replay cache agree on the same
  template context
- workflow history, queue status, task detail, logs, and retry counters agree
- notebook files, backlink graph, tag list, and search results agree

System tests should require multiple projections to stay consistent. A single
final output check is not enough.

## Classification Procedure

For each upstream test:

1. Record test id, file, and name.
2. Identify setup operations.
3. Identify asserted surfaces.
4. Identify whether it uses private implementation details.
5. Assign one layer: atomic, integration, system, or drop.
6. Record a short reason.

Use `drop` when a test depends on private internals, non-hermetic services,
undefined exact formatting, platform-specific behavior, or source-only details.

## Output Table

Store the classification in `wip/{task}/oracle_candidates/test_taxonomy.csv`
with columns:

```text
test_id,file,name,layer,keep,reason,requires_public_packet_change
```

## Audit Questions

- Could a candidate pass this test by implementing one function in isolation?
  If yes, it is probably atomic.
- Does this test require multiple modules to agree on the same fact source?
  If yes, it is integration or system.
- Does it compare at least three public projections of the same state?
  If yes, it is a strong system/E2E candidate.
- Is the expectation invisible from public behavior?
  If yes, drop or revise it.

