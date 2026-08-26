// Spec2Repo oracle - integration tests for kysely-query-compiler-fullrepro-001
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

function countPlaceholders(sqlText: string, style: "pg" | "qmark"): number {
  if (style === "qmark") return (sqlText.match(/\?/g) ?? []).length;
  const nums = [...sqlText.matchAll(/\$(\d+)/g)].map((m) => Number(m[1]));
  return nums.length === 0 ? 0 : Math.max(...nums);
}

describe("cross-dialect consistency", () => {
  test("one join query compiles under all three dialects with identical parameters", () => {
    /** Verifies: KYSL-INV-001, KYSL-INST-006, KYSL-INST-007, KYSL-SEL-009. Seam: builder AST x three dialect compilers */
    const build = (db: AnyDb) =>
      db
        .selectFrom("voyage")
        .innerJoin("cargo", "cargo.voyage_id", "voyage.id")
        .select(["voyage.id", "cargo.label"])
        .where("cargo.mass", ">", 250)
        .where("voyage.status", "=", "active")
        .compile();
    const p = build(pg);
    const m = build(my);
    const s = build(lite);
    expect(p.sql).toBe(
      'select "voyage"."id", "cargo"."label" from "voyage" inner join "cargo" on "cargo"."voyage_id" = "voyage"."id" where "cargo"."mass" > $1 and "voyage"."status" = $2',
    );
    expect(m.sql).toBe(
      "select `voyage`.`id`, `cargo`.`label` from `voyage` inner join `cargo` on `cargo`.`voyage_id` = `voyage`.`id` where `cargo`.`mass` > ? and `voyage`.`status` = ?",
    );
    expect(s.sql).toBe(
      'select "voyage"."id", "cargo"."label" from "voyage" inner join "cargo" on "cargo"."voyage_id" = "voyage"."id" where "cargo"."mass" > ? and "voyage"."status" = ?',
    );
    expect(p.parameters).toEqual([250, "active"]);
    expect(m.parameters).toEqual(p.parameters);
    expect(s.parameters).toEqual(p.parameters);
  });

  test("placeholder counts equal parameter lengths across dialects", () => {
    /** Verifies: KYSL-INV-002, KYSL-EXPR-005, KYSL-SEL-013. Seam: expression parameters x dialect placeholder styles */
    const build = (db: AnyDb) =>
      db
        .selectFrom("cargo")
        .selectAll()
        .where("status", "in", ["docked", "lost", "manifest"])
        .where("mass", ">", 40)
        .limit(3)
        .offset(6)
        .compile();
    const p = build(pg);
    expect(countPlaceholders(p.sql, "pg")).toBe(p.parameters.length);
    expect(p.parameters.length).toBe(6);
    const m = build(my);
    expect(countPlaceholders(m.sql, "qmark")).toBe(m.parameters.length);
    const s = build(lite);
    expect(countPlaceholders(s.sql, "qmark")).toBe(s.parameters.length);
  });

  test("a mysql pipeline renders question marks throughout", () => {
    /** Verifies: KYSL-INST-006, KYSL-SEL-013, KYSL-SEL-009. Seam: full select pipeline x mysql compiler */
    const c = my
      .selectFrom("voyage")
      .leftJoin("cargo", (join) => join.onRef("cargo.voyage_id", "=", "voyage.id").on("cargo.mass", ">", 100))
      .select(["voyage.id"])
      .where("voyage.status", "=", "active")
      .limit(5)
      .offset(10)
      .compile();
    expect(c.sql).toBe(
      "select `voyage`.`id` from `voyage` left join `cargo` on `cargo`.`voyage_id` = `voyage`.`id` and `cargo`.`mass` > ? where `voyage`.`status` = ? limit ? offset ?",
    );
    expect(c.parameters).toEqual([100, "active", 5, 10]);
  });

  test("a sqlite insert returning renders question marks with double quotes", () => {
    /** Verifies: KYSL-MUT-007, KYSL-INST-006. Seam: mutation returning x sqlite compiler */
    const c = lite.insertInto("cargo").values({ label: "ore", mass: 120 }).returning("id").compile();
    expect(c.sql).toBe('insert into "cargo" ("label", "mass") values (?, ?) returning "id"');
    expect(c.parameters).toEqual(["ore", 120]);
  });
});

