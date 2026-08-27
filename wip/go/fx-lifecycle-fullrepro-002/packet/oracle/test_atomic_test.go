package fxgate_test

import (
	"errors"
	"testing"
	"time"

	"go.uber.org/fx"
	"go.uber.org/fx/receipt"
)

// Verifies: FX-LAZY-A01.
func TestFxAtomicUnusedProviderNotConstructedPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "unused-primary"), unused("unused", "service"))
	if got := value.Constructors[0]; got.Demanded || got.Ran {
		t.Fatalf("constructor = %+v", got)
	}
}

// Verifies: FX-LAZY-A01.
func TestFxAtomicUnusedProviderNotConstructedEdge(t *testing.T) {
	keys := []string{"service"}
	journal := appJournal(t, receipt.ConstructorFact{ID: "unused", Scope: "root", ResultKeys: keys})
	keys[0] = "changed"
	entries := journal.Entries()
	got := entries[0].(receipt.ConstructorFact)
	if got.ResultKeys[0] != "service" || got.Demanded || got.Ran {
		t.Fatalf("journal fact = %+v", got)
	}
}

// Verifies: FX-LAZY-A02.
func TestFxAtomicInvokedProviderConstructedOncePrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "demand-primary", "resolution"), demanded("provider", "service"), resolved("service", "invoke"))
	if len(value.Constructors) != 1 || !value.Constructors[0].Ran || len(value.Resolutions) != 1 {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-LAZY-A02.
func TestFxAtomicInvokedProviderConstructedOnceEdge(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "demand-edge", "resolution"), demanded("provider", "service"), resolved("service", "invoke-a"), resolved("service", "invoke-b"))
	if len(value.Constructors) != 1 || len(value.Resolutions) != 2 {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-MODULE-A01.
func TestFxAtomicModulePrivateVisibilityPrimary(t *testing.T) {
	fact := receipt.ResolutionFact{Key: "private", ProviderScope: "root/module", ConsumerScope: "root/module/child", Consumer: "child", Resolved: true}
	value := captureReceipt(t, graphPlan(t, "module-primary", "resolution"), fact)
	if !value.Resolutions[0].Resolved || value.Resolutions[0].ProviderScope != "root/module" {
		t.Fatalf("resolution = %+v", value.Resolutions)
	}
}

// Verifies: FX-MODULE-A01.
func TestFxAtomicModulePrivateVisibilityEdge(t *testing.T) {
	fact := receipt.ResolutionFact{Key: "private", ProviderScope: "root/module", ConsumerScope: "root/sibling", Consumer: "sibling", Optional: true}
	value := captureReceipt(t, graphPlan(t, "module-edge", "resolution"), fact)
	if value.Resolutions[0].Resolved {
		t.Fatalf("private value escaped: %+v", value.Resolutions[0])
	}
}

// Verifies: FX-MODULE-A02.
func TestFxAtomicDecorationReplacesVisibleValuePrimary(t *testing.T) {
	fact := receipt.ResolutionFact{Key: "service", ProviderScope: "root", ConsumerScope: "root/module/child", DecoratorScope: "root/module", Consumer: "invoke", Resolved: true}
	value := captureReceipt(t, graphPlan(t, "decorate-primary", "resolution"), fact)
	if value.Resolutions[0].DecoratorScope != "root/module" {
		t.Fatalf("resolution = %+v", value.Resolutions[0])
	}
}

// Verifies: FX-MODULE-A02.
func TestFxAtomicDecorationReplacesVisibleValueEdge(t *testing.T) {
	fact := receipt.ResolutionFact{Key: "service", ProviderScope: "root", ConsumerScope: "root/sibling", DecoratorScope: "root/module", Consumer: "invoke", Resolved: true}
	_, err := receipt.Capture(graphPlan(t, "decorate-edge", "resolution"), appJournal(t, fact))
	if err == nil {
		t.Fatal("cross-scope decoration was accepted")
	}
}

// Verifies: FX-ROLLBACK-A01.
func TestFxAtomicHookStartRegistrationOrderPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "starts-primary", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""))
	if value.Hooks[0].ID != "one" || value.Hooks[1].ID != "two" {
		t.Fatalf("hooks = %+v", value.Hooks)
	}
}

// Verifies: FX-ROLLBACK-A01.
func TestFxAtomicHookStartRegistrationOrderEdge(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "starts-edge", "lifecycle"), appJournal(t, startHook("one", 0, 1, true, "")))
	if err == nil {
		t.Fatal("noncontiguous start execution was accepted")
	}
}

// Verifies: FX-ROLLBACK-A02.
func TestFxAtomicStartFailurePreservesCausePrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "rollback-primary", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, false, "start-failure"), terminalHook("one", "rollback", 0, 0, ""))
	if value.Hooks[1].ErrorClass != "start-failure" || !value.Hooks[2].Rollback {
		t.Fatalf("hooks = %+v", value.Hooks)
	}
}

