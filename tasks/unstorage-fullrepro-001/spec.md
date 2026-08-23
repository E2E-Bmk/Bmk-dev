
# Unstorage Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`unstorage` is an async key-value storage toolkit that normalizes keys, mounts
drivers, and exposes the same state through direct storage access, namespaced
views, snapshot helpers, tracing, and an HTTP handler. A caller can start with a
memory-backed store and then move the same data through filesystem, browser,
database, cloud, or remote HTTP drivers without changing the public storage API.

The package treats storage as a local graph of mounted backends. Keys normalize
to colon-separated paths, metadata travels with stored values, and helpers such
as `prefixStorage`, `snapshot`, and `withTracing` project the same state through
different public views instead of creating separate stores.

## Non-Goals

- This specification does not require network access, hosted services, or a
  particular backend provider.
- This specification does not define private modules, internal helpers,
  generated files, or build tooling.
- This specification does not define exact error text, trace payload formatting,
  color output, or other presentation-only details.
- This specification does not require a specific persistence layer beyond the
  documented driver contract and JSON-compatible storage rules.
- This specification does not define backend-specific option validation beyond
  the public driver metadata and documented helper behavior.

## Representative Workflows

### Store Data Through A Mounted Driver

```ts
import { createStorage, snapshot, restoreSnapshot, prefixStorage } from "unstorage";
import fsDriver from "unstorage/drivers/fs";

const storage = createStorage({
  driver: fsDriver({ base: "./data" }),
});

const users = prefixStorage(storage, "users");

await users.setItem("1", { name: "Ada" });
const user = await storage.getItem("users:1");
const data = await snapshot(storage, "users");

await restoreSnapshot(storage, data, "backup");
```

The storage instance writes through the mounted driver, the namespace view
removes the shared prefix from its own callers, and the snapshot helpers move
the same logical keys into plain objects and back again.

### Serve Storage Over HTTP

```ts
import { createStorage } from "unstorage";
import { createStorageHandler } from "unstorage/server";
import httpDriver from "unstorage/drivers/http";

const storage = createStorage({
  driver: httpDriver({ base: "http://localhost:3000" }),
});

const fetch = createStorageHandler(storage, {
  authorize({ request, key, type }) {
    const token = request.headers.get("authorization");
    if (token !== "Bearer secret") {
      throw new Error(`Unauthorized ${type} for ${key}`);
    }
  },
});
```

The same storage graph can be exposed through a Fetch-compatible handler and
consumed by the HTTP driver. Path normalization, raw-value handling, and
authorization all follow the same public rules as the in-process storage API.

### Trace Storage Operations

```ts
import { createStorage } from "unstorage";
import { withTracing } from "unstorage/tracing";

const storage = withTracing(createStorage());
await storage.setItem("logs:1", "ready");
```

The tracing wrapper keeps the storage API intact while projecting operation
metadata through Node diagnostics channels when they are available.

## Storage Graph And Mounts

The core storage graph is a mounted key-value tree with one default backend and
zero or more named mounts.

**Construction and defaults.**

- `createStorage` must return a storage instance whose default mount uses the
  in-memory driver when no driver is supplied.
- `createStorage` must accept an optional root driver and use that driver as the
  default mount.
- A storage instance must expose its mounted drivers through `getMount` and
  `getMounts`, and the most specific matching mount must serve each normalized
  key.
- `mount` must accept a base path and a driver, must register the driver under
  the normalized base, and must return the same storage instance.
- Mounting an already occupied base must raise an `Error`.
- `unmount` must remove a mounted driver and must optionally dispose that driver
  when the caller requests disposal.

**Item operations.**

- `hasItem`, `getItem`, `setItem`, `removeItem`, `getItemRaw`, and
  `setItemRaw`, together with the aliases `has`, `get`, `set`, `del`, and
  `remove`, must normalize keys before dispatching to the mounted driver.
- `getItem` must return a deserialized value or `null` when the key is absent.
- `setItem` must serialize JSON-compatible values before writing them, and
  passing `undefined` must remove the key instead of storing it.
- `getItemRaw` and `setItemRaw` must use native raw operations when the driver
  provides them and must fall back to serialized storage when it does not.
