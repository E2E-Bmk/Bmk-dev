import csv
import json
import os
import sqlite3
import sys


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def qident(name):
    if not isinstance(name, str) or not name:
        fail("invalid identifier")
    return '"' + name.replace('"', '""') + '"'


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_out(value):
    print(compact_json(value))


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class Tx:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.conn.execute("BEGIN")
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False


def table_exists(conn, table):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def ordinary_table_exists(conn, table):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def require_table(conn, table):
    if not ordinary_table_exists(conn, table):
        fail(f"missing table: {table}")


def table_info(conn, table):
    rows = conn.execute(f"PRAGMA table_info({qident(table)})").fetchall()
    if not rows:
        require_table(conn, table)
    return [dict(row) for row in rows]


def column_names(conn, table):
    return [row["name"] for row in table_info(conn, table)]


def parse_pk(value):
    cols = [part.strip() for part in value.split(",") if part.strip()]
    if not cols:
        fail("empty primary key")
    return cols


def parse_common_flags(args, need_pk=False):
    fmt = None
    pk = None
    alter = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--json":
            fmt = "json"
            i += 1
        elif arg == "--csv":
            fmt = "csv"
            i += 1
        elif arg == "--pk":
            if i + 1 >= len(args):
                fail("--pk needs a value")
            pk = parse_pk(args[i + 1])
            i += 2
        elif arg == "--alter":
            alter = True
            i += 1
        else:
            fail(f"unknown option: {arg}")
    if fmt is None:
        fail("expected --json or --csv")
    if need_pk and not pk:
        fail("--pk is required")
    return fmt, pk or [], alter


def read_json_records(path):
    try:
        text = open(path, "r", encoding="utf-8").read()
    except OSError as e:
        fail(str(e))
    stripped = text.strip()
    if not stripped:
        return []
    try:
        value = json.loads(stripped)
        if not isinstance(value, list):
            fail("JSON input must be an array or newline-delimited objects")
        rows = value
    except json.JSONDecodeError:
        rows = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                fail(f"invalid JSON on line {line_no}: {e}")
    for row in rows:
        if not isinstance(row, dict):
            fail("each record must be an object")
    return rows


