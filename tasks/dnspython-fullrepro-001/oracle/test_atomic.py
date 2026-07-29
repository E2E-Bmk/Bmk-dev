# Spec2Repo oracle - atomic tests for dnspython-fullrepro-001



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


def test_name_from_text_absolute_preserves_root_label():
    """Verifies: DNS-NAME-001, DNS-NAME-002."""
    name = dns.name.from_text("www.example.")
    assert name.labels == (b"www", b"example", b"")
    assert name.is_absolute()
    assert name.to_text() == "www.example."

def test_name_from_text_relative_with_origin_derelativizes():
    """Verifies: DNS-NAME-002, DNS-NAME-007."""
    origin = dns.name.from_text("example.")
    name = dns.name.from_text("www", origin=origin)
    assert name == dns.name.from_text("www.example.")
    assert name.derelativize(origin) == dns.name.from_text("www.example.")

def test_name_without_origin_remains_relative():
    """Verifies: DNS-NAME-002."""
    name = dns.name.from_text("www", origin=None)
    assert not name.is_absolute()
    assert name.to_text() == "www"

def test_name_wire_round_trip_preserves_labels():
    """Verifies: DNS-NAME-004, DNS-INV-001."""
    name = dns.name.from_text("api.example.")
    wire = name.to_wire()
    restored = dns.name.from_wire(wire, 0)[0]
    assert restored == name
    assert restored.to_text() == "api.example."

def test_relative_name_to_wire_without_origin_raises():
    """Verifies: DNS-NAME-007."""
    with pytest.raises(dns.name.NeedAbsoluteNameOrOrigin):
        dns.name.from_text("relative", origin=None).to_wire()

def test_name_parent_and_concatenate_behaviors():
    """Verifies: DNS-NAME-008, DNS-NAME-009, DNS-NAME-010."""
    name = dns.name.from_text("www.example.")
    assert name.parent() == dns.name.from_text("example.")
    with pytest.raises(dns.name.NoParent):
        dns.name.root.parent()
    with pytest.raises(dns.name.AbsoluteConcatenation):
        dns.name.from_text("example.").concatenate(dns.name.from_text("www"))

def test_name_relation_helpers_share_fullcompare_result():
    """Verifies: DNS-NAME-008."""
    child = dns.name.from_text("www.example.")
    parent = dns.name.from_text("example.")
    relation, order, nlabels = child.fullcompare(parent)
    assert relation == dns.name.NameRelation.SUBDOMAIN
    assert nlabels == 2
    assert child.is_subdomain(parent)
    assert parent.is_superdomain(child)

def test_name_relativize_and_derelativize_are_inverse_for_origin():
    """Verifies: DNS-NAME-008, DNS-INV-001."""
    origin = dns.name.from_text("example.")
    absolute = dns.name.from_text("www.example.")
    relative = absolute.relativize(origin)
    assert relative == dns.name.from_text("www", origin=None)
    assert relative.derelativize(origin) == absolute

def test_unicode_name_uses_idna_projection():
    """Verifies: DNS-NAME-003, DNS-NAME-006."""
    name = dns.name.from_unicode("Königsgäßchen.example.")
    assert name.is_absolute()
    assert name.to_text().endswith(".example.")
    assert "xn--" in name.to_text()

def test_reverse_ipv4_round_trip():
    """Verifies: DNS-ID-003."""
    reverse = dns.reversename.from_address("127.0.0.1")
    assert reverse.to_text() == "1.0.0.127.in-addr.arpa."
    assert dns.reversename.to_address(reverse) == "127.0.0.1"

def test_reverse_ipv6_round_trip():
    """Verifies: DNS-ID-003."""
    reverse = dns.reversename.from_address("::1")
    assert reverse.is_absolute()
    assert dns.reversename.to_address(reverse) == "::1"

def test_rdatatype_known_and_unknown_text_conversion():
    """Verifies: DNS-ID-001, DNS-ID-002, DNS-INV-008."""
    assert dns.rdatatype.from_text("A") == dns.rdatatype.A
    assert dns.rdatatype.to_text(dns.rdatatype.A) == "A"
    assert dns.rdatatype.from_text("TYPE65400") == 65400
    assert dns.rdatatype.to_text(65400) == "TYPE65400"
    with pytest.raises(dns.rdatatype.UnknownRdatatype):
        dns.rdatatype.from_text("NOT_A_TYPE")

