
# Rope Specification

## Product Overview

Rope is a Python refactoring library for tools that need to understand and change a Python project on disk. A rope project is a filesystem tree plus a small amount of rope-owned metadata. The public API lets an editor or script open a project, address files and folders as resources, compute refactoring changes, preview those changes, commit them through project history, undo or redo committed changes, and ask IDE-style questions such as completions, definitions, occurrences, and auto-import suggestions.

Rope treats source code as the primary view of truth. Refactorings return `Change` objects before any filesystem mutation happens. Calling `Project.do(changes)` is the normal way to apply those changes so history, observers, object information, and resource paths stay consistent.

## Scope

This specification covers the Python library surface for:

- Opening and configuring projects.
- Addressing files and folders through resources.
- Reading, writing, creating, moving, removing, previewing, applying, undoing, and redoing changes.
- Static and dynamic object analysis as exposed through `PyCore` and `libutils`.
- Refactoring classes and factories in `rope.refactor`.
- Import organization helpers.
- IDE helper APIs in `rope.contrib`, including code assist, find operations, generation helpers, bad-access reporting, batched changes, module-name fixing, and auto-import.
- Public exception types and task progress/cancellation objects.

## Installable Surface

Install the package as `rope`. There is no required command-line entry point; the supported surface is the Python import API.

The package root exposes metadata:

```python
import rope

rope.VERSION
rope.INFO
rope.COPYRIGHT
```

The documented public import paths are:

```python
from rope.base import project, libutils, exceptions
from rope.base.project import Project
from rope.base.resources import Resource, File, Folder
from rope.base.change import (
    Change,
    ChangeSet,
    ChangeContents,
    MoveResource,
    CreateResource,
    CreateFolder,
    CreateFile,
    RemoveResource,
)
from rope.base.fscommands import FileSystemCommands
from rope.base.history import History
from rope.base.pycore import PyCore
from rope.base.taskhandle import TaskHandle

from rope.refactor.rename import Rename, ChangeOccurrences
from rope.refactor.move import create_move, MoveMethod, MoveGlobal, MoveModule
from rope.refactor.inline import create_inline, InlineMethod, InlineVariable, InlineParameter
from rope.refactor.extract import ExtractMethod, ExtractVariable
from rope.refactor.restructure import Restructure
from rope.refactor.change_signature import (
    ChangeSignature,
    ArgumentNormalizer,
    ArgumentRemover,
    ArgumentAdder,
    ArgumentDefaultInliner,
    ArgumentReorderer,
)
from rope.refactor.importutils import ImportOrganizer, ImportTools
from rope.refactor.topackage import ModuleToPackage
from rope.refactor.usefunction import UseFunction
from rope.refactor.encapsulate_field import EncapsulateField
from rope.refactor.introduce_factory import IntroduceFactory
from rope.refactor.introduce_parameter import IntroduceParameter
from rope.refactor.localtofield import LocalToField
from rope.refactor.method_object import MethodObject
from rope.refactor.multiproject import MultiProjectRefactoring, perform
from rope.refactor.wildcards import DefaultWildcard

from rope.contrib import codeassist, findit, generate
from rope.contrib.codeassist import CompletionProposal, NamedParamProposal
from rope.contrib.findit import Location
from rope.contrib.finderrors import find_errors, Error
from rope.contrib.fixmodnames import FixModuleNames
from rope.contrib.changestack import ChangeStack
from rope.contrib.autoimport import AutoImport
from rope.contrib.autoimport.defs import SearchResult
from rope.contrib.autoimport.sqlite import AutoImport as SqliteAutoImport
```

The package-level `rope.contrib.autoimport.AutoImport` is the legacy pickle-backed compatibility class. The sqlite-backed implementation is public as `rope.contrib.autoimport.sqlite.AutoImport` and is the interface new integrations should prefer.

## Public API

### Projects and Resources

```python
Project(projectroot, fscommands=None, ropefolder=".ropeproject", **prefs)
```

`projectroot` is the root folder of the project. If the folder does not exist, rope creates it. If it exists and is not a directory, opening the project raises `RopeError`. By default rope uses a folder named `.ropeproject` under the root for configuration and persisted data. Passing `ropefolder=None` disables that folder.

Project preferences may come from configuration files and from constructor keyword arguments. Constructor keyword arguments override configuration values. Rope reads `[tool.rope]` from `pyproject.toml` when present. If that is absent, it reads `config.py` from the rope folder when present. If neither project-local source is available, it may read the global `pytool.toml` location supported by `pytoolconfig`.

Important project attributes and methods:

```python
project.address
project.root
project.ropefolder
project.history
project.pycore
project.get_resource(resource_name)
project.get_file(path)
project.get_folder(path)
project.get_files()
project.get_python_files()
project.find_module(modname, folder=None)
project.get_module(name, folder=None)
project.get_pymodule(resource, force_errors=False)
project.get_pycore()
project.find_relative_module(modname, folder, level)
project.get_relative_module(name, folder, level)
project.get_source_folders()
project.get_python_path_folders()
project.is_ignored(resource)
project.validate(folder=None)
project.do(changes, task_handle=DEFAULT_TASK_HANDLE)
project.close()
project.sync()
project.set(key, value)
project.get_prefs()
```

Resource names inside a project use slash-separated paths relative to the project root. The project root resource has path `""`. `Project.get_resource()` requires the path to exist and raises `ResourceNotFoundError` otherwise. `get_file()` and `get_folder()` may return resources that do not exist yet, which is useful when building create changes.

`get_pymodule()` returns rope's parsed Python-module object for a resource. `get_pycore()` returns the same object exposed by the `pycore` attribute. `is_ignored()` reflects the project's ignored-resource matcher and is used by file listing, history, and filesystem command selection.

`Resource`, `File`, and `Folder` objects expose:

```python
resource.project
resource.path
resource.name
resource.real_path
resource.pathlib
resource.exists()
resource.is_folder()
resource.is_dir()
resource.parent
resource.move(new_location)
resource.remove()

file.read()
file.read_bytes()
file.write(contents)

folder.get_children()
folder.get_child(name)
folder.has_child(name)
folder.get_files()
folder.get_folders()
folder.contains(resource)
folder.create_file(file_name)
folder.create_folder(folder_name)
```

`Resource.move()`, `Resource.remove()`, `File.write()`, `Folder.create_file()`, and `Folder.create_folder()` apply their effects through `Project.do()` and therefore participate in history and observers. `File.read()` normalizes file newlines to `\n` and remembers the original newline style so a later `File.write()` can preserve it. Encoding cookies in the first two lines are honored when reading and writing source files.

### Library Utilities

```python
libutils.path_to_resource(project, path, type=None)
libutils.path_relative_to_project_root(project, path)
libutils.report_change(project, path, old_content)
libutils.analyze_module(project, resource)
libutils.analyze_modules(project, task_handle=DEFAULT_TASK_HANDLE)
libutils.get_string_module(project, code, resource=None, force_errors=False)
libutils.get_string_scope(project, code, resource=None)
libutils.is_python_file(project, resource)
libutils.modname(resource)
```

`path_to_resource()` accepts an absolute or project-relative path. If the path is outside the project, it returns a resource backed by rope's no-project view rather than forcing it into the project. When `type` is `"file"` or `"folder"`, the target need not already exist.

`report_change()` is the hook an editor should call after saving a file outside rope. It notifies project observers and, when automatic static object analysis is enabled, analyzes the changed scopes using the old contents passed by the caller.

`get_string_module()` parses code that is not necessarily stored in a project file. If `force_errors=True`, syntax errors raise `ModuleSyntaxError` regardless of the `ignore_syntax_errors` preference.

`modname(resource)` returns the dotted module name for Python file, package folder, or package `__init__.py` resources by walking package parents.

### Changes and History

Refactorings and generators return `Change` objects, usually a `ChangeSet`.

```python
change.get_description()
change.get_changed_resources()

ChangeSet(description, timestamp=None)
changes.changes
changes.description
changes.add_change(change)
changes.do(job_set=DEFAULT_JOB_SET)
changes.undo(job_set=DEFAULT_JOB_SET)

ChangeContents(resource, new_contents, old_contents=None)
MoveResource(resource, new_location, exact=False)
CreateFile(parent, name)
CreateFolder(parent, name)
RemoveResource(resource)
```

`get_description()` is the preview surface. `ChangeContents.get_description()` returns a unified diff. `MoveResource.get_description()` describes a rename from the old resource path to the new resource path. `ChangeSet.get_changed_resources()` is the set of resources an editor should reload after applying the change.

Use `Project.do(changes)` for normal application. Doing so records interesting changes in `project.history`; changes that only affect ignored resources are not recorded. `project.history.undo()` undoes the most recent committed change, and `project.history.redo()` reapplies the most recent undone change. Both may also receive a specific history item, in which case rope also handles later dependent changes that touch the same resources or containing folders. Undoing a `RemoveResource` is not implemented.

`project.close()` writes persisted project data such as history and object information. Tools should call it when the project is no longer needed.

### Task Handles

