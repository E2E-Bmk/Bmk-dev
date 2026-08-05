from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
import sys
from zipfile import ZipFile
from xml.etree import ElementTree as ET

import pytest


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"x": MAIN_NS, "r": DOC_REL_NS, "p": REL_NS}


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the xlsxwriter package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic public behaviors used by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return
    target_root = Path(configured_root).resolve()
    for name in list(sys.modules):
        if name == "xlsxwriter" or name.startswith("xlsxwriter."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))


@pytest.fixture
def workbook_factory():
    from xlsxwriter import Workbook

    def factory(**options):
        stream = BytesIO()
        settings = {"in_memory": True}
        settings.update(options)
        return stream, Workbook(stream, settings)

    return factory


def finish(stream, workbook):
    workbook.close()
    return stream.getvalue()


def part(data, name):
    with ZipFile(BytesIO(data)) as archive:
        return archive.read(name)


def xml_part(data, name):
    return ET.fromstring(part(data, name))


def cells(root):
    return {cell.attrib["r"]: cell for cell in root.findall(".//x:c", NS)}


def shared_texts(data):
    root = xml_part(data, "xl/sharedStrings.xml")
    return ["".join(node.itertext()) for node in root.findall("x:si", NS)]


def relationships(data, name):
    root = xml_part(data, name)
    return [
        {
            "id": node.attrib.get("Id"),
            "type": node.attrib.get("Type"),
            "target": node.attrib.get("Target"),
            "mode": node.attrib.get("TargetMode"),
        }
        for node in root.findall("p:Relationship", NS)
    ]
