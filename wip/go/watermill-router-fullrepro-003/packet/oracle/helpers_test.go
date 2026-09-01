package watermillv3gate_test

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

	"github.com/ThreeDotsLabs/watermill"
	"github.com/ThreeDotsLabs/watermill/components/cqrs"
	"github.com/ThreeDotsLabs/watermill/message"
	"github.com/ThreeDotsLabs/watermill/message/drainbarrier"
	"github.com/ThreeDotsLabs/watermill/message/pubjournal"
	"github.com/ThreeDotsLabs/watermill/message/recovery"
	"github.com/ThreeDotsLabs/watermill/message/retrylineage"
	"github.com/ThreeDotsLabs/watermill/message/routeplan"
	"github.com/ThreeDotsLabs/watermill/message/settlement"
	"github.com/ThreeDotsLabs/watermill/pubsub/gochannel"
)

func mustNoError(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

func mustErrorIs(t *testing.T, err, target error) {
	t.Helper()
	if !errors.Is(err, target) {
		t.Fatalf("error=%v want=%v", err, target)
	}
}

func mustEqual(t *testing.T, got, want any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got=%#v want=%#v", got, want)
	}
}

func bindOrder(t *testing.T, catalog *routeplan.Catalog, kind routeplan.Kind, name string) routeplan.Binding {
	t.Helper()
	b, err := catalog.Bind(routeplan.Binding{
		Kind: kind, Name: name, Handler: "orders.Handler", InputTopic: "orders.in",
		Outputs:    []routeplan.Output{{Name: "event", Topic: "orders.events", Brokers: []string{"primary", "mirror"}}, {Name: "audit", Topic: "orders.audit", Brokers: []string{"primary"}}},
		DeadLetter: "orders.dead", MaxAttempts: 2,
	})
	mustNoError(t, err)
	return b
}

func intents(binding routeplan.Binding) []pubjournal.Intent {
	result := make([]pubjournal.Intent, 0, len(binding.Outputs))
	for _, output := range binding.Outputs {
		result = append(result, pubjournal.Intent{ID: output.Name, Owner: binding.Handler, Topic: output.Topic, Brokers: append([]string(nil), output.Brokers...)})
	}
	return result
}

func openBatch(t *testing.T, journal *pubjournal.Journal, delivery, batch string, binding routeplan.Binding) pubjournal.BatchView {
	t.Helper()
	v, err := journal.Open(delivery, batch, binding.Handler, intents(binding))
	mustNoError(t, err)
	return v
}

func commitBatch(t *testing.T, journal *pubjournal.Journal, batch string, binding routeplan.Binding) pubjournal.BatchView {
	t.Helper()
	for _, output := range binding.Outputs {
		for _, broker := range output.Brokers {
			_, err := journal.Observe(batch, output.Name, broker, pubjournal.Committed, "")
			mustNoError(t, err)
		}
	}
	v, err := journal.Seal(batch)
	mustNoError(t, err)
	return v
}

func rollbackBatch(t *testing.T, journal *pubjournal.Journal, batch string) pubjournal.BatchView {
	t.Helper()
	v, err := journal.Rollback(batch)
	mustNoError(t, err)
	return v
}

func baseAttempt(delivery string) retrylineage.Attempt {
	return retrylineage.Attempt{LogicalID: "logical-order", DeliveryID: delivery, CorrelationID: "corr-order", DedupKey: "dedup-order", Ordinal: 0}
}

func observeAttempt(t *testing.T, index *retrylineage.Index, attempt retrylineage.Attempt, broker, token string) retrylineage.Attempt {
	t.Helper()
	a, err := index.Observe(attempt, retrylineage.BrokerObservation{Broker: broker, Topic: "orders.in", Token: token})
	mustNoError(t, err)
	return a
}

func taggedMessage(delivery string, binding routeplan.Binding) *message.Message {
	msg := message.NewMessage(delivery, []byte(`{"order":"42"}`))
	msg.Metadata.Set("cqrs_kind", string(binding.Kind))
	msg.Metadata.Set("cqrs_type", binding.Name)
	msg.Metadata.Set("route_revision", string(rune(binding.Revision+'0')))
	msg.Metadata.Set("correlation_id", "corr-order")
	msg.Metadata.Set("dedup_key", "dedup-order")
	return msg
}

func assertMessageRoute(t *testing.T, msg *message.Message, binding routeplan.Binding) {
	t.Helper()
	if msg.Metadata.Get("cqrs_kind") != string(binding.Kind) || msg.Metadata.Get("cqrs_type") != binding.Name {
		t.Fatal("message route metadata")
	}
}

func roundTripCQRS(t *testing.T, name string) {
	t.Helper()
	type commandEnvelope struct{ Name string }
	m := cqrs.JSONMarshaler{NewUUID: func() string { return "cqrs-v3" }, GenerateName: func(any) string { return name }}
	msg, err := m.Marshal(commandEnvelope{Name: name})
	mustNoError(t, err)
	var out commandEnvelope
	mustNoError(t, m.Unmarshal(msg, &out))
	if out.Name != name || m.NameFromMessage(msg) != name {
		t.Fatal("cqrs route round trip")
	}
}

func goChannelDelivery(t *testing.T, msg *message.Message) {
	t.Helper()
	bus := gochannel.NewGoChannel(gochannel.Config{}, watermill.NopLogger{})
	defer bus.Close()
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	sub, err := bus.Subscribe(ctx, "orders.in")
	mustNoError(t, err)
	mustNoError(t, bus.Publish("orders.in", msg))
	select {
	case got := <-sub:
		if got.UUID != msg.UUID {
			t.Fatal("gochannel identity")
		}
		got.Ack()
	case <-ctx.Done():
		t.Fatal("gochannel delivery")
	}
}

func checkpointFor(binding routeplan.Binding, journal *pubjournal.Journal, ledger *settlement.Ledger, attempt retrylineage.Attempt, barrier *drainbarrier.Barrier) recovery.Checkpoint {
	return recovery.Checkpoint{ID: "checkpoint-" + attempt.DeliveryID, LogicalID: attempt.LogicalID, DeliveryID: attempt.DeliveryID, Kind: binding.Kind, TypeName: binding.Name, RouteRevision: binding.Revision, JournalCursor: journal.Cursor(), SettlementCursor: ledger.Cursor(), Attempt: attempt.Ordinal, DrainGeneration: barrier.Snapshot().Generation}
}

func buildWorkflow(t *testing.T, delivery string) (*routeplan.Catalog, routeplan.Binding, *pubjournal.Journal, *settlement.Ledger, *retrylineage.Index, retrylineage.Attempt, *drainbarrier.Barrier) {
	t.Helper()
	catalog := routeplan.NewCatalog()
	binding := bindOrder(t, catalog, routeplan.Command, "CreateOrder")
	journal := pubjournal.NewJournal()
	openBatch(t, journal, delivery, "batch-"+delivery, binding)
	ledger := settlement.NewLedger()
	_, err := ledger.Admit(delivery, binding.Revision, "batch-"+delivery)
	mustNoError(t, err)
	index := retrylineage.NewIndex()
	attempt := observeAttempt(t, index, baseAttempt(delivery), "primary", "token-"+delivery)
	barrier := drainbarrier.NewBarrier()
	mustNoError(t, barrier.Admit(delivery))
	return catalog, binding, journal, ledger, index, attempt, barrier
}
