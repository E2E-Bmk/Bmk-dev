# Track A rewrite audit — casbin-policy-enforcement-fullrepro-001

Upstream test tree at e9df34e (v3.11.0), root + model + util packages.

| upstream file group | funcs | import type | rewrite attempt | result |
|---------------------|-------|-------------|-----------------|--------|
| enforcer_test.go, model_test.go (root), management_api_test.go, rbac_api_test.go, rbac_api_with_domains_test.go, abac_test.go, filter_test.go | ~120 | in-package (package casbin); table drivers call unexported helpers (testEnforce, testEnforceWithoutUsers, testDomainEnforce) that require-assert inside; nearly every constructor call loads examples/*.conf + examples/*.csv fixture pairs | the helpers are mechanically inlinable, but each test binds to fixture files whose content (keymatch/rbac/abac model zoo) is part of the assertion; porting means re-authoring both fixture and assertion, which is generation, not rewrite | discard; behavior families (model parsing, matcher functions, effect folds, RBAC/domain queries, management calls) recovered in Track B from string-built models |
| enforcer_cached*_test.go, enforcer_synced*_test.go, enforcer_distributed / transaction*_test.go, watcher*_test.go, frontend*_test.go, enforcer_context_test.go, logger_test.go | ~70 | in-package; exercise cached/synced/distributed/transactional/watcher/frontend surfaces | out of scope by Non-Goals | discard |
| biba_test.go, blp_test.go, lbac_test.go, orbac_test.go, pbac_test.go, syntax_test.go, constraint_test.go, error_test.go, benchmark files | ~43 | in-package; exotic model-zoo fixtures and white-box error paths | mostly out-of-scope model families; in-scope intents (deny-override, priority) recovered in Track B | discard |

Summary: 0 of 233 upstream test functions liftable -> Track B early trigger
(100% of files discarded after rewrite assessment, > 50% threshold).

functions_in_scope: 233 (upstream Test funcs; all excluded above)
functions_kept: 0 (Track A)
functions_excluded: 233
Track B output: see spec_test_map.md.

Coverage-guided generation notes (S3B): generation targets were enumerated
from the spec section list (Model Definition, Request Enforcement, Matcher
Language, Role Inheritance, Policy Management, Persistence; every Error
Semantics row; all 7 CVIs; both Representative Workflows). Expected values
were observed by executing the pinned reference v3.11.0 (5 probe rounds under
wip/casbin-policy-enforcement-fullrepro-001/probe); no reference source files
were used as assertion material. All oracle tests build models from strings
(model.NewModelFromString / string-adapter / temp files written by the test);
no upstream fixture is shipped.
