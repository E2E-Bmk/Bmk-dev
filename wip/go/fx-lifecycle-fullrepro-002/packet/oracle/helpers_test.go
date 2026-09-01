package fxgate_test

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"sync"
	"testing"
	"time"

	"go.uber.org/fx"
	"go.uber.org/fx/receipt"
)

const gateTimeout = 3 * time.Second

func graphPlan(t *testing.T, appID string, projections ...string) receipt.GraphPlan {
	t.Helper()
	plan, err := receipt.NewGraphPlan().SelectApp(appID, "root")
	if err != nil {
		t.Fatalf("SelectApp() error = %v", err)
	}
	for _, projection := range projections {
		switch projection {
		case "resolution":
			plan, err = plan.IncludeResolution()
		case "lifecycle":
			plan, err = plan.IncludeLifecycle()
		case "events":
			plan, err = plan.IncludeEvents()
		case "shutdown":
			plan, err = plan.IncludeShutdown()
		default:
			t.Fatalf("unknown projection %q", projection)
		}
		if err != nil {
			t.Fatalf("include %s error = %v", projection, err)
		}
	}
	return plan
}

func appJournal(t *testing.T, facts ...any) *receipt.AppJournal {
	t.Helper()
	journal := receipt.NewAppJournal()
	for index, fact := range facts {
		if err := journal.Record(uint64(index+1), fact); err != nil {
			t.Fatalf("Record(%d) error = %v", index+1, err)
		}
	}
	return journal
}

func captureReceipt(t *testing.T, plan receipt.GraphPlan, facts ...any) receipt.AppReceipt {
	t.Helper()
	value, err := receipt.Capture(plan, appJournal(t, facts...))
	if err != nil {
		t.Fatalf("Capture() error = %v", err)
	}
	if err := value.Validate(); err != nil {
		t.Fatalf("Validate() error = %v", err)
	}
	return value
}

func demanded(id string, keys ...string) receipt.ConstructorFact {
	return receipt.ConstructorFact{ID: id, Scope: "root", Demanded: true, Ran: true, ResultKeys: keys}
}

func unused(id string, keys ...string) receipt.ConstructorFact {
	return receipt.ConstructorFact{ID: id, Scope: "root", ResultKeys: keys}
}

func resolved(key, consumer string) receipt.ResolutionFact {
	return receipt.ResolutionFact{Key: key, ProviderScope: "root", ConsumerScope: "root", Consumer: consumer, Resolved: true}
}

func startHook(id string, registration, execution int, succeeded bool, errorClass string) receipt.HookFact {
	return receipt.HookFact{ID: id, Owner: "component/" + id, Phase: "start", Registration: registration, Execution: execution, Succeeded: succeeded, ErrorClass: errorClass}
}

func terminalHook(id, phase string, registration, execution int, errorClass string) receipt.HookFact {
	return receipt.HookFact{ID: id, Owner: "component/" + id, Phase: phase, Registration: registration, Execution: execution, Succeeded: errorClass == "", Rollback: phase == "rollback", ErrorClass: errorClass}
}

func event(kind, operation string, sequence uint64, succeeded bool, errorClass string) receipt.EventFact {
	return receipt.EventFact{Kind: kind, Operation: operation, Scope: "root", Sequence: sequence, Succeeded: succeeded, ErrorClass: errorClass}
}

func shutdown(receivers, exitCode int, stopped bool) receipt.ShutdownFact {
	return receipt.ShutdownFact{Requested: true, Receivers: receivers, Delivered: receivers, ExitCode: exitCode, WaitCompleted: true, StopCompleted: stopped}
}

func containsChange(changes []string, prefix string) bool {
	for _, value := range changes {
		if strings.HasPrefix(value, prefix) {
			return true
		}
	}
	return false
}

func startAndStop(t *testing.T, app *fx.App) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), gateTimeout)
	defer cancel()
	if err := app.Start(ctx); err != nil {
		t.Fatalf("Start() error = %v", err)
	}
	if err := app.Stop(ctx); err != nil {
		t.Fatalf("Stop() error = %v", err)
	}
}

type suppliedValue struct{ Value string }
type replacementValue struct{ Value string }
type unrelatedValue struct{ Value string }

type errorRecorder struct {
	mu   sync.Mutex
	errs []error
}

func (recorder *errorRecorder) HandleError(err error) {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	recorder.errs = append(recorder.errs, err)
}

func (recorder *errorRecorder) Errors() []error {
	recorder.mu.Lock()
	defer recorder.mu.Unlock()
	return append([]error(nil), recorder.errs...)
}

type memoryPrinter struct {
	mu    sync.Mutex
	lines []string
}

func (printer *memoryPrinter) Printf(format string, args ...interface{}) {
	printer.mu.Lock()
	defer printer.mu.Unlock()
	printer.lines = append(printer.lines, fmt.Sprintf(format, args...))
}

func (printer *memoryPrinter) Lines() []string {
	printer.mu.Lock()
	defer printer.mu.Unlock()
	return append([]string(nil), printer.lines...)
}

var errNativeInvoke = errors.New("native invoke failure")
