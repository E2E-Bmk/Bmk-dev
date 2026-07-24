# Spec2Repo oracle - integration tests for griffe-apimodel-fullrepro-001

from __future__ import annotations
import io
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
import griffe
import griffecli
from griffe import Alias, AliasResolutionError, Attribute, Class, CyclicAliasError, Docstring, DocstringSectionParameters, DocstringSectionRaises, DocstringSectionReturns, Extension, ExtensionError, ExtensionNotLoadedError, Function, GriffeLoader, Kind, Module, ModulesCollection, Parameter, ParameterKind, Parameters, Parser, TypeAlias, dump, load, load_extensions, main, parse_auto, parse_google, parse_numpy, parse_sphinx, visit
from textwrap import dedent
from griffe import Breakage, BreakageKind, DataclassesExtension, Docstring, Function, Module, Object, Parameter, ParameterKind, Parameters, Parser, UnpackTypedDictExtension, find_breaking_changes, load, load_extensions, main, parse, visit

def write_package(root: Path, name: str, files: dict[str, str]) -> Path:
    package = root / name
    package.mkdir()
    for relative, content in files.items():
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')
    return package

def init_git_repository(repository: Path) -> None:
    commands = (['git', 'init'], ['git', 'config', 'user.email', 'track-b@example.invalid'], ['git', 'config', 'user.name', 'Track B'], ['git', 'add', '.'], ['git', 'commit', '-m', 'initial'])
    for command in commands:
        subprocess.run(command, cwd=repository, check=True, capture_output=True, text=True)

class AddMarker(Extension):

    def on_package(self, *, pkg, loader, **kwargs):
        added = pkg['x']
        added.name = 'added'
        added.value = '7'
        pkg.set_member('added', added)
        del pkg['x']

def _visit(code: str, *, name: str='module', extensions=None, docstring_parser=None) -> Module:
    return visit(name, Path(f'{name}.py'), dedent(code), extensions=extensions, docstring_parser=docstring_parser)

def _load_package(tmp_path: Path, code: str, *, extensions=None, docstring_parser=None) -> Module:
    package = tmp_path / 'pkg'
    package.mkdir()
    package.joinpath('__init__.py').write_text(dedent(code), encoding='utf-8')
    return load(package, extensions=extensions, docstring_parser=docstring_parser)

def _dataclass_module(tmp_path: Path, code: str) -> Module:
    return _load_package(tmp_path, code, extensions=load_extensions(DataclassesExtension()))

def test_minimal_and_full_json_preserve_core_fields_and_json_options(tmp_path: Path):
    write_package(tmp_path, 'serpkg', {'__init__.py': 'VALUE: int = 3\n'})
    module = load('serpkg', search_paths=[tmp_path])
    minimal_json = module.as_json(sort_keys=True)
    full_json = module.as_json(full=True, sort_keys=True)
    minimal = Module.from_json(minimal_json)
    full = Module.from_json(full_json)
    assert minimal.name == full.name == 'serpkg'
    assert minimal.kind is full.kind is Kind.MODULE
    assert set(minimal.members) == set(full.members) == {'VALUE'}
    assert minimal['VALUE'].value == full['VALUE'].value == module['VALUE'].value
    assert module.as_json(indent=2).startswith('{\n  ')

def test_minimal_json_round_trip_preserves_navigation_and_annotations(tmp_path: Path):
    write_package(tmp_path, 'roundpkg', {'__init__.py': 'from .mod import C\n', 'mod.py': 'class C:\n    def f(self, x: int = 1) -> str:\n        """Doc."""\n        return str(x)\n'})
    module = load('roundpkg', search_paths=[tmp_path])
    clone = Module.from_json(module.as_json())
    function = clone['mod.C.f']
    assert function.path == 'roundpkg.mod.C.f'
    assert [parameter.name for parameter in function.parameters] == ['self', 'x']
    assert str(function.parameters['x'].annotation) == 'int'
    assert str(function.returns) == 'str'
    assert function.docstring.value == 'Doc.'

def test_dotted_load_returns_object_from_containing_package_graph(tmp_path: Path):
    write_package(tmp_path, 'nestedpkg', {'__init__.py': 'from .mod import C\n', 'mod.py': 'class C:\n    def method(self):\n        return 1\n'})
    method = load('nestedpkg.mod.C.method', search_paths=[tmp_path])
    top = method
    while top.parent is not None:
        top = top.parent
    assert method.path == 'nestedpkg.mod.C.method'
    assert top.path == 'nestedpkg'
    assert top['mod.C.method'] is method
    assert method.analysis == 'static'

