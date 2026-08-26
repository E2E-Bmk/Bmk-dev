// Oracle - integration tests for the memfs in-memory file-system specification.
import { describe, test, expect } from "vitest";
import { memfs, Volume, vol, createFsFromVolume } from "memfs";

function codeOf(fn: () => unknown): string | undefined {
  try {
    fn();
    return undefined;
  } catch (e) {
    return (e as any).code;
  }
}

// ---------------------------------------------------------------------------
describe("snapshot agreement", () => {
  test("a tree built by operations snapshots and restores faithfully", () => {
    /** Verifies: MFS-INV-001, MFS-INV-006 */
    const v = new Volume();
    v.mkdirSync("/proj/src", { recursive: true });
    v.writeFileSync("/proj/src/main.ts", "export const n = 17;");
    v.appendFileSync("/proj/src/main.ts", "\nexport const m = 4;");
    v.writeFileSync("/proj/notes.md", "remember the demo");
    v.mkdirSync("/proj/dist");
    const snap = v.toJSON();
    expect(snap).toEqual({
      "/proj/src/main.ts": "export const n = 17;\nexport const m = 4;",
      "/proj/notes.md": "remember the demo",
      "/proj/dist": null,
    });
    const restored = Volume.fromJSON(snap);
    for (const [p, content] of Object.entries(snap)) {
      if (content === null) {
        expect(restored.statSync(p).isDirectory()).toBe(true);
      } else {
        expect(restored.readFileSync(p, "utf8")).toBe(content);
      }
    }
  });

  test("every toJSON path reads back exactly and every plain file appears", () => {
    /** Verifies: MFS-INV-001 */
    const v = Volume.fromJSON({
      "/atlas/maps/north.txt": "N",
      "/atlas/maps/south.txt": "S",
      "/atlas/index.txt": "two maps",
    });
    const snap = v.toJSON();
    expect(Object.keys(snap).sort()).toEqual([
      "/atlas/index.txt",
      "/atlas/maps/north.txt",
      "/atlas/maps/south.txt",
    ]);
    for (const [p, c] of Object.entries(snap)) {
      expect(v.readFileSync(p, "utf8")).toBe(c);
    }
  });

  test("restoring a snapshot flattens links into independent plain files", () => {
    /** Verifies: MFS-INV-006, MFS-VOL-015 */
    const v = Volume.fromJSON({ "/genuine.txt": "carbon" });
    v.linkSync("/genuine.txt", "/twin.txt");
    v.symlinkSync("/genuine.txt", "/shadow.txt");
    const snap = v.toJSON();
    expect(snap).toEqual({ "/genuine.txt": "carbon", "/twin.txt": "carbon" });
    const r = Volume.fromJSON(snap);
    expect(r.existsSync("/shadow.txt")).toBe(false);
    expect(r.statSync("/genuine.txt").nlink).toBe(1);
    expect(r.statSync("/twin.txt").nlink).toBe(1);
    expect(r.statSync("/genuine.txt").ino).not.toBe(r.statSync("/twin.txt").ino);
    r.writeFileSync("/twin.txt", "severed");
    expect(r.readFileSync("/genuine.txt", "utf8")).toBe("carbon");
  });

  test("nested and flat construction of the same tree agree in every view", () => {
    /** Verifies: MFS-VOL-005, MFS-VOL-006, MFS-INV-001 */
    const nested = Volume.fromNestedJSON({
      "/store": { bins: { "b1.txt": "nails" }, "list.txt": "one bin" },
    });
    const flat = Volume.fromJSON({
      "/store/bins/b1.txt": "nails",
      "/store/list.txt": "one bin",
    });
    expect(nested.toJSON()).toEqual({
      "/store/bins/b1.txt": "nails",
      "/store/list.txt": "one bin",
    });
    expect(nested.toJSON()).toEqual(flat.toJSON());
    expect(nested.readdirSync("/store")).toEqual(["bins", "list.txt"]);
    expect(nested.readdirSync("/store")).toEqual(flat.readdirSync("/store"));
    expect(nested.readdirSync("/store", { recursive: true })).toEqual(
      flat.readdirSync("/store", { recursive: true }),
    );
  });
});

