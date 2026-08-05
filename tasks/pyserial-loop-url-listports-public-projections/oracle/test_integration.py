from __future__ import annotations

import pytest

import serial
from serial.tools.list_ports_common import ListPortInfo


@pytest.mark.depends_on("test_get_settings_exposes_documented_serial_settings", "test_apply_settings_updates_public_serial_settings")
def test_settings_round_trip_updates_a_closed_serial():
    source = serial.Serial(None, baudrate=57600, parity=serial.PARITY_ODD, timeout=0)
    target = serial.Serial()
    target.apply_settings(source.get_settings())
    assert target.baudrate == 57600
    assert target.parity == serial.PARITY_ODD
    assert target.timeout == 0


@pytest.mark.depends_on("test_serial_for_url_selects_loop_handler", "test_loop_write_returns_byte_count")
def test_url_configuration_and_loop_transfer_form_one_workflow(loop_serial):
    loop_serial.baudrate = 19200
    loop_serial.timeout = 0
    payload = b"configured"
    written = loop_serial.write(payload)
    received = loop_serial.read(written)
    assert written == len(payload)
    assert received == payload
    assert loop_serial.baudrate == 19200


@pytest.mark.depends_on("test_serial_for_url_can_defer_opening", "test_loop_read_returns_written_bytes")
def test_deferred_url_open_then_write_and_read(loop_serial):
    loop_serial.close()
    loop_serial.port = "loop://"
    loop_serial.open()
    loop_serial.write(b"deferred")
    assert loop_serial.read(8) == b"deferred"


@pytest.mark.depends_on("test_serial_context_manager_closes_loop_url", "test_loop_write_returns_byte_count")
def test_context_workflow_writes_reads_and_closes():
    with serial.serial_for_url("loop://", timeout=0) as port:
        count = port.write(b"managed")
        assert port.read(count) == b"managed"
    assert port.closed is True


@pytest.mark.depends_on("test_loop_in_waiting_counts_written_bytes", "test_loop_read_returns_written_bytes")
def test_buffer_projection_progresses_from_write_to_read(loop_serial):
    loop_serial.write(b"progress")
    assert loop_serial.in_waiting == 8
    assert loop_serial.read(3) == b"pro"
    assert loop_serial.in_waiting == 5
    assert loop_serial.read_all() == b"gress"
    assert loop_serial.in_waiting == 0


@pytest.mark.depends_on("test_loop_read_returns_written_bytes", "test_loop_in_waiting_counts_written_bytes")
def test_partial_reads_preserve_the_unread_loop_suffix(loop_serial):
    loop_serial.write(b"abcdef")
    assert loop_serial.read(2) == b"ab"
    assert loop_serial.in_waiting == 4
    assert loop_serial.read(4) == b"cdef"


@pytest.mark.depends_on("test_loop_read_until_includes_expected_terminator", "test_loop_read_all_drains_available_bytes")
def test_delimited_read_then_drain_completes_a_framed_workflow(loop_serial):
    loop_serial.timeout = None
    loop_serial.write(b"header\nbody")
    header = loop_serial.read_until(b"\n")
    body = loop_serial.read_all()
    assert header.endswith(b"\n")
    assert body == b"body"


@pytest.mark.depends_on("test_loop_reset_input_buffer_discards_available_bytes", "test_loop_in_waiting_counts_written_bytes")
def test_reset_discards_one_frame_before_a_new_frame(loop_serial):
    loop_serial.write(b"stale")
    assert loop_serial.in_waiting == 5
    loop_serial.reset_input_buffer()
    loop_serial.write(b"fresh")
    assert loop_serial.read_all() == b"fresh"


@pytest.mark.depends_on("test_timeout_property_accepts_none_zero_and_float", "test_loop_read_returns_written_bytes")
def test_zero_timeout_reads_available_data_without_waiting(loop_serial):
    loop_serial.timeout = 0
    loop_serial.write(b"ready")
    assert loop_serial.read(5) == b"ready"
    assert loop_serial.read(1) == b""


@pytest.mark.depends_on("test_serial_for_url_selects_loop_handler", "test_loop_url_starts_open_and_reports_public_name")
def test_close_reopen_preserves_public_url_configuration(loop_serial):
    loop_serial.write(b"before")
    assert loop_serial.read_all() == b"before"
    loop_serial.close()
    loop_serial.open()
    assert loop_serial.is_open is True
    assert loop_serial.port == "loop://"
    assert loop_serial.read(1) == b""


