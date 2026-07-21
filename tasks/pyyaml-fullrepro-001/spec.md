# PyYAML Specification

## Product Overview

PyYAML is a YAML processing framework for Python. It converts YAML streams to Python objects, converts Python objects to YAML streams, and exposes intermediate YAML token, event, and representation-node views for callers that need scanning, parsing, composition, emission, serialization, or custom tag handling.

The main package is imported as `yaml`. The default public workflow is to use `safe_load` for untrusted input, `full_load` for trusted YAML that needs Python-specific scalar and collection tags without object construction, `unsafe_load` only for trusted streams that intentionally construct Python objects, and `dump` or `safe_dump` to emit YAML.

## Scope

This specification covers:

- Top-level loading, dumping, scanning, parsing, composing, emitting, and serializing functions in `yaml`.
- Loader and dumper classes: `BaseLoader`, `SafeLoader`, `FullLoader`, `Loader`, `UnsafeLoader`, `BaseDumper`, `SafeDumper`, and `Dumper`.
- Optional LibYAML-backed names when the extension is installed: `CBaseLoader`, `CSafeLoader`, `CFullLoader`, `CUnsafeLoader`, `CLoader`, `CBaseDumper`, `CSafeDumper`, and `CDumper`.
- Public token, event, and node data objects returned by `scan`, `parse`, and `compose`.
- Public constructor, representer, resolver, and `YAMLObject` extension hooks.
- Public error base classes, marked error behavior, and `Mark` snippets.

## Installable Surface

The installable import package is `yaml`.

The primary top-level functions are:

```python
yaml.scan(stream, Loader=yaml.Loader)
yaml.parse(stream, Loader=yaml.Loader)
yaml.compose(stream, Loader=yaml.Loader)
yaml.compose_all(stream, Loader=yaml.Loader)
yaml.load(stream, Loader)
yaml.load_all(stream, Loader)
yaml.safe_load(stream)
yaml.safe_load_all(stream)
yaml.full_load(stream)
yaml.full_load_all(stream)
yaml.unsafe_load(stream)
yaml.unsafe_load_all(stream)
yaml.emit(events, stream=None, Dumper=yaml.Dumper, canonical=None, indent=None, width=None, allow_unicode=None, line_break=None)
yaml.serialize(node, stream=None, Dumper=yaml.Dumper, **kwds)
yaml.serialize_all(nodes, stream=None, Dumper=yaml.Dumper, canonical=None, indent=None, width=None, allow_unicode=None, line_break=None, encoding=None, explicit_start=None, explicit_end=None, version=None, tags=None)
yaml.dump(data, stream=None, Dumper=yaml.Dumper, **kwds)
yaml.dump_all(documents, stream=None, Dumper=yaml.Dumper, default_style=None, default_flow_style=False, canonical=None, indent=None, width=None, allow_unicode=None, line_break=None, encoding=None, explicit_start=None, explicit_end=None, version=None, tags=None, sort_keys=True)
yaml.safe_dump(data, stream=None, **kwds)
yaml.safe_dump_all(documents, stream=None, **kwds)
yaml.add_constructor(tag, constructor, Loader=None)
yaml.add_multi_constructor(tag_prefix, multi_constructor, Loader=None)
yaml.add_representer(data_type, representer, Dumper=yaml.Dumper)
yaml.add_multi_representer(data_type, multi_representer, Dumper=yaml.Dumper)
yaml.add_implicit_resolver(tag, regexp, first=None, Loader=None, Dumper=yaml.Dumper)
yaml.add_path_resolver(tag, path, kind=None, Loader=None, Dumper=yaml.Dumper)
```

The top-level package exports `YAMLError`, `MarkedYAMLError`, `Mark`, loader and dumper classes, `YAMLObject`, token classes, event classes, and node classes. Constructor, representer, resolver, reader, scanner, parser, composer, emitter, and serializer base classes and specialized error classes are public through their submodules, including `yaml.constructor.ConstructorError`, `yaml.representer.RepresenterError`, `yaml.resolver.ResolverError`, `yaml.reader.ReaderError`, `yaml.scanner.ScannerError`, `yaml.parser.ParserError`, `yaml.composer.ComposerError`, `yaml.emitter.EmitterError`, and `yaml.serializer.SerializerError`.

