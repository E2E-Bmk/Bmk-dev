// Oracle atomic tests — AST model, parsing, raws, stringification, building,
// traversal, values, cloning and JSON for the postcss engine.
import { describe, expect, test } from "vitest";
import postcss, {
  AtRule,
  Comment,
  Container,
  Declaration,
  Document,
  Input,
  Node,
  Root,
  Rule,
  atRule,
  comment,
  decl,
  document,
  fromJSON,
  list,
  parse,
  root,
  rule,
  stringify,
} from "postcss";

describe("parsing and input", () => {
  test("parse returns a Root and reproduces the input byte for byte", () => {
    /** Verifies: PC-PAR-001, PC-STR-001, PC-CVI-001 */
    const css = "/* head */\n@media (min-width: 10px) {\n  a:hover,  b {\n    color : red !important;\n  }\n}\n\n";
    const tree = parse(css);
    expect(tree instanceof Root).toBe(true);
    expect(tree.type).toBe("root");
    expect(tree.toString()).toBe(css);
  });

  test("parse is reachable as a method of the default export", () => {
    /** Verifies: PC-PAR-011 */
    const tree = postcss.parse("a{}");
    expect(tree instanceof Root).toBe(true);
    expect(tree.toString()).toBe("a{}");
  });

  test("the from option records the absolute file path", () => {
    /** Verifies: PC-PAR-002 */
    const tree = parse("a{}", { from: "/style/dir/app.css" });
    expect(tree.source!.input.file).toBe("/style/dir/app.css");
    expect(tree.source!.input.from).toBe("/style/dir/app.css");
  });

  test("without from the input synthesizes an identifier and file is undefined", () => {
    /** Verifies: PC-PAR-003 */
    const tree = parse("a{}");
    expect(tree.source!.input.file).toBeUndefined();
    expect(typeof tree.source!.input.from).toBe("string");
    expect(tree.source!.input.from.length).toBeGreaterThan(0);
  });

  test("all nodes of one tree share the same Input carrying the css text", () => {
    /** Verifies: PC-PAR-004 */
    const css = "a { color: red }";
    const tree = parse(css);
    const input = tree.source!.input;
    expect(input instanceof Input).toBe(true);
    expect(input.css).toBe(css);
    expect(tree.first!.source!.input).toBe(input);
    expect((tree.first as Rule).first!.source!.input).toBe(input);
  });

  test("a byte-order mark is stripped from css, flagged, and re-emitted", () => {
    /** Verifies: PC-PAR-005 */
    const tree = parse("\uFEFFa{}");
    expect(tree.source!.input.hasBOM).toBe(true);
    expect(tree.source!.input.css).toBe("a{}");
    expect(tree.toString()).toBe("\uFEFFa{}");
    expect(parse("a{}").source!.input.hasBOM).toBe(false);
  });

  test("source positions carry 1-based line and column and 0-based offsets", () => {
    /** Verifies: PC-PAR-006 */
    const tree = parse("a { color: red; top: 0 }");
    const r = tree.first as Rule;
    expect(r.source!.start).toEqual({ line: 1, column: 1, offset: 0 });
    expect(r.source!.end).toEqual({ line: 1, column: 24, offset: 24 });
    const d1 = r.nodes[0] as Declaration;
    expect(d1.source!.start).toEqual({ line: 1, column: 5, offset: 4 });
    expect(d1.source!.end).toEqual({ line: 1, column: 15, offset: 15 });
    const d2 = r.nodes[1] as Declaration;
    expect(d2.source!.end).toEqual({ line: 1, column: 22, offset: 22 });
  });

  test("whitespace between nodes lives in the following node's raws.before", () => {
    /** Verifies: PC-PAR-007 */
    const tree = parse("a{}\n\n  b{}");
    expect((tree.nodes[1] as Rule).raws.before).toBe("\n\n  ");
    expect((tree.first as Rule).raws.before).toBe("");
  });

  test("bodyless at-rules have no nodes property while empty blocks have an empty array", () => {
    /** Verifies: PC-PAR-008 */
    const tree = parse('@import "a.css";\n@media x {}');
    const imp = tree.first as AtRule;
    const media = tree.nodes[1] as AtRule;
    expect(imp.nodes).toBeUndefined();
    expect(media.nodes).toEqual([]);
    expect(imp.name).toBe("import");
    expect(imp.params).toBe('"a.css"');
  });

  test("custom property declarations keep their value verbatim and set variable", () => {
    /** Verifies: PC-PAR-009 */
    const tree = parse(":root{--x:  1px\n  }");
    const d = (tree.first as Rule).first as Declaration;
    expect(d.variable).toBe(true);
    expect(d.value).toBe("1px\n  ");
    const dollar = parse("$width: 10px; a{}").first as Declaration;
    expect(dollar.type).toBe("decl");
    expect(dollar.variable).toBe(true);
    expect(dollar.value).toBe("10px");
    const plain = (parse("a{color:red}").first as Rule).first as Declaration;
    expect(plain.variable).toBe(false);
  });

  test("CRLF line endings round-trip and are captured into raws", () => {
    /** Verifies: PC-PAR-010, PC-STR-001 */
    const css = "a{\r\n color:red}\r\n";
    const tree = parse(css);
    expect(tree.toString()).toBe(css);
    expect(((tree.first as Rule).first as Declaration).raws.before).toBe("\r\n ");
  });

  test("Input is directly constructible", () => {
    /** Verifies: PC-PAR-011 */
    const input = new Input("ab\ncd", { from: "/z/i.css" });
    expect(input.css).toBe("ab\ncd");
    expect(input.file).toBe("/z/i.css");
  });
});

