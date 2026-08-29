# Kryo Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`Kryo` is a Java object-graph serialization library that coordinates class registration, serializer selection, buffered binary input and output, object identity, and graph copying. The installable Maven artifact is `com.esotericsoftware:kryo`, and its core API is exposed through the `com.esotericsoftware.kryo`, `com.esotericsoftware.kryo.io`, and `com.esotericsoftware.kryo.util` packages.

A `Kryo` instance represents one configured serialization session. Its registration table and long-lived context persist across graphs, while reference tracking, graph context, and copy bookkeeping follow the graph lifecycle. `Input` and `Output` expose the byte-oriented projection of the same work, and `Serializer` implementations define how application types move between objects and bytes.

## Non-Goals

- This specification does not require specialized field, collection, map, compatibility, compression, encryption, record, closure, JDK-profile, or Kotlin serializers.
- This specification does not require unsafe or direct-buffer I/O classes.
- This specification does not define a stable byte fixture for compatibility with historical releases or other languages.
- This specification does not require performance-measurement modules, pooling utilities, logging integration, or network services.
- This specification does not define private helper types, internal collection layouts, reflection strategies, exact exception messages, exact log text, or `toString` formatting.
- This specification does not require concurrent use of a `Kryo`, `Input`, or `Output` instance; callers use separate instances across threads.

## Representative Workflows

The first workflow registers an application type, writes one graph to an expandable in-memory buffer, and reads it through the matching typed API.

```java
Kryo kryo = new Kryo();
kryo.register(Message.class);

Message sent = new Message();
sent.text = "hello";

Output output = new Output(64, -1);
kryo.writeObject(output, sent);

Input input = new Input(output.getBuffer(), 0, output.position());
Message received = kryo.readObject(input, Message.class);
```

`received` is a distinct object whose serialized state is equivalent to `sent`. The readable byte range is bounded by the output position rather than the backing array capacity.

The second workflow supplies a serializer, uses the runtime-class form for a nullable value, and enables identity restoration for a self-referential graph.

```java
Kryo kryo = new Kryo();
kryo.setReferences(true);
kryo.register(Node.class, new NodeSerializer());

Node root = new Node("root");
root.next = root;

Output output = new Output(128, -1);
kryo.writeClassAndObject(output, root);

Input input = new Input(output.toBytes());
Node restored = (Node)kryo.readClassAndObject(input);
assert restored.next == restored;
```

The serializer's `read` implementation creates the parent, calls `reference` with it, and then reads `next`. This ordering makes the parent available when the nested reference is resolved.

The third workflow uses the same configured session for direct graph copying without producing bytes.

```java
Kryo kryo = new Kryo();
kryo.register(Node.class, new NodeSerializer());

Node deep = kryo.copy(root);
Node shallow = kryo.copyShallow(root);
```

The deep result duplicates supported descendants while preserving repeated-reference relationships. The shallow result duplicates the root while retaining the original child references.

## Object Graph Reading and Writing

This section defines the paired object operations that connect registered serializers to `Input` and `Output` while maintaining graph boundaries.

**Known-type graphs.**

- The `writeObject` operation must use the registration's serializer for the runtime type when no serializer argument is supplied.
- When a serializer argument is supplied to `writeObject`, the operation must use that serializer instead of the registered serializer.
- The `readObject` operation must use the serializer for the requested concrete type when no serializer argument is supplied.
- When a serializer argument is supplied to `readObject`, the operation must use that serializer instead of the registered serializer.
- If `writeObject` receives a null object, then it must raise `IllegalArgumentException`.
- If `readObject` receives a null `Input` or null type, then it must raise `IllegalArgumentException`.

**Nullable and polymorphic graphs.**

- When `writeObjectOrNull` receives null, the matching `readObjectOrNull` operation must return null.
- When `writeObjectOrNull` receives a non-null value, the matching `readObjectOrNull` operation must return an object decoded by the selected serializer and requested type.
- When `writeClassAndObject` receives a non-null value, it must write enough class information for `readClassAndObject` to select the same registration and return the decoded runtime type.
- When `writeClassAndObject` receives null, the matching `readClassAndObject` operation must return null.
- When `writeClass` writes a type, the matching `readClass` operation must return the registration associated with that type.
- When `writeClass` writes null, the matching `readClass` operation must return null.

