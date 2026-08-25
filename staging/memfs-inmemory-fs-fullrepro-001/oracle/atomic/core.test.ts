// Oracle - atomic tests for the memfs in-memory file-system specification.
import { describe, test, expect } from "vitest";
import { memfs, Volume, vol, fs, createFsFromVolume } from "memfs";
import * as memfsNs from "memfs";

// The published type declarations do not re-export these runtime names.
const { Dirent, constants, F_OK, R_OK, W_OK, readFileSync: topReadFileSync } =
  memfsNs as any;

function codeOf(fn: () => unknown): string | undefined {
  try {
    fn();
    return undefined;
  } catch (e) {
    return (e as any).code;
  }
}

// ---------------------------------------------------------------------------
describe("volumes and snapshots", () => {
  test("a new volume is empty apart from the root directory", () => {
    /** Verifies: MFS-VOL-001 */
    const v = new Volume();
    expect(v.toJSON()).toEqual({});
    expect(v.readdirSync("/")).toEqual([]);
    expect(v.statSync("/").isDirectory()).toBe(true);
  });

  test("fromJSON materializes files, parents, and Buffer contents", () => {
    /** Verifies: MFS-VOL-002, MFS-VOL-014 */
    const v = Volume.fromJSON({
      "/ledger/entries/jan.csv": "41,ore",
      "/ledger/readme.txt": "ledger notes",
      "/ledger/blob.bin": Buffer.from([11, 22, 250]),
    } as any);
    expect(v.readFileSync("/ledger/entries/jan.csv", "utf8")).toBe("41,ore");
    expect(v.readFileSync("/ledger/readme.txt", "utf8")).toBe("ledger notes");
    expect(v.statSync("/ledger").isDirectory()).toBe(true);
    expect(v.statSync("/ledger/entries").isDirectory()).toBe(true);
    const raw = v.readFileSync("/ledger/blob.bin");
    expect(Buffer.isBuffer(raw)).toBe(true);
    expect([...(raw as Buffer)]).toEqual([11, 22, 250]);
  });

  test("a null value in fromJSON creates an empty directory", () => {
    /** Verifies: MFS-VOL-003 */
    const v = Volume.fromJSON({ "/hollow": null });
    expect(v.statSync("/hollow").isDirectory()).toBe(true);
    expect(v.readdirSync("/hollow")).toEqual([]);
  });

  test("instance fromJSON resolves relative keys against the cwd argument", () => {
    /** Verifies: MFS-VOL-004 */
    const v = new Volume();
    v.fromJSON({ "notes.md": "pinned" }, "/vault");
    expect(v.readFileSync("/vault/notes.md", "utf8")).toBe("pinned");
  });

  test("fromNestedJSON treats inner objects as directories", () => {
    /** Verifies: MFS-VOL-005 */
    const v = Volume.fromNestedJSON({
      "/warehouse": {
        aisles: { "a7.txt": "bolts" },
        "manifest.txt": "one aisle",
      },
    });
    expect(v.readFileSync("/warehouse/aisles/a7.txt", "utf8")).toBe("bolts");
    expect(v.readFileSync("/warehouse/manifest.txt", "utf8")).toBe("one aisle");
  });

  test("toJSON flattens files, marks empty dirs null, and filters by subtree", () => {
    /** Verifies: MFS-VOL-006, MFS-VOL-008 */
    const v = Volume.fromJSON({
      "/farm/silo/grain.txt": "rye",
      "/orchard/apple.txt": "gala",
    });
    v.mkdirSync("/farm/barn");
    expect(v.toJSON()).toEqual({
      "/farm/silo/grain.txt": "rye",
      "/orchard/apple.txt": "gala",
      "/farm/barn": null,
    });
    expect(v.toJSON("/farm")).toEqual({
      "/farm/silo/grain.txt": "rye",
      "/farm/barn": null,
    });
  });

  test("reset discards every node", () => {
    /** Verifies: MFS-VOL-009 */
    const v = Volume.fromJSON({ "/tmpwork/x.txt": "gone soon" });
    expect(v.readFileSync("/tmpwork/x.txt", "utf8")).toBe("gone soon");
    v.reset();
    expect(v.toJSON()).toEqual({});
    expect(v.existsSync("/tmpwork/x.txt")).toBe(false);
    expect(v.existsSync("/tmpwork")).toBe(false);
  });

  test("the default volume backs the fs export and top-level named exports", () => {
    /** Verifies: MFS-VOL-010 */
    vol.reset();
    try {
      vol.fromJSON({ "/shared-seed.txt": "from vol" });
      expect(fs.readFileSync("/shared-seed.txt", "utf8")).toBe("from vol");
      expect(topReadFileSync("/shared-seed.txt", "utf8")).toBe("from vol");
      fs.writeFileSync("/via-fs.txt", "written through fs");
      expect(vol.toJSON()["/via-fs.txt"]).toBe("written through fs");
    } finally {
      vol.reset();
    }
  });

  test("memfs() returns a seeded fs and vol pair", () => {
    /** Verifies: MFS-VOL-011 */
    const pair = memfs({ "/kit/tool.txt": "wrench" });
    expect(pair.fs.readFileSync("/kit/tool.txt", "utf8")).toBe("wrench");
    expect(pair.vol.toJSON()).toEqual({ "/kit/tool.txt": "wrench" });
  });

  test("createFsFromVolume wraps an existing volume in both directions", () => {
    /** Verifies: MFS-VOL-012 */
    const v = Volume.fromJSON({ "/core.txt": "root fact" });
    const wrapped = createFsFromVolume(v);
    expect(wrapped.readFileSync("/core.txt", "utf8")).toBe("root fact");
    wrapped.writeFileSync("/added-by-wrapper.txt", "hello volume");
    expect(v.readFileSync("/added-by-wrapper.txt", "utf8")).toBe("hello volume");
    v.writeFileSync("/added-by-volume.txt", "hello wrapper");
    expect(wrapped.readFileSync("/added-by-volume.txt", "utf8")).toBe("hello wrapper");
  });

  test("distinct volumes share no state", () => {
    /** Verifies: MFS-VOL-013 */
    const a = Volume.fromJSON({ "/only-in-a.txt": "a" });
    const b = Volume.fromJSON({ "/only-in-b.txt": "b" });
    expect(a.readFileSync("/only-in-a.txt", "utf8")).toBe("a");
    expect(b.readFileSync("/only-in-b.txt", "utf8")).toBe("b");
    expect(a.existsSync("/only-in-b.txt")).toBe(false);
    expect(b.existsSync("/only-in-a.txt")).toBe(false);
  });

  test("symbolic links are absent from toJSON while hard links appear per name", () => {
    /** Verifies: MFS-VOL-007 */
    const v = Volume.fromJSON({ "/origin.txt": "shared body" });
    v.symlinkSync("/origin.txt", "/soft-name");
    v.linkSync("/origin.txt", "/hard-name");
    expect(v.toJSON()).toEqual({
      "/origin.txt": "shared body",
      "/hard-name": "shared body",
    });
  });
});

