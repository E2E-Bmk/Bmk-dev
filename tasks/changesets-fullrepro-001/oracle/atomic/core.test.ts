import { afterEach, expect, test, vi } from "vitest";
import { parseChangesetFile, default as parseDefault } from "@changesets/parse";
import { readChangesets, default as readDefault } from "@changesets/read";
import { defaultWrittenConfig, defaultConfig, validateConfig, readConfig } from "@changesets/config";
import { getVersionRangeType, default as rangeDefault } from "@changesets/get-version-range-type";
import { shouldSkipPackage } from "@changesets/should-skip-package";
import { GitError, ExitError, InternalError, PreEnterButInPreModeError, PreExitButNotInPreModeError } from "@changesets/errors";
import changelogGit from "@changesets/changelog-git";
import { prefix, error, info, log, success, warn } from "@changesets/logger";
import { chmod, mkdtemp, mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const mocks = vi.hoisted(() => ({
  changed: vi.fn(async () => [] as string[]),
}));

vi.mock("@changesets/git", () => ({
  getChangedChangesetFilesSinceRef: mocks.changed,
}));

afterEach(() => {
  vi.clearAllMocks();
});

const loadWriteModule = async () => import("@changesets/write");
const pkg = (name: string, version = "1.0.0", extra: Record<string, unknown> = {}) =>
  ({ dir: `/tmp/${name}`, packageJson: { name, version, ...extra } }) as any;
const packages = (items: any[] = [pkg("a")]) =>
  ({ rootDir: "/tmp/repo", packages: items, tool: { type: "pnpm" }, rootPackage: pkg("root") }) as any;

test("parse returns releases and trimmed summary", () => {
  /** Verifies: CHG-DOC-001, CHG-DOC-002, CHG-DOC-003, CHG-DOC-004 */
  expect(parseChangesetFile('---\n"a": minor\n"b": patch\n---\n\n  hello  \n')).toEqual({
    releases: [{ name: "a", type: "minor" }, { name: "b", type: "patch" }],
    summary: "hello",
  });
});
test("parse default matches named export", () => {
  /** Verifies: CHG-DOC-006 */
  expect(parseDefault).toBe(parseChangesetFile);
});
test("parse rejects malformed inputs", () => {
  /** Verifies: CHG-DOC-005 */
  for (const input of ["", "hello", "---\n- a\n---\nbody", "---\na: nope\n---\nbody", "---\na:\n---\nbody"]) {
    expect(() => parseChangesetFile(input)).toThrow(Error);
  }
});
test("parse accepts none releases", () => {
  /** Verifies: CHG-DOC-003, CHG-DOC-004 */
  expect(parseChangesetFile("---\na: none\n---\nkeep").releases[0].type).toBe("none");
});
test("write default matches named export", () => {
  /** Verifies: CHG-DOC-012 */
  return loadWriteModule().then(({ default: writeDefault, writeChangeset }) => {
    expect(writeDefault).toBe(writeChangeset);
  });
});
test("write creates a formatted changeset file", async () => {
  /** Verifies: CHG-DOC-007, CHG-DOC-008, CHG-DOC-009, CHG-DOC-011 */
  const { writeChangeset } = await loadWriteModule();
  const root = await mkdtemp(path.join(tmpdir(), "changesets-"));
  const id = await writeChangeset({ summary: "Ship it", releases: [{ name: "@scope/pkg", type: "patch" }] }, root, { format: false });
  const file = path.join(root, ".changeset", `${id}.md`);
  expect((await stat(file)).isFile()).toBe(true);
  expect(await readFile(file, "utf8")).toContain('"@scope/pkg": patch');
  expect(id).toMatch(/^[^/\\]+$/);
});
test("write uses the formatter when enabled", async () => {
  /** Verifies: CHG-DOC-010 */
  const { writeChangeset } = await loadWriteModule();
  const root = await mkdtemp(path.join(tmpdir(), "changesets-format-"));
  const binDir = path.join(root, "node_modules", ".bin");
  const marker = path.join(root, "formatter-called.txt");
  await mkdir(binDir, { recursive: true });
  await writeFile(path.join(root, "package.json"), JSON.stringify({ name: "fixture", private: true, packageManager: "pnpm@11.13.1" }));
  await writeFile(path.join(root, "pnpm-lock.yaml"), "");
  const pnpmBin = path.join(binDir, "pnpm");
  await writeFile(
    pnpmBin,
    `#!/usr/bin/env node
const { appendFileSync } = require("node:fs");
appendFileSync(${JSON.stringify(marker)}, process.argv.at(-1) + "\\n");
`,
  );
  await chmod(pnpmBin, 0o755);
  const oldPath = process.env.PATH;
  process.env.PATH = `${binDir}${path.delimiter}${oldPath ?? ""}`;
  try {
    await writeChangeset({ summary: "Ship it", releases: [{ name: "pkg", type: "patch" }] }, root, { format: "prettier" });
  } finally {
    process.env.PATH = oldPath;
  }
  expect(await readFile(marker, "utf8")).toMatch(/\.changeset[/\\].+\.md\n$/);
});
test("write defaults to a non-empty identifier", async () => {
  /** Verifies: CHG-DOC-007, CHG-DOC-011 */
  const { writeChangeset } = await loadWriteModule();
  const root = await mkdtemp(path.join(tmpdir(), "changesets-id-"));
  const id = await writeChangeset({ summary: "Ship it", releases: [{ name: "pkg", type: "patch" }] }, root, { format: false });
  expect(id.length).toBeGreaterThan(0);
});
test("read default matches named export", () => {
  /** Verifies: CHG-DOC-018 */
  expect(readDefault).toBe(readChangesets);
});
test("read returns live and pre changesets", async () => {
  /** Verifies: CHG-DOC-013, CHG-DOC-014 */
  const root = await mkdtemp(path.join(tmpdir(), "changesets-read-"));
  await mkdir(path.join(root, ".changeset", "pre"), { recursive: true });
  await writeFile(path.join(root, ".changeset", "a.md"), "---\na: patch\n---\na");
  await writeFile(path.join(root, ".changeset", "pre", "b.md"), "---\na: minor\n---\nb");
  expect((await readChangesets(root)).map((x) => x.id).sort()).toEqual(["a", "pre/b"]);
});
test("read applies sinceRef filtering", async () => {
  /** Verifies: CHG-DOC-016 */
  mocks.changed.mockResolvedValueOnce([".changeset/pre/b.md"]);
  const root = await mkdtemp(path.join(tmpdir(), "changesets-since-"));
  await mkdir(path.join(root, ".changeset", "pre"), { recursive: true });
  await writeFile(path.join(root, ".changeset", "a.md"), "---\na: patch\n---\na");
  await writeFile(path.join(root, ".changeset", "pre", "b.md"), "---\na: minor\n---\nb");
  expect((await readChangesets(root, "main")).map((x) => x.id)).toEqual(["pre/b"]);
});
test("default config exposes normalized defaults", () => {
  /** Verifies: CHG-CFG-001, CHG-CFG-002, CHG-CFG-008, CHG-CFG-015 */
  expect(defaultWrittenConfig.baseBranch).toBe("main");
  expect(defaultConfig.privatePackages).toEqual({ version: false, tag: false });
  expect(defaultConfig.fixed).toEqual([]);
});
test("validateConfig normalizes tuple and private package settings", () => {
  /** Verifies: CHG-CFG-003, CHG-CFG-005, CHG-CFG-006, CHG-CFG-015 */
  const result = validateConfig({ changelog: "mod", commit: true, privatePackages: true }, packages());
  expect(result.errors).toBeUndefined();
  expect(result.config?.changelog).toEqual(["mod", null]);
  expect(result.config?.commit).toEqual(["@changesets/cli/commit", { skipCI: "version" }]);
  expect(result.config?.privatePackages).toEqual({ version: true, tag: true });
});
test("validateConfig rejects invalid schema", () => {
  /** Verifies: CHG-CFG-009, CHG-CFG-010, CHG-CFG-011, CHG-CFG-014 */
  const result = validateConfig({ access: "invalid", format: "bad", updateInternalDependencies: "bad" }, packages());
  expect(result.config).toBeUndefined();
  expect(result.errors?.length).toBeGreaterThan(0);
});
test("validateConfig rejects invalid option values", () => {
  /** Verifies: CHG-CFG-009, CHG-CFG-010, CHG-CFG-013, CHG-CFG-014 */
  for (const config of [{ access: "private" }, { format: "markdown" }, { snapshot: { prereleaseTemplate: "" } }]) {
    expect(validateConfig(config, packages()).config).toBeUndefined();
  }
});
test("validateConfig normalizes private package settings", () => {
  /** Verifies: CHG-CFG-006 */
  for (const { config, expected } of [
  { name: "privatePackages true", config: { privatePackages: true }, expected: { version: true, tag: true } },
  { name: "privatePackages version only", config: { privatePackages: { version: true } }, expected: { version: true, tag: false } },
  { name: "privatePackages version false", config: { privatePackages: { version: false } }, expected: { version: false, tag: false } },
  ]) {
    expect(validateConfig(config, packages()).config?.privatePackages).toEqual(expected);
  }
});
test("validateConfig expands package globs", () => {
  /** Verifies: CHG-CFG-007 */
  const result = validateConfig({ ignore: ["@scope/*"], fixed: [["@scope/*"]] }, packages([pkg("@scope/a"), pkg("@scope/b")]));
  expect(result.config?.ignore).toEqual(["@scope/a", "@scope/b"]);
  expect(result.config?.fixed).toEqual([["@scope/a", "@scope/b"]]);
});
test("range operator returns expected prefixes", () => {
  /** Verifies: CHG-PLAN-015 */
  for (const [input, expected] of [["^1.0.0", "^"], ["~1.0.0", "~"], [">=1", ">="], ["<=1", "<="], [">1", ">"], ["1", ""]] as const) {
    expect(getVersionRangeType(input)).toBe(expected);
  }
});
test("range default matches named export", () => {
  /** Verifies: CHG-PLAN-014, CHG-PLAN-015 */
  expect(rangeDefault).toBe(getVersionRangeType);
});
test("shouldSkipPackage returns expected decisions", () => {
  /** Verifies: CHG-PLAN-016 */
  for (const { packageInfo, opts, expected } of [
    { name: "ignored package", packageInfo: pkg("a"), opts: { ignore: ["a"], allowPrivatePackages: true }, expected: true },
    { name: "private package disallowed", packageInfo: pkg("a", "1.0.0", { private: true }), opts: { ignore: [], allowPrivatePackages: false }, expected: true },
    { name: "versionless package", packageInfo: { dir: "/tmp/a", packageJson: { name: "a" } } as any, opts: { ignore: [], allowPrivatePackages: true }, expected: true },
    { name: "ordinary package", packageInfo: pkg("a"), opts: { ignore: [], allowPrivatePackages: true }, expected: false },
  ]) {
    expect(shouldSkipPackage(packageInfo, opts as any)).toBe(expected);
  }
});
test("error classes store codes", () => {
  /** Verifies: CHG-LOG-005 */
  for (const { error, code } of [
  { name: "GitError", error: new GitError(2, "git"), code: 2 },
  { name: "ExitError", error: new ExitError(3), code: 3 },
  ]) {
    expect(error).toBeInstanceOf(Error);
    expect((error as any).code).toBe(code);
  }
});
test("pre and internal error classes are constructible", () => {
  /** Verifies: CHG-LOG-006 */
  for (const error of [
    new PreEnterButInPreModeError(),
    new PreExitButNotInPreModeError(),
    new InternalError("x"),
  ]) {
    expect(error).toBeInstanceOf(Error);
  }
});
test("changelog release lines include summary and commit", async () => {
  /** Verifies: CHG-LOG-001, CHG-LOG-002 */
  for (const { input, expected } of [
    { name: "with commit", input: { id: "x", summary: "first\nsecond", releases: [], commit: "abcdefghi" }, expected: "- abcdefg: first\n  second" },
    { name: "without commit", input: { id: "x", summary: "solo", releases: [] }, expected: "- solo" },
  ]) {
    expect(await changelogGit.getReleaseLine(input as any, "patch", null)).toBe(expected);
  }
});
test("dependency changelog lines summarize updates", async () => {
  /** Verifies: CHG-LOG-003 */
  for (const { changesets, dependencies, expected } of [
    { name: "empty update list", changesets: [], dependencies: [], expected: "" },
    { name: "with updates", changesets: [{ commit: "abcdefghi" }], dependencies: [{ name: "a", newVersion: "2.0.0" }], expected: "- Updated dependencies [abcdefg]\n  - a@2.0.0" },
  ]) {
    expect(await changelogGit.getDependencyReleaseLine(changesets as any, dependencies as any, null)).toBe(expected);
  }
});
test("logger exports categories and prefix", () => {
  /** Verifies: CHG-LOG-004 */
  expect(typeof prefix).toBe("string");
  expect([error, info, log, success, warn].every((fn) => typeof fn === "function")).toBe(true);
});
test("logger forwards category calls to console", () => {
  /** Verifies: CHG-LOG-004 */
  for (const { fn, channel } of [
    { name: "error", fn: error, channel: "error" },
    { name: "info", fn: info, channel: "info" },
    { name: "log", fn: log, channel: "log" },
    { name: "success", fn: success, channel: "log" },
    { name: "warn", fn: warn, channel: "warn" },
  ]) {
    const spy = vi.spyOn(console, channel as any).mockImplementation(() => {});
    fn("value", 2);
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  }
});
test("parse preserves multiline whitespace trimming", () => {
  /** Verifies: CHG-DOC-004 */
  expect(parseChangesetFile("---\na: patch\n---\n\nline 1  \nline 2").summary).toBe("line 1  \nline 2");
});
test("parse rejects empty front matter release type", () => {
  /** Verifies: CHG-DOC-005 */
  expect(() => parseChangesetFile("---\na:\n---\nbody")).toThrow(Error);
});
test("config explicit false remains false", () => {
  /** Verifies: CHG-CFG-008, CHG-CFG-010 */
  expect(validateConfig({ format: false, changelog: false }, packages()).config?.format).toBe(false);
});
test("config snapshot template must be non-empty", () => {
  /** Verifies: CHG-CFG-013, CHG-CFG-014 */
  expect(validateConfig({ snapshot: { prereleaseTemplate: "" } }, packages()).config).toBeUndefined();
});
test("config private object fills omitted flags", () => {
  /** Verifies: CHG-CFG-006 */
  expect(validateConfig({ privatePackages: { version: false } }, packages()).config?.privatePackages).toEqual({ version: false, tag: false });
});
test("readConfig mirrors validateConfig with provided packages", async () => {
  /** Verifies: CHG-CFG-004, CHG-CFG-015 */
  const root = await mkdtemp(path.join(tmpdir(), "changesets-config-"));
  await mkdir(path.join(root, ".changeset"), { recursive: true });
  await writeFile(path.join(root, ".changeset", "config.json"), JSON.stringify({ changelog: "mod", privatePackages: true }));
  const result = await readConfig(root, { rootDir: root, packages: [pkg("a")], tool: { type: "pnpm" } } as any);
  expect(result.config?.changelog).toEqual(["mod", null]);
  expect(result.config?.privatePackages).toEqual({ version: true, tag: true });
});
test("default config commit is disabled", () => {
  /** Verifies: CHG-CFG-001, CHG-CFG-002 */
  expect(defaultConfig.commit).toBe(false);
});
test("default config changelog is a tuple", () => {
  /** Verifies: CHG-CFG-001, CHG-CFG-005 */
  expect(defaultConfig.changelog).toEqual(["@changesets/cli/changelog", null]);
});
test("none release type is preserved by parser", () => {
  /** Verifies: CHG-PLAN-006 */
  expect(parseChangesetFile("---\na: none\n---\nx").releases).toEqual([{ name: "a", type: "none" }]);
});
test("logger error category is callable", () => {
  /** Verifies: CHG-LOG-004 */
  const spy = vi.spyOn(console, "error").mockImplementation(() => {});
  error("bad");
  expect(spy).toHaveBeenCalled();
  spy.mockRestore();
});
test("parse accepts an empty release map", () => {
  /** Verifies: CHG-DOC-002, CHG-DOC-004 */
  expect(parseChangesetFile("---\n---\nsummary")).toEqual({ releases: [], summary: "summary" });
});
test("parse preserves quoted package names", () => {
  /** Verifies: CHG-DOC-003, CHG-DOC-004 */
  expect(parseChangesetFile('---\n"@scope/pkg-name": major\n---\nsummary').releases[0].name).toBe("@scope/pkg-name");
});
test("default written config supplies access policy", () => {
  /** Verifies: CHG-CFG-001, CHG-CFG-009 */
  expect(defaultWrittenConfig.access).toBe("restricted");
});
test("default config supplies dependency update policy", () => {
  /** Verifies: CHG-CFG-001, CHG-CFG-011 */
  expect(defaultConfig.updateInternalDependencies).toBe("patch");
});
test("range utility returns empty for unsupported operators", () => {
  /** Verifies: CHG-PLAN-015 */
  expect(getVersionRangeType("*")).toBe("");
});
test("logger warn category is callable", () => {
  /** Verifies: CHG-LOG-004 */
  const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
  warn("warning");
  expect(spy).toHaveBeenCalled();
  spy.mockRestore();
});
