// Oracle integration tests — cross-view workflows for the postcss engine.
import { describe, expect, test } from "vitest";
import postcss, {
  AtRule,
  Comment,
  CssSyntaxError,
  Declaration,
  Document,
  Result,
  Root,
  Rule,
  decl,
  fromJSON,
  parse,
  root,
  rule,
} from "postcss";

const complexCss = [
  "/* banner */",
  "@charset \"utf-8\";",
  "@media (min-width: 10px) and (max-width: 100px) {", /* } */
  "  a:hover,  b > c {", /* } */
  "    color : red !important;",
  "    --gap:  4px;",
  "  }", /* { */
  "}", /* { */
  "d { margin: 0; padding: calc(1px + 2%) }",
  "",
].join("\n");

describe("round trips", () => {
  test("a complex stylesheet survives parse, JSON, and revival byte for byte", () => {
    /** Verifies: PC-CVI-001, PC-CLN-003, PC-CLN-004 */
    const tree = parse(complexCss);
    expect(tree.toString()).toBe(complexCss);
    const revived = fromJSON(tree.toJSON()) as Root;
    expect(revived.toString()).toBe(complexCss);
    expect(revived.nodes.length).toBe(tree.nodes.length);
  });

  test("read-only traversal never changes the printed output", () => {
    /** Verifies: PC-CVI-001, PC-TRV-003, PC-TRV-004 */
    const tree = parse(complexCss);
    const counts = { rule: 0, decl: 0, atrule: 0, comment: 0 };
    tree.walk((node) => {
      counts[node.type as keyof typeof counts] += 1;
    });
    tree.walkDecls(() => {});
    tree.walkRules(() => {});
    expect(counts).toEqual({ rule: 2, decl: 4, atrule: 2, comment: 1 });
    expect(tree.toString()).toBe(complexCss);
  });

  test("a revived tree accepts further edits and reprints correctly", () => {
    /** Verifies: PC-CLN-004, PC-NOD-005, PC-CVI-001 */
    const revived = fromJSON(parse("a { color: red; top: 0 }").toJSON()) as Root;
    ((revived.first as Rule).first as Declaration).value = "blue";
    (revived.first as Rule).append({ prop: "left", value: "1px" });
    expect(revived.toString()).toBe("a { color: blue; top: 0; left: 1px }");
  });
});

describe("cross-view consistency", () => {
  test("pipeline css equals the final tree's own print after mutations", () => {
    /** Verifies: PC-CVI-002, PC-PRC-010 */
    const rewrite = {
      postcssPlugin: "rewrite",
      Declaration(d: Declaration) {
        if (d.value === "red") d.value = "crimson";
      },
      RuleExit(r: Rule) {
        if (r.selector === "a" && r.nodes.length === 1) r.append({ prop: "outline", value: "none" });
      },
    };
    const lazy = postcss([rewrite]).process("a { color: red }\nb { color: red }", { from: "i.css" });
    const css = lazy.css;
    expect(css).toBe(lazy.root.toString());
    expect(css).toBe("a { color: crimson; outline: none }\nb { color: crimson }");
  });

  test("warning positions agree with the anchor node's own projections", () => {
    /** Verifies: PC-CVI-002, PC-RES-004, PC-POS-001, PC-POS-002 */
    const flag = {
      postcssPlugin: "flag",
      Declaration(d: Declaration, { result }: { result: Result }) {
        if (d.value.includes("!bad")) d.warn(result, "bad marker", { word: "!bad" });
      },
    };
    const result = postcss([flag]).process("a {\n  content: '!' /* x */;\n  filter: !bad\n}", { from: "/c/in.css" }).sync();
    const warnings = result.warnings();
    expect(warnings.length).toBe(1);
    const anchor = warnings[0].node as Declaration;
    const range = anchor.rangeBy({ word: "!bad" });
    expect(warnings[0].line).toBe(range.start.line);
    expect(warnings[0].column).toBe(range.start.column);
    expect(warnings[0].endLine).toBe(range.end.line);
    expect(warnings[0].endColumn).toBe(range.end.column);
    expect(result.warnings()).toEqual(result.messages.filter((m) => m.type === "warning"));
  });

  test("every walked node agrees on root, parent, and index", () => {
    /** Verifies: PC-CVI-003, PC-TRV-005 */
    const tree = parse(complexCss);
    let checked = 0;
    tree.walk((node) => {
      expect(node.root()).toBe(tree);
      const parent = node.parent!;
      expect(parent.nodes![parent.index(node)]).toBe(node);
      checked += 1;
    });
    expect(checked).toBe(9);
    expect(tree.first).toBe(tree.nodes[0]);
    expect(tree.last).toBe(tree.nodes[tree.nodes.length - 1]);
  });

  test("positions project consistently across start, positionBy, and fromOffset", () => {
    /** Verifies: PC-CVI-004, PC-PAR-006, PC-POS-003 */
    const tree = parse(complexCss);
    const input = tree.source!.input;
    tree.walk((node) => {
      expect(node.positionBy({})).toEqual(node.source!.start);
      const from = input.fromOffset(node.source!.start!.offset)!;
      expect(from.line).toBe(node.source!.start!.line);
      expect(from.col).toBe(node.source!.start!.column);
    });
  });

  test("editing one declaration keeps sibling raws and selector caches verbatim", () => {
    /** Verifies: PC-CVI-005, PC-NOD-004 */
    const tree = parse("a /* s */ b {\n  color : red /* v */ ;\n  margin  :  0;\n}");
    const ruleNode = tree.first as Rule;
    (ruleNode.nodes[0] as Declaration).value = "blue";
    expect(tree.toString()).toBe("a /* s */ b {\n  color : blue;\n  margin  :  0;\n}");
    expect(ruleNode.raws.selector!.raw).toBe("a /* s */ b");
    expect((ruleNode.nodes[1] as Declaration).raws.between).toBe("  :  ");
  });

  test("clones stay equivalent while originals move on", () => {
    /** Verifies: PC-CVI-006, PC-CLN-001, PC-TRV-007 */
    const tree = parse("a { color : red }\nb { top: 0 }");
    const original = tree.first as Rule;
    const snapshot = original.clone() as Rule;
    (original.first as Declaration).value = "blue";
    original.remove();
    expect(snapshot.toString()).toBe("a { color : red }");
    expect(tree.toString()).toBe("b { top: 0 }");
  });

  test("one run delivers every node of the final tree including inserted ones", () => {
    /** Verifies: PC-CVI-007, PC-PRC-010 */
    const enterLog: string[] = [];
    const grow = {
      postcssPlugin: "grow",
      Rule(r: Rule) {
        if (r.selector === "a" && !r.some((n) => (n as Declaration).prop === "top")) {
          r.append({ prop: "top", value: "0" });
        }
      },
      Declaration(d: Declaration) {
        enterLog.push(`${d.prop}=${d.value}`);
      },
    };
    const lazy = postcss([grow]).process("a { color: red }\nb { left: 1px }", { from: "i.css" });
    const finalCss = lazy.css;
    const finalProps: string[] = [];
    lazy.root.walkDecls((d) => {
      finalProps.push(`${d.prop}=${d.value}`);
    });
    for (const entry of finalProps) {
      expect(enterLog).toContain(entry);
    }
    expect(finalCss).toBe("a { color: red; top: 0 }\nb { left: 1px }");
  });
});