// ---------------------------------------------------------------------------
describe("files and directories", () => {
  test("writeFileSync stores strings readable back through either encoding form", () => {
    /** Verifies: MFS-FIL-001, MFS-FIL-003 */
    const v = new Volume();
    v.writeFileSync("/memo.txt", "quarterly figures");
    expect(v.readFileSync("/memo.txt", "utf8")).toBe("quarterly figures");
    expect(v.readFileSync("/memo.txt", { encoding: "utf8" })).toBe("quarterly figures");
    v.writeFileSync("/memo.txt", "replaced entirely");
    expect(v.readFileSync("/memo.txt", "utf8")).toBe("replaced entirely");
  });

  test("readFileSync without encoding returns a Buffer", () => {
    /** Verifies: MFS-FIL-001, MFS-FIL-003 */
    const v = new Volume();
    v.writeFileSync("/raw.bin", Buffer.from([3, 141, 59]));
    const out = v.readFileSync("/raw.bin");
    expect(Buffer.isBuffer(out)).toBe(true);
    expect([...(out as Buffer)]).toEqual([3, 141, 59]);
  });

  test("writeFileSync decodes string data through the encoding option", () => {
    /** Verifies: MFS-FIL-002 */
    const v = new Volume();
    v.writeFileSync("/decoded.txt", "bWVtZnM=", { encoding: "base64" });
    expect(v.readFileSync("/decoded.txt", "utf8")).toBe("memfs");
    expect(v.readFileSync("/decoded.txt", "hex")).toBe("6d656d6673");
  });

  test("writeFileSync with flag a appends instead of replacing", () => {
    /** Verifies: MFS-FIL-002 */
    const v = Volume.fromJSON({ "/log.txt": "first;" });
    v.writeFileSync("/log.txt", "second;", { flag: "a" });
    expect(v.readFileSync("/log.txt", "utf8")).toBe("first;second;");
  });

  test("appendFileSync appends to existing files and creates missing ones", () => {
    /** Verifies: MFS-FIL-004 */
    const v = Volume.fromJSON({ "/journal.txt": "day1\n" });
    v.appendFileSync("/journal.txt", "day2\n");
    expect(v.readFileSync("/journal.txt", "utf8")).toBe("day1\nday2\n");
    v.appendFileSync("/fresh-log.txt", "born by append");
    expect(v.readFileSync("/fresh-log.txt", "utf8")).toBe("born by append");
  });

  test("writes reject missing parents and file path components", () => {
    /** Verifies: MFS-FIL-005 */
    const v = Volume.fromJSON({ "/plainfile": "content" });
    expect(codeOf(() => v.writeFileSync("/absent-dir/f.txt", "x"))).toBe("ENOENT");
    expect(codeOf(() => v.writeFileSync("/plainfile/child.txt", "x"))).toBe("ENOTDIR");
  });

  test("reading a directory as a file raises EISDIR", () => {
    /** Verifies: MFS-FIL-005 */
    const v = Volume.fromJSON({ "/box/item.txt": "in box" });
    expect(codeOf(() => v.readFileSync("/box"))).toBe("EISDIR");
  });

  test("non-recursive mkdir rejects missing parents and existing targets", () => {
    /** Verifies: MFS-FIL-006 */
    const v = Volume.fromJSON({ "/present": null });
    expect(codeOf(() => v.mkdirSync("/no-such/child"))).toBe("ENOENT");
    expect(codeOf(() => v.mkdirSync("/present"))).toBe("EEXIST");
    v.mkdirSync("/brand-new");
    expect(v.statSync("/brand-new").isDirectory()).toBe(true);
  });

  test("recursive mkdir returns the full target path or undefined when present", () => {
    /** Verifies: MFS-FIL-007 */
    const v = new Volume();
    const created = v.mkdirSync("/depot/bay/shelf", { recursive: true });
    expect(created).toBe("/depot/bay/shelf");
    expect(v.statSync("/depot/bay").isDirectory()).toBe(true);
    const again = v.mkdirSync("/depot/bay", { recursive: true });
    expect(again).toBeUndefined();
  });

  test("mkdtempSync appends six alphanumeric characters to the prefix", () => {
    /** Verifies: MFS-FIL-009 */
    const v = new Volume();
    const made = v.mkdtempSync("/scratch-") as string;
    expect(made.startsWith("/scratch-")).toBe(true);
    expect(/^[A-Za-z0-9]{6}$/.test(made.slice("/scratch-".length))).toBe(true);
    expect(v.statSync(made).isDirectory()).toBe(true);
  });

  test("readdirSync lists entry names lexicographically sorted", () => {
    /** Verifies: MFS-FIL-010 */
    const v = Volume.fromJSON({
      "/pack/zeta.txt": "z",
      "/pack/alpha.txt": "a",
      "/pack/midway/inner.txt": "m",
    });
    expect(v.readdirSync("/pack")).toEqual(["alpha.txt", "midway", "zeta.txt"]);
  });

  test("withFileTypes returns Dirent objects with parent paths and predicates", () => {
    /** Verifies: MFS-FIL-011 */
    const v = Volume.fromJSON({
      "/crate/leaf.txt": "L",
      "/crate/nested/deep.txt": "D",
    });
    const ents = v.readdirSync("/crate", { withFileTypes: true }) as any[];
    expect(ents.map((d) => String(d.name))).toEqual(["leaf.txt", "nested"]);
    expect(ents[0] instanceof Dirent).toBe(true);
    expect(ents[0].isFile()).toBe(true);
    expect(ents[0].isDirectory()).toBe(false);
    expect(ents[1].isDirectory()).toBe(true);
    expect(String((ents[0] as any).parentPath)).toBe("/crate");
    expect(String((ents[0] as any).path)).toBe("/crate");
  });

  test("recursive readdir returns descendant paths relative to the directory", () => {
    /** Verifies: MFS-FIL-012 */
    const v = Volume.fromJSON({
      "/site/index.html": "root page",
      "/site/assets/app.css": "styles",
    });
    const all = v.readdirSync("/site", { recursive: true }) as string[];
    expect([...all].sort()).toEqual(["assets", "assets/app.css", "index.html"]);
  });

  test("readdirSync rejects files with ENOTDIR and missing paths with ENOENT", () => {
    /** Verifies: MFS-FIL-013 */
    const v = Volume.fromJSON({ "/single.txt": "s" });
    expect(codeOf(() => v.readdirSync("/single.txt"))).toBe("ENOTDIR");
    expect(codeOf(() => v.readdirSync("/never-made"))).toBe("ENOENT");
  });

  test("unlinkSync removes files but rejects directories with EPERM", () => {
    /** Verifies: MFS-FIL-014 */
    const v = Volume.fromJSON({ "/target.txt": "delete me", "/adir/kid.txt": "k" });
    v.unlinkSync("/target.txt");
    expect(v.existsSync("/target.txt")).toBe(false);
    expect(codeOf(() => v.unlinkSync("/adir"))).toBe("EPERM");
  });

  test("rmdirSync removes empty directories only", () => {
    /** Verifies: MFS-FIL-015 */
    const v = Volume.fromJSON({ "/full/occupant.txt": "here", "/bare": null });
    v.rmdirSync("/bare");
    expect(v.existsSync("/bare")).toBe(false);
    expect(codeOf(() => v.rmdirSync("/full"))).toBe("ENOTEMPTY");
    expect(codeOf(() => v.rmdirSync("/full/occupant.txt"))).toBe("ENOTDIR");
  });

  test("rmSync with recursive removes a whole subtree", () => {
    /** Verifies: MFS-FIL-016 */
    const v = Volume.fromJSON({
      "/grove/a/b/leaf.txt": "deep",
      "/grove/top.txt": "shallow",
    });
    expect(v.readFileSync("/grove/a/b/leaf.txt", "utf8")).toBe("deep");
    v.rmSync("/grove", { recursive: true });
    expect(v.existsSync("/grove")).toBe(false);
    expect(v.toJSON()).toEqual({});
  });

  test("rmSync guards: missing path, force, and directory without recursive", () => {
    /** Verifies: MFS-FIL-016 */
    const v = Volume.fromJSON({ "/roomy": null });
    expect(codeOf(() => v.rmSync("/phantom"))).toBe("ENOENT");
    expect(() => v.rmSync("/phantom", { force: true })).not.toThrow();
    expect(codeOf(() => v.rmSync("/roomy"))).toBe("ERR_FS_EISDIR");
  });

  test("renameSync replaces destinations and rejects missing endpoints", () => {
    /** Verifies: MFS-FIL-017 */
    const v = Volume.fromJSON({ "/draft.txt": "v2 text", "/final.txt": "v1 text" });
    v.renameSync("/draft.txt", "/final.txt");
    expect(v.existsSync("/draft.txt")).toBe(false);
    expect(v.readFileSync("/final.txt", "utf8")).toBe("v2 text");
    expect(codeOf(() => v.renameSync("/unreal.txt", "/x.txt"))).toBe("ENOENT");
    expect(codeOf(() => v.renameSync("/final.txt", "/no-parent/y.txt"))).toBe("ENOENT");
  });

  test("renameSync moves a directory subtree and preserves node identity", () => {
    /** Verifies: MFS-FIL-017 */
    const v = Volume.fromJSON({ "/old-home/deep/file.txt": "settled" });
    const inoBefore = v.statSync("/old-home/deep/file.txt").ino;
    v.renameSync("/old-home", "/new-home");
    expect(v.existsSync("/old-home")).toBe(false);
    expect(v.readFileSync("/new-home/deep/file.txt", "utf8")).toBe("settled");
    expect(v.statSync("/new-home/deep/file.txt").ino).toBe(inoBefore);
  });

  test("copyFileSync copies content into a default-mode node and honors COPYFILE_EXCL", () => {
    /** Verifies: MFS-FIL-018 */
    const v = Volume.fromJSON({ "/master.txt": "authoritative" });
    v.chmodSync("/master.txt", 0o600);
    v.copyFileSync("/master.txt", "/duplicate.txt");
    expect(v.readFileSync("/duplicate.txt", "utf8")).toBe("authoritative");
    expect(v.statSync("/duplicate.txt").mode & 0o777).toBe(0o666);
    expect(
      codeOf(() => v.copyFileSync("/master.txt", "/duplicate.txt", constants.COPYFILE_EXCL)),
    ).toBe("EEXIST");
  });

  test("cpSync recursive performs a deep copy of a tree", () => {
    /** Verifies: MFS-FIL-019 */
    const v = Volume.fromJSON({ "/plant/root/stem.txt": "green" });
    v.cpSync("/plant", "/clone", { recursive: true });
    expect(v.readFileSync("/clone/root/stem.txt", "utf8")).toBe("green");
    v.writeFileSync("/plant/root/stem.txt", "mutated");
    expect(v.readFileSync("/clone/root/stem.txt", "utf8")).toBe("green");
  });

  test("cpSync guards: directory without recursive and errorOnExist", () => {
    /** Verifies: MFS-FIL-019 */
    const v = Volume.fromJSON({ "/from/a.txt": "1", "/to/a.txt": "old" });
    expect(codeOf(() => v.cpSync("/from", "/elsewhere"))).toBe("EISDIR");
    expect(
      codeOf(() =>
        v.cpSync("/from", "/to", { recursive: true, force: false, errorOnExist: true }),
      ),
    ).toBe("EEXIST");
    v.cpSync("/from", "/to", { recursive: true });
    expect(v.readFileSync("/to/a.txt", "utf8")).toBe("1");
  });

  test("truncateSync shrinks and zero-extends file content", () => {
    /** Verifies: MFS-FIL-020 */
    const v = Volume.fromJSON({ "/sized.txt": "abcdefgh" });
    v.truncateSync("/sized.txt", 3);
    expect(v.readFileSync("/sized.txt", "utf8")).toBe("abc");
    v.truncateSync("/sized.txt", 6);
    expect([...(v.readFileSync("/sized.txt") as Buffer)]).toEqual([97, 98, 99, 0, 0, 0]);
  });

  test("existence checks report booleans and access raises ENOENT when missing", () => {
    /** Verifies: MFS-FIL-021, MFS-FIL-022 */
    const v = Volume.fromJSON({ "/is-here.txt": "y" });
    expect(v.existsSync("/is-here.txt")).toBe(true);
    expect(v.existsSync("/is-not-here.txt")).toBe(false);
    expect(v.accessSync("/is-here.txt")).toBeUndefined();
    expect(codeOf(() => v.accessSync("/is-not-here.txt"))).toBe("ENOENT");
  });
});

