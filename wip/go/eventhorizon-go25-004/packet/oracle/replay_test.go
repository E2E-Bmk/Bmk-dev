package eventhorizonv4_test

import (
	"context"
	"errors"
	"reflect"
	"sync"
	"testing"
	"time"

	eh "github.com/looplab/eventhorizon"
	aggevents "github.com/looplab/eventhorizon/aggregatestore/events"
	"github.com/looplab/eventhorizon/eventbus/local"
	"github.com/looplab/eventhorizon/eventhandler/projector"
	eventmemory "github.com/looplab/eventhorizon/eventstore/memory"
	outboxmemory "github.com/looplab/eventhorizon/outbox/memory"
	repomemory "github.com/looplab/eventhorizon/repo/memory"
	"github.com/looplab/eventhorizon/uuid"
)

const (
	changeType    eh.EventType     = "go25.eventhorizon.v4.changed"
	counterType   eh.AggregateType = "go25.eventhorizon.v4.counter"
	projectorType projector.Type   = "go25.eventhorizon.v4.projector"
)

type change struct {
	Delta int `json:"delta" bson:"delta"`
}

var registerOnce sync.Once

func registerDomain() {
	registerOnce.Do(func() {
		eh.RegisterEventData(changeType, func() eh.EventData { return &change{} })
		eh.RegisterAggregate(func(id uuid.UUID) eh.Aggregate { return newCounter(id) })
	})
}

func makeEvent(id uuid.UUID, version, delta int) eh.Event {
	registerDomain()
	return eh.NewEvent(
		changeType,
		&change{Delta: delta},
		time.Unix(1_700_000_000+int64(version), int64(delta)).UTC(),
		eh.ForAggregate(counterType, id, version),
		eh.WithMetadata(map[string]any{"version": version}),
	)
}

func newEventStore(t *testing.T) *eventmemory.EventStore {
	t.Helper()
	registerDomain()
	store, err := eventmemory.NewEventStore()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = store.Close() })
	return store
}

func saveEvents(t *testing.T, store eh.EventStore, id uuid.UUID, deltas ...int) []eh.Event {
	t.Helper()
	events := make([]eh.Event, len(deltas))
	for i, delta := range deltas {
		events[i] = makeEvent(id, i+1, delta)
	}
	if err := store.Save(context.Background(), events, 0); err != nil {
		t.Fatal(err)
	}
	return events
}

func deltas(events []eh.Event) []int {
	result := make([]int, len(events))
	for i, event := range events {
		if event == nil {
			result[i] = -9999
			continue
		}
		result[i] = event.Data().(*change).Delta
	}
	return result
}

type counterAggregate struct {
	*aggevents.AggregateBase
	Value int
}

func newCounter(id uuid.UUID) *counterAggregate {
	return &counterAggregate{AggregateBase: aggevents.NewAggregateBase(counterType, id)}
}

func (a *counterAggregate) HandleCommand(context.Context, eh.Command) error { return nil }

func (a *counterAggregate) ApplyEvent(_ context.Context, event eh.Event) error {
	data, ok := event.Data().(*change)
	if !ok {
		return errors.New("unexpected event data")
	}
	a.Value += data.Delta
	return nil
}

type counterState struct {
	Value int
}

func (a *counterAggregate) CreateSnapshot() *eh.Snapshot {
	return &eh.Snapshot{
		Version:       a.AggregateVersion(),
		AggregateType: counterType,
		Timestamp:     time.Now(),
		State:         &counterState{Value: a.Value},
	}
}

func (a *counterAggregate) ApplySnapshot(snapshot *eh.Snapshot) {
	state, ok := snapshot.State.(*counterState)
	if ok {
		a.Value = state.Value
	}
}

type snapshotStore struct {
	*eventmemory.EventStore
	snapshot  *eh.Snapshot
	rangeFrom []int
}

func (s *snapshotStore) LoadSnapshot(context.Context, uuid.UUID) (*eh.Snapshot, error) {
	return s.snapshot, nil
}

func (s *snapshotStore) SaveSnapshot(context.Context, uuid.UUID, eh.Snapshot) error { return nil }

