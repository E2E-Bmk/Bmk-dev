# Commons VFS Core Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`commons-vfs2` is a Java virtual-file-system library that presents local files, memory-resident files, and archive entries through one URI-oriented object model. A manager resolves names into `FileObject` values; each object projects canonical naming, hierarchy, type, content, metadata, provider capabilities, cache identity, and lifecycle state from one backing namespace.

The scoped providers cover mutable `file` and `ram` namespaces and read-only `zip`, `jar`, `tar`, `tgz`, and `tbz2` layers. Layered archive paths retain a link to their backing file and support nested archives without exposing provider implementation classes.

## Non-Goals

- This specification does not require FTP, FTPS, SFTP, HTTP, WebDAV, HDFS, SMB, resource, temporary, or other network and service-backed providers.
- This specification does not require authentication, monitoring, event delivery, Ant tasks, examples, class loaders, URL handler factories, file replication, or virtual junction file systems.
- This specification does not require platform-sensitive permission mutation, symbolic-link behavior, executable flags, or Windows-only UNC edge cases.
- This specification does not require private helpers, provider parser classes, concrete provider file-object/file-system subclasses, decorators, logging hooks, or operations APIs.
- This specification does not define exact exception message text, logging text, thread names, iteration order where the contract says unordered, or `toString()` formatting beyond named enum values.
- This specification does not require archive mutation; ZIP, JAR, TAR, TGZ, and TBZ2 objects are read-only projections.

## Representative Workflows

### Create and inspect a RAM tree

```java
import java.nio.charset.StandardCharsets;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemManager;
import org.apache.commons.vfs2.VFS;

FileSystemManager manager = VFS.getManager();
FileObject note = manager.resolveFile("ram:///notes/today.txt");
try (var out = note.getContent().getOutputStream()) {
    out.write("ready".getBytes(StandardCharsets.UTF_8));
}

FileObject notes = manager.resolveFile("ram:///notes");
String text = note.getContent().getString(StandardCharsets.UTF_8);
FileObject[] children = notes.getChildren();
```

The write materializes the missing folder and file in one RAM namespace. The object, its parent listing, its content size, and the decoded string are different projections of the same bytes and hierarchy.

### Copy between local and RAM namespaces

```java
import java.nio.file.Path;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.Selectors;
import org.apache.commons.vfs2.VFS;

var manager = VFS.getManager();
FileObject source = manager.toFileObject(Path.of("input-tree"));
FileObject destination = manager.resolveFile("ram:///snapshot");
destination.copyFrom(source, Selectors.SELECT_ALL);

FileObject[] copied = destination.findFiles(Selectors.SELECT_FILES);
```

The selector controls which members are copied. Canonical names belong to the destination namespace, while file/folder structure and selected content agree with the source projection.

### Read a nested archive

```java
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.VFS;

FileObject entry = VFS.getManager().resolveFile(
    "jar:zip:file:///data/bundle.zip!/lib/app.jar!/META-INF/MANIFEST.MF");

String manifest = entry.getContent().getString("UTF-8");
FileObject backingJar = entry.getFileSystem().getParentLayer();
```

Each archive scheme opens a read-only file system over the preceding file. The final object exposes entry bytes and canonical layered naming, while `getParentLayer()` identifies the immediate backing archive.

## Manager, Providers, and Resolution

This section defines manager construction, provider registration, name parsing, and scoped resolution because every other view starts from a resolved name.

**Default and configured managers.**

- When `VFS.getManager()` is called without an installed manager, `VFS` must lazily initialize one shared `StandardFileSystemManager` and return that instance on later calls.
- When `VFS.setManager(manager)` is called, `VFS` must use that exact manager for later `getManager()` calls; when the argument is null, the next `getManager()` call must lazily create a standard manager.
- When `VFS.reset()` is called, `VFS` must close the current shared manager, create a new standard manager, and return the new instance.
- When `VFS.close()` is called, `VFS` must close the current shared manager and clear the shared reference; repeated close calls must leave the class usable.
- When `StandardFileSystemManager.init()` completes, the manager must register the scoped schemes `file`, `ram`, `zip`, `jar`, `tar`, `gz`, `bz2`, `tgz`, and `tbz2` from built-in configuration.
- When an unconfigured `DefaultFileSystemManager` is initialized, it must use `SoftRefFilesCache` and `CacheStrategy.ON_RESOLVE` unless setters supplied replacements before initialization.
- If `setCacheStrategy` or `setFilesCache` is called after `DefaultFileSystemManager.init()`, then the manager must raise `FileSystemException`.

**Provider registration and capabilities.**

- When `addProvider` receives a scheme or scheme array and a `FileProvider`, the manager must register that provider for each name and expose the names through `hasProvider()` and `getSchemes()`.
- If `addProvider` receives a scheme that already has a provider, then the manager must raise `FileSystemException` instead of replacing the registration.
- When `removeProvider(scheme)` removes a registration, `hasProvider(scheme)` must return false and new resolutions for that scheme must fail unless a default provider handles it.
- When `getProviderCapabilities(scheme)` is called for a scoped provider, the manager must return the same operation set reported by that provider's `getCapabilities()`.
- If resolution or capability lookup uses an unknown scheme with no applicable default provider, then the manager must raise `FileSystemException`.

**URI and local-name resolution.**