def read_csv_records(path):
    try:
        with open(path, "r", encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            if not reader.fieldnames:
                fail("CSV input needs a header row")
            if any(name is None or name == "" for name in reader.fieldnames):
                fail("CSV header contains an empty column name")
            return [dict(row) for row in reader]
    except csv.Error as e:
        fail(f"invalid CSV: {e}")
    except OSError as e:
        fail(str(e))


def load_records(path, fmt):
    if fmt == "json":
        return read_json_records(path)
    if fmt == "csv":
        return read_csv_records(path)
    fail("unknown input format")


def ordered_columns(rows, pk=()):
    cols = []
    seen = set()
    for col in pk:
        if col not in seen:
            cols.append(col)
            seen.add(col)
    for row in rows:
        for col in row.keys():
            if col not in seen:
                cols.append(col)
                seen.add(col)
    return cols


def normalize_value(value):
    if isinstance(value, (list, dict)):
        return compact_json(value)
    return value


def normalized_row(row):
    return {key: normalize_value(value) for key, value in row.items()}


def infer_type(values):
    saw_float = False
    saw_int = False
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            saw_int = True
        elif isinstance(value, int):
            saw_int = True
        elif isinstance(value, float):
            saw_float = True
        elif isinstance(value, (list, dict)):
            return "TEXT"
        else:
            return "TEXT"
    if saw_float:
        return "REAL"
    if saw_int:
        return "INTEGER"
    return "TEXT"


def infer_column_types(rows, cols):
    types = {}
    for col in cols:
        types[col] = infer_type([row.get(col) for row in rows])
    return types


def create_table_sql(table, cols, types, pk):
    if not cols:
        fail("cannot create a table with no columns")
    for col in pk:
        if col not in cols:
            fail(f"primary key column missing from records: {col}")
    defs = [f"{qident(col)} {types.get(col, 'TEXT')}" for col in cols]
    if pk:
        defs.append("PRIMARY KEY (" + ",".join(qident(col) for col in pk) + ")")
    return f"CREATE TABLE {qident(table)} (" + ", ".join(defs) + ")"


def ensure_insert_table(conn, table, rows, pk, alter):
    incoming_cols = ordered_columns(rows, pk)
    if not table_exists(conn, table):
        types = infer_column_types(rows, incoming_cols)
        conn.execute(create_table_sql(table, incoming_cols, types, pk))
        return incoming_cols

    existing_cols = column_names(conn, table)
    missing = [col for col in incoming_cols if col not in existing_cols]
    if missing and not alter:
        fail("unknown columns: " + ", ".join(missing))
    if missing:
        types = infer_column_types(rows, missing)
        for col in missing:
            conn.execute(
                f"ALTER TABLE {qident(table)} ADD COLUMN {qident(col)} {types[col]}"
            )
        existing_cols.extend(missing)
    return existing_cols


def insert_records(conn, table, rows, pk, alter):
    if not rows:
        if not table_exists(conn, table):
            fail("no rows to create table")
        return
    cols = ensure_insert_table(conn, table, rows, pk, alter)
    row_cols = [col for col in cols if any(col in row for row in rows)]
    sql = (
        f"INSERT INTO {qident(table)} ("
        + ",".join(qident(col) for col in row_cols)
        + ") VALUES ("
        + ",".join("?" for _ in row_cols)
        + ")"
    )
    for raw in rows:
        row = normalized_row(raw)
        conn.execute(sql, [row.get(col) for col in row_cols])


def upsert_records(conn, table, rows, pk, alter):
    if not rows:
        if not table_exists(conn, table):
            fail("no rows to create table")
        return
    ensure_insert_table(conn, table, rows, pk, alter)
    known = set(column_names(conn, table))
    for raw in rows:
        missing_pk = [col for col in pk if col not in raw]
        if missing_pk:
            fail("missing primary key column: " + ", ".join(missing_pk))
        unknown = [col for col in raw if col not in known]
        if unknown:
            fail("unknown columns: " + ", ".join(unknown))
        row = normalized_row(raw)
        cols = list(row.keys())
        update_cols = [col for col in cols if col not in pk]
        sql = (
            f"INSERT INTO {qident(table)} ("
            + ",".join(qident(col) for col in cols)
            + ") VALUES ("
            + ",".join("?" for _ in cols)
            + ") ON CONFLICT ("
            + ",".join(qident(col) for col in pk)
            + ") "
        )
        if update_cols:
            sql += "DO UPDATE SET " + ", ".join(
                f"{qident(col)} = excluded.{qident(col)}" for col in update_cols
            )
        else:
            sql += "DO NOTHING"
        conn.execute(sql, [row[col] for col in cols])


def rows_to_dicts(cursor):
    return [dict(row) for row in cursor.fetchall()]


def cmd_rows(conn, args):
    if not args:
        fail("rows needs a table")
    table = args[0]
    require_table(conn, table)
    where = None
    order = None
    limit = None
    i = 1
    while i < len(args):
        if args[i] == "--where":
            if i + 1 >= len(args):
                fail("--where needs a value")
            where = args[i + 1]
            i += 2
        elif args[i] == "--order":
            if i + 1 >= len(args):
                fail("--order needs a value")
            order = args[i + 1]
            i += 2
        elif args[i] == "--limit":
            if i + 1 >= len(args):
                fail("--limit needs a value")
            try:
                limit = int(args[i + 1])
            except ValueError:
                fail("--limit must be an integer")
            i += 2
        else:
            fail(f"unknown option: {args[i]}")
    sql = f"SELECT * FROM {qident(table)}"
    if where:
        sql += " WHERE " + where
    if order:
        sql += " ORDER BY " + order
    if limit is not None:
        sql += " LIMIT ?"
        cursor = conn.execute(sql, (limit,))
    else:
        cursor = conn.execute(sql)
    json_out(rows_to_dicts(cursor))


def cmd_query(conn, args):
    if not args:
        fail("query needs SQL")
    sql = " ".join(args)
    json_out(rows_to_dicts(conn.execute(sql)))


def cmd_tables(conn, args):
    counts = False
    for arg in args:
        if arg == "--counts":
            counts = True
        else:
            fail(f"unknown option: {arg}")
    names = [
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
    ]
    if counts:
        result = []
        for name in names:
            count = conn.execute(f"SELECT COUNT(*) AS n FROM {qident(name)}").fetchone()[
                "n"
            ]
            result.append({"table": name, "count": count})
        json_out(result)
    else:
        json_out(names)


def cmd_schema(conn, args):
    if len(args) != 1:
        fail("schema needs a table")
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        (args[0],),
    ).fetchone()
    if row is None:
        fail(f"missing table: {args[0]}")
    print(row["sql"])


