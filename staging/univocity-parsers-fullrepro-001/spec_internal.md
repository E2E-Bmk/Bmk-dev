<!-- INTERNAL — not candidate-visible. Kept out of spec.md so the packet's
     candidate-facing document carries no pipeline vocabulary. -->

# Internal header — univocity-parsers-fullrepro-001

- task_id: univocity-parsers-fullrepro-001
- language: java
- repo: uniVocity/univocity-parsers (github)
- repo_commit: 943a542c909709b5e4e7ccd97831bc2d6b8673f4 (tag v2.9.1)
- maven_coordinates: com.univocity:univocity-parsers
- package root: com.univocity.parsers
- source boundary: CSV/TSV/fixed-width parse + write, headers/column
  selection, Record typed views, ParsingContext, TextParsingException;
  excludes annotations/bean routines, JDBC, conversions API, concurrent
  input reading, multi-schema and lookahead parsing (Non-Goals).
- spec basis: project README/tutorial and javadoc public documentation and
  two empirical probe rounds against the pinned 2.9.1 artifact (probe
  programs under /tmp/probe during authoring); quoting rules, null/empty
  substitution, selection reordering, TSV escapes, and fixed-width padding
  verified by probe before being pinned.
- oracle: generated-only (Track B); upstream suite (~564 TestNG test
  functions with internal helpers) used as a behavior checklist only.
