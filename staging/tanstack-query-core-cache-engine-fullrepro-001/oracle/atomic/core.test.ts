// Oracle - atomic tests for the query-core asynchronous state-management specification.
import { afterEach, describe, expect, test } from "vitest";
import {
  QueryClient,
  QueryCache,
  MutationCache,
  QueryObserver,
  InfiniteQueryObserver,
  MutationObserver,
  Query,
  Mutation,
  dehydrate,
  hydrate,
  defaultShouldDehydrateQuery,
  hashKey,
  matchQuery,
  partialMatchKey,
  replaceEqualDeep,
  keepPreviousData,
  skipToken,
  CancelledError,
  isCancelledError,
  notifyManager,
  focusManager,
  onlineManager,
} from "@tanstack/query-core";

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

async function waitUntil(pred: () => boolean, ms = 3000): Promise<void> {
  const start = Date.now();
  while (!pred()) {
    if (Date.now() - start > ms) throw new Error("timed out waiting for condition");
    await sleep(5);
  }
}

const liveClients: QueryClient[] = [];

function makeClient(config?: ConstructorParameters<typeof QueryClient>[0]): QueryClient {
  const client = new QueryClient(config);
  client.mount();
  liveClients.push(client);
  return client;
}

afterEach(() => {
  for (const client of liveClients.splice(0)) {
    try {
      client.clear();
      client.unmount();
    } catch {
      // best-effort cleanup
    }
  }
});

// ---------------------------------------------------------------------------
describe("client and cache fundamentals", () => {
  test("a client exposes the caches it was constructed with", () => {
    /** Verifies: QC-CLI-001, QC-CLI-002 */
    const queryCache = new QueryCache();
    const mutationCache = new MutationCache();
    const client = makeClient({ queryCache, mutationCache });
    expect(client.getQueryCache()).toBe(queryCache);
    expect(client.getMutationCache()).toBe(mutationCache);
    const plain = makeClient();
    expect(plain.getQueryCache()).toBeInstanceOf(QueryCache);
    expect(plain.getMutationCache()).toBeInstanceOf(MutationCache);
  });

  test("defaultOptions.queries are merged into every fetch", async () => {
    /** Verifies: QC-CLI-001 */
    const client = makeClient({ defaultOptions: { queries: { staleTime: 60_000 } } });
    let calls = 0;
    await client.fetchQuery({
      queryKey: ["cfg"],
      queryFn: async () => {
        calls += 1;
        return "first";
      },
    });
    const again = await client.fetchQuery({
      queryKey: ["cfg"],
      queryFn: async () => {
        calls += 1;
        return "second";
      },
    });
    expect(again).toBe("first");
    expect(calls).toBe(1);
  });

  test("clear empties both caches", async () => {
    /** Verifies: QC-CLI-003 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["c", 1], queryFn: async () => 7 });
    const mo = new MutationObserver(client, { mutationFn: async () => "done" });
    await mo.mutate(undefined);
    expect(client.getQueryCache().findAll().length).toBe(1);
    expect(client.getMutationCache().getAll().length).toBe(1);
    client.clear();
    expect(client.getQueryCache().findAll().length).toBe(0);
    expect(client.getMutationCache().getAll().length).toBe(0);
    expect(client.getQueryData(["c", 1])).toBeUndefined();
  });

  test("hashKey is deterministic and insensitive to property order", () => {
    /** Verifies: QC-CLI-004 */
    expect(typeof hashKey([{ a: 1, b: 2 }])).toBe("string");
    expect(hashKey([{ a: 1, b: 2 }])).toBe(hashKey([{ b: 2, a: 1 }]));
    expect(hashKey(["u", { p: { y: 2, x: 1 }, q: 0 }])).toBe(
      hashKey(["u", { q: 0, p: { x: 1, y: 2 } }]),
    );
    expect(hashKey(["a", 1])).not.toBe(hashKey(["a", 2]));
    expect(hashKey(["a"])).toBe(hashKey(["a"]));
  });

  test("partialMatchKey implements deep-prefix matching", () => {
    /** Verifies: QC-CLI-005 */
    expect(partialMatchKey(["a", "b", { x: 1, y: 2 }], ["a"])).toBe(true);
    expect(partialMatchKey(["a", "b", { x: 1, y: 2 }], ["a", "b", { x: 1 }])).toBe(true);
    expect(partialMatchKey(["a", "b"], ["a", "b"])).toBe(true);
    expect(partialMatchKey(["a"], ["a", "b"])).toBe(false);
    expect(partialMatchKey(["a", "c"], ["a", "b"])).toBe(false);
    expect(partialMatchKey(["a", { x: 1 }], ["a", { x: 2 }])).toBe(false);
  });

  test("a cache entry exposes queryKey, queryHash, and state", () => {
    /** Verifies: QC-CLI-006 */
    const client = makeClient();
    client.setQueryData(["entry", 5], "payload");
    const q = client.getQueryCache().find({ queryKey: ["entry", 5] })!;
    expect(q).toBeInstanceOf(Query);
    expect(q.queryKey).toEqual(["entry", 5]);
    expect(q.queryHash).toBe(hashKey(["entry", 5]));
    expect(q.state.data).toBe("payload");
  });

  test("state fields reflect a successful fetch", async () => {
    /** Verifies: QC-CLI-007, QC-FET-002 */
    const client = makeClient();
    const before = Date.now();
    await client.fetchQuery({ queryKey: ["st"], queryFn: async () => ({ ok: 1 }) });
    const after = Date.now();
    const state = client.getQueryState(["st"])!;
    expect(state.status).toBe("success");
    expect(state.fetchStatus).toBe("idle");
    expect(state.data).toEqual({ ok: 1 });
    expect(state.dataUpdatedAt).toBeGreaterThanOrEqual(before);
    expect(state.dataUpdatedAt).toBeLessThanOrEqual(after);
    expect(state.dataUpdateCount).toBe(1);
    expect(state.fetchFailureCount).toBe(0);
    expect(state.isInvalidated).toBe(false);
  });

  test("setQueryDefaults supplies a queryFn to key-only fetches", async () => {
    /** Verifies: QC-CLI-008 */
    const client = makeClient();
    client.setQueryDefaults(["users"], {
      queryFn: async ({ queryKey }) => `user-${queryKey[1]}`,
    });
    const value = await client.fetchQuery({ queryKey: ["users", 7] });
    expect(value).toBe("user-7");
    expect(typeof client.getQueryDefaults(["users", 7]).queryFn).toBe("function");
  });

  test("setMutationDefaults lets mutate run with only a mutationKey", async () => {
    /** Verifies: QC-CLI-009 */
    const client = makeClient();
    client.setMutationDefaults(["send"], {
      mutationFn: async (payload: unknown) => `sent:${payload}`,
    });
    const observer = new MutationObserver<string, Error, string>(client, {
      mutationKey: ["send"],
    });
    const out = await observer.mutate("hello");
    expect(out).toBe("sent:hello");
    expect(typeof client.getMutationDefaults(["send"]).mutationFn).toBe("function");
  });
});

