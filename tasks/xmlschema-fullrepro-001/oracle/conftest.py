from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest


DEMO_NS = "urn:demo"
EXT_NS = "urn:ext"


@dataclass(frozen=True)
class FixturePaths:
    root: Path
    schema: Path
    included: Path
    imported: Path
    extra: Path
    valid_xml: Path
    invalid_xml: Path
    hinted_xml: Path
    json_input: Path


PRIMARY_XSD = """\
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:tns="urn:demo" xmlns:ext="urn:ext"
           targetNamespace="urn:demo" elementFormDefault="qualified">
  <xs:include schemaLocation="common.xsd"/>
  <xs:import namespace="urn:ext" schemaLocation="extension.xsd"/>
  <xs:element name="order" type="tns:OrderType"/>
  <xs:complexType name="OrderType">
    <xs:sequence>
      <xs:element name="customer" type="xs:string"/>
      <xs:element name="items">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="item" type="tns:ItemType" maxOccurs="2"/>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
      <xs:element name="total" type="xs:decimal"/>
      <xs:element ref="ext:note" minOccurs="0"/>
    </xs:sequence>
    <xs:attribute name="id" type="tns:CodeType" use="required"/>
  </xs:complexType>
  <xs:complexType name="ItemType">
    <xs:sequence>
      <xs:element name="sku" type="tns:CodeType"/>
      <xs:element name="quantity" type="xs:positiveInteger"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
"""

INCLUDED_XSD = """\
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="urn:demo" xmlns:tns="urn:demo">
  <xs:simpleType name="CodeType">
    <xs:restriction base="xs:string">
      <xs:pattern value="[A-Z]{2}[0-9]{2}"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>
"""

IMPORTED_XSD = """\
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="urn:ext" xmlns:tns="urn:ext">
  <xs:element name="note" type="xs:string"/>
</xs:schema>
"""

EXTRA_XSD = """\
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="urn:demo" xmlns:tns="urn:demo"
           elementFormDefault="qualified">
  <xs:element name="status" type="xs:string"/>
</xs:schema>
"""

VALID_XML = """\
<order xmlns="urn:demo" xmlns:ext="urn:ext" id="AB12">
  <customer>Ada</customer>
  <items>
    <item><sku>CD34</sku><quantity>2</quantity></item>
    <item><sku>EF56</sku><quantity>1</quantity></item>
  </items>
  <total>19.95</total>
  <ext:note>priority</ext:note>
</order>
"""

INVALID_XML = """\
<order xmlns="urn:demo" xmlns:ext="urn:ext" id="bad">
  <customer>Ada</customer>
  <items>
    <item><sku>CD34</sku><quantity>0</quantity></item>
  </items>
  <total>19.95</total>
</order>
"""

JSON_INPUT = """\
{
  "@xmlns": "urn:demo",
  "@xmlns:ext": "urn:ext",
  "@id": "AB12",
  "customer": "Ada",
  "items": {
    "item": [
      {"sku": "CD34", "quantity": 2},
      {"sku": "EF56", "quantity": 1}
    ]
  },
  "total": 19.95,
  "ext:note": "priority"
}
"""


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "depends_on(*names): declares logical atomic dependencies"
    )


@pytest.fixture
def fixture_paths(tmp_path: Path) -> FixturePaths:
    paths = FixturePaths(
        root=tmp_path,
        schema=tmp_path / "order.xsd",
        included=tmp_path / "common.xsd",
        imported=tmp_path / "extension.xsd",
        extra=tmp_path / "extra.xsd",
        valid_xml=tmp_path / "order.xml",
        invalid_xml=tmp_path / "invalid-order.xml",
        hinted_xml=tmp_path / "hinted-order.xml",
        json_input=tmp_path / "order.json",
    )
    paths.schema.write_text(PRIMARY_XSD, encoding="utf-8")
    paths.included.write_text(INCLUDED_XSD, encoding="utf-8")
    paths.imported.write_text(IMPORTED_XSD, encoding="utf-8")
    paths.extra.write_text(EXTRA_XSD, encoding="utf-8")
    paths.valid_xml.write_text(VALID_XML, encoding="utf-8")
    paths.invalid_xml.write_text(INVALID_XML, encoding="utf-8")
    paths.hinted_xml.write_text(
        VALID_XML.replace(
            'xmlns:ext="urn:ext"',
            'xmlns:ext="urn:ext" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="urn:demo order.xsd"',
        ),
        encoding="utf-8",
    )
    paths.json_input.write_text(JSON_INPUT, encoding="utf-8")
    return paths


@pytest.fixture
def schema(fixture_paths: FixturePaths):
    from xmlschema import XMLSchema

    return XMLSchema(fixture_paths.schema)


@pytest.fixture
def valid_xml(fixture_paths: FixturePaths) -> str:
    return fixture_paths.valid_xml.read_text(encoding="utf-8")
