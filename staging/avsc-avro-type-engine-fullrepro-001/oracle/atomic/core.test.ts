// Oracle - atomic tests for the avsc Avro type-engine specification.
import { describe, expect, test } from "vitest";
import { Type, types, readSchema, readProtocol } from "avsc";

const PERSON_SCHEMA = {
  type: "record",
  name: "Person",
  fields: [
    { name: "name", type: "string" },
    { name: "age", type: "int", default: 25 },
  ],
} as const;

function personType(): types.RecordType {
  return Type.forSchema(PERSON_SCHEMA as any) as types.RecordType;
}

function hex(buf: Buffer): string {
  return Buffer.from(buf).toString("hex");
}

describe("type construction", () => {
  test("the eight primitive names compile to types with matching typeName", () => {
    /** Verifies: AV-TYP-001 */
    const names = ["null", "boolean", "int", "long", "float", "double", "bytes", "string"];
    for (const name of names) {
      const t = Type.forSchema(name as any);
      expect(t.typeName).toBe(name);
      expect(Type.isType(t)).toBe(true);
    }
  });

  test("isType recognizes types and filters by typeName prefix", () => {
    /** Verifies: AV-TYP-001 */
    const int = Type.forSchema("int");
    expect(Type.isType(int)).toBe(true);
    expect(Type.isType({})).toBe(false);
    expect(Type.isType(null)).toBe(false);
    expect(Type.isType(int, "int")).toBe(true);
    expect(Type.isType(int, "string")).toBe(false);
    expect(Type.isType(int, "union", "int")).toBe(true);
  });

  test("record types expose typeName, name, and typed fields", () => {
    /** Verifies: AV-TYP-002 */
    const t = personType();
    expect(t.typeName).toBe("record");
    expect(t.name).toBe("Person");
    expect(t instanceof types.RecordType).toBe(true);
    expect(t.fields.map((f) => `${f.name}:${f.type.typeName}`)).toEqual(["name:string", "age:int"]);
  });

  test("field lookup returns declared metadata and defaults", () => {
    /** Verifies: AV-TYP-002, AV-TYP-004 */
    const t = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "age", type: "int", default: 25 },
        { name: "neu", aliases: ["old"], type: "int" },
      ],
    } as any) as types.RecordType;
    expect(t.field("age").defaultValue()).toBe(25);
    expect(t.field("age").order).toBe("ascending");
    expect(t.field("age").aliases).toEqual([]);
    expect(t.field("neu").aliases).toEqual(["old"]);
  });

  test("declared defaults let validation accept omitted fields", () => {
    /** Verifies: AV-TYP-004, AV-VAL-007 */
    const t = personType();
    expect(t.isValid({ name: "a" })).toBe(true);
    expect(t.isValid({ age: 3 })).toBe(false);
    expect(t.isValid({ name: "a", age: 1 })).toBe(true);
  });

  test("recordConstructor builds declaration-order instances", () => {
    /** Verifies: AV-TYP-003 */
    const t = Type.forSchema({
      type: "record",
      name: "Pt",
      fields: [{ name: "x", type: "int" }],
    }) as types.RecordType;
    const Ctor = t.recordConstructor;
    expect(Ctor.name).toBe("Pt");
    const inst = new Ctor(4);
    expect({ ...inst }).toEqual({ x: 4 });
    expect(t.isValid(inst)).toBe(true);
    const decoded = t.fromBuffer(t.toBuffer({ x: 1 }));
    expect(decoded.constructor.name).toBe("Pt");
    expect(decoded instanceof Ctor).toBe(true);
  });

  test("field defaults must validate against the field type", () => {
    /** Verifies: AV-TYP-004 */
    expect(() =>
      Type.forSchema({ type: "record", name: "R", fields: [{ name: "a", type: "int", default: "x" }] } as any),
    ).toThrow(Error);
    const ok = Type.forSchema({
      type: "record",
      name: "R2",
      fields: [{ name: "u", type: ["null", "int"], default: null }],
    } as any) as types.RecordType;
    expect(ok.field("u").defaultValue()).toBeNull();
    expect(() =>
      Type.forSchema({ type: "record", name: "R3", fields: [{ name: "u", type: ["null", "int"], default: 3 }] } as any),
    ).toThrow(Error);
  });

  test("a record schema without a name compiles with name undefined", () => {
    /** Verifies: AV-TYP-005 */
    const t = Type.forSchema({ type: "record", fields: [{ name: "a", type: "int" }] } as any);
    expect(t.typeName).toBe("record");
    expect(t.name).toBeUndefined();
    expect(t.isValid({ a: 1 })).toBe(true);
  });

  test("omitRecordMethods strips generated prototype methods", () => {
    /** Verifies: AV-TYP-006 */
    const plain = Type.forSchema({ type: "record", name: "A", fields: [{ name: "x", type: "int" }] });
    const decoded = plain.fromBuffer(plain.toBuffer({ x: 1 }));
    const defaultProto = Object.getOwnPropertyNames(Object.getPrototypeOf(decoded));
    expect(defaultProto.length).toBeGreaterThan(1);
    const bare = Type.forSchema(
      { type: "record", name: "B", fields: [{ name: "x", type: "int" }] },
      { omitRecordMethods: true },
    );
    const bareDecoded = bare.fromBuffer(bare.toBuffer({ x: 1 }));
    expect(Object.getOwnPropertyNames(Object.getPrototypeOf(bareDecoded))).toEqual(["constructor"]);
  });

  test("enums expose symbols and accept exactly those strings", () => {
    /** Verifies: AV-TYP-007, AV-VAL-006 */
    const t = Type.forSchema({ type: "enum", name: "Suit", symbols: ["SPADES", "HEARTS"] }) as types.EnumType;
    expect(t instanceof types.EnumType).toBe(true);
    expect(t.symbols).toEqual(["SPADES", "HEARTS"]);
    expect(t.isValid("SPADES")).toBe(true);
    expect(t.isValid("HEARTS")).toBe(true);
    expect(t.isValid("CLUBS")).toBe(false);
    expect(t.isValid(0)).toBe(false);
  });

  test("enum symbols must be valid identifiers", () => {
    /** Verifies: AV-TYP-007 */
    expect(() => Type.forSchema({ type: "enum", name: "E", symbols: ["bad-sym"] })).toThrow(Error);
  });

  test("fixeds expose size and accept only exact-length buffers", () => {
    /** Verifies: AV-TYP-008, AV-VAL-005 */
    const t = Type.forSchema({ type: "fixed", name: "Id", size: 4 }) as types.FixedType;
    expect(t instanceof types.FixedType).toBe(true);
    expect(t.size).toBe(4);
    expect(t.isValid(Buffer.alloc(4))).toBe(true);
    expect(t.isValid(Buffer.alloc(3))).toBe(false);
    expect(t.isValid("abcd")).toBe(false);
  });

  test("array and map types validate homogeneous containers", () => {
    /** Verifies: AV-TYP-009 */
    const a = Type.forSchema({ type: "array", items: "int" }) as types.ArrayType;
    expect(a instanceof types.ArrayType).toBe(true);
    expect(a.itemsType.typeName).toBe("int");
    expect(a.isValid([1, 2])).toBe(true);
    expect(a.isValid([1, "x"])).toBe(false);
    expect(a.isValid([])).toBe(true);
    const m = Type.forSchema({ type: "map", values: "string" }) as types.MapType;
    expect(m instanceof types.MapType).toBe(true);
    expect(m.valuesType.typeName).toBe("string");
    expect(m.isValid({ a: "x" })).toBe(true);
    expect(m.isValid({ a: 1 })).toBe(false);
  });

  test("duplicate branches and directly nested unions raise", () => {
    /** Verifies: AV-TYP-010 */
    expect(() => Type.forSchema(["int", "int"] as any)).toThrow(Error);
    expect(() => Type.forSchema([["int"], "string"] as any)).toThrow(Error);
  });

  test("unwrapped unions hold bare branch values", () => {
    /** Verifies: AV-TYP-011 */
    const t = Type.forSchema(["null", "int"] as any, { wrapUnions: false });
    expect(t.typeName).toBe("union:unwrapped");
    expect(t.isValid(null)).toBe(true);
    expect(t.isValid(1)).toBe(true);
    expect(t.isValid({ int: 1 })).toBe(false);
    expect(t.fromBuffer(t.toBuffer(1))).toBe(1);
    expect(t.fromBuffer(t.toBuffer(null))).toBeNull();
  });

  test("wrapped unions hold single-key branch objects with unwrap", () => {
    /** Verifies: AV-TYP-012 */
    const t = Type.forSchema(["null", "int"] as any, { wrapUnions: true });
    expect(t.typeName).toBe("union:wrapped");
    expect(t.isValid({ int: 1 })).toBe(true);
    expect(t.isValid(1)).toBe(false);
    expect(t.isValid(null)).toBe(true);
    const decoded = t.fromBuffer(t.toBuffer({ int: 1 }));
    expect({ ...decoded }).toEqual({ int: 1 });
    expect(decoded.unwrap()).toBe(1);
  });

  test("the default union mode wraps only ambiguous numeric unions", () => {
    /** Verifies: AV-TYP-013 */
    expect(Type.forSchema(["null", "int"] as any).typeName).toBe("union:unwrapped");
    expect(Type.forSchema(["int", "float"] as any).typeName).toBe("union:wrapped");
    expect(Type.forSchema(["int", "long"] as any).typeName).toBe("union:wrapped");
    expect(Type.forSchema(["int", "string"] as any, { wrapUnions: "auto" }).typeName).toBe("union:unwrapped");
  });

  test("names qualify through namespaces, dots, and the namespace option", () => {
    /** Verifies: AV-TYP-014 */
    const t = Type.forSchema({
      type: "record",
      name: "Person",
      namespace: "org.example",
      fields: [{ name: "x", type: "int" }],
    });
    expect(t.name).toBe("org.example.Person");
    const dotted = Type.forSchema({ type: "record", name: "a.B", fields: [{ name: "x", type: "int" }] });
    expect(dotted.name).toBe("a.B");
    const viaOpt = Type.forSchema(
      { type: "record", name: "Solo", fields: [{ name: "x", type: "int" }] },
      { namespace: "com.opt" },
    );
    expect(viaOpt.name).toBe("com.opt.Solo");
  });

  test("nested named types inherit the enclosing namespace unless dotted", () => {
    /** Verifies: AV-TYP-014 */
    const t = Type.forSchema({
      type: "record",
      name: "Outer",
      namespace: "ns",
      fields: [{ name: "inner", type: { type: "record", name: "Inner", fields: [{ name: "x", type: "int" }] } }],
    }) as types.RecordType;
    expect(t.field("inner").type.name).toBe("ns.Inner");
    const t2 = Type.forSchema({
      type: "record",
      name: "Outer2",
      namespace: "ns",
      fields: [{ name: "inner", type: { type: "record", name: "other.Inner2", fields: [{ name: "x", type: "int" }] } }],
    }) as types.RecordType;
    expect(t2.field("inner").type.name).toBe("other.Inner2");
  });

  test("a shared registry reuses compiled named types by reference", () => {
    /** Verifies: AV-TYP-015 */
    const registry: Record<string, Type> = {};
    const e = Type.forSchema({ type: "enum", name: "E", symbols: ["A", "B"] }, { registry });
    const r = Type.forSchema(
      { type: "record", name: "R", fields: [{ name: "e", type: "E" }] },
      { registry },
    ) as types.RecordType;
    expect(r.field("e").type).toBe(e);
    expect(Object.keys(registry).sort()).toEqual(["E", "R"]);
  });

  test("referencing an undefined type name raises", () => {
    /** Verifies: AV-TYP-016 */
    expect(() =>
      Type.forSchema({ type: "record", name: "R", fields: [{ name: "e", type: "Missing" }] }),
    ).toThrow(Error);
  });

  test("recursive references compile and validate", () => {
    /** Verifies: AV-TYP-017 */
    const t = Type.forSchema({
      type: "record",
      name: "Person",
      fields: [{ name: "friend", type: ["null", "Person"], default: null }],
    } as any);
    expect(t.isValid({ friend: { friend: null } })).toBe(true);
    expect(t.isValid({ friend: { friend: { friend: null } } })).toBe(true);
    expect(t.isValid({ friend: 3 })).toBe(false);
  });

  test("logical types wrap the underlying codec", () => {
    /** Verifies: AV-TYP-018 */
    class DateType extends types.LogicalType {
      protected _fromValue(val: any) {
        return new Date(val);
      }
      protected _toValue(date: any) {
        return date instanceof Date ? +date : undefined;
      }
    }
    const t = Type.forSchema({ type: "long", logicalType: "timestamp-millis" } as any, {
      logicalTypes: { "timestamp-millis": DateType },
    }) as types.LogicalType;
    expect(t.typeName).toBe("logical:timestamp-millis");
    expect(t.underlyingType.typeName).toBe("long");
    const back = t.fromBuffer(t.toBuffer(new Date(1234)));
    expect(back instanceof Date).toBe(true);
    expect(+back).toBe(1234);
    expect(t.isValid(new Date(5))).toBe(true);
    expect(t.isValid(123)).toBe(false);
  });

  test("unregistered logicalType attributes are ignored", () => {
    /** Verifies: AV-TYP-019 */
    const t = Type.forSchema({ type: "long", logicalType: "timestamp-millis" } as any);
    expect(t.typeName).toBe("long");
    expect(t.fromBuffer(t.toBuffer(5))).toBe(5);
  });
});

