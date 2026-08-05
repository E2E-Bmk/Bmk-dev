from __future__ import annotations

import pytest

import serial
from serial.tools.list_ports_common import ListPortInfo


def test_public_import_surface_exposes_version_and_protocol_packages():
    assert isinstance(serial.__version__, str)
    assert serial.VERSION == serial.__version__
    assert isinstance(serial.protocol_handler_packages, list)
    assert callable(serial.serial_for_url)


def test_serial_constants_describe_supported_configuration_values():
    assert serial.EIGHTBITS in (serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS)
    assert serial.PARITY_NONE in (
        serial.PARITY_NONE,
        serial.PARITY_EVEN,
        serial.PARITY_ODD,
        serial.PARITY_MARK,
        serial.PARITY_SPACE,
    )
    assert serial.STOPBITS_ONE in (
        serial.STOPBITS_ONE,
        serial.STOPBITS_ONE_POINT_FIVE,
        serial.STOPBITS_TWO,
    )
    assert serial.Serial.BAUDRATES


def test_serial_without_port_is_closed_and_named_none():
    port = serial.Serial()
    assert port.is_open is False
    assert port.closed is True
    assert port.port is None
    assert port.name is None


def test_serial_constructor_projects_configuration_properties():
    port = serial.Serial(
        None,
        baudrate=19200,
        bytesize=serial.SEVENBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_TWO,
        timeout=1.5,
        write_timeout=2.5,
        inter_byte_timeout=0.5,
    )
    assert port.baudrate == 19200
    assert port.bytesize == serial.SEVENBITS
    assert port.parity == serial.PARITY_EVEN
    assert port.stopbits == serial.STOPBITS_TWO
    assert port.timeout == 1.5
    assert port.write_timeout == 2.5
    assert port.inter_byte_timeout == 0.5


def test_port_property_accepts_string_and_none():
    port = serial.Serial()
    port.port = "loop://"
    assert port.port == "loop://"
    assert port.name == "loop://"
    port.port = None
    assert port.port is None
    assert port.name is None


def test_baudrate_property_accepts_integer_configuration():
    port = serial.Serial()
    port.baudrate = 115200
    assert port.baudrate == 115200


def test_bytesize_property_accepts_documented_value():
    port = serial.Serial()
    port.bytesize = serial.SIXBITS
    assert port.bytesize == serial.SIXBITS


def test_parity_property_accepts_documented_values():
    port = serial.Serial()
    for parity in (serial.PARITY_NONE, serial.PARITY_ODD, serial.PARITY_SPACE):
        port.parity = parity
        assert port.parity == parity


def test_stopbits_property_accepts_documented_values():
    port = serial.Serial()
    for stopbits in (serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO):
        port.stopbits = stopbits
        assert port.stopbits == stopbits


def test_timeout_property_accepts_none_zero_and_float():
    port = serial.Serial()
    for timeout in (None, 0, 1.25):
        port.timeout = timeout
        assert port.timeout == timeout


def test_write_timeout_property_accepts_none_zero_and_float():
    port = serial.Serial()
    for timeout in (None, 0, 1.25):
        port.write_timeout = timeout
        assert port.write_timeout == timeout


def test_inter_byte_timeout_property_accepts_none_zero_and_float():
    port = serial.Serial()
    for timeout in (None, 0, 1.25):
        port.inter_byte_timeout = timeout
        assert port.inter_byte_timeout == timeout


def test_flow_control_properties_project_boolean_values():
    port = serial.Serial()
    port.xonxoff = True
    port.rtscts = True
    assert port.xonxoff is True
    assert port.rtscts is True


def test_dsrdtr_none_follows_rtscts_publicly():
    port = serial.Serial(None, rtscts=True, dsrdtr=None)
    assert port.dsrdtr is True
    port.rtscts = False
    port.dsrdtr = None
    assert port.dsrdtr is False


def test_invalid_configuration_values_raise_value_error():
    invalid_cases = (
        {"baudrate": -1},
        {"bytesize": 9},
        {"parity": "X"},
        {"stopbits": 3},
        {"timeout": -1},
        {"write_timeout": -1},
        {"inter_byte_timeout": -1},
    )
    for settings in invalid_cases:
        with pytest.raises(ValueError):
            serial.Serial(None, **settings)


def test_get_settings_exposes_documented_serial_settings():
    port = serial.Serial(None, baudrate=38400, timeout=0)
    settings = port.get_settings()
    assert set(settings) == {
        "baudrate",
        "bytesize",
        "parity",
        "stopbits",
        "xonxoff",
        "dsrdtr",
        "rtscts",
        "timeout",
        "write_timeout",
        "inter_byte_timeout",
    }
    assert settings["baudrate"] == 38400
    assert settings["timeout"] == 0


def test_apply_settings_updates_public_serial_settings():
    port = serial.Serial()
    settings = port.get_settings()
    settings["baudrate"] = 57600
    settings["parity"] = serial.PARITY_ODD
    settings["timeout"] = 0
    port.apply_settings(settings)
    assert port.baudrate == 57600
    assert port.parity == serial.PARITY_ODD
    assert port.timeout == 0


def test_serial_context_manager_closes_loop_url():
    with serial.serial_for_url("loop://", timeout=0) as port:
        assert port.is_open is True
        port.write(b"context")
    assert port.is_open is False
    assert port.closed is True