When LibYAML bindings are installed, `yaml.__with_libyaml__` returns `True` and the `C*` loader and dumper names are importable from `yaml`. When the bindings are not installed, `yaml.__with_libyaml__` returns `False` and those names are absent. The C-backed names must follow the same public loading, dumping, token, event, node, constructor, representer, resolver, and error contract as the corresponding pure Python names.

The package has no supported command-line interface.

## Product State Model

PyYAML exposes one YAML document stream through three public projections:

- A Python object graph produced by loaders and consumed by dumpers.
- A YAML text or byte stream consumed by readers and parsers and produced by emitters.
- An intermediate model made of tokens, events, and representation nodes.

The same stream state must stay coherent across these projections:

- Loading `dump(data)` with a compatible loader must return an equivalent Python object when all tags in the dump are supported by that loader.
- Composing a stream must return nodes whose tags are the same tags used by constructors to choose Python object types.
- Serializing composed nodes and composing the serialized result must preserve the same node tags and node kinds.
- Parsing a stream and emitting the resulting events must produce a YAML stream that parses into equivalent events, ignoring source marks.
- Custom constructors and representers registered on matching Loader and Dumper classes must make dumped custom tags loadable through the same tag.
- Resolver changes registered on a Loader must affect tags visible through `compose` and object types visible through `load`.

## Public API

### Loading

`yaml.load(stream, Loader)` must parse the first YAML document in `stream` with the supplied Loader class and return the constructed Python object. `Loader` is required; calling `yaml.load(stream)` without it raises `TypeError`. `yaml.load` must return `None` when the stream has no document content. It must raise `YAMLError` when the stream is malformed, when a single-document load sees more than one document, or when the selected loader cannot construct a tag.

`yaml.load_all(stream, Loader)` must return an iterator over all documents in the stream. Empty documents yield `None`. Malformed input or unsupported tags must raise `YAMLError` during iteration.

`yaml.safe_load(stream)` and `yaml.safe_load_all(stream)` must use `SafeLoader`. They must resolve only standard YAML tags for nulls, booleans, integers, floats, binary values, timestamps, ordered maps, pairs, sets, strings, sequences, mappings, and merge keys. They must reject Python-specific tags such as `!!python/tuple`, `!!python/name`, and `!!python/object/apply` by raising `YAMLError`.

`yaml.full_load(stream)` and `yaml.full_load_all(stream)` must use `FullLoader`. They must support all `SafeLoader` tags and must support Python-specific scalar and collection tags for `none`, `bool`, `str`, `unicode`, `bytes`, `int`, `long`, `float`, `complex`, `list`, `tuple`, `dict`, and `python/name`. They must not construct arbitrary Python modules or object instances from `python/module`, `python/object`, `python/object/new`, or `python/object/apply` tags; unsupported unsafe tags must raise `YAMLError`.

`yaml.unsafe_load(stream)` and `yaml.unsafe_load_all(stream)` must use `UnsafeLoader`. They must support the safe and full tag sets and must support Python module lookup and Python object construction tags. These functions must only be used for trusted input because tags are allowed to import modules, call constructors, set object state, extend list-like objects, and assign dictionary items.

`BaseLoader` must construct every scalar as a string and must construct sequences as lists and mappings as dictionaries without implicit scalar typing. `SafeLoader` must use the safe YAML schema. `FullLoader` must add the safe Python-specific tags described above. `Loader` and `UnsafeLoader` must expose the unsafe construction behavior for backward compatibility.

`stream` must accept `str`, `bytes`, and file-like objects returning text or bytes. Byte streams must support UTF-8, UTF-8 with BOM, UTF-16-BE with BOM, and UTF-16-LE with BOM. Invalid byte encodings must raise `YAMLError`.

