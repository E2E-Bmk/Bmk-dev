package fxgate_test

import (
	"context"
	"errors"
	"fmt"
	"reflect"
	"sort"
	"testing"

	"go.uber.org/fx"
	"go.uber.org/fx/receipt"
)

// Verifies: FX-LAZY-I01.
func TestFxSeamInvokeDemandToProviderConstructionPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "lazy-chain", "resolution"), demanded("database", "db"), demanded("service", "service"), resolved("db", "service"), resolved("service", "invoke"))
	if len(value.Constructors) != 2 || value.Constructors[0].ID != "database" || value.Resolutions[1].Consumer != "invoke" {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-LAZY-I01.
func TestFxSeamInvokeDemandToProviderConstructionFailure(t *testing.T) {
	fact := resolved("missing", "invoke")
	fact.Resolved = false
	_, err := receipt.Capture(graphPlan(t, "lazy-missing", "resolution"), appJournal(t, fact))
	if err == nil {
		t.Fatal("mandatory unresolved invoke input was accepted")
	}
}

// Verifies: FX-LAZY-I02.
func TestFxSeamConstructedValueToLifecycleHookPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "lazy-hook", "lifecycle"), demanded("worker", "worker"), startHook("worker", 0, 0, true, ""), terminalHook("worker", "stop", 0, 0, ""))
	if len(value.Constructors) != 1 || len(value.Hooks) != 2 || value.Hooks[0].Owner != "component/worker" {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-LAZY-I02.
func TestFxSeamConstructedValueToLifecycleHookFailure(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "unused-hook", "lifecycle"), appJournal(t, unused("worker", "worker"), startHook("worker", 0, 0, true, "")))
	if err == nil {
		t.Fatal("unused provider appended a lifecycle hook")
	}
}

// Verifies: FX-MODULE-I01.
func TestFxSeamModuleScopeToInvokeResolutionPrimary(t *testing.T) {
	outer := receipt.ResolutionFact{Key: "service", ProviderScope: "root", ConsumerScope: "root/module", DecoratorScope: "root", Consumer: "module-invoke", Resolved: true}
	inner := outer
	inner.ConsumerScope = "root/module/child"
	inner.Consumer = "child-invoke"
	inner.DecoratorScope = "root/module"
	value := captureReceipt(t, graphPlan(t, "module-chain", "resolution"), outer, inner)
	if value.Resolutions[0].DecoratorScope != "root" || value.Resolutions[1].DecoratorScope != "root/module" {
		t.Fatalf("resolutions = %+v", value.Resolutions)
	}
}

// Verifies: FX-MODULE-I01.
func TestFxSeamModuleScopeToInvokeResolutionFailure(t *testing.T) {
	fact := receipt.ResolutionFact{Key: "private", ProviderScope: "root/module", ConsumerScope: "root/sibling", Consumer: "sibling", Resolved: true}
	_, err := receipt.Capture(graphPlan(t, "module-leak", "resolution"), appJournal(t, fact))
	if err == nil {
		t.Fatal("private resolution crossed module scope")
	}
}

// Verifies: FX-MODULE-I02.
func TestFxSeamDecorationToNestedModuleValuePrimary(t *testing.T) {
	plain := resolved("service", "outer")
	decorated := receipt.ResolutionFact{Key: "service", ProviderScope: "root", ConsumerScope: "root/module/child", DecoratorScope: "root/module", Consumer: "inner", Resolved: true}
	value := captureReceipt(t, graphPlan(t, "module-decoration", "resolution"), plain, decorated)
	if value.Resolutions[0].DecoratorScope != "" || value.Resolutions[1].DecoratorScope == "" {
		t.Fatalf("resolutions = %+v", value.Resolutions)
	}
}

// Verifies: FX-MODULE-I02.
func TestFxSeamDecorationToNestedModuleValueFailure(t *testing.T) {
	fact := resolved("service", "ambiguous")
	fact.Name = "named"
	fact.Group = "grouped"
	_, err := receipt.Capture(graphPlan(t, "tag-ambiguous", "resolution"), appJournal(t, fact))
	if err == nil {
		t.Fatal("one resolution was both named and grouped")
	}
}

// Verifies: FX-ROLLBACK-I01.
func TestFxSeamStartFailureToPriorHookRollbackPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "rollback-seam", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), startHook("three", 2, 2, false, "start-three"), terminalHook("two", "rollback", 1, 0, "rollback-two"), terminalHook("one", "rollback", 0, 1, ""))
	if value.Hooks[2].ErrorClass != "start-three" || value.Hooks[3].ID != "two" || value.Hooks[4].ID != "one" {
		t.Fatalf("hooks = %+v", value.Hooks)
	}
}

// Verifies: FX-ROLLBACK-I01.
func TestFxSeamStartFailureToPriorHookRollbackFailure(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "rollback-order", "lifecycle"), appJournal(t, startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), startHook("three", 2, 2, false, "start-three"), terminalHook("one", "rollback", 0, 0, ""), terminalHook("two", "rollback", 1, 1, "")))
	if err == nil {
		t.Fatal("forward rollback order was accepted")
	}
}

// Verifies: FX-ROLLBACK-I02.
func TestFxSeamRollbackToLifecycleEventsPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "rollback-events", "lifecycle", "events"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, false, "start-two"), terminalHook("one", "rollback", 0, 0, ""), event("start", "one", 1, true, ""), event("start", "two", 2, false, "start-two"), event("rollback", "one", 3, true, ""))
	if len(value.Hooks) != 3 || len(value.Events) != 3 || value.Events[2].Kind != "rollback" {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-ROLLBACK-I02.
func TestFxSeamRollbackToLifecycleEventsFailure(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "rollback-events-bad", "events"), appJournal(t, event("start", "one", 2, true, ""), event("rollback", "one", 1, true, "")))
	if err == nil {
		t.Fatal("nonmonotonic lifecycle events were accepted")
	}
}

// Verifies: FX-STOP-I01.
func TestFxSeamStartedHooksToReverseStopPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "reverse-stop", "lifecycle"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), startHook("three", 2, 2, true, ""), terminalHook("three", "stop", 2, 0, ""), terminalHook("two", "stop", 1, 1, ""), terminalHook("one", "stop", 0, 2, ""))
	if got := []string{value.Hooks[3].ID, value.Hooks[4].ID, value.Hooks[5].ID}; !reflect.DeepEqual(got, []string{"three", "two", "one"}) {
		t.Fatalf("stop order = %+v", got)
	}
}

// Verifies: FX-STOP-I01.
func TestFxSeamStartedHooksToReverseStopFailure(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "reverse-stop-bad", "lifecycle"), appJournal(t, startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("two", "stop", 1, 1, ""), terminalHook("one", "stop", 0, 0, "")))
	if err == nil {
		t.Fatal("noncontiguous stop execution was accepted")
	}
}

// Verifies: FX-STOP-I02.
func TestFxSeamStopErrorsToEventLogPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "stop-events", "lifecycle", "events"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("two", "stop", 1, 0, "stop-two"), terminalHook("one", "stop", 0, 1, ""), event("stop", "two", 1, false, "stop-two"), event("stop", "one", 2, true, ""))
	if value.Hooks[2].ErrorClass != value.Events[0].ErrorClass || !value.Events[1].Succeeded {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-STOP-I02.
func TestFxSeamStopErrorsToEventLogFailure(t *testing.T) {
	_, err := receipt.Capture(graphPlan(t, "stop-event-bad", "events"), appJournal(t, event("stop", "one", 1, true, "stop-error")))
	if err == nil {
		t.Fatal("successful stop event retained an error class")
	}
}

// Verifies: FX-ERRGRAPH-I01.
func TestFxSeamGraphFailureToErrorHandlerPrimary(t *testing.T) {
	failed := demanded("invoke", "service")
	failed.ErrorClass = "invoke-error"
	value := captureReceipt(t, graphPlan(t, "graph-handler", "events"), failed, event("error-handler", "invoke", 1, false, "invoke-error"))
	if value.Constructors[0].ErrorClass != value.Events[0].ErrorClass {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-ERRGRAPH-I02.
func TestFxSeamErrorGraphToEventSequencePrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "graph-sequence", "events"), event("provided", "database", 1, true, ""), event("invoking", "handler", 2, true, ""), event("invoked", "handler", 3, false, "invoke-error"))
	if value.Events[0].Sequence != 1 || value.Events[2].Sequence != 3 || value.Events[2].Succeeded {
		t.Fatalf("events = %+v", value.Events)
	}
}

