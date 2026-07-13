# EdgeGate Config Runtime PRD

Task id: `gatewayconfig-fullrepro-001`

## Product

Build `edgegate`, a local gateway configuration runtime. EdgeGate does not proxy
real network traffic. It stores gateway resources, validates them, applies
patches and standalone config reloads, and simulates request routing through
routes, services, upstreams, global plugins, plugin configs, and route-local
plugins.

The product is inspired by Apache APISIX resource lifecycles, but the public API,
resource names, error categories, and runtime simulator are benchmark-owned.
Do not clone APISIX, Nginx, Lua internals, etcd key names, or exact error text.

## Non-Goals

- No real HTTP server or reverse proxy.
- No TLS, certificates, auth, DNS, or service discovery.
- No arbitrary scripting plugin system.
- No APISIX-compatible Admin API.
- No dependence on wall-clock time; tests use supplied timestamps.

## Package Shape

Implement an installable Python package named `edgegate` with at least these
logical modules:

- `models`: public dataclasses/enums and resource IDs.
- `schemas`: validation and normalization for public resource dictionaries.
- `store`: durable resource store with versions, digests, tombstones, and audit.
- `patches`: public JSON-like merge patch semantics.
- `references`: service/upstream/plugin-config/global-rule reference graph.
- `standalone`: load/reload/export deterministic standalone config documents.
- `matcher`: route priority and method/host/path predicate matching.
- `balancer`: upstream node selection using deterministic weighted round robin.
- `plugins`: plugin config merge and execution-plan projection.
- `runtime`: in-process request simulation.
- `admin`: importable API facade.
- `cli`: command entrypoints for apply/get/simulate/report.
- `reports`: public consistency, audit, and runtime projection reports.

The starter skeleton may define these names, but behavior must be implemented by
the candidate.

## Resources

All resources have string IDs, integer versions, a normalized body, an
`updated_at` timestamp supplied by the caller or virtual clock, and a tombstone
flag when deleted.

### Upstream

Fields:

- `id`: string.
- `nodes`: non-empty list of `{id, url, weight}`.
- `timeout_ms`: positive integer, default `5000`.
- `tags`: optional list of strings.

Runtime projection:

- selects enabled nodes by deterministic weighted round robin per upstream ID;
- reports selected node ID and URL.

### Service

Fields:

- `id`: string.
- `upstream_id`: required existing upstream ID.
- `plugins`: optional plugin map.
- `tags`: optional list of strings.

Runtime projection:

- supplies upstream and service-level plugins for routes that reference it.

### PluginConfig

Fields:

- `id`: string.
- `plugins`: non-empty plugin map.

Runtime projection:

- participates in plugin precedence only when a route references it.

### GlobalRule

Fields:

- `id`: string.
- `plugins`: non-empty plugin map.

Runtime projection:

- global plugins execute before service/plugin-config/route plugins.

### Route

Fields:

- `id`: string.
- `methods`: optional list of HTTP methods. Empty or omitted means all methods.
- `hosts`: optional list of exact hosts or `*.suffix` wildcards.
- `paths`: non-empty list of exact paths or prefix patterns ending with `*`.
- `priority`: integer, default `0`.
- `service_id`: optional existing service ID.
- `upstream_id`: optional existing upstream ID.
- `plugin_config_id`: optional existing plugin config ID.
- `plugins`: optional route-local plugin map.

Rules:

- A route must have either `service_id` or `upstream_id`.
- If both are present, route-local `upstream_id` overrides service upstream.
- Higher `priority` wins. Ties break by longest matched path, then lexicographic
  route ID.

## Plugin Semantics

The public plugins are:

- `add_header`: config `{name, value}`.
- `block`: config `{status, reason}`.
- `rewrite_path`: config `{prefix, replacement}`.
- `tag`: config `{name, value}`.

Merge order:

1. global rules in lexicographic ID order;
2. service plugins;
3. route plugin config;
4. route-local plugins.

If the same plugin name appears later, the later config replaces the earlier
config, but the execution plan records both the source that was overridden and
the final source. `block` stops runtime simulation before upstream selection.

## Operations

### `put(kind, id, body, now=None)`

Validates and normalizes the resource. Creates version `1` for new resources and
increments version for body changes. If the normalized body is unchanged, the
version and digest do not change, but the audit log records a `noop_put`.

### `patch(kind, id, patch, now=None)`

Applies public merge-patch rules to the current normalized body and validates the
result. `null` deletes an object field. List fields are replaced, not merged.
PATCH increments the version only when the normalized body changes.

### `delete(kind, id, force=False, now=None)`

Normal delete fails when another live resource references the target. Forced
delete tombstones the target and records dangling references in the consistency
report. Deleted resources are absent from normal `list/get` but visible in
`audit_report(include_deleted=True)`.

### `load_standalone(document, now=None)`

Loads a full config document containing any subset of resource lists. A reload is
atomic: either all resources validate and replace the active config, or no active
resource changes. The standalone generation increments only when the effective
normalized config digest changes. Removed resources become tombstoned.

### `simulate_request(method, host, path, headers=None)`

Returns a deterministic projection:

- matched route ID and route version;
- service/upstream IDs and versions;
- selected upstream node;
- ordered plugin execution plan and final plugin configs;
- rewritten path and response status;
- config generation and digest used for the decision.

### Reports

- `config_report()`: versions, digests, generation, live/tombstoned counts.
- `reference_report()`: forward and reverse references, dangling references.
- `runtime_report()`: route match table, effective upstreams, effective plugins.
- `audit_report(include_deleted=False)`: ordered public audit entries.

## Required Invariants

- Admin API, standalone export, config report, and runtime simulation must use
  the same normalized resource state and generation.
- Reference checks and runtime behavior must agree after create, patch, delete,
  force-delete, and standalone reload.
- PATCH must preserve unrelated fields and update all projections immediately.
- Standalone reload must be atomic and idempotent by normalized digest.
- Route matching, upstream selection, plugin precedence, and reports must agree
  after any operation sequence.
- Forced deletion may create dangling references, but the dangling state must be
  visible in reference and runtime reports.

## Public Errors

Raise `EdgeGateError` with a public `code` string:

- `not_found`
- `already_exists`
- `invalid_resource`
- `invalid_reference`
- `reference_conflict`
- `invalid_patch`
- `standalone_rejected`

Tests assert error codes, not exact message text.

## Candidate Visibility

Candidates see this PRD, a starter skeleton, and public examples. They must not
see hidden scorer rows, reference implementation, score reports, or prior traces.
