#!/usr/bin/env python3
"""dbmini: A compact SQLite database utility inspired by sqlite-utils."""

import argparse
import csv
import json
import os
import sqlite3
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def infer_json_type(value: Any) -> str | None:
    """Infer SQLite column type from a parsed JSON value."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    if isinstance(value, (list, dict)):
        return "TEXT"
    return "TEXT"


def infer_csv_type(value: str) -> str | None:
    """Infer SQLite column type from a CSV string cell."""
    if value == "":
        return None
    if value.lower() in ("true", "false"):
        return "INTEGER"
    try:
        int(value)
        return "INTEGER"
    except ValueError:
        pass
    try:
        float(value)
        return "REAL"
    except ValueError:
        pass
    return "TEXT"


def convert_csv_value(value: str, col_type: str) -> Any:
    """Convert a CSV cell to a Python value based on inferred type."""
    if value == "":
        return None
    if col_type == "INTEGER":
        if value.lower() == "true":
            return 1
        if value.lower() == "false":
            return 0
        try:
            return int(value)
        except ValueError:
            return value
    if col_type == "REAL":
        try:
            return float(value)
        except ValueError:
            return value
    return value


def prepare_json_value(value: Any) -> Any:
    """Prepare a Python value for SQLite storage."""
    if isinstance(value, (list, dict)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if isinstance(value, bool):
        return 1 if value else 0
    return value


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a connection with sensible defaults."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def json_dumps(obj: Any) -> str:
    """Compact JSON output."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=str)


def fail(msg: str) -> None:
    """Print error and exit non-zero."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_pk(pk_str: str) -> list[str]:
    """Parse comma-separated PK columns."""
    return [c.strip() for c in pk_str.split(",") if c.strip()]


def get_table_columns(conn: sqlite3.Connection, table: str) -> list[dict]:
    """Return PRAGMA table_info rows as dicts."""
    cur = conn.execute(f"PRAGMA table_info({json.dumps(table)})")
    return [dict(row) for row in cur.fetchall()]


def get_table_sql(conn: sqlite3.Connection, table: str) -> str:
    """Return the CREATE TABLE SQL for a table."""
    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    row = cur.fetchone()
    if not row or not row[0]:
        fail(f"Table '{table}' not found")
    return row[0]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if a table exists."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None


# ---------------------------------------------------------------------------
# File readers
# ---------------------------------------------------------------------------

def read_json_file(filepath: str) -> list[dict]:
    """Read a JSON file (array of objects or newline-delimited)."""
    with open(filepath, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            fail("JSON file must contain an array or newline-delimited objects")
        return data
    # Newline-delimited JSON
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def read_csv_file(filepath: str) -> tuple[list[str], list[dict]]:
    """Read a CSV file, returning (columns, rows)."""
    with open(filepath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return [], []
        columns = list(reader.fieldnames)
        rows = [dict(row) for row in reader]
    return columns, rows


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def infer_columns_json(rows: list[dict]) -> dict[str, str]:
    """Infer column names and types from JSON rows."""
    columns: dict[str, str] = {}
    for row in rows:
        for key, value in row.items():
            if key not in columns or columns[key] is None:
                t = infer_json_type(value)
                if t is not None:
                    columns[key] = t
    # Any column that only had nulls defaults to TEXT
    for key in columns:
        if columns[key] is None:
            columns[key] = "TEXT"
    return columns


def infer_columns_csv(header: list[str], rows: list[dict]) -> dict[str, str]:
    """Infer column types from CSV rows."""
    columns: dict[str, str] = {}
    for col in header:
        columns[col] = None
    for row in rows:
        for col in header:
            current = columns.get(col)
            if current is None:
                t = infer_csv_type(row.get(col, ""))
                if t is not None:
                    columns[col] = t
    for col in header:
        if columns[col] is None:
            columns[col] = "TEXT"
    return columns


def build_create_table_sql(
    table: str, columns: dict[str, str], pk: list[str] | None = None
) -> str:
    """Build a CREATE TABLE statement from column definitions."""
    parts = []
    for col, col_type in columns.items():
        parts.append(f"{json.dumps(col)} {col_type}")
    if pk:
        quoted = [json.dumps(c) for c in pk]
        parts.append(f"PRIMARY KEY ({', '.join(quoted)})")
    return f"CREATE TABLE {json.dumps(table)} ({', '.join(parts)})"


def ensure_table(
    conn: sqlite3.Connection, table: str, columns: dict[str, str], pk: list[str] | None
) -> None:
    """Create table if it doesn't exist, otherwise verify columns match."""
    if not table_exists(conn, table):
        sql = build_create_table_sql(table, columns, pk)
        conn.execute(sql)
        conn.commit()
        return

    # Table exists — check columns
    existing = {c["name"] for c in get_table_columns(conn, table)}
    for col in columns:
        if col not in existing:
            fail(f"Unknown column '{col}' in table '{table}'")