```python
TaskHandle(name="Task", interrupts=True)
handle.stop()
handle.current_jobset()
handle.add_observer(observer)
handle.is_stopped()
handle.get_jobsets()
handle.create_jobset(name="JobSet", count=None)

jobset.started_job(name)
jobset.finished_job()
jobset.check_status()
jobset.get_percent_done()
jobset.increment()
jobset.name
jobset.job_name
```

Long-running operations accept `task_handle` as a keyword argument, normally as the last parameter. Observers are zero-argument callables notified when a task is stopped or a job finishes. Calling `stop()` on an interrupting handle causes later job status checks to raise `InterruptedTaskError`.

### Object Analysis

Every `Project` has a `pycore` object. The most useful public methods are:

```python
project.pycore.is_python_file(resource)
project.pycore.resource_to_pyobject(resource, force_errors=False)
project.pycore.run_module(resource, args=None, stdin=None, stdout=None)
project.pycore.analyze_module(
    resource,
    should_analyze=lambda py: True,
    search_subscopes=lambda py: True,
    followed_calls=None,
)
```

Static object analysis records function-call and assignment information so later inference, code assist, and some refactorings can be more accurate. `run_module()` runs a module and returns a runner object; when `perform_doa` is enabled, dynamic object information is collected during the run. `analyze_module()` forces static analysis for one Python resource and may follow calls up to `followed_calls`, defaulting to the `soa_followed_calls` preference.

### Refactoring Lifecycle

Refactorings follow the same lifecycle:

1. Construct the refactoring with a `Project`, a `Resource`, and offsets or options identifying the selected Python element.
2. Optionally query the refactoring for information such as the old name or argument list.
3. Call `get_changes(...)` with the user-selected options.
4. Preview or apply the returned `Change` through `Project.do()`.

Offsets are Python string offsets into the current source text. Rope treats DOS newlines and multi-byte characters as one character when callers compute offsets in normal Python strings.

Most project-wide refactorings accept `resources=None`. `None` means all Python files returned by `project.get_python_files()`. Passing a list of `File` resources limits analysis and edits to that list. If a selected name is local, rope narrows some refactorings to the defining resource even when no resource list is provided.

### Rename

```python
Rename(project, resource, offset=None)
renamer.get_old_name()
renamer.get_changes(
    new_name,
    in_file=None,
    in_hierarchy=False,
    unsure=None,
    docs=False,
    resources=None,
    task_handle=DEFAULT_TASK_HANDLE,
)
renamer.validate_changes(new_name)
renamer.is_method()

ChangeOccurrences(project, resource, offset)
changer.get_old_name()
changer.get_changes(new_name, only_calls=False, reads=True, writes=True)
```

`Rename` can rename classes, functions, modules, packages, methods, variables, and keyword parameters. If `offset` is `None`, the resource itself is renamed; a file resource is renamed without its `.py` suffix, and an `__init__.py` resource means its package folder. If an offset does not resolve to a Python identifier, construction raises `RefactoringError`.

`new_name` must not be a Python keyword. For methods, `in_hierarchy=True` renames matching methods in the class hierarchy. `docs=True` also changes visible occurrences in comments, strings, and evaluated strings where the selected name is in scope. `unsure` may be a callable that receives an occurrence and returns whether rope should treat an uncertain occurrence as a match.

When renaming a module or package and the moved resource is within the active resource set, the returned change set includes both source updates and the filesystem move.

`ChangeOccurrences` is a narrower API for replacing occurrences in the scope containing the selected offset. It does not move modules or resources and is useful for custom refactorings.

### Move

```python
create_move(project, resource, offset=None)

MoveMethod(project, resource, offset)
mover.get_method_name()
mover.get_changes(dest_attr, new_name=None, resources=None, task_handle=DEFAULT_TASK_HANDLE)

MoveGlobal(project, resource, offset)
mover.get_changes(dest, resources=None, task_handle=DEFAULT_TASK_HANDLE)

MoveModule(project, resource)
mover.get_changes(dest, resources=None, task_handle=DEFAULT_TASK_HANDLE)
```

`create_move()` chooses `MoveModule`, `MoveGlobal`, or `MoveMethod` from the selected location. It raises `RefactoringError` unless the selection is a module, package, global class/function/variable, or normal method.

`MoveMethod` moves a normal method to the class of one of the original class attributes. `dest_attr` names that destination attribute. The old method remains and calls the new method; callers can inline it afterward if they want call sites rewritten to the destination object. `new_name=None` preserves the old method name.

`MoveGlobal` moves a global class, function, or variable to another module. `dest` may be a destination resource or dotted module name. Moving to a missing destination, a folder destination for non-modules, or the same module raises `RefactoringError`.

`MoveModule` moves a module or package into a package folder. Passing a folder without `__init__.py` as the moved package raises `RefactoringError`; passing a non-folder destination raises `RefactoringError`. Moving a module also converts relative imports in the moving module to absolute imports when necessary.

