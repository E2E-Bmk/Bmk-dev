// Oracle - atomic tests for the jsonata query-and-transformation engine specification.
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

function compileErr(source: string): any {
  try {
    jsonata(source);
  } catch (err) {
    return err;
  }
  throw new Error(`expected compilation of ${source} to throw`);
}

describe("expression compilation and errors", () => {
  test("jsonata compiles a reusable expression object without evaluating it", async () => {
    /** Verifies: JN-CMP-001, JN-CMP-005 */
    const expr = jsonata("a + 1");
    expect(typeof expr.evaluate).toBe("function");
    expect(typeof expr.assign).toBe("function");
    expect(typeof expr.registerFunction).toBe("function");
    expect(typeof expr.ast).toBe("function");
    expect(await expr.evaluate({ a: 1 })).toBe(2);
    expect(await expr.evaluate({ a: 10 })).toBe(11);
  });

  test("an unclosed group throws S0203 with position and (end) token", () => {
    /** Verifies: JN-CMP-002 */
    const err = compileErr("(1 + 2");
    expect(err.code).toBe("S0203");
    expect(err.position).toBe(6);
    expect(err.token).toBe("(end)");
    expect(err instanceof Error).toBe(false);
  });

  test("dangling dots and stray operator characters are syntax errors", () => {
    /** Verifies: JN-CMP-002 */
    const dot = compileErr("Account.");
    expect(dot.code).toBe("S0207");
    expect(dot.position).toBe(8);
    expect(dot.token).toBe("(end)");
    const stray = compileErr("1 === 2");
    expect(stray.code).toBe("S0211");
    expect(stray.position).toBe(4);
    expect(stray.token).toBe("=");
  });

  test("no ** power operator and no infix ^ outside sort", () => {
    /** Verifies: JN-CMP-002 */
    const star = compileErr("2 ** 4");
    expect(star.code).toBe("S0201");
    expect(star.token).toBe("**");
    const caret = compileErr("2^4");
    expect(caret.code).toBe("S0202");
    expect(caret.position).toBe(3);
  });

  test("evaluate returns a promise and empty selections resolve undefined", async () => {
    /** Verifies: JN-CMP-003 */
    const pending = jsonata("Account.Missing").evaluate(STORE);
    expect(typeof (pending as Promise<unknown>).then).toBe("function");
    expect(await pending).toBeUndefined();
    expect(await run("Account.Missing", STORE)).not.toBeNull();
  });

  test("runtime failures reject with code, position, and token but no Error prototype", async () => {
    /** Verifies: JN-CMP-004 */
    const err = await runErr("'a' + 1");
    expect(err.code).toBe("T2001");
    expect(err.position).toBe(5);
    expect(err.token).toBe("+");
    expect(err instanceof Error).toBe(false);
  });

  test("ast exposes path steps and binary operator structure", () => {
    /** Verifies: JN-CMP-006 */
    const path = jsonata("Account.Name").ast() as any;
    expect(path.type).toBe("path");
    expect(path.steps.map((s: any) => ({ type: s.type, value: s.value, position: s.position }))).toEqual([
      { type: "name", value: "Account", position: 7 },
      { type: "name", value: "Name", position: 12 },
    ]);
    const sum = jsonata("1 + 2").ast() as any;
    expect(sum.type).toBe("binary");
    expect(sum.value).toBe("+");
    expect({ type: sum.lhs.type, value: sum.lhs.value }).toEqual({ type: "number", value: 1 });
    expect({ type: sum.rhs.type, value: sum.rhs.value }).toEqual({ type: "number", value: 2 });
  });
});

