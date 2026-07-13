"""JSON CLI for FlowLedger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .api import FlowLedger
from .models import FlowLedgerError


def _json_arg(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
    return json.loads(value)


def _input_payload(args) -> Any:
    if getattr(args, "file", None):
        return Path(args.file).read_text(encoding="utf-8")
    raw = sys.stdin.buffer.read()
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode(errors="replace")
    text = text.lstrip("\ufeff")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flowledger")
    parser.add_argument("--store")
    parser.add_argument("--now")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--store", dest="store_override")
        p.add_argument("--now", dest="now_override")

    add_common(sub.add_parser("init"))
    p = sub.add_parser("put-spec")
    add_common(p)
    p.add_argument("--file")
    p = sub.add_parser("tick")
    add_common(p)
    p = sub.add_parser("start")
    add_common(p)
    p.add_argument("workflow", nargs="?")
    p.add_argument("--workflow", dest="workflow_opt")
    p.add_argument("--params")
    p = sub.add_parser("claim")
    add_common(p)
    p.add_argument("queue", nargs="?")
    p.add_argument("worker_id", nargs="?")
    p.add_argument("--queue", dest="queue_opt")
    p.add_argument("--worker-id", dest="worker_id_opt")
    p.add_argument("--lease-seconds", type=int, default=60)
    p = sub.add_parser("complete")
    add_common(p)
    p.add_argument("item_id", nargs="?")
    p.add_argument("worker_id", nargs="?")
    p.add_argument("--item-id", dest="item_id_opt")
    p.add_argument("--worker-id", dest="worker_id_opt")
    p.add_argument("--output")
    p = sub.add_parser("fail")
    add_common(p)
    p.add_argument("item_id", nargs="?")
    p.add_argument("worker_id", nargs="?")
    p.add_argument("--item-id", dest="item_id_opt")
    p.add_argument("--worker-id", dest="worker_id_opt")
    p.add_argument("--error")
    p = sub.add_parser("cancel")
    add_common(p)
    p.add_argument("run_id", nargs="?")
    p.add_argument("--run-id", dest="run_id_opt")
    p = sub.add_parser("status")
    add_common(p)
    p.add_argument("--workflow")
    p.add_argument("--run-id")
    p = sub.add_parser("history")
    add_common(p)
    p.add_argument("--workflow")
    add_common(sub.add_parser("queue"))
    p = sub.add_parser("next-runs")
    add_common(p)
    p = sub.add_parser("logs")
    add_common(p)
    p.add_argument("--run-id")
    p = sub.add_parser("events")
    add_common(p)
    p.add_argument("--run-id")
    p = sub.add_parser("recover")
    add_common(p)
    add_common(sub.add_parser("export"))
    p = sub.add_parser("import")
    add_common(p)
    p.add_argument("--file")
    return parser

def main(argv: list[str] | None = None) -> int:
    """Run the JSON CLI."""
    parser = _parser()
    args = parser.parse_args(argv)
    store_path = getattr(args, "store_override", None) or getattr(args, "store", None)
    if store_path is None:
        parser.error("--store is required")
    ledger = FlowLedger(store_path)
    try:
        now = getattr(args, "now_override", None) or getattr(args, "now", None)
        command = args.command
        if command == "init":
            result = ledger.init()
        elif command == "put-spec":
            result = ledger.put_spec(_input_payload(args))
        elif command == "tick":
            result = ledger.tick(now)
        elif command == "start":
            workflow = args.workflow_opt or args.workflow
            result = ledger.start(workflow, now, _json_arg(args.params, None))
        elif command == "claim":
            result = ledger.claim(args.queue_opt or args.queue or "default", args.worker_id_opt or args.worker_id, now, args.lease_seconds)
        elif command == "complete":
            result = ledger.complete(args.item_id_opt or args.item_id, args.worker_id_opt or args.worker_id, now, _json_arg(args.output, None))
        elif command == "fail":
            result = ledger.fail(args.item_id_opt or args.item_id, args.worker_id_opt or args.worker_id, now, _json_arg(args.error, {"error": "failed", "message": "failed", "details": {}}))
        elif command == "cancel":
            result = ledger.cancel(args.run_id_opt or args.run_id, now)
        elif command == "status":
            result = ledger.status(args.workflow, args.run_id)
        elif command == "history":
            result = ledger.history(args.workflow)
        elif command == "queue":
            result = ledger.queue()
        elif command == "next-runs":
            result = ledger.next_runs(now)
        elif command == "logs":
            result = ledger.logs(args.run_id)
        elif command == "events":
            result = ledger.events(args.run_id)
        elif command == "recover":
            result = ledger.recover(now)
        elif command == "export":
            result = ledger.export()
        elif command == "import":
            result = ledger.import_snapshot(_input_payload(args))
        else:
            parser.error(f"unknown command {command}")
    except FlowLedgerError as exc:
        print(json.dumps(exc.to_dict(), sort_keys=True))
        return 1
    except Exception as exc:
        print(json.dumps({"error": "internal_error", "message": str(exc), "details": {}}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
