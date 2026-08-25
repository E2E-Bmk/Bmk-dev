#!/usr/bin/env python3
"""Run one public build in a fresh interpreter for System roots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import traceback


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.candidate_root.resolve()))
    try:
        from mkdocs.commands.build import build
        from mkdocs.config import load_config

        config = load_config(config_file=str(args.config.resolve()))
        build(config)
        record = {"ok": True}
        code = 0
    except BaseException as exc:
        record = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error_module": type(exc).__module__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        code = 3
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