describe("validation and value algebra", () => {
  test("isValid answers without throwing on foreign shapes", () => {
    /** Verifies: AV-VAL-001 */
    const int = Type.forSchema("int");
    expect(int.isValid("x")).toBe(false);
    expect(int.isValid(null)).toBe(false);
    expect(int.isValid([])).toBe(false);
    expect(int.isValid(7)).toBe(true);
    const rec = Type.forSchema({ type: "record", name: "R", fields: [{ name: "a", type: "int" }] });
    expect(rec.isValid(null)).toBe(false);
    expect(rec.isValid("not a record")).toBe(false);
  });

  test("int accepts exactly signed 32-bit integers", () => {
    /** Verifies: AV-VAL-002 */
    const t = Type.forSchema("int");
    expect(t.isValid(1)).toBe(true);
    expect(t.isValid(1.5)).toBe(false);
    expect(t.isValid(2 ** 31)).toBe(false);
    expect(t.isValid(2 ** 31 - 1)).toBe(true);
    expect(t.isValid(-(2 ** 31))).toBe(true);
  });

  test("long, float, and double numeric domains", () => {
    /** Verifies: AV-VAL-003, AV-VAL-004 */
    const long = Type.forSchema("long");
    expect(long.isValid(9007199254740990)).toBe(true);
    expect(long.isValid(Number.MAX_SAFE_INTEGER)).toBe(false);
    expect(long.isValid(1.5)).toBe(false);
    const float = Type.forSchema("float");
    expect(float.isValid(1)).toBe(true);
    expect(float.isValid(0.5)).toBe(true);
    expect(float.isValid(Infinity)).toBe(true);
    expect(float.isValid("x")).toBe(false);
    const double = Type.forSchema("double");
    expect(double.isValid(0.1)).toBe(true);
    expect(double.isValid(NaN)).toBe(true);
    expect(double.isValid("0.1")).toBe(false);
  });

  test("bytes, string, and null value domains", () => {
    /** Verifies: AV-VAL-005 */
    const bytes = Type.forSchema("bytes");
    expect(bytes.isValid(Buffer.from([1]))).toBe(true);
    expect(bytes.isValid(new Uint8Array([1]))).toBe(false);
    expect(bytes.isValid("x")).toBe(false);
    const str = Type.forSchema("string");
    expect(str.isValid("s")).toBe(true);
    expect(str.isValid(1)).toBe(false);
    const nul = Type.forSchema("null");
    expect(nul.isValid(null)).toBe(true);
    expect(nul.isValid(undefined)).toBe(false);
    expect(nul.isValid(0)).toBe(false);
  });

  test("records validate declared fields and ignore extras by default", () => {
    /** Verifies: AV-VAL-007 */
    const t = Type.forSchema({ type: "record", name: "R", fields: [{ name: "a", type: "int" }] });
    expect(t.isValid({ a: 1, z: 2 })).toBe(true);
    expect(t.isValid({ a: "x" })).toBe(false);
    expect(t.isValid({})).toBe(false);
  });

  test("noUndeclaredFields rejects undeclared properties", () => {
    /** Verifies: AV-VAL-008 */
    const t = Type.forSchema({ type: "record", name: "R", fields: [{ name: "a", type: "int" }] });
    expect(t.isValid({ a: 1, z: 2 })).toBe(true);
    expect(t.isValid({ a: 1, z: 2 }, { noUndeclaredFields: true })).toBe(false);
    expect(t.isValid({ a: 1 }, { noUndeclaredFields: true })).toBe(true);
  });

  test("errorHook reports each mismatch with its path", () => {
    /** Verifies: AV-VAL-009 */
    const nested = Type.forSchema({
      type: "record",
      name: "Outer",
      fields: [{ name: "inner", type: { type: "record", name: "Inner", fields: [{ name: "x", type: "int" }] } }],
    });
    const seen: Array<[string[], unknown]> = [];
    nested.isValid({ inner: { x: "bad" } }, { errorHook: (path, value) => seen.push([path.slice(), value]) });
    expect(seen).toEqual([[["inner", "x"], "bad"]]);
    const flat = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "a", type: "int" },
        { name: "b", type: "string" },
      ],
    });
    const paths: string[] = [];
    flat.isValid({ a: "x", b: 2 }, { errorHook: (path) => paths.push(path.join(".")) });
    expect(paths).toEqual(["a", "b"]);
  });

  test("clone deep-copies valid values and rejects invalid ones", () => {
    /** Verifies: AV-VAL-010 */
    const t = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "name", type: "string" },
        { name: "tags", type: { type: "array", items: "int" } },
      ],
    });
    const original = { name: "x", tags: [1, 2] };
    const copy = t.clone(original);
    expect({ ...copy, tags: [...copy.tags] }).toEqual(original);
    copy.tags.push(3);
    expect(original.tags).toEqual([1, 2]);
    expect(() => t.clone({ name: "x", tags: "no" })).toThrow(Error);
  });

  test("coerceBuffers converts JSON buffer shapes during clone", () => {
    /** Verifies: AV-VAL-011 */
    const t = Type.forSchema({ type: "record", name: "P", fields: [{ name: "b", type: "bytes" }] });
    expect(() => t.clone({ b: { type: "Buffer", data: [1, 2] } })).toThrow(Error);
    const coerced = t.clone({ b: { type: "Buffer", data: [1, 2] } }, { coerceBuffers: true });
    expect(hex(coerced.b)).toBe("0102");
  });

  test("clone drops undeclared properties in every mode", () => {
    /** Verifies: AV-VAL-012 */
    const t = Type.forSchema({ type: "record", name: "Q", fields: [{ name: "a", type: "int" }] });
    expect({ ...t.clone({ a: 1, extra: 9 }) }).toEqual({ a: 1 });
    expect({ ...t.clone({ a: 1, extra: 9 }, { stripUndeclaredFields: true } as any) }).toEqual({ a: 1 });
  });

  test("compare follows Avro order with field order attributes", () => {
    /** Verifies: AV-VAL-013 */
    const int = Type.forSchema("int");
    expect(int.compare(1, 2)).toBe(-1);
    expect(int.compare(2, 1)).toBe(1);
    expect(int.compare(1, 1)).toBe(0);
    const desc = Type.forSchema({
      type: "record",
      name: "R",
      fields: [{ name: "a", type: "int", order: "descending" }],
    });
    expect(desc.compare({ a: 1 }, { a: 2 })).toBe(1);
    const ignored = Type.forSchema({
      type: "record",
      name: "S",
      fields: [
        { name: "a", type: "int", order: "ignore" },
        { name: "b", type: "int" },
      ],
    } as any);
    expect(ignored.compare({ a: 9, b: 1 }, { a: 0, b: 1 })).toBe(0);
    expect(ignored.compare({ a: 0, b: 1 }, { a: 9, b: 2 })).toBe(-1);
  });

  test("compareBuffers agrees with compare", () => {
    /** Verifies: AV-VAL-014 */
    const int = Type.forSchema("int");
    expect(int.compareBuffers(int.toBuffer(1), int.toBuffer(2))).toBe(-1);
    expect(int.compareBuffers(int.toBuffer(2), int.toBuffer(2))).toBe(0);
    const rec = Type.forSchema({
      type: "record",
      name: "S",
      fields: [
        { name: "a", type: "int", order: "ignore" },
        { name: "b", type: "int" },
      ],
    } as any);
    expect(rec.compareBuffers(rec.toBuffer({ a: 9, b: 1 }), rec.toBuffer({ a: 0, b: 2 }))).toBe(-1);
  });

  test("random produces values the type validates", () => {
    /** Verifies: AV-VAL-015 */
    const rec = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    expect(rec.isValid(rec.random())).toBe(true);
    const en = Type.forSchema({ type: "enum", name: "E", symbols: ["X", "Y"] });
    expect(en.isValid(en.random())).toBe(true);
    const un = Type.forSchema(["null", "int"] as any);
    expect(un.isValid(un.random())).toBe(true);
  });

  test("wrap boxes values in their branch shape", () => {
    /** Verifies: AV-VAL-015 */
    const int = Type.forSchema("int");
    const boxed = int.wrap(5);
    expect(Object.keys(boxed)).toEqual(["int"]);
    expect(boxed.int).toBe(5);
  });
});