### YAML Type Mapping

Safe construction must map YAML tags as follows:

- `tag:yaml.org,2002:null` returns `None`.
- `tag:yaml.org,2002:bool` returns `bool` for `yes/no`, `true/false`, and `on/off`, case-insensitively.
- `tag:yaml.org,2002:int` returns `int` for decimal, binary (`0b`), octal-style leading-zero, hexadecimal (`0x`), underscore-separated, signed, and sexagesimal integer forms.
- `tag:yaml.org,2002:float` returns `float` for decimal, exponent, signed, underscore-separated, sexagesimal, `.inf`, `-.inf`, and `.nan` forms.
- `tag:yaml.org,2002:binary` returns `bytes` decoded from base64 and raises `YAMLError` when the scalar is not ASCII base64 data.
- `tag:yaml.org,2002:timestamp` returns `datetime.date` for date-only values and `datetime.datetime` for date-time values, including UTC and numeric timezone offsets when present.
- `tag:yaml.org,2002:omap` and `tag:yaml.org,2002:pairs` return lists of `(key, value)` pairs and raise `YAMLError` when their YAML value is not a sequence of one-item mappings.
- `tag:yaml.org,2002:set` returns `set`.
- `tag:yaml.org,2002:str` returns `str`.
- `tag:yaml.org,2002:seq` returns `list`.
- `tag:yaml.org,2002:map` returns `dict`.

YAML merge keys (`<<`) inside mappings must merge referenced mappings into the containing mapping. Duplicate merge sources that refer to the same merged key node must not create repeated merged entries. Explicit keys in the containing mapping must override merged keys with the same Python key.

Mapping construction must raise `YAMLError` when a constructed key is unhashable.

### Dumping

`yaml.dump(data, stream=None, Dumper=yaml.Dumper, **kwds)` must serialize one Python object. `yaml.dump_all(documents, stream=None, Dumper=yaml.Dumper, ...)` must serialize every object in `documents`.

When `stream` is `None`, dump functions must return the generated YAML. They must return `str` when `encoding is None` and `bytes` when `encoding` is a concrete encoding such as `utf-8`, `utf-16-be`, or `utf-16-le`. When `stream` is provided, dump functions must write to the stream and return `None`. With `encoding is None`, the dumper must write text; with `encoding` set, it must write bytes. A stream that rejects the written type must raise the underlying Python stream error, such as `TypeError`.

`yaml.safe_dump` and `yaml.safe_dump_all` must use `SafeDumper`. `SafeDumper` must represent `None`, `str`, `bytes`, `bool`, `int`, `float`, `list`, `tuple`, `dict`, `set`, `datetime.date`, and `datetime.datetime` with safe YAML tags. It must raise `yaml.representer.RepresenterError`, a `YAMLError`, when asked to represent an unsupported Python object.

`yaml.dump` with `Dumper` must support the safe types and Python-specific representations for `complex`, `tuple`, classes, functions, built-in functions, modules, `collections.OrderedDict`, and general objects that provide a usable reduce protocol. Unsupported objects must raise `RepresenterError`.

`sort_keys=True` is the default for `dump` and `dump_all`. It must sort mapping items when the keys are mutually comparable. `sort_keys=False` must preserve the mapping iteration order supplied by Python. If `sort_keys=True` cannot compare keys, dumping must continue using the original iteration order.

`default_flow_style=False` must prefer block style for collections. `default_flow_style=True` must prefer flow style. `explicit_start=True` must emit an explicit document start marker. `explicit_end=True` must emit an explicit document end marker. `allow_unicode=True` must emit printable Unicode characters directly; `allow_unicode=False` must escape non-ASCII characters where required by the emitter.

### Tokens, Events, And Nodes