**Serializer callbacks.**

- When a `Serializer` is selected for writing, the framework must invoke its `write` callback with the active `Kryo`, `Output`, and object.
- When a `Serializer` is selected for reading, the framework must invoke its `read` callback with the active `Kryo`, `Input`, and concrete type and must return the callback result.
- Where an application type implements `KryoSerializable`, its public `write` and `read` callbacks must define that type's object-to-byte round trip through the active session.
- If any object operation receives a null `Serializer` argument, then it must raise `IllegalArgumentException`.

## Registration and Serializer Selection

This section defines how class identity, numeric IDs, serializer metadata, and class-resolver callbacks form the public registration view.

**Registration records.**

- When `register` receives a previously unseen type without an explicit ID, it must assign the lowest available non-negative registration ID and return a `Registration`.
- When `register` receives a type that is already registered without a replacement serializer, it must return the existing registration without changing its ID.
- When `register` receives an already registered type with a serializer, it must retain the registration ID and replace the serializer exposed by that registration.
- When `register` receives a previously unseen type with an explicit non-negative ID, the resulting `Registration` must expose that ID through `getId`, the type through `getType`, and the serializer through `getSerializer`.
- When `Registration.setSerializer` receives a non-null serializer, subsequent `getSerializer` and object operations must observe the replacement.
- When `Registration.setInstantiator` receives a non-null `ObjectInstantiator`, subsequent `getInstantiator` and `Kryo.newInstance` operations must use it for that registration.
- If a registration type, serializer, or instantiator that is required by the operation is null, then the operation must raise `IllegalArgumentException`.
- If an explicit registration ID is negative, then `register` must raise `IllegalArgumentException`.

**Required and implicit registration.**

- While registration is required, `getRegistration` for an unregistered type must raise `IllegalArgumentException`.
- Where `setRegistrationRequired(false)` is active, `getRegistration` for an unregistered type must create and return an implicit registration using the selected default serializer.
- The `isRegistrationRequired` operation must return the current registration policy.
- When registered object data is read, the reading session must associate every class with the same numeric ID and compatible serializer configuration used by the writing session.

**Serializer selection.**

- When `getSerializer` receives a registered or implicitly registrable type, it must return the serializer held by that type's registration.
- When `addDefaultSerializer` associates a base type with a serializer or factory, later registration of a matching subtype must use the most specific matching default entry, with insertion order resolving equally specific matches.
- When no added default entry matches, `getDefaultSerializer` must return an instance supplied by the global default serializer policy configured by `setDefaultSerializer`.
- If `setDefaultSerializer` or `addDefaultSerializer` receives a null required argument, then it must raise `IllegalArgumentException`.

**Resolver contract.**

- When a `Kryo` instance is constructed with a `ClassResolver`, it must call `setKryo` on that resolver and route registration lookup, class writing, class reading, implicit registration, and reset through it.
- The `getClassResolver` operation must return the active resolver, and `getRegistration(int)` must return the resolver's registration for that ID or null when none exists.

## Binary Input and Output

This section defines buffer lifecycle, stream bridging, paired primitive encodings, and size protection for the core `Input` and `Output` types.

**Construction and buffer lifecycle.**

- When zero-argument `Output` is constructed, it must remain uninitialized until `setBuffer` supplies a byte array.
- When zero-argument `Input` is constructed, it must remain uninitialized until `setBuffer` supplies a byte array.
- When `Output.setBuffer` installs a byte array, it must use that array directly, clear the output-stream association, and reset `position` and `total` to zero.
- When `Input.setBuffer` installs a byte array with an offset and count, it must use that array directly, set the readable range to the requested slice, clear the input-stream association, and reset `total` to zero.
- When `Output.setOutputStream` installs a stream, it must discard buffered state and reset `position` and `total` to zero.
- When `Input.setInputStream` installs a stream, it must discard buffered state and reset its position, limit, and total for streamed reading.
- The `Output.position`, `Input.position`, `Input.limit`, and `total` operations must expose the current public cursor and cumulative byte-count views.
- When `reset` is called on `Input` or `Output`, it must set position and total to zero without changing the configured backing storage.

