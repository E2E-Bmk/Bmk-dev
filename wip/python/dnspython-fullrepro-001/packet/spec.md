# dnspython Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`dnspython` is a DNS toolkit that represents DNS names, resource data, record sets, messages, dynamic updates, zones, resolver state, and DNS metadata as Python objects and projects that state through public constructors, text forms, wire forms, caches, and local query/update workflows.

The package name is `dns`. The core model is an object graph whose facts include label sequences, DNS classes and types, rdata payloads, sectioned messages, EDNS options, TSIG key metadata, zone nodes, rdatasets, and resolver configuration. Public APIs must preserve those facts across parsing, mutation, serialization, comparison, and lookup views.

## Non-Goals

- This specification does not require live internet DNS queries, external recursive resolver availability, or network services outside the local process.
- This specification does not require DNS-over-HTTPS, DNS-over-QUIC, Trio, WMI, or platform-specific optional backend behavior.
- This specification does not require cryptographic DNSSEC signing or validation unless the required key objects and third-party cryptography support are present.
- This specification does not require exact `repr()` strings, exact exception message text, undocumented private helpers, or private module imports.
- This specification does not define every DNS RFC corner case, timing behavior, socket scheduling behavior, or byte-for-byte fixture snapshot beyond the public text and wire contracts described here.

## Representative Workflows

```python
import dns.name
import dns.rdatatype
import dns.rrset

owner = dns.name.from_text("www.example.")
rrset = dns.rrset.from_text(owner, 300, "IN", "A", "192.0.2.1")

assert owner.is_absolute()
assert rrset.name == owner
assert rrset.rdtype == dns.rdatatype.A
assert rrset.to_text().startswith("www.example.")
```

This workflow constructs a canonical owner name, creates an address RRset from public text input, and observes the same owner, type, TTL, and record facts through object attributes and text output.

```python
import dns.message
import dns.rdatatype

query = dns.message.make_query("www.example.", "A")
wire = query.to_wire()
round_trip = dns.message.from_wire(wire)

assert round_trip.question[0].name == query.question[0].name
assert round_trip.question[0].rdtype == dns.rdatatype.A
assert query.is_response(dns.message.make_response(query))
```

This workflow creates a query message, serializes and parses it through DNS wire format, and checks that the question facts and response relationship survive the message projection.

```python
import dns.rdataset
import dns.update
import dns.zone

zone = dns.zone.from_text("example. 300 IN SOA ns.example. hostmaster.example. 1 2 3 4 5\nexample. 300 IN NS ns.example.")
rdataset = dns.rdataset.from_text("IN", "A", 300, "192.0.2.5")
zone.replace_rdataset("www", rdataset)

update = dns.update.UpdateMessage("example.")
update.replace("www", 300, "A", "192.0.2.6")
```

This workflow demonstrates the local zone and dynamic update surfaces over the same DNS facts: an origin, owner names, rdatasets, TTLs, classes, types, and replacement semantics.

## Name And Identifier Behavior

DNS names and code identifiers are the foundational keys used by messages, records, zones, and resolver answers.

**Name Construction And Relativity.** A `Name` must store labels as DNS wire-format byte labels ordered from least significant to most significant. `dns.name.from_text` must return a `Name` from DNS text; relative text must be interpreted beneath the supplied `origin`, the default `origin` is the root name, and `origin=None` must preserve relative input as relative. Absolute input must keep its trailing root label. `dns.name.from_unicode` must apply the selected IDNA codec before creating labels. `dns.name.from_wire` and `from_wire_parser` must return the decoded name and must honor DNS compression pointers. If text contains an empty interior label, an invalid escape, an overlong label, or a name exceeding DNS length limits, then name construction must raise the applicable `dns.name` syntax or form exception.

**Text, Unicode, And Wire Projection.** `Name.to_text` must return DNS text with escaped special characters and a final dot for absolute names. `Name.to_unicode` must return the Unicode text projection using the selected IDNA codec. `Name.to_wire` must return DNS wire-format labels and must require either an absolute name or an origin that makes the name absolute. If a relative name is converted to wire without an origin, then `to_wire` must raise `NeedAbsoluteNameOrOrigin`.

