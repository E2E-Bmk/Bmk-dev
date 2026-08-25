# Jupyter Client Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

The package must provide Python APIs for starting, managing, and communicating
with Jupyter kernels through connection files, ZeroMQ channels, kernel
specifications, and provisioners. Operations that require an unavailable
kernel, inaccessible filesystem location, unusable network endpoint, or
unregistered provisioner must raise the public exception described for that
operation or the underlying operating-system or transport exception.

## Non-Goals

This specification does not require SSH tunnelling, Windows-only interrupt
handling, multi-kernel manager coordination, terminal-console presentation,
kernel-side language execution, exact diagnostic text, process timing, or
private attributes. Those areas must not add requirements beyond import
compatibility and ordinary Python failure behavior.

## Representative Workflows

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

## Connection Management

This section covers how connection files are created, discovered, loaded, and how connection parameters flow between objects.

**Writing connection files.** When `write_connection_file` is called with an explicit `fname`, it must write the connection JSON to that path. When `fname` is absent, it must create a temporary JSON file. When `ip` is empty, a local IP address must be selected automatically. When any TCP channel port is non-positive, a positive unused port must be selected. Byte keys must be stored as JSON strings in the file. The function must return a tuple of the written path and the connection mapping. The mapping on disk must match the returned mapping for all fields including `ip`, `transport`, `shell_port`, `iopub_port`, `stdin_port`, `control_port`, `hb_port`, `key`, and `signature_scheme`. When the file or requested address cannot be created, the underlying operating-system or socket exception must be raised.

**Finding connection files.** `find_connection_file` must return an absolute matching path. When `path` is absent, it must search the current directory and the Jupyter runtime directory. Exact filenames, substring matches, and glob patterns must all be accepted as the `filename` argument. When several matches exist, the most recently accessed match must be returned. When no match exists, `OSError` must be raised. A supplied `profile` must be ignored with a warning rather than changing lookup.

**Connection file mixin.** `ConnectionFileMixin` must expose `get_connection_info`, `load_connection_file`, `load_connection_info`, `write_connection_file`, `cleanup_connection_file`, `cleanup_ipc_files`, `cleanup_random_ports`, and the five `connect_*` channel methods.

**Loading and inspecting connections.** `load_connection_file` must read a JSON connection file and populate the object's connection properties. It must raise the underlying file or JSON exception when its path is unreadable or malformed. `load_connection_info` must accept a connection mapping and populate the same properties. `get_connection_info` without `session=True` must return a serializable mapping of transport, IP address, channel ports, key, and signature scheme. With `session=True`, it must return a cloned `Session` object; independent clones must share the session identifier and key while keeping independent digest history so that one clone's used message digests do not affect the other.

**Connection info type.** `KernelConnectionInfo` must represent the transport, IP address, five channel ports, authentication key, and signature scheme. It must accept optional kernel name, session, and CurveZMQ key fields. The same names must be importable from both `jupyter_client` and `jupyter_client.connect`.

**Connection file cleanup.** `KernelManager.write_connection_file()` must write a connection JSON file at the manager's `connection_file` path. `cleanup_connection_file()` must remove that file from disk. The written file must contain the manager's active `shell_port`, `ip`, and other connection properties.

## Kernel Specification Discovery

This section covers how kernel specifications are found, installed, and removed.

**Reading a kernel spec.** `KernelSpec.from_resource_dir(resource_dir)` must read `kernel.json` from that directory and raise the underlying file or JSON exception when the file is absent or malformed. `to_dict()` must return a mapping containing at minimum `argv`, `env`, `display_name`, `language`, `interrupt_mode`, `metadata`, and `kernel_protocol_version`. `to_json()` must return the JSON serialization of that mapping. When `env` and `metadata` are present in the kernel JSON, those values must appear in the exported dictionary.

**Discovering kernel specs.** `KernelSpecManager.find_kernel_specs()` must return normalized lowercase names mapped to their resource directories. It must omit directories without `kernel.json`. When `allowed_kernelspecs` is a nonempty set, only matching names must be returned; when the set is empty, all discovered specs must be included. When two configured directories provide the same normalized name, discovery must return the spec from the first configured directory.

