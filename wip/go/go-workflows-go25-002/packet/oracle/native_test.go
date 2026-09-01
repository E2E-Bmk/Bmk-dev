package workflowsgate_test

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

	"github.com/cschleiden/go-workflows/backend"
	"github.com/cschleiden/go-workflows/backend/converter"
	"github.com/cschleiden/go-workflows/backend/history"
	"github.com/cschleiden/go-workflows/backend/sqlite"
	"github.com/cschleiden/go-workflows/client"
	"github.com/cschleiden/go-workflows/core"
	"github.com/cschleiden/go-workflows/registry"
	"github.com/cschleiden/go-workflows/tester"
	"github.com/cschleiden/go-workflows/worker"
	"github.com/cschleiden/go-workflows/workflow"
)

type nativePayload struct {
	Name   string
	Values []int
}

func nativeValueWorkflow(_ workflow.Context, value string) (string, error) {
	return value + "-done", nil
}

func nativeErrorWorkflow(_ workflow.Context) (string, error) {
	return "", errors.New("native workflow failure")
}

func nativeActivity(_ context.Context, value int) (int, error) {
	return value * 2, nil
}

func nativeActivityWorkflow(ctx workflow.Context, value int) (int, error) {
	return workflow.ExecuteActivity[int](ctx, workflow.DefaultActivityOptions, nativeActivity, value).Get(ctx)
}

func nativeSignalWorkflow(ctx workflow.Context) (string, error) {
	value, ok := workflow.NewSignalChannel[string](ctx, "release").Receive(ctx)
	if !ok {
		return "", errors.New("signal channel closed")
	}
	return value, nil
}

func nativeContinueWorkflow(ctx workflow.Context, generation int) (int, error) {
	generation++
	if generation < 3 {
		return generation, workflow.ContinueAsNew(ctx, generation)
	}
	return generation, nil
}

func nativeChildWorkflow(_ workflow.Context, value string) (string, error) {
	return value + "-child", nil
}

func nativeParentWorkflow(ctx workflow.Context, value string) (string, error) {
	return workflow.CreateSubWorkflowInstance[string](ctx, workflow.DefaultSubWorkflowOptions, nativeChildWorkflow, value).Get(ctx)
}

func nativeWaitingWorkflow(ctx workflow.Context) (string, error) {
	_, _ = ctx.Done().Receive(ctx)
	return "", ctx.Err()
}

// Verifies: GWF-NATIVE-A01.
func TestGoWorkflowsAtomicNativeWorkflowInstance(t *testing.T) {
	instance := core.NewWorkflowInstance("instance-primary", "execution-primary")
	if instance.InstanceID != "instance-primary" || instance.ExecutionID != "execution-primary" || instance.SubWorkflow() {
		t.Fatalf("instance = %+v", instance)
	}
}

// Verifies: GWF-NATIVE-A01.
func TestGoWorkflowsAtomicNativeSubWorkflowLineage(t *testing.T) {
	parent := core.NewWorkflowInstance("parent", "execution-parent")
	child := core.NewSubWorkflowInstance("child", "execution-child", parent, 41)
	if !child.SubWorkflow() || child.Parent != parent || child.ParentEventID != 41 {
		t.Fatalf("child = %+v", child)
	}
}

// Verifies: GWF-NATIVE-A02.
func TestGoWorkflowsAtomicNativePayloadConverter(t *testing.T) {
	want := nativePayload{Name: "payload", Values: []int{3, 5, 8}}
	encoded, err := converter.DefaultConverter.To(want)
	if err != nil {
		t.Fatal(err)
	}
	var got nativePayload
	if err := converter.DefaultConverter.From(encoded, &got); err != nil || !reflect.DeepEqual(got, want) {
		t.Fatalf("round trip = %+v, %v", got, err)
	}
}

// Verifies: GWF-NATIVE-A02.
func TestGoWorkflowsAtomicNativeNilPayload(t *testing.T) {
	encoded, err := converter.DefaultConverter.To((*nativePayload)(nil))
	if err != nil {
		t.Fatal(err)
	}
	var got *nativePayload
	if err := converter.DefaultConverter.From(encoded, &got); err != nil || got != nil {
		t.Fatalf("nil round trip = %+v, %v", got, err)
	}
}

// Verifies: GWF-NATIVE-A03.
func TestGoWorkflowsAtomicNativeBackendOptions(t *testing.T) {
	options := backend.ApplyOptions(backend.WithWorkerName("worker-a"), backend.WithMaxHistorySize(731), backend.WithWorkflowLockTimeout(17*time.Millisecond))
	if options.WorkerName != "worker-a" || options.MaxHistorySize != 731 || options.WorkflowLockTimeout != 17*time.Millisecond {
		t.Fatalf("options = %+v", options)
	}
}

