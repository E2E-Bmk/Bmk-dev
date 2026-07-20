
# Jupyter Client Specification

## Product Overview

The package must provide Python APIs for starting, managing, and communicating
with Jupyter kernels through connection files, ZeroMQ channels, kernel
specifications, and provisioners. Operations that require an unavailable
kernel, inaccessible filesystem location, unusable network endpoint, or
unregistered provisioner must raise the public exception described for that
operation or the underlying operating-system or transport exception.

## Scope

This specification must cover connection-file exchange, session message framing
and authentication, kernel-specification discovery and installation, single
kernel manager and provisioner lifecycle behavior, and blocking or asynchronous
client channels. Calls outside these areas must retain their documented import
surface without adding behavior beyond the non-goals below.

## Installable Surface

The package must be imported as `jupyter_client`. Its primary kernel-facing
classes must be available at the package root as `KernelClient`,
`BlockingKernelClient`, `AsyncKernelClient`, `KernelManager`,
`AsyncKernelManager`, `KernelProvisionerBase`, and `LocalProvisioner`.
Connection helpers must be available from both `jupyter_client` and
`jupyter_client.connect`; kernel-specification APIs must be available from
`jupyter_client.kernelspec`; and provisioner APIs must be available from
`jupyter_client.provisioning`. Missing any named import must raise
`ImportError`.

The connection names `KernelConnectionInfo`, `find_connection_file`, and
`write_connection_file` must identify the same public features at both listed
connection import paths. The kernel-specification names `KernelSpec`,
`KernelSpecManager`, `NoSuchKernel`, `find_kernel_specs`, `get_kernel_spec`,
and `install_kernel_spec` must be available from `jupyter_client.kernelspec`.
The provisioner names `KernelProvisionerFactory`, `KernelProvisionerBase`, and
`LocalProvisioner` must be available from `jupyter_client.provisioning`.
`Session` must be available from `jupyter_client.session`, and its failure to
import must raise `ImportError`.

The console programs `jupyter-kernelspec`, `jupyter-run`, and `jupyter-kernel`
must be installed. `python -m jupyter_client` is not supported and must exit
nonzero because the package provides no module entry point.

## Product State Model

A kernel connection must be visible through three public projections: a JSON
connection file, a `KernelConnectionInfo` mapping on managers and clients, and
the addresses and session used by five ZeroMQ channels. A kernelspec must
supply the launch command and metadata, while the selected provisioner must own
the running process and return its connection information.

1. Writing a connection file must return a mapping whose five ports, transport,
   IP address, key, and signature scheme are readable from that file.
2. Loading a written mapping into a connection-aware object must return those
   transport and authentication values through `get_connection_info()`.
3. A client created by a manager must return connection information matching the
   manager's active transport, IP address, and channel ports.
4. A cloned session returned through connection information must preserve the
   original session identifier and key while keeping independent digest history.
5. A kernelspec selected by name must return the same resource directory from
   both `find_kernel_specs()` and `get_kernel_spec(name)`.
6. A provisioner connection mapping returned during launch must become the
   manager connection mapping and the persisted connection-file content.

## Public API

### Connection information

`KernelConnectionInfo` must represent the transport, IP address, five channel
ports (`shell`, `iopub`, `stdin`, `control`, and `hb`), authentication key, and
signature scheme; it must accept optional kernel name, session, and CurveZMQ
key fields. A missing optional field must leave the corresponding configurable
value unchanged.

`write_connection_file(fname=None, shell_port=0, iopub_port=0,
stdin_port=0, hb_port=0, control_port=0, ip="", key=b"",
transport="tcp", signature_scheme="hmac-sha256", kernel_name="",
curve_publickey=None, curve_secretkey=None, **kwargs)` must return a path and
the written connection mapping. It must create a temporary JSON file when
`fname` is absent, must select a local IP address when `ip` is empty, and must
select positive unused channel ports when a TCP port is non-positive. It must
store byte keys as JSON strings and must raise an operating-system or socket
exception when the file or requested address cannot be created.

`find_connection_file(filename="kernel-*.json", path=None, profile=None)`
must return an absolute matching path. It must search the current directory and
the Jupyter runtime directory when `path` is absent, must treat a missing exact
name as a substring glob, and must return the most recently accessed match
when several matches exist. It must raise `OSError` when no match exists; a
supplied `profile` must be ignored with a warning rather than changing lookup.

