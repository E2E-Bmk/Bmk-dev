from pathlib import Path
from .workflow_support import system_case

def test_s03(tmp_path: Path) -> None: system_case("S03", tmp_path)
def test_s04(tmp_path: Path) -> None: system_case("S04", tmp_path)
def test_s05(tmp_path: Path) -> None: system_case("S05", tmp_path)
def test_s06(tmp_path: Path) -> None: system_case("S06", tmp_path)
def test_s07(tmp_path: Path) -> None: system_case("S07", tmp_path)
def test_s08(tmp_path: Path) -> None: system_case("S08", tmp_path)
