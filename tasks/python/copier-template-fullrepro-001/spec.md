<!-- SPEC.md -->
# Copier local-template product contract — Draft C clean

## Authority

This is the sole solver-facing Copier contract for the clean-C design. It defines observable behavior of the pinned local-template product through documented imports, ordinary CLI commands, controlled local templates and Git projects, decoded answers/update output, semantic destination trees, and public errors or statuses.

Conformance does not prescribe private workers, staging/cache layout, merge helpers, prompt internals, subprocess choreography, exact terminal prose, color, progress, exact YAML/JSON serialization, conflict label text, or private diff algorithms. Remote repositories, hosted shortcuts, credentials, and network behavior are outside scope.

## Public entry points and normalization

Documented Python use includes `Phase`, `Settings`, `VcsRef`, `load_settings`, `run_copy`, `run_recopy`, and `run_update`; Copier-specific error/warning names come from `copier.errors`. The console entry point and `python -m copier` expose ordinary copy, recopy, update, and check-update workflows.

Paths are compared after platform normalization, text after line-ending normalization where semantics do not require a particular ending, and YAML/JSON after decoding. Exact formatting, ordering, progress, or wording is not a product law.

## Configuration and settings

A local source contains at most one `copier.yml` or `copier.yaml`. Dual files, invalid structures, and unsupported minimum versions fail through their public categories. Correcting only the offending configuration permits a later operation.

`Settings` supplies isolated defaults and trust data. `load_settings` distinguishes implicit/missing, valid, and invalid settings through public returned values or errors. Observed noninteractive answer precedence is direct data over settings defaults over template defaults.

`_subdirectory` selects the active source subtree. A configured `_exclude` is the template-owned exclusion set; templates that still want control files excluded include those patterns explicitly. Caller exclusions compose at the operation boundary. Exclusions are matched against rendered destination paths.

## Questions and answers

Documented typed questions parse supported direct string/data forms. Unsupported types and missing required values fail through their observed public categories; not every public input failure is required to be a Copier-specific exception subclass.

False conditional questions omit the key from persistent answers while their default remains available to current rendering. Secret values may affect current rendering but are omitted from persistent answers. Choices preserve underlying values rather than labels, and multiselect persists the typed list. Interactive forced asking is outside this clean-C contract.

One effective answer agrees across rendered content, rendered names, and decoded answers wherever each projection applies. Removing a higher-precedence source reveals the next observed source without changing unrelated owners.

## Rendering and public context

`_envops`, `_templates_suffix`, documented filters, and installed Jinja extensions control eligible rendering. Eligible template files render and lose the configured suffix; non-template files copy literally. A local extension is an unsafe feature: it is refused without trust and usable when explicitly trusted.

Ordinary content may observe `_copier_answers`, `_copier_conf`, `_copier_python`, `_copier_phase`, and `_folder_name`. `_copier_operation` is context-specific and is guaranteed here for the documented task/configuration context, not as a universal ordinary-content variable. `Phase.use` restores the previous public phase even after nested failure.

Rendered names remain inside the destination. A safe value can create a normalized nested path; an escaping value fails without an outside write. The contract does not require one narrower exception subclass for that escaping observation.

## Destination ownership policies

Exclusion prevents ownership. `skip_if_exists` preserves a matching file when present but allows template creation when absent. `overwrite` replaces colliding template-owned destinations and leaves unrelated local files unchanged. CLI force composes the documented default/collision policy; without it a noninteractive collision/default requirement may be non-success.

Pretend performs public validation/decision work but makes no destination, answers, task, migration, or conflict-artifact mutation. Quiet changes presentation only.

For a failed task on a fresh Copier-created destination, cleanup-on removes generated partial state; cleanup-off retains it. Cleanup does not broadly remove files already owned by a caller-existing destination.

## Canonical answers state

