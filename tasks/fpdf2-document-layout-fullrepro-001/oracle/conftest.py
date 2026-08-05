from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import re

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "depends_on(*names): declares logical atomic dependencies"
    )


def make_pdf(**kwargs):
    from fpdf import FPDF

    pdf = FPDF(**kwargs)
    pdf.compress = False
    return pdf


def rendered_bytes(pdf) -> bytes:
    stream = BytesIO()
    assert pdf.output(stream) is None
    return stream.getvalue()


def page_count(data: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?:[\s>/])", data))


def decoded_pdf(data: bytes) -> str:
    return data.decode("latin-1")


def fixed_datetime() -> datetime:
    return datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def table_rows():
    return (
        ("Name", "Value"),
        ("Ada", "10"),
        ("Ben", "20"),
        ("Cy", "30"),
    )