describe("path navigation and sequences", () => {
  test("name steps select fields and singleton sequences collapse to the bare value", async () => {
    /** Verifies: JN-PATH-001, JN-PATH-004 */
    expect(await run("Account.Name", STORE)).toBe("acme");
    expect(await run("Account.Order[1].Product.Price", STORE)).toBe(100);
  });

  test("selecting a missing field resolves undefined, not null", async () => {
    /** Verifies: JN-PATH-001, JN-ERR-002 */
    expect(await run("Account.Missing", STORE)).toBeUndefined();
    expect(typeof (await run("Account.Missing", STORE))).toBe("undefined");
  });

  test("steps over arrays map and flatten one level", async () => {
    /** Verifies: JN-PATH-002 */
    expect(await run("Account.Order.OrderID", STORE)).toEqual(["o1", "o2"]);
    expect(await run("Account.Order.Product.Name", STORE)).toEqual(["p1", "p2", "p3"]);
    expect(await run("Account.Order.Product.Price", STORE)).toEqual([10, 5, 100]);
  });

  test("the [] suffix keeps array form for single-item results", async () => {
    /** Verifies: JN-PATH-003 */
    expect(await run("Account.Order[1].Product.Name[]", STORE)).toEqual(["p3"]);
    expect(await run("Account.Order.Product[Price=100].[Name]", STORE)).toEqual(["p3"]);
  });

  test("numeric predicates select by position, zero-based and negative from the end", async () => {
    /** Verifies: JN-PATH-008 */
    expect(await run("Account.Order[0].OrderID", STORE)).toBe("o1");
    expect(await run("Account.Order[-1].OrderID", STORE)).toBe("o2");
    expect(await run("$[0]", 7)).toBe(7);
  });

  test("boolean predicates filter with sequence-rule results", async () => {
    /** Verifies: JN-PATH-008, JN-PATH-001 */
    expect(await run("Account.Order.Product[Price > 8].Name", STORE)).toEqual(["p1", "p3"]);
    expect(await run("Account.Order.Product[Price = 100].Name", STORE)).toBe("p3");
    expect(await run("Account.Order.Product[Price > 1000].Name", STORE)).toBeUndefined();
  });

  test("wildcard * selects all field values of the context object", async () => {
    /** Verifies: JN-PATH-009 */
    expect(await run("Account.Order[0].Product[0].*", STORE)).toEqual(["p1", 10, 2]);
  });

  test("descendant ** selects values at any depth", async () => {
    /** Verifies: JN-PATH-009 */
    expect(await run("**.Name", STORE)).toEqual(["acme", "p1", "p2", "p3"]);
    expect(await run("**.Price", STORE)).toEqual([10, 5, 100]);
  });

  test("$ is the current context and $$ is always the root input", async () => {
    /** Verifies: JN-PATH-004 */
    expect(await run("$.Account.Name", STORE)).toBe("acme");
    expect(await run("$", { x: 1 })).toEqual({ x: 1 });
    expect(await run("$$.x", { x: 1 })).toBe(1);
    expect(await run("Account.Order.Product[Price > $$.Account.Order[0].Product[1].Price].Name", STORE)).toEqual(["p1", "p3"]);
    expect(await run("Account.Order.Product.Name.$", STORE)).toEqual(["p1", "p2", "p3"]);
  });

  test("parenthesized step expressions map over the context sequence", async () => {
    /** Verifies: JN-PATH-005 */
    expect(await run("[1,2,3].($ * 2)")).toEqual([2, 4, 6]);
    expect(await run("$.($*2)", [1, 2])).toEqual([2, 4]);
    expect(await run("Account.Order.Product.(Price * Qty)", STORE)).toEqual([20, 5, 100]);
  });

  test("the parent operator % reaches the enclosing object", async () => {
    /** Verifies: JN-PATH-006 */
    const data = { Account: { Name: "acme", Order: [{ OrderID: "o1", Product: [{ Name: "p1" }] }] } };
    expect(await run("Account.Order.Product.{'p': Name, 'order': %.OrderID}", data)).toEqual({ p: "p1", order: "o1" });
  });

  test("#$var binds zero-based position and @$var binds the context item", async () => {
    /** Verifies: JN-PATH-007 */
    const cities = { cities: [{ name: "a", pop: 3 }, { name: "b", pop: 1 }] };
    expect(await run("cities#$i.{'i': $i, 'n': name}", cities)).toEqual([
      { i: 0, n: "a" },
      { i: 1, n: "b" },
    ]);
    const lib = { library: { books: [{ title: "t1" }, { title: "t2" }] } };
    expect(await run("(library.books)@$b.{'t': $b.title}", lib)).toEqual([{ t: "t1" }, { t: "t2" }]);
  });
});

