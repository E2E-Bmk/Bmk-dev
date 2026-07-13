from __future__ import annotations

import argparse
import json

from .api import WorkflowEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="torkworkflow")
    parser.add_argument("--store", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("submit").add_argument("file")
    sub.add_parser("run-until-idle")
    sub.add_parser("jobs")
    job = sub.add_parser("job")
    job.add_argument("job_id")
    task = sub.add_parser("task")
    task.add_argument("task_id")
    logs = sub.add_parser("logs")
    logs.add_argument("--job-id", default=None)
    logs.add_argument("--task-id", default=None)
    logs.add_argument("--contains", default=None)
    progress = sub.add_parser("progress")
    progress.add_argument("job_id")
    cancel = sub.add_parser("cancel")
    cancel.add_argument("job_id")
    restart = sub.add_parser("restart")
    restart.add_argument("job_id")
    sub.add_parser("queue")
    sub.add_parser("recover")
    tick = sub.add_parser("tick")
    tick.add_argument("--seconds", type=int, default=0)
    sched = sub.add_parser("schedule")
    sched.add_argument("name")
    sched.add_argument("file")
    sched.add_argument("--interval-seconds", type=int, required=True)
    sub.add_parser("schedules")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    engine = WorkflowEngine(args.store)

    if args.command == "submit":
        result = engine.submit(open(args.file, "r", encoding="utf-8").read())
    elif args.command == "run-until-idle":
        result = engine.run_until_idle()
    elif args.command == "jobs":
        result = engine.list_jobs()
    elif args.command == "job":
        result = engine.get_job(args.job_id)
    elif args.command == "task":
        result = engine.get_task(args.task_id)
    elif args.command == "logs":
        result = engine.log_page(job_id=args.job_id, task_id=args.task_id, contains=args.contains)
    elif args.command == "progress":
        result = engine.progress(args.job_id)
    elif args.command == "cancel":
        result = engine.cancel(args.job_id)
    elif args.command == "restart":
        result = engine.restart(args.job_id)
    elif args.command == "queue":
        result = engine.queue_status()
    elif args.command == "recover":
        result = engine.recover()
    elif args.command == "tick":
        result = engine.tick(seconds=args.seconds)
    elif args.command == "schedule":
        result = engine.register_schedule(args.name, open(args.file, "r", encoding="utf-8").read(), interval_seconds=args.interval_seconds)
    elif args.command == "schedules":
        result = engine.schedules()
    else:  # pragma: no cover
        parser.error(f"unknown command {args.command}")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