// ---------------------------------------------------------------------------
describe("cross-projection content agreement", () => {
  test("bytes written through one projection are identical through all readers", async () => {
    /** Verifies: MFS-INV-002 */
    const v = new Volume();
    const ws = v.createWriteStream("/agree.txt");
    ws.write("stream-origin");
    ws.end();
    await new Promise<void>((resolve) => ws.on("finish", () => resolve()));

    expect(v.readFileSync("/agree.txt", "utf8")).toBe("stream-origin");
    expect(await v.promises.readFile("/agree.txt", "utf8")).toBe("stream-origin");

    const fd = v.openSync("/agree.txt", "r");
    const buf = Buffer.alloc(13);
    expect(v.readSync(fd, buf, 0, 13, 0)).toBe(13);
    expect(buf.toString()).toBe("stream-origin");
    expect(v.fstatSync(fd).size).toBe(13);
    v.closeSync(fd);
    expect(v.statSync("/agree.txt").size).toBe(13);

    const rs = v.createReadStream("/agree.txt", { encoding: "utf8" } as any);
    let acc = "";
    rs.on("data", (c: any) => (acc += c));
    await new Promise<void>((resolve) => rs.on("end", () => resolve()));
    expect(acc).toBe("stream-origin");
  });

  test("positional descriptor patches are seen by snapshot, promise and stat views", async () => {
    /** Verifies: MFS-FD-004, MFS-FD-006, MFS-INV-002 */
    const v = Volume.fromJSON({ "/canvas.txt": "..........." });
    const fd = v.openSync("/canvas.txt", "r+");
    v.writeSync(fd, "AB", 2);
    v.writeSync(fd, "YZ", 8);
    v.closeSync(fd);
    expect(v.readFileSync("/canvas.txt", "utf8")).toBe("..AB....YZ.");
    expect(await v.promises.readFile("/canvas.txt", "utf8")).toBe("..AB....YZ.");
    expect(v.toJSON()["/canvas.txt"]).toBe("..AB....YZ.");
    expect(v.statSync("/canvas.txt").size).toBe(11);
  });

  test("truncate, append and descriptor writes keep sizes consistent everywhere", async () => {
    /** Verifies: MFS-MET-005, MFS-INV-002 */
    const v = Volume.fromJSON({ "/gauge.txt": "0123456789" });
    v.truncateSync("/gauge.txt", 4);
    v.appendFileSync("/gauge.txt", "++");
    const fd = v.openSync("/gauge.txt", "a");
    v.writeSync(fd, "!");
    const viaFstat = v.fstatSync(fd).size;
    v.closeSync(fd);
    const content = v.readFileSync("/gauge.txt", "utf8");
    expect(content).toBe("0123++!");
    expect(viaFstat).toBe(7);
    expect(v.statSync("/gauge.txt").size).toBe(7);
    expect((await v.promises.stat("/gauge.txt")).size).toBe(7);
    expect((v.toJSON()["/gauge.txt"] as string).length).toBe(7);
  });

  test("piping a read stream into a write stream copies a file", async () => {
    /** Verifies: MFS-ASY-005, MFS-INV-002 */
    const v = Volume.fromJSON({ "/pipe-src.txt": "carry me across" });
    const rs = v.createReadStream("/pipe-src.txt");
    const ws = v.createWriteStream("/pipe-dst.txt");
    rs.pipe(ws as any);
    await new Promise<void>((resolve) => ws.on("finish", () => resolve()));
    expect(v.readFileSync("/pipe-dst.txt", "utf8")).toBe("carry me across");
    expect(v.toJSON()["/pipe-dst.txt"]).toBe("carry me across");
  });

  test("one file written by wrapper, promise and callback stays coherent", async () => {
    /** Verifies: MFS-ASY-001, MFS-ASY-003, MFS-INV-002 */
    const v = new Volume();
    const wrapped = createFsFromVolume(v);
    wrapped.writeFileSync("/ledger.txt", "line1\n");
    await v.promises.appendFile("/ledger.txt", "line2\n");
    await new Promise<void>((resolve, reject) => {
      v.appendFile("/ledger.txt", "line3\n", (e) => (e ? reject(e) : resolve()));
    });
    const expected = "line1\nline2\nline3\n";
    expect(wrapped.readFileSync("/ledger.txt", "utf8")).toBe(expected);
    expect(await wrapped.promises.readFile("/ledger.txt", "utf8")).toBe(expected);
    expect(v.toJSON()["/ledger.txt"]).toBe(expected);
  });
});