def test_rdataclass_known_and_unknown_text_conversion():
    """Verifies: DNS-ID-001, DNS-ID-002, DNS-INV-008."""
    assert dns.rdataclass.from_text("IN") == dns.rdataclass.IN
    assert dns.rdataclass.to_text(dns.rdataclass.IN) == "IN"
    assert dns.rdataclass.from_text("CLASS65400") == 65400
    with pytest.raises(dns.rdataclass.UnknownRdataclass):
        dns.rdataclass.from_text("NOT_A_CLASS")

def test_opcode_and_rcode_flag_round_trips():
    """Verifies: DNS-ID-001, DNS-ID-002, DNS-INV-008."""
    flags = dns.opcode.to_flags(dns.opcode.UPDATE)
    assert dns.opcode.from_flags(flags) == dns.opcode.UPDATE
    assert dns.opcode.to_text(dns.opcode.UPDATE) == "UPDATE"
    base, edns = dns.rcode.to_flags(dns.rcode.NOERROR)
    assert dns.rcode.from_flags(base, edns) == dns.rcode.NOERROR
    with pytest.raises(dns.opcode.UnknownOpcode):
        dns.opcode.from_text("NO_SUCH_OPCODE")

def test_flags_text_round_trip():
    """Verifies: DNS-ID-001, DNS-INV-008."""
    value = dns.flags.from_text("QR AA RD")
    assert value & dns.flags.QR
    assert value & dns.flags.AA
    assert value & dns.flags.RD
    text = dns.flags.to_text(value)
    assert "QR" in text and "AA" in text and "RD" in text

def test_ttl_unit_text_parses_to_seconds():
    """Verifies: DNS-TTL-001."""
    assert dns.ttl.from_text("1w2d3h4m5s") == 788645
    assert dns.ttl.from_text("3600") == 3600
    with pytest.raises(dns.ttl.BadTTL):
        dns.ttl.from_text("one-hour")

def test_serial_arithmetic_wraps_at_32_bits():
    """Verifies: DNS-META-001."""
    serial = dns.serial.Serial(0xFFFFFFFF)
    assert (serial + 1).value == 0
    assert dns.serial.Serial(1) > dns.serial.Serial(0)

def test_a_rdata_from_text_exposes_class_type_and_text():
    """Verifies: DNS-RDATA-001, DNS-RDATA-005."""
    rdata = dns.rdata.from_text("IN", "A", "192.0.2.1")
    assert rdata.rdclass == dns.rdataclass.IN
    assert rdata.rdtype == dns.rdatatype.A
    assert rdata.to_text() == "192.0.2.1"

def test_rdata_wire_round_trip_preserves_text_payload():
    """Verifies: DNS-RDATA-002, DNS-RDATA-005, DNS-INV-002."""
    rdata = dns.rdata.from_text("IN", "AAAA", "2001:db8::1")
    wire = rdata.to_wire()
    restored = dns.rdata.from_wire("IN", "AAAA", wire, 0, len(wire))
    assert restored == rdata
    assert restored.to_text() == "2001:db8::1"

def test_unknown_rdata_uses_generic_payload():
    """Verifies: DNS-RDATA-003, DNS-RDATA-006."""
    rdata = dns.rdata.from_text("IN", "TYPE65000", r"\# 4 01020304")
    assert isinstance(rdata, dns.rdata.GenericRdata)
    assert rdata.to_generic().data == b"\x01\x02\x03\x04"

def test_malformed_rdata_text_raises_syntax_error():
    """Verifies: DNS-RDATA-004."""
    with pytest.raises(dns.exception.SyntaxError):
        dns.rdata.from_text("IN", "A", "not-an-address")

def test_rdataset_from_text_keeps_ttl_and_unique_records():
    """Verifies: DNS-RDSET-001, DNS-RDSET-002."""
    rdataset = dns.rdataset.from_text("IN", "A", 300, "192.0.2.1", "192.0.2.1")
    assert rdataset.ttl == 300
    assert len(rdataset) == 1
    assert next(iter(rdataset)).to_text() == "192.0.2.1"

