<!-- SPEC.md -->
# Luigi workflow specification

## Authority and scope

This document defines the public behavior of the `luigi` package for declaring
parameterized task graphs and executing them with local targets and a local
scheduler. It covers task identity, supported parameters, static and dynamic
dependencies, atomic local-file publication, scheduler readiness and resource
capacity, callbacks and events, configuration, installed command routes, and
public build outcomes.

The contract is behavioral. An implementation may use any internal parser,
registry, graph, scheduler, worker, cache, or persistence strategy that
preserves the public laws below.

## Task declaration and identity

`Task.requires()` and `Task.output()` return empty collections by default, and
`Task.run()` performs no work by default. A task may override these methods to
declare dependencies, targets, and work. Supported dependency and output
containers include tasks or targets nested in lists, tuples, and dictionaries.
`Task.input()` replaces each requirement with its output and preserves the
supported container shape.

`get_task_family()` returns the class name when no namespace applies and the
qualified family when a namespace applies. `namespace()` affects subsequently
declared matching task classes; a class-level `task_namespace` takes precedence
over ambient namespace selection.

Task equality and hashing use the task class plus significant parameter values.
Equal significant values on the same class identify one logical task even when
insignificant values differ. Different classes or significant values identify
different tasks. An insignificant value remains available to task code but does
not enter significant serialization or task identity. Workflow correctness must
not depend on which identity-equal object supplies an insignificant value.

`clone(cls=None, **kwargs)` constructs the current or supplied destination
class, copies same-named parameter values, and applies explicit overrides using
ordinary destination binding rules.

## Parameters and configuration

Plain and string parameters expose string values. Integer and Boolean
parameters parse their documented command/configuration forms and serialize
back to public string forms. Invalid integers and unknown Boolean spellings raise `ValueError`. Missing
required values, unknown keywords, duplicate bindings, and excess positional
values raise the applicable binding exception exposed by `luigi.parameter`.

List parameters parse JSON arrays into their documented normalized sequence.
Values declared `significant=False` remain Python attributes. They are absent
when `to_str_params(only_significant=True)` requests the significant view; the
default full string-parameter view includes them. `from_str_params()` applies
the documented parsing rules.

Declared defaults are used when no higher-precedence source supplies a value.
Applicable task values progress from defaults to matching configuration, then
command values, then explicit Python constructor values. A class-qualified
command option changes the matching task family, including a dependency of the
selected root. Python underscores in a parameter name use hyphens in command
options.

The cfg parser reads its documented sources, including `LUIGI_CONFIG_PATH`, in
documented priority order. A `Config` subclass obtains typed values from its
own section and remains configuration rather than a schedulable task. Fresh
independent invocations observe current files and environment; recovery of a
previously loaded configuration singleton in the same process is not required.

## Completion, targets, and publication

`Task.complete()` is true when all flattened output targets exist. A task with
no output and no completion override is incomplete. A requirement or output
whose public shape cannot be interpreted causes the corresponding public
scheduling or completion failure rather than silently becoming ready.

`LocalTarget(path)` represents a local file. `exists()` reflects final-file
existence. Writing and reading use the public `open()` interface, with parent
directories created as documented. A missing read exposes the underlying file
failure. `remove`, `copy`, and `move` update controlled files and their public
existence consistently.

`open("w")` publishes through a temporary resource. Successful close commits
the final bytes atomically; an exceptional context exit does not publish a
partial final target. `temporary_path()` follows the same commit-on-success and
no-final-publication-on-failure rule. Only a committed final target establishes
output-based completion or unlocks a dependent task.

Preexisting output makes its task complete and skips that task's `run()`.
Removing a controlled output invalidates a later completion check and permits a
fresh build to reconstruct the missing part of a graph. Reuse is based on
current public target state, not on an inaccessible historical record.

## Static and dynamic graph laws