describe("operators", () => {
  test("arithmetic follows conventional precedence with % and unary minus", async () => {
    /** Verifies: JN-OP-001 */
    expect(await run("(5 + 3 * 2 - 1) / 2")).toBe(5);
    expect(await run("10 % 3")).toBe(1);
    expect(await run("-(3+2)")).toBe(-5);
  });

  test("arithmetic on a defined non-number rejects T2001, on undefined resolves undefined", async () => {
    /** Verifies: JN-OP-001, JN-ERR-002 */
    const err = await runErr("'a' + 1");
    expect(err.code).toBe("T2001");
    expect(await run("Account.Missing + 1", STORE)).toBeUndefined();
  });

  test("order comparisons work on two numbers or two strings and reject mixed types", async () => {
    /** Verifies: JN-OP-002 */
    expect(await run("1 < 2")).toBe(true);
    expect(await run("'a' < 'b'")).toBe(true);
    expect(await run("2 >= 2")).toBe(true);
    const err = await runErr("'a' < 1");
    expect(err.code).toBe("T2009");
    expect(err.position).toBe(5);
    expect(err.token).toBe("<");
  });

  test("= and != are deep structural equality and mixed types compare unequal", async () => {
    /** Verifies: JN-OP-003 */
    expect(await run("[1,2] = [1,2]")).toBe(true);
    expect(await run("{'a':1} = {'a':1}")).toBe(true);
    expect(await run("1 != 2")).toBe(true);
    expect(await run("'a' = 1")).toBe(false);
  });

  test("in tests array membership by primitive value only", async () => {
    /** Verifies: JN-OP-004 */
    expect(await run("2 in [1,2,3]")).toBe(true);
    expect(await run("'x' in 'xyz'")).toBe(false);
    expect(await run("[1,2] in [[1,2],[3]]")).toBe(false);
    expect(await run("null in [null]")).toBe(true);
  });

  test("range expressions expand inclusive integer sequences inside array constructors", async () => {
    /** Verifies: JN-OP-005 */
    expect(await run("[1..4]")).toEqual([1, 2, 3, 4]);
    expect(await run("[1..3, 7..8]")).toEqual([1, 2, 3, 7, 8]);
    expect(await run("[4..1]")).toEqual([]);
    expect(await run("[1..3].($*10)")).toEqual([10, 20, 30]);
  });

  test("& concatenates the string forms of both operands", async () => {
    /** Verifies: JN-OP-006 */
    expect(await run("'a' & 1 & true")).toBe("a1true");
    expect(await run("1 & 2")).toBe("12");
  });

  test("and/or apply effective-boolean coercion to their operands", async () => {
    /** Verifies: JN-OP-007 */
    expect(await run("true and false")).toBe(false);
    expect(await run("true or false")).toBe(true);
    expect(await run("1 and 'x'")).toBe(true);
    expect(await run("0 and 1")).toBe(false);
    expect(await run("'' or 'x'")).toBe(true);
  });

  test("conditionals return undefined when a false test has no else branch", async () => {
    /** Verifies: JN-OP-008 */
    expect(await run("1 < 2 ? 'yes' : 'no'")).toBe("yes");
    expect(await run("false ? 'a'")).toBeUndefined();
  });

  test("?: defaults on falsy values while ?? defaults only on undefined", async () => {
    /** Verifies: JN-OP-009 */
    expect(await run("Missing ?: 'dflt'")).toBe("dflt");
    expect(await run("5 ?: 'dflt'")).toBe(5);
    expect(await run("Missing ?? 'dflt'")).toBe("dflt");
    expect(await run("0 ?? 'dflt'")).toBe(0);
    expect(await run("false ?? 'dflt'")).toBe(false);
    expect(await run("0 ?: 'dflt'")).toBe("dflt");
  });

  test("~> chains pass the left value as first argument, composing left to right", async () => {
    /** Verifies: JN-OP-010 */
    expect(await run("'hello' ~> $uppercase ~> $length")).toBe(5);
    expect(await run("'hello world' ~> $substringBefore(' ') ~> $uppercase")).toBe("HELLO");
  });
});