def test_rdataset_rejects_incompatible_rdata():
    """Verifies: DNS-RDSET-003."""
    rdataset = dns.rdataset.from_text("IN", "A", 300, "192.0.2.1")
    aaaa = dns.rdata.from_text("IN", "AAAA", "2001:db8::1")
    with pytest.raises(dns.rdataset.IncompatibleTypes):
        rdataset.add(aaaa)

def test_rrset_from_text_preserves_owner_and_rdataset():
    """Verifies: DNS-RRSET-001, DNS-RRSET-002, DNS-RRSET-003."""
    rrset = dns.rrset.from_text("www.example.", 300, "IN", "A", "192.0.2.1")
    assert rrset.name == dns.name.from_text("www.example.")
    assert rrset.ttl == 300
    assert rrset.to_rdataset().match(dns.rdataclass.IN, dns.rdatatype.A, dns.rdatatype.NONE)
    assert "192.0.2.1" in rrset.to_text()

def test_rrset_match_and_full_match_use_owner_and_record_data():
    """Verifies: DNS-RRSET-002."""
    rrset = dns.rrset.from_text("www.example.", 300, "IN", "A", "192.0.2.1")
    rdata = dns.rdata.from_text("IN", "A", "192.0.2.1")
    assert rrset.match(dns.name.from_text("www.example."), dns.rdataclass.IN, dns.rdatatype.A, dns.rdatatype.NONE)
    assert rrset.full_match(
        dns.name.from_text("www.example."),
        dns.rdataclass.IN,
        dns.rdatatype.A,
        dns.rdatatype.NONE,
    )

def test_make_query_creates_question_rrset():
    """Verifies: DNS-MSG-004."""
    query = dns.message.make_query("www.example.", "A")
    assert isinstance(query, dns.message.QueryMessage)
    assert len(query.question) == 1
    assert query.question[0].name == dns.name.from_text("www.example.")
    assert query.question[0].rdtype == dns.rdatatype.A

def test_message_short_wire_header_raises():
    """Verifies: DNS-MSG-008."""
    with pytest.raises(dns.message.ShortHeader):
        dns.message.from_wire(b"\x00\x01")

def test_message_opcode_rcode_and_flags_project_through_methods():
    """Verifies: DNS-MSG-009."""
    message = dns.message.make_query("www.example.", "A")
    message.set_opcode(dns.opcode.UPDATE)
    message.set_rcode(dns.rcode.NXDOMAIN)
    assert message.opcode() == dns.opcode.UPDATE
    assert message.rcode() == dns.rcode.NXDOMAIN

def test_resolver_nameserver_assignment_normalizes_public_state():
    """Verifies: DNS-RES-001."""
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ["192.0.2.53"]
    resolver.port = 5353
    resolver.timeout = 1.25
    resolver.lifetime = 2.5
    assert tuple(str(ns) for ns in resolver.nameservers) == ("192.0.2.53",)
    assert resolver.port == 5353
    assert resolver.timeout == 1.25
    assert resolver.lifetime == 2.5

def test_resolver_query_alias_is_resolve_method():
    """Verifies: DNS-RES-002."""
    resolver = dns.resolver.Resolver(configure=False)
    assert resolver.query.__name__ == "query"
    assert resolver.resolve.__name__ == "resolve"

def test_resolver_cache_put_get_flush_and_statistics():
    """Verifies: DNS-CACHE-001, DNS-CACHE-002, DNS-INV-007."""
    cache = dns.resolver.Cache()
    key = (dns.name.from_text("www.example."), dns.rdatatype.A, dns.rdataclass.IN)
    answer = type("AnswerStub", (), {"expiration": 4102444800})()
    cache.put(key, answer)
    assert cache.get(key) is answer
    assert cache.statistics.hits == 1
    cache.flush(key)
    assert cache.get(key) is None
    assert cache.statistics.misses == 1