// ---------------------------------------------------------------------------
describe("fetching and query state", () => {
  test("fetchQuery resolves with the queryFn's value", async () => {
    /** Verifies: QC-FET-001 */
    const client = makeClient();
    const value = await client.fetchQuery({
      queryKey: ["f", 1],
      queryFn: async () => ({ id: 1, name: "ada" }),
    });
    expect(value).toEqual({ id: 1, name: "ada" });
  });

  test("the queryFn context carries client, queryKey, meta, and signal", async () => {
    /** Verifies: QC-FET-001 */
    const client = makeClient();
    let ctx: any;
    await client.fetchQuery({
      queryKey: ["cx", 9],
      queryFn: async (context) => {
        ctx = context;
        return 1;
      },
      meta: { tag: "M" },
    });
    expect(ctx.client).toBe(client);
    expect(ctx.queryKey).toEqual(["cx", 9]);
    expect(ctx.meta).toEqual({ tag: "M" });
    expect(ctx.signal).toBeInstanceOf(AbortSignal);
  });

  test("a failing fetch rejects with the error and records error state", async () => {
    /** Verifies: QC-FET-003, QC-ERR-001 */
    const client = makeClient();
    const boom = new Error("nope");
    await expect(
      client.fetchQuery({
        queryKey: ["bad"],
        queryFn: async () => {
          throw boom;
        },
      }),
    ).rejects.toBe(boom);
    const state = client.getQueryState(["bad"])!;
    expect(state.status).toBe("error");
    expect(state.error).toBe(boom);
  });

  test("cached data within staleTime is served without invoking queryFn", async () => {
    /** Verifies: QC-FET-004 */
    const client = makeClient();
    let calls = 0;
    await client.fetchQuery({
      queryKey: ["fresh"],
      queryFn: async () => {
        calls += 1;
        return "v1";
      },
      staleTime: 60_000,
    });
    const second = await client.fetchQuery({
      queryKey: ["fresh"],
      queryFn: async () => {
        calls += 1;
        return "v2";
      },
      staleTime: 60_000,
    });
    expect(second).toBe("v1");
    expect(calls).toBe(1);
  });

  test("with the default staleTime of zero a repeat fetch refetches", async () => {
    /** Verifies: QC-FET-004 */
    const client = makeClient();
    let calls = 0;
    await client.fetchQuery({
      queryKey: ["zero"],
      queryFn: async () => {
        calls += 1;
        return `v${calls}`;
      },
    });
    const second = await client.fetchQuery({
      queryKey: ["zero"],
      queryFn: async () => {
        calls += 1;
        return `v${calls}`;
      },
    });
    expect(second).toBe("v2");
    expect(calls).toBe(2);
  });

  test("ensureQueryData fetches only when no fresh data exists", async () => {
    /** Verifies: QC-FET-005 */
    const client = makeClient();
    let calls = 0;
    const first = await client.ensureQueryData({
      queryKey: ["ens"],
      queryFn: async () => {
        calls += 1;
        return "first";
      },
      staleTime: 60_000,
    });
    const second = await client.ensureQueryData({
      queryKey: ["ens"],
      queryFn: async () => {
        calls += 1;
        return "second";
      },
      staleTime: 60_000,
    });
    expect(first).toBe("first");
    expect(second).toBe("first");
    expect(calls).toBe(1);
  });

  test("prefetchQuery resolves undefined on success and on failure", async () => {
    /** Verifies: QC-FET-006, QC-ERR-002 */
    const client = makeClient();
    const ok = await client.prefetchQuery({ queryKey: ["pre"], queryFn: async () => "warm" });
    expect(ok).toBeUndefined();
    expect(client.getQueryData(["pre"])).toBe("warm");
    const bad = await client.prefetchQuery({
      queryKey: ["pre-bad"],
      queryFn: async () => {
        throw new Error("x");
      },
    });
    expect(bad).toBeUndefined();
    expect(client.getQueryState(["pre-bad"])!.status).toBe("error");
  });

  test("concurrent fetches for one key share a single queryFn invocation", async () => {
    /** Verifies: QC-FET-007 */
    const client = makeClient();
    let calls = 0;
    const queryFn = async () => {
      calls += 1;
      await sleep(30);
      return "shared";
    };
    const [a, b] = await Promise.all([
      client.fetchQuery({ queryKey: ["dd"], queryFn }),
      client.fetchQuery({ queryKey: ["dd"], queryFn }),
    ]);
    expect(calls).toBe(1);
    expect(a).toBe("shared");
    expect(b).toBe("shared");
  });

  test("retry: 2 makes exactly three attempts and counts the failures", async () => {
    /** Verifies: QC-FET-008, QC-FET-009 */
    const client = makeClient();
    let calls = 0;
    const boom = new Error("still failing");
    await expect(
      client.fetchQuery({
        queryKey: ["rt"],
        queryFn: async () => {
          calls += 1;
          throw boom;
        },
        retry: 2,
        retryDelay: 1,
      }),
    ).rejects.toBe(boom);
    expect(calls).toBe(3);
    expect(client.getQueryState(["rt"])!.fetchFailureCount).toBe(3);
  });

  test("the default retry count in this environment is zero", async () => {
    /** Verifies: QC-FET-008 */
    const client = makeClient();
    let calls = 0;
    await client
      .fetchQuery({
        queryKey: ["dr"],
        queryFn: async () => {
          calls += 1;
          throw new Error("e");
        },
      })
      .catch(() => {});
    expect(calls).toBe(1);
  });

  test("cancelQueries aborts the signal and rejects with CancelledError", async () => {
    /** Verifies: QC-FET-010, QC-ERR-003 */
    const client = makeClient();
    let aborted = false;
    const promise = client.fetchQuery({
      queryKey: ["can"],
      queryFn: ({ signal }) =>
        new Promise<string>((_res, rej) => {
          signal.addEventListener("abort", () => {
            aborted = true;
            rej(new Error("aborted"));
          });
        }),
    });
    promise.catch(() => {});
    await sleep(10);
    await client.cancelQueries({ queryKey: ["can"] });
    let error: unknown;
    try {
      await promise;
    } catch (e) {
      error = e;
    }
    expect(aborted).toBe(true);
    expect(error).toBeInstanceOf(CancelledError);
    expect(isCancelledError(error)).toBe(true);
    const state = client.getQueryState(["can"])!;
    expect(state.status).toBe("pending");
    expect(state.fetchStatus).toBe("idle");
    expect(state.data).toBeUndefined();
  });

  test("an unused entry is collected after its gcTime", async () => {
    /** Verifies: QC-FET-011 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["gc"], queryFn: async () => "kept", gcTime: 50 });
    expect(client.getQueryData(["gc"])).toBe("kept");
    await sleep(250);
    expect(client.getQueryData(["gc"])).toBeUndefined();
    expect(client.getQueryCache().findAll().length).toBe(0);
  });
});

// ---------------------------------------------------------------------------
describe("direct cache reads and writes", () => {
  test("reads distinguish absent keys from present ones", () => {
    /** Verifies: QC-DIR-001, QC-ERR-005 */
    const client = makeClient();
    expect(client.getQueryData(["missing"])).toBeUndefined();
    expect(client.getQueryState(["missing"])).toBeUndefined();
    client.setQueryData(["missing"], "now-present");
    expect(client.getQueryData(["missing"])).toBe("now-present");
    expect(client.getQueryState(["missing"])!.status).toBe("success");
    expect(client.getQueryData(["still-missing"])).toBeUndefined();
  });

  test("setQueryData accepts a plain value or a functional updater", () => {
    /** Verifies: QC-DIR-003 */
    const client = makeClient();
    const w1 = client.setQueryData(["sd"], "v1");
    expect(w1).toBe("v1");
    expect(client.getQueryData(["sd"])).toBe("v1");
    const w2 = client.setQueryData(["sd"], (prev: unknown) => `${prev}!`);
    expect(w2).toBe("v1!");
    expect(client.getQueryData(["sd"])).toBe("v1!");
  });

  test("an updater returning undefined skips the write", () => {
    /** Verifies: QC-DIR-004 */
    const client = makeClient();
    client.setQueryData(["skip"], "keep-me");
    const out = client.setQueryData(["skip"], () => undefined);
    expect(out).toBeUndefined();
    expect(client.getQueryData(["skip"])).toBe("keep-me");
  });

  test("direct writes count as successful data updates", () => {
    /** Verifies: QC-DIR-005 */
    const client = makeClient();
    const before = Date.now();
    client.setQueryData(["dw"], "a");
    client.setQueryData(["dw"], "b");
    const state = client.getQueryState(["dw"])!;
    expect(state.status).toBe("success");
    expect(state.dataUpdateCount).toBe(2);
    expect(state.dataUpdatedAt).toBeGreaterThanOrEqual(before);
  });

  test("getQueriesData returns key/data pairs for every match", () => {
    /** Verifies: QC-DIR-002 */
    const client = makeClient();
    client.setQueryData(["t", 1], "a");
    client.setQueryData(["t", 2], "b");
    client.setQueryData(["u", 1], "c");
    const pairs = client.getQueriesData({ queryKey: ["t"] });
    expect(pairs).toEqual([
      [["t", 1], "a"],
      [["t", 2], "b"],
    ]);
  });

  test("setQueriesData applies one updater to every match", () => {
    /** Verifies: QC-DIR-006 */
    const client = makeClient();
    client.setQueryData(["t", 1], "a");
    client.setQueryData(["t", 2], "b");
    client.setQueryData(["u", 1], "c");
    const written = client.setQueriesData({ queryKey: ["t"] }, (prev: unknown) => `${prev}!`);
    expect(written).toEqual([
      [["t", 1], "a!"],
      [["t", 2], "b!"],
    ]);
    expect(client.getQueryData(["t", 1])).toBe("a!");
    expect(client.getQueryData(["t", 2])).toBe("b!");
    expect(client.getQueryData(["u", 1])).toBe("c");
  });

  test("isFetching counts in-flight fetches and returns to zero", async () => {
    /** Verifies: QC-DIR-007 */
    const client = makeClient();
    expect(client.isFetching()).toBe(0);
    const p = client.fetchQuery({
      queryKey: ["busy"],
      queryFn: async () => {
        await sleep(40);
        return 1;
      },
    });
    await sleep(10);
    expect(client.isFetching()).toBe(1);
    expect(client.isFetching({ queryKey: ["busy"] })).toBe(1);
    await p;
    expect(client.isFetching()).toBe(0);
    expect(client.isMutating()).toBe(0);
  });
});