// Verifies: GWF-NATIVE-A03.
func TestGoWorkflowsAtomicNativeBackendDefaultsDetached(t *testing.T) {
	first := backend.ApplyOptions(backend.WithWorkerName("first"))
	second := backend.ApplyOptions()
	if first == second || second.WorkerName != backend.DefaultOptions.WorkerName || first.WorkerName == second.WorkerName {
		t.Fatalf("first/second = %+v / %+v", first, second)
	}
}

// Verifies: GWF-NATIVE-A04.
func TestGoWorkflowsAtomicNativeHistoryEvent(t *testing.T) {
	now := time.Unix(1700000000, 0).UTC()
	event := history.NewHistoryEvent(9, now, history.EventType_TimerFired, &history.TimerFiredAttributes{}, history.ScheduleEventID(4))
	if event.ID == "" || event.SequenceID != 9 || event.Timestamp != now || event.Type != history.EventType_TimerFired || event.ScheduleEventID != 4 {
		t.Fatalf("event = %+v", event)
	}
}

// Verifies: GWF-NATIVE-A04.
func TestGoWorkflowsAtomicNativePendingCancellationEvent(t *testing.T) {
	now := time.Unix(1700000042, 0).UTC()
	event := history.NewWorkflowCancellationEvent(now)
	if event.ID == "" || event.SequenceID != 0 || event.Timestamp != now || event.Type != history.EventType_WorkflowExecutionCanceled {
		t.Fatalf("event = %+v", event)
	}
}