def build_column_def(col, name=None, force_type=None, force_notnull=None, force_default=None):
    out_name = name if name is not None else col["name"]
    col_type = force_type if force_type is not None else (col["type"] or "TEXT")
    parts = [qident(out_name), col_type]
    notnull = col["notnull"] if force_notnull is None else force_notnull
    if notnull:
        parts.append("NOT NULL")
    dflt = col["dflt_value"] if force_default is None else force_default
    if dflt is not None:
        parts.append("DEFAULT " + dflt)
    return " ".join(parts)


def primary_key_cols(info, rename_map=None, drop_set=None):
    rename_map = rename_map or {}
    drop_set = drop_set or set()
    pk_rows = sorted([col for col in info if col["pk"]], key=lambda col: col["pk"])
    result = []
    for col in pk_rows:
        if col["name"] not in drop_set:
            result.append(rename_map.get(col["name"], col["name"]))
    return result


def create_rebuilt_table(conn, temp_table, info, final_names, drops, not_nulls, defaults, fks):
    defs = []
    pk = []
    for col in info:
        old = col["name"]
        if old in drops:
            continue
        new = final_names[old]
        dflt = defaults.get(new, col["dflt_value"])
        defs.append(build_column_def(col, name=new, force_notnull=(col["notnull"] or new in not_nulls), force_default=dflt))
        if col["pk"]:
            pk.append((col["pk"], new))
    pk_cols = [name for _, name in sorted(pk)]
    if pk_cols:
        defs.append("PRIMARY KEY (" + ",".join(qident(col) for col in pk_cols) + ")")
    defs.extend(fks)
    conn.execute(f"CREATE TABLE {qident(temp_table)} (" + ", ".join(defs) + ")")


def unique_temp_name(conn, base):
    candidate = f"_dbmini_{base}_new"
    i = 0
    while table_exists(conn, candidate):
        i += 1
        candidate = f"_dbmini_{base}_new_{i}"
    return candidate


def cmd_extract(conn, args):
    if len(args) != 3:
        fail("extract needs TABLE COLUMN NEW_TABLE")
    table, column, new_table = args
    require_table(conn, table)
    if table_exists(conn, new_table):
        fail(f"table already exists: {new_table}")
    info = table_info(conn, table)
    if column not in [col["name"] for col in info]:
        fail(f"missing column: {column}")

    rows = conn.execute(
        f"SELECT rowid AS _dbmini_rowid, * FROM {qident(table)} ORDER BY rowid"
    ).fetchall()
    values = []
    value_to_id = {}
    for row in rows:
        value = row[column]
        if value is not None and value not in value_to_id:
            value_to_id[value] = len(values) + 1
            values.append(value)

    with Tx(conn):
        conn.execute(
            f"CREATE TABLE {qident(new_table)} (id INTEGER PRIMARY KEY, value TEXT UNIQUE)"
        )
        for idx, value in enumerate(values, start=1):
            conn.execute(
                f"INSERT INTO {qident(new_table)} (id, value) VALUES (?, ?)",
                (idx, value),
            )

        temp = unique_temp_name(conn, table)
        final_names = {
            col["name"]: (col["name"] + "_id" if col["name"] == column else col["name"])
            for col in info
        }
        defs = []
        pk = []
        for col in info:
            old = col["name"]
            new = final_names[old]
            if old == column:
                defs.append(f"{qident(new)} INTEGER")
            else:
                defs.append(build_column_def(col, name=new))
            if col["pk"]:
                pk.append((col["pk"], new))
        if pk:
            defs.append(
                "PRIMARY KEY ("
                + ",".join(qident(name) for _, name in sorted(pk))
                + ")"
            )
        defs.append(
            f"FOREIGN KEY ({qident(column + '_id')}) REFERENCES {qident(new_table)}(id)"
        )
        conn.execute(f"CREATE TABLE {qident(temp)} (" + ", ".join(defs) + ")")

        out_cols = [final_names[col["name"]] for col in info]
        sql = (
            f"INSERT INTO {qident(temp)} ("
            + ",".join(qident(col) for col in out_cols)
            + ") VALUES ("
            + ",".join("?" for _ in out_cols)
            + ")"
        )
        for row in rows:
            vals = []
            for col in info:
                old = col["name"]
                if old == column:
                    value = row[old]
                    vals.append(value_to_id.get(value) if value is not None else None)
                else:
                    vals.append(row[old])
            conn.execute(sql, vals)
        conn.execute(f"DROP TABLE {qident(table)}")
        conn.execute(f"ALTER TABLE {qident(temp)} RENAME TO {qident(table)}")
    print("ok")