// Verifies: FX-ERRGRAPH-I03.
func TestFxSeamMissingDependencyToAnnotatedModulePrimary(t *testing.T) {
	failed := demanded("module-invoke", "named:database")
	failed.Scope = "root/module"
	failed.ErrorClass = "missing-named-dependency"
	value := captureReceipt(t, graphPlan(t, "module-graph", "events"), failed, event("invoke", "module-invoke", 1, false, "missing-named-dependency"))
	if value.Constructors[0].Scope != "root/module" || value.Events[0].Operation != "module-invoke" {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-SHUTDOWN-I01.
func TestFxSeamShutdownerToWaitChannelPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "shutdown-wait", "events", "shutdown"), event("shutdown-requested", "shutdowner", 1, true, ""), shutdown(2, 17, false))
	if value.Shutdown.Delivered != 2 || value.Shutdown.ExitCode != 17 || value.Events[0].Kind != "shutdown-requested" {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-SHUTDOWN-I02.
func TestFxSeamShutdownToLifecycleStopPrimary(t *testing.T) {
	before := captureReceipt(t, graphPlan(t, "shutdown-before", "shutdown"), shutdown(1, 0, false))
	after := captureReceipt(t, graphPlan(t, "shutdown-after", "shutdown"), shutdown(1, 0, true))
	if before.Shutdown.StopCompleted || !after.Shutdown.StopCompleted || !containsChange(receipt.Diff(before, after).Changes, "shutdown/") {
		t.Fatalf("before/after = %+v / %+v", before.Shutdown, after.Shutdown)
	}
}

// Verifies: FX-SHUTDOWN-I03.
func TestFxSeamRepeatedShutdownToSingleSignalPrimary(t *testing.T) {
	first := captureReceipt(t, graphPlan(t, "shutdown-repeat", "shutdown"), shutdown(3, 9, false))
	second := captureReceipt(t, graphPlan(t, "shutdown-repeat", "shutdown"), shutdown(3, 9, false))
	if !first.Equivalent(second) || len(receipt.Diff(first, second).Changes) != 0 {
		t.Fatalf("receipts diverged: %+v", receipt.Diff(first, second))
	}
}

// Verifies: FX-GROUP-I01.
func TestFxSeamAnnotatedNameToParameterObjectPrimary(t *testing.T) {
	fact := resolved("database", "parameter-object")
	fact.Name = "primary"
	value := captureReceipt(t, graphPlan(t, "named-parameter", "resolution"), fact)
	if value.Resolutions[0].Name != "primary" || !value.Resolutions[0].Resolved {
		t.Fatalf("resolution = %+v", value.Resolutions[0])
	}
}

// Verifies: FX-GROUP-I02.
func TestFxSeamGroupedResultsToInputSlicePrimary(t *testing.T) {
	first := resolved("handler-a", "parameter-object")
	first.Group = "handlers"
	second := resolved("handler-b", "parameter-object")
	second.Group = "handlers"
	second.Contribution = 1
	value := captureReceipt(t, graphPlan(t, "group-input", "resolution"), first, second)
	if len(value.Resolutions) != 2 || value.Resolutions[0].Contribution != 0 || value.Resolutions[1].Contribution != 1 {
		t.Fatalf("resolutions = %+v", value.Resolutions)
	}
}

// Verifies: FX-GROUP-I03.
func TestFxSeamSoftGroupToConstructionDemandPrimary(t *testing.T) {
	first := resolved("plugin-a", "collector")
	first.Group = "plugins"
	second := resolved("plugin-b", "collector")
	second.Group = "plugins"
	second.Contribution = 1
	value := captureReceipt(t, graphPlan(t, "soft-group", "resolution"), demanded("collector", "plugins"), first, second)
	if !value.Constructors[0].Demanded || len(value.Resolutions) != 2 {
		t.Fatalf("receipt = %+v", value)
	}
}

// Verifies: FX-ERRGRAPH-I04.
func TestFxSeamDotGraphToMissingDependencyPrimary(t *testing.T) {
	before := captureReceipt(t, graphPlan(t, "graph-before"), unused("provider", "service"))
	failed := demanded("provider", "service")
	failed.ErrorClass = "missing-dependency"
	after := captureReceipt(t, graphPlan(t, "graph-after"), failed)
	changes := receipt.Diff(before, after).Changes
	if !containsChange(changes, "application/") || !containsChange(changes, "constructors/") {
		t.Fatalf("changes = %+v", changes)
	}
}

// Verifies: FX-ERRGRAPH-I04.
func TestFxSeamDotGraphToMissingDependencyFailure(t *testing.T) {
	failed := demanded("missing", "service")
	failed.ErrorClass = "missing-dependency"
	_, err := receipt.Capture(graphPlan(t, "graph-event-edge", "events"), appJournal(t, failed))
	if err == nil {
		t.Fatal("missing dependency lacked matching event projection")
	}
}

// Verifies: FX-SHUTDOWN-I04.
func TestFxSeamShutdownSignalToWaitReceiptPrimary(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "shutdown-primary", "shutdown"), shutdown(1, 42, false))
	if value.Shutdown == nil || value.Shutdown.ExitCode != 42 || !value.Shutdown.WaitCompleted {
		t.Fatalf("shutdown = %+v", value.Shutdown)
	}
}

