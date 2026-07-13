import copy
import re


class MigrationError(Exception):
    pass


_REV_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _sorted_current(values):
    return sorted(v for v in values if v != "base")


def _parse_cols(parts):
    cols = []
    for part in parts:
        if ":" not in part:
            raise MigrationError("bad column")
        name, typ = part.split(":", 1)
        if not name or not typ:
            raise MigrationError("bad column")
        cols.append([name, typ])
    return cols


class MiniMigrationManager:
    def __init__(self, root=None):
        self.root = root
        self.revisions = {}
        self.children = {}
        self.current_set = set()
        self.tables = {}
        self.ledger_entries = []
        self.pending = None

    def revision(self, rev_id, parents=None, ops=None, message=""):
        self._ensure_mutable()
        self._validate_rev_id(rev_id)
        if rev_id in self.revisions:
            raise MigrationError("duplicate revision")
        parent_list = list(parents or ["base"])
        if not parent_list:
            parent_list = ["base"]
        for parent in parent_list:
            if parent != "base" and parent not in self.revisions:
                raise MigrationError("unknown parent")
            if parent == rev_id:
                raise MigrationError("cycle")
        op_list = list(ops or [])
        for op in op_list:
            self._parse_op(op)
        self.revisions[rev_id] = {
            "id": rev_id,
            "parents": sorted(parent_list),
            "ops": op_list,
            "message": message,
        }
        self.children.setdefault(rev_id, set())
        for parent in parent_list:
            self.children.setdefault(parent, set()).add(rev_id)
        return self._node(rev_id)

    def merge(self, rev_id, parents, message=""):
        if not parents or len(parents) < 2:
            raise MigrationError("merge needs parents")
        return self.revision(rev_id, parents=list(parents), ops=[], message=message)

    def history(self):
        return [self._node(rev_id) for rev_id in self._topological_order()]

    def heads(self):
        heads = [rev for rev in self.revisions if not self.children.get(rev)]
        return sorted(heads)

    def current(self):
        return {
            "revisions": _sorted_current(self.current_set),
            "pending": copy.deepcopy(self.pending),
        }

    def schema(self):
        return {"tables": copy.deepcopy(self.tables)}

    def ledger(self):
        return {"entries": copy.deepcopy(self.ledger_entries)}

    def plan(self, direction, target):
        if direction == "upgrade":
            return [
                {"direction": "upgrade", "revision": rev, "ops": list(self.revisions[rev]["ops"])}
                for rev in self._upgrade_order(target)
            ]
        if direction == "downgrade":
            return [
                {"direction": "downgrade", "revision": rev, "ops": self._reverse_ops(rev)}
                for rev in self._downgrade_order(target)
            ]
        raise MigrationError("bad direction")

    def upgrade(self, target, fail_at=None):
        self._ensure_mutable()
        order = self._upgrade_order(target)
        before = self._snapshot()
        try:
            for rev in order:
                self._apply_revision(rev)
                after_current = self._current_after_apply(rev)
                self.ledger_entries.append(
                    {
                        "kind": "apply",
                        "revision": rev,
                        "before_current": _sorted_current(self.current_set),
                        "after_current": _sorted_current(after_current),
                    }
                )
                self.current_set = after_current
            if fail_at in {"after_schema", "after_ledger"}:
                raise MigrationError("injected failure")
            if fail_at is not None:
                raise MigrationError("bad fail_at")
            return self.current()
        except Exception:
            if fail_at in {"after_schema", "after_ledger"}:
                self._restore(before)
                self.pending = {
                    "operation": "upgrade",
                    "target": target,
                    "fail_at": fail_at,
                }
            raise

    def downgrade(self, target, fail_at=None):
        self._ensure_mutable()
        order = self._downgrade_order(target)
        before = self._snapshot()
        try:
            reverse_map = {rev: self._reverse_ops(rev) for rev in order}
            for rev in order:
                before_current = _sorted_current(self.current_set)
                for op in reverse_map[rev]:
                    self._apply_op(op)
                self.current_set = self._current_after_downgrade(rev)
                self.ledger_entries.append(
                    {
                        "kind": "downgrade",
                        "revision": rev,
                        "before_current": before_current,
                        "after_current": _sorted_current(self.current_set),
                    }
                )
            if fail_at in {"after_schema", "after_ledger"}:
                raise MigrationError("injected failure")
            if fail_at is not None:
                raise MigrationError("bad fail_at")
            return self.current()
        except Exception:
            if fail_at in {"after_schema", "after_ledger"}:
                self._restore(before)
                self.pending = {
                    "operation": "downgrade",
                    "target": target,
                    "fail_at": fail_at,
                }
            raise

    def stamp(self, target):
        self._ensure_mutable()
        target_set = self._target_set(target)
        before = _sorted_current(self.current_set)
        self.current_set = set(target_set)
        self.ledger_entries.append(
            {
                "kind": "stamp",
                "revision": target if isinstance(target, str) else ",".join(_sorted_current(target_set)),
                "before_current": before,
                "after_current": _sorted_current(self.current_set),
            }
        )
        return self.current()

    def recover(self):
        before = _sorted_current(self.current_set)
        if self.pending is None:
            return {"status": "no_pending", "before_current": before, "after_current": before}
        self.pending = None
        after = _sorted_current(self.current_set)
        self.ledger_entries.append(
            {
                "kind": "recover",
                "revision": None,
                "before_current": before,
                "after_current": after,
            }
        )
        return {"status": "rolled_back", "before_current": before, "after_current": after}

    def _ensure_mutable(self):
        if self.pending is not None:
            raise MigrationError("pending recovery")

    def _validate_rev_id(self, rev_id):
        if not isinstance(rev_id, str) or not _REV_RE.match(rev_id):
            raise MigrationError("bad revision id")

    def _node(self, rev_id):
        rev = self.revisions[rev_id]
        return {
            "id": rev_id,
            "parents": sorted(rev["parents"]),
            "children": sorted(self.children.get(rev_id, set())),
            "message": rev.get("message", ""),
            "ops": list(rev["ops"]),
        }

    def _topological_order(self):
        seen = set()
        order = []

        def visit(rev_id):
            if rev_id in seen or rev_id == "base":
                return
            for parent in self.revisions[rev_id]["parents"]:
                visit(parent)
            seen.add(rev_id)
            order.append(rev_id)

        for rev_id in sorted(self.revisions):
            visit(rev_id)
        return order

    def _ancestors(self, rev_id):
        if rev_id == "base":
            return set()
        out = {rev_id}
        for parent in self.revisions[rev_id]["parents"]:
            out.update(self._ancestors(parent))
        return out

    def _target_set(self, target):
        if target == "base":
            return set()
        if target == "current":
            return set(self.current_set)
        if target == "heads":
            return set(self.heads())
        if isinstance(target, str) and target in self.revisions:
            return {target}
        if isinstance(target, (list, tuple, set)):
            for rev in target:
                if rev not in self.revisions:
                    raise MigrationError("unknown target")
            return set(target)
        raise MigrationError("unknown target")

    def _upgrade_order(self, target):
        targets = self._target_set(target)
        needed = set()
        for rev in targets:
            needed.update(self._ancestors(rev))
        applied = set()
        for rev in self.current_set:
            applied.update(self._ancestors(rev))
        missing = needed - applied
        return [rev for rev in self._topological_order() if rev in missing]

    def _downgrade_order(self, target):
        if target == "heads":
            raise MigrationError("bad downgrade target")
        targets = self._target_set(target)
        keep = set()
        for rev in targets:
            keep.update(self._ancestors(rev))
        applied = set()
        for rev in self.current_set:
            applied.update(self._ancestors(rev))
        remove = applied - keep
        return [rev for rev in reversed(self._topological_order()) if rev in remove]

    def _current_after_apply(self, rev):
        new = set(self.current_set)
        for parent in self.revisions[rev]["parents"]:
            new.discard(parent)
        new.add(rev)
        return new

    def _current_after_downgrade(self, rev):
        new = set(self.current_set)
        new.discard(rev)
        for parent in self.revisions[rev]["parents"]:
            if parent != "base":
                new.add(parent)
        return new

    def _parse_op(self, op):
        parts = op.split()
        if not parts:
            raise MigrationError("empty op")
        verb = parts[0]
        if verb in {"create_table", "restore_table"}:
            if len(parts) < 3:
                raise MigrationError("bad table op")
            _parse_cols(parts[2:])
        elif verb == "drop_table":
            if len(parts) != 2:
                raise MigrationError("bad drop_table")
        elif verb in {"add_column", "restore_column"}:
            if len(parts) != 3:
                raise MigrationError("bad column op")
            _parse_cols([parts[2]])
        elif verb == "drop_column":
            if len(parts) != 3:
                raise MigrationError("bad drop_column")
        elif verb == "rename_table":
            if len(parts) != 3:
                raise MigrationError("bad rename_table")
        else:
            raise MigrationError("unknown op")
        return parts

    def _apply_revision(self, rev):
        for op in self.revisions[rev]["ops"]:
            if op.split()[0] not in {"restore_table", "restore_column"}:
                self._apply_op(op)

    def _apply_op(self, op):
        parts = self._parse_op(op)
        verb = parts[0]
        if verb in {"create_table", "restore_table"}:
            name = parts[1]
            if name in self.tables:
                raise MigrationError("table exists")
            self.tables[name] = _parse_cols(parts[2:])
        elif verb == "drop_table":
            name = parts[1]
            if name not in self.tables:
                raise MigrationError("missing table")
            del self.tables[name]
        elif verb in {"add_column", "restore_column"}:
            table = parts[1]
            if table not in self.tables:
                raise MigrationError("missing table")
            col = _parse_cols([parts[2]])[0]
            if any(existing[0] == col[0] for existing in self.tables[table]):
                raise MigrationError("column exists")
            self.tables[table].append(col)
        elif verb == "drop_column":
            table, col = parts[1], parts[2]
            if table not in self.tables:
                raise MigrationError("missing table")
            old = list(self.tables[table])
            self.tables[table] = [item for item in old if item[0] != col]
            if len(old) == len(self.tables[table]):
                raise MigrationError("missing column")
        elif verb == "rename_table":
            old, new = parts[1], parts[2]
            if old not in self.tables or new in self.tables:
                raise MigrationError("bad rename")
            self.tables[new] = self.tables.pop(old)

    def _reverse_ops(self, rev):
        ops = self.revisions[rev]["ops"]
        restore_tables = {}
        restore_columns = {}
        for op in ops:
            parts = op.split()
            if parts and parts[0] == "restore_table":
                restore_tables[parts[1]] = op
            elif parts and parts[0] == "restore_column":
                restore_columns[(parts[1], parts[2].split(":", 1)[0])] = op
        reversed_ops = []
        for op in reversed(ops):
            parts = op.split()
            if not parts:
                continue
            verb = parts[0]
            if verb == "create_table":
                reversed_ops.append(f"drop_table {parts[1]}")
            elif verb == "drop_table":
                if parts[1] not in restore_tables:
                    raise MigrationError("irreversible drop_table")
                reversed_ops.append(restore_tables[parts[1]])
            elif verb == "add_column":
                reversed_ops.append(f"drop_column {parts[1]} {parts[2].split(':', 1)[0]}")
            elif verb == "drop_column":
                key = (parts[1], parts[2])
                if key not in restore_columns:
                    raise MigrationError("irreversible drop_column")
                reversed_ops.append(restore_columns[key])
            elif verb == "rename_table":
                reversed_ops.append(f"rename_table {parts[2]} {parts[1]}")
            elif verb in {"restore_table", "restore_column"}:
                continue
        return reversed_ops

    def _snapshot(self):
        return {
            "current_set": set(self.current_set),
            "tables": copy.deepcopy(self.tables),
            "ledger_entries": copy.deepcopy(self.ledger_entries),
            "pending": copy.deepcopy(self.pending),
        }

    def _restore(self, snap):
        self.current_set = set(snap["current_set"])
        self.tables = copy.deepcopy(snap["tables"])
        self.ledger_entries = copy.deepcopy(snap["ledger_entries"])
        self.pending = copy.deepcopy(snap["pending"])
