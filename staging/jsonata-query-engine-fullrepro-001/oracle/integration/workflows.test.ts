// Oracle - integration tests for the jsonata query-and-transformation engine specification.
import { describe, expect, test } from "vitest";
import jsonata from "jsonata";

const STORE = {
  Account: {
    Name: "acme",
    Order: [
      { OrderID: "o1", Product: [{ Name: "p1", Price: 10, Qty: 2 }, { Name: "p2", Price: 5, Qty: 1 }] },
      { OrderID: "o2", Product: [{ Name: "p3", Price: 100, Qty: 1 }] },
    ],
  },
};

/** Projects an evaluation result onto plain JSON, since the spec contracts JSON values. */
function norm(value: unknown): unknown {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

async function run(source: string, input: unknown = {}, bindings?: Record<string, unknown>): Promise<unknown> {
  return norm(await jsonata(source).evaluate(input, bindings));
}

async function runErr(source: string, input: unknown = {}): Promise<any> {
  try {
    await jsonata(source).evaluate(input);
  } catch (err) {
    return err;
  }
  throw new Error(`expected evaluation of ${source} to reject`);
}

describe("query and transformation workflows", () => {
  test("an order analytics report groups line revenue per sku and counts group sizes", async () => {
    /** Verifies: JN-CON-003, JN-PATH-005, JN-LIB-011, JN-PATH-002 */
    const orders = {
      Order: [
        { id: "A", items: [{ sku: "x", price: 10, qty: 2 }, { sku: "y", price: 5, qty: 1 }] },
        { id: "B", items: [{ sku: "x", price: 10, qty: 1 }] },
      ],
    };
    expect(await run("Order.items{sku: $sum($.(price*qty))}", orders)).toEqual({ x: 30, y: 5 });
    expect(await run("Order.items{sku: $count($)}", orders)).toEqual({ x: 2, y: 1 });
  });

  test("a discount pipeline transforms the catalog copy and leaves the source untouched", async () => {
    /** Verifies: JN-CON-005, JN-FUN-001, JN-LIB-011, JN-OP-010 */
    const cat = { catalog: { items: [{ sku: "x", price: 10 }, { sku: "y", price: 4 }] } };
    const report = await run(
      "($d := $ ~> |catalog.items|{'price': price / 2}|; {'before': $sum(catalog.items.price), 'after': $sum($d.catalog.items.price)})",
      cat,
    );
    expect(report).toEqual({ before: 14, after: 7 });
    expect(cat.catalog.items[0].price).toBe(10);
  });

  test("a registered scoring function drives predicates and descending sort end to end", async () => {
    /** Verifies: JN-BND-003, JN-PATH-008, JN-CON-004 */
    const expr = jsonata("products[$score(rating) >= 2]^(>$score(rating)).name");
    expr.registerFunction("score", (r: number) => Math.round(r), "<n:n>");
    const input = { products: [{ name: "a", rating: 1.2 }, { name: "b", rating: 2.6 }, { name: "c", rating: 1.9 }] };
    expect(norm(await expr.evaluate(input))).toEqual(["b", "c"]);
  });

  test("recursive lambdas fold a tree with existence guards and aggregation", async () => {
    /** Verifies: JN-FUN-004, JN-LIB-016, JN-LIB-014, JN-LIB-011, JN-OP-008 */
    const tree = { value: 1, children: [{ value: 2, children: [{ value: 4 }] }, { value: 3 }] };
    expect(
      await run("($total := function($n){$n.value + ($exists($n.children) ? $sum($map($n.children, $total)) : 0)}; $total($))", tree),
    ).toBe(10);
  });

  test("a slug pipeline chains case mapping, splitting, and joining", async () => {
    /** Verifies: JN-OP-010, JN-LIB-003, JN-LIB-004 */
    expect(await run("'Hello Big World' ~> $lowercase ~> $split(' ') ~> $join('-')")).toBe("hello-big-world");
  });

  test("a regex replacement function converts and re-renders numbers in place", async () => {
    /** Verifies: JN-LIB-005, JN-LIB-007, JN-LIB-001 */
    expect(await run("$replace('a1b2', /\\d/, function($m){$string($number($m.match)+1)})")).toBe("a2b3");
  });

  test("datetime values survive picture-driven round trips", async () => {
    /** Verifies: JN-DT-001, JN-DT-002 */
    expect(await run("$fromMillis($toMillis('23/03/2018', '[D01]/[M01]/[Y0001]'), '[Y0001]-[M01]-[D01]')")).toBe("2018-03-23");
    expect(await run("$toMillis($fromMillis(1521801216617))")).toBe(1521801216617);
  });

  test("a paginated projection combines positional binds, predicates, and sequence rules", async () => {
    /** Verifies: JN-PATH-007, JN-PATH-008, JN-PATH-001, JN-FUN-001 */
    const input = { items: [{ name: "a" }, { name: "b" }, { name: "c" }] };
    expect(
      await run(
        "($size := 2; $withPos := items#$i.{'i': $i, 'name': name}; {'page1': $withPos[i < $size].name, 'page2': $withPos[i >= $size].name})",
        input,
      ),
    ).toEqual({ page1: ["a", "b"], page2: "c" });
  });

  test("parent references feed a grouping that indexes products by order", async () => {
    /** Verifies: JN-PATH-006, JN-CON-003, JN-CON-001 */
    expect(await run("(Account.Order.Product.{'o': %.OrderID, 'n': Name}){n: o}", STORE)).toEqual({
      p1: "o1",
      p2: "o1",
      p3: "o2",
    });
  });

  test("dynamically composed sources evaluate through $eval", async () => {
    /** Verifies: JN-LIB-006, JN-OP-006, JN-LIB-012, JN-OP-005 */
    const input = { items: [{ name: "a" }, { name: "b" }, { name: "c" }] };
    expect(await run("$eval('[1..' & $count(items) & ']')", input)).toEqual([1, 2, 3]);
  });

  test("async and sync host functions combine with library calls in one expression", async () => {
    /** Verifies: JN-BND-003, JN-LIB-011, JN-OP-001 */
    const expr = jsonata("$af() + $sf() + $sum([1,2])");
    expr.registerFunction("af", async () => 30);
    expr.registerFunction("sf", () => 9);
    expect(await expr.evaluate({})).toBe(42);
  });

  test("one compiled expression serves many inputs while call bindings stay per-call", async () => {
    /** Verifies: JN-CMP-005, JN-BND-001, JN-BND-002 */
    const expr = jsonata("$x");
    expr.assign("x", 1);
    expect(await expr.evaluate({}, { x: 2 })).toBe(2);
    expect(await expr.evaluate({})).toBe(1);
    const adder = jsonata("a + $b");
    expect(await adder.evaluate({ a: 1 }, { b: 10 })).toBe(11);
    expect(await adder.evaluate({ a: 5 }, { b: 100 })).toBe(105);
  });

  test("a configuration is filtered, remapped, and merged through object combinators", async () => {
    /** Verifies: JN-LIB-014, JN-LIB-015, JN-CON-001, JN-FUN-004 */
    expect(
      await run(
        "($cfg := {'a':1,'ab':2,'abc':3}; $merge($each($sift($cfg, function($v,$k){$length($k)>1}), function($v,$k){{$k: $v*10}})))",
      ),
    ).toEqual({ ab: 20, abc: 30 });
  });

  test("a sorted distinct union of arrays reproduces an integer range", async () => {
    /** Verifies: JN-LIB-013, JN-OP-005, JN-OP-003 */
    expect(await run("$sort($distinct($append([3,1,2],[2,4])))")).toEqual([1, 2, 3, 4]);
    expect(await run("$sort($distinct($append([3,1,2],[2,4]))) = [1..4]")).toBe(true);
  });

  test("guarded defaults keep a report total while assertions reject bad documents", async () => {
    /** Verifies: JN-OP-009, JN-LIB-017, JN-ERR-001 */
    const partial = { lines: [{ amount: 5 }] };
    expect(await run("{'total': $sum(lines.amount), 'currency': currency ?? 'USD'}", partial)).toEqual({
      total: 5,
      currency: "USD",
    });
    const err = await runErr("$assert($exists(currency), 'currency required')", partial);
    expect(err.code).toBe("D3141");
    expect(err.token).toBe("assert");
  });
});

describe("cross-view invariants", () => {
  test("sequence rules hold identically across paths, predicates, and library filters", async () => {
    /** Verifies: JN-CVI-001 */
    expect(await run("Account.Order.Product[Price = 100].Name", STORE)).toBe("p3");
    expect(await run("$filter([1,2,3], function($v){$v = 2})")).toBe(2);
    expect(await run("Account.Order.Product[Price > 1000].Name", STORE)).toBeUndefined();
    expect(await run("Account.Order.Product[Price = 100].Name[]", STORE)).toEqual(["p3"]);
  });

  test("descendant projections agree with explicit paths under aggregation", async () => {
    /** Verifies: JN-CVI-001, JN-PATH-009, JN-PATH-002, JN-LIB-011 */
    expect(await run("(**.Price) = (Account.Order.Product.Price)", STORE)).toBe(true);
    expect(await run("$sum(**.Price)", STORE)).toBe(115);
    expect(await run("$sum(Account.Order.Product.Price)", STORE)).toBe(115);
  });

  test("every subsystem reports failures as code, position, and token triples", async () => {
    /** Verifies: JN-CVI-002, JN-CMP-002, JN-CMP-004, JN-ERR-001 */
    const collected: any[] = [];
    try {
      jsonata("(1 + 2");
    } catch (err) {
      collected.push(err);
    }
    collected.push(await runErr("'a' + 1"));
    collected.push(await runErr("$number('abc')"));
    collected.push(await runErr("$toMillis('not a date')"));
    expect(collected.map((e) => e.code)).toEqual(["S0203", "T2001", "D3030", "D3110"]);
    for (const err of collected) {
      expect(typeof err.code).toBe("string");
      expect(typeof err.position).toBe("number");
      expect(err).toHaveProperty("token");
      expect(err instanceof Error).toBe(false);
    }
  });

  test("one effective-boolean rule governs conditionals, and, ?:, and $boolean", async () => {
    /** Verifies: JN-CVI-003, JN-OP-007, JN-OP-009, JN-LIB-016 */
    const expected: Record<string, { cond: string; and: boolean; bool: boolean; elvis: unknown }> = {
      "0": { cond: "F", and: false, bool: false, elvis: "F" },
      "1": { cond: "T", and: true, bool: true, elvis: 1 },
      "''": { cond: "F", and: false, bool: false, elvis: "F" },
      "'x'": { cond: "T", and: true, bool: true, elvis: "x" },
      "[]": { cond: "F", and: false, bool: false, elvis: "F" },
      "[0]": { cond: "F", and: false, bool: false, elvis: "F" },
      "{}": { cond: "F", and: false, bool: false, elvis: "F" },
    };
    for (const [source, want] of Object.entries(expected)) {
      const got = await run(`($v := ${source}; {'cond': $v ? 'T' : 'F', 'and': $v and true, 'bool': $boolean($v), 'elvis': $v ?: 'F'})`);
      expect(got, `value ${source}`).toEqual(want);
    }
  });

  test("names bound via :=, assign, and evaluate bindings are indistinguishable at lookup", async () => {
    /** Verifies: JN-CVI-004, JN-BND-001, JN-BND-002, JN-FUN-001 */
    expect(await run("($x := 7; $x * 2)")).toBe(14);
    const assigned = jsonata("$x * 2");
    assigned.assign("x", 7);
    expect(await assigned.evaluate({})).toBe(14);
    expect(await run("$x * 2", {}, { x: 7 })).toBe(14);
    const both = jsonata("$x * 2");
    both.assign("x", 1);
    expect(await both.evaluate({}, { x: 7 })).toBe(14);
  });

  test("structural equality agrees between = and $distinct while in stays primitive", async () => {
    /** Verifies: JN-CVI-005, JN-OP-003, JN-OP-004, JN-LIB-013 */
    expect(await run("[{'a':1}] = [{'a':1}]")).toBe(true);
    expect(await run("$count($distinct([[1,2],[1,2]]))")).toBe(1);
    expect(await run("$distinct([{'a':[1]},{'a':[1]},{'b':2}])")).toEqual([{ a: [1] }, { b: 2 }]);
    expect(await run("[1,2] in [[1,2],[3]]")).toBe(false);
  });

  test("chaining through ~> matches direct application for library functions", async () => {
    /** Verifies: JN-CVI-006, JN-OP-010 */
    expect(
      await run(
        "[('abc' ~> $substring(1)) = $substring('abc', 1), ('a,b' ~> $split(',')) = $split('a,b', ','), (2.345 ~> $round(2)) = $round(2.345, 2)]",
      ),
    ).toEqual([true, true, true]);
    expect(await run("('hello' ~> $uppercase) = $uppercase('hello')")).toBe(true);
  });

  test("ast structure describes exactly what evaluation executes", async () => {
    /** Verifies: JN-CVI-007, JN-CMP-006 */
    const expr = jsonata("Account.Name");
    const ast = expr.ast() as any;
    expect(ast.type).toBe("path");
    expect(ast.steps.map((s: any) => s.value)).toEqual(["Account", "Name"]);
    expect(await expr.evaluate(STORE)).toBe("acme");
    const sum = jsonata("1 + 2");
    const sumAst = sum.ast() as any;
    expect(sumAst.value).toBe("+");
    expect(sumAst.lhs.value + sumAst.rhs.value).toBe(await sum.evaluate({}));
  });
});

describe("end to end", () => {
  test("an invoice document is aggregated, grouped, ranked, and rendered in one pass", async () => {
    /** Verifies: JN-CON-003, JN-CON-004, JN-LIB-010, JN-LIB-011, JN-PATH-005, JN-PATH-008 */
    const invoice = {
      invoice: {
        lines: [
          { desc: "widget", price: 10, qty: 3 },
          { desc: "gadget", price: 100, qty: 1 },
          { desc: "widget", price: 10, qty: 1 },
        ],
      },
    };
    const report = await run(
      "({'total': $formatNumber($sum(invoice.lines.(price*qty)), '#,##0.00'), 'byDesc': invoice.lines{desc: $sum(qty)}, 'top': (invoice.lines^(>price))[0].desc})",
      invoice,
    );
    expect(report).toEqual({ total: "140.00", byDesc: { widget: 4, gadget: 1 }, top: "gadget" });
  });

  test("a full enrichment pipeline transforms, regroups, formats, and stamps a document", async () => {
    /** Verifies: JN-CON-005, JN-CON-003, JN-DT-003, JN-DT-002, JN-BND-001, JN-OP-010 */
    const doc = { shipment: { parcels: [{ dest: "east", kg: 2 }, { dest: "west", kg: 5 }, { dest: "east", kg: 1 }] } };
    const expr = jsonata(
      "($priced := $ ~> |shipment.parcels|{'cost': kg * $rate}|; {'byDest': $priced.shipment.parcels{dest: $sum(cost)}, 'heaviest': (shipment.parcels^(>kg))[0].dest, 'stampOk': $toMillis($now()) = $millis()})",
    );
    const result = norm(await expr.evaluate(doc, { rate: 3 })) as any;
    expect(result.byDest).toEqual({ east: 9, west: 15 });
    expect(result.heaviest).toBe("west");
    expect(result.stampOk).toBe(true);
    expect(doc.shipment.parcels[0]).toEqual({ dest: "east", kg: 2 });
  });
});
