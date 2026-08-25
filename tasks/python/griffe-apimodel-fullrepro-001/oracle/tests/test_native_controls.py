from __future__ import annotations

import io
import json

import pytest

from griffe import (
    Attribute,
    BreakageKind,
    Class,
    Docstring,
    Extension,
    Extensions,
    Function,
    Module,
    Parameter,
    ParameterKind,
    Parameters,
    Parser,
    dump,
    find_breaking_changes,
    load,
    parse_google,
)

from .support import semantic_graph, visit_code, write_package


def test_a01_declared_member_parent_and_path_are_one_identity() -> None:
    package = Module("contract")
    service = Class("Service")
    operation = Function("operate")
    package["Service"] = service
    service["operate"] = operation
    assert operation.parent is service
    assert package["Service.operate"] is operation
    assert operation.path == "contract.Service.operate"
    del service["operate"]
    with pytest.raises(KeyError):
        package["Service.operate"]


def test_a02_parameters_preserve_order_and_normalize_variadic_names() -> None:
    parameters = Parameters(
        Parameter("value", kind=ParameterKind.positional_or_keyword),
        Parameter("items", kind=ParameterKind.var_positional),
        Parameter("options", kind=ParameterKind.var_keyword),
    )
    assert parameters[0] is parameters["value"]
    assert parameters["*items"] is parameters["items"]
    assert parameters["**options"] is parameters["options"]
    parameters["value"] = Parameter("value", default="3")
    assert [item.name for item in parameters] == ["value", "items", "options"]
    assert not parameters["value"].required
    with pytest.raises(ValueError):
        parameters.add(Parameter("value"))


def test_a03_visit_retains_static_exports_lines_and_parents(tmp_path) -> None:
    source = "__all__ = ['public']\npublic: int = 3\n_private = 4\n"
    module = visit_code(source, root=tmp_path)
    assert module.analysis == "static"
    assert [str(item) for item in module.exports] == ["public"]
    assert module["public"].parent is module
    assert module["public"].lineno == 2
    assert module.filepath == tmp_path / "api.py"


def test_a04_docstring_parser_precedence_and_cache_are_public() -> None:
    function = Function(
        "render",
        parameters=Parameters(
            Parameter("value", annotation="int", kind=ParameterKind.positional_or_keyword)
        ),
        returns="str",
    )
    docstring = Docstring(
        "Summary.\n\nArgs:\n    value: Input.\n\nReturns:\n    Output.",
        parent=function,
        parser=Parser.google,
    )
    direct = parse_google(docstring, warnings=False)
    cached = docstring.parsed
    assert [section.kind for section in direct] == [section.kind for section in cached]
    assert docstring.parsed is cached


def test_a05_breakages_ignore_private_and_preserve_kind_class() -> None:
    old = visit_code("def public(value=1): ...\ndef _private(): ...\n")
    new = visit_code("def public(value): ...\n")
    breakages = list(find_breaking_changes(old, new))
    assert {item.kind for item in breakages} == {BreakageKind.PARAMETER_CHANGED_REQUIRED}
    assert all(item.obj.path == "api.public" for item in breakages)


def test_a06_extensions_dispatch_in_order_and_stop_after_failure() -> None:
    calls: list[str] = []

    class First(Extension):
        def on_package(self, *, pkg, loader, **kwargs) -> None:
            calls.append("first")
            pkg["marker"] = Attribute("marker", value="1")

    class Failing(Extension):
        def on_package(self, *, pkg, loader, **kwargs) -> None:
            calls.append("failing")
            raise RuntimeError("stop")

    class Forbidden(Extension):
        def on_package(self, *, pkg, loader, **kwargs) -> None:
            calls.append("forbidden")

    package = Module("api")
    with pytest.raises(RuntimeError, match="stop"):
        Extensions(First(), Failing(), Forbidden()).call("on_package", pkg=package, loader=object())
    assert calls == ["first", "failing"]
    assert package["marker"].parent is package


def test_a07_command_parser_and_dump_have_public_nonzero_protocol(tmp_path) -> None:
    from griffe import get_parser

    parser = get_parser()
    assert parser is not None
    stream = io.StringIO()
    result = dump(["missing_contract_package"], output=stream, search_paths=[tmp_path], allow_inspection=False)
    assert result != 0


