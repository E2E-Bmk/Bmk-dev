from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .api import JobLedger
from .models import JobLedgerError


def _json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    data = json.loads(value)
    if not isinstance(data, dict):
        raise JobLedgerError("JSON argument must be an object")
    return data


def _print(data: object) -> None:
    print(json.dumps(data, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobledger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("path")
    enqueue.add_argument("--kind", required=True)
    enqueue.add_argument("--args")
    enqueue.add_argument("--queue", default="default")
    enqueue.add_argument("--priority", type=int, default=0)
    enqueue.add_argument("--scheduled-at")
    enqueue.add_argument("--now")

    claim = sub.add_parser("claim")
    claim.add_argument("path")
    claim.add_argument("--queue", default="default")
    claim.add_argument("--worker", default="worker")
    claim.add_argument("--limit", type=int, default=1)
    claim.add_argument("--now")

    for name in ("jobs", "queue-report", "metrics", "events", "recover", "export"):
        p = sub.add_parser(name)
        p.add_argument("path")

    complete = sub.add_parser("complete")
    complete.add_argument("path")
    complete.add_argument("job_id")
    complete.add_argument("--now")

    fail = sub.add_parser("fail")
    fail.add_argument("path")
    fail.add_argument("job_id")
    fail.add_argument("--error", required=True)
    fail.add_argument("--now")

    cron_set = sub.add_parser("cron-set")
    cron_set.add_argument("path")
    cron_set.add_argument("name")
    cron_set.add_argument("--every", type=int, required=True)
    cron_set.add_argument("--kind", required=True)
    cron_set.add_argument("--args")
    cron_set.add_argument("--queue", default="default")

    tick = sub.add_parser("tick")
    tick.add_argument("path")
    tick.add_argument("--now", required=True)

    args = parser.parse_args(argv)
    try:
        ledger = JobLedger(args.path)
        if args.cmd == "enqueue":
            _print(ledger.enqueue(args.kind, _json(args.args), queue=args.queue, priority=args.priority, scheduled_at=args.scheduled_at, now=args.now))
        elif args.cmd == "claim":
            _print(ledger.claim(args.queue, worker=args.worker, limit=args.limit, now=args.now))
        elif args.cmd == "complete":
            _print(ledger.complete(args.job_id, now=args.now))
        elif args.cmd == "fail":
            _print(ledger.fail(args.job_id, args.error, now=args.now))
        elif args.cmd == "jobs":
            _print(ledger.jobs())
        elif args.cmd == "queue-report":
            _print(ledger.queue_report())
        elif args.cmd == "metrics":
            _print(ledger.metrics())
        elif args.cmd == "events":
            _print(ledger.events())
        elif args.cmd == "recover":
            _print(ledger.recover())
        elif args.cmd == "export":
            _print(ledger.export_state())
        elif args.cmd == "cron-set":
            _print(ledger.configure_cron(args.name, args.every, args.kind, _json(args.args), queue=args.queue))
        elif args.cmd == "tick":
            _print(ledger.tick(args.now))
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
