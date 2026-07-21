from __future__ import absolute_import
import os
from unittest import TestCase, main
from lark import Lark, Token, Tree, ParseError, UnexpectedInput
from lark.load_grammar import GrammarError, GRAMMAR_ERRORS, find_grammar_errors, list_grammar_imports
from lark.load_grammar import FromPackageLoader
from lark.grammar import Symbol

class TestGrammar(TestCase):

    def setUp(self):
        pass

    def test_errors(self):
        for (msg, examples) in GRAMMAR_ERRORS:
            for example in examples:
                try:
                    p = Lark(example)
                except GrammarError as e:
                    assert msg in str(e)
                else:
                    assert False, 'example did not raise an error'

    def test_empty_literal(self):
        self.assertRaises(GrammarError, Lark, 'start: ""')

    def test_ignore_name(self):
        spaces = []
        p = Lark('\n            start: "a" "b"\n            WS: " "\n            %ignore WS\n        ', parser='lalr', lexer_callbacks={'WS': spaces.append})
        assert p.parse('a b') == p.parse('a    b')
        assert len(spaces) == 5

    def test_override_rule(self):
        p = Lark('\n            %import .test_templates_import (start, sep)\n\n            %override sep{item, delim}: item (delim item)* delim?\n            %ignore " "\n        ', source_path=__file__)
        a = p.parse('[1, 2, 3]')
        b = p.parse('[1, 2, 3, ]')
        assert a == b
        self.assertRaises(GrammarError, Lark, '\n            %import .test_templates_import (start, sep)\n\n            %override sep{item}: item (delim item)* delim?\n        ', source_path=__file__)
        self.assertRaises(GrammarError, Lark, '\n            %override sep{item}: item (delim item)* delim?\n        ', source_path=__file__)

    def test_override_terminal(self):
        p = Lark('\n\n            %import .grammars.ab (startab, A, B)\n\n            %override A: "c"\n            %override B: "d"\n        ', start='startab', source_path=__file__)
        a = p.parse('cd')
        self.assertEqual(a.children[0].children, [Token('A', 'c'), Token('B', 'd')])

    def test_extend_rule(self):
        p = Lark('\n            %import .grammars.ab (startab, A, B, expr)\n\n            %extend expr: B A\n        ', start='startab', source_path=__file__)
        a = p.parse('abab')
        self.assertEqual(a.children[0].children, ['a', Tree('expr', ['b', 'a']), 'b'])
        self.assertRaises(GrammarError, Lark, '\n            %extend expr: B A\n        ')

    def test_extend_term(self):
        p = Lark('\n            %import .grammars.ab (startab, A, B, expr)\n\n            %extend A: "c"\n        ', start='startab', source_path=__file__)
        a = p.parse('acbb')
        self.assertEqual(a.children[0].children, ['a', Tree('expr', ['c', 'b']), 'b'])

    def test_extend_twice(self):
        p = Lark('\n            start: x+\n\n            x: "a"\n            %extend x: "b"\n            %extend x: "c"\n        ')
        assert p.parse('abccbba') == p.parse('cbabbbb')

    def test_undefined_ignore(self):
        g = '!start: "A"\n\n            %ignore B\n            '
        self.assertRaises(GrammarError, Lark, g)
        g = '!start: "A"\n\n            %ignore start\n            '
        self.assertRaises(GrammarError, Lark, g)

    def test_alias_in_terminal(self):
        g = 'start: TERM\n            TERM: "a" -> alias\n            '
        self.assertRaises(GrammarError, Lark, g)

    def test_template_in_terminal(self):
        g = 'start: TERM\n            TERM: _quoted{"\'"}\n            _quoted{q}: q /.*?/ q\n            '
        self.assertRaises(GrammarError, Lark, g)

    def test_undefined_rule(self):
        self.assertRaises(GrammarError, Lark, 'start: a')

    def test_undefined_term(self):
        self.assertRaises(GrammarError, Lark, 'start: A')

    def test_declare_rule_name(self):
        self.assertRaises(GrammarError, Lark, 'start: "a"\n%declare foo')
        self.assertRaises(GrammarError, Lark, 'start: "a"\n%declare FOO bar')

    def test_token_multiline_only_works_with_x_flag(self):
        g = 'start: ABC\n                ABC: /  a      b c\n                            d\n                            e f\n                        /i\n                    '
        self.assertRaises(GrammarError, Lark, g)

    def test_import_custom_sources(self):
        custom_loader = FromPackageLoader(__name__, ('grammars',))
        grammar = '\n        start: startab\n\n        %import ab.startab\n        '
        p = Lark(grammar, import_paths=[custom_loader])
        self.assertEqual(p.parse('ab'), Tree('start', [Tree('startab', [Tree('ab__expr', [Token('ab__A', 'a'), Token('ab__B', 'b')])])]))

    def test_import_custom_sources2(self):
        custom_loader = FromPackageLoader(__name__, ('grammars',))
        grammar = '\n        start: rule_to_import\n\n        %import test_relative_import_of_nested_grammar__grammar_to_import.rule_to_import\n        '
        p = Lark(grammar, import_paths=[custom_loader])
        x = p.parse('N')
        self.assertEqual(next(x.find_data('rule_to_import')).children, ['N'])

    def test_import_custom_sources3(self):
        custom_loader2 = FromPackageLoader(__name__)
        grammar = '\n        %import .test_relative_import (start, WS)\n        %ignore WS\n        '
        p = Lark(grammar, import_paths=[custom_loader2], source_path=__file__)
        x = p.parse('12 capybaras')
        self.assertEqual(x.children, ['12', 'capybaras'])

    def test_ranged_repeat_terms(self):
        g = u'!start: AAA\n                AAA: "A"~3\n            '
        l = Lark(g, parser='lalr')
        self.assertEqual(l.parse(u'AAA'), Tree('start', ['AAA']))
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'AA')
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'AAAA')
        g = u'!start: AABB CC\n                AABB: "A"~0..2 "B"~2\n                CC: "C"~1..2\n            '
        l = Lark(g, parser='lalr')
        self.assertEqual(l.parse(u'AABBCC'), Tree('start', ['AABB', 'CC']))
        self.assertEqual(l.parse(u'BBC'), Tree('start', ['BB', 'C']))
        self.assertEqual(l.parse(u'ABBCC'), Tree('start', ['ABB', 'CC']))
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'AAAB')
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'AAABBB')
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'ABB')
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'AAAABB')

    def test_ranged_repeat_large(self):
        g = u'!start: "A"~60\n            '
        l = Lark(g, parser='lalr')
        self.assertGreater(len(l.rules), 1, 'Expected that more than one rule will be generated')
        self.assertEqual(l.parse(u'A' * 60), Tree('start', ['A'] * 60))
        self.assertRaises(ParseError, l.parse, u'A' * 59)
        self.assertRaises((ParseError, UnexpectedInput), l.parse, u'A' * 61)
        g = u'!start: "A"~15..100\n            '
        l = Lark(g, parser='lalr')
        for i in range(0, 110):
            if 15 <= i <= 100:
                self.assertEqual(l.parse(u'A' * i), Tree('start', ['A'] * i))
            else:
                self.assertRaises(UnexpectedInput, l.parse, u'A' * i)
        g = u'start: "A"~8191\n            '
        l = Lark(g, parser='lalr')
        self.assertEqual(l.parse(u'A' * 8191), Tree('start', []))
        self.assertRaises(UnexpectedInput, l.parse, u'A' * 8190)
        self.assertRaises(UnexpectedInput, l.parse, u'A' * 8192)

    def test_large_terminal(self):
        g = 'start: NUMBERS\n'
        g += 'NUMBERS: ' + '|'.join(('"%s"' % i for i in range(0, 1000)))
        l = Lark(g, parser='lalr')
        for i in (0, 9, 99, 999):
            self.assertEqual(l.parse(str(i)), Tree('start', [str(i)]))
        for i in (-1, 1000):
            self.assertRaises(UnexpectedInput, l.parse, str(i))

    def test_list_grammar_imports(self):
        grammar = '\n            %import .test_templates_import (start, sep)\n\n            %override sep{item, delim}: item (delim item)* delim?\n            %ignore " "\n            '
        imports = list_grammar_imports(grammar, [os.path.dirname(__file__)])
        self.assertEqual({os.path.split(i)[-1] for i in imports}, {'test_templates_import.lark', 'templates.lark'})
        imports = list_grammar_imports('%import common.WS', [])
        assert len(imports) == 1 and imports[0].pkg_name == 'lark'

    def test_inline_with_expand_single(self):
        grammar = '\n        start: _a\n        !?_a: "A"\n        '
        self.assertRaises(GrammarError, Lark, grammar)

    def test_line_breaks(self):
        p = Lark('start: "a" \\\n                       "b"\n                ')
        p.parse('ab')

    def test_symbol_eq(self):
        a = None
        b = Symbol('abc')
        self.assertNotEqual(a, b)
if __name__ == '__main__':
    main()