describe("composed queries", () => {
  test("a cte feeds a join with grouped aggregation", () => {
    /** Verifies: KYSL-COMP-001, KYSL-SEL-009, KYSL-EXPR-009, KYSL-SEL-011. Seam: CTE x join x aggregation */
    const c = pg
      .with("heavy", (qb) => qb.selectFrom("cargo").select(["voyage_id", "mass"]).where("mass", ">", 700))
      .selectFrom("voyage")
      .innerJoin("heavy", "heavy.voyage_id", "voyage.id")
      .select((eb) => ["voyage.id", eb.fn.count("heavy.mass").as("n")])
      .groupBy("voyage.id")
      .compile();
    expect(c.sql).toBe(
      'with "heavy" as (select "voyage_id", "mass" from "cargo" where "mass" > $1) select "voyage"."id", count("heavy"."mass") as "n" from "voyage" inner join "heavy" on "heavy"."voyage_id" = "voyage"."id" group by "voyage"."id"',
    );
    expect(c.parameters).toEqual([700]);
  });

  test("chained ctes reference earlier definitions and union a tail", () => {
    /** Verifies: KYSL-COMP-001, KYSL-COMP-003. Seam: chained CTEs x set operations */
    const c = pg
      .with("recent", (qb) => qb.selectFrom("voyage").select("id").where("status", "=", "active"))
      .with("flagged", (qb) => qb.selectFrom("recent").select("id"))
      .selectFrom("flagged")
      .select("id")
      .union(pg.selectFrom("dock").select("id"))
      .compile();
    expect(c.sql).toBe(
      'with "recent" as (select "id" from "voyage" where "status" = $1), "flagged" as (select "id" from "recent") select "id" from "flagged" union select "id" from "dock"',
    );
    expect(c.parameters).toEqual(["active"]);
  });

  test("a recursive counter cte compiles with a union all body", () => {
    /** Verifies: KYSL-COMP-002, KYSL-COMP-003. Seam: recursive CTE x union all body */
    const c = pg
      .withRecursive("tiers(lvl)", (qb: any) =>
        qb
          .selectNoFrom(sql`1`.as("lvl"))
          .unionAll(qb.selectFrom("tiers").select(sql`lvl + 1`.as("lvl")).where("lvl", "<", 6)),
      )
      .selectFrom("tiers")
      .selectAll()
      .compile();
    expect(c.sql).toBe(
      'with recursive "tiers"("lvl") as (select 1 as "lvl" union all select lvl + 1 as "lvl" from "tiers" where "lvl" < $1) select * from "tiers"',
    );
    expect(c.parameters).toEqual([6]);
  });

  test("an exists filter pairs with a correlated projection", () => {
    /** Verifies: KYSL-EXPR-006, KYSL-SEL-005. Seam: correlated projection x exists filter */
    const c = pg
      .selectFrom("voyage")
      .select((eb) => [
        "id",
        eb.selectFrom("cargo").select("label").whereRef("cargo.voyage_id", "=", "voyage.id").limit(1).as("top_label"),
      ])
      .where((eb) => eb.exists(eb.selectFrom("cargo").select("id").whereRef("cargo.voyage_id", "=", "voyage.id")))
      .compile();
    expect(c.sql).toBe(
      'select "id", (select "label" from "cargo" where "cargo"."voyage_id" = "voyage"."id" limit $1) as "top_label" from "voyage" where exists (select "id" from "cargo" where "cargo"."voyage_id" = "voyage"."id")',
    );
    expect(c.parameters).toEqual([1]);
  });

  test("a derived table join filters on expressions", () => {
    /** Verifies: KYSL-SEL-010, KYSL-EXPR-003. Seam: derived table join x boolean expression trees */
    const c = pg
      .selectFrom("voyage")
      .innerJoin(
        (eb: any) => eb.selectFrom("cargo").select(["voyage_id", "mass"]).where("mass", ">", 400).as("hc"),
        (join: any) => join.onRef("hc.voyage_id", "=", "voyage.id"),
      )
      .selectAll()
      .where((eb: any) => eb.or([eb("voyage.status", "=", "active"), eb("hc.mass", ">", 900)]))
      .compile();
    expect(c.sql).toBe(
      'select * from "voyage" inner join (select "voyage_id", "mass" from "cargo" where "mass" > $1) as "hc" on "hc"."voyage_id" = "voyage"."id" where ("voyage"."status" = $2 or "hc"."mass" > $3)',
    );
    expect(c.parameters).toEqual([400, "active", 900]);
  });

  test("conditional refinements match a hand-built chain", () => {
    /** Verifies: KYSL-COMP-004, KYSL-COMP-005. Seam: conditional refinement x hand-built equivalence */
    const hand = pg.selectFrom("cargo").selectAll().where("mass", ">", 12).compile();
    const cond = pg
      .selectFrom("cargo")
      .selectAll()
      .$if(true, (qb) => qb.where("mass", ">", 12))
      .$if(false, (qb) => qb.where("status", "=", "lost"))
      .compile();
    expect(hand.sql).toBe('select * from "cargo" where "mass" > $1');
    expect(cond.sql).toBe(hand.sql);
    expect(cond.parameters).toEqual([12]);
    expect(cond.parameters).toEqual(hand.parameters);
  });

  test("clearWhere resets filters before new ones apply", () => {
    /** Verifies: KYSL-SEL-008, KYSL-SEL-005. Seam: filter reset x re-filtering */
    const c = pg
      .selectFrom("cargo")
      .selectAll()
      .where("status", "=", "lost")
      .where("mass", "<", 10)
      .clearWhere()
      .where("mass", ">", 640)
      .compile();
    expect(c.sql).toBe('select * from "cargo" where "mass" > $1');
    expect(c.parameters).toEqual([640]);
  });

  test("case cast and aggregates compose in one projection", () => {
    /** Verifies: KYSL-EXPR-007, KYSL-EXPR-008, KYSL-EXPR-009. Seam: case x cast x aggregate in one projection */
    const c = pg
      .selectFrom("cargo")
      .select((eb) => [
        eb.case().when("mass", ">", 500).then("bulk").else("parcel").end().as("size"),
        eb.cast("mass", "integer").as("mi"),
        eb.fn.count("voyage_id").distinct().as("n"),
      ])
      .compile();
    expect(c.sql).toBe(
      'select case when "mass" > $1 then $2 else $3 end as "size", cast("mass" as integer) as "mi", count(distinct "voyage_id") as "n" from "cargo"',
    );
    expect(c.parameters).toEqual([500, "bulk", "parcel"]);
  });
});

describe("mutation pipelines", () => {
  test("a multi-row insert with conflict handling and returning binds in order", () => {
    /** Verifies: KYSL-MUT-002, KYSL-MUT-005, KYSL-MUT-007. Seam: multi-row insert x conflict clause x returning */
    const c = pg
      .insertInto("crew")
      .values([{ call_sign: "Vega", missions: 3 }, { call_sign: "Lyra" }])
      .onConflict((oc) => oc.column("call_sign").doUpdateSet({ missions: 9 }))
      .returning(["id", "call_sign"])
      .compile();
    expect(c.sql).toBe(
      'insert into "crew" ("call_sign", "missions") values ($1, $2), ($3, default) on conflict ("call_sign") do update set "missions" = $4 returning "id", "call_sign"',
    );
    expect(c.parameters).toEqual(["Vega", 3, "Lyra", 9]);
  });

  test("an update mixes expression assignments with bound values and returning", () => {
    /** Verifies: KYSL-MUT-008, KYSL-MUT-007. Seam: expression assignments x bound assignments x returning */
    const c = pg
      .updateTable("crew")
      .set((eb) => ({ missions: eb("missions", "+", 1), rank: "veteran" }))
      .where("id", "=", 4)
      .returningAll()
      .compile();
    expect(c.sql).toBe('update "crew" set "missions" = "missions" + $1, "rank" = $2 where "id" = $3 returning *');
    expect(c.parameters).toEqual([1, "veteran", 4]);
  });

  test("a delete filters through a subquery and returns rows", () => {
    /** Verifies: KYSL-SEL-014, KYSL-MUT-009, KYSL-MUT-007. Seam: delete x subquery filter x returning */
    const c = pg
      .deleteFrom("cargo")
      .where("voyage_id", "in", pg.selectFrom("voyage").select("id").where("status", "=", "lost"))
      .returning(["id"])
      .compile();
    expect(c.sql).toBe(
      'delete from "cargo" where "voyage_id" in (select "id" from "voyage" where "status" = $1) returning "id"',
    );
    expect(c.parameters).toEqual(["lost"]);
  });
});

