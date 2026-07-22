# Spec2Repo oracle - atomic tests for griffe-apimodel-fullrepro-001

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

def test_griffe_exports_primary_public_surface():
    expected = {'Module', 'Class', 'Function', 'Attribute', 'TypeAlias', 'Alias', 'Parameter', 'Parameters', 'ModulesCollection', 'Docstring', 'GriffeLoader', 'load', 'visit', 'inspect', 'JSONEncoder', 'json_decoder', 'parse_auto', 'infer_docstring_style', 'dump', 'check', 'main', 'get_parser'}
    assert all((hasattr(griffe, name) for name in expected))

def test_griffecli_exports_callable_cli_surface():
    names = ('get_parser', 'dump', 'check', 'main')
    assert all((callable(getattr(griffecli, name)) for name in names))
    assert all((callable(getattr(griffe, name)) for name in names))

def test_public_enums_expose_documented_semantic_values():
    assert {'module', 'class', 'function', 'attribute', 'alias', 'type alias'} <= {member.value for member in Kind}
    assert {'positional-only', 'positional or keyword', 'variadic positional', 'keyword-only', 'variadic keyword'} <= {member.value for member in ParameterKind}
    assert {'auto', 'google', 'numpy', 'sphinx'} <= {member.value for member in Parser}
    assert Module('pkg').kind.value == 'module'

def test_member_assignment_establishes_graph_relationships():
    module = Module('pkg')
    cls = Class('C')
    function = Function('f')
    module['C'] = cls
    cls.set_member('f', function)
    assert function.parent is cls
    assert function.path == 'pkg.C.f'
    assert module.members['C'] is cls
    assert module['C.f'] is function

def test_resolved_alias_keeps_import_path_and_exposes_target_metadata():
    modules = ModulesCollection()
    target = Module('target')
    target['Thing'] = Class('Thing')
    holder = Module('holder')
    holder['Imported'] = Alias('Imported', 'target.Thing')
    modules['target'] = target
    modules['holder'] = holder
    alias = holder['Imported']
    alias.resolve_target()
    assert alias.path == 'holder.Imported'
    assert alias.target_path == 'target.Thing'
    assert alias.canonical_path == 'target.Thing'
    assert alias.kind is Kind.CLASS
    assert alias.is_class is True

def test_primary_model_kinds_and_predicates():
    objects = (Module('m'), Class('C'), Function('f', parameters=Parameters(Parameter('x')), returns='str'), Attribute('value', value='1', annotation='int'), TypeAlias('T', value='list[int]'))
    assert [obj.kind.value for obj in objects] == ['module', 'class', 'function', 'attribute', 'type alias']
    assert [objects[0].is_module, objects[1].is_class, objects[2].is_function, objects[3].is_attribute, objects[4].is_type_alias] == [True, True, True, True, True]

def test_item_access_accepts_name_dotted_and_tuple_paths():
    module = Module('pkg')
    module['C'] = Class('C')
    module['C']['f'] = Function('f')
    function = module['C.f']
    assert module['C', 'f'] is function
    assert module['C']['f'] is function
    assert module['C.f'] is function

def test_parameters_are_ordered_mutable_and_name_addressable():
    parameters = Parameters(Parameter('a'), Parameter('args', kind=ParameterKind('variadic positional')), Parameter('kwargs', kind=ParameterKind('variadic keyword')))
    assert len(parameters) == 3
    assert [parameter.name for parameter in parameters] == ['a', 'args', 'kwargs']
    assert parameters[0] is parameters['a']
    assert parameters['*args'].name == 'args'
    assert parameters['**kwargs'].name == 'kwargs'
    parameters['new'] = Parameter('new', default='0')
    parameters['a'] = Parameter('a', default='1')
    parameters[1] = Parameter('rest', kind=ParameterKind('variadic positional'))
    assert [parameter.name for parameter in parameters] == ['a', 'rest', 'kwargs', 'new']
    assert [parameter.required for parameter in parameters] == [False, True, True, False]

def test_visibility_inference_can_be_overridden():
    module = Module('visibility')
    module['shown'] = Attribute('shown')
    module['_hidden'] = Attribute('_hidden')
    module['shown'].public = False
    module['_hidden'].public = True
    assert module['shown'].public is False
    assert module['_hidden'].public is True

def test_alias_resolves_to_available_target():
    modules = ModulesCollection()
    target = Module('target')
    target['Thing'] = Class('Thing')
    holder = Module('holder')
    holder['Imported'] = Alias('Imported', 'target.Thing')
    modules['target'] = target
    modules['holder'] = holder
    alias = holder['Imported']
    assert alias.resolved is False
    alias.resolve_target()
    assert alias.resolved is True
    assert alias.target is target['Thing']
    assert alias.final_target is target['Thing']