### Extract and Inline

```python
ExtractMethod(project, resource, start_offset, end_offset)
ExtractVariable(project, resource, start_offset, end_offset)
extractor.get_changes(extracted_name, similar=False, global_=False, kind=None)

create_inline(project, resource, offset)
inliner.get_kind()
InlineMethod.get_changes(remove=True, only_current=False, resources=None, task_handle=DEFAULT_TASK_HANDLE)
InlineVariable.get_changes(remove=True, only_current=False, resources=None, docs=False, task_handle=DEFAULT_TASK_HANDLE)
InlineParameter.get_changes(**change_signature_options)
```

Extract refactorings trim leading and trailing whitespace from the selected region before analyzing it. `similar=True` replaces similar expressions or statements in the same valid search area. `global_=True` places the extracted method or variable at module level.

For `ExtractMethod`, prefixing `extracted_name` with `@` selects a classmethod extraction and prefixing it with `$` selects a staticmethod extraction. The explicit `kind` values are `"function"`, `"method"`, `"staticmethod"`, and `"classmethod"`. If the prefix and `kind` disagree, rope raises `RefactoringError`. `ExtractVariable` always creates a variable.

`create_inline()` chooses an inliner for a method/function, local variable, or parameter. If the selection is not inlineable, it raises `RefactoringError`. `remove=False` leaves the original definition in place. `only_current=True` inlines only the selected occurrence. Variable inlining requires exactly one assignment and raises `RefactoringError` otherwise. Parameter inlining delegates to change-signature behavior by inserting default values at call sites that omit the parameter.

### Change Signature

```python
ChangeSignature(project, resource, offset)
signature.get_args()
signature.is_method()
signature.get_changes(changers, in_hierarchy=False, resources=None, task_handle=DEFAULT_TASK_HANDLE)

ArgumentNormalizer()
ArgumentRemover(index)
ArgumentAdder(index, name, default=None, value=None)
ArgumentDefaultInliner(index)
ArgumentReorderer(new_order, autodef=None)
```

`ChangeSignature` must be constructed on a function or method selection. Constructing it elsewhere raises `RefactoringError`. If the selected object is a class, rope changes its `__init__` signature and updates constructor calls.

`get_args()` returns a list of `(name, default)` pairs for non-star parameters. Missing defaults are represented by `None`.

`ArgumentAdder` inserts `(name, default)` into the definition and, when `value` is not `None`, adds that value at call sites. Adding a duplicate parameter raises `RefactoringError`. `ArgumentDefaultInliner` inserts an existing default at call sites that omit the argument. `ArgumentReorderer.new_order` is the list of old parameter indexes in their new order; changing `f(a, b, c)` to `f(c, a, b)` uses `[2, 0, 1]`. If `autodef` is a string, rope uses it when a non-default argument must be placed after a defaulted one.

### Restructure and Wildcards

```python
Restructure(project, pattern, goal, args=None, imports=None, wildcards=None)
restructuring.get_changes(checks=None, imports=None, resources=None, task_handle=DEFAULT_TASK_HANDLE)
restructuring.make_checks(string_checks)
```

Restructure rewrites matches of a Python code pattern into a goal template. Pattern variables use `${name}`. Matched names are substituted into the goal text. `imports` is a list of import statements to add to changed modules; rope avoids duplicate imports.

`args` maps wildcard names to wildcard arguments. A string argument uses the default wildcard; a tuple can name another wildcard kind. The default wildcard understands comma-separated keys:

```text
name=<dotted name>
type=<dotted type>
object=<dotted object>
instance=<dotted class>
exact
unsure
```

Without `exact`, a wildcard can match any expression at that point. With `exact`, it only matches the exact name form. `type`, `object`, and `instance` checks are resolved through rope's project module model; `instance` also accepts inherited types.

### Other Refactorings

```python
UseFunction(project, resource, offset)
use_function.get_function_name()
use_function.get_changes(resources=None, task_handle=DEFAULT_TASK_HANDLE)
```

`UseFunction` operates on a global function. It replaces matching code with calls to that function, adding imports in other modules when needed. It raises `RefactoringError` for unresolved selections, non-global functions, generator functions, functions with more than one return statement, and functions whose single return is not the last statement.

```python
EncapsulateField(project, resource, offset)
encapsulator.get_field_name()
encapsulator.get_changes(getter=None, setter=None, resources=None, task_handle=DEFAULT_TASK_HANDLE)
```

`EncapsulateField` operates on class attributes. It adds getter and setter methods to the defining class and rewrites reads to `getter()` and writes to `setter(value)`. Default names are `get_<field>` and `set_<field>`. Tuple assignments to the field raise `RefactoringError`.

