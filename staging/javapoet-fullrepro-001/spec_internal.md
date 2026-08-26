<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — javapoet-fullrepro-001

- task_id: javapoet-fullrepro-001
- language: java
- repo: square/javapoet
- repo_commit: 714e05ca60179285746604452324262b126dcb2d (tag javapoet-1.13.0)
- maven_coordinates: com.squareup:javapoet
- package root: com.squareup.javapoet
- source boundary: the whole library at the pinned commit, minus
  `javax.lang.model` mirror interop beyond accepting `Modifier` values
  (Non-Goals). Records/sealed/module emission excluded (post-1.13 features).
- spec basis: public README format-language documentation, javadoc, and
  empirical probes of the pinned 1.13.0 artifact (probe program under
  /tmp/probe during authoring; exact rendered text asserted only where the
  spec fixes layout).
- oracle: generated-only (Track B); upstream suite used as behavior checklist
  only.
