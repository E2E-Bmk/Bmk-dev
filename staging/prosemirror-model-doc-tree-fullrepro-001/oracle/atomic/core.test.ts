// Oracle - atomic tests for the prosemirror-model document-tree specification.
import { describe, expect, test } from "vitest";
import {
  Schema,
  Node,
  Fragment,
  Slice,
  Mark,
  NodeType,
  MarkType,
  ContentMatch,
  ResolvedPos,
  NodeRange,
  ReplaceError,
} from "prosemirror-model";

/** Base schema: doc of blocks, paragraphs/headings of inline, images with a required attr. */
function makeBase(): Schema {
  return new Schema({
    nodes: {
      doc: { content: "block+" },
      paragraph: { group: "block", content: "inline*" },
      heading: { group: "block", content: "inline*", attrs: { level: { default: 1 } } },
      blockquote: { group: "block", content: "block+" },
      horizontal_rule: { group: "block" },
      text: { group: "inline" },
      image: { group: "inline", inline: true, attrs: { src: {}, alt: { default: null } } },
      hard_break: { group: "inline", inline: true },
    },
    marks: {
      em: {},
      strong: {},
      link: { attrs: { href: {}, title: { default: null } } },
      code: { excludes: "_" },
    },
  });
}

/** Content-rule schema: base plus figure/caption/section with structured expressions. */
function makeContent(): Schema {
  return new Schema({
    nodes: {
      doc: { content: "block+" },
      paragraph: { group: "block", content: "inline*" },
      heading: { group: "block", content: "inline*", attrs: { level: { default: 1 } } },
      blockquote: { group: "block", content: "block+" },
      horizontal_rule: { group: "block" },
      text: { group: "inline" },
      image: { group: "inline", inline: true, attrs: { src: {}, alt: { default: null } } },
      hard_break: { group: "inline", inline: true },
      image_block: { attrs: { src: {} } },
      figure: { group: "block", content: "image_block? caption" },
      caption: { content: "inline*" },
      section: { group: "block", content: "heading paragraph+" },
    },
    marks: {
      em: {},
      strong: {},
      link: { attrs: { href: {}, title: { default: null } } },
      code: { excludes: "_" },
    },
  });
}

