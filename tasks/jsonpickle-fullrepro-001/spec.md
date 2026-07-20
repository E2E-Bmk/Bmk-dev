# jsonpickle Specification

## Product Overview

jsonpickle is a Python library for converting Python object graphs to JSON text and restoring trusted JSON text back into Python objects. It preserves enough metadata by default to rebuild class instances, object references, cycles, bytes, tuples, sets, class objects, module-level functions, and common pickle protocol state. It also supports a simpler one-way JSON representation when callers do not need to restore the original Python types.

Decoding jsonpickle data has the same security posture as unpickling data: callers must only decode trusted data. The `safe` option controls only legacy repr handling and must not be treated as protection for untrusted input.

## Scope

This specification covers the public behavior of:

- top-level `jsonpickle.encode`, `jsonpickle.decode`, `jsonpickle.dumps`, and `jsonpickle.loads`;
- `jsonpickle.Pickler` / `jsonpickle.pickler.Pickler` and `jsonpickle.Unpickler` / `jsonpickle.unpickler.Unpickler`;
- object metadata, reference preservation, class lookup, `__getstate__`, `__setstate__`, `__getnewargs__`, `__getnewargs_ex__`, `__getinitargs__`, and `__reduce__` round trips where they are observable through public encode/decode behavior;
- `unpicklable`, `make_refs`, `keys`, `numeric_keys`, `max_depth`, `max_iter`, `fail_safe`, `warn`, `include_properties`, `handle_readonly`, `use_decimal`, `use_base85`, `classes`, `on_missing`, `safe`, `v1_decode`, and `handler_context` options;
- public custom handler registration through `jsonpickle.handlers` and top-level `jsonpickle.register` / `jsonpickle.unregister`;
- public JSON backend management through `jsonpickle.JSONBackend`, `jsonpickle.json`, and the top-level backend helper functions.

The covered wire format is semantic. JSON object member order and whitespace are not part of the contract except when a caller explicitly passes formatting options through to the active JSON backend.

## Installable Surface

Install the package as `jsonpickle`. The package has no required runtime dependency outside the Python standard library.

The public import surface covered here is:

```python
import jsonpickle

jsonpickle.encode
jsonpickle.decode
jsonpickle.dumps
jsonpickle.loads
jsonpickle.Pickler
jsonpickle.Unpickler
jsonpickle.JSONBackend
jsonpickle.json
jsonpickle.register
jsonpickle.unregister
jsonpickle.set_preferred_backend
jsonpickle.set_encoder_options
jsonpickle.set_decoder_options
jsonpickle.load_backend
jsonpickle.remove_backend
jsonpickle.enable_fallthrough

from jsonpickle.pickler import Pickler, encode
from jsonpickle.unpickler import Unpickler, decode
from jsonpickle.handlers import BaseHandler, Registry, register, unregister
from jsonpickle.backend import JSONBackend
from jsonpickle.errors import ClassNotFoundError
```

There is no command-line interface in the covered public surface.

## Product State Model

jsonpickle exposes the same data through four public projections:

- the original Python projection: live Python objects, containers, classes, functions, references, and object identity;
- the flattened projection: JSON-compatible primitives and dictionaries produced by `Pickler.flatten`;
- the encoded projection: a JSON string produced by a configured JSON backend from the flattened projection;
- the restored Python projection: live Python values produced by `decode` or `Unpickler.restore`.

The default state model is a round-trip object graph model: `encode(value)` records class and reference metadata, and `decode(encoded)` returns a new object graph with equivalent public state and preserved shared references inside the graph. A non-default one-way model is selected with `unpicklable=False`; that model returns plain JSON-compatible data and does not promise original Python types.

The active backend manager is process state. Backend registration, removal, preferred-backend selection, and backend option setters affect later top-level `encode` and `decode` calls that use the shared `jsonpickle.json` backend. A caller-supplied `JSONBackend` or `Pickler` / `Unpickler` context is independent state for that call chain.

## Public API

