from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the ezdxf package or its src directory",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): public atomic behaviors used by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return
    target_root = Path(configured_root).resolve()
    import_root = target_root / "src" if (target_root / "src" / "ezdxf").is_dir() else target_root
    for name in list(sys.modules):
        if name == "ezdxf" or name.startswith("ezdxf."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(import_root))


def ascii_text(doc) -> str:
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue()


@pytest.fixture
def document():
    import ezdxf

    doc = ezdxf.new("R2010", units=6)
    doc.layers.add("DESIGN", color=2)
    doc.layers.add("ANNOTATION", color=4)
    doc.appids.add("APPTEST")
    return doc


@pytest.fixture
def modelspace(document):
    return document.modelspace()


@pytest.fixture
def paperspace(document):
    return document.paperspace()


@pytest.fixture
def populated_document(document):
    from ezdxf.enums import TextEntityAlignment

    msp = document.modelspace()
    msp.add_line((0, 0, 0), (3, 4, 0), dxfattribs={"layer": "DESIGN", "color": 2})
    msp.add_circle((2, 2, 0), 1.5, dxfattribs={"layer": "DESIGN"})
    msp.add_arc((4, 2, 0), 1.0, 15, 120, dxfattribs={"layer": "DESIGN"})
    msp.add_point((6, 2, 0), dxfattribs={"layer": "DESIGN"})
    text = msp.add_text("Label", dxfattribs={"layer": "ANNOTATION"})
    text.set_placement((1, 6), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_mtext("First\\PSecond", dxfattribs={"layer": "ANNOTATION"})
    msp.add_lwpolyline(
        [(0, 8), (2, 8, 0.25, 0.0, 0.0), (2, 10)],
        close=True,
        dxfattribs={"layer": "DESIGN"},
    )
    return document


@pytest.fixture
def block_document(document):
    block = document.blocks.new("SYMBOL", base_point=(1, 2, 0))
    block.add_line((0, 0), (2, 0), dxfattribs={"layer": "DESIGN"})
    block.add_circle((1, 1), 0.5, dxfattribs={"layer": "DESIGN"})
    block.add_attdef("LABEL", insert=(0, 1), text="Default", height=0.5)
    return document


def roundtrip_from_stream(doc):
    import ezdxf

    stream = io.StringIO(ascii_text(doc))
    return ezdxf.read(stream)


def roundtrip_from_file(doc, tmp_path: Path):
    import ezdxf

    path = tmp_path / "roundtrip.dxf"
    doc.saveas(path)
    return ezdxf.readfile(path)