describe("constructors and reshaping", () => {
  test("array constructors preserve nesting and object keys may be computed", async () => {
    /** Verifies: JN-CON-001 */
    expect(await run("[1, 'two', [3]]")).toEqual([1, "two", [3]]);
    expect(await run("{'a': 1, 'b': [2,3]}")).toEqual({ a: 1, b: [2, 3] });
    expect(await run("{'k' & 1: 'v'}")).toEqual({ k1: "v" });
  });

  test("a duplicate key inside one object constructor rejects D1009", async () => {
    /** Verifies: JN-CON-002 */
    const err = await runErr("{'a': 1, 'a': 2}");
    expect(err.code).toBe("D1009");
    expect(err.position).toBe(1);
  });

  test("grouping aggregates values sharing a key with singletons kept bare", async () => {
    /** Verifies: JN-CON-003 */
    const data = { Account: { Order: [{ Product: [{ Name: "a", Price: 1 }, { Name: "b", Price: 2 }] }, { Product: [{ Name: "a", Price: 3 }] }] } };
    expect(await run("Account.Order.Product{Name: Price}", data)).toEqual({ a: [1, 3], b: 2 });
    expect(await run("[{'k':'a','v':1},{'k':'a','v':2}]{k: v}")).toEqual({ a: [1, 2] });
    expect(await run("[{'k':'a'},{'k':'a'}]{'x': k}")).toEqual({ x: ["a", "a"] });
  });

  test("two grouping pairs producing the same key reject D1009", async () => {
    /** Verifies: JN-CON-002 */
    const err = await runErr("[{'t':'x','v':1}]{ t: v, 'x': 99 }");
    expect(err.code).toBe("D1009");
    expect(err.position).toBe(18);
  });

  test("^ sorts ascending by default with > descending and later terms breaking ties", async () => {
    /** Verifies: JN-CON-004 */
    const orders = { Order: [{ p: 3, n: "c" }, { p: 1, n: "a" }, { p: 2, n: "b" }] };
    expect(await run("Order^(p).n", orders)).toEqual(["a", "b", "c"]);
    expect(await run("Order^(>p).n", orders)).toEqual(["c", "b", "a"]);
    expect(await run("Order^(>p, n).n", orders)).toEqual(["c", "b", "a"]);
  });

  test("sorting mixed-type term values rejects T2007", async () => {
    /** Verifies: JN-CON-004 */
    const err = await runErr("[1,'a']^($)");
    expect(err.code).toBe("T2007");
    expect(err.position).toBe(8);
  });

  test("the transform operator merges updates into matched objects on a deep copy", async () => {
    /** Verifies: JN-CON-005 */
    const data = { Account: { Order: [{ Product: [{ Price: 10 }, { Price: 5 }] }] } };
    expect(await run("$ ~> |Account.Order.Product|{'Price': Price * 2}|", data)).toEqual({
      Account: { Order: [{ Product: [{ Price: 20 }, { Price: 10 }] }] },
    });
    expect(data.Account.Order[0].Product[0].Price).toBe(10);
  });

  test("transform deletions strip listed names from matched objects", async () => {
    /** Verifies: JN-CON-005 */
    const data = { Account: { Order: [{ Product: [{ Price: 10 }, { Price: 5 }] }] } };
    expect(await run("$ ~> |Account.Order.Product|{}, ['Price']|", data)).toEqual({
      Account: { Order: [{ Product: [{}, {}] }] },
    });
    expect(data.Account.Order[0].Product.length).toBe(2);
  });
});

describe("variables, blocks, and functions", () => {
  test(":= binds a value and a block returns its last statement", async () => {
    /** Verifies: JN-FUN-001 */
    expect(await run("($x := 5; $y := 3; $x * $y)")).toBe(15);
  });

  test("blocks form child scopes so inner rebinding stays local", async () => {
    /** Verifies: JN-FUN-002 */
    expect(await run("($x := 2; ($x := 3; $x) + $x)")).toBe(5);
  });

  test("unbound variables read as undefined but calling a non-function rejects T1006", async () => {
    /** Verifies: JN-FUN-003 */
    expect(await run("$nope")).toBeUndefined();
    const literal = await runErr("5(3)");
    expect(literal.code).toBe("T1006");
    expect(literal.position).toBe(2);
    expect(literal.token).toBe(5);
    const unknown = await runErr("$nofunc(3)");
    expect(unknown.code).toBe("T1006");
    expect(unknown.token).toBe("nofunc");
  });

  test("lambdas apply, recurse through their binding, and close over scope", async () => {
    /** Verifies: JN-FUN-004 */
    expect(await run("(function($x){$x*2})(21)")).toBe(42);
    expect(await run("($fact := function($n){$n <= 1 ? 1 : $n * $fact($n-1)}; $fact(5))")).toBe(120);
    expect(await run("($add := function($a){function($b){$a+$b}}; $add(2)(3))")).toBe(5);
  });

  test("higher-order library functions pass value and index to lambdas", async () => {
    /** Verifies: JN-FUN-004, JN-LIB-014 */
    expect(await run("$map([1,2,3], function($v, $i){$v + $i})")).toEqual([1, 3, 5]);
  });

  test("lambda signatures validate argument types and reject T0410 at the function name", async () => {
    /** Verifies: JN-FUN-005 */
    expect(await run("($f := function($s)<s:n>{$length($s)}; $f('abc'))")).toBe(3);
    const err = await runErr("($f := function($s)<s:n>{$length($s)}; $f(5))");
    expect(err.code).toBe("T0410");
    expect(err.position).toBe(42);
    expect(err.token).toBe("f");
  });

  test("built-in functions enforce their signatures the same way", async () => {
    /** Verifies: JN-FUN-005 */
    const err = await runErr("$length('a','b','c')");
    expect(err.code).toBe("T0410");
    expect(err.position).toBe(8);
    expect(err.token).toBe("length");
  });
});

