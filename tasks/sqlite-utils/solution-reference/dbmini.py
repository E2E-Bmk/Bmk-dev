#!/usr/bin/env python3
import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path


def q(name):
    return '"' + name.replace('"', '""') + '"'


def parse_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, bool):
        return int(value)
    return value


def parse_default(raw):
    try:
        return parse_value(json.loads(raw))
    except Exception:
        return raw


def coerce_scalar(value):
    if value == "":
        return ""
    low = value.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        if re_full_int(value):
            return int(value)
        if re_full_float(value):
            return float(value)
    except Exception:
        pass
    return value


def re_full_int(value):
    return value.lstrip("-").isdigit()


def re_full_float(value):
    if value.count(".") != 1:
        return False
    left, right = value.split(".", 1)
    return (left.lstrip("-").isdigit() or left in {"", "-"}) and right.isdigit()


def read_rows(path, fmt):
    text = Path(path).read_text(encoding="utf-8")
    if fmt == "json":
        stripped = text.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            rows = json.loads(stripped)
        else:
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        return [dict(row) for row in rows]
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [{key: coerce_scalar(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def infer_type(values):
    seen = [v for v in values if v is not None]
    if not seen:
        return "TEXT"
    if all(isinstance(v, bool) or (isinstance(v, int) and not isinstance(v, bool)) for v in seen):
        return "INTEGER"
    if all(isinstance(v, (bool, int, float)) and not isinstance(v, str) for v in seen):
        return "REAL"
    return "TEXT"


def normalized_rows(rows):
    return [{key: parse_value(value) for key, value in row.items()} for row in rows]


def table_exists(conn, table):
    return conn.execute("select 1 from sqlite_master where type in ('table','view') and name=?", (table,)).fetchone() is not None


def table_cols(conn, table):
    return [row[1] for row in conn.execute(f"pragma table_info({q(table)})")]


def table_info(conn, table):
    return conn.execute(f"pragma table_info({q(table)})").fetchall()


def create_table(conn, table, rows, pk):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    types = {key: infer_type([row.get(key) for row in rows]) for key in keys}
    defs = [f"{q(key)} {types[key]}" for key in keys]
    if pk:
        defs.append(f"PRIMARY KEY ({', '.join(q(col) for col in pk)})")
    conn.execute(f"create table {q(table)} ({', '.join(defs)})")


def add_missing_columns(conn, table, rows, alter):
    existing = table_cols(conn, table)
    incoming = []
    for row in rows:
        for key in row:
            if key not in incoming:
                incoming.append(key)
    missing = [key for key in incoming if key not in existing]
    if missing and not alter:
        raise RuntimeError(f"unknown columns: {', '.join(missing)}")
    for key in missing:
        conn.execute(f"alter table {q(table)} add column {q(key)} {infer_type([row.get(key) for row in rows])}")


def insert_rows(conn, table, rows, pk, alter=False, upsert=False):
    rows = normalized_rows(rows)
    if not rows:
        return
    with conn:
        if not table_exists(conn, table):
            create_table(conn, table, rows, pk)
        else:
            add_missing_columns(conn, table, rows, alter)
        cols = table_cols(conn, table)
        for row in rows:
            row_cols = [col for col in cols if col in row]
            placeholders = ", ".join("?" for _ in row_cols)
            if upsert:
                if not pk:
                    raise RuntimeError("upsert requires primary key")
                update_cols = [col for col in row_cols if col not in pk]
                if update_cols:
                    updates = ", ".join(f"{q(col)}=excluded.{q(col)}" for col in update_cols)
                    sql = f"insert into {q(table)} ({', '.join(q(c) for c in row_cols)}) values ({placeholders}) on conflict ({', '.join(q(c) for c in pk)}) do update set {updates}"
                else:
                    sql = f"insert or ignore into {q(table)} ({', '.join(q(c) for c in row_cols)}) values ({placeholders})"
            else:
                sql = f"insert into {q(table)} ({', '.join(q(c) for c in row_cols)}) values ({placeholders})"
            conn.execute(sql, [row.get(col) for col in row_cols])


def rows_to_dicts(cursor):
    names = [d[0] for d in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def output_json(rows):
    print(json.dumps(rows, separators=(",", ":")))


def cmd_insert(conn, args, upsert=False):
    fmt = "json" if args.json else "csv"
    pk = [p.strip() for p in (args.pk or "").split(",") if p.strip()]
    insert_rows(conn, args.table, read_rows(args.file, fmt), pk, args.alter, upsert=upsert)
    print("ok")


def cmd_rows(conn, args):
    sql = f"select * from {q(args.table)}"
    if args.where:
        sql += " where " + args.where
    if args.order:
        sql += " order by " + args.order
    if args.limit is not None:
        sql += f" limit {int(args.limit)}"
    output_json(rows_to_dicts(conn.execute(sql)))


def cmd_query(conn, args):
    output_json(rows_to_dicts(conn.execute(args.sql)))


def cmd_tables(conn, args):
    tables = [r[0] for r in conn.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")]
    if args.counts:
        output_json([{"table": name, "count": conn.execute(f"select count(*) from {q(name)}").fetchone()[0]} for name in tables if not name.endswith("_fts_config") and not name.endswith("_fts_data") and not name.endswith("_fts_idx") and not name.endswith("_fts_docsize")])
    else:
        output_json(tables)


def cmd_schema(conn, args):
    row = conn.execute("select sql from sqlite_master where type='table' and name=?", (args.table,)).fetchone()
    if not row:
        raise RuntimeError("missing table")
    print(row[0])


def recreate_table(conn, table, new_cols, select_exprs, pk_cols=None, foreign_keys=None, not_null=None, defaults=None):
    tmp = f"_{table}_new"
    pk_cols = pk_cols or []
    foreign_keys = foreign_keys or []
    not_null = set(not_null or [])
    defaults = defaults or {}
    defs = []
    for name, typ in new_cols:
        bits = [q(name), typ]
        if name in not_null:
            bits.append("NOT NULL")
        if name in defaults:
            bits.append("DEFAULT " + repr(defaults[name]))
        defs.append(" ".join(bits))
    if pk_cols:
        defs.append(f"PRIMARY KEY ({', '.join(q(c) for c in pk_cols)})")
    for col, ref_table, ref_col in foreign_keys:
        defs.append(f"FOREIGN KEY ({q(col)}) REFERENCES {q(ref_table)}({q(ref_col)})")
    conn.execute(f"create table {q(tmp)} ({', '.join(defs)})")
    conn.execute(f"insert into {q(tmp)} ({', '.join(q(c[0]) for c in new_cols)}) select {', '.join(select_exprs)} from {q(table)}")
    conn.execute(f"drop table {q(table)}")
    conn.execute(f"alter table {q(tmp)} rename to {q(table)}")


def cmd_extract(conn, args):
    info = table_info(conn, args.table)
    cols = [r[1] for r in info]
    if args.column not in cols:
        raise RuntimeError("missing column")
    with conn:
        conn.execute(f"create table {q(args.new_table)} (id INTEGER PRIMARY KEY, value TEXT UNIQUE)")
        seen = {}
        values = conn.execute(f"select {q(args.column)} from {q(args.table)}").fetchall()
        for (value,) in values:
            if value is not None and value not in seen:
                cur = conn.execute(f"insert into {q(args.new_table)} (value) values (?)", (value,))
                seen[value] = cur.lastrowid
        new_cols = []
        select_exprs = []
        pk_cols = [r[1] for r in info if r[5]]
        for cid, name, typ, notnull, default, pk in info:
            if name == args.column:
                new_cols.append((f"{name}_id", "INTEGER"))
                select_exprs.append(f"(select id from {q(args.new_table)} where value={q(args.table)}.{q(name)})")
            else:
                new_cols.append((name, typ or "TEXT"))
                select_exprs.append(q(name))
        recreate_table(conn, args.table, new_cols, select_exprs, pk_cols, [(f"{args.column}_id", args.new_table, "id")])
    print("ok")


def cmd_enable_fts(conn, args):
    cols = args.columns
    for col in cols:
        if col not in table_cols(conn, args.table):
            raise RuntimeError(f"missing column {col}")
    fts = f"{args.table}_fts"
    with conn:
        conn.execute(f"drop table if exists {q(fts)}")
        conn.execute(f"create virtual table {q(fts)} using fts5({', '.join(q(c) for c in cols)}, content={args.table!r}, content_rowid='rowid')")
        conn.execute(f"insert into {q(fts)}(rowid, {', '.join(q(c) for c in cols)}) select rowid, {', '.join(q(c) for c in cols)} from {q(args.table)}")
    print("ok")


def cmd_search(conn, args):
    fts = f"{args.table}_fts"
    if not table_exists(conn, fts):
        raise RuntimeError("FTS not enabled")
    sql = f"select {q(args.table)}.* from {q(fts)} join {q(args.table)} on {q(args.table)}.rowid = {q(fts)}.rowid where {q(fts)} match ? order by bm25({q(fts)})"
    if args.limit is not None:
        sql += f" limit {int(args.limit)}"
    output_json(rows_to_dicts(conn.execute(sql, (args.query,))))


def cmd_transform(conn, args):
    info = table_info(conn, args.table)
    if not info:
        raise RuntimeError("missing table")
    cols = [r[1] for r in info]
    renames = {}
    for item in args.rename or []:
        if ":" not in item:
            raise RuntimeError("rename must be OLD:NEW")
        old, new = item.split(":", 1)
        if old not in cols:
            raise RuntimeError("missing rename column")
        renames[old] = new
    drops = set(args.drop or [])
    missing = drops.difference(cols)
    if missing:
        raise RuntimeError("missing drop column")
    not_null = set(args.not_null or [])
    defaults = {}
    for item in args.default or []:
        if "=" not in item:
            raise RuntimeError("default must be COL=VALUE")
        key, value = item.split("=", 1)
        defaults[key] = parse_default(value)
    output_names = [(renames.get(r[1], r[1])) for r in info if r[1] not in drops]
    for col in not_null:
        if col not in output_names:
            raise RuntimeError("missing not-null column")
    for col in defaults:
        if col not in output_names:
            # Defaults may add a new column.
            pass
    with conn:
        # Validate not-null before changing anything.
        for original, output in [(r[1], renames.get(r[1], r[1])) for r in info if r[1] not in drops]:
            if output in not_null and conn.execute(f"select 1 from {q(args.table)} where {q(original)} is null limit 1").fetchone():
                raise RuntimeError("not-null would be violated")
        new_cols = []
        select_exprs = []
        pk_cols = []
        for cid, name, typ, notnull, default, pk in info:
            if name in drops:
                continue
            new_name = renames.get(name, name)
            new_cols.append((new_name, typ or "TEXT"))
            select_exprs.append(q(name))
            if pk:
                pk_cols.append(new_name)
        for col, value in defaults.items():
            if col not in [c[0] for c in new_cols]:
                new_cols.append((col, infer_type([value])))
                select_exprs.append("?")
        tmp = f"_{args.table}_new"
        defs = []
        for name, typ in new_cols:
            bits = [q(name), typ]
            if name in not_null:
                bits.append("NOT NULL")
            defs.append(" ".join(bits))
        if pk_cols:
            defs.append(f"PRIMARY KEY ({', '.join(q(c) for c in pk_cols)})")
        conn.execute(f"create table {q(tmp)} ({', '.join(defs)})")
        params = [value for col, value in defaults.items() if col not in cols and col not in renames.values()]
        conn.execute(f"insert into {q(tmp)} ({', '.join(q(c[0]) for c in new_cols)}) select {', '.join(select_exprs)} from {q(args.table)}", params)
        conn.execute(f"drop table {q(args.table)}")
        conn.execute(f"alter table {q(tmp)} rename to {q(args.table)}")
    print("ok")


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("database")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("insert", "upsert"):
        p = sub.add_parser(name)
        p.add_argument("table")
        p.add_argument("file")
        fmt = p.add_mutually_exclusive_group(required=True)
        fmt.add_argument("--json", action="store_true")
        fmt.add_argument("--csv", action="store_true")
        p.add_argument("--pk")
        p.add_argument("--alter", action="store_true")
    p = sub.add_parser("rows")
    p.add_argument("table")
    p.add_argument("--where")
    p.add_argument("--order")
    p.add_argument("--limit", type=int)
    p = sub.add_parser("query")
    p.add_argument("sql")
    p = sub.add_parser("tables")
    p.add_argument("--counts", action="store_true")
    p = sub.add_parser("schema")
    p.add_argument("table")
    p = sub.add_parser("extract")
    p.add_argument("table")
    p.add_argument("column")
    p.add_argument("new_table")
    p = sub.add_parser("enable-fts")
    p.add_argument("table")
    p.add_argument("columns", nargs="+")
    p = sub.add_parser("search")
    p.add_argument("table")
    p.add_argument("query")
    p.add_argument("--limit", type=int)
    p = sub.add_parser("transform")
    p.add_argument("table")
    p.add_argument("--rename", action="append")
    p.add_argument("--drop", action="append")
    p.add_argument("--not-null", action="append", dest="not_null")
    p.add_argument("--default", action="append")
    return parser


def main():
    args = build_parser().parse_args()
    conn = sqlite3.connect(args.database)
    conn.execute("pragma foreign_keys=on")
    try:
        if args.command == "insert":
            cmd_insert(conn, args, upsert=False)
        elif args.command == "upsert":
            cmd_insert(conn, args, upsert=True)
        elif args.command == "rows":
            cmd_rows(conn, args)
        elif args.command == "query":
            cmd_query(conn, args)
        elif args.command == "tables":
            cmd_tables(conn, args)
        elif args.command == "schema":
            cmd_schema(conn, args)
        elif args.command == "extract":
            cmd_extract(conn, args)
        elif args.command == "enable-fts":
            cmd_enable_fts(conn, args)
        elif args.command == "search":
            cmd_search(conn, args)
        elif args.command == "transform":
            cmd_transform(conn, args)
        conn.close()
        return 0
    except Exception as exc:
        conn.rollback()
        conn.close()
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
