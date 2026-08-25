// Oracle - integration tests for the query-core asynchronous state-management specification.
import { afterEach, describe, expect, test } from "vitest";
import {
  QueryClient,
  QueryObserver,
  InfiniteQueryObserver,
  MutationObserver,
  dehydrate,
  hydrate,
  hashKey,
  matchQuery,
  keepPreviousData,
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
describe("cross-projection consistency", () => {
  test("one entry's data agrees across reads, observers, cache queries, and pair listings", async () => {
    /** Verifies: QC-CVI-001 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["agree", 1],
      queryFn: async () => ({ total: 55 }),
    });
    const unsubscribe = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    const viaRead = client.getQueryData(["agree", 1]);
    const viaObserver = observer.getCurrentResult().data;
    const viaFind = client.getQueryCache().find({ queryKey: ["agree", 1] })!.state.data;
    const viaPairs = client.getQueriesData({ queryKey: ["agree"] })[0][1];
    expect(viaRead).toEqual({ total: 55 });
    expect(viaObserver).toBe(viaRead);
    expect(viaFind).toBe(viaRead);
    expect(viaPairs).toBe(viaRead);
    unsubscribe();
  });

  test("hash-equal keys address one entry, one fetch, and one query object", async () => {
    /** Verifies: QC-CVI-002, QC-FET-007 */
    const client = makeClient();
    let calls = 0;
    const queryFn = async () => {
      calls += 1;
      await sleep(30);
      return "one";
    };
    const keyA = [{ a: 1, b: 2 }];
    const keyB = [{ b: 2, a: 1 }];
    expect(hashKey(keyA)).toBe(hashKey(keyB));
    const [ra, rb] = await Promise.all([
      client.fetchQuery({ queryKey: keyA, queryFn }),
      client.fetchQuery({ queryKey: keyB, queryFn }),
    ]);
    expect(calls).toBe(1);
    expect(ra).toBe("one");
    expect(rb).toBe("one");
    const all = client.getQueryCache().findAll();
    expect(all.length).toBe(1);
    expect(client.getQueryData(keyA)).toBe(client.getQueryData(keyB));
  });

  test("invalidateQueries touches exactly the entries matchQuery selects", async () => {
    /** Verifies: QC-CVI-003, QC-FLT-004 */
    const client = makeClient();
    client.setQueryData(["inv", 1], "a");
    client.setQueryData(["inv", 2], "b");
    client.setQueryData(["other"], "c");
    const filters = { queryKey: ["inv"] };
    const expected = client
      .getQueryCache()
      .findAll()
      .filter((q) => matchQuery(filters, q))
      .map((q) => q.queryHash)
      .sort();
    await client.invalidateQueries(filters);
    const invalidated = client
      .getQueryCache()
      .findAll()
      .filter((q) => q.state.isInvalidated)
      .map((q) => q.queryHash)
      .sort();
    expect(invalidated).toEqual(expected);
    expect(invalidated.length).toBe(2);
    expect(client.getQueryState(["other"])!.isInvalidated).toBe(false);
  });

  test("removeQueries with a predicate deletes exactly the matchQuery set", () => {
    /** Verifies: QC-CVI-003, QC-FLT-008 */
    const client = makeClient();
    client.setQueryData(["n", 1], 10);
    client.setQueryData(["n", 2], 99);
    client.setQueryData(["n", 3], 70);
    const filters = { predicate: (q: any) => (q.state.data as number) > 50 };
    const survivors = client
      .getQueryCache()
      .findAll()
      .filter((q) => !matchQuery(filters as any, q))
      .map((q) => q.queryHash)
      .sort();
    client.removeQueries(filters as any);
    const remaining = client
      .getQueryCache()
      .findAll()
      .map((q) => q.queryHash)
      .sort();
    expect(remaining).toEqual(survivors);
    expect(client.getQueryData(["n", 1])).toBe(10);
    expect(client.getQueryData(["n", 2])).toBeUndefined();
    expect(client.getQueryData(["n", 3])).toBeUndefined();
  });

  test("the event stream journals what other projections observe", async () => {
    /** Verifies: QC-CVI-004, QC-FLT-010 */
    const client = makeClient();
    const journal: Array<{ type: string; key: unknown }> = [];
    const stop = client.getQueryCache().subscribe((event) => {
      journal.push({ type: event.type, key: event.query.queryKey });
    });
    await client.fetchQuery({ queryKey: ["j"], queryFn: async () => 1 });
    expect(journal[0]).toEqual({ type: "added", key: ["j"] });
    const updatesAfterFetch = journal.filter((e) => e.type === "updated").length;
    expect(updatesAfterFetch).toBe(2);
    client.setQueryData(["j"], 2);
    expect(journal.filter((e) => e.type === "updated").length).toBe(updatesAfterFetch + 1);
    client.removeQueries({ queryKey: ["j"] });
    expect(journal[journal.length - 1]).toEqual({ type: "removed", key: ["j"] });
    stop();
  });

  test("observer flags track entry state through a fetch lifecycle", async () => {
    /** Verifies: QC-CVI-006 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["lc"],
      queryFn: async () => {
        await sleep(20);
        return "v";
      },
    });
    const transitions: Array<{
      status: string;
      fetchStatus: string;
      isPending: boolean;
      isSuccess: boolean;
      isFetching: boolean;
    }> = [];
    const stop = observer.subscribe((r) => {
      transitions.push({
        status: r.status,
        fetchStatus: r.fetchStatus,
        isPending: r.isPending,
        isSuccess: r.isSuccess,
        isFetching: r.isFetching,
      });
    });
    await waitUntil(() => observer.getCurrentResult().status === "success");
    for (const t of transitions) {
      expect(t.isPending).toBe(t.status === "pending");
      expect(t.isSuccess).toBe(t.status === "success");
      expect(t.isFetching).toBe(t.fetchStatus === "fetching");
    }
    const entry = client.getQueryState(["lc"])!;
    const final = observer.getCurrentResult();
    expect(final.status).toBe(entry.status);
    expect(final.fetchStatus).toBe(entry.fetchStatus);
    expect(final.data).toBe(entry.data);
    stop();
  });

  test("after clear every projection reports emptiness", async () => {
    /** Verifies: QC-CVI-007 */
    const client = makeClient();
    await client.fetchQuery({ queryKey: ["a"], queryFn: async () => 1 });
    const mo = new MutationObserver(client, { mutationFn: async () => 2 });
    await mo.mutate(undefined);
    expect(client.getQueryData(["a"])).toBe(1);
    expect(client.getQueryCache().findAll().length).toBe(1);
    expect(client.getMutationCache().getAll().length).toBe(1);
    expect(dehydrate(client).queries.length).toBe(1);
    client.clear();
    expect(client.getQueryCache().findAll().length).toBe(0);
    expect(client.getQueryData(["a"])).toBeUndefined();
    expect(client.isFetching()).toBe(0);
    expect(client.isMutating()).toBe(0);
    const dehydrated = dehydrate(client);
    expect(dehydrated.queries).toEqual([]);
    expect(dehydrated.mutations).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
describe("observers with bulk operations and direct writes", () => {
  test("invalidateQueries refetches the actively observed entry", async () => {
    /** Verifies: QC-FLT-004 */
    const client = makeClient();
    let calls = 0;
    const observer = new QueryObserver(client, {
      queryKey: ["ref"],
      queryFn: async () => {
        calls += 1;
        return `v${calls}`;
      },
      staleTime: 60_000,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().data === "v1");
    await client.invalidateQueries({ queryKey: ["ref"] });
    expect(calls).toBe(2);
    expect(observer.getCurrentResult().data).toBe("v2");
    expect(client.getQueryState(["ref"])!.isInvalidated).toBe(false);
    stop();
  });

  test("refetchType none marks an observed entry stale without fetching", async () => {
    /** Verifies: QC-FLT-005, QC-FLT-006, QC-FLT-007 */
    const client = makeClient();
    let calls = 0;
    const observer = new QueryObserver(client, {
      queryKey: ["mark"],
      queryFn: async () => {
        calls += 1;
        return `v${calls}`;
      },
      staleTime: 60_000,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().data === "v1");
    await client.invalidateQueries({ queryKey: ["mark"], refetchType: "none" });
    expect(calls).toBe(1);
    expect(observer.getCurrentResult().data).toBe("v1");
    expect(client.getQueryCache().findAll({ stale: true }).map((q) => q.queryKey)).toEqual([
      ["mark"],
    ]);
    await client.refetchQueries({ stale: true });
    expect(calls).toBe(2);
    expect(observer.getCurrentResult().data).toBe("v2");
    stop();
  });

  test("a direct write is pushed to a subscribed observer immediately", async () => {
    /** Verifies: QC-DIR-003, QC-CVI-001 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["push"],
      queryFn: async () => "fetched",
      staleTime: 60_000,
    });
    const seen: unknown[] = [];
    const stop = observer.subscribe((r) => seen.push(r.data));
    await waitUntil(() => observer.getCurrentResult().data === "fetched");
    client.setQueryData(["push"], "written");
    await waitUntil(() => observer.getCurrentResult().data === "written");
    expect(seen).toContain("written");
    expect(client.getQueryData(["push"])).toBe("written");
    stop();
  });

  test("a select observer re-derives its view from raw cache writes", async () => {
    /** Verifies: QC-OBS-005, QC-DIR-003 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["view"],
      queryFn: async () => ({ n: 2 }),
      select: (d: { n: number }) => d.n * 100,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().data === 200);
    client.setQueryData(["view"], { n: 5 });
    await waitUntil(() => observer.getCurrentResult().data === 500);
    expect(client.getQueryData(["view"])).toEqual({ n: 5 });
    stop();
  });

  test("placeholder data is observer-local and absent from cache projections", async () => {
    /** Verifies: QC-OBS-007, QC-CVI-001 */
    const client = makeClient();
    const observer = new QueryObserver(client, {
      queryKey: ["local"],
      queryFn: async () => {
        await sleep(40);
        return "real";
      },
      placeholderData: "ghost",
    });
    const stop = observer.subscribe(() => {});
    const during = observer.getCurrentResult();
    expect(during.data).toBe("ghost");
    expect(during.isPlaceholderData).toBe(true);
    expect(client.getQueryData(["local"])).toBeUndefined();
    expect(client.getQueryCache().find({ queryKey: ["local"] })!.state.data).toBeUndefined();
    await waitUntil(() => observer.getCurrentResult().isPlaceholderData === false);
    expect(client.getQueryData(["local"])).toBe("real");
    expect(observer.getCurrentResult().data).toBe("real");
    stop();
  });

  test("cancelQueries settles an observed fetch back to idle without error", async () => {
    /** Verifies: QC-FET-010 */
    const client = makeClient();
    let aborted = false;
    const observer = new QueryObserver(client, {
      queryKey: ["halt"],
      queryFn: ({ signal }: any) =>
        new Promise<string>((_res, rej) => {
          signal.addEventListener("abort", () => {
            aborted = true;
            rej(new Error("stop"));
          });
        }),
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().fetchStatus === "fetching");
    await client.cancelQueries({ queryKey: ["halt"] });
    await waitUntil(() => observer.getCurrentResult().fetchStatus === "idle");
    const r = observer.getCurrentResult();
    expect(aborted).toBe(true);
    expect(r.status).toBe("pending");
    expect(r.isError).toBe(false);
    expect(client.getQueryState(["halt"])!.fetchStatus).toBe("idle");
    stop();
  });

  test("retry progress is visible through observer failure fields", async () => {
    /** Verifies: QC-FET-008, QC-FET-009 */
    const client = makeClient();
    const boom = new Error("flaky");
    const counts: number[] = [];
    const observer = new QueryObserver(client, {
      queryKey: ["prog"],
      queryFn: async () => {
        throw boom;
      },
      retry: 2,
      retryDelay: 10,
    });
    const stop = observer.subscribe((r) => counts.push(r.failureCount));
    await waitUntil(() => observer.getCurrentResult().status === "error");
    const r = observer.getCurrentResult();
    expect(r.failureCount).toBe(3);
    expect(r.failureReason).toBe(boom);
    expect(counts).toContain(1);
    expect(counts).toContain(2);
    expect(client.getQueryState(["prog"])!.fetchFailureCount).toBe(3);
    stop();
  });

  test("resetQueries reverts and refetches an actively observed entry", async () => {
    /** Verifies: QC-FLT-009 */
    const client = makeClient();
    let calls = 0;
    const observer = new QueryObserver(client, {
      queryKey: ["rst"],
      queryFn: async () => {
        calls += 1;
        return `fresh-${calls}`;
      },
      staleTime: 60_000,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().data === "fresh-1");
    client.setQueryData(["rst"], "edited");
    await waitUntil(() => observer.getCurrentResult().data === "edited");
    await client.resetQueries({ queryKey: ["rst"] });
    await waitUntil(() => observer.getCurrentResult().data === "fresh-2");
    expect(calls).toBe(2);
    stop();
  });

  test("an observer fetch and an imperative fetch share one invocation", async () => {
    /** Verifies: QC-FET-007, QC-CVI-002 */
    const client = makeClient();
    let calls = 0;
    const queryFn = async () => {
      calls += 1;
      await sleep(30);
      return "joint";
    };
    const observer = new QueryObserver(client, { queryKey: ["share"], queryFn });
    const stop = observer.subscribe(() => {});
    const imperative = await client.fetchQuery({ queryKey: ["share"], queryFn });
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(calls).toBe(1);
    expect(imperative).toBe("joint");
    expect(observer.getCurrentResult().data).toBe("joint");
    stop();
  });

  test("a direct write refreshes staleness for later fetches", async () => {
    /** Verifies: QC-FET-004, QC-DIR-005 */
    const client = makeClient();
    let calls = 0;
    await client.fetchQuery({
      queryKey: ["age"],
      queryFn: async () => {
        calls += 1;
        return "fetched";
      },
      staleTime: 60_000,
    });
    client.setQueryData(["age"], "written");
    const value = await client.fetchQuery({
      queryKey: ["age"],
      queryFn: async () => {
        calls += 1;
        return "refetched";
      },
      staleTime: 60_000,
    });
    expect(value).toBe("written");
    expect(calls).toBe(1);
  });

  test("activity counters partition concurrent queries and mutations", async () => {
    /** Verifies: QC-DIR-007, QC-MUT-008 */
    const client = makeClient();
    const qp = client.fetchQuery({
      queryKey: ["q", 1],
      queryFn: async () => {
        await sleep(40);
        return 1;
      },
    });
    const qp2 = client.fetchQuery({
      queryKey: ["r", 1],
      queryFn: async () => {
        await sleep(40);
        return 2;
      },
    });
    const mo = new MutationObserver(client, {
      mutationKey: ["mm"],
      mutationFn: async () => {
        await sleep(40);
        return 3;
      },
    });
    const mp = mo.mutate(undefined);
    await sleep(10);
    expect(client.isFetching()).toBe(2);
    expect(client.isFetching({ queryKey: ["q"] })).toBe(1);
    expect(client.isMutating()).toBe(1);
    await Promise.all([qp, qp2, mp]);
    expect(client.isFetching()).toBe(0);
    expect(client.isMutating()).toBe(0);
  });

  test("per-key defaults drive observers that carry only a key", async () => {
    /** Verifies: QC-CLI-008 */
    const client = makeClient();
    client.setQueryDefaults(["auto"], {
      queryFn: async ({ queryKey }) => `built-${queryKey[1]}`,
    });
    const observer = new QueryObserver(client, { queryKey: ["auto", 3] } as any);
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(observer.getCurrentResult().data).toBe("built-3");
    expect(client.getQueryData(["auto", 3])).toBe("built-3");
    stop();
  });

  test("mutation success handlers can write query state other views observe", async () => {
    /** Verifies: QC-MUT-002, QC-CVI-001 */
    const client = makeClient();
    client.setQueryData(["profile"], { name: "before" });
    const observer = new QueryObserver(client, {
      queryKey: ["profile"],
      queryFn: async () => ({ name: "never" }),
      staleTime: 60_000,
      enabled: false,
    });
    const stop = observer.subscribe(() => {});
    const mutation = new MutationObserver(client, {
      mutationFn: async (name: string) => ({ name }),
      onSuccess: (data: { name: string }) => {
        client.setQueryData(["profile"], data);
      },
    });
    await mutation.mutate("after");
    await waitUntil(
      () => (observer.getCurrentResult().data as any)?.name === "after",
    );
    expect(client.getQueryData(["profile"])).toEqual({ name: "after" });
    expect(client.getQueryCache().find({ queryKey: ["profile"] })!.state.data).toEqual({
      name: "after",
    });
    stop();
  });

  test("the mutation cache indexes concurrent keyed runs", async () => {
    /** Verifies: QC-MUT-008 */
    const client = makeClient();
    const a = new MutationObserver(client, {
      mutationKey: ["job", "a"],
      mutationFn: async () => {
        await sleep(30);
        return "ra";
      },
    });
    const b = new MutationObserver(client, {
      mutationKey: ["job", "b"],
      mutationFn: async () => {
        await sleep(30);
        return "rb";
      },
    });
    const pa = a.mutate(undefined);
    const pb = b.mutate(undefined);
    await sleep(10);
    const cache = client.getMutationCache();
    expect(client.isMutating()).toBe(2);
    expect(cache.findAll({ mutationKey: ["job"] }).length).toBe(2);
    expect(cache.findAll({ mutationKey: ["job", "a"], exact: true }).length).toBe(1);
    await Promise.all([pa, pb]);
    const results = cache
      .findAll({ mutationKey: ["job"] })
      .map((m) => m.state.data)
      .sort();
    expect(results).toEqual(["ra", "rb"]);
  });

  test("maxPages window slides while the cache read stays aligned", async () => {
    /** Verifies: QC-INF-005, QC-CVI-001 */
    const client = makeClient();
    const observer = new InfiniteQueryObserver(client, {
      queryKey: ["slide"],
      queryFn: async (ctx: any) => ({ page: ctx.pageParam }),
      initialPageParam: 0,
      getNextPageParam: (_l: any, _a: any, lastParam: number) => lastParam + 1,
      getPreviousPageParam: (_f: any, _a: any, firstParam: number) =>
        firstParam > 0 ? firstParam - 1 : undefined,
      maxPages: 3,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    await observer.fetchNextPage();
    await observer.fetchNextPage();
    await observer.fetchNextPage();
    const viaCache: any = client.getQueryData(["slide"]);
    const viaObserver: any = observer.getCurrentResult().data;
    expect(viaCache.pages.map((p: any) => p.page)).toEqual([1, 2, 3]);
    expect(viaCache.pageParams).toEqual([1, 2, 3]);
    expect(viaObserver.pages).toEqual(viaCache.pages);
    expect(viaObserver.pageParams).toEqual(viaCache.pageParams);
    stop();
  });
});

// ---------------------------------------------------------------------------
describe("end to end workflows", () => {
  test("a dehydrated cache round-trips into a fresh client with staleness intact", async () => {
    /** Verifies: QC-CVI-005, QC-SER-001, QC-SER-003 */
    const source = makeClient();
    await source.fetchQuery({
      queryKey: ["user", 1],
      queryFn: async () => ({ name: "ada" }),
      staleTime: 60_000,
    });
    await source.fetchQuery({
      queryKey: ["user", 2],
      queryFn: async () => ({ name: "grace" }),
      staleTime: 60_000,
    });
    await source.prefetchQuery({
      queryKey: ["broken"],
      queryFn: async () => {
        throw new Error("x");
      },
    });
    const stamp = source.getQueryState(["user", 1])!.dataUpdatedAt;
    const payload = dehydrate(source);
    expect(payload.queries.length).toBe(2);

    const target = makeClient();
    hydrate(target, payload);
    expect(target.getQueryData(["user", 1])).toEqual({ name: "ada" });
    expect(target.getQueryData(["user", 2])).toEqual({ name: "grace" });
    expect(target.getQueryData(["broken"])).toBeUndefined();
    expect(target.getQueryState(["user", 1])!.dataUpdatedAt).toBe(stamp);
    expect(target.getQueryCache().findAll({ queryKey: ["user"] }).length).toBe(2);
    expect(
      target.getQueryCache().find({ queryKey: ["user", 1] })!.queryHash,
    ).toBe(hashKey(["user", 1]));

    let calls = 0;
    const served = await target.fetchQuery({
      queryKey: ["user", 1],
      queryFn: async () => {
        calls += 1;
        return { name: "other" };
      },
      staleTime: 60_000,
    });
    expect(served).toEqual({ name: "ada" });
    expect(calls).toBe(0);
  });

  test("keepPreviousData bridges a paged browse while both entries stay cached", async () => {
    /** Verifies: QC-OBS-008, QC-CVI-001 */
    const client = makeClient();
    const optionsFor = (page: number) => ({
      queryKey: ["list", page],
      queryFn: async ({ queryKey }: any) => {
        await sleep(25);
        return { page: queryKey[1], rows: [`row-${queryKey[1]}`] };
      },
      placeholderData: keepPreviousData,
    });
    const observer = new QueryObserver(client, optionsFor(1));
    const stop = observer.subscribe(() => {});
    await waitUntil(() => (observer.getCurrentResult().data as any)?.page === 1);
    observer.setOptions(optionsFor(2));
    const bridge = observer.getCurrentResult();
    expect((bridge.data as any).page).toBe(1);
    expect(bridge.isPlaceholderData).toBe(true);
    await waitUntil(() => (observer.getCurrentResult().data as any)?.page === 2);
    expect(observer.getCurrentResult().isPlaceholderData).toBe(false);
    expect((client.getQueryData(["list", 1]) as any).page).toBe(1);
    expect((client.getQueryData(["list", 2]) as any).page).toBe(2);
    stop();
  });

  test("an infinite browse pages forward to exhaustion with consistent views", async () => {
    /** Verifies: QC-INF-001, QC-INF-002, QC-INF-003 */
    const client = makeClient();
    const totalPages = 3;
    const observer = new InfiniteQueryObserver(client, {
      queryKey: ["feed"],
      queryFn: async (ctx: any) => ({ items: [`item-${ctx.pageParam}`] }),
      initialPageParam: 0,
      getNextPageParam: (_l: any, all: any[]) =>
        all.length < totalPages ? all.length : undefined,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    while (observer.getCurrentResult().hasNextPage) {
      await observer.fetchNextPage();
    }
    const result: any = observer.getCurrentResult();
    expect(result.hasNextPage).toBe(false);
    expect(result.data.pages.length).toBe(totalPages);
    expect(result.data.pages.map((p: any) => p.items[0])).toEqual([
      "item-0",
      "item-1",
      "item-2",
    ]);
    const cached: any = client.getQueryData(["feed"]);
    expect(cached.pages).toEqual(result.data.pages);
    expect(cached.pageParams).toEqual([0, 1, 2]);
    await observer.fetchNextPage();
    expect((client.getQueryData(["feed"]) as any).pages.length).toBe(totalPages);
    stop();
  });

  test("an optimistic update is rolled back through the mutation context on failure", async () => {
    /** Verifies: QC-MUT-003, QC-MUT-004, QC-DIR-003 */
    const client = makeClient();
    client.setQueryData(["todos"], ["existing"]);
    const boom = new Error("server down");
    const mutation = new MutationObserver(client, {
      mutationFn: async (_todo: string) => {
        await sleep(10);
        throw boom;
      },
      onMutate: (todo: string) => {
        const previous = client.getQueryData(["todos"]);
        client.setQueryData(["todos"], (old: any) => [...old, todo]);
        return { previous };
      },
      onError: (_err: any, _todo: string, ctx: any) => {
        client.setQueryData(["todos"], ctx.previous);
      },
    });
    const attempt = mutation.mutate("optimistic");
    await waitUntil(() => (client.getQueryData(["todos"]) as string[]).length === 2);
    expect(client.getQueryData(["todos"])).toEqual(["existing", "optimistic"]);
    await expect(attempt).rejects.toBe(boom);
    expect(client.getQueryData(["todos"])).toEqual(["existing"]);
    expect(mutation.getCurrentResult().status).toBe("error");
    expect(mutation.getCurrentResult().error).toBe(boom);
  });

  test("an abandoned entry is garbage collected and journaled as removed", async () => {
    /** Verifies: QC-FET-011, QC-FLT-010 */
    const client = makeClient();
    const events: string[] = [];
    const stopEvents = client.getQueryCache().subscribe((e) => events.push(e.type));
    const observer = new QueryObserver(client, {
      queryKey: ["temp"],
      queryFn: async () => "short-lived",
      gcTime: 50,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => observer.getCurrentResult().status === "success");
    expect(client.getQueryData(["temp"])).toBe("short-lived");
    stop();
    await sleep(250);
    expect(client.getQueryData(["temp"])).toBeUndefined();
    expect(client.getQueryCache().findAll().length).toBe(0);
    expect(events[events.length - 1]).toBe("removed");
    stopEvents();
  });

  test("a full invalidate cycle refreshes data and clears staleness everywhere", async () => {
    /** Verifies: QC-CVI-004, QC-FLT-004, QC-FLT-006 */
    const client = makeClient();
    let version = 1;
    const entryEvents: string[] = [];
    const stopEvents = client.getQueryCache().subscribe((e) => {
      if (e.type === "added" || e.type === "updated" || e.type === "removed") {
        entryEvents.push(e.type);
      }
    });
    const observer = new QueryObserver(client, {
      queryKey: ["doc"],
      queryFn: async () => ({ version }),
      staleTime: 60_000,
    });
    const stop = observer.subscribe(() => {});
    await waitUntil(() => (observer.getCurrentResult().data as any)?.version === 1);
    expect(client.getQueryCache().findAll({ stale: true }).length).toBe(0);
    version = 2;
    const updatesBefore = entryEvents.filter((t) => t === "updated").length;
    await client.invalidateQueries({ queryKey: ["doc"] });
    await waitUntil(() => (observer.getCurrentResult().data as any)?.version === 2);
    expect(client.getQueryData(["doc"])).toEqual({ version: 2 });
    expect(client.getQueryState(["doc"])!.isInvalidated).toBe(false);
    expect(client.getQueryCache().findAll({ stale: true }).length).toBe(0);
    expect(entryEvents[0]).toBe("added");
    expect(entryEvents.filter((t) => t === "updated").length).toBeGreaterThan(updatesBefore);
    stop();
    stopEvents();
  });
});