**Name Relations.** `Name.fullcompare` must return the relation, ordering, and common-label count for two names. The relation must be a member of the `dns.name.NameRelation` enumeration, whose members name the possible outcomes: `NONE`, `SUPERDOMAIN`, `SUBDOMAIN`, `EQUAL`, and `COMMONANCESTOR`. `is_subdomain`, `is_superdomain`, `relativize`, `derelativize`, and `choose_relativity` must derive their result from the same label relationship. If an operation attempts to append a non-empty suffix to an absolute name, then `concatenate` must raise `AbsoluteConcatenation`. If `parent` is requested for the root or empty name, then it must raise `NoParent`. If name text contains an invalid backslash escape, then construction must raise `dns.name.BadEscape`.

**Identifier Enums And Helpers.** `dns.rdatatype`, `dns.rdataclass`, `dns.rcode`, `dns.opcode`, and `dns.flags` conversion helpers must accept documented numeric and textual identifiers and return the corresponding enum or integer values. Their `to_text` helpers must return canonical DNS token text for known values and a generic token form for unknown numeric values where that module defines one. If a textual identifier is unknown or malformed, then the relevant `UnknownRdatatype`, `UnknownRdataclass`, `UnknownRcode`, or `UnknownOpcode` exception must be raised. Reverse-name helpers must convert IPv4 and IPv6 address text to the matching reverse DNS name and must convert valid reverse DNS names back to address text.

Each identifier module must expose its protocol-defined members as named constants, so that a caller can name a value instead of writing its number. `dns.flags` must expose the header flag bits, including `QR`, `AA`, and `RD`, and `dns.flags.from_text` must combine a space-separated flag token string into their bitwise union. `dns.opcode` must expose the operation codes, including `QUERY` and `UPDATE`; `dns.rcode` must expose the response codes, including `NOERROR` and `NXDOMAIN`; and `dns.rdatatype` must expose the record types together with the wildcard-match sentinel `NONE`. `dns.opcode.to_flags` and `dns.rcode.to_flags` must encode a code into the header flag value that carries it, and `dns.opcode.from_flags` and `dns.rcode.from_flags` must recover the code from such a flag value, so that a code survives an encode-then-decode round trip. `dns.rcode.to_flags` must return both the header portion and the EDNS extended portion of a response code.

## Resource Data And Record Set Behavior

Rdata, rdatasets, and rrsets carry the typed DNS record facts that messages and zones share.

**Rdata Fact Construction.** `dns.rdata.from_text` must construct an immutable `Rdata` object for a DNS class, type, and text payload. `from_wire` and `from_wire_parser` must construct the same logical rdata facts from DNS wire payloads. Known DNS types must use their documented specialized classes, and unknown types must use `GenericRdata`. If text syntax, wire length, or token content is malformed, then construction must raise `dns.exception.SyntaxError`, `dns.exception.FormError`, or the type-specific public exception.

**Rdata Projection And Comparison.** An `Rdata` object must expose `rdclass` and `rdtype`, must return a DNS text representation through `to_text`, and must write its wire payload through `to_wire`. `to_generic` must return a generic representation that preserves the wire payload. Rdata with the same class and type must support equality and deterministic ordering. If ordered comparison involves relative names where relative ordering is disallowed, then comparison must raise `NoRelativeRdataOrdering`.

**Rdataset Semantics.** A `Rdataset` must contain only rdata with the same class, type, and covered type and must carry a TTL. `from_text`, `from_text_list`, `from_rdata`, and `from_rdata_list` must create rdatasets with the requested TTL and record contents. Adding compatible rdata must preserve a single set of unique rdata and must lower or update TTL according to the public update method used. If rdata class, type, or covered type is incompatible with the rdataset, then the operation must raise `IncompatibleTypes` or `DifferingCovers`.

**RRset Semantics.** An `RRset` must behave as an rdataset with an owner `name`. `dns.rrset.from_text`, `from_text_list`, `from_rdata`, and `from_rdata_list` must preserve the owner name, class, type, TTL, and records. `RRset.match` and `full_match` must compare owner, class, type, covered type, deleting state, and record contents according to the method's documented scope. `to_rdataset` must return an rdataset view with the same TTL and rdata contents and without the owner name.

## Message And Update Behavior

Messages organize DNS facts into protocol sections and provide the public text, wire, EDNS, TSIG, query, response, and dynamic update views.

**Message Sections.** A `Message` must expose `question`, `answer`, `authority`, and `additional` section lists, and its `sections` sequence must contain those same lists in DNS message order. `find_rrset` must return an existing matching rrset from a section or create one when creation is requested. `get_rrset` must return `None` instead of raising when no matching rrset exists. `section_count` must return the number of records in a section. If a requested section value is unknown, then the message must raise `MessageError`.