**Looking up a kernel spec.** `get_kernel_spec` must return the selected `KernelSpec` with `resource_dir` and `display_name` matching the discovered values, and must raise `NoSuchKernel` when the name is absent or its referenced provisioner is unavailable. `get_all_specs` must return each discoverable name with `resource_dir` and a serializable `spec` mapping; a spec that cannot be loaded (e.g., malformed JSON) must be omitted from the result.

**Installing kernel specs.** `install_kernel_spec` must copy a kernel-spec directory. When `kernel_name` is absent, the name must be derived from the source directory basename and normalized to lowercase. It must raise `ValueError` when a name contains characters other than ASCII letters, digits, `.`, `_`, or `-`, and must raise `ValueError` when both `user` and `prefix` are requested. It must replace an existing destination and return the installed path. The installed path must follow the standard layout under `prefix/share/jupyter/kernels/lowered_name`. Insufficient destination permissions must raise `OSError`.

**Removing kernel specs.** `remove_kernel_spec` must remove the discovered directory and return its path, and must raise `KeyError` when the name is not installed.

**Module-level helpers.** The module helpers `find_kernel_specs()`, `get_kernel_spec(name)`, and `install_kernel_spec(...)` must expose the corresponding manager behavior and must raise the same failure class for the same input.

## Session Framing and Authentication

This section covers how messages are constructed, serialized, deserialized, and authenticated.

**Message construction.** `Session.msg` must return a nested message with `header`, `parent_header`, `metadata`, `content`, `msg_id`, and `msg_type` keys. A default parent or content must become an empty mapping, and supplied metadata must extend session metadata. When a parent message is supplied, `parent_header` must contain the parent's header including its `msg_id` and `msg_type`.

**Message headers.** `Session.msg_header` must return a header containing a fresh message ID, message type, username, session identifier, protocol version, and timestamp. Successive calls with the same message type must produce distinct `msg_id` values but the same `session` identifier.

**Serialization.** `Session.serialize` must return frames consisting of routing identities when supplied, followed by the delimiter, signature, packed header, packed parent header, packed metadata, packed content, and any buffers. When the authentication key is empty, the signature frame must be empty bytes.

**Deserialization.** `Session.deserialize` must reconstruct the nested message form. `feed_identities` must split routing frames from protocol frames and return the identities and remaining wire frames. Deserialized messages must expose trailing extra frames as `buffers` containing `memoryview` objects. Deserialization must raise `ValueError` for an unsigned, duplicate, or invalid signature when signing is enabled, and must raise `TypeError` for fewer than the required message frames.

**Client channels.** `KernelClient` must expose shell, IOPub, stdin, heartbeat, and control channels after `start_channels()` and must release them after `stop_channels()`. Individual channels can be selectively started by passing boolean `shell`, `iopub`, `stdin`, `hb`, and `control` arguments to `start_channels`.

**Request methods.** Request methods including `execute`, `complete`, `inspect`, `history`, `kernel_info`, `comm_info`, `is_complete`, and `shutdown` must return their request message ID when a reply is not requested. `BlockingKernelClient` must provide blocking message retrieval through `get_shell_msg` and reply waiting. `AsyncKernelClient` must provide the same operations as awaitables. A receive operation must raise `queue.Empty` when no message arrives before its timeout, and a reply wait must raise `TimeoutError` when the matching reply does not arrive before its timeout.

**Manager-created clients.** `KernelManager.client()` must return a `BlockingKernelClient` configured from the manager's current connection information. When a connection mapping is loaded into a manager, the client created from that manager must report the same transport, IP, and channel port values.

## Kernel Lifecycle and Provisioning

This section covers how kernels are started, stopped, and how provisioners manage the underlying process.

**Manager lifecycle.** `KernelManager.start_kernel`, `shutdown_kernel`, and `restart_kernel` must perform the matching lifecycle operation. A manager must report `has_kernel` only while its provisioner has a process, and `is_alive()` must return false after a managed provisioner reports an exit status. `interrupt_kernel()` and `signal_kernel()` must raise `RuntimeError` when no managed kernel is running.

**Restart ports.** When `restart_kernel` is called with `newports=True`, it must discard randomly chosen ports before startup. A restart without that flag must retain the existing connection configuration.