// ---------------------------------------------------------------------------
describe("directory and metadata agreement", () => {
  test("readdir names, dirents and lstat predicates agree", () => {
    /** Verifies: MFS-INV-003 */
    const v = Volume.fromJSON({
      "/mix/afile.txt": "f",
      "/mix/bdir/inner.txt": "i",
    });
    v.symlinkSync("/mix/afile.txt", "/mix/clink");
    const names = v.readdirSync("/mix") as string[];
    expect(names).toEqual(["afile.txt", "bdir", "clink"]);
    const ents = v.readdirSync("/mix", { withFileTypes: true }) as any[];
    expect(ents.map((d) => String(d.name))).toEqual(names);
    expect(ents.filter((d) => d.isFile()).map((d) => String(d.name))).toEqual([
      "afile.txt",
    ]);
    for (const d of ents) {
      const st = v.lstatSync(`/mix/${String(d.name)}`);
      expect(d.isFile()).toBe(st.isFile());
      expect(d.isDirectory()).toBe(st.isDirectory());
      expect(d.isSymbolicLink()).toBe(st.isSymbolicLink());
    }
  });

  test("hard-linked names agree across stats, reads and listings", () => {
    /** Verifies: MFS-INV-004 */
    const v = Volume.fromJSON({ "/pool/prime.txt": "shared payload" });
    v.linkSync("/pool/prime.txt", "/pool/echo.txt");
    v.linkSync("/pool/prime.txt", "/third.txt");
    const names = ["/pool/prime.txt", "/pool/echo.txt", "/third.txt"];
    const inos = names.map((n) => v.statSync(n).ino);
    expect(new Set(inos).size).toBe(1);
    for (const n of names) {
      expect(v.statSync(n).nlink).toBe(3);
      expect(v.statSync(n).size).toBe(14);
      expect(v.readFileSync(n, "utf8")).toBe("shared payload");
    }
    v.unlinkSync("/third.txt");
    expect(v.statSync("/pool/prime.txt").nlink).toBe(2);
    expect(v.readdirSync("/pool")).toEqual(["echo.txt", "prime.txt"]);
  });

  test("a rename is observed atomically by every projection", () => {
    /** Verifies: MFS-INV-005 */
    const v = Volume.fromJSON({
      "/cabinet/drawer/socks.txt": "wool",
      "/cabinet/label.txt": "winter",
    });
    const ino = v.statSync("/cabinet/drawer/socks.txt").ino;
    v.renameSync("/cabinet", "/wardrobe");
    expect(v.existsSync("/cabinet")).toBe(false);
    expect(v.readdirSync("/")).toEqual(["wardrobe"]);
    expect(v.toJSON()).toEqual({
      "/wardrobe/drawer/socks.txt": "wool",
      "/wardrobe/label.txt": "winter",
    });
    expect(v.readFileSync("/wardrobe/drawer/socks.txt", "utf8")).toBe("wool");
    expect(v.statSync("/wardrobe/drawer/socks.txt").ino).toBe(ino);
    expect(codeOf(() => v.readFileSync("/cabinet/label.txt"))).toBe("ENOENT");
  });

  test("permission changes gate every read projection consistently", async () => {
    /** Verifies: MFS-MET-008, MFS-MET-009, MFS-INV-007 */
    const v = Volume.fromJSON({ "/vaulted.txt": "classified" });
    v.chmodSync("/vaulted.txt", 0o000);
    expect(codeOf(() => v.readFileSync("/vaulted.txt"))).toBe("EACCES");
    await expect(v.promises.readFile("/vaulted.txt")).rejects.toMatchObject({
      code: "EACCES",
    });
    const cbCode = await new Promise<string>((resolve) => {
      v.readFile("/vaulted.txt", (e: any) => resolve(e && e.code));
    });
    expect(cbCode).toBe("EACCES");
    v.chmodSync("/vaulted.txt", 0o644);
    expect(v.readFileSync("/vaulted.txt", "utf8")).toBe("classified");
  });

  test("sync, callback and promise forms report the same missing-path code", async () => {
    /** Verifies: MFS-INV-007 */
    const v = new Volume();
    expect(codeOf(() => v.readFileSync("/same-code.txt"))).toBe("ENOENT");
    const cb = await new Promise<string>((resolve) => {
      v.readFile("/same-code.txt", (e: any) => resolve(e && e.code));
    });
    expect(cb).toBe("ENOENT");
    await expect(v.promises.readFile("/same-code.txt")).rejects.toMatchObject({
      code: "ENOENT",
    });
    expect(codeOf(() => v.unlinkSync("/same-code.txt"))).toBe("ENOENT");
    const cbUnlink = await new Promise<string>((resolve) => {
      v.unlink("/same-code.txt", (e: any) => resolve(e && e.code));
    });
    expect(cbUnlink).toBe("ENOENT");
    await expect(v.promises.unlink("/same-code.txt")).rejects.toMatchObject({
      code: "ENOENT",
    });
  });
});