`yaml.scan(stream, Loader=yaml.Loader)` must return an iterator of token objects. Public token classes include `DirectiveToken`, `DocumentStartToken`, `DocumentEndToken`, `StreamStartToken`, `StreamEndToken`, `BlockSequenceStartToken`, `BlockMappingStartToken`, `BlockEndToken`, `FlowSequenceStartToken`, `FlowMappingStartToken`, `FlowSequenceEndToken`, `FlowMappingEndToken`, `KeyToken`, `ValueToken`, `BlockEntryToken`, `FlowEntryToken`, `AliasToken`, `AnchorToken`, `TagToken`, and `ScalarToken`. Token objects must expose `start_mark` and `end_mark` when available. Value-bearing tokens must expose their documented attributes: directives expose `name` and `value`; aliases, anchors, and tags expose `value`; scalar tokens expose `value`, `plain`, and `style`; stream-start tokens expose `encoding`.

`yaml.parse(stream, Loader=yaml.Loader)` must return an iterator of event objects. Public event classes include `StreamStartEvent`, `StreamEndEvent`, `DocumentStartEvent`, `DocumentEndEvent`, `AliasEvent`, `ScalarEvent`, `SequenceStartEvent`, `SequenceEndEvent`, `MappingStartEvent`, and `MappingEndEvent`. Node events must expose `anchor`. Scalar events must expose `anchor`, `tag`, `implicit`, `value`, and `style`. Collection start events must expose `anchor`, `tag`, `implicit`, and `flow_style`. `DocumentStartEvent` must expose `explicit`, `version`, and `tags`. `DocumentEndEvent` must expose `explicit`.

`yaml.compose(stream, Loader=yaml.Loader)` must return the representation tree for the single YAML document, or `None` for an empty stream. `yaml.compose_all(stream, Loader=yaml.Loader)` must return an iterator of representation trees for every document. Public node classes are `ScalarNode(tag, value, start_mark=None, end_mark=None, style=None)`, `SequenceNode(tag, value, start_mark=None, end_mark=None, flow_style=None)`, and `MappingNode(tag, value, start_mark=None, end_mark=None, flow_style=None)`. Scalars must expose `tag`, `value`, `style`, and marks. Collection nodes must expose `tag`, `value`, `flow_style`, and marks. A sequence node value must be a list of child nodes. A mapping node value must be a list of `(key_node, value_node)` pairs.

`yaml.emit(events, stream=None, Dumper=yaml.Dumper, ...)` must serialize public event objects into a YAML stream. It must return `str` when `stream is None`; it must write to `stream` and return `None` when `stream` is provided. Invalid event sequences must raise `YAMLError`.

`yaml.serialize(node, stream=None, Dumper=yaml.Dumper, **kwds)` and `yaml.serialize_all(nodes, stream=None, Dumper=yaml.Dumper, ...)` must serialize representation nodes. Their return and stream behavior must match `dump` with respect to `stream` and `encoding`.

### Constructors, Representers, Resolvers, And YAMLObject

`yaml.add_constructor(tag, constructor, Loader=None)` must register a function that accepts `(loader, node)` and returns a Python object. When `Loader` is supplied, registration must affect only that Loader class. When `Loader is None`, registration must affect `Loader`, `FullLoader`, and `UnsafeLoader`, but not `SafeLoader`.

`yaml.add_multi_constructor(tag_prefix, multi_constructor, Loader=None)` must register a function that accepts `(loader, tag_suffix, node)` for tags beginning with `tag_prefix`. A `tag_prefix` of `None` must act as a fallback for otherwise unhandled tags. Loader scoping must follow `add_constructor`.

`yaml.add_representer(data_type, representer, Dumper=yaml.Dumper)` must register a function that accepts `(dumper, data)` and returns a representation node for exact instances of `data_type`. `yaml.add_multi_representer(data_type, multi_representer, Dumper=yaml.Dumper)` must register a function for `data_type` and subclasses. Dumper scoping must affect only the supplied Dumper class.