- When `resolveFile` receives an absolute URI, the manager must select the registered provider from its scheme and return a non-null `FileObject` even when the addressed resource does not exist.
- When `resolveFile` receives an absolute local path or a `File`, `Path`, `URI`, or `URL` naming a local resource, the manager must return a `file`-scheme object for that physical path.
- When `resolveFile` receives a relative name, the manager must resolve it against the supplied base object or file, otherwise against `getBaseFile()`.
- If a relative name is resolved while no explicit or manager base exists, then the manager must raise `FileSystemException`.
- When `resolveFile(name, fileSystemOptions)` is called, the manager must use those options to select or create the file system, and later relative resolutions from the result must retain the same option set.
- When `closeFileSystem(fileSystem)` is called, the manager must remove that file system and its object mappings from manager-owned caches and release its resources.

## Canonical Names and Hierarchy

This section defines canonical paths, relative scopes, type projection, parent/child navigation, and selector traversal.

**Canonical name model.**

- The `FileName` path separator must be `/`, the root path must be `/`, and every `getPath()` result must be an absolute path beginning with `/`.
- When a name contains `/`, `\`, repeated separators, `.` elements, or `..` elements, resolution must normalize separators to `/`, remove redundant elements, and preserve the root boundary.
- If normalization attempts to move above the file-system root or contains an incomplete or invalid percent escape, then resolution must raise `FileSystemException`.
- When a RAM URI contains a valid percent escape, resolution must decode it before projecting both `getPath()` and `getPathDecoded()`; `getURI()` must retain URI validity by percent-encoding characters that require escaping, and normalization must apply the decoded structural meaning of escaped separators or dot elements.
- When `getBaseName()` is called, a non-root name must return its final decoded path element and the root must return an empty string.
- When `getDepth()` is called on a RAM name, the root must return zero and every non-root name must return one plus the number of path elements because the RAM file-system name contributes one additional level.
- When `getParent()` is called on a name or object, the root must return null and every non-root value must return the immediately containing path.
- When `getRelativeName(other)` receives a name in the same file system, it must return a normalized relative path that resolves from the receiver back to `other`.
- When `getFriendlyURI()` or `FileObject.getPublicURIString()` is called, the result must omit any password while retaining enough non-secret naming information for display.

**Resolution scopes.**

- When `NameScope.FILE_SYSTEM` is used, an absolute path must resolve from the owning file-system root and a relative path must resolve from the base name.
- When `NameScope.CHILD` is used, the result must be a direct child of the base; if normalization produces the base, an ancestor, a deeper descendant, or an absolute path, then resolution must raise `FileSystemException`.
- When `NameScope.DESCENDENT` is used, the result must be a strict descendant of the base; if normalization produces the base, an ancestor, or an absolute path, then resolution must raise `FileSystemException`.
- When `NameScope.DESCENDENT_OR_SELF` is used, the result must be the base or one of its descendants; if normalization escapes that subtree, then resolution must raise `FileSystemException`.
- When `FileName.isAncestor(argument)` is called, it must return true exactly when `argument` is a strict ancestor of the receiver; when `FileName.isDescendent(argument)` is called, it must return true exactly when `argument` is a strict descendant of the receiver; when the scoped `isDescendent(argument, nameScope)` overload is called, the same receiver-versus-argument direction must apply and `nameScope` must be evaluated by the resolution-scope rules above.

**Object state and traversal.**

- When a resolved resource does not exist, `exists()` must return false and `getType()` must return `FileType.IMAGINARY`; resolving the name alone must not create backing state.
- When an existing resource is a regular file, `getType()` must return `FileType.FILE`, `isFile()` must return true, `isFolder()` must return false, and its type must report content without children.
- When an existing resource is a folder, `getType()` must return `FileType.FOLDER`, `isFolder()` must return true, `isFile()` must return false, and its type must report children without data content.
- When `getChild(name)` addresses an existing direct child, it must return that child; when no direct child exists, it must return null.
- When `getChildren()` is called on a folder, it must return every direct child in an unordered array and must return an empty array for an empty folder.
- If `getChildren()` or `getChild()` is called on a missing object or a non-folder, then the object must raise `FileSystemException`, with `FileNotFolderException` used for the non-folder case.
- When a `FileSelector` traverses a tree, `FileSelectInfo.getBaseFolder()` must remain the traversal root, `getFile()` must identify the current object, and `getDepth()` must start at zero for the base.
- When standard selectors are used, `SELECT_SELF` must select only depth zero, `SELECT_CHILDREN` only depth one, `SELECT_SELF_AND_CHILDREN` depths zero and one, `EXCLUDE_SELF` every positive depth, `SELECT_FILES` regular files, `SELECT_FOLDERS` folders, and `SELECT_ALL` the base plus all descendants.
- When `findFiles(selector)` returns matches, it must return descendants in depthwise order with a selected child before its selected parent.
- When `findFiles(selector, depthwise, selected)` is called, it must append matches to the supplied list and use deepest-first order exactly when `depthwise` is true.

## Content, Mutation, and Random Access

This section defines how bytes and metadata materialize files, how tree mutations propagate, and how stream and random-access lifecycles behave.

**Creation, copy, move, and deletion.**

- When `createFile()` targets an imaginary path, the object must create missing ancestor folders and a zero-length file; when the path already denotes a file, it must leave its content unchanged.
- When `createFolder()` targets an imaginary path, the object must create all missing ancestor folders; when the path already denotes a folder, it must leave the tree unchanged.
- If `createFile()` targets an existing folder or `createFolder()` targets an existing file, then the object must raise `FileSystemException`.
- When `copyFrom(source, selector)` is called, the destination must copy every selected source object, create missing parents, and replace conflicting destination state before copying.
- When `moveTo(destination)` succeeds within a writable compatible provider, the source must become imaginary and the destination must expose the source's prior type, children, content, and supported metadata.
- When `delete()` targets a missing object, it must return false; when it targets a file or empty folder, it must remove it and return true.
- When `delete()` targets a non-empty RAM folder, it must return false without raising an exception and must preserve the folder and its descendants.
- When `delete(selector)` or `deleteAll()` is called, it must remove selected descendants in a child-before-parent order and return the number of removed objects.

**Streams and whole-content views.**

- When `getContent()` is called for an imaginary file, it must return a content object whose output operations materialize the file and missing parent folders.
- When `getOutputStream()` is opened without append, bytes written before close must replace prior content; when append is true, written bytes must follow prior content, including when the file is created by the append operation.
- When an output stream closes, the provider must commit its bytes so `getSize()`, `getByteArray()`, `getString()`, later input streams, and other resolved objects in the same namespace observe the same content.
- When several input streams are opened for one file, each stream must maintain an independent cursor and return `-1` repeatedly after reaching end of file.
- While an incompatible input, output, or random-access writer is open, the content must reject conflicting access with `FileSystemException`.
- When `FileContent.close()` or `FileObject.close()` is called, the object must close owned streams and commit pending changes, and later operations on the same public object must remain supported.
- When `getByteArray()` is called, it must return all bytes; if the reported size exceeds `Integer.MAX_VALUE`, then it must raise `IllegalStateException`.
- When `getString(charset)` is called with a `Charset` or charset name, it must decode all bytes with that charset; when the charset argument is null, it must use the JVM default charset.
- When `FileContent.write()` or `FileUtil.copyContent()` copies content, it must write all source bytes to the target and the `FileContent.write()` overloads must return the transferred byte count.

**Metadata and random access.**

- When `getSize()` and `isEmpty()` are called on an existing file, size must equal the byte length and emptiness must be true exactly when size is zero.
- When `setLastModifiedTime(modTime)` succeeds on a writable scoped provider, later `getLastModifiedTime()` observations must agree within `FileSystem.getLastModTimeAccuracy()`.
- When attribute names are queried, matching must be case-insensitive, `getAttributeNames()` must never return null, and `getAttributes()` must return a read-only map.
- If a provider does not support attributes or the resource does not exist, then attribute access must raise `FileSystemException` rather than invent values.
- When `getRandomAccessContent(RandomAccessMode.READ)` is opened, reads and seeks must be supported without writes; when `READWRITE` is opened on RAM or local content, reads, writes, seeks, and `setLength()` must be supported; when `getInputStream()` is obtained from either mode, it must begin at the current position, each successful read must advance the same position reported by `getFilePointer()`, and a later `seek(pos)` must set the position for subsequent random-access operations but require a newly obtained input stream.
- When `RandomAccessMode.from` is called with one or more `java.nio.file.AccessMode` arguments, a supported argument list containing `WRITE` must return `RandomAccessMode.READWRITE`, and a supported list containing only `READ` must return `RandomAccessMode.READ`; the supported values must be limited to `AccessMode.READ` and `AccessMode.WRITE`, and the required public form must not be replaced by a `Set` or `OpenOption` overload; when `toAccessModes()` is called, `RandomAccessMode.READ` must return an `AccessMode` array containing only `READ`, while `RandomAccessMode.READWRITE` must return an `AccessMode` array containing `READ` and `WRITE`.
- When random access writes past the current end or `setLength()` grows content, the provider must fill the gap with zero bytes; when `setLength()` shrinks content, bytes beyond the new length must be discarded.
- If `seek(pos)` or `setLength(newLength)` receives a negative value, then random access must raise `IOException`.

## RAM and Local Provider Behavior

This section defines the two writable namespaces and the provider options that distinguish their file-system instances.

**RAM namespace.**

- When `ram:///` is resolved, the RAM root must exist as a folder and deletion of that root must raise `FileSystemException`.
- When two RAM names are resolved with equal `FileSystemOptions`, both objects must belong to the same file-system instance; when their options differ, they must belong to distinct RAM file systems.
- When no RAM maximum is configured, `RamFileSystemConfigBuilder.getLongMaxSize()` must return `Long.MAX_VALUE`; the compatibility `getMaxSize()` must use its documented integer view.
- When `setMaxSize(options, sizeInBytes)` is used, the RAM file system must limit the total bytes of all file contents to that value.
- If a RAM write would make total content exceed `sizeInBytes`, then closing or committing the write must raise `FileSystemException` and the namespace must remain within the configured limit.
- When RAM content is renamed, appended, randomly rewritten, truncated, copied, or deleted, the quota must track the resulting total content rather than cumulative historical writes.

