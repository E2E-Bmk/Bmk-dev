# Which assertions discriminate

**Status:** design note for candidate/task selection. Derived from crop-rope-001, 2026-08-22.
**Companion to:** `FIXTURE_DISCRIMINATION.md` (which asks whether a fixture *can* fail);
this note asks whether a *candidate* can fail, which is a different question with a
different answer.

---

## The headline, which is the opposite of what the aggregate suggests

crop-rope-001 was scored twice. Both runs land in the mid-90s, so the aggregate reads
like a replication of "this task is easy." Split by candidate, it says something worse:

| run | candidate representation | live LOC | atomic | integ | total | rate |
|---|---|---|---|---|---|---|
| `_snapshot_0839_run` | `text: String` + `chunk_boundaries: Vec<usize>` — **flat string** | 2002 | 97/101 | 23/25 | 120/126 | **95.2%** |
| `qwen3.8-max` | `root: Arc<Node>`, real `tree.rs` with `Summary`/`MAX_LEAF`/`MIN_CHUNK` — **actual tree** | 2944 | 97/101 | 21/25 | 118/126 | **93.7%** |
| reference | upstream B-tree @ `d0234ce` | 12947 | 101/101 | 25/25 | 126/126 | 100% |

**The flat string scored higher than the genuine tree.** The oracle does not merely fail
to punish the dumb data structure — it mildly *rewards* it. Any argument that "the task
still measures something, just with a high floor" has to survive that ordering, and it
does not: the ranking is inverted, not compressed.

(The two candidates are independent generations that a second scoring agent wrote to the
same `--output-dir`; the 09:01 run overwrote the 08:51 one, which survives only because it
had been snapshotted. Concurrent writers to one output directory destroy exactly this
comparison by default — it is only available here by luck.)

### A contamination check that came back clean

The overwrite left three gen-1 files in the gen-2 workspace (`rope_slice.rs`,
`rope_builder.rs`, `iter/raw_lines.rs`, 685 lines). Gen-2's `lib.rs` declares
`mod tree/rope/slice/builder/iter/error` and its `iter/mod.rs` sources `RawLines` from
`lines.rs`, so all three are **orphaned modules that rustc never compiles**. The 118/126 is
a clean measurement of gen-2. Worth recording that the check was run, because a chimera of
two candidates would have looked exactly like a valid score.

---

## "Which assertions discriminate" is not a property of the oracle

The tempting move after one run is to read the failures off as *the* structure-sensitive
subset. That inference is wrong, and this task shows why cheaply:

```
failed in BOTH runs (1):   atomic::graphemes_spanning_a_chunk_boundary_are_owned

flat-string only (5):      atomic::assert_invariants_accepts_well_formed_ropes
                           atomic::iterator_types_are_reachable_from_their_declared_paths
                           atomic::the_char_boundary_message_is_scoped_to_the_containing_chunk
                           integration::byte_slices_agree_with_str_slices
                           integration::invariant_9_view_equality_is_view_blind

tree only (7):             atomic::builder_emits_one_chunk_per_leaf
                           atomic::graphemes_inside_one_chunk_are_borrowed
                           atomic::serde_round_trip_preserves_every_measure
                           integration::invariant_8_slicing_and_editing_commute_on_content
                           integration::repeated_inserts_track_a_string_model
                           integration::inserts_of_the_documents_own_text_track_a_string_model
                           integration::repeated_replacements_track_a_string_model

union 13 · intersection 1
```

Two candidates, near-identical scores, **almost disjoint failure sets**. Most failures are
candidate-specific bugs, not signal about the data structure. Discrimination is a property
of the *pair* (oracle × candidate), so a single run's failure list is not a list of
structure-sensitive assertions and must not be treated as one.

Note also that the two atomic scores are both 97/101 while failing *different* tests. Equal
sub-scores are not evidence of the same behaviour.

---

## The one assertion that discriminated against both

`graphemes_spanning_a_chunk_boundary_are_owned` is the only test both candidates failed,
and its shape is the reason:

```rust
let text = "e\u{0301}".repeat(1000);          // 3000 bytes > MAX_LEAF, so >1 chunk
let clusters = r.graphemes().collect::<Vec<_>>();
assert!(clusters.iter().any(|c| matches!(c, Cow::Owned(_))),    "crossing a boundary → reassembled");
assert!(clusters.iter().any(|c| matches!(c, Cow::Borrowed(_))), "inside a chunk → still borrows");
```

