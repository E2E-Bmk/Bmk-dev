# Fixture Discrimination — clauses whose text names the discriminator

**Status:** additive guidance, drafted 2026-08-22 from three field instances.
Does not amend `ORACLE_STANDARD.md` or `QUALITY_GATE.md`; see
[Interaction with 3d](#interaction-with-quality_gate-3d) for one conflict that
needs an owner's decision rather than mine.

## The failure mode

A clause is verbatim-PASS. A test covers it. The test is green. The clause is
still unpinned, because **the fixture cannot tell the two readings apart.**

This is distinct from the failure modes already tracked:

| already tracked | this one |
|---|---|
| unpinned arm — rule has two branches, test pins one | fixture is too plain to *separate* the branches |
| broken tool — differ produces false positives | tools are silent; nothing is wrong to detect |
| widened spec — test asserts what spec never declared | spec declares it fine; the test just can't see it |

Green tells you nothing here. Neither does clause coverage: the clause has a
test, the test passes, and an implementation with the wrong behaviour also
passes. The suite cannot see the question it was written to answer.

## The procedure

Mechanical, and it does not search for absence:

1. **Grep the clause text for a qualifying phrase** — wording that names a
   property the input must have. In practice these read as `including ...`,
   `within the ...`, `across a ...`, `at an internal ...`, `when the ... is
   non-ASCII`, or any adjective that narrows the domain.
2. **Identify which fixture satisfies that property.** Name the actual fixture,
   not the domain it is drawn from.
3. **If no fixture satisfies it, the clause is unpinned** regardless of what the
   suite reports. Fix the fixture, not the assertion.
4. **Prove the fixed test can fail.** Write the wrong reading into the assertion
   and watch it go red. A test that cannot fail is worth the same as a fake zero.

Step 1 is why this is cheap. Every instrument that has failed on this project
failed trying to detect something that was not written down. Here the
discriminator *is* written down — in the clause, in words. You are grepping for
a phrase that is present, not inferring an absence.

## The dangerous shape: random sampling

**A random-sampling test is the most dangerous shape, because it is nominally
over the right domain and still misses the one point the clause named.** It
looks more rigorous than a hand-picked case and is strictly worse at the job the
clause assigned it.

`CROP-SLICE-013` is the worked example: the test drew 24 pseudo-random offsets
from a multi-leaf document — right domain, right size, defensible construction —
and the clause said `including n at an internal leaf boundary`. A few thousand
boundaries, 24 draws, so it hit one essentially never.

When a clause names a specific point, **enumerate that point explicitly.** Keep
the sampling if it earns its place, but add the named case beside it, and guard
the enumeration so it fails loudly if the fixture later shrinks:

```rust
assert!(chunks.len() > 1, "fixture must span more than one chunk");
// ... walk every internal boundary ...
assert!(internal > 0, "fixture must have an internal boundary to test");
```

Without those guards, someone tidying a fixture in two months silently empties
the loop and the suite stays green. That is how this class of hole gets
reintroduced.

## Worked examples

### 1. crop-rope-001 — `CROP-NOTE-006` "within the chunk"

The clause says the char-boundary panic reports the offset *within the chunk*
and prints that chunk. Three readings compete: chunk-scoped, leaf-scoped,
rope-scoped. crop's leaves hold **two** chunks, so leaf and chunk give different
answers — but only on a rope big enough to have a multi-chunk leaf. Every
existing fixture was small, where all three readings coincide.

The discriminating fixture: 3-byte characters, long enough to span several
leaves, and the probe targets the **second chunk** — the right half of the first
leaf. Rope-scoped reports the absolute offset and quotes the whole rope;
leaf-scoped reports the same absolute offset (leaf 0 starts at 0) and quotes a
two-chunk leaf; only chunk-scoped reports `byte offset 1` and quotes one chunk.

Two negative controls, both required:

- assert the rope-scoped reading → red, `byte offset 1 … (bytes 0..3) of "、みんな…"`
  against `byte offset 1024 … (bytes 1023..1026) of "こんにちは…"`
- **hold the offset axis fixed, swap only the quoted text for the leaf** → red,
  with a byte-identical failure prefix

The second control is the one that matters. Without it, "passed first try" is
equally consistent with a test that only ever checked the number.

### 2. crop-rope-001 — `CROP-SLICE-013` "at an internal leaf boundary"

Above. Random sampling over the right domain, missing the named point.

### 3. gix-ref-store-001 — precomposition, reported independently

Precomposition tests could not distinguish two candidate readings because every
fixture name was ASCII, making precomposition the identity. Both readings pass.
Same signature: the clause names the property (non-ASCII, decomposable), no
fixture has it.

Three instances, three clauses that spell out the required property, three
fixtures that lacked it. Found hours apart on unrelated crates.

## What does *not* qualify

Two nearby tests were checked against the same criterion and cleared — worth
recording so the procedure is not read as "rewrite every fixture":

- a graphemes test asserting **both** `any(Owned)` and `any(Borrowed)`: a
  too-small fixture fails the `Owned` half rather than passing quietly, so the
  test already self-guards
- a builder test using a `>2048 B` document: genuinely spans leaves

A fixture that would *fail* when it stops discriminating is fine. The hazard is
a fixture that goes *green* when it stops discriminating.

## Interaction with QUALITY_GATE 3d

`QUALITY_GATE.md` 3d, `ORACLE_STANDARD.md` §五 行为纯粹性, and
`dev/skills/test-filter/SKILL.md` (lines 27, 150, 305, 308) all prohibit
asserting exact exception/panic message text. The stated rationale is that
**message wording is an implementation detail** — a correct reimplementation
with different internals would fail such a test.

That rationale does not hold when the spec makes the wording contractual, and on
crop-rope-001 it does not:

- the spec's Error Semantics section states *"The message formats are exact"*
- the template is a pinned clause (`CROP-ERR-007`), as is its scope
  (`CROP-NOTE-006/007`)
- the Rust dummy gate **forces** it: a bare `#[should_panic]` passes against an
  `unimplemented!()` stub, so every panic test must carry
  `expected = "<exact string>"` or it contributes nothing to discrimination

24 tests in that oracle pin exact declared message text for these reasons.

**The distinction to apply:** *the spec declares this exactly* versus *the spec
describes this loosely*. Pinning a declared format is holding an implementer to
a clause. Pinning an undeclared format is over-constraint, and 3d is right about
it. Draw the line before writing the test, not after.

**Unresolved:** whether 3d should carry that qualifier, or whether the Rust
dummy-gate requirement should be named as an explicit exception, is a change to
a cross-task standard. It is flagged here, not decided here. Note the existing
prohibitions are written in Python idiom (`str(e)`, `pytest.raises`, `caplog`)
and may predate the Rust tasks.