describe("schema construction", () => {
  test("compiled schema exposes type tables, top node, and spec", () => {
    /** Verifies: PM-SCH-001 */
    const schema = makeBase();
    expect(Object.keys(schema.nodes)).toEqual([
      "doc",
      "paragraph",
      "heading",
      "blockquote",
      "horizontal_rule",
      "text",
      "image",
      "hard_break",
    ]);
    expect(Object.keys(schema.marks)).toEqual(["em", "strong", "link", "code"]);
    expect(schema.topNodeType.name).toBe("doc");
    expect(schema.nodes.paragraph).toBeInstanceOf(NodeType);
    expect(schema.marks.em).toBeInstanceOf(MarkType);
    expect(schema.nodes.paragraph.name).toBe("paragraph");
    expect(schema.nodes.paragraph.schema).toBe(schema);
    expect(schema.marks.em.schema).toBe(schema);
    expect(schema.spec.nodes).toBeTruthy();
    const p = schema.node("paragraph", null, [schema.text("hi")]);
    expect(p.type).toBe(schema.nodes.paragraph);
    expect(p.textContent).toBe("hi");
    expect(p.childCount).toBe(1);
  });

  test("topNode option selects the top-level type", () => {
    /** Verifies: PM-SCH-001 */
    const schema = new Schema({
      topNode: "article",
      nodes: {
        article: { content: "paragraph+" },
        paragraph: { content: "text*" },
        text: {},
      },
    });
    expect(schema.topNodeType.name).toBe("article");
    const doc = schema.node("article", null, [schema.node("paragraph", null, [schema.text("x")])]);
    expect(doc.type.name).toBe("article");
    expect(doc.textContent).toBe("x");
  });

  test("node type flags reflect inline/block/text/leaf/textblock roles", () => {
    /** Verifies: PM-SCH-004 */
    const schema = makeBase();
    const p = schema.nodes.paragraph;
    expect(p.isBlock).toBe(true);
    expect(p.isTextblock).toBe(true);
    expect(p.inlineContent).toBe(true);
    expect(p.isText).toBe(false);
    const textType = schema.nodes.text;
    expect(textType.isText).toBe(true);
    expect(textType.isInline).toBe(true);
    expect(textType.isLeaf).toBe(true);
    expect(textType.isAtom).toBe(true);
    const hr = schema.nodes.horizontal_rule;
    expect(hr.isLeaf).toBe(true);
    expect(hr.isBlock).toBe(true);
    const image = schema.nodes.image;
    expect(image.isInline).toBe(true);
    expect(image.isLeaf).toBe(true);
  });

  test("atom spec flag marks a non-leaf node atomic", () => {
    /** Verifies: PM-SCH-004 */
    const schema = new Schema({
      nodes: {
        doc: { content: "block+" },
        widget: { group: "block", content: "text*", atom: true },
        paragraph: { group: "block", content: "text*" },
        text: {},
      },
    });
    expect(schema.nodes.widget.isAtom).toBe(true);
    const w = schema.node("widget", null, [schema.text("x")]);
    expect(w.isAtom).toBe(true);
    expect(w.isLeaf).toBe(false);
  });

  test("null attribute argument fills defaults and nulls", () => {
    /** Verifies: PM-SCH-005 */
    const schema = makeBase();
    const h = schema.node("heading", null, [schema.text("t")]);
    expect(h.attrs).toEqual({ level: 1 });
    const img = schema.nodes.image.create(null);
    expect(img.attrs).toEqual({ src: null, alt: null });
    expect(schema.nodes.image.create().attrs).toEqual({ src: null, alt: null });
    expect(schema.node("image").attrs).toEqual({ src: null, alt: null });
  });

  test("attribute object omitting a required attribute raises RangeError", () => {
    /** Verifies: PM-SCH-006, PM-ERR-001 */
    const schema = makeBase();
    expect(() => schema.nodes.image.create({})).toThrow(RangeError);
    expect(() => schema.nodes.image.create({ alt: "a" })).toThrow(RangeError);
    const ok = schema.nodes.image.create({ src: "u.png" });
    expect(ok.attrs).toEqual({ src: "u.png", alt: null });
  });

  test("undeclared attribute names are dropped from created values", () => {
    /** Verifies: PM-SCH-006 */
    const schema = makeBase();
    const node = schema.nodes.image.create({ src: "u", bogus: 1 } as never);
    expect(node.attrs).toEqual({ src: "u", alt: null });
    const mark = schema.marks.link.create({ href: "h", bogus: 2 } as never);
    expect(mark.attrs).toEqual({ href: "h", title: null });
  });

  test("hasRequiredAttrs reflects presence of default-less attributes", () => {
    /** Verifies: PM-SCH-007 */
    const schema = makeBase();
    expect(schema.nodes.image.hasRequiredAttrs()).toBe(true);
    expect(schema.nodes.heading.hasRequiredAttrs()).toBe(false);
    expect(schema.nodes.paragraph.hasRequiredAttrs()).toBe(false);
  });

  test("schema.node accepts a name or NodeType and several content forms", () => {
    /** Verifies: PM-SCH-008 */
    const schema = makeBase();
    const byName = schema.node("paragraph", null, [schema.text("a")]);
    expect(byName.type).toBe(schema.nodes.paragraph);
    const byType = schema.node(schema.nodes.paragraph, null, schema.text("via"));
    expect(byType.textContent).toBe("via");
    const fromFragment = schema.nodes.paragraph.create(null, Fragment.from(schema.text("frag")));
    expect(fromFragment.textContent).toBe("frag");
    const empty = schema.node("paragraph");
    expect(empty.childCount).toBe(0);
  });

  test("unknown node type name raises RangeError", () => {
    /** Verifies: PM-SCH-008, PM-ERR-001 */
    const schema = makeBase();
    expect(() => schema.node("nope")).toThrow(RangeError);
  });

  test("schema.text builds text nodes and rejects empty text", () => {
    /** Verifies: PM-SCH-009, PM-ERR-001 */
    const schema = makeBase();
    const t = schema.text("abcd");
    expect(t.isText).toBe(true);
    expect(t.text).toBe("abcd");
    expect(t.nodeSize).toBe(4);
    expect(() => schema.text("")).toThrow(RangeError);
  });

  test("schema.mark builds marks from a name or MarkType", () => {
    /** Verifies: PM-SCH-010 */
    const schema = makeBase();
    const em = schema.mark("em");
    expect(em).toBeInstanceOf(Mark);
    expect(em.type.name).toBe("em");
    const viaType = schema.mark(schema.marks.strong);
    expect(viaType.type).toBe(schema.marks.strong);
    expect(schema.mark("em").eq(schema.mark("em"))).toBe(true);
  });

  test("create skips content validation while createChecked enforces it", () => {
    /** Verifies: PM-SCH-011, PM-ERR-001 */
    const schema = makeBase();
    const loose = schema.nodes.doc.create(null, [schema.text("loose")]);
    expect(loose.childCount).toBe(1);
    expect(() => schema.nodes.doc.createChecked(null, [schema.text("loose")])).toThrow(RangeError);
    const p = schema.node("paragraph", null, [schema.text("ok")]);
    const checked = schema.nodes.doc.createChecked(null, [p]);
    expect(checked.childCount).toBe(1);
  });

  test("createAndFill synthesizes required content", () => {
    /** Verifies: PM-SCH-011, PM-CNT-005 */
    const schema = makeBase();
    const doc = schema.nodes.doc.createAndFill()!;
    expect(doc.toString()).toBe("doc(paragraph)");
    const bq = schema.nodes.blockquote.createAndFill()!;
    expect(bq.toString()).toBe("blockquote(paragraph)");
  });

  test("validContent reports content-rule satisfaction", () => {
    /** Verifies: PM-SCH-012 */
    const schema = makeContent();
    const good = Fragment.from([schema.node("heading"), schema.node("paragraph")]);
    expect(schema.nodes.section.validContent(good)).toBe(true);
    expect(schema.nodes.section.validContent(Fragment.from(schema.node("paragraph")))).toBe(false);
  });

  test("compatibleContent detects shared allowed content", () => {
    /** Verifies: PM-SCH-013 */
    const schema = makeBase();
    expect(schema.nodes.paragraph.compatibleContent(schema.nodes.heading)).toBe(true);
    expect(schema.nodes.paragraph.compatibleContent(schema.nodes.blockquote)).toBe(false);
  });

  test("marks spec strings and defaults govern allowsMarkType", () => {
    /** Verifies: PM-SCH-003, PM-SCH-014 */
    const schema = new Schema({
      nodes: {
        doc: { content: "block+" },
        plain: { group: "block", content: "text*", marks: "" },
        fancy: { group: "block", content: "text*", marks: "em" },
        para: { group: "block", content: "text*" },
        container: { group: "block", content: "para+" },
        underscore: { group: "block", content: "text*", marks: "_" },
        text: {},
      },
      marks: { em: {}, strong: {} },
    });
    expect(schema.nodes.plain.allowsMarkType(schema.marks.em)).toBe(false);
    expect(schema.nodes.fancy.allowsMarkType(schema.marks.em)).toBe(true);
    expect(schema.nodes.fancy.allowsMarkType(schema.marks.strong)).toBe(false);
    expect(schema.nodes.para.allowsMarkType(schema.marks.em)).toBe(true);
    expect(schema.nodes.container.allowsMarkType(schema.marks.em)).toBe(false);
    expect(schema.nodes.underscore.allowsMarkType(schema.marks.strong)).toBe(true);
  });

  test("allowedMarks filters a set down to permitted marks", () => {
    /** Verifies: PM-SCH-014 */
    const schema = new Schema({
      nodes: {
        doc: { content: "block+" },
        fancy: { group: "block", content: "text*", marks: "em" },
        text: {},
      },
      marks: { em: {}, strong: {} },
    });
    const filtered = schema.nodes.fancy.allowedMarks([
      schema.mark("em"),
      schema.mark("strong"),
    ]);
    expect(filtered.map((m) => m.type.name)).toEqual(["em"]);
  });

  test("mixing inline and block content raises SyntaxError at construction", () => {
    /** Verifies: PM-SCH-015, PM-ERR-001 */
    expect(
      () =>
        new Schema({
          nodes: {
            doc: { content: "image caption" },
            caption: { content: "text*" },
            image: { inline: true, attrs: { src: {} } },
            text: {},
          },
        }),
    ).toThrow(SyntaxError);
  });

  test("non-generatable type in a required position raises SyntaxError", () => {
    /** Verifies: PM-SCH-016, PM-ERR-001 */
    expect(
      () =>
        new Schema({
          nodes: {
            doc: { content: "image_block caption" },
            image_block: { attrs: { src: {} } },
            caption: { content: "text*" },
            text: {},
          },
        }),
    ).toThrow(SyntaxError);
  });
});

