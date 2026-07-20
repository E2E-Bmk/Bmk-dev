import json
import sys
import unittest
from itertools import product
from unittest import TestCase
from lark import Lark
from lark.reconstruct import Reconstructor
common = '\n%import common (WS_INLINE, NUMBER, WORD)\n%ignore WS_INLINE\n'

def _remove_ws(s):
    return s.replace(' ', '').replace('\n', '')

class TestReconstructor(TestCase):

    def assert_reconstruct(self, grammar, code, **options):
        parser = Lark(grammar, parser='lalr', maybe_placeholders=False, **options)
        tree = parser.parse(code)
        new = Reconstructor(parser).reconstruct(tree)
        self.assertEqual(_remove_ws(code), _remove_ws(new))

    def test_starred_rule(self):
        g = '\n        start: item*\n        item: NL\n            | rule\n        rule: WORD ":" NUMBER\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        code = '\n        Elephants: 12\n        '
        self.assert_reconstruct(g, code)

    def test_starred_group(self):
        g = '\n        start: (rule | NL)*\n        rule: WORD ":" NUMBER\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        code = '\n        Elephants: 12\n        '
        self.assert_reconstruct(g, code)

    def test_alias(self):
        g = '\n        start: line*\n        line: NL\n            | rule\n            | "hello" -> hi\n        rule: WORD ":" NUMBER\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        code = '\n        Elephants: 12\n        hello\n        '
        self.assert_reconstruct(g, code)

    def test_keep_tokens(self):
        g = '\n        start: (NL | stmt)*\n        stmt: var op var\n        !op: ("+" | "-" | "*" | "/")\n        var: WORD\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        code = '\n        a+b\n        '
        self.assert_reconstruct(g, code)

    def test_expand_rule(self):
        g = '\n        ?start: (NL | mult_stmt)*\n        ?mult_stmt: sum_stmt ["*" sum_stmt]\n        ?sum_stmt: var ["+" var]\n        var: WORD\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        code = ['a', 'a*b', 'a+b', 'a*b+c', 'a+b*c', 'a+b*c+d']
        for c in code:
            self.assert_reconstruct(g, c)

    def test_json_example(self):
        test_json = '\n            {\n                "empty_object" : {},\n                "empty_array"  : [],\n                "booleans"     : { "YES" : true, "NO" : false },\n                "numbers"      : [ 0, 1, -2, 3.3, 4.4e5, 6.6e-7 ],\n                "strings"      : [ "This", [ "And" , "That", "And a \\"b" ] ],\n                "nothing"      : null\n            }\n        '
        json_grammar = '\n            ?start: value\n\n            ?value: object\n                  | array\n                  | string\n                  | SIGNED_NUMBER      -> number\n                  | "true"             -> true\n                  | "false"            -> false\n                  | "null"             -> null\n\n            array  : "[" [value ("," value)*] "]"\n            object : "{" [pair ("," pair)*] "}"\n            pair   : string ":" value\n\n            string : ESCAPED_STRING\n\n            %import common.ESCAPED_STRING\n            %import common.SIGNED_NUMBER\n            %import common.WS\n\n            %ignore WS\n        '
        json_parser = Lark(json_grammar, parser='lalr', maybe_placeholders=False)
        tree = json_parser.parse(test_json)
        new_json = Reconstructor(json_parser).reconstruct(tree)
        self.assertEqual(json.loads(new_json), json.loads(test_json))

    def test_keep_all_tokens(self):
        g = '\n        start: "a"? _B? c? _d?\n        _B: "b"\n        c: "c"\n        _d: "d"\n        '
        examples = list(map(''.join, product(('', 'a'), ('', 'b'), ('', 'c'), ('', 'd'))))
        for code in examples:
            self.assert_reconstruct(g, code, keep_all_tokens=True)

    def test_switch_grammar_unicode_terminal(self):
        """
        This test checks that a parse tree built with a grammar containing only ascii characters can be reconstructed
        with a grammar that has unicode rules (or vice versa). The original bug assigned ANON terminals to unicode
        keywords, which offsets the ANON terminal count in the unicode grammar and causes subsequent identical ANON
        tokens (e.g., `+=`) to mismatch between the two grammars.
        """
        g1 = '\n        start: (NL | stmt)*\n        stmt: "keyword" var op var\n        !op: ("+=" | "-=" | "*=" | "/=")\n        var: WORD\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        g2 = '\n        start: (NL | stmt)*\n        stmt: "குறிப்பு" var op var\n        !op: ("+=" | "-=" | "*=" | "/=")\n        var: WORD\n        NL: /(\\r?\\n)+\\s*/\n        ' + common
        code = '\n        keyword x += y\n        '
        l1 = Lark(g1, parser='lalr', maybe_placeholders=False)
        l2 = Lark(g2, parser='lalr', maybe_placeholders=False)
        r = Reconstructor(l2)
        tree = l1.parse(code)
        code2 = r.reconstruct(tree)
        assert l2.parse(code2) == tree
if __name__ == '__main__':
    unittest.main()