describe("binary encoding", () => {
  test("toBuffer, toString, and clone raise on invalid values", () => {
    /** Verifies: AV-BIN-001, AV-ERR-002 */
    const int = Type.forSchema("int");
    expect(() => int.toBuffer("x" as any)).toThrow(Error);
    expect(() => int.toString("x")).toThrow(Error);
    expect(() => int.clone("x")).toThrow(Error);
  });

  test("fromBuffer raises on truncated and trailing bytes", () => {
    /** Verifies: AV-BIN-002, AV-ERR-002 */
    const int = Type.forSchema("int");
    expect(() => int.fromBuffer(Buffer.from([]))).toThrow(Error);
    expect(() => int.fromBuffer(Buffer.from([0x02, 0x02]))).toThrow(Error);
    expect(int.fromBuffer(Buffer.from([0x02]))).toBe(1);
  });

  test("binary round trips return equal constructor instances", () => {
    /** Verifies: AV-BIN-003 */
    const t = personType();
    const buf = t.toBuffer({ name: "ab", age: 3 });
    expect(hex(buf)).toBe("04616206");
    const back = t.fromBuffer(buf);
    expect(back).toEqual({ name: "ab", age: 3 });
    expect(back.constructor.name).toBe("Person");
  });

  test("ints and longs use zigzag varints", () => {
    /** Verifies: AV-BIN-004 */
    const int = Type.forSchema("int");
    expect(hex(int.toBuffer(1))).toBe("02");
    expect(hex(int.toBuffer(-1))).toBe("01");
    expect(hex(int.toBuffer(64))).toBe("8001");
    expect(int.fromBuffer(int.toBuffer(12345))).toBe(12345);
    const long = Type.forSchema("long");
    expect(long.fromBuffer(long.toBuffer(9007199254740990))).toBe(9007199254740990);
  });

  test("strings and bytes are length-prefixed and UTF-8", () => {
    /** Verifies: AV-BIN-005 */
    const str = Type.forSchema("string");
    expect(hex(str.toBuffer("hi"))).toBe("046869");
    expect(hex(str.toBuffer("é"))).toBe("04c3a9");
    expect(str.fromBuffer(str.toBuffer("héllo"))).toBe("héllo");
    const bytes = Type.forSchema("bytes");
    const encoded = bytes.toBuffer(Buffer.from([1, 2, 3]));
    expect(hex(encoded)).toBe("06010203");
    expect(hex(bytes.fromBuffer(encoded))).toBe("010203");
  });

  test("float, double, boolean, and null encodings", () => {
    /** Verifies: AV-BIN-006 */
    const float = Type.forSchema("float");
    expect(hex(float.toBuffer(0.5))).toBe("0000003f");
    const double = Type.forSchema("double");
    expect(hex(double.toBuffer(0.5))).toBe("000000000000e03f");
    const bool = Type.forSchema("boolean");
    expect(hex(bool.toBuffer(true))).toBe("01");
    expect(hex(bool.toBuffer(false))).toBe("00");
    const nul = Type.forSchema("null");
    expect(nul.toBuffer(null).length).toBe(0);
  });

  test("enums encode indices and fixeds copy raw bytes", () => {
    /** Verifies: AV-BIN-007 */
    const en = Type.forSchema({ type: "enum", name: "Suit", symbols: ["SPADES", "HEARTS"] });
    expect(hex(en.toBuffer("SPADES"))).toBe("00");
    expect(hex(en.toBuffer("HEARTS"))).toBe("02");
    const fixed = Type.forSchema({ type: "fixed", name: "Id", size: 4 });
    expect(hex(fixed.toBuffer(Buffer.from([1, 2, 3, 4])))).toBe("01020304");
  });

  test("arrays and maps encode counted blocks with terminators", () => {
    /** Verifies: AV-BIN-008 */
    const arr = Type.forSchema({ type: "array", items: "int" });
    expect(hex(arr.toBuffer([1, 2]))).toBe("04020400");
    expect(hex(arr.toBuffer([]))).toBe("00");
    expect(arr.fromBuffer(arr.toBuffer([1, 2]))).toEqual([1, 2]);
    const map = Type.forSchema({ type: "map", values: "int" });
    expect(hex(map.toBuffer({ a: 1 }))).toBe("0202610200");
    expect(map.fromBuffer(map.toBuffer({ a: 1, b: 2 }))).toEqual({ a: 1, b: 2 });
  });

  test("unions encode a branch tag before the branch value", () => {
    /** Verifies: AV-BIN-009 */
    const t = Type.forSchema(["null", "int"] as any);
    expect(hex(t.toBuffer(null))).toBe("00");
    expect(hex(t.toBuffer(1))).toBe("0202");
  });

  test("record fields encode in declaration order without markers", () => {
    /** Verifies: AV-BIN-010 */
    const ab = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "a", type: "int" },
        { name: "b", type: "int" },
      ],
    });
    const ba = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "b", type: "int" },
        { name: "a", type: "int" },
      ],
    });
    expect(hex(ab.toBuffer({ a: 1, b: 2 }))).toBe("0204");
    expect(hex(ba.toBuffer({ a: 1, b: 2 }))).toBe("0402");
  });

  test("float narrows doubles to single precision", () => {
    /** Verifies: AV-BIN-011 */
    const float = Type.forSchema("float");
    const roundTripped = float.fromBuffer(float.toBuffer(0.1));
    expect(roundTripped).not.toBe(0.1);
    expect(Math.abs(roundTripped - 0.1)).toBeLessThan(1e-7);
  });
});