def test_static_and_forced_dynamic_loading_report_analysis_and_compatible_kinds(tmp_path: Path):
    write_package(tmp_path, 'analysispkg', {'__init__.py': 'VALUE = 3\nclass C:\n    pass\n'})
    static = load('analysispkg', search_paths=[tmp_path])
    dynamic = load('analysispkg', search_paths=[tmp_path], force_inspection=True)
    assert static.analysis == 'static'
    assert dynamic.analysis == 'dynamic'
    assert static['VALUE'].kind is dynamic['VALUE'].kind is Kind.ATTRIBUTE
    assert static['C'].kind is dynamic['C'].kind is Kind.CLASS

def test_visit_builds_static_semantic_graph(tmp_path: Path):
    source = '"""Module docs."""\nVALUE: int = 3\nclass C:\n    def method(self, x: int = 2, *, flag: bool = False) -> str:\n        """Summary."""\n        return str(x)\n'
    filepath = tmp_path / 'mod.py'
    filepath.write_text(source, encoding='utf-8')
    module = visit('visitpkg.mod', filepath, source)
    method = module['C.method']
    assert module.analysis == 'static'
    assert sorted(module.members) == ['C', 'VALUE']
    assert method.parent.path == 'visitpkg.mod.C'
    assert [parameter.name for parameter in method.parameters] == ['self', 'x', 'flag']
    assert str(method.returns) == 'str'
    assert method.docstring.value == 'Summary.'

def test_reused_loader_shares_collection_and_resolves_cross_package_alias(tmp_path: Path):
    write_package(tmp_path, 'provider', {'__init__.py': 'class Thing:\n    pass\n'})
    write_package(tmp_path, 'consumer', {'__init__.py': 'from provider import Thing\n'})
    loader = GriffeLoader(search_paths=[tmp_path])
    consumer = loader.load('consumer')
    alias = consumer['Thing']
    provider = loader.load('provider')
    assert alias.resolved is False
    assert consumer.modules_collection is loader.modules_collection
    assert provider.modules_collection is loader.modules_collection
    assert loader.modules_collection['provider'] is provider
    assert alias.canonical_path == 'provider.Thing'
    assert alias.resolved is True

def test_static_load_and_visit_agree_on_declared_semantics(tmp_path: Path):
    source = 'VALUE: int = 3\nclass C:\n    def method(self, x: int = 2) -> str:\n        """Summary."""\n        return str(x)\n'
    package = write_package(tmp_path, 'agreepkg', {'__init__.py': source})
    loaded = load('agreepkg', search_paths=[tmp_path])
    direct = visit('agreepkg', package / '__init__.py', source)
    assert sorted(loaded.members) == sorted(direct.members) == ['C', 'VALUE']
    assert loaded['VALUE'].kind is direct['VALUE'].kind is Kind.ATTRIBUTE
    assert loaded['C.method'].path == direct['C.method'].path == 'agreepkg.C.method'
    assert [p.name for p in loaded['C.method'].parameters] == [p.name for p in direct['C.method'].parameters]
    assert str(loaded['C.method'].returns) == str(direct['C.method'].returns) == 'str'
    assert loaded['C.method'].docstring.value == direct['C.method'].docstring.value == 'Summary.'

def test_minimal_and_full_views_and_round_trip_preserve_semantic_core(tmp_path: Path):
    write_package(tmp_path, 'viewpkg', {'__init__.py': 'from .mod import C\n', 'mod.py': 'class C:\n    def f(self, x: int = 1) -> str:\n        return str(x)\n'})
    module = load('viewpkg', search_paths=[tmp_path])
    minimal = Module.from_json(module.as_json())
    full = Module.from_json(module.as_json(full=True))
    clone = Module.from_json(module.as_json())
    assert minimal.name == full.name == clone.name == 'viewpkg'
    assert minimal.kind is full.kind is clone.kind is Kind.MODULE
    assert set(minimal.members) == set(full.members) == set(clone.members) == {'C', 'mod'}
    assert clone['mod.C.f'].path == 'viewpkg.mod.C.f'
    assert [p.name for p in clone['mod.C.f'].parameters] == ['self', 'x']

