from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest


class TargetOnlyFontToolsFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "fontTools" or fullname.startswith("fontTools."):
            raise ModuleNotFoundError("fontTools is not available from the selected target root")
        return None


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the fontTools package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic behaviors required by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return

    target_root = Path(configured_root).resolve()
    import_root = target_root / "Lib" if (target_root / "Lib" / "fontTools").is_dir() else target_root
    for name in list(sys.modules):
        if name == "fontTools" or name.startswith("fontTools."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(import_root))
    if not (import_root / "fontTools").is_dir():
        sys.meta_path.insert(0, TargetOnlyFontToolsFinder())


def _empty_glyph():
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    return TTGlyphPen(None).glyph()


def _rect_glyph(x0, y0, x1, y1):
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(None)
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()
    return pen.glyph()


def _triangle_glyph():
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(None)
    pen.moveTo((90, 0))
    pen.lineTo((310, 700))
    pen.lineTo((530, 0))
    pen.closePath()
    return pen.glyph()


def _component_glyph():
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen({"A": None, "acute": None})
    pen.addComponent("A", (1, 0, 0, 1, 0, 0))
    pen.addComponent("acute", (1, 0, 0, 1, 220, 0))
    return pen.glyph()


def build_sample_font():
    from fontTools.fontBuilder import FontBuilder

    glyph_order = [".notdef", "space", "A", "B", "acute", "Aacute", "smile"]
    glyphs = {
        ".notdef": _empty_glyph(),
        "space": _empty_glyph(),
        "A": _triangle_glyph(),
        "B": _rect_glyph(80, 0, 470, 680),
        "acute": _rect_glyph(40, 710, 210, 850),
        "Aacute": _component_glyph(),
        "smile": _rect_glyph(70, 40, 650, 620),
    }
    metrics = {
        ".notdef": (500, 0),
        "space": (250, 0),
        "A": (620, 90),
        "B": (600, 80),
        "acute": (260, 40),
        "Aacute": (620, 90),
        "smile": (720, 70),
    }
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({32: "space", 65: "A", 66: "B", 193: "Aacute", 0x1F600: "smile"})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900, descent=-250)
    fb.setupNameTable(
        {
            "familyName": "Oracle Sample",
            "styleName": "Regular",
            "fullName": "Oracle Sample Regular",
            "psName": "OracleSample-Regular",
            "version": "Version 1.000",
        },
        mac=False,
    )
    fb.setupOS2(
        sTypoAscender=900,
        sTypoDescender=-250,
        usWinAscent=900,
        usWinDescent=250,
        fsSelection=0x40,
        achVendID="TEST",
    )
    fb.setupPost()
    return fb.font


def font_bytes(font):
    stream = io.BytesIO()
    font.save(stream)
    return stream.getvalue()


@pytest.fixture
def sample_font():
    return build_sample_font()


@pytest.fixture
def reloaded_font(sample_font):
    from fontTools.ttLib import TTFont

    return TTFont(io.BytesIO(font_bytes(sample_font)), recalcBBoxes=False, recalcTimestamp=False)