It works because it is **two-armed against the representation in opposite directions**. A
flat string has one contiguous buffer, so every cluster borrows and the `Owned` arm fails.
An over-eager implementation that copies every cluster fails the `Borrowed` arm. Neither
arm alone would do it — pinning only `Owned` is satisfiable by "always allocate," pinning
only `Borrowed` by "one flat buffer." The partition has to be *real* to satisfy both at
once.

This is the same two-arm lesson as `spec2repo-clause-two-arm-coverage`, arriving from the
candidate side rather than the clause side. Stated constructively:

> **An assertion that pins only one arm can be satisfied by degenerating in the other
> direction.** Pin `Owned` alone and "always allocate" passes; pin `Borrowed` alone and
> "one flat buffer" passes. Only the conjunction is unsatisfiable without the real
> structure.

Also worth recording: `the_char_boundary_message_is_scoped_to_the_containing_chunk` — added
during the S3A hardening pass under the `FIXTURE_DISCRIMINATION.md` criterion — is one of
the six the flat string failed. It fails because a flat string reports rope-absolute
offsets and quotes the whole rope, where the spec's template is chunk-scoped. That is
empirical confirmation that the greppable-criterion procedure produces assertions with real
discriminating power, not just verbose ones.

---

## The anti-discriminating class: model-tracking tests

The sharpest design finding here. Four tests compare a sequence of edits against a
`String` model (`repeated_inserts_track_a_string_model` and friends).

- The **flat string passed all four**, trivially and necessarily — it *is* a `String` plus
  a derived index, so the test compares the model against itself. The test cannot fail.
- The **tree failed three of them**, because a real structure has to preserve content
  across splitting and rebalancing, and that is genuinely hard.

So this family of tests **actively inverts the ranking**: it is free for the degenerate
representation and costly for the correct one. Three of the four points separating the
tree from the flat string come from exactly here. Model-tracking tests are worth having as
correctness checks, but they must be understood as contributing *negative* discrimination
toward structure, and a task whose difficulty rests on them is measuring the wrong thing.

The general form: **an assertion that a simpler representation satisfies by construction
transfers score from the correct implementation to the degenerate one.**

---

## Screening procedure for future candidates

Before adopting a target, ask — and answer in writing:

1. **Is there an obviously dumber data structure that passes most assertions?** For a rope,
   `String` + a boundary index. For a graph library, an adjacency `Vec` with linear scans.
   For an index, a sorted vector. If you can name it in one sentence, estimate its score
   before building anything.
2. **Which observables in the public API expose the representation at all?** That set is a
   hard ceiling on discrimination — no amount of test-writing gets past it. For crop it is
   narrow: `chunks()`, grapheme `Cow` borrowed/owned, builder chunk emission, and the
   chunk-scoped panic text. Roughly a twentieth of the suite, which is why both candidates
   cleared 93%.
3. **For each such observable, is the assertion two-armed?** One arm is usually satisfiable
   by a degenerate strategy in the other direction. See above.
4. **Classify the expected failures before running:** representation-forcing vs generic
   bug. If the honest count of representation-forcing assertions is single digits against a
   126-test suite, the task will not separate candidates regardless of how it scores.
5. **Prefer behaviour a dumb structure gets *wrong*, not behaviour it gets *right slowly*.**
   The oracle asserts behaviour and cannot see cost; asymptotics are invisible to it. This
   is the root cause for crop: "logarithmic rather than linear" is the entire point of a
   rope and *no* assertion in a behavioural oracle can observe it.

Point 5 is the one to internalise. A task whose real difficulty is **performance** cannot be
graded by a correctness oracle, and crop-rope-001 is the worked example.

---

## Calibration: every valid Rust measurement to date

Before trusting the screen, check it against what has actually been measured. All Rust
scoring runs in `wip/*/eval/runs/`, with the invalid ones marked:

| task | candidate | result | valid? |
|---|---|---|---|
| crop-rope-001 | flat string | 120/126 = **95.2%** | yes |
| crop-rope-001 | real tree | 118/126 = **93.7%** | yes |
| gix-ref-peel-001 | qwen3.8-max, 60-test oracle | 53/60 = **88.3%** | yes, but a *pilot* on the older upstream-only oracle |
| gix-ref-peel-001 | qwen3.8-max, 72-test oracle | 0/72 | **no** — `4/4 batches had collection/report errors`, all `no_report` |
| guppy-…-001 | qwen3.8-max | 0/155 | **no** — `7/7 batches had collection/report errors (invalid score)`, all 155 `no_report` |