```python
IntroduceFactory(project, resource, offset)
factory.get_name()
factory.get_changes(factory_name, global_factory=False, resources=None, task_handle=DEFAULT_TASK_HANDLE)
```

`IntroduceFactory` operates on a class. With `global_factory=False`, it adds a static factory method on the class and rewrites constructor calls to use it. With `global_factory=True`, it adds a module-level factory function and rewrites external modules with imports as needed. A global factory for a nested class raises `RefactoringError`.

```python
IntroduceParameter(project, resource, offset)
intro.get_changes(new_parameter)
```

`IntroduceParameter` must be used inside a function. It adds a new parameter whose default value is the selected primary expression and replaces matching references to that same object in the function body with the new parameter name.

```python
LocalToField(project, resource, offset)
local_to_field.get_changes()
```

`LocalToField` converts a local variable of a method into `self.<name>` using the method's first parameter name. It raises `RefactoringError` unless the selected name is a local variable defined in a method.

```python
MethodObject(project, resource, offset)
method_object.get_new_class(name)
method_object.get_changes(classname=None, new_class_name=None)
```

`MethodObject` replaces a function or method body with construction and invocation of a new callable class. Parameters become attributes of the new class. A parameter named `self` is accepted by the generated constructor as `host` and stored as `self.self`.

```python
ModuleToPackage(project, resource)
module_to_package.get_changes()
```

`ModuleToPackage` transforms `module.py` into a package folder with `__init__.py`, converting relative imports in the old module to absolute imports first when needed.

```python
MultiProjectRefactoring(refactoring, projects, addpath=True)
cross = MultiProjectRefactoring(Rename, other_projects)
refactoring = cross(main_project, resource, offset)
refactoring.get_all_changes(*args, **kwargs)
perform(project_changes)
```

The multi-project wrapper applies the same refactoring class or factory across a main project and dependent projects. Other projects receive the main project's source folders on their Python path. `get_all_changes()` returns `(project, changes)` pairs. `perform()` applies each pair by calling `project.do(changes)`.

### Import Utilities

```python
ImportOrganizer(project)
organizer.organize_imports(resource, offset=None)
organizer.expand_star_imports(resource, offset=None)
organizer.froms_to_imports(resource, offset=None)
organizer.relatives_to_absolutes(resource, offset=None)
organizer.handle_long_imports(resource, offset=None)

ImportTools(project)
tools.get_import(resource)
tools.get_from_import(resource, name)
tools.module_imports(module, imports_filter=None)
tools.organize_imports(pymodule, unused=True, duplicates=True, selfs=True, sort=True, import_filter=None)
tools.expand_stars(pymodule, import_filter=None)
tools.froms_to_imports(pymodule, import_filter=None)
tools.relatives_to_absolutes(pymodule, import_filter=None)
tools.sort_imports(pymodule, import_filter=None)
tools.handle_long_imports(pymodule, maxdots=2, maxlength=27, import_filter=None)

get_imports(project, pydefined)
get_module_imports(project, pymodule)
add_import(project, pymodule, module_name, name=None)
```

`ImportOrganizer` methods return a `Change` object when the file changes and `None` when no edit is needed. Passing `offset` limits the command to the import statement covering the offset's line.

`organize_imports()` can remove unused imports, remove duplicates, remove self-imports, split comma imports according to preference, and sort import groups. Sorting follows the visible grouping of future imports, standard imports, third-party imports, project imports, then the rest of the module. `handle_long_imports()` treats imports with more than two dots or more than 27 characters as long by default and rewrites them into a shorter from-import form.

`add_import()` returns `(new_source, imported_name)`. `imported_name` is the expression callers should insert at the use site. The selected import style is controlled by `imports.preferred_import_style`, with `"normal-import"`, `"from-module"`, and `"from-global"` choosing among `import package.module`, `from package import module`, and `from package.module import object` when those forms are applicable.

### Code Assist and Find APIs

```python
codeassist.code_assist(
    project,
    source_code,
    offset,
    resource=None,
    templates=None,
    maxfixes=1,
    later_locals=True,
)
codeassist.sorted_proposals(proposals, scopepref=None, typepref=None)
codeassist.starting_offset(source_code, offset)
codeassist.starting_expression(source_code, offset)
codeassist.get_doc(project, source_code, offset, resource=None, maxfixes=1)
codeassist.get_calltip(
    project,
    source_code,
    offset,
    resource=None,
    maxfixes=1,
    ignore_unknown=False,
    remove_self=False,
)
codeassist.get_definition_location(project, source_code, offset, resource=None, maxfixes=1)
codeassist.get_canonical_path(project, resource, offset)
```