// ---------------------------------------------------------------------------
describe("metadata and permissions", () => {
  test("stats expose size, kind predicates, identity and timestamps", () => {
    /** Verifies: MFS-MET-001 */
    const v = Volume.fromJSON({ "/facts.txt": "seven bytes!" });
    const st = v.statSync("/facts.txt");
    expect(st.isFile()).toBe(true);
    expect(st.isDirectory()).toBe(false);
    expect(st.isSymbolicLink()).toBe(false);
    expect(st.size).toBe(12);
    expect(typeof st.ino).toBe("number");
    expect(st.nlink).toBe(1);
    expect(st.mtime instanceof Date).toBe(true);
    expect(typeof st.mtimeMs).toBe("number");
    expect(st.atime instanceof Date).toBe(true);
    expect(st.ctime instanceof Date).toBe(true);
    const sd = v.statSync("/");
    expect(sd.isDirectory()).toBe(true);
    expect(sd.isFile()).toBe(false);
  });

  test("fstatSync reports on an open descriptor", () => {
    /** Verifies: MFS-MET-002 */
    const v = Volume.fromJSON({ "/fd-view.txt": "handle me" });
    const fd = v.openSync("/fd-view.txt", "r");
    expect(v.fstatSync(fd).size).toBe(9);
    expect(v.fstatSync(fd).isFile()).toBe(true);
    v.closeSync(fd);
  });

  test("stat options: bigint fields and throwIfNoEntry", () => {
    /** Verifies: MFS-MET-003, MFS-MET-004 */
    const v = Volume.fromJSON({ "/big.txt": "big" });
    const st = v.statSync("/big.txt", { bigint: true });
    expect(typeof st.size).toBe("bigint");
    expect(v.statSync("/void", { throwIfNoEntry: false })).toBeUndefined();
    expect(codeOf(() => v.statSync("/void"))).toBe("ENOENT");
  });

  test("size tracks writes, appends and truncation", () => {
    /** Verifies: MFS-MET-005 */
    const v = new Volume();
    v.writeFileSync("/meter.txt", "12345");
    expect(v.statSync("/meter.txt").size).toBe(5);
    v.appendFileSync("/meter.txt", "678");
    expect(v.statSync("/meter.txt").size).toBe(8);
    v.truncateSync("/meter.txt", 2);
    expect(v.statSync("/meter.txt").size).toBe(2);
  });

  test("created nodes carry the default permission bits", () => {
    /** Verifies: MFS-MET-006 */
    const v = new Volume();
    v.writeFileSync("/plain.txt", "p");
    v.mkdirSync("/plaindir");
    expect(v.statSync("/plain.txt").mode & 0o777).toBe(0o666);
    expect(v.statSync("/plaindir").mode & 0o777).toBe(0o777);
  });

  test("explicit mode options are honored on creation", () => {
    /** Verifies: MFS-MET-006 */
    const v = new Volume();
    v.mkdirSync("/locked", { mode: 0o700 });
    expect(v.statSync("/locked").mode & 0o777).toBe(0o700);
    const fd = v.openSync("/private.txt", "w", 0o640);
    v.closeSync(fd);
    expect(v.statSync("/private.txt").mode & 0o777).toBe(0o640);
  });

  test("chmod feeds accessSync capability checks", () => {
    /** Verifies: MFS-MET-007, MFS-MET-008 */
    const v = Volume.fromJSON({ "/guarded.txt": "g" });
    v.chmodSync("/guarded.txt", 0o444);
    expect(v.statSync("/guarded.txt").mode & 0o777).toBe(0o444);
    expect(v.accessSync("/guarded.txt", F_OK)).toBeUndefined();
    expect(v.accessSync("/guarded.txt", R_OK)).toBeUndefined();
    expect(codeOf(() => v.accessSync("/guarded.txt", W_OK))).toBe("EACCES");
    v.chmodSync("/guarded.txt", 0o000);
    expect(codeOf(() => v.accessSync("/guarded.txt", R_OK))).toBe("EACCES");
  });

  test("reading a mode-denied file raises EACCES", () => {
    /** Verifies: MFS-MET-009 */
    const v = Volume.fromJSON({ "/sealed.txt": "secret" });
    v.chmodSync("/sealed.txt", 0o000);
    expect(codeOf(() => v.readFileSync("/sealed.txt"))).toBe("EACCES");
    v.chmodSync("/sealed.txt", 0o644);
    expect(v.readFileSync("/sealed.txt", "utf8")).toBe("secret");
  });

  test("utimesSync and futimesSync store the given times", () => {
    /** Verifies: MFS-MET-010 */
    const v = Volume.fromJSON({ "/aged.txt": "old" });
    v.utimesSync("/aged.txt", new Date(1400000000000), new Date(1400000009000));
    expect(v.statSync("/aged.txt").atimeMs).toBe(1400000000000);
    expect(v.statSync("/aged.txt").mtimeMs).toBe(1400000009000);
    v.utimesSync("/aged.txt", 1450000000, 1450000005);
    expect(v.statSync("/aged.txt").atimeMs).toBe(1450000000000);
    expect(v.statSync("/aged.txt").mtimeMs).toBe(1450000005000);
    const fd = v.openSync("/aged.txt", "r+");
    v.futimesSync(fd, 1460000000, 1460000001);
    v.closeSync(fd);
    expect(v.statSync("/aged.txt").mtimeMs).toBe(1460000001000);
  });
});

