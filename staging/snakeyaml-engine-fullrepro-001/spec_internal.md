<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — snakeyaml-engine-fullrepro-001

- task_id: snakeyaml-engine-fullrepro-001
- language: java
- repo: snakeyaml/snakeyaml-engine (bitbucket)
- repo_commit: da5e518605eda2d52ff419bdb77f774a337555bd (tag snakeyaml-engine-2.9)
- maven_coordinates: org.snakeyaml:snakeyaml-engine
- package root: org.snakeyaml.engine
- source boundary: Load/Dump/Compose public API plus LoadSettings/DumpSettings;
  excludes the event-level emitter/parser API, custom constructors and
  representers, comment round-tripping, and YAML 1.1 resolution (Non-Goals).
- spec basis: engine wiki/javadoc public documentation and four empirical probe
  rounds against the pinned 2.9 artifact (probe programs under /tmp/probe
  during authoring); exact dumped text asserted only where the spec fixes
  presentation.
- oracle: generated-only (Track B); upstream suite used as behavior checklist
  only (many upstream tests are white-box against scanner/parser internals).