// ---------------------------------------------------------------------------
describe("links across projections", () => {
  test("writes through a directory symlink land in the real tree", () => {
    /** Verifies: MFS-LNK-002, MFS-INV-001 */
    const v = Volume.fromJSON({ "/realroom/desk.txt": "oak" });
    v.symlinkSync("/realroom", "/door");
    v.writeFileSync("/door/chair.txt", "pine");
    expect(v.readFileSync("/realroom/chair.txt", "utf8")).toBe("pine");
    expect(v.readdirSync("/door")).toEqual(["chair.txt", "desk.txt"]);
    expect(v.realpathSync("/door/chair.txt")).toBe("/realroom/chair.txt");
    expect(v.toJSON()["/realroom/chair.txt"]).toBe("pine");
    expect(Object.keys(v.toJSON())).not.toContain("/door/chair.txt");
  });

  test("a dangling link joins the tree when its target arrives via promises", async () => {
    /** Verifies: MFS-LNK-006, MFS-LNK-007, MFS-ASY-003 */
    const v = new Volume();
    v.symlinkSync("/supply/box.txt", "/reserved");
    expect(v.existsSync("/reserved")).toBe(false);
    await expect(v.promises.readFile("/reserved")).rejects.toMatchObject({
      code: "ENOENT",
    });
    await v.promises.mkdir("/supply");
    await v.promises.writeFile("/supply/box.txt", "materialized");
    expect(v.existsSync("/reserved")).toBe(true);
    expect(v.readFileSync("/reserved", "utf8")).toBe("materialized");
    expect(v.realpathSync("/reserved")).toBe("/supply/box.txt");
  });

  test("hardlink content flows both ways across sync and promise writers", async () => {
    /** Verifies: MFS-LNK-009, MFS-INV-004 */
    const v = Volume.fromJSON({ "/tandem-a.txt": "start" });
    v.linkSync("/tandem-a.txt", "/tandem-b.txt");
    await v.promises.writeFile("/tandem-b.txt", "promise wrote this");
    expect(v.readFileSync("/tandem-a.txt", "utf8")).toBe("promise wrote this");
    const fd = v.openSync("/tandem-a.txt", "r+");
    v.writeSync(fd, "FD", 0);
    v.closeSync(fd);
    expect(await v.promises.readFile("/tandem-b.txt", "utf8")).toBe("FDomise wrote this");
    expect(v.statSync("/tandem-a.txt").size).toBe(v.statSync("/tandem-b.txt").size);
  });
});

