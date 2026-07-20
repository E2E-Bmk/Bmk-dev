import re
import sys
import unittest
from typing import Optional
sys.path.insert(0, '..')
from pycparser.c_lexer import CLexer, Token

def require_token(tok: Optional[Token]) -> Token:
    assert tok is not None
    return tok

def token_list(clex):
    return list(iter(clex.token, None))

def token_types(clex):
    return [i.type for i in token_list(clex)]

class TestCLexerNoErrors(unittest.TestCase):
    """Test lexing of strings that are not supposed to cause
    errors. Therefore, the error_func passed to the lexer
    raises an exception.
    """

    def error_func(self, msg, line, column):
        self.fail(msg)

    def on_lbrace_func(self):
        pass

    def on_rbrace_func(self):
        pass

    def type_lookup_func(self, typ):
        if typ.startswith('mytype'):
            return True
        else:
            return False

    def setUp(self):
        self.clex = CLexer(self.error_func, lambda : None, lambda : None, self.type_lookup_func)

    def assertTokensTypes(self, str, types):
        self.clex.input(str)
        self.assertEqual(token_types(self.clex), types)

    def test_trivial_tokens(self):
        self.assertTokensTypes('1', ['INT_CONST_DEC'])
        self.assertTokensTypes('-', ['MINUS'])
        self.assertTokensTypes('volatile', ['VOLATILE'])
        self.assertTokensTypes('...', ['ELLIPSIS'])
        self.assertTokensTypes('++', ['PLUSPLUS'])
        self.assertTokensTypes('case int', ['CASE', 'INT'])
        self.assertTokensTypes('caseint', ['ID'])
        self.assertTokensTypes('$dollar cent$', ['ID', 'ID'])
        self.assertTokensTypes('i ^= 1;', ['ID', 'XOREQUAL', 'INT_CONST_DEC', 'SEMI'])

    def test_id_typeid(self):
        self.assertTokensTypes('myt', ['ID'])
        self.assertTokensTypes('mytype', ['TYPEID'])
        self.assertTokensTypes('mytype6 var', ['TYPEID', 'ID'])

    def test_integer_constants(self):
        self.assertTokensTypes('12', ['INT_CONST_DEC'])
        self.assertTokensTypes('12u', ['INT_CONST_DEC'])
        self.assertTokensTypes('12l', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872Ul', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872lU', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872LL', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872ull', ['INT_CONST_DEC'])
        self.assertTokensTypes('199872llu', ['INT_CONST_DEC'])
        self.assertTokensTypes('1009843200000uLL', ['INT_CONST_DEC'])
        self.assertTokensTypes('1009843200000LLu', ['INT_CONST_DEC'])
        self.assertTokensTypes('077', ['INT_CONST_OCT'])
        self.assertTokensTypes('0123456L', ['INT_CONST_OCT'])
        self.assertTokensTypes('0xf7', ['INT_CONST_HEX'])
        self.assertTokensTypes('0b110', ['INT_CONST_BIN'])
        self.assertTokensTypes('0x01202AAbbf7Ul', ['INT_CONST_HEX'])
        self.assertTokensTypes("'12'", ['INT_CONST_CHAR'])
        self.assertTokensTypes("'123'", ['INT_CONST_CHAR'])
        self.assertTokensTypes("'1AB4'", ['INT_CONST_CHAR'])
        self.assertTokensTypes("'1A\\n4'", ['INT_CONST_CHAR'])
        self.assertTokensTypes('xf7', ['ID'])
        self.assertTokensTypes('-1', ['MINUS', 'INT_CONST_DEC'])

    def test_special_names(self):
        self.assertTokensTypes('sizeof offsetof', ['SIZEOF', 'OFFSETOF'])

    def test_new_keywords(self):
        self.assertTokensTypes('_Bool', ['_BOOL'])
        self.assertTokensTypes('_Atomic', ['_ATOMIC'])
        self.assertTokensTypes('_Alignas _Alignof', ['_ALIGNAS', '_ALIGNOF'])

    def test_floating_constants(self):
        self.assertTokensTypes('1.5f', ['FLOAT_CONST'])
        self.assertTokensTypes('01.5', ['FLOAT_CONST'])
        self.assertTokensTypes('.15L', ['FLOAT_CONST'])
        self.assertTokensTypes('0.', ['FLOAT_CONST'])
        self.assertTokensTypes('.', ['PERIOD'])
        self.assertTokensTypes('3.3e-3', ['FLOAT_CONST'])
        self.assertTokensTypes('.7e25L', ['FLOAT_CONST'])
        self.assertTokensTypes('6.e+125f', ['FLOAT_CONST'])
        self.assertTokensTypes('666e666', ['FLOAT_CONST'])
        self.assertTokensTypes('00666e+3', ['FLOAT_CONST'])
        self.assertTokensTypes('0x0666e+3', ['INT_CONST_HEX', 'PLUS', 'INT_CONST_DEC'])

    def test_hexadecimal_floating_constants(self):
        self.assertTokensTypes('0xDE.488641p0', ['HEX_FLOAT_CONST'])
        self.assertTokensTypes('0x.488641p0', ['HEX_FLOAT_CONST'])
        self.assertTokensTypes('0X12.P0', ['HEX_FLOAT_CONST'])

    def test_char_constants(self):
        self.assertTokensTypes("'x'", ['CHAR_CONST'])
        self.assertTokensTypes("L'x'", ['WCHAR_CONST'])
        self.assertTokensTypes("u8'x'", ['U8CHAR_CONST'])
        self.assertTokensTypes("u'x'", ['U16CHAR_CONST'])
        self.assertTokensTypes("U'x'", ['U32CHAR_CONST'])
        self.assertTokensTypes("'\\t'", ['CHAR_CONST'])
        self.assertTokensTypes("'\\''", ['CHAR_CONST'])
        self.assertTokensTypes("'\\?'", ['CHAR_CONST'])
        self.assertTokensTypes("'\\0'", ['CHAR_CONST'])
        self.assertTokensTypes("'\\012'", ['CHAR_CONST'])
        self.assertTokensTypes("'\\x2f'", ['CHAR_CONST'])
        self.assertTokensTypes("'\\x2f12'", ['CHAR_CONST'])
        self.assertTokensTypes("L'\\xaf'", ['WCHAR_CONST'])

    def test_on_rbrace_lbrace(self):
        braces = []

        def on_lbrace():
            braces.append('{')

        def on_rbrace():
            braces.append('}')
        clex = CLexer(self.error_func, on_lbrace, on_rbrace, self.type_lookup_func)
        clex.input('hello { there } } and again }}{')
        token_list(clex)
        self.assertEqual(braces, ['{', '}', '}', '}', '}', '{'])

    def test_string_literal(self):
        self.assertTokensTypes('"a string"', ['STRING_LITERAL'])
        self.assertTokensTypes('L"ing"', ['WSTRING_LITERAL'])
        self.assertTokensTypes('u8"ing"', ['U8STRING_LITERAL'])
        self.assertTokensTypes('u"ing"', ['U16STRING_LITERAL'])
        self.assertTokensTypes('U"ing"', ['U32STRING_LITERAL'])
        self.assertTokensTypes('"i am a string too \t"', ['STRING_LITERAL'])
        self.assertTokensTypes('"esc\\ape \\"\\\'\\? \\0234 chars \\rule"', ['STRING_LITERAL'])
        self.assertTokensTypes('"hello \'joe\' wanna give it a \\"go\\"?"', ['STRING_LITERAL'])
        self.assertTokensTypes('"SSSSSSSSSSSSSSSS"', ['STRING_LITERAL'])
        self.assertTokensTypes('"\\x"', ['STRING_LITERAL'])
        self.assertTokensTypes('"\\a\\b\\c\\d\\e\\f\\g\\h\\i\\j\\k\\l\\m\\n\\o\\p\\q\\r\\s\\t\\u\\v\\w\\x\\y\\z\\A\\B\\C\\D\\E\\F\\G\\H\\I\\J\\K\\L\\M\\N\\O\\P\\Q\\R\\S\\T\\U\\V\\W\\X\\Y\\Z"', ['STRING_LITERAL'])
        self.assertTokensTypes('"C:\\x\\fa\\x1e\\xited"', ['STRING_LITERAL'])
        self.assertTokensTypes('"jx\\9"', ['STRING_LITERAL'])
        self.assertTokensTypes('"fo\\9999999"', ['STRING_LITERAL'])

    def test_mess(self):
        self.assertTokensTypes('[{}]()', ['LBRACKET', 'LBRACE', 'RBRACE', 'RBRACKET', 'LPAREN', 'RPAREN'])
        self.assertTokensTypes('()||!C&~Z?J', ['LPAREN', 'RPAREN', 'LOR', 'LNOT', 'ID', 'AND', 'NOT', 'ID', 'CONDOP', 'ID'])
        self.assertTokensTypes('+-*/%|||&&&^><>=<===!=', ['PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'LOR', 'OR', 'LAND', 'AND', 'XOR', 'GT', 'LT', 'GE', 'LE', 'EQ', 'NE'])
        self.assertTokensTypes('++--->?.,;:', ['PLUSPLUS', 'MINUSMINUS', 'ARROW', 'CONDOP', 'PERIOD', 'COMMA', 'SEMI', 'COLON'])

    def test_exprs(self):
        self.assertTokensTypes('bb-cc', ['ID', 'MINUS', 'ID'])
        self.assertTokensTypes('foo & 0xFF', ['ID', 'AND', 'INT_CONST_HEX'])
        self.assertTokensTypes('(2+k) * 62', ['LPAREN', 'INT_CONST_DEC', 'PLUS', 'ID', 'RPAREN', 'TIMES', 'INT_CONST_DEC'])
        self.assertTokensTypes('x | y >> z', ['ID', 'OR', 'ID', 'RSHIFT', 'ID'])
        self.assertTokensTypes('x <<= z << 5', ['ID', 'LSHIFTEQUAL', 'ID', 'LSHIFT', 'INT_CONST_DEC'])
        self.assertTokensTypes('x = y > 0 ? y : -6', ['ID', 'EQUALS', 'ID', 'GT', 'INT_CONST_OCT', 'CONDOP', 'ID', 'COLON', 'MINUS', 'INT_CONST_DEC'])
        self.assertTokensTypes('a+++b', ['ID', 'PLUSPLUS', 'PLUS', 'ID'])

    def test_statements(self):
        self.assertTokensTypes('for (int i = 0; i < n; ++i)', ['FOR', 'LPAREN', 'INT', 'ID', 'EQUALS', 'INT_CONST_OCT', 'SEMI', 'ID', 'LT', 'ID', 'SEMI', 'PLUSPLUS', 'ID', 'RPAREN'])
        self.assertTokensTypes('self: goto self;', ['ID', 'COLON', 'GOTO', 'ID', 'SEMI'])
        self.assertTokensTypes(' switch (typ)\n                {\n                    case TYPE_ID:\n                        m = 5;\n                        break;\n                    default:\n                        m = 8;\n                }', ['SWITCH', 'LPAREN', 'ID', 'RPAREN', 'LBRACE', 'CASE', 'ID', 'COLON', 'ID', 'EQUALS', 'INT_CONST_DEC', 'SEMI', 'BREAK', 'SEMI', 'DEFAULT', 'COLON', 'ID', 'EQUALS', 'INT_CONST_DEC', 'SEMI', 'RBRACE'])

    def test_preprocessor_line(self):
        self.assertTokensTypes('#abracadabra', ['PPHASH', 'ID'])
        str = '\n        546\n        #line 66 "kwas\\df.h"\n        id 4\n        dsf\n        # 9\n        armo\n        #line 10 "..\\~..\\test.h"\n        tok1\n        #line 99999 "include/me.h"\n        tok2\n        '
        self.clex.input(str)
        t1 = require_token(self.clex.token())
        self.assertEqual(t1.type, 'INT_CONST_DEC')
        self.assertEqual(t1.lineno, 2)
        t2 = require_token(self.clex.token())
        self.assertEqual(t2.type, 'ID')
        self.assertEqual(t2.value, 'id')
        self.assertEqual(t2.lineno, 66)
        self.assertEqual(self.clex.filename, 'kwas\\df.h')
        for i in range(3):
            t = require_token(self.clex.token())
        self.assertEqual(t.type, 'ID')
        self.assertEqual(t.value, 'armo')
        self.assertEqual(t.lineno, 9)
        self.assertEqual(self.clex.filename, 'kwas\\df.h')
        t4 = require_token(self.clex.token())
        self.assertEqual(t4.type, 'ID')
        self.assertEqual(t4.value, 'tok1')
        self.assertEqual(t4.lineno, 10)
        self.assertEqual(self.clex.filename, '..\\~..\\test.h')
        t5 = require_token(self.clex.token())
        self.assertEqual(t5.type, 'ID')
        self.assertEqual(t5.value, 'tok2')
        self.assertEqual(t5.lineno, 99999)
        self.assertEqual(self.clex.filename, 'include/me.h')

    def test_preprocessor_line_funny(self):
        str = '\n        #line 10 "..\\6\\joe.h"\n        10\n        '
        self.clex.input(str)
        t1 = require_token(self.clex.token())
        self.assertEqual(t1.type, 'INT_CONST_DEC')
        self.assertEqual(t1.lineno, 10)
        self.assertEqual(self.clex.filename, '..\\6\\joe.h')

    def test_preprocessor_pragma(self):
        str = '\n        42\n        #pragma\n        #pragma helo me\n        #pragma once\n        # pragma omp parallel private(th_id)\n        #\tpragma {pack: 2, smack: 3}\n        #pragma <includeme.h> "nowit.h"\n        #pragma "string"\n        #pragma somestring="some_other_string"\n        #pragma id 124124 and numbers 0235495\n        _Pragma("something else")\n        59\n        '
        self.clex.input(str)
        t1 = require_token(self.clex.token())
        self.assertEqual(t1.type, 'INT_CONST_DEC')
        t2 = require_token(self.clex.token())
        self.assertEqual(t2.type, 'PPPRAGMA')
        t3 = require_token(self.clex.token())
        self.assertEqual(t3.type, 'PPPRAGMA')
        t4 = require_token(self.clex.token())
        self.assertEqual(t4.type, 'PPPRAGMASTR')
        self.assertEqual(t4.value, 'helo me')
        for i in range(3):
            self.clex.token()
        t5 = require_token(self.clex.token())
        self.assertEqual(t5.type, 'PPPRAGMASTR')
        self.assertEqual(t5.value, 'omp parallel private(th_id)')
        for i in range(5):
            ta = require_token(self.clex.token())
            self.assertEqual(ta.type, 'PPPRAGMA')
            tb = require_token(self.clex.token())
            self.assertEqual(tb.type, 'PPPRAGMASTR')
        t6a = require_token(self.clex.token())
        t6l = require_token(self.clex.token())
        t6b = require_token(self.clex.token())
        t6r = require_token(self.clex.token())
        self.assertEqual(t6a.type, '_PRAGMA')
        self.assertEqual(t6l.type, 'LPAREN')
        self.assertEqual(t6b.type, 'STRING_LITERAL')
        self.assertEqual(t6b.value, '"something else"')
        self.assertEqual(t6r.type, 'RPAREN')
        t7 = require_token(self.clex.token())
        self.assertEqual(t7.type, 'INT_CONST_DEC')
        self.assertEqual(t7.lineno, 13)
ERR_ILLEGAL_CHAR = 'Illegal character'
ERR_OCTAL = 'Invalid octal constant'
ERR_UNMATCHED_QUOTE = "Unmatched '"
ERR_INVALID_CCONST = 'Invalid char constant'
ERR_STRING_ESCAPE = 'String contains invalid escape'
ERR_FILENAME_BEFORE_LINE = 'filename before line'
ERR_LINENUM_MISSING = 'line number missing'
ERR_INVALID_LINE_DIRECTIVE = 'invalid #line directive'
ERR_COMMENT = 'Comments are not supported'

class TestCLexerErrors(unittest.TestCase):
    """Test lexing of erroneous strings.
    Works by passing an error function that saves the error
    in an attribute for later perusal.
    """

    def error_func(self, msg, line, column):
        self.error = msg

    def on_lbrace_func(self):
        pass

    def on_rbrace_func(self):
        pass

    def type_lookup_func(self, typ):
        return False

    def setUp(self):
        self.clex = CLexer(self.error_func, self.on_lbrace_func, self.on_rbrace_func, self.type_lookup_func)
        self.error = ''

    def assertLexerError(self, str, error_like):
        self.clex.input(str)
        token_types(self.clex)
        self.assertTrue(self.error, f'Expected a lexical error for {str!r}')
        self.error = ''

    def test_trivial_tokens(self):
        self.assertLexerError('@', ERR_ILLEGAL_CHAR)
        self.assertLexerError('`', ERR_ILLEGAL_CHAR)
        self.assertLexerError('\\', ERR_ILLEGAL_CHAR)

    def test_integer_constants(self):
        self.assertLexerError('029', ERR_OCTAL)
        self.assertLexerError('012345678', ERR_OCTAL)

    def test_char_constants(self):
        self.assertLexerError("'", ERR_UNMATCHED_QUOTE)
        self.assertLexerError("'b\n", ERR_UNMATCHED_QUOTE)
        self.assertLexerError("'\\xaa\n'", ERR_UNMATCHED_QUOTE)
        self.assertLexerError("'123\\12a'", ERR_INVALID_CCONST)
        self.assertLexerError("'123\\xabg'", ERR_INVALID_CCONST)
        self.assertLexerError("''", ERR_INVALID_CCONST)
        self.assertLexerError("'abcjx'", ERR_INVALID_CCONST)
        self.assertLexerError("'\\*'", ERR_INVALID_CCONST)

    def test_string_literals(self):
        self.assertLexerError('"jx\\`"', ERR_STRING_ESCAPE)
        self.assertLexerError('"hekllo\\* on ix"', ERR_STRING_ESCAPE)
        self.assertLexerError('L"hekllo\\* on ix"', ERR_STRING_ESCAPE)
        self.assertLexerError('"\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\`\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123"', ERR_STRING_ESCAPE)
        self.assertLexerError('"\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\x23\\`\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23\\xf1\\x23"', ERR_STRING_ESCAPE)
        self.assertLexerError('"\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\`\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\123\\12\\123456', ERR_ILLEGAL_CHAR)
        self.assertLexerError('"\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\`\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x23\\x2\\x23456', ERR_ILLEGAL_CHAR)

    def test_preprocessor(self):
        self.assertLexerError('#line "ka"', ERR_FILENAME_BEFORE_LINE)
        self.assertLexerError('#line df', ERR_INVALID_LINE_DIRECTIVE)
        self.assertLexerError('#line \n', ERR_LINENUM_MISSING)
        self.assertLexerError('#line 0u', ERR_INVALID_LINE_DIRECTIVE)
        self.assertLexerError('#line 1U', ERR_INVALID_LINE_DIRECTIVE)
        self.assertLexerError('#line 10uLL', ERR_INVALID_LINE_DIRECTIVE)
        self.assertLexerError('//', ERR_COMMENT)
        self.assertLexerError('/*', ERR_COMMENT)
if __name__ == '__main__':
    unittest.main()