def test_lru_cache_evicts_least_recently_used_entry():
    """Verifies: DNS-CACHE-003."""
    cache = dns.resolver.LRUCache(max_size=1)
    key1 = (dns.name.from_text("one.example."), dns.rdatatype.A, dns.rdataclass.IN)
    key2 = (dns.name.from_text("two.example."), dns.rdatatype.A, dns.rdataclass.IN)
    one = type("AnswerStub", (), {"expiration": 4102444800})()
    two = type("AnswerStub", (), {"expiration": 4102444800})()
    cache.put(key1, one)
    assert cache.get(key1) is one
    cache.put(key2, two)
    assert cache.get(key2) is two
    assert cache.get(key1) is None
    assert cache.get_hits_for_key(key2) == 1

def test_generic_edns_option_wire_round_trip_preserves_payload():
    """Verifies: DNS-EDNS-001, DNS-EDNS-002, DNS-INV-009."""
    option = dns.edns.GenericOption(65000, b"payload")
    wire = option.to_wire()
    restored = dns.edns.option_from_wire(65000, wire, 0, len(wire))
    assert isinstance(restored, dns.edns.GenericOption)
    assert restored.otype == 65000
    assert restored.data == b"payload"

def test_ede_option_preserves_code_and_text_projection():
    """Verifies: DNS-EDNS-001."""
    option = dns.edns.EDEOption(dns.edns.EDECode.DNSSEC_BOGUS, "bad signature")
    assert option.code == dns.edns.EDECode.DNSSEC_BOGUS
    assert "bad signature" in option.to_text()
    restored = dns.edns.option_from_wire(option.otype, option.to_wire(), 0, len(option.to_wire()))
    assert restored.code == option.code
    assert restored.text == option.text

def test_tsigkeyring_text_round_trip_preserves_key_name_and_secret():
    """Verifies: DNS-META-002."""
    text = {"key.example.": "MTIzNA=="}
    keyring = dns.tsigkeyring.from_text(text)
    rendered = dns.tsigkeyring.to_text(keyring)
    assert rendered == {"key.example.": "MTIzNA=="}

def test_e164_helpers_round_trip_number_with_origin():
    """Verifies: DNS-META-003."""
    origin = dns.name.from_text("e164.arpa.")
    name = dns.e164.from_e164("+1.650.555.1212", origin=origin)
    assert name.is_absolute()
    assert dns.e164.to_e164(name, origin=origin) == "+16505551212"

def test_generated_name_split_and_choose_relativity():
    """Verifies: DNS-NAME-008."""
    origin = dns.name.from_text("example.")
    name = dns.name.from_text("api.service.example.")
    prefix, suffix = name.split(2)
    assert prefix == dns.name.from_text("api.service", origin=None)
    assert suffix == origin
    assert name.choose_relativity(origin, relativize=True) == prefix

def test_generated_name_successor_and_predecessor_are_ordered():
    """Verifies: DNS-NAME-008."""
    name = dns.name.from_text("b.example.")
    origin = dns.name.from_text("example.")
    assert name.predecessor(origin) < name
    assert name.successor(origin) > name

def test_generated_bad_escape_raises_public_exception():
    """Verifies: DNS-NAME-005."""
    with pytest.raises(dns.name.BadEscape):
        dns.name.from_text(r"bad\12.example.")

def test_generated_absolute_name_wire_with_origin_ignores_origin():
    """Verifies: DNS-NAME-007, DNS-INV-001."""
    name = dns.name.from_text("www.example.")
    other_origin = dns.name.from_text("other.")
    assert dns.name.from_wire(name.to_wire(origin=other_origin), 0)[0] == name

def test_generated_mx_rdata_text_and_wire_preserve_exchange_name():
    """Verifies: DNS-RDATA-001, DNS-RDATA-002, DNS-INV-002."""
    rdata = dns.rdata.from_text("IN", "MX", "10 mail.example.")
    restored = dns.rdata.from_wire("IN", "MX", rdata.to_wire(), 0, len(rdata.to_wire()))
    assert restored.preference == 10
    assert restored.exchange == dns.name.from_text("mail.example.")

def test_generated_rdataset_update_ttl_replaces_visible_ttl():
    """Verifies: DNS-RDSET-001, DNS-RDSET-002."""
    rdataset = dns.rdataset.from_text("IN", "A", 300, "192.0.2.1")
    rdataset.update_ttl(60)
    assert rdataset.ttl == 60
    assert "60" in rdataset.to_text(dns.name.from_text("www.example."))