**Local namespace.**

- When `toFileObject(File)`, `toFileObject(Path)`, an absolute local path, and an equivalent `file:` URI address the same physical path, the resulting names must identify the same local resource.
- When a local `FileObject` is mutated through create, write, append, move, copy, timestamp, or delete operations, the corresponding physical file-system state must reflect the completed operation.
- When external local state changes, `refresh()` must invalidate attached metadata so later existence, type, child, size, and timestamp observations reflect the physical state.
- If a local operation is rejected by the host file system, then the public operation must raise `FileSystemException` or `IOException` and must not report success.

## Layered Archive Behavior

This section defines read-only archive URI composition, entry projection, nesting, metadata, and archive lifecycle.

**Layered names and trees.**

- When a `zip`, `jar`, or `tar` URI names an archive followed by `!` and an absolute entry path, resolution must expose the archive root or addressed entry as a read-only `FileObject` hierarchy.
- When a `tgz` or `tbz2` URI is used, resolution must behave as the corresponding `tar:gz` or `tar:bz2` composition.
- When an archive URI contains multiple layered schemes and `!` boundaries, each layer must use the preceding entry as its backing file and the final object must expose the innermost path.
- When a literal exclamation mark belongs to an archive or entry name, callers must encode it as `%21`, and decoded naming views must restore the literal character.
- When an archive lacks explicit directory records, the hierarchy must still synthesize parent folders needed to expose contained entries.
- When an archive entry is a file, its type, size, timestamp, and bytes must reflect the archive entry; when it is a folder, child listing must expose its direct entries.
- When `getParentLayer()` is called on an archive file system, it must return the immediate backing archive `FileObject`; originating RAM and local file systems must return null.

