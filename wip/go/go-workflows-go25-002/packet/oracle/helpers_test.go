package workflowsgate_test

import (
	"github.com/cschleiden/go-workflows/receipt"
	"testing"
)

func workflowReceipt(t *testing.T, root string) receipt.WorkflowReceipt {
	t.Helper()
	plan := receipt.NewReplayPlan()
	selection := receipt.WorkflowSelection{InstanceID: "instance-" + root, ExecutionID: "execution-1", TraverseLineage: true}
	plan, err := plan.Select(selection)
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeHistory().IncludeAttempts().IncludeSignals().IncludeTimers().IncludeResult()
	observation := receipt.WorkflowReceipt{EventIDs: []string{"event-001", "event-002", "event-003"}, Attempts: []int{1, 2}, Timers: []int64{10, 20}, Signals: []string{"start", "finish"}, Lineage: []string{"execution-1", "execution-2"}, Result: "ok-" + root, Status: receipt.ReceiptCompleted, Backend: receipt.BackendProjection{Kind: "memory", Path: "memory://local", ProcessID: "p1"}, Generation: 1}
	got, err := receipt.CaptureWorkflow(plan, observation)
	if err != nil {
		t.Fatal(err)
	}
	if receipt.HistoryDigest(got) == "" || got.Validate() != nil {
		t.Fatal("invalid workflow receipt")
	}
	return got
}

func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	got := workflowReceipt(t, root)
	switch root {
	case "A01":
		replayPlanSelectionScenario(t, got)
	case "A02":
		captureValidationScenario(t, got)
	case "I01":
		historyDetachmentScenario(t, got)
	case "I02":
		historyOrderingScenario(t, got)
	case "S01":
		historyDigestScenario(t, got)
	case "A03":
		stableGenerationScenario(t, got)
	case "A04":
		activityAttemptGapScenario(t, got)
	case "I03":
		activityDetachmentScenario(t, got)
	case "I04":
		activityDigestScenario(t, got)
	case "I05":
		activityStartsAtOneScenario(t, got)
	case "S02":
		completedResultScenario(t, got)
	case "A05":
		negativeTimerScenario(t, got)
	case "A06":
		timerOrderingScenario(t, got)
	case "I06":
		timerDetachmentScenario(t, got)
	case "I07":
		timerDigestScenario(t, got)
	case "I08":
		equalDeadlineScenario(t, got)
	case "S03":
		timerBackendTransferScenario(t, got)
	case "A07":
		emptySignalScenario(t, got)
	case "A08":
		duplicateSignalScenario(t, got)
	case "I09":
		signalDetachmentScenario(t, got)
	case "I10":
		signalDigestScenario(t, got)
	case "S04":
		signalReorderingScenario(t, got)
	case "A09":
		backendKindScenario(t, got)
	case "I11":
		backendPathScenario(t, got)
	case "I12":
		backendProcessScenario(t, got)
	case "I13":
		backendCompositeScenario(t, got)
	case "I18":
		backendGenerationScenario(t, got)
	case "S05":
		backendResultScenario(t, got)
	case "I14":
		emptyLineageScenario(t, got)
	case "I15":
		lineageCycleScenario(t, got)
	case "I19":
		lineageDetachmentAndDigestScenario(t, got)
	case "I16":
		cancelledLockScenario(t, got)
	case "I17":
		cancelledResultScenario(t, got)
	case "I20":
		cancelledStatusAndDigestScenario(t, got)
	default:
		t.Fatalf("unknown synthetic root %q in %q", root, family)
	}
}

func replayPlanSelectionScenario(t *testing.T, _ receipt.WorkflowReceipt) {
	plan := receipt.NewReplayPlan()
	if _, err := plan.Select(receipt.WorkflowSelection{}); err == nil {
		t.Fatal("blank workflow selection accepted")
	}
}

func captureValidationScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.EventIDs = []string{"event-001", "event-003"}
	if _, err := receipt.CaptureWorkflow(got.Plan, bad); err == nil {
		t.Fatal("capture accepted invalid history")
	}
}