// ---------------------------------------------------------------------------
describe("query filters and bulk operations", () => {
  test("queryKey filters prefix-match and exact filters hash-match", () => {
    /** Verifies: QC-FLT-001 */
    const client = makeClient();
    client.setQueryData(["t", 1], "a");
    client.setQueryData(["t", 2], "b");
    client.setQueryData(["u", 1], "c");
    const cache = client.getQueryCache();
    expect(cache.findAll({ queryKey: ["t"] }).length).toBe(2);
    expect(cache.findAll({ queryKey: ["t"], exact: true }).length).toBe(0);
    expect(cache.findAll({ queryKey: ["t", 1], exact: true }).length).toBe(1);
  });

  test("type filters split entries by observer activity", async () => {
    /** Verifies: QC-FLT-001 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["live"],
      queryFn: async () => 1,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    client.setQueryData(["cold"], 2);
    const cache = client.getQueryCache();
    const active = cache.findAll({ type: "active" }).map((q) => q.queryKey);
    const inactive = cache.findAll({ type: "inactive" }).map((q) => q.queryKey);
    expect(active).toEqual([["live"]]);
    expect(inactive).toEqual([["cold"]]);
    expect(cache.findAll({ type: "all" }).length).toBe(2);
    unsubscribe();
  });

  test("invalidation marks entries and makes them match stale filters", async () => {
    /** Verifies: QC-FLT-004, QC-FLT-005, QC-FLT-006 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["inv"], queryFn: async () => 1, staleTime: 60_000 });
    expect(client.getQueryCache().findAll({ stale: true }).length).toBe(0);
    await client.invalidateQueries({ queryKey: ["inv"], refetchType: "none" });
    expect(client.getQueryState(["inv"])!.isInvalidated).toBe(true);
    expect(client.getQueryCache().findAll({ stale: true }).length).toBe(1);
    expect(client.getQueryCache().findAll({ stale: false }).length).toBe(0);
  });

  test("fetchStatus filters select by fetching activity", async () => {
    /** Verifies: QC-FLT-001 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["done"], queryFn: async () => 0 });
    const p = client.fetchQuery({
      queryKey: ["flight"],
      queryFn: async () => {
        await sleep(40);
        return 1;
      },
    });
    await sleep(10);
    const cache = client.getQueryCache();
    const fetching = cache.findAll({ fetchStatus: "fetching" }).map((q) => q.queryKey);
    expect(fetching).toEqual([["flight"]]);
    expect(cache.findAll({ fetchStatus: "idle" }).map((q) => q.queryKey)).toEqual([["done"]]);
    await p;
    expect(cache.findAll({ fetchStatus: "fetching" }).length).toBe(0);
  });

  test("predicate filters receive the query object", () => {
    /** Verifies: QC-FLT-001 */
    const client = makeClient();
    client.setQueryData(["n", 1], 10);
    client.setQueryData(["n", 2], 99);
    const big = client
      .getQueryCache()
      .findAll({ predicate: (q) => (q.state.data as number) > 50 });
    expect(big.map((q) => q.queryKey)).toEqual([["n", 2]]);
  });

  test("matchQuery makes the same decision as the cache", () => {
    /** Verifies: QC-FLT-002 */
    const client = makeClient();
    client.setQueryData(["m", 1], "x");
    const q = client.getQueryCache().find({ queryKey: ["m", 1] })!;
    expect(matchQuery({ queryKey: ["m"] }, q)).toBe(true);
    expect(matchQuery({ queryKey: ["m", 1], exact: true }, q)).toBe(true);
    expect(matchQuery({ queryKey: ["other"] }, q)).toBe(false);
    expect(matchQuery({ queryKey: ["m"], exact: true }, q)).toBe(false);
  });

  test("find is exact by default while findAll prefix-matches", () => {
    /** Verifies: QC-FLT-003 */
    const client = makeClient();
    client.setQueryData(["x", 1], 1);
    client.setQueryData(["x", 2], 2);
    const cache = client.getQueryCache();
    expect(cache.find({ queryKey: ["x", 1] })!.queryKey).toEqual(["x", 1]);
    expect(cache.find({ queryKey: ["x"] })).toBeUndefined();
    expect(cache.find({ queryKey: ["x"], exact: false })!.queryKey).toEqual(["x", 1]);
    expect(cache.find({ queryKey: ["nothing"] })).toBeUndefined();
    expect(cache.findAll({ queryKey: ["x"] }).length).toBe(2);
    expect(cache.findAll().length).toBe(2);
    expect(cache.findAll({}).length).toBe(2);
  });

  test("refetchQueries refetches matches regardless of staleness", async () => {
    /** Verifies: QC-FLT-007 */
    const client = makeClient();
    let calls = 0;
    await client.fetchQuery({
      queryKey: ["rf"],
      queryFn: async () => {
        calls += 1;
        return `v${calls}`;
      },
      staleTime: 60_000,
    });
    await client.refetchQueries({ queryKey: ["rf"] });
    expect(calls).toBe(2);
    expect(client.getQueryData(["rf"])).toBe("v2");
  });

  test("removeQueries deletes matching entries outright", () => {
    /** Verifies: QC-FLT-008 */
    const client = makeClient();
    client.setQueryData(["rm", 1], "a");
    client.setQueryData(["keep"], "b");
    client.removeQueries({ queryKey: ["rm"] });
    expect(client.getQueryData(["rm", 1])).toBeUndefined();
    expect(client.getQueryCache().findAll().map((q) => q.queryKey)).toEqual([["keep"]]);
  });

  test("resetQueries returns an inactive entry to its pristine state", async () => {
    /** Verifies: QC-FLT-009 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["rs"], queryFn: async () => 42 });
    await client.resetQueries({ queryKey: ["rs"] });
    const state = client.getQueryState(["rs"])!;
    expect(state.status).toBe("pending");
    expect(state.data).toBeUndefined();
  });

  test("the cache event stream reports added, updated, and removed", async () => {
    /** Verifies: QC-FLT-010 */
    const client = makeClient();
    const events: string[] = [];
    const unsubscribe = client.getQueryCache().subscribe((event) => {
      events.push(event.type);
    });
    await client.fetchQuery({ queryKey: ["ev"], queryFn: async () => "e" });
    expect(events).toEqual(["added", "updated", "updated"]);
    client.setQueryData(["ev"], "e2");
    expect(events).toEqual(["added", "updated", "updated", "updated"]);
    client.removeQueries({ queryKey: ["ev"] });
    expect(events[events.length - 1]).toBe("removed");
    const frozen = events.length;
    unsubscribe();
    client.setQueryData(["ev2"], "silent");
    expect(events.length).toBe(frozen);
  });
});