// Verifies: FX-SHUTDOWN-I04.
func TestFxSeamShutdownSignalToWaitReceiptEdge(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "shutdown-edge", "shutdown"), shutdown(3, -1, false))
	if value.Shutdown.Delivered != 3 || value.Shutdown.ExitCode != -1 {
		t.Fatalf("shutdown = %+v", value.Shutdown)
	}
}

// Verifies: FX-GROUP-I04.
func TestFxSeamNamedAndGroupedResolutionPrimary(t *testing.T) {
	fact := resolved("database", "named-consumer")
	fact.Name = "primary"
	value := captureReceipt(t, graphPlan(t, "named-primary", "resolution"), fact)
	if value.Resolutions[0].Name != "primary" || value.Resolutions[0].Group != "" {
		t.Fatalf("resolution = %+v", value.Resolutions[0])
	}
}

// Verifies: FX-GROUP-I04.
func TestFxSeamNamedAndGroupedResolutionEdge(t *testing.T) {
	first := resolved("handler", "group-consumer")
	first.Group = "handlers"
	second := first
	second.Key = "handler-two"
	second.Contribution = 1
	value := captureReceipt(t, graphPlan(t, "group-edge", "resolution"), first, second)
	if len(value.Resolutions) != 2 || value.Resolutions[1].Contribution != 1 {
		t.Fatalf("resolutions = %+v", value.Resolutions)
	}
}

// Verifies: FX-NATIVE-SEAM-004.
func TestFxSeamValidateToErrorHookSeamPrimary(t *testing.T) {
	recorder := &errorRecorder{}
	options := []fx.Option{fx.NopLogger, fx.Invoke(func() error { return errNativeInvoke }), fx.ErrorHook(recorder)}
	if err := fx.ValidateApp(options...); err != nil {
		t.Fatalf("ValidateApp() rejected a structurally valid graph: %v", err)
	}
	app := fx.New(options...)
	observed := recorder.Errors()
	if !errors.Is(app.Err(), errNativeInvoke) || len(observed) != 1 || !errors.Is(observed[0], errNativeInvoke) {
		t.Fatalf("app/handler errors = %v / %+v", app.Err(), observed)
	}
}

// Verifies: FX-NATIVE-SEAM-005.
func TestFxSeamOptionCompositionToAppSeamPrimary(t *testing.T) {
	input := &suppliedValue{Value: "options"}
	var observed *suppliedValue
	options := fx.Options(fx.Supply(input), fx.Invoke(func(value *suppliedValue) { observed = value }))
	app := fx.New(fx.NopLogger, options)
	if app.Err() != nil || observed != input {
		t.Fatalf("app error = %v, observed = %+v", app.Err(), observed)
	}
}