def alter_add_columns(
    conn: sqlite3.Connection, table: str, new_columns: dict[str, str]
) -> None:
    """Add new columns to an existing table."""
    existing = {c["name"] for c in get_table_columns(conn, table)}
    for col, col_type in new_columns.items():
        if col not in existing:
            conn.execute(
                f"ALTER TABLE {json.dumps(table)} "
                f"ADD COLUMN {json.dumps(col)} {col_type}"
            )


# ---------------------------------------------------------------------------
# Data import
# ---------------------------------------------------------------------------

def cmd_insert(
    conn: sqlite3.Connection,
    table: str,
    filepath: str,
    fmt: str,
    pk: list[str] | None,
    alter: bool,
) -> None:
    """Insert records into TABLE."""
    if not os.path.isfile(filepath):
        fail(f"File not found: {filepath}")

    if fmt == "json":
        rows = read_json_file(filepath)
        columns = infer_columns_json(rows)
        header = list(columns.keys())
    else:
        header, rows = read_csv_file(filepath)
        columns = infer_columns_csv(header, rows)

    if not table_exists(conn, table):
        ensure_table(conn, table, columns, pk)
    else:
        existing_cols = {c["name"] for c in get_table_columns(conn, table)}
        unknown = [c for c in columns if c not in existing_cols]
        if unknown and not alter:
            fail(f"Unknown column(s): {', '.join(unknown)}")
        if alter and unknown:
            alter_add_columns(conn, table, {c: columns[c] for c in unknown})
            conn.commit()
        ensure_table(conn, table, columns, pk)

    # Build INSERT
    col_names = list(columns.keys())
    placeholders = ", ".join(["?" for _ in col_names])
    quoted_cols = ", ".join(json.dumps(c) for c in col_names)
    sql = f"INSERT INTO {json.dumps(table)} ({quoted_cols}) VALUES ({placeholders})"

    for row in rows:
        if fmt == "csv":
            values = [convert_csv_value(row.get(c, ""), columns[c]) for c in col_names]
        else:
            values = [prepare_json_value(row.get(c)) for c in col_names]
        try:
            conn.execute(sql, values)
        except sqlite3.IntegrityError as e:
            conn.rollback()
            fail(str(e))

    conn.commit()
    print(f"Inserted {len(rows)} row(s) into {table}")


def cmd_upsert(
    conn: sqlite3.Connection,
    table: str,
    filepath: str,
    fmt: str,
    pk: list[str],
    alter: bool,
) -> None:
    """Upsert records into TABLE by primary key."""
    if not pk:
        fail("--pk is required for upsert")
    if not os.path.isfile(filepath):
        fail(f"File not found: {filepath}")

    if fmt == "json":
        rows = read_json_file(filepath)
        columns = infer_columns_json(rows)
        header = list(columns.keys())
    else:
        header, rows = read_csv_file(filepath)
        columns = infer_columns_csv(header, rows)

    if not table_exists(conn, table):
        ensure_table(conn, table, columns, pk)
    else:
        existing_cols = {c["name"] for c in get_table_columns(conn, table)}
        unknown = [c for c in columns if c not in existing_cols]
        if unknown and alter:
            alter_add_columns(conn, table, {c: columns[c] for c in unknown})
            conn.commit()

    col_names = list(columns.keys())

    # Build WHERE clause for PK lookup
    pk_where = " AND ".join(f"{json.dumps(c)} = ?" for c in pk)

    # Collect all column names in the table (including existing ones)
    all_cols = [c["name"] for c in get_table_columns(conn, table)]

    placeholders = ", ".join(["?" for _ in all_cols])
    quoted_cols = ", ".join(json.dumps(c) for c in all_cols)
    insert_sql = (
        f"INSERT OR REPLACE INTO {json.dumps(table)} "
        f"({quoted_cols}) VALUES ({placeholders})"
    )

    count = 0
    for row in rows:
        # Build PK values
        if fmt == "csv":
            pk_vals = [convert_csv_value(row.get(c, ""), columns.get(c, "TEXT")) for c in pk]
        else:
            pk_vals = [prepare_json_value(row.get(c)) for c in pk]

        # Look up existing row
        cur = conn.execute(
            f"SELECT * FROM {json.dumps(table)} WHERE {pk_where}", pk_vals
        )
        existing = cur.fetchone()

        # Merge: existing values with new row overriding
        merged = {}
        if existing:
            existing_dict = dict(existing)
            for c in all_cols:
                if c in existing_dict:
                    merged[c] = existing_dict[c]
            # Override with columns from the upsert row
            for c in col_names:
                if fmt == "csv":
                    merged[c] = convert_csv_value(row.get(c, ""), columns.get(c, "TEXT"))
                else:
                    if c in row:
                        merged[c] = prepare_json_value(row[c])
        else:
            # No existing row — use only the new row's values
            for c in all_cols:
                merged[c] = None
            for c in col_names:
                if fmt == "csv":
                    merged[c] = convert_csv_value(row.get(c, ""), columns.get(c, "TEXT"))
                else:
                    if c in row:
                        merged[c] = prepare_json_value(row[c])

        values = [merged.get(c) for c in all_cols]
        conn.execute(insert_sql, values)
        count += 1

    conn.commit()
    print(f"Upserted {count} row(s) into {table}")


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------