// ---------------------------------------------------------------------------
describe("query observers", () => {
  test("subscribing triggers a fetch and delivers the success result", async () => {
    /** Verifies: QC-OBS-001, QC-OBS-004 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["obs"],
      queryFn: async () => ({ items: [1, 2] }),
    });
    const seen: Array<{ status: string; fetchStatus: string }> = [];
    const unsubscribe = observer.subscribe((r) => {
      seen.push({ status: r.status, fetchStatus: r.fetchStatus });
    });
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(observer.getCurrentResult().data).toEqual({ items: [1, 2] });
    expect(seen[0]).toEqual({ status: "pending", fetchStatus: "fetching" });
    expect(seen[seen.length - 1]).toEqual({ status: "success", fetchStatus: "idle" });
    unsubscribe();
  });

  test("getCurrentResult reads the latest result synchronously", async () => {
    /** Verifies: QC-OBS-002 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["sync"],
      queryFn: async () => "value",
    });
    const initial = observer.getCurrentResult();
    expect(initial.status).toBe("pending");
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(observer.getCurrentResult().data).toBe("value");
    unsubscribe();
  });

  test("derived booleans agree with the underlying state", async () => {
    /** Verifies: QC-OBS-003 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["flags"],
      queryFn: async () => "f",
      staleTime: 60_000,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    const r = observer.getCurrentResult();
    expect(r.isSuccess).toBe(true);
    expect(r.isPending).toBe(false);
    expect(r.isError).toBe(false);
    expect(r.isFetching).toBe(false);
    expect(r.isFetched).toBe(true);
    expect(r.isStale).toBe(false);
    expect(r.isPlaceholderData).toBe(false);
    unsubscribe();
  });

  test("failure results expose failureCount and failureReason", async () => {
    /** Verifies: QC-FET-009, QC-OBS-003 */
    const client = makeClient();
    const boom = new Error("boom");
    const observer = new QueryObserver(client, {
      queryKey: ["fc"],
      queryFn: async () => {
        throw boom;
      },
      retry: 1,
      retryDelay: 1,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "error");
    const r = observer.getCurrentResult();
    expect(r.isError).toBe(true);
    expect(r.error).toBe(boom);
    expect(r.failureCount).toBe(2);
    expect(r.failureReason).toBe(boom);
    unsubscribe();
  });

  test("select transforms the result while the cache keeps raw data", async () => {
    /** Verifies: QC-OBS-005 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["sel"],
      queryFn: async () => ({ n: 3 }),
      select: (d: { n: number }) => d.n * 10,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(observer.getCurrentResult().data).toBe(30);
    expect(client.getQueryData(["sel"])).toEqual({ n: 3 });
    unsubscribe();
  });

  test("initialData seeds the cache and starts the observer at success", async () => {
    /** Verifies: QC-OBS-006 */
    const client = makeClient();
    let calls = 0;
    const observer = new QueryObserver(client, {
      queryKey: ["init"],
      queryFn: async () => {
        calls += 1;
        return "fetched";
      },
      initialData: "seed",
      staleTime: 60_000,
    });
    const before = observer.getCurrentResult();
    expect(before.status).toBe("success");
    expect(before.data).toBe("seed");
    expect(before.isPlaceholderData).toBe(false);
    const unsubscribe = observer.subscribe(() => {});
    await sleep(30);
    expect(calls).toBe(0);
    expect(client.getQueryData(["init"])).toBe("seed");
    unsubscribe();
  });

  test("placeholderData shows immediately and never enters the cache", async () => {
    /** Verifies: QC-OBS-007 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["ph"],
      queryFn: async () => {
        await sleep(20);
        return "real";
      },
      placeholderData: "placeholder",
    });
    const unsubscribe = observer.subscribe(() => {});
    const first = observer.getCurrentResult();
    expect(first.status).toBe("success");
    expect(first.data).toBe("placeholder");
    expect(first.isPlaceholderData).toBe(true);
    await waitUntil(() => observer.getCurrentResult().isPlaceholderData === false);
    expect(observer.getCurrentResult().data).toBe("real");
    expect(client.getQueryData(["ph"])).toBe("real");
    unsubscribe();
  });

  test("keepPreviousData carries prior data across a key change", async () => {
    /** Verifies: QC-OBS-008 */
    const client = makeClient();
    const optionsFor = (n: number) => ({
      queryKey: ["kp", n],
      queryFn: async ({ queryKey }: any) => {
        await sleep(20);
        return `data-${queryKey[1]}`;
      },
      placeholderData: keepPreviousData,
    });
    const observer = new QueryObserver(client, optionsFor(1));
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().data === "data-1");
    expect(observer.getCurrentResult().isPlaceholderData).toBe(false);
    observer.setOptions(optionsFor(2));
    const mid = observer.getCurrentResult();
    expect(mid.data).toBe("data-1");
    expect(mid.isPlaceholderData).toBe(true);
    expect(mid.status).toBe("success");
    await waitUntil(() => observer.getCurrentResult().data === "data-2");
    expect(observer.getCurrentResult().isPlaceholderData).toBe(false);
    unsubscribe();
  });

  test("enabled: false suppresses fetching while refetch still works", async () => {
    /** Verifies: QC-OBS-009, QC-OBS-002 */
    const client = makeClient();
    let calls = 0;
    const observer = new QueryObserver(client, {
      queryKey: ["en"],
      queryFn: async () => {
        calls += 1;
        return "e";
      },
      enabled: false,
    });
    const unsubscribe = observer.subscribe(() => {});
    await sleep(30);
    const idle = observer.getCurrentResult();
    expect(idle.status).toBe("pending");
    expect(idle.fetchStatus).toBe("idle");
    expect(calls).toBe(0);
    const refetched = await observer.refetch();
    expect(refetched.status).toBe("success");
    expect(refetched.data).toBe("e");
    expect(calls).toBe(1);
    unsubscribe();
  });

  test("a deep-equal refetch keeps the previous data identity", async () => {
    /** Verifies: QC-OBS-010 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["ss"],
      queryFn: async () => ({ list: [{ id: 1 }, { id: 2 }] }),
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    const before = observer.getCurrentResult().data;
    await observer.refetch();
    expect(observer.getCurrentResult().data).toBe(before);
    unsubscribe();
  });

  test("unchanged sub-trees keep their identity through a partial change", async () => {
    /** Verifies: QC-OBS-010 */
    const client = makeClient();
    let version = 0;
    const observer = new QueryObserver(client, {
      queryKey: ["ss2"],
      queryFn: async () => ({ list: [{ id: 1 }, { id: 2 }], meta: { v: version } }),
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    const before: any = observer.getCurrentResult().data;
    version = 1;
    await observer.refetch();
    const after: any = observer.getCurrentResult().data;
    expect(after).not.toBe(before);
    expect(after.list).toBe(before.list);
    expect(after.meta).not.toBe(before.meta);
    expect(after.meta.v).toBe(1);
    unsubscribe();
  });

  test("replaceEqualDeep shares every deep-equal sub-tree", () => {
    /** Verifies: QC-OBS-011 */
    const prev = { a: [1, 2], b: { x: 1 } };
    expect(replaceEqualDeep(prev, { a: [1, 2], b: { x: 1 } })).toBe(prev);
    const out = replaceEqualDeep(prev, { a: [1, 2], b: { x: 2 } });
    expect(out).not.toBe(prev);
    expect(out.a).toBe(prev.a);
    expect(out.b).not.toBe(prev.b);
    expect(out.b.x).toBe(2);
  });

  test("skipToken marks the query unrunnable", async () => {
    /** Verifies: QC-OBS-012 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["sk"],
      queryFn: skipToken,
    });
    const unsubscribe = observer.subscribe(() => {});
    await sleep(30);
    const r = observer.getCurrentResult();
    expect(r.status).toBe("pending");
    expect(r.fetchStatus).toBe("idle");
    expect(r.isPending).toBe(true);
    unsubscribe();
  });

  test("setOptions re-targets the observer to another key", async () => {
    /** Verifies: QC-OBS-002 */
    const client = makeClient();
    const optionsFor = (n: number) => ({
      queryKey: ["tg", n],
      queryFn: async ({ queryKey }: any) => `d${queryKey[1]}`,
    });
    const observer = new QueryObserver(client, optionsFor(1));
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().data === "d1");
    observer.setOptions(optionsFor(2));
    expect(observer.getCurrentResult().status).toBe("pending");
    await waitUntil(() => observer.getCurrentResult().data === "d2");
    expect(observer.getCurrentResult().status).toBe("success");
    unsubscribe();
  });
});

// ---------------------------------------------------------------------------
describe("infinite queries", () => {
  test("fetchInfiniteQuery resolves parallel pages and pageParams arrays", async () => {
    /** Verifies: QC-INF-001 */
    const client = makeClient();
    const seenParams: number[] = [];
    const result = await client.fetchInfiniteQuery({
      queryKey: ["fi"],
      queryFn: async (ctx: any) => {
        seenParams.push(ctx.pageParam);
        return `p${ctx.pageParam}`;
      },
      initialPageParam: 0,
      getNextPageParam: (_last: string, _all: string[], lastParam: number) =>
        lastParam < 2 ? lastParam + 1 : undefined,
    });
    expect(result.pages).toEqual(["p0"]);
    expect(result.pageParams).toEqual([0]);
    expect(seenParams).toEqual([0]);
  });

  test("fetchNextPage appends the next page while one exists", async () => {
    /** Verifies: QC-INF-002, QC-INF-003 */
    const client = makeClient();
    const observer = new InfiniteQueryObserver(client, {
      queryKey: ["inf"],
      queryFn: async (ctx: any) => `p${ctx.pageParam}`,
      initialPageParam: 0,
      getNextPageParam: (_last: any, _all: any, lastParam: number) =>
        lastParam < 2 ? lastParam + 1 : undefined,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(observer.getCurrentResult().hasNextPage).toBe(true);
    await observer.fetchNextPage();
    const data: any = client.getQueryData(["inf"]);
    expect(data.pages).toEqual(["p0", "p1"]);
    expect(data.pageParams).toEqual([0, 1]);
    unsubscribe();
  });

  test("an undefined next param ends paging without growth", async () => {
    /** Verifies: QC-INF-003 */
    const client = makeClient();
    const observer = new InfiniteQueryObserver(client, {
      queryKey: ["cap"],
      queryFn: async (ctx: any) => `p${ctx.pageParam}`,
      initialPageParam: 0,
      getNextPageParam: (_last: any, _all: any, lastParam: number) =>
        lastParam < 1 ? lastParam + 1 : undefined,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    await observer.fetchNextPage();
    expect(observer.getCurrentResult().hasNextPage).toBe(false);
    await observer.fetchNextPage();
    const data: any = client.getQueryData(["cap"]);
    expect(data.pages).toEqual(["p0", "p1"]);
    unsubscribe();
  });

  test("fetchPreviousPage prepends the page and its parameter", async () => {
    /** Verifies: QC-INF-004 */
    const client = makeClient();
    const observer = new InfiniteQueryObserver(client, {
      queryKey: ["back"],
      queryFn: async (ctx: any) => `p${ctx.pageParam}`,
      initialPageParam: 5,
      getNextPageParam: (_last: any, _all: any, lastParam: number) => lastParam + 1,
      getPreviousPageParam: (_first: any, _all: any, firstParam: number) =>
        firstParam > 0 ? firstParam - 1 : undefined,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(observer.getCurrentResult().hasPreviousPage).toBe(true);
    await observer.fetchPreviousPage();
    const data: any = client.getQueryData(["back"]);
    expect(data.pages).toEqual(["p4", "p5"]);
    expect(data.pageParams).toEqual([4, 5]);
    unsubscribe();
  });

  test("maxPages keeps a sliding window with aligned pageParams", async () => {
    /** Verifies: QC-INF-005 */
    const client = makeClient();
    const observer = new InfiniteQueryObserver(client, {
      queryKey: ["win"],
      queryFn: async (ctx: any) => `p${ctx.pageParam}`,
      initialPageParam: 0,
      getNextPageParam: (_last: any, _all: any, lastParam: number) => lastParam + 1,
      getPreviousPageParam: (_first: any, _all: any, firstParam: number) =>
        firstParam > 0 ? firstParam - 1 : undefined,
      maxPages: 2,
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    await observer.fetchNextPage();
    await observer.fetchNextPage();
    let data: any = client.getQueryData(["win"]);
    expect(data.pages).toEqual(["p1", "p2"]);
    expect(data.pageParams).toEqual([1, 2]);
    await observer.fetchPreviousPage();
    data = client.getQueryData(["win"]);
    expect(data.pages).toEqual(["p0", "p1"]);
    expect(data.pageParams).toEqual([0, 1]);
    unsubscribe();
  });
});

// ---------------------------------------------------------------------------
describe("mutations", () => {
  test("a successful mutation runs its lifecycle in order with context", async () => {
    /** Verifies: QC-MUT-001, QC-MUT-002, QC-MUT-004 */
    const client = makeClient();
    const order: string[] = [];
    const observer = new MutationObserver(client, {
      mutationFn: async (v: number) => {
        order.push(`fn:${v}`);
        return v * 2;
      },
      onMutate: (v: number) => {
        order.push(`onMutate:${v}`);
        return { tag: `C${v}` };
      },
      onSuccess: (data: number, v: number, ctx: any) => {
        order.push(`onSuccess:${data}:${v}:${ctx.tag}`);
      },
      onSettled: (data: any, error: any, v: number, ctx: any) => {
        order.push(`onSettled:${data}:${error}:${v}:${ctx.tag}`);
      },
    });
    const out = await observer.mutate(5);
    expect(out).toBe(10);
    expect(order).toEqual([
      "onMutate:5",
      "fn:5",
      "onSuccess:10:5:C5",
      "onSettled:10:null:5:C5",
    ]);
  });

  test("a failing mutation rejects and reports through onError then onSettled", async () => {
    /** Verifies: QC-MUT-003, QC-MUT-004, QC-ERR-004 */
    const client = makeClient();
    const order: string[] = [];
    const boom = new Error("mfail");
    const observer = new MutationObserver(client, {
      mutationFn: async () => {
        order.push("fn");
        throw boom;
      },
      onMutate: () => ({ tag: "T" }),
      onError: (error: any, _v: any, ctx: any) => {
        order.push(`onError:${error.message}:${ctx.tag}`);
      },
      onSettled: (_d: any, error: any, _v: any, ctx: any) => {
        order.push(`onSettled:${error.message}:${ctx.tag}`);
      },
    });
    let caught: unknown;
    try {
      await observer.mutate("x");
    } catch (e) {
      caught = e;
    }
    expect(caught).toBe(boom);
    expect(order).toEqual(["fn", "onError:mfail:T", "onSettled:mfail:T"]);
    expect(observer.getCurrentResult().status).toBe("error");
    expect(observer.getCurrentResult().error).toBe(boom);
  });

  test("getCurrentResult reports the run and reset returns to idle", async () => {
    /** Verifies: QC-MUT-005, QC-MUT-006 */
    const client = makeClient();
    const observer = new MutationObserver(client, {
      mutationFn: async (v: number) => v + 1,
    });
    expect(observer.getCurrentResult().status).toBe("idle");
    await observer.mutate(9);
    const r = observer.getCurrentResult();
    expect(r.status).toBe("success");
    expect(r.data).toBe(10);
    expect(r.variables).toBe(9);
    expect(r.isSuccess).toBe(true);
    expect(r.failureCount).toBe(0);
    observer.reset();
    const after = observer.getCurrentResult();
    expect(after.status).toBe("idle");
    expect(after.data).toBeUndefined();
  });

  test("mutation retry re-invokes the function and counts failures", async () => {
    /** Verifies: QC-MUT-007 */
    const client = makeClient();
    let calls = 0;
    const observer = new MutationObserver(client, {
      mutationFn: async () => {
        calls += 1;
        throw new Error("always");
      },
      retry: 1,
      retryDelay: 1,
    });
    await observer.mutate(undefined).catch(() => {});
    expect(calls).toBe(2);
    const r = observer.getCurrentResult();
    expect(r.failureCount).toBe(2);
    expect(r.status).toBe("error");
  });

  test("the mutation cache records runs and answers find queries", async () => {
    /** Verifies: QC-MUT-008 */
    const client = makeClient();
    const observer = new MutationObserver(client, {
      mutationKey: ["m1"],
      mutationFn: async () => "r1",
    });
    await observer.mutate(undefined);
    const cache = client.getMutationCache();
    expect(cache.getAll().length).toBe(1);
    const found = cache.find({ mutationKey: ["m1"] })!;
    expect(found).toBeInstanceOf(Mutation);
    expect(found.state.status).toBe("success");
    expect(found.state.data).toBe("r1");
    expect(cache.findAll({ mutationKey: ["m1"] }).length).toBe(1);
    expect(cache.findAll({ mutationKey: ["other"] }).length).toBe(0);
  });

  test("isMutating counts running mutations and filters by key", async () => {
    /** Verifies: QC-MUT-008, QC-DIR-007 */
    const client = makeClient();
    const observer = new MutationObserver(client, {
      mutationKey: ["slow"],
      mutationFn: async () => {
        await sleep(40);
        return 1;
      },
    });
    const p = observer.mutate(undefined);
    await sleep(10);
    expect(client.isMutating()).toBe(1);
    expect(client.isMutating({ mutationKey: ["slow"] })).toBe(1);
    expect(client.isMutating({ mutationKey: ["other"] })).toBe(0);
    await p;
    expect(client.isMutating()).toBe(0);
  });
});

// ---------------------------------------------------------------------------
describe("serialization and managers", () => {
  test("dehydrate includes only successful queries by default", async () => {
    /** Verifies: QC-SER-001, QC-SER-002 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["ok"], queryFn: async () => ({ v: 1 }) });
    await client.prefetchQuery({
      queryKey: ["bad"],
      queryFn: async () => {
        throw new Error("x");
      },
    });
    const okQuery = client.getQueryCache().find({ queryKey: ["ok"] })!;
    const badQuery = client.getQueryCache().find({ queryKey: ["bad"] })!;
    expect(defaultShouldDehydrateQuery(okQuery)).toBe(true);
    expect(defaultShouldDehydrateQuery(badQuery)).toBe(false);
    const dehydrated = dehydrate(client);
    expect(Array.isArray(dehydrated.mutations)).toBe(true);
    expect(dehydrated.queries.length).toBe(1);
    const entry: any = dehydrated.queries[0];
    expect(entry.queryKey).toEqual(["ok"]);
    expect(entry.queryHash).toBe(hashKey(["ok"]));
    expect(entry.state.data).toEqual({ v: 1 });
  });

  test("a shouldDehydrateQuery predicate replaces the default", async () => {
    /** Verifies: QC-SER-002 */
    const client = makeClient();
    await client.prefetchQuery({
      queryKey: ["bad"],
      queryFn: async () => {
        throw new Error("x");
      },
    });
    const dehydrated = dehydrate(client, { shouldDehydrateQuery: () => true });
    expect(dehydrated.queries.length).toBe(1);
    expect((dehydrated.queries[0] as any).state.status).toBe("error");
  });

  test("hydrate merges entries preserving data and timestamps", async () => {
    /** Verifies: QC-SER-003 */
    const source = makeClient();
    await source.fetchQuery({ queryKey: ["h", 1], queryFn: async () => ({ v: "x" }) });
    const stamp = source.getQueryState(["h", 1])!.dataUpdatedAt;
    const dehydrated = dehydrate(source);
    await sleep(20);
    const target = makeClient();
    hydrate(target, dehydrated);
    expect(target.getQueryData(["h", 1])).toEqual({ v: "x" });
    expect(target.getQueryState(["h", 1])!.dataUpdatedAt).toBe(stamp);
  });

  test("scheduled callbacks are deferred and run in submission order", async () => {
    /** Verifies: QC-SER-004 */
    const order: string[] = [];
    notifyManager.batch(() => {
      notifyManager.schedule(() => order.push("cb1"));
      notifyManager.schedule(() => order.push("cb2"));
      order.push("end-of-batch-fn");
    });
    order.push("sync-after");
    await waitUntil(() => order.length === 4);
    expect(order).toEqual(["end-of-batch-fn", "sync-after", "cb1", "cb2"]);
  });

  test("focusManager reports and forces the focus flag", () => {
    /** Verifies: QC-SER-005 */
    expect(focusManager.isFocused()).toBe(true);
    focusManager.setFocused(false);
    expect(focusManager.isFocused()).toBe(false);
    focusManager.setFocused(undefined);
    expect(focusManager.isFocused()).toBe(true);
  });

  test("onlineManager reports and sets the online flag", () => {
    /** Verifies: QC-SER-005 */
    expect(onlineManager.isOnline()).toBe(true);
    onlineManager.setOnline(false);
    expect(onlineManager.isOnline()).toBe(false);
    onlineManager.setOnline(true);
    expect(onlineManager.isOnline()).toBe(true);
  });
});
