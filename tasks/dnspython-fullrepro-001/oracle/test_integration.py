# Spec2Repo oracle - integration tests for dnspython-fullrepro-001



import io
import socket
import time

import pytest

import dns.e164
import dns.edns
import dns.exception
import dns.flags
import dns.message
import dns.name
import dns.opcode
import dns.query
import dns.rcode
import dns.rdata
import dns.rdataclass
import dns.rdataset
import dns.rdatatype
import dns.resolver
import dns.reversename
import dns.rrset
import dns.serial
import dns.tsigkeyring
import dns.ttl
import dns.update
import dns.zone


@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_name_wire_round_trip_preserves_labels')
def test_message_wire_round_trip_preserves_question():
    """Verifies: DNS-MSG-006, DNS-MSG-007, DNS-INV-004."""
    query = dns.message.make_query("www.example.", "AAAA")
    restored = dns.message.from_wire(query.to_wire())
    assert restored.id == query.id
    assert restored.question[0].name == query.question[0].name
    assert restored.question[0].rdtype == dns.rdatatype.AAAA

@pytest.mark.depends_on('test_make_query_creates_question_rrset')
def test_make_response_satisfies_query_response_relationship():
    """Verifies: DNS-MSG-005, DNS-INV-005."""
    query = dns.message.make_query("www.example.", "A")
    response = dns.message.make_response(query)
    assert query.is_response(response)
    assert response.id == query.id
    assert response.question[0] == query.question[0]

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_a_rdata_from_text_exposes_class_type_and_text')
def test_message_find_and_get_rrset_section_behavior():
    """Verifies: DNS-MSG-001, DNS-MSG-002, DNS-MSG-003."""
    message = dns.message.make_query("www.example.", "A")
    rrset = message.find_rrset(message.answer, "www.example.", "IN", "A", create=True)
    rrset.add(dns.rdata.from_text("IN", "A", "192.0.2.1"), 300)
    found = message.get_rrset(message.answer, "www.example.", "IN", "A")
    assert found is rrset
    assert message.get_rrset(message.authority, "missing.example.", "IN", "A") is None

@pytest.mark.depends_on('test_make_query_creates_question_rrset')
def test_message_trailing_junk_raises_when_disallowed():
    """Verifies: DNS-MSG-008."""
    query = dns.message.make_query("www.example.", "A")
    wire = query.to_wire() + b"junk"
    with pytest.raises(dns.message.TrailingJunk):
        dns.message.from_wire(wire, ignore_trailing=False)

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_generic_edns_option_wire_round_trip_preserves_payload')
def test_message_use_edns_and_want_dnssec_configures_options():
    """Verifies: DNS-MSG-010, DNS-EDNS-001, DNS-INV-009."""
    option = dns.edns.GenericOption(65001, b"abc")
    message = dns.message.make_query("www.example.", "A")
    message.use_edns(edns=0, payload=1232, options=[option])
    message.want_dnssec(True)
    assert message.edns == 0
    assert message.payload == 1232
    assert message.get_options(65001)[0].data == b"abc"
    assert message.ednsflags & dns.flags.DO

@pytest.mark.depends_on('test_make_query_creates_question_rrset')
def test_message_text_round_trip_preserves_question():
    """Verifies: DNS-MSG-006, DNS-MSG-007, DNS-INV-004."""
    query = dns.message.make_query("www.example.", "MX")
    restored = dns.message.from_text(query.to_text())
    assert restored.question[0].name == query.question[0].name
    assert restored.question[0].rdtype == dns.rdatatype.MX

@pytest.mark.depends_on('test_make_query_creates_question_rrset')
def test_update_message_add_delete_replace_sections_are_visible():
    """Verifies: DNS-UPD-001, DNS-UPD-002, DNS-INV-010."""
    update = dns.update.UpdateMessage("example.")
    update.add("www", 300, "A", "192.0.2.1")
    update.replace("mail", 300, "A", "192.0.2.2")
    update.delete("old", "A")
    assert len(update.update) == 4
    assert update.zone[0].name == dns.name.from_text("example.")