func (s *snapshotStore) LoadRange(ctx context.Context, id uuid.UUID, from, to int) ([]eh.Event, error) {
	s.rangeFrom = append(s.rangeFrom, from)
	return s.EventStore.LoadRange(ctx, id, from, to)
}

type ordinaryStore struct {
	inner *eventmemory.EventStore
}

func (s *ordinaryStore) Save(ctx context.Context, events []eh.Event, version int) error {
	return s.inner.Save(ctx, events, version)
}

func (s *ordinaryStore) Load(ctx context.Context, id uuid.UUID) ([]eh.Event, error) {
	return s.inner.Load(ctx, id)
}

func (s *ordinaryStore) LoadFrom(ctx context.Context, id uuid.UUID, version int) ([]eh.Event, error) {
	return s.inner.LoadFrom(ctx, id, version)
}

func (s *ordinaryStore) Close() error { return s.inner.Close() }

type counterEntity struct {
	ID      uuid.UUID `json:"id"`
	Value   int       `json:"value"`
	Version int       `json:"version"`
}

func (e *counterEntity) EntityID() uuid.UUID   { return e.ID }
func (e *counterEntity) AggregateVersion() int { return e.Version }

type counterProjector struct {
	cancel context.CancelFunc
}

func (p *counterProjector) ProjectorType() projector.Type { return projectorType }

func (p *counterProjector) Project(_ context.Context, event eh.Event, entity eh.Entity) (eh.Entity, error) {
	model := entity.(*counterEntity)
	model.ID = event.AggregateID()
	model.Value += event.Data().(*change).Delta
	model.Version = event.Version()
	if p.cancel != nil {
		p.cancel()
		p.cancel = nil
	}
	return model, nil
}

func newProjection(t *testing.T, options ...projector.Option) (*projector.EventHandler, *repomemory.Repo) {
	t.Helper()
	repo := repomemory.NewRepo()
	repo.SetEntityFactory(func() eh.Entity { return &counterEntity{} })
	t.Cleanup(func() { _ = repo.Close() })
	handler := projector.NewEventHandler(&counterProjector{}, repo, options...)
	handler.SetEntityFactory(func() eh.Entity { return &counterEntity{} })
	return handler, repo
}

func readEntity(t *testing.T, repo eh.ReadRepo, id uuid.UUID) *counterEntity {
	t.Helper()
	entity, err := repo.Find(context.Background(), id)
	if err != nil {
		t.Fatal(err)
	}
	return entity.(*counterEntity)
}

type recorder struct {
	name          eh.EventHandlerType
	mu            sync.Mutex
	values        []int
	attempts      int
	failRemaining int
	alwaysFail    bool
	entered       chan struct{}
	release       chan struct{}
	enterOnce     sync.Once
}

func newRecorder(name string) *recorder              { return &recorder{name: eh.EventHandlerType(name)} }
func (h *recorder) HandlerType() eh.EventHandlerType { return h.name }

func (h *recorder) HandleEvent(ctx context.Context, event eh.Event) error {
	h.mu.Lock()
	h.attempts++
	h.mu.Unlock()
	if h.entered != nil {
		h.enterOnce.Do(func() { close(h.entered) })
		select {
		case <-h.release:
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.alwaysFail || h.failRemaining > 0 {
		if h.failRemaining > 0 {
			h.failRemaining--
		}
		return errors.New("recorder failure")
	}
	h.values = append(h.values, event.Data().(*change).Delta)
	return nil
}

func (h *recorder) snapshot() ([]int, int) {
	h.mu.Lock()
	defer h.mu.Unlock()
	return append([]int(nil), h.values...), h.attempts
}

func configureOutbox(t *testing.T) {
	t.Helper()
	oldInterval := outboxmemory.PeriodicSweepInterval
	oldAge := outboxmemory.PeriodicSweepAge
	oldCleanup := outboxmemory.PeriodicCleanupAge
	outboxmemory.PeriodicSweepInterval = 2 * time.Millisecond
	outboxmemory.PeriodicSweepAge = time.Millisecond
	outboxmemory.PeriodicCleanupAge = time.Millisecond
	t.Cleanup(func() {
		outboxmemory.PeriodicSweepInterval = oldInterval
		outboxmemory.PeriodicSweepAge = oldAge
		outboxmemory.PeriodicCleanupAge = oldCleanup
	})
}

func newOutbox(t *testing.T, handlers ...*recorder) *outboxmemory.Outbox {
	t.Helper()
	configureOutbox(t)
	outbox, err := outboxmemory.NewOutbox()
	if err != nil {
		t.Fatal(err)
	}
	for _, handler := range handlers {
		if err := outbox.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler); err != nil {
			t.Fatal(err)
		}
	}
	outbox.Start()
	return outbox
}

func waitContext() (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.Background(), 2*time.Second)
}