`code_assist()` returns completion proposals. `resource` enables relative import handling. `maxfixes` is the maximum number of syntax errors rope may attempt to repair before analysis. If `later_locals=False`, names defined later in the same scope are omitted.

`CompletionProposal` exposes:

```python
proposal.name
proposal.scope
proposal.type
proposal.parameters
proposal.get_doc()
```

`scope` is one of `"global"`, `"local"`, `"builtin"`, `"attribute"`, `"keyword"`, `"imported"`, or `"parameter_keyword"`. `type` is one of `"instance"`, `"class"`, `"function"`, `"module"`, or `None`. `parameters` is a list of parameter names for function completions and `None` otherwise. `NamedParamProposal.name` includes a trailing `=` and `get_default()` returns the parameter default string or `None`.

`sorted_proposals()` defaults to scope priority `["parameter_keyword", "local", "global", "imported", "attribute", "builtin", "keyword"]` and type priority `["class", "function", "instance", "module", None]`.

`starting_offset()` returns the insertion start for replacing the partial expression before `offset`. `starting_expression()` returns the expression being completed. `get_calltip()` returns a string of the form `module_name.holding_scope_names.function_name(arguments)`; for classes it reports `__init__`, and for callable objects it reports `__call__`. The offset is on the callable name, not after the open parenthesis. `get_definition_location()` returns `(resource, lineno)` or `(None, None)`; if no resource was supplied and the definition is in the same temporary module, the resource part may be `None`. `get_canonical_path()` returns a list of `(name, kind)` tuples from module to nested class/function/parameter or variable.

```python
findit.find_occurrences(project, resource, offset, unsure=False, resources=None, in_hierarchy=False, task_handle=DEFAULT_TASK_HANDLE)
findit.find_implementations(project, resource, offset, resources=None, task_handle=DEFAULT_TASK_HANDLE)
findit.find_definition(project, code, offset, resource=None, maxfixes=1)

Location.resource
Location.region
Location.offset
Location.unsure
Location.lineno
```

`find_occurrences()` returns all matching locations for the selected name. With `unsure=True`, possible matches are included and marked through `Location.unsure`. `find_implementations()` operates on methods and raises `BadIdentifierError` if the selected identifier cannot be resolved or is not a method. `find_definition()` returns a `Location` or `None`.

### Generation and Other Contrib Helpers

```python
generate.create_module(project, name, sourcefolder=None)
generate.create_package(project, name, sourcefolder=None)
generate.create_generate(kind, project, resource, offset, goal_resource=None)
```

`create_module()` creates dotted modules under `sourcefolder` or `project.root` and returns the created `File`. Intermediate package folders must already exist. `create_package()` creates the package folder and its `__init__.py`, returning the created `Folder`.

`create_generate()` accepts `"variable"`, `"function"`, `"class"`, `"module"`, or `"package"` and returns a generation refactoring object. These objects provide `get_changes()` and `get_location()`. `get_location()` returns `(resource, lineno)` for the generated element. Generating an element that already exists or whose insertion scope cannot be determined raises `RefactoringError`.

```python
find_errors(project, resource)
Error(lineno, error)
```

`find_errors()` reports possible unresolved variable, defined-later, and unresolved attribute accesses in one Python resource. Each returned `Error` has `lineno` and `error` fields and stringifies as `"<lineno>: <message>"`.

```python
FixModuleNames(project).get_changes(fixer=str.lower, task_handle=DEFAULT_TASK_HANDLE)
```

`FixModuleNames` repeatedly applies module rename refactorings and returns one merged change set. `fixer` receives a module basename and returns the desired basename.

```python
ChangeStack(project, description="merged changes")
stack.push(changes)
stack.pop_all()
stack.merged()
```

`ChangeStack` lets callers perform several dependent changes temporarily, undo them, and return one merged `ChangeSet` containing the basic changes in push order.

### Auto-Import

```python
AutoImport(project, observe=True, underlined=False)
autoimport.import_assist(starting)
autoimport.get_modules(name)
autoimport.get_all_names()
autoimport.get_name_locations(name)
autoimport.generate_cache(resources=None, underlined=None, task_handle=DEFAULT_TASK_HANDLE)
autoimport.generate_modules_cache(modules, underlined=None, task_handle=DEFAULT_TASK_HANDLE)
autoimport.update_resource(resource, underlined=None)
autoimport.update_module(modname, underlined=None)
autoimport.clear_cache()
autoimport.find_insertion_line(code)
```