describe("JSON codec and schema projection", () => {
  test("toString and fromString round-trip record values", () => {
    /** Verifies: AV-JSN-001, AV-JSN-002 */
    const t = Type.forSchema({
      type: "record",
      name: "P",
      fields: [
        { name: "a", type: "int" },
        { name: "b", type: "bytes" },
      ],
    });
    const text = t.toString({ a: 1, b: Buffer.from([255]) });
    expect(text).toBe('{"a":1,"b":"ÿ"}');
    const back = t.fromString(text);
    expect(back.a).toBe(1);
    expect(hex(back.b)).toBe("ff");
  });

  test("union values serialize as branch-keyed JSON in every mode", () => {
    /** Verifies: AV-JSN-001, AV-JSN-002 */
    const unwrapped = Type.forSchema(["null", "int"] as any);
    expect(unwrapped.toString(1)).toBe('{"int":1}');
    expect(unwrapped.toString(null)).toBe("null");
    expect(unwrapped.fromString('{"int": 1}')).toBe(1);
    expect(unwrapped.fromString("null")).toBeNull();
    const wrapped = Type.forSchema(["null", "int"] as any, { wrapUnions: true });
    expect(wrapped.toString({ int: 5 })).toBe('{"int":5}');
    expect({ ...wrapped.fromString('{"int": 5}') }).toEqual({ int: 5 });
  });

  test("schema output is canonical unless attributes are exported", () => {
    /** Verifies: AV-JSN-003 */
    const t = Type.forSchema({
      type: "record",
      name: "Person",
      fields: [{ name: "age", type: "int", default: 25 }],
    });
    expect(t.schema()).toEqual({ name: "Person", type: "record", fields: [{ name: "age", type: "int" }] });
    expect(t.schema({ exportAttrs: true })).toEqual({
      name: "Person",
      type: "record",
      fields: [{ name: "age", type: "int", default: 25 }],
    });
  });

  test("noDeref and toJSON projections", () => {
    /** Verifies: AV-JSN-003, AV-JSN-004 */
    const t = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    expect(t.schema({ noDeref: true })).toBe("P");
    expect(t.toJSON()).toEqual(t.schema());
    expect(Type.forSchema("int").schema()).toBe("int");
  });

  test("toString without a value prints the schema with names dereferenced once", () => {
    /** Verifies: AV-JSN-004 */
    const named = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    expect(named.toString()).toBe('"P"');
    expect(named.toString()).toBe('"P"');
    const arr = Type.forSchema({ type: "array", items: "int" });
    expect(JSON.parse(arr.toString())).toEqual({ type: "array", items: "int" });
  });

  test("fingerprints digest the canonical schema", () => {
    /** Verifies: AV-JSN-005 */
    const a = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    expect(a.fingerprint().length).toBe(16);
    const b = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    expect(b.fingerprint().equals(a.fingerprint())).toBe(true);
    const decorated = Type.forSchema({
      type: "record",
      name: "P",
      doc: "docs",
      fields: [{ name: "a", type: "int", default: 3, order: "descending" }],
    } as any);
    expect(decorated.fingerprint().equals(a.fingerprint())).toBe(true);
    const different = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "long" }] });
    expect(different.fingerprint().equals(a.fingerprint())).toBe(false);
  });

  test("equals compares canonical schemas", () => {
    /** Verifies: AV-JSN-006 */
    const a = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    const b = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    const c = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "long" }] });
    expect(a.equals(b)).toBe(true);
    expect(a.equals(c)).toBe(false);
  });
});

