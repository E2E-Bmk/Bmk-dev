// Oracle - integration tests for the avsc Avro type-engine specification.
import { describe, expect, test } from "vitest";
import { Type, types, readSchema, readProtocol } from "avsc";

function hex(buf: Buffer): string {
  return Buffer.from(buf).toString("hex");
}

const DOC_SCHEMA = {
  type: "record",
  name: "Doc",
  namespace: "ns",
  fields: [
    { name: "id", type: { type: "fixed", name: "Id", size: 2 } },
    { name: "kind", type: { type: "enum", name: "Kind", symbols: ["A", "B"] } },
    { name: "tags", type: { type: "array", items: "string" } },
    { name: "meta", type: { type: "map", values: "int" } },
    { name: "note", type: ["null", "string"] },
  ],
} as const;

function docType(): types.RecordType {
  return Type.forSchema(DOC_SCHEMA as any) as types.RecordType;
}

function docValue() {
  return {
    id: Buffer.from([0xab, 0xcd]),
    kind: "B",
    tags: ["x", "y"],
    meta: { n: 1 },
    note: "hello",
  };
}

describe("cross-view invariants", () => {
  test("codec agreement holds for accepted and rejected values", () => {
    /** Verifies: AV-CVI-001 */
    const t = docType();
    const value = docValue();
    expect(t.isValid(value)).toBe(true);
    const viaBinary = t.fromBuffer(t.toBuffer(value));
    const viaJson = t.fromString(t.toString(value));
    expect({ ...viaBinary, id: hex(viaBinary.id) }).toEqual({ ...value, id: "abcd" });
    expect({ ...viaJson, id: hex(viaJson.id) }).toEqual({ ...value, id: "abcd" });
    const bad = { ...docValue(), kind: "Z" };
    expect(t.isValid(bad)).toBe(false);
    expect(() => t.toBuffer(bad)).toThrow(Error);
    expect(() => t.clone(bad)).toThrow(Error);
    expect(() => t.toString(bad)).toThrow(Error);
  });

  test("complex schemas round-trip through schema output", () => {
    /** Verifies: AV-CVI-002 */
    const t = docType();
    const recompiled = Type.forSchema(t.schema());
    expect(recompiled.equals(t)).toBe(true);
    expect(recompiled.fingerprint().equals(t.fingerprint())).toBe(true);
    const value = docValue();
    const decoded = recompiled.fromBuffer(t.toBuffer(value));
    expect(hex(decoded.id)).toBe("abcd");
    expect(decoded.tags).toEqual(["x", "y"]);
  });

  test("an evolution chain carries data across three versions", () => {
    /** Verifies: AV-CVI-003, AV-EVO-004, AV-EVO-008 */
    const v1 = Type.forSchema({ type: "record", name: "Doc", fields: [{ name: "id", type: "int" }] });
    const v2 = Type.forSchema({
      type: "record",
      name: "Doc",
      fields: [
        { name: "id", type: "long" },
        { name: "title", type: "string", default: "untitled" },
      ],
    });
    const v3 = Type.forSchema({
      type: "record",
      name: "Doc",
      fields: [
        { name: "docId", aliases: ["id"], type: "long" },
        { name: "title", type: "string", default: "untitled" },
        { name: "note", type: ["null", "string"], default: null },
      ],
    } as any);
    const b1 = v1.toBuffer({ id: 7 });
    expect(v2.fromBuffer(b1, v2.createResolver(v1))).toEqual({ id: 7, title: "untitled" });
    expect(v3.fromBuffer(b1, v3.createResolver(v1))).toEqual({ docId: 7, title: "untitled", note: null });
    const b2 = v2.toBuffer({ id: 8, title: "t" });
    expect(v3.fromBuffer(b2, v3.createResolver(v2))).toEqual({ docId: 8, title: "t", note: null });
  });

  test("independently compiled equal types exchange binary data", () => {
    /** Verifies: AV-CVI-002, AV-BIN-003 */
    const a = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    const b = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    expect(a.equals(b)).toBe(true);
    expect({ ...a.fromBuffer(b.toBuffer({ a: 4 })) }).toEqual({ a: 4 });
    expect({ ...b.fromBuffer(a.toBuffer({ a: 5 })) }).toEqual({ a: 5 });
  });

  test("sorting by compare matches sorting by encoded buffers", () => {
    /** Verifies: AV-CVI-005, AV-VAL-013, AV-VAL-014 */
    const t = Type.forSchema({
      type: "record",
      name: "K",
      fields: [
        { name: "rank", type: "int", order: "descending" },
        { name: "name", type: "string" },
      ],
    });
    const values = [
      { rank: 2, name: "b" },
      { rank: 1, name: "a" },
      { rank: 2, name: "a" },
    ];
    const byCompare = [...values].sort((x, y) => t.compare(x, y)).map((v) => `${v.rank}${v.name}`);
    const byBuffers = [...values]
      .sort((x, y) => t.compareBuffers(t.toBuffer(x), t.toBuffer(y)))
      .map((v) => `${v.rank}${v.name}`);
    expect(byCompare).toEqual(["2a", "2b", "1a"]);
    expect(byBuffers).toEqual(["2a", "2b", "1a"]);
  });

  test("inference closes over its inputs", () => {
    /** Verifies: AV-CVI-004, AV-INF-001, AV-INF-002 */
    const samples: unknown[] = [1, "x", { a: 1, b: "s" }, [1, 2], Buffer.from([7])];
    for (const sample of samples) {
      const t = Type.forValue(sample as any);
      expect(t.isValid(sample)).toBe(true);
      const back = t.fromBuffer(t.toBuffer(sample));
      expect(t.isValid(back)).toBe(true);
    }
    const first = Type.forValue({ a: 1 });
    const second = Type.forValue({ a: 2, b: "x" });
    const combined = Type.forTypes([first, second]);
    expect(combined.isValid({ a: 1 })).toBe(true);
    expect(combined.isValid({ a: 2, b: "x" })).toBe(true);
  });

  test("IDL-compiled types behave like hand-written schemas", () => {
    /** Verifies: AV-CVI-006, AV-IDL-001 */
    const fromIdl = Type.forSchema(readSchema("record Person { string name; int age = 25; }"));
    const manual = Type.forSchema({
      type: "record",
      name: "Person",
      fields: [
        { name: "name", type: "string" },
        { name: "age", type: "int", default: 25 },
      ],
    });
    expect(fromIdl.equals(manual)).toBe(true);
    expect(fromIdl.fingerprint().equals(manual.fingerprint())).toBe(true);
    expect(hex(fromIdl.toBuffer({ name: "ab", age: 3 }))).toBe(hex(manual.toBuffer({ name: "ab", age: 3 })));
    expect(fromIdl.isValid({ name: "a" })).toBe(true);
    expect(fromIdl.isValid({ age: 3 })).toBe(false);
    expect({ ...manual.fromBuffer(fromIdl.toBuffer({ name: "z", age: 1 })) }).toEqual({ name: "z", age: 1 });
  });

  test("shared registries expose one instance across schemas", () => {
    /** Verifies: AV-CVI-007, AV-TYP-015 */
    const registry: Record<string, Type> = {};
    const kind = Type.forSchema({ type: "enum", name: "Kind", symbols: ["A", "B"] }, { registry });
    const message = Type.forSchema(
      { type: "record", name: "Msg", fields: [{ name: "kind", type: "Kind" }] },
      { registry },
    ) as types.RecordType;
    const audit = Type.forSchema(
      { type: "record", name: "Audit", fields: [{ name: "kind", type: "Kind" }] },
      { registry },
    ) as types.RecordType;
    expect(message.field("kind").type).toBe(kind);
    expect(audit.field("kind").type).toBe(kind);
    const buf = message.toBuffer({ kind: "B" });
    expect({ ...audit.fromBuffer(buf) }).toEqual({ kind: "B" });
  });

  test("wrapped and unwrapped unions share the wire format", () => {
    /** Verifies: AV-TYP-011, AV-TYP-012, AV-BIN-009 */
    const unwrapped = Type.forSchema(["null", "string"] as any);
    const wrapped = Type.forSchema(["null", "string"] as any, { wrapUnions: true });
    expect(unwrapped.equals(wrapped)).toBe(true);
    expect(unwrapped.fromBuffer(wrapped.toBuffer({ string: "x" }))).toBe("x");
    expect({ ...wrapped.fromBuffer(unwrapped.toBuffer("y")) }).toEqual({ string: "y" });
    expect(unwrapped.fromBuffer(wrapped.toBuffer(null))).toBeNull();
  });

  test("logical types project through validation, codecs, and evolution", () => {
    /** Verifies: AV-TYP-018, AV-EVO-001, AV-CVI-001 */
    class DateType extends types.LogicalType {
      protected _fromValue(val: any) {
        return new Date(val);
      }
      protected _toValue(date: any) {
        return date instanceof Date ? +date : undefined;
      }
      protected _resolve(type: Type) {
        if (Type.isType(type, "long", "string")) {
          return this._fromValue;
        }
      }
    }
    const t = Type.forSchema({ type: "long", logicalType: "ts" } as any, { logicalTypes: { ts: DateType } });
    expect(t.isValid(new Date(1234))).toBe(true);
    expect(t.isValid(1234)).toBe(false);
    const viaBinary = t.fromBuffer(t.toBuffer(new Date(1234)));
    expect(viaBinary instanceof Date).toBe(true);
    expect(+viaBinary).toBe(1234);
    const text = t.toString(new Date(1234));
    expect(text).toBe("1234");
    const viaJson = t.fromString(text);
    expect(viaJson instanceof Date).toBe(true);
    expect(+viaJson).toBe(1234);
    const plainWriter = Type.forSchema("long");
    const resolved = t.fromBuffer(plainWriter.toBuffer(5000), t.createResolver(plainWriter));
    expect(resolved instanceof Date).toBe(true);
    expect(+resolved).toBe(5000);
    expect(() => t.toBuffer(123 as any)).toThrow(Error);
  });

  test("composite records encode their parts in sequence", () => {
    /** Verifies: AV-BIN-010, AV-BIN-007, AV-BIN-008 */
    const record = Type.forSchema({
      type: "record",
      name: "D",
      fields: [
        { name: "kind", type: { type: "enum", name: "K", symbols: ["A", "B"] } },
        { name: "id", type: { type: "fixed", name: "F", size: 2 } },
        { name: "tags", type: { type: "array", items: "string" } },
        { name: "n", type: "int" },
      ],
    });
    const value = { kind: "B", id: Buffer.from([0xab, 0xcd]), tags: ["x"], n: 3 };
    const whole = record.toBuffer(value);
    const parts = Buffer.concat([
      Type.forSchema({ type: "enum", name: "K", symbols: ["A", "B"] }).toBuffer("B"),
      Type.forSchema({ type: "fixed", name: "F", size: 2 }).toBuffer(value.id),
      Type.forSchema({ type: "array", items: "string" }).toBuffer(["x"]),
      Type.forSchema("int").toBuffer(3),
    ]);
    expect(hex(whole)).toBe("02abcd0202780006");
    expect(whole.equals(parts)).toBe(true);
  });

  test("recursive types round-trip through binary and JSON", () => {
    /** Verifies: AV-TYP-017, AV-CVI-001 */
    const t = Type.forSchema({
      type: "record",
      name: "Node",
      fields: [
        { name: "label", type: "string" },
        { name: "next", type: ["null", "Node"], default: null },
      ],
    } as any);
    const list = { label: "a", next: { label: "b", next: null } };
    expect(t.isValid(list)).toBe(true);
    const viaBinary = t.fromBuffer(t.toBuffer(list));
    expect(viaBinary.label).toBe("a");
    expect(viaBinary.next.label).toBe("b");
    expect(viaBinary.next.next).toBeNull();
    const viaJson = t.fromString(t.toString(list));
    expect(viaJson.next.label).toBe("b");
  });

  test("resolver output stays within the reader's value domain", () => {
    /** Verifies: AV-CVI-003, AV-EVO-001 */
    const writer = Type.forSchema({
      type: "record",
      name: "M",
      fields: [
        { name: "count", type: "int" },
        { name: "label", type: "string" },
      ],
    });
    const reader = Type.forSchema({
      type: "record",
      name: "M",
      fields: [
        { name: "count", type: "double" },
        { name: "label", type: "bytes" },
        { name: "flag", type: "boolean", default: true },
      ],
    });
    const resolver = reader.createResolver(writer);
    for (const value of [{ count: 1, label: "a" }, { count: -3, label: "" }, { count: 2 ** 30, label: "zz" }]) {
      const decoded = reader.fromBuffer(writer.toBuffer(value), resolver);
      expect(reader.isValid(decoded)).toBe(true);
      expect(decoded.count).toBe(value.count);
      expect(decoded.label.toString()).toBe(value.label);
      expect(decoded.flag).toBe(true);
    }
  });

  test("JSON-transported buffers re-enter the binary codec", () => {
    /** Verifies: AV-VAL-011, AV-BIN-003 */
    const t = Type.forSchema({
      type: "record",
      name: "Blob",
      fields: [
        { name: "name", type: "string" },
        { name: "payload", type: "bytes" },
      ],
    });
    const value = { name: "f", payload: Buffer.from([1, 2, 3]) };
    const overJson = JSON.parse(JSON.stringify(value));
    expect(t.isValid(overJson)).toBe(false);
    const restored = t.clone(overJson, { coerceBuffers: true });
    expect(t.isValid(restored)).toBe(true);
    expect(t.toBuffer(restored).equals(t.toBuffer(value))).toBe(true);
  });

  test("validation hooks and strict mode compose across nesting", () => {
    /** Verifies: AV-VAL-008, AV-VAL-009 */
    const t = Type.forSchema({
      type: "record",
      name: "Outer",
      fields: [
        { name: "inner", type: { type: "record", name: "Inner", fields: [{ name: "x", type: "int" }] } },
        { name: "b", type: "string" },
      ],
    });
    const paths: string[] = [];
    const ok = t.isValid(
      { inner: { x: "bad" }, b: 7 },
      { errorHook: (path) => paths.push(path.join(".")) },
    );
    expect(ok).toBe(false);
    expect(paths).toEqual(["inner.x", "b"]);
    expect(t.isValid({ inner: { x: 1 }, b: "s", extra: 0 })).toBe(true);
    expect(t.isValid({ inner: { x: 1 }, b: "s", extra: 0 }, { noUndeclaredFields: true })).toBe(false);
  });

  test("canonical projection ignores decoration attributes", () => {
    /** Verifies: AV-JSN-003, AV-JSN-005, AV-JSN-006 */
    const bare = Type.forSchema({ type: "record", name: "R", fields: [{ name: "a", type: "int" }] });
    const decorated = Type.forSchema({
      type: "record",
      name: "R",
      doc: "docs",
      fields: [{ name: "a", type: "int", default: 3, order: "descending", doc: "field doc" }],
    } as any);
    expect(decorated.equals(bare)).toBe(true);
    expect(decorated.fingerprint().equals(bare.fingerprint())).toBe(true);
    expect(decorated.schema()).toEqual(bare.schema());
    expect({ ...bare.fromBuffer(decorated.toBuffer({ a: 6 })) }).toEqual({ a: 6 });
  });

  test("inferred writers feed declared readers", () => {
    /** Verifies: AV-INF-001, AV-EVO-001, AV-CVI-004 */
    const sample = { a: 1, b: "x" };
    const writer = Type.forValue(sample);
    const reader = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "a", type: "long" },
        { name: "b", type: "string" },
      ],
    });
    const resolver = reader.createResolver(writer);
    const decoded = reader.fromBuffer(writer.toBuffer(sample), resolver);
    expect({ ...decoded }).toEqual({ a: 1, b: "x" });
    expect(reader.isValid(decoded)).toBe(true);
  });

  test("protocol types compile into working codecs", () => {
    /** Verifies: AV-IDL-002, AV-BIN-003 */
    const protocol = readProtocol("protocol Bus { record Msg { string body; int n = 1; } }");
    const msg = Type.forSchema(protocol.types[0]) as types.RecordType;
    expect(msg.name).toBe("Msg");
    expect(hex(msg.toBuffer({ body: "hi", n: 2 }))).toBe("04686904");
    expect(msg.isValid({ body: "b" })).toBe(true);
    expect(msg.field("n").defaultValue()).toBe(1);
    expect({ ...msg.fromBuffer(msg.toBuffer({ body: "hi", n: 2 })) }).toEqual({ body: "hi", n: 2 });
  });

  test("both codecs agree across a composite document", () => {
    /** Verifies: AV-CVI-001, AV-JSN-001 */
    const t = docType();
    for (const note of ["hello", null]) {
      const value = { ...docValue(), note };
      const viaBinary = t.fromBuffer(t.toBuffer(value));
      const viaJson = t.fromString(t.toString(value));
      expect(hex(viaJson.id)).toBe(hex(viaBinary.id));
      expect(viaJson.kind).toBe(viaBinary.kind);
      expect(viaJson.tags).toEqual(viaBinary.tags);
      expect(viaJson.meta).toEqual(viaBinary.meta);
      expect(viaJson.note).toEqual(viaBinary.note);
    }
  });

  test("random values traverse the full pipeline", () => {
    /** Verifies: AV-VAL-015, AV-CVI-001 */
    const t = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "n", type: "int" },
        { name: "s", type: "string" },
        { name: "k", type: { type: "enum", name: "K", symbols: ["A", "B", "C"] } },
        { name: "u", type: ["null", "int"] },
      ],
    } as any);
    for (let i = 0; i < 20; i++) {
      const value = t.random();
      expect(t.isValid(value)).toBe(true);
      const viaBinary = t.fromBuffer(t.toBuffer(value));
      expect({ ...viaBinary }).toEqual({ ...(value as any) });
      const viaJson = t.fromString(t.toString(value));
      expect({ ...viaJson }).toEqual({ ...(value as any) });
    }
  });

  test("fingerprints distinguish and identify schema versions", () => {
    /** Verifies: AV-JSN-005, AV-JSN-006 */
    const v1 = Type.forSchema({ type: "record", name: "Doc", fields: [{ name: "id", type: "int" }] });
    const v2 = Type.forSchema({
      type: "record",
      name: "Doc",
      fields: [
        { name: "id", type: "long" },
        { name: "title", type: "string", default: "untitled" },
      ],
    });
    expect(v1.equals(v2)).toBe(false);
    expect(v1.fingerprint().equals(v2.fingerprint())).toBe(false);
    const v1Copy = Type.forSchema(v1.schema());
    expect(v1Copy.fingerprint().equals(v1.fingerprint())).toBe(true);
    const v2Copy = Type.forSchema(v2.schema({ exportAttrs: true }));
    expect(v2Copy.fingerprint().equals(v2.fingerprint())).toBe(true);
  });
});