**Writing and reading bytes.**

- When bytes are written to an `Output` backed only by an expandable buffer, it must grow up to `maxBufferSize`, where `-1` denotes no configured maximum.
- When buffered `Output` data reaches an associated `OutputStream`, `flush` must write the pending bytes, flush the stream, add those bytes to `total`, and reset the buffer position.
- When `Output.close` is called, it must flush pending bytes and close the associated stream when one exists.
- When `Input` exhausts its current buffer and has an associated `InputStream`, it must refill the buffer and continue the requested read.
- When `Input.close` is called, it must close the associated stream when one exists.
- When `Input.read` is called at end of data, it must return `-1`, and `end` must return true.
- The `Input.available` operation must return the buffered unread byte count plus the associated stream's available byte count.
- If a required read extends beyond all available bytes, then `Input` must raise `KryoBufferUnderflowException`.
- If a required write exceeds the configured maximum after flushing or growth, then `Output` must raise `KryoBufferOverflowException`.

**Primitive and string pairs.**

- When `writeByte`, `writeShort`, `writeChar`, `writeBoolean`, `writeInt`, `writeLong`, `writeFloat`, or `writeDouble` writes a value, the correspondingly named read operation must return the same value subject to the Java primitive type.
- When `writeVarInt` or `writeVarLong` writes a value with an `optimizePositive` setting, the matching read operation with the same setting must return the original value and the write operation must return the encoded byte count.
- The `varIntLength` and `varLongLength` operations must return the byte counts that the corresponding variable-length write operations produce for the same value and `optimizePositive` setting.
- When `canReadInt`, `canReadVarInt`, `canReadLong`, or `canReadVarLong` returns true, a complete value for the corresponding configured encoding must be readable without the availability check consuming that numeric value.
- Where variable-length encoding is enabled, `writeInt` and `writeLong` overloads that accept `optimizePositive` must use variable-length encoding; where it is disabled, those overloads must use fixed-width encoding.
- When `writeString` writes null, an empty string, ASCII text, or non-ASCII text, `readString` must reproduce the same nullable text value.
- When `writeAscii` receives only ASCII text, `readString` and `readStringBuilder` must reproduce the same nullable text content.
- If `writeAscii` receives non-ASCII text, then the method must not guarantee a lossless result.

**Bulk values and bounds.**

- When the primitive-array write operations write the selected offset and count, the corresponding primitive-array read operations must reproduce the selected values in order.
- When `readBytes` receives a length, it must return exactly that many bytes and advance the input position by that length.
- While reading a declared array, string, collection, or map size from a byte-array-backed `Input`, an impossible size beyond the remaining bytes must raise `KryoException` before allocation.
- Where `setMaxArraySize` configures a non-negative bound, a declared element count above that bound must raise `KryoException` before allocation.
- When `validateArrayLength` receives a feasible declared length and element width within the active bound, it must return that length; otherwise it must raise `KryoException` before allocation.
- If `setMaxArraySize` receives a negative value, then it must raise `IllegalArgumentException`.
- If an `Output` buffer size exceeds its finite maximum, or its maximum is less than `-1`, then construction or `setBuffer` must raise `IllegalArgumentException`.

## References, Context, and Reset

This section defines identity preservation and the lifecycle state shared by serializers during one or more object graphs.

**Reference identity.**

- The `getReferences` operation must return false for a newly constructed default `Kryo` instance.
- When `setReferences(true)` is called without an installed resolver, the session must install a `MapReferenceResolver`, enable serialization references, and return the previous setting.
- While serialization references are enabled for a type, repeated appearances of one object in a graph must deserialize as the same object identity.
- While serialization references are enabled for a type, circular graphs must round trip with their cycles restored.
- While serialization references are disabled, repeated appearances of a serializable object must deserialize as distinct objects, and a circular graph must fail rather than produce a restored cycle.
- When `setReferenceResolver` receives a non-null resolver, the session must install it and enable references.
- The `getReferenceResolver` operation must return the active resolver, or null when the session has never installed one.
- If `setReferenceResolver` receives null, then it must raise `IllegalArgumentException`.