**Read-only and metadata rules.**

- When archive content is read, independent streams and sequential reads after other streams or file objects close must continue to return the stored entry bytes until the archive file system is closed.
- When ZIP entry names are decoded without an explicit option, `ZipFileSystemConfigBuilder` must use UTF-8; when a charset is set in `FileSystemOptions`, the ZIP layer must use that charset for entry names.
- When JAR content attributes are queried, the read-only map must combine main manifest attributes with entry attributes, with entry values taking precedence for the same public attribute name.
- If create, output, append, random-write, attribute mutation, move, or delete is requested on an archive entry, then the operation must raise `FileSystemException`.
- If the backing archive is missing, unreadable, malformed, or inconsistent with the selected archive scheme, then resolution or first content access must raise `FileSystemException`.

## Cache Identity and Lifecycle

This section defines file-object identity caches, refresh strategies, option-sensitive file systems, and safe resource release.

**Object cache contract.**

- When `DefaultFilesCache` stores an object, `getFile(fileSystem, name)` must return the stored strong reference until removal, file-system clear, or cache close.
- When `SoftRefFilesCache` or `WeakRefFilesCache` stores an object, lookup must return the same live reference while its reference remains available and must return null after collection or explicit removal.
- When `NullFilesCache` receives `putFile`, it must retain nothing; `getFile` must always return null and `putFileIfAbsent` must return false.
- When `putFileIfAbsent(object)` sees no live mapping, it must install the object and return true; when a live mapping exists, it must preserve that mapping and return false.
- When `removeFile(fileSystem, name)` is called, only that mapping must disappear; when `clear(fileSystem)` is called, every mapping for that file system must disappear; when `close()` is called, every mapping must disappear.

**Refresh and manager lifecycle.**

- While `CacheStrategy.MANUAL` is active, cached metadata must remain attached until `FileObject.refresh()` or lifecycle invalidation occurs.
- While `CacheStrategy.ON_RESOLVE` is active, an external manager or object resolution must refresh the resolved object's metadata before returning it.
- While `CacheStrategy.ON_CALL` is active, state-reading `FileObject` operations must refresh provider metadata before returning their observation.
- When equal canonical names are resolved in one file system with an object cache, the manager must reuse the cached live object according to the selected `FilesCache`; with `NullFilesCache`, repeated resolution must return distinct objects.
- When manager or file-system close occurs, open resources must be released, relevant cache mappings must be cleared, and a later standard-manager initialization must start a usable lifecycle.

## State Model

The core state is a set of provider-backed file systems. Each file system is identified by provider scheme, root, and `FileSystemOptions`, and contains canonical names mapped to imaginary, file, or folder state. Existing files carry bytes and supported metadata; layered file systems additionally retain an immediate backing file.

The public projections of that state are:

1. Manager projection through registered schemes, capabilities, base resolution, option-sensitive file-system selection, and lifecycle.
2. Name projection through canonical URI, encoded and decoded path, base name, depth, parent, root, relative name, and scope relations.
3. Object projection through existence, type, parent/children, selector traversal, and copy/move/delete results.
4. Content projection through streams, whole-content views, size, timestamp, attributes, and random-access position and length.
5. Provider projection through physical local state, in-memory RAM state and quota, and archive entries and backing layers.
6. Cache projection through file-system/name identity, object reuse, refresh strategy, removal, and close.

## Error Semantics

| Condition | Required result |
|---|---|
| Unknown or duplicate provider scheme | If no applicable provider exists or a scheme is already registered, then the manager must raise `FileSystemException`. |
| Invalid percent encoding, root escape, or scope escape | If a name is malformed or resolves beyond its permitted root/subtree, then resolution must raise `FileSystemException`. |
| Missing relative-resolution base | If a relative name has no supplied or configured base, then the manager must raise `FileSystemException`. |
| Missing file during content/metadata access | If an operation requires an existing file and the object is imaginary, then it must raise `FileNotFoundException` or `FileSystemException`. |
| Child operation on a non-folder | If child listing or lookup targets a regular file, then it must raise `FileNotFolderException`. |
| Content operation on a no-content type | If byte content is requested from a folder or another no-content type, then it must raise `FileTypeHasNoContentException` or `FileSystemException`. |
| Type mismatch during create | If file creation targets a folder or folder creation targets a file, then the operation must raise `FileSystemException`. |
| Conflicting open stream or unsupported access | If stream state or provider capabilities reject an access mode, then content access must raise `FileSystemException`. |
| RAM capacity exceeded | If a committed write would exceed the configured RAM maximum, then the write must raise `FileSystemException`. |
| Archive mutation | If a mutation targets a read-only archive entry, then the operation must raise `FileSystemException`. |
| Malformed or unreadable archive | If a backing file is not a readable archive for the selected scheme, then resolution or content access must raise `FileSystemException`. |
| Negative random-access position or length | If a negative seek position or length is requested, then random access must raise `IOException`. |
| Whole-content array too large | If `FileContent.getByteArray()` observes a size above `Integer.MAX_VALUE`, then it must raise `IllegalStateException`. |
| Manager reconfiguration after initialization | If cache strategy or cache implementation is changed after initialization, then the manager must raise `FileSystemException`. |

## Cross-View Invariants

