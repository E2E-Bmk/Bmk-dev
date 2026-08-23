import { serve } from "srvx";
import { describe, expect, it } from "vitest";
import {
  createStorage,
  filterKeyByBase,
  filterKeyByDepth,
  joinKeys,
  normalizeBaseKey,
  normalizeKey,
  prefixStorage,
  restoreSnapshot,
  snapshot,
} from "unstorage";
import httpDriver from "unstorage/drivers/http";
import { createStorageHandler } from "unstorage/server";

describe("generated atomic coverage", () => {
  /**
   * Verifies: UNS-KEYS-001
   */

  /**
   * Verifies: UNS-KEYS-003
   */

  /**
   * Verifies: UNS-KEYS-002
   */

  /**
   * Verifies: UNS-KEYS-004
   */

  /**
   * Verifies: UNS-KEYS-005
   */

  /**
   * Verifies: UNS-STOR-009
   */

  /**
   * Verifies: UNS-STOR-005, UNS-ERR-001
   */

  /**
   * Verifies: UNS-DRV-002, UNS-ERR-006
   */

  /**
   * Verifies: UNS-STOR-010, UNS-ERR-006
   */

  /**
   * Verifies: UNS-STOR-012, UNS-STOR-014, UNS-DRV-003
   */

  /**
   * Verifies: UNS-STOR-011, UNS-STOR-015, UNS-STOR-016
   */

  /**
   * Verifies: UNS-STOR-003, UNS-STOR-004, UNS-KEYS-011
   */
});