def test_missing_alias_target_raises_and_stays_unresolved():
    modules = ModulesCollection()
    holder = Module('holder')
    holder['Missing'] = Alias('Missing', 'absent.Thing')
    modules['holder'] = holder
    alias = holder['Missing']
    with pytest.raises(AliasResolutionError):
        alias.resolve_target()
    assert alias.resolved is False

def test_alias_cycle_and_failed_chain_do_not_partially_resolve():
    cyclic_modules = ModulesCollection()
    cyclic = Module('cyclic')
    cyclic['x'] = Alias('x', 'cyclic.y')
    cyclic['y'] = Alias('y', 'cyclic.x')
    cyclic_modules['cyclic'] = cyclic
    with pytest.raises(CyclicAliasError):
        cyclic['x'].resolve_target()
    assert cyclic['x'].resolved is False
    assert cyclic['y'].resolved is False
    chain_modules = ModulesCollection()
    chain = Module('chain')
    chain['a'] = Alias('a', 'chain.b')
    chain['b'] = Alias('b', 'absent.c')
    chain_modules['chain'] = chain
    with pytest.raises(AliasResolutionError):
        chain['a'].resolve_target()
    assert chain['a'].resolved is False
    assert chain['b'].resolved is False

def test_google_numpy_and_sphinx_parsers_return_structured_sections():
    function = Function('f', parameters=Parameters(Parameter('x', annotation='int')), returns='str')
    google_sections = parse_google(Docstring('Summary.\n\nArgs:\n    x: number\n\nReturns:\n    result\n', parent=function), warnings=False)
    numpy_sections = parse_numpy(Docstring('Summary.\n\nParameters\n----------\nx : int\n    number\n\nReturns\n-------\nstr\n    result\n'), warnings=False)
    sphinx_sections = parse_sphinx(Docstring(':param int x: number\n:returns: result\n:rtype: str\n:raises ValueError: bad\n'), warnings=False)
    google_parameters = next((s for s in google_sections if isinstance(s, DocstringSectionParameters)))
    google_returns = next((s for s in google_sections if isinstance(s, DocstringSectionReturns)))
    assert google_parameters.value[0].name == 'x'
    assert str(google_parameters.value[0].annotation) == 'int'
    assert google_parameters.value[0].description == 'number'
    assert str(google_returns.value[0].annotation) == 'str'
    assert google_returns.value[0].description == 'result'
    numpy_parameters = next((s for s in numpy_sections if isinstance(s, DocstringSectionParameters)))
    numpy_returns = next((s for s in numpy_sections if isinstance(s, DocstringSectionReturns)))
    assert str(numpy_parameters.value[0].annotation) == 'int'
    assert numpy_parameters.value[0].description == 'number'
    assert str(numpy_returns.value[0].annotation) == 'str'
    sphinx_raises = next((s for s in sphinx_sections if isinstance(s, DocstringSectionRaises)))
    assert str(sphinx_raises.value[0].annotation) == 'ValueError'
    assert sphinx_raises.value[0].description == 'bad'

def test_parse_auto_returns_sections_for_detected_numpy_style():
    docstring = Docstring('Summary.\n\nParameters\n----------\nx : int\n    number\n')
    sections = parse_auto(docstring)
    assert [section.kind.value for section in sections] == ['text', 'parameters']
    parameters = next((section for section in sections if isinstance(section, DocstringSectionParameters)))
    assert parameters.value[0].name == 'x'
    assert str(parameters.value[0].annotation) == 'int'

def test_absent_member_and_parameter_operations_raise_key_error():
    module = Module('m')
    parameters = Parameters(Parameter('x'))
    with pytest.raises(KeyError):
        module['missing']
    with pytest.raises(KeyError):
        del parameters['missing']

def test_invalid_extension_raises_public_error():
    with pytest.raises((ExtensionNotLoadedError, ExtensionError)):
        load_extensions('definitely.not.an.extension')

def test_malformed_json_raises_value_error():
    with pytest.raises(ValueError):
        Module.from_json('{')

def test_docstring_parse_with_function_parent_returns_sections() -> None:
    function = Function('func', parameters=Parameters(Parameter('param1', annotation=None, kind=ParameterKind('positional or keyword')), Parameter('param2', annotation='int', kind=ParameterKind('keyword-only'))))
    docstring = Docstring("\n        Hello I'm a docstring!\n\n        Parameters:\n            param1: Description.\n            param2: Description.\n        ", lineno=1, parent=function)
    sections = parse(docstring, Parser.google)
    assert sections