@pytest.mark.depends_on('test_make_query_creates_question_rrset')
def test_update_message_prerequisite_present_and_absent_sections():
    """Verifies: DNS-UPD-001, DNS-UPD-003, DNS-INV-010."""
    update = dns.update.UpdateMessage("example.")
    update.present("www", "A")
    update.absent("missing", "AAAA")
    assert len(update.prerequisite) == 2
    assert update.prerequisite[0].name == dns.name.from_text("www", origin=None)

@pytest.mark.depends_on('test_a_rdata_from_text_exposes_class_type_and_text', 'test_rrset_from_text_preserves_owner_and_rdataset')
def test_zone_from_text_builds_origin_and_required_nodes():
    """Verifies: DNS-ZONE-001, DNS-ZONE-002."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n"
        "www.example. 300 IN A 192.0.2.1\n",
        origin="example.",
    )
    assert zone.origin == dns.name.from_text("example.")
    assert zone.get_node("www") is not None
    assert zone.get_rdataset("www", "A")[0].to_text() == "192.0.2.1"

@pytest.mark.depends_on('test_rdataset_from_text_keeps_ttl_and_unique_records')
def test_zone_replace_and_delete_rdataset_mutates_node_state():
    """Verifies: DNS-ZONE-003, DNS-INV-006."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    rdataset = dns.rdataset.from_text("IN", "A", 300, "192.0.2.9")
    zone.replace_rdataset("www", rdataset)
    assert zone.find_rdataset("www", "A")[0].to_text() == "192.0.2.9"
    zone.delete_rdataset("www", "A")
    assert zone.get_rdataset("www", "A") is None

@pytest.mark.depends_on('test_zone_from_text_builds_origin_and_required_nodes')
def test_zone_iteration_exposes_owner_ttl_and_rdata():
    """Verifies: DNS-ZONE-005, DNS-INV-006."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n"
        "www.example. 300 IN A 192.0.2.1\n",
        origin="example.",
    )
    rdatas = list(zone.iterate_rdatas("A"))
    assert rdatas == [(dns.name.from_text("www", origin=None), 300, dns.rdata.from_text("IN", "A", "192.0.2.1"))]

@pytest.mark.depends_on('test_zone_from_text_builds_origin_and_required_nodes')
def test_zone_to_text_contains_public_record_facts():
    """Verifies: DNS-ZONE-005, DNS-INV-006."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n"
        "www.example. 300 IN A 192.0.2.1\n",
        origin="example.",
    )
    text = zone.to_text()
    assert "SOA" in text
    assert "NS" in text
    assert "192.0.2.1" in text

@pytest.mark.depends_on('test_zone_from_text_builds_origin_and_required_nodes')
def test_zone_origin_check_requires_soa_and_ns():
    """Verifies: DNS-ZONE-004."""
    with pytest.raises(dns.zone.NoSOA):
        dns.zone.from_text("example. 300 IN NS ns.example.\n", origin="example.", check_origin=True)

