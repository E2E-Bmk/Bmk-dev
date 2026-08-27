# Memberlist Specification

═══ Context Layer ═══

## Product Overview

Memberlist is a Go cluster-membership library that converges node identity, health, metadata, and leave state through gossip and push-pull exchange. The installable module name is github.com/hashicorp/memberlist.

The supported topology uses MockNetwork and MockTransport only. Public callers observe membership through Members, NumMembers, LocalNode, Node fields, delegate callbacks, transmitted user messages, dissemination queues, keyrings, health score, and lifecycle methods.

The transcript package adds a deterministic topology transcript for applications that reconcile membership generations, merges, broadcasts, suspicions, encryption keys, metadata, and leave tombstones. It records caller-supplied observations and never opens a transport or advances a clock.

## Non-Goals

- This specification does not require operating-system sockets, DNS, routable addresses, or traffic between processes.
- This specification does not define durable membership after all Memberlist instances stop.
- This specification does not require a metrics sink or external logging service.
- This specification does not define application payload encoding for Delegate.NotifyMsg.
- This specification does not require packet loss or clock-skew simulation.

═══ Orientation Layer ═══

## Representative Workflows

The first workflow creates two nodes on one MockNetwork, joins the second node to the first, and observes the same live membership through direct queries and delegate events.

~~~go
network := &memberlist.MockNetwork{}
transportA := network.NewTransport("node-a")
transportB := network.NewTransport("node-b")

events := make(chan memberlist.NodeEvent, 16)
cfgA := memberlist.DefaultLocalConfig()
cfgA.Name = "node-a"
cfgA.Transport = transportA
cfgA.Events = &memberlist.ChannelEventDelegate{Ch: events}

cfgB := memberlist.DefaultLocalConfig()
cfgB.Name = "node-b"
cfgB.Transport = transportB
metadata := &metadataDelegate{Value: []byte("green")}
cfgB.Delegate = metadata

nodeA, err := memberlist.Create(cfgA)
if err != nil {
    panic(err)
}
nodeB, err := memberlist.Create(cfgB)
if err != nil {
    panic(err)
}

seed := nodeA.LocalNode()
contact := seed.Name + "/" + seed.Address()
if _, err := nodeB.Join([]string{contact}); err != nil {
    panic(err)
}
_ = nodeA.Members()
_ = nodeB.NumMembers()
~~~

The second workflow changes local metadata, waits for the remote update event, leaves gracefully, and then closes both membership instances and their in-memory transports.

~~~go
metadata.Value = []byte("blue")
if err := nodeB.UpdateNode(time.Second); err != nil {
    panic(err)
}

for {
    event := <-events
    if event.Event == memberlist.NodeUpdate && event.Node.Name == "node-b" {
        break
    }
}

if err := nodeB.Leave(time.Second); err != nil {
    panic(err)
}
if err := nodeB.Shutdown(); err != nil {
    panic(err)
}
if err := nodeA.Shutdown(); err != nil {
    panic(err)
}
~~~

The third workflow records two alive generations, a metadata change, and a leave tombstone in one isolated topology view.

~~~go
topology := transcript.NewTopology()
alive, err := topology.RecordAlive("node-a", 1, 1, []byte("zone=one"))
if err != nil {
    panic(err)
}
_, _ = topology.RecordMetadata("node-a", 2, []byte("zone=two"))
left, err := topology.RecordLeave("node-a", 3)
if err != nil {
    panic(err)
}
_ = alive
_ = left
_ = topology.Snapshot()
~~~

═══ Behavior Layer ═══

## Membership Convergence and Incarnations

Membership convergence resolves competing alive information by node identity, incarnation, address, metadata, and protocol range.

**Creation and local view.** Create must validate Config, establish the configured Transport, advertise one local alive record, start background membership activity, and return a Memberlist containing its own Node. Memberlist must own the Config value after Create. LocalNode must return the local Node view. Node.Address must return the host and port address, FullAddress must pair it with the node name, and String must return the node name. Members must return every known node whose state is neither StateDead nor StateLeft, and NumMembers must count the same live set at the observation instant.

**Alive precedence.** When an alive record for a remote node has an incarnation greater than the stored incarnation, the member view must adopt its address, port, metadata, protocol versions, and StateAlive. When a remote alive record has an incarnation less than or equal to the stored incarnation, the member view must ignore it unless a previously dead address is eligible for reclamation. When a local alive record repeats the current incarnation with identical metadata and versions, the local member must ignore it. When that equal-incarnation local record differs, the local member must refute it with a higher incarnation rather than adopt its values.

