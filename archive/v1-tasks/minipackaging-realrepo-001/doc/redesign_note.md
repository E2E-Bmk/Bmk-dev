# MiniPackaging Resolve Metadata Redesign Note

Date: 2026-06-28

## Shared Fact Source

The canonical fact source is now candidate-owned: `resolve_metadata(roots, candidates, environment=None, requested_extras=None, prereleases=None)`. It consumes local root requirements, local candidate records, caller environment, requested extras, and prerelease policy, then projects the same parsed requirement/marker/specifier/version facts into resolver-visible views.

The system layer no longer defines a hidden resolver harness. Hidden and public rubric cases call the candidate implementation's public API and compare semantic fields.

## Derived Views

`resolve_metadata()` must return six coordinated projections from one fact source:

- `selected`: normalized project name to canonical selected version.
- `excluded`: active project name to non-selected supplied candidate versions.
- `edges`: active parent-to-child dependency facts, including child extras, URL, marker, canonical specifier, marker applicability, and specifier-match facts.
- `dependents`: reverse parent lists derived from `edges`.
- `requested_extras`: extras accumulated for each active project from roots and dependency edges.
- `requirements`: active root and dependency requirement facts with source, parent, normalized name, extras, URL, specifier, marker, and marker applicability.

The views are intentionally redundant. A candidate that computes selected versions, dependency edges, reverse dependents, extras, and requirements through separate local shortcuts should be able to pass isolated unit tests but fail system tests when those projections disagree.

## Revision Summary

This redesign makes the resolver/projection layer public rather than evaluator-owned:

- Added `resolve_metadata` to the PRD import list, feature set, API list, and dependency metadata contract.
- Added a light unit/schema case (`MPU019`) that checks importability, documented projection keys, simple schema, and caller metadata non-mutation.
- Rewrote all system tests to call `resolve_metadata()` directly instead of embedding an evaluator-local `resolve(...)` oracle.
- Kept system comparisons semantic: normalized names, canonical versions, extras, URL fields, markers, specifier-match facts, selected versions, dependents, requested extras, requirements, exclusions, and permutation equality.
- Kept primitive parser/string/equality behavior in unit or narrow semantic round-trip checks so system failures are not repeated private-shape or exact-string traps.

## Expected Gap Mechanism

Unit tests can still be passed by independently correct primitives: version parsing, specifier membership, requirement parsing, marker evaluation, environment behavior, satisfaction, and a shallow resolver schema. System tests add the compositional requirement that `resolve_metadata()` maintain one shared graph/fact source and derive every public projection from it.

Expected system-only failures include:

- selecting versions without updating `excluded` consistently;
- producing dependency edges but stale or missing reverse `dependents`;
- applying extras to markers but not carrying them into `requested_extras` or child dependencies;
- using marker/specifier semantics for final selection but not in `requirements` or `specifier_matches`;
- changing results under root or candidate permutation;
- corrupting caller metadata after failed dependency parsing.

## Reference Gate

Command run from `G:\research\01_agents\swe-e2e\Bmk-dev`:

```powershell
python tools\score_unit_system.py task\minipackaging-realrepo-001\rubric.json --solution-dir runs\minipackaging-realrepo-001\solution-reference --timeout 10
```

Result: 31 / 31 cases passed, weighted 172 / 172, Unit 100.00%, System 100.00%, Gap 0.00pp.

## Audit Risks

- Fresh candidate runs are needed. Prior candidate scores predate `resolve_metadata()` and are diagnostic only.
- The new API increases implementation scope; unit coverage keeps only a light schema check so the system layer measures graph/projection consistency rather than parser minutiae.
- There is still some public shape specification for projection dictionaries. The rubric mitigates private-shape risk by comparing documented semantic fields and tolerating list/tuple sequence values where appropriate.
- The resolver remains local and deterministic. It must not drift into pip/network/backtracking scope.
- Exact exception messages, private trace order, whitespace in requirement strings, and repeated equality/hash failures remain non-goals for system scoring.
