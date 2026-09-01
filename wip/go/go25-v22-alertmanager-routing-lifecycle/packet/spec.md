# alertmanager Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in interface design, parameter naming, behavioral edge cases, and error semantics.
> Implementations derived from memory of external codebases will fail the evaluation.

# Context

## Product Overview

`alertmanager` is a Go alert-routing service that loads declarative configuration, stores alert state, matches route trees, forms timed groups, applies silence and inhibition rules, and delivers notifications. Its API and `amtool` command expose the same live alert, group, silence, and status projections.

Routing is label driven. Grouping and notification logs make repeated alert updates into a lifecycle rather than independent HTTP requests, while the last successfully applied configuration remains authoritative after a failed reload.

## Non-Goals

- This specification does not require high-availability gossip, external databases, public notification providers, or Internet delivery.
- This specification does not define wall-clock scheduling precision below configured duration boundaries.
- This specification does not require undocumented storage encodings, private dispatch helpers, or global process configuration.

# Orientation

## Representative Workflows

### Workflow 1: Route and deliver a local alert group

1. Load a configuration containing a top-level route, child matchers, grouping labels, timing values, and a loopback webhook receiver.
2. Start an in-memory alert provider, dispatcher, notification pipeline, marker set, and notification log.
3. Put firing alerts with controlled timestamps and wait for the configured group boundary.
4. Observe route selection and group state through the Go API and HTTP API.
5. Receive the webhook, query the notification log, resolve the alerts, and receive the resolved lifecycle when the receiver enables it.

### Workflow 2: Silence, inhibit, and reload

1. Store a silence with matchers and an active interval, then submit a matching alert.
2. Submit a source alert and target alert that satisfy one inhibition rule and its equal-label set.
3. Observe muted status, marker ownership, API projections, and absence of webhook delivery for the suppressed targets.
4. Reload a valid configuration and observe subsequent alerts using the new route tree.
5. Attempt an invalid reload and observe the last successful route tree and active lifecycle state unchanged.
6. Capture route, group, suppression, delivery, and API projections into one `receipt.LifecycleReceipt` and compare it with the preceding generation.

# Behavior

## Domain 1: Configuration, Routes, and Time Intervals

This domain defines how declarative input becomes the route tree used by every later alert decision.

**Configuration loading.** When `config.Load` or `LoadFile` receives valid YAML, it must return a `Config` containing one top-level `Route`, named `Receiver` values, inhibition rules, and named time intervals. Missing optional global values must receive `DefaultGlobalConfig` defaults. If receiver names are duplicated, route references are missing, intervals are invalid, or YAML is malformed, then loading must return an error and no applicable configuration.

**Route matching.** When `dispatch.NewRoute` receives a configuration route, it must inherit grouping and timing values from its parent unless the child declares replacements. When `Route.Match` receives labels, it must return matching routes in configured traversal order; a matching child with continuation disabled must stop sibling traversal, while continuation enabled must retain later matching siblings. If no child matches, then the top-level route must own the alert.

**Reload publication.** When `Coordinator.Reload` loads a valid file and every subscriber accepts it, the coordinator must publish the new configuration as one generation. If loading or any subscriber fails, then the coordinator must return an error and the preceding generation must remain active across route, receiver, and interval projections.

## Domain 2: Alert Groups, Silences, and Inhibition

This domain defines alert storage, timed grouping, and the two suppression mechanisms visible to callers.

**Alert lifecycle and grouping.** When `mem.Alerts.Put` receives an alert, it must normalize the alert lifecycle, publish it to subscribers, and make it retrievable by fingerprint. When dispatch receives matching alerts, it must group them by route and configured group labels, apply group-wait, group-interval, and repeat-interval boundaries, and expose live groups through `Dispatcher.Groups`. If an alert has invalid labels or lifecycle timestamps, then storage must return an error and must not publish that alert.

