// Spec2Repo oracle - atomic tests for kysely-query-compiler-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  Kysely,
  DummyDriver,
  PostgresAdapter,
  PostgresIntrospector,
  PostgresQueryCompiler,
  MysqlAdapter,
  MysqlIntrospector,
  MysqlQueryCompiler,
  SqliteAdapter,
  SqliteIntrospector,
  SqliteQueryCompiler,
  CamelCasePlugin,
  NoResultError,
  sql,
} from "kysely";

type AnyDb = Kysely<any>;

function makeDb(kind: "pg" | "mysql" | "sqlite", plugins: any[] = []): AnyDb {
  const dialect =
    kind === "mysql"
      ? {
          createAdapter: () => new MysqlAdapter(),
          createDriver: () => new DummyDriver(),
          createIntrospector: (db: AnyDb) => new MysqlIntrospector(db),
          createQueryCompiler: () => new MysqlQueryCompiler(),
        }
      : kind === "sqlite"
        ? {
            createAdapter: () => new SqliteAdapter(),
            createDriver: () => new DummyDriver(),
            createIntrospector: (db: AnyDb) => new SqliteIntrospector(db),
            createQueryCompiler: () => new SqliteQueryCompiler(),
          }
        : {
            createAdapter: () => new PostgresAdapter(),
            createDriver: () => new DummyDriver(),
            createIntrospector: (db: AnyDb) => new PostgresIntrospector(db),
            createQueryCompiler: () => new PostgresQueryCompiler(),
          };
  return new Kysely<any>({ dialect, plugins });
}

const pg = makeDb("pg");
const my = makeDb("mysql");
const lite = makeDb("sqlite");
const cam = makeDb("pg", [new CamelCasePlugin()]);

describe("compilation contract", () => {
  test("a filtered selection compiles to sql text with ordered parameters", () => {
    /** Verifies: KYSL-INST-004, KYSL-SEL-005 */
    const c = pg.selectFrom("crew").select(["id", "call_sign"]).where("missions", ">", 4).compile();
    expect(c.sql).toBe('select "id", "call_sign" from "crew" where "missions" > $1');
    expect(c.parameters).toEqual([4]);
  });

  test("mysql and sqlite compilers render their own quoting and placeholder styles", () => {
    /** Verifies: KYSL-INST-006, KYSL-INST-007 */
    const cMy = my.selectFrom("crew").select(["id", "call_sign"]).where("missions", ">", 4).compile();
    expect(cMy.sql).toBe("select `id`, `call_sign` from `crew` where `missions` > ?");
    expect(cMy.parameters).toEqual([4]);
    const cLite = lite.selectFrom("crew").select(["id", "call_sign"]).where("missions", ">", 4).compile();
    expect(cLite.sql).toBe('select "id", "call_sign" from "crew" where "missions" > ?');
    expect(cLite.parameters).toEqual([4]);
  });

  test("repeated compilation returns equal sql and parameters", () => {
    /** Verifies: KYSL-INST-005 */
    const q = pg.selectFrom("voyage").selectAll().where("status", "=", "active");
    const a = q.compile();
    const b = q.compile();
    expect(a.sql).toBe('select * from "voyage" where "status" = $1');
    expect(a.sql).toBe(b.sql);
    expect(a.parameters).toEqual(["active"]);
    expect(a.parameters).toEqual(b.parameters);
  });

  test("constructing an instance without a dialect throws", () => {
    /** Verifies: KYSL-INST-003, KYSL-ERR-001 */
    expect(() => new (Kysely as any)({})).toThrow();
  });

  test("a query with no bound values compiles with an empty parameters array", () => {
    /** Verifies: KYSL-INST-004 */
    const c = pg.selectFrom("dock").selectAll().compile();
    expect(c.sql).toBe('select * from "dock"');
    expect(c.parameters).toEqual([]);
  });

  test("a table alias registers through the as form", () => {
    /** Verifies: KYSL-SEL-001, KYSL-SEL-003 */
    const c = pg.selectFrom("crew as c").selectAll("c").compile();
    expect(c.sql).toBe('select "c".* from "crew" as "c"');
  });

  test("selectNoFrom compiles a from-less selection", () => {
    /** Verifies: KYSL-SEL-004 */
    const c = pg.selectNoFrom(sql`7 * 6`.as("answer")).compile();
    expect(c.sql).toBe('select 7 * 6 as "answer"');
    expect(c.parameters).toEqual([]);
  });
});

