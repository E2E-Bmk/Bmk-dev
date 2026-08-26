# spec_test_map — avsc-avro-type-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::the eight primitive names compile to types with matching typeName | atomic | positive | section Type Construction And Names | covered | AV-TYP-001 |
| atomic::isType recognizes types and filters by typeName prefix | atomic | positive | section Type Construction And Names | covered | AV-TYP-001 |
| atomic::record types expose typeName, name, and typed fields | atomic | positive | section Type Construction And Names | covered | AV-TYP-002 |
| atomic::field lookup returns declared metadata and defaults | atomic | positive | section Type Construction And Names | covered | AV-TYP-002, AV-TYP-004 |
| atomic::declared defaults let validation accept omitted fields | atomic | positive | section Type Construction And Names + section Value Validation And Algebra | covered | AV-TYP-004, AV-VAL-007 |
| atomic::recordConstructor builds declaration-order instances | atomic | positive | section Type Construction And Names | covered | AV-TYP-003 |
| atomic::field defaults must validate against the field type | atomic | positive | section Type Construction And Names | covered | AV-TYP-004 |
| atomic::a record schema without a name compiles with name undefined | atomic | positive | section Type Construction And Names | covered | AV-TYP-005 |
| atomic::omitRecordMethods strips generated prototype methods | atomic | positive | section Type Construction And Names | covered | AV-TYP-006 |
| atomic::enums expose symbols and accept exactly those strings | atomic | positive | section Type Construction And Names + section Value Validation And Algebra | covered | AV-TYP-007, AV-VAL-006 |
| atomic::enum symbols must be valid identifiers | atomic | failure_path | section Type Construction And Names | covered | AV-TYP-007 |
| atomic::fixeds expose size and accept only exact-length buffers | atomic | positive | section Type Construction And Names + section Value Validation And Algebra | covered | AV-TYP-008, AV-VAL-005 |
| atomic::array and map types validate homogeneous containers | atomic | positive | section Type Construction And Names | covered | AV-TYP-009 |
| atomic::duplicate branches and directly nested unions raise | atomic | failure_path | section Type Construction And Names | covered | AV-TYP-010 |
| atomic::unwrapped unions hold bare branch values | atomic | positive | section Type Construction And Names | covered | AV-TYP-011 |
| atomic::wrapped unions hold single-key branch objects with unwrap | atomic | positive | section Type Construction And Names | covered | AV-TYP-012 |
| atomic::the default union mode wraps only ambiguous numeric unions | atomic | positive | section Type Construction And Names | covered | AV-TYP-013 |
| atomic::names qualify through namespaces, dots, and the namespace option | atomic | positive | section Type Construction And Names | covered | AV-TYP-014 |
| atomic::nested named types inherit the enclosing namespace unless dotted | atomic | positive | section Type Construction And Names | covered | AV-TYP-014 |
| atomic::a shared registry reuses compiled named types by reference | atomic | positive | section Type Construction And Names | covered | AV-TYP-015 |
| atomic::referencing an undefined type name raises | atomic | failure_path | section Type Construction And Names | covered | AV-TYP-016 |
| atomic::recursive references compile and validate | atomic | positive | section Type Construction And Names | covered | AV-TYP-017 |
| atomic::logical types wrap the underlying codec | atomic | positive | section Type Construction And Names | covered | AV-TYP-018 |
| atomic::unregistered logicalType attributes are ignored | atomic | positive | section Type Construction And Names | covered | AV-TYP-019 |
| atomic::isValid answers without throwing on foreign shapes | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-001 |
| atomic::int accepts exactly signed 32-bit integers | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-002 |
| atomic::long, float, and double numeric domains | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-003, AV-VAL-004 |
| atomic::bytes, string, and null value domains | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-005 |
| atomic::records validate declared fields and ignore extras by default | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-007 |
| atomic::noUndeclaredFields rejects undeclared properties | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-008 |
| atomic::errorHook reports each mismatch with its path | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-009 |
| atomic::clone deep-copies valid values and rejects invalid ones | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-010 |
| atomic::coerceBuffers converts JSON buffer shapes during clone | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-011 |
| atomic::clone drops undeclared properties in every mode | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-012 |
| atomic::compare follows Avro order with field order attributes | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-013 |
| atomic::compareBuffers agrees with compare | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-014 |
| atomic::random produces values the type validates | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-015 |
| atomic::wrap boxes values in their branch shape | atomic | positive | section Value Validation And Algebra | covered | AV-VAL-015 |
| atomic::toBuffer, toString, and clone raise on invalid values | atomic | failure_path | section Binary Encoding + section Error Semantics | covered | AV-BIN-001, AV-ERR-002 |
| atomic::fromBuffer raises on truncated and trailing bytes | atomic | positive | section Binary Encoding + section Error Semantics | covered | AV-BIN-002, AV-ERR-002 |
| atomic::binary round trips return equal constructor instances | atomic | positive | section Binary Encoding | covered | AV-BIN-003 |
| atomic::ints and longs use zigzag varints | atomic | positive | section Binary Encoding | covered | AV-BIN-004 |
| atomic::strings and bytes are length-prefixed and UTF-8 | atomic | positive | section Binary Encoding | covered | AV-BIN-005 |
| atomic::float, double, boolean, and null encodings | atomic | positive | section Binary Encoding | covered | AV-BIN-006 |
| atomic::enums encode indices and fixeds copy raw bytes | atomic | positive | section Binary Encoding | covered | AV-BIN-007 |
| atomic::arrays and maps encode counted blocks with terminators | atomic | positive | section Binary Encoding | covered | AV-BIN-008 |
| atomic::unions encode a branch tag before the branch value | atomic | positive | section Binary Encoding | covered | AV-BIN-009 |
| atomic::record fields encode in declaration order without markers | atomic | positive | section Binary Encoding | covered | AV-BIN-010 |
| atomic::float narrows doubles to single precision | atomic | positive | section Binary Encoding | covered | AV-BIN-011 |
| atomic::toString and fromString round-trip record values | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-001, AV-JSN-002 |
| atomic::union values serialize as branch-keyed JSON in every mode | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-001, AV-JSN-002 |
| atomic::schema output is canonical unless attributes are exported | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-003 |
| atomic::noDeref and toJSON projections | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-003, AV-JSN-004 |
| atomic::toString without a value prints the schema with names dereferenced once | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-004 |
| atomic::fingerprints digest the canonical schema | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-005 |
| atomic::equals compares canonical schemas | atomic | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-006 |
| atomic::primitive promotions resolve and demotions raise | atomic | positive | section Schema Evolution | covered | AV-EVO-001 |
| atomic::string and bytes promote to each other | atomic | positive | section Schema Evolution | covered | AV-EVO-001 |
| atomic::containers and fixeds resolve elementwise | atomic | positive | section Schema Evolution | covered | AV-EVO-002 |
| atomic::enum evolution honors reader defaults | atomic | positive | section Schema Evolution | covered | AV-EVO-003 |
| atomic::record evolution fills defaults and follows aliases | atomic | positive | section Schema Evolution | covered | AV-EVO-004 |
| atomic::unresolvable schemas raise at resolver creation | atomic | failure_path | section Schema Evolution | covered | AV-EVO-004, AV-EVO-005, AV-EVO-007 |
| atomic::reader unions absorb writer non-unions | atomic | positive | section Schema Evolution | covered | AV-EVO-006 |
| atomic::reader non-unions require every writer branch to resolve | atomic | positive | section Schema Evolution | covered | AV-EVO-007 |
| atomic::resolver decoding reorders fields and skips writer extras | atomic | positive | section Schema Evolution | covered | AV-EVO-008 |
| atomic::resolvers bind to their creating instance | atomic | positive | section Schema Evolution | covered | AV-EVO-009 |
| atomic::forValue infers primitive types | atomic | positive | section Type Inference | covered | AV-INF-001 |
| atomic::forValue infers containers and anonymous records | atomic | positive | section Type Inference | covered | AV-INF-001 |
| atomic::forTypes widens numbers and unions incompatibles | atomic | positive | section Type Inference | covered | AV-INF-002 |
| atomic::readSchema produces forSchema-ready shapes | atomic | positive | section IDL Parsing | covered | AV-IDL-001 |
| atomic::readProtocol parses protocols with messages | atomic | positive | section IDL Parsing | covered | AV-IDL-002 |
| atomic::malformed IDL raises | atomic | failure_path | section IDL Parsing | covered | AV-IDL-003 |
| integration::codec agreement holds for accepted and rejected values | integration | positive | section Cross-View Invariants | covered | AV-CVI-001; CVI-001 |
| integration::complex schemas round-trip through schema output | integration | positive | section Cross-View Invariants | covered | AV-CVI-002; CVI-002 |
| integration::an evolution chain carries data across three versions | integration | positive | section Cross-View Invariants + section Schema Evolution | covered | AV-CVI-003, AV-EVO-004, AV-EVO-008; CVI-003 |
| integration::independently compiled equal types exchange binary data | integration | positive | section Cross-View Invariants + section Binary Encoding | covered | AV-CVI-002, AV-BIN-003; CVI-002 |
| integration::sorting by compare matches sorting by encoded buffers | integration | positive | section Cross-View Invariants + section Value Validation And Algebra | covered | AV-CVI-005, AV-VAL-013, AV-VAL-014; CVI-005 |
| integration::inference closes over its inputs | integration | positive | section Cross-View Invariants + section Type Inference | covered | AV-CVI-004, AV-INF-001, AV-INF-002; CVI-004 |
| integration::IDL-compiled types behave like hand-written schemas | integration | positive | section Cross-View Invariants + section IDL Parsing | covered | AV-CVI-006, AV-IDL-001; CVI-006 |
| integration::shared registries expose one instance across schemas | integration | positive | section Cross-View Invariants + section Type Construction And Names | covered | AV-CVI-007, AV-TYP-015; CVI-007 |
| integration::wrapped and unwrapped unions share the wire format | integration | positive | section Type Construction And Names + section Binary Encoding | covered | AV-TYP-011, AV-TYP-012, AV-BIN-009 |
| integration::logical types project through validation, codecs, and evolution | integration | positive | section Type Construction And Names + section Schema Evolution + section Cross-View Invariants | covered | AV-TYP-018, AV-EVO-001, AV-CVI-001; CVI-001 |
| integration::composite records encode their parts in sequence | integration | positive | section Binary Encoding | covered | AV-BIN-010, AV-BIN-007, AV-BIN-008 |
| integration::recursive types round-trip through binary and JSON | integration | positive | section Type Construction And Names + section Cross-View Invariants | covered | AV-TYP-017, AV-CVI-001; CVI-001 |
| integration::resolver output stays within the reader's value domain | integration | positive | section Cross-View Invariants + section Schema Evolution | covered | AV-CVI-003, AV-EVO-001; CVI-003 |
| integration::JSON-transported buffers re-enter the binary codec | integration | positive | section Value Validation And Algebra + section Binary Encoding | covered | AV-VAL-011, AV-BIN-003 |
| integration::validation hooks and strict mode compose across nesting | integration | positive | section Value Validation And Algebra | covered | AV-VAL-008, AV-VAL-009 |
| integration::canonical projection ignores decoration attributes | integration | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-003, AV-JSN-005, AV-JSN-006 |
| integration::inferred writers feed declared readers | integration | positive | section Type Inference + section Schema Evolution + section Cross-View Invariants | covered | AV-INF-001, AV-EVO-001, AV-CVI-004; CVI-004 |
| integration::protocol types compile into working codecs | integration | positive | section IDL Parsing + section Binary Encoding | covered | AV-IDL-002, AV-BIN-003 |
| integration::both codecs agree across a composite document | integration | positive | section Cross-View Invariants + section JSON Encoding And Schema Projection | covered | AV-CVI-001, AV-JSN-001; CVI-001 |
| integration::random values traverse the full pipeline | integration | positive | section Value Validation And Algebra + section Cross-View Invariants | covered | AV-VAL-015, AV-CVI-001; CVI-001 |
| integration::fingerprints distinguish and identify schema versions | integration | positive | section JSON Encoding And Schema Projection | covered | AV-JSN-005, AV-JSN-006 |
| integration::publish and evolve a message schema across a registry | system_e2e | positive | section Cross-View Invariants + section Type Construction And Names + section Schema Evolution | covered | AV-CVI-007, AV-CVI-003, AV-TYP-015, AV-EVO-004; CVI-007 |
| integration::an IDL protocol drives a binary message exchange | system_e2e | positive | section Cross-View Invariants + section IDL Parsing + section Binary Encoding | covered | AV-CVI-006, AV-IDL-002, AV-BIN-003; CVI-006 |
| integration::infer, refine, and evolve a log schema from samples | system_e2e | positive | section Cross-View Invariants + section Type Inference + section Schema Evolution | covered | AV-CVI-004, AV-INF-002, AV-EVO-001, AV-CVI-005; CVI-004 |
| integration::timestamps flow through a logical type end to end | system_e2e | positive | section Type Construction And Names + section Cross-View Invariants + section Schema Evolution + section JSON Encoding And Schema Projection | covered | AV-TYP-018, AV-CVI-001, AV-EVO-001, AV-JSN-003; CVI-001 |
| integration::a document store reads every version it ever wrote | system_e2e | positive | section Cross-View Invariants + section Schema Evolution + section JSON Encoding And Schema Projection | covered | AV-CVI-003, AV-EVO-004, AV-JSN-005, AV-CVI-002; CVI-003 |
| integration::a wrapped-union envelope routes typed payloads | system_e2e | positive | section Type Construction And Names + section Cross-View Invariants + section Binary Encoding | covered | AV-TYP-012, AV-CVI-001, AV-BIN-009; CVI-001 |

Total: 99 | kept (covered): 99 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 99

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