**Run helper.** `run_kernel` must yield a connected client and must stop channels and force shutdown when the context exits, including when the context body raises.

**Kernel start helpers.** `start_new_kernel` must return a manager and connected blocking client after readiness succeeds. `start_new_async_kernel` must return the analogous asynchronous pair. Either helper must stop client channels and shut down its manager before re-raising a readiness failure. Starting with an unknown kernel name must raise `NoSuchKernel` without leaving a running kernel.

**Provisioner contract.** `KernelProvisionerBase` must define awaitable launch, polling, wait, signal, termination, cleanup, and persistence operations. `poll()` must return `None` while a process is running and its integer exit status after it exits. `get_provisioner_info()` must return the kernel ID and connection information, and `load_provisioner_info()` must restore those values; a mapping missing either required value must raise `KeyError`. `LocalProvisioner` must provide the built-in local implementation. `LocalProvisioner.kernel_id` and `LocalProvisioner.connection_info` must reflect loaded provisioner information.

**Provisioner factory.** `KernelProvisionerFactory` must read a kernelspec's `metadata.kernel_provisioner` mapping to choose a provisioner entry point. It must use `local-provisioner` when that mapping is absent. `is_provisioner_available` must return `True` for available specs and `False` when the named entry point cannot be loaded. `create_provisioner_instance` must raise `ModuleNotFoundError` when the named provisioner entry point cannot be loaded.

**Transport encryption.** `KernelManager.transport_encryption` must accept `disabled`, `auto`, and `required`; unknown values must raise `traitlets.TraitError`. When `disabled`, connection files must contain no `curve_publickey` or `curve_secretkey` entries. `auto` or `required` without CurveZMQ support must raise `traitlets.TraitError`. `required` must raise `RuntimeError` before startup when the kernelspec does not declare `metadata.supported_encryption` containing `curve`.

## State Model

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

## Error Semantics

Failures described in this specification must surface through these public
exception classes:

- `ImportError` must be raised when any import named in the Import Surface is missing.
- `OSError` must be raised when `find_connection_file` finds no match, when `install_kernel_spec` lacks destination permissions, and when `write_connection_file` cannot create its file or requested address.
- `load_connection_file` and `KernelSpec.from_resource_dir` must raise the underlying file or JSON exception for an unreadable or malformed source.
- `ValueError` must be raised by `install_kernel_spec` for a kernel name with unsupported characters or when both `user` and `prefix` are requested, and by `Session.deserialize` for an unsigned, duplicate, or invalid signature when signing is enabled.
- `TypeError` must be raised by `Session.deserialize` for fewer than the required message frames.
- `NoSuchKernel` must be raised by `get_kernel_spec` when the requested name is absent or its referenced provisioner is unavailable.
- `KeyError` must be raised by `remove_kernel_spec` for a name that is not installed and by `load_provisioner_info` for a mapping missing a required value.
- `queue.Empty` must be raised by a receive operation whose timeout expires, and `TimeoutError` must be raised by a reply wait whose matching reply does not arrive before its timeout.
- `RuntimeError` must be raised by `interrupt_kernel()` and `signal_kernel()` when no managed kernel is running, by readiness waiting when readiness fails, and by `required` transport encryption when the kernelspec does not declare supported encryption.
- `traitlets.TraitError` must be raised when `auto` or `required` transport encryption is selected without CurveZMQ support, or when an unknown transport encryption mode string is supplied.
- `ModuleNotFoundError` must be raised by `create_provisioner_instance` when the named provisioner entry point cannot be loaded.

## Cross-View Invariants

1. A connection file written by `write_connection_file` must be loadable by `load_connection_file` and must produce the same transport, IP address, channel ports, authentication key, and signature scheme.
2. A client created by a manager must return connection information matching the manager's active transport, IP address, and channel ports.
3. A cloned session returned through `get_connection_info(session=True)` must preserve the original session identifier and key while keeping independent digest history, such that a message signed by one clone can be verified by the other clone exactly once.
4. A kernelspec selected by name must return the same resource directory from both `find_kernel_specs()` and `get_kernel_spec(name)`.
5. A provisioner connection mapping returned during launch must become the manager connection mapping and the persisted connection-file content.
6. A malformed document, missing file, unavailable kernel, unregistered provisioner, inaccessible endpoint, or expired receive timeout must raise the documented public or underlying exception rather than establish a partially configured connection.
7. A connection file written by a `KernelManager` must configure a `BlockingKernelClient` that reports the same `shell_port`, `hb_port`, `ip`, and `transport` values as the manager.