describe("schema evolution", () => {
  test("primitive promotions resolve and demotions raise", () => {
    /** Verifies: AV-EVO-001 */
    const int = Type.forSchema("int");
    const long = Type.forSchema("long");
    const double = Type.forSchema("double");
    expect(long.fromBuffer(int.toBuffer(7), long.createResolver(int))).toBe(7);
    expect(double.fromBuffer(int.toBuffer(7), double.createResolver(int))).toBe(7);
    expect(() => int.createResolver(double)).toThrow(Error);
  });

  test("string and bytes promote to each other", () => {
    /** Verifies: AV-EVO-001 */
    const str = Type.forSchema("string");
    const bytes = Type.forSchema("bytes");
    expect(hex(bytes.fromBuffer(str.toBuffer("hi"), bytes.createResolver(str)))).toBe("6869");
    expect(str.fromBuffer(bytes.toBuffer(Buffer.from("hi")), str.createResolver(bytes))).toBe("hi");
  });

  test("containers and fixeds resolve elementwise", () => {
    /** Verifies: AV-EVO-002 */
    const wa = Type.forSchema({ type: "array", items: "int" });
    const ra = Type.forSchema({ type: "array", items: "long" });
    expect(ra.fromBuffer(wa.toBuffer([1, 2]), ra.createResolver(wa))).toEqual([1, 2]);
    const wm = Type.forSchema({ type: "map", values: "int" });
    const rm = Type.forSchema({ type: "map", values: "double" });
    expect(rm.fromBuffer(wm.toBuffer({ a: 1 }), rm.createResolver(wm))).toEqual({ a: 1 });
    const wf = Type.forSchema({ type: "fixed", name: "F", size: 2 });
    const rf = Type.forSchema({ type: "fixed", name: "F", size: 2 });
    expect(hex(rf.fromBuffer(wf.toBuffer(Buffer.from([1, 2])), rf.createResolver(wf)))).toBe("0102");
    const rBad = Type.forSchema({ type: "fixed", name: "F", size: 3 });
    expect(() => rBad.createResolver(wf)).toThrow(Error);
  });

  test("enum evolution honors reader defaults", () => {
    /** Verifies: AV-EVO-003 */
    const writer = Type.forSchema({ type: "enum", name: "E", symbols: ["A", "B", "C"] });
    const strict = Type.forSchema({ type: "enum", name: "E", symbols: ["A", "B"] });
    expect(() => strict.createResolver(writer)).toThrow(Error);
    const defaulted = Type.forSchema({ type: "enum", name: "E", symbols: ["A", "B"], default: "A" } as any);
    const resolver = defaulted.createResolver(writer);
    expect(defaulted.fromBuffer(writer.toBuffer("C"), resolver)).toBe("A");
    expect(defaulted.fromBuffer(writer.toBuffer("B"), resolver)).toBe("B");
  });

  test("record evolution fills defaults and follows aliases", () => {
    /** Verifies: AV-EVO-004 */
    const writer = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    const reader = Type.forSchema({
      type: "record",
      name: "P",
      fields: [
        { name: "a", type: "long" },
        { name: "b", type: "string", default: "hey" },
      ],
    });
    expect(reader.fromBuffer(writer.toBuffer({ a: 5 }), reader.createResolver(writer))).toEqual({ a: 5, b: "hey" });
    const oldType = Type.forSchema({ type: "record", name: "Old", fields: [{ name: "x", type: "int" }] });
    const renamed = Type.forSchema({
      type: "record",
      name: "New",
      aliases: ["Old"],
      fields: [{ name: "x", type: "int" }],
    });
    expect(renamed.fromBuffer(oldType.toBuffer({ x: 3 }), renamed.createResolver(oldType))).toEqual({ x: 3 });
    const fieldWriter = Type.forSchema({ type: "record", name: "R", fields: [{ name: "old", type: "int" }] });
    const fieldReader = Type.forSchema({
      type: "record",
      name: "R",
      fields: [{ name: "neu", aliases: ["old"], type: "int" }],
    } as any);
    expect(fieldReader.fromBuffer(fieldWriter.toBuffer({ old: 4 }), fieldReader.createResolver(fieldWriter))).toEqual({
      neu: 4,
    });
  });

  test("unresolvable schemas raise at resolver creation", () => {
    /** Verifies: AV-EVO-004, AV-EVO-005, AV-EVO-007 */
    const writer = Type.forSchema({ type: "record", name: "P", fields: [{ name: "a", type: "int" }] });
    const defaultless = Type.forSchema({ type: "record", name: "P", fields: [{ name: "c", type: "string" }] });
    expect(() => defaultless.createResolver(writer)).toThrow(Error);
    const int = Type.forSchema("int");
    const writerUnion = Type.forSchema(["null", "int"] as any);
    expect(() => int.createResolver(writerUnion)).toThrow(Error);
  });

  test("reader unions absorb writer non-unions", () => {
    /** Verifies: AV-EVO-006 */
    const readerUnwrapped = Type.forSchema(["null", "int"] as any);
    const int = Type.forSchema("int");
    expect(readerUnwrapped.fromBuffer(int.toBuffer(9), readerUnwrapped.createResolver(int))).toBe(9);
    const readerWrapped = Type.forSchema(["null", "string"] as any, { wrapUnions: true });
    const str = Type.forSchema("string");
    const decoded = readerWrapped.fromBuffer(str.toBuffer("q"), readerWrapped.createResolver(str));
    expect({ ...decoded }).toEqual({ string: "q" });
    const writerUnion = Type.forSchema(["null", "int"] as any);
    const readerUnion = Type.forSchema(["null", "long"] as any);
    const resolver = readerUnion.createResolver(writerUnion);
    expect(readerUnion.fromBuffer(writerUnion.toBuffer(5), resolver)).toBe(5);
    expect(readerUnion.fromBuffer(writerUnion.toBuffer(null), resolver)).toBeNull();
  });

  test("reader non-unions require every writer branch to resolve", () => {
    /** Verifies: AV-EVO-007 */
    const writer = Type.forSchema(["int", "long"] as any, { wrapUnions: true });
    const long = Type.forSchema("long");
    const resolver = long.createResolver(writer);
    expect(long.fromBuffer(writer.toBuffer({ int: 7 }), resolver)).toBe(7);
    expect(long.fromBuffer(writer.toBuffer({ long: 9 }), resolver)).toBe(9);
    const withNull = Type.forSchema(["null", "long"] as any);
    expect(() => long.createResolver(withNull)).toThrow(Error);
  });

  test("resolver decoding reorders fields and skips writer extras", () => {
    /** Verifies: AV-EVO-008 */
    const writer = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "a", type: "int" },
        { name: "b", type: "int" },
      ],
    });
    const reader = Type.forSchema({
      type: "record",
      name: "R",
      fields: [
        { name: "b", type: "int" },
        { name: "a", type: "int" },
      ],
    });
    const decoded = reader.fromBuffer(writer.toBuffer({ a: 1, b: 2 }), reader.createResolver(writer));
    expect(Object.keys(decoded)).toEqual(["b", "a"]);
    expect({ ...decoded }).toEqual({ a: 1, b: 2 });
    const wide = Type.forSchema({
      type: "record",
      name: "S",
      fields: [
        { name: "a", type: "int" },
        { name: "junk", type: "string" },
      ],
    });
    const narrow = Type.forSchema({ type: "record", name: "S", fields: [{ name: "a", type: "int" }] });
    expect({ ...narrow.fromBuffer(wide.toBuffer({ a: 7, junk: "zz" }), narrow.createResolver(wide)) }).toEqual({
      a: 7,
    });
  });

  test("resolvers bind to their creating instance", () => {
    /** Verifies: AV-EVO-009 */
    const int = Type.forSchema("int");
    const double = Type.forSchema("double");
    const resolver = double.createResolver(int);
    expect(double.fromBuffer(int.toBuffer(7), resolver)).toBe(7);
    const otherDouble = Type.forSchema("double");
    expect(() => otherDouble.fromBuffer(int.toBuffer(7), resolver)).toThrow(Error);
  });
});