```python
jsonpickle.encode(
    value,
    unpicklable=True,
    make_refs=True,
    keys=False,
    max_depth=None,
    reset=True,
    backend=None,
    warn=False,
    context=None,
    max_iter=None,
    use_decimal=False,
    numeric_keys=False,
    use_base85=False,
    fail_safe=None,
    indent=None,
    separators=None,
    include_properties=False,
    handle_readonly=False,
    handler_context=None,
) -> str
```

`encode` returns a JSON string for `value`. `dumps` is the same function. It must use `backend` when supplied and the shared `jsonpickle.json` backend otherwise. It must use `context` when a `Pickler` is supplied; when `handler_context` is supplied, it must be stored on that context for handlers in this call. `indent` and `separators` must be passed to the active backend encoder. Invalid input or backend failures must raise the underlying exception unless `fail_safe` handles a pickling exception as described below.

```python
jsonpickle.decode(
    string,
    backend=None,
    context=None,
    keys=False,
    reset=True,
    safe=True,
    classes=None,
    v1_decode=False,
    on_missing="ignore",
    handle_readonly=False,
    handler_context=None,
) -> object
```

`decode` returns a Python value from a JSON string. `loads` is the same function. It must use `backend` when supplied and the shared `jsonpickle.json` backend otherwise. It must use `context` when an `Unpickler` is supplied; when no context is supplied, it must reset the temporary unpickler after restoration so it does not retain caller objects. JSON syntax errors and backend decoding failures must raise the active backend's decoding exception.

```python
Pickler(
    unpicklable=True,
    make_refs=True,
    max_depth=None,
    backend=None,
    keys=False,
    warn=False,
    max_iter=None,
    numeric_keys=False,
    use_decimal=False,
    use_base85=False,
    fail_safe=None,
    include_properties=False,
    handle_readonly=False,
    original_object=None,
    handler_context=None,
)
Pickler.flatten(obj, reset=True) -> object
Pickler.reset() -> None
```

`Pickler.flatten` returns the JSON-compatible flattened projection instead of a JSON string. `reset=True` must clear reference tracking before the operation. `reset=False` must keep existing reference state for nested custom handler workflows. `Pickler.reset` must clear reference, depth, seen-object, and flattened-object tracking.

```python
Unpickler(
    backend=None,
    keys=False,
    safe=True,
    v1_decode=False,
    on_missing="ignore",
    handle_readonly=False,
    handler_context=None,
)
Unpickler.restore(obj, reset=True, classes=None) -> object
Unpickler.register_classes(classes) -> None
Unpickler.reset() -> None
```

`Unpickler.restore` restores an already-decoded flattened projection. `reset=True` must clear reference tracking before the operation and finalize pending reference proxies after the operation. `classes` must accept a single class, a list/tuple/set of classes, or a dictionary mapping serialized class names to class objects. `Unpickler.reset` must clear class overrides and reference/proxy tracking for the unpickler.

```python
class jsonpickle.handlers.BaseHandler:
    def __init__(self, context): ...
    def flatten(self, obj, data): ...
    def restore(self, data): ...

jsonpickle.handlers.register(cls, handler=None, base=False)
jsonpickle.handlers.unregister(cls)
jsonpickle.register(cls, handler=None, base=False)
jsonpickle.unregister(cls)
```

Handlers customize the flattened representation for a registered type. `register` must accept a class and a handler class or handler instance. When `handler` is omitted, `register` must return a decorator that registers the decorated handler. `base=True` must make the handler apply to subclasses unless a more specific handler is registered. `register` must raise `TypeError` when `cls` is not a class. `unregister` must remove direct and base registrations for the class and must return normally when the class was not registered.

```python
JSONBackend(fallthrough=True)
JSONBackend.encode(obj, indent=None, separators=None) -> str
JSONBackend.decode(string) -> object
JSONBackend.dumps(obj, indent=None, separators=None) -> str
JSONBackend.loads(string) -> object
JSONBackend.load_backend(name, dumps="dumps", loads="loads", loads_exc=ValueError) -> bool
JSONBackend.remove_backend(name) -> None
JSONBackend.set_preferred_backend(name) -> None
JSONBackend.set_encoder_options(name, *args, **kwargs) -> None
JSONBackend.set_decoder_options(name, *args, **kwargs) -> None
JSONBackend.enable_fallthrough(enable) -> None
```