**Message Parsing And Serialization.** `dns.message.make_query` must create a `QueryMessage` containing one question rrset for the requested name, class, and type. `make_response` must create a response skeleton preserving the query id, opcode, question, and response relationship. `from_text`, `from_file`, and `from_wire` must parse message facts into the appropriate public message object. `to_text` and `to_wire` must project the same message facts back to text and wire forms. If wire data has a short header, trailing junk when trailing junk is disallowed, malformed EDNS placement, malformed TSIG placement, or a truncated response when truncation raises are requested, then parsing must raise the documented message exception.

**Opcode, Rcode, Flags, EDNS, And TSIG.** `Message.opcode`, `set_opcode`, `rcode`, and `set_rcode` must project opcode and rcode through DNS flags and EDNS extended fields. `use_edns` must configure EDNS level, flags, payload, and option objects; `want_dnssec` must set or clear the DNSSEC desired bit in EDNS flags. `get_options` and `extended_errors` must filter EDNS options by public option type. `use_tsig` must configure key name, key algorithm, original id, fudge, and MAC state for signing and validation. If a message contains a TSIG with an unknown key, then parsing must raise `UnknownTSIGKey`.

**Dynamic Update Messages.** `UpdateMessage` must use dynamic update section names: zone, prerequisite, update, and additional. The `add`, `delete`, and `replace` methods must create update-section records with the requested owner, TTL, type, and rdata semantics. The `present` and `absent` methods must create prerequisite-section records describing required existing or missing owner/type/data state. If the zone origin or record data is malformed, then the update message must raise the same public name, rdata, or message exceptions as ordinary construction.

## Zone, Transaction, And Resolver Behavior

Zones and resolvers provide higher-level state views over names, rdatasets, messages, and network configuration.

**Zone Construction And Node State.** `dns.zone.from_text` and `from_file` must create a `Zone` with an origin, rdata class, relativization policy, and node mapping from zone-file text. `Zone.find_node` and `get_node` must resolve owner names relative to the zone origin and must create nodes only when creation is requested. `find_rdataset`, `get_rdataset`, `replace_rdataset`, and `delete_rdataset` must operate on node rdatasets by owner, class, type, and covered type. If a zone has no origin when one is required, then operations must raise `UnknownOrigin`; if origin checks require SOA or NS records and they are absent, then `NoSOA` or `NoNS` must be raised.

**Zone Projection And Transactions.** `Zone.iterate_rdatasets` and `iterate_rdatas` must yield owner names with their rdatasets or individual rdata facts. `to_text`, `to_file`, and styled variants must project the zone state through zone-file text. `reader` must provide a read-only transaction view, and `writer` must provide a writable transaction view whose changes become visible when committed. If a write operation is attempted through a read-only transaction, then `ReadOnly` must be raised; if a transaction is used after it ends, then `AlreadyEnded` must be raised.

**Resolver Configuration And Answers.** A `Resolver` must maintain nameservers, search list, domain, timeout, lifetime, port, nameserver port overrides, rotation, EDNS settings, TSIG keyring, and cache configuration as public resolver state. `resolve` must query for a name, class, and type and return an `Answer`; `query` must behave as a compatibility alias for `resolve`. `resolve_address` must perform a reverse PTR lookup, and `resolve_name` must request address records for a host name. If the response has no answer, an NXDOMAIN result, disallowed metaquery, all nameservers fail, or the lifetime expires, then the resolver must raise `NoAnswer`, `NXDOMAIN`, `NoMetaqueries`, `NoNameservers`, or `LifetimeTimeout` respectively.

**Default Resolver.** The module must hold one process-wide default `Resolver` that the module-level query helpers use. `dns.resolver.get_default_resolver` must return that resolver, creating it on first call, and must return the same object on subsequent calls until it is reset. `dns.resolver.reset_default_resolver` must discard the current default so that the next `get_default_resolver` call builds a fresh one from local configuration.

**Resolver Cache Behavior.** `Cache` and `LRUCache` must map resolver cache keys to answers and must respect DNS TTL expiration. `Cache.get` must return `None` for missing or expired entries; `put` must associate a key with an answer; `flush` must remove all entries or a selected key when supplied. `LRUCache` must evict least-recently-used entries when the configured maximum size is exceeded and must expose hit counts for keys it retains. Cache statistics must count hits and misses through the public statistics object.

## Local Query, Address, And Metadata Behavior