func historyDetachmentScenario(t *testing.T, got receipt.WorkflowReceipt) {
	observation := got
	observation.EventIDs = append([]string(nil), got.EventIDs...)
	captured, err := receipt.CaptureWorkflow(got.Plan, observation)
	if err != nil {
		t.Fatal(err)
	}
	observation.EventIDs[0] = "changed"
	if captured.EventIDs[0] == "changed" {
		t.Fatal("captured history shares caller storage")
	}
}

func historyOrderingScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.EventIDs = []string{"event-001", "event-003"}
	if bad.Validate() == nil {
		t.Fatal("noncontiguous history validated")
	}
}

func historyDigestScenario(t *testing.T, got receipt.WorkflowReceipt) {
	changed := got
	changed.EventIDs = []string{"event-001", "event-002", "event-003", "event-004"}
	if len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("history change missing from digest")
	}
}

func stableGenerationScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Generation = 0
	if bad.Validate() == nil {
		t.Fatal("zero generation validated")
	}
}

func activityAttemptGapScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Attempts = []int{1, 3}
	if bad.Validate() == nil {
		t.Fatal("activity attempt gap validated")
	}
}

func activityDetachmentScenario(t *testing.T, got receipt.WorkflowReceipt) {
	observation := got
	observation.Attempts = append([]int(nil), got.Attempts...)
	captured, err := receipt.CaptureWorkflow(got.Plan, observation)
	if err != nil {
		t.Fatal(err)
	}
	observation.Attempts[0] = 99
	if captured.Attempts[0] == 99 {
		t.Fatal("captured attempts share caller storage")
	}
}

func activityDigestScenario(t *testing.T, got receipt.WorkflowReceipt) {
	changed := got
	changed.Attempts = []int{1, 2, 3}
	if len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("attempt change missing from digest")
	}
}

func activityStartsAtOneScenario(t *testing.T, got receipt.WorkflowReceipt) {
	valid := got
	valid.Attempts = []int{1}
	if err := valid.Validate(); err != nil {
		t.Fatalf("one-based initial attempt rejected: %v", err)
	}
	bad := got
	bad.Attempts = []int{0, 1}
	if bad.Validate() == nil {
		t.Fatal("zero-based attempts validated")
	}
}

func completedResultScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Result = ""
	if bad.Validate() == nil {
		t.Fatal("completed selected result may be empty")
	}
}

func negativeTimerScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Timers = []int64{-1, 10}
	if bad.Validate() == nil {
		t.Fatal("negative timer validated")
	}
}

func timerOrderingScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Timers = []int64{20, 10}
	if bad.Validate() == nil {
		t.Fatal("reversed timer order validated")
	}
}

func timerDetachmentScenario(t *testing.T, got receipt.WorkflowReceipt) {
	observation := got
	observation.Timers = append([]int64(nil), got.Timers...)
	captured, err := receipt.CaptureWorkflow(got.Plan, observation)
	if err != nil {
		t.Fatal(err)
	}
	observation.Timers[0] = 99
	if captured.Timers[0] == 99 {
		t.Fatal("captured timers share caller storage")
	}
}

func timerDigestScenario(t *testing.T, got receipt.WorkflowReceipt) {
	changed := got
	changed.Timers = []int64{10, 21}
	if len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("timer change missing from digest")
	}
}

func equalDeadlineScenario(t *testing.T, got receipt.WorkflowReceipt) {
	valid := got
	valid.Timers = []int64{10, 10, 20}
	if err := valid.Validate(); err != nil {
		t.Fatalf("equal timer deadlines rejected: %v", err)
	}
}

func timerBackendTransferScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Backend.Path = "/var/tmp/replayed.db"
	other.Timers = []int64{10, 20, 30}
	if len(receipt.ReceiptDiff(got, other)) == 0 {
		t.Fatal("timer change disappeared during backend transfer")
	}
}

func emptySignalScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Signals = []string{"start", ""}
	if bad.Validate() == nil {
		t.Fatal("empty signal validated")
	}
}

func duplicateSignalScenario(t *testing.T, got receipt.WorkflowReceipt) {
	if len(got.Signals) < 2 {
		t.Fatal("fixture lacks ordered signal pair")
	}
	bad := got
	bad.Signals = []string{"start", "start"}
	if bad.Validate() == nil {
		t.Fatal("duplicate signal validated")
	}
}