describe("nodes and fragments", () => {
  test("node anatomy exposes type, attrs, content, marks, and text", () => {
    /** Verifies: PM-DOC-001 */
    const schema = makeBase();
    const word = schema.text("word", [schema.mark("em")]);
    expect(word.text).toBe("word");
    expect(word.marks.map((m) => m.type.name)).toEqual(["em"]);
    const p = schema.node("paragraph", null, [word]);
    expect(p.type.name).toBe("paragraph");
    expect(p.marks).toEqual([]);
    expect(p.content).toBeInstanceOf(Fragment);
    expect(p.content.childCount).toBe(1);
    const h = schema.node("heading", { level: 3 }, [schema.text("t")]);
    expect(h.attrs).toEqual({ level: 3 });
  });

  test("child access distinguishes throwing and null-returning forms", () => {
    /** Verifies: PM-DOC-002, PM-ERR-001 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("a")]),
      schema.node("horizontal_rule"),
    ]);
    expect(doc.childCount).toBe(2);
    expect(doc.child(0).type.name).toBe("paragraph");
    expect(doc.child(1).type.name).toBe("horizontal_rule");
    expect(() => doc.child(2)).toThrow(RangeError);
    expect(doc.maybeChild(2)).toBeNull();
    expect(doc.firstChild!.type.name).toBe("paragraph");
    expect(doc.lastChild!.type.name).toBe("horizontal_rule");
    const empty = schema.node("paragraph");
    expect(empty.firstChild).toBeNull();
    expect(empty.lastChild).toBeNull();
  });

  test("forEach passes each child with offset and index", () => {
    /** Verifies: PM-DOC-002 */
    const schema = makeBase();
    const p = schema.node("paragraph", null, [
      schema.text("ab"),
      schema.text("cd", [schema.mark("em")]),
      schema.text("ef"),
    ]);
    const rows: string[] = [];
    p.forEach((child, offset, index) => rows.push(`${index}:${offset}:${child.text}`));
    expect(rows).toEqual(["0:0:ab", "1:2:cd", "2:4:ef"]);
  });

  test("descendants visits positions and honors early exit", () => {
    /** Verifies: PM-DOC-003 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello")]),
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("world")])]),
    ]);
    const seen: string[] = [];
    doc.descendants((node, pos) => {
      seen.push(`${node.type.name}@${pos}`);
      return true;
    });
    expect(seen).toEqual(["paragraph@0", "text@1", "blockquote@7", "paragraph@8", "text@9"]);
    const shallow: string[] = [];
    doc.descendants((node, pos) => {
      shallow.push(`${node.type.name}@${pos}`);
      return node.type.name !== "blockquote";
    });
    expect(shallow).toEqual(["paragraph@0", "text@1", "blockquote@7"]);
  });

  test("nodesBetween visits the nodes touching a range", () => {
    /** Verifies: PM-DOC-003 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello")]),
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("world")])]),
    ]);
    const seen: string[] = [];
    doc.nodesBetween(3, 10, (node, pos) => {
      seen.push(`${node.type.name}@${pos}`);
    });
    expect(seen).toEqual(["paragraph@0", "text@1", "blockquote@7", "paragraph@8", "text@9"]);
  });

  test("nodeSize arithmetic: text length, leaf 1, container +2", () => {
    /** Verifies: PM-DOC-004, PM-CVI-002 */
    const schema = makeBase();
    expect(schema.text("abcd").nodeSize).toBe(4);
    expect(schema.node("horizontal_rule").nodeSize).toBe(1);
    const p = schema.node("paragraph", null, [
      schema.text("hello ", [schema.mark("em")]),
      schema.text("world"),
    ]);
    expect(p.content.size).toBe(11);
    expect(p.nodeSize).toBe(13);
    const doc = schema.node("doc", null, [
      p,
      schema.node("heading", { level: 2 }, [schema.text("title")]),
      schema.node("horizontal_rule"),
    ]);
    expect(doc.content.size).toBe(13 + 7 + 1);
    expect(doc.nodeSize).toBe(23);
  });

  test("node flags mirror type flags on instances", () => {
    /** Verifies: PM-DOC-005 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [schema.node("paragraph")]);
    expect(doc.isBlock).toBe(true);
    expect(doc.isTextblock).toBe(false);
    const p = doc.child(0);
    expect(p.isTextblock).toBe(true);
    const txt = schema.text("x");
    expect(txt.isText).toBe(true);
    expect(txt.isInline).toBe(true);
    expect(txt.isLeaf).toBe(true);
    const img = schema.node("image", { src: "u.png" });
    expect(img.isInline).toBe(true);
    expect(img.isLeaf).toBe(true);
    expect(img.isAtom).toBe(true);
  });

  test("textContent and textBetween project text with separators and leaf text", () => {
    /** Verifies: PM-DOC-006 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("ab"), schema.node("image", { src: "u" }), schema.text("cd")]),
      schema.node("paragraph", null, [schema.text("ef")]),
    ]);
    expect(doc.textContent).toBe("abcdef");
    expect(doc.textBetween(1, 9)).toBe("abcde");
    expect(doc.textBetween(0, 11, "\n")).toBe("abcd\nef");
    expect(doc.textBetween(0, 11, "\n", "[img]")).toBe("ab[img]cd\nef");
    expect(doc.textBetween(0, 11, "\n", (leaf) => `<${leaf.type.name}>`)).toBe("ab<image>cd\nef");
  });

  test("copy keeps markup while replacing content", () => {
    /** Verifies: PM-DOC-007 */
    const schema = makeBase();
    const p = schema.node("paragraph", null, [schema.text("old")]);
    const copied = p.copy(Fragment.from(schema.text("zz")));
    expect(copied.type.name).toBe("paragraph");
    expect(copied.textContent).toBe("zz");
    const emptied = p.copy();
    expect(emptied.childCount).toBe(0);
    expect(emptied.type.name).toBe("paragraph");
    expect(p.textContent).toBe("old");
  });

  test("node.mark replaces the mark set", () => {
    /** Verifies: PM-DOC-007, PM-MRK-005 */
    const schema = makeBase();
    const word = schema.text("word", [schema.mark("em")]);
    const remarked = word.mark([schema.mark("strong")]);
    expect(remarked.marks.map((m) => m.type.name)).toEqual(["strong"]);
    expect(remarked.text).toBe("word");
    expect(word.marks.map((m) => m.type.name)).toEqual(["em"]);
  });

  test("cut on a text node slices the string and keeps marks", () => {
    /** Verifies: PM-DOC-007 */
    const schema = makeBase();
    const word = schema.text("hello", [schema.mark("em")]);
    const piece = word.cut(1, 3);
    expect(piece.text).toBe("el");
    expect(piece.marks.length).toBe(1);
    expect(piece.marks[0].type.name).toBe("em");
  });

  test("eq, sameMarkup, and hasMarkup compare at different depths", () => {
    /** Verifies: PM-DOC-008, PM-CVI-005 */
    const schema = makeBase();
    const mk = () =>
      schema.node("paragraph", null, [schema.text("hello ", [schema.mark("em")]), schema.text("world")]);
    const a = mk();
    const b = mk();
    expect(a.eq(b)).toBe(true);
    expect(a.sameMarkup(b)).toBe(true);
    const h1 = schema.node("heading", { level: 1 }, [schema.text("t")]);
    const h2 = schema.node("heading", { level: 2 }, [schema.text("t")]);
    expect(h1.eq(h2)).toBe(false);
    expect(h1.sameMarkup(h2)).toBe(false);
    expect(a.hasMarkup(schema.nodes.paragraph)).toBe(true);
    expect(a.hasMarkup(schema.nodes.heading)).toBe(false);
  });

  test("toString renders the debugging tree with mark wrappers", () => {
    /** Verifies: PM-DOC-008 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello ", [schema.mark("em")]), schema.text("world")]),
      schema.node("heading", { level: 2 }, [schema.text("title")]),
      schema.node("horizontal_rule"),
    ]);
    expect(doc.toString()).toBe(
      'doc(paragraph(em("hello "), "world"), heading("title"), horizontal_rule)',
    );
  });

  test("Fragment.from accepts null, node, array, and fragment", () => {
    /** Verifies: PM-DOC-009 */
    const schema = makeBase();
    expect(Fragment.from(null)).toBe(Fragment.empty);
    expect(Fragment.from(null).size).toBe(0);
    const single = Fragment.from(schema.text("q"));
    expect(single.childCount).toBe(1);
    const arr = Fragment.from([schema.text("a", [schema.mark("em")]), schema.node("hard_break")]);
    expect(arr.childCount).toBe(2);
    expect(Fragment.from(arr)).toBe(arr);
    expect(Fragment.empty.childCount).toBe(0);
  });

  test("adjacent text nodes with identical marks merge", () => {
    /** Verifies: PM-DOC-010 */
    const schema = makeBase();
    const merged = Fragment.from([schema.text("ab"), schema.text("cd")]);
    expect(merged.childCount).toBe(1);
    expect(merged.child(0).text).toBe("abcd");
    const kept = Fragment.from([schema.text("ab"), schema.text("cd", [schema.mark("em")])]);
    expect(kept.childCount).toBe(2);
    const appended = Fragment.from(schema.text("ab")).append(Fragment.from(schema.text("cd")));
    expect(appended.childCount).toBe(1);
    expect(appended.child(0).text).toBe("abcd");
    const appendedEm = Fragment.from(schema.text("ab", [schema.mark("em")])).append(
      Fragment.from(schema.text("cd", [schema.mark("em")])),
    );
    expect(appendedEm.childCount).toBe(1);
  });

  test("fragment operations produce expected sequences", () => {
    /** Verifies: PM-DOC-011 */
    const schema = makeBase();
    const em = schema.mark("em");
    const f = Fragment.from([schema.text("ab"), schema.text("cd", [em])]);
    expect(f.size).toBe(4);
    expect(f.childCount).toBe(2);
    expect(f.toString()).toBe('<"ab", em("cd")>');
    expect(f.cut(1, 3).toString()).toBe('<"b", em("c")>');
    expect(f.addToStart(schema.text("Z")).toString()).toBe('<"Z", "ab", em("cd")>');
    expect(f.addToEnd(schema.text("Z")).toString()).toBe('<"ab", em("cd"), "Z">');
    expect(f.replaceChild(0, schema.text("XY")).toString()).toBe('<"XY", em("cd")>');
    const app = f.append(Fragment.from(schema.text("ef", [em])));
    expect(app.childCount).toBe(2);
    expect(app.toString()).toBe('<"ab", em("cdef")>');
    expect(f.child(1).text).toBe("cd");
    expect(f.maybeChild(9)).toBeNull();
    expect(() => f.child(9)).toThrow(RangeError);
    expect(f.firstChild!.text).toBe("ab");
    expect(f.lastChild!.text).toBe("cd");
    expect(f.eq(Fragment.from([schema.text("ab"), schema.text("cd", [em])]))).toBe(true);
    expect(f.eq(Fragment.from(schema.text("ab")))).toBe(false);
  });

  test("findDiffStart and findDiffEnd locate divergence", () => {
    /** Verifies: PM-DOC-012, PM-CVI-005 */
    const schema = makeBase();
    const em = schema.mark("em");
    const fa = Fragment.from([schema.text("hello"), schema.text(" world", [em])]);
    const fb = Fragment.from([schema.text("hellp"), schema.text(" world", [em])]);
    expect(fa.findDiffStart(fb)).toBe(4);
    const end = fa.findDiffEnd(fb)!;
    expect(end.a).toBe(5);
    expect(end.b).toBe(5);
    const same = Fragment.from([schema.text("hello"), schema.text(" world", [em])]);
    expect(fa.findDiffStart(same)).toBeNull();
    expect(fa.findDiffEnd(same)).toBeNull();
  });

  test("check passes valid trees and rejects invalid content", () => {
    /** Verifies: PM-DOC-013, PM-ERR-001 */
    const schema = makeBase();
    const good = schema.node("doc", null, [schema.node("paragraph", null, [schema.text("ok")])]);
    expect(() => good.check()).not.toThrow();
    const bad = schema.nodes.doc.create(null, [schema.text("loose")]);
    expect(() => bad.check()).toThrow(RangeError);
  });
});