1. When bytes are committed through a `FileContent` output or random-access view, the same canonical object and every equivalent resolution in that file system must report matching existence, `FILE` type, size, byte array, decoded string, and input-stream content.
2. When a file or folder is created, moved, copied, or deleted, its parent `getChildren()`, selector traversal, child lookup, canonical name relations, and provider backing state must agree with the completed hierarchy.
3. When a name is resolved through manager, object-relative, file-system-relative, local `File`/`Path`, or equivalent URI entry points, all results must agree on canonical `FileName` identity, root, path, parent chain, and owning file system.
4. When equal RAM options are used, resolved objects must share one RAM namespace and quota; when options differ, neither content nor cache identity must cross between the resulting file systems.
5. When local content changes through the VFS view, physical local bytes and metadata must agree after commit; when physical state changes externally, a contract-required refresh must make the VFS projections agree.
6. When an archive entry is resolved, the layered URI, entry hierarchy, content bytes, read-only capability set, and `getParentLayer()` chain must describe the same sequence of backing archives.
7. When a JAR manifest or entry attribute is visible through `FileContent`, attribute-name lookup, the read-only attribute map, and the archive entry selected by the canonical name must agree.
8. When a cached live object is reused, its file system and canonical name must match the cache key; after removal, clear, close, or `NullFilesCache` resolution, no stale object identity must be reported as a cache hit.
9. While each `CacheStrategy` is active, manager resolution, `FileObject.refresh()`, and state-reading methods must expose metadata at the freshness boundary defined for that strategy.
10. When a manager or file system closes, its cache and resource projections must agree that resources were released, while a newly initialized manager must resolve scoped providers without inheriting closed state.

## Public Interface

### Import Surface

```java
import org.apache.commons.vfs2.CacheStrategy;
import org.apache.commons.vfs2.Capability;
import org.apache.commons.vfs2.FileContent;
import org.apache.commons.vfs2.FileContentInfo;
import org.apache.commons.vfs2.FileName;
import org.apache.commons.vfs2.FileNotFolderException;
import org.apache.commons.vfs2.FileNotFoundException;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSelectInfo;
import org.apache.commons.vfs2.FileSelector;
import org.apache.commons.vfs2.FileSystem;
import org.apache.commons.vfs2.FileSystemConfigBuilder;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.FileSystemManager;
import org.apache.commons.vfs2.FileSystemOptions;
import org.apache.commons.vfs2.FileType;
import org.apache.commons.vfs2.FileTypeHasNoContentException;
import org.apache.commons.vfs2.FileUtil;
import org.apache.commons.vfs2.FilesCache;
import org.apache.commons.vfs2.NameScope;
import org.apache.commons.vfs2.RandomAccessContent;
import org.apache.commons.vfs2.Selectors;
import org.apache.commons.vfs2.VFS;
```

```java
import org.apache.commons.vfs2.cache.DefaultFilesCache;
import org.apache.commons.vfs2.cache.NullFilesCache;
import org.apache.commons.vfs2.cache.SoftRefFilesCache;
import org.apache.commons.vfs2.cache.WeakRefFilesCache;
import org.apache.commons.vfs2.impl.DefaultFileSystemManager;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.apache.commons.vfs2.util.RandomAccessMode;
```

