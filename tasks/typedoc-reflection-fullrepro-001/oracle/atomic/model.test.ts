import { expect, test } from "vitest";
import {
  Application,
  ArrayType,
  Comment,
  CommentTag,
  ConsoleLogger,
  ContainerReflection,
  DeclarationReflection,
  EventDispatcher,
  EventHooks,
  FileRegistry,
  IntrinsicType,
  IntersectionType,
  LiteralType,
  LogLevel,
  MinimalSourceFile,
  NamedTupleMember,
  OptionalType,
  Options,
  ParameterReflection,
  ProjectReflection,
  ReferenceReflection,
  ReferenceType,
  ReflectionFlag,
  ReflectionFlags,
  ReflectionKind,
  RestType,
  SignatureReflection,
  SourceReference,
  TupleType,
  TypeOperatorType,
  UnionType,
  makeRecursiveVisitor,
} from "typedoc";

test("bootstrap creates an application with converter and options", async () => {
  const app = await Application.bootstrap({ logLevel: "None" });
  expect(app.converter).toBeDefined();
  expect(app.options).toBeDefined();
});

test("setOptions returns true for valid option values", async () => {
  const app = await Application.bootstrap({ logLevel: "None" });
  expect(await app.setOptions({ pretty: true, logLevel: "None" })).toBe(true);
  expect(app.options.getValue("pretty" as any)).toBe(true);
});

test("setOptions returns false for invalid option values", async () => {
  const app = await Application.bootstrap({ logLevel: "None" });
  expect(await app.setOptions({ entryPointStrategy: "not-a-strategy" as any, logLevel: "None" })).toBe(false);
});

test("options store explicit values after setValue", () => {
  const options = new Options(new ConsoleLogger());
  options.addDeclaration({ name: "enabled", type: 4 as any, defaultValue: false });
  options.setValue("enabled" as any, true);
  expect(options.getValue("enabled" as any)).toBe(true);
  expect(options.isSet("enabled" as any)).toBe(true);
});

test("reflection flags clear competing visibility flags", () => {
  const flags = new ReflectionFlags();
  flags.setFlag(ReflectionFlag.Private, true);
  flags.setFlag(ReflectionFlag.Protected, true);
  flags.setFlag(ReflectionFlag.Public, true);
  expect(flags.isPrivate).toBe(false);
  expect(flags.isProtected).toBe(false);
  expect(flags.isPublic).toBe(true);
});

test("reflection flags expose independent modifier booleans", () => {
  const flags = new ReflectionFlags();
  flags.setFlag(ReflectionFlag.Static, true);
  flags.setFlag(ReflectionFlag.Optional, true);
  flags.setFlag(ReflectionFlag.Readonly, true);
  expect([flags.isStatic, flags.isOptional, flags.isReadonly]).toEqual([true, true, true]);
});

test("project reflection registers itself by identifier", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  expect(project.getReflectionById(project.id)).toBe(project);
});

test("container addChild updates children and parent projection", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const child = new DeclarationReflection("Widget", ReflectionKind.Class, project);
  project.addChild(child);
  expect(project.children?.map((item) => item.name)).toEqual(["Widget"]);
  expect(project.childrenIncludingDocuments?.map((item) => item.name)).toEqual(["Widget"]);
  expect(child.parent).toBe(project);
});

test("container traverse stops when callback returns false", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  project.addChild(new DeclarationReflection("First", ReflectionKind.Class, project));
  project.addChild(new DeclarationReflection("Second", ReflectionKind.Class, project));
  const seen: string[] = [];
  project.traverse((reflection) => {
    seen.push(reflection.name);
    return false;
  });
  expect(seen).toEqual(["First"]);
});

test("declaration getAllSignatures includes call and index signatures", () => {
  const owner = new DeclarationReflection("Callable", ReflectionKind.Function);
  const call = new SignatureReflection("call", ReflectionKind.CallSignature, owner);
  const index = new SignatureReflection("__index", ReflectionKind.IndexSignature, owner);
  owner.signatures = [call];
  owner.indexSignatures = [index];
  expect(owner.getAllSignatures().map((sig) => sig.kind)).toEqual([
    ReflectionKind.CallSignature,
    ReflectionKind.IndexSignature,
  ]);
  expect(owner.getNonIndexSignatures().map((sig) => sig.kind)).toEqual([ReflectionKind.CallSignature]);
});

test("declaration getProperties returns direct property children", () => {
  const owner = new DeclarationReflection("Widget", ReflectionKind.Class);
  owner.addChild(new DeclarationReflection("name", ReflectionKind.Property, owner));
  expect(owner.getProperties().map((item) => item.name)).toEqual(["name"]);
});