describe("positions and resolution", () => {
  function posDoc(schema: Schema): Node {
    return schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello")]),
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("world")])]),
    ]);
  }

  test("nodeAt maps positions to covering nodes", () => {
    /** Verifies: PM-POS-001, PM-POS-002 */
    const schema = makeBase();
    const doc = posDoc(schema);
    expect(doc.nodeSize).toBe(18);
    expect(doc.content.size).toBe(16);
    expect(doc.nodeAt(0)!.type.name).toBe("paragraph");
    expect(doc.nodeAt(1)!.text).toBe("hello");
    expect(doc.nodeAt(3)!.text).toBe("hello");
    expect(doc.nodeAt(7)!.type.name).toBe("blockquote");
    expect(doc.nodeAt(8)!.type.name).toBe("paragraph");
    expect(doc.nodeAt(doc.content.size)).toBeNull();
  });

  test("childAfter and childBefore report direct children with offsets", () => {
    /** Verifies: PM-POS-002 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const after0 = doc.childAfter(0);
    expect(after0.node!.type.name).toBe("paragraph");
    expect(after0.index).toBe(0);
    expect(after0.offset).toBe(0);
    const after7 = doc.childAfter(7);
    expect(after7.node!.type.name).toBe("blockquote");
    expect(after7.index).toBe(1);
    expect(after7.offset).toBe(7);
    const before7 = doc.childBefore(7);
    expect(before7.node!.type.name).toBe("paragraph");
    expect(before7.index).toBe(0);
    expect(before7.offset).toBe(0);
    const before0 = doc.childBefore(0);
    expect(before0.node).toBeNull();
    expect(before0.index).toBe(0);
    expect(before0.offset).toBe(0);
  });

  test("resolve rejects out-of-range positions", () => {
    /** Verifies: PM-POS-003, PM-ERR-001 */
    const schema = makeBase();
    const doc = posDoc(schema);
    expect(doc.resolve(0)).toBeInstanceOf(ResolvedPos);
    expect(() => doc.resolve(99)).toThrow(RangeError);
    expect(() => doc.resolve(-1)).toThrow(RangeError);
  });

  test("resolved position exposes depth, parent, offsets", () => {
    /** Verifies: PM-POS-004, PM-POS-006 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const r = doc.resolve(3);
    expect(r.pos).toBe(3);
    expect(r.depth).toBe(1);
    expect(r.doc).toBe(doc);
    expect(r.parent.type.name).toBe("paragraph");
    expect(r.parentOffset).toBe(2);
    expect(r.textOffset).toBe(2);
    const r0 = doc.resolve(0);
    expect(r0.depth).toBe(0);
    expect(r0.parentOffset).toBe(0);
  });

  test("start, end, before, after work across depths", () => {
    /** Verifies: PM-POS-004 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const r3 = doc.resolve(3);
    expect([r3.start(), r3.end()]).toEqual([1, 6]);
    expect([r3.before(), r3.after()]).toEqual([0, 7]);
    expect([r3.start(0), r3.end(0)]).toEqual([0, 16]);
    const r9 = doc.resolve(9);
    expect(r9.depth).toBe(2);
    expect([r9.start(0), r9.end(0)]).toEqual([0, 16]);
    expect([r9.start(1), r9.end(1)]).toEqual([8, 15]);
    expect([r9.start(2), r9.end(2)]).toEqual([9, 14]);
    expect([r9.before(1), r9.after(1)]).toEqual([7, 16]);
    expect([r9.before(2), r9.after(2)]).toEqual([8, 15]);
    expect(r9.node(0).type.name).toBe("doc");
    expect(r9.node(1).type.name).toBe("blockquote");
    expect(r9.node(2).type.name).toBe("paragraph");
  });

  test("before and after at depth 0 raise RangeError", () => {
    /** Verifies: PM-POS-005, PM-ERR-001 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const r0 = doc.resolve(0);
    expect(() => r0.before(0)).toThrow(RangeError);
    expect(() => r0.after(0)).toThrow(RangeError);
  });

  test("nodeBefore and nodeAfter split text at the position", () => {
    /** Verifies: PM-POS-007 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const r3 = doc.resolve(3);
    expect(r3.nodeBefore!.text).toBe("he");
    expect(r3.nodeAfter!.text).toBe("llo");
    const r0 = doc.resolve(0);
    expect(r0.nodeBefore).toBeNull();
    expect(r0.nodeAfter!.type.name).toBe("paragraph");
    const emptyDoc = schema.node("doc", null, [schema.node("paragraph")]);
    const inside = emptyDoc.resolve(1);
    expect(inside.nodeAfter).toBeNull();
    expect([inside.start(), inside.end()]).toEqual([1, 1]);
  });

  test("index, indexAfter, and posAtIndex map between views", () => {
    /** Verifies: PM-POS-008, PM-CVI-007 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    const r3 = doc.resolve(3);
    expect(r3.index()).toBe(1);
    expect(r3.indexAfter()).toBe(1);
    expect(r3.index(0)).toBe(0);
    expect(r3.indexAfter(0)).toBe(1);
    expect(r3.posAtIndex(1, 0)).toBe(4);
    expect(r3.posAtIndex(0, 1)).toBe(1);
  });

  test("marks() reports the inline marks at a position", () => {
    /** Verifies: PM-POS-009 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [
        schema.text("ab"),
        schema.text("cd", [schema.mark("em")]),
        schema.text("ef"),
      ]),
    ]);
    const names = (pos: number) => doc.resolve(pos).marks().map((m) => m.type.name);
    expect(names(1)).toEqual([]);
    expect(names(3)).toEqual([]);
    expect(names(4)).toEqual(["em"]);
    expect(names(5)).toEqual(["em"]);
    expect(names(7)).toEqual([]);
  });

  test("sameParent, sharedDepth, min, and max relate positions", () => {
    /** Verifies: PM-POS-010 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const rA = doc.resolve(2);
    const rB = doc.resolve(4);
    const rC = doc.resolve(10);
    expect(rA.sameParent(rB)).toBe(true);
    expect(rA.sameParent(rC)).toBe(false);
    expect(rA.sharedDepth(4)).toBe(1);
    expect(rA.sharedDepth(10)).toBe(0);
    expect(rA.min(rB).pos).toBe(2);
    expect(rA.max(rB).pos).toBe(4);
  });

  test("blockRange and NodeRange expose block-level spans", () => {
    /** Verifies: PM-POS-011 */
    const schema = makeBase();
    const doc = posDoc(schema);
    const range = doc.resolve(2).blockRange(doc.resolve(4))!;
    expect(range.start).toBe(0);
    expect(range.end).toBe(7);
    expect(range.depth).toBe(0);
    expect(range.parent.type.name).toBe("doc");
    expect(range.startIndex).toBe(0);
    expect(range.endIndex).toBe(1);
    const cross = doc.resolve(2).blockRange(doc.resolve(10))!;
    expect(cross.start).toBe(0);
    expect(cross.end).toBe(16);
    expect(cross.parent.type.name).toBe("doc");
    const direct = new NodeRange(doc.resolve(2), doc.resolve(4), 1);
    expect(direct.start).toBe(2);
    expect(direct.end).toBe(4);
    expect(direct.parent.type.name).toBe("paragraph");
  });
});