@pytest.mark.depends_on('test_rdataset_from_text_keeps_ttl_and_unique_records', 'test_zone_replace_and_delete_rdataset_mutates_node_state')
def test_zone_reader_is_read_only_and_writer_commits():
    """Verifies: DNS-ZONE-006, DNS-ZONE-007, DNS-INV-006."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    with zone.reader() as txn:
        with pytest.raises(dns.exception.DNSException):
            txn.replace("www", dns.rdataset.from_text("IN", "A", 300, "192.0.2.1"))
    with zone.writer() as txn:
        txn.replace("www", dns.rdataset.from_text("IN", "A", 300, "192.0.2.1"))
    assert zone.get_rdataset("www", "A")[0].to_text() == "192.0.2.1"

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_make_response_satisfies_query_response_relationship')
def test_query_response_relationship_detects_wrong_question():
    """Verifies: DNS-MSG-005, DNS-QUERY-003."""
    query = dns.message.make_query("www.example.", "A")
    response = dns.message.make_response(dns.message.make_query("other.example.", "A"))
    assert not query.is_response(response)

@pytest.mark.depends_on('test_rrset_from_text_preserves_owner_and_rdataset', 'test_message_wire_round_trip_preserves_question')
def test_generated_rrset_to_wire_and_message_parse_preserve_answer():
    """Verifies: DNS-RRSET-002, DNS-MSG-006, DNS-INV-003."""
    query = dns.message.make_query("www.example.", "A")
    response = dns.message.make_response(query)
    response.answer.append(dns.rrset.from_text("www.example.", 300, "IN", "A", "192.0.2.1"))
    restored = dns.message.from_wire(response.to_wire())
    assert restored.answer[0].name == dns.name.from_text("www.example.")
    assert restored.answer[0][0].to_text() == "192.0.2.1"

@pytest.mark.depends_on('test_make_query_creates_question_rrset')
def test_generated_message_section_number_round_trip():
    """Verifies: DNS-MSG-001."""
    message = dns.message.make_query("www.example.", "A")
    number = message.section_number(message.question)
    assert message.section_from_number(number) is message.question
    assert message.section_count(message.question) == 1

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_generic_edns_option_wire_round_trip_preserves_payload')
def test_generated_message_get_options_filters_by_type():
    """Verifies: DNS-MSG-010, DNS-EDNS-001."""
    one = dns.edns.GenericOption(65001, b"one")
    two = dns.edns.GenericOption(65002, b"two")
    message = dns.message.make_query("www.example.", "A")
    message.use_edns(options=[one, two])
    assert message.get_options(65002) == [two]

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_message_text_round_trip_preserves_question')
def test_generated_message_from_file_reads_one_text_message():
    """Verifies: DNS-MSG-006, DNS-MSG-007."""
    message = dns.message.make_query("www.example.", "TXT")
    loaded = dns.message.from_file(io.StringIO(message.to_text()))
    assert loaded.question[0].rdtype == dns.rdatatype.TXT

@pytest.mark.depends_on('test_update_message_add_delete_replace_sections_are_visible')
def test_generated_update_replace_creates_delete_then_add_sequence():
    """Verifies: DNS-UPD-002, DNS-INV-010."""
    update = dns.update.UpdateMessage("example.")
    update.replace("www", 120, "A", "192.0.2.10")
    assert len(update.update) == 2
    assert update.update[0].deleting is not None
    assert update.update[1][0].to_text() == "192.0.2.10"

@pytest.mark.depends_on('test_update_message_add_delete_replace_sections_are_visible', 'test_message_wire_round_trip_preserves_question')
def test_generated_update_text_wire_round_trip_preserves_sections():
    """Verifies: DNS-UPD-001, DNS-UPD-002, DNS-INV-010."""
    update = dns.update.UpdateMessage("example.")
    update.add("www", 300, "A", "192.0.2.1")
    restored = dns.message.from_wire(update.to_wire())
    assert restored.opcode() == dns.opcode.UPDATE
    assert len(restored.sections[dns.update.UPDATE]) == 1

@pytest.mark.depends_on('test_zone_from_text_builds_origin_and_required_nodes')
def test_generated_zone_get_soa_returns_origin_record():
    """Verifies: DNS-ZONE-004, DNS-ZONE-005."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 7 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    assert zone.get_soa().serial == 7

@pytest.mark.depends_on('test_zone_from_text_builds_origin_and_required_nodes', 'test_zone_to_text_contains_public_record_facts')
def test_generated_zone_file_round_trip_via_string_buffer():
    """Verifies: DNS-ZONE-005, DNS-INV-006."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    output = io.StringIO()
    zone.to_file(output)
    loaded = dns.zone.from_text(output.getvalue(), origin="example.")
    assert loaded.get_soa().mname == dns.name.from_text("ns", origin=None)

@pytest.mark.depends_on('test_zone_replace_and_delete_rdataset_mutates_node_state')
def test_generated_zone_writer_delete_removes_committed_rdataset():
    """Verifies: DNS-ZONE-006, DNS-INV-006."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n"
        "www.example. 300 IN A 192.0.2.1\n",
        origin="example.",
    )
    with zone.writer() as txn:
        txn.delete("www", "A")
    assert zone.get_rdataset("www", "A") is None

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_generic_edns_option_wire_round_trip_preserves_payload')
def test_generated_message_edns_option_survives_wire_parse():
    """Verifies: DNS-MSG-010, DNS-EDNS-001, DNS-INV-009."""
    option = dns.edns.GenericOption(65010, b"abc")
    message = dns.message.make_query("www.example.", "A")
    message.use_edns(payload=1232, options=[option])
    restored = dns.message.from_wire(message.to_wire())
    assert restored.payload == 1232
    assert restored.get_options(65010)[0].data == b"abc"