describe("type inference", () => {
  test("forValue infers primitive types", () => {
    /** Verifies: AV-INF-001 */
    expect(Type.forValue(1 as any).typeName).toBe("int");
    expect(Type.forValue(1.5 as any).typeName).toBe("float");
    expect(Type.forValue("x" as any).typeName).toBe("string");
    expect(Type.forValue(true as any).typeName).toBe("boolean");
    expect(Type.forValue(null as any).typeName).toBe("null");
    expect(Type.forValue(Buffer.from([1])).typeName).toBe("bytes");
  });

  test("forValue infers containers and anonymous records", () => {
    /** Verifies: AV-INF-001 */
    expect(Type.forValue([1, 2]).schema()).toEqual({ type: "array", items: "int" });
    expect(Type.forValue([1, 2.5]).schema()).toEqual({ type: "array", items: "float" });
    expect(Type.forValue({ a: 1, b: "x" }).schema()).toEqual({
      type: "record",
      fields: [
        { name: "a", type: "int" },
        { name: "b", type: "string" },
      ],
    });
    expect(Type.forValue({ a: [1], b: { c: "x" } }).schema()).toEqual({
      type: "record",
      fields: [
        { name: "a", type: { type: "array", items: "int" } },
        { name: "b", type: { type: "record", fields: [{ name: "c", type: "string" }] } },
      ],
    });
  });

  test("forTypes widens numbers and unions incompatibles", () => {
    /** Verifies: AV-INF-002 */
    const widened = Type.forTypes([Type.forSchema("int"), Type.forSchema("long")]);
    expect(widened.schema()).toBe("long");
    const mixed = Type.forTypes([Type.forSchema("int"), Type.forSchema("string")]);
    expect(mixed.typeName).toBe("union:unwrapped");
    expect(mixed.schema()).toEqual(["int", "string"]);
    expect(mixed.isValid(3)).toBe(true);
    expect(mixed.isValid("s")).toBe(true);
  });
});