describe("string functions", () => {
  test("$string renders JSON text for structures and 15-digit decimals for numbers", async () => {
    /** Verifies: JN-LIB-001 */
    expect(await run("$string(5)")).toBe("5");
    expect(await run("$string(1/3)")).toBe("0.333333333333333");
    expect(await run("$string(true)")).toBe("true");
    expect(await run("$string({'a':[1]})")).toBe('{"a":[1]}');
    expect(await run("$string(nothing)")).toBeUndefined();
  });

  test("$length counts characters and $substring supports negative starts", async () => {
    /** Verifies: JN-LIB-002 */
    expect(await run("$length('héllo')")).toBe(5);
    expect(await run("$length('')")).toBe(0);
    expect(await run("$substring('hello world', 0, 5)")).toBe("hello");
    expect(await run("$substring('hello', -3)")).toBe("llo");
    expect(await run("$substring('hello', 1)")).toBe("ello");
  });

  test("$substringBefore/After split at the first separator occurrence", async () => {
    /** Verifies: JN-LIB-002 */
    expect(await run("$substringBefore('a-b-c', '-')")).toBe("a");
    expect(await run("$substringAfter('a-b-c', '-')")).toBe("b-c");
    expect(await run("$substringBefore('abc', 'x')")).toBe("abc");
  });

  test("case mapping, whitespace trimming, and two-sided padding", async () => {
    /** Verifies: JN-LIB-003 */
    expect(await run("$uppercase('aBc')")).toBe("ABC");
    expect(await run("$lowercase('aBc')")).toBe("abc");
    expect(await run("$trim('  a  b  ')")).toBe("a b");
    expect(await run("$pad('7', 3, '0')")).toBe("700");
    expect(await run("$pad('7', -3, '0')")).toBe("007");
  });

  test("$contains, $split, and $join accept strings or regexes", async () => {
    /** Verifies: JN-LIB-004 */
    expect(await run("$contains('hello', 'ell')")).toBe(true);
    expect(await run("$contains('hello', /l+/)")).toBe(true);
    expect(await run("$split('a,b,c', ',')")).toEqual(["a", "b", "c"]);
    expect(await run("$split('a1b2c', /\\d/)")).toEqual(["a", "b", "c"]);
    expect(await run("$split('a,b,c', ',', 2)")).toEqual(["a", "b"]);
    expect(await run("$join(['a','b'], '-')")).toBe("a-b");
    expect(await run("$join('solo')")).toBe("solo");
  });

  test("$match returns match records with index and captured groups", async () => {
    /** Verifies: JN-LIB-005 */
    expect(await run("$match('ab1cd2', /\\d/)")).toEqual([
      { match: "1", index: 2, groups: [] },
      { match: "2", index: 5, groups: [] },
    ]);
    expect(await run("$match('2usd', /(\\d+)([a-z]+)/)")).toEqual({ match: "2usd", index: 0, groups: ["2", "usd"] });
  });

  test("$replace supports group references, replacement functions, and limits", async () => {
    /** Verifies: JN-LIB-005 */
    expect(await run("$replace('a1b2', /\\d/, 'X')")).toBe("aXbX");
    expect(await run("$replace('a1b2', /(\\d)/, '<$1>')")).toBe("a<1>b<2>");
    expect(await run("$replace('aaa', 'a', 'b', 2)")).toBe("bba");
    expect(await run("$replace('a1b2', /\\d/, function($m){'[' & $m.match & ']'})")).toBe("a[1]b[2]");
  });

  test("base64 and URL-component codecs round-trip text", async () => {
    /** Verifies: JN-LIB-006 */
    expect(await run("$base64encode('hi')")).toBe("aGk=");
    expect(await run("$base64decode('aGk=')")).toBe("hi");
    expect(await run("$encodeUrlComponent('a b&c')")).toBe("a%20b%26c");
    expect(await run("$decodeUrlComponent('a%20b')")).toBe("a b");
  });

  test("$eval evaluates a JSONata source string against an optional context", async () => {
    /** Verifies: JN-LIB-006 */
    expect(await run("$eval('[1,2,3].($ * 2)')")).toEqual([2, 4, 6]);
    expect(await run("$eval('a + 1', {'a': 4})")).toBe(5);
  });
});