**Three valid measurements, all between 88% and 95%.** Not one Rust task has produced a
valid score anywhere near the qualifying bar of 50%. The screen therefore has to explain a
systematic ceiling, not a one-off.

### Three distinct zero-gradient failure modes, not one

crop is only the first. Classifying by *where the gradient vanishes*:

**A — ceiling too high (crop-rope-001).** Difficulty is asymptotic; a behavioural oracle
cannot see cost; the degenerate structure passes nearly everything. Diagnostic: name the
dumb structure and estimate its score.

**B — spec completeness eats the difficulty (gix-ref-peel-001).** Peel's seven failures are
all *wrong-answer* behaviour of exactly the kind the screen calls good — partial-name lookup
precedence (`tags before heads`, `direct refs before heads`, `shortest paths first`), a
multi-space `ref:` parse, malformed packed-refs records, worktree layout. The mechanism is
healthy; there is simply too little of it left once the spec states every rule explicitly.
This is the known tension that spec completeness and task difficulty pull against each
other. Diagnostic: count how many rules a candidate must *infer* rather than transcribe.

**C — floor too low, all-or-nothing (guppy, and a standing Rust risk).** A Rust suite is one
compiled artifact per layer, so a single API divergence is a compile error that zeroes the
entire layer (Mechanism 9). guppy's 0/155 is exactly this, and its own S4 analysis says so:
the score is "编译全灭型的 0，155 条断言同生共死、难度梯度为零" — measuring whether a
candidate can transcribe a large API surface, not whether it can implement behaviour.
`gix-ref-peel-001`'s `task.json` records the same risk unprompted: "Score gradient is closer
to binary than the test count suggests… Inherent to Rust; cannot be fixed by test
selection."

A caveat on guppy's status, stated carefully because it is someone else's call to make.
Its `reference` run is clean (155 passed) and its `dummy` run is clean (`status: ok`, 155
*failed*, zero `no_report`), which does establish that the oracle links against a
spec-faithful stub and that the attainable ceiling is not 0. But the **candidate** run it
qualified on is recorded by the harness as `status: "error"` with
`7/7 batches had collection/report errors (invalid score)` and all 155 tests `no_report` —
the marker that exists specifically to stop `no_report` being counted as `failed`. S4
reasoned the zero was candidate-side (it failed to implement declared traits, so the layer
would not link) and that reasoning is defensible; S4 nonetheless flagged the result as
"满足门禁但 benchmark 信息量低，需显式裁决而非默认通过" and asked for explicit adjudication.
So the qualification rests on an override of a machine invalidation rather than on a clean
measurement. Flagging only — guppy's `PIPELINE_STATE.md` is orchestrator-locked and I have
not touched it.

A and C are opposite poles with the same consequence. **A task can be undiscriminating
because everything passes or because everything fails together**; both produce a number
that looks like a measurement and is not one. Note that C also makes A *invisible*: had
crop's candidates failed to link, both would have scored 0 and the flat-string inversion
would never have surfaced.

### Consequence for the bar

The qualifying rule (`qwen3.8-max` under 50%) implicitly assumes a smooth gradient. Under
mode C the only reachable scores are ~0% and ~90%+, so "under 50%" selects for
*compilation failure*, not for difficulty. guppy is the demonstration: it qualified on a
zero its own analysis had already labelled information-free. **A score should not count as
qualifying unless the suite demonstrated a gradient** — e.g. at least one layer partially
passing. That is a bar-design question and belongs to whoever owns the rule, not to me;
it is recorded here because the screen keeps surfacing it.

---

## The screen applied to nine Rust candidates (specs only, nothing built)

Run 2026-08-22 against `gix-{ref-peel,ref-store,ref-txn,config-file,config-parse,object-parse,odb-dynstore,pack-decode}` and `guppy`, from spec text alone.

