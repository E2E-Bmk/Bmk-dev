repo: mtth/avsc
source_path: https://github.com/mtth/avsc (wip/repo-cache/avsc-src)
commit: f44546ac9b91795c5845278b8bcea5e47fe67707 (npm gitHead for avsc@5.7.9)
language: typescript
src_loc: 8317 (lib/*.js; bundled types/index.d.ts ships named-export TS declarations)
test_functions: 631 (mocha tdd test() across 6 files)
test_files: 6 (test_types 300, test_services 184+40, test_specs 63, test_containers 47, test_utils 28, test_index 9)
dominant_test_styles: unit + integration over Type instances; assert-based; heavy value/byte-level checks
public_docs: https://github.com/mtth/avsc/wiki/API (full API reference), README, Avro 1.11 specification (encoding/evolution rules the library implements)
core_fact_source: one compiled type graph per schema - Type subclass instances (primitives, records with generated constructors, enums, fixed, arrays, maps, wrapped/unwrapped unions, logical types) built by Type.forSchema from JSON schemas or by readSchema/readProtocol from Avro IDL
derived_views: (1) construction/registry projection (forSchema opts: registry, namespace, wrapUnions, logicalTypes; named-type reuse; construction errors);
  (2) validation projection (isValid with errorHook; per-type value domains, e.g. long |n|<=2^53-2, int 32-bit);
  (3) binary codec projection (toBuffer/fromBuffer zigzag varints, length-prefixed strings/bytes, block-coded arrays/maps, branch-indexed unions; truncated/trailing errors);
  (4) evolution projection (createResolver: promotions int->long->float->double, string<->bytes, record field defaults/aliases, reader-union acceptance; resolver bound to creating instance);
  (5) schema projection (schema()/toString canonical forms, exportAttrs, name references for registered types, fingerprint, equals);
  (6) inference projection (Type.forValue, Type.forTypes combine);
  (7) IDL projection (readSchema/readProtocol parse Avro IDL into schema JSON that feeds forSchema);
  (8) value algebra (clone with coerceBuffers/stripUndeclaredFields, compare/compareBuffers with field order, random validity, recordConstructor classes).
external_deps: none at runtime; tests use mocha+assert only
test_import_audit: HIGH_RISK for direct reuse - every suite requires '../lib' and '../lib/<module>' relative paths (not the published package entry), and test_utils/test_containers reach module internals (Tap) -> Track B generated oracle importing only 'avsc'
docs_test_alignment: aligned - the wiki API documents the same Type surface the tests exercise; Avro spec grounds codec/evolution behavior
contamination_note: avsc@5.7.9, released 2025-07-13, relative to training cutoff: likely before for the API line (stable since 2015); difficulty rests on byte-exact codec rules, wrapUnions mode algebra, resolver matching rules, and long/int range edges rather than API novelty
decision: keep
reason: rule-engine reimplementation (Avro codec + schema-evolution resolution algebra + IDL parser) with 8 public projections over one compiled type graph; equivalence judgements (equals/fingerprint), language-rule reimplementation (IDL, content of canonical schemas), >=3-projection integration.
risks: (1) upstream tests non-portable (relative '../lib' requires) -> generated_only oracle, every expected value observed by executing 5.7.9;
  (2) services/RPC and container-file streams are large and stream-based -> excluded from scope (spec non-goals);
  (3) byte-exact assertions could drift into implementation details -> only assert encodings the Avro spec fixes (zigzag, length prefixes, block terminators) and round-trip laws;
  (4) random() is nondeterministic -> assert only isValid(random()) closure;
  (5) resolver instance binding and long-range edges are traps -> probe-grounded (wip/probe/avsc a1-a3).
scope_plan: target_subdomain=Type.forSchema construction rules (primitives, records/enums/fixed/arrays/maps/unions, names/namespaces/aliases, registry, wrapUnions modes, logicalTypes hooks), validation (isValid/errorHook, value domains), binary codec (toBuffer/fromBuffer/roundtrips, truncated/trailing errors), schema evolution (createResolver promotions, defaults, aliases, union rules), schema projection (schema()/toString/fingerprint/equals), inference (forValue/forTypes), IDL (readSchema/readProtocol), value algebra (clone opts, compare, recordConstructor); expected_oracle_max=100
excluded: Service/RPC (services.js), container files and streams (containers.js, createFileEncoder/Decoder/extractFileHeader/createBlobEncoder/Decoder), assembleProtocol file imports, parse() deprecated alias, Tap/utils internals, browser builds