describe("row selection", () => {
  test("select accepts a single column, a list, and aliases", () => {
    /** Verifies: KYSL-SEL-002 */
    expect(pg.selectFrom("crew").select("call_sign").compile().sql).toBe('select "call_sign" from "crew"');
    expect(pg.selectFrom("crew").select(["call_sign as cs", "missions"]).compile().sql).toBe(
      'select "call_sign" as "cs", "missions" from "crew"',
    );
  });

  test("qualified column names render each segment quoted", () => {
    /** Verifies: KYSL-SEL-002 */
    const c = pg.selectFrom("crew as c").select("c.call_sign").compile();
    expect(c.sql).toBe('select "c"."call_sign" from "crew" as "c"');
  });

  test("selectAll and distinct render star and distinct forms", () => {
    /** Verifies: KYSL-SEL-003 */
    expect(pg.selectFrom("crew").selectAll().compile().sql).toBe('select * from "crew"');
    expect(pg.selectFrom("crew").select("call_sign").distinct().compile().sql).toBe(
      'select distinct "call_sign" from "crew"',
    );
  });

  test("repeated where calls join with and in call order", () => {
    /** Verifies: KYSL-SEL-005 */
    const c = pg.selectFrom("crew").selectAll().where("rank", "=", "captain").where("missions", ">", 2).compile();
    expect(c.sql).toBe('select * from "crew" where "rank" = $1 and "missions" > $2');
    expect(c.parameters).toEqual(["captain", 2]);
  });

  test("whereRef compares two columns without binding", () => {
    /** Verifies: KYSL-SEL-006 */
    const c = pg.selectFrom("voyage").selectAll().whereRef("voyage.origin", "=", "voyage.destination").compile();
    expect(c.sql).toBe('select * from "voyage" where "voyage"."origin" = "voyage"."destination"');
    expect(c.parameters).toEqual([]);
  });

  test("is and is not render null literally without parameters", () => {
    /** Verifies: KYSL-SEL-007 */
    const a = pg.selectFrom("cargo").selectAll().where("berth_id", "is", null).compile();
    expect(a.sql).toBe('select * from "cargo" where "berth_id" is null');
    expect(a.parameters).toEqual([]);
    const b = pg.selectFrom("cargo").selectAll().where("berth_id", "is not", null).compile();
    expect(b.sql).toBe('select * from "cargo" where "berth_id" is not null');
    expect(b.parameters).toEqual([]);
  });

  test("equality with null binds null as a parameter", () => {
    /** Verifies: KYSL-SEL-007 */
    const c = pg.selectFrom("cargo").selectAll().where("berth_id", "=", null).compile();
    expect(c.sql).toBe('select * from "cargo" where "berth_id" = $1');
    expect(c.parameters).toEqual([null]);
  });

  test("clearWhere discards accumulated filters", () => {
    /** Verifies: KYSL-SEL-008 */
    const c = pg.selectFrom("dock").selectAll().where("lane", "=", 2).clearWhere().compile();
    expect(c.sql).toBe('select * from "dock"');
    expect(c.parameters).toEqual([]);
  });

  test("a subquery is accepted as a filter right-hand side", () => {
    /** Verifies: KYSL-SEL-014 */
    const c = pg
      .selectFrom("cargo")
      .selectAll()
      .where("voyage_id", "in", pg.selectFrom("voyage").select("id").where("status", "=", "lost"))
      .compile();
    expect(c.sql).toBe('select * from "cargo" where "voyage_id" in (select "id" from "voyage" where "status" = $1)');
    expect(c.parameters).toEqual(["lost"]);
  });

  test("innerJoin renders an on clause from column references", () => {
    /** Verifies: KYSL-SEL-009 */
    const c = pg
      .selectFrom("voyage")
      .innerJoin("cargo", "cargo.voyage_id", "voyage.id")
      .select(["voyage.id", "cargo.label as cargo_label"])
      .compile();
    expect(c.sql).toBe(
      'select "voyage"."id", "cargo"."label" as "cargo_label" from "voyage" inner join "cargo" on "cargo"."voyage_id" = "voyage"."id"',
    );
  });

  test("leftJoin callback combines onRef and parameterized on conditions", () => {
    /** Verifies: KYSL-SEL-009 */
    const c = pg
      .selectFrom("voyage")
      .leftJoin("cargo", (join) => join.onRef("cargo.voyage_id", "=", "voyage.id").on("cargo.mass", ">", 900))
      .select(["voyage.id"])
      .compile();
    expect(c.sql).toBe(
      'select "voyage"."id" from "voyage" left join "cargo" on "cargo"."voyage_id" = "voyage"."id" and "cargo"."mass" > $1',
    );
    expect(c.parameters).toEqual([900]);
  });

  test("a derived table joins as an aliased subquery", () => {
    /** Verifies: KYSL-SEL-010 */
    const c = pg
      .selectFrom("voyage")
      .innerJoin(
        (eb: any) => eb.selectFrom("cargo").select("voyage_id").as("cc"),
        (join: any) => join.onRef("cc.voyage_id", "=", "voyage.id"),
      )
      .selectAll()
      .compile();
    expect(c.sql).toBe(
      'select * from "voyage" inner join (select "voyage_id" from "cargo") as "cc" on "cc"."voyage_id" = "voyage"."id"',
    );
  });

  test("groupBy and having accept aggregate and simple forms", () => {
    /** Verifies: KYSL-SEL-011 */
    const agg = pg
      .selectFrom("crew")
      .select("rank")
      .groupBy("rank")
      .having((eb) => eb.fn.count("id"), ">", 3)
      .compile();
    expect(agg.sql).toBe('select "rank" from "crew" group by "rank" having count("id") > $1');
    expect(agg.parameters).toEqual([3]);
    const simple = pg.selectFrom("crew").select("rank").groupBy("rank").having("rank", ">", "b").compile();
    expect(simple.sql).toBe('select "rank" from "crew" group by "rank" having "rank" > $1');
  });

  test("orderBy accumulates terms with optional directions", () => {
    /** Verifies: KYSL-SEL-012 */
    const c = pg
      .selectFrom("crew")
      .selectAll()
      .orderBy("rank")
      .orderBy((eb) => eb.fn("length", ["call_sign"]), "desc")
      .compile();
    expect(c.sql).toBe('select * from "crew" order by "rank", length("call_sign") desc');
    expect(pg.selectFrom("crew").selectAll().orderBy("rank", "asc").compile().sql).toBe(
      'select * from "crew" order by "rank" asc',
    );
  });

  test("limit and offset bind counts as parameters in every dialect", () => {
    /** Verifies: KYSL-SEL-013 */
    const cPg = pg.selectFrom("crew").selectAll().limit(7).offset(14).compile();
    expect(cPg.sql).toBe('select * from "crew" limit $1 offset $2');
    expect(cPg.parameters).toEqual([7, 14]);
    const cMy = my.selectFrom("crew").selectAll().limit(7).offset(14).compile();
    expect(cMy.sql).toBe("select * from `crew` limit ? offset ?");
    expect(cMy.parameters).toEqual([7, 14]);
  });
});