@pytest.mark.depends_on('test_opcode_and_rcode_flag_round_trips', 'test_message_opcode_rcode_and_flags_project_through_methods')
def test_generated_enum_message_flag_views_agree():
    """Verifies: DNS-ID-001, DNS-MSG-009, DNS-INV-008."""
    message = dns.message.make_query("www.example.", "A")
    message.set_opcode(dns.opcode.IQUERY)
    message.set_rcode(dns.rcode.SERVFAIL)
    assert dns.opcode.from_flags(message.flags) == dns.opcode.IQUERY
    assert dns.rcode.from_flags(message.flags, message.ednsflags) == dns.rcode.SERVFAIL

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_message_wire_round_trip_preserves_question')
def test_udp_socket_send_receive_round_trip_local_message():
    """Verifies: DNS-QUERY-001."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        listener.bind(("127.0.0.1", 0))
        sender.bind(("127.0.0.1", 0))
        query = dns.message.make_query("www.example.", "A")
        dns.query.send_udp(sender, query, listener.getsockname())
        received, _, address = dns.query.receive_udp(listener, expiration=None)
        assert received.question[0].name == query.question[0].name
        assert address == sender.getsockname()
    finally:
        listener.close()
        sender.close()

@pytest.mark.depends_on('test_make_query_creates_question_rrset', 'test_zone_from_text_builds_origin_and_required_nodes')
def test_generated_message_question_answer_zone_integration():
    """Verifies: DNS-MSG-004, DNS-MSG-005, DNS-ZONE-003, DNS-INV-003."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n"
        "www.example. 300 IN A 192.0.2.1\n",
        origin="example.",
    )
    query = dns.message.make_query("www.example.", "A")
    response = dns.message.make_response(query)
    response.answer.append(zone.find_rrset("www", "A"))
    assert query.is_response(response)
    assert response.answer[0][0].to_text() == "192.0.2.1"

@pytest.mark.depends_on('test_update_message_add_delete_replace_sections_are_visible', 'test_zone_replace_and_delete_rdataset_mutates_node_state')
def test_generated_dynamic_update_and_zone_apply_same_owner_name():
    """Verifies: DNS-UPD-002, DNS-ZONE-003, DNS-INV-010."""
    update = dns.update.UpdateMessage("example.")
    update.add("www", 300, "A", "192.0.2.99")
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    zone.replace_rdataset(update.update[0].name, update.update[0].to_rdataset())
    assert zone.get_rdataset("www", "A")[0].to_text() == "192.0.2.99"

@pytest.mark.depends_on('test_rdataset_from_text_keeps_ttl_and_unique_records', 'test_rrset_from_text_preserves_owner_and_rdataset', 'test_zone_from_text_builds_origin_and_required_nodes')
def test_generated_rdataset_rrset_message_zone_cross_view_membership():
    """Verifies: DNS-RDSET-001, DNS-RRSET-001, DNS-MSG-001, DNS-ZONE-003, DNS-INV-003."""
    rdataset = dns.rdataset.from_text("IN", "A", 300, "192.0.2.11")
    rrset = dns.rrset.from_rdata_list("www.example.", 300, list(rdataset))
    message = dns.message.make_query("www.example.", "A")
    message.answer.append(rrset)
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    zone.replace_rdataset("www", rrset.to_rdataset())
    assert message.answer[0][0] == zone.get_rdataset("www", "A")[0]