**Silences.** When `Silences.Set` receives a valid silence, it must assign or update its identity and make `Query`, `QueryOne`, `CurrentState`, and `Silencer.Mutes` agree on matcher and time state. When a silence expires, `Expire` must make later status observations report expiration. If a silence is missing, malformed, exceeds configured limits, or uses an invalid state transition, then the operation must return `ErrNotFound`, `ErrInvalidState`, or a descriptive validation error.

**Inhibition and markers.** When a source alert matches an `InhibitRule`, a target alert matches its target set, and every equal-label name has equal values, `Inhibitor.Mutes` must report the target as inhibited. An alert matching both source and target sides must not inhibit itself. `AlertMarker` and `GroupMarker` must publish the silence, inhibition, and time-interval reasons used by API and notification projections.

## Domain 3: Notification Delivery, Receipts, and API

This domain defines deduplication, retry decisions, webhook delivery, notification history, and public service views.

**Pipeline and deduplication.** When `PipelineBuilder.New` constructs a stage for a receiver, it must apply mute stages, deduplication, retry, delivery, and notification logging in their documented order. When the notification log already records the same group and firing/resolved fingerprint sets within the repeat interval, `DedupStage` must suppress duplicate delivery. If a stage fails, then the pipeline must return the stage error and must not record successful delivery.

**Webhook delivery and retry.** When a webhook integration receives a group, it must send one JSON message containing receiver, status, group labels, common labels, common annotations, external URL, and the selected alert subset. A successful 2xx response must return success. If the endpoint returns a retryable status or a transport error, then `RetryStage` must retry within the context deadline; if the response is non-retryable or the context expires, then delivery must return the final error.

**Notification log.** When `nflog.Log.Log` records a receiver, group key, and firing/resolved sets, a later `Query` with matching `QReceiver` and `QGroupKey` must return the entry until expiry. If no entry exists, query must return `nflog.ErrNotFound`. Snapshot and merge operations must preserve logical entries and expiry state.

**HTTP API and command parity.** When the v2 API receives alert or silence changes, its later alert, group, silence, and status reads must reflect the same provider, dispatcher, marker, silence, and config state. `amtool check-config`, alert queries, silence operations, and status queries must follow the corresponding API error and filter semantics. Invalid request data must return a non-success HTTP status or a nonzero command exit without partial state publication.

## Domain 4: Lifecycle Receipts and Projection Reconciliation

This domain defines a stable observation layer across routing, grouping, suppression, notification, history, and API state.

**Routing plans.** `receipt.NewRoutingPlan` must return an empty caller-owned plan. `RoutingPlan.SelectAlert` must associate a stable name with one alert identity, while `IncludeGroups`, `IncludeSuppressions`, `IncludeDeliveries`, and `IncludeAPIState` must select complete projections. Repeating a name must replace its alert without changing its original position. Empty names, nil alerts, and conflicting selections must return an error without changing the preceding plan.

**Lifecycle capture.** `receipt.Capture` must execute one plan against a coherent active configuration and return one complete `LifecycleReceipt`. `RouteFact`, `GroupFact`, `SuppressionFact`, `DeliveryFact`, and `APIStateFact` must reconcile receiver ownership, group keys, alert fingerprints, silence and inhibition reasons, notification-log state, webhook outcomes, and API resources. A failed selected projection or a configuration generation change during capture must return an error and no partial receipt.

**Delivery journal and recovery.** `receipt.NewDeliveryJournal` must create an empty ordered journal. `Record` must append one caller-owned `DeliveryFact` with a strictly increasing sequence, and `Entries` must return an independent snapshot. Retryable, terminal, canceled, deduplicated, and committed outcomes must remain distinguishable. A failed reload or delivery must retain the preceding successful lifecycle receipt and must not claim a later completed generation.

**Validation and comparison.** `LifecycleReceipt.Validate` must reject contradictions among routes, groups, suppressions, deliveries, history, and API state. `Digest` must ignore scheduling latency, temporary paths, and map order while preserving semantic group and lifecycle order. `Equivalent` and `receipt.Diff` must compare generations without changing either input.

# Contract

