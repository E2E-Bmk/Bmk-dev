from __future__ import absolute_import
import logging
from unittest import TestCase, main, skipIf
from lark import Lark, Tree, Transformer, UnexpectedInput
from lark.exceptions import ConfigurationError
from lark.lexer import Lexer, Token
import lark.lark as lark_module
from lark.reconstruct import Reconstructor
from . import test_reconstructor
from io import BytesIO
try:
    import regex
except ImportError:
    regex = None

class MockFile(BytesIO):

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

class MockFS:

    def __init__(self):
        self.files = {}

    def open(self, name, mode='r', **kwargs):
        if name not in self.files:
            if 'r' in mode:
                raise FileNotFoundError(name)
            f = self.files[name] = MockFile()
        else:
            f = self.files[name]
            f.seek(0)
        return f

    def exists(self, name):
        return name in self.files

class CustomLexer(Lexer):

    def __init__(self, lexer_conf):
        pass

    def lex(self, data):
        for obj in data:
            yield Token('A', obj)

class InlineTestT(Transformer):

    def add(self, children):
        return sum(children if isinstance(children, list) else children.children)

    def NUM(self, token):
        return int(token)

    def __reduce__(self):
        raise TypeError('This Transformer should not be pickled.')

def append_zero(t):
    return t.update(value=t.value + '0')

class TestCache(TestCase):
    g = 'start: "a"'

    def setUp(self):
        self.fs = lark_module.FS
        self.mock_fs = MockFS()
        lark_module.FS = self.mock_fs

    def tearDown(self):
        self.mock_fs.files = {}
        lark_module.FS = self.fs

    def test_simple(self):
        fn = 'bla'
        Lark(self.g, parser='lalr', cache=fn)
        assert fn in self.mock_fs.files
        parser = Lark(self.g, parser='lalr', cache=fn)
        assert parser.parse('a') == Tree('start', [])

    def test_options(self):
        Lark(self.g, parser='lalr', debug=True, cache=True)
        parser = Lark(self.g, parser='lalr', debug=True, cache=True)
        assert parser.options.options['debug']

    def test_inline(self):
        g = '\n        start: add+\n        add: NUM "+" NUM\n        NUM: /\\d+/\n        %ignore " "\n        '
        text = '1+2 3+4'
        expected = Tree('start', [30, 70])
        parser = Lark(g, parser='lalr', transformer=InlineTestT(), cache=True, lexer_callbacks={'NUM': append_zero})
        res0 = parser.parse(text)
        parser = Lark(g, parser='lalr', transformer=InlineTestT(), cache=True, lexer_callbacks={'NUM': append_zero})
        assert len(self.mock_fs.files) == 1
        res1 = parser.parse(text)
        res2 = InlineTestT().transform(Lark(g, parser='lalr', cache=True, lexer_callbacks={'NUM': append_zero}).parse(text))
        assert res0 == res1 == res2 == expected

    def test_imports(self):
        g = '\n        %import .grammars.ab (startab, expr)\n        '
        parser = Lark(g, parser='lalr', start='startab', cache=True, source_path=__file__)
        assert len(self.mock_fs.files) == 1
        parser = Lark(g, parser='lalr', start='startab', cache=True, source_path=__file__)
        assert len(self.mock_fs.files) == 1
        res = parser.parse('ab')
        self.assertEqual(res, Tree('startab', [Tree('expr', ['a', 'b'])]))

    @skipIf(regex is None, "'regex' lib not installed")
    def test_recursive_pattern(self):
        g = '\n        start: recursive+\n        recursive: /\\w{3}\\d{3}(?R)?/\n        '
        assert len(self.mock_fs.files) == 0
        Lark(g, parser='lalr', regex=True, cache=True)
        assert len(self.mock_fs.files) == 1
        with self.assertLogs('lark', level='ERROR') as cm:
            Lark(g, parser='lalr', regex=True, cache=True)
            assert len(self.mock_fs.files) == 1
            logging.getLogger('lark').error('dummy message')
        self.assertCountEqual(cm.output, ['ERROR:lark:dummy message'])

    def test_cache_grammar(self):
        with self.assertRaises(ConfigurationError):
            Lark(self.g, parser='lalr', cache=False, cache_grammar=True)
        assert len(self.mock_fs.files) == 0
        parser1 = Lark(self.g, parser='lalr', cache=True, cache_grammar=True)
        parser2 = Lark(self.g, parser='lalr', cache=True, cache_grammar=True)
        assert parser2.parse('a') == Tree('start', [])
        assert len(self.mock_fs.files) == 1
        assert 'cache_grammar' in list(self.mock_fs.files)[0]
        assert parser1.grammar is not parser2.grammar
        assert parser1.grammar.term_defs == parser2.grammar.term_defs
        assert repr(parser1.grammar.rule_defs) == repr(parser2.grammar.rule_defs)

    def test_reconstruct(self):
        grammar = '\n        start: (rule | NL)*\n        rule: WORD ":" NUMBER\n        NL: /(\\r?\\n)+\\s*/\n        ' + test_reconstructor.common
        code = '\n        Elephants: 12\n        '
        _parser = Lark(grammar, parser='lalr', maybe_placeholders=False, cache=True, cache_grammar=True)
        assert len(self.mock_fs.files) == 1
        parser = Lark(grammar, parser='lalr', maybe_placeholders=False, cache=True, cache_grammar=True)
        assert _parser.grammar is not parser.grammar
        tree = parser.parse(code)
        new = Reconstructor(parser).reconstruct(tree)
        self.assertEqual(test_reconstructor._remove_ws(code), test_reconstructor._remove_ws(new))
if __name__ == '__main__':
    main()