describe("node model and raws", () => {
  test("each node type exposes its value properties", () => {
    /** Verifies: PC-NOD-001 */
    const tree = parse("@media screen { a { color: red !important } }\n/* note */");
    const media = tree.first as AtRule;
    expect(media.type).toBe("atrule");
    expect(media.name).toBe("media");
    expect(media.params).toBe("screen");
    const r = media.first as Rule;
    expect(r.type).toBe("rule");
    expect(r.selector).toBe("a");
    const d = r.first as Declaration;
    expect(d.type).toBe("decl");
    expect(d.prop).toBe("color");
    expect(d.value).toBe("red");
    expect(d.important).toBe(true);
    const c = tree.nodes[1] as Comment;
    expect(c.type).toBe("comment");
    expect(c.text).toBe("note");
  });

  test("parent links exist inside a tree and detached nodes have none", () => {
    /** Verifies: PC-NOD-002 */
    const tree = parse("a { color: red }");
    const r = tree.first as Rule;
    expect(r.parent).toBe(tree);
    expect(r.first!.parent).toBe(r);
    expect(decl({ prop: "x", value: "1" }).parent).toBeUndefined();
  });

  test("raws capture the exact formatting fragments", () => {
    /** Verifies: PC-NOD-003 */
    const tree = parse("@media (x) {\n  a {\n    color : red;\n  }\n}\n");
    const media = tree.first as AtRule;
    expect(media.raws).toEqual({ before: "", between: " ", afterName: " ", semicolon: false, after: "\n" });
    const r = media.first as Rule;
    expect(r.raws.before).toBe("\n  ");
    expect(r.raws.between).toBe(" ");
    expect(r.raws.semicolon).toBe(true);
    expect(r.raws.after).toBe("\n  ");
    const d = r.first as Declaration;
    expect(d.raws.before).toBe("\n    ");
    expect(d.raws.between).toBe(" : ");
    expect(tree.raws.after).toBe("\n");
  });

  test("comment raws record the inner whitespace", () => {
    /** Verifies: PC-NOD-003 */
    const c = parse("/*  padded  */").first as Comment;
    expect(c.text).toBe("padded");
    expect(c.raws.left).toBe("  ");
    expect(c.raws.right).toBe("  ");
  });

  test("a commented selector is cached as raw plus cleaned value", () => {
    /** Verifies: PC-NOD-004 */
    const css = "a /* s */ b { color: red }";
    const r = parse(css).first as Rule;
    expect(r.selector).toBe("a  b");
    expect(r.raws.selector).toEqual({ raw: "a /* s */ b", value: "a  b" });
    expect(r.root().toString()).toBe(css);
  });

  test("a commented value is cached and reassignment prints the new value", () => {
    /** Verifies: PC-NOD-004, PC-NOD-005, PC-CVI-005 */
    const tree = parse("a /* s */ b { color: red /* v */ ; margin: 0 }");
    const r = tree.first as Rule;
    const d = r.first as Declaration;
    expect(d.value).toBe("red ");
    expect(d.raws.value).toEqual({ raw: "red /* v */ ", value: "red " });
    d.value = "blue";
    expect(tree.toString()).toBe("a /* s */ b { color: blue; margin: 0 }");
    expect(r.raws.selector).toEqual({ raw: "a /* s */ b", value: "a  b" });
  });

  test("nonstandard important fragments are kept in raws.important", () => {
    /** Verifies: PC-NOD-006, PC-VAL-004 */
    const css = "a{color:red ! important}";
    const tree = parse(css);
    const d = (tree.first as Rule).first as Declaration;
    expect(d.important).toBe(true);
    expect(d.raws.important).toBe(" ! important");
    expect(tree.toString()).toBe(css);
  });

  test("raw resolves captured fragments and synthesizes defaults", () => {
    /** Verifies: PC-NOD-007 */
    const d = (parse("a {\n  color : red;\n}").first as Rule).first as Declaration;
    expect(d.raw("between")).toBe(" : ");
    const constructed = rule({ selector: "x" });
    expect(constructed.raw("between", "beforeOpen")).toBe(" ");
  });

  test("cleanRaws reprints the subtree with default formatting", () => {
    /** Verifies: PC-NOD-008 */
    const tree = parse("a {\n  color : red;\n}");
    tree.cleanRaws();
    expect(tree.toString()).toBe("a {\n    color: red;\n}");
  });

  test("assign applies several properties and returns the node", () => {
    /** Verifies: PC-NOD-009 */
    const d = decl({ prop: "a", value: "1" }).assign({ prop: "b", important: true }) as Declaration;
    expect(d.prop).toBe("b");
    expect(d.important).toBe(true);
    expect(d.toString()).toBe("b: 1 !important");
  });
});