describe("expressions and functions", () => {
  test("the expression builder renders a comparison with a bound value", () => {
    /** Verifies: KYSL-EXPR-001 */
    const c = pg
      .selectFrom("cargo")
      .selectAll()
      .where((eb) => eb("tonnage", ">", 800))
      .compile();
    expect(c.sql).toBe('select * from "cargo" where "tonnage" > $1');
    expect(c.parameters).toEqual([800]);
  });

  test("inequality operators render exactly as written", () => {
    /** Verifies: KYSL-EXPR-001 */
    expect(pg.selectFrom("cargo").selectAll().where("mass", "!=", 5).compile().sql).toBe(
      'select * from "cargo" where "mass" != $1',
    );
    expect(pg.selectFrom("cargo").selectAll().where("mass", "<>", 5).compile().sql).toBe(
      'select * from "cargo" where "mass" <> $1',
    );
  });

  test("an operator outside the supported set is rejected by name", () => {
    /** Verifies: KYSL-EXPR-002, KYSL-ERR-002 */
    expect(() => pg.selectFrom("cargo").selectAll().where("mass", "resembles" as any, 1)).toThrowError(
      /invalid operator "resembles"/,
    );
  });

  test("or and and lists render inside one pair of parentheses", () => {
    /** Verifies: KYSL-EXPR-003 */
    const o = pg
      .selectFrom("crew")
      .selectAll()
      .where((eb) => eb.or([eb("rank", "=", "captain"), eb("missions", "in", [3, 5])]))
      .compile();
    expect(o.sql).toBe('select * from "crew" where ("rank" = $1 or "missions" in ($2, $3))');
    expect(o.parameters).toEqual(["captain", 3, 5]);
    const a = pg
      .selectFrom("crew")
      .selectAll()
      .where((eb) => eb.and([eb("rank", "=", "mate"), eb("missions", ">", 1)]))
      .compile();
    expect(a.sql).toBe('select * from "crew" where ("rank" = $1 and "missions" > $2)');
  });

  test("not prefixes the wrapped expression", () => {
    /** Verifies: KYSL-EXPR-003 */
    const c = pg
      .selectFrom("crew")
      .selectAll()
      .where((eb) => eb.not(eb("missions", "<", 2)))
      .compile();
    expect(c.sql).toBe('select * from "crew" where not "missions" < $1');
  });

  test("between binds both bounds", () => {
    /** Verifies: KYSL-EXPR-004 */
    const c = pg
      .selectFrom("cargo")
      .selectAll()
      .where((eb) => eb.between("tonnage", 100, 900))
      .compile();
    expect(c.sql).toBe('select * from "cargo" where "tonnage" between $1 and $2');
    expect(c.parameters).toEqual([100, 900]);
  });

  test("in binds one parameter per element and an empty list renders bare parentheses", () => {
    /** Verifies: KYSL-EXPR-005 */
    const c = pg.selectFrom("cargo").selectAll().where("status", "in", ["docked", "lost"]).compile();
    expect(c.sql).toBe('select * from "cargo" where "status" in ($1, $2)');
    expect(c.parameters).toEqual(["docked", "lost"]);
    const e = pg.selectFrom("cargo").selectAll().where("status", "in", []).compile();
    expect(e.sql).toBe('select * from "cargo" where "status" in ()');
    expect(e.parameters).toEqual([]);
  });

  test("like and ilike bind their patterns", () => {
    /** Verifies: KYSL-EXPR-001 */
    const l = pg.selectFrom("crew").selectAll().where("call_sign", "like", "%ve%").compile();
    expect(l.sql).toBe('select * from "crew" where "call_sign" like $1');
    expect(l.parameters).toEqual(["%ve%"]);
    const i = pg.selectFrom("crew").selectAll().where("call_sign", "ilike", "%VE%").compile();
    expect(i.sql).toBe('select * from "crew" where "call_sign" ilike $1');
  });

  test("exists wraps a correlated subquery", () => {
    /** Verifies: KYSL-EXPR-006 */
    const c = pg
      .selectFrom("voyage")
      .selectAll()
      .where((eb) => eb.exists(eb.selectFrom("cargo").select("id").whereRef("cargo.voyage_id", "=", "voyage.id")))
      .compile();
    expect(c.sql).toBe(
      'select * from "voyage" where exists (select "id" from "cargo" where "cargo"."voyage_id" = "voyage"."id")',
    );
  });

  test("a correlated subquery projects as an aliased column", () => {
    /** Verifies: KYSL-EXPR-006 */
    const c = pg
      .selectFrom("voyage")
      .select((eb) => [
        "id",
        eb.selectFrom("cargo").select("label").whereRef("cargo.voyage_id", "=", "voyage.id").limit(1).as("top_label"),
      ])
      .compile();
    expect(c.sql).toBe(
      'select "id", (select "label" from "cargo" where "cargo"."voyage_id" = "voyage"."id" limit $1) as "top_label" from "voyage"',
    );
    expect(c.parameters).toEqual([1]);
  });

  test("a case expression parameterizes then and else values", () => {
    /** Verifies: KYSL-EXPR-007 */
    const c = pg
      .selectFrom("crew")
      .select((eb) => eb.case().when("missions", "<", 3).then("novice").else("veteran").end().as("grade"))
      .compile();
    expect(c.sql).toBe('select case when "missions" < $1 then $2 else $3 end as "grade" from "crew"');
    expect(c.parameters).toEqual([3, "novice", "veteran"]);
  });

  test("cast renders the target type unquoted and val binds through coalesce", () => {
    /** Verifies: KYSL-EXPR-008, KYSL-EXPR-009 */
    const c = pg
      .selectFrom("cargo")
      .select((eb) => eb.cast("mass", "integer").as("mi"))
      .compile();
    expect(c.sql).toBe('select cast("mass" as integer) as "mi" from "cargo"');
    const v = pg
      .selectFrom("cargo")
      .select((eb) => eb.fn.coalesce("mass", eb.val(0)).as("m"))
      .compile();
    expect(v.sql).toBe('select coalesce("mass", $1) as "m" from "cargo"');
    expect(v.parameters).toEqual([0]);
  });

  test("fn renders a generic function over column references", () => {
    /** Verifies: KYSL-EXPR-009 */
    const c = pg
      .selectFrom("crew")
      .select((eb) => eb.fn("length", ["call_sign"]).as("len"))
      .compile();
    expect(c.sql).toBe('select length("call_sign") as "len" from "crew"');
  });

  test("aggregate helpers render count and distinct", () => {
    /** Verifies: KYSL-EXPR-009 */
    expect(
      pg
        .selectFrom("crew")
        .select((eb) => eb.fn.count("id").as("n"))
        .compile().sql,
    ).toBe('select count("id") as "n" from "crew"');
    expect(
      pg
        .selectFrom("crew")
        .select((eb) => eb.fn.count("rank").distinct().as("n"))
        .compile().sql,
    ).toBe('select count(distinct "rank") as "n" from "crew"');
  });
});