`jsonpickle.json` is the shared `JSONBackend` used by top-level calls. The top-level backend helper functions are bound methods of this shared backend. `dumps` and `loads` on a backend must be aliases for `encode` and `decode`.

## Encoding And Decoding Behavior

Primitive JSON values must round-trip by value: strings, integers, floats, booleans, and `None` return as the same JSON-compatible value. Lists and dictionaries must recurse into their contents. Tuples and sets must restore as tuples and sets when `unpicklable=True`; they return as JSON arrays/lists when `unpicklable=False`.

Class instances must include enough metadata to restore the original importable class when `unpicklable=True`. Public instance attributes from `__dict__`, declared `__slots__`, dictionary subclasses, sequence subclasses, and set subclasses must be restored as observable Python attributes/items. If a class has `_jsonpickle_exclude`, attributes named in that iterable must be omitted from normal attribute and slot state; when those attributes are absent after decode, decode must not synthesize them.

Objects with `__getstate__` must serialize the returned state. On restore, `__setstate__` must receive that state when present. When `__setstate__` is absent and the state is a dictionary, state keys must become attributes or dictionary items as appropriate. When `__setstate__` is absent and the state is not a dictionary and no constructor new-args were encoded, restore must return the state object rather than an empty instance. Invalid or uncallable `__getstate__` during encoding must raise unless `warn` or `fail_safe` changes the behavior described in Error Semantics.

Objects using pickle construction protocols must round-trip through public behavior: `__getnewargs_ex__` must take precedence over `__getnewargs__`; `__getnewargs__` must take precedence over older initialization arguments when constructing an instance; `__reduce_ex__` must take precedence over `__reduce__` when both provide a value. Reduce results containing state, list items, and dictionary items must restore those visible values through the same public mutation behavior as pickle-compatible objects expose.

Module-level functions and class objects must round-trip by importable name when they are importable. Nested classes and nested class instances must restore when their serialized import path is importable or supplied through `classes`. If a function, class, or object class cannot be imported during decode, `on_missing` semantics apply for object instances; unresolved type/function references must return the unresolved flattened data or `None` according to the tag-specific behavior rather than inventing a replacement object.

Bytes must flatten as an encoded tagged value. The default byte representation must use base64. `use_base85=True` must use base85 for newly encoded bytes. Decoding must restore both base64 and base85 byte tags, and malformed byte payloads must restore as `b""`.

`max_depth` must replace values deeper than the configured depth with their Python `repr()` instead of descending further. `max_iter` must limit how many items are consumed from iterators during encoding; with no limit, an iterator is consumed until exhaustion. If an iterator tag cannot be restored as an iterable, restore must return an empty iterator.

`include_properties=True` must include public property names and their values in the flattened data for consumers of the JSON text. Decode must not require that option to restore normal object attributes, and property metadata must not overwrite explicitly restored attribute state. If a property value cannot be flattened, the same error, warning, or fail-safe behavior as other attributes must apply.

`handle_readonly=True` must let encode/decode skip or set around readonly attributes for types that otherwise raise attribute errors during normal restoration. A caller that encoded with readonly handling must pass `handle_readonly=True` to decode when the type requires that handling.

## References, Cycles, And Identity

With default `unpicklable=True` and `make_refs=True`, repeated references to the same mutable object inside one encoded graph must restore as repeated references to one restored object, not as independent copies. Cycles through objects, lists, dictionaries, tuple-like state, dictionary keys encoded with `keys=True`, and custom handler output must restore without infinite recursion and must preserve observable identity relationships within the restored graph.

With `make_refs=False`, repeated references must be expanded as independent values when expansion is possible. Cycles encountered in this mode must not recurse forever; they must be broken with a `repr()` string for unpicklable output. With `unpicklable=False`, cycles must become `None` at the recursive position, and decode must return JSON-compatible data rather than instances.