**Admission delegates.** Where AliveDelegate is configured, NotifyAlive must receive the proposed Node before it enters membership. If NotifyAlive returns an error, then the proposed node must not appear in Members and no join or update event must be emitted. Where MergeDelegate is configured, NotifyMerge must receive the peer's known nodes during a join push-pull; if it returns an error, then the merge must fail without adding those peers. A detected duplicate name at a different live address must invoke ConflictDelegate and must retain the existing node.

**Event delegates.** A transition from absent, dead, or left to alive must invoke EventDelegate.NotifyJoin. An accepted metadata change for an already live node must invoke NotifyUpdate. A transition to left or dead must invoke NotifyLeave. ChannelEventDelegate must send NodeJoin, NodeUpdate, and NodeLeave values with the corresponding Node to its Ch channel in callback order. If the channel has no capacity and no receiver, then the callback must remain blocked rather than discard the event.

## Join, Probing, and Suspicion

Join and failure detection connect MockTransport exchange, push-pull merge, probe outcomes, suspicion confirmation, and health awareness.

**Mock transport routing.** MockNetwork.NewTransport must allocate a distinct address and register lookup by both address and node name. MockTransport.WriteToAddress must deliver a Packet with source address, bytes, and timestamp to the destination PacketCh. DialAddressTimeout must return one end of an in-memory full-duplex stream and deliver the other end through the destination StreamCh. If no peer matches the requested Address, then packet or stream operations must return a no-route error and must not alter membership. Shutdown must return nil and leave prior membership cleanup to Memberlist.Shutdown.

**Joining.** Join must attempt each supplied contact through the configured Transport and perform a push-pull state exchange. It must return the number of successfully contacted hosts. If at least one contact succeeds, then Join must return that positive count and a nil error. If none succeeds, then Join must return zero and an error. A successful two-way merge must expose accepted live nodes in Members on both sides and must emit the corresponding join events.

**Suspicion and refutation.** When a direct and indirect probe fail for a live remote node, the member must enter StateSuspect and disseminate that suspicion. Distinct confirmations from other nodes must shorten the remaining suspicion interval toward its minimum; repeated confirmation from the same node must not count twice. When the suspect interval expires without an accepted alive refutation, the node must become StateDead and leave the Members view. When a suspect node emits a higher-incarnation alive record before expiry, the member must cancel the pending suspicion, restore StateAlive, and retain the newer incarnation data.

**Awareness.** GetHealthScore must return zero for the healthiest local state and a value below AwarenessMaxMultiplier. Failed probes and degraded local processing must increase the score, successful probes must decrease it toward zero, and probe scheduling must scale its interval by one plus the current score. Changes to awareness must affect timing only and must not directly change membership.

## Dissemination, Metadata, and Keys

Dissemination queues and keyrings control which current state is sent, how often it remains eligible, and which key protects outgoing traffic.

**Broadcast admission.** QueueBroadcast must add a Broadcast for later gossip. A NamedBroadcast with the same nonempty Name as an older queued value must replace that value and call Finished on the older value. A UniqueBroadcast must enter without scanning existing values for invalidation. Other Broadcast values must remove and finish every older value for which Invalidates returns true.

**Selection and completion.** GetBroadcasts must prefer lower transmission counts, choose entries that fit the supplied byte limit after per-message overhead, and increment the transmission count of every returned entry. The retransmission limit must equal RetransmitMult multiplied by the ceiling of the base-10 logarithm of NumNodes plus one. When an entry reaches that limit, the queue must remove it and call Finished exactly once. NumQueued must report the current count. Reset must finish and remove all queued values. Prune must retain no more than its requested count and must finish removed values.

**Node metadata.** Delegate.NodeMeta must receive a maximum length and its result must become LocalNode.Meta during Create and UpdateNode. If NodeMeta returns more than MetaMaxSize bytes, then Create or UpdateNode must panic before disseminating the oversized value. When UpdateNode succeeds, it must advance the local incarnation, broadcast one alive update, update LocalNode.Meta, and cause accepted peers to expose the same metadata and emit NodeUpdate. If a positive timeout expires before an available peer accepts the broadcast, then UpdateNode must return an error.

**Application state delegates.** Delegate.GetBroadcasts must receive per-message overhead and a byte limit and must return application broadcasts that fit that budget. LocalState must return application state for push-pull exchange and must receive true during a join exchange. MergeRemoteState must receive the peer bytes and the same join value after membership state is accepted. NotifyMsg must receive direct user-message bytes.