**Resolver callbacks.**

- When an object is first written with references active, the session must obtain a new ID through `addWrittenObject`; when it is written again, the session must obtain its prior ID through `getWrittenId`.
- When an object is first read with references active, the session must reserve an ID through `nextReadId`, associate the decoded object through `setReadObject`, and resolve later occurrences through `getReadObject`.
- Where a resolver's `useReferences` returns false for a type, the session must skip identity tracking for values of that type.
- When `reset` is called, the session must invoke `reset` on the active class resolver and, while references are enabled, on the active reference resolver.

**Serializer-visible graph state.**

- The `getContext` operation must return a mutable name-value map whose entries persist across graph completion and explicit reset.
- The `getGraphContext` operation must return a mutable name-value map whose entries remain visible to serializers during the current graph.
- When a complete top-level read or write finishes while auto-reset is enabled, the session must clear graph context, class-resolver graph state, reference-resolver graph state, and copy bookkeeping.
- Where `setAutoReset(false)` is active, graph-scoped state must persist after a top-level operation until `reset` is called explicitly.
- While a serializer callback is nested in an object graph, `getDepth` must report its distance from the root, and graph completion must restore depth to zero.
- If `setMaxDepth` receives a value less than one, then it must raise `IllegalArgumentException`; otherwise a graph deeper than the configured maximum must raise `KryoException`.

## Deep and Shallow Copying

This section defines direct object copying through serializer callbacks and application-supplied `KryoCopyable` callbacks.

**Copy selection.**

- When `copy` receives null, it must return null.
- When `copy` receives a non-null object, it must use that object's `KryoCopyable.copy` callback when implemented, otherwise it must use the selected `Serializer.copy` callback.
- When `copy` completes for a non-immutable object with a supported copy callback, it must return a distinct root whose supported descendants are copied recursively.
- When `copyShallow` completes for a non-immutable object with a supported copy callback, it must return a distinct root while retaining the original references for nested descendants.
- When a serializer argument is supplied to a copy operation for a non-`KryoCopyable` object, the operation must use that serializer instead of the registered serializer.

**Identity and immutable values.**

- While copy-reference tracking is enabled, repeated appearances of one source object must map to one copied object and circular relationships must be preserved.
- Where `setCopyReferences(false)` is active, repeated appearances must be copied independently and a circular copy must fail rather than return a preserved cycle.
- When `Serializer.setImmutable(true)` is active, the default `Serializer.copy` implementation must return the original object.
- If a non-immutable serializer does not implement copying, then its default `Serializer.copy` must raise `KryoException`.
- When a copy callback creates a parent whose child is permitted to reference it, the callback must call `Kryo.reference` with the copy before copying that child.

## State Model

The core state is one configured `Kryo` session plus the current byte and object-graph cursors. Its public projections are:

1. the registration projection exposed by `Registration`, `getRegistration`, `getSerializer`, and the active `ClassResolver`;
2. the binary projection exposed by `Output` bytes, positions, totals, and the matching `Input` cursor;
3. the reconstructed graph projection exposed by typed and runtime-class read operations;
4. the identity projection exposed by reference-preserving reads and the active `ReferenceResolver`;
5. the serializer projection exposed by callbacks, `getContext`, `getGraphContext`, and `getDepth`; and
6. the copy projection exposed by deep or shallow results and repeated-reference topology.

The registration configuration and general context persist until changed by the caller. Graph context, reference IDs, implicit class-name state, and depth belong to graph-scoped state and follow the auto-reset policy.

## Error Semantics

| Condition | Required result |
|---|---|
| A required `Kryo`, `Input`, `Output`, type, serializer, resolver, registration type, buffer, or instantiator argument is null | Raise `IllegalArgumentException` |
| A class is unregistered while registration is required | Raise `IllegalArgumentException` |
| An explicit registration ID is negative | Raise `IllegalArgumentException` |
| A maximum depth is less than one | Raise `IllegalArgumentException` |
| A maximum array size is negative | Raise `IllegalArgumentException` |
| An output initial size exceeds its finite maximum, or the maximum is below `-1` | Raise `IllegalArgumentException` |
| A required read exceeds all available bytes | Raise `KryoBufferUnderflowException` |
| A required write exceeds the finite output maximum | Raise `KryoBufferOverflowException` |
| A declared container or string size violates the active safety bound | Raise `KryoException` before allocation |
| A reference ID does not resolve to a previously read object | Raise `KryoException` |
| A graph exceeds the configured maximum depth | Raise `KryoException` |
| A non-immutable serializer has no copy implementation | Raise `KryoException` |

