"""Frozen sealed-admission protocol for arbitrary source-blank candidates."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


GATE = Path(__file__).resolve().parent
CONFIG = json.loads((GATE / "SCORER-CONFIG.json").read_text(encoding="utf-8"))
PROTOCOL_FILES = (
    "SCORER-CONFIG.json",
    "ROOT-MAP.json",
    "probe_root.py",
    "scenario_driver.py",
    "score_gate.py",
    "anchor_protocol.py",
    "anchor_admission.py",
    "ANCHOR-ADMISSION-PROTOCOL.md",
    "ANCHOR-SEAL-KEY.txt",
    "audit_public_operations.py",
    "PUBLIC-OPERATION-CONTRACT.json",
    "audit_record_shapes.py",
    "RECORD-SHAPE-CONTRACT.json",
)


class AdmissionError(RuntimeError):
    """The candidate cannot be admitted to anchor scoring."""


def require(value: bool, message: str) -> None:
    if not value:
        raise AdmissionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(files: dict[str, str]) -> str:
    payload = "".join(f"{name}\t{digest}\n" for name, digest in sorted(files.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _snapshot(files: dict[str, str]) -> dict[str, Any]:
    return {
        "files": dict(sorted(files.items())),
        "file_count": len(files),
        "aggregate_sha256": aggregate(files),
    }


def candidate_tree_snapshot(root: Path, *, strict: bool) -> dict[str, Any]:
    root = root.resolve()
    require(root.is_dir() and not root.is_symlink(), "candidate root missing or symlinked")
    excluded = set(CONFIG["protocol"]["candidate_excluded_names"])
    files: dict[str, str] = {}
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in dirs:
            child = current_path / name
            require(not child.is_symlink(), f"directory symlink under candidate: {child}")
            if strict:
                require(name not in excluded, f"forbidden generated directory under candidate: {child}")
        dirs[:] = sorted(name for name in dirs if name not in excluded)
        for name in sorted(names):
            path = current_path / name
            require(path.is_file() and not path.is_symlink(), f"unsafe candidate file: {path}")
            relative = path.relative_to(root).as_posix()
            require(not strict or name not in excluded, f"forbidden generated file: {relative}")
            files[relative] = sha256(path)
    if strict:
        for relative in CONFIG["protocol"]["anchor_required_files"]:
            require(relative in files, f"missing required candidate source: {relative}")
    return _snapshot(files)


def payload_snapshot() -> dict[str, Any]:
    files: dict[str, str] = {}
    for relative in CONFIG["candidate_payload"]:
        path = GATE / "candidate-payload" / relative
        require(path.is_file() and not path.is_symlink(), f"missing candidate payload: {relative}")
        path.read_bytes().decode("utf-8", "strict")
        files[relative] = sha256(path)
    return _snapshot(files)


def protocol_snapshot() -> dict[str, Any]:
    files: dict[str, str] = {}
    for relative in PROTOCOL_FILES:
        path = GATE / relative
        require(path.is_file() and not path.is_symlink(), f"missing anchor protocol file: {relative}")
        path.read_bytes().decode("utf-8", "strict")
        files[relative] = sha256(path)
    return _snapshot(files)


def validate_candidate_root(root: Path) -> Path:
    root = root.resolve()
    require(root.is_dir() and not root.is_symlink(), "candidate root missing or symlinked")
    reference = (GATE / CONFIG["reference"]["source_root"]).resolve()
    dummy = (GATE / "dummy").resolve()
    require(root != reference, "reference source cannot be admitted as an anchor")
    require(root != dummy, "dummy control cannot be admitted in place")
    require(not root.is_relative_to(GATE), "gate-contained source cannot be admitted as an anchor")
    return root


def _key() -> bytes:
    raw = (GATE / "ANCHOR-SEAL-KEY.txt").read_text(encoding="ascii").strip()
    require(bool(re.fullmatch(r"[0-9a-f]{64}", raw)), "invalid anchor seal key")
    return bytes.fromhex(raw)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def issue_admission(candidate_root: Path, candidate_id: str) -> dict[str, Any]:
    require(bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", candidate_id)), "invalid candidate identity")
    root = validate_candidate_root(candidate_root)
    body = {
        "schema_version": 1,
        "suite": CONFIG["suite"],
        "kind": CONFIG["protocol"]["anchor_mode"],
        "seal_domain": CONFIG["protocol"]["seal_domain"],
        "candidate_id": candidate_id,
        "candidate_root": str(root),
        "candidate_tree": candidate_tree_snapshot(root, strict=True),
        "candidate_payload": payload_snapshot(),
        "evaluator_protocol": protocol_snapshot(),
    }
    seal = hmac.new(_key(), _canonical(body), hashlib.sha256).hexdigest()
    return {"body": body, "seal": seal}


def write_admission(path: Path, record: dict[str, Any]) -> None:
    path = path.resolve()
    require(not path.exists(), "admission output already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def verify_admission(path: Path, candidate_root: Path) -> dict[str, Any]:
    path = path.resolve()
    require(path.is_file() and not path.is_symlink(), "anchor admission seal missing or unsafe")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise AdmissionError("anchor admission seal is not valid JSON") from exc
    require(isinstance(record, dict) and set(record) == {"body", "seal"}, "invalid admission envelope")
    body, seal = record["body"], record["seal"]
    require(isinstance(body, dict) and isinstance(seal, str), "invalid admission fields")
    expected = hmac.new(_key(), _canonical(body), hashlib.sha256).hexdigest()
    require(hmac.compare_digest(expected, seal), "anchor admission authentication failed")
    root = validate_candidate_root(candidate_root)
    require(body.get("schema_version") == 1, "anchor admission schema mismatch")
    require(body.get("suite") == CONFIG["suite"], "anchor admission suite mismatch")
    require(body.get("kind") == CONFIG["protocol"]["anchor_mode"], "anchor admission kind mismatch")
    require(body.get("seal_domain") == CONFIG["protocol"]["seal_domain"], "anchor admission domain mismatch")
    require(body.get("candidate_root") == str(root), "anchor admission candidate root mismatch")
    require(body.get("candidate_tree") == candidate_tree_snapshot(root, strict=True), "candidate tree does not match sealed admission")
    require(body.get("candidate_payload") == payload_snapshot(), "candidate payload changed after admission")
    require(body.get("evaluator_protocol") == protocol_snapshot(), "anchor protocol changed after admission")
    candidate_id = body.get("candidate_id")
    require(isinstance(candidate_id, str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", candidate_id)), "invalid sealed candidate identity")
    return {
        "kind": CONFIG["protocol"]["anchor_mode"],
        "candidate_id": candidate_id,
        "candidate_root": str(root),
        "candidate_tree": body["candidate_tree"],
        "candidate_payload": body["candidate_payload"],
        "evaluator_protocol": body["evaluator_protocol"],
        "admission_sha256": sha256(path),
        "seal": seal,
    }