describe("stringification", () => {
  test("stringify drives the builder with parts and container markers", () => {
    /** Verifies: PC-STR-002 */
    const parts: Array<[string, string | undefined, string | undefined]> = [];
    const tree = parse("a{x:1}");
    stringify(tree, (part, node, type) => parts.push([part, node?.type, type]));
    expect(parts).toEqual([
      ["a{", "rule", "start"], /* } */
      ["x:1", "decl", undefined],
      ["}", "rule", "end"], /* { */
    ]);
    expect(parts.map((p) => p[0]).join("")).toBe(tree.toString());
  });

  test("constructed declarations and rules use documented default formatting", () => {
    /** Verifies: PC-STR-003 */
    expect(decl({ prop: "color", value: "black" }).toString()).toBe("color: black");
    const important = decl({ prop: "color", value: "black" });
    important.important = true;
    expect(important.toString()).toBe("color: black !important");
    expect(rule({ selector: "a" }).toString()).toBe("a {}");
  });

  test("constructed children indent four spaces and separate with semicolons", () => {
    /** Verifies: PC-STR-004 */
    const tree = root();
    const r = rule({ selector: "a" });
    r.append(decl({ prop: "color", value: "red" }));
    r.append({ prop: "top", value: "0" });
    tree.append(r);
    tree.append(rule({ selector: "b" }));
    expect(tree.toString()).toBe("a {\n    color: red;\n    top: 0\n}\nb {}");
  });

  test("nested constructed containers indent per level", () => {
    /** Verifies: PC-STR-004 */
    const tree = root();
    const m = atRule({ name: "media", params: "screen" });
    m.append(rule({ selector: "a" }));
    (m.first as Rule).append({ prop: "x", value: "1" });
    tree.append(m);
    expect(tree.toString()).toBe("@media screen {\n    a {\n        x: 1\n    }\n}");
  });

  test("bodyless at-rules, comments, and root-level declarations print with defaults", () => {
    /** Verifies: PC-STR-005 */
    expect(atRule({ name: "charset", params: '"utf-8"' }).toString()).toBe('@charset "utf-8"');
    expect(comment({ text: "hi" }).toString()).toBe("/* hi */");
    const tree = root();
    tree.append(decl({ prop: "a", value: "b" }));
    expect(tree.toString()).toBe("a: b");
  });

  test("insertion into a parsed tree inherits indentation and semicolon style", () => {
    /** Verifies: PC-STR-006 */
    const indented = parse("@media screen {\n    a {\n        color: red\n    }\n}");
    ((indented.first as AtRule).first as Rule).append({ prop: "top", value: "0" });
    expect(indented.toString()).toBe("@media screen {\n    a {\n        color: red;\n        top: 0\n    }\n}");
    const semi = parse("a{x:1;}");
    (semi.first as Rule).append({ prop: "y", value: "2" });
    expect(semi.toString()).toBe("a{x:1;y:2;}");
  });

  test("a document concatenates its roots and reparents them", () => {
    /** Verifies: PC-STR-007 */
    const doc = new Document();
    const r1 = parse("a{}");
    const r2 = parse("b{}");
    doc.append(r1, r2);
    expect(doc.type).toBe("document");
    expect(doc.toString()).toBe("a{}b{}");
    expect(r1.parent).toBe(doc);
    expect(doc.nodes.length).toBe(2);
  });
});