## State Model

Configuration moves through **unloaded**, **active generation**, **reloading**, **replacement active**, and **last-good retained** states. An alert moves through **received**, **pending group**, **firing group**, **suppressed**, **delivered**, **resolved**, and **expired** states. A silence moves through **pending**, **active**, **expired**, and **removed** states. Notification history moves through **absent**, **recorded**, and **expired** states.

Public projections are provider alerts, route matches, dispatch groups, markers, silence queries, inhibition decisions, webhook messages, notification-log entries, HTTP API resources, command output, and returned errors. A transition must become visible consistently across every affected projection.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid configuration or subscriber rejection | Reload must return an error and retain the last successful configuration. |
| Invalid alert labels or lifecycle | Provider insertion must return an error without publication. |
| Missing or invalid silence transition | Silence operations must return the applicable sentinel or validation error. |
| Missing notification-log entry | Query must return `nflog.ErrNotFound`. |
| Notification stage failure | The pipeline must return the error and omit a success receipt. |
| Retry deadline exceeded | Delivery must return the context error. |
| Invalid API payload or filter | The API must return a non-success status and no partial change. |
| Invalid command input | `amtool` must exit nonzero with a diagnostic. |

## Cross-View Invariants

1. The active configuration, route tree, receiver lookup, interval lookup, and status API must describe the same applied generation.
2. Provider fingerprints, dispatch group membership, marker status, webhook alerts, and API alerts must refer to the same alert identities.
3. Silence queries, `Silencer.Mutes`, markers, group views, and API status must agree at the same controlled time.
4. Inhibition decisions, marker reasons, group visibility, webhook omission, and API status must agree for each target alert.
5. Route grouping labels and receiver selection must remain identical across dispatcher groups, notification context, webhook messages, notification-log entries, and API groups.
6. A successful webhook response and its notification-log receipt must describe the same receiver, group key, firing set, and resolved set.
7. A failed reload must preserve route selection, suppression behavior, receiver choice, and API status from the preceding generation.
8. API and `amtool` projections must apply identical matcher, silence-state, and configuration-validation semantics.
9. A lifecycle receipt must reconcile selected route, group, suppression, delivery, history, and API facts under one configuration generation.
10. Equivalent lifecycle generations must produce equal receipt digests across fresh providers, loopback receivers, API clients, and command observations.

# Reference

## Public Interface

### Import Surface