```java
import org.apache.commons.vfs2.provider.FileProvider;
import org.apache.commons.vfs2.provider.LocalFileProvider;
import org.apache.commons.vfs2.provider.bzip2.Bzip2FileProvider;
import org.apache.commons.vfs2.provider.gzip.GzipFileProvider;
import org.apache.commons.vfs2.provider.jar.JarFileProvider;
import org.apache.commons.vfs2.provider.local.DefaultLocalFileProvider;
import org.apache.commons.vfs2.provider.ram.RamFileProvider;
import org.apache.commons.vfs2.provider.ram.RamFileSystemConfigBuilder;
import org.apache.commons.vfs2.provider.tar.TarFileProvider;
import org.apache.commons.vfs2.provider.tar.Tbz2FileProvider;
import org.apache.commons.vfs2.provider.tar.TgzFileProvider;
import org.apache.commons.vfs2.provider.zip.ZipFileProvider;
import org.apache.commons.vfs2.provider.zip.ZipFileSystemConfigBuilder;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `VFS` | class | Owns the shared default manager and URI-style switch. |
| `VFS.getManager` | method | Returns or initializes the shared manager. |
| `VFS.setManager` | method | Installs or clears the shared manager. |
| `VFS.reset` | method | Replaces the shared manager with a fresh standard manager. |
| `VFS.close` | method | Closes and clears the shared manager. |
| `VFS.isUriStyle` | method | Reports URI-style formatting. |
| `VFS.setUriStyle` | method | Sets URI-style formatting. |
| `FileSystemManager` | interface | Resolves names and coordinates providers and file systems. |
| `FileSystemManager.close` | method | Releases manager-owned resources. |
| `FileSystemManager.closeFileSystem` | method | Closes one file system. |
| `FileSystemManager.canCreateFileSystem` | method | Reports layered-provider support for a backing file. |
| `FileSystemManager.createFileSystem` | method | Creates a layered file-system root. |
| `FileSystemManager.getBaseFile` | method | Returns the relative-resolution base. |
| `FileSystemManager.getCacheStrategy` | method | Returns the active refresh strategy. |
| `FileSystemManager.getFilesCache` | method | Returns the active object cache. |
| `FileSystemManager.getFileSystemConfigBuilder` | method | Returns a scheme's option builder. |
| `FileSystemManager.getProviderCapabilities` | method | Returns a scheme's capability set. |
| `FileSystemManager.getSchemes` | method | Returns registered schemes. |
| `FileSystemManager.hasProvider` | method | Tests scheme registration. |
| `FileSystemManager.resolveFile` | method | Resolves string, based, local, URI, and URL names. |
| `FileSystemManager.resolveName` | method | Resolves and normalizes a name under a scope. |
| `FileSystemManager.resolveURI` | method | Parses an absolute URI into a `FileName`. |
| `FileSystemManager.toFileObject` | method | Converts a local `File` or `Path`. |
| `FileObject` | interface | Projects one canonical path and its provider state. |
| `FileObject.EMPTY_ARRAY` | constant | Shared empty object array. |
| `FileObject.close` | method | Closes an instance or performs a null-safe static close. |
| `FileObject.canRenameTo` | method | Reports compatible rename support. |
| `FileObject.copyFrom` | method | Copies a selected source tree. |
| `FileObject.createFile` | method | Materializes a file and missing ancestors. |
| `FileObject.createFolder` | method | Materializes a folder and missing ancestors. |
| `FileObject.delete` | method | Deletes self or selected descendants. |
| `FileObject.deleteAll` | method | Deletes self and all descendants. |
| `FileObject.exists` | method | Reports existence. |
| `FileObject.findFiles` | method | Traverses and collects selector matches. |
| `FileObject.getChild` | method | Returns an existing direct child or null. |
| `FileObject.getChildren` | method | Returns direct children. |
| `FileObject.getContent` | method | Returns the content projection. |
| `FileObject.getFileSystem` | method | Returns the owning file system. |
| `FileObject.getName` | method | Returns the canonical name. |
| `FileObject.getParent` | method | Returns the containing folder or null. |
| `FileObject.getPath` | method | Returns a NIO path view. |
| `FileObject.getPublicURIString` | method | Returns a credential-safe URI string. |
| `FileObject.getType` | method | Returns current file type. |
| `FileObject.getURI` | method | Returns an ASCII-safe URI. |
| `FileObject.getURL` | method | Returns a VFS-backed URL. |
| `FileObject.isAttached` | method | Reports attachment state. |
| `FileObject.isContentOpen` | method | Reports open content resources. |
| `FileObject.isFile` | method | Tests regular-file state. |
| `FileObject.isFolder` | method | Tests folder state. |
| `FileObject.isHidden` | method | Tests hidden state. |
| `FileObject.isReadable` | method | Tests readable state. |
| `FileObject.isWriteable` | method | Tests writable state. |
| `FileObject.moveTo` | method | Moves or renames to a destination. |
| `FileObject.refresh` | method | Invalidates attached metadata. |
| `FileObject.resolveFile` | method | Resolves a name within the owning file system. |
| `FileContent` | interface | Projects bytes, streams, metadata, and random access. |
| `FileContent.close` | method | Commits and closes owned content resources. |
| `FileContent.getAttribute` | method | Looks up a content attribute. |
| `FileContent.getAttributeNames` | method | Returns attribute names. |
| `FileContent.getAttributes` | method | Returns a read-only attribute map. |
| `FileContent.getByteArray` | method | Reads all bytes. |
| `FileContent.getCertificates` | method | Returns signer certificates. |
| `FileContent.getContentInfo` | method | Returns type and encoding metadata. |
| `FileContent.getFile` | method | Returns the owning object. |
| `FileContent.getInputStream` | method | Opens buffered input. |
| `FileContent.getLastModifiedTime` | method | Returns last-modified time. |
| `FileContent.getOutputStream` | method | Opens replace or append output. |
| `FileContent.getRandomAccessContent` | method | Opens random-access content. |
| `FileContent.getSize` | method | Returns byte length. |
| `FileContent.getString` | method | Reads and decodes all bytes. |
| `FileContent.hasAttribute` | method | Tests attribute presence. |
| `FileContent.isEmpty` | method | Tests zero length. |
| `FileContent.isOpen` | method | Reports content resource state. |
| `FileContent.removeAttribute` | method | Removes a writable attribute. |
| `FileContent.setAttribute` | method | Sets a writable attribute. |
| `FileContent.setLastModifiedTime` | method | Sets last-modified time. |
| `FileContent.write` | method | Copies all bytes to content, object, or stream targets. |
| `FileContentInfo` | interface | Exposes content type and encoding. |
| `FileContentInfo.getContentEncoding` | method | Returns content encoding or null. |
| `FileContentInfo.getContentType` | method | Returns content type or null. |
| `FileName` | interface | Immutable canonical name. |
| `FileName.SEPARATOR_CHAR` | constant | Canonical separator character. |
| `FileName.SEPARATOR` | constant | Canonical separator string. |
| `FileName.ROOT_PATH` | constant | Canonical root path. |
| `FileName.EMPTY_ARRAY` | constant | Shared empty name array. |
| `FileName.getBaseName` | method | Returns the final decoded path element. |
| `FileName.getDepth` | method | Returns root-relative depth. |
| `FileName.getExtension` | method | Returns the final-name extension. |
| `FileName.getFriendlyURI` | method | Returns a credential-safe display URI. |
| `FileName.getParent` | method | Returns the parent name or null. |
| `FileName.getPath` | method | Returns the encoded canonical path. |
| `FileName.getPathDecoded` | method | Returns the decoded canonical path. |
| `FileName.getRelativeName` | method | Returns a relative path to another name. |
| `FileName.getRoot` | method | Returns the root name. |
| `FileName.getRootURI` | method | Returns the root URI. |
| `FileName.getScheme` | method | Returns the provider scheme. |
| `FileName.getType` | method | Returns requested or attached type. |
| `FileName.getURI` | method | Returns the absolute canonical URI. |
| `FileName.isAncestor` | method | Tests strict ancestry. |
| `FileName.isDescendent` | method | Tests strict or scoped descent. |
| `FileName.isFile` | method | Tests file-name type. |
| `FileSystem` | interface | Represents one provider-backed namespace. |
| `FileSystem.getFileSystemManager` | method | Returns the owner manager. |
| `FileSystem.getFileSystemOptions` | method | Returns creation options. |
| `FileSystem.getLastModTimeAccuracy` | method | Returns timestamp accuracy. |
| `FileSystem.getParentLayer` | method | Returns the immediate backing archive. |
| `FileSystem.getRoot` | method | Returns the root object. |
| `FileSystem.getRootName` | method | Returns the root name. |
| `FileSystem.getRootURI` | method | Returns the root URI. |
| `FileSystem.hasCapability` | method | Tests provider capability. |
| `FileSystem.resolveFile` | method | Resolves within the namespace. |
| `FileSystemOptions` | class | Holds provider options and participates in file-system identity. |
| `FileSystemOptions.clone` | method | Copies an option set. |
| `FileSystemOptions.equals` | method | Compares option values. |
| `FileSystemOptions.hashCode` | method | Hashes option values. |
| `FileSystemOptions.compareTo` | method | Orders option sets. |
| `FileSystemConfigBuilder` | class | Base class for scheme option builders. |
| `FileSystemConfigBuilder.getRootURI` | method | Reads the root URI option. |
| `FileSystemConfigBuilder.setRootURI` | method | Writes the root URI option. |
| `FileType` | enum | Declares `FOLDER`, `FILE`, `FILE_OR_FOLDER`, and `IMAGINARY`. |
| `FileType.getName` | method | Returns the public type name. |
| `FileType.hasAttributes` | method | Reports attribute support by type. |
| `FileType.hasChildren` | method | Reports child support by type. |
| `FileType.hasContent` | method | Reports content support by type. |
| `NameScope` | enum | Declares `CHILD`, `DESCENDENT`, `DESCENDENT_OR_SELF`, and `FILE_SYSTEM`. |
| `NameScope.getName` | method | Returns the public scope name. |
| `FileSelector` | interface | Selects objects and controls traversal. |
| `FileSelector.includeFile` | method | Selects one visited object. |
| `FileSelector.traverseDescendants` | method | Controls subtree traversal. |
| `FileSelector.traverseDescendents` | method | Compatibility spelling for subtree traversal. |
| `FileSelectInfo` | interface | Describes one selector visit. |
| `FileSelectInfo.getBaseFolder` | method | Returns the traversal base. |
| `FileSelectInfo.getDepth` | method | Returns visit depth. |
| `FileSelectInfo.getFile` | method | Returns the visited object. |
| `Selectors` | class | Publishes standard selector constants. |
| `Selectors.SELECT_SELF` | constant | Selects the base. |
| `Selectors.SELECT_SELF_AND_CHILDREN` | constant | Selects the base and direct children. |
| `Selectors.SELECT_CHILDREN` | constant | Selects direct children. |
| `Selectors.EXCLUDE_SELF` | constant | Selects all descendants. |
| `Selectors.SELECT_FILES` | constant | Selects regular files. |
| `Selectors.SELECT_FOLDERS` | constant | Selects folders. |
| `Selectors.SELECT_ALL` | constant | Selects the base and all descendants. |
| `FileUtil` | class | Provides complete-content copy/read/write helpers. |
| `FileUtil.copyContent` | method | Copies bytes between objects. |
| `FileUtil.getContent` | method | Reads all bytes from an object. |
| `FileUtil.writeContent` | method | Writes all object bytes to a stream. |
| `RandomAccessContent` | interface | Provides seekable data input and output. |
| `RandomAccessContent.getFilePointer` | method | Returns the current offset. |
| `RandomAccessContent.getInputStream` | method | Returns input from the current offset. |
| `RandomAccessContent.length` | method | Returns current length. |
| `RandomAccessContent.seek` | method | Repositions the cursor. |
| `RandomAccessContent.setLength` | method | Truncates or extends writable content. |
| `RandomAccessContent.close` | method | Commits and releases random access. |
| `RandomAccessMode` | enum | Declares `READ` and `READWRITE`. |
| `RandomAccessMode.from` | method | Converts NIO access modes. |
| `RandomAccessMode.getModeString` | method | Returns the provider mode string. |
| `RandomAccessMode.requestRead` | method | Reports requested read access. |
| `RandomAccessMode.requestWrite` | method | Reports requested write access. |
| `RandomAccessMode.toAccessModes` | method | Returns equivalent NIO access modes. |
| `CacheStrategy` | enum | Declares `MANUAL`, `ON_RESOLVE`, and `ON_CALL`. |
| `CacheStrategy.getName` | method | Returns the public strategy name. |
| `FilesCache` | interface | Maps file-system/name keys to object identities. |
| `FilesCache.getFile` | method | Looks up a cached object. |
| `FilesCache.putFile` | method | Inserts or replaces an object. |
| `FilesCache.putFileIfAbsent` | method | Inserts only when no live mapping exists. |
| `FilesCache.removeFile` | method | Removes one mapping. |
| `FilesCache.clear` | method | Clears mappings for one file system. |
| `FilesCache.close` | method | Clears all mappings and releases resources. |
| `DefaultFilesCache` | class | Strong-reference cache with a public no-argument constructor. |
| `SoftRefFilesCache` | class | Soft-reference cache with a public no-argument constructor. |
| `WeakRefFilesCache` | class | Weak-reference cache with a public no-argument constructor. |
| `NullFilesCache` | class | No-op cache with a public no-argument constructor. |
| `Capability` | enum | Names provider operations including create, delete, rename, type, children, URI, content, append, random access, attributes, timestamps, compression, and virtual layers. |
| `FileSystemException` | exception | Checked VFS I/O failure with code, context, cause, and null-guard constructors/helpers. |
| `FileSystemException.requireNonNull` | method | Rejects null with this exception family. |
| `FileSystemException.getCode` | method | Returns the message/resource code. |
| `FileSystemException.getInfo` | method | Returns formatting context values. |
| `FileNotFoundException` | exception | Specializes missing-resource access failure. |
| `FileNotFolderException` | exception | Specializes child access on a non-folder. |
| `FileTypeHasNoContentException` | exception | Specializes content access on a no-content type. |
| `DefaultFileSystemManager` | class | Programmatically configured manager with a public no-argument constructor. |
| `DefaultFileSystemManager.addProvider` | method | Registers one or several schemes. |
| `DefaultFileSystemManager.removeProvider` | method | Unregisters a scheme. |
| `DefaultFileSystemManager.init` | method | Applies defaults and activates the manager. |
| `DefaultFileSystemManager.setBaseFile` | method | Sets the relative-resolution base. |
| `DefaultFileSystemManager.setCacheStrategy` | method | Sets pre-initialization refresh strategy. |
| `DefaultFileSystemManager.setFilesCache` | method | Sets the pre-initialization object cache. |
| `DefaultFileSystemManager.freeUnusedResources` | method | Releases unused provider resources. |
| `StandardFileSystemManager` | class | Built-in/classpath-configured manager with a public no-argument constructor. |
| `StandardFileSystemManager.init` | method | Loads built-in and classpath provider configuration. |
| `FileProvider` | interface | Defines originating and layered provider entry points. |
| `FileProvider.findFile` | method | Resolves through an originating provider. |
| `FileProvider.createFileSystem` | method | Creates a layered root. |
| `FileProvider.parseUri` | method | Parses a provider URI. |
| `FileProvider.getCapabilities` | method | Returns provider capabilities. |
| `FileProvider.getConfigBuilder` | method | Returns provider options builder or null. |
| `LocalFileProvider` | interface | Extends providers with local-file lookup. |
| `LocalFileProvider.findLocalFile` | method | Resolves a `File` or local path. |
| `LocalFileProvider.isAbsoluteLocalName` | method | Tests platform-aware absolute local naming. |
| `DefaultLocalFileProvider` | class | Mutable local provider with a public no-argument constructor. |
| `RamFileProvider` | class | Mutable memory provider with a public no-argument constructor. |
| `RamFileSystemConfigBuilder` | class | Configures RAM file systems. |
| `RamFileSystemConfigBuilder.getInstance` | method | Returns the singleton builder. |
| `RamFileSystemConfigBuilder.getLongMaxSize` | method | Returns the long quota. |
| `RamFileSystemConfigBuilder.getMaxSize` | method | Returns the compatibility integer quota. |
| `RamFileSystemConfigBuilder.setMaxSize` | method | Sets total content-byte quota. |
| `ZipFileProvider` | class | Read-only ZIP provider with a public no-argument constructor. |
| `ZipFileSystemConfigBuilder` | class | Configures ZIP entry-name decoding. |
| `ZipFileSystemConfigBuilder.getInstance` | method | Returns the singleton builder. |
| `ZipFileSystemConfigBuilder.getCharset` | method | Returns configured or UTF-8 charset. |
| `ZipFileSystemConfigBuilder.setCharset` | method | Sets archive-entry charset. |
| `JarFileProvider` | class | Read-only JAR provider with manifest attributes and a public no-argument constructor. |
| `TarFileProvider` | class | Read-only TAR provider with a public no-argument constructor. |
| `TgzFileProvider` | class | Composite TGZ provider with a public no-argument constructor. |
| `Tbz2FileProvider` | class | Composite TBZ2 provider with a public no-argument constructor. |
| `GzipFileProvider` | class | Read-only GZIP layer with a public no-argument constructor. |
| `Bzip2FileProvider` | class | Read-only BZIP2 layer with a public no-argument constructor. |

### CLI Entry Points

There is no console script for this package. `java -jar commons-vfs2.jar` is not supported. Programmatic use is through the Java packages above.

## Appendix A: Environment

The working environment runs Linux with OpenJDK 17 and Apache Maven. Compiled library classes must remain compatible with Java 8 bytecode and language level. The local Maven repository provides JUnit Jupiter for assessment code and the runtime libraries `commons-logging`, `commons-lang3`, `commons-io`, and `commons-compress`; no external service is available and network access is disabled.

The project must provide a standard Maven `pom.xml` at the project root with `groupId` `org.apache.commons`, `artifactId` `commons-vfs2`, and version `2.11.0-SNAPSHOT`. Production Java sources must live under `src/main/java`, and the POM must declare every non-JDK runtime dependency used by the implementation. Maven must compile and test the project without downloading additional artifacts.

## Appendix B: Assessment Notes

Assessment uses public Java imports and members from this document. Checks cover manager/provider lifecycle, canonical and scoped naming, file/folder state, selectors, stream and whole-content behavior, copy/move/delete, timestamps and attributes, random access, RAM quota and option isolation, local backing-state agreement, nested read-only archives, provider capabilities, cache identity, refresh strategies, and cross-view invariants.

Atomic checks focus on one public rule. Integration checks combine resolution, canonical names, hierarchy, content, provider backing state, layered archives, cache identity, and lifecycle. Temporary local files and archives are generated during assessment; live network services, private fields, internal helper classes, exact messages, and textual representations are not assessed.
