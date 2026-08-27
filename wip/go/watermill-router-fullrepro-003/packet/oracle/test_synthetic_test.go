package watermillv3gate_test

import (
	"context"
	"errors"
	"testing"

	"github.com/ThreeDotsLabs/watermill/message/drainbarrier"
	"github.com/ThreeDotsLabs/watermill/message/pubjournal"
	"github.com/ThreeDotsLabs/watermill/message/recovery"
	"github.com/ThreeDotsLabs/watermill/message/retrylineage"
	"github.com/ThreeDotsLabs/watermill/message/routeplan"
	"github.com/ThreeDotsLabs/watermill/message/settlement"
)

func atomicRouteRevision(t *testing.T) {
	c := routeplan.NewCatalog()
	first := bindOrder(t, c, routeplan.Command, "CreateOrder")
	second := bindOrder(t, c, routeplan.Command, "CreateOrder")
	old, err := c.AtRevision(routeplan.Command, "CreateOrder", first.Revision)
	mustNoError(t, err)
	if first.Revision == 0 || second.Revision <= first.Revision || old.Revision != first.Revision || len(c.Snapshot()) != 1 {
		t.Fatal("route revisions")
	}
}
func TestWatermillV3AtomicRouteRevisionPrimary(t *testing.T)   { atomicRouteRevision(t) }
func TestWatermillV3AtomicRouteRevisionSecondary(t *testing.T) { atomicRouteRevision(t) }

func atomicRouteCompatibility(t *testing.T) {
	c := routeplan.NewCatalog()
	first := bindOrder(t, c, routeplan.Query, "OrderStatus")
	next := bindOrder(t, c, routeplan.Query, "OrderStatus")
	other := next
	other.Handler = "other.Handler"
	if !routeplan.Compatible(first, next) || routeplan.Compatible(first, other) {
		t.Fatal("route compatibility")
	}
}
func TestWatermillV3AtomicRouteCompatibilityPrimary(t *testing.T)   { atomicRouteCompatibility(t) }
func TestWatermillV3AtomicRouteCompatibilitySecondary(t *testing.T) { atomicRouteCompatibility(t) }

func atomicJournalOwnership(t *testing.T) {
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Command, "CreateOrder")
	j := pubjournal.NewJournal()
	view := openBatch(t, j, "d-a03", "b-a03", b)
	bad := intents(b)
	if len(bad) == 0 {
		bad = []pubjournal.Intent{{ID: "fallback", Owner: "orders.Handler", Topic: "orders.fallback", Brokers: []string{"primary"}}}
	}
	bad[0].Owner = "foreign.Handler"
	_, err := j.Open("d-bad", "b-bad", b.Handler, bad)
	if view.RouteOwner != b.Handler || len(view.Intents) != 2 || !errors.Is(err, pubjournal.ErrInvalid) {
		t.Fatal("publication ownership")
	}
}
func TestWatermillV3AtomicJournalOwnershipPrimary(t *testing.T)   { atomicJournalOwnership(t) }
func TestWatermillV3AtomicJournalOwnershipSecondary(t *testing.T) { atomicJournalOwnership(t) }

func atomicPartialCompensation(t *testing.T) {
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Command, "CreateOrder")
	j := pubjournal.NewJournal()
	openBatch(t, j, "d-a04", "b-a04", b)
	_, err := j.Observe("b-a04", "event", "primary", pubjournal.Committed, "")
	mustNoError(t, err)
	_, err = j.Observe("b-a04", "event", "mirror", pubjournal.Rejected, "mirror unavailable")
	mustNoError(t, err)
	_, err = j.Rollback("b-a04")
	mustErrorIs(t, err, pubjournal.ErrPartial)
	_, err = j.Observe("b-a04", "event", "primary", pubjournal.Compensated, "retracted")
	mustNoError(t, err)
	v, err := j.Rollback("b-a04")
	mustNoError(t, err)
	if !v.RolledBack || v.Sealed {
		t.Fatal("compensated rollback")
	}
}
func TestWatermillV3AtomicPartialCompensationPrimary(t *testing.T)   { atomicPartialCompensation(t) }
func TestWatermillV3AtomicPartialCompensationSecondary(t *testing.T) { atomicPartialCompensation(t) }