`reset=False` on `encode`, `decode`, `Pickler.flatten`, or `Unpickler.restore` must preserve the active context's reference tracking so custom handlers and nested calls share object identity state. `reset=True` must start a fresh graph.

`v1_decode=True` on `decode` or `Unpickler` must read legacy jsonpickle v1 payloads whose reference numbering did not reserve reference IDs for plain dictionaries. When this option is true, plain dictionaries must restore without being inserted into the reference table before their contents are restored, so later `py/id` references resolve according to v1 numbering. `v1_decode=False` must use the current reference model, where dictionaries participate in reference tracking and dictionary identity can be preserved. Encoding must always emit the current wire format; jsonpickle does not provide an option to write new v1-format payloads.

## Dictionary Key Semantics

By default, JSON object keys are simple JSON keys. String keys must remain strings. `None` keys must become the string `"null"`. Non-string keys such as integers, tuples, and objects must be converted to strings using `repr()` when possible and `str()` as a fallback.

`keys=True` during encoding must encode non-string keys through jsonpickle's key protocol so integers, tuples, `None`, and object keys restore as their original key values when decoding also uses `keys=True`. A caller that encodes with `keys=True` and decodes with `keys=False` must receive the escaped JSON key strings rather than the original non-string keys.

When `keys=True`, user string keys that begin with the key-escape prefix or equal reserved jsonpickle metadata tags must round-trip as ordinary user keys. Those user keys must not be mistaken for object metadata during decode.

`numeric_keys=True` must leave integer and float keys as numeric keys in the flattened projection when the active backend accepts them. This option is not a replacement for `keys=True`; when the backend converts numeric JSON keys to strings, decode must reflect the backend result.

## Class Metadata And Missing Classes

When `unpicklable=True`, objects must carry class metadata using jsonpickle's reserved metadata keys. The exact placement of metadata in a JSON object is not ordered, but decode must recognize the reserved metadata keys wherever the active backend returns them.

The recognized jsonpickle wire tags are fixed string keys. `py/object` stores the importable class path for an instance, `py/type` stores an importable type object, `py/function` stores an importable function, `py/mod` stores a module reference, and `py/repr` stores a legacy repr payload. `py/state` stores object state, `py/seq` stores sequence contents for sequence-like objects, `py/set` stores set contents, `py/tuple` stores tuple contents, `py/iterator` stores consumed iterator items, and `py/property` stores included property values. `py/id` and `py/ref` store reference-table identifiers. `py/initargs`, `py/newargs`, `py/newargsex`, `py/newobj`, `py/reduce`, and `py/default_factory` store construction and reduction data. `py/b64` and `py/b85` store encoded bytes. `json://` is the prefix used when `keys=True` escapes a user dictionary key that is itself encoded through jsonpickle's key protocol. A user dictionary key equal to a wire tag or beginning with `json://` must round-trip as user data when `keys=True`, not as metadata.

`classes` on `decode` and `Unpickler.restore` must make local or renamed classes available. A single class must register under its importable name. A sequence of classes must register each class. A dictionary must map serialized class names or class objects to replacement classes. When both the serialized class path and `classes` provide a match, the explicit `classes` mapping must be used for that decode operation.

`on_missing` must be interpreted case-insensitively when it is a string. `"ignore"` must return the decoded JSON-compatible dictionary for an instance whose class cannot be found. `"warn"` must emit a warning and return the decoded dictionary. `"error"` must raise `jsonpickle.errors.ClassNotFoundError`. A callable `on_missing` must be called with the missing class name and then restoration must continue with the decoded dictionary. A non-string, non-callable `on_missing` value must emit a warning and otherwise behave as ignored.

`safe=True` must avoid evaluating legacy repr payloads. `safe=False` must enable legacy repr restoration through `eval()` and is unsafe for untrusted data. `safe` must not change the behavior of current class metadata, reference tags, handlers, or backend JSON parsing.