`yaml.add_implicit_resolver(tag, regexp, first=None, Loader=None, Dumper=yaml.Dumper)` must assign `tag` to plain scalars whose value matches `regexp`. `first` must be a sequence of possible initial characters; `first=None` must register a wildcard resolver. When `Loader` is supplied, it must affect only that Loader class; when `Loader is None`, it must affect `Loader`, `FullLoader`, and `UnsafeLoader`, but not `SafeLoader`. The resolver must also be registered on the supplied Dumper.

`yaml.add_path_resolver(tag, path, kind=None, Loader=None, Dumper=yaml.Dumper)` must assign `tag` to nodes reached through a path. Path elements must accept strings for mapping keys, integers for sequence indexes, `None` for any value position, and `(node_check, index_check)` tuples. `node_check` and `kind` must accept `str`, `list`, `dict`, `ScalarNode`, `SequenceNode`, `MappingNode`, or `None`. Invalid node checks, index checks, or kinds must raise `yaml.resolver.ResolverError`.

Loader instances must expose constructor helper methods used by custom constructors: `construct_scalar(node)`, `construct_sequence(node, deep=False)`, `construct_mapping(node, deep=False)`, and `construct_pairs(node, deep=False)`. These methods must raise `YAMLError` when called with the wrong node kind. Dumper instances must expose representer helper methods used by custom representers: `represent_scalar(tag, value, style=None)`, `represent_sequence(tag, sequence, flow_style=None)`, and `represent_mapping(tag, mapping, flow_style=None)`.

`yaml.YAMLObject` subclasses must register themselves when the class defines a non-`None` `yaml_tag`. `yaml_loader` must be either one Loader class or a list of Loader classes. `yaml_dumper` must be one Dumper class. The default `from_yaml` must construct an instance using the subclass and mapping state. The default `to_yaml` must represent object state using the subclass `yaml_tag` and `yaml_flow_style`. Subclasses that override `from_yaml` or `to_yaml` must receive the active loader or dumper and the node or data object.

`yaml.warnings(settings=None)` is a deprecated compatibility function. It must return `{}` when called with no settings.

## Error Semantics

`YAMLError` is the public base class for YAML processing errors. All parsing, composing, constructing, representing, emitting, serializing, scanning, and reader errors raised by PyYAML-specific processing must inherit from `YAMLError`. Ordinary Python misuse, such as omitting the required `Loader` argument to `yaml.load`, must raise the ordinary Python exception for that misuse.

`MarkedYAMLError` must expose `context`, `context_mark`, `problem`, `problem_mark`, and `note`. Its string form must include the non-empty context/problem text, the relevant mark locations, and the note. It must omit a duplicate context mark when it points to the same location as the problem mark.

`Mark(name, index, line, column, buffer, pointer)` must expose those attributes. `Mark.get_snippet(indent=4, max_length=75)` must return `None` when `buffer is None`; otherwise it must return a two-line snippet with the selected source line and a caret under `pointer`, shortening long lines with ellipses. `str(mark)` must report the source name and 1-based line and column, followed by the snippet when available.

Malformed YAML input to `scan`, `parse`, `compose`, `load`, or their `_all` variants must raise a `YAMLError` subclass. Reader failures for invalid byte streams must raise `YAMLError`. Single-document APIs must raise `YAMLError` when more than one document is present. Unsupported tags must raise `YAMLError`. Invalid merge values, invalid ordered-map or pairs shapes, invalid base64 binary values, unhashable mapping keys, blocked unsafe state keys in `FullLoader`, and invalid resolver path declarations must raise `YAMLError`.

Invalid event streams passed to `emit` and invalid node streams passed to `serialize` must raise `YAMLError`. Unsupported Python objects passed to `safe_dump` or to a Dumper without a suitable representer must raise `RepresenterError`.

## Cross-View Invariants

