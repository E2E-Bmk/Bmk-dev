<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — jsoup-fullrepro-001

- task_id: jsoup-fullrepro-001
- language: java
- repo: jhy/jsoup
- repo_commit: 7c56eb26c8cc772c5c3d0e052dc076a128173c85 (tag jsoup-1.18.3)
- maven_coordinates: org.jsoup:jsoup
- package root: org.jsoup
- source boundary: parse + DOM + select + clean + serialize; excludes the
  network `Connection`/`HttpConnection` API, form helpers, `org.w3c.dom`
  interop, XPath, and streaming parsing (Non-Goals).
- spec basis: jsoup cookbook/apidocs public documentation and six empirical
  probe rounds against the pinned 1.18.3 artifact (probe programs under
  /tmp/probe during authoring); exact serialized markup asserted only where
  the spec fixes layout.
- oracle: generated-only (Track B); upstream suite used as behavior checklist
  only (upstream tests are largely same-package white-box and unusable
  directly).
