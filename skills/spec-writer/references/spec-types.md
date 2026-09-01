# Spec Type Classification

## Framework

Two axes define the four types:

```
                  行为描述 (What)      实现指导 (How)
使用者视角    │  Type 1: 用户指南   │  Type 2: API 参考   │
实现者视角    │  Type 3: 行为规格   │  Type 4: 实现蓝图   │
```

Benchmark evidence (cookiecutter, 2026-06-29, same candidate model):

| Type | Example | pass rate |
|------|---------|-----------|
| Type 1 | public_packet.md + README | 12.50% |
| Type 3 (condensed) | spec_v3.md | 16.15% |
| Type 4 | spec_v4.md (NL2RepoBench style) | 16.74% |
| Type 3 (complete) | spec_v2.md | 25.38% |

The gap is entirely in integration (+10 tests) and system_e2e (+14 tests). Atomic pass rate is identical between Type 3 complete and Type 3 condensed. Type 4 degraded because the model implemented Jinja2 and Click from scratch (scope creep triggered by architecture prescription).

**Use Type 3 for reconstruction benchmarks.**

---

## Type 1: User Guide

**Audience:** end users of the library

**Should contain:**
- One-paragraph product description
- Installation (`pip install`)
- 2-3 end-to-end usage examples
- Core concept glossary
- Common Q&A

**Must not contain:**
- Complete API signature list
- Edge cases, error semantics
- Cross-component invariants
- Internal architecture

**Benchmark use:** Never sufficient alone. Missing invariants cause system_e2e failures.

---

## Type 2: API Reference

**Audience:** developers calling the library as a dependency

**Should contain:**
- All public function/class signatures (parameter names, types, return values)
- Per-parameter semantics (what values are accepted)
- All public exception classes and trigger conditions
- Module import paths

**Must not contain:**
- Implementation algorithms
- End-to-end workflow examples (belong in Type 1)
- Cross-function system-level invariants (belong in Type 3)

**Benchmark use:** Necessary but not sufficient. Without invariants, model passes atomic tests but fails integration/system.

---

## Type 3: Behavioral Specification (TARGET TYPE)

**Audience:** engineer implementing the library from scratch, or formal verification

**Should contain:**
- Product overview and explicit non-goals
- All public API signatures (overlaps Type 2 — required here too)
- Variable/state semantics: behavioral contract for each input type
- Context precedence: ordered list of how multiple input sources merge
- Cross-View Invariants: ≥ 6 items, user-observable language, spanning all public projection pairs
- Error semantics: which exception for which trigger
- At least one complete end-to-end workflow example (behavioral anchor)
- Implementation Guidance: what test dimensions exist (no fixture shapes)

**Must not contain:**
- Internal file/module structure (private modules, undocumented implementation paths)
- Algorithm step sequences ("Step 1: load JSON, Step 2: iterate keys...")
- Dependency version pinning (`Jinja2>=3.0`)
- Class/function names not appearing in public docs
- Prescriptive implementation choices ("use Click for CLI")

Note: public module import paths that appear in official docs (e.g. `from cookiecutter.main import cookiecutter`) ARE required — they are part of the public API contract, not internal structure.

**Key test:** the same behavioral constraint must be satisfiable by two different internal architectures. If the spec only works for one architecture, it has leaked implementation details.

---

## Type 4: Implementation Blueprint

**Audience:** developer following a specific build plan

**Should contain:**
- Complete file structure (each module listed)
- Per-function algorithm pseudo-code or numbered steps
- Specific dependency choices with versions
- Concrete code examples (complete or near-complete)
- Implementation notes ("handle Windows read-only files", "preserve ordering")

**Must not contain (lessons from v4 failure):**
- Negative dependency constraints ("do not use X") — models misread as "implement X from scratch"
- Vague "implement from scratch" phrasing — triggers scope creep into dependency tree
- Architecture that contradicts the library's actual module split

**Benchmark use:** Avoid. Prescriptive style constrains the model to a specific implementation path; any divergence between the blueprint and real library behavior is amplified. Observed failure: model created custom Jinja2 (130 lines, regex-based) and Click (110 lines, argparse-based) stubs instead of using real packages, producing 74 collection errors.

---

## Completeness vs. Conciseness Trade-off

Within Type 3, more complete beats more concise:
- spec_v2 (complete Type 3): 25.38%
- spec_v3 (condensed Type 3, dropped Logging section and 2 invariants): 16.15%

The dropped invariants in v3 correlated with a 14-test drop in system_e2e (from 20 to 6). Do not condense by removing invariants or removing the Implementation Guidance section.