def cmd_rows(
    conn: sqlite3.Connection,
    table: str,
    where: str | None,
    order: str | None,
    limit: int | None,
) -> None:
    """Return rows from TABLE as JSON."""
    if not table_exists(conn, table):
        fail(f"Table '{table}' not found")

    sql = f"SELECT * FROM {json.dumps(table)}"
    params: list = []
    if where:
        sql += f" WHERE {where}"
    if order:
        sql += f" ORDER BY {order}"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    print(json_dumps(rows))


def cmd_query(conn: sqlite3.Connection, sql: str) -> None:
    """Run a SQL query and return JSON array."""
    try:
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
    except sqlite3.Error as e:
        fail(str(e))
    print(json_dumps(rows))


def cmd_tables(conn: sqlite3.Connection, counts: bool) -> None:
    """List table names, optionally with row counts."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    if counts:
        result = []
        for row in cur:
            name = row[0]
            cnt = conn.execute(
                f"SELECT COUNT(*) FROM {json.dumps(name)}"
            ).fetchone()[0]
            result.append({"table": name, "count": cnt})
        print(json_dumps(result))
    else:
        result = [row[0] for row in cur]
        print(json_dumps(result))


def cmd_schema(conn: sqlite3.Connection, table: str) -> None:
    """Print CREATE TABLE SQL."""
    if not table_exists(conn, table):
        fail(f"Table '{table}' not found")
    print(get_table_sql(conn, table))


# ---------------------------------------------------------------------------
# Derived structures
# ---------------------------------------------------------------------------

def cmd_extract(
    conn: sqlite3.Connection, table: str, column: str, new_table: str
) -> None:
    """Normalize repeated text values from TABLE.COLUMN into NEW_TABLE."""
    if not table_exists(conn, table):
        fail(f"Table '{table}' not found")

    existing_cols = {c["name"] for c in get_table_columns(conn, table)}
    if column not in existing_cols:
        fail(f"Column '{column}' not found in table '{table}'")

    if table_exists(conn, new_table):
        fail(f"Table '{new_table}' already exists")

    # Get all rows in original order and extract distinct non-null values
    rows = [
        dict(r)
        for r in conn.execute(
            f"SELECT rowid, * FROM {json.dumps(table)}"
        ).fetchall()
    ]

    # Collect distinct non-null values in first-seen order
    seen = set()
    value_order = []
    for row in rows:
        val = row.get(column)
        if val is not None and val not in seen:
            seen.add(val)
            value_order.append(val)

    # Create NEW_TABLE and insert values
    conn.execute(
        f"CREATE TABLE {json.dumps(new_table)} "
        "(id INTEGER PRIMARY KEY, value TEXT UNIQUE)"
    )
    value_to_id = {}
    for i, val in enumerate(value_order):
        conn.execute(
            f"INSERT INTO {json.dumps(new_table)} (id, value) VALUES (?, ?)",
            (i + 1, val),
        )
        value_to_id[val] = i + 1

    # Build new schema for original table
    col_info = get_table_columns(conn, table)
    new_col_name = f"{column}_id"

    new_col_defs = []
    for ci in col_info:
        if ci["name"] == column:
            new_col_defs.append(f"{json.dumps(new_col_name)} INTEGER")
        else:
            new_col_defs.append(
                f"{json.dumps(ci['name'])} {ci['type']}"
            )

    # Preserve primary key
    pk_cols = [ci["name"] for ci in col_info if ci["pk"]]
    if pk_cols:
        quoted_pk = ", ".join(json.dumps(c) for c in pk_cols)
        new_col_defs.append(f"PRIMARY KEY ({quoted_pk})")

    # Foreign key
    if new_col_name not in [ci["name"] for ci in col_info]:
        new_col_defs.append(
            f"FOREIGN KEY ({json.dumps(new_col_name)}) "
            f"REFERENCES {json.dumps(new_table)}(id)"
        )

    tmp_table = f"_dbmini_tmp_{table}"

    try:
        # Create new table
        conn.execute(
            f"CREATE TABLE {json.dumps(tmp_table)} ({', '.join(new_col_defs)})"
        )

        # Copy data
        new_col_names = [new_col_name if ci["name"] == column else ci["name"] for ci in col_info]
        quoted_new = ", ".join(json.dumps(c) for c in new_col_names)
        placeholders = ", ".join(["?" for _ in new_col_names])

        for row in rows:
            vals = []
            for ci in col_info:
                if ci["name"] == column:
                    orig_val = row.get(column)
                    vals.append(value_to_id.get(orig_val))
                else:
                    vals.append(row.get(ci["name"]))
            conn.execute(
                f"INSERT INTO {json.dumps(tmp_table)} ({quoted_new}) "
                f"VALUES ({placeholders})",
                vals,
            )

        # Swap tables
        conn.execute(f"DROP TABLE {json.dumps(table)}")
        conn.execute(
            f"ALTER TABLE {json.dumps(tmp_table)} RENAME TO {json.dumps(table)}"
        )

        conn.commit()
        print(f"Extracted '{column}' from '{table}' into '{new_table}'")

    except Exception:
        conn.rollback()
        # Clean up temp table if it exists
        try:
            conn.execute(f"DROP TABLE IF EXISTS {json.dumps(tmp_table)}")
            conn.commit()
        except Exception:
            pass
        raise


def cmd_enable_fts(
    conn: sqlite3.Connection, table: str, columns: list[str]
) -> None:
    """Create or rebuild an FTS5 table for TABLE."""
    if not table_exists(conn, table):
        fail(f"Table '{table}' not found")

    existing_cols = {c["name"] for c in get_table_columns(conn, table)}
    for col in columns:
        if col not in existing_cols:
            fail(f"Column '{col}' not found in table '{table}'")

    fts_table = f"{table}_fts"

    # Drop existing FTS table if any
    conn.execute(f"DROP TABLE IF EXISTS {json.dumps(fts_table)}")

    col_list = ", ".join(json.dumps(c) for c in columns)
    conn.execute(
        f"CREATE VIRTUAL TABLE {json.dumps(fts_table)} "
        f"USING fts5({col_list}, content={json.dumps(table)}, content_rowid='rowid')"
    )

    # Populate FTS index
    conn.execute(f"INSERT INTO {json.dumps(fts_table)}({json.dumps(fts_table)}) VALUES('rebuild')")
    conn.commit()
    print(f"FTS enabled on '{table}' for columns: {', '.join(columns)}")


def cmd_search(
    conn: sqlite3.Connection, table: str, query: str, limit: int | None
) -> None:
    """Search the FTS table and return matching rows."""
    fts_table = f"{table}_fts"
    if not table_exists(conn, fts_table):
        fail(f"FTS not enabled for table '{table}'")

    sql = (
        f"SELECT {json.dumps(table)}.* "
        f"FROM {json.dumps(table)} "
        f"JOIN {json.dumps(fts_table)} "
        f"ON {json.dumps(table)}.rowid = {json.dumps(fts_table)}.rowid "
        f"WHERE {json.dumps(fts_table)} MATCH ? "
        f"ORDER BY rank"
    )
    params: list = [query]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    print(json_dumps(rows))


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def cmd_transform(
    conn: sqlite3.Connection,
    table: str,
    rename: list[tuple[str, str]],
    drop: list[str],
    not_null: list[str],
    defaults: list[tuple[str, Any]],
) -> None:
    """Recreate TABLE with schema changes while preserving rows."""
    if not table_exists(conn, table):
        fail(f"Table '{table}' not found")

    col_info = get_table_columns(conn, table)
    col_names = [ci["name"] for ci in col_info]
    col_map = {ci["name"]: ci for ci in col_info}

    # Build rename mapping
    rename_map: dict[str, str] = {}
    for old, new in rename:
        if old not in col_names:
            fail(f"Cannot rename: column '{old}' not found")
        if old in rename_map:
            fail(f"Column '{old}' renamed multiple times")
        rename_map[old] = new

    # Build effective column name (after rename)
    def effective_name(name: str) -> str:
        return rename_map.get(name, name)

    # Validate drops
    for col in drop:
        if col not in col_names:
            fail(f"Cannot drop: column '{col}' not found")
        # If a column is dropped, it can't be renamed
        if col in rename_map:
            fail(f"Cannot drop and rename the same column: '{col}'")

    # Validate not-null
    for col in not_null:
        if col not in col_names:
            fail(f"Cannot set NOT NULL: column '{col}' not found")

    # Validate defaults
    for col, _ in defaults:
        if col not in col_names:
            fail(f"Cannot set default: column '{col}' not found")

    # Determine which columns to keep
    keep_cols = [c for c in col_names if c not in drop]
    new_names = [effective_name(c) for c in keep_cols]

    # Check for duplicate names after rename
    if len(new_names) != len(set(new_names)):
        fail("Column rename results in duplicate column names")

    # Get all rows
    rows = [
        dict(r)
        for r in conn.execute(f"SELECT * FROM {json.dumps(table)}").fetchall()
    ]

    # Check NOT NULL constraints
    for col in not_null:
        eff = effective_name(col)
        for row in rows:
            val = row.get(col)
            # Check if default will be applied
            has_default = any(d[0] == col for d in defaults)
            if val is None and not has_default:
                fail(
                    f"NOT NULL constraint would be violated for column "
                    f"'{eff}': existing row has NULL"
                )

    # Build new column definitions
    new_col_defs = []
    for ci in col_info:
        name = ci["name"]
        if name in drop:
            continue
        eff = effective_name(name)
        col_type = ci["type"]
        nn = name in not_null

        dflt_clause = ""
        for dcol, dval in defaults:
            if dcol == name:
                if isinstance(dval, str):
                    dflt_clause = f" DEFAULT {json.dumps(dval)}"
                elif dval is None:
                    dflt_clause = " DEFAULT NULL"
                else:
                    dflt_clause = f" DEFAULT {json.dumps(dval)}"
                break

        parts = [json.dumps(eff), col_type]
        if nn:
            parts.append("NOT NULL")
        if dflt_clause:
            parts.append(dflt_clause)
        new_col_defs.append(" ".join(parts))

    # Preserve PK columns not dropped
    pk_cols = [ci["name"] for ci in col_info if ci["pk"] and ci["name"] not in drop]
    if pk_cols:
        quoted_pk = ", ".join(json.dumps(effective_name(c)) for c in pk_cols)
        new_col_defs.append(f"PRIMARY KEY ({quoted_pk})")

    tmp_table = f"_dbmini_tmp_{table}"

    try:
        # Create new table
        conn.execute(
            f"CREATE TABLE {json.dumps(tmp_table)} ({', '.join(new_col_defs)})"
        )

        # Copy data
        quoted_cols = ", ".join(json.dumps(c) for c in new_names)
        placeholders = ", ".join(["?" for _ in new_names])

        for row in rows:
            vals = []
            for ci in col_info:
                name = ci["name"]
                if name in drop:
                    continue
                val = row.get(name)
                # Apply default if value is NULL and default is specified
                if val is None:
                    for dcol, dval in defaults:
                        if dcol == name:
                            val = dval
                            break
                vals.append(val)
            conn.execute(
                f"INSERT INTO {json.dumps(tmp_table)} ({quoted_cols}) "
                f"VALUES ({placeholders})",
                vals,
            )

        # Swap tables
        conn.execute(f"DROP TABLE {json.dumps(table)}")
        conn.execute(
            f"ALTER TABLE {json.dumps(tmp_table)} RENAME TO {json.dumps(table)}"
        )

        conn.commit()
        print(f"Transformed '{table}'")

    except Exception:
        conn.rollback()
        try:
            conn.execute(f"DROP TABLE IF EXISTS {json.dumps(tmp_table)}")
            conn.commit()
        except Exception:
            pass
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_default(s: str) -> tuple[str, Any]:
    """Parse COL=VALUE into (column, parsed_value)."""
    if "=" not in s:
        fail(f"Invalid default format: {s} (expected COL=VALUE)")
    col, val_str = s.split("=", 1)
    try:
        val = json.loads(val_str)
    except (json.JSONDecodeError, ValueError):
        val = val_str
    return col, val


def parse_rename(s: str) -> tuple[str, str]:
    """Parse OLD:NEW into (old, new)."""
    if ":" not in s:
        fail(f"Invalid rename format: {s} (expected OLD:NEW)")
    parts = s.split(":", 1)
    return parts[0], parts[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dbmini",
        description="Compact SQLite database utility",
    )
    parser.add_argument("database", help="SQLite database file path")
    parser.add_argument("command", help="Command to run")

    # Parse known args first to get the command
    args, remaining = parser.parse_known_args()

    db_path = args.database
    command = args.command

    # Build command-specific parser
    cmd_parser = argparse.ArgumentParser(add_help=False)
    conn = get_connection(db_path)

    try:
        if command == "insert":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("file")
            cmd_parser.add_argument("--json", action="store_true")
            cmd_parser.add_argument("--csv", action="store_true")
            cmd_parser.add_argument("--pk")
            cmd_parser.add_argument("--alter", action="store_true")
            opts = cmd_parser.parse_args(remaining)

            if opts.json == opts.csv:
                fail("Must specify either --json or --csv")
            fmt = "json" if opts.json else "csv"
            pk = parse_pk(opts.pk) if opts.pk else None
            cmd_insert(conn, opts.table, opts.file, fmt, pk, opts.alter)

        elif command == "upsert":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("file")
            cmd_parser.add_argument("--json", action="store_true")
            cmd_parser.add_argument("--csv", action="store_true")
            cmd_parser.add_argument("--pk", required=True)
            cmd_parser.add_argument("--alter", action="store_true")
            opts = cmd_parser.parse_args(remaining)

            if opts.json == opts.csv:
                fail("Must specify either --json or --csv")
            fmt = "json" if opts.json else "csv"
            pk = parse_pk(opts.pk)
            cmd_upsert(conn, opts.table, opts.file, fmt, pk, opts.alter)

        elif command == "rows":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("--where")
            cmd_parser.add_argument("--order")
            cmd_parser.add_argument("--limit", type=int)
            opts = cmd_parser.parse_args(remaining)
            cmd_rows(conn, opts.table, opts.where, opts.order, opts.limit)

        elif command == "query":
            cmd_parser.add_argument("sql", nargs=argparse.REMAINDER)
            opts = cmd_parser.parse_args(remaining)
            sql = " ".join(opts.sql)
            if not sql.strip():
                fail("SQL query is required")
            cmd_query(conn, sql)

        elif command == "tables":
            cmd_parser.add_argument("--counts", action="store_true")
            opts = cmd_parser.parse_args(remaining)
            cmd_tables(conn, opts.counts)

        elif command == "schema":
            cmd_parser.add_argument("table")
            opts = cmd_parser.parse_args(remaining)
            cmd_schema(conn, opts.table)

        elif command == "extract":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("column")
            cmd_parser.add_argument("new_table")
            opts = cmd_parser.parse_args(remaining)
            cmd_extract(conn, opts.table, opts.column, opts.new_table)

        elif command == "enable-fts":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("columns", nargs="+")
            opts = cmd_parser.parse_args(remaining)
            cmd_enable_fts(conn, opts.table, opts.columns)

        elif command == "search":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("query")
            cmd_parser.add_argument("--limit", type=int)
            opts = cmd_parser.parse_args(remaining)
            cmd_search(conn, opts.table, opts.query, opts.limit)

        elif command == "transform":
            cmd_parser.add_argument("table")
            cmd_parser.add_argument("--rename", action="append", default=[])
            cmd_parser.add_argument("--drop", action="append", default=[])
            cmd_parser.add_argument("--not-null", action="append", default=[])
            cmd_parser.add_argument("--default", action="append", default=[], dest="defaults")
            opts = cmd_parser.parse_args(remaining)

            renames = [parse_rename(r) for r in opts.rename]
            drops = opts.drop
            not_nulls = opts.not_null
            defs = [parse_default(d) for d in opts.defaults]
            cmd_transform(conn, opts.table, renames, drops, not_nulls, defs)

        else:
            fail(f"Unknown command: {command}")

    except Exception as e:
        conn.rollback()
        conn.close()
        fail(str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
