import { expect, test } from "vitest";
import {
  Application,
  ConsoleLogger,
  Deserializer,
  EntryPointStrategy,
  FileRegistry,
  JSONOutput,
  ReflectionKind,
} from "typedoc";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { mkdtempSync } from "node:fs";

async function makeProject(files: Record<string, string>, options: Record<string, unknown> = {}) {
  const root = mkdtempSync(path.join(tmpdir(), "typedoc-oracle-"));
  const src = path.join(root, "src");
  await mkdir(src, { recursive: true });
  await writeFile(path.join(root, "tsconfig.json"), JSON.stringify({
    compilerOptions: {
      target: "ES2020",
      module: "NodeNext",
      moduleResolution: "NodeNext",
      strict: true,
    },
  }));
  for (const [name, text] of Object.entries(files)) {
    const full = path.join(root, name);
    await mkdir(path.dirname(full), { recursive: true });
    await writeFile(full, text);
  }
  const app = await Application.bootstrap({
    entryPoints: [path.join(src, "index.ts")],
    tsconfig: path.join(root, "tsconfig.json"),
    skipErrorChecking: true,
    logLevel: "None",
    ...options,
  });
  return { root, app, project: await app.convert() };
}

async function converted(source: string, options: Record<string, unknown> = {}) {
  return makeProject({ "src/index.ts": source }, options);
}

test("conversion returns a project for exported class function and variable", async () => {
  const { project } = await converted(`
    /** Widget docs */
    export class Widget {}
    /** Render docs */
    export function render(value: string): string { return value; }
    export const enabled = true;
  `);
  expect(project?.children?.map((child) => child.name).sort()).toEqual(["Widget", "enabled", "render"]);
  expect(project?.getReflectionsByKind(ReflectionKind.Class).map((child) => child.name)).toEqual(["Widget"]);
});

test("conversion preserves method parameter types and default values", async () => {
  const { project } = await converted(`
    export class Widget {
      render(name: string = "x"): string { return name; }
    }
  `);
  const render = project?.getChildByName("Widget")?.getChildByName("render") as any;
  expect(render.signatures[0].parameters[0].name).toBe("name");
  expect(render.signatures[0].parameters[0].type.toString()).toBe("string");
  expect(render.signatures[0].parameters[0].defaultValue).toBe('"x"');
});

test("conversion records accessor and property reflections together", async () => {
  const { project } = await converted(`
    export class Box {
      value: string = "x";
      get label(): string { return this.value; }
      set label(value: string) { this.value = value; }
    }
  `);
  const names = (project?.getChildByName("Box") as any).children.map((child: any) => [child.name, child.kind]);
  expect(names).toContainEqual(["value", ReflectionKind.Property]);
  expect(names).toContainEqual(["label", ReflectionKind.Accessor]);
});

test("conversion records union tuple and interface member type strings", async () => {
  const { project } = await converted(`
    export type Choice = "a" | "b" | number;
    export type Pair<T> = [name: string, value?: T, rest: boolean[]];
    export interface Shape { a: string; b?: number; }
  `);
  expect((project?.getChildByName("Choice") as any).type.toString()).toBe('"a" | "b" | number');
  expect((project?.getChildByName("Pair") as any).type.toString()).toBe("[name: string, value?: T, rest: boolean[]]");
  expect((project?.getChildByName("Shape") as any).children.map((child: any) => [child.name, child.flags.isOptional])).toEqual([
    ["a", false],
    ["b", true],
  ]);
});

test("project groups and categories are derived from comment tags", async () => {
  const { project } = await converted(`
    /** @group Utilities @category Core */
    export function alpha(): void {}
    /** @category Core */
    export const beta = 1;
  `);
  const groups = new Map(project?.groups?.map((group) => [group.title, group.children.map((child) => child.name)]));
  expect(groups.get("Utilities")).toEqual(["alpha"]);
  expect(groups.get("Variables")).toEqual(["beta"]);
  expect(project?.categories?.map((category) => [category.title, category.children.map((child) => child.name)])).toEqual([
    ["Core", ["beta", "alpha"]],
  ]);
});

test("comment block tags become signature comments", async () => {
  const { project } = await converted(`
    /** Say hello.
     * @returns greeting text
     */
    export function hello(name: string): string { return name; }
  `);
  const signature = (project?.getChildByName("hello") as any).signatures[0];
  expect(signature.comment.summary.map((part: any) => part.text).join("")).toBe("Say hello.");
  expect(signature.comment.getTag("@returns").content.map((part: any) => part.text).join("")).toBe("greeting text");
});