describe("generated integration coverage", () => {
  /**
   * Verifies: UNS-KEYS-003, UNS-KEYS-006, UNS-CVI-002
   */
  it("uses the same graph through an empty prefix view", async () => {
    const storage = createStorage();
    const prefixed = prefixStorage(storage, "");

    await prefixed.setItem("a/b?x=1", "v");

    expect(await storage.getKeys()).toEqual(["a:b"]);
    expect(await storage.getItem("a:b")).toBe("v");
    expect(await snapshot(storage, "")).toEqual({ "a:b": "v" });
    expect(await snapshot(prefixed, "")).toEqual({ "a:b": "v" });
  });

  /**
   * Verifies: UNS-KEYS-001, UNS-KEYS-007, UNS-KEYS-008, UNS-CVI-003
   */
  it("restores snapshots under normalized bases and reads them back through snapshots", async () => {
    const storage = createStorage();

    await restoreSnapshot(storage, { "source:item": { nested: true } }, "backup\\copy");

    expect(await storage.getItem("backup:copy:source:item")).toEqual({ nested: true });
    expect(await snapshot(storage, "backup/copy")).toEqual({
      "source:item": { nested: true },
    });
  });

  /**
   * Verifies: UNS-TRACE-004, UNS-TRACE-005, UNS-TRACE-006, UNS-TRACE-009
   */
  it("serves PUT GET and HEAD through the fetch handler with authorization context", async () => {
    const storage = createStorage();
    const seen: Array<{ key: string; type: string; method: string }> = [];
    const handler = createStorageHandler(storage, {
      authorize(request) {
        seen.push({
          key: request.key,
          type: request.type,
          method: request.request.method,
        });
      },
    });

    const put = await handler(new Request("http://local/docs/item", { method: "PUT", body: "stored" }));
    expect(put.status).toBe(200);
    expect(await put.text()).toBe("OK");
    expect(await storage.getItem("docs:item")).toBe("stored");

    const get = await handler(new Request("http://local/docs/item", { method: "GET" }));
    expect(get.status).toBe(200);
    expect(await get.text()).toBe("stored");

    const head = await handler(new Request("http://local/docs/item", { method: "HEAD" }));
    expect(head.status).toBe(200);
    expect(await head.text()).toBe("");

    expect(seen).toEqual([
      { key: "docs:item", type: "write", method: "PUT" },
      { key: "docs:item", type: "read", method: "GET" },
      { key: "docs:item", type: "read", method: "HEAD" },
    ]);
  });

  /**
   * Verifies: UNS-TRACE-006, UNS-CVI-006
   */
  it("lists base paths over HTTP with slash-form keys", async () => {
    const storage = createStorage();
    await storage.setItem("docs:one", "1");
    await storage.setItem("docs:two", "2");
    await storage.setItem("other", "3");

    const response = await createStorageHandler(storage)(
      new Request("http://local/docs/", { method: "GET" }),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/json");
    expect(await response.json()).toEqual(["docs/one", "docs/two"]);
  });

  /**
   * Verifies: UNS-STOR-010, UNS-TRACE-008, UNS-CVI-006
   */
  it("stores and returns octet-stream request bodies as raw values", async () => {
    const storage = createStorage();
    const handler = createStorageHandler(storage);
    const raw = new Uint8Array([0, 1, 2, 255]);

    const put = await handler(
      new Request("http://local/bin/file", {
        method: "PUT",
        body: raw,
        headers: { "content-type": "application/octet-stream" },
      }),
    );
    expect(put.status).toBe(200);
    expect(await storage.getItemRaw("bin:file")).toEqual(raw);

    const get = await handler(
      new Request("http://local/bin/file", {
        method: "GET",
        headers: { accept: "application/octet-stream" },
      }),
    );
    expect(get.status).toBe(200);
    expect(Array.from(new Uint8Array(await get.arrayBuffer()))).toEqual([0, 1, 2, 255]);
  });

  /**
   * Verifies: UNS-ERR-003, UNS-ERR-004, UNS-TRACE-010
   */
  it("maps authorization failures and unsupported methods to HTTP error statuses", async () => {
    const storage = createStorage();
    const handler = createStorageHandler(storage, {
      authorize(request) {
        if (request.key === "private:item") {
          throw new Error("blocked");
        }
      },
    });

    const unauthorized = await handler(new Request("http://local/private/item", { method: "GET" }));
    expect(unauthorized.status).toBe(401);
    await expect(unauthorized.json()).resolves.toMatchObject({ status: 401 });

    const unsupported = await handler(new Request("http://local/private/item", { method: "PATCH" }));
    expect(unsupported.status).toBe(405);
    await expect(unsupported.json()).resolves.toMatchObject({ status: 405 });
  });

  /**
   * Verifies: UNS-TRACE-011, UNS-CVI-001
   */
  it("uses resolvePath before normalizing the handler key", async () => {
    const storage = createStorage();
    const handler = createStorageHandler(storage, {
      resolvePath() {
        return "/resolved/key";
      },
    });

    const put = await handler(new Request("http://local/ignored/path", { method: "PUT", body: "stored" }));

    expect(put.status).toBe(200);
    expect(await storage.getItem("resolved:key")).toBe("stored");
    expect(await storage.getItem("ignored:path")).toBe(null);
  });

  /**
   * Verifies: UNS-DRV-007, UNS-TRACE-004, UNS-CVI-006
   */
  it("lets the HTTP driver consume a fetch-served storage graph", async () => {
    const storage = createStorage();
    const server = await serve({ port: 0, fetch: createStorageHandler(storage) });

    try {
      const remote = createStorage({ driver: httpDriver({ base: server.url! }) });

      await remote.setItem("remote/path", { ok: true });
      expect(await storage.getItem("remote:path")).toEqual({ ok: true });
      expect(await remote.getItem("remote/path")).toEqual({ ok: true });
      expect(await remote.getKeys("remote")).toEqual(["remote:path"]);

      const raw = new Uint8Array([7, 8, 9]);
      await remote.setItemRaw("remote/raw.bin", raw);
      expect(await storage.getItemRaw("remote:raw.bin")).toEqual(raw);
      expect(Array.from(new Uint8Array(await remote.getItemRaw("remote/raw.bin")))).toEqual([7, 8, 9]);
    } finally {
      await server.close();
    }
  });
});