func signalDetachmentScenario(t *testing.T, got receipt.WorkflowReceipt) {
	observation := got
	observation.Signals = append([]string(nil), got.Signals...)
	captured, err := receipt.CaptureWorkflow(got.Plan, observation)
	if err != nil {
		t.Fatal(err)
	}
	observation.Signals[0] = "changed"
	if captured.Signals[0] == "changed" {
		t.Fatal("captured signals share caller storage")
	}
}

func signalDigestScenario(t *testing.T, got receipt.WorkflowReceipt) {
	changed := got
	changed.Signals = []string{"start", "finish", "archive"}
	if len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("signal change missing from digest")
	}
}

func signalReorderingScenario(t *testing.T, got receipt.WorkflowReceipt) {
	changed := got
	changed.Signals = []string{"finish", "start"}
	if changed.Validate() != nil || len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("signal reordering was not observable")
	}
}

func backendKindScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Backend.Kind = "sqlite"
	if len(receipt.ReceiptDiff(got, other)) != 0 {
		t.Fatal("backend kind changed semantics")
	}
}

func backendPathScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Backend.Path = "file:/tmp/workflow.db"
	if len(receipt.ReceiptDiff(got, other)) != 0 {
		t.Fatal("backend path changed semantics")
	}
}

func backendProcessScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Backend.ProcessID = "worker-42"
	if len(receipt.ReceiptDiff(got, other)) != 0 {
		t.Fatal("backend process changed semantics")
	}
}

func backendCompositeScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Backend = receipt.BackendProjection{Kind: "sqlite", Path: "file:reopen.db", ProcessID: "replacement"}
	if len(receipt.ReceiptDiff(got, other)) != 0 {
		t.Fatal("combined backend identity changed semantics")
	}
}

func backendGenerationScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Generation++
	if len(receipt.ReceiptDiff(got, other)) == 0 {
		t.Fatal("stable generation change was ignored")
	}
}

func backendResultScenario(t *testing.T, got receipt.WorkflowReceipt) {
	other := got
	other.Result = "different-result"
	if len(receipt.ReceiptDiff(got, other)) == 0 {
		t.Fatal("terminal result change was ignored")
	}
}

func emptyLineageScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Lineage = []string{"execution-1", ""}
	if bad.Validate() == nil {
		t.Fatal("empty lineage execution validated")
	}
}

func lineageCycleScenario(t *testing.T, got receipt.WorkflowReceipt) {
	if got.Lineage[0] == got.Lineage[1] {
		t.Fatal("fixture lineage already cyclic")
	}
	bad := got
	bad.Lineage = []string{"execution-1", "execution-1"}
	if bad.Validate() == nil {
		t.Fatal("lineage cycle validated")
	}
}

func lineageDetachmentAndDigestScenario(t *testing.T, got receipt.WorkflowReceipt) {
	observation := got
	observation.Lineage = append([]string(nil), got.Lineage...)
	captured, err := receipt.CaptureWorkflow(got.Plan, observation)
	if err != nil {
		t.Fatal(err)
	}
	observation.Lineage[0] = "changed"
	if captured.Lineage[0] == "changed" {
		t.Fatal("captured lineage shares caller storage")
	}
	changed := got
	changed.Lineage = []string{"execution-1", "execution-2", "execution-3"}
	if len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("lineage change missing from digest")
	}
}

func cancelledLockScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Status, bad.Result, bad.LockToken = receipt.ReceiptCancelled, "", "abandoned"
	if bad.Validate() == nil {
		t.Fatal("cancelled receipt retained lock")
	}
}

func cancelledResultScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Status, bad.Result, bad.LockToken = receipt.ReceiptCancelled, "completed", ""
	if bad.LockToken != "" {
		t.Fatal("result scenario unexpectedly retained lock")
	}
	if bad.Validate() == nil {
		t.Fatal("cancelled receipt retained result")
	}
}

func cancelledStatusAndDigestScenario(t *testing.T, got receipt.WorkflowReceipt) {
	bad := got
	bad.Status, bad.Result = receipt.ReceiptStatus("failed"), ""
	if bad.Validate() == nil {
		t.Fatal("unknown status validated")
	}
	changed := got
	changed.Status = receipt.ReceiptRunning
	if len(receipt.ReceiptDiff(got, changed)) == 0 {
		t.Fatal("status change missing from digest")
	}
}
