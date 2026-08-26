// Oracle atomic tests — processors, plugin pipeline, results, warnings,
// positions, and error construction for the postcss engine.
import { describe, expect, test } from "vitest";
import postcss, {
  CssSyntaxError,
  Declaration,
  Input,
  Processor,
  Result,
  Root,
  Rule,
  Warning,
  decl,
  parse,
} from "postcss";

const passthrough = { postcssPlugin: "passthrough", Once() {} };

describe("processor construction", () => {
  test("the default export builds a Processor from plugins or arrays", () => {
    /** Verifies: PC-PRC-001 */
    const a = { postcssPlugin: "a", Once() {} };
    const b = { postcssPlugin: "b", Once() {} };
    expect(postcss(a, b) instanceof Processor).toBe(true);
    expect(postcss(a, b).plugins.length).toBe(2);
    expect(postcss([a, b]).plugins.length).toBe(2);
    expect(postcss().plugins).toEqual([]);
  });

  test("Processor is constructible and use appends plugins", () => {
    /** Verifies: PC-PRC-001 */
    const proc = new Processor();
    const returned = proc.use(passthrough);
    expect(returned).toBe(proc);
    expect(proc.plugins.length).toBe(1);
  });

  test("version reports a version string", () => {
    /** Verifies: PC-PRC-001 */
    expect(typeof postcss().version).toBe("string");
    expect(postcss().version.length).toBeGreaterThan(0);
  });

  test("a creator function with postcss=true is invoked without arguments", () => {
    /** Verifies: PC-PRC-002 */
    const creator = (opts: { v?: number } = {}) => ({
      postcssPlugin: "creator",
      Once(tree: Root) {
        tree.append(`x{y:${opts.v ?? 0}}`);
      },
    });
    creator.postcss = true as const;
    expect(postcss([creator]).process("a{}", { from: "i.css" }).css).toBe("a{}x{y:0}");
    expect(postcss([creator({ v: 9 })]).process("a{}", { from: "i.css" }).css).toBe("a{}x{y:9}");
  });

  test("prepare returns listeners scoped to the run", () => {
    /** Verifies: PC-PRC-003 */
    const prep = {
      postcssPlugin: "prep",
      prepare(result: Result) {
        const from = result.opts.from;
        return {
          Once(tree: Root) {
            tree.append(`/* ${from?.split("/").pop()} */`);
          },
        };
      },
    };
    expect(postcss([prep]).process("a{}", { from: "/x/y/in.css" }).css).toBe("a{}/* in.css */");
    expect(postcss([prep]).process("a{}", { from: "/x/y/other.css" }).css).toBe("a{}/* other.css */");
  });
});