func atomicSettlementFence(t *testing.T) {
	_, b, j, l, _, _, _ := buildWorkflow(t, "d-a05")
	pending, _ := j.Batch("batch-d-a05")
	_, err := l.Acknowledge("d-a05", pending)
	mustErrorIs(t, err, settlement.ErrNotReady)
	sealed := commitBatch(t, j, "batch-d-a05", b)
	record, err := l.Acknowledge("d-a05", sealed)
	mustNoError(t, err)
	_, err = l.Reject("d-a05", sealed, "late")
	if record.Decision != settlement.Ack || !errors.Is(err, settlement.ErrConflict) {
		t.Fatal("settlement fence")
	}
}
func TestWatermillV3AtomicSettlementFencePrimary(t *testing.T)   { atomicSettlementFence(t) }
func TestWatermillV3AtomicSettlementFenceSecondary(t *testing.T) { atomicSettlementFence(t) }

func atomicRetryOrdinal(t *testing.T) {
	i := retrylineage.NewIndex()
	first := observeAttempt(t, i, baseAttempt("d-a06"), "primary", "p0")
	next := baseAttempt("d-a06-r1")
	next.Ordinal = 1
	second := observeAttempt(t, i, next, "mirror", "m1")
	gap := next
	gap.Ordinal = 3
	_, err := i.Observe(gap, retrylineage.BrokerObservation{Broker: "primary", Topic: "orders.in", Token: "p3"})
	if first.Ordinal != 0 || second.Ordinal != 1 || !errors.Is(err, retrylineage.ErrConflict) {
		t.Fatal("retry ordinal")
	}
}
func TestWatermillV3AtomicRetryOrdinalPrimary(t *testing.T)   { atomicRetryOrdinal(t) }
func TestWatermillV3AtomicRetryOrdinalSecondary(t *testing.T) { atomicRetryOrdinal(t) }

func atomicCrossBrokerDedup(t *testing.T) {
	i := retrylineage.NewIndex()
	a := baseAttempt("d-a07")
	observeAttempt(t, i, a, "primary", "p0")
	merged := observeAttempt(t, i, a, "mirror", "m0")
	duplicate := observeAttempt(t, i, a, "mirror", "m0")
	owner, ok := i.ResolveDedup(a.DedupKey)
	if len(merged.Observations) != 2 || !merged.Duplicate || !duplicate.Duplicate || !ok || owner != a.LogicalID {
		t.Fatal("cross broker dedup")
	}
}
func TestWatermillV3AtomicCrossBrokerDedupPrimary(t *testing.T)   { atomicCrossBrokerDedup(t) }
func TestWatermillV3AtomicCrossBrokerDedupSecondary(t *testing.T) { atomicCrossBrokerDedup(t) }

func atomicDrainInflight(t *testing.T) {
	b := drainbarrier.NewBarrier()
	mustNoError(t, b.Admit("d-a08"))
	mustNoError(t, b.StartOutput("d-a08", "output-1"))
	v, err := b.Begin(7)
	mustNoError(t, err)
	mustNoError(t, b.RequestCancel("d-a08", "shutdown"))
	if v.Closed || len(v.Frozen) != 1 || len(b.Snapshot().Pending) != 1 {
		t.Fatal("drain inflight")
	}
}
func TestWatermillV3AtomicDrainInflightPrimary(t *testing.T)   { atomicDrainInflight(t) }
func TestWatermillV3AtomicDrainInflightSecondary(t *testing.T) { atomicDrainInflight(t) }

func atomicCheckpointMonotonic(t *testing.T) {
	s := recovery.NewStore()
	c := recovery.Checkpoint{ID: "cp", LogicalID: "l", DeliveryID: "d", Kind: routeplan.Command, TypeName: "CreateOrder", RouteRevision: 2, JournalCursor: 4, SettlementCursor: 3, Attempt: 1, DrainGeneration: 5}
	mustNoError(t, s.Save(c))
	stale := c
	stale.JournalCursor = 2
	err := s.Save(stale)
	loaded, ok := s.Load("cp")
	if !ok || loaded.JournalCursor != 4 || !errors.Is(err, recovery.ErrConflict) {
		t.Fatal("checkpoint monotonic")
	}
}
func TestWatermillV3AtomicCheckpointMonotonicPrimary(t *testing.T)   { atomicCheckpointMonotonic(t) }
func TestWatermillV3AtomicCheckpointMonotonicSecondary(t *testing.T) { atomicCheckpointMonotonic(t) }