The package-level `AutoImport` keeps a cache of global names by module. Its cache can be inaccurate or stale until regenerated. With `observe=True`, it listens for project resource changes and updates cached project modules. With `underlined=False`, names beginning with `_` are omitted from the cache. `import_assist()` returns `(name, module)` tuples for names starting with the prefix. `get_modules()` returns modules that provide an exact global name. `get_name_locations()` returns `(resource, lineno)` tuples where a cached name is defined.

```python
SqliteAutoImport(project, observe=True, underlined=False, memory=...)
SqliteAutoImport.create_database_connection(project=None, memory=False)
sqlite_autoimport.import_assist(starting)
sqlite_autoimport.search(name, exact_match=False)
sqlite_autoimport.search_full(name, exact_match=False, ignored_names=None)
sqlite_autoimport.generate_cache(resources=None, underlined=False, task_handle=DEFAULT_TASK_HANDLE)
sqlite_autoimport.generate_modules_cache(modules=None, task_handle=DEFAULT_TASK_HANDLE, single_thread=False, underlined=None)
sqlite_autoimport.update_module(module)
sqlite_autoimport.update_resource(resource, underlined=False, commit=True)
sqlite_autoimport.close()
```

The sqlite implementation can store its database in memory or under the rope folder. If `memory=False`, a project is required. If memory storage is used, connections are created with a shared in-memory sqlite URI so the same auto-import object can be used across threads. Call `close()` when done; it commits and closes the connection.

`search()` returns sorted, deduplicated `(import_statement, import_name)` tuples for both module names and importable names. `search_full()` yields unique `SearchResult(import_statement, name, source, itemkind)` records and can ignore names in `ignored_names`. `generate_cache()` indexes project resources. `generate_modules_cache()` indexes external modules; with `modules=None`, it scans available modules on `sys.path` and configured Python folders. Use `generate_cache()` for internal project names rather than external module indexing.

## Behavioral Sections

### Project Configuration and Ignored Resources

Ignored resources are not returned by `Project.get_files()`, are not committed through VCS commands, and do not make a history item interesting. Default ignored patterns include the rope folder, common VCS directories, common virtual environments, bytecode files, and common tool caches. Pattern matching uses `/` as the separator; `*` and `?` do not cross slashes, and `//` allows matching across any number of path segments. Symbolic links are treated as ignored resources.

`python_files` controls which files rope treats as Python files. By default only `*.py` files are Python files. `source_folders` are project-root-relative paths using `/` on every platform. `python_path` extends lookup for modules outside project source folders. `extension_modules` and `import_dynload_stdmods` control which built-in or C extension modules rope is allowed to inspect.

### Object Information and Persistence

The rope folder may store configuration, history, object information, and auto-import data. `save_history` controls whether undo/redo history is written across sessions. `max_history_items` controls how many undo entries are retained. `save_objectdb`, `automatic_soa`, `soa_followed_calls`, `perform_doa`, and `validate_objectdb` control object inference persistence and analysis behavior.

Static object analysis is recommended before large refactorings when more accurate inference is useful. Dynamic object analysis can improve inference after running modules but slows execution while information is collected.

### Filesystem Commands

`Project(..., fscommands=...)` accepts an object implementing:

```python
create_file(path)
create_folder(path)
move(path, new_location)
remove(path)
write(path, data)
read(path)
```

Rope uses this interface for all filesystem changes performed through changes. If no `fscommands` is supplied, rope detects common VCS folders and uses the corresponding command adapter when available; otherwise it uses direct filesystem operations. Rope does not commit to version control; it only uses VCS-aware file operations for adds, moves, and removes.

## Error Semantics

All rope-specific exceptions inherit from `RopeError`.

- `ResourceNotFoundError`: raised when a requested existing resource or parent folder cannot be found.
- `RefactoringError`: raised when a selected location or requested refactoring option is invalid for that refactoring.
- `InterruptedTaskError`: raised from task job status checks after an interrupting `TaskHandle` is stopped.
- `HistoryError`: raised for invalid undo/redo operations, including undo with an empty undo list, redo with an empty redo list, and undoing a content change that has not been performed.
- `ModuleNotFoundError`: raised when a requested module cannot be found.
- `AttributeNotFoundError`, `NameNotFoundError`, and `BadIdentifierError`: raised when name or attribute resolution fails in APIs that require a resolvable Python object.
- `ModuleSyntaxError(filename, lineno, message)`: raised for syntax errors when syntax errors are not being ignored or when string parsing is forced to report them. The object exposes `filename`, `lineno`, and `message_`.
- `ModuleDecodeError(filename, message)`: raised when a file cannot be decoded. The object exposes `filename` and `message_`.

Refactoring constructors validate the selected element early when possible. `get_changes()` validates user-provided options such as names, destinations, resources, and incompatible extraction kinds. APIs that return optional query answers use `None` or `(None, None)` where documented rather than raising for ordinary "not found" results.