describe("lazy result lifecycle", () => {
  test("awaiting a processed run resolves to a Result", async () => {
    /** Verifies: PC-PRC-004 */
    const result = await postcss([passthrough]).process("a{color:red}", { from: "i.css" });
    expect(result instanceof Result).toBe(true);
    expect(result.css).toBe("a{color:red}");
  });

  test("synchronous reads run the pipeline and sync/async return the Result", async () => {
    /** Verifies: PC-PRC-004 */
    const upper = {
      postcssPlugin: "upper",
      Declaration(d: Declaration) {
        if (d.value === "red") d.value = "crimson";
      },
    };
    expect(postcss([upper]).process("a{color:red}", { from: "i.css" }).css).toBe("a{color:crimson}");
    expect(postcss([upper]).process("a{color:red}", { from: "i.css" }).sync() instanceof Result).toBe(true);
    const viaAsync = await postcss([upper]).process("a{color:red}", { from: "i.css" }).async();
    expect(viaAsync instanceof Result).toBe(true);
    expect(viaAsync.css).toBe("a{color:crimson}");
  });

  test("reading root synchronously exposes the processed tree", () => {
    /** Verifies: PC-PRC-004 */
    const lazy = postcss([passthrough]).process("a{color:red}", { from: "i.css" });
    expect(lazy.root instanceof Root).toBe(true);
    expect(lazy.root.toString()).toBe("a{color:red}");
  });

  test("an asynchronous plugin forbids synchronous access but awaits fine", async () => {
    /** Verifies: PC-PRC-005 */
    const asyncPlugin = {
      postcssPlugin: "ap",
      async Once(tree: Root) {
        await new Promise((resolve) => setTimeout(resolve, 1));
        tree.append("b{}");
      },
    };
    const lazy = postcss([asyncPlugin]).process("a{}", { from: "i.css" });
    expect(() => lazy.css).toThrow(Error);
    const lazy2 = postcss([asyncPlugin]).process("a{}", { from: "i.css" });
    expect(() => lazy2.sync()).toThrow(Error);
    const result = await postcss([asyncPlugin]).process("a{}", { from: "i.css" });
    expect(result.css).toBe("a{}b{}");
  });

  test("the plugin-free fast path returns input text without parsing", () => {
    /** Verifies: PC-PRC-006 */
    const lazy = postcss().process("NOT VALID {", { from: "i.css" }); /* } */
    expect(lazy.css).toBe("NOT VALID {"); /* } */
    expect(lazy.content).toBe("NOT VALID {"); /* } */
    expect(() => lazy.root).toThrow(CssSyntaxError);
  });

  test("the plugin-free fast path still resolves to a full Result", async () => {
    /** Verifies: PC-PRC-006 */
    const result = await postcss().process("a{color:red}", { from: "i.css" });
    expect(result instanceof Result).toBe(true);
    expect(result.css).toBe("a{color:red}");
    expect(result.root.type).toBe("root");
    const valid = postcss().process("a{color:red}", { from: "i.css" });
    expect(valid.root instanceof Root).toBe(true);
  });

  test("process accepts an existing Root without reparsing", () => {
    /** Verifies: PC-PRC-013 */
    const tree = parse("a{color:red}");
    const recolor = {
      postcssPlugin: "recolor",
      Declaration(d: Declaration) {
        if (d.value === "red") d.value = "blue";
      },
    };
    const lazy = postcss([recolor]).process(tree, { from: "i.css" });
    expect(lazy.css).toBe("a{color:blue}");
    expect(lazy.root).toBe(tree);
  });

  test("process accepts any object with a toString method", () => {
    /** Verifies: PC-PRC-013 */
    const source = { toString: () => "a{top:0}" };
    expect(postcss([passthrough]).process(source, { from: "i.css" }).css).toBe("a{top:0}");
  });
});