## Custom Handlers

A custom handler must derive from or behave like `BaseHandler`: it receives the active pickler or unpickler context at construction time, `flatten(obj, data)` must return a JSON-compatible representation, and `restore(data)` must return the restored object.

When a registered handler is used with `unpicklable=True`, jsonpickle must provide the handler a data dictionary that already includes the class metadata for the handled object. A handler return value must become the flattened representation for that object. Returning `None` must make the object encode as `None` and must warn only when `warn=True`.

When `handler_context` is supplied to `encode`, `decode`, `Pickler`, or `Unpickler`, jsonpickle must pass it to handler `flatten` or `restore` only when that handler method accepts a parameter named `handler_context` or arbitrary keyword arguments. Handlers without that parameter must be called normally.

Handler registrations must affect both top-level `encode`/`decode` and explicit `Pickler`/`Unpickler` contexts. A direct handler registered for a subclass must take precedence over a base handler registered for an ancestor class. `unregister` must remove the handler so later calls use default behavior or another applicable base handler.

## JSON Backend Selection

The shared backend must load available JSON libraries and use the current preferred backend first. The standard-library `json` backend must be supported. The public optional backend names include `simplejson`; other loaded backends are supported only when the caller explicitly loads and selects them.

`load_backend(name, dumps="dumps", loads="loads", loads_exc=ValueError)` must import `name`, support dotted module names, locate the named encoder, decoder, and decoder exception, and return `True` only when all required components are available. It must return `False` for missing modules or missing components and must not leave a partially loaded backend active.

`set_preferred_backend(name)` must move an already loaded backend to the front of the selection order. It must raise `AssertionError` when `name` has not been loaded. `remove_backend(name)` must remove encoder, decoder, decoder exception, and option state for that backend and must return normally when the backend is absent.

`set_encoder_options(name, *args, **kwargs)` and `set_decoder_options(name, *args, **kwargs)` must persist options for later calls through that backend. Encoder options must be passed to backend dumps functions, and decoder options must be passed to backend loads functions. Per-call `indent` and `separators` passed to `encode` must override or supplement backend encoder options for that call.

When backend fallthrough is enabled, backend `encode` and `decode` must try configured backends in order and raise the last backend exception when all backends fail. When fallthrough is disabled, backend `encode` and `decode` must raise the first selected backend's exception without trying later backends.

## Error Semantics

Encoding must raise the original exception for object traversal, custom handler, attribute access, or backend encoding failures unless `fail_safe` handles a pickling exception. `KeyboardInterrupt` and `SystemExit` must always be re-raised and must not be passed to `fail_safe`.

When `fail_safe` is a callable and a non-system-exit exception occurs while flattening an object, jsonpickle must call `fail_safe(exception)` and use the callable's return value as that object's flattened value. If the callable records the exception and returns `None`, the failed object must encode as JSON `null`. If the callable raises, that new exception must propagate.

When `warn=True` and an object cannot be pickled through normal public mechanisms, jsonpickle must emit a warning and encode that object as `None`. When `warn=False`, the same unpicklable object must encode as `None` silently if no exception is raised by traversal. If sorting backend options require mutating slot attributes and `warn=True`, encoding an object with slots must raise `TypeError`.

Decoding invalid JSON must raise the active backend's JSON decoding exception. Decoding metadata for a missing class must follow `on_missing`. Decoding invalid base64 or base85 byte payloads must return `b""`. Decoding malformed tuple, set, iterator, id-reference, or reduce payloads must return the documented fallback for that tag when the tag-specific code defines one, or must raise the underlying exception when no fallback is defined.

Registering a handler with a non-class `cls` must raise `TypeError`. Registering a valid class with a handler must return `None`; registering without a handler must return a decorator. Calling `BaseHandler.flatten` or `BaseHandler.restore` directly without overriding them must raise `NotImplementedError`.

Selecting an unloaded backend must raise `AssertionError`. Loading a backend with missing dumps, loads, or decoder exception attributes must return `False`. Encoding or decoding when no backend is loaded must raise `AssertionError`.