def cmd_enable_fts(conn, args):
    if len(args) < 2:
        fail("enable-fts needs TABLE COLUMN [COLUMN...]")
    table, cols = args[0], args[1:]
    require_table(conn, table)
    existing = set(column_names(conn, table))
    missing = [col for col in cols if col not in existing]
    if missing:
        fail("missing columns: " + ", ".join(missing))
    fts = table + "_fts"
    with Tx(conn):
        conn.execute(f"DROP TABLE IF EXISTS {qident(fts)}")
        conn.execute(
            f"CREATE VIRTUAL TABLE {qident(fts)} USING fts5("
            + ", ".join(qident(col) for col in cols)
            + ")"
        )
        conn.execute(
            f"INSERT INTO {qident(fts)} (rowid, "
            + ",".join(qident(col) for col in cols)
            + f") SELECT rowid, "
            + ",".join(qident(col) for col in cols)
            + f" FROM {qident(table)}"
        )
    print("ok")


def cmd_search(conn, args):
    if len(args) < 2:
        fail("search needs TABLE QUERY")
    table = args[0]
    query = args[1]
    limit = None
    i = 2
    while i < len(args):
        if args[i] == "--limit":
            if i + 1 >= len(args):
                fail("--limit needs a value")
            try:
                limit = int(args[i + 1])
            except ValueError:
                fail("--limit must be an integer")
            i += 2
        else:
            fail(f"unknown option: {args[i]}")
    require_table(conn, table)
    fts = table + "_fts"
    if not ordinary_table_exists(conn, fts):
        fail("FTS is not enabled")
    sql = (
        f"SELECT {qident(table)}.* FROM {qident(table)} "
        f"JOIN {qident(fts)} ON {qident(table)}.rowid = {qident(fts)}.rowid "
        f"WHERE {qident(fts)} MATCH ? "
        f"ORDER BY bm25({qident(fts)})"
    )
    params = [query]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    json_out(rows_to_dicts(conn.execute(sql, params)))


def sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return repr(value)
    if isinstance(value, (list, dict)):
        value = compact_json(value)
    else:
        value = str(value)
    return "'" + value.replace("'", "''") + "'"