describe("building trees", () => {
  test("factories build detached typed nodes", () => {
    /** Verifies: PC-BLD-001 */
    const r = rule({ selector: "a" });
    expect(r instanceof Rule).toBe(true);
    expect(r.selector).toBe("a");
    expect(r.type).toBe("rule");
    const d = decl({ prop: "x", value: "1" });
    expect(d instanceof Declaration).toBe(true);
    expect(d.prop).toBe("x");
    expect(d.value).toBe("1");
    const a = atRule({ name: "media", params: "screen" });
    expect(a instanceof AtRule).toBe(true);
    expect(a.name).toBe("media");
    expect(a.params).toBe("screen");
    const c = comment({ text: "t" });
    expect(c instanceof Comment).toBe(true);
    expect(c.text).toBe("t");
    expect(root() instanceof Root).toBe(true);
    expect(document() instanceof Document).toBe(true);
  });

  test("factory helpers are also reachable from the default export", () => {
    /** Verifies: PC-BLD-001 */
    expect(postcss.rule({ selector: "a" }).selector).toBe("a");
    expect(postcss.decl({ prop: "x", value: "1" }).prop).toBe("x");
    expect(postcss.atRule({ name: "layer" }).name).toBe("layer");
    expect(postcss.comment({ text: "note" }).text).toBe("note");
    expect(postcss.root().append({ selector: "a" }).toString()).toBe("a {}");
    expect(postcss.document() instanceof Document).toBe(true);
  });

  test("classes are constructible with properties objects and subclass Node", () => {
    /** Verifies: PC-BLD-001 */
    const r = new Rule({ selector: "a" });
    expect(r.selector).toBe("a");
    expect(r instanceof Container).toBe(true);
    expect(r instanceof Node).toBe(true);
    const d = new Declaration({ prop: "x", value: "1" });
    expect(d instanceof Node).toBe(true);
    expect(new AtRule({ name: "m", params: "p" }).params).toBe("p");
  });

  test("append accepts strings, arrays, and nodes and returns the container", () => {
    /** Verifies: PC-BLD-002 */
    const tree = root();
    tree.append("a { color: red; top: 0 }");
    expect(tree.toString()).toBe("a { color: red; top: 0 }");
    expect(tree.first!.type).toBe("rule");
    expect((tree.first as Rule).nodes.length).toBe(2);
    tree.append([rule({ selector: "c" }), comment({ text: "done" })]);
    expect(tree.toString()).toBe("a { color: red; top: 0 }\nc {} /* done */");
    const chained = root().append({ selector: "x" });
    expect(chained instanceof Root).toBe(true);
  });

  test("descriptor shapes select the node type", () => {
    /** Verifies: PC-BLD-002 */
    const tree = root();
    tree.append({ name: "layer", params: "base" });
    tree.append({ text: "note" });
    expect(tree.nodes[0].type).toBe("atrule");
    expect(tree.nodes[1].type).toBe("comment");
  });

  test("prepend puts nodes at the front in argument order", () => {
    /** Verifies: PC-BLD-002 */
    const tree = parse("a{}");
    tree.prepend({ selector: "x" }, "y{}");
    expect(tree.toString()).toBe("x{}\ny{}\na{}");
  });

  test("a declaration descriptor without a value throws", () => {
    /** Verifies: PC-BLD-003 */
    const r = rule({ selector: "a" });
    expect(() => r.append({ prop: "color" } as never)).toThrow(Error);
  });

  test("an unrecognized descriptor shape throws", () => {
    /** Verifies: PC-BLD-004 */
    expect(() => root().append({ unknown: 1 } as never)).toThrow(Error);
  });

  test("insertBefore and insertAfter splice relative to a child or index", () => {
    /** Verifies: PC-BLD-005 */
    const tree = parse("a { color: red }");
    const r = tree.first as Rule;
    r.insertBefore(r.first!, { prop: "m", value: "1" });
    r.insertAfter(r.nodes[1], { prop: "n", value: "2" });
    expect(tree.toString()).toBe("a { m: 1; color: red; n: 2 }");
    const byIndex = parse("a{} c{}");
    byIndex.insertBefore(1, { selector: "b" });
    expect(byIndex.toString()).toBe("a{} b{} c{}");
  });

  test("inserting a node owned by another tree removes it there first", () => {
    /** Verifies: PC-BLD-006 */
    const t1 = parse("a{x:1}");
    const t2 = parse("b{}");
    const moved = (t1.first as Rule).first!;
    (t2.first as Rule).append(moved);
    expect(t1.toString()).toBe("a{}");
    expect(t2.toString()).toBe("b{x:1}");
    expect(moved.parent).toBe(t2.first);
    expect((t1.first as Rule).nodes.length).toBe(0);
  });
});