`ConnectionFileMixin` must expose `get_connection_info`,
`load_connection_file`, `load_connection_info`, `write_connection_file`,
`cleanup_connection_file`, `cleanup_ipc_files`, `cleanup_random_ports`, and
the five `connect_*` channel methods. `get_connection_info(session=False)`
must return serializable key and signature information, while
`get_connection_info(session=True)` must return a cloned `Session`; an
independent clone must prevent one caller's digest history from changing the
other caller's digest history. `load_connection_file` must raise the underlying
file or JSON exception when its path is unreadable or malformed.

### Kernel specifications

`KernelSpec.from_resource_dir(resource_dir)` must read `kernel.json` from that
directory, and must raise the underlying file or JSON exception when the file
is absent or malformed. `to_dict()` must return `argv`, `env`, `display_name`,
`language`, `interrupt_mode`, `metadata`, and `kernel_protocol_version`; and
`to_json()` must return JSON for that mapping.

`KernelSpecManager.find_kernel_specs()` must return normalized lowercase names
mapped to their resource directories, must omit directories without
`kernel.json`, and must apply `allowed_kernelspecs` when that set is nonempty.
When two configured directories provide the same normalized name, discovery
must return the spec from the first configured directory. `get_kernel_spec`
must return the selected `KernelSpec` and must raise `NoSuchKernel` when the
name is absent or its referenced provisioner is unavailable. `get_all_specs`
must return each discoverable name with `resource_dir` and a serializable
`spec` mapping; a spec that cannot be loaded must be omitted.

`install_kernel_spec(source_dir, kernel_name=None, user=False, replace=None,
prefix=None)` must copy a kernel-spec directory, must derive a missing name
from the source directory basename, and must normalize the destination name to
lowercase. It must raise `ValueError` when a name contains characters other
than ASCII letters, digits, `.`, `_`, or `-`, and must raise `ValueError` when
both `user` and `prefix` are requested. It must replace an existing destination
and return its path; insufficient destination permissions must raise `OSError`.
`remove_kernel_spec(name)` must remove the discovered directory and return its
path, and must raise `KeyError` when the name is not installed.

The module helpers `find_kernel_specs()`, `get_kernel_spec(name)`, and
`install_kernel_spec(...)` must expose the corresponding manager behavior and
must raise the same failure class for the same input.

### Sessions and clients

`Session.msg(msg_type, content=None, parent=None, header=None, metadata=None)`
must return a nested message with `header`, `parent_header`, `metadata`,
`content`, `msg_id`, and `msg_type`. A default parent or content must become an
empty mapping, and supplied metadata must extend session metadata. `msg_header`
and `Session.msg_header` must return a header containing a fresh message ID,
message type, username, session identifier, protocol version, and timestamp.

`Session.serialize(msg, ident=None)` must return routing identities when
supplied, followed by the delimiter, signature, packed header, packed parent
header, packed metadata, packed content, and any buffers. `Session.deserialize`
must reconstruct that nested form and expose trailing buffers as memoryviews.
It must raise `ValueError` for an unsigned, duplicate, or invalid signature
when signing is enabled, and must raise `TypeError` for fewer than the required
message frames. An empty authentication key must produce an empty signature.

`KernelClient` must expose shell, IOPub, stdin, heartbeat, and control channels
after `start_channels()` and must release them after `stop_channels()`. Request
methods including `execute`, `complete`, `inspect`, `history`, `kernel_info`,
`comm_info`, `is_complete`, and `shutdown` must return their request message ID
when a reply is not requested. `BlockingKernelClient` must provide blocking
message retrieval and reply waiting; `AsyncKernelClient` must provide the same
operations as awaitables. A receive operation must raise `queue.Empty` when no
message arrives before its timeout, and a reply wait must raise `TimeoutError`
when the matching reply does not arrive before its timeout.

### Kernel managers and provisioners

`KernelManager.client(**kwargs)` must return a blocking client configured from
the manager's current connection information; `AsyncKernelManager.client` must
return an asynchronous client configured from the same information. A manager
must report `has_kernel` only while its provisioner has a process, and
`is_alive()` must return false after a managed provisioner reports an exit
status. `interrupt_kernel()` and `signal_kernel()` must raise `RuntimeError`
when no managed kernel is running.

