# GatewayConfig Source Evidence

Source repository: `apache/apisix`

Local clone: `.repo_cache/apache__apisix`

Commit: `496cb68c47db836b3cdecda0281dfb94de11b27f`

## Evidence Used

- Admin API lifecycle: `docs/en/latest/admin-api.md`
- Route semantics: `docs/en/latest/terminology/route.md`
- Service semantics: `docs/en/latest/terminology/service.md`
- Upstream semantics: `docs/en/latest/terminology/upstream.md`
- Plugin config semantics: `docs/en/latest/terminology/plugin-config.md`
- Global rule semantics: `docs/en/latest/terminology/global-rule.md`
- Generic admin resource behavior: `apisix/admin/resource.lua`
- Route/service/upstream admin resources: `apisix/admin/routes.lua`,
  `apisix/admin/services.lua`, `apisix/admin/upstreams.lua`
- Standalone config behavior: `apisix/admin/standalone.lua`,
  `t/admin/standalone.spec.ts`
- Runtime/plugin behavior: `apisix/plugin.lua`, `apisix/init.lua`

## Benchmark-Owned Variants

The benchmark intentionally changes the public surface:

- product name is `edgegate`, not APISIX;
- implementation language is Python;
- runtime is an in-process simulator, not Nginx/OpenResty;
- public errors use stable error codes, not APISIX exact messages;
- resource storage is benchmark-defined, not APISIX etcd key layout;
- plugin set is small and deterministic.

These variants preserve the agreement surface while reducing memorization and
private-shape risk.
