import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { createDatabase } from "db0";
import { createStorage } from "unstorage";
import db0Driver from "unstorage/drivers/db0";

async function sqliteDatabase() {
  const sqlite = await import("db0/connectors/node-sqlite").then((m) => m.default);
  return createDatabase(sqlite({ name: ":memory:" }));
}
async function libsqlDatabase() {
  const libSQL = await import("db0/connectors/libsql/node").then((m) => m.default);
  return createDatabase(libSQL({ url: ":memory:" }));
}
async function pgliteDatabase() {
  const pglite = await import("db0/connectors/pglite").then((m) => m.default);
  return createDatabase(pglite());
}
function configureMetaSuite(getDB: () => Promise<any>) {
  let db: any;
  let storage: ReturnType<typeof createStorage>;
  beforeAll(async () => { db = await getDB(); storage = createStorage({ driver: db0Driver({ database: db }) }); });
  afterEach(async () => { await storage.clear(); });
  afterAll(async () => { await db.sql`DROP TABLE IF EXISTS unstorage`; await db.dispose?.(); });
  return () => storage;
}

describe("drivers: db0 - sqlite", () => {
  const getStorage = configureMetaSuite(sqliteDatabase);
  it("meta", async () => {
    const storage = getStorage();
    await storage.setItem("meta:test", "test_data");
    expect(await storage.getMeta("meta:test")).toMatchObject({ birthtime: expect.any(Date), mtime: expect.any(Date) });
  });
});

describe("drivers: db0 - libsql", () => {
  const getStorage = configureMetaSuite(libsqlDatabase);
  it("meta", async () => {
    const storage = getStorage();
    await storage.setItem("meta:test", "test_data");
    expect(await storage.getMeta("meta:test")).toMatchObject({ birthtime: expect.any(Date), mtime: expect.any(Date) });
  });
});

describe("drivers: db0 - pglite", () => {
  const getStorage = configureMetaSuite(pgliteDatabase);
  it("meta", async () => {
    const storage = getStorage();
    await storage.setItem("meta:test", "test_data");
    expect(await storage.getMeta("meta:test")).toMatchObject({ birthtime: expect.any(Date), mtime: expect.any(Date) });
  });
});
