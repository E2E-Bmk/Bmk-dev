# spec_test_map — orama-search-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::create yields an empty instance with zero count | atomic | positive | section Instance Creation And Schema | covered | ORAMA-CRE-001 |
| atomic::create rejects an unknown schema type string | atomic | failure_path | section Instance Creation And Schema + section Error Semantics | covered | ORAMA-CRE-003, ORAMA-ERR-001 |
| atomic::insert returns a generated string id when the document has none | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-001 |
| atomic::insert uses the document id property as the stored id | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-001 |
| atomic::insertMultiple returns the assigned ids in document order | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-002 |
| atomic::insert rejects a document whose value contradicts the schema type | atomic | failure_path | section Document Lifecycle + section Error Semantics | covered | ORAMA-DOC-004, ORAMA-ERR-002 |
| atomic::insert rejects a duplicate document id | atomic | failure_path | section Document Lifecycle + section Error Semantics | covered | ORAMA-DOC-003, ORAMA-ERR-003 |
| atomic::documents keep omitted schema fields absent and extra fields verbatim | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-005, ORAMA-DOC-007 |
| atomic::count reflects the number of stored documents | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-006 |
| atomic::getByID returns undefined for an unknown id | atomic | positive | section Document Lifecycle + section Error Semantics | covered | ORAMA-DOC-007, ORAMA-ERR-007 |
| atomic::remove returns true for a present id and decrements count | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-008 |
| atomic::remove returns false for a missing id and leaves the store unchanged | atomic | failure_path | section Document Lifecycle + section Error Semantics | covered | ORAMA-DOC-008, ORAMA-ERR-008 |
| atomic::removeMultiple returns the number of documents actually removed | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-009 |
| atomic::update replaces the stored document and returns the new id | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-010 |
| atomic::updateMultiple replaces several documents and returns the new ids | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-011 |
| atomic::upsert inserts a new document when the id is absent | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-012 |
| atomic::upsert replaces an existing document without changing the count | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-012 |
| atomic::upsertMultiple mixes inserts and replacements and returns the ids | atomic | positive | section Document Lifecycle | covered | ORAMA-DOC-013 |
| atomic::search result carries hits with id score and document plus count and elapsed | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-001 |
| atomic::term matching is case-insensitive | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-003 |
| atomic::a query token matches indexed tokens by prefix | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-004 |
| atomic::omitting the term matches every stored document | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-005 |
| atomic::properties restricts full-text matching to the named string properties | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-006 |
| atomic::searching an unknown property raises UNKNOWN_INDEX | atomic | failure_path | section Full-Text Search + section Error Semantics | covered | ORAMA-FTS-007, ORAMA-ERR-004 |
| atomic::exact matching excludes prefix-only matches | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-008 |
| atomic::exact matching suppresses tolerance | atomic | failure_path | section Full-Text Search | covered | ORAMA-FTS-008 |
| atomic::tolerance admits tokens within the edit distance | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-009 |
| atomic::a misspelled token without tolerance matches nothing | atomic | failure_path | section Full-Text Search | covered | ORAMA-FTS-009 |
| atomic::threshold zero returns only documents matching every token | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-010 |
| atomic::default threshold returns documents matching any token | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-010 |
| atomic::limit and offset slice ranked hits while count stays total | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-012 |
| atomic::preflight reports the matched count with empty hits | atomic | positive | section Full-Text Search | covered | ORAMA-FTS-013 |
| atomic::number filters support comparison operators | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-001 |
| atomic::number between filter is inclusive on both ends | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-001 |
| atomic::boolean filters accept a direct boolean value | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-002 |
| atomic::enum filters support eq in and nin operators | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-003 |
| atomic::string filters match whole tokens without prefix expansion | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-004 |
| atomic::string array filters match documents containing the element | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-005 |
| atomic::nested dot path properties participate in filters | atomic | positive | section Instance Creation And Schema + section Filters, Facets, Groups, And Sorting | covered | ORAMA-CRE-002, ORAMA-STR-001 |
| atomic::filtering on an unknown property raises UNKNOWN_FILTER_PROPERTY | atomic | failure_path | section Filters, Facets, Groups, And Sorting + section Error Semantics | covered | ORAMA-STR-007, ORAMA-ERR-005 |
| atomic::enum facets report distinct value buckets and their count | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-008 |
| atomic::boolean facets bucket documents under true and false string keys | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-008 |
| atomic::string array facets count documents per distinct element | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-008 |
| atomic::number facets bucket matched documents into inclusive ranges | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-009 |
| atomic::string facets honor sort and limit options | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-010 |
| atomic::sortBy orders hits by a number property in both directions | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-011 |
| atomic::sortBy orders hits by a nested dot path property | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-011 |
| atomic::sortBy accepts a comparator over id score document triples | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-012 |
| atomic::groupBy partitions matched documents and bounds results per group | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-013 |
| atomic::groupBy rejects enum properties | atomic | failure_path | section Filters, Facets, Groups, And Sorting + section Error Semantics | covered | ORAMA-STR-014, ORAMA-ERR-006 |
| atomic::distinctOn keeps the first hit per distinct value while count stays total | atomic | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-015 |
| atomic::save returns a JSON-serializable snapshot | atomic | positive | section Persistence | covered | ORAMA-PER-001 |
| integration::an inserted document is visible across count getByID search facets and groups | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-001; Seam: state consistency |
| integration::a removed document disappears from every projection simultaneously | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-002; Seam: state consistency |
| integration::count stays the unsliced total across limit offset preflight and distinct | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-003; Seam: state consistency |
| integration::hit documents deep-equal getByID lookups | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-004; Seam: state consistency |
| integration::facet bucket totals equal the matched documents carrying the property | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-005; Seam: state consistency |
| integration::update redirects full-text matching filters and facets to the new content | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-006; Seam: state consistency |
| integration::save and load preserve count lookups and ranked order | system_e2e | positive | section Cross-View Invariants + section Persistence | covered | ORAMA-CVI-007, ORAMA-PER-002; Seam: lifecycle crossing |
| integration::documents inserted after load join restored ones in results | system_e2e | positive | section Cross-View Invariants + section Persistence | covered | ORAMA-CVI-007, ORAMA-PER-002; Seam: lifecycle crossing |
| integration::groupBy places every matched document in exactly one group | integration | positive | section Cross-View Invariants | covered | ORAMA-CVI-008; Seam: state consistency |
| integration::term and where filters combine conjunctively | integration | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-006; Seam: config interaction |
| integration::multiple where clauses form a conjunction | integration | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-006; Seam: config interaction |
| integration::facets aggregate only over filtered matches | integration | positive | section Cross-View Invariants + section Filters, Facets, Groups, And Sorting | covered | ORAMA-CVI-005, ORAMA-STR-008; Seam: config interaction |
| integration::boost reorders title and body matches without changing the match set | integration | positive | section Full-Text Search | covered | ORAMA-FTS-011; Seam: config interaction |
| integration::threshold composes with filters | integration | positive | section Full-Text Search + section Filters, Facets, Groups, And Sorting | covered | ORAMA-FTS-010, ORAMA-STR-006; Seam: config interaction |
| integration::sortBy with distinctOn keeps the first sorted hit per distinct value | integration | positive | section Filters, Facets, Groups, And Sorting | covered | ORAMA-STR-011, ORAMA-STR-015; Seam: config interaction |
| integration::offset windows partition the sorted hit sequence | integration | positive | section Full-Text Search + section Filters, Facets, Groups, And Sorting | covered | ORAMA-FTS-012, ORAMA-STR-011; Seam: protocol handoff |
| integration::insertMultiple and repeated insert produce equivalent projections | integration | positive | section Document Lifecycle | covered | ORAMA-DOC-001, ORAMA-DOC-002; Seam: protocol handoff |
| integration::a failed search leaves the instance usable | integration | positive | section Filters, Facets, Groups, And Sorting + section Error Semantics | covered | ORAMA-STR-007, ORAMA-ERR-005; Seam: error propagation |
| integration::a rejected insert leaves all projections unchanged | integration | positive | section Document Lifecycle + section Error Semantics | covered | ORAMA-DOC-004, ORAMA-ERR-002; Seam: error propagation |
| integration::upsert replacement makes stale content unmatchable | integration | positive | section Document Lifecycle + section Cross-View Invariants | covered | ORAMA-DOC-012, ORAMA-CVI-006; Seam: state consistency |
| integration::removeMultiple recomputes facets and groups | integration | positive | section Document Lifecycle + section Cross-View Invariants | covered | ORAMA-DOC-009, ORAMA-CVI-002; Seam: state consistency |
| integration::nested dot path agrees across where facets and sortBy | integration | positive | section Instance Creation And Schema + section Filters, Facets, Groups, And Sorting | covered | ORAMA-CRE-002, ORAMA-STR-001, ORAMA-STR-009, ORAMA-STR-011; Seam: config interaction |
| integration::a loaded instance accepts update and remove like a native one | system_e2e | positive | section Persistence + section Document Lifecycle | covered | ORAMA-PER-002, ORAMA-DOC-010; Seam: lifecycle crossing |
| integration::distinct results survive a save load round trip | integration | positive | section Cross-View Invariants + section Filters, Facets, Groups, And Sorting | covered | ORAMA-CVI-007, ORAMA-STR-015; Seam: lifecycle crossing |
| integration::multi-token queries rank documents matching more tokens first | integration | positive | section Full-Text Search | covered | ORAMA-FTS-002, ORAMA-FTS-010; Seam: protocol handoff |
| integration::exact and threshold compose on the same query | integration | positive | section Full-Text Search | covered | ORAMA-FTS-008, ORAMA-FTS-010; Seam: config interaction |

Total: 78 | kept (covered): 78 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 78

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
