// Oracle - integration tests for the prosemirror-model document-tree specification.
import { describe, expect, test } from "vitest";
import {
  Schema,
  Node,
  Fragment,
  Slice,
  Mark,
  NodeRange,
  ReplaceError,
} from "prosemirror-model";

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

describe("cross-view invariants", () => {
  test("JSON round trip preserves equality for a marked multi-block document", () => {
    /** Verifies: PM-CVI-001, PM-JSN-002 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [
        schema.text("plain "),
        schema.text("emphasized", [schema.mark("em")]),
        schema.node("image", { src: "pic.png", alt: "alt" }),
      ]),
      schema.node("blockquote", null, [
        schema.node("heading", { level: 2 }, [schema.text("quoted title")]),
        schema.node("paragraph", null, [
          schema.text("linked", [schema.marks.link.create({ href: "https://x" })]),
        ]),
      ]),
      schema.node("horizontal_rule"),
    ]);
    const rebuilt = Node.fromJSON(schema, doc.toJSON());
    expect(rebuilt.eq(doc)).toBe(true);
    expect(rebuilt.toString()).toBe(doc.toString());
    const slice = doc.slice(3, 12);
    const sliceBack = Slice.fromJSON(schema, slice.toJSON());
    expect(sliceBack.content.eq(slice.content)).toBe(true);
    expect(sliceBack.openStart).toBe(slice.openStart);
    expect(sliceBack.openEnd).toBe(slice.openEnd);
  });

  test("descendants positions agree with nodeAt and size arithmetic", () => {
    /** Verifies: PM-CVI-002 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("ab"), schema.node("image", { src: "u" })]),
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("cd")])]),
      schema.node("horizontal_rule"),
    ]);
    let visits = 0;
    doc.descendants((node, pos) => {
      visits += 1;
      expect(doc.nodeAt(pos)).toBe(node);
      if (!node.isText && !node.isLeaf) {
        expect(node.nodeSize).toBe(node.content.size + 2);
      }
      return true;
    });
    expect(visits).toBe(7);
    let childSum = 0;
    doc.forEach((child) => {
      childSum += child.nodeSize;
    });
    expect(childSum).toBe(doc.content.size);
    expect(doc.nodeSize).toBe(doc.content.size + 2);
  });

  test("slice then replace reproduces the document over every block range", () => {
    /** Verifies: PM-CVI-003, PM-SLC-007 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("hello")]),
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("world")])]),
    ]);
    const ranges: Array<[number, number]> = [
      [0, 0],
      [1, 6],
      [3, 10],
      [2, 12],
      [0, doc.content.size],
    ];
    for (const [from, to] of ranges) {
      const rebuilt = doc.replace(from, to, doc.slice(from, to));
      expect(rebuilt.eq(doc)).toBe(true);
    }
  });

  test("cut agrees with the content captured by slice", () => {
    /** Verifies: PM-CVI-003, PM-SLC-010 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    const from = 2;
    const to = 6;
    const cut = doc.cut(from, to);
    const slice = doc.slice(from, to);
    expect(cut.toString()).toBe('doc(paragraph("B"), paragraph("C"))');
    expect(cut.content.eq(Fragment.from(slice.content))).toBe(true);
  });

  test("automaton, createChecked, and check agree on validity", () => {
    /** Verifies: PM-CVI-004, PM-CNT-002, PM-DOC-013 */
    const schema = makeContent();
    const secType = schema.nodes.section;
    const good = Fragment.from([
      schema.node("heading", null, [schema.text("h")]),
      schema.node("paragraph", null, [schema.text("b")]),
    ]);
    const bad = Fragment.from([schema.node("paragraph", null, [schema.text("b")])]);
    expect(secType.contentMatch.matchFragment(good)!.validEnd).toBe(true);
    expect(secType.validContent(good)).toBe(true);
    const checked = secType.createChecked(null, good);
    expect(() => checked.check()).not.toThrow();
    expect(secType.contentMatch.matchFragment(bad)).toBeNull();
    expect(secType.validContent(bad)).toBe(false);
    expect(() => secType.createChecked(null, bad)).toThrow(RangeError);
    const sneaky = secType.create(null, bad);
    expect(() => sneaky.check()).toThrow(RangeError);
  });

  test("diffing agrees with equality across fragment edits", () => {
    /** Verifies: PM-CVI-005, PM-DOC-012 */
    const schema = makeBase();
    const em = schema.mark("em");
    const original = Fragment.from([schema.text("shared"), schema.text(" tail", [em])]);
    const identical = Fragment.from([schema.text("shared"), schema.text(" tail", [em])]);
    expect(original.eq(identical)).toBe(true);
    expect(original.findDiffStart(identical)).toBeNull();
    expect(original.findDiffEnd(identical)).toBeNull();
    const edited = Fragment.from([schema.text("shored"), schema.text(" tail", [em])]);
    expect(original.eq(edited)).toBe(false);
    const start = original.findDiffStart(edited);
    const end = original.findDiffEnd(edited);
    expect(start).not.toBeNull();
    expect(end).not.toBeNull();
    expect(start!).toBe(2);
    expect(end!.a).toBe(3);
    expect(end!.b).toBe(3);
  });

  test("mark sets agree between construction, node marks, resolver, and rangeHasMark", () => {
    /** Verifies: PM-CVI-006, PM-MRK-002, PM-POS-009 */
    const schema = makeBase();
    const em = schema.mark("em");
    const strong = schema.mark("strong");
    let set = strong.addToSet(Mark.none);
    set = em.addToSet(set);
    expect(set.map((m) => m.type.name)).toEqual(["em", "strong"]);
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("ab"), schema.text("cd", set), schema.text("ef")]),
    ]);
    const stored = doc.nodeAt(3)!.marks;
    expect(Mark.sameSet(stored, set)).toBe(true);
    expect(doc.resolve(4).marks().map((m) => m.type.name)).toEqual(["em", "strong"]);
    expect(doc.rangeHasMark(3, 5, schema.marks.em)).toBe(true);
    expect(doc.rangeHasMark(3, 5, schema.marks.strong)).toBe(true);
    expect(doc.rangeHasMark(1, 3, schema.marks.em)).toBe(false);
    expect(em.isInSet(stored)).toBe(true);
  });

  test("resolution agrees with child access at every depth", () => {
    /** Verifies: PM-CVI-007, PM-POS-004, PM-POS-008 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("one")]),
      schema.node("blockquote", null, [
        schema.node("paragraph", null, [schema.text("two")]),
        schema.node("paragraph", null, [schema.text("three")]),
      ]),
    ]);
    const r = doc.resolve(12); // inside "three"
    expect(r.depth).toBe(2);
    expect(r.node(0)).toBe(doc);
    expect(r.node(1)).toBe(doc.child(1));
    expect(r.node(2).textContent).toBe("three");
    expect(doc.child(r.index(0))).toBe(r.node(1));
    expect(r.node(1).child(r.index(1))).toBe(r.node(2));
    expect(r.posAtIndex(r.index(1), 1)).toBe(r.before(2));
    const childInfo = doc.childAfter(r.before(1));
    expect(childInfo.node).toBe(r.node(1));
    expect(childInfo.index).toBe(r.index(0));
  });
});

describe("editing workflows", () => {
  test("open slice paste splits and merges paragraph halves", () => {
    /** Verifies: PM-SLC-006, PM-SLC-001 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    const openSlice = new Slice(
      Fragment.from([
        schema.node("paragraph", null, [schema.text("X")]),
        schema.node("paragraph", null, [schema.text("Y")]),
      ]),
      1,
      1,
    );
    const pasted = doc.replace(2, 6, openSlice);
    expect(pasted.toString()).toBe('doc(paragraph("AX"), paragraph("YD"))');
    expect(() => pasted.check()).not.toThrow();
    expect(doc.toString()).toBe('doc(paragraph("AB"), paragraph("CD"))');
  });

  test("slice cut from a nested context splices into a flat paragraph", () => {
    /** Verifies: PM-SLC-001, PM-SLC-006 */
    const schema = makeBase();
    const src = schema.node("doc", null, [
      schema.node("blockquote", null, [schema.node("paragraph", null, [schema.text("inner")])]),
    ]);
    const slice = src.slice(2, 7);
    expect(slice.content.toString()).toBe('<"inner">');
    expect(slice.openStart).toBe(0);
    expect(slice.openEnd).toBe(0);
    const target = schema.node("doc", null, [schema.node("paragraph", null, [schema.text("AB")])]);
    const merged = target.replace(2, 2, slice);
    expect(merged.toString()).toBe('doc(paragraph("AinnerB"))');
    expect(merged.textContent).toBe("AinnerB");
  });

  test("deleting a block range found through blockRange", () => {
    /** Verifies: PM-POS-011, PM-SLC-006 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("keep")]),
      schema.node("paragraph", null, [schema.text("drop")]),
      schema.node("paragraph", null, [schema.text("stay")]),
    ]);
    const $inside = doc.resolve(8); // inside "drop"
    const range = $inside.blockRange($inside)!;
    expect(range.parent.type.name).toBe("doc");
    expect(range.startIndex).toBe(1);
    expect(range.endIndex).toBe(2);
    const deleted = doc.replace(range.start, range.end, Slice.empty);
    expect(deleted.toString()).toBe('doc(paragraph("keep"), paragraph("stay"))');
    expect(deleted.childCount).toBe(2);
  });

  test("wrapping a node according to findWrapping produces valid content", () => {
    /** Verifies: PM-CNT-004, PM-DOC-013 */
    const schema = makeContent();
    const caption = schema.node("caption", null, [schema.text("cap")]);
    const wrappers = schema.nodes.doc.contentMatch.findWrapping(caption.type)!;
    expect(wrappers.map((w) => w.name)).toEqual(["figure"]);
    let wrapped: Node = caption;
    for (let i = wrappers.length - 1; i >= 0; i--) {
      wrapped = wrappers[i].create(null, Fragment.from(wrapped));
    }
    const doc = schema.nodes.doc.createChecked(null, Fragment.from(wrapped));
    expect(() => doc.check()).not.toThrow();
    expect(doc.toString()).toBe('doc(figure(caption("cap")))');
  });

  test("fillBefore output completes a partial section into checked validity", () => {
    /** Verifies: PM-CNT-004, PM-CVI-004 */
    const schema = makeContent();
    const partial = Fragment.from(schema.node("paragraph", null, [schema.text("body")]));
    const prefix = schema.nodes.section.contentMatch.fillBefore(partial, false)!;
    expect(prefix.childCount).toBe(1);
    expect(prefix.child(0).type.name).toBe("heading");
    const after = schema.nodes.section.contentMatch
      .matchFragment(prefix.append(partial))!
      .fillBefore(Fragment.empty, true)!;
    const content = prefix.append(partial).append(after);
    const section = schema.nodes.section.createChecked(null, content);
    expect(() => section.check()).not.toThrow();
    expect(section.child(0).type.name).toBe("heading");
    expect(section.textContent).toBe("body");
  });

  test("replace failures leave clear error taxonomy while valid edits pass check", () => {
    /** Verifies: PM-SLC-008, PM-ERR-001, PM-DOC-013 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("AB")]),
      schema.node("paragraph", null, [schema.text("CD")]),
    ]);
    expect(() =>
      doc.replace(
        2,
        6,
        new Slice(Fragment.from(schema.node("blockquote", null, [schema.node("paragraph")])), 0, 0),
      ),
    ).toThrow(ReplaceError);
    expect(() => doc.replace(0, 0, new Slice(Fragment.from(schema.text("x")), 2, 2))).toThrow(
      ReplaceError,
    );
    const ok = doc.replace(2, 6, new Slice(Fragment.from(schema.text("-")), 0, 0));
    expect(ok.toString()).toBe('doc(paragraph("A-D"))');
    expect(() => ok.check()).not.toThrow();
  });

  test("structural sharing keeps untouched branches identical after replace", () => {
    /** Verifies: PM-SLC-006, PM-DOC-007 */
    const schema = makeBase();
    const untouched = schema.node("blockquote", null, [
      schema.node("paragraph", null, [schema.text("static")]),
    ]);
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("edit me")]),
      untouched,
    ]);
    const edited = doc.replace(1, 5, new Slice(Fragment.from(schema.text("done")), 0, 0));
    expect(edited.textContent).toBe("done mestatic");
    expect(edited.child(1)).toBe(untouched);
    expect(doc.child(0).textContent).toBe("edit me");
  });

  test("mark exclusion plays through document construction and checking", () => {
    /** Verifies: PM-MRK-004, PM-MRK-005, PM-CVI-006 */
    const schema = makeBase();
    const em = schema.mark("em");
    const code = schema.mark("code");
    const withCode = code.addToSet(em.addToSet(Mark.none));
    expect(withCode.map((m) => m.type.name)).toEqual(["code"]);
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("snippet", withCode)]),
    ]);
    expect(() => doc.check()).not.toThrow();
    expect(doc.rangeHasMark(1, 8, schema.marks.code)).toBe(true);
    expect(doc.rangeHasMark(1, 8, schema.marks.em)).toBe(false);
    expect(em.addToSet(doc.nodeAt(1)!.marks).map((m) => m.type.name)).toEqual(["code"]);
  });

  test("text projections agree with slices over the same range", () => {
    /** Verifies: PM-DOC-006, PM-SLC-001 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("ab"), schema.node("image", { src: "u" }), schema.text("cd")]),
      schema.node("paragraph", null, [schema.text("ef")]),
    ]);
    expect(doc.textBetween(1, 9)).toBe("abcde");
    const slice = doc.slice(1, 9);
    let sliceText = "";
    slice.content.forEach((child) => {
      sliceText += child.textContent;
    });
    expect(sliceText).toBe("abcde");
    expect(doc.textBetween(0, doc.content.size, "|")).toBe("abcd|ef");
    expect(doc.textContent).toBe("abcdef");
  });

  test("NodeRange constructed directly matches blockRange discovery", () => {
    /** Verifies: PM-POS-011 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("one")]),
      schema.node("paragraph", null, [schema.text("two")]),
    ]);
    const found = doc.resolve(2).blockRange(doc.resolve(8))!;
    const direct = new NodeRange(doc.resolve(2), doc.resolve(8), found.depth);
    expect(direct.start).toBe(found.start);
    expect(direct.end).toBe(found.end);
    expect(direct.parent).toBe(found.parent);
    expect(found.startIndex).toBe(0);
    expect(found.endIndex).toBe(2);
    expect(found.start).toBe(0);
    expect(found.end).toBe(10);
  });

  test("counted expressions guide fill and reject overflow through replace", () => {
    /** Verifies: PM-CNT-001, PM-CNT-005, PM-SLC-008 */
    const schema = new Schema({
      nodes: {
        doc: { content: "paragraph{2,3}" },
        paragraph: { content: "text*" },
        text: {},
      },
    });
    const filled = schema.nodes.doc.createAndFill()!;
    expect(filled.childCount).toBe(2);
    expect(() => filled.check()).not.toThrow();
    const three = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("a")]),
      schema.node("paragraph", null, [schema.text("b")]),
      schema.node("paragraph", null, [schema.text("c")]),
    ]);
    expect(() => three.check()).not.toThrow();
    const p4 = Fragment.from([
      schema.node("paragraph"),
      schema.node("paragraph"),
      schema.node("paragraph"),
      schema.node("paragraph"),
    ]);
    expect(schema.nodes.doc.validContent(p4)).toBe(false);
    expect(() => schema.nodes.doc.createChecked(null, p4)).toThrow(RangeError);
  });

  test("copy and mark derive new nodes without touching originals", () => {
    /** Verifies: PM-DOC-007, PM-DOC-008 */
    const schema = makeBase();
    const original = schema.node("paragraph", null, [schema.text("stable", [schema.mark("em")])]);
    const recontented = original.copy(Fragment.from(schema.text("fresh")));
    expect(recontented.sameMarkup(original)).toBe(true);
    expect(recontented.eq(original)).toBe(false);
    expect(recontented.textContent).toBe("fresh");
    const remarked = original.child(0).mark([schema.mark("strong")]);
    expect(remarked.marks.map((m) => m.type.name)).toEqual(["strong"]);
    expect(original.child(0).marks.map((m) => m.type.name)).toEqual(["em"]);
    expect(original.textContent).toBe("stable");
  });
});