describe("visitor events", () => {
  test("Once fires before per-node events, exits after children, OnceExit last", () => {
    /** Verifies: PC-PRC-007 */
    const order: string[] = [];
    const spy = {
      postcssPlugin: "spy",
      Once(tree: Root) {
        order.push(`Once:${tree.nodes.length}`);
      },
      Rule(r: Rule) {
        order.push(`Rule:${r.selector}`);
      },
      Declaration(d: Declaration) {
        order.push(`Decl:${d.prop}`);
      },
      RuleExit(r: Rule) {
        order.push(`RuleExit:${r.selector}`);
      },
      OnceExit() {
        order.push("OnceExit");
      },
    };
    postcss([spy]).process("a{color:red;top:0}b{left:1px}", { from: "i.css" }).css;
    expect(order).toEqual([
      "Once:2",
      "Rule:a",
      "Decl:color",
      "Decl:top",
      "RuleExit:a",
      "Rule:b",
      "Decl:left",
      "RuleExit:b",
      "OnceExit",
    ]);
  });

  test("AtRule and Comment listeners fire for their node types", () => {
    /** Verifies: PC-PRC-007 */
    const seen: string[] = [];
    const spy = {
      postcssPlugin: "spy",
      AtRule(a: { name: string }) {
        seen.push(`at:${a.name}`);
      },
      Comment(c: { text: string }) {
        seen.push(`comment:${c.text}`);
      },
    };
    postcss([spy]).process("@media x { a{} }\n/* note */", { from: "i.css" }).css;
    expect(seen).toEqual(["at:media", "comment:note"]);
  });

  test("keyed Declaration listeners fire alongside the star listener", () => {
    /** Verifies: PC-PRC-008 */
    const hits: string[] = [];
    const keyed = {
      postcssPlugin: "keyed",
      Declaration: {
        "*": (d: Declaration) => {
          hits.push(`any:${d.prop}`);
        },
        color: (d: Declaration) => {
          hits.push(`color=${d.value}`);
        },
      },
    };
    postcss([keyed]).process("a{color:red;top:0}", { from: "i.css" }).css;
    expect(hits.slice().sort()).toEqual(["any:color", "any:top", "color=red"]);
  });

  test("keyed AtRule listeners match by name", () => {
    /** Verifies: PC-PRC-008 */
    const names: string[] = [];
    const keyed = {
      postcssPlugin: "keyed",
      AtRule: {
        media: (a: { params: string }) => {
          names.push(`media:${a.params}`);
        },
      },
    };
    postcss([keyed]).process("@media x {}\n@layer y;", { from: "i.css" }).css;
    expect(names).toEqual(["media:x"]);
  });

  test("listeners receive a helper object carrying the result", () => {
    /** Verifies: PC-PRC-009 */
    let captured: unknown;
    const grab = {
      postcssPlugin: "grab",
      Declaration(_d: Declaration, helpers: { result: Result }) {
        captured = helpers.result;
      },
    };
    const lazy = postcss([grab]).process("a{color:red}", { from: "i.css" });
    lazy.css;
    expect(captured instanceof Result).toBe(true);
    expect((captured as Result).opts.from).toBe("i.css");
  });

  test("a mutated declaration is revisited in the same run", () => {
    /** Verifies: PC-PRC-010 */
    const log: string[] = [];
    const mutator = {
      postcssPlugin: "mutator",
      Declaration(d: Declaration) {
        log.push(`${d.prop}=${d.value}`);
        if (d.value === "red") d.value = "blue";
      },
    };
    const out = postcss([mutator]).process("a{color:red}", { from: "i.css" }).css;
    expect(log).toEqual(["color=red", "color=blue"]);
    expect(out).toBe("a{color:blue}");
  });

  test("nodes inserted during the run are visited", () => {
    /** Verifies: PC-PRC-010 */
    const visited: string[] = [];
    const inserter = {
      postcssPlugin: "inserter",
      Declaration(d: Declaration) {
        visited.push(d.prop);
        if (d.prop === "color") d.cloneBefore({ prop: "-x-color" });
      },
    };
    const out = postcss([inserter]).process("a{color:red}", { from: "i.css" }).css;
    expect(visited.slice().sort()).toEqual(["-x-color", "color"]);
    expect(out).toBe("a{-x-color:red;color:red}");
  });

  test("toResult produces a synchronous Result over the same root", () => {
    /** Verifies: PC-PRC-011 */
    const tree = parse("a{color:red}");
    const result = tree.toResult();
    expect(result instanceof Result).toBe(true);
    expect(result.root).toBe(tree);
    expect(result.css).toBe("a{color:red}");
    expect(tree.toResult({ to: "out.css" }).opts.to).toBe("out.css");
  });

  test("a node error thrown inside a listener carries the plugin name", () => {
    /** Verifies: PC-PRC-012 */
    const thrower = {
      postcssPlugin: "thrower",
      Once(tree: Root) {
        throw tree.first!.error("bad node", { word: "color" });
      },
    };
    let caught: CssSyntaxError | undefined;
    try {
      postcss([thrower]).process("a{color:red}", { from: "i.css" }).css;
    } catch (error) {
      caught = error as CssSyntaxError;
    }
    expect(caught instanceof CssSyntaxError).toBe(true);
    expect(caught!.plugin).toBe("thrower");
    expect(caught!.reason).toBe("bad node");
    expect(caught!.line).toBe(1);
    expect(caught!.column).toBe(3);
  });
});