- Loading a YAML stream with `SafeLoader` must return Python values whose types match the tags visible from `compose` with `SafeLoader`.
- Loading a stream produced by `safe_dump(data)` with `safe_load` must return an equivalent object for safe scalar, sequence, mapping, set, date, datetime, bytes, and null values.
- Loading a stream produced by `dump(data)` with `unsafe_load` must return an equivalent object for objects represented with Python-specific tags when their classes and referenced callables are importable.
- Composing a stream, serializing the resulting node, and composing the serialized stream must preserve document count, node kinds, tags, scalar values, sequence order, and mapping key/value structure.
- Parsing a stream, emitting the resulting events, and parsing the emitted stream must preserve event class sequence and event data attributes other than marks.
- A custom implicit resolver registered on a Loader must change both the tag returned by `compose(..., Loader=ThatLoader)` and the constructor selected by `load(..., Loader=ThatLoader)`.
- A custom path resolver registered on a Loader and Dumper must affect node tags during both composition and serialization at matching paths.
- A custom constructor registered on a Loader and a matching representer registered on a Dumper must make the dumped custom tag load through the registered constructor.
- `SafeDumper` output must only require `SafeLoader` tag support for built-in safe types; `Dumper` output must require `FullLoader` or `UnsafeLoader` when it emits Python-specific tags.
- Optional C-backed loaders and dumpers must return the same public Python objects, tokens, events, nodes, and errors as their pure Python counterparts for the same supported input and options.

## Representative Workflows

### Safe Configuration Loading

```python
import yaml

text = """
name: service
enabled: true
retries: 3
started: 2026-07-09
"""

data = yaml.safe_load(text)
assert data["enabled"] is True
assert data["started"].isoformat() == "2026-07-09"

rendered = yaml.safe_dump(data, sort_keys=False)
assert yaml.safe_load(rendered) == data
```

### Custom Tag Round Trip

```python
import re
import yaml

class DiceLoader(yaml.SafeLoader):
    pass

class DiceDumper(yaml.SafeDumper):
    pass

def construct_dice(loader, node):
    return ("dice", loader.construct_scalar(node))

def represent_dice(dumper, value):
    return dumper.represent_scalar("!dice", value[1])

yaml.add_implicit_resolver("!dice", re.compile(r"^\d+d\d+$"), list("0123456789"), Loader=DiceLoader, Dumper=DiceDumper)
yaml.add_constructor("!dice", construct_dice, Loader=DiceLoader)
yaml.add_representer(tuple, represent_dice, Dumper=DiceDumper)

loaded = yaml.load("roll: 2d6\n", Loader=DiceLoader)
assert loaded == {"roll": ("dice", "2d6")}

rendered = yaml.dump(loaded, Dumper=DiceDumper)
assert yaml.load(rendered, Loader=DiceLoader) == loaded
```

### Intermediate Representation

```python
import yaml

node = yaml.compose("items: [1, 2]\n")
assert isinstance(node, yaml.MappingNode)

events = list(yaml.parse("items: [1, 2]\n"))
text = yaml.emit(events)
assert yaml.safe_load(text) == {"items": [1, 2]}
```

## Non-Goals

This specification does not require reimplementation of PyYAML private scanner, parser, composer, serializer, emitter, or reader internal state machines. It does not require compatibility with private helper modules in the test suite. It does not require byte-for-byte identical formatting for every emitted YAML stream except for public options that select observable behavior such as returned type, stream type, document markers, flow versus block style, key ordering, encoding, and successful round-trip semantics. It does not require a LibYAML C extension implementation; C-backed names are required only when such bindings are present. It does not require the deprecated top-level `_yaml` compatibility module beyond the documented `yaml` package surface.

## Evaluation Notes

Evaluation checks public behavior through the candidate-visible API described above. Tests exercise loading and dumping across safe, full, unsafe, base, and custom loaders and dumpers; YAML scalar type resolution; merge keys; Unicode and byte stream handling; token, event, and node projections; extension hooks; `YAMLObject`; error inheritance and marks; and round-trip invariants between object, stream, event, and node views.

Scoring is based on observable API compatibility. Tests must not require private implementation structure, exact internal helper names, or fixture-specific formatting that is not part of the public behavior described here.
