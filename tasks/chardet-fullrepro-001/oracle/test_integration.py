from __future__ import annotations

import subprocess
import sys

import chardet


def test_sparse_null_separators_remain_ascii_text() -> None:
    data = (
        b"master:README.md\x002\x00For support slack to #kodiak-support\n"
        b"master:support.txt\x001\x00For support slack to #kodiak-support\n"
    )
    result = chardet.detect(data)
    assert result["encoding"] == "ascii"
    assert result["confidence"] == 0.99
    assert result["mime_type"] == "text/plain"


def test_misaligned_utf32_little_endian_falls_back_to_utf16() -> None:
    data = b"\xff\xfe\x00\x000\x00"
    result = chardet.detect(data)
    assert result["encoding"] == "UTF-16"
    assert result["confidence"] == 1.0


def test_misaligned_utf32_big_endian_falls_through_to_binary() -> None:
    data = b"\x00\x00\xfe\xff\x00H"
    result = chardet.detect(data)
    assert result["encoding"] is None
    assert result["mime_type"] == "application/octet-stream"


def test_cli_detects_ascii_file(tmp_path) -> None:
    path = tmp_path / "ascii.txt"
    path.write_bytes(b"Hello world")
    result = subprocess.run(
        [sys.executable, "-m", "chardet.cli", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "ascii" in result.stdout.lower()


def test_cli_detects_utf8_file(tmp_path) -> None:
    path = tmp_path / "utf8.txt"
    path.write_bytes("Héllo wörld".encode())
    result = subprocess.run(
        [sys.executable, "-m", "chardet.cli", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "utf-8" in result.stdout.lower()


def test_cli_reads_standard_input() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "chardet.cli"],
        input=b"Hello world",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "ascii" in result.stdout.decode().lower()


def test_cli_version_has_numeric_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "chardet.cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    output = result.stdout.strip()
    assert output.startswith("chardet ")
    assert output.split()[-1][0].isdigit()


def test_cli_minimal_outputs_only_encoding(tmp_path) -> None:
    path = tmp_path / "ascii.txt"
    path.write_bytes(b"Hello world")
    result = subprocess.run(
        [sys.executable, "-m", "chardet.cli", "--minimal", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "ascii"