describe("mutations", () => {
  test("insert renders columns from object keys and binds values", () => {
    /** Verifies: KYSL-MUT-001 */
    const c = pg.insertInto("crew").values({ call_sign: "Vega", missions: 3 }).compile();
    expect(c.sql).toBe('insert into "crew" ("call_sign", "missions") values ($1, $2)');
    expect(c.parameters).toEqual(["Vega", 3]);
  });

  test("multi-row insert unions columns and renders default for gaps", () => {
    /** Verifies: KYSL-MUT-002 */
    const c = pg
      .insertInto("crew")
      .values([
        { call_sign: "Vega", missions: 3 },
        { call_sign: "Lyra", rank: "mate" },
      ])
      .compile();
    expect(c.sql).toBe(
      'insert into "crew" ("call_sign", "missions", "rank") values ($1, $2, default), ($3, default, $4)',
    );
    expect(c.parameters).toEqual(["Vega", 3, "Lyra", "mate"]);
  });

  test("a raw fragment inserts inline instead of binding", () => {
    /** Verifies: KYSL-MUT-003 */
    const c = pg.insertInto("voyage").values({ logged_at: sql`now()` }).compile();
    expect(c.sql).toBe('insert into "voyage" ("logged_at") values (now())');
    expect(c.parameters).toEqual([]);
  });

  test("defaultValues renders the default values clause", () => {
    /** Verifies: KYSL-MUT-004 */
    const c = pg.insertInto("dock").defaultValues().compile();
    expect(c.sql).toBe('insert into "dock" default values');
  });

  test("on conflict renders do nothing and parameterized do update set", () => {
    /** Verifies: KYSL-MUT-005 */
    const n = pg
      .insertInto("crew")
      .values({ call_sign: "Vega" })
      .onConflict((oc) => oc.column("call_sign").doNothing())
      .compile();
    expect(n.sql).toBe('insert into "crew" ("call_sign") values ($1) on conflict ("call_sign") do nothing');
    expect(n.parameters).toEqual(["Vega"]);
    const u = pg
      .insertInto("crew")
      .values({ call_sign: "Vega" })
      .onConflict((oc) => oc.column("call_sign").doUpdateSet({ missions: 8 }))
      .compile();
    expect(u.sql).toBe(
      'insert into "crew" ("call_sign") values ($1) on conflict ("call_sign") do update set "missions" = $2',
    );
    expect(u.parameters).toEqual(["Vega", 8]);
  });

  test("mysql ignore renders insert ignore", () => {
    /** Verifies: KYSL-MUT-006 */
    const c = my.insertInto("crew").values({ call_sign: "Vega" }).ignore().compile();
    expect(c.sql).toBe("insert ignore into `crew` (`call_sign`) values (?)");
  });

  test("returning lists columns and returningAll renders star", () => {
    /** Verifies: KYSL-MUT-007 */
    const r = pg.insertInto("crew").values({ call_sign: "Vega" }).returning(["id"]).compile();
    expect(r.sql).toBe('insert into "crew" ("call_sign") values ($1) returning "id"');
    const ra = pg.updateTable("crew").set({ missions: 9 }).returningAll().compile();
    expect(ra.sql).toBe('update "crew" set "missions" = $1 returning *');
  });

  test("update set renders assignments in key order", () => {
    /** Verifies: KYSL-MUT-008 */
    const c = pg.updateTable("crew").set({ missions: 9, rank: "captain" }).where("id", "=", 4).compile();
    expect(c.sql).toBe('update "crew" set "missions" = $1, "rank" = $2 where "id" = $3');
    expect(c.parameters).toEqual([9, "captain", 4]);
  });

  test("update set accepts expression assignments", () => {
    /** Verifies: KYSL-MUT-008 */
    const c = pg
      .updateTable("crew")
      .set((eb) => ({ missions: eb("missions", "+", 1) }))
      .where("id", "=", 4)
      .compile();
    expect(c.sql).toBe('update "crew" set "missions" = "missions" + $1 where "id" = $2');
    expect(c.parameters).toEqual([1, 4]);
  });

  test("delete renders with filters and returning", () => {
    /** Verifies: KYSL-MUT-009, KYSL-MUT-007 */
    const c = pg.deleteFrom("cargo").where("mass", "<", 50).returningAll().compile();
    expect(c.sql).toBe('delete from "cargo" where "mass" < $1 returning *');
    expect(c.parameters).toEqual([50]);
  });
});