describe("raw and builder interleaving", () => {
  test("embedded fragment parameters interleave left to right", () => {
    /** Verifies: KYSL-RAW-003, KYSL-INV-005. Seam: fragment parameters x builder parameters */
    const c = pg
      .selectFrom("cargo")
      .selectAll()
      .where("mass", ">", 100)
      .where(sql`mod(${7})`, ">", 1)
      .compile();
    expect(c.sql).toBe('select * from "cargo" where "mass" > $1 and mod($2) > $3');
    expect(c.parameters).toEqual([100, 7, 1]);
  });

  test("fragment values keep interpolation order standalone and embedded", () => {
    /** Verifies: KYSL-INV-005, KYSL-RAW-001. Seam: standalone fragment compile x embedded compile */
    const frag = sql`greatest(${5}, ${8})`;
    const alone = frag.compile(pg);
    expect(alone.sql).toBe("greatest($1, $2)");
    expect(alone.parameters).toEqual([5, 8]);
    const embedded = pg.selectFrom("cargo").selectAll().where("mass", ">", 2).where(frag, ">", 6).compile();
    expect(embedded.sql).toBe('select * from "cargo" where "mass" > $1 and greatest($2, $3) > $4');
    expect(embedded.parameters).toEqual([2, 5, 8, 6]);
  });

  test("identifier helpers follow the compiling dialect", () => {
    /** Verifies: KYSL-RAW-002, KYSL-RAW-004, KYSL-INST-006. Seam: identifier helpers x dialect quoting */
    const frag = sql`select ${sql.id("m", "berth")} from ${sql.table("manifest")}`;
    expect(frag.compile(pg).sql).toBe('select "m"."berth" from "manifest"');
    expect(frag.compile(my).sql).toBe("select `m`.`berth` from `manifest`");
    expect(frag.compile(lite).sql).toBe('select "m"."berth" from "manifest"');
  });
});

describe("transforms over mutations", () => {
  test("camel case rewrite leaves mutation parameters identical", () => {
    /** Verifies: KYSL-PLUG-001, KYSL-PLUG-002, KYSL-INV-004. Seam: plugin identifier rewrite x mutation parameters */
    const plain = pg.updateTable("crew_member").set({ mission_count: 9 }).where("is_active", "=", true).compile();
    const rewritten = cam.updateTable("crewMember").set({ missionCount: 9 }).where("isActive", "=", true).compile();
    expect(rewritten.sql).toBe('update "crew_member" set "mission_count" = $1 where "is_active" = $2');
    expect(rewritten.sql).toBe(plain.sql);
    expect(rewritten.parameters).toEqual(plain.parameters);
  });

  test("schema scoping spans queries mutations and ddl", () => {
    /** Verifies: KYSL-PLUG-003, KYSL-MUT-008, KYSL-DDL-001. Seam: schema scoping x queries x mutations x ddl */
    const scoped = pg.withSchema("ops");
    expect(scoped.selectFrom("crew").selectAll().compile().sql).toBe('select * from "ops"."crew"');
    expect(scoped.updateTable("crew").set({ missions: 1 }).compile().sql).toBe(
      'update "ops"."crew" set "missions" = $1',
    );
    expect(scoped.deleteFrom("crew").compile().sql).toBe('delete from "ops"."crew"');
    expect(scoped.schema.createTable("berth").addColumn("id", "integer").compile().sql).toBe(
      'create table "ops"."berth" ("id" integer)',
    );
  });

  test("camel case composes with schema scoping", () => {
    /** Verifies: KYSL-PLUG-001, KYSL-PLUG-003. Seam: camel case plugin x schema scoping */
    const c = cam
      .withSchema("ops")
      .updateTable("crewMember")
      .set({ isActive: false })
      .where("missionCount", ">", 2)
      .compile();
    expect(c.sql).toBe('update "ops"."crew_member" set "is_active" = $1 where "mission_count" > $2');
    expect(c.parameters).toEqual([false, 2]);
  });
});

describe("immutability across derivations", () => {
  test("a shared base branches into independent queries", () => {
    /** Verifies: KYSL-COMP-005, KYSL-INV-003. Seam: shared base builder x independent branches */
    const base = pg.selectFrom("cargo").select(["id", "label"]);
    const filtered = base.where("mass", ">", 30);
    const ordered = base.orderBy("label", "desc").limit(2);
    expect(base.compile().sql).toBe('select "id", "label" from "cargo"');
    expect(base.compile().parameters).toEqual([]);
    expect(filtered.compile().sql).toBe('select "id", "label" from "cargo" where "mass" > $1');
    expect(filtered.compile().parameters).toEqual([30]);
    expect(ordered.compile().sql).toBe('select "id", "label" from "cargo" order by "label" desc limit $1');
    expect(ordered.compile().parameters).toEqual([2]);
  });
});