**Headline, and it is not what I expected: none of the nine is crop-like.** Not one places
its difficulty in asymptotic cost. Every spec either disclaims performance outright or
converts a perf knob into a non-observable — peel neutralises the mmap threshold ("the
results of `open` do not depend on which side of the threshold the file falls"), txn
disclaims descriptor and memory bounds, guppy says "does not require caching or any
particular performance characteristic." crop's mode A appears to be a one-off, not a
pattern in the pool.

Ranked by the **dumb-structure estimate**, which is a *floor* on what a candidate scores:

| # | task | dumb-structure est. | verdict | oracle today |
|---|---|---|---|---|
| 1 | `gix-object-parse-001` | **20-30%** | GRADEABLE (high) | none |
| 2 | `gix-pack-decode-001` | **25-30%** | GRADEABLE (high) | none |
| 3 | `gix-config-file-001` | **25-30%** | GRADEABLE (high) | 119 tests, gate run |
| 4 | `gix-config-parse-001` | **30-35%** | GRADEABLE (high) | none |
| 5 | `gix-ref-txn-001` | ~35% | GRADEABLE (high) | helpers only |
| 6 | `gix-ref-store-001` | 40-55% | GRADEABLE (high) | 175 tests |
| 7 | `guppy-…-001` | 50-60% | GRADEABLE content / **low confidence in the measurement** | 155, contested |
| 8 | `gix-ref-peel-001` | 60-70%, *strictly dominated* | GRADEABLE (high) | 72; measured 88.3% |
| 9 | `gix-odb-dynstore-001` | ~70% | GRADEABLE (medium) | none |

### Calibrating the estimate against the two things actually measured

The estimate is a floor, and the gap between floor and real-model score is the number that
decides qualification. Two anchors:

- **crop flat string: predicted ~95%, measured 95.2%.** Near-zero gap — but only because
  the candidate *was* the dumb structure.
- **peel: predicted 60-70%, `qwen3.8-max` measured 88.3%.** Gap **+18 to +28 points.**
  (Loose anchor: the estimate was made against the 445-clause spec, the score against the
  older 60-test oracle.)

One usable data point, so treat it as an order of magnitude and not a law. Applying it:
ranks 1-4 land at roughly **45-60%**, straddling the bar; ranks 5-6 at 60-80%; ranks 7-9
at 75-95%. **Only the top four have a plausible path under 50%, and none of them is
comfortably under.** No task in this pool qualifies on difficulty with margin.

Which sharpens the mode-C consequence already recorded below: the only mechanism that
reliably drives a Rust score under 50% is the compile cliff, and it lands on 0%, not 40%.
The pool does not currently contain a task that would qualify *for the right reason*.

### Mode D — the oracle does not assert the gradeable part

A fourth failure mode, and the one this screen actually discovered. A, B and C are
properties of the **spec**. D is a property of the **oracle**: the spec locates real
difficulty in an observable, and no test ever looks at it.

guppy is the worked example, verified by grep rather than taken from a report — `V1`,
`V3`, `V1Install`, `InitialsPlatform`, `add_omitted_packages`, `set_include_dev`,
`platform_features`, `features_only`, `CargoSet::new` each appear 2-6 times in the spec
and **zero** times in `oracle/`. All 24 cargo-simulation tests hard-set `V2`. So the
V1↔V2 divergence — which the spec itself nominates as "the single observable difference
between the resolver versions" — is unscored, and a candidate implementing only V2 loses
nothing.

The reason this matters here: **guppy's clause verification is 294/294 PASS.** Verbatim
clause checking cannot see mode D, exactly as `spec2repo-clause-two-arm-coverage` found
for one-armed rules. A one-line grep of the oracle per spec-declared symbol catches it.

Smaller instances found in the same pass: odb-dynstore's MRU reordering (§7.2, ~5 clauses,
no observable — the one genuinely crop-shaped corner in the whole pool); store's four
cross-view invariants that a single-map implementation satisfies by construction; and
pass-by-construction clauses flagged in config-parse and object-parse.

### Two amendments to the procedure above

**Step 0 — measure the surface gate before asking about difficulty.** A large API catalog
behind a single compilation unit is a *bimodal* scorer: near-0 or near-ceiling, nothing
between. guppy's 358-row catalog across 53 types is why its 0/155 carries no behavioural
signal. Note this is the opposite defect from crop — guppy scores too *low* for the wrong
reason, crop too *high* — and a screen hunting only for the crop shape passes guppy clean.

**Step 6 — dead-clause coverage.** Step 2 asks what the spec exposes; also ask what the
oracle asserts. Grep the oracle for every spec-declared symbol before trusting the ceiling.

**Step 7 — never trust a single Rust score; test for bimodality first.** Added after peel
turned mode C from a prediction into a measurement (below). Cheapest form: same model, ≥3
draws, look at the `status` distribution rather than the pass rates. Mixed `ok`/`error`
means the task is currently measuring the compile cliff and not difficulty at all.

Two rules that follow, both about arithmetic:

- **`status: error` runs must never be averaged in as zeros.** The harness already refused
  to record them as scores; averaging them launders that refusal into a number. Peel's four
  generations average to 22% — which reads as "qualifies" and is meaningless.
- **A valid run and an invalid run are not two samples of the same quantity.** Peel's one
  valid run says 88.3%; the three invalid ones say nothing. The honest report is "n=1".

