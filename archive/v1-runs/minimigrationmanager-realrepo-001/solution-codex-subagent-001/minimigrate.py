"""A tiny dependency-free migration manager used by the public PRD tests."""

from __future__ import annotations

import copy
import re


class MigrationError(Exception):
    """Raised when a migration graph or schema operation is invalid."""


_REVISION_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_RESERVED_TARGETS = {"base", "heads", "current"}


class MiniMigrationManager:
    def __init__(self, root=None):
        self.root = root
        self._nodes = {}
        self._current = {"base"}
        self._schema = {}
        self._ledger = []
        self._runtime = {}
        self._pending = None
        self._pending_snapshot = None

    def revision(self, rev_id, parents=None, ops=None, message=""):
        self._ensure_mutable()
        self._validate_revision_id(rev_id)
        if rev_id in self._nodes:
            raise MigrationError("duplicate revision")

        normalized_parents = self._normalize_parents(parents)
        try:
            normalized_ops = list(ops or [])
        except TypeError as exc:
            raise MigrationError("ops must be iterable") from exc
        for op in normalized_ops:
            self._parse_op(op)
        self._validate_revision_metadata(normalized_ops)

        self._nodes[rev_id] = {
            "id": rev_id,
            "parents": normalized_parents,
            "children": set(),
            "message": message,
            "ops": normalized_ops,
        }
        for parent in normalized_parents:
            if parent != "base":
                self._nodes[parent]["children"].add(rev_id)
        return self.history_node(rev_id)

    def merge(self, rev_id, parents, message=""):
        return self.revision(rev_id, parents=parents, ops=[], message=message)

    def history(self):
        return [self.history_node(rev_id) for rev_id in sorted(self._nodes)]

    def history_node(self, rev_id):
        node = self._nodes[rev_id]
        return {
            "id": node["id"],
            "parents": list(node["parents"]),
            "children": sorted(node["children"]),
            "message": node["message"],
            "ops": list(node["ops"]),
        }

    def heads(self):
        return sorted(
            rev_id for rev_id, node in self._nodes.items() if not node["children"]
        )

    def current(self):
        return {
            "revisions": self._public_current(self._current),
            "pending": copy.deepcopy(self._pending),
        }

    def schema(self):
        return {"tables": self._copy_schema(self._schema)}

    def plan(self, direction, target):
        if direction == "upgrade":
            return self._upgrade_plan(target)
        if direction == "downgrade":
            return self._downgrade_plan(target)
        raise MigrationError("unknown direction")

    def upgrade(self, target, fail_at=None):
        self._ensure_mutable()
        if fail_at not in (None, "after_schema", "after_ledger"):
            raise MigrationError("unsupported fail_at")
        steps = self._upgrade_plan(target)
        self._run_steps("upgrade", target, steps, fail_at)
        return self.current()

    def downgrade(self, target, fail_at=None):
        self._ensure_mutable()
        if fail_at not in (None, "after_schema", "after_ledger"):
            raise MigrationError("unsupported fail_at")
        steps = self._downgrade_plan(target)
        self._ensure_reversible(steps)
        self._run_steps("downgrade", target, steps, fail_at)
        return self.current()

    def stamp(self, target):
        self._ensure_mutable()
        target_current = self._resolve_target_current(target)
        before = self._public_current(self._current)
        self._current = set(target_current)
        after = self._public_current(self._current)
        self._ledger.append(
            {
                "kind": "stamp",
                "revision": None,
                "before_current": before,
                "after_current": after,
            }
        )
        return self.current()

    def ledger(self):
        return {"entries": copy.deepcopy(self._ledger)}

    def recover(self):
        before = self._public_current(self._current)
        if self._pending is None:
            return {
                "status": "no_pending",
                "before_current": before,
                "after_current": before,
            }

        snapshot = self._pending_snapshot
        self._schema = self._copy_schema(snapshot["schema"])
        self._current = set(snapshot["current"])
        self._ledger = copy.deepcopy(snapshot["ledger"])
        self._runtime = copy.deepcopy(snapshot["runtime"])
        after = self._public_current(self._current)
        self._pending = None
        self._pending_snapshot = None
        self._ledger.append(
            {
                "kind": "recover",
                "revision": None,
                "before_current": before,
                "after_current": after,
            }
        )
        return {
            "status": "rolled_back",
            "before_current": before,
            "after_current": after,
        }

    def _ensure_mutable(self):
        if self._pending is not None:
            raise MigrationError("recovery pending")

    def _validate_revision_id(self, rev_id):
        if not isinstance(rev_id, str) or not _REVISION_RE.match(rev_id):
            raise MigrationError("invalid revision id")
        if rev_id in _RESERVED_TARGETS:
            raise MigrationError("reserved revision id")

    def _normalize_parents(self, parents):
        if parents is None:
            heads = self.heads()
            if not heads:
                return ["base"]
            if len(heads) == 1:
                return heads
            raise MigrationError("parents required when multiple heads exist")
        if isinstance(parents, str):
            parents = [parents]
        try:
            normalized = list(parents)
        except TypeError as exc:
            raise MigrationError("parents must be iterable") from exc
        if not normalized:
            normalized = ["base"]
        if len(set(normalized)) != len(normalized):
            raise MigrationError("duplicate parents")
        if "base" in normalized and len(normalized) > 1:
            raise MigrationError("base cannot be mixed with other parents")
        for parent in normalized:
            if parent == "base":
                continue
            if parent not in self._nodes:
                raise MigrationError("unknown parent")
        return normalized

    def _parse_op(self, op):
        if not isinstance(op, str):
            raise MigrationError("operation must be a string")
        parts = op.split()
        if not parts:
            raise MigrationError("empty operation")
        kind = parts[0]

        if kind in ("create_table", "restore_table"):
            if len(parts) < 3:
                raise MigrationError("table operation requires columns")
            return (kind, parts[1], self._parse_columns(parts[2:]))
        if kind == "drop_table":
            if len(parts) != 2:
                raise MigrationError("drop_table requires table")
            return (kind, parts[1])
        if kind in ("add_column", "restore_column"):
            if len(parts) != 3:
                raise MigrationError("column operation requires table and column")
            name, typ = self._parse_column(parts[2])
            return (kind, parts[1], name, typ)
        if kind == "drop_column":
            if len(parts) != 3 or ":" in parts[2]:
                raise MigrationError("drop_column requires table and column name")
            return (kind, parts[1], parts[2])
        if kind == "rename_table":
            if len(parts) != 3:
                raise MigrationError("rename_table requires old and new names")
            if parts[1] == parts[2]:
                raise MigrationError("rename_table requires different names")
            return (kind, parts[1], parts[2])
        raise MigrationError("unknown operation")

    def _parse_columns(self, specs):
        columns = [self._parse_column(spec) for spec in specs]
        names = [name for name, _typ in columns]
        if len(set(names)) != len(names):
            raise MigrationError("duplicate columns")
        return columns

    def _parse_column(self, spec):
        if ":" not in spec:
            raise MigrationError("column spec must contain ':'")
        name, typ = spec.split(":", 1)
        if not name or not typ:
            raise MigrationError("empty column name or type")
        return name, typ

    def _validate_revision_metadata(self, ops):
        restore_tables = set()
        restore_columns = set()
        for op in ops:
            parsed = self._parse_op(op)
            if parsed[0] == "restore_table":
                if parsed[1] in restore_tables:
                    raise MigrationError("duplicate restore_table metadata")
                restore_tables.add(parsed[1])
            elif parsed[0] == "restore_column":
                key = (parsed[1], parsed[2])
                if key in restore_columns:
                    raise MigrationError("duplicate restore_column metadata")
                restore_columns.add(key)

    def _resolve_target_current(self, target):
        if not isinstance(target, str):
            raise MigrationError("unknown target")
        if target == "base":
            return {"base"}
        if target == "current":
            return set(self._current)
        if target == "heads":
            heads = set(self.heads())
            return heads or {"base"}
        if target in self._nodes:
            return {target}
        raise MigrationError("unknown target")

    def _applied_closure(self, current):
        current = set(current)
        if not current or current == {"base"}:
            return set()
        applied = set()

        def visit(rev_id):
            if rev_id == "base" or rev_id in applied:
                return
            if rev_id not in self._nodes:
                raise MigrationError("unknown current revision")
            applied.add(rev_id)
            for parent in self._nodes[rev_id]["parents"]:
                visit(parent)

        for rev_id in current:
            visit(rev_id)
        return applied

    def _target_closure(self, target):
        return self._applied_closure(self._resolve_target_current(target))

    def _upgrade_plan(self, target):
        target_current = self._resolve_target_current(target)
        applied = self._applied_closure(self._current)
        target_applied = self._applied_closure(target_current)
        if not applied.issubset(target_applied):
            raise MigrationError("upgrade target is not above current")
        missing = target_applied - applied
        order = self._topological_order(target_applied)
        return [
            {
                "direction": "upgrade",
                "revision": rev_id,
                "ops": list(self._nodes[rev_id]["ops"]),
            }
            for rev_id in order
            if rev_id in missing
        ]

    def _downgrade_plan(self, target):
        if target == "heads":
            raise MigrationError("cannot downgrade to heads")
        target_current = self._resolve_target_current(target)
        applied = self._applied_closure(self._current)
        target_applied = self._applied_closure(target_current)
        if not target_applied.issubset(applied):
            raise MigrationError("downgrade target is not below current")
        reverting = applied - target_applied
        order = list(reversed(self._topological_order(applied)))
        return [
            {
                "direction": "downgrade",
                "revision": rev_id,
                "ops": list(self._nodes[rev_id]["ops"]),
            }
            for rev_id in order
            if rev_id in reverting
        ]

    def _topological_order(self, rev_ids):
        rev_ids = set(rev_ids)
        seen = set()
        order = []

        def visit(rev_id):
            if rev_id == "base" or rev_id in seen or rev_id not in rev_ids:
                return
            seen.add(rev_id)
            for parent in self._nodes[rev_id]["parents"]:
                visit(parent)
            order.append(rev_id)

        for rev_id in sorted(rev_ids):
            visit(rev_id)
        return order

    def _run_steps(self, operation, target, steps, fail_at):
        if not steps:
            return

        snapshot = self._snapshot()
        schema = self._copy_schema(self._schema)
        ledger = copy.deepcopy(self._ledger)
        runtime = copy.deepcopy(self._runtime)
        current = set(self._current)
        applied = self._applied_closure(current)

        try:
            for index, step in enumerate(steps):
                rev_id = step["revision"]
                before_current = self._public_current(current)
                if operation == "upgrade":
                    self._apply_revision(rev_id, schema, runtime)
                    applied.add(rev_id)
                    current = self._heads_for_applied(applied)
                    kind = "apply"
                else:
                    self._downgrade_revision(rev_id, schema, runtime)
                    applied.remove(rev_id)
                    current = self._heads_for_applied(applied)
                    kind = "downgrade"

                if fail_at == "after_schema" and index == 0:
                    raise _InjectedFailure

                after_current = self._public_current(current)
                ledger.append(
                    {
                        "kind": kind,
                        "revision": rev_id,
                        "before_current": before_current,
                        "after_current": after_current,
                    }
                )

                if fail_at == "after_ledger" and index == 0:
                    raise _InjectedFailure
        except _InjectedFailure:
            self._restore_snapshot(snapshot)
            self._pending = {
                "operation": operation,
                "target": target,
                "failure_point": fail_at,
            }
            self._pending_snapshot = snapshot
            raise MigrationError("migration failed")
        except MigrationError:
            self._restore_snapshot(snapshot)
            raise

        self._schema = schema
        self._current = current
        self._ledger = ledger
        self._runtime = runtime

    def _snapshot(self):
        return {
            "schema": self._copy_schema(self._schema),
            "current": set(self._current),
            "ledger": copy.deepcopy(self._ledger),
            "runtime": copy.deepcopy(self._runtime),
        }

    def _restore_snapshot(self, snapshot):
        self._schema = self._copy_schema(snapshot["schema"])
        self._current = set(snapshot["current"])
        self._ledger = copy.deepcopy(snapshot["ledger"])
        self._runtime = copy.deepcopy(snapshot["runtime"])

    def _apply_revision(self, rev_id, schema, runtime):
        runtime.setdefault(rev_id, {"drop_tables": {}, "drop_columns": {}})
        for op in self._nodes[rev_id]["ops"]:
            self._apply_upgrade_op(self._parse_op(op), schema, runtime, rev_id)

    def _downgrade_revision(self, rev_id, schema, runtime):
        metadata = self._revision_metadata(rev_id)
        for op in reversed(self._nodes[rev_id]["ops"]):
            self._apply_downgrade_op(
                self._parse_op(op), schema, metadata, runtime, rev_id
            )
        runtime.pop(rev_id, None)

    def _ensure_reversible(self, steps):
        for step in steps:
            metadata = self._revision_metadata(step["revision"])
            for op in self._nodes[step["revision"]]["ops"]:
                parsed = self._parse_op(op)
                if parsed[0] == "drop_table" and parsed[1] not in metadata["tables"]:
                    raise MigrationError("irreversible drop_table")
                if parsed[0] == "drop_column":
                    key = (parsed[1], parsed[2])
                    if key not in metadata["columns"]:
                        raise MigrationError("irreversible drop_column")

    def _revision_metadata(self, rev_id):
        tables = {}
        columns = {}
        for op in self._nodes[rev_id]["ops"]:
            parsed = self._parse_op(op)
            if parsed[0] == "restore_table":
                tables[parsed[1]] = parsed[2]
            elif parsed[0] == "restore_column":
                columns[(parsed[1], parsed[2])] = parsed[3]
        return {"tables": tables, "columns": columns}

    def _apply_upgrade_op(self, parsed, schema, runtime, rev_id):
        kind = parsed[0]
        if kind == "create_table":
            _kind, table, columns = parsed
            if table in schema:
                raise MigrationError("table already exists")
            schema[table] = [[name, typ] for name, typ in columns]
        elif kind == "drop_table":
            _kind, table = parsed
            if table not in schema:
                raise MigrationError("missing table")
            runtime[rev_id]["drop_tables"][table] = {
                "index": list(schema).index(table),
                "columns": [list(column) for column in schema[table]],
            }
            del schema[table]
        elif kind == "restore_table":
            return
        elif kind == "add_column":
            _kind, table, name, typ = parsed
            columns = self._table_columns(schema, table)
            if self._column_index(columns, name) is not None:
                raise MigrationError("column already exists")
            columns.append([name, typ])
        elif kind == "drop_column":
            _kind, table, name = parsed
            columns = self._table_columns(schema, table)
            index = self._column_index(columns, name)
            if index is None:
                raise MigrationError("missing column")
            runtime[rev_id]["drop_columns"][(table, name)] = {
                "index": index,
                "column": list(columns[index]),
            }
            del columns[index]
        elif kind == "restore_column":
            return
        elif kind == "rename_table":
            _kind, old, new = parsed
            self._rename_table(schema, old, new)

    def _apply_downgrade_op(self, parsed, schema, metadata, runtime, rev_id):
        kind = parsed[0]
        if kind == "create_table":
            _kind, table, _columns = parsed
            if table not in schema:
                raise MigrationError("missing table")
            del schema[table]
        elif kind == "drop_table":
            _kind, table = parsed
            if table in schema:
                raise MigrationError("table already exists")
            if table not in metadata["tables"]:
                raise MigrationError("irreversible drop_table")
            table_runtime = runtime.get(rev_id, {}).get("drop_tables", {}).get(table, {})
            columns = [[name, typ] for name, typ in metadata["tables"][table]]
            self._insert_table(schema, table, columns, table_runtime.get("index"))
        elif kind == "restore_table":
            return
        elif kind == "add_column":
            _kind, table, name, _typ = parsed
            columns = self._table_columns(schema, table)
            index = self._column_index(columns, name)
            if index is None:
                raise MigrationError("missing column")
            del columns[index]
        elif kind == "drop_column":
            _kind, table, name = parsed
            columns = self._table_columns(schema, table)
            if self._column_index(columns, name) is not None:
                raise MigrationError("column already exists")
            key = (table, name)
            if key not in metadata["columns"]:
                raise MigrationError("irreversible drop_column")
            column_runtime = runtime.get(rev_id, {}).get("drop_columns", {}).get(key, {})
            restored = [name, metadata["columns"][key]]
            index = column_runtime.get("index")
            if index is None or index > len(columns):
                columns.append(restored)
            else:
                columns.insert(index, restored)
        elif kind == "restore_column":
            return
        elif kind == "rename_table":
            _kind, old, new = parsed
            self._rename_table(schema, new, old)

    def _table_columns(self, schema, table):
        if table not in schema:
            raise MigrationError("missing table")
        return schema[table]

    def _column_index(self, columns, name):
        for index, column in enumerate(columns):
            if column[0] == name:
                return index
        return None

    def _rename_table(self, schema, old, new):
        if old not in schema:
            raise MigrationError("missing table")
        if new in schema:
            raise MigrationError("table already exists")
        renamed = {}
        for table, columns in schema.items():
            renamed[new if table == old else table] = columns
        schema.clear()
        schema.update(renamed)

    def _insert_table(self, schema, table, columns, index):
        items = list(schema.items())
        if index is None or index > len(items):
            index = len(items)
        items.insert(index, (table, columns))
        schema.clear()
        schema.update(items)

    def _heads_for_applied(self, applied):
        applied = set(applied)
        if not applied:
            return {"base"}
        heads = set()
        for rev_id in applied:
            if not (self._nodes[rev_id]["children"] & applied):
                heads.add(rev_id)
        return heads or {"base"}

    def _public_current(self, current):
        current = set(current)
        if not current or current == {"base"}:
            return ["base"]
        return sorted(current)

    def _copy_schema(self, schema):
        return {table: [list(column) for column in columns] for table, columns in schema.items()}


class _InjectedFailure(Exception):
    pass