Local helpers and metadata conversions make DNS object state usable without requiring live external services.

**Local Query Message I/O.** `dns.query.send_udp`, `receive_udp`, `send_tcp`, and `receive_tcp` must write and read `Message` wire data through caller-supplied sockets. The higher-level UDP and TCP query functions must return response messages that answer the requested question and must validate source address and question relationship. If a response comes from an unexpected source or does not answer the requested question, then `UnexpectedSource` or `BadResponse` must be raised. If a UDP response is truncated and fallback is enabled, then `udp_with_fallback` must return the TCP response together with a flag indicating TCP was used.

**EDNS Option Objects.** EDNS option classes must preserve option type and option data across object construction, wire parsing, `to_wire`, and text projection. `GenericOption` must preserve unknown option payload bytes. ECS, EDE, NSID, Cookie, ReportChannel, and filtering-related option classes must expose their documented public fields through object attributes and text output: `ECSOption`, `EDEOption`, `NSIDOption`, `CookieOption`, and `ReportChannelOption`. A `CookieOption` must carry the client cookie and the optional server cookie as separate public byte fields. An `EDEOption` must carry an extended DNS error code and an optional text reason; the error codes are named members of the `dns.edns.EDECode` enumeration, including `DNSSEC_BOGUS`. `dns.edns.option_from_wire` must return the option object for a given option type and wire payload, selecting the registered class for known types and `GenericOption` otherwise, so that an option survives a `to_wire` then `option_from_wire` round trip. If option wire data is malformed for the option type, then parsing must raise `dns.exception.FormError`.

**TTL, Serial, TSIG Keyring, And Address Helpers.** `dns.ttl.from_text` must parse plain seconds and unit-suffixed TTL text into integer seconds and must raise `BadTTL` for malformed TTL text. `dns.serial.Serial` must compare and add serial values using DNS serial arithmetic. `dns.tsigkeyring.from_text` and `to_text` must convert between textual key dictionaries and keyring objects while preserving key names, algorithms, and secrets. `dns.e164.from_e164` must convert E.164 telephone-number text to an ENUM owner name beneath the supplied origin, and `dns.e164.to_e164` must recover the leading-plus telephone text from such a name, so that a number survives a `from_e164` then `to_e164` round trip.

## State Model

The public state model has these projections:

1. Label state: `Name` objects, text names, Unicode names, wire labels, and reverse-name helpers.
2. Record state: `Rdata`, `Rdataset`, and `RRset` objects, including class, type, covered type, TTL, owner name, and record payload facts.
3. Message state: section lists, ids, flags, opcode, rcode, question/answer data, EDNS options, TSIG metadata, and wire/text message forms.
4. Zone state: origin, rdata class, node mapping, rdatasets, transaction visibility, and zone-file text forms.
5. Resolver state: nameservers, search behavior, timeout/lifetime, ports, EDNS/TSIG configuration, cache entries, and answer objects.
6. Metadata state: enum token mappings, TTL values, serial arithmetic values, EDNS options, and TSIG keyring entries.

Every public projection must preserve the same DNS facts unless an operation explicitly transforms those facts, such as relativizing a name, compacting a message into wire format, applying a dynamic update, or evicting an expired cache entry.

## Error Semantics

| Condition | Exception |
| --- | --- |
| DNS text has malformed syntax, bad escapes, overlong labels, or unexpected end | `dns.exception.SyntaxError` or a more specific `dns.name` syntax exception |
| DNS wire data is malformed, has invalid compression, has a bad label type, or violates message section placement | `dns.exception.FormError` or a more specific `dns.message`/`dns.name` form exception |
| A DNS message exceeds the supported wire size | `dns.exception.TooBig` |
| A relative name is converted to wire without a usable origin | `dns.name.NeedAbsoluteNameOrOrigin` |
| An absolute name is concatenated with a non-empty suffix | `dns.name.AbsoluteConcatenation` |
| The parent of the root or empty name is requested | `dns.name.NoParent` |
| Rdata added to an rdataset has incompatible class, type, or covered type | `dns.rdataset.IncompatibleTypes` or `dns.rdataset.DifferingCovers` |
| Message parsing sees a short header, trailing junk, malformed EDNS, malformed TSIG, or unknown TSIG key | `ShortHeader`, `TrailingJunk`, `BadEDNS`, `BadTSIG`, or `UnknownTSIGKey` |
| A resolver result is NXDOMAIN, has no answer, exhausts nameservers, uses a disallowed metaquery, or exceeds lifetime | `NXDOMAIN`, `NoAnswer`, `NoNameservers`, `NoMetaqueries`, or `LifetimeTimeout` |
| A zone lacks required origin, SOA, NS, or digest records | `UnknownOrigin`, `NoSOA`, `NoNS`, or `NoDigest` |
| A transaction is read-only or already ended | `ReadOnly` or `AlreadyEnded` |
| A textual enum token is unknown | `UnknownRdatatype`, `UnknownRdataclass`, `UnknownRcode`, or `UnknownOpcode` |
| TTL text is malformed | `BadTTL` |
| A local query response comes from the wrong source or does not answer the query | `UnexpectedSource` or `BadResponse` |

