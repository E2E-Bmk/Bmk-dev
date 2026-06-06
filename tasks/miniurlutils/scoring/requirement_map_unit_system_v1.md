# MiniURLUtils Unit/System Requirement Map

Date: 2026-06-03

Public packet: `candidate_task_unit_system/public_packet.md`

Rubric: `scoring/rubrics_unit_system_v1.json`

Scorer: `scoring/score_miniurlutils_unit_system.py`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-package-shape` | Importable module names | Overview | `URL`, `QueryParamDict`, `parse_url`, `find_all_links`, and `URLParseError` import from `miniurlutils` |
| `REQ-feature-set` | Bounded 6-module feature set | Feature Set | Parsing, mutable URL state, query params, navigation/normalization, link extraction, and errors |
| `REQ-global-invariants` | Cross-feature URL state invariants | Global Invariants | Missing components, authority/userinfo, query order, normalization, link-derived URL objects, and error recovery stay consistent |
| `REQ-parse` | URL parsing | Parsing | URL text decomposes into scheme, authority, path, query, fragment, userinfo, host, port, and IP family where detectable |
| `REQ-url-object` | Mutable URL object and serialization | URL Object | URL attributes, `path_parts`, `query_params`, `to_text`, `from_parts`, and `get_authority` expose coherent state |
| `REQ-query-params` | Ordered repeated query parameters | QueryParamDict | Repeated keys, bare keys, add, assignment, getlist, items, sorted copies, and serialization work predictably |
| `REQ-navigation` | Navigation and normalization | URL Object | Relative navigation and in-place normalization update path/host/port state and later serialization |
| `REQ-link-extraction` | Plain-text URL extraction | Link Extraction | Extracted links are returned as mutable `URL` objects |
| `REQ-errors` | Error behavior | Parsing, Non-Goals | Malformed URLs raise useful exceptions; later valid operations still work |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit cases exercise one module at a time |
| `REQ-system-eval` | System testing definition | Evaluation Style | System cases cross at least two modules and carry `system_dimension` labels |

## Unit Coverage

| Test | Feature | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `MUU001` | imports | `REQ-package-shape` | Public names import from the module |
| `MUU002` | parse URL | `REQ-parse` | Absolute URL components are exposed in the parse dictionary |
| `MUU003` | URL object | `REQ-url-object`, `REQ-query-params` | URL attributes, query params, serialization, and authority work on a simple URL |
| `MUU004` | query params | `REQ-query-params` | Repeated and bare query params parse and serialize in order |
| `MUU005` | query params | `REQ-query-params` | `add`, assignment, and `getlist` expose multi-value behavior |
| `MUU006` | navigation | `REQ-navigation`, `REQ-url-object` | Relative navigation resolves from a base URL |
| `MUU007` | normalization | `REQ-navigation` | Normalize lowercases scheme/host, removes default port, and resolves dot segments |
| `MUU008` | link extraction | `REQ-link-extraction`, `REQ-url-object` | HTTP(S) links extract as serializable URLs |
| `MUU009` | errors | `REQ-errors` | Malformed URLs raise exceptions |

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `MUS001` | `global_invariant` | parse -> URL object -> authority -> serialization | `REQ-parse`, `REQ-url-object`, `REQ-global-invariants` | Userinfo is preserved in full serialization while host authority remains distinct |
| `MUS002` | `boundary_crossing` | parse variants -> URL navigation | `REQ-parse`, `REQ-url-object`, `REQ-navigation` | Scheme-relative and path-only inputs preserve absent component semantics through later navigation |
| `MUS003` | `operation_order_sensitivity` | query append -> query replace -> URL serialization | `REQ-query-params`, `REQ-url-object` | Query mutation order is visible in final serialized state |
| `MUS004` | `cross_feature_dataflow` | from_parts -> query params -> navigation | `REQ-url-object`, `REQ-query-params`, `REQ-navigation` | Constructed URL state becomes a valid navigation base |
| `MUS005` | `state_accumulation` | normalize -> query edit -> navigate | `REQ-url-object`, `REQ-query-params`, `REQ-navigation` | Mutations accumulate before later relative navigation |
| `MUS006` | `cross_feature_dataflow` | link extraction -> URL mutation -> serialization | `REQ-link-extraction`, `REQ-query-params`, `REQ-url-object` | Extracted links behave like directly constructed mutable URL objects |
| `MUS007` | `boundary_crossing` | IPv6 parse -> URL authority -> normalize | `REQ-parse`, `REQ-url-object`, `REQ-navigation` | IPv6 host/family, authority formatting, default port removal, and normalized path agree |
| `MUS008` | `error_atomicity` | failed parse -> later URL/query operations | `REQ-errors`, `REQ-url-object`, `REQ-query-params` | A malformed input does not poison later valid stateful operations |
| `MUS009` | `global_invariant` | URL query -> sorted copy -> serialization | `REQ-query-params`, `REQ-url-object`, `REQ-global-invariants` | Sorting a query copy does not mutate the original URL's query order |
| `MUS010` | `operation_order_sensitivity` | normalize -> relative navigation | `REQ-url-object`, `REQ-navigation` | Normalized base path controls later relative resolution |

System dimension coverage:

- `cross_feature_dataflow`: `MUS004`, `MUS006`
- `state_accumulation`: `MUS005`
- `global_invariant`: `MUS001`, `MUS009`
- `error_atomicity`: `MUS008`
- `operation_order_sensitivity`: `MUS003`, `MUS010`
- `boundary_crossing`: `MUS002`, `MUS007`

## Reference And Model Verification

| Solution | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `score_report_reference_unit_system_v1.json` |
| Codex subagent | 100.00% | 70.00% | 30.00pp | `score_report_codex_subagent_001_unit_system_v1.json` |
| OpenHands + DeepSeek V4 Pro | 100.00% | 60.00% | 40.00pp | `score_report_openhands_deepseek_v4_pro_001_unit_system_v1.json` |

## Fairness Notes

- `MUS004` was audited to follow standard relative-URL semantics: navigating from `/api/v1` with `../v2/users` resolves to `/v2/users`, because `v1` is treated as the last path segment.
- The scorer avoids treating percent-encoding display preferences for spaces and slashes as hidden requirements.
- Remaining failures are product-level state/invariant issues: authority/userinfo separation, absent-component representation, IPv6 family detection, and query replacement order.