describe("IDL parsing", () => {
  test("readSchema produces forSchema-ready shapes", () => {
    /** Verifies: AV-IDL-001 */
    const record = readSchema("record Person { string name; int age = 25; }");
    expect(record).toEqual({
      type: "record",
      name: "Person",
      fields: [
        { type: "string", name: "name" },
        { type: "int", name: "age", default: 25 },
      ],
    });
    const compiled = Type.forSchema(record) as types.RecordType;
    expect(compiled.name).toBe("Person");
    expect(compiled.field("age").defaultValue()).toBe(25);
    expect(readSchema("union { null, string }")).toEqual(["null", "string"]);
    expect(readSchema("map<int>")).toEqual({ type: "map", values: "int" });
    expect(readSchema("array<string>")).toEqual({ type: "array", items: "string" });
  });

  test("readProtocol parses protocols with messages", () => {
    /** Verifies: AV-IDL-002 */
    const protocol = readProtocol("protocol Ping { record Beat { int count; } null ping(); }");
    expect(protocol.protocol).toBe("Ping");
    expect(protocol.types).toEqual([
      { type: "record", name: "Beat", fields: [{ type: "int", name: "count" }] },
    ]);
    expect(protocol.messages).toEqual({ ping: { request: [], response: "null" } });
  });

  test("malformed IDL raises", () => {
    /** Verifies: AV-IDL-003 */
    expect(() => readSchema("record {")).toThrow(Error);
    expect(() => readProtocol("protocol x")).toThrow(Error);
  });
});