describe("traversal and mutation", () => {
  const sample = () =>
    parse("a { color: red; top: 0 }\n@media screen { b { color: blue } }\n/* note */\nc { margin: 0 }");

  test("walk visits every descendant depth-first in document order", () => {
    /** Verifies: PC-TRV-003 */
    const seen: string[] = [];
    sample().walk((node) => {
      seen.push(node.type);
    });
    expect(seen).toEqual(["rule", "decl", "decl", "atrule", "rule", "decl", "comment", "rule", "decl"]);
  });

  test("typed walks visit their node type anywhere in the subtree", () => {
    /** Verifies: PC-TRV-004 */
    const tree = sample();
    const selectors: string[] = [];
    tree.walkRules((r) => {
      selectors.push(r.selector);
    });
    expect(selectors).toEqual(["a", "b", "c"]);
    const atNames: string[] = [];
    tree.walkAtRules((a) => {
      atNames.push(a.name);
    });
    expect(atNames).toEqual(["media"]);
    const texts: string[] = [];
    tree.walkComments((c) => {
      texts.push(c.text);
    });
    expect(texts).toEqual(["note"]);
  });

  test("string filters match exactly and regexps are tested", () => {
    /** Verifies: PC-TRV-004 */
    const tree = sample();
    const exact: string[] = [];
    tree.walkRules("b", (r) => {
      exact.push(r.selector);
    });
    expect(exact).toEqual(["b"]);
    const byRe: string[] = [];
    tree.walkRules(/^[bc]$/, (r) => {
      byRe.push(r.selector);
    });
    expect(byRe).toEqual(["b", "c"]);
    const colors: string[] = [];
    tree.walkDecls("color", (d) => {
      colors.push(d.value);
    });
    expect(colors).toEqual(["red", "blue"]);
    const caseSensitive: string[] = [];
    parse("a{Color:1;color:2}").walkDecls("color", (d) => {
      caseSensitive.push(d.value);
    });
    expect(caseSensitive).toEqual(["2"]);
  });

  test("returning false halts a walk and is returned", () => {
    /** Verifies: PC-TRV-002 */
    let count = 0;
    const result = sample().walk(() => {
      count += 1;
      if (count === 3) return false;
    });
    expect(count).toBe(3);
    expect(result).toBe(false);
  });

  test("each iterates direct children with indexes and stops on false", () => {
    /** Verifies: PC-TRV-001, PC-TRV-002 */
    const indexes: number[] = [];
    const tree = sample();
    const stopped = tree.each((_node, i) => {
      indexes.push(i);
      if (i === 1) return false;
    });
    expect(indexes).toEqual([0, 1]);
    expect(stopped).toBe(false);
  });

  test("each keeps visiting after inserts and removals during iteration", () => {
    /** Verifies: PC-TRV-001 */
    const grow = parse("a{} b{} c{}");
    const visited: string[] = [];
    grow.each((n) => {
      visited.push((n as Rule).selector);
      if ((n as Rule).selector === "b") grow.insertAfter(n, rule({ selector: "x" }));
    });
    expect(visited).toEqual(["a", "b", "x", "c"]);
    const shrink = parse("a{} b{} c{}");
    const survivors: string[] = [];
    shrink.each((n) => {
      survivors.push((n as Rule).selector);
      if ((n as Rule).selector === "a") n.remove();
    });
    expect(survivors).toEqual(["a", "b", "c"]);
    expect(shrink.toString()).toBe("b{} c{}");
  });

  test("every and some evaluate predicates over direct children", () => {
    /** Verifies: PC-TRV-008 */
    const tree = sample();
    expect(tree.every((n) => (n.type as string) !== "font")).toBe(true);
    expect(tree.some((n) => n.type === "comment")).toBe(true);
    expect(tree.some((n) => (n.type as string) === "font")).toBe(false);
  });

  test("structural reads: first, last, index, next, prev, root", () => {
    /** Verifies: PC-TRV-005, PC-CVI-003 */
    const tree = sample();
    expect(tree.first).toBe(tree.nodes[0]);
    expect(tree.last).toBe(tree.nodes[tree.nodes.length - 1]);
    expect(tree.index(tree.nodes[2])).toBe(2);
    expect(tree.nodes[0].next()).toBe(tree.nodes[1]);
    expect(tree.nodes[1].prev()).toBe(tree.nodes[0]);
    expect(tree.first!.prev()).toBeUndefined();
    expect(tree.last!.next()).toBeUndefined();
    const deep = ((tree.nodes[1] as AtRule).first as Rule).first!;
    expect(deep.root()).toBe(tree);
  });

  test("replaceWith substitutes nodes and descriptors in place", () => {
    /** Verifies: PC-TRV-006 */
    const tree = parse("a { color: red }");
    ((tree.first as Rule).first as Declaration).replaceWith(
      decl({ prop: "top", value: "1" }),
      decl({ prop: "left", value: "2" }),
    );
    expect(tree.toString()).toBe("a { top: 1; left: 2 }");
    const viaDescriptor = parse("a{x:1}");
    ((viaDescriptor.first as Rule).first as Declaration).replaceWith({ prop: "y", value: "2" });
    expect(viaDescriptor.toString()).toBe("a{y: 2}");
  });

  test("remove, removeChild, and removeAll detach nodes", () => {
    /** Verifies: PC-TRV-007 */
    const tree = parse("a{x:1;y:2}");
    const r = tree.first as Rule;
    const x = r.first!;
    x.remove();
    expect(tree.toString()).toBe("a{y:2}");
    expect(x.parent).toBeUndefined();
    r.removeAll();
    expect(r.nodes).toEqual([]);
    expect(tree.toString()).toBe("a{}");
    const other = parse("a{m:1;n:2}");
    (other.first as Rule).removeChild((other.first as Rule).nodes[1]);
    expect(other.toString()).toBe("a{m:1}");
  });
});

