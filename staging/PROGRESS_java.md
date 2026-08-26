# Java Stage 1–3 packet production — progress

Worker branch: `cursor/8-26-50tasks-java-a9d6`. Quota: 10 ACCEPTABLE Java
Stage 1–3 task packets under `staging/{task_id}/`.

## Deliverable definition (Definition A)

Each packet contains:

- `spec.md` — candidate-visible 6-layer spec (internal header included in the
  staging copy; stripped only when a packet graduates).
- `oracle/` — Maven oracle project in the style of the shipped Java tasks
  under `wip/java/*-fullrepro-001/packet/oracle/`: `pom.xml` (depends on the
  target coordinate through `${candidate.version}`), `requirements.txt`
  (packet marker), `src/test/java/{atomic,integration,support}`, runnable by
  `harness/lang/java/runner.py` (JavaRunner) and `harness/lang/java/score_java.py`.
- `filter/spec_test_map.md`, `filter/kept_nodeids.txt`, `filter/taxonomy.jsonl`,
  `filter/rewrite_audit.md`, `filter/lint_result.txt` (first line `LINT_PASS`,
  newer than every oracle test source), `filter/local_reference_run.txt`
  (non-Docker `mvn test` run against the pinned reference artifact at 100%).
- `task.json` with `language: "java"`, `maven_coordinates`,
  `program_file: "pom.xml"`, taxonomy, stats.
- `PIPELINE_STATE.md` (state machine instance, through `S3_DONE`, noting the
  Docker dummy gate and Docker reference run PENDING).
- `filter_notes.md` (Stage 1 screening evidence).

## Infrastructure notes

- `harness/core/oracle_import_lint.py` gained a `staging/{task}/oracle`
  fallback in its oracle resolver so LINT_PASS artifacts are produced against
  the staged packet itself.
- The ten task ids are registered in `harness/lang/java/target_imports.json`
  with their Java package roots (the form the shipped fullrepro Java tasks
  use in `harness/core/target_imports.py`), so the lint has non-vacuous
  target roots.
- Docker is unavailable on this VM, so `harness/lang/java/score_java.py`
  (dummy gate + official reference gate, both Docker-only) is PENDING for
  every packet. As the non-Docker substitute, each oracle is compiled and
  run with local Maven 3.9.9 / OpenJDK 21 against the pinned release
  artifact resolved from Maven Central
  (`mvn test -Dcandidate.version={pinned}`), recorded in
  `filter/local_reference_run.txt`; the gate requirement is 100%.

## Repo bans (dupes of prior Java task sources on any tier)

commons-pool, cron-utils, depgraph-maven-plugin, halodb, hikaricp, japicmp,
jimfs, jline2, jpeek, mybatis migrations, maven-resolver, pf4j, xmlunit,
classgraph (screened by prior research), commons-configuration (rejected by
prior research: spring-coupled tests).

## Task ledger

| # | task_id | repo | state | notes |
|---|---------|------|-------|-------|
| 1 | javapoet-fullrepro-001 | square/javapoet | S3_DONE (Docker gates PENDING) | 91 tests (61 atomic / 30 integration); local mvn reference 91/91; LINT_PASS; verify_task STATIC_VALID |
| 2 | jsoup-fullrepro-001 | jhy/jsoup | S3_DONE (Docker gates PENDING) | 106 tests (73 atomic / 33 integration); local mvn reference 106/106; LINT_PASS; verify_task STATIC_VALID |
| 3 | snakeyaml-engine-fullrepro-001 | snakeyaml/snakeyaml-engine | S3_DONE (Docker gates PENDING) | 93 tests (66 atomic / 27 integration); local mvn reference 93/93; LINT_PASS; verify_task STATIC_VALID |