## Cross-View Invariants

- A value flattened with a default `Pickler` and then restored with a default `Unpickler` must preserve primitive values, container contents, and public object state.
- A value encoded with default `encode` and then decoded with default `decode` must return the same restored Python projection as restoring `Pickler().flatten(value)` with `Unpickler().restore(...)`.
- A repeated object reference in the original Python projection must return as one shared object in the restored projection when `unpicklable=True` and `make_refs=True`.
- A repeated object reference in the original Python projection must return as distinct expanded values when `make_refs=False` and no cycle forces a repr fallback.
- A non-string dictionary key encoded with `keys=True` must return as the original key object/value when decoded with `keys=True`.
- A non-string dictionary key encoded with default options must return as a string key after decode.
- A class supplied through `classes` during decode must be visible to object metadata restoration in that decode call and must not mutate unrelated future temporary decoders.
- A handler registered through `jsonpickle.handlers.register` must affect top-level `jsonpickle.encode` and explicit `Pickler.flatten` calls until `unregister` removes it.
- Backend options set through top-level backend helpers must affect later top-level encode/decode calls that use the shared backend.
- `dumps` must return the same result as `encode` for the same arguments, and `loads` must return the same result as `decode` for the same arguments.
- A custom handler that uses `context.flatten(..., reset=False)` or `context.restore(..., reset=False)` must share the same reference graph as the enclosing encode/decode operation.
- A JSON string produced with formatting options must decode to the same Python projection as an unformatted JSON string for the same flattened data.

## Representative Workflows

```python
import jsonpickle

class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

root = Node("root")
leaf = Node("leaf")
root.children = [leaf, leaf]
leaf.parent = root

payload = jsonpickle.encode(root)
clone = jsonpickle.decode(payload)

assert clone.name == "root"
assert clone.children[0] is clone.children[1]
assert clone.children[0].parent is clone
```

```python
import jsonpickle

class Token:
    def __init__(self, value):
        self.value = value

data = {(1, 2): Token("pair"), None: "sentinel"}
payload = jsonpickle.encode(data, keys=True)
restored = jsonpickle.decode(payload, keys=True)

assert restored[(1, 2)].value == "pair"
assert restored[None] == "sentinel"
```

```python
import jsonpickle
import jsonpickle.handlers

class Money:
    def __init__(self, amount, currency=None):
        self.amount = amount
        self.currency = currency

@jsonpickle.handlers.register(Money)
class MoneyHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data, handler_context):
        data["amount"] = obj.amount
        data["currency"] = handler_context["currency"]
        return data

    def restore(self, data, handler_context):
        return Money(data["amount"], handler_context["currency"])

payload = jsonpickle.encode(Money(5), handler_context={"currency": "USD"})
restored = jsonpickle.decode(payload, handler_context={"currency": "EUR"})
assert restored.amount == 5
assert restored.currency == "EUR"
```

```python
import jsonpickle

class OldThing:
    def __init__(self, value):
        self.value = value

class NewThing:
    def __init__(self, value=None):
        self.value = value

payload = jsonpickle.encode(OldThing("saved"))
restored = jsonpickle.decode(payload, classes={"__main__.OldThing": NewThing})
assert isinstance(restored, NewThing)
assert restored.value == "saved"
```

## Non-Goals

- The specification does not require exact JSON object member order, whitespace, or backend-specific escaping unless the caller explicitly requests backend formatting options.
- The specification does not require implementing private helper functions, private attributes, or internal backend registry data structures.
- The specification does not require optional dependency internals for numpy, pandas, sklearn, bson, sqlalchemy, yaml, ecdsa, gmpy2, or feedparser.
- The specification does not require matching test helper class names or repository-local fixture modules.
- The specification does not require preserving object identity across separate top-level encode/decode operations.
- The specification does not make decoding untrusted jsonpickle data safe.
- The specification does not require compatibility with undocumented historical wire formats beyond the public `safe` and `v1_decode` options described here.