def test_loading_docstring_parser_matches_direct_parse(tmp_path: Path):
    write_package(tmp_path, 'docpkg', {'__init__.py': 'def f(x: int) -> str:\n    """Summary.\n\n    Args:\n        x: number\n\n    Returns:\n        result\n    """\n    return str(x)\n'})
    function = load('docpkg.f', search_paths=[tmp_path], docstring_parser=Parser.google)
    loaded_sections = function.docstring.parsed
    direct_sections = parse_google(function.docstring, warnings=False)
    assert [section.kind.value for section in loaded_sections] == [section.kind.value for section in direct_sections] == ['text', 'parameters', 'returns']
    loaded_parameter = next((s for s in loaded_sections if isinstance(s, DocstringSectionParameters))).value[0]
    direct_parameter = next((s for s in direct_sections if isinstance(s, DocstringSectionParameters))).value[0]
    assert (loaded_parameter.name, str(loaded_parameter.annotation), loaded_parameter.description) == (direct_parameter.name, str(direct_parameter.annotation), direct_parameter.description) == ('x', 'int', 'number')

def test_extension_mutation_reaches_graph_and_json(tmp_path: Path):
    write_package(tmp_path, 'extpkg', {'__init__.py': 'x = 1\n'})
    loaded = load('extpkg', search_paths=[tmp_path], extensions=load_extensions(AddMarker()))
    clone = Module.from_json(loaded.as_json())
    assert loaded.members['added'] is loaded['added']
    assert loaded['added'].parent is loaded
    assert clone['added'].value == loaded['added'].value == '7'

def test_extension_mutation_reaches_callable_dump(tmp_path: Path):
    write_package(tmp_path, 'extpkg', {'__init__.py': 'x = 1\n'})
    stream = io.StringIO()
    result = dump(['extpkg'], output=stream, search_paths=[tmp_path], extensions=[AddMarker()])
    dumped = Module.from_json(json.dumps(json.loads(stream.getvalue())['extpkg']))
    assert result == 0
    assert dumped['added'].value == '7'

def test_callable_dump_combines_packages_and_template_outputs(tmp_path: Path):
    write_package(tmp_path, 'p1', {'__init__.py': 'VALUE = 1\n'})
    write_package(tmp_path, 'p2', {'__init__.py': 'VALUE = 2\n'})
    stream = io.StringIO()
    result = dump(['p1', 'p2'], output=stream, search_paths=[tmp_path])
    combined = json.loads(stream.getvalue())
    template = str(tmp_path / '{package}.json')
    template_result = dump(['p1', 'p2'], output=template, search_paths=[tmp_path])
    assert result == 0
    assert sorted(combined) == ['p1', 'p2']
    assert [Module.from_json(json.dumps(combined[name])).name for name in sorted(combined)] == ['p1', 'p2']
    assert template_result == 0
    assert Module.from_json((tmp_path / 'p1.json').read_text(encoding='utf-8')).name == 'p1'
    assert Module.from_json((tmp_path / 'p2.json').read_text(encoding='utf-8')).name == 'p2'

def test_main_dispatches_dump_and_reports_invalid_syntax(tmp_path: Path):
    write_package(tmp_path, 'mainpkg', {'__init__.py': 'VALUE = 1\n'})
    output = tmp_path / 'main.json'
    result = main(['dump', 'mainpkg', '--search', str(tmp_path), '--output', str(output)])
    assert result == 0
    dumped = json.loads(output.read_text(encoding='utf-8'))['mainpkg']
    assert Module.from_json(json.dumps(dumped)).name == 'mainpkg'
    try:
        invalid_result = main(['not-a-command'])
    except SystemExit as caught:
        invalid_result = caught.code
    assert isinstance(invalid_result, int)
    assert invalid_result != 0

def test_python_m_griffe_dumps_local_package(tmp_path: Path):
    write_package(tmp_path, 'modulepkg', {'__init__.py': 'VALUE = 1\n'})
    completed = subprocess.run([sys.executable, '-m', 'griffe', 'dump', 'modulepkg', '--search', str(tmp_path)], check=False, capture_output=True, text=True, env=os.environ.copy())
    assert completed.returncode == 0
    dumped = json.loads(completed.stdout)['modulepkg']
    assert Module.from_json(json.dumps(dumped)).name == 'modulepkg'