def parse_default_value(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def parse_transform_args(args):
    renames = []
    drops = []
    not_nulls = []
    defaults = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--rename":
            if i + 1 >= len(args) or ":" not in args[i + 1]:
                fail("--rename needs OLD:NEW")
            old, new = args[i + 1].split(":", 1)
            if not old or not new:
                fail("--rename needs OLD:NEW")
            renames.append((old, new))
            i += 2
        elif arg == "--drop":
            if i + 1 >= len(args):
                fail("--drop needs a column")
            drops.append(args[i + 1])
            i += 2
        elif arg == "--not-null":
            if i + 1 >= len(args):
                fail("--not-null needs a column")
            not_nulls.append(args[i + 1])
            i += 2
        elif arg == "--default":
            if i + 1 >= len(args) or "=" not in args[i + 1]:
                fail("--default needs COL=VALUE")
            col, value = args[i + 1].split("=", 1)
            if not col:
                fail("--default needs COL=VALUE")
            defaults[col] = sql_literal(parse_default_value(value))
            i += 2
        else:
            fail(f"unknown option: {arg}")
    return renames, drops, not_nulls, defaults


def cmd_transform(conn, args):
    if not args:
        fail("transform needs a table")
    table = args[0]
    require_table(conn, table)
    renames, drops, not_nulls, defaults = parse_transform_args(args[1:])
    info = table_info(conn, table)
    original = [col["name"] for col in info]
    original_set = set(original)

    rename_map = {}
    for old, new in renames:
        if old not in original_set:
            fail(f"missing column: {old}")
        if old in rename_map:
            fail(f"duplicate rename: {old}")
        rename_map[old] = new

    drop_set = set()
    for col in drops:
        if col not in original_set:
            fail(f"missing column: {col}")
        drop_set.add(col)

    final_names = {}
    final_seen = set()
    for col in original:
        if col in drop_set:
            continue
        new = rename_map.get(col, col)
        if new in final_seen:
            fail(f"duplicate column after transform: {new}")
        final_seen.add(new)
        final_names[col] = new

    final_to_old = {new: old for old, new in final_names.items()}

    for col in not_nulls:
        if col not in final_seen:
            fail(f"missing column: {col}")
        source = final_to_old[col]
        count = conn.execute(
            f"SELECT COUNT(*) AS n FROM {qident(table)} WHERE {qident(source)} IS NULL"
        ).fetchone()["n"]
        if count:
            fail(f"not-null constraint would be violated: {col}")

    for col in defaults:
        if col not in final_seen:
            fail(f"missing column: {col}")

    if not final_names:
        fail("cannot drop every column")

    temp = unique_temp_name(conn, table)
    create_defaults = dict(defaults)
    fks = []
    with Tx(conn):
        create_rebuilt_table(
            conn,
            temp,
            info,
            final_names,
            drop_set,
            set(not_nulls),
            create_defaults,
            fks,
        )
        old_cols = [old for old in original if old not in drop_set]
        new_cols = [final_names[old] for old in old_cols]
        conn.execute(
            f"INSERT INTO {qident(temp)} ("
            + ",".join(qident(col) for col in new_cols)
            + ") SELECT "
            + ",".join(qident(col) for col in old_cols)
            + f" FROM {qident(table)}"
        )
        conn.execute(f"DROP TABLE {qident(table)}")
        conn.execute(f"ALTER TABLE {qident(temp)} RENAME TO {qident(table)}")
    print("ok")


def run(argv):
    if len(argv) < 3:
        fail("usage: dbmini.py DATABASE COMMAND [ARGS...]")
    db_path = argv[1]
    command = argv[2]
    args = argv[3:]
    conn = connect(db_path)
    try:
        if command in ("insert", "upsert"):
            if len(args) < 2:
                fail(f"{command} needs TABLE FILE")
            table, file_path = args[0], args[1]
            fmt, pk, alter = parse_common_flags(args[2:], need_pk=(command == "upsert"))
            rows = load_records(file_path, fmt)
            with Tx(conn):
                if command == "insert":
                    insert_records(conn, table, rows, pk, alter)
                else:
                    upsert_records(conn, table, rows, pk, alter)
            print("ok")
        elif command == "rows":
            cmd_rows(conn, args)
        elif command == "query":
            cmd_query(conn, args)
        elif command == "tables":
            cmd_tables(conn, args)
        elif command == "schema":
            cmd_schema(conn, args)
        elif command == "extract":
            cmd_extract(conn, args)
        elif command == "enable-fts":
            cmd_enable_fts(conn, args)
        elif command == "search":
            cmd_search(conn, args)
        elif command == "transform":
            cmd_transform(conn, args)
        else:
            fail(f"unknown command: {command}")
    except sqlite3.Error as e:
        fail(str(e))
    finally:
        conn.close()


if __name__ == "__main__":
    run(sys.argv)
