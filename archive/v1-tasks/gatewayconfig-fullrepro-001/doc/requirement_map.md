# GatewayConfig Requirement Map

## Requirements

| ID | Requirement | Evidence | Test Layers |
|---|---|---|---|
| EG-REQ-001 | Validate and normalize upstream, service, route, plugin config, and global rule resources. | APISIX admin/resource and terminology docs. | unit, integration |
| EG-REQ-002 | Maintain resource versions, normalized digests, tombstones, and audit entries. | Admin resource lifecycle and standalone behavior. | unit, integration, system |
| EG-REQ-003 | Apply public PATCH semantics without losing unrelated fields. | Admin API update/PATCH behavior, benchmark variant. | unit, integration, system |
| EG-REQ-004 | Enforce reference constraints and expose reverse reference reports. | Service/upstream/plugin references, delete behavior. | unit, integration, system |
| EG-REQ-005 | Support force-delete with visible dangling-reference reports. | APISIX delete/reference behavior adapted to public error codes. | integration, system |
| EG-REQ-006 | Load standalone config atomically and increment generation only on effective digest change. | Standalone admin source/tests. | integration, system |
| EG-REQ-007 | Match routes by method, host, path, priority, longest path, and stable route ID tie-break. | Route terminology and runtime routing behavior. | unit, integration, system |
| EG-REQ-008 | Resolve route/service/upstream precedence and deterministic upstream node selection. | Service/upstream route relations. | unit, integration, system |
| EG-REQ-009 | Merge global, service, plugin-config, and route-local plugins in public precedence order. | Plugin config and global rule docs/source. | unit, integration, system |
| EG-REQ-010 | Simulate request routing and plugin execution from the same state exposed by reports. | Runtime/plugin behavior. | integration, system |
| EG-REQ-011 | Produce config, reference, runtime, and audit reports from the same normalized state. | Admin/runtime projection surface. | integration, system |
| EG-REQ-012 | Keep all projections coherent after mixed create, patch, delete, force-delete, reload, and simulate sequences. | Full agreement-surface invariant. | system |

## Unit Layer Rules

Unit checks must be feature-pure. Setup may use constructors, direct resource
fixtures, or mocks. Unit tests must not build state through unrelated public API
operations.

## System Layer Rules

System checks must exercise at least two public projections in each check, such
as Admin API plus runtime simulation, standalone reload plus reports, or delete
operations plus reference/runtime reports.