Exception message wording is not part of the contract.

## Cross-View Invariants

1. When registration and serializer configuration agree, an object written through a known-type write operation must be readable through the matching known-type read operation.
2. When an object is written through `writeClassAndObject`, it must return through `readClassAndObject` with a runtime type and registration consistent with the writing session.
3. The `Registration` returned by `register` must be the same registration observed through `getRegistration` by type and by ID, and its serializer must be the one returned by `getSerializer`.
4. When an `Output` readable range is passed to `Input`, it must end at `Output.position`, and consuming that range must advance the input cursor consistently with the values decoded.
5. Where references are enabled, the byte projection and reconstructed graph projection must agree on repeated identity and circular relationships.
6. Where auto-reset is enabled, completing a top-level graph must preserve registrations and general context while clearing graph context, resolver graph state, and depth.
7. Where auto-reset is disabled, serializer callbacks in consecutive top-level operations must observe the same graph context and resolver state until explicit `reset`.
8. Where a non-immutable root has supported copy callbacks, the deep-copy projection must preserve supported values and repeated-reference topology without sharing mutable copied descendants with the source graph.
9. Where a non-immutable root has a supported copy callback, the shallow-copy projection must preserve root values while sharing nested descendant identities with the source graph.
10. When a custom serializer is selected by registration, explicit method argument, or default selection, it must govern both the byte representation and the reconstructed or copied result for that operation.

## Public Interface

### Import Surface