test("inline link tags resolve to reflected declarations", async () => {
  const { project } = await converted(`
    /** Target docs */
    export class Target { run(): void {} }
    /** See {@link Target | target class}. */
    export function use(): void {}
  `, { useTsLinkResolution: true });
  const summary = (project?.getChildByName("use") as any).signatures[0].comment.summary;
  expect(summary.find((part: any) => part.kind === "inline-tag").target.name).toBe("Target");
  expect(summary.map((part: any) => part.text ?? "").join("")).toContain("target class");
});

test("inline member link tags resolve to member reflections", async () => {
  const { project } = await converted(`
    export class Target { /** member docs */ run(): void {} }
    /** See {@link Target.run}. */
    export function use(): void {}
  `, { useTsLinkResolution: true });
  const summary = (project?.getChildByName("use") as any).signatures[0].comment.summary;
  expect(summary.find((part: any) => part.kind === "inline-tag").target.name).toBe("run");
});

test("excludePrivate removes private members from traversal", async () => {
  const { project } = await converted(`
    export class Widget {
      public shown = 1;
      private hidden = 2;
    }
  `, { excludePrivate: true });
  expect((project?.getChildByName("Widget") as any).children.map((child: any) => child.name)).toEqual([
    "constructor",
    "shown",
  ]);
});

test("excludeProtected removes protected members from traversal", async () => {
  const { project } = await converted(`
    export class Widget {
      public shown = 1;
      protected hidden = 2;
    }
  `, { excludeProtected: true });
  expect((project?.getChildByName("Widget") as any).children.map((child: any) => child.name)).toEqual([
    "constructor",
    "shown",
  ]);
});

test("excludeInternal removes declarations tagged internal", async () => {
  const { project } = await converted(`
    /** @internal */
    export const hidden = 1;
    export const shown = 2;
  `, { excludeInternal: true });
  expect(project?.children?.map((child) => child.name)).toEqual(["shown"]);
});

test("serializer projectToObject writes schema version and children", async () => {
  const { root, app, project } = await converted("export class Widget {}");
  const json = app.serializer.projectToObject(project!, root) as any;
  expect(json.schemaVersion).toBe(JSONOutput.SCHEMA_VERSION);
  expect(json.name).toBe("Documentation");
  expect(json.children.map((child: any) => child.name)).toEqual(["Widget"]);
});

test("deserializer revives serialized child relationships", async () => {
  const { root, app, project } = await converted("export class Widget { value: string = 'x'; }");
  const json = app.serializer.projectToObject(project!, root) as any;
  const revived = new Deserializer(new ConsoleLogger()).reviveProject("Revived", json, {
    projectRoot: root,
    registry: new FileRegistry(),
  });
  expect(revived.children?.map((child) => child.name)).toEqual(["Widget"]);
  expect((revived.getChildByName("Widget") as any).children.map((child: any) => child.name)).toEqual([
    "constructor",
    "value",
  ]);
});

test("serialized and revived type strings remain stable", async () => {
  const { root, app, project } = await converted("export type Choice = 'a' | 'b' | number;");
  const json = app.serializer.projectToObject(project!, root) as any;
  const revived = new Deserializer(new ConsoleLogger()).reviveProject("Revived", json, {
    projectRoot: root,
    registry: new FileRegistry(),
  });
  expect((project?.getChildByName("Choice") as any).type.toString()).toBe('"a" | "b" | number');
  expect((revived.getChildByName("Choice") as any).type.toString()).toBe('"a" | "b" | number');
});

test("serialized and revived comments keep summary text", async () => {
  const { root, app, project } = await converted(`
    /** Widget summary. */
    export class Widget {}
  `);
  const json = app.serializer.projectToObject(project!, root) as any;
  const revived = new Deserializer(new ConsoleLogger()).reviveProject("Revived", json, {
    projectRoot: root,
    registry: new FileRegistry(),
  });
  expect((revived.getChildByName("Widget") as any).comment.summary.map((part: any) => part.text).join("")).toBe("Widget summary.");
});

test("generateJson writes a project json file", async () => {
  const { root, app, project } = await converted("export const value = 1;");
  const out = path.join(root, "docs", "api.json");
  await app.generateJson(project!, out);
  const json = JSON.parse(await readFile(out, "utf8"));
  expect(json.schemaVersion).toBe(JSONOutput.SCHEMA_VERSION);
  expect(json.children.map((child: any) => child.name)).toEqual(["value"]);
});

