repo: immerjs/immer
source_path: https://github.com/immerjs/immer (/tmp/repos/immer at v11.1.18)
commit: b00474e3755954f6b27a392dcb4bce97254c100c (npm gitHead for immer@11.1.18, tag v11.1.18)
language: typescript
src_loc: 3305 (src/**/*.ts excluding .d.ts: core/{immerClass,proxy,finalize,current,scope}, plugins/{patches,mapset,arrayMethods}, utils/{common,env,errors,plugins}, immer.ts, internal.ts)
test_functions: 514 direct it/test across 22 jest files in __tests__/ (plus generator-driven variants)
test_files: __tests__/{base,produce,draft,patch,curry,current,original,frozen,manual,map-set,plugins,regressions,...} (22 files)
dominant_test_styles: behavior-driven unit tests over produce/patch/draft lifecycles; some snapshot files (__snapshots__, __prod_snapshots__) for error messages
public_docs: https://immerjs.github.io/immer/ (produce, curried producers, patches, map/set, freezing, current/original, createDraft/finishDraft, performance/plugins pages), README
core_fact_source: one draft tree per producer scope - a proxy graph over a base state whose recorded mutations finalize into (1) a structurally shared next state, (2) a forward patch stream, and (3) an inverse patch stream, under global/instance configuration (autoFreeze, strict shallow copy, strict iteration, loaded plugins)
derived_views: (1) produced next state (structural sharing + no-change identity + frozen output);
  (2) patch projection (produceWithPatches/patchListener -> JSON-patch-like op/path/value records, forward and inverse);
  (3) patch application projection (applyPatches over plain bases and over live drafts);
  (4) draft lifecycle projection (createDraft/finishDraft, isDraft, revocation after finalize);
  (5) snapshot projection (current unfrozen snapshots, original base access);
  (6) container projections (Map/Set drafts via enableMapSet, array-method semantics via enableArrayMethods);
  (7) configuration projection (setAutoFreeze/setUseStrictShallowCopy/setUseStrictIteration/Immer instances with isolated config);
  (8) draftability projection (isDraftable/immerable/freeze)
external_deps: none at runtime; upstream tests use jest + lodash/deepFreeze helpers
test_import_audit: HIGH_RISK for direct reuse - 21 of 22 test files import "../src/immer" relative source paths (0 import the published "immer" entry); several rely on jest snapshot files and process.env.NODE_ENV switching -> Track B generated oracle importing only 'immer'
docs_test_alignment: aligned - immerjs.github.io documents the same produce/patches/draft/plugin surface the tests exercise; error-message snapshots are implementation detail and excluded
contamination_note: immer@11.1.18, released 2026-08-19; major 11.0.0 released 2025-11-23, likely after common training cutoffs. v11 removed recipe this-binding and async producers, made produce throw on non-draftable object bases, added enableArrayMethods (callbacks see base values, subset results are drafts) and setUseStrictIteration - all diverge from the widely trained immer 9/10 surface, giving memorization traps
decision: keep
reason: a lazily-finalized proxy graph with three simultaneous public projections (next state, forward patches, inverse patches) plus lifecycle, snapshot, and container views; patch algebra is an equivalence-grade contract (apply(base,patches)=next, apply(next,inverse)=base) and v11 fresh-major divergences resist pattern matching.
risks: (1) upstream tests non-portable (relative src imports + snapshot dependence) -> generated_only oracle, every expected value observed by executing 11.1.18;
  (2) module-global switches (plugins, autoFreeze, strict modes) leak across tests -> plugin-off error probes isolated in their own vitest file (fresh module graph per file), config switches restored per test or exercised through Immer instances;
  (3) error message wording is minified in prod builds -> assert only that an Error is thrown for error paths, never message text;
  (4) internal proxy shapes/DRAFT_STATE are implementation detail -> assert only via public API (isDraft, mutation visibility, identity);
  (5) patch op ordering could be seen as implementation-specific -> assert per-path op content and round-trip equivalence rather than global stream order where docs are silent, and keep observed op shapes for single-mutation cases only
scope_plan: target_subdomain=produce semantics (no-change identity, structural sharing, recipe return rules incl. nothing, curried producers with default state, deep-freeze autoFreeze), patch algebra (enablePatches gating, produceWithPatches/patchListener forward+inverse records, applyPatches over bases and drafts, add/replace/remove ops, root replacement, '-' append, path-resolution errors), draft lifecycle (createDraft/finishDraft with patch listener, revocation after finalize, leaked-draft errors), snapshots (current unfrozen point-in-time, original, strict iteration effect on symbol-keyed children), draftability and freezing (isDraft/isDraftable/freeze shallow+deep/immerable classes with prototype preservation), configuration (setAutoFreeze, setUseStrictShallowCopy incl. class_only and non-enumerable handling, Immer instances with isolated config), Map/Set drafts (enableMapSet gating, draft ops, iteration drafts, patches keyed by map key/set order), array methods plugin (enableArrayMethods: stored-value callbacks, draft subset results, mutating methods); expected_oracle_max=105 (initial estimate 100; raised during Stage 3 to satisfy the integration+system_e2e >= 25 layer floor; final oracle 104)
excluded: exact error-message wording and error numbering, production-build minified message format, TypeScript-only type utilities' compile-time behavior (Draft/Immutable/castDraft runtime identity only), internal proxy/state shapes, performance characteristics, structural-sharing internals beyond observable identity, async recipes (removed in v11 - probed: returning a promise while modifying the draft throws), legacy ES5 fallback (removed since v10)