// Verifies: FX-ROLLBACK-A02.
func TestFxAtomicStartFailurePreservesCauseEdge(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "rollback-edge", "lifecycle"), startHook("first", 0, 0, false, "first-failure"))
	if len(value.Hooks) != 1 || value.Hooks[0].ErrorClass != "first-failure" {
		t.Fatalf("hooks = %+v", value.Hooks)
	}
}

// Verifies: FX-STOP-A01.
func TestFxAtomicStopUsesReverseStartOrderPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "stop-primary", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("two", "stop", 1, 0, ""), terminalHook("one", "stop", 0, 1, ""))
	if value.Hooks[2].ID != "two" || value.Hooks[3].ID != "one" {
		t.Fatalf("hooks = %+v", value.Hooks)
	}
}

// Verifies: FX-STOP-A01.
func TestFxAtomicStopUsesReverseStartOrderEdge(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "stop-edge", "lifecycle"), appJournal(t, startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("one", "stop", 0, 0, ""), terminalHook("two", "stop", 1, 1, "")))
	if err == nil {
		t.Fatal("forward stop order was accepted")
	}
}

// Verifies: FX-STOP-A02.
func TestFxAtomicStopAggregatesHookErrorsPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "stop-errors", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("two", "stop", 1, 0, "stop-two"), terminalHook("one", "stop", 0, 1, ""))
	if value.Hooks[2].ErrorClass != "stop-two" || value.Hooks[3].ID != "one" {
		t.Fatalf("hooks = %+v", value.Hooks)
	}
}

// Verifies: FX-STOP-A02.
func TestFxAtomicStopAggregatesHookErrorsEdge(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "stop-errors-edge", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("two", "stop", 1, 0, "stop-two"), terminalHook("one", "stop", 0, 1, "stop-one"))
	if value.Hooks[2].Succeeded || value.Hooks[3].Succeeded {
		t.Fatalf("stop errors = %+v", value.Hooks[2:])
	}
}