func TestEventHorizonV4A01(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 2, 3)
	events, err := store.Load(context.Background(), id)
	if err != nil || !reflect.DeepEqual(deltas(events), []int{2, 3}) {
		t.Fatalf("native stream: %v %v", err, deltas(events))
	}
}

func TestEventHorizonV4A02(t *testing.T) {
	cause := errors.New("cause")
	err := &eh.EventStoreError{Err: cause, Op: eh.EventStoreOpLoad, AggregateID: uuid.New()}
	if !errors.Is(err, cause) || err.Error() == cause.Error() {
		t.Fatalf("native error identity: %v", err)
	}
}

func TestEventHorizonV4A03(t *testing.T) {
	store := newEventStore(t)
	_, err := store.LoadRange(context.Background(), uuid.New(), 0, 2)
	if !errors.Is(err, eh.ErrInvalidEventRange) {
		t.Fatalf("invalid lower bound: %v", err)
	}
}

func TestEventHorizonV4A04(t *testing.T) {
	store := newEventStore(t)
	_, err := store.LoadRange(context.Background(), uuid.New(), 4, 3)
	if !errors.Is(err, eh.ErrInvalidEventRange) {
		t.Fatalf("reversed range: %v", err)
	}
}

func TestEventHorizonV4A05(t *testing.T) {
	store := newEventStore(t)
	_, err := store.LoadRange(context.Background(), uuid.New(), 1, 3)
	if !errors.Is(err, eh.ErrAggregateNotFound) {
		t.Fatalf("missing stream: %v", err)
	}
}

func TestEventHorizonV4A06(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 1)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := store.LoadRange(ctx, id, 1, 1)
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("canceled range: %v", err)
	}
}

func TestEventHorizonV4A07(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 1, 3, 5, 7)
	events, err := store.LoadRange(context.Background(), id, 2, 3)
	if err != nil || !reflect.DeepEqual(deltas(events), []int{3, 5}) || events[0].Version() != 2 || events[1].Version() != 3 {
		t.Fatalf("inclusive order: %v %v", err, deltas(events))
	}
}

func TestEventHorizonV4A08(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 4, 6)
	events, err := store.LoadRange(context.Background(), id, 2, 99)
	if err != nil || !reflect.DeepEqual(deltas(events), []int{6}) {
		t.Fatalf("range past head: %v %v", err, deltas(events))
	}
}

func TestEventHorizonV4A09(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 8)
	first, err := store.LoadRange(context.Background(), id, 1, 1)
	if err != nil {
		t.Fatal(err)
	}
	first[0].Data().(*change).Delta = 100
	second, err := store.LoadRange(context.Background(), id, 1, 1)
	if err != nil || second[0].Data().(*change).Delta != 8 {
		t.Fatalf("range aliases storage: %v %v", err, deltas(second))
	}
}

func TestEventHorizonV4A10(t *testing.T) {
	store := newEventStore(t)
	aggregates, err := aggevents.NewAggregateStore(store)
	if err != nil {
		t.Fatal(err)
	}
	aggregate, err := aggregates.LoadVersion(context.Background(), counterType, uuid.New(), 0)
	if err != nil || aggregate.(*counterAggregate).Value != 0 || aggregate.(*counterAggregate).AggregateVersion() != 0 {
		t.Fatalf("version zero: %v %#v", err, aggregate)
	}
}

func TestEventHorizonV4A11(t *testing.T) {
	store := newEventStore(t)
	aggregates, _ := aggevents.NewAggregateStore(store)
	_, err := aggregates.LoadVersion(context.Background(), counterType, uuid.New(), -1)
	if !errors.Is(err, aggevents.ErrInvalidAggregateVersion) {
		t.Fatalf("negative version: %v", err)
	}
}