describe("slices and replacement", () => {
  test("slice records open depths and size", () => {
    /** Verifies: PM-SLC-001, PM-SLC-002, PM-SLC-003 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello")]),
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("world")])]),
    ]);
    const inner = doc.slice(1, 6);
    expect(inner.content.toString()).toBe('<"hello">');
    expect(inner.openStart).toBe(0);
    expect(inner.openEnd).toBe(0);
    expect(inner.size).toBe(5);
    const cross = doc.slice(3, 10);
    expect(cross.content.toString()).toBe('<paragraph("llo"), blockquote(paragraph("w"))>');
    expect(cross.openStart).toBe(1);
    expect(cross.openEnd).toBe(2);
    expect(cross.size).toBe(7);
    const full = doc.slice(0, doc.content.size);
    expect(full.openStart).toBe(0);
    expect(full.openEnd).toBe(0);
    expect(full.content.eq(doc.content)).toBe(true);
  });

  test("Slice.empty and Slice.maxOpen bound openness", () => {
    /** Verifies: PM-SLC-003, PM-SLC-004 */
    const schema = makeBase();
    expect(Slice.empty.size).toBe(0);
    expect(Slice.empty.openStart).toBe(0);
    expect(Slice.empty.openEnd).toBe(0);
    const mo = Slice.maxOpen(Fragment.from(schema.node("paragraph", null, [schema.text("Q")])));
    expect(mo.openStart).toBe(1);
    expect(mo.openEnd).toBe(1);
    expect(mo.content.toString()).toBe('<paragraph("Q")>');
    const leaf = Slice.maxOpen(Fragment.from(schema.node("horizontal_rule")));
    expect(leaf.openStart).toBe(0);
    expect(leaf.openEnd).toBe(0);
  });

  test("slice JSON round trip and empty-slice null form", () => {
    /** Verifies: PM-SLC-005, PM-JSN-001 */
    const schema = makeBase();
    const sl = new Slice(Fragment.from(schema.node("paragraph", null, [schema.text("X")])), 1, 1);
    expect(sl.toJSON()).toEqual({
      content: [{ type: "paragraph", content: [{ type: "text", text: "X" }] }],
      openStart: 1,
      openEnd: 1,
    });
    const back = Slice.fromJSON(schema, sl.toJSON());
    expect(back.toJSON()).toEqual(sl.toJSON());
    expect(Slice.empty.toJSON()).toBeNull();
    expect(Slice.fromJSON(schema, null).size).toBe(0);
  });

  test("replace splices closed slices into text ranges", () => {
    /** Verifies: PM-SLC-006 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    const rep = doc.replace(2, 6, new Slice(Fragment.from(schema.text("xy")), 0, 0));
    expect(rep.toString()).toBe('doc(paragraph("AxyD"))');
    const cleared = doc.replace(1, 7, Slice.empty);
    expect(cleared.toString()).toBe("doc(paragraph)");
  });

  test("replacing a range with its own slice is identity", () => {
    /** Verifies: PM-SLC-007, PM-CVI-003 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    const again = doc.replace(2, 6, doc.slice(2, 6));
    expect(again.eq(doc)).toBe(true);
  });

  test("invalid replacements raise ReplaceError", () => {
    /** Verifies: PM-SLC-008, PM-ERR-001 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    expect(() => doc.replace(1, 2, new Slice(Fragment.from(schema.node("paragraph")), 0, 0))).toThrow(
      ReplaceError,
    );
    expect(() => doc.replace(0, 0, new Slice(Fragment.from(schema.text("x")), 2, 2))).toThrow(
      ReplaceError,
    );
    const err = (() => {
      try {
        doc.replace(1, 2, new Slice(Fragment.from(schema.node("paragraph")), 0, 0));
        return null;
      } catch (e) {
        return e;
      }
    })();
    expect(err).toBeInstanceOf(ReplaceError);
    expect(err).toBeInstanceOf(Error);
  });

  test("canReplace, canReplaceWith, and canAppend answer feasibility", () => {
    /** Verifies: PM-SLC-009 */
    const schema = makeContent();
    const sec = schema.node("section", null, [
      schema.node("heading", null, [schema.text("h")]),
      schema.node("paragraph", null, [schema.text("b")]),
    ]);
    expect(sec.canReplace(0, 1)).toBe(false);
    expect(sec.canReplace(0, 1, Fragment.from(schema.node("heading")))).toBe(true);
    expect(sec.canReplaceWith(0, 1, schema.nodes.paragraph)).toBe(false);
    expect(sec.canReplaceWith(0, 1, schema.nodes.heading)).toBe(true);
    expect(sec.canAppend(schema.node("paragraph"))).toBe(false);
    expect(sec.canAppend(schema.node("heading"))).toBe(false);
  });

  test("cut returns the standalone region between positions", () => {
    /** Verifies: PM-SLC-010, PM-CVI-003 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    expect(doc.cut(2, 6).toString()).toBe('doc(paragraph("B"), paragraph("C"))');
    expect(doc.cut(0).eq(doc)).toBe(true);
  });
});

describe("content rules", () => {
  test("match automaton walks the doc content expression", () => {
    /** Verifies: PM-CNT-002 */
    const schema = makeContent();
    const start = schema.nodes.doc.contentMatch;
    expect(start).toBeInstanceOf(ContentMatch);
    expect(start.validEnd).toBe(false);
    const afterP = start.matchType(schema.nodes.paragraph)!;
    expect(afterP.validEnd).toBe(true);
    expect(start.matchType(schema.nodes.text)).toBeNull();
  });

  test("sequenced expression tracks required members", () => {
    /** Verifies: PM-CNT-002 */
    const schema = makeContent();
    const secMatch = schema.nodes.section.contentMatch;
    expect(secMatch.validEnd).toBe(false);
    const afterH = secMatch.matchType(schema.nodes.heading)!;
    expect(afterH.validEnd).toBe(false);
    expect(afterH.matchType(schema.nodes.heading)).toBeNull();
    const afterHP = afterH.matchType(schema.nodes.paragraph)!;
    expect(afterHP.validEnd).toBe(true);
    expect(afterHP.matchType(schema.nodes.paragraph)).not.toBeNull();
  });

  test("matchFragment consumes whole fragments", () => {
    /** Verifies: PM-CNT-002 */
    const schema = makeContent();
    const secMatch = schema.nodes.section.contentMatch;
    const good = Fragment.from([
      schema.node("heading", null, [schema.text("x")]),
      schema.node("paragraph"),
    ]);
    expect(secMatch.matchFragment(good)!.validEnd).toBe(true);
    expect(secMatch.matchFragment(Fragment.from(schema.node("paragraph")))).toBeNull();
  });

  test("defaultType, edgeCount, edge, and contentMatchAt inspect states", () => {
    /** Verifies: PM-CNT-003 */
    const schema = makeContent();
    const start = schema.nodes.doc.contentMatch;
    expect(start.defaultType!.name).toBe("paragraph");
    expect(start.edgeCount).toBe(6);
    expect(start.edge(0).type.name).toBe("paragraph");
    const afterH = schema.nodes.section.contentMatch.matchType(schema.nodes.heading)!;
    expect(afterH.defaultType!.name).toBe("paragraph");
    const sec = schema.node("section", null, [
      schema.node("heading", null, [schema.text("h")]),
      schema.node("paragraph", null, [schema.text("b")]),
    ]);
    expect(sec.contentMatchAt(1).defaultType!.name).toBe("paragraph");
  });

  test("fillBefore synthesizes completing fragments", () => {
    /** Verifies: PM-CNT-004 */
    const schema = makeContent();
    const secMatch = schema.nodes.section.contentMatch;
    const close = secMatch.matchType(schema.nodes.heading)!.fillBefore(Fragment.empty, true)!;
    expect(close.childCount).toBe(1);
    expect(close.child(0).type.name).toBe("paragraph");
    const open = secMatch.fillBefore(Fragment.from(schema.node("paragraph")), false)!;
    expect(open.childCount).toBe(1);
    expect(open.child(0).type.name).toBe("heading");
    const docFill = schema.nodes.doc.contentMatch.fillBefore(Fragment.empty, true)!;
    expect(docFill.toString()).toBe("<paragraph>");
  });

  test("findWrapping computes wrapper chains or null", () => {
    /** Verifies: PM-CNT-004 */
    const schema = makeContent();
    const start = schema.nodes.doc.contentMatch;
    expect(start.findWrapping(schema.nodes.caption)!.map((t) => t.name)).toEqual(["figure"]);
    expect(start.findWrapping(schema.nodes.image)!.map((t) => t.name)).toEqual(["paragraph"]);
    expect(start.findWrapping(schema.nodes.paragraph)).toEqual([]);
  });

  test("counted range modifiers bound repetition", () => {
    /** Verifies: PM-CNT-001 */
    const schema = new Schema({
      nodes: {
        doc: { content: "paragraph{2,3}" },
        paragraph: { content: "text*" },
        text: {},
      },
    });
    const cm = schema.nodes.doc.contentMatch;
    const one = cm.matchType(schema.nodes.paragraph)!;
    expect(one.validEnd).toBe(false);
    const two = one.matchType(schema.nodes.paragraph)!;
    expect(two.validEnd).toBe(true);
    const three = two.matchType(schema.nodes.paragraph)!;
    expect(three.validEnd).toBe(true);
    expect(three.matchType(schema.nodes.paragraph)).toBeNull();
    const fill = cm.fillBefore(Fragment.empty, true)!;
    expect(fill.toString()).toBe("<paragraph, paragraph>");
  });

  test("alternation and optional groups admit either branch once", () => {
    /** Verifies: PM-CNT-001 */
    const schema = new Schema({
      nodes: {
        doc: { content: "(title | subtitle)? body+" },
        title: { content: "text*" },
        subtitle: { content: "text*" },
        body: { content: "text*" },
        text: {},
      },
    });
    const am = schema.nodes.doc.contentMatch;
    expect(am.matchType(schema.nodes.title)!.matchType(schema.nodes.body)).not.toBeNull();
    expect(am.matchType(schema.nodes.body)).not.toBeNull();
    expect(am.matchType(schema.nodes.title)!.matchType(schema.nodes.title)).toBeNull();
    expect(am.defaultType!.name).toBe("body");
  });

  test("createAndFill completes structured content and skips optional non-generatable slots", () => {
    /** Verifies: PM-CNT-005 */
    const schema = makeContent();
    const fig = schema.nodes.figure.createAndFill()!;
    expect(fig.toString()).toBe("figure(caption)");
    const sec = schema.nodes.section.createAndFill()!;
    expect(sec.toString()).toBe("section(heading, paragraph)");
    const withBody = schema.nodes.section.createAndFill(
      null,
      Fragment.from(schema.node("paragraph", null, [schema.text("body")])),
    )!;
    expect(withBody.toString()).toBe('section(heading, paragraph("body"))');
  });
});

