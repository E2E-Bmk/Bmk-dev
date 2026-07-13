from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="torkworkflow")
    parser.add_argument("--store", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("submit").add_argument("file")
    sub.add_parser("run-until-idle")
    sub.add_parser("jobs")
    job = sub.add_parser("job")
    job.add_argument("job_id")
    cancel = sub.add_parser("cancel")
    cancel.add_argument("job_id")
    restart = sub.add_parser("restart")
    restart.add_argument("job_id")
    sub.add_parser("queue")
    sub.add_parser("recover")
    return parser


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError
