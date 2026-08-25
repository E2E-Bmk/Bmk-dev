#!/usr/bin/env python3
"""Exercise v14 anchor admission without creating a source-blank anchor."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
from typing import Any


GATE = Path(__file__).resolve().parent


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def run(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env.update({
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "0",
        "PIP_NO_INDEX": "1",
    })
    return subprocess.run(
        [sys.executable, "-s", "-X", "utf8", "-B", *arguments],
        cwd=GATE,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=900,
        check=False,
    )


def issue(candidate: Path, candidate_id: str, output: Path) -> subprocess.CompletedProcess[bytes]:
    return run([
        str(GATE / "anchor_admission.py"),
        "--candidate-root", str(candidate),
        "--candidate-id", candidate_id,
        "--output", str(output),
    ])


def score(candidate: Path, seal: Path, output: Path) -> subprocess.CompletedProcess[bytes]:
    return run([
        str(GATE / "score_gate.py"),
        "--mode", "anchor",
        "--candidate-root", str(candidate),
        "--candidate-seal", str(seal),
        "--output", str(output),
    ])


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def execute() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mkdocs-v14-admission-control-") as temporary:
        root = Path(temporary)

        good = root / "arbitrary-good"
        shutil.copytree(GATE / "dummy", good)
        good_seal = root / "good.seal.json"
        admitted = issue(good, "control-valid", good_seal)
        require(admitted.returncode == 0 and good_seal.exists(), "valid arbitrary control was not admitted")
        good_score = root / "good.score.json"
        scored = score(good, good_seal, good_score)
        require(scored.returncode == 0 and good_score.exists(), "valid arbitrary control did not score")
        good_record = read(good_score)
        require(good_record.get("valid") is True and good_record.get("mode") == "anchor", "anchor scorer record invalid")
        require(sum(good_record["stable_vector"].values()) == 0, "behavior-empty admission control unexpectedly passed")
        require(len(good_record["rounds"]) == 9, "anchor control did not run the full order-round matrix")
        require(all(set(item["phases"].values()) == {"semantic-call"} for item in good_record["rounds"]), "anchor control missed semantic-call phase")

        missing = root / "missing-required-source"
        shutil.copytree(GATE / "dummy", missing)
        (missing / "mkdocs" / "commands" / "build.py").unlink()
        missing_seal = root / "missing.seal.json"
        missing_run = issue(missing, "control-missing", missing_seal)
        require(missing_run.returncode == 2 and not missing_seal.exists(), "missing source was admitted")

        changed = root / "post-seal-change"
        shutil.copytree(GATE / "dummy", changed)
        changed_seal = root / "changed.seal.json"
        require(issue(changed, "control-changed", changed_seal).returncode == 0, "change control admission failed")
        with (changed / "mkdocs" / "__init__.py").open("ab") as stream:
            stream.write(b"\n# changed after seal\n")
        changed_score = root / "changed.score.json"
        changed_run = score(changed, changed_seal, changed_score)
        changed_record = read(changed_score)
        require(changed_run.returncode == 2 and changed_record.get("valid") is False, "post-seal mutation was scored")

        broken = root / "broken-public-call"
        shutil.copytree(GATE / "dummy", broken)
        (broken / "mkdocs" / "config" / "__init__.py").write_text(
            "def load_config(config_file=None, **kwargs):\n    return object()\n",
            encoding="utf-8",
            newline="\n",
        )
        broken_seal = root / "broken.seal.json"
        require(issue(broken, "control-broken-call", broken_seal).returncode == 0, "broken-call structure could not be sealed")
        broken_score = root / "broken.score.json"
        broken_run = score(broken, broken_seal, broken_score)
        broken_record = read(broken_score)
        require(broken_run.returncode == 2 and broken_record.get("valid") is False, "broken public call was scored")

        keyerror = root / "public-keyerror"
        shutil.copytree(GATE / "dummy", keyerror)
        (keyerror / "mkdocs" / "config" / "__init__.py").write_text(
            "def load_config(config_file=None, **kwargs):\n    raise KeyError('public config lookup')\n",
            encoding="utf-8",
            newline="\n",
        )
        keyerror_seal = root / "keyerror.seal.json"
        require(issue(keyerror, "control-public-keyerror", keyerror_seal).returncode == 0, "public-KeyError control admission failed")
        keyerror_score = root / "keyerror.score.json"
        keyerror_run = score(keyerror, keyerror_seal, keyerror_score)
        keyerror_record = read(keyerror_score)
        require(keyerror_run.returncode == 0 and keyerror_record.get("valid") is True, "public product KeyError did not remain scoreable")
        require(sum(keyerror_record["stable_vector"].values()) == 0, "public-KeyError control unexpectedly passed")
        require(all(set(item["classifications"].values()) <= {"semantic-mismatch"} for item in keyerror_record["rounds"]), "public product KeyError escaped semantic classification")

        provenance = good_record["provenance"]
        phase_values = sorted({value for item in good_record["rounds"] for value in item["phases"].values()})
        classification_values = sorted({value for item in good_record["rounds"] for value in item["classifications"].values()})
        return {
            "schema_version": 1,
            "suite": "mkdocs-v14-formal-a",
            "valid": True,
            "kind": "non-anchor-arbitrary-candidate-admission-control",
            "anchors_started": False,
            "positive": {
                "candidate_id": provenance["candidate_id"],
                "candidate_tree": provenance["candidate_tree"],
                "candidate_payload": provenance["candidate_payload"],
                "evaluator_protocol": provenance["evaluator_protocol"],
                "orders": list(good_record["orders"]),
                "rounds": len(good_record["rounds"]),
                "fresh_process_per_root": good_record["fresh_process_per_root"],
                "passed": sum(good_record["stable_vector"].values()),
                "total": len(good_record["stable_vector"]),
                "scores": good_record["scores"],
                "phases": phase_values,
                "classifications": classification_values,
            },
            "negative": {
                "missing_required_source_rejected_at_admission": True,
                "post_seal_tree_change_invalidated_before_collection": True,
                "broken_public_call_structure_invalidated": True,
                "public_product_keyerror_scored_semantic": True,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "output already exists")
        record = execute()
        code = 0
    except BaseException as exc:
        record = {
            "schema_version": 1,
            "suite": "mkdocs-v14-formal-a",
            "valid": False,
            "classification": "invalid-anchor-admission-control",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
