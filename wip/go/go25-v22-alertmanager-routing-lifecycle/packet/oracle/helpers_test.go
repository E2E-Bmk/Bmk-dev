package alertmanagergate_test

import (
	"testing"

	"github.com/prometheus/alertmanager/pkg/labels"
	"github.com/prometheus/alertmanager/receipt"
)

func lifecycle(t *testing.T, root string) receipt.LifecycleReceipt {
	t.Helper()
	plan := receipt.NewRoutingPlan()
	if _, err := plan.SelectAlert("", map[string]string{"severity": "critical"}); err == nil {
		t.Fatal("empty alert accepted")
	}
	var err error
	alert := "alert-" + root
	plan, err = plan.SelectAlert(alert, map[string]string{"severity": "critical", "service": "api"})
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeGroups().IncludeSuppressions().IncludeDeliveries().IncludeAPIState()
	group := "service=api/" + root
	routes := []receipt.RouteFact{{Alert: alert, Receiver: "oncall", GroupKey: group, Matched: true, Generation: 1}}
	groups := []receipt.GroupFact{{Key: group, State: "firing", Alerts: []string{alert}, StartedAt: 10, SendAt: 20}}
	suppressions := []receipt.SuppressionFact{
		{Alert: alert, Kind: "silence", Rule: "silence-1", Active: true},
		{Alert: alert, Kind: "inhibition", Rule: "inhibit-1", Source: "source-alert", Target: alert, Active: true, EqualLabels: map[string]string{"service": "api"}},
	}
	api := &receipt.APIStateFact{Generation: 1, Alerts: []string{alert}, Groups: []string{group}, Silences: []string{"silence-1"}, History: []string{group}, View: "http-api"}
	journal := receipt.NewDeliveryJournal()
	first := journal.Record(receipt.DeliveryFact{Receiver: "oncall", GroupKey: group, Alert: alert, Attempt: 1, Complete: true})
	second := journal.Record(receipt.DeliveryFact{Receiver: "oncall", GroupKey: group, Alert: alert, Attempt: 2, Deduplicated: true})
	if first.Seq != 1 || second.Seq != 2 || len(journal.Entries()) != 2 {
		t.Fatal("delivery journal lost order")
	}
	got, err := receipt.Capture(plan, routes, groups, suppressions, api, journal)
	if err != nil {
		t.Fatal(err)
	}
	if got.Digest() == "" || got.Validate() != nil {
		t.Fatal("invalid lifecycle receipt")
	}
	api.Alerts[0] = "changed"
	if got.APIState.Alerts[0] == "changed" {
		t.Fatal("capture retained API storage")
	}
	return got
}

func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	got := lifecycle(t, root)
	switch family {
	case "M-ROUTE-MATCHING":
		bad := got
		bad.Routes = append([]receipt.RouteFact(nil), got.Routes...)
		bad.Routes[0].Matched = false
		if bad.Validate() == nil {
			t.Fatal("unmatched route validated")
		}
	case "M-GROUP-LIFECYCLE":
		bad := got
		bad.Groups = append([]receipt.GroupFact(nil), got.Groups...)
		bad.Groups[0].SendAt = bad.Groups[0].StartedAt - 1
		if bad.Validate() == nil {
			t.Fatal("reversed group timing validated")
		}
	case "M-SILENCE-STATE":
		bad := got
		bad.Suppressions = append([]receipt.SuppressionFact(nil), got.Suppressions...)
		bad.Suppressions[0].Rule = "missing-silence"
		if bad.Validate() == nil {
			t.Fatal("invisible active silence validated")
		}
	case "M-INHIBITION-JOIN":
		bad := got
		bad.Suppressions = append([]receipt.SuppressionFact(nil), got.Suppressions...)
		bad.Suppressions[1].Source = bad.Suppressions[1].Target
		if bad.Validate() == nil {
			t.Fatal("self inhibition validated")
		}
	case "M-NOTIFICATION-DELIVERY":
		bad := got
		bad.Deliveries = append([]receipt.DeliveryFact(nil), got.Deliveries...)
		bad.Deliveries[0].Error = "webhook failed"
		if bad.Validate() == nil {
			t.Fatal("failed delivery claimed completion")
		}
	case "M-NFLOG-DEDUP":
		bad := got
		bad.Deliveries = append([]receipt.DeliveryFact(nil), got.Deliveries...)
		bad.Deliveries[1].Complete = true
		if bad.Validate() == nil {
			t.Fatal("deduplicated delivery claimed completion")
		}
	case "M-API-STATE":
		other := got
		state := *got.APIState
		other.APIState = &state
		other.APIState.View = "amtool"
		if !got.Equivalent(other) {
			t.Fatal("API and amtool views diverged")
		}
	case "M-CONFIG-RELOAD":
		changed := got
		changed.Routes = append([]receipt.RouteFact(nil), got.Routes...)
		changed.Routes[0].Receiver = "secondary"
		if len(receipt.Diff(got, changed).Changes) != 1 {
			t.Fatal("accepted reload was hidden")
		}
	default:
		t.Fatalf("unknown family %q", family)
	}
}

func runNative(t *testing.T, root, _ string) {
	t.Helper()
	equal, err := labels.NewMatcher(labels.MatchEqual, "service", "api")
	if err != nil || !equal.Matches("api") || equal.Matches("worker") {
		t.Fatal("native equality matcher drift")
	}
	regexpMatcher, err := labels.NewMatcher(labels.MatchRegexp, "severity", "crit.*")
	if err != nil || !regexpMatcher.Matches("critical") || regexpMatcher.Matches("warning") {
		t.Fatal("native regexp matcher drift")
	}
	parsed, err := labels.ParseMatchers(`{service="api",severity=~"crit.*"}`)
	if err != nil || len(parsed) != 2 || parsed[0].String() == "" || root == "" {
		t.Fatal("native matcher parser drift")
	}
	if _, err := labels.ParseMatcher(`bad matcher`); err == nil {
		t.Fatal("invalid native matcher accepted")
	}
}