describe("results, warnings, and messages", () => {
  test("result exposes css, content alias, root, opts, processor, toString", () => {
    /** Verifies: PC-RES-001 */
    const proc = postcss([passthrough]);
    const lazy = proc.process("a{}", { from: "/r/in.css", to: "/r/out.css" });
    const css = lazy.css;
    const result = lazy.sync();
    expect(css).toBe("a{}");
    expect(result.content).toBe(result.css);
    expect(result.root.type).toBe("root");
    expect(result.opts.from).toBe("/r/in.css");
    expect(result.opts.to).toBe("/r/out.css");
    expect(result.processor).toBe(proc);
    expect(result.toString()).toBe(result.css);
  });

  test("warnings returns exactly the messages typed warning", () => {
    /** Verifies: PC-RES-002, PC-CVI-002 */
    const mixed = {
      postcssPlugin: "mixed",
      Once(tree: Root, { result }: { result: Result }) {
        result.warn("first note");
        result.messages.push({ type: "dependency", plugin: "mixed", file: "x.css", parent: "" });
        tree.first!.warn(result, "second note");
      },
    };
    const result = postcss([mixed]).process("a{}", { from: "i.css" }).sync();
    expect(result.messages.length).toBe(3);
    expect(result.warnings().length).toBe(2);
    expect(result.warnings()).toEqual(result.messages.filter((m) => m.type === "warning"));
  });

  test("node.warn anchors a Warning with positions narrowed by word", () => {
    /** Verifies: PC-RES-003, PC-RES-004 */
    const warner = {
      postcssPlugin: "warner",
      Declaration(d: Declaration, { result }: { result: Result }) {
        if (d.prop === "bad") d.warn(result, "avoid bad", { word: "bad" });
      },
    };
    const result = postcss([warner]).process("a{bad:1}", { from: "/w/in.css" }).sync();
    const warning = result.warnings()[0] as Warning;
    expect(warning instanceof Warning).toBe(true);
    expect(warning.type).toBe("warning");
    expect(warning.text).toBe("avoid bad");
    expect(warning.plugin).toBe("warner");
    expect(warning.line).toBe(1);
    expect(warning.column).toBe(3);
    expect(warning.endLine).toBe(1);
    expect(warning.endColumn).toBe(6);
  });

  test("a result-level warning has no position fields", () => {
    /** Verifies: PC-RES-003, PC-RES-005 */
    const bare = {
      postcssPlugin: "bare",
      Once(_tree: Root, { result }: { result: Result }) {
        result.warn("free-floating");
      },
    };
    const warning = postcss([bare]).process("a{}", { from: "i.css" }).sync().warnings()[0];
    expect(warning.text).toBe("free-floating");
    expect(warning.plugin).toBe("bare");
    expect(warning.line).toBeUndefined();
    expect(warning.column).toBeUndefined();
    expect(warning.node).toBeUndefined();
  });

  test("Warning toString includes plugin, position identifier, and text", () => {
    /** Verifies: PC-RES-006 */
    const warner = {
      postcssPlugin: "warner",
      Once(tree: Root, { result }: { result: Result }) {
        tree.first!.warn(result, "anchored");
        result.warn("floating");
      },
    };
    const warnings = postcss([warner]).process("a{}", { from: "/w/in.css" }).sync().warnings();
    expect(warnings[0].toString()).toBe("warner: /w/in.css:1:1: anchored");
    expect(warnings[1].toString()).toBe("warner: floating");
  });
});

describe("positions and error construction", () => {
  test("positionBy resolves word, index, and default positions", () => {
    /** Verifies: PC-POS-001, PC-CVI-004 */
    const d = (parse("a { color: notacolor }").first as Rule).first as Declaration;
    expect(d.positionBy({ word: "notacolor" })).toEqual({ line: 1, column: 12, offset: 11 });
    expect(d.positionBy({ index: 7 })).toEqual({ line: 1, column: 12, offset: 11 });
    expect(d.positionBy({})).toEqual({ line: 1, column: 5, offset: 4 });
    expect(d.positionBy({})).toEqual(d.source!.start);
  });

  test("rangeBy covers a word exactly or the whole node", () => {
    /** Verifies: PC-POS-002, PC-CVI-004 */
    const d = (parse("a { color: notacolor }").first as Rule).first as Declaration;
    expect(d.rangeBy({ word: "notacolor" })).toEqual({
      start: { line: 1, column: 12, offset: 11 },
      end: { line: 1, column: 21, offset: 20 },
    });
    const whole = d.rangeBy({});
    expect(whole.start).toEqual({ line: 1, column: 5, offset: 4 });
    expect(whole.end).toEqual({ line: 1, column: d.source!.end!.column + 1, offset: d.source!.end!.offset });
  });

  test("fromOffset converts offsets to line and col", () => {
    /** Verifies: PC-POS-003, PC-CVI-004 */
    const input = new Input("ab\ncd\ne");
    expect(input.fromOffset(0)).toEqual({ line: 1, col: 1 });
    expect(input.fromOffset(3)).toEqual({ line: 2, col: 1 });
    expect(input.fromOffset(6)).toEqual({ line: 3, col: 1 });
    const d = (parse("a {\n  color: red\n}").first as Rule).first as Declaration;
    expect(d.source!.input.fromOffset(d.source!.start!.offset)!.line).toBe(d.source!.start!.line);
  });

  test("node.error returns a positioned CssSyntaxError without throwing", () => {
    /** Verifies: PC-POS-004 */
    const d = (parse("a { color: notacolor }", { from: "/e/x.css" }).first as Rule).first as Declaration;
    const whole = d.error("unknown color");
    expect(whole instanceof CssSyntaxError).toBe(true);
    expect(whole.line).toBe(1);
    expect(whole.column).toBe(5);
    expect(whole.endLine).toBe(1);
    expect(whole.endColumn).toBe(21);
    const byWord = d.error("unknown color", { word: "notacolor" });
    expect(byWord.line).toBe(1);
    expect(byWord.column).toBe(12);
    expect(byWord.file).toBe("/e/x.css");
    const byIndex = d.error("idx", { index: 7 });
    expect(byIndex.column).toBe(12);
  });

  test("input.error builds an error at an explicit position", () => {
    /** Verifies: PC-POS-005 */
    const input = new Input("a{}", { from: "/e/z.css" });
    const error = input.error("bad", 1, 2);
    expect(error instanceof CssSyntaxError).toBe(true);
    expect(error.line).toBe(1);
    expect(error.column).toBe(2);
    expect(error.file).toBe("/e/z.css");
  });

  test("a sourceless node still manufactures an error without positions", () => {
    /** Verifies: PC-POS-006 */
    const error = decl({ prop: "a", value: "b" }).error("no source");
    expect(error instanceof CssSyntaxError).toBe(true);
    expect(error.line).toBeUndefined();
    expect(error.column).toBeUndefined();
  });
});