`KernelManager.start_kernel`, `shutdown_kernel`, and `restart_kernel` must
perform the matching lifecycle operation; their `AsyncKernelManager`
counterparts must be awaitable. `restart_kernel(newports=True)` must discard
randomly chosen ports before startup; a restart without that flag must retain
the existing connection configuration. `run_kernel(**kwargs)` must yield a
connected client and must stop channels and force shutdown when the context
exits, including when the context body raises.

`start_new_kernel(startup_timeout=60, kernel_name="python", **kwargs)` must
return a manager and connected blocking client after readiness succeeds.
`start_new_async_kernel` must return the analogous asynchronous pair. Either
helper must stop client channels and shut down its manager before re-raising a
readiness failure.

`KernelProvisionerBase` must define awaitable launch, polling, wait, signal,
termination, cleanup, and persistence operations for provisioner subclasses.
`poll()` must return `None` while a process is running and its integer exit
status after it exits. `get_provisioner_info()` must return the kernel ID and
connection information, and `load_provisioner_info()` must restore those
values; a mapping missing either required value must raise `KeyError`.
`LocalProvisioner` must provide the built-in local implementation.

`KernelProvisionerFactory` must read a kernelspec's
`metadata.kernel_provisioner` mapping to choose a provisioner entry point. It
must use `local-provisioner` when that mapping is absent, must return false
from `is_provisioner_available` when the named entry point cannot be loaded,
and must raise `ModuleNotFoundError` from `create_provisioner_instance` in that
case.

### Transport encryption

`KernelManager.transport_encryption` must accept `disabled`, `auto`, and
`required`. It must raise `traitlets.TraitError` when `auto` or `required` is
selected without CurveZMQ support. `disabled` must write no CurveZMQ keys;
`auto` must write CurveZMQ keys only when the selected kernelspec declares
`metadata.supported_encryption` containing `curve`; and `required` must raise
`RuntimeError` before startup when that declaration is absent. A connection
file with transport encryption must contain `curve_publickey` and
`curve_secretkey` as Z85 text.

## Representative Workflow

```python
from jupyter_client import KernelManager

manager = KernelManager(kernel_name="python3")
manager.start_kernel()
client = manager.client()
client.start_channels()
client.wait_for_ready(timeout=60)
request_id = client.execute("1 + 1")
reply = client.get_shell_msg(timeout=60)
client.stop_channels()
manager.shutdown_kernel()
```

The workflow must return a request ID before the shell reply is read. It must
raise `RuntimeError` when readiness fails, `queue.Empty` when the shell reply
does not arrive before its timeout, or the underlying launch exception when the
kernel cannot start.

## Non-Goals

This specification does not require SSH tunnelling, Windows-only interrupt
handling, multi-kernel manager coordination, terminal-console presentation,
kernel-side language execution, exact diagnostic text, process timing, or
private attributes. Those areas must not add requirements beyond import
compatibility and ordinary Python failure behavior.

## Invocation Protocol

| Invocation | Successful result | Failure result |
|---|---|---|
| `jupyter-kernelspec` | must exit `0` after a valid subcommand completes | must exit nonzero for invalid arguments or an unsuccessful file operation |
| `jupyter-run` | must exit `0` after a valid run completes | must exit nonzero when its requested run fails |
| `jupyter-kernel` | must exit `0` after normal kernel termination | must exit nonzero when startup fails |
| `python -m jupyter_client` | must not provide a module entry point | must exit nonzero |

## Environment

The implementation is permitted to use any third-party packages available on
PyPI. Declare runtime dependencies in a standard `requirements.txt` or
`pyproject.toml` at the project root. Declared dependencies must be available
at runtime.

## Compatibility

Applications must be able to combine public imports, connection files, session
frames, kernelspec directories, provisioner metadata, kernel lifecycle calls,
and command-line entry points without translating those public representations.
An application that supplies a malformed document, missing file, unavailable
kernel, unregistered provisioner, inaccessible endpoint, or expired receive
timeout must receive the documented public or underlying failure rather than a
partially established connection.


## Implementation Guidance

Validation covers public imports, connection-file handling, session framing and authentication, kernelspec discovery and installation, client channels, kernel and provisioner lifecycles, transport encryption, command-line behavior, and cross-view invariants. Checks use local files, endpoints, and available kernels, and assess independently observable synchronous and asynchronous behavior. Private attributes, process timing, kernel-side language execution, and exact diagnostic text are not considered.