- `removeItem` must support the legacy boolean form that controls metadata
  removal and must remove the metadata record when metadata removal is requested.

**Batching and metadata.**

- `getItems` must read several keys and return one key/value record per request.
- `setItems` must write several values and must resolve only after all writes
  complete.
- Batch operations must group work by mount and must use the driver's batch
  methods when they exist.
- `getMeta` must merge native driver metadata with custom metadata stored under
  the matching metadata key.
- `setMeta` and `removeMeta` must project the same metadata record that
  `getMeta` reads.
- `clear` must clear every matching mount and must fall back to per-key removal
  when a driver does not implement `clear`.
- `dispose` must call each mounted driver's `dispose` method when it exists.

**Watching.**

- `watch` must register a storage change callback and must return a cleanup
  function.
- When a driver does not implement native watch support, the storage layer must
  synthesize `update` and `remove` events for individual writes and removals.
- `unwatch` must remove every registered listener and must stop any active
  driver watchers.

## Key Views And Snapshots

The key helpers turn the same storage graph into namespace views and plain
snapshot objects.

**Normalized keys.**

- `normalizeKey` must collapse `/`, `\`, repeated separators, and surrounding
  separators into colon notation and must discard the query string portion of a
  key.
- `joinKeys` must join several segments into a normalized colon-separated key.
- `normalizeBaseKey` must return the normalized base key with a trailing colon,
  or an empty string when the input is empty.
- `filterKeyByDepth` must accept keys whose separator count is within the
  requested depth.
- `filterKeyByBase` must accept keys under the requested base and must exclude
  metadata suffixes.

**Namespace views and snapshots.**

- `prefixStorage` must return a namespace view that prefixes every key-based
  operation with the normalized base and strips that base back out of returned
  keys and watch callbacks.
- A prefixed storage view must share the same underlying mounts, lifecycle
  methods, and alias methods as the original storage instance.
- `snapshot` must read all keys under a normalized base into a plain object
  whose keys are the suffixes below that base.
- `restoreSnapshot` must write each snapshot entry under the requested base and
  must preserve the stored values.

**Key listing.**

- `getKeys` must return normalized keys and must exclude metadata keys.
- `getKeys` must honor `maxDepth` even when the active driver cannot enforce the
  depth limit itself.
- `getMounts` must return the mounted drivers for the requested base and must
  include parent mounts only when the caller asks for them.

## Driver Contract And Built-Ins

Drivers define the storage backend contract, and the package exposes a built-in
catalog for common backends.

**Driver contract.**

- A driver must implement `hasItem`, `getItem`, and `getKeys`.
- `setItem`, `removeItem`, `clear`, `getMeta`, `watch`, `dispose`,
  `getItemRaw`, `setItemRaw`, `getItems`, and `setItems` are optional driver
  capabilities.
- Driver methods must work with mount-relative normalized keys.
- A driver that supports lazy third-party imports must publish dependency
  metadata through `DRIVER_DEPENDENCIES` and must accept a dependency override
  option such as `lib` when the backend uses one.

**Built-in metadata.**

- `builtinDrivers` must map each built-in driver name to its module specifier.
- `builtinDriverDependencies` must map built-in driver names to the dependency
  metadata required by that driver.
- The `unstorage/drivers/*` entry points must expose default-export driver
  factories, and the drivers that depend on additional packages must expose the
  same dependency metadata through their module exports.

## Tracing And HTTP Serving

The tracing and server projections expose the same storage graph through
diagnostics and Fetch-compatible HTTP behavior.

**Tracing.**

- `withTracing` must wrap a storage instance without changing the storage API.
- When diagnostics channels are unavailable, `withTracing` must return the
  original storage unchanged.
- Traced operations must include the normalized keys for the operation and the
  mount and driver information when that context is available.

**HTTP serving.**

- `createStorageHandler` must return a Fetch-compatible handler.
- The handler must support `HEAD`, `GET`, `PUT`, and `DELETE`.
- `GET` on a key must return the stored value, while `GET` on a base path must
  return the listed keys for that base.
- `PUT` must store the request body, and `DELETE` must remove a key or clear a
  base path when the request targets a base.
- Requests that declare `application/octet-stream` must use the raw-value
  methods.
- `authorize` must run before each supported operation and must receive the
  request, normalized key, and read/write operation type.
- A non-HTTP authorization failure must become a `401` response, while an
  `HTTPError` must pass through unchanged.
- `resolvePath` must override how the request path is converted into a storage
  key.

## State Model

The core state is a mounted key-value graph with normalized keys, value
serialization rules, metadata records, watch registrations, tracing context, and
Fetch handler projections.

The public projections of this state are:

1. `Storage` instances and their aliases for direct reads, writes, metadata,
   mount inspection, and lifecycle control.
2. `prefixStorage` namespace views that project the same graph through a base
   prefix.
3. `snapshot` and `restoreSnapshot` projections that move the same logical
   values through plain objects.
4. `withTracing` projections that emit diagnostics-channel context for storage
   operations.
5. `createStorageHandler` projections that expose the same graph through a
   Fetch-compatible HTTP surface.
6. `builtinDrivers` and `builtinDriverDependencies` projections that describe
   the built-in driver catalog.

## Error Semantics

| Condition | Required result |
|---|---|
| A mount base is already occupied | `mount` must raise `Error`. |
| A storage value cannot be serialized by the JSON rules | `setItem` and `setItems` must raise `Error`. |
| A request method is not one of `HEAD`, `GET`, `PUT`, or `DELETE` | `createStorageHandler` must raise an HTTP 405 error. |
| A non-HTTP authorization check fails | `createStorageHandler` must return a 401 response that preserves the failure cause when possible. |
| A requested key is absent | `getItem` must return `null`; HTTP `GET` and `HEAD` must report absence through their normal empty or missing-item responses. |
| A driver lacks a requested optional capability | the storage layer must use its documented fallback instead of failing solely for that omission. |
| Diagnostics channels are unavailable | `withTracing` must return the original storage without error. |

## Cross-View Invariants

1. `normalizeKey`, `createStorage`, `prefixStorage`, `snapshot`, `restoreSnapshot`,
   `withTracing`, and `createStorageHandler` must agree on the normalized key
   form for the same logical path.
2. A key written through a namespace view must be readable through the original
   storage instance at the corresponding normalized key.
3. A snapshot written back with `restoreSnapshot` must recreate the same logical
   values that `snapshot` read from the storage graph.
4. A mount reported by `getMount` or `getMounts` must be the same driver that
   receives the underlying storage operation and appears in tracing context.
5. A driver that lacks native watch support must still produce storage-level
   change notifications for individual writes and removals.
6. The HTTP handler and the in-process storage API must interpret base paths and
   raw values through the same normalization rules.
7. `builtinDrivers` and `builtinDriverDependencies` must describe the same
   built-in driver catalog that the module entry points expose.
8. `getKeys` and `filterKeyByDepth` must agree on which keys are visible at a
   given depth.

## Public Interface

There is no standalone console script; callers use the module entry points
directly.

### Import Surface

```ts
import {
  createStorage,
  snapshot,
  restoreSnapshot,
  prefixStorage,
  normalizeKey,
  normalizeBaseKey,
  joinKeys,
  filterKeyByDepth,
  filterKeyByBase,
  builtinDrivers,
  builtinDriverDependencies,
} from "unstorage";
import type {
  Storage,
  Driver,
  StorageMeta,
  StorageValue,
  WatchCallback,
  Unwatch,
  TransactionOptions,
  GetKeysOptions,
  DriverFlags,
  DriverDependency,
  DriverDependencies,
  CreateStorageOptions,
  Snapshot,
  BuiltinDriverName,
  BuiltinDriverOptions,
} from "unstorage";
import { withTracing } from "unstorage/tracing";
import type { TraceContext, TracedOperation } from "unstorage/tracing";
import { createStorageHandler } from "unstorage/server";
import type {
  StorageServerRequest,
  StorageServerOptions,
  FetchHandler,
} from "unstorage/server";
import cacheBindingDriver from "unstorage/drivers/cloudflare-cache-binding";
import kvBindingDriver from "unstorage/drivers/cloudflare-kv-binding";
import r2BindingDriver from "unstorage/drivers/cloudflare-r2-binding";
import db0Driver from "unstorage/drivers/db0";
import memoryDriver from "unstorage/drivers/memory";
import fsDriver from "unstorage/drivers/fs";
import fsLiteDriver from "unstorage/drivers/fs-lite";
import httpDriver from "unstorage/drivers/http";
import indexedDbDriver from "unstorage/drivers/indexedb";
import localStorageDriver from "unstorage/drivers/localstorage";
import mongodbDriver from "unstorage/drivers/mongodb";
import s3Driver from "unstorage/drivers/s3";
import sessionStorageDriver from "unstorage/drivers/session-storage";
import vercelRuntimeCacheDriver from "unstorage/drivers/vercel-runtime-cache";
```

The root entry point exposes the storage constructor, snapshot helpers, key
utilities, and built-in driver maps. The dedicated tracing and server entry
points expose their own named helpers, and each `unstorage/drivers/*` module
exposes a default driver factory with any driver-specific metadata that the
backend publishes.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| createStorage | function | Creates a mounted storage graph. |
| snapshot | function | Reads a base into a plain snapshot object. |
| restoreSnapshot | function | Writes a snapshot back into storage. |
| prefixStorage | function | Creates a namespaced storage view. |
| normalizeKey | function | Converts a path to normalized colon notation. |
| normalizeBaseKey | function | Converts a base path to a normalized mount prefix. |
| joinKeys | function | Joins several path segments into one normalized key. |
| filterKeyByDepth | function | Filters keys by separator depth. |
| filterKeyByBase | function | Filters keys by mount base and metadata suffix. |
| builtinDrivers | constant | Maps built-in driver names to module specifiers. |
| builtinDriverDependencies | constant | Describes built-in driver dependency metadata. |
| withTracing | function | Wraps a storage instance with diagnostics-channel tracing. |
| createStorageHandler | function | Creates a Fetch-compatible HTTP handler for storage. |
| Storage | interface | Describes the public storage graph projection. |
| Driver | interface | Describes the driver contract. |
| StorageMeta | interface | Describes stored metadata fields. |
| StorageValue | type | Describes JSON-compatible stored values. |
| WatchCallback | type | Describes storage watch callbacks. |
| Unwatch | type | Describes the unwatch cleanup function. |
| TransactionOptions | type | Describes per-operation storage options. |
| GetKeysOptions | type | Describes key-listing options. |
| DriverFlags | interface | Describes driver capability flags. |
| DriverDependency | interface | Describes one lazy dependency declaration. |
| DriverDependencies | type | Describes the dependency map for a driver. |
| CreateStorageOptions | interface | Describes root storage construction options. |
| Snapshot | type | Describes a snapshot object. |
| BuiltinDriverName | type | Describes supported built-in driver names. |
| BuiltinDriverOptions | type | Describes built-in driver option maps. |
| TraceContext | interface | Describes trace metadata for an operation. |
| TracedOperation | type | Describes the traceable storage operations. |
| StorageServerRequest | type | Describes the request projection passed to authorization. |
| StorageServerOptions | interface | Describes server handler options. |
| FetchHandler | type | Describes the Fetch-compatible handler signature. |

## Appendix A: Environment

The working environment runs Node.js 22 on Linux with pnpm available and without
network access during behavioral checks. The assessment environment provides
TypeScript, Vitest, h3, ofetch, srvx, jsdom, fake-indexeddb, ioredis-mock,
mongodb-memory-server, azurite, wrangler, db0, and the other backend libraries
declared by the selected driver matrix. The project must declare its package
metadata, exports, and runtime dependencies in `package.json` so each public
module entry point can be installed locally.

## Appendix B: Assessment Notes

Assessment checks cover key normalization, mounted storage behavior, namespace
views, snapshot round-tripping, metadata projection, batch operations, watch
events, driver dependency metadata, tracing context, HTTP handler behavior, raw
value handling, and the documented type projections. The checks compare
observable state and returned values; they do not require private module layout,
exact error text, fixture shapes, or external services.