describe("numeric and aggregation functions", () => {
  test("$number converts numeric strings, hex, and booleans and rejects D3030 otherwise", async () => {
    /** Verifies: JN-LIB-007 */
    expect(await run("$number('12.5')")).toBe(12.5);
    expect(await run("$number('0x1F')")).toBe(31);
    expect(await run("$number(true)")).toBe(1);
    const err = await runErr("$number('abc')");
    expect(err.code).toBe("D3030");
    expect(err.position).toBe(8);
    expect(err.token).toBe("number");
  });

  test("$abs, $floor, $ceil, and half-to-even $round with precision", async () => {
    /** Verifies: JN-LIB-008 */
    expect(await run("$abs(-3.2)")).toBe(3.2);
    expect(await run("$floor(3.7)")).toBe(3);
    expect(await run("$ceil(3.2)")).toBe(4);
    expect(await run("$round(2.5)")).toBe(2);
    expect(await run("$round(3.5)")).toBe(4);
    expect(await run("$round(-2.5)")).toBe(-2);
    expect(await run("$round(2.345, 2)")).toBe(2.34);
  });

  test("$power and $sqrt compute, $sqrt of a negative rejects D3060, $random stays in [0,1)", async () => {
    /** Verifies: JN-LIB-009 */
    expect(await run("$power(2,10)")).toBe(1024);
    expect(await run("$sqrt(16)")).toBe(4);
    const err = await runErr("$sqrt(-1)");
    expect(err.code).toBe("D3060");
    expect(err.token).toBe("sqrt");
    expect(await run("($r := $random(); $r >= 0 and $r < 1)")).toBe(true);
  });

  test("number formatting pictures, radix formatting, and word-form integers", async () => {
    /** Verifies: JN-LIB-010 */
    expect(await run("$formatNumber(12345.6, '#,##0.00')")).toBe("12,345.60");
    expect(await run("$formatNumber(0.14, '0.0%')")).toBe("14.0%");
    expect(await run("$formatBase(255, 16)")).toBe("ff");
    expect(await run("$formatBase(5)")).toBe("5");
    expect(await run("$formatInteger(2789, 'w')")).toBe("two thousand, seven hundred and eighty-nine");
    expect(await run("$parseInteger('twelve', 'w')")).toBe(12);
  });

  test("aggregators reduce numeric arrays and treat a bare number as its own aggregate", async () => {
    /** Verifies: JN-LIB-011 */
    expect(await run("$sum([1,2,3])")).toBe(6);
    expect(await run("$max([4,1,9])")).toBe(9);
    expect(await run("$min([4,1,9])")).toBe(1);
    expect(await run("$average([1,2,3,4])")).toBe(2.5);
    expect(await run("$sum(5)")).toBe(5);
    expect(await run("$sum([])")).toBe(0);
    const err = await runErr("$sum(['a'])");
    expect(err.code).toBe("T0412");
    expect(err.token).toBe("sum");
  });

  test("$count reports array length, 1 for a bare value, and 0 for no value", async () => {
    /** Verifies: JN-LIB-012 */
    expect(await run("$count([1,2,3])")).toBe(3);
    expect(await run("$count('x')")).toBe(1);
    expect(await run("$count(nothing)")).toBe(0);
  });
});