// ---------------------------------------------------------------------------
describe("links and path resolution", () => {
  test("symlinkSync stores a target returned verbatim by readlinkSync", () => {
    /** Verifies: MFS-LNK-001 */
    const v = Volume.fromJSON({ "/anchor.txt": "solid" });
    v.symlinkSync("/anchor.txt", "/pointer");
    expect(v.readlinkSync("/pointer")).toBe("/anchor.txt");
    expect(v.readFileSync("/pointer", "utf8")).toBe("solid");
  });

  test("links resolve at intermediate path components", () => {
    /** Verifies: MFS-LNK-002 */
    const v = Volume.fromJSON({ "/actual/inside.txt": "found" });
    v.symlinkSync("/actual", "/alias-dir");
    expect(v.readFileSync("/alias-dir/inside.txt", "utf8")).toBe("found");
    expect(v.realpathSync("/alias-dir/inside.txt")).toBe("/actual/inside.txt");
  });

  test("statSync follows links while lstatSync reports the link node", () => {
    /** Verifies: MFS-LNK-003 */
    const v = Volume.fromJSON({ "/subject.txt": "watched" });
    v.symlinkSync("/subject.txt", "/watcher");
    expect(v.statSync("/watcher").isFile()).toBe(true);
    expect(v.statSync("/watcher").isSymbolicLink()).toBe(false);
    expect(v.lstatSync("/watcher").isSymbolicLink()).toBe(true);
  });

  test("realpathSync follows chains of links transitively", () => {
    /** Verifies: MFS-LNK-004 */
    const v = Volume.fromJSON({ "/base.txt": "bottom" });
    v.symlinkSync("/base.txt", "/hop1");
    v.symlinkSync("/hop1", "/hop2");
    expect(v.realpathSync("/hop2")).toBe("/base.txt");
    expect(v.readFileSync("/hop2", "utf8")).toBe("bottom");
  });

  test("readlinkSync on a regular file raises EINVAL", () => {
    /** Verifies: MFS-LNK-005 */
    const v = Volume.fromJSON({ "/not-a-link.txt": "n" });
    expect(codeOf(() => v.readlinkSync("/not-a-link.txt"))).toBe("EINVAL");
  });

  test("a dangling link hides from exists until its target appears", () => {
    /** Verifies: MFS-LNK-006, MFS-LNK-007 */
    const v = new Volume();
    v.symlinkSync("/late.txt", "/waiting");
    expect(v.existsSync("/waiting")).toBe(false);
    expect(v.lstatSync("/waiting").isSymbolicLink()).toBe(true);
    expect(codeOf(() => v.readFileSync("/waiting"))).toBe("ENOENT");
    expect(codeOf(() => v.realpathSync("/waiting"))).toBe("ENOENT");
    v.writeFileSync("/late.txt", "arrived");
    expect(v.existsSync("/waiting")).toBe(true);
    expect(v.readFileSync("/waiting", "utf8")).toBe("arrived");
  });

  test("unlinking a symlink leaves its target intact", () => {
    /** Verifies: MFS-LNK-008 */
    const v = Volume.fromJSON({ "/kept.txt": "still here" });
    v.symlinkSync("/kept.txt", "/discard");
    v.unlinkSync("/discard");
    expect(v.existsSync("/discard")).toBe(false);
    expect(v.readFileSync("/kept.txt", "utf8")).toBe("still here");
  });

  test("hard links share identity and content in both directions", () => {
    /** Verifies: MFS-LNK-009 */
    const v = Volume.fromJSON({ "/first-name.txt": "one body" });
    v.linkSync("/first-name.txt", "/second-name.txt");
    expect(v.statSync("/first-name.txt").nlink).toBe(2);
    expect(v.statSync("/second-name.txt").ino).toBe(v.statSync("/first-name.txt").ino);
    v.writeFileSync("/second-name.txt", "rewritten");
    expect(v.readFileSync("/first-name.txt", "utf8")).toBe("rewritten");
    v.unlinkSync("/first-name.txt");
    expect(v.readFileSync("/second-name.txt", "utf8")).toBe("rewritten");
    expect(v.statSync("/second-name.txt").nlink).toBe(1);
  });

  test("linkSync rejects an existing destination and a missing source", () => {
    /** Verifies: MFS-LNK-010 */
    const v = Volume.fromJSON({ "/exists-a.txt": "a", "/exists-b.txt": "b" });
    expect(codeOf(() => v.linkSync("/exists-a.txt", "/exists-b.txt"))).toBe("EEXIST");
    expect(codeOf(() => v.linkSync("/missing-src.txt", "/new-name.txt"))).toBe("ENOENT");
  });
});