test("generateOutputs writes selected json output", async () => {
  const root = mkdtempSync(path.join(tmpdir(), "typedoc-output-"));
  const out = path.join(root, "api.json");
  const { app, project } = await converted("export const value = 1;", {
    json: out,
  });
  await app.generateOutputs(project!);
  await expect(access(out)).resolves.toBeUndefined();
});

test("entry point discovery returns configured entry points", async () => {
  const { app } = await converted("export const value = 1;");
  const entries = app.getEntryPoints();
  expect(entries?.map((entry) => path.basename(entry.displayName))).toEqual(["index"]);
});

test("missing entry points make getDefinedEntryPoints return undefined", async () => {
  const root = mkdtempSync(path.join(tmpdir(), "typedoc-missing-"));
  const app = await Application.bootstrap({
    entryPoints: [path.join(root, "missing.ts")],
    skipErrorChecking: true,
    logLevel: "None",
  });
  expect(app.getDefinedEntryPoints()).toBeUndefined();
  expect(await app.convert()).toBeUndefined();
});

test("skipErrorChecking false prevents conversion on TypeScript diagnostics", async () => {
  const { project } = await converted("export const value: string = 1;", { skipErrorChecking: false });
  expect(project).toBeUndefined();
});

test("skipErrorChecking true still converts declarations with diagnostics", async () => {
  const { project } = await converted("export const value: string = 1;", { skipErrorChecking: true });
  expect(project?.children?.map((child) => child.name)).toEqual(["value"]);
});

test("alwaysCreateEntryPointModule wraps project children in a module", async () => {
  const { project } = await converted("export const value = 1;", { alwaysCreateEntryPointModule: true });
  expect(project?.children?.map((child) => child.name)).toEqual(["index"]);
  expect((project?.getChildByName("index") as any).children.map((child: any) => child.name)).toEqual(["value"]);
});

test("merge entry point strategy revives json project inputs", async () => {
  const first = await converted("export const value = 1;");
  const jsonPath = path.join(first.root, "api.json");
  await first.app.generateJson(first.project!, jsonPath);
  const app = await Application.bootstrap({
    entryPoints: [jsonPath],
    entryPointStrategy: EntryPointStrategy.Merge,
    logLevel: "None",
  });
  const merged = await app.convert();
  expect(merged?.children?.map((child) => child.name)).toEqual(["value"]);
});

test("source references record source file positions", async () => {
  const { project } = await converted("export const value = 1;");
  const source = (project?.getChildByName("value") as any).sources[0];
  expect(source.fileName).toBe("index.ts");
  expect(source.line).toBe(1);
  expect(source.character).toBe(13);
});

test("source references include the full source file path", async () => {
  const { project } = await converted("export const value = 1;");
  const source = (project?.getChildByName("value") as any).sources[0];
  expect(source.fullFileName.endsWith(path.join("src", "index.ts"))).toBe(true);
});

test("reference type resolves to the revived target after json round trip", async () => {
  const { root, app, project } = await converted(`
    export class Widget {}
    export interface Holder { widget: Widget; }
  `);
  const json = app.serializer.projectToObject(project!, root) as any;
  const revived = new Deserializer(new ConsoleLogger()).reviveProject("Revived", json, {
    projectRoot: root,
    registry: new FileRegistry(),
  });
  const holder = revived.getChildByName("Holder") as any;
  const widgetProperty = holder.children.find((child: any) => child.name === "widget");
  expect(widgetProperty.type.reflection.name).toBe("Widget");
});

test("category metadata survives json round trip", async () => {
  const { root, app, project } = await converted(`
    /** @category Core */
    export const value = 1;
  `);
  const json = app.serializer.projectToObject(project!, root) as any;
  const revived = new Deserializer(new ConsoleLogger()).reviveProject("Revived", json, {
    projectRoot: root,
    registry: new FileRegistry(),
  });
  expect(revived.categories?.map((category) => [category.title, category.children.map((child) => child.name)])).toEqual([
    ["Core", ["value"]],
  ]);
});

test("group metadata survives json round trip", async () => {
  const { root, app, project } = await converted(`
    /** @group Utilities */
    export function value(): void {}
  `);
  const json = app.serializer.projectToObject(project!, root) as any;
  const revived = new Deserializer(new ConsoleLogger()).reviveProject("Revived", json, {
    projectRoot: root,
    registry: new FileRegistry(),
  });
  expect(revived.groups?.map((group) => [group.title, group.children.map((child) => child.name)])).toEqual([
    ["Utilities", ["value"]],
  ]);
});