func TestEventHorizonV4A12(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 2, 4)
	aggregates, _ := aggevents.NewAggregateStore(store)
	_, err := aggregates.LoadVersion(context.Background(), counterType, id, 3)
	if !errors.Is(err, aggevents.ErrAggregateVersionNotFound) {
		t.Fatalf("unreached version: %v", err)
	}
}

func TestEventHorizonV4I01(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 2, -1, 7, 4)
	aggregates, _ := aggevents.NewAggregateStore(store)
	aggregate, err := aggregates.LoadVersion(context.Background(), counterType, id, 3)
	got := aggregate.(*counterAggregate)
	if err != nil || got.AggregateVersion() != 3 || got.Value != 8 {
		t.Fatalf("historical fold: %v v%d value%d", err, got.AggregateVersion(), got.Value)
	}
}

func TestEventHorizonV4I02(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 1, 2, 4)
	aggregates, _ := aggevents.NewAggregateStore(store)
	old, err := aggregates.LoadVersion(context.Background(), counterType, id, 1)
	if err != nil || old.(*counterAggregate).Value != 1 {
		t.Fatal(err)
	}
	current, err := aggregates.Load(context.Background(), counterType, id)
	if err != nil || current.(*counterAggregate).Value != 7 || current.(*counterAggregate).AggregateVersion() != 3 {
		t.Fatalf("current changed: %v %#v", err, current)
	}
}

func TestEventHorizonV4I03(t *testing.T) {
	base := newEventStore(t)
	id := uuid.New()
	saveEvents(t, base, id, 2, 3, 5)
	store := &snapshotStore{EventStore: base, snapshot: &eh.Snapshot{Version: 3, AggregateType: counterType, State: &counterState{Value: 100}}}
	aggregates, _ := aggevents.NewAggregateStore(store)
	aggregate, err := aggregates.LoadVersion(context.Background(), counterType, id, 2)
	if err != nil || aggregate.(*counterAggregate).Value != 5 || !reflect.DeepEqual(store.rangeFrom, []int{1}) {
		t.Fatalf("newer snapshot used: %v value=%d ranges=%v", err, aggregate.(*counterAggregate).Value, store.rangeFrom)
	}
}

func TestEventHorizonV4I04(t *testing.T) {
	base := newEventStore(t)
	id := uuid.New()
	saveEvents(t, base, id, 2, 3, 5, 7)
	store := &snapshotStore{EventStore: base, snapshot: &eh.Snapshot{Version: 2, AggregateType: counterType, State: &counterState{Value: 5}}}
	aggregates, _ := aggevents.NewAggregateStore(store)
	aggregate, err := aggregates.LoadVersion(context.Background(), counterType, id, 4)
	if err != nil || aggregate.(*counterAggregate).Value != 17 || !reflect.DeepEqual(store.rangeFrom, []int{3}) {
		t.Fatalf("snapshot tail: %v value=%d ranges=%v", err, aggregate.(*counterAggregate).Value, store.rangeFrom)
	}
}

func TestEventHorizonV4I05(t *testing.T) {
	base := newEventStore(t)
	id := uuid.New()
	saveEvents(t, base, id, 3, 4, 9)
	aggregates, _ := aggevents.NewAggregateStore(&ordinaryStore{inner: base})
	aggregate, err := aggregates.LoadVersion(context.Background(), counterType, id, 2)
	if err != nil || aggregate.(*counterAggregate).Value != 7 || aggregate.(*counterAggregate).AggregateVersion() != 2 {
		t.Fatalf("ordinary store fallback: %v %#v", err, aggregate)
	}
}

func TestEventHorizonV4I06(t *testing.T) {
	id := uuid.New()
	handler, repo := newProjection(t)
	if err := handler.Replay(context.Background(), []eh.Event{makeEvent(id, 1, 2), makeEvent(id, 2, 5)}); err != nil {
		t.Fatal(err)
	}
	entity := readEntity(t, repo, id)
	if entity.Value != 7 || entity.Version != 2 {
		t.Fatalf("projection: %#v", entity)
	}
}

