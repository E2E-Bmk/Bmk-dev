<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — jsonpath-fullrepro-001

- task_id: jsonpath-fullrepro-001
- language: java
- repo: json-path/JsonPath (github)
- repo_commit: af7e516c69df680a6584fca7180ef082eb67c96c (tag json-path-2.9.0)
- maven_coordinates: com.jayway.jsonpath:json-path
- package root: com.jayway.jsonpath
- source boundary: the public query/write API (JsonPath statics, compiled
  paths, DocumentContext, Configuration/Option, Filter/Criteria/Predicate,
  MapFunction, exception tree) over the default json-smart provider model;
  excludes alternative providers/mappers, the path cache SPI, evaluation
  listeners, and internal token classes (Non-Goals).
- spec basis: project README/javadoc public documentation and three empirical
  probe rounds against the pinned 2.9.0 artifact (probe programs under
  /tmp/probe during authoring); result shapes, runtime types, normalized path
  strings, and exception classes asserted only as the spec states them.
- oracle: generated-only (Track B); upstream suite used as behavior checklist
  only (upstream tests are heavily provider-matrix and internals-driven).