## Cross-View Invariants

1. A name parsed from text and then written to wire must return an equal `Name` when parsed from that wire under the same origin and relativization conditions.
2. An rdata object created from text and then converted through wire must preserve its class, type, text-equivalent payload, and generic payload bytes.
3. An rdataset placed into an rrset, message section, or zone node must preserve TTL, class, type, covered type, and rdata membership across the containing object's public views.
4. A query message serialized to wire and parsed back must preserve id, flags, opcode, rcode, question section, EDNS configuration, and TSIG metadata that are present in the serialized form.
5. A response skeleton created from a query must satisfy `query.is_response(response)` and must preserve the query id, opcode, and question facts.
6. A zone mutation performed through `replace_rdataset` or a writable transaction must be visible through node lookup, rdataset lookup, iteration, and zone text projection after the mutation is committed.
7. Resolver cache lookup must return the same answer object facts that were inserted while the cache entry is unexpired, and resolver cache statistics must reflect hit and miss observations.
8. Enum conversion helpers must agree across text, numeric, and flag projections: a known opcode, rcode, class, or type converted to text and back must identify the same DNS code.
9. EDNS option objects parsed from wire must preserve option type and payload when written back to wire and when attached to a message through `use_edns`.
10. Dynamic update convenience methods must produce message sections that remain visible through ordinary message section APIs and text/wire projections.

## Public Interface

### Import Surface

```python
import dns
import dns.name
import dns.rdata
import dns.rdataset
import dns.rrset
import dns.message
import dns.update
import dns.zone
import dns.resolver
import dns.query
import dns.edns
import dns.flags
import dns.opcode
import dns.rcode
import dns.rdataclass
import dns.rdatatype
import dns.reversename
import dns.e164
import dns.ttl
import dns.serial
import dns.tsig
import dns.tsigkeyring
import dns.exception
```

### API Catalog