**Keyring ordering.** NewKeyring must accept no keys for unencrypted operation, one primary key, or a key set with a primary key. Every key must contain 16, 24, or 32 bytes. The primary key must occupy position zero, must encrypt outgoing traffic, and must be attempted first for incoming decryption. AddKey must add a valid absent key and must return nil for a duplicate. UseKey must move an installed key to position zero. RemoveKey must reject the current primary and must remove an installed non-primary key. GetPrimaryKey and GetKeys must expose the current ordering.

**Encrypted membership.** Where Config.Keyring or SecretKey enables encryption, outgoing protocol messages must use the primary key and incoming messages must be accepted with any installed key. After all peers add a replacement key and select it with UseKey, communication must continue across the change. If an incoming message uses no installed key, then it must not change membership, metadata, delegate events, or queued broadcasts.

## Leave, Shutdown, and User Messages

Lifecycle operations distinguish graceful leave dissemination from process-local shutdown and preserve transport delivery guarantees.

**Graceful leave.** Leave must mark the local node StateLeft and disseminate an intentional leave whose node and source identities match. If another live member exists, Leave must wait until the leave broadcast is sent or a positive timeout expires. Repeated Leave calls before shutdown must return nil without sending a second leave transition. Peers accepting the leave must remove the node from Members and emit NodeLeave.

**Shutdown.** Shutdown must stop Transport activity and background maintenance without sending a graceful leave. Repeated Shutdown calls must return nil. If Leave is called after Shutdown, then Leave must panic. After shutdown, no new metadata, membership, or delegate events must originate from that Memberlist instance.

**User messages.** SendBestEffort must deliver a packet-oriented user message through Transport and must return a transport error when delivery fails. SendReliable must deliver a stream-oriented user message and must guarantee delivery to Delegate.NotifyMsg when it returns nil. NotifyMsg receives transport-owned bytes; a Delegate retaining the data must copy it before the callback returns. PingDelegate.AckPayload must contribute acknowledgement payload bytes, and NotifyPingComplete must receive the remote Node, measured round-trip duration, and returned payload for successful direct probes.

## Topology Transcript

The transcript package records public membership observations without owning a Memberlist, Transport, Delegate, Broadcast queue, or Keyring. A Topology created by NewTopology begins empty. Generation is an unsigned monotonic value associated with a node or named record. Every accepted node identity and record name must be nonempty. TopologySnapshot must return isolated byte slices, maps, and ordered receipt lists.

**Alive precedence.** RecordAlive must accept only a newer incarnation, or an equal incarnation carrying a strictly newer metadata generation. Its metadata bytes must be copied before return. Repeating identical values must return the same AliveReceipt. A stale value must return ErrStaleGeneration and leave membership state unchanged.

**Join merge.** RecordJoin must merge each remote node by generation and return one ordered receipt containing only changed identities. Remote identities must be considered in lexical order regardless of map iteration. A remote generation below the accepted local generation must be ignored. MergeReceipt must preserve the contact identity and ordered changed identities.

**Broadcast supersession.** RecordBroadcast must retain only the newest generation for a name while preserving unrelated named and unique broadcasts. A newer named record replaces the earlier payload. A unique record receives an independent ordinal and does not replace another record. Repeating identical values must return the same BroadcastReceipt; a stale generation must return ErrStaleGeneration.

**Leave tombstones.** RecordLeave must create one terminal tombstone generation and prevent later non-newer alive receipts from restoring membership. A newer leave generation replaces an earlier tombstone. A newer alive incarnation whose metadata generation exceeds the tombstone must restore the node. LeaveReceipt must expose the prior accepted generation and the tombstone generation.

**Metadata updates.** RecordMetadata must advance one node generation, isolate copied bytes, and produce exactly one visible metadata receipt. The node must already have an AliveReceipt. Repeating the same generation and bytes must return the same MetadataReceipt. A stale generation or conflicting bytes at the same generation must return ErrStaleGeneration.

**Suspicion accounting.** RecordSuspicion must count distinct confirmations, preserve the earliest deadline, and clear suspicion only through a newer alive generation. Repeating a confirmer must not increase the count. A later deadline must not replace an earlier one. SuspicionReceipt must preserve the node, generation, sorted confirmer identities, deadline, and cleared state.

**Key acceptance.** RecordKeyUse must accept a packet only for a known key and identify whether that key is currently primary. Unknown keys must produce a KeyReceipt marked rejected without changing node, metadata, broadcast, or suspicion state. Repeating the same key observation must return the same receipt.