## Public Interface

### Import Surface

The package must be imported as `jupyter_client`. Missing any named import must raise `ImportError`.

```python
import jupyter_client
from jupyter_client import (
    KernelClient, BlockingKernelClient, AsyncKernelClient,
    KernelManager, AsyncKernelManager, KernelProvisionerBase, LocalProvisioner,
    KernelConnectionInfo, find_connection_file, write_connection_file,
)
from jupyter_client.connect import (
    KernelConnectionInfo, find_connection_file, write_connection_file,
)
from jupyter_client.kernelspec import (
    KernelSpec, KernelSpecManager, NoSuchKernel,
    find_kernel_specs, get_kernel_spec, install_kernel_spec,
)
from jupyter_client.provisioning import (
    KernelProvisionerFactory, KernelProvisionerBase, LocalProvisioner,
)
from jupyter_client.session import Session
```

The connection names `KernelConnectionInfo`, `find_connection_file`, and `write_connection_file` must identify the same public features at both listed connection import paths.

The console programs `jupyter-kernelspec`, `jupyter-run`, and `jupyter-kernel` must be installed. The corresponding module invocations `jupyter_client.kernelspecapp`, `jupyter_client.runapp`, and `jupyter_client.kernelapp` must be runnable with `--help`. `python -m jupyter_client` is not supported and must exit nonzero because the package provides no module entry point.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| KernelConnectionInfo | type | Connection transport, ports, key, and scheme |
| write_connection_file | function | Write a connection JSON file with port allocation |
| find_connection_file | function | Locate an existing connection file by name pattern |
| ConnectionFileMixin | mixin | Connection-file load, write, and cleanup operations |
| KernelSpec | class | Parsed kernel specification from a resource directory |
| KernelSpecManager | class | Discover, install, and remove kernel specifications |
| NoSuchKernel | exception | Raised when a requested kernel name is absent |
| find_kernel_specs | function | Module-level kernel specification discovery |
| get_kernel_spec | function | Module-level kernel specification lookup |
| install_kernel_spec | function | Module-level kernel specification installation |
| Session | class | Message framing, serialization, and authentication |
| KernelClient | class | Channel-based client for kernel communication |
| BlockingKernelClient | class | Blocking variant of KernelClient |
| AsyncKernelClient | class | Async variant of KernelClient |
| KernelManager | class | Start, stop, and restart a managed kernel |
| AsyncKernelManager | class | Async variant of KernelManager |
| start_new_kernel | function | Return a manager and connected blocking client |
| start_new_async_kernel | function | Return an async manager and connected async client |
| KernelProvisionerBase | class | Base for kernel process provisioner subclasses |
| LocalProvisioner | class | Built-in local kernel provisioner |
| KernelProvisionerFactory | class | Select and instantiate a provisioner from a kernelspec |

### CLI Entry Points

| Invocation | Successful result | Failure result |
|---|---|---|
| `jupyter-kernelspec` | must exit `0` after a valid subcommand completes | must exit nonzero for invalid arguments or an unsuccessful file operation |
| `jupyter-run` | must exit `0` after a valid run completes | must exit nonzero when its requested run fails |
| `jupyter-kernel` | must exit `0` after normal kernel termination | must exit nonzero when startup fails |
| `python -m jupyter_client` | must not provide a module entry point | must exit nonzero |

## Appendix A: Environment

The implementation is permitted to use any third-party packages available on
PyPI. Declare runtime dependencies in a standard `requirements.txt` or
`pyproject.toml` at the project root. Declared dependencies must be available
at runtime.

## Appendix B: Assessment Notes

Validation covers public imports, connection-file handling, session framing and authentication, kernelspec discovery and installation, client channels, kernel and provisioner lifecycles, transport encryption, command-line behavior, and cross-view invariants. Checks use local files, endpoints, and available kernels, and assess independently observable synchronous and asynchronous behavior. Private attributes, process timing, kernel-side language execution, and exact diagnostic text are not considered.