describe("values and selectors", () => {
  test("selectors splits on commas with trimming", () => {
    /** Verifies: PC-VAL-001 */
    const r = parse("a:hover,  b { color: red }").first as Rule;
    expect(r.selectors).toEqual(["a:hover", "b"]);
  });

  test("assigning selectors reuses the existing separator style", () => {
    /** Verifies: PC-VAL-001 */
    const r = parse("a, b { color: red }").first as Rule;
    r.selectors = ["i", "u"];
    expect(r.selector).toBe("i, u");
    expect(r.toString()).toBe("i, u { color: red }");
  });

  test("list.space splits on top-level whitespace only", () => {
    /** Verifies: PC-VAL-002 */
    expect(list.space("1px calc(10% + 1px) 'a b'")).toEqual(["1px", "calc(10% + 1px)", "'a b'"]);
  });

  test("list.comma splits on top-level commas only", () => {
    /** Verifies: PC-VAL-002 */
    expect(list.comma("black, linear-gradient(white, black), a")).toEqual([
      "black",
      "linear-gradient(white, black)",
      "a",
    ]);
    expect(list.comma("a,")).toEqual(["a", ""]);
  });

  test("list.split honors the trailing-item flag", () => {
    /** Verifies: PC-VAL-003 */
    expect(list.split("a;b;c", [";"], true)).toEqual(["a", "b", "c"]);
    expect(list.split("a b ", [" "], false)).toEqual(["a", "b"]);
    expect(list.split("a b ", [" "], true)).toEqual(["a", "b", ""]);
  });

  test("canonical important parses to true and reprints", () => {
    /** Verifies: PC-VAL-004 */
    const css = "a{color:red !important}";
    const tree = parse(css);
    expect(((tree.first as Rule).first as Declaration).important).toBe(true);
    expect(tree.toString()).toBe(css);
  });
});

