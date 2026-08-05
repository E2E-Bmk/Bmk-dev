# xmlschema Public Fixture Specification

## Product Overview
`xmlschema` parses XML Schema definitions, validates XML documents, and
projects XML data into Python and JSON values. It also encodes public mapping
values back to XML, supports documented converter conventions, exposes schema
component maps, and provides deterministic local CLI conversions.

## Scope
The covered behavior uses generated local XSD, XML, and JSON fixtures:

- XMLSchema construction from local files and text with `base_url`.
- Include and import resolution, deferred `build()`, `add_schema()`, and
  public component/map projections.
- Package and schema validation through `validate`, `is_valid`, and
  `iter_errors`.
- `to_dict`, `to_json`, `to_etree`, and `from_json`.
- Default, Parker, BadgerFish, JsonML, and Columnar converter projections.
- Local XML resources, access controls, namespace discovery, schema hints, and
  offline `export`.
- Deterministic `xmlschema-validate`, `xmlschema-xml2json`, and
  `xmlschema-json2xml` command functions.

Live remote resources, exhaustive W3C conformance suites, optional lxml-only
parity, private implementation details, upstream test imports, exact error
wording, whole serialized snapshots, sleeps, and host-state behavior are out
of scope.

## Public Import Surface
The covered imports are `xmlschema`, its documented converter classes,
`xmlschema.cli`, and public resource and exception modules. The primary
symbols are `XMLSchema`, `XMLSchema10`, `validate`, `is_valid`, `iter_errors`,
`to_dict`, `to_json`, `to_etree`, `from_json`, `XMLResource`, `fetch_resource`,
`fetch_schema`, `fetch_namespaces`, `ParkerConverter`, `BadgerFishConverter`,
`JsonMLConverter`, and `ColumnarConverter`. The public
`xmlschema.exceptions` module supplies `XMLResourceBlocked` for resource-policy
failures.

## Product State Model
An `XMLSchema` instance retains its target namespace, namespace mappings,
include/import registrations, built state, global component maps, root
elements, and locations. XML resources retain local source and URL state.
Decoded mappings, JSON text, XML elements, converter projections, and exported
local XSD files are views of the same generated fixtures.

## Error Semantics
Valid local documents return successful validation results and empty error
collections. Invalid documents return `False`, nonempty `iter_errors()` output,
or a validation exception from strict operations. Resource restrictions raise
the public resource-blocking exception. Exact exception prose and complete
traceback strings are not contractual.

## Cross-View Invariants
- A valid local fixture is accepted by package and schema validation APIs.
- `to_dict` and `to_json` agree on stable business fields.
- Mapping-to-XML and JSON-to-XML projections produce the generated root name.
- Converter projections can be decoded and re-encoded while preserving their
  documented structural convention.
- Include/import maps and root/component projections identify the same public
  declarations.
- An exported local schema bundle can be loaded offline and validate the same
  XML fixture.
- CLI output files are deterministic local projections that can be consumed by
  the opposite CLI conversion.

## Representative Workflows
1. Generate a schema with an included type library and an imported namespace,
   build it, validate a document, decode it, and inspect component maps.
2. Decode a valid document with a converter, encode the projection, and check
   the generated root and validation outcome.
3. Convert XML to JSON with the CLI, convert that JSON back to XML, and
   validate the rebuilt document.
4. Export the schema and its dependencies to a local directory, reload the
   exported XSD, and validate the original local XML.

## Non-Goals
This specification does not require remote access, network isolation claims,
optional dependency parity, exhaustive standards coverage, private attributes,
upstream test modules, exact diagnostics, serialized snapshots, or performance
and memory guarantees.

## Invocation Protocol
The verifier is run with `pytest` against the two packaged test files.
Fixtures are generated inside pytest temporary directories. No network,
subprocess, sleep, host-state, or persistent external resource is required.

## Environment
Reference execution uses Python 3.10 or Python 3.11 on Linux without network access.
The target package is not pre-installed; the fixed checkout is placed on
`PYTHONPATH` and `elementpath==5.1.3` is available. `pytest` and
`pytest-json-report` are required. Optional lxml and remote-resource support are
not required.

## Evaluation Notes
Tests assert public return types, structural values, component names, tags,
exit codes, and stable fields. They do not assert exact error messages or
whole serialized output snapshots. Integration cases each compose two or more
public operations and declare dependencies on physical atomic test names.