- `github.com/prometheus/alertmanager/config`: `Config`, `GlobalConfig`, `Route`, `Receiver`, `TimeInterval`, `Load`, `LoadFile`, `DefaultGlobalConfig`, `Coordinator`, `NewCoordinator`
- `github.com/prometheus/alertmanager/types`: `Alert`, `AlertSlice`, `Alerts`
- `github.com/prometheus/alertmanager/provider/mem`: `Alerts`, `NewAlerts`
- `github.com/prometheus/alertmanager/dispatch`: `Route`, `RouteOpts`, `DefaultRouteOpts`, `NewRoute`, `Dispatcher`, `NewDispatcher`, `AlertGroup`, `AlertGroups`
- `github.com/prometheus/alertmanager/silence`: `Silences`, `Silencer`, `Options`, `New`, `NewSilencer`, `SilenceState`, `CurrentState`, `QIDs`, `QMatches`, `QState`, `ErrNotFound`, `ErrInvalidState`
- `github.com/prometheus/alertmanager/inhibit`: `Inhibitor`, `InhibitRule`, `NewInhibitor`, `NewInhibitRule`
- `github.com/prometheus/alertmanager/marker`: `AlertMarker`, `GroupMarker`, `NewAlertMarker`, `NewGroupMarker`, `WithContext`, `FromContext`
- `github.com/prometheus/alertmanager/notify`: `Notifier`, `Integration`, `NewIntegration`, `Stage`, `StageFunc`, `PipelineBuilder`, `NewPipelineBuilder`, `DedupStage`, `NewDedupStage`, `RetryStage`, `NewRetryStage`
- `github.com/prometheus/alertmanager/notify/webhook`: `Notifier`, `WebhookConfig`, `Message`, `New`
- `github.com/prometheus/alertmanager/nflog`: `Log`, `Options`, `New`, `QReceiver`, `QGroupKey`, `Store`, `NewStore`, `ErrNotFound`, `ErrInvalidState`
- `github.com/prometheus/alertmanager/api/v2`: `API`, `NewAPI`, `SortSilences`, `CheckSilenceMatchesFilterLabels`
- `github.com/prometheus/alertmanager/receipt`: `RoutingPlan`, `NewRoutingPlan`, `RouteFact`, `GroupFact`, `SuppressionFact`, `DeliveryFact`, `APIStateFact`, `DeliveryJournal`, `NewDeliveryJournal`, `LifecycleReceipt`, `ChangeReceipt`, `Capture`, `Diff`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `config.Config`, `GlobalConfig`, `Route`, `Receiver`, `TimeInterval` | types | Represent loaded routing configuration. |
| `config.Load`, `LoadFile`, `DefaultGlobalConfig` | functions | Load and default configuration. |
| `config.Coordinator`, `NewCoordinator` | type and function | Apply configuration generations to subscribers. |
| `types.Alert`, `AlertSlice`, `Alerts` | types and value | Represent and organize alert state. |
| `mem.Alerts`, `NewAlerts` | type and function | Store alerts and publish lifecycle changes. |
| `dispatch.Route`, `RouteOpts`, `DefaultRouteOpts`, `NewRoute` | types, value, and function | Build and match the route tree. |
| `dispatch.Dispatcher`, `NewDispatcher`, `AlertGroup`, `AlertGroups` | types and function | Form timed alert groups and expose them. |
| `silence.Silences`, `Options`, `New` | types and function | Store and query silence state. |
| `silence.Silencer`, `NewSilencer`, `SilenceState`, `CurrentState` | types and functions | Project silence state onto alert labels and time. |
| `silence.QIDs`, `QMatches`, `QState` | functions | Build silence query filters. |
| `silence.ErrNotFound`, `ErrInvalidState` | error values | Identify silence lookup and transition failures. |
| `inhibit.Inhibitor`, `InhibitRule`, `NewInhibitor`, `NewInhibitRule` | types and functions | Evaluate source/target inhibition. |
| `marker.AlertMarker`, `GroupMarker`, `NewAlertMarker`, `NewGroupMarker`, `WithContext`, `FromContext` | interfaces and functions | Publish alert and group suppression reasons. |
| `notify.Notifier`, `Integration`, `NewIntegration` | interface, type, and function | Represent a receiver delivery integration. |
| `notify.Stage`, `StageFunc`, `PipelineBuilder`, `NewPipelineBuilder` | interfaces, types, and function | Build and execute notification stages. |
| `notify.DedupStage`, `NewDedupStage`, `RetryStage`, `NewRetryStage` | types and functions | Suppress repeated groups and retry recoverable failures. |
| `webhook.Notifier`, `WebhookConfig`, `Message`, `New` | types and function | Deliver grouped alerts to generic HTTP endpoints. |
| `nflog.Log`, `Options`, `New`, `QReceiver`, `QGroupKey` | types and functions | Store and query delivery receipts. |
| `nflog.Store`, `NewStore` | type and function | Attach receiver-specific values to a receipt. |
| `nflog.ErrNotFound`, `ErrInvalidState` | error values | Identify history lookup and state failures. |
| `v2.API`, `NewAPI`, `SortSilences`, `CheckSilenceMatchesFilterLabels` | type and functions | Serve and normalize v2 resources. |