describe("cloning and json", () => {
  test("clone returns a detached deep copy applying overrides", () => {
    /** Verifies: PC-CLN-001 */
    const tree = parse("a { color: red }");
    const original = (tree.first as Rule).first as Declaration;
    const copy = original.clone({ value: "blue" }) as Declaration;
    expect(copy.prop).toBe("color");
    expect(copy.value).toBe("blue");
    expect(copy.parent).toBeUndefined();
    expect(copy.source).toBe(original.source);
    expect(original.value).toBe("red");
  });

  test("a clone of an unmodified node prints identically", () => {
    /** Verifies: PC-CLN-001, PC-CVI-006 */
    const tree = parse("a /* s */ b { color : red }");
    const copy = (tree.first as Rule).clone() as Rule;
    expect(copy.toString()).toBe((tree.first as Rule).toString());
    expect(copy.raws.selector).toEqual({ raw: "a /* s */ b", value: "a  b" });
  });

  test("cloneBefore and cloneAfter insert the copy and return it", () => {
    /** Verifies: PC-CLN-002 */
    const tree = parse("a { color: red }");
    const original = (tree.first as Rule).first as Declaration;
    const before = original.cloneBefore({ prop: "border" }) as Declaration;
    expect(tree.toString()).toBe("a { border: red; color: red }");
    expect(before.parent).toBe(tree.first);
    const after = original.cloneAfter({ prop: "outline" }) as Declaration;
    expect(after).toBe((tree.first as Rule).nodes[2]);
    expect(tree.toString()).toBe("a { border: red; color: red; outline: red }");
  });

  test("toJSON produces plain data with a root-level inputs array", () => {
    /** Verifies: PC-CLN-003 */
    const json = parse("a { color: red }", { from: "/j/f.css" }).toJSON() as Record<string, unknown>;
    expect(json.type).toBe("root");
    expect(Array.isArray(json.nodes)).toBe(true);
    const inputs = json.inputs as Array<Record<string, unknown>>;
    expect(inputs.length).toBe(1);
    expect(inputs[0].css).toBe("a { color: red }");
    expect(inputs[0].hasBOM).toBe(false);
    expect(inputs[0].file).toBe("/j/f.css");
  });

  test("fromJSON revives nodes that print identically with working sources", () => {
    /** Verifies: PC-CLN-004, PC-CVI-001 */
    const css = "a /* s */ b {\n  color : red !important;\n}\n";
    const revived = fromJSON(parse(css).toJSON()) as Root;
    expect(revived instanceof Root).toBe(true);
    expect(revived.toString()).toBe(css);
    expect((revived.first as Rule).source!.input.css).toBe(css);
    expect(((revived.first as Rule).first as Declaration).prop).toBe("color");
  });
});
