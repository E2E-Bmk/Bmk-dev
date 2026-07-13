from __future__ import annotations

import argparse
import json
import sys

from .admin import EdgeGate
from .models import EdgeGateError


def _print(value) -> None:
    print(json.dumps(value, sort_keys=True))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="edgegate")
    parser.add_argument("--state", required=True)
    sub = parser.add_subparsers(dest="cmd", required=True)
    apply_p = sub.add_parser("apply")
    apply_p.add_argument("document")
    get_p = sub.add_parser("get")
    get_p.add_argument("kind")
    get_p.add_argument("id", nargs="?")
    sim_p = sub.add_parser("simulate")
    sim_p.add_argument("method")
    sim_p.add_argument("host")
    sim_p.add_argument("path")
    report_p = sub.add_parser("report")
    report_p.add_argument("name", choices=["config", "reference", "runtime", "audit"])
    args = parser.parse_args(argv)
    gate = EdgeGate(args.state)
    try:
        if args.cmd == "apply":
            with open(args.document, "r", encoding="utf-8") as handle:
                _print(gate.load_standalone(json.load(handle)))
        elif args.cmd == "get":
            _print(gate.get(args.kind, args.id) if args.id else gate.list(args.kind))
        elif args.cmd == "simulate":
            _print(gate.simulate_request(args.method, args.host, args.path))
        elif args.cmd == "report":
            if args.name == "config":
                _print(gate.config_report())
            elif args.name == "reference":
                _print(gate.reference_report())
            elif args.name == "runtime":
                _print(gate.runtime_report())
            elif args.name == "audit":
                _print(gate.audit_report(include_deleted=True))
    except EdgeGateError as exc:
        _print({"error": exc.code})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