def test_serial_for_url_selects_loop_handler():
    port = serial.serial_for_url("loop://", timeout=0)
    try:
        assert port.is_open is True
        assert port.port == "loop://"
        assert port.name == "loop://"
    finally:
        port.close()


def test_serial_for_url_can_defer_opening():
    port = serial.serial_for_url("loop://", timeout=0, do_not_open=True)
    assert port.is_open is False
    assert port.port == "loop://"
    port.open()
    try:
        assert port.is_open is True
    finally:
        port.close()


def test_unknown_url_protocol_raises_value_error():
    with pytest.raises(ValueError):
        serial.serial_for_url("unknown-protocol://", do_not_open=True)


def test_loop_url_accepts_documented_logging_option():
    port = serial.serial_for_url("loop://?logging=warning", timeout=0)
    try:
        assert port.is_open is True
        port.write(b"logging")
        assert port.read_all() == b"logging"
    finally:
        port.close()


def test_loop_url_starts_open_and_reports_public_name(loop_serial):
    assert loop_serial.is_open is True
    assert loop_serial.port == "loop://"
    assert loop_serial.name == "loop://"


def test_loop_write_returns_byte_count(loop_serial):
    payload = b"public-loop"
    assert loop_serial.write(payload) == len(payload)


def test_loop_in_waiting_counts_written_bytes(loop_serial):
    payload = b"buffer-count"
    loop_serial.write(payload)
    assert loop_serial.in_waiting == len(payload)


def test_loop_read_returns_written_bytes(loop_serial):
    payload = b"read-once"
    loop_serial.write(payload)
    assert loop_serial.read(len(payload)) == payload


def test_loop_read_all_drains_available_bytes(loop_serial):
    payload = b"read-all"
    loop_serial.write(payload)
    assert loop_serial.read_all() == payload
    assert loop_serial.in_waiting == 0


def test_loop_read_until_includes_expected_terminator(loop_serial):
    loop_serial.timeout = None
    loop_serial.write(b"first\nsecond")
    assert loop_serial.read_until(b"\n") == b"first\n"
    assert loop_serial.read_all() == b"second"


def test_loop_reset_input_buffer_discards_available_bytes(loop_serial):
    loop_serial.write(b"discard-me")
    loop_serial.reset_input_buffer()
    assert loop_serial.in_waiting == 0
    assert loop_serial.read(1) == b""


def test_closed_loop_operations_raise_port_not_open_error(make_loop):
    port = make_loop()
    port.close()
    with pytest.raises(serial.PortNotOpenError):
        port.in_waiting
    with pytest.raises(serial.PortNotOpenError):
        port.read(1)
    with pytest.raises(serial.PortNotOpenError):
        port.write(b"x")


def test_list_port_info_initializes_public_metadata_defaults():
    info = ListPortInfo("ttyOracle0", skip_link_detection=True)
    assert info.device == "ttyOracle0"
    assert info.name == "ttyOracle0"
    assert info.description == "n/a"
    assert info.hwid == "n/a"
    assert info.vid is None
    assert info.pid is None
    assert info.serial_number is None
    assert info.location is None
    assert info.manufacturer is None
    assert info.product is None
    assert info.interface is None


def test_list_port_info_projects_runner_created_metadata():
    info = ListPortInfo("synthetic/ttyOracle1", skip_link_detection=True)
    info.description = "Oracle adapter"
    info.hwid = "SYNTHETIC"
    info.vid = 0x1234
    info.pid = 0x5678
    info.serial_number = "SER-1"
    info.location = "1-2"
    info.manufacturer = "Maker"
    info.product = "Adapter"
    info.interface = "Interface A"
    assert info.name == "ttyOracle1"
    assert info.description == "Oracle adapter"
    assert info.hwid == "SYNTHETIC"
    assert info.vid == 0x1234
    assert info.pid == 0x5678
    assert info.serial_number == "SER-1"
    assert info.location == "1-2"
    assert info.manufacturer == "Maker"
    assert info.product == "Adapter"
    assert info.interface == "Interface A"


def test_list_port_info_usb_description_uses_product_and_interface():
    info = ListPortInfo("ttyOracle2", skip_link_detection=True)
    info.product = "Adapter"
    assert info.usb_description() == "Adapter"
    info.interface = "Channel 1"
    assert info.usb_description() == "Adapter - Channel 1"


def test_list_port_info_usb_info_projects_identifiers():
    info = ListPortInfo("ttyOracle3", skip_link_detection=True)
    info.vid = 0x1234
    info.pid = 0x00AB
    info.serial_number = "SER-3"
    info.location = "2-4"
    rendered = info.usb_info()
    assert "USB VID:PID=1234:00AB" in rendered
    assert "SER=SER-3" in rendered
    assert "LOCATION=2-4" in rendered


def test_list_port_info_supports_legacy_index_projection():
    info = ListPortInfo("ttyOracle4", skip_link_detection=True)
    info.description = "Description"
    info.hwid = "Hardware"
    assert (info[0], info[1], info[2]) == ("ttyOracle4", "Description", "Hardware")
    with pytest.raises(IndexError):
        info[3]


def test_list_port_info_natural_order_and_equality_are_public():
    first = ListPortInfo("ttyOracle2", skip_link_detection=True)
    second = ListPortInfo("ttyOracle10", skip_link_detection=True)
    same = ListPortInfo("ttyOracle2", skip_link_detection=True)
    assert first < second
    assert first == same
    assert hash(first) == hash(same)