═══ Contract Layer ═══

## State Model

The product exposes eight connected projections:

1. Membership: known Node values and their alive, suspect, dead, or left states.
2. Incarnation: the monotonic precedence value for each node.
3. Transport: MockNetwork routes, packet channels, stream channels, and shutdown.
4. Delegates: join, update, leave, merge, conflict, alive, message, and ping callbacks.
5. Dissemination: queued Broadcast values, transmission counts, invalidation, and completion.
6. Encryption: installed keys, primary-key order, and packet acceptance.
7. Lifecycle and health: joined, left, shutdown, and awareness score.
8. Topology transcript: node generations, merge changes, broadcast supersession, tombstones, suspicions, key use, and isolated metadata bytes.

Every accepted protocol change must leave these projections consistent with the invariants below.

## Error Semantics

| Condition | Required result |
|---|---|
| Create receives invalid protocol bounds, name, transport, or address configuration | Create returns an error and no Memberlist |
| MockTransport cannot resolve a peer | The operation returns a no-route error and membership is unchanged |
| No Join contact succeeds | Join returns zero and an error |
| At least one Join contact succeeds | Join returns a positive count and nil |
| AliveDelegate rejects a proposed peer | The peer is not admitted and no event is emitted |
| MergeDelegate rejects a merge | Join returns an error for that contact and does not merge its peers |
| UpdateNode metadata exceeds MetaMaxSize | UpdateNode panics before dissemination |
| UpdateNode or Leave exceeds a positive broadcast timeout | The method returns an error |
| Leave follows Shutdown | Leave panics |
| A key length is not 16, 24, or 32 bytes | ValidateKey, AddKey, or NewKeyring returns an error |
| UseKey receives an absent key | UseKey returns an error and ordering is unchanged |
| RemoveKey receives the primary key | RemoveKey returns an error and ordering is unchanged |
| An incoming packet uses no installed key | The packet is rejected and public membership state is unchanged |
| SendBestEffort or SendReliable transport delivery fails | The method returns the transport error |
| A transcript operation supplies a stale or conflicting generation | The operation returns transcript.ErrStaleGeneration and TopologySnapshot remains unchanged |
| RecordMetadata names a node without an accepted alive receipt | RecordMetadata returns transcript.ErrStaleGeneration without creating the node |

## Cross-View Invariants

1. Members and NumMembers must agree on the live set, and every returned Node must carry the accepted incarnation's address, metadata, protocol bounds, and state.
2. A newly accepted node must appear in Members before its NodeJoin callback completes; a left or dead node must be absent when its NodeLeave callback completes.
3. An accepted higher-incarnation metadata update must be identical in LocalNode or Members, the disseminated alive value, and the NodeUpdate callback.
4. A rejected alive or merge decision must leave Members, NumMembers, broadcast queue, and event channel unchanged.
5. A NamedBroadcast replacement must leave only the newest value eligible for MockTransport delivery and must finish the displaced value exactly once.
6. A suspicion refuted by a higher incarnation must restore the same Node to StateAlive, cancel its pending dead transition, and disseminate the newer alive value.
7. GetHealthScore must alter probe timing without directly changing Node state, membership count, or delegate output.
8. The Keyring primary value must be the first key in GetKeys, the key used for outgoing encryption, and a key accepted by every peer before rotation completes.
9. An unknown encryption key must produce no accepted packet, no membership change, no metadata update, and no event callback.
10. A graceful Leave must produce a peer-visible StateLeft and NodeLeave before Shutdown ends local background activity.
11. Each accepted MetadataReceipt must agree with the metadata bytes and generation in the corresponding AliveReceipt and TopologySnapshot node view.
12. A LeaveReceipt tombstone must suppress every AliveReceipt that does not exceed its recorded generation boundary.
13. TopologySnapshot must preserve deterministic ordering and isolate every returned byte slice and collection from caller modification.

═══ Reference Layer ═══

## Public Interface

### Import Surface