describe("end-to-end workflows", () => {
  test("define schema insert query and destroy in one lifecycle", async () => {
    /** Verifies: KYSL-DDL-001, KYSL-MUT-001, KYSL-SEL-009, KYSL-EXEC-001, KYSL-EXEC-003, KYSL-INV-006. Seam: ddl x mutation x selection x execution lifecycle */
    const db = makeDb("pg");
    const ddl = db.schema
      .createTable("manifest")
      .addColumn("id", "serial", (cb) => cb.primaryKey())
      .addColumn("voyage_id", "integer", (cb) => cb.references("voyage.id").onDelete("cascade"))
      .compile();
    expect(ddl.sql).toBe(
      'create table "manifest" ("id" serial primary key, "voyage_id" integer references "voyage" ("id") on delete cascade)',
    );
    const ins = db.insertInto("manifest").values({ voyage_id: 12 }).returning(["id"]);
    expect(ins.compile().sql).toBe('insert into "manifest" ("voyage_id") values ($1) returning "id"');
    const sel = db
      .selectFrom("manifest")
      .innerJoin("voyage", "voyage.id", "manifest.voyage_id")
      .select(["manifest.id", "voyage.status"]);
    const selCompiled = sel.compile();
    expect(await sel.execute()).toEqual([]);
    expect(await sel.executeTakeFirst()).toBeUndefined();
    await db.destroy();
    await expect(sel.execute()).rejects.toThrowError(/destroyed/);
    expect(sel.compile().sql).toBe(selCompiled.sql);
  });

  test("one reporting query compiles under all dialects and executes", async () => {
    /** Verifies: KYSL-INV-001, KYSL-INV-002, KYSL-EXEC-001. Seam: one definition x three dialects x execution */
    const dbs: Array<[AnyDb, "pg" | "qmark"]> = [
      [makeDb("pg"), "pg"],
      [makeDb("mysql"), "qmark"],
      [makeDb("sqlite"), "qmark"],
    ];
    for (const [db, style] of dbs) {
      const q = db
        .selectFrom("voyage")
        .select((eb) => ["status", eb.fn.count("id").as("n")])
        .where("status", "in", ["active", "lost"])
        .groupBy("status")
        .orderBy("status");
      const c = q.compile();
      expect(c.parameters).toEqual(["active", "lost"]);
      expect(countPlaceholders(c.sql, style)).toBe(2);
      expect(await q.execute()).toEqual([]);
      await db.destroy();
    }
  });

  test("a camel case pipeline runs from ddl to select", async () => {
    /** Verifies: KYSL-PLUG-001, KYSL-DDL-001, KYSL-MUT-001, KYSL-EXEC-001. Seam: camel case plugin x ddl x mutation x execution */
    const db = makeDb("pg", [new CamelCasePlugin()]);
    expect(
      db.schema.createTable("crewMember").addColumn("missionCount", "integer", (cb) => cb.notNull()).compile().sql,
    ).toBe('create table "crew_member" ("mission_count" integer not null)');
    expect(db.schema.createIndex("crewIdx").on("crewMember").column("missionCount").compile().sql).toBe(
      'create index "crew_idx" on "crew_member" ("mission_count")',
    );
    const ins = db.insertInto("crewMember").values({ missionCount: 4 });
    expect(ins.compile().sql).toBe('insert into "crew_member" ("mission_count") values ($1)');
    const sel = db.selectFrom("crewMember as cm").select("cm.missionCount").where("cm.missionCount", ">", 1);
    expect(sel.compile().sql).toBe(
      'select "cm"."mission_count" from "crew_member" as "cm" where "cm"."mission_count" > $1',
    );
    expect(await sel.execute()).toEqual([]);
    await db.destroy();
  });

  test("raw fragments builders ctes and unions cooperate end to end", async () => {
    /** Verifies: KYSL-COMP-001, KYSL-COMP-003, KYSL-RAW-003, KYSL-EXEC-002. Seam: ctes x unions x raw fragments x execution errors */
    const db = makeDb("pg");
    const q = db
      .with("busy", (qb) => qb.selectFrom("dock").select("id").where(sql`coalesce(${sql.ref("lane")}, 0)`, ">", 2))
      .selectFrom("busy")
      .select("id")
      .unionAll(db.selectFrom("berth").select("id"))
      .compile();
    expect(q.sql).toBe(
      'with "busy" as (select "id" from "dock" where coalesce("lane", 0) > $1) select "id" from "busy" union all select "id" from "berth"',
    );
    expect(q.parameters).toEqual([2]);
    await expect(db.selectFrom("dock").selectAll().executeTakeFirstOrThrow()).rejects.toBeInstanceOf(NoResultError);
    await db.destroy();
  });
});
