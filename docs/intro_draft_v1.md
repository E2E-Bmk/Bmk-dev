# Introduction — Draft v1

> 2026-07-12. 按 Background → Question → Motivation → Solution → Contribution 结构。
> AAAI 格式，正文约 1-1.5 页。

---

## 1. Introduction

Large language models have demonstrated remarkable progress in code generation, achieving strong performance on function-level benchmarks such as HumanEval and MBPP, and even tackling repository-level tasks like bug fixing in SWE-bench. These advances have fueled a wave of AI-powered coding assistants that are increasingly deployed in real-world software development.

However, a critical gap remains between what these benchmarks measure and what software engineering actually demands. Writing a correct function is fundamentally different from delivering a working software project. The core difficulty of real-world software engineering lies not in producing locally correct code fragments, but in maintaining **system-wide consistency** — ensuring that independently authored modules share coherent state representations, honor interface contracts, and propagate errors correctly across component boundaries. This cross-module integration capability is what separates a collection of correct functions from a functioning system.

**Do current LLMs possess this capability?** Despite the proliferation of code generation benchmarks, this question remains unanswered — not because it is unimportant, but because existing evaluation frameworks are structurally unable to isolate it.

Current benchmarks fall into two categories, neither of which isolates system integration. Function-level benchmarks (HumanEval, MBPP, LiveCodeBench) evaluate local correctness on isolated problems. Repository-level benchmarks take two forms: *modification-based* benchmarks (SWE-bench, Aider-bench) test the ability to patch existing codebases, where the surrounding architecture is already provided; *generation-based* benchmarks (NL2RepoBench, PRDBench, ProgramBench) ask models to produce entire repositories, but primarily measure **specification-following ability** — whether a model can faithfully implement a detailed blueprint. NL2RepoBench, for instance, provides specifications exceeding 6,000 words per task, including complete API signatures, usage examples, and edge-case descriptions. This design is well-suited for evaluating implementation fidelity, but it largely eliminates the need for autonomous architectural decisions and cross-module reasoning — the specification already prescribes how modules should be organized and how they interact. As a result, a complementary but distinct capability remains unmeasured: **system design ability**, i.e., whether a model can independently make consistent architectural decisions given only behavioral constraints.

To isolate and measure this capability, we need a benchmark that satisfies three design requirements: (1) the input specification must describe *what the system should do* without prescribing *how it should be organized internally*; (2) the evaluation oracle must be sensitive to cross-module consistency failures, not just per-function correctness; and (3) the oracle must carry information beyond what is stated in the specification, so that models cannot achieve high scores through specification-to-code translation alone.

We introduce **Spec2Repo**, a benchmark designed to isolate and quantify LLMs' cross-module system integration capability. Given a behavioral specification of approximately 1,000 words — describing functional requirements, global invariants, and a minimal test-interface contract, but no internal architecture, API documentation, or code examples — the model must deliver a complete, installable Python package. Crucially, our test suites are derived from original repository tests but **rewritten to verify behavior rather than implementation interfaces**, allowing models full freedom in architectural decisions while still enabling rigorous evaluation.

Spec2Repo employs a two-layer evaluation framework that separately measures unit-level correctness and integration-level correctness. We define the **Integration Gap** — the difference between unit test pass rate and integration test pass rate — as a diagnostic metric for cross-module consistency. A large Integration Gap indicates that the model can produce individually correct components but fails to make them work together as a coherent system.

Our main contributions are as follows:

- **Benchmark and Methodology.** We present Spec2Repo, a benchmark of [N] end-to-end Python project generation tasks with behavioral specifications and behavior-verifying test suites. To our knowledge, this is the first benchmark that isolates cross-module system integration as a distinct evaluation dimension, decoupled from specification-translation ability.

- **Integration Gap Analysis.** We evaluate [M] frontier LLMs and find a substantial Integration Gap: models achieve [X]% unit test pass rate but only [Y]% integration test pass rate. Manual classification of 100 integration failures reveals that [Z]% stem from cross-module consistency issues (state inconsistency, interface contract violations, error propagation breakage) rather than single-module logic errors.

- **Specification-Integration Tradeoff.** Through controlled ablation on NL2RepoBench tasks, we characterize how Integration Gap varies with specification granularity, revealing the relationship between specification detail and the model's reliance on autonomous system design.

- **Human Baseline.** We establish a human baseline showing that experienced developers achieve an Integration Gap of less than [H]%, confirming that the gap observed in LLMs reflects a model-specific deficiency rather than inherent task difficulty.

Our findings have direct implications for both training and deployment: they identify cross-module consistency as a concrete capability gap that current training regimes do not adequately address, and they delineate a practical boundary for AI-assisted software development — where models can reliably generate components but require human oversight for system-level integration.