| Name | Kind | Role |
| --- | --- | --- |
| `dns.name.Name` | class | Represents a DNS name as ordered wire-format labels. |
| `dns.name.from_text` | function | Builds a name from DNS text. |
| `dns.name.from_unicode` | function | Builds a name from Unicode text through an IDNA codec. |
| `dns.name.from_wire` | function | Builds a name from DNS wire-format data. |
| `dns.name.NameRelation` | enum | Describes the relationship between two names. |
| `dns.rdata.Rdata` | class | Base object for typed DNS resource data. |
| `dns.rdata.GenericRdata` | class | Represents unknown rdata types by preserving wire payload bytes. |
| `dns.rdata.from_text` | function | Builds rdata from class, type, and text payload. |
| `dns.rdata.from_wire` | function | Builds rdata from class, type, and wire payload. |
| `dns.rdataset.Rdataset` | class | Holds a TTL and a set of compatible rdata objects. |
| `dns.rdataset.ImmutableRdataset` | class | Provides an immutable rdataset view. |
| `dns.rdataset.from_text` | function | Builds an rdataset from text rdata values. |
| `dns.rrset.RRset` | class | Holds an owner name together with rdataset facts. |
| `dns.rrset.from_text` | function | Builds an RRset from owner, TTL, class, type, and text rdata. |
| `dns.message.Message` | class | Represents a sectioned DNS message. |
| `dns.message.QueryMessage` | class | Represents an ordinary DNS query message. |
| `dns.message.ChainingResult` | class | Reports CNAME chaining resolution facts. |
| `dns.message.from_text` | function | Parses a text-format DNS message. |
| `dns.message.from_wire` | function | Parses a wire-format DNS message. |
| `dns.message.make_query` | function | Creates a DNS query message. |
| `dns.message.make_response` | function | Creates a response skeleton for a query. |
| `dns.update.UpdateMessage` | class | Represents a DNS dynamic update message. |
| `dns.zone.Zone` | class | Represents a DNS zone as owner nodes and rdatasets. |
| `dns.zone.from_text` | function | Builds a zone from zone-file text. |
| `dns.zone.from_file` | function | Builds a zone from a zone file. |
| `dns.resolver.Resolver` | class | Performs stub resolver queries using configured nameservers and cache state. |
| `dns.resolver.Answer` | class | Represents a resolver answer and its response metadata. |
| `dns.resolver.Cache` | class | Provides a TTL-aware resolver answer cache. |
| `dns.resolver.LRUCache` | class | Provides a bounded TTL-aware least-recently-used cache. |
| `dns.resolver.resolve` | function | Resolves a name through the default resolver. |
| `dns.resolver.resolve_address` | function | Resolves reverse PTR data for an address. |
| `dns.resolver.get_default_resolver` | function | Returns the process-wide default resolver. |
| `dns.resolver.reset_default_resolver` | function | Discards the current default resolver. |
| `dns.query.udp` | function | Sends a DNS message over UDP and returns the response. |
| `dns.query.tcp` | function | Sends a DNS message over TCP and returns the response. |
| `dns.query.udp_with_fallback` | function | Performs UDP query behavior with TCP fallback for truncation. |
| `dns.edns.Option` | class | Base object for EDNS options. |
| `dns.edns.GenericOption` | class | Preserves unknown EDNS option payload bytes. |
| `dns.edns.ECSOption` | class | Represents EDNS Client Subnet option state. |
| `dns.edns.EDEOption` | class | Represents Extended DNS Error option state. |
| `dns.edns.NSIDOption` | class | Represents EDNS name-server identifier option state. |
| `dns.edns.CookieOption` | class | Represents client and server DNS cookie state. |
| `dns.edns.EDECode` | enum | Names the extended DNS error codes. |
| `dns.edns.option_from_wire` | function | Builds the option object for an option type and wire payload. |
| `dns.flags.from_text` | function | Converts DNS flag text to an integer flag value. |
| `dns.flags.to_text` | function | Converts DNS flag values to text. |
| `dns.opcode.from_text` | function | Converts opcode text to an opcode value. |
| `dns.opcode.to_flags` | function | Encodes an opcode into a header flag value. |
| `dns.opcode.from_flags` | function | Recovers an opcode from a header flag value. |
| `dns.rcode.from_text` | function | Converts rcode text to an rcode value. |
| `dns.rcode.to_flags` | function | Encodes an rcode into header and EDNS flag portions. |
| `dns.rcode.from_flags` | function | Recovers an rcode from header and EDNS flag portions. |
| `dns.rdataclass.from_text` | function | Converts DNS class text to a class value. |
| `dns.rdatatype.from_text` | function | Converts DNS type text to a type value. |
| `dns.reversename.from_address` | function | Converts address text to a reverse DNS name. |
| `dns.reversename.to_address` | function | Converts reverse DNS name text to address text. |
| `dns.e164.from_e164` | function | Converts E.164 telephone text to an ENUM DNS name. |
| `dns.e164.to_e164` | function | Converts an ENUM DNS name back to E.164 telephone text. |
| `dns.ttl.from_text` | function | Converts TTL text to integer seconds. |
| `dns.serial.Serial` | class | Represents DNS serial arithmetic values. |
| `dns.tsigkeyring.from_text` | function | Builds a TSIG keyring from textual key data. |
| `dns.exception.DNSException` | exception | Base class for package-specific exceptions. |

### CLI Entry Points

There is no console script for this package. `python -m dns` is not supported. Programmatic use is through Python imports.

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access.
The following third-party packages are preinstalled and importable:
`pytest` and `pytest-json-report`. The assessment environment provides the same
interpreter and package set.

The target package is not preinstalled. The project must declare its packaging metadata in a standard `pyproject.toml` or `setup.py` at the project root so pip installation succeeds.

## Appendix B: Assessment Notes

Assessment covers deterministic local behavior across public DNS object construction, mutation, comparison, text projection, wire projection, zone state, message sections, resolver cache state, and documented exception types. Assertions focus on observable API behavior, not private helper modules or exact diagnostic wording.

The assessment does not require live internet access. Query behavior is limited to local sockets or caller-supplied message objects where deterministic behavior is possible. Optional DNSSEC cryptography, DoH, DoQ, Trio, and platform-specific configuration paths are not part of the required package surface unless explicitly exercised through the environment listed above.