describe("parse errors", () => {
  test("unclosed block", () => {
    /** Verifies: PC-ERR-001 */
    let caught: CssSyntaxError | undefined;
    try {
      parse("a {"); /* } */
    } catch (error) {
      caught = error as CssSyntaxError;
    }
    expect(caught instanceof CssSyntaxError).toBe(true);
    expect(caught!.name).toBe("CssSyntaxError");
    expect(caught!.line).toBe(1);
    expect(caught!.column).toBe(1);
    expect(caught!.source).toBe("a {"); /* } */
  });

  test("stray closing brace, unclosed comment, unclosed string, unknown word", () => {
    /** Verifies: PC-ERR-001 */
    const positions: Array<[number, number]> = [];
    for (const css of ["}", "/* unclosed", 'a { content: "x }', "a { color red }"]) { /* { */
      try {
        parse(css);
        positions.push([-1, -1]);
      } catch (error) {
        positions.push([(error as CssSyntaxError).line!, (error as CssSyntaxError).column!]);
      }
    }
    expect(positions).toEqual([
      [1, 1],
      [1, 1],
      [1, 14],
      [1, 5],
    ]);
  });

  test("error anatomy: message combines identifier, position, and reason", () => {
    /** Verifies: PC-ERR-002 */
    let generic: CssSyntaxError | undefined;
    try {
      parse("a {"); /* } */
    } catch (error) {
      generic = error as CssSyntaxError;
    }
    expect(generic!.message).toBe(`<css input>:1:1: ${generic!.reason}`);
    expect(generic! instanceof Error).toBe(true);
    let filed: CssSyntaxError | undefined;
    try {
      parse("a {", { from: "/p/broken.css" }); /* } */
    } catch (error) {
      filed = error as CssSyntaxError;
    }
    expect(filed!.message).toBe(`/p/broken.css:1:1: ${filed!.reason}`);
    expect(filed!.file).toBe("/p/broken.css");
  });

  test("a ranged parse error carries end coordinates", () => {
    /** Verifies: PC-ERR-002 */
    let caught: CssSyntaxError | undefined;
    try {
      parse("a { color red }");
    } catch (error) {
      caught = error as CssSyntaxError;
    }
    expect(caught!.line).toBe(1);
    expect(caught!.column).toBe(5);
    expect(caught!.endLine).toBe(1);
    expect(caught!.endColumn).toBe(10);
  });

  test("showSourceCode renders an uncolored frame and toString embeds it", () => {
    /** Verifies: PC-ERR-003 */
    let caught: CssSyntaxError | undefined;
    try {
      parse("a {\n  color: red\n"); /* } */
    } catch (error) {
      caught = error as CssSyntaxError;
    }
    const frame = caught!.showSourceCode(false);
    expect(frame).toContain("> 1 | a {"); /* } */
    expect(frame).toContain("    | ^");
    expect(frame).toContain("  2 |   color: red");
    const printed = caught!.toString();
    expect(printed.startsWith(`CssSyntaxError: ${caught!.message}`)).toBe(true);
    expect(printed).toContain("> 1 | a {"); /* } */
  });
});