@pytest.mark.depends_on("test_flow_control_properties_project_boolean_values", "test_serial_for_url_selects_loop_handler")
def test_loop_control_configuration_projects_status_lines(loop_serial):
    loop_serial.rts = False
    loop_serial.dtr = False
    assert loop_serial.rts is False
    assert loop_serial.dtr is False
    assert loop_serial.cts is False
    assert loop_serial.dsr is False


@pytest.mark.depends_on("test_dsrdtr_none_follows_rtscts_publicly", "test_loop_url_starts_open_and_reports_public_name")
def test_loop_control_line_changes_are_visible_through_public_properties(loop_serial):
    loop_serial.rts = False
    assert loop_serial.cts is False
    loop_serial.rts = True
    assert loop_serial.cts is True
    loop_serial.dtr = False
    assert loop_serial.dsr is False
    loop_serial.dtr = True
    assert loop_serial.dsr is True


@pytest.mark.depends_on("test_get_settings_exposes_documented_serial_settings", "test_serial_for_url_can_defer_opening")
def test_settings_apply_before_open_then_support_loop_io(make_loop):
    port = make_loop()
    port.close()
    settings = port.get_settings()
    settings["baudrate"] = 38400
    settings["parity"] = serial.PARITY_EVEN
    port.apply_settings(settings)
    port.open()
    try:
        assert port.baudrate == 38400
        assert port.parity == serial.PARITY_EVEN
        port.write(b"settings")
        assert port.read_all() == b"settings"
    finally:
        port.close()


@pytest.mark.depends_on("test_loop_write_returns_byte_count", "test_loop_read_returns_written_bytes")
def test_loop_accepts_a_bytearray_and_returns_bytes(loop_serial):
    payload = bytearray(b"bytearray")
    assert loop_serial.write(payload) == len(payload)
    result = loop_serial.read_all()
    assert isinstance(result, bytes)
    assert result == bytes(payload)


@pytest.mark.depends_on("test_loop_read_all_drains_available_bytes", "test_loop_reset_input_buffer_discards_available_bytes")
def test_read_all_and_reset_keep_buffer_state_explicit(loop_serial):
    loop_serial.write(b"first")
    assert loop_serial.read_all() == b"first"
    loop_serial.write(b"second")
    loop_serial.reset_input_buffer()
    assert loop_serial.read_all() == b""


@pytest.mark.depends_on("test_list_port_info_projects_runner_created_metadata", "test_list_port_info_supports_legacy_index_projection")
def test_metadata_and_legacy_tuple_projection_agree():
    info = ListPortInfo("synthetic/ttyOracle5", skip_link_detection=True)
    info.description = "Adapter"
    info.hwid = "SYNTHETIC"
    assert info.device == info[0]
    assert info.description == info[1]
    assert info.hwid == info[2]
    assert info.name == "ttyOracle5"


@pytest.mark.depends_on("test_list_port_info_usb_description_uses_product_and_interface", "test_list_port_info_usb_info_projects_identifiers")
def test_metadata_updates_drive_both_usb_public_projections():
    info = ListPortInfo("ttyOracle6", skip_link_detection=True)
    info.product = "Product"
    info.interface = "Interface"
    info.vid = 0x0ABC
    info.pid = 0x0123
    info.serial_number = "S6"
    assert info.usb_description() == "Product - Interface"
    rendered = info.usb_info()
    assert "0ABC:0123" in rendered
    assert "SER=S6" in rendered


@pytest.mark.depends_on("test_list_port_info_natural_order_and_equality_are_public", "test_list_port_info_initializes_public_metadata_defaults")
def test_synthetic_metadata_records_sort_and_deduplicate_by_device():
    records = [
        ListPortInfo("ttyOracle10", skip_link_detection=True),
        ListPortInfo("ttyOracle2", skip_link_detection=True),
        ListPortInfo("ttyOracle2", skip_link_detection=True),
    ]
    ordered = sorted(records)
    assert [record.device for record in ordered] == ["ttyOracle2", "ttyOracle2", "ttyOracle10"]
    assert len(set(records)) == 2


