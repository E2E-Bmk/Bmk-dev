# MkDocs v14 candidate-packet public-operation audit

Status: pre-freeze static admission check.

The semantic oracle imports fourteen public names from six ordinary MkDocs
modules.  Each import is present in `ENVIRONMENT.json` and is described in the
candidate-visible TASK or SPEC with its supported call signature and return
shape.

| Public module | Imported names | Candidate-visible contract |
|---|---|---|
| `mkdocs.config` | `load_config` | path/file/None input, keyword-only path, mapping and attribute result protocol |
| `mkdocs.commands.build` | `build` | keyword-only build controls, `None` return, failure and cleanup boundary |
| `mkdocs.exceptions` | `MkDocsException`, `Abort`, `ConfigurationError`, `BuildError`, `PluginError` | hierarchy, common catch boundary, strict/build categories, exit status |
| `mkdocs.structure.files` | `File`, `Files`, `get_files` | constructors, attributes, identity, iteration/length/membership, non-indexability, return shapes |
| `mkdocs.structure.nav` | `Link`, `Section`, `get_navigation` | constructors, navigation return, top-level and flat-list protocols, identity and adjacency |
| `mkdocs.structure.pages` | `Page` | constructor, File back-reference, read/render returns, metadata/content/title/TOC lifecycle |

`audit_public_operations.py` parses `probe_root.py` and `scenario_driver.py`
without importing or executing candidate code.  It freezes both the fourteen
imports and all forty-four observed public operations: constructor/function
calls, method calls, attributes, mapping membership/access, sequence
iteration/indexing/length, TOC length, exception catching, and public type
relationships.  `PUBLIC-OPERATION-CONTRACT.json` maps every observation to a
general TASK/SPEC clause.  An added or changed oracle operation, a missing
mapping, or a missing clause invalidates static registry admission.

Durable JSON keys are audited separately by `RECORD-SHAPE-CONTRACT.json` and
`audit_record_shapes.py`; treating those artifacts as ordinary dictionaries in
this operation audit was the v13 coverage gap repaired by this clean successor.

The protocol-dimension review is broader than the current observations.  It
states for Config, File, Files, Page, TableOfContents, Navigation, and returned
navigation lists whether length, iteration, indexing, and truth testing are
supported, and it records their attributes and return shapes.  In particular,
the rendered TOC is sized and iterable, `Files.src_uris` is a URI-to-File
mapping, navigation `items`/`pages` are indexable lists, and Page/File identity
is shared.

The candidate packet also states that every public configuration, source,
render, navigation, build, and durable-record call closes the resources it
opens on success and failure.  Valid calls emit no warnings and remain valid
with warnings promoted to errors.  This directly covers fresh-process reopen
and retry lifecycles without prescribing an internal implementation.

Root and copied candidate packet files must be byte-identical.  Packet wording
uses ordinary OSS compatibility terms and exposes no root IDs, fixtures,
expected vectors, mutation labels, scorer mechanics, or hidden call order.
The v14 repair preserves the root mapping, dependency graph, reference overlay,
and mutation designation from qualified v13.  It changes only candidate-visible
record documentation, fail-safe observation, and the audits needed to bind
those laws before freeze.