describe("composition primitives", () => {
  test("with prepends common table expressions in declaration order", () => {
    /** Verifies: KYSL-COMP-001 */
    const c = pg
      .with("heavy", (qb) => qb.selectFrom("cargo").select("id").where("mass", ">", 500))
      .with("labeled", (qb) => qb.selectFrom("heavy").select("id"))
      .selectFrom("labeled")
      .selectAll()
      .compile();
    expect(c.sql).toBe(
      'with "heavy" as (select "id" from "cargo" where "mass" > $1), "labeled" as (select "id" from "heavy") select * from "labeled"',
    );
    expect(c.parameters).toEqual([500]);
  });

  test("withRecursive renders the recursive keyword and column list", () => {
    /** Verifies: KYSL-COMP-002 */
    const c = pg
      .withRecursive("nums(n)", (qb: any) =>
        qb.selectNoFrom(sql`1`.as("n")).unionAll(qb.selectFrom("nums").select(sql`n + 1`.as("n")).where("n", "<", 4)),
      )
      .selectFrom("nums")
      .selectAll()
      .compile();
    expect(c.sql).toBe(
      'with recursive "nums"("n") as (select 1 as "n" union all select n + 1 as "n" from "nums" where "n" < $1) select * from "nums"',
    );
    expect(c.parameters).toEqual([4]);
  });

  test("union and unionAll chain in call order", () => {
    /** Verifies: KYSL-COMP-003 */
    const c = pg
      .selectFrom("dock")
      .select("id")
      .union(pg.selectFrom("berth").select("id"))
      .unionAll(pg.selectFrom("pier").select("id"))
      .compile();
    expect(c.sql).toBe('select "id" from "dock" union select "id" from "berth" union all select "id" from "pier"');
  });

  test("$if applies its refinement only when the condition is true", () => {
    /** Verifies: KYSL-COMP-004 */
    const on = pg
      .selectFrom("cargo")
      .selectAll()
      .$if(true, (qb) => qb.where("mass", ">", 9))
      .compile();
    expect(on.sql).toBe('select * from "cargo" where "mass" > $1');
    expect(on.parameters).toEqual([9]);
    const off = pg
      .selectFrom("cargo")
      .selectAll()
      .$if(false, (qb) => qb.where("mass", ">", 9))
      .compile();
    expect(off.sql).toBe('select * from "cargo"');
    expect(off.parameters).toEqual([]);
  });

  test("deriving a builder leaves the original unchanged", () => {
    /** Verifies: KYSL-COMP-005, KYSL-INV-003 */
    const base = pg.selectFrom("cargo").selectAll();
    const before = base.compile();
    const derived = base.where("mass", ">", 70);
    expect(base.compile().sql).toBe(before.sql);
    expect(base.compile().parameters).toEqual([]);
    expect(derived.compile().sql).toBe('select * from "cargo" where "mass" > $1');
  });
});

