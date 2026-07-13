from __future__ import annotations

import argparse
import json

from .api import QueueLedger


def main() -> int:
    parser = argparse.ArgumentParser(prog="queueledger")
    parser.add_argument("--store", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    enqueue = sub.add_parser("enqueue")
    enqueue.add_argument("entrypoint")
    enqueue.add_argument("payload")
    enqueue.add_argument("--now", type=float, default=0.0)
    sub.add_parser("report")
    args = parser.parse_args()

    ledger = QueueLedger.file(args.store)
    if args.command == "enqueue":
        job = ledger.enqueue(args.entrypoint, args.payload.encode(), now=args.now)
        print(json.dumps({"id": job.id, "status": job.status.value}, sort_keys=True))
    elif args.command == "report":
        report = ledger.queue_report()
        print(json.dumps({"queued": report.queued, "picked": report.picked, "terminal": report.terminal, "by_entrypoint": report.by_entrypoint}, sort_keys=True))
    return 0