func TestEventHorizonV4I07(t *testing.T) {
	id := uuid.New()
	handler, repo := newProjection(t)
	events := []eh.Event{makeEvent(id, 1, 2), makeEvent(id, 2, 5)}
	if err := handler.Replay(context.Background(), events); err != nil {
		t.Fatal(err)
	}
	if err := handler.Replay(context.Background(), events); err != nil {
		t.Fatal(err)
	}
	entity := readEntity(t, repo, id)
	if entity.Value != 7 || entity.Version != 2 {
		t.Fatalf("duplicate replay: %#v", entity)
	}
}

func TestEventHorizonV4I08(t *testing.T) {
	id := uuid.New()
	handler, repo := newProjection(t)
	err := handler.Replay(context.Background(), []eh.Event{makeEvent(id, 1, 2), makeEvent(id, 3, 5)})
	if !errors.Is(err, eh.ErrIncorrectEntityVersion) {
		t.Fatalf("gap error: %v", err)
	}
	entity := readEntity(t, repo, id)
	if entity.Value != 2 || entity.Version != 1 {
		t.Fatalf("completed prefix lost: %#v", entity)
	}
}

func TestEventHorizonV4I09(t *testing.T) {
	id := uuid.New()
	repo := repomemory.NewRepo()
	repo.SetEntityFactory(func() eh.Entity { return &counterEntity{} })
	ctx, cancel := context.WithCancel(context.Background())
	handler := projector.NewEventHandler(&counterProjector{cancel: cancel}, repo)
	handler.SetEntityFactory(func() eh.Entity { return &counterEntity{} })
	err := handler.Replay(ctx, []eh.Event{makeEvent(id, 1, 2), makeEvent(id, 2, 5)})
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("replay cancellation: %v", err)
	}
	entity := readEntity(t, repo, id)
	if entity.Value != 2 || entity.Version != 1 {
		t.Fatalf("canceled prefix: %#v", entity)
	}
}

func TestEventHorizonV4I10(t *testing.T) {
	id := uuid.New()
	handler, repo := newProjection(t, projector.WithIrregularVersioning())
	if err := handler.Replay(context.Background(), []eh.Event{makeEvent(id, 2, 3), makeEvent(id, 5, 4)}); err != nil {
		t.Fatal(err)
	}
	entity := readEntity(t, repo, id)
	if entity.Value != 7 || entity.Version != 5 {
		t.Fatalf("irregular replay: %#v", entity)
	}
}

func TestEventHorizonV4I11(t *testing.T) {
	id := uuid.New()
	handler := newRecorder("bus-i11")
	handler.entered, handler.release = make(chan struct{}), make(chan struct{})
	bus := local.NewEventBus()
	if err := bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler); err != nil {
		t.Fatal(err)
	}
	if err := bus.HandleEvent(context.Background(), makeEvent(id, 1, 3)); err != nil {
		t.Fatal(err)
	}
	<-handler.entered
	done := make(chan error, 1)
	go func() { done <- bus.Wait(context.Background()) }()
	select {
	case err := <-done:
		t.Fatalf("wait crossed blocked handler: %v", err)
	case <-time.After(20 * time.Millisecond):
	}
	close(handler.release)
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	_ = bus.Close()
}

func TestEventHorizonV4I12(t *testing.T) {
	handler := newRecorder("bus-i12")
	bus := local.NewEventBus()
	_ = bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler)
	for i := 1; i <= 4; i++ {
		_ = bus.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, i))
	}
	ctx, cancel := waitContext()
	defer cancel()
	if err := bus.Wait(ctx); err != nil {
		t.Fatal(err)
	}
	values, _ := handler.snapshot()
	if !reflect.DeepEqual(values, []int{1, 2, 3, 4}) {
		t.Fatalf("barrier order: %v", values)
	}
	_ = bus.Close()
}