describe("raw sql fragments", () => {
  test("the template tag binds interpolations in order", () => {
    /** Verifies: KYSL-RAW-001, KYSL-RAW-002 */
    const c = sql`select * from harbor where depth > ${9} and lane = ${"west"}`.compile(pg);
    expect(c.sql).toBe("select * from harbor where depth > $1 and lane = $2");
    expect(c.parameters).toEqual([9, "west"]);
  });

  test("a fragment renders under the dialect it compiles against", () => {
    /** Verifies: KYSL-RAW-002, KYSL-RAW-004 */
    const frag = sql`select * from ${sql.table("harbor")} where ${sql.ref("depth")} > ${9}`;
    const p = frag.compile(pg);
    expect(p.sql).toBe('select * from "harbor" where "depth" > $1');
    expect(p.parameters).toEqual([9]);
    const m = frag.compile(my);
    expect(m.sql).toBe("select * from `harbor` where `depth` > ?");
    expect(m.parameters).toEqual([9]);
  });

  test("identifier helpers render quoted references", () => {
    /** Verifies: KYSL-RAW-004 */
    const c = sql`select ${sql.id("h", "lane")} from ${sql.table("harbor")} where ${sql.ref("depth")} > ${3}`.compile(pg);
    expect(c.sql).toBe('select "h"."lane" from "harbor" where "depth" > $1');
    expect(c.parameters).toEqual([3]);
  });

  test("lit inlines a literal and raw splices verbatim", () => {
    /** Verifies: KYSL-RAW-005 */
    const c = sql`select ${sql.raw("3 * 4")}, ${sql.lit("west")}`.compile(pg);
    expect(c.sql).toBe("select 3 * 4, 'west'");
    expect(c.parameters).toEqual([]);
  });

  test("join renders parameters with a default and a custom separator", () => {
    /** Verifies: KYSL-RAW-006 */
    const d = sql`select ${sql.join([1, 2, 3])}`.compile(pg);
    expect(d.sql).toBe("select $1, $2, $3");
    expect(d.parameters).toEqual([1, 2, 3]);
    const o = sql`select ${sql.join([1, 2], sql.raw(" or "))}`.compile(pg);
    expect(o.sql).toBe("select $1 or $2");
  });

  test("a fragment serves as a filter left-hand side", () => {
    /** Verifies: KYSL-RAW-003 */
    const c = pg
      .selectFrom("cargo")
      .selectAll()
      .where(sql`coalesce(${sql.ref("mass")}, 0)`, ">", 5)
      .compile();
    expect(c.sql).toBe('select * from "cargo" where coalesce("mass", 0) > $1');
    expect(c.parameters).toEqual([5]);
  });
});