The local scheduler discovers work through `requires()`. A task is runnable
only after every dependency is complete. Readiness takes precedence over
priority; priority orders only tasks that are simultaneously ready and
otherwise eligible to run.

Identity-equal requirements denote one logical scheduled task. Different
significant identities remain separate nodes and keep their own targets in
nested `input()` structures. `ExternalTask.run` is `None`; a missing external
target blocks its dependent branch without executing the external task.
`WrapperTask` is complete when its flattened requirements are complete.

A task whose `run()` returns without establishing its declared completion state
does not unlock consumers. Exceptions from `requires()` or `complete()` are
scheduling failures. An exception from `run()` is a task failure. In each case,
dependent work stays blocked while an independent eligible branch may still
commit its own output.

`DynamicRequirements` exposes its flat requirements and output paths and uses
its default or supplied public completion function. A task may yield a task or
a flat `DynamicRequirements` collection from `run()`. The parent suspends while
yielded work is scheduled and restarts from the beginning after that work
completes, so code before the yield must be idempotent. The parent cannot
publish final output before its yielded dependencies and its restarted final
phase complete.

Already-complete yielded work is reused. Failed or incomplete yielded work
prevents successful parent completion. An independent later graph may correct
the controlled cause and complete the dynamic chain without changing an
already committed sibling target.

## Scheduler resources and worker ownership

`Task.resources` is a mapping from resource name to the amount claimed by the
task. `process_resources()` supplies the effective mapping used for scheduling
and may derive it from public parameter state. The `[resources]` configuration
section supplies global capacities; an unspecified named resource has the
documented default capacity of one.

With multiple workers sharing one scheduler, the scheduler does not start a
task when doing so would make the sum of running claims exceed a named
capacity. Different resource names constrain their own capacities independently.
Dependency readiness still applies before resource eligibility, and priority
chooses only among tasks that are both ready and resource-eligible. A caller may
use multiple single-process `Worker` instances when platform multiprocessing is
not supported.

A task holds its effective claim while its worker body is running. Completion
or failure releases that claim so another eligible task can make progress.
`decrease_running_resources(mapping)` reduces the current task's running claim
through the public task interface; newly available capacity may then admit
another ready task while the first task continues.

Resource arbitration does not change identity, target ownership, dependency
association, callback state, or result classification. A resource-blocked task
has not run and cannot publish output. A failing resource holder does not make
its consumer ready, but release of its claim may allow an independent waiting
task to complete.

`build(tasks, local_scheduler=True, workers=N, ...)` requests the supplied
worker capacity; platform limitations on multiprocessing still apply. For
deterministic local resource arbitration, callers may instead use public
`Scheduler` and single-process `Worker` objects that share that scheduler. When
a `worker_scheduler_factory` object implementing the documented creation
methods is supplied, the scheduler and worker it creates execute the task graph.
Private default-factory classes, queues, resource tables, worker messages, and
object identities are not part of this contract.

## Callbacks and events

After `run()` returns successfully, Luigi calls that task instance's
`on_success()`. When `run()` raises, Luigi calls `on_failure(exception)` with
the raised exception before recording task failure. A preexisting complete
task whose worker body is skipped receives no new run callback.

`Task.event_handler(event)` registers a handler, `trigger_event(event, *args)`
delivers controlled arguments, and `remove_event_handler(event, handler)`
removes that registration. Ordinary exceptions raised by an event handler are protected from replacing
the task's own execution outcome; other eligible handlers may still receive
the event. `KeyboardInterrupt` is not covered by that guarantee.

During ordinary local worker execution, public lifecycle events describe the
same task transition as callbacks, targets, and results. `Event.START` precedes
the worker body for a task that actually runs. Successful execution emits
`Event.SUCCESS` and a processing-time event; failed execution emits
`Event.FAILURE` with the task and raised exception. A reused complete task does
not emit a new worker lifecycle. Exact elapsed values, log text, handler order,
and timing are not specified.

## Build, run, installed routes, and results