```java
import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.Registration;
import com.esotericsoftware.kryo.Serializer;
import com.esotericsoftware.kryo.ClassResolver;
import com.esotericsoftware.kryo.ReferenceResolver;
import com.esotericsoftware.kryo.KryoSerializable;
import com.esotericsoftware.kryo.KryoCopyable;
import com.esotericsoftware.kryo.KryoException;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;
import com.esotericsoftware.kryo.io.KryoBufferOverflowException;
import com.esotericsoftware.kryo.io.KryoBufferUnderflowException;
import com.esotericsoftware.kryo.util.DefaultClassResolver;
import com.esotericsoftware.kryo.util.MapReferenceResolver;
import com.esotericsoftware.kryo.util.HashMapReferenceResolver;
import com.esotericsoftware.kryo.util.ListReferenceResolver;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Kryo` | class | Owns registration, serializer dispatch, graph state, reference handling, and copying. |
| `Kryo.register` | method | Create and query class registrations. |
| `Kryo.getRegistration` | method | Create and query class registrations. |
| `Kryo.getNextRegistrationId` | method | Create and query class registrations. |
| `Kryo.getSerializer` | method | Select and configure serializers. |
| `Kryo.getDefaultSerializer` | method | Select and configure serializers. |
| `Kryo.addDefaultSerializer` | method | Select and configure serializers. |
| `Kryo.setDefaultSerializer` | method | Select and configure serializers. |
| `Kryo.writeClass` | method | Encode and decode class registrations. |
| `Kryo.readClass` | method | Encode and decode class registrations. |
| `Kryo.writeObject` | method | Write and read non-null known-type objects. |
| `Kryo.readObject` | method | Write and read non-null known-type objects. |
| `Kryo.writeObjectOrNull` | method | Write and read nullable known-type objects. |
| `Kryo.readObjectOrNull` | method | Write and read nullable known-type objects. |
| `Kryo.writeClassAndObject` | method | Write and read nullable runtime-typed objects. |
| `Kryo.readClassAndObject` | method | Write and read nullable runtime-typed objects. |
| `Kryo.reference` | method | Control and participate in serialization identity tracking. |
| `Kryo.setReferences` | method | Control and participate in serialization identity tracking. |
| `Kryo.getReferences` | method | Control and participate in serialization identity tracking. |
| `Kryo.setReferenceResolver` | method | Control and participate in serialization identity tracking. |
| `Kryo.getReferenceResolver` | method | Control and participate in serialization identity tracking. |
| `Kryo.getContext` | method | Expose and control serializer-visible graph lifecycle state. |
| `Kryo.getGraphContext` | method | Expose and control serializer-visible graph lifecycle state. |
| `Kryo.getDepth` | method | Expose and control serializer-visible graph lifecycle state. |
| `Kryo.setAutoReset` | method | Expose and control serializer-visible graph lifecycle state. |
| `Kryo.reset` | method | Expose and control serializer-visible graph lifecycle state. |
| `Kryo.setMaxDepth` | method | Expose and control serializer-visible graph lifecycle state. |
| `Kryo.copy` | method | Produce direct deep graph copies. |
| `Kryo.copyShallow` | method | Produce direct shallow graph copies. |
| `Kryo.setCopyReferences` | method | Configure identity tracking during graph copies. |
| `Kryo.getClassResolver` | method | Expose the resolver, registration policy, and registered construction path. |
| `Kryo.setRegistrationRequired` | method | Expose the resolver, registration policy, and registered construction path. |
| `Kryo.isRegistrationRequired` | method | Expose the resolver, registration policy, and registered construction path. |
| `Kryo.newInstance` | method | Expose the resolver, registration policy, and registered construction path. |
| `Registration` | class | Associates a type, numeric ID, serializer, and optional object instantiator. |
| `Registration.getType` | method | Read or update public registration metadata. |
| `Registration.getId` | method | Read or update public registration metadata. |
| `Registration.getSerializer` | method | Read or update public registration metadata. |
| `Registration.setSerializer` | method | Read or update public registration metadata. |
| `Registration.getInstantiator` | method | Read or update public registration metadata. |
| `Registration.setInstantiator` | method | Read or update public registration metadata. |
| `Serializer` | abstract class | Defines object write, read, null-handling, immutability, and copy callbacks. |
| `Serializer.write` | method | Implement and configure serializer behavior. |
| `Serializer.read` | method | Implement and configure serializer behavior. |
| `Serializer.copy` | method | Implement and configure serializer behavior. |
| `Serializer.getAcceptsNull` | method | Implement and configure serializer behavior. |
| `Serializer.setAcceptsNull` | method | Implement and configure serializer behavior. |
| `Serializer.isImmutable` | method | Implement and configure serializer behavior. |
| `Serializer.setImmutable` | method | Implement and configure serializer behavior. |
| `KryoSerializable` | interface | Lets an application type supply its own write and read callbacks. |
| `KryoSerializable.write` | method | Move an implementing object to and from the active byte stream. |
| `KryoSerializable.read` | method | Move an implementing object to and from the active byte stream. |
| `KryoCopyable` | interface | Lets an application type supply its own copy callback. |
| `KryoCopyable.copy` | method | Creates an application-defined copy through the active session. |
| `ClassResolver` | interface | Defines registration storage and class identifier encoding callbacks. |
| `ClassResolver.setKryo` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.register` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.unregister` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.registerImplicit` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.getRegistration` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.writeClass` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.readClass` | method | Connect a class resolver to the session lifecycle. |
| `ClassResolver.reset` | method | Connect a class resolver to the session lifecycle. |
| `DefaultClassResolver` | class | Supplies the standard class-registration and class-identifier behavior. |
| `ReferenceResolver` | interface | Defines written-object IDs, read-object lookup, per-type participation, and reset. |
| `ReferenceResolver.setKryo` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.getWrittenId` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.addWrittenObject` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.nextReadId` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.setReadObject` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.getReadObject` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.useReferences` | method | Connect identity storage to the session lifecycle. |
| `ReferenceResolver.reset` | method | Connect identity storage to the session lifecycle. |
| `MapReferenceResolver` | class | Supplies the default identity-based reference resolver. |
| `HashMapReferenceResolver` | class | Supplies identity tracking backed by a hash map. |
| `ListReferenceResolver` | class | Supplies identity tracking optimized for small graphs. |
| `Input` | class | Reads buffered bytes, primitives, strings, arrays, and stream data. |
| `Input.setBuffer` | method | Configure and observe input storage and cursor state. |
| `Input.getBuffer` | method | Configure and observe input storage and cursor state. |
| `Input.setInputStream` | method | Configure and observe input storage and cursor state. |
| `Input.getInputStream` | method | Configure and observe input storage and cursor state. |
| `Input.position` | method | Configure and observe input storage and cursor state. |
| `Input.setPosition` | method | Configure and observe input storage and cursor state. |
| `Input.limit` | method | Configure and observe input storage and cursor state. |
| `Input.setLimit` | method | Configure and observe input storage and cursor state. |
| `Input.total` | method | Configure and observe input storage and cursor state. |
| `Input.setTotal` | method | Configure and observe input storage and cursor state. |
| `Input.reset` | method | Configure and observe input storage and cursor state. |
| `Input.end` | method | Configure and observe input storage and cursor state. |
| `Input.available` | method | Configure and observe input storage and cursor state. |
| `Input.skip` | method | Configure and observe input storage and cursor state. |
| `Input.close` | method | Configure and observe input storage and cursor state. |
| `Input.read` | method | Read raw byte values and ranges. |
| `Input.readByte` | method | Read raw byte values and ranges. |
| `Input.readByteUnsigned` | method | Read raw byte values and ranges. |
| `Input.readBytes` | method | Read raw byte values and ranges. |
| `Input.readShort` | method | Read fixed-width and configured primitive values. |
| `Input.readShortUnsigned` | method | Read fixed-width and configured primitive values. |
| `Input.readChar` | method | Read fixed-width and configured primitive values. |
| `Input.readBoolean` | method | Read fixed-width and configured primitive values. |
| `Input.readInt` | method | Read fixed-width and configured primitive values. |
| `Input.readLong` | method | Read fixed-width and configured primitive values. |
| `Input.readFloat` | method | Read fixed-width and configured primitive values. |
| `Input.readDouble` | method | Read fixed-width and configured primitive values. |
| `Input.readVarInt` | method | Read variable-length numeric values and inspect availability. |
| `Input.readVarLong` | method | Read variable-length numeric values and inspect availability. |
| `Input.readVarFloat` | method | Read variable-length numeric values and inspect availability. |
| `Input.readVarDouble` | method | Read variable-length numeric values and inspect availability. |
| `Input.canReadInt` | method | Read variable-length numeric values and inspect availability. |
| `Input.canReadVarInt` | method | Read variable-length numeric values and inspect availability. |
| `Input.canReadLong` | method | Read variable-length numeric values and inspect availability. |
| `Input.canReadVarLong` | method | Read variable-length numeric values and inspect availability. |
| `Input.readString` | method | Read nullable ASCII or UTF-8 text. |
| `Input.readStringBuilder` | method | Read nullable ASCII or UTF-8 text. |
| `Input.readInts` | method | Read primitive arrays. |
| `Input.readLongs` | method | Read primitive arrays. |
| `Input.readFloats` | method | Read primitive arrays. |
| `Input.readDoubles` | method | Read primitive arrays. |
| `Input.readShorts` | method | Read primitive arrays. |
| `Input.readChars` | method | Read primitive arrays. |
| `Input.readBooleans` | method | Read primitive arrays. |
| `Input.getVariableLengthEncoding` | method | Configure numeric encoding and declared-size safety. |
| `Input.setVariableLengthEncoding` | method | Configure numeric encoding and declared-size safety. |
| `Input.getMaxArraySize` | method | Configure numeric encoding and declared-size safety. |
| `Input.setMaxArraySize` | method | Configure numeric encoding and declared-size safety. |
| `Input.validateArrayLength` | method | Configure numeric encoding and declared-size safety. |
| `Output` | class | Writes buffered bytes, primitives, strings, arrays, and stream data. |
| `Output.setBuffer` | method | Configure and observe output storage and cursor state. |
| `Output.getBuffer` | method | Configure and observe output storage and cursor state. |
| `Output.toBytes` | method | Configure and observe output storage and cursor state. |
| `Output.setOutputStream` | method | Configure and observe output storage and cursor state. |
| `Output.getOutputStream` | method | Configure and observe output storage and cursor state. |
| `Output.position` | method | Configure and observe output storage and cursor state. |
| `Output.setPosition` | method | Configure and observe output storage and cursor state. |
| `Output.total` | method | Configure and observe output storage and cursor state. |
| `Output.getMaxCapacity` | method | Configure and observe output storage and cursor state. |
| `Output.reset` | method | Configure and observe output storage and cursor state. |
| `Output.flush` | method | Configure and observe output storage and cursor state. |
| `Output.close` | method | Configure and observe output storage and cursor state. |
| `Output.write` | method | Write raw byte values and ranges. |
| `Output.writeByte` | method | Write raw byte values and ranges. |
| `Output.writeBytes` | method | Write raw byte values and ranges. |
| `Output.writeShort` | method | Write fixed-width and configured primitive values. |
| `Output.writeChar` | method | Write fixed-width and configured primitive values. |
| `Output.writeBoolean` | method | Write fixed-width and configured primitive values. |
| `Output.writeInt` | method | Write fixed-width and configured primitive values. |
| `Output.writeLong` | method | Write fixed-width and configured primitive values. |
| `Output.writeFloat` | method | Write fixed-width and configured primitive values. |
| `Output.writeDouble` | method | Write fixed-width and configured primitive values. |
| `Output.writeVarInt` | method | Write variable-length numeric values and report encoded lengths. |
| `Output.writeVarLong` | method | Write variable-length numeric values and report encoded lengths. |
| `Output.writeVarFloat` | method | Write variable-length numeric values and report encoded lengths. |
| `Output.writeVarDouble` | method | Write variable-length numeric values and report encoded lengths. |
| `Output.varIntLength` | method | Write variable-length numeric values and report encoded lengths. |
| `Output.varLongLength` | method | Write variable-length numeric values and report encoded lengths. |
| `Output.writeString` | method | Write nullable UTF-8 or ASCII text. |
| `Output.writeAscii` | method | Write nullable UTF-8 or ASCII text. |
| `Output.writeInts` | method | Write primitive arrays. |
| `Output.writeLongs` | method | Write primitive arrays. |
| `Output.writeFloats` | method | Write primitive arrays. |
| `Output.writeDoubles` | method | Write primitive arrays. |
| `Output.writeShorts` | method | Write primitive arrays. |
| `Output.writeChars` | method | Write primitive arrays. |
| `Output.writeBooleans` | method | Write primitive arrays. |
| `Output.getVariableLengthEncoding` | method | Configure the numeric overload encoding policy. |
| `Output.setVariableLengthEncoding` | method | Configure the numeric overload encoding policy. |
| `KryoException` | exception | Reports serialization, deserialization, graph-depth, size, reference, and unsupported-copy failures. |
| `KryoBufferOverflowException` | exception | Reports a write beyond the finite output capacity. |
| `KryoBufferUnderflowException` | exception | Reports a required read beyond available input. |

### CLI Entry Points

There is no console script or executable main class for this package. Programmatic use is through Java imports and the Maven artifact.

## Appendix A: Environment

The working environment runs a Linux JDK with Java 8-compatible source and bytecode and Maven without network access. The following third-party Maven artifacts are preinstalled and resolvable: `com.esotericsoftware:reflectasm`, `org.objenesis:objenesis`, and `com.esotericsoftware:minlog`. The assessment environment provides the same JDK and artifact set. The target library is not preinstalled.

The project must declare standard Maven packaging metadata in a root `pom.xml`. It must provide the coordinate `com.esotericsoftware:kryo` and compile its production sources into the corresponding JAR without downloading additional dependencies.

## Appendix B: Assessment Notes

Assessment covers public symbol availability, registration and serializer dispatch, typed and runtime-class round trips, nullable values, buffer and primitive I/O, size and cursor boundaries, reference identity and cycles, serializer callbacks, reset/context lifecycle, and deep or shallow copying. Checks use observable values, exception types, object identity, callback effects, and cross-component workflows; they do not depend on private fields, exact exception text, log wording, historical byte fixtures, unsafe classes, or specialized serializer implementations.