describe("identifier transforms", () => {
  test("camel case plugin renders snake case tables and columns", () => {
    /** Verifies: KYSL-PLUG-001 */
    const c = cam.selectFrom("crewMember").select(["firstName", "lastName as ln"]).where("missionCount", ">", 2).compile();
    expect(c.sql).toBe('select "first_name", "last_name" as "ln" from "crew_member" where "mission_count" > $1');
    expect(c.parameters).toEqual([2]);
  });

  test("camel case plugin transforms alias positions qualified refs and raw refs", () => {
    /** Verifies: KYSL-PLUG-001 */
    expect(cam.selectFrom("crewMember as cm").select("cm.firstName").compile().sql).toBe(
      'select "cm"."first_name" from "crew_member" as "cm"',
    );
    expect(cam.selectFrom("crewMember").select("firstName as displayLabel").compile().sql).toBe(
      'select "first_name" as "display_label" from "crew_member"',
    );
    expect(cam.selectFrom("crewMember").select(sql`${sql.ref("firstName")}`.as("x")).compile().sql).toBe(
      'select "first_name" as "x" from "crew_member"',
    );
  });

  test("camel case plugin leaves parameters untouched", () => {
    /** Verifies: KYSL-PLUG-002, KYSL-INV-004 */
    const plain = pg.insertInto("crew_member").values({ first_name: "Ada", signup_count: 3 }).compile();
    const camc = cam.insertInto("crewMember").values({ firstName: "Ada", signupCount: 3 }).compile();
    expect(camc.sql).toBe('insert into "crew_member" ("first_name", "signup_count") values ($1, $2)');
    expect(camc.parameters).toEqual(plain.parameters);
  });

  test("withSchema qualifies table references across statement kinds", () => {
    /** Verifies: KYSL-PLUG-003 */
    expect(pg.withSchema("ops").selectFrom("crew").selectAll().compile().sql).toBe('select * from "ops"."crew"');
    expect(pg.withSchema("ops").insertInto("crew").values({ call_sign: "Vega" }).compile().sql).toBe(
      'insert into "ops"."crew" ("call_sign") values ($1)',
    );
    expect(
      pg.withSchema("ops").schema.createTable("berth").addColumn("id", "integer").compile().sql,
    ).toBe('create table "ops"."berth" ("id" integer)');
  });
});