describe("pipeline workflows", () => {
  test("plugins visit each node in registration order", () => {
    /** Verifies: PC-PRC-007, PC-PRC-001 */
    const log: string[] = [];
    const first = {
      postcssPlugin: "first",
      Declaration(d: Declaration) {
        log.push(`first:${d.prop}`);
      },
    };
    const second = {
      postcssPlugin: "second",
      Declaration(d: Declaration) {
        log.push(`second:${d.prop}`);
      },
    };
    postcss([first, second]).process("a{x:1;y:2}", { from: "i.css" }).css;
    expect(log).toEqual(["first:x", "second:x", "first:y", "second:y"]);
  });

  test("an async pipeline mutates, warns, and resolves coherently", async () => {
    /** Verifies: PC-PRC-005, PC-RES-002, PC-CVI-002 */
    const asyncFix = {
      postcssPlugin: "async-fix",
      async Once(tree: Root, { result }: { result: Result }) {
        await new Promise((resolve) => setTimeout(resolve, 1));
        tree.walkDecls("color", (d) => {
          d.warn(result, "recolored");
          d.value = "navy";
        });
      },
    };
    const result = await postcss([asyncFix]).process("a{color:red}b{color:red}", { from: "i.css" });
    expect(result.css).toBe("a{color:navy}b{color:navy}");
    expect(result.css).toBe(result.root.toString());
    expect(result.warnings().map((w) => w.plugin)).toEqual(["async-fix", "async-fix"]);
  });

  test("creator, prepare, and plain object plugins compose in one processor", () => {
    /** Verifies: PC-PRC-002, PC-PRC-003, PC-PRC-001 */
    const banner = (opts: { text: string }) => ({
      postcssPlugin: "banner",
      Once(tree: Root) {
        tree.prepend({ text: opts.text });
      },
    });
    banner.postcss = true as const;
    const stamped = {
      postcssPlugin: "stamped",
      prepare(result: Result) {
        return {
          OnceExit(tree: Root) {
            tree.append(`/* from ${result.opts.from} */`);
          },
        };
      },
    };
    const upper = {
      postcssPlugin: "upper",
      Declaration(d: Declaration) {
        d.value = d.value.toUpperCase();
      },
    };
    const css = postcss([banner({ text: "hi" }), stamped, upper]).process("a{x:low}", { from: "in.css" }).css;
    expect(css).toBe("/* hi */\na{x:LOW}/* from in.css */");
  });

  test("a plugin error rejects the awaited pipeline with plugin identity", async () => {
    /** Verifies: PC-PRC-012, PC-ERR-002 */
    const strict = {
      postcssPlugin: "strict",
      Declaration(d: Declaration) {
        if (d.prop === "bad") throw d.error("forbidden property", { word: "bad" });
      },
    };
    let caught: CssSyntaxError | undefined;
    try {
      await postcss([strict]).process("a{\n  bad: 1\n}", { from: "/s/in.css" });
    } catch (error) {
      caught = error as CssSyntaxError;
    }
    expect(caught instanceof CssSyntaxError).toBe(true);
    expect(caught!.plugin).toBe("strict");
    expect(caught!.file).toBe("/s/in.css");
    expect(caught!.line).toBe(2);
    expect(caught!.column).toBe(3);
  });

  test("the fast path and a plugin run agree on printed css for valid input", async () => {
    /** Verifies: PC-PRC-006, PC-PRC-004 */
    const input = "a { color: red }\n@media x { b { top: 0 } }";
    const fast = postcss().process(input, { from: "i.css" });
    const slow = postcss([{ postcssPlugin: "noop", Once() {} }]).process(input, { from: "i.css" });
    expect(fast.css).toBe(input);
    expect(slow.css).toBe(input);
    const fastResult = await fast;
    expect(fastResult.root.toString()).toBe(input);
  });
});