// ---------------------------------------------------------------------------
describe("instances and isolation", () => {
  test("memfs pairs, wrappers and the default volume stay independent", () => {
    /** Verifies: MFS-VOL-011, MFS-VOL-012, MFS-VOL-013 */
    vol.reset();
    try {
      const one = memfs({ "/one.txt": "1" });
      const two = memfs({ "/two.txt": "2" });
      const wrappedOne = createFsFromVolume(one.vol);
      wrappedOne.writeFileSync("/one-extra.txt", "1x");
      expect(one.fs.readFileSync("/one-extra.txt", "utf8")).toBe("1x");
      expect(two.vol.existsSync("/one.txt")).toBe(false);
      expect(two.vol.existsSync("/one-extra.txt")).toBe(false);
      expect(one.vol.existsSync("/two.txt")).toBe(false);
      expect(vol.existsSync("/one.txt")).toBe(false);
      expect(vol.existsSync("/two.txt")).toBe(false);
      expect(vol.toJSON()).toEqual({});
    } finally {
      vol.reset();
    }
  });

  test("a deep copy between volumes via snapshot has independent state", () => {
    /** Verifies: MFS-VOL-002, MFS-VOL-006, MFS-VOL-013 */
    const src = Volume.fromJSON({ "/data/rows.csv": "a,b\n1,2\n" });
    const dst = Volume.fromJSON(src.toJSON());
    dst.appendFileSync("/data/rows.csv", "3,4\n");
    expect(src.readFileSync("/data/rows.csv", "utf8")).toBe("a,b\n1,2\n");
    expect(dst.readFileSync("/data/rows.csv", "utf8")).toBe("a,b\n1,2\n3,4\n");
  });

  test("cp recursive inside one volume then divergence leaves the copy alone", () => {
    /** Verifies: MFS-FIL-019, MFS-INV-001 */
    const v = Volume.fromJSON({
      "/theme/base.css": "body{}",
      "/theme/parts/btn.css": ".btn{}",
    });
    v.cpSync("/theme", "/theme-v2", { recursive: true });
    v.writeFileSync("/theme/base.css", "body{margin:0}");
    v.rmSync("/theme/parts", { recursive: true });
    expect(v.readFileSync("/theme-v2/base.css", "utf8")).toBe("body{}");
    expect(v.readFileSync("/theme-v2/parts/btn.css", "utf8")).toBe(".btn{}");
    expect(v.toJSON("/theme-v2")).toEqual({
      "/theme-v2/base.css": "body{}",
      "/theme-v2/parts/btn.css": ".btn{}",
    });
  });

  test("mkdtemp workspaces live a full create-use-destroy cycle", () => {
    /** Verifies: MFS-FIL-009, MFS-FIL-016, MFS-INV-001 */
    const v = new Volume();
    v.mkdirSync("/work");
    const dir = v.mkdtempSync("/work/job-") as string;
    v.writeFileSync(`${dir}/result.txt`, "42");
    expect(v.readdirSync("/work")).toEqual([dir.slice("/work/".length)]);
    expect(v.toJSON()[`${dir}/result.txt`]).toBe("42");
    v.rmSync(dir, { recursive: true });
    expect(v.readdirSync("/work")).toEqual([]);
    expect(v.toJSON()).toEqual({ "/work": null });
  });

  test("mixed failure codes surface correctly across one populated tree", () => {
    /** Verifies: MFS-ERR-002 */
    const v = Volume.fromJSON({
      "/estate/house/key.txt": "brass",
      "/estate/garden": null,
    });
    expect(codeOf(() => v.mkdirSync("/estate/house"))).toBe("EEXIST");
    expect(codeOf(() => v.readFileSync("/estate/house"))).toBe("EISDIR");
    expect(codeOf(() => v.readdirSync("/estate/house/key.txt"))).toBe("ENOTDIR");
    expect(codeOf(() => v.unlinkSync("/estate/garden"))).toBe("EPERM");
    expect(codeOf(() => v.rmdirSync("/estate/house"))).toBe("ENOTEMPTY");
    expect(codeOf(() => v.rmSync("/estate/house"))).toBe("ERR_FS_EISDIR");
    expect(codeOf(() => v.writeFileSync("/estate/house/key.txt/sub", "x"))).toBe("ENOTDIR");
    expect(codeOf(() => v.readFileSync("/estate/cellar/wine.txt"))).toBe("ENOENT");
  });
});