def test_a08_minimal_json_restores_navigation_and_callable_facts() -> None:
    package = Module("api", docstring=Docstring("API docs."))
    package["run"] = Function(
        "run",
        parameters=Parameters(
            Parameter("value", annotation="int", kind=ParameterKind.positional_or_keyword)
        ),
        returns="str",
        lineno=1,
        endlineno=1,
    )
    restored = Module.from_json(package.as_json(full=False, sort_keys=True))
    assert restored["run"].parent is restored
    assert restored["run"].parameters["value"].name == "value"
    assert str(restored["run"].returns) == "str"


def test_i01_explicit_submodule_load_preserves_alias_and_definition_paths(tmp_path) -> None:
    write_package(
        tmp_path,
        "native_one",
        {
            "__init__.py": "from .models import Item as PublicItem\n__all__=['PublicItem']\n",
            "models.py": "class Item:\n    value = 7\n",
        },
    )
    package = load(
        "native_one",
        search_paths=[tmp_path],
        submodules=True,
        resolve_aliases=True,
        resolve_external=False,
        allow_inspection=False,
    )
    alias = package["PublicItem"]
    assert alias.path == "native_one.PublicItem"
    assert alias.canonical_path == "native_one.models.Item"
    assert alias.final_target is package["models.Item"]


def test_i02_visit_minimal_roundtrip_preserves_graph_semantics(tmp_path) -> None:
    module = visit_code("class Box:\n    def get(self, value: int) -> str: ...\n", root=tmp_path)
    restored = Module.from_json(module.as_json(full=False))
    assert semantic_graph(restored) == semantic_graph(module)
    assert restored["Box.get"].parent is restored["Box"]


def test_i03_loaded_docstring_parser_matches_direct_configuration(tmp_path) -> None:
    write_package(
        tmp_path,
        "native_three",
        {"__init__.py": "def run(value: int) -> str:\n    '''Summary.\\n\\nArgs:\\n    value: Input.\\n\\nReturns:\\n    Output.'''\n"},
    )
    package = load("native_three", search_paths=[tmp_path], docstring_parser=Parser.google)
    loaded = package["run"].docstring.parsed
    direct = parse_google(package["run"].docstring, warnings=False)
    assert [section.kind for section in loaded] == [section.kind for section in direct]


def test_i04_extension_effect_reaches_navigation_and_minimal_json(tmp_path) -> None:
    write_package(tmp_path, "native_four", {"__init__.py": "original = 1\n"})

    class Marker(Extension):
        def on_package(self, *, pkg, loader, **kwargs) -> None:
            pkg["marker"] = Attribute("marker", value="2", lineno=1, endlineno=1)

    package = load("native_four", search_paths=[tmp_path], extensions=Extensions(Marker()))
    restored = Module.from_json(package.as_json(full=False))
    assert str(restored["marker"].value) == "2"
    assert restored["marker"].parent is restored


def test_i05_breakage_set_survives_minimal_roundtrip(tmp_path) -> None:
    old = visit_code("def call(value=1): ...\n", name="api", root=tmp_path)
    new = visit_code("def call(value): ...\n", name="api", root=tmp_path)
    before = {item.kind for item in find_breaking_changes(old, new)}
    after = {
        item.kind
        for item in find_breaking_changes(
            Module.from_json(old.as_json(full=False)),
            Module.from_json(new.as_json(full=False)),
        )
    }
    assert before == after == {BreakageKind.PARAMETER_CHANGED_REQUIRED}


def test_i06_callable_dump_combines_packages_with_parented_graphs(tmp_path) -> None:
    write_package(tmp_path, "native_six_a", {"__init__.py": "VALUE = 1\n"})
    write_package(tmp_path, "native_six_b", {"__init__.py": "VALUE = 2\n"})
    stream = io.StringIO()
    result = dump(["native_six_a", "native_six_b"], output=stream, search_paths=[tmp_path], full=False)
    payload = json.loads(stream.getvalue())
    first = Module.from_json(json.dumps(payload["native_six_a"]))
    assert result == 0
    assert sorted(payload) == ["native_six_a", "native_six_b"]
    assert first["VALUE"].parent is first