describe("schema definition", () => {
  test("createTable passes column types through and lists columns", () => {
    /** Verifies: KYSL-DDL-001, KYSL-DDL-002 */
    const c = pg.schema
      .createTable("berth")
      .addColumn("id", "serial", (cb) => cb.primaryKey())
      .addColumn("label", "varchar(40)", (cb) => cb.notNull().unique())
      .compile();
    expect(c.sql).toBe('create table "berth" ("id" serial primary key, "label" varchar(40) not null unique)');
  });

  test("references with onDelete renders the foreign key action", () => {
    /** Verifies: KYSL-DDL-002 */
    const c = pg.schema
      .createTable("berth")
      .addColumn("dock_id", "integer", (cb) => cb.references("dock.id").onDelete("cascade"))
      .compile();
    expect(c.sql).toBe('create table "berth" ("dock_id" integer references "dock" ("id") on delete cascade)');
  });

  test("column modifiers render in canonical order regardless of call order", () => {
    /** Verifies: KYSL-DDL-002 */
    const p = pg.schema
      .createTable("berth")
      .addColumn("label", "text", (cb) => cb.unique().notNull())
      .compile();
    expect(p.sql).toBe('create table "berth" ("label" text not null unique)');
    const m = my.schema
      .createTable("berth")
      .addColumn("id", "integer", (cb) => cb.autoIncrement().primaryKey())
      .compile();
    expect(m.sql).toBe("create table `berth` (`id` integer primary key auto_increment)");
  });

  test("defaultTo inlines literals and raw fragments", () => {
    /** Verifies: KYSL-DDL-003 */
    expect(
      pg.schema.createTable("berth").addColumn("slots", "integer", (cb) => cb.defaultTo(0)).compile().sql,
    ).toBe('create table "berth" ("slots" integer default 0)');
    expect(
      pg.schema.createTable("berth").addColumn("state", "text", (cb) => cb.defaultTo("open")).compile().sql,
    ).toBe("create table \"berth\" (\"state\" text default 'open')");
    expect(
      pg.schema.createTable("berth").addColumn("noted_at", "timestamptz", (cb) => cb.defaultTo(sql`now()`)).compile()
        .sql,
    ).toBe('create table "berth" ("noted_at" timestamptz default now())');
  });

  test("createIndex dropTable and alterTable render their statements", () => {
    /** Verifies: KYSL-DDL-004 */
    expect(pg.schema.createIndex("berth_dock_idx").on("berth").column("dock_id").compile().sql).toBe(
      'create index "berth_dock_idx" on "berth" ("dock_id")',
    );
    expect(pg.schema.dropTable("berth").ifExists().compile().sql).toBe('drop table if exists "berth"');
    expect(pg.schema.alterTable("crew").addColumn("nickname", "text").compile().sql).toBe(
      'alter table "crew" add column "nickname" text',
    );
  });

  test("schema statements compile with empty parameters", () => {
    /** Verifies: KYSL-DDL-005 */
    const c = pg.schema
      .createTable("berth")
      .addColumn("slots", "integer", (cb) => cb.defaultTo(5))
      .compile();
    expect(c.parameters).toEqual([]);
  });
});

describe("execution lifecycle", () => {
  test("execute resolves with no rows and executeTakeFirst resolves undefined under the dummy driver", async () => {
    /** Verifies: KYSL-EXEC-001 */
    const rows = await pg.selectFrom("crew").selectAll().execute();
    expect(rows).toEqual([]);
    const first = await pg.selectFrom("crew").selectAll().executeTakeFirst();
    expect(first).toBeUndefined();
  });

  test("executeTakeFirstOrThrow rejects with NoResultError", async () => {
    /** Verifies: KYSL-EXEC-002, KYSL-ERR-003 */
    const p = pg.selectFrom("crew").selectAll().executeTakeFirstOrThrow();
    await expect(p).rejects.toBeInstanceOf(NoResultError);
    await expect(pg.selectFrom("crew").selectAll().executeTakeFirstOrThrow()).rejects.toThrowError(/no result/);
  });

  test("execution after destroy rejects while compilation still works", async () => {
    /** Verifies: KYSL-EXEC-003, KYSL-ERR-004, KYSL-INV-006 */
    const db = makeDb("pg");
    const q = db.selectFrom("crew").selectAll();
    const before = q.compile();
    await q.execute();
    await db.destroy();
    await expect(q.execute()).rejects.toThrowError(/destroyed/);
    expect(q.compile().sql).toBe(before.sql);
  });
});