The canonical answers file contains the local source identity, selected revision when versioned, and persistent nonsecret answers. A configured custom relative path is the only canonical file; no competing `.copier-answers.yml` is invented.

Later recopy/update/check-update operations that use a custom path must select it through the documented explicit `answers_file` argument/option. The product does not magically discover a nondefault custom path when that selection is omitted.

Missing, malformed, or unusable source/revision metadata fails through the public operation. Restoring the required public metadata permits the later operation; no private repair is part of conformance.

## Trust, tasks, and migrations

Tasks, migrations, and Jinja extensions are unsafe features. Refusal produces no unsafe side effect; explicit trust permits the eligible feature. `skip_tasks` suppresses ordinary task execution but is not a general trust grant and does not bypass an eligible migration.

Trusted tasks run after rendered output is available, in declaration order, with task-phase and operation context. A failing later task exposes public task status fields. If cleanup is disabled, a successful earlier task effect remains; a corrected repeated copy executes that earlier task again before the corrected later task succeeds.

Versioned migrations run in declared before/after stages and expose public old/new/stage version values. A side-effect-free before-stage migration failure leaves the controlled v1 tree and answers unchanged. Correcting the migration in a v2.0.1 target permits one coherent update and success marker.

No general law is made here that every migration failure at every stage leaves revision metadata unchanged. In particular, after-stage failure occurs after a different public commit boundary and is outside the narrowed failure root.

## Copy and recopy

Successful copy resolves answers, validates trust/configuration/paths, renders owned output, writes the canonical answers state, and runs eligible trusted tasks. Equivalent library and CLI inputs produce equivalent normalized trees and decoded answers.

Recopy uses recorded local source/answers when the canonical answers path is selected. A direct recopy override changes current answers and creates the corresponding answer-driven path. In the observed nonversioned recopy, a previously rendered differently named file remains; automatic stale-name removal is not promised.

Explicit-custom-path recopy fails if the path selection is omitted, succeeds when supplied, and never creates a default fallback answers file. Recopy pretend with changed data leaves the complete existing tree and answers unchanged.

## Versioned update and check-update

Update operates on a clean committed destination repository. The public Python adapter supplies `overwrite=True`; ordinary CLI update supplies its corresponding public policy. Dirty-repository refusal is a valid precondition failure, not a product miss.

From a committed v1 project, selected v2 update advances decoded `_commit`, applies target template changes, preserves a committed nonoverlapping project edit, preserves a present skipped file, recreates a missing skipped file, and omits a target path selected by exclusion. A later `VcsRef.CURRENT` pretend uses the recorded current revision and changes nothing.

Check-update JSON and quiet status encode the same decision: the controlled newer-template state yields the documented newer status, while the updated current state yields the current status. Exact JSON formatting or prose is excluded.

## Conflict policies

For a true overlap, inline policy writes recognizable project/template alternatives to the owned destination file while unrelated target content and answers revision advance. Exact marker labels are excluded.

For reject policy, the owned destination file takes the template-target content and the `.rej` artifact records the rejected project-local patch. Unrelated target content and answers revision advance. Exact unified-diff formatting is excluded.

A fresh no-overlap counterfactual applies the template target and retains a separate local project file. Automatic cleanup after manual conflict resolution is not promised by this contract.

## Failure containment and correction

Failure is never silently converted to success. Conformance distinguishes configuration/question/path refusal, fresh-copy task failure with cleanup policy, mutation-free before-migration failure, successful target update, and conflict representation.

Owner correction changes the responsible config, answer, path, trust decision, command, migration target, source metadata, or overlap. It does not use broad deletion, global suppression, or private state. A versioned project may require an ordinary clean Git checkpoint before the next update/pretend lifecycle entry.

The full repeated lifecycle is: local v1 copy, unsafe refusal, side-effect-free before-migration failure, owner correction to v2.0.1, successful project checkpoint, and `VcsRef.CURRENT` pretend with zero semantic delta.