describe("array and object functions", () => {
  test("$append concatenates, treating non-arrays as singletons", async () => {
    /** Verifies: JN-LIB-013 */
    expect(await run("$append([1,2], [3])")).toEqual([1, 2, 3]);
    expect(await run("$append(1, 2)")).toEqual([1, 2]);
  });

  test("$sort defaults ascending with an optional out-of-order comparator", async () => {
    /** Verifies: JN-LIB-013 */
    expect(await run("$sort([3,1,2])")).toEqual([1, 2, 3]);
    expect(await run("$sort(['b','a'], function($l,$r){$l > $r})")).toEqual(["a", "b"]);
  });

  test("$reverse, $distinct with deep equality, and $zip stopping at the shortest input", async () => {
    /** Verifies: JN-LIB-013 */
    expect(await run("$reverse([1,2,3])")).toEqual([3, 2, 1]);
    expect(await run("$distinct([1,2,1,3,2])")).toEqual([1, 2, 3]);
    expect(await run("$zip([1,2],[3,4],[5,6])")).toEqual([[1, 3, 5], [2, 4, 6]]);
    expect(await run("$zip([1,2],[3])")).toEqual([[1, 3]]);
  });

  test("$filter, $reduce with optional init, and $single's unique-match contract", async () => {
    /** Verifies: JN-LIB-014 */
    expect(await run("$filter([1,2,3,4], function($v){$v > 2})")).toEqual([3, 4]);
    expect(await run("$reduce([1,2,3,4], function($a,$b){$a*$b})")).toBe(24);
    expect(await run("$reduce([1,2], function($a,$b){$a+$b}, 10)")).toBe(13);
    expect(await run("$single([1,2,3], function($v){$v = 2})")).toBe(2);
    const err = await runErr("$single([1,3], function($v){$v = 2})");
    expect(err.code).toBe("D3139");
    expect(err.token).toBe("single");
  });

  test("$each maps entries to values and $sift filters entries by predicate", async () => {
    /** Verifies: JN-LIB-014 */
    expect(await run("$each({'a':1,'b':2}, function($v,$k){$k & '=' & $v})")).toEqual(["a=1", "b=2"]);
    expect(await run("$sift({'a':1,'ab':2}, function($v,$k){$length($k)>1})")).toEqual({ ab: 2 });
  });

  test("$keys unions over arrays, $lookup gathers across arrays, $merge lets later keys win", async () => {
    /** Verifies: JN-LIB-015 */
    expect(await run("$keys({'a':1,'b':2})")).toEqual(["a", "b"]);
    expect(await run("$keys([{'a':1},{'b':2}])")).toEqual(["a", "b"]);
    expect(await run("$lookup({'a':1}, 'a')")).toBe(1);
    expect(await run("$lookup([{'a':1},{'a':2}], 'a')")).toEqual([1, 2]);
    expect(await run("$merge([{'a':1},{'b':2},{'a':3}])")).toEqual({ a: 3, b: 2 });
    expect(await run("$spread({'a':1,'b':2})")).toEqual([{ a: 1 }, { b: 2 }]);
  });

  test("$type names the seven value kinds", async () => {
    /** Verifies: JN-LIB-016 */
    expect(await run("$type(1)")).toBe("number");
    expect(await run("$type('x')")).toBe("string");
    expect(await run("$type(null)")).toBe("null");
    expect(await run("$type([1])")).toBe("array");
    expect(await run("$type({})")).toBe("object");
    expect(await run("$type($sum)")).toBe("function");
  });

  test("$exists distinguishes null from absence and $boolean applies effective-boolean rules", async () => {
    /** Verifies: JN-LIB-016 */
    expect(await run("$exists(nothing)")).toBe(false);
    expect(await run("$exists(null)")).toBe(true);
    expect(await run("$boolean([])")).toBe(false);
    expect(await run("$boolean([0])")).toBe(false);
    expect(await run("$boolean('')")).toBe(false);
    expect(await run("$boolean({})")).toBe(false);
    expect(await run("$not(true)")).toBe(false);
  });

  test("null is a value: equal to itself, storable, and never equal to absence", async () => {
    /** Verifies: JN-LIB-016, JN-OP-003 */
    expect(await run("null")).toBeNull();
    expect(await run("null = null")).toBe(true);
    expect(await run("{'a': null}")).toEqual({ a: null });
    expect(await run("nothing = null")).toBe(false);
  });

  test("$error rejects D3137 and $assert rejects D3141 only on a false condition", async () => {
    /** Verifies: JN-LIB-017 */
    const custom = await runErr("$error('custom')");
    expect(custom.code).toBe("D3137");
    expect(custom.token).toBe("error");
    const failed = await runErr("$assert(false, 'oops')");
    expect(failed.code).toBe("D3141");
    expect(failed.token).toBe("assert");
    expect(await run("$assert(true, 'oops')")).toBeUndefined();
  });
});