// Verifies: FX-NATIVE-SEAM-006.
func TestFxSeamPrinterToOptionStringSeamPrimary(t *testing.T) {
	printer := &memoryPrinter{}
	option := fx.Supply(&suppliedValue{Value: "printed"})
	app := fx.New(fx.Logger(printer), option, fx.Invoke(func(*suppliedValue) {}))
	if app.Err() != nil || len(printer.Lines()) == 0 || fmt.Sprint(option) == "" {
		t.Fatalf("app error = %v, lines = %d, option = %q", app.Err(), len(printer.Lines()), fmt.Sprint(option))
	}
}

// Verifies: FX-NATIVE-SEAM-007.
func TestFxSeamPopulateToLifecycleSeamPrimary(t *testing.T) {
	effects := make([]string, 0, 2)
	var populated *suppliedValue
	app := fx.New(fx.NopLogger,
		fx.Provide(func(lifecycle fx.Lifecycle) *suppliedValue {
			lifecycle.Append(fx.Hook{OnStart: func(context.Context) error { effects = append(effects, "start"); return nil }, OnStop: func(context.Context) error { effects = append(effects, "stop"); return nil }})
			return &suppliedValue{Value: "lifecycle"}
		}),
		fx.Populate(&populated),
	)
	if app.Err() != nil || populated == nil {
		t.Fatalf("app error = %v, populated = %+v", app.Err(), populated)
	}
	startAndStop(t, app)
	if !reflect.DeepEqual(effects, []string{"start", "stop"}) {
		t.Fatalf("effects = %+v", effects)
	}
}

// Verifies: FX-LAZY-S01.
func TestFxE2EFreshDemandConstructionReceiptFreshReceipt(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "fresh-demand", "resolution"), demanded("database", "db"), demanded("service", "service"), unused("unused", "unused"), resolved("db", "service"), resolved("service", "invoke"))
	if value.Constructors[0].ID != "database" || value.Constructors[2].Ran || value.Resolutions[1].Key != "service" || value.Digest() == "" {
		t.Fatalf("fresh receipt = %+v", value)
	}
}

// Verifies: FX-MODULE-S01.
func TestFxE2EFreshNestedModuleDecorationReceiptFreshReceipt(t *testing.T) {
	private := receipt.ResolutionFact{Key: "private", ProviderScope: "root/module", ConsumerScope: "root/module/child", Consumer: "child", Resolved: true}
	decorated := receipt.ResolutionFact{Key: "service", ProviderScope: "root", ConsumerScope: "root/module/child", DecoratorScope: "root/module", Consumer: "child", Resolved: true}
	outside := resolved("service", "outside")
	value := captureReceipt(t, graphPlan(t, "fresh-module", "resolution"), private, decorated, outside)
	if len(value.Resolutions) != 3 || value.Resolutions[0].ProviderScope != "root/module" || value.Resolutions[2].DecoratorScope != "" {
		t.Fatalf("fresh receipt = %+v", value)
	}
}

// Verifies: FX-ROLLBACK-S01.
func TestFxE2EFreshStartFailureRollbackReceiptFreshReceipt(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "fresh-rollback", "lifecycle", "events"), demanded("one", "one"), demanded("two", "two"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, false, "start-two"), terminalHook("one", "rollback", 0, 0, "rollback-one"), event("start", "one", 1, true, ""), event("start", "two", 2, false, "start-two"), event("rollback", "one", 3, false, "rollback-one"))
	if len(value.Constructors) != 2 || value.Hooks[2].ID != "one" || value.Events[2].Kind != "rollback" {
		t.Fatalf("fresh receipt = %+v", value)
	}
}

// Verifies: FX-STOP-S01.
func TestFxE2EFreshReverseStopReceiptFreshReceipt(t *testing.T) {
	value := captureReceipt(t, graphPlan(t, "fresh-stop", "lifecycle", "shutdown"), demanded("one", "one"), demanded("two", "two"), startHook("one", 0, 0, true, ""), startHook("two", 1, 1, true, ""), terminalHook("two", "stop", 1, 0, ""), terminalHook("one", "stop", 0, 1, ""), shutdown(1, 0, true))
	if value.Hooks[2].ID != "two" || value.Hooks[3].ID != "one" || value.Shutdown == nil || !value.Shutdown.StopCompleted {
		t.Fatalf("fresh receipt = %+v", value)
	}
}

