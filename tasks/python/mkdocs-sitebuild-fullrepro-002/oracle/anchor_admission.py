#!/usr/bin/env python3
"""Issue one authenticated admission seal for an arbitrary anchor candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import traceback

from anchor_protocol import AdmissionError, issue_admission, write_admission


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        record = issue_admission(args.candidate_root, args.candidate_id)
        write_admission(args.output, record)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    except BaseException as exc:
        record = {
            "valid": False,
            "classification": "invalid-anchor-admission",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