func TestWatermillV3SeamRouteMetadataCQRS(t *testing.T) {
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Command, "CreateOrder")
	msg := taggedMessage("d-i01", b)
	assertMessageRoute(t, msg, b)
	roundTripCQRS(t, b.Name)
	resolved, err := c.Resolve(b.Kind, b.Name)
	mustNoError(t, err)
	if b.Revision == 0 || resolved.Revision != b.Revision {
		t.Fatal("route revision metadata")
	}
}
func TestWatermillV3SeamPartialBlocksAck(t *testing.T) {
	_, b, j, l, _, _, _ := buildWorkflow(t, "d-i02")
	_, err := j.Observe("batch-d-i02", "event", "primary", pubjournal.Committed, "")
	mustNoError(t, err)
	_, err = j.Observe("batch-d-i02", "event", "mirror", pubjournal.Rejected, "failed")
	mustNoError(t, err)
	view, _ := j.Batch("batch-d-i02")
	_, err = l.Acknowledge("d-i02", view)
	mustErrorIs(t, err, settlement.ErrNotReady)
	assertMessageRoute(t, taggedMessage("d-i02", b), b)
}
func TestWatermillV3SeamCompensationEnablesNack(t *testing.T) {
	_, b, j, l, _, _, _ := buildWorkflow(t, "d-i03")
	_, _ = j.Observe("batch-d-i03", "event", "primary", pubjournal.Committed, "")
	_, _ = j.Observe("batch-d-i03", "event", "mirror", pubjournal.Rejected, "failed")
	_, _ = j.Observe("batch-d-i03", "event", "primary", pubjournal.Compensated, "undo")
	rolled := rollbackBatch(t, j, "batch-d-i03")
	r, err := l.Reject("d-i03", rolled, "publish failed")
	mustNoError(t, err)
	msg := taggedMessage("d-i03", b)
	if r.Decision != settlement.Nack || !msg.Nack() {
		t.Fatal("nack recovery")
	}
}
func TestWatermillV3SeamInterleavedAckNack(t *testing.T) {
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Command, "CreateOrder")
	j := pubjournal.NewJournal()
	l := settlement.NewLedger()
	openBatch(t, j, "ack", "ba", b)
	openBatch(t, j, "nack", "bn", b)
	_, _ = l.Admit("ack", b.Revision, "ba")
	_, _ = l.Admit("nack", b.Revision, "bn")
	_, _ = j.Observe("bn", "event", "primary", pubjournal.Rejected, "x")
	rb := rollbackBatch(t, j, "bn")
	sealed := commitBatch(t, j, "ba", b)
	nr, ne := l.Reject("nack", rb, "x")
	ar, ae := l.Acknowledge("ack", sealed)
	mustNoError(t, ne)
	mustNoError(t, ae)
	if nr.Sequence >= ar.Sequence || len(l.Snapshot()) != 2 {
		t.Fatal("interleaved decisions")
	}
}
func TestWatermillV3SeamAckSignalsMessage(t *testing.T) {
	_, b, j, l, _, _, _ := buildWorkflow(t, "d-i05")
	sealed := commitBatch(t, j, "batch-d-i05", b)
	r, err := l.Acknowledge("d-i05", sealed)
	mustNoError(t, err)
	msg := taggedMessage("d-i05", b)
	if r.Decision != settlement.Ack || !msg.Ack() || msg.Nack() {
		t.Fatal("ack signal")
	}
}
func TestWatermillV3SeamNackSignalsMessage(t *testing.T) {
	_, b, j, l, _, _, _ := buildWorkflow(t, "d-i06")
	rb := rollbackBatch(t, j, "batch-d-i06")
	r, err := l.Reject("d-i06", rb, "handler failed")
	mustNoError(t, err)
	msg := taggedMessage("d-i06", b)
	if r.Decision != settlement.Nack || !msg.Nack() || msg.Ack() {
		t.Fatal("nack signal")
	}
}
func TestWatermillV3SeamBrokerMetadataReconcile(t *testing.T) {
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Event, "OrderCreated")
	msg := taggedMessage("d-i07", b)
	i := retrylineage.NewIndex()
	a := baseAttempt(msg.UUID)
	observeAttempt(t, i, a, "primary", "p")
	merged := observeAttempt(t, i, a, "mirror", "m")
	if merged.CorrelationID != msg.Metadata.Get("correlation_id") || len(merged.Observations) != 2 {
		t.Fatal("metadata reconcile")
	}
}
func TestWatermillV3SeamRetryUsesCurrentRoute(t *testing.T) {
	c := routeplan.NewCatalog()
	old := bindOrder(t, c, routeplan.Command, "CreateOrder")
	current := bindOrder(t, c, routeplan.Command, "CreateOrder")
	i := retrylineage.NewIndex()
	a := observeAttempt(t, i, baseAttempt("d-i08"), "primary", "p")
	next := a
	next.DeliveryID = "d-i08-r1"
	next.Ordinal = 1
	next.Observations = nil
	next = observeAttempt(t, i, next, "mirror", "m")
	resolved, _ := c.Resolve(current.Kind, current.Name)
	if !routeplan.Compatible(old, resolved) || next.Ordinal != 1 || resolved.Revision != current.Revision {
		t.Fatal("retry route")
	}
}
func TestWatermillV3SeamTwoIndexesReconcile(t *testing.T) {
	a := baseAttempt("d-i09")
	left := retrylineage.NewIndex()
	right := retrylineage.NewIndex()
	observeAttempt(t, left, a, "primary", "p")
	observeAttempt(t, right, a, "mirror", "m")
	lv := observeAttempt(t, left, a, "mirror", "m")
	rv := observeAttempt(t, right, a, "primary", "p")
	if len(lv.Observations) != 2 || len(rv.Observations) != 2 || lv.CorrelationID == "" || lv.CorrelationID != rv.CorrelationID {
		t.Fatal("two index reconcile")
	}
}
func TestWatermillV3SeamCancelWaitsForOutput(t *testing.T) {
	_, b, j, l, _, _, bar := buildWorkflow(t, "d-i10")
	mustNoError(t, bar.StartOutput("d-i10", "out"))
	_, _ = bar.Begin(3)
	mustNoError(t, bar.RequestCancel("d-i10", "shutdown"))
	rb := rollbackBatch(t, j, "batch-d-i10")
	r, err := l.Cancel("d-i10", rb, "shutdown")
	mustNoError(t, err)
	mustNoError(t, bar.Observe(r))
	if bar.Snapshot().Closed {
		t.Fatal("closed with inflight output")
	}
	mustNoError(t, bar.FinishOutput("d-i10", "out"))
	if !bar.Snapshot().Closed || b.Revision == 0 {
		t.Fatal("finish did not close")
	}
}
func TestWatermillV3SeamSettlementBeforeOutputFinish(t *testing.T) {
	_, _, j, l, _, _, bar := buildWorkflow(t, "d-i11")
	mustNoError(t, bar.StartOutput("d-i11", "one"))
	mustNoError(t, bar.StartOutput("d-i11", "two"))
	_, _ = bar.Begin(4)
	rb := rollbackBatch(t, j, "batch-d-i11")
	r, _ := l.Reject("d-i11", rb, "x")
	mustNoError(t, bar.Observe(r))
	mustNoError(t, bar.FinishOutput("d-i11", "two"))
	if bar.Snapshot().Closed {
		t.Fatal("one output remains")
	}
	mustNoError(t, bar.FinishOutput("d-i11", "one"))
	if !bar.Snapshot().Closed {
		t.Fatal("barrier remains open")
	}
}
func TestWatermillV3SeamTwoDeliveryDrainInterleave(t *testing.T) {
	b := drainbarrier.NewBarrier()
	mustNoError(t, b.Admit("one"))
	mustNoError(t, b.Admit("two"))
	mustNoError(t, b.StartOutput("two", "out"))
	v, _ := b.Begin(8)
	late := b.Admit("late")
	if len(v.Frozen) != 2 || !errors.Is(late, drainbarrier.ErrDraining) {
		t.Fatal("drain freeze")
	}
	mustNoError(t, b.FinishOutput("two", "out"))
	if b.Snapshot().Closed {
		t.Fatal("unsettled deliveries")
	}
}
func TestWatermillV3SeamCheckpointCapturesCursors(t *testing.T) {
	_, b, j, l, _, a, bar := buildWorkflow(t, "d-i13")
	s := recovery.NewStore()
	cp := checkpointFor(b, j, l, a, bar)
	mustNoError(t, s.Save(cp))
	got, ok := s.Load(cp.ID)
	if !ok || got.JournalCursor != j.Cursor() || got.SettlementCursor != l.Cursor() {
		t.Fatal("checkpoint cursors")
	}
}
func TestWatermillV3SeamCheckpointReopenReplay(t *testing.T) {
	_, b, j, l, _, a, bar := buildWorkflow(t, "d-i14")
	first := recovery.NewStore()
	cp := checkpointFor(b, j, l, a, bar)
	mustNoError(t, first.Save(cp))
	reopened := recovery.NewStore()
	for _, item := range first.Snapshot() {
		mustNoError(t, reopened.Save(item))
	}
	got, ok := reopened.Load(cp.ID)
	if !ok || got != cp {
		t.Fatal("checkpoint replay")
	}
}
func TestWatermillV3SeamCheckpointRejectsStaleJournal(t *testing.T) {
	_, b, j, l, _, a, bar := buildWorkflow(t, "d-i15")
	cp := checkpointFor(b, j, l, a, bar)
	s := recovery.NewStore()
	mustNoError(t, s.Save(cp))
	stale := cp
	stale.JournalCursor--
	err := s.Save(stale)
	if !errors.Is(err, recovery.ErrConflict) {
		t.Fatal("stale journal cursor")
	}
}
func TestWatermillV3SeamCheckpointRouteReplay(t *testing.T) {
	c, b, j, l, _, a, bar := buildWorkflow(t, "d-i16")
	cp := checkpointFor(b, j, l, a, bar)
	next := bindOrder(t, c, routeplan.Command, "CreateOrder")
	store := recovery.NewStore()
	cp.RouteRevision = next.Revision
	mustNoError(t, store.Save(cp))
	loaded, _ := store.Load(cp.ID)
	resolved, _ := c.AtRevision(next.Kind, next.Name, loaded.RouteRevision)
	if resolved.Revision != next.Revision || !routeplan.Compatible(b, resolved) {
		t.Fatal("route replay")
	}
}