| `config.Coordinator.Subscribe`, `Reload`, `ApplyConfig` | methods | Register consumers and publish complete configuration generations. |
| `mem.Alerts.Put`, `Get`, `Subscribe`, `SlurpAndSubscribe`, `Close` | methods | Change, observe, stream, and close in-memory alert state. |
| `dispatch.Route.Match`, `Key`, `ID`, `Walk` | methods | Match labels and traverse route identity. |
| `dispatch.Dispatcher.Run`, `Stop`, `Groups`, `WaitForLoading` | methods | Manage grouping lifecycle and expose live groups. |
| `silence.Silences.Set`, `Expire`, `Query`, `QueryOne`, `Version`, `CountState` | methods | Change and observe silence state. |
| `silence.Silencer.Mutes`, `inhibit.Inhibitor.Mutes` | methods | Project suppression decisions for alert labels. |
| `inhibit.Inhibitor.Run`, `Stop`, `WaitForLoading` | methods | Manage inhibition lifecycle. |
| `marker.AlertMarker.SetSilenced`, `SetInhibited`, `Status`, `Delete` | methods | Publish and clear alert suppression state. |
| `notify.Stage.Exec`, `notify.Integration.Notify` | methods | Execute one pipeline stage or integration delivery. |
| `nflog.Log.Log`, `Query`, `Snapshot`, `Merge`, `GC` | methods | Record, query, persist, merge, and expire delivery history. |
| `v2.API.Update` | method | Replace API configuration and alert-status ownership. |
| `receipt.RoutingPlan`, `receipt.NewRoutingPlan` | type and function | Select named alerts and complete lifecycle projections. |
| `receipt.RoutingPlan.SelectAlert`, `receipt.RoutingPlan.IncludeGroups`, `receipt.RoutingPlan.IncludeSuppressions`, `receipt.RoutingPlan.IncludeDeliveries`, `receipt.RoutingPlan.IncludeAPIState` | methods | Build a stable caller-owned lifecycle observation plan. |
| `receipt.RouteFact`, `receipt.GroupFact`, `receipt.SuppressionFact`, `receipt.DeliveryFact`, `receipt.APIStateFact` | records | Normalize routing grouping suppression delivery and service state. |
| `receipt.DeliveryJournal`, `receipt.NewDeliveryJournal` | type and function | Own ordered notification attempts and terminal outcomes. |
| `receipt.DeliveryJournal.Record`, `receipt.DeliveryJournal.Entries` | methods | Append delivery outcomes and return independent ordered snapshots. |
| `receipt.LifecycleReceipt`, `receipt.Capture` | type and function | Capture one coherent alert lifecycle across selected projections. |
| `receipt.LifecycleReceipt.Validate`, `receipt.LifecycleReceipt.Digest`, `receipt.LifecycleReceipt.Equivalent` | methods | Reconcile and compare normalized lifecycle generations. |
| `receipt.ChangeReceipt`, `receipt.Diff` | type and function | Describe semantic additions removals and changes between lifecycle receipts. |

### CLI Entry Points

| Command | Role | Success | Failure |
|---|---|---|---|
| `amtool check-config` | Parse and validate configuration. | Exit 0 for a valid configuration. | Exit nonzero with configuration diagnostics. |
| `amtool alert query` | Query live alerts by matchers. | Exit 0 with matching alerts. | Exit nonzero on invalid matchers or API failure. |
| `amtool silence add`, `amtool silence query`, `amtool silence expire` | Manage silence state. | Exit 0 after the requested API operation succeeds. | Exit nonzero on invalid input, missing state, or API failure. |
| `amtool config routes`, `amtool status` | Observe route and service status. | Exit 0 with the requested projection. | Exit nonzero on invalid input or API failure. |

# Meta

## Appendix A: Environment

The working environment runs Go 1.25 on Linux without public network access. Configuration, silence snapshots, notification history, and command output use temporary directories. Notification delivery targets only caller-owned loopback HTTP handlers.

## Appendix B: Assessment Notes

Conformance is assessed across configuration defaults and reload recovery, matcher traversal, route inheritance, group timing, alert lifecycle, silence state, inhibition equality, markers, webhook retries, notification deduplication, API filters, and `amtool` parity. Exact scheduling latency, temporary paths, and undocumented storage layout have no contractual meaning.

