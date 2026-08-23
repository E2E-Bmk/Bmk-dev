import { describe, expect, test } from "vitest";
import { readChangesets } from "@changesets/read";
import { writeChangeset } from "@changesets/write";
import { enterPre, exitPre, readPreState } from "@changesets/pre";
import { assembleReleasePlan } from "@changesets/assemble-release-plan";
import { applyReleasePlan } from "@changesets/apply-release-plan";
import { defaultConfig } from "@changesets/config";
import { PreEnterButInPreModeError, PreExitButNotInPreModeError } from "@changesets/errors";
import { getDependentsGraph } from "@changesets/get-dependents-graph";
import { mkdtemp, mkdir, readFile, writeFile, access } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const makePkg = (root: string, name: string, version = "1.0.0", extra: Record<string, unknown> = {}) => ({
  dir: path.join(root, name),
  packageJson: { name, version, ...extra },
});
const makePackages = (root: string, items: any[], rootPackage?: any) => ({ rootDir: root, packages: items, rootPackage, tool: { type: "pnpm" } }) as any;
const cfg = () => ({ ...defaultConfig, changelog: false, format: false });

test("write then read preserves changeset projections", async () => {
  /** Verifies: CHG-INV-001, CHG-DOC-014 */
  const root = await mkdtemp(path.join(tmpdir(), "changesets-flow-"));
  const id = await writeChangeset({ summary: "summary", releases: [{ name: "a", type: "minor" }] }, root, { format: false });
  const found = await readChangesets(root);
  expect(found).toEqual([{ id, summary: "summary", releases: [{ name: "a", type: "minor" }] }]);
});
test("read filters helper markdown files", async () => {
  /** Verifies: CHG-DOC-015 */
  const root = await mkdtemp(path.join(tmpdir(), "changesets-filter-"));
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(root, ".changeset", "README.md"), "readme");
  await writeFile(path.join(root, ".changeset", "AGENTS.md"), "agents");
  await writeFile(path.join(root, ".changeset", "real.md"), "---\na: patch\n---\nreal");
  expect((await readChangesets(root)).map((x) => x.id)).toEqual(["real"]);
});
test("read rejects missing changeset directory", async () => {
  /** Verifies: CHG-DOC-017, CHG-ERR-002 */
  await expect(readChangesets(await mkdtemp(path.join(tmpdir(), "changesets-missing-")))).rejects.toBeInstanceOf(Error);
});
test("read includes pre directory with prefixed id", async () => {
  /** Verifies: CHG-DOC-014, CHG-INV-008 */
  const root = await mkdtemp(path.join(tmpdir(), "changesets-pre-read-"));
  await mkdir(path.join(root, ".changeset", "pre"), { recursive: true });
  await writeFile(path.join(root, ".changeset", "pre", "x.md"), "---\na: patch\n---\npre");
  expect((await readChangesets(root))[0].id).toBe("pre/x");
});
test("dependents graph includes root and reverse edge", () => {
  /** Verifies: CHG-PLAN-001, CHG-PLAN-002, CHG-INV-004 */
  const root = "/tmp/graph";
  const a = makePkg(root, "a");
  const b = makePkg(root, "b", "1.0.0", { dependencies: { a: "^1.0.0" } });
  const graph = getDependentsGraph(makePackages(root, [a, b], makePkg(root, "root")));
  expect(graph.has("root")).toBe(true);
  expect(graph.get("a")).toContain("b");
});
test("dependents graph without root is empty", () => {
  /** Verifies: CHG-PLAN-002 */
  const root = "/tmp/graph-empty";
  const a = makePkg(root, "a");
  expect(getDependentsGraph(makePackages(root, [a])).size).toBe(0);
});
test("assembly consolidates multiple changesets", () => {
  /** Verifies: CHG-PLAN-004, CHG-PLAN-005, CHG-PLAN-006, CHG-INV-003 */
  const root = "/tmp/plan";
  const a = makePkg(root, "a");
  const plan = assembleReleasePlan([
    { id: "one", summary: "one", releases: [{ name: "a", type: "patch" }] },
    { id: "two", summary: "two", releases: [{ name: "a", type: "minor" }] },
  ], makePackages(root, [a], makePkg(root, "root")), cfg(), undefined);
  expect(plan.releases).toHaveLength(1);
  expect(plan.releases[0]).toMatchObject({ name: "a", type: "minor", oldVersion: "1.0.0", newVersion: "1.1.0" });
});
test("assembly rejects unknown package", () => {
  /** Verifies: CHG-PLAN-007, CHG-ERR-005 */
  expect(() => assembleReleasePlan([{ id: "x", summary: "x", releases: [{ name: "missing", type: "patch" }] }], makePackages("/tmp/x", [makePkg("/tmp/x", "a")], makePkg("/tmp/x", "root")), cfg(), undefined)).toThrow(Error);
});
test("assembly propagates dependent release", () => {
  /** Verifies: CHG-PLAN-011, CHG-INV-004 */
  const root = "/tmp/deps";
  const a = makePkg(root, "a");
  const b = makePkg(root, "b", "1.0.0", { dependencies: { a: "^1.0.0" } });
  const plan = assembleReleasePlan([{ id: "x", summary: "x", releases: [{ name: "a", type: "major" }] }], makePackages(root, [a, b], makePkg(root, "root")), cfg(), undefined);
  expect(plan.releases.map((r) => r.name)).toContain("b");
});
test("pre lifecycle enters and reads state", async () => {
  /** Verifies: CHG-PRE-001, CHG-PRE-002, CHG-INV-006 */
  const root = await mkdtemp(path.join(tmpdir(), "pre-enter-"));
  await writeFile(path.join(root, "package.json"), JSON.stringify({ name: "root", version: "1.0.0", private: true }));
  await enterPre(root, "next");
  expect(await readPreState(root)).toEqual({ mode: "pre", tag: "next" });
});
test("pre lifecycle rejects repeated enter", async () => {
  /** Verifies: CHG-PRE-002, CHG-PRE-005, CHG-ERR-007 */
  const root = await mkdtemp(path.join(tmpdir(), "pre-repeat-"));
  await writeFile(path.join(root, "package.json"), JSON.stringify({ name: "root", version: "1.0.0", private: true }));
  await enterPre(root, "next");
  await expect(enterPre(root, "other")).rejects.toBeInstanceOf(PreEnterButInPreModeError);
});
test("pre lifecycle exits and reads exit state", async () => {
  /** Verifies: CHG-PRE-003, CHG-INV-006 */
  const root = await mkdtemp(path.join(tmpdir(), "pre-exit-"));
  await writeFile(path.join(root, "package.json"), JSON.stringify({ name: "root", version: "1.0.0", private: true }));
  await enterPre(root, "next");
  await exitPre(root);
  expect(await readPreState(root)).toMatchObject({ mode: "exit", tag: "next" });
});
test("pre exit rejects without state", async () => {
  /** Verifies: CHG-PRE-003, CHG-PRE-005, CHG-ERR-008 */
  await expect(exitPre(await mkdtemp(path.join(tmpdir(), "pre-none-")))).rejects.toBeInstanceOf(PreExitButNotInPreModeError);
});
test("apply plan updates package and removes changeset", async () => {
  /** Verifies: CHG-PRE-006, CHG-PRE-007, CHG-PRE-009, CHG-PRE-012, CHG-INV-007 */
  const root = await mkdtemp(path.join(tmpdir(), "apply-"));
  const pkg = makePkg(root, "a");
  await mkdir(pkg.dir, { recursive: true });
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(pkg.dir, "package.json"), JSON.stringify({ name: "a", version: "1.0.0", marker: true }));
  await writeFile(path.join(root, ".changeset", "x.md"), "---\na: patch\n---\nfix");
  const plan = assembleReleasePlan([{ id: "x", summary: "fix", releases: [{ name: "a", type: "patch" }] }], makePackages(root, [pkg], makePkg(root, "root")), cfg(), undefined);
  const touched = await applyReleasePlan(plan, makePackages(root, [pkg], makePkg(root, "root")), cfg());
  expect(JSON.parse(await readFile(path.join(pkg.dir, "package.json"), "utf8"))).toMatchObject({ version: "1.0.1", marker: true });
  await expect(access(path.join(root, ".changeset", "x.md"))).rejects.toBeInstanceOf(Error);
  expect(touched).toContain(path.join(pkg.dir, "package.json"));
});
test("apply plan rejects missing package before writing", async () => {
  /** Verifies: CHG-PRE-011, CHG-ERR-011 */
  const root = await mkdtemp(path.join(tmpdir(), "apply-missing-"));
  const plan = { changesets: [], releases: [{ name: "missing", type: "patch", oldVersion: "1.0.0", newVersion: "1.0.1", changesets: [] }], preState: undefined } as any;
  await expect(applyReleasePlan(plan, makePackages(root, [], makePkg(root, "root")), cfg())).rejects.toBeInstanceOf(Error);
});
test("apply pre plan moves changeset into pre directory", async () => {
  /** Verifies: CHG-PRE-009, CHG-INV-008 */
  const root = await mkdtemp(path.join(tmpdir(), "apply-pre-"));
  const pkg = makePkg(root, "a");
  await mkdir(pkg.dir, { recursive: true });
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(pkg.dir, "package.json"), JSON.stringify({ name: "a", version: "1.0.0" }));
  await writeFile(path.join(root, ".changeset", "x.md"), "---\na: patch\n---\nfix");
  const plan = assembleReleasePlan([{ id: "x", summary: "fix", releases: [{ name: "a", type: "patch" }] }], makePackages(root, [pkg], makePkg(root, "root")), cfg(), { mode: "pre", tag: "next" });
  await applyReleasePlan(plan, makePackages(root, [pkg], makePkg(root, "root")), cfg());
  expect(await readFile(path.join(root, ".changeset", "pre", "x.md"), "utf8")).toContain("fix");
});
test("snapshot plan produces tagged version", () => {
  /** Verifies: CHG-PLAN-012 */
  const root = "/tmp/snapshot";
  const a = makePkg(root, "a");
  const config = { ...cfg(), snapshot: { useCalculatedVersion: false, prereleaseTemplate: "{tag}-{commit-short}" } };
  const plan = assembleReleasePlan([{ id: "x", summary: "x", releases: [{ name: "a", type: "patch" }] }], makePackages(root, [a], makePkg(root, "root")), config as any, undefined, { tag: "canary", commit: "abcdefghi" });
  expect(plan.releases[0].newVersion).toBe("0.0.0-canary-abcdefg");
});
test("pre state filters pre-prefixed changesets", () => {
  /** Verifies: CHG-PLAN-009 */
  const root = "/tmp/pre-filter";
  const a = makePkg(root, "a");
  const plan = assembleReleasePlan([{ id: "pre/x", summary: "x", releases: [{ name: "a", type: "patch" }] }, { id: "x", summary: "y", releases: [{ name: "a", type: "minor" }] }], makePackages(root, [a], makePkg(root, "root")), cfg(), { mode: "pre", tag: "next" });
  expect(plan.changesets.map((x) => x.id)).toEqual(["x"]);
});
test("fixed group converges releases", () => {
  /** Verifies: CHG-PLAN-010, CHG-INV-005 */
  const root = "/tmp/fixed";
  const a = makePkg(root, "a");
  const b = makePkg(root, "b");
  const config = { ...cfg(), fixed: [["a", "b"]] };
  const plan = assembleReleasePlan([{ id: "x", summary: "x", releases: [{ name: "a", type: "minor" }] }], makePackages(root, [a, b], makePkg(root, "root")), config as any, undefined);
  expect(plan.releases.map((x) => x.name).sort()).toEqual(["a", "b"]);
});
test("named and default behavior is cross-view consistent", async () => {
  /** Verifies: CHG-INV-009, CHG-STATE-002, CHG-STATE-005 */
  const root = await mkdtemp(path.join(tmpdir(), "cross-view-"));
  const id = await writeChangeset({ summary: "cross", releases: [{ name: "a", type: "patch" }] }, root, { format: false });
  expect((await readChangesets(root)).find((x) => x.id === id)?.summary).toBe("cross");
});
test("assembly preserves none version", () => {
  /** Verifies: CHG-PLAN-006, CHG-INV-003 */
  const root = "/tmp/none-plan";
  const a = makePkg(root, "a");
  const plan = assembleReleasePlan([{ id: "x", summary: "x", releases: [{ name: "a", type: "none" }] }], makePackages(root, [a], makePkg(root, "root")), cfg(), undefined);
  expect(plan.releases[0]).toMatchObject({ type: "none", oldVersion: "1.0.0", newVersion: "1.0.0" });
});
test("assembly rejects mixed ignored and non-ignored changeset", () => {
  /** Verifies: CHG-PLAN-008, CHG-ERR-006 */
  const root = "/tmp/mixed-plan";
  const a = makePkg(root, "a");
  const b = makePkg(root, "b");
  const config = { ...cfg(), ignore: ["b"] };
  expect(() => assembleReleasePlan([{ id: "x", summary: "x", releases: [{ name: "a", type: "patch" }, { name: "b", type: "patch" }] }], makePackages(root, [a, b], makePkg(root, "root")), config as any, undefined)).toThrow(Error);
});
test("apply plan preserves dependency range style", async () => {
  /** Verifies: CHG-PRE-007, CHG-INV-007 */
  const root = await mkdtemp(path.join(tmpdir(), "apply-range-"));
  const a = makePkg(root, "a");
  const b = makePkg(root, "b", "1.0.0", { dependencies: { a: "^1.0.0" } });
  for (const item of [a, b]) await mkdir(item.dir, { recursive: true });
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(a.dir, "package.json"), JSON.stringify(a.packageJson));
  await writeFile(path.join(b.dir, "package.json"), JSON.stringify(b.packageJson));
  await writeFile(path.join(root, ".changeset", "x.md"), "---\na: major\n---\nfix");
  const pkgs = makePackages(root, [a, b], makePkg(root, "root"));
  const plan = assembleReleasePlan([{ id: "x", summary: "fix", releases: [{ name: "a", type: "major" }] }], pkgs, cfg(), undefined);
  await applyReleasePlan(plan, pkgs, cfg());
  expect(JSON.parse(await readFile(path.join(b.dir, "package.json"), "utf8")).dependencies.a).toBe("^2.0.0");
});
test("apply exit plan removes pre state", async () => {
  /** Verifies: CHG-PRE-010, CHG-INV-007 */
  const root = await mkdtemp(path.join(tmpdir(), "apply-exit-"));
  const a = makePkg(root, "a");
  await mkdir(a.dir, { recursive: true });
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(a.dir, "package.json"), JSON.stringify(a.packageJson));
  await writeFile(path.join(root, ".changeset", "pre.json"), JSON.stringify({ mode: "exit", tag: "next" }));
  const plan = { changesets: [], releases: [], preState: { mode: "exit", tag: "next" } } as any;
  const touched = await applyReleasePlan(plan, makePackages(root, [a], makePkg(root, "root")), cfg());
  await expect(access(path.join(root, ".changeset", "pre.json"))).rejects.toBeInstanceOf(Error);
  expect(touched).toContain(path.join(root, ".changeset", "pre.json"));
});
test("pre migration moves listed changeset", async () => {
  /** Verifies: CHG-PRE-004, CHG-INV-006 */
  const root = await mkdtemp(path.join(tmpdir(), "pre-migrate-"));
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(root, ".changeset", "x.md"), "---\na: patch\n---\nx");
  await writeFile(path.join(root, ".changeset", "pre.json"), JSON.stringify({ mode: "pre", tag: "next", changesets: ["x"], initialVersions: { a: "1.0.0" } }));
  const state = await readPreState(root);
  expect(state).toEqual({ mode: "pre", tag: "next" });
  expect(await readFile(path.join(root, ".changeset", "pre", "x.md"), "utf8")).toContain("x");
});
test("assembly returns pre state projection", () => {
  /** Verifies: CHG-PLAN-004, CHG-STATE-004 */
  const root = "/tmp/pre-plan-state";
  const a = makePkg(root, "a");
  const plan = assembleReleasePlan([], makePackages(root, [a], makePkg(root, "root")), cfg(), { mode: "pre", tag: "next" });
  expect(plan.preState).toEqual({ mode: "pre", tag: "next" });
});
test("apply plan reports unique touched paths", async () => {
  /** Verifies: CHG-PRE-012, CHG-INV-007 */
  const root = await mkdtemp(path.join(tmpdir(), "apply-touched-"));
  const plan = { changesets: [], releases: [], preState: undefined } as any;
  const touched = await applyReleasePlan(plan, makePackages(root, [], makePkg(root, "root")), cfg());
  expect(new Set(touched).size).toBe(touched.length);
});