func resumeFixture(t *testing.T, delivery string, ordinal uint, cancel bool) (recovery.Checkpoint, routeplan.Binding, pubjournal.BatchView, settlement.Record, retrylineage.Attempt, drainbarrier.View) {
	_, b, j, l, i, a, bar := buildWorkflow(t, delivery)
	if ordinal > 0 {
		next := a
		next.DeliveryID = delivery
		next.Ordinal = ordinal
		next.Observations = nil
		a = observeAttempt(t, i, next, "mirror", "retry")
	}
	rb := rollbackBatch(t, j, "batch-"+delivery)
	record, _ := l.Lookup(delivery)
	if cancel {
		_, _ = bar.Begin(12)
		mustNoError(t, bar.RequestCancel(delivery, "shutdown"))
	}
	cp := checkpointFor(b, j, l, a, bar)
	return cp, b, rb, record, a, bar.Snapshot()
}
func TestWatermillV3SeamCQRSRetryAfterRollback(t *testing.T) {
	cp, b, batch, r, a, d := resumeFixture(t, "d-i17", 0, false)
	p, err := recovery.BuildResume(cp, b, batch, r, a, d)
	mustNoError(t, err)
	roundTripCQRS(t, b.Name)
	if p.Action != recovery.Retry || p.Topic != b.InputTopic || p.NextAttempt != 1 {
		t.Fatal("cqrs retry")
	}
}
func TestWatermillV3SeamCQRSDeadLetterAtLimit(t *testing.T) {
	cp, b, batch, r, a, d := resumeFixture(t, "d-i18", 1, false)
	p, err := recovery.BuildResume(cp, b, batch, r, a, d)
	mustNoError(t, err)
	if p.Action != recovery.DeadLetter || p.Topic != b.DeadLetter {
		t.Fatal("cqrs dead letter")
	}
}
func TestWatermillV3SeamCQRSCancelFromDrain(t *testing.T) {
	cp, b, batch, r, a, d := resumeFixture(t, "d-i19", 0, true)
	p, err := recovery.BuildResume(cp, b, batch, r, a, d)
	mustNoError(t, err)
	if p.Action != recovery.Cancel || p.Cause != "shutdown" {
		t.Fatal("cqrs cancel")
	}
}

