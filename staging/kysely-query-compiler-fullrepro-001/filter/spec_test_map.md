# spec_test_map — kysely-query-compiler-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::a filtered selection compiles to sql text with ordered parameters | atomic | positive | section Query Compiler Instances And Dialects + section Row Selection Queries | covered | KYSL-INST-004, KYSL-SEL-005 |
| atomic::mysql and sqlite compilers render their own quoting and placeholder styles | atomic | positive | section Query Compiler Instances And Dialects | covered | KYSL-INST-006, KYSL-INST-007 |
| atomic::repeated compilation returns equal sql and parameters | atomic | positive | section Query Compiler Instances And Dialects | covered | KYSL-INST-005 |
| atomic::constructing an instance without a dialect throws | atomic | failure_path | section Query Compiler Instances And Dialects + section Error Semantics | covered | KYSL-INST-003, KYSL-ERR-001 |
| atomic::a query with no bound values compiles with an empty parameters array | atomic | positive | section Query Compiler Instances And Dialects | covered | KYSL-INST-004 |
| atomic::a table alias registers through the as form | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-001, KYSL-SEL-003 |
| atomic::selectNoFrom compiles a from-less selection | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-004 |
| atomic::select accepts a single column, a list, and aliases | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-002 |
| atomic::qualified column names render each segment quoted | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-002 |
| atomic::selectAll and distinct render star and distinct forms | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-003 |
| atomic::repeated where calls join with and in call order | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-005 |
| atomic::whereRef compares two columns without binding | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-006 |
| atomic::is and is not render null literally without parameters | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-007 |
| atomic::equality with null binds null as a parameter | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-007 |
| atomic::clearWhere discards accumulated filters | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-008 |
| atomic::a subquery is accepted as a filter right-hand side | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-014 |
| atomic::innerJoin renders an on clause from column references | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-009 |
| atomic::leftJoin callback combines onRef and parameterized on conditions | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-009 |
| atomic::a derived table joins as an aliased subquery | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-010 |
| atomic::groupBy and having accept aggregate and simple forms | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-011 |
| atomic::orderBy accumulates terms with optional directions | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-012 |
| atomic::limit and offset bind counts as parameters in every dialect | atomic | positive | section Row Selection Queries | covered | KYSL-SEL-013 |
| atomic::the expression builder renders a comparison with a bound value | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-001 |
| atomic::inequality operators render exactly as written | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-001 |
| atomic::an operator outside the supported set is rejected by name | atomic | failure_path | section Expressions And Scalar Functions + section Error Semantics | covered | KYSL-EXPR-002, KYSL-ERR-002 |
| atomic::or and and lists render inside one pair of parentheses | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-003 |
| atomic::not prefixes the wrapped expression | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-003 |
| atomic::between binds both bounds | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-004 |
| atomic::in binds one parameter per element and an empty list renders bare parentheses | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-005 |
| atomic::like and ilike bind their patterns | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-001 |
| atomic::exists wraps a correlated subquery | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-006 |
| atomic::a correlated subquery projects as an aliased column | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-006 |
| atomic::a case expression parameterizes then and else values | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-007 |
| atomic::cast renders the target type unquoted and val binds through coalesce | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-008, KYSL-EXPR-009 |
| atomic::fn renders a generic function over column references | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-009 |
| atomic::aggregate helpers render count and distinct | atomic | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-009 |
| atomic::insert renders columns from object keys and binds values | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-001 |
| atomic::multi-row insert unions columns and renders default for gaps | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-002 |
| atomic::a raw fragment inserts inline instead of binding | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-003 |
| atomic::defaultValues renders the default values clause | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-004 |
| atomic::on conflict renders do nothing and parameterized do update set | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-005 |
| atomic::mysql ignore renders insert ignore | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-006 |
| atomic::returning lists columns and returningAll renders star | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-007 |
| atomic::update set renders assignments in key order | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-008 |
| atomic::update set accepts expression assignments | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-008 |
| atomic::delete renders with filters and returning | atomic | positive | section Insert, Update And Delete | covered | KYSL-MUT-009, KYSL-MUT-007 |
| atomic::with prepends common table expressions in declaration order | atomic | positive | section Query Composition And Reuse | covered | KYSL-COMP-001 |
| atomic::withRecursive renders the recursive keyword and column list | atomic | positive | section Query Composition And Reuse | covered | KYSL-COMP-002 |
| atomic::union and unionAll chain in call order | atomic | positive | section Query Composition And Reuse | covered | KYSL-COMP-003 |
| atomic::$if applies its refinement only when the condition is true | atomic | positive | section Query Composition And Reuse | covered | KYSL-COMP-004 |
| atomic::deriving a builder leaves the original unchanged | atomic | positive | section Query Composition And Reuse + section Cross-View Invariants | covered | KYSL-COMP-005, KYSL-INV-003 |
| atomic::the template tag binds interpolations in order | atomic | positive | section Raw SQL Fragments | covered | KYSL-RAW-001, KYSL-RAW-002 |
| atomic::a fragment renders under the dialect it compiles against | atomic | positive | section Raw SQL Fragments | covered | KYSL-RAW-002, KYSL-RAW-004 |
| atomic::identifier helpers render quoted references | atomic | positive | section Raw SQL Fragments | covered | KYSL-RAW-004 |
| atomic::lit inlines a literal and raw splices verbatim | atomic | positive | section Raw SQL Fragments | covered | KYSL-RAW-005 |
| atomic::join renders parameters with a default and a custom separator | atomic | positive | section Raw SQL Fragments | covered | KYSL-RAW-006 |
| atomic::a fragment serves as a filter left-hand side | atomic | positive | section Raw SQL Fragments | covered | KYSL-RAW-003 |
| atomic::camel case plugin renders snake case tables and columns | atomic | positive | section Identifier Transforms And Schema Scoping | covered | KYSL-PLUG-001 |
| atomic::camel case plugin transforms alias positions qualified refs and raw refs | atomic | positive | section Identifier Transforms And Schema Scoping | covered | KYSL-PLUG-001 |
| atomic::camel case plugin leaves parameters untouched | atomic | positive | section Identifier Transforms And Schema Scoping + section Cross-View Invariants | covered | KYSL-PLUG-002, KYSL-INV-004 |
| atomic::withSchema qualifies table references across statement kinds | atomic | positive | section Identifier Transforms And Schema Scoping | covered | KYSL-PLUG-003 |
| atomic::createTable passes column types through and lists columns | atomic | positive | section Schema Definition Statements | covered | KYSL-DDL-001, KYSL-DDL-002 |
| atomic::references with onDelete renders the foreign key action | atomic | positive | section Schema Definition Statements | covered | KYSL-DDL-002 |
| atomic::column modifiers render in canonical order regardless of call order | atomic | positive | section Schema Definition Statements | covered | KYSL-DDL-002 |
| atomic::defaultTo inlines literals and raw fragments | atomic | positive | section Schema Definition Statements | covered | KYSL-DDL-003 |
| atomic::createIndex dropTable and alterTable render their statements | atomic | positive | section Schema Definition Statements | covered | KYSL-DDL-004 |
| atomic::schema statements compile with empty parameters | atomic | positive | section Schema Definition Statements | covered | KYSL-DDL-005 |
| atomic::execute resolves with no rows and executeTakeFirst resolves undefined under the dummy driver | atomic | positive | section Execution Lifecycle | covered | KYSL-EXEC-001 |
| atomic::executeTakeFirstOrThrow rejects with NoResultError | atomic | failure_path | section Execution Lifecycle + section Error Semantics | covered | KYSL-EXEC-002, KYSL-ERR-003 |
| atomic::execution after destroy rejects while compilation still works | atomic | failure_path | section Execution Lifecycle + section Error Semantics + section Cross-View Invariants | covered | KYSL-EXEC-003, KYSL-ERR-004, KYSL-INV-006 |
| integration::one join query compiles under all three dialects with identical parameters | integration | positive | section Cross-View Invariants + section Query Compiler Instances And Dialects + section Row Selection Queries | covered | KYSL-INV-001, KYSL-INST-006, KYSL-INST-007, KYSL-SEL-009; Seam: builder AST x three dialect compilers |
| integration::placeholder counts equal parameter lengths across dialects | integration | positive | section Cross-View Invariants + section Expressions And Scalar Functions + section Row Selection Queries | covered | KYSL-INV-002, KYSL-EXPR-005, KYSL-SEL-013; Seam: expression parameters x dialect placeholder styles |
| integration::a mysql pipeline renders question marks throughout | integration | positive | section Query Compiler Instances And Dialects + section Row Selection Queries | covered | KYSL-INST-006, KYSL-SEL-013, KYSL-SEL-009; Seam: full select pipeline x mysql compiler |
| integration::a sqlite insert returning renders question marks with double quotes | integration | positive | section Insert, Update And Delete + section Query Compiler Instances And Dialects | covered | KYSL-MUT-007, KYSL-INST-006; Seam: mutation returning x sqlite compiler |
| integration::a cte feeds a join with grouped aggregation | integration | positive | section Query Composition And Reuse + section Row Selection Queries + section Expressions And Scalar Functions | covered | KYSL-COMP-001, KYSL-SEL-009, KYSL-EXPR-009, KYSL-SEL-011; Seam: CTE x join x aggregation |
| integration::chained ctes reference earlier definitions and union a tail | integration | positive | section Query Composition And Reuse | covered | KYSL-COMP-001, KYSL-COMP-003; Seam: chained CTEs x set operations |
| integration::a recursive counter cte compiles with a union all body | integration | positive | section Query Composition And Reuse | covered | KYSL-COMP-002, KYSL-COMP-003; Seam: recursive CTE x union all body |
| integration::an exists filter pairs with a correlated projection | integration | positive | section Expressions And Scalar Functions + section Row Selection Queries | covered | KYSL-EXPR-006, KYSL-SEL-005; Seam: correlated projection x exists filter |
| integration::a derived table join filters on expressions | integration | positive | section Row Selection Queries + section Expressions And Scalar Functions | covered | KYSL-SEL-010, KYSL-EXPR-003; Seam: derived table join x boolean expression trees |
| integration::conditional refinements match a hand-built chain | integration | positive | section Query Composition And Reuse | covered | KYSL-COMP-004, KYSL-COMP-005; Seam: conditional refinement x hand-built equivalence |
| integration::clearWhere resets filters before new ones apply | integration | positive | section Row Selection Queries | covered | KYSL-SEL-008, KYSL-SEL-005; Seam: filter reset x re-filtering |
| integration::case cast and aggregates compose in one projection | integration | positive | section Expressions And Scalar Functions | covered | KYSL-EXPR-007, KYSL-EXPR-008, KYSL-EXPR-009; Seam: case x cast x aggregate in one projection |
| integration::a multi-row insert with conflict handling and returning binds in order | integration | positive | section Insert, Update And Delete | covered | KYSL-MUT-002, KYSL-MUT-005, KYSL-MUT-007; Seam: multi-row insert x conflict clause x returning |
| integration::an update mixes expression assignments with bound values and returning | integration | positive | section Insert, Update And Delete | covered | KYSL-MUT-008, KYSL-MUT-007; Seam: expression assignments x bound assignments x returning |
| integration::a delete filters through a subquery and returns rows | integration | positive | section Row Selection Queries + section Insert, Update And Delete | covered | KYSL-SEL-014, KYSL-MUT-009, KYSL-MUT-007; Seam: delete x subquery filter x returning |
| integration::embedded fragment parameters interleave left to right | integration | positive | section Raw SQL Fragments + section Cross-View Invariants | covered | KYSL-RAW-003, KYSL-INV-005; Seam: fragment parameters x builder parameters |
| integration::fragment values keep interpolation order standalone and embedded | integration | positive | section Cross-View Invariants + section Raw SQL Fragments | covered | KYSL-INV-005, KYSL-RAW-001; Seam: standalone fragment compile x embedded compile |
| integration::identifier helpers follow the compiling dialect | integration | positive | section Raw SQL Fragments + section Query Compiler Instances And Dialects | covered | KYSL-RAW-002, KYSL-RAW-004, KYSL-INST-006; Seam: identifier helpers x dialect quoting |
| integration::camel case rewrite leaves mutation parameters identical | integration | positive | section Identifier Transforms And Schema Scoping + section Cross-View Invariants | covered | KYSL-PLUG-001, KYSL-PLUG-002, KYSL-INV-004; Seam: plugin identifier rewrite x mutation parameters |
| integration::schema scoping spans queries mutations and ddl | integration | positive | section Identifier Transforms And Schema Scoping + section Insert, Update And Delete + section Schema Definition Statements | covered | KYSL-PLUG-003, KYSL-MUT-008, KYSL-DDL-001; Seam: schema scoping x queries x mutations x ddl |
| integration::camel case composes with schema scoping | integration | positive | section Identifier Transforms And Schema Scoping | covered | KYSL-PLUG-001, KYSL-PLUG-003; Seam: camel case plugin x schema scoping |
| integration::a shared base branches into independent queries | integration | positive | section Query Composition And Reuse + section Cross-View Invariants | covered | KYSL-COMP-005, KYSL-INV-003; Seam: shared base builder x independent branches |
| integration::define schema insert query and destroy in one lifecycle | system_e2e | positive | section Schema Definition Statements + section Insert, Update And Delete + section Row Selection Queries + section Execution Lifecycle + section Cross-View Invariants | covered | KYSL-DDL-001, KYSL-MUT-001, KYSL-SEL-009, KYSL-EXEC-001, KYSL-EXEC-003, KYSL-INV-006; Seam: ddl x mutation x selection x execution lifecycle |
| integration::one reporting query compiles under all dialects and executes | system_e2e | positive | section Cross-View Invariants + section Execution Lifecycle | covered | KYSL-INV-001, KYSL-INV-002, KYSL-EXEC-001; Seam: one definition x three dialects x execution |
| integration::a camel case pipeline runs from ddl to select | system_e2e | positive | section Identifier Transforms And Schema Scoping + section Schema Definition Statements + section Insert, Update And Delete + section Execution Lifecycle | covered | KYSL-PLUG-001, KYSL-DDL-001, KYSL-MUT-001, KYSL-EXEC-001; Seam: camel case plugin x ddl x mutation x execution |
| integration::raw fragments builders ctes and unions cooperate end to end | system_e2e | positive | section Query Composition And Reuse + section Raw SQL Fragments + section Execution Lifecycle | covered | KYSL-COMP-001, KYSL-COMP-003, KYSL-RAW-003, KYSL-EXEC-002; Seam: ctes x unions x raw fragments x execution errors |

Total: 96 | kept (covered): 96 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 96

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
