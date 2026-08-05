# Spec2Repo oracle - atomic tests for griffe-apimodel-fullrepro-001

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from griffe import (
    Alias,
    AliasResolutionError,
    Attribute,
    Class,
    CyclicAliasError,
    Docstring,
    DocstringSectionParameters,
    DocstringSectionRaises,
    DocstringSectionReturns,
    DocstringSectionText,
    ExtensionError,
    ExtensionNotLoadedError,
    Function,
    Kind,
    Module,
    ModulesCollection,
    Parameter,
    ParameterKind,
    Parameters,
    Parser,
    TypeAlias,
    infer_docstring_style,
    load,
    load_extensions,
    parse,
    parse_auto,
    parse_google,
    parse_numpy,
    parse_sphinx,
    visit,
)

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

# --- composition fix additions (2026-07-20) ---


def test_load_single_module_exposes_docstring_parameters_and_annotations(tmp_path: Path):
    source = '"""Module docs."""\n\nLIMIT: int = 10\n\ndef build(name: str, count: int = 2) -> list:\n    """Build things."""\n    return [name] * count\n'
    (tmp_path / 'singlemod.py').write_text(source, encoding='utf-8')
    module = load('singlemod', search_paths=[tmp_path])
    function = module['build']
    assert module.analysis == 'static'
    assert module.docstring.value == 'Module docs.'
    assert [parameter.name for parameter in function.parameters] == ['name', 'count']
    assert str(function.returns) == 'list'
    assert function.parameters['count'].default == '2'
    assert function.parameters['count'].required is False
    assert function.parameters['name'].required is True
    assert str(module['LIMIT'].annotation) == 'int'
    assert module['LIMIT'].value == '10'

def test_docstring_value_is_dedented_and_lines_split():
    docstring = Docstring('\n    Summary.\n\n    More text.\n    ')
    assert docstring.value == 'Summary.\n\nMore text.'
    assert docstring.lines == ['Summary.', '', 'More text.']

def test_infer_docstring_style_detects_known_styles_and_none_for_plain_text():
    numpy_doc = Docstring('Summary.\n\nParameters\n----------\nx : int\n    number\n')
    google_doc = Docstring('Summary.\n\nArgs:\n    x: number\n')
    plain_doc = Docstring('Just a sentence.')
    assert infer_docstring_style(numpy_doc) == (Parser.numpy, None)
    assert infer_docstring_style(google_doc) == (Parser.google, None)
    assert infer_docstring_style(plain_doc) == (None, None)

def test_parameters_add_appends_and_rejects_duplicate_names():
    parameters = Parameters()
    parameters.add(Parameter('x', annotation='int'))
    assert len(parameters) == 1
    assert 'x' in parameters
    assert parameters[0].name == 'x'
    with pytest.raises(ValueError):
        parameters.add(Parameter('x'))

def test_docstring_parse_uses_call_parser_then_stored_parser_then_text_fallback():
    function = Function('f', parameters=Parameters(Parameter('x', annotation='int')))
    stored = Docstring('Summary.\n\nArgs:\n    x: number\n', parent=function, parser=Parser.google)
    assert [section.kind.value for section in stored.parse()] == ['text', 'parameters']
    assert [section.kind.value for section in stored.parse(Parser.sphinx)] == ['text']
    plain = Docstring('Hello world.')
    fallback = plain.parse()
    assert [type(section) for section in fallback] == [DocstringSectionText]
    assert fallback[0].value == 'Hello world.'

# --- supplemental atomic tests (2026-07-23) ---

def test_member_deletion_removes_from_graph():
    module = Module('pkg')
    module['a'] = Attribute('a')
    assert 'a' in module.members
    del module['a']
    with pytest.raises(KeyError):
        module['a']

def test_type_alias_exposes_value_and_kind():
    ta = TypeAlias('MyType', value='list[str]')
    assert ta.kind is Kind.TYPE_ALIAS
    assert ta.is_type_alias is True
    assert ta.value == 'list[str]'
    assert ta.name == 'MyType'

def test_docstring_source_raises_value_error_without_parent():
    doc = Docstring('Hello.')
    with pytest.raises(ValueError):
        _ = doc.source

def test_object_path_reflects_hierarchical_location():
    module = Module('root')
    cls = Class('Inner')
    module['Inner'] = cls
    assert cls.path == 'root.Inner'
    assert cls.canonical_path == 'root.Inner'
    assert module.path == 'root'

def test_function_exposes_return_annotation_and_parameter_required():
    f = Function('compute',
                 parameters=Parameters(
                     Parameter('x', annotation='float', kind=ParameterKind('positional or keyword')),
                     Parameter('y', annotation='float', default='0.0'),
                 ),
                 returns='float')
    assert [p.name for p in f.parameters] == ['x', 'y']
    assert str(f.returns) == 'float'
    assert f.parameters['x'].required is True
    assert f.parameters['y'].required is False

def test_class_exposes_bases_and_kind():
    cls = Class('Sub', bases=['Base', 'Mixin'])
    assert cls.kind is Kind.CLASS
    assert cls.is_class is True
    assert 'Base' in [str(b) for b in cls.bases]

def test_module_from_json_reconstructs_navigable_graph():
    module = visit('test_mod', Path('test_mod.py'), dedent('''
        def f(a: int):
            pass

        v: int = 42
    '''))
    json_str = module.as_json()
    clone = Module.from_json(json_str)
    assert clone.name == 'test_mod'
    assert clone['f'].kind is Kind.FUNCTION
    assert clone['v'].kind is Kind.ATTRIBUTE
    assert clone['v'].value == '42'
    assert [p.name for p in clone['f'].parameters] == ['a']

def test_docstring_parsed_caches_first_result():
    doc = Docstring('Summary.\n\nArgs:\n    x: number\n', parser=Parser.google)
    first = doc.parsed
    doc.parser = Parser.sphinx
    doc.parser_options = {"returns_multiple_items": False}
    second = doc.parsed
    assert first is second
    assert [section.kind.value for section in second] == ['text', 'parameters']

def test_attribute_exposes_annotation_and_value():
    attr = Attribute('LIMIT', annotation='int', value='100')
    assert attr.kind is Kind.ATTRIBUTE
    assert attr.is_attribute is True
    assert str(attr.annotation) == 'int'
    assert attr.value == '100'
    assert attr.name == 'LIMIT'
