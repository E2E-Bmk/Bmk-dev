from __future__ import annotations

from pathlib import Path


def _astroid():
    import astroid
    return astroid


def test_a01(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("x = 1\ny = x + 2\n", module_name="sample", path="sample.py", apply_transforms=False)
    assert module.name == "sample" and str(module.file).endswith("sample.py")
    assert [type(item).__name__ for item in module.body] == ["Assign", "Assign"]


def test_a02(tmp_path: Path) -> None:
    astroid = _astroid()
    selected = astroid.extract_node("value = 1\nresult = __(value + 2)")
    assert type(selected).__name__ == "BinOp" and selected.as_string() == "value + 2"


def test_a03(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("def f(a):\n    return a\n", apply_transforms=False)
    function = module.body[0]; returned = function.body[0].value
    assert returned.parent is function.body[0] and returned.root() is module and returned.frame() is function


def test_a04(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("public = 1\n_hidden = 2\n__all__ = ['public']\n", apply_transforms=False)
    assert module.public_names() == ["public"] and module.wildcard_import_names() == ["public"]
    assert module.getattr("public") == module.locals["public"]


def test_a05(tmp_path: Path) -> None:
    astroid = _astroid()
    node = astroid.extract_node("6 * 7")
    inferred = list(node.infer())
    assert len(inferred) == 1 and type(inferred[0]).__name__ == "Const" and inferred[0].value == 42


def test_a06(tmp_path: Path) -> None:
    astroid = _astroid()
    manager = astroid.manager.AstroidManager()
    module = manager.ast_from_string("token = 'x'", modname="local_probe")
    assert module.name == "local_probe" and manager.astroid_cache["local_probe"] is module


def test_a07(tmp_path: Path) -> None:
    astroid = _astroid()
    try:
        astroid.parse("if :")
    except astroid.AstroidSyntaxError as exc:
        assert exc.error is not None
    else:
        raise AssertionError("invalid source must fail")


def test_a08(tmp_path: Path) -> None:
    astroid = _astroid()
    assert astroid.UnresolvableName is astroid.NameInferenceError
    assert astroid.NotFoundError is astroid.AttributeInferenceError


def test_i01(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("base = 40\ndef compute():\n    local = base + 2\n    return local\n", apply_transforms=False)
    function = module.locals["compute"][0]
    name = next(node for node in function.nodes_of_class(astroid.nodes.Name) if node.name == "base")
    scope, bindings = name.lookup("base")
    assert scope is module and bindings == module.locals["base"] and list(name.infer())[0].value == 40


def test_i02(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("class Base:\n    marker = 7\nclass Child(Base):\n    pass\nitem = Child()\nvalue = item.marker\n", apply_transforms=False)
    value = module.locals["value"][0].parent.value
    inferred = list(value.infer())
    assert len(inferred) == 1 and inferred[0].value == 7 and next(module.locals["Child"][0].ancestors()).name == "Base"


def test_i03(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("def add(a, b=2):\n    return a + b\nresult = add(40)\n", apply_transforms=False)
    function = module.locals["add"][0]
    assert function.args.default_value("b").value == 2
    assert list(module.locals["result"][0].parent.value.infer())[0].value == 42


def test_i04(tmp_path: Path) -> None:
    astroid = _astroid()
    manager = astroid.manager.AstroidManager()
    one = manager.ast_from_string("value = 1", modname="cache_probe")
    two = manager.ast_from_string("value = 2", modname="cache_probe")
    assert one is manager.astroid_cache["cache_probe"] and two is not one
    assert list(two.locals) == ["value"]


def test_s01(tmp_path: Path) -> None:
    astroid = _astroid()
    module = astroid.parse("class C:\n    def method(self):\n        return 3\nobj = C()\nresult = obj.method()\n", apply_transforms=False)
    result = list(module.locals["result"][0].parent.value.infer())
    assert len(result) == 1 and result[0].value == 3
    assert module.locals["C"][0].locals["method"][0].parent is module.locals["C"][0]


def test_s02(tmp_path: Path) -> None:
    astroid = _astroid()
    manager = astroid.manager.AstroidManager()
    module = manager.ast_from_module_name("builtins", use_cache=False)
    assert module.name == "builtins" and module.getattr("len") and list(module.igetattr("len"))