def test_local_git_check_returns_zero_then_one_for_known_breakage(tmp_path: Path, monkeypatch):
    new_repository = tmp_path / 'new'
    old_repository = tmp_path / 'old'
    new_repository.mkdir()
    old_repository.mkdir()
    new_package = write_package(new_repository, 'cpkg', {'__init__.py': 'def f(x=1):\n    return x\n'})
    old_package = write_package(old_repository, 'cpkg', {'__init__.py': 'def f(x=1):\n    return x\n'})
    init_git_repository(new_repository)
    init_git_repository(old_repository)
    monkeypatch.chdir(new_repository)
    assert griffe.check('cpkg', against='HEAD', against_path=old_package) == 0
    (new_package / '__init__.py').write_text('def f(x):\n    return x\n', encoding='utf-8')
    assert griffe.check('cpkg', against='HEAD', against_path=old_package) == 1

@pytest.mark.parametrize(('old_code', 'new_code', 'expected_breakages'), [('a = True', 'a = False', [BreakageKind.ATTRIBUTE_CHANGED_VALUE]), ('class a(int, str): ...', 'class a(int): ...', [BreakageKind.CLASS_REMOVED_BASE]), ('a = 0', 'class a: ...', [BreakageKind.OBJECT_CHANGED_KIND]), ('a = True', '', [BreakageKind.OBJECT_REMOVED]), ('def a(): ...', 'def a(x): ...', [BreakageKind.PARAMETER_ADDED_REQUIRED]), ('def a(x=0): ...', 'def a(x=1): ...', [BreakageKind.PARAMETER_CHANGED_DEFAULT]), ('def a(x, /): ...', 'def a(*, x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(*, x): ...', 'def a(x, /): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(x): ...', 'def a(x, /): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(x): ...', 'def a(*, x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(x, /): ...', 'def a(*x): ...', []), ('def a(x): ...', 'def a(*x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(*, x): ...', 'def a(*x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(**x): ...', 'def a(*x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(x): ...', 'def a(*x, **y): ...', []), ('def a(*, x): ...', 'def a(*x, **y): ...', []), ('def a(x, /): ...', 'def a(**x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(x): ...', 'def a(**x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(*, x): ...', 'def a(**x): ...', []), ('def a(*x): ...', 'def a(**x): ...', [BreakageKind.PARAMETER_CHANGED_KIND]), ('def a(x, /): ...', 'def a(*y, **x): ...', []), ('def a(x): ...', 'def a(*y, **x): ...', []), ('def a(x=1): ...', 'def a(x): ...', [BreakageKind.PARAMETER_CHANGED_REQUIRED]), ('def a(x, y): ...', 'def a(y, x): ...', [BreakageKind.PARAMETER_MOVED, BreakageKind.PARAMETER_MOVED]), ('def a(x, y): ...', 'def a(x): ...', [BreakageKind.PARAMETER_REMOVED]), ('class a:\n    b: int | None = None', 'class a:\n    b: int', [BreakageKind.ATTRIBUTE_CHANGED_VALUE]), ('def a() -> int: ...', 'def a() -> str: ...', [])])
def test_diff_griffe(old_code: str, new_code: str, expected_breakages: list[Breakage]) -> None:
    old_module = _visit(old_code, name='old_module')
    new_module = _visit(new_code, name='new_module')
    breaking = list(find_breaking_changes(old_module, new_module))
    assert [item.kind for item in breaking] == expected_breakages

def test_moving_members_in_parent_classes(tmp_path: Path) -> None:
    old_package = tmp_path / 'old' / 'module'
    new_package = tmp_path / 'new' / 'module'
    old_package.mkdir(parents=True)
    new_package.mkdir(parents=True)
    old_package.joinpath('__init__.py').write_text(dedent('\n            class Parent:\n                ...\n\n            class Base(Parent):\n                def method(self):\n                    ...\n            '), encoding='utf-8')
    new_package.joinpath('__init__.py').write_text(dedent('\n            class Parent:\n                def method(self):\n                    ...\n\n            class Base(Parent):\n                ...\n            '), encoding='utf-8')
    old_module = load(old_package)
    new_module = load(new_package)
    assert not list(find_breaking_changes(old_module, new_module))