describe("editing workflows", () => {
  test("nodes move between trees keeping their original source input", () => {
    /** Verifies: PC-BLD-006, PC-PAR-002, PC-STR-001 */
    const one = parse("a{x:1}", { from: "/one.css" });
    const two = parse("b{}", { from: "/two.css" });
    const moved = (one.first as Rule).first as Declaration;
    (two.first as Rule).append(moved);
    expect(one.toString()).toBe("a{}");
    expect(two.toString()).toBe("b{x:1}");
    expect(moved.source!.input.file).toBe("/one.css");
    expect(two.source!.input.file).toBe("/two.css");
  });

  test("a walk-driven rewrite touches only matched declarations", () => {
    /** Verifies: PC-TRV-004, PC-CVI-005 */
    const tree = parse("a { color : red; top : 1px }\n@media x { b { color: red } }");
    tree.walkDecls("color", (d) => {
      d.value = "blue";
      d.important = true;
    });
    expect(tree.toString()).toBe("a { color : blue !important; top : 1px }\n@media x { b { color: blue !important } }");
  });

  test("unwrapping an at-rule with replaceWith preserves children order", () => {
    /** Verifies: PC-TRV-006, PC-STR-001 */
    const tree = parse("@media x {\n  a { color: red }\n  b { top: 0 }\n}\nc {}");
    const media = tree.first as AtRule;
    media.replaceWith(...media.nodes!);
    expect(tree.nodes.map((n) => n.type)).toEqual(["rule", "rule", "rule"]);
    expect(tree.nodes.map((n) => (n as Rule).selector)).toEqual(["a", "b", "c"]);
    expect(tree.toString()).toBe("\n  a { color: red }\nb { top: 0 }\nc {}");
  });

  test("factories, insertion, and formatting inheritance build one stylesheet", () => {
    /** Verifies: PC-BLD-001, PC-STR-004, PC-STR-006 */
    const tree = parse("main {\n  display: grid;\n}");
    const extra = rule({ selector: "aside" });
    extra.append(decl({ prop: "color", value: "gray" }));
    tree.append(extra);
    (tree.first as Rule).append({ prop: "gap", value: "1rem" });
    expect(tree.toString()).toBe("main {\n  display: grid;\n  gap: 1rem;\n}\naside {\n  color: gray;\n}");
  });

  test("selector rewrites and structural inserts compose", () => {
    /** Verifies: PC-VAL-001, PC-BLD-005 */
    const tree = parse("a, b { color: red }\nc { top: 0 }");
    const head = tree.first as Rule;
    head.selectors = [...head.selectors, "d"];
    tree.insertBefore(tree.nodes[1], { selector: "between" });
    expect(tree.toString()).toBe("a, b, d { color: red }\nbetween {}\nc { top: 0 }");
  });

  test("a document collects parsed roots and prints their concatenation", () => {
    /** Verifies: PC-STR-007, PC-CVI-001 */
    const doc = new Document();
    const one = parse("a{x:1}\n");
    const two = parse("b{y:2}\n");
    doc.append(one, two);
    expect(doc.toString()).toBe("a{x:1}\nb{y:2}\n");
    const walked: string[] = [];
    doc.walk((node) => {
      walked.push(node.type);
    });
    expect(walked).toEqual(["root", "rule", "decl", "root", "rule", "decl"]);
  });

  test("each-driven pruning with mixed removals prints the survivors", () => {
    /** Verifies: PC-TRV-001, PC-TRV-007 */
    const tree = parse("a{} /* x */ b{} c{} /* y */");
    const kept: string[] = [];
    tree.each((node) => {
      if (node.type === "comment") {
        node.remove();
      } else {
        kept.push((node as Rule).selector);
      }
    });
    expect(kept).toEqual(["a", "b", "c"]);
    expect(tree.toString()).toBe("a{} b{} c{}");
  });
});