test("project registry finds reflections by kind mask", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const cls = new DeclarationReflection("Widget", ReflectionKind.Class, project);
  const fn = new DeclarationReflection("render", ReflectionKind.Function, project);
  project.addChild(cls);
  project.addChild(fn);
  project.registerReflection(cls);
  project.registerReflection(fn);
  expect(project.getReflectionsByKind(ReflectionKind.Class).map((item) => item.name)).toEqual(["Widget"]);
});

test("reference reflection resolves its immediate target", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const target = new DeclarationReflection("Target", ReflectionKind.Class, project);
  project.addChild(target);
  project.registerReflection(target);
  const alias = new ReferenceReflection("Alias", target, project);
  expect(alias.tryGetTargetReflection()).toBe(target);
  expect(alias.getTargetReflection()).toBe(target);
});

test("reference reflection follows nested reference targets", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const target = new DeclarationReflection("Target", ReflectionKind.Class, project);
  project.addChild(target);
  project.registerReflection(target);
  const alias = new ReferenceReflection("Alias", target, project);
  project.addChild(alias);
  project.registerReflection(alias);
  const alias2 = new ReferenceReflection("Alias2", alias, project);
  expect(alias2.tryGetTargetReflectionDeep()).toBe(target);
});

test("reference reflection delegates child lookup to its target", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const target = new DeclarationReflection("Target", ReflectionKind.Class, project);
  const member = new DeclarationReflection("member", ReflectionKind.Property, target);
  target.addChild(member);
  project.registerReflection(target);
  const alias = new ReferenceReflection("Alias", target, project);
  expect(alias.getChildByName("member")).toBe(member);
});

test("unresolved reference reflection raises on required target access", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const alias = new ReferenceReflection("Alias", 99999, project);
  expect(alias.tryGetTargetReflection()).toBeUndefined();
  expect(() => alias.getTargetReflection()).toThrow(Error);
});

test("comment display parts combine text code and inline tags", () => {
  const parts: any[] = [
    { kind: "text", text: "See " },
    { kind: "code", text: "`Widget`" },
    { kind: "inline-tag", tag: "@link", text: "Target", target: "Target" },
    { kind: "relative-link", text: " guide", target: "./guide.md" },
  ];
  expect(Comment.combineDisplayParts(parts)).toBe("See `Widget`{@link Target} guide");
});

test("comment display part cloning returns independent arrays", () => {
  const parts: any[] = [{ kind: "text", text: "hello" }];
  const cloned = Comment.cloneDisplayParts(parts);
  cloned[0].text = "changed";
  expect(parts[0].text).toBe("hello");
  expect(cloned[0].text).toBe("changed");
});

test("comment tags can be selected and removed by tag name", () => {
  const returns = new CommentTag("@returns", [{ kind: "text", text: "ok" }] as any);
  const comment = new Comment([], [returns], new Set(["@beta"]));
  expect(comment.getTag("@returns")?.content.map((part: any) => part.text).join("")).toBe("ok");
  expect(comment.hasModifier("@beta")).toBe(true);
  comment.removeModifier("@beta");
  comment.removeTags("@returns");
  expect(comment.hasModifier("@beta")).toBe(false);
  expect(comment.getTag("@returns")).toBeUndefined();
});

test("comment short summary uses the first paragraph when enabled", () => {
  const comment = new Comment([{ kind: "text", text: "Header\n\nBody" }] as any, []);
  expect(comment.getShortSummary(true).map((part: any) => part.text).join("")).toBe("Header");
  expect(comment.getShortSummary(false)).toEqual([]);
});

test("comment splitPartsToHeaderAndBody separates header from body", () => {
  expect(Comment.splitPartsToHeaderAndBody([{ kind: "text", text: "Header\n\nBody" }] as any)).toEqual({
    header: "Header",
    body: [{ kind: "text", text: "\nBody" }],
  });
});

test("similar comment tags compare tag and combined content", () => {
  const a = new CommentTag("@returns", [{ kind: "text", text: "ok" }] as any);
  const b = new CommentTag("@returns", [{ kind: "text", text: "ok" }] as any);
  b.skipRendering = true;
  expect(a.similarTo(b)).toBe(true);
});

test("intrinsic array union and intersection types stringify", () => {
  expect(new IntrinsicType("string").toString()).toBe("string");
  expect(new ArrayType(new IntrinsicType("number")).toString()).toBe("number[]");
  expect(new UnionType([new LiteralType("yes"), new IntrinsicType("boolean")]).toString()).toBe('"yes" | boolean');
  expect(new IntersectionType([new IntrinsicType("A"), new IntrinsicType("B")]).toString()).toBe("A & B");
});