// Verifies: GWF-NATIVE-A05.
func TestGoWorkflowsAtomicNativeWorkflowRegistration(t *testing.T) {
	values := registry.New()
	if err := values.RegisterWorkflow(nativeValueWorkflow); err != nil {
		t.Fatal(err)
	}
	if _, err := values.GetWorkflow("nativeValueWorkflow"); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GWF-NATIVE-A05.
func TestGoWorkflowsAtomicNativeRegistrationRejectsDuplicate(t *testing.T) {
	values := registry.New()
	if err := values.RegisterActivity(nativeActivity); err != nil {
		t.Fatal(err)
	}
	if err := values.RegisterActivity(nativeActivity); err == nil {
		t.Fatal("duplicate activity registration succeeded")
	}
}

// Verifies: GWF-NATIVE-A06.
func TestGoWorkflowsAtomicNativeTesterResult(t *testing.T) {
	runner := tester.NewWorkflowTester[string](nativeValueWorkflow)
	runner.Execute(context.Background(), "tester")
	got, err := runner.WorkflowResult()
	if err != nil || !runner.WorkflowFinished() || got != "tester-done" {
		t.Fatalf("result = %q, finished = %v, err = %v", got, runner.WorkflowFinished(), err)
	}
}

// Verifies: GWF-NATIVE-A06.
func TestGoWorkflowsAtomicNativeTesterError(t *testing.T) {
	runner := tester.NewWorkflowTester[string](nativeErrorWorkflow)
	runner.Execute(context.Background())
	got, err := runner.WorkflowResult()
	if got != "" || err == nil || err.Error() != "native workflow failure" {
		t.Fatalf("result/error = %q / %v", got, err)
	}
}

// Verifies: GWF-NATIVE-A07.
func TestGoWorkflowsAtomicNativeWorkerRegistration(t *testing.T) {
	storage := sqlite.NewInMemoryBackend()
	t.Cleanup(func() { _ = storage.Close() })
	runner := worker.New(storage, nil)
	if err := runner.RegisterWorkflow(nativeValueWorkflow); err != nil {
		t.Fatal(err)
	}
	if err := runner.RegisterActivity(nativeActivity); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GWF-NATIVE-A07.
func TestGoWorkflowsAtomicNativeWorkerStartStop(t *testing.T) {
	storage := sqlite.NewInMemoryBackend()
	t.Cleanup(func() { _ = storage.Close() })
	runner := worker.New(storage, nil)
	ctx, cancel := context.WithCancel(context.Background())
	if err := runner.Start(ctx); err != nil {
		cancel()
		t.Fatal(err)
	}
	cancel()
	if err := runner.WaitForCompletion(); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GWF-NATIVE-I01.
func TestGoWorkflowsNativeSeamActivityContextValue(t *testing.T) {
	runner := tester.NewWorkflowTester[int](nativeActivityWorkflow)
	if err := runner.Registry().RegisterActivity(nativeActivity); err != nil {
		t.Fatal(err)
	}
	runner.Execute(context.Background(), 21)
	got, err := runner.WorkflowResult()
	if err != nil || got != 42 {
		t.Fatalf("activity result = %d, %v", got, err)
	}
}

// Verifies: GWF-NATIVE-I02.
func TestGoWorkflowsNativeSeamTesterSignalResult(t *testing.T) {
	runner := tester.NewWorkflowTester[string](nativeSignalWorkflow)
	runner.ScheduleCallback(time.Millisecond, func() { runner.SignalWorkflow("release", "signaled") })
	runner.Execute(context.Background())
	got, err := runner.WorkflowResult()
	if err != nil || got != "signaled" {
		t.Fatalf("signal result = %q, %v", got, err)
	}
}

func runNativeSQLiteWorkflow(t *testing.T, id string, wf workflow.Workflow, args ...any) (*client.Client, *core.WorkflowInstance, *worker.Worker, *sqliteBackendCloser) {
	t.Helper()
	storage := sqlite.NewInMemoryBackend()
	closer := &sqliteBackendCloser{close: storage.Close}
	t.Cleanup(func() { _ = closer.Close() })
	runner := worker.New(storage, nil)
	if err := runner.RegisterWorkflow(wf); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(func() { cancel(); _ = runner.WaitForCompletion() })
	if err := runner.Start(ctx); err != nil {
		t.Fatal(err)
	}
	c := client.New(storage)
	instance, err := c.CreateWorkflowInstance(context.Background(), client.WorkflowInstanceOptions{InstanceID: id}, wf, args...)
	if err != nil {
		t.Fatal(err)
	}
	return c, instance, runner, closer
}

type sqliteBackendCloser struct {
	close func() error
	done  bool
}

func (c *sqliteBackendCloser) Close() error {
	if c.done {
		return nil
	}
	c.done = true
	return c.close()
}

// Verifies: GWF-NATIVE-I03.
func TestGoWorkflowsNativeSeamSQLiteStartResult(t *testing.T) {
	c, instance, _, _ := runNativeSQLiteWorkflow(t, "native-result", nativeValueWorkflow, "sqlite")
	got, err := client.GetWorkflowResult[string](context.Background(), c, instance, 5*time.Second)
	if err != nil || got != "sqlite-done" {
		t.Fatalf("client result = %q, %v", got, err)
	}
}

// Verifies: GWF-NATIVE-I04.
func TestGoWorkflowsNativeSeamRemoveCompletedInstance(t *testing.T) {
	c, instance, _, _ := runNativeSQLiteWorkflow(t, "native-remove", nativeValueWorkflow, "remove")
	if _, err := client.GetWorkflowResult[string](context.Background(), c, instance, 5*time.Second); err != nil {
		t.Fatal(err)
	}
	if err := c.RemoveWorkflowInstance(context.Background(), instance); err != nil {
		t.Fatal(err)
	}
	if _, err := c.GetWorkflowInstanceState(context.Background(), instance); !errors.Is(err, backend.ErrInstanceNotFound) {
		t.Fatalf("removed state error = %v", err)
	}
}

// Verifies: GWF-NATIVE-S01.
func TestGoWorkflowsSystemNativeContinueAsNewReceipt(t *testing.T) {
	runner := tester.NewWorkflowTester[int](nativeContinueWorkflow)
	runner.Execute(context.Background(), 0)
	got, err := runner.WorkflowResult()
	if err != nil || !runner.WorkflowFinished() || got != 3 {
		t.Fatalf("continue result = %d, finished = %v, err = %v", got, runner.WorkflowFinished(), err)
	}
}

// Verifies: GWF-NATIVE-S02.
func TestGoWorkflowsSystemNativeSubWorkflowReceipt(t *testing.T) {
	runner := tester.NewWorkflowTester[string](nativeParentWorkflow)
	if err := runner.Registry().RegisterWorkflow(nativeChildWorkflow); err != nil {
		t.Fatal(err)
	}
	runner.Execute(context.Background(), "parent")
	got, err := runner.WorkflowResult()
	if err != nil || got != "parent-child" {
		t.Fatalf("subworkflow result = %q, %v", got, err)
	}
}

// Verifies: GWF-NATIVE-S03.
func TestGoWorkflowsSystemNativeCancelRemoveReceipt(t *testing.T) {
	cancelled := tester.NewWorkflowTester[string](nativeWaitingWorkflow)
	cancelled.ScheduleCallback(time.Millisecond, cancelled.CancelWorkflow)
	cancelled.Execute(context.Background())
	if _, err := cancelled.WorkflowResult(); err == nil {
		t.Fatal("cancelled workflow returned a successful result")
	}

	c, instance, _, _ := runNativeSQLiteWorkflow(t, "native-cancel-remove", nativeValueWorkflow, "terminal")
	if _, err := client.GetWorkflowResult[string](context.Background(), c, instance, 5*time.Second); err != nil {
		t.Fatal(err)
	}
	if err := c.RemoveWorkflowInstance(context.Background(), instance); err != nil {
		t.Fatal(err)
	}
	if _, err := c.GetWorkflowInstanceState(context.Background(), instance); !errors.Is(err, backend.ErrInstanceNotFound) {
		t.Fatalf("removed state error = %v", err)
	}
}
