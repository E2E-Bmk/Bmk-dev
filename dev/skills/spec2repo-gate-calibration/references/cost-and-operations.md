# Cost-efficient operation

## Spend model tokens only on independent reasoning

- Use exactly one source-blank Solver implementation per case.
- Natural/reverse/permuted and repeated reference/control runs are local
  compute checks; they do not need additional model agents.
- Parallelize different cases or bounded gate-building subtasks when the user
  authorizes it, but never let two agents edit the same case/version.
- Keep long scorer runs local and report only boundary changes or failures.
- Do not repeatedly ask approval for project-local actions already authorized.

## Reuse mechanics without copying answers

Mechanically reuse proven scorer, manifest, provenance, fresh-process, and
static-audit infrastructure. Author case-specific SPEC, public-surface audit,
native controls, mutation families, and broad profiles. Never copy prior
candidate source, exact failed-root lists, or score-targeted patches.

Prefer deterministic scripts for inventory, hashing, score math, and JSON
validation. Keep the model focused on architecture and semantic diagnosis.

## Stop conditions

- After freeze and Solver scoring, do not iterate the same version to improve
  the score.
- One invalid Solver caused by its own provenance/source is an exit under the
  one-Solver policy, not permission for a second implementation.
- A frozen gate defect creates a new version only if the remaining campaign
  value justifies another case cycle.
- If Combined exceeds the tolerance or Gap is negative, redesign the
  architecture, not individual assertions.

## Packaging hygiene

Keep evidence, probes, caches, build environments, and reports outside the
user-facing dataset unless requested. For a minimal Spec2Repo delivery,
include only the case JSON/spec input and executable oracle assets, with all
required evaluator manifests/provenance dependencies actually present.

Before packaging, mechanically verify:

- every referenced asset exists in the package;
- every JSON decodes as UTF-8;
- oracle entry points and relative paths resolve from the packaged root;
- no cache, smoke workspace, historic candidate, score receipt, or private
  report is included;
- a clean extraction can collect the oracle without the original workspace.
