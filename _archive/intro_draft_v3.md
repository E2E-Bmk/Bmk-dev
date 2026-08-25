# Introduction — Draft v3

> 2026-07-15. 七段式重组：P2/P3 拆开，P4/P5 拆开，新增 P6 headline findings，贡献压缩为 3 条。
> 采用 SWE-Bench Pro 的 defect→intervention 对应 + ProgramBench 的 construct-first + PaperBench 的 evaluator-validity 论证。

---

## 1. Introduction

### P1 — Capability trend + stakes

Large language models have progressed rapidly in code generation, advancing from function-level synthesis (HumanEval, MBPP) to repository-level tasks such as bug fixing (SWE-bench) and feature implementation. These advances have fueled a wave of AI-powered coding assistants that are increasingly deployed in real-world software development, where tasks routinely require coordinating multiple files, modules, and subsystems rather than producing isolated code fragments.

### P2 — Evaluation validity crisis

However, a growing body of evidence suggests that headline pass rates on popular coding benchmarks may not reflect genuine capability gains. Audits of SWE-bench Verified revealed fundamental design flaws and training contamination, and a subsequent audit of SWE-Bench Pro found that approximately 30% of tasks are broken, with failures driven by four recurring validity issues: (i) tests that enforce implementation details not stated in the prompt, (ii) prompts that omit requirements that hidden tests check, (iii) tests with insufficient coverage that allow incomplete fixes to pass, and (iv) prompts that mislead models toward incorrect behavior. The root cause is structural: these benchmarks are programmatically derived from pull-request histories, where tests are written to validate a specific change rather than to define an implementation-agnostic behavioral standard. Separating signal from noise in coding evaluations has become an urgent prerequisite for any meaningful benchmark.

### P3 — Construct gap: the question Spec2Repo answers

Yet even a trustworthy pass rate answers only *whether* a model succeeded — not *what capability* the task actually measures. We argue that the core difficulty of real-world software engineering lies not in producing locally correct code fragments, but in maintaining **cross-module system integration**: ensuring that independently authored modules share coherent state representations, honor interface contracts, and propagate errors correctly across component boundaries. This capability is what separates a collection of correct functions from a functioning system. **Do current LLMs possess it?**

Despite the proliferation of code generation benchmarks, this question remains unanswered — because existing evaluation frameworks are structurally unable to isolate it. Function-level benchmarks evaluate local correctness on isolated problems. Modification-based benchmarks (SWE-bench, Aider-bench) test patching within an existing architecture that already provides module boundaries and interfaces. Generation-based benchmarks ask models to produce entire repositories but primarily measure *specification-following ability*: NL2RepoBench, for instance, provides specifications exceeding 6,000 words per task, including complete API signatures and usage examples, largely eliminating the need for autonomous architectural decisions. These designs are well-suited for evaluating implementation fidelity, but they cannot distinguish whether a model failed because it *did not follow the specification* or because it *cannot make consistent cross-module design decisions on its own*. A complementary construct remains unmeasured: **system integration ability** — whether a model can independently make coherent architectural decisions given only behavioral constraints.

### P4 — Benchmark reveal + task contract

To isolate this capability, we introduce **Spec2Repo**, a benchmark of [N] end-to-end Python project generation tasks. Each task provides a behavioral specification of approximately 1,000 words that describes *what* the system should do — its observable behaviors, input–output contracts, and error-handling expectations — but deliberately omits *how* the system should be structured: no module decomposition, no API signatures, no directory layout, no code examples. Given this specification and a minimal test-interface contract, the model must produce a complete, runnable project from an empty workspace, autonomously deciding internal architecture, module boundaries, and cross-module data flow.

We evaluate generated projects through a **two-layer test framework**. *Unit tests* verify that individual components produce correct outputs in isolation. *Integration tests* verify that components interact correctly — that data flows between modules preserve type and semantic contracts, that shared state is consistently represented, and that errors propagate across component boundaries. We define the **Integration Gap** as the difference between unit test pass rate and integration test pass rate. A large gap indicates that the model can produce individually correct components but fails to assemble them into a coherent system — directly quantifying the system integration construct.

### P5 — Instrument credibility (defect → intervention)

Benchmark design must also ensure that scores are not artifacts of flawed tasks. Spec2Repo's forward construction pipeline directly targets the four validity failure modes identified in P2:

| PR-derived defect | Spec2Repo intervention |
|---|---|
| (i) Tests enforce implementation details | Behavioral test suites verify *what the code does*, not *what it is named or how it is structured*. Any functionally correct implementation passes regardless of method names, class hierarchies, or directory layout. |
| (ii) Prompts omit hidden requirements | Behavioral specifications follow explicit inclusion/exclusion criteria, with systematic calibration to ensure that all tested behaviors are derivable from the specification. |
| (iii) Insufficient test coverage | Oracle test suites are derived from original repository tests through systematic filtering that removes contradictions and adds coverage beyond what the specification explicitly states. Gold solutions must achieve 100% pass rate. |
| (iv) Misleading prompts | Specifications undergo a calibration review to remove ambiguous language, contradictory constraints, and phrasing that could systematically bias model behavior. |

The benchmark comprises [N] tasks spanning [D] application domains, with a total of [T] behavioral tests (approximately [U] unit tests and [I] integration tests).

### P6 — Headline findings

We evaluate [M] frontier LLMs under a standardized generation pipeline and find a substantial and consistent Integration Gap across all models. The strongest model achieves [X]% unit test pass rate but only [Y]% integration test pass rate — a gap of [X−Y] percentage points. Experienced human developers, given the same specifications, achieve an Integration Gap of less than [H]%, confirming that the gap reflects a model-specific deficiency rather than inherent task ambiguity. Manual classification of 100 integration failures reveals that [Z]% stem from cross-module consistency issues — state representation mismatches, interface contract violations, and error propagation breakage — rather than single-module logic errors. Models can write correct components but cannot assemble them into coherent systems.

### P7 — Contributions + implications

Our main contributions are:

1. **Trustworthy benchmark construction methodology.** We present Spec2Repo, built through a forward specification-and-oracle pipeline that systematically avoids the validity failure modes prevalent in PR-derived benchmarks. We validate instrument quality through broken-rate analysis, behavioral test fairness verification (refactored gold solutions still pass), and gold-solution gate (100% oracle pass rate).

2. **First isolation of system integration capability.** To our knowledge, Spec2Repo is the first benchmark that decouples cross-module system integration from specification-following ability. The Integration Gap metric provides a diagnostic signal that existing benchmarks structurally cannot produce. Through controlled ablation varying specification granularity, we show that the gap diminishes monotonically as architectural detail increases — confirming that it measures autonomous design decisions, not implementation skill.

3. **Empirical characterization of the integration bottleneck.** Failure mode analysis reveals that cross-module consistency, not single-module correctness, is the binding constraint for current LLMs. Human baselines confirm the gap is model-specific. These findings delineate where AI-assisted development can autonomously generate components and where human oversight remains essential for system-level integration.