func TestEventHorizonV4I13(t *testing.T) {
	one := newRecorder("bus-i13-one")
	two := newRecorder("bus-i13-two")
	two.entered, two.release = make(chan struct{}), make(chan struct{})
	bus := local.NewEventBus()
	_ = bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, one)
	_ = bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, two)
	_ = bus.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 6))
	<-two.entered
	done := make(chan error, 1)
	go func() { done <- bus.Wait(context.Background()) }()
	select {
	case err := <-done:
		t.Fatalf("wait skipped a blocked queue: %v", err)
	case <-time.After(15 * time.Millisecond):
	}
	close(two.release)
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	valuesOne, _ := one.snapshot()
	valuesTwo, _ := two.snapshot()
	if !reflect.DeepEqual(valuesOne, []int{6}) || !reflect.DeepEqual(valuesTwo, []int{6}) {
		t.Fatalf("multi queue: %v %v", valuesOne, valuesTwo)
	}
	_ = bus.Close()
}

func TestEventHorizonV4I14(t *testing.T) {
	handler := newRecorder("bus-i14")
	handler.alwaysFail = true
	bus := local.NewEventBus()
	_ = bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler)
	_ = bus.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 9))
	ctx, cancel := waitContext()
	defer cancel()
	if err := bus.Wait(ctx); err != nil {
		t.Fatalf("handler error blocked barrier: %v", err)
	}
	select {
	case err := <-bus.Errors():
		if err == nil {
			t.Fatal("nil bus error")
		}
	case <-time.After(time.Second):
		t.Fatal("missing bus error")
	}
	_ = bus.Close()
}

func TestEventHorizonV4I15(t *testing.T) {
	handler := newRecorder("bus-i15")
	handler.entered, handler.release = make(chan struct{}), make(chan struct{})
	bus := local.NewEventBus()
	_ = bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler)
	_ = bus.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 1))
	<-handler.entered
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := bus.Wait(ctx); !errors.Is(err, context.Canceled) {
		t.Fatalf("canceled bus wait: %v", err)
	}
	close(handler.release)
	_ = bus.Close()
}

func TestEventHorizonV4I16(t *testing.T) {
	bus := local.NewEventBus()
	ctx, cancel := waitContext()
	defer cancel()
	if err := bus.Wait(ctx); err != nil {
		t.Fatalf("empty group: %v", err)
	}
	_ = bus.Close()
}

func TestEventHorizonV4I17(t *testing.T) {
	handler := newRecorder("outbox-i17")
	outbox := newOutbox(t, handler)
	_ = outbox.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 4))
	ctx, cancel := waitContext()
	defer cancel()
	if err := outbox.Wait(ctx); err != nil {
		t.Fatal(err)
	}
	values, _ := handler.snapshot()
	if !reflect.DeepEqual(values, []int{4}) {
		t.Fatalf("outbox delivery: %v", values)
	}
	_ = outbox.Close()
}

func TestEventHorizonV4I18(t *testing.T) {
	handler := newRecorder("outbox-i18")
	outbox := newOutbox(t, handler)
	other := eh.NewEvent("other", nil, time.Now(), eh.ForAggregate(counterType, uuid.New(), 1))
	_ = outbox.HandleEvent(context.Background(), other)
	ctx, cancel := waitContext()
	defer cancel()
	if err := outbox.Wait(ctx); err != nil {
		t.Fatal(err)
	}
	_, attempts := handler.snapshot()
	if attempts != 0 {
		t.Fatalf("nonmatch handled: %d", attempts)
	}
	_ = outbox.Close()
}

func TestEventHorizonV4I19(t *testing.T) {
	handler := newRecorder("outbox-i19")
	handler.alwaysFail = true
	outbox := newOutbox(t, handler)
	_ = outbox.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 5))
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Millisecond)
	defer cancel()
	if err := outbox.Wait(ctx); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("failed work disappeared: %v", err)
	}
	select {
	case <-outbox.Errors():
	case <-time.After(time.Second):
		t.Fatal("missing outbox error")
	}
	_ = outbox.Close()
}

func TestEventHorizonV4I20(t *testing.T) {
	stable := newRecorder("outbox-i20-stable")
	flaky := newRecorder("outbox-i20-flaky")
	flaky.failRemaining = 1
	outbox := newOutbox(t, stable, flaky)
	_ = outbox.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 7))
	ctx, cancel := waitContext()
	defer cancel()
	if err := outbox.Wait(ctx); err != nil {
		t.Fatal(err)
	}
	stableValues, stableAttempts := stable.snapshot()
	flakyValues, flakyAttempts := flaky.snapshot()
	if !reflect.DeepEqual(stableValues, []int{7}) || stableAttempts != 1 || !reflect.DeepEqual(flakyValues, []int{7}) || flakyAttempts < 2 {
		t.Fatalf("retry ownership: stable=%v/%d flaky=%v/%d", stableValues, stableAttempts, flakyValues, flakyAttempts)
	}
	_ = outbox.Close()
}