// ---------------------------------------------------------------------------
describe("file descriptors", () => {
  test("openSync returns distinct numeric descriptors", () => {
    /** Verifies: MFS-FD-001 */
    const v = Volume.fromJSON({ "/multi.txt": "shared" });
    const fd1 = v.openSync("/multi.txt", "r");
    const fd2 = v.openSync("/multi.txt", "r");
    expect(typeof fd1).toBe("number");
    expect(typeof fd2).toBe("number");
    expect(fd1).not.toBe(fd2);
    v.closeSync(fd1);
    v.closeSync(fd2);
  });

  test("open flag guards: r and r+ need the file, wx refuses it, w truncates", () => {
    /** Verifies: MFS-FD-002 */
    const v = Volume.fromJSON({ "/notes.txt": "long existing body" });
    expect(codeOf(() => v.openSync("/void.txt", "r"))).toBe("ENOENT");
    expect(codeOf(() => v.openSync("/void.txt", "r+"))).toBe("ENOENT");
    expect(codeOf(() => v.openSync("/notes.txt", "wx"))).toBe("EEXIST");
    const fd = v.openSync("/notes.txt", "w");
    expect(v.fstatSync(fd).size).toBe(0);
    v.closeSync(fd);
  });

  test("flag a appends every write at the end", () => {
    /** Verifies: MFS-FD-002 */
    const v = Volume.fromJSON({ "/tail.txt": "head-" });
    const fd = v.openSync("/tail.txt", "a");
    v.writeSync(fd, "tail1-");
    v.writeSync(fd, "tail2");
    v.closeSync(fd);
    expect(v.readFileSync("/tail.txt", "utf8")).toBe("head-tail1-tail2");
  });

  test("readSync copies bytes at an absolute position and reports the count", () => {
    /** Verifies: MFS-FD-003 */
    const v = Volume.fromJSON({ "/window.txt": "ABCDEFGHIJ" });
    const fd = v.openSync("/window.txt", "r");
    const buf = Buffer.alloc(4);
    const n = v.readSync(fd, buf, 0, 4, 3);
    expect(n).toBe(4);
    expect(buf.toString()).toBe("DEFG");
    v.closeSync(fd);
  });

  test("null-position reads advance the descriptor position sequentially", () => {
    /** Verifies: MFS-FD-003 */
    const v = Volume.fromJSON({ "/walk.txt": "stepwise" });
    const fd = v.openSync("/walk.txt", "r");
    const b1 = Buffer.alloc(4);
    const b2 = Buffer.alloc(4);
    v.readSync(fd, b1, 0, 4, null as any);
    v.readSync(fd, b2, 0, 4, null as any);
    expect(b1.toString()).toBe("step");
    expect(b2.toString()).toBe("wise");
    v.closeSync(fd);
  });

  test("writeSync reports bytes written and overwrites at a position", () => {
    /** Verifies: MFS-FD-004 */
    const v = new Volume();
    const fd = v.openSync("/patch.txt", "w+");
    expect(v.writeSync(fd, "0123456789")).toBe(10);
    v.writeSync(fd, "XY", 4);
    v.closeSync(fd);
    expect(v.readFileSync("/patch.txt", "utf8")).toBe("0123XY6789");
  });

  test("ftruncateSync truncates through the descriptor", () => {
    /** Verifies: MFS-FD-005 */
    const v = Volume.fromJSON({ "/cut.txt": "keep-drop" });
    const fd = v.openSync("/cut.txt", "r+");
    v.ftruncateSync(fd, 4);
    v.closeSync(fd);
    expect(v.readFileSync("/cut.txt", "utf8")).toBe("keep");
  });

  test("descriptor writes are immediately visible to path reads", () => {
    /** Verifies: MFS-FD-006 */
    const v = new Volume();
    const fd = v.openSync("/live.txt", "w");
    v.writeSync(fd, "before close");
    expect(v.readFileSync("/live.txt", "utf8")).toBe("before close");
    v.closeSync(fd);
  });

  test("stale descriptors raise EBADF everywhere", () => {
    /** Verifies: MFS-FD-007 */
    const v = Volume.fromJSON({ "/gone-fd.txt": "x" });
    const fd = v.openSync("/gone-fd.txt", "r");
    v.closeSync(fd);
    expect(codeOf(() => v.readSync(fd, Buffer.alloc(1), 0, 1, 0))).toBe("EBADF");
    expect(codeOf(() => v.writeSync(fd, "y"))).toBe("EBADF");
    expect(codeOf(() => v.closeSync(fd))).toBe("EBADF");
  });
});