By default, `build()` returns the same Boolean represented by the detailed
result's `scheduling_succeeded` field. With `detailed_summary=True`, it returns
`LuigiRunResult`, whose public fields include `status`, `scheduling_succeeded`,
and string `summary_text`. Public `LuigiStatusCode` values distinguish success,
task failure, missing external data, work not run, and scheduling failure; when
several categories coexist, the aggregate enum may combine or prioritize them
while branch target and event facts retain each branch's state.

The Boolean or process outcome, detailed status, scheduling Boolean, callbacks,
events, committed targets, and blocked consumers must describe the same
workflow state. `summary_text` is required only to be a string; its exact
vocabulary, layout, task ordering, and counts are not specified.

`run()` accepts command-style arguments and may select a supplied
`main_task_cls`. A supplied argument collection must have the documented list
or tuple shape. The installed `luigi` command and `python -m luigi` accept the
same local invocation grammar, including module import, root family, local
scheduler, workers, and task options. Equivalent Python and command routes
select the same typed task identities, graph, semantic target bytes, and
success or failure category.

Configured `[retcode]` values apply to their documented categories. When more
than one configured nonzero category applies, the numerically greatest
configured code wins. Exact stdout, stderr, help prose, logs, and traceback
formatting are not part of the behavioral result.

## Failure isolation and correction

A scheduling failure does not run the invalid task as though scheduling had
succeeded. A worker exception invokes the failure callback and event, does not
commit an atomic final target, and blocks consumers. A missing external target
blocks only the branch that depends on it. A failure in one root does not erase,
rewrite, or relabel an independently committed sibling target.

Correction may use a fresh task graph, scheduler, worker, configuration owner,
process, or destination. The corrected build observes current public target
state, reuses surviving siblings, and runs only work that is incomplete and
eligible. Reuse of a failed task object, scheduler object, worker object,
factory object, or configuration singleton is not required.

## Cross-view laws

1. A selected parameter value agrees across task attributes, significant
   identity, dependency construction, effective resource claims, and target
   content.
2. Task family and namespace agree across Python construction and installed
   command lookup.
3. Static and dynamic dependency ownership agrees with input target shape and
   scheduler readiness.
4. Current committed target state agrees with completion, downstream access,
   reuse, and selective rebuilding.
5. Resource eligibility limits worker entry without changing graph identity or
   falsely publishing blocked work.
6. Completion or failure releases a running resource claim; failure still
   blocks only its dependent branch.
7. Worker callbacks and lifecycle events agree with whether the task actually
   ran, committed, failed, or was reused.
8. Boolean, detailed, and installed-command outcomes agree with scheduling,
   target, callback, and event state.

## Public import surface

The package exposes its documented task, target, parameter, execution, event,
configuration, scheduler-factory, status, and exception surfaces, including
`Task`, `ExternalTask`, `WrapperTask`, `Config`, `DynamicRequirements`,
`LocalTarget`, `Parameter`, `StrParameter`, `IntParameter`, `BoolParameter`,
`ListParameter`, `Event`, `LuigiStatusCode`, `build`, `run`, `namespace`, and
the public parameter-binding exception families from `luigi.parameter`.
`LuigiRunResult` is available from its documented execution-summary module.

## Out of scope

- private scheduler/worker queues, graph records, resource tables, registries,
  caches, RPC payloads, locks, persistence schemas, and task-history stores;
- exact logs, warnings, messages, tracebacks, representations, summaries,
  console prose, elapsed values, or incidental callback/handler ordering;
- automatic retry counts, retry delay, disable windows, retry exhaustion,
  batching, assistant workers, remote scheduling, and same-object recovery;
- nested dynamic-yield grammar beyond one task or a flat
  `DynamicRequirements` collection; and
- Hadoop, Spark, HDFS, cloud, SQL, Redis, metrics, email, SSH, FTP,
  Kubernetes, browser, daemon, and other contrib integrations.
