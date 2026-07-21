from __future__ import annotations

# Rewritten from tests/importer/test_importer.py at the pinned source revision.
import ast
import importlib
import runpy
import sys
from importlib import reload
from pathlib import Path
import pytest
import hy
from hy.compiler import hy_compile
from hy.errors import HyLanguageError
from hy.importer import HyLoader
from hy.reader import read_many

RESOURCE_ROOT = Path(__file__).with_name('_hy_test_resources')

def test_basics():
    """Make sure the basics of the importer work"""
    resources_mod = importlib.import_module('_hy_test_resources')
    assert resources_mod.in_init == 'chippy'
    bin_mod = importlib.import_module('_hy_test_resources.bin')
    assert hasattr(bin_mod, '_null_fn_for_import_test')

def test_runpy():
    basic_ns = runpy.run_path(str(RESOURCE_ROOT / 'importer/basic.hy'))
    assert 'square' in basic_ns
    main_ns = runpy.run_path(str(RESOURCE_ROOT / 'bin'))
    assert main_ns['visited_main'] == 1
    del main_ns
    main_ns = runpy.run_module('_hy_test_resources.bin')
    assert main_ns['visited_main'] == 1
    with pytest.raises(IOError):
        runpy.run_path(str(RESOURCE_ROOT / 'foobarbaz.py'))

def test_stringer():
    _ast = hy_compile(read_many('(defn square [x] (* x x))'), __name__, import_stdlib=False)
    assert type(_ast.body[0]) == ast.FunctionDef

def test_imports():
    source = RESOURCE_ROOT / 'importer/a.hy'
    testLoader = HyLoader('_hy_test_resources.importer.a', str(source))
    spec = importlib.util.spec_from_loader(testLoader.name, testLoader)
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(NameError) as excinfo:
        testLoader.exec_module(mod)
    assert 'thisshouldnotwork' in excinfo.value.args[0]

def test_import_error_reporting():
    """Make sure that (import) reports errors correctly."""
    with pytest.raises(HyLanguageError):
        hy_compile(read_many('(import "sys")'), __name__)

def test_import_error_cleanup():
    """Failed initial imports should not leave dead modules in `sys.modules`."""
    with pytest.raises(hy.errors.HyMacroExpansionError):
        importlib.import_module('_hy_test_resources.fails')
    assert '_hy_test_resources.fails' not in sys.modules

@pytest.mark.skipif(sys.dont_write_bytecode, reason='Bytecode generation is suppressed')
def test_import_autocompiles(tmp_path):
    """Test that (import) byte-compiles the module."""
    p = tmp_path / 'mymodule.hy'
    p.write_text('(defn pyctest [s] (+ "X" s "Y"))')

    def import_from_path(path):
        spec = importlib.util.spec_from_file_location('mymodule', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    assert import_from_path(p).pyctest('flim') == 'XflimY'
    assert Path(importlib.util.cache_from_source(p)).exists()
    assert import_from_path(importlib.util.cache_from_source(p)).pyctest('flam') == 'XflamY'

def test_eval():

    def eval_str(s):
        return hy.eval(hy.read(s))
    assert eval_str('[1 2 3]') == [1, 2, 3]
    assert eval_str('{"dog" "bark" "cat" "meow"}') == {'dog': 'bark', 'cat': 'meow'}
    assert eval_str('#(1 2 3)') == (1, 2, 3)
    assert eval_str('#{3 1 2}') == {1, 2, 3}
    assert eval_str('(.strip " fooooo   ")') == 'fooooo'
    assert eval_str('(if True "this is if true" "this is if false")') == 'this is if true'
    assert eval_str('(lfor num (range 100) :if (= (% num 2) 1) (pow num 2))') == [pow(num, 2) for num in range(100) if num % 2 == 1]

def test_reload(tmp_path, monkeypatch):
    """Generate a test module, confirm that it imports properly (and puts the
    module in `sys.modules`), then modify the module so that it produces an
    error when reloaded.  Next, fix the error, reload, and check that the
    module is updated and working fine.  Rinse, repeat.

    This test is adapted from CPython's `test_import.py`.
    """

    def unlink(filename):
        Path(source).unlink()
        bytecode = importlib.util.cache_from_source(source)
        if Path(bytecode).is_file():
            Path(bytecode).unlink()
    TESTFN = 'testfn'
    source = tmp_path / (TESTFN + '.hy')
    source.write_text('(setv a 1)  (setv b 2)')
    monkeypatch.syspath_prepend(tmp_path)
    try:
        mod = importlib.import_module(TESTFN)
        assert TESTFN in sys.modules
        assert mod.a == 1
        assert mod.b == 2
        unlink(source)
        source.write_text('(setv a 10)  (setv b (// 20 0))')
        with pytest.raises(ZeroDivisionError):
            reload(mod)
        mod = sys.modules.get(TESTFN)
        assert mod is not None
        assert mod.a == 10
        assert mod.b == 2
        unlink(source)
        source.write_text('(setv a 11)  (setv b (// 20 1))')
        reload(mod)
        mod = sys.modules.get(TESTFN)
        assert mod is not None
        assert mod.a == 11
        assert mod.b == 20
        unlink(source)
        source.write_text('(setv a 11  (setv b (// 20 1))')
        with pytest.raises(hy.PrematureEndOfInput):
            reload(mod)
        mod = sys.modules.get(TESTFN)
        assert mod is not None
        assert mod.a == 11
        assert mod.b == 20
        unlink(source)
        source.write_text('(setv a 12)  (setv b (// 10 1))')
        reload(mod)
        mod = sys.modules.get(TESTFN)
        assert mod is not None
        assert mod.a == 12
        assert mod.b == 10
    finally:
        if TESTFN in sys.modules:
            del sys.modules[TESTFN]

def test_reload_reexecute(capsys):
    """A module is re-executed when it's reloaded, even if it's
    unchanged.

    https://github.com/hylang/hy/issues/712"""
    import _hy_test_resources.hello_world
    assert capsys.readouterr().out == 'hello world\n'
    assert capsys.readouterr().out == ''
    reload(_hy_test_resources.hello_world)
    assert capsys.readouterr().out == 'hello world\n'

def test_circular(monkeypatch):
    """Test circular imports by creating a temporary file/module that calls a
    function that imports itself."""
    monkeypatch.syspath_prepend(RESOURCE_ROOT / 'importer')
    assert runpy.run_module('circular')['f']() == 1

def test_shadowed_basename(monkeypatch):
    """Make sure Hy loads `.hy` files instead of their `.py` counterparts (.e.g
    `__init__.py` and `__init__.hy`).
    """
    monkeypatch.syspath_prepend(RESOURCE_ROOT / 'importer')
    foo = importlib.import_module('foo')
    assert Path(foo.__file__).name == '__init__.hy'
    assert foo.ext == 'hy'
    some_mod = importlib.import_module('foo.some_mod')
    assert Path(some_mod.__file__).name == 'some_mod.hy'
    assert some_mod.ext == 'hy'