// ---------------------------------------------------------------------------
describe("callbacks, promises, and streams", () => {
  test("callbacks deliver values on success and codes on failure", async () => {
    /** Verifies: MFS-ASY-001 */
    const v = Volume.fromJSON({ "/cb-read.txt": "callback value" });
    const [err, data] = await new Promise<[unknown, unknown]>((resolve) => {
      v.readFile("/cb-read.txt", "utf8", (e, d) => resolve([e, d]));
    });
    expect(err).toBeNull();
    expect(data).toBe("callback value");
    const missErr = await new Promise<any>((resolve) => {
      v.readFile("/cb-miss.txt", (e) => resolve(e));
    });
    expect(missErr.code).toBe("ENOENT");
  });

  test("callback writes and mkdirs mutate the tree", async () => {
    /** Verifies: MFS-ASY-001 */
    const v = new Volume();
    await new Promise<void>((resolve, reject) => {
      v.mkdir("/async-dir", (e) => (e ? reject(e) : resolve()));
    });
    await new Promise<void>((resolve, reject) => {
      v.writeFile("/async-dir/made.txt", "by callback", (e) => (e ? reject(e) : resolve()));
    });
    expect(v.readFileSync("/async-dir/made.txt", "utf8")).toBe("by callback");
  });

  test("exists delivers a single boolean to its callback", async () => {
    /** Verifies: MFS-ASY-002 */
    const v = Volume.fromJSON({ "/here.txt": "h" });
    const yes = await new Promise<boolean>((resolve) => v.exists("/here.txt", resolve));
    const no = await new Promise<boolean>((resolve) => v.exists("/nowhere.txt", resolve));
    expect(yes).toBe(true);
    expect(no).toBe(false);
  });

  test("the promises API mirrors operations and rejection codes", async () => {
    /** Verifies: MFS-ASY-003 */
    const v = new Volume();
    await v.promises.mkdir("/pr/depth", { recursive: true });
    await v.promises.writeFile("/pr/depth/leaf.txt", "promised leaf");
    expect(await v.promises.readFile("/pr/depth/leaf.txt", "utf8")).toBe("promised leaf");
    expect(await v.promises.readdir("/pr")).toEqual(["depth"]);
    await expect(v.promises.readFile("/pr-miss.txt")).rejects.toMatchObject({
      code: "ENOENT",
    });
  });

  test("a FileHandle reads, stats and closes", async () => {
    /** Verifies: MFS-ASY-004 */
    const v = Volume.fromJSON({ "/handle.txt": "held content" });
    const fh = await v.promises.open("/handle.txt", "r");
    expect(typeof fh.fd).toBe("number");
    expect(String(await fh.readFile("utf8" as any))).toBe("held content");
    const st = await fh.stat();
    expect(st.size).toBe(12);
    await fh.close();
  });

  test("FileHandle writes report bytesWritten and store the bytes", async () => {
    /** Verifies: MFS-ASY-004 */
    const v = new Volume();
    const fh = await v.promises.open("/hw.txt", "w");
    const res = await fh.write(Buffer.from("handle bytes"));
    expect(res.bytesWritten).toBe(12);
    await fh.close();
    expect(v.readFileSync("/hw.txt", "utf8")).toBe("handle bytes");
    const fh2 = await v.promises.open("/hw2.txt", "w");
    await fh2.writeFile("via handle writeFile");
    await fh2.close();
    expect(v.readFileSync("/hw2.txt", "utf8")).toBe("via handle writeFile");
  });

  test("write streams persist on finish and read streams honor encoding", async () => {
    /** Verifies: MFS-ASY-005 */
    const v = new Volume();
    const ws = v.createWriteStream("/streamed.txt");
    ws.write("chunk-one|");
    ws.write("chunk-two");
    ws.end();
    await new Promise<void>((resolve) => ws.on("finish", () => resolve()));
    expect(v.readFileSync("/streamed.txt", "utf8")).toBe("chunk-one|chunk-two");
    const rs = v.createReadStream("/streamed.txt", { encoding: "utf8" } as any);
    let acc = "";
    rs.on("data", (c: any) => (acc += c));
    await new Promise<void>((resolve) => rs.on("end", () => resolve()));
    expect(acc).toBe("chunk-one|chunk-two");
  });

  test("a read stream for a missing path emits ENOENT", async () => {
    /** Verifies: MFS-ASY-006 */
    const v = new Volume();
    const rs = v.createReadStream("/no-stream.txt");
    const code = await new Promise<string>((resolve) => {
      rs.on("error", (e: any) => resolve(e.code));
      rs.on("data", () => {});
    });
    expect(code).toBe("ENOENT");
  });
});

// ---------------------------------------------------------------------------
describe("error object shape", () => {
  test("failures carry code and path properties", () => {
    /** Verifies: MFS-ERR-001, MFS-ERR-002 */
    const v = new Volume();
    try {
      v.readFileSync("/absent-and-noted.txt");
      expect.unreachable("readFileSync should have thrown");
    } catch (e: any) {
      expect(e).toBeInstanceOf(Error);
      expect(e.code).toBe("ENOENT");
      expect(e.path).toBe("/absent-and-noted.txt");
    }
  });
});