def test_generated_rdataset_union_and_intersection_keep_compatible_members():
    """Verifies: DNS-RDSET-002."""
    first = dns.rdataset.from_text("IN", "A", 300, "192.0.2.1")
    second = dns.rdataset.from_text("IN", "A", 300, "192.0.2.2")
    first.union_update(second)
    assert {r.to_text() for r in first} == {"192.0.2.1", "192.0.2.2"}
    first.intersection_update(dns.rdataset.from_text("IN", "A", 300, "192.0.2.2"))
    assert [r.to_text() for r in first] == ["192.0.2.2"]

def test_generated_zone_find_node_create_false_raises_key_error():
    """Verifies: DNS-ZONE-002."""
    zone = dns.zone.from_text(
        "example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\n"
        "example. 300 IN NS ns.example.\n",
        origin="example.",
    )
    with pytest.raises(KeyError):
        zone.find_node("missing", create=False)

def test_generated_resolver_cache_expired_entry_is_miss():
    """Verifies: DNS-CACHE-001, DNS-CACHE-002."""
    cache = dns.resolver.Cache()
    key = (dns.name.from_text("www.example."), dns.rdatatype.A, dns.rdataclass.IN)
    expired = type("AnswerStub", (), {"expiration": time.time() - 1})()
    cache.put(key, expired)
    assert cache.get(key) is None
    assert cache.statistics.misses == 1

def test_generated_lru_cache_flush_selected_key_only():
    """Verifies: DNS-CACHE-002, DNS-CACHE-003."""
    cache = dns.resolver.LRUCache(max_size=10)
    key1 = (dns.name.from_text("one.example."), dns.rdatatype.A, dns.rdataclass.IN)
    key2 = (dns.name.from_text("two.example."), dns.rdatatype.A, dns.rdataclass.IN)
    answer = type("AnswerStub", (), {"expiration": 4102444800})()
    cache.put(key1, answer)
    cache.put(key2, answer)
    cache.flush(key1)
    assert cache.get(key1) is None
    assert cache.get(key2) is answer

def test_generated_resolver_reset_replaces_default_resolver():
    """Verifies: DNS-RES-001, DNS-RES-002."""
    before = dns.resolver.get_default_resolver()
    dns.resolver.reset_default_resolver()
    after = dns.resolver.get_default_resolver()
    assert isinstance(after, dns.resolver.Resolver)
    assert after is not before

def test_generated_edns_ecs_option_preserves_address_prefix_and_scope():
    """Verifies: DNS-EDNS-001."""
    option = dns.edns.ECSOption("192.0.2.0", srclen=24, scopelen=8)
    restored = dns.edns.option_from_wire(option.otype, option.to_wire(), 0, len(option.to_wire()))
    assert restored.address == "192.0.2.0"
    assert restored.srclen == 24
    assert restored.scopelen == 8

def test_generated_cookie_option_preserves_client_and_server_cookie():
    """Verifies: DNS-EDNS-001."""
    option = dns.edns.CookieOption(b"12345678", b"server-cookie")
    restored = dns.edns.option_from_wire(option.otype, option.to_wire(), 0, len(option.to_wire()))
    assert restored.client == b"12345678"
    assert restored.server == b"server-cookie"

def test_generated_tsigkeyring_accepts_dns_name_keys():
    """Verifies: DNS-META-002."""
    keyring = dns.tsigkeyring.from_text({"key.example.": "MTIzNA=="})
    assert dns.name.from_text("key.example.") in keyring

def test_generated_zone_unknown_origin_error_for_relative_zone_without_origin():
    """Verifies: DNS-ZONE-004."""
    with pytest.raises(dns.zone.UnknownOrigin):
        dns.zone.from_text("@ 300 IN NS ns", origin=None)

def test_generated_message_trailing_junk_parse_raises():
    """Verifies: DNS-MSG-008."""
    message = dns.message.make_query("www.example.", "A")
    with pytest.raises(dns.message.TrailingJunk):
        dns.message.from_wire(message.to_wire() + b"extra", ignore_trailing=False)