describe("marks", () => {
  test("mark creation defaults attributes and enforces required ones", () => {
    /** Verifies: PM-MRK-001, PM-ERR-001 */
    const schema = makeBase();
    const link = schema.marks.link.create({ href: "u" });
    expect(link.attrs).toEqual({ href: "u", title: null });
    expect(schema.marks.link.create(null).attrs).toEqual({ href: null, title: null });
    expect(() => schema.marks.link.create({})).toThrow(RangeError);
    expect(() => schema.marks.link.create({ title: "t" })).toThrow(RangeError);
    expect(link.eq(schema.marks.link.create({ href: "u" }))).toBe(true);
    expect(link.eq(schema.marks.link.create({ href: "v" }))).toBe(false);
    expect(schema.mark("em").eq(schema.mark("em"))).toBe(true);
  });

  test("addToSet keeps schema order and deduplicates", () => {
    /** Verifies: PM-MRK-002 */
    const schema = makeBase();
    const em = schema.mark("em");
    const strong = schema.mark("strong");
    const link = schema.marks.link.create({ href: "u" });
    let set = em.addToSet(Mark.none);
    set = link.addToSet(set);
    set = strong.addToSet(set);
    expect(set.map((m) => m.type.name)).toEqual(["em", "strong", "link"]);
    expect(em.addToSet(set).length).toBe(3);
    expect(em.isInSet(set)).toBe(true);
    expect(strong.isInSet(set)).toBe(true);
    expect(schema.mark("code").isInSet(set)).toBe(false);
    expect(strong.removeFromSet(set).map((m) => m.type.name)).toEqual(["em", "link"]);
  });

  test("Mark.none, setFrom, and sameSet handle set construction", () => {
    /** Verifies: PM-MRK-003 */
    const schema = makeBase();
    const em = schema.mark("em");
    const strong = schema.mark("strong");
    const link = schema.marks.link.create({ href: "u" });
    expect(Mark.none.length).toBe(0);
    expect(Mark.setFrom(null).length).toBe(0);
    expect(Mark.setFrom(strong).map((m) => m.type.name)).toEqual(["strong"]);
    expect(Mark.setFrom([strong, em]).map((m) => m.type.name)).toEqual(["em", "strong"]);
    const set = [em, strong, link];
    expect(Mark.sameSet(set, [em, strong, link])).toBe(true);
    expect(Mark.sameSet(set, [em, strong])).toBe(false);
  });

  test("exclusion removes expelled marks and blocks excluded additions", () => {
    /** Verifies: PM-MRK-004 */
    const schema = makeBase();
    const em = schema.mark("em");
    const strong = schema.mark("strong");
    const code = schema.mark("code");
    const set = [em, strong];
    expect(code.addToSet(set).map((m) => m.type.name)).toEqual(["code"]);
    expect(em.addToSet([code]).map((m) => m.type.name)).toEqual(["code"]);
    expect(schema.marks.code.excludes(schema.marks.em)).toBe(true);
    expect(schema.marks.em.excludes(schema.marks.code)).toBe(false);
  });

  test("mark constraints are enforced by createChecked, check, and rangeHasMark", () => {
    /** Verifies: PM-MRK-005, PM-ERR-001 */
    const schema = new Schema({
      nodes: {
        doc: { content: "block+" },
        plain: { group: "block", content: "text*", marks: "" },
        text: {},
      },
      marks: { em: {} },
    });
    expect(() =>
      schema.nodes.plain.createChecked(null, [schema.text("x", [schema.mark("em")])]),
    ).toThrow(RangeError);
    const sneaky = schema.nodes.plain.create(null, [schema.text("x", [schema.mark("em")])]);
    expect(() => sneaky.check()).toThrow(RangeError);
    const base = makeBase();
    const doc = base.node("doc", null, [
      base.node("paragraph", null, [
        base.text("ab"),
        base.text("cd", [base.mark("em")]),
        base.text("ef"),
      ]),
    ]);
    expect(doc.rangeHasMark(1, 7, base.marks.em)).toBe(true);
    expect(doc.rangeHasMark(1, 3, base.marks.em)).toBe(false);
    expect(doc.rangeHasMark(1, 7, base.mark("em"))).toBe(true);
  });

  test("mark JSON round trips through the schema", () => {
    /** Verifies: PM-JSN-001, PM-JSN-002 */
    const schema = makeBase();
    const link = schema.marks.link.create({ href: "u" });
    expect(link.toJSON()).toEqual({ type: "link", attrs: { href: "u", title: null } });
    expect(Mark.fromJSON(schema, link.toJSON()).eq(link)).toBe(true);
    const em = schema.mark("em");
    expect((em.toJSON() as { type: string }).type).toBe("em");
    expect(Mark.fromJSON(schema, em.toJSON()).eq(em)).toBe(true);
  });
});

describe("json serialization", () => {
  test("node JSON carries type, attrs, content, marks, and text", () => {
    /** Verifies: PM-JSN-001 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hi", [schema.mark("em")])]),
      schema.node("heading", { level: 2 }, [schema.text("t")]),
    ]);
    expect(doc.toJSON()).toEqual({
      type: "doc",
      content: [
        {
          type: "paragraph",
          content: [{ type: "text", marks: [{ type: "em" }], text: "hi" }],
        },
        {
          type: "heading",
          attrs: { level: 2 },
          content: [{ type: "text", text: "t" }],
        },
      ],
    });
  });

  test("fromJSON rebuilds nodes and fragments equal to the originals", () => {
    /** Verifies: PM-JSN-002, PM-CVI-001 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello ", [schema.mark("em")]), schema.text("world")]),
      schema.node("horizontal_rule"),
    ]);
    expect(Node.fromJSON(schema, doc.toJSON()).eq(doc)).toBe(true);
    const frag = doc.content;
    expect(Fragment.fromJSON(schema, frag.toJSON()).eq(frag)).toBe(true);
  });
});