func TestEventHorizonV4I21(t *testing.T) {
	handler := newRecorder("outbox-i21")
	handler.alwaysFail = true
	outbox := newOutbox(t, handler)
	_ = outbox.HandleEvent(context.Background(), makeEvent(uuid.New(), 1, 8))
	done := make(chan error, 1)
	go func() { done <- outbox.Wait(context.Background()) }()
	select {
	case <-outbox.Errors():
	case <-time.After(time.Second):
		t.Fatal("handler was not attempted")
	}
	_ = outbox.Close()
	if err := <-done; !errors.Is(err, context.Canceled) {
		t.Fatalf("close did not release wait: %v", err)
	}
}

func TestEventHorizonV4I22(t *testing.T) {
	store := newEventStore(t)
	id := uuid.New()
	saveEvents(t, store, id, 2, 3, -1, 8)
	rangeEvents, err := store.LoadRange(context.Background(), id, 1, 3)
	if err != nil {
		t.Fatal(err)
	}
	aggregates, _ := aggevents.NewAggregateStore(store)
	historical, err := aggregates.LoadVersion(context.Background(), counterType, id, 3)
	if err != nil {
		t.Fatal(err)
	}
	handler, repo := newProjection(t)
	if err := handler.Replay(context.Background(), rangeEvents); err != nil {
		t.Fatal(err)
	}
	entity := readEntity(t, repo, id)
	if historical.(*counterAggregate).Value != 4 || entity.Value != 4 || entity.Version != 3 {
		t.Fatalf("cross view replay: aggregate=%d entity=%#v", historical.(*counterAggregate).Value, entity)
	}
}

func TestEventHorizonV4I23(t *testing.T) {
	id := uuid.New()
	handler, repo := newProjection(t)
	bus := local.NewEventBus()
	_ = bus.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler)
	store, err := eventmemory.NewEventStore(eventmemory.WithEventHandler(bus))
	if err != nil {
		t.Fatal(err)
	}
	saveEvents(t, store, id, 3, 5, 7)
	ctx, cancel := waitContext()
	defer cancel()
	if err := bus.Wait(ctx); err != nil {
		t.Fatal(err)
	}
	entity := readEntity(t, repo, id)
	rangeEvents, err := store.LoadRange(context.Background(), id, 2, 3)
	if err != nil || entity.Value != 15 || entity.Version != 3 || !reflect.DeepEqual(deltas(rangeEvents), []int{5, 7}) {
		t.Fatalf("store-bus-projector: %v %#v %v", err, entity, deltas(rangeEvents))
	}
	_ = bus.Close()
	_ = store.Close()
}

func TestEventHorizonV4I24(t *testing.T) {
	configureOutbox(t)
	id := uuid.New()
	handler, repo := newProjection(t)
	outbox, err := outboxmemory.NewOutbox()
	if err != nil {
		t.Fatal(err)
	}
	if err := outbox.AddHandler(context.Background(), eh.MatchEvents{changeType}, handler); err != nil {
		t.Fatal(err)
	}
	outbox.Start()
	store, err := eventmemory.NewEventStore(eventmemory.WithEventHandler(outbox))
	if err != nil {
		t.Fatal(err)
	}
	saveEvents(t, store, id, 4, -2, 9)
	ctx, cancel := waitContext()
	defer cancel()
	if err := outbox.Wait(ctx); err != nil {
		t.Fatal(err)
	}
	entity := readEntity(t, repo, id)
	aggregates, _ := aggevents.NewAggregateStore(store)
	historical, err := aggregates.LoadVersion(context.Background(), counterType, id, 2)
	if err != nil || entity.Value != 11 || entity.Version != 3 || historical.(*counterAggregate).Value != 2 {
		t.Fatalf("store-outbox-projector: %v entity=%#v historical=%d", err, entity, historical.(*counterAggregate).Value)
	}
	_ = outbox.Close()
	_ = store.Close()
}