// ---------------------------------------------------------------------------
describe("end-to-end workflows", () => {
  test("a project scaffold is built, linked, verified and snapshotted", () => {
    /** Verifies: MFS-INV-001, MFS-INV-003, MFS-INV-004, MFS-LNK-004 */
    const { fs: pfs, vol: pvol } = memfs();
    pfs.mkdirSync("/app/src/lib", { recursive: true });
    pfs.writeFileSync("/app/src/lib/util.ts", "export const u = 1;");
    pfs.writeFileSync("/app/src/entry.ts", "import './lib/util';");
    pfs.appendFileSync("/app/src/entry.ts", "\nexport {};");
    pfs.symlinkSync("/app/src/lib", "/app/lib-link");
    pfs.linkSync("/app/src/entry.ts", "/app/entry-alias.ts");

    expect(pfs.readFileSync("/app/lib-link/util.ts", "utf8")).toBe("export const u = 1;");
    expect(pfs.realpathSync("/app/lib-link/util.ts")).toBe("/app/src/lib/util.ts");
    expect(pfs.statSync("/app/entry-alias.ts").nlink).toBe(2);

    const listing = pfs.readdirSync("/app", { recursive: true }) as string[];
    expect([...listing].sort()).toEqual([
      "entry-alias.ts",
      "lib-link",
      "src",
      "src/entry.ts",
      "src/lib",
      "src/lib/util.ts",
    ]);

    const snap = pvol.toJSON();
    expect(snap).toEqual({
      "/app/src/lib/util.ts": "export const u = 1;",
      "/app/src/entry.ts": "import './lib/util';\nexport {};",
      "/app/entry-alias.ts": "import './lib/util';\nexport {};",
    });

    const restored = Volume.fromJSON(snap);
    expect(restored.existsSync("/app/lib-link")).toBe(false);
    expect(restored.statSync("/app/entry-alias.ts").nlink).toBe(1);
    expect(restored.readFileSync("/app/entry-alias.ts", "utf8")).toBe(
      "import './lib/util';\nexport {};",
    );
  });

  test("an editor session mixes descriptors, promises, truncation and streams", async () => {
    /** Verifies: MFS-FD-003, MFS-FD-004, MFS-FD-005, MFS-ASY-003, MFS-ASY-005, MFS-INV-002 */
    const v = new Volume();
    v.mkdirSync("/doc");

    const fd = v.openSync("/doc/draft.txt", "w+");
    v.writeSync(fd, "The quick brown fox");
    v.writeSync(fd, "slow!", 4);
    v.ftruncateSync(fd, 15);
    const probe = Buffer.alloc(5);
    v.readSync(fd, probe, 0, 5, 4);
    expect(probe.toString()).toBe("slow!");
    v.closeSync(fd);
    expect(v.readFileSync("/doc/draft.txt", "utf8")).toBe("The slow! brown");

    await v.promises.appendFile("/doc/draft.txt", " cat");

    const rs = v.createReadStream("/doc/draft.txt", { encoding: "utf8" } as any);
    let seen = "";
    rs.on("data", (c: any) => (seen += c));
    await new Promise<void>((resolve) => rs.on("end", () => resolve()));
    expect(seen).toBe("The slow! brown cat");
    expect(v.statSync("/doc/draft.txt").size).toBe(19);
    expect(v.toJSON()["/doc/draft.txt"]).toBe("The slow! brown cat");
  });

  test("a backup is exported, reorganized in a second volume and verified", async () => {
    /** Verifies: MFS-VOL-004, MFS-INV-005, MFS-INV-006, MFS-FIL-017 */
    const live = Volume.fromJSON({
      "/svc/config/app.json": '{"port":7314}',
      "/svc/data/users.db": "u1|u2",
      "/svc/data/cache/tmp1": "junk",
    });
    live.rmSync("/svc/data/cache", { recursive: true });
    const backup = live.toJSON("/svc");

    const restoreVol = new Volume();
    restoreVol.fromJSON(backup, "/");
    restoreVol.renameSync("/svc", "/restored-svc");

    expect(restoreVol.toJSON()).toEqual({
      "/restored-svc/config/app.json": '{"port":7314}',
      "/restored-svc/data/users.db": "u1|u2",
    });
    expect(await restoreVol.promises.readFile("/restored-svc/data/users.db", "utf8")).toBe(
      "u1|u2",
    );
    expect(codeOf(() => restoreVol.readFileSync("/svc/config/app.json"))).toBe("ENOENT");
    expect(live.readFileSync("/svc/config/app.json", "utf8")).toBe('{"port":7314}');
  });

  test("a content pipeline decodes, guards and republishes across projections", async () => {
    /** Verifies: MFS-FIL-002, MFS-FIL-018, MFS-MET-008, MFS-MET-009, MFS-INV-002 */
    const v = new Volume();
    v.mkdirSync("/intake", { recursive: true });
    v.writeFileSync("/intake/payload.txt", "cHVibGlzaCBtZQ==", { encoding: "base64" });
    expect(v.readFileSync("/intake/payload.txt", "utf8")).toBe("publish me");

    v.copyFileSync("/intake/payload.txt", "/outbox-payload.txt");
    v.chmodSync("/intake/payload.txt", 0o000);
    expect(codeOf(() => v.readFileSync("/intake/payload.txt"))).toBe("EACCES");
    expect(v.readFileSync("/outbox-payload.txt", "utf8")).toBe("publish me");

    v.truncateSync("/outbox-payload.txt", 7);
    v.appendFileSync("/outbox-payload.txt", "ed!");
    expect(await v.promises.readFile("/outbox-payload.txt", "utf8")).toBe("published!");
    expect(v.statSync("/outbox-payload.txt").size).toBe(10);
    expect(v.toJSON()["/outbox-payload.txt"]).toBe("published!");
  });
});