## Cross-View Invariants

1. A `Resource.path` is always the project-root-relative slash path, while `Resource.real_path` is the absolute filesystem path. Any API that returns a resource must preserve that distinction.
2. A `Change` preview and a committed `Project.do()` operation describe the same resource set: every resource that will need editor reload after commit appears in `get_changed_resources()`.
3. Source refactorings and filesystem refactorings are one logical change set. Renaming or moving a module updates import/use sites and moves the resource only when the moved resource is inside the active resource set.
4. History only reflects changes applied through rope. Manual filesystem edits require `Project.validate()` or `libutils.report_change()` before later refactorings can rely on fresh caches.
5. The rope folder is project data, not project source. It may affect configuration, history, object information, and auto-import, but it is ignored as a normal project resource by default.
6. `resources=None` means all Python files in the project view; a concrete resource list limits both analysis and edits, except where a local selection necessarily restricts the operation to its defining resource.
7. `task_handle` cancellation is cooperative. Long operations report jobs through job sets and raise `InterruptedTaskError` only when they check the handle status.
8. Code-assist offsets, refactoring offsets, and returned location regions are offsets into the exact Python source string the caller supplied or read from the `Resource`.
9. Auto-import search results are cache views. Updating project files, module caches, or aliases does not change source text until the caller inserts an import or applies a returned change.
10. Import-adding helpers and refactorings must keep the inserted reference expression consistent with the import style they chose; the source edit and the returned or substituted expression are one contract.

## Representative Workflow(s)

### Rename a Symbol and Keep the Editor in Sync

```python
from rope.base.project import Project
from rope.base import libutils
from rope.refactor.rename import Rename

project = Project("/path/to/workspace")
try:
    resource = libutils.path_to_resource(project, "/path/to/workspace/pkg/mod.py")
    source = resource.read()
    offset = source.index("old_name")

    renamer = Rename(project, resource, offset)
    assert renamer.get_old_name() == "old_name"

    changes = renamer.get_changes("new_name", docs=True)
    preview = changes.get_description()
    changed_resources = changes.get_changed_resources()

    project.do(changes)

    for changed in changed_resources:
        reloaded_text = changed.read()

    project.history.undo()
    project.history.redo()
finally:
    project.close()
```

This workflow opens a project, converts a filesystem path to a rope resource, computes a project-wide rename, previews it, applies it through history, reloads affected resources, and closes the project so persisted rope data is flushed.

### Complete a Name and Insert the Selected Proposal

```python
from rope.base.project import Project
from rope.contrib import codeassist

project = Project("/path/to/workspace")
try:
    resource = project.get_resource("pkg/mod.py")
    source = resource.read()
    offset = source.index("partial") + len("partial")

    proposals = codeassist.code_assist(project, source, offset, resource=resource)
    proposals = codeassist.sorted_proposals(proposals)
    start = codeassist.starting_offset(source, offset)

    proposal = proposals[0]
    new_source = source[:start] + proposal.name + source[offset:]
finally:
    project.close()
```

The completion proposal supplies the replacement text through `proposal.name`; the insertion range starts at `starting_offset()` and ends at the original completion offset.

## Non-Goals

- Rope does not provide a required CLI surface.
- Rope does not guarantee perfect Python type inference; object information is best-effort and may improve after static or dynamic analysis.
- Rope does not modify files outside the project passed to a refactoring, except through explicit multi-project workflows where each project receives its own change set.
- Rope does not commit version-control changes; it only uses VCS-aware filesystem commands for file operations when available.
- Rope does not automatically know about editor-side unsaved buffers. Editors must pass current source strings to query APIs and report or validate external saves before refactoring.
- Rope does not promise that auto-import caches are complete or current without explicit cache generation or update calls.
- Rope does not undo resource removals through history.
- Rope does not treat every importable module path under `rope` as stable public API; the supported surface is the documented and exported library API described here.

## Evaluation Notes

Evaluation should exercise public behavior through the documented import paths and should score both source-level results and object-level API contracts. Useful dimensions include project creation and configuration precedence, resource path behavior, change previews and application, history undo/redo, task-handle cancellation, refactoring outputs, import organization, static-analysis-assisted behavior, code-assist query results, find/query location objects, generation helpers, and auto-import cache/search behavior.

Scoring should compare user-observable results: returned object types and fields, changed source text, changed resources, filesystem state inside the project, exception classes for invalid operations, and persisted rope-folder effects where persistence is part of the public contract. Tests should not depend on private helper names, undocumented module internals, or a particular internal algorithm for finding or applying edits.