---

## Mode C, measured: peel's compile cliff

Mode C was a prediction until `spec-check-gixref-a` measured it on peel. Four candidate
generations, same model, same spec, four distinct workspace md5s:

| generation | `Target::id` returns | result |
|---|---|---|
| `qwen3.8-max` (60-test oracle) | `&gix_hash::oid` | 30/32 + 23/28 = **88.3%**, `ok` |
| `…-72-attempt1` | `&ObjectId` | 0/38 + 0/34, `error` rc=101 |
| `…-72-attempt2` | `&ObjectId` | 0/38 + 0/34, `error` rc=101 |
| `…-72` | `&ObjectId` | 0/38 + 0/34, `error` rc=101 |

Three compile failures, one root cause: the oracle writes the gix idiom `&oid` (borrowed),
the candidates returned `&ObjectId` (owned). I checked the fairness question at source
before repeating the conclusion — `spec/api_surface.md` rows 29/30/41/42 declare
`Target::id(&self) -> &oid` and `try_id(&self) -> Option<&oid>`, both marked
non-derivable + include. **The oracle is right, the spec is right, and the candidates
violated a declared row.** A legitimate mechanism-9 zero, not a broken task.

Which is exactly what makes it the cleanest available demonstration of mode C. The
distribution is **88.3 / 0 / 0 / 0** and the mode is selected by a single type alias. It is
not even a stable property of the model: attempt1 got `TargetRef::id -> &'a oid` right while
getting `Target::id` wrong *in the same file*. Verified independently: the three failing
runs each carry `8 no_report / 2 ok / 2 error`, the invalid-run signature.

**The two failure shapes bracket the problem.** crop compresses into a 93-95% band with no
discrimination; peel splits into 88.3/0 with no discrimination. One too blunt, one too
brittle. **No Rust task in this pool has ever produced a score in the 40-60% continuous
range** — that, rather than any ranking, is why nothing qualifies for the right reason.

Gate gap on the same task: `reference-72` exists at 72/72 `ok`, **`dummy-72` does not
exist**. The expanded oracle has a positive gate and no non-vacuity gate.

---

## The missing instrument: a naive-but-compiling implementation

Every dummy gate in this pool is an `unimplemented!()` surface stub. **A stub proves
non-vacuity and nothing else.** crop's killer was not a stub — it was a *working* flat
`String` that compiled, ran, returned plausible answers, and scored 95.2%. No gate in the
pool would have caught it, because no gate contains an artifact of that kind.

The proposal: per task, one **naive-but-compiling implementation** — the dumbest data
structure that satisfies the declared API surface, returning real values rather than
panicking.

Why this specific artifact and not more tests:

1. **It clears the compile cliff on purpose**, so it measures the *floor of the continuous
   band* instead of mode C. A stub and a wrong-typed candidate both score 0 and are
   indistinguishable; a naive implementation that scores 0 means something entirely
   different from one that scores 70.
2. **It converts my nine-way ranking from estimates into measurements.** The table above is
   nine educated guesses with one loose calibration anchor (peel: predicted 60-70%, measured
   88.3%, gap +18-28). The naive implementation *is* the dumb-structure estimate, executed.
3. **It is the only gate that detects mode A before the oracle is built** — the failure that
   cost crop its hours. High naive score = no discrimination = stop, do not build.
4. **It detects mode D from the other side.** A naive implementation passing a clause it
   should fail localises a by-construction assertion precisely.

Reading the result, with the bar at <50%: naive ≥80% means mode A, the task is a crop, stop.
Naive 40-70% means the oracle discriminates but the headroom is thin. Naive ≤30% is the
healthy shape — real difficulty above the floor. Naive at 0% **with `status: ok`** means the
oracle is strict and the floor is genuinely low; naive at 0% with `status: error` means the
artifact is broken, not the task, and must be fixed before the number counts.

Cost is bounded by the API surface, not the spec: it is type-driven work with no algorithm
in it. The honest comparison is against the cost of discovering mode A *after* building a
full oracle, which is the position crop was in.

---

## What this does *not* license

Do **not** reweight the oracle toward the discriminating handful to push the score down.
Selecting tests to hit a score target is engineering the oracle toward a number
(**Rule 5**), and it would also destroy the measurement this note is built on. The
conclusion is about *candidate selection*, not about editing `oracle/`. crop-rope-001's
oracle is correct and stays as-is; the task simply does not qualify (bar: qwen3.8-max under
50%; actual: 93.7–95.2%).