describe("end-to-end document sessions", () => {
  test("author, navigate, edit, validate, and persist a document", () => {
    /** Verifies: PM-CVI-001, PM-CVI-003, PM-POS-004, PM-SLC-006, PM-DOC-013 */
    const schema = makeBase();
    // 1. author
    let doc = schema.node("doc", null, [
      schema.node("heading", { level: 1 }, [schema.text("Report")]),
      schema.node("paragraph", null, [schema.text("The quick brown fox.")]),
      schema.node("paragraph", null, [schema.text("End.")]),
    ]);
    expect(() => doc.check()).not.toThrow();
    // 2. navigate: find the word "quick" via resolver
    const start = doc.textContent.indexOf("quick");
    expect(start).toBe(10);
    const $pos = doc.resolve(13); // inside "quick" (heading is 8 tokens: 0..8)
    expect($pos.parent.type.name).toBe("paragraph");
    expect($pos.node(0).type.name).toBe("doc");
    // 3. edit: replace "quick" (positions 13..18 inside second block) with "sly"
    const from = 13;
    const to = 18;
    expect(doc.textBetween(from, to)).toBe("quick");
    doc = doc.replace(from, to, new Slice(Fragment.from(schema.text("sly")), 0, 0));
    expect(doc.child(1).textContent).toBe("The sly brown fox.");
    expect(() => doc.check()).not.toThrow();
    // 4. persist and restore
    const restored = Node.fromJSON(schema, doc.toJSON());
    expect(restored.eq(doc)).toBe(true);
    // 5. identity edit keeps equality
    const round = restored.replace(9, 15, restored.slice(9, 15));
    expect(round.eq(doc)).toBe(true);
  });

  test("split a paragraph, then join it back through open slices", () => {
    /** Verifies: PM-SLC-006, PM-SLC-007, PM-CVI-003 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [schema.node("paragraph", null, [schema.text("HelloWorld")])]);
    // split at position 6 by replacing the empty range with an open two-paragraph slice
    const splitSlice = new Slice(
      Fragment.from([schema.node("paragraph"), schema.node("paragraph")]),
      1,
      1,
    );
    const split = doc.replace(6, 6, splitSlice);
    expect(split.toString()).toBe('doc(paragraph("Hello"), paragraph("World"))');
    expect(() => split.check()).not.toThrow();
    // join back by deleting across the boundary
    const joined = split.replace(6, 8, Slice.empty);
    expect(joined.toString()).toBe('doc(paragraph("HelloWorld"))');
    expect(joined.eq(doc)).toBe(true);
  });

  test("schema-driven synthesis composes a valid document from automaton hints", () => {
    /** Verifies: PM-CNT-003, PM-CNT-005, PM-CVI-004 */
    const schema = makeContent();
    // walk the doc automaton, always taking the default generatable type
    const docType = schema.nodes.doc;
    let state = docType.contentMatch;
    const first = state.defaultType!;
    expect(first.name).toBe("paragraph");
    const child = first.createAndFill()!;
    state = state.matchType(first)!;
    const closing = state.fillBefore(Fragment.empty, true)!;
    const content = Fragment.from(child).append(closing);
    const doc = docType.createChecked(null, content);
    expect(() => doc.check()).not.toThrow();
    expect(docType.validContent(doc.content)).toBe(true);
    // section requires synthesis of a heading before paragraphs
    const section = schema.nodes.section.createAndFill(
      null,
      Fragment.from(schema.node("paragraph", null, [schema.text("prose")])),
    )!;
    expect(section.child(0).type.name).toBe("heading");
    expect(section.child(1).textContent).toBe("prose");
    const full = docType.createChecked(null, Fragment.from(section));
    expect(() => full.check()).not.toThrow();
  });

  test("diff-guided reconciliation converges two documents", () => {
    /** Verifies: PM-CVI-005, PM-DOC-012, PM-SLC-006 */
    const schema = makeBase();
    const mine = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("shared intro")]),
      schema.node("paragraph", null, [schema.text("local edit")]),
    ]);
    const theirs = schema.node("doc", null, [
      schema.node("paragraph", null, [schema.text("shared intro")]),
      schema.node("paragraph", null, [schema.text("remote change")]),
    ]);
    const start = mine.content.findDiffStart(theirs.content)!;
    const end = mine.content.findDiffEnd(theirs.content)!;
    expect(start).toBe(15);
    // adopt their version of the differing range
    const patched = mine.replace(start, end.a, theirs.slice(start, end.b));
    expect(patched.eq(theirs)).toBe(true);
    expect(patched.content.findDiffStart(theirs.content)).toBeNull();
  });

  test("full multi-projection sweep stays consistent on a nested document", () => {
    /** Verifies: PM-CVI-001, PM-CVI-002, PM-CVI-006, PM-CVI-007 */
    const schema = makeBase();
    const doc = schema.node("doc", null, [
      schema.node("heading", { level: 3 }, [schema.text("Deep")]),
      schema.node("blockquote", null, [
        schema.node("paragraph", null, [
          schema.text("plain "),
          schema.text("marked", [schema.mark("em"), schema.mark("strong")]),
        ]),
        schema.node("horizontal_rule"),
      ]),
    ]);
    // sizes vs positions
    expect(doc.nodeSize).toBe(doc.content.size + 2);
    doc.descendants((node, pos) => {
      expect(doc.nodeAt(pos)).toBe(node);
      return true;
    });
    // resolver vs children
    const $m = doc.resolve(15); // inside "marked"
    expect($m.parent.type.name).toBe("paragraph");
    expect($m.node(1).type.name).toBe("blockquote");
    expect(doc.child($m.index(0))).toBe($m.node(1));
    // marks across views
    expect($m.marks().map((m) => m.type.name)).toEqual(["em", "strong"]);
    expect(doc.rangeHasMark(13, 19, schema.marks.strong)).toBe(true);
    // persistence
    const round = Node.fromJSON(schema, doc.toJSON());
    expect(round.eq(doc)).toBe(true);
    expect(round.slice(8, 16).content.eq(doc.slice(8, 16).content)).toBe(true);
  });

  test("template completion pipeline: fill, verify, serialize, restore, re-verify", () => {
    /** Verifies: PM-CNT-005, PM-CVI-001, PM-CVI-004, PM-JSN-002 */
    const schema = makeContent();
    const section = schema.nodes.section.createAndFill()!;
    const figure = schema.nodes.figure.createAndFill()!;
    const doc = schema.nodes.doc.createChecked(null, Fragment.from([section, figure]));
    expect(() => doc.check()).not.toThrow();
    expect(doc.toString()).toBe("doc(section(heading, paragraph), figure(caption))");
    expect(schema.nodes.doc.validContent(doc.content)).toBe(true);
    const json = doc.toJSON();
    const restored = Node.fromJSON(schema, json);
    expect(restored.eq(doc)).toBe(true);
    expect(() => restored.check()).not.toThrow();
    expect(restored.childCount).toBe(2);
    expect(restored.child(0).child(0).type.name).toBe("heading");
  });
});