@pytest.mark.depends_on("test_serial_constants_describe_supported_configuration_values", "test_serial_constructor_projects_configuration_properties")
def test_configuration_constants_and_url_stream_work_together(loop_serial):
    loop_serial.bytesize = serial.EIGHTBITS
    loop_serial.parity = serial.PARITY_NONE
    loop_serial.stopbits = serial.STOPBITS_ONE
    loop_serial.write(b"config-stream")
    assert loop_serial.read_all() == b"config-stream"
    assert loop_serial.bytesize == serial.EIGHTBITS
    assert loop_serial.parity == serial.PARITY_NONE
    assert loop_serial.stopbits == serial.STOPBITS_ONE


@pytest.mark.depends_on("test_unknown_url_protocol_raises_value_error", "test_serial_for_url_selects_loop_handler")
def test_valid_loop_url_remains_selectable_after_invalid_url_attempt():
    with pytest.raises(ValueError):
        serial.serial_for_url("not-a-handler://", do_not_open=True)
    port = serial.serial_for_url("LOOP://", timeout=0)
    try:
        port.write(b"case")
        assert port.read_all() == b"case"
    finally:
        port.close()


@pytest.mark.depends_on(
    "test_serial_for_url_can_defer_opening",
    "test_apply_settings_updates_public_serial_settings",
)
def test_deferred_open_applies_all_settings_before_first_loop_frame(make_loop):
    port = make_loop(baudrate=9600, parity=serial.PARITY_EVEN)
    port.close()
    port.apply_settings({"baudrate": 19200, "parity": serial.PARITY_ODD, "timeout": 0})
    port.open()
    try:
        port.write(b"configured-frame")
        assert port.read_all() == b"configured-frame"
        assert (port.baudrate, port.parity, port.timeout) == (19200, serial.PARITY_ODD, 0)
    finally:
        port.close()


@pytest.mark.depends_on(
    "test_loop_read_until_includes_expected_terminator",
    "test_loop_read_returns_written_bytes",
)
def test_multiple_delimiters_and_partial_reads_preserve_frame_boundaries(loop_serial):
    loop_serial.timeout = None
    loop_serial.write(b"one\ntwo\nthree")

    assert loop_serial.read_until(b"\n") == b"one\n"
    assert loop_serial.read(2) == b"tw"
    assert loop_serial.read_until(b"\n") == b"o\n"
    assert loop_serial.read_all() == b"three"


@pytest.mark.depends_on(
    "test_flow_control_properties_project_boolean_values",
    "test_baudrate_property_accepts_integer_configuration",
    "test_loop_read_all_drains_available_bytes",
)
def test_control_line_state_survives_configuration_and_loop_transfer(loop_serial):
    loop_serial.rts = False
    loop_serial.dtr = False
    loop_serial.baudrate = 115200
    loop_serial.write(b"control-state")

    assert loop_serial.read_all() == b"control-state"
    assert loop_serial.rts is False
    assert loop_serial.dtr is False
    assert loop_serial.baudrate == 115200


@pytest.mark.depends_on(
    "test_list_port_info_usb_info_projects_identifiers",
    "test_list_port_info_natural_order_and_equality_are_public",
)
def test_metadata_sorting_keeps_usb_projection_fields_attached_to_each_device():
    first = ListPortInfo("ttyOracle20", skip_link_detection=True)
    first.product = "First"
    first.vid = 0x1000
    second = ListPortInfo("ttyOracle3", skip_link_detection=True)
    second.product = "Second"
    second.vid = 0x2000

    ordered = sorted([first, second])

    assert [item.device for item in ordered] == ["ttyOracle3", "ttyOracle20"]
    assert [item.product for item in ordered] == ["Second", "First"]
    assert [item.vid for item in ordered] == [0x2000, 0x1000]


@pytest.mark.depends_on(
    "test_apply_settings_updates_public_serial_settings",
    "test_loop_reset_input_buffer_discards_available_bytes",
)
def test_settings_round_trip_and_buffer_reset_are_independent_public_steps():
    port = serial.serial_for_url(
        "loop://",
        baudrate=4800,
        timeout=0,
        do_not_open=True,
    )
    try:
        settings = port.get_settings()
        settings["baudrate"] = 38400
        port.apply_settings(settings)
        port.open()
        port.write(b"discard-me")
        port.reset_input_buffer()
        assert port.read_all() == b""
        assert port.baudrate == 38400
    finally:
        port.close()