def test_minimal_data_is_enough() -> None:
    module = _visit('\n        VALUE: int = 1\n\n        class Service:\n            def run(self, item: str = "x") -> bool:\n                return True\n        ')
    minimal = module.as_json(full=False, indent=2, sort_keys=True)
    reloaded = Module.from_json(minimal)
    assert reloaded.name == module.name == 'module'
    assert set(reloaded.members) == set(module.members) == {'VALUE', 'Service'}
    assert reloaded['VALUE'].kind is module['VALUE'].kind
    assert reloaded['Service.run'].path == module['Service.run'].path
    assert [parameter.name for parameter in reloaded['Service.run'].parameters] == ['self', 'item']
    original_default = module['Service.run'].parameters['item'].default
    assert Object.from_json(minimal)['Service.run'].parameters['item'].default == original_default

def test_dataclass_support(tmp_path: Path) -> None:
    pkg = _dataclass_module(tmp_path, "\n        from dataclasses import dataclass\n\n        @dataclass\n        class Point:\n            x: int\n            '''Docstring for x.'''\n            y: int\n            '''Docstring for y.'''\n        ")
    init = pkg['Point.__init__']
    assert [param.name for param in init.parameters] == ['self', 'x', 'y']
    assert str(init.parameters['x'].annotation) == 'int'

def test_non_init_fields(tmp_path: Path) -> None:
    pkg = _dataclass_module(tmp_path, '\n        from dataclasses import dataclass, field\n\n        @dataclass\n        class Point:\n            x: int\n            y: int = field(init=False)\n        ')
    assert [param.name for param in pkg['Point.__init__'].parameters] == ['self', 'x']

def test_classvar_fields(tmp_path: Path) -> None:
    pkg = _dataclass_module(tmp_path, '\n        from dataclasses import dataclass\n        from typing import ClassVar\n\n        @dataclass\n        class Point:\n            x: int\n            y: ClassVar[int]\n        ')
    assert [param.name for param in pkg['Point.__init__'].parameters] == ['self', 'x']

def test_kw_only_fields(tmp_path: Path) -> None:
    pkg = _dataclass_module(tmp_path, '\n        from dataclasses import dataclass, field\n\n        @dataclass\n        class Point:\n            x: int\n            y: int = field(kw_only=True)\n        ')
    assert pkg['Point.__init__'].parameters['y'].kind is ParameterKind('keyword-only')

def test_kw_only_sentinel(tmp_path: Path) -> None:
    pkg = _dataclass_module(tmp_path, '\n        from dataclasses import KW_ONLY, dataclass\n\n        @dataclass\n        class Point:\n            x: int\n            _: KW_ONLY\n            y: int\n        ')
    assert pkg['Point.__init__'].parameters['y'].kind is ParameterKind('keyword-only')

def test_all_kw_only_fields(tmp_path: Path) -> None:
    pkg = _dataclass_module(tmp_path, '\n        from dataclasses import dataclass\n\n        @dataclass(kw_only=True)\n        class Point:\n            x: int\n            y: int\n        ')
    init = pkg['Point.__init__']
    assert init.parameters['x'].kind is ParameterKind('keyword-only')
    assert init.parameters['y'].kind is ParameterKind('keyword-only')

def test_unpack_support(tmp_path: Path) -> None:
    pkg = _load_package(tmp_path, "\n        from typing import TypedDict, Unpack\n\n        class Kwargs(TypedDict):\n            a: int\n            '''Docstring for a.'''\n            b: str\n            '''Docstring for b.'''\n\n        def func(**kwargs: Unpack[Kwargs]) -> None:\n            '''A function.\n\n            Parameters:\n                **kwargs: The keyword arguments.\n            '''\n        ", extensions=load_extensions(UnpackTypedDictExtension()), docstring_parser='google')
    func = pkg['func']
    assert [param.name for param in func.parameters] == ['a', 'b']
    assert str(func.parameters['a'].annotation) == 'int'

def test_main(tmp_path: Path) -> None:
    package = tmp_path / 'sample_pkg'
    package.mkdir()
    package.joinpath('__init__.py').write_text('VALUE = 1\n', encoding='utf-8')
    output = tmp_path / 'dump.json'
    assert main(['dump', str(package), '--output', str(output)]) == 0
    data = json.loads(output.read_text(encoding='utf-8'))
    assert data['sample_pkg']['name'] == 'sample_pkg'