describe("end-to-end schema sessions", () => {
  test("publish and evolve a message schema across a registry", () => {
    /** Verifies: AV-CVI-007, AV-CVI-003, AV-TYP-015, AV-EVO-004 */
    const registry: Record<string, Type> = {};
    const level = Type.forSchema({ type: "enum", name: "Level", symbols: ["INFO", "WARN"] }, { registry });
    const eventV1 = Type.forSchema(
      {
        type: "record",
        name: "Event",
        fields: [
          { name: "level", type: "Level" },
          { name: "code", type: "int" },
        ],
      },
      { registry },
    ) as types.RecordType;
    expect(eventV1.field("level").type).toBe(level);
    const published = [
      eventV1.toBuffer({ level: "INFO", code: 1 }),
      eventV1.toBuffer({ level: "WARN", code: 64 }),
    ];
    const eventV2 = Type.forSchema({
      type: "record",
      name: "Event",
      fields: [
        { name: "level", type: { type: "enum", name: "Level", symbols: ["INFO", "WARN"] } },
        { name: "code", type: "long" },
        { name: "source", type: "string", default: "legacy" },
      ],
    });
    const resolver = eventV2.createResolver(eventV1);
    const upgraded = published.map((buf) => eventV2.fromBuffer(buf, resolver));
    expect({ ...upgraded[0] }).toEqual({ level: "INFO", code: 1, source: "legacy" });
    expect({ ...upgraded[1] }).toEqual({ level: "WARN", code: 64, source: "legacy" });
    for (const value of upgraded) {
      expect(eventV2.isValid(value)).toBe(true);
      expect(eventV2.fromString(eventV2.toString(value))).toEqual(value);
    }
    expect(eventV1.fingerprint().equals(eventV2.fingerprint())).toBe(false);
  });

  test("an IDL protocol drives a binary message exchange", () => {
    /** Verifies: AV-CVI-006, AV-IDL-002, AV-BIN-003 */
    const protocol = readProtocol(
      "protocol Chat { record Join { string user; } record Post { string user; string body; int votes = 0; } }",
    );
    expect(protocol.protocol).toBe("Chat");
    const [joinSchema, postSchema] = protocol.types;
    const join = Type.forSchema(joinSchema);
    const post = Type.forSchema(postSchema) as types.RecordType;
    const manualPost = Type.forSchema({
      type: "record",
      name: "Post",
      fields: [
        { name: "user", type: "string" },
        { name: "body", type: "string" },
        { name: "votes", type: "int", default: 0 },
      ],
    });
    expect(post.equals(manualPost)).toBe(true);
    expect(post.fingerprint().equals(manualPost.fingerprint())).toBe(true);
    const wire = [
      join.toBuffer({ user: "ann" }),
      post.toBuffer({ user: "ann", body: "hi", votes: 2 }),
    ];
    expect({ ...join.fromBuffer(wire[0]) }).toEqual({ user: "ann" });
    expect({ ...manualPost.fromBuffer(wire[1]) }).toEqual({ user: "ann", body: "hi", votes: 2 });
    expect(post.field("votes").defaultValue()).toBe(0);
    expect(post.isValid({ user: "b", body: "x" })).toBe(true);
  });

  test("infer, refine, and evolve a log schema from samples", () => {
    /** Verifies: AV-CVI-004, AV-INF-002, AV-EVO-001, AV-CVI-005 */
    const samples = [
      { host: "a", ms: 3 },
      { host: "b", ms: 5 },
    ];
    const inferred = Type.forValue(samples[0]);
    for (const sample of samples) {
      expect(inferred.isValid(sample)).toBe(true);
    }
    const batch = samples.map((s) => inferred.toBuffer(s));
    const reader = Type.forSchema({
      type: "record",
      name: "LogLine",
      fields: [
        { name: "host", type: "string" },
        { name: "ms", type: "double" },
        { name: "region", type: "string", default: "eu" },
      ],
    });
    const resolver = reader.createResolver(inferred);
    const decoded = batch.map((buf) => reader.fromBuffer(buf, resolver));
    expect({ ...decoded[0] }).toEqual({ host: "a", ms: 3, region: "eu" });
    expect({ ...decoded[1] }).toEqual({ host: "b", ms: 5, region: "eu" });
    const sortedByValue = [...decoded].sort((x, y) => reader.compare(x, y)).map((v) => v.host);
    const sortedByBuffer = [...decoded]
      .map((v) => reader.toBuffer(v))
      .sort((x, y) => reader.compareBuffers(x, y))
      .map((buf) => reader.fromBuffer(buf).host);
    expect(sortedByValue).toEqual(["a", "b"]);
    expect(sortedByBuffer).toEqual(["a", "b"]);
    const merged = Type.forTypes([Type.forValue({ host: "c", ms: 1 }), Type.forValue({ host: "d", ms: 2.5 })]);
    expect(merged.isValid({ host: "c", ms: 1 })).toBe(true);
    expect(merged.isValid({ host: "d", ms: 2.5 })).toBe(true);
  });

  test("timestamps flow through a logical type end to end", () => {
    /** Verifies: AV-TYP-018, AV-CVI-001, AV-EVO-001, AV-JSN-003 */
    class Timestamp extends types.LogicalType {
      protected _fromValue(val: any) {
        return new Date(val);
      }
      protected _toValue(date: any) {
        return date instanceof Date ? +date : undefined;
      }
      protected _resolve(type: Type) {
        if (Type.isType(type, "long")) {
          return this._fromValue;
        }
      }
    }
    const event = Type.forSchema(
      {
        type: "record",
        name: "Event",
        fields: [
          { name: "name", type: "string" },
          { name: "at", type: { type: "long", logicalType: "ts" } },
        ],
      } as any,
      { logicalTypes: { ts: Timestamp } },
    ) as types.RecordType;
    expect(event.field("at").type.typeName).toBe("logical:ts");
    const value = { name: "boot", at: new Date(86400000) };
    expect(event.isValid(value)).toBe(true);
    expect(event.isValid({ name: "boot", at: 86400000 })).toBe(false);
    const viaBinary = event.fromBuffer(event.toBuffer(value));
    expect(viaBinary.at instanceof Date).toBe(true);
    expect(+viaBinary.at).toBe(86400000);
    const viaJson = event.fromString(event.toString(value));
    expect(viaJson.at instanceof Date).toBe(true);
    expect(+viaJson.at).toBe(86400000);
    const plainWriter = Type.forSchema({
      type: "record",
      name: "Event",
      fields: [
        { name: "name", type: "string" },
        { name: "at", type: "long" },
      ],
    });
    const migrated = event.fromBuffer(plainWriter.toBuffer({ name: "old", at: 1000 }), event.createResolver(plainWriter));
    expect(migrated.at instanceof Date).toBe(true);
    expect(+migrated.at).toBe(1000);
    expect(event.schema({ exportAttrs: true })).toEqual({
      name: "Event",
      type: "record",
      fields: [
        { name: "name", type: "string" },
        { name: "at", type: { type: "long", logicalType: "ts" } },
      ],
    });
  });

  test("a document store reads every version it ever wrote", () => {
    /** Verifies: AV-CVI-003, AV-EVO-004, AV-JSN-005, AV-CVI-002 */
    const v1 = Type.forSchema({ type: "record", name: "Doc", fields: [{ name: "id", type: "int" }] });
    const v2 = Type.forSchema({
      type: "record",
      name: "Doc",
      fields: [
        { name: "id", type: "long" },
        { name: "title", type: "string", default: "untitled" },
      ],
    });
    const v3 = Type.forSchema({
      type: "record",
      name: "Doc",
      fields: [
        { name: "docId", aliases: ["id"], type: "long" },
        { name: "title", type: "string", default: "untitled" },
        { name: "note", type: ["null", "string"], default: null },
      ],
    } as any);
    const store = [
      { version: v1, buf: v1.toBuffer({ id: 1 }) },
      { version: v2, buf: v2.toBuffer({ id: 2, title: "two" }) },
      { version: v3, buf: v3.toBuffer({ docId: 3, title: "three", note: "n" }) },
    ];
    const resolvers = new Map<Type, unknown>([
      [v1, v3.createResolver(v1)],
      [v2, v3.createResolver(v2)],
    ]);
    const loaded = store.map(({ version, buf }) =>
      version === v3 ? v3.fromBuffer(buf) : v3.fromBuffer(buf, resolvers.get(version) as any),
    );
    expect({ ...loaded[0] }).toEqual({ docId: 1, title: "untitled", note: null });
    expect({ ...loaded[1] }).toEqual({ docId: 2, title: "two", note: null });
    expect({ ...loaded[2] }).toEqual({ docId: 3, title: "three", note: "n" });
    for (const doc of loaded) {
      expect(v3.isValid(doc)).toBe(true);
    }
    const prints = [v1, v2, v3].map((t) => t.fingerprint().toString("hex"));
    expect(new Set(prints).size).toBe(3);
    const v3Copy = Type.forSchema(v3.schema());
    expect(v3Copy.equals(v3)).toBe(true);
  });

  test("a wrapped-union envelope routes typed payloads", () => {
    /** Verifies: AV-TYP-012, AV-CVI-001, AV-BIN-009 */
    const envelope = Type.forSchema(
      [
        "null",
        { type: "record", name: "Ping", fields: [{ name: "seq", type: "int" }] },
        { type: "record", name: "Data", fields: [{ name: "body", type: "string" }] },
      ] as any,
      { wrapUnions: true },
    );
    expect(envelope.typeName).toBe("union:wrapped");
    const messages = [{ Ping: { seq: 1 } }, { Data: { body: "hi" } }, null];
    const wire = messages.map((m) => envelope.toBuffer(m));
    const received = wire.map((buf) => envelope.fromBuffer(buf));
    expect(received[2]).toBeNull();
    const ping = received[0] as any;
    expect(Object.keys(ping)).toEqual(["Ping"]);
    expect({ ...ping.unwrap() }).toEqual({ seq: 1 });
    const data = received[1] as any;
    expect({ ...data.unwrap() }).toEqual({ body: "hi" });
    expect(envelope.isValid({ seq: 1 })).toBe(false);
    expect(envelope.isValid({ Ping: { seq: "x" } })).toBe(false);
    expect(() => envelope.toBuffer({ seq: 1 })).toThrow(Error);
    const json = envelope.toString(messages[0]);
    expect(JSON.parse(json)).toEqual({ Ping: { seq: 1 } });
    const back = envelope.fromString(json) as any;
    expect({ ...back.unwrap() }).toEqual({ seq: 1 });
  });
});