describe("date and time", () => {
  test("$fromMillis renders ISO UTC by default and honors pictures with timezones", async () => {
    /** Verifies: JN-DT-001 */
    expect(await run("$fromMillis(1521801216617)")).toBe("2018-03-23T10:33:36.617Z");
    expect(await run("$fromMillis(1521801216617, '[Y0001]-[M01]-[D01]')")).toBe("2018-03-23");
    expect(await run("$fromMillis(1521801216617, '[H01]:[m01] [P]', '-0500')")).toBe("05:33 am");
  });

  test("$toMillis parses ISO or picture-described text and rejects D3110 otherwise", async () => {
    /** Verifies: JN-DT-002 */
    expect(await run("$toMillis('2018-03-23T10:33:36.617Z')")).toBe(1521801216617);
    expect(await run("$toMillis('23/03/2018', '[D01]/[M01]/[Y0001]')")).toBe(1521763200000);
    const err = await runErr("$toMillis('not a date')");
    expect(err.code).toBe("D3110");
    expect(err.token).toBe("toMillis");
  });

  test("$now and $millis observe the same instant within one evaluation", async () => {
    /** Verifies: JN-DT-003 */
    expect(await run("($n := $now(); $m := $millis(); $toMillis($n) = $m)")).toBe(true);
    expect(await run("$now('[Y0001]') = $fromMillis($millis(), '[Y0001]')")).toBe(true);
  });
});

describe("bindings and host integration", () => {
  test("the bindings argument of evaluate provides per-call variables", async () => {
    /** Verifies: JN-BND-001 */
    expect(await run("$a + $b", {}, { a: 4, b: 38 })).toBe(42);
  });

  test("assign persists bindings across evaluations of the same expression", async () => {
    /** Verifies: JN-BND-002 */
    const expr = jsonata("$greet & ', ' & name");
    expr.assign("greet", "hi");
    expect(await expr.evaluate({ name: "bob" })).toBe("hi, bob");
    expect(await expr.evaluate({ name: "sue" })).toBe("hi, sue");
  });

  test("evaluate-time bindings take precedence over assigned bindings", async () => {
    /** Verifies: JN-BND-002 */
    const expr = jsonata("$x");
    expr.assign("x", 1);
    expect(await expr.evaluate({}, { x: 2 })).toBe(2);
  });

  test("registerFunction binds host functions and enforces their signatures", async () => {
    /** Verifies: JN-BND-003 */
    const expr = jsonata("$twice(21)");
    expr.registerFunction("twice", (n: number) => n * 2, "<n:n>");
    expect(await expr.evaluate({})).toBe(42);
    const bad = jsonata("$twice('a')");
    bad.registerFunction("twice", (n: number) => n * 2, "<n:n>");
    let caught: any;
    try {
      await bad.evaluate({});
    } catch (err) {
      caught = err;
    }
    expect(caught.code).toBe("T0410");
    expect(caught.position).toBe(7);
    expect(caught.token).toBe("twice");
  });

  test("promise-returning host functions are awaited before use", async () => {
    /** Verifies: JN-BND-003 */
    const expr = jsonata("$fetchy() + 1");
    expr.registerFunction("fetchy", async () => 41);
    expect(await expr.evaluate({})).toBe(42);
  });

  test("host functions see the evaluation timestamp and input through this", async () => {
    /** Verifies: JN-BND-004 */
    const expr = jsonata("$probe()");
    expr.registerFunction("probe", function (this: any) {
      return { tsIsDate: this.environment.timestamp instanceof Date, inputX: this.input.x };
    });
    expect(await expr.evaluate({ x: 9 })).toEqual({ tsIsDate: true, inputX: 9 });
  });
});