func TestWatermillV3SystemRoutePartialFailureRecoveryFreshViews(t *testing.T) {
	c, b, j, l, _, _, _ := buildWorkflow(t, "d-s01")
	_, _ = j.Observe("batch-d-s01", "event", "primary", pubjournal.Committed, "")
	_, _ = j.Observe("batch-d-s01", "event", "mirror", pubjournal.Rejected, "down")
	_, _ = j.Observe("batch-d-s01", "event", "primary", pubjournal.Compensated, "undo")
	rb := rollbackBatch(t, j, "batch-d-s01")
	r, err := l.Reject("d-s01", rb, "down")
	mustNoError(t, err)
	resolved, _ := c.Resolve(b.Kind, b.Name)
	if r.Decision != settlement.Nack || resolved.Revision != b.Revision || j.Cursor() <= rb.Cursor-1 {
		t.Fatal("fresh failure views")
	}
}
func TestWatermillV3SystemInterleavedSettlementFreshViews(t *testing.T) {
	TestWatermillV3SeamInterleavedAckNack(t)
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Command, "CreateOrder")
	msg := taggedMessage("s02", b)
	assertMessageRoute(t, msg, b)
	if !msg.Ack() {
		t.Fatal("terminal hook")
	}
}
func TestWatermillV3SystemRetryAcrossBrokerFreshViews(t *testing.T) {
	c := routeplan.NewCatalog()
	b := bindOrder(t, c, routeplan.Event, "OrderCreated")
	i := retrylineage.NewIndex()
	a := baseAttempt("d-s03")
	observeAttempt(t, i, a, "primary", "p")
	merged := observeAttempt(t, i, a, "mirror", "m")
	msg := taggedMessage("d-s03", b)
	roundTripCQRS(t, b.Name)
	if len(merged.Observations) != 2 || msg.Metadata.Get("dedup_key") != merged.DedupKey {
		t.Fatal("fresh lineage views")
	}
}
func TestWatermillV3SystemDrainCancelRaceFreshViews(t *testing.T) {
	TestWatermillV3SeamCancelWaitsForOutput(t)
	_, b, _, _, _, _, _ := buildWorkflow(t, "d-s04-hook")
	msg := taggedMessage("d-s04-hook", b)
	ctx, cancel := context.WithCancel(msg.Context())
	msg.SetContext(ctx)
	cancel()
	if msg.Context().Err() == nil {
		t.Fatal("cancel hook")
	}
}
func TestWatermillV3SystemCheckpointCQRSReplayFreshViews(t *testing.T) {
	cp, b, batch, r, a, d := resumeFixture(t, "d-s05", 0, false)
	store := recovery.NewStore()
	mustNoError(t, store.Save(cp))
	reopened := recovery.NewStore()
	loaded, _ := store.Load(cp.ID)
	mustNoError(t, reopened.Save(loaded))
	plan, err := recovery.BuildResume(loaded, b, batch, r, a, d)
	mustNoError(t, err)
	roundTripCQRS(t, b.Name)
	goChannelDelivery(t, taggedMessage("d-s05", b))
	if plan.Action != recovery.Retry {
		t.Fatal("checkpoint cqrs replay")
	}
}
func TestWatermillV3SystemCrossViewReconcileWithoutReceipt(t *testing.T) {
	_, b, j, l, i, a, bar := buildWorkflow(t, "d-s06")
	sealed := commitBatch(t, j, "batch-d-s06", b)
	record, err := l.Acknowledge("d-s06", sealed)
	mustNoError(t, err)
	mustNoError(t, bar.Observe(record))
	cp := checkpointFor(b, j, l, a, bar)
	store := recovery.NewStore()
	mustNoError(t, store.Save(cp))
	line := i.Lineage(a.LogicalID)
	view := bar.Snapshot()
	if len(line) != 1 || !sealed.Sealed || record.Decision != settlement.Ack || len(view.Pending) != 0 || len(store.Snapshot()) != 1 {
		t.Fatal("independent views disagree")
	}
}