// Verifies: FX-ERRGRAPH-S01.
func TestFxE2EFreshGraphFailureReceiptFreshReceipt(t *testing.T) {
	failed := demanded("graph-invoke", "named:missing")
	failed.ErrorClass = "missing-dependency"
	value := captureReceipt(t, graphPlan(t, "fresh-graph", "events"), failed, event("error-handler", "graph-invoke", 1, false, "missing-dependency"), event("invoked", "graph-invoke", 2, false, "missing-dependency"))
	copy := value
	copy.Events = append([]receipt.EventFact(nil), value.Events...)
	if value.Events[0].ErrorClass != failed.ErrorClass || !value.Equivalent(copy) || value.Digest() == "" {
		t.Fatalf("fresh receipt = %+v", value)
	}
}

// Verifies: FX-NATIVE-SYS-001.
func TestFxE2ENativeSupplyInvokeLifecycleFreshReceipt(t *testing.T) {
	input := &suppliedValue{Value: "fresh-native"}
	effects := make([]string, 0, 3)
	app := fx.New(fx.NopLogger,
		fx.Supply(input),
		fx.Provide(func(lifecycle fx.Lifecycle, value *suppliedValue) *unrelatedValue {
			lifecycle.Append(fx.Hook{OnStart: func(context.Context) error { effects = append(effects, "start:"+value.Value); return nil }, OnStop: func(context.Context) error { effects = append(effects, "stop:"+value.Value); return nil }})
			return &unrelatedValue{Value: value.Value}
		}),
		fx.Invoke(func(value *unrelatedValue) { effects = append(effects, "invoke:"+value.Value) }),
	)
	if app.Err() != nil {
		t.Fatal(app.Err())
	}
	startAndStop(t, app)
	if !reflect.DeepEqual(effects, []string{"invoke:fresh-native", "start:fresh-native", "stop:fresh-native"}) {
		t.Fatalf("effects = %+v", effects)
	}
}

// Verifies: FX-NATIVE-SYS-002.
func TestFxE2ENativeReplacePopulateAppFreshReceipt(t *testing.T) {
	replacement := &replacementValue{Value: "fresh-replacement"}
	unrelated := &unrelatedValue{Value: "stable"}
	var gotReplacement *replacementValue
	var gotUnrelated *unrelatedValue
	options := fx.Options(fx.Supply(&replacementValue{Value: "old"}, unrelated), fx.Replace(replacement), fx.Populate(&gotReplacement, &gotUnrelated))
	app := fx.New(fx.NopLogger, options)
	if app.Err() != nil || gotReplacement != replacement || gotUnrelated != unrelated {
		t.Fatalf("app error = %v, outputs = %+v, %+v", app.Err(), gotReplacement, gotUnrelated)
	}
}

// Verifies: FX-NATIVE-SYS-003.
func TestFxE2ENativeValidateProvideInvokeFreshReceipt(t *testing.T) {
	recorder := &errorRecorder{}
	options := []fx.Option{
		fx.NopLogger,
		fx.Provide(func() *suppliedValue { return &suppliedValue{Value: "fresh"} }),
		fx.Invoke(func(*suppliedValue) error { return errNativeInvoke }),
		fx.ErrorHook(recorder),
	}
	if err := fx.ValidateApp(options...); err != nil {
		t.Fatalf("ValidateApp() error = %v", err)
	}
	app := fx.New(options...)
	errs := recorder.Errors()
	if !errors.Is(app.Err(), errNativeInvoke) || len(errs) != 1 || !errors.Is(errs[0], errNativeInvoke) {
		t.Fatalf("app/handler errors = %v / %+v", app.Err(), errs)
	}
}

func sortedStrings(values []string) []string {
	copy := append([]string(nil), values...)
	sort.Strings(copy)
	return copy
}
