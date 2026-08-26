// Oracle system tests — full user sessions across parsing, pipeline,
// results, errors, and serialization for the postcss engine.
import { describe, expect, test } from "vitest";
import postcss, {
  CssSyntaxError,
  Declaration,
  Result,
  Root,
  Rule,
  fromJSON,
  parse,
} from "postcss";

describe("system workflows", () => {
  test("a lint-and-fix session: warnings, fixes, and coherent output", async () => {
    /** Verifies: PC-PRC-004, PC-RES-002, PC-RES-004, PC-CVI-002, PC-CVI-007 */
    const source = [
      "a {", /* } */
      "  color: red;",
      "  z-index: 9999;",
      "}", /* { */
      "@media (min-width: 10px) {", /* } */
      "  b { color: red }",
      "}", /* { */
      "",
    ].join("\n");
    const noRed = {
      postcssPlugin: "no-red",
      Declaration(d: Declaration, { result }: { result: Result }) {
        if (d.value === "red") {
          d.warn(result, "red is banned", { word: "red" });
          d.value = "crimson";
        }
      },
    };
    const zCap = {
      postcssPlugin: "z-cap",
      Declaration(d: Declaration, { result }: { result: Result }) {
        if (d.prop === "z-index" && Number(d.value) > 100) {
          d.warn(result, "z-index too large");
          d.value = "100";
        }
      },
    };
    const result = await postcss([noRed, zCap]).process(source, { from: "/app/styles.css" });
    expect(result.css).toBe(source.replace(/red/g, "crimson").replace("9999", "100"));
    expect(result.css).toBe(result.root.toString());
    const warnings = result.warnings();
    expect(warnings.map((w) => `${w.plugin}:${w.text}`)).toEqual([
      "no-red:red is banned",
      "z-cap:z-index too large",
      "no-red:red is banned",
    ]);
    expect(warnings[0].toString()).toBe("no-red: /app/styles.css:2:10: red is banned");
    for (const w of warnings) {
      expect(w.node).toBeDefined();
      expect(w.node!.root().toString()).toBe(result.root.toString());
    }
  });

  test("a refactor session: move, clone, edit, and serialize one stylesheet", () => {
    /** Verifies: PC-CVI-001, PC-CVI-005, PC-CVI-006, PC-BLD-006, PC-CLN-004 */
    const source = "/* theme */\n.btn {\n  color : red;\n  border: 1px solid red;\n}\n.card { padding: 1rem }\n";
    const tree = parse(source, { from: "/ui/theme.css" });
    expect(tree.toString()).toBe(source);

    const btn = tree.nodes[1] as Rule;
    const dark = btn.clone() as Rule;
    dark.selector = ".btn-dark";
    dark.walkDecls("color", (d) => {
      d.value = "white";
    });
    tree.insertAfter(btn, dark);

    (btn.first as Declaration).value = "blue";

    const printed = tree.toString();
    expect(printed).toContain(".btn {\n  color : blue;\n  border: 1px solid red;\n}");
    expect(printed).toContain(".btn-dark {\n  color : white;\n  border: 1px solid red;\n}");
    expect(printed).toContain(".card { padding: 1rem }");

    const revived = fromJSON(tree.toJSON()) as Root;
    expect(revived.toString()).toBe(printed);
    expect(parse(printed).toString()).toBe(printed);
  });

  test("a scratch build processed end to end through a processor", async () => {
    /** Verifies: PC-BLD-001, PC-STR-004, PC-PRC-011, PC-CVI-002 */
    const tree = postcss.root();
    const reset = postcss.rule({ selector: "*" });
    reset.append({ prop: "margin", value: "0" }, { prop: "padding", value: "0" });
    tree.append(reset);
    const media = postcss.atRule({ name: "media", params: "print" });
    media.append(postcss.rule({ selector: "nav" }));
    (media.first as Rule).append({ prop: "display", value: "none" });
    tree.append(media);

    const direct = tree.toResult();
    expect(direct.root).toBe(tree);
    expect(direct.css).toBe("* {\n    margin: 0;\n    padding: 0\n}\n@media print {\n    nav {\n        display: none\n    }\n}");

    const important = {
      postcssPlugin: "important",
      Declaration(d: Declaration) {
        if (d.prop === "display") d.important = true;
      },
    };
    const result = await postcss([important]).process(tree, { from: "gen.css" });
    expect(result.root).toBe(tree);
    expect(result.css).toContain("display: none !important");
    expect(result.css).toBe(tree.toString());
  });

  test("an error recovery session: diagnose a broken file, fix it, process it", async () => {
    /** Verifies: PC-ERR-001, PC-ERR-002, PC-ERR-003, PC-PRC-006 */
    const broken = "a {\n  color: red\n"; /* } */
    let diagnosis: CssSyntaxError | undefined;
    try {
      parse(broken, { from: "/site/broken.css" });
    } catch (error) {
      diagnosis = error as CssSyntaxError;
    }
    expect(diagnosis instanceof CssSyntaxError).toBe(true);
    expect(diagnosis!.file).toBe("/site/broken.css");
    expect(diagnosis!.message).toBe(`/site/broken.css:1:1: ${diagnosis!.reason}`);
    expect(diagnosis!.showSourceCode(false)).toContain("> 1 | a {"); /* } */

    const fastPath = postcss().process(broken, { from: "/site/broken.css" });
    expect(fastPath.css).toBe(broken);
    expect(() => fastPath.root).toThrow(CssSyntaxError);

    const fixed = broken + "}"; /* { */
    const tree = parse(fixed, { from: "/site/broken.css" });
    const result = await postcss([{ postcssPlugin: "noop", Once() {} }]).process(tree, { from: "/site/broken.css" });
    expect(result.css).toBe(fixed);
    expect(result.warnings()).toEqual([]);
  });

  test("a multi-file session: one document aggregates independently parsed sheets", () => {
    /** Verifies: PC-STR-007, PC-PAR-002, PC-CVI-003 */
    const doc = postcss.document();
    const base = parse("body { margin: 0 }\n", { from: "/css/base.css" });
    const theme = parse(".dark { background: black }\n", { from: "/css/theme.css" });
    doc.append(base, theme);
    expect(doc.toString()).toBe("body { margin: 0 }\n.dark { background: black }\n");
    expect(base.parent).toBe(doc);
    const files: string[] = [];
    doc.walkRules((r) => {
      files.push(r.source!.input.file!);
      expect(r.root()).toBe(doc.nodes[files.length - 1]);
    });
    expect(files).toEqual(["/css/base.css", "/css/theme.css"]);
  });
});