// Verifies: FX-ERRGRAPH-A01.
func TestFxAtomicEventLoggerReceivesConstructionErrorPrimary(t *testing.T) {
	failed := demanded("provider", "service")
	failed.ErrorClass = "construction-error"
	value := captureReceipt(t, graphPlan(t, "event-error", "events"), failed, event("constructor", "provider", 1, false, "construction-error"))
	if value.Events[0].ErrorClass != failed.ErrorClass {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-ERRGRAPH-A01.
func TestFxAtomicEventLoggerReceivesConstructionErrorEdge(t *testing.T) {
	failed := demanded("provider", "service")
	failed.ErrorClass = "construction-error"
	_, err := receipt.Capture(graphPlan(t, "event-error-edge", "events"), appJournal(t, failed, event("constructor", "provider", 1, false, "other-error")))
	if err == nil {
		t.Fatal("contradictory event error was accepted")
	}
}

// Verifies: FX-NATIVE-START-TIMEOUT-001.
func TestFxAtomicStartTimeoutOptionPrimary(t *testing.T) {
	want := 37 * time.Millisecond
	app := fx.New(fx.NopLogger, fx.StartTimeout(want))
	if app.Err() != nil || app.StartTimeout() != want {
		t.Fatalf("app error = %v, start timeout = %v", app.Err(), app.StartTimeout())
	}
}

// Verifies: FX-NATIVE-START-TIMEOUT-001.
func TestFxAtomicStartTimeoutOptionEdge(t *testing.T) {
	want := time.Nanosecond
	app := fx.New(fx.NopLogger, fx.StartTimeout(want))
	if app.Err() != nil || app.StartTimeout() != want {
		t.Fatalf("app error = %v, start timeout = %v", app.Err(), app.StartTimeout())
	}
}

// Verifies: FX-NATIVE-STOP-TIMEOUT-001.
func TestFxAtomicStopTimeoutOptionPrimary(t *testing.T) {
	want := 41 * time.Millisecond
	app := fx.New(fx.NopLogger, fx.StopTimeout(want))
	if app.Err() != nil || app.StopTimeout() != want {
		t.Fatalf("app error = %v, stop timeout = %v", app.Err(), app.StopTimeout())
	}
}

// Verifies: FX-NATIVE-STOP-TIMEOUT-001.
func TestFxAtomicStopTimeoutOptionEdge(t *testing.T) {
	want := 2 * time.Nanosecond
	app := fx.New(fx.NopLogger, fx.StopTimeout(want))
	if app.Err() != nil || app.StopTimeout() != want {
		t.Fatalf("app error = %v, stop timeout = %v", app.Err(), app.StopTimeout())
	}
}

// Verifies: FX-NATIVE-ERROR-001.
func TestFxAtomicErrorOptionPrimary(t *testing.T) {
	want := errors.New("construction stopped")
	app := fx.New(fx.NopLogger, fx.Error(want))
	if !errors.Is(app.Err(), want) {
		t.Fatalf("app error = %v", app.Err())
	}
}

// Verifies: FX-NATIVE-ERROR-001.
func TestFxAtomicErrorOptionEdge(t *testing.T) {
	left := errors.New("left")
	right := errors.New("right")
	app := fx.New(fx.NopLogger, fx.Error(left, right))
	if !errors.Is(app.Err(), left) || !errors.Is(app.Err(), right) {
		t.Fatalf("app error = %v", app.Err())
	}
}

// Verifies: FX-NATIVE-SUPPLY-001.
func TestFxAtomicSupplyConcreteValuePrimary(t *testing.T) {
	input := &suppliedValue{Value: "supplied"}
	var output *suppliedValue
	app := fx.New(fx.NopLogger, fx.Supply(input), fx.Populate(&output))
	if app.Err() != nil || output != input {
		t.Fatalf("app error = %v, output = %+v", app.Err(), output)
	}
}

// Verifies: FX-NATIVE-SUPPLY-001.
func TestFxAtomicSupplyConcreteValueEdge(t *testing.T) {
	left := &suppliedValue{Value: "left"}
	right := &unrelatedValue{Value: "right"}
	var gotLeft *suppliedValue
	var gotRight *unrelatedValue
	app := fx.New(fx.NopLogger, fx.Supply(left, right), fx.Populate(&gotLeft, &gotRight))
	if app.Err() != nil || gotLeft != left || gotRight != right {
		t.Fatalf("app error = %v, outputs = %+v, %+v", app.Err(), gotLeft, gotRight)
	}
}

// Verifies: FX-NATIVE-REPLACE-001.
func TestFxAtomicReplaceConcreteValuePrimary(t *testing.T) {
	original := &replacementValue{Value: "original"}
	replacement := &replacementValue{Value: "replacement"}
	var output *replacementValue
	app := fx.New(fx.NopLogger, fx.Supply(original), fx.Replace(replacement), fx.Populate(&output))
	if app.Err() != nil || output != replacement {
		t.Fatalf("app error = %v, output = %+v", app.Err(), output)
	}
}

// Verifies: FX-NATIVE-REPLACE-001.
func TestFxAtomicReplaceConcreteValueEdge(t *testing.T) {
	replacement := &replacementValue{Value: "replacement"}
	unrelated := &unrelatedValue{Value: "stable"}
	var gotReplacement *replacementValue
	var gotUnrelated *unrelatedValue
	app := fx.New(fx.NopLogger, fx.Supply(&replacementValue{Value: "original"}, unrelated), fx.Replace(replacement), fx.Populate(&gotReplacement, &gotUnrelated))
	if app.Err() != nil || gotReplacement != replacement || gotUnrelated != unrelated {
		t.Fatalf("app error = %v, outputs = %+v, %+v", app.Err(), gotReplacement, gotUnrelated)
	}
}

// Verifies: FX-NATIVE-POP-001.
func TestFxAtomicPopulatePointerTargetPrimary(t *testing.T) {
	constructed := &suppliedValue{Value: "provided"}
	var output *suppliedValue
	app := fx.New(fx.NopLogger, fx.Provide(func() *suppliedValue { return constructed }), fx.Populate(&output))
	if app.Err() != nil || output != constructed {
		t.Fatalf("app error = %v, output = %+v", app.Err(), output)
	}
}

// Verifies: FX-NATIVE-POP-001.
func TestFxAtomicPopulatePointerTargetEdge(t *testing.T) {
	app := fx.New(fx.NopLogger, fx.Supply(&suppliedValue{}), fx.Populate((*suppliedValue)(nil)))
	if app.Err() == nil {
		t.Fatal("nil populate target was accepted")
	}
}

// Verifies: FX-NATIVE-VALIDATE-001.
func TestFxAtomicValidateAppSuccessPrimary(t *testing.T) {
	if err := fx.ValidateApp(fx.NopLogger, fx.Provide(func() *suppliedValue { return &suppliedValue{Value: "valid"} }), fx.Invoke(func(*suppliedValue) {})); err != nil {
		t.Fatalf("ValidateApp() error = %v", err)
	}
}

// Verifies: FX-NATIVE-VALIDATE-001.
func TestFxAtomicValidateAppSuccessEdge(t *testing.T) {
	called := false
	err := fx.ValidateApp(fx.NopLogger, fx.Provide(func() *suppliedValue { return &suppliedValue{} }), fx.Invoke(func(*suppliedValue) { called = true }))
	if err != nil || called {
		t.Fatalf("ValidateApp() error = %v, invoked = %v", err, called)
	}
}