~~~go
import (
    "github.com/hashicorp/memberlist"
    "github.com/hashicorp/memberlist/transcript"
)
~~~

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Config | type | Configures identity, transport, protocol timing, delegates, encryption, and queues. |
| transcript.Topology | type | Records deterministic membership observations and generations. |
| transcript.NewTopology | function | Creates an empty topology transcript. |
| transcript.Generation | type | Represents one monotonic node or named-record generation. |
| transcript.AliveReceipt | type | Captures accepted incarnation and metadata generation. |
| transcript.MergeReceipt | type | Captures an ordered set of identities changed by a join. |
| transcript.BroadcastReceipt | type | Captures named supersession or unique admission. |
| transcript.LeaveReceipt | type | Captures a terminal membership tombstone. |
| transcript.MetadataReceipt | type | Captures isolated metadata bytes and generation. |
| transcript.SuspicionReceipt | type | Captures confirmations, deadline, and cleared state. |
| transcript.KeyReceipt | type | Captures known, primary, and accepted key status. |
| transcript.TopologySnapshot | type | Exposes an isolated deterministic transcript view. |
| transcript.ErrStaleGeneration | error | Reports stale or conflicting transcript input. |
| transcript.Topology.RecordAlive | method | Records incarnation and metadata precedence. |
| transcript.Topology.RecordJoin | method | Merges remote generations in deterministic order. |
| transcript.Topology.RecordBroadcast | method | Records named or unique dissemination. |
| transcript.Topology.RecordLeave | method | Records a leave tombstone generation. |
| transcript.Topology.RecordMetadata | method | Records an isolated metadata generation. |
| transcript.Topology.RecordSuspicion | method | Records distinct suspicion confirmations. |
| transcript.Topology.RecordKeyUse | method | Records encryption-key acceptance. |
| transcript.Topology.Snapshot | method | Returns an isolated topology projection. |
| DefaultLANConfig | function | Returns a local-area baseline configuration. |
| DefaultWANConfig | function | Returns a wide-area baseline configuration. |
| DefaultLocalConfig | function | Returns an isolated-host baseline configuration. |
| ParseCIDRs | function | Parses allowed network ranges. |
| Config.BuildVsnArray | method | Returns protocol and delegate version bounds. |
| Config.IPAllowed | method | Validates an address against allowed ranges. |
| Config.EncryptionEnabled | method | Reports whether encryption is configured. |
| ProtocolVersionMin | constant | Defines the minimum supported membership protocol. |
| ProtocolVersionMax | constant | Defines the maximum supported membership protocol. |
| MetaMaxSize | constant | Defines the maximum node metadata size. |
| Memberlist | type | Coordinates membership, dissemination, health, and lifecycle. |
| Create | function | Creates an unjoined membership instance. |
| Memberlist.Join | method | Merges state through supplied contacts. |
| Memberlist.LocalNode | method | Returns the local Node view. |
| Memberlist.UpdateNode | method | Advances and disseminates local metadata. |
| Memberlist.Members | method | Returns known nodes not dead or left. |
| Memberlist.NumMembers | method | Counts known nodes not dead or left. |
| Memberlist.SendBestEffort | method | Sends a packet-oriented user message. |
| Memberlist.SendReliable | method | Sends a stream-oriented user message. |
| Memberlist.Ping | method | Measures one direct probe. |
| Memberlist.Leave | method | Disseminates intentional departure. |
| Memberlist.GetHealthScore | method | Returns local awareness score. |
| Memberlist.ProtocolVersion | method | Returns the active protocol version. |
| Memberlist.Shutdown | method | Stops transport and background activity. |
| Node | type | Exposes member identity, address, metadata, state, and protocol bounds. |
| Node.Address | method | Returns the host and port address. |
| Node.FullAddress | method | Returns name and address for Transport. |
| Node.String | method | Returns the node name. |
| NodeStateType | type | Represents alive, suspect, dead, and left states. |
| StateAlive | constant | Identifies a live node. |
| StateSuspect | constant | Identifies a node under failure suspicion. |
| StateDead | constant | Identifies a failed node. |
| StateLeft | constant | Identifies an intentional departure. |
| Address | type | Holds a transport address and optional node name. |
| Address.String | method | Formats name and address. |
| Packet | type | Carries packet bytes, source, and timestamp. |
| Transport | interface | Carries packet and stream membership traffic. |
| NodeAwareTransport | interface | Adds named-address transport operations. |
| MockNetwork | type | Registers in-memory transports by name and address. |
| MockNetwork.NewTransport | method | Creates and registers a MockTransport. |
| MockTransport | type | Implements packet and stream loopback delivery. |
| MockTransport.FinalAdvertiseAddr | method | Returns its in-memory advertised address. |
| MockTransport.WriteTo | method | Sends a packet by address. |
| MockTransport.WriteToAddress | method | Sends a packet by Address. |
| MockTransport.PacketCh | method | Exposes incoming packets. |
| MockTransport.DialTimeout | method | Opens an in-memory stream by address. |
| MockTransport.DialAddressTimeout | method | Opens an in-memory stream by Address. |
| MockTransport.StreamCh | method | Exposes incoming streams. |
| MockTransport.Shutdown | method | Completes transport shutdown. |
| Delegate | interface | Supplies node metadata, user-message handling, broadcasts, and local state exchange. |
| Delegate.NodeMeta | method | Supplies bounded local node metadata. |
| Delegate.NotifyMsg | method | Receives one direct user message. |
| Delegate.GetBroadcasts | method | Supplies application broadcasts under a byte budget. |
| Delegate.LocalState | method | Supplies application state for push-pull exchange. |
| Delegate.MergeRemoteState | method | Receives application state from a peer. |
| EventDelegate | interface | Receives join, leave, and update callbacks. |
| EventDelegate.NotifyJoin | method | Receives an accepted join transition. |
| EventDelegate.NotifyLeave | method | Receives a leave or dead transition. |
| EventDelegate.NotifyUpdate | method | Receives an accepted metadata update. |
| ChannelEventDelegate | type | Sends membership callbacks as NodeEvent values. |
| ChannelEventDelegate.NotifyJoin | method | Sends a NodeJoin value. |
| ChannelEventDelegate.NotifyLeave | method | Sends a NodeLeave value. |
| ChannelEventDelegate.NotifyUpdate | method | Sends a NodeUpdate value. |
| NodeEvent | type | Pairs a NodeEventType with a Node. |
| NodeEventType | type | Identifies join, leave, and update callbacks. |
| NodeJoin | constant | Identifies a join callback. |
| NodeLeave | constant | Identifies a leave callback. |
| NodeUpdate | constant | Identifies an update callback. |
| AliveDelegate | interface | Accepts or rejects proposed live peers. |
| AliveDelegate.NotifyAlive | method | Accepts or rejects one proposed live Node. |
| MergeDelegate | interface | Accepts or rejects push-pull merges. |
| MergeDelegate.NotifyMerge | method | Accepts or rejects one proposed peer set. |
| ConflictDelegate | interface | Receives duplicate-name address conflicts. |
| ConflictDelegate.NotifyConflict | method | Receives existing and conflicting Node views. |
| PingDelegate | interface | Supplies and receives direct-ping payloads. |
| PingDelegate.AckPayload | method | Supplies direct-ping acknowledgement bytes. |
| PingDelegate.NotifyPingComplete | method | Receives successful direct-ping timing and payload. |
| Broadcast | interface | Supplies disseminated bytes, invalidation, and completion. |
| Broadcast.Invalidates | method | Reports whether a newer broadcast replaces an older one. |
| Broadcast.Message | method | Returns disseminated bytes. |
| Broadcast.Finished | method | Reports terminal queue removal. |
| NamedBroadcast | interface | Gives a Broadcast replacement identity. |
| UniqueBroadcast | interface | Marks a Broadcast as intrinsically unique. |
| TransmitLimitedQueue | type | Prioritizes and bounds gossip retransmission. |
| TransmitLimitedQueue.QueueBroadcast | method | Adds a dissemination value. |
| TransmitLimitedQueue.GetBroadcasts | method | Selects values under a byte limit. |
| TransmitLimitedQueue.NumQueued | method | Returns queue size. |
| TransmitLimitedQueue.Reset | method | Finishes and removes all values. |
| TransmitLimitedQueue.Prune | method | Bounds retained queue size. |
| Keyring | type | Orders encryption and decryption keys. |
| NewKeyring | function | Creates a keyring with a selected primary. |
| ValidateKey | function | Validates AES key length. |
| Keyring.AddKey | method | Adds a decryption key. |
| Keyring.UseKey | method | Selects the outgoing primary key. |
| Keyring.RemoveKey | method | Removes a non-primary key. |
| Keyring.GetKeys | method | Returns keys in attempt order. |
| Keyring.GetPrimaryKey | method | Returns the outgoing primary key. |
| NoPingResponseError | error type | Reports a direct probe with no response. |

### CLI Entry Points

There is no console command for this module. Direct execution with go run is not supported. Programmatic use is through Go imports.

═══ Meta Layer ═══

## Appendix A: Environment

The working environment runs Go 1.25.0 on Linux without network access. The standard library and the dependency graph recorded by the delivered go.mod and go.sum are available from the local module cache. The delivered module must keep the module path github.com/hashicorp/memberlist and must build without fetching additional packages.

All membership traffic must use MockNetwork and MockTransport. No operating-system listener or address discovery is part of the supported environment.