test("tuple related types stringify named optional and rest elements", () => {
  const tuple = new TupleType([
    new NamedTupleMember("name", false, new IntrinsicType("string")),
    new OptionalType(new IntrinsicType("number")),
    new RestType(new ArrayType(new IntrinsicType("boolean"))),
  ]);
  expect(tuple.toString()).toBe("[name: string, number?, ...boolean[]]");
});

test("type operator wraps its target expression", () => {
  expect(new TypeOperatorType(new IntrinsicType("string"), "keyof").toString()).toBe("keyof string");
});

test("resolved reference type exposes target reflection", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const target = new DeclarationReflection("Widget", ReflectionKind.Class, project);
  project.registerReflection(target);
  const type = ReferenceType.createResolvedReference("Widget", target, project);
  expect(type.toString()).toBe("Widget");
  expect(type.reflection).toBe(target);
  expect(type.isIntentionallyBroken()).toBe(false);
});

test("broken reference type remains printable and intentionally broken", () => {
  const project = new ProjectReflection("Pkg", "/tmp/pkg");
  const type = ReferenceType.createBrokenReference("Missing", project);
  expect(type.toString()).toBe("Missing");
  expect(type.reflection).toBeUndefined();
  expect(type.isIntentionallyBroken()).toBe(true);
});

test("recursive visitor walks nested type objects", () => {
  const seen: string[] = [];
  const visitor = makeRecursiveVisitor({
    union: (type) => seen.push(`union:${type.types.length}`),
    array: (type) => seen.push(`array:${type.elementType.type}`),
    intrinsic: (type) => seen.push(`intrinsic:${type.name}`),
    literal: (type) => seen.push(`literal:${type.value}`),
  });
  new UnionType([new ArrayType(new IntrinsicType("string")), new LiteralType(2)]).visit(visitor);
  expect(seen).toEqual(["union:2", "array:intrinsic", "intrinsic:string", "literal:2"]);
});

test("file registry reuses ids for repeated absolute paths", () => {
  const registry = new FileRegistry();
  expect(registry.registerAbsolute("/tmp/a.png")).toEqual({ target: 1 });
  expect(registry.registerAbsolute("/tmp/a.png")).toEqual({ target: 1 });
  expect(registry.getName(1)).toBe("a.png");
  expect(registry.resolvePath(1)).toBe("/tmp/a.png");
});

test("file registry allocates distinct media names for basename collisions", () => {
  const registry = new FileRegistry();
  registry.registerAbsolute("/tmp/a.png");
  registry.registerAbsolute("/other/a.png");
  expect(registry.getName(1)).toBe("a.png");
  expect(registry.getName(2)).toBe("a-1.png");
});

test("source reference records file position values", () => {
  const source = new SourceReference("src/index.ts", 4, 2);
  expect(source.fileName).toBe("src/index.ts");
  expect(source.line).toBe(4);
  expect(source.character).toBe(2);
});

test("minimal source file maps positions to lines and characters", () => {
  const file = new MinimalSourceFile("a\nbb\nccc", "/tmp/input.ts");
  expect(file.fileName).toBe("/tmp/input.ts");
  expect(file.getLineAndCharacterOfPosition(3)).toEqual({ line: 1, character: 1 });
});

test("event dispatcher removes listeners after off", () => {
  const events = new EventDispatcher();
  const seen: number[] = [];
  const callback = (value: number) => seen.push(value);
  events.on("go", callback);
  events.trigger("go", 1);
  events.off("go", callback);
  events.trigger("go", 2);
  expect(seen).toEqual([1]);
});

test("event hooks emit in priority order and collect results", () => {
  const hooks = new EventHooks();
  const seen: string[] = [];
  hooks.on("value", (value: number) => {
    seen.push(`late:${value}`);
    return value + 1;
  }, 100);
  hooks.on("value", (value: number) => {
    seen.push(`early:${value}`);
    return value + 1;
  }, 0);
  expect(hooks.emit("value", 1)).toEqual([2, 2]);
  expect(seen).toEqual(["early:1", "late:1"]);
});

test("logger level constants preserve ordering by severity", () => {
  expect(LogLevel.None).toBeGreaterThan(LogLevel.Warn);
});

test("parameter reflections keep assigned types and default values", () => {
  const signature = new SignatureReflection("call", ReflectionKind.CallSignature);
  const parameter = new ParameterReflection("value", ReflectionKind.Parameter, signature);
  parameter.type = new IntrinsicType("string");
  parameter.defaultValue = '"x"';
  expect(parameter.name).toBe("value");
  expect(parameter.type.toString()).toBe("string");
  expect(parameter.defaultValue).toBe('"x"');
});

test("container reflection exposes empty child projections by default", () => {
  const container = new ContainerReflection("Container", ReflectionKind.Module);
  expect(container.children).toBeUndefined();
  expect(container.childrenIncludingDocuments).toBeUndefined();
});
